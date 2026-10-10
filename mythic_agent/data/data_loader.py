__all__ = [
    "Any",
    "Dict",
    "List",
    "MAX_RESOURCE_BYTES",
    "Optional",
    "Path",
    "RobustDataLoader",
    "Union",
    "data_loader",
    "logger",
    "publish_sync",
]
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from ..core.secure_api import publish_sync
from ..core.validation import ValidationError

logger = logging.getLogger("mythic_data_loader")

#: Hard cap on the size of any single resource/data file the loaders will
#: touch. Checked via ``stat`` *before* any bytes are read or parsed, so a
#: hostile or corrupt multi-gigabyte file can never reach a parser.
MAX_RESOURCE_BYTES = 1024 * 1024  # 1 MiB


def _check_size(path: Path) -> int:
    """Reject files larger than :data:`MAX_RESOURCE_BYTES` before reading.

    Returns the file size in bytes. Raises :class:`ValidationError` naming
    the path, the observed size, and the limit when the file is oversized.
    """
    size = path.stat().st_size
    if size > MAX_RESOURCE_BYTES:
        raise ValidationError(
            f"Refusing to load {path}: size {size} bytes exceeds the "
            f"{MAX_RESOURCE_BYTES}-byte limit (checked before parsing)."
        )
    return size


def _yaml_error(path: Path, exc: Exception) -> ValidationError:
    """Build a ValidationError for malformed YAML with file/line/column info."""
    mark = getattr(exc, "problem_mark", None)
    if mark is not None:
        # PyYAML marks are 0-based; humans count lines/columns from 1.
        location = f"line {mark.line + 1}, column {mark.column + 1}"
        detail = getattr(exc, "problem", None) or str(exc).splitlines()[0]
        message = f"Malformed YAML in {path} at {location}: {detail}"
    else:
        message = f"Malformed YAML in {path}: {exc}"
    return ValidationError(message)


class RobustDataLoader:
    """
    Implements Thor Guardian's principle of 'Járngreipr' (Iron Gloves) for safe handling
    of potentially corrupt or varied data structures.
    """

    @staticmethod
    def load_json(
        filepath: Union[str, Path], fallback: Any = None, *, strict: bool = False
    ) -> Any:
        """Safely loads JSON data.

        ``strict=False`` (default) preserves the historical contract: missing,
        empty, or malformed files yield ``fallback``. ``strict=True`` hardens
        the load: a missing file raises ``FileNotFoundError`` naming the
        expected path, malformed JSON raises ``json.JSONDecodeError`` (which
        already carries line/column info), and an empty file yields an empty
        mapping ``{}``. Files larger than :data:`MAX_RESOURCE_BYTES` are
        rejected with ``ValidationError`` in both modes, before parsing.
        """
        path = Path(filepath)
        if not path.exists():
            if strict:
                raise FileNotFoundError(f"resource file not found: {path}")
            logger.warning(f"File not found: {path}")
            return fallback

        _check_size(path)

        try:
            content = path.read_text(encoding="utf-8").strip()
            if not content:
                if strict:
                    # Documented: an empty file is an empty mapping, not a crash.
                    return {}
                logger.warning(f"File is empty: {path}")
                return fallback
            return json.loads(content)
        except json.JSONDecodeError as e:
            if strict:
                raise
            logger.error(f"JSON Parsing Error in {path}: {e}")
            publish_sync("ui_notification", title="Data Error", message=f"Failed to parse {path.name}.", severity="error")
            return fallback
        except Exception as e:
            if strict:
                raise
            logger.error(f"Unexpected error reading {path}: {e}")
            return fallback

    @staticmethod
    def load_markdown(
        filepath: Union[str, Path], fallback: str = "", *, strict: bool = False
    ) -> str:
        """Safely loads Markdown data.

        ``strict=True`` raises ``FileNotFoundError`` naming the expected path
        for a missing file instead of returning ``fallback``. Files larger
        than :data:`MAX_RESOURCE_BYTES` are rejected with ``ValidationError``
        in both modes, before reading.
        """
        path = Path(filepath)
        if not path.exists():
            if strict:
                raise FileNotFoundError(f"resource file not found: {path}")
            return fallback

        _check_size(path)

        try:
            return path.read_text(encoding="utf-8")
        except Exception as e:
            if strict:
                raise
            logger.error(f"Unexpected error reading Markdown {path}: {e}")
            return fallback

    @staticmethod
    def load_yaml(
        filepath: Union[str, Path], fallback: Any = None, *, strict: bool = False
    ) -> Any:
        """Safely loads YAML data, if pyyaml is installed.

        ``strict=False`` (default) preserves the historical contract: missing
        or malformed files yield ``fallback``. ``strict=True`` hardens the
        load: a missing file raises ``FileNotFoundError`` naming the expected
        path, malformed YAML raises ``ValidationError`` carrying the file
        path plus line/column info, and an empty (or content-free, e.g.
        comments-only) file yields an empty mapping ``{}`` (documented)
        instead of crashing or returning ``None``. Files
        larger than :data:`MAX_RESOURCE_BYTES` are rejected with
        ``ValidationError`` in both modes, before parsing.
        """
        path = Path(filepath)
        if not path.exists():
            if strict:
                raise FileNotFoundError(f"resource file not found: {path}")
            return fallback

        _check_size(path)

        try:
            import yaml
            content = path.read_text(encoding="utf-8")
            if strict and not content.strip():
                # Documented: an empty file is an empty mapping, not a crash.
                return {}
            parsed = yaml.safe_load(content)
            if strict and parsed is None:
                # Content-free YAML (e.g. comments only) is also an empty mapping.
                return {}
            return parsed
        except ImportError:
            if strict:
                raise
            logger.error("PyYAML is not installed. Cannot load YAML.")
            return fallback
        except ValidationError:
            raise
        except Exception as e:
            if strict:
                # Import here so yaml.YAMLError need not be imported at module
                # scope when PyYAML is absent; any parse failure becomes a
                # ValidationError with file path and line/column info.
                try:
                    import yaml as _yaml

                    if isinstance(e, _yaml.YAMLError):
                        raise _yaml_error(path, e) from e
                except ImportError:
                    pass
                raise _yaml_error(path, e) from e
            logger.error(f"Error reading YAML {path}: {e}")
            return fallback

    @staticmethod
    def read_any(filepath: Union[str, Path], *, strict: bool = False) -> Any:
        """Autodetects format and safely loads data.

        ``strict`` is forwarded to the format-specific loader, enabling the
        hardened contract (``FileNotFoundError`` on missing files,
        ``ValidationError`` on malformed YAML, empty file as empty mapping).
        """
        path = Path(filepath)
        if path.suffix == ".json":
            return RobustDataLoader.load_json(path, strict=strict)
        elif path.suffix in [".yaml", ".yml"]:
            return RobustDataLoader.load_yaml(path, strict=strict)
        elif path.suffix in [".md", ".txt"]:
            return RobustDataLoader.load_markdown(path, strict=strict)
        else:
            # Fallback to plain text
            try:
                if not path.exists():
                    if strict:
                        raise FileNotFoundError(f"resource file not found: {path}")
                    return None
                _check_size(path)
                return path.read_text(encoding="utf-8")
            except (FileNotFoundError, ValidationError):
                raise
            except Exception as e:
                if strict:
                    raise
                logger.error(f"Failed to read file {path}: {e}")
                return None

# Singleton data loader instance
data_loader = RobustDataLoader()
