"""Rename/move files as first-class edits (roadmap slice M-085).

Part IV - The Editor's Hand. The roadmap's words:
rename/move files as first-class edits (history-preserving
git mv, references updated via Part III's graph).

What already shipped, and what this slice adds:

* Renaming a file used to be invisible work: a shell
  ``mv`` here, a few import fixes there, nothing named,
  nothing journaled, and the file's history quietly
  severed if plain ``mv`` rather than ``git mv`` did the
  moving. References in other files were found by luck
  and grep, or not found at all.
* Part III's symbol graph (``context/symbol_graph.py``)
  already knows which files import and reference which:
  its file edges and import edges say exactly whose text
  can mention a moved file's path or module name.
* This slice is the pure planning layer for a move: one
  source path, one destination path, validated before
  anything moves; the history-preserving command is
  ``git mv`` and nothing else; the reference updates are
  computed in memory from the referencing files' true
  current text, as exact-token replacements of the old
  path and (for Python) the old dotted module name -
  every replacement counted, and a referencing file the
  graph names but whose text holds no exact token is
  reported as a warning, never silently passed over.
  This module moves no file and writes no file: the
  agent layer executes the plan (git mv, then journaled
  writes for the reference updates), so a move is named,
  recorded, and undoable like any other edit.

Honesty rules, enforced here and pinned by tests:

* **History is preserved or the move refuses.** The
  only move command this layer plans is ``git mv``.
  A source that is not tracked, or a destination whose
  parent is not tracked-or-creatable by git, is the
  executing layer's fact to check; the plan itself
  never degrades to a plain filesystem rename.
* **Nothing overwrites.** A destination that already
  exists refuses at plan time. A move onto itself, a
  move of a directory into itself, an absolute path,
  and a path escaping the worktree (``..``) all refuse.
* **References update by exact token, never by fuzz.**
  The old repo-relative path and the old dotted module
  name are replaced as whole tokens only; a substring
  inside a longer name is left alone and counted as
  untouched. Updated texts are computed whole, in
  memory, before any write - one file that cannot be
  updated cleanly refuses the whole plan.
* **The graph decides who is checked.** Only files the
  caller names as referencing the source (from Part
  III's graph) are candidates for updates, plus any
  file whose text the caller supplies. A file that
  references the source in a form this layer does not
  rewrite (a computed path, a string built at runtime)
  surfaces as a warning on the plan, never as silence.
* **The setting is a gate, not a guess.** With
  ``rename_move`` off, moves through the agent layer
  refuse and say so; the pure planning maths stays
  available. A malformed stored setting raises.
"""

from __future__ import annotations

__all__ = [
    "PLAIN_EXPLANATION",
    "RENAME_MOVE_SLICE",
    "SETTING_KEY",
    "USAGE",
    "Any",
    "BoolChange",
    "Dict",
    "List",
    "Mapping",
    "MovePlan",
    "Optional",
    "ReferenceUpdate",
    "Sequence",
    "Tuple",
    "enabled_from_config",
    "format_move_plan",
    "format_move_record",
    "format_rename_move",
    "format_setting_change",
    "module_name_for",
    "parse_rename_args",
    "plan_move",
    "set_enabled",
]

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

RENAME_MOVE_SLICE = "M-085"
SETTING_KEY = "rename_move"
USAGE = "rename <old-path> <new-path>"
PLAIN_EXPLANATION = (
    "Renaming or moving a file is an edit with a name: "
    "git keeps the file's history, and every file that "
    "points at the old place is updated to point at the "
    "new one - planned first, counted, and journaled.")


def _validate_path(raw: Any, label: str) -> str:
    """One repo-relative POSIX path, or a plain refusal."""
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"{label} path must be a non-empty string")
    path = raw.strip()
    if path.startswith("/") or path.startswith("\\"):
        raise ValueError(f"{label} path must be repo-relative: {raw!r}")
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ValueError(
            f"{label} path must be a clean repo-relative path: {raw!r}")
    return path


def module_name_for(path: str) -> Optional[str]:
    """The dotted module name a Python path answers to.

    ``pkg/mod.py`` is ``pkg.mod``; ``pkg/__init__.py``
    is ``pkg``; a non-Python path has no module name.
    """
    if not path.endswith(".py"):
        return None
    stem = path[:-3]
    if stem.endswith("/__init__"):
        stem = stem[: -len("/__init__")]
    if stem == "__init__":
        return None
    return stem.replace("/", ".")


