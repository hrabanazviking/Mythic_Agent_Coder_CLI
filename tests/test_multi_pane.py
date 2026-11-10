"""M-192 Multi-Pane Working - pure-layer tests.

TIER: integration

The pure layer is the working screen, held as
data: one record per pane, held whole as a
card - under its title, its kind in the closed
vocabulary (chat, board, files, terminal, work,
crew), its width and its height held honestly
(unknown stays empty, never invented), the
target it opens on, named as data, and its
detail - the notes held as data beside them,
each naming its pane, its stance and its
target, and the pane index derived at call
time from the held panes alone, never stored
where it could drift. A pane naming no target
stands unanchored, named in its gaps; two
panes standing for one pane id refuse by name,
and one stance record stands per pane stance.
A record claiming a pane actually opened,
focused or resized refuses by name, and a
stored index or verdict refuses by name. The
panel is derived for one held layout and the
verdict is derived for the whole book under
one layout. The shipped example book is held
in a data file, and a loader reads a book from
any file. This layer opens no pane, focuses
nothing, resizes nothing and opens no network:
it holds the working screen as data and tells
it.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.multi_pane import (
    KINDS,
    EXAMPLE_TARGET,
    STANCES,
    INDEX_ACTION,
    MULTI_PANE_RESOURCE,
    MULTI_PANE_SCHEMA,
    MULTI_PANE_SLICE,
    PANE_RULE,
    PLAIN_EXPLANATION,
    USAGE,
    VERDICT_WORDS,
    LAYOUT_FILTERS,
    ANCHOR_WORDS,
    PaneCard,
    NoteRecord,
    PaneBook,
    PanePanel,
    MultiPaneRegistry,
    PaneVerdict,
    PaneLayout,
    book_record,
    build_book,
    build_pane,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_layout,
    derive_index,
    derive_panel,
    derive_verdict,
    first_note,
    format_book,
    format_pane,
    format_index,
    format_note,
    format_pane_screen,
    format_panel,
    format_target,
    format_verdict,
    format_layout,
    pane_for_target,
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
    load_multi_pane,
    load_multi_pane_file,
    normalize_kind,
    normalize_stance,
    normalize_layout_filter,
    panel_plain_words,
    panel_record,
    parse_pane_args,
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
    validate_layout,
    verdict_plain_words,
    verdict_record,
    layout_plain_words,
    layout_record,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.tui_redesign_charter import load_charter

ROOT = Path(__file__).resolve().parents[1]
ON = "2026-11-09"
BY = "the coordinator"
EXAMPLE_TITLE = "Multi-pane working at the M-191 slice boundary"


def _pane(**overrides):
    fields = {
        "pane_id": "pane-test",
        "seq": 1,
        "title": "A test pane",
        "kind": "work",
        "width": "3 lines",
        "height": "2 lines",
        "target": "mythic_agent/core/session.py:128",
        "detail": "A test pane held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "pane-test",
    }
    fields.update(overrides)
    return build_pane(fields)


def _stored_pane(pane):
    return pane.to_record()


def _layout(**overrides):
    fields = {
        "layout_id": "layout-test",
        "seq": 1,
        "layout_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "pane-test",
    }
    fields.update(overrides)
    return build_layout(fields)


def _stored_layout(layout):
    return layout.to_record()


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
        "origin_session": "pane-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _book(panes=None, layouts=None, notes=None, **overrides):
    fields = {
        "schema": MULTI_PANE_SCHEMA,
        "slice": "M-192",
        "multi_pane": {"title": "A test pane book"},
        "panes": [_stored_pane(item) for item in (
            panes if panes is not None else [_pane()])],
        "layouts": [_stored_layout(item) for item in (
            layouts if layouts is not None else [_layout()])],
        "notes": [item.to_record() for item in (notes or [])],
        "panels": [],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(panes=[
        _pane(),
        _pane(pane_id="pane-board-only", seq=2,
              title="A board pane", kind="board",
              width="", height="", target=""),
    ])


def test_shipped_book_loads_with_pinned_shape():
    book = load_multi_pane()
    assert book.title == EXAMPLE_TITLE
    assert book.pane_ids() == (
        "pane-work-session", "pane-files-costs",
        "pane-board-gate", "pane-chat-guide",
        "pane-terminal-sweep", "pane-crew-roadmap")
    assert [v.layout_id for v in book.layouts] == [
        "layout-field", "layout-anchored"]
    assert [m.pane_id for m in book.notes] == [
        "pane-work-session",
        "pane-chat-guide"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m191-boundary"
    assert panel.as_of == "2026-11-10"
    assert [row.item_id for row in panel.rows] == list(book.pane_ids())
    derived = derive_panel(book, "layout-field")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 6
    assert panel.total_shown == derived.total_shown == 6
    assert {c.standing: c.items for c in panel.target_counts} == {
        "anchored": 5, "unanchored": 1}
    assert derive_verdict(book, "layout-field").verdict == "strained"
    assert derive_verdict(book, "layout-field").passing_shown == 5
    assert derive_verdict(book, "layout-anchored").verdict == "open"
    assert derive_verdict(book, "layout-anchored").passing_shown == 5
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / MULTI_PANE_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == MULTI_PANE_SCHEMA
    assert raw["slice"] == "M-192"
    assert "verdict" not in raw
    assert "pane_index" not in raw


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-192")]
    assert slice_.title == "Multi-pane working"
    assert slice_.part == 8
    assert "chat, board, files, and terminal panes" in slice_.summary
    assert "Mythic layout" in slice_.summary
    assert "board left, work centre, crew right" in slice_.summary
    assert MULTI_PANE_SLICE == "M-192"


def test_charter_does_not_name_m192():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert owners.count("M-187") == 1
    assert "M-192" not in owners


def test_closed_vocabularies():
    assert ANCHOR_WORDS == ("anchored", "unanchored")
    assert KINDS == ("chat", "board", "files", "terminal", "work", "crew")
    assert STANCES == ("note", "concern", "praise", "question")
    assert LAYOUT_FILTERS == ("all", "anchored", "unanchored")
    assert VERDICT_WORDS == ("open", "strained", "shut")
    assert INDEX_ACTION == "index"
    assert EXAMPLE_TARGET == "mythic_agent/core/session.py:128"
    assert normalize_kind("WORK") == "work"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_layout_filter("ALL") == "all"
    with pytest.raises(ValueError):
        normalize_kind("the void")
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_layout_filter("some")
    assert "held as data alone" in PANE_RULE
    assert "opens no pane" in PANE_RULE
    assert "M-192" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /panes")


def test_shipped_book_judged_honestly_as_data():
    book = load_multi_pane()
    login = book.pane_for("pane-work-session")
    assert pane_passes(login) is True
    assert pane_gaps(login) == ()
    assert plain_lines(login) == (
        "Pane: Work",
        "Kind: work",
        "Width: 2 shares",
        "Height: full height",
        "Target: mythic_agent/core/session.py:128")
    addeds = book.pane_for("pane-files-costs")
    assert addeds.width == ""
    assert "Width: unknown" in plain_lines(addeds)
    flaky = book.pane_for("pane-board-gate")
    assert flaky.height == ""
    assert "Height: unknown" in plain_lines(flaky)
    sweep = book.pane_for("pane-terminal-sweep")
    assert pane_gaps(sweep) == ("no pane target",)
    assert pane_passes(sweep) is False
    assert [g.pane_id for g in passing_panes(book)] == [
        "pane-work-session", "pane-files-costs",
        "pane-board-gate", "pane-chat-guide",
        "pane-crew-roadmap"]
    assert total_panes(book) == 6
    index = derive_index(book)
    assert [e.target for e in index.entries] == [
        "mythic_agent/core/session.py:128", "mythic_agent/core/costs_face.py:12", "tests/test_part7_gate.py:41",
            "docs/gallery_guide.md:1", "mythic_agent/data/roadmap_slices.yaml:1186"]
    assert index.gaps == ("pane-terminal-sweep",)
    assert pane_for_target(book, "mythic_agent/core/session.py:128").pane_id == (
        "pane-work-session")
    assert pane_for_target(book, "triple resume") is None
    assert first_note(book).note_id == "note-note-work"
    assert note_for_pane(
        book, "pane-work-session", "note").note_id == (
            "note-note-work")
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
    assert rebuilt.target == "mythic_agent/core/session.py:128"
    record = pane_record(pane)
    assert record["type"] == "diff_pane"
    assert record["passes"] is True
    assert record["gaps"] == []


def test_pane_refuses_stored_judgements():
    for key in ("standing", "anchored", "gaps", "segment", "verdict",
                "index", "entries", "coverage"):
        fields = _stored_pane(_pane())
        fields[key] = "stored"
        with pytest.raises(ValueError):
            build_pane(fields)
    fields = _stored_pane(_pane())
    fields["surprise"] = "stored"
    with pytest.raises(ValueError):
        build_pane(fields)


def test_pane_refuses_a_live_session_claim():
    for key in ("opens_pane", "opened_pane", "focuses_pane",
                "posted_note", "opens_pane"):
        fields = _stored_pane(_pane())
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_pane(fields)
        assert "held as data alone" in str(caught.value)
    for key in ("posts_note", "opened_pane"):
        fields = _note().to_record()
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_note(fields)
        assert "held as data alone" in str(caught.value)
    record = _note(pane_id="pane-test")
    assert validate_note(record) is record
    assert record.pane_id == "pane-test"
    assert note_record(record)["type"] == "pane_note"


def test_pane_vocabularies_are_closed():
    assert _pane(kind="WORK").kind == "work"
    assert _pane(width="").width == ""
    assert _pane(height=None).height == ""
    with pytest.raises(ValueError):
        _pane(kind="a hunch")
    with pytest.raises(ValueError):
        _pane(title="   ")
    with pytest.raises(ValueError):
        _pane(seq=0)
    with pytest.raises(ValueError):
        _pane(target=5)
    with pytest.raises(ValueError):
        _pane(width=5)
    with pytest.raises(ValueError):
        _pane(height=5)
    with pytest.raises(ValueError):
        _pane(detail="   ")


def test_plain_telling_derives_from_the_panes_own_fields():
    pane = _pane(
        title="Test Session", kind="board", width="", height="",
        target="", detail="The target waits on a held pane.")
    lines = plain_lines(pane)
    assert lines[0] == "Pane: Test Session"
    assert lines[1] == "Kind: board"
    assert lines[2] == "Width: unknown"
    assert lines[3] == "Height: unknown"
    assert lines[4] == "Target: none"
    assert plain_words(pane) == pane_plain_words(pane)
    assert "Test Session" in plain_words(pane)
    assert "held pane" in plain_words(pane)


def test_unanchored_pane_stands_named_in_its_gaps():
    pane = _pane(target="")
    assert pane_gaps(pane) == ("no pane target",)
    assert pane_passes(pane) is False
    text = format_pane(pane)
    assert "stands unanchored" in text
    current_text = format_pane(_pane())
    assert "stands anchored" in current_text


def test_layout_and_note_round_trip():
    layout = _layout()
    assert validate_layout(layout) is layout
    assert build_layout(_stored_layout(layout)) == layout
    record = layout_record(layout)
    assert record["type"] == "pane_layout"
    assert record["layout_filter"] == "all"
    assert "shows all panes" in layout_plain_words(layout)
    assert "filter all" in format_layout(layout)
    with pytest.raises(ValueError):
        _layout(layout_filter="some")
    stance = _note()
    assert build_note(stance.to_record()) == stance
    assert "Pane note note pane-test" in format_note(stance)
    assert "opens no pane" in format_note(stance)
    assert "toward the user" in note_plain_words(stance)
    with pytest.raises(ValueError):
        _note(stance="dance")


# ---------------------------------------------------------------------
# The index and the stance targets: derived at call time, never held.
# ---------------------------------------------------------------------


def test_index_is_derived_from_the_held_panes_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.pane_id for e in index.entries] == ["pane-test"]
    assert index.entries[0].target == "mythic_agent/core/session.py:128"
    assert index.gaps == ("pane-board-only",)
    assert index_record(index)["type"] == "pane_index"
    assert index_record(book)["gaps"] == ["pane-board-only"]
    assert "1 targets" in index_plain_words(book)
    text = format_index(book)
    assert "Pane index" in text
    assert "mythic_agent/core/session.py:128 - A test pane (pane-test)" in text
    assert "pane-board-only" in text
    assert "opens no pane" in text


def test_target_reaches_its_pane_and_an_unheld_target_reaches_nothing():
    book = _mixed_book()
    assert pane_for_target(book, "mythic_agent/core/session.py:128").pane_id == "pane-test"
    assert pane_for_target(book, "triple resume") is None
    assert pane_for_target(book, "") is None
    assert "A test pane" in format_target(book, "mythic_agent/core/session.py:128")
    assert "reaches nothing in this book" in format_target(
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
    assert isinstance(panel, PanePanel)
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
    assert record["type"] == "pane_panel"
    assert record["panel_id"] == panel.panel_id


def test_verdict_is_derived_from_the_shown_panes():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert isinstance(verdict, PaneVerdict)
    assert verdict.verdict == "strained"
    assert verdict.total_shown == 2
    assert verdict.passing_shown == 1
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    record = verdict_record(verdict, book)
    assert record["type"] == "pane_verdict"
    assert "strained" in verdict_plain_words(book)
    assert "strained" in format_verdict(book)


def test_verdict_open_and_shut_edges():
    whole = _book(panes=[_pane()])
    assert derive_verdict(whole).verdict == "open"
    absent_book = _book(panes=[_pane(target="")])
    assert derive_verdict(absent_book).verdict == "shut"
    none_shown = _book(
        panes=[_pane(target="")],
        layouts=[_layout(layout_filter="anchored")])
    verdict = derive_verdict(none_shown)
    assert verdict.total_shown == 0
    assert verdict.verdict == "shut"


def test_shown_and_kind_readings():
    book = _mixed_book()
    assert [g.pane_id for g in shown_panes(book)] == [
        "pane-test", "pane-board-only"]
    anchored_layout = _layout(
        layout_id="layout-r", seq=2, layout_filter="anchored")
    book2 = _book(
        panes=[_pane(), _pane(
            pane_id="pane-board-only", seq=2, title="A board pane",
            kind="board", width="", height="", target="")],
        layouts=[_layout(), anchored_layout])
    assert [g.pane_id for g in shown_panes(book2, anchored_layout)] == [
        "pane-test"]
    assert [g.pane_id for g in panes_for_kind(book2, "board")] == [
        "pane-board-only"]
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
        _book(layouts=[_layout(), _layout(layout_filter="anchored")])
    with pytest.raises(ValueError) as caught:
        _book(notes=[_note(), _note(note_id="note-two", seq=2)])
    assert "one stance stands per session target" in str(caught.value)
    fields = {
        "schema": MULTI_PANE_SCHEMA, "slice": "M-192",
        "multi_pane": {"title": "A test pane book"},
        "panes": [_stored_pane(_pane())],
        "layouts": [_stored_layout(_layout())], "notes": [],
        "panels": [], "verdict": "open",
    }
    with pytest.raises(ValueError):
        build_book(fields)
    del fields["verdict"]
    fields["pane_index"] = "stored"
    with pytest.raises(ValueError):
        build_book(fields)
    raw = {
        "schema": MULTI_PANE_SCHEMA, "slice": "M-192",
        "multi_pane": {"title": "A test pane book"},
        "panes": [], "layouts": [], "notes": [], "panels": [],
        "opens_pane": True,
    }
    with pytest.raises(ValueError) as caught:
        build_book(raw)
    assert "held as data alone" in str(caught.value)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / MULTI_PANE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "multi_pane.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_multi_pane_file(path)
    assert book.title == EXAMPLE_TITLE
    assert total_panes(book) == 6


def test_registry_holds_panes_and_layouts_one_by_one():
    registry = MultiPaneRegistry()
    assert registry.list_items() == ()
    held = registry.register_pane(_pane())
    assert held.pane_id == "pane-test"
    registry.register_layout(_layout())
    assert [i.item_id if hasattr(i, "item_id") else i.layout_id
            for i in registry.list_items()] == ["pane-test", "layout-test"]
    assert registry.get_pane("pane-test").title == "A test pane"
    assert registry.get_layout("layout-test").layout_filter == "all"
    assert registry.book().title == "An unheld pane book"
    with pytest.raises(ValueError):
        registry.register_pane(_pane(seq=2))
    with pytest.raises(ValueError):
        registry.register_pane(_pane(pane_id="pane-two"))
    with pytest.raises(KeyError):
        registry.get_pane("pane-nope")


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = MultiPaneRegistry()
    book = _mixed_book()
    held = registry.register_book(book)
    assert held.title == "A test pane book"
    assert len(registry.list_panes()) == 2
    other = _book(panes=[_pane(
        pane_id="pane-x", seq=9, title="Other", target="mythic_agent/core/session.py:128")],
        layouts=[_layout(layout_id="layout-x", seq=9)])
    object.__setattr__(other, "title", "Another title")
    with pytest.raises(ValueError):
        registry.register_book(other)


def test_plain_words_and_formatters():
    book = _mixed_book()
    assert "kind: 'work'" in format_book(book)
    assert "pane-board-only" in format_book(book, "board")
    assert "pane-test" not in format_book(book, "board")
    assert "Pane panel under layout layout-test" in format_panel(book)
    assert panel_plain_words(book).startswith(
        "The pane book holds 2 panes")
    screen = format_pane_screen(book)
    assert "Multi-Pane Working (M-192)" in screen
    assert PLAIN_EXPLANATION in screen
    assert "pane-terminal-sweep" not in screen
    assert "pane-board-only" in screen
    record = book_record(book)
    assert record["type"] == "pane_book"
    assert record["title"] == "A test pane book"
    assert len(record["panes"]) == 2
    panel = derive_panel(book)
    assert panel_record(panel, book)["rows"][0]["item_id"] == "pane-test"
    assert verdict_record(derive_verdict(book), book)["verdict"] == (
        "strained")
    pane_text = format_pane(book.panes[0])
    assert "Pane: A test pane" in pane_text
    assert "Target: mythic_agent/core/session.py:128" in pane_text


def test_parse_args_inspect_and_loader_targets():
    assert parse_pane_args("") == ("show", None)
    assert parse_pane_args("show") == ("show", None)
    assert parse_pane_args(None) == ("show", None)
    assert parse_pane_args("pane pane-test") == (
        "pane", "pane-test")
    assert parse_pane_args("target resume from checkpoint") == (
        "target", "resume from checkpoint")
    assert parse_pane_args("kind work") == (
        "kind", "work")
    assert parse_pane_args("layout layout-test") == ("layout", "layout-test")
    assert parse_pane_args("note note-test") == (
        "note", "note-test")
    assert parse_pane_args("index") == ("index", None)
    assert parse_pane_args("panel") == ("panel", None)
    assert parse_pane_args("verdict") == ("verdict", None)
    for bad in ("dance", "pane", "target", "kind", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_pane_args(bad)
    pane = _pane()
    assert inspect_pane_source(pane) == {
        "kind": "pane", "pane_id": "pane-test"}
    assert inspect_pane_source(_stored_pane(pane))["kind"] == (
        "pane")
    assert inspect_pane_source(_stored_layout(_layout()))["kind"] == (
        "layout")
    assert inspect_pane_source(_note().to_record())["kind"] == (
        "note")
    assert inspect_pane_source(42)["kind"] == "unknown"
    book = load_multi_pane({
        "schema": MULTI_PANE_SCHEMA, "slice": "M-192",
        "multi_pane": {"title": "A judged book"},
        "panes": [_stored_pane(_pane())],
        "layouts": [_stored_layout(_layout())], "notes": [], "panels": []})
    assert isinstance(book, PaneBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_multi_pane({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_multi_pane({"slice": "M-999"})
    built = build_pane(
        pane_id="pane-kw", seq=3, title="Kw Session",
        kind="work", width="1 share", height="1 share",
        target="mythic_agent/core/session.py:128", detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="pane-test")
    assert built.pane_id == "pane-kw"
    assert pane_passes(built) is True
