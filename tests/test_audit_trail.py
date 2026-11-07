"""M-109 Audit trail - pure-layer tests.

TIER: integration

The pure layer is the audit trail as data: an
entry (its kind - a tool call, an approval, an
edit or a command - its actor - the human, the
coder, the crew or a hook - what happened, and
optionally the target touched and a detail), a
record of one entry shaped as session news, an
export that names every held entry for review,
and an append-only registry with deterministic
ids: entries are frozen, no road edits, removes
or reorders one, and reusing a held id refuses.
Nothing here writes a file or appends to a
journal.
"""

import pytest

from mythic_agent.core.audit_trail import (
    AUDIT_ACTORS,
    AUDIT_KINDS,
    AUDIT_TRAIL_SLICE,
    PLAIN_EXPLANATION,
    USAGE,
    AuditEntry,
    AuditRegistry,
    Entry,
    audit_record,
    build_entry,
    export_trail,
    format_audit_record,
    format_audit_screen,
    format_entries,
    format_entry,
    format_export,
    format_record,
    normalize_audit_actor,
    normalize_audit_id,
    normalize_audit_kind,
    parse_audit_args,
    validate_entry,
)


def _registry(*entries):
    registry = AuditRegistry()
    for entry in entries:
        registry.append(entry)
    return registry


def _entry(**kwargs):
    base = {"kind": "tool_call", "actor": "coder",
            "summary": "ran the search tool"}
    base.update(kwargs)
    return AuditEntry(**base)


# -- constants and word readings ---------------------------------------


def test_constants_and_usage():
    assert AUDIT_TRAIL_SLICE == "M-109"
    assert AUDIT_KINDS == ("tool_call", "approval", "edit", "command")
    assert AUDIT_ACTORS == ("human", "coder", "crew", "hook")
    assert USAGE.startswith("Usage: /audit")
    assert "export" in USAGE
    assert "append-only" in PLAIN_EXPLANATION
    assert "tool call" in PLAIN_EXPLANATION
    assert "human" in PLAIN_EXPLANATION


def test_kind_word_readings():
    assert normalize_audit_kind("tool_call") == "tool_call"
    assert normalize_audit_kind("Tool Call") == "tool_call"
    assert normalize_audit_kind("tool") == "tool_call"
    assert normalize_audit_kind("TOOLCALL") == "tool_call"
    assert normalize_audit_kind("approval") == "approval"
    assert normalize_audit_kind("Approve") == "approval"
    assert normalize_audit_kind("edit") == "edit"
    assert normalize_audit_kind("file-edit") == "edit"
    assert normalize_audit_kind("command") == "command"
    assert normalize_audit_kind("CMD") == "command"
    assert normalize_audit_kind("shell") == "command"
    with pytest.raises(ValueError):
        normalize_audit_kind("thought")
    with pytest.raises(ValueError):
        normalize_audit_kind("")
    with pytest.raises(ValueError):
        normalize_audit_kind(None)


def test_actor_word_readings():
    assert normalize_audit_actor("human") == "human"
    assert normalize_audit_actor("User") == "human"
    assert normalize_audit_actor("person") == "human"
    assert normalize_audit_actor("coder") == "coder"
    assert normalize_audit_actor("AGENT") == "coder"
    assert normalize_audit_actor("crew") == "crew"
    assert normalize_audit_actor("Fleet") == "crew"
    assert normalize_audit_actor("hook") == "hook"
    assert normalize_audit_actor("hooks") == "hook"
    with pytest.raises(ValueError):
        normalize_audit_actor("nobody")
    with pytest.raises(ValueError):
        normalize_audit_actor(42)


def test_entry_id_readings():
    assert normalize_audit_id("audit-1") == "audit-1"
    assert normalize_audit_id(" Audit-9.x ") == "Audit-9.x"
    with pytest.raises(ValueError):
        normalize_audit_id("two words")
    with pytest.raises(ValueError):
        normalize_audit_id("")
    with pytest.raises(ValueError):
        normalize_audit_id(None)


# -- the entry itself ----------------------------------------------------


def test_entry_happy_path_and_record():
    entry = AuditEntry(
        kind="tool_call", actor="coder",
        summary="ran the search tool", target="search",
        detail="3 hits", entry_id="audit-1")
    assert entry.kind == "tool_call" and entry.actor == "coder"
    assert entry.display_label == "audit-1 (tool call by coder)"
    record = entry.to_record()
    assert record["type"] == "audit_entry"
    assert record["slice"] == "M-109"
    assert record["entry_id"] == "audit-1"
    assert record["kind"] == "tool_call"
    assert record["actor"] == "coder"
    assert record["summary"] == "ran the search tool"
    assert record["target"] == "search"
    assert record["detail"] == "3 hits"
    assert Entry is AuditEntry


