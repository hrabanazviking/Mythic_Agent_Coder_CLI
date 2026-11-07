"""The stash shelf (roadmap slice M-088).

Part IV - The Editor's Hand. The roadmap's words:
quick-shelve work-in-progress by name, restore
across sessions; the shelf survives crashes
(journal-backed).

What already shipped, and what this slice adds:

* Checkpoints (M-075) freeze the whole working tree
  under a name so it can be restored later, and the
  EditJournal (M-072's line) records individual edits
  so one edit can be undone. Neither is a quick
  shelf for work-in-progress: a checkpoint captures
  everything, clean or not, and stays the tree's
  head; there was nowhere to put a half-finished
  change down by name, go back to a clean tree, and
  pick that same change up again in another session.
* This slice is that shelf. Shelving compares the
  working tree against its base (the last clean
  state), captures only the difference - files added,
  modified, or deleted, with their contents - under
  a name the user chooses, and the working tree goes
  back to the base. Restoring judges the tree as it
  stands now: if a shelved file's path has moved
  since the shelve, the restore refuses and names
  the conflicted files, unless the user discards
  those changes on purpose. The shelf itself is an
  append-only journal of checksummed records: each
  entry is written as one JSON line carrying the
  SHA-256 of its canonical form, so the shelf can be
  rebuilt after a crash, and a torn or corrupted
  line is counted and skipped, never silently
  applied. This module is the pure layer: it works
  on in-memory trees (path -> text) and journal
  text, and writes no file - the agent layer owns
  the real tree, the real journal file, and the
  session events.

Honesty rules, enforced here and pinned by tests:

* **Shelving nothing refuses.** If the working tree
  matches its base, there is no work-in-progress to
  shelve; the refusal says so in plain words rather
  than shelving an empty entry under a real name.
* **Names are unique and the user's own words.** A
  shelf name is free text, validated only for
  emptiness, length, and control characters; a
  second shelve under a name already on the shelf
  refuses and says so.
* **Restore judges a moved tree, and refuses
  honestly.** A path the entry touches whose current
  content differs from the base the entry was
  shelved against is a conflict: restore names every
  conflicted path and changes nothing, unless the
  caller discards those changes on purpose - counted
  in the call, never hidden.
* **The journal is checksummed, line by line.** An
  entry only joins the shelf when its line parses
  and its checksum matches; a torn final line from
  a crash is reported as a corrupt line, not loaded
  as a half entry and not fatal to the whole shelf.
* **The setting is a gate, not a guess.** With
  ``stash_shelf`` off, shelving and restoring
  through the agent layer refuse and say so; the
  shelf stays readable. A malformed stored setting
  raises, never defaults silently.
"""

from __future__ import annotations

__all__ = [
    "MAX_NAME_CHARS",
    "PLAIN_EXPLANATION",
    "SETTING_KEY",
    "SHORT_HASH_LEN",
    "STASH_SHELF_SLICE",
    "USAGE",
    "Any",
    "BoolChange",
    "Dict",
    "FileChange",
    "List",
    "Optional",
    "Shelf",
    "ShelfEntry",
    "Tuple",
    "build_entry",
    "clean_tree",
    "content_anchor",
    "enabled_from_config",
    "entry_from_record",
    "format_setting_change",
    "format_shelf_entry",
    "format_shelf_list",
    "format_stash_shelf",
    "parse_stash_args",
    "restore_conflicts",
    "restore_tree",
    "set_enabled",
    "validate_name",
]

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

STASH_SHELF_SLICE = "M-088"
SETTING_KEY = "stash_shelf"
USAGE = "stash shelve <name>"
PLAIN_EXPLANATION = (
    "Work-in-progress is shelved by name and the tree "
    "goes back to clean; a shelved change restores in "
    "any later session, refuses plainly when the tree "
    "has moved under it, and the shelf itself is a "
    "checksummed journal, so it survives a crash.")
#: A shelf name is the user's words, kept short enough
#: to stay a name (checkpoints use the same spirit).
MAX_NAME_CHARS = 80
#: How many hex digits of an anchor a surface shows.
SHORT_HASH_LEN = 12

_MISSING = object()


