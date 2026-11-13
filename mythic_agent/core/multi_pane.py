"""Multi-pane working (All-Features roadmap slice M-192).

Part VIII - The Beautiful Face - builds here. The
roadmap words: *chat, board, files, and terminal
panes in the layouts the field loves - plus the
Mythic layout (board left, work centre, crew
right).*

What already ships, and what this slice adds:

* The face already holds its pieces one by one -
  the chat, the board of slices, the files, the
  terminal - and earlier slices held the work
  view and the slice board as data. What nothing
  held is *the whole working screen as a book*:
  every pane held as checkable data - one card
  per pane, held whole with its title, its kind
  (a closed vocabulary - chat, board, files,
  terminal, work, crew), its width and its height,
  and the target it opens on, named as data; the
  pane index, derived from those held panes; the
  layouts, which show every pane, the anchored
  or the unanchored - among them the field's
  favourite splits and the Mythic layout itself;
  and the notes on panes, held as data beside
  them - note, concern, praise and question named
  as stances, each feeding back to the user as
  data, never posted by this layer. This slice is
  that book, in its own module, standing in the
  M-191 diff theatre final form's book shape.

* A pane is held whole: the title it stands
  under, its kind, its width and its height -
  held honestly, an unknown width or height
  standing empty, never invented - the target
  it opens on, named as data, and its detail.
  A pane naming no target is held honestly with
  an empty target: it stands unanchored, named
  in its gaps - anchoredness is judged from the
  held records alone, never claimed live.
* The pane index is DERIVED at call time from
  the held panes - never a second stored copy
  that could drift from the panes themselves.
  A stored index, anchoredness verdict or
  coverage judgement on any record refuses by
  name.
* The notes are held as data: a note record
  naming its pane, its stance - note, concern,
  praise or question, a closed vocabulary - and
  what it feeds back toward. A book holds at
  most one note record per pane stance. Holding
  a note posts none of it: the rule stands as
  data (:data:`PANE_RULE`) and a record claiming
  a pane was actually opened, focused or resized
  refuses BY NAME.
* The shipped data file holds one example book
  in exactly the shape a real pane file takes,
  a loader reads a pane file anywhere on disk,
  panes and layouts are shaped as session news,
  and a small in-memory registry holds records
  one by one. The agent layer owns holding a
  pane book for a session and telling from it.
  This layer reaches no live road: it opens no
  pane, focuses nothing, resizes nothing and
  opens no network - it holds the working screen
  as data and tells it.

Honesty rules, enforced here and pinned by tests:

* **Anchoredness from records alone.** Every
  anchoredness telling is derived from the held
  pane records; a claim of a live open, focus
  or resize refuses by name.
* **Unanchored stands unanchored.** A pane
  naming no target stands unanchored, named in
  its gaps - no target is invented for it.
* **Unknown stays unknown.** A width or height
  that is not known stands empty on its pane -
  no figure is invented for it.
* **The index is derived, never stored.** The
  pane index is derived from the held panes at
  call time; a stored index refuses by name, so
  it can never drift.
* **One pane per pane.** Two panes standing for
  one pane id refuse by name, and one note
  record stands per pane stance.
* **The notes are data alone.** The records
  hold the feedback; holding, viewing or telling
  them opens nothing, focuses nothing and posts
  nothing.
"""


from __future__ import annotations

__all__ = [
    "KINDS",
    "EXAMPLE_TARGET",
    "STANCES",
    "INDEX_ACTION",
    "MULTI_PANE_RESOURCE",
    "MULTI_PANE_SCHEMA",
    "MULTI_PANE_SLICE",
    "PANE_RULE",
    "PLAIN_EXPLANATION",
    "THE_MULTI_PANE_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "LAYOUT_FILTERS",
    "ANCHOR_WORDS",
    "Any",
    "Dict",
    "List",
    "Optional",
    "PaneCard",
    "IndexEntry",
    "NoteRecord",
    "PaneBook",
    "PaneIndex",
    "PanePanel",
    "PanePanelRow",
    "MultiPaneRegistry",
    "PaneVerdict",
    "PaneLayout",
    "TargetCount",
    "book_record",
    "build_book",
    "build_pane",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_layout",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "first_note",
    "format_book",
    "format_pane",
    "format_index",
    "format_note",
    "format_pane_screen",
    "format_panel",
    "format_target",
    "format_verdict",
    "format_layout",
    "pane_for_target",
    "pane_gaps",
    "pane_passes",
    "pane_plain_words",
    "pane_record",
    "panes_for_kind",
    "index_plain_words",
    "index_record",
    "inspect_pane_source",
    "note_for_pane",
    "note_plain_words",
    "note_record",
    "load_multi_pane",
    "load_multi_pane_file",
    "normalize_kind",
    "normalize_stance",
    "normalize_layout_filter",
    "panel_plain_words",
    "panel_record",
    "parse_pane_args",
    "passing_panes",
    "plain_lines",
    "plain_words",
    "segment_of",
    "shown_panes",
    "total_panes",
    "validate_book",
    "validate_pane",
    "validate_note",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_layout",
    "verdict_plain_words",
    "verdict_record",
    "layout_plain_words",
    "layout_record",
]

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

