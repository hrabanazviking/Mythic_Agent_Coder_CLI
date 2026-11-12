"""M-213 Retrospectives - pure-layer tests.

TIER: integration

The pure layer is the scribe, held as data: one
record per retro, held whole - the slice it
answers for, named by slice id, its title, the
steps it walked in walk order and the evidence
it carries, held by kind. The question walk is
explicit - named, reflected, written, distilled,
filed, with their legal steps held as data -
and a retro's standing is derived at call
time: a retro that opens anywhere but opened, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet reached filed stands open,
named in its gaps. A retro stands only for
an active slice: a retro naming no held
slice, or one that is not active, refuses by
name. The retro's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, board, trace, order and current
retro are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, distilled or
filed live. The shipped example book is held
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

from mythic_agent.core.retrospectives import (
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
    RETRO_RESOURCE,
    RETRO_RULE,
    RETRO_SCHEMA,
    RETRO_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    RetroRecord,
    IndexEntry,
    SliceRef,
    NoteRecord,
    RetroBook,
    RetroIndex,
    RetroPanel,
    RetroRegistry,
    RetroVerdict,
    RetroView,
    trace_for_retro,
    board_record,
    book_record,
    build_trace,
    build_book,
    build_retro,
    build_slice_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_retro,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    retro_for_check,
    retro_gaps,
    retro_order,
    retro_record,
    retro_green,
    retros_for_slice,
    first_note,
    format_book,
    format_retro,
    format_index,
    format_note,
    format_check,
    format_panel,
    format_retro_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    slice_record,
    load_retro,
    legal_step,
    load_retro_file,
    next_check,
    normalize_check,
    normalize_claim_kind,
    normalize_slice_state,
    normalize_stance,
    normalize_view_filter,
    note_for_retro,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_retro_args,
    green_retros,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_retros,
    validate_book,
    validate_retro,
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
EXAMPLE_TITLE = "Retrospectives at the M-212 slice boundary"
EXAMPLE_CHECKS = ["filed", "filed", "filed"]
EXAMPLE_RUN_IDS = (
    "retro-held-lesson", "retro-rechecked-lesson",
    "retro-own-lesson", "retro-bare-lesson",
    "retro-leaping-lesson")
EXAMPLE_TRACE = "opened > reflected > written > distilled > filed"


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
        "origin_session": "retro-test",
    }
    fields.update(overrides)
    return build_slice_ref(fields)


def _retro(**overrides):
    fields = {
        "retro_id": "retro-test",
        "seq": 1,
        "slice_id": "slice-test",
        "title": "A test retro",
        "checks": ["opened", "reflected", "written", "distilled", "filed"],
        "claims": [],
        "detail": "A test retro held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "retro-test",
    }
    fields.update(overrides)
    return build_retro(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "retro-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "retro_id": "retro-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "retro-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "retro_id": "retro-test",
        "trace": "opened > reflected > written > distilled > filed",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "retro-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(slices=None, retros=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": RETRO_SCHEMA,
        "slice": "M-213",
        "retrospectives": {"title": "A test retro book"},
        "slices": [item.to_record() for item in (
            slices if slices is not None else [_ref()])],
        "retros": [item.to_record() for item in (
            retros if retros is not None else [_retro()])],
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
    return _book(retros=[
        _retro(),
        _retro(retro_id="retro-hidden", seq=2,
               title="A hidden retro", checks=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_retro()
    assert book.title == EXAMPLE_TITLE
    assert book.retro_ids() == EXAMPLE_RUN_IDS
    assert book.slice_ids() == (
        "slice-m212-bugrule", "slice-m213-retro",
        "slice-m214-pattern")
    assert [v.view_id for v in book.views] == [
        "view-retros", "view-filed"]
    assert [m.retro_id for m in book.notes] == [
        "retro-held-lesson", "retro-bare-lesson"]
    assert [a.retro_id for a in book.traces] == ["retro-held-lesson"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m212-boundary"
    assert panel.as_of == "2026-11-10"
    assert [row.item_id for row in panel.rows] == list(book.retro_ids())
    derived = derive_panel(book, "view-retros")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-retros").verdict == "held"
    assert derive_verdict(book, "view-retros").green_shown == 3
    assert derive_verdict(book, "view-filed").verdict == "filed"
    assert derive_verdict(book, "view-filed").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / RETRO_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == RETRO_SCHEMA
    assert raw["slice"] == "M-213"
    assert "verdict" not in raw
    assert "retro_index" not in raw
    assert "board" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-213")]
    assert slice_.title == "Retrospectives"
    assert slice_.part == 9
    assert "at part and campaign close" in slice_.summary
    assert "the crew writes what was learned" in slice_.summary
    assert "Self-Improving" in slice_.summary
    assert "M-155" in slice_.summary
    assert RETRO_SLICE == "M-213"

def test_charter_rows_do_not_name_m213():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-213" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert COMPLETE_WORDS == ("complete", "open")
    assert CHECK_FIELDS == ("checks", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "complete", "open")
    assert VERDICT_WORDS == ("filed", "held", "blocked")
    assert SLICE_STATES == ("active", "queued")
    assert CHECKS == ("opened", "reflected", "written", "distilled", "filed")
    assert HELD_EVIDENCE == ("slice_ref", "lesson_ref", "test_record", "ledger_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["distilled"] == ("opened", "filed")
    assert TRANSITIONS["filed"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_CHECK == "filed"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_slice_state("ACTIVE") == "active"
    assert normalize_check("WRITTEN") == "written"
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
    assert legal_step("written", "distilled") is True
    assert legal_step("reflected", "filed") is False
    assert legal_step("filed", "opened") is False
    assert next_check("opened") == "reflected"
    assert next_check("written") == "distilled"
    assert next_check("distilled", failed=True) == "opened"
    assert next_check("distilled") == "filed"
    assert next_check("filed") is None
    assert "held as data alone" in RETRO_RULE
    assert "retro sequence" in RETRO_RULE
    assert "M-213" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /retrospectives")

def test_shipped_book_judged_honestly_as_data():
    book = load_retro()
    opening = book.retro_for("retro-held-lesson")
    assert retro_green(opening, book) is True
    assert retro_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Retro: The held lesson",
        "Slice: slice-m212-bugrule",
        "Check: filed",
        "Claims: slice_ref")
    asking = book.retro_for("retro-bare-lesson")
    assert retro_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert retro_green(asking, book) is False
    skipping = book.retro_for("retro-leaping-lesson")
    assert retro_gaps(skipping, book) == (
        "steps from reflected to filed, which the retro sequence "
        "does not allow",)
    assert [g.retro_id for g in green_retros(book)] == [
        "retro-held-lesson", "retro-rechecked-lesson", "retro-own-lesson"]
    index = derive_index(book)
    assert [e.check for e in index.entries] == EXAMPLE_CHECKS
    assert index.gaps == ("retro-bare-lesson", "retro-leaping-lesson")
    assert retro_for_check(book, EXAMPLE_CHECK).retro_id == (
        "retro-held-lesson")
    assert retro_for_check(book, "triple resume") is None
    assert transition_breaks(book) == (
        "retro-leaping-lesson: reflected > filed",)
    assert [g.retro_id for g in retro_order(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "retro-held-lesson") == EXAMPLE_TRACE
    assert trace_current(book, "retro-held-lesson") is True
    assert trace_current(book, "retro-rechecked-lesson") is False
    assert trace_for_retro(
        book, "retro-held-lesson").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_retro(
        book, "retro-held-lesson", "note").note_id == (
            "note-note-first")
    assert note_for_retro(book, "retro-nope") is None
    assert current_retro(book).retro_id == "retro-bare-lesson"
    board = board_record(book)
    assert board["standings"] == [
        {"standing": "complete", "retros": 3},
        {"standing": "open", "retros": 2}]
    assert board["total"] == 5
    assert board["current_retro"] == "retro-bare-lesson"
    assert board["traces"] == [
        {"retro_id": "retro-held-lesson", "trace": "current"},
        {"retro_id": "retro-rechecked-lesson", "trace": "unheld"},
        {"retro_id": "retro-own-lesson", "trace": "unheld"},
        {"retro_id": "retro-bare-lesson", "trace": "unheld"},
        {"retro_id": "retro-leaping-lesson", "trace": "unheld"}]
    assert board["breaks"] == ["retro-leaping-lesson: reflected > filed"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 236
    assert citizen["next_slice"] == "M-237"
    assert citizen["m213_title"] == "Retrospectives"
    assert citizen["m213_part"] == 9
    assert citizen["m213_status"] == "done"

def test_retro_record_round_trips():
    retro = _retro()
    assert validate_retro(retro) is retro
    rebuilt = build_retro(retro.to_record())
    assert rebuilt == retro
    assert rebuilt.item_id == "retro-test"
    assert rebuilt.check == "filed"
    record = retro_record(retro)
    assert record["type"] == "retro_retro"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert slice_record(ref)["type"] == "retro_slice"
    assert slice_record(ref)["state"] == "active"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _retro(checks=[])
    assert retro_gaps(silent) == (
        "has passed through no step: the retro has not started",)
    assert retro_green(silent) is False
    walking = _retro(checks=["opened", "reflected"])
    assert retro_gaps(walking) == (
        "has not reached filed: the retro stands at reflected",)
    assert walking.check == "reflected"
    sideways = _retro(checks=["reflected", "written", "distilled", "filed"])
    assert retro_gaps(sideways) == (
        "opens at reflected, not at opened: the retro opens "
        "with the reflection",)
    repaired = _retro(checks=["opened", "reflected", "written", "distilled", "opened", "reflected", "written", "distilled", "filed"])
    assert retro_gaps(repaired) == ()
    assert retro_green(repaired) is True
    with pytest.raises(ValueError):
        _retro(checks=[42])
    with pytest.raises(ValueError):
        _retro(checks="inspect as a bare string")
    with pytest.raises(ValueError):
        _retro(checks=["opened", "polish"])
    with pytest.raises(ValueError):
        _retro(claims=["weather"])
    with pytest.raises(ValueError):
        _retro(claims="slice_ref")
    none_retro = _retro(checks=None, claims=None)
    assert none_retro.checks == ()
    assert none_retro.claims == ()

def test_retro_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "entries", "coverage", "current_retro",
                "board", "order"):
        fields = _retro().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_retro(fields)
    fields = _retro().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_retro(fields)


def test_retro_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _retro().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_retro(fields)


def test_retro_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _retro(title="")
    with pytest.raises(ValueError):
        _retro(slice_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "opened > reflected > written > distilled > filed"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_retros_own_fields():
    retro = _retro(claims=["slice_ref"])
    assert plain_lines(retro) == (
        "Retro: A test retro",
        "Slice: slice-test",
        "Check: filed",
        "Claims: slice_ref")
    segment = segment_of(retro)
    assert segment.startswith("retro-test: A test retro")
    assert "check: 'filed'" in segment
    assert "gaps: none" in segment
    assert plain_words(retro).startswith(
        "A test retro - from slice-test")

def test_red_retros_stand_named_in_their_gaps():
    asking = _retro(claims=["feeling", "slice_ref", "summary"])
    assert retro_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert retro_green(asking) is False
    skipping = _retro(checks=["opened", "reflected", "filed"])
    assert retro_gaps(skipping) == (
        "steps from reflected to filed, which the retro sequence "
        "does not allow",)
    book = _book(retros=[
        _retro(),
        _retro(retro_id="retro-skipping", seq=2,
             checks=["opened", "reflected", "filed"]),
    ])
    assert transition_breaks(book) == (
        "retro-skipping: reflected > filed",)
    assert current_retro(book).retro_id == "retro-skipping"
    assert [g.retro_id for g in retro_order(book)] == [
        "retro-test", "retro-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "retro_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "retro_note"
    assert record["retro_id"] == "retro-test"
    assert view_plain_words(view) == "View view-test: shows all retros."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_retros_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.check for e in index.entries] == ["filed"]
    assert index.entries[0] == IndexEntry(
        check="filed",
        retro_id="retro-test", title="A test retro")
    assert index.gaps == ("retro-hidden",)
    record = index_record(book)
    assert record["type"] == "retro_index"
    assert record["gaps"] == ["retro-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "retro_book"

def test_check_target_reaches_its_retro_and_an_unheld_target_reaches_nothing():
    book = load_retro()
    assert retro_for_check(book, "filed").retro_id == (
        "retro-held-lesson")
    assert retro_for_check(book, "") is None
    assert retro_for_check(book, None) is None
    assert retro_for_check(book, "not held at all") is None
    text = format_check(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_retro()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Retro note note retro-held-lesson" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").retro_id == "retro-test"
    assert note_for_retro(book, "retro-test").note_id == "note-test"
    assert note_for_retro(book, "retro-test", "praise") is None
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
    row = build_row(None, _retro(), book)
    assert row.standing == "complete"
    assert validate_row(row, _retro(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_retros():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "retro_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "filed"
    empty_book = _book(retros=[_retro(checks=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(RetroVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_retro()
    assert [g.retro_id for g in shown_retros(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.retro_id for g in shown_retros(book, "view-filed")] == [
        "retro-held-lesson", "retro-rechecked-lesson", "retro-own-lesson"]
    assert [g.retro_id for g in retros_for_slice(
        book, "slice-m213-retro")] == [
            "retro-own-lesson", "retro-bare-lesson",
            "retro-leaping-lesson"]
    assert retros_for_slice(book, "slice-nope") == ()
    assert current_retro(_mixed_book()).retro_id == "retro-hidden"
    assert current_retro(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "retro-test") == (
        "opened > reflected > written > distilled > filed")
    assert trace_current(stale, "retro-test") is False
    assert board_record(stale)["traces"] == [
        {"retro_id": "retro-test", "trace": "stale"}]

def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(retros=[_retro(), _retro(seq=2)])
    with pytest.raises(ValueError):
        _book(retros=[_retro(), _retro(retro_id="retro-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(retros=[_retro(slice_id="slice-nope")])
    with pytest.raises(ValueError):
        _book(slices=[_ref(), _ref(
            slice_id="slice-cold", seq=2, state="queued")],
            retros=[_retro(slice_id="slice-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(slice_id="slice-nope")])
    fields = {
        "schema": RETRO_SCHEMA, "slice": "M-213",
        "retrospectives": {"title": "A written book"},
        "slices": [_ref().to_record()],
        "retros": [_retro().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "filed"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_retro"] = "retro-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_retro")
    fields["trace"] = "retro-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / RETRO_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "retrospectives.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_retro_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.retro_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = RetroRegistry()
    assert registry.title() is None
    registry.register_slice_ref(_ref())
    registry.register_retro(_retro())
    registry.register_view(_view())
    assert [g.retro_id for g in registry.list_retros()] == ["retro-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_retro("retro-test").title == "A test retro"
    assert registry.get_slice("slice-test").state == "active"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("retro-test").retro_id == "retro-test"
    with pytest.raises(ValueError):
        registry.register_retro(_retro(seq=9))
    with pytest.raises(ValueError):
        registry.register_retro(_retro(retro_id="retro-two"))
    with pytest.raises(KeyError):
        registry.get_retro("retro-nope")
    assert registry.book().title == "An unheld retro book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = RetroRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test retro book"
    assert registry.title() == "A test retro book"
    assert len(registry.list_retros()) == 2
    other = RetroRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    retro = _retro()
    assert "A test retro" in plain_words(retro)
    assert panel_plain_words(_mixed_book()).startswith(
        "The retro book holds 2 retros")
    assert verdict_plain_words(_mixed_book()) == (
        "The retros stand held: 1 of 2 shown retros stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green retros; red, "
        "named in its gaps: retro-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_retro(retro)
    assert "Retro: A test retro" in text
    assert "stands complete" in text
    text = format_retro(_retro(checks=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Retro Gate (M-213) - A test retro book" in book_text
    assert "retro-hidden" in format_book(_mixed_book(), "slice-test")
    assert "Retro panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "filed - A test retro (retro-test)" in index_text
    assert "retro-hidden" in index_text
    screen = format_retro_screen()
    assert "The Retro Gate (M-213)" in screen
    assert "retro-bare-lesson" in screen

def test_parse_args_board_and_loader_targets():
    assert parse_retro_args("") == ("show", None)
    assert parse_retro_args(None) == ("show", None)
    assert parse_retro_args("show") == ("show", None)
    assert parse_retro_args("retro retro-test") == (
        "retro", "retro-test")
    assert parse_retro_args("check filed") == (
        "check", "filed")
    assert parse_retro_args("slice slice-test") == (
        "slice", "slice-test")
    assert parse_retro_args("view view-test") == ("view", "view-test")
    assert parse_retro_args("note note-test") == ("note", "note-test")
    assert parse_retro_args("index") == ("index", None)
    assert parse_retro_args("panel") == ("panel", None)
    assert parse_retro_args("verdict") == ("verdict", None)
    for bad in ("dance", "retro", "check", "slice", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_retro_args(bad)
    board = board_record()
    assert board["type"] == "retro_board"
    assert board["total"] == 5
    assert board["current_retro"] == "retro-bare-lesson"
    book = load_retro({
        "schema": RETRO_SCHEMA, "slice": "M-213",
        "retrospectives": {"title": "A written book"},
        "slices": [_ref().to_record()],
        "retros": [_retro().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, RetroBook)
    assert book.title == "A written book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_retro({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_retro({"slice": "M-999"})
    built = build_retro(
        retro_id="retro-kw", seq=3, slice_id="slice-test",
        title="Kw Retro", checks=["opened", "reflected", "written", "distilled", "filed"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="retro-test")
    assert built.retro_id == "retro-kw"
    assert retro_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-213 agent layer: the agent holds a retro
# book for the session, retros and views are
# published as session news through the
# checkpoint target (journal first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held retros, the board is derived from
# the held retros' completeness, the roadmap standing
# is read from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no slice. This layer retros
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_RETRO_EVENT_TYPES = (
    "retro_retro", "retro_slice", "retro_view",
    "retro_panel", "retro_verdict")


def _retro_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_retro_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / RETRO_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "retrospectives.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestRetroAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.retro_status()
        assert status["retros"] == []
        assert status["slices"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["retro_book"]["title"] == EXAMPLE_TITLE
        assert len(status["retro_book"]["slices"]) == 3
        assert len(status["retro_book"]["retros"]) == 5
        assert len(status["retro_book"]["views"]) == 2
        assert len(status["retro_book"]["notes"]) == 2
        assert len(status["retro_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m212-boundary"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["check"] for e in status["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert status["index"]["gaps"] == [
            "retro-bare-lesson", "retro-leaping-lesson"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["board"]["total"] == 5
        assert status["board"]["current_retro"] == "retro-bare-lesson"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 236
        assert status["roadmap"]["next_slice"] == "M-237"
        assert status["roadmap"]["m213_title"] == "Retrospectives"
        assert "held as data alone" in status["rule"]
        assert "retro-bare-lesson" in status["plain_words"]
        assert "The Retro Gate (M-213)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._retro_registry()
        assert agent._retro_registry() is first
        assert agent._retro_store is first
        for name in ("retro_book", "retro_status", "retro_panel",
                     "retro_verdict", "retro_index", "report_retro"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_retro_registry", "retro_book", "retro_status",
            "get_retro_retro", "get_retro_view", "get_retro_note",
            "retro_retros_for_slice", "retro_retros_green",
            "retro_panel", "retro_verdict", "retro_index",
            "register_retro_retro", "register_retro_view",
            "view_retro", "register_retro_book",
            "record_retro_book", "report_retro",
            "_publish_retro_record", "_retro_screen",
            "_retro_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.retro_status()
        assert agent.get_retro_retro(
            "retro-held-lesson").title == "The held lesson"
        assert agent.get_retro_view(
            "view-retros").view_filter == "all"
        assert agent.get_retro_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.retro_id for d in agent.retro_retros_for_slice(
            "slice-m213-retro")] == [
            "retro-own-lesson", "retro-bare-lesson",
            "retro-leaping-lesson"]
        assert [d.retro_id for d in agent.retro_retros_green()] == [
            "retro-held-lesson", "retro-rechecked-lesson", "retro-own-lesson"]
        agent.retro_panel()
        agent.retro_verdict()
        agent.retro_index()
        agent.report_retro()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _RETRO_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_retro_retro("retro-nope")
        with pytest.raises(KeyError):
            agent.get_retro_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_retro_note("note-nope")
        with pytest.raises(ValueError):
            agent.retro_retros_for_slice("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_retro_retro(_retro())
        status = agent.retro_status()
        assert [d["retro_id"] for d in status["retros"]] == ["retro-test"]
        assert status["book"]["title"] == "An unheld retro book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["check"] for e in status["index"]["entries"]] == [
            "filed"]
        assert status["first_note"] is None
        assert "retro-test" in status["screen"]
    def test_held_retro_never_falls_back_to_the_example(
            self, agent):
        agent.register_retro_retro(_retro())
        with pytest.raises(KeyError):
            agent.get_retro_retro("retro-held-lesson")
        with pytest.raises(KeyError):
            agent.get_retro_view("view-retros")
        with pytest.raises(KeyError):
            agent.get_retro_note("note-note-first")
        retro = agent.get_retro_retro("retro-test")
        assert retro.title == "A test retro"
        assert agent.retro_book().title == (
            "An unheld retro book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_retro_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.retro_id == "retro-held-lesson"
        status = agent.retro_status()
        assert status["index"]["gaps"] == [
            "retro-bare-lesson", "retro-leaping-lesson"]
        assert status["first_note"]["retro_id"] == (
            "retro-held-lesson")
        assert status["first_note"]["stance"] == "note"

class TestRetroAgentHolding:
    def test_register_retro_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_retro_retro(_retro())
        assert result["retro"]["retro_id"] == "retro-test"
        assert result["record_news"]["type"] == "retro_retro"
        assert "retro-test" in result["screen"]
        events = _retro_events(store, session_id, "retro_retro")
        assert len(events) == 1
        agent.close()

    def test_duplicate_retro_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_retro_retro(_retro())
        with pytest.raises(ValueError):
            agent.register_retro_retro(_retro(seq=9))
        with pytest.raises(ValueError):
            agent.register_retro_retro(_retro(retro_id="retro-two"))
        events = _retro_events(store, session_id, "retro_retro")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_retro_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_retro_events(
            store, session_id, "retro_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_retro_retro(_retro())
        result = agent.view_retro("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "retro_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "filed"
        assert len(_retro_events(
            store, session_id, "retro_view")) == 1
        assert len(_retro_events(
            store, session_id, "retro_panel")) == 1
        assert len(_retro_events(
            store, session_id, "retro_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_retro_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "retro_slice", "retro_retro", "retro_view"]
        assert len(_retro_events(
            store, session_id, "retro_retro")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_retro_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "retro_panel"
        assert result["index_record"]["gaps"] == [
            "retro-bare-lesson", "retro-leaping-lesson"]
        with pytest.raises(ValueError):
            agent.record_retro_book()
        assert len(_retro_events(
            store, session_id, "retro_slice")) == 3
        assert len(_retro_events(
            store, session_id, "retro_retro")) == 5
        assert len(_retro_events(
            store, session_id, "retro_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_retro_book_file(tmp_path)
        book = load_retro_file(path)
        result = agent.record_retro_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_retro()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "held"
        assert report["index"]["gaps"] == [
            "retro-bare-lesson", "retro-leaping-lesson"]
        assert "retro-held-lesson" in report["book_text"]
        assert "filed - The held lesson (retro-held-lesson)" in report["index_text"]
        agent.register_retro_retro(_retro())
        report = agent.report_retro()
        assert report["book"]["title"] == "An unheld retro book"
        assert report["panel"] is None
        assert report["verdict"] is None

class TestRetroTerminalHeading:
    def test_show_retro_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/retrospectives")
        assert "The Retro Gate (M-213)" in text
        _, _, text = _slash(agent, "/retrospectives retro retro-held-lesson")
        assert "Retro: The held lesson" in text
        _, _, text = _slash(
            agent, "/retrospectives check filed")
        assert "Retro: The held lesson" in text
        _, _, text = _slash(agent, "/retrospectives check triple resume")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/retrospectives slice slice-m213-retro")
        assert "retro-bare-lesson" in text
        assert "retro-held-lesson" not in text
        _, _, text = _slash(agent, "/retrospectives view view-retros")
        assert "filter all" in text
        _, _, text = _slash(agent, "/retrospectives note note-note-first")
        assert "Retro note note retro-held-lesson" in text
        _, _, text = _slash(agent, "/retrospectives index")
        assert "Retro index" in text
        assert "retro-bare-lesson" in text
        _, _, text = _slash(agent, "/retrospectives panel")
        assert "Retro panel under view view-retros" in text
        _, _, text = _slash(agent, "/retrospectives verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/retrospectives [show|retro <retro-id>"
                "|check <check>|slice <slice-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/retrospectives dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/retrospectives retro retro-nope")
        assert "no retro named" in text
@pytest.fixture()
def retro_handler(agent, monkeypatch):
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


def _retro_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestRetroCommand:
    def test_show_is_default(self, retro_handler, agent):
        retro_handler._handle_retro("")
        assert "The Retro Gate (M-213)" in (
            _retro_published_text(retro_handler))

    def test_retro_check_slice_view_note_index_panel_verdict(
            self, retro_handler, agent):
        retro_handler._handle_retro("retro retro-held-lesson")
        assert "Retro: The held lesson" in _retro_published_text(
            retro_handler)
        retro_handler._handle_retro(
            "check filed")
        assert "Retro: The held lesson" in _retro_published_text(
            retro_handler)
        retro_handler._handle_retro("slice slice-m213-retro")
        assert "retro-bare-lesson" in _retro_published_text(
            retro_handler)
        retro_handler._handle_retro("view view-retros")
        assert "filter all" in _retro_published_text(retro_handler)
        retro_handler._handle_retro("note note-note-first")
        assert "Retro note note retro-held-lesson" in (
            _retro_published_text(retro_handler))
        retro_handler._handle_retro("index")
        assert "Retro index" in _retro_published_text(retro_handler)
        retro_handler._handle_retro("panel")
        assert "Retro panel under view" in _retro_published_text(
            retro_handler)
        retro_handler._handle_retro("verdict")
        assert "held" in _retro_published_text(retro_handler)
    def test_bad_grammar_is_published(
            self, retro_handler, agent):
        retro_handler._handle_retro("dance party")
        assert USAGE in _retro_published_text(retro_handler)
        retro_handler._handle_retro("retro retro-nope")
        assert "no retro named" in _retro_published_text(
            retro_handler)


class TestChatScreenRoutingRetro:
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
        screen.handle_command("/retrospectives panel", _FakeLog())
        assert calls == [("/retrospectives", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/retrospectives[/green] - show the Retro gate (M-213)" in (
            text)
        assert ('"/retrospectives": "Usage: /retrospectives | '
                '/retrospectives retro <retro-id>') in text

class TestRetroDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.retro_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-retros"
        verdict = agent.retro_verdict()
        assert verdict.verdict == "held"
        found = agent.retro_verdict("view-filed")
        assert found.verdict == "filed"
        assert found.green_shown == 3
        agent.register_retro_retro(_retro())
        with pytest.raises(ValueError):
            agent.retro_panel()
        with pytest.raises(ValueError):
            agent.retro_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_retro_retro(_retro(checks=[]))
        result = agent.view_retro("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.retro_index()
        assert [e["check"] for e in result["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert result["index"]["gaps"] == [
            "retro-bare-lesson", "retro-leaping-lesson"]
        assert "filed - The held lesson (retro-held-lesson)" in (
            result["index_text"])
        retro = agent.get_retro_retro("retro-leaping-lesson")
        assert retro_gaps(retro, agent.retro_book()) == (
            "steps from reflected to filed, which the retro sequence "
            "does not allow",)
        assert retro_green(retro, agent.retro_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _RETRO_EVENT_TYPES] == []
        agent.close()
