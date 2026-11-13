"""UI undo (All-Features roadmap slice M-198).

Part VIII - The Beautiful Face - builds here. The
roadmap words: *closing a pane or clearing a view
is never destructive to work; view state per
session persists.*

What already ships, and what this slice adds:

* Panes close and views clear in the shipped
  faces, and an undo timeline already walks edits,
  commands and checkpoints. What nothing held is
  *the undo of the UI itself, as a book*: every
  closed pane and cleared view held as checkable
  data - one card per preserved view, held whole
  with its title, its kind (a closed vocabulary -
  pane, view, panel, tab), its cursor held
  honestly, and the view state it preserves,
  named as data; the undo index, derived from
  those held panes; the views, which show every
  pane, the ready or the incomplete; and the
  notes on panes, held as data beside them -
  note, concern, praise and question named as
  stances, each feeding back to the user as data,
  never applied by this layer. This slice is that
  book, in its own module, standing in the M-197
  command-palette book shape. The M-171 charter
  names NO row for this slice - the grep stands
  empty and the slice tests pin that live - so
  there is no charter verdict for this slice to
  honour; the slice is built to the roadmap words
  alone, in the M-194/M-195 manner.

* A pane is held whole: the title it stands
  under, its kind, its cursor - held honestly, an
  unknown cursor standing empty, never invented -
  the view state it preserves, named as data, and
  its detail. A pane naming no preserved state is
  held honestly with an empty state: it stands
  incomplete, named in its gaps - completeness is
  judged from the held records alone, never
  claimed live.
* The undo index is DERIVED at call time from the
  held panes - never a second stored copy that
  could drift from the panes themselves. A stored
  index, completeness verdict or coverage
  judgement on any record refuses by name.
* The notes are held as data: a note record
  naming its pane, its stance - note, concern,
  praise or question, a closed vocabulary - and
  what it feeds back toward. A book holds at most
  one note record per pane stance. Holding a note
  applies none of it: the rule stands as data
  (:data:`UNDO_RULE`) and a record claiming a pane
  was actually restored, a view actually
  reopened, or work actually destroyed, refuses
  BY NAME.
* The shipped data file holds one example book in
  exactly the shape a real undo file takes, a
  loader reads an undo file anywhere on disk,
  panes and views are shaped as session news, and
  a small in-memory registry holds records one by
  one. The agent layer owns holding an undo book
  for a session and telling from it. This layer
  reaches no live road: it restores nothing,
  reopens nothing, destroys no work, opens no
  network and writes nothing - it holds the
  preserved views as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **Completeness from records alone.** Every
  completeness telling is derived from the held
  pane records; a claim of a live restoration,
  reopening or destruction refuses by name.
* **Incomplete stands incomplete.** A pane naming
  no preserved state stands incomplete, named in
  its gaps - no state is invented for it.
* **Unknown stays unknown.** A cursor that is not
  known stands empty on its pane - no position is
  invented for it.
* **The index is derived, never stored.** The undo
  index is derived from the held panes at call
  time; a stored index refuses by name, so it can
  never drift.
* **One pane per pane.** Two panes standing for
  one pane id refuse by name, and one note record
  stands per pane stance.
"""


from __future__ import annotations

