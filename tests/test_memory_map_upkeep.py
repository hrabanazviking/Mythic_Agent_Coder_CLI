"""M-211 Question Law - pure-layer tests.

TIER: integration

The pure layer is the scribe, held as data: one
record per upkeep, held whole - the slice it
answers for, named by slice id, its title, the
steps it walked in walk order and the evidence
it carries, held by kind. The question walk is
explicit - named, noted, mapped, checked,
sealed, with their legal steps held as data -
and a upkeep's standing is derived at call
time: a upkeep that opens anywhere but banked, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet reached sealed stands open,
named in its gaps. A upkeep stands only for
an active slice: a upkeep naming no held
slice, or one that is not active, refuses by
name. The upkeep's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, board, trace, order and current
upkeep are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, checked or
sealed live. The shipped example book is held
in a data file, and a loader reads a book from
any file. No charter row names this slice: the
M-171 TUI charter binds Part VIII alone, and the
M-005 method charter names the whole of Part IX
as the part that executes it, both pinned live
below.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.memory_map_upkeep import (
    EXAMPLE_CHECK,
    BARE_CLAIMS,
    HELD_EVIDENCE,
    INDEX_ACTION,
    CHECKS,
    CLAIM_KINDS,
    TRANSITIONS,
    SLICE_STATES,
    CHECK_FIELDS,
    PLAIN_EXPLANATION,
    UPKEEP_RESOURCE,
    UPKEEP_RULE,
    UPKEEP_SCHEMA,
    UPKEEP_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    UpkeepRecord,
    IndexEntry,
    SliceRef,
    NoteRecord,
    UpkeepBook,
    UpkeepIndex,
    UpkeepPanel,
    UpkeepRegistry,
    UpkeepVerdict,
    UpkeepView,
    trace_for_upkeep,
    board_record,
    book_record,
    build_trace,
    build_book,
    build_upkeep,
    build_slice_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_upkeep,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    upkeep_for_check,
    upkeep_gaps,
    upkeep_order,
    upkeep_record,
    upkeep_green,
    upkeeps_for_slice,
    first_note,
    format_book,
    format_upkeep,
    format_index,
    format_note,
    format_check,
    format_panel,
    format_upkeep_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    slice_record,
    load_upkeep,
    legal_step,
    load_upkeep_file,
    next_check,
    normalize_check,
    normalize_claim_kind,
    normalize_slice_state,
    normalize_stance,
    normalize_view_filter,
    note_for_upkeep,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_upkeep_args,
    green_upkeeps,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_upkeeps,
    validate_book,
    validate_upkeep,
    validate_note,
    validate_panel,
    validate_row,
    validate_verdict,
    validate_view,
    verdict_plain_words,
    verdict_record,
    view_plain_words,
    view_record,
)
from mythic_agent.core.method_charter import (
    load_charter as load_method_charter,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.tui_redesign_charter import load_charter

ROOT = Path(__file__).resolve().parents[1]
ON = "2026-11-10"
BY = "the coordinator"
EXAMPLE_TITLE = "The memory-map upkeep at the M-210 slice boundary"
EXAMPLE_CHECKS = ["sealed", "sealed", "sealed"]
EXAMPLE_RUN_IDS = (
    "upkeep-held-update", "upkeep-rechecked-update",
    "upkeep-own-update", "upkeep-bare-update",
    "upkeep-leaping-update")
EXAMPLE_TRACE = "banked > noted > mapped > checked > sealed"


def _ref(**overrides):
    fields = {
        "slice_id": "slice-test",
        "seq": 1,
        "title": "A test slice",
        "state": "active",
        "detail": "A test slice reference held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "upkeep-test",
    }
    fields.update(overrides)
    return build_slice_ref(fields)


def _upkeep(**overrides):
    fields = {
        "upkeep_id": "upkeep-test",
        "seq": 1,
        "slice_id": "slice-test",
        "title": "A test upkeep",
        "checks": ["banked", "noted", "mapped", "checked", "sealed"],
        "claims": [],
        "detail": "A test upkeep held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "upkeep-test",
    }
    fields.update(overrides)
    return build_upkeep(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "upkeep-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "upkeep_id": "upkeep-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "upkeep-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "upkeep_id": "upkeep-test",
        "trace": "banked > noted > mapped > checked > sealed",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "upkeep-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(slices=None, upkeeps=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": UPKEEP_SCHEMA,
        "slice": "M-211",
        "memory_map_upkeep": {"title": "A test upkeep book"},
        "slices": [item.to_record() for item in (
            slices if slices is not None else [_ref()])],
        "upkeeps": [item.to_record() for item in (
            upkeeps if upkeeps is not None else [_upkeep()])],
        "views": [item.to_record() for item in (
            views if views is not None else [_view()])],
        "notes": [item.to_record() for item in (notes or [])],
        "traces": [item.to_record() for item in (
            traces or [])],
        "panels": [],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(upkeeps=[
        _upkeep(),
        _upkeep(upkeep_id="upkeep-hidden", seq=2,
               title="A hidden upkeep", checks=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_upkeep()
    assert book.title == EXAMPLE_TITLE
    assert book.upkeep_ids() == EXAMPLE_RUN_IDS
    assert book.slice_ids() == (
        "slice-m210-scope", "slice-m211-memory",
        "slice-m212-bugrule")
    assert [v.view_id for v in book.views] == [
        "view-upkeeps", "view-sealed"]
    assert [m.upkeep_id for m in book.notes] == [
        "upkeep-held-update", "upkeep-bare-update"]
    assert [a.upkeep_id for a in book.traces] == ["upkeep-held-update"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m210-boundary"
    assert panel.as_of == "2026-11-10"
    assert [row.item_id for row in panel.rows] == list(book.upkeep_ids())
    derived = derive_panel(book, "view-upkeeps")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-upkeeps").verdict == "held"
    assert derive_verdict(book, "view-upkeeps").green_shown == 3
    assert derive_verdict(book, "view-sealed").verdict == "sealed"
    assert derive_verdict(book, "view-sealed").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / UPKEEP_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == UPKEEP_SCHEMA
    assert raw["slice"] == "M-211"
    assert "verdict" not in raw
    assert "upkeep_index" not in raw
    assert "board" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-211")]
    assert slice_.title == "Memory-map upkeep"
    assert slice_.part == 9
    assert "the Scribe updates the Project Memory Map" in slice_.summary
    assert "in the same session as each banked slice" in slice_.summary
    assert "the map is never a later chore" in slice_.summary
    assert UPKEEP_SLICE == "M-211"

def test_charter_rows_do_not_name_m211():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-211" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert COMPLETE_WORDS == ("complete", "open")
    assert CHECK_FIELDS == ("checks", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "complete", "open")
    assert VERDICT_WORDS == ("sealed", "held", "blocked")
    assert SLICE_STATES == ("active", "queued")
    assert CHECKS == ("banked", "noted", "mapped", "checked", "sealed")
    assert HELD_EVIDENCE == ("slice_ref", "map_ref", "entry_record", "ledger_row")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["checked"] == ("banked", "sealed")
    assert TRANSITIONS["sealed"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_CHECK == "sealed"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_slice_state("ACTIVE") == "active"
    assert normalize_check("MAPPED") == "mapped"
    assert normalize_claim_kind("FEELING") == "feeling"
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    with pytest.raises(ValueError):
        normalize_slice_state("blessed")
    with pytest.raises(ValueError):
        normalize_check("polish")
    with pytest.raises(ValueError):
        normalize_claim_kind("weather")
    assert legal_step("mapped", "checked") is True
    assert legal_step("noted", "sealed") is False
    assert legal_step("sealed", "banked") is False
    assert next_check("banked") == "noted"
    assert next_check("mapped") == "checked"
    assert next_check("checked", failed=True) == "banked"
    assert next_check("checked") == "sealed"
    assert next_check("sealed") is None
    assert "held as data alone" in UPKEEP_RULE
    assert "upkeep sequence" in UPKEEP_RULE
    assert "M-211" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /mapupkeep")

def test_shipped_book_judged_honestly_as_data():
    book = load_upkeep()
    opening = book.upkeep_for("upkeep-held-update")
    assert upkeep_green(opening, book) is True
    assert upkeep_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Upkeep: The held update",
        "Slice: slice-m210-scope",
        "Check: sealed",
        "Claims: slice_ref")
    asking = book.upkeep_for("upkeep-bare-update")
    assert upkeep_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert upkeep_green(asking, book) is False
    skipping = book.upkeep_for("upkeep-leaping-update")
    assert upkeep_gaps(skipping, book) == (
        "steps from noted to sealed, which the upkeep sequence "
        "does not allow",)
    assert [g.upkeep_id for g in green_upkeeps(book)] == [
        "upkeep-held-update", "upkeep-rechecked-update", "upkeep-own-update"]
    index = derive_index(book)
    assert [e.check for e in index.entries] == EXAMPLE_CHECKS
    assert index.gaps == ("upkeep-bare-update", "upkeep-leaping-update")
    assert upkeep_for_check(book, EXAMPLE_CHECK).upkeep_id == (
        "upkeep-held-update")
    assert upkeep_for_check(book, "triple resume") is None
    assert transition_breaks(book) == (
        "upkeep-leaping-update: noted > sealed",)
    assert [g.upkeep_id for g in upkeep_order(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "upkeep-held-update") == EXAMPLE_TRACE
    assert trace_current(book, "upkeep-held-update") is True
    assert trace_current(book, "upkeep-rechecked-update") is False
    assert trace_for_upkeep(
        book, "upkeep-held-update").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_upkeep(
        book, "upkeep-held-update", "note").note_id == (
            "note-note-first")
    assert note_for_upkeep(book, "upkeep-nope") is None
    assert current_upkeep(book).upkeep_id == "upkeep-bare-update"
    board = board_record(book)
    assert board["standings"] == [
        {"standing": "complete", "upkeeps": 3},
        {"standing": "open", "upkeeps": 2}]
    assert board["total"] == 5
    assert board["current_upkeep"] == "upkeep-bare-update"
    assert board["traces"] == [
        {"upkeep_id": "upkeep-held-update", "trace": "current"},
        {"upkeep_id": "upkeep-rechecked-update", "trace": "unheld"},
        {"upkeep_id": "upkeep-own-update", "trace": "unheld"},
        {"upkeep_id": "upkeep-bare-update", "trace": "unheld"},
        {"upkeep_id": "upkeep-leaping-update", "trace": "unheld"}]
    assert board["breaks"] == ["upkeep-leaping-update: noted > sealed"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 253
    assert citizen["next_slice"] == "M-254"
    assert citizen["m211_title"] == "Memory-map upkeep"
    assert citizen["m211_part"] == 9
    assert citizen["m211_status"] == "done"

def test_upkeep_record_round_trips():
    upkeep = _upkeep()
    assert validate_upkeep(upkeep) is upkeep
    rebuilt = build_upkeep(upkeep.to_record())
    assert rebuilt == upkeep
    assert rebuilt.item_id == "upkeep-test"
    assert rebuilt.check == "sealed"
    record = upkeep_record(upkeep)
    assert record["type"] == "upkeep_upkeep"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert slice_record(ref)["type"] == "upkeep_slice"
    assert slice_record(ref)["state"] == "active"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _upkeep(checks=[])
    assert upkeep_gaps(silent) == (
        "has passed through no step: the upkeep has not started",)
    assert upkeep_green(silent) is False
    walking = _upkeep(checks=["banked", "noted"])
    assert upkeep_gaps(walking) == (
        "has not reached sealed: the upkeep stands at noted",)
    assert walking.check == "noted"
    sideways = _upkeep(checks=["noted", "mapped", "checked", "sealed"])
    assert upkeep_gaps(sideways) == (
        "opens at noted, not at banked: the upkeep opens "
        "with the question",)
    repaired = _upkeep(checks=["banked", "noted", "mapped", "checked", "banked", "noted", "mapped", "checked", "sealed"])
    assert upkeep_gaps(repaired) == ()
    assert upkeep_green(repaired) is True
    with pytest.raises(ValueError):
        _upkeep(checks=[42])
    with pytest.raises(ValueError):
        _upkeep(checks="inspect as a bare string")
    with pytest.raises(ValueError):
        _upkeep(checks=["banked", "polish"])
    with pytest.raises(ValueError):
        _upkeep(claims=["weather"])
    with pytest.raises(ValueError):
        _upkeep(claims="slice_ref")
    none_upkeep = _upkeep(checks=None, claims=None)
    assert none_upkeep.checks == ()
    assert none_upkeep.claims == ()

def test_upkeep_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "entries", "coverage", "current_upkeep",
                "board", "order"):
        fields = _upkeep().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_upkeep(fields)
    fields = _upkeep().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_upkeep(fields)


def test_upkeep_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _upkeep().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_upkeep(fields)


def test_upkeep_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _upkeep(title="")
    with pytest.raises(ValueError):
        _upkeep(slice_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "banked > noted > mapped > checked > sealed"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_upkeeps_own_fields():
    upkeep = _upkeep(claims=["slice_ref"])
    assert plain_lines(upkeep) == (
        "Upkeep: A test upkeep",
        "Slice: slice-test",
        "Check: sealed",
        "Claims: slice_ref")
    segment = segment_of(upkeep)
    assert segment.startswith("upkeep-test: A test upkeep")
    assert "check: 'sealed'" in segment
    assert "gaps: none" in segment
    assert plain_words(upkeep).startswith(
        "A test upkeep - from slice-test")

def test_red_upkeeps_stand_named_in_their_gaps():
    asking = _upkeep(claims=["feeling", "slice_ref", "summary"])
    assert upkeep_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert upkeep_green(asking) is False
    skipping = _upkeep(checks=["banked", "noted", "sealed"])
    assert upkeep_gaps(skipping) == (
        "steps from noted to sealed, which the upkeep sequence "
        "does not allow",)
    book = _book(upkeeps=[
        _upkeep(),
        _upkeep(upkeep_id="upkeep-skipping", seq=2,
             checks=["banked", "noted", "sealed"]),
    ])
    assert transition_breaks(book) == (
        "upkeep-skipping: noted > sealed",)
    assert current_upkeep(book).upkeep_id == "upkeep-skipping"
    assert [g.upkeep_id for g in upkeep_order(book)] == [
        "upkeep-test", "upkeep-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "upkeep_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "upkeep_note"
    assert record["upkeep_id"] == "upkeep-test"
    assert view_plain_words(view) == "View view-test: shows all upkeeps."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_upkeeps_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.check for e in index.entries] == ["sealed"]
    assert index.entries[0] == IndexEntry(
        check="sealed",
        upkeep_id="upkeep-test", title="A test upkeep")
    assert index.gaps == ("upkeep-hidden",)
    record = index_record(book)
    assert record["type"] == "upkeep_index"
    assert record["gaps"] == ["upkeep-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "upkeep_book"

def test_check_target_reaches_its_upkeep_and_an_unheld_target_reaches_nothing():
    book = load_upkeep()
    assert upkeep_for_check(book, "sealed").upkeep_id == (
        "upkeep-held-update")
    assert upkeep_for_check(book, "") is None
    assert upkeep_for_check(book, None) is None
    assert upkeep_for_check(book, "not held at all") is None
    text = format_check(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_upkeep()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Upkeep note note upkeep-held-update" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").upkeep_id == "upkeep-test"
    assert note_for_upkeep(book, "upkeep-test").note_id == "note-test"
    assert note_for_upkeep(book, "upkeep-test", "praise") is None
    with pytest.raises(KeyError):
        book.note_for("note-nope")
    with pytest.raises(ValueError):
        _book(notes=[_note(), _note(note_id="note-two", seq=2)])


def test_panel_is_derived_and_a_stored_panel_must_agree():
    book = _mixed_book()
    panel = derive_panel(book)
    assert panel.panel_id == "panel-view-test"
    assert panel.total_items == 2
    assert panel.total_shown == 2
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 1, "open": 1}
    assert validate_panel(panel, book) is panel
    assert build_panel(panel.to_record(), book) == panel
    row = build_row(None, _upkeep(), book)
    assert row.standing == "complete"
    assert validate_row(row, _upkeep(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_upkeeps():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "upkeep_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "sealed"
    empty_book = _book(upkeeps=[_upkeep(checks=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(UpkeepVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_upkeep()
    assert [g.upkeep_id for g in shown_upkeeps(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.upkeep_id for g in shown_upkeeps(book, "view-sealed")] == [
        "upkeep-held-update", "upkeep-rechecked-update", "upkeep-own-update"]
    assert [g.upkeep_id for g in upkeeps_for_slice(
        book, "slice-m211-memory")] == [
            "upkeep-own-update", "upkeep-bare-update",
            "upkeep-leaping-update"]
    assert upkeeps_for_slice(book, "slice-nope") == ()
    assert current_upkeep(_mixed_book()).upkeep_id == "upkeep-hidden"
    assert current_upkeep(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "upkeep-test") == (
        "banked > noted > mapped > checked > sealed")
    assert trace_current(stale, "upkeep-test") is False
    assert board_record(stale)["traces"] == [
        {"upkeep_id": "upkeep-test", "trace": "stale"}]

def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(upkeeps=[_upkeep(), _upkeep(seq=2)])
    with pytest.raises(ValueError):
        _book(upkeeps=[_upkeep(), _upkeep(upkeep_id="upkeep-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(upkeeps=[_upkeep(slice_id="slice-nope")])
    with pytest.raises(ValueError):
        _book(slices=[_ref(), _ref(
            slice_id="slice-cold", seq=2, state="queued")],
            upkeeps=[_upkeep(slice_id="slice-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(slice_id="slice-nope")])
    fields = {
        "schema": UPKEEP_SCHEMA, "slice": "M-211",
        "memory_map_upkeep": {"title": "A mapped book"},
        "slices": [_ref().to_record()],
        "upkeeps": [_upkeep().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "sealed"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_upkeep"] = "upkeep-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_upkeep")
    fields["trace"] = "upkeep-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / UPKEEP_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "memory_map_upkeep.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_upkeep_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.upkeep_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = UpkeepRegistry()
    assert registry.title() is None
    registry.register_slice_ref(_ref())
    registry.register_upkeep(_upkeep())
    registry.register_view(_view())
    assert [g.upkeep_id for g in registry.list_upkeeps()] == ["upkeep-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_upkeep("upkeep-test").title == "A test upkeep"
    assert registry.get_slice("slice-test").state == "active"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("upkeep-test").upkeep_id == "upkeep-test"
    with pytest.raises(ValueError):
        registry.register_upkeep(_upkeep(seq=9))
    with pytest.raises(ValueError):
        registry.register_upkeep(_upkeep(upkeep_id="upkeep-two"))
    with pytest.raises(KeyError):
        registry.get_upkeep("upkeep-nope")
    assert registry.book().title == "An unheld upkeep book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = UpkeepRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test upkeep book"
    assert registry.title() == "A test upkeep book"
    assert len(registry.list_upkeeps()) == 2
    other = UpkeepRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    upkeep = _upkeep()
    assert "A test upkeep" in plain_words(upkeep)
    assert panel_plain_words(_mixed_book()).startswith(
        "The upkeep book holds 2 upkeeps")
    assert verdict_plain_words(_mixed_book()) == (
        "The upkeeps stand held: 1 of 2 shown upkeeps stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green upkeeps; red, "
        "named in its gaps: upkeep-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_upkeep(upkeep)
    assert "Upkeep: A test upkeep" in text
    assert "stands complete" in text
    text = format_upkeep(_upkeep(checks=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Memory Gate (M-211) - A test upkeep book" in book_text
    assert "upkeep-hidden" in format_book(_mixed_book(), "slice-test")
    assert "Upkeep panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "sealed - A test upkeep (upkeep-test)" in index_text
    assert "upkeep-hidden" in index_text
    screen = format_upkeep_screen()
    assert "The Memory Gate (M-211)" in screen
    assert "upkeep-bare-update" in screen

def test_parse_args_board_and_loader_targets():
    assert parse_upkeep_args("") == ("show", None)
    assert parse_upkeep_args(None) == ("show", None)
    assert parse_upkeep_args("show") == ("show", None)
    assert parse_upkeep_args("upkeep upkeep-test") == (
        "upkeep", "upkeep-test")
    assert parse_upkeep_args("check sealed") == (
        "check", "sealed")
    assert parse_upkeep_args("slice slice-test") == (
        "slice", "slice-test")
    assert parse_upkeep_args("view view-test") == ("view", "view-test")
    assert parse_upkeep_args("note note-test") == ("note", "note-test")
    assert parse_upkeep_args("index") == ("index", None)
    assert parse_upkeep_args("panel") == ("panel", None)
    assert parse_upkeep_args("verdict") == ("verdict", None)
    for bad in ("dance", "upkeep", "check", "slice", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_upkeep_args(bad)
    board = board_record()
    assert board["type"] == "upkeep_board"
    assert board["total"] == 5
    assert board["current_upkeep"] == "upkeep-bare-update"
    book = load_upkeep({
        "schema": UPKEEP_SCHEMA, "slice": "M-211",
        "memory_map_upkeep": {"title": "A mapped book"},
        "slices": [_ref().to_record()],
        "upkeeps": [_upkeep().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, UpkeepBook)
    assert book.title == "A mapped book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_upkeep({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_upkeep({"slice": "M-999"})
    built = build_upkeep(
        upkeep_id="upkeep-kw", seq=3, slice_id="slice-test",
        title="Kw Upkeep", checks=["banked", "noted", "mapped", "checked", "sealed"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="upkeep-test")
    assert built.upkeep_id == "upkeep-kw"
    assert upkeep_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-211 agent layer: the agent holds a upkeep
# book for the session, upkeeps and views are
# published as session news through the
# checkpoint target (journal first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held upkeeps, the board is derived from
# the held upkeeps' completeness, the roadmap standing
# is read from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no slice. This layer upkeeps
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_UPKEEP_EVENT_TYPES = (
    "upkeep_upkeep", "upkeep_slice", "upkeep_view",
    "upkeep_panel", "upkeep_verdict")


def _upkeep_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_upkeep_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / UPKEEP_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "memory_map_upkeep.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestUpkeepAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.upkeep_status()
        assert status["upkeeps"] == []
        assert status["slices"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["upkeep_book"]["title"] == EXAMPLE_TITLE
        assert len(status["upkeep_book"]["slices"]) == 3
        assert len(status["upkeep_book"]["upkeeps"]) == 5
        assert len(status["upkeep_book"]["views"]) == 2
        assert len(status["upkeep_book"]["notes"]) == 2
        assert len(status["upkeep_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m210-boundary"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["check"] for e in status["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert status["index"]["gaps"] == [
            "upkeep-bare-update", "upkeep-leaping-update"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["board"]["total"] == 5
        assert status["board"]["current_upkeep"] == "upkeep-bare-update"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 253
        assert status["roadmap"]["next_slice"] == "M-254"
        assert status["roadmap"]["m211_title"] == "Memory-map upkeep"
        assert "held as data alone" in status["rule"]
        assert "upkeep-bare-update" in status["plain_words"]
        assert "The Memory Gate (M-211)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._upkeep_registry()
        assert agent._upkeep_registry() is first
        assert agent._upkeep_store is first
        for name in ("upkeep_book", "upkeep_status", "upkeep_panel",
                     "upkeep_verdict", "upkeep_index", "report_upkeep"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_upkeep_registry", "upkeep_book", "upkeep_status",
            "get_upkeep_upkeep", "get_upkeep_view", "get_upkeep_note",
            "upkeep_upkeeps_for_slice", "upkeep_upkeeps_green",
            "upkeep_panel", "upkeep_verdict", "upkeep_index",
            "register_upkeep_upkeep", "register_upkeep_view",
            "view_upkeep", "register_upkeep_book",
            "record_upkeep_book", "report_upkeep",
            "_publish_upkeep_record", "_upkeep_screen",
            "_upkeep_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.upkeep_status()
        assert agent.get_upkeep_upkeep(
            "upkeep-held-update").title == "The held update"
        assert agent.get_upkeep_view(
            "view-upkeeps").view_filter == "all"
        assert agent.get_upkeep_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.upkeep_id for d in agent.upkeep_upkeeps_for_slice(
            "slice-m211-memory")] == [
            "upkeep-own-update", "upkeep-bare-update",
            "upkeep-leaping-update"]
        assert [d.upkeep_id for d in agent.upkeep_upkeeps_green()] == [
            "upkeep-held-update", "upkeep-rechecked-update", "upkeep-own-update"]
        agent.upkeep_panel()
        agent.upkeep_verdict()
        agent.upkeep_index()
        agent.report_upkeep()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _UPKEEP_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_upkeep_upkeep("upkeep-nope")
        with pytest.raises(KeyError):
            agent.get_upkeep_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_upkeep_note("note-nope")
        with pytest.raises(ValueError):
            agent.upkeep_upkeeps_for_slice("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_upkeep_upkeep(_upkeep())
        status = agent.upkeep_status()
        assert [d["upkeep_id"] for d in status["upkeeps"]] == ["upkeep-test"]
        assert status["book"]["title"] == "An unheld upkeep book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["check"] for e in status["index"]["entries"]] == [
            "sealed"]
        assert status["first_note"] is None
        assert "upkeep-test" in status["screen"]
    def test_held_upkeep_never_falls_back_to_the_example(
            self, agent):
        agent.register_upkeep_upkeep(_upkeep())
        with pytest.raises(KeyError):
            agent.get_upkeep_upkeep("upkeep-held-update")
        with pytest.raises(KeyError):
            agent.get_upkeep_view("view-upkeeps")
        with pytest.raises(KeyError):
            agent.get_upkeep_note("note-note-first")
        upkeep = agent.get_upkeep_upkeep("upkeep-test")
        assert upkeep.title == "A test upkeep"
        assert agent.upkeep_book().title == (
            "An unheld upkeep book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_upkeep_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.upkeep_id == "upkeep-held-update"
        status = agent.upkeep_status()
        assert status["index"]["gaps"] == [
            "upkeep-bare-update", "upkeep-leaping-update"]
        assert status["first_note"]["upkeep_id"] == (
            "upkeep-held-update")
        assert status["first_note"]["stance"] == "note"

class TestUpkeepAgentHolding:
    def test_register_upkeep_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_upkeep_upkeep(_upkeep())
        assert result["upkeep"]["upkeep_id"] == "upkeep-test"
        assert result["record_news"]["type"] == "upkeep_upkeep"
        assert "upkeep-test" in result["screen"]
        events = _upkeep_events(store, session_id, "upkeep_upkeep")
        assert len(events) == 1
        agent.close()

    def test_duplicate_upkeep_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_upkeep_upkeep(_upkeep())
        with pytest.raises(ValueError):
            agent.register_upkeep_upkeep(_upkeep(seq=9))
        with pytest.raises(ValueError):
            agent.register_upkeep_upkeep(_upkeep(upkeep_id="upkeep-two"))
        events = _upkeep_events(store, session_id, "upkeep_upkeep")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_upkeep_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_upkeep_events(
            store, session_id, "upkeep_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_upkeep_upkeep(_upkeep())
        result = agent.view_upkeep("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "upkeep_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "sealed"
        assert len(_upkeep_events(
            store, session_id, "upkeep_view")) == 1
        assert len(_upkeep_events(
            store, session_id, "upkeep_panel")) == 1
        assert len(_upkeep_events(
            store, session_id, "upkeep_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_upkeep_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "upkeep_slice", "upkeep_upkeep", "upkeep_view"]
        assert len(_upkeep_events(
            store, session_id, "upkeep_upkeep")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_upkeep_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "upkeep_panel"
        assert result["index_record"]["gaps"] == [
            "upkeep-bare-update", "upkeep-leaping-update"]
        with pytest.raises(ValueError):
            agent.record_upkeep_book()
        assert len(_upkeep_events(
            store, session_id, "upkeep_slice")) == 3
        assert len(_upkeep_events(
            store, session_id, "upkeep_upkeep")) == 5
        assert len(_upkeep_events(
            store, session_id, "upkeep_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_upkeep_book_file(tmp_path)
        book = load_upkeep_file(path)
        result = agent.record_upkeep_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_upkeep()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "held"
        assert report["index"]["gaps"] == [
            "upkeep-bare-update", "upkeep-leaping-update"]
        assert "upkeep-held-update" in report["book_text"]
        assert "sealed - The held update (upkeep-held-update)" in report["index_text"]
        agent.register_upkeep_upkeep(_upkeep())
        report = agent.report_upkeep()
        assert report["book"]["title"] == "An unheld upkeep book"
        assert report["panel"] is None
        assert report["verdict"] is None

class TestUpkeepTerminalHeading:
    def test_show_upkeep_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/mapupkeep")
        assert "The Memory Gate (M-211)" in text
        _, _, text = _slash(agent, "/mapupkeep upkeep upkeep-held-update")
        assert "Upkeep: The held update" in text
        _, _, text = _slash(
            agent, "/mapupkeep check sealed")
        assert "Upkeep: The held update" in text
        _, _, text = _slash(agent, "/mapupkeep check triple resume")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/mapupkeep slice slice-m211-memory")
        assert "upkeep-bare-update" in text
        assert "upkeep-held-update" not in text
        _, _, text = _slash(agent, "/mapupkeep view view-upkeeps")
        assert "filter all" in text
        _, _, text = _slash(agent, "/mapupkeep note note-note-first")
        assert "Upkeep note note upkeep-held-update" in text
        _, _, text = _slash(agent, "/mapupkeep index")
        assert "Upkeep index" in text
        assert "upkeep-bare-update" in text
        _, _, text = _slash(agent, "/mapupkeep panel")
        assert "Upkeep panel under view view-upkeeps" in text
        _, _, text = _slash(agent, "/mapupkeep verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/mapupkeep [show|upkeep <upkeep-id>"
                "|check <check>|slice <slice-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/mapupkeep dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/mapupkeep upkeep upkeep-nope")
        assert "no upkeep named" in text
@pytest.fixture()
def upkeep_handler(agent, monkeypatch):
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


def _upkeep_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestUpkeepCommand:
    def test_show_is_default(self, upkeep_handler, agent):
        upkeep_handler._handle_upkeep("")
        assert "The Memory Gate (M-211)" in (
            _upkeep_published_text(upkeep_handler))

    def test_upkeep_check_slice_view_note_index_panel_verdict(
            self, upkeep_handler, agent):
        upkeep_handler._handle_upkeep("upkeep upkeep-held-update")
        assert "Upkeep: The held update" in _upkeep_published_text(
            upkeep_handler)
        upkeep_handler._handle_upkeep(
            "check sealed")
        assert "Upkeep: The held update" in _upkeep_published_text(
            upkeep_handler)
        upkeep_handler._handle_upkeep("slice slice-m211-memory")
        assert "upkeep-bare-update" in _upkeep_published_text(
            upkeep_handler)
        upkeep_handler._handle_upkeep("view view-upkeeps")
        assert "filter all" in _upkeep_published_text(upkeep_handler)
        upkeep_handler._handle_upkeep("note note-note-first")
        assert "Upkeep note note upkeep-held-update" in (
            _upkeep_published_text(upkeep_handler))
        upkeep_handler._handle_upkeep("index")
        assert "Upkeep index" in _upkeep_published_text(upkeep_handler)
        upkeep_handler._handle_upkeep("panel")
        assert "Upkeep panel under view" in _upkeep_published_text(
            upkeep_handler)
        upkeep_handler._handle_upkeep("verdict")
        assert "held" in _upkeep_published_text(upkeep_handler)
    def test_bad_grammar_is_published(
            self, upkeep_handler, agent):
        upkeep_handler._handle_upkeep("dance party")
        assert USAGE in _upkeep_published_text(upkeep_handler)
        upkeep_handler._handle_upkeep("upkeep upkeep-nope")
        assert "no upkeep named" in _upkeep_published_text(
            upkeep_handler)


class TestChatScreenRoutingUpkeep:
    def test_onboard_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/mapupkeep panel", _FakeLog())
        assert calls == [("/mapupkeep", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/mapupkeep[/green] - show the Memory gate (M-211)" in (
            text)
        assert ('"/mapupkeep": "Usage: /mapupkeep | '
                '/mapupkeep upkeep <upkeep-id>') in text

class TestUpkeepDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.upkeep_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-upkeeps"
        verdict = agent.upkeep_verdict()
        assert verdict.verdict == "held"
        found = agent.upkeep_verdict("view-sealed")
        assert found.verdict == "sealed"
        assert found.green_shown == 3
        agent.register_upkeep_upkeep(_upkeep())
        with pytest.raises(ValueError):
            agent.upkeep_panel()
        with pytest.raises(ValueError):
            agent.upkeep_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_upkeep_upkeep(_upkeep(checks=[]))
        result = agent.view_upkeep("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.upkeep_index()
        assert [e["check"] for e in result["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert result["index"]["gaps"] == [
            "upkeep-bare-update", "upkeep-leaping-update"]
        assert "sealed - The held update (upkeep-held-update)" in (
            result["index_text"])
        upkeep = agent.get_upkeep_upkeep("upkeep-leaping-update")
        assert upkeep_gaps(upkeep, agent.upkeep_book()) == (
            "steps from noted to sealed, which the upkeep sequence "
            "does not allow",)
        assert upkeep_green(upkeep, agent.upkeep_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _UPKEEP_EVENT_TYPES] == []
        agent.close()