def test_entry_defaults_and_text_stripping():
    entry = AuditEntry(kind="edit", actor="human", summary="  fixed it  ")
    assert entry.summary == "fixed it"
    assert entry.detail == "" and entry.target == ""
    assert entry.entry_id is None
    assert entry.display_label == "entry (edit by human)"
    assert AuditEntry(
        kind="CMD", actor="FLEET", summary="ran it").kind == "command"
    assert AuditEntry(
        kind="CMD", actor="FLEET", summary="ran it").actor == "crew"


def test_every_kind_and_actor_is_recordable():
    for kind in AUDIT_KINDS:
        for actor in AUDIT_ACTORS:
            entry = AuditEntry(kind=kind, actor=actor, summary="did a thing")
            assert entry.kind == kind and entry.actor == actor


def test_entry_refusals():
    with pytest.raises(ValueError):
        AuditEntry(kind="thought", actor="coder", summary="x")
    with pytest.raises(ValueError):
        AuditEntry(kind="edit", actor="ghost", summary="x")
    with pytest.raises(ValueError):
        AuditEntry(kind="edit", actor="coder", summary="")
    with pytest.raises(ValueError):
        AuditEntry(kind="edit", actor="coder", summary="   ")
    with pytest.raises(ValueError):
        AuditEntry(kind="edit", actor="coder", summary=42)
    with pytest.raises(ValueError):
        AuditEntry(kind="edit", actor="coder", summary="x", detail=42)
    with pytest.raises(ValueError):
        AuditEntry(kind="edit", actor="coder", summary="x", target=None)
    with pytest.raises(ValueError):
        AuditEntry(
            kind="edit", actor="coder", summary="x",
            entry_id="two words")


def test_entry_build_spellings():
    entry = build_entry({
        "id": "audit-7", "type": "tool", "by": "user",
        "what": "ran the search tool", "details": "3 hits",
        "subject": "search"})
    assert entry.entry_id == "audit-7"
    assert entry.kind == "tool_call" and entry.actor == "human"
    assert entry.summary == "ran the search tool"
    assert entry.detail == "3 hits" and entry.target == "search"
    entry = build_entry(
        kind="command", actor="hook", summary="ran the hook command")
    assert entry.kind == "command" and entry.actor == "hook"
    assert build_entry(entry) is entry
    assert validate_entry(entry) is entry


def test_entry_build_refusals():
    with pytest.raises(ValueError):
        build_entry({"kind": "edit", "type": "command",
                     "actor": "coder", "summary": "x"})
    with pytest.raises(ValueError):
        build_entry({"kind": "edit", "actor": "coder",
                     "summary": "x", "surprise": 1})
    with pytest.raises(ValueError):
        build_entry({"actor": "coder", "summary": "x"})
    with pytest.raises(ValueError):
        build_entry({"kind": "edit", "summary": "x"})
    with pytest.raises(ValueError):
        build_entry({"kind": "edit", "actor": "coder"})
    with pytest.raises(ValueError):
        build_entry("edit")
    with pytest.raises(ValueError):
        build_entry()


# -- the registry: deterministic ids, append order -----------------------


def test_registry_deterministic_ids():
    registry = AuditRegistry()
    first = registry.append(
        {"kind": "tool_call", "actor": "coder", "summary": "one"})
    second = registry.append(_entry(summary="two"))
    assert (first.entry_id, second.entry_id) == ("audit-1", "audit-2")
    assert [e.entry_id for e in registry.list_entries()] == [
        "audit-1", "audit-2"]
    assert registry.get("audit-2").summary == "two"
    assert len(registry) == 2
    with pytest.raises(KeyError):
        registry.get("audit-99")


def test_registry_supplied_ids_and_duplicates():
    registry = AuditRegistry()
    registry.append({"entry_id": "audit-2", "kind": "edit",
                     "actor": "human", "summary": "supplied"})
    fresh = registry.append(
        {"kind": "edit", "actor": "human", "summary": "fresh"})
    assert fresh.entry_id == "audit-1"
    nxt = registry.append(
        {"kind": "edit", "actor": "human", "summary": "next"})
    assert nxt.entry_id == "audit-3"
    with pytest.raises(ValueError):
        registry.append({"entry_id": "audit-2", "kind": "edit",
                         "actor": "human", "summary": "rewrite"})


