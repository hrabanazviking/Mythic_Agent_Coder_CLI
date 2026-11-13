"""Copy and share (All-Features roadmap slice M-195).

Part VIII - The Beautiful Face - builds here. The
roadmap words: *any answer, diff, or report copyable
as clean markdown; a shareable session summary
generated on command.*

What already ships, and what this slice adds:

* Answers, diffs and reports already stand in the
  session, and the M-194 small-terminal book holds
  the folding of the screen as data. What nothing
  held is *the copying and sharing itself as a
  book*: every clip held as checkable data - one
  card per clip, held whole with its heading, its
  kind (a closed vocabulary - answer, diff, report,
  code, summary), its format and its origin, held
  honestly, and the clean markdown it carries,
  named as data; the clip index, derived from those
  held clips; the views, which show every clip, the
  ready or the unready; and the notes on clips, held
  as data beside them - note, concern, praise and
  question named as stances, each feeding back to
  the user as data, never posted by this layer. This
  slice is that book, in its own module, standing
  in the M-194 small-terminal grace book shape. The
  M-171 charter names this slice on NO row - the
  grep stands empty and the slice tests pin that
  absence live - so the slice is built to the
  roadmap words alone.

* A clip is held whole: the heading it stands
  under, its kind, its format and its origin - held
  honestly, an unknown format or origin standing
  empty, never invented - the clean markdown it
  carries, named as data, and its detail. A clip
  naming no markdown body is held honestly with an
  empty markdown: it stands unready, named in its
  gaps - readiness is judged from the held records
  alone, never claimed live.
* The clip index is DERIVED at call time from the
  held clips - never a second stored copy that
  could drift from the clips themselves. A stored
  index, readiness verdict or coverage judgement
  on any record refuses by name.
* The notes are held as data: a note record naming
  its clip, its stance - note, concern, praise or
  question, a closed vocabulary - and what it feeds
  back toward. A book holds at most one note record
  per clip stance. Holding a note posts none of it:
  the rule stands as data (:data:`SHARE_RULE`) and
  a record claiming a clip was actually copied to
  a clipboard, actually shared, sent or posted
  refuses BY NAME.
* The shipped data file holds one example book in
  exactly the shape a real clip file takes, a
  loader reads a clip file anywhere on disk, clips
  and views are shaped as session news, and a small
  in-memory registry holds records one by one. The
  agent layer owns holding a clip book for a
  session and telling from it. This layer reaches
  no live road: it copies nothing to any clipboard,
  shares nothing, sends nothing, posts nothing and
  opens no network - it holds the copying and
  sharing as data and tells it.

Honesty rules, enforced here and pinned by tests:

* **Readiness from records alone.** Every readiness
  telling is derived from the held clip records; a
  claim of a live copy, share, send or post refuses
  by name.
* **Unready stands unready.** A clip naming no
  markdown body stands unready, named in its gaps -
  no markdown is invented for it.
* **Unknown stays unknown.** A format or origin
  that is not known stands empty on its clip - no
  figure is invented for it.
* **The index is derived, never stored.** The clip
  index is derived from the held clips at call time;
  a stored index refuses by name, so it can never
  drift.
* **One clip per clip.** Two clips standing for one
  clip id refuse by name, and one note record stands
  per clip stance.
* **The notes are data alone.** The records hold
  the feedback; holding, viewing or telling them
  copies nothing, shares nothing and posts nothing.
"""


from __future__ import annotations

