"""Undo grown up (All-Features roadmap slice M-077).

Part IV — The Editor's Hand. The roadmap's words: ``/undo``
walks edits, commands, and checkpoints as one timeline;
undo of a *command's* effects is attempted via its recorded
footprint, labelled certain or best-effort.

What already shipped, and what this slice adds:

* The EditJournal (``core/edits.py``) has always undone the
  last agent *edit* — conservatively, refusing when the file
  changed after the edit. That road is unchanged and stays
  the edit strand's engine.
* Commands run through the agent's ``run_command`` tool
  changed files with no record at all: once a command ran,
  nothing could say what it had touched, let alone put it
  back. This slice records a **footprint** for each such
  command — the workspace files it created, changed, or
  deleted, judged by a before/after snapshot of the tree,
  with the before-contents of changed files backed up —
  and undoes a command by restoring that footprint.
* Checkpoints (M-075, Checkpoints v2) are the third strand.
  M-075 is built in parallel and is NOT in this tree, so
  this slice invents none of its internals: the checkpoint
  strand is read through one clearly-named seam, the
  :class:`CheckpointTimelineSource` protocol below. An
  agent that carries a ``checkpoint_timeline_source``
  supplies checkpoint entries and checkpoint restores
  through it; an agent without one shows the checkpoint
  strand as not yet wired (DEPENDS-ON-M-075), honestly,
  while the edit and command strands walk live.

Honesty rules, enforced here and pinned by the slice's
tests:

* **One timeline, walked from the top.** Edits, commands,
  and checkpoints share one ordered timeline. Undo takes
  the newest entry; asking for a buried entry (an older
  edit under a newer command, say) refuses and names the
  newer entry that must be undone first — nothing is ever
  undone out from under a later change silently.
* **A command's undo is labelled certain or best-effort.**
  A footprint is *certain* only when the before and after
  snapshots were complete and every changed file's
  before-contents are backed up. Anything less — a tree
  too large to snapshot whole, a file too large to back
  up, an unreadable file — makes the footprint
  *best-effort*, with the reasons carried on the record,
  and the label is shown wherever the undo is offered or
  reported. Certainty is never claimed by default.
* **Command undo is all-or-nothing.** Every file in the
  footprint must still be exactly as the command left it;
  one file changed since refuses the whole undo and
  changes nothing — a partial rollback is never dressed
  up as an undo.
* **A command that changed no files is an honest entry.**
  Its footprint is empty, its undo is a certain no-change,
  and it still takes its place on the timeline.
* **The gate is a gate, not a guess.** With
  ``undo_timeline`` off, the timeline refuses at the agent
  layer and ``/undo`` keeps its original last-edit
  behaviour; the pure timeline maths stays readable. A
  malformed stored setting raises, never defaults
  silently.
* **Recording never alters a command.** A footprint is
  taken around a command's run; a failure to record is
  reported on the session journal where one is attached,
  and the command's own result is never changed by it.
"""

from __future__ import annotations

__all__ = [
    "CERTAINTIES",
    "CHECKPOINT_SOURCE_ATTR",
    "KINDS",
    "MAX_BACKUP_BYTES",
    "MAX_SNAPSHOT_FILES",
    "PLAIN_EXPLANATION",
    "SETTING_KEY",
    "UNDO_TIMELINE_SLICE",
    "USAGE",
    "Any",
    "BoolChange",
    "CheckpointTimelineSource",
    "CommandFootprint",
    "Dict",
    "FileChange",
    "List",
    "Mapping",
    "Optional",
    "Protocol",
    "Sequence",
    "Snapshot",
    "TimelineEntry",
    "Tuple",
    "UndoOutcome",
    "UndoStore",
    "build_footprint",
    "build_timeline",
    "checkpoint_entries_from_source",
    "enabled_from_config",
    "format_setting_change",
    "format_timeline",
    "format_undo_outcome",
    "format_undo_timeline",
    "judge_walk",
    "parse_undo_args",
    "register_edit_entry",
    "runtime_checkable",
    "set_enabled",
    "take_snapshot",
]

import hashlib
import sqlite3
import stat
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Any, Dict, List, Mapping, Optional, Protocol, Sequence, Tuple,
    runtime_checkable,
)

from .config_manager import config_manager
from .edits import atomic_write
from .workspace import resolve_file, workspace_id

#: The slice that owns this module.
UNDO_TIMELINE_SLICE = "M-077"

