"""Campaigns as data (All-Features roadmap slice M-201).

Part IX - The Mythic Method Engine - opens here. The
roadmap words: *a roadmap/campaign file (parts,
slices, acceptance checks, state) the app reads,
displays (M-173), executes, and keeps current - this
roadmap is its first citizen (M-017).*

What already ships, and what this slice adds:

* The M-017 roadmap layer already holds this road's
  own 272 slices as data, and the M-173 slice board
  already displays slices as cards in columns. What
  nothing held is *the campaign file itself as a
  book*: any roadmap or campaign held as checkable
  data - one card per slice, held whole with its
  title, the part it stands in, its state in the
  board's own column vocabulary (queued, building,
  verifying, banked), its evidence held honestly
  (a slice not yet banked holds its evidence empty,
  never invented), the acceptance checks it carries,
  named as data, and its detail; the campaign index,
  derived from those held slices; the views, which
  show every slice, the ready or the unready; and
  the notes on slices, held as data beside them -
  note, concern, praise and question named as
  stances, each feeding back to the user as data,
  never posted by this layer. This slice is that
  book, in its own module, standing in the M-195
  copy-and-share book shape.

* No charter row names this slice: the M-171 TUI
  redesign charter binds Part VIII alone (M-172 to
  M-200) and names M-201 on no row, and the slice
  tests pin that absence live. The M-005 method
  charter names no slice row either: its own words
  name the whole of Part IX (M-201-M-232) as the
  part that executes the charter, and this slice -
  the range's first slice - is built to the roadmap
  words and that execution note together. The
  M-003 gap audit names the workflow slice runner
  as the method engine's owning module basis; this
  book is the data that engine reads.

* A slice is held whole: the title it stands under,
  the part it stands in, its state, its evidence -
  held honestly, a slice whose evidence is not yet
  held standing empty, never invented - the
  acceptance checks it carries, named as data, and
  its detail. A slice naming no acceptance checks
  is held honestly with empty checks: it stands
  unready, named in its gaps - readiness is judged
  from the held records alone, never claimed live.
  A slice claiming the banked state with no evidence
  held for it stands named in its gaps too: banked
  is a state with evidence, not a feeling.
* The campaign index is DERIVED at call time from
  the held slices - never a second stored copy that
  could drift from the slices themselves. A stored
  index, readiness verdict, board or current-slice
  claim on any record refuses by name.
* The display state is DERIVED for the M-173 slice
  board, never duplicated here: the board record
  reads the held slices' states through the board's
  own column vocabulary, so the campaign and the
  board can never tell two stories.
* The campaign's current slice is DERIVED at call
  time - the first held slice not yet banked, in
  held order - never stored where it could go stale:
  that is what keeping current means in this layer.
* The first citizen is proved, not asserted: the
  first-citizen record loads this repo's own roadmap
  through the M-017 layer for real and tells its
  counts - 272 slices, 11 parts, and M-201 standing
  queued at this slice's build time.
* The notes are held as data: a note record naming
  its slice, its stance - note, concern, praise or
  question, a closed vocabulary - and what it feeds
  back toward. A book holds at most one note record
  per slice stance. Holding a note posts none of
  it: the rule stands as data (:data:`CAMPAIGN_RULE`)
  and a record claiming a slice was actually
  executed, a campaign actually run or banked live,
  or a push actually made refuses BY NAME.
* The shipped data file holds one example book in
  exactly the shape a real campaign file takes, a
  loader reads a campaign file anywhere on disk,
  slices and views are shaped as session news, and
  a small in-memory registry holds records one by
  one. The agent layer owns holding a campaign book
  for a session and telling from it. This layer
  reaches no live road: it executes nothing, runs
  no campaign, banks nothing, pushes nothing and
  opens no network - it holds campaigns as data
  and tells them.

Honesty rules, enforced here and pinned by tests:

* **Readiness from records alone.** Every readiness
  telling is derived from the held slice records; a
  claim of a live execution, run, banking or push
  refuses by name.
* **Unready stands unready.** A slice naming no
  acceptance checks stands unready, named in its
  gaps - no checks are invented for it.
* **Banked carries evidence.** A slice claiming the
  banked state with no evidence held stands named
  in its gaps - no evidence is invented for it.
* **Unknown stays unknown.** An evidence line that
  is not held stands empty on its slice - no figure
  is invented for it.
* **The index, board and current slice are derived,
  never stored.** Each is derived from the held
  slices at call time; a stored one refuses by
  name, so it can never drift.
* **One slice per slice.** Two slices standing for
  one slice id refuse by name, and one note record
  stands per slice stance.
* **The notes are data alone.** The records hold
  the feedback; holding, viewing or telling them
  executes nothing, banks nothing and posts
  nothing.
"""


