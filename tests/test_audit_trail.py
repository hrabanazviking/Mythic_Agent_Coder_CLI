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