def test_registry_append_order_is_the_trail_order():
    registry = _registry(
        {"kind": "command", "actor": "hook", "summary": "first"},
        {"kind": "approval", "actor": "human", "summary": "second"},
        {"kind": "edit", "actor": "crew", "summary": "third"})
    assert [e.summary for e in registry.list_entries()] == [
        "first", "second", "third"]
    assert [e.kind for e in registry.list_entries()] == [
        "command", "approval", "edit"]


def test_registry_append_field_words_and_register_alias():
    registry = AuditRegistry()
    entry = registry.append(
        kind="approval", actor="human", summary="approved the edit")
    assert entry.entry_id == "audit-1" and entry.kind == "approval"
    held = registry.register(_entry(summary="via register"))
    assert held.entry_id == "audit-2"
    with pytest.raises(ValueError):
        registry.append(_entry(), actor="named twice over")
    with pytest.raises(KeyError):
        registry.record("audit-99")


# -- append-only, enforced -------------------------------------------------


def test_entries_are_frozen():
    import dataclasses

    entry = _entry()
    with pytest.raises(dataclasses.FrozenInstanceError):
        entry.summary = "rewritten"
    with pytest.raises(dataclasses.FrozenInstanceError):
        entry.kind = "edit"


def test_registry_has_no_mutation_or_removal_roads():
    registry = AuditRegistry()
    for road in ("remove", "delete", "clear", "pop", "update",
                 "replace", "discard", "edit_entry", "remove_entry",
                 "delete_entry", "clear_entries", "reorder"):
        assert not hasattr(registry, road), road


def test_a_held_id_can_never_be_rewritten():
    registry = _registry(
        {"kind": "edit", "actor": "coder", "summary": "the real edit"})
    with pytest.raises(ValueError):
        registry.append(AuditEntry(
            kind="edit", actor="coder", summary="a forged edit",
            entry_id="audit-1"))
    assert registry.get("audit-1").summary == "the real edit"
    assert len(registry) == 1


def test_list_entries_is_an_immutable_snapshot():
    registry = _registry(_entry(summary="one"))
    snapshot = registry.list_entries()
    assert isinstance(snapshot, tuple)
    registry.append(_entry(summary="two"))
    assert [e.summary for e in snapshot] == ["one"]
    assert len(registry.list_entries()) == 2
    with pytest.raises(AttributeError):
        snapshot.append(_entry(summary="three"))


# -- the news record ----------------------------------------------------------


def test_record_is_news_for_an_entry():
    record = audit_record(AuditEntry(
        kind="command", actor="hook", summary="ran the verify hook",
        target="pytest -q", entry_id="audit-3"))
    assert record["type"] == "audit_recorded"
    assert record["news"] is True
    assert record["slice"] == "M-109"
    assert record["entry_id"] == "audit-3"
    assert record["kind"] == "command" and record["actor"] == "hook"
    headline = record["headline"]
    assert headline.startswith("Audit recorded (audit-3)")
    assert "command by hook" in headline
    assert "ran the verify hook" in headline
    assert "Target: pytest -q." in headline
    assert format_audit_record(record) == headline
    assert format_record(record) == headline
    with pytest.raises(ValueError):
        format_audit_record({"type": "audit_entry", "headline": "x"})


def test_record_headline_names_detail_only_when_present():
    plain = audit_record(_entry())
    assert "Detail:" not in plain["headline"]
    assert "Target:" not in plain["headline"]
    detailed = audit_record(_entry(detail="exit 0"))
    assert "Detail: exit 0." in detailed["headline"]


def test_registry_record_announces_the_held_entry():
    registry = _registry(
        {"kind": "approval", "actor": "human",
         "summary": "approved the push"})
    record = registry.record("audit-1")
    assert record["type"] == "audit_recorded"
    assert record["kind"] == "approval"
    assert "approved the push" in record["headline"]


# -- the export: complete, for review ----------------------------------------


def _mixed_registry():
    return _registry(
        {"kind": "tool_call", "actor": "coder",
         "summary": "ran the search tool", "target": "search"},
        {"kind": "approval", "actor": "human",
         "summary": "approved the edit"},
        {"kind": "edit", "actor": "coder",
         "summary": "edited budgets.py", "target": "budgets.py"},
        {"kind": "command", "actor": "hook",
         "summary": "ran the verify hook"},
        {"kind": "edit", "actor": "crew",
         "summary": "edited fleet_mode.py", "target": "fleet_mode.py"})


def test_export_data_names_every_entry_in_order():
    registry = _mixed_registry()
    export = export_trail(registry)
    assert export["type"] == "audit_export"
    assert export["slice"] == "M-109"
    assert export["append_only"] is True
    assert export["count"] == 5
    assert [e["entry_id"] for e in export["entries"]] == [
        "audit-1", "audit-2", "audit-3", "audit-4", "audit-5"]
    assert [e["summary"] for e in export["entries"]] == [
        e.summary for e in registry.list_entries()]
    assert export["by_kind"] == {
        "tool_call": 1, "approval": 1, "edit": 2, "command": 1}
    assert export["by_actor"] == {
        "human": 1, "coder": 2, "crew": 1, "hook": 1}
    assert registry.export() == export


