"""M-239 Cross-app method - pure-layer tests.

TIER: integration

The pure layer is the tracker, held as data: one
record per companion, held whole - the editor it
answers for, linked by editor id, its title, the
steps it walked in walk companion and the evidence
it carries, held by editor. The question walk is
explicit - linked, probed, opened, shared,
held, with their legal steps held as data -
and a companion's standing is derived at call
time: a companion that opens anywhere but linked, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet linked held stands open,
linked in its gaps. A companion stands only for
an active editor: a companion naming no held
editor, or one that is not active, refuses by
name. The companion's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, ledger, trace, companion and current
companion are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, shared or
held live. The shipped example book is held
in a data file, and a loader reads a book from
any file. No charter row names this editor: the
M-171 TUI charter binds Part VIII alone, and the
M-005 method charter names the whole of Part X
as the part that executes it, both pinned live
below.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.vscode_companions import (
    EXAMPLE_STAGE,
    BARE_CLAIMS,
    HELD_EVIDENCE,
    INDEX_ACTION,
    STAGES,
    CLAIM_KINDS,
    TRANSITIONS,
    EDITOR_STATES,
    STAGE_FIELDS,
    PLAIN_EXPLANATION,
    COMPANION_RESOURCE,
    COMPANION_RULE,
    COMPANION_SCHEMA,
    COMPANION_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    CompanionRecord,
    IndexCompanion,
    EditorRef,
    NoteRecord,
    CompanionBook,
    CompanionIndex,
    CompanionPanel,
    CompanionRegistry,
    CompanionVerdict,
    CompanionView,
    trace_for_companion,
    ledger_record,
    book_record,
    build_trace,
    build_book,
    build_companion,
    build_editor_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_companion,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    companion_for_check,
    companion_gaps,
    companion_companion,
    companion_record,
    companion_green,
    companions_for_editor,
    first_note,
    format_book,
    format_companion,
    format_index,
    format_note,
    format_stage,
    format_panel,
    format_companion_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    editor_record,
    load_companion,
    legal_step,
    load_companion_file,
    next_stage,
    normalize_stage,
    normalize_claim_kind,
    normalize_editor_state,
    normalize_stance,
    normalize_view_filter,
    note_for_companion,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_companion_args,
    green_companions,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_companions,
    validate_book,
    validate_companion,
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
EXAMPLE_TITLE = "VS Code companions at the M-239 slice run"
EXAMPLE_STAGES = ["held", "held", "held"]
EXAMPLE_RUN_IDS = (
    "companion-held-companion", "companion-retried-companion",
    "companion-own-companion", "companion-bare-companion",
    "companion-leaping-companion")
EXAMPLE_TRACE = "linked > probed > opened > shared > held"


def _ref(**overrides):
    fields = {
        "editor_id": "editor-test",
        "seq": 1,
        "title": "A test editor",
        "state": "live",
        "detail": "A test editor reference held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "companion-test",
    }
    fields.update(overrides)
    return build_editor_ref(fields)


def _companion(**overrides):
    fields = {
        "companion_id": "companion-test",
        "seq": 1,
        "editor_id": "editor-test",
        "title": "A test companion",
        "stages": ["linked", "probed", "opened", "shared", "held"],
        "claims": [],
        "detail": "A test companion held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "companion-test",
    }
    fields.update(overrides)
    return build_companion(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "companion-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "companion_id": "companion-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "companion-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "companion_id": "companion-test",
        "trace": "linked > probed > opened > shared > held",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "companion-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(editors=None, companions=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": COMPANION_SCHEMA,
        "editor": "M-239",
        "vscode_companions": {"title": "A test companion book"},
        "editors": [item.to_record() for item in (
            editors if editors is not None else [_ref()])],
        "companion_records": [item.to_record() for item in (
            companions if companions is not None else [_companion()])],
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
    return _book(companions=[
        _companion(),
        _companion(companion_id="companion-hidden", seq=2,
               title="A hidden companion", stages=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_companion()
    assert book.title == EXAMPLE_TITLE
    assert book.companion_ids() == EXAMPLE_RUN_IDS
    assert book.editor_ids() == (
        "editor-vscode", "editor-insiders",
        "editor-vscodium")
    assert [v.view_id for v in book.views] == [
        "view-companions", "view-held"]
    assert [m.companion_id for m in book.notes] == [
        "companion-held-companion", "companion-bare-companion"]
    assert [a.companion_id for a in book.traces] == ["companion-held-companion"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-editor"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.companion_ids())
    derived = derive_panel(book, "view-companions")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-companions").verdict == "held"
    assert derive_verdict(book, "view-companions").green_shown == 3
    assert derive_verdict(book, "view-held").verdict == "held"
    assert derive_verdict(book, "view-held").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / COMPANION_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == COMPANION_SCHEMA
    assert raw["editor"] == "M-239"
    assert "verdict" not in raw
    assert "companion_index" not in raw
    assert "ledger" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-239")]
    assert slice_.title == "IDE companions I — VS Code family"
    assert slice_.part == 10
    assert "open-file-at-line, selection-into-context" in slice_.summary
    assert "diff-in-editor bridges" in slice_.summary
    assert COMPANION_SLICE == "M-239"

def test_charter_rows_do_not_name_m239():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-239" not in owners
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
    assert EDITOR_STATES == ("live", "dormant")
    assert STAGES == ("linked", "probed", "opened", "shared", "held")
    assert HELD_EVIDENCE == ("file_ref", "line_ref", "selection_ref", "context_ref", "diff_ref", "connection_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["shared"] == ("linked", "held")
    assert TRANSITIONS["held"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_STAGE == "held"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_editor_state("LIVE") == "live"
    assert normalize_stage("OPENED") == "opened"
    assert normalize_claim_kind("FEELING") == "feeling"
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    with pytest.raises(ValueError):
        normalize_editor_state("blessed")
    with pytest.raises(ValueError):
        normalize_stage("polish")
    with pytest.raises(ValueError):
        normalize_claim_kind("weather")
    assert legal_step("opened", "shared") is True
    assert legal_step("probed", "held") is False
    assert legal_step("held", "linked") is False
    assert next_stage("linked") == "probed"
    assert next_stage("opened") == "shared"
    assert next_stage("shared", failed=True) == "linked"
    assert next_stage("shared") == "held"
    assert next_stage("held") is None
    assert "held as data alone" in COMPANION_RULE
    assert "companion sequence" in COMPANION_RULE
    assert "M-239" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /vscodecompanions")

def test_shipped_book_judged_honestly_as_data():
    book = load_companion()
    opening = book.companion_for("companion-held-companion")
    assert companion_green(opening, book) is True
    assert companion_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Companion: The held companion",
        "Editor: editor-vscode",
        "Stage: held",
        "Claims: file_ref")
    asking = book.companion_for("companion-bare-companion")
    assert companion_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert companion_green(asking, book) is False
    skipping = book.companion_for("companion-leaping-companion")
    assert companion_gaps(skipping, book) == (
        "steps from probed to held, which the companion sequence "
        "does not allow",)
    assert [g.companion_id for g in green_companions(book)] == [
        "companion-held-companion", "companion-retried-companion", "companion-own-companion"]
    index = derive_index(book)
    assert [e.stage for e in index.companions] == EXAMPLE_STAGES
    assert index.gaps == ("companion-bare-companion", "companion-leaping-companion")
    assert companion_for_check(book, EXAMPLE_STAGE).companion_id == (
        "companion-held-companion")
    assert companion_for_check(book, "triple companion") is None
    assert transition_breaks(book) == (
        "companion-leaping-companion: probed > held",)
    assert [g.companion_id for g in companion_companion(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "companion-held-companion") == EXAMPLE_TRACE
    assert trace_current(book, "companion-held-companion") is True
    assert trace_current(book, "companion-retried-companion") is False
    assert trace_for_companion(
        book, "companion-held-companion").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_companion(
        book, "companion-held-companion", "note").note_id == (
            "note-note-first")
    assert note_for_companion(book, "companion-nope") is None
    assert current_companion(book).companion_id == "companion-bare-companion"
    ledger = ledger_record(book)
    assert ledger["standings"] == [
        {"standing": "complete", "companion_records": 3},
        {"standing": "open", "companion_records": 2}]
    assert ledger["total"] == 5
    assert ledger["current_companion"] == "companion-bare-companion"
    assert ledger["traces"] == [
        {"companion_id": "companion-held-companion", "trace": "current"},
        {"companion_id": "companion-retried-companion", "trace": "unheld"},
        {"companion_id": "companion-own-companion", "trace": "unheld"},
        {"companion_id": "companion-bare-companion", "trace": "unheld"},
        {"companion_id": "companion-leaping-companion", "trace": "unheld"}]
    assert ledger["breaks"] == ["companion-leaping-companion: probed > held"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 255
    assert citizen["next_slice"] == "M-256"
    assert citizen["m239_title"] == "IDE companions I — VS Code family"
    assert citizen["m239_part"] == 10
    assert citizen["m239_status"] == "done"

def test_companion_record_round_trips():
    companion = _companion()
    assert validate_companion(companion) is companion
    rebuilt = build_companion(companion.to_record())
    assert rebuilt == companion
    assert rebuilt.item_id == "companion-test"
    assert rebuilt.stage == "held"
    record = companion_record(companion)
    assert record["type"] == "companion_companion"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert editor_record(ref)["type"] == "companion_run"
    assert editor_record(ref)["state"] == "live"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _companion(stages=[])
    assert companion_gaps(silent) == (
        "has passed through no step: the companion has not started",)
    assert companion_green(silent) is False
    walking = _companion(stages=["linked", "probed"])
    assert companion_gaps(walking) == (
        "has not reached held: the companion stands at probed",)
    assert walking.stage == "probed"
    sideways = _companion(stages=["probed", "opened", "shared", "held"])
    assert companion_gaps(sideways) == (
        "opens at probed, not at linked: the companion opens "
        "with the reflection",)
    repaired = _companion(stages=["linked", "probed", "opened", "shared", "linked", "probed", "opened", "shared", "held"])
    assert companion_gaps(repaired) == ()
    assert companion_green(repaired) is True
    with pytest.raises(ValueError):
        _companion(stages=[42])
    with pytest.raises(ValueError):
        _companion(stages="inspect as a bare string")
    with pytest.raises(ValueError):
        _companion(stages=["linked", "polish"])
    with pytest.raises(ValueError):
        _companion(claims=["weather"])
    with pytest.raises(ValueError):
        _companion(claims="file_ref")
    none_companion = _companion(stages=None, claims=None)
    assert none_companion.stages == ()
    assert none_companion.claims == ()

def test_connection_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "companions", "coverage", "current_companion",
                "ledger", "companion"):
        fields = _companion().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_companion(fields)
    fields = _companion().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_companion(fields)


def test_connection_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _companion().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_companion(fields)


def test_companion_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _companion(title="")
    with pytest.raises(ValueError):
        _companion(editor_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "linked > probed > opened > shared > held"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_companions_own_fields():
    companion = _companion(claims=["file_ref"])
    assert plain_lines(companion) == (
        "Companion: A test companion",
        "Editor: editor-test",
        "Stage: held",
        "Claims: file_ref")
    segment = segment_of(companion)
    assert segment.startswith("companion-test: A test companion")
    assert "stage: 'held'" in segment
    assert "gaps: none" in segment
    assert plain_words(companion).startswith(
        "A test companion - from editor-test")

def test_red_companions_stand_named_in_their_gaps():
    asking = _companion(claims=["feeling", "file_ref", "summary"])
    assert companion_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert companion_green(asking) is False
    skipping = _companion(stages=["linked", "probed", "held"])
    assert companion_gaps(skipping) == (
        "steps from probed to held, which the companion sequence "
        "does not allow",)
    book = _book(companions=[
        _companion(),
        _companion(companion_id="companion-skipping", seq=2,
             stages=["linked", "probed", "held"]),
    ])
    assert transition_breaks(book) == (
        "companion-skipping: probed > held",)
    assert current_companion(book).companion_id == "companion-skipping"
    assert [g.companion_id for g in companion_companion(book)] == [
        "companion-test", "companion-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "companion_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "companion_note"
    assert record["companion_id"] == "companion-test"
    assert view_plain_words(view) == "View view-test: shows all companions."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_companions_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.stage for e in index.companions] == ["held"]
    assert index.companions[0] == IndexCompanion(
        stage="held",
        companion_id="companion-test", title="A test companion")
    assert index.gaps == ("companion-hidden",)
    record = index_record(book)
    assert record["type"] == "companion_index"
    assert record["gaps"] == ["companion-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "companion_book"

def test_check_target_reaches_its_companion_and_an_unheld_target_reaches_nothing():
    book = load_companion()
    assert companion_for_check(book, "held").companion_id == (
        "companion-held-companion")
    assert companion_for_check(book, "") is None
    assert companion_for_check(book, None) is None
    assert companion_for_check(book, "not held at all") is None
    text = format_stage(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_companion()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Companion note note companion-held-companion" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").companion_id == "companion-test"
    assert note_for_companion(book, "companion-test").note_id == "note-test"
    assert note_for_companion(book, "companion-test", "praise") is None
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
    row = build_row(None, _companion(), book)
    assert row.standing == "complete"
    assert validate_row(row, _companion(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_companions():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "companion_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "held"
    empty_book = _book(companions=[_companion(stages=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(CompanionVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_companions():
    book = load_companion()
    assert [g.companion_id for g in shown_companions(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.companion_id for g in shown_companions(book, "view-held")] == [
        "companion-held-companion", "companion-retried-companion", "companion-own-companion"]
    assert [g.companion_id for g in companions_for_editor(
        book, "editor-insiders")] == [
            "companion-own-companion", "companion-bare-companion",
            "companion-leaping-companion"]
    assert companions_for_editor(book, "editor-nope") == ()
    assert current_companion(_mixed_book()).companion_id == "companion-hidden"
    assert current_companion(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "companion-test") == (
        "linked > probed > opened > shared > held")
    assert trace_current(stale, "companion-test") is False
    assert ledger_record(stale)["traces"] == [
        {"companion_id": "companion-test", "trace": "stale"}]

def test_line_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(companions=[_companion(), _companion(seq=2)])
    with pytest.raises(ValueError):
        _book(companions=[_companion(), _companion(companion_id="companion-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(companions=[_companion(editor_id="editor-nope")])
    with pytest.raises(ValueError):
        _book(editors=[_ref(), _ref(
            editor_id="editor-cold", seq=2, state="dormant")],
            companions=[_companion(editor_id="editor-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(editor_id="editor-nope")])
    fields = {
        "schema": COMPANION_SCHEMA, "editor": "M-239",
        "vscode_companions": {"title": "A opened book"},
        "editors": [_ref().to_record()],
        "companion_records": [_companion().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "held"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_companion"] = "companion-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_companion")
    fields["trace"] = "companion-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / COMPANION_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "vscode_companions.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_companion_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.companion_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = CompanionRegistry()
    assert registry.title() is None
    registry.register_editor_ref(_ref())
    registry.register_companion(_companion())
    registry.register_view(_view())
    assert [g.companion_id for g in registry.list_companions()] == ["companion-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_companion("companion-test").title == "A test companion"
    assert registry.get_slice("editor-test").state == "live"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("companion-test").companion_id == "companion-test"
    with pytest.raises(ValueError):
        registry.register_companion(_companion(seq=9))
    with pytest.raises(ValueError):
        registry.register_companion(_companion(companion_id="companion-two"))
    with pytest.raises(KeyError):
        registry.get_companion("companion-nope")
    assert registry.book().title == "An unheld companion book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = CompanionRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test companion book"
    assert registry.title() == "A test companion book"
    assert len(registry.list_companions()) == 2
    other = CompanionRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    companion = _companion()
    assert "A test companion" in plain_words(companion)
    assert panel_plain_words(_mixed_book()).startswith(
        "The companion book holds 2 companions")
    assert verdict_plain_words(_mixed_book()) == (
        "The companions stand held: 1 of 2 shown companions stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green companions; red, "
        "linked in its gaps: companion-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_companion(companion)
    assert "Companion: A test companion" in text
    assert "stands complete" in text
    text = format_companion(_companion(stages=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The VS Code Companions (M-239) - A test companion book" in book_text
    assert "companion-hidden" in format_book(_mixed_book(), "editor-test")
    assert "Companion panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "held - A test companion (companion-test)" in index_text
    assert "companion-hidden" in index_text
    screen = format_companion_screen()
    assert "The VS Code Companions (M-239)" in screen
    assert "companion-bare-companion" in screen

def test_parse_args_well_and_loader_targets():
    assert parse_companion_args("") == ("show", None)
    assert parse_companion_args(None) == ("show", None)
    assert parse_companion_args("show") == ("show", None)
    assert parse_companion_args("companion companion-test") == (
        "companion", "companion-test")
    assert parse_companion_args("stage held") == (
        "stage", "held")
    assert parse_companion_args("editor editor-test") == (
        "editor", "editor-test")
    assert parse_companion_args("view view-test") == ("view", "view-test")
    assert parse_companion_args("note note-test") == ("note", "note-test")
    assert parse_companion_args("index") == ("index", None)
    assert parse_companion_args("panel") == ("panel", None)
    assert parse_companion_args("verdict") == ("verdict", None)
    for bad in ("dance", "companion", "stage", "editor", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_companion_args(bad)
    ledger = ledger_record()
    assert ledger["type"] == "companion_well"
    assert ledger["total"] == 5
    assert ledger["current_companion"] == "companion-bare-companion"
    book = load_companion({
        "schema": COMPANION_SCHEMA, "editor": "M-239",
        "vscode_companions": {"title": "A opened book"},
        "editors": [_ref().to_record()],
        "companion_records": [_companion().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, CompanionBook)
    assert book.title == "A opened book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_companion({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_companion({"editor": "M-999"})
    built = build_companion(
        companion_id="companion-kw", seq=3, editor_id="editor-test",
        title="Kw Companion", stages=["linked", "probed", "opened", "shared", "held"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="companion-test")
    assert built.companion_id == "companion-kw"
    assert companion_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-239 agent layer: the agent holds a companion
# book for the session, companions and views are
# published as session news through the
# checkpoint target (ledger first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held companions, the ledger is derived from
# the held companions' completeness, the roadmap standing
# is shared from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no editor. This layer companions
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session ledger news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_COMPANION_EVENT_TYPES = (
    "companion_companion", "companion_run", "companion_view",
    "companion_panel", "companion_verdict")


def _companion_events(store, session_id, editor):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == editor]


def _write_vscodecompanions_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / COMPANION_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "vscode_companions.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestCompanionAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.vscodecompanions_status()
        assert status["companion_records"] == []
        assert status["editors"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["vscodecompanions_book"]["title"] == EXAMPLE_TITLE
        assert len(status["vscodecompanions_book"]["editors"]) == 3
        assert len(status["vscodecompanions_book"]["companion_records"]) == 5
        assert len(status["vscodecompanions_book"]["views"]) == 2
        assert len(status["vscodecompanions_book"]["notes"]) == 2
        assert len(status["vscodecompanions_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-editor"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["stage"] for e in status["index"]["companions"]] == (
            EXAMPLE_STAGES)
        assert status["index"]["gaps"] == [
            "companion-bare-companion", "companion-leaping-companion"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["ledger"]["total"] == 5
        assert status["ledger"]["current_companion"] == "companion-bare-companion"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 255
        assert status["roadmap"]["next_slice"] == "M-256"
        assert status["roadmap"]["m239_title"] == "IDE companions I — VS Code family"
        assert "held as data alone" in status["rule"]
        assert "companion-bare-companion" in status["plain_words"]
        assert "The VS Code Companions (M-239)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._vscodecompanions_registry()
        assert agent._vscodecompanions_registry() is first
        assert agent._vscodecompanions_store is first
        for name in ("vscodecompanions_book", "vscodecompanions_status", "vscodecompanions_panel",
                     "vscodecompanions_verdict", "vscodecompanions_index", "report_vscodecompanions"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_vscodecompanions_registry", "vscodecompanions_book", "vscodecompanions_status",
            "get_vscodecompanions_companion", "get_vscodecompanions_view", "get_vscodecompanions_note",
            "companions_for_editor", "vscodecompanions_green",
            "vscodecompanions_panel", "vscodecompanions_verdict", "vscodecompanions_index",
            "register_vscodecompanions_companion", "register_vscodecompanions_view",
            "view_vscodecompanions", "register_vscodecompanions_book",
            "record_vscodecompanions_book", "report_vscodecompanions",
            "_publish_vscodecompanions_record", "_vscodecompanions_screen",
            "_vscodecompanions_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.vscodecompanions_status()
        assert agent.get_vscodecompanions_companion(
            "companion-held-companion").title == "The held companion"
        assert agent.get_vscodecompanions_view(
            "view-companions").view_filter == "all"
        assert agent.get_vscodecompanions_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.companion_id for d in agent.companions_for_editor(
            "editor-insiders")] == [
            "companion-own-companion", "companion-bare-companion",
            "companion-leaping-companion"]
        assert [d.companion_id for d in agent.vscodecompanions_green()] == [
            "companion-held-companion", "companion-retried-companion", "companion-own-companion"]
        agent.vscodecompanions_panel()
        agent.vscodecompanions_verdict()
        agent.vscodecompanions_index()
        agent.report_vscodecompanions()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _COMPANION_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_vscodecompanions_companion("companion-nope")
        with pytest.raises(KeyError):
            agent.get_vscodecompanions_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_vscodecompanions_note("note-nope")
        with pytest.raises(ValueError):
            agent.companions_for_editor("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_vscodecompanions_companion(_companion())
        status = agent.vscodecompanions_status()
        assert [d["companion_id"] for d in status["companion_records"]] == ["companion-test"]
        assert status["book"]["title"] == "An unheld companion book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["stage"] for e in status["index"]["companions"]] == [
            "held"]
        assert status["first_note"] is None
        assert "companion-test" in status["screen"]
    def test_held_companion_never_falls_back_to_the_example(
            self, agent):
        agent.register_vscodecompanions_companion(_companion())
        with pytest.raises(KeyError):
            agent.get_vscodecompanions_companion("companion-held-companion")
        with pytest.raises(KeyError):
            agent.get_vscodecompanions_view("view-companions")
        with pytest.raises(KeyError):
            agent.get_vscodecompanions_note("note-note-first")
        companion = agent.get_vscodecompanions_companion("companion-test")
        assert companion.title == "A test companion"
        assert agent.vscodecompanions_book().title == (
            "An unheld companion book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_vscodecompanions_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.companion_id == "companion-held-companion"
        status = agent.vscodecompanions_status()
        assert status["index"]["gaps"] == [
            "companion-bare-companion", "companion-leaping-companion"]
        assert status["first_note"]["companion_id"] == (
            "companion-held-companion")
        assert status["first_note"]["stance"] == "note"

class TestCompanionAgentHolding:
    def test_register_companion_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_vscodecompanions_companion(_companion())
        assert result["companion"]["companion_id"] == "companion-test"
        assert result["record_news"]["type"] == "companion_companion"
        assert "companion-test" in result["screen"]
        events = _companion_events(store, session_id, "companion_companion")
        assert len(events) == 1
        agent.close()

    def test_duplicate_connection_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_vscodecompanions_companion(_companion())
        with pytest.raises(ValueError):
            agent.register_vscodecompanions_companion(_companion(seq=9))
        with pytest.raises(ValueError):
            agent.register_vscodecompanions_companion(_companion(companion_id="companion-two"))
        events = _companion_events(store, session_id, "companion_companion")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_vscodecompanions_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_companion_events(
            store, session_id, "companion_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_vscodecompanions_companion(_companion())
        result = agent.view_vscodecompanions("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "companion_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "held"
        assert len(_companion_events(
            store, session_id, "companion_view")) == 1
        assert len(_companion_events(
            store, session_id, "companion_panel")) == 1
        assert len(_companion_events(
            store, session_id, "companion_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_companion(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_vscodecompanions_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "companion_run", "companion_companion", "companion_view"]
        assert len(_companion_events(
            store, session_id, "companion_companion")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_vscodecompanions_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "companion_panel"
        assert result["index_record"]["gaps"] == [
            "companion-bare-companion", "companion-leaping-companion"]
        with pytest.raises(ValueError):
            agent.record_vscodecompanions_book()
        assert len(_companion_events(
            store, session_id, "companion_run")) == 3
        assert len(_companion_events(
            store, session_id, "companion_companion")) == 5
        assert len(_companion_events(
            store, session_id, "companion_view")) == 2
        agent.close()

    def test_book_from_a_file_is_linked_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_vscodecompanions_book_file(tmp_path)
        book = load_companion_file(path)
        result = agent.record_vscodecompanions_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_runrt_renders_example_then_held_book_only(self, agent):
        companion = agent.report_vscodecompanions()
        assert companion["book"]["title"] == EXAMPLE_TITLE
        assert companion["verdict"]["verdict"] == "held"
        assert companion["index"]["gaps"] == [
            "companion-bare-companion", "companion-leaping-companion"]
        assert "companion-held-companion" in companion["book_text"]
        assert "held - The held companion (companion-held-companion)" in companion["index_text"]
        agent.register_vscodecompanions_companion(_companion())
        companion = agent.report_vscodecompanions()
        assert companion["book"]["title"] == "An unheld companion book"
        assert companion["panel"] is None
        assert companion["verdict"] is None

class TestCompanionTerminalHeading:
    def test_show_companion_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/vscodecompanions")
        assert "The VS Code Companions (M-239)" in text
        _, _, text = _slash(agent, "/vscodecompanions companion companion-held-companion")
        assert "Companion: The held companion" in text
        _, _, text = _slash(
            agent, "/vscodecompanions stage held")
        assert "Companion: The held companion" in text
        _, _, text = _slash(agent, "/vscodecompanions stage triple companion")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/vscodecompanions editor editor-insiders")
        assert "companion-bare-companion" in text
        assert "companion-held-companion" not in text
        _, _, text = _slash(agent, "/vscodecompanions view view-companions")
        assert "filter all" in text
        _, _, text = _slash(agent, "/vscodecompanions note note-note-first")
        assert "Companion note note companion-held-companion" in text
        _, _, text = _slash(agent, "/vscodecompanions index")
        assert "Companion index" in text
        assert "companion-bare-companion" in text
        _, _, text = _slash(agent, "/vscodecompanions panel")
        assert "Companion panel under view view-companions" in text
        _, _, text = _slash(agent, "/vscodecompanions verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/vscodecompanions [show|companion <companion-id>"
                "|stage <stage>|editor <editor-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/vscodecompanions dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/vscodecompanions companion companion-nope")
        assert "no companion linked" in text
@pytest.fixture()
def companion_handler(agent, monkeypatch):
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


def _companion_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestCompanionEditor:
    def test_show_is_default(self, companion_handler, agent):
        companion_handler._handle_vscodecompanions("")
        assert "The VS Code Companions (M-239)" in (
            _companion_published_text(companion_handler))

    def test_companion_check_slice_view_note_index_panel_verdict(
            self, companion_handler, agent):
        companion_handler._handle_vscodecompanions("companion companion-held-companion")
        assert "Companion: The held companion" in _companion_published_text(
            companion_handler)
        companion_handler._handle_vscodecompanions(
            "stage held")
        assert "Companion: The held companion" in _companion_published_text(
            companion_handler)
        companion_handler._handle_vscodecompanions("editor editor-insiders")
        assert "companion-bare-companion" in _companion_published_text(
            companion_handler)
        companion_handler._handle_vscodecompanions("view view-companions")
        assert "filter all" in _companion_published_text(companion_handler)
        companion_handler._handle_vscodecompanions("note note-note-first")
        assert "Companion note note companion-held-companion" in (
            _companion_published_text(companion_handler))
        companion_handler._handle_vscodecompanions("index")
        assert "Companion index" in _companion_published_text(companion_handler)
        companion_handler._handle_vscodecompanions("panel")
        assert "Companion panel under view" in _companion_published_text(
            companion_handler)
        companion_handler._handle_vscodecompanions("verdict")
        assert "held" in _companion_published_text(companion_handler)
    def test_bad_grammar_is_published(
            self, companion_handler, agent):
        companion_handler._handle_vscodecompanions("dance party")
        assert USAGE in _companion_published_text(companion_handler)
        companion_handler._handle_vscodecompanions("companion companion-nope")
        assert "no companion linked" in _companion_published_text(
            companion_handler)


class TestChatScreenRoutingCompanion:
    def test_onwell_routes_as_system_editor(self, monkeypatch):
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
        screen.handle_command("/vscodecompanions panel", _FakeLog())
        assert calls == [("/vscodecompanions", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/vscodecompanions[/green] - show the VS Code companions (M-239)" in (
            text)
        assert ('"/vscodecompanions": "Usage: /vscodecompanions | '
                '/vscodecompanions companion <companion-id>') in text

class TestCompanionDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.vscodecompanions_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-companions"
        verdict = agent.vscodecompanions_verdict()
        assert verdict.verdict == "held"
        linked = agent.vscodecompanions_verdict("view-held")
        assert linked.verdict == "held"
        assert linked.green_shown == 3
        agent.register_vscodecompanions_companion(_companion())
        with pytest.raises(ValueError):
            agent.vscodecompanions_panel()
        with pytest.raises(ValueError):
            agent.vscodecompanions_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_vscodecompanions_companion(_companion(stages=[]))
        result = agent.view_vscodecompanions("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.vscodecompanions_index()
        assert [e["stage"] for e in result["index"]["companions"]] == (
            EXAMPLE_STAGES)
        assert result["index"]["gaps"] == [
            "companion-bare-companion", "companion-leaping-companion"]
        assert "held - The held companion (companion-held-companion)" in (
            result["index_text"])
        companion = agent.get_vscodecompanions_companion("companion-leaping-companion")
        assert companion_gaps(companion, agent.vscodecompanions_book()) == (
            "steps from probed to held, which the companion sequence "
            "does not allow",)
        assert companion_green(companion, agent.vscodecompanions_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _COMPANION_EVENT_TYPES] == []
        agent.close()
