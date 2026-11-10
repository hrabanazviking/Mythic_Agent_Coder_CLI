"""Splash and ceremony, restrained (All-Features roadmap slice M-193).

Part VIII - The Beautiful Face - builds here. The
roadmap words: *the forge's face keeps its beauty
inside the Lawbook's budgets - ceremony at start
and at a roadmap's completion, quiet the rest of
the time.*

What already ships, and what this slice adds:

* The face already opens on a splash screen -
  block-character wordmark art and longship art
  over a loading spinner, held for two seconds -
  and the M-171 TUI redesign charter names that
  screen S-01 and gives it a rebuild verdict for
  this slice: *rebuild as a brief wordmark in
  plain text with a one-line status of what is
  loading, the art retired or demoted under the
  ceremony budget, and a text alternative for
  anything pictorial that stays.* What nothing
  held is *the ceremony itself as a book*: every
  ceremony moment held as checkable data - one
  card per moment, held whole with its occasion,
  its kind (a closed vocabulary - wordmark,
  status, art, silence), its duration and its
  budget, and the text alternative it carries,
  named as data; the ceremony index, derived
  from those held moments; the views, which show
  every moment, the alternated or the
  unalternated; and the notes on moments, held
  as data beside them - note, concern, praise
  and question named as stances, each feeding
  back to the user as data, never posted by this
  layer. This slice is that book, in its own
  module, standing in the M-192 multi-pane
  book shape.

* A moment is held whole: the occasion it stands
  for, its kind, its duration and its budget -
  held honestly, an unknown duration or budget
  standing empty, never invented - the text
  alternative it carries, named as data, and its
  detail. A moment naming no text alternative is
  held honestly with an empty alternative: it
  stands unalternated, named in its gaps -
  alternatedness is judged from the held records
  alone, never claimed live.
* The ceremony index is DERIVED at call time
  from the held moments - never a second stored
  copy that could drift from the moments
  themselves. A stored index, alternatedness
  verdict or coverage judgement on any record
  refuses by name.
* The notes are held as data: a note record
  naming its moment, its stance - note, concern,
  praise or question, a closed vocabulary - and
  what it feeds back toward. A book holds at
  most one note record per moment stance.
  Holding a note posts none of it: the rule
  stands as data (:data:`CEREMONY_RULE`) and a
  record claiming a ceremony was actually shown,
  played or performed refuses BY NAME.
* The shipped data file holds one example book
  in exactly the shape a real ceremony file
  takes, a loader reads a ceremony file anywhere
  on disk, moments and views are shaped as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a ceremony book for a session and
  telling from it. This layer reaches no live
  road: it shows no splash, plays no ceremony,
  performs nothing and opens no network - it
  holds the ceremony as data and tells it.

Honesty rules, enforced here and pinned by tests:

* **Alternatedness from records alone.** Every
  alternatedness telling is derived from the
  held moment records; a claim of a live show,
  play or performance refuses by name.
* **Unalternated stands unalternated.** A moment
  naming no text alternative stands unalternated,
  named in its gaps - no alternative is invented
  for it.
* **Unknown stays unknown.** A duration or budget
  that is not known stands empty on its moment -
  no figure is invented for it.
* **The index is derived, never stored.** The
  ceremony index is derived from the held moments
  at call time; a stored index refuses by name,
  so it can never drift.
* **One moment per moment.** Two moments standing
  for one moment id refuse by name, and one note
  record stands per moment stance.
* **The notes are data alone.** The records hold
  the feedback; holding, viewing or telling them
  shows nothing, plays nothing and posts nothing.
"""


from __future__ import annotations