from __future__ import annotations

__all__ = [
    "STATES",
    "EXAMPLE_CHECKS",
    "STANCES",
    "INDEX_ACTION",
    "CAMPAIGNS_RESOURCE",
    "CAMPAIGNS_SCHEMA",
    "CAMPAIGNS_SLICE",
    "CAMPAIGN_RULE",
    "PLAIN_EXPLANATION",
    "THE_CAMPAIGNS_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "READY_WORDS",
    "Any",
    "Dict",
    "List",
    "Optional",
    "CampaignSlice",
    "IndexEntry",
    "NoteRecord",
    "CampaignBook",
    "CampaignIndex",
    "CampaignPanel",
    "CampaignPanelRow",
    "CampaignsRegistry",
    "CampaignVerdict",
    "CampaignView",
    "TargetCount",
    "board_record",
    "book_record",
    "build_book",
    "build_note",
    "build_panel",
    "build_row",
    "build_slice",
    "build_verdict",
    "build_view",
    "current_slice",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "first_citizen_record",
    "first_note",
    "format_book",
    "format_campaign_screen",
    "format_checks",
    "format_index",
    "format_note",
    "format_panel",
    "format_slice",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "load_campaigns",
    "load_campaigns_file",
    "normalize_state",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_slice",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_campaign_args",
    "passing_slices",
    "plain_lines",
    "plain_words",
    "segment_of",
    "shown_slices",
    "slice_for_checks",
    "slice_gaps",
    "slice_passes",
    "slice_record",
    "slices_for_state",
    "validate_book",
    "validate_note",
    "validate_panel",
    "validate_row",
    "validate_slice",
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

CAMPAIGNS_SCHEMA = "mythic.campaigns/1"
CAMPAIGNS_SLICE = "M-201"
THE_CAMPAIGNS_SLICE = CAMPAIGNS_SLICE
CAMPAIGNS_RESOURCE = "campaigns.yaml"
INDEX_ACTION = "index"
EXAMPLE_CHECKS = "the campaign file loads, validates and displays"
READY_WORDS = ("ready", "unready")
STATES = ("queued", "building", "verifying", "banked")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "ready", "unready")
VERDICT_WORDS = ("open", "strained", "shut")
CAMPAIGN_RULE = (
    "campaigns are held as data alone: "
    "holding, viewing and reading a campaign "
    "file executes nothing, runs no campaign, "
    "banks nothing, pushes nothing and "
    "opens no network - a campaign's state is "
    "judged from its held records and their "
    "evidence alone, never claimed live")
PLAIN_EXPLANATION = (
    "Campaigns as data (M-201): "
    "every campaign stands held as a file "
    "of parts, slices, acceptance checks "
    "and state - the app reads it, displays "
    "it on the slice board (M-173), and "
    "keeps it current; this roadmap is its "
    "first citizen (M-017).")
USAGE = (
    "Usage: /campaigns | /campaigns slice <slice-id> | "
    "/campaigns checks <checks> | /campaigns state <state> | "
    "/campaigns view <view-id> | /campaigns note <note-id> | "
    "/campaigns index | /campaigns panel | /campaigns verdict")

_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_SLICE_KEYS = frozenset({
    "slice_id", "seq", "title", "part", "state", "evidence",
    "checks", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "slice_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "ready", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered",
    "current_slice", "next_slice", "progress", "board",
    "current"})
