"""M-173 The Slice Board - pure-layer tests.

TIER: integration

The pure layer is the board card, held as data:
one slice standing on the board - the slice it
stands for, its place, its part, its title and
its summary in the roadmap's own words, its
column in the closed column set (queued,
building, verifying, banked), its hand flags,
and its provenance whole (the day it was
recorded, who recorded it, its source and the
session it was recorded in). The board line is
derived, never chosen, and a card composed from
the shipped roadmap by import takes its column
from the slice's own ledger status. What the
human does by hand is held as its own action
record - advance, re-order, pause, resume or
strike - and the effective board, its panel and
its verdict are derived by standing the held
actions on the held cards. The shipped example
board is held in a data file, and a loader reads
a board from any file. Nothing here runs a
build, banks anything, sends, posts, schedules,
calls a model or persists anything: a card held
here is a record of a plan, never the work
itself.
"""

from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.slice_board import (
    ACTION_KINDS,
    COLUMNS,
    PLAIN_EXPLANATION,
    ROADMAP_COLUMNS,
    SLICE_BOARD_RESOURCE,
    SLICE_BOARD_SCHEMA,
    SLICE_BOARD_SLICE,
    USAGE,
    VERDICT_WORDS,
    BoardAction,
    BoardCard,
    BoardPanel,
    BoardVerdict,
    ColumnCount,
    SliceBoard,
    SliceBoardRegistry,
    action_plain_words,
    action_record,
    board_record,
    build_action,
    build_board,
    build_card,
    build_panel,
    build_row,
    build_verdict,
    card_from_roadmap_slice,
    card_record,
    cards_in_column,
    column_for_status,
    derive_panel,
    derive_verdict,
    effective_cards,
    format_action,
    format_board,
    format_card,
    format_panel,
    format_slice_board_screen,
    format_verdict,
    inspect_slice_source,
    line_of,
    load_slice_board,
    load_slice_board_file,
    normalize_action_kind,
    normalize_column,
    panel_plain_words,
    panel_record,
    parse_slice_board_args,
    plain_words,
    total_cards,
    validate_action,
    validate_board,
    validate_card,
    validate_panel,
    validate_row,
    validate_verdict,
    verdict_plain_words,
    verdict_record,
)
from mythic_agent.core.tui_redesign_charter import load_charter

ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_TITLE = "Slice Board at the M-172 slice boundary"

BY = "the coordinator"
HAND = "the jarl"
ON = "2026-11-09"


