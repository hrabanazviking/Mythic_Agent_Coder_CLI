"""Session gallery (All-Features roadmap slice M-189).

Part VIII - The Beautiful Face - builds here. The
roadmap's words: *past sessions as browsable cards
(task, outcome, cost, duration) with resume/fork/
export - history as a library, not a log file.*

What already ships, and what this slice adds:

* The shipped tree already carries session records
  (the session store and its journal) and roads
  that fork or resume a live session. What nothing
  held is *the gallery*: past sessions as browsable
  cards, held as checkable data - one card per
  past session, held whole with its task, its
  outcome, its cost and its duration, and the
  resume road that reaches it; the gallery index,
  derived from those held cards; and the action
  roads, held as data beside them - resume, fork
  and export named as roads, never travelled by
  this layer. This slice is that book, in its
  own module.
* A card is held whole: the task the session
  worked, its outcome (a closed vocabulary -
  completed, failed, stopped, abandoned), its
  cost and its duration - held honestly, an
  unknown cost or duration standing empty, never
  invented - the resume road that reaches it,
  named as data, and its detail. A card naming
  no resume road is held honestly with an empty
  road: it stands unresumable, named in its
  gaps - resumability is judged from the held
  records alone, never claimed live.
* The gallery index is DERIVED at call time from
  the held cards - never a second stored copy
  that could drift from the cards themselves.
  A stored index, resumability verdict or
  coverage judgement on any record refuses by
  name.
* The action roads are held as data: an action
  record naming its session, its action - resume,
  fork or export, a closed vocabulary - and the
  target the road stands toward. A book holds at
  most one action record per session road.
  Holding a road travels none of it: the rule
  stands as data (:data:`GALLERY_RULE`) and a
  record claiming a session actually resumed,
  forked or exported refuses BY NAME.
* The shipped data file (``mythic_agent/data/
  session_gallery.yaml``) holds one example book
  in exactly the shape a real gallery file takes,
  a loader reads a gallery file anywhere on disk,
  cards and views are shaped as session news, and
  a small in-memory registry holds records one by
  one. The agent layer owns holding a gallery
  book for a session and telling from it. This
  layer reaches no live road: it resumes no
  session, forks nothing, exports nothing and
  opens no network - it holds the gallery as
  data and tells it.

Honesty rules, enforced here and pinned by tests:

* **Resumability from records alone.** Every
  resumability telling is derived from the held
  card records; a claim of a live resume, fork
  or export refuses by name.
* **Unresumable stands unresumable.** A card
  naming no resume road stands unresumable,
  named in its gaps - no road is invented for it.
* **Unknown stays unknown.** A cost or duration
  that is not known stands empty on its card -
  no figure is invented for it.
* **The index is derived, never stored.** The
  gallery index is derived from the held cards
  at call time; a stored index refuses by name,
  so it can never drift.
* **One card per session.** Two cards standing
  for one session id refuse by name, and one
  action record stands per session road.
* **The action roads are data alone.** The
  records hold the roads; holding, viewing or
  telling them resumes, forks and exports
  nothing.
"""

from __future__ import annotations

__all__ = [
    "OUTCOMES",
    "EXAMPLE_ROAD",
    "ACTIONS",
    "INDEX_ACTION",
    "SESSION_GALLERY_RESOURCE",
    "SESSION_GALLERY_SCHEMA",
    "SESSION_GALLERY_SLICE",
    "GALLERY_RULE",
    "PLAIN_EXPLANATION",
    "THE_SESSION_GALLERY_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "ROAD_WORDS",
    "Any",
    "Dict",
    "List",
    "Optional",
    "SessionCard",
    "IndexEntry",
    "ActionRecord",
    "GalleryBook",
    "GalleryIndex",
    "GalleryPanel",
    "GalleryPanelRow",
    "SessionGalleryRegistry",
    "GalleryVerdict",
    "GalleryView",
    "RoadCount",
    "book_record",
    "build_book",
    "build_card",
    "build_action",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "first_action",
    "format_book",
    "format_card",
    "format_index",
    "format_action",
    "format_gallery_screen",
    "format_panel",
    "format_road",
    "format_verdict",
    "format_view",
    "card_for_road",
    "card_gaps",
    "card_passes",
    "card_plain_words",
    "card_record",
    "cards_for_outcome",
    "index_plain_words",
    "index_record",
    "inspect_gallery_source",
    "action_for_session",
    "action_plain_words",
    "action_record",
    "load_session_gallery",
    "load_session_gallery_file",
    "normalize_outcome",
    "normalize_action",
    "normalize_view_filter",
    "panel_plain_words",
    "panel_record",
    "parse_gallery_args",
    "passing_cards",
    "plain_lines",
    "plain_words",
    "segment_of",
    "shown_cards",
    "total_cards",
    "validate_book",
    "validate_card",
    "validate_action",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
]

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