#: The config key the undo-timeline gate lives under.
SETTING_KEY = "undo_timeline"

#: The three strands the one timeline walks.
KINDS: Tuple[str, ...] = ("edit", "command", "checkpoint")

#: The labels a timeline entry's undo may carry. A command
#: footprint earns ``certain`` or ``best-effort`` by its
#: completeness; ``unknown`` is the honest label where a
#: strand cannot judge (checkpoint entries name their own
#: certainty through the seam, or carry ``unknown``).
CERTAINTIES: Tuple[str, ...] = ("certain", "best-effort", "unknown")

#: The attribute an agent carries its checkpoint seam
#: source under (M-075 wiring point; see the docstring).
CHECKPOINT_SOURCE_ATTR = "checkpoint_timeline_source"

#: Snapshot bounds. Past either bound a snapshot is
#: incomplete and every footprint judged from it is
#: best-effort, with the reason named — never silent.
MAX_SNAPSHOT_FILES = 2000
MAX_BACKUP_BYTES = 1_000_000
MAX_TOTAL_BACKUP_BYTES = 16_000_000

_IGNORED_DIRS = frozenset(
    {".git", "__pycache__", ".venv", ".venv-hammer", "node_modules"})

#: The setting explained in plain words — the sentence
#: every surface shows.
PLAIN_EXPLANATION = (
    "Undo grown up: /undo walks edits, commands, and "
    "checkpoints as one timeline, newest first. Undoing "
    "takes the newest entry — an older entry cannot be "
    "undone out from under a newer one; the newer entry "
    "is named and must be undone first. An edit undoes "
    "through the EditJournal exactly as before. A command "
    "undoes through its recorded footprint — the files "
    "the command created, changed, or deleted, judged "
    "from snapshots taken around its run — and is "
    "labelled certain when the snapshots were complete "
    "and every changed file's old contents are backed "
    "up, or best-effort, with its reasons, when they "
    "were not. If any file in a footprint has changed "
    "since the command ran, the whole command undo "
    "refuses and changes nothing. Checkpoints join the "
    "same timeline through the checkpoint seam "
    "(M-075, Checkpoints v2)."
)

USAGE = (
    "Usage: /undo, /undo list, /undo edit, /undo command, "
    "/undo checkpoint <id>, /undo <count>, /undo on, "
    "or /undo off"
)


# ---------------------------------------------------------------------
# Snapshots and footprints (pure).
# ---------------------------------------------------------------------

def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class Snapshot:
    """One judged look at a workspace tree.

    ``hashes`` maps each workspace-relative file path to
    the sha256 of its contents; ``contents`` carries the
    bytes of every file small enough to back up (bounded
    by MAX_BACKUP_BYTES per file and MAX_TOTAL_BACKUP_BYTES
    in total). ``complete`` is False — with the reasons
    named — when the tree outgrew a bound or a file could
    not be read; a footprint judged from an incomplete
    snapshot is best-effort, never certain.
    """

    hashes: Dict[str, str]
    contents: Dict[str, bytes]
    complete: bool
    reasons: Tuple[str, ...] = ()


def take_snapshot(root: Path) -> Snapshot:
    """Snapshot the workspace tree under *root*.

    Directories named in the ignore set (version-control
    internals, caches, virtualenvs, dependency trees) are
    not walked, symlinks are not followed, and only
    regular files are recorded. The walk is bounded:
    past MAX_SNAPSHOT_FILES the snapshot is incomplete.
    This function writes nothing.
    """
    root = Path(root).resolve()
    hashes: Dict[str, str] = {}
    contents: Dict[str, bytes] = {}
    reasons: List[str] = []
    total_backup = 0
    seen = 0
    for dirpath, dirnames, filenames in _walk(root):
        dirnames[:] = [d for d in dirnames if d not in _IGNORED_DIRS]
        for name in sorted(filenames):
            path = Path(dirpath) / name
            try:
                info = path.lstat()
            except OSError:
                reasons.append(f"{name} could not be examined")
                continue
            if not stat.S_ISREG(info.st_mode):
                continue
            seen += 1
            if seen > MAX_SNAPSHOT_FILES:
                reasons.append(
                    f"the tree holds more than "
                    f"{MAX_SNAPSHOT_FILES} files; the snapshot "
                    f"stopped there")
                return Snapshot(hashes=hashes, contents=contents,
                                complete=False,
                                reasons=tuple(reasons))
            try:
                data = path.read_bytes()
            except OSError:
                reasons.append(
                    f"{path.relative_to(root)} could not be read")
                continue
            relative = str(path.relative_to(root))
            hashes[relative] = _sha256(data)
            if len(data) <= MAX_BACKUP_BYTES and (
                    total_backup + len(data)
                    <= MAX_TOTAL_BACKUP_BYTES):
                contents[relative] = data
                total_backup += len(data)
    return Snapshot(hashes=hashes, contents=contents,
                    complete=not reasons, reasons=tuple(reasons))