__all__ = [
    "KINDS",
    "EXAMPLE_STATE",
    "STANCES",
    "INDEX_ACTION",
    "UI_UNDO_RESOURCE",
    "UI_UNDO_SCHEMA",
    "UI_UNDO_SLICE",
    "UNDO_RULE",
    "PLAIN_EXPLANATION",
    "THE_UI_UNDO_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "READY_WORDS",
    "Any",
    "Dict",
    "List",
    "Optional",
    "PaneCard",
    "IndexEntry",
    "NoteRecord",
    "UndoBook",
    "UndoIndex",
    "UndoPanel",
    "UndoPanelRow",
    "UiUndoRegistry",
    "UndoVerdict",
    "UndoView",
    "TargetCount",
    "book_record",
    "build_book",
    "build_pane",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "first_note",
    "format_book",
    "format_pane",
    "format_index",
    "format_note",
    "format_undo_screen",
    "format_panel",
    "format_state",
    "format_verdict",
    "format_view",
    "pane_for_state",
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
    "load_ui_undo",
    "load_ui_undo_file",
    "normalize_kind",
    "normalize_stance",
    "normalize_view_filter",
    "panel_plain_words",
    "panel_record",
    "parse_undo_args",
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

UI_UNDO_SCHEMA = "mythic.ui_undo/1"
UI_UNDO_SLICE = "M-198"
THE_UI_UNDO_SLICE = UI_UNDO_SLICE
UI_UNDO_RESOURCE = "ui_undo.yaml"
INDEX_ACTION = "index"
EXAMPLE_STATE = "the editor draft still open"
READY_WORDS = ("ready", "unready")
KINDS = ("pane", "view", "panel", "tab")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "ready", "unready")
VERDICT_WORDS = ("open", "strained", "shut")

UNDO_RULE = (
    "UI undo is held as data alone: "
    "holding, viewing and telling the undo "
    "book restores nothing, reopens nothing, "
    "destroys no work, opens no network and "
    "writes nothing - completeness is judged "
    "from the held records alone, never "
    "claimed live")
PLAIN_EXPLANATION = (
    "UI undo (M-198): "
    "every closed pane and cleared view "
    "stands held as a card with its title, "
    "its kind, its cursor honestly held, "
    "the view state it preserves, and the "
    "views that arrange the panes - closing "
    "a pane or clearing a view is never "
    "destructive to work.")
USAGE = (
    "Usage: /uiundo | /uiundo pane <pane-id> | "
    "/uiundo state <state> | /uiundo kind <kind> | "
    "/uiundo view <view-id> | /uiundo note <note-id> | "
    "/uiundo index | /uiundo panel | /uiundo verdict")

_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_PANE_KEYS = frozenset({
    "pane_id", "seq", "title", "kind", "cursor",
    "state", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "pane_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "ready", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "panes", "coverage", "covered", "uncovered"})
_LIVE_KEYS = (
    "live_pane", "live_view", "shows_pane",
    "show_pane", "shown_pane", "restores_pane",
    "restored_pane", "restore_pane", "reopens_view",
    "reopened_view", "reopen_view", "destroys_work",
    "destroyed_work", "destroy_work", "restores_now",
    "reopens_now", "destroys_now", "performs_restore",
    "performed_restore", "opens_network", "writes_file",
    "write_file", "renders_now", "posts_note", "posted_note")


# ---------------------------------------------------------------------
# Small judges, in the sibling shape.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_state(value: Any) -> str:
    """Held preserved state: named as data, or honestly empty.

    An pane naming no preserved state is held with
    empty words and stands incomplete in its
    gaps; words that are not a string at all
    refuse.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("state must be a string naming the preserved state")
    return value.strip()


def _check_measure(value: Any, what: str) -> str:
    """A held measure: a cursor, named as data or honestly empty.

    An pane whose cursor is not known is
    held with an empty cursor: unknown stays unknown,
    and no key is invented for it. A cursor that
    is not a string at all refuses.
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
                f"{what} claims a live undo execution "
                f"({key!r} is named on it): "
                f"{UNDO_RULE}")
    for key in mapping:
        if key in _DERIVED_KEYS:
            raise ValueError(
                f"{what} carries {key!r}, which is derived from its "
                f"own fields and never stored")
        if key not in allowed:
            raise ValueError(f"{what} carries unknown field {key!r}")


def normalize_kind(value: Any) -> str:
    kind = _clean_text(value, "a kind").lower()
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


def normalize_view_filter(value: Any) -> str:
    view_filter = _clean_text(value, "a view filter").lower()
    if view_filter not in VIEW_FILTERS:
        raise ValueError(
            f"view filter {view_filter!r} is not one of the held "
            f"filters: " + ", ".join(VIEW_FILTERS))
    return view_filter


# ---------------------------------------------------------------------
# The held pane: one door, with the words that find it.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class PaneCard:
    """One undo pane, held as data with its preserved state.

    The pane names its plain title, the kind it
    lives in - one of the closed kind vocabulary -
    its cursor, the preserved state it carries, named
    as data, and its detail. An pane naming no
    preserved state is held with empty words: it stands
    incomplete, named in its gaps, and no words are
    invented for it. The pane is local data alone -
    no live execution stands behind it: holding it
    executes nothing.
    """

    pane_id: str
    seq: int
    title: str
    kind: str
    cursor: str = ""
    state: str = ""
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
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "cursor", _check_measure(self.cursor, "a cursor"))
        object.__setattr__(
            self, "state", _check_state(self.state))
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
            "cursor": self.cursor,
            "state": self.state, "detail": self.detail,
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
        cursor=data.get("cursor"),
        state=data.get("state"), detail=data.get("detail"),
        **_provenance(data))


