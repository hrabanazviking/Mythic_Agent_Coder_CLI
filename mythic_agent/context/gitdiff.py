"""Git-diff-aware context (Slice 060).

Exposes staged and unstaged ``git diff`` hunks as compiler blocks so the
model sees exactly what changed in the working tree.  Non-git
directories, missing ``git`` binaries and oversized diffs are handled
gracefully with warnings -- never tracebacks.
"""

from __future__ import annotations

__all__ = [
    "GitDiff",
    "collect_git_diff",
]

import logging
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..core.redaction import SecretRedactor
from ..core.workspace import canonical_workspace_root
from .budget import TokenEstimator
from .compiler import ContextBlock, ContextSource


MAX_DIFF_BYTES = 200_000
_DIFF_TIMEOUT = 15


@dataclass
class GitDiff:
    """Staged/unstaged diff text plus collection warnings."""

    staged: str = ""
    unstaged: str = ""
    is_git_repo: bool = False
    warnings: list[str] = field(default_factory=list)


def _run_git(workspace: Path, *args: str) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["git", "-C", str(workspace), *args],
        capture_output=True, timeout=_DIFF_TIMEOUT)
    stdout = proc.stdout.decode("utf-8", errors="replace")
    stderr = proc.stderr.decode("utf-8", errors="replace")
    return proc.returncode, stdout, stderr


def collect_git_diff(
    workspace: Path | str,
    *,
    max_diff_bytes: int = MAX_DIFF_BYTES,
    redactor: SecretRedactor | None = None,
) -> GitDiff:
    """Collect staged and unstaged diffs for *workspace*.

    A directory that is not a git repository (or a missing ``git``
    binary) yields ``is_git_repo=False`` with an explanatory warning --
    callers treat it as "no diff context", not an error.
    """
    root = canonical_workspace_root(workspace)
    diff = GitDiff()
    if shutil.which("git") is None:
        diff.warnings.append("git binary not found; diff context unavailable")
        return diff
    try:
        code, _out, err = _run_git(root, "rev-parse", "--is-inside-work-tree")
    except (subprocess.TimeoutExpired, OSError) as exc:
        diff.warnings.append(f"git rev-parse failed: {exc}")
        return diff
    if code != 0 or "true" not in _out:
        diff.warnings.append(
            f"not a git repository ({err.strip() or 'rev-parse failed'}); "
            "diff context unavailable")
        return diff
    diff.is_git_repo = True
    for attr, args in (("staged", ("diff", "--cached", "--no-color")),
                       ("unstaged", ("diff", "--no-color"))):
        try:
            code, out, err = _run_git(root, *args)
        except (subprocess.TimeoutExpired, OSError) as exc:
            diff.warnings.append(f"git {' '.join(args)} failed: {exc}")
            continue
        if code != 0:
            diff.warnings.append(
                f"git {' '.join(args)} exited {code}: {err.strip()}")
            continue
        text = out
        if len(text.encode("utf-8")) > max_diff_bytes:
            raw = text.encode("utf-8")[:max_diff_bytes].decode("utf-8", errors="ignore")
            text = raw + "\n... [diff truncated]"
            diff.warnings.append(f"{attr} diff exceeded {max_diff_bytes} bytes; truncated")
        if redactor is not None:
            text = redactor.text(text)
        setattr(diff, attr, text)
    return diff


class GitDiffSource(ContextSource):
    """Compiler source exposing staged/unstaged diff hunks (Slice 060)."""

    def __init__(self, *, priority: int = 2, enabled: bool = True,
                 max_diff_bytes: int = MAX_DIFF_BYTES) -> None:
        self.name = "git-diff"
        self.priority = priority
        self.enabled = enabled
        self.max_diff_bytes = max_diff_bytes

    def collect(self, ctx) -> list[ContextBlock]:
        diff = collect_git_diff(ctx.workspace, max_diff_bytes=self.max_diff_bytes,
                                redactor=ctx.redactor)
        for warning in diff.warnings:
            logging.getLogger(__name__).warning("git-diff: %s", warning)
        blocks: list[ContextBlock] = []
        if diff.staged.strip():
            blocks.append(ContextBlock(
                name="diff:staged", content="Staged changes:\n" + diff.staged,
                priority=self.priority, trimmable=True,
                provenance={"kind": "staged"}))
        if diff.unstaged.strip():
            blocks.append(ContextBlock(
                name="diff:unstaged", content="Unstaged changes:\n" + diff.unstaged,
                priority=self.priority, trimmable=True,
                provenance={"kind": "unstaged"}))
        for block in blocks:
            block.provenance["warnings"] = list(diff.warnings)
            block.provenance["is_git_repo"] = diff.is_git_repo
        return blocks