def _walk(root: Path):
    import os

    return os.walk(root)


@dataclass(frozen=True)
class FileChange:
    """One file a command touched, as the snapshots judge it."""

    path: str
    before_sha: Optional[str]
    after_sha: Optional[str]
    backed_up: bool

    @property
    def kind(self) -> str:
        if self.before_sha is None:
            return "created"
        if self.after_sha is None:
            return "deleted"
        return "changed"


@dataclass(frozen=True)
class CommandFootprint:
    """What one command did to the workspace, as data.

    ``certainty`` is *certain* only when both snapshots
    were complete and every changed file's before-contents
    are backed up; otherwise *best-effort*, with the
    reasons carried in ``reasons``.
    """

    command: str
    changes: Tuple[FileChange, ...]
    complete: bool
    reasons: Tuple[str, ...] = ()

    @property
    def certainty(self) -> str:
        if self.complete and all(
                change.backed_up or change.before_sha is None
                for change in self.changes):
            return "certain"
        return "best-effort"

    def event(self) -> Dict[str, Any]:
        return {"type": "command_footprint_recorded",
                "command": self.command,
                "files": len(self.changes),
                "certainty": self.certainty,
                "complete": self.complete,
                "reasons": list(self.reasons)}


def build_footprint(command: str, before: Snapshot,
                    after: Snapshot) -> CommandFootprint:
    """Judge what *command* changed, from its two snapshots."""
    if not isinstance(command, str):
        raise ValueError("a footprint records a command's text")
    reasons: List[str] = list(before.reasons) + [
        reason for reason in after.reasons
        if reason not in before.reasons]
    changes: List[FileChange] = []
    for path in sorted(set(before.hashes) | set(after.hashes)):
        before_sha = before.hashes.get(path)
        after_sha = after.hashes.get(path)
        if before_sha == after_sha:
            continue
        backed_up = before_sha is None or path in before.contents
        if before_sha is not None and not backed_up:
            reasons.append(
                f"{path}'s old contents were too large to "
                f"back up, so they cannot be restored")
        changes.append(FileChange(
            path=path, before_sha=before_sha, after_sha=after_sha,
            backed_up=backed_up))
    complete = before.complete and after.complete
    return CommandFootprint(
        command=command, changes=tuple(changes),
        complete=complete, reasons=tuple(reasons))


# ---------------------------------------------------------------------
# The checkpoint seam (M-075 wiring point).
# ---------------------------------------------------------------------

@runtime_checkable
class CheckpointTimelineSource(Protocol):
    """The seam the checkpoint strand is read through.

    M-075 (Checkpoints v2) owns checkpoints: what one
    captures, where it is stored, how restore judges a
    dirty tree. This slice invents none of that. A source
    — supplied by the agent under the attribute named by
    CHECKPOINT_SOURCE_ATTR, as the object itself or as a
    zero-argument callable returning it — offers exactly
    two roads:

    * ``list_checkpoint_entries()``: the checkpoints as
      mappings, each carrying at least ``id`` (its stable
      identifier) and ``name`` or ``label`` (its plain
      name); ``certainty`` may ride along, and defaults
      to the honest ``unknown`` when it does not.
    * ``restore_checkpoint(checkpoint_id)``: restore the
      named checkpoint by M-075's own road and return the
      outcome in plain words.
    """

    def list_checkpoint_entries(
            self) -> Sequence[Mapping[str, Any]]:
        ...

    def restore_checkpoint(self, checkpoint_id: str) -> str:
        ...