SESSION_GALLERY_SCHEMA = "mythic.session_gallery/1"
SESSION_GALLERY_SLICE = "M-189"
THE_SESSION_GALLERY_SLICE = SESSION_GALLERY_SLICE
SESSION_GALLERY_RESOURCE = "session_gallery.yaml"
INDEX_ACTION = "index"
EXAMPLE_ROAD = "resume"
ROAD_WORDS = ("resumable", "unresumable")
OUTCOMES = ("completed", "failed", "stopped", "abandoned")
ACTIONS = ("resume", "fork", "export")
VIEW_FILTERS = ("all", "resumable", "unresumable")
VERDICT_WORDS = ("open", "strained", "shut")
GALLERY_RULE = (
    "session gallery is held as data alone: "
    "holding, viewing and browsing the cards "
    "resumes no session, forks nothing, exports "
    "nothing and opens no network - resumability "
    "is judged from the held records alone, "
    "never claimed live")
PLAIN_EXPLANATION = (
    "Session gallery (M-189): every past session "
    "stands held as a browsable card with its task, "
    "its outcome, its cost and its duration, the "
    "index tells from those held cards, and resume, "
    "fork and export roads stand held as data "
    "beside them.")
USAGE = (
    "Usage: /gallery | /gallery card <card-id> | "
    "/gallery road <road> | /gallery outcome <outcome> | "
    "/gallery view <view-id> | /gallery action <action-id> | "
    "/gallery index | /gallery panel | /gallery verdict")