def validate_name(raw: Any) -> str:
    """Validate one shelf name: the user's words, kept sane."""
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("shelf name must be a non-empty string")
    name = raw.strip()
    if len(name) > MAX_NAME_CHARS:
        raise ValueError(
            f"shelf name must be at most {MAX_NAME_CHARS} "
            f"characters, got {len(name)}")
    if any(ord(c) < 32 or ord(c) == 127 for c in name):
        raise ValueError("shelf name must not contain control characters")
    return name


def _validate_path(raw: Any) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("path must be a non-empty string")
    path = raw.strip()
    if path.startswith("/") or path.startswith("\\"):
        raise ValueError(f"path must be repo-relative: {raw!r}")
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ValueError(f"path must be a clean repo-relative path: {raw!r}")
    return path


def _validate_tree(raw: Any, label: str) -> Dict[str, str]:
    if not isinstance(raw, dict):
        raise ValueError(f"{label} tree must be a dict of path -> text")
    clean: Dict[str, str] = {}
    for path, text in raw.items():
        clean_path = _validate_path(path)
        if clean_path in clean:
            raise ValueError(f"{label} tree names {clean_path!r} twice")
        if not isinstance(text, str):
            raise ValueError(f"{label} tree text for {clean_path!r} must be a string")
        clean[clean_path] = text
    return clean