def checkpoint_entries_from_source(
        source: Any) -> List[Dict[str, Any]]:
    """Read checkpoint entries through the seam, validated.

    Returns plain dicts with ``id``, ``label``, and
    ``certainty`` keys. A source that does not speak the
    seam, or an entry with no usable id, raises — a
    checkpoint strand is never invented from a shape this
    slice cannot judge.
    """
    if source is None:
        return []
    lister = getattr(source, "list_checkpoint_entries", None)
    if not callable(lister):
        raise ValueError(
            "the checkpoint source does not offer "
            "list_checkpoint_entries(); the checkpoint strand "
            "cannot be read through it")
    entries: List[Dict[str, Any]] = []
    for raw in lister():
        if not isinstance(raw, Mapping):
            raise ValueError(
                "a checkpoint entry must be a mapping of its "
                f"id and name; got {type(raw).__name__}")
        entry_id = raw.get("id")
        if not isinstance(entry_id, str) or not entry_id:
            raise ValueError(
                "a checkpoint entry carries no usable id; "
                "the checkpoint strand cannot name it")
        label = raw.get("name") or raw.get("label") or entry_id
        certainty = raw.get("certainty", "unknown")
        if certainty not in CERTAINTIES:
            certainty = "unknown"
        entries.append({"id": entry_id, "label": str(label),
                        "certainty": certainty})
    return entries


# ---------------------------------------------------------------------
# The one timeline (pure).
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TimelineEntry:
    """One entry on the shared undo timeline.

    ``seq`` is the timeline's own order: higher is newer.
    It is assigned by the store when an entry is first
    seen (edits register at write time through the
    EditJournal's hook, commands at record time,
    checkpoints when first listed through the seam), so
    the three strands share one honest order.
    """

    kind: str
    ref_id: str
    label: str
    detail: str
    seq: int
    certainty: str
    status: str = "recorded"

    def to_dict(self) -> Dict[str, Any]:
        return {"kind": self.kind, "ref_id": self.ref_id,
                "label": self.label, "detail": self.detail,
                "seq": self.seq, "certainty": self.certainty,
                "status": self.status}

    def event(self) -> Dict[str, Any]:
        return {"type": "undo_performed", "kind": self.kind,
                "ref_id": self.ref_id, "label": self.label,
                "certainty": self.certainty}


def build_timeline(
        entries: Sequence[TimelineEntry]) -> Tuple[TimelineEntry, ...]:
    """The entries as one timeline, newest first."""
    for entry in entries:
        if entry.kind not in KINDS:
            raise ValueError(
                f"a timeline entry is one of {KINDS}; "
                f"got {entry.kind!r}")
        if entry.certainty not in CERTAINTIES:
            raise ValueError(
                f"a timeline entry's certainty is one of "
                f"{CERTAINTIES}; got {entry.certainty!r}")
    return tuple(sorted(entries, key=lambda e: e.seq,
                        reverse=True))


def judge_walk(entries: Sequence[TimelineEntry],
               target: TimelineEntry) -> None:
    """Judge an undo of *target* against the walk order.

    The timeline is walked from the top: only the newest
    entry may be undone. A buried target refuses, naming
    the newer entry that blocks it — undoing out from
    under a later change is never done silently.
    """
    if not entries:
        raise ValueError("the timeline is empty; nothing to undo")
    newest = entries[0]
    if (newest.kind, newest.ref_id) != (target.kind, target.ref_id):
        raise ValueError(
            f"undo refused: {target.kind} {target.label!r} is "
            f"not the newest entry on the timeline — "
            f"{newest.kind} {newest.label!r} came after it and "
            f"must be undone first; nothing was changed")


# ---------------------------------------------------------------------
# The gate setting (pure).
# ---------------------------------------------------------------------

