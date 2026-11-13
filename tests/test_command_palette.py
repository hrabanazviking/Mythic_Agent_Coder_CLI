"""M-197 Command Palette - pure-layer tests.

TIER: integration

The pure layer is the command palette, held as
data: one record per entry, held whole as a
card - under its title, its kind in the closed
vocabulary (command, action, navigation,
setting), its shortcut held honestly (unknown
stays empty, never invented), the search words
it carries, named as data, and its detail
- the notes held as data beside them, each naming
its entry, its stance and its target, and the
palette index derived at call time from the held
entries alone, never stored where it could drift.
An entry naming no search words stands
incomplete, named in its gaps; two entries
standing for one entry id refuse by name, and
one stance record stands per entry stance. A
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
and writes nothing: it holds the palette as
data and tells it.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.command_palette import (
    KINDS,
    EXAMPLE_KEYWORDS,
    STANCES,
    INDEX_ACTION,
    COMMAND_PALETTE_RESOURCE,
    COMMAND_PALETTE_SCHEMA,
    COMMAND_PALETTE_SLICE,
    PALETTE_RULE,
    PLAIN_EXPLANATION,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    READY_WORDS,
    EntryCard,
    NoteRecord,
    PaletteBook,
    PalettePanel,
    CommandPaletteRegistry,
    PaletteVerdict,
    PaletteView,
    book_record,
    build_book,
    build_entry,
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
    format_entry,
    format_index,
    format_note,
    format_palette_screen,
    format_panel,
    format_keywords,
    format_verdict,
    format_view,
    entry_for_keywords,
    entry_gaps,
    entry_passes,
    entry_plain_words,
    entry_record,
    entries_for_kind,
    index_plain_words,
    index_record,
    inspect_entry_source,
    note_for_entry,
    note_plain_words,
    note_record,
    load_command_palette,
    load_command_palette_file,
    normalize_kind,
    normalize_stance,
    normalize_view_filter,
    panel_plain_words,
    panel_record,
    parse_palette_args,
    passing_entries,
    plain_lines,
    plain_words,
    shown_entries,
    total_entries,
    validate_book,
    validate_entry,
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
EXAMPLE_TITLE = "Command palette at the M-196 slice boundary"


def _entry(**overrides):
    fields = {
        "entry_id": "entry-test",
        "seq": 1,
        "title": "A test entry",
        "kind": "command",
        "shortcut": "ctrl+k",
        "keywords": "the one door frequent hands use",
        "detail": "A test entry held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "palette-test",
    }
    fields.update(overrides)
    return build_entry(fields)


def _stored_entry(entry):
    return entry.to_record()


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "palette-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _stored_view(view):
    return view.to_record()


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "entry_id": "entry-test",
        "stance": "note",
        "target": "the user",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "palette-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _book(entries=None, views=None, notes=None, **overrides):
    fields = {
        "schema": COMMAND_PALETTE_SCHEMA,
        "slice": "M-197",
        "command_palette": {"title": "A test palette book"},
        "entries": [_stored_entry(item) for item in (
            entries if entries is not None else [_entry()])],
        "views": [_stored_view(item) for item in (
            views if views is not None else [_view()])],
        "notes": [item.to_record() for item in (notes or [])],
        "panels": [],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(entries=[
        _entry(),
        _entry(entry_id="entry-quiet-only", seq=2,
              title="A quiet entry", kind="action",
              shortcut="", keywords=""),
    ])


def test_shipped_book_loads_with_pinned_shape():
    book = load_command_palette()
    assert book.title == EXAMPLE_TITLE
    assert book.entry_ids() == (
        "entry-open-main", "entry-save-main",
        "entry-home-main", "entry-model-main",
        "entry-quiet-main", "entry-help-main")
    assert [v.view_id for v in book.views] == [
        "view-palette", "view-ready"]
    assert [m.entry_id for m in book.notes] == [
        "entry-open-main",
        "entry-help-main"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m196-boundary"
    assert panel.as_of == "2026-11-10"
    assert [row.item_id for row in panel.rows] == list(book.entry_ids())
    derived = derive_panel(book, "view-palette")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 6
    assert panel.total_shown == derived.total_shown == 6
    assert {c.standing: c.items for c in panel.target_counts} == {
        "ready": 5, "unready": 1}
    assert derive_verdict(book, "view-palette").verdict == "strained"
    assert derive_verdict(book, "view-palette").passing_shown == 5
    assert derive_verdict(book, "view-ready").verdict == "open"
    assert derive_verdict(book, "view-ready").passing_shown == 5
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / COMMAND_PALETTE_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == COMMAND_PALETTE_SCHEMA
    assert raw["slice"] == "M-197"
    assert "verdict" not in raw
    assert "palette_index" not in raw


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-197")]
    assert slice_.title == "Command palette"
    assert slice_.part == 8
    assert "Ctrl-K over everything" in slice_.summary
    assert "commands, actions, navigation, settings" in slice_.summary
    assert "the one door frequent hands" in slice_.summary
    assert COMMAND_PALETTE_SLICE == "M-197"


def test_charter_does_not_name_m197():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert owners.count("M-187") == 1
    assert owners.count("M-197") == 0


def test_closed_vocabularies():
    assert READY_WORDS == ("ready", "unready")
    assert KINDS == ("command", "action", "navigation", "setting")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "ready", "unready")
    assert VERDICT_WORDS == ("open", "strained", "shut")
    assert INDEX_ACTION == "index"
    assert EXAMPLE_KEYWORDS == "the one door frequent hands use"
    assert normalize_kind("COMMAND") == "command"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    with pytest.raises(ValueError):
        normalize_kind("the void")
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    assert "held as data alone" in PALETTE_RULE
    assert "executes nothing" in PALETTE_RULE
    assert "opens no network" in PALETTE_RULE
    assert "M-197" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /commandpalette")


def test_shipped_book_judged_honestly_as_data():
    book = load_command_palette()
    opener = book.entry_for("entry-open-main")
    assert entry_passes(opener) is True
    assert entry_gaps(opener) == ()
    assert plain_lines(opener) == (
        "Entry: Open the palette",
        "Kind: command",
        "Shortcut: ctrl+k",
        "Keywords: the one door frequent hands use")
    save = book.entry_for("entry-save-main")
    assert save.shortcut == ""
    assert "Shortcut: unknown" in plain_lines(save)
    model = book.entry_for("entry-model-main")
    assert model.kind == "setting"
    assert "Kind: setting" in plain_lines(model)
    quiet = book.entry_for("entry-quiet-main")
    assert entry_gaps(quiet) == ("no search words",)
    assert entry_passes(quiet) is False
    assert [g.entry_id for g in passing_entries(book)] == [
        "entry-open-main", "entry-save-main",
        "entry-home-main", "entry-model-main",
        "entry-help-main"]
    assert total_entries(book) == 6
    index = derive_index(book)
    assert [e.keywords for e in index.entries] == [
        "the one door frequent hands use", "keep the work safe",
        "return to the first screen", "the model that answers you",
        "help when you are stuck"]
    assert index.gaps == ("entry-quiet-main",)
    assert entry_for_keywords(book, "the one door frequent hands use").entry_id == (
        "entry-open-main")
    assert entry_for_keywords(book, "triple resume") is None
    assert first_note(book).note_id == "note-note-open"
    assert note_for_entry(
        book, "entry-open-main", "note").note_id == (
            "note-note-open")
    assert note_for_entry(book, "entry-nope") is None

# ---------------------------------------------------------------------
# The held entry: judged whole, its telling derived.
# ---------------------------------------------------------------------


def test_entry_record_round_trips():
    entry = _entry()
    assert validate_entry(entry) is entry
    rebuilt = build_entry(_stored_entry(entry))
    assert rebuilt == entry
    assert rebuilt.item_id == "entry-test"
    assert rebuilt.keywords == "the one door frequent hands use"
    record = entry_record(entry)
    assert record["type"] == "palette_entry"
    assert record["passes"] is True
    assert record["gaps"] == []


def test_entry_refuses_stored_judgements():
    for key in ("standing", "ready", "gaps", "segment", "verdict",
                "index", "entries", "coverage"):
        fields = _stored_entry(_entry())
        fields[key] = "stored"
        with pytest.raises(ValueError):
            build_entry(fields)
    fields = _stored_entry(_entry())
    fields["surprise"] = "stored"
    with pytest.raises(ValueError):
        build_entry(fields)


def test_entry_refuses_a_live_execution_claim():
    for key in ("executes_command", "executed_command", "runs_action",
                "ran_action", "navigates_now", "opens_palette", "invokes_command"):
        fields = _stored_entry(_entry())
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_entry(fields)
        assert "held as data alone" in str(caught.value)
    for key in ("posts_note", "shown_entry"):
        fields = _note().to_record()
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_note(fields)
        assert "held as data alone" in str(caught.value)
    record = _note(entry_id="entry-test")
    assert validate_note(record) is record
    assert record.entry_id == "entry-test"
    assert note_record(record)["type"] == "palette_note"


def test_entry_vocabularies_are_closed():
    assert _entry(kind="COMMAND").kind == "command"
    assert _entry(shortcut="").shortcut == ""
    assert _entry(shortcut=None).shortcut == ""
    with pytest.raises(ValueError):
        _entry(kind="a hunch")
    with pytest.raises(ValueError):
        _entry(title="   ")
    with pytest.raises(ValueError):
        _entry(seq=0)
    with pytest.raises(ValueError):
        _entry(keywords=5)
    with pytest.raises(ValueError):
        _entry(shortcut=5)
    with pytest.raises(ValueError):
        _entry(detail="   ")


def test_plain_telling_derives_from_the_entrys_own_fields():
    entry = _entry(
        title="Test Entry", kind="action", shortcut="", keywords="",
        detail="The words wait on a held entry.")
    lines = plain_lines(entry)
    assert lines[0] == "Entry: Test Entry"
    assert lines[1] == "Kind: action"
    assert lines[2] == "Shortcut: unknown"
    assert lines[3] == "Keywords: none"
    assert plain_words(entry) == entry_plain_words(entry)
    assert "Test Entry" in plain_words(entry)
    assert "held entry" in plain_words(entry)


def test_incomplete_entry_stands_named_in_its_gaps():
    entry = _entry(keywords="")
    assert entry_gaps(entry) == ("no search words",)
    assert entry_passes(entry) is False
    text = format_entry(entry)
    assert "stands unready" in text
    current_text = format_entry(_entry())
    assert "stands ready" in current_text


def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(_stored_view(view)) == view
    record = view_record(view)
    assert record["type"] == "palette_view"
    assert record["view_filter"] == "all"
    assert "shows all entries" in view_plain_words(view)
    assert "filter all" in format_view(view)
    with pytest.raises(ValueError):
        _view(view_filter="some")
    stance = _note()
    assert build_note(stance.to_record()) == stance
    assert "Palette note note entry-test" in format_note(stance)
    assert "executes no command" in format_note(stance)
    assert "toward the user" in note_plain_words(stance)
    with pytest.raises(ValueError):
        _note(stance="dance")

# ---------------------------------------------------------------------
# The index and the stance targets: derived at call time, never held.
# ---------------------------------------------------------------------


def test_index_is_derived_from_the_held_entries_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.entry_id for e in index.entries] == ["entry-test"]
    assert index.entries[0].keywords == "the one door frequent hands use"
    assert index.gaps == ("entry-quiet-only",)
    assert index_record(index)["type"] == "palette_index"
    assert index_record(book)["gaps"] == ["entry-quiet-only"]
    assert "1 search words" in index_plain_words(book)
    text = format_index(book)
    assert "Palette index" in text
    assert "the one door frequent hands use - A test entry (entry-test)" in text
    assert "entry-quiet-only" in text
    assert "executes no command" in text


def test_target_reaches_its_entry_and_an_unheld_target_reaches_nothing():
    book = _mixed_book()
    assert entry_for_keywords(book, "the one door frequent hands use").entry_id == "entry-test"
    assert entry_for_keywords(book, "triple resume") is None
    assert entry_for_keywords(book, "") is None
    assert "A test entry" in format_keywords(book, "the one door frequent hands use")
    assert "reaches nothing in this book" in format_keywords(
        book, "triple resume")


def test_first_note_is_held_as_data():
    book = _book(notes=[_note(), _note(
        note_id="note-two", seq=2, entry_id="entry-other",
        stance="question", title="The second stance")])
    assert first_note(book).note_id == "note-test"
    assert note_for_entry(book, "entry-other").note_id == (
        "note-two")
    assert note_for_entry(
        book, "entry-other", "question").note_id == "note-two"
    assert note_for_entry(book, "entry-other", "praise") is None
    bare = _book()
    assert first_note(bare) is None
    assert note_for_entry(bare, "entry-other") is None
    text = format_note(first_note(book))
    assert "held as data alone" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    stance = _note(
        entry_id="entry-x", stance="concern",
        target="a branched session")
    assert stance.stance == "concern"
    rebuilt = build_note(stance.to_record())
    assert rebuilt == stance
    assert rebuilt.entry_id == "entry-x"
    assert rebuilt.target == "a branched session"
    with pytest.raises(ValueError):
        _note(entry_id="   ")
    with pytest.raises(ValueError):
        _note(target="   ")
    with pytest.raises(ValueError):
        _note(stance="teleport")


def test_panel_is_derived_and_a_stored_panel_must_agree():
    book = _mixed_book()
    panel = derive_panel(book)
    assert isinstance(panel, PalettePanel)
    assert panel.total_items == 2
    assert panel.total_shown == 2
    assert validate_panel(panel, book) is panel
    assert build_panel(panel.to_record(), book).rows == panel.rows
    assert build_row(panel.rows[0], book.entries[0]) == panel.rows[0]
    assert validate_row(panel.rows[0], book.entries[0]) == panel.rows[0]
    tampered = dict(panel.to_record())
    tampered["total_shown"] = 99
    with pytest.raises(ValueError):
        build_panel(tampered, book)
    renamed = dict(panel.to_record())
    renamed["panel_id"] = "panel-renamed"
    assert build_panel(renamed, book).panel_id == "panel-renamed"
    record = panel_record(panel, book)
    assert record["type"] == "palette_panel"
    assert record["panel_id"] == panel.panel_id


def test_verdict_is_derived_from_the_shown_entries():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert isinstance(verdict, PaletteVerdict)
    assert verdict.verdict == "strained"
    assert verdict.total_shown == 2
    assert verdict.passing_shown == 1
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    record = verdict_record(verdict, book)
    assert record["type"] == "palette_verdict"
    assert "strained" in verdict_plain_words(book)
    assert "strained" in format_verdict(book)


def test_verdict_open_and_shut_edges():
    whole = _book(entries=[_entry()])
    assert derive_verdict(whole).verdict == "open"
    absent_book = _book(entries=[_entry(keywords="")])
    assert derive_verdict(absent_book).verdict == "shut"
    none_shown = _book(
        entries=[_entry(keywords="")],
        views=[_view(view_filter="ready")])
    verdict = derive_verdict(none_shown)
    assert verdict.total_shown == 0
    assert verdict.verdict == "shut"


def test_shown_and_kind_readings():
    book = _mixed_book()
    assert [g.entry_id for g in shown_entries(book)] == [
        "entry-test", "entry-quiet-only"]
    ready_view = _view(
        view_id="view-r", seq=2, view_filter="ready")
    book2 = _book(
        entries=[_entry(), _entry(
            entry_id="entry-quiet-only", seq=2, title="A quiet entry",
            kind="action", shortcut="", keywords="")],
        views=[_view(), ready_view])
    assert [g.entry_id for g in shown_entries(book2, ready_view)] == [
        "entry-test"]
    assert [g.entry_id for g in entries_for_kind(book2, "action")] == [
        "entry-quiet-only"]
    assert [g.entry_id for g in passing_entries(book2)] == [
        "entry-test"]
    assert total_entries(book2) == 2
    with pytest.raises(ValueError):
        entries_for_kind(book2, "the void")


def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(entries=[_entry(), _entry(seq=2)])
    with pytest.raises(ValueError):
        _book(entries=[_entry(), _entry(entry_id="entry-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(view_filter="ready")])
    with pytest.raises(ValueError) as caught:
        _book(notes=[_note(), _note(note_id="note-two", seq=2)])
    assert "one stance stands per entry target" in str(caught.value)
    fields = {
        "schema": COMMAND_PALETTE_SCHEMA, "slice": "M-197",
        "command_palette": {"title": "A test palette book"},
        "entries": [_stored_entry(_entry())],
        "views": [_stored_view(_view())], "notes": [],
        "panels": [], "verdict": "open",
    }
    with pytest.raises(ValueError):
        build_book(fields)
    del fields["verdict"]
    fields["palette_index"] = "stored"
    with pytest.raises(ValueError):
        build_book(fields)
    raw = {
        "schema": COMMAND_PALETTE_SCHEMA, "slice": "M-197",
        "command_palette": {"title": "A test palette book"},
        "entries": [], "views": [], "notes": [], "panels": [],
        "executes_command": True,
    }
    with pytest.raises(ValueError) as caught:
        build_book(raw)
    assert "held as data alone" in str(caught.value)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / COMMAND_PALETTE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "command_palette.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_command_palette_file(path)
    assert book.title == EXAMPLE_TITLE
    assert total_entries(book) == 6


def test_registry_holds_entries_and_views_one_by_one():
    registry = CommandPaletteRegistry()
    assert registry.list_items() == ()
    held = registry.register_entry(_entry())
    assert held.entry_id == "entry-test"
    registry.register_view(_view())
    assert [i.item_id if hasattr(i, "item_id") else i.view_id
            for i in registry.list_items()] == ["entry-test", "view-test"]
    assert registry.get_entry("entry-test").title == "A test entry"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.book().title == "An unheld palette book"
    with pytest.raises(ValueError):
        registry.register_entry(_entry(seq=2))
    with pytest.raises(ValueError):
        registry.register_entry(_entry(entry_id="entry-two"))
    with pytest.raises(KeyError):
        registry.get_entry("entry-nope")


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = CommandPaletteRegistry()
    book = _mixed_book()
    held = registry.register_book(book)
    assert held.title == "A test palette book"
    assert len(registry.list_entries()) == 2
    other = _book(entries=[_entry(
        entry_id="entry-x", seq=9, title="Other", keywords="the one door frequent hands use")],
        views=[_view(view_id="view-x", seq=9)])
    object.__setattr__(other, "title", "Another title")
    with pytest.raises(ValueError):
        registry.register_book(other)


def test_plain_words_and_formatters():
    book = _mixed_book()
    assert "kind: 'command'" in format_book(book)
    assert "entry-quiet-only" in format_book(book, "action")
    assert "entry-test" not in format_book(book, "action")
    assert "Palette panel under view view-test" in format_panel(book)
    assert panel_plain_words(book).startswith(
        "The command palette book holds 2 entries")
    screen = format_palette_screen(book)
    assert "Command Palette (M-197)" in screen
    assert PLAIN_EXPLANATION in screen
    assert "entry-quiet-sweep" not in screen
    assert "entry-quiet-only" in screen
    record = book_record(book)
    assert record["type"] == "palette_book"
    assert record["title"] == "A test palette book"
    assert len(record["entries"]) == 2
    panel = derive_panel(book)
    assert panel_record(panel, book)["rows"][0]["item_id"] == "entry-test"
    assert verdict_record(derive_verdict(book), book)["verdict"] == (
        "strained")
    entry_text = format_entry(book.entries[0])
    assert "Entry: A test entry" in entry_text
    assert "Keywords: the one door frequent hands use" in entry_text


def test_parse_args_inspect_and_loader_targets():
    assert parse_palette_args("") == ("show", None)
    assert parse_palette_args("show") == ("show", None)
    assert parse_palette_args(None) == ("show", None)
    assert parse_palette_args("entry entry-test") == (
        "entry", "entry-test")
    assert parse_palette_args("keywords the one door frequent hands use") == (
        "keywords", "the one door frequent hands use")
    assert parse_palette_args("kind command") == (
        "kind", "command")
    assert parse_palette_args("view view-test") == ("view", "view-test")
    assert parse_palette_args("note note-test") == (
        "note", "note-test")
    assert parse_palette_args("index") == ("index", None)
    assert parse_palette_args("panel") == ("panel", None)
    assert parse_palette_args("verdict") == ("verdict", None)
    for bad in ("dance", "entry", "keywords", "kind", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_palette_args(bad)
    entry = _entry()
    assert inspect_entry_source(entry) == {
        "kind": "entry", "entry_id": "entry-test"}
    assert inspect_entry_source(_stored_entry(entry))["kind"] == (
        "entry")
    assert inspect_entry_source(_stored_view(_view()))["kind"] == (
        "view")
    assert inspect_entry_source(_note().to_record())["kind"] == (
        "note")
    assert inspect_entry_source(42)["kind"] == "unknown"
    book = load_command_palette({
        "schema": COMMAND_PALETTE_SCHEMA, "slice": "M-197",
        "command_palette": {"title": "A judged book"},
        "entries": [_stored_entry(_entry())],
        "views": [_stored_view(_view())], "notes": [], "panels": []})
    assert isinstance(book, PaletteBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_command_palette({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_command_palette({"slice": "M-999"})
    built = build_entry(
        entry_id="entry-kw", seq=3, title="Kw Entry",
        kind="command", shortcut="ctrl+k",
        keywords="the one door frequent hands use", detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="palette-test")
    assert built.entry_id == "entry-kw"
    assert entry_passes(built) is True


# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-197 agent layer: the agent holds a palette book
# for the session, entries and views are published
# as session news through the checkpoint target
# (journal first, deduped per shape), the panel
# and verdict are derived at call time from the
# whole book under a view, never held, the index
# is derived from the book's held entries, and the
# stance targets are held as data beside them -
# holding one executes no command. This layer
# executes nothing, runs no action, navigates
# nowhere, opens no network and persists nothing
# beyond the session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _palette_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_palette_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / COMMAND_PALETTE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "command_palette.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestPaletteAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.command_palette_status()
        assert status["entries"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["command_palette"]["title"] == EXAMPLE_TITLE
        assert len(status["command_palette"]["entries"]) == 6
        assert len(status["command_palette"]["views"]) == 2
        assert len(status["command_palette"]["notes"]) == 2
        assert status["panel"]["total_items"] == 6
        assert status["panel"]["total_shown"] == 6
        assert status["panels"][0]["panel_id"] == "panel-m196-boundary"
        assert status["verdict"]["verdict"] == "strained"
        assert status["verdict"]["passing_shown"] == 5
        assert [e["keywords"] for e in status["index"]["entries"]] == ["the one door frequent hands use", "keep the work safe", "return to the first screen", "the model that answers you", "help when you are stuck"]
        assert status["index"]["gaps"] == ["entry-quiet-main"]
        assert status["first_note"]["note_id"] == "note-note-open"
        assert "held as data alone" in status["rule"]
        assert "help when you are stuck" in status["plain_words"]
        assert "Command Palette (M-197)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._command_palette_registry()
        assert agent._command_palette_registry() is first
        assert agent._command_palette_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.command_palette_status()
        assert agent.get_palette_entry(
            "entry-open-main").title == "Open the palette"
        assert agent.get_palette_view("view-palette").view_filter == "all"
        assert agent.get_palette_note(
            "note-note-open").note_id == "note-note-open"
        assert [a.entry_id for a in agent.palette_entries_for_kind(
            "command")] == ["entry-open-main", "entry-help-main"]
        assert [a.entry_id for a in agent.palette_entries_for_kind(
            "setting")] == ["entry-model-main"]
        assert [a.entry_id for a in agent.palette_entries_passing()] == [
            "entry-open-main", "entry-save-main",
            "entry-home-main", "entry-model-main",
            "entry-help-main"]
        agent.command_palette_panel()
        agent.command_palette_verdict()
        agent.palette_index()
        agent.report_command_palette()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("palette")] == []
        with pytest.raises(KeyError):
            agent.get_palette_entry("entry-nope")
        with pytest.raises(KeyError):
            agent.get_palette_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_palette_note("note-nope")
        with pytest.raises(ValueError):
            agent.palette_entries_for_kind("the void")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_palette_entry(_entry())
        status = agent.command_palette_status()
        assert [a["entry_id"] for a in status["entries"]] == ["entry-test"]
        assert status["book"]["title"] == "An unheld palette book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["keywords"] for e in status["index"]["entries"]] == [
            "the one door frequent hands use"]
        assert status["first_note"] is None
        assert "entry-test" in status["screen"]

    def test_held_entry_never_falls_back_to_the_example(
            self, agent):
        agent.register_palette_entry(_entry())
        with pytest.raises(KeyError):
            agent.get_palette_entry("entry-open-main")
        with pytest.raises(KeyError):
            agent.get_palette_view("view-palette")
        with pytest.raises(KeyError):
            agent.get_palette_note("modal")
        entry = agent.get_palette_entry("entry-test")
        assert entry.title == "A test entry"
        assert agent.command_palette_book().title == (
            "An unheld palette book")

    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_palette_note("note-note-open")
        assert first.note_id == "note-note-open"
        assert first.entry_id == "entry-open-main"
        status = agent.command_palette_status()
        assert status["index"]["gaps"] == ["entry-quiet-main"]
        assert status["first_note"]["entry_id"] == (
            "entry-open-main")
        assert status["first_note"]["stance"] == "note"


class TestPaletteAgentHolding:
    def test_register_entry_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_palette_entry(_entry())
        assert result["entry"]["entry_id"] == "entry-test"
        assert result["record_news"]["type"] == "palette_entry"
        assert "entry-test" in result["screen"]
        events = _palette_events(store, session_id, "palette_entry")
        assert len(events) == 1
        agent.close()

    def test_duplicate_entry_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_palette_entry(_entry())
        with pytest.raises(ValueError):
            agent.register_palette_entry(_entry(seq=9))
        with pytest.raises(ValueError):
            agent.register_palette_entry(_entry(entry_id="entry-two"))
        events = _palette_events(store, session_id, "palette_entry")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_palette_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_palette_events(
            store, session_id, "palette_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_palette_entry(_entry())
        result = agent.view_palette("ready")
        assert result["view"]["view_filter"] == "ready"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "palette_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "open"
        assert len(_palette_events(
            store, session_id, "palette_view")) == 1
        assert len(_palette_events(
            store, session_id, "palette_panel")) == 1
        assert len(_palette_events(
            store, session_id, "palette_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_palette_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "palette_entry", "palette_view"]
        assert len(_palette_events(
            store, session_id, "palette_entry")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_palette_book()
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "palette_panel"
        assert result["index_record"]["gaps"] == [
            "entry-quiet-main"]
        with pytest.raises(ValueError):
            agent.record_palette_book()
        assert len(_palette_events(
            store, session_id, "palette_entry")) == 6
        assert len(_palette_events(
            store, session_id, "palette_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_palette_book_file(tmp_path)
        book = load_command_palette_file(path)
        result = agent.record_palette_book(book)
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_command_palette()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "strained"
        assert report["index"]["gaps"] == ["entry-quiet-main"]
        assert "entry-open-main" in report["book_text"]
        assert "the one door frequent hands use - Open the palette (entry-open-main)" in report["index_text"]
        agent.register_palette_entry(_entry())
        report = agent.report_command_palette()
        assert report["book"]["title"] == "An unheld palette book"
        assert report["panel"] is None
        assert report["verdict"] is None


class TestPaletteTerminalHeading:
    def test_show_entry_keywords_kind_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/commandpalette")
        assert "Command Palette (M-197)" in text
        _, _, text = _slash(agent, "/commandpalette entry entry-open-main")
        assert "Entry: Open the palette" in text
        _, _, text = _slash(agent, "/commandpalette keywords the one door frequent hands use")
        assert "the one door frequent hands use" in text
        _, _, text = _slash(agent, "/commandpalette keywords triple resume")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/commandpalette kind command")
        assert "entry-open-main" in text
        assert "entry-model-main" not in text
        _, _, text = _slash(agent, "/commandpalette view view-palette")
        assert "filter all" in text
        _, _, text = _slash(agent, "/commandpalette note note-note-open")
        assert "Palette note note entry-open-main" in text
        _, _, text = _slash(agent, "/commandpalette index")
        assert "Palette index" in text
        assert "entry-model-main" in text
        _, _, text = _slash(agent, "/commandpalette panel")
        assert "Palette panel under view view-palette" in text
        _, _, text = _slash(agent, "/commandpalette verdict")
        assert "strained" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/commandpalette [show|entry <entry-id>"
                "|keywords <keywords>|kind <kind>|view <view-id>"
                "|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/commandpalette dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/commandpalette entry entry-nope")
        assert "no entry named" in text


@pytest.fixture()
def palette_handler(agent, monkeypatch):
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


def _palette_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestPaletteCommand:
    def test_show_is_default(self, palette_handler, agent):
        palette_handler._handle_commandpalette("")
        assert "Command Palette (M-197)" in (
            _palette_published_text(palette_handler))

    def test_entry_keywords_kind_view_note_index_panel_verdict(
            self, palette_handler, agent):
        palette_handler._handle_commandpalette("entry entry-open-main")
        assert "Entry: Open the palette" in _palette_published_text(
            palette_handler)
        palette_handler._handle_commandpalette("keywords the one door frequent hands use")
        assert "the one door frequent hands use" in _palette_published_text(
            palette_handler)
        palette_handler._handle_commandpalette("kind command")
        assert "entry-open-main" in _palette_published_text(palette_handler)
        palette_handler._handle_commandpalette("view view-palette")
        assert "filter all" in _palette_published_text(palette_handler)
        palette_handler._handle_commandpalette("note note-note-open")
        assert "Palette note note entry-open-main" in _palette_published_text(palette_handler)
        palette_handler._handle_commandpalette("index")
        assert "Palette index" in _palette_published_text(palette_handler)
        palette_handler._handle_commandpalette("panel")
        assert "Palette panel under view" in _palette_published_text(
            palette_handler)
        palette_handler._handle_commandpalette("verdict")
        assert "strained" in _palette_published_text(palette_handler)

    def test_bad_grammar_is_published(
            self, palette_handler, agent):
        palette_handler._handle_commandpalette("dance party")
        assert USAGE in _palette_published_text(palette_handler)
        palette_handler._handle_commandpalette("entry entry-nope")
        assert "no entry named" in _palette_published_text(palette_handler)


class TestChatScreenRoutingPalette:
    def test_palette_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/commandpalette panel", _FakeLog())
        assert calls == [("/commandpalette", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/commandpalette[/green] - show command palette (M-197)" in (
            text)
        assert ('"/commandpalette": "Usage: /commandpalette | '
                '/commandpalette entry <entry-id>') in text


class TestPaletteDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.command_palette_panel()
        assert panel.total_shown == 6
        assert panel.panel_id == "panel-view-palette"
        verdict = agent.command_palette_verdict()
        assert verdict.verdict == "strained"
        found = agent.command_palette_verdict("view-ready")
        assert found.verdict == "open"
        assert found.passing_shown == 5
        agent.register_palette_entry(_entry())
        with pytest.raises(ValueError):
            agent.command_palette_panel()
        with pytest.raises(ValueError):
            agent.command_palette_verdict()

    def test_view_target_over_an_unshown_filter_is_shut(self, agent):
        agent.register_palette_entry(_entry(keywords=""))
        result = agent.view_palette("ready")
        assert result["verdict_record"]["verdict"] == "shut"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.palette_index()
        assert [e["keywords"] for e in result["index"]["entries"]] == ["the one door frequent hands use", "keep the work safe", "return to the first screen", "the model that answers you", "help when you are stuck"]
        assert result["index"]["gaps"] == ["entry-quiet-main"]
        assert "the one door frequent hands use - Open the palette (entry-open-main)" in (
            result["index_text"])
        entry = agent.get_palette_entry("entry-quiet-main")
        assert entry_gaps(entry) == ("no search words",)
        assert entry_passes(entry) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("palette")] == []
        agent.close()
