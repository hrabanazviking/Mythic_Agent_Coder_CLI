"""Small-terminal grace (All-Features roadmap slice M-194).

Part VIII - The Beautiful Face - builds here. The
roadmap words: *the TUI folds gracefully to 80x24
and to a phone-over-SSH width without losing the
work.*

What already ships, and what this slice adds:

* The TUI already warns when the terminal stands
  too small, and the M-192 multi-pane book holds
  the working screen as data. What nothing held
  is *the folding itself as a book*: every fold
  held as checkable data - one card per fold, held
  whole with its surface, its kind (a closed
  vocabulary - full, folded, stacked, hidden,
  summary), its width and its height, and the
  work it preserves, named as data; the fold
  index, derived from those held folds; the
  views, which show every fold, the preserved or
  the losable; and the notes on folds, held as
  data beside them - note, concern, praise and
  question named as stances, each feeding back
  to the user as data, never posted by this
  layer. This slice is that book, in its own
  module, standing in the M-193 splash and
  ceremony book shape. The M-171 charter names
  this slice on NO row - the grep stands empty
  and the slice tests pin that absence live - so
  the slice is built to the roadmap words alone.

* A fold is held whole: the surface it stands
  for, its kind, its width and its height - held
  honestly, an unknown width or height standing
  empty, never invented - the work it preserves,
  named as data, and its detail. A fold naming
  no preserved work is held honestly with an
  empty preserves: it stands losable, named in
  its gaps - preservation is judged from the
  held records alone, never claimed live.
* The fold index is DERIVED at call time from
  the held folds - never a second stored copy
  that could drift from the folds themselves. A
  stored index, preservation verdict or coverage
  judgement on any record refuses by name.
* The notes are held as data: a note record
  naming its fold, its stance - note, concern,
  praise or question, a closed vocabulary - and
  what it feeds back toward. A book holds at
  most one note record per fold stance. Holding
  a note posts none of it: the rule stands as
  data (:data:`GRACE_RULE`) and a record claiming
  a terminal was actually resized, a pane
  actually folded on a live terminal or work
  actually rendered refuses BY NAME.
* The shipped data file holds one example book
  in exactly the shape a real fold file takes, a
  loader reads a fold file anywhere on disk,
  folds and views are shaped as session news, and
  a small in-memory registry holds records one
  by one. The agent layer owns holding a fold
  book for a session and telling from it. This
  layer reaches no live road: it resizes no
  terminal, folds no pane, renders no work and
  opens no network - it holds the folding as
  data and tells it.

Honesty rules, enforced here and pinned by tests:

* **Preservation from records alone.** Every
  preservation telling is derived from the held
  fold records; a claim of a live resize, fold
  or render refuses by name.
* **Losable stands losable.** A fold naming no
  preserved work stands losable, named in its
  gaps - no work is invented for it.
* **Unknown stays unknown.** A width or height
  that is not known stands empty on its fold -
  no figure is invented for it.
* **The index is derived, never stored.** The
  fold index is derived from the held folds at
  call time; a stored index refuses by name, so
  it can never drift.
* **One fold per fold.** Two folds standing for
  one fold id refuse by name, and one note
  record stands per fold stance.
* **The notes are data alone.** The records hold
  the feedback; holding, viewing or telling them
  resizes nothing, folds nothing and posts
  nothing.
"""


from __future__ import annotations