_LIVE_KEYS = (
    "live_slice", "live_view", "shows_slice",
    "show_slice", "shown_slice", "runs_slice",
    "ran_slice", "runs_campaign", "ran_campaign",
    "executes_slice", "executed_slice",
    "executes_campaign", "executed_campaign",
    "executes_live", "runs_live", "live_execution",
    "banks_slice", "banked_live", "banking_live",
    "banks_live", "pushes_campaign", "pushed_campaign",
    "pushed_live", "merges_live", "merged_live",
    "keeper_live", "live_banking", "live_board",
    "displays_live", "displayed_live",
    "opens_network", "writes_file", "write_file",
    "sends_campaign", "sent_campaign",
    "posts_note", "posted_note")


# ---------------------------------------------------------------------
# Small judges, in the sibling shape.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_checks(value: Any) -> str:
    """A held slice target: checks named as data, or honestly empty.

    A slice naming no acceptance checks is held with
    empty checks and stands unready in its gaps; a
    checks line that is not a string at all refuses.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("checks must be a string naming the acceptance checks")
    return value.strip()


def _check_evidence(value: Any, what: str) -> str:
    """A held evidence line, named as data or honestly empty.

    A slice whose evidence is not yet held is held
    with an empty evidence line: unknown stays
    unknown, and no figure is invented for it. An
    evidence line that is not a string refuses.
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


def _check_part(value: Any, what: str = "a part") -> int:
    return _check_seq(value, what)


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
                f"{what} claims a live campaign execution "
                f"({key!r} is named on it): "
                f"{CAMPAIGN_RULE}")
    for key in mapping:
        if key in _DERIVED_KEYS:
            raise ValueError(
                f"{what} carries {key!r}, which is derived from its "
                f"own fields and never stored")
        if key not in allowed:
            raise ValueError(f"{what} carries unknown field {key!r}")


def normalize_state(value: Any) -> str:
    state = _clean_text(value, "a state").lower()
    if state not in STATES:
        raise ValueError(
            f"state {state!r} is not one of the named states: "
            + ", ".join(STATES))
    return state


