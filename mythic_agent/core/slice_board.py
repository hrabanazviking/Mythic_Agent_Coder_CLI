"""The Slice Board (All-Features roadmap slice M-173).

Part VIII - The Beautiful Face - builds here. The
roadmap's words: *plans and roadmaps as a visible
board (queued / building / verifying / banked) -
the Mythic way of working *seen*; the human can
re-order, pause, or strike a slice by hand.*

What already ships, and what this slice adds:

* The shipped roadmap data layer (M-017,
  ``core/roadmap_slices.py``) holds the road as
  data - 272 slices, each done or queued - but
  nothing showed that road as a working board,
  and the M-171 TUI redesign charter judged the
  main chat screen (its S-03 row) REPAIR on
  exactly that count: its K-05 judgement fails
  because *no queued, building, verifying or
  banked slices are visible at any moment*, and
  its direction names M-173 as an owning slice:
  *show long jobs as a visible slice board*. The
  terminal loop's S-08 row notes the same absence
  (a long job is a flow, never a board) but names
  other owning slices, so this slice honours the
  one charter row that names it.
* This slice is that board, as a pure layer: one
  board card validated as data WITH ITS
  PROVENANCE WHOLE - the slice it stands for,
  named by its slice id alone on the board; its
  place on the board; its part, its title and its
  summary in the roadmap's own words; its column
  in the closed column set - queued, building,
  verifying or banked; whether a hand has paused
  or struck it - and the day it was recorded, who
  recorded it, its source and the session it was
  recorded in. A card composed from the shipped
  roadmap BY IMPORT takes its column from the
  slice's own ledger status: done reads banked,
  queued reads queued. What the human does by
  hand is held as its own record - one board
  action, judged whole: its kind in the closed
  action set (advance, re-order, pause, resume,
  strike), the slice it touches, its own words
  for why, and its provenance whole. The
  EFFECTIVE board is DERIVED by standing the
  held actions, in their recorded order, on the
  held cards: the panel is derived from the
  effective board (its rows the cards in board
  order carrying their derived board lines, its
  totals the cards' own counts, its next slice
  the first queued card no hand has paused or
  struck), and a board VERDICT is derived for
  the whole board. The shipped data file
  (``mythic_agent/data/slice_board.yaml``) holds
  one example board in exactly the shape a real
  board file takes, a loader reads a board file
  anywhere on disk, cards and actions are shaped
  as session news, and a small in-memory registry
  model holds cards and actions one by one. The
  agent layer owns holding a board for a session
  and standing a hand action on it.

Honesty rules, enforced here and pinned by tests:

* **The board line is derived, never chosen.**
  A card's line is read off its slice id, its
  title, its column and its paused/struck flags
  alone. A stored line naming anything else
  refuses, and no field of a card may smuggle a
  chosen line in.
* **Columns are judged from the shipped road.**
  A card raised over a roadmap slice takes its
  column from the slice's own ledger status,
  read onto the closed column set; a status the
  set does not know refuses plainly rather than
  inventing a column. Building and verifying are
  reached only by a held advance action standing
  on a queued or building card - never by a
  stored word alone at the composition road.
* **Hand actions are records, not rewrites.**
  Re-ordering, pausing or striking on the held
  board moves THIS board alone: no hand action
  held here rewrites the shipped roadmap data,
  re-sequences the road, banks a slice or
  deletes one. A struck slice still stands on
  the board, struck - the strike is seen, not
  hidden - and banking stays the coordinator's
  road on the shipped ledger, not this layer's.
* **The board stands in order.** A board holds
  its cards in board order - positions strictly
  ascending, one card per slice and per
  position - and its actions in recorded order,
  one action per sequence, so the board can
  never fork or run backwards. A re-order
  renumbers the board contiguously, first card
  first, so two panels of one board diff cleanly.
* **Data only.** This layer holds plans as
  data: it runs no build, banks nothing, sends
  nothing, posts nothing, schedules nothing,
  calls no model and persists nothing - a card
  held here is a record of a plan, never the
  work itself.
"""

from __future__ import annotations

__all__ = [
    "ACTION_KINDS",
    "COLUMNS",
    "PLAIN_EXPLANATION",
    "ROADMAP_COLUMNS",
    "SLICE_BOARD_RESOURCE",
    "SLICE_BOARD_SCHEMA",
    "SLICE_BOARD_SLICE",
    "THE_SLICE_BOARD_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "Any",
    "BoardAction",
    "BoardCard",
    "BoardPanel",
    "BoardPanelRow",
    "BoardVerdict",
    "ColumnCount",
    "Dict",
    "List",
    "Optional",
    "SliceBoard",
    "SliceBoardRegistry",
    "Tuple",
    "action_record",
    "board_record",
    "build_action",
    "build_board",
    "build_card",
    "build_panel",
    "build_row",
    "build_verdict",
    "card_from_roadmap_slice",
    "card_record",
    "cards_in_column",
    "column_for_status",
    "derive_panel",
    "derive_verdict",
    "effective_cards",
    "format_action",
    "format_board",
    "format_card",
    "format_panel",
    "format_slice_board_screen",
    "format_verdict",
    "inspect_slice_source",
    "line_of",
    "load_slice_board",
    "load_slice_board_file",
    "normalize_action_kind",
    "normalize_column",
    "panel_plain_words",
    "panel_record",
    "parse_slice_board_args",
    "plain_words",
    "action_plain_words",
    "total_cards",
    "validate_action",
    "validate_board",
    "validate_card",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "verdict_plain_words",
    "verdict_record",
]

import re
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .validation import ValidationError

SLICE_BOARD_SLICE = "M-173"

#: The longer name other layers cite for this slice.
THE_SLICE_BOARD_SLICE = SLICE_BOARD_SLICE

SLICE_BOARD_RESOURCE = "slice_board.yaml"

SLICE_BOARD_SCHEMA = "mythic.slice_board/1"

#: The columns one slice may stand in, in board
#: order: waiting, being built, being proven,
#: banked. The roadmap's own four words.
COLUMNS = ("queued", "building", "verifying", "banked")

_COLUMN_ALIASES = {
    "queued": "queued", "queue": "queued",
    "waiting": "queued", "todo": "queued",
    "building": "building", "build": "building",
    "in-progress": "building", "started": "building",
    "verifying": "verifying", "verify": "verifying",
    "checking": "verifying", "review": "verifying",
    "banked": "banked", "done": "banked",
    "finished": "banked", "complete": "banked",
    "shipped": "banked",
}

#: The acts one hand may do on the board, in the
#: roadmap's own order of concern: move a slice
#: forward, re-order it, pause it, resume it, or
#: strike it.
ACTION_KINDS = ("advance", "reorder", "pause", "resume", "strike")

_ACTION_ALIASES = {
    "advance": "advance", "move": "advance",
    "forward": "advance",
    "reorder": "reorder", "re-order": "reorder",
    "order": "reorder",
    "pause": "pause", "hold": "pause",
    "resume": "resume", "unpause": "resume",
    "strike": "strike", "struck": "strike",
    "cut": "strike",
}

#: The columns an advance action may move a card
#: to: a hand moves work forward on the board;
#: banking itself stays the coordinator's road.
_ADVANCE_TARGETS = ("building", "verifying")

#: The one legal advance step from each column.
_ADVANCE_FROM = {"queued": "building", "building": "verifying"}

#: The words a whole board's verdict may carry:
#: complete while every card stands banked,
#: flowing while any card stands building or
#: verifying, waiting while the board only waits.
VERDICT_WORDS = ("complete", "flowing", "waiting")

#: The shipped roadmap's ledger statuses read
#: onto the board's columns: the composition
#: road's whole judgement, by import.
ROADMAP_COLUMNS = {"done": "banked", "queued": "queued"}

_SLICE_ID_RE = re.compile(r"^M-\d{3}$")

_CARD_KEYS = frozenset({
    "slice_id", "id", "slice", "position", "place",
    "order", "part", "title", "summary", "column",
    "state", "paused", "struck",
    "recorded_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session"})

_ROW_KEYS = frozenset({
    "slice_id", "id", "position", "part", "title",
    "column", "paused", "struck", "line",
    "board_line", "recorded_on"})

_COLUMN_COUNT_KEYS = frozenset({"column", "items", "count"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "rows", "cards",
    "total_cards", "total", "total_queued", "queued",
    "total_building", "building", "total_verifying",
    "verifying", "total_banked", "banked",
    "total_paused", "paused", "total_struck", "struck",
    "distinct_parts", "parts",
    "column_counts", "columns", "next_slice_id",
    "next", "as_of", "day", "account", "statements"})

_ACTION_KEYS = frozenset({
    "action_id", "id", "seq", "sequence", "order",
    "kind", "act", "slice_id", "slice", "detail",
    "reason", "target_position", "position",
    "target_column", "column",
    "recorded_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session"})

_VERDICT_KEYS = frozenset({
    "total_cards", "total", "total_queued", "queued",
    "total_building", "building", "total_verifying",
    "verifying", "total_banked", "banked",
    "total_paused", "paused", "total_struck", "struck",
    "distinct_parts", "parts",
    "earliest_on", "earliest", "latest_on", "latest",
    "verdict"})

_BOARD_KEYS = frozenset({"title", "name"})

_SLICE_BOARD_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "cards", "actions",
    "panels"})

_EXAMPLE_TITLE = "Slice Board at the M-172 slice boundary"