def test_export_counts_cover_the_full_vocabulary():
    export = export_trail(_registry(_entry()))
    assert export["by_kind"] == {
        "tool_call": 1, "approval": 0, "edit": 0, "command": 0}
    assert export["by_actor"] == {
        "human": 0, "coder": 1, "crew": 0, "hook": 0}


def test_export_of_an_empty_trail():
    export = export_trail()
    assert export["count"] == 0 and export["entries"] == []
    assert export["by_kind"] == {kind: 0 for kind in AUDIT_KINDS}
    assert export["by_actor"] == {actor: 0 for actor in AUDIT_ACTORS}
    assert export_trail(AuditRegistry())["count"] == 0


def test_export_accepts_a_list_or_one_entry():
    entries = [_entry(summary="one"), _entry(summary="two")]
    export = export_trail(entries)
    assert export["count"] == 2
    assert export["entries"][1]["summary"] == "two"
    single = export_trail(_entry(summary="solo"))
    assert single["count"] == 1
    with pytest.raises(ValueError):
        export_trail(42)


def test_export_text_names_every_entry():
    registry = _mixed_registry()
    text = format_export(registry)
    assert text.startswith("Audit trail export (M-109) - 5 entries")
    assert "append-only" in text.splitlines()[0]
    assert "By kind: tool call 1, approval 1, edit 2, command 1." in text
    assert "By actor: human 1, coder 2, crew 1, hook 1." in text
    for entry in registry.list_entries():
        assert entry.entry_id in text
        assert entry.summary in text
    assert "No audit entry is held." in format_export()


# -- formatters and the shared parser ------------------------------------------


def test_format_entry_states_kind_and_actor_in_words():
    line = format_entry(AuditEntry(
        kind="tool_call", actor="crew", summary="ran the tests",
        target="pytest", detail="all green", entry_id="audit-4"))
    assert line.startswith("audit-4: audit entry - tool call by crew")
    assert "ran the tests." in line
    assert "Target: pytest." in line
    assert "Detail: all green." in line
    bare = format_entry(_entry())
    assert bare == (
        "entry: audit entry - tool call by coder: "
        "ran the search tool.")


def test_format_entries_empty_list_and_registry():
    empty = "Audit trail: none recorded. No audit entry is held."
    assert format_entries() == empty
    assert format_entries([]) == empty
    assert format_entries(AuditRegistry()) == empty
    registry = _mixed_registry()
    text = format_entries(registry)
    assert text.startswith("Audit trail: 5 recorded.")
    assert len(text.splitlines()) == 6
    assert "approval by human" in text
    from_list = format_entries([_entry(summary="listed")])
    assert "listed" in from_list
    with pytest.raises(ValueError):
        format_entries(42)


def test_format_screen_is_the_whole_slice():
    screen = format_audit_screen(_mixed_registry())
    assert screen.startswith("Audit trail (M-109) - ")
    assert "Audit trail: 5 recorded." in screen
    assert USAGE in screen
    empty_screen = format_audit_screen()
    assert empty_screen.splitlines()[2] == (
        "Audit trail: none recorded. No audit entry is held.")


def test_parse_audit_args_grammar():
    assert parse_audit_args("") == ("show", None)
    assert parse_audit_args(None) == ("show", None)
    assert parse_audit_args("show") == ("show", None)
    assert parse_audit_args("show audit-3") == ("show", "audit-3")
    assert parse_audit_args("audit-3") == ("show", "audit-3")
    assert parse_audit_args("frobnicate") == ("show", "frobnicate")
    assert parse_audit_args("export") == ("export", None)
    assert parse_audit_args("EXPORT") == ("export", None)
    assert parse_audit_args("SHOW audit-1") == ("show", "audit-1")
    assert parse_audit_args("  show   audit-2  ") == ("show", "audit-2")


def test_parse_audit_args_refusals_are_the_usage():
    for bad in ("tool_call", "edit", "human", "hook", "export all",
                "export audit-1", "show a b", "show export",
                "show show", "two words"):
        with pytest.raises(ValueError) as excinfo:
            parse_audit_args(bad)
        assert str(excinfo.value) == USAGE
    with pytest.raises(ValueError):
        parse_audit_args(42)


# -- more pure-layer readings ----------------------------------------------------


