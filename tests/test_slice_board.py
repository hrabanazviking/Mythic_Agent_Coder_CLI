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
        by_id["M-271"], position=3, column="queued")
    assert queued.column == "queued"
    with pytest.raises(ValueError):
        card_from_roadmap_slice(by_id["M-271"], position=3,
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
        board.card_for("M-271")
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
        registry.get_card("M-271")


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


# -- agent layer -----------------------------------------------------------
#
# M-173 agent layer: the agent holds a
# SliceBoardRegistry for the session (session
# state only, no new setting), cards and hand
# actions are held by being registered - each
# judged whole, and each action judged against
# the board it lands on, before it is held -
# published as their card_record / action_record
# session news through the checkpoint road,
# deduped per shape - a card composed from the
# shipped roadmap by import takes its column
# from the slice's own ledger status, the
# hand-action road composes one action at the
# held board's next sequence and publishes the
# derived panel and verdict news with it,
# whole-board register and record roads hold a
# board judged whole first, the report road
# renders the held board (or the shipped example
# when unheld) through the pure formatters, and
# the /sliceboard surface rides both roads on
# the pure parser + formatters. Status, get,
# base-get, column, panel, verdict and report
# reads register and publish nothing, answer
# from the held registry first and from the
# shipped example only while nothing is held -
# a held card never falls back to the example.
# The panel and the verdict derive at call time
# from the whole board, never held. This layer
# sends nothing, posts nothing, schedules
# nothing, calls no model, persists nothing
# beyond the session journal news, runs no build
# and banks nothing - a card held here is a
# record of a plan, never the work itself, and
# a hand action moves the held board alone,
# never the shipped roadmap.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _board_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_board_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "slice_board.yaml").read_text(encoding="utf-8")
    path = tmp_path / "slice_board.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestSliceBoardAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.slice_board_status()
        assert status["cards"] == []
        assert status["actions"] == []
        assert status["board"] is None
        assert status["slice_board"]["title"] == EXAMPLE_TITLE
        assert len(status["slice_board"]["cards"]) == 7
        assert len(status["slice_board"]["actions"]) == 4
        assert status["panel"]["total_cards"] == 7
        assert status["panel"]["total_building"] == 1
        assert status["panel"]["next_slice_id"] == "M-176"
        assert status["panels"][0]["panel_id"] == "panel-m172-boundary"
        assert status["board_record"]["card_count"] == 7
        assert status["board_record"]["action_count"] == 4
        assert status["verdict"]["verdict"] == "flowing"
        assert "M-177 Prompt craft - queued, struck" in (
            status["plain_words"])
        assert "struck by hand" in status["plain_words"]
        assert "The Slice Board (M-173)" in status["screen"]
        assert "next stands M-176" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._slice_board_registry()
        assert agent._slice_board_registry() is first
        assert agent._slice_board_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.slice_board_status()
        assert agent.get_slice_board_card("M-173").column == "building"
        assert agent.get_slice_board_base_card(
            "M-173").column == "queued"
        assert agent.get_slice_board_action(
            "act-open-m173").kind == "advance"
        assert [c.slice_id for c in agent.slice_board_cards_in_column(
            "queued")] == ["M-176", "M-174", "M-175", "M-177"]
        agent.slice_board_panel()
        agent.slice_board_verdict()
        agent.report_slice_board()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("slice_board")] == []
        with pytest.raises(KeyError):
            agent.get_slice_board_card("M-999")
        with pytest.raises(KeyError):
            agent.get_slice_board_action("act-nope")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_slice_board_card(_card())
        status = agent.slice_board_status()
        assert [item["slice_id"] for item in status["cards"]] == [
            "M-190"]
        assert status["board"]["title"] == "Slice Board"
        assert status["panel"]["total_cards"] == 1
        assert status["panel"]["next_slice_id"] == "M-190"
        assert status["verdict"]["verdict"] == "waiting"

    def test_held_card_never_falls_back_to_the_example(
            self, agent):
        agent.register_slice_board_card(_card())
        with pytest.raises(KeyError):
            agent.get_slice_board_card("M-171")
        with pytest.raises(KeyError):
            agent.get_slice_board_action("act-open-m173")
        card = agent.get_slice_board_card("M-190")
        assert card.title == "A test slice"
        assert agent.slice_board_board().title == "Slice Board"


