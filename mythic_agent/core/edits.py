"""Atomic file edits with a durable journal and conservative undo."""

import os
import sqlite3
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from filelock import FileLock

from .config_manager import config_manager
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
    def __init__(self, root: Path):
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

    def write(self, value: str, text: str) -> Path:
        if not isinstance(text, str):
            raise ValueError("content must be a string")
        with self.lock, self._connect() as connection:
            self._recover(connection)
            path = resolve_file(self.root, value, write=True)
            before = self._contents(path)
            after = text.encode("utf-8")
            if before == after:
                return path
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
            return path

    def replace(self, value: str, target: str, replacement: str) -> Path:
        if not target:
            raise ValueError("target_content must not be empty")
        with self.lock:
            path = resolve_file(self.root, value, write=True)
            content = path.read_text(encoding="utf-8")
            if content.count(target) != 1:
                raise ValueError("target_content must match exactly one block")
            return self.write(value, content.replace(target, replacement, 1))

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
