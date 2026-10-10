"""Serialization invariants (R-016): round-trips are a tested contract.

Covers session records (``sessions.session_to_dict``/``session_from_dict``),
journal checkpoint entries (``WriteAheadLog``, already checksummed), and
config dicts (``config_manager.config_to_dict``/``config_from_dict``), plus
the canonical-JSON helpers in ``storage``.

Every malformed input must raise a ``ValueError`` naming the offending
field -- never a bare ``KeyError``/``TypeError`` traceback.
"""

import copy
import json
from datetime import datetime, timezone

import pytest

from mythic_agent.core.config_manager import config_from_dict, config_to_dict
from mythic_agent.core.journal import WriteAheadLog
from mythic_agent.core.sessions import (
    SessionStore,
    session_from_dict,
    session_to_dict,
)
from mythic_agent.core.storage import (
    canonical_json,
    decode_json_bytes,
    strict_json_loads,
)


def _messages():
    return [
        {"role": "system", "content": "Fixture system"},
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi there"},
    ]


def _store(tmp_path):
    return SessionStore(tmp_path, tmp_path / "state")


def _session_record(tmp_path):
    store = _store(tmp_path)
    session_id = store.create(_messages(), {"origin": "serialization-test"})
    store.checkpoint(session_id, _messages(), "running", 11,
                     {"status": "running", "note": "halfway"})
    record = store.load(session_id)
    store.release(session_id)
    return record


def _valid_config():
    return {
        "config_version": 3,
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com/v1",
        "api_keys": {"deepseek": "sk-test"},
        "permission_mode": "ask",
        "runtime": {
            "request_timeout": 120.0,
            "max_retries": 2,
            "max_tokens": 127000,
            "edit_lock_timeout": 20.0,
        },
        "github": {"repo_url": "", "token": ""},
        "sub_agents": [],
    }


def _checkpoint_payload():
    return {
        "messages": _messages(),
        "status": "running",
        "total_tokens": 42,
        "outcome": {"status": "running"},
    }


def _assert_value_error_naming(excinfo, *fragments):
    message = str(excinfo.value)
    for fragment in fragments:
        assert fragment in message, f"expected {fragment!r} in error: {message!r}"
    assert not isinstance(excinfo.value, (KeyError, TypeError))


# ------------------------------------------------- session record round-trip

def test_session_record_round_trip(tmp_path):
    record = _session_record(tmp_path)
    as_dict = session_to_dict(record)
    text = canonical_json(as_dict)
    revived = session_from_dict(strict_json_loads(text))
    assert revived == record
    # Timestamps travel as ISO-8601 strings and parse back.
    for field in ("created_at", "updated_at"):
        assert isinstance(as_dict[field], str)
        datetime.fromisoformat(as_dict[field])


def test_session_to_dict_accepts_datetime_objects(tmp_path):
    record = _session_record(tmp_path)
    moment = datetime(2026, 10, 10, 6, 7, 45, tzinfo=timezone.utc)
    record["created_at"] = moment
    record["updated_at"] = datetime(2026, 10, 10, 6, 8, 45)  # naive -> UTC
    as_dict = session_to_dict(record)
    assert as_dict["created_at"] == "2026-10-10T06:07:45+00:00"
    assert as_dict["updated_at"] == "2026-10-10T06:08:45+00:00"
    # Original record is untouched.
    assert record["created_at"] is moment


def test_session_to_dict_does_not_mutate_input(tmp_path):
    record = _session_record(tmp_path)
    before = copy.deepcopy(record)
    session_to_dict(record)
    assert record == before


def test_session_canonical_form_byte_identical(tmp_path):
    record = _session_record(tmp_path)
    first = canonical_json(session_to_dict(record))
    second = canonical_json(session_to_dict(record))
    assert first == second
    assert isinstance(first, str)


# ------------------------------------------------ journal checkpoint entries

def test_journal_checkpoint_entry_round_trip(tmp_path):
    checkpoint = _checkpoint_payload()
    text = canonical_json(checkpoint)
    assert strict_json_loads(text) == checkpoint

    wal = WriteAheadLog(tmp_path / "journal.log")
    journal_id = wal.append_checkpoint("abc123", checkpoint, {"type": "note"})
    pending = wal.pending()
    assert len(pending) == 1
    entry = pending[0]
    assert entry["journal_id"] == journal_id
    assert entry["checkpoint"] == checkpoint
    assert entry["event"] == {"type": "note"}
    # The journaled record itself survives a JSON round-trip intact.
    assert strict_json_loads(canonical_json(entry))["checkpoint"] == checkpoint


