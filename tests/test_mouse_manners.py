"""M-188 Mouse Manners - pure-layer tests.

TIER: integration

The pure layer is mouse manners, held as data:
one record per gesture, held whole - under its
title, the area it lives in in the closed
vocabulary, its kind in the closed gesture
vocabulary, the mouse road that reaches it,
named as data, and its detail - the file links
held as data beside them, each naming its file,
its line number and the user's editor as its
target, and the gesture guide derived at call
time from the held gestures' roads alone, never
stored where it could drift. A gesture naming
no mouse road stands unwired, named in its
gaps; two links standing for one file at one
line refuse by name. A record claiming a live
pointer move, a live click or a file actually
opened refuses by name, and a stored guide or
verdict refuses by name. The panel is derived
for one held view and the verdict is derived
for the whole book under one view. The shipped
example book is held in a data file, and a
loader reads a book from any file. This layer
moves no pointer, clicks nothing, scrolls
nothing and opens no file: it holds mouse
manners as data and tells it.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.mouse_manners import (
    AREAS,
    EXAMPLE_ROAD,
    GESTURES,
    GUIDE_ACTION,
    MOUSE_MANNERS_RESOURCE,
    MOUSE_MANNERS_SCHEMA,
    MOUSE_MANNERS_SLICE,
    MOUSE_RULE,
    PLAIN_EXPLANATION,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    WIRE_WORDS,
    GestureRecord,
    LinkRecord,
    MouseBook,
    MousePanel,
    MouseRegistry,
    MouseVerdict,
    MouseView,
    book_record,
    build_book,
    build_gesture,
    build_link,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    derive_guide,
    derive_panel,
    derive_verdict,
    editor_link,
    format_book,
    format_gesture,
    format_guide,
    format_link,
    format_mouse_screen,
    format_panel,
    format_road,
    format_verdict,
    format_view,
    gesture_for_road,
    gesture_gaps,
    gesture_passes,
    gesture_plain_words,
    gesture_record,
    gestures_for_area,
    guide_plain_words,
    guide_record,
    inspect_mouse_source,
    link_for_target,
    link_plain_words,
    link_record,
    load_mouse_manners,
    load_mouse_manners_file,
    normalize_area,
    normalize_gesture,
    normalize_view_filter,
    panel_plain_words,
    panel_record,
    parse_mouse_args,
    passing_gestures,
    plain_lines,
    plain_words,
    shown_gestures,
    total_gestures,
    validate_book,
    validate_gesture,
    validate_link,
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
EXAMPLE_TITLE = "Mouse manners at the M-187 slice boundary"


def _gesture(**overrides):
    fields = {
        "gesture_id": "gesture-test",
        "seq": 1,
        "title": "A test gesture",
        "area": "editor",
        "gesture": "drag-select",
        "road": "drag",
        "detail": "A test gesture held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_gesture(fields)


def _stored_gesture(gesture):
    return gesture.to_record()


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _stored_view(view):
    return view.to_record()


def _link(**overrides):
    fields = {
        "link_id": "link-test",
        "seq": 1,
        "path": "mythic_agent/terminal.py",
        "line": 279,
        "editor": "the user's editor",
        "title": "A test link",
        "detail": "A test link held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_link(fields)


def _book(gestures=None, views=None, links=None, **overrides):
    fields = {
        "schema": MOUSE_MANNERS_SCHEMA,
        "slice": "M-188",
        "guide": {"title": "A test mouse book"},
        "gestures": [_stored_gesture(item) for item in (
            gestures if gestures is not None else [_gesture()])],
        "views": [_stored_view(item) for item in (
            views if views is not None else [_view()])],
        "links": [item.to_record() for item in (links or [])],
        "panels": [],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(gestures=[
        _gesture(),
        _gesture(gesture_id="gesture-touch", seq=2,
                 title="Pan by touch", area="review",
                 gesture="scroll", road=""),
    ])


# ---------------------------------------------------------------------
# The shipped example book, the roadmap and the charter.
# ---------------------------------------------------------------------


def test_shipped_book_loads_with_pinned_shape():
    book = load_mouse_manners()
    assert book.title == EXAMPLE_TITLE
    assert book.gesture_ids() == (
        "gesture-open-file-link", "gesture-place-cursor",
        "gesture-drag-select", "gesture-scroll-transcript",
        "gesture-touch-pan", "gesture-click-approve")
    assert [v.view_id for v in book.views] == [
        "view-all", "view-wired"]
    assert [m.path for m in book.links] == [
        "mythic_agent/terminal.py",
        "mythic_agent/ui/screens/chat_screen.py"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m187-boundary"
    assert panel.as_of == "2026-11-09"
    assert [row.item_id for row in panel.rows] == list(book.gesture_ids())
    derived = derive_panel(book, "view-all")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 6
    assert panel.total_shown == derived.total_shown == 6
    assert {c.wire: c.items for c in panel.wire_counts} == {
        "wired": 5, "unwired": 1}
    assert derive_verdict(book, "view-all").verdict == "strained"
    assert derive_verdict(book, "view-all").passing_shown == 5
    assert derive_verdict(book, "view-wired").verdict == "open"
    assert derive_verdict(book, "view-wired").passing_shown == 5
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / MOUSE_MANNERS_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == MOUSE_MANNERS_SCHEMA
    assert raw["slice"] == "M-188"
    assert "verdict" not in raw
    assert "gesture_guide" not in raw


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-188")]
    assert slice_.title == "Mouse manners"
    assert slice_.part == 8
    assert "click, drag-select, scroll" in slice_.summary
    assert "links that open files at line numbers" in slice_.summary
    assert "user's editor" in slice_.summary
    assert MOUSE_MANNERS_SLICE == "M-188"


def test_charter_does_not_name_m188():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert owners.count("M-187") == 1
    assert "M-188" not in owners


def test_closed_vocabularies():
    assert WIRE_WORDS == ("wired", "unwired")
    assert AREAS == (
        "chat", "terminal", "editor", "review", "settings",
        "onboarding", "lessons", "command palace")
    assert GESTURES == ("click", "drag-select", "scroll", "link")
    assert VIEW_FILTERS == ("all", "wired", "unwired")
    assert VERDICT_WORDS == ("open", "strained", "shut")
    assert GUIDE_ACTION == "guide"
    assert EXAMPLE_ROAD == "click"
    assert normalize_area("Command Palace") == "command palace"
    assert normalize_gesture("DRAG-SELECT") == "drag-select"
    assert normalize_view_filter("ALL") == "all"
    with pytest.raises(ValueError):
        normalize_area("the void")
    with pytest.raises(ValueError):
        normalize_gesture("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    assert "held as data alone" in MOUSE_RULE
    assert "move no pointer" in MOUSE_RULE
    assert "M-188" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /mouse")


def test_shipped_book_judged_honestly_as_data():
    book = load_mouse_manners()
    cursor = book.gesture_for("gesture-place-cursor")
    assert gesture_passes(cursor) is True
    assert gesture_gaps(cursor) == ()
    assert plain_lines(cursor) == (
        "Gesture: Place the cursor",
        "Area: editor",
        "Road: left click")
    touch = book.gesture_for("gesture-touch-pan")
    assert gesture_gaps(touch) == ("no mouse road",)
    assert gesture_passes(touch) is False
    assert [g.gesture_id for g in passing_gestures(book)] == [
        "gesture-open-file-link", "gesture-place-cursor",
        "gesture-drag-select", "gesture-scroll-transcript",
        "gesture-click-approve"]
    assert total_gestures(book) == 6
    guide = derive_guide(book)
    assert [e.road for e in guide.entries] == [
        "click", "left click", "drag", "wheel", "left click"]
    assert guide.gaps == ("gesture-touch-pan",)
    assert gesture_for_road(book, "click").gesture_id == (
        "gesture-open-file-link")
    assert gesture_for_road(book, "triple click") is None
    assert editor_link(book).link_id == "link-terminal-help"
    assert link_for_target(
        book, "mythic_agent/terminal.py", 279).link_id == (
            "link-terminal-help")
    assert link_for_target(book, "nope.py") is None


# ---------------------------------------------------------------------
# The held gesture: judged whole, its telling derived.
# ---------------------------------------------------------------------


def test_gesture_record_round_trips():
    gesture = _gesture()
    assert validate_gesture(gesture) is gesture
    rebuilt = build_gesture(_stored_gesture(gesture))
    assert rebuilt == gesture
    assert rebuilt.item_id == "gesture-test"
    assert rebuilt.road == "drag"
    record = gesture_record(gesture)
    assert record["type"] == "mouse_gesture"
    assert record["passes"] is True
    assert record["gaps"] == []


def test_gesture_refuses_stored_judgements():
    for key in ("wire", "wired", "gaps", "segment", "verdict",
                "guide", "entries", "coverage"):
        fields = _stored_gesture(_gesture())
        fields[key] = "stored"
        with pytest.raises(ValueError):
            build_gesture(fields)
    fields = _stored_gesture(_gesture())
    fields["surprise"] = "stored"
    with pytest.raises(ValueError):
        build_gesture(fields)


def test_gesture_refuses_a_live_mouse_road():
    for key in ("move_pointer", "pointer_move", "opens_file",
                "launches_editor", "click_now"):
        fields = _stored_gesture(_gesture())
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_gesture(fields)
        assert "held as data alone" in str(caught.value)
    for key in ("opens_file", "follows_link"):
        fields = _link().to_record()
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_link(fields)
        assert "held as data alone" in str(caught.value)
    record = _link(line=279)
    assert validate_link(record) is record
    assert record.line == 279
    assert link_record(record)["type"] == "mouse_link"


def test_gesture_vocabularies_are_closed():
    assert _gesture(area="CHAT").area == "chat"
    assert _gesture(gesture="CLICK").gesture == "click"
    with pytest.raises(ValueError):
        _gesture(area="a hunch")
    with pytest.raises(ValueError):
        _gesture(gesture="pinch")
    with pytest.raises(ValueError):
        _gesture(title="   ")
    with pytest.raises(ValueError):
        _gesture(seq=0)
    with pytest.raises(ValueError):
        _gesture(road=5)
    with pytest.raises(ValueError):
        _gesture(detail="   ")


def test_plain_telling_derives_from_the_gestures_own_fields():
    gesture = _gesture(
        title="Test Gesture", area="editor", road="",
        detail="The road waits on a held gesture.")
    lines = plain_lines(gesture)
    assert lines[0] == "Gesture: Test Gesture"
    assert lines[1] == "Area: editor"
    assert lines[2] == "Road: none"
    assert plain_words(gesture) == gesture_plain_words(gesture)
    assert "Test Gesture" in plain_words(gesture)
    assert "held gesture" in plain_words(gesture)


def test_unwired_gesture_stands_named_in_its_gaps():
    gesture = _gesture(road="")
    assert gesture_gaps(gesture) == ("no mouse road",)
    assert gesture_passes(gesture) is False
    text = format_gesture(gesture)
    assert "stands unwired" in text
    current_text = format_gesture(_gesture())
    assert "stands wired to the mouse" in current_text


def test_view_and_link_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(_stored_view(view)) == view
    record = view_record(view)
    assert record["type"] == "mouse_view"
    assert record["view_filter"] == "all"
    assert "shows all gestures" in view_plain_words(view)
    assert "filter all" in format_view(view)
    with pytest.raises(ValueError):
        _view(view_filter="some")
    link = _link()
    assert build_link(link.to_record()) == link
    assert "File link mythic_agent/terminal.py:279" in format_link(link)
    assert "opens no file" in format_link(link)
    assert "line 279" in link_plain_words(link)
    with pytest.raises(ValueError):
        _link(line=0)


# ---------------------------------------------------------------------
# The guide and the link roads: derived at call time, never held.
# ---------------------------------------------------------------------


def test_guide_is_derived_from_the_held_roads_alone():
    book = _mixed_book()
    guide = derive_guide(book)
    assert [e.gesture_id for e in guide.entries] == ["gesture-test"]
    assert guide.entries[0].road == "drag"
    assert guide.gaps == ("gesture-touch",)
    assert guide_record(guide)["type"] == "mouse_guide"
    assert guide_record(book)["gaps"] == ["gesture-touch"]
    assert "1 roads" in guide_plain_words(book)
    text = format_guide(book)
    assert "Gesture guide" in text
    assert "drag - A test gesture (gesture-test)" in text
    assert "gesture-touch" in text
    assert "moves no pointer" in text


def test_road_reaches_its_gesture_and_an_unheld_road_reaches_nothing():
    book = _mixed_book()
    assert gesture_for_road(book, "drag").gesture_id == "gesture-test"
    assert gesture_for_road(book, "triple click") is None
    assert gesture_for_road(book, "") is None
    assert "A test gesture" in format_road(book, "drag")
    assert "reaches nothing in this book" in format_road(
        book, "triple click")


def test_editor_link_is_held_as_data():
    book = _book(links=[_link(), _link(
        link_id="link-two", seq=2, path="other.py", line=12,
        title="The second link")])
    assert editor_link(book).link_id == "link-test"
    assert link_for_target(book, "other.py").link_id == "link-two"
    assert link_for_target(book, "other.py", 12).link_id == "link-two"
    assert link_for_target(book, "other.py", 99) is None
    bare = _book()
    assert editor_link(bare) is None
    assert link_for_target(bare, "other.py") is None
    text = format_link(editor_link(book))
    assert "held as data alone" in text
    assert "launches no editor" in text


def test_link_targets_stand_held_whole():
    link = _link(path="a/b.py", line=42, editor="the user's editor")
    assert link.line == 42
    rebuilt = build_link(link.to_record())
    assert rebuilt == link
    assert rebuilt.path == "a/b.py"
    assert rebuilt.editor == "the user's editor"
    with pytest.raises(ValueError):
        _link(line="279")
    with pytest.raises(ValueError):
        _link(editor="   ")
    with pytest.raises(ValueError):
        _link(path="   ")


def test_panel_is_derived_and_a_stored_panel_must_agree():
    book = _mixed_book()
    panel = derive_panel(book)
    assert isinstance(panel, MousePanel)
    assert panel.total_items == 2
    assert panel.total_shown == 2
    assert validate_panel(panel, book) is panel
    assert build_panel(panel.to_record(), book).rows == panel.rows
    assert build_row(panel.rows[0], book.gestures[0]) == panel.rows[0]
    assert validate_row(panel.rows[0], book.gestures[0]) == panel.rows[0]
    tampered = dict(panel.to_record())
    tampered["total_shown"] = 99
    with pytest.raises(ValueError):
        build_panel(tampered, book)
    renamed = dict(panel.to_record())
    renamed["panel_id"] = "panel-renamed"
    assert build_panel(renamed, book).panel_id == "panel-renamed"
    record = panel_record(panel, book)
    assert record["type"] == "mouse_panel"
    assert record["panel_id"] == panel.panel_id


def test_verdict_is_derived_from_the_shown_gestures():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert isinstance(verdict, MouseVerdict)
    assert verdict.verdict == "strained"
    assert verdict.total_shown == 2
    assert verdict.passing_shown == 1
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    record = verdict_record(verdict, book)
    assert record["type"] == "mouse_verdict"
    assert "strained" in verdict_plain_words(book)
    assert "strained" in format_verdict(book)


def test_verdict_open_and_shut_edges():
    whole = _book(gestures=[_gesture()])
    assert derive_verdict(whole).verdict == "open"
    absent_book = _book(gestures=[_gesture(road="")])
    assert derive_verdict(absent_book).verdict == "shut"
    none_shown = _book(
        gestures=[_gesture(road="")],
        views=[_view(view_filter="wired")])
    verdict = derive_verdict(none_shown)
    assert verdict.total_shown == 0
    assert verdict.verdict == "shut"


def test_shown_and_area_readings():
    book = _mixed_book()
    assert [g.gesture_id for g in shown_gestures(book)] == [
        "gesture-test", "gesture-touch"]
    wired_view = _view(view_id="view-w", seq=2, view_filter="wired")
    book2 = _book(
        gestures=[_gesture(), _gesture(
            gesture_id="gesture-touch", seq=2, title="Pan by touch",
            area="review", gesture="scroll", road="")],
        views=[_view(), wired_view])
    assert [g.gesture_id for g in shown_gestures(book2, wired_view)] == [
        "gesture-test"]
    assert [g.gesture_id for g in gestures_for_area(book2, "review")] == [
        "gesture-touch"]
    assert [g.gesture_id for g in passing_gestures(book2)] == [
        "gesture-test"]
    assert total_gestures(book2) == 2
    with pytest.raises(ValueError):
        gestures_for_area(book2, "the void")


def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(gestures=[_gesture(), _gesture(seq=2)])
    with pytest.raises(ValueError):
        _book(gestures=[_gesture(), _gesture(gesture_id="gesture-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(view_filter="wired")])
    with pytest.raises(ValueError) as caught:
        _book(links=[_link(), _link(link_id="link-two", seq=2)])
    assert "one link stands per file line" in str(caught.value)
    fields = {
        "schema": MOUSE_MANNERS_SCHEMA, "slice": "M-188",
        "guide": {"title": "A test mouse book"},
        "gestures": [_stored_gesture(_gesture())],
        "views": [_stored_view(_view())], "links": [],
        "panels": [], "verdict": "open",
    }
    with pytest.raises(ValueError):
        build_book(fields)
    del fields["verdict"]
    fields["gesture_guide"] = "stored"
    with pytest.raises(ValueError):
        build_book(fields)
    raw = {
        "schema": MOUSE_MANNERS_SCHEMA, "slice": "M-188",
        "guide": {"title": "A test mouse book"},
        "gestures": [], "views": [], "links": [], "panels": [],
        "move_pointer": True,
    }
    with pytest.raises(ValueError) as caught:
        build_book(raw)
    assert "live mouse road" in str(caught.value)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / MOUSE_MANNERS_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "mouse_manners.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_mouse_manners_file(path)
    assert book.title == EXAMPLE_TITLE
    assert total_gestures(book) == 6


def test_registry_holds_gestures_and_views_one_by_one():
    registry = MouseRegistry()
    assert registry.list_items() == ()
    held = registry.register_gesture(_gesture())
    assert held.gesture_id == "gesture-test"
    registry.register_view(_view())
    assert [i.item_id if hasattr(i, "item_id") else i.view_id
            for i in registry.list_items()] == ["gesture-test", "view-test"]
    assert registry.get_gesture("gesture-test").title == "A test gesture"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.book().title == "An unheld mouse book"
    with pytest.raises(ValueError):
        registry.register_gesture(_gesture(seq=2))
    with pytest.raises(ValueError):
        registry.register_gesture(_gesture(gesture_id="gesture-two"))
    with pytest.raises(KeyError):
        registry.get_gesture("gesture-nope")


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = MouseRegistry()
    book = _mixed_book()
    held = registry.register_book(book)
    assert held.title == "A test mouse book"
    assert len(registry.list_gestures()) == 2
    other = _book(gestures=[_gesture(
        gesture_id="gesture-x", seq=9, title="Other", road="wheel")],
        views=[_view(view_id="view-x", seq=9)])
    object.__setattr__(other, "title", "Another title")
    with pytest.raises(ValueError):
        registry.register_book(other)


def test_plain_words_and_formatters():
    book = _mixed_book()
    assert "in area 'editor'" in format_book(book)
    assert "gesture-touch" in format_book(book, "review")
    assert "gesture-test" not in format_book(book, "review")
    assert "Mouse panel under view view-test" in format_panel(book)
    assert panel_plain_words(book).startswith(
        "The mouse book holds 2 gestures")
    screen = format_mouse_screen(book)
    assert "Mouse Manners (M-188)" in screen
    assert PLAIN_EXPLANATION in screen
    assert "gesture-touch-pan" not in screen
    assert "gesture-touch" in screen
    record = book_record(book)
    assert record["type"] == "mouse_book"
    assert record["title"] == "A test mouse book"
    assert len(record["gestures"]) == 2
    panel = derive_panel(book)
    assert panel_record(panel, book)["rows"][0]["item_id"] == "gesture-test"
    assert verdict_record(derive_verdict(book), book)["verdict"] == (
        "strained")
    gesture_text = format_gesture(book.gestures[0])
    assert "Gesture: A test gesture" in gesture_text
    assert "Road: drag" in gesture_text


def test_parse_args_inspect_and_loader_roads():
    assert parse_mouse_args("") == ("show", None)
    assert parse_mouse_args("show") == ("show", None)
    assert parse_mouse_args(None) == ("show", None)
    assert parse_mouse_args("gesture gesture-test") == (
        "gesture", "gesture-test")
    assert parse_mouse_args("road left click") == ("road", "left click")
    assert parse_mouse_args("area command palace") == (
        "area", "command palace")
    assert parse_mouse_args("view view-test") == ("view", "view-test")
    assert parse_mouse_args("link link-test") == ("link", "link-test")
    assert parse_mouse_args("guide") == ("guide", None)
    assert parse_mouse_args("panel") == ("panel", None)
    assert parse_mouse_args("verdict") == ("verdict", None)
    for bad in ("dance", "gesture", "road", "area", "guide now",
                "link a b"):
        with pytest.raises(ValueError):
            parse_mouse_args(bad)
    gesture = _gesture()
    assert inspect_mouse_source(gesture) == {
        "kind": "gesture", "gesture_id": "gesture-test"}
    assert inspect_mouse_source(_stored_gesture(gesture))["kind"] == (
        "gesture")
    assert inspect_mouse_source(_stored_view(_view()))["kind"] == (
        "view")
    assert inspect_mouse_source(_link().to_record())["kind"] == "link"
    assert inspect_mouse_source(42)["kind"] == "unknown"
    book = load_mouse_manners({
        "schema": MOUSE_MANNERS_SCHEMA, "slice": "M-188",
        "guide": {"title": "A judged book"},
        "gestures": [_stored_gesture(_gesture())],
        "views": [_stored_view(_view())], "links": [], "panels": []})
    assert isinstance(book, MouseBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_mouse_manners({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_mouse_manners({"slice": "M-999"})
    built = build_gesture(
        gesture_id="gesture-kw", seq=3, title="Kw Gesture",
        area="chat", gesture="click", road="click",
        detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="session-test")
    assert built.gesture_id == "gesture-kw"
    assert gesture_passes(built) is True


# ---------------------------------------------------------------------
# M-188 agent layer: the agent holds a mouse book
# for the session, gestures and views are published
# as session news through the checkpoint road
# (journal first, deduped per shape), the panel
# and verdict are derived at call time from the
# whole book under a view, never held, the guide
# is derived from the book's held gestures, and the
# file links are held as data beside them -
# holding one opens no file. This layer moves no
# pointer, renders no live UI, opens no file
# and persists nothing beyond the
# session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _mouse_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_mouse_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / MOUSE_MANNERS_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "mouse_manners.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestMouseAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.mouse_manners_status()
        assert status["gestures"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["mouse"]["title"] == EXAMPLE_TITLE
        assert len(status["mouse"]["gestures"]) == 6
        assert len(status["mouse"]["views"]) == 2
        assert len(status["mouse"]["links"]) == 2
        assert status["panel"]["total_items"] == 6
        assert status["panel"]["total_shown"] == 6
        assert status["panels"][0]["panel_id"] == "panel-m187-boundary"
        assert status["verdict"]["verdict"] == "strained"
        assert status["verdict"]["passing_shown"] == 5
        assert [e["road"] for e in status["guide"]["entries"]] == [
            "click", "left click", "drag", "wheel", "left click"]
        assert status["guide"]["gaps"] == ["gesture-touch-pan"]
        assert status["editor_link"]["link_id"] == "link-terminal-help"
        assert "held as data alone" in status["rule"]
        assert "Approve a tool call" in status["plain_words"]
        assert "Mouse Manners (M-188)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._mouse_manners_registry()
        assert agent._mouse_manners_registry() is first
        assert agent._mouse_manners_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.mouse_manners_status()
        assert agent.get_mouse_gesture("gesture-place-cursor").title == (
            "Place the cursor")
        assert agent.get_mouse_view("view-all").view_filter == "all"
        assert agent.get_mouse_link("link-terminal-help").link_id == "link-terminal-help"
        assert [a.gesture_id for a in agent.mouse_gestures_for_area(
            "editor")] == ["gesture-place-cursor", "gesture-drag-select"]
        assert [a.gesture_id for a in agent.mouse_gestures_passing()] == [
            "gesture-open-file-link", "gesture-place-cursor", "gesture-drag-select",
            "gesture-scroll-transcript", "gesture-click-approve"]
        agent.mouse_manners_panel()
        agent.mouse_manners_verdict()
        agent.mouse_guide()
        agent.report_mouse_manners()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("mouse")] == []
        with pytest.raises(KeyError):
            agent.get_mouse_gesture("gesture-nope")
        with pytest.raises(KeyError):
            agent.get_mouse_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_mouse_link("link-nope")
        with pytest.raises(ValueError):
            agent.mouse_gestures_for_area("the void")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_mouse_gesture(_gesture())
        status = agent.mouse_manners_status()
        assert [a["gesture_id"] for a in status["gestures"]] == ["gesture-test"]
        assert status["book"]["title"] == "An unheld mouse book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["road"] for e in status["guide"]["entries"]] == [
            "drag"]
        assert status["editor_link"] is None
        assert "gesture-test" in status["screen"]

    def test_held_act_never_falls_back_to_the_example(
            self, agent):
        agent.register_mouse_gesture(_gesture())
        with pytest.raises(KeyError):
            agent.get_mouse_gesture("gesture-place-cursor")
        with pytest.raises(KeyError):
            agent.get_mouse_view("view-all")
        with pytest.raises(KeyError):
            agent.get_mouse_link("modal")
        act = agent.get_mouse_gesture("gesture-test")
        assert act.title == "A test gesture"
        assert agent.mouse_manners_book().title == (
            "An unheld mouse book")

    def test_links_and_guide_stand_in_the_example(self, agent):
        first = agent.get_mouse_link("link-terminal-help")
        assert first.link_id == "link-terminal-help"
        assert first.path == "mythic_agent/terminal.py"
        status = agent.mouse_manners_status()
        assert status["guide"]["gaps"] == ["gesture-touch-pan"]
        assert status["editor_link"]["path"] == "mythic_agent/terminal.py"
        assert status["editor_link"]["line"] == 279


class TestMouseAgentHolding:
    def test_register_act_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_mouse_gesture(_gesture())
        assert result["gesture"]["gesture_id"] == "gesture-test"
        assert result["record_news"]["type"] == "mouse_gesture"
        assert "gesture-test" in result["screen"]
        events = _mouse_events(store, session_id, "mouse_gesture")
        assert len(events) == 1
        agent.close()

    def test_duplicate_act_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_mouse_gesture(_gesture())
        with pytest.raises(ValueError):
            agent.register_mouse_gesture(_gesture(seq=9))
        with pytest.raises(ValueError):
            agent.register_mouse_gesture(_gesture(gesture_id="gesture-two"))
        events = _mouse_events(store, session_id, "mouse_gesture")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_mouse_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_mouse_events(
            store, session_id, "mouse_view")) == 1
        agent.close()

    def test_view_road_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_mouse_gesture(_gesture())
        result = agent.view_mouse("wired")
        assert result["view"]["view_filter"] == "wired"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "mouse_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "open"
        assert len(_mouse_events(
            store, session_id, "mouse_view")) == 1
        assert len(_mouse_events(
            store, session_id, "mouse_panel")) == 1
        assert len(_mouse_events(
            store, session_id, "mouse_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_mouse_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "mouse_gesture", "mouse_view"]
        assert len(_mouse_events(
            store, session_id, "mouse_gesture")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_mouse_book()
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "mouse_panel"
        assert result["guide_record"]["gaps"] == ["gesture-touch-pan"]
        with pytest.raises(ValueError):
            agent.record_mouse_book()
        assert len(_mouse_events(
            store, session_id, "mouse_gesture")) == 6
        assert len(_mouse_events(
            store, session_id, "mouse_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_mouse_book_file(tmp_path)
        book = load_mouse_manners_file(path)
        result = agent.record_mouse_book(book)
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_mouse_manners()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "strained"
        assert report["guide"]["gaps"] == ["gesture-touch-pan"]
        assert "gesture-place-cursor" in report["book_text"]
        assert "drag - Drag to select text" in report["guide_text"]
        agent.register_mouse_gesture(_gesture())
        report = agent.report_mouse_manners()
        assert report["book"]["title"] == "An unheld mouse book"
        assert report["panel"] is None
        assert report["verdict"] is None


class TestMouseTerminalSurface:
    def test_show_gesture_road_area_view_link_guide_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/mouse")
        assert "Mouse Manners (M-188)" in text
        _, _, text = _slash(agent, "/mouse gesture gesture-place-cursor")
        assert "Gesture: Place the cursor" in text
        _, _, text = _slash(agent, "/mouse road drag")
        assert "Drag to select text" in text
        _, _, text = _slash(agent, "/mouse road triple click")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/mouse area editor")
        assert "gesture-drag-select" in text
        assert "gesture-open-file-link" not in text
        _, _, text = _slash(agent, "/mouse view view-all")
        assert "filter all" in text
        _, _, text = _slash(agent, "/mouse link link-terminal-help")
        assert "File link mythic_agent/terminal.py:279" in text
        _, _, text = _slash(agent, "/mouse guide")
        assert "Gesture guide" in text
        assert "gesture-drag-select" in text
        _, _, text = _slash(agent, "/mouse panel")
        assert "Mouse panel under view view-all" in text
        _, _, text = _slash(agent, "/mouse verdict")
        assert "strained" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/mouse [show|gesture <gesture-id>"
                "|road <road>|area <area>|view <view-id>"
                "|link <link-id>|guide|panel|verdict]") in text
        _, _, text = _slash(agent, "/mouse dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/mouse gesture gesture-nope")
        assert "no gesture named" in text


@pytest.fixture()
def mouse_handler(agent, monkeypatch):
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


def _mouse_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestMouseCommand:
    def test_show_is_default(self, mouse_handler, agent):
        mouse_handler._handle_mouse("")
        assert "Mouse Manners (M-188)" in (
            _mouse_published_text(mouse_handler))

    def test_gesture_road_area_view_link_guide_panel_verdict(
            self, mouse_handler, agent):
        mouse_handler._handle_mouse("gesture gesture-place-cursor")
        assert "Gesture: Place the cursor" in _mouse_published_text(
            mouse_handler)
        mouse_handler._handle_mouse("road drag")
        assert "Drag to select text" in _mouse_published_text(
            mouse_handler)
        mouse_handler._handle_mouse("area editor")
        assert "gesture-drag-select" in _mouse_published_text(mouse_handler)
        mouse_handler._handle_mouse("view view-all")
        assert "filter all" in _mouse_published_text(mouse_handler)
        mouse_handler._handle_mouse("link link-terminal-help")
        assert "File link mythic_agent/terminal.py:279" in _mouse_published_text(mouse_handler)
        mouse_handler._handle_mouse("guide")
        assert "Gesture guide" in _mouse_published_text(mouse_handler)
        mouse_handler._handle_mouse("panel")
        assert "Mouse panel under view" in _mouse_published_text(
            mouse_handler)
        mouse_handler._handle_mouse("verdict")
        assert "strained" in _mouse_published_text(mouse_handler)

    def test_bad_grammar_is_published(
            self, mouse_handler, agent):
        mouse_handler._handle_mouse("dance party")
        assert USAGE in _mouse_published_text(mouse_handler)
        mouse_handler._handle_mouse("gesture gesture-nope")
        assert "no gesture named" in _mouse_published_text(mouse_handler)


class TestChatScreenRoutingMouse:
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
        screen.handle_command("/mouse panel", _FakeLog())
        assert calls == [("/mouse", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/mouse[/green] - show mouse manners (M-188)" in (
            text)
        assert ('"/mouse": "Usage: /mouse | '
                '/mouse gesture <gesture-id>') in text


class TestMouseDerivedRoads:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.mouse_manners_panel()
        assert panel.total_shown == 6
        assert panel.panel_id == "panel-view-all"
        verdict = agent.mouse_manners_verdict()
        assert verdict.verdict == "strained"
        found = agent.mouse_manners_verdict("view-wired")
        assert found.verdict == "open"
        assert found.passing_shown == 5
        agent.register_mouse_gesture(_gesture())
        with pytest.raises(ValueError):
            agent.mouse_manners_panel()
        with pytest.raises(ValueError):
            agent.mouse_manners_verdict()

    def test_view_road_over_an_unshown_filter_is_shut(self, agent):
        agent.register_mouse_gesture(_gesture(road=""))
        result = agent.view_mouse("wired")
        assert result["verdict_record"]["verdict"] == "shut"
        assert result["verdict_record"]["total_shown"] == 0

    def test_print_road_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.mouse_guide()
        assert [e["road"] for e in result["guide"]["entries"]] == [
            "click", "left click", "drag", "wheel", "left click"]
        assert result["guide"]["gaps"] == ["gesture-touch-pan"]
        assert "drag - Drag to select text (gesture-drag-select)" in (
            result["guide_text"])
        act = agent.get_mouse_gesture("gesture-touch-pan")
        assert gesture_gaps(act) == ("no mouse road",)
        assert gesture_passes(act) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("mouse")] == []
        agent.close()
