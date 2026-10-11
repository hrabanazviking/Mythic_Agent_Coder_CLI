"""Repository instruction resolver + layered precedence (Slices 054/055).

:class:`InstructionResolver` discovers instruction files (``AGENTS.md``,
``.mythic``, ``.muserules``, ...) inside one workspace: size-capped,
malformed inputs skipped with warnings, symlink escapes and
cross-workspace reads blocked.

:func:`apply_precedence` merges the layers ``system > repo > dir > file``
(higher precedence wins): bullet directives are deduplicated across
layers, ``KEY: value`` directives keep the highest-precedence definition,
and every decision carries provenance.  Conflicts (same key, different
values in different layers) are reported, never silently resolved.
"""

from __future__ import annotations

__all__ = [
    "INSTRUCTION_FILENAMES",
    "LAYER_ORDER",
    "InstructionFile",
    "InstructionResolver",
    "PrecedenceResult",
    "apply_precedence",
    "parse_directives",
]

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..core.workspace import assert_within_workspace, canonical_workspace_root
from .compiler import ContextBlock, ContextSource


INSTRUCTION_FILENAMES = (
    "AGENTS.md",
    "CLAUDE.md",
    ".mythic.md",
    ".mythic",
    ".muserules",
    ".cursorrules",
    ".aider.rules.md",
)

# Lower number == higher precedence (wins conflicts).
LAYER_ORDER = {"system": 0, "repo": 1, "dir": 2, "file": 3}

MAX_FILE_BYTES = 65_536
MAX_TOTAL_BYTES = 262_144

_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
              "dist", "build", ".hg", ".svn"}

_BULLET_RE = re.compile(r"^\s*[-*]\s+(.+?)\s*$")
_KEYVALUE_RE = re.compile(r"^\s*([A-Za-z][\w ./-]{0,60})\s*:\s*(.+?)\s*$")


@dataclass
class InstructionFile:
    """One discovered instruction file with its precedence layer."""

    path: Path
    layer: str  # "repo" or "dir"
    content: str
    size: int
    provenance: dict[str, Any] = field(default_factory=dict)


class InstructionResolver:
    """Discover instruction files inside a single workspace."""

    def __init__(
        self,
        workspace: Path | str,
        *,
        filenames: tuple[str, ...] = INSTRUCTION_FILENAMES,
        max_file_bytes: int = MAX_FILE_BYTES,
        max_total_bytes: int = MAX_TOTAL_BYTES,
    ) -> None:
        self.root = canonical_workspace_root(workspace)
        self.filenames = filenames
        self.max_file_bytes = max_file_bytes
        self.max_total_bytes = max_total_bytes
        self.warnings: list[str] = []

    def discover(self) -> list[InstructionFile]:
        """Walk the workspace and return instruction files, ordered by layer."""
        self.warnings = []
        found: list[InstructionFile] = []
        total = 0
        for dirpath, dirnames, filenames in os.walk(self.root, followlinks=False):
            dirnames[:] = sorted(d for d in dirnames
                                 if d not in _SKIP_DIRS and not d.startswith("."))
            for name in sorted(filenames):
                if name not in self.filenames:
                    continue
                candidate = Path(dirpath) / name
                try:
                    resolved = assert_within_workspace(self.root, candidate)
                except Exception as exc:
                    self.warnings.append(f"blocked {candidate}: {exc}")
                    continue
                if not resolved.is_file():
                    continue
                size = resolved.stat().st_size
                if size > self.max_file_bytes:
                    self.warnings.append(
                        f"oversized instruction file skipped: {resolved} ({size} bytes)")
                    continue
                if total + size > self.max_total_bytes:
                    self.warnings.append(
                        f"instruction total budget exceeded; skipped {resolved}")
                    continue
                try:
                    raw = resolved.read_bytes()
                except OSError as exc:
                    self.warnings.append(f"unreadable instruction file {resolved}: {exc}")
                    continue
                if b"\x00" in raw:
                    self.warnings.append(
                        f"malformed instruction file skipped (binary): {resolved}")
                    continue
                try:
                    content = raw.decode("utf-8")
                except UnicodeDecodeError:
                    self.warnings.append(
                        f"malformed instruction file skipped (not utf-8): {resolved}")
                    continue
                if not content.strip():
                    continue
                total += size
                layer = "repo" if resolved.parent == self.root else "dir"
                found.append(InstructionFile(
                    path=resolved, layer=layer, content=content, size=size,
                    provenance={"layer": layer,
                                "relative": str(resolved.relative_to(self.root))}))
        found.sort(key=lambda f: (LAYER_ORDER[f.layer], str(f.path)))
        return found

    def resolve(self) -> list[InstructionFile]:
        """Alias for :meth:`discover` (discovery IS resolution here)."""
        return self.discover()


@dataclass
class _Directive:
    kind: str  # "key" or "bullet"
    key: str
    text: str
    layer: str
    source: str