def test_append_does_not_mutate_the_callers_entry():
    registry = AuditRegistry()
    original = _entry(summary="held as given")
    held = registry.append(original)
    assert original.entry_id is None
    assert held.entry_id == "audit-1" and held is not original
    assert held.summary == original.summary
    supplied = _entry(summary="with id", entry_id="audit-9")
    assert registry.append(supplied) is supplied


def test_build_entry_conflicting_detail_spellings_refuse():
    with pytest.raises(ValueError):
        build_entry({"kind": "edit", "actor": "coder", "summary": "x",
                     "detail": "one", "details": "two"})
    agreed = build_entry({"kind": "edit", "actor": "coder",
                          "summary": "x", "detail": "same",
                          "details": "same"})
    assert agreed.detail == "same"


def test_format_entries_accepts_entry_mappings():
    text = format_entries([
        {"kind": "command", "actor": "hook", "summary": "ran it"}])
    assert "command by hook" in text and "ran it" in text
    one = format_entries(_entry(summary="single"))
    assert one.startswith("Audit trail: 1 recorded.")


def test_export_order_survives_supplied_and_fresh_ids_mixed():
    registry = AuditRegistry()
    registry.append({"entry_id": "audit-5", "kind": "edit",
                     "actor": "human", "summary": "supplied first"})
    registry.append({"kind": "edit", "actor": "human",
                     "summary": "fresh second"})
    export = registry.export()
    assert [e["summary"] for e in export["entries"]] == [
        "supplied first", "fresh second"]
    assert [e["entry_id"] for e in export["entries"]] == [
        "audit-5", "audit-1"]


def test_the_trail_only_grows_by_appending():
    registry = _registry(_entry(summary="one"))
    before = registry.list_entries()
    registry.append(_entry(summary="two"))
    registry.append(_entry(summary="three"))
    after = registry.list_entries()
    assert after[:1] == before
    assert [e.summary for e in after] == ["one", "two", "three"]
    assert export_trail(registry)["count"] == 3

# -- agent layer: the trail held for a session (M-109) --------------------

import copy as _copy
import json as _json
import sys as _sys

from mythic_agent.core.sessions import SessionStore


class _OfflineMemoryAudit:
    def __init__(self):
        self.archived = []

    def search(self, query, top_k=2):
        return []

    def insert(self, text, metadata=None):
        self.archived.append(text)


@pytest.fixture()
def audit_agent(tmp_path, monkeypatch):
    from mythic_agent.agents import llm
    from mythic_agent.core.secure_api import unsubscribe

    config = {"model": "test-model", "base_url": "http://localhost:1/v1",
              "api_keys": {}}
    monkeypatch.setattr(llm.config_manager, "MYTHIC_DIR", tmp_path / "state")
    monkeypatch.setattr(llm.config_manager, "load_config",
                        lambda: _copy.deepcopy(config))
    monkeypatch.setattr(llm.config_manager, "save_config",
                        lambda config: True)
    monkeypatch.setattr(llm, "get_vector_provider",
                        lambda *args: _OfflineMemoryAudit())
    instance = llm.Agent(project_root=tmp_path)
    from mythic_agent.core.policy import ToolPolicy
    instance.tool_policy = ToolPolicy("trusted")
    yield instance
    unsubscribe("agent_clear_history", instance._handle_clear_history)
    unsubscribe("agent_compact_history", instance._handle_compact_history)


def _audit_events(store, session_id):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == "audit_recorded"]


def _call(agent, name, arguments):
    return agent._execute_call({"function": {
        "name": name, "arguments": _json.dumps(arguments)}})


def _entries(agent):
    return agent._audit_registry().list_entries()


