"""Locate immutable resources in installed wheels and editable checkouts."""

__all__ = [
    "MAX_RESOURCE_BYTES",
    "Path",
    "character_directory",
    "engineering_protocol",
    "files",
    "load_resource",
    "resource_path",
    "resource_root",
]

from importlib.resources import files
from pathlib import Path

from mythic_agent.core.validation import SecurityError, ValidationError
from mythic_agent.data.data_loader import MAX_RESOURCE_BYTES, RobustDataLoader


def character_directory() -> Path:
    """Return the character asset directory independently of working directory."""
    packaged = files("mythic_agent").joinpath("resources", "characters")
    if packaged.is_dir():
        return Path(str(packaged))
    return Path(__file__).resolve().parent.parent / "default_agent_characters"


def engineering_protocol() -> str:
    """Read the shipped Mythic Engineering protocol."""
    packaged = files("mythic_agent").joinpath("resources", "engineering.md")
    if packaged.is_file():
        return packaged.read_text(encoding="utf-8")
    source = Path(__file__).resolve().parent.parent / "Mythic-Engineering"
    return (source / "Mythic-Engineering_SKILL.md").read_text(encoding="utf-8")


def resource_root() -> Path:
    """Return the package data directory that resource names resolve under.

    This is the on-disk ``mythic_agent/data`` directory, which ships inside
    installed wheels (the whole ``mythic_agent`` package is included) and is
    present in editable checkouts. Resource names passed to
    :func:`resource_path` / :func:`load_resource` may never resolve outside
    this directory.
    """
    return Path(__file__).resolve().parent / "data"


def resource_path(name: str) -> Path:
    """Resolve a resource *name* to a path inside :func:`resource_root`.

    Hardened against path traversal: absolute paths, ``..`` segments, null
    bytes, and anything that resolves outside the package data directory are
    rejected with :class:`~mythic_agent.core.validation.SecurityError` (a
    ``ValidationError`` subclass). A name that passes validation but names no
    existing file still resolves to the expected path; existence is checked by
    :func:`load_resource`, which raises ``FileNotFoundError`` naming that path.
    """
    if not isinstance(name, str) or not name:
        raise SecurityError(f"Invalid resource name: {name!r} (must be a non-empty string).")
    if "\x00" in name:
        raise SecurityError(f"Invalid resource name {name!r}: null bytes are not allowed.")
    candidate = Path(name)
    if candidate.is_absolute():
        raise SecurityError(
            f"Invalid resource name {name!r}: absolute paths are not allowed; "
            f"names must be relative to the package data dir {resource_root()}."
        )
    if ".." in candidate.parts:
        raise SecurityError(
            f"Invalid resource name {name!r}: parent-directory (..) segments "
            "are not allowed; names must stay inside the package data dir."
        )
    root = resource_root().resolve()
    resolved = (root / candidate).resolve()
    if resolved != root and root not in resolved.parents:
        raise SecurityError(
            f"Invalid resource name {name!r}: resolves to {resolved}, which is "
            f"outside the package data dir {root}."
        )
    return resolved


def load_resource(name: str, *, format: str | None = None) -> object:
    """Load a packaged data resource by name, with hardening.

    The name is validated by :func:`resource_path` (traversal-safe); a name
    that resolves to no file raises ``FileNotFoundError`` naming the expected
    path. Loading is strict: files larger than ``MAX_RESOURCE_BYTES`` (1 MiB)
    are rejected before parsing, malformed YAML raises ``ValidationError``
    with file path and line/column info, and an empty file yields an empty
    mapping ``{}`` instead of crashing.

    ``format`` overrides suffix-based dispatch (``json`` / ``yaml`` / ``yml``
    / ``md`` / ``txt``); anything else is read as UTF-8 text (also size-capped).
    """
    path = resource_path(name)
    if not path.is_file():
        raise FileNotFoundError(
            f"resource file not found: {path} (expected under {resource_root()})"
        )
    fmt = (format or path.suffix.lstrip(".")).lower()
    if fmt == "json":
        return RobustDataLoader.load_json(path, strict=True)
    if fmt in ("yaml", "yml"):
        return RobustDataLoader.load_yaml(path, strict=True)
    if fmt in ("md", "txt", "text"):
        return RobustDataLoader.load_markdown(path, strict=True)
    if path.stat().st_size > MAX_RESOURCE_BYTES:
        raise ValidationError(
            f"Refusing to load {path}: size {path.stat().st_size} bytes exceeds "
            f"the {MAX_RESOURCE_BYTES}-byte limit (checked before parsing)."
        )
    return path.read_text(encoding="utf-8")
