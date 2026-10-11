"""Explicit file context via @-mentions (Slice 056).

Mentions like ``@src/main.py`` in a user query resolve against the
workspace root.  Containment is enforced with
:func:`~mythic_agent.core.workspace.assert_within_workspace`, which
resolves symlinks -- a symlink pointing outside the workspace is
rejected, as are ``..`` escapes and cross-workspace paths.  Missing,
oversized and malformed inputs produce warnings, never tracebacks.
"""

from __future__ import annotations

__all__ = [
    "MENTION_RE",
    "ExplicitFileContext",
    "ResolvedFile",
    "extract_mentions",
    "resolve_mentions",
]

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..core.workspace import assert_within_workspace, canonical_workspace_root
from .budget import TokenEstimator, truncate_text
from .compiler import ContextBlock, ContextSource


MENTION_RE = re.compile(r"@([A-Za-z0-9_][\w.\-/]*)")

MAX_FILE_BYTES = 100_000


@dataclass
class ResolvedFile:
    """One successfully resolved @-mention."""

    mention: str
    path: Path
    content: str
    tokens: int
    truncated: bool = False
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExplicitFileContext:
    """Outcome of :func:`resolve_mentions`."""

    files: list[ResolvedFile]
    warnings: list[str]


def extract_mentions(query: str) -> list[str]:
    """Return @-mention paths in order of first appearance, deduplicated."""
    seen: list[str] = []
    for match in MENTION_RE.finditer(query or ""):
        mention = match.group(1).rstrip("/")
        if mention and mention not in seen:
            seen.append(mention)
    return seen


def resolve_mentions(
    query: str,
    workspace: Path | str,
    *,
    estimator: TokenEstimator | None = None,
    max_file_bytes: int = MAX_FILE_BYTES,
) -> ExplicitFileContext:
    """Resolve @-mentions in *query* against *workspace*.

    Symlink traversal outside the workspace, ``..`` escapes and
    cross-workspace absolute paths raise containment errors that become
    warnings here -- the mention is blocked, never read.
    """
    estimator = estimator or TokenEstimator()
    root = canonical_workspace_root(workspace)
    files: list[ResolvedFile] = []
    warnings: list[str] = []
    for mention in extract_mentions(query):
        try:
            resolved = assert_within_workspace(root, mention)
        except Exception as exc:
            warnings.append(f"blocked mention @{mention}: {exc}")
            continue
        if not resolved.exists():
            warnings.append(f"missing file for @{mention}")
            continue
        if resolved.is_dir():
            warnings.append(f"@{mention} is a directory, not a file")
            continue
        if not resolved.is_file():
            warnings.append(f"@{mention} is not a regular file")
            continue
        try:
            raw = resolved.read_bytes()
        except OSError as exc:
            warnings.append(f"unreadable file @{mention}: {exc}")
            continue
        if len(raw) > max_file_bytes:
            raw = raw[:max_file_bytes]
            truncated = True
        else:
            truncated = False
        if b"\x00" in raw:
            warnings.append(f"malformed file skipped (binary): @{mention}")
            continue
        content = raw.decode("utf-8", errors="replace")
        if not content.strip():
            warnings.append(f"empty file: @{mention}")
            continue
        files.append(ResolvedFile(
            mention=mention, path=resolved, content=content,
            tokens=estimator.count(content), truncated=truncated,
            provenance={"mention": mention,
                        "relative": str(resolved.relative_to(root))}))
    return ExplicitFileContext(files=files, warnings=warnings)


class ExplicitFilesSource(ContextSource):
    """Compiler source resolving @-mentions from the query (Slice 056)."""

    def __init__(self, *, priority: int = 2, enabled: bool = True) -> None:
        self.name = "explicit-files"
        self.priority = priority
        self.enabled = enabled

    def collect(self, ctx) -> list[ContextBlock]:
        result = resolve_mentions(ctx.query or "", ctx.workspace)
        for warning in result.warnings:
            import logging
            logging.getLogger(__name__).warning("explicit-files: %s", warning)
        blocks = []
        for item in result.files:
            blocks.append(ContextBlock(
                name=f"file:{item.provenance['relative']}",
                content=f"--- {item.provenance['relative']} ---\n{item.content}",
                priority=self.priority,
                provenance={"mention": item.mention,
                            "relative": item.provenance["relative"],
                            "truncated": item.truncated,
                            "warnings": list(result.warnings)}))
        return blocks