_EXAMPLE_CARD_IDS = (
    "M-171", "M-172", "M-173", "M-174",
    "M-175", "M-176", "M-177")

_EXAMPLE_FIRST_CARD_ID = "M-171"

_EXAMPLE_FIRST_CARD_TITLE = "The TUI redesign charter"

_EXAMPLE_PANEL_ID = "panel-m172-boundary"

_EXAMPLE_AS_OF = "2026-11-09"

_EXAMPLE_PANEL_ROW_IDS = (
    "M-171", "M-172", "M-173", "M-176",
    "M-174", "M-175", "M-177")

_EXAMPLE_ACTION_IDS = (
    "act-open-m173", "act-pause-m175",
    "act-reorder-m176", "act-strike-m177")

PLAIN_EXPLANATION = (
    "The Slice Board: plans and roadmaps as a "
    "visible board - every slice a card standing "
    "in one of four columns, queued, building, "
    "verifying or banked, its line derived from "
    "its slice, its title and its column, never "
    "chosen. A card composed from the shipped "
    "roadmap takes its column from the slice's "
    "own ledger status, done reading banked and "
    "queued reading queued. What the human does "
    "by hand - advance, re-order, pause, resume "
    "or strike a slice - is held as its own "
    "action record with its provenance whole, "
    "and the effective board, its panel and its "
    "verdict are derived by standing the held "
    "actions on the held cards. A hand action "
    "moves this board alone: it rewrites no "
    "shipped roadmap data, banks nothing and "
    "deletes nothing - a struck slice still "
    "stands on the board, struck and seen. This "
    "layer holds plans as data only: it runs no "
    "build, sends nothing, posts nothing, "
    "schedules nothing, calls no model and "
    "persists nothing - a card held here is a "
    "record of a plan, never the work itself."
)

USAGE = (
    "Usage: /sliceboard, /sliceboard show, "
    "/sliceboard card <slice-id>, "
    "/sliceboard column <column>, "
    "/sliceboard action <action-id>, "
    "/sliceboard panel, /sliceboard verdict"
)


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_title(value: Any, what: str = "a title") -> str:
    text = _clean_text(value, what)
    if len(text) > 120 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"120 characters, got {len(text)} characters")
    return text


def _check_long_text(value: Any, what: str) -> str:
    text = _clean_text(value, what)
    if len(text) > 2000 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"2000 characters, got {len(text)} characters")
    return text


def _check_account(value: Any) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"an account must be a list of statements, "
            f"got {value!r}")
    account = tuple(
        _check_long_text(a, "an account statement")
        for a in value)
    if not account:
        raise ValueError("an account carries at least one statement")
    if len(account) > 16:
        raise ValueError(
            f"an account carries at most 16 statements, "
            f"got {len(account)}")
    if len(set(account)) != len(account):
        raise ValueError("an account states one statement twice")
    return account


def _pick_any(mapping: Dict[str, Any], spellings: Tuple[str, ...],
              what: str) -> Any:
    values = [mapping[s] for s in spellings if s in mapping]
    if not values:
        return None
    if any(value != values[0] for value in values[1:]):
        raise ValueError(f"a record names two different {what}")
    return values[0]


