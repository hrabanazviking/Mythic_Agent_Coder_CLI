"""M-176 Slash-Command Palace - pure-layer tests.

TIER: integration

The pure layer is the palace entry, held as data:
one discoverable command with its kind in the
closed kind set (shipped, custom - the roadmap's
own order), its command in the shape the surfaces
speak, its plain-language description, one example
of its use and its tags, with its provenance whole
(the day it was recorded, who recorded it, its
source and the session it was recorded in). A
custom command is first held as its own record,
judged whole - its prompt template held as data,
never rendered or run - and joins the palace as an
entry of the custom kind on the same terms as a
shipped one. A browse is held as its own record,
the words typed after /, read into tokens by the
shipped M-175 picker's one token road, imported.
An entry's score under a browse is derived from
those tokens against the entry's own command,
tags, description and example - never stored,
never ranked by hand. The panel is derived for
one held browse and the verdict is derived for
the whole book under one browse. The shipped
example book is held in a data file, and a loader
reads a book from any file. Nothing here runs a
command it shows, renders a template, opens a
skill, changes a session, renders a live UI,
sends, posts, schedules, calls a model or
persists anything: an entry held here is a
finding, never the act of running the command
found, and browsing commits no choice at all.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.command_palace import (
    COMMAND_PALACE_RESOURCE,
    COMMAND_PALACE_SCHEMA,
    COMMAND_PALACE_SLICE,
    ENTRY_KINDS,
    KIND_FILTERS,
    PLAIN_EXPLANATION,
    USAGE,
    VERDICT_WORDS,
    CommandPalaceBook,
    CommandPalaceRegistry,
    CustomCommand,
    PalaceBrowse,
    PalaceEntry,
    PalaceKindCount,
    PalacePanel,
    PalacePanelRow,
    PalaceVerdict,
    book_record,
    browse_record,
    build_book,
    build_browse,
    build_custom_command,
    build_entry,
    build_panel,
    build_row,
    build_verdict,
    custom_command_record,
    derive_panel,
    derive_verdict,
    entries_with_kind,
    entry_from_custom_command,
    entry_from_picker_candidate,
    entry_from_shipped_command,
    entry_record,
    format_book,
    format_browse,
    format_command_palace_screen,
    format_entry,
    format_panel,
    format_verdict,
    inspect_entry_source,
    line_of,
    load_command_palace,
    load_command_palace_file,
    normalize_kind,
    normalize_kind_filter,
    browse_plain_words,
    panel_plain_words,
    panel_record,
    parse_command_palace_args,
    plain_words,
    rank_entries,
    score_of,
    total_entries,
    validate_browse,
    validate_custom_command,
    validate_entry,
    validate_panel,
    validate_row,
    validate_verdict,
    verdict_plain_words,
    verdict_record,
)
from mythic_agent.core.fuzzy_picker import (
    build_candidate as build_picker_candidate,
    parse_query,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.tui_redesign_charter import load_charter

ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_TITLE = "Command Palace at the M-175 slice boundary"

BY = "the coordinator"
ON = "2026-11-09"


def _entry(**overrides):
    fields = {
        "entry_id": "entry-test",
        "kind": "shipped",
        "command": "/thing",
        "description": "The thing command, standing for the tests.",
        "example": "/thing now",
        "tags": ["thing", "command"],
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_entry(fields)


def _stored_entry(entry):
    stored = entry.to_record()
    for key in ("type", "slice", "line"):
        stored.pop(key)
    return stored


def _browse(**overrides):
    fields = {
        "browse_id": "browse-test",
        "seq": 1,
        "text": "thing",
        "kind_filter": "all",
        "detail": "Find the thing for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_browse(fields)


def _stored_browse(browse):
    stored = browse.to_record()
    for key in ("type", "slice", "tokens"):
        stored.pop(key)
    return stored


def _custom(**overrides):
    fields = {
        "custom_id": "custom-test",
        "command": "/thing",
        "description": "The thing custom command, for the tests.",
        "example": "/thing now",
        "template": "Do the thing with the given words.",
        "arguments": ["words"],
        "home": "project",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_custom_command(fields)


def _book(entries=None, browses=(), **overrides):
    fields = {
        "title": "A test palace book",
        "entries": [_stored_entry(item) for item in (
            entries if entries is not None else [_entry()])],
        "browses": [_stored_browse(item) for item in browses],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(
        entries=[
            _entry(),
            _entry(entry_id="entry-second", kind="custom",
                   command="/otherthing",
                   description="The other thing command, for the tests.",
                   example="/otherthing",
                   tags=["thing", "custom"]),
            _entry(entry_id="entry-other", kind="shipped",
                   command="/unrelated",
                   description="An unrelated command, for the tests.",
                   example="/unrelated",
                   tags=["other"]),
        ],
        browses=[_browse()])


# ---------------------------------------------------------------------
# The shipped example book, the roadmap and the charter.
# ---------------------------------------------------------------------


def test_shipped_book_loads_with_pinned_shape():
    book = load_command_palace()
    assert book.title == EXAMPLE_TITLE
    assert book.entry_ids() == (
        "entry-help", "entry-model",
        "entry-approvalcards", "entry-sliceboard",
        "entry-fuzzypicker", "entry-compact",
        "entry-standup", "entry-verse")
    first = book.entries[0]
    assert first.command == "/help"
    assert first.kind == "shipped"
    assert book.browse_ids() == (
        "browse-session", "browse-picker")
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m175-boundary"
    assert panel.as_of == "2026-11-09"
    assert [row.entry_id for row in panel.rows] == [
        "entry-compact", "entry-model",
        "entry-fuzzypicker", "entry-standup"]
    derived = derive_panel(book, "browse-session")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_entries == derived.total_entries == 8
    assert panel.total_matched == derived.total_matched == 4
    assert {c.kind: c.items for c in panel.kind_counts} == {
        "shipped": 3, "custom": 1}
    assert derive_verdict(book, "browse-session").verdict == "spanning"
    assert derive_verdict(book, "browse-picker").verdict == (
        "shelved")
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / COMMAND_PALACE_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == COMMAND_PALACE_SCHEMA
    assert raw["slice"] == "M-176"


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-176")]
    assert slice_.title == "Slash-command palace"
    assert slice_.part == 8
    assert "discoverable" in slice_.summary
    assert "plain-language descriptions and examples" in slice_.summary
    assert "custom commands" in slice_.summary
    assert COMMAND_PALACE_SLICE == "M-176"


def test_charter_s06_names_m176():
    charter = load_charter()
    screen = charter.screen("subagent_picker")
    assert screen.id == "S-06"
    assert screen.verdict == "keep"
    assert "M-176" in screen.owning_slices
    assert "M-175" in screen.owning_slices
    assert screen.judgement("K-01").standing == "strains"
    assert screen.judgement("K-09").standing == "strains"
    assert "fuzzy picker" in screen.direction
    assert "auto-dismiss" in screen.direction
    assert "plain words first" in screen.direction


def test_closed_vocabularies():
    assert ENTRY_KINDS == ("shipped", "custom")
    assert KIND_FILTERS == ("all",) + ENTRY_KINDS
    assert VERDICT_WORDS == ("spanning", "shelved", "empty")
    assert normalize_kind("skills") == "custom"
    assert normalize_kind("Builtin") == "shipped"
    assert normalize_kind_filter("everything") == "all"
    assert normalize_kind_filter("customs") == "custom"
    with pytest.raises(ValueError):
        normalize_kind("whenever")
    with pytest.raises(ValueError):
        normalize_kind_filter("whenever")
    assert "every command discoverable" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /commandpalace")


# ---------------------------------------------------------------------
# The entry: judged whole, its score derived by the one road.
# ---------------------------------------------------------------------


def test_entry_record_round_trips():
    entry = _entry()
    assert build_entry(_stored_entry(entry)) == entry
    record = entry.to_record()
    assert record["line"] == "/thing - shipped"
    assert record["type"] == "command_palace_entry"
    assert record["tags"] == ["thing", "command"]
    assert entry.line == line_of(entry)


def test_entry_provenance_is_whole_and_required():
    entry = _entry()
    assert entry.actor == BY
    assert entry.origin_session == "session-test"
    for missing in ("entry_id", "kind", "command", "description",
                    "example", "tags", "recorded_on", "actor",
                    "source", "origin_session"):
        fields = _stored_entry(entry)
        fields.pop(missing)
        with pytest.raises(ValueError):
            build_entry(fields)
    with pytest.raises(ValueError):
        _entry(tags=[])


def test_entry_refuses_unknown_keys_and_derived_keys():
    for derived_key, value in (
            ("score", 75), ("rank", 1),
            ("line", "/thing - shipped"),
            ("results", ["/thing"])):
        fields = _stored_entry(_entry())
        fields[derived_key] = value
        with pytest.raises(ValueError):
            build_entry(fields)
    fields = _stored_entry(_entry())
    fields["surprise"] = "x"
    with pytest.raises(ValueError):
        build_entry(fields)
    with pytest.raises(ValueError):
        _entry(kind="whatever")


def test_entry_alias_spellings_read_onto_the_fields():
    entry = build_entry({
        "id": "entry-alias", "type_of": "skills",
        "name": "/alias",
        "detail": "An alias-spelled entry for the tests.",
        "usage": "/alias",
        "keywords": ["alias"], "day": ON, "by": BY,
        "source": "alias source", "session": "session-alias"})
    assert entry.kind == "custom"
    assert entry.command == "/alias"
    assert entry.description == (
        "An alias-spelled entry for the tests.")
    assert entry.example == "/alias"
    assert entry.tags == ("alias",)


def test_entry_example_must_show_its_own_command():
    with pytest.raises(ValueError):
        _entry(example="/other now")
    with pytest.raises(ValueError):
        _entry(example="thing now")
    entry = _entry(example="/thing")
    assert entry.example == "/thing"


def test_score_and_line_are_derived_by_the_one_road():
    exact = _entry(
        entry_id="entry-alpha", command="/palace",
        description="palace stands here.",
        example="/palace", tags=["palace"])
    assert score_of(exact, "palace") == 230
    assert line_of(exact) == "/palace - shipped"
    opening = _entry(
        entry_id="entry-opening", command="/palaces",
        description="nothing here.",
        example="/palaces", tags=["zzz"])
    assert score_of(opening, "palace") == 55
    holding = _entry(
        entry_id="entry-holding", command="/xpalace",
        description="nothing here.",
        example="/xpalace", tags=["zzz"])
    assert score_of(holding, "palace") == 35
    threaded = _entry(
        entry_id="entry-threaded", command="/pxalxaxcxe",
        description="nothing here.",
        example="/pxalxaxcxe", tags=["zzz"])
    assert score_of(threaded, "palace") == 10
    assert score_of(exact, {"text": "palace", "kind_filter": "custom"}) == 0
    assert exact.to_record().get("score") is None


def test_one_road_for_both_kinds():
    # The same browse is parsed by the one token road
    # whatever kind it ranges over, and a kind filter
    # narrows which entries stand - never the score.
    book = _mixed_book()
    browse = _browse(text="thing")
    ranked = rank_entries(book.entries, browse)
    assert [e.entry_id for e in ranked] == [
        "entry-test", "entry-second"]
    scores = {e.entry_id: score_of(e, browse) for e in ranked}
    assert scores["entry-test"] > scores["entry-second"] > 0
    only_custom = _browse(
        browse_id="browse-custom", seq=2, text="thing",
        kind_filter="custom")
    assert [e.entry_id for e in rank_entries(
        book.entries, only_custom)] == ["entry-second"]
    assert score_of(book.entry_for("entry-second"), only_custom) == (
        scores["entry-second"])


def test_custom_entries_join_on_the_same_terms():
    # Two entries alike in every judged field but
    # their kind derive the same score under one
    # browse, and stand shipped first on a tie: the
    # custom kind joins on the same terms.
    shipped = _entry(entry_id="entry-ship")
    custom = _entry(entry_id="entry-cust", kind="custom")
    browse = _browse(text="thing")
    assert score_of(shipped, browse) == score_of(custom, browse)
    ranked = rank_entries([custom, shipped], browse)
    assert [e.entry_id for e in ranked] == [
        "entry-ship", "entry-cust"]


# ---------------------------------------------------------------------
# Composition: the shipped rooms, by import.
# ---------------------------------------------------------------------


def test_entry_from_shipped_command_shape():
    entry = entry_from_shipped_command(
        "/commandpalace", entry_id="entry-cmd",
        description="Shows the slash-command palace.",
        example="/commandpalace")
    assert entry.kind == "shipped"
    assert entry.command == "/commandpalace"
    with pytest.raises(ValueError):
        entry_from_shipped_command(
            "commandpalace", entry_id="entry-x",
            description="No slash, no command.",
            example="/commandpalace")
    with pytest.raises(ValueError):
        entry_from_shipped_command(
            "/Command Palace", entry_id="entry-x",
            description="Not one lowercase word.",
            example="/Command Palace")


def test_entry_from_picker_candidate_by_import():
    candidate = build_picker_candidate({
        "candidate_id": "cand-cmd", "kind": "command",
        "label": "/commandpalace",
        "detail": "Shows the slash-command palace.",
        "tags": ["palace", "command"],
        "recorded_on": ON, "actor": BY,
        "source": "test source",
        "origin_session": "session-test"})
    entry = entry_from_picker_candidate(
        candidate, entry_id="entry-cmd",
        example="/commandpalace")
    assert entry.kind == "shipped"
    assert entry.command == "/commandpalace"
    assert entry.description == "Shows the slash-command palace."
    assert entry.tags == ("palace", "command")
    not_a_command = build_picker_candidate({
        "candidate_id": "cand-file", "kind": "file",
        "label": "docs/thing.md",
        "detail": "A file candidate, for the tests.",
        "tags": ["file"],
        "recorded_on": ON, "actor": BY,
        "source": "test source",
        "origin_session": "session-test"})
    with pytest.raises(ValueError):
        entry_from_picker_candidate(
            not_a_command, entry_id="entry-x",
            example="/commandpalace")
    with pytest.raises(ValueError):
        entry_from_picker_candidate(
            None, entry_id="entry-x", example="/commandpalace")


def test_custom_command_is_judged_whole():
    custom = _custom()
    assert validate_custom_command(
        _stored_custom(custom)) == custom
    assert custom.arguments == ("words",)
    assert custom.home == "project"
    record = custom.to_record()
    assert record["type"] == "command_palace_custom_command"
    assert record["template"] == (
        "Do the thing with the given words.")
    for missing in ("custom_id", "command", "description",
                    "example", "template", "home",
                    "recorded_on", "actor", "source",
                    "origin_session"):
        fields = _stored_custom(custom)
        fields.pop(missing)
        with pytest.raises(ValueError):
            build_custom_command(fields)
    with pytest.raises(ValueError):
        _custom(home="elsewhere")
    bare = _custom(arguments=None)
    assert bare.arguments == ()
    assert isinstance(custom, CustomCommand)


def _stored_custom(custom):
    stored = custom.to_record()
    for key in ("type", "slice"):
        stored.pop(key)
    return stored


def test_entry_from_custom_command_by_import():
    custom = _custom()
    entry = entry_from_custom_command(
        custom, entry_id="entry-custom")
    assert entry.kind == "custom"
    assert entry.command == "/thing"
    assert entry.description == custom.description
    assert entry.example == custom.example
    assert entry.actor == BY
    # The palace is a catalogue: the template stays
    # on the custom command's own record and is
    # never carried into, rendered or run by an
    # entry.
    assert "template" not in entry.to_record()
    assert not hasattr(entry, "template")
    with pytest.raises(ValueError):
        entry_from_custom_command(None, entry_id="entry-x")


def test_inspect_entry_source_names_what_a_piece_is():
    found = inspect_entry_source(
        {"kind": "skills", "command": "/verse"})
    assert found["kind"] == "custom"
    assert found["command"] == "/verse"
    bad = inspect_entry_source({"kind": "nope", "command": "/x"})
    assert bad["kind"] is None
    assert inspect_entry_source({"command": "/x"})["kind"] is None
    assert inspect_entry_source("nope")["kind"] is None


# ---------------------------------------------------------------------
# The browse record and the ranking: judged whole, derived order.
# ---------------------------------------------------------------------


def test_browse_is_judged_whole():
    browse = _browse()
    assert build_browse(_stored_browse(browse)) == browse
    assert validate_browse(_stored_browse(browse)) == browse
    with pytest.raises(ValueError):
        _browse(text="!!!")
    fields = _stored_browse(browse)
    fields["results"] = ["entry-test"]
    with pytest.raises(ValueError):
        build_browse(fields)
    fields = _stored_browse(browse)
    fields["tokens"] = ["thing"]
    with pytest.raises(ValueError):
        build_browse(fields)
    fields = _stored_browse(browse)
    fields.pop("detail")
    with pytest.raises(ValueError):
        build_browse(fields)


def test_browse_tokens_come_from_the_picker_road():
    # The browse's tokens are read by the shipped
    # M-175 picker's one token road, imported - the
    # palace grows no token road of its own.
    browse = _browse(text="Hello, World! 42")
    assert browse.tokens == parse_query("Hello, World! 42")
    assert browse.tokens == ("hello", "world", "42")


def test_rank_entries_orders_by_score_kind_command():
    book = load_command_palace()
    ranked = rank_entries(
        book.entries, book.browse_for("browse-session"))
    assert [e.entry_id for e in ranked] == [
        "entry-compact", "entry-model",
        "entry-fuzzypicker", "entry-standup"]
    assert [score_of(e, book.browse_for("browse-session"))
            for e in ranked] == [25, 25, 5, 5]


# ---------------------------------------------------------------------
# The panel and the verdict: derived, never chosen.
# ---------------------------------------------------------------------


def test_panel_is_derived_for_one_browse():
    book = _mixed_book()
    panel = derive_panel(book, "browse-test")
    assert panel.total_entries == 3
    assert panel.total_matched == 2
    assert [row.entry_id for row in panel.rows] == [
        "entry-test", "entry-second"]
    assert {c.kind: c.items for c in panel.kind_counts} == {
        "shipped": 1, "custom": 1}
    assert panel.rows[0].line == "/thing - shipped"
    assert panel.browse_id == "browse-test"
    assert PalaceKindCount(kind="skills", items=2).to_record() == {
        "kind": "custom", "items": 2}
    assert isinstance(panel, PalacePanel)


def test_panel_refuses_a_stored_panel_that_disagrees():
    book = _mixed_book()
    stored = derive_panel(book, "browse-test").to_record()
    stored.pop("type")
    stored.pop("slice")
    stored["total_matched"] = 3
    with pytest.raises(ValueError):
        validate_panel(stored, book)
    stored = derive_panel(book, "browse-test").to_record()
    stored.pop("type")
    stored.pop("slice")
    stored["rows"][0]["score"] = 999
    with pytest.raises(ValueError):
        validate_panel(stored, book)
    panel = build_panel(
        derive_panel(book, "browse-test").to_record(), book)
    assert panel.total_matched == 2


def test_row_is_judged_against_its_entry_and_browse():
    entry = _entry()
    browse = _browse(text="thing")
    row = build_row(entry=entry, browse=browse)
    assert row.score == score_of(entry, browse)
    assert row.line == "/thing - shipped"
    assert validate_row(row.to_record(), entry, browse) == row
    bad = row.to_record()
    bad["score"] = row.score + 1
    with pytest.raises(ValueError):
        validate_row(bad, entry, browse)
    bad = row.to_record()
    bad["line"] = "a chosen line"
    with pytest.raises(ValueError):
        validate_row(bad, entry, browse)
    assert isinstance(row, PalacePanelRow)


def test_verdict_words_spanning_shelved_empty():
    book = load_command_palace()
    assert derive_verdict(book, "browse-session").verdict == "spanning"
    assert derive_verdict(
        book, "browse-picker").verdict == "shelved"
    empty_browse = _browse(
        browse_id="browse-empty", seq=9, text="zzzz",
        detail="Find nothing, for the tests.")
    empty = derive_verdict(book, empty_browse)
    assert empty.verdict == "empty"
    assert empty.total_matched == 0
    assert build_verdict(empty.to_record(), book, empty_browse) == empty
    with pytest.raises(ValueError):
        PalaceVerdict(
            total_entries=8, total_matched=4, distinct_kinds=2,
            earliest_on=ON, latest_on=ON, verdict="shelved")
    with pytest.raises(ValueError):
        validate_verdict(empty.to_record(), book, "browse-session")
    assert isinstance(empty, PalaceVerdict)


# ---------------------------------------------------------------------
# The book, the file loader and the registry.
# ---------------------------------------------------------------------


def test_book_laws_one_entry_per_id_and_command():
    with pytest.raises(ValueError):
        _book(entries=[_entry(), _entry(
            command="/other", example="/other")])
    with pytest.raises(ValueError):
        _book(entries=[
            _entry(), _entry(entry_id="entry-two")])
    with pytest.raises(ValueError):
        _book(browses=[
            _browse(), _browse(browse_id="browse-two", text="other")])
    book = _mixed_book()
    assert book.entry_for("entry-second").command == "/otherthing"
    assert book.browse_for("browse-test").text == "thing"
    with pytest.raises(KeyError):
        book.entry_for("entry-nope")
    with pytest.raises(KeyError):
        book.browse_for("browse-nope")
    assert total_entries(book) == 3
    assert [e.entry_id for e in entries_with_kind(
        book, "skills")] == ["entry-second"]
    assert isinstance(book, CommandPalaceBook)


def test_book_file_loader_reads_any_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "command_palace.yaml").read_text(encoding="utf-8")
    path = tmp_path / "command_palace.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_command_palace_file(path)
    assert book.title == EXAMPLE_TITLE
    assert total_entries(book) == 8


def test_registry_holds_entries_and_browses_one_by_one():
    registry = CommandPalaceRegistry()
    registry.register_entry(_entry())
    registry.register_entry(_entry(
        entry_id="entry-second", kind="custom", command="/otherthing",
        description="The other thing command, for the tests.",
        example="/otherthing",
        tags=["thing", "custom"]))
    held = registry.register_browse(_browse(browse_id=None))
    assert held.browse_id == "browse-1"
    assert registry.latest_browse().browse_id == "browse-1"
    assert registry.book().title == "Command Palace"
    assert registry.panel("browse-1").total_matched == 2
    assert registry.verdict("browse-1").verdict == "spanning"
    with pytest.raises(ValueError):
        registry.register_entry(_entry(command="/another"))
    with pytest.raises(ValueError):
        registry.register_entry(_entry(entry_id="entry-third"))
    with pytest.raises(ValueError):
        registry.register_browse(_browse(browse_id="browse-1", seq=2))
    with pytest.raises(ValueError):
        registry.register_browse(_browse(browse_id="browse-two"))
    assert [b.browse_id for b in registry.list_browses()] == ["browse-1"]
    with pytest.raises(KeyError):
        registry.get_entry("entry-nope")
    with pytest.raises(KeyError):
        registry.get_browse("browse-nope")


def test_registry_register_book_and_refusals():
    registry = CommandPalaceRegistry()
    book = registry.register_book(_mixed_book())
    assert total_entries(book) == 3
    assert registry.title() == "A test palace book"
    with pytest.raises(ValueError):
        registry.register_book(_book())
    other = CommandPalaceRegistry(_book())
    assert other.get_entry("entry-test").entry_id == "entry-test"
    assert isinstance(other.book(), CommandPalaceBook)
    assert isinstance(_entry(), PalaceEntry)
    assert isinstance(_browse(), PalaceBrowse)


# ---------------------------------------------------------------------
# News, plain words, formatters and the grammar.
# ---------------------------------------------------------------------


def test_news_records_carry_headlines():
    entry = _entry()
    news = entry_record(entry)
    assert news["news"] is True
    assert news["type"] == "command_palace_entry"
    assert "/thing - shipped" in news["headline"]
    custom_news = custom_command_record(_custom())
    assert custom_news["type"] == "command_palace_custom_command"
    assert "/thing" in custom_news["headline"]
    browse_news = browse_record(_browse())
    assert browse_news["type"] == "command_palace_browse"
    assert "thing" in browse_news["headline"]
    panel_news = panel_record(derive_panel(_mixed_book(), "browse-test"))
    assert "Command palace panel" in panel_news["headline"]
    verdict_news = verdict_record(
        derive_verdict(_mixed_book(), "browse-test"))
    assert "spanning" in verdict_news["headline"]
    book_news = book_record(_mixed_book())
    assert book_news["entry_count"] == 3
    assert book_news["browse_count"] == 1


def test_formatters_and_screen():
    book = load_command_palace()
    text = format_entry(book.entry_for("entry-verse"))
    assert "Kind: custom" in text
    assert "Command: /verse" in text
    assert "Example: /verse on courage" in text
    browse_text = format_browse(book.browse_for("browse-session"))
    assert "Tokens: session" in browse_text
    listed = format_book(book)
    assert "entry-help: /help - shipped" in listed
    customs = format_book(book, kind="custom")
    assert "entry-standup" in customs
    assert "entry-model" not in customs
    assert "Panel in Command Palace at the M-175 slice boundary" in (
        format_panel(book))
    assert format_verdict(book).startswith(
        "Verdict in Command Palace over")
    assert "spanning" in format_verdict(book)
    screen = format_command_palace_screen()
    assert "Command Palace (M-176)" in screen
    assert "commits" in screen
    assert "/verse - custom" in plain_words(
        book.entry_for("entry-verse"))
    assert "commits no choice" in browse_plain_words(
        book.browse_for("browse-session"))
    assert "Shown, in derived order" in panel_plain_words(book)
    assert "spanning" in verdict_plain_words(book)


def test_parse_command_palace_args_grammar():
    assert parse_command_palace_args("") == ("show", None)
    assert parse_command_palace_args(None) == ("show", None)
    assert parse_command_palace_args("show") == ("show", None)
    assert parse_command_palace_args("list") == ("show", None)
    assert parse_command_palace_args("entry entry-test") == (
        "entry", "entry-test")
    assert parse_command_palace_args("browse browse-session") == (
        "browse", "browse-session")
    assert parse_command_palace_args("visit approval cards") == (
        "visit", "approval cards")
    assert parse_command_palace_args("kind skills") == ("kind", "custom")
    assert parse_command_palace_args("panel") == ("panel", None)
    assert parse_command_palace_args("verdict") == ("verdict", None)
    for bad in ("entry", "browse", "visit", "kind whenever",
                "panel now", "dance", 42):
        with pytest.raises(ValueError):
            parse_command_palace_args(bad)


def test_pure_layer_imports_no_agent_or_ui():
    text = (ROOT / "mythic_agent" / "core"
            / "command_palace.py").read_text(encoding="utf-8")
    assert "mythic_agent.agents" not in text
    assert "import textual" not in text
    assert "from ..agents" not in text


# -- agent layer -----------------------------------------------------------
#
# M-176 agent layer: the agent holds a
# CommandPalaceRegistry for the session (session
# state only, no new setting), entries and browse
# records are held by being registered - each
# judged whole before it is held - published as
# their entry_record / browse_record session news
# through the checkpoint road, deduped per shape -
# an entry composed from a shipped room by import
# stands on the register road exactly as the pure
# layer composed it, the browsing road composes
# one browse record at the held book's next
# sequence and publishes the derived panel and
# verdict news with it, whole-book register and
# record roads hold a book judged whole first, the
# report road renders the held book (or the
# shipped example when unheld) through the pure
# formatters, and the /commandpalace surface rides
# both roads on the pure parser + formatters.
# Status, get, kind, panel, verdict and report
# reads register and publish nothing, answer from
# the held registry first and from the shipped
# example only while nothing is held - a held
# entry never falls back to the example. The panel
# and the verdict derive at call time from the
# whole book under a browse, never held. This
# layer sends nothing, posts nothing, schedules
# nothing, calls no model, persists nothing beyond
# the session journal news, runs no command the
# palace shows, renders no custom command's
# template, renders no live UI and banks nothing -
# an entry held here is a finding, never the act
# of running the command found, and browsing
# commits no choice at all.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _palace_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "command_palace.yaml").read_text(encoding="utf-8")
    path = tmp_path / "command_palace.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestCommandPalaceAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.command_palace_status()
        assert status["entries"] == []
        assert status["browses"] == []
        assert status["book"] is None
        assert status["command_palace"]["title"] == EXAMPLE_TITLE
        assert len(status["command_palace"]["entries"]) == 8
        assert len(status["command_palace"]["browses"]) == 2
        assert status["panel"]["total_entries"] == 8
        assert status["panel"]["total_matched"] == 4
        assert status["panels"][0]["panel_id"] == "panel-m175-boundary"
        assert status["book_record"]["entry_count"] == 8
        assert status["book_record"]["browse_count"] == 2
        assert status["verdict"]["verdict"] == "spanning"
        assert "/verse - custom" in status["plain_words"]
        assert "Command Palace (M-176)" in status["screen"]
        assert "4 of 8 commands show" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._command_palace_registry()
        assert agent._command_palace_registry() is first
        assert agent._command_palace_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.command_palace_status()
        assert agent.get_palace_entry(
            "entry-verse").kind == "custom"
        assert agent.get_palace_browse(
            "browse-session").text == "session"
        assert [e.entry_id for e in agent.command_palace_with_kind(
            "shipped")] == [
                "entry-help", "entry-model",
                "entry-approvalcards", "entry-sliceboard",
                "entry-fuzzypicker", "entry-compact"]
        assert [e.entry_id for e in agent.command_palace_with_kind(
            "skills")] == ["entry-standup", "entry-verse"]
        agent.command_palace_panel()
        agent.command_palace_verdict()
        agent.report_command_palace()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("command_palace")] == []
        with pytest.raises(KeyError):
            agent.get_palace_entry("entry-nope")
        with pytest.raises(KeyError):
            agent.get_palace_browse("browse-nope")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_palace_entry(_entry())
        status = agent.command_palace_status()
        assert [item["entry_id"] for item in status["entries"]] == [
            "entry-test"]
        assert status["book"]["title"] == "Command Palace"
        assert status["panel"] is None
        assert status["verdict"] is None

    def test_held_entry_never_falls_back_to_the_example(
            self, agent):
        agent.register_palace_entry(_entry())
        with pytest.raises(KeyError):
            agent.get_palace_entry("entry-help")
        with pytest.raises(KeyError):
            agent.get_palace_browse("browse-session")
        entry = agent.get_palace_entry("entry-test")
        assert entry.command == "/thing"
        assert agent.command_palace_book().title == "Command Palace"


class TestCommandPalaceAgentHolding:
    def test_register_entry_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_palace_entry(_entry())
        assert outcome["entry"]["entry_id"] == "entry-test"
        assert outcome["record_news"]["news"] is True
        assert outcome["record_news"]["type"] == "command_palace_entry"
        assert "entry-test" in outcome["screen"]
        agent.register_palace_entry(_entry(
            entry_id="entry-second", kind="custom",
            command="/otherthing",
            description="The other thing command, for the tests.",
            example="/otherthing",
            tags=["thing", "custom"]))
        events = _palace_events(store, session_id, "command_palace_entry")
        assert len(events) == 2
        agent._publish_command_palace_record(entry_record(_entry()))
        agent._publish_command_palace_record(
            {"type": "slice_board_card", "news": True})
        events = _palace_events(store, session_id, "command_palace_entry")
        assert len(events) == 2
        agent.close()

    def test_duplicate_entry_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_palace_entry(_entry())
        with pytest.raises(ValueError):
            agent.register_palace_entry(_entry())
        with pytest.raises(ValueError):
            agent.register_palace_entry(
                _entry(entry_id="entry-two"))
        with pytest.raises(ValueError):
            agent.register_palace_entry(
                _entry(command="/another", example="/another"))
        events = _palace_events(store, session_id, "command_palace_entry")
        assert len(events) == 1
        agent.close()

    def test_composed_entries_hold_by_import(self, agent):
        shipped = entry_from_shipped_command(
            "/commandpalace", entry_id="entry-cmd",
            description="Shows the slash-command palace.",
            example="/commandpalace")
        outcome = agent.register_palace_entry(shipped)
        assert outcome["entry"]["command"] == "/commandpalace"
        candidate = build_picker_candidate({
            "candidate_id": "cand-cmd", "kind": "command",
            "label": "/fuzzypicker",
            "detail": "Shows the fuzzy everything picker.",
            "tags": ["fuzzy", "picker"],
            "recorded_on": ON, "actor": BY,
            "source": "test source",
            "origin_session": "session-test"})
        from_picker = entry_from_picker_candidate(
            candidate, entry_id="entry-picker",
            example="/fuzzypicker")
        agent.register_palace_entry(from_picker)
        custom = entry_from_custom_command(
            _custom(custom_id="custom-verse", command="/verse",
                    description="Answers in a short verse.",
                    example="/verse on courage"),
            entry_id="entry-verse")
        agent.register_palace_entry(custom)
        assert [e.entry_id for e in agent.command_palace_with_kind(
            "custom")] == ["entry-verse"]
        assert agent.get_palace_entry(
            "entry-picker").command == "/fuzzypicker"

    def test_register_browse_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_palace_entry(_entry())
        outcome = agent.register_palace_browse(_browse())
        assert outcome["browse"]["browse_id"] == "browse-test"
        assert outcome["record_news"]["type"] == "command_palace_browse"
        with pytest.raises(ValueError):
            agent.register_palace_browse(_browse(seq=2))
        with pytest.raises(ValueError):
            agent.register_palace_browse(
                _browse(browse_id="browse-two"))
        assert [b.browse_id for b in
                agent._command_palace_registry().list_browses()] == [
                    "browse-test"]
        events = _palace_events(store, session_id, "command_palace_browse")
        assert len(events) == 1
        agent.close()

    def test_browse_road_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_palace_entry(_entry())
        agent.register_palace_entry(_entry(
            entry_id="entry-second", kind="custom",
            command="/otherthing",
            description="The other thing command, for the tests.",
            example="/otherthing",
            tags=["thing", "custom"]))
        outcome = agent.browse_command_palace("thing")
        assert outcome["browse"]["seq"] == 1
        assert outcome["browse"]["browse_id"] == "browse-1"
        assert outcome["record_news"]["type"] == "command_palace_browse"
        assert outcome["panel_record"]["type"] == "command_palace_panel"
        assert outcome["panel_record"]["total_matched"] == 2
        assert outcome["verdict_record"]["type"] == (
            "command_palace_verdict")
        assert outcome["verdict_record"]["verdict"] == "spanning"
        second = agent.browse_command_palace(
            "thing", kind_filter="custom",
            detail="Find the thing custom command alone, for the tests.")
        assert second["browse"]["seq"] == 2
        assert second["verdict_record"]["verdict"] == "shelved"
        assert agent.command_palace_verdict().verdict == "spanning"
        assert len(_palace_events(
            store, session_id, "command_palace_browse")) == 2
        assert len(_palace_events(
            store, session_id, "command_palace_verdict")) == 2
        agent.close()

    def test_browse_road_refuses_an_empty_query(self, agent):
        agent.register_palace_entry(_entry())
        with pytest.raises(ValueError):
            agent.browse_command_palace("!!!")
        assert agent._command_palace_registry().list_browses() == ()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_command_palace_book(_mixed_book())
        assert outcome["count"] == 3
        assert [e["entry_id"] for e in outcome["entries"]] == [
            "entry-test", "entry-second", "entry-other"]
        assert [r["type"] for r in outcome["records_news"]] == [
            "command_palace_entry", "command_palace_entry",
            "command_palace_entry", "command_palace_browse"]
        events = _palace_events(store, session_id, "command_palace_entry")
        assert [e["entry_id"] for e in events] == [
            "entry-test", "entry-second", "entry-other"]
        assert agent.command_palace_book().title == (
            "A test palace book")
        with pytest.raises(ValueError):
            agent.register_command_palace_book(_mixed_book())
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_command_palace_book()
        assert outcome["count"] == 8
        assert outcome["book"]["title"] == EXAMPLE_TITLE
        assert len(_palace_events(
            store, session_id, "command_palace_entry")) == 8
        assert len(_palace_events(
            store, session_id, "command_palace_browse")) == 2
        status = agent.command_palace_status()
        assert status["panels"][0]["panel_id"] == "panel-m175-boundary"
        with pytest.raises(ValueError):
            agent.record_command_palace_book()
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_book_file(tmp_path)
        book = load_command_palace_file(path)
        outcome = agent.record_command_palace_book(book)
        assert outcome["count"] == 8
        assert agent.command_palace_book().title == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_command_palace()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert len(report["entries"]) == 8
        assert report["verdict"]["verdict"] == "spanning"
        assert "entry-verse: /verse - custom" in (
            report["book_text"])
        agent.register_palace_entry(_entry())
        report = agent.report_command_palace()
        assert [e["entry_id"] for e in report["entries"]] == [
            "entry-test"]
        assert "entry-test: /thing - shipped" in (
            report["book_text"])
        assert report["verdict"] is None

    def test_holding_and_browsing_execute_nothing(self, agent):
        for name in (
                "run_command_palace", "execute_palace_entry",
                "run_palace_command", "apply_palace_entry",
                "open_palace_entry", "render_palace_template",
                "bank_command_palace",
                "persist_command_palace", "send_command_palace",
                "schedule_command_palace", "render_command_palace_ui",
                "delete_palace_entry"):
            assert not hasattr(agent, name), name
        agent.register_palace_entry(_entry())
        agent.browse_command_palace("thing")
        # A browse held here only ever looks: no command
        # it shows was run, no template was rendered,
        # and the palace's standing lives in no setting.
        assert agent.command_palace_book().title == "Command Palace"
        assert agent.config.get("command_palace") is None


class TestCommandPalaceTerminalSurface:
    def test_show_entry_browse_visit_kind_panel_verdict(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/commandpalace")
        assert "Command Palace (M-176)" in text
        _, _, text = _slash(
            agent, "/commandpalace entry entry-verse")
        assert "Kind: custom" in text
        assert "Command: /verse" in text
        _, _, text = _slash(agent, "/commandpalace browse browse-session")
        assert "Tokens: session" in text
        _, _, text = _slash(agent, "/commandpalace visit picker")
        assert "entry-fuzzypicker" in text
        _, _, text = _slash(agent, "/commandpalace kind custom")
        assert "entry-verse" in text
        assert "entry-model" not in text
        _, _, text = _slash(agent, "/commandpalace panel")
        assert "Panel in Command Palace at the M-175 slice boundary" in (
            text)
        _, _, text = _slash(agent, "/commandpalace verdict")
        assert "spanning" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/commandpalace [show|entry <entry-id>"
                "|browse <browse-id>|visit <words>|kind <kind>"
                "|panel|verdict]") in text
        _, _, text = _slash(agent, "/commandpalace dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/commandpalace entry entry-nope")
        assert "no entry named" in text


@pytest.fixture()
def palace_handler(agent, monkeypatch):
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


def _palace_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestCommandPalaceCommand:
    def test_show_is_default(self, palace_handler, agent):
        palace_handler._handle_commandpalace("")
        assert "Command Palace (M-176)" in (
            _palace_published_text(palace_handler))

    def test_entry_browse_panel_verdict(
            self, palace_handler, agent):
        palace_handler._handle_commandpalace("entry entry-verse")
        assert "Command: /verse" in (
            _palace_published_text(palace_handler))
        palace_handler._handle_commandpalace("browse browse-session")
        assert "Tokens: session" in _palace_published_text(
            palace_handler)
        palace_handler._handle_commandpalace("panel")
        assert "Panel in Command Palace" in (
            _palace_published_text(palace_handler))
        palace_handler._handle_commandpalace("verdict")
        assert "spanning" in _palace_published_text(palace_handler)

    def test_bad_grammar_is_published(
            self, palace_handler, agent):
        palace_handler._handle_commandpalace("dance party")
        assert USAGE in _palace_published_text(palace_handler)
        palace_handler._handle_commandpalace("entry entry-nope")
        assert "no entry named" in _palace_published_text(
            palace_handler)


class TestChatScreenRoutingCommandPalace:
    def test_commandpalace_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/commandpalace panel", _FakeLog())
        assert calls == [("/commandpalace", "panel")]

    def test_chat_screen_help_and_usage_name_the_palace(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/commandpalace[/green] - show the slash-command palace (M-176)" in (
            text)
        assert ('"/commandpalace": "Usage: /commandpalace | '
                '/commandpalace entry <entry-id>') in text
