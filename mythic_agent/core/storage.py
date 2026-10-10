"""Private atomic state files, shared by settings and export adapters."""

__all__ = [
    "Any",
    "Path",
    "atomic_private_json",
    "atomic_private_write",
    "canonical_json",
    "decode_json_bytes",
    "strict_json_loads",
]

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def atomic_private_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(prefix=".mythic-state-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_private_json(path: Path, value: Any) -> None:
    encoded = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8")
    atomic_private_write(path, encoded)


def canonical_json(value: Any) -> str:
    """Serialize ``value`` to canonical JSON.

    Canonical form means: keys sorted, no insignificant whitespace, UTF-8
    safe (``ensure_ascii=True``), and ``allow_nan=False`` so NaN/Infinity
    payloads are rejected. Two serializations of equal values are
    byte-identical.

    Raises:
        ValueError: naming the problem when ``value`` is not JSON-serializable
            or contains non-finite floats. Never a bare ``TypeError``.
    """
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          allow_nan=False, ensure_ascii=True)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"state is not JSON-serializable: {exc}") from exc


def decode_json_bytes(raw: bytes) -> str:
    """Decode raw ``bytes`` as UTF-8 text for JSON parsing.

    Raises:
        ValueError: naming the payload when ``raw`` is not bytes or is not
            valid UTF-8. Non-UTF8 payloads are rejected, never silently
            repaired.
    """
    if not isinstance(raw, (bytes, bytearray)):
        raise ValueError(f"JSON payload must be bytes, got {type(raw).__name__}")
    try:
        return bytes(raw).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"JSON payload is not valid UTF-8: {exc}") from exc


def strict_json_loads(text: str) -> Any:
    """Parse JSON text, rejecting non-finite constants (NaN/Infinity).

    Unlike :func:`json.loads`, the ``NaN``/``Infinity``/``-Infinity``
    constants are refused so non-compliant payloads never enter state.

    Raises:
        ValueError: naming the problem for non-text input, malformed JSON,
            or non-finite constants.
    """
    if not isinstance(text, str):
        raise ValueError(f"JSON payload must be text, got {type(text).__name__}")

    def _reject_constant(token: str) -> Any:
        raise ValueError(f"non-finite JSON constant rejected: {token}")

    try:
        return json.loads(text, parse_constant=_reject_constant)
    except ValueError as exc:
        raise ValueError(f"invalid JSON payload: {exc}") from exc
