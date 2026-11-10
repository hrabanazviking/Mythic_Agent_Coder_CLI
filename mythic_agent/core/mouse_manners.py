"""Mouse manners (All-Features roadmap slice M-188).

Part VIII - The Beautiful Face - builds here. The
roadmap's words: *click, drag-select, scroll, and
links that open files at line numbers in the
user's editor.*

What already ships, and what this slice adds:

* The shipped tree already carries pointer roads
  (the Textual screens take clicks, drags and
  scrolls, and the M-187 book even names the
  drag-select act it could not reach by keyboard).
  What nothing held is *mouse manners*, as
  checkable data: one record per gesture, held
  whole with the mouse road that reaches it; the
  gesture guide, derived from those held records;
  and the file links, held as data beside them -
  each naming its file, its line number and the
  user's editor as its target. This slice is that
  book, in its own module.
* A gesture is held whole: the gesture it names,
  the area it lives in (a closed vocabulary -
  chat, terminal, editor, review, settings,
  onboarding, lessons, command palace), its kind
  (a closed vocabulary - click, drag-select,
  scroll, link), the mouse road that reaches it,
  named as data, and its detail. A gesture naming
  no mouse road is held honestly with an empty
  road: it stands unwired, named in its gaps -
  wiring is judged from the held records alone,
  never claimed live.
* The gesture guide is DERIVED at call time from
  the held gestures' roads - never a second
  stored copy that could drift from the gestures
  themselves. A stored guide, wiring verdict or
  coverage judgement on any record refuses by
  name.
* The file links are held as data: a link record
  naming its file, its line number, the editor
  that stands as its target, its title and its
  detail. A book holds at most one link per file
  line. Holding a link opens no file: the rule
  stands as data (:data:`MOUSE_RULE`) and a
  record claiming a live pointer move, a live
  click or a file actually opened refuses BY
  NAME.
* The shipped data file (``mythic_agent/data/
  mouse_manners.yaml``) holds one example book
  in exactly the shape a real gesture file
  takes, a loader reads a gesture file anywhere
  on disk, gestures and views are shaped as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a mouse book for a session and telling
  from it. This layer reaches no live road: it
  moves no pointer, clicks nothing, scrolls
  nothing and opens no file - it holds mouse
  manners as data and tells it.

Honesty rules, enforced here and pinned by tests:

* **Wiring from records alone.** Every wiring
  telling is derived from the held gesture
  records; a claim of a live pointer, a live
  click or an opened file refuses by name.
* **Unwired stands unwired.** A gesture naming
  no mouse road stands unwired, named in its
  gaps - no road is invented for it.
* **The guide is derived, never stored.** The
  gesture guide is derived from the held
  gestures at call time; a stored guide refuses
  by name, so it can never drift.
* **One link per file line.** Two link records
  standing for one file at one line refuse by
  name.
* **The editor target is data alone.** The link
  records hold the target; holding, viewing or
  telling them opens no file and launches no
  editor.
"""

from __future__ import annotations

