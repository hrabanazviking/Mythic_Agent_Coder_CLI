"""Workspace-scoped transcripts with atomic checkpoints and exclusive leases."""

import copy
import json
import os
import re
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from filelock import FileLock, Timeout

from .redaction import SecretRedactor
from .workspace import workspace_id


class SessionBusy(RuntimeError):
    """Another attached agent/process owns this session."""


def validate_session_id(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{32}", value):
        raise ValueError("Session ID must be 32 lowercase hexadecimal characters")
    return value


def validate_messages(messages: Any) -> dict[str, dict[str, Any]]:
    """Validate the chat protocol; return final calls still awaiting a result."""
    if (not isinstance(messages, list) or not messages or not isinstance(messages[0], dict)
            or messages[0].get("role") != "system"):
        raise ValueError("Session context must start with a system message")
    pending = {}
    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            raise ValueError("Session messages must be objects")
        role = message.get("role")
        if role not in {"system", "user", "assistant", "tool"}:
            raise ValueError("Unsupported session message role")
        if role == "system" and index != 0:
            raise ValueError("Only the first message may be a system message")
        content = message.get("content")
        if not isinstance(content, str) and not (role == "assistant" and content is None):
            raise ValueError("Session content must be text")
        if role == "tool":
            call_id = message.get("tool_call_id")
            if not isinstance(call_id, str) or call_id not in pending:
                raise ValueError("Tool result has no matching pending call")
            pending.pop(call_id)
        else:
            if pending:
                raise ValueError("Tool results must complete before the next message")
            calls = message.get("tool_calls", [])
            if not isinstance(calls, list) or (calls and role != "assistant"):
                raise ValueError("Invalid session tool calls")
            for call in calls:
                if not isinstance(call, dict):
                    raise ValueError("Tool calls must be objects")
                call_id, function = call.get("id"), call.get("function")
                if (not isinstance(call_id, str) or not call_id or call_id in pending
                        or call.get("type") != "function" or not isinstance(function, dict)
                        or not isinstance(function.get("name"), str)
                        or not isinstance(function.get("arguments"), str)):
                    raise ValueError("Invalid session tool call")
                pending[call_id] = call
    json.dumps(messages, allow_nan=False)
    return pending


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionStore:
    SCHEMA_VERSION = 1
    STATUSES = {"idle", "running", "completed", "failed", "cancelled", "interrupted"}

    def __init__(self, workspace: Path, state_root: Path, redactor: SecretRedactor | None = None):
        self.workspace = Path(workspace).resolve()
        self.root = Path(state_root) / "sessions" / workspace_id(self.workspace)
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = self.root / "sessions.sqlite"
        self.redactor = redactor or SecretRedactor({})
        self._leases: dict[str, FileLock] = {}
        with FileLock(str(self.root / "initialize.lock"), timeout=10):
            try:
                descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError:
                pass
            else:
                os.close(descriptor)
            with self._connection() as connection:
                version = connection.execute("PRAGMA user_version").fetchone()[0]
                if version not in {0, self.SCHEMA_VERSION}:
                    raise ValueError("Unsupported session storage version; original preserved")
                connection.executescript("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id TEXT PRIMARY KEY, schema_version INTEGER NOT NULL,
                        created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                        status TEXT NOT NULL, context TEXT NOT NULL,
                        total_tokens INTEGER NOT NULL, metadata TEXT NOT NULL, outcome TEXT
                    );
                    CREATE TABLE IF NOT EXISTS events (
                        sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL REFERENCES sessions(id),
                        created_at TEXT NOT NULL, payload TEXT NOT NULL
                    );
                """)
                connection.execute(f"PRAGMA user_version={self.SCHEMA_VERSION}")

    @contextmanager
    def _connection(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA synchronous=FULL")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _acquire(self, session_id: str) -> None:
        validate_session_id(session_id)
        if session_id in self._leases:
            raise SessionBusy("Session already attached; close it before resuming")
        lock = FileLock(str(self.root / f"{session_id}.lock"))
        try:
            lock.acquire(timeout=0)
        except Timeout as exc:
            raise SessionBusy("Session is in use by another process; close that session first") from exc
        self._leases[session_id] = lock

    def release(self, session_id: str) -> None:
        lock = self._leases.pop(session_id, None)
        if lock:
            lock.release()

    def create(self, messages: list[dict[str, Any]], metadata: dict[str, Any]) -> str:
        validate_messages(messages)
        session_id, now = uuid.uuid4().hex, _now()
        self._acquire(session_id)
        try:
            with self._connection() as connection:
                connection.execute("INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (
                    session_id, self.SCHEMA_VERSION, now, now, "idle",
                    json.dumps(messages, allow_nan=False), 0,
                    json.dumps(self.redactor.sanitize(metadata), allow_nan=False), None))
                self._insert_event(connection, session_id, {"type": "created", "messages": messages})
        except Exception:
            self.release(session_id)
            raise
        return session_id

    @staticmethod
    def _insert_event(connection, session_id: str, event: dict[str, Any]) -> None:
        connection.execute("INSERT INTO events (session_id, created_at, payload) VALUES (?, ?, ?)",
                           (session_id, _now(), json.dumps(event, allow_nan=False)))

    @staticmethod
    def _decode(row) -> dict[str, Any]:
        if row is None:
            raise ValueError("Session not found in this workspace")
        data = dict(row)
        if data["schema_version"] != SessionStore.SCHEMA_VERSION:
            raise ValueError("Unsupported session version; original preserved")
        for key in ("context", "metadata", "outcome"):
            data[key] = json.loads(data[key]) if data[key] is not None else None
        validate_messages(data["context"])
        if (data["status"] not in SessionStore.STATUSES
                or not isinstance(data["metadata"], dict)
                or not isinstance(data["total_tokens"], int) or data["total_tokens"] < 0
                or (data["outcome"] is not None and not isinstance(data["outcome"], dict))):
            raise ValueError("Invalid session checkpoint; original preserved")
        return data

    def load(self, session_id: str) -> dict[str, Any]:
        validate_session_id(session_id)
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
        return self._decode(row)

    def resume(self, session_id: str) -> dict[str, Any]:
        self._acquire(session_id)
        try:
            data = self.load(session_id)
            pending = validate_messages(data["context"])
            if pending or data["status"] == "running":
                recovered = [{"role": "tool", "tool_call_id": call_id,
                              "content": "Interrupted before a result was recorded. Execution may have completed; inspect workspace before retrying. No tool was re-executed."}
                             for call_id in pending]
                context = data["context"] + recovered
                outcome = {"status": "interrupted", "error": "Previous process ended during a turn; inspect progress before continuing."}
                self.checkpoint(session_id, context, "interrupted", data["total_tokens"], outcome,
                                {"type": "recovered", "messages": recovered, "outcome": outcome})
                data = self.load(session_id)
            return data
        except Exception:
            self.release(session_id)
            raise

    def checkpoint(self, session_id: str, messages: list[dict[str, Any]], status: str,
                   total_tokens: int, outcome: dict[str, Any] | None = None,
                   event: dict[str, Any] | None = None) -> None:
        if session_id not in self._leases or not self._leases[session_id].is_locked:
            raise SessionBusy("A session lease is required to write a checkpoint")
        validate_messages(messages)
        if status not in self.STATUSES or isinstance(total_tokens, bool) or not isinstance(total_tokens, int) or total_tokens < 0:
            raise ValueError("Invalid session outcome")
        context = json.dumps(messages, allow_nan=False)
        encoded_outcome = json.dumps(outcome, allow_nan=False) if outcome is not None else None
        with self._connection() as connection:
            cursor = connection.execute("UPDATE sessions SET updated_at=?, status=?, context=?, total_tokens=?, outcome=? WHERE id=?",
                                        (_now(), status, context, total_tokens, encoded_outcome, session_id))
            if cursor.rowcount != 1:
                raise ValueError("Session not found in this workspace")
            if event:
                self._insert_event(connection, session_id, event)

    def list_sessions(self) -> list[dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute("SELECT id, schema_version, created_at, updated_at, status, total_tokens, metadata FROM sessions ORDER BY updated_at DESC, id").fetchall()
        return self.redactor.sanitize([{**dict(row), "metadata": json.loads(row["metadata"])} for row in rows])

    def export(self, session_id: str) -> dict[str, Any]:
        validate_session_id(session_id)
        # One read transaction gives a consistent context/transcript snapshot.
        with self._connection() as connection:
            connection.execute("BEGIN")
            data = self._decode(connection.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone())
            events = [{"sequence": row["sequence"], "created_at": row["created_at"],
                       **json.loads(row["payload"])} for row in connection.execute(
                           "SELECT * FROM events WHERE session_id=? ORDER BY sequence", (session_id,))]
        return self.redactor.sanitize({**copy.deepcopy(data), "workspace": str(self.workspace), "events": events})