__all__ = [
    "KINDS",
    "EXAMPLE_PRESERVES",
    "STANCES",
    "INDEX_ACTION",
    "SMALL_TERMINAL_GRACE_RESOURCE",
    "SMALL_TERMINAL_GRACE_SCHEMA",
    "SMALL_TERMINAL_GRACE_SLICE",
    "GRACE_RULE",
    "PLAIN_EXPLANATION",
    "THE_SMALL_TERMINAL_GRACE_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "PRESERVE_WORDS",
    "Any",
    "Dict",
    "List",
    "Optional",
    "FoldCard",
    "IndexEntry",
    "NoteRecord",
    "FoldBook",
    "FoldIndex",
    "FoldPanel",
    "FoldPanelRow",
    "SmallTerminalGraceRegistry",
    "FoldVerdict",
    "FoldView",
    "TargetCount",
    "book_record",
    "build_book",
    "build_fold",
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
    "format_fold",
    "format_index",
    "format_note",
    "format_grace_screen",
    "format_panel",
    "format_preserves",
    "format_verdict",
    "format_view",
    "fold_for_preserves",
    "fold_gaps",
    "fold_passes",
    "fold_plain_words",
    "fold_record",
    "folds_for_kind",
    "index_plain_words",
    "index_record",
    "inspect_fold_source",
    "note_for_fold",
    "note_plain_words",
    "note_record",
    "load_small_terminal_grace",
    "load_small_terminal_grace_file",
    "normalize_kind",
    "normalize_stance",
    "normalize_view_filter",
    "panel_plain_words",
    "panel_record",
    "parse_grace_args",
    "passing_folds",
    "plain_lines",
    "plain_words",
    "segment_of",
    "shown_folds",
    "total_folds",
    "validate_book",
    "validate_fold",
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

SMALL_TERMINAL_GRACE_SCHEMA = "mythic.small_terminal_grace/1"
SMALL_TERMINAL_GRACE_SLICE = "M-194"
THE_SMALL_TERMINAL_GRACE_SLICE = SMALL_TERMINAL_GRACE_SLICE
SMALL_TERMINAL_GRACE_RESOURCE = "small_terminal_grace.yaml"
INDEX_ACTION = "index"
EXAMPLE_PRESERVES = "the work in progress"
PRESERVE_WORDS = ("preserved", "losable")
KINDS = ("full", "folded", "stacked", "hidden", "summary")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "preserved", "losable")
VERDICT_WORDS = ("open", "strained", "shut")
GRACE_RULE = (
    "small-terminal grace is held as data alone: "
    "holding, viewing and reading the folds "
    "resizes no terminal, folds no pane, renders "
    "no work and opens no network - preservation "
    "is judged from the held records "
    "alone, never claimed live")
PLAIN_EXPLANATION = (
    "Splash and grace, restrained (M-194): "
    "every grace fold stands held as a card "
    "with its surface, its kind, its width "
    "and height honestly held, the preserved work "
    "it carries, and the views that arrange the "
    "folds - grace at start and at a roadmap's "
    "completion, quiet the rest of the time, inside "
    "the Lawbook's heights.")
USAGE = (
    "Usage: /grace | /grace fold <fold-id> | "
    "/grace preserves <preserves> | /grace kind <kind> | "
    "/grace view <view-id> | /grace note <note-id> | "
    "/grace index | /grace panel | /grace verdict")

_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_FOLD_KEYS = frozenset({
    "fold_id", "seq", "surface", "kind", "width", "height",
    "preserves", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "fold_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "preserved", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered"})
_LIVE_KEYS = (
    "live_fold", "live_view", "resizes_terminal",
    "resized_terminal", "resizes_fold", "resized_fold",
    "folds_pane", "folded_pane", "folds_terminal",
    "folded_terminal", "renders_work", "rendered_work",
    "displays_fold", "displayed_fold",
    "opens_network", "writes_file", "write_file",
    "live_display", "show_now", "note_now",
    "renders_now", "posts_note", "posted_note")


# ---------------------------------------------------------------------
# Small judges, in the sibling shape.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_preserves(value: Any) -> str:
    """A held fold target: a fold named as data, or honestly empty.

    A fold naming no fold target is held with an
    empty target and stands losable in its gaps; a
    target that is not a string at all refuses.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("an preserves must be a string naming the preserved work")
    return value.strip()


def _check_measure(value: Any, what: str) -> str:
    """A held measure: width or height, named as data or honestly empty.

    A fold whose width or height is not known is
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
                f"{what} claims a live terminal folding "
                f"({key!r} is named on it): "
                f"{GRACE_RULE}")
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


def normalize_view_filter(value: Any) -> str:
    view_filter = _clean_text(value, "a view filter").lower()
    if view_filter not in VIEW_FILTERS:
        raise ValueError(
            f"view filter {view_filter!r} is not one of the held "
            f"filters: " + ", ".join(VIEW_FILTERS))
    return view_filter


