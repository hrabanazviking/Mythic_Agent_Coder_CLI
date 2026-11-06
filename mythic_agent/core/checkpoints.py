"""Named checkpoints (All-Features roadmap slice M-075).

Part IV — The Editor's Hand. The roadmap's words: named
checkpoints ("before the auth rework") capturing working
tree + session state; restore is one command, and the
journal shows the whole checkpoint tree.

What already shipped, and what this slice adds:

* Session checkpoints (``core/sessions.py``) are a
  crash-safety mechanism: a write-ahead journal of the
  current session's transcript so a dead process loses
  nothing. They are unnamed, automatic, and capture no
  working tree. The EditJournal (``core/edits.py``)
  records individual file edits so one edit can be
  undone. Neither lets a user say "freeze everything as
  it stands, under this name, and bring it all back
  later with one command".
* This slice is that freeze: a checkpoint captures the
  whole working tree (every file's bytes, content-
  addressed in a blob store, plus symlinks as links) and
  — when a session is attached — the session state
  (its messages, status, token count and outcome), under
  a name the user chooses. Checkpoints form a tree: each
  new checkpoint's parent is the checkpoint that was
  current when it was taken, and restoring an older
  checkpoint and taking a new one from there grows a
  branch. The store lives beside the EditJournal's,
  under ``MYTHIC_DIR / "checkpoints" / workspace_id``.

Honesty rules, enforced here and pinned by the slice's
tests:

* **Restore judges a dirty tree, and refuses honestly.**
  The tree is clean exactly when it matches the
  checkpoint at the head of the tree (the last one taken
  or restored). If the tree has changed since then,
  restoring would silently throw un-checkpointed work
  away, so restore refuses, names the changed files, and
  gives the remedy: take a checkpoint of the current
  tree first, or restore with ``discard`` to throw those
  changes away on purpose — counted in the outcome,
  never hidden.
* **A checkpoint is whole or it is refused.** A file
  over the size cap, an unreadable file, or a missing
  blob refuses the whole take / restore before anything
  is written — a checkpoint never quietly captures or
  restores only part of the tree. Cache and VCS
  directories (``.git``, ``__pycache__`` and kin) are
  outside a checkpoint's scope, named here, never
  silently half-included; empty directories are not
  captured (the git rule).
* **Session state is restored only into its own
  session.** A checkpoint taken in another session
  restores the tree and says plainly that the session
  state was left alone, naming both sessions — history
  is never smuggled across sessions.
* **Names are the user's words.** A checkpoint name is
  free text ("before the auth rework"), validated only
  for emptiness, length and control characters, and it
  must be unique in the workspace — a second take under
  the same name refuses and says so.
* **The setting is a gate, not a guess.** With
  ``checkpoints`` off, takes and restores through the
  agent layer refuse and say so; the tree stays
  readable. A malformed stored setting raises, never
  defaults silently.
"""

from __future__ import annotations

__all__ = [
    "CHECKPOINTS_SLICE",
    "MAX_FILE_BYTES",
    "MAX_FILES",
    "MAX_NAME_CHARS",
    "PLAIN_EXPLANATION",
    "SETTING_KEY",
    "SKIP_DIRS",
    "USAGE",
    "Any",
    "BoolChange",
    "Checkpoint",
    "CheckpointStore",
    "Dict",
    "List",
    "Optional",
    "RestoreOutcome",
    "Tuple",
    "capture_manifest",
    "diff_manifests",
    "enabled_from_config",
    "format_checkpoint_created",
    "format_checkpoint_restored",
    "format_checkpoint_tree",
    "format_checkpoints",
    "format_setting_change",
    "parse_checkpoint_args",
    "set_enabled",
    "tree_hash",
    "validate_name",
    "validate_session_snapshot",
]

import hashlib
import json
import os
import sqlite3
import stat
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

from filelock import FileLock

from .config_manager import config_manager
from .edits import atomic_write
from .workspace import workspace_id

#: The slice that owns this module.
CHECKPOINTS_SLICE = "M-075"

#: The config key the checkpoints gate lives under.
SETTING_KEY = "checkpoints"

#: A checkpoint name is the user's own words; this only
#: bounds them so a name stays a name, not a document.
MAX_NAME_CHARS = 80

#: One file larger than this refuses the whole take:
#: a checkpoint is whole or it is refused, never partial.
MAX_FILE_BYTES = 32 * 1024 * 1024

#: A tree larger than this refuses the whole take, for
#: the same reason.
MAX_FILES = 20000

