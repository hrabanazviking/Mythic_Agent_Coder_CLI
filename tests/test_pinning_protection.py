"""M-159 Pinning and protection - pure-layer tests.

TIER: integration

The pure layer is the pin itself, held as data: one
protected file or fact carried with its provenance
whole (what is pinned, its kind, the reference it
stands under, why it is protected, who pinned it,
the day, and where it was read from), composed by
import from the shipped holdings it protects (the
compaction glass-box, M-151, the context budget,
M-147, and the memory holdings M-150, M-153, M-154,
M-155, M-156, M-133), each judged by its own layer's
validation, a pin panel derived from the whole book
in settled order - pins are visible - the shipped
example book held in a data file, and a loader that
reads a book from any file. One thing is pinned once
in a book. Nothing here compacts any live context,
drops any message, calls a model, edits any code or
writes any project's files: holding a pin declares
protection, and that is the whole road.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.compaction_glassbox import (
    load_compaction_glassbox,
)
from mythic_agent.core.context_budget import (
    build_item as build_context_item,
)
from mythic_agent.core.cross_project_memory import (
    load_cross_project_memory,
)
from mythic_agent.core.decision_records import load_decision_records
from mythic_agent.core.project_memory_map import (
    build_entry as build_map_entry,
    load_project_memory_map,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.self_improving_ledger import (
    load_self_improving_ledger,
)
from mythic_agent.core.session_memory import load_session_memory
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.pinning_protection import (
    PINNING_PROTECTION_RESOURCE,
    PINNING_PROTECTION_SCHEMA,
    PINNING_PROTECTION_SLICE,
    PIN_KINDS,
    PLAIN_EXPLANATION,
    USAGE,
    Pin,
    PinKindCount,
    PinPanelRow,
    PinningBook,
    PinningPanel,
    PinningRegistry,
    book_record,
    build_book,
    build_panel,
    build_pin,
    build_row,
    derive_panel,
    format_panel,
    format_pin,
    format_pinning_protection_screen,
    format_pins,
    inspect_pin_source,
    is_protected,
    load_pinning_protection,
    load_pinning_protection_file,
    normalize_pin_kind,
    panel_plain_words,
    panel_record,
    parse_pin_args,
    pin_from_compaction_record,
    pin_from_context_item,
    pin_from_cross_project,
    pin_from_decision_record,
    pin_from_ledger_candidate,
    pin_from_memory_map,
    pin_from_session_memory,
    pin_record,
    pinned_refs,
    pins_from_memory_map,
    pins_from_session_memory,
    plain_words,
    validate_book,
    validate_panel,
    validate_pin,
    validate_row,
)

ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_TITLE = "Pinning and protection at the M-158 slice boundary"

WHY = "Compaction may never drop it while the test work stands."
BY = "Volmarr"
ON = "2026-11-08"


def _pin(**overrides):
    fields = {
        "pin_id": "pin-test",
        "subject": "the test fact",
        "kind": "fact",
        "ref": "fact-test",
        "why": WHY,
        "pinned_by": BY,
        "pinned_on": ON,
        "source": "test source",
    }
    fields.update(overrides)
    return build_pin(fields)


def _stored_pin(pin):
    stored = pin.to_record()
    stored.pop("type")
    stored.pop("slice")
    return stored


def _stored_panel(panel):
    stored = panel.to_record()
    stored.pop("type")
    stored.pop("slice")
    for row in stored["rows"]:
        row.pop("type")
        row.pop("slice")
    return stored


def _book(pins=None, **overrides):
    fields = {
        "title": "A test pinning book",
        "pins": [_stored_pin(item) for item in (
            pins if pins is not None else [_pin()])],
    }
    fields.update(overrides)
    return build_book(fields)


def _shipped_raw():
    path = ROOT / "mythic_agent" / "data" / "pinning_protection.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_constants_and_usage():
    assert PINNING_PROTECTION_SLICE == "M-159"
    assert PINNING_PROTECTION_SCHEMA == "mythic.pinning_protection/1"
    assert PINNING_PROTECTION_RESOURCE == "pinning_protection.yaml"
    assert PIN_KINDS == (
        "task", "law", "failing-test", "file", "fact")
    assert "may never drop" in PLAIN_EXPLANATION
    assert "compacts nothing, drops" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /pins")
    assert "pin <pin-id>" in USAGE


def test_roadmap_boundary_is_derived_from_the_shipped_roadmap():
    road = load_roadmap()
    ids = [item.id for item in road.slices]
    assert "M-159" in ids
    mine = road.slices[ids.index("M-159")]
    assert mine.title == "Pinning and protection"
    assert mine.part == 7
    assert "may never drop" in mine.summary
    assert "pins are" in mine.summary
    for earlier in road.slices[:ids.index("M-159")]:
        assert earlier.status == "done", earlier.id


def test_shipped_example_shape():
    book = load_pinning_protection()
    assert isinstance(book, PinningBook)
    assert book.title == EXAMPLE_TITLE
    assert book.pin_ids() == (
        "pin-the-task", "pin-forge-laws",
        "pin-failing-test", "pin-recipes-module")
    assert book.total_pins == 4
    first = book.pins[0]
    assert first.subject == (
        "the task the session is working on: "
        "M-159, pinning and protection")
    assert first.kind == "task"
    assert first.pinned_by == "Volmarr"
    assert first.pinned_on == "2026-11-08"
    assert len(book.panels) == 1


def test_shipped_panel_is_pinned_and_derived():
    book = load_pinning_protection()
    panel = book.panel_for("panel-m158-boundary")
    derived = derive_panel(book)
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert [row.pin_id for row in panel.rows] == [
        "pin-the-task", "pin-forge-laws",
        "pin-failing-test", "pin-recipes-module"]
    assert panel.total_pins == 4


def test_normalizers_and_aliases():
    assert normalize_pin_kind("Tasks") == "task"
    assert normalize_pin_kind("LAWS") == "law"
    assert normalize_pin_kind("rule") == "law"
    assert normalize_pin_kind("failing") == "failing-test"
    assert normalize_pin_kind("test") == "failing-test"
    assert normalize_pin_kind("Files") == "file"
    assert normalize_pin_kind("facts") == "fact"
    with pytest.raises(ValueError):
        normalize_pin_kind("vault")


def test_pin_validation_and_alias_spellings():
    pin = _pin()
    assert isinstance(pin, Pin)
    assert pin.kind == "fact"
    aliased = build_pin({
        "what": "the aliased law", "class": "laws",
        "reference": "law-x", "reason": "It governs the work.",
        "by": "Volmarr", "day": "2026-11-08",
        "source": "the charter"})
    assert aliased.subject == "the aliased law"
    assert aliased.kind == "law"
    assert aliased.ref == "law-x"
    assert aliased.pinned_by == "Volmarr"
    with pytest.raises(ValueError):
        build_pin({"subject": "the bare fact"})
    with pytest.raises(ValueError):
        _pin(pinned_on="08/11/2026")
    with pytest.raises(ValueError):
        _pin(pinned_on="2026-13-01")
    with pytest.raises(ValueError):
        _pin(kind="vault")


def test_pin_refuses_missing_provenance():
    fields = _stored_pin(_pin())
    fields.pop("pinned_by")
    with pytest.raises(ValueError, match="missing its"):
        build_pin(fields)
    fields = _stored_pin(_pin())
    fields.pop("source")
    with pytest.raises(ValueError, match="missing its"):
        build_pin(fields)
    fields = _stored_pin(_pin())
    fields["bogus"] = "nope"
    with pytest.raises(ValueError, match="unknown pin keys"):
        build_pin(fields)


def test_book_refuses_duplicate_pin_and_duplicate_thing():
    with pytest.raises(ValueError, match="already exists"):
        _book([_pin(), _pin(subject="another subject")])
    # One thing is pinned once in a book, under any
    # second pin id or subject.
    with pytest.raises(ValueError, match="pinned once"):
        _book([_pin(), _pin(pin_id="pin-copy")])
    # The same reference under another kind is another
    # thing, and the same kind under another reference
    # is another thing: both stand.
    book = _book([_pin(), _pin(
        pin_id="pin-law", subject="the test law", kind="law"),
        _pin(pin_id="pin-other", subject="the other fact",
             ref="fact-other")])
    assert book.total_pins == 3


def test_pin_for_ref_in_book():
    book = load_pinning_protection()
    pin = book.pin_for_ref("laws", "law-forge-protocol")
    assert pin.pin_id == "pin-forge-laws"
    assert isinstance(book.pin_for("pin-the-task"), Pin)
    with pytest.raises(KeyError):
        book.pin_for_ref("task", "task-nope")
    with pytest.raises(KeyError):
        book.pin_for("pin-nope")


def test_composition_from_compaction_record():
    book = load_compaction_glassbox()
    record = book.records[0]
    pin = pin_from_compaction_record(
        record, why=WHY, pinned_by=BY, pinned_on=ON)
    assert pin.kind == "fact"
    assert pin.ref == record.record_id
    assert pin.subject == f"compaction record {record.record_id}"
    # Only the id crosses: the record's own words stand
    # in no pin this road builds.
    blob = str(pin.to_record())
    assert record.title not in blob
    assert record.summary not in blob
    for piece in record.replaced:
        assert piece not in blob


def test_composition_from_context_item():
    file_item = build_context_item({
        "item_id": "ctx-file-x", "kind": "file",
        "title": "A file title of its own",
        "source": "workspace", "reason": "It is read.",
        "tokens": 10})
    pin = pin_from_context_item(
        file_item, why=WHY, pinned_by=BY, pinned_on=ON)
    assert pin.kind == "file"
    assert pin.ref == "ctx-file-x"
    assert "A file title of its own" not in str(pin.to_record())
    note_item = build_context_item({
        "item_id": "ctx-note-x", "kind": "note",
        "title": "A note title", "source": "session",
        "reason": "It is carried.", "tokens": 5})
    pin = pin_from_context_item(
        note_item, why=WHY, pinned_by=BY, pinned_on=ON)
    assert pin.kind == "fact"
    assert pin.ref == "ctx-note-x"


def test_composition_from_session_memory():
    book = load_session_memory()
    notes = [n for s in book.situations for n in s.memory if n.note_id]
    assert notes
    pin = pin_from_session_memory(
        notes[0], why=WHY, pinned_by=BY, pinned_on=ON)
    assert pin.kind == "fact"
    assert pin.ref == notes[0].note_id
    blob = str(pin.to_record())
    assert notes[0].title not in blob
    assert notes[0].detail not in blob


def test_composition_from_cross_project_and_ledger():
    lessons = [item for item in load_cross_project_memory().lessons
               if item.lesson_id]
    assert lessons
    pin = pin_from_cross_project(
        lessons[0], why=WHY, pinned_by=BY, pinned_on=ON)
    assert pin.kind == "law"
    assert pin.ref == lessons[0].lesson_id
    candidates = [c for c in load_self_improving_ledger().candidates
                  if c.candidate_id]
    assert candidates
    pin = pin_from_ledger_candidate(
        candidates[0], why=WHY, pinned_by=BY, pinned_on=ON)
    assert pin.kind == "fact"
    assert pin.ref == candidates[0].candidate_id


def test_composition_from_decision_record():
    record = load_decision_records().record_for("record-httpx-client")
    pin = pin_from_decision_record(
        record, why=WHY, pinned_by=BY, pinned_on=ON)
    assert pin.kind == "law"
    assert pin.ref == "record-httpx-client"
    blob = str(pin.to_record())
    assert record.title not in blob


def test_composition_from_memory_map_and_inspection():
    shipped = load_project_memory_map()
    first = shipped.entries[0]
    pin = pin_from_memory_map(
        first, why=WHY, pinned_by=BY, pinned_on=ON)
    assert pin.kind == "fact"
    assert pin.ref == first.entry_id
    seen = inspect_pin_source(first)
    assert seen == {"kind": "fact", "ref": first.entry_id}
    seen = inspect_pin_source(load_compaction_glassbox().records[0])
    assert seen == {"kind": "fact", "ref": "compact-pruner-boundary"}
    seen = inspect_pin_source(load_decision_records().records[0])
    assert seen["kind"] == "law"
    from mythic_agent.core.crew_memory import (
        build_entry as build_crew_entry,
    )
    crew_entry = build_crew_entry({
        "entry_id": "crew-note-1", "member": "cartographer",
        "title": "A crew fact held in a notebook",
        "fact": "The crew fact's own words.",
        "tags": ["roads"], "provenance": "test source"})
    seen = inspect_pin_source(crew_entry)
    assert seen == {"kind": "fact", "ref": "crew-note-1"}
    with pytest.raises(ValueError):
        inspect_pin_source(object())
    bare = build_map_entry({
        "section": "gotcha", "title": "A bare fact",
        "detail": "A fact with no standing reference.",
        "source": "test", "ref": "nowhere"})
    with pytest.raises(ValueError):
        pin_from_memory_map(bare, why=WHY, pinned_by=BY, pinned_on=ON)


def test_composition_requires_the_reason_and_pinner():
    note_book = load_session_memory()
    note = [n for s in note_book.situations for n in s.memory][0]
    with pytest.raises(ValueError, match="reason"):
        pin_from_session_memory(
            note, why=None, pinned_by=BY, pinned_on=ON)
    with pytest.raises(ValueError, match="who pinned it"):
        pin_from_session_memory(
            note, why=WHY, pinned_by=None, pinned_on=ON)
    with pytest.raises(ValueError, match="missing its"):
        validate_pin({"kind": "fact", "ref": "fact-x"})


def test_plural_composition_roads():
    book = load_session_memory()
    notes = [n for s in book.situations for n in s.memory if n.note_id]
    pins = pins_from_session_memory(
        book, why=WHY, pinned_by=BY, pinned_on=ON)
    assert len(pins) == len(notes)
    assert {p.kind for p in pins} == {"fact"}
    shipped = load_project_memory_map()
    pins = pins_from_memory_map(
        shipped, why=WHY, pinned_by=BY, pinned_on=ON)
    assert len(pins) == len(shipped.entries)


def test_book_validation_refusals():
    raw = _shipped_raw()
    raw["schema"] = "mythic.other/1"
    with pytest.raises(ValidationError):
        validate_book(raw)
    raw = _shipped_raw()
    raw["panels"][0]["total_pins"] = 9
    with pytest.raises(ValidationError):
        validate_book(raw)
    raw = _shipped_raw()
    raw["pins"][1]["ref"] = "task-m159"
    raw["pins"][1]["kind"] = "task"
    with pytest.raises(ValidationError):
        validate_book(raw)
    raw = _shipped_raw()
    raw["guide"]["title"] = "A different title"
    with pytest.raises(ValidationError):
        validate_book(raw, require_example=True)


def test_load_pinning_protection_file_roundtrip(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "pinning_protection.yaml").read_text(encoding="utf-8")
    path = tmp_path / "pinning_protection.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_pinning_protection_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.pin_ids()[0] == "pin-the-task"
    with pytest.raises(FileNotFoundError):
        load_pinning_protection_file(tmp_path / "nope.yaml")


def test_registry_holds_pins_one_by_one():
    registry = PinningRegistry()
    held = registry.register_pin({
        "subject": "the held fact", "kind": "fact",
        "ref": "fact-held", "why": WHY,
        "pinned_by": BY, "pinned_on": ON, "source": "test"})
    assert held.pin_id == "pin-1"
    second = registry.register_pin(_pin())
    assert second.pin_id == "pin-test"
    assert registry.latest_pin().pin_id == "pin-test"
    assert [p.pin_id for p in registry.list_pins()] == [
        "pin-1", "pin-test"]
    with pytest.raises(ValueError, match="pinned once"):
        registry.register_pin(_pin(pin_id="pin-copy"))
    with pytest.raises(ValueError):
        registry.register_pin(_pin())
    with pytest.raises(KeyError):
        registry.get_pin("pin-nope")
    assert registry.pin_for_ref("fact", "fact-test").pin_id == (
        "pin-test")
    named = PinningRegistry()
    named.register_book(_book())
    assert named.book().title == "A test pinning book"
    assert named.panel().total_pins == 1
    with pytest.raises(ValueError):
        named.register_book(_book(title="Another title"))


def test_panel_row_judged_against_its_pin():
    pin = _pin()
    panel = derive_panel(_book([pin]))
    row = panel.rows[0]
    assert isinstance(row, PinPanelRow)
    assert validate_row(row, pin) == row
    bad = build_row({
        "pin_id": "pin-test", "subject": "another subject",
        "kind": "fact", "ref": "fact-test",
        "pinned_by": BY, "pinned_on": ON})
    with pytest.raises(ValueError, match="disagrees"):
        validate_row(bad, pin)
    counts = panel.kind_counts
    assert counts == (PinKindCount(kind="fact", pins=1),)


def test_panel_validation_refusals():
    book = _book()
    panel = derive_panel(book)
    stored = _stored_panel(panel)
    assert validate_panel(stored, book) == panel
    bad = _stored_panel(panel)
    bad["total_pins"] = 9
    with pytest.raises(ValueError):
        validate_panel(bad)
    bad = _stored_panel(panel)
    bad["account"] = ["A different account."]
    with pytest.raises(ValueError, match="disagrees"):
        validate_panel(bad, book)
    built = build_panel(_stored_panel(panel))
    assert built == panel
    # Panel order is settled by kind first: a task pin
    # held second still stands first on the panel.
    mixed = _book([_pin(), _pin(
        pin_id="pin-task", subject="the held task",
        kind="task", ref="task-test")])
    panel = derive_panel(mixed)
    assert [row.pin_id for row in panel.rows] == [
        "pin-task", "pin-test"]


def test_records_and_plain_words():
    pin = _pin()
    record = pin_record(pin)
    assert record["type"] == "pinning_protection_pin"
    assert record["news"] is True
    assert "the test fact" in record["headline"]
    assert set(record) == {
        "type", "slice", "pin_id", "subject", "kind", "ref",
        "why", "pinned_by", "pinned_on", "source",
        "news", "headline"}
    words = plain_words(pin)
    assert "the test fact" in words and "fact-test" in words
    book = load_pinning_protection()
    panel_rec = panel_record(derive_panel(book), book)
    assert panel_rec["headline"].startswith("Pin panel: 4 pins")
    book_rec = book_record(book)
    assert book_rec["pin_count"] == 4
    told = panel_plain_words(book)
    assert "pin-forge-laws" in told
    assert "Every pin is visible" in told


def test_formatters_and_screen():
    book = load_pinning_protection()
    text = format_pin(book.pins[0])
    assert "pin-the-task" in text
    assert "task-m159" in text
    assert "compacts nothing and drops nothing" in text
    assert "pin-forge-laws" in format_pins(book)
    laws = format_pins(book, "laws")
    assert "pin-forge-laws" in laws
    assert "pin-the-task" not in laws
    panel_text = format_panel(book)
    assert "Pin panel in Pinning and protection" in panel_text
    screen = format_pinning_protection_screen()
    assert "Pinning and Protection (M-159)" in screen
    assert USAGE in screen


def test_parse_pin_args_grammar():
    assert parse_pin_args("") == ("show", None)
    assert parse_pin_args("show") == ("show", None)
    assert parse_pin_args("list") == ("show", None)
    assert parse_pin_args("pin pin-test") == ("pin", "pin-test")
    assert parse_pin_args("kind laws") == ("kind", "law")
    assert parse_pin_args("kind failing-test") == (
        "kind", "failing-test")
    assert parse_pin_args("panel") == ("panel", None)
    for bad in ("dance", "pin", "pin a b", "kind", "kind vault", 5):
        with pytest.raises(ValueError):
            parse_pin_args(bad)


def test_visible_surface_pinned_refs_and_is_protected():
    book = load_pinning_protection()
    assert pinned_refs(book) == (
        ("task", "task-m159"), ("law", "law-forge-protocol"),
        ("failing-test", "test-pinning-protection"),
        ("file", "file-context-recipes"))
    assert is_protected(book, "laws", "law-forge-protocol") is True
    assert is_protected(book, "task", "task-nope") is False
    assert is_protected(book, "fact", "task-m159") is False


def test_honest_boundary_module_imports_no_live_roads():
    source = (ROOT / "mythic_agent" / "core"
              / "pinning_protection.py").read_text(encoding="utf-8")
    assert "from .compaction_glassbox import" in source
    assert "from .context_budget import" in source
    assert "from .session_memory import" in source
    assert "from .cross_project_memory import" in source
    assert "from .self_improving_ledger import" in source
    assert "from .decision_records import" in source
    assert "from .project_memory_map import" in source
    assert "from ..agents" not in source
    assert "from ..ui" not in source
    assert "from ..terminal" not in source
    assert "import agents" not in source


def test_registry_constructor_and_titleless_book_refusal():
    registry = PinningRegistry(load_pinning_protection())
    assert registry.book().title == EXAMPLE_TITLE
    assert registry.panel().total_pins == 4
    bare = PinningRegistry()
    bare.register_pin(_pin())
    with pytest.raises(ValueError, match="no pinning book is held"):
        bare.book()
    # The panel still derives from what stands held,
    # title or no title: derivation needs no book.
    assert bare.panel().total_pins == 1
    assert isinstance(derive_panel(load_pinning_protection()),
                      PinningPanel)
    direct = validate_pin(_stored_pin(_pin()))
    assert direct == _pin()


# -- agent layer -----------------------------------------------------------
#
# M-159 agent layer: the agent holds a PinningRegistry
# for the session (session state only, no new setting),
# pins are held by being registered - published as
# their pin_record session news with the derived
# panel_record, through the checkpoint road, deduped
# per shape - the report road renders the held book
# (or the shipped example when unheld) through the
# pure formatters, a protection road reads the
# session's compaction glass-box book onto pins and
# holds them (mutating no live compaction record), and
# the /pins surface rides both roads on the pure
# parser + formatters. Status, get, panel and report
# reads register and publish nothing, answer from the
# held registry first and from the shipped example
# only while nothing is held - a held session never
# falls back to the example. The panel derives at call
# time from the whole book, never held. This layer
# calls no model, compacts nothing, drops nothing and
# persists nothing beyond the session journal news,
# and there is no Part VIII board yet, so the screen
# is where the book is visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _pin_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_pin_book(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "pinning_protection.yaml").read_text(encoding="utf-8")
    path = tmp_path / "pinning_protection.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestPinningAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.pinning_protection_status()
        assert status["pins"] == []
        assert status["book"] is None
        assert status["protecting"]["title"] == EXAMPLE_TITLE
        assert len(status["protecting"]["pins"]) == 4
        assert status["panel"]["total_pins"] == 4
        assert status["panels"][0]["panel_id"] == "panel-m158-boundary"
        assert status["book_record"]["pin_count"] == 4
        assert "Pinning and Protection (M-159)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._pinning_protection_registry()
        assert agent._pinning_protection_registry() is first
        assert agent._pinning_protection_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.pinning_protection_status()
        agent.get_pin("pin-the-task")
        agent.pinning_protection_panel()
        agent.report_pinning_protection()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("pinning_protection")] == []
        agent.close()

    def test_unheld_reads_raise(self, agent):
        with pytest.raises(KeyError):
            agent.get_pin("pin-nope")

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_pin(_pin())
        status = agent.pinning_protection_status()
        assert [item["pin_id"] for item in status["pins"]] == [
            "pin-test"]
        assert status["book"]["title"] == "Pinning and protection"

    def test_held_session_never_falls_back_to_the_example(
            self, agent):
        agent.register_pin(_pin())
        with pytest.raises(KeyError):
            agent.get_pin("pin-the-task")
        pin = agent.get_pin("pin-test")
        assert pin.subject == "the test fact"
        assert agent.pinning_protection_book().title == (
            "Pinning and protection")


class TestPinningAgentHolding:
    def test_register_pin_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_pin(_pin())
        assert outcome["pin"]["pin_id"] == "pin-test"
        assert outcome["pin_news"]["type"] == "pinning_protection_pin"
        events = _pin_events(
            store, session_id, "pinning_protection_pin")
        assert len(events) == 1
        assert events[0]["pin_id"] == "pin-test"
        agent._publish_pinning_record(outcome["pin_news"])
        assert len(_pin_events(
            store, session_id, "pinning_protection_pin")) == 1
        agent._publish_pinning_record(
            {"type": "mentions_mention", "mention_id": "mention-x"})
        agent._publish_pinning_record(
            book_record(load_pinning_protection()))
        for kind in ("mentions_mention", "pinning_protection_book"):
            assert _pin_events(store, session_id, kind) == []
        agent.close()

    def test_duplicate_pin_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_pin(_pin())
        with pytest.raises(ValueError):
            agent.register_pin(_pin())
        with pytest.raises(ValueError):
            agent.register_pin(_pin(pin_id="pin-copy"))
        assert len(_pin_events(
            store, session_id, "pinning_protection_pin")) == 1
        agent.close()

    def test_protect_session_compactions_carries_ids_only(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        glassbox_book = load_compaction_glassbox()
        records = [r for r in glassbox_book.records if r.record_id]
        expected = len(records)
        outcome = agent.protect_session_compactions(
            why="A compaction the session still stands on.",
            pinned_by="Volmarr", pinned_on="2026-11-08")
        assert outcome["count"] == expected
        events = _pin_events(
            store, session_id, "pinning_protection_pin")
        assert len(events) == expected
        blob = str(events) + str(outcome["pins"])
        for record in records:
            assert record.title not in blob
            assert record.summary not in blob
            for piece in record.replaced:
                assert piece not in blob
        # Protecting mutated no live compaction: the
        # session's glass-box book stands whole.
        assert agent.compaction_glassbox_book().records == (
            glassbox_book.records)
        assert agent.pinning_protection_panel().total_pins == expected
        with pytest.raises(ValueError):
            agent.protect_session_compactions(
                why="Again.", pinned_by="Volmarr",
                pinned_on="2026-11-08")
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent):
        book = _book()
        outcome = agent.register_pinning_book(book)
        assert outcome["count"] == 1
        assert [item["type"] for item in outcome["pins_news"]] == [
            "pinning_protection_pin"]
        assert agent.pinning_protection_book().title == (
            "A test pinning book")

    def test_register_book_twice_refuses(self, agent):
        agent.register_pinning_book(load_pinning_protection())
        with pytest.raises(ValueError):
            agent.register_pinning_book(load_pinning_protection())

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_pinning_book()
        assert outcome["count"] == 4
        assert outcome["book"]["title"] == EXAMPLE_TITLE
        assert len(_pin_events(
            store, session_id, "pinning_protection_pin")) == 4
        assert agent.pinning_protection_book().panels[0].panel_id == (
            "panel-m158-boundary")
        agent.close()

    def test_record_same_book_twice_refuses(self, agent):
        agent.record_pinning_book()
        with pytest.raises(ValueError):
            agent.record_pinning_book()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_pin_book(tmp_path)
        book = load_pinning_protection_file(path)
        outcome = agent.record_pinning_book(book)
        assert outcome["count"] == 4
        assert agent.get_pin("pin-the-task").kind == "task"

    def test_report_renders_the_example_when_unheld(self, agent):
        report = agent.report_pinning_protection()
        assert report["book"]["pin_count"] == 4
        assert "pin-the-task" in report["pins_text"]
        assert "Pin panel in Pinning and protection" in (
            report["panel_text"])

    def test_report_renders_the_held_book_only(self, agent):
        agent.register_pin(_pin())
        report = agent.report_pinning_protection()
        assert report["book"]["title"] == "Pinning and protection"
        assert "pin-the-task" not in report["pins_text"]
        assert "pin-test" in report["pins_text"]

    def test_report_registers_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.report_pinning_protection()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("pinning_protection")] == []
        agent.close()

    def test_no_live_compact_or_persist_road(
            self, agent, tmp_path):
        # This layer holds pins as data: it calls no
        # model, compacts no live context, drops no
        # message, writes no project files and persists
        # nothing - and there is no Part VIII board yet.
        # Holding, recording or protecting changes no
        # workspace file and no built context.
        assert not hasattr(agent, "apply_pinning_protection")
        assert not hasattr(agent, "compact_pinning_protection")
        assert not hasattr(agent, "persist_pinning_protection")
        assert not hasattr(agent, "pinning_protection_board")
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
        agent.register_pin(_pin())
        agent.record_pinning_book()
        agent.protect_session_compactions(
            why="A compaction the session still stands on.",
            pinned_by="Volmarr", pinned_on="2026-11-08")
        assert builder.build() == built_before
        assert {
            p.name: p.read_bytes()
            for p in tmp_path.glob("*.py")} == before


class TestPinningTerminalSurface:
    def test_show_pin_kind_panel(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/pins")
        assert "Pinning and Protection (M-159)" in text
        _, _, text = _slash(agent, "/pins pin pin-the-task")
        assert "task-m159" in text
        _, _, text = _slash(agent, "/pins kind laws")
        assert "pin-forge-laws" in text
        assert "pin-the-task" not in text
        _, _, text = _slash(agent, "/pins panel")
        assert "Pin panel in Pinning and protection" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/pins [show|pin <pin-id>"
                "|kind <kind>|panel]") in text
        _, _, text = _slash(agent, "/pins dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/pins pin pin-nope")
        assert "no pin in the book" in text


@pytest.fixture()
def pins_handler(agent, monkeypatch):
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


def _pins_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestPinningCommand:
    def test_show_is_default(self, pins_handler, agent):
        pins_handler._handle_pins("")
        assert "Pinning and Protection (M-159)" in (
            _pins_published_text(pins_handler))

    def test_pin_kind_panel(self, pins_handler, agent):
        pins_handler._handle_pins("pin pin-the-task")
        assert "task-m159" in _pins_published_text(pins_handler)
        pins_handler._handle_pins("kind laws")
        assert "pin-forge-laws" in _pins_published_text(pins_handler)
        pins_handler._handle_pins("panel")
        assert "Pin panel in Pinning and protection" in (
            _pins_published_text(pins_handler))

    def test_bad_grammar_is_published(self, pins_handler, agent):
        pins_handler._handle_pins("dance party")
        assert USAGE in _pins_published_text(pins_handler)


class TestChatScreenRoutingPins:
    def test_pins_routes_as_system_command(self, monkeypatch):
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
            "/pins pin pin-the-task", _FakeLog())
        assert calls == [("/pins", "pin pin-the-task")]