def enabled_from_config(config: Dict[str, Any]) -> bool:
    """The undo-timeline setting stored in *config*.

    Absent means True (the setting ships on). A stored
    value that is not a bool raises — never guessed at.
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
        return {"type": "undo_timeline_setting_changed",
                "from": self.before, "to": self.after}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "undo_timeline_setting_changed",
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
            f"undo timeline is already "
            f"{'on' if before else 'off'}")
    return enabled, BoolChange(before=before, after=enabled)


# ---------------------------------------------------------------------
# The durable store: timeline order + command footprints.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class UndoOutcome:
    """What one command undo did, in counted plain data."""

    command_id: int
    restored: int
    deleted: int
    recreated: int
    certainty: str

    @property
    def changed(self) -> bool:
        return bool(self.restored or self.deleted or self.recreated)

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "undo_performed", "kind": "command",
                "ref_id": str(self.command_id),
                "restored": self.restored,
                "deleted": self.deleted,
                "recreated": self.recreated,
                "certainty": self.certainty,
                "changed": self.changed,
                "session_id": session_id, "journaled": journaled}


class UndoStore:
    """The timeline's durable home for one workspace.

    Lives beside the EditJournal under the Mythic state
    directory, keyed by workspace. It holds two things:
    the shared sequence that orders all three strands
    into one timeline, and the command footprints (with
    the backed-up before-contents undo restores from).
    Edit entries themselves stay in the EditJournal;
    checkpoint entries stay with M-075 behind the seam —
    this store keeps only their order and, for commands,
    their substance.
    """

    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        directory = (config_manager.MYTHIC_DIR / "undo"
                     / workspace_id(self.root))
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.database = directory / "timeline.sqlite"
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS timeline ("
                "kind TEXT NOT NULL, ref_id TEXT NOT NULL, "
                "seq INTEGER NOT NULL, "
                "PRIMARY KEY (kind, ref_id))")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS commands ("
                "id INTEGER PRIMARY KEY, command TEXT NOT NULL, "
                "certainty TEXT NOT NULL, complete INTEGER NOT NULL, "
                "reasons TEXT NOT NULL, status TEXT NOT NULL)")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS command_files ("
                "command_id INTEGER NOT NULL, path TEXT NOT NULL, "
                "before BLOB, before_sha TEXT, after_sha TEXT, "
                "backed_up INTEGER NOT NULL)")
        self.database.chmod(0o600)

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.database)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    # ---------------------------------------------------------- order

    def register(self, kind: str, ref_id: str) -> int:
        """The entry's sequence, assigning the next if new."""
        if kind not in KINDS:
            raise ValueError(f"unknown timeline kind {kind!r}")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT seq FROM timeline WHERE kind=? AND ref_id=?",
                (kind, ref_id)).fetchone()
            if row:
                return int(row[0])
            seq = connection.execute(
                "SELECT COALESCE(MAX(seq), 0) + 1 FROM timeline"
            ).fetchone()[0]
            connection.execute(
                "INSERT INTO timeline(kind, ref_id, seq) "
                "VALUES (?,?,?)", (kind, ref_id, seq))
            connection.commit()
            return int(seq)

    def _seq(self, kind: str, ref_id: str) -> int:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT seq FROM timeline WHERE kind=? AND ref_id=?",
                (kind, ref_id)).fetchone()
        return int(row[0]) if row else 0

    # ------------------------------------------------------ footprints

    def record_footprint(self, footprint: CommandFootprint,
                         before: Snapshot) -> int:
        """Record one command's footprint; returns its id."""
        import json

        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO commands(command, certainty, "
                "complete, reasons, status) VALUES (?,?,?,?,'recorded')",
                (footprint.command, footprint.certainty,
                 1 if footprint.complete else 0,
                 json.dumps(list(footprint.reasons))))
            command_id = int(cursor.lastrowid)
            for change in footprint.changes:
                before_bytes = before.contents.get(change.path)
                connection.execute(
                    "INSERT INTO command_files(command_id, path, "
                    "before, before_sha, after_sha, backed_up) "
                    "VALUES (?,?,?,?,?,?)",
                    (command_id, change.path, before_bytes,
                     change.before_sha, change.after_sha,
                     1 if change.backed_up else 0))
            connection.commit()
        self.register("command", str(command_id))
        return command_id

    def footprints(self) -> List[Dict[str, Any]]:
        """Recorded (not yet undone) footprints, oldest first."""
        import json

        result: List[Dict[str, Any]] = []
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, command, certainty, complete, "
                "reasons FROM commands WHERE status='recorded' "
                "ORDER BY id ASC").fetchall()
            for command_id, command, certainty, complete, raw in rows:
                count = connection.execute(
                    "SELECT COUNT(*) FROM command_files "
                    "WHERE command_id=?", (command_id,)).fetchone()[0]
                result.append({
                    "id": command_id, "command": command,
                    "certainty": certainty,
                    "complete": bool(complete),
                    "reasons": json.loads(raw), "files": count})
        return result

    def undo_footprint(self, command_id: int) -> UndoOutcome:
        """Undo one recorded command, all-or-nothing.

        Every file the command touched must still be
        exactly as the command left it; one changed file
        refuses the whole undo and changes nothing. A file
        whose before-contents were never backed up (too
        large) likewise refuses — a best-effort footprint
        is attempted, never faked.
        """
        with self._connect() as connection:
            head = connection.execute(
                "SELECT certainty, status FROM commands "
                "WHERE id=?", (command_id,)).fetchone()
            if head is None or head[1] != "recorded":
                raise ValueError(
                    f"there is no recorded command footprint "
                    f"{command_id} to undo")
            certainty = head[0]
            rows = connection.execute(
                "SELECT path, before, before_sha, after_sha, "
                "backed_up FROM command_files WHERE command_id=?",
                (command_id,)).fetchall()
        plan: List[Tuple[str, Optional[bytes]]] = []
        for name, before_bytes, _b_sha, after_sha, backed_up in rows:
            path = resolve_file(self.root, name, write=True)
            current = (path.read_bytes() if path.exists() else None)
            current_sha = _sha256(current) if current is not None else None
            if current_sha != after_sha:
                raise ValueError(
                    f"undo refused: {name} changed after the "
                    f"command ran; your work is preserved and "
                    f"nothing was changed")
            if _b_sha is not None and not backed_up:
                raise ValueError(
                    f"undo refused: {name}'s old contents were "
                    f"not backed up (too large to back up), so "
                    f"they cannot be restored; nothing was "
                    f"changed")
            plan.append((name, before_bytes))
        restored = deleted = recreated = 0
        for name, before_bytes in plan:
            path = resolve_file(self.root, name, write=True)
            existed_after = path.exists()
            if before_bytes is None:
                if existed_after:
                    path.unlink()
                    deleted += 1
            else:
                mode = (stat.S_IMODE(path.stat().st_mode)
                        if existed_after else 0o600)
                atomic_write(path, before_bytes, mode)
                if existed_after:
                    restored += 1
                else:
                    recreated += 1
        with self._connect() as connection:
            connection.execute(
                "UPDATE commands SET status='undone' WHERE id=?",
                (command_id,))
            connection.commit()
        return UndoOutcome(
            command_id=command_id, restored=restored,
            deleted=deleted, recreated=recreated,
            certainty=certainty)

    # -------------------------------------------------------- timeline

    def timeline(self, edit_entries: Sequence[Mapping[str, Any]],
                 checkpoint_entries: Sequence[Mapping[str, Any]] = ()
                 ) -> Tuple[TimelineEntry, ...]:
        """Assemble the one timeline from its three strands.

        *edit_entries* are EditJournal rows (``id``,
        ``path``, ``status``); *checkpoint_entries* are the
        validated seam dicts from
        :func:`checkpoint_entries_from_source`. Undone
        command footprints leave the timeline; undone
        edits never arrive here (the journal filters them).
        """
        entries: List[TimelineEntry] = []
        for edit in sorted(edit_entries, key=lambda e: e["id"]):
            ref = str(edit["id"])
            seq = self._seq("edit", ref) or self.register("edit", ref)
            entries.append(TimelineEntry(
                kind="edit", ref_id=ref, label=str(edit["path"]),
                detail=f"edit ({edit['status']})", seq=seq,
                certainty="certain", status=str(edit["status"])))
        for record in self.footprints():
            ref = str(record["id"])
            seq = self._seq("command", ref) or self.register(
                "command", ref)
            entries.append(TimelineEntry(
                kind="command", ref_id=ref,
                label=record["command"],
                detail=f"{record['files']} file(s) changed",
                seq=seq, certainty=record["certainty"]))
        for checkpoint in checkpoint_entries:
            ref = str(checkpoint["id"])
            seq = self._seq("checkpoint", ref) or self.register(
                "checkpoint", ref)
            entries.append(TimelineEntry(
                kind="checkpoint", ref_id=ref,
                label=str(checkpoint["label"]),
                detail="checkpoint (through the M-075 seam)",
                seq=seq, certainty=str(checkpoint["certainty"])))
        return build_timeline(entries)


