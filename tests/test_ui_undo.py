"""M-198 Command Undo - pure-layer tests.

TIER: integration

The pure layer is the command undo, held as
data: one record per pane, held whole as a
card - under its title, its kind in the closed
vocabulary (command, action, navigation,
setting), its cursor held honestly (unknown
stays empty, never invented), the preserved state
it carries, named as data, and its detail
- the notes held as data beside them, each naming
its pane, its stance and its target, and the
undo index derived at call time from the held
panes alone, never stored where it could drift.
An pane naming no preserved state stands
incomplete, named in its gaps; two panes
standing for one pane id refuse by name, and
one stance record stands per pane stance. A
record claiming a command was actually executed,
an action actually run, or a navigation actually
taken, refuses by name, and a stored index or
verdict refuses by name. The panel is derived for
one held view and the verdict is derived for the
whole book under one view. The shipped example
book is held in a data file, and a loader reads a
book from any file. The M-171 charter names NO
row for this slice - and the tests pin that
live. This layer executes nothing, runs no
command, navigates nowhere, opens no network
and writes nothing: it holds the undo as
data and tells it.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.ui_undo import (
    KINDS,
    EXAMPLE_STATE,
    STANCES,
    INDEX_ACTION,
    UI_UNDO_RESOURCE,
    UI_UNDO_SCHEMA,
    UI_UNDO_SLICE,
    UNDO_RULE,
    PLAIN_EXPLANATION,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    READY_WORDS,
    PaneCard,
    NoteRecord,
    UndoBook,
    UndoPanel,
    UiUndoRegistry,
    UndoVerdict,
    UndoView,
    book_record,
    build_book,
    build_pane,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    derive_index,
    derive_panel,
    derive_verdict,
    first_note,
    format_book,
    format_pane,
    format_index,
    format_note,
    format_undo_screen,
    format_panel,
    format_state,
    format_verdict,
    format_view,
    pane_for_state,
    pane_gaps,
    pane_passes,
    pane_plain_words,
    pane_record,
    panes_for_kind,
    index_plain_words,
    index_record,
    inspect_pane_source,
    note_for_pane,
    note_plain_words,
    note_record,
    load_ui_undo,
    load_ui_undo_file,
    normalize_kind,
    normalize_stance,
    normalize_view_filter,
    panel_plain_words,
    panel_record,
    parse_undo_args,
    passing_panes,
    plain_lines,
    plain_words,
    shown_panes,
    total_panes,
    validate_book,
    validate_pane,
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
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.tui_redesign_charter import load_charter

ROOT = Path(__file__).resolve().parents[1]
ON = "2026-11-09"
BY = "the coordinator"
EXAMPLE_TITLE = "UI undo at the M-197 slice boundary"


def _pane(**overrides):
    fields = {
        "pane_id": "pane-test",
        "seq": 1,
        "title": "A test pane",
        "kind": "pane",
        "cursor": "ctrl+k",
        "state": "the editor draft still open",
        "detail": "A test pane held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "undo-test",
    }
    fields.update(overrides)
    return build_pane(fields)


def _stored_pane(pane):
    return pane.to_record()


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "undo-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _stored_view(view):
    return view.to_record()


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "pane_id": "pane-test",
        "stance": "note",
        "target": "the user",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "undo-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _book(panes=None, views=None, notes=None, **overrides):
    fields = {
        "schema": UI_UNDO_SCHEMA,
        "slice": "M-198",
        "ui_undo": {"title": "A test undo book"},
        "panes": [_stored_pane(item) for item in (
            panes if panes is not None else [_pane()])],
        "views": [_stored_view(item) for item in (
            views if views is not None else [_view()])],
        "notes": [item.to_record() for item in (notes or [])],
        "panels": [],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(panes=[
        _pane(),
        _pane(pane_id="pane-quiet-only", seq=2,
              title="A quiet pane", kind="view",
              cursor="", state=""),
    ])


def test_shipped_book_loads_with_pinned_shape():
    book = load_ui_undo()
    assert book.title == EXAMPLE_TITLE
    assert book.pane_ids() == (
        "pane-editor-main", "pane-files-main",
        "pane-board-main", "pane-preview-main",
        "pane-quiet-main", "pane-help-main")
    assert [v.view_id for v in book.views] == [
        "view-undo", "view-ready"]
    assert [m.pane_id for m in book.notes] == [
        "pane-editor-main",
        "pane-help-main"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m197-boundary"
    assert panel.as_of == "2026-11-10"
    assert [row.item_id for row in panel.rows] == list(book.pane_ids())
    derived = derive_panel(book, "view-undo")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 6
    assert panel.total_shown == derived.total_shown == 6
    assert {c.standing: c.items for c in panel.target_counts} == {
        "ready": 5, "unready": 1}
    assert derive_verdict(book, "view-undo").verdict == "strained"
    assert derive_verdict(book, "view-undo").passing_shown == 5
    assert derive_verdict(book, "view-ready").verdict == "open"
    assert derive_verdict(book, "view-ready").passing_shown == 5
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / UI_UNDO_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == UI_UNDO_SCHEMA
    assert raw["slice"] == "M-198"
    assert "verdict" not in raw
    assert "undo_index" not in raw


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-198")]
    assert slice_.title == "Undo of UI itself"
    assert slice_.part == 8
    assert "closing a pane or clearing a view" in slice_.summary
    assert "never destructive to work" in slice_.summary
    assert "view state per session persists" in slice_.summary
    assert UI_UNDO_SLICE == "M-198"


def test_charter_does_not_name_m197():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert owners.count("M-187") == 1
    assert owners.count("M-198") == 0


def test_closed_vocabularies():
    assert READY_WORDS == ("ready", "unready")
    assert KINDS == ("pane", "view", "panel", "tab")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "ready", "unready")
    assert VERDICT_WORDS == ("open", "strained", "shut")
    assert INDEX_ACTION == "index"
    assert EXAMPLE_STATE == "the editor draft still open"
    assert normalize_kind("PANE") == "pane"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    with pytest.raises(ValueError):
        normalize_kind("the void")
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    assert "held as data alone" in UNDO_RULE
    assert "restores nothing" in UNDO_RULE
    assert "opens no network" in UNDO_RULE
    assert "M-198" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /uiundo")


def test_shipped_book_judged_honestly_as_data():
    book = load_ui_undo()
    opener = book.pane_for("pane-editor-main")
    assert pane_passes(opener) is True
    assert pane_gaps(opener) == ()
    assert plain_lines(opener) == (
        "Pane: The editor pane",
        "Kind: pane",
        "Cursor: line 12",
        "State: the editor draft still open")
    save = book.pane_for("pane-files-main")
    assert save.cursor == ""
    assert "Cursor: unknown" in plain_lines(save)
    model = book.pane_for("pane-preview-main")
    assert model.kind == "tab"
    assert "Kind: tab" in plain_lines(model)
    quiet = book.pane_for("pane-quiet-main")
    assert pane_gaps(quiet) == ("no preserved state",)
    assert pane_passes(quiet) is False
    assert [g.pane_id for g in passing_panes(book)] == [
        "pane-editor-main", "pane-files-main",
        "pane-board-main", "pane-preview-main",
        "pane-help-main"]
    assert total_panes(book) == 6
    index = derive_index(book)
    assert [e.state for e in index.panes] == [
        "the editor draft still open", "the files still in view",
        "the board as it stood", "the preview still rendered",
        "help when you are stuck"]
    assert index.gaps == ("pane-quiet-main",)
    assert pane_for_state(book, "the editor draft still open").pane_id == (
        "pane-editor-main")
    assert pane_for_state(book, "triple resume") is None
    assert first_note(book).note_id == "note-note-editor"
    assert note_for_pane(
        book, "pane-editor-main", "note").note_id == (
            "note-note-editor")
    assert note_for_pane(book, "pane-nope") is None

# ---------------------------------------------------------------------
# The held pane: judged whole, its telling derived.
# ---------------------------------------------------------------------


def test_pane_record_round_trips():
    pane = _pane()
    assert validate_pane(pane) is pane
    rebuilt = build_pane(_stored_pane(pane))
    assert rebuilt == pane
    assert rebuilt.item_id == "pane-test"
    assert rebuilt.state == "the editor draft still open"
    record = pane_record(pane)
    assert record["type"] == "undo_pane"
    assert record["passes"] is True
    assert record["gaps"] == []


def test_pane_refuses_stored_judgements():
    for key in ("standing", "ready", "gaps", "segment", "verdict",
                "index", "panes", "coverage"):
        fields = _stored_pane(_pane())
        fields[key] = "stored"
        with pytest.raises(ValueError):
            build_pane(fields)
    fields = _stored_pane(_pane())
    fields["surprise"] = "stored"
    with pytest.raises(ValueError):
        build_pane(fields)


def test_pane_refuses_a_live_execution_claim():
    for key in ("restores_pane", "restored_pane", "reopens_view",
                "reopened_view", "destroys_work", "destroyed_work", "restores_now"):
        fields = _stored_pane(_pane())
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_pane(fields)
        assert "held as data alone" in str(caught.value)
    for key in ("posts_note", "shown_pane"):
        fields = _note().to_record()
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_note(fields)
        assert "held as data alone" in str(caught.value)
    record = _note(pane_id="pane-test")
    assert validate_note(record) is record
    assert record.pane_id == "pane-test"
    assert note_record(record)["type"] == "undo_note"


def test_pane_vocabularies_are_closed():
    assert _pane(kind="PANE").kind == "pane"
    assert _pane(cursor="").cursor == ""
    assert _pane(cursor=None).cursor == ""
    with pytest.raises(ValueError):
        _pane(kind="a hunch")
    with pytest.raises(ValueError):
        _pane(title="   ")
    with pytest.raises(ValueError):
        _pane(seq=0)
    with pytest.raises(ValueError):
        _pane(state=5)
    with pytest.raises(ValueError):
        _pane(cursor=5)
    with pytest.raises(ValueError):
        _pane(detail="   ")


def test_plain_telling_derives_from_the_panes_own_fields():
    pane = _pane(
        title="Test Pane", kind="view", cursor="", state="",
        detail="The words wait on a held pane.")
    lines = plain_lines(pane)
    assert lines[0] == "Pane: Test Pane"
    assert lines[1] == "Kind: view"
    assert lines[2] == "Cursor: unknown"
    assert lines[3] == "State: none"
    assert plain_words(pane) == pane_plain_words(pane)
    assert "Test Pane" in plain_words(pane)
    assert "held pane" in plain_words(pane)


def test_incomplete_pane_stands_named_in_its_gaps():
    pane = _pane(state="")
    assert pane_gaps(pane) == ("no preserved state",)
    assert pane_passes(pane) is False
    text = format_pane(pane)
    assert "stands unready" in text
    current_text = format_pane(_pane())
    assert "stands ready" in current_text


def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(_stored_view(view)) == view
    record = view_record(view)
    assert record["type"] == "undo_view"
    assert record["view_filter"] == "all"
    assert "shows all panes" in view_plain_words(view)
    assert "filter all" in format_view(view)
    with pytest.raises(ValueError):
        _view(view_filter="some")
    stance = _note()
    assert build_note(stance.to_record()) == stance
    assert "Undo note note pane-test" in format_note(stance)
    assert "executes no command" in format_note(stance)
    assert "toward the user" in note_plain_words(stance)
    with pytest.raises(ValueError):
        _note(stance="dance")

# ---------------------------------------------------------------------
# The index and the stance targets: derived at call time, never held.
# ---------------------------------------------------------------------


def test_index_is_derived_from_the_held_panes_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.pane_id for e in index.panes] == ["pane-test"]
    assert index.panes[0].state == "the editor draft still open"
    assert index.gaps == ("pane-quiet-only",)
    assert index_record(index)["type"] == "undo_index"
    assert index_record(book)["gaps"] == ["pane-quiet-only"]
    assert "1 preserved state" in index_plain_words(book)
    text = format_index(book)
    assert "Undo index" in text
    assert "the editor draft still open - A test pane (pane-test)" in text
    assert "pane-quiet-only" in text
    assert "executes no command" in text


def test_target_reaches_its_pane_and_an_unheld_target_reaches_nothing():
    book = _mixed_book()
    assert pane_for_state(book, "the editor draft still open").pane_id == "pane-test"
    assert pane_for_state(book, "triple resume") is None
    assert pane_for_state(book, "") is None
    assert "A test pane" in format_state(book, "the editor draft still open")
    assert "reaches nothing in this book" in format_state(
        book, "triple resume")


def test_first_note_is_held_as_data():
    book = _book(notes=[_note(), _note(
        note_id="note-two", seq=2, pane_id="pane-other",
        stance="question", title="The second stance")])
    assert first_note(book).note_id == "note-test"
    assert note_for_pane(book, "pane-other").note_id == (
        "note-two")
    assert note_for_pane(
        book, "pane-other", "question").note_id == "note-two"
    assert note_for_pane(book, "pane-other", "praise") is None
    bare = _book()
    assert first_note(bare) is None
    assert note_for_pane(bare, "pane-other") is None
    text = format_note(first_note(book))
    assert "held as data alone" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    stance = _note(
        pane_id="pane-x", stance="concern",
        target="a branched session")
    assert stance.stance == "concern"
    rebuilt = build_note(stance.to_record())
    assert rebuilt == stance
    assert rebuilt.pane_id == "pane-x"
    assert rebuilt.target == "a branched session"
    with pytest.raises(ValueError):
        _note(pane_id="   ")
    with pytest.raises(ValueError):
        _note(target="   ")
    with pytest.raises(ValueError):
        _note(stance="teleport")


def test_panel_is_derived_and_a_stored_panel_must_agree():
    book = _mixed_book()
    panel = derive_panel(book)
    assert isinstance(panel, UndoPanel)
    assert panel.total_items == 2
    assert panel.total_shown == 2
    assert validate_panel(panel, book) is panel
    assert build_panel(panel.to_record(), book).rows == panel.rows
    assert build_row(panel.rows[0], book.panes[0]) == panel.rows[0]
    assert validate_row(panel.rows[0], book.panes[0]) == panel.rows[0]
    tampered = dict(panel.to_record())
    tampered["total_shown"] = 99
    with pytest.raises(ValueError):
        build_panel(tampered, book)
    renamed = dict(panel.to_record())
    renamed["panel_id"] = "panel-renamed"
    assert build_panel(renamed, book).panel_id == "panel-renamed"
    record = panel_record(panel, book)
    assert record["type"] == "undo_panel"
    assert record["panel_id"] == panel.panel_id


def test_verdict_is_derived_from_the_shown_panes():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert isinstance(verdict, UndoVerdict)
    assert verdict.verdict == "strained"
    assert verdict.total_shown == 2
    assert verdict.passing_shown == 1
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    record = verdict_record(verdict, book)
    assert record["type"] == "undo_verdict"
    assert "strained" in verdict_plain_words(book)
    assert "strained" in format_verdict(book)


def test_verdict_open_and_shut_edges():
    whole = _book(panes=[_pane()])
    assert derive_verdict(whole).verdict == "open"
    absent_book = _book(panes=[_pane(state="")])
    assert derive_verdict(absent_book).verdict == "shut"
    none_shown = _book(
        panes=[_pane(state="")],
        views=[_view(view_filter="ready")])
    verdict = derive_verdict(none_shown)
    assert verdict.total_shown == 0
    assert verdict.verdict == "shut"


def test_shown_and_kind_readings():
    book = _mixed_book()
    assert [g.pane_id for g in shown_panes(book)] == [
        "pane-test", "pane-quiet-only"]
    ready_view = _view(
        view_id="view-r", seq=2, view_filter="ready")
    book2 = _book(
        panes=[_pane(), _pane(
            pane_id="pane-quiet-only", seq=2, title="A quiet pane",
            kind="view", cursor="", state="")],
        views=[_view(), ready_view])
    assert [g.pane_id for g in shown_panes(book2, ready_view)] == [
        "pane-test"]
    assert [g.pane_id for g in panes_for_kind(book2, "view")] == [
        "pane-quiet-only"]
    assert [g.pane_id for g in passing_panes(book2)] == [
        "pane-test"]
    assert total_panes(book2) == 2
    with pytest.raises(ValueError):
        panes_for_kind(book2, "the void")


def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(panes=[_pane(), _pane(seq=2)])
    with pytest.raises(ValueError):
        _book(panes=[_pane(), _pane(pane_id="pane-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(view_filter="ready")])
    with pytest.raises(ValueError) as caught:
        _book(notes=[_note(), _note(note_id="note-two", seq=2)])
    assert "one stance stands per pane target" in str(caught.value)
    fields = {
        "schema": UI_UNDO_SCHEMA, "slice": "M-198",
        "ui_undo": {"title": "A test undo book"},
        "panes": [_stored_pane(_pane())],
        "views": [_stored_view(_view())], "notes": [],
        "panels": [], "verdict": "open",
    }
    with pytest.raises(ValueError):
        build_book(fields)
    del fields["verdict"]
    fields["undo_index"] = "stored"
    with pytest.raises(ValueError):
        build_book(fields)
    raw = {
        "schema": UI_UNDO_SCHEMA, "slice": "M-198",
        "ui_undo": {"title": "A test undo book"},
        "panes": [], "views": [], "notes": [], "panels": [],
        "restores_pane": True,
    }
    with pytest.raises(ValueError) as caught:
        build_book(raw)
    assert "held as data alone" in str(caught.value)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / UI_UNDO_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "ui_undo.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_ui_undo_file(path)
    assert book.title == EXAMPLE_TITLE
    assert total_panes(book) == 6


def test_registry_holds_panes_and_views_one_by_one():
    registry = UiUndoRegistry()
    assert registry.list_items() == ()
    held = registry.register_pane(_pane())
    assert held.pane_id == "pane-test"
    registry.register_view(_view())
    assert [i.item_id if hasattr(i, "item_id") else i.view_id
            for i in registry.list_items()] == ["pane-test", "view-test"]
    assert registry.get_pane("pane-test").title == "A test pane"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.book().title == "An unheld undo book"
    with pytest.raises(ValueError):
        registry.register_pane(_pane(seq=2))
    with pytest.raises(ValueError):
        registry.register_pane(_pane(pane_id="pane-two"))
    with pytest.raises(KeyError):
        registry.get_pane("pane-nope")


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = UiUndoRegistry()
    book = _mixed_book()
    held = registry.register_book(book)
    assert held.title == "A test undo book"
    assert len(registry.list_panes()) == 2
    other = _book(panes=[_pane(
        pane_id="pane-x", seq=9, title="Other", state="the editor draft still open")],
        views=[_view(view_id="view-x", seq=9)])
    object.__setattr__(other, "title", "Another title")
    with pytest.raises(ValueError):
        registry.register_book(other)


def test_plain_words_and_formatters():
    book = _mixed_book()
    assert "kind: 'pane'" in format_book(book)
    assert "pane-quiet-only" in format_book(book, "view")
    assert "pane-test" not in format_book(book, "view")
    assert "Undo panel under view view-test" in format_panel(book)
    assert panel_plain_words(book).startswith(
        "The UI undo book holds 2 panes")
    screen = format_undo_screen(book)
    assert "UI Undo (M-198)" in screen
    assert PLAIN_EXPLANATION in screen
    assert "pane-quiet-sweep" not in screen
    assert "pane-quiet-only" in screen
    record = book_record(book)
    assert record["type"] == "undo_book"
    assert record["title"] == "A test undo book"
    assert len(record["panes"]) == 2
    panel = derive_panel(book)
    assert panel_record(panel, book)["rows"][0]["item_id"] == "pane-test"
    assert verdict_record(derive_verdict(book), book)["verdict"] == (
        "strained")
    pane_text = format_pane(book.panes[0])
    assert "Pane: A test pane" in pane_text
    assert "State: the editor draft still open" in pane_text


def test_parse_args_inspect_and_loader_targets():
    assert parse_undo_args("") == ("show", None)
    assert parse_undo_args("show") == ("show", None)
    assert parse_undo_args(None) == ("show", None)
    assert parse_undo_args("pane pane-test") == (
        "pane", "pane-test")
    assert parse_undo_args("state the editor draft still open") == (
        "state", "the editor draft still open")
    assert parse_undo_args("kind pane") == (
        "kind", "pane")
    assert parse_undo_args("view view-test") == ("view", "view-test")
    assert parse_undo_args("note note-test") == (
        "note", "note-test")
    assert parse_undo_args("index") == ("index", None)
    assert parse_undo_args("panel") == ("panel", None)
    assert parse_undo_args("verdict") == ("verdict", None)
    for bad in ("dance", "pane", "state", "kind", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_undo_args(bad)
    pane = _pane()
    assert inspect_pane_source(pane) == {
        "kind": "pane", "pane_id": "pane-test"}
    assert inspect_pane_source(_stored_pane(pane))["kind"] == (
        "pane")
    assert inspect_pane_source(_stored_view(_view()))["kind"] == (
        "view")
    assert inspect_pane_source(_note().to_record())["kind"] == (
        "note")
    assert inspect_pane_source(42)["kind"] == "unknown"
    book = load_ui_undo({
        "schema": UI_UNDO_SCHEMA, "slice": "M-198",
        "ui_undo": {"title": "A judged book"},
        "panes": [_stored_pane(_pane())],
        "views": [_stored_view(_view())], "notes": [], "panels": []})
    assert isinstance(book, UndoBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_ui_undo({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_ui_undo({"slice": "M-999"})
    built = build_pane(
        pane_id="pane-kw", seq=3, title="Kw Pane",
        kind="pane", cursor="ctrl+k",
        state="the editor draft still open", detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="undo-test")
    assert built.pane_id == "pane-kw"
    assert pane_passes(built) is True


# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-198 agent layer: the agent holds a undo book
# for the session, panes and views are published
# as session news through the checkpoint target
# (journal first, deduped per shape), the panel
# and verdict are derived at call time from the
# whole book under a view, never held, the index
# is derived from the book's held panes, and the
# stance targets are held as data beside them -
# holding one executes no command. This layer
# executes nothing, runs no action, navigates
# nowhere, opens no network and persists nothing
# beyond the session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _undo_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_undo_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / UI_UNDO_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "ui_undo.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestUndoAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.ui_undo_status()
        assert status["panes"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["ui_undo"]["title"] == EXAMPLE_TITLE
        assert len(status["ui_undo"]["panes"]) == 6
        assert len(status["ui_undo"]["views"]) == 2
        assert len(status["ui_undo"]["notes"]) == 2
        assert status["panel"]["total_items"] == 6
        assert status["panel"]["total_shown"] == 6
        assert status["panels"][0]["panel_id"] == "panel-m197-boundary"
        assert status["verdict"]["verdict"] == "strained"
        assert status["verdict"]["passing_shown"] == 5
        assert [e["state"] for e in status["index"]["panes"]] == ["the editor draft still open", "the files still in view", "the board as it stood", "the preview still rendered", "help when you are stuck"]
        assert status["index"]["gaps"] == ["pane-quiet-main"]
        assert status["first_note"]["note_id"] == "note-note-editor"
        assert "held as data alone" in status["rule"]
        assert "help when you are stuck" in status["plain_words"]
        assert "UI Undo (M-198)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._ui_undo_registry()
        assert agent._ui_undo_registry() is first
        assert agent._ui_undo_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.ui_undo_status()
        assert agent.get_undo_pane(
            "pane-editor-main").title == "The editor pane"
        assert agent.get_undo_view("view-undo").view_filter == "all"
        assert agent.get_undo_note(
            "note-note-editor").note_id == "note-note-editor"
        assert [a.pane_id for a in agent.undo_panes_for_kind(
            "pane")] == ["pane-editor-main", "pane-help-main"]
        assert [a.pane_id for a in agent.undo_panes_for_kind(
            "tab")] == ["pane-preview-main"]
        assert [a.pane_id for a in agent.undo_panes_passing()] == [
            "pane-editor-main", "pane-files-main",
            "pane-board-main", "pane-preview-main",
            "pane-help-main"]
        agent.ui_undo_panel()
        agent.ui_undo_verdict()
        agent.undo_index()
        agent.report_ui_undo()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("undo")] == []
        with pytest.raises(KeyError):
            agent.get_undo_pane("pane-nope")
        with pytest.raises(KeyError):
            agent.get_undo_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_undo_note("note-nope")
        with pytest.raises(ValueError):
            agent.undo_panes_for_kind("the void")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_undo_pane(_pane())
        status = agent.ui_undo_status()
        assert [a["pane_id"] for a in status["panes"]] == ["pane-test"]
        assert status["book"]["title"] == "An unheld undo book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["state"] for e in status["index"]["panes"]] == [
            "the editor draft still open"]
        assert status["first_note"] is None
        assert "pane-test" in status["screen"]

    def test_held_pane_never_falls_back_to_the_example(
            self, agent):
        agent.register_undo_pane(_pane())
        with pytest.raises(KeyError):
            agent.get_undo_pane("pane-editor-main")
        with pytest.raises(KeyError):
            agent.get_undo_view("view-undo")
        with pytest.raises(KeyError):
            agent.get_undo_note("modal")
        pane = agent.get_undo_pane("pane-test")
        assert pane.title == "A test pane"
        assert agent.ui_undo_book().title == (
            "An unheld undo book")

    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_undo_note("note-note-editor")
        assert first.note_id == "note-note-editor"
        assert first.pane_id == "pane-editor-main"
        status = agent.ui_undo_status()
        assert status["index"]["gaps"] == ["pane-quiet-main"]
        assert status["first_note"]["pane_id"] == (
            "pane-editor-main")
        assert status["first_note"]["stance"] == "note"


class TestUndoAgentHolding:
    def test_register_pane_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_undo_pane(_pane())
        assert result["pane"]["pane_id"] == "pane-test"
        assert result["record_news"]["type"] == "undo_pane"
        assert "pane-test" in result["screen"]
        events = _undo_events(store, session_id, "undo_pane")
        assert len(events) == 1
        agent.close()

    def test_duplicate_pane_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_undo_pane(_pane())
        with pytest.raises(ValueError):
            agent.register_undo_pane(_pane(seq=9))
        with pytest.raises(ValueError):
            agent.register_undo_pane(_pane(pane_id="pane-two"))
        events = _undo_events(store, session_id, "undo_pane")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_undo_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_undo_events(
            store, session_id, "undo_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_undo_pane(_pane())
        result = agent.view_undo("ready")
        assert result["view"]["view_filter"] == "ready"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "undo_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "open"
        assert len(_undo_events(
            store, session_id, "undo_view")) == 1
        assert len(_undo_events(
            store, session_id, "undo_panel")) == 1
        assert len(_undo_events(
            store, session_id, "undo_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_undo_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "undo_pane", "undo_view"]
        assert len(_undo_events(
            store, session_id, "undo_pane")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_undo_book()
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "undo_panel"
        assert result["index_record"]["gaps"] == [
            "pane-quiet-main"]
        with pytest.raises(ValueError):
            agent.record_undo_book()
        assert len(_undo_events(
            store, session_id, "undo_pane")) == 6
        assert len(_undo_events(
            store, session_id, "undo_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_undo_book_file(tmp_path)
        book = load_ui_undo_file(path)
        result = agent.record_undo_book(book)
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_ui_undo()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "strained"
        assert report["index"]["gaps"] == ["pane-quiet-main"]
        assert "pane-editor-main" in report["book_text"]
        assert "the editor draft still open - The editor pane (pane-editor-main)" in report["index_text"]
        agent.register_undo_pane(_pane())
        report = agent.report_ui_undo()
        assert report["book"]["title"] == "An unheld undo book"
        assert report["panel"] is None
        assert report["verdict"] is None


class TestUndoTerminalHeading:
    def test_show_pane_state_kind_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/uiundo")
        assert "UI Undo (M-198)" in text
        _, _, text = _slash(agent, "/uiundo pane pane-editor-main")
        assert "Pane: The editor pane" in text
        _, _, text = _slash(agent, "/uiundo state the editor draft still open")
        assert "the editor draft still open" in text
        _, _, text = _slash(agent, "/uiundo state triple resume")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/uiundo kind pane")
        assert "pane-editor-main" in text
        assert "pane-preview-main" not in text
        _, _, text = _slash(agent, "/uiundo view view-undo")
        assert "filter all" in text
        _, _, text = _slash(agent, "/uiundo note note-note-editor")
        assert "Undo note note pane-editor-main" in text
        _, _, text = _slash(agent, "/uiundo index")
        assert "Undo index" in text
        assert "pane-preview-main" in text
        _, _, text = _slash(agent, "/uiundo panel")
        assert "Undo panel under view view-undo" in text
        _, _, text = _slash(agent, "/uiundo verdict")
        assert "strained" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/uiundo [show|pane <pane-id>"
                "|state <state>|kind <kind>|view <view-id>"
                "|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/uiundo dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/uiundo pane pane-nope")
        assert "no pane named" in text


@pytest.fixture()
def undo_handler(agent, monkeypatch):
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


def _undo_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestUndoCommand:
    def test_show_is_default(self, undo_handler, agent):
        undo_handler._handle_uiundo("")
        assert "UI Undo (M-198)" in (
            _undo_published_text(undo_handler))

    def test_pane_state_kind_view_note_index_panel_verdict(
            self, undo_handler, agent):
        undo_handler._handle_uiundo("pane pane-editor-main")
        assert "Pane: The editor pane" in _undo_published_text(
            undo_handler)
        undo_handler._handle_uiundo("state the editor draft still open")
        assert "the editor draft still open" in _undo_published_text(
            undo_handler)
        undo_handler._handle_uiundo("kind pane")
        assert "pane-editor-main" in _undo_published_text(undo_handler)
        undo_handler._handle_uiundo("view view-undo")
        assert "filter all" in _undo_published_text(undo_handler)
        undo_handler._handle_uiundo("note note-note-editor")
        assert "Undo note note pane-editor-main" in _undo_published_text(undo_handler)
        undo_handler._handle_uiundo("index")
        assert "Undo index" in _undo_published_text(undo_handler)
        undo_handler._handle_uiundo("panel")
        assert "Undo panel under view" in _undo_published_text(
            undo_handler)
        undo_handler._handle_uiundo("verdict")
        assert "strained" in _undo_published_text(undo_handler)

    def test_bad_grammar_is_published(
            self, undo_handler, agent):
        undo_handler._handle_uiundo("dance party")
        assert USAGE in _undo_published_text(undo_handler)
        undo_handler._handle_uiundo("pane pane-nope")
        assert "no pane named" in _undo_published_text(undo_handler)


class TestChatScreenRoutingUndo:
    def test_undo_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/uiundo panel", _FakeLog())
        assert calls == [("/uiundo", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/uiundo[/green] - show UI undo (M-198)" in (
            text)
        assert ('"/uiundo": "Usage: /uiundo | '
                '/uiundo pane <pane-id>') in text


class TestUndoDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.ui_undo_panel()
        assert panel.total_shown == 6
        assert panel.panel_id == "panel-view-undo"
        verdict = agent.ui_undo_verdict()
        assert verdict.verdict == "strained"
        found = agent.ui_undo_verdict("view-ready")
        assert found.verdict == "open"
        assert found.passing_shown == 5
        agent.register_undo_pane(_pane())
        with pytest.raises(ValueError):
            agent.ui_undo_panel()
        with pytest.raises(ValueError):
            agent.ui_undo_verdict()

    def test_view_target_over_an_unshown_filter_is_shut(self, agent):
        agent.register_undo_pane(_pane(state=""))
        result = agent.view_undo("ready")
        assert result["verdict_record"]["verdict"] == "shut"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.undo_index()
        assert [e["state"] for e in result["index"]["panes"]] == ["the editor draft still open", "the files still in view", "the board as it stood", "the preview still rendered", "help when you are stuck"]
        assert result["index"]["gaps"] == ["pane-quiet-main"]
        assert "the editor draft still open - The editor pane (pane-editor-main)" in (
            result["index_text"])
        pane = agent.get_undo_pane("pane-quiet-main")
        assert pane_gaps(pane) == ("no preserved state",)
        assert pane_passes(pane) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("undo")] == []
        agent.close()
