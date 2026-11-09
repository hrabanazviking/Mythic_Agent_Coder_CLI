"""M-177 Prompt Craft - pure-layer tests.

TIER: integration

The pure layer is the craft item, held as data:
one piece of the input box's craft with its kind
in the closed kind set (draft, history, image,
file - the roadmap's own order), the one project
it stands in (history is per project), its title
and its words held whole, multi-line where they
run so, with its provenance whole (the day it was
recorded, who recorded it, its source and the
session it was recorded in). A pasted image is
first held as its own record, judged whole - its
name, its format and the plain words that
describe it, the image itself never held - and
joins the book as an item of the image kind; a
dropped file is first held as its own record,
judged whole - its path named, never opened,
never read - and joins as an item of the file
kind. A view is held as its own record, the one
project it looks at or every project at once. An
item's line and line count are derived from its
own title, kind, project and words - never
stored, never counted by hand. The panel is
derived for one held view and the verdict is
derived for the whole book under one view. The
shipped example book is held in a data file, and
a loader reads a book from any file. Dictation
is M-180's road and is not built here: no
 dictation kind, record or road stands in this
layer. Nothing here edits a live input box,
pastes, drops, dictates, opens a dropped file,
sends, calls a model or persists anything: an
item held here is a finding, never the act of
typing, pasting or sending the prompt found.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.prompt_craft import (
    IMAGE_FORMATS,
    ITEM_KINDS,
    PLAIN_EXPLANATION,
    PROMPT_CRAFT_RESOURCE,
    PROMPT_CRAFT_SCHEMA,
    PROMPT_CRAFT_SLICE,
    USAGE,
    VERDICT_WORDS,
    DroppedFile,
    PastedImage,
    PromptCraftBook,
    PromptCraftRegistry,
    PromptItem,
    PromptKindCount,
    PromptPanel,
    PromptPanelRow,
    PromptVerdict,
    PromptView,
    book_record,
    build_book,
    build_file,
    build_image,
    build_item,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    derive_panel,
    derive_verdict,
    file_record,
    format_book,
    format_item,
    format_panel,
    format_prompt_craft_screen,
    format_verdict,
    format_view,
    image_record,
    inspect_item_source,
    item_from_draft_text,
    item_from_dropped_file,
    item_from_history_entry,
    item_from_pasted_image,
    item_record,
    items_for_project,
    items_with_kind,
    line_count_of,
    line_of,
    load_prompt_craft,
    load_prompt_craft_file,
    normalize_image_format,
    normalize_kind,
    normalize_project_filter,
    panel_plain_words,
    panel_record,
    parse_prompt_craft_args,
    plain_words,
    shown_items,
    total_items,
    validate_file,
    validate_image,
    validate_item,
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

EXAMPLE_TITLE = "Prompt Craft at the M-176 slice boundary"

BY = "the coordinator"
ON = "2026-11-09"


def _item(**overrides):
    fields = {
        "item_id": "item-test",
        "kind": "draft",
        "project": "mythic-coder",
        "title": "Thing draft",
        "body": "First line.\nSecond line.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_item(fields)


def _stored_item(item):
    stored = item.to_record()
    for key in ("type", "slice", "line", "line_count"):
        stored.pop(key)
    return stored


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "project_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _stored_view(view):
    stored = view.to_record()
    for key in ("type", "slice"):
        stored.pop(key)
    return stored


def _image(**overrides):
    fields = {
        "image_id": "image-test",
        "name": "Thing sketch",
        "format": "png",
        "note": "A pasted image held as words, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_image(fields)


def _stored_image(image):
    stored = image.to_record()
    for key in ("type", "slice"):
        stored.pop(key)
    return stored


def _file(**overrides):
    fields = {
        "file_id": "file-test",
        "path": "notes/thing.md",
        "note": "A dropped file held as words, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_file(fields)


def _stored_file(dropped):
    stored = dropped.to_record()
    for key in ("type", "slice"):
        stored.pop(key)
    return stored


def _book(items=None, views=(), **overrides):
    fields = {
        "title": "A test craft book",
        "items": [_stored_item(item) for item in (
            items if items is not None else [_item()])],
        "views": [_stored_view(item) for item in views],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(
        items=[
            _item(),
            _item(item_id="item-second", kind="history",
                  project="samtal", title="Thing prompt",
                  body="The thing prompt, as sent."),
            _item(item_id="item-other", kind="file",
                  title="Other file",
                  body="An unrelated drop, for the tests."),
        ],
        views=[_view()])


# ---------------------------------------------------------------------
# The shipped example book, the roadmap and the charter.
# ---------------------------------------------------------------------


def test_shipped_book_loads_with_pinned_shape():
    book = load_prompt_craft()
    assert book.title == EXAMPLE_TITLE
    assert book.item_ids() == (
        "item-opening-draft", "item-palace-note",
        "item-first-prompt", "item-standup-prompt",
        "item-longship-sketch", "item-harbour-photo",
        "item-roadmap-drop", "item-verses-drop")
    first = book.items[0]
    assert first.kind == "draft"
    assert first.project == "mythic-coder"
    assert first.line_count == 3
    assert book.view_ids() == ("view-all", "view-mythic-coder")
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m176-boundary"
    assert panel.as_of == "2026-11-09"
    assert [row.item_id for row in panel.rows] == [
        "item-opening-draft", "item-palace-note",
        "item-first-prompt", "item-standup-prompt",
        "item-longship-sketch", "item-harbour-photo",
        "item-roadmap-drop", "item-verses-drop"]
    derived = derive_panel(book, "view-all")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 8
    assert panel.total_shown == derived.total_shown == 8
    assert {c.kind: c.items for c in panel.kind_counts} == {
        "draft": 2, "history": 2, "image": 2, "file": 2}
    assert derive_verdict(book, "view-all").verdict == "shared"
    assert derive_verdict(book, "view-mythic-coder").verdict == (
        "held")
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / PROMPT_CRAFT_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == PROMPT_CRAFT_SCHEMA
    assert raw["slice"] == "M-177"


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-177")]
    assert slice_.title == "Prompt craft"
    assert slice_.part == 8
    assert "multi-line editing" in slice_.summary
    assert "history per project" in slice_.summary
    assert "image paste" in slice_.summary
    assert "file drop" in slice_.summary
    assert "dictation (M-180)" in slice_.summary
    assert "small editor" in slice_.summary
    assert PROMPT_CRAFT_SLICE == "M-177"


def test_charter_names_no_row_for_m177():
    # No M-171 charter row names M-177 as an owning
    # slice: the slice is built to the roadmap words
    # alone. The input lives on the main chat screen
    # (S-03), whose owning slices are named here so
    # the absence is proven against the live rows,
    # not assumed.
    charter = load_charter()
    for key in charter.screen_keys():
        screen = charter.screen(key)
        assert "M-177" not in screen.owning_slices, key
    chat = charter.screen("main_chat")
    assert chat.id == "S-03"
    assert chat.verdict == "repair"
    assert tuple(chat.owning_slices) == (
        "M-172", "M-173", "M-178")


def test_closed_vocabularies():
    assert ITEM_KINDS == ("draft", "history", "image", "file")
    assert VERDICT_WORDS == ("shared", "held", "empty")
    assert IMAGE_FORMATS == ("png", "jpeg", "gif", "webp")
    assert normalize_kind("pasted") == "image"
    assert normalize_kind("Drop") == "file"
    assert normalize_image_format("JPG") == "jpeg"
    assert normalize_project_filter("ALL") == "all"
    assert normalize_project_filter("samtal") == "samtal"
    with pytest.raises(ValueError):
        normalize_kind("whenever")
    with pytest.raises(ValueError):
        normalize_image_format("tiff")
    assert "small editor" in PLAIN_EXPLANATION
    assert "M-180" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /promptcraft")


def test_dictation_is_m180s_road_not_built():
    # Dictation stands in the roadmap words with its
    # own slice named (M-180) and is not built here:
    # it is no kind, no item and no road of this layer.
    assert "dictation" not in ITEM_KINDS
    with pytest.raises(ValueError):
        normalize_kind("dictation")
    with pytest.raises(ValueError):
        _item(kind="dictation")
    with pytest.raises(ValueError):
        parse_prompt_craft_args("dictate hello")
    book = load_prompt_craft()
    assert {item.kind for item in book.items} == set(ITEM_KINDS)


# ---------------------------------------------------------------------
# The item: judged whole, its line derived from its own fields.
# ---------------------------------------------------------------------


def test_item_record_round_trips():
    item = _item()
    assert build_item(_stored_item(item)) == item
    record = item.to_record()
    assert record["line"] == "Thing draft - draft in mythic-coder"
    assert record["line_count"] == 2
    assert record["type"] == "prompt_craft_item"
    assert item.line == line_of(item)
    assert item.line_count == line_count_of(item)


def test_item_provenance_is_whole_and_required():
    item = _item()
    assert item.actor == BY
    assert item.origin_session == "session-test"
    for missing in ("item_id", "kind", "project", "title",
                    "body", "recorded_on", "actor",
                    "source", "origin_session"):
        fields = _stored_item(item)
        fields.pop(missing)
        with pytest.raises(ValueError):
            build_item(fields)
    with pytest.raises(ValueError):
        _item(body="   ")


def test_item_refuses_unknown_keys_and_derived_keys():
    for derived_key, value in (
            ("line", "Thing draft - draft in mythic-coder"),
            ("line_count", 2), ("lines", 2),
            ("sent_text", "First line.")):
        fields = _stored_item(_item())
        fields[derived_key] = value
        with pytest.raises(ValueError):
            build_item(fields)
    fields = _stored_item(_item())
    fields["surprise"] = "x"
    with pytest.raises(ValueError):
        build_item(fields)
    with pytest.raises(ValueError):
        _item(kind="whatever")


def test_item_alias_spellings_read_onto_the_fields():
    item = build_item({
        "id": "item-alias", "type_of": "pasted",
        "project_ref": "samtal", "name": "Alias sketch",
        "text": "An alias-spelled item for the tests.",
        "day": ON, "by": BY,
        "source": "alias source", "session": "session-alias"})
    assert item.kind == "image"
    assert item.project == "samtal"
    assert item.title == "Alias sketch"
    assert item.body == "An alias-spelled item for the tests."


def test_item_stands_in_one_named_project_never_all():
    # History is per project: an item stands in
    # exactly one named project, and the every-
    # project filter is a view's alone.
    with pytest.raises(ValueError):
        _item(project="all")
    with pytest.raises(ValueError):
        _item(project="ALL")
    with pytest.raises(ValueError):
        _item(project="two words")
    assert _item(project="samtal").project == "samtal"


def test_line_and_count_are_derived():
    one = _item(body="Only line.")
    assert line_count_of(one) == 1
    assert line_of(one) == "Thing draft - draft in mythic-coder"
    three = _item(body="One.\nTwo.\nThree.")
    assert line_count_of(three) == 3
    assert three.to_record().get("line_count") == 3
    held = _item(kind="history", project="samtal",
                 title="Old prompt", body="As sent.")
    assert line_of(held) == "Old prompt - history in samtal"
    # The count is derived, never a stored field the
    # item itself carries into judgement.
    fields = _stored_item(three)
    assert "line_count" not in fields
    assert "line" not in fields


def test_multiline_words_are_held_whole():
    item = _item(body="First.\n\nThird after a blank.")
    assert item.body == "First.\n\nThird after a blank."
    assert line_count_of(item) == 3
    record = item.to_record()
    assert record["body"] == "First.\n\nThird after a blank."


def test_view_narrows_never_judges():
    # A view narrows which items stand in its panel;
    # the items it shows are the held items
    # themselves, judged exactly as they stand.
    book = _mixed_book()
    view_all = _view()
    assert [i.item_id for i in shown_items(
        book.items, view_all)] == [
            "item-test", "item-second", "item-other"]
    view_samtal = _view(
        view_id="view-samtal", seq=2, project_filter="samtal")
    shown = shown_items(book.items, view_samtal)
    assert [i.item_id for i in shown] == ["item-second"]
    assert shown[0] is book.item_for("item-second")
    assert view_all.shows(book.item_for("item-second"))
    assert not view_samtal.shows(book.item_for("item-test"))


# ---------------------------------------------------------------------
# Composition: the box's own pieces, judged whole.
# ---------------------------------------------------------------------


def test_draft_item_from_text():
    item = item_from_draft_text(
        "Shape the thing.\nThen shape it again.",
        item_id="item-draft", project="mythic-coder",
        title="Shaping draft")
    assert item.kind == "draft"
    assert item.line_count == 2
    assert item.body == "Shape the thing.\nThen shape it again."
    with pytest.raises(ValueError):
        item_from_draft_text(
            "   ", item_id="item-x", project="mythic-coder",
            title="Empty draft")
    with pytest.raises(ValueError):
        item_from_draft_text(
            "Words.", item_id="item-x", project="all",
            title="Nowhere draft")


def test_history_item_from_entry():
    item = item_from_history_entry(
        {"project": "samtal", "text": "Draft the stand-up.",
         "recorded_on": ON, "actor": BY,
         "source": "test source", "origin_session": "session-test"},
        item_id="item-history", title="Stand-up, as sent")
    assert item.kind == "history"
    assert item.project == "samtal"
    assert item.body == "Draft the stand-up."
    untitled = item_from_history_entry(
        {"project": "samtal",
         "text": "First line stands as the name.\nSecond line."},
        item_id="item-history-two")
    assert untitled.title == "First line stands as the name."
    assert untitled.line_count == 2
    with pytest.raises(ValueError):
        item_from_history_entry(
            {"text": "No project named."}, item_id="item-x")
    with pytest.raises(ValueError):
        item_from_history_entry(
            {"project": "samtal"}, item_id="item-x")
    with pytest.raises(ValueError):
        item_from_history_entry("nope", item_id="item-x")


def test_pasted_image_is_judged_whole():
    image = _image()
    assert validate_image(_stored_image(image)) == image
    assert image.format == "png"
    record = image.to_record()
    assert record["type"] == "prompt_craft_image"
    assert validate_image(
        _stored_image(_image(format="JPG"))).format == "jpeg"
    for missing in ("image_id", "name", "format", "note",
                    "recorded_on", "actor", "source",
                    "origin_session"):
        fields = _stored_image(image)
        fields.pop(missing)
        with pytest.raises(ValueError):
            build_image(fields)
    with pytest.raises(ValueError):
        _image(format="tiff")
    assert isinstance(image, PastedImage)


def test_item_from_pasted_image():
    image = _image()
    item = item_from_pasted_image(
        image, item_id="item-image", project="mythic-coder")
    assert item.kind == "image"
    assert item.title == "Thing sketch"
    assert item.body == image.note
    assert item.actor == BY
    # The book holds the paste as data: the image's
    # own record keeps the format; the item carries
    # no image bytes and no format of its own.
    assert "format" not in item.to_record()
    assert not hasattr(item, "format")
    assert not hasattr(item, "image_data")
    with pytest.raises(ValueError):
        item_from_pasted_image(
            None, item_id="item-x", project="mythic-coder")


def test_dropped_file_is_judged_whole():
    dropped = _file()
    assert validate_file(_stored_file(dropped)) == dropped
    assert dropped.path == "notes/thing.md"
    record = dropped.to_record()
    assert record["type"] == "prompt_craft_file"
    for missing in ("file_id", "path", "note",
                    "recorded_on", "actor", "source",
                    "origin_session"):
        fields = _stored_file(dropped)
        fields.pop(missing)
        with pytest.raises(ValueError):
            build_file(fields)
    assert isinstance(dropped, DroppedFile)


def test_item_from_dropped_file():
    dropped = _file()
    item = item_from_dropped_file(
        dropped, item_id="item-file", project="samtal")
    assert item.kind == "file"
    assert item.project == "samtal"
    # The title is the dropped path's own last part,
    # and the path named here does not exist on
    # disk: the item stands without the file ever
    # being opened or read.
    assert item.title == "thing.md"
    assert item.body == dropped.note
    named = item_from_dropped_file(
        dropped, item_id="item-file-two", project="samtal",
        title="Named afresh")
    assert named.title == "Named afresh"
    with pytest.raises(ValueError):
        item_from_dropped_file(
            None, item_id="item-x", project="samtal")


def test_inspect_item_source_names_what_a_piece_is():
    found = inspect_item_source(
        {"kind": "pasted", "project": "samtal"})
    assert found["kind"] == "image"
    assert found["project"] == "samtal"
    bad = inspect_item_source(
        {"kind": "dictation", "project": "samtal"})
    assert bad["kind"] is None
    assert inspect_item_source(
        {"kind": "draft"})["kind"] is None
    assert inspect_item_source("nope")["kind"] is None


# ---------------------------------------------------------------------
# The view record, the panel and the verdict: derived, never chosen.
# ---------------------------------------------------------------------


def test_view_is_judged_whole():
    view = _view()
    assert build_view(_stored_view(view)) == view
    assert validate_view(_stored_view(view)) == view
    fields = _stored_view(view)
    fields["rows"] = ["item-test"]
    with pytest.raises(ValueError):
        build_view(fields)
    fields = _stored_view(view)
    fields.pop("detail")
    with pytest.raises(ValueError):
        build_view(fields)
    with pytest.raises(ValueError):
        _view(project_filter="two words")
    assert _view(project_filter="ALL").project_filter == "all"
    assert isinstance(view, PromptView)


def test_panel_is_derived_for_one_view():
    book = _mixed_book()
    panel = derive_panel(book, "view-test")
    assert panel.total_items == 3
    assert panel.total_shown == 3
    assert [row.item_id for row in panel.rows] == [
        "item-test", "item-second", "item-other"]
    assert {c.kind: c.items for c in panel.kind_counts} == {
        "draft": 1, "history": 1, "file": 1}
    assert panel.rows[0].line == "Thing draft - draft in mythic-coder"
    assert panel.rows[0].line_count == 2
    assert panel.view_id == "view-test"
    assert PromptKindCount(kind="pasted", items=2).to_record() == {
        "kind": "image", "items": 2}
    assert isinstance(panel, PromptPanel)
    samtal = derive_panel(book, _view(
        view_id="view-samtal", seq=2, project_filter="samtal"))
    assert samtal.total_shown == 1
    assert samtal.rows[0].item_id == "item-second"


def test_panel_refuses_a_stored_panel_that_disagrees():
    book = _mixed_book()
    stored = derive_panel(book, "view-test").to_record()
    stored.pop("type")
    stored.pop("slice")
    stored["total_shown"] = 2
    with pytest.raises(ValueError):
        validate_panel(stored, book)
    stored = derive_panel(book, "view-test").to_record()
    stored.pop("type")
    stored.pop("slice")
    stored["rows"][0]["line_count"] = 99
    with pytest.raises(ValueError):
        validate_panel(stored, book)
    panel = build_panel(
        derive_panel(book, "view-test").to_record(), book)
    assert panel.total_shown == 3


def test_row_is_judged_against_its_item():
    item = _item()
    row = build_row(item=item)
    assert row.line == "Thing draft - draft in mythic-coder"
    assert row.line_count == 2
    assert validate_row(row.to_record(), item) == row
    bad = row.to_record()
    bad["line_count"] = row.line_count + 1
    with pytest.raises(ValueError):
        validate_row(bad, item)
    bad = row.to_record()
    bad["line"] = "a chosen line"
    with pytest.raises(ValueError):
        validate_row(bad, item)
    assert isinstance(row, PromptPanelRow)


def test_verdict_words_shared_held_empty():
    book = load_prompt_craft()
    assert derive_verdict(book, "view-all").verdict == "shared"
    assert derive_verdict(
        book, "view-mythic-coder").verdict == "held"
    empty_view = _view(
        view_id="view-empty", seq=9, project_filter="elsewhere",
        detail="See a project with nothing held, for the tests.")
    empty = derive_verdict(book, empty_view)
    assert empty.verdict == "empty"
    assert empty.total_shown == 0
    assert empty.distinct_projects == 0
    assert build_verdict(empty.to_record(), book, empty_view) == empty
    with pytest.raises(ValueError):
        PromptVerdict(
            total_items=8, total_shown=4, distinct_projects=2,
            earliest_on=ON, latest_on=ON, verdict="held")
    with pytest.raises(ValueError):
        validate_verdict(empty.to_record(), book, "view-all")
    assert isinstance(empty, PromptVerdict)


# ---------------------------------------------------------------------
# The book, the file loader and the registry.
# ---------------------------------------------------------------------


def test_book_laws_one_item_per_id():
    with pytest.raises(ValueError):
        _book(items=[_item(), _item(title="Another draft")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(view_id="view-two")])
    with pytest.raises(ValueError):
        _book(views=[
            _view(), _view(view_id="view-two", seq=1,
                           project_filter="samtal")])
    book = _mixed_book()
    assert book.item_for("item-second").kind == "history"
    assert book.view_for("view-test").project_filter == "all"
    with pytest.raises(KeyError):
        book.item_for("item-nope")
    with pytest.raises(KeyError):
        book.view_for("view-nope")
    assert total_items(book) == 3
    assert [i.item_id for i in items_with_kind(
        book, "pasted")] == []
    assert [i.item_id for i in items_for_project(
        book, "samtal")] == ["item-second"]
    assert [i.item_id for i in items_for_project(
        book, "all")] == [
            "item-test", "item-second", "item-other"]
    assert isinstance(book, PromptCraftBook)
    assert isinstance(_item(), PromptItem)


def test_book_file_loader_reads_any_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "prompt_craft.yaml").read_text(encoding="utf-8")
    path = tmp_path / "prompt_craft.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_prompt_craft_file(path)
    assert book.title == EXAMPLE_TITLE
    assert total_items(book) == 8


def test_registry_holds_items_and_views_one_by_one():
    registry = PromptCraftRegistry()
    registry.register_item(_item())
    registry.register_item(_item(
        item_id="item-second", kind="history", project="samtal",
        title="Thing prompt", body="The thing prompt, as sent."))
    held = registry.register_view(_view(view_id=None))
    assert held.view_id == "view-1"
    assert registry.latest_view().view_id == "view-1"
    assert registry.book().title == "Prompt Craft"
    assert registry.panel("view-1").total_shown == 2
    assert registry.verdict("view-1").verdict == "shared"
    with pytest.raises(ValueError):
        registry.register_item(_item(title="Same id again"))
    with pytest.raises(ValueError):
        registry.register_view(_view(view_id="view-1", seq=2))
    with pytest.raises(ValueError):
        registry.register_view(_view(view_id="view-two"))
    assert [v.view_id for v in registry.list_views()] == ["view-1"]
    with pytest.raises(KeyError):
        registry.get_item("item-nope")
    with pytest.raises(KeyError):
        registry.get_view("view-nope")


def test_registry_register_book_and_refusals():
    registry = PromptCraftRegistry()
    book = registry.register_book(_mixed_book())
    assert total_items(book) == 3
    assert registry.title() == "A test craft book"
    with pytest.raises(ValueError):
        registry.register_book(_book())
    other = PromptCraftRegistry(_book())
    assert other.get_item("item-test").item_id == "item-test"
    assert isinstance(other.book(), PromptCraftBook)
    assert isinstance(_view(), PromptView)


# ---------------------------------------------------------------------
# News, plain words, formatters and the grammar.
# ---------------------------------------------------------------------


def test_news_records_carry_headlines():
    item = _item()
    news = item_record(item)
    assert news["news"] is True
    assert news["type"] == "prompt_craft_item"
    assert "Thing draft - draft in mythic-coder" in news["headline"]
    image_news = image_record(_image())
    assert image_news["type"] == "prompt_craft_image"
    assert "Thing sketch" in image_news["headline"]
    file_news = file_record(_file())
    assert file_news["type"] == "prompt_craft_file"
    assert "notes/thing.md" in file_news["headline"]
    view_news = view_record(_view())
    assert view_news["type"] == "prompt_craft_view"
    assert "all" in view_news["headline"]
    panel_news = panel_record(derive_panel(_mixed_book(), "view-test"))
    assert "Prompt craft panel" in panel_news["headline"]
    verdict_news = verdict_record(
        derive_verdict(_mixed_book(), "view-test"))
    assert "shared" in verdict_news["headline"]
    book_news = book_record(_mixed_book())
    assert book_news["item_count"] == 3
    assert book_news["view_count"] == 1


def test_formatters_and_screen():
    book = load_prompt_craft()
    text = format_item(book.item_for("item-verses-drop"))
    assert "Kind: file" in text
    assert "Project: samtal" in text
    assert "Verses file" in text
    view_text = format_view(book.view_for("view-all"))
    assert "project 'all'" in view_text
    listed = format_book(book)
    assert "item-opening-draft: Opening draft - draft in mythic-coder" in (
        listed)
    images = format_book(book, kind="image")
    assert "item-harbour-photo" in images
    assert "item-first-prompt" not in images
    assert "Panel in Prompt Craft at the M-176 slice boundary" in (
        format_panel(book))
    assert format_verdict(book).startswith(
        "Verdict in Prompt Craft over")
    assert "shared" in format_verdict(book)
    screen = format_prompt_craft_screen()
    assert "Prompt Craft (M-177)" in screen
    assert "dictates nothing" in screen
    assert "Opening draft - draft in mythic-coder" in plain_words(
        book.item_for("item-opening-draft"))
    assert "edits no live input box" in view_plain_words(
        book.view_for("view-all"))
    assert "Shown, in held order" in panel_plain_words(book)
    assert "shared" in verdict_plain_words(book)


def test_parse_prompt_craft_args_grammar():
    assert parse_prompt_craft_args("") == ("show", None)
    assert parse_prompt_craft_args(None) == ("show", None)
    assert parse_prompt_craft_args("show") == ("show", None)
    assert parse_prompt_craft_args("list") == ("show", None)
    assert parse_prompt_craft_args("item item-test") == (
        "item", "item-test")
    assert parse_prompt_craft_args("view view-all") == (
        "view", "view-all")
    assert parse_prompt_craft_args("project samtal") == (
        "project", "samtal")
    assert parse_prompt_craft_args("project ALL") == (
        "project", "all")
    assert parse_prompt_craft_args("kind pasted") == ("kind", "image")
    assert parse_prompt_craft_args("panel") == ("panel", None)
    assert parse_prompt_craft_args("verdict") == ("verdict", None)
    for bad in ("item", "view", "project", "kind whenever",
                "kind dictation", "panel now", "dance", 42):
        with pytest.raises(ValueError):
            parse_prompt_craft_args(bad)


def test_pure_layer_imports_no_agent_or_ui():
    text = (ROOT / "mythic_agent" / "core"
            / "prompt_craft.py").read_text(encoding="utf-8")
    assert "mythic_agent.agents" not in text
    assert "import textual" not in text
    assert "from ..agents" not in text


# -- agent layer -----------------------------------------------------------
#
# M-177 agent layer: the agent holds a
# PromptCraftRegistry for the session (session
# state only, no new setting), items and view
# records are held by being registered - each
# judged whole before it is held - published as
# their item_record / view_record session news
# through the checkpoint road, deduped per shape -
# an item composed from the box's own pieces
# stands on the register road exactly as the pure
# layer composed it, the viewing road composes
# one view record at the held book's next sequence
# and publishes the derived panel and verdict news
# with it, whole-book register and record roads
# hold a book judged whole first, the report road
# renders the held book (or the shipped example
# when unheld) through the pure formatters, and
# the /promptcraft surface rides both roads on the
# pure parser + formatters. Status, get, kind,
# project, panel, verdict and report reads register
# and publish nothing, answer from the held
# registry first and from the shipped example only
# while nothing is held - a held item never falls
# back to the example. The panel and the verdict
# derive at call time from the whole book under a
# view, never held. This layer edits no live input
# box, pastes nothing, drops nothing, dictates
# nothing (dictation is M-180's road), opens no
# dropped file, sends nothing, calls no model,
# persists nothing beyond the session journal
# news and banks nothing - an item held here is a
# finding, never the act of typing, pasting or
# sending the prompt found.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _craft_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "prompt_craft.yaml").read_text(encoding="utf-8")
    path = tmp_path / "prompt_craft.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestPromptCraftAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.prompt_craft_status()
        assert status["items"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["prompt_craft"]["title"] == EXAMPLE_TITLE
        assert len(status["prompt_craft"]["items"]) == 8
        assert len(status["prompt_craft"]["views"]) == 2
        assert status["panel"]["total_items"] == 8
        assert status["panel"]["total_shown"] == 8
        assert status["panels"][0]["panel_id"] == "panel-m176-boundary"
        assert status["book_record"]["item_count"] == 8
        assert status["book_record"]["view_count"] == 2
        assert status["verdict"]["verdict"] == "shared"
        assert "Verses file - file in samtal" in status["plain_words"]
        assert "Prompt Craft (M-177)" in status["screen"]
        assert "8 of 8 items show" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._prompt_craft_registry()
        assert agent._prompt_craft_registry() is first
        assert agent._prompt_craft_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.prompt_craft_status()
        assert agent.get_craft_item(
            "item-verses-drop").kind == "file"
        assert agent.get_craft_view(
            "view-all").project_filter == "all"
        assert [i.item_id for i in agent.prompt_craft_with_kind(
            "draft")] == [
                "item-opening-draft", "item-palace-note"]
        assert [i.item_id for i in agent.prompt_craft_with_kind(
            "pasted")] == [
                "item-longship-sketch", "item-harbour-photo"]
        assert [i.item_id for i in agent.prompt_craft_for_project(
            "samtal")] == [
                "item-standup-prompt", "item-harbour-photo",
                "item-verses-drop"]
        agent.prompt_craft_panel()
        agent.prompt_craft_verdict()
        agent.report_prompt_craft()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("prompt_craft")] == []
        with pytest.raises(KeyError):
            agent.get_craft_item("item-nope")
        with pytest.raises(KeyError):
            agent.get_craft_view("view-nope")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_craft_item(_item())
        status = agent.prompt_craft_status()
        assert [item["item_id"] for item in status["items"]] == [
            "item-test"]
        assert status["book"]["title"] == "Prompt Craft"
        assert status["panel"] is None
        assert status["verdict"] is None

    def test_held_item_never_falls_back_to_the_example(
            self, agent):
        agent.register_craft_item(_item())
        with pytest.raises(KeyError):
            agent.get_craft_item("item-opening-draft")
        with pytest.raises(KeyError):
            agent.get_craft_view("view-all")
        item = agent.get_craft_item("item-test")
        assert item.title == "Thing draft"
        assert agent.prompt_craft_book().title == "Prompt Craft"


class TestPromptCraftAgentHolding:
    def test_register_item_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_craft_item(_item())
        assert outcome["item"]["item_id"] == "item-test"
        assert outcome["record_news"]["news"] is True
        assert outcome["record_news"]["type"] == "prompt_craft_item"
        assert "item-test" in outcome["screen"]
        agent.register_craft_item(_item(
            item_id="item-second", kind="history", project="samtal",
            title="Thing prompt", body="The thing prompt, as sent."))
        events = _craft_events(store, session_id, "prompt_craft_item")
        assert len(events) == 2
        agent._publish_prompt_craft_record(item_record(_item()))
        agent._publish_prompt_craft_record(
            {"type": "slice_board_card", "news": True})
        events = _craft_events(store, session_id, "prompt_craft_item")
        assert len(events) == 2
        agent.close()

    def test_duplicate_item_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_craft_item(_item())
        with pytest.raises(ValueError):
            agent.register_craft_item(_item())
        with pytest.raises(ValueError):
            agent.register_craft_item(
                _item(title="Same id, new title"))
        events = _craft_events(store, session_id, "prompt_craft_item")
        assert len(events) == 1
        agent.close()

    def test_composed_items_hold_by_the_register_road(self, agent):
        draft = item_from_draft_text(
            "Shape the thing.\nThen shape it again.",
            item_id="item-draft", project="mythic-coder",
            title="Shaping draft")
        outcome = agent.register_craft_item(draft)
        assert outcome["item"]["kind"] == "draft"
        history = item_from_history_entry(
            {"project": "samtal", "text": "Draft the stand-up."},
            item_id="item-history", title="Stand-up, as sent")
        agent.register_craft_item(history)
        image_item = item_from_pasted_image(
            _image(), item_id="item-image", project="mythic-coder")
        agent.register_craft_item(image_item)
        file_item = item_from_dropped_file(
            _file(), item_id="item-file", project="samtal")
        agent.register_craft_item(file_item)
        assert [i.item_id for i in agent.prompt_craft_with_kind(
            "image")] == ["item-image"]
        assert [i.item_id for i in agent.prompt_craft_for_project(
            "samtal")] == ["item-history", "item-file"]
        assert agent.get_craft_item(
            "item-draft").line_count == 2

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_craft_item(_item())
        outcome = agent.register_craft_view(_view())
        assert outcome["view"]["view_id"] == "view-test"
        assert outcome["record_news"]["type"] == "prompt_craft_view"
        with pytest.raises(ValueError):
            agent.register_craft_view(_view(seq=2))
        with pytest.raises(ValueError):
            agent.register_craft_view(
                _view(view_id="view-two"))
        assert [v.view_id for v in
                agent._prompt_craft_registry().list_views()] == [
                    "view-test"]
        events = _craft_events(store, session_id, "prompt_craft_view")
        assert len(events) == 1
        agent.close()

    def test_view_road_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_craft_item(_item())
        agent.register_craft_item(_item(
            item_id="item-second", kind="history", project="samtal",
            title="Thing prompt", body="The thing prompt, as sent."))
        outcome = agent.view_prompt_craft("all")
        assert outcome["view"]["seq"] == 1
        assert outcome["view"]["view_id"] == "view-1"
        assert outcome["record_news"]["type"] == "prompt_craft_view"
        assert outcome["panel_record"]["type"] == "prompt_craft_panel"
        assert outcome["panel_record"]["total_shown"] == 2
        assert outcome["verdict_record"]["type"] == (
            "prompt_craft_verdict")
        assert outcome["verdict_record"]["verdict"] == "shared"
        second = agent.view_prompt_craft(
            "samtal",
            detail="See the samtal project's craft alone, for the tests.")
        assert second["view"]["seq"] == 2
        assert second["verdict_record"]["verdict"] == "held"
        assert agent.prompt_craft_verdict().verdict == "shared"
        assert len(_craft_events(
            store, session_id, "prompt_craft_view")) == 2
        assert len(_craft_events(
            store, session_id, "prompt_craft_verdict")) == 2
        agent.close()

    def test_view_road_over_an_unheld_project_is_empty(self, agent):
        agent.register_craft_item(_item())
        outcome = agent.view_prompt_craft("elsewhere")
        assert outcome["panel_record"]["total_shown"] == 0
        assert outcome["verdict_record"]["verdict"] == "empty"
        assert agent.prompt_craft_panel(
            outcome["view"]["view_id"]).total_shown == 0

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_prompt_craft_book(_mixed_book())
        assert outcome["count"] == 3
        assert [i["item_id"] for i in outcome["items"]] == [
            "item-test", "item-second", "item-other"]
        assert [r["type"] for r in outcome["records_news"]] == [
            "prompt_craft_item", "prompt_craft_item",
            "prompt_craft_item", "prompt_craft_view"]
        events = _craft_events(store, session_id, "prompt_craft_item")
        assert [e["item_id"] for e in events] == [
            "item-test", "item-second", "item-other"]
        assert agent.prompt_craft_book().title == (
            "A test craft book")
        with pytest.raises(ValueError):
            agent.register_prompt_craft_book(_mixed_book())
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_prompt_craft_book()
        assert outcome["count"] == 8
        assert outcome["book"]["title"] == EXAMPLE_TITLE
        assert len(_craft_events(
            store, session_id, "prompt_craft_item")) == 8
        assert len(_craft_events(
            store, session_id, "prompt_craft_view")) == 2
        status = agent.prompt_craft_status()
        assert status["panels"][0]["panel_id"] == "panel-m176-boundary"
        with pytest.raises(ValueError):
            agent.record_prompt_craft_book()
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_book_file(tmp_path)
        book = load_prompt_craft_file(path)
        outcome = agent.record_prompt_craft_book(book)
        assert outcome["count"] == 8
        assert agent.prompt_craft_book().title == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_prompt_craft()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert len(report["items"]) == 8
        assert report["verdict"]["verdict"] == "shared"
        assert "item-verses-drop: Verses file - file in samtal" in (
            report["book_text"])
        agent.register_craft_item(_item())
        report = agent.report_prompt_craft()
        assert [i["item_id"] for i in report["items"]] == [
            "item-test"]
        assert "item-test: Thing draft - draft in mythic-coder" in (
            report["book_text"])
        assert report["verdict"] is None

    def test_holding_and_viewing_execute_nothing(self, agent):
        for name in (
                "paste_prompt_image", "drop_prompt_file",
                "dictate_prompt", "send_prompt_craft",
                "persist_prompt_craft", "bank_prompt_craft",
                "apply_prompt_craft", "render_prompt_craft_ui",
                "open_dropped_file", "read_dropped_file",
                "edit_live_input_box", "run_prompt_craft",
                "delete_craft_item"):
            assert not hasattr(agent, name), name
        agent.register_craft_item(_item())
        agent.view_prompt_craft("all")
        # A view held here only ever looks: no live box
        # was edited, no prompt was sent, no dropped
        # file was opened, and the craft's standing
        # lives in no setting. Dictation is M-180's
        # road and stands nowhere on this agent.
        assert agent.prompt_craft_book().title == "Prompt Craft"
        assert agent.config.get("prompt_craft") is None


class TestPromptCraftTerminalSurface:
    def test_show_item_view_project_kind_panel_verdict(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/promptcraft")
        assert "Prompt Craft (M-177)" in text
        _, _, text = _slash(
            agent, "/promptcraft item item-verses-drop")
        assert "Kind: file" in text
        assert "Project: samtal" in text
        _, _, text = _slash(agent, "/promptcraft view view-all")
        assert "project 'all'" in text
        _, _, text = _slash(agent, "/promptcraft project samtal")
        assert "item-standup-prompt" in text
        assert "item-opening-draft" not in text
        _, _, text = _slash(agent, "/promptcraft kind image")
        assert "item-harbour-photo" in text
        assert "item-first-prompt" not in text
        _, _, text = _slash(agent, "/promptcraft panel")
        assert "Panel in Prompt Craft at the M-176 slice boundary" in (
            text)
        _, _, text = _slash(agent, "/promptcraft verdict")
        assert "shared" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/promptcraft [show|item <item-id>"
                "|view <view-id>|project <project>|kind <kind>"
                "|panel|verdict]") in text
        _, _, text = _slash(agent, "/promptcraft dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/promptcraft item item-nope")
        assert "no item named" in text


@pytest.fixture()
def craft_handler(agent, monkeypatch):
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


def _craft_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestPromptCraftCommand:
    def test_show_is_default(self, craft_handler, agent):
        craft_handler._handle_promptcraft("")
        assert "Prompt Craft (M-177)" in (
            _craft_published_text(craft_handler))

    def test_item_view_panel_verdict(
            self, craft_handler, agent):
        craft_handler._handle_promptcraft("item item-verses-drop")
        assert "Project: samtal" in (
            _craft_published_text(craft_handler))
        craft_handler._handle_promptcraft("view view-all")
        assert "project 'all'" in _craft_published_text(
            craft_handler)
        craft_handler._handle_promptcraft("panel")
        assert "Panel in Prompt Craft" in (
            _craft_published_text(craft_handler))
        craft_handler._handle_promptcraft("verdict")
        assert "shared" in _craft_published_text(craft_handler)

    def test_bad_grammar_is_published(
            self, craft_handler, agent):
        craft_handler._handle_promptcraft("dance party")
        assert USAGE in _craft_published_text(craft_handler)
        craft_handler._handle_promptcraft("item item-nope")
        assert "no item named" in _craft_published_text(
            craft_handler)


class TestChatScreenRoutingPromptCraft:
    def test_promptcraft_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/promptcraft panel", _FakeLog())
        assert calls == [("/promptcraft", "panel")]

    def test_chat_screen_help_and_usage_name_the_craft(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/promptcraft[/green] - show prompt craft (M-177)" in (
            text)
        assert ('"/promptcraft": "Usage: /promptcraft | '
                '/promptcraft item <item-id>') in text