def test_journal_rejects_nan_checkpoint_fail_fast(tmp_path):
    wal = WriteAheadLog(tmp_path / "journal.log")
    bad = dict(_checkpoint_payload(), total_tokens=float("nan"))
    with pytest.raises(ValueError):
        wal.append_checkpoint("abc123", bad)


def test_journal_skips_checksum_tampered_line(tmp_path):
    path = tmp_path / "journal.log"
    wal = WriteAheadLog(path)
    wal.append_checkpoint("abc123", _checkpoint_payload())
    assert wal.has_pending()
    lines = path.read_text(encoding="utf-8").splitlines()
    tampered = json.loads(lines[0])
    tampered["checksum"] = "0" * 64
    path.write_text(json.dumps(tampered) + "\n", encoding="utf-8")
    assert WriteAheadLog(path).pending() == []


# ------------------------------------------------------- config dicts

def test_config_dict_round_trip_with_nested_runtime():
    config = _valid_config()
    as_dict = config_to_dict(config)
    text = canonical_json(as_dict)
    revived = config_from_dict(strict_json_loads(text))
    assert revived == config
    assert revived["runtime"]["max_retries"] == 2


def test_config_canonical_form_byte_identical_across_key_order():
    first = canonical_json(config_to_dict(_valid_config()))
    shuffled = dict(reversed(list(_valid_config().items())))
    second = canonical_json(config_to_dict(shuffled))
    assert first == second
    # Canonical means sorted keys, no insignificant whitespace.
    assert first == json.dumps(json.loads(first), sort_keys=True, separators=(",", ":"))


def test_config_to_dict_does_not_mutate_input():
    config = _valid_config()
    before = copy.deepcopy(config)
    config_to_dict(config)
    assert config == before


# ------------------------------------------------------- malformed inputs

@pytest.mark.parametrize("bad", ["nope", 42, ["id"], None])
def test_session_from_dict_rejects_non_objects(bad):
    with pytest.raises(ValueError, match="session record") as excinfo:
        session_from_dict(bad)
    _assert_value_error_naming(excinfo, "session record")


def test_session_from_dict_missing_key_names_field(tmp_path):
    record = _session_record(tmp_path)
    del record["status"]
    with pytest.raises(ValueError, match="session record field 'status'") as excinfo:
        session_from_dict(record)
    _assert_value_error_naming(excinfo, "session record field 'status'", "missing")


@pytest.mark.parametrize("field,value,fragment", [
    ("id", "not-a-session-id", "session record field 'id'"),
    ("id", 123, "session record field 'id'"),
    ("schema_version", "1", "session record field 'schema_version'"),
    ("schema_version", True, "session record field 'schema_version'"),
    ("schema_version", 999, "session record field 'schema_version'"),
    ("created_at", "not-a-date", "session record field 'created_at'"),
    ("created_at", "2026-13-99T99:99:99", "session record field 'created_at'"),
    ("created_at", 12345, "session record field 'created_at'"),
    ("updated_at", None, "session record field 'updated_at'"),
    ("status", "bogus", "session record field 'status'"),
    ("context", "just a string", "session record field 'context'"),
    ("total_tokens", "many", "session record field 'total_tokens'"),
    ("total_tokens", -3, "session record field 'total_tokens'"),
    ("total_tokens", True, "session record field 'total_tokens'"),
    ("metadata", ["not", "a", "dict"], "session record field 'metadata'"),
    ("outcome", "done?", "session record field 'outcome'"),
])
def test_session_from_dict_wrong_types_name_field(tmp_path, field, value, fragment):
    record = _session_record(tmp_path)
    record[field] = value
    with pytest.raises(ValueError, match=fragment) as excinfo:
        session_from_dict(record)
    _assert_value_error_naming(excinfo, fragment)


def test_session_from_dict_rejects_invalid_chat_protocol(tmp_path):
    record = _session_record(tmp_path)
    record["context"] = [{"role": "user", "content": "no system message first"}]
    with pytest.raises(ValueError, match="session record field 'context'") as excinfo:
        session_from_dict(record)
    _assert_value_error_naming(excinfo, "session record field 'context'")