__all__ = [
    "KINDS",
    "EXAMPLE_MARKDOWN",
    "STANCES",
    "INDEX_ACTION",
    "COPY_SHARE_RESOURCE",
    "COPY_SHARE_SCHEMA",
    "COPY_SHARE_SLICE",
    "SHARE_RULE",
    "PLAIN_EXPLANATION",
    "THE_COPY_SHARE_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "READY_WORDS",
    "Any",
    "Dict",
    "List",
    "Optional",
    "ClipCard",
    "IndexEntry",
    "NoteRecord",
    "ClipBook",
    "ClipIndex",
    "ClipPanel",
    "ClipPanelRow",
    "CopyShareRegistry",
    "ClipVerdict",
    "ClipView",
    "TargetCount",
    "book_record",
    "build_book",
    "build_clip",
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
    "format_clip",
    "format_index",
    "format_note",
    "format_share_screen",
    "format_panel",
    "format_markdown",
    "format_verdict",
    "format_view",
    "clip_for_markdown",
    "clip_gaps",
    "clip_passes",
    "clip_plain_words",
    "clip_record",
    "clips_for_kind",
    "index_plain_words",
    "index_record",
    "inspect_clip_source",
    "note_for_clip",
    "note_plain_words",
    "note_record",
    "load_copy_share",
    "load_copy_share_file",
    "normalize_kind",
    "normalize_stance",
    "normalize_view_filter",
    "panel_plain_words",
    "panel_record",
    "parse_share_args",
    "passing_clips",
    "plain_lines",
    "plain_words",
    "segment_of",
    "shown_clips",
    "total_clips",
    "validate_book",
    "validate_clip",
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

COPY_SHARE_SCHEMA = "mythic.copy_share/1"
COPY_SHARE_SLICE = "M-195"
THE_COPY_SHARE_SLICE = COPY_SHARE_SLICE
COPY_SHARE_RESOURCE = "copy_share.yaml"
INDEX_ACTION = "index"
EXAMPLE_MARKDOWN = "the answer in clean markdown"
READY_WORDS = ("ready", "unready")
KINDS = ("answer", "diff", "report", "code", "summary")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "ready", "unready")
VERDICT_WORDS = ("open", "strained", "shut")
SHARE_RULE = (
    "copy and share is held as data alone: "
    "holding, viewing and reading the clips "
    "copies nothing to any clipboard, shares "
    "nothing, sends nothing, posts nothing and "
    "opens no network - readiness is judged "
    "from the held records alone, never "
    "claimed live")
PLAIN_EXPLANATION = (
    "Copy and share (M-195): "
    "every clip stands held as a card "
    "with its heading, its kind, its format "
    "and origin honestly held, the clean "
    "markdown it carries, and the views that "
    "arrange the clips - any answer, diff, or "
    "report copyable as clean markdown, and "
    "a shareable session summary generated "
    "on command.")
USAGE = (
    "Usage: /copyshare | /copyshare clip <clip-id> | "
    "/copyshare markdown <markdown> | /copyshare kind <kind> | "
    "/copyshare view <view-id> | /copyshare note <note-id> | "
    "/copyshare index | /copyshare panel | /copyshare verdict")

_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_CLIP_KEYS = frozenset({
    "clip_id", "seq", "heading", "kind", "format", "origin",
    "markdown", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "clip_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "ready", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered"})
_LIVE_KEYS = (
    "live_clip", "live_view", "shows_clip",
    "show_clip", "shown_clip", "plays_clip",
    "played_clip", "performs_clip", "performed_clip",
    "resizes_terminal",
    "resized_terminal", "resizes_clip", "resized_clip",
    "clips_pane", "diff_pane", "clips_terminal",
    "diff_terminal", "renders_work", "rendered_work",
    "displays_clip", "displayed_clip",
    "opens_network", "writes_file", "write_file",
    "copies_to_clipboard", "copied_to_clipboard",
    "copy_to_clipboard", "copies_clip", "copied_clip",
    "shares_live", "shared_live", "share_live",
    "shares_clip", "shared_clip", "sends_clip",
    "sent_clip", "posts_clip", "posted_clip",
    "publishes_clip", "published_clip",
    "live_display", "show_now", "note_now",
    "renders_now", "posts_note", "posted_note")