def pane_gaps(pane: Any) -> Tuple[str, ...]:
    """The gaps that keep a pane from completeness."""
    checked = _check_pane_ref(pane)
    return () if checked.state else ("no preserved state",)


def pane_passes(pane: Any) -> bool:
    return not pane_gaps(pane)


def plain_lines(pane: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the pane's own fields."""
    checked = _check_pane_ref(pane)
    return (
        f"Pane: {checked.title}",
        f"Kind: {checked.kind}",
        f"Cursor: {checked.cursor if checked.cursor else 'unknown'}",
        f"State: {checked.state if checked.state else 'none'}",
    )


def segment_of(pane: Any) -> str:
    checked = _check_pane_ref(pane)
    gaps = pane_gaps(checked)
    return (
        f"{checked.pane_id}: {checked.title} - kind: "
        f"'{checked.kind}' - cursor: "
        f"'{checked.cursor if checked.cursor else 'unknown'}' - "
        f"state: '{checked.state if checked.state else 'none'}' - "
        f"detail: '{checked.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held stance: a note on a pane, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One undo note, held as data.

    The record names its pane, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per pane
    stance in a book. The record is data alone:
    holding it executes no command and runs no
    action, ever.
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
            self, "pane_id", _clean_text(self.pane_id, "a pane id"))
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
# The held view: which panes a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class UndoView:
    """A view over the book: every pane, the ready, the rest."""

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


def _check_view_ref(value: Any) -> UndoView:
    if not isinstance(value, UndoView):
        raise ValueError("a view must be a UndoView")
    return value


def validate_view(view: Any) -> UndoView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> UndoView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, UndoView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or a UndoView")
    _needed(data, _VIEW_KEYS, "a view")
    return UndoView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


def inspect_pane_source(piece: Any) -> Dict[str, Any]:
    """Name what one pane source piece is, without judging it."""
    if isinstance(piece, PaneCard):
        return {"kind": "pane", "pane_id": piece.pane_id}
    if isinstance(piece, dict):
        if "note_id" in piece:
            return {"kind": "note", "note_id": piece.get("note_id")}
        if "view_id" in piece:
            return {"kind": "view", "view_id": piece.get("view_id")}
        if "pane_id" in piece:
            return {"kind": "pane", "pane_id": piece.get("pane_id")}
    return {"kind": "unknown", "pane_id": None}


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class UndoPanelRow:
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


def _row_for_pane(pane: PaneCard) -> UndoPanelRow:
    return UndoPanelRow(
        item_id=pane.pane_id,
        standing="ready" if pane_passes(pane) else "unready",
        label=pane.title, segment=segment_of(pane),
        recorded_on=pane.recorded_on)


def _check_row_ref(value: Any) -> UndoPanelRow:
    if not isinstance(value, UndoPanelRow):
        raise ValueError("a panel row must be a UndoPanelRow")
    return value


def validate_row(row: Any, pane: Any = None) -> UndoPanelRow:
    checked = _check_row_ref(row)
    if pane is not None:
        derived = _row_for_pane(_check_pane_ref(pane))
        if checked != derived:
            raise ValueError(
                f"panel row {checked.item_id!r} does not agree with "
                f"the row derived from its pane")
    return checked


def build_row(row: Any = None, pane: Any = None,
              **kwargs: Any) -> UndoPanelRow:
    if pane is not None:
        derived = _row_for_pane(_check_pane_ref(pane))
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            UndoPanelRow(**kwargs))
        return validate_row(built, pane)
    if isinstance(row, UndoPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in READY_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return UndoPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return UndoPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or a UndoPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[UndoPanelRow, ...]
                 ) -> Tuple[TargetCount, ...]:
    counts: List[TargetCount] = []
    for standing in READY_WORDS:
        number = sum(1 for row in rows if row.standing == standing)
        if number:
            counts.append(TargetCount(standing=standing, items=number))
    return tuple(counts)