_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_CARD_KEYS = frozenset({
    "card_id", "seq", "task", "outcome", "cost", "duration",
    "road", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "action_id", "seq", "session_id", "action", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "resumable", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered"})
_LIVE_KEYS = (
    "live_session", "live_gallery", "resumes_session",
    "resume_session", "resumed_session", "forks_session",
    "fork_session", "forked_session", "exports_session",
    "export_session", "exported_session", "opens_session",
    "open_session", "opens_network", "writes_file",
    "write_file", "live_resume", "resume_now",
    "fork_now", "export_now", "performs_resume",
    "performs_fork", "performs_export")


# ---------------------------------------------------------------------
# Small judges, in the sibling shape.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_road(value: Any) -> str:
    """A held gallery road: a card named as data, or honestly empty.

    A card naming no gallery road is held with an
    empty road and stands unresumable in its gaps; a
    road that is not a string at all refuses.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("a road must be a string naming the gallery road")
    return value.strip()


def _check_measure(value: Any, what: str) -> str:
    """A held measure: cost or duration, named as data or honestly empty.

    A session whose cost or duration is not known is
    held with an empty measure: unknown stays
    unknown, and no figure is invented for it. A
    measure that is not a string at all refuses.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{what} must be a string naming it, or empty")
    return value.strip()


def _check_count(value: Any, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{what} must be a whole number")
    if value < 0:
        raise ValueError(f"{what} must not be negative")
    return value


def _check_seq(value: Any, what: str = "a sequence") -> int:
    number = _check_count(value, what)
    if number < 1:
        raise ValueError(f"{what} must stand at 1 or later")
    return number


def _provenance(mapping: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key in _PROVENANCE:
        if key == "recorded_on":
            out[key] = _clean_text(mapping.get(key), "a recorded_on day")
        else:
            out[key] = _clean_text(mapping.get(key), f"a {key}")
    return out


def _needed(mapping: Dict[str, Any], allowed: frozenset,
            what: str) -> None:
    if not isinstance(mapping, dict):
        raise ValueError(f"{what} must be a mapping")
    for key in _LIVE_KEYS:
        if key in mapping:
            raise ValueError(
                f"{what} claims a live gallery road "
                f"({key!r} is named on it): "
                f"{GALLERY_RULE}")
    for key in mapping:
        if key in _DERIVED_KEYS:
            raise ValueError(
                f"{what} carries {key!r}, which is derived from its "
                f"own fields and never stored")
        if key not in allowed:
            raise ValueError(f"{what} carries unknown field {key!r}")


def normalize_outcome(value: Any) -> str:
    outcome = _clean_text(value, "an outcome").lower()
    if outcome not in OUTCOMES:
        raise ValueError(
            f"outcome {outcome!r} is not one of the named outcomes: "
            + ", ".join(OUTCOMES))
    return outcome


def normalize_action(value: Any) -> str:
    action = _clean_text(value, "an action").lower()
    if action not in ACTIONS:
        raise ValueError(
            f"action {action!r} is not one of the held "
            f"actions: " + ", ".join(ACTIONS))
    return action


def normalize_view_filter(value: Any) -> str:
    view_filter = _clean_text(value, "a view filter").lower()
    if view_filter not in VIEW_FILTERS:
        raise ValueError(
            f"view filter {view_filter!r} is not one of the held "
            f"filters: " + ", ".join(VIEW_FILTERS))
    return view_filter


# ---------------------------------------------------------------------
# The held card: one card, with the road that reaches it.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class SessionCard:
    """One card, held as data with its gallery road.

    The card names its title, the outcome it lives
    in - one of the closed outcome vocabulary - its
    kind, one of the closed card vocabulary,
    the gallery road that reaches it, named as data,
    and its detail. A card naming no gallery road
    is held with an empty road: it stands unresumable,
    named in its gaps, and no road is invented for
    it. The card is local data alone - no live
    road stands behind it: holding it clicks
    nothing.
    """

    card_id: str
    seq: int
    task: str
    outcome: str
    cost: str = ""
    duration: str = ""
    road: str = ""
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "card_id", _clean_text(self.card_id, "a card id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "task", _clean_text(self.task, "a task"))
        object.__setattr__(self, "outcome", normalize_outcome(self.outcome))
        object.__setattr__(
            self, "cost", _check_measure(self.cost, "a cost"))
        object.__setattr__(
            self, "duration", _check_measure(self.duration, "a duration"))
        object.__setattr__(self, "road", _check_road(self.road))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a card detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.card_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "card_id": self.card_id, "seq": self.seq,
            "task": self.task, "outcome": self.outcome,
            "cost": self.cost, "duration": self.duration,
            "road": self.road, "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_card_ref(value: Any) -> SessionCard:
    if not isinstance(value, SessionCard):
        raise ValueError("a card must be a SessionCard")
    return value


def validate_card(card: Any) -> SessionCard:
    return _check_card_ref(card)


def build_card(record: Any = None, **kwargs: Any) -> SessionCard:
    """Build one held card from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, SessionCard):
        if kwargs:
            raise ValueError("a card stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a card must be a mapping or a SessionCard")
    _needed(data, _CARD_KEYS, "a card")
    return SessionCard(
        card_id=data.get("card_id"), seq=data.get("seq"),
        task=data.get("task"), outcome=data.get("outcome"),
        cost=data.get("cost"), duration=data.get("duration"),
        road=data.get("road"), detail=data.get("detail"),
        **_provenance(data))


def card_gaps(card: Any) -> Tuple[str, ...]:
    """The gaps that keep a card from the gallery."""
    checked = _check_card_ref(card)
    return () if checked.road else ("no resume road",)


def card_passes(card: Any) -> bool:
    return not card_gaps(card)


def plain_lines(card: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the card's own fields."""
    checked = _check_card_ref(card)
    return (
        f"Card: {checked.task}",
        f"Outcome: {checked.outcome}",
        f"Cost: {checked.cost if checked.cost else 'unknown'}",
        f"Duration: {checked.duration if checked.duration else 'unknown'}",
        f"Road: {checked.road if checked.road else 'none'}",
    )


def segment_of(card: Any) -> str:
    checked = _check_card_ref(card)
    gaps = card_gaps(checked)
    return (
        f"{checked.card_id}: {checked.task} - outcome: "
        f"'{checked.outcome}' - cost: "
        f"'{checked.cost if checked.cost else 'unknown'}' - "
        f"duration: "
        f"'{checked.duration if checked.duration else 'unknown'}' - "
        f"road: '{checked.road if checked.road else 'none'}' - "
        f"detail: '{checked.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held action: a file at a line, with its editor target, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ActionRecord:
    """One file action, held as data.

    The record names its file, its line number and
    the editor that stands as its target, with its
    title and its detail. One record stands per
    file line in a book. The record is data alone:
    holding it opens no file and launches no
    editor, ever.
    """

    action_id: str
    seq: int
    session_id: str
    action: str
    target: str
    title: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "action_id", _clean_text(self.action_id, "a action id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "session_id", _clean_text(self.session_id, "a session id"))
        object.__setattr__(self, "action", normalize_action(self.action))
        object.__setattr__(
            self, "target", _clean_text(self.target, "an action target"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a action title"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a action detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.action_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "action_id": self.action_id, "seq": self.seq,
            "session_id": self.session_id, "action": self.action,
            "target": self.target, "title": self.title,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_action_ref(value: Any) -> ActionRecord:
    if not isinstance(value, ActionRecord):
        raise ValueError("a action must be a ActionRecord")
    return value


def validate_action(action: Any) -> ActionRecord:
    return _check_action_ref(action)


def build_action(action: Any = None, **kwargs: Any) -> ActionRecord:
    if action is None:
        data = dict(kwargs)
    elif isinstance(action, ActionRecord):
        if kwargs:
            raise ValueError("a action stands whole or by fields, not both")
        return action
    elif isinstance(action, dict):
        data = dict(action)
        data.update(kwargs)
    else:
        raise ValueError("a action must be a mapping or a ActionRecord")
    _needed(data, _ACTION_KEYS, "a action")
    return ActionRecord(
        action_id=data.get("action_id"), seq=data.get("seq"),
        session_id=data.get("session_id"), action=data.get("action"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which cards a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class GalleryView:
    """A view over the book: every card, the resumable, the rest."""

    view_id: str
    seq: int
    view_filter: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "view_id", _clean_text(self.view_id, "a view id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "view_filter", normalize_view_filter(self.view_filter))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a view detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    def to_record(self) -> Dict[str, Any]:
        record = {
            "view_id": self.view_id, "seq": self.seq,
            "view_filter": self.view_filter, "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_view_ref(value: Any) -> GalleryView:
    if not isinstance(value, GalleryView):
        raise ValueError("a view must be a GalleryView")
    return value


def validate_view(view: Any) -> GalleryView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> GalleryView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, GalleryView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or a GalleryView")
    _needed(data, _VIEW_KEYS, "a view")
    return GalleryView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


def inspect_gallery_source(piece: Any) -> Dict[str, Any]:
    """Name what one gallery source piece is, without judging it."""
    if isinstance(piece, SessionCard):
        return {"kind": "card", "card_id": piece.card_id}
    if isinstance(piece, dict):
        if "card_id" in piece:
            return {"kind": "card", "card_id": piece.get("card_id")}
        if "view_id" in piece:
            return {"kind": "view", "view_id": piece.get("view_id")}
        if "action_id" in piece:
            return {"kind": "action", "action_id": piece.get("action_id")}
    return {"kind": "unknown", "card_id": None}


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class GalleryPanelRow:
    item_id: str
    standing: str
    label: str
    segment: str
    recorded_on: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id, "standing": self.standing,
            "label": self.label, "segment": self.segment,
            "recorded_on": self.recorded_on,
        }


def _row_for_card(card: SessionCard) -> GalleryPanelRow:
    return GalleryPanelRow(
        item_id=card.card_id,
        standing="resumable" if card_passes(card) else "unresumable",
        label=card.task, segment=segment_of(card),
        recorded_on=card.recorded_on)


def _check_row_ref(value: Any) -> GalleryPanelRow:
    if not isinstance(value, GalleryPanelRow):
        raise ValueError("a panel row must be a GalleryPanelRow")
    return value


def validate_row(row: Any, card: Any = None) -> GalleryPanelRow:
    checked = _check_row_ref(row)
    if card is not None:
        derived = _row_for_card(_check_card_ref(card))
        if checked != derived:
            raise ValueError(
                f"panel row {checked.item_id!r} does not agree with "
                f"the row derived from its card")
    return checked


def build_row(row: Any = None, card: Any = None,
              **kwargs: Any) -> GalleryPanelRow:
    if card is not None:
        derived = _row_for_card(_check_card_ref(card))
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            GalleryPanelRow(**kwargs))
        return validate_row(built, card)
    if isinstance(row, GalleryPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in ROAD_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return GalleryPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return GalleryPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or a GalleryPanelRow")


@dataclass(frozen=True)
class RoadCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _road_counts(rows: Tuple[GalleryPanelRow, ...]
                 ) -> Tuple[RoadCount, ...]:
    counts: List[RoadCount] = []
    for standing in ROAD_WORDS:
        number = sum(1 for row in rows if row.standing == standing)
        if number:
            counts.append(RoadCount(standing=standing, items=number))
    return tuple(counts)


def _panel_account(total_items: int, total_shown: int,
                   passing_shown: int,
                   road_counts: Tuple[RoadCount, ...],
                   view_filter: str, as_of: str) -> Tuple[str, ...]:
    standing_words = ", ".join(
        f"{count.standing} {count.items}"
        for count in road_counts) or "none"
    return (
        f"The gallery book holds {total_items} cards as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {passing_shown} of the shown cards "
        f"stand resumable.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its card's own fields "
        "- the task, the outcome, the cost and duration "
        "honestly held and the resume road that honestly "
        "reaches it - and no judgement is stored on any card.",
        "Resumability is judged from the held records alone: "
        "a card naming no resume road stands unresumable, and the "
        "gallery index is derived from the held cards, "
        "never stored where it could drift.",
    )


@dataclass(frozen=True)
class GalleryPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[GalleryPanelRow, ...]
    total_items: int
    total_shown: int
    road_counts: Tuple[RoadCount, ...]
    as_of: str
    account: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "panel_id": self.panel_id, "view_id": self.view_id,
            "view_filter": self.view_filter,
            "rows": [row.to_record() for row in self.rows],
            "total_items": self.total_items,
            "total_shown": self.total_shown,
            "road_counts": [c.to_record() for c in self.road_counts],
            "as_of": self.as_of, "account": list(self.account),
        }


def _resolve_view(source: Any, view: Any) -> GalleryView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, GalleryView):
        return view
    return book.view_for(view)


def shown_cards(source: Any, view: Any = None
                   ) -> Tuple[SessionCard, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.cards
    if resolved.view_filter == "resumable":
        return tuple(g for g in book.cards if card_passes(g))
    return tuple(g for g in book.cards if not card_passes(g))


def cards_for_outcome(source: Any, outcome: Any
                      ) -> Tuple[SessionCard, ...]:
    wanted = normalize_outcome(outcome)
    return tuple(
        g for g in _source_book(source).cards if g.outcome == wanted)


def passing_cards(source: Any) -> Tuple[SessionCard, ...]:
    return tuple(
        g for g in _source_book(source).cards if card_passes(g))


def total_cards(source: Any) -> int:
    return len(_source_book(source).cards)


def derive_panel(source: Any, view: Any = None) -> GalleryPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_cards(book, resolved)
    rows = tuple(_row_for_card(card) for card in shown)
    counts = _road_counts(rows)
    as_of = max((g.recorded_on for g in book.cards), default="")
    passing = sum(1 for g in shown if card_passes(g))
    return GalleryPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.cards), total_shown=len(shown),
        road_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.cards), len(shown), passing, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> GalleryPanel:
    if not isinstance(value, GalleryPanel):
        raise ValueError("a panel must be a GalleryPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> GalleryPanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 lesson).
    """
    checked = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(checked.view_id)
                if checked.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "road_counts", "as_of", "account"):
            if getattr(checked, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {checked.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return checked


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> GalleryPanel:
    if isinstance(panel, GalleryPanel):
        if kwargs:
            raise ValueError("a panel stands whole or by fields, not both")
        return validate_panel(panel, source)
    if isinstance(panel, dict):
        data = dict(panel)
        data.update(kwargs)
        rows = tuple(build_row(row) for row in data.get("rows") or ())
        counts = tuple(
            RoadCount(
                standing=_clean_text(
                    c.get("standing"), "a standing count word").lower(),
                items=_check_count(c.get("items"), "a standing count"))
            for c in data.get("road_counts") or ()
            if isinstance(c, dict))
        built = GalleryPanel(
            panel_id=_clean_text(data.get("panel_id"), "a panel id"),
            view_id=data.get("view_id"),
            view_filter=normalize_view_filter(data.get("view_filter")),
            rows=rows,
            total_items=_check_count(
                data.get("total_items"), "a total_items count"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            road_counts=counts,
            as_of=_clean_text(data.get("as_of"), "an as_of day"),
            account=_check_lines(data.get("account"), "the account"))
        return validate_panel(built, source)
    if panel is None and source is not None:
        return derive_panel(source, kwargs.get("view"))
    raise ValueError("a panel must be a mapping, a GalleryPanel, or derived")


def _check_lines(value: Any, what: str) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError(f"{what} must be a list of lines")
    lines = []
    for line in value:
        lines.append(_clean_text(line, f"a line of {what}"))
    return tuple(lines)


def _verdict_word(total_shown: int, passing_shown: int) -> str:
    if total_shown > 0 and passing_shown == total_shown:
        return "open"
    if passing_shown == 0:
        return "shut"
    return "strained"


@dataclass(frozen=True)
class GalleryVerdict:
    verdict: str
    view_id: Optional[str]
    total_shown: int
    passing_shown: int
    latest_on: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict, "view_id": self.view_id,
            "total_shown": self.total_shown,
            "passing_shown": self.passing_shown,
            "latest_on": self.latest_on,
        }


def derive_verdict(source: Any, view: Any = None) -> GalleryVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_cards(book, resolved)
    passing = sum(1 for g in shown if card_passes(g))
    latest = max((g.recorded_on for g in shown), default="")
    return GalleryVerdict(
        verdict=_verdict_word(len(shown), passing),
        view_id=resolved.view_id, total_shown=len(shown),
        passing_shown=passing, latest_on=latest)


def _check_verdict_ref(value: Any) -> GalleryVerdict:
    if not isinstance(value, GalleryVerdict):
        raise ValueError("a verdict must be a GalleryVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> GalleryVerdict:
    checked = _check_verdict_ref(verdict)
    if checked.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {checked.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(checked.view_id)
                if checked.view_id is not None else None)
        derived = derive_verdict(book, view)
        if checked != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return checked


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> GalleryVerdict:
    if isinstance(verdict, GalleryVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = GalleryVerdict(
            verdict=_clean_text(data.get("verdict"), "a verdict"),
            view_id=data.get("view_id"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            passing_shown=_check_count(
                data.get("passing_shown"), "a passing_shown count"),
            latest_on=_clean_text(data.get("latest_on"), "a latest day"))
        return validate_verdict(built, source)
    if verdict is None and source is not None:
        return derive_verdict(source, kwargs.get("view"))
    raise ValueError(
        "a verdict must be a mapping, a GalleryVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held cards' roads at call time, and
# the action roads: which file actions the book holds, derived too.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    road: str
    card_id: str
    task: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "road": self.road, "card_id": self.card_id,
            "task": self.task,
        }


@dataclass(frozen=True)
class GalleryIndex:
    """The card index, derived from the held cards.

    The index names one entry per resumable card, in
    held order - the card's own road, its id and
    its title - and the cards that stand
    unresumable, named in its gaps. Nothing here is
    stored on any card: the index is derived at
    call time from the held records alone, so it
    can never drift from them.
    """

    entries: Tuple[IndexEntry, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "entries": [e.to_record() for e in self.entries],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> GalleryIndex:
    """Derive the card index from the book's held cards."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(road=g.road, card_id=g.card_id, task=g.task)
        for g in book.cards if card_passes(g))
    gaps = tuple(
        g.card_id for g in book.cards if not card_passes(g))
    return GalleryIndex(entries=entries, gaps=gaps)


def card_for_road(source: Any, road: Any) -> Optional[SessionCard]:
    """The first held card one road reaches, or none - honestly."""
    wanted = _check_road(road)
    if not wanted:
        return None
    for card in _source_book(source).cards:
        if card.road == wanted:
            return card
    return None


def action_for_session(source: Any, session_id: Any,
                       action: Any = None) -> Optional[ActionRecord]:
    """The held action road for one session (and action, when named)."""
    wanted = _clean_text(session_id, "a session id")
    for record in _source_book(source).actions:
        if record.session_id == wanted and (
                action is None
                or record.action == normalize_action(action)):
            return record
    return None


def first_action(source: Any) -> Optional[ActionRecord]:
    """The first held action road, standing for the gallery roads, or none."""
    actions = _source_book(source).actions
    return actions[0] if actions else None


# ---------------------------------------------------------------------
# The book: cards, views and actions held together, one pinned panel
# at most per telling, and no verdict or index ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class GalleryBook:
    title: str
    cards: Tuple[SessionCard, ...] = ()
    views: Tuple[GalleryView, ...] = ()
    actions: Tuple[ActionRecord, ...] = ()
    panels: Tuple[GalleryPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        cards = tuple(_check_card_ref(g) for g in self.cards)
        views = tuple(_check_view_ref(v) for v in self.views)
        actions = tuple(_check_action_ref(m) for m in self.actions)
        panels = tuple(_check_panel_ref(p) for p in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for card in cards:
            if card.card_id in seen_ids:
                raise ValueError(
                    f"two cards stand under id {card.card_id!r}")
            if card.seq in seen_seqs:
                raise ValueError(
                    f"two cards stand at sequence {card.seq}")
            seen_ids.add(card.card_id)
            seen_seqs.add(card.seq)
        view_ids = set()
        view_seqs = set()
        for view in views:
            if view.view_id in view_ids:
                raise ValueError(
                    f"two views stand under id {view.view_id!r}")
            if view.seq in view_seqs:
                raise ValueError(
                    f"two views stand at sequence {view.seq}")
            view_ids.add(view.view_id)
            view_seqs.add(view.seq)
        action_ids = set()
        action_seqs = set()
        action_targets = set()
        for record in actions:
            if record.action_id in action_ids:
                raise ValueError(
                    f"two actions stand under id {record.action_id!r}")
            if record.seq in action_seqs:
                raise ValueError(
                    f"two actions stand at sequence {record.seq}")
            target = (record.session_id, record.action)
            if target in action_targets:
                raise ValueError(
                    f"two action records stand for session "
                    f"{record.session_id!r} under action "
                    f"{record.action!r}: one action stands "
                    f"per session road")
            action_ids.add(record.action_id)
            action_seqs.add(record.seq)
            action_targets.add(target)
        object.__setattr__(
            self, "cards", tuple(sorted(cards, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "actions", tuple(sorted(actions, key=lambda m: m.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.cards + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.card_id for g in self.cards) + tuple(
            v.view_id for v in self.views)

    def card_ids(self) -> Tuple[str, ...]:
        return tuple(g.card_id for g in self.cards)

    def card_for(self, card_id: Any) -> SessionCard:
        wanted = _clean_text(card_id, "a card id")
        for card in self.cards:
            if card.card_id == wanted:
                return card
        raise KeyError(f"no card named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> GalleryView:
        wanted = _clean_text(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view named {wanted!r} stands in this book")

    def action_for(self, action_id: Any) -> ActionRecord:
        wanted = _clean_text(action_id, "a action id")
        for record in self.actions:
            if record.action_id == wanted:
                return record
        raise KeyError(f"no action named {wanted!r} stands in this book")

    def item_for(self, item_id: Any) -> Any:
        wanted = _clean_text(item_id, "an item id")
        for card in self.cards:
            if card.card_id == wanted:
                return card
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "cards": [g.to_record() for g in self.cards],
            "views": [v.to_record() for v in self.views],
            "actions": [m.to_record() for m in self.actions],
            "panels": [p.to_record() for p in self.panels],
        }


def _judge_book_panels(book: GalleryBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: GalleryBook) -> None:
    if book.title != "Session gallery at the M-188 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.cards) != 6 or len(book.views) != 2:
        raise ValueError(
            "the shipped example book must hold six cards and two views")
    if len(book.actions) != 2:
        raise ValueError(
            "the shipped example book must hold two action records")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m188-boundary":
        raise ValueError("the pinned panel is panel-m188-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "strained" or verdict.passing_shown != 5:
        raise ValueError(
            "the shipped example book's verdict must stand strained "
            "at five resumable of six")
    index = derive_index(book)
    if [e.road for e in index.entries] != [
            "resume", "resume from checkpoint", "fork and resume",
            "resume", "resume from checkpoint"]:
        raise ValueError(
            "the shipped example book's index must derive the "
            "five held roads in held order")
    if index.gaps != ("session-abandoned-sweep",):
        raise ValueError(
            "the shipped example book must leave the abandoned "
            "sweep session honestly unresumable, named in its gaps")
    found = card_for_road(book, EXAMPLE_ROAD)
    if found is None or found.card_id != "session-fix-login-redirect":
        raise ValueError(
            "the shipped example book must reach its login "
            "card under the example road")
    first = first_action(book)
    if first is None or first.action_id != "action-resume-login":
        raise ValueError(
            "the shipped example book must hold the login resume "
            "action as its first action road")


def validate_book(data: Any, *, require_example: bool = False) -> GalleryBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, GalleryBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a gallery book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live gallery road "
                f"({key!r} is named on it): {GALLERY_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its cards under a view")
    if "gallery_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held cards at call time")
    if data.get("schema") is not None and (
            data["schema"] != SESSION_GALLERY_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{SESSION_GALLERY_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != SESSION_GALLERY_SLICE):
        raise ValueError(
            f"a book's slice must be {SESSION_GALLERY_SLICE!r}")
    head = data.get("gallery") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's gallery head must be a mapping")
    title = head.get("title") or data.get("title")
    cards = tuple(build_card(g) for g in data.get("cards") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    actions = tuple(build_action(m) for m in data.get("actions") or ())
    book = GalleryBook(
        title=title, cards=cards, views=views, actions=actions, panels=())
    panels = tuple(
        build_panel(p, book) for p in data.get("panels") or ())
    book = GalleryBook(
        title=book.title, cards=book.cards, views=book.views,
        actions=book.actions, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> GalleryBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (GalleryBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or a GalleryBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> GalleryBook:
    return validate_book(data, require_example=require_example)


def load_session_gallery(
        data: Optional[Dict[str, Any]] = None) -> GalleryBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(SESSION_GALLERY_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_session_gallery_file(path: Any) -> GalleryBook:
    """Load one card file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: cards and views held one by one.
# ---------------------------------------------------------------------

class SessionGalleryRegistry:
    """An in-memory holding of cards and views.

    The registry is the pure layer's model of a
    session's gallery book: cards are held under
    their ids, one card per id and per
    sequence, and views are held in recorded
    order, one view per sequence and per id.
    Holding is data only - nothing held here moves
    a pointer, clicks anything, or opens a file.
    """

    def __init__(self, book: Any = None) -> None:
        self._cards: List[SessionCard] = []
        self._views: List[GalleryView] = []
        self._title: Optional[str] = None
        if book is not None:
            self.register_book(book)

    def title(self) -> Optional[str]:
        return self._title

    def _fresh_view_id(self, held_ids: Any) -> str:
        n = 1
        while f"view-{n}" in held_ids:
            n += 1
        return f"view-{n}"

    def _register(self, held: List[Any], item: Any,
                  id_attr: str, what: str) -> Any:
        for other in held:
            if getattr(other, id_attr) == getattr(item, id_attr):
                raise ValueError(
                    f"a {what} already stands under id "
                    f"{getattr(item, id_attr)!r}")
            if other.seq == item.seq:
                raise ValueError(
                    f"a {what} already stands at sequence {item.seq}")
        held.append(item)
        held.sort(key=lambda held_item: held_item.seq)
        return item

    def register_card(self, item: Any) -> SessionCard:
        """Hold one card, judged whole before held."""
        checked = _check_card_ref(item)
        return self._register(
            self._cards, checked, "card_id", "card")

    def register_view(self, view: Any) -> GalleryView:
        """Hold one view; a view naming no id takes a fresh one."""
        checked = _check_view_ref(view)
        if not checked.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            checked = build_view({**checked.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, checked, "view_id", "view")

    def register_book(self, book: Any) -> GalleryBook:
        """Hold a whole book's cards and views, under its title."""
        checked = build_book(book)
        if self._title is not None and checked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {checked.title!r}")
        for card in checked.cards:
            self.register_card(card)
        for view in checked.views:
            self.register_view(view)
        self._title = checked.title
        return self.book()

    def book(self) -> GalleryBook:
        return GalleryBook(
            title=self._title or "An unheld gallery book",
            cards=tuple(self._cards), views=tuple(self._views),
            actions=(), panels=())

    def list_cards(self) -> Tuple[SessionCard, ...]:
        return tuple(self._cards)

    def list_views(self) -> Tuple[GalleryView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._cards) + tuple(self._views)

    def get_card(self, card_id: Any) -> SessionCard:
        return self.book().card_for(card_id)

    def get_view(self, view_id: Any) -> GalleryView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records shaped for the journal road.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> GalleryBook:
    if source is None:
        return load_session_gallery()
    if isinstance(source, GalleryBook):
        return source
    if isinstance(source, SessionGalleryRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def card_record(card: Any, source: Any = None) -> Dict[str, Any]:
    checked = _check_card_ref(card)
    record = {
        "type": "session_card",
        "slice": SESSION_GALLERY_SLICE,
        "card_id": checked.card_id,
        "task": checked.task,
        "segment": segment_of(checked),
        "passes": card_passes(checked),
        "gaps": list(card_gaps(checked)),
    }
    record.update(_provenance_record(checked))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    checked = _check_view_ref(view)
    record = {
        "type": "gallery_view",
        "slice": SESSION_GALLERY_SLICE,
        "view_id": checked.view_id, "seq": checked.seq,
        "view_filter": checked.view_filter,
    }
    record.update(_provenance_record(checked))
    return record


def action_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_action_ref(record_in)
    record = {
        "type": "gallery_action",
        "slice": SESSION_GALLERY_SLICE,
        "action_id": checked.action_id,
        "session_id": checked.session_id,
        "action": checked.action,
    }
    record.update(_provenance_record(checked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    checked = validate_panel(panel, source)
    record = {"type": "gallery_panel",
              "slice": SESSION_GALLERY_SLICE}
    record.update(checked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, GalleryVerdict):
        checked = validate_verdict(verdict, source)
    else:
        checked = derive_verdict(_source_book(verdict), view)
    record = {"type": "gallery_verdict",
              "slice": SESSION_GALLERY_SLICE}
    record.update(checked.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, GalleryIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "gallery_index",
              "slice": SESSION_GALLERY_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    checked = _source_book(book)
    record = {"type": "gallery_book",
              "slice": SESSION_GALLERY_SLICE,
              "title": checked.title}
    record.update(checked.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(card: Any, source: Any = None) -> str:
    checked = _check_card_ref(card)
    return (
        f"{checked.task} - outcome {checked.outcome}: "
        f"cost {checked.cost if checked.cost else 'unknown'}, "
        f"duration {checked.duration if checked.duration else 'unknown'}, "
        f"road {checked.road if checked.road else 'none'}. "
        f"{checked.detail}")


def card_plain_words(card: Any, source: Any = None) -> str:
    return plain_words(card, source)


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The session gallery stands {verdict.verdict}: "
        f"{verdict.passing_shown} of {verdict.total_shown} shown "
        f"cards stand resumable.")


def view_plain_words(view: Any) -> str:
    checked = _check_view_ref(view)
    return f"View {checked.view_id}: shows {checked.view_filter} cards."


def action_plain_words(record_in: Any) -> str:
    checked = _check_action_ref(record_in)
    return (
        f"Action {checked.action_id}: {checked.action} "
        f"{checked.session_id}, toward {checked.target}. "
        f"{checked.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, GalleryIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} roads for "
        f"{len(index.entries)} cards; unresumable, named in "
        f"its gaps: {gaps}.")


def format_card(card: Any, source: Any = None) -> str:
    checked = _check_card_ref(card)
    lines = [f"{checked.task} ({checked.card_id})"]
    lines.extend(plain_lines(checked))
    lines.append(checked.detail)
    if card_passes(checked):
        lines.append(
            "This card stands resumable to the gallery, under "
            "the road its record names.")
    else:
        lines.append(
            "This card stands unresumable - it names no gallery "
            "road, stands named in its gaps, and no road is "
            "invented for it.")
    return "\n".join(lines)


def format_view(view: Any) -> str:
    checked = _check_view_ref(view)
    return (
        f"View {checked.view_id}: filter {checked.view_filter} - "
        f"{checked.detail}")


def format_action(record_in: Any) -> str:
    checked = _check_action_ref(record_in)
    lines = [
        f"Session action {checked.action} {checked.session_id} "
        f"({checked.action_id}): {checked.title}. {checked.detail}"]
    lines.append(
        "This action road stands held as data alone - holding "
        "or reading it resumes no session, forks nothing "
        "and exports nothing.")
    return "\n".join(lines)


def format_road(source: Any, road: Any) -> str:
    card = card_for_road(source, road)
    if card is not None:
        return format_card(card)
    wanted = _check_road(road)
    return (
        f"No held card stands under road {wanted!r} yet - the "
        f"road reaches nothing in this book, and no card is "
        f"invented for it.")


def format_book(source: Any = None, outcome: Any = None) -> str:
    book = _source_book(source)
    cards = (cards_for_outcome(book, outcome)
                if outcome is not None else book.cards)
    lines = [f"Session Gallery (M-189) - {book.title}"]
    lines.extend(segment_of(card) for card in cards)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Gallery panel under view {panel.view_id}:"]
    lines.extend(row.segment for row in panel.rows)
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return verdict_plain_words(source, view) + (
        f" (view {verdict.view_id}, as of {verdict.latest_on})")


def format_index(source: Any = None) -> str:
    book = _source_book(source)
    index = derive_index(book)
    lines = ["Card index, derived from the held cards:"]
    for entry in index.entries:
        lines.append(f"{entry.road} - {entry.task} ({entry.card_id})")
    if index.gaps:
        lines.append(
            "Unresumable to the gallery, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "resumes no session and opens no network.")
    return "\n".join(lines)


def format_gallery_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "Session Gallery (M-189)",
        f"{book.title}: {len(book.cards)} cards held, "
        f"{len(passing_cards(book))} cards standing resumable, "
        f"{len(book.actions)} action roads held.",
    ]
    if book.views:
        panel = derive_panel(book, book.views[0])
        lines.append(
            f"{panel.total_shown} of {panel.total_items} items show "
            f"under the first view.")
        lines.extend(row.segment for row in panel.rows)
    lines.append(index_plain_words(book))
    lines.append(PLAIN_EXPLANATION)
    return "\n".join(lines)


def parse_gallery_args(args: Any) -> Tuple[str, Any]:
    """Parse the /gallery grammar into (action, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("card", "view", "action"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("road", "outcome"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