# ---------------------------------------------------------------------
# Small judges, in the sibling shape.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_markdown(value: Any) -> str:
    """A held clip target: a clip named as data, or honestly empty.

    A clip naming no clip target is held with an
    empty target and stands unready in its gaps; a
    target that is not a string at all refuses.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("an markdown must be a string naming the ready work")
    return value.strip()


def _check_measure(value: Any, what: str) -> str:
    """A held measure: format or origin, named as data or honestly empty.

    A clip whose format or origin is not known is
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
                f"{what} claims a live terminal cliping "
                f"({key!r} is named on it): "
                f"{SHARE_RULE}")
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
# The held clip: one clip, with the target that reaches it.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ClipCard:
    """One share clip, held as data with its ready work.

    The clip names its heading, the kind it
    lives in - one of the closed kind vocabulary -
    its format and its origin, the text
    markdown it carries, named as data, and its
    detail. A clip naming no markdown body is
    held with an empty markdown: it stands
    unready, named in its gaps, and no
    markdown is invented for it. The clip is
    local data alone - no live showing stands
    behind it: holding it shows nothing.
    """

    clip_id: str
    seq: int
    heading: str
    kind: str
    format: str = ""
    origin: str = ""
    markdown: str = ""
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "clip_id", _clean_text(self.clip_id, "a clip id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "heading", _clean_text(self.heading, "an heading"))
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "format", _check_measure(self.format, "a format"))
        object.__setattr__(
            self, "origin", _check_measure(self.origin, "a origin"))
        object.__setattr__(
            self, "markdown", _check_markdown(self.markdown))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a clip detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.clip_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "clip_id": self.clip_id, "seq": self.seq,
            "heading": self.heading, "kind": self.kind,
            "format": self.format, "origin": self.origin,
            "markdown": self.markdown, "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_clip_ref(value: Any) -> ClipCard:
    if not isinstance(value, ClipCard):
        raise ValueError("a clip must be a ClipCard")
    return value


def validate_clip(clip: Any) -> ClipCard:
    return _check_clip_ref(clip)


def build_clip(record: Any = None, **kwargs: Any) -> ClipCard:
    """Build one held clip from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, ClipCard):
        if kwargs:
            raise ValueError("a clip stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a clip must be a mapping or a ClipCard")
    _needed(data, _CLIP_KEYS, "a clip")
    return ClipCard(
        clip_id=data.get("clip_id"), seq=data.get("seq"),
        heading=data.get("heading"), kind=data.get("kind"),
        format=data.get("format"), origin=data.get("origin"),
        markdown=data.get("markdown"), detail=data.get("detail"),
        **_provenance(data))


def clip_gaps(clip: Any) -> Tuple[str, ...]:
    """The gaps that keep a clip from the share."""
    checked = _check_clip_ref(clip)
    return () if checked.markdown else ("no markdown body",)


def clip_passes(clip: Any) -> bool:
    return not clip_gaps(clip)


def plain_lines(clip: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the clip's own fields."""
    checked = _check_clip_ref(clip)
    return (
        f"Clip: {checked.heading}",
        f"Kind: {checked.kind}",
        f"Format: {checked.format if checked.format else 'unknown'}",
        f"Origin: {checked.origin if checked.origin else 'unknown'}",
        f"Markdown: {checked.markdown if checked.markdown else 'none'}",
    )


