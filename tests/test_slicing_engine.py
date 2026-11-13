"""M-203 The Slicing Engine - pure-layer tests.

TIER: integration

The pure layer is the draft slice, held as data:
one record per draft, held whole - the approved
intent it was drafted from, named by intent id,
its title, its verifiable outcomes and its
dependencies, named by draft id. The grain is
derived at call time: a draft carrying no
verifiable outcome, or claiming two or more,
stands unsound, named in its gaps - one verifiable
outcome each is the house grain. Dependencies are
judged from the held drafts alone: a dependency
naming no held draft stands named in its gaps,
and a dependency cycle is named in the gaps of
every draft standing in it, never silently
ordered; the dependency order and each intent's
shape are derived at call time, and the human's
approval holds the shape as data - the set and
its order, never a step. A draft stands only from
an approved intent: a draft naming no held intent,
or one that is not approved, refuses by name. The
index, panel, verdict, board, shape, order and
current draft are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a slice
was actually built, executed live, banked or
pushed. The shipped example book is held in a data
file, and a loader reads a book from any file. No
charter row names this slice: the M-171 TUI
charter binds Part VIII alone, and the M-005
method charter names no slice row - its source
note names the whole Part IX range M-201-M-232 as
the part that executes it, and the tests pin both
facts live. This layer builds no slice, executes
nothing, banks nothing, pushes nothing and opens
no network: it holds draft slices as data and
tells them.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.slicing_engine import (
    EXAMPLE_OUTCOME,
    INDEX_ACTION,
    INTENT_STATES,
    OUTCOME_FIELDS,
    PLAIN_EXPLANATION,
    SLICING_RESOURCE,
    SLICING_RULE,
    SLICING_SCHEMA,
    SLICING_SLICE,
    SOUND_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    ApprovalRecord,
    DraftRecord,
    IndexEntry,
    IntentRef,
    NoteRecord,
    SlicingBook,
    SlicingIndex,
    SlicingPanel,
    SlicingRegistry,
    SlicingVerdict,
    SlicingView,
    approval_for_intent,
    board_record,
    book_record,
    build_approval,
    build_book,
    build_draft,
    build_intent_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_draft,
    dependency_cycles,
    derive_index,
    derive_panel,
    derive_verdict,
    draft_for_outcome,
    draft_gaps,
    draft_order,
    draft_record,
    draft_sound,
    drafts_for_intent,
    first_note,
    format_book,
    format_draft,
    format_index,
    format_note,
    format_outcome,
    format_panel,
    format_slicing_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    intent_record,
    load_slicing,
    load_slicing_file,
    normalize_intent_state,
    normalize_stance,
    normalize_view_filter,
    note_for_draft,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_slicing_args,
    passing_drafts,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    shape_approved,
    shape_of,
    shown_drafts,
    validate_book,
    validate_draft,
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
EXAMPLE_TITLE = "The slicing engine at the M-202 slice boundary"
EXAMPLE_OUTCOMES = [
    "the intent stands held in the user's plain words",
    "slices stand drafted at the house grain",
    "the shape stands approved as data",
]
EXAMPLE_DRAFT_IDS = (
    "draft-capture-intent", "draft-draft-slices",
    "draft-shape-approval", "draft-two-outcomes",
    "draft-loose-thread")
EXAMPLE_SHAPE = (
    "draft-capture-intent > draft-draft-slices > "
    "draft-shape-approval")


def _ref(**overrides):
    fields = {
        "intent_id": "intent-test",
        "seq": 1,
        "project": "A test project",
        "state": "approved",
        "detail": "A test intent reference held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "slicing-test",
    }
    fields.update(overrides)
    return build_intent_ref(fields)


def _draft(**overrides):
    fields = {
        "draft_id": "draft-test",
        "seq": 1,
        "intent_id": "intent-test",
        "title": "A test draft",
        "outcomes": ["the test draft stands sound"],
        "dependencies": [],
        "detail": "A test draft held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "slicing-test",
    }
    fields.update(overrides)
    return build_draft(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "slicing-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "draft_id": "draft-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "slicing-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _approval(**overrides):
    fields = {
        "approval_id": "approval-test",
        "seq": 1,
        "intent_id": "intent-test",
        "shape": "draft-test",
        "detail": "A test shape approval held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "slicing-test",
    }
    fields.update(overrides)
    return build_approval(fields)


def _book(intents=None, drafts=None, views=None, notes=None,
          approvals=None, **overrides):
    fields = {
        "schema": SLICING_SCHEMA,
        "slice": "M-203",
        "slicing_engine": {"title": "A test slicing book"},
        "intents": [item.to_record() for item in (
            intents if intents is not None else [_ref()])],
        "drafts": [item.to_record() for item in (
            drafts if drafts is not None else [_draft()])],
        "views": [item.to_record() for item in (
            views if views is not None else [_view()])],
        "notes": [item.to_record() for item in (notes or [])],
        "approvals": [item.to_record() for item in (
            approvals or [])],
        "panels": [],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(drafts=[
        _draft(),
        _draft(draft_id="draft-hidden", seq=2,
               title="A hidden draft", outcomes=[]),
    ])


def test_shipped_book_loads_with_pinned_shape():
    book = load_slicing()
    assert book.title == EXAMPLE_TITLE
    assert book.draft_ids() == EXAMPLE_DRAFT_IDS
    assert book.intent_ids() == (
        "intent-plain-words", "intent-verbatim",
        "intent-unapproved")
    assert [v.view_id for v in book.views] == [
        "view-slicing", "view-sound"]
    assert [m.draft_id for m in book.notes] == [
        "draft-capture-intent", "draft-two-outcomes"]
    assert [a.intent_id for a in book.approvals] == [
        "intent-plain-words"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m202-boundary"
    assert panel.as_of == "2026-11-10"
    assert [row.item_id for row in panel.rows] == list(book.draft_ids())
    derived = derive_panel(book, "view-slicing")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "sound": 3, "unsound": 2}
    assert derive_verdict(book, "view-slicing").verdict == "strained"
    assert derive_verdict(book, "view-slicing").passing_shown == 3
    assert derive_verdict(book, "view-sound").verdict == "open"
    assert derive_verdict(book, "view-sound").passing_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / SLICING_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == SLICING_SCHEMA
    assert raw["slice"] == "M-203"
    assert "verdict" not in raw
    assert "slicing_index" not in raw
    assert "board" not in raw
    assert "shape" not in raw


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-203")]
    assert slice_.title == "The slicing engine"
    assert slice_.part == 9
    assert "approved intent" in slice_.summary
    assert "house grain" in slice_.summary
    assert "dependencies" in slice_.summary
    assert "shape" in slice_.summary
    assert SLICING_SLICE == "M-203"


def test_charter_rows_do_not_name_m203():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-203" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "PROJECT_FORGE" in method.source_note


def test_closed_vocabularies():
    assert SOUND_WORDS == ("sound", "unsound")
    assert OUTCOME_FIELDS == ("outcomes", "dependencies")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "sound", "unsound")
    assert VERDICT_WORDS == ("open", "strained", "shut")
    assert INTENT_STATES == ("approved", "unapproved")
    assert INDEX_ACTION == "index"
    assert EXAMPLE_OUTCOME == (
        "the intent stands held in the user's plain words")
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_intent_state("APPROVED") == "approved"
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    with pytest.raises(ValueError):
        normalize_intent_state("blessed")
    assert "held as data alone" in SLICING_RULE
    assert "house grain" in SLICING_RULE
    assert "M-203" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /slicing")


def test_shipped_book_judged_honestly_as_data():
    book = load_slicing()
    opening = book.draft_for("draft-capture-intent")
    assert draft_sound(opening, book) is True
    assert draft_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Draft: Capture the intent",
        "Intent: intent-plain-words",
        "Outcome: the intent stands held in the user's plain words",
        "Dependencies: none")
    wide = book.draft_for("draft-two-outcomes")
    assert draft_gaps(wide, book) == (
        "claims 2 outcomes, not the house grain of one "
        "verifiable outcome each",)
    assert draft_sound(wide, book) is False
    loose = book.draft_for("draft-loose-thread")
    assert draft_gaps(loose, book) == (
        "depends on draft-never-held, which stands nowhere "
        "in this book",)
    assert [g.draft_id for g in passing_drafts(book)] == [
        "draft-capture-intent", "draft-draft-slices",
        "draft-shape-approval"]
    index = derive_index(book)
    assert [e.outcome for e in index.entries] == EXAMPLE_OUTCOMES
    assert index.gaps == ("draft-two-outcomes", "draft-loose-thread")
    assert draft_for_outcome(book, EXAMPLE_OUTCOME).draft_id == (
        "draft-capture-intent")
    assert draft_for_outcome(book, "triple resume") is None
    assert dependency_cycles(book) == ()
    assert [g.draft_id for g in draft_order(book)] == list(
        EXAMPLE_DRAFT_IDS)
    assert shape_of(book, "intent-plain-words") == EXAMPLE_SHAPE
    assert shape_approved(book, "intent-plain-words") is True
    assert shape_approved(book, "intent-verbatim") is False
    assert approval_for_intent(
        book, "intent-plain-words").approval_id == (
            "approval-shape-open")
    assert first_note(book).note_id == "note-note-open"
    assert note_for_draft(
        book, "draft-capture-intent", "note").note_id == (
            "note-note-open")
    assert note_for_draft(book, "draft-nope") is None
    assert current_draft(book).draft_id == "draft-two-outcomes"
    board = board_record(book)
    assert board["standings"] == [
        {"standing": "sound", "drafts": 3},
        {"standing": "unsound", "drafts": 2}]
    assert board["total"] == 5
    assert board["current_draft"] == "draft-two-outcomes"
    assert board["shapes"] == [
        {"intent_id": "intent-plain-words", "shape": "approved"},
        {"intent_id": "intent-verbatim", "shape": "unapproved"},
        {"intent_id": "intent-unapproved", "shape": "unapproved"}]
    assert board["cycles"] == []
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 263
    assert citizen["next_slice"] == "M-264"
    assert citizen["m203_title"] == "The slicing engine"
    assert citizen["m203_part"] == 9
    assert citizen["m203_status"] == "done"


def test_draft_record_round_trips():
    draft = _draft()
    assert validate_draft(draft) is draft
    rebuilt = build_draft(draft.to_record())
    assert rebuilt == draft
    assert rebuilt.item_id == "draft-test"
    assert rebuilt.outcome == "the test draft stands sound"
    record = draft_record(draft)
    assert record["type"] == "slicing_draft"
    assert record["sound"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert intent_record(ref)["type"] == "slicing_intent"
    assert intent_record(ref)["state"] == "approved"


def test_grain_is_derived_from_the_outcomes_alone():
    silent = _draft(outcomes=[])
    assert draft_gaps(silent) == ("carries no verifiable outcome",)
    assert draft_sound(silent) is False
    wide = _draft(outcomes=["one outcome", "another outcome"])
    assert draft_gaps(wide) == (
        "claims 2 outcomes, not the house grain of one "
        "verifiable outcome each",)
    assert wide.outcome == ""
    with pytest.raises(ValueError):
        _draft(outcomes=[42])
    with pytest.raises(ValueError):
        _draft(outcomes="one outcome as a bare string")
    with pytest.raises(ValueError):
        _draft(dependencies=["draft-a", "draft-a"])
    with pytest.raises(ValueError):
        _draft(dependencies="draft-a")
    none_draft = _draft(outcomes=None, dependencies=None)
    assert none_draft.outcomes == ()
    assert none_draft.dependencies == ()


def test_draft_refuses_stored_judgements():
    for key in ("standing", "sound", "gaps", "segment", "verdict",
                "index", "entries", "coverage", "current_draft",
                "board", "order"):
        fields = _draft().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_draft(fields)
    fields = _draft().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_draft(fields)


def test_draft_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _draft().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_draft(fields)


def test_draft_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _draft(title="")
    with pytest.raises(ValueError):
        _draft(intent_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _approval(shape="")
    approval = _approval()
    assert approval.shape == "draft-test"
    assert approval.item_id == "approval-test"


def test_plain_telling_derives_from_the_drafts_own_fields():
    draft = _draft(dependencies=["draft-a"])
    assert plain_lines(draft) == (
        "Draft: A test draft",
        "Intent: intent-test",
        "Outcome: the test draft stands sound",
        "Dependencies: draft-a")
    segment = segment_of(draft)
    assert segment.startswith("draft-test: A test draft")
    assert "outcome: 'the test draft stands sound'" in segment
    assert "gaps: none" in segment
    assert plain_words(draft).startswith(
        "A test draft - from intent-test")


def test_unsound_drafts_stand_named_in_their_gaps():
    book = _book(drafts=[
        _draft(draft_id="draft-a", seq=1,
               dependencies=["draft-b"]),
        _draft(draft_id="draft-b", seq=2,
               dependencies=["draft-a"]),
        _draft(draft_id="draft-c", seq=3,
               dependencies=["draft-missing"]),
    ])
    a = book.draft_for("draft-a")
    assert draft_gaps(a, book) == (
        "stands in a dependency cycle: "
        "draft-a > draft-b > draft-a",)
    b = book.draft_for("draft-b")
    assert draft_gaps(b, book) == (
        "stands in a dependency cycle: "
        "draft-a > draft-b > draft-a",)
    assert dependency_cycles(book) == (
        "draft-a > draft-b > draft-a",)
    assert [g.draft_id for g in draft_order(book)] == ["draft-c"]
    c = book.draft_for("draft-c")
    assert draft_gaps(c, book) == (
        "depends on draft-missing, which stands nowhere "
        "in this book",)
    selfish = _draft(dependencies=["draft-test"])
    assert draft_gaps(selfish) == (
        "stands in a dependency cycle: draft-test > draft-test",)
    assert current_draft(book).draft_id == "draft-a"


def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "slicing_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "slicing_note"
    assert record["draft_id"] == "draft-test"
    assert view_plain_words(view) == "View view-test: shows all drafts."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_drafts_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.outcome for e in index.entries] == [
        "the test draft stands sound"]
    assert index.entries[0] == IndexEntry(
        outcome="the test draft stands sound",
        draft_id="draft-test", title="A test draft")
    assert index.gaps == ("draft-hidden",)
    record = index_record(book)
    assert record["type"] == "slicing_index"
    assert record["gaps"] == ["draft-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "slicing_book"


def test_outcome_target_reaches_its_draft_and_an_unheld_target_reaches_nothing():
    book = load_slicing()
    assert draft_for_outcome(
        book, "slices stand drafted at the house grain").draft_id == (
            "draft-draft-slices")
    assert draft_for_outcome(book, "") is None
    assert draft_for_outcome(book, None) is None
    assert draft_for_outcome(book, "not held at all") is None
    text = format_outcome(book, "not held at all")
    assert "reaches nothing in this book" in text


def test_first_note_is_held_as_data():
    book = load_slicing()
    first = first_note(book)
    assert first.note_id == "note-note-open"
    assert first.stance == "note"
    text = format_note(first)
    assert "Slicing note note draft-capture-intent" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").draft_id == "draft-test"
    assert note_for_draft(book, "draft-test").note_id == "note-test"
    assert note_for_draft(book, "draft-test", "praise") is None
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
    row = build_row(None, _draft(), book)
    assert row.standing == "sound"
    assert validate_row(row, _draft(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_drafts():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "strained"
    assert verdict.passing_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "slicing_verdict"
    sound_book = _book(views=[_view(view_filter="sound")])
    assert derive_verdict(sound_book).verdict == "open"
    empty_book = _book(drafts=[_draft(outcomes=[])],
                       views=[_view(view_filter="sound")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "shut"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(SlicingVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            passing_shown=1, latest_on=ON))


def test_shown_and_intent_readings():
    book = load_slicing()
    assert [g.draft_id for g in shown_drafts(book)] == list(
        EXAMPLE_DRAFT_IDS)
    assert [g.draft_id for g in shown_drafts(book, "view-sound")] == [
        "draft-capture-intent", "draft-draft-slices",
        "draft-shape-approval"]
    assert [g.draft_id for g in drafts_for_intent(
        book, "intent-verbatim")] == [
            "draft-two-outcomes", "draft-loose-thread"]
    assert drafts_for_intent(book, "intent-nope") == ()
    assert current_draft(_mixed_book()).draft_id == "draft-hidden"
    assert current_draft(_book()) is None
    stale = _book(approvals=[_approval(shape="draft-other")])
    assert shape_of(stale, "intent-test") == "draft-test"
    assert shape_approved(stale, "intent-test") is False
    assert board_record(stale)["shapes"] == [
        {"intent_id": "intent-test", "shape": "stale"}]


def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(drafts=[_draft(), _draft(seq=2)])
    with pytest.raises(ValueError):
        _book(drafts=[_draft(), _draft(draft_id="draft-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(drafts=[_draft(intent_id="intent-nope")])
    with pytest.raises(ValueError):
        _book(intents=[_ref(), _ref(
            intent_id="intent-cold", seq=2, state="unapproved")],
            drafts=[_draft(intent_id="intent-cold")])
    with pytest.raises(ValueError):
        _book(approvals=[_approval(), _approval(
            approval_id="approval-two", seq=2)])
    with pytest.raises(ValueError):
        _book(approvals=[_approval(intent_id="intent-nope")])
    fields = {
        "schema": SLICING_SCHEMA, "slice": "M-203",
        "slicing_engine": {"title": "A judged book"},
        "intents": [_ref().to_record()],
        "drafts": [_draft().to_record()],
        "views": [_view().to_record()], "notes": [],
        "approvals": [], "panels": [],
        "verdict": "open"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_draft"] = "draft-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_draft")
    fields["shape"] = "draft-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("shape")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / SLICING_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "slicing_engine.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_slicing_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.draft_ids() == EXAMPLE_DRAFT_IDS


def test_registry_holds_records_one_by_one():
    registry = SlicingRegistry()
    assert registry.title() is None
    registry.register_intent_ref(_ref())
    registry.register_draft(_draft())
    registry.register_view(_view())
    assert [g.draft_id for g in registry.list_drafts()] == ["draft-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_draft("draft-test").title == "A test draft"
    assert registry.get_intent("intent-test").state == "approved"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("draft-test").draft_id == "draft-test"
    with pytest.raises(ValueError):
        registry.register_draft(_draft(seq=9))
    with pytest.raises(ValueError):
        registry.register_draft(_draft(draft_id="draft-two"))
    with pytest.raises(KeyError):
        registry.get_draft("draft-nope")
    assert registry.book().title == "An unheld slicing book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = SlicingRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test slicing book"
    assert registry.title() == "A test slicing book"
    assert len(registry.list_drafts()) == 2
    other = SlicingRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    draft = _draft()
    assert "A test draft" in plain_words(draft)
    assert panel_plain_words(_mixed_book()).startswith(
        "The slicing book holds 2 drafts")
    assert verdict_plain_words(_mixed_book()) == (
        "The drafts stand strained: 1 of 2 shown drafts stand sound.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 sound drafts for 1 outcomes; unsound, "
        "named in its gaps: draft-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_draft(draft)
    assert "Draft: A test draft" in text
    assert "stands sound" in text
    text = format_draft(_draft(outcomes=[]))
    assert "stands unsound" in text
    assert "carries no verifiable outcome" in text
    book_text = format_book(_mixed_book())
    assert "The Slicing Engine (M-203) - A test slicing book" in book_text
    assert "draft-hidden" in format_book(_mixed_book(), "intent-test")
    assert "Slicing panel under view view-test" in format_panel(_mixed_book())
    assert "strained" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "the test draft stands sound - A test draft (draft-test)" in index_text
    assert "draft-hidden" in index_text
    screen = format_slicing_screen()
    assert "The Slicing Engine (M-203)" in screen
    assert "draft-two-outcomes" in screen


def test_parse_args_board_and_loader_targets():
    assert parse_slicing_args("") == ("show", None)
    assert parse_slicing_args(None) == ("show", None)
    assert parse_slicing_args("show") == ("show", None)
    assert parse_slicing_args("draft draft-test") == (
        "draft", "draft-test")
    assert parse_slicing_args("outcome the test draft stands sound") == (
        "outcome", "the test draft stands sound")
    assert parse_slicing_args("intent intent-test") == (
        "intent", "intent-test")
    assert parse_slicing_args("view view-test") == ("view", "view-test")
    assert parse_slicing_args("note note-test") == ("note", "note-test")
    assert parse_slicing_args("index") == ("index", None)
    assert parse_slicing_args("panel") == ("panel", None)
    assert parse_slicing_args("verdict") == ("verdict", None)
    for bad in ("dance", "draft", "outcome", "intent", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_slicing_args(bad)
    board = board_record()
    assert board["type"] == "slicing_board"
    assert board["total"] == 5
    assert board["current_draft"] == "draft-two-outcomes"
    book = load_slicing({
        "schema": SLICING_SCHEMA, "slice": "M-203",
        "slicing_engine": {"title": "A judged book"},
        "intents": [_ref().to_record()],
        "drafts": [_draft().to_record()],
        "views": [_view().to_record()], "notes": [],
        "approvals": [], "panels": []})
    assert isinstance(book, SlicingBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_slicing({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_slicing({"slice": "M-999"})
    built = build_draft(
        draft_id="draft-kw", seq=3, intent_id="intent-test",
        title="Kw Draft", outcomes=["a kw outcome"],
        dependencies=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="slicing-test")
    assert built.draft_id == "draft-kw"
    assert draft_sound(built) is True




# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-203 agent layer: the agent holds a slicing
# book for the session, drafts and views are
# published as session news through the
# checkpoint target (journal first, deduped per
# shape), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held drafts, the board is derived from
# the held drafts' soundness, the roadmap standing
# is read from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no slice. This layer runs
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_SLICING_EVENT_TYPES = (
    "slicing_draft", "slicing_intent", "slicing_view",
    "slicing_panel", "slicing_verdict")


def _slicing_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_slicing_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / SLICING_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "slicing_engine.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestSlicingAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.slicing_status()
        assert status["drafts"] == []
        assert status["intents"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["slicing_book"]["title"] == EXAMPLE_TITLE
        assert len(status["slicing_book"]["intents"]) == 3
        assert len(status["slicing_book"]["drafts"]) == 5
        assert len(status["slicing_book"]["views"]) == 2
        assert len(status["slicing_book"]["notes"]) == 2
        assert len(status["slicing_book"]["approvals"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m202-boundary"
        assert status["verdict"]["verdict"] == "strained"
        assert status["verdict"]["passing_shown"] == 3
        assert [e["outcome"] for e in status["index"]["entries"]] == (
            EXAMPLE_OUTCOMES)
        assert status["index"]["gaps"] == [
            "draft-two-outcomes", "draft-loose-thread"]
        assert status["first_note"]["note_id"] == "note-note-open"
        assert status["board"]["total"] == 5
        assert status["board"]["current_draft"] == "draft-two-outcomes"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 263
        assert status["roadmap"]["next_slice"] == "M-264"
        assert status["roadmap"]["m203_title"] == "The slicing engine"
        assert "held as data alone" in status["rule"]
        assert "draft-two-outcomes" in status["plain_words"]
        assert "The Slicing Engine (M-203)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._slicing_registry()
        assert agent._slicing_registry() is first
        assert agent._slicing_store is first
        for name in ("slicing_book", "slicing_status", "slicing_panel",
                     "slicing_verdict", "slicing_index", "report_slicing"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_slicing_registry", "slicing_book", "slicing_status",
            "get_slicing_draft", "get_slicing_view", "get_slicing_note",
            "slicing_drafts_for_intent", "slicing_drafts_sound",
            "slicing_panel", "slicing_verdict", "slicing_index",
            "register_slicing_draft", "register_slicing_view",
            "view_slicing", "register_slicing_book",
            "record_slicing_book", "report_slicing",
            "_publish_slicing_record", "_slicing_screen",
            "_slicing_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.slicing_status()
        assert agent.get_slicing_draft(
            "draft-capture-intent").title == "Capture the intent"
        assert agent.get_slicing_view(
            "view-slicing").view_filter == "all"
        assert agent.get_slicing_note(
            "note-note-open").note_id == "note-note-open"
        assert [d.draft_id for d in agent.slicing_drafts_for_intent(
            "intent-verbatim")] == [
            "draft-two-outcomes", "draft-loose-thread"]
        assert [d.draft_id for d in agent.slicing_drafts_sound()] == [
            "draft-capture-intent", "draft-draft-slices",
            "draft-shape-approval"]
        agent.slicing_panel()
        agent.slicing_verdict()
        agent.slicing_index()
        agent.report_slicing()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _SLICING_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_slicing_draft("draft-nope")
        with pytest.raises(KeyError):
            agent.get_slicing_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_slicing_note("note-nope")
        with pytest.raises(ValueError):
            agent.slicing_drafts_for_intent("")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_slicing_draft(_draft())
        status = agent.slicing_status()
        assert [d["draft_id"] for d in status["drafts"]] == ["draft-test"]
        assert status["book"]["title"] == "An unheld slicing book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["outcome"] for e in status["index"]["entries"]] == [
            "the test draft stands sound"]
        assert status["first_note"] is None
        assert "draft-test" in status["screen"]

    def test_held_draft_never_falls_back_to_the_example(
            self, agent):
        agent.register_slicing_draft(_draft())
        with pytest.raises(KeyError):
            agent.get_slicing_draft("draft-capture-intent")
        with pytest.raises(KeyError):
            agent.get_slicing_view("view-slicing")
        with pytest.raises(KeyError):
            agent.get_slicing_note("note-note-open")
        draft = agent.get_slicing_draft("draft-test")
        assert draft.title == "A test draft"
        assert agent.slicing_book().title == (
            "An unheld slicing book")

    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_slicing_note("note-note-open")
        assert first.note_id == "note-note-open"
        assert first.draft_id == "draft-capture-intent"
        status = agent.slicing_status()
        assert status["index"]["gaps"] == [
            "draft-two-outcomes", "draft-loose-thread"]
        assert status["first_note"]["draft_id"] == (
            "draft-capture-intent")
        assert status["first_note"]["stance"] == "note"


class TestSlicingAgentHolding:
    def test_register_draft_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_slicing_draft(_draft())
        assert result["draft"]["draft_id"] == "draft-test"
        assert result["record_news"]["type"] == "slicing_draft"
        assert "draft-test" in result["screen"]
        events = _slicing_events(store, session_id, "slicing_draft")
        assert len(events) == 1
        agent.close()

    def test_duplicate_draft_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_slicing_draft(_draft())
        with pytest.raises(ValueError):
            agent.register_slicing_draft(_draft(seq=9))
        with pytest.raises(ValueError):
            agent.register_slicing_draft(_draft(draft_id="draft-two"))
        events = _slicing_events(store, session_id, "slicing_draft")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_slicing_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_slicing_events(
            store, session_id, "slicing_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_slicing_draft(_draft())
        result = agent.view_slicing("sound")
        assert result["view"]["view_filter"] == "sound"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "slicing_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "open"
        assert len(_slicing_events(
            store, session_id, "slicing_view")) == 1
        assert len(_slicing_events(
            store, session_id, "slicing_panel")) == 1
        assert len(_slicing_events(
            store, session_id, "slicing_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_slicing_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "slicing_intent", "slicing_draft", "slicing_view"]
        assert len(_slicing_events(
            store, session_id, "slicing_draft")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_slicing_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "slicing_panel"
        assert result["index_record"]["gaps"] == [
            "draft-two-outcomes", "draft-loose-thread"]
        with pytest.raises(ValueError):
            agent.record_slicing_book()
        assert len(_slicing_events(
            store, session_id, "slicing_intent")) == 3
        assert len(_slicing_events(
            store, session_id, "slicing_draft")) == 5
        assert len(_slicing_events(
            store, session_id, "slicing_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_slicing_book_file(tmp_path)
        book = load_slicing_file(path)
        result = agent.record_slicing_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_slicing()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "strained"
        assert report["index"]["gaps"] == [
            "draft-two-outcomes", "draft-loose-thread"]
        assert "draft-capture-intent" in report["book_text"]
        assert "the intent stands held in the user's plain words - Capture the intent (draft-capture-intent)" in report["index_text"]
        agent.register_slicing_draft(_draft())
        report = agent.report_slicing()
        assert report["book"]["title"] == "An unheld slicing book"
        assert report["panel"] is None
        assert report["verdict"] is None


class TestSlicingTerminalHeading:
    def test_show_draft_outcome_intent_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/slicing")
        assert "The Slicing Engine (M-203)" in text
        _, _, text = _slash(agent, "/slicing draft draft-capture-intent")
        assert "Draft: Capture the intent" in text
        _, _, text = _slash(
            agent,
            "/slicing outcome the intent stands held in the user's plain words")
        assert "Draft: Capture the intent" in text
        _, _, text = _slash(agent, "/slicing outcome triple resume")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/slicing intent intent-verbatim")
        assert "draft-two-outcomes" in text
        assert "draft-capture-intent" not in text
        _, _, text = _slash(agent, "/slicing view view-slicing")
        assert "filter all" in text
        _, _, text = _slash(agent, "/slicing note note-note-open")
        assert "Slicing note note draft-capture-intent" in text
        _, _, text = _slash(agent, "/slicing index")
        assert "Slicing index" in text
        assert "draft-two-outcomes" in text
        _, _, text = _slash(agent, "/slicing panel")
        assert "Slicing panel under view view-slicing" in text
        _, _, text = _slash(agent, "/slicing verdict")
        assert "strained" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/slicing [show|draft <draft-id>"
                "|outcome <outcome>|intent <intent-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/slicing dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/slicing draft draft-nope")
        assert "no draft named" in text


@pytest.fixture()
def slicing_handler(agent, monkeypatch):
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


def _slicing_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestSlicingCommand:
    def test_show_is_default(self, slicing_handler, agent):
        slicing_handler._handle_slicing("")
        assert "The Slicing Engine (M-203)" in (
            _slicing_published_text(slicing_handler))

    def test_draft_outcome_intent_view_note_index_panel_verdict(
            self, slicing_handler, agent):
        slicing_handler._handle_slicing("draft draft-capture-intent")
        assert "Draft: Capture the intent" in _slicing_published_text(
            slicing_handler)
        slicing_handler._handle_slicing(
            "outcome the intent stands held in the user's plain words")
        assert "Draft: Capture the intent" in _slicing_published_text(
            slicing_handler)
        slicing_handler._handle_slicing("intent intent-verbatim")
        assert "draft-two-outcomes" in _slicing_published_text(
            slicing_handler)
        slicing_handler._handle_slicing("view view-slicing")
        assert "filter all" in _slicing_published_text(slicing_handler)
        slicing_handler._handle_slicing("note note-note-open")
        assert "Slicing note note draft-capture-intent" in (
            _slicing_published_text(slicing_handler))
        slicing_handler._handle_slicing("index")
        assert "Slicing index" in _slicing_published_text(slicing_handler)
        slicing_handler._handle_slicing("panel")
        assert "Slicing panel under view" in _slicing_published_text(
            slicing_handler)
        slicing_handler._handle_slicing("verdict")
        assert "strained" in _slicing_published_text(slicing_handler)

    def test_bad_grammar_is_published(
            self, slicing_handler, agent):
        slicing_handler._handle_slicing("dance party")
        assert USAGE in _slicing_published_text(slicing_handler)
        slicing_handler._handle_slicing("draft draft-nope")
        assert "no draft named" in _slicing_published_text(
            slicing_handler)


class TestChatScreenRoutingSlicing:
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
        screen.handle_command("/slicing panel", _FakeLog())
        assert calls == [("/slicing", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/slicing[/green] - show the slicing engine (M-203)" in (
            text)
        assert ('"/slicing": "Usage: /slicing | '
                '/slicing draft <draft-id>') in text


class TestSlicingDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.slicing_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-slicing"
        verdict = agent.slicing_verdict()
        assert verdict.verdict == "strained"
        found = agent.slicing_verdict("view-sound")
        assert found.verdict == "open"
        assert found.passing_shown == 3
        agent.register_slicing_draft(_draft())
        with pytest.raises(ValueError):
            agent.slicing_panel()
        with pytest.raises(ValueError):
            agent.slicing_verdict()

    def test_view_target_over_an_unshown_filter_is_shut(self, agent):
        agent.register_slicing_draft(_draft(outcomes=[]))
        result = agent.view_slicing("sound")
        assert result["verdict_record"]["verdict"] == "shut"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.slicing_index()
        assert [e["outcome"] for e in result["index"]["entries"]] == (
            EXAMPLE_OUTCOMES)
        assert result["index"]["gaps"] == [
            "draft-two-outcomes", "draft-loose-thread"]
        assert "the intent stands held in the user's plain words - Capture the intent (draft-capture-intent)" in (
            result["index_text"])
        draft = agent.get_slicing_draft("draft-loose-thread")
        assert draft_gaps(draft, agent.slicing_book()) == (
            "depends on draft-never-held, which stands nowhere "
            "in this book",)
        assert draft_sound(draft, agent.slicing_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _SLICING_EVENT_TYPES] == []
        agent.close()