#: Directories outside a checkpoint's scope: version-
#: control internals and disposable caches. Files under
#: them are neither captured nor restored nor deleted.
SKIP_DIRS = frozenset({
    ".git", ".hg", ".svn", "__pycache__",
    ".mypy_cache", ".pytest_cache", ".venv", "venv",
    "node_modules",
})

#: The setting explained in plain words — the sentence
#: every surface shows.
PLAIN_EXPLANATION = (
    "Named checkpoints: /checkpoint take <name> captures "
    "the whole working tree plus the current session "
    "state under a name you choose ('before the auth "
    "rework'); /checkpoint restore <name> brings that "
    "tree and session back in one command. Checkpoints "
    "form a tree — each new one hangs from the one that "
    "was current when it was taken, and restoring an "
    "older checkpoint and taking a new one from there "
    "grows a branch; the journal view shows the whole "
    "tree. Restore is judged honestly: if the working "
    "tree has changed since the last checkpoint was "
    "taken or restored, restore refuses and names the "
    "changed files — take a checkpoint of the current "
    "tree first, or restore with 'discard' to throw "
    "those changes away on purpose. Nothing is ever "
    "silently overwritten.")

USAGE = (
    "Usage: /checkpoint | /checkpoint take <name> | "
    "/checkpoint restore <name> [discard] | "
    "/checkpoint on | /checkpoint off")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_name(name: Any) -> str:
    """A checkpoint name, judged. The user's words, kept."""
    if not isinstance(name, str):
        raise ValueError(
            f"a checkpoint name is words; got {type(name).__name__}")
    cleaned = name.strip()
    if not cleaned:
        raise ValueError(
            "a checkpoint needs a name — e.g. "
            "/checkpoint take before the auth rework")
    if len(cleaned) > MAX_NAME_CHARS:
        raise ValueError(
            f"a checkpoint name is at most {MAX_NAME_CHARS} "
            f"characters; got {len(cleaned)}")
    if any(ord(char) < 32 for char in cleaned):
        raise ValueError(
            "a checkpoint name may not carry control characters")
    return cleaned


def validate_session_snapshot(session: Any) -> Optional[Dict[str, Any]]:
    """Session state a checkpoint carries, judged as data.

    ``None`` is an honest checkpoint of the tree alone.
    Anything else must be the whole shape — the session's
    id, its status, its token count, its messages, and
    its outcome when it has one — and JSON-clean, proven
    here before it is stored, never at restore time.
    """
    if session is None:
        return None
    if not isinstance(session, dict):
        raise ValueError(
            "session state must be a record; got "
            f"{type(session).__name__}")
    session_id = session.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        raise ValueError("session state needs its session id")
    status = session.get("status")
    if not isinstance(status, str) or not status:
        raise ValueError("session state needs its status")
    total_tokens = session.get("total_tokens")
    if (isinstance(total_tokens, bool)
            or not isinstance(total_tokens, int) or total_tokens < 0):
        raise ValueError("session state needs its token count")
    messages = session.get("messages")
    if (not isinstance(messages, list)
            or not all(isinstance(m, dict) for m in messages)):
        raise ValueError("session state needs its messages")
    outcome = session.get("outcome")
    if outcome is not None and not isinstance(outcome, dict):
        raise ValueError("session outcome must be a record or none")
    snapshot = {"session_id": session_id, "status": status,
                "total_tokens": total_tokens, "messages": messages,
                "outcome": outcome}
    json.dumps(snapshot, allow_nan=False)  # fail fast, like the WAL
    return snapshot