def content_anchor(text: str) -> str:
    """The full SHA-256 anchor of one file's exact text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class FileChange:
    """One file's shelved change, with both sides' text."""

    path: str
    kind: str
    base_content: Optional[str]
    shelf_content: Optional[str]

    @property
    def base_anchor(self) -> Optional[str]:
        return None if self.base_content is None else content_anchor(self.base_content)

    @property
    def shelf_anchor(self) -> Optional[str]:
        return None if self.shelf_content is None else content_anchor(self.shelf_content)

    def record(self) -> Dict[str, Any]:
        return {"path": self.path, "kind": self.kind,
                "base_content": self.base_content,
                "shelf_content": self.shelf_content,
                "base_anchor": self.base_anchor,
                "shelf_anchor": self.shelf_anchor}


@dataclass(frozen=True)
class ShelfEntry:
    """One named work-in-progress entry on the shelf."""

    name: str
    session_id: Optional[str]
    created_at: str
    changes: Tuple[FileChange, ...]

    @property
    def file_count(self) -> int:
        return len(self.changes)

    @property
    def total_bytes(self) -> int:
        total = 0
        for change in self.changes:
            if change.shelf_content is not None:
                total += len(change.shelf_content.encode("utf-8"))
        return total

    def record(self) -> Dict[str, Any]:
        return {"type": "stash_shelf_entry", "slice": STASH_SHELF_SLICE,
                "name": self.name, "session_id": self.session_id,
                "created_at": self.created_at,
                "changes": [c.record() for c in self.changes]}


def build_entry(name: Any, base: Any, working: Any,
                session_id: Optional[str] = None,
                created_at: Optional[str] = None) -> ShelfEntry:
    """Build one shelf entry from a base/working tree pair.

    Only the difference is shelved: a path added in
    the working tree, modified from the base, or
    deleted from it. If there is no difference there
    is nothing to shelve, and the refusal says so.
    """
    clean_name = validate_name(name)
    if session_id is not None and not isinstance(session_id, str):
        raise ValueError("session_id must be a string or None")
    base_tree = _validate_tree(base, "base")
    working_tree = _validate_tree(working, "working")
    changes: List[FileChange] = []
    for path in sorted(set(base_tree) | set(working_tree)):
        before = base_tree.get(path, _MISSING)
        after = working_tree.get(path, _MISSING)
        if before is _MISSING and after is not _MISSING:
            changes.append(FileChange(path=path, kind="added",
                                      base_content=None,
                                      shelf_content=after))
        elif after is _MISSING and before is not _MISSING:
            changes.append(FileChange(path=path, kind="deleted",
                                      base_content=before,
                                      shelf_content=None))
        elif before != after:
            changes.append(FileChange(path=path, kind="modified",
                                      base_content=before,
                                      shelf_content=after))
    if not changes:
        raise ValueError(
            "nothing to shelve: the working tree matches its "
            "base, so there is no work-in-progress under "
            f"the name {clean_name!r}")
    stamp = created_at or datetime.now(timezone.utc).isoformat()
    if not isinstance(stamp, str) or not stamp.strip():
        raise ValueError("created_at must be an ISO timestamp string")
    return ShelfEntry(name=clean_name, session_id=session_id,
                      created_at=stamp, changes=tuple(changes))


def _check_entry_against_base(entry: ShelfEntry, base_tree: Dict[str, str]) -> None:
    for change in entry.changes:
        current = base_tree.get(change.path, _MISSING)
        expected = _MISSING if change.base_content is None else change.base_content
        if current != expected:
            raise ValueError(
                f"shelf entry {entry.name!r} was not shelved "
                f"against this base: {change.path} differs")


def clean_tree(base: Any, entry: ShelfEntry) -> Dict[str, str]:
    """The tree after shelving *entry*: its base, exactly.

    The entry is judged against the base first - an
    entry shelved against a different base refuses
    rather than pretending to clean this tree.
    """
    base_tree = _validate_tree(base, "base")
    _check_entry_against_base(entry, base_tree)
    return dict(base_tree)


def restore_conflicts(entry: ShelfEntry, base: Any,
                      working: Any) -> List[str]:
    """Paths where *working* has moved since the shelve.

    A path conflicts when its current content is not
    the base content the entry was shelved against:
    restoring would silently overwrite that movement.
    """
    base_tree = _validate_tree(base, "base")
    working_tree = _validate_tree(working, "working")
    _check_entry_against_base(entry, base_tree)
    conflicts: List[str] = []
    for change in entry.changes:
        current = working_tree.get(change.path, _MISSING)
        expected = _MISSING if change.base_content is None else change.base_content
        if current != expected:
            conflicts.append(change.path)
    return conflicts


def restore_tree(entry: ShelfEntry, base: Any, working: Any,
                 discard: bool = False) -> Dict[str, str]:
    """Apply *entry*'s changes onto *working*, or refuse.

    With conflicts present and ``discard`` false, the
    refusal names every conflicted path and changes
    nothing. With ``discard`` true those paths are
    overwritten on purpose - the caller's word, in
    the open.
    """
    if not isinstance(discard, bool):
        raise ValueError("discard must be true or false")
    working_tree = _validate_tree(working, "working")
    conflicts = restore_conflicts(entry, base, working)
    if conflicts and not discard:
        raise ValueError(
            f"cannot restore {entry.name!r}: the tree has "
            f"moved on {', '.join(conflicts)} since the "
            "shelve; shelve or undo those changes first, "
            "or restore with discard to overwrite them "
            "on purpose")
    restored = dict(working_tree)
    for change in entry.changes:
        if change.kind == "deleted":
            restored.pop(change.path, None)
        else:
            restored[change.path] = change.shelf_content
    return restored


def entry_from_record(record: Any) -> ShelfEntry:
    """Rebuild one entry from its journal record, validated."""
    if not isinstance(record, dict):
        raise ValueError("shelf entry record must be a dict")
    if record.get("type") != "stash_shelf_entry":
        raise ValueError("record is not a stash shelf entry")
    if record.get("slice") != STASH_SHELF_SLICE:
        raise ValueError("record is not an M-088 stash shelf entry")
    name = validate_name(record.get("name"))
    session_id = record.get("session_id")
    if session_id is not None and not isinstance(session_id, str):
        raise ValueError("session_id must be a string or None")
    created_at = record.get("created_at")
    if not isinstance(created_at, str) or not created_at.strip():
        raise ValueError("created_at must be an ISO timestamp string")
    raw_changes = record.get("changes")
    if not isinstance(raw_changes, list) or not raw_changes:
        raise ValueError("shelf entry must carry at least one change")
    changes: List[FileChange] = []
    seen = set()
    for raw in raw_changes:
        if not isinstance(raw, dict):
            raise ValueError("shelf change must be a dict")
        path = _validate_path(raw.get("path"))
        if path in seen:
            raise ValueError(f"shelf entry names {path!r} twice")
        seen.add(path)
        kind = raw.get("kind")
        base_content = raw.get("base_content")
        shelf_content = raw.get("shelf_content")
        if kind == "added":
            if base_content is not None or not isinstance(shelf_content, str):
                raise ValueError(f"added change for {path!r} is malformed")
        elif kind == "deleted":
            if shelf_content is not None or not isinstance(base_content, str):
                raise ValueError(f"deleted change for {path!r} is malformed")
        elif kind == "modified":
            if not isinstance(base_content, str) or not isinstance(shelf_content, str):
                raise ValueError(f"modified change for {path!r} is malformed")
            if base_content == shelf_content:
                raise ValueError(f"modified change for {path!r} changes nothing")
        else:
            raise ValueError(f"unknown shelf change kind {kind!r}")
        change = FileChange(path=path, kind=kind,
                            base_content=base_content,
                            shelf_content=shelf_content)
        if raw.get("base_anchor") != change.base_anchor:
            raise ValueError(f"base anchor mismatch for {path!r}")
        if raw.get("shelf_anchor") != change.shelf_anchor:
            raise ValueError(f"shelf anchor mismatch for {path!r}")
        changes.append(change)
    return ShelfEntry(name=name, session_id=session_id,
                      created_at=created_at, changes=tuple(changes))


def _checksum(record: Dict[str, Any]) -> str:
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":"),
                           allow_nan=False, ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class Shelf:
    """The shelf itself: named entries, journal-backed.

    The journal form is one JSON line per entry, each
    line carrying the checksum of the entry record it
    holds. Rebuilding from journal text counts the
    lines it could not trust and skips them - a torn
    last line from a crash costs that entry, never
    the whole shelf, and the loss is reported, never
    hidden.
    """

    def __init__(self, entries: Optional[List[ShelfEntry]] = None) -> None:
        self._entries: List[ShelfEntry] = []
        for entry in entries or []:
            self.shelve(entry)

    def __len__(self) -> int:
        return len(self._entries)

    def entries(self) -> List[ShelfEntry]:
        return list(self._entries)

    def names(self) -> List[str]:
        return [entry.name for entry in self._entries]

    def get(self, name: Any) -> ShelfEntry:
        clean = validate_name(name)
        for entry in self._entries:
            if entry.name == clean:
                return entry
        raise ValueError(f"no shelf entry named {clean!r}")

    def shelve(self, entry: ShelfEntry) -> ShelfEntry:
        if not isinstance(entry, ShelfEntry):
            raise ValueError("only a built shelf entry can be shelved")
        if entry.name in self.names():
            raise ValueError(
                f"the shelf already holds an entry named "
                f"{entry.name!r}; restore or drop it first, "
                "or shelve under another name")
        self._entries.append(entry)
        return entry

    def drop(self, name: Any) -> ShelfEntry:
        entry = self.get(name)
        self._entries.remove(entry)
        return entry

    def restore(self, name: Any, base: Any, working: Any,
                discard: bool = False,
                keep: bool = False) -> Dict[str, str]:
        """Restore one entry's tree; a kept entry stays shelved."""
        if not isinstance(keep, bool):
            raise ValueError("keep must be true or false")
        entry = self.get(name)
        restored = restore_tree(entry, base, working, discard=discard)
        if not keep:
            self._entries.remove(entry)
        return restored

    def to_journal_text(self) -> str:
        lines = []
        for entry in self._entries:
            record = entry.record()
            lines.append(json.dumps(
                {"record": record, "checksum": _checksum(record)},
                sort_keys=True, ensure_ascii=True))
        return "".join(line + "\n" for line in lines)

    @classmethod
    def from_journal_text(cls, text: Any) -> Tuple["Shelf", int]:
        """Rebuild a shelf from journal text.

        Returns ``(shelf, corrupt_lines)``: every line
        that fails to parse, fails its checksum, fails
        validation, or repeats a name is skipped and
        counted, so the caller can report the loss.
        """
        if not isinstance(text, str):
            raise ValueError("journal text must be a string")
        shelf = cls()
        corrupt = 0
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                if not isinstance(payload, dict):
                    raise ValueError("journal line is not an object")
                record = payload.get("record")
                if not isinstance(record, dict):
                    raise ValueError("journal line carries no record")
                if payload.get("checksum") != _checksum(record):
                    raise ValueError("journal line checksum mismatch")
                shelf.shelve(entry_from_record(record))
            except (ValueError, TypeError, KeyError):
                corrupt += 1
        return shelf, corrupt


