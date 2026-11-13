"""Diff theatre final form (All-Features roadmap slice M-191).

Part VIII - The Beautiful Face - builds here, with
M-091. The roadmap words: *the review screen a
user would *choose* to read code in - folding,
intra-line colour, jump-to-file, comment-on-hunk
feeding back to the coder.*

What already ships, and what this slice adds:

* M-091 diff theatre already stages one change
  two ways - unified and side-by-side - with
  word-level segments inside a changed line and a
  whitespace toggle judged and flagged, colour
  never the only signal. What nothing held is
  *the final form as a book*: the whole change
  under review held as checkable data - one card
  per hunk, held whole with its file, its kind
  (a closed vocabulary - added, removed, changed,
  mixed), its added and removed counts, and the
  jump target that reaches it in the user's editor,
  named as data; the review index, derived from
  those held hunks; the folding views, which show
  every hunk, the targeted or the untargeted;
  and the comments on hunks, held as data beside
  them - note, concern, praise and question named
  as stances, each feeding back to the coder as
  data, never posted by this layer. This slice is
  that book, in its own module, standing on the
  M-091 theatre the way the M-190 costs face
  stood on the M-189 gallery shape.

* A hunk is held whole: the file it stands in,
  its kind, its added and removed counts - held
  honestly, an unknown count standing empty,
  never invented - the jump target that reaches
  it, named as data, and its detail. A hunk
  naming no jump target is held honestly with
  an empty target: it stands untargeted, named
  in its gaps - targetedness is judged from the
  held records alone, never claimed live.
* The review index is DERIVED at call time from
  the held hunks - never a second stored copy
  that could drift from the hunks themselves.
  A stored index, targetedness verdict or
  coverage judgement on any record refuses by
  name.
* The comments are held as data: a comment
  record naming its hunk, its stance - note,
  concern, praise or question, a closed
  vocabulary - and what it feeds back toward.
  A book holds at most one comment record per
  hunk stance. Holding a comment posts none of
  it: the rule stands as data
  (:data:`THEATRE_RULE`) and a record claiming
  a jump was actually taken, a hunk actually
  applied or a comment actually posted refuses
  BY NAME.
* The shipped data file holds one example book
  in exactly the shape a real review file
  takes, a loader reads a review file anywhere
  on disk, hunks and views are shaped as session
  news, and a small in-memory registry holds
  records one by one. The agent layer owns
  holding a review book for a session and
  telling from it. This layer reaches no live
  road: it jumps to no file, applies no hunk,
  posts no comment and opens no network - it
  holds the final form as data and tells it.
  Intra-line colour stays with M-091; this book
  holds the hunks it colours, as data.

Honesty rules, enforced here and pinned by tests:

* **Targetedness from records alone.** Every
  targetedness telling is derived from the held
  hunk records; a claim of a live jump, apply
  or posted comment refuses by name.
* **Untargeted stands untargeted.** A hunk
  naming no jump target stands untargeted,
  named in its gaps - no target is invented
  for it.
* **Unknown stays unknown.** An added or
  removed count that is not known stands empty
  on its hunk - no figure is invented for it.
* **The index is derived, never stored.** The
  review index is derived from the held hunks
  at call time; a stored index refuses by name,
  so it can never drift.
* **One hunk per hunk.** Two hunks standing
  for one hunk id refuse by name, and one
  comment record stands per hunk stance.
* **The comments are data alone.** The records
  hold the feedback; holding, viewing or
  telling them jumps nowhere, applies nothing
  and posts nothing.
"""

from __future__ import annotations

