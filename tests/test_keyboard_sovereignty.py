"""M-187 Keyboard Sovereignty - pure-layer tests.

TIER: integration

The pure layer is keyboard sovereignty, held as
data: one record per act, held whole - under
its title, the area it lives in in the closed
vocabulary, the key that reaches it, named as
data, and its detail - the vim-mode prompt
option held as data beside them, and the
printable keymap derived at call time from the
held acts' keys alone, never stored where it
could drift. An act naming no key stands
unreachable, named in its gaps; two acts under
one key refuse by name. A record claiming a live
key press, a live UI render or a live prompt-mode
change refuses by name, and a stored keymap or
verdict refuses by name. The panel is derived
for one held view and the verdict is derived
for the whole book under one view. The shipped
example book is held in a data file, and a
loader reads a book from any file. This layer
presses no keys, renders no live UI, changes no
live prompt mode and writes nothing: it holds
keyboard sovereignty as data and tells it.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.keyboard_sovereignty import (
    AREAS,
    EXAMPLE_KEY,
    KEYBOARD_RULE,
    KEYBOARD_SOVEREIGNTY_RESOURCE,
    KEYBOARD_SOVEREIGNTY_SCHEMA,
    KEYBOARD_SOVEREIGNTY_SLICE,
    MODES,
    PLAIN_EXPLANATION,
    PRINT_ACTION,
    REACH_WORDS,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    ActRecord,
    KeyboardBook,
    KeyboardPanel,
    KeyboardRegistry,
    KeyboardVerdict,
    KeyboardView,
    ModeRecord,
    act_for_key,
    act_gaps,
    act_passes,
    act_plain_words,
    act_record,
    acts_for_area,
    book_record,
    build_act,
    build_book,
    build_mode,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    derive_keymap,
    derive_panel,
    derive_verdict,
    format_act,
    format_book,
    format_key,
    format_keyboard_screen,
    format_keymap,
    format_mode,
    format_panel,
    format_verdict,
    format_view,
    inspect_keyboard_source,
    keymap_plain_words,
    keymap_record,
    load_keyboard_sovereignty,
    load_keyboard_sovereignty_file,
    mode_for_word,
    mode_plain_words,
    mode_record,
    normalize_area,
    normalize_mode,
    normalize_view_filter,
    panel_plain_words,
    panel_record,
    parse_keyboard_args,
    passing_acts,
    plain_lines,
    plain_words,
    segment_of,
    shown_acts,
    total_acts,
    validate_act,
    validate_book,
    validate_mode,
    validate_panel,
    validate_row,
    validate_verdict,
    validate_view,
    verdict_plain_words,
    verdict_record,
    view_plain_words,
    view_record,
    vim_mode,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.tui_redesign_charter import load_charter

ROOT = Path(__file__).resolve().parents[1]
ON = "2026-11-09"
BY = "the coordinator"
EXAMPLE_TITLE = "Keyboard sovereignty at the M-186 slice boundary"


def _act(**overrides):
    fields = {
        "act_id": "act-test",
        "seq": 1,
        "title": "A test act",
        "area": "terminal",
        "key": "Ctrl-T",
        "detail": "A test act held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_act(fields)


def _stored_act(act):
    return act.to_record()


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


def _mode(**overrides):
    fields = {
        "mode_id": "mode-test",
        "seq": 1,
        "mode": "modal",
        "title": "A test mode",
        "detail": "A test mode held as data, for the tests.",
        "grammar": ["Esc - return to normal mode."],
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_mode(fields)


def _book(acts=None, views=None, modes=None, **overrides):
    fields = {
        "schema": KEYBOARD_SOVEREIGNTY_SCHEMA,
        "slice": "M-187",
        "guide": {"title": "A test keyboard book"},
        "acts": [_stored_act(item) for item in (
            acts if acts is not None else [_act()])],
        "views": [_stored_view(item) for item in (
            views if views is not None else [_view()])],
        "modes": [item.to_record() for item in (modes or [])],
        "panels": [],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(acts=[
        _act(),
        _act(act_id="act-drag", seq=2, title="Drag to select text",
             area="editor", key=""),
    ])


# ---------------------------------------------------------------------
# The shipped example book, the roadmap and the charter.
# ---------------------------------------------------------------------


def test_shipped_book_loads_with_pinned_shape():
    book = load_keyboard_sovereignty()
    assert book.title == EXAMPLE_TITLE
    assert book.act_ids() == (
        "act-ask-question", "act-undo-change", "act-open-keymap",
        "act-approve-tool", "act-drag-select", "act-toggle-plain")
    assert [v.view_id for v in book.views] == [
        "view-all", "view-reachable"]
    assert [m.mode for m in book.modes] == ["off", "modal"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m186-boundary"
    assert panel.as_of == "2026-11-09"
    assert [row.item_id for row in panel.rows] == list(book.act_ids())
    derived = derive_panel(book, "view-all")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 6
    assert panel.total_shown == derived.total_shown == 6
    assert {c.reach: c.items for c in panel.reach_counts} == {
        "reachable": 5, "unreachable": 1}
    assert derive_verdict(book, "view-all").verdict == "strained"
    assert derive_verdict(book, "view-all").passing_shown == 5
    assert derive_verdict(book, "view-reachable").verdict == "open"
    assert derive_verdict(book, "view-reachable").passing_shown == 5
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / KEYBOARD_SOVEREIGNTY_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == KEYBOARD_SOVEREIGNTY_SCHEMA
    assert raw["slice"] == "M-187"
    assert "verdict" not in raw
    assert "keymap" not in raw


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-187")]
    assert slice_.title == "Keyboard sovereignty"
    assert slice_.part == 8
    assert "every act reachable by keyboard" in slice_.summary
    assert "printable keymap" in slice_.summary
    assert "vim-mode" in slice_.summary
    assert KEYBOARD_SOVEREIGNTY_SLICE == "M-187"


def test_charter_names_m187_on_the_terminal_loop_row():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert owners.count("M-187") == 1
    row = charter.screen("terminal_loop")
    assert "M-187" in row.owning_slices
    assert row.verdict == "repair"
    assert "keyboard-only construction stays exactly as it is" in (
        row.direction)


def test_closed_vocabularies():
    assert REACH_WORDS == ("reachable", "unreachable")
    assert AREAS == (
        "chat", "terminal", "editor", "review", "settings",
        "onboarding", "lessons", "command palace")
    assert MODES == ("off", "modal")
    assert VIEW_FILTERS == ("all", "reachable", "unreachable")
    assert VERDICT_WORDS == ("open", "strained", "shut")
    assert PRINT_ACTION == "print"
    assert EXAMPLE_KEY == "Ctrl-K"
    assert normalize_area("Command Palace") == "command palace"
    assert normalize_mode("MODAL") == "modal"
    assert normalize_view_filter("ALL") == "all"
    with pytest.raises(ValueError):
        normalize_area("the void")
    with pytest.raises(ValueError):
        normalize_mode("insert")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    assert "held as data alone" in KEYBOARD_RULE
    assert "press no keys" in KEYBOARD_RULE
    assert "M-187" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /keymap")


def test_shipped_book_judged_honestly_as_data():
    book = load_keyboard_sovereignty()
    undo = book.act_for("act-undo-change")
    assert act_passes(undo) is True
    assert act_gaps(undo) == ()
    assert plain_lines(undo) == (
        "Act: Undo the last change",
        "Area: editor",
        "Key: Ctrl-Z")
    drag = book.act_for("act-drag-select")
    assert act_gaps(drag) == ("no key",)
    assert act_passes(drag) is False
    assert [a.act_id for a in passing_acts(book)] == [
        "act-ask-question", "act-undo-change", "act-open-keymap",
        "act-approve-tool", "act-toggle-plain"]
    assert total_acts(book) == 6
    keymap = derive_keymap(book)
    assert [e.key for e in keymap.entries] == [
        "Enter", "Ctrl-Z", "Ctrl-K", "y", "Ctrl-P"]
    assert keymap.gaps == ("act-drag-select",)
    assert act_for_key(book, "Ctrl-K").act_id == "act-open-keymap"
    assert act_for_key(book, "F9") is None
    assert vim_mode(book).mode_id == "mode-vim"
    assert mode_for_word(book, "off").mode_id == "mode-off"


# ---------------------------------------------------------------------
# The held act: judged whole, its telling derived.
# ---------------------------------------------------------------------


def test_act_record_round_trips():
    act = _act()
    assert validate_act(act) is act
    rebuilt = build_act(_stored_act(act))
    assert rebuilt == act
    assert rebuilt.item_id == "act-test"
    assert rebuilt.key == "Ctrl-T"
    record = act_record(act)
    assert record["type"] == "keyboard_act"
    assert record["passes"] is True
    assert record["gaps"] == []


def test_act_refuses_stored_judgements():
    for key in ("reach", "reachable", "gaps", "segment", "verdict",
                "keymap", "entries", "coverage"):
        fields = _stored_act(_act())
        fields[key] = "stored"
        with pytest.raises(ValueError):
            build_act(fields)
    fields = _stored_act(_act())
    fields["surprise"] = "stored"
    with pytest.raises(ValueError):
        build_act(fields)


def test_act_refuses_a_live_keyboard_road():
    for key in ("press_key", "key_press", "live_ui",
                "prompt_mode_change", "enables_vim"):
        fields = _stored_act(_act())
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_act(fields)
        assert "held as data alone" in str(caught.value)
    for key in ("press_key", "switches_mode"):
        fields = _mode().to_record()
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_mode(fields)
        assert "held as data alone" in str(caught.value)
    record = _mode(mode="MODAL")
    assert validate_mode(record) is record
    assert record.mode == "modal"
    assert mode_record(record)["type"] == "keyboard_mode"


def test_act_vocabularies_are_closed():
    assert _act(area="CHAT").area == "chat"
    with pytest.raises(ValueError):
        _act(area="a hunch")
    with pytest.raises(ValueError):
        _act(title="   ")
    with pytest.raises(ValueError):
        _act(seq=0)
    with pytest.raises(ValueError):
        _act(key=5)
    with pytest.raises(ValueError):
        _act(detail="   ")


def test_plain_telling_derives_from_the_acts_own_fields():
    act = _act(
        title="Test Act", area="editor", key="",
        detail="The road waits on a held key.")
    lines = plain_lines(act)
    assert lines[0] == "Act: Test Act"
    assert lines[1] == "Area: editor"
    assert lines[2] == "Key: none"
    assert plain_words(act) == act_plain_words(act)
    assert "Test Act" in plain_words(act)
    assert "held key" in plain_words(act)


def test_unreachable_act_stands_named_in_its_gaps():
    act = _act(key="")
    assert act_gaps(act) == ("no key",)
    assert act_passes(act) is False
    text = format_act(act)
    assert "stands unreachable" in text
    current_text = format_act(_act())
    assert "stands reachable by keyboard" in current_text


def test_view_and_mode_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(_stored_view(view)) == view
    record = view_record(view)
    assert record["type"] == "keyboard_view"
    assert record["view_filter"] == "all"
    assert "shows all acts" in view_plain_words(view)
    assert "filter all" in format_view(view)
    with pytest.raises(ValueError):
        _view(view_filter="some")
    mode = _mode()
    assert build_mode(mode.to_record()) == mode
    assert "Prompt mode modal" in format_mode(mode)
    assert "modal prompt" in mode_plain_words(mode)
    with pytest.raises(ValueError):
        _mode(mode="insert")


# ---------------------------------------------------------------------
# The keymap and the mode roads: derived at call time, never held.
# ---------------------------------------------------------------------


def test_keymap_is_derived_from_the_held_keys_alone():
    book = _mixed_book()
    keymap = derive_keymap(book)
    assert [e.act_id for e in keymap.entries] == ["act-test"]
    assert keymap.entries[0].key == "Ctrl-T"
    assert keymap.gaps == ("act-drag",)
    assert keymap_record(keymap)["type"] == "keyboard_keymap"
    assert keymap_record(book)["gaps"] == ["act-drag"]
    assert "1 keys" in keymap_plain_words(book)
    text = format_keymap(book)
    assert "Printable keymap" in text
    assert "Ctrl-T - A test act (act-test)" in text
    assert "act-drag" in text
    assert "presses no keys" in text


def test_key_reaches_its_act_and_an_unheld_key_reaches_nothing():
    book = _mixed_book()
    assert act_for_key(book, "Ctrl-T").act_id == "act-test"
    assert act_for_key(book, "F9") is None
    assert act_for_key(book, "") is None
    assert "A test act" in format_key(book, "Ctrl-T")
    assert "reaches nothing in this book" in format_key(book, "F9")


def test_vim_mode_option_is_held_as_data():
    book = _book(modes=[_mode(), _mode(
        mode_id="mode-plain", seq=2, mode="off",
        title="The prompt as it stands", grammar=[])])
    assert vim_mode(book).mode_id == "mode-test"
    assert mode_for_word(book, "OFF").mode_id == "mode-plain"
    bare = _book()
    assert vim_mode(bare) is None
    assert mode_for_word(bare, "modal") is None
    text = format_mode(vim_mode(book))
    assert "Esc - return to normal mode." in text
    assert "switches no live prompt mode" in text
    with pytest.raises(ValueError):
        mode_for_word(book, "insert")


def test_mode_grammar_and_off_mode_stand_held():
    mode = _mode(grammar=["i - enter insert.", "dd - clear the line."])
    assert mode.grammar == ("i - enter insert.", "dd - clear the line.")
    rebuilt = build_mode(mode.to_record())
    assert rebuilt.grammar == mode.grammar
    off = _mode(mode_id="mode-off", mode="OFF")
    assert off.mode == "off"
    assert normalize_mode("Modal") == "modal"
    with pytest.raises(ValueError):
        _mode(grammar="Esc leaves insert")


def test_panel_is_derived_and_a_stored_panel_must_agree():
    book = _mixed_book()
    panel = derive_panel(book)
    assert isinstance(panel, KeyboardPanel)
    assert panel.total_items == 2
    assert panel.total_shown == 2
    assert validate_panel(panel, book) is panel
    assert build_panel(panel.to_record(), book).rows == panel.rows
    assert build_row(panel.rows[0], book.acts[0]) == panel.rows[0]
    assert validate_row(panel.rows[0], book.acts[0]) == panel.rows[0]
    tampered = dict(panel.to_record())
    tampered["total_shown"] = 99
    with pytest.raises(ValueError):
        build_panel(tampered, book)
    renamed = dict(panel.to_record())
    renamed["panel_id"] = "panel-renamed"
    assert build_panel(renamed, book).panel_id == "panel-renamed"
    record = panel_record(panel, book)
    assert record["type"] == "keyboard_panel"
    assert record["panel_id"] == panel.panel_id


def test_verdict_is_derived_from_the_shown_acts():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert isinstance(verdict, KeyboardVerdict)
    assert verdict.verdict == "strained"
    assert verdict.total_shown == 2
    assert verdict.passing_shown == 1
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    record = verdict_record(verdict, book)
    assert record["type"] == "keyboard_verdict"
    assert "strained" in verdict_plain_words(book)
    assert "strained" in format_verdict(book)


def test_verdict_open_and_shut_edges():
    whole = _book(acts=[_act()])
    assert derive_verdict(whole).verdict == "open"
    absent_book = _book(acts=[_act(key="")])
    assert derive_verdict(absent_book).verdict == "shut"
    none_shown = _book(
        acts=[_act(key="")],
        views=[_view(view_filter="reachable")])
    verdict = derive_verdict(none_shown)
    assert verdict.total_shown == 0
    assert verdict.verdict == "shut"


def test_shown_and_area_readings():
    book = _mixed_book()
    assert [a.act_id for a in shown_acts(book)] == [
        "act-test", "act-drag"]
    reach_view = _view(view_id="view-r", seq=2, view_filter="reachable")
    book2 = _book(
        acts=[_act(), _act(
            act_id="act-drag", seq=2, title="Drag to select text",
            area="editor", key="")],
        views=[_view(), reach_view])
    assert [a.act_id for a in shown_acts(book2, reach_view)] == [
        "act-test"]
    assert [a.act_id for a in acts_for_area(book2, "editor")] == [
        "act-drag"]
    assert [a.act_id for a in passing_acts(book2)] == ["act-test"]
    assert total_acts(book2) == 2
    with pytest.raises(ValueError):
        acts_for_area(book2, "the void")


def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(acts=[_act(), _act(seq=2)])
    with pytest.raises(ValueError):
        _book(acts=[_act(), _act(act_id="act-two")])
    with pytest.raises(ValueError) as caught:
        _book(acts=[_act(), _act(act_id="act-two", seq=2)])
    assert "one act stands per key" in str(caught.value)
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(view_filter="reachable")])
    with pytest.raises(ValueError) as caught:
        _book(modes=[_mode(), _mode(mode_id="mode-two", seq=2)])
    assert "one mode record stands per mode" in str(caught.value)
    fields = {
        "schema": KEYBOARD_SOVEREIGNTY_SCHEMA, "slice": "M-187",
        "guide": {"title": "A test keyboard book"},
        "acts": [_stored_act(_act())],
        "views": [_stored_view(_view())], "modes": [],
        "panels": [], "verdict": "open",
    }
    with pytest.raises(ValueError):
        build_book(fields)
    del fields["verdict"]
    fields["keymap"] = "stored"
    with pytest.raises(ValueError):
        build_book(fields)
    raw = {
        "schema": KEYBOARD_SOVEREIGNTY_SCHEMA, "slice": "M-187",
        "guide": {"title": "A test keyboard book"},
        "acts": [], "views": [], "modes": [], "panels": [],
        "press_key": True,
    }
    with pytest.raises(ValueError) as caught:
        build_book(raw)
    assert "live keyboard road" in str(caught.value)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / KEYBOARD_SOVEREIGNTY_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "keyboard_sovereignty.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_keyboard_sovereignty_file(path)
    assert book.title == EXAMPLE_TITLE
    assert total_acts(book) == 6


def test_registry_holds_acts_and_views_one_by_one():
    registry = KeyboardRegistry()
    assert registry.list_items() == ()
    held = registry.register_act(_act())
    assert held.act_id == "act-test"
    registry.register_view(_view())
    assert [i.item_id if hasattr(i, "item_id") else i.view_id
            for i in registry.list_items()] == ["act-test", "view-test"]
    assert registry.get_act("act-test").title == "A test act"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.book().title == "An unheld keyboard book"
    with pytest.raises(ValueError):
        registry.register_act(_act(seq=2))
    with pytest.raises(ValueError):
        registry.register_act(_act(act_id="act-two", seq=3))
    with pytest.raises(ValueError):
        registry.register_act(_act(act_id="act-two"))
    with pytest.raises(KeyError):
        registry.get_act("act-nope")


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = KeyboardRegistry()
    book = _mixed_book()
    held = registry.register_book(book)
    assert held.title == "A test keyboard book"
    assert len(registry.list_acts()) == 2
    other = _book(acts=[_act(act_id="act-x", seq=9, title="Other",
                             key="F9")],
                  views=[_view(view_id="view-x", seq=9)])
    object.__setattr__(other, "title", "Another title")
    with pytest.raises(ValueError):
        registry.register_book(other)


def test_plain_words_and_formatters():
    book = _mixed_book()
    assert "in area 'terminal'" in format_book(book)
    assert "act-drag" in format_book(book, "editor")
    assert "act-test" not in format_book(book, "editor")
    assert "Keyboard panel under view view-test" in format_panel(book)
    assert panel_plain_words(book).startswith(
        "The keymap book holds 2 acts")
    screen = format_keyboard_screen(book)
    assert "Keyboard Sovereignty (M-187)" in screen
    assert PLAIN_EXPLANATION in screen
    assert "act-drag-select" not in screen
    assert "act-drag" in screen
    record = book_record(book)
    assert record["type"] == "keyboard_book"
    assert record["title"] == "A test keyboard book"
    assert len(record["acts"]) == 2
    panel = derive_panel(book)
    assert panel_record(panel, book)["rows"][0]["item_id"] == "act-test"
    assert verdict_record(derive_verdict(book), book)["verdict"] == (
        "strained")
    act_text = format_act(book.acts[0])
    assert "Act: A test act" in act_text
    assert "Key: Ctrl-T" in act_text


def test_parse_args_inspect_and_loader_roads():
    assert parse_keyboard_args("") == ("show", None)
    assert parse_keyboard_args("show") == ("show", None)
    assert parse_keyboard_args(None) == ("show", None)
    assert parse_keyboard_args("act act-test") == ("act", "act-test")
    assert parse_keyboard_args("key Ctrl-K") == ("key", "Ctrl-K")
    assert parse_keyboard_args("area command palace") == (
        "area", "command palace")
    assert parse_keyboard_args("view view-test") == ("view", "view-test")
    assert parse_keyboard_args("mode mode-vim") == ("mode", "mode-vim")
    assert parse_keyboard_args("print") == ("print", None)
    assert parse_keyboard_args("panel") == ("panel", None)
    assert parse_keyboard_args("verdict") == ("verdict", None)
    for bad in ("dance", "act", "key", "area", "print now",
                "mode a b"):
        with pytest.raises(ValueError):
            parse_keyboard_args(bad)
    act = _act()
    assert inspect_keyboard_source(act) == {
        "kind": "act", "act_id": "act-test"}
    assert inspect_keyboard_source(_stored_act(act))["kind"] == "act"
    assert inspect_keyboard_source(_stored_view(_view()))["kind"] == (
        "view")
    assert inspect_keyboard_source(_mode().to_record())["kind"] == "mode"
    assert inspect_keyboard_source(42)["kind"] == "unknown"
    book = load_keyboard_sovereignty({
        "schema": KEYBOARD_SOVEREIGNTY_SCHEMA, "slice": "M-187",
        "guide": {"title": "A judged book"},
        "acts": [_stored_act(_act())],
        "views": [_stored_view(_view())], "modes": [], "panels": []})
    assert isinstance(book, KeyboardBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_keyboard_sovereignty({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_keyboard_sovereignty({"slice": "M-999"})
    built = build_act(
        act_id="act-kw", seq=3, title="Kw Act",
        area="chat", key="F2",
        detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="session-test")
    assert built.act_id == "act-kw"
    assert act_passes(built) is True