def capture_manifest(root: Path) -> Dict[str, Dict[str, Any]]:
    """The working tree at *root*, as data.

    Every in-scope file becomes an entry keyed by its
    path relative to the root: a regular file carries
    its content hash, size and mode; a symlink carries
    its target and is never followed. A file over the
    size cap or unreadable refuses the whole capture,
    naming itself — a checkpoint is whole or refused.
    """
    root = Path(root).resolve()
    manifest: Dict[str, Dict[str, Any]] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        here = Path(dirpath)
        kept = []
        for dirname in sorted(dirnames):
            if dirname in SKIP_DIRS:
                continue
            candidate = here / dirname
            if candidate.is_symlink():
                relative = str(candidate.relative_to(root))
                manifest[relative] = {
                    "kind": "link", "target": os.readlink(candidate)}
            else:
                kept.append(dirname)
        dirnames[:] = kept
        for filename in sorted(filenames):
            candidate = here / filename
            relative = str(candidate.relative_to(root))
            if candidate.is_symlink():
                manifest[relative] = {
                    "kind": "link", "target": os.readlink(candidate)}
                continue
            try:
                info = candidate.stat()
            except OSError as exc:
                raise ValueError(
                    f"cannot read {relative} to checkpoint it: "
                    f"{exc}") from exc
            if not stat.S_ISREG(info.st_mode):
                raise ValueError(
                    f"{relative} is not a regular file; a "
                    "checkpoint captures files and links only")
            if info.st_size > MAX_FILE_BYTES:
                raise ValueError(
                    f"{relative} is {info.st_size} bytes — over "
                    f"the {MAX_FILE_BYTES}-byte checkpoint cap; "
                    "nothing was captured")
            try:
                data = candidate.read_bytes()
            except OSError as exc:
                raise ValueError(
                    f"cannot read {relative} to checkpoint it: "
                    f"{exc}") from exc
            manifest[relative] = {
                "kind": "file",
                "sha256": hashlib.sha256(data).hexdigest(),
                "size": len(data),
                "mode": stat.S_IMODE(info.st_mode)}
            if len(manifest) > MAX_FILES:
                raise ValueError(
                    f"the tree holds more than {MAX_FILES} "
                    "entries; nothing was captured")
    return manifest


def tree_hash(manifest: Dict[str, Dict[str, Any]]) -> str:
    """One hash for one whole tree state."""
    digest = hashlib.sha256()
    for path in sorted(manifest):
        entry = manifest[path]
        if entry["kind"] == "file":
            marker = f"file:{entry['sha256']}:{entry['mode']:o}"
        else:
            marker = f"link:{entry['target']}"
        digest.update(f"{path}\0{marker}\n".encode("utf-8"))
    return digest.hexdigest()


def diff_manifests(anchor: Dict[str, Dict[str, Any]],
                   current: Dict[str, Dict[str, Any]]
                   ) -> Dict[str, List[str]]:
    """How *current* differs from *anchor*, in plain lists.

    ``added`` stands in current only, ``deleted`` in the
    anchor only, ``modified`` in both but changed — the
    exact judgement restore makes of a dirty tree.
    """
    added = sorted(p for p in current if p not in anchor)
    deleted = sorted(p for p in anchor if p not in current)
    modified = sorted(p for p in current
                      if p in anchor and current[p] != anchor[p])
    return {"added": added, "modified": modified, "deleted": deleted}


def _dirty_count(dirty: Dict[str, List[str]]) -> int:
    return sum(len(paths) for paths in dirty.values())


@dataclass(frozen=True)
class Checkpoint:
    """One named checkpoint, as data."""

    id: int
    name: str
    parent_id: Optional[int]
    parent_name: Optional[str]
    created_at: str
    manifest: Dict[str, Dict[str, Any]]
    session: Optional[Dict[str, Any]]
    tree_hash: str

    @property
    def file_count(self) -> int:
        return len(self.manifest)

    @property
    def total_bytes(self) -> int:
        return sum(entry["size"] for entry in self.manifest.values()
                   if entry["kind"] == "file")

    @property
    def session_id(self) -> Optional[str]:
        return self.session["session_id"] if self.session else None


@dataclass(frozen=True)
class RestoreOutcome:
    """What a restore did, in counted plain data."""

    restored: int
    removed: int
    unchanged: int
    discarded_changes: int