MULTI_PANE_SCHEMA = "mythic.multi_pane/1"
MULTI_PANE_SLICE = "M-192"
THE_MULTI_PANE_SLICE = MULTI_PANE_SLICE
MULTI_PANE_RESOURCE = "multi_pane.yaml"
INDEX_ACTION = "index"
EXAMPLE_TARGET = "mythic_agent/core/session.py:128"
ANCHOR_WORDS = ("anchored", "unanchored")
KINDS = ("chat", "board", "files", "terminal", "work", "crew")
STANCES = ("note", "concern", "praise", "question")
LAYOUT_FILTERS = ("all", "anchored", "unanchored")
VERDICT_WORDS = ("open", "strained", "shut")
PANE_RULE = (
    "multi-pane working is held as data alone: "
    "holding, viewing and reading the panes "
    "opens no pane, focuses no pane, resizes no "
    "pane and opens no network - pane targets "
    "are judged from the held records alone, "
    "never claimed live")
PLAIN_EXPLANATION = (
    "Multi-pane working (M-192): every pane of "
    "the working screen stands held as a card "
    "with its title, its kind, its width and "
    "height honestly held, the target it opens "
    "on, and the layouts that arrange the panes "
    "- the field's favourite splits and the "
    "Mythic layout, board left, work centre, "
    "crew right.")
USAGE = (
    "Usage: /panes | /panes pane <pane-id> | "
    "/panes target <target> | /panes kind <kind> | "
    "/panes layout <layout-id> | /panes note <note-id> | "
    "/panes index | /panes panel | /panes verdict")

_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_PANE_KEYS = frozenset({
    "pane_id", "seq", "title", "kind", "width", "height",
    "target", "detail",
} | set(_PROVENANCE))
_LAYOUT_KEYS = frozenset({
    "layout_id", "seq", "layout_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "pane_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "anchored", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered"})
_LIVE_KEYS = (
    "live_pane", "live_layout", "opens_pane",
    "open_pane", "opened_pane", "focuses_pane",
    "focused_pane", "resizes_pane", "resized_pane",
    "moves_pane", "moved_pane", "opens_window",
    "opens_network", "writes_file", "write_file",
    "live_focus", "focus_now", "note_now",
    "performs_focus", "performs_note",
    "posts_note", "posted_note")


# ---------------------------------------------------------------------
# Small judges, in the sibling shape.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_target(value: Any) -> str:
    """A held pane target: a pane named as data, or honestly empty.

    A pane naming no pane target is held with an
    empty target and stands unanchored in its gaps; a
    target that is not a string at all refuses.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("a target must be a string naming the pane target")
    return value.strip()


def _check_measure(value: Any, what: str) -> str:
    """A held measure: width or height, named as data or honestly empty.

    A session whose width or height is not known is
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
                f"{what} claims a live pane target "
                f"({key!r} is named on it): "
                f"{PANE_RULE}")
    for key in mapping:
        if key in _DERIVED_KEYS:
            raise ValueError(
                f"{what} carries {key!r}, which is derived from its "
                f"own fields and never stored")
        if key not in allowed:
            raise ValueError(f"{what} carries unknown field {key!r}")


def normalize_kind(value: Any) -> str:
    kind = _clean_text(value, "an kind").lower()
    if kind not in KINDS:
        raise ValueError(
            f"kind {kind!r} is not one of the named kinds: "
            + ", ".join(KINDS))
    return kind


def normalize_stance(value: Any) -> str:
    stance = _clean_text(value, "an stance").lower()
    if stance not in STANCES:
        raise ValueError(
            f"stance {stance!r} is not one of the held "
            f"notes: " + ", ".join(STANCES))
    return stance


def normalize_layout_filter(value: Any) -> str:
    layout_filter = _clean_text(value, "a layout filter").lower()
    if layout_filter not in LAYOUT_FILTERS:
        raise ValueError(
            f"layout filter {layout_filter!r} is not one of the held "
            f"filters: " + ", ".join(LAYOUT_FILTERS))
    return layout_filter


# ---------------------------------------------------------------------
# The held pane: one pane, with the target that reaches it.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class PaneCard:
    """One pane, held as data with its pane target.

    The pane names its title, the kind it lives
    in - one of the closed kind vocabulary - its
    kind, one of the closed pane vocabulary,
    the pane target that reaches it, named as data,
    and its detail. A pane naming no pane target
    is held with an empty target: it stands unanchored,
    named in its gaps, and no target is invented for
    it. The pane is local data alone - no live
    target stands behind it: holding it clicks
    nothing.
    """

    pane_id: str
    seq: int
    title: str
    kind: str
    width: str = ""
    height: str = ""
    target: str = ""
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "pane_id", _clean_text(self.pane_id, "a pane id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a file"))
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "width", _check_measure(self.width, "a width"))
        object.__setattr__(
            self, "height", _check_measure(self.height, "a height"))
        object.__setattr__(self, "target", _check_target(self.target))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a pane detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.pane_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "pane_id": self.pane_id, "seq": self.seq,
            "title": self.title, "kind": self.kind,
            "width": self.width, "height": self.height,
            "target": self.target, "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_pane_ref(value: Any) -> PaneCard:
    if not isinstance(value, PaneCard):
        raise ValueError("a pane must be a PaneCard")
    return value


