"""
TIER: unit
Session Catalogue gate (All-Features roadmap slice M-010).

The shipped catalogue (``mythic_agent/data/session_catalog.yaml``)
is the forward-compat contract for every session/journal format.
These tests do two jobs:

1. Cross-check the catalogue against the live tree — the version
   constants, the live SQLite schema, the session record's required
   keys, a fresh crash report's keys, a fresh journal line's keys —
   so a new format or a silent version bump cannot land uncatalogued.
2. THE FORWARD-COMPAT GOLDEN TESTS (``test_golden_*``): literal
   version-1 artefacts frozen in this file — a session database
   built with raw SQL, journal lines built with raw JSON + sha256,
   a plain-dict record, a crash report, transcript spill lines —
   read back through the app's real readers. They are built with
   raw primitives, NEVER with the current writers, so if a future
   change breaks reading today's formats, these tests fail. They
   must never break, and their fixtures must never be regenerated
   to match a new writer.
"""

import copy
import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from mythic_agent.core.journal import (
    CRASH_REPORT_VERSION,
    JOURNAL_SCHEMA_VERSION,
    WriteAheadLog,
    write_crash_report,
)
from mythic_agent.core.session_catalog import (
    SessionCatalog,
    load_catalog,
    render_markdown,
    validate_catalog,
)
from mythic_agent.core.sessions import (
    SessionStore,
    session_from_dict,
    session_to_dict,
)
from mythic_agent.core.transcript import BoundedTranscript
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.workspace import workspace_id
from mythic_agent.resources import load_resource

REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Golden fixtures — frozen version-1 artefacts. DO NOT regenerate.
# ---------------------------------------------------------------------------

GOLDEN_SESSION_ID = "0123456789abcdef0123456789abcdef"
GOLDEN_MESSAGES = [
    {"role": "system", "content": "Fixture system"},
    {"role": "user", "content": "hello from the golden fixture"},
]
GOLDEN_CREATED = "2026-10-30T12:00:00+00:00"
GOLDEN_METADATA = {"origin": "golden-fixture"}
GOLDEN_OUTCOME = {"status": "ok"}

# The v1 sessions/events DDL, copied literally as frozen text.
GOLDEN_DDL = """
CREATE TABLE sessions (
    id TEXT PRIMARY KEY, schema_version INTEGER NOT NULL,
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
    status TEXT NOT NULL, context TEXT NOT NULL,
    total_tokens INTEGER NOT NULL, metadata TEXT NOT NULL, outcome TEXT
);
CREATE TABLE events (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    created_at TEXT NOT NULL, payload TEXT NOT NULL
);
"""

GOLDEN_RECORD = {
    "id": GOLDEN_SESSION_ID,
    "schema_version": 1,
    "created_at": GOLDEN_CREATED,
    "updated_at": GOLDEN_CREATED,
    "status": "completed",
    "context": GOLDEN_MESSAGES,
    "total_tokens": 42,
    "metadata": GOLDEN_METADATA,
    "outcome": GOLDEN_OUTCOME,
}

GOLDEN_CHECKPOINT = {
    "messages": GOLDEN_MESSAGES,
    "status": "running",
    "total_tokens": 42,
    "outcome": None,
}

GOLDEN_SPILL_TURNS = [
    {"role": "user", "content": "oldest golden turn"},
    {"role": "assistant", "content": "second golden turn"},
]


def _golden_journal_line(body):
    """Stamp a literal journal body the v1 way: sha256 of canonical JSON."""
    canonical = json.dumps(
        body, sort_keys=True, separators=(",", ":"), allow_nan=False, ensure_ascii=True
    )
    return json.dumps({**body, "checksum": hashlib.sha256(canonical.encode("utf-8")).hexdigest()})


@pytest.fixture(scope="module")
def catalog() -> SessionCatalog:
    return load_catalog()


def _by_name(catalog):
    return {f.name: f for f in catalog.formats}


# ---------------------------------------------------------------------------
# Catalogue cross-checks against the live tree
# ---------------------------------------------------------------------------

def test_shipped_catalogue_loads_and_validates(catalog):
    assert isinstance(catalog, SessionCatalog)
    assert validate_catalog(load_resource("session_catalog.yaml")) == []
    (n_formats,) = catalog.counts()
    assert n_formats >= 7


