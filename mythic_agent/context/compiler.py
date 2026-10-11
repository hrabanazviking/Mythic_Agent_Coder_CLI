"""Context compiler architecture (Slice 051).

:class:`ContextCompiler` assembles an ordered sequence of
:class:`ContextBlock` objects from pluggable :class:`ContextSource`
implementations.  Sources are isolated to one canonical workspace root;
every file a source touches must resolve inside that root, so a source
bound to workspace A can never read workspace B.

Data-quality behavior is explicit, not silent:

* **stale** -- :class:`CachedSource` wraps a source with a TTL; expired
  entries are re-collected.
* **malformed** -- sources record a warning and skip the offending item
  instead of poisoning the whole compilation.
* **missing** -- missing inputs produce empty blocks plus warnings.
* **oversized** -- blocks beyond ``max_block_tokens`` are truncated
  (when trimmable) or dropped, recorded in the result.

Cancellation is cooperative: a ``threading.Event`` checked between
sources raises :class:`ContextCompilationCancelled`.
"""

from __future__ import annotations

__all__ = [
    "CachedSource",
    "CompileContext",
    "CompiledContext",
    "ContextBlock",
    "ContextCompilationCancelled",
    "ContextCompiler",
    "ContextError",
    "ContextSource",
    "format_compiled",
]

import logging
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Protocol, runtime_checkable

from ..core.redaction import SecretRedactor
from ..core.workspace import canonical_workspace_root
from .budget import TokenEstimator, truncate_text


class ContextError(Exception):
    """Base error for context compilation failures."""


class ContextCompilationCancelled(ContextError):
    """Raised when the cancel event fires mid-compilation."""


@dataclass
class ContextBlock:
    """One ordered unit of compiled context."""

    name: str
    content: str
    priority: int = 5  # lower == more important; <= 0 always kept
    provenance: dict[str, Any] = field(default_factory=dict)
    trimmable: bool = True
    tokens: int = 0  # filled in by ContextCompiler.compile()


@runtime_checkable
class ContextSource(Protocol):
    """A pluggable producer of context blocks."""

    name: str
    priority: int
    enabled: bool

    def collect(self, ctx: "CompileContext") -> Iterable[ContextBlock]:
        """Yield blocks for *ctx*; may raise to skip this source."""
        ...


@dataclass
class CompileContext:
    """Inputs handed to every source during one compilation."""

    workspace: Path
    config: dict[str, Any] = field(default_factory=dict)
    query: str | None = None
    cancel_event: threading.Event | None = None
    redactor: SecretRedactor | None = None
    budget_tokens: int = 4000


@dataclass
class CompiledContext:
    """The result of :meth:`ContextCompiler.compile`."""

    blocks: list[ContextBlock]
    total_tokens: int
    budget_tokens: int
    truncated: list[str] = field(default_factory=list)
    dropped: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _check_cancelled(event: threading.Event | None) -> None:
    if event is not None and event.is_set():
        raise ContextCompilationCancelled("context compilation cancelled")