def _check_count(value: Any, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{what} must be a count, got {value!r}")
    if value < 0:
        raise ValueError(f"{what} must not be negative, got {value!r}")
    return value


def _check_position(value: Any, what: str = "a card's position") -> int:
    position = _check_count(value, what)
    if position < 1:
        raise ValueError(
            f"{what} stands from 1, got {value!r}")
    return position


def _check_seq(value: Any) -> int:
    seq = _check_count(value, "an action's sequence")
    if seq < 1:
        raise ValueError(
            f"an action's sequence stands from 1, got {value!r}")
    return seq


def _check_word(value: Any, what: str) -> str:
    try:
        return normalize_member_id(value)
    except ValueError:
        raise ValueError(
            f"{what} must be one plain word, "
            f"got {value!r}") from None


def _check_slice_id(value: Any, what: str = "a slice id") -> str:
    text = _clean_text(value, what)
    if not _SLICE_ID_RE.match(text):
        raise ValueError(
            f"{what} must look like 'M-001', got {text!r}")
    return text


def _check_part(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"a card's part must be a count, got {value!r}")
    if not 1 <= value <= 11:
        raise ValueError(f"a card's part must be 1..11, got {value!r}")
    return value


def _check_flag(value: Any, what: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{what} must be true or false, got {value!r}")
    return value


def _check_day(value: Any, what: str = "a day") -> str:
    text = _clean_text(value, what)
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        raise ValueError(
            f"{what} must be an ISO date "
            f"(YYYY-MM-DD), got {text!r}") from None
    if parsed.isoformat() != text:
        raise ValueError(
            f"{what} must be an ISO date "
            f"(YYYY-MM-DD), got {text!r}")
    return text


def normalize_column(value: Any) -> str:
    """One column word, read onto the closed column set."""
    if not isinstance(value, str):
        raise ValueError(f"a column must be a word, got {value!r}")
    column = _COLUMN_ALIASES.get(value.strip().lower())
    if column is None:
        raise ValueError(
            "a column is one of %s, got %r"
            % ("/".join(COLUMNS), value))
    return column


def normalize_action_kind(value: Any) -> str:
    """One hand-action kind word, read onto the closed set."""
    if not isinstance(value, str):
        raise ValueError(f"an action kind must be a word, got {value!r}")
    kind = _ACTION_ALIASES.get(value.strip().lower())
    if kind is None:
        raise ValueError(
            "an action kind is one of %s, got %r"
            % ("/".join(ACTION_KINDS), value))
    return kind


def column_for_status(status: Any) -> str:
    """The board column a shipped ledger status derives.

    The roadmap's own statuses, read by import
    from the shipped roadmap layer's vocabulary:
    done reads banked, queued reads queued. A
    status the road does not know refuses plainly.
    """
    if not isinstance(status, str):
        raise ValueError(f"a slice status must be a word, got {status!r}")
    column = ROADMAP_COLUMNS.get(status.strip().lower())
    if column is None:
        raise ValueError(
            f"no column stands judged for roadmap status "
            f"{status!r} - the board reads only the shipped "
            f"road's own statuses ({'/'.join(ROADMAP_COLUMNS)}), "
            f"and invents no column for the rest")
    return column


def line_of(card: Any) -> str:
    """The board line one card derives.

    Read off the card's slice id, title, column
    and paused/struck flags alone: the slice and
    its title, its column as a word, and its hand
    flags named as words when they stand - colour
    is never the only signal, because there is no
    colour in this layer at all.
    """
    current = _check_card_ref(card)
    line = f"{current.slice_id} {current.title} - {current.column}"
    if current.paused:
        line += ", paused"
    if current.struck:
        line += ", struck"
    return line


# ---------------------------------------------------------------------
# The card: one slice on the board, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class BoardCard:
    """One slice standing on the board, held whole.

    ``column`` is where the slice stands in the
    closed column set; ``paused`` and ``struck``
    are the hand flags a held action may set.
    ``position`` is the card's place on the
    board, from 1. The provenance - the day it
    was recorded, who recorded it, its source
    and the session it was recorded in - rides
    whole. The board line is never a field: it
    is derived by :func:`line_of` at call time.
    """

    slice_id: str
    position: int
    part: int
    title: str
    summary: str
    column: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str
    paused: bool = False
    struck: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "slice_id", _check_slice_id(self.slice_id))
        object.__setattr__(self, "position", _check_position(self.position))
        object.__setattr__(self, "part", _check_part(self.part))
        object.__setattr__(
            self, "title", _check_title(self.title, "a slice title"))
        object.__setattr__(
            self, "summary",
            _check_long_text(self.summary, "a slice summary"))
        object.__setattr__(self, "column", normalize_column(self.column))
        object.__setattr__(
            self, "paused", _check_flag(self.paused, "a card's paused flag"))
        object.__setattr__(
            self, "struck", _check_flag(self.struck, "a card's struck flag"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _check_title(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _check_title(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))

    @property
    def line(self) -> str:
        """The derived board line of this card."""
        return line_of(self)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "slice_board_card",
            "slice": SLICE_BOARD_SLICE,
            "slice_id": self.slice_id,
            "position": self.position,
            "part": self.part,
            "title": self.title,
            "summary": self.summary,
            "column": self.column,
            "paused": self.paused,
            "struck": self.struck,
            "line": self.line,
            "recorded_on": self.recorded_on,
            "actor": self.actor,
            "source": self.source,
            "origin_session": self.origin_session,
        }


def _check_card_ref(value: Any) -> BoardCard:
    if isinstance(value, BoardCard):
        return value
    return validate_card(value)


def validate_card(card: Any) -> BoardCard:
    """Judge one card whole and return it as a BoardCard.

    A mapping is read through its spellings: a
    derived key (``line``/``board_line``) refuses -
    the line is derived, never stored - as does
    any key the card does not carry, and two
    spellings naming two different values.
    """
    if isinstance(card, BoardCard):
        return card
    if not isinstance(card, dict):
        raise ValueError(
            f"a board card must be a mapping, got {card!r}")
    unknown = set(card) - _CARD_KEYS
    if unknown:
        raise ValueError(
            f"a board card carries unknown keys: "
            f"{sorted(unknown)}")
    if "type" in card:
        raise ValueError("a board card is judged without its news keys")

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(card, spellings, what)
        if value is None:
            raise ValueError(f"a board card names no {what}")
        return value

    paused = _pick_any(card, ("paused",), "paused flag")
    struck = _pick_any(card, ("struck",), "struck flag")
    return BoardCard(
        slice_id=_needed(("slice_id", "id", "slice"), "slice id"),
        position=_needed(
            ("position", "place", "order"), "position"),
        part=_needed(("part",), "part"),
        title=_needed(("title",), "title"),
        summary=_needed(("summary",), "summary"),
        column=_needed(("column", "state"), "column"),
        paused=False if paused is None else paused,
        struck=False if struck is None else struck,
        recorded_on=_needed(
            ("recorded_on", "day", "date"), "day it was recorded"),
        actor=_needed(("actor", "by", "who"), "actor"),
        source=_needed(("source",), "source"),
        origin_session=_needed(
            ("origin_session", "session"), "origin session"),
    )


def build_card(card: Any = None, **kwargs: Any) -> BoardCard:
    """Build one card from a mapping, a card, or fields."""
    if kwargs:
        if card is not None:
            raise ValueError("a card is built one way at a time")
        card = kwargs
    return validate_card(card)


def card_from_roadmap_slice(slice_: Any = None, *,
                            position: Any,
                            recorded_on: Any = "2026-11-09",
                            actor: Any = "the coordinator",
                            source: Any = "slice board",
                            origin_session: Any = "session-m173",
                            column: Any = None) -> BoardCard:
    """Raise one card over a shipped roadmap slice, by import.

    The slice is a shipped roadmap layer's own
    slice (its id, part, title, summary and
    ledger status read off it directly). The
    column is DERIVED from the slice's own
    status by :func:`column_for_status` - a
    column named here that disagrees with the
    derived one refuses. The card stands
    unpaused and unstruck: a hand flag is set
    only by a held board action, never here.
    """
    if slice_ is None:
        raise ValueError("a roadmap slice is needed to raise a card")
    status = getattr(slice_, "status", None)
    derived = column_for_status(status)
    if column is not None and normalize_column(column) != derived:
        raise ValueError(
            f"a column named for slice {getattr(slice_, 'id', None)!r} "
            f"must be the derived column {derived!r}, got {column!r} "
            f"- the column is derived from the shipped road, "
            f"never chosen")
    return BoardCard(
        slice_id=getattr(slice_, "id", None),
        position=position,
        part=getattr(slice_, "part", None),
        title=getattr(slice_, "title", None),
        summary=getattr(slice_, "summary", None),
        column=derived,
        recorded_on=recorded_on, actor=actor,
        source=source, origin_session=origin_session)


def inspect_slice_source(piece: Any) -> Dict[str, Any]:
    """Judge one raw roadmap piece and name what it is.

    A piece shaped like a shipped roadmap slice
    - a mapping carrying a slice id (``id`` /
    ``slice_id``) and a ledger status
    (``status``) - is read onto the column it
    derives, without holding it. Anything else
    is named not-a-slice.
    """
    if not isinstance(piece, dict):
        return {"column": None, "slice_id": None,
                "reason": "not a mapping - no slice stands here"}
    slice_id = _pick_any(piece, ("id", "slice_id"), "slice id")
    if slice_id is None:
        return {"column": None, "slice_id": None,
                "reason": "no slice id named - no slice stands here"}
    status = _pick_any(piece, ("status",), "status")
    try:
        column = column_for_status(status)
        checked = _check_slice_id(slice_id)
    except ValueError as exc:
        return {"column": None, "slice_id": slice_id,
                "reason": str(exc)}
    return {"column": column, "slice_id": checked,
            "status": status, "reason": "a shipped roadmap slice"}


# ---------------------------------------------------------------------
# The action: one act of a human hand, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class BoardAction:
    """One act of a human hand on the board.

    ``kind`` is the act in the closed action
    set; ``slice_id`` is the slice it touches;
    ``detail`` is the hand's own words for why.
    An advance names its ``target_column``
    (building or verifying alone - banking is
    not a hand act here); a re-order names its
    ``target_position``; a pause, resume or
    strike names neither. ``seq`` is the act's
    place in the board's recorded order, from
    1. The provenance rides whole.
    """

    seq: int
    kind: str
    slice_id: str
    detail: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str
    action_id: Optional[str] = None
    target_position: Optional[int] = None
    target_column: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "seq", _check_seq(self.seq))
        kind = normalize_action_kind(self.kind)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(
            self, "slice_id", _check_slice_id(self.slice_id))
        object.__setattr__(
            self, "detail",
            _check_long_text(self.detail, "the action's words"))
        if self.target_position is not None:
            object.__setattr__(
                self, "target_position",
                _check_position(
                    self.target_position, "a target position"))
        if self.target_column is not None:
            object.__setattr__(
                self, "target_column",
                normalize_column(self.target_column))
        if kind == "advance":
            if self.target_column is None:
                raise ValueError(
                    "an advance action names its target column")
            if self.target_column not in _ADVANCE_TARGETS:
                raise ValueError(
                    f"a hand advances a slice to "
                    f"{'/'.join(_ADVANCE_TARGETS)} alone - banking "
                    f"stays the coordinator's road on the shipped "
                    f"ledger, got {self.target_column!r}")
            if self.target_position is not None:
                raise ValueError(
                    "an advance action names no target position")
        elif kind == "reorder":
            if self.target_position is None:
                raise ValueError(
                    "a re-order action names its target position")
            if self.target_column is not None:
                raise ValueError(
                    "a re-order action names no target column")
        else:
            if self.target_position is not None or (
                    self.target_column is not None):
                raise ValueError(
                    f"a {kind} action names neither a target "
                    f"position nor a target column")
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _check_title(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _check_title(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))
        if self.action_id is not None:
            object.__setattr__(
                self, "action_id",
                _check_word(self.action_id, "an action id"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "slice_board_action",
            "slice": SLICE_BOARD_SLICE,
            "action_id": self.action_id,
            "seq": self.seq,
            "kind": self.kind,
            "slice_id": self.slice_id,
            "detail": self.detail,
            "target_position": self.target_position,
            "target_column": self.target_column,
            "recorded_on": self.recorded_on,
            "actor": self.actor,
            "source": self.source,
            "origin_session": self.origin_session,
        }


def _check_action_ref(value: Any) -> BoardAction:
    if isinstance(value, BoardAction):
        return value
    return validate_action(value)


def validate_action(action: Any) -> BoardAction:
    """Judge one hand action whole and return it."""
    if isinstance(action, BoardAction):
        return action
    if not isinstance(action, dict):
        raise ValueError(
            f"a board action must be a mapping, got {action!r}")
    unknown = set(action) - _ACTION_KEYS
    if unknown:
        raise ValueError(
            f"a board action carries unknown keys: "
            f"{sorted(unknown)}")
    if "type" in action:
        raise ValueError("a board action is judged without its news keys")

    def _needed(spellings: Tuple[str, ...], what: str) -> Any:
        value = _pick_any(action, spellings, what)
        if value is None:
            raise ValueError(f"a board action names no {what}")
        return value

    return BoardAction(
        action_id=_pick_any(action, ("action_id", "id"), "action id"),
        seq=_needed(("seq", "sequence", "order"), "sequence"),
        kind=_needed(("kind", "act"), "kind"),
        slice_id=_needed(("slice_id", "slice"), "slice id"),
        detail=_needed(("detail", "reason"), "the action's words"),
        target_position=_pick_any(
            action, ("target_position", "position"), "target position"),
        target_column=_pick_any(
            action, ("target_column", "column"), "target column"),
        recorded_on=_needed(
            ("recorded_on", "day", "date"), "day it was recorded"),
        actor=_needed(("actor", "by", "who"), "actor"),
        source=_needed(("source",), "source"),
        origin_session=_needed(
            ("origin_session", "session"), "origin session"),
    )


def build_action(action: Any = None, **kwargs: Any) -> BoardAction:
    """Build one action from a mapping, an action, or fields."""
    if kwargs:
        if action is not None:
            raise ValueError("an action is built one way at a time")
        action = kwargs
    return validate_action(action)


def _apply_action(cards: List[BoardCard],
                  action: BoardAction) -> List[BoardCard]:
    """Stand one held action on a list of cards.

    The transition laws of the board, enforced
    at every derivation: an advance moves one
    legal step (queued to building, building to
    verifying) on a card no hand has paused or
    struck; a re-order moves an unstruck card
    and renumbers the board contiguously; a
    pause lands on a waiting or working card
    that is neither banked, struck nor already
    paused; a resume lands only on a paused
    card; a strike lands on any card not banked
    and not already struck, and clears its
    pause - a struck slice stands struck, its
    waiting over.
    """
    index = None
    for i, card in enumerate(cards):
        if card.slice_id == action.slice_id:
            index = i
            break
    if index is None:
        raise ValueError(
            f"a board action touches slice {action.slice_id!r}, "
            f"which stands on no card of this board")
    card = cards[index]
    if action.kind == "advance":
        if card.struck:
            raise ValueError(
                f"a struck slice cannot advance: {card.slice_id} "
                f"stands struck on the board")
        if card.paused:
            raise ValueError(
                f"a paused slice cannot advance: {card.slice_id} "
                f"stands paused on the board - resume it first")
        wanted = _ADVANCE_FROM.get(card.column)
        if wanted is None or wanted != action.target_column:
            raise ValueError(
                f"a slice standing {card.column} cannot advance "
                f"to {action.target_column} - a hand moves work "
                f"one step: queued to building, building to "
                f"verifying, and banking is not a hand act")
        return [
            replace(c, column=action.target_column)
            if c.slice_id == card.slice_id else c
            for c in cards]
    if action.kind == "reorder":
        if card.struck:
            raise ValueError(
                f"a struck slice cannot be re-ordered: "
                f"{card.slice_id} stands struck on the board")
        target = action.target_position
        if target is None or not 1 <= target <= len(cards):
            raise ValueError(
                f"a re-order names a place on this board "
                f"(1..{len(cards)}), got {target!r}")
        moved = cards.pop(index)
        cards.insert(target - 1, moved)
        return [
            replace(c, position=i + 1)
            for i, c in enumerate(cards)]
    if action.kind == "pause":
        if card.column == "banked":
            raise ValueError(
                f"a banked slice cannot be paused: "
                f"{card.slice_id} already stands banked")
        if card.struck:
            raise ValueError(
                f"a struck slice cannot be paused: "
                f"{card.slice_id} stands struck on the board")
        if card.paused:
            raise ValueError(
                f"slice {card.slice_id} already stands paused")
        return [
            replace(c, paused=True)
            if c.slice_id == card.slice_id else c
            for c in cards]
    if action.kind == "resume":
        if not card.paused:
            raise ValueError(
                f"slice {card.slice_id} does not stand paused - "
                f"there is nothing to resume")
        return [
            replace(c, paused=False)
            if c.slice_id == card.slice_id else c
            for c in cards]
    if action.kind == "strike":
        if card.column == "banked":
            raise ValueError(
                f"a banked slice cannot be struck: "
                f"{card.slice_id} already stands banked")
        if card.struck:
            raise ValueError(
                f"slice {card.slice_id} already stands struck")
        return [
            replace(c, struck=True, paused=False)
            if c.slice_id == card.slice_id else c
            for c in cards]
    raise ValueError(f"unknown board action kind {action.kind!r}")


def effective_cards(cards: Any, actions: Any = ()) -> Tuple[BoardCard, ...]:
    """The effective board: held actions stood on held cards.

    Cards are read in board order and actions in
    recorded order; every action is judged
    against the board it lands on, so an illegal
    act refuses the whole derivation plainly.
    """
    held = sorted(
        (_check_card_ref(c) for c in cards),
        key=lambda c: c.position)
    stood: List[BoardCard] = list(held)
    for action in sorted(
            (_check_action_ref(a) for a in actions),
            key=lambda a: a.seq):
        stood = _apply_action(stood, action)
    return tuple(
        sorted(stood, key=lambda c: c.position))


# ---------------------------------------------------------------------
# The panel: the whole board, derived at a glance.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class BoardPanelRow:
    """One effective card as the panel carries it.

    The row carries the card's slice id, its
    effective place on the board, its part, its
    title, its effective column, its hand flags,
    its DERIVED board line and its recorded day.
    The summary never stands in a row - the
    panel is the board at a glance.
    """

    slice_id: str
    position: int
    part: int
    title: str
    column: str
    paused: bool
    struck: bool
    line: str
    recorded_on: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "slice_id", _check_slice_id(self.slice_id))
        object.__setattr__(self, "position", _check_position(self.position))
        object.__setattr__(self, "part", _check_part(self.part))
        object.__setattr__(
            self, "title", _check_title(self.title, "a slice title"))
        object.__setattr__(self, "column", normalize_column(self.column))
        object.__setattr__(
            self, "paused", _check_flag(self.paused, "a row's paused flag"))
        object.__setattr__(
            self, "struck", _check_flag(self.struck, "a row's struck flag"))
        object.__setattr__(
            self, "line",
            _check_long_text(self.line, "a board line"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))

    def sort_key(self) -> Tuple[int, str]:
        return (self.position, self.slice_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "slice_id": self.slice_id,
            "position": self.position,
            "part": self.part,
            "title": self.title,
            "column": self.column,
            "paused": self.paused,
            "struck": self.struck,
            "line": self.line,
            "recorded_on": self.recorded_on,
        }


def _row_for_card(card: BoardCard) -> BoardPanelRow:
    return BoardPanelRow(
        slice_id=card.slice_id, position=card.position,
        part=card.part, title=card.title,
        column=card.column, paused=card.paused,
        struck=card.struck, line=line_of(card),
        recorded_on=card.recorded_on)


def _check_row_ref(value: Any) -> BoardPanelRow:
    if isinstance(value, BoardPanelRow):
        return value
    return validate_row(value)


def validate_row(row: Any, card: Any = None) -> BoardPanelRow:
    """Judge one panel row, against its card when named."""
    if isinstance(row, BoardPanelRow):
        current = row
    elif isinstance(row, dict):
        unknown = set(row) - _ROW_KEYS
        if unknown:
            raise ValueError(
                f"a slice board row carries unknown keys: "
                f"{sorted(unknown)}")

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(row, spellings, what)
            if value is None:
                raise ValueError(f"a slice board row names no {what}")
            return value

        paused = _pick_any(row, ("paused",), "paused flag")
        struck = _pick_any(row, ("struck",), "struck flag")
        if paused is None or struck is None:
            raise ValueError(
                "a slice board row names its paused and struck flags")
        current = BoardPanelRow(
            slice_id=_needed(("slice_id", "id"), "slice id"),
            position=_needed(("position",), "position"),
            part=_needed(("part",), "part"),
            title=_needed(("title",), "title"),
            column=_needed(("column",), "column"),
            paused=paused,
            struck=struck,
            line=_needed(("line", "board_line"), "board line"),
            recorded_on=_needed(("recorded_on",), "day it was recorded"))
    else:
        raise ValueError(
            f"a slice board row must be a mapping, got {row!r}")
    if card is not None:
        wanted = _row_for_card(_check_card_ref(card))
        if current != wanted:
            raise ValueError(
                "a slice board row must be its card's own row - "
                "the board line is derived from the card, never "
                "written beside it")
    return current


def build_row(row: Any = None, card: Any = None,
              **kwargs: Any) -> BoardPanelRow:
    """Build one panel row from a mapping, a row, or its card."""
    if card is not None:
        if row is not None or kwargs:
            return validate_row(row if row is not None else kwargs,
                                card)
        return _row_for_card(_check_card_ref(card))
    if kwargs:
        if row is not None:
            raise ValueError("a row is built one way at a time")
        row = kwargs
    return validate_row(row)


@dataclass(frozen=True)
class ColumnCount:
    """How many cards of one column a panel holds."""

    column: str
    items: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "column", normalize_column(self.column))
        object.__setattr__(
            self, "items", _check_count(self.items, "a column's items"))

    def to_record(self) -> Dict[str, Any]:
        return {"column": self.column, "items": self.items}