__all__ = [
    "KINDS",
    "EXAMPLE_ALTERNATIVE",
    "STANCES",
    "INDEX_ACTION",
    "SPLASH_CEREMONY_RESOURCE",
    "SPLASH_CEREMONY_SCHEMA",
    "SPLASH_CEREMONY_SLICE",
    "CEREMONY_RULE",
    "PLAIN_EXPLANATION",
    "THE_SPLASH_CEREMONY_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "ALTERN_WORDS",
    "Any",
    "Dict",
    "List",
    "Optional",
    "MomentCard",
    "IndexEntry",
    "NoteRecord",
    "MomentBook",
    "MomentIndex",
    "MomentPanel",
    "MomentPanelRow",
    "SplashCeremonyRegistry",
    "MomentVerdict",
    "MomentView",
    "TargetCount",
    "book_record",
    "build_book",
    "build_moment",
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
    "format_moment",
    "format_index",
    "format_note",
    "format_ceremony_screen",
    "format_panel",
    "format_alternative",
    "format_verdict",
    "format_view",
    "moment_for_alternative",
    "moment_gaps",
    "moment_passes",
    "moment_plain_words",
    "moment_record",
    "moments_for_kind",
    "index_plain_words",
    "index_record",
    "inspect_moment_source",
    "note_for_moment",
    "note_plain_words",
    "note_record",
    "load_splash_ceremony",
    "load_splash_ceremony_file",
    "normalize_kind",
    "normalize_stance",
    "normalize_view_filter",
    "panel_plain_words",
    "panel_record",
    "parse_ceremony_args",
    "passing_moments",
    "plain_lines",
    "plain_words",
    "segment_of",
    "shown_moments",
    "total_moments",
    "validate_book",
    "validate_moment",
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

SPLASH_CEREMONY_SCHEMA = "mythic.splash_ceremony/1"
SPLASH_CEREMONY_SLICE = "M-193"
THE_SPLASH_CEREMONY_SLICE = SPLASH_CEREMONY_SLICE
SPLASH_CEREMONY_RESOURCE = "splash_ceremony.yaml"
INDEX_ACTION = "index"
EXAMPLE_ALTERNATIVE = "Mythic Agent Coder"
ALTERN_WORDS = ("alternated", "unalternated")
KINDS = ("wordmark", "status", "art", "silence")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "alternated", "unalternated")
VERDICT_WORDS = ("open", "strained", "shut")
CEREMONY_RULE = (
    "splash and ceremony is held as data alone: "
    "holding, viewing and reading the moments "
    "shows no splash, plays no ceremony, performs "
    "no moment and opens no network - ceremony "
    "alternatives are judged from the held records "
    "alone, never claimed live")
PLAIN_EXPLANATION = (
    "Splash and ceremony, restrained (M-193): "
    "every ceremony moment stands held as a card "
    "with its occasion, its kind, its duration "
    "and budget honestly held, the text alternative "
    "it carries, and the views that arrange the "
    "moments - ceremony at start and at a roadmap's "
    "completion, quiet the rest of the time, inside "
    "the Lawbook's budgets.")
USAGE = (
    "Usage: /ceremony | /ceremony moment <moment-id> | "
    "/ceremony alternative <alternative> | /ceremony kind <kind> | "
    "/ceremony view <view-id> | /ceremony note <note-id> | "
    "/ceremony index | /ceremony panel | /ceremony verdict")

_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_MOMENT_KEYS = frozenset({
    "moment_id", "seq", "occasion", "kind", "duration", "budget",
    "text_alternative", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "moment_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "alternated", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered"})
_LIVE_KEYS = (
    "live_moment", "live_view", "shows_moment",
    "show_moment", "shown_moment", "plays_moment",
    "played_moment", "performs_moment", "performed_moment",
    "displays_moment", "displayed_moment",
    "shows_splash", "shown_splash", "plays_ceremony",
    "opens_network", "writes_file", "write_file",
    "live_display", "show_now", "note_now",
    "performs_show", "posts_note", "posted_note")