__all__ = [
    "KINDS",
    "EXAMPLE_TARGET",
    "STANCES",
    "INDEX_ACTION",
    "DIFF_THEATRE_FINAL_RESOURCE",
    "DIFF_THEATRE_FINAL_SCHEMA",
    "DIFF_THEATRE_FINAL_SLICE",
    "THEATRE_RULE",
    "PLAIN_EXPLANATION",
    "THE_DIFF_THEATRE_FINAL_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "TARGET_WORDS",
    "Any",
    "Dict",
    "List",
    "Optional",
    "HunkCard",
    "IndexEntry",
    "CommentRecord",
    "TheatreBook",
    "TheatreIndex",
    "TheatrePanel",
    "TheatrePanelRow",
    "DiffTheatreFinalRegistry",
    "TheatreVerdict",
    "TheatreView",
    "TargetCount",
    "book_record",
    "build_book",
    "build_hunk",
    "build_comment",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "first_comment",
    "format_book",
    "format_hunk",
    "format_index",
    "format_comment",
    "format_theatre_screen",
    "format_panel",
    "format_target",
    "format_verdict",
    "format_view",
    "hunk_for_target",
    "hunk_gaps",
    "hunk_passes",
    "hunk_plain_words",
    "hunk_record",
    "hunks_for_kind",
    "index_plain_words",
    "index_record",
    "inspect_theatre_source",
    "comment_for_hunk",
    "comment_plain_words",
    "comment_record",
    "load_diff_theatre_final",
    "load_diff_theatre_final_file",
    "normalize_kind",
    "normalize_stance",
    "normalize_view_filter",
    "panel_plain_words",
    "panel_record",
    "parse_theatre_args",
    "passing_hunks",
    "plain_lines",
    "plain_words",
    "segment_of",
    "shown_hunks",
    "total_hunks",
    "validate_book",
    "validate_hunk",
    "validate_comment",
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

DIFF_THEATRE_FINAL_SCHEMA = "mythic.diff_theatre_final/1"
DIFF_THEATRE_FINAL_SLICE = "M-191"
THE_DIFF_THEATRE_FINAL_SLICE = DIFF_THEATRE_FINAL_SLICE
DIFF_THEATRE_FINAL_RESOURCE = "diff_theatre_final.yaml"
INDEX_ACTION = "index"
EXAMPLE_TARGET = "mythic_agent/core/session.py:128"
TARGET_WORDS = ("targeted", "untargeted")
KINDS = ("added", "removed", "changed", "mixed")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "targeted", "untargeted")
VERDICT_WORDS = ("open", "strained", "shut")
THEATRE_RULE = (
    "diff theatre final form is held as data alone: "
    "holding, viewing and reading the review "
    "jumps to no file, applies no hunk, posts no "
    "comment and opens no network - jump targets "
    "are judged from the held records alone, "
    "never claimed live")
PLAIN_EXPLANATION = (
    "Diff theatre final form (M-191): every hunk "
    "of a change stands held as a review card with "
    "its file, its kind, its added and removed "
    "counts honestly held, the jump target that "
    "reaches it in the user's editor, and the "
    "comments that feed back to the coder.")
USAGE = (
    "Usage: /theatre | /theatre hunk <hunk-id> | "
    "/theatre target <target> | /theatre kind <kind> | "
    "/theatre view <view-id> | /theatre comment <comment-id> | "
    "/theatre index | /theatre panel | /theatre verdict")

_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_HUNK_KEYS = frozenset({
    "hunk_id", "seq", "file", "kind", "added", "removed",
    "target", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "comment_id", "seq", "hunk_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "targeted", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered"})
_LIVE_KEYS = (
    "live_hunk", "live_theatre", "jumps_to_file",
    "jump_to_file", "jumped_to_file", "opens_file",
    "open_file", "applies_hunk", "applied_hunk",
    "posts_comment", "posted_comment", "feeds_back",
    "opens_network", "writes_file", "write_file",
    "live_jump", "jump_now", "comment_now",
    "performs_jump", "performs_comment")


# ---------------------------------------------------------------------
# Small judges, in the sibling shape.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_target(value: Any) -> str:
    """A held theatre target: a hunk named as data, or honestly empty.

    A hunk naming no theatre target is held with an
    empty target and stands untargeted in its gaps; a
    target that is not a string at all refuses.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("a target must be a string naming the theatre target")
    return value.strip()


def _check_measure(value: Any, what: str) -> str:
    """A held measure: added or removed, named as data or honestly empty.

    A session whose added or removed is not known is
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
                f"{what} claims a live theatre target "
                f"({key!r} is named on it): "
                f"{THEATRE_RULE}")
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
            f"comments: " + ", ".join(STANCES))
    return stance


def normalize_view_filter(value: Any) -> str:
    view_filter = _clean_text(value, "a view filter").lower()
    if view_filter not in VIEW_FILTERS:
        raise ValueError(
            f"view filter {view_filter!r} is not one of the held "
            f"filters: " + ", ".join(VIEW_FILTERS))
    return view_filter


