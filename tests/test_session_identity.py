"""R-019: session identity invariants.

Session ID scheme (as found in ``mythic_agent/core/sessions.py``):
  * IDs are generated store-side by ``SessionStore.create()`` via
    ``uuid.uuid4().hex`` -- 122 bits of entropy (RFC 4122 v4 reserves 6 bits),
    rendered as 32 lowercase hexadecimal characters.
  * ``validate_session_id`` enforces the ``[0-9a-f]{32}`` format on every
    entry point.
  * ``create()`` takes NO session-id parameter, so a caller cannot supply an
    explicit ID: duplicate creation is impossible by construction, and every
    call deterministically mints a fresh ID.  The tests below lock that in.
"""

import fcntl
import inspect
import os
import re
import sqlite3
import time

import pytest

from mythic_agent.core.sessions import (
    SessionBusy,
    SessionStore,
    validate_session_id,
)

MSGS = [
    {"role": "system", "content": "You are a test harness."},
    {"role": "user", "content": "hello"},
]

ID_RE = re.compile(r"[0-9a-f]{32}")


@pytest.fixture
def store(tmp_path):
    workspace = tmp_path / "ws"
    workspace.mkdir()
    return SessionStore(workspace, tmp_path / "state")


def test_session_ids_unique_across_1000_creations(store):
    ids = []
    for _ in range(1000):
        session_id = store.create(MSGS, {})
        assert ID_RE.fullmatch(session_id), f"bad id format: {session_id!r}"
        validate_session_id(session_id)
        ids.append(session_id)
        store.release(session_id)  # avoid holding 1000 lock fds at once
    assert len(set(ids)) == 1000, "session IDs must be unique across many creations"


def test_id_scheme_carries_122_bits_of_entropy():
    # uuid4().hex: 32 hex chars = 128 bits of text, 122 bits of entropy
    # (RFC 4122 v4 reserves 6 bits for version/variant).
    import uuid

    sample = uuid.uuid4().hex
    assert len(sample) == 32
    assert ID_RE.fullmatch(sample)
    assert (len(sample) * 4) - 6 == 122


def test_create_takes_no_explicit_id():
    # Regression lock: callers cannot force a duplicate ID; create() always
    # mints a fresh one, so "create twice with the same ID" is impossible.
    params = inspect.signature(SessionStore.create).parameters
    assert "id" not in params and "session_id" not in params


def test_two_creations_never_collide(store):
    first = store.create(MSGS, {})
    store.release(first)
    second = store.create(MSGS, {})
    store.release(second)
    assert first != second


def test_resume_unknown_id_is_deterministic(store):
    unknown = "a" * 32  # well-formed, but no such session
    with pytest.raises(ValueError, match="Session not found in this workspace"):
        store.resume(unknown)
    # Repeating raises the same error: the failed resume must not leak its
    # lease (otherwise this would be SessionBusy instead).
    with pytest.raises(ValueError, match="Session not found in this workspace"):
        store.resume(unknown)


def test_corrupt_sqlite_file_names_the_file(tmp_path):
    workspace = tmp_path / "ws"
    workspace.mkdir()
    state = tmp_path / "state"
    SessionStore(workspace, state)
    db_path = next((state / "sessions").rglob("sessions.sqlite"))
    db_path.write_bytes(b"\x00\x01garbage-not-a-sqlite-database" * 64)
    with pytest.raises(ValueError, match=re.escape("sessions.sqlite")):
        SessionStore(workspace, state)


def test_malformed_context_json_names_file_and_session(store):
    session_id = store.create(MSGS, {})
    store.release(session_id)
    with sqlite3.connect(store.path) as connection:
        connection.execute(
            "UPDATE sessions SET context=? WHERE id=?", ('{"broken json', session_id)
        )
        connection.commit()
    with pytest.raises(ValueError) as excinfo:
        store.load(session_id)
    message = str(excinfo.value)
    assert "sessions.sqlite" in message
    assert session_id in message


def _hold_raw_flock(path):
    """Hold an exclusive flock like a live process would (not via filelock)."""
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    return fd


def test_stale_lock_file_does_not_wedge_new_session(tmp_path):
    workspace = tmp_path / "ws"
    workspace.mkdir()
    state = tmp_path / "state"
    store = SessionStore(workspace, state)
    session_id = store.create(MSGS, {})
    store.release(session_id)
    lock_path = store.root / f"{session_id}.lock"

    # Simulate a crashed process: it held the lock, then died -- the OS
    # closed its fd (releasing the flock) but the lock FILE remains on disk.
    fd = _hold_raw_flock(lock_path)
    os.close(fd)
    assert lock_path.exists(), "stale lock file must remain to prove the point"

    start = time.monotonic()
    fresh = SessionStore(workspace, state)
    data = fresh.resume(session_id)
    fresh.release(session_id)
    elapsed = time.monotonic() - start
    assert elapsed < 10, f"stale lock wedged the session ({elapsed:.1f}s)"
    assert data["id"] == session_id


def test_live_lock_holder_gets_clear_busy_error(tmp_path):
    workspace = tmp_path / "ws"
    workspace.mkdir()
    state = tmp_path / "state"
    store = SessionStore(workspace, state)
    session_id = store.create(MSGS, {})
    store.release(session_id)
    lock_path = store.root / f"{session_id}.lock"

    fd = _hold_raw_flock(lock_path)  # another live process owns this session
    try:
        start = time.monotonic()
        with pytest.raises(SessionBusy, match="in use"):
            store.resume(session_id)
        assert time.monotonic() - start < 10, "busy check must not hang"
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)

    # Once the holder is gone, the session opens cleanly again.
    data = store.resume(session_id)
    store.release(session_id)
    assert data["id"] == session_id