def _check_column_count_ref(value: Any) -> ColumnCount:
    if isinstance(value, ColumnCount):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _COLUMN_COUNT_KEYS
        if unknown:
            raise ValueError(
                f"a column count carries unknown keys: "
                f"{sorted(unknown)}")
        column = _pick_any(value, ("column",), "column")
        items = _pick_any(value, ("items", "count"), "items")
        if column is None or items is None:
            raise ValueError("a column count names its column and its items")
        return ColumnCount(column=column, items=items)
    raise ValueError(f"a column count must be a mapping, got {value!r}")


def _column_counts(rows: Tuple[BoardPanelRow, ...]) -> Tuple[ColumnCount, ...]:
    counts: Dict[str, int] = {}
    for row in rows:
        counts[row.column] = counts.get(row.column, 0) + 1
    return tuple(
        ColumnCount(column=column, items=counts[column])
        for column in COLUMNS if column in counts)


def _next_slice_id(rows: Tuple[BoardPanelRow, ...]) -> Optional[str]:
    for row in rows:
        if row.column == "queued" and not row.paused and not row.struck:
            return row.slice_id
    return None


def _panel_account(total_cards: int, total_queued: int,
                   total_building: int, total_verifying: int,
                   total_banked: int, total_paused: int,
                   total_struck: int, distinct_parts: int,
                   column_counts: Tuple[ColumnCount, ...],
                   next_slice_id: Optional[str],
                   as_of: str) -> Tuple[str, ...]:
    columns = ", ".join(
        f"{count.column} {count.items}" for count in column_counts)
    return (
        f"The slice board holds {total_cards} slices as of "
        f"{as_of}: {total_queued} queued, {total_building} "
        f"building, {total_verifying} verifying and "
        f"{total_banked} banked over {distinct_parts} parts: "
        f"{columns}; {total_paused} stand paused by hand and "
        f"{total_struck} stand struck by hand.",
        "Rows stand in board order, first slice first, so "
        "two panels of one board diff cleanly, line by line.",
        f"The next slice standing ready is "
        f"{next_slice_id or 'none'}: the first queued slice "
        f"no hand has paused or struck, read off the board "
        f"at call time.",
        "Every row carries its derived board line and its "
        "column as words: a hand action held on this board "
        "moves this board alone - it rewrites no shipped "
        "roadmap data, banks nothing and deletes nothing, "
        "and standing on this panel runs no build.",
    )