# ---------------------------------------------------------------------
# The held hunk: one hunk, with the target that reaches it.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class HunkCard:
    """One hunk, held as data with its theatre target.

    The hunk names its title, the kind it lives
    in - one of the closed kind vocabulary - its
    kind, one of the closed hunk vocabulary,
    the theatre target that reaches it, named as data,
    and its detail. A hunk naming no theatre target
    is held with an empty target: it stands untargeted,
    named in its gaps, and no target is invented for
    it. The hunk is local data alone - no live
    target stands behind it: holding it clicks
    nothing.
    """

    hunk_id: str
    seq: int
    file: str
    kind: str
    added: str = ""
    removed: str = ""
    target: str = ""
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "hunk_id", _clean_text(self.hunk_id, "a hunk id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "file", _clean_text(self.file, "a file"))
        object.__setattr__(self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "added", _check_measure(self.added, "a added"))
        object.__setattr__(
            self, "removed", _check_measure(self.removed, "a removed"))
        object.__setattr__(self, "target", _check_target(self.target))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a hunk detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.hunk_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "hunk_id": self.hunk_id, "seq": self.seq,
            "file": self.file, "kind": self.kind,
            "added": self.added, "removed": self.removed,
            "target": self.target, "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_hunk_ref(value: Any) -> HunkCard:
    if not isinstance(value, HunkCard):
        raise ValueError("a hunk must be a HunkCard")
    return value


def validate_hunk(hunk: Any) -> HunkCard:
    return _check_hunk_ref(hunk)


def build_hunk(record: Any = None, **kwargs: Any) -> HunkCard:
    """Build one held hunk from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, HunkCard):
        if kwargs:
            raise ValueError("a hunk stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a hunk must be a mapping or a HunkCard")
    _needed(data, _HUNK_KEYS, "a hunk")
    return HunkCard(
        hunk_id=data.get("hunk_id"), seq=data.get("seq"),
        file=data.get("file"), kind=data.get("kind"),
        added=data.get("added"), removed=data.get("removed"),
        target=data.get("target"), detail=data.get("detail"),
        **_provenance(data))


def hunk_gaps(hunk: Any) -> Tuple[str, ...]:
    """The gaps that keep a hunk from the theatre."""
    checked = _check_hunk_ref(hunk)
    return () if checked.target else ("no jump target",)


def hunk_passes(hunk: Any) -> bool:
    return not hunk_gaps(hunk)


def plain_lines(hunk: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the hunk's own fields."""
    checked = _check_hunk_ref(hunk)
    return (
        f"Hunk: {checked.file}",
        f"Kind: {checked.kind}",
        f"Added: {checked.added if checked.added else 'unknown'}",
        f"Removed: {checked.removed if checked.removed else 'unknown'}",
        f"Target: {checked.target if checked.target else 'none'}",
    )


def segment_of(hunk: Any) -> str:
    checked = _check_hunk_ref(hunk)
    gaps = hunk_gaps(checked)
    return (
        f"{checked.hunk_id}: {checked.file} - kind: "
        f"'{checked.kind}' - added: "
        f"'{checked.added if checked.added else 'unknown'}' - "
        f"removed: "
        f"'{checked.removed if checked.removed else 'unknown'}' - "
        f"target: '{checked.target if checked.target else 'none'}' - "
        f"detail: '{checked.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held stance: a file at a line, with its editor target, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CommentRecord:
    """One file stance, held as data.

    The record names its file, its line number and
    the editor that stands as its target, with its
    title and its detail. One record stands per
    file line in a book. The record is data alone:
    holding it opens no file and launches no
    editor, ever.
    """

    comment_id: str
    seq: int
    hunk_id: str
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
            self, "comment_id", _clean_text(self.comment_id, "a stance id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "hunk_id", _clean_text(self.hunk_id, "a session id"))
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
        return self.comment_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "comment_id": self.comment_id, "seq": self.seq,
            "hunk_id": self.hunk_id, "stance": self.stance,
            "target": self.target, "title": self.title,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_comment_ref(value: Any) -> CommentRecord:
    if not isinstance(value, CommentRecord):
        raise ValueError("a stance must be a CommentRecord")
    return value


def validate_comment(stance: Any) -> CommentRecord:
    return _check_comment_ref(stance)


def build_comment(stance: Any = None, **kwargs: Any) -> CommentRecord:
    if stance is None:
        data = dict(kwargs)
    elif isinstance(stance, CommentRecord):
        if kwargs:
            raise ValueError("a stance stands whole or by fields, not both")
        return stance
    elif isinstance(stance, dict):
        data = dict(stance)
        data.update(kwargs)
    else:
        raise ValueError("a stance must be a mapping or a CommentRecord")
    _needed(data, _ACTION_KEYS, "a stance")
    return CommentRecord(
        comment_id=data.get("comment_id"), seq=data.get("seq"),
        hunk_id=data.get("hunk_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which hunks a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TheatreView:
    """A view over the book: every hunk, the targeted, the rest."""

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


def _check_view_ref(value: Any) -> TheatreView:
    if not isinstance(value, TheatreView):
        raise ValueError("a view must be a TheatreView")
    return value


def validate_view(view: Any) -> TheatreView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> TheatreView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, TheatreView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or a TheatreView")
    _needed(data, _VIEW_KEYS, "a view")
    return TheatreView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


def inspect_theatre_source(piece: Any) -> Dict[str, Any]:
    """Name what one theatre source piece is, without judging it."""
    if isinstance(piece, HunkCard):
        return {"kind": "hunk", "hunk_id": piece.hunk_id}
    if isinstance(piece, dict):
        if "comment_id" in piece:
            return {"kind": "comment", "comment_id": piece.get("comment_id")}
        if "view_id" in piece:
            return {"kind": "view", "view_id": piece.get("view_id")}
        if "hunk_id" in piece:
            return {"kind": "hunk", "hunk_id": piece.get("hunk_id")}
    return {"kind": "unknown", "hunk_id": None}


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TheatrePanelRow:
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


def _row_for_hunk(hunk: HunkCard) -> TheatrePanelRow:
    return TheatrePanelRow(
        item_id=hunk.hunk_id,
        standing="targeted" if hunk_passes(hunk) else "untargeted",
        label=hunk.file, segment=segment_of(hunk),
        recorded_on=hunk.recorded_on)


def _check_row_ref(value: Any) -> TheatrePanelRow:
    if not isinstance(value, TheatrePanelRow):
        raise ValueError("a panel row must be a TheatrePanelRow")
    return value


def validate_row(row: Any, hunk: Any = None) -> TheatrePanelRow:
    checked = _check_row_ref(row)
    if hunk is not None:
        derived = _row_for_hunk(_check_hunk_ref(hunk))
        if checked != derived:
            raise ValueError(
                f"panel row {checked.item_id!r} does not agree with "
                f"the row derived from its hunk")
    return checked


def build_row(row: Any = None, hunk: Any = None,
              **kwargs: Any) -> TheatrePanelRow:
    if hunk is not None:
        derived = _row_for_hunk(_check_hunk_ref(hunk))
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            TheatrePanelRow(**kwargs))
        return validate_row(built, hunk)
    if isinstance(row, TheatrePanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in TARGET_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return TheatrePanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return TheatrePanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or a TheatrePanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[TheatrePanelRow, ...]
                 ) -> Tuple[TargetCount, ...]:
    counts: List[TargetCount] = []
    for standing in TARGET_WORDS:
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
        f"The theatre book holds {total_items} hunks as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {passing_shown} of the shown hunks "
        f"stand targeted.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its hunk's own fields "
        "- the file, the kind, the added and removed "
        "honestly held and the jump target that honestly "
        "reaches it - and no judgement is stored on any hunk.",
        "Targetedness is judged from the held records alone: "
        "a hunk naming no jump target stands untargeted, and the "
        "theatre index is derived from the held hunks, "
        "never stored where it could drift.",
    )


@dataclass(frozen=True)
class TheatrePanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[TheatrePanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> TheatreView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, TheatreView):
        return view
    return book.view_for(view)


def shown_hunks(source: Any, view: Any = None
                   ) -> Tuple[HunkCard, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.hunks
    if resolved.view_filter == "targeted":
        return tuple(g for g in book.hunks if hunk_passes(g))
    return tuple(g for g in book.hunks if not hunk_passes(g))


def hunks_for_kind(source: Any, kind: Any
                      ) -> Tuple[HunkCard, ...]:
    wanted = normalize_kind(kind)
    return tuple(
        g for g in _source_book(source).hunks if g.kind == wanted)


def passing_hunks(source: Any) -> Tuple[HunkCard, ...]:
    return tuple(
        g for g in _source_book(source).hunks if hunk_passes(g))


def total_hunks(source: Any) -> int:
    return len(_source_book(source).hunks)


def derive_panel(source: Any, view: Any = None) -> TheatrePanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_hunks(book, resolved)
    rows = tuple(_row_for_hunk(hunk) for hunk in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.hunks), default="")
    passing = sum(1 for g in shown if hunk_passes(g))
    return TheatrePanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.hunks), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.hunks), len(shown), passing, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> TheatrePanel:
    if not isinstance(value, TheatrePanel):
        raise ValueError("a panel must be a TheatrePanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> TheatrePanel:
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
                **kwargs: Any) -> TheatrePanel:
    if isinstance(panel, TheatrePanel):
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
        built = TheatrePanel(
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
    raise ValueError("a panel must be a mapping, a TheatrePanel, or derived")


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
class TheatreVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> TheatreVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_hunks(book, resolved)
    passing = sum(1 for g in shown if hunk_passes(g))
    latest = max((g.recorded_on for g in shown), default="")
    return TheatreVerdict(
        verdict=_verdict_word(len(shown), passing),
        view_id=resolved.view_id, total_shown=len(shown),
        passing_shown=passing, latest_on=latest)


def _check_verdict_ref(value: Any) -> TheatreVerdict:
    if not isinstance(value, TheatreVerdict):
        raise ValueError("a verdict must be a TheatreVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> TheatreVerdict:
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
                  **kwargs: Any) -> TheatreVerdict:
    if isinstance(verdict, TheatreVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = TheatreVerdict(
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
        "a verdict must be a mapping, a TheatreVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held hunks' targets at call time, and
# the stance targets: which file comments the book holds, derived too.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    target: str
    hunk_id: str
    file: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "target": self.target, "hunk_id": self.hunk_id,
            "file": self.file,
        }


@dataclass(frozen=True)
class TheatreIndex:
    """The hunk index, derived from the held hunks.

    The index names one entry per targeted hunk, in
    held order - the hunk's own target, its id and
    its title - and the hunks that stand
    untargeted, named in its gaps. Nothing here is
    stored on any hunk: the index is derived at
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


def derive_index(source: Any) -> TheatreIndex:
    """Derive the hunk index from the book's held hunks."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(target=g.target, hunk_id=g.hunk_id, file=g.file)
        for g in book.hunks if hunk_passes(g))
    gaps = tuple(
        g.hunk_id for g in book.hunks if not hunk_passes(g))
    return TheatreIndex(entries=entries, gaps=gaps)


def hunk_for_target(source: Any, target: Any) -> Optional[HunkCard]:
    """The first held hunk one target reaches, or none - honestly."""
    wanted = _check_target(target)
    if not wanted:
        return None
    for hunk in _source_book(source).hunks:
        if hunk.target == wanted:
            return hunk
    return None


def comment_for_hunk(source: Any, hunk_id: Any,
                       stance: Any = None) -> Optional[CommentRecord]:
    """The held stance target for one session (and stance, when named)."""
    wanted = _clean_text(hunk_id, "a session id")
    for record in _source_book(source).comments:
        if record.hunk_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_comment(source: Any) -> Optional[CommentRecord]:
    """The first held stance target, standing for the theatre targets, or none."""
    comments = _source_book(source).comments
    return comments[0] if comments else None


# ---------------------------------------------------------------------
# The book: hunks, views and comments held together, one pinned panel
# at most per telling, and no verdict or index ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TheatreBook:
    title: str
    hunks: Tuple[HunkCard, ...] = ()
    views: Tuple[TheatreView, ...] = ()
    comments: Tuple[CommentRecord, ...] = ()
    panels: Tuple[TheatrePanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        hunks = tuple(_check_hunk_ref(g) for g in self.hunks)
        views = tuple(_check_view_ref(v) for v in self.views)
        comments = tuple(_check_comment_ref(m) for m in self.comments)
        panels = tuple(_check_panel_ref(p) for p in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for hunk in hunks:
            if hunk.hunk_id in seen_ids:
                raise ValueError(
                    f"two hunks stand under id {hunk.hunk_id!r}")
            if hunk.seq in seen_seqs:
                raise ValueError(
                    f"two hunks stand at sequence {hunk.seq}")
            seen_ids.add(hunk.hunk_id)
            seen_seqs.add(hunk.seq)
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
        comment_ids = set()
        comment_seqs = set()
        comment_targets = set()
        for record in comments:
            if record.comment_id in comment_ids:
                raise ValueError(
                    f"two comments stand under id {record.comment_id!r}")
            if record.seq in comment_seqs:
                raise ValueError(
                    f"two comments stand at sequence {record.seq}")
            target = (record.hunk_id, record.stance)
            if target in comment_targets:
                raise ValueError(
                    f"two stance records stand for session "
                    f"{record.hunk_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per session target")
            comment_ids.add(record.comment_id)
            comment_seqs.add(record.seq)
            comment_targets.add(target)
        object.__setattr__(
            self, "hunks", tuple(sorted(hunks, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "comments", tuple(sorted(comments, key=lambda m: m.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.hunks + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.hunk_id for g in self.hunks) + tuple(
            v.view_id for v in self.views)

    def hunk_ids(self) -> Tuple[str, ...]:
        return tuple(g.hunk_id for g in self.hunks)

    def hunk_for(self, hunk_id: Any) -> HunkCard:
        wanted = _clean_text(hunk_id, "a hunk id")
        for hunk in self.hunks:
            if hunk.hunk_id == wanted:
                return hunk
        raise KeyError(f"no hunk named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> TheatreView:
        wanted = _clean_text(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view named {wanted!r} stands in this book")

    def comment_for(self, comment_id: Any) -> CommentRecord:
        wanted = _clean_text(comment_id, "a stance id")
        for record in self.comments:
            if record.comment_id == wanted:
                return record
        raise KeyError(f"no stance named {wanted!r} stands in this book")

    def item_for(self, item_id: Any) -> Any:
        wanted = _clean_text(item_id, "an item id")
        for hunk in self.hunks:
            if hunk.hunk_id == wanted:
                return hunk
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "hunks": [g.to_record() for g in self.hunks],
            "views": [v.to_record() for v in self.views],
            "comments": [m.to_record() for m in self.comments],
            "panels": [p.to_record() for p in self.panels],
        }


def _judge_book_panels(book: TheatreBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: TheatreBook) -> None:
    if book.title != "Diff theatre final form at the M-190 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.hunks) != 6 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold six hunks and two views")
    if len(book.comments) != 2:
        raise ValueError("the shipped example book must hold two comment records")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m190-boundary":
        raise ValueError("the pinned panel is panel-m190-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "strained" or verdict.passing_shown != 5:
        raise ValueError("the shipped example book verdict must stand strained at five targeted of six")
    index = derive_index(book)
    if [e.target for e in index.entries] != ["mythic_agent/core/session.py:128", "mythic_agent/core/costs_face.py:12", "tests/test_part7_gate.py:41", "docs/gallery_guide.md:1", "mythic_agent/data/roadmap_slices.yaml:1180"]:
        raise ValueError("the shipped example book index must derive the five held targets in held order")
    if index.gaps != ("hunk-store-sweep",):
        raise ValueError("the shipped example book must leave the store sweep hunk honestly untargeted, named in its gaps")
    found = hunk_for_target(book, EXAMPLE_TARGET)
    if found is None or found.hunk_id != "hunk-login-redirect":
        raise ValueError("the shipped example book must reach its login hunk under the example target")
    first = first_comment(book)
    if first is None or first.comment_id != "comment-note-login":
        raise ValueError("the shipped example book must hold the login note comment as its first comment road")


def validate_book(data: Any, *, require_example: bool = False) -> TheatreBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, TheatreBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a theatre book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live theatre target "
                f"({key!r} is named on it): {THEATRE_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its hunks under a view")
    if "theatre_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held hunks at call time")
    if data.get("schema") is not None and (
            data["schema"] != DIFF_THEATRE_FINAL_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{DIFF_THEATRE_FINAL_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != DIFF_THEATRE_FINAL_SLICE):
        raise ValueError(
            f"a book's slice must be {DIFF_THEATRE_FINAL_SLICE!r}")
    head = data.get("theatre") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's theatre head must be a mapping")
    title = head.get("title") or data.get("title")
    hunks = tuple(build_hunk(g) for g in data.get("hunks") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    comments = tuple(build_comment(m) for m in data.get("comments") or ())
    book = TheatreBook(
        title=title, hunks=hunks, views=views, comments=comments, panels=())
    panels = tuple(
        build_panel(p, book) for p in data.get("panels") or ())
    book = TheatreBook(
        title=book.title, hunks=book.hunks, views=book.views,
        comments=book.comments, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> TheatreBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (TheatreBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or a TheatreBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> TheatreBook:
    return validate_book(data, require_example=require_example)


def load_diff_theatre_final(
        data: Optional[Dict[str, Any]] = None) -> TheatreBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(DIFF_THEATRE_FINAL_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_diff_theatre_final_file(path: Any) -> TheatreBook:
    """Load one hunk file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: hunks and views held one by one.
# ---------------------------------------------------------------------

class DiffTheatreFinalRegistry:
    """An in-memory holding of hunks and views.

    The registry is the pure layer's model of a
    session's theatre book: hunks are held under
    their ids, one hunk per id and per
    sequence, and views are held in recorded
    order, one view per sequence and per id.
    Holding is data only - nothing held here moves
    a pointer, clicks anything, or opens a file.
    """

    def __init__(self, book: Any = None) -> None:
        self._hunks: List[HunkCard] = []
        self._views: List[TheatreView] = []
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

    def register_hunk(self, item: Any) -> HunkCard:
        """Hold one hunk, judged whole before held."""
        checked = _check_hunk_ref(item)
        return self._register(
            self._hunks, checked, "hunk_id", "hunk")

    def register_view(self, view: Any) -> TheatreView:
        """Hold one view; a view naming no id takes a fresh one."""
        checked = _check_view_ref(view)
        if not checked.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            checked = build_view({**checked.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, checked, "view_id", "view")

    def register_book(self, book: Any) -> TheatreBook:
        """Hold a whole book's hunks and views, under its title."""
        checked = build_book(book)
        if self._title is not None and checked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {checked.title!r}")
        for hunk in checked.hunks:
            self.register_hunk(hunk)
        for view in checked.views:
            self.register_view(view)
        self._title = checked.title
        return self.book()

    def book(self) -> TheatreBook:
        return TheatreBook(
            title=self._title or "An unheld theatre book",
            hunks=tuple(self._hunks), views=tuple(self._views),
            comments=(), panels=())

    def list_hunks(self) -> Tuple[HunkCard, ...]:
        return tuple(self._hunks)

    def list_views(self) -> Tuple[TheatreView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._hunks) + tuple(self._views)

    def get_hunk(self, hunk_id: Any) -> HunkCard:
        return self.book().hunk_for(hunk_id)

    def get_view(self, view_id: Any) -> TheatreView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records shaped for the journal target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> TheatreBook:
    if source is None:
        return load_diff_theatre_final()
    if isinstance(source, TheatreBook):
        return source
    if isinstance(source, DiffTheatreFinalRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def hunk_record(hunk: Any, source: Any = None) -> Dict[str, Any]:
    checked = _check_hunk_ref(hunk)
    record = {
        "type": "diff_hunk",
        "slice": DIFF_THEATRE_FINAL_SLICE,
        "hunk_id": checked.hunk_id,
        "file": checked.file,
        "segment": segment_of(checked),
        "passes": hunk_passes(checked),
        "gaps": list(hunk_gaps(checked)),
    }
    record.update(_provenance_record(checked))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    checked = _check_view_ref(view)
    record = {
        "type": "theatre_view",
        "slice": DIFF_THEATRE_FINAL_SLICE,
        "view_id": checked.view_id, "seq": checked.seq,
        "view_filter": checked.view_filter,
    }
    record.update(_provenance_record(checked))
    return record


def comment_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_comment_ref(record_in)
    record = {
        "type": "theatre_comment",
        "slice": DIFF_THEATRE_FINAL_SLICE,
        "comment_id": checked.comment_id,
        "hunk_id": checked.hunk_id,
        "stance": checked.stance,
    }
    record.update(_provenance_record(checked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    checked = validate_panel(panel, source)
    record = {"type": "theatre_panel",
              "slice": DIFF_THEATRE_FINAL_SLICE}
    record.update(checked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, TheatreVerdict):
        checked = validate_verdict(verdict, source)
    else:
        checked = derive_verdict(_source_book(verdict), view)
    record = {"type": "theatre_verdict",
              "slice": DIFF_THEATRE_FINAL_SLICE}
    record.update(checked.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, TheatreIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "theatre_index",
              "slice": DIFF_THEATRE_FINAL_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    checked = _source_book(book)
    record = {"type": "theatre_book",
              "slice": DIFF_THEATRE_FINAL_SLICE,
              "title": checked.title}
    record.update(checked.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(hunk: Any, source: Any = None) -> str:
    checked = _check_hunk_ref(hunk)
    return (
        f"{checked.file} - kind {checked.kind}: "
        f"added {checked.added if checked.added else 'unknown'}, "
        f"removed {checked.removed if checked.removed else 'unknown'}, "
        f"target {checked.target if checked.target else 'none'}. "
        f"{checked.detail}")


def hunk_plain_words(hunk: Any, source: Any = None) -> str:
    return plain_words(hunk, source)


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The diff theatre final form stands {verdict.verdict}: "
        f"{verdict.passing_shown} of {verdict.total_shown} shown "
        f"hunks stand targeted.")


def view_plain_words(view: Any) -> str:
    checked = _check_view_ref(view)
    return f"View {checked.view_id}: shows {checked.view_filter} hunks."


def comment_plain_words(record_in: Any) -> str:
    checked = _check_comment_ref(record_in)
    return (
        f"Comment {checked.comment_id}: {checked.stance} "
        f"{checked.hunk_id}, toward {checked.target}. "
        f"{checked.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, TheatreIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} targets for "
        f"{len(index.entries)} hunks; untargeted, named in "
        f"its gaps: {gaps}.")


def format_hunk(hunk: Any, source: Any = None) -> str:
    checked = _check_hunk_ref(hunk)
    lines = [f"{checked.file} ({checked.hunk_id})"]
    lines.extend(plain_lines(checked))
    lines.append(checked.detail)
    if hunk_passes(checked):
        lines.append(
            "This hunk stands targeted to the theatre, under "
            "the target its record names.")
    else:
        lines.append(
            "This hunk stands untargeted - it names no theatre "
            "target, stands named in its gaps, and no target is "
            "invented for it.")
    return "\n".join(lines)


def format_view(view: Any) -> str:
    checked = _check_view_ref(view)
    return (
        f"View {checked.view_id}: filter {checked.view_filter} - "
        f"{checked.detail}")


def format_comment(record_in: Any) -> str:
    checked = _check_comment_ref(record_in)
    lines = [
        f"Hunk comment {checked.stance} {checked.hunk_id} "
        f"({checked.comment_id}): {checked.title}. {checked.detail}"]
    lines.append(
        "This comment stands held as data alone - holding "
        "or reading it jumps to no file, applies no hunk "
        "and posts no comment.")
    return "\n".join(lines)


def format_target(source: Any, target: Any) -> str:
    hunk = hunk_for_target(source, target)
    if hunk is not None:
        return format_hunk(hunk)
    wanted = _check_target(target)
    return (
        f"No held hunk stands under target {wanted!r} yet - the "
        f"target reaches nothing in this book, and no hunk is "
        f"invented for it.")


def format_book(source: Any = None, kind: Any = None) -> str:
    book = _source_book(source)
    hunks = (hunks_for_kind(book, kind)
                if kind is not None else book.hunks)
    lines = [f"Diff Theatre Final Form (M-191) - {book.title}"]
    lines.extend(segment_of(hunk) for hunk in hunks)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Theatre panel under view {panel.view_id}:"]
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
    lines = ["Hunk index, derived from the held hunks:"]
    for entry in index.entries:
        lines.append(f"{entry.target} - {entry.file} ({entry.hunk_id})")
    if index.gaps:
        lines.append(
            "Untargeted to the theatre, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "jumps to no file and opens no network.")
    return "\n".join(lines)


def format_theatre_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "Diff Theatre Final Form (M-191)",
        f"{book.title}: {len(book.hunks)} hunks held, "
        f"{len(passing_hunks(book))} hunks standing targeted, "
        f"{len(book.comments)} comments held.",
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


def parse_theatre_args(args: Any) -> Tuple[str, Any]:
    """Parse the /theatre grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("hunk", "view", "comment"):
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
