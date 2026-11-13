"""M-212 Question Law - pure-layer tests.

TIER: integration

The pure layer is the scribe, held as data: one
record per bug, held whole - the slice it
answers for, named by slice id, its title, the
steps it walked in walk order and the evidence
it carries, held by kind. The question walk is
explicit - named, triaged, fixed, verified,
closed, with their legal steps held as data -
and a bug's standing is derived at call
time: a bug that opens anywhere but discovered, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet reached closed stands open,
named in its gaps. A bug stands only for
an active slice: a bug naming no held
slice, or one that is not active, refuses by
name. The bug's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, board, trace, order and current
bug are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, verified or
closed live. The shipped example book is held
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

from mythic_agent.core.bug_rule import (
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
    BUG_RESOURCE,
    BUG_RULE,
    BUG_SCHEMA,
    BUG_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    BugRecord,
    IndexEntry,
    SliceRef,
    NoteRecord,
    BugBook,
    BugIndex,
    BugPanel,
    BugRegistry,
    BugVerdict,
    BugView,
    trace_for_bug,
    board_record,
    book_record,
    build_trace,
    build_book,
    build_bug,
    build_slice_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_bug,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    bug_for_check,
    bug_gaps,
    bug_order,
    bug_record,
    bug_green,
    bugs_for_slice,
    first_note,
    format_book,
    format_bug,
    format_index,
    format_note,
    format_check,
    format_panel,
    format_bug_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    slice_record,
    load_bug,
    legal_step,
    load_bug_file,
    next_check,
    normalize_check,
    normalize_claim_kind,
    normalize_slice_state,
    normalize_stance,
    normalize_view_filter,
    note_for_bug,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_bug_args,
    green_bugs,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_bugs,
    validate_book,
    validate_bug,
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
EXAMPLE_TITLE = "The never-leave-a-bug rule at the M-211 slice boundary"
EXAMPLE_CHECKS = ["closed", "closed", "closed"]
EXAMPLE_RUN_IDS = (
    "bug-held-fix", "bug-rechecked-fix",
    "bug-own-fix", "bug-bare-fix",
    "bug-leaping-fix")
EXAMPLE_TRACE = "discovered > triaged > fixed > verified > closed"


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
        "origin_session": "bug-test",
    }
    fields.update(overrides)
    return build_slice_ref(fields)


def _bug(**overrides):
    fields = {
        "bug_id": "bug-test",
        "seq": 1,
        "slice_id": "slice-test",
        "title": "A test bug",
        "checks": ["discovered", "triaged", "fixed", "verified", "closed"],
        "claims": [],
        "detail": "A test bug held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "bug-test",
    }
    fields.update(overrides)
    return build_bug(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "bug-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "bug_id": "bug-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "bug-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "bug_id": "bug-test",
        "trace": "discovered > triaged > fixed > verified > closed",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "bug-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(slices=None, bugs=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": BUG_SCHEMA,
        "slice": "M-212",
        "bug_rule": {"title": "A test bug book"},
        "slices": [item.to_record() for item in (
            slices if slices is not None else [_ref()])],
        "bugs": [item.to_record() for item in (
            bugs if bugs is not None else [_bug()])],
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
    return _book(bugs=[
        _bug(),
        _bug(bug_id="bug-hidden", seq=2,
               title="A hidden bug", checks=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_bug()
    assert book.title == EXAMPLE_TITLE
    assert book.bug_ids() == EXAMPLE_RUN_IDS
    assert book.slice_ids() == (
        "slice-m211-upkeep", "slice-m212-bugrule",
        "slice-m213-retro")
    assert [v.view_id for v in book.views] == [
        "view-bugs", "view-closed"]
    assert [m.bug_id for m in book.notes] == [
        "bug-held-fix", "bug-bare-fix"]
    assert [a.bug_id for a in book.traces] == ["bug-held-fix"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m211-boundary"
    assert panel.as_of == "2026-11-10"
    assert [row.item_id for row in panel.rows] == list(book.bug_ids())
    derived = derive_panel(book, "view-bugs")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-bugs").verdict == "held"
    assert derive_verdict(book, "view-bugs").green_shown == 3
    assert derive_verdict(book, "view-closed").verdict == "closed"
    assert derive_verdict(book, "view-closed").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / BUG_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == BUG_SCHEMA
    assert raw["slice"] == "M-212"
    assert "verdict" not in raw
    assert "bug_index" not in raw
    assert "board" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-212")]
    assert slice_.title == "The never-leave-a-bug rule"
    assert slice_.part == 9
    assert "a bug discovered mid-slice is fixed in scope" in slice_.summary
    assert "commissioned as a new slice on the spot" in slice_.summary
    assert "note it and move on" in slice_.summary
    assert BUG_SLICE == "M-212"

def test_charter_rows_do_not_name_m212():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-212" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert COMPLETE_WORDS == ("complete", "open")
    assert CHECK_FIELDS == ("checks", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "complete", "open")
    assert VERDICT_WORDS == ("closed", "held", "blocked")
    assert SLICE_STATES == ("active", "queued")
    assert CHECKS == ("discovered", "triaged", "fixed", "verified", "closed")
    assert HELD_EVIDENCE == ("slice_ref", "fix_ref", "test_record", "commission_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["verified"] == ("discovered", "closed")
    assert TRANSITIONS["closed"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_CHECK == "closed"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_slice_state("ACTIVE") == "active"
    assert normalize_check("FIXED") == "fixed"
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
    assert legal_step("fixed", "verified") is True
    assert legal_step("triaged", "closed") is False
    assert legal_step("closed", "discovered") is False
    assert next_check("discovered") == "triaged"
    assert next_check("fixed") == "verified"
    assert next_check("verified", failed=True) == "discovered"
    assert next_check("verified") == "closed"
    assert next_check("closed") is None
    assert "held as data alone" in BUG_RULE
    assert "bug sequence" in BUG_RULE
    assert "M-212" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /bugrule")

def test_shipped_book_judged_honestly_as_data():
    book = load_bug()
    opening = book.bug_for("bug-held-fix")
    assert bug_green(opening, book) is True
    assert bug_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Bug: The held fix",
        "Slice: slice-m211-upkeep",
        "Check: closed",
        "Claims: slice_ref")
    asking = book.bug_for("bug-bare-fix")
    assert bug_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert bug_green(asking, book) is False
    skipping = book.bug_for("bug-leaping-fix")
    assert bug_gaps(skipping, book) == (
        "steps from triaged to closed, which the bug sequence "
        "does not allow",)
    assert [g.bug_id for g in green_bugs(book)] == [
        "bug-held-fix", "bug-rechecked-fix", "bug-own-fix"]
    index = derive_index(book)
    assert [e.check for e in index.entries] == EXAMPLE_CHECKS
    assert index.gaps == ("bug-bare-fix", "bug-leaping-fix")
    assert bug_for_check(book, EXAMPLE_CHECK).bug_id == (
        "bug-held-fix")
    assert bug_for_check(book, "triple resume") is None
    assert transition_breaks(book) == (
        "bug-leaping-fix: triaged > closed",)
    assert [g.bug_id for g in bug_order(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "bug-held-fix") == EXAMPLE_TRACE
    assert trace_current(book, "bug-held-fix") is True
    assert trace_current(book, "bug-rechecked-fix") is False
    assert trace_for_bug(
        book, "bug-held-fix").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_bug(
        book, "bug-held-fix", "note").note_id == (
            "note-note-first")
    assert note_for_bug(book, "bug-nope") is None
    assert current_bug(book).bug_id == "bug-bare-fix"
    board = board_record(book)
    assert board["standings"] == [
        {"standing": "complete", "bugs": 3},
        {"standing": "open", "bugs": 2}]
    assert board["total"] == 5
    assert board["current_bug"] == "bug-bare-fix"
    assert board["traces"] == [
        {"bug_id": "bug-held-fix", "trace": "current"},
        {"bug_id": "bug-rechecked-fix", "trace": "unheld"},
        {"bug_id": "bug-own-fix", "trace": "unheld"},
        {"bug_id": "bug-bare-fix", "trace": "unheld"},
        {"bug_id": "bug-leaping-fix", "trace": "unheld"}]
    assert board["breaks"] == ["bug-leaping-fix: triaged > closed"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 267
    assert citizen["next_slice"] == "M-268"
    assert citizen["m212_title"] == "The never-leave-a-bug rule"
    assert citizen["m212_part"] == 9
    assert citizen["m212_status"] == "done"

def test_bug_record_round_trips():
    bug = _bug()
    assert validate_bug(bug) is bug
    rebuilt = build_bug(bug.to_record())
    assert rebuilt == bug
    assert rebuilt.item_id == "bug-test"
    assert rebuilt.check == "closed"
    record = bug_record(bug)
    assert record["type"] == "bug_bug"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert slice_record(ref)["type"] == "bug_slice"
    assert slice_record(ref)["state"] == "active"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _bug(checks=[])
    assert bug_gaps(silent) == (
        "has passed through no step: the bug has not started",)
    assert bug_green(silent) is False
    walking = _bug(checks=["discovered", "triaged"])
    assert bug_gaps(walking) == (
        "has not reached closed: the bug stands at triaged",)
    assert walking.check == "triaged"
    sideways = _bug(checks=["triaged", "fixed", "verified", "closed"])
    assert bug_gaps(sideways) == (
        "opens at triaged, not at discovered: the bug opens "
        "with the question",)
    repaired = _bug(checks=["discovered", "triaged", "fixed", "verified", "discovered", "triaged", "fixed", "verified", "closed"])
    assert bug_gaps(repaired) == ()
    assert bug_green(repaired) is True
    with pytest.raises(ValueError):
        _bug(checks=[42])
    with pytest.raises(ValueError):
        _bug(checks="inspect as a bare string")
    with pytest.raises(ValueError):
        _bug(checks=["discovered", "polish"])
    with pytest.raises(ValueError):
        _bug(claims=["weather"])
    with pytest.raises(ValueError):
        _bug(claims="slice_ref")
    none_bug = _bug(checks=None, claims=None)
    assert none_bug.checks == ()
    assert none_bug.claims == ()

def test_bug_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "entries", "coverage", "current_bug",
                "board", "order"):
        fields = _bug().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_bug(fields)
    fields = _bug().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_bug(fields)


def test_bug_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _bug().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_bug(fields)


def test_bug_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _bug(title="")
    with pytest.raises(ValueError):
        _bug(slice_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "discovered > triaged > fixed > verified > closed"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_bugs_own_fields():
    bug = _bug(claims=["slice_ref"])
    assert plain_lines(bug) == (
        "Bug: A test bug",
        "Slice: slice-test",
        "Check: closed",
        "Claims: slice_ref")
    segment = segment_of(bug)
    assert segment.startswith("bug-test: A test bug")
    assert "check: 'closed'" in segment
    assert "gaps: none" in segment
    assert plain_words(bug).startswith(
        "A test bug - from slice-test")

def test_red_bugs_stand_named_in_their_gaps():
    asking = _bug(claims=["feeling", "slice_ref", "summary"])
    assert bug_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert bug_green(asking) is False
    skipping = _bug(checks=["discovered", "triaged", "closed"])
    assert bug_gaps(skipping) == (
        "steps from triaged to closed, which the bug sequence "
        "does not allow",)
    book = _book(bugs=[
        _bug(),
        _bug(bug_id="bug-skipping", seq=2,
             checks=["discovered", "triaged", "closed"]),
    ])
    assert transition_breaks(book) == (
        "bug-skipping: triaged > closed",)
    assert current_bug(book).bug_id == "bug-skipping"
    assert [g.bug_id for g in bug_order(book)] == [
        "bug-test", "bug-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "bug_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "bug_note"
    assert record["bug_id"] == "bug-test"
    assert view_plain_words(view) == "View view-test: shows all bugs."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_bugs_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.check for e in index.entries] == ["closed"]
    assert index.entries[0] == IndexEntry(
        check="closed",
        bug_id="bug-test", title="A test bug")
    assert index.gaps == ("bug-hidden",)
    record = index_record(book)
    assert record["type"] == "bug_index"
    assert record["gaps"] == ["bug-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "bug_book"

def test_check_target_reaches_its_bug_and_an_unheld_target_reaches_nothing():
    book = load_bug()
    assert bug_for_check(book, "closed").bug_id == (
        "bug-held-fix")
    assert bug_for_check(book, "") is None
    assert bug_for_check(book, None) is None
    assert bug_for_check(book, "not held at all") is None
    text = format_check(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_bug()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Bug note note bug-held-fix" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").bug_id == "bug-test"
    assert note_for_bug(book, "bug-test").note_id == "note-test"
    assert note_for_bug(book, "bug-test", "praise") is None
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
    row = build_row(None, _bug(), book)
    assert row.standing == "complete"
    assert validate_row(row, _bug(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_bugs():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "bug_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "closed"
    empty_book = _book(bugs=[_bug(checks=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(BugVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_bug()
    assert [g.bug_id for g in shown_bugs(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.bug_id for g in shown_bugs(book, "view-closed")] == [
        "bug-held-fix", "bug-rechecked-fix", "bug-own-fix"]
    assert [g.bug_id for g in bugs_for_slice(
        book, "slice-m212-bugrule")] == [
            "bug-own-fix", "bug-bare-fix",
            "bug-leaping-fix"]
    assert bugs_for_slice(book, "slice-nope") == ()
    assert current_bug(_mixed_book()).bug_id == "bug-hidden"
    assert current_bug(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "bug-test") == (
        "discovered > triaged > fixed > verified > closed")
    assert trace_current(stale, "bug-test") is False
    assert board_record(stale)["traces"] == [
        {"bug_id": "bug-test", "trace": "stale"}]

def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(bugs=[_bug(), _bug(seq=2)])
    with pytest.raises(ValueError):
        _book(bugs=[_bug(), _bug(bug_id="bug-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(bugs=[_bug(slice_id="slice-nope")])
    with pytest.raises(ValueError):
        _book(slices=[_ref(), _ref(
            slice_id="slice-cold", seq=2, state="queued")],
            bugs=[_bug(slice_id="slice-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(slice_id="slice-nope")])
    fields = {
        "schema": BUG_SCHEMA, "slice": "M-212",
        "bug_rule": {"title": "A fixed book"},
        "slices": [_ref().to_record()],
        "bugs": [_bug().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "closed"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_bug"] = "bug-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_bug")
    fields["trace"] = "bug-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / BUG_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "bug_rule.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_bug_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.bug_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = BugRegistry()
    assert registry.title() is None
    registry.register_slice_ref(_ref())
    registry.register_bug(_bug())
    registry.register_view(_view())
    assert [g.bug_id for g in registry.list_bugs()] == ["bug-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_bug("bug-test").title == "A test bug"
    assert registry.get_slice("slice-test").state == "active"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("bug-test").bug_id == "bug-test"
    with pytest.raises(ValueError):
        registry.register_bug(_bug(seq=9))
    with pytest.raises(ValueError):
        registry.register_bug(_bug(bug_id="bug-two"))
    with pytest.raises(KeyError):
        registry.get_bug("bug-nope")
    assert registry.book().title == "An unheld bug book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = BugRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test bug book"
    assert registry.title() == "A test bug book"
    assert len(registry.list_bugs()) == 2
    other = BugRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    bug = _bug()
    assert "A test bug" in plain_words(bug)
    assert panel_plain_words(_mixed_book()).startswith(
        "The bug book holds 2 bugs")
    assert verdict_plain_words(_mixed_book()) == (
        "The bugs stand held: 1 of 2 shown bugs stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green bugs; red, "
        "named in its gaps: bug-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_bug(bug)
    assert "Bug: A test bug" in text
    assert "stands complete" in text
    text = format_bug(_bug(checks=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Bug Gate (M-212) - A test bug book" in book_text
    assert "bug-hidden" in format_book(_mixed_book(), "slice-test")
    assert "Bug panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "closed - A test bug (bug-test)" in index_text
    assert "bug-hidden" in index_text
    screen = format_bug_screen()
    assert "The Bug Gate (M-212)" in screen
    assert "bug-bare-fix" in screen

def test_parse_args_board_and_loader_targets():
    assert parse_bug_args("") == ("show", None)
    assert parse_bug_args(None) == ("show", None)
    assert parse_bug_args("show") == ("show", None)
    assert parse_bug_args("bug bug-test") == (
        "bug", "bug-test")
    assert parse_bug_args("check closed") == (
        "check", "closed")
    assert parse_bug_args("slice slice-test") == (
        "slice", "slice-test")
    assert parse_bug_args("view view-test") == ("view", "view-test")
    assert parse_bug_args("note note-test") == ("note", "note-test")
    assert parse_bug_args("index") == ("index", None)
    assert parse_bug_args("panel") == ("panel", None)
    assert parse_bug_args("verdict") == ("verdict", None)
    for bad in ("dance", "bug", "check", "slice", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_bug_args(bad)
    board = board_record()
    assert board["type"] == "bug_board"
    assert board["total"] == 5
    assert board["current_bug"] == "bug-bare-fix"
    book = load_bug({
        "schema": BUG_SCHEMA, "slice": "M-212",
        "bug_rule": {"title": "A fixed book"},
        "slices": [_ref().to_record()],
        "bugs": [_bug().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, BugBook)
    assert book.title == "A fixed book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_bug({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_bug({"slice": "M-999"})
    built = build_bug(
        bug_id="bug-kw", seq=3, slice_id="slice-test",
        title="Kw Bug", checks=["discovered", "triaged", "fixed", "verified", "closed"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="bug-test")
    assert built.bug_id == "bug-kw"
    assert bug_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-212 agent layer: the agent holds a bug
# book for the session, bugs and views are
# published as session news through the
# checkpoint target (journal first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held bugs, the board is derived from
# the held bugs' completeness, the roadmap standing
# is read from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no slice. This layer bugs
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_BUG_EVENT_TYPES = (
    "bug_bug", "bug_slice", "bug_view",
    "bug_panel", "bug_verdict")


def _bug_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_bug_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / BUG_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "bug_rule.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestBugAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.bug_status()
        assert status["bugs"] == []
        assert status["slices"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["bug_book"]["title"] == EXAMPLE_TITLE
        assert len(status["bug_book"]["slices"]) == 3
        assert len(status["bug_book"]["bugs"]) == 5
        assert len(status["bug_book"]["views"]) == 2
        assert len(status["bug_book"]["notes"]) == 2
        assert len(status["bug_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m211-boundary"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["check"] for e in status["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert status["index"]["gaps"] == [
            "bug-bare-fix", "bug-leaping-fix"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["board"]["total"] == 5
        assert status["board"]["current_bug"] == "bug-bare-fix"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 267
        assert status["roadmap"]["next_slice"] == "M-268"
        assert status["roadmap"]["m212_title"] == "The never-leave-a-bug rule"
        assert "held as data alone" in status["rule"]
        assert "bug-bare-fix" in status["plain_words"]
        assert "The Bug Gate (M-212)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._bug_registry()
        assert agent._bug_registry() is first
        assert agent._bug_store is first
        for name in ("bug_book", "bug_status", "bug_panel",
                     "bug_verdict", "bug_index", "report_bug"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_bug_registry", "bug_book", "bug_status",
            "get_bug_bug", "get_bug_view", "get_bug_note",
            "bug_bugs_for_slice", "bug_bugs_green",
            "bug_panel", "bug_verdict", "bug_index",
            "register_bug_bug", "register_bug_view",
            "view_bug", "register_bug_book",
            "record_bug_book", "report_bug",
            "_publish_bug_record", "_bug_screen",
            "_bug_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.bug_status()
        assert agent.get_bug_bug(
            "bug-held-fix").title == "The held fix"
        assert agent.get_bug_view(
            "view-bugs").view_filter == "all"
        assert agent.get_bug_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.bug_id for d in agent.bug_bugs_for_slice(
            "slice-m212-bugrule")] == [
            "bug-own-fix", "bug-bare-fix",
            "bug-leaping-fix"]
        assert [d.bug_id for d in agent.bug_bugs_green()] == [
            "bug-held-fix", "bug-rechecked-fix", "bug-own-fix"]
        agent.bug_panel()
        agent.bug_verdict()
        agent.bug_index()
        agent.report_bug()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _BUG_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_bug_bug("bug-nope")
        with pytest.raises(KeyError):
            agent.get_bug_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_bug_note("note-nope")
        with pytest.raises(ValueError):
            agent.bug_bugs_for_slice("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_bug_bug(_bug())
        status = agent.bug_status()
        assert [d["bug_id"] for d in status["bugs"]] == ["bug-test"]
        assert status["book"]["title"] == "An unheld bug book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["check"] for e in status["index"]["entries"]] == [
            "closed"]
        assert status["first_note"] is None
        assert "bug-test" in status["screen"]
    def test_held_bug_never_falls_back_to_the_example(
            self, agent):
        agent.register_bug_bug(_bug())
        with pytest.raises(KeyError):
            agent.get_bug_bug("bug-held-fix")
        with pytest.raises(KeyError):
            agent.get_bug_view("view-bugs")
        with pytest.raises(KeyError):
            agent.get_bug_note("note-note-first")
        bug = agent.get_bug_bug("bug-test")
        assert bug.title == "A test bug"
        assert agent.bug_book().title == (
            "An unheld bug book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_bug_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.bug_id == "bug-held-fix"
        status = agent.bug_status()
        assert status["index"]["gaps"] == [
            "bug-bare-fix", "bug-leaping-fix"]
        assert status["first_note"]["bug_id"] == (
            "bug-held-fix")
        assert status["first_note"]["stance"] == "note"

class TestBugAgentHolding:
    def test_register_bug_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_bug_bug(_bug())
        assert result["bug"]["bug_id"] == "bug-test"
        assert result["record_news"]["type"] == "bug_bug"
        assert "bug-test" in result["screen"]
        events = _bug_events(store, session_id, "bug_bug")
        assert len(events) == 1
        agent.close()

    def test_duplicate_bug_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_bug_bug(_bug())
        with pytest.raises(ValueError):
            agent.register_bug_bug(_bug(seq=9))
        with pytest.raises(ValueError):
            agent.register_bug_bug(_bug(bug_id="bug-two"))
        events = _bug_events(store, session_id, "bug_bug")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_bug_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_bug_events(
            store, session_id, "bug_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_bug_bug(_bug())
        result = agent.view_bug("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "bug_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "closed"
        assert len(_bug_events(
            store, session_id, "bug_view")) == 1
        assert len(_bug_events(
            store, session_id, "bug_panel")) == 1
        assert len(_bug_events(
            store, session_id, "bug_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_bug_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "bug_slice", "bug_bug", "bug_view"]
        assert len(_bug_events(
            store, session_id, "bug_bug")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_bug_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "bug_panel"
        assert result["index_record"]["gaps"] == [
            "bug-bare-fix", "bug-leaping-fix"]
        with pytest.raises(ValueError):
            agent.record_bug_book()
        assert len(_bug_events(
            store, session_id, "bug_slice")) == 3
        assert len(_bug_events(
            store, session_id, "bug_bug")) == 5
        assert len(_bug_events(
            store, session_id, "bug_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_bug_book_file(tmp_path)
        book = load_bug_file(path)
        result = agent.record_bug_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_bug()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "held"
        assert report["index"]["gaps"] == [
            "bug-bare-fix", "bug-leaping-fix"]
        assert "bug-held-fix" in report["book_text"]
        assert "closed - The held fix (bug-held-fix)" in report["index_text"]
        agent.register_bug_bug(_bug())
        report = agent.report_bug()
        assert report["book"]["title"] == "An unheld bug book"
        assert report["panel"] is None
        assert report["verdict"] is None

class TestBugTerminalHeading:
    def test_show_bug_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/bugrule")
        assert "The Bug Gate (M-212)" in text
        _, _, text = _slash(agent, "/bugrule bug bug-held-fix")
        assert "Bug: The held fix" in text
        _, _, text = _slash(
            agent, "/bugrule check closed")
        assert "Bug: The held fix" in text
        _, _, text = _slash(agent, "/bugrule check triple resume")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/bugrule slice slice-m212-bugrule")
        assert "bug-bare-fix" in text
        assert "bug-held-fix" not in text
        _, _, text = _slash(agent, "/bugrule view view-bugs")
        assert "filter all" in text
        _, _, text = _slash(agent, "/bugrule note note-note-first")
        assert "Bug note note bug-held-fix" in text
        _, _, text = _slash(agent, "/bugrule index")
        assert "Bug index" in text
        assert "bug-bare-fix" in text
        _, _, text = _slash(agent, "/bugrule panel")
        assert "Bug panel under view view-bugs" in text
        _, _, text = _slash(agent, "/bugrule verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/bugrule [show|bug <bug-id>"
                "|check <check>|slice <slice-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/bugrule dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/bugrule bug bug-nope")
        assert "no bug named" in text
@pytest.fixture()
def bug_handler(agent, monkeypatch):
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


def _bug_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestBugCommand:
    def test_show_is_default(self, bug_handler, agent):
        bug_handler._handle_bug("")
        assert "The Bug Gate (M-212)" in (
            _bug_published_text(bug_handler))

    def test_bug_check_slice_view_note_index_panel_verdict(
            self, bug_handler, agent):
        bug_handler._handle_bug("bug bug-held-fix")
        assert "Bug: The held fix" in _bug_published_text(
            bug_handler)
        bug_handler._handle_bug(
            "check closed")
        assert "Bug: The held fix" in _bug_published_text(
            bug_handler)
        bug_handler._handle_bug("slice slice-m212-bugrule")
        assert "bug-bare-fix" in _bug_published_text(
            bug_handler)
        bug_handler._handle_bug("view view-bugs")
        assert "filter all" in _bug_published_text(bug_handler)
        bug_handler._handle_bug("note note-note-first")
        assert "Bug note note bug-held-fix" in (
            _bug_published_text(bug_handler))
        bug_handler._handle_bug("index")
        assert "Bug index" in _bug_published_text(bug_handler)
        bug_handler._handle_bug("panel")
        assert "Bug panel under view" in _bug_published_text(
            bug_handler)
        bug_handler._handle_bug("verdict")
        assert "held" in _bug_published_text(bug_handler)
    def test_bad_grammar_is_published(
            self, bug_handler, agent):
        bug_handler._handle_bug("dance party")
        assert USAGE in _bug_published_text(bug_handler)
        bug_handler._handle_bug("bug bug-nope")
        assert "no bug named" in _bug_published_text(
            bug_handler)


class TestChatScreenRoutingBug:
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
        screen.handle_command("/bugrule panel", _FakeLog())
        assert calls == [("/bugrule", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/bugrule[/green] - show the Bug gate (M-212)" in (
            text)
        assert ('"/bugrule": "Usage: /bugrule | '
                '/bugrule bug <bug-id>') in text

class TestBugDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.bug_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-bugs"
        verdict = agent.bug_verdict()
        assert verdict.verdict == "held"
        found = agent.bug_verdict("view-closed")
        assert found.verdict == "closed"
        assert found.green_shown == 3
        agent.register_bug_bug(_bug())
        with pytest.raises(ValueError):
            agent.bug_panel()
        with pytest.raises(ValueError):
            agent.bug_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_bug_bug(_bug(checks=[]))
        result = agent.view_bug("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.bug_index()
        assert [e["check"] for e in result["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert result["index"]["gaps"] == [
            "bug-bare-fix", "bug-leaping-fix"]
        assert "closed - The held fix (bug-held-fix)" in (
            result["index_text"])
        bug = agent.get_bug_bug("bug-leaping-fix")
        assert bug_gaps(bug, agent.bug_book()) == (
            "steps from triaged to closed, which the bug sequence "
            "does not allow",)
        assert bug_green(bug, agent.bug_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _BUG_EVENT_TYPES] == []
        agent.close()