# ---------------------------------------------------------------------
# The held fold: one fold, with the target that reaches it.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class FoldCard:
    """One grace fold, held as data with its preserved work.

    The fold names its surface, the kind it
    lives in - one of the closed kind vocabulary -
    its width and its height, the text
    preserves it carries, named as data, and its
    detail. A fold naming no preserved work is
    held with an empty preserves: it stands
    losable, named in its gaps, and no
    preserves is invented for it. The fold is
    local data alone - no live showing stands
    behind it: holding it shows nothing.
    """

    fold_id: str
    seq: int
    surface: str
    kind: str
    width: str = ""
    height: str = ""
    preserves: str = ""
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "fold_id", _clean_text(self.fold_id, "a fold id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "surface", _clean_text(self.surface, "an surface"))
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "width", _check_measure(self.width, "a width"))
        object.__setattr__(
            self, "height", _check_measure(self.height, "a height"))
        object.__setattr__(
            self, "preserves", _check_preserves(self.preserves))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a fold detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.fold_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "fold_id": self.fold_id, "seq": self.seq,
            "surface": self.surface, "kind": self.kind,
            "width": self.width, "height": self.height,
            "preserves": self.preserves, "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_fold_ref(value: Any) -> FoldCard:
    if not isinstance(value, FoldCard):
        raise ValueError("a fold must be a FoldCard")
    return value


def validate_fold(fold: Any) -> FoldCard:
    return _check_fold_ref(fold)


def build_fold(record: Any = None, **kwargs: Any) -> FoldCard:
    """Build one held fold from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, FoldCard):
        if kwargs:
            raise ValueError("a fold stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a fold must be a mapping or a FoldCard")
    _needed(data, _FOLD_KEYS, "a fold")
    return FoldCard(
        fold_id=data.get("fold_id"), seq=data.get("seq"),
        surface=data.get("surface"), kind=data.get("kind"),
        width=data.get("width"), height=data.get("height"),
        preserves=data.get("preserves"), detail=data.get("detail"),
        **_provenance(data))


def fold_gaps(fold: Any) -> Tuple[str, ...]:
    """The gaps that keep a fold from the grace."""
    checked = _check_fold_ref(fold)
    return () if checked.preserves else ("no preserved work",)


def fold_passes(fold: Any) -> bool:
    return not fold_gaps(fold)


def plain_lines(fold: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the fold's own fields."""
    checked = _check_fold_ref(fold)
    return (
        f"Fold: {checked.surface}",
        f"Kind: {checked.kind}",
        f"Width: {checked.width if checked.width else 'unknown'}",
        f"Height: {checked.height if checked.height else 'unknown'}",
        f"Preserves: {checked.preserves if checked.preserves else 'none'}",
    )