def test_ids_are_sequential(catalog):
    assert [f.id for f in catalog.formats] == [
        f"J-{n:02d}" for n in range(1, len(catalog.formats) + 1)]


def test_reader_modules_exist(catalog):
    for entry in catalog.formats:
        assert (REPO_ROOT / entry.reader).exists(), entry.reader


def test_live_version_constants_match_the_catalogue(catalog):
    assert catalog.version_of("session-store") == str(SessionStore.SCHEMA_VERSION)
    assert catalog.version_of("session-record") == str(SessionStore.SCHEMA_VERSION)
    assert catalog.version_of("wal-journal") == str(JOURNAL_SCHEMA_VERSION)
    assert catalog.version_of("crash-report") == str(CRASH_REPORT_VERSION)


def test_session_store_fields_match_the_live_sqlite_schema(catalog, tmp_path):
    (tmp_path / "ws").mkdir()
    store = SessionStore(tmp_path / "ws", tmp_path / "state")
    with sqlite3.connect(store.path) as conn:
        sessions_cols = {row[1] for row in conn.execute("PRAGMA table_info(sessions)")}
        events_cols = {row[1] for row in conn.execute("PRAGMA table_info(events)")}
        user_version = conn.execute("PRAGMA user_version").fetchone()[0]
    assert user_version == SessionStore.SCHEMA_VERSION
    assert set(_by_name(catalog)["session-store"].fields) == sessions_cols | events_cols


def test_session_record_fields_match_the_required_keys(catalog):
    from mythic_agent.core.sessions import _SESSION_RECORD_REQUIRED

    fields = set(_by_name(catalog)["session-record"].fields)
    assert fields == set(_SESSION_RECORD_REQUIRED) | {"outcome"}


def test_fresh_journal_line_keys_match_the_catalogue(catalog, tmp_path):
    wal = WriteAheadLog(tmp_path / "journal.log")
    wal.append_checkpoint("s1", GOLDEN_CHECKPOINT, {"type": "note"})
    line = (tmp_path / "journal.log").read_text(encoding="utf-8").splitlines()[0]
    assert set(json.loads(line)) == set(_by_name(catalog)["wal-journal"].fields)


def test_render_covers_every_format(catalog):
    text = render_markdown(catalog)
    for name in catalog.format_names():
        assert f"`{name}`" in text
        assert catalog.version_of(name) in text
    for entry in catalog.formats:
        assert entry.id in text and entry.location in text


def _tampered(mutator):
    data = copy.deepcopy(load_resource("session_catalog.yaml"))
    mutator(data)
    return data


def test_validation_rejects_a_dropped_format():
    data = _tampered(lambda d: d["formats"].pop(0))
    problems = validate_catalog(data)
    assert any("sequential" in p or "non-empty" in p for p in problems)
    with pytest.raises(ValidationError):
        load_catalog(data)


def test_validation_rejects_an_unknown_kind():
    data = _tampered(lambda d: d["formats"][0].update(kind="somewhere"))
    problems = validate_catalog(data)
    assert any("kind" in p for p in problems)


def test_validation_rejects_a_contract_without_forward_compat():
    data = _tampered(lambda d: d.update(scope_note="A list of formats."))
    problems = validate_catalog(data)
    assert any("forward-compat" in p for p in problems)


# ---------------------------------------------------------------------------
# Golden forward-compat tests — these must NEVER break
# ---------------------------------------------------------------------------