@dataclass(frozen=True)
class BoardPanel:
    """The derived panel of one board: the board at a glance.

    Rows stand in effective board order; the
    totals are the rows' own counts;
    ``next_slice_id`` is the first queued row no
    hand has paused or struck, or None while no
    slice stands ready. A stored panel is judged
    whole in ``__post_init__``: its totals, its
    column counts, its next slice, its as-of day
    and its account must all be the rows' own
    derived shape - a panel may not soften its
    board.
    """

    panel_id: Optional[str]
    rows: Tuple[BoardPanelRow, ...]
    total_cards: int
    total_queued: int
    total_building: int
    total_verifying: int
    total_banked: int
    total_paused: int
    total_struck: int
    distinct_parts: int
    column_counts: Tuple[ColumnCount, ...]
    next_slice_id: Optional[str]
    as_of: str
    account: Tuple[str, ...]

    def __post_init__(self) -> None:
        if self.panel_id is not None:
            object.__setattr__(
                self, "panel_id",
                _check_word(self.panel_id, "a panel id"))
        rows = tuple(_check_row_ref(r) for r in self.rows)
        object.__setattr__(self, "rows", rows)
        positions = [r.position for r in rows]
        if positions != sorted(positions) or (
                len(set(positions)) != len(positions)):
            raise ValueError(
                "panel rows stand in board order, one row "
                "per position")
        for field in ("total_cards", "total_queued",
                      "total_building", "total_verifying",
                      "total_banked", "total_paused",
                      "total_struck", "distinct_parts"):
            object.__setattr__(
                self, field,
                _check_count(getattr(self, field), f"a panel's {field}"))
        counts = tuple(
            _check_column_count_ref(c) for c in self.column_counts)
        object.__setattr__(self, "column_counts", counts)
        if self.next_slice_id is not None:
            object.__setattr__(
                self, "next_slice_id",
                _check_slice_id(self.next_slice_id, "a next slice id"))
        object.__setattr__(self, "as_of", _check_day(self.as_of, "an as-of day"))
        object.__setattr__(self, "account", _check_account(self.account))
        if self.total_cards != len(rows):
            raise ValueError("a panel's total is its rows' own count")
        for column, field in (
                ("queued", "total_queued"),
                ("building", "total_building"),
                ("verifying", "total_verifying"),
                ("banked", "total_banked")):
            if getattr(self, field) != sum(
                    1 for r in rows if r.column == column):
                raise ValueError(
                    f"a panel's {column} total is its rows' own count")
        if self.total_paused != sum(1 for r in rows if r.paused):
            raise ValueError("a panel's paused total is its rows' own count")
        if self.total_struck != sum(1 for r in rows if r.struck):
            raise ValueError("a panel's struck total is its rows' own count")
        if self.distinct_parts != len({r.part for r in rows}):
            raise ValueError(
                "a panel's distinct parts are its rows' own count")
        if counts != _column_counts(rows):
            raise ValueError("a panel's column counts are its rows' own counts")
        if self.next_slice_id != _next_slice_id(rows):
            raise ValueError(
                "a panel's next slice is the first queued row no "
                "hand has paused or struck, derived, never chosen")
        if rows and self.as_of != max(r.recorded_on for r in rows):
            raise ValueError("a panel's as-of day is its rows' latest day")
        wanted = _panel_account(
            self.total_cards, self.total_queued, self.total_building,
            self.total_verifying, self.total_banked, self.total_paused,
            self.total_struck, self.distinct_parts, counts,
            self.next_slice_id, self.as_of)
        if self.account != wanted:
            raise ValueError("a panel's account is its derived account")

    def row_for(self, slice_id: Any) -> BoardPanelRow:
        """The row one slice id names (KeyError if absent)."""
        wanted = _check_slice_id(slice_id)
        for row in self.rows:
            if row.slice_id == wanted:
                return row
        raise KeyError(f"no row named {wanted!r} stands in the panel")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "slice_board_panel",
            "slice": SLICE_BOARD_SLICE,
            "panel_id": self.panel_id,
            "rows": [r.to_record() for r in self.rows],
            "total_cards": self.total_cards,
            "total_queued": self.total_queued,
            "total_building": self.total_building,
            "total_verifying": self.total_verifying,
            "total_banked": self.total_banked,
            "total_paused": self.total_paused,
            "total_struck": self.total_struck,
            "distinct_parts": self.distinct_parts,
            "column_counts": [c.to_record() for c in self.column_counts],
            "next_slice_id": self.next_slice_id,
            "as_of": self.as_of,
            "account": list(self.account),
        }


def _held_cards(source: Any) -> Tuple[BoardCard, ...]:
    if isinstance(source, SliceBoard):
        return source.effective_cards()
    if isinstance(source, SliceBoardRegistry):
        return source.effective_cards()
    if isinstance(source, BoardCard):
        return (source,)
    raise ValueError(f"a slice-board source is needed, got {source!r}")


def derive_panel(source: Any) -> BoardPanel:
    """Derive the board panel of a board, registry or card."""
    cards = _held_cards(source)
    rows = tuple(_row_for_card(c) for c in cards)
    counts = _column_counts(rows)
    totals = {
        column: sum(1 for r in rows if r.column == column)
        for column in COLUMNS}
    distinct = len({r.part for r in rows})
    as_of = max((r.recorded_on for r in rows), default=_EXAMPLE_AS_OF)
    return BoardPanel(
        panel_id=None, rows=rows, total_cards=len(rows),
        total_queued=totals["queued"],
        total_building=totals["building"],
        total_verifying=totals["verifying"],
        total_banked=totals["banked"],
        total_paused=sum(1 for r in rows if r.paused),
        total_struck=sum(1 for r in rows if r.struck),
        distinct_parts=distinct, column_counts=counts,
        next_slice_id=_next_slice_id(rows), as_of=as_of,
        account=_panel_account(
            len(rows), totals["queued"], totals["building"],
            totals["verifying"], totals["banked"],
            sum(1 for r in rows if r.paused),
            sum(1 for r in rows if r.struck),
            distinct, counts, _next_slice_id(rows), as_of))


def validate_panel(panel: Any, source: Any = None) -> BoardPanel:
    """Judge one panel whole, against its source when named."""
    if isinstance(panel, BoardPanel):
        current = panel
    elif isinstance(panel, dict):
        data = dict(panel)
        data.pop("type", None)
        data.pop("slice", None)
        unknown = set(data) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                f"a slice board panel carries unknown keys: "
                f"{sorted(unknown)}")

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(data, spellings, what)
            if value is None:
                raise ValueError(f"a slice board panel names no {what}")
            return value

        rows_in = _needed(("rows", "cards"), "rows")
        counts_in = _needed(("column_counts", "columns"), "column counts")
        current = BoardPanel(
            panel_id=_pick_any(data, ("panel_id", "id"), "panel id"),
            rows=tuple(validate_row(r) for r in rows_in),
            total_cards=_needed(("total_cards", "total"), "total cards"),
            total_queued=_needed(("total_queued", "queued"), "queued total"),
            total_building=_needed(
                ("total_building", "building"), "building total"),
            total_verifying=_needed(
                ("total_verifying", "verifying"), "verifying total"),
            total_banked=_needed(("total_banked", "banked"), "banked total"),
            total_paused=_needed(("total_paused", "paused"), "paused total"),
            total_struck=_needed(("total_struck", "struck"), "struck total"),
            distinct_parts=_needed(
                ("distinct_parts", "parts"), "distinct parts"),
            column_counts=tuple(
                _check_column_count_ref(c) for c in counts_in),
            next_slice_id=_pick_any(
                data, ("next_slice_id", "next"), "next slice"),
            as_of=_needed(("as_of", "day"), "as-of day"),
            account=tuple(_needed(("account", "statements"), "account")))
    else:
        raise ValueError(f"a slice board panel must be a mapping, got {panel!r}")
    if source is not None:
        derived = derive_panel(source)
        if (current.rows != derived.rows
                or current.total_cards != derived.total_cards
                or current.total_queued != derived.total_queued
                or current.total_building != derived.total_building
                or current.total_verifying != derived.total_verifying
                or current.total_banked != derived.total_banked
                or current.total_paused != derived.total_paused
                or current.total_struck != derived.total_struck
                or current.distinct_parts != derived.distinct_parts
                or current.column_counts != derived.column_counts
                or current.next_slice_id != derived.next_slice_id
                or current.as_of != derived.as_of
                or current.account != derived.account):
            raise ValueError(
                "a stored panel must equal the panel its board "
                "derives - the panel is derived, never stored loose")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> BoardPanel:
    """Build one panel from a mapping, a panel, or its source."""
    if kwargs:
        if panel is not None:
            raise ValueError("a panel is built one way at a time")
        panel = kwargs
    if panel is None and source is not None:
        return derive_panel(source)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The verdict: the whole board, judged in one word.
# ---------------------------------------------------------------------


def _verdict_word(total_cards: int, total_building: int,
                  total_verifying: int, total_banked: int) -> str:
    if total_cards > 0 and total_banked == total_cards:
        return "complete"
    if total_building + total_verifying > 0:
        return "flowing"
    return "waiting"


