"""M-243 Cross-app method - pure-layer tests.

TIER: integration

The pure layer is the tracker, held as data: one
record per dispatch, held whole - the hall it
answers for, summoned by hall id, its title, the
steps it walked in walk dispatch and the evidence
it carries, held by hall. The question walk is
explicit - summoned, heard, answered, approved,
held, with their legal steps held as data -
and a dispatch's standing is derived at call
time: a dispatch that opens anywhere but summoned, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet summoned held stands open,
summoned in its gaps. A dispatch stands only for
an active hall: a dispatch naming no held
hall, or one that is not active, refuses by
name. The dispatch's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, ledger, trace, dispatch and current
dispatch are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, approved or
held live. The shipped example book is held
in a data file, and a loader reads a book from
any file. No charter row names this hall: the
M-171 TUI charter binds Part VIII alone, and the
M-005 method charter names the whole of Part X
as the part that executes it, both pinned live
below.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.samtal_bridge import (
    EXAMPLE_STAGE,
    BARE_CLAIMS,
    HELD_EVIDENCE,
    INDEX_ACTION,
    STAGES,
    CLAIM_KINDS,
    TRANSITIONS,
    HALL_STATES,
    STAGE_FIELDS,
    PLAIN_EXPLANATION,
    DISPATCH_RESOURCE,
    DISPATCH_RULE,
    DISPATCH_SCHEMA,
    DISPATCH_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    DispatchRecord,
    IndexDispatch,
    HallRef,
    NoteRecord,
    DispatchBook,
    DispatchIndex,
    DispatchPanel,
    DispatchRegistry,
    DispatchVerdict,
    DispatchView,
    trace_for_dispatch,
    ledger_record,
    book_record,
    build_trace,
    build_book,
    build_dispatch,
    build_hall_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_dispatch,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    dispatch_for_check,
    dispatch_gaps,
    dispatch_dispatch,
    dispatch_record,
    dispatch_green,
    dispatches_for_hall,
    first_note,
    format_book,
    format_dispatch,
    format_index,
    format_note,
    format_stage,
    format_panel,
    format_dispatch_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    hall_record,
    load_dispatch,
    legal_step,
    load_dispatch_file,
    next_stage,
    normalize_stage,
    normalize_claim_kind,
    normalize_hall_state,
    normalize_stance,
    normalize_view_filter,
    note_for_dispatch,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_dispatch_args,
    green_dispatches,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_dispatches,
    validate_book,
    validate_dispatch,
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
EXAMPLE_TITLE = "Samtal bridge at the M-243 slice run"
EXAMPLE_STAGES = ["held", "held", "held"]
EXAMPLE_RUN_IDS = (
    "dispatch-held-dispatch", "dispatch-retried-dispatch",
    "dispatch-own-dispatch", "dispatch-bare-dispatch",
    "dispatch-leaping-dispatch")
EXAMPLE_TRACE = "summoned > heard > answered > approved > held"


def _ref(**overrides):
    fields = {
        "hall_id": "hall-test",
        "seq": 1,
        "title": "A test hall",
        "state": "live",
        "detail": "A test hall reference held as data.",
        "recorded_on": ON,
        "actor": BY,
        "repo": "test hall",
        "origin_session": "dispatch-test",
    }
    fields.update(overrides)
    return build_hall_ref(fields)


def _dispatch(**overrides):
    fields = {
        "dispatch_id": "dispatch-test",
        "seq": 1,
        "hall_id": "hall-test",
        "title": "A test dispatch",
        "stages": ["summoned", "heard", "answered", "approved", "held"],
        "claims": [],
        "detail": "A test dispatch held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "repo": "test hall",
        "origin_session": "dispatch-test",
    }
    fields.update(overrides)
    return build_dispatch(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "repo": "test hall",
        "origin_session": "dispatch-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "dispatch_id": "dispatch-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "repo": "test hall",
        "origin_session": "dispatch-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "dispatch_id": "dispatch-test",
        "trace": "summoned > heard > answered > approved > held",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "repo": "test hall",
        "origin_session": "dispatch-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(halls=None, dispatches=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": DISPATCH_SCHEMA,
        "repo": "M-243",
        "samtal_bridge": {"title": "A test dispatch book"},
        "halls": [item.to_record() for item in (
            halls if halls is not None else [_ref()])],
        "dispatch_records": [item.to_record() for item in (
            dispatches if dispatches is not None else [_dispatch()])],
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
    return _book(dispatches=[
        _dispatch(),
        _dispatch(dispatch_id="dispatch-hidden", seq=2,
               title="A hidden dispatch", stages=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_dispatch()
    assert book.title == EXAMPLE_TITLE
    assert book.dispatch_ids() == EXAMPLE_RUN_IDS
    assert book.hall_ids() == (
        "hall-longhouse", "hall-hearth",
        "hall-archive")
    assert [v.view_id for v in book.views] == [
        "view-dispatches", "view-held"]
    assert [m.dispatch_id for m in book.notes] == [
        "dispatch-held-dispatch", "dispatch-bare-dispatch"]
    assert [a.dispatch_id for a in book.traces] == ["dispatch-held-dispatch"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-samtal"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.dispatch_ids())
    derived = derive_panel(book, "view-dispatches")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-dispatches").verdict == "held"
    assert derive_verdict(book, "view-dispatches").green_shown == 3
    assert derive_verdict(book, "view-held").verdict == "held"
    assert derive_verdict(book, "view-held").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / DISPATCH_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == DISPATCH_SCHEMA
    assert raw["repo"] == "M-243"
    assert "verdict" not in raw
    assert "dispatch_index" not in raw
    assert "ledger" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-243")]
    assert slice_.title == "Samtal bridge"
    assert slice_.part == 10
    assert "a seat in a hall can summon the coder" in slice_.summary
    assert "approvals can be given in the hall" in slice_.summary
    assert DISPATCH_SLICE == "M-243"

def test_charter_rows_do_not_name_m243():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-243" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert COMPLETE_WORDS == ("complete", "open")
    assert STAGE_FIELDS == ("stages", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "complete", "open")
    assert VERDICT_WORDS == ("held", "held", "blocked")
    assert HALL_STATES == ("live", "dormant")
    assert STAGES == ("summoned", "heard", "answered", "approved", "held")
    assert HELD_EVIDENCE == ("hall_ref", "seat_ref", "report_ref", "approval_ref", "scope_ref", "reach_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["approved"] == ("summoned", "held")
    assert TRANSITIONS["held"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_STAGE == "held"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_hall_state("LIVE") == "live"
    assert normalize_stage("ANSWERED") == "answered"
    assert normalize_claim_kind("FEELING") == "feeling"
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    with pytest.raises(ValueError):
        normalize_hall_state("blessed")
    with pytest.raises(ValueError):
        normalize_stage("polish")
    with pytest.raises(ValueError):
        normalize_claim_kind("weather")
    assert legal_step("answered", "approved") is True
    assert legal_step("heard", "held") is False
    assert legal_step("held", "summoned") is False
    assert next_stage("summoned") == "heard"
    assert next_stage("answered") == "approved"
    assert next_stage("approved", failed=True) == "summoned"
    assert next_stage("approved") == "held"
    assert next_stage("held") is None
    assert "held as data alone" in DISPATCH_RULE
    assert "dispatch sequence" in DISPATCH_RULE
    assert "M-243" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /samtalbridge")

def test_shipped_book_judged_honestly_as_data():
    book = load_dispatch()
    opening = book.dispatch_for("dispatch-held-dispatch")
    assert dispatch_green(opening, book) is True
    assert dispatch_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Dispatch: The held dispatch",
        "Hall: hall-longhouse",
        "Stage: held",
        "Claims: hall_ref")
    asking = book.dispatch_for("dispatch-bare-dispatch")
    assert dispatch_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert dispatch_green(asking, book) is False
    skipping = book.dispatch_for("dispatch-leaping-dispatch")
    assert dispatch_gaps(skipping, book) == (
        "steps from heard to held, which the dispatch sequence "
        "does not allow",)
    assert [g.dispatch_id for g in green_dispatches(book)] == [
        "dispatch-held-dispatch", "dispatch-retried-dispatch", "dispatch-own-dispatch"]
    index = derive_index(book)
    assert [e.stage for e in index.dispatches] == EXAMPLE_STAGES
    assert index.gaps == ("dispatch-bare-dispatch", "dispatch-leaping-dispatch")
    assert dispatch_for_check(book, EXAMPLE_STAGE).dispatch_id == (
        "dispatch-held-dispatch")
    assert dispatch_for_check(book, "triple dispatch") is None
    assert transition_breaks(book) == (
        "dispatch-leaping-dispatch: heard > held",)
    assert [g.dispatch_id for g in dispatch_dispatch(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "dispatch-held-dispatch") == EXAMPLE_TRACE
    assert trace_current(book, "dispatch-held-dispatch") is True
    assert trace_current(book, "dispatch-retried-dispatch") is False
    assert trace_for_dispatch(
        book, "dispatch-held-dispatch").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_dispatch(
        book, "dispatch-held-dispatch", "note").note_id == (
            "note-note-first")
    assert note_for_dispatch(book, "dispatch-nope") is None
    assert current_dispatch(book).dispatch_id == "dispatch-bare-dispatch"
    ledger = ledger_record(book)
    assert ledger["standings"] == [
        {"standing": "complete", "dispatch_records": 3},
        {"standing": "open", "dispatch_records": 2}]
    assert ledger["total"] == 5
    assert ledger["current_dispatch"] == "dispatch-bare-dispatch"
    assert ledger["traces"] == [
        {"dispatch_id": "dispatch-held-dispatch", "trace": "current"},
        {"dispatch_id": "dispatch-retried-dispatch", "trace": "unheld"},
        {"dispatch_id": "dispatch-own-dispatch", "trace": "unheld"},
        {"dispatch_id": "dispatch-bare-dispatch", "trace": "unheld"},
        {"dispatch_id": "dispatch-leaping-dispatch", "trace": "unheld"}]
    assert ledger["breaks"] == ["dispatch-leaping-dispatch: heard > held"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 242
    assert citizen["next_slice"] == "M-243"
    assert citizen["m243_title"] == "Samtal bridge"
    assert citizen["m243_part"] == 10
    assert citizen["m243_status"] == "queued"

def test_dispatch_record_round_trips():
    dispatch = _dispatch()
    assert validate_dispatch(dispatch) is dispatch
    rebuilt = build_dispatch(dispatch.to_record())
    assert rebuilt == dispatch
    assert rebuilt.item_id == "dispatch-test"
    assert rebuilt.stage == "held"
    record = dispatch_record(dispatch)
    assert record["type"] == "dispatch_dispatch"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert hall_record(ref)["type"] == "dispatch_run"
    assert hall_record(ref)["state"] == "live"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _dispatch(stages=[])
    assert dispatch_gaps(silent) == (
        "has passed through no step: the dispatch has not started",)
    assert dispatch_green(silent) is False
    walking = _dispatch(stages=["summoned", "heard"])
    assert dispatch_gaps(walking) == (
        "has not reached held: the dispatch stands at heard",)
    assert walking.stage == "heard"
    sideways = _dispatch(stages=["heard", "answered", "approved", "held"])
    assert dispatch_gaps(sideways) == (
        "opens at heard, not at summoned: the dispatch opens "
        "with the reflection",)
    repaired = _dispatch(stages=["summoned", "heard", "answered", "approved", "summoned", "heard", "answered", "approved", "held"])
    assert dispatch_gaps(repaired) == ()
    assert dispatch_green(repaired) is True
    with pytest.raises(ValueError):
        _dispatch(stages=[42])
    with pytest.raises(ValueError):
        _dispatch(stages="inspect as a bare string")
    with pytest.raises(ValueError):
        _dispatch(stages=["summoned", "polish"])
    with pytest.raises(ValueError):
        _dispatch(claims=["weather"])
    with pytest.raises(ValueError):
        _dispatch(claims="hall_ref")
    none_dispatch = _dispatch(stages=None, claims=None)
    assert none_dispatch.stages == ()
    assert none_dispatch.claims == ()

def test_reach_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "dispatches", "coverage", "current_dispatch",
                "ledger", "dispatch"):
        fields = _dispatch().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_dispatch(fields)
    fields = _dispatch().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_dispatch(fields)


def test_reach_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _dispatch().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_dispatch(fields)


def test_dispatch_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _dispatch(title="")
    with pytest.raises(ValueError):
        _dispatch(hall_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "summoned > heard > answered > approved > held"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_dispatches_own_fields():
    dispatch = _dispatch(claims=["hall_ref"])
    assert plain_lines(dispatch) == (
        "Dispatch: A test dispatch",
        "Hall: hall-test",
        "Stage: held",
        "Claims: hall_ref")
    segment = segment_of(dispatch)
    assert segment.startswith("dispatch-test: A test dispatch")
    assert "stage: 'held'" in segment
    assert "gaps: none" in segment
    assert plain_words(dispatch).startswith(
        "A test dispatch - from hall-test")

def test_red_dispatches_stand_named_in_their_gaps():
    asking = _dispatch(claims=["feeling", "hall_ref", "summary"])
    assert dispatch_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert dispatch_green(asking) is False
    skipping = _dispatch(stages=["summoned", "heard", "held"])
    assert dispatch_gaps(skipping) == (
        "steps from heard to held, which the dispatch sequence "
        "does not allow",)
    book = _book(dispatches=[
        _dispatch(),
        _dispatch(dispatch_id="dispatch-skipping", seq=2,
             stages=["summoned", "heard", "held"]),
    ])
    assert transition_breaks(book) == (
        "dispatch-skipping: heard > held",)
    assert current_dispatch(book).dispatch_id == "dispatch-skipping"
    assert [g.dispatch_id for g in dispatch_dispatch(book)] == [
        "dispatch-test", "dispatch-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "dispatch_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "dispatch_note"
    assert record["dispatch_id"] == "dispatch-test"
    assert view_plain_words(view) == "View view-test: shows all dispatches."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_dispatches_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.stage for e in index.dispatches] == ["held"]
    assert index.dispatches[0] == IndexDispatch(
        stage="held",
        dispatch_id="dispatch-test", title="A test dispatch")
    assert index.gaps == ("dispatch-hidden",)
    record = index_record(book)
    assert record["type"] == "dispatch_index"
    assert record["gaps"] == ["dispatch-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "dispatch_book"

def test_check_target_reaches_its_dispatch_and_an_unheld_target_reaches_nothing():
    book = load_dispatch()
    assert dispatch_for_check(book, "held").dispatch_id == (
        "dispatch-held-dispatch")
    assert dispatch_for_check(book, "") is None
    assert dispatch_for_check(book, None) is None
    assert dispatch_for_check(book, "not held at all") is None
    text = format_stage(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_dispatch()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Dispatch note note dispatch-held-dispatch" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").dispatch_id == "dispatch-test"
    assert note_for_dispatch(book, "dispatch-test").note_id == "note-test"
    assert note_for_dispatch(book, "dispatch-test", "praise") is None
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
    row = build_row(None, _dispatch(), book)
    assert row.standing == "complete"
    assert validate_row(row, _dispatch(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_dispatches():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "dispatch_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "held"
    empty_book = _book(dispatches=[_dispatch(stages=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(DispatchVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_dispatches():
    book = load_dispatch()
    assert [g.dispatch_id for g in shown_dispatches(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.dispatch_id for g in shown_dispatches(book, "view-held")] == [
        "dispatch-held-dispatch", "dispatch-retried-dispatch", "dispatch-own-dispatch"]
    assert [g.dispatch_id for g in dispatches_for_hall(
        book, "hall-hearth")] == [
            "dispatch-own-dispatch", "dispatch-bare-dispatch",
            "dispatch-leaping-dispatch"]
    assert dispatches_for_hall(book, "hall-nope") == ()
    assert current_dispatch(_mixed_book()).dispatch_id == "dispatch-hidden"
    assert current_dispatch(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "dispatch-test") == (
        "summoned > heard > answered > approved > held")
    assert trace_current(stale, "dispatch-test") is False
    assert ledger_record(stale)["traces"] == [
        {"dispatch_id": "dispatch-test", "trace": "stale"}]

def test_seat_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(dispatches=[_dispatch(), _dispatch(seq=2)])
    with pytest.raises(ValueError):
        _book(dispatches=[_dispatch(), _dispatch(dispatch_id="dispatch-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(dispatches=[_dispatch(hall_id="hall-nope")])
    with pytest.raises(ValueError):
        _book(halls=[_ref(), _ref(
            hall_id="hall-cold", seq=2, state="dormant")],
            dispatches=[_dispatch(hall_id="hall-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(hall_id="hall-nope")])
    fields = {
        "schema": DISPATCH_SCHEMA, "repo": "M-243",
        "samtal_bridge": {"title": "A answered book"},
        "halls": [_ref().to_record()],
        "dispatch_records": [_dispatch().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "held"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_dispatch"] = "dispatch-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_dispatch")
    fields["trace"] = "dispatch-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / DISPATCH_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "samtal_bridge.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_dispatch_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.dispatch_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = DispatchRegistry()
    assert registry.title() is None
    registry.register_hall_ref(_ref())
    registry.register_dispatch(_dispatch())
    registry.register_view(_view())
    assert [g.dispatch_id for g in registry.list_dispatches()] == ["dispatch-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_dispatch("dispatch-test").title == "A test dispatch"
    assert registry.get_slice("hall-test").state == "live"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("dispatch-test").dispatch_id == "dispatch-test"
    with pytest.raises(ValueError):
        registry.register_dispatch(_dispatch(seq=9))
    with pytest.raises(ValueError):
        registry.register_dispatch(_dispatch(dispatch_id="dispatch-two"))
    with pytest.raises(KeyError):
        registry.get_dispatch("dispatch-nope")
    assert registry.book().title == "An unheld dispatch book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = DispatchRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test dispatch book"
    assert registry.title() == "A test dispatch book"
    assert len(registry.list_dispatches()) == 2
    other = DispatchRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    dispatch = _dispatch()
    assert "A test dispatch" in plain_words(dispatch)
    assert panel_plain_words(_mixed_book()).startswith(
        "The dispatch book holds 2 dispatches")
    assert verdict_plain_words(_mixed_book()) == (
        "The dispatches stand held: 1 of 2 shown dispatches stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green dispatches; red, "
        "summoned in its gaps: dispatch-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_dispatch(dispatch)
    assert "Dispatch: A test dispatch" in text
    assert "stands complete" in text
    text = format_dispatch(_dispatch(stages=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Samtal Bridge (M-243) - A test dispatch book" in book_text
    assert "dispatch-hidden" in format_book(_mixed_book(), "hall-test")
    assert "Dispatch panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "held - A test dispatch (dispatch-test)" in index_text
    assert "dispatch-hidden" in index_text
    screen = format_dispatch_screen()
    assert "The Samtal Bridge (M-243)" in screen
    assert "dispatch-bare-dispatch" in screen

def test_parse_args_well_and_loader_targets():
    assert parse_dispatch_args("") == ("show", None)
    assert parse_dispatch_args(None) == ("show", None)
    assert parse_dispatch_args("show") == ("show", None)
    assert parse_dispatch_args("dispatch dispatch-test") == (
        "dispatch", "dispatch-test")
    assert parse_dispatch_args("stage held") == (
        "stage", "held")
    assert parse_dispatch_args("hall hall-test") == (
        "hall", "hall-test")
    assert parse_dispatch_args("view view-test") == ("view", "view-test")
    assert parse_dispatch_args("note note-test") == ("note", "note-test")
    assert parse_dispatch_args("index") == ("index", None)
    assert parse_dispatch_args("panel") == ("panel", None)
    assert parse_dispatch_args("verdict") == ("verdict", None)
    for bad in ("dance", "dispatch", "stage", "hall", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_dispatch_args(bad)
    ledger = ledger_record()
    assert ledger["type"] == "dispatch_well"
    assert ledger["total"] == 5
    assert ledger["current_dispatch"] == "dispatch-bare-dispatch"
    book = load_dispatch({
        "schema": DISPATCH_SCHEMA, "repo": "M-243",
        "samtal_bridge": {"title": "A answered book"},
        "halls": [_ref().to_record()],
        "dispatch_records": [_dispatch().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, DispatchBook)
    assert book.title == "A answered book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_dispatch({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_dispatch({"repo": "M-999"})
    built = build_dispatch(
        dispatch_id="dispatch-kw", seq=3, hall_id="hall-test",
        title="Kw Dispatch", stages=["summoned", "heard", "answered", "approved", "held"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        repo="test hall", origin_session="dispatch-test")
    assert built.dispatch_id == "dispatch-kw"
    assert dispatch_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-243 agent layer: the agent holds a dispatch
# book for the session, dispatches and views are
# published as session news through the
# checkpoint target (ledger first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held dispatches, the ledger is derived from
# the held dispatches' completeness, the roadmap standing
# is approved from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no hall. This layer dispatches
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session ledger news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_DISPATCH_EVENT_TYPES = (
    "dispatch_dispatch", "dispatch_run", "dispatch_view",
    "dispatch_panel", "dispatch_verdict")


def _dispatch_events(store, session_id, hall):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == hall]


def _write_samtalbridge_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / DISPATCH_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "samtal_bridge.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestDispatchAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.samtalbridge_status()
        assert status["dispatch_records"] == []
        assert status["halls"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["samtalbridge_book"]["title"] == EXAMPLE_TITLE
        assert len(status["samtalbridge_book"]["halls"]) == 3
        assert len(status["samtalbridge_book"]["dispatch_records"]) == 5
        assert len(status["samtalbridge_book"]["views"]) == 2
        assert len(status["samtalbridge_book"]["notes"]) == 2
        assert len(status["samtalbridge_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-samtal"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["stage"] for e in status["index"]["dispatches"]] == (
            EXAMPLE_STAGES)
        assert status["index"]["gaps"] == [
            "dispatch-bare-dispatch", "dispatch-leaping-dispatch"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["ledger"]["total"] == 5
        assert status["ledger"]["current_dispatch"] == "dispatch-bare-dispatch"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 242
        assert status["roadmap"]["next_slice"] == "M-243"
        assert status["roadmap"]["m243_title"] == "Samtal bridge"
        assert "held as data alone" in status["rule"]
        assert "dispatch-bare-dispatch" in status["plain_words"]
        assert "The Samtal Bridge (M-243)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._samtalbridge_registry()
        assert agent._samtalbridge_registry() is first
        assert agent._samtalbridge_store is first
        for name in ("samtalbridge_book", "samtalbridge_status", "samtalbridge_panel",
                     "samtalbridge_verdict", "samtalbridge_index", "report_samtalbridge"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_samtalbridge_registry", "samtalbridge_book", "samtalbridge_status",
            "get_samtalbridge_dispatch", "get_samtalbridge_view", "get_samtalbridge_note",
            "dispatches_for_hall", "samtalbridge_green",
            "samtalbridge_panel", "samtalbridge_verdict", "samtalbridge_index",
            "register_samtalbridge_dispatch", "register_samtalbridge_view",
            "view_samtalbridge", "register_samtalbridge_book",
            "record_samtalbridge_book", "report_samtalbridge",
            "_publish_samtalbridge_record", "_samtalbridge_screen",
            "_samtalbridge_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.samtalbridge_status()
        assert agent.get_samtalbridge_dispatch(
            "dispatch-held-dispatch").title == "The held dispatch"
        assert agent.get_samtalbridge_view(
            "view-dispatches").view_filter == "all"
        assert agent.get_samtalbridge_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.dispatch_id for d in agent.dispatches_for_hall(
            "hall-hearth")] == [
            "dispatch-own-dispatch", "dispatch-bare-dispatch",
            "dispatch-leaping-dispatch"]
        assert [d.dispatch_id for d in agent.samtalbridge_green()] == [
            "dispatch-held-dispatch", "dispatch-retried-dispatch", "dispatch-own-dispatch"]
        agent.samtalbridge_panel()
        agent.samtalbridge_verdict()
        agent.samtalbridge_index()
        agent.report_samtalbridge()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _DISPATCH_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_samtalbridge_dispatch("dispatch-nope")
        with pytest.raises(KeyError):
            agent.get_samtalbridge_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_samtalbridge_note("note-nope")
        with pytest.raises(ValueError):
            agent.dispatches_for_hall("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_samtalbridge_dispatch(_dispatch())
        status = agent.samtalbridge_status()
        assert [d["dispatch_id"] for d in status["dispatch_records"]] == ["dispatch-test"]
        assert status["book"]["title"] == "An unheld dispatch book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["stage"] for e in status["index"]["dispatches"]] == [
            "held"]
        assert status["first_note"] is None
        assert "dispatch-test" in status["screen"]
    def test_held_dispatch_never_falls_back_to_the_example(
            self, agent):
        agent.register_samtalbridge_dispatch(_dispatch())
        with pytest.raises(KeyError):
            agent.get_samtalbridge_dispatch("dispatch-held-dispatch")
        with pytest.raises(KeyError):
            agent.get_samtalbridge_view("view-dispatches")
        with pytest.raises(KeyError):
            agent.get_samtalbridge_note("note-note-first")
        dispatch = agent.get_samtalbridge_dispatch("dispatch-test")
        assert dispatch.title == "A test dispatch"
        assert agent.samtalbridge_book().title == (
            "An unheld dispatch book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_samtalbridge_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.dispatch_id == "dispatch-held-dispatch"
        status = agent.samtalbridge_status()
        assert status["index"]["gaps"] == [
            "dispatch-bare-dispatch", "dispatch-leaping-dispatch"]
        assert status["first_note"]["dispatch_id"] == (
            "dispatch-held-dispatch")
        assert status["first_note"]["stance"] == "note"

class TestDispatchAgentHolding:
    def test_register_dispatch_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_samtalbridge_dispatch(_dispatch())
        assert result["dispatch"]["dispatch_id"] == "dispatch-test"
        assert result["record_news"]["type"] == "dispatch_dispatch"
        assert "dispatch-test" in result["screen"]
        events = _dispatch_events(store, session_id, "dispatch_dispatch")
        assert len(events) == 1
        agent.close()

    def test_duplicate_reach_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_samtalbridge_dispatch(_dispatch())
        with pytest.raises(ValueError):
            agent.register_samtalbridge_dispatch(_dispatch(seq=9))
        with pytest.raises(ValueError):
            agent.register_samtalbridge_dispatch(_dispatch(dispatch_id="dispatch-two"))
        events = _dispatch_events(store, session_id, "dispatch_dispatch")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_samtalbridge_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_dispatch_events(
            store, session_id, "dispatch_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_samtalbridge_dispatch(_dispatch())
        result = agent.view_samtalbridge("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "dispatch_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "held"
        assert len(_dispatch_events(
            store, session_id, "dispatch_view")) == 1
        assert len(_dispatch_events(
            store, session_id, "dispatch_panel")) == 1
        assert len(_dispatch_events(
            store, session_id, "dispatch_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_dispatch(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_samtalbridge_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "dispatch_run", "dispatch_dispatch", "dispatch_view"]
        assert len(_dispatch_events(
            store, session_id, "dispatch_dispatch")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_samtalbridge_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "dispatch_panel"
        assert result["index_record"]["gaps"] == [
            "dispatch-bare-dispatch", "dispatch-leaping-dispatch"]
        with pytest.raises(ValueError):
            agent.record_samtalbridge_book()
        assert len(_dispatch_events(
            store, session_id, "dispatch_run")) == 3
        assert len(_dispatch_events(
            store, session_id, "dispatch_dispatch")) == 5
        assert len(_dispatch_events(
            store, session_id, "dispatch_view")) == 2
        agent.close()

    def test_book_from_a_file_is_reached_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_samtalbridge_book_file(tmp_path)
        book = load_dispatch_file(path)
        result = agent.record_samtalbridge_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_runrt_renders_example_then_held_book_only(self, agent):
        dispatch = agent.report_samtalbridge()
        assert dispatch["book"]["title"] == EXAMPLE_TITLE
        assert dispatch["verdict"]["verdict"] == "held"
        assert dispatch["index"]["gaps"] == [
            "dispatch-bare-dispatch", "dispatch-leaping-dispatch"]
        assert "dispatch-held-dispatch" in dispatch["book_text"]
        assert "held - The held dispatch (dispatch-held-dispatch)" in dispatch["index_text"]
        agent.register_samtalbridge_dispatch(_dispatch())
        dispatch = agent.report_samtalbridge()
        assert dispatch["book"]["title"] == "An unheld dispatch book"
        assert dispatch["panel"] is None
        assert dispatch["verdict"] is None

class TestDispatchTerminalHeading:
    def test_show_dispatch_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/samtalbridge")
        assert "The Samtal Bridge (M-243)" in text
        _, _, text = _slash(agent, "/samtalbridge dispatch dispatch-held-dispatch")
        assert "Dispatch: The held dispatch" in text
        _, _, text = _slash(
            agent, "/samtalbridge stage held")
        assert "Dispatch: The held dispatch" in text
        _, _, text = _slash(agent, "/samtalbridge stage triple dispatch")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/samtalbridge hall hall-hearth")
        assert "dispatch-bare-dispatch" in text
        assert "dispatch-held-dispatch" not in text
        _, _, text = _slash(agent, "/samtalbridge view view-dispatches")
        assert "filter all" in text
        _, _, text = _slash(agent, "/samtalbridge note note-note-first")
        assert "Dispatch note note dispatch-held-dispatch" in text
        _, _, text = _slash(agent, "/samtalbridge index")
        assert "Dispatch index" in text
        assert "dispatch-bare-dispatch" in text
        _, _, text = _slash(agent, "/samtalbridge panel")
        assert "Dispatch panel under view view-dispatches" in text
        _, _, text = _slash(agent, "/samtalbridge verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/samtalbridge [show|dispatch <dispatch-id>"
                "|stage <stage>|hall <hall-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/samtalbridge dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/samtalbridge dispatch dispatch-nope")
        assert "no dispatch summoned" in text
@pytest.fixture()
def dispatch_handler(agent, monkeypatch):
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


def _dispatch_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestDispatchSource:
    def test_show_is_default(self, dispatch_handler, agent):
        dispatch_handler._handle_samtalbridge("")
        assert "The Samtal Bridge (M-243)" in (
            _dispatch_published_text(dispatch_handler))

    def test_dispatch_check_slice_view_note_index_panel_verdict(
            self, dispatch_handler, agent):
        dispatch_handler._handle_samtalbridge("dispatch dispatch-held-dispatch")
        assert "Dispatch: The held dispatch" in _dispatch_published_text(
            dispatch_handler)
        dispatch_handler._handle_samtalbridge(
            "stage held")
        assert "Dispatch: The held dispatch" in _dispatch_published_text(
            dispatch_handler)
        dispatch_handler._handle_samtalbridge("hall hall-hearth")
        assert "dispatch-bare-dispatch" in _dispatch_published_text(
            dispatch_handler)
        dispatch_handler._handle_samtalbridge("view view-dispatches")
        assert "filter all" in _dispatch_published_text(dispatch_handler)
        dispatch_handler._handle_samtalbridge("note note-note-first")
        assert "Dispatch note note dispatch-held-dispatch" in (
            _dispatch_published_text(dispatch_handler))
        dispatch_handler._handle_samtalbridge("index")
        assert "Dispatch index" in _dispatch_published_text(dispatch_handler)
        dispatch_handler._handle_samtalbridge("panel")
        assert "Dispatch panel under view" in _dispatch_published_text(
            dispatch_handler)
        dispatch_handler._handle_samtalbridge("verdict")
        assert "held" in _dispatch_published_text(dispatch_handler)
    def test_bad_grammar_is_published(
            self, dispatch_handler, agent):
        dispatch_handler._handle_samtalbridge("dance party")
        assert USAGE in _dispatch_published_text(dispatch_handler)
        dispatch_handler._handle_samtalbridge("dispatch dispatch-nope")
        assert "no dispatch summoned" in _dispatch_published_text(
            dispatch_handler)


class TestChatScreenRoutingDispatch:
    def test_onwell_routes_as_system_hall(self, monkeypatch):
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
        screen.handle_command("/samtalbridge panel", _FakeLog())
        assert calls == [("/samtalbridge", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/samtalbridge[/green] - show the Samtal bridge (M-243)" in (
            text)
        assert ('"/samtalbridge": "Usage: /samtalbridge | '
                '/samtalbridge dispatch <dispatch-id>') in text

class TestDispatchDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.samtalbridge_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-dispatches"
        verdict = agent.samtalbridge_verdict()
        assert verdict.verdict == "held"
        summoned = agent.samtalbridge_verdict("view-held")
        assert summoned.verdict == "held"
        assert summoned.green_shown == 3
        agent.register_samtalbridge_dispatch(_dispatch())
        with pytest.raises(ValueError):
            agent.samtalbridge_panel()
        with pytest.raises(ValueError):
            agent.samtalbridge_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_samtalbridge_dispatch(_dispatch(stages=[]))
        result = agent.view_samtalbridge("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.samtalbridge_index()
        assert [e["stage"] for e in result["index"]["dispatches"]] == (
            EXAMPLE_STAGES)
        assert result["index"]["gaps"] == [
            "dispatch-bare-dispatch", "dispatch-leaping-dispatch"]
        assert "held - The held dispatch (dispatch-held-dispatch)" in (
            result["index_text"])
        dispatch = agent.get_samtalbridge_dispatch("dispatch-leaping-dispatch")
        assert dispatch_gaps(dispatch, agent.samtalbridge_book()) == (
            "steps from heard to held, which the dispatch sequence "
            "does not allow",)
        assert dispatch_green(dispatch, agent.samtalbridge_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _DISPATCH_EVENT_TYPES] == []
        agent.close()