# ---------------------------------------------------------------------
# Small judges, in the sibling shape.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_alternative(value: Any) -> str:
    """A held moment target: a moment named as data, or honestly empty.

    A moment naming no moment target is held with an
    empty target and stands unalternated in its gaps; a
    target that is not a string at all refuses.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("an alternative must be a string naming the text alternative")
    return value.strip()


def _check_measure(value: Any, what: str) -> str:
    """A held measure: duration or budget, named as data or honestly empty.

    A moment whose duration or budget is not known is
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
                f"{what} claims a live ceremony showing "
                f"({key!r} is named on it): "
                f"{CEREMONY_RULE}")
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
# The held moment: one moment, with the target that reaches it.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class MomentCard:
    """One ceremony moment, held as data with its text alternative.

    The moment names its occasion, the kind it
    lives in - one of the closed kind vocabulary -
    its duration and its budget, the text
    alternative it carries, named as data, and its
    detail. A moment naming no text alternative is
    held with an empty alternative: it stands
    unalternated, named in its gaps, and no
    alternative is invented for it. The moment is
    local data alone - no live showing stands
    behind it: holding it shows nothing.
    """

    moment_id: str
    seq: int
    occasion: str
    kind: str
    duration: str = ""
    budget: str = ""
    text_alternative: str = ""
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "moment_id", _clean_text(self.moment_id, "a moment id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "occasion", _clean_text(self.occasion, "an occasion"))
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "duration", _check_measure(self.duration, "a duration"))
        object.__setattr__(
            self, "budget", _check_measure(self.budget, "a budget"))
        object.__setattr__(
            self, "text_alternative", _check_alternative(self.text_alternative))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a moment detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.moment_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "moment_id": self.moment_id, "seq": self.seq,
            "occasion": self.occasion, "kind": self.kind,
            "duration": self.duration, "budget": self.budget,
            "text_alternative": self.text_alternative, "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_moment_ref(value: Any) -> MomentCard:
    if not isinstance(value, MomentCard):
        raise ValueError("a moment must be a MomentCard")
    return value


def validate_moment(moment: Any) -> MomentCard:
    return _check_moment_ref(moment)


def build_moment(record: Any = None, **kwargs: Any) -> MomentCard:
    """Build one held moment from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, MomentCard):
        if kwargs:
            raise ValueError("a moment stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a moment must be a mapping or a MomentCard")
    _needed(data, _MOMENT_KEYS, "a moment")
    return MomentCard(
        moment_id=data.get("moment_id"), seq=data.get("seq"),
        occasion=data.get("occasion"), kind=data.get("kind"),
        duration=data.get("duration"), budget=data.get("budget"),
        text_alternative=data.get("text_alternative"), detail=data.get("detail"),
        **_provenance(data))


def moment_gaps(moment: Any) -> Tuple[str, ...]:
    """The gaps that keep a moment from the ceremony."""
    checked = _check_moment_ref(moment)
    return () if checked.text_alternative else ("no text alternative",)


def moment_passes(moment: Any) -> bool:
    return not moment_gaps(moment)


def plain_lines(moment: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the moment's own fields."""
    checked = _check_moment_ref(moment)
    return (
        f"Moment: {checked.occasion}",
        f"Kind: {checked.kind}",
        f"Duration: {checked.duration if checked.duration else 'unknown'}",
        f"Budget: {checked.budget if checked.budget else 'unknown'}",
        f"Alternative: {checked.text_alternative if checked.text_alternative else 'none'}",
    )