@dataclass(frozen=True)
class BoardVerdict:
    """The derived verdict of one whole board.

    The word is read off the tallies alone:
    complete while every card stands banked,
    flowing while any card stands building or
    verifying, waiting while the board only
    waits. A stored verdict is judged against
    those tallies in ``__post_init__``.
    """

    total_cards: int
    total_queued: int
    total_building: int
    total_verifying: int
    total_banked: int
    total_paused: int
    total_struck: int
    distinct_parts: int
    earliest_on: str
    latest_on: str
    verdict: str

    def __post_init__(self) -> None:
        for field in ("total_cards", "total_queued", "total_building",
                      "total_verifying", "total_banked", "total_paused",
                      "total_struck", "distinct_parts"):
            object.__setattr__(
                self, field,
                _check_count(getattr(self, field), f"a verdict's {field}"))
        object.__setattr__(
            self, "earliest_on", _check_day(self.earliest_on, "an earliest day"))
        object.__setattr__(
            self, "latest_on", _check_day(self.latest_on, "a latest day"))
        if self.latest_on < self.earliest_on:
            raise ValueError("a verdict's latest day precedes its earliest")
        if self.total_cards != (
                self.total_queued + self.total_building
                + self.total_verifying + self.total_banked):
            raise ValueError(
                "a verdict's tallies must close on its total")
        word = _clean_text(self.verdict, "a verdict")
        if word not in VERDICT_WORDS:
            raise ValueError(
                f"a verdict is one of {VERDICT_WORDS}, got {word!r}")
        object.__setattr__(self, "verdict", word)
        if word != _verdict_word(
                self.total_cards, self.total_building,
                self.total_verifying, self.total_banked):
            raise ValueError(
                "a verdict's word is derived from its tallies, "
                "never chosen")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "slice_board_verdict",
            "slice": SLICE_BOARD_SLICE,
            "total_cards": self.total_cards,
            "total_queued": self.total_queued,
            "total_building": self.total_building,
            "total_verifying": self.total_verifying,
            "total_banked": self.total_banked,
            "total_paused": self.total_paused,
            "total_struck": self.total_struck,
            "distinct_parts": self.distinct_parts,
            "earliest_on": self.earliest_on,
            "latest_on": self.latest_on,
            "verdict": self.verdict,
        }


def derive_verdict(source: Any) -> BoardVerdict:
    """Derive the board verdict of a board, registry or card."""
    cards = _held_cards(source)
    totals = {
        column: sum(1 for c in cards if c.column == column)
        for column in COLUMNS}
    days = [c.recorded_on for c in cards]
    return BoardVerdict(
        total_cards=len(cards), total_queued=totals["queued"],
        total_building=totals["building"],
        total_verifying=totals["verifying"],
        total_banked=totals["banked"],
        total_paused=sum(1 for c in cards if c.paused),
        total_struck=sum(1 for c in cards if c.struck),
        distinct_parts=len({c.part for c in cards}),
        earliest_on=min(days) if days else _EXAMPLE_AS_OF,
        latest_on=max(days) if days else _EXAMPLE_AS_OF,
        verdict=_verdict_word(
            len(cards), totals["building"], totals["verifying"],
            totals["banked"]))


def _check_verdict_ref(value: Any) -> BoardVerdict:
    if isinstance(value, BoardVerdict):
        return value
    return validate_verdict(value)


def validate_verdict(verdict: Any, source: Any = None) -> BoardVerdict:
    """Judge one verdict whole, against its source when named."""
    if isinstance(verdict, BoardVerdict):
        current = verdict
    elif isinstance(verdict, dict):
        data = dict(verdict)
        data.pop("type", None)
        data.pop("slice", None)
        unknown = set(data) - _VERDICT_KEYS
        if unknown:
            raise ValueError(
                f"a slice board verdict carries unknown keys: "
                f"{sorted(unknown)}")

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(data, spellings, what)
            if value is None:
                raise ValueError(f"a slice board verdict names no {what}")
            return value

        current = BoardVerdict(
            total_cards=_needed(("total_cards", "total"), "total cards"),
            total_queued=_needed(("total_queued", "queued"), "queued total"),
            total_building=_needed(
                ("total_building", "building"), "building total"),
            total_verifying=_needed(
                ("total_verifying", "verifying"), "verifying total"),
            total_banked=_needed(("total_banked", "banked"), "banked total"),
            total_paused=_needed(("total_paused", "paused"), "paused total"),
            total_struck=_needed(("total_struck", "struck"), "struck total"),
            distinct_parts=_needed(
                ("distinct_parts", "parts"), "distinct parts"),
            earliest_on=_needed(("earliest_on", "earliest"), "earliest day"),
            latest_on=_needed(("latest_on", "latest"), "latest day"),
            verdict=_needed(("verdict",), "verdict"))
    else:
        raise ValueError(f"a slice board verdict must be a mapping, got {verdict!r}")
    if source is not None:
        derived = derive_verdict(source)
        if current != derived:
            raise ValueError(
                "a stored verdict must equal the verdict its "
                "board derives - the verdict is derived, never "
                "stored loose")
    return current


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> BoardVerdict:
    """Build one verdict from a mapping, a verdict, or its source."""
    if kwargs:
        if verdict is not None:
            raise ValueError("a verdict is built one way at a time")
        verdict = kwargs
    if verdict is None and source is not None:
        return derive_verdict(source)
    return validate_verdict(verdict, source)


# ---------------------------------------------------------------------
# The board: one plan of slices, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SliceBoard:
    """One plan of slices standing on a board, held whole.

    Cards stand in board order - positions
    strictly ascending, one card per slice and
    per position - actions stand in recorded
    order, one action per sequence and per id,
    every action must stand legally on the
    board it touches (the effective board is
    derived in ``__post_init__``), and every
    stored panel is judged against the board it
    stands in.
    """

    title: str
    cards: Tuple[BoardCard, ...] = ()
    actions: Tuple[BoardAction, ...] = ()
    panels: Tuple[BoardPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a board title"))
        cards = tuple(_check_card_ref(c) for c in self.cards)
        object.__setattr__(self, "cards", cards)
        positions = [c.position for c in cards]
        if positions != sorted(positions) or (
                len(set(positions)) != len(positions)):
            raise ValueError(
                "a board's cards stand in board order, one "
                "card per position")
        ids = [c.slice_id for c in cards]
        if len(set(ids)) != len(ids):
            raise ValueError("a board holds one card per slice id")
        actions = tuple(_check_action_ref(a) for a in self.actions)
        object.__setattr__(self, "actions", actions)
        seqs = [a.seq for a in actions]
        if seqs != sorted(seqs) or len(set(seqs)) != len(seqs):
            raise ValueError(
                "a board's actions stand in recorded order, "
                "one action per sequence")
        action_ids = [a.action_id for a in actions if a.action_id is not None]
        if len(set(action_ids)) != len(action_ids):
            raise ValueError("a board holds one action per action id")
        # The effective board must derive: every held
        # action stands legally on the board it touches.
        effective_cards(cards, actions)
        panels = tuple(
            validate_panel(p, self) for p in self.panels)
        object.__setattr__(self, "panels", panels)

    def card_for(self, slice_id: Any) -> BoardCard:
        """The held (base) card one slice id names (KeyError)."""
        wanted = _check_slice_id(slice_id)
        for card in self.cards:
            if card.slice_id == wanted:
                return card
        raise KeyError(f"no card named {wanted!r} stands on the board")

    def effective_card(self, slice_id: Any) -> BoardCard:
        """The effective card one slice id names (KeyError)."""
        wanted = _check_slice_id(slice_id)
        for card in self.effective_cards():
            if card.slice_id == wanted:
                return card
        raise KeyError(f"no card named {wanted!r} stands on the board")

    def action_for(self, action_id: Any) -> BoardAction:
        """The action one id names (KeyError if absent)."""
        wanted = _check_word(action_id, "an action id")
        for action in self.actions:
            if action.action_id == wanted:
                return action
        raise KeyError(f"no action named {wanted!r} stands on the board")

    def panel_for(self, panel_id: Any) -> BoardPanel:
        """The panel one id names (KeyError if absent)."""
        wanted = _check_word(panel_id, "a panel id")
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel named {wanted!r} stands on the board")

    def effective_cards(self) -> Tuple[BoardCard, ...]:
        """The board as the held actions leave it standing."""
        return effective_cards(self.cards, self.actions)

    def slice_ids(self) -> Tuple[str, ...]:
        """The board's slice ids, in held board order."""
        return tuple(c.slice_id for c in self.cards)

    def action_ids(self) -> Tuple[Optional[str], ...]:
        """The board's action ids, in recorded order."""
        return tuple(a.action_id for a in self.actions)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "slice_board_book",
            "slice": SLICE_BOARD_SLICE,
            "title": self.title,
            "cards": [c.to_record() for c in self.cards],
            "actions": [a.to_record() for a in self.actions],
            "panels": [p.to_record() for p in self.panels],
            "card_count": len(self.cards),
            "action_count": len(self.actions),
        }


def _judge_board_panels(board: SliceBoard) -> None:
    for panel in board.panels:
        validate_panel(panel, board)


