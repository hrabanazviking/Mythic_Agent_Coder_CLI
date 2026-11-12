"""M-218 Roads - pure-layer tests.

TIER: integration

The pure layer is the roadkeeper, held as data: one
record per road, held whole - the slice it
answers for, named by slice id, its title, the
steps it walked in walk order and the evidence
it carries, held by concordance. The question walk is
explicit - named, loaded, mapped, verified,
runnable, with their legal steps held as data -
and a road's standing is derived at call
time: a road that opens anywhere but charted, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet reached runnable stands open,
named in its gaps. A road stands only for
an active slice: a road naming no held
slice, or one that is not active, refuses by
name. The road's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, well, trace, order and current
road are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, verified or
runnable live. The shipped example book is held
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

from mythic_agent.core.mimisbrunnr_road import (
    EXAMPLE_CHECK,
    BARE_CLAIMS,
    HELD_EVIDENCE,
    INDEX_ACTION,
    CHECKS,
    CLAIM_CONCORDANCES,
    TRANSITIONS,
    CONCORDANCE_STATES,
    CHECK_FIELDS,
    PLAIN_EXPLANATION,
    ROAD_RESOURCE,
    ROAD_RULE,
    ROAD_SCHEMA,
    ROAD_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    RoadRecord,
    IndexEntry,
    ConcordanceRef,
    NoteRecord,
    RoadBook,
    RoadIndex,
    RoadPanel,
    RoadRegistry,
    RoadVerdict,
    RoadView,
    trace_for_road,
    well_record,
    book_record,
    build_trace,
    build_book,
    build_road,
    build_concordance_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_road,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    road_for_check,
    road_gaps,
    road_order,
    road_record,
    road_green,
    roads_for_concordance,
    first_note,
    format_book,
    format_road,
    format_index,
    format_note,
    format_check,
    format_panel,
    format_road_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    concordance_record,
    load_road,
    legal_step,
    load_road_file,
    next_check,
    normalize_check,
    normalize_claim_concordance,
    normalize_concordance_state,
    normalize_stance,
    normalize_view_filter,
    note_for_road,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_road_args,
    green_roads,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_roads,
    validate_book,
    validate_road,
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
ON = "2026-11-11"
BY = "the coordinator"
EXAMPLE_TITLE = "The 500-slice road as a campaign at the M-218 slice boundary"
EXAMPLE_CHECKS = ["runnable", "runnable", "runnable"]
EXAMPLE_RUN_IDS = (
    "road-held-road", "road-remeasured-road",
    "road-own-road", "road-bare-road",
    "road-leaping-road")
EXAMPLE_TRACE = "charted > loaded > mapped > verified > runnable"


def _ref(**overrides):
    fields = {
        "concordance_id": "slice-test",
        "seq": 1,
        "title": "A test slice",
        "state": "live",
        "detail": "A test slice reference held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "road-test",
    }
    fields.update(overrides)
    return build_concordance_ref(fields)


def _road(**overrides):
    fields = {
        "road_id": "road-test",
        "seq": 1,
        "concordance_id": "slice-test",
        "title": "A test road",
        "checks": ["charted", "loaded", "mapped", "verified", "runnable"],
        "claims": [],
        "detail": "A test road held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "road-test",
    }
    fields.update(overrides)
    return build_road(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "road-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "road_id": "road-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "road-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "road_id": "road-test",
        "trace": "charted > loaded > mapped > verified > runnable",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "road-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(slices=None, roads=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": ROAD_SCHEMA,
        "slice": "M-218",
        "mimisbrunnr_road": {"title": "A test road book"},
        "concordances": [item.to_record() for item in (
            slices if slices is not None else [_ref()])],
        "road_records": [item.to_record() for item in (
            roads if roads is not None else [_road()])],
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
    return _book(roads=[
        _road(),
        _road(road_id="road-hidden", seq=2,
               title="A hidden road", checks=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_road()
    assert book.title == EXAMPLE_TITLE
    assert book.road_ids() == EXAMPLE_RUN_IDS
    assert book.concordance_ids() == (
        "concordance-m217-templates", "concordance-m218-road",
        "concordance-m219-interrupts")
    assert [v.view_id for v in book.views] == [
        "view-roads", "view-runnable"]
    assert [m.road_id for m in book.notes] == [
        "road-held-road", "road-bare-road"]
    assert [a.road_id for a in book.traces] == ["road-held-road"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m217-boundary"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.road_ids())
    derived = derive_panel(book, "view-roads")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-roads").verdict == "held"
    assert derive_verdict(book, "view-roads").green_shown == 3
    assert derive_verdict(book, "view-runnable").verdict == "runnable"
    assert derive_verdict(book, "view-runnable").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / ROAD_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == ROAD_SCHEMA
    assert raw["slice"] == "M-218"
    assert "verdict" not in raw
    assert "road_index" not in raw
    assert "well" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-218")]
    assert slice_.title == "The 500-slice road as a campaign"
    assert slice_.part == 9
    assert "Mimisbrunnr roadmap loadable as a campaign file" in slice_.summary
    assert "his own road, runnable" in slice_.summary
    assert ROAD_SLICE == "M-218"

def test_charter_rows_do_not_name_m218():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-218" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert COMPLETE_WORDS == ("complete", "open")
    assert CHECK_FIELDS == ("checks", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "complete", "open")
    assert VERDICT_WORDS == ("runnable", "held", "blocked")
    assert CONCORDANCE_STATES == ("live", "dormant")
    assert CHECKS == ("charted", "loaded", "mapped", "verified", "runnable")
    assert HELD_EVIDENCE == ("concordance_ref", "well_ref", "keeper_record", "run_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_CONCORDANCES == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["verified"] == ("charted", "runnable")
    assert TRANSITIONS["runnable"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_CHECK == "runnable"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_concordance_state("LIVE") == "live"
    assert normalize_check("MAPPED") == "mapped"
    assert normalize_claim_concordance("FEELING") == "feeling"
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    with pytest.raises(ValueError):
        normalize_concordance_state("blessed")
    with pytest.raises(ValueError):
        normalize_check("polish")
    with pytest.raises(ValueError):
        normalize_claim_concordance("weather")
    assert legal_step("mapped", "verified") is True
    assert legal_step("loaded", "runnable") is False
    assert legal_step("runnable", "charted") is False
    assert next_check("charted") == "loaded"
    assert next_check("mapped") == "verified"
    assert next_check("verified", failed=True) == "charted"
    assert next_check("verified") == "runnable"
    assert next_check("runnable") is None
    assert "held as data alone" in ROAD_RULE
    assert "road sequence" in ROAD_RULE
    assert "M-218" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /mimis")

def test_shipped_book_judged_honestly_as_data():
    book = load_road()
    opening = book.road_for("road-held-road")
    assert road_green(opening, book) is True
    assert road_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Road: The held road",
        "Concordance: concordance-m217-templates",
        "Check: runnable",
        "Claims: concordance_ref")
    asking = book.road_for("road-bare-road")
    assert road_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert road_green(asking, book) is False
    skipping = book.road_for("road-leaping-road")
    assert road_gaps(skipping, book) == (
        "steps from loaded to runnable, which the road sequence "
        "does not allow",)
    assert [g.road_id for g in green_roads(book)] == [
        "road-held-road", "road-remeasured-road", "road-own-road"]
    index = derive_index(book)
    assert [e.check for e in index.entries] == EXAMPLE_CHECKS
    assert index.gaps == ("road-bare-road", "road-leaping-road")
    assert road_for_check(book, EXAMPLE_CHECK).road_id == (
        "road-held-road")
    assert road_for_check(book, "triple resume") is None
    assert transition_breaks(book) == (
        "road-leaping-road: loaded > runnable",)
    assert [g.road_id for g in road_order(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "road-held-road") == EXAMPLE_TRACE
    assert trace_current(book, "road-held-road") is True
    assert trace_current(book, "road-remeasured-road") is False
    assert trace_for_road(
        book, "road-held-road").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_road(
        book, "road-held-road", "note").note_id == (
            "note-note-first")
    assert note_for_road(book, "road-nope") is None
    assert current_road(book).road_id == "road-bare-road"
    well = well_record(book)
    assert well["standings"] == [
        {"standing": "complete", "road_records": 3},
        {"standing": "open", "road_records": 2}]
    assert well["total"] == 5
    assert well["current_road"] == "road-bare-road"
    assert well["traces"] == [
        {"road_id": "road-held-road", "trace": "current"},
        {"road_id": "road-remeasured-road", "trace": "unheld"},
        {"road_id": "road-own-road", "trace": "unheld"},
        {"road_id": "road-bare-road", "trace": "unheld"},
        {"road_id": "road-leaping-road", "trace": "unheld"}]
    assert well["breaks"] == ["road-leaping-road: loaded > runnable"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 236
    assert citizen["next_slice"] == "M-237"
    assert citizen["m218_title"] == "The 500-slice road as a campaign"
    assert citizen["m218_part"] == 9
    assert citizen["m218_status"] == "done"

def test_road_record_round_trips():
    road = _road()
    assert validate_road(road) is road
    rebuilt = build_road(road.to_record())
    assert rebuilt == road
    assert rebuilt.item_id == "road-test"
    assert rebuilt.check == "runnable"
    record = road_record(road)
    assert record["type"] == "road_road"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert concordance_record(ref)["type"] == "road_slice"
    assert concordance_record(ref)["state"] == "live"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _road(checks=[])
    assert road_gaps(silent) == (
        "has passed through no step: the road has not started",)
    assert road_green(silent) is False
    walking = _road(checks=["charted", "loaded"])
    assert road_gaps(walking) == (
        "has not reached runnable: the road stands at loaded",)
    assert walking.check == "loaded"
    sideways = _road(checks=["loaded", "mapped", "verified", "runnable"])
    assert road_gaps(sideways) == (
        "opens at loaded, not at charted: the road opens "
        "with the reflection",)
    repaired = _road(checks=["charted", "loaded", "mapped", "verified", "charted", "loaded", "mapped", "verified", "runnable"])
    assert road_gaps(repaired) == ()
    assert road_green(repaired) is True
    with pytest.raises(ValueError):
        _road(checks=[42])
    with pytest.raises(ValueError):
        _road(checks="inspect as a bare string")
    with pytest.raises(ValueError):
        _road(checks=["charted", "polish"])
    with pytest.raises(ValueError):
        _road(claims=["weather"])
    with pytest.raises(ValueError):
        _road(claims="concordance_ref")
    none_road = _road(checks=None, claims=None)
    assert none_road.checks == ()
    assert none_road.claims == ()

def test_road_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "entries", "coverage", "current_road",
                "well", "order"):
        fields = _road().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_road(fields)
    fields = _road().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_road(fields)


def test_road_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _road().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_road(fields)


def test_road_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _road(title="")
    with pytest.raises(ValueError):
        _road(concordance_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "charted > loaded > mapped > verified > runnable"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_roads_own_fields():
    road = _road(claims=["concordance_ref"])
    assert plain_lines(road) == (
        "Road: A test road",
        "Concordance: slice-test",
        "Check: runnable",
        "Claims: concordance_ref")
    segment = segment_of(road)
    assert segment.startswith("road-test: A test road")
    assert "check: 'runnable'" in segment
    assert "gaps: none" in segment
    assert plain_words(road).startswith(
        "A test road - from slice-test")

def test_red_roads_stand_named_in_their_gaps():
    asking = _road(claims=["feeling", "concordance_ref", "summary"])
    assert road_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert road_green(asking) is False
    skipping = _road(checks=["charted", "loaded", "runnable"])
    assert road_gaps(skipping) == (
        "steps from loaded to runnable, which the road sequence "
        "does not allow",)
    book = _book(roads=[
        _road(),
        _road(road_id="road-skipping", seq=2,
             checks=["charted", "loaded", "runnable"]),
    ])
    assert transition_breaks(book) == (
        "road-skipping: loaded > runnable",)
    assert current_road(book).road_id == "road-skipping"
    assert [g.road_id for g in road_order(book)] == [
        "road-test", "road-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "road_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "road_note"
    assert record["road_id"] == "road-test"
    assert view_plain_words(view) == "View view-test: shows all roads."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_roads_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.check for e in index.entries] == ["runnable"]
    assert index.entries[0] == IndexEntry(
        check="runnable",
        road_id="road-test", title="A test road")
    assert index.gaps == ("road-hidden",)
    record = index_record(book)
    assert record["type"] == "road_index"
    assert record["gaps"] == ["road-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "road_book"

def test_check_target_reaches_its_road_and_an_unheld_target_reaches_nothing():
    book = load_road()
    assert road_for_check(book, "runnable").road_id == (
        "road-held-road")
    assert road_for_check(book, "") is None
    assert road_for_check(book, None) is None
    assert road_for_check(book, "not held at all") is None
    text = format_check(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_road()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Road note note road-held-road" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").road_id == "road-test"
    assert note_for_road(book, "road-test").note_id == "note-test"
    assert note_for_road(book, "road-test", "praise") is None
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
    row = build_row(None, _road(), book)
    assert row.standing == "complete"
    assert validate_row(row, _road(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_roads():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "road_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "runnable"
    empty_book = _book(roads=[_road(checks=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(RoadVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_road()
    assert [g.road_id for g in shown_roads(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.road_id for g in shown_roads(book, "view-runnable")] == [
        "road-held-road", "road-remeasured-road", "road-own-road"]
    assert [g.road_id for g in roads_for_concordance(
        book, "concordance-m218-road")] == [
            "road-own-road", "road-bare-road",
            "road-leaping-road"]
    assert roads_for_concordance(book, "slice-nope") == ()
    assert current_road(_mixed_book()).road_id == "road-hidden"
    assert current_road(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "road-test") == (
        "charted > loaded > mapped > verified > runnable")
    assert trace_current(stale, "road-test") is False
    assert well_record(stale)["traces"] == [
        {"road_id": "road-test", "trace": "stale"}]

def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(roads=[_road(), _road(seq=2)])
    with pytest.raises(ValueError):
        _book(roads=[_road(), _road(road_id="road-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(roads=[_road(concordance_id="slice-nope")])
    with pytest.raises(ValueError):
        _book(slices=[_ref(), _ref(
            concordance_id="slice-cold", seq=2, state="dormant")],
            roads=[_road(concordance_id="slice-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(concordance_id="slice-nope")])
    fields = {
        "schema": ROAD_SCHEMA, "slice": "M-218",
        "mimisbrunnr_road": {"title": "A mapped book"},
        "slices": [_ref().to_record()],
        "road_records": [_road().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "runnable"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_road"] = "road-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_road")
    fields["trace"] = "road-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / ROAD_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "mimisbrunnr_road.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_road_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.road_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = RoadRegistry()
    assert registry.title() is None
    registry.register_concordance_ref(_ref())
    registry.register_road(_road())
    registry.register_view(_view())
    assert [g.road_id for g in registry.list_roads()] == ["road-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_road("road-test").title == "A test road"
    assert registry.get_slice("slice-test").state == "live"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("road-test").road_id == "road-test"
    with pytest.raises(ValueError):
        registry.register_road(_road(seq=9))
    with pytest.raises(ValueError):
        registry.register_road(_road(road_id="road-two"))
    with pytest.raises(KeyError):
        registry.get_road("road-nope")
    assert registry.book().title == "An unheld road book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = RoadRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test road book"
    assert registry.title() == "A test road book"
    assert len(registry.list_roads()) == 2
    other = RoadRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    road = _road()
    assert "A test road" in plain_words(road)
    assert panel_plain_words(_mixed_book()).startswith(
        "The road book holds 2 roads")
    assert verdict_plain_words(_mixed_book()) == (
        "The roads stand held: 1 of 2 shown roads stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green roads; red, "
        "named in its gaps: road-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_road(road)
    assert "Road: A test road" in text
    assert "stands complete" in text
    text = format_road(_road(checks=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Road Gate (M-218) - A test road book" in book_text
    assert "road-hidden" in format_book(_mixed_book(), "slice-test")
    assert "Road panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "runnable - A test road (road-test)" in index_text
    assert "road-hidden" in index_text
    screen = format_road_screen()
    assert "The Road Gate (M-218)" in screen
    assert "road-bare-road" in screen

def test_parse_args_well_and_loader_targets():
    assert parse_road_args("") == ("show", None)
    assert parse_road_args(None) == ("show", None)
    assert parse_road_args("show") == ("show", None)
    assert parse_road_args("road road-test") == (
        "road", "road-test")
    assert parse_road_args("check runnable") == (
        "check", "runnable")
    assert parse_road_args("concordance slice-test") == (
        "concordance", "slice-test")
    assert parse_road_args("view view-test") == ("view", "view-test")
    assert parse_road_args("note note-test") == ("note", "note-test")
    assert parse_road_args("index") == ("index", None)
    assert parse_road_args("panel") == ("panel", None)
    assert parse_road_args("verdict") == ("verdict", None)
    for bad in ("dance", "road", "check", "slice", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_road_args(bad)
    well = well_record()
    assert well["type"] == "road_well"
    assert well["total"] == 5
    assert well["current_road"] == "road-bare-road"
    book = load_road({
        "schema": ROAD_SCHEMA, "slice": "M-218",
        "mimisbrunnr_road": {"title": "A mapped book"},
        "slices": [_ref().to_record()],
        "road_records": [_road().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, RoadBook)
    assert book.title == "A mapped book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_road({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_road({"slice": "M-999"})
    built = build_road(
        road_id="road-kw", seq=3, concordance_id="slice-test",
        title="Kw Road", checks=["charted", "loaded", "mapped", "verified", "runnable"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="road-test")
    assert built.road_id == "road-kw"
    assert road_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-218 agent layer: the agent holds a road
# book for the session, roads and views are
# published as session news through the
# checkpoint target (journal first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held roads, the well is derived from
# the held roads' completeness, the roadmap standing
# is read from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no slice. This layer roads
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_ROAD_EVENT_TYPES = (
    "road_road", "road_slice", "road_view",
    "road_panel", "road_verdict")


def _road_events(store, session_id, concordance):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == concordance]


def _write_mimis_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / ROAD_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "mimisbrunnr_road.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestRoadAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.mimis_status()
        assert status["road_records"] == []
        assert status["slices"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["mimis_book"]["title"] == EXAMPLE_TITLE
        assert len(status["mimis_book"]["slices"]) == 3
        assert len(status["mimis_book"]["road_records"]) == 5
        assert len(status["mimis_book"]["views"]) == 2
        assert len(status["mimis_book"]["notes"]) == 2
        assert len(status["mimis_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m217-boundary"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["check"] for e in status["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert status["index"]["gaps"] == [
            "road-bare-road", "road-leaping-road"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["well"]["total"] == 5
        assert status["well"]["current_road"] == "road-bare-road"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 236
        assert status["roadmap"]["next_slice"] == "M-237"
        assert status["roadmap"]["m218_title"] == "The 500-slice road as a campaign"
        assert "held as data alone" in status["rule"]
        assert "road-bare-road" in status["plain_words"]
        assert "The Road Gate (M-218)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._mimis_registry()
        assert agent._mimis_registry() is first
        assert agent._mimis_store is first
        for name in ("mimis_book", "mimis_status", "mimis_panel",
                     "mimis_verdict", "mimis_index", "report_mimis"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_mimis_registry", "mimis_book", "mimis_status",
            "get_mimis_road", "get_mimis_view", "get_mimis_note",
            "mimis_roads_for_concordance", "mimis_roads_green",
            "mimis_panel", "mimis_verdict", "mimis_index",
            "register_mimis_road", "register_mimis_view",
            "view_mimis", "register_mimis_book",
            "record_mimis_book", "report_mimis",
            "_publish_mimis_record", "_mimis_screen",
            "_mimis_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.mimis_status()
        assert agent.get_mimis_road(
            "road-held-road").title == "The held road"
        assert agent.get_mimis_view(
            "view-roads").view_filter == "all"
        assert agent.get_mimis_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.road_id for d in agent.mimis_roads_for_concordance(
            "concordance-m218-road")] == [
            "road-own-road", "road-bare-road",
            "road-leaping-road"]
        assert [d.road_id for d in agent.mimis_roads_green()] == [
            "road-held-road", "road-remeasured-road", "road-own-road"]
        agent.mimis_panel()
        agent.mimis_verdict()
        agent.mimis_index()
        agent.report_mimis()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _ROAD_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_mimis_road("road-nope")
        with pytest.raises(KeyError):
            agent.get_mimis_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_mimis_note("note-nope")
        with pytest.raises(ValueError):
            agent.mimis_roads_for_concordance("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_mimis_road(_road())
        status = agent.mimis_status()
        assert [d["road_id"] for d in status["road_records"]] == ["road-test"]
        assert status["book"]["title"] == "An unheld road book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["check"] for e in status["index"]["entries"]] == [
            "runnable"]
        assert status["first_note"] is None
        assert "road-test" in status["screen"]
    def test_held_road_never_falls_back_to_the_example(
            self, agent):
        agent.register_mimis_road(_road())
        with pytest.raises(KeyError):
            agent.get_mimis_road("road-held-road")
        with pytest.raises(KeyError):
            agent.get_mimis_view("view-roads")
        with pytest.raises(KeyError):
            agent.get_mimis_note("note-note-first")
        road = agent.get_mimis_road("road-test")
        assert road.title == "A test road"
        assert agent.mimis_book().title == (
            "An unheld road book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_mimis_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.road_id == "road-held-road"
        status = agent.mimis_status()
        assert status["index"]["gaps"] == [
            "road-bare-road", "road-leaping-road"]
        assert status["first_note"]["road_id"] == (
            "road-held-road")
        assert status["first_note"]["stance"] == "note"

class TestRoadAgentHolding:
    def test_register_road_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_mimis_road(_road())
        assert result["road"]["road_id"] == "road-test"
        assert result["record_news"]["type"] == "road_road"
        assert "road-test" in result["screen"]
        events = _road_events(store, session_id, "road_road")
        assert len(events) == 1
        agent.close()

    def test_duplicate_road_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_mimis_road(_road())
        with pytest.raises(ValueError):
            agent.register_mimis_road(_road(seq=9))
        with pytest.raises(ValueError):
            agent.register_mimis_road(_road(road_id="road-two"))
        events = _road_events(store, session_id, "road_road")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_mimis_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_road_events(
            store, session_id, "road_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_mimis_road(_road())
        result = agent.view_mimis("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "road_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "runnable"
        assert len(_road_events(
            store, session_id, "road_view")) == 1
        assert len(_road_events(
            store, session_id, "road_panel")) == 1
        assert len(_road_events(
            store, session_id, "road_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_mimis_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "road_slice", "road_road", "road_view"]
        assert len(_road_events(
            store, session_id, "road_road")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_mimis_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "road_panel"
        assert result["index_record"]["gaps"] == [
            "road-bare-road", "road-leaping-road"]
        with pytest.raises(ValueError):
            agent.record_mimis_book()
        assert len(_road_events(
            store, session_id, "road_slice")) == 3
        assert len(_road_events(
            store, session_id, "road_road")) == 5
        assert len(_road_events(
            store, session_id, "road_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_mimis_book_file(tmp_path)
        book = load_road_file(path)
        result = agent.record_mimis_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_concordancert_renders_example_then_held_book_only(self, agent):
        report = agent.report_mimis()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "held"
        assert report["index"]["gaps"] == [
            "road-bare-road", "road-leaping-road"]
        assert "road-held-road" in report["book_text"]
        assert "runnable - The held road (road-held-road)" in report["index_text"]
        agent.register_mimis_road(_road())
        report = agent.report_mimis()
        assert report["book"]["title"] == "An unheld road book"
        assert report["panel"] is None
        assert report["verdict"] is None

class TestRoadTerminalHeading:
    def test_show_road_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/mimis")
        assert "The Road Gate (M-218)" in text
        _, _, text = _slash(agent, "/mimis road road-held-road")
        assert "Road: The held road" in text
        _, _, text = _slash(
            agent, "/mimis check runnable")
        assert "Road: The held road" in text
        _, _, text = _slash(agent, "/mimis check triple resume")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/mimis concordance concordance-m218-road")
        assert "road-bare-road" in text
        assert "road-held-road" not in text
        _, _, text = _slash(agent, "/mimis view view-roads")
        assert "filter all" in text
        _, _, text = _slash(agent, "/mimis note note-note-first")
        assert "Road note note road-held-road" in text
        _, _, text = _slash(agent, "/mimis index")
        assert "Road index" in text
        assert "road-bare-road" in text
        _, _, text = _slash(agent, "/mimis panel")
        assert "Road panel under view view-roads" in text
        _, _, text = _slash(agent, "/mimis verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/mimis [show|road <road-id>"
                "|check <check>|concordance <concordance-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/mimis dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/mimis road road-nope")
        assert "no road named" in text
@pytest.fixture()
def road_handler(agent, monkeypatch):
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


def _road_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestRoadCommand:
    def test_show_is_default(self, road_handler, agent):
        road_handler._handle_mimis("")
        assert "The Road Gate (M-218)" in (
            _road_published_text(road_handler))

    def test_road_check_slice_view_note_index_panel_verdict(
            self, road_handler, agent):
        road_handler._handle_mimis("road road-held-road")
        assert "Road: The held road" in _road_published_text(
            road_handler)
        road_handler._handle_mimis(
            "check runnable")
        assert "Road: The held road" in _road_published_text(
            road_handler)
        road_handler._handle_mimis("concordance concordance-m218-road")
        assert "road-bare-road" in _road_published_text(
            road_handler)
        road_handler._handle_mimis("view view-roads")
        assert "filter all" in _road_published_text(road_handler)
        road_handler._handle_mimis("note note-note-first")
        assert "Road note note road-held-road" in (
            _road_published_text(road_handler))
        road_handler._handle_mimis("index")
        assert "Road index" in _road_published_text(road_handler)
        road_handler._handle_mimis("panel")
        assert "Road panel under view" in _road_published_text(
            road_handler)
        road_handler._handle_mimis("verdict")
        assert "held" in _road_published_text(road_handler)
    def test_bad_grammar_is_published(
            self, road_handler, agent):
        road_handler._handle_mimis("dance party")
        assert USAGE in _road_published_text(road_handler)
        road_handler._handle_mimis("road road-nope")
        assert "no road named" in _road_published_text(
            road_handler)


class TestChatScreenRoutingRoad:
    def test_onwell_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/mimis panel", _FakeLog())
        assert calls == [("/mimis", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/mimis[/green] - show the Road gate (M-218)" in (
            text)
        assert ('"/mimis": "Usage: /mimis | '
                '/mimis road <road-id>') in text

class TestRoadDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.mimis_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-roads"
        verdict = agent.mimis_verdict()
        assert verdict.verdict == "held"
        found = agent.mimis_verdict("view-runnable")
        assert found.verdict == "runnable"
        assert found.green_shown == 3
        agent.register_mimis_road(_road())
        with pytest.raises(ValueError):
            agent.mimis_panel()
        with pytest.raises(ValueError):
            agent.mimis_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_mimis_road(_road(checks=[]))
        result = agent.view_mimis("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.mimis_index()
        assert [e["check"] for e in result["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert result["index"]["gaps"] == [
            "road-bare-road", "road-leaping-road"]
        assert "runnable - The held road (road-held-road)" in (
            result["index_text"])
        road = agent.get_mimis_road("road-leaping-road")
        assert road_gaps(road, agent.mimis_book()) == (
            "steps from loaded to runnable, which the road sequence "
            "does not allow",)
        assert road_green(road, agent.mimis_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _ROAD_EVENT_TYPES] == []
        agent.close()
