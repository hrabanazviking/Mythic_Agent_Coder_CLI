"""M-207 Keeper Runtime - pure-layer tests.

TIER: integration

The pure layer is the keeper, held as data: one
record per keeping, held whole - the slice it
keeps, named by slice id, its title, the steps it
walked in walk order and the evidence it carries,
held by kind. The keeper walk is explicit -
dealt, watched, judged, restarted, banked, with
their legal steps held as data - and a keeping's
standing is derived at call time: a keeping that
opens anywhere but dealt, steps where the
sequence does not allow, carries a bare claim in
place of held evidence, or has not yet reached
banked stands open, named in its gaps. A
keeping stands only for an active slice: a
keeping naming no held slice, or one that is not
active, refuses by name. The keeping's trace -
its walked steps as one line - is derived at call
time, and a held trace record stands current
only while it agrees with the derived trace. The
index, panel, verdict, board, trace, order and
current keeping are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
slice was actually restarted, dealt or reported
live. The shipped example book is held in a data
file, and a loader reads a book from any file.
No charter row names this slice: the M-171 TUI
charter binds Part VIII alone, and the M-005
method charter names the whole of Part IX as the
part that executes it, both pinned live below.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.keeper_runtime import (
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
    KEEPING_RESOURCE,
    KEEPING_RULE,
    KEEPING_SCHEMA,
    KEEPING_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    KeepingRecord,
    IndexEntry,
    SliceRef,
    NoteRecord,
    KeepingBook,
    KeepingIndex,
    KeepingPanel,
    KeepingRegistry,
    KeepingVerdict,
    KeepingView,
    trace_for_keeping,
    board_record,
    book_record,
    build_trace,
    build_book,
    build_keeping,
    build_slice_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_keeping,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    keeping_for_check,
    keeping_gaps,
    keeping_order,
    keeping_record,
    keeping_green,
    keepings_for_slice,
    first_note,
    format_book,
    format_keeping,
    format_index,
    format_note,
    format_check,
    format_panel,
    format_keeping_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    slice_record,
    load_keeping,
    legal_step,
    load_keeping_file,
    next_check,
    normalize_check,
    normalize_claim_kind,
    normalize_slice_state,
    normalize_stance,
    normalize_view_filter,
    note_for_keeping,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_keeping_args,
    green_keepings,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_keepings,
    validate_book,
    validate_keeping,
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
EXAMPLE_TITLE = "The Keeper runtime at the M-206 slice boundary"
EXAMPLE_CHECKS = ["banked", "banked", "banked"]
EXAMPLE_RUN_IDS = (
    "keeping-clean-deal", "keeping-restart-deal",
    "keeping-runtime-deal", "keeping-bare-deal",
    "keeping-leaping-deal")
EXAMPLE_TRACE = "dealt > watched > judged > banked"


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
        "origin_session": "keeping-test",
    }
    fields.update(overrides)
    return build_slice_ref(fields)


def _keeping(**overrides):
    fields = {
        "keeping_id": "keeping-test",
        "seq": 1,
        "slice_id": "slice-test",
        "title": "A test keeping",
        "checks": ["dealt", "watched", "judged", "banked"],
        "claims": [],
        "detail": "A test keeping held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "keeping-test",
    }
    fields.update(overrides)
    return build_keeping(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "keeping-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "keeping_id": "keeping-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "keeping-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "keeping_id": "keeping-test",
        "trace": "dealt > watched > judged > banked",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "keeping-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(slices=None, keepings=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": KEEPING_SCHEMA,
        "slice": "M-207",
        "keeper_runtime": {"title": "A test keeping book"},
        "slices": [item.to_record() for item in (
            slices if slices is not None else [_ref()])],
        "keepings": [item.to_record() for item in (
            keepings if keepings is not None else [_keeping()])],
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
    return _book(keepings=[
        _keeping(),
        _keeping(keeping_id="keeping-hidden", seq=2,
               title="A hidden keeping", checks=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_keeping()
    assert book.title == EXAMPLE_TITLE
    assert book.keeping_ids() == EXAMPLE_RUN_IDS
    assert book.slice_ids() == (
        "slice-m206-banking", "slice-m207-keeper",
        "slice-m208-pauselines")
    assert [v.view_id for v in book.views] == [
        "view-keepings", "view-complete"]
    assert [m.keeping_id for m in book.notes] == [
        "keeping-clean-deal", "keeping-bare-deal"]
    assert [a.keeping_id for a in book.traces] == ["keeping-clean-deal"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m206-boundary"
    assert panel.as_of == "2026-11-10"
    assert [row.item_id for row in panel.rows] == list(book.keeping_ids())
    derived = derive_panel(book, "view-keepings")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-keepings").verdict == "kept"
    assert derive_verdict(book, "view-keepings").green_shown == 3
    assert derive_verdict(book, "view-complete").verdict == "reported"
    assert derive_verdict(book, "view-complete").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / KEEPING_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == KEEPING_SCHEMA
    assert raw["slice"] == "M-207"
    assert "verdict" not in raw
    assert "keeping_index" not in raw
    assert "board" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-207")]
    assert slice_.title == "Keeper runtime"
    assert slice_.part == 9
    assert "restarts stalled slices" in slice_.summary
    assert "deals the next slice" in slice_.summary
    assert "only ever reports milestones" in slice_.summary
    assert "blockers, and completion" in slice_.summary
    assert "when one banks" in slice_.summary
    assert KEEPING_SLICE == "M-207"

def test_charter_rows_do_not_name_m207():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-207" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert COMPLETE_WORDS == ("complete", "open")
    assert CHECK_FIELDS == ("checks", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "complete", "open")
    assert VERDICT_WORDS == ("reported", "kept", "blocked")
    assert SLICE_STATES == ("active", "queued")
    assert CHECKS == ("dealt", "watched", "judged", "restarted", "banked")
    assert HELD_EVIDENCE == ("heartbeat_log", "deal_ref", "banked_ref", "ledger_row")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["judged"] == ("restarted", "banked")
    assert TRANSITIONS["banked"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_CHECK == "banked"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_slice_state("ACTIVE") == "active"
    assert normalize_check("JUDGED") == "judged"
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
    assert legal_step("judged", "restarted") is True
    assert legal_step("watched", "banked") is False
    assert legal_step("banked", "dealt") is False
    assert next_check("dealt") == "watched"
    assert next_check("judged") == "banked"
    assert next_check("judged", failed=True) == "restarted"
    assert next_check("restarted") == "judged"
    assert next_check("banked") is None
    assert "held as data alone" in KEEPING_RULE
    assert "keeper sequence" in KEEPING_RULE
    assert "M-207" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /keepruntime")

def test_shipped_book_judged_honestly_as_data():
    book = load_keeping()
    opening = book.keeping_for("keeping-clean-deal")
    assert keeping_green(opening, book) is True
    assert keeping_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Keeping: The clean deal keeping",
        "Slice: slice-m206-banking",
        "Check: banked",
        "Claims: heartbeat_log")
    asking = book.keeping_for("keeping-bare-deal")
    assert keeping_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert keeping_green(asking, book) is False
    skipping = book.keeping_for("keeping-leaping-deal")
    assert keeping_gaps(skipping, book) == (
        "steps from watched to banked, which the keeper sequence "
        "does not allow",)
    assert [g.keeping_id for g in green_keepings(book)] == [
        "keeping-clean-deal", "keeping-restart-deal", "keeping-runtime-deal"]
    index = derive_index(book)
    assert [e.check for e in index.entries] == EXAMPLE_CHECKS
    assert index.gaps == ("keeping-bare-deal", "keeping-leaping-deal")
    assert keeping_for_check(book, EXAMPLE_CHECK).keeping_id == (
        "keeping-clean-deal")
    assert keeping_for_check(book, "triple resume") is None
    assert transition_breaks(book) == (
        "keeping-leaping-deal: watched > banked",)
    assert [g.keeping_id for g in keeping_order(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "keeping-clean-deal") == EXAMPLE_TRACE
    assert trace_current(book, "keeping-clean-deal") is True
    assert trace_current(book, "keeping-restart-deal") is False
    assert trace_for_keeping(
        book, "keeping-clean-deal").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_keeping(
        book, "keeping-clean-deal", "note").note_id == (
            "note-note-first")
    assert note_for_keeping(book, "keeping-nope") is None
    assert current_keeping(book).keeping_id == "keeping-bare-deal"
    board = board_record(book)
    assert board["standings"] == [
        {"standing": "complete", "keepings": 3},
        {"standing": "open", "keepings": 2}]
    assert board["total"] == 5
    assert board["current_keeping"] == "keeping-bare-deal"
    assert board["traces"] == [
        {"keeping_id": "keeping-clean-deal", "trace": "current"},
        {"keeping_id": "keeping-restart-deal", "trace": "unheld"},
        {"keeping_id": "keeping-runtime-deal", "trace": "unheld"},
        {"keeping_id": "keeping-bare-deal", "trace": "unheld"},
        {"keeping_id": "keeping-leaping-deal", "trace": "unheld"}]
    assert board["breaks"] == ["keeping-leaping-deal: watched > banked"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 216
    assert citizen["next_slice"] == "M-217"
    assert citizen["m207_title"] == "Keeper runtime"
    assert citizen["m207_part"] == 9
    assert citizen["m207_status"] == "done"

def test_keeping_record_round_trips():
    keeping = _keeping()
    assert validate_keeping(keeping) is keeping
    rebuilt = build_keeping(keeping.to_record())
    assert rebuilt == keeping
    assert rebuilt.item_id == "keeping-test"
    assert rebuilt.check == "banked"
    record = keeping_record(keeping)
    assert record["type"] == "keeping_keeping"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert slice_record(ref)["type"] == "keeping_slice"
    assert slice_record(ref)["state"] == "active"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _keeping(checks=[])
    assert keeping_gaps(silent) == (
        "has passed through no step: the keeping has not started",)
    assert keeping_green(silent) is False
    walking = _keeping(checks=["dealt", "watched"])
    assert keeping_gaps(walking) == (
        "has not reached banked: the keeping stands at watched",)
    assert walking.check == "watched"
    sideways = _keeping(checks=["watched", "judged", "banked"])
    assert keeping_gaps(sideways) == (
        "opens at watched, not at dealt: the keeping opens "
        "with the deal",)
    repaired = _keeping(checks=[
        "dealt", "watched", "judged", "restarted", "judged", "banked"])
    assert keeping_gaps(repaired) == ()
    assert keeping_green(repaired) is True
    with pytest.raises(ValueError):
        _keeping(checks=[42])
    with pytest.raises(ValueError):
        _keeping(checks="inspect as a bare string")
    with pytest.raises(ValueError):
        _keeping(checks=["dealt", "polish"])
    with pytest.raises(ValueError):
        _keeping(claims=["weather"])
    with pytest.raises(ValueError):
        _keeping(claims="heartbeat_log")
    none_keeping = _keeping(checks=None, claims=None)
    assert none_keeping.checks == ()
    assert none_keeping.claims == ()

def test_keeping_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "entries", "coverage", "current_keeping",
                "board", "order"):
        fields = _keeping().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_keeping(fields)
    fields = _keeping().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_keeping(fields)


def test_keeping_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _keeping().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_keeping(fields)


def test_keeping_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _keeping(title="")
    with pytest.raises(ValueError):
        _keeping(slice_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "dealt > watched > judged > banked"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_keepings_own_fields():
    keeping = _keeping(claims=["heartbeat_log"])
    assert plain_lines(keeping) == (
        "Keeping: A test keeping",
        "Slice: slice-test",
        "Check: banked",
        "Claims: heartbeat_log")
    segment = segment_of(keeping)
    assert segment.startswith("keeping-test: A test keeping")
    assert "check: 'banked'" in segment
    assert "gaps: none" in segment
    assert plain_words(keeping).startswith(
        "A test keeping - from slice-test")

def test_red_keepings_stand_named_in_their_gaps():
    asking = _keeping(claims=["feeling", "heartbeat_log", "summary"])
    assert keeping_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert keeping_green(asking) is False
    skipping = _keeping(checks=["dealt", "watched", "banked"])
    assert keeping_gaps(skipping) == (
        "steps from watched to banked, which the keeper sequence "
        "does not allow",)
    book = _book(keepings=[
        _keeping(),
        _keeping(keeping_id="keeping-skipping", seq=2,
             checks=["dealt", "watched", "banked"]),
    ])
    assert transition_breaks(book) == (
        "keeping-skipping: watched > banked",)
    assert current_keeping(book).keeping_id == "keeping-skipping"
    assert [g.keeping_id for g in keeping_order(book)] == [
        "keeping-test", "keeping-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "keeping_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "keeping_note"
    assert record["keeping_id"] == "keeping-test"
    assert view_plain_words(view) == "View view-test: shows all keepings."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_keepings_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.check for e in index.entries] == ["banked"]
    assert index.entries[0] == IndexEntry(
        check="banked",
        keeping_id="keeping-test", title="A test keeping")
    assert index.gaps == ("keeping-hidden",)
    record = index_record(book)
    assert record["type"] == "keeping_index"
    assert record["gaps"] == ["keeping-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "keeping_book"

def test_check_target_reaches_its_keeping_and_an_unheld_target_reaches_nothing():
    book = load_keeping()
    assert keeping_for_check(book, "banked").keeping_id == (
        "keeping-clean-deal")
    assert keeping_for_check(book, "") is None
    assert keeping_for_check(book, None) is None
    assert keeping_for_check(book, "not held at all") is None
    text = format_check(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_keeping()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Keeping note note keeping-clean-deal" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").keeping_id == "keeping-test"
    assert note_for_keeping(book, "keeping-test").note_id == "note-test"
    assert note_for_keeping(book, "keeping-test", "praise") is None
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
    row = build_row(None, _keeping(), book)
    assert row.standing == "complete"
    assert validate_row(row, _keeping(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_keepings():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "kept"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "keeping_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "reported"
    empty_book = _book(keepings=[_keeping(checks=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(KeepingVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_keeping()
    assert [g.keeping_id for g in shown_keepings(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.keeping_id for g in shown_keepings(book, "view-complete")] == [
        "keeping-clean-deal", "keeping-restart-deal", "keeping-runtime-deal"]
    assert [g.keeping_id for g in keepings_for_slice(
        book, "slice-m207-keeper")] == [
            "keeping-runtime-deal", "keeping-bare-deal",
            "keeping-leaping-deal"]
    assert keepings_for_slice(book, "slice-nope") == ()
    assert current_keeping(_mixed_book()).keeping_id == "keeping-hidden"
    assert current_keeping(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "keeping-test") == (
        "dealt > watched > judged > banked")
    assert trace_current(stale, "keeping-test") is False
    assert board_record(stale)["traces"] == [
        {"keeping_id": "keeping-test", "trace": "stale"}]

def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(keepings=[_keeping(), _keeping(seq=2)])
    with pytest.raises(ValueError):
        _book(keepings=[_keeping(), _keeping(keeping_id="keeping-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(keepings=[_keeping(slice_id="slice-nope")])
    with pytest.raises(ValueError):
        _book(slices=[_ref(), _ref(
            slice_id="slice-cold", seq=2, state="queued")],
            keepings=[_keeping(slice_id="slice-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(slice_id="slice-nope")])
    fields = {
        "schema": KEEPING_SCHEMA, "slice": "M-207",
        "keeper_runtime": {"title": "A judged book"},
        "slices": [_ref().to_record()],
        "keepings": [_keeping().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "reported"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_keeping"] = "keeping-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_keeping")
    fields["trace"] = "keeping-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / KEEPING_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "keeper_runtime.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_keeping_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.keeping_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = KeepingRegistry()
    assert registry.title() is None
    registry.register_slice_ref(_ref())
    registry.register_keeping(_keeping())
    registry.register_view(_view())
    assert [g.keeping_id for g in registry.list_keepings()] == ["keeping-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_keeping("keeping-test").title == "A test keeping"
    assert registry.get_slice("slice-test").state == "active"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("keeping-test").keeping_id == "keeping-test"
    with pytest.raises(ValueError):
        registry.register_keeping(_keeping(seq=9))
    with pytest.raises(ValueError):
        registry.register_keeping(_keeping(keeping_id="keeping-two"))
    with pytest.raises(KeyError):
        registry.get_keeping("keeping-nope")
    assert registry.book().title == "An unheld keeping book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = KeepingRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test keeping book"
    assert registry.title() == "A test keeping book"
    assert len(registry.list_keepings()) == 2
    other = KeepingRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    keeping = _keeping()
    assert "A test keeping" in plain_words(keeping)
    assert panel_plain_words(_mixed_book()).startswith(
        "The keeping book holds 2 keepings")
    assert verdict_plain_words(_mixed_book()) == (
        "The keepings stand kept: 1 of 2 shown keepings stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green keepings; red, "
        "named in its gaps: keeping-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_keeping(keeping)
    assert "Keeping: A test keeping" in text
    assert "stands complete" in text
    text = format_keeping(_keeping(checks=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Keeper Gate (M-207) - A test keeping book" in book_text
    assert "keeping-hidden" in format_book(_mixed_book(), "slice-test")
    assert "Keeping panel under view view-test" in format_panel(_mixed_book())
    assert "kept" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "banked - A test keeping (keeping-test)" in index_text
    assert "keeping-hidden" in index_text
    screen = format_keeping_screen()
    assert "The Keeper Gate (M-207)" in screen
    assert "keeping-bare-deal" in screen

def test_parse_args_board_and_loader_targets():
    assert parse_keeping_args("") == ("show", None)
    assert parse_keeping_args(None) == ("show", None)
    assert parse_keeping_args("show") == ("show", None)
    assert parse_keeping_args("keeping keeping-test") == (
        "keeping", "keeping-test")
    assert parse_keeping_args("check banked") == (
        "check", "banked")
    assert parse_keeping_args("slice slice-test") == (
        "slice", "slice-test")
    assert parse_keeping_args("view view-test") == ("view", "view-test")
    assert parse_keeping_args("note note-test") == ("note", "note-test")
    assert parse_keeping_args("index") == ("index", None)
    assert parse_keeping_args("panel") == ("panel", None)
    assert parse_keeping_args("verdict") == ("verdict", None)
    for bad in ("dance", "keeping", "check", "slice", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_keeping_args(bad)
    board = board_record()
    assert board["type"] == "keeping_board"
    assert board["total"] == 5
    assert board["current_keeping"] == "keeping-bare-deal"
    book = load_keeping({
        "schema": KEEPING_SCHEMA, "slice": "M-207",
        "keeper_runtime": {"title": "A judged book"},
        "slices": [_ref().to_record()],
        "keepings": [_keeping().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, KeepingBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_keeping({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_keeping({"slice": "M-999"})
    built = build_keeping(
        keeping_id="keeping-kw", seq=3, slice_id="slice-test",
        title="Kw Keeping", checks=["dealt", "watched", "judged", "banked"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="keeping-test")
    assert built.keeping_id == "keeping-kw"
    assert keeping_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-207 agent layer: the agent holds a keeping
# book for the session, keepings and views are
# published as session news through the
# checkpoint target (journal first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held keepings, the board is derived from
# the held keepings' completeness, the roadmap standing
# is read from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no slice. This layer keepings
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_KEEPING_EVENT_TYPES = (
    "keeping_keeping", "keeping_slice", "keeping_view",
    "keeping_panel", "keeping_verdict")


def _keeping_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_keeping_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / KEEPING_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "keeper_runtime.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestKeepingAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.keeping_status()
        assert status["keepings"] == []
        assert status["slices"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["keeping_book"]["title"] == EXAMPLE_TITLE
        assert len(status["keeping_book"]["slices"]) == 3
        assert len(status["keeping_book"]["keepings"]) == 5
        assert len(status["keeping_book"]["views"]) == 2
        assert len(status["keeping_book"]["notes"]) == 2
        assert len(status["keeping_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m206-boundary"
        assert status["verdict"]["verdict"] == "kept"
        assert status["verdict"]["green_shown"] == 3
        assert [e["check"] for e in status["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert status["index"]["gaps"] == [
            "keeping-bare-deal", "keeping-leaping-deal"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["board"]["total"] == 5
        assert status["board"]["current_keeping"] == "keeping-bare-deal"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 216
        assert status["roadmap"]["next_slice"] == "M-217"
        assert status["roadmap"]["m207_title"] == "Keeper runtime"
        assert "held as data alone" in status["rule"]
        assert "keeping-bare-deal" in status["plain_words"]
        assert "The Keeper Gate (M-207)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._keeping_registry()
        assert agent._keeping_registry() is first
        assert agent._keeping_store is first
        for name in ("keeping_book", "keeping_status", "keeping_panel",
                     "keeping_verdict", "keeping_index", "report_keeping"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_keeping_registry", "keeping_book", "keeping_status",
            "get_keeping_keeping", "get_keeping_view", "get_keeping_note",
            "keeping_keepings_for_slice", "keeping_keepings_green",
            "keeping_panel", "keeping_verdict", "keeping_index",
            "register_keeping_keeping", "register_keeping_view",
            "view_keeping", "register_keeping_book",
            "record_keeping_book", "report_keeping",
            "_publish_keeping_record", "_keeping_screen",
            "_keeping_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.keeping_status()
        assert agent.get_keeping_keeping(
            "keeping-clean-deal").title == "The clean deal keeping"
        assert agent.get_keeping_view(
            "view-keepings").view_filter == "all"
        assert agent.get_keeping_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.keeping_id for d in agent.keeping_keepings_for_slice(
            "slice-m207-keeper")] == [
            "keeping-runtime-deal", "keeping-bare-deal",
            "keeping-leaping-deal"]
        assert [d.keeping_id for d in agent.keeping_keepings_green()] == [
            "keeping-clean-deal", "keeping-restart-deal", "keeping-runtime-deal"]
        agent.keeping_panel()
        agent.keeping_verdict()
        agent.keeping_index()
        agent.report_keeping()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _KEEPING_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_keeping_keeping("keeping-nope")
        with pytest.raises(KeyError):
            agent.get_keeping_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_keeping_note("note-nope")
        with pytest.raises(ValueError):
            agent.keeping_keepings_for_slice("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_keeping_keeping(_keeping())
        status = agent.keeping_status()
        assert [d["keeping_id"] for d in status["keepings"]] == ["keeping-test"]
        assert status["book"]["title"] == "An unheld keeping book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["check"] for e in status["index"]["entries"]] == [
            "banked"]
        assert status["first_note"] is None
        assert "keeping-test" in status["screen"]
    def test_held_keeping_never_falls_back_to_the_example(
            self, agent):
        agent.register_keeping_keeping(_keeping())
        with pytest.raises(KeyError):
            agent.get_keeping_keeping("keeping-clean-deal")
        with pytest.raises(KeyError):
            agent.get_keeping_view("view-keepings")
        with pytest.raises(KeyError):
            agent.get_keeping_note("note-note-first")
        keeping = agent.get_keeping_keeping("keeping-test")
        assert keeping.title == "A test keeping"
        assert agent.keeping_book().title == (
            "An unheld keeping book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_keeping_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.keeping_id == "keeping-clean-deal"
        status = agent.keeping_status()
        assert status["index"]["gaps"] == [
            "keeping-bare-deal", "keeping-leaping-deal"]
        assert status["first_note"]["keeping_id"] == (
            "keeping-clean-deal")
        assert status["first_note"]["stance"] == "note"

class TestKeepingAgentHolding:
    def test_register_keeping_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_keeping_keeping(_keeping())
        assert result["keeping"]["keeping_id"] == "keeping-test"
        assert result["record_news"]["type"] == "keeping_keeping"
        assert "keeping-test" in result["screen"]
        events = _keeping_events(store, session_id, "keeping_keeping")
        assert len(events) == 1
        agent.close()

    def test_duplicate_keeping_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_keeping_keeping(_keeping())
        with pytest.raises(ValueError):
            agent.register_keeping_keeping(_keeping(seq=9))
        with pytest.raises(ValueError):
            agent.register_keeping_keeping(_keeping(keeping_id="keeping-two"))
        events = _keeping_events(store, session_id, "keeping_keeping")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_keeping_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_keeping_events(
            store, session_id, "keeping_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_keeping_keeping(_keeping())
        result = agent.view_keeping("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "keeping_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "reported"
        assert len(_keeping_events(
            store, session_id, "keeping_view")) == 1
        assert len(_keeping_events(
            store, session_id, "keeping_panel")) == 1
        assert len(_keeping_events(
            store, session_id, "keeping_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_keeping_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "keeping_slice", "keeping_keeping", "keeping_view"]
        assert len(_keeping_events(
            store, session_id, "keeping_keeping")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_keeping_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "keeping_panel"
        assert result["index_record"]["gaps"] == [
            "keeping-bare-deal", "keeping-leaping-deal"]
        with pytest.raises(ValueError):
            agent.record_keeping_book()
        assert len(_keeping_events(
            store, session_id, "keeping_slice")) == 3
        assert len(_keeping_events(
            store, session_id, "keeping_keeping")) == 5
        assert len(_keeping_events(
            store, session_id, "keeping_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_keeping_book_file(tmp_path)
        book = load_keeping_file(path)
        result = agent.record_keeping_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_keeping()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "kept"
        assert report["index"]["gaps"] == [
            "keeping-bare-deal", "keeping-leaping-deal"]
        assert "keeping-clean-deal" in report["book_text"]
        assert "banked - The clean deal keeping (keeping-clean-deal)" in report["index_text"]
        agent.register_keeping_keeping(_keeping())
        report = agent.report_keeping()
        assert report["book"]["title"] == "An unheld keeping book"
        assert report["panel"] is None
        assert report["verdict"] is None

class TestKeepingTerminalHeading:
    def test_show_keeping_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/keepruntime")
        assert "The Keeper Gate (M-207)" in text
        _, _, text = _slash(agent, "/keepruntime keeping keeping-clean-deal")
        assert "Keeping: The clean deal keeping" in text
        _, _, text = _slash(
            agent, "/keepruntime check banked")
        assert "Keeping: The clean deal keeping" in text
        _, _, text = _slash(agent, "/keepruntime check triple resume")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/keepruntime slice slice-m207-keeper")
        assert "keeping-bare-deal" in text
        assert "keeping-clean-deal" not in text
        _, _, text = _slash(agent, "/keepruntime view view-keepings")
        assert "filter all" in text
        _, _, text = _slash(agent, "/keepruntime note note-note-first")
        assert "Keeping note note keeping-clean-deal" in text
        _, _, text = _slash(agent, "/keepruntime index")
        assert "Keeping index" in text
        assert "keeping-bare-deal" in text
        _, _, text = _slash(agent, "/keepruntime panel")
        assert "Keeping panel under view view-keepings" in text
        _, _, text = _slash(agent, "/keepruntime verdict")
        assert "kept" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/keepruntime [show|keeping <keeping-id>"
                "|check <check>|slice <slice-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/keepruntime dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/keepruntime keeping keeping-nope")
        assert "no keeping named" in text
@pytest.fixture()
def keeping_handler(agent, monkeypatch):
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


def _keeping_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestKeepingCommand:
    def test_show_is_default(self, keeping_handler, agent):
        keeping_handler._handle_keeping("")
        assert "The Keeper Gate (M-207)" in (
            _keeping_published_text(keeping_handler))

    def test_keeping_check_slice_view_note_index_panel_verdict(
            self, keeping_handler, agent):
        keeping_handler._handle_keeping("keeping keeping-clean-deal")
        assert "Keeping: The clean deal keeping" in _keeping_published_text(
            keeping_handler)
        keeping_handler._handle_keeping(
            "check banked")
        assert "Keeping: The clean deal keeping" in _keeping_published_text(
            keeping_handler)
        keeping_handler._handle_keeping("slice slice-m207-keeper")
        assert "keeping-bare-deal" in _keeping_published_text(
            keeping_handler)
        keeping_handler._handle_keeping("view view-keepings")
        assert "filter all" in _keeping_published_text(keeping_handler)
        keeping_handler._handle_keeping("note note-note-first")
        assert "Keeping note note keeping-clean-deal" in (
            _keeping_published_text(keeping_handler))
        keeping_handler._handle_keeping("index")
        assert "Keeping index" in _keeping_published_text(keeping_handler)
        keeping_handler._handle_keeping("panel")
        assert "Keeping panel under view" in _keeping_published_text(
            keeping_handler)
        keeping_handler._handle_keeping("verdict")
        assert "kept" in _keeping_published_text(keeping_handler)
    def test_bad_grammar_is_published(
            self, keeping_handler, agent):
        keeping_handler._handle_keeping("dance party")
        assert USAGE in _keeping_published_text(keeping_handler)
        keeping_handler._handle_keeping("keeping keeping-nope")
        assert "no keeping named" in _keeping_published_text(
            keeping_handler)


class TestChatScreenRoutingKeeping:
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
        screen.handle_command("/keepruntime panel", _FakeLog())
        assert calls == [("/keepruntime", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/keepruntime[/green] - show the Keeper gate (M-207)" in (
            text)
        assert ('"/keepruntime": "Usage: /keepruntime | '
                '/keepruntime keeping <keeping-id>') in text

class TestKeepingDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.keeping_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-keepings"
        verdict = agent.keeping_verdict()
        assert verdict.verdict == "kept"
        found = agent.keeping_verdict("view-complete")
        assert found.verdict == "reported"
        assert found.green_shown == 3
        agent.register_keeping_keeping(_keeping())
        with pytest.raises(ValueError):
            agent.keeping_panel()
        with pytest.raises(ValueError):
            agent.keeping_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_keeping_keeping(_keeping(checks=[]))
        result = agent.view_keeping("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.keeping_index()
        assert [e["check"] for e in result["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert result["index"]["gaps"] == [
            "keeping-bare-deal", "keeping-leaping-deal"]
        assert "banked - The clean deal keeping (keeping-clean-deal)" in (
            result["index_text"])
        keeping = agent.get_keeping_keeping("keeping-leaping-deal")
        assert keeping_gaps(keeping, agent.keeping_book()) == (
            "steps from watched to banked, which the keeper sequence "
            "does not allow",)
        assert keeping_green(keeping, agent.keeping_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _KEEPING_EVENT_TYPES] == []
        agent.close()