def parse_directives(text: str, *, layer: str, source: str) -> list[_Directive]:
    """Extract ``KEY: value`` and bullet directives from *text*."""
    directives: list[_Directive] = []
    for line in text.splitlines():
        keyed = _KEYVALUE_RE.match(line)
        if keyed:
            name = re.sub(r"\s+", " ", keyed.group(1)).strip().lower()
            directives.append(_Directive("key", name, line.strip(),
                                         layer, source))
            continue
        bullet = _BULLET_RE.match(line)
        if bullet:
            body = re.sub(r"\s+", " ", bullet.group(1)).strip().lower()
            if body:
                directives.append(_Directive("bullet", body, line.strip(),
                                             layer, source))
    return directives


@dataclass
class PrecedenceResult:
    """Outcome of :func:`apply_precedence`."""

    blocks: list[ContextBlock]
    conflicts: list[dict[str, Any]]
    provenance: list[dict[str, Any]]


def apply_precedence(
    system_text: str = "",
    *,
    repo: list[InstructionFile] | None = None,
    dir_files: list[InstructionFile] | None = None,
    file_directives: list[tuple[str, str]] | None = None,
) -> PrecedenceResult:
    """Merge instruction layers with ``system > repo > dir > file`` precedence.

    * Bullet directives identical across layers are kept once, from the
      highest-precedence layer, with provenance listing every layer.
    * ``KEY: value`` directives keep the highest-precedence definition;
      when layers disagree on a key it is recorded in ``conflicts`` and
      the winner is used.
    """
    layers: list[tuple[str, str, str]] = []  # (layer, source, text)
    if system_text and system_text.strip():
        layers.append(("system", "system-prompt", system_text))
    for item in repo or []:
        layers.append(("repo", str(item.path), item.content))
    for item in dir_files or []:
        layers.append(("dir", str(item.path), item.content))
    for source, text in file_directives or []:
        if text and text.strip():
            layers.append(("file", source, text))

    key_defs: dict[str, _Directive] = {}
    bullet_defs: dict[str, _Directive] = {}
    conflicts: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []

    for layer, source, text in layers:
        for directive in parse_directives(text, layer=layer, source=source):
            provenance.append({"directive": directive.text, "layer": layer,
                               "source": source})
            if directive.kind == "key":
                incumbent = key_defs.get(directive.key)
                if incumbent is None:
                    key_defs[directive.key] = directive
                elif incumbent.text != directive.text:
                    # First definition wins only if it outranks; layers are
                    # visited highest-precedence first, so a later different
                    # text is always a lower-precedence override attempt.
                    conflicts.append({
                        "key": directive.key,
                        "winner": {"text": incumbent.text, "layer": incumbent.layer,
                                   "source": incumbent.source},
                        "overridden": {"text": directive.text, "layer": directive.layer,
                                       "source": directive.source},
                    })
                # identical redefinition: harmless, keep first.
            else:
                incumbent = bullet_defs.get(directive.key)
                if incumbent is None:
                    bullet_defs[directive.key] = directive
                # identical bullets across layers dedupe automatically.

    blocks: list[ContextBlock] = []
    if system_text and system_text.strip():
        blocks.append(ContextBlock(
            name="instructions:system", content=system_text.strip(), priority=1,
            provenance={"layer": "system"}))
    merged_keys = sorted(key_defs.values(), key=lambda d: d.key)
    merged_bullets = sorted(bullet_defs.values(), key=lambda d: d.key)
    if merged_keys or merged_bullets:
        lines = [d.text for d in merged_keys] + [d.text for d in merged_bullets]
        blocks.append(ContextBlock(
            name="instructions:merged",
            content="Repository instructions (precedence system > repo > dir > file):\n"
                    + "\n".join(f"- {line}" for line in lines),
            priority=1,
            provenance={"layer": "merged",
                        "key_directives": len(merged_keys),
                        "bullet_directives": len(merged_bullets),
                        "conflicts": len(conflicts)}))
    return PrecedenceResult(blocks=blocks, conflicts=conflicts, provenance=provenance)


class InstructionSource(ContextSource):
    """Compiler source producing instruction blocks (Slices 054/055)."""

    def __init__(self, *, priority: int = 1, enabled: bool = True,
                 system_text: str = "") -> None:
        self.name = "instructions"
        self.priority = priority
        self.enabled = enabled
        self.system_text = system_text

    def collect(self, ctx) -> list[ContextBlock]:
        resolver = InstructionResolver(ctx.workspace)
        files = resolver.resolve()
        for warning in resolver.warnings:
            logging.getLogger(__name__).warning("instructions: %s", warning)
        result = apply_precedence(
            self.system_text,
            repo=[f for f in files if f.layer == "repo"],
            dir_files=[f for f in files if f.layer == "dir"],
        )
        for block in result.blocks:
            block.provenance["warnings"] = list(resolver.warnings)
            block.provenance["conflicts"] = list(result.conflicts)
        return result.blocks