def _card(**overrides):
    fields = {
        "slice_id": "M-190",
        "position": 1,
        "part": 8,
        "title": "A test slice",
        "summary": "a test slice standing on the board for the tests.",
        "column": "queued",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_card(fields)


def _stored_card(card):
    stored = card.to_record()
    for key in ("type", "slice", "line"):
        stored.pop(key)
    return stored


def _action(**overrides):
    fields = {
        "action_id": "act-test",
        "seq": 1,
        "kind": "pause",
        "slice_id": "M-190",
        "detail": "held by hand for the tests.",
        "recorded_on": ON,
        "actor": HAND,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_action(fields)


def _stored_action(action):
    stored = action.to_record()
    for key in ("type", "slice"):
        stored.pop(key)
    return stored


def _board(cards=None, actions=(), **overrides):
    fields = {
        "title": "A test slice board",
        "cards": [_stored_card(item) for item in (
            cards if cards is not None else [_card()])],
        "actions": [_stored_action(item) for item in actions],
    }
    fields.update(overrides)
    return build_board(fields)


def _mixed_board():
    return _board(
        cards=[
            _card(),
            _card(slice_id="M-191", position=2,
                  title="A second test slice"),
            _card(slice_id="M-192", position=3, part=9,
                  title="A banked test slice", column="banked"),
        ],
        actions=[
            _action(action_id="act-open", seq=1, kind="advance",
                    target_column="building",
                    detail="the first slice opens by hand."),
            _action(action_id="act-hold", seq=2,
                    slice_id="M-191",
                    detail="the second slice waits by hand."),
        ])


# ---------------------------------------------------------------------
# The shipped example board, the roadmap and the charter.
# ---------------------------------------------------------------------


def test_shipped_board_loads_with_pinned_shape():
    board = load_slice_board()
    assert board.title == EXAMPLE_TITLE
    assert board.slice_ids() == (
        "M-171", "M-172", "M-173", "M-174",
        "M-175", "M-176", "M-177")
    first = board.cards[0]
    assert first.title == "The TUI redesign charter"
    assert first.column == "banked"
    assert board.action_ids() == (
        "act-open-m173", "act-pause-m175",
        "act-reorder-m176", "act-strike-m177")
    assert len(board.panels) == 1
    panel = board.panels[0]
    assert panel.panel_id == "panel-m172-boundary"
    assert panel.as_of == "2026-11-09"
    assert tuple(row.slice_id for row in panel.rows) == (
        "M-171", "M-172", "M-173", "M-176",
        "M-174", "M-175", "M-177")
    derived = derive_panel(board)
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_cards == derived.total_cards == 7
    assert (panel.total_queued, panel.total_building,
            panel.total_verifying, panel.total_banked) == (4, 1, 0, 2)
    assert (panel.total_paused, panel.total_struck) == (1, 1)
    assert panel.next_slice_id == "M-176"
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / SLICE_BOARD_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == SLICE_BOARD_SCHEMA
    assert raw["slice"] == "M-173"


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-173")]
    assert slice_.title == "The Slice Board"
    assert slice_.part == 8
    assert "visible board" in slice_.summary
    assert "re-order, pause, or strike" in slice_.summary
    assert SLICE_BOARD_SLICE == "M-173"


def test_charter_s03_names_m173():
    charter = load_charter()
    screen = charter.screen("main_chat")
    assert screen.id == "S-03"
    assert screen.verdict == "repair"
    assert "M-173" in screen.owning_slices
    assert screen.judgement("K-05").standing == "fails"
    assert "no queued, building, verifying or banked" in (
        screen.judgement("K-05").note)
    assert "visible slice board" in screen.direction


def test_closed_vocabularies():
    assert COLUMNS == ("queued", "building", "verifying", "banked")
    assert ACTION_KINDS == (
        "advance", "reorder", "pause", "resume", "strike")
    assert VERDICT_WORDS == ("complete", "flowing", "waiting")
    assert ROADMAP_COLUMNS == {"done": "banked", "queued": "queued"}
    assert normalize_column("queue") == "queued"
    assert normalize_column("done") == "banked"
    assert normalize_column("review") == "verifying"
    assert normalize_action_kind("re-order") == "reorder"
    assert normalize_action_kind("hold") == "pause"
    assert normalize_action_kind("cut") == "strike"
    with pytest.raises(ValueError):
        normalize_column("whenever")
    with pytest.raises(ValueError):
        normalize_action_kind("whenever")
    assert "visible board" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /sliceboard")


# ---------------------------------------------------------------------
# The card: judged whole, its line derived.
# ---------------------------------------------------------------------


def test_card_record_round_trips():
    card = _card()
    assert build_card(_stored_card(card)) == card
    assert card.to_record()["line"] == "M-190 A test slice - queued"
    assert card.to_record()["type"] == "slice_board_card"
    assert card.line == line_of(card)


def test_card_provenance_is_whole_and_required():
    card = _card()
    assert card.actor == BY
    assert card.origin_session == "session-test"
    for missing in ("slice_id", "position", "part", "title",
                    "summary", "column", "recorded_on", "actor",
                    "source", "origin_session"):
        fields = _stored_card(card)
        fields.pop(missing)
        with pytest.raises(ValueError):
            build_card(fields)


def test_card_refuses_unknown_keys_split_spellings_and_stored_line():
    fields = _stored_card(_card())
    fields["line"] = "M-190 A test slice - queued"
    with pytest.raises(ValueError):
        build_card(fields)
    fields = _stored_card(_card())
    fields["place"] = 99
    with pytest.raises(ValueError):
        build_card(fields)
    fields = _stored_card(_card())
    fields["surprise"] = "x"
    with pytest.raises(ValueError):
        build_card(fields)
    with pytest.raises(ValueError):
        _card(slice_id="X-190")
    with pytest.raises(ValueError):
        _card(part=12)
    with pytest.raises(ValueError):
        _card(position=0)


def test_card_alias_spellings_read_onto_the_fields():
    card = build_card({
        "id": "M-191", "place": 3, "part": 9,
        "title": "An alias slice",
        "summary": "an alias-spelled card for the tests.",
        "state": "done", "day": ON, "by": BY,
        "source": "alias source", "session": "session-alias"})
    assert card.column == "banked"
    assert card.position == 3
    assert card.slice_id == "M-191"


def test_line_is_derived_from_column_and_flags():
    assert line_of(_card()) == "M-190 A test slice - queued"
    assert line_of(_card(column="building")) == (
        "M-190 A test slice - building")
    assert line_of(_card(paused=True)) == (
        "M-190 A test slice - queued, paused")
    assert line_of(_card(struck=True)) == (
        "M-190 A test slice - queued, struck")
    assert line_of(_card(column="banked")) == (
        "M-190 A test slice - banked")


# ---------------------------------------------------------------------
# Composition: columns judged from the shipped road.
# ---------------------------------------------------------------------


def test_column_for_status_judges_the_shipped_road():
    assert column_for_status("done") == "banked"
    assert column_for_status("queued") == "queued"
    with pytest.raises(ValueError):
        column_for_status("building")
    with pytest.raises(ValueError):
        column_for_status(None)


def test_card_from_roadmap_slice_derives_its_column():
    roadmap = load_roadmap()
    by_id = {item.id: item for item in roadmap.slices}
    banked = card_from_roadmap_slice(by_id["M-171"], position=1)
    assert banked.column == "banked"
    assert banked.title == "The TUI redesign charter"
    queued = card_from_roadmap_slice(
        by_id["M-173"], position=3, column="queued")
    assert queued.column == "queued"
    with pytest.raises(ValueError):
        card_from_roadmap_slice(by_id["M-173"], position=3,
                                column="banked")
    ghost = SimpleNamespace(
        id="M-190", part=8, title="A ghost slice",
        summary="a slice the road does not know.", status="building")
    with pytest.raises(ValueError):
        card_from_roadmap_slice(ghost, position=1)


def test_inspect_slice_source_names_what_a_piece_is():
    found = inspect_slice_source({"id": "M-171", "status": "done"})
    assert found["column"] == "banked"
    assert found["slice_id"] == "M-171"
    assert inspect_slice_source({"words": "x"})["column"] is None
    assert inspect_slice_source("nope")["column"] is None
    unknown = inspect_slice_source({"id": "M-171", "status": "building"})
    assert unknown["column"] is None
    assert "no column stands judged" in unknown["reason"]


# ---------------------------------------------------------------------
# The action: one hand act, judged whole, stood on the board.
# ---------------------------------------------------------------------


def test_action_is_judged_whole_per_kind():
    advance = _action(kind="advance", target_column="building")
    assert advance.target_column == "building"
    with pytest.raises(ValueError):
        _action(kind="advance", target_column="banked")
    with pytest.raises(ValueError):
        _action(kind="advance")
    with pytest.raises(ValueError):
        _action(kind="advance", target_column="building",
                target_position=2)
    reorder = _action(kind="reorder", target_position=2)
    assert reorder.target_position == 2
    with pytest.raises(ValueError):
        _action(kind="reorder")
    with pytest.raises(ValueError):
        _action(kind="pause", target_position=2)
    with pytest.raises(ValueError):
        _action(kind="whenever")


def test_effective_board_stands_actions_in_order():
    board = _mixed_board()
    effective = board.effective_cards()
    assert [card.slice_id for card in effective] == [
        "M-190", "M-191", "M-192"]
    assert effective[0].column == "building"
    assert effective[1].paused is True
    assert effective[2].column == "banked"
    assert board.cards[0].column == "queued"
    stepped = _board(
        cards=[_card()],
        actions=[
            _action(action_id="act-one", seq=1, kind="advance",
                    target_column="building"),
            _action(action_id="act-two", seq=2, kind="advance",
                    target_column="verifying"),
        ])
    assert stepped.effective_cards()[0].column == "verifying"
    with pytest.raises(ValueError):
        _board(actions=[_action(kind="advance",
                                target_column="verifying")])
    with pytest.raises(ValueError):
        _board(
            cards=[_card(column="banked")],
            actions=[_action(kind="strike")])


def test_reorder_renumbers_the_board_contiguously():
    board = _board(
        cards=[
            _card(),
            _card(slice_id="M-191", position=2,
                  title="A second test slice"),
            _card(slice_id="M-192", position=3,
                  title="A third test slice"),
        ],
        actions=[_action(kind="reorder", slice_id="M-192",
                         target_position=1,
                         detail="the third slice moves first.")])
    effective = board.effective_cards()
    assert [card.slice_id for card in effective] == [
        "M-192", "M-190", "M-191"]
    assert [card.position for card in effective] == [1, 2, 3]


# ---------------------------------------------------------------------
# The panel and the verdict: derived, never chosen.
# ---------------------------------------------------------------------


def test_panel_is_derived_from_the_whole_board():
    board = _mixed_board()
    panel = derive_panel(board)
    assert panel.total_cards == 3
    assert (panel.total_queued, panel.total_building,
            panel.total_verifying, panel.total_banked) == (1, 1, 0, 1)
    assert (panel.total_paused, panel.total_struck) == (1, 0)
    assert panel.distinct_parts == 2
    assert panel.next_slice_id is None
    assert [row.slice_id for row in panel.rows] == [
        "M-190", "M-191", "M-192"]
    assert panel.rows[0].line == "M-190 A test slice - building"
    assert {c.column: c.items for c in panel.column_counts} == {
        "queued": 1, "building": 1, "banked": 1}


def test_panel_refuses_a_stored_panel_that_disagrees():
    board = _mixed_board()
    stored = derive_panel(board).to_record()
    stored.pop("type")
    stored.pop("slice")
    stored["total_queued"] = 3
    with pytest.raises(ValueError):
        validate_panel(stored, board)
    stored = derive_panel(board).to_record()
    stored.pop("type")
    stored.pop("slice")
    stored["rows"][0]["line"] = "a chosen line"
    with pytest.raises(ValueError):
        validate_panel(stored, board)
    panel = build_panel(derive_panel(board).to_record(), board)
    assert panel.total_cards == 3


def test_row_is_judged_against_its_card():
    card = _card()
    row = build_row(card=card)
    assert row.line == "M-190 A test slice - queued"
    assert validate_row(row.to_record(), card) == row
    bad = row.to_record()
    bad["line"] = "a chosen line"
    with pytest.raises(ValueError):
        validate_row(bad, card)


def test_verdict_bands_and_the_flowing_example():
    board = load_slice_board()
    verdict = derive_verdict(board)
    assert verdict.verdict == "flowing"
    assert verdict.total_building == 1
    done = _board(cards=[_card(column="banked")])
    assert derive_verdict(done).verdict == "complete"
    waiting = _board()
    assert derive_verdict(waiting).verdict == "waiting"
    mixed = derive_verdict(_mixed_board())
    assert mixed.verdict == "flowing"
    assert build_verdict(mixed.to_record(), _mixed_board()) == mixed
    with pytest.raises(ValueError):
        BoardVerdict(
            total_cards=1, total_queued=0, total_building=0,
            total_verifying=0, total_banked=1, total_paused=0,
            total_struck=0, distinct_parts=1,
            earliest_on=ON, latest_on=ON, verdict="waiting")
    with pytest.raises(ValueError):
        validate_verdict(mixed.to_record(), _board())


# ---------------------------------------------------------------------
# The board, the file loader and the registry.
# ---------------------------------------------------------------------


def test_board_laws_one_card_per_slice_and_actions_in_order():
    with pytest.raises(ValueError):
        _board(cards=[_card(), _card(position=2)])
    with pytest.raises(ValueError):
        _board(cards=[_card(), _card(slice_id="M-191")])
    with pytest.raises(ValueError):
        _board(cards=[_card(position=2),
                      _card(slice_id="M-191", position=1)])
    with pytest.raises(ValueError):
        _board(actions=[_action(), _action(action_id="act-two")])
    with pytest.raises(ValueError):
        _board(actions=[_action(),
                        _action(action_id="act-two", seq=2,
                                kind="strike"),
                        _action(seq=3, kind="resume",
                                detail="a second act-test id.")])
    board = _mixed_board()
    assert board.card_for("M-191").title == "A second test slice"
    assert board.effective_card("M-190").column == "building"
    assert board.action_for("act-open").kind == "advance"
    with pytest.raises(KeyError):
        board.card_for("M-199")
    with pytest.raises(KeyError):
        board.action_for("act-nope")
    assert total_cards(board) == 3
    assert [c.slice_id for c in cards_in_column(board, "banked")] == [
        "M-192"]
    assert [c.slice_id for c in cards_in_column(board, "done")] == [
        "M-192"]


def test_board_file_loader_reads_any_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "slice_board.yaml").read_text(encoding="utf-8")
    path = tmp_path / "slice_board.yaml"
    path.write_text(raw, encoding="utf-8")
    board = load_slice_board_file(path)
    assert board.title == EXAMPLE_TITLE
    assert total_cards(board) == 7


def test_registry_holds_cards_and_actions_one_by_one():
    registry = SliceBoardRegistry()
    registry.register_card(_card())
    registry.register_card(_card(
        slice_id="M-192", position=2, title="A banked test slice",
        column="banked"))
    held = registry.register_action(_action(action_id=None))
    assert held.action_id == "act-1"
    assert registry.get_card("M-190").paused is True
    assert registry.get_base_card("M-190").paused is False
    assert registry.latest_action().action_id == "act-1"
    assert registry.board().title == "Slice Board"
    assert registry.panel().total_cards == 2
    assert registry.verdict().verdict == "waiting"
    with pytest.raises(ValueError):
        registry.register_card(_card(position=3))
    with pytest.raises(ValueError):
        registry.register_card(_card(slice_id="M-193"))
    with pytest.raises(ValueError):
        registry.register_action(_action(
            action_id="act-banked", seq=2, kind="pause",
            slice_id="M-192"))
    assert [a.action_id for a in registry.list_actions()] == ["act-1"]
    with pytest.raises(KeyError):
        registry.get_card("M-199")


def test_registry_register_board_and_refusals():
    registry = SliceBoardRegistry()
    board = registry.register_board(_mixed_board())
    assert total_cards(board) == 3
    assert registry.title() == "A test slice board"
    with pytest.raises(ValueError):
        registry.register_board(_board())
    other = SliceBoardRegistry(_board())
    assert other.get_base_card("M-190").slice_id == "M-190"


# ---------------------------------------------------------------------
# News, plain words, formatters and the grammar.
# ---------------------------------------------------------------------


def test_news_records_carry_headlines():
    card = _card()
    news = card_record(card)
    assert news["news"] is True
    assert news["type"] == "slice_board_card"
    assert "M-190 A test slice - queued" in news["headline"]
    action_news = action_record(_action())
    assert action_news["type"] == "slice_board_action"
    assert "pause" in action_news["headline"]
    panel_news = panel_record(derive_panel(_mixed_board()))
    assert "Slice board panel" in panel_news["headline"]
    verdict_news = verdict_record(derive_verdict(_mixed_board()))
    assert "flowing" in verdict_news["headline"]
    board_news = board_record(_mixed_board())
    assert board_news["card_count"] == 3
    assert board_news["action_count"] == 2


def test_formatters_and_screen():
    board = load_slice_board()
    text = format_card(board.effective_card("M-173"))
    assert "M-173: M-173 The Slice Board - building" in text
    action_text = format_action(board.action_for("act-reorder-m176"))
    assert "act-reorder-m176: reorder M-176" in action_text
    assert "Target place: 4" in action_text
    listed = format_board(board)
    assert "M-171: M-171 The TUI redesign charter - banked" in listed
    queued = format_board(board, column="queued")
    assert "M-176" in queued
    assert "M-173" not in queued
    assert "Panel in Slice Board at the M-172 slice boundary" in (
        format_panel(board))
    assert format_verdict(board).startswith(
        "Verdict in The Slice Board over")
    assert "flowing" in format_verdict(board)
    screen = format_slice_board_screen()
    assert "The Slice Board (M-173)" in screen
    assert "next stands M-176" in screen
    assert "paused by hand" in plain_words(
        board.effective_card("M-175"))
    assert "moves this board" in action_plain_words(
        board.action_for("act-pause-m175")) or (
            "board alone" in action_plain_words(
                board.action_for("act-pause-m175")))
    assert "Slices, in board order" in panel_plain_words(board)
    assert "flowing" in verdict_plain_words(board)


def test_parse_slice_board_args_grammar():
    assert parse_slice_board_args("") == ("show", None)
    assert parse_slice_board_args(None) == ("show", None)
    assert parse_slice_board_args("show") == ("show", None)
    assert parse_slice_board_args("list") == ("show", None)
    assert parse_slice_board_args("card M-173") == ("card", "M-173")
    assert parse_slice_board_args("column done") == (
        "column", "banked")
    assert parse_slice_board_args("action act-open-m173") == (
        "action", "act-open-m173")
    assert parse_slice_board_args("panel") == ("panel", None)
    assert parse_slice_board_args("verdict") == ("verdict", None)
    for bad in ("card", "card X-173", "column whenever",
                "action", "panel now", "dance", 42):
        with pytest.raises(ValueError):
            parse_slice_board_args(bad)


def test_pure_layer_imports_no_agent_or_ui():
    text = (ROOT / "mythic_agent" / "core"
            / "slice_board.py").read_text(encoding="utf-8")
    assert "mythic_agent.agents" not in text
    assert "import textual" not in text
    assert "from ..agents" not in text