def register_edit_entry(root: Path, edit_id: int) -> None:
    """Register an edit on the shared timeline (write hook).

    Called by the EditJournal after an edit commits, so
    an edit's place in the one timeline is fixed when it
    happens, not when someone later looks. Failures here
    must never break an edit: the caller guards the call.
    """
    UndoStore(root).register("edit", str(edit_id))


# ---------------------------------------------------------------------
# The /undo surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------

def parse_undo_args(args: str) -> Dict[str, Any]:
    """Parse ``/undo`` arguments.

    /undo                -> undo the newest timeline entry
    /undo list           -> show the timeline
    /undo edit           -> undo the newest edit entry
    /undo command        -> undo the newest command entry
    /undo checkpoint <id>-> restore a checkpoint (seam)
    /undo <count>        -> walk back <count> entries
    /undo on / off       -> the gate setting
    """
    text = (args or "").strip()
    if not text:
        return {"action": "next", "count": 1}
    if text == "list":
        return {"action": "show"}
    if text == "on":
        return {"action": "setting", "enabled": True}
    if text == "off":
        return {"action": "setting", "enabled": False}
    if text in ("edit", "command"):
        return {"action": "kind", "kind": text}
    if text.startswith("checkpoint"):
        parts = text.split(None, 1)
        if len(parts) == 2 and parts[1].strip():
            return {"action": "checkpoint",
                    "checkpoint_id": parts[1].strip()}
        raise ValueError(USAGE)
    if text.isdigit():
        count = int(text)
        if count < 1:
            raise ValueError(USAGE)
        return {"action": "next", "count": count}
    raise ValueError(USAGE)