def enabled_from_config(config: Dict[str, Any]) -> bool:
    """The stash_shelf setting stored in *config*.

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
        return {"type": "stash_shelf_setting_changed",
                "from": self.before, "to": self.after}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "stash_shelf_setting_changed",
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
            f"the stash shelf is already "
            f"{'on' if before else 'off'}")
    return enabled, BoolChange(before=before, after=enabled)


# ---------------------------------------------------------------------
# The /stash surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------

def parse_stash_args(args: str) -> Dict[str, Any]:
    """Parse the /stash grammar both surfaces share.

    ``show`` / ``list`` / ``on`` / ``off`` stand alone;
    ``shelve``, ``restore``, and ``drop`` take the
    entry's name as the rest of the line - names are
    free text, so every remaining word joins the name.
    """
    text = (args or "").strip()
    if not text or text in ("show", "list"):
        return {"action": "show"}
    if text == "on":
        return {"action": "on"}
    if text == "off":
        return {"action": "off"}
    parts = text.split(None, 1)
    if parts[0] in ("shelve", "restore", "drop") and len(parts) == 2:
        return {"action": parts[0], "name": validate_name(parts[1])}
    raise ValueError(
        f"usage: {USAGE} (or: stash show|on|off, "
        "stash restore <name>, stash drop <name>)")


def format_setting_change(record: Dict[str, Any]) -> str:
    state = "on" if record.get("to") else "off"
    return f"The stash shelf is now {state}."


def format_shelf_entry(entry: Any) -> str:
    """Format one entry, dataclass or record dict."""
    if isinstance(entry, dict):
        record = entry
        name = record.get("name")
        changes = record.get("changes") or []
        lines = [f"{name}: {len(changes)} file(s) shelved"]
        for change in changes:
            lines.append(f"  {change.get('kind')}: {change.get('path')}")
        return "\n".join(lines)
    lines = [f"{entry.name}: {entry.file_count} file(s) shelved, "
             f"{entry.total_bytes} byte(s) of work-in-progress"]
    for change in entry.changes:
        anchor = change.shelf_anchor
        note = (f" (anchor {anchor[:SHORT_HASH_LEN]})"
                if anchor else "")
        lines.append(f"  {change.kind}: {change.path}{note}")
    return "\n".join(lines)


def format_shelf_list(shelf: Any) -> str:
    """The shelf's contents, in plain words."""
    entries = shelf.entries() if isinstance(shelf, Shelf) else list(shelf)
    if not entries:
        return "The stash shelf is empty."
    lines = [f"{len(entries)} entr(ies) on the stash shelf:"]
    for entry in entries:
        if isinstance(entry, dict):
            lines.append(format_shelf_entry(entry))
        else:
            lines.append(
                f"{entry.name}: {entry.file_count} file(s), "
                f"{entry.total_bytes} byte(s), shelved "
                f"{entry.created_at}")
    return "\n".join(lines)


def format_stash_shelf(config: Dict[str, Any]) -> str:
    """The whole slice, in plain words, for /stash.

    Built from build_entry() / restore_tree(), so the
    show surface exercises the shelf road it names: a
    change is shelved, the tree stands clean, and the
    change restores whole.
    """
    enabled = enabled_from_config(config)
    lines = ["The stash shelf (M-088) - " + PLAIN_EXPLANATION, ""]
    lines.append(f"Setting: {'on' if enabled else 'off'} "
                 f"({SETTING_KEY}).")
    lines.append("")
    base = {"src/app.py": "x = 1\n"}
    working = {"src/app.py": "x = 2\n", "src/new.py": "y = 3\n"}
    entry = build_entry("half-done fix", base, working,
                        created_at="2026-01-01T00:00:00+00:00")
    lines.append(format_shelf_entry(entry))
    lines.append("After shelving, the tree stands at its base.")
    restored = restore_tree(entry, base, clean_tree(base, entry))
    lines.append("Restored whole: "
                 + ", ".join(sorted(restored)) + ".")
    lines.append("")
    lines.append("Usage: /stash | /stash on | /stash off | "
                 "/stash shelve <name> | /stash restore <name> | "
                 "/stash drop <name>")
    return "\n".join(lines)