def segment_of(clip: Any) -> str:
    checked = _check_clip_ref(clip)
    gaps = clip_gaps(checked)
    return (
        f"{checked.clip_id}: {checked.heading} - kind: "
        f"'{checked.kind}' - format: "
        f"'{checked.format if checked.format else 'unknown'}' - "
        f"origin: "
        f"'{checked.origin if checked.origin else 'unknown'}' - "
        f"markdown: '{checked.markdown if checked.markdown else 'none'}' - "
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
    clip_id: str
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
            self, "clip_id", _clean_text(self.clip_id, "a session id"))
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
            "clip_id": self.clip_id, "stance": self.stance,
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
        clip_id=data.get("clip_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which clips a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ClipView:
    """A view over the book: every clip, the ready, the rest."""

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


def _check_view_ref(value: Any) -> ClipView:
    if not isinstance(value, ClipView):
        raise ValueError("a view must be a ClipView")
    return value


def validate_view(view: Any) -> ClipView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> ClipView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, ClipView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or a ClipView")
    _needed(data, _VIEW_KEYS, "a view")
    return ClipView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


def inspect_clip_source(piece: Any) -> Dict[str, Any]:
    """Name what one clip source piece is, without judging it."""
    if isinstance(piece, ClipCard):
        return {"kind": "clip", "clip_id": piece.clip_id}
    if isinstance(piece, dict):
        if "note_id" in piece:
            return {"kind": "note", "note_id": piece.get("note_id")}
        if "view_id" in piece:
            return {"kind": "view", "view_id": piece.get("view_id")}
        if "clip_id" in piece:
            return {"kind": "clip", "clip_id": piece.get("clip_id")}
    return {"kind": "unknown", "clip_id": None}


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ClipPanelRow:
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


def _row_for_clip(clip: ClipCard) -> ClipPanelRow:
    return ClipPanelRow(
        item_id=clip.clip_id,
        standing="ready" if clip_passes(clip) else "unready",
        label=clip.heading, segment=segment_of(clip),
        recorded_on=clip.recorded_on)


def _check_row_ref(value: Any) -> ClipPanelRow:
    if not isinstance(value, ClipPanelRow):
        raise ValueError("a panel row must be a ClipPanelRow")
    return value


def validate_row(row: Any, clip: Any = None) -> ClipPanelRow:
    checked = _check_row_ref(row)
    if clip is not None:
        derived = _row_for_clip(_check_clip_ref(clip))
        if checked != derived:
            raise ValueError(
                f"panel row {checked.item_id!r} does not agree with "
                f"the row derived from its clip")
    return checked


def build_row(row: Any = None, clip: Any = None,
              **kwargs: Any) -> ClipPanelRow:
    if clip is not None:
        derived = _row_for_clip(_check_clip_ref(clip))
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            ClipPanelRow(**kwargs))
        return validate_row(built, clip)
    if isinstance(row, ClipPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in READY_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return ClipPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return ClipPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or a ClipPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[ClipPanelRow, ...]
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
        f"The share book holds {total_items} clips as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {passing_shown} of the shown clips "
        f"stand ready.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its clip's own fields "
        "- the heading, the kind, the format and origin "
        "honestly held and the ready work it honestly "
        "carries - and no judgement is stored on any clip.",
        "Preservation is judged from the held records alone: "
        "a clip naming no markdown body stands unready, and the "
        "share index is derived from the held clips, "
        "never stored where it could drift.",
    )
@dataclass(frozen=True)
class ClipPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[ClipPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> ClipView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, ClipView):
        return view
    return book.view_for(view)