def validate_pane(pane: Any) -> PaneCard:
    return _check_pane_ref(pane)


def build_pane(record: Any = None, **kwargs: Any) -> PaneCard:
    """Build one held pane from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, PaneCard):
        if kwargs:
            raise ValueError("a pane stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a pane must be a mapping or a PaneCard")
    _needed(data, _PANE_KEYS, "a pane")
    return PaneCard(
        pane_id=data.get("pane_id"), seq=data.get("seq"),
        title=data.get("title"), kind=data.get("kind"),
        width=data.get("width"), height=data.get("height"),
        target=data.get("target"), detail=data.get("detail"),
        **_provenance(data))


def pane_gaps(pane: Any) -> Tuple[str, ...]:
    """The gaps that keep a pane from the pane."""
    checked = _check_pane_ref(pane)
    return () if checked.target else ("no pane target",)


def pane_passes(pane: Any) -> bool:
    return not pane_gaps(pane)


def plain_lines(pane: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the pane's own fields."""
    checked = _check_pane_ref(pane)
    return (
        f"Pane: {checked.title}",
        f"Kind: {checked.kind}",
        f"Width: {checked.width if checked.width else 'unknown'}",
        f"Height: {checked.height if checked.height else 'unknown'}",
        f"Target: {checked.target if checked.target else 'none'}",
    )