__all__ = [
    "AREAS",
    "EXAMPLE_ROAD",
    "GESTURES",
    "GUIDE_ACTION",
    "MOUSE_MANNERS_RESOURCE",
    "MOUSE_MANNERS_SCHEMA",
    "MOUSE_MANNERS_SLICE",
    "MOUSE_RULE",
    "PLAIN_EXPLANATION",
    "THE_MOUSE_MANNERS_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "WIRE_WORDS",
    "Any",
    "Dict",
    "List",
    "Optional",
    "GestureRecord",
    "GuideEntry",
    "LinkRecord",
    "MouseBook",
    "MouseGuide",
    "MousePanel",
    "MousePanelRow",
    "MouseRegistry",
    "MouseVerdict",
    "MouseView",
    "WireCount",
    "book_record",
    "build_book",
    "build_gesture",
    "build_link",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "derive_guide",
    "derive_panel",
    "derive_verdict",
    "editor_link",
    "format_book",
    "format_gesture",
    "format_guide",
    "format_link",
    "format_mouse_screen",
    "format_panel",
    "format_road",
    "format_verdict",
    "format_view",
    "gesture_for_road",
    "gesture_gaps",
    "gesture_passes",
    "gesture_plain_words",
    "gesture_record",
    "gestures_for_area",
    "guide_plain_words",
    "guide_record",
    "inspect_mouse_source",
    "link_for_target",
    "link_plain_words",
    "link_record",
    "load_mouse_manners",
    "load_mouse_manners_file",
    "normalize_area",
    "normalize_gesture",
    "normalize_view_filter",
    "panel_plain_words",
    "panel_record",
    "parse_mouse_args",
    "passing_gestures",
    "plain_lines",
    "plain_words",
    "segment_of",
    "shown_gestures",
    "total_gestures",
    "validate_book",
    "validate_gesture",
    "validate_link",
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

MOUSE_MANNERS_SCHEMA = "mythic.mouse_manners/1"
MOUSE_MANNERS_SLICE = "M-188"
THE_MOUSE_MANNERS_SLICE = MOUSE_MANNERS_SLICE
MOUSE_MANNERS_RESOURCE = "mouse_manners.yaml"
GUIDE_ACTION = "guide"
EXAMPLE_ROAD = "click"
WIRE_WORDS = ("wired", "unwired")
AREAS = (
    "chat", "terminal", "editor", "review", "settings",
    "onboarding", "lessons", "command palace")
GESTURES = ("click", "drag-select", "scroll", "link")
VIEW_FILTERS = ("all", "wired", "unwired")
VERDICT_WORDS = ("open", "strained", "shut")
MOUSE_RULE = (
    "mouse manners are held as data alone: "
    "holding, viewing and telling the gestures "
    "move no pointer, click nothing, scroll "
    "nothing and open no file - wiring is judged "
    "from the held records alone, never claimed live")
PLAIN_EXPLANATION = (
    "Mouse manners (M-188): every gesture stands "
    "held with the mouse road that reaches it, the "
    "guide tells from those held roads, and file "
    "links stand held with their line numbers and "
    "the user's editor as target, as data beside them.")
USAGE = (
    "Usage: /mouse | /mouse gesture <gesture-id> | "
    "/mouse road <road> | /mouse area <area> | "
    "/mouse view <view-id> | /mouse link <link-id> | "
    "/mouse guide | /mouse panel | /mouse verdict")

_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_GESTURE_KEYS = frozenset({
    "gesture_id", "seq", "title", "area", "gesture", "road", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_LINK_KEYS = frozenset({
    "link_id", "seq", "path", "line", "editor", "title", "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "wire", "wired", "gaps", "segment",
    "plain_lines", "telling", "verdict", "guide",
    "entries", "coverage", "covered", "uncovered"})
_LIVE_KEYS = (
    "live_mouse", "move_pointer", "moves_pointer",
    "pointer_move", "live_ui", "render_ui",
    "opens_file", "open_file", "opened_file",
    "launches_editor", "launch_editor",
    "executes_link", "follows_link", "live_editor",
    "click_now", "performs_click", "scroll_now",
    "drags_now")


# ---------------------------------------------------------------------
# Small judges, in the sibling shape.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_road(value: Any) -> str:
    """A held mouse road: a gesture named as data, or honestly empty.

    A gesture naming no mouse road is held with an
    empty road and stands unwired in its gaps; a
    road that is not a string at all refuses.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("a road must be a string naming the mouse road")
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


def _check_line(value: Any) -> int:
    number = _check_count(value, "a line number")
    if number < 1:
        raise ValueError("a line number must stand at 1 or later")
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
                f"{what} claims a live mouse road "
                f"({key!r} is named on it): "
                f"{MOUSE_RULE}")
    for key in mapping:
        if key in _DERIVED_KEYS:
            raise ValueError(
                f"{what} carries {key!r}, which is derived from its "
                f"own fields and never stored")
        if key not in allowed:
            raise ValueError(f"{what} carries unknown field {key!r}")


def normalize_area(value: Any) -> str:
    area = _clean_text(value, "an area").lower()
    if area not in AREAS:
        raise ValueError(
            f"area {area!r} is not one of the named areas: "
            + ", ".join(AREAS))
    return area


def normalize_gesture(value: Any) -> str:
    gesture = _clean_text(value, "a gesture kind").lower()
    if gesture not in GESTURES:
        raise ValueError(
            f"gesture {gesture!r} is not one of the held "
            f"kinds: " + ", ".join(GESTURES))
    return gesture


def normalize_view_filter(value: Any) -> str:
    view_filter = _clean_text(value, "a view filter").lower()
    if view_filter not in VIEW_FILTERS:
        raise ValueError(
            f"view filter {view_filter!r} is not one of the held "
            f"filters: " + ", ".join(VIEW_FILTERS))
    return view_filter


# ---------------------------------------------------------------------
# The held gesture: one gesture, with the road that reaches it.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class GestureRecord:
    """One gesture, held as data with its mouse road.

    The gesture names its title, the area it lives
    in - one of the closed area vocabulary - its
    kind, one of the closed gesture vocabulary,
    the mouse road that reaches it, named as data,
    and its detail. A gesture naming no mouse road
    is held with an empty road: it stands unwired,
    named in its gaps, and no road is invented for
    it. The gesture is local data alone - no live
    road stands behind it: holding it clicks
    nothing.
    """

    gesture_id: str
    seq: int
    title: str
    area: str
    gesture: str
    road: str = ""
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "gesture_id", _clean_text(self.gesture_id, "a gesture id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(self, "area", normalize_area(self.area))
        object.__setattr__(self, "gesture", normalize_gesture(self.gesture))
        object.__setattr__(self, "road", _check_road(self.road))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a gesture detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.gesture_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "gesture_id": self.gesture_id, "seq": self.seq,
            "title": self.title, "area": self.area,
            "gesture": self.gesture, "road": self.road,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_gesture_ref(value: Any) -> GestureRecord:
    if not isinstance(value, GestureRecord):
        raise ValueError("a gesture must be a GestureRecord")
    return value


def validate_gesture(gesture: Any) -> GestureRecord:
    return _check_gesture_ref(gesture)


def build_gesture(record: Any = None, **kwargs: Any) -> GestureRecord:
    """Build one held gesture from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, GestureRecord):
        if kwargs:
            raise ValueError("a gesture stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a gesture must be a mapping or a GestureRecord")
    _needed(data, _GESTURE_KEYS, "a gesture")
    return GestureRecord(
        gesture_id=data.get("gesture_id"), seq=data.get("seq"),
        title=data.get("title"), area=data.get("area"),
        gesture=data.get("gesture"), road=data.get("road"),
        detail=data.get("detail"),
        **_provenance(data))


def gesture_gaps(gesture: Any) -> Tuple[str, ...]:
    """The gaps that keep a gesture from the mouse."""
    checked = _check_gesture_ref(gesture)
    return () if checked.road else ("no mouse road",)


def gesture_passes(gesture: Any) -> bool:
    return not gesture_gaps(gesture)


def plain_lines(gesture: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the gesture's own fields."""
    checked = _check_gesture_ref(gesture)
    return (
        f"Gesture: {checked.title}",
        f"Area: {checked.area}",
        f"Road: {checked.road if checked.road else 'none'}",
    )


def segment_of(gesture: Any) -> str:
    checked = _check_gesture_ref(gesture)
    gaps = gesture_gaps(checked)
    return (
        f"{checked.gesture_id}: {checked.title} in area "
        f"'{checked.area}' - gesture: "
        f"'{checked.gesture}' - road: "
        f"'{checked.road if checked.road else 'none'}' - "
        f"detail: '{checked.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held link: a file at a line, with its editor target, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class LinkRecord:
    """One file link, held as data.

    The record names its file, its line number and
    the editor that stands as its target, with its
    title and its detail. One record stands per
    file line in a book. The record is data alone:
    holding it opens no file and launches no
    editor, ever.
    """

    link_id: str
    seq: int
    path: str
    line: int
    editor: str
    title: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "link_id", _clean_text(self.link_id, "a link id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "path", _clean_text(self.path, "a file path"))
        object.__setattr__(self, "line", _check_line(self.line))
        object.__setattr__(
            self, "editor", _clean_text(self.editor, "an editor target"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a link title"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a link detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.link_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "link_id": self.link_id, "seq": self.seq,
            "path": self.path, "line": self.line,
            "editor": self.editor, "title": self.title,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_link_ref(value: Any) -> LinkRecord:
    if not isinstance(value, LinkRecord):
        raise ValueError("a link must be a LinkRecord")
    return value


def validate_link(link: Any) -> LinkRecord:
    return _check_link_ref(link)


def build_link(link: Any = None, **kwargs: Any) -> LinkRecord:
    if link is None:
        data = dict(kwargs)
    elif isinstance(link, LinkRecord):
        if kwargs:
            raise ValueError("a link stands whole or by fields, not both")
        return link
    elif isinstance(link, dict):
        data = dict(link)
        data.update(kwargs)
    else:
        raise ValueError("a link must be a mapping or a LinkRecord")
    _needed(data, _LINK_KEYS, "a link")
    return LinkRecord(
        link_id=data.get("link_id"), seq=data.get("seq"),
        path=data.get("path"), line=data.get("line"),
        editor=data.get("editor"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which gestures a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class MouseView:
    """A view over the book: every gesture, the wired, the rest."""

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


def _check_view_ref(value: Any) -> MouseView:
    if not isinstance(value, MouseView):
        raise ValueError("a view must be a MouseView")
    return value


def validate_view(view: Any) -> MouseView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> MouseView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, MouseView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or a MouseView")
    _needed(data, _VIEW_KEYS, "a view")
    return MouseView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


def inspect_mouse_source(piece: Any) -> Dict[str, Any]:
    """Name what one mouse source piece is, without judging it."""
    if isinstance(piece, GestureRecord):
        return {"kind": "gesture", "gesture_id": piece.gesture_id}
    if isinstance(piece, dict):
        if "gesture_id" in piece:
            return {"kind": "gesture", "gesture_id": piece.get("gesture_id")}
        if "view_id" in piece:
            return {"kind": "view", "view_id": piece.get("view_id")}
        if "link_id" in piece:
            return {"kind": "link", "link_id": piece.get("link_id")}
    return {"kind": "unknown", "gesture_id": None}


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class MousePanelRow:
    item_id: str
    wire: str
    label: str
    segment: str
    recorded_on: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id, "wire": self.wire,
            "label": self.label, "segment": self.segment,
            "recorded_on": self.recorded_on,
        }


def _row_for_gesture(gesture: GestureRecord) -> MousePanelRow:
    return MousePanelRow(
        item_id=gesture.gesture_id,
        wire="wired" if gesture_passes(gesture) else "unwired",
        label=gesture.title, segment=segment_of(gesture),
        recorded_on=gesture.recorded_on)


def _check_row_ref(value: Any) -> MousePanelRow:
    if not isinstance(value, MousePanelRow):
        raise ValueError("a panel row must be a MousePanelRow")
    return value


def validate_row(row: Any, gesture: Any = None) -> MousePanelRow:
    checked = _check_row_ref(row)
    if gesture is not None:
        derived = _row_for_gesture(_check_gesture_ref(gesture))
        if checked != derived:
            raise ValueError(
                f"panel row {checked.item_id!r} does not agree with "
                f"the row derived from its gesture")
    return checked


def build_row(row: Any = None, gesture: Any = None,
              **kwargs: Any) -> MousePanelRow:
    if gesture is not None:
        derived = _row_for_gesture(_check_gesture_ref(gesture))
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            MousePanelRow(**kwargs))
        return validate_row(built, gesture)
    if isinstance(row, MousePanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        wire = _clean_text(data.get("wire"), "a row wire").lower()
        if wire not in WIRE_WORDS:
            raise ValueError(f"row wire {wire!r} is not a held word")
        return MousePanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            wire=wire,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return MousePanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or a MousePanelRow")


@dataclass(frozen=True)
class WireCount:
    wire: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"wire": self.wire, "items": self.items}


def _wire_counts(rows: Tuple[MousePanelRow, ...]
                 ) -> Tuple[WireCount, ...]:
    counts: List[WireCount] = []
    for wire in WIRE_WORDS:
        number = sum(1 for row in rows if row.wire == wire)
        if number:
            counts.append(WireCount(wire=wire, items=number))
    return tuple(counts)


def _panel_account(total_items: int, total_shown: int,
                   passing_shown: int,
                   wire_counts: Tuple[WireCount, ...],
                   view_filter: str, as_of: str) -> Tuple[str, ...]:
    wire_words = ", ".join(
        f"{count.wire} {count.items}"
        for count in wire_counts) or "none"
    return (
        f"The mouse book holds {total_items} gestures as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {wire_words}; {passing_shown} of the shown gestures "
        f"stand wired to the mouse.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its gesture's own fields "
        "- the title, the area it lives in and "
        "the mouse road that honestly reaches it - and no "
        "judgement is stored on any gesture.",
        "Wiring is judged from the held records alone: "
        "a gesture naming no mouse road stands unwired, and the "
        "gesture guide is derived from the held roads, "
        "never stored where it could drift.",
    )


@dataclass(frozen=True)
class MousePanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[MousePanelRow, ...]
    total_items: int
    total_shown: int
    wire_counts: Tuple[WireCount, ...]
    as_of: str
    account: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "panel_id": self.panel_id, "view_id": self.view_id,
            "view_filter": self.view_filter,
            "rows": [row.to_record() for row in self.rows],
            "total_items": self.total_items,
            "total_shown": self.total_shown,
            "wire_counts": [c.to_record() for c in self.wire_counts],
            "as_of": self.as_of, "account": list(self.account),
        }


def _resolve_view(source: Any, view: Any) -> MouseView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, MouseView):
        return view
    return book.view_for(view)


def shown_gestures(source: Any, view: Any = None
                   ) -> Tuple[GestureRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.gestures
    if resolved.view_filter == "wired":
        return tuple(g for g in book.gestures if gesture_passes(g))
    return tuple(g for g in book.gestures if not gesture_passes(g))


def gestures_for_area(source: Any, area: Any
                      ) -> Tuple[GestureRecord, ...]:
    wanted = normalize_area(area)
    return tuple(
        g for g in _source_book(source).gestures if g.area == wanted)


def passing_gestures(source: Any) -> Tuple[GestureRecord, ...]:
    return tuple(
        g for g in _source_book(source).gestures if gesture_passes(g))


def total_gestures(source: Any) -> int:
    return len(_source_book(source).gestures)


def derive_panel(source: Any, view: Any = None) -> MousePanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_gestures(book, resolved)
    rows = tuple(_row_for_gesture(gesture) for gesture in shown)
    counts = _wire_counts(rows)
    as_of = max((g.recorded_on for g in book.gestures), default="")
    passing = sum(1 for g in shown if gesture_passes(g))
    return MousePanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.gestures), total_shown=len(shown),
        wire_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.gestures), len(shown), passing, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> MousePanel:
    if not isinstance(value, MousePanel):
        raise ValueError("a panel must be a MousePanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> MousePanel:
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
                     "total_shown", "wire_counts", "as_of", "account"):
            if getattr(checked, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {checked.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return checked


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> MousePanel:
    if isinstance(panel, MousePanel):
        if kwargs:
            raise ValueError("a panel stands whole or by fields, not both")
        return validate_panel(panel, source)
    if isinstance(panel, dict):
        data = dict(panel)
        data.update(kwargs)
        rows = tuple(build_row(row) for row in data.get("rows") or ())
        counts = tuple(
            WireCount(
                wire=_clean_text(
                    c.get("wire"), "a wire count word").lower(),
                items=_check_count(c.get("items"), "a wire count"))
            for c in data.get("wire_counts") or ()
            if isinstance(c, dict))
        built = MousePanel(
            panel_id=_clean_text(data.get("panel_id"), "a panel id"),
            view_id=data.get("view_id"),
            view_filter=normalize_view_filter(data.get("view_filter")),
            rows=rows,
            total_items=_check_count(
                data.get("total_items"), "a total_items count"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            wire_counts=counts,
            as_of=_clean_text(data.get("as_of"), "an as_of day"),
            account=_check_lines(data.get("account"), "the account"))
        return validate_panel(built, source)
    if panel is None and source is not None:
        return derive_panel(source, kwargs.get("view"))
    raise ValueError("a panel must be a mapping, a MousePanel, or derived")


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
class MouseVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> MouseVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_gestures(book, resolved)
    passing = sum(1 for g in shown if gesture_passes(g))
    latest = max((g.recorded_on for g in shown), default="")
    return MouseVerdict(
        verdict=_verdict_word(len(shown), passing),
        view_id=resolved.view_id, total_shown=len(shown),
        passing_shown=passing, latest_on=latest)


def _check_verdict_ref(value: Any) -> MouseVerdict:
    if not isinstance(value, MouseVerdict):
        raise ValueError("a verdict must be a MouseVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> MouseVerdict:
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
                  **kwargs: Any) -> MouseVerdict:
    if isinstance(verdict, MouseVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = MouseVerdict(
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
        "a verdict must be a mapping, a MouseVerdict, or derived")


# ---------------------------------------------------------------------
# The guide: derived from the held gestures' roads at call time, and
# the link roads: which file links the book holds, derived too.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class GuideEntry:
    road: str
    gesture_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "road": self.road, "gesture_id": self.gesture_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class MouseGuide:
    """The gesture guide, derived from the held gestures.

    The guide names one entry per wired gesture, in
    held order - the gesture's own road, its id and
    its title - and the gestures that stand
    unwired, named in its gaps. Nothing here is
    stored on any gesture: the guide is derived at
    call time from the held records alone, so it
    can never drift from them.
    """

    entries: Tuple[GuideEntry, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "entries": [e.to_record() for e in self.entries],
            "gaps": list(self.gaps),
        }


def derive_guide(source: Any) -> MouseGuide:
    """Derive the gesture guide from the book's held gestures."""
    book = _source_book(source)
    entries = tuple(
        GuideEntry(road=g.road, gesture_id=g.gesture_id, title=g.title)
        for g in book.gestures if gesture_passes(g))
    gaps = tuple(
        g.gesture_id for g in book.gestures if not gesture_passes(g))
    return MouseGuide(entries=entries, gaps=gaps)


def gesture_for_road(source: Any, road: Any) -> Optional[GestureRecord]:
    """The first held gesture one road reaches, or none - honestly."""
    wanted = _check_road(road)
    if not wanted:
        return None
    for gesture in _source_book(source).gestures:
        if gesture.road == wanted:
            return gesture
    return None


def link_for_target(source: Any, path: Any,
                    line: Any = None) -> Optional[LinkRecord]:
    """The held link for one file (and line, when named), or none."""
    wanted = _clean_text(path, "a file path")
    for record in _source_book(source).links:
        if record.path == wanted and (
                line is None or record.line == _check_line(line)):
            return record
    return None


def editor_link(source: Any) -> Optional[LinkRecord]:
    """The first held file link, standing for the editor road, or none."""
    links = _source_book(source).links
    return links[0] if links else None


# ---------------------------------------------------------------------
# The book: gestures, views and links held together, one pinned panel
# at most per telling, and no verdict or guide ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class MouseBook:
    title: str
    gestures: Tuple[GestureRecord, ...] = ()
    views: Tuple[MouseView, ...] = ()
    links: Tuple[LinkRecord, ...] = ()
    panels: Tuple[MousePanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        gestures = tuple(_check_gesture_ref(g) for g in self.gestures)
        views = tuple(_check_view_ref(v) for v in self.views)
        links = tuple(_check_link_ref(m) for m in self.links)
        panels = tuple(_check_panel_ref(p) for p in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for gesture in gestures:
            if gesture.gesture_id in seen_ids:
                raise ValueError(
                    f"two gestures stand under id {gesture.gesture_id!r}")
            if gesture.seq in seen_seqs:
                raise ValueError(
                    f"two gestures stand at sequence {gesture.seq}")
            seen_ids.add(gesture.gesture_id)
            seen_seqs.add(gesture.seq)
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
        link_ids = set()
        link_seqs = set()
        link_targets = set()
        for record in links:
            if record.link_id in link_ids:
                raise ValueError(
                    f"two links stand under id {record.link_id!r}")
            if record.seq in link_seqs:
                raise ValueError(
                    f"two links stand at sequence {record.seq}")
            target = (record.path, record.line)
            if target in link_targets:
                raise ValueError(
                    f"two link records stand for {record.path!r} "
                    f"at line {record.line}: one link stands "
                    f"per file line")
            link_ids.add(record.link_id)
            link_seqs.add(record.seq)
            link_targets.add(target)
        object.__setattr__(
            self, "gestures", tuple(sorted(gestures, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "links", tuple(sorted(links, key=lambda m: m.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.gestures + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.gesture_id for g in self.gestures) + tuple(
            v.view_id for v in self.views)

    def gesture_ids(self) -> Tuple[str, ...]:
        return tuple(g.gesture_id for g in self.gestures)

    def gesture_for(self, gesture_id: Any) -> GestureRecord:
        wanted = _clean_text(gesture_id, "a gesture id")
        for gesture in self.gestures:
            if gesture.gesture_id == wanted:
                return gesture
        raise KeyError(f"no gesture named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> MouseView:
        wanted = _clean_text(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view named {wanted!r} stands in this book")

    def link_for(self, link_id: Any) -> LinkRecord:
        wanted = _clean_text(link_id, "a link id")
        for record in self.links:
            if record.link_id == wanted:
                return record
        raise KeyError(f"no link named {wanted!r} stands in this book")

    def item_for(self, item_id: Any) -> Any:
        wanted = _clean_text(item_id, "an item id")
        for gesture in self.gestures:
            if gesture.gesture_id == wanted:
                return gesture
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "gestures": [g.to_record() for g in self.gestures],
            "views": [v.to_record() for v in self.views],
            "links": [m.to_record() for m in self.links],
            "panels": [p.to_record() for p in self.panels],
        }


def _judge_book_panels(book: MouseBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: MouseBook) -> None:
    if book.title != "Mouse manners at the M-187 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.gestures) != 6 or len(book.views) != 2:
        raise ValueError(
            "the shipped example book must hold six gestures and two views")
    if len(book.links) != 2:
        raise ValueError(
            "the shipped example book must hold two link records")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m187-boundary":
        raise ValueError("the pinned panel is panel-m187-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "strained" or verdict.passing_shown != 5:
        raise ValueError(
            "the shipped example book's verdict must stand strained "
            "at five wired of six")
    guide = derive_guide(book)
    if [e.road for e in guide.entries] != [
            "click", "left click", "drag", "wheel", "left click"]:
        raise ValueError(
            "the shipped example book's guide must derive the "
            "five held roads in held order")
    if guide.gaps != ("gesture-touch-pan",):
        raise ValueError(
            "the shipped example book must leave the touch-pan "
            "gesture honestly unwired, named in its gaps")
    found = gesture_for_road(book, EXAMPLE_ROAD)
    if found is None or found.gesture_id != "gesture-open-file-link":
        raise ValueError(
            "the shipped example book must reach its file-link "
            "gesture under the example road")
    first = editor_link(book)
    if first is None or first.link_id != "link-terminal-help":
        raise ValueError(
            "the shipped example book must hold the terminal help "
            "link as its first editor link")


def validate_book(data: Any, *, require_example: bool = False) -> MouseBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, MouseBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a mouse book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live mouse road "
                f"({key!r} is named on it): {MOUSE_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its gestures under a view")
    if "gesture_guide" in data or "guides" in data:
        raise ValueError(
            "a book stores no guide: the guide is derived from "
            "its held gestures at call time")
    if data.get("schema") is not None and (
            data["schema"] != MOUSE_MANNERS_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{MOUSE_MANNERS_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != MOUSE_MANNERS_SLICE):
        raise ValueError(
            f"a book's slice must be {MOUSE_MANNERS_SLICE!r}")
    guide = data.get("guide") or {}
    if not isinstance(guide, dict):
        raise ValueError("a book's guide must be a mapping")
    title = guide.get("title") or data.get("title")
    gestures = tuple(build_gesture(g) for g in data.get("gestures") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    links = tuple(build_link(m) for m in data.get("links") or ())
    book = MouseBook(
        title=title, gestures=gestures, views=views, links=links, panels=())
    panels = tuple(
        build_panel(p, book) for p in data.get("panels") or ())
    book = MouseBook(
        title=book.title, gestures=book.gestures, views=book.views,
        links=book.links, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> MouseBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (MouseBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or a MouseBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> MouseBook:
    return validate_book(data, require_example=require_example)


def load_mouse_manners(
        data: Optional[Dict[str, Any]] = None) -> MouseBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(MOUSE_MANNERS_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_mouse_manners_file(path: Any) -> MouseBook:
    """Load one gesture file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: gestures and views held one by one.
# ---------------------------------------------------------------------

class MouseRegistry:
    """An in-memory holding of gestures and views.

    The registry is the pure layer's model of a
    session's mouse book: gestures are held under
    their ids, one gesture per id and per
    sequence, and views are held in recorded
    order, one view per sequence and per id.
    Holding is data only - nothing held here moves
    a pointer, clicks anything, or opens a file.
    """

    def __init__(self, book: Any = None) -> None:
        self._gestures: List[GestureRecord] = []
        self._views: List[MouseView] = []
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

    def register_gesture(self, item: Any) -> GestureRecord:
        """Hold one gesture, judged whole before held."""
        checked = _check_gesture_ref(item)
        return self._register(
            self._gestures, checked, "gesture_id", "gesture")

    def register_view(self, view: Any) -> MouseView:
        """Hold one view; a view naming no id takes a fresh one."""
        checked = _check_view_ref(view)
        if not checked.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            checked = build_view({**checked.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, checked, "view_id", "view")

    def register_book(self, book: Any) -> MouseBook:
        """Hold a whole book's gestures and views, under its title."""
        checked = build_book(book)
        if self._title is not None and checked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {checked.title!r}")
        for gesture in checked.gestures:
            self.register_gesture(gesture)
        for view in checked.views:
            self.register_view(view)
        self._title = checked.title
        return self.book()

    def book(self) -> MouseBook:
        return MouseBook(
            title=self._title or "An unheld mouse book",
            gestures=tuple(self._gestures), views=tuple(self._views),
            links=(), panels=())

    def list_gestures(self) -> Tuple[GestureRecord, ...]:
        return tuple(self._gestures)

    def list_views(self) -> Tuple[MouseView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._gestures) + tuple(self._views)

    def get_gesture(self, gesture_id: Any) -> GestureRecord:
        return self.book().gesture_for(gesture_id)

    def get_view(self, view_id: Any) -> MouseView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records shaped for the journal road.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> MouseBook:
    if source is None:
        return load_mouse_manners()
    if isinstance(source, MouseBook):
        return source
    if isinstance(source, MouseRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def gesture_record(gesture: Any, source: Any = None) -> Dict[str, Any]:
    checked = _check_gesture_ref(gesture)
    record = {
        "type": "mouse_gesture",
        "slice": MOUSE_MANNERS_SLICE,
        "gesture_id": checked.gesture_id,
        "title": checked.title,
        "segment": segment_of(checked),
        "passes": gesture_passes(checked),
        "gaps": list(gesture_gaps(checked)),
    }
    record.update(_provenance_record(checked))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    checked = _check_view_ref(view)
    record = {
        "type": "mouse_view",
        "slice": MOUSE_MANNERS_SLICE,
        "view_id": checked.view_id, "seq": checked.seq,
        "view_filter": checked.view_filter,
    }
    record.update(_provenance_record(checked))
    return record


def link_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_link_ref(record_in)
    record = {
        "type": "mouse_link",
        "slice": MOUSE_MANNERS_SLICE,
        "link_id": checked.link_id,
        "path": checked.path,
        "line": checked.line,
    }
    record.update(_provenance_record(checked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    checked = validate_panel(panel, source)
    record = {"type": "mouse_panel",
              "slice": MOUSE_MANNERS_SLICE}
    record.update(checked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, MouseVerdict):
        checked = validate_verdict(verdict, source)
    else:
        checked = derive_verdict(_source_book(verdict), view)
    record = {"type": "mouse_verdict",
              "slice": MOUSE_MANNERS_SLICE}
    record.update(checked.to_record())
    return record


def guide_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, MouseGuide):
        guide = source
    else:
        guide = derive_guide(source)
    record = {"type": "mouse_guide",
              "slice": MOUSE_MANNERS_SLICE}
    record.update(guide.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    checked = _source_book(book)
    record = {"type": "mouse_book",
              "slice": MOUSE_MANNERS_SLICE,
              "title": checked.title}
    record.update(checked.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(gesture: Any, source: Any = None) -> str:
    checked = _check_gesture_ref(gesture)
    return (
        f"{checked.title} - in area {checked.area}: "
        f"road {checked.road if checked.road else 'none'}. "
        f"{checked.detail}")


def gesture_plain_words(gesture: Any, source: Any = None) -> str:
    return plain_words(gesture, source)


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The mouse book stands {verdict.verdict}: "
        f"{verdict.passing_shown} of {verdict.total_shown} shown "
        f"gestures stand wired to the mouse.")


def view_plain_words(view: Any) -> str:
    checked = _check_view_ref(view)
    return f"View {checked.view_id}: shows {checked.view_filter} gestures."


def link_plain_words(record_in: Any) -> str:
    checked = _check_link_ref(record_in)
    return (
        f"Link {checked.link_id}: {checked.path} at line "
        f"{checked.line}, for {checked.editor}. {checked.detail}")


def guide_plain_words(source: Any) -> str:
    guide = (source if isinstance(source, MouseGuide)
             else derive_guide(source))
    gaps = ", ".join(guide.gaps) or "none"
    return (
        f"The guide holds {len(guide.entries)} roads for "
        f"{len(guide.entries)} gestures; unwired, named in "
        f"its gaps: {gaps}.")


def format_gesture(gesture: Any, source: Any = None) -> str:
    checked = _check_gesture_ref(gesture)
    lines = [f"{checked.title} ({checked.gesture_id})"]
    lines.extend(plain_lines(checked))
    lines.append(checked.detail)
    if gesture_passes(checked):
        lines.append(
            "This gesture stands wired to the mouse, under "
            "the road its record names.")
    else:
        lines.append(
            "This gesture stands unwired - it names no mouse "
            "road, stands named in its gaps, and no road is "
            "invented for it.")
    return "\n".join(lines)


def format_view(view: Any) -> str:
    checked = _check_view_ref(view)
    return (
        f"View {checked.view_id}: filter {checked.view_filter} - "
        f"{checked.detail}")


def format_link(record_in: Any) -> str:
    checked = _check_link_ref(record_in)
    lines = [
        f"File link {checked.path}:{checked.line} "
        f"({checked.link_id}): {checked.title}. {checked.detail}"]
    lines.append(
        "This link stands held as data alone - holding "
        "or reading it opens no file and launches no editor.")
    return "\n".join(lines)


def format_road(source: Any, road: Any) -> str:
    gesture = gesture_for_road(source, road)
    if gesture is not None:
        return format_gesture(gesture)
    wanted = _check_road(road)
    return (
        f"No held gesture stands under road {wanted!r} yet - the "
        f"road reaches nothing in this book, and no gesture is "
        f"invented for it.")


def format_book(source: Any = None, area: Any = None) -> str:
    book = _source_book(source)
    gestures = (gestures_for_area(book, area)
                if area is not None else book.gestures)
    lines = [f"Mouse Manners (M-188) - {book.title}"]
    lines.extend(segment_of(gesture) for gesture in gestures)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Mouse panel under view {panel.view_id}:"]
    lines.extend(row.segment for row in panel.rows)
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return verdict_plain_words(source, view) + (
        f" (view {verdict.view_id}, as of {verdict.latest_on})")


def format_guide(source: Any = None) -> str:
    book = _source_book(source)
    guide = derive_guide(book)
    lines = ["Gesture guide, derived from the held gestures:"]
    for entry in guide.entries:
        lines.append(f"{entry.road} - {entry.title} ({entry.gesture_id})")
    if guide.gaps:
        lines.append(
            "Unwired to the mouse, named honestly: "
            + ", ".join(guide.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "moves no pointer and opens no file.")
    return "\n".join(lines)


def format_mouse_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "Mouse Manners (M-188)",
        f"{book.title}: {len(book.gestures)} gestures held, "
        f"{len(passing_gestures(book))} gestures standing wired, "
        f"{len(book.links)} file links held.",
    ]
    if book.views:
        panel = derive_panel(book, book.views[0])
        lines.append(
            f"{panel.total_shown} of {panel.total_items} items show "
            f"under the first view.")
        lines.extend(row.segment for row in panel.rows)
    lines.append(guide_plain_words(book))
    lines.append(PLAIN_EXPLANATION)
    return "\n".join(lines)


def parse_mouse_args(args: Any) -> Tuple[str, Any]:
    """Parse the /mouse grammar into (action, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("gesture", "view", "link"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("road", "area"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("guide", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