def _panel_account(total_items: int, total_shown: int,
                   passing_shown: int,
                   target_counts: Tuple[TargetCount, ...],
                   view_filter: str, as_of: str) -> Tuple[str, ...]:
    standing_words = ", ".join(
        f"{count.standing} {count.items}"
        for count in target_counts) or "none"
    return (
        f"The UI undo book holds {total_items} panes as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {passing_shown} of the shown panes "
        f"stand ready.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its pane's own fields "
        "- the title, the kind, the cursor honestly held "
        "and the preserved state it honestly carries - and no "
        "judgement is stored on any pane.",
        "Completeness is judged from the held records alone: "
        "a pane naming no preserved state stands unready, and the "
        "undo index is derived from the held panes, "
        "never stored where it could drift.",
    )


@dataclass(frozen=True)
class UndoPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[UndoPanelRow, ...]
    total_items: int
    total_shown: int
    target_counts: Tuple[TargetCount, ...]
    as_of: str
    account: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "panel_id": self.panel_id, "view_id": self.view_id,
            "view_filter": self.view_filter,
            "rows": [row.to_record() for row in self.rows],
            "total_items": self.total_items,
            "total_shown": self.total_shown,
            "target_counts": [c.to_record() for c in self.target_counts],
            "as_of": self.as_of, "account": list(self.account),
        }


def _resolve_view(source: Any, view: Any) -> UndoView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, UndoView):
        return view
    return book.view_for(view)