def segment_of(fold: Any) -> str:
    checked = _check_fold_ref(fold)
    gaps = fold_gaps(checked)
    return (
        f"{checked.fold_id}: {checked.surface} - kind: "
        f"'{checked.kind}' - width: "
        f"'{checked.width if checked.width else 'unknown'}' - "
        f"height: "
        f"'{checked.height if checked.height else 'unknown'}' - "
        f"preserves: '{checked.preserves if checked.preserves else 'none'}' - "
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
    fold_id: str
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
            self, "fold_id", _clean_text(self.fold_id, "a session id"))
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
            "fold_id": self.fold_id, "stance": self.stance,
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
        fold_id=data.get("fold_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which folds a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class FoldView:
    """A view over the book: every fold, the preserved, the rest."""

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


def _check_view_ref(value: Any) -> FoldView:
    if not isinstance(value, FoldView):
        raise ValueError("a view must be a FoldView")
    return value


def validate_view(view: Any) -> FoldView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> FoldView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, FoldView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or a FoldView")
    _needed(data, _VIEW_KEYS, "a view")
    return FoldView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


def inspect_fold_source(piece: Any) -> Dict[str, Any]:
    """Name what one fold source piece is, without judging it."""
    if isinstance(piece, FoldCard):
        return {"kind": "fold", "fold_id": piece.fold_id}
    if isinstance(piece, dict):
        if "note_id" in piece:
            return {"kind": "note", "note_id": piece.get("note_id")}
        if "view_id" in piece:
            return {"kind": "view", "view_id": piece.get("view_id")}
        if "fold_id" in piece:
            return {"kind": "fold", "fold_id": piece.get("fold_id")}
    return {"kind": "unknown", "fold_id": None}


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class FoldPanelRow:
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


def _row_for_fold(fold: FoldCard) -> FoldPanelRow:
    return FoldPanelRow(
        item_id=fold.fold_id,
        standing="preserved" if fold_passes(fold) else "losable",
        label=fold.surface, segment=segment_of(fold),
        recorded_on=fold.recorded_on)


def _check_row_ref(value: Any) -> FoldPanelRow:
    if not isinstance(value, FoldPanelRow):
        raise ValueError("a panel row must be a FoldPanelRow")
    return value


def validate_row(row: Any, fold: Any = None) -> FoldPanelRow:
    checked = _check_row_ref(row)
    if fold is not None:
        derived = _row_for_fold(_check_fold_ref(fold))
        if checked != derived:
            raise ValueError(
                f"panel row {checked.item_id!r} does not agree with "
                f"the row derived from its fold")
    return checked


def build_row(row: Any = None, fold: Any = None,
              **kwargs: Any) -> FoldPanelRow:
    if fold is not None:
        derived = _row_for_fold(_check_fold_ref(fold))
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            FoldPanelRow(**kwargs))
        return validate_row(built, fold)
    if isinstance(row, FoldPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in PRESERVE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return FoldPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return FoldPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or a FoldPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[FoldPanelRow, ...]
                 ) -> Tuple[TargetCount, ...]:
    counts: List[TargetCount] = []
    for standing in PRESERVE_WORDS:
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
        f"The grace book holds {total_items} folds as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {passing_shown} of the shown folds "
        f"stand preserved.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its fold's own fields "
        "- the surface, the kind, the width and height "
        "honestly held and the preserved work it honestly "
        "carries - and no judgement is stored on any fold.",
        "Preservation is judged from the held records alone: "
        "a fold naming no preserved work stands losable, and the "
        "grace index is derived from the held folds, "
        "never stored where it could drift.",
    )
@dataclass(frozen=True)
class FoldPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[FoldPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> FoldView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, FoldView):
        return view
    return book.view_for(view)