class CheckpointStore:
    """The workspace's checkpoints: a tree of named freezes.

    Lives under ``MYTHIC_DIR / "checkpoints" /
    workspace_id(root)`` beside the EditJournal's store:
    a SQLite index of checkpoints (name, parent, the
    manifest, the captured session state) and a content-
    addressed blob directory the manifests point into.
    The store's head is the checkpoint the working tree
    is judged against — the last one taken or restored.
    """

    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        directory = (config_manager.MYTHIC_DIR / "checkpoints"
                     / workspace_id(self.root))
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.directory = directory
        self.database = directory / "checkpoints.sqlite"
        self.blobs = directory / "blobs"
        self.blobs.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.lock = FileLock(str(directory / "checkpoints.lock"),
                             timeout=10)
        with self.lock, self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS checkpoints ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "name TEXT NOT NULL UNIQUE, parent_id INTEGER, "
                "created_at TEXT NOT NULL, session TEXT, "
                "manifest TEXT NOT NULL, tree_hash TEXT NOT NULL)")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS meta ("
                "key TEXT PRIMARY KEY, value TEXT)")
        self.database.chmod(0o600)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _blob_path(self, digest: str) -> Path:
        return self.blobs / digest

    def _store_blob(self, data: bytes) -> str:
        digest = hashlib.sha256(data).hexdigest()
        path = self._blob_path(digest)
        if not path.exists():
            atomic_write(path, data, 0o600)
        return digest

    def _head_id(self, connection) -> Optional[int]:
        row = connection.execute(
            "SELECT value FROM meta WHERE key='head'").fetchone()
        return int(row["value"]) if row else None

    def _set_head(self, connection, checkpoint_id: int) -> None:
        connection.execute(
            "INSERT OR REPLACE INTO meta(key, value) "
            "VALUES ('head', ?)", (str(checkpoint_id),))

    def _row_to_checkpoint(self, connection, row) -> Checkpoint:
        parent_name = None
        if row["parent_id"] is not None:
            parent = connection.execute(
                "SELECT name FROM checkpoints WHERE id=?",
                (row["parent_id"],)).fetchone()
            parent_name = parent["name"] if parent else None
        return Checkpoint(
            id=row["id"], name=row["name"],
            parent_id=row["parent_id"], parent_name=parent_name,
            created_at=row["created_at"],
            manifest=json.loads(row["manifest"]),
            session=(json.loads(row["session"])
                     if row["session"] else None),
            tree_hash=row["tree_hash"])

    def list_checkpoints(self) -> List[Checkpoint]:
        """Every checkpoint in the tree, oldest first."""
        with self.lock, self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM checkpoints ORDER BY id").fetchall()
            return [self._row_to_checkpoint(connection, row)
                    for row in rows]

    def head(self) -> Optional[Checkpoint]:
        """The checkpoint the tree is judged against, if any."""
        with self.lock, self._connect() as connection:
            head_id = self._head_id(connection)
            if head_id is None:
                return None
            row = connection.execute(
                "SELECT * FROM checkpoints WHERE id=?",
                (head_id,)).fetchone()
            return (self._row_to_checkpoint(connection, row)
                    if row else None)

    def get(self, name: str) -> Checkpoint:
        """One checkpoint by its name, or an honest refusal."""
        cleaned = validate_name(name)
        with self.lock, self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM checkpoints WHERE name=?",
                (cleaned,)).fetchone()
            if row is None:
                raise ValueError(
                    f"no checkpoint named {cleaned!r} in this "
                    "workspace — /checkpoint shows the tree")
            return self._row_to_checkpoint(connection, row)

    def create(self, name: str,
               session: Optional[Dict[str, Any]] = None) -> Checkpoint:
        """Freeze the tree (and session state) under *name*.

        The new checkpoint's parent is the current head;
        the new checkpoint becomes the head. A name already
        taken refuses — names are how humans point at
        freezes, so they stay unique.
        """
        cleaned = validate_name(name)
        snapshot = validate_session_snapshot(session)
        manifest = capture_manifest(self.root)
        with self.lock, self._connect() as connection:
            taken = connection.execute(
                "SELECT id FROM checkpoints WHERE name=?",
                (cleaned,)).fetchone()
            if taken is not None:
                raise ValueError(
                    f"a checkpoint named {cleaned!r} already "
                    "exists — names are unique; pick another")
            parent_id = self._head_id(connection)
            for relative, entry in manifest.items():
                if entry["kind"] == "file":
                    data = (self.root / relative).read_bytes()
                    digest = self._store_blob(data)
                    if digest != entry["sha256"]:
                        raise ValueError(
                            f"{relative} changed while it was "
                            "being checkpointed; nothing was "
                            "captured — take the checkpoint again")
            cursor = connection.execute(
                "INSERT INTO checkpoints(name, parent_id, "
                "created_at, session, manifest, tree_hash) "
                "VALUES (?,?,?,?,?,?)",
                (cleaned, parent_id, _now(),
                 json.dumps(snapshot, allow_nan=False)
                 if snapshot is not None else None,
                 json.dumps(manifest, allow_nan=False,
                            sort_keys=True),
                 tree_hash(manifest)))
            checkpoint_id = cursor.lastrowid
            self._set_head(connection, checkpoint_id)
            row = connection.execute(
                "SELECT * FROM checkpoints WHERE id=?",
                (checkpoint_id,)).fetchone()
            return self._row_to_checkpoint(connection, row)

    def plan_restore(self, name: str, discard: bool = False
                     ) -> Tuple[Checkpoint, Dict[str, Any],
                                Dict[str, List[str]]]:
        """Judge a restore before anything is touched.

        Returns (checkpoint, plan, dirty): the plan names
        the entries to write and to remove against the
        tree as it stands. The dirty judgement compares
        the tree against the head checkpoint's manifest;
        a dirty tree without ``discard`` refuses here,
        naming the changed files and the remedy, and a
        missing blob refuses here too — nothing is ever
        half-restored by surprise.
        """
        checkpoint = self.get(name)
        current = capture_manifest(self.root)
        head = self.head()
        anchor = head.manifest if head is not None else {}
        dirty = diff_manifests(anchor, current)
        if _dirty_count(dirty) and not discard:
            changed = sorted(dirty["added"] + dirty["modified"]
                             + dirty["deleted"])
            shown = ", ".join(changed[:5])
            if len(changed) > 5:
                shown += f", and {len(changed) - 5} more"
            raise ValueError(
                f"the working tree has {_dirty_count(dirty)} "
                f"un-checkpointed change(s) ({shown}) — "
                "restoring would throw them away. Take a "
                f"checkpoint of the current tree first, or "
                f"restore with discard: /checkpoint restore "
                f"{checkpoint.name} discard")
        missing = [relative for relative, entry
                   in checkpoint.manifest.items()
                   if entry["kind"] == "file"
                   and not self._blob_path(entry["sha256"]).exists()]
        if missing:
            raise ValueError(
                "checkpoint " + repr(checkpoint.name)
                + " is damaged: the stored contents of "
                + ", ".join(sorted(missing)[:5])
                + " are missing; nothing was restored")
        writes = [relative for relative, entry
                  in checkpoint.manifest.items()
                  if current.get(relative) != entry]
        removes = [relative for relative in current
                   if relative not in checkpoint.manifest]
        unchanged = sum(1 for relative, entry
                        in checkpoint.manifest.items()
                        if current.get(relative) == entry)
        plan = {"writes": sorted(writes), "removes": sorted(removes),
                "unchanged": unchanged}
        return checkpoint, plan, dirty

    def restore(self, name: str, discard: bool = False
                ) -> Tuple[Checkpoint, RestoreOutcome]:
        """Bring one checkpoint's tree back, in one motion.

        Judged first by :meth:`plan_restore`; then files
        the checkpoint does not know are removed, the
        checkpoint's files and links are written back
        atomically with their recorded modes, and the
        restored checkpoint becomes the head — the tree
        is clean against it by construction.
        """
        checkpoint, plan, dirty = self.plan_restore(name, discard)
        with self.lock:
            for relative in plan["removes"]:
                target = self.root / relative
                if target.is_symlink() or target.exists():
                    target.unlink()
                parent = target.parent
                while parent != self.root and parent.exists():
                    try:
                        parent.rmdir()
                    except OSError:
                        break
                    parent = parent.parent
            for relative in plan["writes"]:
                entry = checkpoint.manifest[relative]
                target = self.root / relative
                if entry["kind"] == "link":
                    if target.is_symlink() or target.exists():
                        target.unlink()
                    target.parent.mkdir(parents=True, exist_ok=True)
                    os.symlink(entry["target"], target)
                else:
                    if target.is_symlink():
                        target.unlink()
                    data = self._blob_path(entry["sha256"]).read_bytes()
                    if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                        raise ValueError(
                            "checkpoint " + repr(checkpoint.name)
                            + f" is damaged: the stored contents "
                            f"of {relative} no longer match their "
                            "hash; the restore stopped there")
                    atomic_write(target, data, entry["mode"])
            with self._connect() as connection:
                self._set_head(connection, checkpoint.id)
        return checkpoint, RestoreOutcome(
            restored=len(plan["writes"]), removed=len(plan["removes"]),
            unchanged=plan["unchanged"],
            discarded_changes=_dirty_count(dirty) if discard else 0)


