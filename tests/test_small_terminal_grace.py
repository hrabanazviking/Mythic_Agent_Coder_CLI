"""M-194 Small-Terminal Grace - pure-layer tests.

TIER: integration

The pure layer is the folding, held as data:
one record per fold, held whole as a card -
under its surface, its kind in the closed
vocabulary (full, folded, stacked, hidden,
summary), its width and its height held
honestly (unknown stays empty, never
invented), the work it preserves, named as
data, and its detail - the notes held as data
beside them, each naming its fold, its stance
and its target, and the fold index derived at
call time from the held folds alone, never
stored where it could drift. A fold naming
no preserved work stands losable, named
in its gaps; two folds standing for one
fold id refuse by name, and one stance
record stands per fold stance. A record
claiming a terminal was actually resized, a
pane actually folded or work actually
rendered refuses by name, and a stored
index or verdict refuses by name. The panel
is derived for one held view and the verdict
is derived for the whole book under one view.
The shipped example book is held in a data
file, and a loader reads a book from any file.
The M-171 charter names this slice on NO row,
and the tests pin that absence live. This
layer resizes no terminal, folds no pane,
renders no work and opens no network: it
holds the folding as data and tells it.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.small_terminal_grace import (
    KINDS,
    EXAMPLE_PRESERVES,
    STANCES,
    INDEX_ACTION,
    SMALL_TERMINAL_GRACE_RESOURCE,
    SMALL_TERMINAL_GRACE_SCHEMA,
    SMALL_TERMINAL_GRACE_SLICE,
    GRACE_RULE,
    PLAIN_EXPLANATION,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    PRESERVE_WORDS,
    FoldCard,
    NoteRecord,
    FoldBook,
    FoldPanel,
    SmallTerminalGraceRegistry,
    FoldVerdict,
    FoldView,
    book_record,
    build_book,
    build_fold,
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
    format_fold,
    format_index,
    format_note,
    format_grace_screen,
    format_panel,
    format_preserves,
    format_verdict,
    format_view,
    fold_for_preserves,
    fold_gaps,
    fold_passes,
    fold_plain_words,
    fold_record,
    folds_for_kind,
    index_plain_words,
    index_record,
    inspect_fold_source,
    note_for_fold,
    note_plain_words,
    note_record,
    load_small_terminal_grace,
    load_small_terminal_grace_file,
    normalize_kind,
    normalize_stance,
    normalize_view_filter,
    panel_plain_words,
    panel_record,
    parse_grace_args,
    passing_folds,
    plain_lines,
    plain_words,
    shown_folds,
    total_folds,
    validate_book,
    validate_fold,
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
EXAMPLE_TITLE = "Small-terminal grace at the M-193 slice boundary"


def _fold(**overrides):
    fields = {
        "fold_id": "fold-test",
        "seq": 1,
        "surface": "A test fold",
        "kind": "full",
        "width": "80 columns",
        "height": "24 rows",
        "preserves": "the work in progress",
        "detail": "A test fold held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "fold-test",
    }
    fields.update(overrides)
    return build_fold(fields)


def _stored_fold(fold):
    return fold.to_record()


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "fold-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _stored_view(view):
    return view.to_record()


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "fold_id": "fold-test",
        "stance": "note",
        "target": "the user",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "fold-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _book(folds=None, views=None, notes=None, **overrides):
    fields = {
        "schema": SMALL_TERMINAL_GRACE_SCHEMA,
        "slice": "M-194",
        "small_terminal_grace": {"title": "A test fold book"},
        "folds": [_stored_fold(item) for item in (
            folds if folds is not None else [_fold()])],
        "views": [_stored_view(item) for item in (
            views if views is not None else [_view()])],
        "notes": [item.to_record() for item in (notes or [])],
        "panels": [],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(folds=[
        _fold(),
        _fold(fold_id="fold-terminal-only", seq=2,
              surface="A hidden fold", kind="hidden",
              width="", height="", preserves=""),
    ])


def test_shipped_book_loads_with_pinned_shape():
    book = load_small_terminal_grace()
    assert book.title == EXAMPLE_TITLE
    assert book.fold_ids() == (
        "fold-work-wide", "fold-board-wide",
        "fold-crew-phone", "fold-files-phone",
        "fold-terminal-phone", "fold-chat-wide")
    assert [v.view_id for v in book.views] == [
        "view-grace", "view-preserved"]
    assert [m.fold_id for m in book.notes] == [
        "fold-work-wide",
        "fold-board-wide"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m193-boundary"
    assert panel.as_of == "2026-11-10"
    assert [row.item_id for row in panel.rows] == list(book.fold_ids())
    derived = derive_panel(book, "view-grace")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 6
    assert panel.total_shown == derived.total_shown == 6
    assert {c.standing: c.items for c in panel.target_counts} == {
        "preserved": 5, "losable": 1}
    assert derive_verdict(book, "view-grace").verdict == "strained"
    assert derive_verdict(book, "view-grace").passing_shown == 5
    assert derive_verdict(book, "view-preserved").verdict == "open"
    assert derive_verdict(book, "view-preserved").passing_shown == 5
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / SMALL_TERMINAL_GRACE_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == SMALL_TERMINAL_GRACE_SCHEMA
    assert raw["slice"] == "M-194"
    assert "verdict" not in raw
    assert "grace_index" not in raw


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-194")]
    assert slice_.title == "Small-terminal grace"
    assert slice_.part == 8
    assert "folds gracefully" in slice_.summary
    assert "phone-over-SSH" in slice_.summary
    assert "without losing the work" in slice_.summary
    assert SMALL_TERMINAL_GRACE_SLICE == "M-194"


def test_charter_does_not_name_m194():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert owners.count("M-187") == 1
    assert "M-194" not in owners


def test_closed_vocabularies():
    assert PRESERVE_WORDS == ("preserved", "losable")
    assert KINDS == ("full", "folded", "stacked", "hidden", "summary")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "preserved", "losable")
    assert VERDICT_WORDS == ("open", "strained", "shut")
    assert INDEX_ACTION == "index"
    assert EXAMPLE_PRESERVES == "the work in progress"
    assert normalize_kind("FULL") == "full"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    with pytest.raises(ValueError):
        normalize_kind("the void")
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    assert "held as data alone" in GRACE_RULE
    assert "resizes no terminal" in GRACE_RULE
    assert "M-194" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /smallterminal")


def test_shipped_book_judged_honestly_as_data():
    book = load_small_terminal_grace()
    wordmark = book.fold_for("fold-work-wide")
    assert fold_passes(wordmark) is True
    assert fold_gaps(wordmark) == ()
    assert plain_lines(wordmark) == (
        "Fold: Work pane on the wide terminal",
        "Kind: full",
        "Width: 80 columns",
        "Height: 24 rows",
        "Preserves: the work in progress")
    loading = book.fold_for("fold-board-wide")
    assert loading.width == ""
    assert "Width: unknown" in plain_lines(loading)
    art = book.fold_for("fold-crew-phone")
    assert art.height == ""
    assert "Height: unknown" in plain_lines(art)
    sweep = book.fold_for("fold-terminal-phone")
    assert fold_gaps(sweep) == ("no preserved work",)
    assert fold_passes(sweep) is False
    assert [g.fold_id for g in passing_folds(book)] == [
        "fold-work-wide", "fold-board-wide",
        "fold-crew-phone", "fold-files-phone",
        "fold-chat-wide"]
    assert total_folds(book) == 6
    index = derive_index(book)
    assert [e.preserves for e in index.entries] == [
        "the work in progress", "the board and its slice standings",
        "the crew roster and each worker's slice", "the file list, folded to names and standings",
        "the conversation and the question on the floor"]
    assert index.gaps == ("fold-terminal-phone",)
    assert fold_for_preserves(book, "the work in progress").fold_id == (
        "fold-work-wide")
    assert fold_for_preserves(book, "triple resume") is None
    assert first_note(book).note_id == "note-note-work"
    assert note_for_fold(
        book, "fold-work-wide", "note").note_id == (
            "note-note-work")
    assert note_for_fold(book, "fold-nope") is None


# ---------------------------------------------------------------------
# The held fold: judged whole, its telling derived.
# ---------------------------------------------------------------------


def test_fold_record_round_trips():
    fold = _fold()
    assert validate_fold(fold) is fold
    rebuilt = build_fold(_stored_fold(fold))
    assert rebuilt == fold
    assert rebuilt.item_id == "fold-test"
    assert rebuilt.preserves == "the work in progress"
    record = fold_record(fold)
    assert record["type"] == "grace_fold"
    assert record["passes"] is True
    assert record["gaps"] == []


def test_fold_refuses_stored_judgements():
    for key in ("standing", "preserved", "gaps", "segment", "verdict",
                "index", "entries", "coverage"):
        fields = _stored_fold(_fold())
        fields[key] = "stored"
        with pytest.raises(ValueError):
            build_fold(fields)
    fields = _stored_fold(_fold())
    fields["surprise"] = "stored"
    with pytest.raises(ValueError):
        build_fold(fields)


def test_fold_refuses_a_live_session_claim():
    for key in ("shows_fold", "shown_fold", "plays_fold",
                "performed_fold", "posted_note"):
        fields = _stored_fold(_fold())
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_fold(fields)
        assert "held as data alone" in str(caught.value)
    for key in ("posts_note", "shown_fold"):
        fields = _note().to_record()
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_note(fields)
        assert "held as data alone" in str(caught.value)
    record = _note(fold_id="fold-test")
    assert validate_note(record) is record
    assert record.fold_id == "fold-test"
    assert note_record(record)["type"] == "grace_note"


def test_fold_vocabularies_are_closed():
    assert _fold(kind="FULL").kind == "full"
    assert _fold(width="").width == ""
    assert _fold(height=None).height == ""
    with pytest.raises(ValueError):
        _fold(kind="a hunch")
    with pytest.raises(ValueError):
        _fold(surface="   ")
    with pytest.raises(ValueError):
        _fold(seq=0)
    with pytest.raises(ValueError):
        _fold(preserves=5)
    with pytest.raises(ValueError):
        _fold(width=5)
    with pytest.raises(ValueError):
        _fold(height=5)
    with pytest.raises(ValueError):
        _fold(detail="   ")


def test_plain_telling_derives_from_the_folds_own_fields():
    fold = _fold(
        surface="Test Fold", kind="folded", width="", height="",
        preserves="", detail="The preserves waits on a held fold.")
    lines = plain_lines(fold)
    assert lines[0] == "Fold: Test Fold"
    assert lines[1] == "Kind: folded"
    assert lines[2] == "Width: unknown"
    assert lines[3] == "Height: unknown"
    assert lines[4] == "Preserves: none"
    assert plain_words(fold) == fold_plain_words(fold)
    assert "Test Fold" in plain_words(fold)
    assert "held fold" in plain_words(fold)


def test_losable_fold_stands_named_in_its_gaps():
    fold = _fold(preserves="")
    assert fold_gaps(fold) == ("no preserved work",)
    assert fold_passes(fold) is False
    text = format_fold(fold)
    assert "stands losable" in text
    current_text = format_fold(_fold())
    assert "stands preserved" in current_text


def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(_stored_view(view)) == view
    record = view_record(view)
    assert record["type"] == "grace_view"
    assert record["view_filter"] == "all"
    assert "shows all folds" in view_plain_words(view)
    assert "filter all" in format_view(view)
    with pytest.raises(ValueError):
        _view(view_filter="some")
    stance = _note()
    assert build_note(stance.to_record()) == stance
    assert "Fold note note fold-test" in format_note(stance)
    assert "resizes no terminal" in format_note(stance)
    assert "toward the user" in note_plain_words(stance)
    with pytest.raises(ValueError):
        _note(stance="dance")


# ---------------------------------------------------------------------
# The index and the stance targets: derived at call time, never held.
# ---------------------------------------------------------------------


def test_index_is_derived_from_the_held_folds_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.fold_id for e in index.entries] == ["fold-test"]
    assert index.entries[0].preserves == "the work in progress"
    assert index.gaps == ("fold-terminal-only",)
    assert index_record(index)["type"] == "grace_index"
    assert index_record(book)["gaps"] == ["fold-terminal-only"]
    assert "1 preserved works" in index_plain_words(book)
    text = format_index(book)
    assert "Fold index" in text
    assert "the work in progress - A test fold (fold-test)" in text
    assert "fold-terminal-only" in text
    assert "resizes no terminal" in text


def test_target_reaches_its_fold_and_an_unheld_target_reaches_nothing():
    book = _mixed_book()
    assert fold_for_preserves(book, "the work in progress").fold_id == "fold-test"
    assert fold_for_preserves(book, "triple resume") is None
    assert fold_for_preserves(book, "") is None
    assert "A test fold" in format_preserves(book, "the work in progress")
    assert "reaches nothing in this book" in format_preserves(
        book, "triple resume")


def test_first_note_is_held_as_data():
    book = _book(notes=[_note(), _note(
        note_id="note-two", seq=2, fold_id="fold-other",
        stance="question", title="The second stance")])
    assert first_note(book).note_id == "note-test"
    assert note_for_fold(book, "fold-other").note_id == (
        "note-two")
    assert note_for_fold(
        book, "fold-other", "question").note_id == "note-two"
    assert note_for_fold(book, "fold-other", "praise") is None
    bare = _book()
    assert first_note(bare) is None
    assert note_for_fold(bare, "fold-other") is None
    text = format_note(first_note(book))
    assert "held as data alone" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    stance = _note(
        fold_id="fold-x", stance="concern",
        target="a branched session")
    assert stance.stance == "concern"
    rebuilt = build_note(stance.to_record())
    assert rebuilt == stance
    assert rebuilt.fold_id == "fold-x"
    assert rebuilt.target == "a branched session"
    with pytest.raises(ValueError):
        _note(fold_id="   ")
    with pytest.raises(ValueError):
        _note(target="   ")
    with pytest.raises(ValueError):
        _note(stance="teleport")


def test_panel_is_derived_and_a_stored_panel_must_agree():
    book = _mixed_book()
    panel = derive_panel(book)
    assert isinstance(panel, FoldPanel)
    assert panel.total_items == 2
    assert panel.total_shown == 2
    assert validate_panel(panel, book) is panel
    assert build_panel(panel.to_record(), book).rows == panel.rows
    assert build_row(panel.rows[0], book.folds[0]) == panel.rows[0]
    assert validate_row(panel.rows[0], book.folds[0]) == panel.rows[0]
    tampered = dict(panel.to_record())
    tampered["total_shown"] = 99
    with pytest.raises(ValueError):
        build_panel(tampered, book)
    renamed = dict(panel.to_record())
    renamed["panel_id"] = "panel-renamed"
    assert build_panel(renamed, book).panel_id == "panel-renamed"
    record = panel_record(panel, book)
    assert record["type"] == "grace_panel"
    assert record["panel_id"] == panel.panel_id


def test_verdict_is_derived_from_the_shown_folds():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert isinstance(verdict, FoldVerdict)
    assert verdict.verdict == "strained"
    assert verdict.total_shown == 2
    assert verdict.passing_shown == 1
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    record = verdict_record(verdict, book)
    assert record["type"] == "grace_verdict"
    assert "strained" in verdict_plain_words(book)
    assert "strained" in format_verdict(book)


def test_verdict_open_and_shut_edges():
    whole = _book(folds=[_fold()])
    assert derive_verdict(whole).verdict == "open"
    absent_book = _book(folds=[_fold(preserves="")])
    assert derive_verdict(absent_book).verdict == "shut"
    none_shown = _book(
        folds=[_fold(preserves="")],
        views=[_view(view_filter="preserved")])
    verdict = derive_verdict(none_shown)
    assert verdict.total_shown == 0
    assert verdict.verdict == "shut"


def test_shown_and_kind_readings():
    book = _mixed_book()
    assert [g.fold_id for g in shown_folds(book)] == [
        "fold-test", "fold-terminal-only"]
    preserved_view = _view(
        view_id="view-r", seq=2, view_filter="preserved")
    book2 = _book(
        folds=[_fold(), _fold(
            fold_id="fold-terminal-only", seq=2, surface="A hidden fold",
            kind="hidden", width="", height="", preserves="")],
        views=[_view(), preserved_view])
    assert [g.fold_id for g in shown_folds(book2, preserved_view)] == [
        "fold-test"]
    assert [g.fold_id for g in folds_for_kind(book2, "hidden")] == [
        "fold-terminal-only"]
    assert [g.fold_id for g in passing_folds(book2)] == [
        "fold-test"]
    assert total_folds(book2) == 2
    with pytest.raises(ValueError):
        folds_for_kind(book2, "the void")


def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(folds=[_fold(), _fold(seq=2)])
    with pytest.raises(ValueError):
        _book(folds=[_fold(), _fold(fold_id="fold-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(view_filter="preserved")])
    with pytest.raises(ValueError) as caught:
        _book(notes=[_note(), _note(note_id="note-two", seq=2)])
    assert "one stance stands per session target" in str(caught.value)
    fields = {
        "schema": SMALL_TERMINAL_GRACE_SCHEMA, "slice": "M-194",
        "small_terminal_grace": {"title": "A test fold book"},
        "folds": [_stored_fold(_fold())],
        "views": [_stored_view(_view())], "notes": [],
        "panels": [], "verdict": "open",
    }
    with pytest.raises(ValueError):
        build_book(fields)
    del fields["verdict"]
    fields["grace_index"] = "stored"
    with pytest.raises(ValueError):
        build_book(fields)
    raw = {
        "schema": SMALL_TERMINAL_GRACE_SCHEMA, "slice": "M-194",
        "small_terminal_grace": {"title": "A test fold book"},
        "folds": [], "views": [], "notes": [], "panels": [],
        "shows_fold": True,
    }
    with pytest.raises(ValueError) as caught:
        build_book(raw)
    assert "held as data alone" in str(caught.value)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / SMALL_TERMINAL_GRACE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "small_terminal_grace.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_small_terminal_grace_file(path)
    assert book.title == EXAMPLE_TITLE
    assert total_folds(book) == 6


def test_registry_holds_folds_and_views_one_by_one():
    registry = SmallTerminalGraceRegistry()
    assert registry.list_items() == ()
    held = registry.register_fold(_fold())
    assert held.fold_id == "fold-test"
    registry.register_view(_view())
    assert [i.item_id if hasattr(i, "item_id") else i.view_id
            for i in registry.list_items()] == ["fold-test", "view-test"]
    assert registry.get_fold("fold-test").surface == "A test fold"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.book().title == "An unheld fold book"
    with pytest.raises(ValueError):
        registry.register_fold(_fold(seq=2))
    with pytest.raises(ValueError):
        registry.register_fold(_fold(fold_id="fold-two"))
    with pytest.raises(KeyError):
        registry.get_fold("fold-nope")


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = SmallTerminalGraceRegistry()
    book = _mixed_book()
    held = registry.register_book(book)
    assert held.title == "A test fold book"
    assert len(registry.list_folds()) == 2
    other = _book(folds=[_fold(
        fold_id="fold-x", seq=9, surface="Other", preserves="the work in progress")],
        views=[_view(view_id="view-x", seq=9)])
    object.__setattr__(other, "title", "Another title")
    with pytest.raises(ValueError):
        registry.register_book(other)


def test_plain_words_and_formatters():
    book = _mixed_book()
    assert "kind: 'full'" in format_book(book)
    assert "fold-terminal-only" in format_book(book, "hidden")
    assert "fold-test" not in format_book(book, "hidden")
    assert "Grace panel under view view-test" in format_panel(book)
    assert panel_plain_words(book).startswith(
        "The grace book holds 2 folds")
    screen = format_grace_screen(book)
    assert "Small-Terminal Grace (M-194)" in screen
    assert PLAIN_EXPLANATION in screen
    assert "fold-terminal-sweep" not in screen
    assert "fold-terminal-only" in screen
    record = book_record(book)
    assert record["type"] == "grace_book"
    assert record["title"] == "A test fold book"
    assert len(record["folds"]) == 2
    panel = derive_panel(book)
    assert panel_record(panel, book)["rows"][0]["item_id"] == "fold-test"
    assert verdict_record(derive_verdict(book), book)["verdict"] == (
        "strained")
    fold_text = format_fold(book.folds[0])
    assert "Fold: A test fold" in fold_text
    assert "Preserves: the work in progress" in fold_text


def test_parse_args_inspect_and_loader_targets():
    assert parse_grace_args("") == ("show", None)
    assert parse_grace_args("show") == ("show", None)
    assert parse_grace_args(None) == ("show", None)
    assert parse_grace_args("fold fold-test") == (
        "fold", "fold-test")
    assert parse_grace_args("preserves the work in progress") == (
        "preserves", "the work in progress")
    assert parse_grace_args("kind full") == (
        "kind", "full")
    assert parse_grace_args("view view-test") == ("view", "view-test")
    assert parse_grace_args("note note-test") == (
        "note", "note-test")
    assert parse_grace_args("index") == ("index", None)
    assert parse_grace_args("panel") == ("panel", None)
    assert parse_grace_args("verdict") == ("verdict", None)
    for bad in ("dance", "fold", "preserves", "kind", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_grace_args(bad)
    fold = _fold()
    assert inspect_fold_source(fold) == {
        "kind": "fold", "fold_id": "fold-test"}
    assert inspect_fold_source(_stored_fold(fold))["kind"] == (
        "fold")
    assert inspect_fold_source(_stored_view(_view()))["kind"] == (
        "view")
    assert inspect_fold_source(_note().to_record())["kind"] == (
        "note")
    assert inspect_fold_source(42)["kind"] == "unknown"
    book = load_small_terminal_grace({
        "schema": SMALL_TERMINAL_GRACE_SCHEMA, "slice": "M-194",
        "small_terminal_grace": {"title": "A judged book"},
        "folds": [_stored_fold(_fold())],
        "views": [_stored_view(_view())], "notes": [], "panels": []})
    assert isinstance(book, FoldBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_small_terminal_grace({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_small_terminal_grace({"slice": "M-999"})
    built = build_fold(
        fold_id="fold-kw", seq=3, surface="Kw Fold",
        kind="full", width="80 columns", height="24 rows",
        preserves="the work in progress", detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="fold-test")
    assert built.fold_id == "fold-kw"
    assert fold_passes(built) is True


# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-194 agent layer: the agent holds a fold book
# for the session, folds and views are published
# as session news through the checkpoint target
# (journal first, deduped per shape), the panel
# and verdict are derived at call time from the
# whole book under a view, never held, the index
# is derived from the book's held folds, and the
# stance targets are held as data beside them -
# holding one resumes no session. This layer
# resumes nothing, renders no live UI, exports
# nothing and persists nothing beyond the
# session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _fold_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_fold_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / SMALL_TERMINAL_GRACE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "small_terminal_grace.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestGraceAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.small_terminal_grace_status()
        assert status["folds"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["small_terminal_grace"]["title"] == EXAMPLE_TITLE
        assert len(status["small_terminal_grace"]["folds"]) == 6
        assert len(status["small_terminal_grace"]["views"]) == 2
        assert len(status["small_terminal_grace"]["notes"]) == 2
        assert status["panel"]["total_items"] == 6
        assert status["panel"]["total_shown"] == 6
        assert status["panels"][0]["panel_id"] == "panel-m193-boundary"
        assert status["verdict"]["verdict"] == "strained"
        assert status["verdict"]["passing_shown"] == 5
        assert [e["preserves"] for e in status["index"]["entries"]] == ["the work in progress", "the board and its slice standings", "the crew roster and each worker's slice", "the file list, folded to names and standings", "the conversation and the question on the floor"]
        assert status["index"]["gaps"] == ["fold-terminal-phone"]
        assert status["first_note"]["note_id"] == "note-note-work"
        assert "held as data alone" in status["rule"]
        assert "the conversation and the question on the floor" in status["plain_words"]
        assert "Small-Terminal Grace (M-194)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._small_terminal_grace_registry()
        assert agent._small_terminal_grace_registry() is first
        assert agent._small_terminal_grace_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.small_terminal_grace_status()
        assert agent.get_grace_fold(
            "fold-work-wide").surface == "Work pane on the wide terminal"
        assert agent.get_grace_view("view-grace").view_filter == "all"
        assert agent.get_grace_note(
            "note-note-work").note_id == "note-note-work"
        assert [a.fold_id for a in agent.grace_folds_for_kind(
            "full")] == ["fold-work-wide", "fold-chat-wide"]
        assert [a.fold_id for a in agent.grace_folds_for_kind(
            "folded")] == ["fold-board-wide"]
        assert [a.fold_id for a in agent.grace_folds_passing()] == [
            "fold-work-wide", "fold-board-wide",
            "fold-crew-phone", "fold-files-phone",
            "fold-chat-wide"]
        agent.small_terminal_grace_panel()
        agent.small_terminal_grace_verdict()
        agent.grace_index()
        agent.report_small_terminal_grace()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("grace")
                or e["type"] == "grace_fold"] == []
        with pytest.raises(KeyError):
            agent.get_grace_fold("fold-nope")
        with pytest.raises(KeyError):
            agent.get_grace_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_grace_note("note-nope")
        with pytest.raises(ValueError):
            agent.grace_folds_for_kind("the void")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_grace_fold(_fold())
        status = agent.small_terminal_grace_status()
        assert [a["fold_id"] for a in status["folds"]] == ["fold-test"]
        assert status["book"]["title"] == "An unheld fold book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["preserves"] for e in status["index"]["entries"]] == [
            "the work in progress"]
        assert status["first_note"] is None
        assert "fold-test" in status["screen"]

    def test_held_fold_never_falls_back_to_the_example(
            self, agent):
        agent.register_grace_fold(_fold())
        with pytest.raises(KeyError):
            agent.get_grace_fold("fold-work-wide")
        with pytest.raises(KeyError):
            agent.get_grace_view("view-grace")
        with pytest.raises(KeyError):
            agent.get_grace_note("modal")
        fold = agent.get_grace_fold("fold-test")
        assert fold.surface == "A test fold"
        assert agent.small_terminal_grace_book().title == (
            "An unheld fold book")

    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_grace_note("note-note-work")
        assert first.note_id == "note-note-work"
        assert first.fold_id == "fold-work-wide"
        status = agent.small_terminal_grace_status()
        assert status["index"]["gaps"] == ["fold-terminal-phone"]
        assert status["first_note"]["fold_id"] == (
            "fold-work-wide")
        assert status["first_note"]["stance"] == "note"


class TestGraceAgentHolding:
    def test_register_fold_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_grace_fold(_fold())
        assert result["fold"]["fold_id"] == "fold-test"
        assert result["record_news"]["type"] == "grace_fold"
        assert "fold-test" in result["screen"]
        events = _fold_events(store, session_id, "grace_fold")
        assert len(events) == 1
        agent.close()

    def test_duplicate_fold_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_grace_fold(_fold())
        with pytest.raises(ValueError):
            agent.register_grace_fold(_fold(seq=9))
        with pytest.raises(ValueError):
            agent.register_grace_fold(_fold(fold_id="fold-two"))
        events = _fold_events(store, session_id, "grace_fold")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_grace_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_fold_events(
            store, session_id, "grace_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_grace_fold(_fold())
        result = agent.view_grace("preserved")
        assert result["view"]["view_filter"] == "preserved"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "grace_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "open"
        assert len(_fold_events(
            store, session_id, "grace_view")) == 1
        assert len(_fold_events(
            store, session_id, "grace_panel")) == 1
        assert len(_fold_events(
            store, session_id, "grace_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_grace_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "grace_fold", "grace_view"]
        assert len(_fold_events(
            store, session_id, "grace_fold")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_grace_book()
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "grace_panel"
        assert result["index_record"]["gaps"] == [
            "fold-terminal-phone"]
        with pytest.raises(ValueError):
            agent.record_grace_book()
        assert len(_fold_events(
            store, session_id, "grace_fold")) == 6
        assert len(_fold_events(
            store, session_id, "grace_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_fold_book_file(tmp_path)
        book = load_small_terminal_grace_file(path)
        result = agent.record_grace_book(book)
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_small_terminal_grace()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "strained"
        assert report["index"]["gaps"] == ["fold-terminal-phone"]
        assert "fold-work-wide" in report["book_text"]
        assert "the work in progress - Work pane on the wide terminal (fold-work-wide)" in report["index_text"]
        agent.register_grace_fold(_fold())
        report = agent.report_small_terminal_grace()
        assert report["book"]["title"] == "An unheld fold book"
        assert report["panel"] is None
        assert report["verdict"] is None


class TestGraceTerminalSurface:
    def test_show_fold_target_kind_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/smallterminal")
        assert "Small-Terminal Grace (M-194)" in text
        _, _, text = _slash(agent, "/smallterminal fold fold-work-wide")
        assert "Fold: Work pane on the wide terminal" in text
        _, _, text = _slash(agent, "/smallterminal preserves the work in progress")
        assert "the work in progress" in text
        _, _, text = _slash(agent, "/smallterminal preserves triple resume")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/smallterminal kind full")
        assert "fold-work-wide" in text
        assert "fold-terminal-phone" not in text
        _, _, text = _slash(agent, "/smallterminal view view-grace")
        assert "filter all" in text
        _, _, text = _slash(agent, "/smallterminal note note-note-work")
        assert "Fold note note fold-work-wide" in text
        _, _, text = _slash(agent, "/smallterminal index")
        assert "Fold index" in text
        assert "fold-files-phone" in text
        _, _, text = _slash(agent, "/smallterminal panel")
        assert "Grace panel under view view-grace" in text
        _, _, text = _slash(agent, "/smallterminal verdict")
        assert "strained" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/smallterminal [show|fold <fold-id>"
                "|preserves <preserves>|kind <kind>|view <view-id>"
                "|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/smallterminal dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/smallterminal fold fold-nope")
        assert "no fold named" in text


@pytest.fixture()
def grace_handler(agent, monkeypatch):
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


def _fold_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestGraceCommand:
    def test_show_is_default(self, grace_handler, agent):
        grace_handler._handle_smallterminal("")
        assert "Small-Terminal Grace (M-194)" in (
            _fold_published_text(grace_handler))

    def test_fold_target_kind_view_note_index_panel_verdict(
            self, grace_handler, agent):
        grace_handler._handle_smallterminal("fold fold-work-wide")
        assert "Fold: Work pane on the wide terminal" in _fold_published_text(
            grace_handler)
        grace_handler._handle_smallterminal("preserves the work in progress")
        assert "the work in progress" in _fold_published_text(
            grace_handler)
        grace_handler._handle_smallterminal("kind full")
        assert "fold-work-wide" in _fold_published_text(grace_handler)
        grace_handler._handle_smallterminal("view view-grace")
        assert "filter all" in _fold_published_text(grace_handler)
        grace_handler._handle_smallterminal("note note-note-work")
        assert "Fold note note fold-work-wide" in _fold_published_text(grace_handler)
        grace_handler._handle_smallterminal("index")
        assert "Fold index" in _fold_published_text(grace_handler)
        grace_handler._handle_smallterminal("panel")
        assert "Grace panel under view" in _fold_published_text(
            grace_handler)
        grace_handler._handle_smallterminal("verdict")
        assert "strained" in _fold_published_text(grace_handler)

    def test_bad_grammar_is_published(
            self, grace_handler, agent):
        grace_handler._handle_smallterminal("dance party")
        assert USAGE in _fold_published_text(grace_handler)
        grace_handler._handle_smallterminal("fold fold-nope")
        assert "no fold named" in _fold_published_text(grace_handler)


class TestChatScreenRoutingGrace:
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
        screen.handle_command("/smallterminal panel", _FakeLog())
        assert calls == [("/smallterminal", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/smallterminal[/green] - show small-terminal grace (M-194)" in (
            text)
        assert ('"/smallterminal": "Usage: /smallterminal | '
                '/smallterminal fold <fold-id>') in text


class TestGraceDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.small_terminal_grace_panel()
        assert panel.total_shown == 6
        assert panel.panel_id == "panel-view-grace"
        verdict = agent.small_terminal_grace_verdict()
        assert verdict.verdict == "strained"
        found = agent.small_terminal_grace_verdict("view-preserved")
        assert found.verdict == "open"
        assert found.passing_shown == 5
        agent.register_grace_fold(_fold())
        with pytest.raises(ValueError):
            agent.small_terminal_grace_panel()
        with pytest.raises(ValueError):
            agent.small_terminal_grace_verdict()

    def test_view_target_over_an_unshown_filter_is_shut(self, agent):
        agent.register_grace_fold(_fold(preserves=""))
        result = agent.view_grace("preserved")
        assert result["verdict_record"]["verdict"] == "shut"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.grace_index()
        assert [e["preserves"] for e in result["index"]["entries"]] == ["the work in progress", "the board and its slice standings", "the crew roster and each worker's slice", "the file list, folded to names and standings", "the conversation and the question on the floor"]
        assert result["index"]["gaps"] == ["fold-terminal-phone"]
        assert "the work in progress - Work pane on the wide terminal (fold-work-wide)" in (
            result["index_text"])
        fold = agent.get_grace_fold("fold-terminal-phone")
        assert fold_gaps(fold) == ("no preserved work",)
        assert fold_passes(fold) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("grace")
                or e["type"] == "grace_fold"] == []
        agent.close()