def shown_folds(source: Any, view: Any = None
                   ) -> Tuple[FoldCard, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.folds
    if resolved.view_filter == "preserved":
        return tuple(g for g in book.folds if fold_passes(g))
    return tuple(g for g in book.folds if not fold_passes(g))


def folds_for_kind(source: Any, kind: Any
                      ) -> Tuple[FoldCard, ...]:
    wanted = normalize_kind(kind)
    return tuple(
        g for g in _source_book(source).folds if g.kind == wanted)


def passing_folds(source: Any) -> Tuple[FoldCard, ...]:
    return tuple(
        g for g in _source_book(source).folds if fold_passes(g))


def total_folds(source: Any) -> int:
    return len(_source_book(source).folds)


def derive_panel(source: Any, view: Any = None) -> FoldPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_folds(book, resolved)
    rows = tuple(_row_for_fold(fold) for fold in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.folds), default="")
    passing = sum(1 for g in shown if fold_passes(g))
    return FoldPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.folds), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.folds), len(shown), passing, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> FoldPanel:
    if not isinstance(value, FoldPanel):
        raise ValueError("a panel must be a FoldPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> FoldPanel:
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
                **kwargs: Any) -> FoldPanel:
    if isinstance(panel, FoldPanel):
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
        built = FoldPanel(
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
    raise ValueError("a panel must be a mapping, a FoldPanel, or derived")


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
class FoldVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> FoldVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_folds(book, resolved)
    passing = sum(1 for g in shown if fold_passes(g))
    latest = max((g.recorded_on for g in shown), default="")
    return FoldVerdict(
        verdict=_verdict_word(len(shown), passing),
        view_id=resolved.view_id, total_shown=len(shown),
        passing_shown=passing, latest_on=latest)


def _check_verdict_ref(value: Any) -> FoldVerdict:
    if not isinstance(value, FoldVerdict):
        raise ValueError("a verdict must be a FoldVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> FoldVerdict:
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
                  **kwargs: Any) -> FoldVerdict:
    if isinstance(verdict, FoldVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = FoldVerdict(
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
        "a verdict must be a mapping, a FoldVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held folds' targets at call time, and
# the stance targets: which file notes the book holds, derived too.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    preserves: str
    fold_id: str
    surface: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "preserves": self.preserves, "fold_id": self.fold_id,
            "surface": self.surface,
        }


@dataclass(frozen=True)
class FoldIndex:
    """The fold index, derived from the held folds.

    The index names one entry per preserved fold, in
    held order - the fold's own target, its id and
    its title - and the folds that stand
    losable, named in its gaps. Nothing here is
    stored on any fold: the index is derived at
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


def derive_index(source: Any) -> FoldIndex:
    """Derive the fold index from the book's held folds."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(preserves=g.preserves, fold_id=g.fold_id, surface=g.surface)
        for g in book.folds if fold_passes(g))
    gaps = tuple(
        g.fold_id for g in book.folds if not fold_passes(g))
    return FoldIndex(entries=entries, gaps=gaps)


def fold_for_preserves(source: Any, preserves: Any) -> Optional[FoldCard]:
    """The first held fold one target reaches, or none - honestly."""
    wanted = _check_preserves(preserves)
    if not wanted:
        return None
    for fold in _source_book(source).folds:
        if fold.preserves == wanted:
            return fold
    return None


def note_for_fold(source: Any, fold_id: Any,
                       stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one session (and stance, when named)."""
    wanted = _clean_text(fold_id, "a session id")
    for record in _source_book(source).notes:
        if record.fold_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the fold targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


# ---------------------------------------------------------------------
# The book: folds, views and notes held together, one pinned panel
# at most per telling, and no verdict or index ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class FoldBook:
    title: str
    folds: Tuple[FoldCard, ...] = ()
    views: Tuple[FoldView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    panels: Tuple[FoldPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        folds = tuple(_check_fold_ref(g) for g in self.folds)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        panels = tuple(_check_panel_ref(p) for p in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for fold in folds:
            if fold.fold_id in seen_ids:
                raise ValueError(
                    f"two folds stand under id {fold.fold_id!r}")
            if fold.seq in seen_seqs:
                raise ValueError(
                    f"two folds stand at sequence {fold.seq}")
            seen_ids.add(fold.fold_id)
            seen_seqs.add(fold.seq)
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
            target = (record.fold_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for session "
                    f"{record.fold_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per session target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        object.__setattr__(
            self, "folds", tuple(sorted(folds, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.folds + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.fold_id for g in self.folds) + tuple(
            v.view_id for v in self.views)

    def fold_ids(self) -> Tuple[str, ...]:
        return tuple(g.fold_id for g in self.folds)

    def fold_for(self, fold_id: Any) -> FoldCard:
        wanted = _clean_text(fold_id, "a fold id")
        for fold in self.folds:
            if fold.fold_id == wanted:
                return fold
        raise KeyError(f"no fold named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> FoldView:
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
        for fold in self.folds:
            if fold.fold_id == wanted:
                return fold
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "folds": [g.to_record() for g in self.folds],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "panels": [p.to_record() for p in self.panels],
        }


def _judge_book_panels(book: FoldBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: FoldBook) -> None:
    if book.title != "Small-terminal grace at the M-193 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.folds) != 6 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold six folds and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m193-boundary":
        raise ValueError("the pinned panel is panel-m193-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "strained" or verdict.passing_shown != 5:
        raise ValueError("the shipped example book verdict must stand strained at five preserved of six")
    index = derive_index(book)
    if [e.preserves for e in index.entries] != ["the work in progress", "the board and its slice standings", "the crew roster and each worker's slice", "the file list, folded to names and standings", "the conversation and the question on the floor"]:
        raise ValueError("the shipped example book index must derive the five held preserved works in held order")
    if index.gaps != ("fold-terminal-phone",):
        raise ValueError("the shipped example book must leave the terminal fold honestly losable, named in its gaps")
    found = fold_for_preserves(book, EXAMPLE_PRESERVES)
    if found is None or found.fold_id != "fold-work-wide":
        raise ValueError("the shipped example book must reach its work fold under the example preserves")
    first = first_note(book)
    if first is None or first.note_id != "note-note-work":
        raise ValueError("the shipped example book must hold the work note as its first note road")


def validate_book(data: Any, *, require_example: bool = False) -> FoldBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, FoldBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a fold book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live terminal folding "
                f"({key!r} is named on it): {GRACE_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its folds under a view")
    if "grace_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held folds at call time")
    if data.get("schema") is not None and (
            data["schema"] != SMALL_TERMINAL_GRACE_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{SMALL_TERMINAL_GRACE_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != SMALL_TERMINAL_GRACE_SLICE):
        raise ValueError(
            f"a book's slice must be {SMALL_TERMINAL_GRACE_SLICE!r}")
    head = data.get("small_terminal_grace") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's fold head must be a mapping")
    title = head.get("title") or data.get("title")
    folds = tuple(build_fold(g) for g in data.get("folds") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    book = FoldBook(
        title=title, folds=folds, views=views, notes=notes, panels=())
    panels = tuple(
        build_panel(p, book) for p in data.get("panels") or ())
    book = FoldBook(
        title=book.title, folds=book.folds, views=book.views,
        notes=book.notes, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> FoldBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (FoldBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or a FoldBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> FoldBook:
    return validate_book(data, require_example=require_example)


def load_small_terminal_grace(
        data: Optional[Dict[str, Any]] = None) -> FoldBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(SMALL_TERMINAL_GRACE_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_small_terminal_grace_file(path: Any) -> FoldBook:
    """Load one fold file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: folds and views held one by one.
# ---------------------------------------------------------------------

class SmallTerminalGraceRegistry:
    """An in-memory holding of folds and views.

    The registry is the pure layer's model of a
    session's fold book: folds are held under
    their ids, one fold per id and per
    sequence, and views are held in recorded
    order, one view per sequence and per id.
    Holding is data only - nothing held here moves
    a pointer, clicks anything, or opens a file.
    """

    def __init__(self, book: Any = None) -> None:
        self._folds: List[FoldCard] = []
        self._views: List[FoldView] = []
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

    def register_fold(self, item: Any) -> FoldCard:
        """Hold one fold, judged whole before held."""
        checked = _check_fold_ref(item)
        return self._register(
            self._folds, checked, "fold_id", "fold")

    def register_view(self, view: Any) -> FoldView:
        """Hold one view; a view naming no id takes a fresh one."""
        checked = _check_view_ref(view)
        if not checked.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            checked = build_view({**checked.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, checked, "view_id", "view")

    def register_book(self, book: Any) -> FoldBook:
        """Hold a whole book's folds and views, under its title."""
        checked = build_book(book)
        if self._title is not None and checked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {checked.title!r}")
        for fold in checked.folds:
            self.register_fold(fold)
        for view in checked.views:
            self.register_view(view)
        self._title = checked.title
        return self.book()

    def book(self) -> FoldBook:
        return FoldBook(
            title=self._title or "An unheld fold book",
            folds=tuple(self._folds), views=tuple(self._views),
            notes=(), panels=())

    def list_folds(self) -> Tuple[FoldCard, ...]:
        return tuple(self._folds)

    def list_views(self) -> Tuple[FoldView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._folds) + tuple(self._views)

    def get_fold(self, fold_id: Any) -> FoldCard:
        return self.book().fold_for(fold_id)

    def get_view(self, view_id: Any) -> FoldView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records shaped for the journal target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> FoldBook:
    if source is None:
        return load_small_terminal_grace()
    if isinstance(source, FoldBook):
        return source
    if isinstance(source, SmallTerminalGraceRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def fold_record(fold: Any, source: Any = None) -> Dict[str, Any]:
    checked = _check_fold_ref(fold)
    record = {
        "type": "grace_fold",
        "slice": SMALL_TERMINAL_GRACE_SLICE,
        "fold_id": checked.fold_id,
        "surface": checked.surface,
        "segment": segment_of(checked),
        "passes": fold_passes(checked),
        "gaps": list(fold_gaps(checked)),
    }
    record.update(_provenance_record(checked))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    checked = _check_view_ref(view)
    record = {
        "type": "grace_view",
        "slice": SMALL_TERMINAL_GRACE_SLICE,
        "view_id": checked.view_id, "seq": checked.seq,
        "view_filter": checked.view_filter,
    }
    record.update(_provenance_record(checked))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_note_ref(record_in)
    record = {
        "type": "grace_note",
        "slice": SMALL_TERMINAL_GRACE_SLICE,
        "note_id": checked.note_id,
        "fold_id": checked.fold_id,
        "stance": checked.stance,
    }
    record.update(_provenance_record(checked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    checked = validate_panel(panel, source)
    record = {"type": "grace_panel",
              "slice": SMALL_TERMINAL_GRACE_SLICE}
    record.update(checked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, FoldVerdict):
        checked = validate_verdict(verdict, source)
    else:
        checked = derive_verdict(_source_book(verdict), view)
    record = {"type": "grace_verdict",
              "slice": SMALL_TERMINAL_GRACE_SLICE}
    record.update(checked.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, FoldIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "grace_index",
              "slice": SMALL_TERMINAL_GRACE_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    checked = _source_book(book)
    record = {"type": "grace_book",
              "slice": SMALL_TERMINAL_GRACE_SLICE,
              "title": checked.title}
    record.update(checked.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(fold: Any, source: Any = None) -> str:
    checked = _check_fold_ref(fold)
    return (
        f"{checked.surface} - kind {checked.kind}: "
        f"width {checked.width if checked.width else 'unknown'}, "
        f"height {checked.height if checked.height else 'unknown'}, "
        f"preserves {checked.preserves if checked.preserves else 'none'}. "
        f"{checked.detail}")


def fold_plain_words(fold: Any, source: Any = None) -> str:
    return plain_words(fold, source)


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The small-terminal grace stands {verdict.verdict}: "
        f"{verdict.passing_shown} of {verdict.total_shown} shown "
        f"folds stand preserved.")


def view_plain_words(view: Any) -> str:
    checked = _check_view_ref(view)
    return f"View {checked.view_id}: shows {checked.view_filter} folds."


def note_plain_words(record_in: Any) -> str:
    checked = _check_note_ref(record_in)
    return (
        f"Note {checked.note_id}: {checked.stance} "
        f"{checked.fold_id}, toward {checked.target}. "
        f"{checked.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, FoldIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} preserved works for "
        f"{len(index.entries)} folds; losable, named in "
        f"its gaps: {gaps}.")


def format_fold(fold: Any, source: Any = None) -> str:
    checked = _check_fold_ref(fold)
    lines = [f"{checked.surface} ({checked.fold_id})"]
    lines.extend(plain_lines(checked))
    lines.append(checked.detail)
    if fold_passes(checked):
        lines.append(
            "This fold stands preserved - it carries the text "
            "preserves its record names.")
    else:
        lines.append(
            "This fold stands losable - it names no text "
            "preserves, stands named in its gaps, and no preserves is "
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
        f"Fold note {checked.stance} {checked.fold_id} "
        f"({checked.note_id}): {checked.title}. {checked.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it resizes no terminal, folds no pane "
        "and posts no note.")
    return "\n".join(lines)


def format_preserves(source: Any, preserves: Any) -> str:
    fold = fold_for_preserves(source, preserves)
    if fold is not None:
        return format_fold(fold)
    wanted = _check_preserves(preserves)
    return (
        f"No held fold stands under preserves {wanted!r} yet - the "
        f"preserves reaches nothing in this book, and no fold is "
        f"invented for it.")


def format_book(source: Any = None, kind: Any = None) -> str:
    book = _source_book(source)
    folds = (folds_for_kind(book, kind)
                if kind is not None else book.folds)
    lines = [f"Splash and Grace (M-194) - {book.title}"]
    lines.extend(segment_of(fold) for fold in folds)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Grace panel under view {panel.view_id}:"]
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
    lines = ["Fold index, derived from the held folds:"]
    for entry in index.entries:
        lines.append(f"{entry.preserves} - {entry.surface} ({entry.fold_id})")
    if index.gaps:
        lines.append(
            "Losable, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "resizes no terminal and opens no network.")
    return "\n".join(lines)


def format_grace_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "Splash and Grace (M-194)",
        f"{book.title}: {len(book.folds)} folds held, "
        f"{len(passing_folds(book))} folds standing preserved, "
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


def parse_grace_args(args: Any) -> Tuple[str, Any]:
    """Parse the /grace grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("fold", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("preserves", "kind"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
