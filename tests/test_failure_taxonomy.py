"""M-223 Failures - pure-layer tests.

TIER: integration

The pure layer is the taxonomist, held as data: one
record per failure, held whole - the run it
answers for, named by run id, its title, the
steps it walked in walk order and the evidence
it carries, held by run. The question walk is
explicit - named, tagged, classed, remedied,
learned, with their legal steps held as data -
and a failure's standing is derived at call
time: a failure that opens anywhere but spotted, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet spotted learned stands open,
named in its gaps. A failure stands only for
an active run: a failure naming no held
run, or one that is not active, refuses by
name. The failure's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, ledger, trace, order and current
failure are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, remedied or
learned live. The shipped example book is held
in a data file, and a loader reads a book from
any file. No charter row names this run: the
M-171 TUI charter binds Part VIII alone, and the
M-005 method charter names the whole of Part IX
as the part that executes it, both pinned live
below.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.failure_taxonomy import (
    EXAMPLE_STAGE,
    BARE_CLAIMS,
    HELD_EVIDENCE,
    INDEX_ACTION,
    STAGES,
    CLAIM_RUNS,
    TRANSITIONS,
    RUN_STATES,
    STAGE_FIELDS,
    PLAIN_EXPLANATION,
    FAILURE_RESOURCE,
    FAILURE_RULE,
    FAILURE_SCHEMA,
    FAILURE_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    FailureRecord,
    IndexFailure,
    RunRef,
    NoteRecord,
    FailureBook,
    FailureIndex,
    FailurePanel,
    FailureRegistry,
    FailureVerdict,
    FailureView,
    trace_for_failure,
    ledger_record,
    book_record,
    build_trace,
    build_book,
    build_failure,
    build_run_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_failure,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    failure_for_check,
    failure_gaps,
    failure_order,
    failure_record,
    failure_green,
    failures_for_run,
    first_note,
    format_book,
    format_failure,
    format_index,
    format_note,
    format_stage,
    format_panel,
    format_failure_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    run_record,
    load_failure,
    legal_step,
    load_failure_file,
    next_stage,
    normalize_stage,
    normalize_claim_run,
    normalize_run_state,
    normalize_stance,
    normalize_view_filter,
    note_for_failure,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_failure_args,
    green_failures,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_failures,
    validate_book,
    validate_failure,
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
EXAMPLE_TITLE = "Failure taxonomy at the M-223 slice run"
EXAMPLE_STAGES = ["learned", "learned", "learned"]
EXAMPLE_RUN_IDS = (
    "failure-held-failure", "failure-retried-failure",
    "failure-own-failure", "failure-bare-failure",
    "failure-leaping-failure")
EXAMPLE_TRACE = "spotted > tagged > classed > remedied > learned"


def _ref(**overrides):
    fields = {
        "run_id": "run-test",
        "seq": 1,
        "title": "A test run",
        "state": "live",
        "detail": "A test run reference held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "failure-test",
    }
    fields.update(overrides)
    return build_run_ref(fields)


def _failure(**overrides):
    fields = {
        "failure_id": "failure-test",
        "seq": 1,
        "run_id": "run-test",
        "title": "A test failure",
        "stages": ["spotted", "tagged", "classed", "remedied", "learned"],
        "claims": [],
        "detail": "A test failure held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "failure-test",
    }
    fields.update(overrides)
    return build_failure(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "failure-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "failure_id": "failure-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "failure-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "failure_id": "failure-test",
        "trace": "spotted > tagged > classed > remedied > learned",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "failure-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(runs=None, failures=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": FAILURE_SCHEMA,
        "run": "M-223",
        "failure_taxonomy": {"title": "A test failure book"},
        "runs": [item.to_record() for item in (
            runs if runs is not None else [_ref()])],
        "failure_records": [item.to_record() for item in (
            failures if failures is not None else [_failure()])],
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
    return _book(failures=[
        _failure(),
        _failure(failure_id="failure-hidden", seq=2,
               title="A hidden failure", stages=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_failure()
    assert book.title == EXAMPLE_TITLE
    assert book.failure_ids() == EXAMPLE_RUN_IDS
    assert book.run_ids() == (
        "run-m222-selfmod", "run-m223-taxonomy",
        "run-m224-dryrun")
    assert [v.view_id for v in book.views] == [
        "view-failures", "view-learned"]
    assert [m.failure_id for m in book.notes] == [
        "failure-held-failure", "failure-bare-failure"]
    assert [a.failure_id for a in book.traces] == ["failure-held-failure"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m222-run"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.failure_ids())
    derived = derive_panel(book, "view-failures")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-failures").verdict == "held"
    assert derive_verdict(book, "view-failures").green_shown == 3
    assert derive_verdict(book, "view-learned").verdict == "learned"
    assert derive_verdict(book, "view-learned").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / FAILURE_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == FAILURE_SCHEMA
    assert raw["run"] == "M-223"
    assert "verdict" not in raw
    assert "failure_index" not in raw
    assert "ledger" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-223")]
    assert slice_.title == "Failure taxonomy"
    assert slice_.part == 9
    assert "slice failures classified (code, test, environment, provider, scope)" in slice_.summary
    assert "the loop learns its own weather" in slice_.summary
    assert FAILURE_SLICE == "M-223"

def test_charter_rows_do_not_name_m223():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-223" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert COMPLETE_WORDS == ("complete", "open")
    assert STAGE_FIELDS == ("stages", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "complete", "open")
    assert VERDICT_WORDS == ("learned", "held", "blocked")
    assert RUN_STATES == ("live", "dormant")
    assert STAGES == ("spotted", "tagged", "classed", "remedied", "learned")
    assert HELD_EVIDENCE == ("run_ref", "class_ref", "keeper_record", "failure_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_RUNS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["remedied"] == ("spotted", "learned")
    assert TRANSITIONS["learned"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_STAGE == "learned"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_run_state("LIVE") == "live"
    assert normalize_stage("CLASSED") == "classed"
    assert normalize_claim_run("FEELING") == "feeling"
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    with pytest.raises(ValueError):
        normalize_run_state("blessed")
    with pytest.raises(ValueError):
        normalize_stage("polish")
    with pytest.raises(ValueError):
        normalize_claim_run("weather")
    assert legal_step("classed", "remedied") is True
    assert legal_step("tagged", "learned") is False
    assert legal_step("learned", "spotted") is False
    assert next_stage("spotted") == "tagged"
    assert next_stage("classed") == "remedied"
    assert next_stage("remedied", failed=True) == "spotted"
    assert next_stage("remedied") == "learned"
    assert next_stage("learned") is None
    assert "held as data alone" in FAILURE_RULE
    assert "failure sequence" in FAILURE_RULE
    assert "M-223" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /failures")

def test_shipped_book_judged_honestly_as_data():
    book = load_failure()
    opening = book.failure_for("failure-held-failure")
    assert failure_green(opening, book) is True
    assert failure_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Failure: The held failure",
        "Run: run-m222-selfmod",
        "Stage: learned",
        "Claims: run_ref")
    asking = book.failure_for("failure-bare-failure")
    assert failure_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert failure_green(asking, book) is False
    skipping = book.failure_for("failure-leaping-failure")
    assert failure_gaps(skipping, book) == (
        "steps from tagged to learned, which the failure sequence "
        "does not allow",)
    assert [g.failure_id for g in green_failures(book)] == [
        "failure-held-failure", "failure-retried-failure", "failure-own-failure"]
    index = derive_index(book)
    assert [e.stage for e in index.failures] == EXAMPLE_STAGES
    assert index.gaps == ("failure-bare-failure", "failure-leaping-failure")
    assert failure_for_check(book, EXAMPLE_STAGE).failure_id == (
        "failure-held-failure")
    assert failure_for_check(book, "triple failure") is None
    assert transition_breaks(book) == (
        "failure-leaping-failure: tagged > learned",)
    assert [g.failure_id for g in failure_order(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "failure-held-failure") == EXAMPLE_TRACE
    assert trace_current(book, "failure-held-failure") is True
    assert trace_current(book, "failure-retried-failure") is False
    assert trace_for_failure(
        book, "failure-held-failure").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_failure(
        book, "failure-held-failure", "note").note_id == (
            "note-note-first")
    assert note_for_failure(book, "failure-nope") is None
    assert current_failure(book).failure_id == "failure-bare-failure"
    ledger = ledger_record(book)
    assert ledger["standings"] == [
        {"standing": "complete", "failure_records": 3},
        {"standing": "open", "failure_records": 2}]
    assert ledger["total"] == 5
    assert ledger["current_failure"] == "failure-bare-failure"
    assert ledger["traces"] == [
        {"failure_id": "failure-held-failure", "trace": "current"},
        {"failure_id": "failure-retried-failure", "trace": "unheld"},
        {"failure_id": "failure-own-failure", "trace": "unheld"},
        {"failure_id": "failure-bare-failure", "trace": "unheld"},
        {"failure_id": "failure-leaping-failure", "trace": "unheld"}]
    assert ledger["breaks"] == ["failure-leaping-failure: tagged > learned"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 267
    assert citizen["next_slice"] == "M-268"
    assert citizen["m223_title"] == "Failure taxonomy"
    assert citizen["m223_part"] == 9
    assert citizen["m223_status"] == "done"

def test_failure_record_round_trips():
    failure = _failure()
    assert validate_failure(failure) is failure
    rebuilt = build_failure(failure.to_record())
    assert rebuilt == failure
    assert rebuilt.item_id == "failure-test"
    assert rebuilt.stage == "learned"
    record = failure_record(failure)
    assert record["type"] == "failure_failure"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert run_record(ref)["type"] == "failure_run"
    assert run_record(ref)["state"] == "live"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _failure(stages=[])
    assert failure_gaps(silent) == (
        "has passed through no step: the failure has not started",)
    assert failure_green(silent) is False
    walking = _failure(stages=["spotted", "tagged"])
    assert failure_gaps(walking) == (
        "has not reached learned: the failure stands at tagged",)
    assert walking.stage == "tagged"
    sideways = _failure(stages=["tagged", "classed", "remedied", "learned"])
    assert failure_gaps(sideways) == (
        "opens at tagged, not at spotted: the failure opens "
        "with the reflection",)
    repaired = _failure(stages=["spotted", "tagged", "classed", "remedied", "spotted", "tagged", "classed", "remedied", "learned"])
    assert failure_gaps(repaired) == ()
    assert failure_green(repaired) is True
    with pytest.raises(ValueError):
        _failure(stages=[42])
    with pytest.raises(ValueError):
        _failure(stages="inspect as a bare string")
    with pytest.raises(ValueError):
        _failure(stages=["spotted", "polish"])
    with pytest.raises(ValueError):
        _failure(claims=["weather"])
    with pytest.raises(ValueError):
        _failure(claims="run_ref")
    none_failure = _failure(stages=None, claims=None)
    assert none_failure.stages == ()
    assert none_failure.claims == ()

def test_failure_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "failures", "coverage", "current_failure",
                "ledger", "order"):
        fields = _failure().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_failure(fields)
    fields = _failure().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_failure(fields)


def test_failure_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _failure().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_failure(fields)


def test_failure_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _failure(title="")
    with pytest.raises(ValueError):
        _failure(run_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "spotted > tagged > classed > remedied > learned"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_failures_own_fields():
    failure = _failure(claims=["run_ref"])
    assert plain_lines(failure) == (
        "Failure: A test failure",
        "Run: run-test",
        "Stage: learned",
        "Claims: run_ref")
    segment = segment_of(failure)
    assert segment.startswith("failure-test: A test failure")
    assert "stage: 'learned'" in segment
    assert "gaps: none" in segment
    assert plain_words(failure).startswith(
        "A test failure - from run-test")

def test_red_failures_stand_named_in_their_gaps():
    asking = _failure(claims=["feeling", "run_ref", "summary"])
    assert failure_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert failure_green(asking) is False
    skipping = _failure(stages=["spotted", "tagged", "learned"])
    assert failure_gaps(skipping) == (
        "steps from tagged to learned, which the failure sequence "
        "does not allow",)
    book = _book(failures=[
        _failure(),
        _failure(failure_id="failure-skipping", seq=2,
             stages=["spotted", "tagged", "learned"]),
    ])
    assert transition_breaks(book) == (
        "failure-skipping: tagged > learned",)
    assert current_failure(book).failure_id == "failure-skipping"
    assert [g.failure_id for g in failure_order(book)] == [
        "failure-test", "failure-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "failure_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "failure_note"
    assert record["failure_id"] == "failure-test"
    assert view_plain_words(view) == "View view-test: shows all failures."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_failures_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.stage for e in index.failures] == ["learned"]
    assert index.failures[0] == IndexFailure(
        stage="learned",
        failure_id="failure-test", title="A test failure")
    assert index.gaps == ("failure-hidden",)
    record = index_record(book)
    assert record["type"] == "failure_index"
    assert record["gaps"] == ["failure-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "failure_book"

def test_check_target_reaches_its_failure_and_an_unheld_target_reaches_nothing():
    book = load_failure()
    assert failure_for_check(book, "learned").failure_id == (
        "failure-held-failure")
    assert failure_for_check(book, "") is None
    assert failure_for_check(book, None) is None
    assert failure_for_check(book, "not held at all") is None
    text = format_stage(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_failure()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Failure note note failure-held-failure" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").failure_id == "failure-test"
    assert note_for_failure(book, "failure-test").note_id == "note-test"
    assert note_for_failure(book, "failure-test", "praise") is None
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
    row = build_row(None, _failure(), book)
    assert row.standing == "complete"
    assert validate_row(row, _failure(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_failures():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "failure_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "learned"
    empty_book = _book(failures=[_failure(stages=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(FailureVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_failure()
    assert [g.failure_id for g in shown_failures(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.failure_id for g in shown_failures(book, "view-learned")] == [
        "failure-held-failure", "failure-retried-failure", "failure-own-failure"]
    assert [g.failure_id for g in failures_for_run(
        book, "run-m223-taxonomy")] == [
            "failure-own-failure", "failure-bare-failure",
            "failure-leaping-failure"]
    assert failures_for_run(book, "run-nope") == ()
    assert current_failure(_mixed_book()).failure_id == "failure-hidden"
    assert current_failure(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "failure-test") == (
        "spotted > tagged > classed > remedied > learned")
    assert trace_current(stale, "failure-test") is False
    assert ledger_record(stale)["traces"] == [
        {"failure_id": "failure-test", "trace": "stale"}]

def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(failures=[_failure(), _failure(seq=2)])
    with pytest.raises(ValueError):
        _book(failures=[_failure(), _failure(failure_id="failure-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(failures=[_failure(run_id="run-nope")])
    with pytest.raises(ValueError):
        _book(runs=[_ref(), _ref(
            run_id="run-cold", seq=2, state="dormant")],
            failures=[_failure(run_id="run-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(run_id="run-nope")])
    fields = {
        "schema": FAILURE_SCHEMA, "run": "M-223",
        "failure_taxonomy": {"title": "A classed book"},
        "runs": [_ref().to_record()],
        "failure_records": [_failure().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "learned"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_failure"] = "failure-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_failure")
    fields["trace"] = "failure-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / FAILURE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "failure_taxonomy.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_failure_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.failure_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = FailureRegistry()
    assert registry.title() is None
    registry.register_run_ref(_ref())
    registry.register_failure(_failure())
    registry.register_view(_view())
    assert [g.failure_id for g in registry.list_failures()] == ["failure-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_failure("failure-test").title == "A test failure"
    assert registry.get_slice("run-test").state == "live"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("failure-test").failure_id == "failure-test"
    with pytest.raises(ValueError):
        registry.register_failure(_failure(seq=9))
    with pytest.raises(ValueError):
        registry.register_failure(_failure(failure_id="failure-two"))
    with pytest.raises(KeyError):
        registry.get_failure("failure-nope")
    assert registry.book().title == "An unheld failure book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = FailureRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test failure book"
    assert registry.title() == "A test failure book"
    assert len(registry.list_failures()) == 2
    other = FailureRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    failure = _failure()
    assert "A test failure" in plain_words(failure)
    assert panel_plain_words(_mixed_book()).startswith(
        "The failure book holds 2 failures")
    assert verdict_plain_words(_mixed_book()) == (
        "The failures stand held: 1 of 2 shown failures stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green failures; red, "
        "named in its gaps: failure-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_failure(failure)
    assert "Failure: A test failure" in text
    assert "stands complete" in text
    text = format_failure(_failure(stages=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Failure Gate (M-223) - A test failure book" in book_text
    assert "failure-hidden" in format_book(_mixed_book(), "run-test")
    assert "Failure panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "learned - A test failure (failure-test)" in index_text
    assert "failure-hidden" in index_text
    screen = format_failure_screen()
    assert "The Failure Gate (M-223)" in screen
    assert "failure-bare-failure" in screen

def test_parse_args_well_and_loader_targets():
    assert parse_failure_args("") == ("show", None)
    assert parse_failure_args(None) == ("show", None)
    assert parse_failure_args("show") == ("show", None)
    assert parse_failure_args("failure failure-test") == (
        "failure", "failure-test")
    assert parse_failure_args("stage learned") == (
        "stage", "learned")
    assert parse_failure_args("run run-test") == (
        "run", "run-test")
    assert parse_failure_args("view view-test") == ("view", "view-test")
    assert parse_failure_args("note note-test") == ("note", "note-test")
    assert parse_failure_args("index") == ("index", None)
    assert parse_failure_args("panel") == ("panel", None)
    assert parse_failure_args("verdict") == ("verdict", None)
    for bad in ("dance", "failure", "stage", "run", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_failure_args(bad)
    ledger = ledger_record()
    assert ledger["type"] == "failure_well"
    assert ledger["total"] == 5
    assert ledger["current_failure"] == "failure-bare-failure"
    book = load_failure({
        "schema": FAILURE_SCHEMA, "run": "M-223",
        "failure_taxonomy": {"title": "A classed book"},
        "runs": [_ref().to_record()],
        "failure_records": [_failure().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, FailureBook)
    assert book.title == "A classed book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_failure({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_failure({"run": "M-999"})
    built = build_failure(
        failure_id="failure-kw", seq=3, run_id="run-test",
        title="Kw Failure", stages=["spotted", "tagged", "classed", "remedied", "learned"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="failure-test")
    assert built.failure_id == "failure-kw"
    assert failure_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-223 agent layer: the agent holds a failure
# book for the session, failures and views are
# published as session news through the
# checkpoint target (ledger first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held failures, the ledger is derived from
# the held failures' completeness, the roadmap standing
# is remedied from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no run. This layer failures
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session ledger news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_FAILURE_EVENT_TYPES = (
    "failure_failure", "failure_run", "failure_view",
    "failure_panel", "failure_verdict")


def _failure_events(store, session_id, run):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == run]


def _write_failtax_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / FAILURE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "failure_taxonomy.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestFailureAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.failtax_status()
        assert status["failure_records"] == []
        assert status["runs"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["failtax_book"]["title"] == EXAMPLE_TITLE
        assert len(status["failtax_book"]["runs"]) == 3
        assert len(status["failtax_book"]["failure_records"]) == 5
        assert len(status["failtax_book"]["views"]) == 2
        assert len(status["failtax_book"]["notes"]) == 2
        assert len(status["failtax_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m222-run"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["stage"] for e in status["index"]["failures"]] == (
            EXAMPLE_STAGES)
        assert status["index"]["gaps"] == [
            "failure-bare-failure", "failure-leaping-failure"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["ledger"]["total"] == 5
        assert status["ledger"]["current_failure"] == "failure-bare-failure"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 267
        assert status["roadmap"]["next_slice"] == "M-268"
        assert status["roadmap"]["m223_title"] == "Failure taxonomy"
        assert "held as data alone" in status["rule"]
        assert "failure-bare-failure" in status["plain_words"]
        assert "The Failure Gate (M-223)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._failtax_registry()
        assert agent._failtax_registry() is first
        assert agent._failtax_store is first
        for name in ("failtax_book", "failtax_status", "failtax_panel",
                     "failtax_verdict", "failtax_index", "report_failtax"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_failtax_registry", "failtax_book", "failtax_status",
            "get_failtax_failure", "get_failtax_view", "get_failtax_note",
            "failures_for_run", "failures_green",
            "failtax_panel", "failtax_verdict", "failtax_index",
            "register_failtax_failure", "register_failtax_view",
            "view_failtax", "register_failtax_book",
            "record_failtax_book", "report_failtax",
            "_publish_failtax_record", "_failtax_screen",
            "_failtax_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.failtax_status()
        assert agent.get_failtax_failure(
            "failure-held-failure").title == "The held failure"
        assert agent.get_failtax_view(
            "view-failures").view_filter == "all"
        assert agent.get_failtax_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.failure_id for d in agent.failures_for_run(
            "run-m223-taxonomy")] == [
            "failure-own-failure", "failure-bare-failure",
            "failure-leaping-failure"]
        assert [d.failure_id for d in agent.failures_green()] == [
            "failure-held-failure", "failure-retried-failure", "failure-own-failure"]
        agent.failtax_panel()
        agent.failtax_verdict()
        agent.failtax_index()
        agent.report_failtax()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _FAILURE_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_failtax_failure("failure-nope")
        with pytest.raises(KeyError):
            agent.get_failtax_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_failtax_note("note-nope")
        with pytest.raises(ValueError):
            agent.failures_for_run("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_failtax_failure(_failure())
        status = agent.failtax_status()
        assert [d["failure_id"] for d in status["failure_records"]] == ["failure-test"]
        assert status["book"]["title"] == "An unheld failure book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["stage"] for e in status["index"]["failures"]] == [
            "learned"]
        assert status["first_note"] is None
        assert "failure-test" in status["screen"]
    def test_held_failure_never_falls_back_to_the_example(
            self, agent):
        agent.register_failtax_failure(_failure())
        with pytest.raises(KeyError):
            agent.get_failtax_failure("failure-held-failure")
        with pytest.raises(KeyError):
            agent.get_failtax_view("view-failures")
        with pytest.raises(KeyError):
            agent.get_failtax_note("note-note-first")
        failure = agent.get_failtax_failure("failure-test")
        assert failure.title == "A test failure"
        assert agent.failtax_book().title == (
            "An unheld failure book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_failtax_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.failure_id == "failure-held-failure"
        status = agent.failtax_status()
        assert status["index"]["gaps"] == [
            "failure-bare-failure", "failure-leaping-failure"]
        assert status["first_note"]["failure_id"] == (
            "failure-held-failure")
        assert status["first_note"]["stance"] == "note"

class TestFailureAgentHolding:
    def test_register_failure_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_failtax_failure(_failure())
        assert result["failure"]["failure_id"] == "failure-test"
        assert result["record_news"]["type"] == "failure_failure"
        assert "failure-test" in result["screen"]
        events = _failure_events(store, session_id, "failure_failure")
        assert len(events) == 1
        agent.close()

    def test_duplicate_failure_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_failtax_failure(_failure())
        with pytest.raises(ValueError):
            agent.register_failtax_failure(_failure(seq=9))
        with pytest.raises(ValueError):
            agent.register_failtax_failure(_failure(failure_id="failure-two"))
        events = _failure_events(store, session_id, "failure_failure")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_failtax_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_failure_events(
            store, session_id, "failure_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_failtax_failure(_failure())
        result = agent.view_failtax("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "failure_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "learned"
        assert len(_failure_events(
            store, session_id, "failure_view")) == 1
        assert len(_failure_events(
            store, session_id, "failure_panel")) == 1
        assert len(_failure_events(
            store, session_id, "failure_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_failtax_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "failure_run", "failure_failure", "failure_view"]
        assert len(_failure_events(
            store, session_id, "failure_failure")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_failtax_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "failure_panel"
        assert result["index_record"]["gaps"] == [
            "failure-bare-failure", "failure-leaping-failure"]
        with pytest.raises(ValueError):
            agent.record_failtax_book()
        assert len(_failure_events(
            store, session_id, "failure_run")) == 3
        assert len(_failure_events(
            store, session_id, "failure_failure")) == 5
        assert len(_failure_events(
            store, session_id, "failure_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_failtax_book_file(tmp_path)
        book = load_failure_file(path)
        result = agent.record_failtax_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_runrt_renders_example_then_held_book_only(self, agent):
        failure = agent.report_failtax()
        assert failure["book"]["title"] == EXAMPLE_TITLE
        assert failure["verdict"]["verdict"] == "held"
        assert failure["index"]["gaps"] == [
            "failure-bare-failure", "failure-leaping-failure"]
        assert "failure-held-failure" in failure["book_text"]
        assert "learned - The held failure (failure-held-failure)" in failure["index_text"]
        agent.register_failtax_failure(_failure())
        failure = agent.report_failtax()
        assert failure["book"]["title"] == "An unheld failure book"
        assert failure["panel"] is None
        assert failure["verdict"] is None

class TestFailureTerminalHeading:
    def test_show_failure_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/failures")
        assert "The Failure Gate (M-223)" in text
        _, _, text = _slash(agent, "/failures failure failure-held-failure")
        assert "Failure: The held failure" in text
        _, _, text = _slash(
            agent, "/failures stage learned")
        assert "Failure: The held failure" in text
        _, _, text = _slash(agent, "/failures stage triple failure")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/failures run run-m223-taxonomy")
        assert "failure-bare-failure" in text
        assert "failure-held-failure" not in text
        _, _, text = _slash(agent, "/failures view view-failures")
        assert "filter all" in text
        _, _, text = _slash(agent, "/failures note note-note-first")
        assert "Failure note note failure-held-failure" in text
        _, _, text = _slash(agent, "/failures index")
        assert "Failure index" in text
        assert "failure-bare-failure" in text
        _, _, text = _slash(agent, "/failures panel")
        assert "Failure panel under view view-failures" in text
        _, _, text = _slash(agent, "/failures verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/failures [show|failure <failure-id>"
                "|stage <stage>|run <run-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/failures dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/failures failure failure-nope")
        assert "no failure named" in text
@pytest.fixture()
def failure_handler(agent, monkeypatch):
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


def _failure_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestFailureCommand:
    def test_show_is_default(self, failure_handler, agent):
        failure_handler._handle_failtax("")
        assert "The Failure Gate (M-223)" in (
            _failure_published_text(failure_handler))

    def test_failure_check_slice_view_note_index_panel_verdict(
            self, failure_handler, agent):
        failure_handler._handle_failtax("failure failure-held-failure")
        assert "Failure: The held failure" in _failure_published_text(
            failure_handler)
        failure_handler._handle_failtax(
            "stage learned")
        assert "Failure: The held failure" in _failure_published_text(
            failure_handler)
        failure_handler._handle_failtax("run run-m223-taxonomy")
        assert "failure-bare-failure" in _failure_published_text(
            failure_handler)
        failure_handler._handle_failtax("view view-failures")
        assert "filter all" in _failure_published_text(failure_handler)
        failure_handler._handle_failtax("note note-note-first")
        assert "Failure note note failure-held-failure" in (
            _failure_published_text(failure_handler))
        failure_handler._handle_failtax("index")
        assert "Failure index" in _failure_published_text(failure_handler)
        failure_handler._handle_failtax("panel")
        assert "Failure panel under view" in _failure_published_text(
            failure_handler)
        failure_handler._handle_failtax("verdict")
        assert "held" in _failure_published_text(failure_handler)
    def test_bad_grammar_is_published(
            self, failure_handler, agent):
        failure_handler._handle_failtax("dance party")
        assert USAGE in _failure_published_text(failure_handler)
        failure_handler._handle_failtax("failure failure-nope")
        assert "no failure named" in _failure_published_text(
            failure_handler)


class TestChatScreenRoutingFailure:
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
        screen.handle_command("/failures panel", _FakeLog())
        assert calls == [("/failures", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/failures[/green] - show the Failure gate (M-223)" in (
            text)
        assert ('"/failures": "Usage: /failures | '
                '/failures failure <failure-id>') in text

class TestFailureDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.failtax_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-failures"
        verdict = agent.failtax_verdict()
        assert verdict.verdict == "held"
        found = agent.failtax_verdict("view-learned")
        assert found.verdict == "learned"
        assert found.green_shown == 3
        agent.register_failtax_failure(_failure())
        with pytest.raises(ValueError):
            agent.failtax_panel()
        with pytest.raises(ValueError):
            agent.failtax_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_failtax_failure(_failure(stages=[]))
        result = agent.view_failtax("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.failtax_index()
        assert [e["stage"] for e in result["index"]["failures"]] == (
            EXAMPLE_STAGES)
        assert result["index"]["gaps"] == [
            "failure-bare-failure", "failure-leaping-failure"]
        assert "learned - The held failure (failure-held-failure)" in (
            result["index_text"])
        failure = agent.get_failtax_failure("failure-leaping-failure")
        assert failure_gaps(failure, agent.failtax_book()) == (
            "steps from tagged to learned, which the failure sequence "
            "does not allow",)
        assert failure_green(failure, agent.failtax_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _FAILURE_EVENT_TYPES] == []
        agent.close()
