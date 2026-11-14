"""M-153 Session memory across days - pure-layer tests.

TIER: integration

The pure layer is the situation as data: one resumable
session's carried memory map (the shipped project
memory map's entries, composed by import), its open
slices (the shipped roadmap's queued slices, composed
by import) and its standing decisions (the map's
decision entries standing as decisions), with the
transcript counted and never carried - a panel derived
from the situation in settled order, the shipped
example book held in a data file, a loader that reads
a book from any file, a restore road that builds a
situation from a shipped session export judged by the
store's own validation, and a registry. A stored panel
or situation disagreeing with its derived shape is
refused. Nothing here calls a model, attaches or
resumes a live session or replays a transcript:
holding a situation changes nothing but data.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.project_memory_map import (
    build_entry as build_map_entry,
    load_project_memory_map,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.session_memory import (
    OPEN_SLICE_STATES,
    PANEL_KINDS,
    PLAIN_EXPLANATION,
    SESSION_MEMORY_RESOURCE,
    SESSION_MEMORY_SCHEMA,
    SESSION_MEMORY_SLICE,
    SESSION_STATUSES,
    USAGE,
    CarriedMemory,
    OpenSlice,
    SessionMemoryBook,
    SessionMemoryRegistry,
    SessionSituation,
    SituationKindCount,
    SituationPanel,
    SituationPanelRow,
    StandingDecision,
    book_record,
    build_book,
    build_decision,
    build_note,
    build_panel,
    build_row,
    build_situation,
    build_slice,
    decisions_from_memory_map,
    derive_panel,
    format_decisions,
    format_memory,
    format_panel,
    format_session_memory_screen,
    format_situation,
    format_slices,
    load_session_memory,
    load_session_memory_file,
    normalize_slice_state,
    note_record,
    notes_from_memory_map,
    open_slices_from_roadmap,
    panel_plain_words,
    panel_record,
    parse_session_memory_args,
    plain_words,
    situation_from_export,
    situation_record,
    validate_book,
    validate_decision,
    validate_note,
    validate_panel,
    validate_row,
    validate_situation,
    validate_slice,
)

ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_TITLE = (
    "Session memory across days at the M-152 slice boundary")


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "section": "architecture",
        "title": "A carried fact",
        "detail": "The fact itself, in plain words.",
        "source": "test source",
        "ref": "mythic_agent/core/session_memory.py",
    }
    fields.update(overrides)
    return build_note(fields)


def _slice(**overrides):
    fields = {
        "slice_id": "M-153",
        "title": "Session memory across days",
        "state": "open",
        "note": "The slice itself, standing open.",
    }
    fields.update(overrides)
    return build_slice(fields)


def _decision(**overrides):
    fields = {
        "decision_id": "decision-test",
        "title": "A standing decision",
        "decision": "The settled words the next day stands under.",
        "source": "test source",
    }
    fields.update(overrides)
    return build_decision(fields)


def _situation(**overrides):
    fields = {
        "session_ref": "session-test-day",
        "workspace": "/tmp/test-workspace",
        "title": "A test situation",
        "saved_on": "2026-11-08",
        "status": "idle",
        "transcript_messages": 3,
        "memory": [_note()],
        "open_slices": [_slice()],
        "decisions": [_decision()],
        "situation_id": "situation-test",
    }
    fields.update(overrides)
    return build_situation(fields)


def _stored_situation(situation):
    record = situation.to_record()
    record.pop("type")
    record.pop("slice")
    for key in ("memory", "open_slices", "decisions"):
        for item in record[key]:
            item.pop("type")
            item.pop("slice")
    return record


def _stored_panel(panel):
    record = panel.to_record()
    record.pop("type")
    record.pop("slice")
    for row in record["rows"]:
        row.pop("type")
        row.pop("slice")
    return record


def _shipped_raw():
    path = ROOT / "mythic_agent" / "data" / "session_memory.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_constants_and_usage():
    assert SESSION_MEMORY_SLICE == "M-153"
    assert SESSION_MEMORY_SCHEMA == "mythic.session_memory/1"
    assert SESSION_MEMORY_RESOURCE.endswith("session_memory.yaml")
    assert OPEN_SLICE_STATES == ("open", "in-progress", "blocked")
    assert PANEL_KINDS == ("memory", "slice", "decision")
    assert SESSION_STATUSES == (
        "idle", "running", "completed", "failed",
        "cancelled", "interrupted")
    assert "Session memory across days" in PLAIN_EXPLANATION
    assert "/daymemory situation <situation-id>" in USAGE


def test_shipped_example_shape():
    book = load_session_memory()
    assert book.title == EXAMPLE_TITLE
    assert book.situation_ids() == ("situation-m152-boundary",)
    situation = book.situations[0]
    assert situation.session_ref == "session-m152-graph-retrieval"
    assert situation.workspace == (
        "purplelongship:/home/volmarr/mythic-hammer")
    assert situation.saved_on == "2026-11-08"
    assert situation.status == "idle"
    # The transcript is counted, never carried.
    assert situation.transcript_messages == 42
    assert situation.total_memory == 3
    assert situation.total_slices == 2
    assert situation.total_decisions == 2
    assert [n.note_id for n in situation.memory] == [
        "note-connected-code", "note-reap-at-bank",
        "note-campaign-home"]
    assert [s.slice_id for s in situation.open_slices] == [
        "M-153", "M-154"]
    assert situation.open_slices[0].state == "in-progress"
    assert situation.open_slices[1].state == "open"
    assert [d.decision_id for d in situation.decisions] == [
        "decision-banking-order", "decision-no-docker"]
    assert len(book.panels) == 1
    assert book.panels[0].panel_id == "panel-m152-boundary"
    assert book.panel_for("panel-m152-boundary") is book.panels[0]
    assert book.situation_for(
        "situation-m152-boundary") is situation
    with pytest.raises(KeyError):
        book.situation_for("situation-nope")


def test_shipped_panel_is_pinned_and_derived():
    book = load_session_memory()
    stored = book.panels[0]
    derived = derive_panel(book.situations[0])
    assert [r.item_id for r in stored.rows] == [
        "note-connected-code", "note-reap-at-bank",
        "note-campaign-home", "M-153", "M-154",
        "decision-banking-order", "decision-no-docker"]
    assert stored.rows == derived.rows
    assert stored.total_items == derived.total_items == 7
    assert stored.total_memory == derived.total_memory == 3
    assert stored.total_slices == derived.total_slices == 2
    assert stored.total_decisions == derived.total_decisions == 2
    assert stored.kind_counts == derived.kind_counts
    assert stored.account == derived.account
    assert stored.account[0] == (
        "The panel holds 7 carried pieces: memory 3, "
        "open slices 2, standing decisions 2.")
    # A stored panel judged against its situation stands.
    assert validate_panel(stored, book.situations[0]) is stored
    assert stored.row_for("M-154").kind == "slice"
    with pytest.raises(KeyError):
        stored.row_for("M-999")


def test_note_validation_and_aliases():
    note = build_note({
        "id": "note-alias", "kind": "Gotchas",
        "name": "An aliased fact",
        "body": "The aliased fact itself, in plain words.",
        "source": "test source", "path": "some/ref.py"})
    assert note.note_id == "note-alias"
    assert note.section == "gotcha"
    assert note.title == "An aliased fact"
    assert note.detail == "The aliased fact itself, in plain words."
    assert note.ref == "some/ref.py"
    assert validate_note(note) is note
    built = build_note(
        section="location", title="Built from words",
        detail="A fact built from field words.",
        source="test source", ref="some/place")
    assert isinstance(built, CarriedMemory)
    assert built.note_id is None


def test_note_composes_the_shipped_map_entry():
    entry = build_map_entry({
        "entry_id": "map-test-entry", "section": "decision",
        "title": "A map decision",
        "detail": "The map entry's own words, carried whole.",
        "source": "test source", "ref": "some/ref.py"})
    note = validate_note(entry)
    assert note.note_id == "map-test-entry"
    assert note.section == "decision"
    assert note.title == entry.title
    assert note.detail == entry.detail
    assert note.ref == entry.ref


def test_note_refusals():
    with pytest.raises(ValueError):
        build_note({"section": "architecture", "title": "x",
                    "detail": "y", "source": "z", "ref": "r",
                    "bogus": 1})
    with pytest.raises(ValueError):
        build_note({"title": "x", "detail": "y",
                    "source": "z", "ref": "r"})
    with pytest.raises(ValueError):
        build_note({"section": "secrets", "title": "x",
                    "detail": "y", "source": "z", "ref": "r"})
    with pytest.raises(ValueError):
        build_note({"section": "architecture", "title": "one",
                    "name": "two", "detail": "y",
                    "source": "z", "ref": "r"})
    with pytest.raises(ValueError):
        _note(ref="a ref with spaces")
    with pytest.raises(ValueError):
        validate_note("not a mapping")


def test_slice_validation_states_and_aliases():
    assert normalize_slice_state("queued") == "open"
    assert normalize_slice_state("Queued") == "open"
    assert normalize_slice_state("in_progress") == "in-progress"
    assert normalize_slice_state("IN PROGRESS") == "in-progress"
    assert normalize_slice_state("blocked") == "blocked"
    aliased = build_slice({
        "id": "M-200", "name": "An aliased slice",
        "status": "queued", "detail": "Standing open."})
    assert aliased.slice_id == "M-200"
    assert aliased.state == "open"
    assert aliased.note == "Standing open."
    assert validate_slice(aliased) is aliased


def test_slice_composes_the_shipped_roadmap():
    queued = [s for s in load_roadmap().slices
              if s.status == "queued"]
    first = validate_slice(queued[0])
    assert isinstance(first, OpenSlice)
    assert first.slice_id == queued[0].id
    assert first.title == queued[0].title
    assert first.state == "open"
    assert first.note == queued[0].summary


def test_slice_refusals():
    with pytest.raises(ValueError):
        normalize_slice_state("doing")
    with pytest.raises(ValueError):
        _slice(slice_id="M-99")
    with pytest.raises(ValueError):
        _slice(slice_id="X-153")
    with pytest.raises(ValueError):
        build_slice({"slice_id": "M-153", "title": "x",
                     "state": "open", "note": "y", "bogus": 1})


def test_decision_validation_and_aliases():
    decision = build_decision({
        "id": "decision-alias", "name": "An aliased decision",
        "body": "The settled words, aliased.", "source": "src"})
    assert decision.decision_id == "decision-alias"
    assert decision.title == "An aliased decision"
    assert decision.decision == "The settled words, aliased."
    assert validate_decision(decision) is decision
    with pytest.raises(ValueError):
        build_decision({"title": "x", "decision": "y",
                        "source": "z", "bogus": 1})
    with pytest.raises(ValueError):
        build_decision({"title": "x", "source": "z"})


def test_decision_composes_only_map_decision_entries():
    entry = build_map_entry({
        "entry_id": "map-decision-entry", "section": "decision",
        "title": "A settled map word",
        "detail": "The decision the map itself settled.",
        "source": "test source", "ref": "some/ref.py"})
    decision = validate_decision(entry)
    assert isinstance(decision, StandingDecision)
    assert decision.decision_id == "map-decision-entry"
    assert decision.decision == entry.detail
    other = build_map_entry({
        "entry_id": "map-arch-entry", "section": "architecture",
        "title": "A plain map fact",
        "detail": "A fact, never silently promoted to law.",
        "source": "test source", "ref": "some/ref.py"})
    with pytest.raises(ValueError):
        validate_decision(other)


def test_situation_totals_are_derived_and_judged():
    situation = _situation()
    assert situation.total_memory == 1
    assert situation.total_slices == 1
    assert situation.total_decisions == 1
    assert validate_situation(situation) is situation
    assert build_situation(_stored_situation(situation)) == situation
    with pytest.raises(ValueError):
        _situation(total_memory=99)
    with pytest.raises(ValueError):
        _situation(transcript_messages=-1)
    with pytest.raises(ValueError):
        _situation(transcript_messages=True)


def test_situation_refusals():
    with pytest.raises(ValueError):
        _situation(saved_on="08/11/2026")
    with pytest.raises(ValueError):
        _situation(saved_on="2026-13-01")
    with pytest.raises(ValueError):
        _situation(status="sleeping")
    with pytest.raises(ValueError):
        _situation(session_ref="a ref with spaces")
    with pytest.raises(ValueError):
        _situation(memory=[_note(), _note()])
    with pytest.raises(ValueError):
        _situation(memory=[
            _note(note_id="note-a"),
            _note(note_id="note-b")])
    with pytest.raises(ValueError):
        _situation(open_slices=[_slice(), _slice()])
    with pytest.raises(ValueError):
        _situation(decisions=[
            _decision(decision_id="decision-a"),
            _decision(decision_id="decision-b")])
    with pytest.raises(ValueError):
        build_situation({"session_ref": "s", "workspace": "w",
                         "title": "t", "saved_on": "2026-11-08",
                         "status": "idle", "transcript_messages": 1,
                         "memory": [], "open_slices": [],
                         "decisions": [], "bogus": 1})


def test_situation_lookups():
    situation = _situation()
    assert situation.note_for("note-test") is situation.memory[0]
    assert situation.slice_for("M-153") is situation.open_slices[0]
    assert situation.decision_for(
        "decision-test") is situation.decisions[0]
    with pytest.raises(KeyError):
        situation.note_for("note-nope")
    with pytest.raises(KeyError):
        situation.slice_for("M-999")
    with pytest.raises(KeyError):
        situation.decision_for("decision-nope")


def test_panel_is_derived_in_settled_order():
    situation = _situation(
        memory=[
            _note(note_id="note-loc", section="location",
                  title="Zeta fact"),
            _note(note_id="note-arch", section="architecture",
                  title="Alpha fact")],
        open_slices=[
            _slice(slice_id="M-160", title="Later work"),
            _slice(slice_id="M-153")],
        decisions=[
            _decision(decision_id="decision-b",
                      title="B decision"),
            _decision(decision_id="decision-a",
                      title="A decision")])
    panel = derive_panel(situation)
    # Memory in map order (architecture before location),
    # slices in roadmap order, decisions by title -
    # never in held order.
    assert [r.item_id for r in panel.rows] == [
        "note-arch", "note-loc", "M-153", "M-160",
        "decision-a", "decision-b"]
    assert [r.kind for r in panel.rows] == [
        "memory", "memory", "slice", "slice",
        "decision", "decision"]
    assert panel.total_items == 6
    assert panel.kind_counts == (
        SituationKindCount(kind="memory", items=2),
        SituationKindCount(kind="slice", items=2),
        SituationKindCount(kind="decision", items=2))
    assert panel.account[0] == (
        "The panel holds 6 carried pieces: memory 2, "
        "open slices 2, standing decisions 2.")
    assert panel.panel_id is None


def test_panel_judgement_against_its_situation():
    situation = _situation()
    panel = derive_panel(situation)
    assert validate_panel(_stored_panel(panel), situation) == panel
    assert build_panel(_stored_panel(panel)) == panel
    tampered = _stored_panel(panel)
    tampered["rows"][0]["detail"] = "Rewritten words."
    with pytest.raises(ValueError):
        validate_panel(tampered, situation)
    tampered = _stored_panel(panel)
    tampered["kind_counts"][0]["items"] = 99
    with pytest.raises(ValueError):
        validate_panel(tampered, situation)
    tampered = _stored_panel(panel)
    tampered["account"] = ["A rewritten account."]
    with pytest.raises(ValueError):
        validate_panel(tampered, situation)
    tampered = _stored_panel(panel)
    tampered["bogus"] = 1
    with pytest.raises(ValueError):
        validate_panel(tampered)


def test_panel_construction_refusals():
    situation = _situation()
    panel = derive_panel(situation)
    with pytest.raises(ValueError):
        SituationPanel(
            rows=tuple(reversed(panel.rows)),
            total_items=panel.total_items,
            total_memory=panel.total_memory,
            total_slices=panel.total_slices,
            total_decisions=panel.total_decisions,
            kind_counts=panel.kind_counts,
            account=panel.account)
    with pytest.raises(ValueError):
        SituationPanel(
            rows=panel.rows, total_items=panel.total_items,
            total_memory=99, total_slices=panel.total_slices,
            total_decisions=panel.total_decisions,
            kind_counts=panel.kind_counts, account=panel.account)
    with pytest.raises(ValueError):
        SituationPanel(
            rows=panel.rows, total_items=panel.total_items,
            total_memory=panel.total_memory,
            total_slices=panel.total_slices,
            total_decisions=panel.total_decisions,
            kind_counts=(SituationKindCount(
                kind="memory", items=99),),
            account=panel.account)


def test_panel_row_judged_against_its_piece():
    note = _note()
    row = build_row(note)
    assert row == SituationPanelRow(
        kind="memory", item_id="note-test",
        title=note.title, detail=note.detail)
    assert validate_row(row, note) is row
    with pytest.raises(ValueError):
        validate_row(
            {"kind": "memory", "item_id": "note-test",
             "title": "Rewritten", "detail": note.detail}, note)
    with pytest.raises(ValueError):
        derive_panel(_situation(memory=[_note(note_id=None)]))
    with pytest.raises(ValueError):
        derive_panel(_situation(
            memory=[], open_slices=[], decisions=[]))


def test_notes_and_decisions_from_the_shipped_map():
    book = load_project_memory_map()
    notes = notes_from_memory_map(book)
    assert len(notes) == len(book.entries) == 9
    assert [n.note_id for n in notes] == [
        e.entry_id for e in book.entries]
    assert [n.section for n in notes] == [
        e.section for e in book.entries]
    assert len(notes_from_memory_map(book.entries)) == 9
    decisions = decisions_from_memory_map(book)
    assert [d.decision_id for d in decisions] == [
        "map-ci-manual", "map-scribe-law"]
    assert all(
        d.decision == e.detail for d, e in zip(
            decisions,
            [e for e in book.entries
             if e.section == "decision"]))


def test_open_slices_from_the_shipped_roadmap():
    road = load_roadmap()
    queued_ids = [s.id for s in road.slices
                  if s.status == "queued"]
    slices = open_slices_from_roadmap()
    assert slices[0].slice_id == queued_ids[0]
    assert all(s.state == "open" for s in slices)
    assert len(slices) == 1
    limited = open_slices_from_roadmap(limit=2)
    assert [s.slice_id for s in limited] == queued_ids[:2]
    assert [s.slice_id for s in open_slices_from_roadmap(
        road, limit=1)] == queued_ids[:1]
    with pytest.raises(ValueError):
        open_slices_from_roadmap(limit=0)


def test_situation_from_export_counts_never_carries():
    export = {
        "id": "0123456789abcdef0123456789abcdef",
        "workspace": "/tmp/test-workspace",
        "status": "idle",
        "updated_at": "2026-11-08T10:30:00+00:00",
        "context": [
            {"role": "system", "content": "You are the coder."},
            {"role": "user", "content": "Build the slice."},
            {"role": "assistant", "content": "Built."}],
    }
    situation = situation_from_export(
        export, memory=[_note()], open_slices=[_slice()],
        decisions=[_decision()], situation_id="situation-export")
    assert situation.session_ref == export["id"]
    assert situation.transcript_messages == 3
    assert situation.saved_on == "2026-11-08"
    assert situation.title == "Session 01234567 situation"
    assert situation.situation_id == "situation-export"
    # The transcript itself stands nowhere in the record.
    assert "context" not in situation.to_record()
    assert not hasattr(situation, "context")
    named = situation_from_export(
        export, title="A named restore", saved_on="2026-11-07")
    assert named.title == "A named restore"
    assert named.saved_on == "2026-11-07"


def test_situation_from_export_refusals():
    base = {
        "id": "0123456789abcdef0123456789abcdef",
        "workspace": "/tmp/test-workspace",
        "status": "idle",
        "updated_at": "2026-11-08T10:30:00+00:00",
        "context": [{"role": "system", "content": "sys"}],
    }
    with pytest.raises(ValueError):
        situation_from_export({**base, "id": "not-a-session-id"})
    with pytest.raises(ValueError):
        situation_from_export({**base, "context": []})
    with pytest.raises(ValueError):
        situation_from_export(
            {k: v for k, v in base.items() if k != "context"})
    with pytest.raises(ValueError):
        situation_from_export(
            {k: v for k, v in base.items() if k != "workspace"})
    with pytest.raises(ValueError):
        situation_from_export("not an export")


def test_book_validation_refusals():
    raw = _shipped_raw()
    with pytest.raises(ValidationError):
        validate_book({**raw, "schema": "mythic.other/1"})
    with pytest.raises(ValidationError):
        validate_book({**raw, "bogus": 1})
    duplicated = _shipped_raw()
    duplicated["situations"] = (
        duplicated["situations"] + duplicated["situations"])
    with pytest.raises(ValidationError):
        validate_book(duplicated)
    tampered = _shipped_raw()
    tampered["panels"][0]["rows"][0]["detail"] = "Rewritten."
    with pytest.raises(ValidationError):
        validate_book(tampered)
    retitled = _shipped_raw()
    retitled["guide"] = {"title": "A different title"}
    with pytest.raises(ValidationError):
        load_session_memory(retitled)
    # The same file without the example check stands on
    # its own records.
    assert validate_book(retitled).title == "A different title"
    with pytest.raises(ValueError):
        SessionMemoryBook(title="Empty", situations=[])
    built = build_book({
        "title": "A built book", "situations": [_situation()]})
    assert built.situation_ids() == ("situation-test",)
    assert build_book(built) is built


def test_load_session_memory_file_roundtrip(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "session_memory.yaml").read_text(encoding="utf-8")
    path = tmp_path / "session_memory.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_session_memory_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.situation_ids() == ("situation-m152-boundary",)
    bad = tmp_path / "bad.yaml"
    bad.write_text("schema: mythic.session_memory/1\n"
                   "guide: {title: x}\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_session_memory_file(bad)
    with pytest.raises(FileNotFoundError):
        load_session_memory_file(tmp_path / "missing.yaml")


def test_registry_holds_situations_one_by_one():
    registry = SessionMemoryRegistry()
    assert registry.list_situations() == ()
    with pytest.raises(ValueError):
        registry.book()
    with pytest.raises(ValueError):
        registry.latest_situation()
    held = registry.register_situation(
        _situation(situation_id=None))
    assert held.situation_id == "situation-1"
    assert registry.latest_situation() is held
    assert registry.get_situation("situation-1") is held
    with pytest.raises(KeyError):
        registry.get_situation("situation-nope")
    with pytest.raises(ValueError):
        registry.register_situation(held)
    panel = registry.panel()
    assert panel.total_items == 3


def test_registry_register_book_titles():
    registry = SessionMemoryRegistry()
    book = registry.register_book(load_session_memory())
    assert book.title == EXAMPLE_TITLE
    assert [s.situation_id for s in registry.list_situations()] == [
        "situation-m152-boundary"]
    with pytest.raises(ValueError):
        registry.register_book(load_session_memory())
    other = SessionMemoryBook(
        title="Another book", situations=[_situation()])
    with pytest.raises(ValueError):
        registry.register_book(other)
    fresh = SessionMemoryRegistry(load_session_memory())
    assert fresh.latest_situation().situation_id == (
        "situation-m152-boundary")


def test_records_and_plain_words():
    book = load_session_memory()
    situation = book.situations[0]
    note = note_record(situation.memory[0])
    assert note["type"] == "session_memory_note"
    assert note["news"] is True
    assert "Retrieval returns connected code" in note["headline"]
    record = situation_record(situation)
    assert record["type"] == "session_memory_situation"
    assert record["news"] is True
    assert "not the 42-message transcript" in record["headline"]
    panel = panel_record(book.panels[0], situation)
    assert panel["type"] == "session_memory_panel"
    assert "7 carried pieces" in panel["headline"]
    whole = book_record(book)
    assert whole["type"] == "session_memory_book"
    assert whole["situation_count"] == 1
    words = plain_words(situation)
    assert "session session-m152-graph-retrieval" in words
    assert "counted and not carried" in words
    told = panel_plain_words(book)
    assert EXAMPLE_TITLE in told
    assert "note-connected-code: memory" in told
    assert "The panel holds 7 carried pieces" in told


def test_formatters_and_screen():
    book = load_session_memory()
    situation = book.situations[0]
    text = format_situation(situation)
    assert "situation-m152-boundary: Graph retrieval landed" in text
    assert "counted, not carried" in text
    assert "memory note-connected-code:" in text
    assert "slice M-153:" in text
    assert "decision decision-no-docker:" in text
    assert "note-reap-at-bank" in format_memory(book)
    assert "M-154: Cross-project memory" in format_slices(book)
    assert "decision-no-docker: No Docker, ever" in (
        format_decisions(book))
    panel_text = format_panel(book)
    assert "Panel in " + EXAMPLE_TITLE in panel_text
    assert "M-153: slice - Session memory across days" in panel_text
    screen = format_session_memory_screen()
    assert "Session Memory Across Days (M-153)" in screen
    assert USAGE in screen
    assert format_memory(_situation(
        memory=[], open_slices=[], decisions=[])) == (
            "No memory is carried.")
    assert format_slices(_situation(
        memory=[], open_slices=[], decisions=[])) == (
            "No open slices are carried.")
    assert format_decisions(_situation(
        memory=[], open_slices=[], decisions=[])) == (
            "No standing decisions are carried.")


def test_parse_session_memory_args_grammar():
    assert parse_session_memory_args("") == ("show", None)
    assert parse_session_memory_args(None) == ("show", None)
    assert parse_session_memory_args("show") == ("show", None)
    assert parse_session_memory_args("list") == ("show", None)
    assert parse_session_memory_args(
        "situation situation-m152-boundary") == (
            "situation", "situation-m152-boundary")
    assert parse_session_memory_args("memory") == ("memory", None)
    assert parse_session_memory_args("MEMORY") == ("memory", None)
    assert parse_session_memory_args("slices") == ("slices", None)
    assert parse_session_memory_args(
        "decisions") == ("decisions", None)
    assert parse_session_memory_args("panel") == ("panel", None)
    for bad in ("situation", "situation a b", "dance party",
                "memory extra"):
        with pytest.raises(ValueError):
            parse_session_memory_args(bad)
    with pytest.raises(ValueError):
        parse_session_memory_args(123)


def test_honest_boundary_module_imports_no_live_roads():
    source = (ROOT / "mythic_agent" / "core"
              / "session_memory.py").read_text(encoding="utf-8")
    # The pure layer composes the shipped map, roadmap
    # and session store by import, and imports no agent,
    # ui or terminal code: holding a situation can call
    # no model, attach no session and replay nothing.
    assert "from .project_memory_map import" in source
    assert "from .roadmap_slices import" in source
    assert "from .sessions import" in source
    assert "from ..agents" not in source
    assert "from ..ui" not in source
    assert "from ..terminal" not in source
    assert "import agents" not in source


# -- agent layer -----------------------------------------------------------
#
# M-153 agent layer: the agent holds a
# SessionMemoryRegistry for the session (session state
# only, no new setting), situations are held by being
# registered - published as their situation_record
# session news with the derived panel_record, through
# the checkpoint road, deduped per shape - the report
# road renders the held book (or the shipped example
# when unheld) through the pure formatters, a restore
# road builds one stored session's situation from the
# shipped store's export composed with the session's
# memory-map book and the roadmap's next queued slices,
# and the /daymemory surface rides both roads on the
# pure parser + formatters. Status, get and panel reads
# register and publish nothing, answer from the held
# registry first and from the shipped example only while
# nothing is held - a held session never falls back to
# the example. The panel derives at call time from the
# latest held situation, never held. This layer calls
# no model, attaches or resumes no live session and
# replays no transcript, and there is no Part VIII
# board yet, so the screen is where the situation is
# visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _memory_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_memory_book(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "session_memory.yaml").read_text(encoding="utf-8")
    path = tmp_path / "session_memory.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestSessionMemoryAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.session_memory_status()
        assert status["situations"] == []
        assert status["book"] is None
        assert status["session_memory"]["title"] == EXAMPLE_TITLE
        assert len(status["session_memory"]["situations"]) == 1
        assert status["panel"]["total_items"] == 7
        assert status["panel"]["total_memory"] == 3
        assert status["panels"][0]["panel_id"] == (
            "panel-m152-boundary")
        assert status["book_record"]["situation_count"] == 1
        assert "Session Memory Across Days (M-153)" in (
            status["screen"])
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._session_memory_registry()
        assert agent._session_memory_registry() is first
        assert agent._session_memory_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.session_memory_status()
        agent.get_session_situation("situation-m152-boundary")
        agent.get_session_memory_note("note-connected-code")
        agent.session_memory_panel()
        agent.report_session_memory()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("session_memory")] == []
        agent.close()

    def test_unheld_reads_raise(self, agent):
        with pytest.raises(KeyError):
            agent.get_session_situation("situation-nope")
        with pytest.raises(KeyError):
            agent.get_session_memory_note("note-nope")

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_session_situation(_situation())
        status = agent.session_memory_status()
        assert [s["situation_id"] for s in status["situations"]] == [
            "situation-test"]
        assert status["book"]["title"] == (
            "Session memory across days")
        assert status["panel"]["total_items"] == 3

    def test_held_session_never_falls_back_to_the_example(
            self, agent):
        agent.register_session_situation(_situation())
        with pytest.raises(KeyError):
            agent.get_session_situation("situation-m152-boundary")
        with pytest.raises(KeyError):
            agent.get_session_memory_note("note-connected-code")
        note = agent.get_session_memory_note("note-test")
        assert note.title == "A carried fact"
        assert agent.session_memory_book().title == (
            "Session memory across days")


class TestSessionMemoryAgentHolding:
    def test_register_situation_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_session_situation(_situation())
        assert outcome["situation"]["situation_id"] == (
            "situation-test")
        assert outcome["situation_news"]["type"] == (
            "session_memory_situation")
        assert outcome["panel_record"]["type"] == (
            "session_memory_panel")
        events = _memory_events(
            store, session_id, "session_memory_situation")
        assert len(events) == 1
        assert events[0]["situation_id"] == "situation-test"
        panels = _memory_events(
            store, session_id, "session_memory_panel")
        assert len(panels) == 1
        assert panels[0]["total_items"] == 3
        agent._publish_session_memory_record(
            outcome["situation_news"])
        agent._publish_session_memory_record(
            outcome["panel_record"])
        assert len(_memory_events(
            store, session_id, "session_memory_situation")) == 1
        assert len(_memory_events(
            store, session_id, "session_memory_panel")) == 1
        agent._publish_session_memory_record(
            {"type": "mentions_mention", "mention_id": "mention-x"})
        agent._publish_session_memory_record(
            book_record(load_session_memory()))
        for kind in ("mentions_mention", "session_memory_book"):
            assert _memory_events(store, session_id, kind) == []
        agent.close()

    def test_duplicate_situation_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_session_situation(_situation())
        with pytest.raises(ValueError):
            agent.register_session_situation(_situation())
        assert len(_memory_events(
            store, session_id, "session_memory_situation")) == 1
        agent.close()

    def test_restore_builds_the_situation_from_the_store(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        export = store.export(session_id)
        outcome = agent.restore_session_situation()
        assert outcome["session_id"] == session_id
        situation_id = f"situation-{session_id[:8]}"
        assert outcome["situation"]["situation_id"] == situation_id
        situation = agent.get_session_situation(situation_id)
        # Judged by the shipped store: the situation
        # names the stored session itself, and counts
        # its transcript instead of carrying it.
        assert situation.session_ref == session_id
        assert situation.transcript_messages == len(
            export["context"])
        assert situation.saved_on == export["updated_at"][:10]
        # Composed by import: the session's memory map
        # stands as carried memory and standing
        # decisions, the roadmap's next work as slices.
        assert len(situation.memory) == 9
        assert [d.decision_id for d in situation.decisions] == [
            "map-ci-manual", "map-scribe-law"]
        road = load_roadmap()
        assert [s.slice_id for s in situation.open_slices[:2]] == [
            s.id for s in road.slices
            if s.status == "queued"][:2]
        assert len(situation.open_slices) == 1
        assert len(_memory_events(
            store, session_id, "session_memory_situation")) == 1
        with pytest.raises(ValueError):
            agent.restore_session_situation()
        agent.close()

    def test_restore_without_a_store_refuses_honestly(self, agent):
        with pytest.raises(ValueError):
            agent.restore_session_situation()

    def test_register_book_holds_and_publishes_in_order(
            self, agent):
        book = build_book({
            "title": "A held session memory book",
            "situations": [_stored_situation(_situation())]})
        outcome = agent.register_session_memory_book(book)
        assert outcome["count"] == 1
        assert [s["type"] for s in outcome["situations_news"]] == [
            "session_memory_situation"]
        assert agent.session_memory_book().title == (
            "A held session memory book")

    def test_register_book_twice_refuses(self, agent):
        agent.register_session_memory_book(load_session_memory())
        with pytest.raises(ValueError):
            agent.register_session_memory_book(load_session_memory())

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_session_memory_book()
        assert outcome["count"] == 1
        assert outcome["book"]["title"] == EXAMPLE_TITLE
        assert len(_memory_events(
            store, session_id, "session_memory_situation")) == 1
        assert agent.session_memory_book().panels[0].panel_id == (
            "panel-m152-boundary")
        agent.close()

    def test_record_same_book_twice_refuses(self, agent):
        agent.record_session_memory_book()
        with pytest.raises(ValueError):
            agent.record_session_memory_book()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_memory_book(tmp_path)
        book = load_session_memory_file(path)
        outcome = agent.record_session_memory_book(book)
        assert outcome["count"] == 1
        assert agent.get_session_memory_note(
            "note-connected-code").title == (
                "Retrieval returns connected code")

    def test_report_renders_the_example_when_unheld(self, agent):
        report = agent.report_session_memory()
        assert report["book"]["situation_count"] == 1
        assert "situation-m152-boundary" in report["situation_text"]
        assert "Panel in Session memory" in report["panel_text"]

    def test_report_renders_the_held_book_only(self, agent):
        agent.register_session_situation(_situation())
        report = agent.report_session_memory()
        assert report["book"]["title"] == (
            "Session memory across days")
        assert "note-connected-code" not in report["situation_text"]
        assert "note-test" in report["situation_text"]

    def test_report_registers_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.report_session_memory()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("session_memory")] == []
        agent.close()

    def test_no_live_resume_or_persist_road(
            self, agent, tmp_path):
        # This layer holds situations as data: it calls
        # no model, attaches or resumes no live session,
        # replays no transcript and persists nothing -
        # and there is no Part VIII board yet. Holding
        # or recording a situation changes no workspace
        # file and no live context.
        assert not hasattr(agent, "apply_session_memory")
        assert not hasattr(agent, "edit_session_memory")
        assert not hasattr(agent, "persist_session_memory")
        assert not hasattr(agent, "replay_session_memory")
        assert not hasattr(agent, "session_memory_board")
        (tmp_path / "alpha.py").write_text(
            "def greet(name):\n    return name\n", encoding="utf-8")
        before = {
            p.name: p.read_bytes()
            for p in tmp_path.glob("*.py")}
        from mythic_agent.agents.context import ContextBuilder
        builder = ContextBuilder(max_tokens=4000)
        builder.add_system("You are the coder.")
        builder.add_turn("user", "Build the slice.")
        built_before = builder.build()
        agent.register_session_situation(_situation())
        agent.record_session_memory_book()
        assert builder.build() == built_before
        assert {
            p.name: p.read_bytes()
            for p in tmp_path.glob("*.py")} == before


class TestSessionMemoryTerminalSurface:
    def test_show_situation_memory_slices_decisions_panel(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/daymemory")
        assert "Session Memory Across Days (M-153)" in text
        _, _, text = _slash(
            agent, "/daymemory situation situation-m152-boundary")
        assert "Graph retrieval landed" in text
        _, _, text = _slash(agent, "/daymemory memory")
        assert "note-connected-code" in text
        _, _, text = _slash(agent, "/daymemory slices")
        assert "M-153: Session memory across days" in text
        _, _, text = _slash(agent, "/daymemory decisions")
        assert "No Docker, ever" in text
        _, _, text = _slash(agent, "/daymemory panel")
        assert "Panel in Session memory" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/daymemory [show|situation <situation-id>"
                "|memory|slices|decisions|panel]") in text
        _, _, text = _slash(agent, "/daymemory dance party")
        assert text == USAGE
        _, _, text = _slash(
            agent, "/daymemory situation situation-nope")
        assert "no situation in the book" in text


@pytest.fixture()
def daymemory_handler(agent, monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.agents.llm import AGENT_REGISTRY
    published = []
    monkeypatch.setattr(
        handler_module, "publish_sync",
        lambda event, **kwargs: published.append((event, kwargs)))
    AGENT_REGISTRY["Primary"] = agent
    instance = CommandHandler.__new__(CommandHandler)
    instance.published = published
    yield instance
    AGENT_REGISTRY.pop("Primary", None)


def _daymemory_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestSessionMemoryCommand:
    def test_show_is_default(self, daymemory_handler, agent):
        daymemory_handler._handle_daymemory("")
        assert "Session Memory Across Days (M-153)" in (
            _daymemory_published_text(daymemory_handler))

    def test_situation_memory_slices_decisions_panel(
            self, daymemory_handler, agent):
        daymemory_handler._handle_daymemory(
            "situation situation-m152-boundary")
        assert "Graph retrieval landed" in _daymemory_published_text(
            daymemory_handler)
        daymemory_handler._handle_daymemory("memory")
        assert "note-connected-code" in _daymemory_published_text(
            daymemory_handler)
        daymemory_handler._handle_daymemory("slices")
        assert "M-153" in _daymemory_published_text(daymemory_handler)
        daymemory_handler._handle_daymemory("decisions")
        assert "No Docker, ever" in _daymemory_published_text(
            daymemory_handler)
        daymemory_handler._handle_daymemory("panel")
        assert "Panel in Session memory" in _daymemory_published_text(
            daymemory_handler)

    def test_bad_grammar_is_published(self, daymemory_handler, agent):
        daymemory_handler._handle_daymemory("dance party")
        assert USAGE in _daymemory_published_text(daymemory_handler)


class TestChatScreenRoutingSessionMemory:
    def test_daymemory_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command(
            "/daymemory situation situation-m152-boundary",
            _FakeLog())
        assert calls == [(
            "/daymemory", "situation situation-m152-boundary")]
