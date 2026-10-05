"""Portable workspace identity and contained file resolution."""

import hashlib
from pathlib import Path, PureWindowsPath
from typing import Any


def resolve_workspace(
    explicit: Path | str | None = None, config: dict[str, Any] | None = None,
) -> Path:
    configured = (config or {}).get("working_directory")
    path = Path(explicit or configured or Path.cwd()).expanduser().resolve()
    if not path.is_dir():
        raise ValueError(f"Workspace is not an existing directory: {path}")
    return path


def workspace_id(root: Path) -> str:
    return hashlib.sha256(str(root.resolve()).encode("utf-8")).hexdigest()


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
        relative = path.relative_to(root)
    except ValueError as exc:
        raise ValueError("Path is outside the workspace") from exc
    if write and (path == root or ".git" in relative.parts):
        raise ValueError("Cannot edit the workspace root or Git metadata")
    return path
