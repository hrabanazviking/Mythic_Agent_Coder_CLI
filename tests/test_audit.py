"""Slice 46: audit logging."""

import json

import pytest

from mythic_agent.core.audit import AuditEntry, AuditLog


def test_log_and_query(tmp_path):
    audit = AuditLog(tmp_path)
    audit.log("tool.execute", actor="primary", details={"tool": "run_command"})
    entries = audit.query()
    assert len(entries) == 1
    e = entries[0]
    assert e.action == "tool.execute"
    assert e.actor == "primary"
    assert e.details["tool"] == "run_command"
    assert e.timestamp


def test_append_only(tmp_path):
    audit = AuditLog(tmp_path)
    audit.log("file.write", actor="primary")
    audit.log("tool.execute", actor="sub")
    audit.log("permission.decision", actor="primary")
    lines = (tmp_path / ".mythic" / "audit.jsonl").read_text().strip().splitlines()
    assert len(lines) == 3
    for line in lines:
        json.loads(line)  # valid JSON, one object per line


def test_query_filters_by_action(tmp_path):
    audit = AuditLog(tmp_path)
    audit.log("tool.execute", actor="primary")
    audit.log("file.write", actor="primary")
    entries = audit.query({"action": "file.write"})
    assert len(entries) == 1
    assert entries[0].action == "file.write"


def test_query_filters_by_nested_details(tmp_path):
    audit = AuditLog(tmp_path)
    audit.log("tool.execute", actor="primary", details={"tool": "read_file"})
    audit.log("tool.execute", actor="primary", details={"tool": "run_command"})
    entries = audit.query({"details": {"tool": "run_command"}})
    assert len(entries) == 1
    assert entries[0].details["tool"] == "run_command"


def test_query_empty_log(tmp_path):
    audit = AuditLog(tmp_path)
    assert audit.query() == []
    assert audit.count() == 0


def test_convenience_recorders(tmp_path):
    audit = AuditLog(tmp_path)
    audit.log_tool_execution("primary", "run_command", {"command": "ls"}, "ok")
    audit.log_file_write("primary", "a.txt", 10)
    audit.log_permission_decision("primary", "write_file", True, "trusted")
    actions = {e.action for e in audit.query()}
    assert actions == {"tool.execute", "file.write", "permission.decision"}


def test_missing_action_or_actor_rejected(tmp_path):
    audit = AuditLog(tmp_path)
    with pytest.raises(ValueError):
        audit.log("", actor="primary")
    with pytest.raises(ValueError):
        audit.log("tool.execute", actor="")


def test_entry_roundtrip():
    e = AuditEntry.create("x.y", "me", {"k": "v"})
    e2 = AuditEntry.from_json(e.to_json())
    assert e2.action == "x.y"
    assert e2.actor == "me"
    assert e2.details == {"k": "v"}
    assert e2.timestamp == e.timestamp
