"""M-221 Entrys - pure-layer tests.

TIER: integration

The pure layer is the logkeeper, held as data: one
record per entry, held whole - the slice it
answers for, named by slice id, its title, the
steps it walked in walk order and the evidence
it carries, held by day. The question walk is
explicit - named, worded, checked, read,
kept, with their legal steps held as data -
and a entry's standing is derived at call
time: a entry that opens anywhere but noted, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet noted kept stands open,
named in its gaps. A entry stands only for
an active slice: a entry naming no held
slice, or one that is not active, refuses by
name. The entry's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, diary, trace, order and current
entry are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, read or
kept live. The shipped example book is held
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

from mythic_agent.core.build_log import (
    EXAMPLE_CHECK,
    BARE_CLAIMS,
    HELD_EVIDENCE,
    INDEX_ACTION,
    CHECKS,
    CLAIM_DAYS,
    TRANSITIONS,
    DAY_STATES,
    CHECK_FIELDS,
    PLAIN_EXPLANATION,
    ENTRY_RESOURCE,
    ENTRY_RULE,
    ENTRY_SCHEMA,
    ENTRY_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    EntryRecord,
    IndexEntry,
    DayRef,
    NoteRecord,
    EntryBook,
    EntryIndex,
    EntryPanel,
    EntryRegistry,
    EntryVerdict,
    EntryView,
    trace_for_entry,
    diary_record,
    book_record,
    build_trace,
    build_book,
    build_entry,
    build_day_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_entry,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    entry_for_check,
    entry_gaps,
    entry_order,
    entry_record,
    entry_green,
    entries_for_day,
    first_note,
    format_book,
    format_entry,
    format_index,
    format_note,
    format_check,
    format_panel,
    format_entry_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    day_record,
    load_entry,
    legal_step,
    load_entry_file,
    next_check,
    normalize_check,
    normalize_claim_day,
    normalize_day_state,
    normalize_stance,
    normalize_view_filter,
    note_for_entry,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_entry_args,
    green_entrys,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_entrys,
    validate_book,
    validate_entry,
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
EXAMPLE_TITLE = "The plain-language build log at the M-221 slice day"
EXAMPLE_CHECKS = ["kept", "kept", "kept"]
EXAMPLE_RUN_IDS = (
    "entry-held-entry", "entry-remeasured-entry",
    "entry-own-entry", "entry-bare-entry",
    "entry-leaping-entry")
EXAMPLE_TRACE = "noted > worded > checked > read > kept"


def _ref(**overrides):
    fields = {
        "day_id": "slice-test",
        "seq": 1,
        "title": "A test slice",
        "state": "live",
        "detail": "A test slice reference held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "entry-test",
    }
    fields.update(overrides)
    return build_day_ref(fields)


def _entry(**overrides):
    fields = {
        "entry_id": "entry-test",
        "seq": 1,
        "day_id": "slice-test",
        "title": "A test entry",
        "checks": ["noted", "worded", "checked", "read", "kept"],
        "claims": [],
        "detail": "A test entry held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "entry-test",
    }
    fields.update(overrides)
    return build_entry(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "entry-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "entry_id": "entry-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "entry-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "entry_id": "entry-test",
        "trace": "noted > worded > checked > read > kept",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "entry-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(slices=None, entries=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": ENTRY_SCHEMA,
        "slice": "M-221",
        "build_log": {"title": "A test entry book"},
        "days": [item.to_record() for item in (
            slices if slices is not None else [_ref()])],
        "entry_records": [item.to_record() for item in (
            entries if entries is not None else [_entry()])],
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
    return _book(entries=[
        _entry(),
        _entry(entry_id="entry-hidden", seq=2,
               title="A hidden entry", checks=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_entry()
    assert book.title == EXAMPLE_TITLE
    assert book.entry_ids() == EXAMPLE_RUN_IDS
    assert book.day_ids() == (
        "day-m220-milestones", "day-m221-log",
        "day-m222-guarded")
    assert [v.view_id for v in book.views] == [
        "view-entries", "view-kept"]
    assert [m.entry_id for m in book.notes] == [
        "entry-held-entry", "entry-bare-entry"]
    assert [a.entry_id for a in book.traces] == ["entry-held-entry"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m220-day"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.entry_ids())
    derived = derive_panel(book, "view-entries")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-entries").verdict == "held"
    assert derive_verdict(book, "view-entries").green_shown == 3
    assert derive_verdict(book, "view-kept").verdict == "kept"
    assert derive_verdict(book, "view-kept").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / ENTRY_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == ENTRY_SCHEMA
    assert raw["slice"] == "M-221"
    assert "verdict" not in raw
    assert "entry_index" not in raw
    assert "diary" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-221")]
    assert slice_.title == "The plain-language build log"
    assert slice_.part == 9
    assert "the campaign's diary in the user's words" in slice_.summary
    assert "readable by the human it was built for" in slice_.summary
    assert ENTRY_SLICE == "M-221"

def test_charter_rows_do_not_name_m221():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-221" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert COMPLETE_WORDS == ("complete", "open")
    assert CHECK_FIELDS == ("checks", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "complete", "open")
    assert VERDICT_WORDS == ("kept", "held", "blocked")
    assert DAY_STATES == ("live", "dormant")
    assert CHECKS == ("noted", "worded", "checked", "read", "kept")
    assert HELD_EVIDENCE == ("day_ref", "words_ref", "keeper_record", "entry_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_DAYS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["read"] == ("noted", "kept")
    assert TRANSITIONS["kept"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_CHECK == "kept"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_day_state("LIVE") == "live"
    assert normalize_check("CHECKED") == "checked"
    assert normalize_claim_day("FEELING") == "feeling"
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    with pytest.raises(ValueError):
        normalize_day_state("blessed")
    with pytest.raises(ValueError):
        normalize_check("polish")
    with pytest.raises(ValueError):
        normalize_claim_day("weather")
    assert legal_step("checked", "read") is True
    assert legal_step("worded", "kept") is False
    assert legal_step("kept", "noted") is False
    assert next_check("noted") == "worded"
    assert next_check("checked") == "read"
    assert next_check("read", failed=True) == "noted"
    assert next_check("read") == "kept"
    assert next_check("kept") is None
    assert "held as data alone" in ENTRY_RULE
    assert "entry sequence" in ENTRY_RULE
    assert "M-221" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /log")

def test_shipped_book_judged_honestly_as_data():
    book = load_entry()
    opening = book.entry_for("entry-held-entry")
    assert entry_green(opening, book) is True
    assert entry_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Entry: The held entry",
        "Day: day-m220-milestones",
        "Check: kept",
        "Claims: day_ref")
    asking = book.entry_for("entry-bare-entry")
    assert entry_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert entry_green(asking, book) is False
    skipping = book.entry_for("entry-leaping-entry")
    assert entry_gaps(skipping, book) == (
        "steps from worded to kept, which the entry sequence "
        "does not allow",)
    assert [g.entry_id for g in green_entrys(book)] == [
        "entry-held-entry", "entry-remeasured-entry", "entry-own-entry"]
    index = derive_index(book)
    assert [e.check for e in index.entries] == EXAMPLE_CHECKS
    assert index.gaps == ("entry-bare-entry", "entry-leaping-entry")
    assert entry_for_check(book, EXAMPLE_CHECK).entry_id == (
        "entry-held-entry")
    assert entry_for_check(book, "triple entry") is None
    assert transition_breaks(book) == (
        "entry-leaping-entry: worded > kept",)
    assert [g.entry_id for g in entry_order(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "entry-held-entry") == EXAMPLE_TRACE
    assert trace_current(book, "entry-held-entry") is True
    assert trace_current(book, "entry-remeasured-entry") is False
    assert trace_for_entry(
        book, "entry-held-entry").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_entry(
        book, "entry-held-entry", "note").note_id == (
            "note-note-first")
    assert note_for_entry(book, "entry-nope") is None
    assert current_entry(book).entry_id == "entry-bare-entry"
    diary = diary_record(book)
    assert diary["standings"] == [
        {"standing": "complete", "entry_records": 3},
        {"standing": "open", "entry_records": 2}]
    assert diary["total"] == 5
    assert diary["current_entry"] == "entry-bare-entry"
    assert diary["traces"] == [
        {"entry_id": "entry-held-entry", "trace": "current"},
        {"entry_id": "entry-remeasured-entry", "trace": "unheld"},
        {"entry_id": "entry-own-entry", "trace": "unheld"},
        {"entry_id": "entry-bare-entry", "trace": "unheld"},
        {"entry_id": "entry-leaping-entry", "trace": "unheld"}]
    assert diary["breaks"] == ["entry-leaping-entry: worded > kept"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 222
    assert citizen["next_slice"] == "M-223"
    assert citizen["m221_title"] == "The plain-language build log"
    assert citizen["m221_part"] == 9
    assert citizen["m221_status"] == "done"

def test_entry_record_round_trips():
    entry = _entry()
    assert validate_entry(entry) is entry
    rebuilt = build_entry(entry.to_record())
    assert rebuilt == entry
    assert rebuilt.item_id == "entry-test"
    assert rebuilt.check == "kept"
    record = entry_record(entry)
    assert record["type"] == "entry_entry"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert day_record(ref)["type"] == "entry_slice"
    assert day_record(ref)["state"] == "live"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _entry(checks=[])
    assert entry_gaps(silent) == (
        "has passed through no step: the entry has not started",)
    assert entry_green(silent) is False
    walking = _entry(checks=["noted", "worded"])
    assert entry_gaps(walking) == (
        "has not noted kept: the entry stands at worded",)
    assert walking.check == "worded"
    sideways = _entry(checks=["worded", "checked", "read", "kept"])
    assert entry_gaps(sideways) == (
        "opens at worded, not at noted: the entry opens "
        "with the reflection",)
    repaired = _entry(checks=["noted", "worded", "checked", "read", "noted", "worded", "checked", "read", "kept"])
    assert entry_gaps(repaired) == ()
    assert entry_green(repaired) is True
    with pytest.raises(ValueError):
        _entry(checks=[42])
    with pytest.raises(ValueError):
        _entry(checks="inspect as a bare string")
    with pytest.raises(ValueError):
        _entry(checks=["noted", "polish"])
    with pytest.raises(ValueError):
        _entry(claims=["weather"])
    with pytest.raises(ValueError):
        _entry(claims="day_ref")
    none_entry = _entry(checks=None, claims=None)
    assert none_entry.checks == ()
    assert none_entry.claims == ()

def test_entry_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "entries", "coverage", "current_entry",
                "diary", "order"):
        fields = _entry().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_entry(fields)
    fields = _entry().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_entry(fields)


def test_entry_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _entry().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_entry(fields)


def test_entry_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _entry(title="")
    with pytest.raises(ValueError):
        _entry(day_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "noted > worded > checked > read > kept"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_entrys_own_fields():
    entry = _entry(claims=["day_ref"])
    assert plain_lines(entry) == (
        "Entry: A test entry",
        "Day: slice-test",
        "Check: kept",
        "Claims: day_ref")
    segment = segment_of(entry)
    assert segment.startswith("entry-test: A test entry")
    assert "check: 'kept'" in segment
    assert "gaps: none" in segment
    assert plain_words(entry).startswith(
        "A test entry - from slice-test")

def test_red_entrys_stand_named_in_their_gaps():
    asking = _entry(claims=["feeling", "day_ref", "summary"])
    assert entry_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert entry_green(asking) is False
    skipping = _entry(checks=["noted", "worded", "kept"])
    assert entry_gaps(skipping) == (
        "steps from worded to kept, which the entry sequence "
        "does not allow",)
    book = _book(entries=[
        _entry(),
        _entry(entry_id="entry-skipping", seq=2,
             checks=["noted", "worded", "kept"]),
    ])
    assert transition_breaks(book) == (
        "entry-skipping: worded > kept",)
    assert current_entry(book).entry_id == "entry-skipping"
    assert [g.entry_id for g in entry_order(book)] == [
        "entry-test", "entry-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "entry_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "entry_note"
    assert record["entry_id"] == "entry-test"
    assert view_plain_words(view) == "View view-test: shows all entries."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_entrys_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.check for e in index.entries] == ["kept"]
    assert index.entries[0] == IndexEntry(
        check="kept",
        entry_id="entry-test", title="A test entry")
    assert index.gaps == ("entry-hidden",)
    record = index_record(book)
    assert record["type"] == "entry_index"
    assert record["gaps"] == ["entry-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "entry_book"

def test_check_target_reaches_its_entry_and_an_unheld_target_reaches_nothing():
    book = load_entry()
    assert entry_for_check(book, "kept").entry_id == (
        "entry-held-entry")
    assert entry_for_check(book, "") is None
    assert entry_for_check(book, None) is None
    assert entry_for_check(book, "not held at all") is None
    text = format_check(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_entry()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Entry note note entry-held-entry" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").entry_id == "entry-test"
    assert note_for_entry(book, "entry-test").note_id == "note-test"
    assert note_for_entry(book, "entry-test", "praise") is None
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
    row = build_row(None, _entry(), book)
    assert row.standing == "complete"
    assert validate_row(row, _entry(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_entrys():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "entry_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "kept"
    empty_book = _book(entries=[_entry(checks=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(EntryVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_entry()
    assert [g.entry_id for g in shown_entrys(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.entry_id for g in shown_entrys(book, "view-kept")] == [
        "entry-held-entry", "entry-remeasured-entry", "entry-own-entry"]
    assert [g.entry_id for g in entries_for_day(
        book, "day-m221-log")] == [
            "entry-own-entry", "entry-bare-entry",
            "entry-leaping-entry"]
    assert entries_for_day(book, "slice-nope") == ()
    assert current_entry(_mixed_book()).entry_id == "entry-hidden"
    assert current_entry(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "entry-test") == (
        "noted > worded > checked > read > kept")
    assert trace_current(stale, "entry-test") is False
    assert diary_record(stale)["traces"] == [
        {"entry_id": "entry-test", "trace": "stale"}]

def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(entries=[_entry(), _entry(seq=2)])
    with pytest.raises(ValueError):
        _book(entries=[_entry(), _entry(entry_id="entry-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(entries=[_entry(day_id="slice-nope")])
    with pytest.raises(ValueError):
        _book(slices=[_ref(), _ref(
            day_id="slice-cold", seq=2, state="dormant")],
            entries=[_entry(day_id="slice-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(day_id="slice-nope")])
    fields = {
        "schema": ENTRY_SCHEMA, "slice": "M-221",
        "build_log": {"title": "A checked book"},
        "slices": [_ref().to_record()],
        "entry_records": [_entry().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "kept"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_entry"] = "entry-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_entry")
    fields["trace"] = "entry-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / ENTRY_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "build_log.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_entry_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.entry_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = EntryRegistry()
    assert registry.title() is None
    registry.register_day_ref(_ref())
    registry.register_entry(_entry())
    registry.register_view(_view())
    assert [g.entry_id for g in registry.list_entrys()] == ["entry-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_entry("entry-test").title == "A test entry"
    assert registry.get_slice("slice-test").state == "live"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("entry-test").entry_id == "entry-test"
    with pytest.raises(ValueError):
        registry.register_entry(_entry(seq=9))
    with pytest.raises(ValueError):
        registry.register_entry(_entry(entry_id="entry-two"))
    with pytest.raises(KeyError):
        registry.get_entry("entry-nope")
    assert registry.book().title == "An unheld entry book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = EntryRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test entry book"
    assert registry.title() == "A test entry book"
    assert len(registry.list_entrys()) == 2
    other = EntryRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    entry = _entry()
    assert "A test entry" in plain_words(entry)
    assert panel_plain_words(_mixed_book()).startswith(
        "The entry book holds 2 entries")
    assert verdict_plain_words(_mixed_book()) == (
        "The entries stand held: 1 of 2 shown entries stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green entries; red, "
        "named in its gaps: entry-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_entry(entry)
    assert "Entry: A test entry" in text
    assert "stands complete" in text
    text = format_entry(_entry(checks=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Entry Gate (M-221) - A test entry book" in book_text
    assert "entry-hidden" in format_book(_mixed_book(), "slice-test")
    assert "Entry panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "kept - A test entry (entry-test)" in index_text
    assert "entry-hidden" in index_text
    screen = format_entry_screen()
    assert "The Entry Gate (M-221)" in screen
    assert "entry-bare-entry" in screen

def test_parse_args_well_and_loader_targets():
    assert parse_entry_args("") == ("show", None)
    assert parse_entry_args(None) == ("show", None)
    assert parse_entry_args("show") == ("show", None)
    assert parse_entry_args("entry entry-test") == (
        "entry", "entry-test")
    assert parse_entry_args("check kept") == (
        "check", "kept")
    assert parse_entry_args("day slice-test") == (
        "day", "slice-test")
    assert parse_entry_args("view view-test") == ("view", "view-test")
    assert parse_entry_args("note note-test") == ("note", "note-test")
    assert parse_entry_args("index") == ("index", None)
    assert parse_entry_args("panel") == ("panel", None)
    assert parse_entry_args("verdict") == ("verdict", None)
    for bad in ("dance", "entry", "check", "slice", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_entry_args(bad)
    diary = diary_record()
    assert diary["type"] == "entry_well"
    assert diary["total"] == 5
    assert diary["current_entry"] == "entry-bare-entry"
    book = load_entry({
        "schema": ENTRY_SCHEMA, "slice": "M-221",
        "build_log": {"title": "A checked book"},
        "slices": [_ref().to_record()],
        "entry_records": [_entry().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, EntryBook)
    assert book.title == "A checked book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_entry({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_entry({"slice": "M-999"})
    built = build_entry(
        entry_id="entry-kw", seq=3, day_id="slice-test",
        title="Kw Entry", checks=["noted", "worded", "checked", "read", "kept"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="entry-test")
    assert built.entry_id == "entry-kw"
    assert entry_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-221 agent layer: the agent holds a entry
# book for the session, entries and views are
# published as session news through the
# checkpoint target (diary first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held entries, the diary is derived from
# the held entries' completeness, the roadmap standing
# is read from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no slice. This layer entries
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session diary news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_ENTRY_EVENT_TYPES = (
    "entry_entry", "entry_slice", "entry_view",
    "entry_panel", "entry_verdict")


def _entry_events(store, session_id, day):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == day]


def _write_log_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / ENTRY_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "build_log.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestEntryAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.log_status()
        assert status["entry_records"] == []
        assert status["slices"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["log_book"]["title"] == EXAMPLE_TITLE
        assert len(status["log_book"]["slices"]) == 3
        assert len(status["log_book"]["entry_records"]) == 5
        assert len(status["log_book"]["views"]) == 2
        assert len(status["log_book"]["notes"]) == 2
        assert len(status["log_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m220-day"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["check"] for e in status["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert status["index"]["gaps"] == [
            "entry-bare-entry", "entry-leaping-entry"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["diary"]["total"] == 5
        assert status["diary"]["current_entry"] == "entry-bare-entry"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 222
        assert status["roadmap"]["next_slice"] == "M-223"
        assert status["roadmap"]["m221_title"] == "The plain-language build log"
        assert "held as data alone" in status["rule"]
        assert "entry-bare-entry" in status["plain_words"]
        assert "The Entry Gate (M-221)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._log_registry()
        assert agent._log_registry() is first
        assert agent._log_store is first
        for name in ("log_book", "log_status", "log_panel",
                     "log_verdict", "log_index", "report_log"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_log_registry", "log_book", "log_status",
            "get_log_entry", "get_log_view", "get_log_note",
            "entries_for_day", "entries_green",
            "log_panel", "log_verdict", "log_index",
            "register_log_entry", "register_log_view",
            "view_log", "register_log_book",
            "record_log_book", "report_log",
            "_publish_log_record", "_log_screen",
            "_log_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.log_status()
        assert agent.get_log_entry(
            "entry-held-entry").title == "The held entry"
        assert agent.get_log_view(
            "view-entries").view_filter == "all"
        assert agent.get_log_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.entry_id for d in agent.entries_for_day(
            "day-m221-log")] == [
            "entry-own-entry", "entry-bare-entry",
            "entry-leaping-entry"]
        assert [d.entry_id for d in agent.entries_green()] == [
            "entry-held-entry", "entry-remeasured-entry", "entry-own-entry"]
        agent.log_panel()
        agent.log_verdict()
        agent.log_index()
        agent.report_log()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _ENTRY_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_log_entry("entry-nope")
        with pytest.raises(KeyError):
            agent.get_log_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_log_note("note-nope")
        with pytest.raises(ValueError):
            agent.entries_for_day("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_log_entry(_entry())
        status = agent.log_status()
        assert [d["entry_id"] for d in status["entry_records"]] == ["entry-test"]
        assert status["book"]["title"] == "An unheld entry book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["check"] for e in status["index"]["entries"]] == [
            "kept"]
        assert status["first_note"] is None
        assert "entry-test" in status["screen"]
    def test_held_entry_never_falls_back_to_the_example(
            self, agent):
        agent.register_log_entry(_entry())
        with pytest.raises(KeyError):
            agent.get_log_entry("entry-held-entry")
        with pytest.raises(KeyError):
            agent.get_log_view("view-entries")
        with pytest.raises(KeyError):
            agent.get_log_note("note-note-first")
        entry = agent.get_log_entry("entry-test")
        assert entry.title == "A test entry"
        assert agent.log_book().title == (
            "An unheld entry book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_log_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.entry_id == "entry-held-entry"
        status = agent.log_status()
        assert status["index"]["gaps"] == [
            "entry-bare-entry", "entry-leaping-entry"]
        assert status["first_note"]["entry_id"] == (
            "entry-held-entry")
        assert status["first_note"]["stance"] == "note"

class TestEntryAgentHolding:
    def test_register_entry_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_log_entry(_entry())
        assert result["entry"]["entry_id"] == "entry-test"
        assert result["record_news"]["type"] == "entry_entry"
        assert "entry-test" in result["screen"]
        events = _entry_events(store, session_id, "entry_entry")
        assert len(events) == 1
        agent.close()

    def test_duplicate_entry_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_log_entry(_entry())
        with pytest.raises(ValueError):
            agent.register_log_entry(_entry(seq=9))
        with pytest.raises(ValueError):
            agent.register_log_entry(_entry(entry_id="entry-two"))
        events = _entry_events(store, session_id, "entry_entry")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_log_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_entry_events(
            store, session_id, "entry_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_log_entry(_entry())
        result = agent.view_log("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "entry_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "kept"
        assert len(_entry_events(
            store, session_id, "entry_view")) == 1
        assert len(_entry_events(
            store, session_id, "entry_panel")) == 1
        assert len(_entry_events(
            store, session_id, "entry_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_log_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "entry_slice", "entry_entry", "entry_view"]
        assert len(_entry_events(
            store, session_id, "entry_entry")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_log_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "entry_panel"
        assert result["index_record"]["gaps"] == [
            "entry-bare-entry", "entry-leaping-entry"]
        with pytest.raises(ValueError):
            agent.record_log_book()
        assert len(_entry_events(
            store, session_id, "entry_slice")) == 3
        assert len(_entry_events(
            store, session_id, "entry_entry")) == 5
        assert len(_entry_events(
            store, session_id, "entry_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_log_book_file(tmp_path)
        book = load_entry_file(path)
        result = agent.record_log_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_dayrt_renders_example_then_held_book_only(self, agent):
        entry = agent.report_log()
        assert entry["book"]["title"] == EXAMPLE_TITLE
        assert entry["verdict"]["verdict"] == "held"
        assert entry["index"]["gaps"] == [
            "entry-bare-entry", "entry-leaping-entry"]
        assert "entry-held-entry" in entry["book_text"]
        assert "kept - The held entry (entry-held-entry)" in entry["index_text"]
        agent.register_log_entry(_entry())
        entry = agent.report_log()
        assert entry["book"]["title"] == "An unheld entry book"
        assert entry["panel"] is None
        assert entry["verdict"] is None

class TestEntryTerminalHeading:
    def test_show_entry_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/log")
        assert "The Entry Gate (M-221)" in text
        _, _, text = _slash(agent, "/log entry entry-held-entry")
        assert "Entry: The held entry" in text
        _, _, text = _slash(
            agent, "/log check kept")
        assert "Entry: The held entry" in text
        _, _, text = _slash(agent, "/log check triple entry")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/log day day-m221-log")
        assert "entry-bare-entry" in text
        assert "entry-held-entry" not in text
        _, _, text = _slash(agent, "/log view view-entries")
        assert "filter all" in text
        _, _, text = _slash(agent, "/log note note-note-first")
        assert "Entry note note entry-held-entry" in text
        _, _, text = _slash(agent, "/log index")
        assert "Entry index" in text
        assert "entry-bare-entry" in text
        _, _, text = _slash(agent, "/log panel")
        assert "Entry panel under view view-entries" in text
        _, _, text = _slash(agent, "/log verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/log [show|entry <entry-id>"
                "|check <check>|day <day-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/log dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/log entry entry-nope")
        assert "no entry named" in text
@pytest.fixture()
def entry_handler(agent, monkeypatch):
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


def _entry_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestEntryCommand:
    def test_show_is_default(self, entry_handler, agent):
        entry_handler._handle_log("")
        assert "The Entry Gate (M-221)" in (
            _entry_published_text(entry_handler))

    def test_entry_check_slice_view_note_index_panel_verdict(
            self, entry_handler, agent):
        entry_handler._handle_log("entry entry-held-entry")
        assert "Entry: The held entry" in _entry_published_text(
            entry_handler)
        entry_handler._handle_log(
            "check kept")
        assert "Entry: The held entry" in _entry_published_text(
            entry_handler)
        entry_handler._handle_log("day day-m221-log")
        assert "entry-bare-entry" in _entry_published_text(
            entry_handler)
        entry_handler._handle_log("view view-entries")
        assert "filter all" in _entry_published_text(entry_handler)
        entry_handler._handle_log("note note-note-first")
        assert "Entry note note entry-held-entry" in (
            _entry_published_text(entry_handler))
        entry_handler._handle_log("index")
        assert "Entry index" in _entry_published_text(entry_handler)
        entry_handler._handle_log("panel")
        assert "Entry panel under view" in _entry_published_text(
            entry_handler)
        entry_handler._handle_log("verdict")
        assert "held" in _entry_published_text(entry_handler)
    def test_bad_grammar_is_published(
            self, entry_handler, agent):
        entry_handler._handle_log("dance party")
        assert USAGE in _entry_published_text(entry_handler)
        entry_handler._handle_log("entry entry-nope")
        assert "no entry named" in _entry_published_text(
            entry_handler)


class TestChatScreenRoutingEntry:
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
        screen.handle_command("/log panel", _FakeLog())
        assert calls == [("/log", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/log[/green] - show the Entry gate (M-221)" in (
            text)
        assert ('"/log": "Usage: /log | '
                '/log entry <entry-id>') in text

class TestEntryDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.log_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-entries"
        verdict = agent.log_verdict()
        assert verdict.verdict == "held"
        found = agent.log_verdict("view-kept")
        assert found.verdict == "kept"
        assert found.green_shown == 3
        agent.register_log_entry(_entry())
        with pytest.raises(ValueError):
            agent.log_panel()
        with pytest.raises(ValueError):
            agent.log_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_log_entry(_entry(checks=[]))
        result = agent.view_log("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.log_index()
        assert [e["check"] for e in result["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert result["index"]["gaps"] == [
            "entry-bare-entry", "entry-leaping-entry"]
        assert "kept - The held entry (entry-held-entry)" in (
            result["index_text"])
        entry = agent.get_log_entry("entry-leaping-entry")
        assert entry_gaps(entry, agent.log_book()) == (
            "steps from worded to kept, which the entry sequence "
            "does not allow",)
        assert entry_green(entry, agent.log_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _ENTRY_EVENT_TYPES] == []
        agent.close()
