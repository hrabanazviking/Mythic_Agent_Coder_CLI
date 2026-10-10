"""Portable workspace identity and contained file resolution."""

__all__ = [
    "Any",
    "Path",
    "PureWindowsPath",
    "SecurityError",
    "assert_within_workspace",
    "canonical_workspace_root",
    "resolve_file",
    "resolve_workspace",
    "workspace_id",
]

import hashlib
from pathlib import Path, PureWindowsPath
from typing import Any

from .exceptions import MythicSecurityError


class SecurityError(MythicSecurityError, ValueError):
    """A path escaped its workspace root (containment breach).

    Subclasses :class:`ValueError` so existing ``except ValueError`` guards
    around :func:`resolve_file` keep working, and shares the
    :class:`MythicSecurityError` base with the validation layer's
    ``SecurityError`` so ``except MythicSecurityError`` catches both.
    """


def canonical_workspace_root(path: Path | str) -> Path:
    """Return the canonical absolute path of an existing workspace directory.

    Canonicalization collapses every spelling of the same directory --
    trailing slashes, ``.``/``..`` segments, symlinks, relative vs absolute
    paths -- into one real path (``os.path.realpath`` semantics via
    :meth:`Path.resolve`).

    Case variants: on case-insensitive filesystems the OS layer collapses
    them to the same canonical path; on case-sensitive filesystems
    differently-cased names are genuinely different directories and keep
    distinct identities (no case folding is applied, which would wrongly
    merge distinct directories).
    """
    root = Path(path).expanduser()
    if not root.is_dir():
        raise ValueError(f"Workspace is not an existing directory: {root}")
    return root.resolve()


def resolve_workspace(
    explicit: Path | str | None = None, config: dict[str, Any] | None = None,
) -> Path:
    configured = (config or {}).get("working_directory")
    path = Path(explicit or configured or Path.cwd()).expanduser().resolve()
    if not path.is_dir():
        raise ValueError(f"Workspace is not an existing directory: {path}")
    return path


def workspace_id(root: Path | str) -> str:
    """Stable identity for a workspace directory.

    The same directory reached via any spelling -- trailing slash, ``..``
    segments, symlinks, relative or absolute paths -- resolves to ONE
    canonical identity: SHA-256 over the canonical (realpath) location.
    Distinct directories always hash distinctly.

    Raises :class:`ValueError` for a non-existent path instead of silently
    minting an identity for a phantom directory.
    """
    return hashlib.sha256(str(canonical_workspace_root(root)).encode("utf-8")).hexdigest()


def assert_within_workspace(root: Path | str, path: Path | str) -> Path:
    """Containment check: *path* must resolve inside workspace *root*.

    Returns the canonical resolved path.  Raises :class:`SecurityError`
    naming both paths when *path* escapes the workspace, so a path inside
    workspace A can never resolve into workspace B (or anywhere else).

    Relative *path* values are interpreted against the workspace root,
    matching :func:`resolve_file` semantics.
    """
    canonical_root = canonical_workspace_root(root)
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = canonical_root / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(canonical_root)
    except ValueError as exc:
        raise SecurityError(
            f"Path escapes workspace: {resolved} is outside {canonical_root}"
        ) from exc
    return resolved


def resolve_file(root: Path, value: str, *, write: bool = False) -> Path:
    """Reject traversal and symlink escapes; this is not an OS sandbox."""
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise ValueError("path must be a nonempty string without NUL characters")
    root = root.resolve()
    candidate = Path(value).expanduser()
    if PureWindowsPath(value).drive and not candidate.is_absolute():
        raise ValueError("Foreign-drive paths are outside the workspace")
    path = (root / candidate).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise SecurityError(f"Path is outside the workspace: {path}") from exc
    if write and (path == root or ".git" in path.relative_to(root).parts):
        raise ValueError("Cannot edit the workspace root or Git metadata")
    return path