def format_setting_change(record: Dict[str, Any]) -> str:
    """A setting change record, in plain words."""
    word = {True: "on", False: "off"}
    return (f"Undo timeline: {word[record['from']]} -> "
            f"{word[record['to']]}.")


def format_timeline(entries: Sequence[TimelineEntry]) -> str:
    """The timeline, newest first, in plain words."""
    if not entries:
        return "The undo timeline is empty: no edits, " \
               "commands, or checkpoints are recorded yet."
    noun = "entry" if len(entries) == 1 else "entries"
    lines = [f"Undo timeline — {len(entries)} {noun}, "
             f"newest first:"]
    for position, entry in enumerate(entries, start=1):
        label = entry.label
        if len(label) > 80:
            label = label[:77] + "..."
        lines.append(
            f"  {position}. [{entry.kind}] {label} — "
            f"{entry.detail} (undo: {entry.certainty})")
    return "\n".join(lines)


def format_undo_outcome(record: Dict[str, Any]) -> str:
    """One performed undo, in plain words."""
    if record.get("message"):
        return str(record["message"])
    if record.get("kind") == "command":
        return (
            f"Undid command {record['label']!r} "
            f"({record['certainty']}): "
            f"{record.get('restored', 0)} file(s) restored, "
            f"{record.get('deleted', 0)} created file(s) "
            f"removed, {record.get('recreated', 0)} deleted "
            f"file(s) brought back.")
    return f"Undid {record.get('kind')} {record.get('label')!r}."


_SAMPLE_ENTRIES = (
    TimelineEntry(kind="edit", ref_id="sample-edit",
                  label="app.py", detail="edit (applied)",
                  seq=1, certainty="certain"),
    TimelineEntry(kind="command", ref_id="sample-command",
                  label="python -m pytest -q",
                  detail="2 file(s) changed", seq=2,
                  certainty="best-effort"),
)


def format_undo_timeline(config: Dict[str, Any],
                         entries: Sequence[TimelineEntry] = (),
                         checkpoint_wired: bool = False) -> str:
    """The whole slice, in plain words, for /undo list.

    Built from build_timeline() / format_timeline() /
    judge_walk(), so every public road this module offers
    is exercised by its own show surface: a worked example
    timeline (an edit, then a command over it — the edit
    cannot be undone until the command is), then the
    caller's true timeline.
    """
    enabled = enabled_from_config(config)
    lines = ["Undo grown up (M-077) — " + PLAIN_EXPLANATION, ""]
    lines.append(f"Setting: {'on' if enabled else 'off'} "
                 f"({SETTING_KEY}).")
    lines.append(
        "Checkpoint strand: "
        + ("wired through the checkpoint seam."
           if checkpoint_wired else
           "no checkpoint source is wired yet — "
           "DEPENDS-ON-M-075 (Checkpoints v2); the edit "
           "and command strands are live."))
    lines.append("")
    sample = build_timeline(_SAMPLE_ENTRIES)
    lines.append("How the walk works, on an example timeline:")
    lines.append(format_timeline(sample))
    try:
        judge_walk(sample, sample[1])
        lines.append("  (the buried edit undid cleanly — "
                     "this line is never reached)")
    except ValueError as exc:
        lines.append(f"  Undoing the buried edit first: {exc}")
    lines.append("")
    lines.append("Your timeline:")
    lines.append(format_timeline(entries))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)