def test_golden_v1_session_database_is_readable(tmp_path):
    """A raw-SQL v1 sessions.sqlite loads through today's SessionStore."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    root = tmp_path / "state" / "sessions" / workspace_id(workspace)
    root.mkdir(parents=True)
    db_path = root / "sessions.sqlite"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(GOLDEN_DDL)
        conn.execute("PRAGMA user_version=1")
        conn.execute(
            "INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (GOLDEN_SESSION_ID, 1, GOLDEN_CREATED, GOLDEN_CREATED, "completed",
             json.dumps(GOLDEN_MESSAGES), 42, json.dumps(GOLDEN_METADATA),
             json.dumps(GOLDEN_OUTCOME)),
        )
        conn.execute(
            "INSERT INTO events (session_id, created_at, payload) VALUES (?, ?, ?)",
            (GOLDEN_SESSION_ID, GOLDEN_CREATED,
             json.dumps({"type": "created", "messages": GOLDEN_MESSAGES})),
        )
    store = SessionStore(workspace, tmp_path / "state")
    loaded = store.load(GOLDEN_SESSION_ID)
    assert loaded["id"] == GOLDEN_SESSION_ID
    assert loaded["schema_version"] == 1
    assert loaded["status"] == "completed"
    assert loaded["context"] == GOLDEN_MESSAGES
    assert loaded["total_tokens"] == 42
    assert loaded["metadata"] == GOLDEN_METADATA
    assert loaded["outcome"] == GOLDEN_OUTCOME
    exported = store.export(GOLDEN_SESSION_ID)
    assert exported["workspace"] == str(workspace.resolve())
    assert [e["type"] for e in exported["events"]] == ["created"]
    assert store.list_sessions()[0]["id"] == GOLDEN_SESSION_ID
    assert store.session_event_counts(GOLDEN_SESSION_ID)["by_type"] == {"created": 1}


def test_golden_v1_journal_lines_are_readable(tmp_path):
    """Literal v1 journal lines: committed checkpoint is gone, pending remains."""
    committed_id = "11111111111111111111111111111111"
    pending_id = "22222222222222222222222222222222"
    bodies = [
        {"v": 1, "ts": GOLDEN_CREATED, "seq": 1, "op": "checkpoint",
         "journal_id": committed_id, "session_id": GOLDEN_SESSION_ID,
         "checkpoint": GOLDEN_CHECKPOINT, "event": {"type": "note"}},
        {"v": 1, "ts": GOLDEN_CREATED, "seq": 2, "op": "tombstone",
         "journal_id": committed_id},
        {"v": 1, "ts": GOLDEN_CREATED, "seq": 3, "op": "checkpoint",
         "journal_id": pending_id, "session_id": GOLDEN_SESSION_ID,
         "checkpoint": GOLDEN_CHECKPOINT, "event": {"type": "note"}},
    ]
    path = tmp_path / "journal.log"
    path.write_text("\n".join(_golden_journal_line(b) for b in bodies) + "\n",
                    encoding="utf-8")
    pending = WriteAheadLog(path).pending()
    assert [p["journal_id"] for p in pending] == [pending_id]
    assert pending[0]["v"] == 1
    assert pending[0]["checkpoint"] == GOLDEN_CHECKPOINT
    assert pending[0]["session_id"] == GOLDEN_SESSION_ID


def test_golden_v1_session_record_round_trips():
    """The literal v1 record dict passes from_dict and to_dict unchanged."""
    record = session_from_dict(copy.deepcopy(GOLDEN_RECORD))
    assert record["id"] == GOLDEN_SESSION_ID
    assert record["context"] == GOLDEN_MESSAGES
    assert session_to_dict(record) == GOLDEN_RECORD


def test_golden_v1_crash_report_shape(catalog, tmp_path):
    """A fresh crash report carries exactly the catalogued v1 keys."""
    path = write_crash_report(ValueError("golden boom"), mythic_dir=tmp_path)
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["schema_version"] == CRASH_REPORT_VERSION == 1
    assert set(report) == set(_by_name(catalog)["crash-report"].fields)
    assert report["exception_type"] == "ValueError"
    # A literal v1 report, as written the day the format froze, parses whole.
    literal = {
        "schema_version": 1, "timestamp": GOLDEN_CREATED, "session_id": None,
        "exception_type": "RuntimeError", "exception_message": "old crash",
        "traceback": ["Traceback (most recent call last):", "RuntimeError: old crash"],
        "python_version": "3.12.0", "platform": "Linux", "pid": 1234,
    }
    assert set(literal) == set(_by_name(catalog)["crash-report"].fields)
    assert json.loads(json.dumps(literal)) == literal


def test_golden_v1_transcript_spill_lines_reconstruct(tmp_path):
    """Literal spill JSONL lines + a hot turn rebuild in original order."""
    spill = tmp_path / "spill_golden.jsonl"
    spill.write_text(
        "".join(json.dumps(turn) + "\n" for turn in GOLDEN_SPILL_TURNS),
        encoding="utf-8",
    )
    transcript = BoundedTranscript(max_tokens=10**9, spill_dir=tmp_path)
    transcript._spill_path = spill
    transcript._spill_count = len(GOLDEN_SPILL_TURNS)
    hot = {"role": "user", "content": "newest golden turn"}
    transcript.add(hot)
    assert transcript.get_all() == GOLDEN_SPILL_TURNS + [hot]
