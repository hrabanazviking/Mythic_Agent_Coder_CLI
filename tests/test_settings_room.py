"""M-196 Settings as One Room - pure-layer tests.

TIER: integration

The pure layer is the settings room, held as
data: one record per setting, held whole as a
card - under its name, its section in the closed
vocabulary (model, keys, display, behaviour,
privacy), its current value and its current
source layer in the closed vocabulary (default,
project, user, session) held honestly (unknown
stays empty, never invented), the plain-language
meaning it carries, named as data, and its detail
- the notes held as data beside them, each naming
its setting, its stance and its target, and the
settings index derived at call time from the held
settings alone, never stored where it could drift.
A setting naming no plain meaning stands
incomplete, named in its gaps; two settings
standing for one setting id refuse by name, and
one stance record stands per setting stance. A
record claiming a setting was actually changed,
applied or saved, or that a config was actually
written, refuses by name, and a stored index or
verdict refuses by name. The panel is derived for
one held view and the verdict is derived for the
whole book under one view. The shipped example
book is held in a data file, and a loader reads a
book from any file. The M-171 charter names this
slice on TWO rows - S-02 the setup wizard
(verdict rebuild, co-owned with M-184 and M-182)
and S-05 the GitHub config modal (verdict keep,
sole owner M-196) - and the tests pin that
ownership live. This layer changes nothing,
applies nothing, saves nothing, writes no config
and opens no network: it holds the settings as
data and tells it.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.settings_room import (
    SECTIONS,
    LAYERS,
    EXAMPLE_MEANING,
    STANCES,
    INDEX_ACTION,
    SETTINGS_ROOM_RESOURCE,
    SETTINGS_ROOM_SCHEMA,
    SETTINGS_ROOM_SLICE,
    ROOM_RULE,
    PLAIN_EXPLANATION,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    READY_WORDS,
    SettingCard,
    NoteRecord,
    RoomBook,
    RoomPanel,
    SettingsRoomRegistry,
    RoomVerdict,
    RoomView,
    book_record,
    build_book,
    build_setting,
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
    format_setting,
    format_index,
    format_note,
    format_room_screen,
    format_panel,
    format_meaning,
    format_verdict,
    format_view,
    setting_for_meaning,
    setting_gaps,
    setting_passes,
    setting_plain_words,
    setting_record,
    settings_for_section,
    index_plain_words,
    index_record,
    inspect_setting_source,
    note_for_setting,
    note_plain_words,
    note_record,
    load_settings_room,
    load_settings_room_file,
    normalize_section,
    normalize_layer,
    normalize_stance,
    normalize_view_filter,
    panel_plain_words,
    panel_record,
    parse_room_args,
    passing_settings,
    plain_lines,
    plain_words,
    shown_settings,
    total_settings,
    validate_book,
    validate_setting,
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
EXAMPLE_TITLE = "Settings as one room at the M-195 slice boundary"


def _setting(**overrides):
    fields = {
        "setting_id": "setting-test",
        "seq": 1,
        "name": "A test setting",
        "section": "model",
        "value": "the session model",
        "layer": "session",
        "meaning": "the model that answers you",
        "detail": "A test setting held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "setting-test",
    }
    fields.update(overrides)
    return build_setting(fields)


def _stored_setting(setting):
    return setting.to_record()


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "setting-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _stored_view(view):
    return view.to_record()


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "setting_id": "setting-test",
        "stance": "note",
        "target": "the user",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "setting-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _book(settings=None, views=None, notes=None, **overrides):
    fields = {
        "schema": SETTINGS_ROOM_SCHEMA,
        "slice": "M-196",
        "settings_room": {"title": "A test settings book"},
        "settings": [_stored_setting(item) for item in (
            settings if settings is not None else [_setting()])],
        "views": [_stored_view(item) for item in (
            views if views is not None else [_view()])],
        "notes": [item.to_record() for item in (notes or [])],
        "panels": [],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(settings=[
        _setting(),
        _setting(setting_id="setting-privacy-only", seq=2,
              name="A hidden setting", section="privacy",
              value="", layer="user", meaning=""),
    ])


def test_shipped_book_loads_with_pinned_shape():
    book = load_settings_room()
    assert book.title == EXAMPLE_TITLE
    assert book.setting_ids() == (
        "setting-model-main", "setting-key-main",
        "setting-theme-main", "setting-autosave-main",
        "setting-telemetry-main", "setting-font-main")
    assert [v.view_id for v in book.views] == [
        "view-room", "view-ready"]
    assert [m.setting_id for m in book.notes] == [
        "setting-model-main",
        "setting-theme-main"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m195-boundary"
    assert panel.as_of == "2026-11-10"
    assert [row.item_id for row in panel.rows] == list(book.setting_ids())
    derived = derive_panel(book, "view-room")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 6
    assert panel.total_shown == derived.total_shown == 6
    assert {c.standing: c.items for c in panel.target_counts} == {
        "ready": 5, "unready": 1}
    assert derive_verdict(book, "view-room").verdict == "strained"
    assert derive_verdict(book, "view-room").passing_shown == 5
    assert derive_verdict(book, "view-ready").verdict == "open"
    assert derive_verdict(book, "view-ready").passing_shown == 5
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / SETTINGS_ROOM_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == SETTINGS_ROOM_SCHEMA
    assert raw["slice"] == "M-196"
    assert "verdict" not in raw
    assert "room_index" not in raw


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-196")]
    assert slice_.title == "Settings as one room"
    assert slice_.part == 8
    assert "every setting in one searchable screen" in slice_.summary
    assert "plain-language meaning" in slice_.summary
    assert "default/project/user/session" in slice_.summary
    assert SETTINGS_ROOM_SLICE == "M-196"


def test_charter_names_m196_on_two_rows():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert owners.count("M-196") == 2
    wizard = charter.screen("setup_wizard")
    assert wizard.verdict == "rebuild"
    assert "M-196" in wizard.owning_slices
    assert "M-184" in wizard.owning_slices
    assert "M-182" in wizard.owning_slices
    modal = charter.screen("github_config")
    assert modal.verdict == "keep"
    assert list(modal.owning_slices) == ["M-196"]
    assert "one room" in modal.direction
    assert "folds into" in modal.direction


def test_closed_vocabularies():
    assert READY_WORDS == ("ready", "unready")
    assert SECTIONS == ("model", "keys", "display", "behaviour", "privacy")
    assert LAYERS == ("default", "project", "user", "session")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "ready", "unready")
    assert VERDICT_WORDS == ("open", "strained", "shut")
    assert INDEX_ACTION == "index"
    assert EXAMPLE_MEANING == "the model that answers you"
    assert normalize_section("MODEL") == "model"
    assert normalize_layer("USER") == "user"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    with pytest.raises(ValueError):
        normalize_section("the void")
    with pytest.raises(ValueError):
        normalize_layer("the cloud")
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    assert "held as data alone" in ROOM_RULE
    assert "changes nothing" in ROOM_RULE
    assert "writes no config" in ROOM_RULE
    assert "M-196" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /settingsroom")


def test_shipped_book_judged_honestly_as_data():
    book = load_settings_room()
    model = book.setting_for("setting-model-main")
    assert setting_passes(model) is True
    assert setting_gaps(model) == ()
    assert plain_lines(model) == (
        "Setting: The model in use",
        "Section: model",
        "Value: the session model",
        "Layer: session",
        "Meaning: the model that answers you")
    key = book.setting_for("setting-key-main")
    assert key.value == ""
    assert "Value: unknown" in plain_lines(key)
    theme = book.setting_for("setting-theme-main")
    assert theme.layer == "project"
    assert "Layer: project" in plain_lines(theme)
    telemetry = book.setting_for("setting-telemetry-main")
    assert setting_gaps(telemetry) == ("no plain meaning",)
    assert setting_passes(telemetry) is False
    assert [g.setting_id for g in passing_settings(book)] == [
        "setting-model-main", "setting-key-main",
        "setting-theme-main", "setting-autosave-main",
        "setting-font-main"]
    assert total_settings(book) == 6
    index = derive_index(book)
    assert [e.meaning for e in index.entries] == [
        "the model that answers you", "the key that opens your provider",
        "the colours the screen wears", "whether your work is saved as you go",
        "how large the letters stand"]
    assert index.gaps == ("setting-telemetry-main",)
    assert setting_for_meaning(book, "the model that answers you").setting_id == (
        "setting-model-main")
    assert setting_for_meaning(book, "triple resume") is None
    assert first_note(book).note_id == "note-note-model"
    assert note_for_setting(
        book, "setting-model-main", "note").note_id == (
            "note-note-model")
    assert note_for_setting(book, "setting-nope") is None

# ---------------------------------------------------------------------
# The held setting: judged whole, its telling derived.
# ---------------------------------------------------------------------


def test_setting_record_round_trips():
    setting = _setting()
    assert validate_setting(setting) is setting
    rebuilt = build_setting(_stored_setting(setting))
    assert rebuilt == setting
    assert rebuilt.item_id == "setting-test"
    assert rebuilt.meaning == "the model that answers you"
    record = setting_record(setting)
    assert record["type"] == "room_setting"
    assert record["passes"] is True
    assert record["gaps"] == []


def test_setting_refuses_stored_judgements():
    for key in ("standing", "ready", "gaps", "segment", "verdict",
                "index", "entries", "coverage"):
        fields = _stored_setting(_setting())
        fields[key] = "stored"
        with pytest.raises(ValueError):
            build_setting(fields)
    fields = _stored_setting(_setting())
    fields["surprise"] = "stored"
    with pytest.raises(ValueError):
        build_setting(fields)


def test_setting_refuses_a_live_change_claim():
    for key in ("changes_setting", "changed_setting", "applies_setting",
                "applied_setting", "saves_setting", "saved_setting", "writes_config", "config_write"):
        fields = _stored_setting(_setting())
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_setting(fields)
        assert "held as data alone" in str(caught.value)
    for key in ("posts_note", "shown_setting"):
        fields = _note().to_record()
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_note(fields)
        assert "held as data alone" in str(caught.value)
    record = _note(setting_id="setting-test")
    assert validate_note(record) is record
    assert record.setting_id == "setting-test"
    assert note_record(record)["type"] == "room_note"


def test_setting_vocabularies_are_closed():
    assert _setting(section="MODEL").section == "model"
    assert _setting(layer="USER").layer == "user"
    assert _setting(value="").value == ""
    assert _setting(value=None).value == ""
    with pytest.raises(ValueError):
        _setting(section="a hunch")
    with pytest.raises(ValueError):
        _setting(layer="the cloud")
    with pytest.raises(ValueError):
        _setting(name="   ")
    with pytest.raises(ValueError):
        _setting(seq=0)
    with pytest.raises(ValueError):
        _setting(meaning=5)
    with pytest.raises(ValueError):
        _setting(value=5)
    with pytest.raises(ValueError):
        _setting(detail="   ")


def test_plain_telling_derives_from_the_settings_own_fields():
    setting = _setting(
        name="Test Setting", section="keys", value="", layer="user",
        meaning="", detail="The meaning waits on a held setting.")
    lines = plain_lines(setting)
    assert lines[0] == "Setting: Test Setting"
    assert lines[1] == "Section: keys"
    assert lines[2] == "Value: unknown"
    assert lines[3] == "Layer: user"
    assert lines[4] == "Meaning: none"
    assert plain_words(setting) == setting_plain_words(setting)
    assert "Test Setting" in plain_words(setting)
    assert "held setting" in plain_words(setting)


def test_incomplete_setting_stands_named_in_its_gaps():
    setting = _setting(meaning="")
    assert setting_gaps(setting) == ("no plain meaning",)
    assert setting_passes(setting) is False
    text = format_setting(setting)
    assert "stands unready" in text
    current_text = format_setting(_setting())
    assert "stands ready" in current_text


def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(_stored_view(view)) == view
    record = view_record(view)
    assert record["type"] == "room_view"
    assert record["view_filter"] == "all"
    assert "shows all settings" in view_plain_words(view)
    assert "filter all" in format_view(view)
    with pytest.raises(ValueError):
        _view(view_filter="some")
    stance = _note()
    assert build_note(stance.to_record()) == stance
    assert "Setting note note setting-test" in format_note(stance)
    assert "changes no setting" in format_note(stance)
    assert "toward the user" in note_plain_words(stance)
    with pytest.raises(ValueError):
        _note(stance="dance")


# ---------------------------------------------------------------------
# The index and the stance targets: derived at call time, never held.
# ---------------------------------------------------------------------


def test_index_is_derived_from_the_held_settings_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.setting_id for e in index.entries] == ["setting-test"]
    assert index.entries[0].meaning == "the model that answers you"
    assert index.gaps == ("setting-privacy-only",)
    assert index_record(index)["type"] == "room_index"
    assert index_record(book)["gaps"] == ["setting-privacy-only"]
    assert "1 plain meanings" in index_plain_words(book)
    text = format_index(book)
    assert "Settings index" in text
    assert "the model that answers you - A test setting (setting-test)" in text
    assert "setting-privacy-only" in text
    assert "changes no setting" in text


def test_target_reaches_its_setting_and_an_unheld_target_reaches_nothing():
    book = _mixed_book()
    assert setting_for_meaning(book, "the model that answers you").setting_id == "setting-test"
    assert setting_for_meaning(book, "triple resume") is None
    assert setting_for_meaning(book, "") is None
    assert "A test setting" in format_meaning(book, "the model that answers you")
    assert "reaches nothing in this book" in format_meaning(
        book, "triple resume")


def test_first_note_is_held_as_data():
    book = _book(notes=[_note(), _note(
        note_id="note-two", seq=2, setting_id="setting-other",
        stance="question", title="The second stance")])
    assert first_note(book).note_id == "note-test"
    assert note_for_setting(book, "setting-other").note_id == (
        "note-two")
    assert note_for_setting(
        book, "setting-other", "question").note_id == "note-two"
    assert note_for_setting(book, "setting-other", "praise") is None
    bare = _book()
    assert first_note(bare) is None
    assert note_for_setting(bare, "setting-other") is None
    text = format_note(first_note(book))
    assert "held as data alone" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    stance = _note(
        setting_id="setting-x", stance="concern",
        target="a branched session")
    assert stance.stance == "concern"
    rebuilt = build_note(stance.to_record())
    assert rebuilt == stance
    assert rebuilt.setting_id == "setting-x"
    assert rebuilt.target == "a branched session"
    with pytest.raises(ValueError):
        _note(setting_id="   ")
    with pytest.raises(ValueError):
        _note(target="   ")
    with pytest.raises(ValueError):
        _note(stance="teleport")


def test_panel_is_derived_and_a_stored_panel_must_agree():
    book = _mixed_book()
    panel = derive_panel(book)
    assert isinstance(panel, RoomPanel)
    assert panel.total_items == 2
    assert panel.total_shown == 2
    assert validate_panel(panel, book) is panel
    assert build_panel(panel.to_record(), book).rows == panel.rows
    assert build_row(panel.rows[0], book.settings[0]) == panel.rows[0]
    assert validate_row(panel.rows[0], book.settings[0]) == panel.rows[0]
    tampered = dict(panel.to_record())
    tampered["total_shown"] = 99
    with pytest.raises(ValueError):
        build_panel(tampered, book)
    renamed = dict(panel.to_record())
    renamed["panel_id"] = "panel-renamed"
    assert build_panel(renamed, book).panel_id == "panel-renamed"
    record = panel_record(panel, book)
    assert record["type"] == "room_panel"
    assert record["panel_id"] == panel.panel_id


def test_verdict_is_derived_from_the_shown_settings():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert isinstance(verdict, RoomVerdict)
    assert verdict.verdict == "strained"
    assert verdict.total_shown == 2
    assert verdict.passing_shown == 1
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    record = verdict_record(verdict, book)
    assert record["type"] == "room_verdict"
    assert "strained" in verdict_plain_words(book)
    assert "strained" in format_verdict(book)


def test_verdict_open_and_shut_edges():
    whole = _book(settings=[_setting()])
    assert derive_verdict(whole).verdict == "open"
    absent_book = _book(settings=[_setting(meaning="")])
    assert derive_verdict(absent_book).verdict == "shut"
    none_shown = _book(
        settings=[_setting(meaning="")],
        views=[_view(view_filter="ready")])
    verdict = derive_verdict(none_shown)
    assert verdict.total_shown == 0
    assert verdict.verdict == "shut"


def test_shown_and_section_readings():
    book = _mixed_book()
    assert [g.setting_id for g in shown_settings(book)] == [
        "setting-test", "setting-privacy-only"]
    ready_view = _view(
        view_id="view-r", seq=2, view_filter="ready")
    book2 = _book(
        settings=[_setting(), _setting(
            setting_id="setting-privacy-only", seq=2, name="A hidden setting",
            section="privacy", value="", layer="user", meaning="")],
        views=[_view(), ready_view])
    assert [g.setting_id for g in shown_settings(book2, ready_view)] == [
        "setting-test"]
    assert [g.setting_id for g in settings_for_section(book2, "privacy")] == [
        "setting-privacy-only"]
    assert [g.setting_id for g in passing_settings(book2)] == [
        "setting-test"]
    assert total_settings(book2) == 2
    with pytest.raises(ValueError):
        settings_for_section(book2, "the void")


def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(settings=[_setting(), _setting(seq=2)])
    with pytest.raises(ValueError):
        _book(settings=[_setting(), _setting(setting_id="setting-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(view_filter="ready")])
    with pytest.raises(ValueError) as caught:
        _book(notes=[_note(), _note(note_id="note-two", seq=2)])
    assert "one stance stands per setting target" in str(caught.value)
    fields = {
        "schema": SETTINGS_ROOM_SCHEMA, "slice": "M-196",
        "settings_room": {"title": "A test settings book"},
        "settings": [_stored_setting(_setting())],
        "views": [_stored_view(_view())], "notes": [],
        "panels": [], "verdict": "open",
    }
    with pytest.raises(ValueError):
        build_book(fields)
    del fields["verdict"]
    fields["room_index"] = "stored"
    with pytest.raises(ValueError):
        build_book(fields)
    raw = {
        "schema": SETTINGS_ROOM_SCHEMA, "slice": "M-196",
        "settings_room": {"title": "A test settings book"},
        "settings": [], "views": [], "notes": [], "panels": [],
        "changes_setting": True,
    }
    with pytest.raises(ValueError) as caught:
        build_book(raw)
    assert "held as data alone" in str(caught.value)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / SETTINGS_ROOM_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "settings_room.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_settings_room_file(path)
    assert book.title == EXAMPLE_TITLE
    assert total_settings(book) == 6


def test_registry_holds_settings_and_views_one_by_one():
    registry = SettingsRoomRegistry()
    assert registry.list_items() == ()
    held = registry.register_setting(_setting())
    assert held.setting_id == "setting-test"
    registry.register_view(_view())
    assert [i.item_id if hasattr(i, "item_id") else i.view_id
            for i in registry.list_items()] == ["setting-test", "view-test"]
    assert registry.get_setting("setting-test").name == "A test setting"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.book().title == "An unheld settings book"
    with pytest.raises(ValueError):
        registry.register_setting(_setting(seq=2))
    with pytest.raises(ValueError):
        registry.register_setting(_setting(setting_id="setting-two"))
    with pytest.raises(KeyError):
        registry.get_setting("setting-nope")


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = SettingsRoomRegistry()
    book = _mixed_book()
    held = registry.register_book(book)
    assert held.title == "A test settings book"
    assert len(registry.list_settings()) == 2
    other = _book(settings=[_setting(
        setting_id="setting-x", seq=9, name="Other", meaning="the model that answers you")],
        views=[_view(view_id="view-x", seq=9)])
    object.__setattr__(other, "title", "Another title")
    with pytest.raises(ValueError):
        registry.register_book(other)


def test_plain_words_and_formatters():
    book = _mixed_book()
    assert "section: 'model'" in format_book(book)
    assert "setting-privacy-only" in format_book(book, "privacy")
    assert "setting-test" not in format_book(book, "privacy")
    assert "Room panel under view view-test" in format_panel(book)
    assert panel_plain_words(book).startswith(
        "The settings book holds 2 settings")
    screen = format_room_screen(book)
    assert "Settings as One Room (M-196)" in screen
    assert PLAIN_EXPLANATION in screen
    assert "setting-privacy-sweep" not in screen
    assert "setting-privacy-only" in screen
    record = book_record(book)
    assert record["type"] == "room_book"
    assert record["title"] == "A test settings book"
    assert len(record["settings"]) == 2
    panel = derive_panel(book)
    assert panel_record(panel, book)["rows"][0]["item_id"] == "setting-test"
    assert verdict_record(derive_verdict(book), book)["verdict"] == (
        "strained")
    setting_text = format_setting(book.settings[0])
    assert "Setting: A test setting" in setting_text
    assert "Meaning: the model that answers you" in setting_text


def test_parse_args_inspect_and_loader_targets():
    assert parse_room_args("") == ("show", None)
    assert parse_room_args("show") == ("show", None)
    assert parse_room_args(None) == ("show", None)
    assert parse_room_args("setting setting-test") == (
        "setting", "setting-test")
    assert parse_room_args("meaning the model that answers you") == (
        "meaning", "the model that answers you")
    assert parse_room_args("section model") == (
        "section", "model")
    assert parse_room_args("view view-test") == ("view", "view-test")
    assert parse_room_args("note note-test") == (
        "note", "note-test")
    assert parse_room_args("index") == ("index", None)
    assert parse_room_args("panel") == ("panel", None)
    assert parse_room_args("verdict") == ("verdict", None)
    for bad in ("dance", "setting", "meaning", "section", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_room_args(bad)
    setting = _setting()
    assert inspect_setting_source(setting) == {
        "kind": "setting", "setting_id": "setting-test"}
    assert inspect_setting_source(_stored_setting(setting))["kind"] == (
        "setting")
    assert inspect_setting_source(_stored_view(_view()))["kind"] == (
        "view")
    assert inspect_setting_source(_note().to_record())["kind"] == (
        "note")
    assert inspect_setting_source(42)["kind"] == "unknown"
    book = load_settings_room({
        "schema": SETTINGS_ROOM_SCHEMA, "slice": "M-196",
        "settings_room": {"title": "A judged book"},
        "settings": [_stored_setting(_setting())],
        "views": [_stored_view(_view())], "notes": [], "panels": []})
    assert isinstance(book, RoomBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_settings_room({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_settings_room({"slice": "M-999"})
    built = build_setting(
        setting_id="setting-kw", seq=3, name="Kw Setting",
        section="model", value="the session model", layer="session",
        meaning="the model that answers you", detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="setting-test")
    assert built.setting_id == "setting-kw"
    assert setting_passes(built) is True


# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-196 agent layer: the agent holds a settings book
# for the session, settings and views are published
# as session news through the checkpoint target
# (journal first, deduped per shape), the panel
# and verdict are derived at call time from the
# whole book under a view, never held, the index
# is derived from the book's held settings, and the
# stance targets are held as data beside them -
# holding one changes no setting. This layer
# changes nothing, applies nothing, saves nothing,
# writes no config and persists nothing beyond the
# session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _room_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_room_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / SETTINGS_ROOM_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "settings_room.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestRoomAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.settings_room_status()
        assert status["settings"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["settings_room"]["title"] == EXAMPLE_TITLE
        assert len(status["settings_room"]["settings"]) == 6
        assert len(status["settings_room"]["views"]) == 2
        assert len(status["settings_room"]["notes"]) == 2
        assert status["panel"]["total_items"] == 6
        assert status["panel"]["total_shown"] == 6
        assert status["panels"][0]["panel_id"] == "panel-m195-boundary"
        assert status["verdict"]["verdict"] == "strained"
        assert status["verdict"]["passing_shown"] == 5
        assert [e["meaning"] for e in status["index"]["entries"]] == ["the model that answers you", "the key that opens your provider", "the colours the screen wears", "whether your work is saved as you go", "how large the letters stand"]
        assert status["index"]["gaps"] == ["setting-telemetry-main"]
        assert status["first_note"]["note_id"] == "note-note-model"
        assert "held as data alone" in status["rule"]
        assert "how large the letters stand" in status["plain_words"]
        assert "Settings as One Room (M-196)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._settings_room_registry()
        assert agent._settings_room_registry() is first
        assert agent._settings_room_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.settings_room_status()
        assert agent.get_room_setting(
            "setting-model-main").name == "The model in use"
        assert agent.get_room_view("view-room").view_filter == "all"
        assert agent.get_room_note(
            "note-note-model").note_id == "note-note-model"
        assert [a.setting_id for a in agent.room_settings_for_section(
            "display")] == ["setting-theme-main", "setting-font-main"]
        assert [a.setting_id for a in agent.room_settings_for_section(
            "model")] == ["setting-model-main"]
        assert [a.setting_id for a in agent.room_settings_passing()] == [
            "setting-model-main", "setting-key-main",
            "setting-theme-main", "setting-autosave-main",
            "setting-font-main"]
        agent.settings_room_panel()
        agent.settings_room_verdict()
        agent.room_index()
        agent.report_settings_room()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("room")
                or e["type"] == "room_setting"] == []
        with pytest.raises(KeyError):
            agent.get_room_setting("setting-nope")
        with pytest.raises(KeyError):
            agent.get_room_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_room_note("note-nope")
        with pytest.raises(ValueError):
            agent.room_settings_for_section("the void")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_room_setting(_setting())
        status = agent.settings_room_status()
        assert [a["setting_id"] for a in status["settings"]] == ["setting-test"]
        assert status["book"]["title"] == "An unheld settings book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["meaning"] for e in status["index"]["entries"]] == [
            "the model that answers you"]
        assert status["first_note"] is None
        assert "setting-test" in status["screen"]

    def test_held_setting_never_falls_back_to_the_example(
            self, agent):
        agent.register_room_setting(_setting())
        with pytest.raises(KeyError):
            agent.get_room_setting("setting-model-main")
        with pytest.raises(KeyError):
            agent.get_room_view("view-room")
        with pytest.raises(KeyError):
            agent.get_room_note("modal")
        setting = agent.get_room_setting("setting-test")
        assert setting.name == "A test setting"
        assert agent.settings_room_book().title == (
            "An unheld settings book")

    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_room_note("note-note-model")
        assert first.note_id == "note-note-model"
        assert first.setting_id == "setting-model-main"
        status = agent.settings_room_status()
        assert status["index"]["gaps"] == ["setting-telemetry-main"]
        assert status["first_note"]["setting_id"] == (
            "setting-model-main")
        assert status["first_note"]["stance"] == "note"


class TestRoomAgentHolding:
    def test_register_setting_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_room_setting(_setting())
        assert result["setting"]["setting_id"] == "setting-test"
        assert result["record_news"]["type"] == "room_setting"
        assert "setting-test" in result["screen"]
        events = _room_events(store, session_id, "room_setting")
        assert len(events) == 1
        agent.close()

    def test_duplicate_setting_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_room_setting(_setting())
        with pytest.raises(ValueError):
            agent.register_room_setting(_setting(seq=9))
        with pytest.raises(ValueError):
            agent.register_room_setting(_setting(setting_id="setting-two"))
        events = _room_events(store, session_id, "room_setting")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_room_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_room_events(
            store, session_id, "room_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_room_setting(_setting())
        result = agent.view_room("ready")
        assert result["view"]["view_filter"] == "ready"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "room_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "open"
        assert len(_room_events(
            store, session_id, "room_view")) == 1
        assert len(_room_events(
            store, session_id, "room_panel")) == 1
        assert len(_room_events(
            store, session_id, "room_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_room_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "room_setting", "room_view"]
        assert len(_room_events(
            store, session_id, "room_setting")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_room_book()
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "room_panel"
        assert result["index_record"]["gaps"] == [
            "setting-telemetry-main"]
        with pytest.raises(ValueError):
            agent.record_room_book()
        assert len(_room_events(
            store, session_id, "room_setting")) == 6
        assert len(_room_events(
            store, session_id, "room_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_room_book_file(tmp_path)
        book = load_settings_room_file(path)
        result = agent.record_room_book(book)
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_settings_room()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "strained"
        assert report["index"]["gaps"] == ["setting-telemetry-main"]
        assert "setting-model-main" in report["book_text"]
        assert "the model that answers you - The model in use (setting-model-main)" in report["index_text"]
        agent.register_room_setting(_setting())
        report = agent.report_settings_room()
        assert report["book"]["title"] == "An unheld settings book"
        assert report["panel"] is None
        assert report["verdict"] is None


class TestRoomTerminalHeading:
    def test_show_setting_meaning_section_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/settingsroom")
        assert "Settings as One Room (M-196)" in text
        _, _, text = _slash(agent, "/settingsroom setting setting-model-main")
        assert "Setting: The model in use" in text
        _, _, text = _slash(agent, "/settingsroom meaning the model that answers you")
        assert "the model that answers you" in text
        _, _, text = _slash(agent, "/settingsroom meaning triple resume")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/settingsroom section model")
        assert "setting-model-main" in text
        assert "setting-theme-main" not in text
        _, _, text = _slash(agent, "/settingsroom view view-room")
        assert "filter all" in text
        _, _, text = _slash(agent, "/settingsroom note note-note-model")
        assert "Setting note note setting-model-main" in text
        _, _, text = _slash(agent, "/settingsroom index")
        assert "Settings index" in text
        assert "setting-autosave-main" in text
        _, _, text = _slash(agent, "/settingsroom panel")
        assert "Room panel under view view-room" in text
        _, _, text = _slash(agent, "/settingsroom verdict")
        assert "strained" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/settingsroom [show|setting <setting-id>"
                "|meaning <meaning>|section <section>|view <view-id>"
                "|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/settingsroom dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/settingsroom setting setting-nope")
        assert "no setting named" in text


@pytest.fixture()
def room_handler(agent, monkeypatch):
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


def _room_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestRoomCommand:
    def test_show_is_default(self, room_handler, agent):
        room_handler._handle_settingsroom("")
        assert "Settings as One Room (M-196)" in (
            _room_published_text(room_handler))

    def test_setting_meaning_section_view_note_index_panel_verdict(
            self, room_handler, agent):
        room_handler._handle_settingsroom("setting setting-model-main")
        assert "Setting: The model in use" in _room_published_text(
            room_handler)
        room_handler._handle_settingsroom("meaning the model that answers you")
        assert "the model that answers you" in _room_published_text(
            room_handler)
        room_handler._handle_settingsroom("section model")
        assert "setting-model-main" in _room_published_text(room_handler)
        room_handler._handle_settingsroom("view view-room")
        assert "filter all" in _room_published_text(room_handler)
        room_handler._handle_settingsroom("note note-note-model")
        assert "Setting note note setting-model-main" in _room_published_text(room_handler)
        room_handler._handle_settingsroom("index")
        assert "Settings index" in _room_published_text(room_handler)
        room_handler._handle_settingsroom("panel")
        assert "Room panel under view" in _room_published_text(
            room_handler)
        room_handler._handle_settingsroom("verdict")
        assert "strained" in _room_published_text(room_handler)

    def test_bad_grammar_is_published(
            self, room_handler, agent):
        room_handler._handle_settingsroom("dance party")
        assert USAGE in _room_published_text(room_handler)
        room_handler._handle_settingsroom("setting setting-nope")
        assert "no setting named" in _room_published_text(room_handler)


class TestChatScreenRoutingRoom:
    def test_room_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/settingsroom panel", _FakeLog())
        assert calls == [("/settingsroom", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/settingsroom[/green] - show settings as one room (M-196)" in (
            text)
        assert ('"/settingsroom": "Usage: /settingsroom | '
                '/settingsroom setting <setting-id>') in text


class TestRoomDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.settings_room_panel()
        assert panel.total_shown == 6
        assert panel.panel_id == "panel-view-room"
        verdict = agent.settings_room_verdict()
        assert verdict.verdict == "strained"
        found = agent.settings_room_verdict("view-ready")
        assert found.verdict == "open"
        assert found.passing_shown == 5
        agent.register_room_setting(_setting())
        with pytest.raises(ValueError):
            agent.settings_room_panel()
        with pytest.raises(ValueError):
            agent.settings_room_verdict()

    def test_view_target_over_an_unshown_filter_is_shut(self, agent):
        agent.register_room_setting(_setting(meaning=""))
        result = agent.view_room("ready")
        assert result["verdict_record"]["verdict"] == "shut"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.room_index()
        assert [e["meaning"] for e in result["index"]["entries"]] == ["the model that answers you", "the key that opens your provider", "the colours the screen wears", "whether your work is saved as you go", "how large the letters stand"]
        assert result["index"]["gaps"] == ["setting-telemetry-main"]
        assert "the model that answers you - The model in use (setting-model-main)" in (
            result["index_text"])
        setting = agent.get_room_setting("setting-telemetry-main")
        assert setting_gaps(setting) == ("no plain meaning",)
        assert setting_passes(setting) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("room")
                or e["type"] == "room_setting"] == []
        agent.close()
