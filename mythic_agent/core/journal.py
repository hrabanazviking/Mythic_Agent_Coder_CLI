"""Write-ahead journal for session checkpoints and structured crash reports.

Every session state mutation is first appended to a durable journal file
*before* it is applied to the SQLite store.  If the process dies between the
journal append and the store commit, the next startup detects the uncommitted
entries and can replay them, so no checkpoint is silently lost.

Journal layout: one JSON record per line.  Each record carries a checksum so a
torn or corrupted line is detected and skipped rather than applied.

Appends are atomic: the whole file is rewritten through a temporary file plus
``os.replace`` (with fsync) while holding a cross-process file lock, so readers
never observe a half-written journal.
"""


from __future__ import annotations

__all__ = [
    "Any",
    "CRASH_REPORT_VERSION",
    "CorruptJournalLine",
    "FileLock",
    "JOURNAL_SCHEMA_VERSION",
    "Path",
    "WriteAheadLog",
    "datetime",
    "timezone",
    "write_crash_report",
]

import hashlib
import json
import os
import platform
import sys
import tempfile
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .exceptions import MythicJournalError
from typing import Any

from filelock import FileLock

JOURNAL_SCHEMA_VERSION = 1
CRASH_REPORT_VERSION = 1


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _checksum(record: dict[str, Any]) -> str:
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":"),
                           allow_nan=False, ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class CorruptJournalLine(MythicJournalError):
    """A journal line failed checksum/parse validation; it is skipped."""


class WriteAheadLog:
    """Append-only write-ahead log with commit tombstones.

    Usage pattern for a state mutation::

        journal_id = wal.append_checkpoint(session_id, checkpoint, event)
        try:
            store.apply_mutation(...)   # the real write
        except Exception:
            raise                   # entry stays pending -> recovered later
        wal.commit(journal_id)      # tombstone: mutation is durable

    If ``vacuum()`` is never called the file grows forever, so appends
    automatically sweep the journal once tombstoned records pile up past
    ``auto_vacuum_threshold`` (pass ``None`` to disable and manage it by
    hand). The sweep only drops tombstoned pairs; uncommitted checkpoints
    are never swept.
    """

    def __init__(self, path: str | Path, auto_vacuum_threshold: int | None = 1000) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._lock = FileLock(str(self.path) + ".lock", timeout=10)
        self.auto_vacuum_threshold = auto_vacuum_threshold

    # ------------------------------------------------------------------ I/O

    def _read_records(self) -> list[dict[str, Any]]:
        """Read and checksum-validate every record; skip corrupt lines."""
        if not self.path.exists():
            return []
        records = []
        with self.path.open("r", encoding="utf-8") as stream:
            for line in stream:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue  # torn write: never apply a partial line
                if not isinstance(record, dict):
                    continue
                expected = record.get("checksum")
                body = {k: v for k, v in record.items() if k != "checksum"}
                if not isinstance(expected, str) or _checksum(body) != expected:
                    continue  # corrupted line: skip, never apply
                records.append(record)
        return records

    def _write_records(self, records: list[dict[str, Any]]) -> None:
        """Atomically replace the journal via temp file + rename + fsync."""
        fd, temporary = tempfile.mkstemp(prefix=".journal-", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "wb") as stream:
                for record in records:
                    body = {k: v for k, v in record.items() if k != "checksum"}
                    stamped = {**body, "checksum": _checksum(body)}
                    stream.write((json.dumps(stamped, allow_nan=False) + "\n").encode("utf-8"))
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, self.path)
            # fsync the directory so the rename itself survives a crash
            dir_fd = os.open(str(self.path.parent), os.O_DIRECTORY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def _append_record(self, record: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            records = self._read_records()
            record = {"v": JOURNAL_SCHEMA_VERSION, "ts": _utcnow(), **record}
            record["seq"] = max((r.get("seq", 0) for r in records), default=0) + 1
            records.append(record)
            self._write_records(records)
            if (self.auto_vacuum_threshold is not None
                    and sum(1 for r in records if r.get("op") == "tombstone")
                    > self.auto_vacuum_threshold):
                self._vacuum_locked()
            return record

    # ------------------------------------------------------------- public API

    def append_checkpoint(self, session_id: str, checkpoint: dict[str, Any],
                          event: dict[str, Any] | None = None) -> str:
        """Journal a checkpoint intent *before* applying it. Returns journal id."""
        json.dumps(checkpoint, allow_nan=False)  # fail fast on unserializable state
        journal_id = uuid.uuid4().hex
        self._append_record({"op": "checkpoint", "journal_id": journal_id,
                             "session_id": session_id,
                             "checkpoint": checkpoint, "event": event})
        return journal_id

    def commit(self, journal_id: str) -> None:
        """Mark a journaled mutation as durably applied (tombstone record)."""
        self._append_record({"op": "tombstone", "journal_id": journal_id})

    def pending(self) -> list[dict[str, Any]]:
        """Checkpoint entries journaled but never committed, oldest first."""
        with self._lock:
            records = self._read_records()
        committed = {r["journal_id"] for r in records
                     if r.get("op") == "tombstone" and isinstance(r.get("journal_id"), str)}
        return [r for r in sorted(records, key=lambda r: r.get("seq", 0))
                if r.get("op") == "checkpoint" and r.get("journal_id") not in committed]

    def has_pending(self) -> bool:
        return bool(self.pending())

    def vacuum(self) -> int:
        """Rewrite the journal dropping tombstoned entries; returns records kept."""
        with self._lock:
            return self._vacuum_locked()

    def _vacuum_locked(self) -> int:
        """Vacuum assuming the caller already holds ``self._lock``."""
        records = self._read_records()
        committed = {r["journal_id"] for r in records
                     if r.get("op") == "tombstone" and isinstance(r.get("journal_id"), str)}
        live = [r for r in records
                if not (r.get("op") == "tombstone"
                        or (r.get("op") == "checkpoint" and r.get("journal_id") in committed))]
        self._write_records(live)
        return len(live)

    def discard(self) -> None:
        """Drop the entire journal (clean shutdown with nothing pending)."""
        with self._lock:
            self._write_records([])


# ------------------------------------------------------------ crash reports

def write_crash_report(exc: BaseException, *, session_id: str | None = None,
                       mythic_dir: str | Path | None = None,
                       redactor: Any | None = None) -> Path:
    """Write a structured JSON crash report to ``~/.mythic/crashes/``.

    Replaces the ad-hoc ``mythic_crash_*.txt`` dumps with a machine-readable
    report carrying timestamp, traceback, and session id.
    """
    root = Path(mythic_dir).expanduser() if mythic_dir else Path.home() / ".mythic"
    crashes = root / "crashes"
    crashes.mkdir(parents=True, exist_ok=True, mode=0o700)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = crashes / f"crash_{stamp}_{os.getpid()}.json"

    report = {
        "schema_version": CRASH_REPORT_VERSION,
        "timestamp": _utcnow(),
        "session_id": session_id,
        "exception_type": type(exc).__name__,
        "exception_message": str(exc),
        "traceback": traceback.format_exception(exc),
        "python_version": sys.version,
        "platform": platform.platform(),
        "pid": os.getpid(),
    }
    if redactor is not None:
        try:
            report = redactor.sanitize(report)
        except Exception:
            pass
    payload = (json.dumps(report, indent=2, allow_nan=False) + "\n").encode("utf-8")

    fd, temporary = tempfile.mkstemp(prefix=".crash-", dir=str(crashes))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return path