def validate_board(data: Any, *, require_example: bool = False) -> SliceBoard:
    """Judge one board file's data whole and return its board."""
    if isinstance(data, SliceBoard):
        board = data
        _judge_board_panels(board)
        if require_example:
            _check_example(board)
        return board
    if not isinstance(data, dict):
        raise ValueError(f"a slice board must be a mapping, got {data!r}")
    unknown = set(data) - _SLICE_BOARD_KEYS - {"guide"}
    if unknown:
        raise ValueError(
            f"a slice board carries unknown keys: {sorted(unknown)}")
    if data.get("schema") != SLICE_BOARD_SCHEMA:
        raise ValueError(
            f"a slice board's schema must be {SLICE_BOARD_SCHEMA!r}, "
            f"got {data.get('schema')!r}")
    if data.get("slice") != SLICE_BOARD_SLICE:
        raise ValueError(
            f"a slice board's slice must be {SLICE_BOARD_SLICE!r}, "
            f"got {data.get('slice')!r}")
    guide = data.get("guide") or {}
    title = _pick_any(guide, ("title", "name"), "title")
    if title is None:
        title = _pick_any(data, ("title", "name"), "title")
    cards_in = _pick_any(data, ("cards",), "cards")
    if cards_in is None:
        raise ValueError("a slice board names no cards")
    actions_in = data.get("actions") or []
    panels_in = data.get("panels") or []
    cards = []
    for raw in cards_in:
        stored = dict(raw)
        stored.pop("type", None)
        stored.pop("slice", None)
        stored.pop("line", None)
        cards.append(validate_card(stored))
    actions = []
    for raw in actions_in:
        stored = dict(raw)
        stored.pop("type", None)
        stored.pop("slice", None)
        actions.append(validate_action(stored))
    board = SliceBoard(
        title=title,
        cards=tuple(cards),
        actions=tuple(actions),
        panels=tuple(validate_panel(p) for p in panels_in))
    _judge_board_panels(board)
    if require_example:
        _check_example(board)
    return board


def _check_example(board: SliceBoard) -> None:
    if board.title != _EXAMPLE_TITLE:
        raise ValueError(
            f"the shipped example board is {_EXAMPLE_TITLE!r}, "
            f"got {board.title!r}")
    if board.slice_ids() != _EXAMPLE_CARD_IDS:
        raise ValueError("the shipped example board's cards differ")
    first = board.cards[0]
    if first.title != _EXAMPLE_FIRST_CARD_TITLE:
        raise ValueError("the shipped example board's first card differs")
    if board.action_ids() != _EXAMPLE_ACTION_IDS:
        raise ValueError("the shipped example board's actions differ")
    if len(board.panels) != 1 or (
            board.panels[0].panel_id != _EXAMPLE_PANEL_ID):
        raise ValueError("the shipped example board's panel differs")
    if board.panels[0].as_of != _EXAMPLE_AS_OF:
        raise ValueError("the shipped example board's as-of day differs")
    if tuple(r.slice_id for r in board.panels[0].rows) != (
            _EXAMPLE_PANEL_ROW_IDS):
        raise ValueError("the shipped example board's panel rows differ")


def build_board(board: Any = None, **kwargs: Any) -> SliceBoard:
    """Build one board from a mapping, a board, or fields."""
    if isinstance(board, SliceBoard) and not kwargs:
        return validate_board(board)
    if kwargs:
        if board is not None:
            raise ValueError("a board is built one way at a time")
        fields = dict(kwargs)
    elif isinstance(board, dict) and (
            "cards" in board) and (
            "schema" not in board and "guide" not in board
            and "canon_note" not in board):
        fields = dict(board)
    else:
        return _board_from(board, require_example=False)
    unknown = set(fields) - _BOARD_KEYS - {
        "cards", "actions", "panels"}
    if unknown:
        raise ValueError(
            f"a slice board carries unknown keys: {sorted(unknown)}")
    title = _pick_any(fields, ("title", "name"), "title")
    if title is None:
        raise ValueError("a slice board names no title")
    cards_in = _pick_any(fields, ("cards",), "cards") or ()
    return SliceBoard(
        title=title,
        cards=tuple(_check_card_ref(c) for c in cards_in),
        actions=tuple(
            _check_action_ref(a) for a in fields.get("actions") or ()),
        panels=tuple(
            validate_panel(p) for p in fields.get("panels") or ()))


def _board_from(data: Any, *, require_example: bool) -> SliceBoard:
    if isinstance(data, SliceBoard):
        return validate_board(data, require_example=require_example)
    if isinstance(data, dict):
        return validate_board(data, require_example=require_example)
    raise ValueError(f"a slice board must be a mapping, got {data!r}")


def load_slice_board(data: Optional[Dict[str, Any]] = None) -> SliceBoard:
    """Load the shipped example board, or judge *data* as one."""
    if data is None:
        data = load_resource(SLICE_BOARD_RESOURCE)
        return _board_from(data, require_example=True)
    return _board_from(data, require_example=False)


def load_slice_board_file(path: Any) -> SliceBoard:
    """Load one board file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _board_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: cards and actions held one by one.
# ---------------------------------------------------------------------


class SliceBoardRegistry:
    """An in-memory holding of board cards and actions.

    The registry is the pure layer's model of a
    session's board: cards are held under their
    slice ids, one card per slice and per
    position, in board order, and actions are
    held in recorded order, each judged against
    the effective board it lands on before it is
    held, so an illegal act holds nothing.
    Holding is data only - no card held here
    runs its slice's build or banks it.
    """

    def __init__(self, board: Any = None) -> None:
        self._cards: List[BoardCard] = []
        self._actions: List[BoardAction] = []
        self._title: Optional[str] = None
        if board is not None:
            self.register_board(board)

    def title(self) -> Optional[str]:
        return self._title

    def _fresh_action_id(self, held_ids: Any) -> str:
        n = 1
        while f"act-{n}" in held_ids:
            n += 1
        return f"act-{n}"

    def _check_card_free(self, card: BoardCard) -> None:
        for held in self._cards:
            if held.slice_id == card.slice_id:
                raise ValueError(
                    f"a card already stands for slice "
                    f"{card.slice_id!r}")
            if held.position == card.position:
                raise ValueError(
                    f"a card already stands at position "
                    f"{card.position} - the board holds one "
                    f"slice per place")

    def register_card(self, card: Any) -> BoardCard:
        """Hold one card, judged whole before it is held."""
        validated = _check_card_ref(card)
        self._check_card_free(validated)
        self._cards.append(validated)
        self._cards.sort(key=lambda c: c.position)
        return validated

    def _check_action_stands(self, action: BoardAction) -> None:
        for held in self._actions:
            if action.action_id is not None and (
                    held.action_id == action.action_id):
                raise ValueError(
                    f"an action already stands under id "
                    f"{action.action_id!r}")
            if held.seq == action.seq:
                raise ValueError(
                    f"an action already stands at sequence "
                    f"{action.seq} - the board holds one "
                    f"act per place")
        # The act must stand legally on the board
        # it lands on, judged before it is held.
        effective_cards(
            self._cards, tuple(self._actions) + (action,))

    def register_action(self, action: Any) -> BoardAction:
        """Hold one hand action, judged whole first.

        The action is judged against the effective
        board it lands on before it is held - an
        illegal act (advancing a paused slice,
        pausing a banked one, re-ordering a struck
        one) refuses and holds nothing new.
        """
        validated = _check_action_ref(action)
        self._check_action_stands(validated)
        if validated.action_id is None:
            validated = BoardAction(
                action_id=self._fresh_action_id(
                    {a.action_id for a in self._actions}),
                seq=validated.seq, kind=validated.kind,
                slice_id=validated.slice_id,
                detail=validated.detail,
                target_position=validated.target_position,
                target_column=validated.target_column,
                recorded_on=validated.recorded_on,
                actor=validated.actor, source=validated.source,
                origin_session=validated.origin_session)
        self._actions.append(validated)
        self._actions.sort(key=lambda a: a.seq)
        return validated

    def register_board(self, board: Any) -> SliceBoard:
        """Hold a whole board, judged whole first."""
        validated = build_board(board)
        for card in validated.cards:
            self._check_card_free(card)
        if self._title is None:
            self._title = validated.title
        elif validated.title != self._title:
            raise ValueError(
                "a second board under a different title refuses - "
                "one board stands in one registry")
        for card in validated.cards:
            self._cards.append(card)
        self._cards.sort(key=lambda c: c.position)
        for action in validated.actions:
            self.register_action(action)
        return self.board()

    def get_card(self, slice_id: Any) -> BoardCard:
        """The effective card one slice id names (KeyError)."""
        wanted = _check_slice_id(slice_id)
        for card in self.effective_cards():
            if card.slice_id == wanted:
                return card
        raise KeyError(f"no card named {wanted!r} stands held")

    def get_base_card(self, slice_id: Any) -> BoardCard:
        """The held (base) card one slice id names (KeyError)."""
        wanted = _check_slice_id(slice_id)
        for card in self._cards:
            if card.slice_id == wanted:
                return card
        raise KeyError(f"no card named {wanted!r} stands held")

    def get_action(self, action_id: Any) -> BoardAction:
        """The action one id names (KeyError if absent)."""
        wanted = _check_word(action_id, "an action id")
        for action in self._actions:
            if action.action_id == wanted:
                return action
        raise KeyError(f"no action named {wanted!r} stands held")

    def latest_action(self) -> BoardAction:
        """The last action recorded (KeyError if none)."""
        if not self._actions:
            raise KeyError("no action stands held")
        return self._actions[-1]

    def list_cards(self) -> Tuple[BoardCard, ...]:
        return tuple(self._cards)

    def list_actions(self) -> Tuple[BoardAction, ...]:
        return tuple(self._actions)

    def effective_cards(self) -> Tuple[BoardCard, ...]:
        return effective_cards(self._cards, tuple(self._actions))

    def board(self) -> SliceBoard:
        return SliceBoard(
            title=self._title or "Slice Board",
            cards=tuple(self._cards),
            actions=tuple(self._actions))

    def panel(self) -> BoardPanel:
        return derive_panel(self.board())

    def verdict(self) -> BoardVerdict:
        return derive_verdict(self.board())


def cards_in_column(source: Any, column: Any) -> Tuple[BoardCard, ...]:
    """The effective cards of one column, in board order."""
    wanted = normalize_column(column)
    return tuple(
        c for c in _held_cards(source) if c.column == wanted)


def total_cards(source: Any) -> int:
    """How many cards a source holds, effectively."""
    return len(_held_cards(source))


# ---------------------------------------------------------------------
# Session news, plain words, and the screens.
# ---------------------------------------------------------------------


def card_record(card: Any) -> Dict[str, Any]:
    """The session-news record of one board card."""
    current = _check_card_ref(card)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Slice board over {current.slice_id}: "
        f"{line_of(current)}.")
    return record_out


def action_record(action: Any) -> Dict[str, Any]:
    """The session-news record of one board action."""
    current = _check_action_ref(action)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Slice board hand action on {current.slice_id}: "
        f"{current.kind} - {current.detail}")
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived panel."""
    current = validate_panel(panel, source)
    record = current.to_record()
    record["news"] = True
    columns = ", ".join(
        f"{c.column} {c.items}" for c in current.column_counts)
    record["headline"] = (
        f"Slice board panel as of {current.as_of}: "
        f"{current.total_cards} slices - {current.total_queued} "
        f"queued, {current.total_building} building, "
        f"{current.total_verifying} verifying, "
        f"{current.total_banked} banked ({columns}); next "
        f"stands {current.next_slice_id or 'none'}.")
    return record