def segment_of(moment: Any) -> str:
    checked = _check_moment_ref(moment)
    gaps = moment_gaps(checked)
    return (
        f"{checked.moment_id}: {checked.occasion} - kind: "
        f"'{checked.kind}' - duration: "
        f"'{checked.duration if checked.duration else 'unknown'}' - "
        f"budget: "
        f"'{checked.budget if checked.budget else 'unknown'}' - "
        f"alternative: '{checked.text_alternative if checked.text_alternative else 'none'}' - "
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
    moment_id: str
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
            self, "moment_id", _clean_text(self.moment_id, "a session id"))
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
            "moment_id": self.moment_id, "stance": self.stance,
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
        moment_id=data.get("moment_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which moments a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class MomentView:
    """A view over the book: every moment, the alternated, the rest."""

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


def _check_view_ref(value: Any) -> MomentView:
    if not isinstance(value, MomentView):
        raise ValueError("a view must be a MomentView")
    return value


def validate_view(view: Any) -> MomentView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> MomentView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, MomentView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or a MomentView")
    _needed(data, _VIEW_KEYS, "a view")
    return MomentView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


def inspect_moment_source(piece: Any) -> Dict[str, Any]:
    """Name what one moment source piece is, without judging it."""
    if isinstance(piece, MomentCard):
        return {"kind": "moment", "moment_id": piece.moment_id}
    if isinstance(piece, dict):
        if "note_id" in piece:
            return {"kind": "note", "note_id": piece.get("note_id")}
        if "view_id" in piece:
            return {"kind": "view", "view_id": piece.get("view_id")}
        if "moment_id" in piece:
            return {"kind": "moment", "moment_id": piece.get("moment_id")}
    return {"kind": "unknown", "moment_id": None}


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class MomentPanelRow:
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


def _row_for_moment(moment: MomentCard) -> MomentPanelRow:
    return MomentPanelRow(
        item_id=moment.moment_id,
        standing="alternated" if moment_passes(moment) else "unalternated",
        label=moment.occasion, segment=segment_of(moment),
        recorded_on=moment.recorded_on)


def _check_row_ref(value: Any) -> MomentPanelRow:
    if not isinstance(value, MomentPanelRow):
        raise ValueError("a panel row must be a MomentPanelRow")
    return value


def validate_row(row: Any, moment: Any = None) -> MomentPanelRow:
    checked = _check_row_ref(row)
    if moment is not None:
        derived = _row_for_moment(_check_moment_ref(moment))
        if checked != derived:
            raise ValueError(
                f"panel row {checked.item_id!r} does not agree with "
                f"the row derived from its moment")
    return checked


def build_row(row: Any = None, moment: Any = None,
              **kwargs: Any) -> MomentPanelRow:
    if moment is not None:
        derived = _row_for_moment(_check_moment_ref(moment))
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            MomentPanelRow(**kwargs))
        return validate_row(built, moment)
    if isinstance(row, MomentPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in ALTERN_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return MomentPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return MomentPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or a MomentPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[MomentPanelRow, ...]
                 ) -> Tuple[TargetCount, ...]:
    counts: List[TargetCount] = []
    for standing in ALTERN_WORDS:
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
        f"The ceremony book holds {total_items} moments as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {passing_shown} of the shown moments "
        f"stand alternated.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its moment's own fields "
        "- the occasion, the kind, the duration and budget "
        "honestly held and the text alternative it honestly "
        "carries - and no judgement is stored on any moment.",
        "Alternatedness is judged from the held records alone: "
        "a moment naming no text alternative stands unalternated, and the "
        "ceremony index is derived from the held moments, "
        "never stored where it could drift.",
    )
@dataclass(frozen=True)
class MomentPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[MomentPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> MomentView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, MomentView):
        return view
    return book.view_for(view)