class TestSliceBoardAgentHolding:
    def test_register_card_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_slice_board_card(_card())
        assert outcome["card"]["slice_id"] == "M-190"
        assert outcome["record_news"]["news"] is True
        assert outcome["record_news"]["type"] == "slice_board_card"
        assert "M-190" in outcome["screen"]
        agent.register_slice_board_card(_card(
            slice_id="M-191", position=2,
            title="A second test slice"))
        events = _board_events(store, session_id, "slice_board_card")
        assert len(events) == 2
        agent._publish_slice_board_record(card_record(_card()))
        agent._publish_slice_board_record(
            {"type": "work_view_event", "news": True})
        events = _board_events(store, session_id, "slice_board_card")
        assert len(events) == 2
        agent.close()

    def test_duplicate_card_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_slice_board_card(_card())
        with pytest.raises(ValueError):
            agent.register_slice_board_card(_card())
        with pytest.raises(ValueError):
            agent.register_slice_board_card(_card(position=2))
        with pytest.raises(ValueError):
            agent.register_slice_board_card(
                _card(slice_id="M-191"))
        events = _board_events(store, session_id, "slice_board_card")
        assert len(events) == 1
        agent.close()

    def test_roadmap_card_composes_by_import_and_holds(
            self, agent):
        roadmap = load_roadmap()
        by_id = {item.id: item for item in roadmap.slices}
        card = card_from_roadmap_slice(by_id["M-229"], position=1)
        assert card.column == "queued"
        assert card.title == "The method, teachable"
        with pytest.raises(ValueError):
            card_from_roadmap_slice(
                by_id["M-229"], position=1, column="banked")
        outcome = agent.register_slice_board_card(card)
        assert outcome["card"]["column"] == "queued"
        banked = card_from_roadmap_slice(by_id["M-171"], position=2)
        assert banked.column == "banked"
        agent.register_slice_board_card(banked)
        assert [c.slice_id for c in agent.slice_board_cards_in_column(
            "banked")] == ["M-171"]

    def test_register_action_is_judged_against_its_board(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_slice_board_card(_card())
        agent.register_slice_board_card(_card(
            slice_id="M-192", position=2,
            title="A banked test slice", column="banked"))
        outcome = agent.register_slice_board_action(_action())
        assert outcome["action"]["action_id"] == "act-test"
        assert outcome["record_news"]["type"] == "slice_board_action"
        assert agent.get_slice_board_card("M-190").paused is True
        assert agent.get_slice_board_base_card(
            "M-190").paused is False
        with pytest.raises(ValueError):
            agent.register_slice_board_action(_action(
                action_id="act-bad", seq=2, slice_id="M-192"))
        assert [a.action_id for a in
                agent._slice_board_registry().list_actions()] == [
                    "act-test"]
        events = _board_events(store, session_id, "slice_board_action")
        assert len(events) == 1
        agent.close()

    def test_hand_action_road_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_slice_board_card(_card())
        agent.register_slice_board_card(_card(
            slice_id="M-191", position=2,
            title="A second test slice"))
        outcome = agent.apply_slice_board_action(
            "advance", slice_id="M-190",
            detail="the first slice opens by hand.",
            target_column="building")
        assert outcome["kind"] == "advance"
        assert outcome["action"]["seq"] == 1
        assert outcome["action"]["action_id"] == "act-1"
        assert outcome["record_news"]["type"] == "slice_board_action"
        assert outcome["panel_record"]["type"] == "slice_board_panel"
        assert outcome["verdict_record"]["type"] == (
            "slice_board_verdict")
        assert agent.get_slice_board_card("M-190").column == "building"
        assert agent.get_slice_board_base_card(
            "M-190").column == "queued"
        second = agent.apply_slice_board_action(
            "pause", slice_id="M-191",
            detail="the second slice waits by hand.")
        assert second["action"]["seq"] == 2
        assert agent.get_slice_board_card("M-191").paused is True
        assert len(_board_events(
            store, session_id, "slice_board_action")) == 2
        assert len(_board_events(
            store, session_id, "slice_board_panel")) == 1
        assert len(_board_events(
            store, session_id, "slice_board_verdict")) == 1
        agent.close()

    def test_hand_action_road_refuses_an_illegal_act(self, agent):
        agent.register_slice_board_card(_card())
        agent.apply_slice_board_action(
            "pause", slice_id="M-190",
            detail="the slice waits by hand.")
        with pytest.raises(ValueError):
            agent.apply_slice_board_action(
                "advance", slice_id="M-190",
                detail="a paused slice cannot move.",
                target_column="building")
        with pytest.raises(ValueError):
            agent.apply_slice_board_action(
                "advance", slice_id="M-190",
                detail="banking is never a hand act.",
                target_column="banked")
        assert [a.kind for a in
                agent._slice_board_registry().list_actions()] == [
                    "pause"]
        assert agent.get_slice_board_card("M-190").column == "queued"

    def test_register_board_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_slice_board_board(_mixed_board())
        assert outcome["count"] == 3
        assert [c["slice_id"] for c in outcome["cards"]] == [
            "M-190", "M-191", "M-192"]
        assert [r["type"] for r in outcome["records_news"]] == [
            "slice_board_card", "slice_board_card",
            "slice_board_card", "slice_board_action",
            "slice_board_action"]
        events = _board_events(store, session_id, "slice_board_card")
        assert [e["slice_id"] for e in events] == [
            "M-190", "M-191", "M-192"]
        assert len(_board_events(
            store, session_id, "slice_board_panel")) == 1
        assert agent.slice_board_board().title == "A test slice board"
        with pytest.raises(ValueError):
            agent.register_slice_board_board(_mixed_board())
        agent.close()

    def test_record_board_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_slice_board_board()
        assert outcome["count"] == 7
        assert outcome["board"]["title"] == EXAMPLE_TITLE
        assert len(_board_events(
            store, session_id, "slice_board_card")) == 7
        assert len(_board_events(
            store, session_id, "slice_board_action")) == 4
        status = agent.slice_board_status()
        assert status["panels"][0]["panel_id"] == "panel-m172-boundary"
        with pytest.raises(ValueError):
            agent.record_slice_board_board()
        agent.close()

    def test_board_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_board_file(tmp_path)
        board = load_slice_board_file(path)
        outcome = agent.record_slice_board_board(board)
        assert outcome["count"] == 7
        assert agent.slice_board_board().title == EXAMPLE_TITLE

    def test_report_renders_example_then_held_board_only(self, agent):
        report = agent.report_slice_board()
        assert report["board"]["title"] == EXAMPLE_TITLE
        assert len(report["cards"]) == 7
        assert report["verdict"]["verdict"] == "flowing"
        assert "M-173 The Slice Board - building" in (
            report["board_text"])
        agent.register_slice_board_card(_card())
        report = agent.report_slice_board()
        assert [c["slice_id"] for c in report["cards"]] == ["M-190"]
        assert "M-190 A test slice - queued" in report["board_text"]
        assert report["verdict"]["verdict"] == "waiting"

    def test_holding_and_hand_actions_run_no_build(self, agent):
        for name in (
                "run_slice_board_build", "execute_slice_board",
                "bank_slice_board", "build_slice_board_slice",
                "persist_slice_board", "send_slice_board",
                "schedule_slice_board", "sync_slice_board",
                "delete_slice_board_card", "rewrite_roadmap"):
            assert not hasattr(agent, name), name
        before = {item.id: item.status
                  for item in load_roadmap().slices}
        agent.register_slice_board_card(_card(
            slice_id="M-229", title="The method, teachable"))
        agent.apply_slice_board_action(
            "strike", slice_id="M-229",
            detail="struck by hand for the tests.")
        assert agent.get_slice_board_card("M-229").struck is True
        after = {item.id: item.status
                 for item in load_roadmap().slices}
        assert after == before
        assert after["M-229"] == "queued"


class TestSliceBoardTerminalSurface:
    def test_show_card_column_action_panel_verdict(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/sliceboard")
        assert "The Slice Board (M-173)" in text
        _, _, text = _slash(agent, "/sliceboard card M-173")
        assert "M-173 The Slice Board - building" in text
        _, _, text = _slash(agent, "/sliceboard column queued")
        assert "M-176" in text
        assert "M-173" not in text
        _, _, text = _slash(agent, "/sliceboard column done")
        assert "M-171" in text
        assert "M-176" not in text
        _, _, text = _slash(
            agent, "/sliceboard action act-reorder-m176")
        assert "reorder M-176" in text
        assert "Target place: 4" in text
        _, _, text = _slash(agent, "/sliceboard panel")
        assert "Panel in Slice Board at the M-172 slice boundary" in (
            text)
        _, _, text = _slash(agent, "/sliceboard verdict")
        assert "flowing" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/sliceboard [show|card <slice-id>"
                "|column <column>|action <action-id>"
                "|panel|verdict]") in text
        _, _, text = _slash(agent, "/sliceboard dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/sliceboard card M-999")
        assert "no card named" in text


@pytest.fixture()
def board_handler(agent, monkeypatch):
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


def _board_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestSliceBoardCommand:
    def test_show_is_default(self, board_handler, agent):
        board_handler._handle_sliceboard("")
        assert "The Slice Board (M-173)" in (
            _board_published_text(board_handler))

    def test_card_column_action_panel_verdict(
            self, board_handler, agent):
        board_handler._handle_sliceboard("card M-173")
        assert "M-173 The Slice Board - building" in (
            _board_published_text(board_handler))
        board_handler._handle_sliceboard("column queued")
        assert "M-176" in _board_published_text(board_handler)
        board_handler._handle_sliceboard("action act-open-m173")
        assert "advance M-173" in _board_published_text(board_handler)
        board_handler._handle_sliceboard("panel")
        assert "Panel in Slice Board" in (
            _board_published_text(board_handler))
        board_handler._handle_sliceboard("verdict")
        assert "flowing" in _board_published_text(board_handler)

    def test_bad_grammar_is_published(
            self, board_handler, agent):
        board_handler._handle_sliceboard("dance party")
        assert USAGE in _board_published_text(board_handler)
        board_handler._handle_sliceboard("card M-999")
        assert "no card named" in _board_published_text(
            board_handler)


class TestChatScreenRoutingSliceBoard:
    def test_sliceboard_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/sliceboard panel", _FakeLog())
        assert calls == [("/sliceboard", "panel")]

    def test_chat_screen_help_and_usage_name_the_board(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/sliceboard[/green] - show the slice board (M-173)" in (
            text)
        assert ('"/sliceboard": "Usage: /sliceboard | '
                '/sliceboard card <slice-id>') in text


# -- agent layer -----------------------------------------------------------
#
# M-173 agent layer: the agent holds a
# SliceBoardRegistry for the session (session
# state only, no new setting), cards and hand
# actions are held by being registered - each
# judged whole, and each action judged against
# the board it lands on, before it is held -
# published as their card_record / action_record
# session news through the checkpoint road,
# deduped per shape - a card composed from the
# shipped roadmap by import takes its column
# from the slice's own ledger status, the
# hand-action road composes one action at the
# held board's next sequence and publishes the
# derived panel and verdict news with it,
# whole-board register and record roads hold a
# board judged whole first, the report road
# renders the held board (or the shipped example
# when unheld) through the pure formatters, and
# the /sliceboard surface rides both roads on
# the pure parser + formatters. Status, get,
# base-get, column, panel, verdict and report
# reads register and publish nothing, answer
# from the held registry first and from the
# shipped example only while nothing is held -
# a held card never falls back to the example.
# The panel and the verdict derive at call time
# from the whole board, never held. This layer
# sends nothing, posts nothing, schedules
# nothing, calls no model, persists nothing
# beyond the session journal news, runs no build
# and banks nothing - a card held here is a
# record of a plan, never the work itself, and
# a hand action moves the held board alone,
# never the shipped roadmap.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _board_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_board_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "slice_board.yaml").read_text(encoding="utf-8")
    path = tmp_path / "slice_board.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestSliceBoardAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.slice_board_status()
        assert status["cards"] == []
        assert status["actions"] == []
        assert status["board"] is None
        assert status["slice_board"]["title"] == EXAMPLE_TITLE
        assert len(status["slice_board"]["cards"]) == 7
        assert len(status["slice_board"]["actions"]) == 4
        assert status["panel"]["total_cards"] == 7
        assert status["panel"]["total_building"] == 1
        assert status["panel"]["next_slice_id"] == "M-176"
        assert status["panels"][0]["panel_id"] == "panel-m172-boundary"
        assert status["board_record"]["card_count"] == 7
        assert status["board_record"]["action_count"] == 4
        assert status["verdict"]["verdict"] == "flowing"
        assert "M-177 Prompt craft - queued, struck" in (
            status["plain_words"])
        assert "struck by hand" in status["plain_words"]
        assert "The Slice Board (M-173)" in status["screen"]
        assert "next stands M-176" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._slice_board_registry()
        assert agent._slice_board_registry() is first
        assert agent._slice_board_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.slice_board_status()
        assert agent.get_slice_board_card("M-173").column == "building"
        assert agent.get_slice_board_base_card(
            "M-173").column == "queued"
        assert agent.get_slice_board_action(
            "act-open-m173").kind == "advance"
        assert [c.slice_id for c in agent.slice_board_cards_in_column(
            "queued")] == ["M-176", "M-174", "M-175", "M-177"]
        agent.slice_board_panel()
        agent.slice_board_verdict()
        agent.report_slice_board()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("slice_board")] == []
        with pytest.raises(KeyError):
            agent.get_slice_board_card("M-999")
        with pytest.raises(KeyError):
            agent.get_slice_board_action("act-nope")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_slice_board_card(_card())
        status = agent.slice_board_status()
        assert [item["slice_id"] for item in status["cards"]] == [
            "M-190"]
        assert status["board"]["title"] == "Slice Board"
        assert status["panel"]["total_cards"] == 1
        assert status["panel"]["next_slice_id"] == "M-190"
        assert status["verdict"]["verdict"] == "waiting"

    def test_held_card_never_falls_back_to_the_example(
            self, agent):
        agent.register_slice_board_card(_card())
        with pytest.raises(KeyError):
            agent.get_slice_board_card("M-171")
        with pytest.raises(KeyError):
            agent.get_slice_board_action("act-open-m173")
        card = agent.get_slice_board_card("M-190")
        assert card.title == "A test slice"
        assert agent.slice_board_board().title == "Slice Board"


class TestSliceBoardAgentHolding:
    def test_register_card_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_slice_board_card(_card())
        assert outcome["card"]["slice_id"] == "M-190"
        assert outcome["record_news"]["news"] is True
        assert outcome["record_news"]["type"] == "slice_board_card"
        assert "M-190" in outcome["screen"]
        agent.register_slice_board_card(_card(
            slice_id="M-191", position=2,
            title="A second test slice"))
        events = _board_events(store, session_id, "slice_board_card")
        assert len(events) == 2
        agent._publish_slice_board_record(card_record(_card()))
        agent._publish_slice_board_record(
            {"type": "work_view_event", "news": True})
        events = _board_events(store, session_id, "slice_board_card")
        assert len(events) == 2
        agent.close()

    def test_duplicate_card_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_slice_board_card(_card())
        with pytest.raises(ValueError):
            agent.register_slice_board_card(_card())
        with pytest.raises(ValueError):
            agent.register_slice_board_card(_card(position=2))
        with pytest.raises(ValueError):
            agent.register_slice_board_card(
                _card(slice_id="M-191"))
        events = _board_events(store, session_id, "slice_board_card")
        assert len(events) == 1
        agent.close()

    def test_roadmap_card_composes_by_import_and_holds(
            self, agent):
        roadmap = load_roadmap()
        by_id = {item.id: item for item in roadmap.slices}
        card = card_from_roadmap_slice(by_id["M-271"], position=1)
        assert card.column == "queued"
        assert card.title == "Retro and lessons"
        with pytest.raises(ValueError):
            card_from_roadmap_slice(
                by_id["M-271"], position=1, column="banked")
        outcome = agent.register_slice_board_card(card)
        assert outcome["card"]["column"] == "queued"
        banked = card_from_roadmap_slice(by_id["M-171"], position=2)
        assert banked.column == "banked"
        agent.register_slice_board_card(banked)
        assert [c.slice_id for c in agent.slice_board_cards_in_column(
            "banked")] == ["M-171"]

    def test_register_action_is_judged_against_its_board(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_slice_board_card(_card())
        agent.register_slice_board_card(_card(
            slice_id="M-192", position=2,
            title="A banked test slice", column="banked"))
        outcome = agent.register_slice_board_action(_action())
        assert outcome["action"]["action_id"] == "act-test"
        assert outcome["record_news"]["type"] == "slice_board_action"
        assert agent.get_slice_board_card("M-190").paused is True
        assert agent.get_slice_board_base_card(
            "M-190").paused is False
        with pytest.raises(ValueError):
            agent.register_slice_board_action(_action(
                action_id="act-bad", seq=2, slice_id="M-192"))
        assert [a.action_id for a in
                agent._slice_board_registry().list_actions()] == [
                    "act-test"]
        events = _board_events(store, session_id, "slice_board_action")
        assert len(events) == 1
        agent.close()

    def test_hand_action_road_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_slice_board_card(_card())
        agent.register_slice_board_card(_card(
            slice_id="M-191", position=2,
            title="A second test slice"))
        outcome = agent.apply_slice_board_action(
            "advance", slice_id="M-190",
            detail="the first slice opens by hand.",
            target_column="building")
        assert outcome["kind"] == "advance"
        assert outcome["action"]["seq"] == 1
        assert outcome["action"]["action_id"] == "act-1"
        assert outcome["record_news"]["type"] == "slice_board_action"
        assert outcome["panel_record"]["type"] == "slice_board_panel"
        assert outcome["verdict_record"]["type"] == (
            "slice_board_verdict")
        assert agent.get_slice_board_card("M-190").column == "building"
        assert agent.get_slice_board_base_card(
            "M-190").column == "queued"
        second = agent.apply_slice_board_action(
            "pause", slice_id="M-191",
            detail="the second slice waits by hand.")
        assert second["action"]["seq"] == 2
        assert agent.get_slice_board_card("M-191").paused is True
        assert len(_board_events(
            store, session_id, "slice_board_action")) == 2
        assert len(_board_events(
            store, session_id, "slice_board_panel")) == 1
        assert len(_board_events(
            store, session_id, "slice_board_verdict")) == 1
        agent.close()

    def test_hand_action_road_refuses_an_illegal_act(self, agent):
        agent.register_slice_board_card(_card())
        agent.apply_slice_board_action(
            "pause", slice_id="M-190",
            detail="the slice waits by hand.")
        with pytest.raises(ValueError):
            agent.apply_slice_board_action(
                "advance", slice_id="M-190",
                detail="a paused slice cannot move.",
                target_column="building")
        with pytest.raises(ValueError):
            agent.apply_slice_board_action(
                "advance", slice_id="M-190",
                detail="banking is never a hand act.",
                target_column="banked")
        assert [a.kind for a in
                agent._slice_board_registry().list_actions()] == [
                    "pause"]
        assert agent.get_slice_board_card("M-190").column == "queued"

    def test_register_board_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_slice_board_board(_mixed_board())
        assert outcome["count"] == 3
        assert [c["slice_id"] for c in outcome["cards"]] == [
            "M-190", "M-191", "M-192"]
        assert [r["type"] for r in outcome["records_news"]] == [
            "slice_board_card", "slice_board_card",
            "slice_board_card", "slice_board_action",
            "slice_board_action"]
        events = _board_events(store, session_id, "slice_board_card")
        assert [e["slice_id"] for e in events] == [
            "M-190", "M-191", "M-192"]
        assert len(_board_events(
            store, session_id, "slice_board_panel")) == 1
        assert agent.slice_board_board().title == "A test slice board"
        with pytest.raises(ValueError):
            agent.register_slice_board_board(_mixed_board())
        agent.close()

    def test_record_board_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_slice_board_board()
        assert outcome["count"] == 7
        assert outcome["board"]["title"] == EXAMPLE_TITLE
        assert len(_board_events(
            store, session_id, "slice_board_card")) == 7
        assert len(_board_events(
            store, session_id, "slice_board_action")) == 4
        status = agent.slice_board_status()
        assert status["panels"][0]["panel_id"] == "panel-m172-boundary"
        with pytest.raises(ValueError):
            agent.record_slice_board_board()
        agent.close()

    def test_board_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_board_file(tmp_path)
        board = load_slice_board_file(path)
        outcome = agent.record_slice_board_board(board)
        assert outcome["count"] == 7
        assert agent.slice_board_board().title == EXAMPLE_TITLE

    def test_report_renders_example_then_held_board_only(self, agent):
        report = agent.report_slice_board()
        assert report["board"]["title"] == EXAMPLE_TITLE
        assert len(report["cards"]) == 7
        assert report["verdict"]["verdict"] == "flowing"
        assert "M-173 The Slice Board - building" in (
            report["board_text"])
        agent.register_slice_board_card(_card())
        report = agent.report_slice_board()
        assert [c["slice_id"] for c in report["cards"]] == ["M-190"]
        assert "M-190 A test slice - queued" in report["board_text"]
        assert report["verdict"]["verdict"] == "waiting"

    def test_holding_and_hand_actions_run_no_build(self, agent):
        for name in (
                "run_slice_board_build", "execute_slice_board",
                "bank_slice_board", "build_slice_board_slice",
                "persist_slice_board", "send_slice_board",
                "schedule_slice_board", "sync_slice_board",
                "delete_slice_board_card", "rewrite_roadmap"):
            assert not hasattr(agent, name), name
        before = {item.id: item.status
                  for item in load_roadmap().slices}
        agent.register_slice_board_card(_card(
            slice_id="M-271", title="Retro and lessons"))
        agent.apply_slice_board_action(
            "strike", slice_id="M-271",
            detail="struck by hand for the tests.")
        assert agent.get_slice_board_card("M-271").struck is True
        after = {item.id: item.status
                 for item in load_roadmap().slices}
        assert after == before
        assert after["M-271"] == "queued"


class TestSliceBoardTerminalSurface:
    def test_show_card_column_action_panel_verdict(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/sliceboard")
        assert "The Slice Board (M-173)" in text
        _, _, text = _slash(agent, "/sliceboard card M-173")
        assert "M-173 The Slice Board - building" in text
        _, _, text = _slash(agent, "/sliceboard column queued")
        assert "M-176" in text
        assert "M-173" not in text
        _, _, text = _slash(agent, "/sliceboard column done")
        assert "M-171" in text
        assert "M-176" not in text
        _, _, text = _slash(
            agent, "/sliceboard action act-reorder-m176")
        assert "reorder M-176" in text
        assert "Target place: 4" in text
        _, _, text = _slash(agent, "/sliceboard panel")
        assert "Panel in Slice Board at the M-172 slice boundary" in (
            text)
        _, _, text = _slash(agent, "/sliceboard verdict")
        assert "flowing" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/sliceboard [show|card <slice-id>"
                "|column <column>|action <action-id>"
                "|panel|verdict]") in text
        _, _, text = _slash(agent, "/sliceboard dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/sliceboard card M-999")
        assert "no card named" in text


@pytest.fixture()
def board_handler(agent, monkeypatch):
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


def _board_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestSliceBoardCommand:
    def test_show_is_default(self, board_handler, agent):
        board_handler._handle_sliceboard("")
        assert "The Slice Board (M-173)" in (
            _board_published_text(board_handler))

    def test_card_column_action_panel_verdict(
            self, board_handler, agent):
        board_handler._handle_sliceboard("card M-173")
        assert "M-173 The Slice Board - building" in (
            _board_published_text(board_handler))
        board_handler._handle_sliceboard("column queued")
        assert "M-176" in _board_published_text(board_handler)
        board_handler._handle_sliceboard("action act-open-m173")
        assert "advance M-173" in _board_published_text(board_handler)
        board_handler._handle_sliceboard("panel")
        assert "Panel in Slice Board" in (
            _board_published_text(board_handler))
        board_handler._handle_sliceboard("verdict")
        assert "flowing" in _board_published_text(board_handler)

    def test_bad_grammar_is_published(
            self, board_handler, agent):
        board_handler._handle_sliceboard("dance party")
        assert USAGE in _board_published_text(board_handler)
        board_handler._handle_sliceboard("card M-999")
        assert "no card named" in _board_published_text(
            board_handler)


class TestChatScreenRoutingSliceBoard:
    def test_sliceboard_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/sliceboard panel", _FakeLog())
        assert calls == [("/sliceboard", "panel")]

    def test_chat_screen_help_and_usage_name_the_board(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/sliceboard[/green] - show the slice board (M-173)" in (
            text)
        assert ('"/sliceboard": "Usage: /sliceboard | '
                '/sliceboard card <slice-id>') in text
