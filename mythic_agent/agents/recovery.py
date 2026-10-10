"""Error recovery intelligence for the Mythic agent (Slice 20).

When a tool call fails, :func:`analyze_failure` classifies the failure
into a :class:`RecoveryStrategy` and :func:`suggest_fix` proposes
corrected arguments where a deterministic correction exists
(e.g. a mistyped path resolved via fuzzy matching).
"""

__all__ = [
    "Any",
    "Enum",
    "Optional",
    "Path",
    "RecoveryStrategy",
    "analyze_failure",
    "fuzzy_find",
    "suggest_fix",
]

from enum import Enum
from pathlib import Path
from typing import Any, Optional

from ..tools.smart_files import fuzzy_find

__all__ = [
    "RecoveryStrategy",
    "analyze_failure",
    "suggest_fix",
]

#: Tools whose arguments carry a filesystem path that can be repaired.
_PATH_TOOLS: dict[str, str] = {
    "read_file": "path",
    "write_file": "path",
    "list_dir": "path",
    "replace_file_content": "path",
    "grep_search": "path",
}

#: Errors that mean "the same call will never succeed".
_ABORT_SIGNALS = (
    "permission denied", "permissionerror", "operation not permitted",
    "read-only", "read only", "access is denied",
)

#: Errors that mean "the target is wrong, try a nearby alternative".
_PATH_SIGNALS = (
    "no such file", "filenotfound", "not found", "does not exist",
    "enoent", "path does not exist",
)

#: Errors that mean "fix the arguments and try again".
_RETRY_SIGNALS = (
    "timeout", "timed out", "temporarily", "try again", "busy",
    "locked", "eagain",
)

#: Errors that mean "a different approach is needed".
_ALTERNATIVE_SIGNALS = (
    "unsupported", "not supported", "invalid argument", "bad argument",
    "unknown tool", "no such tool",
)


class RecoveryStrategy(Enum):
    """What the agent should do after a tool failure."""
    RETRY = "retry"               # Same call, transient problem.
    FIX_PATH = "fix_path"         # A path argument looks wrong; correct it.
    TRY_ALTERNATIVE = "try_alternative"  # Different tool/approach needed.
    ABORT = "abort"               # Do not retry; surface to the user.


def _norm(error: Any) -> str:
    if isinstance(error, BaseException):
        text = f"{type(error).__name__}: {error}"
    else:
        text = str(error)
    return text.lower()


def analyze_failure(tool_name: str, args: Optional[dict[str, Any]],
                    error: Any) -> RecoveryStrategy:
    """Classify a tool failure into a recovery strategy.

    Rule-based: permission problems abort, missing paths trigger path
    repair, transient errors retry, argument/tool problems try an
    alternative.
    """
    text = _norm(error)

    if isinstance(error, PermissionError) or any(s in text for s in _ABORT_SIGNALS):
        return RecoveryStrategy.ABORT

    if isinstance(error, FileNotFoundError) or any(s in text for s in _PATH_SIGNALS):
        return RecoveryStrategy.FIX_PATH

    if isinstance(error, TimeoutError) or any(s in text for s in _RETRY_SIGNALS):
        return RecoveryStrategy.RETRY

    if isinstance(error, (ValueError, TypeError, KeyError)) or any(
        s in text for s in _ALTERNATIVE_SIGNALS
    ):
        return RecoveryStrategy.TRY_ALTERNATIVE

    # Heuristic fallback: a path-like argument that does not exist on disk
    # suggests a fixable path problem.
    if args and tool_name in _PATH_TOOLS:
        key = _PATH_TOOLS[tool_name]
        candidate = args.get(key)
        if isinstance(candidate, str):
            p = Path(candidate)
            if not p.exists() and ("/" in candidate or "\\" in candidate
                                   or "." in Path(candidate).name):
                return RecoveryStrategy.FIX_PATH

    return RecoveryStrategy.TRY_ALTERNATIVE


def suggest_fix(tool_name: str, args: Optional[dict[str, Any]],
                error: Any, *, root: Optional[str | Path] = None,
                limit: int = 3) -> Optional[dict[str, Any]]:
    """Return corrected arguments for a FIX_PATH failure, else None.

    Uses fuzzy file matching against *root* (default: current directory)
    to find the most likely intended path.
    """
    args = dict(args or {})
    if analyze_failure(tool_name, args, error) != RecoveryStrategy.FIX_PATH:
        return None
    key = _PATH_TOOLS.get(tool_name)
    if key is None or key not in args:
        return None

    broken = str(args[key])
    root = Path(root) if root is not None else Path(".")
    query = Path(broken).name or broken
    matches = fuzzy_find(query, root, limit=limit)
    if not matches:
        return None

    fixed = args.copy()
    fixed[key] = str(matches[0])
    if len(matches) > 1:
        fixed["_alternatives"] = [str(m) for m in matches[1:]]
    fixed["_recovery_note"] = (
        f"repaired {key} {broken!r} -> {matches[0]!s}"
    )
    return fixed
