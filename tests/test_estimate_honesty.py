"""M-215 Estimates - pure-layer tests.

TIER: integration

The pure layer is the estimator, held as data: one
record per estimate, held whole - the slice it
answers for, named by slice id, its title, the
steps it walked in walk order and the evidence
it carries, held by kind. The question walk is
explicit - named, recorded, measured, compared,
calibrated, with their legal steps held as data -
and a estimate's standing is derived at call
time: a estimate that opens anywhere but predicted, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet reached calibrated stands open,
named in its gaps. A estimate stands only for
an active slice: a estimate naming no held
slice, or one that is not active, refuses by
name. The estimate's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, board, trace, order and current
estimate are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, compared or
calibrated live. The shipped example book is held
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

from mythic_agent.core.estimate_honesty import (
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
    ESTIMATE_RESOURCE,
    ESTIMATE_RULE,
    ESTIMATE_SCHEMA,
    ESTIMATE_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    EstimateRecord,
    IndexEntry,
    SliceRef,
    NoteRecord,
    EstimateBook,
    EstimateIndex,
    EstimatePanel,
    EstimateRegistry,
    EstimateVerdict,
    EstimateView,
    trace_for_estimate,
    board_record,
    book_record,
    build_trace,
    build_book,
    build_estimate,
    build_slice_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_estimate,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    estimate_for_check,
    estimate_gaps,
    estimate_order,
    estimate_record,
    estimate_green,
    estimates_for_slice,
    first_note,
    format_book,
    format_estimate,
    format_index,
    format_note,
    format_check,
    format_panel,
    format_estimate_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    slice_record,
    load_estimate,
    legal_step,
    load_estimate_file,
    next_check,
    normalize_check,
    normalize_claim_kind,
    normalize_slice_state,
    normalize_stance,
    normalize_view_filter,
    note_for_estimate,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_estimate_args,
    green_estimates,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_estimates,
    validate_book,
    validate_estimate,
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
EXAMPLE_TITLE = "Estimate honesty at the M-214 slice boundary"
EXAMPLE_CHECKS = ["calibrated", "calibrated", "calibrated"]
EXAMPLE_RUN_IDS = (
    "estimate-held-forecast", "estimate-remeasured-forecast",
    "estimate-own-forecast", "estimate-bare-forecast",
    "estimate-leaping-forecast")
EXAMPLE_TRACE = "predicted > recorded > measured > compared > calibrated"


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
        "origin_session": "estimate-test",
    }
    fields.update(overrides)
    return build_slice_ref(fields)


def _estimate(**overrides):
    fields = {
        "estimate_id": "estimate-test",
        "seq": 1,
        "slice_id": "slice-test",
        "title": "A test estimate",
        "checks": ["predicted", "recorded", "measured", "compared", "calibrated"],
        "claims": [],
        "detail": "A test estimate held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "estimate-test",
    }
    fields.update(overrides)
    return build_estimate(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "estimate-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "estimate_id": "estimate-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "estimate-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "estimate_id": "estimate-test",
        "trace": "predicted > recorded > measured > compared > calibrated",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "estimate-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(slices=None, estimates=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": ESTIMATE_SCHEMA,
        "slice": "M-215",
        "estimate_honesty": {"title": "A test estimate book"},
        "slices": [item.to_record() for item in (
            slices if slices is not None else [_ref()])],
        "estimate_records": [item.to_record() for item in (
            estimates if estimates is not None else [_estimate()])],
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
    return _book(estimates=[
        _estimate(),
        _estimate(estimate_id="estimate-hidden", seq=2,
               title="A hidden estimate", checks=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_estimate()
    assert book.title == EXAMPLE_TITLE
    assert book.estimate_ids() == EXAMPLE_RUN_IDS
    assert book.slice_ids() == (
        "slice-m214-pattern", "slice-m215-estimate",
        "slice-m216-hall")
    assert [v.view_id for v in book.views] == [
        "view-estimates", "view-calibrated"]
    assert [m.estimate_id for m in book.notes] == [
        "estimate-held-forecast", "estimate-bare-forecast"]
    assert [a.estimate_id for a in book.traces] == ["estimate-held-forecast"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m214-boundary"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.estimate_ids())
    derived = derive_panel(book, "view-estimates")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-estimates").verdict == "held"
    assert derive_verdict(book, "view-estimates").green_shown == 3
    assert derive_verdict(book, "view-calibrated").verdict == "calibrated"
    assert derive_verdict(book, "view-calibrated").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / ESTIMATE_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == ESTIMATE_SCHEMA
    assert raw["slice"] == "M-215"
    assert "verdict" not in raw
    assert "estimate_index" not in raw
    assert "board" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-215")]
    assert slice_.title == "Estimate honesty"
    assert slice_.part == 9
    assert "slice forecasts (time/tokens) recorded against outcomes" in slice_.summary
    assert "the app shows its own calibration" in slice_.summary
    assert "improving visibly or not at all" in slice_.summary
    assert ESTIMATE_SLICE == "M-215"

def test_charter_rows_do_not_name_m215():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-215" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert COMPLETE_WORDS == ("complete", "open")
    assert CHECK_FIELDS == ("checks", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "complete", "open")
    assert VERDICT_WORDS == ("calibrated", "held", "blocked")
    assert SLICE_STATES == ("active", "queued")
    assert CHECKS == ("predicted", "recorded", "measured", "compared", "calibrated")
    assert HELD_EVIDENCE == ("slice_ref", "outcome_ref", "test_record", "calibration_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["compared"] == ("predicted", "calibrated")
    assert TRANSITIONS["calibrated"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_CHECK == "calibrated"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_slice_state("ACTIVE") == "active"
    assert normalize_check("MEASURED") == "measured"
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
    assert legal_step("measured", "compared") is True
    assert legal_step("recorded", "calibrated") is False
    assert legal_step("calibrated", "predicted") is False
    assert next_check("predicted") == "recorded"
    assert next_check("measured") == "compared"
    assert next_check("compared", failed=True) == "predicted"
    assert next_check("compared") == "calibrated"
    assert next_check("calibrated") is None
    assert "held as data alone" in ESTIMATE_RULE
    assert "estimate sequence" in ESTIMATE_RULE
    assert "M-215" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /estimates")

def test_shipped_book_judged_honestly_as_data():
    book = load_estimate()
    opening = book.estimate_for("estimate-held-forecast")
    assert estimate_green(opening, book) is True
    assert estimate_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Estimate: The held forecast",
        "Slice: slice-m214-pattern",
        "Check: calibrated",
        "Claims: slice_ref")
    asking = book.estimate_for("estimate-bare-forecast")
    assert estimate_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert estimate_green(asking, book) is False
    skipping = book.estimate_for("estimate-leaping-forecast")
    assert estimate_gaps(skipping, book) == (
        "steps from recorded to calibrated, which the estimate sequence "
        "does not allow",)
    assert [g.estimate_id for g in green_estimates(book)] == [
        "estimate-held-forecast", "estimate-remeasured-forecast", "estimate-own-forecast"]
    index = derive_index(book)
    assert [e.check for e in index.entries] == EXAMPLE_CHECKS
    assert index.gaps == ("estimate-bare-forecast", "estimate-leaping-forecast")
    assert estimate_for_check(book, EXAMPLE_CHECK).estimate_id == (
        "estimate-held-forecast")
    assert estimate_for_check(book, "triple resume") is None
    assert transition_breaks(book) == (
        "estimate-leaping-forecast: recorded > calibrated",)
    assert [g.estimate_id for g in estimate_order(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "estimate-held-forecast") == EXAMPLE_TRACE
    assert trace_current(book, "estimate-held-forecast") is True
    assert trace_current(book, "estimate-remeasured-forecast") is False
    assert trace_for_estimate(
        book, "estimate-held-forecast").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_estimate(
        book, "estimate-held-forecast", "note").note_id == (
            "note-note-first")
    assert note_for_estimate(book, "estimate-nope") is None
    assert current_estimate(book).estimate_id == "estimate-bare-forecast"
    board = board_record(book)
    assert board["standings"] == [
        {"standing": "complete", "estimate_records": 3},
        {"standing": "open", "estimate_records": 2}]
    assert board["total"] == 5
    assert board["current_estimate"] == "estimate-bare-forecast"
    assert board["traces"] == [
        {"estimate_id": "estimate-held-forecast", "trace": "current"},
        {"estimate_id": "estimate-remeasured-forecast", "trace": "unheld"},
        {"estimate_id": "estimate-own-forecast", "trace": "unheld"},
        {"estimate_id": "estimate-bare-forecast", "trace": "unheld"},
        {"estimate_id": "estimate-leaping-forecast", "trace": "unheld"}]
    assert board["breaks"] == ["estimate-leaping-forecast: recorded > calibrated"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 252
    assert citizen["next_slice"] == "M-253"
    assert citizen["m215_title"] == "Estimate honesty"
    assert citizen["m215_part"] == 9
    assert citizen["m215_status"] == "done"

def test_estimate_record_round_trips():
    estimate = _estimate()
    assert validate_estimate(estimate) is estimate
    rebuilt = build_estimate(estimate.to_record())
    assert rebuilt == estimate
    assert rebuilt.item_id == "estimate-test"
    assert rebuilt.check == "calibrated"
    record = estimate_record(estimate)
    assert record["type"] == "estimate_estimate"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert slice_record(ref)["type"] == "estimate_slice"
    assert slice_record(ref)["state"] == "active"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _estimate(checks=[])
    assert estimate_gaps(silent) == (
        "has passed through no step: the estimate has not started",)
    assert estimate_green(silent) is False
    walking = _estimate(checks=["predicted", "recorded"])
    assert estimate_gaps(walking) == (
        "has not reached calibrated: the estimate stands at recorded",)
    assert walking.check == "recorded"
    sideways = _estimate(checks=["recorded", "measured", "compared", "calibrated"])
    assert estimate_gaps(sideways) == (
        "opens at recorded, not at predicted: the estimate opens "
        "with the reflection",)
    repaired = _estimate(checks=["predicted", "recorded", "measured", "compared", "predicted", "recorded", "measured", "compared", "calibrated"])
    assert estimate_gaps(repaired) == ()
    assert estimate_green(repaired) is True
    with pytest.raises(ValueError):
        _estimate(checks=[42])
    with pytest.raises(ValueError):
        _estimate(checks="inspect as a bare string")
    with pytest.raises(ValueError):
        _estimate(checks=["predicted", "polish"])
    with pytest.raises(ValueError):
        _estimate(claims=["weather"])
    with pytest.raises(ValueError):
        _estimate(claims="slice_ref")
    none_estimate = _estimate(checks=None, claims=None)
    assert none_estimate.checks == ()
    assert none_estimate.claims == ()

def test_estimate_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "entries", "coverage", "current_estimate",
                "board", "order"):
        fields = _estimate().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_estimate(fields)
    fields = _estimate().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_estimate(fields)


def test_estimate_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _estimate().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_estimate(fields)


def test_estimate_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _estimate(title="")
    with pytest.raises(ValueError):
        _estimate(slice_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "predicted > recorded > measured > compared > calibrated"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_estimates_own_fields():
    estimate = _estimate(claims=["slice_ref"])
    assert plain_lines(estimate) == (
        "Estimate: A test estimate",
        "Slice: slice-test",
        "Check: calibrated",
        "Claims: slice_ref")
    segment = segment_of(estimate)
    assert segment.startswith("estimate-test: A test estimate")
    assert "check: 'calibrated'" in segment
    assert "gaps: none" in segment
    assert plain_words(estimate).startswith(
        "A test estimate - from slice-test")

def test_red_estimates_stand_named_in_their_gaps():
    asking = _estimate(claims=["feeling", "slice_ref", "summary"])
    assert estimate_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert estimate_green(asking) is False
    skipping = _estimate(checks=["predicted", "recorded", "calibrated"])
    assert estimate_gaps(skipping) == (
        "steps from recorded to calibrated, which the estimate sequence "
        "does not allow",)
    book = _book(estimates=[
        _estimate(),
        _estimate(estimate_id="estimate-skipping", seq=2,
             checks=["predicted", "recorded", "calibrated"]),
    ])
    assert transition_breaks(book) == (
        "estimate-skipping: recorded > calibrated",)
    assert current_estimate(book).estimate_id == "estimate-skipping"
    assert [g.estimate_id for g in estimate_order(book)] == [
        "estimate-test", "estimate-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "estimate_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "estimate_note"
    assert record["estimate_id"] == "estimate-test"
    assert view_plain_words(view) == "View view-test: shows all estimates."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_estimates_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.check for e in index.entries] == ["calibrated"]
    assert index.entries[0] == IndexEntry(
        check="calibrated",
        estimate_id="estimate-test", title="A test estimate")
    assert index.gaps == ("estimate-hidden",)
    record = index_record(book)
    assert record["type"] == "estimate_index"
    assert record["gaps"] == ["estimate-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "estimate_book"

def test_check_target_reaches_its_estimate_and_an_unheld_target_reaches_nothing():
    book = load_estimate()
    assert estimate_for_check(book, "calibrated").estimate_id == (
        "estimate-held-forecast")
    assert estimate_for_check(book, "") is None
    assert estimate_for_check(book, None) is None
    assert estimate_for_check(book, "not held at all") is None
    text = format_check(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_estimate()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Estimate note note estimate-held-forecast" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").estimate_id == "estimate-test"
    assert note_for_estimate(book, "estimate-test").note_id == "note-test"
    assert note_for_estimate(book, "estimate-test", "praise") is None
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
    row = build_row(None, _estimate(), book)
    assert row.standing == "complete"
    assert validate_row(row, _estimate(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_estimates():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "estimate_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "calibrated"
    empty_book = _book(estimates=[_estimate(checks=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(EstimateVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_estimate()
    assert [g.estimate_id for g in shown_estimates(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.estimate_id for g in shown_estimates(book, "view-calibrated")] == [
        "estimate-held-forecast", "estimate-remeasured-forecast", "estimate-own-forecast"]
    assert [g.estimate_id for g in estimates_for_slice(
        book, "slice-m215-estimate")] == [
            "estimate-own-forecast", "estimate-bare-forecast",
            "estimate-leaping-forecast"]
    assert estimates_for_slice(book, "slice-nope") == ()
    assert current_estimate(_mixed_book()).estimate_id == "estimate-hidden"
    assert current_estimate(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "estimate-test") == (
        "predicted > recorded > measured > compared > calibrated")
    assert trace_current(stale, "estimate-test") is False
    assert board_record(stale)["traces"] == [
        {"estimate_id": "estimate-test", "trace": "stale"}]

def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(estimates=[_estimate(), _estimate(seq=2)])
    with pytest.raises(ValueError):
        _book(estimates=[_estimate(), _estimate(estimate_id="estimate-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(estimates=[_estimate(slice_id="slice-nope")])
    with pytest.raises(ValueError):
        _book(slices=[_ref(), _ref(
            slice_id="slice-cold", seq=2, state="queued")],
            estimates=[_estimate(slice_id="slice-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(slice_id="slice-nope")])
    fields = {
        "schema": ESTIMATE_SCHEMA, "slice": "M-215",
        "estimate_honesty": {"title": "A measured book"},
        "slices": [_ref().to_record()],
        "estimate_records": [_estimate().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "calibrated"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_estimate"] = "estimate-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_estimate")
    fields["trace"] = "estimate-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / ESTIMATE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "estimate_honesty.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_estimate_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.estimate_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = EstimateRegistry()
    assert registry.title() is None
    registry.register_slice_ref(_ref())
    registry.register_estimate(_estimate())
    registry.register_view(_view())
    assert [g.estimate_id for g in registry.list_estimates()] == ["estimate-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_estimate("estimate-test").title == "A test estimate"
    assert registry.get_slice("slice-test").state == "active"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("estimate-test").estimate_id == "estimate-test"
    with pytest.raises(ValueError):
        registry.register_estimate(_estimate(seq=9))
    with pytest.raises(ValueError):
        registry.register_estimate(_estimate(estimate_id="estimate-two"))
    with pytest.raises(KeyError):
        registry.get_estimate("estimate-nope")
    assert registry.book().title == "An unheld estimate book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = EstimateRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test estimate book"
    assert registry.title() == "A test estimate book"
    assert len(registry.list_estimates()) == 2
    other = EstimateRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    estimate = _estimate()
    assert "A test estimate" in plain_words(estimate)
    assert panel_plain_words(_mixed_book()).startswith(
        "The estimate book holds 2 estimates")
    assert verdict_plain_words(_mixed_book()) == (
        "The estimates stand held: 1 of 2 shown estimates stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green estimates; red, "
        "named in its gaps: estimate-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_estimate(estimate)
    assert "Estimate: A test estimate" in text
    assert "stands complete" in text
    text = format_estimate(_estimate(checks=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Estimate Gate (M-215) - A test estimate book" in book_text
    assert "estimate-hidden" in format_book(_mixed_book(), "slice-test")
    assert "Estimate panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "calibrated - A test estimate (estimate-test)" in index_text
    assert "estimate-hidden" in index_text
    screen = format_estimate_screen()
    assert "The Estimate Gate (M-215)" in screen
    assert "estimate-bare-forecast" in screen

def test_parse_args_board_and_loader_targets():
    assert parse_estimate_args("") == ("show", None)
    assert parse_estimate_args(None) == ("show", None)
    assert parse_estimate_args("show") == ("show", None)
    assert parse_estimate_args("estimate estimate-test") == (
        "estimate", "estimate-test")
    assert parse_estimate_args("check calibrated") == (
        "check", "calibrated")
    assert parse_estimate_args("slice slice-test") == (
        "slice", "slice-test")
    assert parse_estimate_args("view view-test") == ("view", "view-test")
    assert parse_estimate_args("note note-test") == ("note", "note-test")
    assert parse_estimate_args("index") == ("index", None)
    assert parse_estimate_args("panel") == ("panel", None)
    assert parse_estimate_args("verdict") == ("verdict", None)
    for bad in ("dance", "estimate", "check", "slice", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_estimate_args(bad)
    board = board_record()
    assert board["type"] == "estimate_board"
    assert board["total"] == 5
    assert board["current_estimate"] == "estimate-bare-forecast"
    book = load_estimate({
        "schema": ESTIMATE_SCHEMA, "slice": "M-215",
        "estimate_honesty": {"title": "A measured book"},
        "slices": [_ref().to_record()],
        "estimate_records": [_estimate().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, EstimateBook)
    assert book.title == "A measured book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_estimate({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_estimate({"slice": "M-999"})
    built = build_estimate(
        estimate_id="estimate-kw", seq=3, slice_id="slice-test",
        title="Kw Estimate", checks=["predicted", "recorded", "measured", "compared", "calibrated"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="estimate-test")
    assert built.estimate_id == "estimate-kw"
    assert estimate_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-215 agent layer: the agent holds a estimate
# book for the session, estimates and views are
# published as session news through the
# checkpoint target (journal first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held estimates, the board is derived from
# the held estimates' completeness, the roadmap standing
# is read from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no slice. This layer estimates
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_ESTIMATE_EVENT_TYPES = (
    "estimate_estimate", "estimate_slice", "estimate_view",
    "estimate_panel", "estimate_verdict")


def _estimate_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_estimate_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / ESTIMATE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "estimate_honesty.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestEstimateAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.estimate_status()
        assert status["estimate_records"] == []
        assert status["slices"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["estimate_book"]["title"] == EXAMPLE_TITLE
        assert len(status["estimate_book"]["slices"]) == 3
        assert len(status["estimate_book"]["estimate_records"]) == 5
        assert len(status["estimate_book"]["views"]) == 2
        assert len(status["estimate_book"]["notes"]) == 2
        assert len(status["estimate_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m214-boundary"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["check"] for e in status["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert status["index"]["gaps"] == [
            "estimate-bare-forecast", "estimate-leaping-forecast"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["board"]["total"] == 5
        assert status["board"]["current_estimate"] == "estimate-bare-forecast"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 252
        assert status["roadmap"]["next_slice"] == "M-253"
        assert status["roadmap"]["m215_title"] == "Estimate honesty"
        assert "held as data alone" in status["rule"]
        assert "estimate-bare-forecast" in status["plain_words"]
        assert "The Estimate Gate (M-215)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._estimate_registry()
        assert agent._estimate_registry() is first
        assert agent._estimate_store is first
        for name in ("estimate_book", "estimate_status", "estimate_panel",
                     "estimate_verdict", "estimate_index", "report_estimate"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_estimate_registry", "estimate_book", "estimate_status",
            "get_estimate_estimate", "get_estimate_view", "get_estimate_note",
            "estimate_estimates_for_slice", "estimate_estimates_green",
            "estimate_panel", "estimate_verdict", "estimate_index",
            "register_estimate_estimate", "register_estimate_view",
            "view_estimate", "register_estimate_book",
            "record_estimate_book", "report_estimate",
            "_publish_estimate_record", "_estimate_screen",
            "_estimate_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.estimate_status()
        assert agent.get_estimate_estimate(
            "estimate-held-forecast").title == "The held forecast"
        assert agent.get_estimate_view(
            "view-estimates").view_filter == "all"
        assert agent.get_estimate_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.estimate_id for d in agent.estimate_estimates_for_slice(
            "slice-m215-estimate")] == [
            "estimate-own-forecast", "estimate-bare-forecast",
            "estimate-leaping-forecast"]
        assert [d.estimate_id for d in agent.estimate_estimates_green()] == [
            "estimate-held-forecast", "estimate-remeasured-forecast", "estimate-own-forecast"]
        agent.estimate_panel()
        agent.estimate_verdict()
        agent.estimate_index()
        agent.report_estimate()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _ESTIMATE_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_estimate_estimate("estimate-nope")
        with pytest.raises(KeyError):
            agent.get_estimate_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_estimate_note("note-nope")
        with pytest.raises(ValueError):
            agent.estimate_estimates_for_slice("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_estimate_estimate(_estimate())
        status = agent.estimate_status()
        assert [d["estimate_id"] for d in status["estimate_records"]] == ["estimate-test"]
        assert status["book"]["title"] == "An unheld estimate book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["check"] for e in status["index"]["entries"]] == [
            "calibrated"]
        assert status["first_note"] is None
        assert "estimate-test" in status["screen"]
    def test_held_estimate_never_falls_back_to_the_example(
            self, agent):
        agent.register_estimate_estimate(_estimate())
        with pytest.raises(KeyError):
            agent.get_estimate_estimate("estimate-held-forecast")
        with pytest.raises(KeyError):
            agent.get_estimate_view("view-estimates")
        with pytest.raises(KeyError):
            agent.get_estimate_note("note-note-first")
        estimate = agent.get_estimate_estimate("estimate-test")
        assert estimate.title == "A test estimate"
        assert agent.estimate_book().title == (
            "An unheld estimate book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_estimate_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.estimate_id == "estimate-held-forecast"
        status = agent.estimate_status()
        assert status["index"]["gaps"] == [
            "estimate-bare-forecast", "estimate-leaping-forecast"]
        assert status["first_note"]["estimate_id"] == (
            "estimate-held-forecast")
        assert status["first_note"]["stance"] == "note"

class TestEstimateAgentHolding:
    def test_register_estimate_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_estimate_estimate(_estimate())
        assert result["estimate"]["estimate_id"] == "estimate-test"
        assert result["record_news"]["type"] == "estimate_estimate"
        assert "estimate-test" in result["screen"]
        events = _estimate_events(store, session_id, "estimate_estimate")
        assert len(events) == 1
        agent.close()

    def test_duplicate_estimate_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_estimate_estimate(_estimate())
        with pytest.raises(ValueError):
            agent.register_estimate_estimate(_estimate(seq=9))
        with pytest.raises(ValueError):
            agent.register_estimate_estimate(_estimate(estimate_id="estimate-two"))
        events = _estimate_events(store, session_id, "estimate_estimate")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_estimate_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_estimate_events(
            store, session_id, "estimate_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_estimate_estimate(_estimate())
        result = agent.view_estimate("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "estimate_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "calibrated"
        assert len(_estimate_events(
            store, session_id, "estimate_view")) == 1
        assert len(_estimate_events(
            store, session_id, "estimate_panel")) == 1
        assert len(_estimate_events(
            store, session_id, "estimate_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_estimate_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "estimate_slice", "estimate_estimate", "estimate_view"]
        assert len(_estimate_events(
            store, session_id, "estimate_estimate")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_estimate_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "estimate_panel"
        assert result["index_record"]["gaps"] == [
            "estimate-bare-forecast", "estimate-leaping-forecast"]
        with pytest.raises(ValueError):
            agent.record_estimate_book()
        assert len(_estimate_events(
            store, session_id, "estimate_slice")) == 3
        assert len(_estimate_events(
            store, session_id, "estimate_estimate")) == 5
        assert len(_estimate_events(
            store, session_id, "estimate_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_estimate_book_file(tmp_path)
        book = load_estimate_file(path)
        result = agent.record_estimate_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_estimate()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "held"
        assert report["index"]["gaps"] == [
            "estimate-bare-forecast", "estimate-leaping-forecast"]
        assert "estimate-held-forecast" in report["book_text"]
        assert "calibrated - The held forecast (estimate-held-forecast)" in report["index_text"]
        agent.register_estimate_estimate(_estimate())
        report = agent.report_estimate()
        assert report["book"]["title"] == "An unheld estimate book"
        assert report["panel"] is None
        assert report["verdict"] is None

class TestEstimateTerminalHeading:
    def test_show_estimate_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/estimates")
        assert "The Estimate Gate (M-215)" in text
        _, _, text = _slash(agent, "/estimates estimate estimate-held-forecast")
        assert "Estimate: The held forecast" in text
        _, _, text = _slash(
            agent, "/estimates check calibrated")
        assert "Estimate: The held forecast" in text
        _, _, text = _slash(agent, "/estimates check triple resume")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/estimates slice slice-m215-estimate")
        assert "estimate-bare-forecast" in text
        assert "estimate-held-forecast" not in text
        _, _, text = _slash(agent, "/estimates view view-estimates")
        assert "filter all" in text
        _, _, text = _slash(agent, "/estimates note note-note-first")
        assert "Estimate note note estimate-held-forecast" in text
        _, _, text = _slash(agent, "/estimates index")
        assert "Estimate index" in text
        assert "estimate-bare-forecast" in text
        _, _, text = _slash(agent, "/estimates panel")
        assert "Estimate panel under view view-estimates" in text
        _, _, text = _slash(agent, "/estimates verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/estimates [show|estimate <estimate-id>"
                "|check <check>|slice <slice-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/estimates dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/estimates estimate estimate-nope")
        assert "no estimate named" in text
@pytest.fixture()
def estimate_handler(agent, monkeypatch):
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


def _estimate_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestEstimateCommand:
    def test_show_is_default(self, estimate_handler, agent):
        estimate_handler._handle_estimate("")
        assert "The Estimate Gate (M-215)" in (
            _estimate_published_text(estimate_handler))

    def test_estimate_check_slice_view_note_index_panel_verdict(
            self, estimate_handler, agent):
        estimate_handler._handle_estimate("estimate estimate-held-forecast")
        assert "Estimate: The held forecast" in _estimate_published_text(
            estimate_handler)
        estimate_handler._handle_estimate(
            "check calibrated")
        assert "Estimate: The held forecast" in _estimate_published_text(
            estimate_handler)
        estimate_handler._handle_estimate("slice slice-m215-estimate")
        assert "estimate-bare-forecast" in _estimate_published_text(
            estimate_handler)
        estimate_handler._handle_estimate("view view-estimates")
        assert "filter all" in _estimate_published_text(estimate_handler)
        estimate_handler._handle_estimate("note note-note-first")
        assert "Estimate note note estimate-held-forecast" in (
            _estimate_published_text(estimate_handler))
        estimate_handler._handle_estimate("index")
        assert "Estimate index" in _estimate_published_text(estimate_handler)
        estimate_handler._handle_estimate("panel")
        assert "Estimate panel under view" in _estimate_published_text(
            estimate_handler)
        estimate_handler._handle_estimate("verdict")
        assert "held" in _estimate_published_text(estimate_handler)
    def test_bad_grammar_is_published(
            self, estimate_handler, agent):
        estimate_handler._handle_estimate("dance party")
        assert USAGE in _estimate_published_text(estimate_handler)
        estimate_handler._handle_estimate("estimate estimate-nope")
        assert "no estimate named" in _estimate_published_text(
            estimate_handler)


class TestChatScreenRoutingEstimate:
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
        screen.handle_command("/estimates panel", _FakeLog())
        assert calls == [("/estimates", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/estimates[/green] - show the Estimate gate (M-215)" in (
            text)
        assert ('"/estimates": "Usage: /estimates | '
                '/estimates estimate <estimate-id>') in text

class TestEstimateDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.estimate_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-estimates"
        verdict = agent.estimate_verdict()
        assert verdict.verdict == "held"
        found = agent.estimate_verdict("view-calibrated")
        assert found.verdict == "calibrated"
        assert found.green_shown == 3
        agent.register_estimate_estimate(_estimate())
        with pytest.raises(ValueError):
            agent.estimate_panel()
        with pytest.raises(ValueError):
            agent.estimate_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_estimate_estimate(_estimate(checks=[]))
        result = agent.view_estimate("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.estimate_index()
        assert [e["check"] for e in result["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert result["index"]["gaps"] == [
            "estimate-bare-forecast", "estimate-leaping-forecast"]
        assert "calibrated - The held forecast (estimate-held-forecast)" in (
            result["index_text"])
        estimate = agent.get_estimate_estimate("estimate-leaping-forecast")
        assert estimate_gaps(estimate, agent.estimate_book()) == (
            "steps from recorded to calibrated, which the estimate sequence "
            "does not allow",)
        assert estimate_green(estimate, agent.estimate_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _ESTIMATE_EVENT_TYPES] == []
        agent.close()