def verdict_record(verdict: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived verdict."""
    current = validate_verdict(verdict, source)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Slice board verdict: {current.verdict} - "
        f"{current.total_banked} of {current.total_cards} "
        f"slices banked, {current.total_building} building "
        f"and {current.total_verifying} verifying, from "
        f"{current.earliest_on} to {current.latest_on}.")
    return record


def board_record(board: Any) -> Dict[str, Any]:
    """The session-news record of one slice board."""
    current = board if isinstance(board, SliceBoard) else build_board(board)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Slice board {current.title}: "
        f"{record['card_count']} slices named, "
        f"{record['action_count']} hand actions held.")
    return record


def plain_words(card: Any) -> str:
    """One card, in one plain sentence."""
    current = _check_card_ref(card)
    flags = ""
    if current.paused:
        flags += " It stands paused by hand."
    if current.struck:
        flags += " It stands struck by hand."
    return (
        f"{line_of(current)} - slice {current.slice_id} "
        f"of part {current.part}, standing "
        f"{current.column} at place {current.position} "
        f"on the board, recorded on "
        f"{current.recorded_on}.{flags}")


def action_plain_words(action: Any) -> str:
    """One hand action, in one plain sentence."""
    current = _check_action_ref(action)
    target = ""
    if current.kind == "advance":
        target = f" to {current.target_column}"
    elif current.kind == "reorder":
        target = f" to place {current.target_position}"
    return (
        f"A hand {current.kind} on slice "
        f"{current.slice_id}{target}, recorded on "
        f"{current.recorded_on} by {current.actor}: "
        f"{current.detail} The act moves this board "
        f"alone - the shipped roadmap is untouched.")


def panel_plain_words(source: Any) -> str:
    """The panel in plain words, in full."""
    if isinstance(source, BoardPanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, (SliceBoard, SliceBoardRegistry)):
        panel = derive_panel(source)
        title = source.title if isinstance(source, SliceBoard) else None
    else:
        raise ValueError(f"a slice-board source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Slices, in board order:")
    for row in panel.rows:
        lines.append(
            f"{row.slice_id}: {row.line} "
            f"(part {row.part}, place {row.position}, "
            f"{row.recorded_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def verdict_plain_words(source: Any) -> str:
    """The board verdict in plain words, in full."""
    if isinstance(source, BoardVerdict):
        verdict = validate_verdict(source)
    elif isinstance(source, (SliceBoard, SliceBoardRegistry)):
        verdict = derive_verdict(source)
    else:
        raise ValueError(f"a slice-board source is needed, got {source!r}")
    return (
        f"Slice board verdict: {verdict.verdict} - "
        f"{verdict.total_banked} slices banked, "
        f"{verdict.total_building} building, "
        f"{verdict.total_verifying} verifying and "
        f"{verdict.total_queued} queued, "
        f"{verdict.total_paused} paused by hand and "
        f"{verdict.total_struck} struck by hand, over "
        f"{verdict.distinct_parts} parts, from "
        f"{verdict.earliest_on} to {verdict.latest_on}, "
        f"of {verdict.total_cards} slices - every line "
        f"is derived from its card and its held hand "
        f"actions.")


def _source_board(source: Any) -> SliceBoard:
    if source is None:
        return load_slice_board()
    if isinstance(source, SliceBoardRegistry):
        return source.board()
    if isinstance(source, SliceBoard):
        return source
    if isinstance(source, BoardCard):
        return SliceBoard(title="One board card", cards=(source,))
    raise ValueError(f"a slice board is needed, got {source!r}")


def format_card(card: Any) -> str:
    """One effective card as a screen block."""
    current = _check_card_ref(card)
    lines = [
        f"{current.slice_id}: {line_of(current)}",
        f"Part: {current.part} - Place: {current.position} - "
        f"Column: {current.column} - "
        f"Paused: {'yes' if current.paused else 'no'} - "
        f"Struck: {'yes' if current.struck else 'no'}",
        f"Summary: {current.summary}",
        f"Recorded: on {current.recorded_on} by {current.actor} "
        f"from {current.source} in {current.origin_session}.",
    ]
    return "\n".join(lines)


def format_action(action: Any) -> str:
    """One hand action as a screen block."""
    current = _check_action_ref(action)
    lines = [
        f"{current.action_id or '-'}: {current.kind} "
        f"{current.slice_id}",
        f"Words: {current.detail}",
    ]
    if current.kind == "advance":
        lines.append(f"Target column: {current.target_column}")
    if current.kind == "reorder":
        lines.append(f"Target place: {current.target_position}")
    lines.append(
        f"Recorded: on {current.recorded_on} by {current.actor} "
        f"from {current.source} in {current.origin_session}.")
    return "\n".join(lines)


def format_board(source: Any = None, column: Any = None) -> str:
    """The board as derived lines, in board order.

    By default the lines are the effective
    board's derived lines alone. With ``column``
    only that column's cards stand in the list.
    """
    board = _source_board(source)
    wanted = normalize_column(column) if column is not None else None
    lines = []
    for card in board.effective_cards():
        if wanted is not None and card.column != wanted:
            continue
        lines.append(f"{card.slice_id}: {line_of(card)}")
    if not lines:
        lines.append("No slices stand on the board on that reading.")
    return "\n".join(lines)


def format_panel(source: Any = None) -> str:
    """The panel as a screen block: every row and the account."""
    if isinstance(source, BoardPanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        board = _source_board(source)
        panel = derive_panel(board)
        lines = [f"Panel in {board.title}:"]
    lines.append("Slices, in board order:")
    for row in panel.rows:
        lines.append(
            f"{row.slice_id}: {row.line} - "
            f"part {row.part} at place {row.position} "
            f"({row.recorded_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None) -> str:
    """The verdict as a screen block."""
    if isinstance(source, BoardVerdict):
        verdict = validate_verdict(source)
        title = "the board"
    else:
        board = _source_board(source)
        verdict = derive_verdict(board)
        title = board.title
    return (
        f"Verdict in The Slice Board over {title}: "
        f"{verdict.verdict} - {verdict.total_banked} of "
        f"{verdict.total_cards} slices banked, "
        f"{verdict.total_building} building, "
        f"{verdict.total_verifying} verifying, "
        f"{verdict.total_queued} queued, from "
        f"{verdict.earliest_on} to {verdict.latest_on}.")


def format_slice_board_screen(source: Any = None) -> str:
    """The whole slice-board screen for one board."""
    board = _source_board(source)
    panel = derive_panel(board)
    verdict = derive_verdict(board)
    lines = [
        f"The Slice Board (M-173) - {board.title}",
        format_board(board),
        f"Panel: {panel.total_cards} slices - "
        f"{panel.total_queued} queued, {panel.total_building} "
        f"building, {panel.total_verifying} verifying, "
        f"{panel.total_banked} banked; next stands "
        f"{panel.next_slice_id or 'none'}.",
        f"Verdict: {verdict.verdict}.",
        "A hand action moves this board alone - the "
        "shipped roadmap data is not rewritten here.",
    ]
    return "\n".join(lines)


def parse_slice_board_args(args: Any) -> Tuple[str, Any]:
    """Parse the /sliceboard grammar into (action, target).

    ``""``/``show``/``list`` show the board;
    ``card <slice-id>`` shows one effective card;
    ``column <column>`` shows one column's cards;
    ``action <action-id>`` shows one held hand
    action; ``panel`` and ``verdict`` show the
    derived panel and verdict. Anything else
    raises ValueError carrying the usage line.
    """
    if args is None:
        return ("show", None)
    if not isinstance(args, str):
        raise ValueError(USAGE)
    parts = args.split()
    if not parts or parts == ["show"] or parts == ["list"]:
        return ("show", None)
    if parts[0] == "card" and len(parts) == 2:
        return ("card", _check_slice_id(parts[1]))
    if parts[0] == "column" and len(parts) == 2:
        return ("column", normalize_column(parts[1]))
    if parts[0] == "action" and len(parts) == 2:
        return ("action", _check_word(parts[1], "an action id"))
    if parts == ["panel"]:
        return ("panel", None)
    if parts == ["verdict"]:
        return ("verdict", None)
    raise ValueError(USAGE)
