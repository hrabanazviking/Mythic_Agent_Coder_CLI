"""M-222 Changes - pure-layer tests.

TIER: integration

The pure layer is the guardkeeper, held as data: one
record per change, held whole - the slice it
answers for, named by slice id, its title, the
steps it walked in walk order and the evidence
it carries, held by tool. The question walk is
explicit - named, drafted, guarded, tested,
adopted, with their legal steps held as data -
and a change's standing is derived at call
time: a change that opens anywhere but proposed, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet proposed adopted stands open,
named in its gaps. A change stands only for
an active slice: a change naming no held
slice, or one that is not active, refuses by
name. The change's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, ledger, trace, order and current
change are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, tested or
adopted live. The shipped example book is held
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

from mythic_agent.core.self_modification import (
    EXAMPLE_CHECK,
    BARE_CLAIMS,
    HELD_EVIDENCE,
    INDEX_ACTION,
    CHECKS,
    CLAIM_TOOLS,
    TRANSITIONS,
    TOOL_STATES,
    CHECK_FIELDS,
    PLAIN_EXPLANATION,
    CHANGE_RESOURCE,
    CHANGE_RULE,
    CHANGE_SCHEMA,
    CHANGE_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    ChangeRecord,
    IndexChange,
    ToolRef,
    NoteRecord,
    ChangeBook,
    ChangeIndex,
    ChangePanel,
    ChangeRegistry,
    ChangeVerdict,
    ChangeView,
    trace_for_change,
    ledger_record,
    book_record,
    build_trace,
    build_book,
    build_change,
    build_tool_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_change,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    change_for_check,
    change_gaps,
    change_order,
    change_record,
    change_green,
    changes_for_tool,
    first_note,
    format_book,
    format_change,
    format_index,
    format_note,
    format_check,
    format_panel,
    format_change_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    tool_record,
    load_change,
    legal_step,
    load_change_file,
    next_check,
    normalize_check,
    normalize_claim_tool,
    normalize_tool_state,
    normalize_stance,
    normalize_view_filter,
    note_for_change,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_change_args,
    green_changes,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_changes,
    validate_book,
    validate_change,
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
EXAMPLE_TITLE = "Guarded self-modification at the M-222 slice tool"
EXAMPLE_CHECKS = ["adopted", "adopted", "adopted"]
EXAMPLE_RUN_IDS = (
    "change-held-change", "change-remeasured-change",
    "change-own-change", "change-bare-change",
    "change-leaping-change")
EXAMPLE_TRACE = "proposed > drafted > guarded > tested > adopted"


def _ref(**overrides):
    fields = {
        "tool_id": "slice-test",
        "seq": 1,
        "title": "A test slice",
        "state": "live",
        "detail": "A test slice reference held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "change-test",
    }
    fields.update(overrides)
    return build_tool_ref(fields)


def _change(**overrides):
    fields = {
        "change_id": "change-test",
        "seq": 1,
        "tool_id": "slice-test",
        "title": "A test change",
        "checks": ["proposed", "drafted", "guarded", "tested", "adopted"],
        "claims": [],
        "detail": "A test change held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "change-test",
    }
    fields.update(overrides)
    return build_change(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "change-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "change_id": "change-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "change-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "change_id": "change-test",
        "trace": "proposed > drafted > guarded > tested > adopted",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "change-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(slices=None, changes=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": CHANGE_SCHEMA,
        "slice": "M-222",
        "self_modification": {"title": "A test change book"},
        "tools": [item.to_record() for item in (
            slices if slices is not None else [_ref()])],
        "change_records": [item.to_record() for item in (
            changes if changes is not None else [_change()])],
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
    return _book(changes=[
        _change(),
        _change(change_id="change-hidden", seq=2,
               title="A hidden change", checks=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_change()
    assert book.title == EXAMPLE_TITLE
    assert book.change_ids() == EXAMPLE_RUN_IDS
    assert book.tool_ids() == (
        "tool-m221-log", "tool-m222-selfmod",
        "tool-m223-taxonomy")
    assert [v.view_id for v in book.views] == [
        "view-changes", "view-adopted"]
    assert [m.change_id for m in book.notes] == [
        "change-held-change", "change-bare-change"]
    assert [a.change_id for a in book.traces] == ["change-held-change"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m221-tool"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.change_ids())
    derived = derive_panel(book, "view-changes")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-changes").verdict == "held"
    assert derive_verdict(book, "view-changes").green_shown == 3
    assert derive_verdict(book, "view-adopted").verdict == "adopted"
    assert derive_verdict(book, "view-adopted").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / CHANGE_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == CHANGE_SCHEMA
    assert raw["slice"] == "M-222"
    assert "verdict" not in raw
    assert "change_index" not in raw
    assert "ledger" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-222")]
    assert slice_.title == "Guarded self-modification"
    assert slice_.part == 9
    assert "Mythic improving *itself* under campaign rules (M-141)" in slice_.summary
    assert "the forge may sharpen its own hammer only on the record" in slice_.summary
    assert CHANGE_SLICE == "M-222"

def test_charter_rows_do_not_name_m222():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-222" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert COMPLETE_WORDS == ("complete", "open")
    assert CHECK_FIELDS == ("checks", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "complete", "open")
    assert VERDICT_WORDS == ("adopted", "held", "blocked")
    assert TOOL_STATES == ("live", "dormant")
    assert CHECKS == ("proposed", "drafted", "guarded", "tested", "adopted")
    assert HELD_EVIDENCE == ("tool_ref", "draft_ref", "keeper_record", "change_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_TOOLS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["tested"] == ("proposed", "adopted")
    assert TRANSITIONS["adopted"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_CHECK == "adopted"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_tool_state("LIVE") == "live"
    assert normalize_check("GUARDED") == "guarded"
    assert normalize_claim_tool("FEELING") == "feeling"
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    with pytest.raises(ValueError):
        normalize_tool_state("blessed")
    with pytest.raises(ValueError):
        normalize_check("polish")
    with pytest.raises(ValueError):
        normalize_claim_tool("weather")
    assert legal_step("guarded", "tested") is True
    assert legal_step("drafted", "adopted") is False
    assert legal_step("adopted", "proposed") is False
    assert next_check("proposed") == "drafted"
    assert next_check("guarded") == "tested"
    assert next_check("tested", failed=True) == "proposed"
    assert next_check("tested") == "adopted"
    assert next_check("adopted") is None
    assert "held as data alone" in CHANGE_RULE
    assert "change sequence" in CHANGE_RULE
    assert "M-222" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /selfmod")

def test_shipped_book_judged_honestly_as_data():
    book = load_change()
    opening = book.change_for("change-held-change")
    assert change_green(opening, book) is True
    assert change_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Change: The held change",
        "Tool: tool-m221-log",
        "Check: adopted",
        "Claims: tool_ref")
    asking = book.change_for("change-bare-change")
    assert change_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert change_green(asking, book) is False
    skipping = book.change_for("change-leaping-change")
    assert change_gaps(skipping, book) == (
        "steps from drafted to adopted, which the change sequence "
        "does not allow",)
    assert [g.change_id for g in green_changes(book)] == [
        "change-held-change", "change-remeasured-change", "change-own-change"]
    index = derive_index(book)
    assert [e.check for e in index.changes] == EXAMPLE_CHECKS
    assert index.gaps == ("change-bare-change", "change-leaping-change")
    assert change_for_check(book, EXAMPLE_CHECK).change_id == (
        "change-held-change")
    assert change_for_check(book, "triple change") is None
    assert transition_breaks(book) == (
        "change-leaping-change: drafted > adopted",)
    assert [g.change_id for g in change_order(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "change-held-change") == EXAMPLE_TRACE
    assert trace_current(book, "change-held-change") is True
    assert trace_current(book, "change-remeasured-change") is False
    assert trace_for_change(
        book, "change-held-change").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_change(
        book, "change-held-change", "note").note_id == (
            "note-note-first")
    assert note_for_change(book, "change-nope") is None
    assert current_change(book).change_id == "change-bare-change"
    ledger = ledger_record(book)
    assert ledger["standings"] == [
        {"standing": "complete", "change_records": 3},
        {"standing": "open", "change_records": 2}]
    assert ledger["total"] == 5
    assert ledger["current_change"] == "change-bare-change"
    assert ledger["traces"] == [
        {"change_id": "change-held-change", "trace": "current"},
        {"change_id": "change-remeasured-change", "trace": "unheld"},
        {"change_id": "change-own-change", "trace": "unheld"},
        {"change_id": "change-bare-change", "trace": "unheld"},
        {"change_id": "change-leaping-change", "trace": "unheld"}]
    assert ledger["breaks"] == ["change-leaping-change: drafted > adopted"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 228
    assert citizen["next_slice"] == "M-229"
    assert citizen["m222_title"] == "Guarded self-modification"
    assert citizen["m222_part"] == 9
    assert citizen["m222_status"] == "done"

def test_change_record_round_trips():
    change = _change()
    assert validate_change(change) is change
    rebuilt = build_change(change.to_record())
    assert rebuilt == change
    assert rebuilt.item_id == "change-test"
    assert rebuilt.check == "adopted"
    record = change_record(change)
    assert record["type"] == "change_change"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert tool_record(ref)["type"] == "change_slice"
    assert tool_record(ref)["state"] == "live"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _change(checks=[])
    assert change_gaps(silent) == (
        "has passed through no step: the change has not started",)
    assert change_green(silent) is False
    walking = _change(checks=["proposed", "drafted"])
    assert change_gaps(walking) == (
        "has not proposed adopted: the change stands at drafted",)
    assert walking.check == "drafted"
    sideways = _change(checks=["drafted", "guarded", "tested", "adopted"])
    assert change_gaps(sideways) == (
        "opens at drafted, not at proposed: the change opens "
        "with the reflection",)
    repaired = _change(checks=["proposed", "drafted", "guarded", "tested", "proposed", "drafted", "guarded", "tested", "adopted"])
    assert change_gaps(repaired) == ()
    assert change_green(repaired) is True
    with pytest.raises(ValueError):
        _change(checks=[42])
    with pytest.raises(ValueError):
        _change(checks="inspect as a bare string")
    with pytest.raises(ValueError):
        _change(checks=["proposed", "polish"])
    with pytest.raises(ValueError):
        _change(claims=["weather"])
    with pytest.raises(ValueError):
        _change(claims="tool_ref")
    none_change = _change(checks=None, claims=None)
    assert none_change.checks == ()
    assert none_change.claims == ()

def test_change_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "changes", "coverage", "current_change",
                "ledger", "order"):
        fields = _change().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_change(fields)
    fields = _change().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_change(fields)


def test_change_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _change().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_change(fields)


def test_change_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _change(title="")
    with pytest.raises(ValueError):
        _change(tool_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "proposed > drafted > guarded > tested > adopted"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_changes_own_fields():
    change = _change(claims=["tool_ref"])
    assert plain_lines(change) == (
        "Change: A test change",
        "Tool: slice-test",
        "Check: adopted",
        "Claims: tool_ref")
    segment = segment_of(change)
    assert segment.startswith("change-test: A test change")
    assert "check: 'adopted'" in segment
    assert "gaps: none" in segment
    assert plain_words(change).startswith(
        "A test change - from slice-test")

def test_red_changes_stand_named_in_their_gaps():
    asking = _change(claims=["feeling", "tool_ref", "summary"])
    assert change_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert change_green(asking) is False
    skipping = _change(checks=["proposed", "drafted", "adopted"])
    assert change_gaps(skipping) == (
        "steps from drafted to adopted, which the change sequence "
        "does not allow",)
    book = _book(changes=[
        _change(),
        _change(change_id="change-skipping", seq=2,
             checks=["proposed", "drafted", "adopted"]),
    ])
    assert transition_breaks(book) == (
        "change-skipping: drafted > adopted",)
    assert current_change(book).change_id == "change-skipping"
    assert [g.change_id for g in change_order(book)] == [
        "change-test", "change-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "change_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "change_note"
    assert record["change_id"] == "change-test"
    assert view_plain_words(view) == "View view-test: shows all changes."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_changes_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.check for e in index.changes] == ["adopted"]
    assert index.changes[0] == IndexChange(
        check="adopted",
        change_id="change-test", title="A test change")
    assert index.gaps == ("change-hidden",)
    record = index_record(book)
    assert record["type"] == "change_index"
    assert record["gaps"] == ["change-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "change_book"

def test_check_target_reaches_its_change_and_an_unheld_target_reaches_nothing():
    book = load_change()
    assert change_for_check(book, "adopted").change_id == (
        "change-held-change")
    assert change_for_check(book, "") is None
    assert change_for_check(book, None) is None
    assert change_for_check(book, "not held at all") is None
    text = format_check(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_change()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Change note note change-held-change" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").change_id == "change-test"
    assert note_for_change(book, "change-test").note_id == "note-test"
    assert note_for_change(book, "change-test", "praise") is None
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
    row = build_row(None, _change(), book)
    assert row.standing == "complete"
    assert validate_row(row, _change(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_changes():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "change_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "adopted"
    empty_book = _book(changes=[_change(checks=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(ChangeVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_change()
    assert [g.change_id for g in shown_changes(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.change_id for g in shown_changes(book, "view-adopted")] == [
        "change-held-change", "change-remeasured-change", "change-own-change"]
    assert [g.change_id for g in changes_for_tool(
        book, "tool-m222-selfmod")] == [
            "change-own-change", "change-bare-change",
            "change-leaping-change"]
    assert changes_for_tool(book, "slice-nope") == ()
    assert current_change(_mixed_book()).change_id == "change-hidden"
    assert current_change(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "change-test") == (
        "proposed > drafted > guarded > tested > adopted")
    assert trace_current(stale, "change-test") is False
    assert ledger_record(stale)["traces"] == [
        {"change_id": "change-test", "trace": "stale"}]

def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(changes=[_change(), _change(seq=2)])
    with pytest.raises(ValueError):
        _book(changes=[_change(), _change(change_id="change-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(changes=[_change(tool_id="slice-nope")])
    with pytest.raises(ValueError):
        _book(slices=[_ref(), _ref(
            tool_id="slice-cold", seq=2, state="dormant")],
            changes=[_change(tool_id="slice-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(tool_id="slice-nope")])
    fields = {
        "schema": CHANGE_SCHEMA, "slice": "M-222",
        "self_modification": {"title": "A guarded book"},
        "slices": [_ref().to_record()],
        "change_records": [_change().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "adopted"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_change"] = "change-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_change")
    fields["trace"] = "change-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / CHANGE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "self_modification.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_change_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.change_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = ChangeRegistry()
    assert registry.title() is None
    registry.register_tool_ref(_ref())
    registry.register_change(_change())
    registry.register_view(_view())
    assert [g.change_id for g in registry.list_changes()] == ["change-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_change("change-test").title == "A test change"
    assert registry.get_slice("slice-test").state == "live"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("change-test").change_id == "change-test"
    with pytest.raises(ValueError):
        registry.register_change(_change(seq=9))
    with pytest.raises(ValueError):
        registry.register_change(_change(change_id="change-two"))
    with pytest.raises(KeyError):
        registry.get_change("change-nope")
    assert registry.book().title == "An unheld change book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = ChangeRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test change book"
    assert registry.title() == "A test change book"
    assert len(registry.list_changes()) == 2
    other = ChangeRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    change = _change()
    assert "A test change" in plain_words(change)
    assert panel_plain_words(_mixed_book()).startswith(
        "The change book holds 2 changes")
    assert verdict_plain_words(_mixed_book()) == (
        "The changes stand held: 1 of 2 shown changes stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green changes; red, "
        "named in its gaps: change-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_change(change)
    assert "Change: A test change" in text
    assert "stands complete" in text
    text = format_change(_change(checks=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Change Gate (M-222) - A test change book" in book_text
    assert "change-hidden" in format_book(_mixed_book(), "slice-test")
    assert "Change panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "adopted - A test change (change-test)" in index_text
    assert "change-hidden" in index_text
    screen = format_change_screen()
    assert "The Change Gate (M-222)" in screen
    assert "change-bare-change" in screen

def test_parse_args_well_and_loader_targets():
    assert parse_change_args("") == ("show", None)
    assert parse_change_args(None) == ("show", None)
    assert parse_change_args("show") == ("show", None)
    assert parse_change_args("change change-test") == (
        "change", "change-test")
    assert parse_change_args("check adopted") == (
        "check", "adopted")
    assert parse_change_args("tool slice-test") == (
        "tool", "slice-test")
    assert parse_change_args("view view-test") == ("view", "view-test")
    assert parse_change_args("note note-test") == ("note", "note-test")
    assert parse_change_args("index") == ("index", None)
    assert parse_change_args("panel") == ("panel", None)
    assert parse_change_args("verdict") == ("verdict", None)
    for bad in ("dance", "change", "check", "slice", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_change_args(bad)
    ledger = ledger_record()
    assert ledger["type"] == "change_well"
    assert ledger["total"] == 5
    assert ledger["current_change"] == "change-bare-change"
    book = load_change({
        "schema": CHANGE_SCHEMA, "slice": "M-222",
        "self_modification": {"title": "A guarded book"},
        "slices": [_ref().to_record()],
        "change_records": [_change().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, ChangeBook)
    assert book.title == "A guarded book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_change({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_change({"slice": "M-999"})
    built = build_change(
        change_id="change-kw", seq=3, tool_id="slice-test",
        title="Kw Change", checks=["proposed", "drafted", "guarded", "tested", "adopted"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="change-test")
    assert built.change_id == "change-kw"
    assert change_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-222 agent layer: the agent holds a change
# book for the session, changes and views are
# published as session news through the
# checkpoint target (ledger first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held changes, the ledger is derived from
# the held changes' completeness, the roadmap standing
# is tested from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no slice. This layer changes
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session ledger news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_CHANGE_EVENT_TYPES = (
    "change_change", "change_slice", "change_view",
    "change_panel", "change_verdict")


def _change_events(store, session_id, tool):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == tool]


def _write_selfmod_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / CHANGE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "self_modification.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestChangeAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.selfmod_status()
        assert status["change_records"] == []
        assert status["slices"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["selfmod_book"]["title"] == EXAMPLE_TITLE
        assert len(status["selfmod_book"]["slices"]) == 3
        assert len(status["selfmod_book"]["change_records"]) == 5
        assert len(status["selfmod_book"]["views"]) == 2
        assert len(status["selfmod_book"]["notes"]) == 2
        assert len(status["selfmod_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m221-tool"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["check"] for e in status["index"]["changes"]] == (
            EXAMPLE_CHECKS)
        assert status["index"]["gaps"] == [
            "change-bare-change", "change-leaping-change"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["ledger"]["total"] == 5
        assert status["ledger"]["current_change"] == "change-bare-change"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 228
        assert status["roadmap"]["next_slice"] == "M-229"
        assert status["roadmap"]["m222_title"] == "Guarded self-modification"
        assert "held as data alone" in status["rule"]
        assert "change-bare-change" in status["plain_words"]
        assert "The Change Gate (M-222)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._selfmod_registry()
        assert agent._selfmod_registry() is first
        assert agent._selfmod_store is first
        for name in ("selfmod_book", "selfmod_status", "selfmod_panel",
                     "selfmod_verdict", "selfmod_index", "report_selfmod"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_selfmod_registry", "selfmod_book", "selfmod_status",
            "get_selfmod_change", "get_selfmod_view", "get_selfmod_note",
            "changes_for_tool", "changes_green",
            "selfmod_panel", "selfmod_verdict", "selfmod_index",
            "register_selfmod_change", "register_selfmod_view",
            "view_selfmod", "register_selfmod_book",
            "record_selfmod_book", "report_selfmod",
            "_publish_selfmod_record", "_selfmod_screen",
            "_selfmod_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.selfmod_status()
        assert agent.get_selfmod_change(
            "change-held-change").title == "The held change"
        assert agent.get_selfmod_view(
            "view-changes").view_filter == "all"
        assert agent.get_selfmod_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.change_id for d in agent.changes_for_tool(
            "tool-m222-selfmod")] == [
            "change-own-change", "change-bare-change",
            "change-leaping-change"]
        assert [d.change_id for d in agent.changes_green()] == [
            "change-held-change", "change-remeasured-change", "change-own-change"]
        agent.selfmod_panel()
        agent.selfmod_verdict()
        agent.selfmod_index()
        agent.report_selfmod()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _CHANGE_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_selfmod_change("change-nope")
        with pytest.raises(KeyError):
            agent.get_selfmod_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_selfmod_note("note-nope")
        with pytest.raises(ValueError):
            agent.changes_for_tool("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_selfmod_change(_change())
        status = agent.selfmod_status()
        assert [d["change_id"] for d in status["change_records"]] == ["change-test"]
        assert status["book"]["title"] == "An unheld change book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["check"] for e in status["index"]["changes"]] == [
            "adopted"]
        assert status["first_note"] is None
        assert "change-test" in status["screen"]
    def test_held_change_never_falls_back_to_the_example(
            self, agent):
        agent.register_selfmod_change(_change())
        with pytest.raises(KeyError):
            agent.get_selfmod_change("change-held-change")
        with pytest.raises(KeyError):
            agent.get_selfmod_view("view-changes")
        with pytest.raises(KeyError):
            agent.get_selfmod_note("note-note-first")
        change = agent.get_selfmod_change("change-test")
        assert change.title == "A test change"
        assert agent.selfmod_book().title == (
            "An unheld change book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_selfmod_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.change_id == "change-held-change"
        status = agent.selfmod_status()
        assert status["index"]["gaps"] == [
            "change-bare-change", "change-leaping-change"]
        assert status["first_note"]["change_id"] == (
            "change-held-change")
        assert status["first_note"]["stance"] == "note"

class TestChangeAgentHolding:
    def test_register_change_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_selfmod_change(_change())
        assert result["change"]["change_id"] == "change-test"
        assert result["record_news"]["type"] == "change_change"
        assert "change-test" in result["screen"]
        events = _change_events(store, session_id, "change_change")
        assert len(events) == 1
        agent.close()

    def test_duplicate_change_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_selfmod_change(_change())
        with pytest.raises(ValueError):
            agent.register_selfmod_change(_change(seq=9))
        with pytest.raises(ValueError):
            agent.register_selfmod_change(_change(change_id="change-two"))
        events = _change_events(store, session_id, "change_change")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_selfmod_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_change_events(
            store, session_id, "change_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_selfmod_change(_change())
        result = agent.view_selfmod("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "change_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "adopted"
        assert len(_change_events(
            store, session_id, "change_view")) == 1
        assert len(_change_events(
            store, session_id, "change_panel")) == 1
        assert len(_change_events(
            store, session_id, "change_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_selfmod_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "change_slice", "change_change", "change_view"]
        assert len(_change_events(
            store, session_id, "change_change")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_selfmod_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "change_panel"
        assert result["index_record"]["gaps"] == [
            "change-bare-change", "change-leaping-change"]
        with pytest.raises(ValueError):
            agent.record_selfmod_book()
        assert len(_change_events(
            store, session_id, "change_slice")) == 3
        assert len(_change_events(
            store, session_id, "change_change")) == 5
        assert len(_change_events(
            store, session_id, "change_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_selfmod_book_file(tmp_path)
        book = load_change_file(path)
        result = agent.record_selfmod_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_toolrt_renders_example_then_held_book_only(self, agent):
        change = agent.report_selfmod()
        assert change["book"]["title"] == EXAMPLE_TITLE
        assert change["verdict"]["verdict"] == "held"
        assert change["index"]["gaps"] == [
            "change-bare-change", "change-leaping-change"]
        assert "change-held-change" in change["book_text"]
        assert "adopted - The held change (change-held-change)" in change["index_text"]
        agent.register_selfmod_change(_change())
        change = agent.report_selfmod()
        assert change["book"]["title"] == "An unheld change book"
        assert change["panel"] is None
        assert change["verdict"] is None

class TestChangeTerminalHeading:
    def test_show_change_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/selfmod")
        assert "The Change Gate (M-222)" in text
        _, _, text = _slash(agent, "/selfmod change change-held-change")
        assert "Change: The held change" in text
        _, _, text = _slash(
            agent, "/selfmod check adopted")
        assert "Change: The held change" in text
        _, _, text = _slash(agent, "/selfmod check triple change")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/selfmod tool tool-m222-selfmod")
        assert "change-bare-change" in text
        assert "change-held-change" not in text
        _, _, text = _slash(agent, "/selfmod view view-changes")
        assert "filter all" in text
        _, _, text = _slash(agent, "/selfmod note note-note-first")
        assert "Change note note change-held-change" in text
        _, _, text = _slash(agent, "/selfmod index")
        assert "Change index" in text
        assert "change-bare-change" in text
        _, _, text = _slash(agent, "/selfmod panel")
        assert "Change panel under view view-changes" in text
        _, _, text = _slash(agent, "/selfmod verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/selfmod [show|change <change-id>"
                "|check <check>|tool <tool-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/selfmod dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/selfmod change change-nope")
        assert "no change named" in text
@pytest.fixture()
def change_handler(agent, monkeypatch):
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


def _change_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestChangeCommand:
    def test_show_is_default(self, change_handler, agent):
        change_handler._handle_selfmod("")
        assert "The Change Gate (M-222)" in (
            _change_published_text(change_handler))

    def test_change_check_slice_view_note_index_panel_verdict(
            self, change_handler, agent):
        change_handler._handle_selfmod("change change-held-change")
        assert "Change: The held change" in _change_published_text(
            change_handler)
        change_handler._handle_selfmod(
            "check adopted")
        assert "Change: The held change" in _change_published_text(
            change_handler)
        change_handler._handle_selfmod("tool tool-m222-selfmod")
        assert "change-bare-change" in _change_published_text(
            change_handler)
        change_handler._handle_selfmod("view view-changes")
        assert "filter all" in _change_published_text(change_handler)
        change_handler._handle_selfmod("note note-note-first")
        assert "Change note note change-held-change" in (
            _change_published_text(change_handler))
        change_handler._handle_selfmod("index")
        assert "Change index" in _change_published_text(change_handler)
        change_handler._handle_selfmod("panel")
        assert "Change panel under view" in _change_published_text(
            change_handler)
        change_handler._handle_selfmod("verdict")
        assert "held" in _change_published_text(change_handler)
    def test_bad_grammar_is_published(
            self, change_handler, agent):
        change_handler._handle_selfmod("dance party")
        assert USAGE in _change_published_text(change_handler)
        change_handler._handle_selfmod("change change-nope")
        assert "no change named" in _change_published_text(
            change_handler)


class TestChatScreenRoutingChange:
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
        screen.handle_command("/selfmod panel", _FakeLog())
        assert calls == [("/selfmod", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/selfmod[/green] - show the Change gate (M-222)" in (
            text)
        assert ('"/selfmod": "Usage: /selfmod | '
                '/selfmod change <change-id>') in text

class TestChangeDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.selfmod_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-changes"
        verdict = agent.selfmod_verdict()
        assert verdict.verdict == "held"
        found = agent.selfmod_verdict("view-adopted")
        assert found.verdict == "adopted"
        assert found.green_shown == 3
        agent.register_selfmod_change(_change())
        with pytest.raises(ValueError):
            agent.selfmod_panel()
        with pytest.raises(ValueError):
            agent.selfmod_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_selfmod_change(_change(checks=[]))
        result = agent.view_selfmod("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.selfmod_index()
        assert [e["check"] for e in result["index"]["changes"]] == (
            EXAMPLE_CHECKS)
        assert result["index"]["gaps"] == [
            "change-bare-change", "change-leaping-change"]
        assert "adopted - The held change (change-held-change)" in (
            result["index_text"])
        change = agent.get_selfmod_change("change-leaping-change")
        assert change_gaps(change, agent.selfmod_book()) == (
            "steps from drafted to adopted, which the change sequence "
            "does not allow",)
        assert change_green(change, agent.selfmod_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _CHANGE_EVENT_TYPES] == []
        agent.close()
