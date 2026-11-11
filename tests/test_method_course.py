"""M-229 The method, teachable - pure-layer tests.

TIER: integration

The pure layer is the mentor, held as data: one
record per lesson, held whole - the campaign it
answers for, named by campaign id, its title, the
steps it walked in walk lesson and the evidence
it carries, held by campaign. The question walk is
explicit - named, guided, practised, proven,
taught, with their legal steps held as data -
and a lesson's standing is derived at call
time: a lesson that opens anywhere but begun, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet begun taught stands open,
named in its gaps. A lesson stands only for
an active campaign: a lesson naming no held
campaign, or one that is not active, refuses by
name. The lesson's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, ledger, trace, lesson and current
lesson are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, proven or
taught live. The shipped example book is held
in a data file, and a loader reads a book from
any file. No charter row names this campaign: the
M-171 TUI charter binds Part VIII alone, and the
M-005 method charter names the whole of Part IX
as the part that executes it, both pinned live
below.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.method_course import (
    EXAMPLE_STAGE,
    BARE_CLAIMS,
    HELD_EVIDENCE,
    INDEX_ACTION,
    STAGES,
    CLAIM_KINDS,
    TRANSITIONS,
    CAMPAIGN_STATES,
    STAGE_FIELDS,
    PLAIN_EXPLANATION,
    LESSON_RESOURCE,
    LESSON_RULE,
    LESSON_SCHEMA,
    LESSON_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    LessonRecord,
    IndexLesson,
    CampaignRef,
    NoteRecord,
    LessonBook,
    LessonIndex,
    LessonPanel,
    LessonRegistry,
    LessonVerdict,
    LessonView,
    trace_for_lesson,
    ledger_record,
    book_record,
    build_trace,
    build_book,
    build_lesson,
    build_campaign_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_lesson,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    lesson_for_check,
    lesson_gaps,
    lesson_lesson,
    lesson_record,
    lesson_green,
    lessons_for_campaign,
    first_note,
    format_book,
    format_lesson,
    format_index,
    format_note,
    format_stage,
    format_panel,
    format_lesson_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    campaign_record,
    load_lesson,
    legal_step,
    load_lesson_file,
    next_stage,
    normalize_stage,
    normalize_claim_kind,
    normalize_campaign_state,
    normalize_stance,
    normalize_view_filter,
    note_for_lesson,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_lesson_args,
    green_lessons,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_lessons,
    validate_book,
    validate_lesson,
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
EXAMPLE_TITLE = "The method, teachable at the M-229 slice run"
EXAMPLE_STAGES = ["taught", "taught", "taught"]
EXAMPLE_RUN_IDS = (
    "lesson-held-lesson", "lesson-retried-lesson",
    "lesson-own-lesson", "lesson-bare-lesson",
    "lesson-leaping-lesson")
EXAMPLE_TRACE = "begun > guided > practised > proven > taught"


def _ref(**overrides):
    fields = {
        "campaign_id": "campaign-test",
        "seq": 1,
        "title": "A test campaign",
        "state": "live",
        "detail": "A test campaign reference held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "lesson-test",
    }
    fields.update(overrides)
    return build_campaign_ref(fields)


def _lesson(**overrides):
    fields = {
        "lesson_id": "lesson-test",
        "seq": 1,
        "campaign_id": "campaign-test",
        "title": "A test lesson",
        "stages": ["begun", "guided", "practised", "proven", "taught"],
        "claims": [],
        "detail": "A test lesson held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "lesson-test",
    }
    fields.update(overrides)
    return build_lesson(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "lesson-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "lesson_id": "lesson-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "lesson-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "lesson_id": "lesson-test",
        "trace": "begun > guided > practised > proven > taught",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "lesson-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(campaigns=None, lessons=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": LESSON_SCHEMA,
        "campaign": "M-229",
        "method_course": {"title": "A test lesson book"},
        "campaigns": [item.to_record() for item in (
            campaigns if campaigns is not None else [_ref()])],
        "lesson_records": [item.to_record() for item in (
            lessons if lessons is not None else [_lesson()])],
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
    return _book(lessons=[
        _lesson(),
        _lesson(lesson_id="lesson-hidden", seq=2,
               title="A hidden lesson", stages=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_lesson()
    assert book.title == EXAMPLE_TITLE
    assert book.lesson_ids() == EXAMPLE_RUN_IDS
    assert book.campaign_ids() == (
        "campaign-m228-scaling", "campaign-m229-teachable",
        "campaign-m230-metrics")
    assert [v.view_id for v in book.views] == [
        "view-lessons", "view-taught"]
    assert [m.lesson_id for m in book.notes] == [
        "lesson-held-lesson", "lesson-bare-lesson"]
    assert [a.lesson_id for a in book.traces] == ["lesson-held-lesson"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m228-campaign"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.lesson_ids())
    derived = derive_panel(book, "view-lessons")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-lessons").verdict == "held"
    assert derive_verdict(book, "view-lessons").green_shown == 3
    assert derive_verdict(book, "view-taught").verdict == "taught"
    assert derive_verdict(book, "view-taught").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / LESSON_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == LESSON_SCHEMA
    assert raw["campaign"] == "M-229"
    assert "verdict" not in raw
    assert "lesson_index" not in raw
    assert "ledger" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-229")]
    assert slice_.title == "The method, teachable"
    assert slice_.part == 9
    assert "`mythic tutorial` gains the Method course" in slice_.summary
    assert "a newcomer learns campaigns by running a tiny one" in slice_.summary
    assert LESSON_SLICE == "M-229"

def test_charter_rows_do_not_name_m229():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-229" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert COMPLETE_WORDS == ("complete", "open")
    assert STAGE_FIELDS == ("stages", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "complete", "open")
    assert VERDICT_WORDS == ("taught", "held", "blocked")
    assert CAMPAIGN_STATES == ("live", "dormant")
    assert STAGES == ("begun", "guided", "practised", "proven", "taught")
    assert HELD_EVIDENCE == ("course_ref", "guide_ref", "practice_ref", "proof_ref", "lesson_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["proven"] == ("begun", "taught")
    assert TRANSITIONS["taught"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_STAGE == "taught"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_campaign_state("LIVE") == "live"
    assert normalize_stage("PRACTISED") == "practised"
    assert normalize_claim_kind("FEELING") == "feeling"
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    with pytest.raises(ValueError):
        normalize_campaign_state("blessed")
    with pytest.raises(ValueError):
        normalize_stage("polish")
    with pytest.raises(ValueError):
        normalize_claim_kind("weather")
    assert legal_step("practised", "proven") is True
    assert legal_step("guided", "taught") is False
    assert legal_step("taught", "begun") is False
    assert next_stage("begun") == "guided"
    assert next_stage("practised") == "proven"
    assert next_stage("proven", failed=True) == "begun"
    assert next_stage("proven") == "taught"
    assert next_stage("taught") is None
    assert "held as data alone" in LESSON_RULE
    assert "lesson sequence" in LESSON_RULE
    assert "M-229" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /course")

def test_shipped_book_judged_honestly_as_data():
    book = load_lesson()
    opening = book.lesson_for("lesson-held-lesson")
    assert lesson_green(opening, book) is True
    assert lesson_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Lesson: The held lesson",
        "Campaign: campaign-m228-scaling",
        "Stage: taught",
        "Claims: course_ref")
    asking = book.lesson_for("lesson-bare-lesson")
    assert lesson_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert lesson_green(asking, book) is False
    skipping = book.lesson_for("lesson-leaping-lesson")
    assert lesson_gaps(skipping, book) == (
        "steps from guided to taught, which the lesson sequence "
        "does not allow",)
    assert [g.lesson_id for g in green_lessons(book)] == [
        "lesson-held-lesson", "lesson-retried-lesson", "lesson-own-lesson"]
    index = derive_index(book)
    assert [e.stage for e in index.lessons] == EXAMPLE_STAGES
    assert index.gaps == ("lesson-bare-lesson", "lesson-leaping-lesson")
    assert lesson_for_check(book, EXAMPLE_STAGE).lesson_id == (
        "lesson-held-lesson")
    assert lesson_for_check(book, "triple lesson") is None
    assert transition_breaks(book) == (
        "lesson-leaping-lesson: guided > taught",)
    assert [g.lesson_id for g in lesson_lesson(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "lesson-held-lesson") == EXAMPLE_TRACE
    assert trace_current(book, "lesson-held-lesson") is True
    assert trace_current(book, "lesson-retried-lesson") is False
    assert trace_for_lesson(
        book, "lesson-held-lesson").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_lesson(
        book, "lesson-held-lesson", "note").note_id == (
            "note-note-first")
    assert note_for_lesson(book, "lesson-nope") is None
    assert current_lesson(book).lesson_id == "lesson-bare-lesson"
    ledger = ledger_record(book)
    assert ledger["standings"] == [
        {"standing": "complete", "lesson_records": 3},
        {"standing": "open", "lesson_records": 2}]
    assert ledger["total"] == 5
    assert ledger["current_lesson"] == "lesson-bare-lesson"
    assert ledger["traces"] == [
        {"lesson_id": "lesson-held-lesson", "trace": "current"},
        {"lesson_id": "lesson-retried-lesson", "trace": "unheld"},
        {"lesson_id": "lesson-own-lesson", "trace": "unheld"},
        {"lesson_id": "lesson-bare-lesson", "trace": "unheld"},
        {"lesson_id": "lesson-leaping-lesson", "trace": "unheld"}]
    assert ledger["breaks"] == ["lesson-leaping-lesson: guided > taught"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 228
    assert citizen["next_slice"] == "M-229"
    assert citizen["m229_title"] == "The method, teachable"
    assert citizen["m229_part"] == 9
    assert citizen["m229_status"] == "queued"

def test_lesson_record_round_trips():
    lesson = _lesson()
    assert validate_lesson(lesson) is lesson
    rebuilt = build_lesson(lesson.to_record())
    assert rebuilt == lesson
    assert rebuilt.item_id == "lesson-test"
    assert rebuilt.stage == "taught"
    record = lesson_record(lesson)
    assert record["type"] == "lesson_lesson"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert campaign_record(ref)["type"] == "lesson_run"
    assert campaign_record(ref)["state"] == "live"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _lesson(stages=[])
    assert lesson_gaps(silent) == (
        "has passed through no step: the lesson has not started",)
    assert lesson_green(silent) is False
    walking = _lesson(stages=["begun", "guided"])
    assert lesson_gaps(walking) == (
        "has not reached taught: the lesson stands at guided",)
    assert walking.stage == "guided"
    sideways = _lesson(stages=["guided", "practised", "proven", "taught"])
    assert lesson_gaps(sideways) == (
        "opens at guided, not at begun: the lesson opens "
        "with the reflection",)
    repaired = _lesson(stages=["begun", "guided", "practised", "proven", "begun", "guided", "practised", "proven", "taught"])
    assert lesson_gaps(repaired) == ()
    assert lesson_green(repaired) is True
    with pytest.raises(ValueError):
        _lesson(stages=[42])
    with pytest.raises(ValueError):
        _lesson(stages="inspect as a bare string")
    with pytest.raises(ValueError):
        _lesson(stages=["begun", "polish"])
    with pytest.raises(ValueError):
        _lesson(claims=["weather"])
    with pytest.raises(ValueError):
        _lesson(claims="course_ref")
    none_lesson = _lesson(stages=None, claims=None)
    assert none_lesson.stages == ()
    assert none_lesson.claims == ()

def test_lesson_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "lessons", "coverage", "current_lesson",
                "ledger", "lesson"):
        fields = _lesson().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_lesson(fields)
    fields = _lesson().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_lesson(fields)


def test_lesson_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _lesson().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_lesson(fields)


def test_lesson_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _lesson(title="")
    with pytest.raises(ValueError):
        _lesson(campaign_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "begun > guided > practised > proven > taught"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_lessons_own_fields():
    lesson = _lesson(claims=["course_ref"])
    assert plain_lines(lesson) == (
        "Lesson: A test lesson",
        "Campaign: campaign-test",
        "Stage: taught",
        "Claims: course_ref")
    segment = segment_of(lesson)
    assert segment.startswith("lesson-test: A test lesson")
    assert "stage: 'taught'" in segment
    assert "gaps: none" in segment
    assert plain_words(lesson).startswith(
        "A test lesson - from campaign-test")

def test_red_lessons_stand_named_in_their_gaps():
    asking = _lesson(claims=["feeling", "course_ref", "summary"])
    assert lesson_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert lesson_green(asking) is False
    skipping = _lesson(stages=["begun", "guided", "taught"])
    assert lesson_gaps(skipping) == (
        "steps from guided to taught, which the lesson sequence "
        "does not allow",)
    book = _book(lessons=[
        _lesson(),
        _lesson(lesson_id="lesson-skipping", seq=2,
             stages=["begun", "guided", "taught"]),
    ])
    assert transition_breaks(book) == (
        "lesson-skipping: guided > taught",)
    assert current_lesson(book).lesson_id == "lesson-skipping"
    assert [g.lesson_id for g in lesson_lesson(book)] == [
        "lesson-test", "lesson-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "lesson_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "lesson_note"
    assert record["lesson_id"] == "lesson-test"
    assert view_plain_words(view) == "View view-test: shows all lessons."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_lessons_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.stage for e in index.lessons] == ["taught"]
    assert index.lessons[0] == IndexLesson(
        stage="taught",
        lesson_id="lesson-test", title="A test lesson")
    assert index.gaps == ("lesson-hidden",)
    record = index_record(book)
    assert record["type"] == "lesson_index"
    assert record["gaps"] == ["lesson-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "lesson_book"

def test_check_target_reaches_its_lesson_and_an_unheld_target_reaches_nothing():
    book = load_lesson()
    assert lesson_for_check(book, "taught").lesson_id == (
        "lesson-held-lesson")
    assert lesson_for_check(book, "") is None
    assert lesson_for_check(book, None) is None
    assert lesson_for_check(book, "not held at all") is None
    text = format_stage(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_lesson()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Lesson note note lesson-held-lesson" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").lesson_id == "lesson-test"
    assert note_for_lesson(book, "lesson-test").note_id == "note-test"
    assert note_for_lesson(book, "lesson-test", "praise") is None
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
    row = build_row(None, _lesson(), book)
    assert row.standing == "complete"
    assert validate_row(row, _lesson(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_lessons():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "lesson_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "taught"
    empty_book = _book(lessons=[_lesson(stages=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(LessonVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_lesson()
    assert [g.lesson_id for g in shown_lessons(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.lesson_id for g in shown_lessons(book, "view-taught")] == [
        "lesson-held-lesson", "lesson-retried-lesson", "lesson-own-lesson"]
    assert [g.lesson_id for g in lessons_for_campaign(
        book, "campaign-m229-teachable")] == [
            "lesson-own-lesson", "lesson-bare-lesson",
            "lesson-leaping-lesson"]
    assert lessons_for_campaign(book, "campaign-nope") == ()
    assert current_lesson(_mixed_book()).lesson_id == "lesson-hidden"
    assert current_lesson(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "lesson-test") == (
        "begun > guided > practised > proven > taught")
    assert trace_current(stale, "lesson-test") is False
    assert ledger_record(stale)["traces"] == [
        {"lesson_id": "lesson-test", "trace": "stale"}]

def test_guide_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(lessons=[_lesson(), _lesson(seq=2)])
    with pytest.raises(ValueError):
        _book(lessons=[_lesson(), _lesson(lesson_id="lesson-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(lessons=[_lesson(campaign_id="campaign-nope")])
    with pytest.raises(ValueError):
        _book(campaigns=[_ref(), _ref(
            campaign_id="campaign-cold", seq=2, state="dormant")],
            lessons=[_lesson(campaign_id="campaign-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(campaign_id="campaign-nope")])
    fields = {
        "schema": LESSON_SCHEMA, "campaign": "M-229",
        "method_course": {"title": "A practised book"},
        "campaigns": [_ref().to_record()],
        "lesson_records": [_lesson().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "taught"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_lesson"] = "lesson-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_lesson")
    fields["trace"] = "lesson-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / LESSON_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "method_course.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_lesson_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.lesson_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = LessonRegistry()
    assert registry.title() is None
    registry.register_campaign_ref(_ref())
    registry.register_lesson(_lesson())
    registry.register_view(_view())
    assert [g.lesson_id for g in registry.list_lessons()] == ["lesson-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_lesson("lesson-test").title == "A test lesson"
    assert registry.get_slice("campaign-test").state == "live"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("lesson-test").lesson_id == "lesson-test"
    with pytest.raises(ValueError):
        registry.register_lesson(_lesson(seq=9))
    with pytest.raises(ValueError):
        registry.register_lesson(_lesson(lesson_id="lesson-two"))
    with pytest.raises(KeyError):
        registry.get_lesson("lesson-nope")
    assert registry.book().title == "An unheld lesson book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = LessonRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test lesson book"
    assert registry.title() == "A test lesson book"
    assert len(registry.list_lessons()) == 2
    other = LessonRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    lesson = _lesson()
    assert "A test lesson" in plain_words(lesson)
    assert panel_plain_words(_mixed_book()).startswith(
        "The lesson book holds 2 lessons")
    assert verdict_plain_words(_mixed_book()) == (
        "The lessons stand held: 1 of 2 shown lessons stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green lessons; red, "
        "named in its gaps: lesson-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_lesson(lesson)
    assert "Lesson: A test lesson" in text
    assert "stands complete" in text
    text = format_lesson(_lesson(stages=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Lesson Gate (M-229) - A test lesson book" in book_text
    assert "lesson-hidden" in format_book(_mixed_book(), "campaign-test")
    assert "Lesson panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "taught - A test lesson (lesson-test)" in index_text
    assert "lesson-hidden" in index_text
    screen = format_lesson_screen()
    assert "The Lesson Gate (M-229)" in screen
    assert "lesson-bare-lesson" in screen

def test_parse_args_well_and_loader_targets():
    assert parse_lesson_args("") == ("show", None)
    assert parse_lesson_args(None) == ("show", None)
    assert parse_lesson_args("show") == ("show", None)
    assert parse_lesson_args("lesson lesson-test") == (
        "lesson", "lesson-test")
    assert parse_lesson_args("stage taught") == (
        "stage", "taught")
    assert parse_lesson_args("campaign campaign-test") == (
        "campaign", "campaign-test")
    assert parse_lesson_args("view view-test") == ("view", "view-test")
    assert parse_lesson_args("note note-test") == ("note", "note-test")
    assert parse_lesson_args("index") == ("index", None)
    assert parse_lesson_args("panel") == ("panel", None)
    assert parse_lesson_args("verdict") == ("verdict", None)
    for bad in ("dance", "lesson", "stage", "campaign", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_lesson_args(bad)
    ledger = ledger_record()
    assert ledger["type"] == "lesson_well"
    assert ledger["total"] == 5
    assert ledger["current_lesson"] == "lesson-bare-lesson"
    book = load_lesson({
        "schema": LESSON_SCHEMA, "campaign": "M-229",
        "method_course": {"title": "A practised book"},
        "campaigns": [_ref().to_record()],
        "lesson_records": [_lesson().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, LessonBook)
    assert book.title == "A practised book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_lesson({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_lesson({"campaign": "M-999"})
    built = build_lesson(
        lesson_id="lesson-kw", seq=3, campaign_id="campaign-test",
        title="Kw Lesson", stages=["begun", "guided", "practised", "proven", "taught"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="lesson-test")
    assert built.lesson_id == "lesson-kw"
    assert lesson_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-229 agent layer: the agent holds a lesson
# book for the session, lessons and views are
# published as session news through the
# checkpoint target (ledger first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held lessons, the ledger is derived from
# the held lessons' completeness, the roadmap standing
# is proven from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no campaign. This layer lessons
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session ledger news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_LESSON_EVENT_TYPES = (
    "lesson_lesson", "lesson_run", "lesson_view",
    "lesson_panel", "lesson_verdict")


def _lesson_events(store, session_id, campaign):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == campaign]


def _write_course_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / LESSON_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "method_course.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestLessonAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.course_status()
        assert status["lesson_records"] == []
        assert status["campaigns"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["course_book"]["title"] == EXAMPLE_TITLE
        assert len(status["course_book"]["campaigns"]) == 3
        assert len(status["course_book"]["lesson_records"]) == 5
        assert len(status["course_book"]["views"]) == 2
        assert len(status["course_book"]["notes"]) == 2
        assert len(status["course_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m228-campaign"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["stage"] for e in status["index"]["lessons"]] == (
            EXAMPLE_STAGES)
        assert status["index"]["gaps"] == [
            "lesson-bare-lesson", "lesson-leaping-lesson"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["ledger"]["total"] == 5
        assert status["ledger"]["current_lesson"] == "lesson-bare-lesson"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 228
        assert status["roadmap"]["next_slice"] == "M-229"
        assert status["roadmap"]["m229_title"] == "The method, teachable"
        assert "held as data alone" in status["rule"]
        assert "lesson-bare-lesson" in status["plain_words"]
        assert "The Lesson Gate (M-229)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._course_registry()
        assert agent._course_registry() is first
        assert agent._course_store is first
        for name in ("course_book", "course_status", "course_panel",
                     "course_verdict", "course_index", "report_course"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_course_registry", "course_book", "course_status",
            "get_course_lesson", "get_course_view", "get_course_note",
            "lessons_for_campaign", "course_green",
            "course_panel", "course_verdict", "course_index",
            "register_course_lesson", "register_course_view",
            "view_course", "register_course_book",
            "record_course_book", "report_course",
            "_publish_course_record", "_course_screen",
            "_course_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.course_status()
        assert agent.get_course_lesson(
            "lesson-held-lesson").title == "The held lesson"
        assert agent.get_course_view(
            "view-lessons").view_filter == "all"
        assert agent.get_course_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.lesson_id for d in agent.lessons_for_campaign(
            "campaign-m229-teachable")] == [
            "lesson-own-lesson", "lesson-bare-lesson",
            "lesson-leaping-lesson"]
        assert [d.lesson_id for d in agent.course_green()] == [
            "lesson-held-lesson", "lesson-retried-lesson", "lesson-own-lesson"]
        agent.course_panel()
        agent.course_verdict()
        agent.course_index()
        agent.report_course()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _LESSON_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_course_lesson("lesson-nope")
        with pytest.raises(KeyError):
            agent.get_course_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_course_note("note-nope")
        with pytest.raises(ValueError):
            agent.lessons_for_campaign("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_course_lesson(_lesson())
        status = agent.course_status()
        assert [d["lesson_id"] for d in status["lesson_records"]] == ["lesson-test"]
        assert status["book"]["title"] == "An unheld lesson book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["stage"] for e in status["index"]["lessons"]] == [
            "taught"]
        assert status["first_note"] is None
        assert "lesson-test" in status["screen"]
    def test_held_lesson_never_falls_back_to_the_example(
            self, agent):
        agent.register_course_lesson(_lesson())
        with pytest.raises(KeyError):
            agent.get_course_lesson("lesson-held-lesson")
        with pytest.raises(KeyError):
            agent.get_course_view("view-lessons")
        with pytest.raises(KeyError):
            agent.get_course_note("note-note-first")
        lesson = agent.get_course_lesson("lesson-test")
        assert lesson.title == "A test lesson"
        assert agent.course_book().title == (
            "An unheld lesson book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_course_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.lesson_id == "lesson-held-lesson"
        status = agent.course_status()
        assert status["index"]["gaps"] == [
            "lesson-bare-lesson", "lesson-leaping-lesson"]
        assert status["first_note"]["lesson_id"] == (
            "lesson-held-lesson")
        assert status["first_note"]["stance"] == "note"

class TestLessonAgentHolding:
    def test_register_lesson_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_course_lesson(_lesson())
        assert result["lesson"]["lesson_id"] == "lesson-test"
        assert result["record_news"]["type"] == "lesson_lesson"
        assert "lesson-test" in result["screen"]
        events = _lesson_events(store, session_id, "lesson_lesson")
        assert len(events) == 1
        agent.close()

    def test_duplicate_lesson_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_course_lesson(_lesson())
        with pytest.raises(ValueError):
            agent.register_course_lesson(_lesson(seq=9))
        with pytest.raises(ValueError):
            agent.register_course_lesson(_lesson(lesson_id="lesson-two"))
        events = _lesson_events(store, session_id, "lesson_lesson")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_course_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_lesson_events(
            store, session_id, "lesson_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_course_lesson(_lesson())
        result = agent.view_course("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "lesson_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "taught"
        assert len(_lesson_events(
            store, session_id, "lesson_view")) == 1
        assert len(_lesson_events(
            store, session_id, "lesson_panel")) == 1
        assert len(_lesson_events(
            store, session_id, "lesson_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_lesson(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_course_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "lesson_run", "lesson_lesson", "lesson_view"]
        assert len(_lesson_events(
            store, session_id, "lesson_lesson")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_course_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "lesson_panel"
        assert result["index_record"]["gaps"] == [
            "lesson-bare-lesson", "lesson-leaping-lesson"]
        with pytest.raises(ValueError):
            agent.record_course_book()
        assert len(_lesson_events(
            store, session_id, "lesson_run")) == 3
        assert len(_lesson_events(
            store, session_id, "lesson_lesson")) == 5
        assert len(_lesson_events(
            store, session_id, "lesson_view")) == 2
        agent.close()

    def test_book_from_a_file_is_guided_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_course_book_file(tmp_path)
        book = load_lesson_file(path)
        result = agent.record_course_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_runrt_renders_example_then_held_book_only(self, agent):
        lesson = agent.report_course()
        assert lesson["book"]["title"] == EXAMPLE_TITLE
        assert lesson["verdict"]["verdict"] == "held"
        assert lesson["index"]["gaps"] == [
            "lesson-bare-lesson", "lesson-leaping-lesson"]
        assert "lesson-held-lesson" in lesson["book_text"]
        assert "taught - The held lesson (lesson-held-lesson)" in lesson["index_text"]
        agent.register_course_lesson(_lesson())
        lesson = agent.report_course()
        assert lesson["book"]["title"] == "An unheld lesson book"
        assert lesson["panel"] is None
        assert lesson["verdict"] is None

class TestLessonTerminalHeading:
    def test_show_lesson_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/course")
        assert "The Lesson Gate (M-229)" in text
        _, _, text = _slash(agent, "/course lesson lesson-held-lesson")
        assert "Lesson: The held lesson" in text
        _, _, text = _slash(
            agent, "/course stage taught")
        assert "Lesson: The held lesson" in text
        _, _, text = _slash(agent, "/course stage triple lesson")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/course campaign campaign-m229-teachable")
        assert "lesson-bare-lesson" in text
        assert "lesson-held-lesson" not in text
        _, _, text = _slash(agent, "/course view view-lessons")
        assert "filter all" in text
        _, _, text = _slash(agent, "/course note note-note-first")
        assert "Lesson note note lesson-held-lesson" in text
        _, _, text = _slash(agent, "/course index")
        assert "Lesson index" in text
        assert "lesson-bare-lesson" in text
        _, _, text = _slash(agent, "/course panel")
        assert "Lesson panel under view view-lessons" in text
        _, _, text = _slash(agent, "/course verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/course [show|lesson <lesson-id>"
                "|stage <stage>|campaign <campaign-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/course dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/course lesson lesson-nope")
        assert "no lesson named" in text
@pytest.fixture()
def lesson_handler(agent, monkeypatch):
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


def _lesson_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestLessonCommand:
    def test_show_is_default(self, lesson_handler, agent):
        lesson_handler._handle_course("")
        assert "The Lesson Gate (M-229)" in (
            _lesson_published_text(lesson_handler))

    def test_lesson_check_slice_view_note_index_panel_verdict(
            self, lesson_handler, agent):
        lesson_handler._handle_course("lesson lesson-held-lesson")
        assert "Lesson: The held lesson" in _lesson_published_text(
            lesson_handler)
        lesson_handler._handle_course(
            "stage taught")
        assert "Lesson: The held lesson" in _lesson_published_text(
            lesson_handler)
        lesson_handler._handle_course("campaign campaign-m229-teachable")
        assert "lesson-bare-lesson" in _lesson_published_text(
            lesson_handler)
        lesson_handler._handle_course("view view-lessons")
        assert "filter all" in _lesson_published_text(lesson_handler)
        lesson_handler._handle_course("note note-note-first")
        assert "Lesson note note lesson-held-lesson" in (
            _lesson_published_text(lesson_handler))
        lesson_handler._handle_course("index")
        assert "Lesson index" in _lesson_published_text(lesson_handler)
        lesson_handler._handle_course("panel")
        assert "Lesson panel under view" in _lesson_published_text(
            lesson_handler)
        lesson_handler._handle_course("verdict")
        assert "held" in _lesson_published_text(lesson_handler)
    def test_bad_grammar_is_published(
            self, lesson_handler, agent):
        lesson_handler._handle_course("dance party")
        assert USAGE in _lesson_published_text(lesson_handler)
        lesson_handler._handle_course("lesson lesson-nope")
        assert "no lesson named" in _lesson_published_text(
            lesson_handler)


class TestChatScreenRoutingLesson:
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
        screen.handle_command("/course panel", _FakeLog())
        assert calls == [("/course", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/course[/green] - show the Lesson gate (M-229)" in (
            text)
        assert ('"/course": "Usage: /course | '
                '/course lesson <lesson-id>') in text

class TestLessonDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.course_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-lessons"
        verdict = agent.course_verdict()
        assert verdict.verdict == "held"
        found = agent.course_verdict("view-taught")
        assert found.verdict == "taught"
        assert found.green_shown == 3
        agent.register_course_lesson(_lesson())
        with pytest.raises(ValueError):
            agent.course_panel()
        with pytest.raises(ValueError):
            agent.course_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_course_lesson(_lesson(stages=[]))
        result = agent.view_course("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.course_index()
        assert [e["stage"] for e in result["index"]["lessons"]] == (
            EXAMPLE_STAGES)
        assert result["index"]["gaps"] == [
            "lesson-bare-lesson", "lesson-leaping-lesson"]
        assert "taught - The held lesson (lesson-held-lesson)" in (
            result["index_text"])
        lesson = agent.get_course_lesson("lesson-leaping-lesson")
        assert lesson_gaps(lesson, agent.course_book()) == (
            "steps from guided to taught, which the lesson sequence "
            "does not allow",)
        assert lesson_green(lesson, agent.course_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _LESSON_EVENT_TYPES] == []
        agent.close()
