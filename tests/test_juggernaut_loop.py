"""M-204 The Juggernaut Loop As Runtime - pure-layer tests.

TIER: integration

The pure layer is the loop run, held as data: one
record per run, held whole - the slice it runs,
named by slice id, its title, the phases it
walked in walk order and the questions it asked,
held by kind. The state machine is explicit -
inspect, build, test, repair, continue, with its
legal steps held as data - and a run's standing
is derived at call time: a run that opens
anywhere but inspect, steps where the machine
does not allow, asks a file, framework, table or
function question the code can answer, or has
not yet reached continue stands unsound, named
in its gaps. A run stands only for an active
slice: a run naming no held slice, or one that
is not active, refuses by name. The run's trace
- its walked phases as one line - is derived at
call time, and a held trace record stands
current only while it agrees with the derived
trace. The index, panel, verdict, board, trace,
order and current run are derived at call time,
never stored where they could drift, and a
stored one refuses by name, as does a record
claiming a loop was actually run live, a slice
actually built, banked or pushed. The shipped
example book is held in a data file, and a
loader reads a book from any file. No charter
row names this slice: the M-171 TUI charter
binds Part VIII alone, and the M-005 method
charter names no slice row - its source note
names the whole Part IX range M-201-M-232 as
the part that executes it and names
YRSA_CODING_JUGGERNAUT itself among the six
plugs, and the tests pin both facts live. This
layer runs no loop, builds nothing, banks
nothing, pushes nothing and opens no network:
it holds loop runs as data and tells them.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.juggernaut_loop import (
    EXAMPLE_PHASE,
    CODE_QUESTIONS,
    HUMAN_QUESTIONS,
    INDEX_ACTION,
    PHASES,
    QUESTION_KINDS,
    TRANSITIONS,
    SLICE_STATES,
    PHASE_FIELDS,
    PLAIN_EXPLANATION,
    JUGGERNAUT_RESOURCE,
    JUGGERNAUT_RULE,
    JUGGERNAUT_SCHEMA,
    JUGGERNAUT_SLICE,
    SOUND_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    RunRecord,
    IndexEntry,
    SliceRef,
    NoteRecord,
    JuggernautBook,
    JuggernautIndex,
    JuggernautPanel,
    JuggernautRegistry,
    JuggernautVerdict,
    JuggernautView,
    trace_for_run,
    board_record,
    book_record,
    build_trace,
    build_book,
    build_run,
    build_slice_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_run,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    run_for_phase,
    run_gaps,
    run_order,
    run_record,
    run_sound,
    runs_for_slice,
    first_note,
    format_book,
    format_run,
    format_index,
    format_note,
    format_phase,
    format_panel,
    format_juggernaut_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    slice_record,
    load_juggernaut,
    legal_step,
    load_juggernaut_file,
    next_phase,
    normalize_phase,
    normalize_question_kind,
    normalize_slice_state,
    normalize_stance,
    normalize_view_filter,
    note_for_run,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_juggernaut_args,
    passing_runs,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_runs,
    validate_book,
    validate_run,
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
EXAMPLE_TITLE = "The Juggernaut loop at the M-203 slice boundary"
EXAMPLE_PHASES = ["continue", "continue", "continue"]
EXAMPLE_RUN_IDS = (
    "run-slicing-loop", "run-repair-loop",
    "run-runtime-loop", "run-asking-loop",
    "run-skipping-loop")
EXAMPLE_TRACE = "inspect > build > test > continue"


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
        "origin_session": "juggernaut-test",
    }
    fields.update(overrides)
    return build_slice_ref(fields)


def _run(**overrides):
    fields = {
        "run_id": "run-test",
        "seq": 1,
        "slice_id": "slice-test",
        "title": "A test run",
        "phases": ["inspect", "build", "test", "continue"],
        "questions": [],
        "detail": "A test run held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "juggernaut-test",
    }
    fields.update(overrides)
    return build_run(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "juggernaut-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "run_id": "run-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "juggernaut-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "run_id": "run-test",
        "trace": "inspect > build > test > continue",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "juggernaut-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(slices=None, runs=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": JUGGERNAUT_SCHEMA,
        "slice": "M-204",
        "juggernaut_loop": {"title": "A test juggernaut book"},
        "slices": [item.to_record() for item in (
            slices if slices is not None else [_ref()])],
        "runs": [item.to_record() for item in (
            runs if runs is not None else [_run()])],
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
    return _book(runs=[
        _run(),
        _run(run_id="run-hidden", seq=2,
               title="A hidden run", phases=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_juggernaut()
    assert book.title == EXAMPLE_TITLE
    assert book.run_ids() == EXAMPLE_RUN_IDS
    assert book.slice_ids() == (
        "slice-m203-slicing", "slice-m204-juggernaut",
        "slice-m205-gates")
    assert [v.view_id for v in book.views] == [
        "view-loop", "view-sound"]
    assert [m.run_id for m in book.notes] == [
        "run-slicing-loop", "run-asking-loop"]
    assert [a.run_id for a in book.traces] == ["run-slicing-loop"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m203-boundary"
    assert panel.as_of == "2026-11-10"
    assert [row.item_id for row in panel.rows] == list(book.run_ids())
    derived = derive_panel(book, "view-loop")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "sound": 3, "unsound": 2}
    assert derive_verdict(book, "view-loop").verdict == "strained"
    assert derive_verdict(book, "view-loop").passing_shown == 3
    assert derive_verdict(book, "view-sound").verdict == "open"
    assert derive_verdict(book, "view-sound").passing_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / JUGGERNAUT_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == JUGGERNAUT_SCHEMA
    assert raw["slice"] == "M-204"
    assert "verdict" not in raw
    assert "juggernaut_index" not in raw
    assert "board" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-204")]
    assert slice_.title == "The Juggernaut loop as runtime"
    assert slice_.part == 9
    assert "inspect" in slice_.summary
    assert "file/framework" in slice_.summary
    assert "state machine" in slice_.summary
    assert "visible" in slice_.summary
    assert JUGGERNAUT_SLICE == "M-204"

def test_charter_rows_do_not_name_m204():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-204" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert SOUND_WORDS == ("sound", "unsound")
    assert PHASE_FIELDS == ("phases", "questions")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "sound", "unsound")
    assert VERDICT_WORDS == ("open", "strained", "shut")
    assert SLICE_STATES == ("active", "queued")
    assert PHASES == ("inspect", "build", "test", "repair", "continue")
    assert HUMAN_QUESTIONS == ("meaning", "behaviour", "values", "direction")
    assert CODE_QUESTIONS == ("file", "framework", "table", "function")
    assert QUESTION_KINDS == HUMAN_QUESTIONS + CODE_QUESTIONS
    assert TRANSITIONS["test"] == ("repair", "continue")
    assert TRANSITIONS["continue"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_PHASE == "continue"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_slice_state("ACTIVE") == "active"
    assert normalize_phase("TEST") == "test"
    assert normalize_question_kind("FILE") == "file"
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    with pytest.raises(ValueError):
        normalize_slice_state("blessed")
    with pytest.raises(ValueError):
        normalize_phase("polish")
    with pytest.raises(ValueError):
        normalize_question_kind("weather")
    assert legal_step("test", "repair") is True
    assert legal_step("build", "continue") is False
    assert legal_step("continue", "inspect") is False
    assert next_phase("inspect") == "build"
    assert next_phase("test") == "continue"
    assert next_phase("test", failed=True) == "repair"
    assert next_phase("repair") == "test"
    assert next_phase("continue") is None
    assert "held as data alone" in JUGGERNAUT_RULE
    assert "state machine" in JUGGERNAUT_RULE
    assert "M-204" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /juggernaut")

def test_shipped_book_judged_honestly_as_data():
    book = load_juggernaut()
    opening = book.run_for("run-slicing-loop")
    assert run_sound(opening, book) is True
    assert run_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Run: The slicing engine run",
        "Slice: slice-m203-slicing",
        "Phase: continue",
        "Questions: meaning")
    asking = book.run_for("run-asking-loop")
    assert run_gaps(asking, book) == (
        "asked a file question the code can answer",)
    assert run_sound(asking, book) is False
    skipping = book.run_for("run-skipping-loop")
    assert run_gaps(skipping, book) == (
        "steps from build to continue, which the state "
        "machine does not allow",)
    assert [g.run_id for g in passing_runs(book)] == [
        "run-slicing-loop", "run-repair-loop", "run-runtime-loop"]
    index = derive_index(book)
    assert [e.phase for e in index.entries] == EXAMPLE_PHASES
    assert index.gaps == ("run-asking-loop", "run-skipping-loop")
    assert run_for_phase(book, EXAMPLE_PHASE).run_id == (
        "run-slicing-loop")
    assert run_for_phase(book, "triple resume") is None
    assert transition_breaks(book) == (
        "run-skipping-loop: build > continue",)
    assert [g.run_id for g in run_order(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "run-slicing-loop") == EXAMPLE_TRACE
    assert trace_current(book, "run-slicing-loop") is True
    assert trace_current(book, "run-repair-loop") is False
    assert trace_for_run(
        book, "run-slicing-loop").trace_id == "trace-open"
    assert first_note(book).note_id == "note-note-open"
    assert note_for_run(
        book, "run-slicing-loop", "note").note_id == (
            "note-note-open")
    assert note_for_run(book, "run-nope") is None
    assert current_run(book).run_id == "run-asking-loop"
    board = board_record(book)
    assert board["standings"] == [
        {"standing": "sound", "runs": 3},
        {"standing": "unsound", "runs": 2}]
    assert board["total"] == 5
    assert board["current_run"] == "run-asking-loop"
    assert board["traces"] == [
        {"run_id": "run-slicing-loop", "trace": "current"},
        {"run_id": "run-repair-loop", "trace": "unheld"},
        {"run_id": "run-runtime-loop", "trace": "unheld"},
        {"run_id": "run-asking-loop", "trace": "unheld"},
        {"run_id": "run-skipping-loop", "trace": "unheld"}]
    assert board["breaks"] == ["run-skipping-loop: build > continue"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 220
    assert citizen["next_slice"] == "M-221"
    assert citizen["m204_title"] == "The Juggernaut loop as runtime"
    assert citizen["m204_part"] == 9
    assert citizen["m204_status"] == "done"

def test_run_record_round_trips():
    run = _run()
    assert validate_run(run) is run
    rebuilt = build_run(run.to_record())
    assert rebuilt == run
    assert rebuilt.item_id == "run-test"
    assert rebuilt.phase == "continue"
    record = run_record(run)
    assert record["type"] == "juggernaut_run"
    assert record["sound"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert slice_record(ref)["type"] == "juggernaut_slice"
    assert slice_record(ref)["state"] == "active"

def test_the_walk_is_derived_from_the_phases_alone():
    silent = _run(phases=[])
    assert run_gaps(silent) == (
        "has passed through no phase: the loop has not started",)
    assert run_sound(silent) is False
    walking = _run(phases=["inspect", "build"])
    assert run_gaps(walking) == (
        "has not reached continue: the loop stands at build",)
    assert walking.phase == "build"
    sideways = _run(phases=["build", "test", "continue"])
    assert run_gaps(sideways) == (
        "opens at build, not at inspect: the loop opens "
        "by inspecting",)
    repaired = _run(phases=[
        "inspect", "build", "test", "repair", "test", "continue"])
    assert run_gaps(repaired) == ()
    assert run_sound(repaired) is True
    with pytest.raises(ValueError):
        _run(phases=[42])
    with pytest.raises(ValueError):
        _run(phases="inspect as a bare string")
    with pytest.raises(ValueError):
        _run(phases=["inspect", "polish"])
    with pytest.raises(ValueError):
        _run(questions=["weather"])
    with pytest.raises(ValueError):
        _run(questions="meaning")
    none_run = _run(phases=None, questions=None)
    assert none_run.phases == ()
    assert none_run.questions == ()

def test_run_refuses_stored_judgements():
    for key in ("standing", "sound", "gaps", "segment", "verdict",
                "index", "entries", "coverage", "current_run",
                "board", "order"):
        fields = _run().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_run(fields)
    fields = _run().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_run(fields)


def test_run_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _run().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_run(fields)


def test_run_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _run(title="")
    with pytest.raises(ValueError):
        _run(slice_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "inspect > build > test > continue"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_runs_own_fields():
    run = _run(questions=["meaning"])
    assert plain_lines(run) == (
        "Run: A test run",
        "Slice: slice-test",
        "Phase: continue",
        "Questions: meaning")
    segment = segment_of(run)
    assert segment.startswith("run-test: A test run")
    assert "phase: 'continue'" in segment
    assert "gaps: none" in segment
    assert plain_words(run).startswith(
        "A test run - from slice-test")

def test_unsound_runs_stand_named_in_their_gaps():
    asking = _run(questions=["file", "meaning", "function"])
    assert run_gaps(asking) == (
        "asked a file question the code can answer",
        "asked a function question the code can answer")
    assert run_sound(asking) is False
    skipping = _run(phases=["inspect", "build", "continue"])
    assert run_gaps(skipping) == (
        "steps from build to continue, which the state "
        "machine does not allow",)
    book = _book(runs=[
        _run(),
        _run(run_id="run-skipping", seq=2,
             phases=["inspect", "build", "continue"]),
    ])
    assert transition_breaks(book) == (
        "run-skipping: build > continue",)
    assert current_run(book).run_id == "run-skipping"
    assert [g.run_id for g in run_order(book)] == [
        "run-test", "run-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "juggernaut_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "juggernaut_note"
    assert record["run_id"] == "run-test"
    assert view_plain_words(view) == "View view-test: shows all runs."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_runs_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.phase for e in index.entries] == ["continue"]
    assert index.entries[0] == IndexEntry(
        phase="continue",
        run_id="run-test", title="A test run")
    assert index.gaps == ("run-hidden",)
    record = index_record(book)
    assert record["type"] == "juggernaut_index"
    assert record["gaps"] == ["run-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "juggernaut_book"

def test_phase_target_reaches_its_run_and_an_unheld_target_reaches_nothing():
    book = load_juggernaut()
    assert run_for_phase(book, "continue").run_id == (
        "run-slicing-loop")
    assert run_for_phase(book, "") is None
    assert run_for_phase(book, None) is None
    assert run_for_phase(book, "not held at all") is None
    text = format_phase(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_juggernaut()
    first = first_note(book)
    assert first.note_id == "note-note-open"
    assert first.stance == "note"
    text = format_note(first)
    assert "Juggernaut note note run-slicing-loop" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").run_id == "run-test"
    assert note_for_run(book, "run-test").note_id == "note-test"
    assert note_for_run(book, "run-test", "praise") is None
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
        "sound": 1, "unsound": 1}
    assert validate_panel(panel, book) is panel
    assert build_panel(panel.to_record(), book) == panel
    row = build_row(None, _run(), book)
    assert row.standing == "sound"
    assert validate_row(row, _run(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_runs():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "strained"
    assert verdict.passing_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "juggernaut_verdict"
    sound_book = _book(views=[_view(view_filter="sound")])
    assert derive_verdict(sound_book).verdict == "open"
    empty_book = _book(runs=[_run(phases=[])],
                       views=[_view(view_filter="sound")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "shut"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(JuggernautVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            passing_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_juggernaut()
    assert [g.run_id for g in shown_runs(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.run_id for g in shown_runs(book, "view-sound")] == [
        "run-slicing-loop", "run-repair-loop", "run-runtime-loop"]
    assert [g.run_id for g in runs_for_slice(
        book, "slice-m204-juggernaut")] == [
            "run-runtime-loop", "run-asking-loop",
            "run-skipping-loop"]
    assert runs_for_slice(book, "slice-nope") == ()
    assert current_run(_mixed_book()).run_id == "run-hidden"
    assert current_run(_book()) is None
    stale = _book(traces=[_trace(trace="inspect > build")])
    assert trace_of(stale, "run-test") == (
        "inspect > build > test > continue")
    assert trace_current(stale, "run-test") is False
    assert board_record(stale)["traces"] == [
        {"run_id": "run-test", "trace": "stale"}]

def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(runs=[_run(), _run(seq=2)])
    with pytest.raises(ValueError):
        _book(runs=[_run(), _run(run_id="run-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(runs=[_run(slice_id="slice-nope")])
    with pytest.raises(ValueError):
        _book(slices=[_ref(), _ref(
            slice_id="slice-cold", seq=2, state="queued")],
            runs=[_run(slice_id="slice-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(slice_id="slice-nope")])
    fields = {
        "schema": JUGGERNAUT_SCHEMA, "slice": "M-204",
        "juggernaut_loop": {"title": "A judged book"},
        "slices": [_ref().to_record()],
        "runs": [_run().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "open"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_run"] = "run-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_run")
    fields["trace"] = "run-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / JUGGERNAUT_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "juggernaut_loop.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_juggernaut_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.run_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = JuggernautRegistry()
    assert registry.title() is None
    registry.register_slice_ref(_ref())
    registry.register_run(_run())
    registry.register_view(_view())
    assert [g.run_id for g in registry.list_runs()] == ["run-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_run("run-test").title == "A test run"
    assert registry.get_slice("slice-test").state == "active"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("run-test").run_id == "run-test"
    with pytest.raises(ValueError):
        registry.register_run(_run(seq=9))
    with pytest.raises(ValueError):
        registry.register_run(_run(run_id="run-two"))
    with pytest.raises(KeyError):
        registry.get_run("run-nope")
    assert registry.book().title == "An unheld juggernaut book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = JuggernautRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test juggernaut book"
    assert registry.title() == "A test juggernaut book"
    assert len(registry.list_runs()) == 2
    other = JuggernautRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    run = _run()
    assert "A test run" in plain_words(run)
    assert panel_plain_words(_mixed_book()).startswith(
        "The juggernaut book holds 2 runs")
    assert verdict_plain_words(_mixed_book()) == (
        "The runs stand strained: 1 of 2 shown runs stand sound.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 sound runs; unsound, "
        "named in its gaps: run-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_run(run)
    assert "Run: A test run" in text
    assert "stands sound" in text
    text = format_run(_run(phases=[]))
    assert "stands unsound" in text
    assert "has passed through no phase" in text
    book_text = format_book(_mixed_book())
    assert "The Juggernaut Loop (M-204) - A test juggernaut book" in book_text
    assert "run-hidden" in format_book(_mixed_book(), "slice-test")
    assert "Juggernaut panel under view view-test" in format_panel(_mixed_book())
    assert "strained" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "continue - A test run (run-test)" in index_text
    assert "run-hidden" in index_text
    screen = format_juggernaut_screen()
    assert "The Juggernaut Loop (M-204)" in screen
    assert "run-asking-loop" in screen

def test_parse_args_board_and_loader_targets():
    assert parse_juggernaut_args("") == ("show", None)
    assert parse_juggernaut_args(None) == ("show", None)
    assert parse_juggernaut_args("show") == ("show", None)
    assert parse_juggernaut_args("run run-test") == (
        "run", "run-test")
    assert parse_juggernaut_args("phase continue") == (
        "phase", "continue")
    assert parse_juggernaut_args("slice slice-test") == (
        "slice", "slice-test")
    assert parse_juggernaut_args("view view-test") == ("view", "view-test")
    assert parse_juggernaut_args("note note-test") == ("note", "note-test")
    assert parse_juggernaut_args("index") == ("index", None)
    assert parse_juggernaut_args("panel") == ("panel", None)
    assert parse_juggernaut_args("verdict") == ("verdict", None)
    for bad in ("dance", "run", "phase", "slice", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_juggernaut_args(bad)
    board = board_record()
    assert board["type"] == "juggernaut_board"
    assert board["total"] == 5
    assert board["current_run"] == "run-asking-loop"
    book = load_juggernaut({
        "schema": JUGGERNAUT_SCHEMA, "slice": "M-204",
        "juggernaut_loop": {"title": "A judged book"},
        "slices": [_ref().to_record()],
        "runs": [_run().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, JuggernautBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_juggernaut({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_juggernaut({"slice": "M-999"})
    built = build_run(
        run_id="run-kw", seq=3, slice_id="slice-test",
        title="Kw Run", phases=["inspect", "build", "test", "continue"],
        questions=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="juggernaut-test")
    assert built.run_id == "run-kw"
    assert run_sound(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-204 agent layer: the agent holds a juggernaut
# book for the session, runs and views are
# published as session news through the
# checkpoint target (journal first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held runs, the board is derived from
# the held runs' soundness, the roadmap standing
# is read from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no slice. This layer runs
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_JUGGERNAUT_EVENT_TYPES = (
    "juggernaut_run", "juggernaut_slice", "juggernaut_view",
    "juggernaut_panel", "juggernaut_verdict")


def _juggernaut_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_juggernaut_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / JUGGERNAUT_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "juggernaut_loop.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestJuggernautAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.juggernaut_status()
        assert status["runs"] == []
        assert status["slices"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["juggernaut_book"]["title"] == EXAMPLE_TITLE
        assert len(status["juggernaut_book"]["slices"]) == 3
        assert len(status["juggernaut_book"]["runs"]) == 5
        assert len(status["juggernaut_book"]["views"]) == 2
        assert len(status["juggernaut_book"]["notes"]) == 2
        assert len(status["juggernaut_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m203-boundary"
        assert status["verdict"]["verdict"] == "strained"
        assert status["verdict"]["passing_shown"] == 3
        assert [e["phase"] for e in status["index"]["entries"]] == (
            EXAMPLE_PHASES)
        assert status["index"]["gaps"] == [
            "run-asking-loop", "run-skipping-loop"]
        assert status["first_note"]["note_id"] == "note-note-open"
        assert status["board"]["total"] == 5
        assert status["board"]["current_run"] == "run-asking-loop"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 220
        assert status["roadmap"]["next_slice"] == "M-221"
        assert status["roadmap"]["m204_title"] == "The Juggernaut loop as runtime"
        assert "held as data alone" in status["rule"]
        assert "run-asking-loop" in status["plain_words"]
        assert "The Juggernaut Loop (M-204)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._juggernaut_registry()
        assert agent._juggernaut_registry() is first
        assert agent._juggernaut_store is first
        for name in ("juggernaut_book", "juggernaut_status", "juggernaut_panel",
                     "juggernaut_verdict", "juggernaut_index", "report_juggernaut"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_juggernaut_registry", "juggernaut_book", "juggernaut_status",
            "get_juggernaut_run", "get_juggernaut_view", "get_juggernaut_note",
            "juggernaut_runs_for_slice", "juggernaut_runs_sound",
            "juggernaut_panel", "juggernaut_verdict", "juggernaut_index",
            "register_juggernaut_run", "register_juggernaut_view",
            "view_juggernaut", "register_juggernaut_book",
            "record_juggernaut_book", "report_juggernaut",
            "_publish_juggernaut_record", "_juggernaut_screen",
            "_juggernaut_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.juggernaut_status()
        assert agent.get_juggernaut_run(
            "run-slicing-loop").title == "The slicing engine run"
        assert agent.get_juggernaut_view(
            "view-loop").view_filter == "all"
        assert agent.get_juggernaut_note(
            "note-note-open").note_id == "note-note-open"
        assert [d.run_id for d in agent.juggernaut_runs_for_slice(
            "slice-m204-juggernaut")] == [
            "run-runtime-loop", "run-asking-loop",
            "run-skipping-loop"]
        assert [d.run_id for d in agent.juggernaut_runs_sound()] == [
            "run-slicing-loop", "run-repair-loop", "run-runtime-loop"]
        agent.juggernaut_panel()
        agent.juggernaut_verdict()
        agent.juggernaut_index()
        agent.report_juggernaut()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _JUGGERNAUT_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_juggernaut_run("run-nope")
        with pytest.raises(KeyError):
            agent.get_juggernaut_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_juggernaut_note("note-nope")
        with pytest.raises(ValueError):
            agent.juggernaut_runs_for_slice("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_juggernaut_run(_run())
        status = agent.juggernaut_status()
        assert [d["run_id"] for d in status["runs"]] == ["run-test"]
        assert status["book"]["title"] == "An unheld juggernaut book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["phase"] for e in status["index"]["entries"]] == [
            "continue"]
        assert status["first_note"] is None
        assert "run-test" in status["screen"]
    def test_held_run_never_falls_back_to_the_example(
            self, agent):
        agent.register_juggernaut_run(_run())
        with pytest.raises(KeyError):
            agent.get_juggernaut_run("run-slicing-loop")
        with pytest.raises(KeyError):
            agent.get_juggernaut_view("view-loop")
        with pytest.raises(KeyError):
            agent.get_juggernaut_note("note-note-open")
        run = agent.get_juggernaut_run("run-test")
        assert run.title == "A test run"
        assert agent.juggernaut_book().title == (
            "An unheld juggernaut book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_juggernaut_note("note-note-open")
        assert first.note_id == "note-note-open"
        assert first.run_id == "run-slicing-loop"
        status = agent.juggernaut_status()
        assert status["index"]["gaps"] == [
            "run-asking-loop", "run-skipping-loop"]
        assert status["first_note"]["run_id"] == (
            "run-slicing-loop")
        assert status["first_note"]["stance"] == "note"

class TestJuggernautAgentHolding:
    def test_register_run_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_juggernaut_run(_run())
        assert result["run"]["run_id"] == "run-test"
        assert result["record_news"]["type"] == "juggernaut_run"
        assert "run-test" in result["screen"]
        events = _juggernaut_events(store, session_id, "juggernaut_run")
        assert len(events) == 1
        agent.close()

    def test_duplicate_run_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_juggernaut_run(_run())
        with pytest.raises(ValueError):
            agent.register_juggernaut_run(_run(seq=9))
        with pytest.raises(ValueError):
            agent.register_juggernaut_run(_run(run_id="run-two"))
        events = _juggernaut_events(store, session_id, "juggernaut_run")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_juggernaut_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_juggernaut_events(
            store, session_id, "juggernaut_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_juggernaut_run(_run())
        result = agent.view_juggernaut("sound")
        assert result["view"]["view_filter"] == "sound"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "juggernaut_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "open"
        assert len(_juggernaut_events(
            store, session_id, "juggernaut_view")) == 1
        assert len(_juggernaut_events(
            store, session_id, "juggernaut_panel")) == 1
        assert len(_juggernaut_events(
            store, session_id, "juggernaut_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_juggernaut_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "juggernaut_slice", "juggernaut_run", "juggernaut_view"]
        assert len(_juggernaut_events(
            store, session_id, "juggernaut_run")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_juggernaut_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "juggernaut_panel"
        assert result["index_record"]["gaps"] == [
            "run-asking-loop", "run-skipping-loop"]
        with pytest.raises(ValueError):
            agent.record_juggernaut_book()
        assert len(_juggernaut_events(
            store, session_id, "juggernaut_slice")) == 3
        assert len(_juggernaut_events(
            store, session_id, "juggernaut_run")) == 5
        assert len(_juggernaut_events(
            store, session_id, "juggernaut_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_juggernaut_book_file(tmp_path)
        book = load_juggernaut_file(path)
        result = agent.record_juggernaut_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_juggernaut()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "strained"
        assert report["index"]["gaps"] == [
            "run-asking-loop", "run-skipping-loop"]
        assert "run-slicing-loop" in report["book_text"]
        assert "continue - The slicing engine run (run-slicing-loop)" in report["index_text"]
        agent.register_juggernaut_run(_run())
        report = agent.report_juggernaut()
        assert report["book"]["title"] == "An unheld juggernaut book"
        assert report["panel"] is None
        assert report["verdict"] is None

class TestJuggernautTerminalHeading:
    def test_show_run_phase_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/juggernaut")
        assert "The Juggernaut Loop (M-204)" in text
        _, _, text = _slash(agent, "/juggernaut run run-slicing-loop")
        assert "Run: The slicing engine run" in text
        _, _, text = _slash(
            agent, "/juggernaut phase continue")
        assert "Run: The slicing engine run" in text
        _, _, text = _slash(agent, "/juggernaut phase triple resume")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/juggernaut slice slice-m204-juggernaut")
        assert "run-asking-loop" in text
        assert "run-slicing-loop" not in text
        _, _, text = _slash(agent, "/juggernaut view view-loop")
        assert "filter all" in text
        _, _, text = _slash(agent, "/juggernaut note note-note-open")
        assert "Juggernaut note note run-slicing-loop" in text
        _, _, text = _slash(agent, "/juggernaut index")
        assert "Juggernaut index" in text
        assert "run-asking-loop" in text
        _, _, text = _slash(agent, "/juggernaut panel")
        assert "Juggernaut panel under view view-loop" in text
        _, _, text = _slash(agent, "/juggernaut verdict")
        assert "strained" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/juggernaut [show|run <run-id>"
                "|phase <phase>|slice <slice-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/juggernaut dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/juggernaut run run-nope")
        assert "no run named" in text
@pytest.fixture()
def juggernaut_handler(agent, monkeypatch):
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


def _juggernaut_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestJuggernautCommand:
    def test_show_is_default(self, juggernaut_handler, agent):
        juggernaut_handler._handle_juggernaut("")
        assert "The Juggernaut Loop (M-204)" in (
            _juggernaut_published_text(juggernaut_handler))

    def test_run_phase_slice_view_note_index_panel_verdict(
            self, juggernaut_handler, agent):
        juggernaut_handler._handle_juggernaut("run run-slicing-loop")
        assert "Run: The slicing engine run" in _juggernaut_published_text(
            juggernaut_handler)
        juggernaut_handler._handle_juggernaut(
            "phase continue")
        assert "Run: The slicing engine run" in _juggernaut_published_text(
            juggernaut_handler)
        juggernaut_handler._handle_juggernaut("slice slice-m204-juggernaut")
        assert "run-asking-loop" in _juggernaut_published_text(
            juggernaut_handler)
        juggernaut_handler._handle_juggernaut("view view-loop")
        assert "filter all" in _juggernaut_published_text(juggernaut_handler)
        juggernaut_handler._handle_juggernaut("note note-note-open")
        assert "Juggernaut note note run-slicing-loop" in (
            _juggernaut_published_text(juggernaut_handler))
        juggernaut_handler._handle_juggernaut("index")
        assert "Juggernaut index" in _juggernaut_published_text(juggernaut_handler)
        juggernaut_handler._handle_juggernaut("panel")
        assert "Juggernaut panel under view" in _juggernaut_published_text(
            juggernaut_handler)
        juggernaut_handler._handle_juggernaut("verdict")
        assert "strained" in _juggernaut_published_text(juggernaut_handler)
    def test_bad_grammar_is_published(
            self, juggernaut_handler, agent):
        juggernaut_handler._handle_juggernaut("dance party")
        assert USAGE in _juggernaut_published_text(juggernaut_handler)
        juggernaut_handler._handle_juggernaut("run run-nope")
        assert "no run named" in _juggernaut_published_text(
            juggernaut_handler)


class TestChatScreenRoutingJuggernaut:
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
        screen.handle_command("/juggernaut panel", _FakeLog())
        assert calls == [("/juggernaut", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/juggernaut[/green] - show the Juggernaut loop (M-204)" in (
            text)
        assert ('"/juggernaut": "Usage: /juggernaut | '
                '/juggernaut run <run-id>') in text

class TestJuggernautDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.juggernaut_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-loop"
        verdict = agent.juggernaut_verdict()
        assert verdict.verdict == "strained"
        found = agent.juggernaut_verdict("view-sound")
        assert found.verdict == "open"
        assert found.passing_shown == 3
        agent.register_juggernaut_run(_run())
        with pytest.raises(ValueError):
            agent.juggernaut_panel()
        with pytest.raises(ValueError):
            agent.juggernaut_verdict()

    def test_view_target_over_an_unshown_filter_is_shut(self, agent):
        agent.register_juggernaut_run(_run(phases=[]))
        result = agent.view_juggernaut("sound")
        assert result["verdict_record"]["verdict"] == "shut"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.juggernaut_index()
        assert [e["phase"] for e in result["index"]["entries"]] == (
            EXAMPLE_PHASES)
        assert result["index"]["gaps"] == [
            "run-asking-loop", "run-skipping-loop"]
        assert "continue - The slicing engine run (run-slicing-loop)" in (
            result["index_text"])
        run = agent.get_juggernaut_run("run-skipping-loop")
        assert run_gaps(run, agent.juggernaut_book()) == (
            "steps from build to continue, which the state "
            "machine does not allow",)
        assert run_sound(run, agent.juggernaut_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _JUGGERNAUT_EVENT_TYPES] == []
        agent.close()