def shown_clips(source: Any, view: Any = None
                   ) -> Tuple[ClipCard, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.clips
    if resolved.view_filter == "ready":
        return tuple(g for g in book.clips if clip_passes(g))
    return tuple(g for g in book.clips if not clip_passes(g))


def clips_for_kind(source: Any, kind: Any
                      ) -> Tuple[ClipCard, ...]:
    wanted = normalize_kind(kind)
    return tuple(
        g for g in _source_book(source).clips if g.kind == wanted)


def passing_clips(source: Any) -> Tuple[ClipCard, ...]:
    return tuple(
        g for g in _source_book(source).clips if clip_passes(g))


def total_clips(source: Any) -> int:
    return len(_source_book(source).clips)


def derive_panel(source: Any, view: Any = None) -> ClipPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_clips(book, resolved)
    rows = tuple(_row_for_clip(clip) for clip in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.clips), default="")
    passing = sum(1 for g in shown if clip_passes(g))
    return ClipPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.clips), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.clips), len(shown), passing, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> ClipPanel:
    if not isinstance(value, ClipPanel):
        raise ValueError("a panel must be a ClipPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> ClipPanel:
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
                **kwargs: Any) -> ClipPanel:
    if isinstance(panel, ClipPanel):
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
        built = ClipPanel(
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
    raise ValueError("a panel must be a mapping, a ClipPanel, or derived")


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
class ClipVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> ClipVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_clips(book, resolved)
    passing = sum(1 for g in shown if clip_passes(g))
    latest = max((g.recorded_on for g in shown), default="")
    return ClipVerdict(
        verdict=_verdict_word(len(shown), passing),
        view_id=resolved.view_id, total_shown=len(shown),
        passing_shown=passing, latest_on=latest)


def _check_verdict_ref(value: Any) -> ClipVerdict:
    if not isinstance(value, ClipVerdict):
        raise ValueError("a verdict must be a ClipVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> ClipVerdict:
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
                  **kwargs: Any) -> ClipVerdict:
    if isinstance(verdict, ClipVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = ClipVerdict(
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
        "a verdict must be a mapping, a ClipVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held clips' targets at call time, and
# the stance targets: which file notes the book holds, derived too.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    markdown: str
    clip_id: str
    heading: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "markdown": self.markdown, "clip_id": self.clip_id,
            "heading": self.heading,
        }


@dataclass(frozen=True)
class ClipIndex:
    """The clip index, derived from the held clips.

    The index names one entry per ready clip, in
    held order - the clip's own target, its id and
    its title - and the clips that stand
    unready, named in its gaps. Nothing here is
    stored on any clip: the index is derived at
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


def derive_index(source: Any) -> ClipIndex:
    """Derive the clip index from the book's held clips."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(markdown=g.markdown, clip_id=g.clip_id, heading=g.heading)
        for g in book.clips if clip_passes(g))
    gaps = tuple(
        g.clip_id for g in book.clips if not clip_passes(g))
    return ClipIndex(entries=entries, gaps=gaps)


def clip_for_markdown(source: Any, markdown: Any) -> Optional[ClipCard]:
    """The first held clip one target reaches, or none - honestly."""
    wanted = _check_markdown(markdown)
    if not wanted:
        return None
    for clip in _source_book(source).clips:
        if clip.markdown == wanted:
            return clip
    return None


def note_for_clip(source: Any, clip_id: Any,
                       stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one session (and stance, when named)."""
    wanted = _clean_text(clip_id, "a session id")
    for record in _source_book(source).notes:
        if record.clip_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the clip targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


# ---------------------------------------------------------------------
# The book: clips, views and notes held together, one pinned panel
# at most per telling, and no verdict or index ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ClipBook:
    title: str
    clips: Tuple[ClipCard, ...] = ()
    views: Tuple[ClipView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    panels: Tuple[ClipPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        clips = tuple(_check_clip_ref(g) for g in self.clips)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        panels = tuple(_check_panel_ref(p) for p in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for clip in clips:
            if clip.clip_id in seen_ids:
                raise ValueError(
                    f"two clips stand under id {clip.clip_id!r}")
            if clip.seq in seen_seqs:
                raise ValueError(
                    f"two clips stand at sequence {clip.seq}")
            seen_ids.add(clip.clip_id)
            seen_seqs.add(clip.seq)
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
            target = (record.clip_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for session "
                    f"{record.clip_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per session target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        object.__setattr__(
            self, "clips", tuple(sorted(clips, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.clips + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.clip_id for g in self.clips) + tuple(
            v.view_id for v in self.views)

    def clip_ids(self) -> Tuple[str, ...]:
        return tuple(g.clip_id for g in self.clips)

    def clip_for(self, clip_id: Any) -> ClipCard:
        wanted = _clean_text(clip_id, "a clip id")
        for clip in self.clips:
            if clip.clip_id == wanted:
                return clip
        raise KeyError(f"no clip named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> ClipView:
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
        for clip in self.clips:
            if clip.clip_id == wanted:
                return clip
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "clips": [g.to_record() for g in self.clips],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "panels": [p.to_record() for p in self.panels],
        }


def _judge_book_panels(book: ClipBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: ClipBook) -> None:
    if book.title != "Copy and share at the M-194 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.clips) != 6 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold six clips and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m194-boundary":
        raise ValueError("the pinned panel is panel-m194-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "strained" or verdict.passing_shown != 5:
        raise ValueError("the shipped example book verdict must stand strained at five ready of six")
    index = derive_index(book)
    if [e.markdown for e in index.entries] != ["the answer in clean markdown", "the diff in clean markdown", "the report in clean markdown", "the session summary in clean markdown", "the conversation and the question on the floor"]:
        raise ValueError("the shipped example book index must derive the five held ready works in held order")
    if index.gaps != ("clip-code-main",):
        raise ValueError("the shipped example book must leave the code clip honestly unready, named in its gaps")
    found = clip_for_markdown(book, EXAMPLE_MARKDOWN)
    if found is None or found.clip_id != "clip-answer-main":
        raise ValueError("the shipped example book must reach its work clip under the example markdown")
    first = first_note(book)
    if first is None or first.note_id != "note-note-answer":
        raise ValueError("the shipped example book must hold the work note as its first note road")


def validate_book(data: Any, *, require_example: bool = False) -> ClipBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, ClipBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a clip book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live copy or share "
                f"({key!r} is named on it): {SHARE_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its clips under a view")
    if "share_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held clips at call time")
    if data.get("schema") is not None and (
            data["schema"] != COPY_SHARE_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{COPY_SHARE_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != COPY_SHARE_SLICE):
        raise ValueError(
            f"a book's slice must be {COPY_SHARE_SLICE!r}")
    head = data.get("copy_share") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's clip head must be a mapping")
    title = head.get("title") or data.get("title")
    clips = tuple(build_clip(g) for g in data.get("clips") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    book = ClipBook(
        title=title, clips=clips, views=views, notes=notes, panels=())
    panels = tuple(
        build_panel(p, book) for p in data.get("panels") or ())
    book = ClipBook(
        title=book.title, clips=book.clips, views=book.views,
        notes=book.notes, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> ClipBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (ClipBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or a ClipBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> ClipBook:
    return validate_book(data, require_example=require_example)


def load_copy_share(
        data: Optional[Dict[str, Any]] = None) -> ClipBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(COPY_SHARE_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_copy_share_file(path: Any) -> ClipBook:
    """Load one clip file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: clips and views held one by one.
# ---------------------------------------------------------------------

class CopyShareRegistry:
    """An in-memory holding of clips and views.

    The registry is the pure layer's model of a
    session's clip book: clips are held under
    their ids, one clip per id and per
    sequence, and views are held in recorded
    order, one view per sequence and per id.
    Holding is data only - nothing held here moves
    a pointer, clicks anything, or opens a file.
    """

    def __init__(self, book: Any = None) -> None:
        self._clips: List[ClipCard] = []
        self._views: List[ClipView] = []
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

    def register_clip(self, item: Any) -> ClipCard:
        """Hold one clip, judged whole before held."""
        checked = _check_clip_ref(item)
        return self._register(
            self._clips, checked, "clip_id", "clip")

    def register_view(self, view: Any) -> ClipView:
        """Hold one view; a view naming no id takes a fresh one."""
        checked = _check_view_ref(view)
        if not checked.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            checked = build_view({**checked.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, checked, "view_id", "view")

    def register_book(self, book: Any) -> ClipBook:
        """Hold a whole book's clips and views, under its title."""
        checked = build_book(book)
        if self._title is not None and checked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {checked.title!r}")
        for clip in checked.clips:
            self.register_clip(clip)
        for view in checked.views:
            self.register_view(view)
        self._title = checked.title
        return self.book()

    def book(self) -> ClipBook:
        return ClipBook(
            title=self._title or "An unheld clip book",
            clips=tuple(self._clips), views=tuple(self._views),
            notes=(), panels=())

    def list_clips(self) -> Tuple[ClipCard, ...]:
        return tuple(self._clips)

    def list_views(self) -> Tuple[ClipView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._clips) + tuple(self._views)

    def get_clip(self, clip_id: Any) -> ClipCard:
        return self.book().clip_for(clip_id)

    def get_view(self, view_id: Any) -> ClipView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records shaped for the journal target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> ClipBook:
    if source is None:
        return load_copy_share()
    if isinstance(source, ClipBook):
        return source
    if isinstance(source, CopyShareRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def clip_record(clip: Any, source: Any = None) -> Dict[str, Any]:
    checked = _check_clip_ref(clip)
    record = {
        "type": "share_clip",
        "slice": COPY_SHARE_SLICE,
        "clip_id": checked.clip_id,
        "heading": checked.heading,
        "segment": segment_of(checked),
        "passes": clip_passes(checked),
        "gaps": list(clip_gaps(checked)),
    }
    record.update(_provenance_record(checked))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    checked = _check_view_ref(view)
    record = {
        "type": "share_view",
        "slice": COPY_SHARE_SLICE,
        "view_id": checked.view_id, "seq": checked.seq,
        "view_filter": checked.view_filter,
    }
    record.update(_provenance_record(checked))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_note_ref(record_in)
    record = {
        "type": "share_note",
        "slice": COPY_SHARE_SLICE,
        "note_id": checked.note_id,
        "clip_id": checked.clip_id,
        "stance": checked.stance,
    }
    record.update(_provenance_record(checked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    checked = validate_panel(panel, source)
    record = {"type": "share_panel",
              "slice": COPY_SHARE_SLICE}
    record.update(checked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, ClipVerdict):
        checked = validate_verdict(verdict, source)
    else:
        checked = derive_verdict(_source_book(verdict), view)
    record = {"type": "share_verdict",
              "slice": COPY_SHARE_SLICE}
    record.update(checked.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, ClipIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "share_index",
              "slice": COPY_SHARE_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    checked = _source_book(book)
    record = {"type": "share_book",
              "slice": COPY_SHARE_SLICE,
              "title": checked.title}
    record.update(checked.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(clip: Any, source: Any = None) -> str:
    checked = _check_clip_ref(clip)
    return (
        f"{checked.heading} - kind {checked.kind}: "
        f"format {checked.format if checked.format else 'unknown'}, "
        f"origin {checked.origin if checked.origin else 'unknown'}, "
        f"markdown {checked.markdown if checked.markdown else 'none'}. "
        f"{checked.detail}")


def clip_plain_words(clip: Any, source: Any = None) -> str:
    return plain_words(clip, source)


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The copy and share stands {verdict.verdict}: "
        f"{verdict.passing_shown} of {verdict.total_shown} shown "
        f"clips stand ready.")


def view_plain_words(view: Any) -> str:
    checked = _check_view_ref(view)
    return f"View {checked.view_id}: shows {checked.view_filter} clips."


def note_plain_words(record_in: Any) -> str:
    checked = _check_note_ref(record_in)
    return (
        f"Note {checked.note_id}: {checked.stance} "
        f"{checked.clip_id}, toward {checked.target}. "
        f"{checked.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, ClipIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} ready works for "
        f"{len(index.entries)} clips; unready, named in "
        f"its gaps: {gaps}.")


def format_clip(clip: Any, source: Any = None) -> str:
    checked = _check_clip_ref(clip)
    lines = [f"{checked.heading} ({checked.clip_id})"]
    lines.extend(plain_lines(checked))
    lines.append(checked.detail)
    if clip_passes(checked):
        lines.append(
            "This clip stands ready - it carries the text "
            "markdown its record names.")
    else:
        lines.append(
            "This clip stands unready - it names no text "
            "markdown, stands named in its gaps, and no markdown is "
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
        f"Clip note {checked.stance} {checked.clip_id} "
        f"({checked.note_id}): {checked.title}. {checked.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it copies nothing to any clipboard, shares nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_markdown(source: Any, markdown: Any) -> str:
    clip = clip_for_markdown(source, markdown)
    if clip is not None:
        return format_clip(clip)
    wanted = _check_markdown(markdown)
    return (
        f"No held clip stands under markdown {wanted!r} yet - the "
        f"markdown reaches nothing in this book, and no clip is "
        f"invented for it.")


def format_book(source: Any = None, kind: Any = None) -> str:
    book = _source_book(source)
    clips = (clips_for_kind(book, kind)
                if kind is not None else book.clips)
    lines = [f"Copy and Share (M-195) - {book.title}"]
    lines.extend(segment_of(clip) for clip in clips)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Share panel under view {panel.view_id}:"]
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
    lines = ["Clip index, derived from the held clips:"]
    for entry in index.entries:
        lines.append(f"{entry.markdown} - {entry.heading} ({entry.clip_id})")
    if index.gaps:
        lines.append(
            "Unready, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "copies nothing to any clipboard and opens no network.")
    return "\n".join(lines)


def format_share_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "Copy and Share (M-195)",
        f"{book.title}: {len(book.clips)} clips held, "
        f"{len(passing_clips(book))} clips standing ready, "
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


def parse_share_args(args: Any) -> Tuple[str, Any]:
    """Parse the /share grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("clip", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("markdown", "kind"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