class ContextCompiler:
    """Assemble ordered context blocks from pluggable sources.

    The compiler is bound to one canonical workspace root; sources
    receive that root and must read only inside it.  Selection is
    priority-ordered: priority ``<= 0`` blocks are mandatory, the rest
    compete atomically (most important first; ties keep source order),
    with per-block truncation before any block is dropped.
    """

    def __init__(
        self,
        workspace: Path | str,
        *,
        config: dict[str, Any] | None = None,
        estimator: TokenEstimator | None = None,
        budget_tokens: int = 4000,
        max_block_tokens: int = 2000,
        cancel_event: threading.Event | None = None,
        redactor: SecretRedactor | None = None,
    ) -> None:
        # Raises ValueError for a missing/non-directory workspace.
        self.workspace = canonical_workspace_root(workspace)
        self.config = config or {}
        self.estimator = estimator or TokenEstimator()
        if budget_tokens <= 0:
            raise ValueError("budget_tokens must be positive")
        if max_block_tokens <= 0:
            raise ValueError("max_block_tokens must be positive")
        self.budget_tokens = budget_tokens
        self.max_block_tokens = max_block_tokens
        self.cancel_event = cancel_event
        self.redactor = redactor or SecretRedactor(self.config)
        self._sources: list[ContextSource] = []
        self._counter = 0

    def add_source(self, source: ContextSource) -> ContextSource:
        """Register *source*; returns it for chaining."""
        for attr in ("name", "priority", "enabled", "collect"):
            if not hasattr(source, attr):
                raise TypeError(f"source is missing attribute {attr!r}")
        self._sources.append(source)
        return source

    @property
    def sources(self) -> list[ContextSource]:
        return list(self._sources)

    def compile(self, query: str | None = None) -> CompiledContext:
        """Collect, redact, fit and order blocks inside the budget."""
        _check_cancelled(self.cancel_event)
        ctx = CompileContext(
            workspace=self.workspace,
            config=self.config,
            query=query,
            cancel_event=self.cancel_event,
            redactor=self.redactor,
            budget_tokens=self.budget_tokens,
        )
        blocks: list[ContextBlock] = []
        warnings: list[str] = []
        for source in self._sources:
            _check_cancelled(self.cancel_event)
            if not source.enabled:
                continue
            try:
                produced = list(source.collect(ctx) or [])
            except ContextCompilationCancelled:
                raise
            except Exception as exc:  # one bad source never kills the run
                warnings.append(f"source {source.name!r} failed: {exc}")
                logging.warning("Context source %r failed: %s", source.name, exc)
                continue
            _check_cancelled(self.cancel_event)
            for block in produced:
                if not isinstance(block, ContextBlock):
                    warnings.append(
                        f"source {source.name!r} produced a non-block; skipped")
                    continue
                block.provenance.setdefault("source", source.name)
                block.provenance.setdefault("workspace", str(self.workspace))
                blocks.append(block)

        fitted, truncated, dropped, fit_warnings = self._fit(blocks)
        warnings.extend(fit_warnings)
        # Stable order: priority asc, then source-registration order.
        order = {id(b): i for i, b in enumerate(blocks)}
        fitted.sort(key=lambda b: (b.priority, order[id(b)]))
        total = sum(b.tokens for b in fitted)
        return CompiledContext(
            blocks=fitted,
            total_tokens=total,
            budget_tokens=self.budget_tokens,
            truncated=truncated,
            dropped=dropped,
            warnings=warnings,
        )

    # -- internals ------------------------------------------------------
    def _fit(self, blocks: list[ContextBlock]
             ) -> tuple[list[ContextBlock], list[str], list[str], list[str]]:
        """Redact, tokenize, truncate oversized blocks, then select."""
        truncated: list[str] = []
        dropped: list[str] = []
        warnings: list[str] = []
        sized: list[ContextBlock] = []
        for block in blocks:
            content = self.redactor.text(block.content) if block.content else ""
            if not content.strip():
                warnings.append(f"block {block.name!r} is empty; dropped")
                dropped.append(block.name)
                continue
            tokens = self.estimator.count(content)
            if tokens > self.max_block_tokens:
                if block.trimmable:
                    content = truncate_text(content, self.max_block_tokens,
                                            self.estimator)
                    tokens = self.estimator.count(content)
                    truncated.append(block.name)
                    warnings.append(
                        f"block {block.name!r} exceeded {self.max_block_tokens} "
                        f"tokens; truncated")
                else:
                    dropped.append(block.name)
                    warnings.append(
                        f"block {block.name!r} exceeded {self.max_block_tokens} "
                        f"tokens and is not trimmable; dropped")
                    continue
            block.content = content
            block.tokens = tokens
            sized.append(block)

        mandatory = [b for b in sized if b.priority <= 0]
        rest = sorted((b for b in sized if b.priority > 0),
                      key=lambda b: b.priority)
        selected = list(mandatory)
        used = sum(b.tokens for b in mandatory)
        remaining = self.budget_tokens - used
        for block in rest:
            if block.tokens <= remaining:
                selected.append(block)
                remaining -= block.tokens
            else:
                dropped.append(block.name)
                warnings.append(
                    f"block {block.name!r} did not fit the remaining budget; dropped")
        return selected, truncated, dropped, warnings


class CachedSource:
    """Wrap a source with TTL caching to bound stale data (Slice 051).

    Results are cached per (source name, workspace, query) for
    ``ttl_seconds``; expired entries are re-collected.  ``ttl_seconds=0``
    disables the cache entirely (always fresh).
    """

    def __init__(self, source: ContextSource, ttl_seconds: float = 300.0) -> None:
        if ttl_seconds < 0:
            raise ValueError("ttl_seconds must be non-negative")
        self._source = source
        self.ttl_seconds = ttl_seconds
        self._cache: dict[tuple[str, str, str | None],
                          tuple[float, list[ContextBlock]]] = {}
        self._lock = threading.Lock()

    @property
    def name(self) -> str:
        return self._source.name

    @property
    def priority(self) -> int:
        return self._source.priority

    @property
    def enabled(self) -> bool:
        return self._source.enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._source.enabled = value

    def collect(self, ctx: CompileContext) -> Iterable[ContextBlock]:
        _check_cancelled(ctx.cancel_event)
        if self.ttl_seconds == 0:
            return list(self._source.collect(ctx))
        key = (self._source.name, str(ctx.workspace), ctx.query)
        now = time.monotonic()
        with self._lock:
            hit = self._cache.get(key)
            if hit is not None and now - hit[0] < self.ttl_seconds:
                return list(hit[1])
        blocks = list(self._source.collect(ctx))
        with self._lock:
            self._cache[key] = (now, list(blocks))
        return blocks

    def invalidate(self) -> None:
        """Drop all cached entries."""
        with self._lock:
            self._cache.clear()


def format_compiled(compiled: CompiledContext) -> str:
    """Render compiled blocks as prompt text with provenance headers."""
    parts = []
    for block in compiled.blocks:
        source = block.provenance.get("source", "?")
        parts.append(f"\n\n[Context: {block.name} — source {source}]\n{block.content}")
    return "".join(parts)