class TestAuditAgentStatus:
    def test_status_starts_empty(self, audit_agent):
        status = audit_agent.audit_status()
        assert status["entries"] == []
        assert status["export"]["count"] == 0
        assert "Audit trail: none recorded." in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["screen"] == format_audit_screen(
            audit_agent._audit_registry())

    def test_unknown_entry_raises_keyerror(self, audit_agent):
        with pytest.raises(KeyError):
            audit_agent.get_audit_entry("audit-99")

    def test_record_audit_entry_publishes_once(self, audit_agent, tmp_path):
        store = SessionStore(tmp_path, tmp_path / "state")
        session_id = audit_agent.attach_session(store)
        result = audit_agent.record_audit_entry({
            "kind": "approval", "actor": "human",
            "summary": "approved the push"})
        assert result["entry"]["entry_id"] == "audit-1"
        assert result["record"]["type"] == "audit_recorded"
        assert result["record"]["news"] is True
        events = _audit_events(store, session_id)
        assert len(events) == 1 and events[0]["entry_id"] == "audit-1"
        status = audit_agent.audit_status()
        assert [e["entry_id"] for e in status["entries"]] == ["audit-1"]
        assert audit_agent.get_audit_entry("audit-1").summary == (
            "approved the push")

    def test_record_audit_entry_refusals_hold_nothing(self, audit_agent):
        with pytest.raises(ValueError):
            audit_agent.record_audit_entry({
                "kind": "thought", "actor": "coder", "summary": "x"})
        audit_agent.record_audit_entry({
            "kind": "edit", "actor": "coder", "summary": "one"})
        with pytest.raises(ValueError):
            audit_agent.record_audit_entry({
                "entry_id": "audit-1", "kind": "edit",
                "actor": "coder", "summary": "rewrite"})
        assert len(_entries(audit_agent)) == 1

    def test_status_and_export_reads_publish_nothing(
            self, audit_agent, tmp_path):
        store = SessionStore(tmp_path, tmp_path / "state")
        session_id = audit_agent.attach_session(store)
        audit_agent.record_audit_entry({
            "kind": "edit", "actor": "coder", "summary": "one"})
        assert len(_audit_events(store, session_id)) == 1
        audit_agent.audit_status()
        audit_agent.audit_export()
        audit_agent.get_audit_entry("audit-1")
        assert len(_audit_events(store, session_id)) == 1
        assert len(_entries(audit_agent)) == 1


class TestAuditToolRoad:
    def test_read_file_is_a_tool_call(self, audit_agent, tmp_path):
        (tmp_path / "note.txt").write_text("hello trail")
        result = _call(audit_agent, "read_file", {"path": "note.txt"})
        assert result == "hello trail"
        (entry,) = _entries(audit_agent)
        assert entry.kind == "tool_call" and entry.actor == "coder"
        assert entry.target == "read_file"
        assert entry.summary == "ran tool read_file"
        assert entry.detail == "completed"

    def test_write_file_is_an_edit_recorded_once(self, audit_agent):
        result = _call(audit_agent, "write_file",
                       {"path": "made.txt", "content": "body"})
        assert "Successfully wrote" in result
        (entry,) = _entries(audit_agent)
        assert entry.kind == "edit" and entry.actor == "coder"
        assert entry.target == "made.txt"
        assert "edited made.txt" in entry.summary

    def test_replace_is_an_edit(self, audit_agent, tmp_path):
        (tmp_path / "editme.txt").write_text("before")
        result = _call(audit_agent, "replace_file_content", {
            "path": "editme.txt", "target_content": "before",
            "replacement_content": "after"})
        assert "Successfully replaced" in result
        (entry,) = _entries(audit_agent)
        assert entry.kind == "edit" and entry.target == "editme.txt"

    def test_run_command_is_a_command(self, audit_agent):
        result = _call(audit_agent, "run_command",
                       {"command": "echo audit-hello"})
        assert "audit-hello" in result
        (entry,) = _entries(audit_agent)
        assert entry.kind == "command" and entry.actor == "coder"
        assert entry.target == "echo audit-hello"
        assert entry.summary.startswith("ran command")
        assert "audit-hello" not in entry.detail

    def test_named_subagent_acts_are_crew(self, audit_agent, tmp_path):
        (tmp_path / "note.txt").write_text("crew read")
        audit_agent.name = "Scout"
        _call(audit_agent, "read_file", {"path": "note.txt"})
        (entry,) = _entries(audit_agent)
        assert entry.actor == "crew" and entry.kind == "tool_call"

    def test_permission_denied_is_trailed_as_refused(self, audit_agent):
        from mythic_agent.core.policy import ToolPolicy
        audit_agent.tool_policy = ToolPolicy("read-only")
        result = _call(audit_agent, "write_file",
                       {"path": "never.txt", "content": "x"})
        assert "Permission denied" in result
        (entry,) = _entries(audit_agent)
        assert entry.kind == "edit"
        assert entry.detail.startswith("permission denied")

    def test_failed_calls_are_trailed_once(self, audit_agent):
        result = audit_agent._execute_call({"function": {
            "name": "read_file", "arguments": "not json"}})
        assert result.startswith("Tool read_file failed")
        result = audit_agent._execute_call({"function": {
            "name": "read_file", "arguments": "[1]"}})
        assert result == "Tool arguments must be a JSON object."
        entries = _entries(audit_agent)
        assert len(entries) == 2
        assert entries[0].detail == "failed"
        assert entries[1].detail.startswith("refused")

    def test_tool_acts_publish_as_session_news(self, audit_agent, tmp_path):
        store = SessionStore(tmp_path, tmp_path / "state")
        session_id = audit_agent.attach_session(store)
        (tmp_path / "note.txt").write_text("news")
        _call(audit_agent, "read_file", {"path": "note.txt"})
        events = _audit_events(store, session_id)
        assert len(events) == 1
        assert events[0]["kind"] == "tool_call"
        assert events[0]["actor"] == "coder"


