"""M-209 Question Law - pure-layer tests.

TIER: integration

The pure layer is the answerer, held as data: one
record per questioning, held whole - the slice it
answers for, named by slice id, its title, the
steps it walked in walk order and the evidence
it carries, held by kind. The question walk is
explicit - raised, paused, drafted, delivered,
resumed, with their legal steps held as data -
and a questioning's standing is derived at call
time: a questioning that opens anywhere but
raised, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet reached resumed stands open,
named in its gaps. A questioning stands only for
an active slice: a questioning naming no held
slice, or one that is not active, refuses by
name. The questioning's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, board, trace, order and current
questioning are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, delivered or
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

from mythic_agent.core.question_law import (
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
    QUESTIONING_RESOURCE,
    QUESTIONING_RULE,
    QUESTIONING_SCHEMA,
    QUESTIONING_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    QuestioningRecord,
    IndexEntry,
    SliceRef,
    NoteRecord,
    QuestioningBook,
    QuestioningIndex,
    QuestioningPanel,
    QuestioningRegistry,
    QuestioningVerdict,
    QuestioningView,
    trace_for_questioning,
    board_record,
    book_record,
    build_trace,
    build_book,
    build_questioning,
    build_slice_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_questioning,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    questioning_for_check,
    questioning_gaps,
    questioning_order,
    questioning_record,
    questioning_green,
    questionings_for_slice,
    first_note,
    format_book,
    format_questioning,
    format_index,
    format_note,
    format_check,
    format_panel,
    format_questioning_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    slice_record,
    load_questioning,
    legal_step,
    load_questioning_file,
    next_check,
    normalize_check,
    normalize_claim_kind,
    normalize_slice_state,
    normalize_stance,
    normalize_view_filter,
    note_for_questioning,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_questioning_args,
    green_questionings,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_questionings,
    validate_book,
    validate_questioning,
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
EXAMPLE_TITLE = "The question law at the M-208 slice boundary"
EXAMPLE_CHECKS = ["resumed", "resumed", "resumed"]
EXAMPLE_RUN_IDS = (
    "questioning-answered-question", "questioning-followed-question",
    "questioning-wired-question", "questioning-bare-question",
    "questioning-leaping-question")
EXAMPLE_TRACE = "raised > paused > drafted > delivered > resumed"


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
        "origin_session": "questioning-test",
    }
    fields.update(overrides)
    return build_slice_ref(fields)


def _questioning(**overrides):
    fields = {
        "questioning_id": "questioning-test",
        "seq": 1,
        "slice_id": "slice-test",
        "title": "A test questioning",
        "checks": ["raised", "paused", "drafted", "delivered", "resumed"],
        "claims": [],
        "detail": "A test questioning held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "questioning-test",
    }
    fields.update(overrides)
    return build_questioning(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "questioning-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "questioning_id": "questioning-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "questioning-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "questioning_id": "questioning-test",
        "trace": "raised > paused > drafted > delivered > resumed",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "questioning-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(slices=None, questionings=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": QUESTIONING_SCHEMA,
        "slice": "M-209",
        "question_law": {"title": "A test questioning book"},
        "slices": [item.to_record() for item in (
            slices if slices is not None else [_ref()])],
        "questionings": [item.to_record() for item in (
            questionings if questionings is not None else [_questioning()])],
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
    return _book(questionings=[
        _questioning(),
        _questioning(questioning_id="questioning-hidden", seq=2,
               title="A hidden questioning", checks=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_questioning()
    assert book.title == EXAMPLE_TITLE
    assert book.questioning_ids() == EXAMPLE_RUN_IDS
    assert book.slice_ids() == (
        "slice-m208-pauselines", "slice-m209-question",
        "slice-m210-scope")
    assert [v.view_id for v in book.views] == [
        "view-questionings", "view-resumed"]
    assert [m.questioning_id for m in book.notes] == [
        "questioning-answered-question", "questioning-bare-question"]
    assert [a.questioning_id for a in book.traces] == ["questioning-answered-question"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m208-boundary"
    assert panel.as_of == "2026-11-10"
    assert [row.item_id for row in panel.rows] == list(book.questioning_ids())
    derived = derive_panel(book, "view-questionings")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-questionings").verdict == "held"
    assert derive_verdict(book, "view-questionings").green_shown == 3
    assert derive_verdict(book, "view-resumed").verdict == "reported"
    assert derive_verdict(book, "view-resumed").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / QUESTIONING_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == QUESTIONING_SCHEMA
    assert raw["slice"] == "M-209"
    assert "verdict" not in raw
    assert "questioning_index" not in raw
    assert "board" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-209")]
    assert slice_.title == "Question law"
    assert slice_.part == 9
    assert "when the human asks a question" in slice_.summary
    assert "the campaign pauses" in slice_.summary
    assert "answered first, plainly and fully" in slice_.summary
    assert "then work resumes" in slice_.summary
    assert "Volmarr's supreme law" in slice_.summary
    assert QUESTIONING_SLICE == "M-209"

def test_charter_rows_do_not_name_m209():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-209" not in owners
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
    assert SLICE_STATES == ("active", "queued")
    assert CHECKS == ("raised", "paused", "drafted", "delivered", "resumed")
    assert HELD_EVIDENCE == ("answer_record", "question_ref", "delivery_ref", "ledger_row")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["delivered"] == ("raised", "resumed")
    assert TRANSITIONS["resumed"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_CHECK == "resumed"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_slice_state("ACTIVE") == "active"
    assert normalize_check("DRAFTED") == "drafted"
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
    assert legal_step("drafted", "delivered") is True
    assert legal_step("paused", "resumed") is False
    assert legal_step("resumed", "raised") is False
    assert next_check("raised") == "paused"
    assert next_check("drafted") == "delivered"
    assert next_check("delivered", failed=True) == "raised"
    assert next_check("delivered") == "resumed"
    assert next_check("resumed") is None
    assert "held as data alone" in QUESTIONING_RULE
    assert "question sequence" in QUESTIONING_RULE
    assert "M-209" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /questionlaw")

def test_shipped_book_judged_honestly_as_data():
    book = load_questioning()
    opening = book.questioning_for("questioning-answered-question")
    assert questioning_green(opening, book) is True
    assert questioning_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Questioning: The answered question questioning",
        "Slice: slice-m208-pauselines",
        "Check: resumed",
        "Claims: answer_record")
    asking = book.questioning_for("questioning-bare-question")
    assert questioning_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert questioning_green(asking, book) is False
    skipping = book.questioning_for("questioning-leaping-question")
    assert questioning_gaps(skipping, book) == (
        "steps from paused to resumed, which the question sequence "
        "does not allow",)
    assert [g.questioning_id for g in green_questionings(book)] == [
        "questioning-answered-question", "questioning-followed-question", "questioning-wired-question"]
    index = derive_index(book)
    assert [e.check for e in index.entries] == EXAMPLE_CHECKS
    assert index.gaps == ("questioning-bare-question", "questioning-leaping-question")
    assert questioning_for_check(book, EXAMPLE_CHECK).questioning_id == (
        "questioning-answered-question")
    assert questioning_for_check(book, "triple resume") is None
    assert transition_breaks(book) == (
        "questioning-leaping-question: paused > resumed",)
    assert [g.questioning_id for g in questioning_order(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "questioning-answered-question") == EXAMPLE_TRACE
    assert trace_current(book, "questioning-answered-question") is True
    assert trace_current(book, "questioning-followed-question") is False
    assert trace_for_questioning(
        book, "questioning-answered-question").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_questioning(
        book, "questioning-answered-question", "note").note_id == (
            "note-note-first")
    assert note_for_questioning(book, "questioning-nope") is None
    assert current_questioning(book).questioning_id == "questioning-bare-question"
    board = board_record(book)
    assert board["standings"] == [
        {"standing": "complete", "questionings": 3},
        {"standing": "open", "questionings": 2}]
    assert board["total"] == 5
    assert board["current_questioning"] == "questioning-bare-question"
    assert board["traces"] == [
        {"questioning_id": "questioning-answered-question", "trace": "current"},
        {"questioning_id": "questioning-followed-question", "trace": "unheld"},
        {"questioning_id": "questioning-wired-question", "trace": "unheld"},
        {"questioning_id": "questioning-bare-question", "trace": "unheld"},
        {"questioning_id": "questioning-leaping-question", "trace": "unheld"}]
    assert board["breaks"] == ["questioning-leaping-question: paused > resumed"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 258
    assert citizen["next_slice"] == "M-259"
    assert citizen["m209_title"] == "Question law"
    assert citizen["m209_part"] == 9
    assert citizen["m209_status"] == "done"

def test_questioning_record_round_trips():
    questioning = _questioning()
    assert validate_questioning(questioning) is questioning
    rebuilt = build_questioning(questioning.to_record())
    assert rebuilt == questioning
    assert rebuilt.item_id == "questioning-test"
    assert rebuilt.check == "resumed"
    record = questioning_record(questioning)
    assert record["type"] == "questioning_questioning"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert slice_record(ref)["type"] == "questioning_slice"
    assert slice_record(ref)["state"] == "active"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _questioning(checks=[])
    assert questioning_gaps(silent) == (
        "has passed through no step: the questioning has not started",)
    assert questioning_green(silent) is False
    walking = _questioning(checks=["raised", "paused"])
    assert questioning_gaps(walking) == (
        "has not reached resumed: the questioning stands at paused",)
    assert walking.check == "paused"
    sideways = _questioning(checks=["paused", "drafted", "delivered", "resumed"])
    assert questioning_gaps(sideways) == (
        "opens at paused, not at raised: the questioning opens "
        "with the question",)
    repaired = _questioning(checks=["raised", "paused", "drafted", "delivered", "raised", "paused", "drafted", "delivered", "resumed"])
    assert questioning_gaps(repaired) == ()
    assert questioning_green(repaired) is True
    with pytest.raises(ValueError):
        _questioning(checks=[42])
    with pytest.raises(ValueError):
        _questioning(checks="inspect as a bare string")
    with pytest.raises(ValueError):
        _questioning(checks=["raised", "polish"])
    with pytest.raises(ValueError):
        _questioning(claims=["weather"])
    with pytest.raises(ValueError):
        _questioning(claims="answer_record")
    none_questioning = _questioning(checks=None, claims=None)
    assert none_questioning.checks == ()
    assert none_questioning.claims == ()

def test_questioning_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "entries", "coverage", "current_questioning",
                "board", "order"):
        fields = _questioning().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_questioning(fields)
    fields = _questioning().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_questioning(fields)


def test_questioning_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _questioning().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_questioning(fields)


def test_questioning_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _questioning(title="")
    with pytest.raises(ValueError):
        _questioning(slice_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "raised > paused > drafted > delivered > resumed"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_questionings_own_fields():
    questioning = _questioning(claims=["answer_record"])
    assert plain_lines(questioning) == (
        "Questioning: A test questioning",
        "Slice: slice-test",
        "Check: resumed",
        "Claims: answer_record")
    segment = segment_of(questioning)
    assert segment.startswith("questioning-test: A test questioning")
    assert "check: 'resumed'" in segment
    assert "gaps: none" in segment
    assert plain_words(questioning).startswith(
        "A test questioning - from slice-test")

def test_red_questionings_stand_named_in_their_gaps():
    asking = _questioning(claims=["feeling", "answer_record", "summary"])
    assert questioning_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert questioning_green(asking) is False
    skipping = _questioning(checks=["raised", "paused", "resumed"])
    assert questioning_gaps(skipping) == (
        "steps from paused to resumed, which the question sequence "
        "does not allow",)
    book = _book(questionings=[
        _questioning(),
        _questioning(questioning_id="questioning-skipping", seq=2,
             checks=["raised", "paused", "resumed"]),
    ])
    assert transition_breaks(book) == (
        "questioning-skipping: paused > resumed",)
    assert current_questioning(book).questioning_id == "questioning-skipping"
    assert [g.questioning_id for g in questioning_order(book)] == [
        "questioning-test", "questioning-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "questioning_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "questioning_note"
    assert record["questioning_id"] == "questioning-test"
    assert view_plain_words(view) == "View view-test: shows all questionings."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_questionings_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.check for e in index.entries] == ["resumed"]
    assert index.entries[0] == IndexEntry(
        check="resumed",
        questioning_id="questioning-test", title="A test questioning")
    assert index.gaps == ("questioning-hidden",)
    record = index_record(book)
    assert record["type"] == "questioning_index"
    assert record["gaps"] == ["questioning-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "questioning_book"

def test_check_target_reaches_its_questioning_and_an_unheld_target_reaches_nothing():
    book = load_questioning()
    assert questioning_for_check(book, "resumed").questioning_id == (
        "questioning-answered-question")
    assert questioning_for_check(book, "") is None
    assert questioning_for_check(book, None) is None
    assert questioning_for_check(book, "not held at all") is None
    text = format_check(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_questioning()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Questioning note note questioning-answered-question" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").questioning_id == "questioning-test"
    assert note_for_questioning(book, "questioning-test").note_id == "note-test"
    assert note_for_questioning(book, "questioning-test", "praise") is None
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
    row = build_row(None, _questioning(), book)
    assert row.standing == "complete"
    assert validate_row(row, _questioning(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_questionings():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "questioning_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "reported"
    empty_book = _book(questionings=[_questioning(checks=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(QuestioningVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_questioning()
    assert [g.questioning_id for g in shown_questionings(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.questioning_id for g in shown_questionings(book, "view-resumed")] == [
        "questioning-answered-question", "questioning-followed-question", "questioning-wired-question"]
    assert [g.questioning_id for g in questionings_for_slice(
        book, "slice-m209-question")] == [
            "questioning-wired-question", "questioning-bare-question",
            "questioning-leaping-question"]
    assert questionings_for_slice(book, "slice-nope") == ()
    assert current_questioning(_mixed_book()).questioning_id == "questioning-hidden"
    assert current_questioning(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "questioning-test") == (
        "raised > paused > drafted > delivered > resumed")
    assert trace_current(stale, "questioning-test") is False
    assert board_record(stale)["traces"] == [
        {"questioning_id": "questioning-test", "trace": "stale"}]

def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(questionings=[_questioning(), _questioning(seq=2)])
    with pytest.raises(ValueError):
        _book(questionings=[_questioning(), _questioning(questioning_id="questioning-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(questionings=[_questioning(slice_id="slice-nope")])
    with pytest.raises(ValueError):
        _book(slices=[_ref(), _ref(
            slice_id="slice-cold", seq=2, state="queued")],
            questionings=[_questioning(slice_id="slice-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(slice_id="slice-nope")])
    fields = {
        "schema": QUESTIONING_SCHEMA, "slice": "M-209",
        "question_law": {"title": "A judged book"},
        "slices": [_ref().to_record()],
        "questionings": [_questioning().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "reported"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_questioning"] = "questioning-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_questioning")
    fields["trace"] = "questioning-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / QUESTIONING_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "question_law.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_questioning_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.questioning_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = QuestioningRegistry()
    assert registry.title() is None
    registry.register_slice_ref(_ref())
    registry.register_questioning(_questioning())
    registry.register_view(_view())
    assert [g.questioning_id for g in registry.list_questionings()] == ["questioning-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_questioning("questioning-test").title == "A test questioning"
    assert registry.get_slice("slice-test").state == "active"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("questioning-test").questioning_id == "questioning-test"
    with pytest.raises(ValueError):
        registry.register_questioning(_questioning(seq=9))
    with pytest.raises(ValueError):
        registry.register_questioning(_questioning(questioning_id="questioning-two"))
    with pytest.raises(KeyError):
        registry.get_questioning("questioning-nope")
    assert registry.book().title == "An unheld questioning book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = QuestioningRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test questioning book"
    assert registry.title() == "A test questioning book"
    assert len(registry.list_questionings()) == 2
    other = QuestioningRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    questioning = _questioning()
    assert "A test questioning" in plain_words(questioning)
    assert panel_plain_words(_mixed_book()).startswith(
        "The questioning book holds 2 questionings")
    assert verdict_plain_words(_mixed_book()) == (
        "The questionings stand held: 1 of 2 shown questionings stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green questionings; red, "
        "named in its gaps: questioning-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_questioning(questioning)
    assert "Questioning: A test questioning" in text
    assert "stands complete" in text
    text = format_questioning(_questioning(checks=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Question Gate (M-209) - A test questioning book" in book_text
    assert "questioning-hidden" in format_book(_mixed_book(), "slice-test")
    assert "Questioning panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "resumed - A test questioning (questioning-test)" in index_text
    assert "questioning-hidden" in index_text
    screen = format_questioning_screen()
    assert "The Question Gate (M-209)" in screen
    assert "questioning-bare-question" in screen

def test_parse_args_board_and_loader_targets():
    assert parse_questioning_args("") == ("show", None)
    assert parse_questioning_args(None) == ("show", None)
    assert parse_questioning_args("show") == ("show", None)
    assert parse_questioning_args("questioning questioning-test") == (
        "questioning", "questioning-test")
    assert parse_questioning_args("check resumed") == (
        "check", "resumed")
    assert parse_questioning_args("slice slice-test") == (
        "slice", "slice-test")
    assert parse_questioning_args("view view-test") == ("view", "view-test")
    assert parse_questioning_args("note note-test") == ("note", "note-test")
    assert parse_questioning_args("index") == ("index", None)
    assert parse_questioning_args("panel") == ("panel", None)
    assert parse_questioning_args("verdict") == ("verdict", None)
    for bad in ("dance", "questioning", "check", "slice", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_questioning_args(bad)
    board = board_record()
    assert board["type"] == "questioning_board"
    assert board["total"] == 5
    assert board["current_questioning"] == "questioning-bare-question"
    book = load_questioning({
        "schema": QUESTIONING_SCHEMA, "slice": "M-209",
        "question_law": {"title": "A judged book"},
        "slices": [_ref().to_record()],
        "questionings": [_questioning().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, QuestioningBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_questioning({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_questioning({"slice": "M-999"})
    built = build_questioning(
        questioning_id="questioning-kw", seq=3, slice_id="slice-test",
        title="Kw Questioning", checks=["raised", "paused", "drafted", "delivered", "resumed"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="questioning-test")
    assert built.questioning_id == "questioning-kw"
    assert questioning_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-209 agent layer: the agent holds a questioning
# book for the session, questionings and views are
# published as session news through the
# checkpoint target (journal first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held questionings, the board is derived from
# the held questionings' completeness, the roadmap standing
# is read from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no slice. This layer questionings
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_QUESTIONING_EVENT_TYPES = (
    "questioning_questioning", "questioning_slice", "questioning_view",
    "questioning_panel", "questioning_verdict")


def _questioning_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_questioning_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / QUESTIONING_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "question_law.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestQuestioningAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.questioning_status()
        assert status["questionings"] == []
        assert status["slices"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["questioning_book"]["title"] == EXAMPLE_TITLE
        assert len(status["questioning_book"]["slices"]) == 3
        assert len(status["questioning_book"]["questionings"]) == 5
        assert len(status["questioning_book"]["views"]) == 2
        assert len(status["questioning_book"]["notes"]) == 2
        assert len(status["questioning_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m208-boundary"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["check"] for e in status["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert status["index"]["gaps"] == [
            "questioning-bare-question", "questioning-leaping-question"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["board"]["total"] == 5
        assert status["board"]["current_questioning"] == "questioning-bare-question"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 258
        assert status["roadmap"]["next_slice"] == "M-259"
        assert status["roadmap"]["m209_title"] == "Question law"
        assert "held as data alone" in status["rule"]
        assert "questioning-bare-question" in status["plain_words"]
        assert "The Question Gate (M-209)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._questioning_registry()
        assert agent._questioning_registry() is first
        assert agent._questioning_store is first
        for name in ("questioning_book", "questioning_status", "questioning_panel",
                     "questioning_verdict", "questioning_index", "report_questioning"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_questioning_registry", "questioning_book", "questioning_status",
            "get_questioning_questioning", "get_questioning_view", "get_questioning_note",
            "questioning_questionings_for_slice", "questioning_questionings_green",
            "questioning_panel", "questioning_verdict", "questioning_index",
            "register_questioning_questioning", "register_questioning_view",
            "view_questioning", "register_questioning_book",
            "record_questioning_book", "report_questioning",
            "_publish_questioning_record", "_questioning_screen",
            "_questioning_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.questioning_status()
        assert agent.get_questioning_questioning(
            "questioning-answered-question").title == "The answered question questioning"
        assert agent.get_questioning_view(
            "view-questionings").view_filter == "all"
        assert agent.get_questioning_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.questioning_id for d in agent.questioning_questionings_for_slice(
            "slice-m209-question")] == [
            "questioning-wired-question", "questioning-bare-question",
            "questioning-leaping-question"]
        assert [d.questioning_id for d in agent.questioning_questionings_green()] == [
            "questioning-answered-question", "questioning-followed-question", "questioning-wired-question"]
        agent.questioning_panel()
        agent.questioning_verdict()
        agent.questioning_index()
        agent.report_questioning()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _QUESTIONING_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_questioning_questioning("questioning-nope")
        with pytest.raises(KeyError):
            agent.get_questioning_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_questioning_note("note-nope")
        with pytest.raises(ValueError):
            agent.questioning_questionings_for_slice("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_questioning_questioning(_questioning())
        status = agent.questioning_status()
        assert [d["questioning_id"] for d in status["questionings"]] == ["questioning-test"]
        assert status["book"]["title"] == "An unheld questioning book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["check"] for e in status["index"]["entries"]] == [
            "resumed"]
        assert status["first_note"] is None
        assert "questioning-test" in status["screen"]
    def test_held_questioning_never_falls_back_to_the_example(
            self, agent):
        agent.register_questioning_questioning(_questioning())
        with pytest.raises(KeyError):
            agent.get_questioning_questioning("questioning-answered-question")
        with pytest.raises(KeyError):
            agent.get_questioning_view("view-questionings")
        with pytest.raises(KeyError):
            agent.get_questioning_note("note-note-first")
        questioning = agent.get_questioning_questioning("questioning-test")
        assert questioning.title == "A test questioning"
        assert agent.questioning_book().title == (
            "An unheld questioning book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_questioning_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.questioning_id == "questioning-answered-question"
        status = agent.questioning_status()
        assert status["index"]["gaps"] == [
            "questioning-bare-question", "questioning-leaping-question"]
        assert status["first_note"]["questioning_id"] == (
            "questioning-answered-question")
        assert status["first_note"]["stance"] == "note"

class TestQuestioningAgentHolding:
    def test_register_questioning_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_questioning_questioning(_questioning())
        assert result["questioning"]["questioning_id"] == "questioning-test"
        assert result["record_news"]["type"] == "questioning_questioning"
        assert "questioning-test" in result["screen"]
        events = _questioning_events(store, session_id, "questioning_questioning")
        assert len(events) == 1
        agent.close()

    def test_duplicate_questioning_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_questioning_questioning(_questioning())
        with pytest.raises(ValueError):
            agent.register_questioning_questioning(_questioning(seq=9))
        with pytest.raises(ValueError):
            agent.register_questioning_questioning(_questioning(questioning_id="questioning-two"))
        events = _questioning_events(store, session_id, "questioning_questioning")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_questioning_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_questioning_events(
            store, session_id, "questioning_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_questioning_questioning(_questioning())
        result = agent.view_questioning("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "questioning_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "reported"
        assert len(_questioning_events(
            store, session_id, "questioning_view")) == 1
        assert len(_questioning_events(
            store, session_id, "questioning_panel")) == 1
        assert len(_questioning_events(
            store, session_id, "questioning_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_questioning_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "questioning_slice", "questioning_questioning", "questioning_view"]
        assert len(_questioning_events(
            store, session_id, "questioning_questioning")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_questioning_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "questioning_panel"
        assert result["index_record"]["gaps"] == [
            "questioning-bare-question", "questioning-leaping-question"]
        with pytest.raises(ValueError):
            agent.record_questioning_book()
        assert len(_questioning_events(
            store, session_id, "questioning_slice")) == 3
        assert len(_questioning_events(
            store, session_id, "questioning_questioning")) == 5
        assert len(_questioning_events(
            store, session_id, "questioning_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_questioning_book_file(tmp_path)
        book = load_questioning_file(path)
        result = agent.record_questioning_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_questioning()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "held"
        assert report["index"]["gaps"] == [
            "questioning-bare-question", "questioning-leaping-question"]
        assert "questioning-answered-question" in report["book_text"]
        assert "resumed - The answered question questioning (questioning-answered-question)" in report["index_text"]
        agent.register_questioning_questioning(_questioning())
        report = agent.report_questioning()
        assert report["book"]["title"] == "An unheld questioning book"
        assert report["panel"] is None
        assert report["verdict"] is None

class TestQuestioningTerminalHeading:
    def test_show_questioning_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/questionlaw")
        assert "The Question Gate (M-209)" in text
        _, _, text = _slash(agent, "/questionlaw questioning questioning-answered-question")
        assert "Questioning: The answered question questioning" in text
        _, _, text = _slash(
            agent, "/questionlaw check resumed")
        assert "Questioning: The answered question questioning" in text
        _, _, text = _slash(agent, "/questionlaw check triple resume")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/questionlaw slice slice-m209-question")
        assert "questioning-bare-question" in text
        assert "questioning-answered-question" not in text
        _, _, text = _slash(agent, "/questionlaw view view-questionings")
        assert "filter all" in text
        _, _, text = _slash(agent, "/questionlaw note note-note-first")
        assert "Questioning note note questioning-answered-question" in text
        _, _, text = _slash(agent, "/questionlaw index")
        assert "Questioning index" in text
        assert "questioning-bare-question" in text
        _, _, text = _slash(agent, "/questionlaw panel")
        assert "Questioning panel under view view-questionings" in text
        _, _, text = _slash(agent, "/questionlaw verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/questionlaw [show|questioning <questioning-id>"
                "|check <check>|slice <slice-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/questionlaw dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/questionlaw questioning questioning-nope")
        assert "no questioning named" in text
@pytest.fixture()
def questioning_handler(agent, monkeypatch):
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


def _questioning_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestQuestioningCommand:
    def test_show_is_default(self, questioning_handler, agent):
        questioning_handler._handle_questioning("")
        assert "The Question Gate (M-209)" in (
            _questioning_published_text(questioning_handler))

    def test_questioning_check_slice_view_note_index_panel_verdict(
            self, questioning_handler, agent):
        questioning_handler._handle_questioning("questioning questioning-answered-question")
        assert "Questioning: The answered question questioning" in _questioning_published_text(
            questioning_handler)
        questioning_handler._handle_questioning(
            "check resumed")
        assert "Questioning: The answered question questioning" in _questioning_published_text(
            questioning_handler)
        questioning_handler._handle_questioning("slice slice-m209-question")
        assert "questioning-bare-question" in _questioning_published_text(
            questioning_handler)
        questioning_handler._handle_questioning("view view-questionings")
        assert "filter all" in _questioning_published_text(questioning_handler)
        questioning_handler._handle_questioning("note note-note-first")
        assert "Questioning note note questioning-answered-question" in (
            _questioning_published_text(questioning_handler))
        questioning_handler._handle_questioning("index")
        assert "Questioning index" in _questioning_published_text(questioning_handler)
        questioning_handler._handle_questioning("panel")
        assert "Questioning panel under view" in _questioning_published_text(
            questioning_handler)
        questioning_handler._handle_questioning("verdict")
        assert "held" in _questioning_published_text(questioning_handler)
    def test_bad_grammar_is_published(
            self, questioning_handler, agent):
        questioning_handler._handle_questioning("dance party")
        assert USAGE in _questioning_published_text(questioning_handler)
        questioning_handler._handle_questioning("questioning questioning-nope")
        assert "no questioning named" in _questioning_published_text(
            questioning_handler)


class TestChatScreenRoutingQuestioning:
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
        screen.handle_command("/questionlaw panel", _FakeLog())
        assert calls == [("/questionlaw", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/questionlaw[/green] - show the Question gate (M-209)" in (
            text)
        assert ('"/questionlaw": "Usage: /questionlaw | '
                '/questionlaw questioning <questioning-id>') in text

class TestQuestioningDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.questioning_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-questionings"
        verdict = agent.questioning_verdict()
        assert verdict.verdict == "held"
        found = agent.questioning_verdict("view-resumed")
        assert found.verdict == "reported"
        assert found.green_shown == 3
        agent.register_questioning_questioning(_questioning())
        with pytest.raises(ValueError):
            agent.questioning_panel()
        with pytest.raises(ValueError):
            agent.questioning_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_questioning_questioning(_questioning(checks=[]))
        result = agent.view_questioning("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.questioning_index()
        assert [e["check"] for e in result["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert result["index"]["gaps"] == [
            "questioning-bare-question", "questioning-leaping-question"]
        assert "resumed - The answered question questioning (questioning-answered-question)" in (
            result["index_text"])
        questioning = agent.get_questioning_questioning("questioning-leaping-question")
        assert questioning_gaps(questioning, agent.questioning_book()) == (
            "steps from paused to resumed, which the question sequence "
            "does not allow",)
        assert questioning_green(questioning, agent.questioning_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _QUESTIONING_EVENT_TYPES] == []
        agent.close()