@dataclass(frozen=True)
class ReferenceUpdate:
    """One referencing file's computed new text."""

    path: str
    replacements: int
    new_text: str

    def record(self) -> Dict[str, Any]:
        return {"path": self.path, "replacements": self.replacements}


@dataclass(frozen=True)
class MovePlan:
    """A validated move, planned whole before anything moves."""

    source: str
    destination: str
    is_directory: bool
    updates: Tuple[ReferenceUpdate, ...]
    warnings: Tuple[str, ...]

    @property
    def git_argv(self) -> Tuple[str, ...]:
        """The only move command: history-preserving git mv."""
        return ("git", "mv", self.source, self.destination)

    @property
    def total_replacements(self) -> int:
        return sum(u.replacements for u in self.updates)

    def record(self) -> Dict[str, Any]:
        return {
            "type": "file_moved",
            "slice": RENAME_MOVE_SLICE,
            "source": self.source,
            "destination": self.destination,
            "is_directory": self.is_directory,
            "command": list(self.git_argv),
            "reference_updates": [u.record() for u in self.updates],
            "warnings": list(self.warnings),
        }


def _replace_token(text: str, old: str, new: str) -> Tuple[str, int]:
    """Replace whole-token occurrences of *old* with *new*.

    A token boundary is any character that cannot be part
    of a path or module name (not alnum, ``_``, ``-``,
    ``.``, ``/``). Substring hits inside a longer name
    are not replacements and are never counted.
    """
    if not old:
        return text, 0
    out: List[str] = []
    count = 0
    i = 0
    width = len(old)
    boundary = set(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789_-./")
    while True:
        j = text.find(old, i)
        if j < 0:
            out.append(text[i:])
            break
        before = text[j - 1] if j > 0 else ""
        after = text[j + width] if j + width < len(text) else ""
        if before in boundary or after in boundary:
            out.append(text[i:j + width])
            i = j + width
            continue
        out.append(text[i:j])
        out.append(new)
        count += 1
        i = j + width
    return "".join(out), count


def plan_move(source: Any, destination: Any, *,
              existing: Sequence[str],
              referencing: Sequence[str] = (),
              texts: Mapping[str, str] = {},
              is_directory: bool = False) -> MovePlan:
    """Plan one rename/move, or refuse plainly.

    *existing* names every path currently in the tree
    (the caller's fact, from disk). *referencing* names
    the files Part III's graph says point at the source;
    *texts* carries those files' true current text.
    Reference updates replace the old path token and,
    for Python sources, the old dotted module token.
    A referencing file with no supplied text, or whose
    text holds no exact token, becomes a warning.
    """
    src = _validate_path(source, "source")
    dst = _validate_path(destination, "destination")
    if src == dst:
        raise ValueError(f"source and destination are the same: {src}")
    known = set(existing)
    if src not in known:
        raise ValueError(f"source does not exist: {src}")
    if dst in known:
        raise ValueError(f"destination already exists: {dst}")
    if is_directory and dst.startswith(src + "/"):
        raise ValueError(
            f"a directory cannot move into itself: {src} -> {dst}")
    old_module = module_name_for(src)
    new_module = module_name_for(dst)
    updates: List[ReferenceUpdate] = []
    warnings: List[str] = []
    for path in referencing:
        if path == src:
            continue
        if path not in texts:
            warnings.append(
                f"{path} references {src} per the graph, but its "
                f"text was not supplied - not updated")
            continue
        text = texts[path]
        new_text, n_path = _replace_token(text, src, dst)
        total = n_path
        if old_module and new_module:
            new_text, n_mod = _replace_token(new_text, old_module, new_module)
            total += n_mod
        if total == 0:
            warnings.append(
                f"{path} references {src} per the graph, but no "
                f"exact path or module token was found - not updated")
            continue
        updates.append(ReferenceUpdate(
            path=path, replacements=total, new_text=new_text))
    return MovePlan(source=src, destination=dst,
                    is_directory=bool(is_directory),
                    updates=tuple(updates), warnings=tuple(warnings))


def enabled_from_config(config: Dict[str, Any]) -> bool:
    """The rename/move setting stored in *config*.

    Absent means True (the setting ships on). A stored
    value that is not a bool raises - never guessed at.
    """
    raw = config.get(SETTING_KEY, True)
    if not isinstance(raw, bool):
        raise ValueError(
            f"{SETTING_KEY} must be true or false, "
            f"got {type(raw).__name__}")
    return raw


@dataclass(frozen=True)
class BoolChange:
    """A recorded change of the gate setting."""

    before: bool
    after: bool

    def event(self) -> Dict[str, Any]:
        return {"type": "rename_move_setting_changed",
                "from": self.before, "to": self.after}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "rename_move_setting_changed",
                "from": self.before, "to": self.after,
                "session_id": session_id, "journaled": journaled}


