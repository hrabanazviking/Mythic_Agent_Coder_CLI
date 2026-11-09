"""M-165 The subconscious v2 - pure-layer tests.

TIER: integration

The pure layer is the dual-layer vector memory at
v2, held as data: one memory record carried with
its provenance whole (the layer it stands in -
core or subconscious - where it came from, by the
shipped piece's id alone, the session and day it
was earned, who recorded it and where it was read
from), its confidence (the trust it was earned
with) and its decay (a half-life in days and the
day it was last earned: the effective confidence
halves every half-life, so a memory stands fresh,
fading, stale or faded as of any named day, and
re-earning resets the decay clock at the same
trust - it never inflates it), composed by import
from the shipped layers it extends (the project
memory map M-150, session memory M-153,
cross-project memory M-154, the self-improving
ledger M-155, crew memory M-133 and the shipped
vector record shape), each judged by its own
layer's validation, a subconscious panel derived
from the whole book as of a day, a freshness
verdict derived for the whole book - a faded book
is named neglected plainly, never smoothed - the
shipped example book held in a data file, and a
loader that reads a book from any file. Nothing
here sends, posts, schedules, calls a model or
writes any live memory: earning a v2 memory
records an earning, and that is the whole road.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.crew_memory import load_crew_memory
from mythic_agent.core.cross_project_memory import (
    load_cross_project_memory)
from mythic_agent.core.project_memory_map import load_project_memory_map
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.self_improving_ledger import (
    load_self_improving_ledger)
from mythic_agent.core.session_memory import load_session_memory
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.subconscious_v2 import (
    FRESHNESS_STATES,
    MEMORY_LAYERS,
    PLAIN_EXPLANATION,
    SOURCE_KINDS,
    SUBCONSCIOUS_V2_RESOURCE,
    SUBCONSCIOUS_V2_SCHEMA,
    SUBCONSCIOUS_V2_SLICE,
    USAGE,
    VERDICT_WORDS,
    FreshnessVerdict,
    StateCount,
    SubconsciousBook,
    SubconsciousMemory,
    SubconsciousPanel,
    SubconsciousPanelRow,
    SubconsciousRegistry,
    age_days,
    book_record,
    build_book,
    build_memory,
    build_panel,
    build_verdict,
    derive_panel,
    derive_verdict,
    effective_confidence,
    format_memories,
    format_memory,
    format_panel,
    format_subconscious_screen,
    format_verdict,
    freshness_state,
    inspect_memory_source,
    load_subconscious_v2,
    load_subconscious_v2_file,
    memories_from_crew_memory,
    memories_from_cross_project,
    memories_from_ledger,
    memories_from_memory_map,
    memories_from_session_memory,
    memory_from_crew_entry,
    memory_from_cross_project_lesson,
    memory_from_ledger_candidate,
    memory_from_map_entry,
    memory_from_session_note,
    memory_from_vector_record,
    memory_record,
    memory_refs,
    normalize_freshness_state,
    normalize_memory_layer,
    normalize_source_kind,
    panel_plain_words,
    panel_record,
    parse_subconscious_args,
    plain_words,
    reearn_memory,
    total_memories,
    validate_book,
    validate_memory,
    validate_panel,
    validate_verdict,
    verdict_plain_words,
    verdict_record,
)

ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_TITLE = "The subconscious v2 at the M-164 slice boundary"

BY = "Volmarr"
ON = "2026-11-09"


def _memory(**overrides):
    fields = {
        "memory_id": "memory-test",
        "title": "the test memory, earned by hand",
        "layer": "core",
        "source_kind": "manual",
        "source_ref": "ref-test",
        "origin_session": "session-test",
        "earned_on": "2026-11-01",
        "recorded_by": BY,
        "source": "test source",
        "confidence": 0.8,
        "half_life_days": 10,
    }
    fields.update(overrides)
    return build_memory(fields)


def _stored_memory(memory):
    stored = memory.to_record()
    for key in ("type", "slice"):
        stored.pop(key)
    return stored


# ---------------------------------------------------------------------
# The shipped example book and the roadmap.
# ---------------------------------------------------------------------


def test_shipped_book_loads_with_pinned_shape():
    book = load_subconscious_v2()
    assert book.title == EXAMPLE_TITLE
    assert book.memory_ids() == (
        "memory-no-docker-law", "memory-commit-before-answer",
        "memory-suite-extras", "memory-samtal-wal",
        "memory-reap-at-bank", "memory-two-roads")
    assert book.total_memories == 6
    assert len(book.panels) == 1
    panel = book.panel_for("panel-m164-boundary")
    assert panel.as_of == ON
    assert panel.total_core == 3
    assert panel.total_subconscious == 3


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-165")]
    assert slice_.title == "The subconscious v2"
    assert "provenance" in slice_.summary
    assert "confidence" in slice_.summary
    assert "decay" in slice_.summary
    assert SUBCONSCIOUS_V2_SLICE == "M-165"
    assert SUBCONSCIOUS_V2_SCHEMA == "mythic.subconscious_v2/1"
    assert SUBCONSCIOUS_V2_RESOURCE == "subconscious_v2.yaml"


def test_closed_vocabularies():
    assert MEMORY_LAYERS == ("core", "subconscious")
    assert FRESHNESS_STATES == ("fresh", "fading", "stale", "faded")
    assert "memory-map" in SOURCE_KINDS
    assert "vector-record" in SOURCE_KINDS
    assert VERDICT_WORDS == (
        "well-kept", "fading", "going-stale", "neglected")
    assert normalize_memory_layer("VECTOR") == "subconscious"
    assert normalize_memory_layer("core-memory") == "core"
    assert normalize_source_kind("map") == "memory-map"
    assert normalize_source_kind("lesson") == "cross-project-lesson"
    assert normalize_freshness_state("gone") == "faded"
    with pytest.raises(ValueError):
        normalize_memory_layer("archive")
    with pytest.raises(ValueError):
        normalize_source_kind("dream")
    with pytest.raises(ValueError):
        normalize_freshness_state("bright")


# ---------------------------------------------------------------------
# The memory record: provenance whole, judged whole.
# ---------------------------------------------------------------------


def test_memory_record_round_trips():
    memory = _memory()
    assert validate_memory(_stored_memory(memory)) == memory
    record = memory.to_record()
    assert record["type"] == "subconscious_v2_memory"
    assert record["slice"] == "M-165"
    assert record["last_earned_on"] == "2026-11-01"
    assert record["reearn_count"] == 0


def test_memory_provenance_is_whole_and_required():
    for field in ("title", "layer", "source_kind", "source_ref",
                  "origin_session", "earned_on", "recorded_by",
                  "source", "confidence"):
        fields = _stored_memory(_memory())
        fields.pop(field)
        with pytest.raises(ValueError):
            build_memory(fields)


def test_memory_refuses_unknown_keys_and_split_spellings():
    fields = _stored_memory(_memory())
    fields["dream"] = "x"
    with pytest.raises(ValueError):
        build_memory(fields)
    fields = _stored_memory(_memory())
    fields["kind"] = "manual"
    fields["source_kind"] = "memory-map"
    with pytest.raises(ValueError):
        build_memory(fields)


def test_memory_confidence_is_bounded():
    with pytest.raises(ValueError):
        _memory(confidence=1.5)
    with pytest.raises(ValueError):
        _memory(confidence=-0.1)
    with pytest.raises(ValueError):
        _memory(confidence=True)
    with pytest.raises(ValueError):
        _memory(confidence="high")
    assert _memory(confidence=0).confidence == 0.0
    assert _memory(confidence=1).confidence == 1.0


def test_memory_decay_fields_are_judged():
    with pytest.raises(ValueError):
        _memory(half_life_days=0)
    with pytest.raises(ValueError):
        _memory(half_life_days=2.5)
    with pytest.raises(ValueError):
        _memory(last_earned_on="2026-10-01")
    with pytest.raises(ValueError):
        _memory(earned_on="Nov 1 2026")
    memory = _memory(last_earned_on="2026-11-05", reearn_count=2)
    assert memory.last_earned_on == "2026-11-05"
    assert memory.reearn_count == 2


# ---------------------------------------------------------------------
# Decay: derived, never stored; re-earning resets the clock only.
# ---------------------------------------------------------------------


def test_effective_confidence_halves_per_half_life():
    memory = _memory()
    assert effective_confidence(memory, "2026-11-01") == 0.8
    assert effective_confidence(memory, "2026-11-11") == 0.4
    assert effective_confidence(memory, "2026-11-21") == 0.2
    assert age_days(memory, "2026-11-21") == 20


def test_freshness_bands():
    memory = _memory()
    assert freshness_state(memory, "2026-11-01") == "fresh"
    assert freshness_state(memory, "2026-11-11") == "fading"
    assert freshness_state(memory, "2026-11-21") == "stale"
    assert freshness_state(memory, "2026-12-21") == "faded"


def test_decay_refuses_a_day_before_the_last_earning():
    memory = _memory(last_earned_on="2026-11-05", reearn_count=1)
    with pytest.raises(ValueError):
        effective_confidence(memory, "2026-11-01")
    with pytest.raises(ValueError):
        freshness_state(memory, "2026-11-04")


def test_reearn_resets_the_clock_at_the_same_trust():
    memory = _memory()
    assert freshness_state(memory, "2026-12-21") == "faded"
    renewed = reearn_memory(memory, on="2026-12-21")
    assert renewed.confidence == memory.confidence
    assert renewed.last_earned_on == "2026-12-21"
    assert renewed.reearn_count == 1
    assert freshness_state(renewed, "2026-12-21") == "fresh"
    assert memory.reearn_count == 0
    with pytest.raises(ValueError):
        reearn_memory(memory, on="2026-10-01")


# ---------------------------------------------------------------------
# Composition by import: ids only across the seams.
# ---------------------------------------------------------------------


def test_memory_from_map_entry_carries_id_only():
    entry = load_project_memory_map().entries[0]
    memory = memory_from_map_entry(
        entry, origin_session="session-test", earned_on=ON,
        recorded_by=BY)
    assert memory.source_kind == "memory-map"
    assert memory.source_ref == entry.entry_id
    assert memory.layer == "core"
    assert memory.memory_id == f"memory-{entry.entry_id}"
    assert entry.detail not in memory.title
    assert entry.detail not in memory.source


def test_memory_from_ledger_candidate_and_lesson():
    candidate = load_self_improving_ledger().candidates[0]
    memory = memory_from_ledger_candidate(
        candidate, origin_session="session-test", earned_on=ON,
        recorded_by=BY)
    assert memory.source_kind == "ledger-candidate"
    assert memory.source_ref == candidate.candidate_id
    lesson = load_cross_project_memory().lessons[0]
    learned = memory_from_cross_project_lesson(
        lesson, origin_session="session-test", earned_on=ON,
        recorded_by=BY)
    assert learned.source_kind == "cross-project-lesson"
    assert learned.source_ref == lesson.lesson_id
    assert learned.layer == "subconscious"


def test_memory_from_session_note_and_crew_entry():
    note = load_session_memory().situations[0].memory[0]
    memory = memory_from_session_note(
        note, origin_session="session-test", earned_on=ON,
        recorded_by=BY)
    assert memory.source_kind == "session-note"
    assert memory.source_ref == note.note_id
    entry = load_crew_memory().notebooks[0].entries[0]
    fact = memory_from_crew_entry(
        entry, origin_session="session-test", earned_on=ON,
        recorded_by=BY)
    assert fact.source_kind == "crew-fact"
    assert fact.source_ref == entry.entry_id
    assert entry.fact not in fact.title


def test_memory_from_vector_record_carries_ref_only():
    record = {"text": "the archived words themselves",
              "vector": [0.1, 0.2, 0.3],
              "metadata": {"name": "archival-alpha"}}
    memory = memory_from_vector_record(
        record, origin_session="session-test", earned_on=ON,
        recorded_by=BY)
    assert memory.source_kind == "vector-record"
    assert memory.source_ref == "archival-alpha"
    assert "archived words" not in memory.title
    with pytest.raises(ValueError):
        memory_from_vector_record(
            {"text": "x", "vector": [0.1], "metadata": {}},
            origin_session="session-test", earned_on=ON,
            recorded_by=BY)
    with pytest.raises(ValueError):
        memory_from_vector_record(
            {"text": "x", "vector": "nope", "metadata": {}},
            origin_session="session-test", earned_on=ON,
            recorded_by=BY, ref="ref-x")


def test_composition_refuses_a_piece_with_no_id():
    entry = {"section": "architecture", "title": "an unnamed entry",
             "detail": "a detail", "source": "test", "ref": "ref-x"}
    with pytest.raises(ValueError):
        memory_from_map_entry(
            entry, origin_session="session-test", earned_on=ON,
            recorded_by=BY)


def test_bulk_roads_earn_whole_holdings():
    earned = dict(origin_session="session-test", earned_on=ON,
                  recorded_by=BY)
    from_map = memories_from_memory_map(load_project_memory_map(), **earned)
    assert len(from_map) == len(load_project_memory_map().entries)
    assert all(m.source_kind == "memory-map" for m in from_map)
    from_notes = memories_from_session_memory(load_session_memory(), **earned)
    assert len(from_notes) == 3
    from_ledger = memories_from_ledger(load_self_improving_ledger(), **earned)
    assert len(from_ledger) == len(load_self_improving_ledger().candidates)
    from_cross = memories_from_cross_project(
        load_cross_project_memory(), **earned)
    assert len(from_cross) == 3
    from_crew = memories_from_crew_memory(load_crew_memory(), **earned)
    assert len(from_crew) >= 1
    assert all(m.source_kind == "crew-fact" for m in from_crew)


def test_inspect_memory_source_judges_by_owning_layer():
    entry = load_project_memory_map().entries[0]
    assert inspect_memory_source(entry) == {
        "source_kind": "memory-map", "source_ref": entry.entry_id}
    assert inspect_memory_source(_memory())["source_kind"] == "manual"
    with pytest.raises(ValueError):
        inspect_memory_source(42)


# ---------------------------------------------------------------------
# The panel and the verdict: derived, judged against the book.
# ---------------------------------------------------------------------


def test_panel_is_derived_in_panel_order():
    book = load_subconscious_v2()
    panel = derive_panel(book, ON)
    assert [r.memory_id for r in panel.rows] == [
        "memory-commit-before-answer", "memory-no-docker-law",
        "memory-suite-extras", "memory-reap-at-bank",
        "memory-samtal-wal", "memory-two-roads"]
    assert panel.total_memories == 6
    assert panel.total_reearned == 3
    states = {c.state: c.items for c in panel.state_counts}
    assert states == {"fresh": 3, "fading": 1, "stale": 1, "faded": 1}
    row = panel.row_for("memory-two-roads")
    assert row.freshness == "faded"
    assert row.effective_confidence < 0.01
    stored = book.panel_for("panel-m164-boundary")
    assert validate_panel(stored, book) == stored
    assert stored.rows == panel.rows
    assert stored.account == panel.account


def test_panel_defaults_to_the_books_latest_day():
    book = load_subconscious_v2()
    panel = derive_panel(book)
    assert panel.as_of == ON


def test_panel_refuses_a_stored_panel_that_disagrees():
    book = load_subconscious_v2()
    panel = derive_panel(book, ON)
    stored = panel.to_record()
    for key in ("type", "slice"):
        stored.pop(key)
    for row in stored["rows"]:
        for key in ("type", "slice"):
            row.pop(key)
    stored["rows"][0]["effective_confidence"] = 0.01
    with pytest.raises(ValueError):
        validate_panel(stored, book)
    with pytest.raises(ValueError):
        build_panel({**stored, "total_memories": 99})


def test_verdict_names_a_faded_book_neglected():
    book = load_subconscious_v2()
    verdict = derive_verdict(book, ON)
    assert verdict.verdict == "neglected"
    assert verdict.total_fresh == 3
    assert verdict.total_faded == 1
    assert verdict.distinct_sources == 6
    stored_verdict = verdict.to_record()
    for key in ("type", "slice"):
        stored_verdict.pop(key)
    assert validate_verdict(stored_verdict, book) == verdict
    fresh_book = SubconsciousBook(
        title="a fresh book", memories=(_memory(),))
    assert derive_verdict(fresh_book, "2026-11-01").verdict == "well-kept"
    assert derive_verdict(fresh_book, "2026-11-11").verdict == "fading"
    assert derive_verdict(fresh_book, "2026-11-21").verdict == "going-stale"
    with pytest.raises(ValueError):
        build_verdict({**stored_verdict, "verdict": "well-kept"})


def test_book_laws_one_earning_per_piece():
    first = _memory()
    second = _memory(memory_id="memory-other", title="another earning")
    with pytest.raises(ValueError):
        SubconsciousBook(title="a forked book", memories=(first, second))
    with pytest.raises(ValueError):
        SubconsciousBook(title="a doubled book", memories=(first, first))
    book = SubconsciousBook(title="a sound book", memories=(first,))
    assert book.memory_for("memory-test") == first
    assert book.memory_for_source("manual", "ref-test") == first
    assert total_memories(book) == 1
    assert memory_refs(book) == (("manual", "ref-test"),)
    with pytest.raises(KeyError):
        book.memory_for("memory-nope")


def test_book_file_loader_reads_any_file(tmp_path):
    book = load_subconscious_v2()
    raw = yaml.safe_load(
        (ROOT / "mythic_agent" / "data" / "subconscious_v2.yaml").read_text())
    raw["guide"]["title"] = "A copied subconscious book"
    path = tmp_path / "copy.yaml"
    path.write_text(yaml.safe_dump(raw))
    copied = load_subconscious_v2_file(path)
    assert copied.title == "A copied subconscious book"
    assert copied.memory_ids() == book.memory_ids()
    raw["schema"] = "mythic.other/9"
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(ValidationError):
        load_subconscious_v2_file(path)
    with pytest.raises(ValidationError):
        validate_book({"schema": SUBCONSCIOUS_V2_SCHEMA})


def test_registry_holds_and_reearns():
    registry = SubconsciousRegistry()
    held = registry.register_memory(_memory(memory_id=None))
    assert held.memory_id == "memory-1"
    with pytest.raises(ValueError):
        registry.register_memory(_memory(memory_id="memory-other"))
    renewed = registry.reearn_memory("memory-1", on="2026-12-21")
    assert renewed.reearn_count == 1
    assert registry.get_memory("memory-1").last_earned_on == "2026-12-21"
    assert registry.latest_memory() == renewed
    assert registry.panel("2026-12-21").total_memories == 1
    assert registry.verdict("2026-12-21").verdict == "well-kept"
    registry.register_book(load_subconscious_v2())
    assert registry.book().total_memories == 7
    with pytest.raises(ValueError):
        registry.register_book(load_subconscious_v2())
    with pytest.raises(KeyError):
        registry.get_memory("memory-nope")


# ---------------------------------------------------------------------
# News records, plain words, screens and the shared grammar.
# ---------------------------------------------------------------------


def test_news_records_carry_headlines():
    book = load_subconscious_v2()
    record = memory_record(book.memories[0])
    assert record["news"] is True
    assert "map-no-docker" in record["headline"]
    panel = panel_record(derive_panel(book, ON), book)
    assert panel["type"] == "subconscious_v2_panel"
    assert "6 memories" in panel["headline"]
    verdict = verdict_record(derive_verdict(book, ON), book)
    assert "neglected" in verdict["headline"]
    assert book_record(book)["memory_count"] == 6
    assert "no Docker ever" in plain_words(book.memories[0])
    assert "memory-two-roads" in panel_plain_words(book, ON)
    assert "neglected" in verdict_plain_words(book, ON)


def test_formatters_and_screen():
    book = load_subconscious_v2()
    block = format_memory(book.memories[0], ON)
    assert "memory-no-docker-law" in block
    assert "fresh" in block
    core = format_memories(book, layer="core")
    assert "memory-samtal-wal" not in core
    maps = format_memories(book, source_kind="memory-map")
    assert "memory-commit-before-answer" not in maps
    assert "neglected" in format_verdict(book, ON)
    assert "panel-m164-boundary" not in format_panel(book, ON)
    screen = format_subconscious_screen(book)
    assert "The Subconscious v2 (M-165)" in screen
    assert PLAIN_EXPLANATION in screen
    assert USAGE in screen
    assert "memory-two-roads" in format_subconscious_screen()


def test_parse_subconscious_args_grammar():
    assert parse_subconscious_args("") == ("show", None)
    assert parse_subconscious_args("show") == ("show", None)
    assert parse_subconscious_args("memory memory-x") == (
        "memory", "memory-x")
    assert parse_subconscious_args("layer vector") == (
        "layer", "subconscious")
    assert parse_subconscious_args("source map") == (
        "source", "memory-map")
    assert parse_subconscious_args("panel") == ("panel", None)
    assert parse_subconscious_args("verdict") == ("verdict", None)
    for bad in ("memory", "layer archive", "source dream",
                "panel now", "dream", None.__class__ and 42):
        with pytest.raises(ValueError):
            parse_subconscious_args(bad)
