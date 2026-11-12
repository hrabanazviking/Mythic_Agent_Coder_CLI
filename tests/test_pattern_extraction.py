"""M-214 Patterns - pure-layer tests.

TIER: integration

The pure layer is the scribe, held as data: one
record per pattern, held whole - the slice it
answers for, named by slice id, its title, the
steps it walked in walk order and the evidence
it carries, held by kind. The question walk is
explicit - named, repeated, drafted, judged,
approved, with their legal steps held as data -
and a pattern's standing is derived at call
time: a pattern that opens anywhere but spotted, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet reached approved stands open,
named in its gaps. A pattern stands only for
an active slice: a pattern naming no held
slice, or one that is not active, refuses by
name. The pattern's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, board, trace, order and current
pattern are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, judged or
approved live. The shipped example book is held
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

from mythic_agent.core.pattern_extraction import (
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
    PATTERN_RESOURCE,
    PATTERN_RULE,
    PATTERN_SCHEMA,
    PATTERN_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    PatternRecord,
    IndexEntry,
    SliceRef,
    NoteRecord,
    PatternBook,
    PatternIndex,
    PatternPanel,
    PatternRegistry,
    PatternVerdict,
    PatternView,
    trace_for_pattern,
    board_record,
    book_record,
    build_trace,
    build_book,
    build_pattern,
    build_slice_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_pattern,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    pattern_for_check,
    pattern_gaps,
    pattern_order,
    pattern_record,
    pattern_green,
    patterns_for_slice,
    first_note,
    format_book,
    format_pattern,
    format_index,
    format_note,
    format_check,
    format_panel,
    format_pattern_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    slice_record,
    load_pattern,
    legal_step,
    load_pattern_file,
    next_check,
    normalize_check,
    normalize_claim_kind,
    normalize_slice_state,
    normalize_stance,
    normalize_view_filter,
    note_for_pattern,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_pattern_args,
    green_patterns,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_patterns,
    validate_book,
    validate_pattern,
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
EXAMPLE_TITLE = "Pattern extraction at the M-213 slice boundary"
EXAMPLE_CHECKS = ["approved", "approved", "approved"]
EXAMPLE_RUN_IDS = (
    "pattern-held-manoeuvre", "pattern-redrafted-manoeuvre",
    "pattern-own-manoeuvre", "pattern-bare-manoeuvre",
    "pattern-leaping-manoeuvre")
EXAMPLE_TRACE = "spotted > repeated > drafted > judged > approved"


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
        "origin_session": "pattern-test",
    }
    fields.update(overrides)
    return build_slice_ref(fields)


def _pattern(**overrides):
    fields = {
        "pattern_id": "pattern-test",
        "seq": 1,
        "slice_id": "slice-test",
        "title": "A test pattern",
        "checks": ["spotted", "repeated", "drafted", "judged", "approved"],
        "claims": [],
        "detail": "A test pattern held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "pattern-test",
    }
    fields.update(overrides)
    return build_pattern(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "pattern-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "pattern_id": "pattern-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "pattern-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "pattern_id": "pattern-test",
        "trace": "spotted > repeated > drafted > judged > approved",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "pattern-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(slices=None, patterns=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": PATTERN_SCHEMA,
        "slice": "M-214",
        "pattern_extraction": {"title": "A test pattern book"},
        "slices": [item.to_record() for item in (
            slices if slices is not None else [_ref()])],
        "pattern_records": [item.to_record() for item in (
            patterns if patterns is not None else [_pattern()])],
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
    return _book(patterns=[
        _pattern(),
        _pattern(pattern_id="pattern-hidden", seq=2,
               title="A hidden pattern", checks=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_pattern()
    assert book.title == EXAMPLE_TITLE
    assert book.pattern_ids() == EXAMPLE_RUN_IDS
    assert book.slice_ids() == (
        "slice-m213-retro", "slice-m214-pattern",
        "slice-m215-estimate")
    assert [v.view_id for v in book.views] == [
        "view-patterns", "view-approved"]
    assert [m.pattern_id for m in book.notes] == [
        "pattern-held-manoeuvre", "pattern-bare-manoeuvre"]
    assert [a.pattern_id for a in book.traces] == ["pattern-held-manoeuvre"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m213-boundary"
    assert panel.as_of == "2026-11-10"
    assert [row.item_id for row in panel.rows] == list(book.pattern_ids())
    derived = derive_panel(book, "view-patterns")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-patterns").verdict == "held"
    assert derive_verdict(book, "view-patterns").green_shown == 3
    assert derive_verdict(book, "view-approved").verdict == "approved"
    assert derive_verdict(book, "view-approved").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / PATTERN_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == PATTERN_SCHEMA
    assert raw["slice"] == "M-214"
    assert "verdict" not in raw
    assert "pattern_index" not in raw
    assert "board" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-214")]
    assert slice_.title == "Pattern extraction"
    assert slice_.part == 9
    assert "repeated successful manoeuvres" in slice_.summary
    assert "become candidate skills" in slice_.summary
    assert "drafted by the Scribe for approval" in slice_.summary
    assert PATTERN_SLICE == "M-214"

def test_charter_rows_do_not_name_m214():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-214" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert COMPLETE_WORDS == ("complete", "open")
    assert CHECK_FIELDS == ("checks", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "complete", "open")
    assert VERDICT_WORDS == ("approved", "held", "blocked")
    assert SLICE_STATES == ("active", "queued")
    assert CHECKS == ("spotted", "repeated", "drafted", "judged", "approved")
    assert HELD_EVIDENCE == ("slice_ref", "manoeuvre_ref", "test_record", "skill_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["judged"] == ("spotted", "approved")
    assert TRANSITIONS["approved"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_CHECK == "approved"
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
    assert legal_step("drafted", "judged") is True
    assert legal_step("repeated", "approved") is False
    assert legal_step("approved", "spotted") is False
    assert next_check("spotted") == "repeated"
    assert next_check("drafted") == "judged"
    assert next_check("judged", failed=True) == "spotted"
    assert next_check("judged") == "approved"
    assert next_check("approved") is None
    assert "held as data alone" in PATTERN_RULE
    assert "pattern sequence" in PATTERN_RULE
    assert "M-214" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /patterns")

def test_shipped_book_judged_honestly_as_data():
    book = load_pattern()
    opening = book.pattern_for("pattern-held-manoeuvre")
    assert pattern_green(opening, book) is True
    assert pattern_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Pattern: The held manoeuvre",
        "Slice: slice-m213-retro",
        "Check: approved",
        "Claims: slice_ref")
    asking = book.pattern_for("pattern-bare-manoeuvre")
    assert pattern_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert pattern_green(asking, book) is False
    skipping = book.pattern_for("pattern-leaping-manoeuvre")
    assert pattern_gaps(skipping, book) == (
        "steps from repeated to approved, which the pattern sequence "
        "does not allow",)
    assert [g.pattern_id for g in green_patterns(book)] == [
        "pattern-held-manoeuvre", "pattern-redrafted-manoeuvre", "pattern-own-manoeuvre"]
    index = derive_index(book)
    assert [e.check for e in index.entries] == EXAMPLE_CHECKS
    assert index.gaps == ("pattern-bare-manoeuvre", "pattern-leaping-manoeuvre")
    assert pattern_for_check(book, EXAMPLE_CHECK).pattern_id == (
        "pattern-held-manoeuvre")
    assert pattern_for_check(book, "triple resume") is None
    assert transition_breaks(book) == (
        "pattern-leaping-manoeuvre: repeated > approved",)
    assert [g.pattern_id for g in pattern_order(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "pattern-held-manoeuvre") == EXAMPLE_TRACE
    assert trace_current(book, "pattern-held-manoeuvre") is True
    assert trace_current(book, "pattern-redrafted-manoeuvre") is False
    assert trace_for_pattern(
        book, "pattern-held-manoeuvre").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_pattern(
        book, "pattern-held-manoeuvre", "note").note_id == (
            "note-note-first")
    assert note_for_pattern(book, "pattern-nope") is None
    assert current_pattern(book).pattern_id == "pattern-bare-manoeuvre"
    board = board_record(book)
    assert board["standings"] == [
        {"standing": "complete", "pattern_records": 3},
        {"standing": "open", "pattern_records": 2}]
    assert board["total"] == 5
    assert board["current_pattern"] == "pattern-bare-manoeuvre"
    assert board["traces"] == [
        {"pattern_id": "pattern-held-manoeuvre", "trace": "current"},
        {"pattern_id": "pattern-redrafted-manoeuvre", "trace": "unheld"},
        {"pattern_id": "pattern-own-manoeuvre", "trace": "unheld"},
        {"pattern_id": "pattern-bare-manoeuvre", "trace": "unheld"},
        {"pattern_id": "pattern-leaping-manoeuvre", "trace": "unheld"}]
    assert board["breaks"] == ["pattern-leaping-manoeuvre: repeated > approved"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 248
    assert citizen["next_slice"] == "M-249"
    assert citizen["m214_title"] == "Pattern extraction"
    assert citizen["m214_part"] == 9
    assert citizen["m214_status"] == "done"

def test_pattern_record_round_trips():
    pattern = _pattern()
    assert validate_pattern(pattern) is pattern
    rebuilt = build_pattern(pattern.to_record())
    assert rebuilt == pattern
    assert rebuilt.item_id == "pattern-test"
    assert rebuilt.check == "approved"
    record = pattern_record(pattern)
    assert record["type"] == "pattern_pattern"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert slice_record(ref)["type"] == "pattern_slice"
    assert slice_record(ref)["state"] == "active"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _pattern(checks=[])
    assert pattern_gaps(silent) == (
        "has passed through no step: the pattern has not started",)
    assert pattern_green(silent) is False
    walking = _pattern(checks=["spotted", "repeated"])
    assert pattern_gaps(walking) == (
        "has not reached approved: the pattern stands at repeated",)
    assert walking.check == "repeated"
    sideways = _pattern(checks=["repeated", "drafted", "judged", "approved"])
    assert pattern_gaps(sideways) == (
        "opens at repeated, not at spotted: the pattern opens "
        "with the reflection",)
    repaired = _pattern(checks=["spotted", "repeated", "drafted", "judged", "spotted", "repeated", "drafted", "judged", "approved"])
    assert pattern_gaps(repaired) == ()
    assert pattern_green(repaired) is True
    with pytest.raises(ValueError):
        _pattern(checks=[42])
    with pytest.raises(ValueError):
        _pattern(checks="inspect as a bare string")
    with pytest.raises(ValueError):
        _pattern(checks=["spotted", "polish"])
    with pytest.raises(ValueError):
        _pattern(claims=["weather"])
    with pytest.raises(ValueError):
        _pattern(claims="slice_ref")
    none_pattern = _pattern(checks=None, claims=None)
    assert none_pattern.checks == ()
    assert none_pattern.claims == ()

def test_pattern_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "entries", "coverage", "current_pattern",
                "board", "order"):
        fields = _pattern().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_pattern(fields)
    fields = _pattern().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_pattern(fields)


def test_pattern_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _pattern().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_pattern(fields)


def test_pattern_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _pattern(title="")
    with pytest.raises(ValueError):
        _pattern(slice_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "spotted > repeated > drafted > judged > approved"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_patterns_own_fields():
    pattern = _pattern(claims=["slice_ref"])
    assert plain_lines(pattern) == (
        "Pattern: A test pattern",
        "Slice: slice-test",
        "Check: approved",
        "Claims: slice_ref")
    segment = segment_of(pattern)
    assert segment.startswith("pattern-test: A test pattern")
    assert "check: 'approved'" in segment
    assert "gaps: none" in segment
    assert plain_words(pattern).startswith(
        "A test pattern - from slice-test")

def test_red_patterns_stand_named_in_their_gaps():
    asking = _pattern(claims=["feeling", "slice_ref", "summary"])
    assert pattern_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert pattern_green(asking) is False
    skipping = _pattern(checks=["spotted", "repeated", "approved"])
    assert pattern_gaps(skipping) == (
        "steps from repeated to approved, which the pattern sequence "
        "does not allow",)
    book = _book(patterns=[
        _pattern(),
        _pattern(pattern_id="pattern-skipping", seq=2,
             checks=["spotted", "repeated", "approved"]),
    ])
    assert transition_breaks(book) == (
        "pattern-skipping: repeated > approved",)
    assert current_pattern(book).pattern_id == "pattern-skipping"
    assert [g.pattern_id for g in pattern_order(book)] == [
        "pattern-test", "pattern-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "pattern_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "pattern_note"
    assert record["pattern_id"] == "pattern-test"
    assert view_plain_words(view) == "View view-test: shows all patterns."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_patterns_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.check for e in index.entries] == ["approved"]
    assert index.entries[0] == IndexEntry(
        check="approved",
        pattern_id="pattern-test", title="A test pattern")
    assert index.gaps == ("pattern-hidden",)
    record = index_record(book)
    assert record["type"] == "pattern_index"
    assert record["gaps"] == ["pattern-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "pattern_book"

def test_check_target_reaches_its_pattern_and_an_unheld_target_reaches_nothing():
    book = load_pattern()
    assert pattern_for_check(book, "approved").pattern_id == (
        "pattern-held-manoeuvre")
    assert pattern_for_check(book, "") is None
    assert pattern_for_check(book, None) is None
    assert pattern_for_check(book, "not held at all") is None
    text = format_check(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_pattern()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Pattern note note pattern-held-manoeuvre" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").pattern_id == "pattern-test"
    assert note_for_pattern(book, "pattern-test").note_id == "note-test"
    assert note_for_pattern(book, "pattern-test", "praise") is None
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
    row = build_row(None, _pattern(), book)
    assert row.standing == "complete"
    assert validate_row(row, _pattern(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_patterns():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "pattern_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "approved"
    empty_book = _book(patterns=[_pattern(checks=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(PatternVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_pattern()
    assert [g.pattern_id for g in shown_patterns(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.pattern_id for g in shown_patterns(book, "view-approved")] == [
        "pattern-held-manoeuvre", "pattern-redrafted-manoeuvre", "pattern-own-manoeuvre"]
    assert [g.pattern_id for g in patterns_for_slice(
        book, "slice-m214-pattern")] == [
            "pattern-own-manoeuvre", "pattern-bare-manoeuvre",
            "pattern-leaping-manoeuvre"]
    assert patterns_for_slice(book, "slice-nope") == ()
    assert current_pattern(_mixed_book()).pattern_id == "pattern-hidden"
    assert current_pattern(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "pattern-test") == (
        "spotted > repeated > drafted > judged > approved")
    assert trace_current(stale, "pattern-test") is False
    assert board_record(stale)["traces"] == [
        {"pattern_id": "pattern-test", "trace": "stale"}]

def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(patterns=[_pattern(), _pattern(seq=2)])
    with pytest.raises(ValueError):
        _book(patterns=[_pattern(), _pattern(pattern_id="pattern-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(patterns=[_pattern(slice_id="slice-nope")])
    with pytest.raises(ValueError):
        _book(slices=[_ref(), _ref(
            slice_id="slice-cold", seq=2, state="queued")],
            patterns=[_pattern(slice_id="slice-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(slice_id="slice-nope")])
    fields = {
        "schema": PATTERN_SCHEMA, "slice": "M-214",
        "pattern_extraction": {"title": "A drafted book"},
        "slices": [_ref().to_record()],
        "pattern_records": [_pattern().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "approved"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_pattern"] = "pattern-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_pattern")
    fields["trace"] = "pattern-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / PATTERN_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "pattern_extraction.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_pattern_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.pattern_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = PatternRegistry()
    assert registry.title() is None
    registry.register_slice_ref(_ref())
    registry.register_pattern(_pattern())
    registry.register_view(_view())
    assert [g.pattern_id for g in registry.list_patterns()] == ["pattern-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_pattern("pattern-test").title == "A test pattern"
    assert registry.get_slice("slice-test").state == "active"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("pattern-test").pattern_id == "pattern-test"
    with pytest.raises(ValueError):
        registry.register_pattern(_pattern(seq=9))
    with pytest.raises(ValueError):
        registry.register_pattern(_pattern(pattern_id="pattern-two"))
    with pytest.raises(KeyError):
        registry.get_pattern("pattern-nope")
    assert registry.book().title == "An unheld pattern book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = PatternRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test pattern book"
    assert registry.title() == "A test pattern book"
    assert len(registry.list_patterns()) == 2
    other = PatternRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    pattern = _pattern()
    assert "A test pattern" in plain_words(pattern)
    assert panel_plain_words(_mixed_book()).startswith(
        "The pattern book holds 2 patterns")
    assert verdict_plain_words(_mixed_book()) == (
        "The patterns stand held: 1 of 2 shown patterns stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green patterns; red, "
        "named in its gaps: pattern-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_pattern(pattern)
    assert "Pattern: A test pattern" in text
    assert "stands complete" in text
    text = format_pattern(_pattern(checks=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Pattern Gate (M-214) - A test pattern book" in book_text
    assert "pattern-hidden" in format_book(_mixed_book(), "slice-test")
    assert "Pattern panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "approved - A test pattern (pattern-test)" in index_text
    assert "pattern-hidden" in index_text
    screen = format_pattern_screen()
    assert "The Pattern Gate (M-214)" in screen
    assert "pattern-bare-manoeuvre" in screen

def test_parse_args_board_and_loader_targets():
    assert parse_pattern_args("") == ("show", None)
    assert parse_pattern_args(None) == ("show", None)
    assert parse_pattern_args("show") == ("show", None)
    assert parse_pattern_args("pattern pattern-test") == (
        "pattern", "pattern-test")
    assert parse_pattern_args("check approved") == (
        "check", "approved")
    assert parse_pattern_args("slice slice-test") == (
        "slice", "slice-test")
    assert parse_pattern_args("view view-test") == ("view", "view-test")
    assert parse_pattern_args("note note-test") == ("note", "note-test")
    assert parse_pattern_args("index") == ("index", None)
    assert parse_pattern_args("panel") == ("panel", None)
    assert parse_pattern_args("verdict") == ("verdict", None)
    for bad in ("dance", "pattern", "check", "slice", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_pattern_args(bad)
    board = board_record()
    assert board["type"] == "pattern_board"
    assert board["total"] == 5
    assert board["current_pattern"] == "pattern-bare-manoeuvre"
    book = load_pattern({
        "schema": PATTERN_SCHEMA, "slice": "M-214",
        "pattern_extraction": {"title": "A drafted book"},
        "slices": [_ref().to_record()],
        "pattern_records": [_pattern().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, PatternBook)
    assert book.title == "A drafted book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_pattern({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_pattern({"slice": "M-999"})
    built = build_pattern(
        pattern_id="pattern-kw", seq=3, slice_id="slice-test",
        title="Kw Pattern", checks=["spotted", "repeated", "drafted", "judged", "approved"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="pattern-test")
    assert built.pattern_id == "pattern-kw"
    assert pattern_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-214 agent layer: the agent holds a pattern
# book for the session, patterns and views are
# published as session news through the
# checkpoint target (journal first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held patterns, the board is derived from
# the held patterns' completeness, the roadmap standing
# is read from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no slice. This layer patterns
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_PATTERN_EVENT_TYPES = (
    "pattern_pattern", "pattern_slice", "pattern_view",
    "pattern_panel", "pattern_verdict")


def _pattern_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_pattern_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / PATTERN_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "pattern_extraction.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestPatternAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.pattern_status()
        assert status["pattern_records"] == []
        assert status["slices"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["pattern_book"]["title"] == EXAMPLE_TITLE
        assert len(status["pattern_book"]["slices"]) == 3
        assert len(status["pattern_book"]["pattern_records"]) == 5
        assert len(status["pattern_book"]["views"]) == 2
        assert len(status["pattern_book"]["notes"]) == 2
        assert len(status["pattern_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m213-boundary"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["check"] for e in status["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert status["index"]["gaps"] == [
            "pattern-bare-manoeuvre", "pattern-leaping-manoeuvre"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["board"]["total"] == 5
        assert status["board"]["current_pattern"] == "pattern-bare-manoeuvre"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 248
        assert status["roadmap"]["next_slice"] == "M-249"
        assert status["roadmap"]["m214_title"] == "Pattern extraction"
        assert "held as data alone" in status["rule"]
        assert "pattern-bare-manoeuvre" in status["plain_words"]
        assert "The Pattern Gate (M-214)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._pattern_registry()
        assert agent._pattern_registry() is first
        assert agent._pattern_store is first
        for name in ("pattern_book", "pattern_status", "pattern_panel",
                     "pattern_verdict", "pattern_index", "report_pattern"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_pattern_registry", "pattern_book", "pattern_status",
            "get_pattern_pattern", "get_pattern_view", "get_pattern_note",
            "pattern_patterns_for_slice", "pattern_patterns_green",
            "pattern_panel", "pattern_verdict", "pattern_index",
            "register_pattern_pattern", "register_pattern_view",
            "view_pattern", "register_pattern_book",
            "record_pattern_book", "report_pattern",
            "_publish_pattern_record", "_pattern_screen",
            "_pattern_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.pattern_status()
        assert agent.get_pattern_pattern(
            "pattern-held-manoeuvre").title == "The held manoeuvre"
        assert agent.get_pattern_view(
            "view-patterns").view_filter == "all"
        assert agent.get_pattern_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.pattern_id for d in agent.pattern_patterns_for_slice(
            "slice-m214-pattern")] == [
            "pattern-own-manoeuvre", "pattern-bare-manoeuvre",
            "pattern-leaping-manoeuvre"]
        assert [d.pattern_id for d in agent.pattern_patterns_green()] == [
            "pattern-held-manoeuvre", "pattern-redrafted-manoeuvre", "pattern-own-manoeuvre"]
        agent.pattern_panel()
        agent.pattern_verdict()
        agent.pattern_index()
        agent.report_pattern()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _PATTERN_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_pattern_pattern("pattern-nope")
        with pytest.raises(KeyError):
            agent.get_pattern_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_pattern_note("note-nope")
        with pytest.raises(ValueError):
            agent.pattern_patterns_for_slice("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_pattern_pattern(_pattern())
        status = agent.pattern_status()
        assert [d["pattern_id"] for d in status["pattern_records"]] == ["pattern-test"]
        assert status["book"]["title"] == "An unheld pattern book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["check"] for e in status["index"]["entries"]] == [
            "approved"]
        assert status["first_note"] is None
        assert "pattern-test" in status["screen"]
    def test_held_pattern_never_falls_back_to_the_example(
            self, agent):
        agent.register_pattern_pattern(_pattern())
        with pytest.raises(KeyError):
            agent.get_pattern_pattern("pattern-held-manoeuvre")
        with pytest.raises(KeyError):
            agent.get_pattern_view("view-patterns")
        with pytest.raises(KeyError):
            agent.get_pattern_note("note-note-first")
        pattern = agent.get_pattern_pattern("pattern-test")
        assert pattern.title == "A test pattern"
        assert agent.pattern_book().title == (
            "An unheld pattern book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_pattern_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.pattern_id == "pattern-held-manoeuvre"
        status = agent.pattern_status()
        assert status["index"]["gaps"] == [
            "pattern-bare-manoeuvre", "pattern-leaping-manoeuvre"]
        assert status["first_note"]["pattern_id"] == (
            "pattern-held-manoeuvre")
        assert status["first_note"]["stance"] == "note"

class TestPatternAgentHolding:
    def test_register_pattern_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_pattern_pattern(_pattern())
        assert result["pattern"]["pattern_id"] == "pattern-test"
        assert result["record_news"]["type"] == "pattern_pattern"
        assert "pattern-test" in result["screen"]
        events = _pattern_events(store, session_id, "pattern_pattern")
        assert len(events) == 1
        agent.close()

    def test_duplicate_pattern_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_pattern_pattern(_pattern())
        with pytest.raises(ValueError):
            agent.register_pattern_pattern(_pattern(seq=9))
        with pytest.raises(ValueError):
            agent.register_pattern_pattern(_pattern(pattern_id="pattern-two"))
        events = _pattern_events(store, session_id, "pattern_pattern")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_pattern_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_pattern_events(
            store, session_id, "pattern_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_pattern_pattern(_pattern())
        result = agent.view_pattern("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "pattern_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "approved"
        assert len(_pattern_events(
            store, session_id, "pattern_view")) == 1
        assert len(_pattern_events(
            store, session_id, "pattern_panel")) == 1
        assert len(_pattern_events(
            store, session_id, "pattern_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_pattern_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "pattern_slice", "pattern_pattern", "pattern_view"]
        assert len(_pattern_events(
            store, session_id, "pattern_pattern")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_pattern_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "pattern_panel"
        assert result["index_record"]["gaps"] == [
            "pattern-bare-manoeuvre", "pattern-leaping-manoeuvre"]
        with pytest.raises(ValueError):
            agent.record_pattern_book()
        assert len(_pattern_events(
            store, session_id, "pattern_slice")) == 3
        assert len(_pattern_events(
            store, session_id, "pattern_pattern")) == 5
        assert len(_pattern_events(
            store, session_id, "pattern_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_pattern_book_file(tmp_path)
        book = load_pattern_file(path)
        result = agent.record_pattern_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_pattern()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "held"
        assert report["index"]["gaps"] == [
            "pattern-bare-manoeuvre", "pattern-leaping-manoeuvre"]
        assert "pattern-held-manoeuvre" in report["book_text"]
        assert "approved - The held manoeuvre (pattern-held-manoeuvre)" in report["index_text"]
        agent.register_pattern_pattern(_pattern())
        report = agent.report_pattern()
        assert report["book"]["title"] == "An unheld pattern book"
        assert report["panel"] is None
        assert report["verdict"] is None

class TestPatternTerminalHeading:
    def test_show_pattern_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/patterns")
        assert "The Pattern Gate (M-214)" in text
        _, _, text = _slash(agent, "/patterns pattern pattern-held-manoeuvre")
        assert "Pattern: The held manoeuvre" in text
        _, _, text = _slash(
            agent, "/patterns check approved")
        assert "Pattern: The held manoeuvre" in text
        _, _, text = _slash(agent, "/patterns check triple resume")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/patterns slice slice-m214-pattern")
        assert "pattern-bare-manoeuvre" in text
        assert "pattern-held-manoeuvre" not in text
        _, _, text = _slash(agent, "/patterns view view-patterns")
        assert "filter all" in text
        _, _, text = _slash(agent, "/patterns note note-note-first")
        assert "Pattern note note pattern-held-manoeuvre" in text
        _, _, text = _slash(agent, "/patterns index")
        assert "Pattern index" in text
        assert "pattern-bare-manoeuvre" in text
        _, _, text = _slash(agent, "/patterns panel")
        assert "Pattern panel under view view-patterns" in text
        _, _, text = _slash(agent, "/patterns verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/patterns [show|pattern <pattern-id>"
                "|check <check>|slice <slice-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/patterns dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/patterns pattern pattern-nope")
        assert "no pattern named" in text
@pytest.fixture()
def pattern_handler(agent, monkeypatch):
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


def _pattern_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestPatternCommand:
    def test_show_is_default(self, pattern_handler, agent):
        pattern_handler._handle_pattern("")
        assert "The Pattern Gate (M-214)" in (
            _pattern_published_text(pattern_handler))

    def test_pattern_check_slice_view_note_index_panel_verdict(
            self, pattern_handler, agent):
        pattern_handler._handle_pattern("pattern pattern-held-manoeuvre")
        assert "Pattern: The held manoeuvre" in _pattern_published_text(
            pattern_handler)
        pattern_handler._handle_pattern(
            "check approved")
        assert "Pattern: The held manoeuvre" in _pattern_published_text(
            pattern_handler)
        pattern_handler._handle_pattern("slice slice-m214-pattern")
        assert "pattern-bare-manoeuvre" in _pattern_published_text(
            pattern_handler)
        pattern_handler._handle_pattern("view view-patterns")
        assert "filter all" in _pattern_published_text(pattern_handler)
        pattern_handler._handle_pattern("note note-note-first")
        assert "Pattern note note pattern-held-manoeuvre" in (
            _pattern_published_text(pattern_handler))
        pattern_handler._handle_pattern("index")
        assert "Pattern index" in _pattern_published_text(pattern_handler)
        pattern_handler._handle_pattern("panel")
        assert "Pattern panel under view" in _pattern_published_text(
            pattern_handler)
        pattern_handler._handle_pattern("verdict")
        assert "held" in _pattern_published_text(pattern_handler)
    def test_bad_grammar_is_published(
            self, pattern_handler, agent):
        pattern_handler._handle_pattern("dance party")
        assert USAGE in _pattern_published_text(pattern_handler)
        pattern_handler._handle_pattern("pattern pattern-nope")
        assert "no pattern named" in _pattern_published_text(
            pattern_handler)


class TestChatScreenRoutingPattern:
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
        screen.handle_command("/patterns panel", _FakeLog())
        assert calls == [("/patterns", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/patterns[/green] - show the Pattern gate (M-214)" in (
            text)
        assert ('"/patterns": "Usage: /patterns | '
                '/patterns pattern <pattern-id>') in text

class TestPatternDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.pattern_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-patterns"
        verdict = agent.pattern_verdict()
        assert verdict.verdict == "held"
        found = agent.pattern_verdict("view-approved")
        assert found.verdict == "approved"
        assert found.green_shown == 3
        agent.register_pattern_pattern(_pattern())
        with pytest.raises(ValueError):
            agent.pattern_panel()
        with pytest.raises(ValueError):
            agent.pattern_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_pattern_pattern(_pattern(checks=[]))
        result = agent.view_pattern("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.pattern_index()
        assert [e["check"] for e in result["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert result["index"]["gaps"] == [
            "pattern-bare-manoeuvre", "pattern-leaping-manoeuvre"]
        assert "approved - The held manoeuvre (pattern-held-manoeuvre)" in (
            result["index_text"])
        pattern = agent.get_pattern_pattern("pattern-leaping-manoeuvre")
        assert pattern_gaps(pattern, agent.pattern_book()) == (
            "steps from repeated to approved, which the pattern sequence "
            "does not allow",)
        assert pattern_green(pattern, agent.pattern_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _PATTERN_EVENT_TYPES] == []
        agent.close()
