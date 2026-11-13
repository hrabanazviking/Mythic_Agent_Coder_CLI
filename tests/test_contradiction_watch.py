"""M-166 Contradiction watch - pure-layer tests.

TIER: integration

The pure layer is the contradiction watch, held as
data: one watch standing over one stored memory -
named by the kind of holding it stands in and the
shipped piece's id alone, the piece's own words
never crossing - carrying its provenance whole
(the stored claim in the watcher's own words, the
newer evidence in its own words, where the evidence
was read from and the day the contradiction was
found, who recorded the watch, the session it was
raised in and where the watch was read from),
composed by import from the shipped holdings it
stands over (the project memory map M-150, session
memory M-153, cross-project memory M-154, the
self-improving ledger M-155, crew memory M-133 and
the subconscious v2 M-165), each judged by its own
layer's validation, ids and refs only across the
seams. The winner is derived, never chosen: the
newer truth - the evidence - wins on every watch,
and the correction the map shows is derived from
the watch, the stored claim struck through by the
evidence that replaces it. One stored memory is
corrected once in a book, so the correction never
forks. A contradiction panel is derived from the
whole book (every watch carried whole, in a settled
order, the correction shown on every row), a
correction verdict is derived for the whole book -
a broadly overturned map is named overturned
plainly, never smoothed - the shipped example book
is held in a data file, and a loader reads a book
from any file. Nothing here sends, posts, schedules,
calls a model, persists anything or writes any live
memory: a watch corrects this layer's map only, and
the stored memory's own holding is never touched.
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
from mythic_agent.core.subconscious_v2 import load_subconscious_v2
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.contradiction_watch import (
    CONTRADICTION_WATCH_RESOURCE,
    CONTRADICTION_WATCH_SCHEMA,
    CONTRADICTION_WATCH_SLICE,
    MEMORY_KINDS,
    PLAIN_EXPLANATION,
    USAGE,
    VERDICT_WORDS,
    WINNER,
    ContradictionBook,
    ContradictionPanel,
    ContradictionRegistry,
    ContradictionWatch,
    CorrectionVerdict,
    KindCount,
    book_record,
    build_book,
    build_panel,
    build_row,
    build_verdict,
    build_watch,
    correction_line,
    derive_panel,
    derive_verdict,
    format_contradiction_screen,
    format_panel,
    format_verdict,
    format_watch,
    format_watches,
    inspect_watch_source,
    load_contradiction_watch,
    load_contradiction_watch_file,
    normalize_memory_kind,
    panel_plain_words,
    panel_record,
    parse_contradiction_args,
    plain_words,
    total_watches,
    validate_book,
    validate_panel,
    validate_row,
    validate_verdict,
    validate_watch,
    verdict_plain_words,
    verdict_record,
    watch_for,
    watch_from_crew_entry,
    watch_from_cross_project_lesson,
    watch_from_ledger_candidate,
    watch_from_map_entry,
    watch_from_session_note,
    watch_from_subconscious_memory,
    watch_record,
    watch_refs,
    winner_of,
)

ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_TITLE = "Contradiction watch at the M-165 slice boundary"

BY = "Volmarr"
ON = "2026-11-09"


def _watch(**overrides):
    fields = {
        "watch_id": "watch-test",
        "title": "the test watch, raised by hand",
        "memory_kind": "manual",
        "memory_ref": "ref-test",
        "stored_claim": "the stored words, as the watcher read them",
        "evidence_claim": "the newer words, as the evidence states them",
        "evidence_source": "the test check",
        "found_on": ON,
        "recorded_by": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_watch(fields)


def _stored_watch(watch):
    stored = watch.to_record()
    for key in ("type", "slice", "winner", "correction"):
        stored.pop(key)
    return stored


def _clean(record):
    cleaned = dict(record)
    for key in ("type", "slice"):
        cleaned.pop(key, None)
    return cleaned


# ---------------------------------------------------------------------
# The shipped example book and the roadmap.
# ---------------------------------------------------------------------


def test_shipped_book_loads_with_pinned_shape():
    book = load_contradiction_watch()
    assert book.title == EXAMPLE_TITLE
    assert book.watch_ids() == (
        "watch-verify-on-devices", "watch-kubuntu-lts",
        "watch-muse-renewal", "watch-reap-at-bank")
    assert book.total_watches == 4
    assert len(book.panels) == 1
    panel = book.panel_for("panel-m165-boundary")
    assert panel.as_of == ON
    assert panel.total_watches == 4
    assert panel.total_corrected == 4
    assert panel.distinct_memories == 4
    first = book.watches[0]
    assert first.watch_id == "watch-verify-on-devices"
    assert first.title == "verify on his devices, not the VM"
    assert book.watch_for_memory(
        "crew-fact", "crew-verify-copies").watch_id == (
            "watch-reap-at-bank")


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-166")]
    assert slice_.title == "Contradiction watch"
    assert "contradicts" in slice_.summary
    assert "newer truth wins" in slice_.summary
    assert "correction" in slice_.summary
    assert CONTRADICTION_WATCH_SLICE == "M-166"
    assert CONTRADICTION_WATCH_SCHEMA == "mythic.contradiction_watch/1"
    assert CONTRADICTION_WATCH_RESOURCE == "contradiction_watch.yaml"


def test_closed_vocabularies():
    assert MEMORY_KINDS == (
        "memory-map", "session-note", "cross-project-lesson",
        "ledger-candidate", "crew-fact", "subconscious-memory",
        "vector-record", "manual")
    assert VERDICT_WORDS == ("correcting", "contested", "overturned")
    assert WINNER == "evidence"
    assert normalize_memory_kind("MAP") == "memory-map"
    assert normalize_memory_kind("note") == "session-note"
    assert normalize_memory_kind("lesson") == "cross-project-lesson"
    assert normalize_memory_kind("ledger") == "ledger-candidate"
    assert normalize_memory_kind("crew") == "crew-fact"
    assert normalize_memory_kind("v2") == "subconscious-memory"
    assert normalize_memory_kind("vector") == "vector-record"
    assert normalize_memory_kind("by-hand") == "manual"
    with pytest.raises(ValueError):
        normalize_memory_kind("dream")


# ---------------------------------------------------------------------
# The watch record: provenance whole, judged whole.
# ---------------------------------------------------------------------


def test_watch_record_round_trips():
    watch = _watch(evidence_ref="ref-evidence")
    assert validate_watch(_stored_watch(watch)) == watch
    record = watch.to_record()
    assert record["type"] == "contradiction_watch_watch"
    assert record["slice"] == "M-166"
    assert record["winner"] == "evidence"
    assert record["evidence_ref"] == "ref-evidence"
    assert record["correction"] == correction_line(watch)


def test_watch_provenance_is_whole_and_required():
    for field in ("title", "memory_kind", "memory_ref",
                  "stored_claim", "evidence_claim", "evidence_source",
                  "found_on", "recorded_by", "source",
                  "origin_session"):
        fields = _stored_watch(_watch())
        fields.pop(field)
        with pytest.raises(ValueError):
            build_watch(fields)


def test_watch_refuses_unknown_keys_and_split_spellings():
    fields = _stored_watch(_watch())
    fields["dream"] = "x"
    with pytest.raises(ValueError):
        build_watch(fields)
    fields = _stored_watch(_watch())
    fields["winner"] = "evidence"
    with pytest.raises(ValueError):
        build_watch(fields)
    fields = _stored_watch(_watch())
    fields["claim"] = "a different stored claim"
    with pytest.raises(ValueError):
        build_watch(fields)


def test_watch_refuses_identical_claims():
    with pytest.raises(ValueError, match="contradicts nothing"):
        _watch(evidence_claim="the stored words, as the watcher "
                              "read them")
    with pytest.raises(ValueError):
        _watch(found_on="Nov 9 2026")
    with pytest.raises(ValueError):
        _watch(memory_ref="two words")


def test_watch_alias_spellings_read_onto_the_fields():
    watch = build_watch({
        "name": "an alias watch", "kind": "map", "ref": "ref-alias",
        "claim": "stored alias words", "newer": "newer alias words",
        "evidence_from": "the alias check", "day": ON, "by": BY,
        "source": "test source", "session": "session-test",
        "id": "watch-alias"})
    assert watch.memory_kind == "memory-map"
    assert watch.memory_ref == "ref-alias"
    assert watch.watch_id == "watch-alias"
    assert watch.origin_session == "session-test"


def test_winner_is_always_the_newer_truth():
    watch = _watch()
    assert winner_of(watch) == "evidence"
    line = correction_line(watch)
    assert line.startswith("the stored words")
    assert "corrected: the newer words" in line
    assert "the newer truth stands" in line
    assert "2026-11-09" in line


# ---------------------------------------------------------------------
# Composition by import: ids only across the seams.
# ---------------------------------------------------------------------


def test_watch_from_map_entry_carries_id_only():
    entry = load_project_memory_map().entries[0]
    watch = watch_from_map_entry(
        entry, stored_claim="the stored words",
        evidence_claim="the newer words",
        evidence_source="the check", found_on=ON, recorded_by=BY,
        origin_session="session-test")
    assert watch.memory_kind == "memory-map"
    assert watch.memory_ref == entry.entry_id
    assert watch.watch_id == f"watch-{entry.entry_id}"
    assert entry.detail not in watch.title
    assert entry.detail not in watch.stored_claim


def test_watch_from_session_note_and_cross_project_lesson():
    note = load_session_memory().situations[0].memory[0]
    watch = watch_from_session_note(
        note, stored_claim="the stored words",
        evidence_claim="the newer words",
        evidence_source="the check", found_on=ON, recorded_by=BY,
        origin_session="session-test")
    assert watch.memory_kind == "session-note"
    assert watch.memory_ref == note.note_id
    lesson = load_cross_project_memory().lessons[0]
    learned = watch_from_cross_project_lesson(
        lesson, stored_claim="the stored words",
        evidence_claim="the newer words",
        evidence_source="the check", found_on=ON, recorded_by=BY,
        origin_session="session-test")
    assert learned.memory_kind == "cross-project-lesson"
    assert learned.memory_ref == lesson.lesson_id


def test_watch_from_ledger_candidate_and_crew_entry():
    candidate = load_self_improving_ledger().candidates[0]
    watch = watch_from_ledger_candidate(
        candidate, stored_claim="the stored words",
        evidence_claim="the newer words",
        evidence_source="the check", found_on=ON, recorded_by=BY,
        origin_session="session-test")
    assert watch.memory_kind == "ledger-candidate"
    assert watch.memory_ref == candidate.candidate_id
    entry = load_crew_memory().notebooks[0].entries[0]
    fact = watch_from_crew_entry(
        entry, stored_claim="the stored words",
        evidence_claim="the newer words",
        evidence_source="the check", found_on=ON, recorded_by=BY,
        origin_session="session-test")
    assert fact.memory_kind == "crew-fact"
    assert fact.memory_ref == entry.entry_id
    assert entry.fact not in fact.title


def test_watch_from_subconscious_memory_carries_id_only():
    memory = load_subconscious_v2().memories[0]
    watch = watch_from_subconscious_memory(
        memory, stored_claim="the stored words",
        evidence_claim="the newer words",
        evidence_source="the check", found_on=ON, recorded_by=BY,
        origin_session="session-test")
    assert watch.memory_kind == "subconscious-memory"
    assert watch.memory_ref == memory.memory_id
    assert memory.title not in watch.title
    assert memory.title not in watch.stored_claim


def test_composition_refuses_a_piece_with_no_id():
    entry = {"section": "architecture", "title": "an unnamed entry",
             "detail": "a detail", "source": "test", "ref": "ref-x"}
    with pytest.raises(ValueError, match="with no id"):
        watch_from_map_entry(
            entry, stored_claim="the stored words",
            evidence_claim="the newer words",
            evidence_source="the check", found_on=ON, recorded_by=BY,
            origin_session="session-test")


def test_inspect_watch_source_judges_by_owning_layer():
    entry = load_project_memory_map().entries[0]
    assert inspect_watch_source(entry) == {
        "memory_kind": "memory-map", "memory_ref": entry.entry_id}
    memory = load_subconscious_v2().memories[0]
    assert inspect_watch_source(memory) == {
        "memory_kind": "subconscious-memory",
        "memory_ref": memory.memory_id}
    assert inspect_watch_source(_watch()) == {
        "memory_kind": "manual", "memory_ref": "ref-test"}
    record = {"text": "the archived words themselves",
              "vector": [0.1, 0.2, 0.3],
              "metadata": {"name": "archival-alpha"}}
    assert inspect_watch_source(record) == {
        "memory_kind": "vector-record", "memory_ref": "archival-alpha"}
    with pytest.raises(ValueError):
        inspect_watch_source(42)


# ---------------------------------------------------------------------
# The panel and the verdict: derived, judged against the book.
# ---------------------------------------------------------------------


def test_panel_is_derived_in_panel_order():
    book = load_contradiction_watch()
    panel = derive_panel(book)
    assert [r.watch_id for r in panel.rows] == [
        "watch-verify-on-devices", "watch-muse-renewal",
        "watch-reap-at-bank", "watch-kubuntu-lts"]
    assert panel.total_watches == 4
    assert panel.total_corrected == 4
    assert panel.distinct_memories == 4
    assert panel.as_of == ON
    counts = {c.kind: c.items for c in panel.kind_counts}
    assert counts == {"crew-fact": 1, "memory-map": 1,
                      "session-note": 1, "subconscious-memory": 1}
    row = panel.row_for("watch-kubuntu-lts")
    assert row.winner == "evidence"
    assert row.memory_kind == "session-note"
    stored = book.panel_for("panel-m165-boundary")
    assert validate_panel(stored, book) == stored
    assert stored.rows == panel.rows
    assert stored.account == panel.account


def test_panel_refuses_a_stored_panel_that_disagrees():
    book = load_contradiction_watch()
    panel = derive_panel(book)
    stored = _clean(panel.to_record())
    stored["rows"] = [_clean(row) for row in stored["rows"]]
    stored["rows"][0]["evidence_claim"] = "a tampered claim"
    with pytest.raises(ValueError):
        validate_panel(stored, book)
    with pytest.raises(ValueError):
        build_panel({**_clean(panel.to_record()),
                     "rows": [_clean(r) for r in
                              panel.to_record()["rows"]],
                     "total_watches": 99})


def test_panel_account_and_kind_counts_are_its_own():
    book = load_contradiction_watch()
    panel = derive_panel(book)
    assert panel.account[0].startswith(
        "The contradiction panel holds 4 watches as of 2026-11-09")
    stored = _clean(panel.to_record())
    stored["rows"] = [_clean(row) for row in stored["rows"]]
    stored["account"] = ["A foreign account of the panel."]
    with pytest.raises(ValueError, match="disagrees"):
        validate_panel(stored, book)
    one = ContradictionBook(title="a one-watch book", watches=(_watch(),))
    single = derive_panel(one)
    cleaned = _clean(single.to_record())
    cleaned["rows"] = [_clean(row) for row in cleaned["rows"]]
    with pytest.raises(ValueError):
        build_panel({**cleaned, "kind_counts": [
            {"kind": "manual", "items": 99}]})


def test_row_is_judged_against_its_watch():
    book = load_contradiction_watch()
    watch = book.watches[0]
    row = derive_panel(book).row_for(watch.watch_id)
    cleaned = _clean(row.to_record())
    assert validate_row(cleaned, watch) == row
    assert build_row(cleaned, watch) == row
    with pytest.raises(ValueError, match="disagrees"):
        validate_row({**cleaned, "evidence_claim": "tampered"}, watch)
    with pytest.raises(ValueError, match="never wins"):
        build_row({**cleaned, "winner": "stored"})


def test_verdict_bands_and_the_overturned_example():
    book = load_contradiction_watch()
    verdict = derive_verdict(book)
    assert verdict.verdict == "overturned"
    assert verdict.total_watches == 4
    assert verdict.total_corrected == 4
    assert verdict.distinct_memories == 4
    assert verdict.distinct_kinds == 4
    assert verdict.earliest_on == "2026-11-05"
    assert verdict.latest_on == "2026-11-09"
    stored_verdict = _clean(verdict.to_record())
    assert validate_verdict(stored_verdict, book) == verdict
    one = ContradictionBook(title="a one-watch book", watches=(_watch(),))
    assert derive_verdict(one).verdict == "correcting"
    two = ContradictionBook(title="a two-watch book", watches=(
        _watch(), _watch(watch_id="watch-two", memory_ref="ref-two",
                         title="a second watch")))
    assert derive_verdict(two).verdict == "contested"
    three = ContradictionBook(title="a three-watch book", watches=(
        _watch(), _watch(watch_id="watch-two", memory_ref="ref-two",
                         title="a second watch"),
        _watch(watch_id="watch-three", memory_ref="ref-three",
               title="a third watch")))
    assert derive_verdict(three).verdict == "contested"
    with pytest.raises(ValueError):
        build_verdict({**stored_verdict, "verdict": "correcting"})


def test_verdict_tallies_are_judged():
    with pytest.raises(ValueError):
        build_verdict({
            "total_watches": 1, "total_corrected": 1,
            "distinct_memories": 2, "distinct_kinds": 1,
            "earliest_on": ON, "latest_on": ON,
            "verdict": "contested"})
    with pytest.raises(ValueError):
        build_verdict({
            "total_watches": 2, "total_corrected": 2,
            "distinct_memories": 2, "distinct_kinds": 2,
            "earliest_on": "2026-11-09", "latest_on": "2026-11-01",
            "verdict": "contested"})
    with pytest.raises(ValueError):
        build_verdict({
            "total_watches": 2, "total_corrected": 1,
            "distinct_memories": 2, "distinct_kinds": 2,
            "earliest_on": "2026-11-01", "latest_on": "2026-11-09",
            "verdict": "contested"})


def test_book_laws_one_correction_per_memory():
    first = _watch()
    forked = _watch(watch_id="watch-fork", title="a forking watch")
    with pytest.raises(ValueError, match="corrected twice"):
        ContradictionBook(title="a forked book", watches=(first, forked))
    with pytest.raises(ValueError, match="already exists"):
        ContradictionBook(title="a doubled book", watches=(first, first))
    book = ContradictionBook(title="a sound book", watches=(first,))
    assert book.watch_for("watch-test") == first
    assert book.watch_for_memory("manual", "ref-test") == first
    assert total_watches(book) == 1
    assert watch_refs(book) == (("manual", "ref-test"),)
    assert watch_for(book, "manual", "ref-test") == first
    with pytest.raises(KeyError):
        book.watch_for("watch-nope")
    with pytest.raises(KeyError):
        book.watch_for_memory("manual", "ref-nope")


def test_book_file_loader_reads_any_file(tmp_path):
    book = load_contradiction_watch()
    raw = yaml.safe_load(
        (ROOT / "mythic_agent" / "data"
         / "contradiction_watch.yaml").read_text())
    raw["guide"]["title"] = "A copied contradiction book"
    path = tmp_path / "copy.yaml"
    path.write_text(yaml.safe_dump(raw))
    copied = load_contradiction_watch_file(path)
    assert copied.title == "A copied contradiction book"
    assert copied.watch_ids() == book.watch_ids()
    raw["schema"] = "mythic.other/9"
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(ValidationError):
        load_contradiction_watch_file(path)
    with pytest.raises(ValidationError):
        validate_book({"schema": CONTRADICTION_WATCH_SCHEMA})
    with pytest.raises(ValidationError):
        validate_book({**yaml.safe_load(
            (ROOT / "mythic_agent" / "data"
             / "contradiction_watch.yaml").read_text()),
            "dream": "x"})


def test_registry_holds_watches_one_by_one():
    registry = ContradictionRegistry()
    held = registry.register_watch(_watch(watch_id=None))
    assert held.watch_id == "watch-1"
    with pytest.raises(ValueError, match="corrected twice"):
        registry.register_watch(_watch(watch_id="watch-other"))
    assert registry.latest_watch() == held
    assert registry.panel().total_watches == 1
    assert registry.verdict().verdict == "correcting"
    registry.register_book(load_contradiction_watch())
    assert registry.book().total_watches == 5
    assert registry.get_watch("watch-reap-at-bank").memory_kind == (
        "crew-fact")
    assert registry.watch_for_memory(
        "manual", "ref-test").watch_id == "watch-1"
    with pytest.raises(ValueError):
        registry.register_book(load_contradiction_watch())
    with pytest.raises(KeyError):
        registry.get_watch("watch-nope")


# ---------------------------------------------------------------------
# News records, plain words, screens and the shared grammar.
# ---------------------------------------------------------------------


def test_news_records_carry_headlines():
    book = load_contradiction_watch()
    record = watch_record(book.watches[0])
    assert record["news"] is True
    assert "Correction over memory-map map-verify-on-vm" in (
        record["headline"])
    panel = panel_record(derive_panel(book), book)
    assert panel["type"] == "contradiction_watch_panel"
    assert "4 watches" in panel["headline"]
    verdict = verdict_record(derive_verdict(book), book)
    assert verdict["type"] == "contradiction_watch_verdict"
    assert "overturned" in verdict["headline"]
    assert book_record(book)["watch_count"] == 4
    assert "the newer truth wins" in plain_words(book.watches[0])
    assert "watch-kubuntu-lts" in panel_plain_words(book)
    assert "overturned" in verdict_plain_words(book)


def test_formatters_and_screen():
    book = load_contradiction_watch()
    block = format_watch(book.watches[0])
    assert "watch-verify-on-devices" in block
    assert "The map shows the correction:" in block
    crew = format_watches(book, kind="crew-fact")
    assert "watch-reap-at-bank" in crew
    assert "watch-kubuntu-lts" not in crew
    assert "watch-kubuntu-lts" in format_watches(book)
    assert "overturned" in format_verdict(book)
    assert "panel-m165-boundary" not in format_panel(book)
    assert "Panel in Contradiction watch" in format_panel(book)
    screen = format_contradiction_screen(book)
    assert "Contradiction Watch (M-166)" in screen
    assert PLAIN_EXPLANATION in screen
    assert USAGE in screen
    assert "watch-reap-at-bank" in format_contradiction_screen()


def test_parse_contradiction_args_grammar():
    assert parse_contradiction_args("") == ("show", None)
    assert parse_contradiction_args("show") == ("show", None)
    assert parse_contradiction_args("list") == ("show", None)
    assert parse_contradiction_args("watch watch-x") == (
        "watch", "watch-x")
    assert parse_contradiction_args("kind map") == (
        "kind", "memory-map")
    assert parse_contradiction_args("kind crew") == (
        "kind", "crew-fact")
    assert parse_contradiction_args("panel") == ("panel", None)
    assert parse_contradiction_args("verdict") == ("verdict", None)
    for bad in ("watch", "kind dream", "panel now", "dance",
                None.__class__ and 42):
        with pytest.raises(ValueError):
            parse_contradiction_args(bad)


# -- agent layer -----------------------------------------------------------
#
# M-166 agent layer: the agent holds a
# ContradictionRegistry for the session (session
# state only, no new setting), watches are held by
# being registered - published as their watch_record
# session news through the checkpoint road, deduped
# per shape - the report road renders the held book
# (or the shipped example when unheld) through the
# pure formatters, a composing road raises a watch
# over one of the session's own subconscious v2
# memories by import (its id alone crossing, the
# memory's own words never crossing, the memory
# itself never touched), and the /contradiction
# surface rides both roads on the pure parser +
# formatters. Status, get, panel, verdict and report
# reads register and publish nothing, answer from
# the held registry first and from the shipped
# example only while nothing is held - a held watch
# never falls back to the example. The panel and the
# verdict derive at call time from the whole book,
# never held. This layer sends nothing, posts
# nothing, schedules nothing, calls no model,
# persists nothing beyond the session journal news
# and writes no live memory - a watch corrects this
# layer's map only, and there is no Part VIII board
# yet, so the screen is where the book is visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _contradiction_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _book(watches=None, **overrides):
    fields = {
        "title": "A test contradiction book",
        "watches": [_stored_watch(item) for item in (
            watches if watches is not None else [_watch()])],
    }
    fields.update(overrides)
    return build_book(fields)


def _write_contradiction_book(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "contradiction_watch.yaml").read_text(encoding="utf-8")
    path = tmp_path / "contradiction_watch.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestContradictionAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.contradiction_status()
        assert status["watches"] == []
        assert status["book"] is None
        assert status["contradiction"]["title"] == EXAMPLE_TITLE
        assert len(status["contradiction"]["watches"]) == 4
        assert status["panel"]["total_watches"] == 4
        assert status["panel"]["total_corrected"] == 4
        assert status["panels"][0]["panel_id"] == "panel-m165-boundary"
        assert status["book_record"]["watch_count"] == 4
        assert status["verdict"]["verdict"] == "overturned"
        assert status["verdict"]["distinct_kinds"] == 4
        assert "crew-verify-copies" in status["plain_words"]
        assert "overturned" in status["verdict_plain_words"]
        assert "Contradiction Watch (M-166)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._contradiction_registry()
        assert agent._contradiction_registry() is first
        assert agent._contradiction_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.contradiction_status()
        agent.get_contradiction_watch("watch-reap-at-bank")
        agent.watch_for_memory("crew-fact", "crew-verify-copies")
        agent.contradiction_panel()
        agent.contradiction_verdict()
        agent.report_contradiction()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("contradiction_watch")] == []
        with pytest.raises(KeyError):
            agent.get_contradiction_watch("watch-nope")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_contradiction_watch(_watch())
        status = agent.contradiction_status()
        assert [item["watch_id"] for item in status["watches"]] == [
            "watch-test"]
        assert status["book"]["title"] == "Contradiction watch"
        assert status["panel"]["total_watches"] == 1
        assert status["verdict"]["verdict"] == "correcting"

    def test_held_watch_never_falls_back_to_the_example(
            self, agent):
        agent.register_contradiction_watch(_watch())
        with pytest.raises(KeyError):
            agent.get_contradiction_watch("watch-reap-at-bank")
        watch = agent.get_contradiction_watch("watch-test")
        assert watch.title == "the test watch, raised by hand"
        assert agent.watch_for_memory(
            "manual", "ref-test").watch_id == "watch-test"
        assert agent.contradiction_book().title == (
            "Contradiction watch")


class TestContradictionAgentHolding:
    def test_register_watch_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_contradiction_watch(_watch())
        assert outcome["watch"]["watch_id"] == "watch-test"
        assert outcome["record_news"]["type"] == (
            "contradiction_watch_watch")
        events = _contradiction_events(
            store, session_id, "contradiction_watch_watch")
        assert len(events) == 1
        assert events[0]["watch_id"] == "watch-test"
        agent._publish_contradiction_record(outcome["record_news"])
        assert len(_contradiction_events(
            store, session_id, "contradiction_watch_watch")) == 1
        agent._publish_contradiction_record(
            {"type": "mentions_mention", "mention_id": "mention-x"})
        agent._publish_contradiction_record(
            book_record(load_contradiction_watch()))
        for kind in ("mentions_mention", "contradiction_watch_book"):
            assert _contradiction_events(store, session_id, kind) == []
        agent.close()

    def test_duplicate_watch_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_contradiction_watch(_watch())
        with pytest.raises(ValueError):
            agent.register_contradiction_watch(_watch())
        with pytest.raises(ValueError, match="corrected twice"):
            agent.register_contradiction_watch(_watch(
                watch_id="watch-copy"))
        assert len(_contradiction_events(
            store, session_id, "contradiction_watch_watch")) == 1
        agent.close()

    def test_watch_subconscious_memory_raises_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        memory_before = agent.get_subconscious_memory(
            "memory-no-docker-law")
        outcome = agent.watch_subconscious_memory(
            "memory-no-docker-law",
            stored_claim="models are verified in VM-local copies",
            evidence_claim="verification runs on his devices first",
            evidence_source="the verify-on-devices ruling",
            found_on=ON, recorded_by=BY,
            origin_session="session-test")
        assert outcome["watch"]["memory_kind"] == (
            "subconscious-memory")
        assert outcome["watch"]["memory_ref"] == (
            "memory-no-docker-law")
        assert outcome["watch"]["watch_id"] == (
            "watch-memory-no-docker-law")
        assert outcome["record_news"]["type"] == (
            "contradiction_watch_watch")
        assert outcome["panel_record"]["type"] == (
            "contradiction_watch_panel")
        assert outcome["verdict_record"]["type"] == (
            "contradiction_watch_verdict")
        for kind in ("contradiction_watch_watch",
                     "contradiction_watch_panel",
                     "contradiction_watch_verdict"):
            assert len(_contradiction_events(
                store, session_id, kind)) == 1
        # The watched memory stands exactly as it stood.
        assert agent.get_subconscious_memory(
            "memory-no-docker-law") == memory_before
        with pytest.raises(ValueError, match="corrected twice"):
            agent.watch_subconscious_memory(
                "memory-no-docker-law",
                stored_claim="models are verified in VM-local copies",
                evidence_claim="verification runs on his devices", watch_id="watch-again",
                evidence_source="the verify-on-devices ruling",
                found_on=ON, recorded_by=BY,
                origin_session="session-test")
        agent.close()

    def test_watch_subconscious_memory_unknown_id_raises(
            self, agent):
        with pytest.raises(KeyError):
            agent.watch_subconscious_memory(
                "memory-nope",
                stored_claim="a stored claim",
                evidence_claim="a newer claim",
                evidence_source="the check",
                found_on=ON, recorded_by=BY,
                origin_session="session-test")
        assert agent.contradiction_status()["watches"] == []

    def test_register_book_holds_and_publishes_in_order(
            self, agent):
        book = _book()
        outcome = agent.register_contradiction_book(book)
        assert outcome["count"] == 1
        assert [item["type"] for item in outcome["records_news"]] == [
            "contradiction_watch_watch"]
        assert outcome["panel_record"]["type"] == (
            "contradiction_watch_panel")
        assert agent.contradiction_book().title == (
            "A test contradiction book")
        with pytest.raises(ValueError):
            agent.register_contradiction_book(book)
        with pytest.raises(ValueError, match="different title"):
            agent.register_contradiction_book(_book(
                title="Another title",
                watches=[_watch(
                    watch_id="watch-other",
                    memory_ref="ref-other")]))
        broken = {"title": "A broken book",
                  "watches": [{"watch_id": "watch-x"}]}
        with pytest.raises(ValueError, match="missing its"):
            agent.register_contradiction_book(broken)
        assert [item["watch_id"] for item in
                agent.contradiction_status()["watches"]] == [
            "watch-test"]

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_contradiction_book()
        assert outcome["count"] == 4
        assert outcome["book"]["title"] == EXAMPLE_TITLE
        assert len(_contradiction_events(
            store, session_id, "contradiction_watch_watch")) == 4
        assert len(_contradiction_events(
            store, session_id, "contradiction_watch_panel")) == 1
        assert agent.contradiction_book().panels[0].panel_id == (
            "panel-m165-boundary")
        with pytest.raises(ValueError, match="already recorded"):
            agent.record_contradiction_book()
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_contradiction_book(tmp_path)
        book = load_contradiction_watch_file(path)
        outcome = agent.record_contradiction_book(book)
        assert outcome["count"] == 4
        assert agent.get_contradiction_watch(
            "watch-kubuntu-lts").memory_kind == "session-note"

    def test_report_renders_the_example_when_unheld(self, agent):
        report = agent.report_contradiction()
        assert report["book"]["watch_count"] == 4
        assert "watch-reap-at-bank" in report["watches_text"]
        assert "Panel in Contradiction watch" in (
            report["panel_text"])
        assert "overturned" in report["verdict_text"]
        assert "watch-verify-on-devices" in report["watches_text"]

    def test_report_renders_the_held_book_only(self, agent):
        agent.register_contradiction_watch(_watch())
        report = agent.report_contradiction()
        assert report["book"]["title"] == "Contradiction watch"
        assert "watch-reap-at-bank" not in report["watches_text"]
        assert "watch-test" in report["watches_text"]
        assert "correcting" in report["verdict_text"]

    def test_holding_writes_no_live_memory(
            self, agent, tmp_path):
        # HONEST BOUNDARY: holding a watch writes no
        # live memory - the session's own subconscious
        # and memory-map holdings stand exactly as they
        # stood, the watched memory is never edited,
        # and there is no road here that applies a
        # correction into any stored memory.
        assert not hasattr(agent, "apply_contradiction_watch")
        assert not hasattr(agent, "apply_contradiction")
        assert not hasattr(agent, "run_contradiction")
        assert not hasattr(agent, "persist_contradiction")
        assert not hasattr(agent, "contradiction_board")
        assert not hasattr(agent, "send_contradiction_watch")
        assert not hasattr(agent, "post_contradiction_watch")
        assert not hasattr(agent, "schedule_contradiction_watch")
        assert not hasattr(agent, "overwrite_stored_memory")
        map_before = agent.project_memory_map_book()
        subconscious_before = agent.subconscious_book()
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
        agent.register_contradiction_watch(_watch())
        agent.watch_subconscious_memory(
            "memory-no-docker-law",
            stored_claim="models are verified in VM-local copies",
            evidence_claim="verification runs on his devices first",
            evidence_source="the verify-on-devices ruling",
            found_on=ON, recorded_by=BY,
            origin_session="session-test")
        assert agent.project_memory_map_book().entry_ids() == (
            map_before.entry_ids())
        assert agent.subconscious_book().memory_ids() == (
            subconscious_before.memory_ids())
        assert agent.get_subconscious_memory(
            "memory-no-docker-law").title == (
                subconscious_before.memories[0].title)
        assert builder.build() == built_before
        assert {
            p.name: p.read_bytes()
            for p in tmp_path.glob("*.py")} == before


class TestContradictionTerminalSurface:
    def test_show_watch_kind_panel_verdict(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/contradiction")
        assert "Contradiction Watch (M-166)" in text
        _, _, text = _slash(
            agent, "/contradiction watch watch-verify-on-devices")
        assert "verify on his devices" in text
        _, _, text = _slash(agent, "/contradiction kind crew-fact")
        assert "watch-reap-at-bank" in text
        assert "watch-kubuntu-lts" not in text
        _, _, text = _slash(agent, "/contradiction panel")
        assert "Panel in Contradiction watch" in text
        _, _, text = _slash(agent, "/contradiction verdict")
        assert "overturned" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/contradiction [show|watch <watch-id>"
                "|kind <memory-kind>|panel|verdict]") in text
        _, _, text = _slash(agent, "/contradiction dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/contradiction watch watch-nope")
        assert "no watch in the book" in text


@pytest.fixture()
def contradiction_handler(agent, monkeypatch):
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


def _contradiction_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestContradictionCommand:
    def test_show_is_default(self, contradiction_handler, agent):
        contradiction_handler._handle_contradiction("")
        assert "Contradiction Watch (M-166)" in (
            _contradiction_published_text(contradiction_handler))

    def test_watch_kind_panel_verdict(
            self, contradiction_handler, agent):
        contradiction_handler._handle_contradiction(
            "watch watch-verify-on-devices")
        assert "watch-verify-on-devices" in (
            _contradiction_published_text(contradiction_handler))
        contradiction_handler._handle_contradiction("kind crew-fact")
        assert "watch-reap-at-bank" in _contradiction_published_text(
            contradiction_handler)
        contradiction_handler._handle_contradiction("panel")
        assert "Panel in Contradiction watch" in (
            _contradiction_published_text(contradiction_handler))
        contradiction_handler._handle_contradiction("verdict")
        assert "overturned" in _contradiction_published_text(
            contradiction_handler)

    def test_bad_grammar_is_published(
            self, contradiction_handler, agent):
        contradiction_handler._handle_contradiction("dance party")
        assert USAGE in _contradiction_published_text(
            contradiction_handler)
        contradiction_handler._handle_contradiction("watch watch-nope")
        assert "no watch in the book" in _contradiction_published_text(
            contradiction_handler)


class TestChatScreenRoutingContradiction:
    def test_contradiction_routes_as_system_command(self, monkeypatch):
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
            "/contradiction kind crew-fact", _FakeLog())
        assert calls == [("/contradiction", "kind crew-fact")]
