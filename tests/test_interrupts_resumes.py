"""M-219 Resumes - pure-layer tests.

TIER: integration

The pure layer is the resumekeeper, held as data: one
record per resume, held whole - the slice it
answers for, named by slice id, its title, the
steps it walked in walk order and the evidence
it carries, held by pause. The question walk is
explicit - named, journalled, mapped, restated,
resumed, with their legal steps held as data -
and a resume's standing is derived at call
time: a resume that opens anywhere but paused, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet reached resumed stands open,
named in its gaps. A resume stands only for
an active slice: a resume naming no held
slice, or one that is not active, refuses by
name. The resume's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, journal, trace, order and current
resume are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, restated or
resumed live. The shipped example book is held
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

from mythic_agent.core.interrupts_resumes import (
    EXAMPLE_CHECK,
    BARE_CLAIMS,
    HELD_EVIDENCE,
    INDEX_ACTION,
    CHECKS,
    CLAIM_PAUSES,
    TRANSITIONS,
    PAUSE_STATES,
    CHECK_FIELDS,
    PLAIN_EXPLANATION,
    RESUME_RESOURCE,
    RESUME_RULE,
    RESUME_SCHEMA,
    RESUME_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    ResumeRecord,
    IndexEntry,
    PauseRef,
    NoteRecord,
    ResumeBook,
    ResumeIndex,
    ResumePanel,
    ResumeRegistry,
    ResumeVerdict,
    ResumeView,
    trace_for_resume,
    journal_record,
    book_record,
    build_trace,
    build_book,
    build_resume,
    build_pause_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_resume,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    resume_for_check,
    resume_gaps,
    resume_order,
    resume_record,
    resume_green,
    resumes_for_pause,
    first_note,
    format_book,
    format_resume,
    format_index,
    format_note,
    format_check,
    format_panel,
    format_resume_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    pause_record,
    load_resume,
    legal_step,
    load_resume_file,
    next_check,
    normalize_check,
    normalize_claim_pause,
    normalize_pause_state,
    normalize_stance,
    normalize_view_filter,
    note_for_resume,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_resume_args,
    green_resumes,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_resumes,
    validate_book,
    validate_resume,
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
EXAMPLE_TITLE = "Interrupts and resumes across days at the M-219 slice boundary"
EXAMPLE_CHECKS = ["resumed", "resumed", "resumed"]
EXAMPLE_RUN_IDS = (
    "resume-held-resume", "resume-remeasured-resume",
    "resume-own-resume", "resume-bare-resume",
    "resume-leaping-resume")
EXAMPLE_TRACE = "paused > journalled > mapped > restated > resumed"


def _ref(**overrides):
    fields = {
        "pause_id": "slice-test",
        "seq": 1,
        "title": "A test slice",
        "state": "live",
        "detail": "A test slice reference held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "resume-test",
    }
    fields.update(overrides)
    return build_pause_ref(fields)


def _resume(**overrides):
    fields = {
        "resume_id": "resume-test",
        "seq": 1,
        "pause_id": "slice-test",
        "title": "A test resume",
        "checks": ["paused", "journalled", "mapped", "restated", "resumed"],
        "claims": [],
        "detail": "A test resume held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "resume-test",
    }
    fields.update(overrides)
    return build_resume(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "resume-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "resume_id": "resume-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "resume-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "resume_id": "resume-test",
        "trace": "paused > journalled > mapped > restated > resumed",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "resume-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(slices=None, resumes=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": RESUME_SCHEMA,
        "slice": "M-219",
        "interrupts_resumes": {"title": "A test resume book"},
        "pauses": [item.to_record() for item in (
            slices if slices is not None else [_ref()])],
        "resume_records": [item.to_record() for item in (
            resumes if resumes is not None else [_resume()])],
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
    return _book(resumes=[
        _resume(),
        _resume(resume_id="resume-hidden", seq=2,
               title="A hidden resume", checks=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_resume()
    assert book.title == EXAMPLE_TITLE
    assert book.resume_ids() == EXAMPLE_RUN_IDS
    assert book.pause_ids() == (
        "pause-m218-road", "pause-m219-resumes",
        "pause-m220-milestones")
    assert [v.view_id for v in book.views] == [
        "view-resumes", "view-resumed"]
    assert [m.resume_id for m in book.notes] == [
        "resume-held-resume", "resume-bare-resume"]
    assert [a.resume_id for a in book.traces] == ["resume-held-resume"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m218-boundary"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.resume_ids())
    derived = derive_panel(book, "view-resumes")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-resumes").verdict == "held"
    assert derive_verdict(book, "view-resumes").green_shown == 3
    assert derive_verdict(book, "view-resumed").verdict == "resumed"
    assert derive_verdict(book, "view-resumed").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / RESUME_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == RESUME_SCHEMA
    assert raw["slice"] == "M-219"
    assert "verdict" not in raw
    assert "resume_index" not in raw
    assert "journal" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-219")]
    assert slice_.title == "Interrupts and resumes across days"
    assert slice_.part == 9
    assert "a campaign paused mid-slice resumes from journal + map" in slice_.summary
    assert "situation restated in plain words before work continues" in slice_.summary
    assert RESUME_SLICE == "M-219"

def test_charter_rows_do_not_name_m219():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-219" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert COMPLETE_WORDS == ("complete", "open")
    assert CHECK_FIELDS == ("checks", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "complete", "open")
    assert VERDICT_WORDS == ("resumed", "held", "blocked")
    assert PAUSE_STATES == ("live", "dormant")
    assert CHECKS == ("paused", "journalled", "mapped", "restated", "resumed")
    assert HELD_EVIDENCE == ("pause_ref", "journal_ref", "keeper_record", "resume_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_PAUSES == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["restated"] == ("paused", "resumed")
    assert TRANSITIONS["resumed"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_CHECK == "resumed"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_pause_state("LIVE") == "live"
    assert normalize_check("MAPPED") == "mapped"
    assert normalize_claim_pause("FEELING") == "feeling"
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    with pytest.raises(ValueError):
        normalize_pause_state("blessed")
    with pytest.raises(ValueError):
        normalize_check("polish")
    with pytest.raises(ValueError):
        normalize_claim_pause("weather")
    assert legal_step("mapped", "restated") is True
    assert legal_step("journalled", "resumed") is False
    assert legal_step("resumed", "paused") is False
    assert next_check("paused") == "journalled"
    assert next_check("mapped") == "restated"
    assert next_check("restated", failed=True) == "paused"
    assert next_check("restated") == "resumed"
    assert next_check("resumed") is None
    assert "held as data alone" in RESUME_RULE
    assert "resume sequence" in RESUME_RULE
    assert "M-219" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /resumes")

def test_shipped_book_judged_honestly_as_data():
    book = load_resume()
    opening = book.resume_for("resume-held-resume")
    assert resume_green(opening, book) is True
    assert resume_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Resume: The held resume",
        "Pause: pause-m218-road",
        "Check: resumed",
        "Claims: pause_ref")
    asking = book.resume_for("resume-bare-resume")
    assert resume_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert resume_green(asking, book) is False
    skipping = book.resume_for("resume-leaping-resume")
    assert resume_gaps(skipping, book) == (
        "steps from journalled to resumed, which the resume sequence "
        "does not allow",)
    assert [g.resume_id for g in green_resumes(book)] == [
        "resume-held-resume", "resume-remeasured-resume", "resume-own-resume"]
    index = derive_index(book)
    assert [e.check for e in index.entries] == EXAMPLE_CHECKS
    assert index.gaps == ("resume-bare-resume", "resume-leaping-resume")
    assert resume_for_check(book, EXAMPLE_CHECK).resume_id == (
        "resume-held-resume")
    assert resume_for_check(book, "triple resume") is None
    assert transition_breaks(book) == (
        "resume-leaping-resume: journalled > resumed",)
    assert [g.resume_id for g in resume_order(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "resume-held-resume") == EXAMPLE_TRACE
    assert trace_current(book, "resume-held-resume") is True
    assert trace_current(book, "resume-remeasured-resume") is False
    assert trace_for_resume(
        book, "resume-held-resume").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_resume(
        book, "resume-held-resume", "note").note_id == (
            "note-note-first")
    assert note_for_resume(book, "resume-nope") is None
    assert current_resume(book).resume_id == "resume-bare-resume"
    journal = journal_record(book)
    assert journal["standings"] == [
        {"standing": "complete", "resume_records": 3},
        {"standing": "open", "resume_records": 2}]
    assert journal["total"] == 5
    assert journal["current_resume"] == "resume-bare-resume"
    assert journal["traces"] == [
        {"resume_id": "resume-held-resume", "trace": "current"},
        {"resume_id": "resume-remeasured-resume", "trace": "unheld"},
        {"resume_id": "resume-own-resume", "trace": "unheld"},
        {"resume_id": "resume-bare-resume", "trace": "unheld"},
        {"resume_id": "resume-leaping-resume", "trace": "unheld"}]
    assert journal["breaks"] == ["resume-leaping-resume: journalled > resumed"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 263
    assert citizen["next_slice"] == "M-264"
    assert citizen["m219_title"] == "Interrupts and resumes across days"
    assert citizen["m219_part"] == 9
    assert citizen["m219_status"] == "done"

def test_resume_record_round_trips():
    resume = _resume()
    assert validate_resume(resume) is resume
    rebuilt = build_resume(resume.to_record())
    assert rebuilt == resume
    assert rebuilt.item_id == "resume-test"
    assert rebuilt.check == "resumed"
    record = resume_record(resume)
    assert record["type"] == "resume_resume"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert pause_record(ref)["type"] == "resume_slice"
    assert pause_record(ref)["state"] == "live"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _resume(checks=[])
    assert resume_gaps(silent) == (
        "has passed through no step: the resume has not started",)
    assert resume_green(silent) is False
    walking = _resume(checks=["paused", "journalled"])
    assert resume_gaps(walking) == (
        "has not reached resumed: the resume stands at journalled",)
    assert walking.check == "journalled"
    sideways = _resume(checks=["journalled", "mapped", "restated", "resumed"])
    assert resume_gaps(sideways) == (
        "opens at journalled, not at paused: the resume opens "
        "with the reflection",)
    repaired = _resume(checks=["paused", "journalled", "mapped", "restated", "paused", "journalled", "mapped", "restated", "resumed"])
    assert resume_gaps(repaired) == ()
    assert resume_green(repaired) is True
    with pytest.raises(ValueError):
        _resume(checks=[42])
    with pytest.raises(ValueError):
        _resume(checks="inspect as a bare string")
    with pytest.raises(ValueError):
        _resume(checks=["paused", "polish"])
    with pytest.raises(ValueError):
        _resume(claims=["weather"])
    with pytest.raises(ValueError):
        _resume(claims="pause_ref")
    none_resume = _resume(checks=None, claims=None)
    assert none_resume.checks == ()
    assert none_resume.claims == ()

def test_resume_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "entries", "coverage", "current_resume",
                "journal", "order"):
        fields = _resume().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_resume(fields)
    fields = _resume().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_resume(fields)


def test_resume_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _resume().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_resume(fields)


def test_resume_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _resume(title="")
    with pytest.raises(ValueError):
        _resume(pause_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "paused > journalled > mapped > restated > resumed"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_resumes_own_fields():
    resume = _resume(claims=["pause_ref"])
    assert plain_lines(resume) == (
        "Resume: A test resume",
        "Pause: slice-test",
        "Check: resumed",
        "Claims: pause_ref")
    segment = segment_of(resume)
    assert segment.startswith("resume-test: A test resume")
    assert "check: 'resumed'" in segment
    assert "gaps: none" in segment
    assert plain_words(resume).startswith(
        "A test resume - from slice-test")

def test_red_resumes_stand_named_in_their_gaps():
    asking = _resume(claims=["feeling", "pause_ref", "summary"])
    assert resume_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert resume_green(asking) is False
    skipping = _resume(checks=["paused", "journalled", "resumed"])
    assert resume_gaps(skipping) == (
        "steps from journalled to resumed, which the resume sequence "
        "does not allow",)
    book = _book(resumes=[
        _resume(),
        _resume(resume_id="resume-skipping", seq=2,
             checks=["paused", "journalled", "resumed"]),
    ])
    assert transition_breaks(book) == (
        "resume-skipping: journalled > resumed",)
    assert current_resume(book).resume_id == "resume-skipping"
    assert [g.resume_id for g in resume_order(book)] == [
        "resume-test", "resume-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "resume_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "resume_note"
    assert record["resume_id"] == "resume-test"
    assert view_plain_words(view) == "View view-test: shows all resumes."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_resumes_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.check for e in index.entries] == ["resumed"]
    assert index.entries[0] == IndexEntry(
        check="resumed",
        resume_id="resume-test", title="A test resume")
    assert index.gaps == ("resume-hidden",)
    record = index_record(book)
    assert record["type"] == "resume_index"
    assert record["gaps"] == ["resume-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "resume_book"

def test_check_target_reaches_its_resume_and_an_unheld_target_reaches_nothing():
    book = load_resume()
    assert resume_for_check(book, "resumed").resume_id == (
        "resume-held-resume")
    assert resume_for_check(book, "") is None
    assert resume_for_check(book, None) is None
    assert resume_for_check(book, "not held at all") is None
    text = format_check(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_resume()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Resume note note resume-held-resume" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").resume_id == "resume-test"
    assert note_for_resume(book, "resume-test").note_id == "note-test"
    assert note_for_resume(book, "resume-test", "praise") is None
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
    row = build_row(None, _resume(), book)
    assert row.standing == "complete"
    assert validate_row(row, _resume(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_resumes():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "resume_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "resumed"
    empty_book = _book(resumes=[_resume(checks=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(ResumeVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_resume()
    assert [g.resume_id for g in shown_resumes(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.resume_id for g in shown_resumes(book, "view-resumed")] == [
        "resume-held-resume", "resume-remeasured-resume", "resume-own-resume"]
    assert [g.resume_id for g in resumes_for_pause(
        book, "pause-m219-resumes")] == [
            "resume-own-resume", "resume-bare-resume",
            "resume-leaping-resume"]
    assert resumes_for_pause(book, "slice-nope") == ()
    assert current_resume(_mixed_book()).resume_id == "resume-hidden"
    assert current_resume(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "resume-test") == (
        "paused > journalled > mapped > restated > resumed")
    assert trace_current(stale, "resume-test") is False
    assert journal_record(stale)["traces"] == [
        {"resume_id": "resume-test", "trace": "stale"}]

def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(resumes=[_resume(), _resume(seq=2)])
    with pytest.raises(ValueError):
        _book(resumes=[_resume(), _resume(resume_id="resume-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(resumes=[_resume(pause_id="slice-nope")])
    with pytest.raises(ValueError):
        _book(slices=[_ref(), _ref(
            pause_id="slice-cold", seq=2, state="dormant")],
            resumes=[_resume(pause_id="slice-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(pause_id="slice-nope")])
    fields = {
        "schema": RESUME_SCHEMA, "slice": "M-219",
        "interrupts_resumes": {"title": "A mapped book"},
        "slices": [_ref().to_record()],
        "resume_records": [_resume().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "resumed"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_resume"] = "resume-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_resume")
    fields["trace"] = "resume-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / RESUME_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "interrupts_resumes.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_resume_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.resume_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = ResumeRegistry()
    assert registry.title() is None
    registry.register_pause_ref(_ref())
    registry.register_resume(_resume())
    registry.register_view(_view())
    assert [g.resume_id for g in registry.list_resumes()] == ["resume-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_resume("resume-test").title == "A test resume"
    assert registry.get_slice("slice-test").state == "live"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("resume-test").resume_id == "resume-test"
    with pytest.raises(ValueError):
        registry.register_resume(_resume(seq=9))
    with pytest.raises(ValueError):
        registry.register_resume(_resume(resume_id="resume-two"))
    with pytest.raises(KeyError):
        registry.get_resume("resume-nope")
    assert registry.book().title == "An unheld resume book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = ResumeRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test resume book"
    assert registry.title() == "A test resume book"
    assert len(registry.list_resumes()) == 2
    other = ResumeRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    resume = _resume()
    assert "A test resume" in plain_words(resume)
    assert panel_plain_words(_mixed_book()).startswith(
        "The resume book holds 2 resumes")
    assert verdict_plain_words(_mixed_book()) == (
        "The resumes stand held: 1 of 2 shown resumes stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green resumes; red, "
        "named in its gaps: resume-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_resume(resume)
    assert "Resume: A test resume" in text
    assert "stands complete" in text
    text = format_resume(_resume(checks=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Resume Gate (M-219) - A test resume book" in book_text
    assert "resume-hidden" in format_book(_mixed_book(), "slice-test")
    assert "Resume panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "resumed - A test resume (resume-test)" in index_text
    assert "resume-hidden" in index_text
    screen = format_resume_screen()
    assert "The Resume Gate (M-219)" in screen
    assert "resume-bare-resume" in screen

def test_parse_args_well_and_loader_targets():
    assert parse_resume_args("") == ("show", None)
    assert parse_resume_args(None) == ("show", None)
    assert parse_resume_args("show") == ("show", None)
    assert parse_resume_args("resume resume-test") == (
        "resume", "resume-test")
    assert parse_resume_args("check resumed") == (
        "check", "resumed")
    assert parse_resume_args("pause slice-test") == (
        "pause", "slice-test")
    assert parse_resume_args("view view-test") == ("view", "view-test")
    assert parse_resume_args("note note-test") == ("note", "note-test")
    assert parse_resume_args("index") == ("index", None)
    assert parse_resume_args("panel") == ("panel", None)
    assert parse_resume_args("verdict") == ("verdict", None)
    for bad in ("dance", "resume", "check", "slice", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_resume_args(bad)
    journal = journal_record()
    assert journal["type"] == "resume_well"
    assert journal["total"] == 5
    assert journal["current_resume"] == "resume-bare-resume"
    book = load_resume({
        "schema": RESUME_SCHEMA, "slice": "M-219",
        "interrupts_resumes": {"title": "A mapped book"},
        "slices": [_ref().to_record()],
        "resume_records": [_resume().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, ResumeBook)
    assert book.title == "A mapped book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_resume({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_resume({"slice": "M-999"})
    built = build_resume(
        resume_id="resume-kw", seq=3, pause_id="slice-test",
        title="Kw Resume", checks=["paused", "journalled", "mapped", "restated", "resumed"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="resume-test")
    assert built.resume_id == "resume-kw"
    assert resume_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-219 agent layer: the agent holds a resume
# book for the session, resumes and views are
# published as session news through the
# checkpoint target (journal first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held resumes, the journal is derived from
# the held resumes' completeness, the roadmap standing
# is read from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no slice. This layer resumes
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_RESUME_EVENT_TYPES = (
    "resume_resume", "resume_slice", "resume_view",
    "resume_panel", "resume_verdict")


def _resume_events(store, session_id, pause):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == pause]


def _write_daybook_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / RESUME_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "interrupts_resumes.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestResumeAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.daybook_status()
        assert status["resume_records"] == []
        assert status["slices"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["daybook_book"]["title"] == EXAMPLE_TITLE
        assert len(status["daybook_book"]["slices"]) == 3
        assert len(status["daybook_book"]["resume_records"]) == 5
        assert len(status["daybook_book"]["views"]) == 2
        assert len(status["daybook_book"]["notes"]) == 2
        assert len(status["daybook_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m218-boundary"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["check"] for e in status["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert status["index"]["gaps"] == [
            "resume-bare-resume", "resume-leaping-resume"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["journal"]["total"] == 5
        assert status["journal"]["current_resume"] == "resume-bare-resume"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 263
        assert status["roadmap"]["next_slice"] == "M-264"
        assert status["roadmap"]["m219_title"] == "Interrupts and resumes across days"
        assert "held as data alone" in status["rule"]
        assert "resume-bare-resume" in status["plain_words"]
        assert "The Resume Gate (M-219)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._daybook_registry()
        assert agent._daybook_registry() is first
        assert agent._daybook_store is first
        for name in ("daybook_book", "daybook_status", "daybook_panel",
                     "daybook_verdict", "daybook_index", "report_daybook"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_daybook_registry", "daybook_book", "daybook_status",
            "get_daybook_resume", "get_daybook_view", "get_daybook_note",
            "daybook_resumes_for_pause", "daybook_resumes_green",
            "daybook_panel", "daybook_verdict", "daybook_index",
            "register_daybook_resume", "register_daybook_view",
            "view_daybook", "register_daybook_book",
            "record_daybook_book", "report_daybook",
            "_publish_daybook_record", "_daybook_screen",
            "_daybook_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.daybook_status()
        assert agent.get_daybook_resume(
            "resume-held-resume").title == "The held resume"
        assert agent.get_daybook_view(
            "view-resumes").view_filter == "all"
        assert agent.get_daybook_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.resume_id for d in agent.daybook_resumes_for_pause(
            "pause-m219-resumes")] == [
            "resume-own-resume", "resume-bare-resume",
            "resume-leaping-resume"]
        assert [d.resume_id for d in agent.daybook_resumes_green()] == [
            "resume-held-resume", "resume-remeasured-resume", "resume-own-resume"]
        agent.daybook_panel()
        agent.daybook_verdict()
        agent.daybook_index()
        agent.report_daybook()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _RESUME_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_daybook_resume("resume-nope")
        with pytest.raises(KeyError):
            agent.get_daybook_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_daybook_note("note-nope")
        with pytest.raises(ValueError):
            agent.daybook_resumes_for_pause("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_daybook_resume(_resume())
        status = agent.daybook_status()
        assert [d["resume_id"] for d in status["resume_records"]] == ["resume-test"]
        assert status["book"]["title"] == "An unheld resume book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["check"] for e in status["index"]["entries"]] == [
            "resumed"]
        assert status["first_note"] is None
        assert "resume-test" in status["screen"]
    def test_held_resume_never_falls_back_to_the_example(
            self, agent):
        agent.register_daybook_resume(_resume())
        with pytest.raises(KeyError):
            agent.get_daybook_resume("resume-held-resume")
        with pytest.raises(KeyError):
            agent.get_daybook_view("view-resumes")
        with pytest.raises(KeyError):
            agent.get_daybook_note("note-note-first")
        resume = agent.get_daybook_resume("resume-test")
        assert resume.title == "A test resume"
        assert agent.daybook_book().title == (
            "An unheld resume book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_daybook_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.resume_id == "resume-held-resume"
        status = agent.daybook_status()
        assert status["index"]["gaps"] == [
            "resume-bare-resume", "resume-leaping-resume"]
        assert status["first_note"]["resume_id"] == (
            "resume-held-resume")
        assert status["first_note"]["stance"] == "note"

class TestResumeAgentHolding:
    def test_register_resume_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_daybook_resume(_resume())
        assert result["resume"]["resume_id"] == "resume-test"
        assert result["record_news"]["type"] == "resume_resume"
        assert "resume-test" in result["screen"]
        events = _resume_events(store, session_id, "resume_resume")
        assert len(events) == 1
        agent.close()

    def test_duplicate_resume_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_daybook_resume(_resume())
        with pytest.raises(ValueError):
            agent.register_daybook_resume(_resume(seq=9))
        with pytest.raises(ValueError):
            agent.register_daybook_resume(_resume(resume_id="resume-two"))
        events = _resume_events(store, session_id, "resume_resume")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_daybook_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_resume_events(
            store, session_id, "resume_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_daybook_resume(_resume())
        result = agent.view_daybook("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "resume_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "resumed"
        assert len(_resume_events(
            store, session_id, "resume_view")) == 1
        assert len(_resume_events(
            store, session_id, "resume_panel")) == 1
        assert len(_resume_events(
            store, session_id, "resume_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_daybook_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "resume_slice", "resume_resume", "resume_view"]
        assert len(_resume_events(
            store, session_id, "resume_resume")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_daybook_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "resume_panel"
        assert result["index_record"]["gaps"] == [
            "resume-bare-resume", "resume-leaping-resume"]
        with pytest.raises(ValueError):
            agent.record_daybook_book()
        assert len(_resume_events(
            store, session_id, "resume_slice")) == 3
        assert len(_resume_events(
            store, session_id, "resume_resume")) == 5
        assert len(_resume_events(
            store, session_id, "resume_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_daybook_book_file(tmp_path)
        book = load_resume_file(path)
        result = agent.record_daybook_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_pausert_renders_example_then_held_book_only(self, agent):
        report = agent.report_daybook()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "held"
        assert report["index"]["gaps"] == [
            "resume-bare-resume", "resume-leaping-resume"]
        assert "resume-held-resume" in report["book_text"]
        assert "resumed - The held resume (resume-held-resume)" in report["index_text"]
        agent.register_daybook_resume(_resume())
        report = agent.report_daybook()
        assert report["book"]["title"] == "An unheld resume book"
        assert report["panel"] is None
        assert report["verdict"] is None

class TestResumeTerminalHeading:
    def test_show_resume_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/resumes")
        assert "The Resume Gate (M-219)" in text
        _, _, text = _slash(agent, "/resumes resume resume-held-resume")
        assert "Resume: The held resume" in text
        _, _, text = _slash(
            agent, "/resumes check resumed")
        assert "Resume: The held resume" in text
        _, _, text = _slash(agent, "/resumes check triple resume")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/resumes pause pause-m219-resumes")
        assert "resume-bare-resume" in text
        assert "resume-held-resume" not in text
        _, _, text = _slash(agent, "/resumes view view-resumes")
        assert "filter all" in text
        _, _, text = _slash(agent, "/resumes note note-note-first")
        assert "Resume note note resume-held-resume" in text
        _, _, text = _slash(agent, "/resumes index")
        assert "Resume index" in text
        assert "resume-bare-resume" in text
        _, _, text = _slash(agent, "/resumes panel")
        assert "Resume panel under view view-resumes" in text
        _, _, text = _slash(agent, "/resumes verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/resumes [show|resume <resume-id>"
                "|check <check>|pause <pause-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/resumes dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/resumes resume resume-nope")
        assert "no resume named" in text
@pytest.fixture()
def resume_handler(agent, monkeypatch):
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


def _resume_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestResumeCommand:
    def test_show_is_default(self, resume_handler, agent):
        resume_handler._handle_daybook("")
        assert "The Resume Gate (M-219)" in (
            _resume_published_text(resume_handler))

    def test_resume_check_slice_view_note_index_panel_verdict(
            self, resume_handler, agent):
        resume_handler._handle_daybook("resume resume-held-resume")
        assert "Resume: The held resume" in _resume_published_text(
            resume_handler)
        resume_handler._handle_daybook(
            "check resumed")
        assert "Resume: The held resume" in _resume_published_text(
            resume_handler)
        resume_handler._handle_daybook("pause pause-m219-resumes")
        assert "resume-bare-resume" in _resume_published_text(
            resume_handler)
        resume_handler._handle_daybook("view view-resumes")
        assert "filter all" in _resume_published_text(resume_handler)
        resume_handler._handle_daybook("note note-note-first")
        assert "Resume note note resume-held-resume" in (
            _resume_published_text(resume_handler))
        resume_handler._handle_daybook("index")
        assert "Resume index" in _resume_published_text(resume_handler)
        resume_handler._handle_daybook("panel")
        assert "Resume panel under view" in _resume_published_text(
            resume_handler)
        resume_handler._handle_daybook("verdict")
        assert "held" in _resume_published_text(resume_handler)
    def test_bad_grammar_is_published(
            self, resume_handler, agent):
        resume_handler._handle_daybook("dance party")
        assert USAGE in _resume_published_text(resume_handler)
        resume_handler._handle_daybook("resume resume-nope")
        assert "no resume named" in _resume_published_text(
            resume_handler)


class TestChatScreenRoutingResume:
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
        screen.handle_command("/resumes panel", _FakeLog())
        assert calls == [("/resumes", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/resumes[/green] - show the Resume gate (M-219)" in (
            text)
        assert ('"/resumes": "Usage: /resumes | '
                '/resumes resume <resume-id>') in text

class TestResumeDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.daybook_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-resumes"
        verdict = agent.daybook_verdict()
        assert verdict.verdict == "held"
        found = agent.daybook_verdict("view-resumed")
        assert found.verdict == "resumed"
        assert found.green_shown == 3
        agent.register_daybook_resume(_resume())
        with pytest.raises(ValueError):
            agent.daybook_panel()
        with pytest.raises(ValueError):
            agent.daybook_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_daybook_resume(_resume(checks=[]))
        result = agent.view_daybook("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.daybook_index()
        assert [e["check"] for e in result["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert result["index"]["gaps"] == [
            "resume-bare-resume", "resume-leaping-resume"]
        assert "resumed - The held resume (resume-held-resume)" in (
            result["index_text"])
        resume = agent.get_daybook_resume("resume-leaping-resume")
        assert resume_gaps(resume, agent.daybook_book()) == (
            "steps from journalled to resumed, which the resume sequence "
            "does not allow",)
        assert resume_green(resume, agent.daybook_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _RESUME_EVENT_TYPES] == []
        agent.close()