def shown_panes(source: Any, view: Any = None
                   ) -> Tuple[PaneCard, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.panes
    if resolved.view_filter == "ready":
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


def derive_panel(source: Any, view: Any = None) -> UndoPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_panes(book, resolved)
    rows = tuple(_row_for_pane(pane) for pane in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.panes), default="")
    passing = sum(1 for g in shown if pane_passes(g))
    return UndoPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.panes), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.panes), len(shown), passing, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> UndoPanel:
    if not isinstance(value, UndoPanel):
        raise ValueError("a panel must be a UndoPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> UndoPanel:
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
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(checked, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {checked.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return checked


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> UndoPanel:
    if isinstance(panel, UndoPanel):
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
        built = UndoPanel(
            panel_id=_clean_text(data.get("panel_id"), "a panel id"),
            view_id=data.get("view_id"),
            view_filter=normalize_view_filter(data.get("view_filter")),
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
        return derive_panel(source, kwargs.get("view"))
    raise ValueError("a panel must be a mapping, a UndoPanel, or derived")


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
class UndoVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> UndoVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_panes(book, resolved)
    passing = sum(1 for g in shown if pane_passes(g))
    latest = max((g.recorded_on for g in shown), default="")
    return UndoVerdict(
        verdict=_verdict_word(len(shown), passing),
        view_id=resolved.view_id, total_shown=len(shown),
        passing_shown=passing, latest_on=latest)


def _check_verdict_ref(value: Any) -> UndoVerdict:
    if not isinstance(value, UndoVerdict):
        raise ValueError("a verdict must be a UndoVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> UndoVerdict:
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
                  **kwargs: Any) -> UndoVerdict:
    if isinstance(verdict, UndoVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = UndoVerdict(
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
        "a verdict must be a mapping, a UndoVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held panes' words at call time, and
# the stance targets: which pane notes the book holds, derived too.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    state: str
    pane_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "state": self.state, "pane_id": self.pane_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class UndoIndex:
    """The undo index, derived from the held panes.

    The index names one pane per complete pane, in
    held order - the pane's own preserved state, its id and
    its title - and the panes that stand incomplete,
    named in its gaps. Nothing here is stored on any
    pane: the index is derived at call time from the
    held records alone, so it can never drift from them.
    """

    panes: Tuple[IndexEntry, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "panes": [e.to_record() for e in self.panes],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> UndoIndex:
    """Derive the undo index from the book's held panes."""
    book = _source_book(source)
    panes = tuple(
        IndexEntry(state=g.state, pane_id=g.pane_id, title=g.title)
        for g in book.panes if pane_passes(g))
    gaps = tuple(
        g.pane_id for g in book.panes if not pane_passes(g))
    return UndoIndex(panes=panes, gaps=gaps)


def pane_for_state(source: Any, state: Any) -> Optional[PaneCard]:
    """The first held pane one set of words reaches, or none - honestly."""
    wanted = _check_state(state)
    if not wanted:
        return None
    for pane in _source_book(source).panes:
        if pane.state == wanted:
            return pane
    return None


def note_for_pane(source: Any, pane_id: Any,
                       stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one pane (and stance, when named)."""
    wanted = _clean_text(pane_id, "a pane id")
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
# The book: panes, views and notes held together, one pinned panel
# at most per telling, and no verdict or index ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class UndoBook:
    title: str
    panes: Tuple[PaneCard, ...] = ()
    views: Tuple[UndoView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    panels: Tuple[UndoPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        panes = tuple(_check_pane_ref(g) for g in self.panes)
        views = tuple(_check_view_ref(v) for v in self.views)
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
                    f"two stance records stand for pane "
                    f"{record.pane_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per pane target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        object.__setattr__(
            self, "panes", tuple(sorted(panes, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.panes + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.pane_id for g in self.panes) + tuple(
            v.view_id for v in self.views)

    def pane_ids(self) -> Tuple[str, ...]:
        return tuple(g.pane_id for g in self.panes)

    def pane_for(self, pane_id: Any) -> PaneCard:
        wanted = _clean_text(pane_id, "a pane id")
        for pane in self.panes:
            if pane.pane_id == wanted:
                return pane
        raise KeyError(f"no pane named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> UndoView:
        wanted = _clean_text(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view named {wanted!r} stands in this book")

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
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "panes": [g.to_record() for g in self.panes],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "panels": [p.to_record() for p in self.panels],
        }


def _judge_book_panels(book: UndoBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: UndoBook) -> None:
    if book.title != "UI undo at the M-197 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.panes) != 6 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold six panes and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m197-boundary":
        raise ValueError("the pinned panel is panel-m197-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "strained" or verdict.passing_shown != 5:
        raise ValueError("the shipped example book verdict must stand strained at five ready of six")
    index = derive_index(book)
    if [e.state for e in index.panes] != ["the editor draft still open", "the files still in view", "the board as it stood", "the preview still rendered", "help when you are stuck"]:
        raise ValueError("the shipped example book index must derive the five held states in held order")
    if index.gaps != ("pane-quiet-main",):
        raise ValueError("the shipped example book must leave the quiet pane honestly incomplete, named in its gaps")
    found = pane_for_state(book, EXAMPLE_STATE)
    if found is None or found.pane_id != "pane-editor-main":
        raise ValueError("the shipped example book must reach its editor pane under the example state")
    first = first_note(book)
    if first is None or first.note_id != "note-note-editor":
        raise ValueError("the shipped example book must hold the editor note as its first note road")



def validate_book(data: Any, *, require_example: bool = False) -> UndoBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, UndoBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a undo book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live undo execution "
                f"({key!r} is named on it): {UNDO_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its panes under a view")
    if "undo_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held panes at call time")
    if data.get("schema") is not None and (
            data["schema"] != UI_UNDO_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{UI_UNDO_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != UI_UNDO_SLICE):
        raise ValueError(
            f"a book's slice must be {UI_UNDO_SLICE!r}")
    head = data.get("ui_undo") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's undo head must be a mapping")
    title = head.get("title") or data.get("title")
    panes = tuple(build_pane(g) for g in data.get("panes") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    book = UndoBook(
        title=title, panes=panes, views=views, notes=notes, panels=())
    panels = tuple(
        build_panel(p, book) for p in data.get("panels") or ())
    book = UndoBook(
        title=book.title, panes=book.panes, views=book.views,
        notes=book.notes, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> UndoBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (UndoBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or a UndoBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> UndoBook:
    return validate_book(data, require_example=require_example)


def load_ui_undo(
        data: Optional[Dict[str, Any]] = None) -> UndoBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(UI_UNDO_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_ui_undo_file(path: Any) -> UndoBook:
    """Load one undo file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: panes and views held one by one.
# ---------------------------------------------------------------------

class UiUndoRegistry:
    """An in-memory holding of panes and views.

    The registry is the pure layer's model of a
    session's undo book: panes are held under
    their ids, one pane per id and per sequence,
    and views are held in recorded order, one view
    per sequence and per id. Holding is data only -
    nothing held here executes a command, runs an
    action, or navigates anywhere.
    """

    def __init__(self, book: Any = None) -> None:
        self._panes: List[PaneCard] = []
        self._views: List[UndoView] = []
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

    def register_pane(self, item: Any) -> PaneCard:
        """Hold one pane, judged whole before held."""
        checked = _check_pane_ref(item)
        return self._register(
            self._panes, checked, "pane_id", "pane")

    def register_view(self, view: Any) -> UndoView:
        """Hold one view; a view naming no id takes a fresh one."""
        checked = _check_view_ref(view)
        if not checked.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            checked = build_view({**checked.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, checked, "view_id", "view")

    def register_book(self, book: Any) -> UndoBook:
        """Hold a whole book's panes and views, under its title."""
        checked = build_book(book)
        if self._title is not None and checked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {checked.title!r}")
        for pane in checked.panes:
            self.register_pane(pane)
        for view in checked.views:
            self.register_view(view)
        self._title = checked.title
        return self.book()

    def book(self) -> UndoBook:
        return UndoBook(
            title=self._title or "An unheld undo book",
            panes=tuple(self._panes), views=tuple(self._views),
            notes=(), panels=())

    def list_panes(self) -> Tuple[PaneCard, ...]:
        return tuple(self._panes)

    def list_views(self) -> Tuple[UndoView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._panes) + tuple(self._views)

    def get_pane(self, pane_id: Any) -> PaneCard:
        return self.book().pane_for(pane_id)

    def get_view(self, view_id: Any) -> UndoView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records shaped for the journal target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> UndoBook:
    if source is None:
        return load_ui_undo()
    if isinstance(source, UndoBook):
        return source
    if isinstance(source, UiUndoRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def pane_record(pane: Any, source: Any = None) -> Dict[str, Any]:
    checked = _check_pane_ref(pane)
    record = {
        "type": "undo_pane",
        "slice": UI_UNDO_SLICE,
        "pane_id": checked.pane_id,
        "title": checked.title,
        "segment": segment_of(checked),
        "passes": pane_passes(checked),
        "gaps": list(pane_gaps(checked)),
    }
    record.update(_provenance_record(checked))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    checked = _check_view_ref(view)
    record = {
        "type": "undo_view",
        "slice": UI_UNDO_SLICE,
        "view_id": checked.view_id, "seq": checked.seq,
        "view_filter": checked.view_filter,
    }
    record.update(_provenance_record(checked))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_note_ref(record_in)
    record = {
        "type": "undo_note",
        "slice": UI_UNDO_SLICE,
        "note_id": checked.note_id,
        "pane_id": checked.pane_id,
        "stance": checked.stance,
    }
    record.update(_provenance_record(checked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    checked = validate_panel(panel, source)
    record = {"type": "undo_panel",
              "slice": UI_UNDO_SLICE}
    record.update(checked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, UndoVerdict):
        checked = validate_verdict(verdict, source)
    else:
        checked = derive_verdict(_source_book(verdict), view)
    record = {"type": "undo_verdict",
              "slice": UI_UNDO_SLICE}
    record.update(checked.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, UndoIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "undo_index",
              "slice": UI_UNDO_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    checked = _source_book(book)
    record = {"type": "undo_book",
              "slice": UI_UNDO_SLICE,
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
        f"cursor {checked.cursor if checked.cursor else 'unknown'}, "
        f"state {checked.state if checked.state else 'none'}. "
        f"{checked.detail}")


def pane_plain_words(pane: Any, source: Any = None) -> str:
    return plain_words(pane, source)


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The command undo stands {verdict.verdict}: "
        f"{verdict.passing_shown} of {verdict.total_shown} shown "
        f"panes stand ready.")


def view_plain_words(view: Any) -> str:
    checked = _check_view_ref(view)
    return f"View {checked.view_id}: shows {checked.view_filter} panes."


def note_plain_words(record_in: Any) -> str:
    checked = _check_note_ref(record_in)
    return (
        f"Note {checked.note_id}: {checked.stance} "
        f"{checked.pane_id}, toward {checked.target}. "
        f"{checked.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, UndoIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.panes)} preserved state for "
        f"{len(index.panes)} panes; incomplete, named in "
        f"its gaps: {gaps}.")


def format_pane(pane: Any, source: Any = None) -> str:
    checked = _check_pane_ref(pane)
    lines = [f"{checked.title} ({checked.pane_id})"]
    lines.extend(plain_lines(checked))
    lines.append(checked.detail)
    if pane_passes(checked):
        lines.append(
            "This pane stands ready - it carries the search "
            "words its record names.")
    else:
        lines.append(
            "This pane stands unready - it names no search "
            "words, stands named in its gaps, and no words are "
            "invented for it.")
    return "\n".join(lines)


def format_view(view: Any) -> str:
    checked = _check_view_ref(view)
    return (
        f"View {checked.view_id}: filter {checked.view_filter} - "
        f"{checked.detail}")


def format_note(record_in: Any) -> str:
    checked = _check_note_ref(record_in)
    lines = [
        f"Undo note {checked.stance} {checked.pane_id} "
        f"({checked.note_id}): {checked.title}. {checked.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it executes no command, runs no action "
        "and posts no note.")
    return "\n".join(lines)


def format_state(source: Any, state: Any) -> str:
    pane = pane_for_state(source, state)
    if pane is not None:
        return format_pane(pane)
    wanted = _check_state(state)
    return (
        f"No held pane stands under state {wanted!r} yet - the "
        f"state reaches nothing in this book, and no pane is "
        f"invented for them.")


def format_book(source: Any = None, kind: Any = None) -> str:
    book = _source_book(source)
    panes = (panes_for_kind(book, kind)
                if kind is not None else book.panes)
    lines = [f"UI Undo (M-198) - {book.title}"]
    lines.extend(segment_of(pane) for pane in panes)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Undo panel under view {panel.view_id}:"]
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
    lines = ["Undo index, derived from the held panes:"]
    for pane in index.panes:
        lines.append(f"{pane.state} - {pane.title} ({pane.pane_id})")
    if index.gaps:
        lines.append(
            "Incomplete, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "executes no command and opens no network.")
    return "\n".join(lines)


def format_undo_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "UI Undo (M-198)",
        f"{book.title}: {len(book.panes)} panes held, "
        f"{len(passing_panes(book))} panes standing ready, "
        f"{len(book.notes)} notes held.",
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


def parse_undo_args(args: Any) -> Tuple[str, Any]:
    """Parse the /uiundo grammar into (action, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("pane", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("state", "kind"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