class _ApprovingUI:
    def call_from_thread(self, method, *args):
        return method(*args)

    def action_request_approval(self, text, approve, reject):
        approve()
        return object()

    def action_cancel_approval(self, modal):
        pass


class _RefusingUI:
    def call_from_thread(self, method, *args):
        return method(*args)

    def action_request_approval(self, text, approve, reject):
        reject()
        return object()

    def action_cancel_approval(self, modal):
        pass


class TestAuditApprovalRoad:
    def test_prompt_approval_granted_is_trailed(self, audit_agent):
        audit_agent.bind_tui(_ApprovingUI(), mode="ask")
        assert audit_agent.tool_policy.authorize(
            "write_file", {"path": "x", "content": "y"}) is True
        (entry,) = _entries(audit_agent)
        assert entry.kind == "approval" and entry.actor == "human"
        assert entry.summary == "approved tool write_file"
        assert "approval prompt" in entry.detail

    def test_prompt_approval_refused_is_trailed(self, audit_agent):
        audit_agent.bind_tui(_RefusingUI(), mode="ask")
        assert audit_agent.tool_policy.authorize(
            "write_file", {"path": "x", "content": "y"}) is False
        (entry,) = _entries(audit_agent)
        assert entry.kind == "approval" and entry.actor == "human"
        assert entry.summary == "refused tool write_file"

    def test_terminal_remembered_approval_is_trailed(
            self, audit_agent, tmp_path):
        from types import SimpleNamespace

        from mythic_agent import terminal
        from mythic_agent.core.secure_api import unsubscribe

        args = SimpleNamespace(workspace=tmp_path, model=None,
                               base_url=None, permission="ask",
                               resume=None)
        wired = terminal.configured_agent(args, "ask")
        try:
            spec = {"command": "git", "args_pattern": ["status"],
                    "path": str(wired.project_root)}
            wired.remember_command_approval(spec, explicit=True)
            assert wired.tool_policy.authorize(
                "run_command", {"command": "git status"}) is True
            assert wired.tool_policy.authorize(
                "run_command", {"command": "git log"}) is False
        finally:
            wired.close()
            unsubscribe("agent_clear_history",
                        wired._handle_clear_history)
            unsubscribe("agent_compact_history",
                        wired._handle_compact_history)
        entries = wired._audit_registry().list_entries()
        assert [e.kind for e in entries] == ["approval", "approval"]
        assert entries[0].actor == "human"
        assert entries[0].summary == "approved tool run_command"
        assert "remembered approval" in entries[0].detail
        assert entries[1].summary == "refused tool run_command"


class TestAuditBackgroundRoad:
    def test_background_start_is_a_command(self, audit_agent):
        record = audit_agent.start_background_job(
            [_sys.executable, "-c", "pass"])
        (entry,) = _entries(audit_agent)
        assert entry.kind == "command" and entry.actor == "coder"
        assert record["job_id"] in entry.detail
        assert entry.target.startswith(_sys.executable)

    def test_fleet_labelled_job_is_crew(self, audit_agent):
        audit_agent.register_fleet_task({
            "label": "crew audit",
            "argv": [_sys.executable, "-c", "pass"]})
        audit_agent.start_background_job({
            "argv": [_sys.executable, "-c", "pass"],
            "label": "crew audit"})
        (entry,) = _entries(audit_agent)
        assert entry.kind == "command" and entry.actor == "crew"
        assert "crew audit" in entry.summary

    def test_unstartable_command_is_trailed(self, audit_agent):
        record = audit_agent.start_background_job(
            ["/nonexistent/audit-binary-xyz"])
        assert record["state"] == "failed"
        (entry,) = _entries(audit_agent)
        assert entry.kind == "command" and entry.actor == "coder"
        assert "failed" in entry.detail


class TestAuditHookRoad:
    def test_hook_run_is_trailed_with_hook_actor(self, audit_agent):
        audit_agent.config["hooks"] = [
            {"event": "on_session", "command": "exit 0"}]
        verdicts = audit_agent.run_hooks("on_session")
        assert len(verdicts) == 1 and verdicts[0].decision == "allow"
        (entry,) = _entries(audit_agent)
        assert entry.kind == "command" and entry.actor == "hook"
        assert entry.target == "exit 0"
        assert "on_session" in entry.summary
        assert "decision allow" in entry.detail
        quiet = audit_agent.run_hooks("on_test")
        assert quiet == [] and len(_entries(audit_agent)) == 1