def test_session_decode_rejects_bad_timestamp(tmp_path):
    store = _store(tmp_path)
    session_id = store.create(_messages(), {})
    row = dict(store.load(session_id))
    row["created_at"] = "yesterday-ish"
    row["context"] = json.dumps(row["context"])
    row["metadata"] = json.dumps(row["metadata"])
    row["outcome"] = None
    with pytest.raises(ValueError, match="created_at"):
        SessionStore._decode(row)
    store.release(session_id)


def test_config_from_dict_rejects_non_objects():
    with pytest.raises(ValueError, match="config") as excinfo:
        config_from_dict(["model"])
    _assert_value_error_naming(excinfo, "config")


@pytest.mark.parametrize("mutate,fragment", [
    (lambda c: c.update(model=""), "model"),
    (lambda c: c.update(model=123), "model"),
    (lambda c: c.update(base_url="not a url"), "base_url"),
    (lambda c: c["runtime"].update(max_retries="two"), "runtime.max_retries"),
    (lambda c: c["runtime"].update(max_tokens=0), "runtime.max_tokens"),
    (lambda c: c.update(permission_mode="yolo"), "permission_mode"),
    (lambda c: c.update(config_version=0), "config_version"),
    (lambda c: c.pop("model"), "model"),
])
def test_config_from_dict_names_bad_fields(mutate, fragment):
    config = _valid_config()
    mutate(config)
    with pytest.raises(ValueError, match=fragment.replace(".", r"\.")) as excinfo:
        config_from_dict(config)
    _assert_value_error_naming(excinfo, fragment)


# ------------------------------------------------- non-UTF8 / NaN payloads

def test_canonical_json_rejects_nan_and_infinity():
    for bad in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValueError, match="[Nn]on-finite|[Jj]SON-serializable|not JSON compliant"):
            canonical_json({"value": bad})


def test_canonical_json_rejects_non_serializable():
    with pytest.raises(ValueError, match="not JSON-serializable"):
        canonical_json({"value": object()})


def test_strict_json_loads_rejects_nan_constants():
    with pytest.raises(ValueError, match="non-finite JSON constant"):
        strict_json_loads('{"value": NaN}')
    with pytest.raises(ValueError, match="non-finite JSON constant"):
        strict_json_loads('{"value": Infinity}')


def test_strict_json_loads_rejects_malformed_and_non_text():
    with pytest.raises(ValueError, match="invalid JSON payload"):
        strict_json_loads('{"value": ')
    with pytest.raises(ValueError, match="must be text"):
        strict_json_loads(b'{"value": 1}')


def test_decode_json_bytes_rejects_non_utf8():
    with pytest.raises(ValueError, match="not valid UTF-8"):
        decode_json_bytes(b"\xff\xfe\x00bad")
    with pytest.raises(ValueError, match="must be bytes"):
        decode_json_bytes('{"value": 1}')
    assert decode_json_bytes('{"value": 1}'.encode("utf-8")) == '{"value": 1}'


def test_session_to_dict_rejects_nan_metadata(tmp_path):
    record = _session_record(tmp_path)
    record["metadata"] = {"score": float("nan")}
    with pytest.raises(ValueError, match="session record"):
        session_to_dict(record)


def test_config_to_dict_rejects_nan(tmp_path):
    config = _valid_config()
    config["runtime"]["request_timeout"] = float("nan")
    with pytest.raises(ValueError, match="config"):
        config_to_dict(config)
    with pytest.raises(ValueError, match="config"):
        config_from_dict(config)


# ------------------------------------------------- canonical JSON invariants

def test_canonical_json_sorts_keys_and_compacts():
    assert canonical_json({"b": 1, "a": [3, 2]}) == '{"a":[3,2],"b":1}'
    assert canonical_json({"b": 1, "a": 2}) == canonical_json({"a": 2, "b": 1})


def test_canonical_json_is_ascii_safe():
    text = canonical_json({"note": "héllo wörld ☃"})
    text.encode("ascii")  # raises if not ASCII-safe
    assert strict_json_loads(text)["note"] == "héllo wörld ☃"
