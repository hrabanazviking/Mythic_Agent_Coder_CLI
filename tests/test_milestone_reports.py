"""M-220 Reports - pure-layer tests.

TIER: integration

The pure layer is the reportkeeper, held as data: one
record per report, held whole - the slice it
answers for, named by slice id, its title, the
steps it walked in walk order and the evidence
it carries, held by boundary. The question walk is
explicit - named, gathered, weighed, stated,
reported, with their legal steps held as data -
and a report's standing is derived at call
time: a report that opens anywhere but reached, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet reached reported stands open,
named in its gaps. A report stands only for
an active slice: a report naming no held
slice, or one that is not active, refuses by
name. The report's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, chronicle, trace, order and current
report are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, stated or
reported live. The shipped example book is held
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

from mythic_agent.core.milestone_reports import (
    EXAMPLE_CHECK,
    BARE_CLAIMS,
    HELD_EVIDENCE,
    INDEX_ACTION,
    CHECKS,
    CLAIM_BOUNDARYS,
    TRANSITIONS,
    BOUNDARY_STATES,
    CHECK_FIELDS,
    PLAIN_EXPLANATION,
    REPORT_RESOURCE,
    REPORT_RULE,
    REPORT_SCHEMA,
    REPORT_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    ReportRecord,
    IndexEntry,
    BoundaryRef,
    NoteRecord,
    ReportBook,
    ReportIndex,
    ReportPanel,
    ReportRegistry,
    ReportVerdict,
    ReportView,
    trace_for_report,
    chronicle_record,
    book_record,
    build_trace,
    build_book,
    build_report,
    build_boundary_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_report,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    report_for_check,
    report_gaps,
    report_order,
    report_record,
    report_green,
    reports_for_boundary,
    first_note,
    format_book,
    format_report,
    format_index,
    format_note,
    format_check,
    format_panel,
    format_report_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    boundary_record,
    load_report,
    legal_step,
    load_report_file,
    next_check,
    normalize_check,
    normalize_claim_boundary,
    normalize_boundary_state,
    normalize_stance,
    normalize_view_filter,
    note_for_report,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_report_args,
    green_reports,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_reports,
    validate_book,
    validate_report,
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
EXAMPLE_TITLE = "Milestone reports at the M-220 slice boundary"
EXAMPLE_CHECKS = ["reported", "reported", "reported"]
EXAMPLE_RUN_IDS = (
    "report-held-report", "report-remeasured-report",
    "report-own-report", "report-bare-report",
    "report-leaping-report")
EXAMPLE_TRACE = "reached > gathered > weighed > stated > reported"


def _ref(**overrides):
    fields = {
        "boundary_id": "slice-test",
        "seq": 1,
        "title": "A test slice",
        "state": "live",
        "detail": "A test slice reference held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "report-test",
    }
    fields.update(overrides)
    return build_boundary_ref(fields)


def _report(**overrides):
    fields = {
        "report_id": "report-test",
        "seq": 1,
        "boundary_id": "slice-test",
        "title": "A test report",
        "checks": ["reached", "gathered", "weighed", "stated", "reported"],
        "claims": [],
        "detail": "A test report held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "report-test",
    }
    fields.update(overrides)
    return build_report(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "report-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "report_id": "report-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "report-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "report_id": "report-test",
        "trace": "reached > gathered > weighed > stated > reported",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "report-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(slices=None, reports=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": REPORT_SCHEMA,
        "slice": "M-220",
        "milestone_reports": {"title": "A test report book"},
        "boundaries": [item.to_record() for item in (
            slices if slices is not None else [_ref()])],
        "report_records": [item.to_record() for item in (
            reports if reports is not None else [_report()])],
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
    return _book(reports=[
        _report(),
        _report(report_id="report-hidden", seq=2,
               title="A hidden report", checks=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_report()
    assert book.title == EXAMPLE_TITLE
    assert book.report_ids() == EXAMPLE_RUN_IDS
    assert book.boundary_ids() == (
        "boundary-m219-resumes", "boundary-m220-milestones",
        "boundary-m221-log")
    assert [v.view_id for v in book.views] == [
        "view-reports", "view-reported"]
    assert [m.report_id for m in book.notes] == [
        "report-held-report", "report-bare-report"]
    assert [a.report_id for a in book.traces] == ["report-held-report"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m219-boundary"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.report_ids())
    derived = derive_panel(book, "view-reports")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-reports").verdict == "held"
    assert derive_verdict(book, "view-reports").green_shown == 3
    assert derive_verdict(book, "view-reported").verdict == "reported"
    assert derive_verdict(book, "view-reported").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / REPORT_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == REPORT_SCHEMA
    assert raw["slice"] == "M-220"
    assert "verdict" not in raw
    assert "report_index" not in raw
    assert "chronicle" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-220")]
    assert slice_.title == "Milestone reports"
    assert slice_.part == 9
    assert "at part boundaries the coordinator reports plainly" in slice_.summary
    assert "blocked with what it needs" in slice_.summary
    assert REPORT_SLICE == "M-220"

def test_charter_rows_do_not_name_m220():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-220" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert COMPLETE_WORDS == ("complete", "open")
    assert CHECK_FIELDS == ("checks", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "complete", "open")
    assert VERDICT_WORDS == ("reported", "held", "blocked")
    assert BOUNDARY_STATES == ("live", "dormant")
    assert CHECKS == ("reached", "gathered", "weighed", "stated", "reported")
    assert HELD_EVIDENCE == ("boundary_ref", "evidence_ref", "keeper_record", "report_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_BOUNDARYS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["stated"] == ("reached", "reported")
    assert TRANSITIONS["reported"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_CHECK == "reported"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_boundary_state("LIVE") == "live"
    assert normalize_check("WEIGHED") == "weighed"
    assert normalize_claim_boundary("FEELING") == "feeling"
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    with pytest.raises(ValueError):
        normalize_boundary_state("blessed")
    with pytest.raises(ValueError):
        normalize_check("polish")
    with pytest.raises(ValueError):
        normalize_claim_boundary("weather")
    assert legal_step("weighed", "stated") is True
    assert legal_step("gathered", "reported") is False
    assert legal_step("reported", "reached") is False
    assert next_check("reached") == "gathered"
    assert next_check("weighed") == "stated"
    assert next_check("stated", failed=True) == "reached"
    assert next_check("stated") == "reported"
    assert next_check("reported") is None
    assert "held as data alone" in REPORT_RULE
    assert "report sequence" in REPORT_RULE
    assert "M-220" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /milestones")

def test_shipped_book_judged_honestly_as_data():
    book = load_report()
    opening = book.report_for("report-held-report")
    assert report_green(opening, book) is True
    assert report_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Report: The held report",
        "Boundary: boundary-m219-resumes",
        "Check: reported",
        "Claims: boundary_ref")
    asking = book.report_for("report-bare-report")
    assert report_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert report_green(asking, book) is False
    skipping = book.report_for("report-leaping-report")
    assert report_gaps(skipping, book) == (
        "steps from gathered to reported, which the report sequence "
        "does not allow",)
    assert [g.report_id for g in green_reports(book)] == [
        "report-held-report", "report-remeasured-report", "report-own-report"]
    index = derive_index(book)
    assert [e.check for e in index.entries] == EXAMPLE_CHECKS
    assert index.gaps == ("report-bare-report", "report-leaping-report")
    assert report_for_check(book, EXAMPLE_CHECK).report_id == (
        "report-held-report")
    assert report_for_check(book, "triple report") is None
    assert transition_breaks(book) == (
        "report-leaping-report: gathered > reported",)
    assert [g.report_id for g in report_order(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "report-held-report") == EXAMPLE_TRACE
    assert trace_current(book, "report-held-report") is True
    assert trace_current(book, "report-remeasured-report") is False
    assert trace_for_report(
        book, "report-held-report").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_report(
        book, "report-held-report", "note").note_id == (
            "note-note-first")
    assert note_for_report(book, "report-nope") is None
    assert current_report(book).report_id == "report-bare-report"
    chronicle = chronicle_record(book)
    assert chronicle["standings"] == [
        {"standing": "complete", "report_records": 3},
        {"standing": "open", "report_records": 2}]
    assert chronicle["total"] == 5
    assert chronicle["current_report"] == "report-bare-report"
    assert chronicle["traces"] == [
        {"report_id": "report-held-report", "trace": "current"},
        {"report_id": "report-remeasured-report", "trace": "unheld"},
        {"report_id": "report-own-report", "trace": "unheld"},
        {"report_id": "report-bare-report", "trace": "unheld"},
        {"report_id": "report-leaping-report", "trace": "unheld"}]
    assert chronicle["breaks"] == ["report-leaping-report: gathered > reported"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 223
    assert citizen["next_slice"] == "M-224"
    assert citizen["m220_title"] == "Milestone reports"
    assert citizen["m220_part"] == 9
    assert citizen["m220_status"] == "done"

def test_report_record_round_trips():
    report = _report()
    assert validate_report(report) is report
    rebuilt = build_report(report.to_record())
    assert rebuilt == report
    assert rebuilt.item_id == "report-test"
    assert rebuilt.check == "reported"
    record = report_record(report)
    assert record["type"] == "report_report"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert boundary_record(ref)["type"] == "report_slice"
    assert boundary_record(ref)["state"] == "live"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _report(checks=[])
    assert report_gaps(silent) == (
        "has passed through no step: the report has not started",)
    assert report_green(silent) is False
    walking = _report(checks=["reached", "gathered"])
    assert report_gaps(walking) == (
        "has not reached reported: the report stands at gathered",)
    assert walking.check == "gathered"
    sideways = _report(checks=["gathered", "weighed", "stated", "reported"])
    assert report_gaps(sideways) == (
        "opens at gathered, not at reached: the report opens "
        "with the reflection",)
    repaired = _report(checks=["reached", "gathered", "weighed", "stated", "reached", "gathered", "weighed", "stated", "reported"])
    assert report_gaps(repaired) == ()
    assert report_green(repaired) is True
    with pytest.raises(ValueError):
        _report(checks=[42])
    with pytest.raises(ValueError):
        _report(checks="inspect as a bare string")
    with pytest.raises(ValueError):
        _report(checks=["reached", "polish"])
    with pytest.raises(ValueError):
        _report(claims=["weather"])
    with pytest.raises(ValueError):
        _report(claims="boundary_ref")
    none_report = _report(checks=None, claims=None)
    assert none_report.checks == ()
    assert none_report.claims == ()

def test_report_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "entries", "coverage", "current_report",
                "chronicle", "order"):
        fields = _report().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_report(fields)
    fields = _report().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_report(fields)


def test_report_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _report().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_report(fields)


def test_report_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _report(title="")
    with pytest.raises(ValueError):
        _report(boundary_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "reached > gathered > weighed > stated > reported"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_reports_own_fields():
    report = _report(claims=["boundary_ref"])
    assert plain_lines(report) == (
        "Report: A test report",
        "Boundary: slice-test",
        "Check: reported",
        "Claims: boundary_ref")
    segment = segment_of(report)
    assert segment.startswith("report-test: A test report")
    assert "check: 'reported'" in segment
    assert "gaps: none" in segment
    assert plain_words(report).startswith(
        "A test report - from slice-test")

def test_red_reports_stand_named_in_their_gaps():
    asking = _report(claims=["feeling", "boundary_ref", "summary"])
    assert report_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert report_green(asking) is False
    skipping = _report(checks=["reached", "gathered", "reported"])
    assert report_gaps(skipping) == (
        "steps from gathered to reported, which the report sequence "
        "does not allow",)
    book = _book(reports=[
        _report(),
        _report(report_id="report-skipping", seq=2,
             checks=["reached", "gathered", "reported"]),
    ])
    assert transition_breaks(book) == (
        "report-skipping: gathered > reported",)
    assert current_report(book).report_id == "report-skipping"
    assert [g.report_id for g in report_order(book)] == [
        "report-test", "report-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "report_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "report_note"
    assert record["report_id"] == "report-test"
    assert view_plain_words(view) == "View view-test: shows all reports."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_reports_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.check for e in index.entries] == ["reported"]
    assert index.entries[0] == IndexEntry(
        check="reported",
        report_id="report-test", title="A test report")
    assert index.gaps == ("report-hidden",)
    record = index_record(book)
    assert record["type"] == "report_index"
    assert record["gaps"] == ["report-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "report_book"

def test_check_target_reaches_its_report_and_an_unheld_target_reaches_nothing():
    book = load_report()
    assert report_for_check(book, "reported").report_id == (
        "report-held-report")
    assert report_for_check(book, "") is None
    assert report_for_check(book, None) is None
    assert report_for_check(book, "not held at all") is None
    text = format_check(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_report()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Report note note report-held-report" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").report_id == "report-test"
    assert note_for_report(book, "report-test").note_id == "note-test"
    assert note_for_report(book, "report-test", "praise") is None
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
    row = build_row(None, _report(), book)
    assert row.standing == "complete"
    assert validate_row(row, _report(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_reports():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "report_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "reported"
    empty_book = _book(reports=[_report(checks=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(ReportVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_report()
    assert [g.report_id for g in shown_reports(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.report_id for g in shown_reports(book, "view-reported")] == [
        "report-held-report", "report-remeasured-report", "report-own-report"]
    assert [g.report_id for g in reports_for_boundary(
        book, "boundary-m220-milestones")] == [
            "report-own-report", "report-bare-report",
            "report-leaping-report"]
    assert reports_for_boundary(book, "slice-nope") == ()
    assert current_report(_mixed_book()).report_id == "report-hidden"
    assert current_report(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "report-test") == (
        "reached > gathered > weighed > stated > reported")
    assert trace_current(stale, "report-test") is False
    assert chronicle_record(stale)["traces"] == [
        {"report_id": "report-test", "trace": "stale"}]

def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(reports=[_report(), _report(seq=2)])
    with pytest.raises(ValueError):
        _book(reports=[_report(), _report(report_id="report-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(reports=[_report(boundary_id="slice-nope")])
    with pytest.raises(ValueError):
        _book(slices=[_ref(), _ref(
            boundary_id="slice-cold", seq=2, state="dormant")],
            reports=[_report(boundary_id="slice-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(boundary_id="slice-nope")])
    fields = {
        "schema": REPORT_SCHEMA, "slice": "M-220",
        "milestone_reports": {"title": "A weighed book"},
        "slices": [_ref().to_record()],
        "report_records": [_report().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "reported"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_report"] = "report-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_report")
    fields["trace"] = "report-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / REPORT_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "milestone_reports.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_report_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.report_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = ReportRegistry()
    assert registry.title() is None
    registry.register_boundary_ref(_ref())
    registry.register_report(_report())
    registry.register_view(_view())
    assert [g.report_id for g in registry.list_reports()] == ["report-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_report("report-test").title == "A test report"
    assert registry.get_slice("slice-test").state == "live"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("report-test").report_id == "report-test"
    with pytest.raises(ValueError):
        registry.register_report(_report(seq=9))
    with pytest.raises(ValueError):
        registry.register_report(_report(report_id="report-two"))
    with pytest.raises(KeyError):
        registry.get_report("report-nope")
    assert registry.book().title == "An unheld report book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = ReportRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test report book"
    assert registry.title() == "A test report book"
    assert len(registry.list_reports()) == 2
    other = ReportRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    report = _report()
    assert "A test report" in plain_words(report)
    assert panel_plain_words(_mixed_book()).startswith(
        "The report book holds 2 reports")
    assert verdict_plain_words(_mixed_book()) == (
        "The reports stand held: 1 of 2 shown reports stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green reports; red, "
        "named in its gaps: report-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_report(report)
    assert "Report: A test report" in text
    assert "stands complete" in text
    text = format_report(_report(checks=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Report Gate (M-220) - A test report book" in book_text
    assert "report-hidden" in format_book(_mixed_book(), "slice-test")
    assert "Report panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "reported - A test report (report-test)" in index_text
    assert "report-hidden" in index_text
    screen = format_report_screen()
    assert "The Report Gate (M-220)" in screen
    assert "report-bare-report" in screen

def test_parse_args_well_and_loader_targets():
    assert parse_report_args("") == ("show", None)
    assert parse_report_args(None) == ("show", None)
    assert parse_report_args("show") == ("show", None)
    assert parse_report_args("report report-test") == (
        "report", "report-test")
    assert parse_report_args("check reported") == (
        "check", "reported")
    assert parse_report_args("boundary slice-test") == (
        "boundary", "slice-test")
    assert parse_report_args("view view-test") == ("view", "view-test")
    assert parse_report_args("note note-test") == ("note", "note-test")
    assert parse_report_args("index") == ("index", None)
    assert parse_report_args("panel") == ("panel", None)
    assert parse_report_args("verdict") == ("verdict", None)
    for bad in ("dance", "report", "check", "slice", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_report_args(bad)
    chronicle = chronicle_record()
    assert chronicle["type"] == "report_well"
    assert chronicle["total"] == 5
    assert chronicle["current_report"] == "report-bare-report"
    book = load_report({
        "schema": REPORT_SCHEMA, "slice": "M-220",
        "milestone_reports": {"title": "A weighed book"},
        "slices": [_ref().to_record()],
        "report_records": [_report().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, ReportBook)
    assert book.title == "A weighed book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_report({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_report({"slice": "M-999"})
    built = build_report(
        report_id="report-kw", seq=3, boundary_id="slice-test",
        title="Kw Report", checks=["reached", "gathered", "weighed", "stated", "reported"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="report-test")
    assert built.report_id == "report-kw"
    assert report_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-220 agent layer: the agent holds a report
# book for the session, reports and views are
# published as session news through the
# checkpoint target (chronicle first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held reports, the chronicle is derived from
# the held reports' completeness, the roadmap standing
# is read from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no slice. This layer reports
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session chronicle news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_REPORT_EVENT_TYPES = (
    "report_report", "report_slice", "report_view",
    "report_panel", "report_verdict")


def _report_events(store, session_id, boundary):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == boundary]


def _write_milestone_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / REPORT_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "milestone_reports.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestReportAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.milestone_status()
        assert status["report_records"] == []
        assert status["slices"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["milestone_book"]["title"] == EXAMPLE_TITLE
        assert len(status["milestone_book"]["slices"]) == 3
        assert len(status["milestone_book"]["report_records"]) == 5
        assert len(status["milestone_book"]["views"]) == 2
        assert len(status["milestone_book"]["notes"]) == 2
        assert len(status["milestone_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m219-boundary"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["check"] for e in status["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert status["index"]["gaps"] == [
            "report-bare-report", "report-leaping-report"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["chronicle"]["total"] == 5
        assert status["chronicle"]["current_report"] == "report-bare-report"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 223
        assert status["roadmap"]["next_slice"] == "M-224"
        assert status["roadmap"]["m220_title"] == "Milestone reports"
        assert "held as data alone" in status["rule"]
        assert "report-bare-report" in status["plain_words"]
        assert "The Report Gate (M-220)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._milestone_registry()
        assert agent._milestone_registry() is first
        assert agent._milestone_store is first
        for name in ("milestone_book", "milestone_status", "milestone_panel",
                     "milestone_verdict", "milestone_index", "report_milestone"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_milestone_registry", "milestone_book", "milestone_status",
            "get_milestone_report", "get_milestone_view", "get_milestone_note",
            "milestone_reports_for_boundary", "milestone_reports_green",
            "milestone_panel", "milestone_verdict", "milestone_index",
            "register_milestone_report", "register_milestone_view",
            "view_milestone", "register_milestone_book",
            "record_milestone_book", "report_milestone",
            "_publish_milestone_record", "_milestone_screen",
            "_milestone_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.milestone_status()
        assert agent.get_milestone_report(
            "report-held-report").title == "The held report"
        assert agent.get_milestone_view(
            "view-reports").view_filter == "all"
        assert agent.get_milestone_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.report_id for d in agent.milestone_reports_for_boundary(
            "boundary-m220-milestones")] == [
            "report-own-report", "report-bare-report",
            "report-leaping-report"]
        assert [d.report_id for d in agent.milestone_reports_green()] == [
            "report-held-report", "report-remeasured-report", "report-own-report"]
        agent.milestone_panel()
        agent.milestone_verdict()
        agent.milestone_index()
        agent.report_milestone()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _REPORT_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_milestone_report("report-nope")
        with pytest.raises(KeyError):
            agent.get_milestone_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_milestone_note("note-nope")
        with pytest.raises(ValueError):
            agent.milestone_reports_for_boundary("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_milestone_report(_report())
        status = agent.milestone_status()
        assert [d["report_id"] for d in status["report_records"]] == ["report-test"]
        assert status["book"]["title"] == "An unheld report book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["check"] for e in status["index"]["entries"]] == [
            "reported"]
        assert status["first_note"] is None
        assert "report-test" in status["screen"]
    def test_held_report_never_falls_back_to_the_example(
            self, agent):
        agent.register_milestone_report(_report())
        with pytest.raises(KeyError):
            agent.get_milestone_report("report-held-report")
        with pytest.raises(KeyError):
            agent.get_milestone_view("view-reports")
        with pytest.raises(KeyError):
            agent.get_milestone_note("note-note-first")
        report = agent.get_milestone_report("report-test")
        assert report.title == "A test report"
        assert agent.milestone_book().title == (
            "An unheld report book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_milestone_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.report_id == "report-held-report"
        status = agent.milestone_status()
        assert status["index"]["gaps"] == [
            "report-bare-report", "report-leaping-report"]
        assert status["first_note"]["report_id"] == (
            "report-held-report")
        assert status["first_note"]["stance"] == "note"

class TestReportAgentHolding:
    def test_register_report_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_milestone_report(_report())
        assert result["report"]["report_id"] == "report-test"
        assert result["record_news"]["type"] == "report_report"
        assert "report-test" in result["screen"]
        events = _report_events(store, session_id, "report_report")
        assert len(events) == 1
        agent.close()

    def test_duplicate_report_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_milestone_report(_report())
        with pytest.raises(ValueError):
            agent.register_milestone_report(_report(seq=9))
        with pytest.raises(ValueError):
            agent.register_milestone_report(_report(report_id="report-two"))
        events = _report_events(store, session_id, "report_report")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_milestone_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_report_events(
            store, session_id, "report_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_milestone_report(_report())
        result = agent.view_milestone("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "report_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "reported"
        assert len(_report_events(
            store, session_id, "report_view")) == 1
        assert len(_report_events(
            store, session_id, "report_panel")) == 1
        assert len(_report_events(
            store, session_id, "report_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_milestone_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "report_slice", "report_report", "report_view"]
        assert len(_report_events(
            store, session_id, "report_report")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_milestone_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "report_panel"
        assert result["index_record"]["gaps"] == [
            "report-bare-report", "report-leaping-report"]
        with pytest.raises(ValueError):
            agent.record_milestone_book()
        assert len(_report_events(
            store, session_id, "report_slice")) == 3
        assert len(_report_events(
            store, session_id, "report_report")) == 5
        assert len(_report_events(
            store, session_id, "report_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_milestone_book_file(tmp_path)
        book = load_report_file(path)
        result = agent.record_milestone_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_boundaryrt_renders_example_then_held_book_only(self, agent):
        report = agent.report_milestone()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "held"
        assert report["index"]["gaps"] == [
            "report-bare-report", "report-leaping-report"]
        assert "report-held-report" in report["book_text"]
        assert "reported - The held report (report-held-report)" in report["index_text"]
        agent.register_milestone_report(_report())
        report = agent.report_milestone()
        assert report["book"]["title"] == "An unheld report book"
        assert report["panel"] is None
        assert report["verdict"] is None

class TestReportTerminalHeading:
    def test_show_report_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/milestones")
        assert "The Report Gate (M-220)" in text
        _, _, text = _slash(agent, "/milestones report report-held-report")
        assert "Report: The held report" in text
        _, _, text = _slash(
            agent, "/milestones check reported")
        assert "Report: The held report" in text
        _, _, text = _slash(agent, "/milestones check triple report")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/milestones boundary boundary-m220-milestones")
        assert "report-bare-report" in text
        assert "report-held-report" not in text
        _, _, text = _slash(agent, "/milestones view view-reports")
        assert "filter all" in text
        _, _, text = _slash(agent, "/milestones note note-note-first")
        assert "Report note note report-held-report" in text
        _, _, text = _slash(agent, "/milestones index")
        assert "Report index" in text
        assert "report-bare-report" in text
        _, _, text = _slash(agent, "/milestones panel")
        assert "Report panel under view view-reports" in text
        _, _, text = _slash(agent, "/milestones verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/milestones [show|report <report-id>"
                "|check <check>|boundary <boundary-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/milestones dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/milestones report report-nope")
        assert "no report named" in text
@pytest.fixture()
def report_handler(agent, monkeypatch):
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


def _report_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestReportCommand:
    def test_show_is_default(self, report_handler, agent):
        report_handler._handle_milestone("")
        assert "The Report Gate (M-220)" in (
            _report_published_text(report_handler))

    def test_report_check_slice_view_note_index_panel_verdict(
            self, report_handler, agent):
        report_handler._handle_milestone("report report-held-report")
        assert "Report: The held report" in _report_published_text(
            report_handler)
        report_handler._handle_milestone(
            "check reported")
        assert "Report: The held report" in _report_published_text(
            report_handler)
        report_handler._handle_milestone("boundary boundary-m220-milestones")
        assert "report-bare-report" in _report_published_text(
            report_handler)
        report_handler._handle_milestone("view view-reports")
        assert "filter all" in _report_published_text(report_handler)
        report_handler._handle_milestone("note note-note-first")
        assert "Report note note report-held-report" in (
            _report_published_text(report_handler))
        report_handler._handle_milestone("index")
        assert "Report index" in _report_published_text(report_handler)
        report_handler._handle_milestone("panel")
        assert "Report panel under view" in _report_published_text(
            report_handler)
        report_handler._handle_milestone("verdict")
        assert "held" in _report_published_text(report_handler)
    def test_bad_grammar_is_published(
            self, report_handler, agent):
        report_handler._handle_milestone("dance party")
        assert USAGE in _report_published_text(report_handler)
        report_handler._handle_milestone("report report-nope")
        assert "no report named" in _report_published_text(
            report_handler)


class TestChatScreenRoutingReport:
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
        screen.handle_command("/milestones panel", _FakeLog())
        assert calls == [("/milestones", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/milestones[/green] - show the Report gate (M-220)" in (
            text)
        assert ('"/milestones": "Usage: /milestones | '
                '/milestones report <report-id>') in text

class TestReportDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.milestone_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-reports"
        verdict = agent.milestone_verdict()
        assert verdict.verdict == "held"
        found = agent.milestone_verdict("view-reported")
        assert found.verdict == "reported"
        assert found.green_shown == 3
        agent.register_milestone_report(_report())
        with pytest.raises(ValueError):
            agent.milestone_panel()
        with pytest.raises(ValueError):
            agent.milestone_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_milestone_report(_report(checks=[]))
        result = agent.view_milestone("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.milestone_index()
        assert [e["check"] for e in result["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert result["index"]["gaps"] == [
            "report-bare-report", "report-leaping-report"]
        assert "reported - The held report (report-held-report)" in (
            result["index_text"])
        report = agent.get_milestone_report("report-leaping-report")
        assert report_gaps(report, agent.milestone_book()) == (
            "steps from gathered to reported, which the report sequence "
            "does not allow",)
        assert report_green(report, agent.milestone_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _REPORT_EVENT_TYPES] == []
        agent.close()