def shown_moments(source: Any, view: Any = None
                   ) -> Tuple[MomentCard, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.moments
    if resolved.view_filter == "alternated":
        return tuple(g for g in book.moments if moment_passes(g))
    return tuple(g for g in book.moments if not moment_passes(g))


def moments_for_kind(source: Any, kind: Any
                      ) -> Tuple[MomentCard, ...]:
    wanted = normalize_kind(kind)
    return tuple(
        g for g in _source_book(source).moments if g.kind == wanted)


def passing_moments(source: Any) -> Tuple[MomentCard, ...]:
    return tuple(
        g for g in _source_book(source).moments if moment_passes(g))


def total_moments(source: Any) -> int:
    return len(_source_book(source).moments)


def derive_panel(source: Any, view: Any = None) -> MomentPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_moments(book, resolved)
    rows = tuple(_row_for_moment(moment) for moment in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.moments), default="")
    passing = sum(1 for g in shown if moment_passes(g))
    return MomentPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.moments), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.moments), len(shown), passing, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> MomentPanel:
    if not isinstance(value, MomentPanel):
        raise ValueError("a panel must be a MomentPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> MomentPanel:
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
                **kwargs: Any) -> MomentPanel:
    if isinstance(panel, MomentPanel):
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
        built = MomentPanel(
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
    raise ValueError("a panel must be a mapping, a MomentPanel, or derived")


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
class MomentVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> MomentVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_moments(book, resolved)
    passing = sum(1 for g in shown if moment_passes(g))
    latest = max((g.recorded_on for g in shown), default="")
    return MomentVerdict(
        verdict=_verdict_word(len(shown), passing),
        view_id=resolved.view_id, total_shown=len(shown),
        passing_shown=passing, latest_on=latest)


def _check_verdict_ref(value: Any) -> MomentVerdict:
    if not isinstance(value, MomentVerdict):
        raise ValueError("a verdict must be a MomentVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> MomentVerdict:
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
                  **kwargs: Any) -> MomentVerdict:
    if isinstance(verdict, MomentVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = MomentVerdict(
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
        "a verdict must be a mapping, a MomentVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held moments' targets at call time, and
# the stance targets: which file notes the book holds, derived too.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    alternative: str
    moment_id: str
    occasion: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "alternative": self.alternative, "moment_id": self.moment_id,
            "occasion": self.occasion,
        }


@dataclass(frozen=True)
class MomentIndex:
    """The moment index, derived from the held moments.

    The index names one entry per alternated moment, in
    held order - the moment's own target, its id and
    its title - and the moments that stand
    unalternated, named in its gaps. Nothing here is
    stored on any moment: the index is derived at
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


def derive_index(source: Any) -> MomentIndex:
    """Derive the moment index from the book's held moments."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(alternative=g.text_alternative, moment_id=g.moment_id, occasion=g.occasion)
        for g in book.moments if moment_passes(g))
    gaps = tuple(
        g.moment_id for g in book.moments if not moment_passes(g))
    return MomentIndex(entries=entries, gaps=gaps)


def moment_for_alternative(source: Any, alternative: Any) -> Optional[MomentCard]:
    """The first held moment one target reaches, or none - honestly."""
    wanted = _check_alternative(alternative)
    if not wanted:
        return None
    for moment in _source_book(source).moments:
        if moment.text_alternative == wanted:
            return moment
    return None


def note_for_moment(source: Any, moment_id: Any,
                       stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one session (and stance, when named)."""
    wanted = _clean_text(moment_id, "a session id")
    for record in _source_book(source).notes:
        if record.moment_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the moment targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


# ---------------------------------------------------------------------
# The book: moments, views and notes held together, one pinned panel
# at most per telling, and no verdict or index ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class MomentBook:
    title: str
    moments: Tuple[MomentCard, ...] = ()
    views: Tuple[MomentView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    panels: Tuple[MomentPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        moments = tuple(_check_moment_ref(g) for g in self.moments)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        panels = tuple(_check_panel_ref(p) for p in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for moment in moments:
            if moment.moment_id in seen_ids:
                raise ValueError(
                    f"two moments stand under id {moment.moment_id!r}")
            if moment.seq in seen_seqs:
                raise ValueError(
                    f"two moments stand at sequence {moment.seq}")
            seen_ids.add(moment.moment_id)
            seen_seqs.add(moment.seq)
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
            target = (record.moment_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for session "
                    f"{record.moment_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per session target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        object.__setattr__(
            self, "moments", tuple(sorted(moments, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.moments + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.moment_id for g in self.moments) + tuple(
            v.view_id for v in self.views)

    def moment_ids(self) -> Tuple[str, ...]:
        return tuple(g.moment_id for g in self.moments)

    def moment_for(self, moment_id: Any) -> MomentCard:
        wanted = _clean_text(moment_id, "a moment id")
        for moment in self.moments:
            if moment.moment_id == wanted:
                return moment
        raise KeyError(f"no moment named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> MomentView:
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
        for moment in self.moments:
            if moment.moment_id == wanted:
                return moment
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "moments": [g.to_record() for g in self.moments],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "panels": [p.to_record() for p in self.panels],
        }


def _judge_book_panels(book: MomentBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: MomentBook) -> None:
    if book.title != "Splash and ceremony at the M-192 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.moments) != 6 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold six moments and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m192-boundary":
        raise ValueError("the pinned panel is panel-m192-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "strained" or verdict.passing_shown != 5:
        raise ValueError("the shipped example book verdict must stand strained at five alternated of six")
    index = derive_index(book)
    if [e.alternative for e in index.entries] != ["Mythic Agent Coder", "Loading the forge: provider, model and tools.", "A longship under sail, drawn in line art.", "Ready - the chat stands open.", "Roadmap complete - all 272 slices stand banked."]:
        raise ValueError("the shipped example book index must derive the five held alternatives in held order")
    if index.gaps != ("moment-silence-work",):
        raise ValueError("the shipped example book must leave the silence moment honestly unalternated, named in its gaps")
    found = moment_for_alternative(book, EXAMPLE_ALTERNATIVE)
    if found is None or found.moment_id != "moment-wordmark-start":
        raise ValueError("the shipped example book must reach its wordmark moment under the example alternative")
    first = first_note(book)
    if first is None or first.note_id != "note-note-wordmark":
        raise ValueError("the shipped example book must hold the wordmark note as its first note road")


def validate_book(data: Any, *, require_example: bool = False) -> MomentBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, MomentBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a moment book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live ceremony showing "
                f"({key!r} is named on it): {CEREMONY_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its moments under a view")
    if "ceremony_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held moments at call time")
    if data.get("schema") is not None and (
            data["schema"] != SPLASH_CEREMONY_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{SPLASH_CEREMONY_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != SPLASH_CEREMONY_SLICE):
        raise ValueError(
            f"a book's slice must be {SPLASH_CEREMONY_SLICE!r}")
    head = data.get("splash_ceremony") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's moment head must be a mapping")
    title = head.get("title") or data.get("title")
    moments = tuple(build_moment(g) for g in data.get("moments") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    book = MomentBook(
        title=title, moments=moments, views=views, notes=notes, panels=())
    panels = tuple(
        build_panel(p, book) for p in data.get("panels") or ())
    book = MomentBook(
        title=book.title, moments=book.moments, views=book.views,
        notes=book.notes, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> MomentBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (MomentBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or a MomentBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> MomentBook:
    return validate_book(data, require_example=require_example)


def load_splash_ceremony(
        data: Optional[Dict[str, Any]] = None) -> MomentBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(SPLASH_CEREMONY_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_splash_ceremony_file(path: Any) -> MomentBook:
    """Load one moment file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: moments and views held one by one.
# ---------------------------------------------------------------------

class SplashCeremonyRegistry:
    """An in-memory holding of moments and views.

    The registry is the pure layer's model of a
    session's moment book: moments are held under
    their ids, one moment per id and per
    sequence, and views are held in recorded
    order, one view per sequence and per id.
    Holding is data only - nothing held here moves
    a pointer, clicks anything, or opens a file.
    """

    def __init__(self, book: Any = None) -> None:
        self._moments: List[MomentCard] = []
        self._views: List[MomentView] = []
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

    def register_moment(self, item: Any) -> MomentCard:
        """Hold one moment, judged whole before held."""
        checked = _check_moment_ref(item)
        return self._register(
            self._moments, checked, "moment_id", "moment")

    def register_view(self, view: Any) -> MomentView:
        """Hold one view; a view naming no id takes a fresh one."""
        checked = _check_view_ref(view)
        if not checked.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            checked = build_view({**checked.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, checked, "view_id", "view")

    def register_book(self, book: Any) -> MomentBook:
        """Hold a whole book's moments and views, under its title."""
        checked = build_book(book)
        if self._title is not None and checked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {checked.title!r}")
        for moment in checked.moments:
            self.register_moment(moment)
        for view in checked.views:
            self.register_view(view)
        self._title = checked.title
        return self.book()

    def book(self) -> MomentBook:
        return MomentBook(
            title=self._title or "An unheld moment book",
            moments=tuple(self._moments), views=tuple(self._views),
            notes=(), panels=())

    def list_moments(self) -> Tuple[MomentCard, ...]:
        return tuple(self._moments)

    def list_views(self) -> Tuple[MomentView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._moments) + tuple(self._views)

    def get_moment(self, moment_id: Any) -> MomentCard:
        return self.book().moment_for(moment_id)

    def get_view(self, view_id: Any) -> MomentView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records shaped for the journal target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> MomentBook:
    if source is None:
        return load_splash_ceremony()
    if isinstance(source, MomentBook):
        return source
    if isinstance(source, SplashCeremonyRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def moment_record(moment: Any, source: Any = None) -> Dict[str, Any]:
    checked = _check_moment_ref(moment)
    record = {
        "type": "ceremony_moment",
        "slice": SPLASH_CEREMONY_SLICE,
        "moment_id": checked.moment_id,
        "occasion": checked.occasion,
        "segment": segment_of(checked),
        "passes": moment_passes(checked),
        "gaps": list(moment_gaps(checked)),
    }
    record.update(_provenance_record(checked))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    checked = _check_view_ref(view)
    record = {
        "type": "ceremony_view",
        "slice": SPLASH_CEREMONY_SLICE,
        "view_id": checked.view_id, "seq": checked.seq,
        "view_filter": checked.view_filter,
    }
    record.update(_provenance_record(checked))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_note_ref(record_in)
    record = {
        "type": "ceremony_note",
        "slice": SPLASH_CEREMONY_SLICE,
        "note_id": checked.note_id,
        "moment_id": checked.moment_id,
        "stance": checked.stance,
    }
    record.update(_provenance_record(checked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    checked = validate_panel(panel, source)
    record = {"type": "ceremony_panel",
              "slice": SPLASH_CEREMONY_SLICE}
    record.update(checked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, MomentVerdict):
        checked = validate_verdict(verdict, source)
    else:
        checked = derive_verdict(_source_book(verdict), view)
    record = {"type": "ceremony_verdict",
              "slice": SPLASH_CEREMONY_SLICE}
    record.update(checked.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, MomentIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "ceremony_index",
              "slice": SPLASH_CEREMONY_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    checked = _source_book(book)
    record = {"type": "ceremony_book",
              "slice": SPLASH_CEREMONY_SLICE,
              "title": checked.title}
    record.update(checked.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(moment: Any, source: Any = None) -> str:
    checked = _check_moment_ref(moment)
    return (
        f"{checked.occasion} - kind {checked.kind}: "
        f"duration {checked.duration if checked.duration else 'unknown'}, "
        f"budget {checked.budget if checked.budget else 'unknown'}, "
        f"alternative {checked.text_alternative if checked.text_alternative else 'none'}. "
        f"{checked.detail}")


def moment_plain_words(moment: Any, source: Any = None) -> str:
    return plain_words(moment, source)


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The splash ceremony stands {verdict.verdict}: "
        f"{verdict.passing_shown} of {verdict.total_shown} shown "
        f"moments stand alternated.")


def view_plain_words(view: Any) -> str:
    checked = _check_view_ref(view)
    return f"View {checked.view_id}: shows {checked.view_filter} moments."


def note_plain_words(record_in: Any) -> str:
    checked = _check_note_ref(record_in)
    return (
        f"Note {checked.note_id}: {checked.stance} "
        f"{checked.moment_id}, toward {checked.target}. "
        f"{checked.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, MomentIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} alternatives for "
        f"{len(index.entries)} moments; unalternated, named in "
        f"its gaps: {gaps}.")


def format_moment(moment: Any, source: Any = None) -> str:
    checked = _check_moment_ref(moment)
    lines = [f"{checked.occasion} ({checked.moment_id})"]
    lines.extend(plain_lines(checked))
    lines.append(checked.detail)
    if moment_passes(checked):
        lines.append(
            "This moment stands alternated - it carries the text "
            "alternative its record names.")
    else:
        lines.append(
            "This moment stands unalternated - it names no text "
            "alternative, stands named in its gaps, and no alternative is "
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
        f"Moment note {checked.stance} {checked.moment_id} "
        f"({checked.note_id}): {checked.title}. {checked.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it shows no splash, plays no ceremony "
        "and posts no note.")
    return "\n".join(lines)


def format_alternative(source: Any, alternative: Any) -> str:
    moment = moment_for_alternative(source, alternative)
    if moment is not None:
        return format_moment(moment)
    wanted = _check_alternative(alternative)
    return (
        f"No held moment stands under alternative {wanted!r} yet - the "
        f"alternative reaches nothing in this book, and no moment is "
        f"invented for it.")


def format_book(source: Any = None, kind: Any = None) -> str:
    book = _source_book(source)
    moments = (moments_for_kind(book, kind)
                if kind is not None else book.moments)
    lines = [f"Splash and Ceremony (M-193) - {book.title}"]
    lines.extend(segment_of(moment) for moment in moments)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Ceremony panel under view {panel.view_id}:"]
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
    lines = ["Moment index, derived from the held moments:"]
    for entry in index.entries:
        lines.append(f"{entry.alternative} - {entry.occasion} ({entry.moment_id})")
    if index.gaps:
        lines.append(
            "Unalternated, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "shows no splash and opens no network.")
    return "\n".join(lines)


def format_ceremony_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "Splash and Ceremony (M-193)",
        f"{book.title}: {len(book.moments)} moments held, "
        f"{len(passing_moments(book))} moments standing alternated, "
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


def parse_ceremony_args(args: Any) -> Tuple[str, Any]:
    """Parse the /ceremony grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("moment", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("alternative", "kind"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