def set_enabled(config: Dict[str, Any],
                enabled: Any) -> Tuple[bool, BoolChange]:
    """Validate a gate change against *config*, purely."""
    if not isinstance(enabled, bool):
        raise ValueError(
            f"{SETTING_KEY} is turned on or off; got {enabled!r}")
    before = enabled_from_config(config)
    if enabled == before:
        raise ValueError(
            f"rename/move is already {'on' if before else 'off'}")
    return enabled, BoolChange(before=before, after=enabled)


# ---------------------------------------------------------------------
# The /rename surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------

def parse_rename_args(args: str) -> Dict[str, Any]:
    """Parse the /rename grammar both surfaces share.

    ``show`` / ``on`` / ``off`` steer the gate; exactly
    two path words plan a move; anything else is a
    usage error naming the grammar.
    """
    words = (args or "").split()
    if not words or words == ["show"]:
        return {"action": "show"}
    if words == ["on"]:
        return {"action": "on"}
    if words == ["off"]:
        return {"action": "off"}
    if len(words) == 2:
        return {"action": "move",
                "source": _validate_path(words[0], "source"),
                "destination": _validate_path(words[1], "destination")}
    raise ValueError(f"usage: {USAGE} (or: rename show|on|off)")


def format_setting_change(record: Dict[str, Any]) -> str:
    state = "on" if record.get("to") else "off"
    return f"Rename/move is now {state}."


def format_move_plan(plan: MovePlan) -> str:
    """The plan in plain words, for either surface."""
    lines = [
        f"Move: {plan.source} -> {plan.destination}",
        f"History: preserved by {' '.join(plan.git_argv)}",
    ]
    if plan.updates:
        lines.append(
            f"Reference updates: {len(plan.updates)} file(s), "
            f"{plan.total_replacements} replacement(s)")
        for update in plan.updates:
            lines.append(
                f"  {update.path}: {update.replacements} replacement(s)")
    else:
        lines.append("Reference updates: none")
    for warning in plan.warnings:
        lines.append(f"Warning: {warning}")
    return "\n".join(lines)


def format_move_record(record: Dict[str, Any]) -> str:
    """An executed move's record, in plain words."""
    lines = [
        f"Moved: {record.get('source')} -> {record.get('destination')}",
        "History: preserved by git mv",
    ]
    updates = record.get("reference_updates") or []
    if updates:
        total = sum(u.get("replacements", 0) for u in updates)
        lines.append(
            f"Reference updates: {len(updates)} file(s), "
            f"{total} replacement(s)")
        for update in updates:
            lines.append(
                f"  {update.get('path')}: "
                f"{update.get('replacements')} replacement(s)")
    else:
        lines.append("Reference updates: none")
    for warning in record.get("warnings") or []:
        lines.append(f"Warning: {warning}")
    if record.get("graph_warning"):
        lines.append(f"Warning: {record['graph_warning']}")
    return "\n".join(lines)


def format_rename_move(config: Dict[str, Any]) -> str:
    """The whole slice, in plain words, for /rename.

    Built from plan_move() / format_move_plan(), so the
    show surface exercises the planning road it names:
    a worked example in which app.py's import of the
    moved module is rewritten by exact token.
    """
    enabled = enabled_from_config(config)
    lines = ["Rename/move files (M-085) — "
             + PLAIN_EXPLANATION, ""]
    lines.append(f"Setting: {'on' if enabled else 'off'} "
                 f"({SETTING_KEY}).")
    lines.append("")
    plan = plan_move(
        "pkg/mod.py", "pkg/renamed.py",
        existing=["pkg/mod.py", "pkg/__init__.py", "app.py"],
        referencing=["app.py"],
        texts={"app.py": "import pkg.mod\n"})
    lines.append("A sample move, as it is planned:")
    lines.append(format_move_plan(plan))
    lines.append("")
    lines.append("Usage: /rename | /rename on | /rename off | "
                 "/rename <old-path> <new-path>")
    return "\n".join(lines)
