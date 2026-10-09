"""Write-ahead journal, crash recovery, and structured crash reports."""

import json
from pathlib import Path

import pytest

from mythic_agent.core.journal import WriteAheadLog, write_crash_report
from mythic_agent.core.sessions import SessionStore


def wal_for(tmp_path):
    return WriteAheadLog(tmp_path / "journal.log")


def store_for(tmp_path, workspace=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state")


def messages():
    return [{"role": "system", "content": "Fixture system"},
            {"role": "user", "content": "hello"}]


def checkpoint_payload(extra_user_text="second turn"):
    return {"messages": messages() + [{"role": "user", "content": extra_user_text}],
            "status": "running", "total_tokens": 42, "outcome": None}


# ------------------------------------------------------- WriteAheadLog basics

def test_append_makes_entry_pending(tmp_path):
    wal = wal_for(tmp_path)
    assert not wal.has_pending()
    journal_id = wal.append_checkpoint("abc123", checkpoint_payload(), {"type": "note"})
    pending = wal.pending()
    assert len(pending) == 1
    assert pending[0]["journal_id"] == journal_id
    assert pending[0]["session_id"] == "abc123"
    assert pending[0]["checkpoint"]["total_tokens"] == 42
    assert pending[0]["event"] == {"type": "note"}
    assert wal.has_pending()


def test_commit_clears_pending(tmp_path):
    wal = wal_for(tmp_path)
    journal_id = wal.append_checkpoint("abc123", checkpoint_payload())
    wal.commit(journal_id)
    assert wal.pending() == []
    assert not wal.has_pending()


def test_multiple_entries_recover_oldest_first(tmp_path):
    wal = wal_for(tmp_path)
    first = wal.append_checkpoint("s1", checkpoint_payload("one"))
    second = wal.append_checkpoint("s2", checkpoint_payload("two"))
    wal.commit(first)
    pending = wal.pending()
    assert [p["journal_id"] for p in pending] == [second]
    assert pending[0]["checkpoint"]["messages"][-1]["content"] == "two"


def test_journal_survives_new_instance_unclean_shutdown(tmp_path):
    """Simulates a kill between journal append and commit: a fresh WAL sees it."""
    wal = wal_for(tmp_path)
    journal_id = wal.append_checkpoint("s1", checkpoint_payload())
    del wal  # process "dies" here; commit() never runs
    fresh = WriteAheadLog(tmp_path / "journal.log")
    pending = fresh.pending()
    assert len(pending) == 1 and pending[0]["journal_id"] == journal_id


def test_corrupt_line_is_skipped_never_applied(tmp_path):
    wal = wal_for(tmp_path)
    good = wal.append_checkpoint("s1", checkpoint_payload())
    path = tmp_path / "journal.log"
    lines = path.read_text(encoding="utf-8").splitlines()
    tampered = json.loads(lines[-1])
    tampered["checkpoint"]["total_tokens"] = 999999  # breaks the checksum
    lines[-1] = json.dumps(tampered)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert wal_for(tmp_path).pending() == []  # corrupt entry must not recover


def test_torn_write_partial_line_is_skipped(tmp_path):
    wal = wal_for(tmp_path)
    wal.append_checkpoint("s1", checkpoint_payload())
    with open(tmp_path / "journal.log", "a", encoding="utf-8") as fh:
        fh.write('{"v": 1, "op": "checkpo')  # torn line: kill mid-write
        fh.flush()
    pending = wal_for(tmp_path).pending()
    assert len(pending) == 1
    assert pending[0]["session_id"] == "s1"


def test_vacuum_drops_tombstoned_entries(tmp_path):
    wal = wal_for(tmp_path)
    first = wal.append_checkpoint("s1", checkpoint_payload("one"))
    wal.append_checkpoint("s2", checkpoint_payload("two"))
    wal.commit(first)
    kept = wal.vacuum()
    assert kept == 1
    records = [json.loads(line) for line in
               (tmp_path / "journal.log").read_text(encoding="utf-8").splitlines()]
    assert all(r["op"] == "checkpoint" for r in records)
    assert [r["session_id"] for r in records] == ["s2"]


# ------------------------------------------------- SessionStore integration

def test_clean_checkpoint_leaves_no_pending_journal(tmp_path):
    store = store_for(tmp_path)
    session_id = store.create(messages(), {})
    store.checkpoint(session_id, messages(), "idle", 3)
    assert store.check_recovery() == []
    assert not store.journal.has_pending()
    store.release(session_id)


def test_failed_checkpoint_stays_pending_for_recovery(tmp_path):
    """Crash between journal append and SQLite apply leaves a pending entry."""
    store = store_for(tmp_path)
    session_id = store.create(messages(), {})
    store.release(session_id)
    # checkpoint() requires a live lease; release it first so the SQLite write
    # path is never reached -- journal append already happened? No: checkpoint
    # checks the lease first. Use a bogus id with a held lease instead.
    other = store_for(tmp_path)
    bogus = "0" * 32
    other._acquire(bogus)
    try:
        with pytest.raises(ValueError, match="Session not found"):
            other.checkpoint(bogus, messages(), "idle", 1)
    finally:
        other.release(bogus)
    assert other.journal.has_pending()
    # A fresh store on next startup detects it.
    assert store_for(tmp_path).check_recovery() != []


def test_crash_between_apply_and_commit_recovers_state(tmp_path):
    """Kill after the SQLite write but before the tombstone: replay is safe."""
    store = store_for(tmp_path)
    session_id = store.create(messages(), {})

    real_commit = WriteAheadLog.commit

    def dying_commit(self, journal_id):
        raise KeyboardInterrupt("simulated kill mid-checkpoint")

    WriteAheadLog.commit = dying_commit
    try:
        with pytest.raises(KeyboardInterrupt):
            store.checkpoint(session_id, checkpoint_payload()["messages"],
                             "running", 42)
    finally:
        WriteAheadLog.commit = real_commit
    # The SQLite row WAS updated (crash happened after apply)...
    assert store.load(session_id)["total_tokens"] == 42
    # ...but the journal still shows the entry as uncommitted.
    restarted = store_for(tmp_path)
    pending = restarted.check_recovery()
    assert len(pending) == 1 and pending[0]["session_id"] == session_id
    # Recovery replays idempotently and clears the journal.
    assert restarted.recover_pending() == [session_id]
    assert restarted.check_recovery() == []
    assert restarted.load(session_id)["total_tokens"] == 42
    restarted.release(session_id)


def test_crash_before_apply_recovers_lost_checkpoint(tmp_path):
    """Kill after journal append but before SQLite apply: state is restored."""
    store = store_for(tmp_path)
    session_id = store.create(messages(), {})
    payload = checkpoint_payload()
    journal_id = store.journal.append_checkpoint(
        session_id,
        {"messages": payload["messages"], "status": payload["status"],
         "total_tokens": payload["total_tokens"], "outcome": None},
        {"type": "auto"})
    assert journal_id
    del store  # process dies before checkpoint() ever runs
    restarted = store_for(tmp_path)
    assert len(restarted.check_recovery()) == 1
    assert restarted.recover_pending() == [session_id]
    data = restarted.load(session_id)
    assert data["status"] == "running"
    assert data["total_tokens"] == 42
    assert data["context"][-1]["content"] == "second turn"
    restarted.release(session_id)


def test_recovery_is_idempotent_no_duplicate_events(tmp_path):
    store = store_for(tmp_path)
    session_id = store.create(messages(), {})
    payload = checkpoint_payload()
    store.journal.append_checkpoint(
        session_id,
        {"messages": payload["messages"], "status": "running",
         "total_tokens": 42, "outcome": None}, None)
    del store
    restarted = store_for(tmp_path)
    assert restarted.recover_pending() == [session_id]
    events_before = restarted.export(session_id)["events"]
    # Second recovery pass must change nothing.
    assert restarted.recover_pending() == []
    events_after = restarted.export(session_id)["events"]
    assert events_after == events_before
    assert sum(1 for e in events_after if e.get("type") == "recovered") == 1
    restarted.release(session_id)


def test_recovery_skips_missing_session_but_clears_journal(tmp_path):
    store = store_for(tmp_path)
    session_id = store.create(messages(), {})
    payload = checkpoint_payload()
    store.journal.append_checkpoint(
        session_id,
        {"messages": payload["messages"], "status": "running",
         "total_tokens": 42, "outcome": None}, None)
    # Session row deleted out from under the journal (e.g. manual cleanup).
    with store._connection() as conn:
        conn.execute("DELETE FROM events WHERE session_id=?", (session_id,))
        conn.execute("DELETE FROM sessions WHERE id=?", (session_id,))
    del store
    restarted = store_for(tmp_path)
    assert restarted.recover_pending() == []  # nothing to replay into
    assert restarted.check_recovery() == []   # ...but journal is cleared


def test_startup_check_recovery_lists_pending_summaries(tmp_path):
    store = store_for(tmp_path)
    session_id = store.create(messages(), {})
    payload = checkpoint_payload()
    journal_id = store.journal.append_checkpoint(
        session_id,
        {"messages": payload["messages"], "status": "running",
         "total_tokens": 42, "outcome": None}, None)
    summaries = store_for(tmp_path).check_recovery()
    assert len(summaries) == 1
    assert summaries[0]["journal_id"] == journal_id
    assert summaries[0]["session_id"] == session_id
    assert summaries[0]["status"] == "running"
    assert summaries[0]["total_tokens"] == 42
    assert "recorded_at" in summaries[0]


# ---------------------------------------------------------- crash reports

def test_write_crash_report_structured_json(tmp_path):
    try:
        raise RuntimeError("boom in the test")
    except RuntimeError as exc:
        path = write_crash_report(exc, session_id="deadbeef" * 4,
                                  mythic_dir=tmp_path / ".mythic")
    assert path.parent == tmp_path / ".mythic" / "crashes"
    assert path.name.startswith("crash_") and path.suffix == ".json"
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["schema_version"] == 1
    assert report["exception_type"] == "RuntimeError"
    assert report["exception_message"] == "boom in the test"
    assert report["session_id"] == "deadbeef" * 4
    assert "timestamp" in report and "python_version" in report
    assert "platform" in report and "pid" in report
    assert any("boom in the test" in frame for frame in report["traceback"])
    # Private file permissions.
    assert path.stat().st_mode & 0o777 == 0o600


def test_write_crash_report_without_session_id(tmp_path):
    try:
        raise ValueError("no session")
    except ValueError as exc:
        path = write_crash_report(exc, mythic_dir=tmp_path / ".mythic")
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["session_id"] is None
    assert report["exception_type"] == "ValueError"
