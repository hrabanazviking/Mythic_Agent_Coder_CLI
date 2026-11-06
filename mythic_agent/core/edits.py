"""Atomic file edits with a durable journal and conservative undo."""

__all__ = [
    "EditJournal",
    "GuardianRefusal",
    "FileLock",
    "Iterator",
    "Path",
    "atomic_write",
    "config_manager",
    "explicit_from_config",
    "guard_or_raise",
    "contextmanager",
    "resolve_file",
    "runtime_settings",
    "workspace_id",
]

import os
import sqlite3
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from filelock import FileLock

from .config_manager import config_manager
from .file_guardians import GuardianRefusal, explicit_from_config, guard_or_raise
from .runtime import runtime_settings
from .workspace import resolve_file, workspace_id


def atomic_write(path: Path, content: bytes, mode: int) -> None:
    """Replace a file only after its complete contents are flushed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".mythic-edit-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class EditJournal:
    def __init__(self, root: Path, explicit_word: bool | None = None):
        # M-079: the user's explicit word for guarded files
        # (README / licence), when the caller carries it (the
        # agent layer passes its own config's word). None
        # means: read the stored config at write time.
        self._explicit_word_override = explicit_word
        self.root = root.resolve()
        directory = config_manager.MYTHIC_DIR / "edits" / workspace_id(self.root)
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.database = directory / "journal.sqlite"
        timeout = runtime_settings(config_manager.load_config())["edit_lock_timeout"]
        self.lock = FileLock(str(directory / "journal.lock"), timeout=timeout)
        with self.lock, self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS edits ("
                "id INTEGER PRIMARY KEY, path TEXT NOT NULL, before BLOB, "
                "after BLOB NOT NULL, mode INTEGER NOT NULL, status TEXT NOT NULL)"
            )
        self.database.chmod(0o600)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    @staticmethod
    def _contents(path: Path) -> bytes | None:
        return path.read_bytes() if path.exists() else None

    def _recover(self, connection: sqlite3.Connection) -> None:
        rows = connection.execute(
            "SELECT id,path,before,after,status,mode FROM edits "
            "WHERE status IN ('prepared','undo_prepared')"
        ).fetchall()
        for entry_id, name, before, after, status, mode in rows:
            path = resolve_file(self.root, name, write=True)
            current = self._contents(path)
            if status == "prepared":
                recovered = "applied" if current == after else "aborted" if current == before else "conflict"
            else:
                recovered = "undone" if current == before else "applied" if current == after else "conflict"
            if recovered == "applied" and path.exists():
                mode = stat.S_IMODE(path.stat().st_mode)
            connection.execute(
                "UPDATE edits SET status=?,mode=? WHERE id=?",
                (recovered, mode, entry_id),
            )
        connection.commit()

    def _explicit_word(self, explicit_word: bool | None) -> bool:
        """The explicit word for one write (M-079).

        A per-call word wins, then this journal's own, then
        the stored config's — absent everywhere means not
        given; the word is never presumed.
        """
        if explicit_word is not None:
            return explicit_word
        if self._explicit_word_override is not None:
            return self._explicit_word_override
        return explicit_from_config(config_manager.load_config())

    def write(self, value: str, text: str, *,
              operation: str | None = None,
              explicit_word: bool | None = None) -> Path:
        if not isinstance(text, str):
            raise ValueError("content must be a string")
        with self.lock, self._connect() as connection:
            self._recover(connection)
            path = resolve_file(self.root, value, write=True)
            before = self._contents(path)
            after = text.encode("utf-8")
            if before == after:
                return path
            # M-079: the guardians judge every write that
            # passes through this journal — every edit road
            # in the layer (formats, anchored, reviewed,
            # tool, LSP, rewrite, formatter) writes here.
            # An unclassified write to an existing file is
            # an overwrite; to a new file, a creation. A
            # refusal raises before the journal records or
            # the file moves: nothing is changed.
            guard_or_raise(
                value,
                operation or ("overwrite" if before is not None
                              else "create"),
                exists=before is not None,
                explicit_word=self._explicit_word(explicit_word),
                current_text=(before.decode("utf-8", "replace")
                              if before is not None else None))
            mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
            relative = str(path.relative_to(self.root))
            cursor = connection.execute(
                "INSERT INTO edits(path,before,after,mode,status) VALUES (?,?,?,?, 'prepared')",
                (relative, before, after, mode),
            )
            connection.commit()  # The recovery receipt exists before any file mutation.
            resolve_file(self.root, relative, write=True)
            atomic_write(path, after, mode)
            actual_mode = stat.S_IMODE(path.stat().st_mode)
            connection.execute(
                "UPDATE edits SET status='applied',mode=? WHERE id=?",
                (actual_mode, cursor.lastrowid),
            )
            connection.commit()
            try:
                from .undo_timeline import register_edit_entry

                register_edit_entry(self.root, cursor.lastrowid)
            except Exception:
                pass  # the shared timeline never breaks an edit
            return path

    def write_anchored_range(self, value: str, start: int, end: int,
                             expected: str, replacement: str) -> Path:
        """Write a range edit judged by its lines' anchor (M-072).

        The pure layer in :mod:`mythic_agent.core.hash_anchored`
        judges the edit against the file's true current text:
        the range's recomputed SHA-256 anchor must match
        *expected* or the edit refuses and this journal writes
        nothing at all. A successful edit rides this journal's
        own ``write`` road, so it is undoable like any edit.
        """
        from .hash_anchored import apply_anchored_range

        path = resolve_file(self.root, value, write=True)
        if not path.exists():
            raise ValueError(
                f"an anchored edit needs an existing file; "
                f"{value} does not exist — nothing was changed")
        current = path.read_text(encoding="utf-8")
        new_text, _applied = apply_anchored_range(
            current, start, end, expected, replacement)
        # M-079: a range covering the whole file is an
        # overwrite, however it arrives; a partial range is
        # an in-place edit.
        operation = ("overwrite" if start <= 1
                     and end >= len(current.splitlines())
                     else "inplace")
        return self.write(value, new_text, operation=operation)

    def write_anchored_search(self, value: str, target: str,
                              expected: str, replacement: str) -> Path:
        """Write a search edit judged by its block's anchor (M-072).

        The search text must match exactly once and the matched
        lines' anchor must match *expected*; any other outcome
        refuses and this journal writes nothing at all.
        """
        from .hash_anchored import apply_anchored_search

        path = resolve_file(self.root, value, write=True)
        if not path.exists():
            raise ValueError(
                f"an anchored edit needs an existing file; "
                f"{value} does not exist — nothing was changed")
        current = path.read_text(encoding="utf-8")
        new_text, _applied = apply_anchored_search(
            current, target, expected, replacement)
        # M-079: a search block that is the file's whole
        # text is an overwrite; any lesser block is in-place.
        # (One trailing newline is the file's ending, not
        # part of the comparison.)
        whole = current[:-1] if current.endswith("\n") else current
        sought = target[:-1] if target.endswith("\n") else target
        operation = "overwrite" if sought == whole else "inplace"
        return self.write(value, new_text, operation=operation)

    def replace(self, value: str, target: str, replacement: str) -> Path:
        if not target:
            raise ValueError("target_content must not be empty")
        with self.lock:
            path = resolve_file(self.root, value, write=True)
            content = path.read_text(encoding="utf-8")
            if content.count(target) != 1:
                raise ValueError("target_content must match exactly one block")
            # M-079: a targeted replace is the in-place road.
            return self.write(value, content.replace(target, replacement, 1),
                              operation="inplace")

    def entries(self) -> list:
        """Edits still in force, oldest first (M-077).

        The edit strand of the shared undo timeline reads
        through here: each entry's id, path, and status.
        Undone and aborted edits are not on the timeline.
        """
        with self.lock, self._connect() as connection:
            self._recover(connection)
            rows = connection.execute(
                "SELECT id,path,status FROM edits "
                "WHERE status IN ('applied','conflict') ORDER BY id ASC"
            ).fetchall()
        return [{"id": row[0], "path": row[1], "status": row[2]}
                for row in rows]

    def undo(self) -> str:
        with self.lock, self._connect() as connection:
            self._recover(connection)
            row = connection.execute(
                "SELECT id,path,before,after,mode,status FROM edits "
                "WHERE status IN ('applied','conflict') ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if not row:
                return "No agent edit to undo in this workspace."
            entry_id, name, before, after, mode, status = row
            path = resolve_file(self.root, name, write=True)
            changed_mode = path.exists() and stat.S_IMODE(path.stat().st_mode) != mode
            if status == "conflict" or self._contents(path) != after or changed_mode:
                return "Undo refused: the file changed after the agent edit; your work is preserved."
            connection.execute("UPDATE edits SET status='undo_prepared' WHERE id=?", (entry_id,))
            connection.commit()
            if before is None:
                path.unlink()  # Explicit undo of the unchanged agent-created file.
            else:
                atomic_write(path, before, mode)
            connection.execute("UPDATE edits SET status='undone' WHERE id=?", (entry_id,))
            connection.commit()
            return f"Restored the last agent edit: {name}. Git history and index were preserved."