def segment_of(pane: Any) -> str:
    checked = _check_pane_ref(pane)
    gaps = pane_gaps(checked)
    return (
        f"{checked.pane_id}: {checked.title} - kind: "
        f"'{checked.kind}' - width: "
        f"'{checked.width if checked.width else 'unknown'}' - "
        f"height: "
        f"'{checked.height if checked.height else 'unknown'}' - "
        f"target: '{checked.target if checked.target else 'none'}' - "
        f"detail: '{checked.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held stance: a file at a line, with its editor target, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One file stance, held as data.

    The record names its file, its line number and
    the editor that stands as its target, with its
    title and its detail. One record stands per
    file line in a book. The record is data alone:
    holding it opens no file and launches no
    editor, ever.
    """

    note_id: str
    seq: int
    pane_id: str
    stance: str
    target: str
    title: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "note_id", _clean_text(self.note_id, "a stance id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "pane_id", _clean_text(self.pane_id, "a session id"))
        object.__setattr__(self, "stance", normalize_stance(self.stance))
        object.__setattr__(
            self, "target", _clean_text(self.target, "an stance target"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a stance title"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a stance detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.note_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "note_id": self.note_id, "seq": self.seq,
            "pane_id": self.pane_id, "stance": self.stance,
            "target": self.target, "title": self.title,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_note_ref(value: Any) -> NoteRecord:
    if not isinstance(value, NoteRecord):
        raise ValueError("a stance must be a NoteRecord")
    return value


def validate_note(stance: Any) -> NoteRecord:
    return _check_note_ref(stance)


def build_note(stance: Any = None, **kwargs: Any) -> NoteRecord:
    if stance is None:
        data = dict(kwargs)
    elif isinstance(stance, NoteRecord):
        if kwargs:
            raise ValueError("a stance stands whole or by fields, not both")
        return stance
    elif isinstance(stance, dict):
        data = dict(stance)
        data.update(kwargs)
    else:
        raise ValueError("a stance must be a mapping or a NoteRecord")
    _needed(data, _ACTION_KEYS, "a stance")
    return NoteRecord(
        note_id=data.get("note_id"), seq=data.get("seq"),
        pane_id=data.get("pane_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held layout: which panes a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class PaneLayout:
    """A layout over the book: every pane, the anchored, the rest."""

    layout_id: str
    seq: int
    layout_filter: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "layout_id", _clean_text(self.layout_id, "a layout id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "layout_filter", normalize_layout_filter(self.layout_filter))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a layout detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    def to_record(self) -> Dict[str, Any]:
        record = {
            "layout_id": self.layout_id, "seq": self.seq,
            "layout_filter": self.layout_filter, "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_layout_ref(value: Any) -> PaneLayout:
    if not isinstance(value, PaneLayout):
        raise ValueError("a layout must be a PaneLayout")
    return value


def validate_layout(layout: Any) -> PaneLayout:
    return _check_layout_ref(layout)


def build_layout(layout: Any = None, **kwargs: Any) -> PaneLayout:
    if layout is None:
        data = dict(kwargs)
    elif isinstance(layout, PaneLayout):
        if kwargs:
            raise ValueError("a layout stands whole or by fields, not both")
        return layout
    elif isinstance(layout, dict):
        data = dict(layout)
        data.update(kwargs)
    else:
        raise ValueError("a layout must be a mapping or a PaneLayout")
    _needed(data, _LAYOUT_KEYS, "a layout")
    return PaneLayout(
        layout_id=data.get("layout_id"), seq=data.get("seq"),
        layout_filter=data.get("layout_filter"), detail=data.get("detail"),
        **_provenance(data))


def inspect_pane_source(piece: Any) -> Dict[str, Any]:
    """Name what one pane source piece is, without judging it."""
    if isinstance(piece, PaneCard):
        return {"kind": "pane", "pane_id": piece.pane_id}
    if isinstance(piece, dict):
        if "note_id" in piece:
            return {"kind": "note", "note_id": piece.get("note_id")}
        if "layout_id" in piece:
            return {"kind": "layout", "layout_id": piece.get("layout_id")}
        if "pane_id" in piece:
            return {"kind": "pane", "pane_id": piece.get("pane_id")}
    return {"kind": "unknown", "pane_id": None}


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class PanePanelRow:
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


def _row_for_pane(pane: PaneCard) -> PanePanelRow:
    return PanePanelRow(
        item_id=pane.pane_id,
        standing="anchored" if pane_passes(pane) else "unanchored",
        label=pane.title, segment=segment_of(pane),
        recorded_on=pane.recorded_on)


def _check_row_ref(value: Any) -> PanePanelRow:
    if not isinstance(value, PanePanelRow):
        raise ValueError("a panel row must be a PanePanelRow")
    return value


def validate_row(row: Any, pane: Any = None) -> PanePanelRow:
    checked = _check_row_ref(row)
    if pane is not None:
        derived = _row_for_pane(_check_pane_ref(pane))
        if checked != derived:
            raise ValueError(
                f"panel row {checked.item_id!r} does not agree with "
                f"the row derived from its pane")
    return checked


def build_row(row: Any = None, pane: Any = None,
              **kwargs: Any) -> PanePanelRow:
    if pane is not None:
        derived = _row_for_pane(_check_pane_ref(pane))
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            PanePanelRow(**kwargs))
        return validate_row(built, pane)
    if isinstance(row, PanePanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in ANCHOR_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return PanePanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return PanePanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or a PanePanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[PanePanelRow, ...]
                 ) -> Tuple[TargetCount, ...]:
    counts: List[TargetCount] = []
    for standing in ANCHOR_WORDS:
        number = sum(1 for row in rows if row.standing == standing)
        if number:
            counts.append(TargetCount(standing=standing, items=number))
    return tuple(counts)


def _panel_account(total_items: int, total_shown: int,
                   passing_shown: int,
                   target_counts: Tuple[TargetCount, ...],
                   layout_filter: str, as_of: str) -> Tuple[str, ...]:
    standing_words = ", ".join(
        f"{count.standing} {count.items}"
        for count in target_counts) or "none"
    return (
        f"The pane book holds {total_items} panes as of "
        f"{as_of}: the layout '{layout_filter}' shows {total_shown} of "
        f"them: {standing_words}; {passing_shown} of the shown panes "
        f"stand anchored.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one layout diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its pane's own fields "
        "- the file, the kind, the width and height "
        "honestly held and the pane target that honestly "
        "reaches it - and no judgement is stored on any pane.",
        "Targetedness is judged from the held records alone: "
        "a pane naming no pane target stands unanchored, and the "
        "pane index is derived from the held panes, "
        "never stored where it could drift.",
    )


@dataclass(frozen=True)
class PanePanel:
    panel_id: str
    layout_id: Optional[str]
    layout_filter: str
    rows: Tuple[PanePanelRow, ...]
    total_items: int
    total_shown: int
    target_counts: Tuple[TargetCount, ...]
    as_of: str
    account: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "panel_id": self.panel_id, "layout_id": self.layout_id,
            "layout_filter": self.layout_filter,
            "rows": [row.to_record() for row in self.rows],
            "total_items": self.total_items,
            "total_shown": self.total_shown,
            "target_counts": [c.to_record() for c in self.target_counts],
            "as_of": self.as_of, "account": list(self.account),
        }


def _resolve_layout(source: Any, layout: Any) -> PaneLayout:
    book = _source_book(source)
    if layout is None:
        if not book.layouts:
            raise ValueError("the book holds no layout to derive under")
        return book.layouts[0]
    if isinstance(layout, PaneLayout):
        return layout
    return book.layout_for(layout)


def shown_panes(source: Any, layout: Any = None
                   ) -> Tuple[PaneCard, ...]:
    book = _source_book(source)
    resolved = _resolve_layout(book, layout)
    if resolved.layout_filter == "all":
        return book.panes
    if resolved.layout_filter == "anchored":
        return tuple(g for g in book.panes if pane_passes(g))
    return tuple(g for g in book.panes if not pane_passes(g))


def panes_for_kind(source: Any, kind: Any
                      ) -> Tuple[PaneCard, ...]:
    wanted = normalize_kind(kind)
    return tuple(
        g for g in _source_book(source).panes if g.kind == wanted)


def passing_panes(source: Any) -> Tuple[PaneCard, ...]:
    return tuple(
        g for g in _source_book(source).panes if pane_passes(g))


def total_panes(source: Any) -> int:
    return len(_source_book(source).panes)


def derive_panel(source: Any, layout: Any = None) -> PanePanel:
    book = _source_book(source)
    resolved = _resolve_layout(book, layout)
    shown = shown_panes(book, resolved)
    rows = tuple(_row_for_pane(pane) for pane in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.panes), default="")
    passing = sum(1 for g in shown if pane_passes(g))
    return PanePanel(
        panel_id=f"panel-{resolved.layout_id}", layout_id=resolved.layout_id,
        layout_filter=resolved.layout_filter, rows=rows,
        total_items=len(book.panes), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.panes), len(shown), passing, counts,
            resolved.layout_filter, as_of))


def _check_panel_ref(value: Any) -> PanePanel:
    if not isinstance(value, PanePanel):
        raise ValueError("a panel must be a PanePanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> PanePanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 lesson).
    """
    checked = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        layout = (book.layout_for(checked.layout_id)
                if checked.layout_id is not None else None)
        derived = derive_panel(book, layout)
        for attr in ("layout_id", "layout_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(checked, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {checked.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return checked


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> PanePanel:
    if isinstance(panel, PanePanel):
        if kwargs:
            raise ValueError("a panel stands whole or by fields, not both")
        return validate_panel(panel, source)
    if isinstance(panel, dict):
        data = dict(panel)
        data.update(kwargs)
        rows = tuple(build_row(row) for row in data.get("rows") or ())
        counts = tuple(
            TargetCount(
                standing=_clean_text(
                    c.get("standing"), "a standing count word").lower(),
                items=_check_count(c.get("items"), "a standing count"))
            for c in data.get("target_counts") or ()
            if isinstance(c, dict))
        built = PanePanel(
            panel_id=_clean_text(data.get("panel_id"), "a panel id"),
            layout_id=data.get("layout_id"),
            layout_filter=normalize_layout_filter(data.get("layout_filter")),
            rows=rows,
            total_items=_check_count(
                data.get("total_items"), "a total_items count"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            target_counts=counts,
            as_of=_clean_text(data.get("as_of"), "an as_of day"),
            account=_check_lines(data.get("account"), "the account"))
        return validate_panel(built, source)
    if panel is None and source is not None:
        return derive_panel(source, kwargs.get("layout"))
    raise ValueError("a panel must be a mapping, a PanePanel, or derived")


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
class PaneVerdict:
    verdict: str
    layout_id: Optional[str]
    total_shown: int
    passing_shown: int
    latest_on: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict, "layout_id": self.layout_id,
            "total_shown": self.total_shown,
            "passing_shown": self.passing_shown,
            "latest_on": self.latest_on,
        }


def derive_verdict(source: Any, layout: Any = None) -> PaneVerdict:
    book = _source_book(source)
    resolved = _resolve_layout(book, layout)
    shown = shown_panes(book, resolved)
    passing = sum(1 for g in shown if pane_passes(g))
    latest = max((g.recorded_on for g in shown), default="")
    return PaneVerdict(
        verdict=_verdict_word(len(shown), passing),
        layout_id=resolved.layout_id, total_shown=len(shown),
        passing_shown=passing, latest_on=latest)


def _check_verdict_ref(value: Any) -> PaneVerdict:
    if not isinstance(value, PaneVerdict):
        raise ValueError("a verdict must be a PaneVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> PaneVerdict:
    checked = _check_verdict_ref(verdict)
    if checked.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {checked.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        layout = (book.layout_for(checked.layout_id)
                if checked.layout_id is not None else None)
        derived = derive_verdict(book, layout)
        if checked != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return checked


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> PaneVerdict:
    if isinstance(verdict, PaneVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = PaneVerdict(
            verdict=_clean_text(data.get("verdict"), "a verdict"),
            layout_id=data.get("layout_id"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            passing_shown=_check_count(
                data.get("passing_shown"), "a passing_shown count"),
            latest_on=_clean_text(data.get("latest_on"), "a latest day"))
        return validate_verdict(built, source)
    if verdict is None and source is not None:
        return derive_verdict(source, kwargs.get("layout"))
    raise ValueError(
        "a verdict must be a mapping, a PaneVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held panes' targets at call time, and
# the stance targets: which file notes the book holds, derived too.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    target: str
    pane_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "target": self.target, "pane_id": self.pane_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class PaneIndex:
    """The pane index, derived from the held panes.

    The index names one entry per anchored pane, in
    held order - the pane's own target, its id and
    its title - and the panes that stand
    unanchored, named in its gaps. Nothing here is
    stored on any pane: the index is derived at
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


def derive_index(source: Any) -> PaneIndex:
    """Derive the pane index from the book's held panes."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(target=g.target, pane_id=g.pane_id, title=g.title)
        for g in book.panes if pane_passes(g))
    gaps = tuple(
        g.pane_id for g in book.panes if not pane_passes(g))
    return PaneIndex(entries=entries, gaps=gaps)


def pane_for_target(source: Any, target: Any) -> Optional[PaneCard]:
    """The first held pane one target reaches, or none - honestly."""
    wanted = _check_target(target)
    if not wanted:
        return None
    for pane in _source_book(source).panes:
        if pane.target == wanted:
            return pane
    return None


def note_for_pane(source: Any, pane_id: Any,
                       stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one session (and stance, when named)."""
    wanted = _clean_text(pane_id, "a session id")
    for record in _source_book(source).notes:
        if record.pane_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the pane targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


# ---------------------------------------------------------------------
# The book: panes, layouts and notes held together, one pinned panel
# at most per telling, and no verdict or index ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class PaneBook:
    title: str
    panes: Tuple[PaneCard, ...] = ()
    layouts: Tuple[PaneLayout, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    panels: Tuple[PanePanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        panes = tuple(_check_pane_ref(g) for g in self.panes)
        layouts = tuple(_check_layout_ref(v) for v in self.layouts)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        panels = tuple(_check_panel_ref(p) for p in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for pane in panes:
            if pane.pane_id in seen_ids:
                raise ValueError(
                    f"two panes stand under id {pane.pane_id!r}")
            if pane.seq in seen_seqs:
                raise ValueError(
                    f"two panes stand at sequence {pane.seq}")
            seen_ids.add(pane.pane_id)
            seen_seqs.add(pane.seq)
        layout_ids = set()
        layout_seqs = set()
        for layout in layouts:
            if layout.layout_id in layout_ids:
                raise ValueError(
                    f"two layouts stand under id {layout.layout_id!r}")
            if layout.seq in layout_seqs:
                raise ValueError(
                    f"two layouts stand at sequence {layout.seq}")
            layout_ids.add(layout.layout_id)
            layout_seqs.add(layout.seq)
        note_ids = set()
        note_seqs = set()
        note_targets = set()
        for record in notes:
            if record.note_id in note_ids:
                raise ValueError(
                    f"two notes stand under id {record.note_id!r}")
            if record.seq in note_seqs:
                raise ValueError(
                    f"two notes stand at sequence {record.seq}")
            target = (record.pane_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for session "
                    f"{record.pane_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per session target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        object.__setattr__(
            self, "panes", tuple(sorted(panes, key=lambda g: g.seq)))
        object.__setattr__(
            self, "layouts", tuple(sorted(layouts, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.panes + self.layouts

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.pane_id for g in self.panes) + tuple(
            v.layout_id for v in self.layouts)

    def pane_ids(self) -> Tuple[str, ...]:
        return tuple(g.pane_id for g in self.panes)

    def pane_for(self, pane_id: Any) -> PaneCard:
        wanted = _clean_text(pane_id, "a pane id")
        for pane in self.panes:
            if pane.pane_id == wanted:
                return pane
        raise KeyError(f"no pane named {wanted!r} stands in this book")

    def layout_for(self, layout_id: Any) -> PaneLayout:
        wanted = _clean_text(layout_id, "a layout id")
        for layout in self.layouts:
            if layout.layout_id == wanted:
                return layout
        raise KeyError(f"no layout named {wanted!r} stands in this book")

    def note_for(self, note_id: Any) -> NoteRecord:
        wanted = _clean_text(note_id, "a stance id")
        for record in self.notes:
            if record.note_id == wanted:
                return record
        raise KeyError(f"no stance named {wanted!r} stands in this book")

    def item_for(self, item_id: Any) -> Any:
        wanted = _clean_text(item_id, "an item id")
        for pane in self.panes:
            if pane.pane_id == wanted:
                return pane
        for layout in self.layouts:
            if layout.layout_id == wanted:
                return layout
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "panes": [g.to_record() for g in self.panes],
            "layouts": [v.to_record() for v in self.layouts],
            "notes": [m.to_record() for m in self.notes],
            "panels": [p.to_record() for p in self.panels],
        }


def _judge_book_panels(book: PaneBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: PaneBook) -> None:
    if book.title != "Multi-pane working at the M-191 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.panes) != 6 or len(book.layouts) != 2:
        raise ValueError("the shipped example book must hold six panes and two layouts")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m191-boundary":
        raise ValueError("the pinned panel is panel-m191-boundary")
    verdict = derive_verdict(book, book.layout_for(panel.layout_id))
    if verdict.verdict != "strained" or verdict.passing_shown != 5:
        raise ValueError("the shipped example book verdict must stand strained at five anchored of six")
    index = derive_index(book)
    if [e.target for e in index.entries] != ["mythic_agent/core/session.py:128", "mythic_agent/core/costs_face.py:12", "tests/test_part7_gate.py:41", "docs/gallery_guide.md:1", "mythic_agent/data/roadmap_slices.yaml:1186"]:
        raise ValueError("the shipped example book index must derive the five held targets in held order")
    if index.gaps != ("pane-terminal-sweep",):
        raise ValueError("the shipped example book must leave the terminal sweep pane honestly unanchored, named in its gaps")
    found = pane_for_target(book, EXAMPLE_TARGET)
    if found is None or found.pane_id != "pane-work-session":
        raise ValueError("the shipped example book must reach its work pane under the example target")
    first = first_note(book)
    if first is None or first.note_id != "note-note-work":
        raise ValueError("the shipped example book must hold the work note as its first note road")


def validate_book(data: Any, *, require_example: bool = False) -> PaneBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, PaneBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a pane book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live pane target "
                f"({key!r} is named on it): {PANE_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its panes under a layout")
    if "pane_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held panes at call time")
    if data.get("schema") is not None and (
            data["schema"] != MULTI_PANE_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{MULTI_PANE_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != MULTI_PANE_SLICE):
        raise ValueError(
            f"a book's slice must be {MULTI_PANE_SLICE!r}")
    head = data.get("multi_pane") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's pane head must be a mapping")
    title = head.get("title") or data.get("title")
    panes = tuple(build_pane(g) for g in data.get("panes") or ())
    layouts = tuple(build_layout(v) for v in data.get("layouts") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    book = PaneBook(
        title=title, panes=panes, layouts=layouts, notes=notes, panels=())
    panels = tuple(
        build_panel(p, book) for p in data.get("panels") or ())
    book = PaneBook(
        title=book.title, panes=book.panes, layouts=book.layouts,
        notes=book.notes, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> PaneBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (PaneBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or a PaneBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> PaneBook:
    return validate_book(data, require_example=require_example)


def load_multi_pane(
        data: Optional[Dict[str, Any]] = None) -> PaneBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(MULTI_PANE_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_multi_pane_file(path: Any) -> PaneBook:
    """Load one pane file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: panes and layouts held one by one.
# ---------------------------------------------------------------------

class MultiPaneRegistry:
    """An in-memory holding of panes and layouts.

    The registry is the pure layer's model of a
    session's pane book: panes are held under
    their ids, one pane per id and per
    sequence, and layouts are held in recorded
    order, one layout per sequence and per id.
    Holding is data only - nothing held here moves
    a pointer, clicks anything, or opens a file.
    """

    def __init__(self, book: Any = None) -> None:
        self._panes: List[PaneCard] = []
        self._layouts: List[PaneLayout] = []
        self._title: Optional[str] = None
        if book is not None:
            self.register_book(book)

    def title(self) -> Optional[str]:
        return self._title

    def _fresh_layout_id(self, held_ids: Any) -> str:
        n = 1
        while f"layout-{n}" in held_ids:
            n += 1
        return f"layout-{n}"

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

    def register_pane(self, item: Any) -> PaneCard:
        """Hold one pane, judged whole before held."""
        checked = _check_pane_ref(item)
        return self._register(
            self._panes, checked, "pane_id", "pane")

    def register_layout(self, layout: Any) -> PaneLayout:
        """Hold one layout; a layout naming no id takes a fresh one."""
        checked = _check_layout_ref(layout)
        if not checked.layout_id:
            fresh = self._fresh_layout_id(
                [held.layout_id for held in self._layouts])
            checked = build_layout({**checked.to_record(),
                                  "layout_id": fresh})
        return self._register(
            self._layouts, checked, "layout_id", "layout")

    def register_book(self, book: Any) -> PaneBook:
        """Hold a whole book's panes and layouts, under its title."""
        checked = build_book(book)
        if self._title is not None and checked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {checked.title!r}")
        for pane in checked.panes:
            self.register_pane(pane)
        for layout in checked.layouts:
            self.register_layout(layout)
        self._title = checked.title
        return self.book()

    def book(self) -> PaneBook:
        return PaneBook(
            title=self._title or "An unheld pane book",
            panes=tuple(self._panes), layouts=tuple(self._layouts),
            notes=(), panels=())

    def list_panes(self) -> Tuple[PaneCard, ...]:
        return tuple(self._panes)

    def list_layouts(self) -> Tuple[PaneLayout, ...]:
        return tuple(self._layouts)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._panes) + tuple(self._layouts)

    def get_pane(self, pane_id: Any) -> PaneCard:
        return self.book().pane_for(pane_id)

    def get_layout(self, layout_id: Any) -> PaneLayout:
        return self.book().layout_for(layout_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records shaped for the journal target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> PaneBook:
    if source is None:
        return load_multi_pane()
    if isinstance(source, PaneBook):
        return source
    if isinstance(source, MultiPaneRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def pane_record(pane: Any, source: Any = None) -> Dict[str, Any]:
    checked = _check_pane_ref(pane)
    record = {
        "type": "diff_pane",
        "slice": MULTI_PANE_SLICE,
        "pane_id": checked.pane_id,
        "title": checked.title,
        "segment": segment_of(checked),
        "passes": pane_passes(checked),
        "gaps": list(pane_gaps(checked)),
    }
    record.update(_provenance_record(checked))
    return record


def layout_record(layout: Any) -> Dict[str, Any]:
    checked = _check_layout_ref(layout)
    record = {
        "type": "pane_layout",
        "slice": MULTI_PANE_SLICE,
        "layout_id": checked.layout_id, "seq": checked.seq,
        "layout_filter": checked.layout_filter,
    }
    record.update(_provenance_record(checked))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_note_ref(record_in)
    record = {
        "type": "pane_note",
        "slice": MULTI_PANE_SLICE,
        "note_id": checked.note_id,
        "pane_id": checked.pane_id,
        "stance": checked.stance,
    }
    record.update(_provenance_record(checked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    checked = validate_panel(panel, source)
    record = {"type": "pane_panel",
              "slice": MULTI_PANE_SLICE}
    record.update(checked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   layout: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, PaneVerdict):
        checked = validate_verdict(verdict, source)
    else:
        checked = derive_verdict(_source_book(verdict), layout)
    record = {"type": "pane_verdict",
              "slice": MULTI_PANE_SLICE}
    record.update(checked.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, PaneIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "pane_index",
              "slice": MULTI_PANE_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    checked = _source_book(book)
    record = {"type": "pane_book",
              "slice": MULTI_PANE_SLICE,
              "title": checked.title}
    record.update(checked.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(pane: Any, source: Any = None) -> str:
    checked = _check_pane_ref(pane)
    return (
        f"{checked.title} - kind {checked.kind}: "
        f"width {checked.width if checked.width else 'unknown'}, "
        f"height {checked.height if checked.height else 'unknown'}, "
        f"target {checked.target if checked.target else 'none'}. "
        f"{checked.detail}")


def pane_plain_words(pane: Any, source: Any = None) -> str:
    return plain_words(pane, source)


def panel_plain_words(source: Any, layout: Any = None) -> str:
    panel = derive_panel(source, layout)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, layout: Any = None) -> str:
    verdict = derive_verdict(source, layout)
    return (
        f"The multi-pane working stands {verdict.verdict}: "
        f"{verdict.passing_shown} of {verdict.total_shown} shown "
        f"panes stand anchored.")


def layout_plain_words(layout: Any) -> str:
    checked = _check_layout_ref(layout)
    return f"Layout {checked.layout_id}: shows {checked.layout_filter} panes."


def note_plain_words(record_in: Any) -> str:
    checked = _check_note_ref(record_in)
    return (
        f"Note {checked.note_id}: {checked.stance} "
        f"{checked.pane_id}, toward {checked.target}. "
        f"{checked.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, PaneIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} targets for "
        f"{len(index.entries)} panes; unanchored, named in "
        f"its gaps: {gaps}.")


def format_pane(pane: Any, source: Any = None) -> str:
    checked = _check_pane_ref(pane)
    lines = [f"{checked.title} ({checked.pane_id})"]
    lines.extend(plain_lines(checked))
    lines.append(checked.detail)
    if pane_passes(checked):
        lines.append(
            "This pane stands anchored to the pane, under "
            "the target its record names.")
    else:
        lines.append(
            "This pane stands unanchored - it names no pane "
            "target, stands named in its gaps, and no target is "
            "invented for it.")
    return "\n".join(lines)


def format_layout(layout: Any) -> str:
    checked = _check_layout_ref(layout)
    return (
        f"Layout {checked.layout_id}: filter {checked.layout_filter} - "
        f"{checked.detail}")


def format_note(record_in: Any) -> str:
    checked = _check_note_ref(record_in)
    lines = [
        f"Pane note {checked.stance} {checked.pane_id} "
        f"({checked.note_id}): {checked.title}. {checked.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it opens no pane, focuses no pane "
        "and posts no note.")
    return "\n".join(lines)


def format_target(source: Any, target: Any) -> str:
    pane = pane_for_target(source, target)
    if pane is not None:
        return format_pane(pane)
    wanted = _check_target(target)
    return (
        f"No held pane stands under target {wanted!r} yet - the "
        f"target reaches nothing in this book, and no pane is "
        f"invented for it.")


def format_book(source: Any = None, kind: Any = None) -> str:
    book = _source_book(source)
    panes = (panes_for_kind(book, kind)
                if kind is not None else book.panes)
    lines = [f"Multi-Pane Working (M-192) - {book.title}"]
    lines.extend(segment_of(pane) for pane in panes)
    return "\n".join(lines)


def format_panel(source: Any = None, layout: Any = None) -> str:
    panel = derive_panel(source, layout)
    lines = [f"Pane panel under layout {panel.layout_id}:"]
    lines.extend(row.segment for row in panel.rows)
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None, layout: Any = None) -> str:
    verdict = derive_verdict(source, layout)
    return verdict_plain_words(source, layout) + (
        f" (layout {verdict.layout_id}, as of {verdict.latest_on})")


def format_index(source: Any = None) -> str:
    book = _source_book(source)
    index = derive_index(book)
    lines = ["Pane index, derived from the held panes:"]
    for entry in index.entries:
        lines.append(f"{entry.target} - {entry.title} ({entry.pane_id})")
    if index.gaps:
        lines.append(
            "Unanchored to the pane, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "opens no pane and opens no network.")
    return "\n".join(lines)


def format_pane_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "Multi-Pane Working (M-192)",
        f"{book.title}: {len(book.panes)} panes held, "
        f"{len(passing_panes(book))} panes standing anchored, "
        f"{len(book.notes)} notes held.",
    ]
    if book.layouts:
        panel = derive_panel(book, book.layouts[0])
        lines.append(
            f"{panel.total_shown} of {panel.total_items} items show "
            f"under the first layout.")
        lines.extend(row.segment for row in panel.rows)
    lines.append(index_plain_words(book))
    lines.append(PLAIN_EXPLANATION)
    return "\n".join(lines)


def parse_pane_args(args: Any) -> Tuple[str, Any]:
    """Parse the /panes grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("pane", "layout", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("target", "kind"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