def enabled_from_config(config: Dict[str, Any]) -> bool:
    """The checkpoints setting stored in *config*.

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
        return {"type": "checkpoints_setting_changed",
                "from": self.before, "to": self.after}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "checkpoints_setting_changed",
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
            f"checkpoints are already "
            f"{'on' if before else 'off'}")
    return enabled, BoolChange(before=before, after=enabled)


# ---------------------------------------------------------------------
# The /checkpoint surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------

def parse_checkpoint_args(args: str) -> Dict[str, Any]:
    """Parse ``/checkpoint`` arguments.

    /checkpoint                        -> show the tree
    /checkpoint on / off               -> the gate
    /checkpoint take <name...>         -> freeze under a name
    /checkpoint restore <name...>      -> bring one back
    /checkpoint restore <name> discard -> ...throwing the
        un-checkpointed changes away, on purpose
    """
    text = (args or "").strip()
    if not text or text in ("list", "tree"):
        return {"action": "show"}
    if text == "on":
        return {"action": "setting", "enabled": True}
    if text == "off":
        return {"action": "setting", "enabled": False}
    if text.startswith("take "):
        return {"action": "take",
                "name": validate_name(text[5:])}
    if text.startswith("restore "):
        rest = text[8:].strip()
        discard = False
        if rest.endswith(" discard"):
            discard = True
            rest = rest[:-len(" discard")].strip()
        if not rest or rest == "discard":
            raise ValueError(USAGE)
        return {"action": "restore", "name": validate_name(rest),
                "discard": discard}
    raise ValueError(USAGE)


def format_setting_change(record: Dict[str, Any]) -> str:
    """A setting change record, in plain words."""
    word = {True: "on", False: "off"}
    return (f"Checkpoints: {word[record['from']]} -> "
            f"{word[record['to']]}.")


def format_checkpoint_tree(checkpoints: List[Checkpoint],
                           head_id: Optional[int]) -> str:
    """The whole checkpoint tree — the journal view.

    Every checkpoint, roots first, each branch indented
    under its parent, the head (the checkpoint the tree
    is judged against) marked. Restoring an older
    checkpoint and taking a new one from there is how a
    second branch grows under the same root.
    """
    if not checkpoints:
        return ("No checkpoints yet — take the first with "
                "/checkpoint take <name>.")
    by_id = {checkpoint.id: checkpoint for checkpoint in checkpoints}
    children: Dict[Optional[int], List[Checkpoint]] = {}
    for checkpoint in checkpoints:
        parent = checkpoint.parent_id
        if parent not in by_id:
            parent = None
        children.setdefault(parent, []).append(checkpoint)
    lines = ["Checkpoint tree:"]

    def render(checkpoint: Checkpoint, depth: int) -> None:
        marker = " *" if checkpoint.id == head_id else ""
        session = (f", session {checkpoint.session_id[:8]}…"
                   if checkpoint.session_id else "")
        lines.append(
            f"{'  ' * depth}- {checkpoint.name}{marker} "
            f"({checkpoint.file_count} file(s), "
            f"{checkpoint.created_at}{session})")
        for child in children.get(checkpoint.id, []):
            render(child, depth + 1)

    for root_checkpoint in children.get(None, []):
        render(root_checkpoint, 0)
    lines.append("* = the head: the checkpoint the working "
                 "tree is judged against.")
    return "\n".join(lines)


def format_checkpoints(config: Dict[str, Any],
                       checkpoints: List[Checkpoint],
                       head_id: Optional[int]) -> str:
    """The whole slice, in plain words, for /checkpoint."""
    enabled = enabled_from_config(config)
    lines = ["Named checkpoints (M-075) — " + PLAIN_EXPLANATION, ""]
    lines.append(f"Setting: {'on' if enabled else 'off'} "
                 f"({SETTING_KEY}).")
    lines.append("")
    lines.append(format_checkpoint_tree(checkpoints, head_id))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def format_checkpoint_created(record: Dict[str, Any]) -> str:
    """A taken checkpoint, in plain words."""
    parent = (f", under {record['parent_name']!r}"
              if record.get("parent_name") else "")
    session = (" Session state captured."
               if record.get("session_captured") else
               " No session was attached, so the tree alone "
               "was captured.")
    return (f"Checkpoint {record['name']!r} taken{parent}: "
            f"{record['files']} file(s), {record['bytes']} "
            f"byte(s) frozen.{session}")


def format_checkpoint_restored(record: Dict[str, Any]) -> str:
    """A restored checkpoint, in plain words."""
    lines = [
        f"Checkpoint {record['name']!r} restored: "
        f"{record['restored']} file(s) written back, "
        f"{record['removed']} removed, {record['unchanged']} "
        "already as they were."]
    if record.get("discarded_changes"):
        lines.append(
            f"{record['discarded_changes']} un-checkpointed "
            "change(s) were discarded, as ordered.")
    if record.get("session_restored"):
        lines.append("Session state restored with the tree.")
    elif record.get("session_note"):
        lines.append(record["session_note"])
    return " ".join(lines)
