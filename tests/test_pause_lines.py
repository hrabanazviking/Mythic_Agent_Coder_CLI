"""M-208 The Pause-Lines Wired - pure-layer tests.

TIER: integration

The pure layer is the guard, held as data: one
record per pausing, held whole - the slice it
guards, named by slice id, its title, the steps
it walked in walk order and the evidence it
carries, held by kind. The pause walk is
explicit - proposed, checked, paused, reasked,
crossed, with their legal steps held as data -
and a pausing's standing is derived at call
time: a pausing that opens anywhere but
proposed, steps where the sequence does not
allow, carries a bare claim in place of held
evidence, or has not yet reached crossed stands
open, named in its gaps. A pausing stands only
for an active slice: a pausing naming no held
slice, or one that is not active, refuses by
name. The pausing's trace - its walked steps as
one line - is derived at call time, and a held
trace record stands current only while it
agrees with the derived trace. The index,
panel, verdict, board, trace, order and current
pausing are derived at call time, never stored
where they could drift, and a stored one
refuses by name, as does a record claiming a
slice was actually crossed, approved or
reported live. The shipped example book is held
in a data file, and a loader reads a book from
any file. No charter row names this slice: the
M-171 TUI charter binds Part VIII alone, and
the M-005 method charter names the whole of
Part IX as the part that executes it, both
pinned live below.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.pause_lines import (
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
    PAUSING_RESOURCE,
    PAUSING_RULE,
    PAUSING_SCHEMA,
    PAUSING_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    PausingRecord,
    IndexEntry,
    SliceRef,
    NoteRecord,
    PausingBook,
    PausingIndex,
    PausingPanel,
    PausingRegistry,
    PausingVerdict,
    PausingView,
    trace_for_pausing,
    board_record,
    book_record,
    build_trace,
    build_book,
    build_pausing,
    build_slice_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_pausing,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    pausing_for_check,
    pausing_gaps,
    pausing_order,
    pausing_record,
    pausing_green,
    pausings_for_slice,
    first_note,
    format_book,
    format_pausing,
    format_index,
    format_note,
    format_check,
    format_panel,
    format_pausing_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    slice_record,
    load_pausing,
    legal_step,
    load_pausing_file,
    next_check,
    normalize_check,
    normalize_claim_kind,
    normalize_slice_state,
    normalize_stance,
    normalize_view_filter,
    note_for_pausing,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_pausing_args,
    green_pausings,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_pausings,
    validate_book,
    validate_pausing,
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
EXAMPLE_TITLE = "The pause-lines wired at the M-207 slice boundary"
EXAMPLE_CHECKS = ["crossed", "crossed", "crossed"]
EXAMPLE_RUN_IDS = (
    "pausing-approved-crossing", "pausing-reasked-crossing",
    "pausing-wired-crossing", "pausing-bare-crossing",
    "pausing-leaping-crossing")
EXAMPLE_TRACE = "proposed > checked > paused > crossed"


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
        "origin_session": "pausing-test",
    }
    fields.update(overrides)
    return build_slice_ref(fields)


def _pausing(**overrides):
    fields = {
        "pausing_id": "pausing-test",
        "seq": 1,
        "slice_id": "slice-test",
        "title": "A test pausing",
        "checks": ["proposed", "checked", "paused", "crossed"],
        "claims": [],
        "detail": "A test pausing held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "pausing-test",
    }
    fields.update(overrides)
    return build_pausing(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "pausing-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "pausing_id": "pausing-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "pausing-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "pausing_id": "pausing-test",
        "trace": "proposed > checked > paused > crossed",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "pausing-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(slices=None, pausings=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": PAUSING_SCHEMA,
        "slice": "M-208",
        "pause_lines": {"title": "A test pausing book"},
        "slices": [item.to_record() for item in (
            slices if slices is not None else [_ref()])],
        "pausings": [item.to_record() for item in (
            pausings if pausings is not None else [_pausing()])],
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
    return _book(pausings=[
        _pausing(),
        _pausing(pausing_id="pausing-hidden", seq=2,
               title="A hidden pausing", checks=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_pausing()
    assert book.title == EXAMPLE_TITLE
    assert book.pausing_ids() == EXAMPLE_RUN_IDS
    assert book.slice_ids() == (
        "slice-m207-keeper", "slice-m208-pauselines",
        "slice-m209-question")
    assert [v.view_id for v in book.views] == [
        "view-pausings", "view-crossed"]
    assert [m.pausing_id for m in book.notes] == [
        "pausing-approved-crossing", "pausing-bare-crossing"]
    assert [a.pausing_id for a in book.traces] == ["pausing-approved-crossing"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m207-boundary"
    assert panel.as_of == "2026-11-10"
    assert [row.item_id for row in panel.rows] == list(book.pausing_ids())
    derived = derive_panel(book, "view-pausings")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-pausings").verdict == "held"
    assert derive_verdict(book, "view-pausings").green_shown == 3
    assert derive_verdict(book, "view-crossed").verdict == "reported"
    assert derive_verdict(book, "view-crossed").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / PAUSING_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == PAUSING_SCHEMA
    assert raw["slice"] == "M-208"
    assert "verdict" not in raw
    assert "pausing_index" not in raw
    assert "board" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-208")]
    assert slice_.title == "The pause-lines wired"
    assert slice_.part == 9
    assert "destruction, irreversible infra" in slice_.summary
    assert "*cannot* cross them unapproved" in slice_.summary
    assert "the lines are data" in slice_.summary
    assert "user's own wording preserved" in slice_.summary
    assert "sending-as-user, secrets, security" in slice_.summary
    assert PAUSING_SLICE == "M-208"

def test_charter_rows_do_not_name_m208():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-208" not in owners
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
    assert CHECKS == ("proposed", "checked", "paused", "reasked", "crossed")
    assert HELD_EVIDENCE == ("approval_record", "wording_ref", "crossing_ref", "ledger_row")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["paused"] == ("reasked", "crossed")
    assert TRANSITIONS["crossed"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_CHECK == "crossed"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_slice_state("ACTIVE") == "active"
    assert normalize_check("PAUSED") == "paused"
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
    assert legal_step("paused", "reasked") is True
    assert legal_step("checked", "crossed") is False
    assert legal_step("crossed", "proposed") is False
    assert next_check("proposed") == "checked"
    assert next_check("paused") == "crossed"
    assert next_check("paused", failed=True) == "reasked"
    assert next_check("reasked") == "paused"
    assert next_check("crossed") is None
    assert "held as data alone" in PAUSING_RULE
    assert "pause sequence" in PAUSING_RULE
    assert "M-208" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /pauselines")

def test_shipped_book_judged_honestly_as_data():
    book = load_pausing()
    opening = book.pausing_for("pausing-approved-crossing")
    assert pausing_green(opening, book) is True
    assert pausing_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Pausing: The approved crossing pausing",
        "Slice: slice-m207-keeper",
        "Check: crossed",
        "Claims: approval_record")
    asking = book.pausing_for("pausing-bare-crossing")
    assert pausing_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert pausing_green(asking, book) is False
    skipping = book.pausing_for("pausing-leaping-crossing")
    assert pausing_gaps(skipping, book) == (
        "steps from checked to crossed, which the pause sequence "
        "does not allow",)
    assert [g.pausing_id for g in green_pausings(book)] == [
        "pausing-approved-crossing", "pausing-reasked-crossing", "pausing-wired-crossing"]
    index = derive_index(book)
    assert [e.check for e in index.entries] == EXAMPLE_CHECKS
    assert index.gaps == ("pausing-bare-crossing", "pausing-leaping-crossing")
    assert pausing_for_check(book, EXAMPLE_CHECK).pausing_id == (
        "pausing-approved-crossing")
    assert pausing_for_check(book, "triple resume") is None
    assert transition_breaks(book) == (
        "pausing-leaping-crossing: checked > crossed",)
    assert [g.pausing_id for g in pausing_order(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "pausing-approved-crossing") == EXAMPLE_TRACE
    assert trace_current(book, "pausing-approved-crossing") is True
    assert trace_current(book, "pausing-reasked-crossing") is False
    assert trace_for_pausing(
        book, "pausing-approved-crossing").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_pausing(
        book, "pausing-approved-crossing", "note").note_id == (
            "note-note-first")
    assert note_for_pausing(book, "pausing-nope") is None
    assert current_pausing(book).pausing_id == "pausing-bare-crossing"
    board = board_record(book)
    assert board["standings"] == [
        {"standing": "complete", "pausings": 3},
        {"standing": "open", "pausings": 2}]
    assert board["total"] == 5
    assert board["current_pausing"] == "pausing-bare-crossing"
    assert board["traces"] == [
        {"pausing_id": "pausing-approved-crossing", "trace": "current"},
        {"pausing_id": "pausing-reasked-crossing", "trace": "unheld"},
        {"pausing_id": "pausing-wired-crossing", "trace": "unheld"},
        {"pausing_id": "pausing-bare-crossing", "trace": "unheld"},
        {"pausing_id": "pausing-leaping-crossing", "trace": "unheld"}]
    assert board["breaks"] == ["pausing-leaping-crossing: checked > crossed"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 271
    assert citizen["next_slice"] == "M-272"
    assert citizen["m208_title"] == "The pause-lines wired"
    assert citizen["m208_part"] == 9
    assert citizen["m208_status"] == "done"

def test_pausing_record_round_trips():
    pausing = _pausing()
    assert validate_pausing(pausing) is pausing
    rebuilt = build_pausing(pausing.to_record())
    assert rebuilt == pausing
    assert rebuilt.item_id == "pausing-test"
    assert rebuilt.check == "crossed"
    record = pausing_record(pausing)
    assert record["type"] == "pausing_pausing"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert slice_record(ref)["type"] == "pausing_slice"
    assert slice_record(ref)["state"] == "active"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _pausing(checks=[])
    assert pausing_gaps(silent) == (
        "has passed through no step: the pausing has not started",)
    assert pausing_green(silent) is False
    walking = _pausing(checks=["proposed", "checked"])
    assert pausing_gaps(walking) == (
        "has not reached crossed: the pausing stands at checked",)
    assert walking.check == "checked"
    sideways = _pausing(checks=["checked", "paused", "crossed"])
    assert pausing_gaps(sideways) == (
        "opens at checked, not at proposed: the pausing opens "
        "with the proposal",)
    repaired = _pausing(checks=[
        "proposed", "checked", "paused", "reasked", "paused", "crossed"])
    assert pausing_gaps(repaired) == ()
    assert pausing_green(repaired) is True
    with pytest.raises(ValueError):
        _pausing(checks=[42])
    with pytest.raises(ValueError):
        _pausing(checks="inspect as a bare string")
    with pytest.raises(ValueError):
        _pausing(checks=["proposed", "polish"])
    with pytest.raises(ValueError):
        _pausing(claims=["weather"])
    with pytest.raises(ValueError):
        _pausing(claims="approval_record")
    none_pausing = _pausing(checks=None, claims=None)
    assert none_pausing.checks == ()
    assert none_pausing.claims == ()

def test_pausing_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "entries", "coverage", "current_pausing",
                "board", "order"):
        fields = _pausing().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_pausing(fields)
    fields = _pausing().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_pausing(fields)


def test_pausing_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _pausing().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_pausing(fields)


def test_pausing_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _pausing(title="")
    with pytest.raises(ValueError):
        _pausing(slice_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "proposed > checked > paused > crossed"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_pausings_own_fields():
    pausing = _pausing(claims=["approval_record"])
    assert plain_lines(pausing) == (
        "Pausing: A test pausing",
        "Slice: slice-test",
        "Check: crossed",
        "Claims: approval_record")
    segment = segment_of(pausing)
    assert segment.startswith("pausing-test: A test pausing")
    assert "check: 'crossed'" in segment
    assert "gaps: none" in segment
    assert plain_words(pausing).startswith(
        "A test pausing - from slice-test")

def test_red_pausings_stand_named_in_their_gaps():
    asking = _pausing(claims=["feeling", "approval_record", "summary"])
    assert pausing_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert pausing_green(asking) is False
    skipping = _pausing(checks=["proposed", "checked", "crossed"])
    assert pausing_gaps(skipping) == (
        "steps from checked to crossed, which the pause sequence "
        "does not allow",)
    book = _book(pausings=[
        _pausing(),
        _pausing(pausing_id="pausing-skipping", seq=2,
             checks=["proposed", "checked", "crossed"]),
    ])
    assert transition_breaks(book) == (
        "pausing-skipping: checked > crossed",)
    assert current_pausing(book).pausing_id == "pausing-skipping"
    assert [g.pausing_id for g in pausing_order(book)] == [
        "pausing-test", "pausing-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "pausing_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "pausing_note"
    assert record["pausing_id"] == "pausing-test"
    assert view_plain_words(view) == "View view-test: shows all pausings."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_pausings_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.check for e in index.entries] == ["crossed"]
    assert index.entries[0] == IndexEntry(
        check="crossed",
        pausing_id="pausing-test", title="A test pausing")
    assert index.gaps == ("pausing-hidden",)
    record = index_record(book)
    assert record["type"] == "pausing_index"
    assert record["gaps"] == ["pausing-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "pausing_book"

def test_check_target_reaches_its_pausing_and_an_unheld_target_reaches_nothing():
    book = load_pausing()
    assert pausing_for_check(book, "crossed").pausing_id == (
        "pausing-approved-crossing")
    assert pausing_for_check(book, "") is None
    assert pausing_for_check(book, None) is None
    assert pausing_for_check(book, "not held at all") is None
    text = format_check(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_pausing()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Pausing note note pausing-approved-crossing" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").pausing_id == "pausing-test"
    assert note_for_pausing(book, "pausing-test").note_id == "note-test"
    assert note_for_pausing(book, "pausing-test", "praise") is None
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
    row = build_row(None, _pausing(), book)
    assert row.standing == "complete"
    assert validate_row(row, _pausing(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_pausings():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "pausing_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "reported"
    empty_book = _book(pausings=[_pausing(checks=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(PausingVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_pausing()
    assert [g.pausing_id for g in shown_pausings(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.pausing_id for g in shown_pausings(book, "view-crossed")] == [
        "pausing-approved-crossing", "pausing-reasked-crossing", "pausing-wired-crossing"]
    assert [g.pausing_id for g in pausings_for_slice(
        book, "slice-m208-pauselines")] == [
            "pausing-wired-crossing", "pausing-bare-crossing",
            "pausing-leaping-crossing"]
    assert pausings_for_slice(book, "slice-nope") == ()
    assert current_pausing(_mixed_book()).pausing_id == "pausing-hidden"
    assert current_pausing(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "pausing-test") == (
        "proposed > checked > paused > crossed")
    assert trace_current(stale, "pausing-test") is False
    assert board_record(stale)["traces"] == [
        {"pausing_id": "pausing-test", "trace": "stale"}]

def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(pausings=[_pausing(), _pausing(seq=2)])
    with pytest.raises(ValueError):
        _book(pausings=[_pausing(), _pausing(pausing_id="pausing-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(pausings=[_pausing(slice_id="slice-nope")])
    with pytest.raises(ValueError):
        _book(slices=[_ref(), _ref(
            slice_id="slice-cold", seq=2, state="queued")],
            pausings=[_pausing(slice_id="slice-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(slice_id="slice-nope")])
    fields = {
        "schema": PAUSING_SCHEMA, "slice": "M-208",
        "pause_lines": {"title": "A judged book"},
        "slices": [_ref().to_record()],
        "pausings": [_pausing().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "reported"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_pausing"] = "pausing-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_pausing")
    fields["trace"] = "pausing-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / PAUSING_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "pause_lines.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_pausing_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.pausing_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = PausingRegistry()
    assert registry.title() is None
    registry.register_slice_ref(_ref())
    registry.register_pausing(_pausing())
    registry.register_view(_view())
    assert [g.pausing_id for g in registry.list_pausings()] == ["pausing-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_pausing("pausing-test").title == "A test pausing"
    assert registry.get_slice("slice-test").state == "active"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("pausing-test").pausing_id == "pausing-test"
    with pytest.raises(ValueError):
        registry.register_pausing(_pausing(seq=9))
    with pytest.raises(ValueError):
        registry.register_pausing(_pausing(pausing_id="pausing-two"))
    with pytest.raises(KeyError):
        registry.get_pausing("pausing-nope")
    assert registry.book().title == "An unheld pausing book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = PausingRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test pausing book"
    assert registry.title() == "A test pausing book"
    assert len(registry.list_pausings()) == 2
    other = PausingRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    pausing = _pausing()
    assert "A test pausing" in plain_words(pausing)
    assert panel_plain_words(_mixed_book()).startswith(
        "The pausing book holds 2 pausings")
    assert verdict_plain_words(_mixed_book()) == (
        "The pausings stand held: 1 of 2 shown pausings stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green pausings; red, "
        "named in its gaps: pausing-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_pausing(pausing)
    assert "Pausing: A test pausing" in text
    assert "stands complete" in text
    text = format_pausing(_pausing(checks=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Pause Gate (M-208) - A test pausing book" in book_text
    assert "pausing-hidden" in format_book(_mixed_book(), "slice-test")
    assert "Pausing panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "crossed - A test pausing (pausing-test)" in index_text
    assert "pausing-hidden" in index_text
    screen = format_pausing_screen()
    assert "The Pause Gate (M-208)" in screen
    assert "pausing-bare-crossing" in screen

def test_parse_args_board_and_loader_targets():
    assert parse_pausing_args("") == ("show", None)
    assert parse_pausing_args(None) == ("show", None)
    assert parse_pausing_args("show") == ("show", None)
    assert parse_pausing_args("pausing pausing-test") == (
        "pausing", "pausing-test")
    assert parse_pausing_args("check crossed") == (
        "check", "crossed")
    assert parse_pausing_args("slice slice-test") == (
        "slice", "slice-test")
    assert parse_pausing_args("view view-test") == ("view", "view-test")
    assert parse_pausing_args("note note-test") == ("note", "note-test")
    assert parse_pausing_args("index") == ("index", None)
    assert parse_pausing_args("panel") == ("panel", None)
    assert parse_pausing_args("verdict") == ("verdict", None)
    for bad in ("dance", "pausing", "check", "slice", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_pausing_args(bad)
    board = board_record()
    assert board["type"] == "pausing_board"
    assert board["total"] == 5
    assert board["current_pausing"] == "pausing-bare-crossing"
    book = load_pausing({
        "schema": PAUSING_SCHEMA, "slice": "M-208",
        "pause_lines": {"title": "A judged book"},
        "slices": [_ref().to_record()],
        "pausings": [_pausing().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, PausingBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_pausing({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_pausing({"slice": "M-999"})
    built = build_pausing(
        pausing_id="pausing-kw", seq=3, slice_id="slice-test",
        title="Kw Pausing", checks=["proposed", "checked", "paused", "crossed"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="pausing-test")
    assert built.pausing_id == "pausing-kw"
    assert pausing_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-208 agent layer: the agent holds a pausing
# book for the session, pausings and views are
# published as session news through the
# checkpoint target (journal first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held pausings, the board is derived from
# the held pausings' completeness, the roadmap standing
# is read from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no slice. This layer pausings
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_PAUSING_EVENT_TYPES = (
    "pausing_pausing", "pausing_slice", "pausing_view",
    "pausing_panel", "pausing_verdict")


def _pausing_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_pausing_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / PAUSING_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "pause_lines.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestPausingAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.pausing_status()
        assert status["pausings"] == []
        assert status["slices"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["pausing_book"]["title"] == EXAMPLE_TITLE
        assert len(status["pausing_book"]["slices"]) == 3
        assert len(status["pausing_book"]["pausings"]) == 5
        assert len(status["pausing_book"]["views"]) == 2
        assert len(status["pausing_book"]["notes"]) == 2
        assert len(status["pausing_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m207-boundary"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["check"] for e in status["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert status["index"]["gaps"] == [
            "pausing-bare-crossing", "pausing-leaping-crossing"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["board"]["total"] == 5
        assert status["board"]["current_pausing"] == "pausing-bare-crossing"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 271
        assert status["roadmap"]["next_slice"] == "M-272"
        assert status["roadmap"]["m208_title"] == "The pause-lines wired"
        assert "held as data alone" in status["rule"]
        assert "pausing-bare-crossing" in status["plain_words"]
        assert "The Pause Gate (M-208)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._pausing_registry()
        assert agent._pausing_registry() is first
        assert agent._pausing_store is first
        for name in ("pausing_book", "pausing_status", "pausing_panel",
                     "pausing_verdict", "pausing_index", "report_pausing"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_pausing_registry", "pausing_book", "pausing_status",
            "get_pausing_pausing", "get_pausing_view", "get_pausing_note",
            "pausing_pausings_for_slice", "pausing_pausings_green",
            "pausing_panel", "pausing_verdict", "pausing_index",
            "register_pausing_pausing", "register_pausing_view",
            "view_pausing", "register_pausing_book",
            "record_pausing_book", "report_pausing",
            "_publish_pausing_record", "_pausing_screen",
            "_pausing_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.pausing_status()
        assert agent.get_pausing_pausing(
            "pausing-approved-crossing").title == "The approved crossing pausing"
        assert agent.get_pausing_view(
            "view-pausings").view_filter == "all"
        assert agent.get_pausing_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.pausing_id for d in agent.pausing_pausings_for_slice(
            "slice-m208-pauselines")] == [
            "pausing-wired-crossing", "pausing-bare-crossing",
            "pausing-leaping-crossing"]
        assert [d.pausing_id for d in agent.pausing_pausings_green()] == [
            "pausing-approved-crossing", "pausing-reasked-crossing", "pausing-wired-crossing"]
        agent.pausing_panel()
        agent.pausing_verdict()
        agent.pausing_index()
        agent.report_pausing()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _PAUSING_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_pausing_pausing("pausing-nope")
        with pytest.raises(KeyError):
            agent.get_pausing_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_pausing_note("note-nope")
        with pytest.raises(ValueError):
            agent.pausing_pausings_for_slice("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_pausing_pausing(_pausing())
        status = agent.pausing_status()
        assert [d["pausing_id"] for d in status["pausings"]] == ["pausing-test"]
        assert status["book"]["title"] == "An unheld pausing book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["check"] for e in status["index"]["entries"]] == [
            "crossed"]
        assert status["first_note"] is None
        assert "pausing-test" in status["screen"]
    def test_held_pausing_never_falls_back_to_the_example(
            self, agent):
        agent.register_pausing_pausing(_pausing())
        with pytest.raises(KeyError):
            agent.get_pausing_pausing("pausing-approved-crossing")
        with pytest.raises(KeyError):
            agent.get_pausing_view("view-pausings")
        with pytest.raises(KeyError):
            agent.get_pausing_note("note-note-first")
        pausing = agent.get_pausing_pausing("pausing-test")
        assert pausing.title == "A test pausing"
        assert agent.pausing_book().title == (
            "An unheld pausing book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_pausing_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.pausing_id == "pausing-approved-crossing"
        status = agent.pausing_status()
        assert status["index"]["gaps"] == [
            "pausing-bare-crossing", "pausing-leaping-crossing"]
        assert status["first_note"]["pausing_id"] == (
            "pausing-approved-crossing")
        assert status["first_note"]["stance"] == "note"

class TestPausingAgentHolding:
    def test_register_pausing_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_pausing_pausing(_pausing())
        assert result["pausing"]["pausing_id"] == "pausing-test"
        assert result["record_news"]["type"] == "pausing_pausing"
        assert "pausing-test" in result["screen"]
        events = _pausing_events(store, session_id, "pausing_pausing")
        assert len(events) == 1
        agent.close()

    def test_duplicate_pausing_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_pausing_pausing(_pausing())
        with pytest.raises(ValueError):
            agent.register_pausing_pausing(_pausing(seq=9))
        with pytest.raises(ValueError):
            agent.register_pausing_pausing(_pausing(pausing_id="pausing-two"))
        events = _pausing_events(store, session_id, "pausing_pausing")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_pausing_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_pausing_events(
            store, session_id, "pausing_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_pausing_pausing(_pausing())
        result = agent.view_pausing("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "pausing_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "reported"
        assert len(_pausing_events(
            store, session_id, "pausing_view")) == 1
        assert len(_pausing_events(
            store, session_id, "pausing_panel")) == 1
        assert len(_pausing_events(
            store, session_id, "pausing_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_pausing_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "pausing_slice", "pausing_pausing", "pausing_view"]
        assert len(_pausing_events(
            store, session_id, "pausing_pausing")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_pausing_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "pausing_panel"
        assert result["index_record"]["gaps"] == [
            "pausing-bare-crossing", "pausing-leaping-crossing"]
        with pytest.raises(ValueError):
            agent.record_pausing_book()
        assert len(_pausing_events(
            store, session_id, "pausing_slice")) == 3
        assert len(_pausing_events(
            store, session_id, "pausing_pausing")) == 5
        assert len(_pausing_events(
            store, session_id, "pausing_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_pausing_book_file(tmp_path)
        book = load_pausing_file(path)
        result = agent.record_pausing_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_pausing()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "held"
        assert report["index"]["gaps"] == [
            "pausing-bare-crossing", "pausing-leaping-crossing"]
        assert "pausing-approved-crossing" in report["book_text"]
        assert "crossed - The approved crossing pausing (pausing-approved-crossing)" in report["index_text"]
        agent.register_pausing_pausing(_pausing())
        report = agent.report_pausing()
        assert report["book"]["title"] == "An unheld pausing book"
        assert report["panel"] is None
        assert report["verdict"] is None

class TestPausingTerminalHeading:
    def test_show_pausing_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/pauselines")
        assert "The Pause Gate (M-208)" in text
        _, _, text = _slash(agent, "/pauselines pausing pausing-approved-crossing")
        assert "Pausing: The approved crossing pausing" in text
        _, _, text = _slash(
            agent, "/pauselines check crossed")
        assert "Pausing: The approved crossing pausing" in text
        _, _, text = _slash(agent, "/pauselines check triple resume")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/pauselines slice slice-m208-pauselines")
        assert "pausing-bare-crossing" in text
        assert "pausing-approved-crossing" not in text
        _, _, text = _slash(agent, "/pauselines view view-pausings")
        assert "filter all" in text
        _, _, text = _slash(agent, "/pauselines note note-note-first")
        assert "Pausing note note pausing-approved-crossing" in text
        _, _, text = _slash(agent, "/pauselines index")
        assert "Pausing index" in text
        assert "pausing-bare-crossing" in text
        _, _, text = _slash(agent, "/pauselines panel")
        assert "Pausing panel under view view-pausings" in text
        _, _, text = _slash(agent, "/pauselines verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/pauselines [show|pausing <pausing-id>"
                "|check <check>|slice <slice-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/pauselines dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/pauselines pausing pausing-nope")
        assert "no pausing named" in text
@pytest.fixture()
def pausing_handler(agent, monkeypatch):
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


def _pausing_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestPausingCommand:
    def test_show_is_default(self, pausing_handler, agent):
        pausing_handler._handle_pausing("")
        assert "The Pause Gate (M-208)" in (
            _pausing_published_text(pausing_handler))

    def test_pausing_check_slice_view_note_index_panel_verdict(
            self, pausing_handler, agent):
        pausing_handler._handle_pausing("pausing pausing-approved-crossing")
        assert "Pausing: The approved crossing pausing" in _pausing_published_text(
            pausing_handler)
        pausing_handler._handle_pausing(
            "check crossed")
        assert "Pausing: The approved crossing pausing" in _pausing_published_text(
            pausing_handler)
        pausing_handler._handle_pausing("slice slice-m208-pauselines")
        assert "pausing-bare-crossing" in _pausing_published_text(
            pausing_handler)
        pausing_handler._handle_pausing("view view-pausings")
        assert "filter all" in _pausing_published_text(pausing_handler)
        pausing_handler._handle_pausing("note note-note-first")
        assert "Pausing note note pausing-approved-crossing" in (
            _pausing_published_text(pausing_handler))
        pausing_handler._handle_pausing("index")
        assert "Pausing index" in _pausing_published_text(pausing_handler)
        pausing_handler._handle_pausing("panel")
        assert "Pausing panel under view" in _pausing_published_text(
            pausing_handler)
        pausing_handler._handle_pausing("verdict")
        assert "held" in _pausing_published_text(pausing_handler)
    def test_bad_grammar_is_published(
            self, pausing_handler, agent):
        pausing_handler._handle_pausing("dance party")
        assert USAGE in _pausing_published_text(pausing_handler)
        pausing_handler._handle_pausing("pausing pausing-nope")
        assert "no pausing named" in _pausing_published_text(
            pausing_handler)


class TestChatScreenRoutingPausing:
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
        screen.handle_command("/pauselines panel", _FakeLog())
        assert calls == [("/pauselines", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/pauselines[/green] - show the Pause gate (M-208)" in (
            text)
        assert ('"/pauselines": "Usage: /pauselines | '
                '/pauselines pausing <pausing-id>') in text

class TestPausingDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.pausing_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-pausings"
        verdict = agent.pausing_verdict()
        assert verdict.verdict == "held"
        found = agent.pausing_verdict("view-crossed")
        assert found.verdict == "reported"
        assert found.green_shown == 3
        agent.register_pausing_pausing(_pausing())
        with pytest.raises(ValueError):
            agent.pausing_panel()
        with pytest.raises(ValueError):
            agent.pausing_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_pausing_pausing(_pausing(checks=[]))
        result = agent.view_pausing("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.pausing_index()
        assert [e["check"] for e in result["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert result["index"]["gaps"] == [
            "pausing-bare-crossing", "pausing-leaping-crossing"]
        assert "crossed - The approved crossing pausing (pausing-approved-crossing)" in (
            result["index_text"])
        pausing = agent.get_pausing_pausing("pausing-leaping-crossing")
        assert pausing_gaps(pausing, agent.pausing_book()) == (
            "steps from checked to crossed, which the pause sequence "
            "does not allow",)
        assert pausing_green(pausing, agent.pausing_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _PAUSING_EVENT_TYPES] == []
        agent.close()