def normalize_stance(value: Any) -> str:
    stance = _clean_text(value, "a stance").lower()
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
# The held slice: one campaign slice, with the checks that reach it.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CampaignSlice:
    """One campaign slice, held as data with its checks.

    The slice names its title, the part it stands
    in, its state - one of the closed state
    vocabulary, the slice board's own columns - its
    evidence, the acceptance checks it carries,
    named as data, and its detail. A slice naming
    no acceptance checks is held with empty checks:
    it stands unready, named in its gaps, and no
    checks are invented for it. A slice claiming
    the banked state with no evidence held stands
    named in its gaps too. The slice is local data
    alone - no live execution stands behind it:
    holding it runs nothing.
    """

    slice_id: str
    seq: int
    title: str
    part: int
    state: str
    evidence: str = ""
    checks: str = ""
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "slice_id", _clean_text(self.slice_id, "a slice id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(self, "part", _check_part(self.part))
        object.__setattr__(self, "state", normalize_state(self.state))
        object.__setattr__(
            self, "evidence", _check_evidence(self.evidence, "an evidence line"))
        object.__setattr__(
            self, "checks", _check_checks(self.checks))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a slice detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.slice_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "slice_id": self.slice_id, "seq": self.seq,
            "title": self.title, "part": self.part,
            "state": self.state, "evidence": self.evidence,
            "checks": self.checks, "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_slice_ref(value: Any) -> CampaignSlice:
    if not isinstance(value, CampaignSlice):
        raise ValueError("a slice must be a CampaignSlice")
    return value


def validate_slice(slice_: Any) -> CampaignSlice:
    return _check_slice_ref(slice_)


def build_slice(record: Any = None, **kwargs: Any) -> CampaignSlice:
    """Build one held slice from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, CampaignSlice):
        if kwargs:
            raise ValueError("a slice stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a slice must be a mapping or a CampaignSlice")
    _needed(data, _SLICE_KEYS, "a slice")
    return CampaignSlice(
        slice_id=data.get("slice_id"), seq=data.get("seq"),
        title=data.get("title"), part=data.get("part"),
        state=data.get("state"), evidence=data.get("evidence"),
        checks=data.get("checks"), detail=data.get("detail"),
        **_provenance(data))


def slice_gaps(slice_: Any) -> Tuple[str, ...]:
    """The gaps that keep a slice from standing ready."""
    checked = _check_slice_ref(slice_)
    gaps: List[str] = []
    if not checked.checks:
        gaps.append("no acceptance checks")
    if checked.state == "banked" and not checked.evidence:
        gaps.append("banked without evidence")
    return tuple(gaps)


def slice_passes(slice_: Any) -> bool:
    return not slice_gaps(slice_)


def plain_lines(slice_: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the slice's own fields."""
    checked = _check_slice_ref(slice_)
    return (
        f"Slice: {checked.title}",
        f"Part: {checked.part}",
        f"State: {checked.state}",
        f"Evidence: {checked.evidence if checked.evidence else 'unknown'}",
        f"Checks: {checked.checks if checked.checks else 'none'}",
    )


def segment_of(slice_: Any) -> str:
    checked = _check_slice_ref(slice_)
    gaps = slice_gaps(checked)
    return (
        f"{checked.slice_id}: {checked.title} - part: "
        f"'{checked.part}' - state: "
        f"'{checked.state}' - "
        f"evidence: "
        f"'{checked.evidence if checked.evidence else 'unknown'}' - "
        f"checks: '{checked.checks if checked.checks else 'none'}' - "
        f"detail: '{checked.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held stance: a note on a slice, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One slice stance, held as data.

    The record names its slice, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per slice stance
    in a book. The record is data alone: holding
    it executes nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    slice_id: str
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
            self, "slice_id", _clean_text(self.slice_id, "a slice id"))
        object.__setattr__(self, "stance", normalize_stance(self.stance))
        object.__setattr__(
            self, "target", _clean_text(self.target, "a stance target"))
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
            "slice_id": self.slice_id, "stance": self.stance,
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
        slice_id=data.get("slice_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which slices a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CampaignView:
    """A view over the book: every slice, the ready, the rest."""

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


def _check_view_ref(value: Any) -> CampaignView:
    if not isinstance(value, CampaignView):
        raise ValueError("a view must be a CampaignView")
    return value


def validate_view(view: Any) -> CampaignView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> CampaignView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, CampaignView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or a CampaignView")
    _needed(data, _VIEW_KEYS, "a view")
    return CampaignView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CampaignPanelRow:
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


def _row_for_slice(slice_: CampaignSlice) -> CampaignPanelRow:
    return CampaignPanelRow(
        item_id=slice_.slice_id,
        standing="ready" if slice_passes(slice_) else "unready",
        label=slice_.title, segment=segment_of(slice_),
        recorded_on=slice_.recorded_on)


def _check_row_ref(value: Any) -> CampaignPanelRow:
    if not isinstance(value, CampaignPanelRow):
        raise ValueError("a panel row must be a CampaignPanelRow")
    return value


def validate_row(row: Any, slice_: Any = None) -> CampaignPanelRow:
    checked = _check_row_ref(row)
    if slice_ is not None:
        derived = _row_for_slice(_check_slice_ref(slice_))
        if checked != derived:
            raise ValueError(
                f"panel row {checked.item_id!r} does not agree with "
                f"the row derived from its slice")
    return checked


def build_row(row: Any = None, slice_: Any = None,
              **kwargs: Any) -> CampaignPanelRow:
    if slice_ is not None:
        derived = _row_for_slice(_check_slice_ref(slice_))
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            CampaignPanelRow(**kwargs))
        return validate_row(built, slice_)
    if isinstance(row, CampaignPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in READY_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return CampaignPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return CampaignPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or a CampaignPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[CampaignPanelRow, ...]
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
        f"The campaign book holds {total_items} slices as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {passing_shown} of the shown slices "
        f"stand ready.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its slice's own fields "
        "- the title, the part, the state and evidence "
        "honestly held and the checks it honestly "
        "carries - and no judgement is stored on any slice.",
        "State is judged from the held records alone: "
        "a slice naming no acceptance checks stands unready, "
        "a slice claiming banked with no evidence stands named "
        "in its gaps, and the campaign index is derived from "
        "the held slices, never stored where it could drift.",
    )


@dataclass(frozen=True)
class CampaignPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[CampaignPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> CampaignView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, CampaignView):
        return view
    return book.view_for(view)


def shown_slices(source: Any, view: Any = None
                   ) -> Tuple[CampaignSlice, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.slices
    if resolved.view_filter == "ready":
        return tuple(g for g in book.slices if slice_passes(g))
    return tuple(g for g in book.slices if not slice_passes(g))


def slices_for_state(source: Any, state: Any
                      ) -> Tuple[CampaignSlice, ...]:
    wanted = normalize_state(state)
    return tuple(
        g for g in _source_book(source).slices if g.state == wanted)


def passing_slices(source: Any) -> Tuple[CampaignSlice, ...]:
    return tuple(
        g for g in _source_book(source).slices if slice_passes(g))


def current_slice(source: Any) -> Optional[CampaignSlice]:
    """The campaign's current slice, DERIVED at call time.

    The first held slice, in held order, whose state
    is not yet banked - where the campaign resumes.
    Nothing here is stored: the telling is derived
    from the held states alone, so it can never go
    stale against them. A campaign whose every
    slice stands banked has no current slice.
    """
    for slice_ in _source_book(source).slices:
        if slice_.state != "banked":
            return slice_
    return None


def derive_panel(source: Any, view: Any = None) -> CampaignPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_slices(book, resolved)
    rows = tuple(_row_for_slice(slice_) for slice_ in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.slices), default="")
    passing = sum(1 for g in shown if slice_passes(g))
    return CampaignPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.slices), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.slices), len(shown), passing, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> CampaignPanel:
    if not isinstance(value, CampaignPanel):
        raise ValueError("a panel must be a CampaignPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> CampaignPanel:
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
                **kwargs: Any) -> CampaignPanel:
    if isinstance(panel, CampaignPanel):
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
        built = CampaignPanel(
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
    raise ValueError("a panel must be a mapping, a CampaignPanel, or derived")


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
class CampaignVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> CampaignVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_slices(book, resolved)
    passing = sum(1 for g in shown if slice_passes(g))
    latest = max((g.recorded_on for g in shown), default="")
    return CampaignVerdict(
        verdict=_verdict_word(len(shown), passing),
        view_id=resolved.view_id, total_shown=len(shown),
        passing_shown=passing, latest_on=latest)


def _check_verdict_ref(value: Any) -> CampaignVerdict:
    if not isinstance(value, CampaignVerdict):
        raise ValueError("a verdict must be a CampaignVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> CampaignVerdict:
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
                  **kwargs: Any) -> CampaignVerdict:
    if isinstance(verdict, CampaignVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = CampaignVerdict(
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
        "a verdict must be a mapping, a CampaignVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held slices' checks at call time, and
# the stance targets: which slice notes the book holds, derived too.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    checks: str
    slice_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "checks": self.checks, "slice_id": self.slice_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class CampaignIndex:
    """The campaign index, derived from the held slices.

    The index names one entry per ready slice, in
    held order - the slice's own checks, its id and
    its title - and the slices that stand unready,
    named in its gaps. Nothing here is stored on
    any slice: the index is derived at call time
    from the held records alone, so it can never
    drift from them.
    """

    entries: Tuple[IndexEntry, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "entries": [e.to_record() for e in self.entries],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> CampaignIndex:
    """Derive the campaign index from the book's held slices."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(checks=g.checks, slice_id=g.slice_id, title=g.title)
        for g in book.slices if slice_passes(g))
    gaps = tuple(
        g.slice_id for g in book.slices if not slice_passes(g))
    return CampaignIndex(entries=entries, gaps=gaps)


def slice_for_checks(source: Any, checks: Any) -> Optional[CampaignSlice]:
    """The first held slice one checks line reaches, or none - honestly."""
    wanted = _check_checks(checks)
    if not wanted:
        return None
    for slice_ in _source_book(source).slices:
        if slice_.checks == wanted:
            return slice_
    return None


def note_for_slice(source: Any, slice_id: Any,
                       stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one slice (and stance, when named)."""
    wanted = _clean_text(slice_id, "a slice id")
    for record in _source_book(source).notes:
        if record.slice_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the slice targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def board_record(source: Any = None) -> Dict[str, Any]:
    """The display state for the M-173 slice board, DERIVED here.

    The board's own column vocabulary is read from
    the shipped slice-board layer by import - the
    campaign states ARE the board's columns, so the
    counts below are the board's counts, told once:
    this layer derives the display from the held
    slices and stores no second board of its own.
    """
    from .slice_board import COLUMNS, normalize_column
    book = _source_book(source)
    columns = []
    for column in COLUMNS:
        number = sum(
            1 for g in book.slices if normalize_column(g.state) == column)
        columns.append({"column": column, "slices": number})
    current = current_slice(book)
    return {
        "type": "campaign_board",
        "slice": CAMPAIGNS_SLICE,
        "board_slice": "M-173",
        "columns": columns,
        "total": len(book.slices),
        "current_slice": current.slice_id if current is not None else None,
    }


def first_citizen_record() -> Dict[str, Any]:
    """The first citizen, proved from the shipped roadmap itself.

    This repo's own roadmap - the M-017 data file -
    is the first campaign this book knows. The
    record loads it through the shipped roadmap
    layer for real and tells its counts as they
    stand: 272 slices in 11 parts, the banked
    prefix, the next slice where the campaign
    resumes, and M-201's own ledger standing.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(CAMPAIGNS_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "first_citizen",
        "slice": CAMPAIGNS_SLICE,
        "campaign_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m201_title": own.title,
        "m201_part": own.part,
        "m201_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: slices, views and notes held together, one pinned panel
# at most per telling, and no verdict or index ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CampaignBook:
    title: str
    slices: Tuple[CampaignSlice, ...] = ()
    views: Tuple[CampaignView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    panels: Tuple[CampaignPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        slices = tuple(_check_slice_ref(g) for g in self.slices)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        panels = tuple(_check_panel_ref(p) for p in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for slice_ in slices:
            if slice_.slice_id in seen_ids:
                raise ValueError(
                    f"two slices stand under id {slice_.slice_id!r}")
            if slice_.seq in seen_seqs:
                raise ValueError(
                    f"two slices stand at sequence {slice_.seq}")
            seen_ids.add(slice_.slice_id)
            seen_seqs.add(slice_.seq)
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
            target = (record.slice_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for slice "
                    f"{record.slice_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per slice target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        object.__setattr__(
            self, "slices", tuple(sorted(slices, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.slices + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.slice_id for g in self.slices) + tuple(
            v.view_id for v in self.views)

    def slice_ids(self) -> Tuple[str, ...]:
        return tuple(g.slice_id for g in self.slices)

    def slice_for(self, slice_id: Any) -> CampaignSlice:
        wanted = _clean_text(slice_id, "a slice id")
        for slice_ in self.slices:
            if slice_.slice_id == wanted:
                return slice_
        raise KeyError(f"no slice named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> CampaignView:
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
        for slice_ in self.slices:
            if slice_.slice_id == wanted:
                return slice_
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "slices": [g.to_record() for g in self.slices],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "panels": [p.to_record() for p in self.panels],
        }


def _judge_book_panels(book: CampaignBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: CampaignBook) -> None:
    if book.title != "Campaigns as data at the M-200 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.slices) != 6 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold six slices and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m200-boundary":
        raise ValueError("the pinned panel is panel-m200-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "strained" or verdict.passing_shown != 5:
        raise ValueError("the shipped example book verdict must stand strained at five ready of six")
    index = derive_index(book)
    if [e.checks for e in index.entries] != ["the part gate stands banked", "the campaign file loads, validates and displays", "the intent stands in the user's plain words", "each slice stands one verifiable outcome", "each slice carries its checks"]:
        raise ValueError("the shipped example book index must derive the five held ready works in held order")
    if index.gaps != ("slice-juggernaut-loop",):
        raise ValueError("the shipped example book must leave the juggernaut slice honestly unready, named in its gaps")
    found = slice_for_checks(book, EXAMPLE_CHECKS)
    if found is None or found.slice_id != "slice-campaigns-data":
        raise ValueError("the shipped example book must reach its work slice under the example checks")
    first = first_note(book)
    if first is None or first.note_id != "note-note-open":
        raise ValueError("the shipped example book must hold the work note as its first note road")


def validate_book(data: Any, *, require_example: bool = False) -> CampaignBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, CampaignBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a campaign book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live campaign execution "
                f"({key!r} is named on it): {CAMPAIGN_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its slices under a view")
    if "campaign_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held slices at call time")
    if "board" in data or "current_slice" in data:
        raise ValueError(
            "a book stores no board and no current slice: both are "
            "derived from its held slices at call time")
    if data.get("schema") is not None and (
            data["schema"] != CAMPAIGNS_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{CAMPAIGNS_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != CAMPAIGNS_SLICE):
        raise ValueError(
            f"a book's slice must be {CAMPAIGNS_SLICE!r}")
    head = data.get("campaigns") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's campaign head must be a mapping")
    title = head.get("title") or data.get("title")
    slices = tuple(build_slice(g) for g in data.get("slices") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    book = CampaignBook(
        title=title, slices=slices, views=views, notes=notes, panels=())
    panels = tuple(
        build_panel(p, book) for p in data.get("panels") or ())
    book = CampaignBook(
        title=book.title, slices=book.slices, views=book.views,
        notes=book.notes, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> CampaignBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (CampaignBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or a CampaignBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> CampaignBook:
    return validate_book(data, require_example=require_example)


def load_campaigns(
        data: Optional[Dict[str, Any]] = None) -> CampaignBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(CAMPAIGNS_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_campaigns_file(path: Any) -> CampaignBook:
    """Load one campaign file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: slices and views held one by one.
# ---------------------------------------------------------------------

class CampaignsRegistry:
    """An in-memory holding of slices and views.

    The registry is the pure layer's model of a
    session's campaign book: slices are held under
    their ids, one slice per id and per sequence,
    and views are held in recorded order, one view
    per sequence and per id. Holding is data only -
    nothing held here executes anything, banks
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[CampaignSlice] = []
        self._views: List[CampaignView] = []
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

    def register_slice(self, item: Any) -> CampaignSlice:
        """Hold one slice, judged whole before held."""
        checked = _check_slice_ref(item)
        return self._register(
            self._slices, checked, "slice_id", "slice")

    def register_view(self, view: Any) -> CampaignView:
        """Hold one view; a view naming no id takes a fresh one."""
        checked = _check_view_ref(view)
        if not checked.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            checked = build_view({**checked.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, checked, "view_id", "view")

    def register_book(self, book: Any) -> CampaignBook:
        """Hold a whole book's slices and views, under its title."""
        checked = build_book(book)
        if self._title is not None and checked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {checked.title!r}")
        for slice_ in checked.slices:
            self.register_slice(slice_)
        for view in checked.views:
            self.register_view(view)
        self._title = checked.title
        return self.book()

    def book(self) -> CampaignBook:
        return CampaignBook(
            title=self._title or "An unheld campaign book",
            slices=tuple(self._slices), views=tuple(self._views),
            notes=(), panels=())

    def list_slices(self) -> Tuple[CampaignSlice, ...]:
        return tuple(self._slices)

    def list_views(self) -> Tuple[CampaignView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._slices) + tuple(self._views)

    def get_slice(self, slice_id: Any) -> CampaignSlice:
        return self.book().slice_for(slice_id)

    def get_view(self, view_id: Any) -> CampaignView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records shaped for the journal target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> CampaignBook:
    if source is None:
        return load_campaigns()
    if isinstance(source, CampaignBook):
        return source
    if isinstance(source, CampaignsRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def slice_record(slice_: Any, source: Any = None) -> Dict[str, Any]:
    checked = _check_slice_ref(slice_)
    record = {
        "type": "campaign_slice",
        "slice": CAMPAIGNS_SLICE,
        "slice_id": checked.slice_id,
        "title": checked.title,
        "segment": segment_of(checked),
        "passes": slice_passes(checked),
        "gaps": list(slice_gaps(checked)),
    }
    record.update(_provenance_record(checked))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    checked = _check_view_ref(view)
    record = {
        "type": "campaign_view",
        "slice": CAMPAIGNS_SLICE,
        "view_id": checked.view_id, "seq": checked.seq,
        "view_filter": checked.view_filter,
    }
    record.update(_provenance_record(checked))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_note_ref(record_in)
    record = {
        "type": "campaign_note",
        "slice": CAMPAIGNS_SLICE,
        "note_id": checked.note_id,
        "slice_id": checked.slice_id,
        "stance": checked.stance,
    }
    record.update(_provenance_record(checked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    checked = validate_panel(panel, source)
    record = {"type": "campaign_panel",
              "slice": CAMPAIGNS_SLICE}
    record.update(checked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, CampaignVerdict):
        checked = validate_verdict(verdict, source)
    else:
        checked = derive_verdict(_source_book(verdict), view)
    record = {"type": "campaign_verdict",
              "slice": CAMPAIGNS_SLICE}
    record.update(checked.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, CampaignIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "campaign_index",
              "slice": CAMPAIGNS_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    checked = _source_book(book)
    record = {"type": "campaign_book",
              "slice": CAMPAIGNS_SLICE,
              "title": checked.title}
    record.update(checked.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(slice_: Any, source: Any = None) -> str:
    checked = _check_slice_ref(slice_)
    return (
        f"{checked.title} - part {checked.part}, state {checked.state}: "
        f"evidence {checked.evidence if checked.evidence else 'unknown'}, "
        f"checks {checked.checks if checked.checks else 'none'}. "
        f"{checked.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The campaigns stand {verdict.verdict}: "
        f"{verdict.passing_shown} of {verdict.total_shown} shown "
        f"slices stand ready.")


def view_plain_words(view: Any) -> str:
    checked = _check_view_ref(view)
    return f"View {checked.view_id}: shows {checked.view_filter} slices."


def note_plain_words(record_in: Any) -> str:
    checked = _check_note_ref(record_in)
    return (
        f"Note {checked.note_id}: {checked.stance} "
        f"{checked.slice_id}, toward {checked.target}. "
        f"{checked.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, CampaignIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} ready works for "
        f"{len(index.entries)} slices; unready, named in "
        f"its gaps: {gaps}.")


def format_slice(slice_: Any, source: Any = None) -> str:
    checked = _check_slice_ref(slice_)
    lines = [f"{checked.title} ({checked.slice_id})"]
    lines.extend(plain_lines(checked))
    lines.append(checked.detail)
    if slice_passes(checked):
        lines.append(
            "This slice stands ready - it carries the acceptance "
            "checks its record names.")
    else:
        lines.append(
            "This slice stands unready - it stands named in "
            f"its gaps: {', '.join(slice_gaps(checked))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)


def format_view(view: Any) -> str:
    checked = _check_view_ref(view)
    return (
        f"View {checked.view_id}: filter {checked.view_filter} - "
        f"{checked.detail}")


def format_note(record_in: Any) -> str:
    checked = _check_note_ref(record_in)
    lines = [
        f"Slice note {checked.stance} {checked.slice_id} "
        f"({checked.note_id}): {checked.title}. {checked.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it executes nothing, banks nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_checks(source: Any, checks: Any) -> str:
    slice_ = slice_for_checks(source, checks)
    if slice_ is not None:
        return format_slice(slice_)
    wanted = _check_checks(checks)
    return (
        f"No held slice stands under checks {wanted!r} yet - the "
        f"checks reach nothing in this book, and no slice is "
        f"invented for it.")


def format_book(source: Any = None, state: Any = None) -> str:
    book = _source_book(source)
    slices = (slices_for_state(book, state)
                if state is not None else book.slices)
    lines = [f"Campaigns as Data (M-201) - {book.title}"]
    lines.extend(segment_of(slice_) for slice_ in slices)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Campaign panel under view {panel.view_id}:"]
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
    lines = ["Campaign index, derived from the held slices:"]
    for entry in index.entries:
        lines.append(f"{entry.checks} - {entry.title} ({entry.slice_id})")
    if index.gaps:
        lines.append(
            "Unready, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "executes nothing, banks nothing and opens no network.")
    return "\n".join(lines)


def format_campaign_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "Campaigns as Data (M-201)",
        f"{book.title}: {len(book.slices)} slices held, "
        f"{len(passing_slices(book))} slices standing ready, "
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


def parse_campaign_args(args: Any) -> Tuple[str, Any]:
    """Parse the /campaigns grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("slice", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("checks", "state"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