class TestAuditExportRoad:
    def test_export_names_every_entry(self, audit_agent, tmp_path):
        audit_agent.record_audit_entry({
            "kind": "approval", "actor": "human",
            "summary": "approved the edit"})
        (tmp_path / "note.txt").write_text("x")
        _call(audit_agent, "read_file", {"path": "note.txt"})
        out = audit_agent.audit_export()
        assert out["export"]["count"] == 2
        assert out["export"]["by_kind"]["approval"] == 1
        assert out["export"]["by_kind"]["tool_call"] == 1
        assert out["export"]["by_actor"]["human"] == 1
        assert "approved the edit" in out["text"]
        assert "ran tool read_file" in out["text"]
        assert out["text"].startswith(
            "Audit trail export (M-109) - 2 entries")


class TestAuditTerminalSurface:
    def test_show_is_the_whole_slice(self, audit_agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(audit_agent, "/audit")
        assert text.startswith("Audit trail (M-109) - ")
        assert "Audit trail: none recorded." in text
        assert USAGE in text

    def test_show_one_and_export_via_the_terminal(self, audit_agent):
        from mythic_agent.terminal import _slash
        audit_agent.record_audit_entry({
            "kind": "edit", "actor": "coder",
            "summary": "edited budgets.py", "target": "budgets.py"})
        _, _, text = _slash(audit_agent, "/audit show audit-1")
        assert text.startswith("audit-1: audit entry - edit by coder")
        _, _, text = _slash(audit_agent, "/audit audit-1")
        assert "edited budgets.py" in text
        _, _, text = _slash(audit_agent, "/audit export")
        assert text.startswith("Audit trail export (M-109) - 1 entries")
        assert "By actor: human 0, coder 1, crew 0, hook 0." in text

    def test_unknown_entry_is_named(self, audit_agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(audit_agent, "/audit show audit-99")
        assert "unknown audit entry" in text

    def test_bad_grammar_is_the_usage(self, audit_agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(audit_agent, "/audit tool_call")
        assert text == USAGE
        _, _, text = _slash(audit_agent, "/audit export all")
        assert text == USAGE


@pytest.fixture()
def audit_handler(audit_agent, monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.agents.llm import AGENT_REGISTRY

    published = []
    monkeypatch.setattr(
        handler_module, "publish_sync",
        lambda event, **kwargs: published.append((event, kwargs)))
    AGENT_REGISTRY["Primary"] = audit_agent
    instance = CommandHandler.__new__(CommandHandler)
    instance.published = published
    yield instance
    AGENT_REGISTRY.pop("Primary", None)


def _audit_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestAuditCommand:
    def test_show_is_default(self, audit_handler, audit_agent):
        audit_handler._handle_audit("")
        assert "Audit trail: none recorded." in _audit_published_text(
            audit_handler)

    def test_show_one_via_the_handler(self, audit_handler, audit_agent):
        audit_agent.record_audit_entry({
            "kind": "command", "actor": "hook",
            "summary": "ran the verify hook"})
        audit_handler._handle_audit("show audit-1")
        assert "audit-1: " in _audit_published_text(audit_handler)
        assert "command by hook" in _audit_published_text(audit_handler)

    def test_export_via_the_handler(self, audit_handler, audit_agent):
        audit_agent.record_audit_entry({
            "kind": "command", "actor": "hook",
            "summary": "ran the verify hook"})
        audit_handler._handle_audit("export")
        assert "Audit trail export (M-109)" in _audit_published_text(
            audit_handler)

    def test_bad_grammar_and_unknown_are_published(
            self, audit_handler, audit_agent):
        audit_handler._handle_audit("export all")
        assert "Usage: /audit" in _audit_published_text(audit_handler)
        audit_handler._handle_audit("show audit-99")
        assert "unknown audit entry" in _audit_published_text(audit_handler)


class TestChatScreenRoutingAudit:
    def test_audit_routes_as_system_command(self, monkeypatch):
        from mythic_agent.ui.screens import chat_screen
        from mythic_agent.ui.screens.chat_screen import MainChatScreen

        class _FakeLog:
            def __init__(self):
                self.lines = []

            def write(self, *args, **kwargs):
                self.lines.append(" ".join(str(a) for a in args))

        calls = []
        monkeypatch.setattr(
            chat_screen.SecureAPI, "publish_system_command",
            staticmethod(lambda cmd, args: calls.append((cmd, args))))
        screen = MainChatScreen.__new__(MainChatScreen)
        screen.handle_command("/audit export", _FakeLog())
        assert calls == [("/audit", "export")]
