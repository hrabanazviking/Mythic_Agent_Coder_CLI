"""Roads (roadmap slice M-218).

Part IX - The Mythic Method Engine. The roadmap
words: **Volmarr's Mimisbrunnr roadmap loadable as a campaign file (via the M-002 concordance) - his own road, runnable.*

What already ships, and what this slice adds:

* The roads book already ships as data
  (M-201, ``core/roads.py``): a roadmap/road
  file (parts, slices, acceptance checks, state) the
  app reads. This slice WIRES the mimis that book's
  mimis invites - several roads held across
  concordances with one well over them - as data, in its
  own module, standing in the M-195 copy-and-share
  book mimis the M-218 book stands in: one roadkeeper
  per mimis, and the roadkeeper's charge over one
  road across its concordance held as a book - a
  road. The shipped roads stand untouched behind
  their seams: this layer holds roads as data
  over the mimis's concordances and rewrites none of them,
  and the roads book keeps its own standing.
  Roads stand on the well AS DATA alone: a
  road carries a well ref, a reference held in
  this book; holding, viewing or telling a road
  runs no road live, moves no keeper and files
  nothing.
* No charter row names this slice: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-218 on no row, and the
  slice tests pin that absence live. The M-005
  method charter names no slice row either: its
  own words name the whole of Part IX as the
  part that executes the charter, and this slice
  is built to the roadmap words and that
  execution note together.

* A road is held whole: the slice it
  answers for, named by its slice id; its title;
  the road steps it walked, held as data in
  walk order; and the evidence it carries, held
  as data by concordance. The road walk is EXPLICIT:
  its sequence stands as data
  (:data:`CHECKS`, :data:`TRANSITIONS`) -
  charted, loaded, mapped, verified, runnable -
  and a road's standing is DERIVED at
  call time from its held steps and evidence
  alone: a road that opens anywhere but
  charted, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet reached runnable stands
  open, named in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - concordance_ref,
  well_ref, keeper_record, run_ref, evidence
  a roadkeeper can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A road is
  verified from held evidence alone, never
  from a feeling: a road holding a
  bare claim stands open, named in its gaps.
* A road stands only for an ACTIVE
  slice. The book holds each slice it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  road naming a slice that stands
  nowhere in the book refuses BY NAME, and a
  road for a slice that is not active
  refuses BY NAME beside it: the roadkeeper deals with
  the slice in hand, in roadmap order, never a
  queued one, and a slice whose road already
  stands complete is never mapped twice - the
  current road is derived, so a
  completed slice is never the current road
  twice.
* The road's trace is visible. A trace
  record holds one road's walked steps
  as one trace line, exactly as walked, beside
  the road. The derived trace is
  computed at call time from the road's
  held steps; a held trace that no longer agrees
  with it stands stale, named in the well - the
  trace is the walk itself, never a retelling
  of it.
* The road index is DERIVED at call
  time from the held roads - one entry
  per complete road, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, order or current-road
  claim on any record refuses by name.
* The current road is DERIVED at call
  time - the first held road, in held
  order, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its road, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per road stance; holding
  a note posts none of it, the rule stands as
  data (:data:`ROAD_RULE`), and a record
  claiming a road was actually runnable,
  captured or promoted live refuses BY NAME.
  The roadkeeper reports - and those reports, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the mimis a real road
  file takes, a loader reads a file anywhere on
  disk, roads and views are loaded as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a road book for a session and
  telling from it. This layer reaches no live
  road: it writes no road live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no roadkeeper, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds roads
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The road walk is explicit.** A
  road is verified against the held
  steps and legal steps alone; an illegal step
  stands named in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  road that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, named in its gaps:
  a road is verified from evidence, not
  vibes.
* **Active slices only, in roadmap order.** A
  road for a missing or queued slice
  refuses by name; no road is invented
  for a slice the roadkeeper has not dealt with.
* **Unknown stays unknown.** A road
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, order
  and current road are derived, never
  stored.** Each is derived from the held
  roads at call time; a stored one
  refuses by name, so it can never drift.
* **One road per road.** Two
  roads standing for one road id
  refuse by name, and one note record stands per
  road stance.
* **The notes are data alone.** The records
  hold the feedback; holding, viewing or telling
  them writes nothing, files nothing and posts
  nothing.
"""


from __future__ import annotations

__all__ = [
    "CHECK_FIELDS",
    "CHECKS",
    "CLAIM_CONCORDANCES",
    "HELD_EVIDENCE",
    "BARE_CLAIMS",
    "TRANSITIONS",
    "EXAMPLE_CHECK",
    "STANCES",
    "INDEX_ACTION",
    "ROAD_RESOURCE",
    "ROAD_SCHEMA",
    "ROAD_SLICE",
    "ROAD_RULE",
    "PLAIN_EXPLANATION",
    "THE_ROAD_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "COMPLETE_WORDS",
    "CONCORDANCE_STATES",
    "Any",
    "Dict",
    "List",
    "Optional",
    "TraceRecord",
    "RoadRecord",
    "IndexEntry",
    "ConcordanceRef",
    "NoteRecord",
    "RoadBook",
    "RoadIndex",
    "RoadPanel",
    "RoadPanelRow",
    "RoadRegistry",
    "RoadVerdict",
    "RoadView",
    "TargetCount",
    "trace_for_road",
    "trace_record",
    "well_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_road",
    "build_concordance_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_road",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "road_for_check",
    "road_order",
    "road_record",
    "first_note",
    "format_book",
    "format_road",
    "format_index",
    "format_note",
    "format_check",
    "format_panel",
    "format_road_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "concordance_record",
    "load_road",
    "load_road_file",
    "normalize_concordance_state",
    "normalize_check",
    "normalize_claim_concordance",
    "legal_step",
    "next_check",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_road",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_road_args",
    "green_roads",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_roads",
    "validate_trace",
    "validate_book",
    "validate_road",
    "validate_concordance_ref",
    "validate_note",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
    "road_gaps",
    "road_green",
    "roads_for_concordance",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

ROAD_SCHEMA = "mythic.mimisbrunnr_road/1"
ROAD_SLICE = "M-218"
THE_ROAD_SLICE = ROAD_SLICE
ROAD_RESOURCE = "mimisbrunnr_road.yaml"
INDEX_ACTION = "index"
EXAMPLE_CHECK = "runnable"
CHECK_FIELDS = ("checks", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("runnable", "held", "blocked")
CONCORDANCE_STATES = ("live", "dormant")
ROAD_RULE = 'roads are held as data alone: several roads across concordances stand with one well, keepers per road, and the human sees the whole forge at a run - a run stands as data, held by reference (a run ref), never taken live - the road walk stands as an explicit road sequence - charted, loaded, mapped, verified, runnable - and a road completes only complete, complete being a state with evidence held - concordance ref, well ref, keeper record, run ref - never a feeling, a memory, an assertion or a summary; holding, viewing and reading a road runs no road live, approves nothing, spawns no process and opens no network'
PLAIN_EXPLANATION = "The 500-slice road as a campaign (M-218): Volmarr's Mimisbrunnr roadmap loadable as a campaign file (via the M-002 concordance) - his own road, runnable."
USAGE = 'Usage: /mimis | /mimis road <road-id> | /mimis check <check> | /mimis concordance <concordance-id> | /mimis view <view-id> | /mimis note <note-id> | /mimis index | /mimis panel | /mimis verdict'

CHECKS = ("charted", "loaded", "mapped", "verified", "runnable")
HELD_EVIDENCE = ("concordance_ref", "well_ref", "keeper_record", "run_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_CONCORDANCES = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "charted": ("loaded",),
    "loaded": ("mapped",),
    "mapped": ("verified",),
    "verified": ("charted", "runnable"),
    "runnable": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a failure or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a road stands complete.
    A check outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_check(check: Any, failed: Any = False) -> Optional[str]:
    """The step the roadkeeper takes next, DERIVED from the sequence.

    Banked leads to loaded and loaded to
    mapped; mapped leads to verified; at
    verified a follow-up banking steps back to charted and a finished road steps to runnable;
    runnable is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    verified = normalize_check(check)
    if verified == "charted":
        return "loaded"
    if verified == "loaded":
        return "mapped"
    if verified == "mapped":
        return "verified"
    if verified == "verified":
        return "charted" if failed else "runnable"
    return None


_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "road_id", "seq", "concordance_id", "title", "checks",
    "claims", "detail",
} | set(_PROVENANCE))
_SLICE_REF_KEYS = frozenset({
    "concordance_id", "seq", "title", "state", "detail",
} | set(_PROVENANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "road_id", "trace", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "road_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered",
    "current_road", "next_road", "progress", "well",
    "current", "order", "breaks", "live"})
_LIVE_KEYS = (
    "live_road", "roads_live", "live_question",
    "roads_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "resumes_live",
    "resumed_live", "pauses_road", "paused_live",
    "runs_road", "ran_road", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "road_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_road", "sent_road",
    "posts_note", "posted_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_road", "filed_live", "spawns_roadkeeper", "spawned_roadkeeper", "sends_road", "sent_road", "writes_road", "wrote_road")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_checks(value: Any) -> Tuple[str, ...]:
    """A road's walked checks, held as data.

    The checks stand as a list of check names in
    walk order, each one a check of the explicit
    gate sequence; a walk not yet held stands
    honestly empty - no check is invented - and
    a name outside the machine refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("checks must be a list of gate sequence checks")
    return tuple(normalize_check(v) for v in value)

def _check_claims(value: Any) -> Tuple[str, ...]:
    """A road's asked claims: claim concordances named as data.

    Each claim names one concordance from the runnable
    vocabulary - the human concordances the gate may ask
    and the code concordances it must never ask, both
    held honestly as data - and a concordance outside
    the vocabulary refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("claims must be a list of claim concordances")
    return tuple(normalize_claim_concordance(v) for v in value)

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
                f"{what} claims a live gate road or slice build "
                f"execution ({key!r} is named on it): "
                f"{ROAD_RULE}")
    for key in mapping:
        if key in _DERIVED_KEYS:
            raise ValueError(
                f"{what} carries {key!r}, which is derived from its "
                f"own fields and never stored")
        if key not in allowed:
            raise ValueError(f"{what} carries unknown field {key!r}")


def normalize_stance(value: Any) -> str:
    stance = _clean_text(value, "a stance").lower()
    if stance not in STANCES:
        raise ValueError(
            f"stance {stance!r} is not one of the held "
            f"notes: " + ", ".join(STANCES))
    return stance


def normalize_concordance_state(value: Any) -> str:
    state = _clean_text(value, "an slice state").lower()
    if state not in CONCORDANCE_STATES:
        raise ValueError(
            f"slice state {state!r} is not one of the held "
            f"states: " + ", ".join(CONCORDANCE_STATES))
    return state


def normalize_view_filter(value: Any) -> str:
    view_filter = _clean_text(value, "a view filter").lower()
    if view_filter not in VIEW_FILTERS:
        raise ValueError(
            f"view filter {view_filter!r} is not one of the held "
            f"filters: " + ", ".join(VIEW_FILTERS))
    return view_filter


def normalize_check(value: Any) -> str:
    check = _clean_text(value, "a check").lower()
    if check not in CHECKS:
        raise ValueError(
            f"check {check!r} is not one of the held "
            f"checks: " + ", ".join(CHECKS))
    return check


def normalize_claim_concordance(value: Any) -> str:
    concordance = _clean_text(value, "a claim concordance").lower()
    if concordance not in CLAIM_CONCORDANCES:
        raise ValueError(
            f"claim concordance {concordance!r} is not one of the held "
            f"concordances: " + ", ".join(CLAIM_CONCORDANCES))
    return concordance

# ---------------------------------------------------------------------
# The held road: one slice cut from an active slice.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class RoadRecord:
    """One road slice, held as data.

    The road names the active slice it was
    held from, by slice id, its title, its
    verifiable checks, held as data, and its
    claims, named by road id. The grain is
    derived, never stored: exactly one verifiable
    walk is mapped against the machine. A road whose
    checks are not yet held stands with its
    checks empty: it stands open, named in
    its gaps, and no check is invented for it.
    The road is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    road_id: str
    seq: int
    concordance_id: str
    title: str
    checks: Tuple[str, ...] = ()
    claims: Tuple[str, ...] = ()
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "road_id", _clean_text(self.road_id, "a road id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "concordance_id", _clean_text(self.concordance_id, "an slice id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a road title"))
        object.__setattr__(
            self, "checks", _check_checks(self.checks))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a road detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.road_id

    @property
    def check(self) -> str:
        """The check the road stands at: its last walked check."""
        return self.checks[-1] if self.checks else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "road_id": self.road_id, "seq": self.seq,
            "concordance_id": self.concordance_id, "title": self.title,
            "checks": list(self.checks),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_road_ref(value: Any) -> RoadRecord:
    if not isinstance(value, RoadRecord):
        raise ValueError("a road must be a RoadRecord")
    return value


def validate_road(road: Any) -> RoadRecord:
    return _check_road_ref(road)


def build_road(record: Any = None, **kwargs: Any) -> RoadRecord:
    """Build one held road from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, RoadRecord):
        if kwargs:
            raise ValueError("a road stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a road must be a mapping or a RoadRecord")
    _needed(data, _RUN_KEYS, "a road")
    return RoadRecord(
        road_id=data.get("road_id"), seq=data.get("seq"),
        concordance_id=data.get("concordance_id"), title=data.get("title"),
        checks=data.get("checks"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_provenance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each road to the steps it took outside the machine.

    Derived from the held roads alone: a break is
    one consecutive pair of walked checks the
    explicit gate sequence does not allow, told
    in walk order as before, then after.
    """
    found: Dict[str, Tuple[str, ...]] = {}
    for road in book.roads:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(road.checks, road.checks[1:])
            if not legal_step(before, after))
        if breaks:
            found[road.road_id] = breaks
    return found

def road_gaps(road: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a road from standing complete.

    Mapped from the road's own held fields alone -
    its walked steps against the explicit question
    sequence, and its carried evidence against the
    runnable vocabulary: the road opens at
    named, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a road stands complete only when it has
    reached runnable. The source names nothing
    further: no gap is borrowed from another
    road.
    """
    verified = _check_road_ref(road)
    gaps: List[str] = []
    if not verified.checks:
        gaps.append(
            "has passed through no step: the road has not started")
        return tuple(gaps)
    if verified.checks[0] != "charted":
        gaps.append(
            f"opens at {verified.checks[0]}, not at charted: "
            f"the road opens with the reflection")
    for before, after in zip(verified.checks, verified.checks[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"road sequence does not allow")
    for concordance in verified.claims:
        if concordance in BARE_CLAIMS:
            gaps.append(
                f"carries a {concordance} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if verified.checks[-1] != "runnable":
        gaps.append(
            f"has not reached runnable: the road stands "
            f"at {verified.checks[-1]}")
    return tuple(gaps)

def road_green(road: Any, source: Any = None) -> bool:
    return not road_gaps(road, source)


def plain_lines(road: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the road's own fields."""
    verified = _check_road_ref(road)
    return (
        f"Road: {verified.title}",
        f"Concordance: {verified.concordance_id}",
        f"Check: {verified.check if verified.check else 'none'}",
        f"Claims: "
        f"{', '.join(verified.claims) if verified.claims else 'none'}",
    )


def segment_of(road: Any, source: Any = None) -> str:
    verified = _check_road_ref(road)
    gaps = road_gaps(verified, source)
    return (
        f"{verified.road_id}: {verified.title} - slice: "
        f"'{verified.concordance_id}' - check: "
        f"'{verified.check if verified.check else 'none'}' - "
        f"checks: {len(verified.checks)} - claims: "
        f"'{', '.join(verified.claims) if verified.claims else 'none'}' - "
        f"detail: '{verified.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held slice reference: the active slice a book roads from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ConcordanceRef:
    """One slice a road book roads from, held as a reference.

    The record names the slice, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 slice book's own telling. A road
    stands only from an active reference: the
    book refuses a road naming no held reference,
    and a road from an queued one, BY NAME.
    """

    concordance_id: str
    seq: int
    title: str
    state: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "concordance_id", _clean_text(self.concordance_id, "an slice id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(
            self, "state", normalize_concordance_state(self.state))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an slice detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.concordance_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "concordance_id": self.concordance_id, "seq": self.seq,
            "title": self.title, "state": self.state,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_concordance_ref(value: Any) -> ConcordanceRef:
    if not isinstance(value, ConcordanceRef):
        raise ValueError("a slice reference must be an ConcordanceRef")
    return value


def validate_concordance_ref(ref: Any) -> ConcordanceRef:
    return _check_concordance_ref(ref)


def build_concordance_ref(record: Any = None, **kwargs: Any) -> ConcordanceRef:
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, ConcordanceRef):
        if kwargs:
            raise ValueError(
                "a slice reference stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError(
            "a slice reference must be a mapping or an ConcordanceRef")
    _needed(data, _SLICE_REF_KEYS, "a slice reference")
    return ConcordanceRef(
        concordance_id=data.get("concordance_id"), seq=data.get("seq"),
        title=data.get("title"), state=data.get("state"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held trace trace: the human approves the trace, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TraceRecord:
    """One trace trace, held as data.

    The record names its slice and the trace the
    human active - the slice's road ids in
    derived claim order, held exactly as
    active. The trace is of the set and its
    order, never of a step: when the derived
    trace moves, this record stands stale, named
    in the well, until a new trace is active.
    """

    trace_id: str
    seq: int
    road_id: str
    trace: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "trace_id",
            _clean_text(self.trace_id, "an trace id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "road_id", _clean_text(self.road_id, "an slice id"))
        object.__setattr__(
            self, "trace", _clean_text(self.trace, "an active trace"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an trace detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.trace_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "trace_id": self.trace_id, "seq": self.seq,
            "road_id": self.road_id, "trace": self.trace,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_trace_ref(value: Any) -> TraceRecord:
    if not isinstance(value, TraceRecord):
        raise ValueError("an trace must be an TraceRecord")
    return value


def validate_trace(trace: Any) -> TraceRecord:
    return _check_trace_ref(trace)


def build_trace(record: Any = None, **kwargs: Any) -> TraceRecord:
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, TraceRecord):
        if kwargs:
            raise ValueError(
                "an trace stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError(
            "an trace must be a mapping or an TraceRecord")
    _needed(data, _TRACE_KEYS, "an trace")
    return TraceRecord(
        trace_id=data.get("trace_id"), seq=data.get("seq"),
        road_id=data.get("road_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a road, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One road stance, held as data.

    The record names its road, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per road stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    road_id: str
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
            self, "road_id", _clean_text(self.road_id, "a road id"))
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
            "road_id": self.road_id, "stance": self.stance,
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
        road_id=data.get("road_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which slices a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class RoadView:
    """A view over the book: every road, the green, the rest."""

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

    @property
    def item_id(self) -> str:
        return self.view_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "view_id": self.view_id, "seq": self.seq,
            "view_filter": self.view_filter, "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_view_ref(value: Any) -> RoadView:
    if not isinstance(value, RoadView):
        raise ValueError("a view must be an RoadView")
    return value


def validate_view(view: Any) -> RoadView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> RoadView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, RoadView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an RoadView")
    _needed(data, _VIEW_KEYS, "a view")
    return RoadView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class RoadPanelRow:
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


def _row_for_road(road: RoadRecord,
                     source: Any = None) -> RoadPanelRow:
    return RoadPanelRow(
        item_id=road.road_id,
        standing="complete" if road_green(road, source) else "open",
        label=road.title, segment=segment_of(road, source),
        recorded_on=road.recorded_on)


def _check_row_ref(value: Any) -> RoadPanelRow:
    if not isinstance(value, RoadPanelRow):
        raise ValueError("a panel row must be an RoadPanelRow")
    return value


def validate_row(row: Any, road: Any = None,
                 source: Any = None) -> RoadPanelRow:
    verified = _check_row_ref(row)
    if road is not None:
        derived = _row_for_road(_check_road_ref(road), source)
        if verified != derived:
            raise ValueError(
                f"panel row {verified.item_id!r} does not agree with "
                f"the row derived from its road")
    return verified


def build_row(row: Any = None, road: Any = None,
              source: Any = None,
              **kwargs: Any) -> RoadPanelRow:
    if road is not None:
        derived = _row_for_road(_check_road_ref(road), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            RoadPanelRow(**kwargs))
        return validate_row(built, road, source)
    if isinstance(row, RoadPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return RoadPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return RoadPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an RoadPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[RoadPanelRow, ...]
                 ) -> Tuple[TargetCount, ...]:
    counts: List[TargetCount] = []
    for standing in COMPLETE_WORDS:
        number = sum(1 for row in rows if row.standing == standing)
        if number:
            counts.append(TargetCount(standing=standing, items=number))
    return tuple(counts)


def _panel_account(total_items: int, total_shown: int,
                   green_shown: int,
                   target_counts: Tuple[TargetCount, ...],
                   view_filter: str, as_of: str) -> Tuple[str, ...]:
    standing_words = ", ".join(
        f"{count.standing} {count.items}"
        for count in target_counts) or "none"
    return (
        f"The road book holds {total_items} roads as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown roads "
        f"stand complete.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its road's own fields "
        "- the slice it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any road.",
        "Completeness is mapped from the held records alone: "
        "a road that steps outside the road sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not reached runnable stands open, named in its "
        "gaps, and the road index is derived from the "
        "held roads, never stored where it could drift.",
    )

@dataclass(frozen=True)
class RoadPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[RoadPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> RoadView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, RoadView):
        return view
    return book.view_for(view)


def shown_roads(source: Any, view: Any = None
                   ) -> Tuple[RoadRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.roads
    if resolved.view_filter == "complete":
        return tuple(g for g in book.roads if road_green(g, book))
    return tuple(g for g in book.roads if not road_green(g, book))


def roads_for_concordance(source: Any, concordance_id: Any
                      ) -> Tuple[RoadRecord, ...]:
    wanted = _clean_text(concordance_id, "an slice id")
    return tuple(
        g for g in _source_book(source).roads if g.concordance_id == wanted)


def green_roads(source: Any) -> Tuple[RoadRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.roads if road_green(g, book))


def current_road(source: Any) -> Optional[RoadRecord]:
    """The book's current road, DERIVED at call time.

    The first held road, in held order, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held roads alone, so it can
    never go stale against them. A book whose every
    road stands complete has no current road.
    """
    book = _source_book(source)
    for road in book.roads:
        if not road_green(road, book):
            return road
    return None


def derive_panel(source: Any, view: Any = None) -> RoadPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_roads(book, resolved)
    rows = tuple(_row_for_road(road, book) for road in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.roads), default="")
    green = sum(1 for g in shown if road_green(g, book))
    return RoadPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.roads), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.roads), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> RoadPanel:
    if not isinstance(value, RoadPanel):
        raise ValueError("a panel must be an RoadPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> RoadPanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 road).
    """
    verified = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(verified.view_id)
                if verified.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(verified, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {verified.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return verified


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> RoadPanel:
    if isinstance(panel, RoadPanel):
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
        built = RoadPanel(
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
    raise ValueError("a panel must be a mapping, an RoadPanel, or derived")


def _check_lines(value: Any, what: str) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError(f"{what} must be a list of lines")
    lines = []
    for line in value:
        lines.append(_clean_text(line, f"a line of {what}"))
    return tuple(lines)


def _verdict_word(total_shown: int, green_shown: int) -> str:
    if total_shown > 0 and green_shown == total_shown:
        return "runnable"
    if green_shown == 0:
        return "blocked"
    return "held"


@dataclass(frozen=True)
class RoadVerdict:
    verdict: str
    view_id: Optional[str]
    total_shown: int
    green_shown: int
    latest_on: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict, "view_id": self.view_id,
            "total_shown": self.total_shown,
            "green_shown": self.green_shown,
            "latest_on": self.latest_on,
        }


def derive_verdict(source: Any, view: Any = None) -> RoadVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_roads(book, resolved)
    green = sum(1 for g in shown if road_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return RoadVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> RoadVerdict:
    if not isinstance(value, RoadVerdict):
        raise ValueError("a verdict must be an RoadVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> RoadVerdict:
    verified = _check_verdict_ref(verdict)
    if verified.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {verified.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(verified.view_id)
                if verified.view_id is not None else None)
        derived = derive_verdict(book, view)
        if verified != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return verified


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> RoadVerdict:
    if isinstance(verdict, RoadVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = RoadVerdict(
            verdict=_clean_text(data.get("verdict"), "a verdict"),
            view_id=data.get("view_id"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            green_shown=_check_count(
                data.get("green_shown"), "a green_shown count"),
            latest_on=_clean_text(data.get("latest_on"), "a latest day"))
        return validate_verdict(built, source)
    if verdict is None and source is not None:
        return derive_verdict(source, kwargs.get("view"))
    raise ValueError(
        "a verdict must be a mapping, an RoadVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held slices' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    check: str
    road_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "check": self.check, "road_id": self.road_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class RoadIndex:
    """The road index, derived from the held roads.

    The index names one entry per green road, in
    held order - the road's own one verifiable
    check, its road id and its title - and the
    roads that do not stand complete, named in its
    gaps. Nothing here is stored on any road: the
    index is derived at call time from the held
    records alone, so it can never drift from them.
    """

    entries: Tuple[IndexEntry, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "entries": [e.to_record() for e in self.entries],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> RoadIndex:
    """Derive the road index from the book's held roads."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(check=g.check, road_id=g.road_id,
                   title=g.title)
        for g in book.roads if road_green(g, book))
    gaps = tuple(
        g.road_id for g in book.roads if not road_green(g, book))
    return RoadIndex(entries=entries, gaps=gaps)


def road_for_check(source: Any, check: Any) -> Optional[RoadRecord]:
    """The first held road one check reaches, or none - honestly."""
    if check is None:
        return None
    if not isinstance(check, str):
        raise ValueError("an check must be a string naming the check")
    wanted = check.strip()
    if not wanted:
        return None
    for road in _source_book(source).roads:
        if road.check == wanted:
            return road
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held order: the road
    that took it and the step it took, before,
    then after. A book whose roads all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{road_id}: {step}"
        for road_id, steps in _breaks_map(book).items()
        for step in steps)

def road_order(source: Any,
              concordance_id: Any = None) -> Tuple[RoadRecord, ...]:
    """The held roads in their held order, DERIVED at call time.

    Roads stand in the order the book holds them -
    the order their slices were taken - optionally
    for one slice alone. Nothing here is stored:
    the order is the book's own held order, told.
    """
    book = _source_book(source)
    roads = list(book.roads)
    if concordance_id is not None:
        wanted = _clean_text(concordance_id, "a slice id")
        roads = [r for r in roads if r.concordance_id == wanted]
    return tuple(roads)

def trace_of(source: Any, road_id: Any) -> str:
    """One road's trace, DERIVED at call time.

    The road's walked checks joined as one trace
    line, in walk order. A road that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is named
    elsewhere.
    """
    road = _source_book(source).road_for(road_id)
    return " > ".join(road.checks)

def trace_for_road(source: Any,
                  road_id: Any) -> Optional[TraceRecord]:
    """The held trace for one road, or none - honestly."""
    wanted = _clean_text(road_id, "a road id")
    for record in _source_book(source).traces:
        if record.road_id == wanted:
            return record
    return None

def trace_current(source: Any, road_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_road(source, road_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, road_id)

def note_for_road(source: Any, road_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one road (and stance, when named)."""
    wanted = _clean_text(road_id, "a road id")
    for record in _source_book(source).notes:
        if record.road_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the slice targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def well_record(source: Any = None) -> Dict[str, Any]:
    """The road well, DERIVED here from the held roads alone.

    The well counts the held roads by their
    derived completeness - green and red - names
    the current road, the first that does not yet
    stand complete, tells each held road's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held roads took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.roads
            if ("complete" if road_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "road_records": number})
    current = current_road(book)
    traces = []
    for road in book.roads:
        trace = trace_for_road(book, road.road_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, road.road_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"road_id": road.road_id, "trace": standing})
    return {
        "type": "road_well",
        "slice": ROAD_SLICE,
        "standings": standings,
        "total": len(book.roads),
        "current_road": current.road_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This slice's own roadmap standing, proved from the roadmap itself.

    The record loads this concordance's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 slices in 11 parts,
    the charted prefix, the next slice where the
    road resumes, and M-218's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(ROAD_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "road_roadmap",
        "slice": ROAD_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m218_title": own.title,
        "m218_part": own.part,
        "m218_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: slices, roads, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or order ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class RoadBook:
    title: str
    slices: Tuple[ConcordanceRef, ...] = ()
    roads: Tuple[RoadRecord, ...] = ()
    views: Tuple[RoadView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[RoadPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        slices = tuple(_check_concordance_ref(g) for g in self.slices)
        roads = tuple(_check_road_ref(g) for g in self.roads)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        traces = tuple(_check_trace_ref(a) for a in self.traces)
        panels = tuple(_check_panel_ref(pn) for pn in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for ref in slices:
            if ref.concordance_id in seen_ids:
                raise ValueError(
                    f"two slice references stand under id {ref.concordance_id!r}")
            if ref.seq in seen_seqs:
                raise ValueError(
                    f"two slice references stand at sequence {ref.seq}")
            seen_ids.add(ref.concordance_id)
            seen_seqs.add(ref.seq)
        road_ids = set()
        road_seqs = set()
        for road in roads:
            if road.road_id in road_ids:
                raise ValueError(
                    f"two roads stand under id {road.road_id!r}")
            if road.seq in road_seqs:
                raise ValueError(
                    f"two roads stand at sequence {road.seq}")
            road_ids.add(road.road_id)
            road_seqs.add(road.seq)
        by_slice = {ref.concordance_id: ref for ref in slices}
        for road in (roads if slices else ()):

            ref = by_slice.get(road.concordance_id)
            if ref is None:
                raise ValueError(
                    f"road {road.road_id!r} is held from slice "
                    f"{road.concordance_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "live":
                raise ValueError(
                    f"road {road.road_id!r} is held from slice "
                    f"{road.concordance_id!r}, which is not active: "
                    f"no slice is held from an queued slice")
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
            target = (record.road_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for road "
                    f"{record.road_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per road target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_roads = set()
        road_ids = {road.road_id for road in roads}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.road_id in trace_roads:
                raise ValueError(
                    f"two traces stand for road "
                    f"{record.road_id!r}: one trace stands "
                    f"per road walk")
            if roads and record.road_id not in road_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces road "
                    f"{record.road_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_roads.add(record.road_id)
        object.__setattr__(
            self, "concordances", tuple(sorted(slices, key=lambda g: g.seq)))
        object.__setattr__(
            self, "road_records", tuple(sorted(roads, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.roads + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.road_id for g in self.roads) + tuple(
            v.view_id for v in self.views)

    def road_ids(self) -> Tuple[str, ...]:
        return tuple(g.road_id for g in self.roads)

    def concordance_ids(self) -> Tuple[str, ...]:
        return tuple(g.concordance_id for g in self.slices)

    def road_for(self, road_id: Any) -> RoadRecord:
        wanted = _clean_text(road_id, "a road id")
        for road in self.roads:
            if road.road_id == wanted:
                return road
        raise KeyError(f"no road named {wanted!r} stands in this book")

    def slice_for(self, concordance_id: Any) -> ConcordanceRef:
        wanted = _clean_text(concordance_id, "an slice id")
        for ref in self.slices:
            if ref.concordance_id == wanted:
                return ref
        raise KeyError(f"no slice named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> RoadView:
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

    def trace_for(self, trace_id: Any) -> TraceRecord:
        wanted = _clean_text(trace_id, "an trace id")
        for record in self.traces:
            if record.trace_id == wanted:
                return record
        raise KeyError(f"no trace named {wanted!r} stands in this book")

    def item_for(self, item_id: Any) -> Any:
        wanted = _clean_text(item_id, "an item id")
        for road in self.roads:
            if road.road_id == wanted:
                return road
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "concordances": [g.to_record() for g in self.slices],
            "road_records": [g.to_record() for g in self.roads],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: RoadBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: RoadBook) -> None:
    if book.title != "The 500-slice road as a campaign at the M-218 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.slices) != 3 or len(book.roads) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three slice references, five roads and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m217-boundary":
        raise ValueError("the pinned panel is panel-m217-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.check for e in index.entries] != ["runnable", "runnable", "runnable"]:
        raise ValueError("the shipped example book index must derive the three held complete roads in held order")
    if index.gaps != ("road-bare-road", "road-leaping-road"):
        raise ValueError("the shipped example book must leave the bare and leaping roads honestly open, named in its gaps")
    found = road_for_check(book, EXAMPLE_CHECK)
    if found is None or found.road_id != "road-held-road":
        raise ValueError("the shipped example book must reach its opening road under the example check")
    if trace_of(book, "road-held-road") != "charted > loaded > mapped > verified > runnable":
        raise ValueError("the shipped example book must derive the opening road's trace from its walked steps")
    if not trace_current(book, "road-held-road"):
        raise ValueError("the shipped example book must hold the opening road's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note road")

def validate_book(data: Any, *, require_example: bool = False) -> RoadBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, RoadBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a road book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live slice build or execution "
                f"({key!r} is named on it): {ROAD_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its roads under a view")
    if "road_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held roads at call time")
    if "well" in data or "current_road" in data:
        raise ValueError(
            "a book stores no well and no current road: both are "
            "derived from its held roads at call time")
    if "trace" in data or "order" in data:
        raise ValueError(
            "a book stores no trace and no order: both are derived "
            "from its held roads at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != ROAD_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{ROAD_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != ROAD_SLICE):
        raise ValueError(
            f"a book's slice must be {ROAD_SLICE!r}")
    head = data.get("road_head") or data.get("mimisbrunnr_road") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's road head must be a mapping")
    title = head.get("title") or data.get("title")
    slices = tuple(build_concordance_ref(g) for g in data.get("concordances") or ())
    roads = tuple(build_road(g) for g in data.get("road_records") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = RoadBook(
        title=title, slices=slices, roads=roads, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = RoadBook(
        title=book.title, slices=book.slices, roads=book.roads,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> RoadBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (RoadBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an RoadBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> RoadBook:
    return validate_book(data, require_example=require_example)


def load_road(
        data: Optional[Dict[str, Any]] = None) -> RoadBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(ROAD_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_road_file(path: Any) -> RoadBook:
    """Load one road file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: slice references, roads and views held one by one.
# ---------------------------------------------------------------------

class RoadRegistry:
    """An in-memory holding of slice references, roads and views.

    The registry is the pure layer's model of a
    session's road book: slice references are
    held under their ids, roads are held under
    their ids, one road per id and per sequence,
    and views are held in loaded order, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[ConcordanceRef] = []
        self._roads: List[RoadRecord] = []
        self._views: List[RoadView] = []
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

    def register_concordance_ref(self, item: Any) -> ConcordanceRef:
        """Hold one slice reference, mapped whole before held."""
        verified = _check_concordance_ref(item)
        return self._register(
            self._slices, verified, "concordance_id", "slice reference")

    def register_road(self, item: Any) -> RoadRecord:
        """Hold one road, mapped whole before held."""
        verified = _check_road_ref(item)
        return self._register(
            self._roads, verified, "road_id", "road")

    def register_view(self, view: Any) -> RoadView:
        """Hold one view; a view naming no id takes a fresh one."""
        verified = _check_view_ref(view)
        if not verified.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            verified = build_view({**verified.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, verified, "view_id", "view")

    def register_book(self, book: Any) -> RoadBook:
        """Hold a whole book's records, under its title."""
        verified = build_book(book)
        if self._title is not None and verified.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {verified.title!r}")
        for ref in verified.slices:
            self.register_concordance_ref(ref)
        for road in verified.roads:
            self.register_road(road)
        for view in verified.views:
            self.register_view(view)
        self._title = verified.title
        return self.book()

    def book(self) -> RoadBook:
        return RoadBook(
            title=self._title or "An unheld road book",
            slices=tuple(self._slices), roads=tuple(self._roads),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[ConcordanceRef, ...]:
        return tuple(self._slices)

    def list_roads(self) -> Tuple[RoadRecord, ...]:
        return tuple(self._roads)

    def list_views(self) -> Tuple[RoadView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._roads) + tuple(self._views)

    def get_slice(self, concordance_id: Any) -> ConcordanceRef:
        return self.book().slice_for(concordance_id)

    def get_road(self, road_id: Any) -> RoadRecord:
        return self.book().road_for(road_id)

    def get_view(self, view_id: Any) -> RoadView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the journal target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> RoadBook:
    if source is None:
        return load_road()
    if isinstance(source, RoadBook):
        return source
    if isinstance(source, RoadRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def road_record(road: Any, source: Any = None) -> Dict[str, Any]:
    verified = _check_road_ref(road)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "road_road",
        "slice": ROAD_SLICE,
        "road_id": verified.road_id,
        "concordance_id": verified.concordance_id,
        "title": verified.title,
        "segment": segment_of(verified, book),
        "complete": road_green(verified, book),
        "gaps": list(road_gaps(verified, book)),
    }
    record.update(_provenance_record(verified))
    return record


def concordance_record(ref: Any) -> Dict[str, Any]:
    verified = _check_concordance_ref(ref)
    record = {
        "type": "road_slice",
        "slice": ROAD_SLICE,
        "concordance_id": verified.concordance_id,
        "title": verified.title,
        "state": verified.state,
    }
    record.update(_provenance_record(verified))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    verified = _check_trace_ref(record_in)
    record = {
        "type": "road_trace",
        "slice": ROAD_SLICE,
        "trace_id": verified.trace_id,
        "road_id": verified.road_id,
        "trace": verified.trace,
    }
    record.update(_provenance_record(verified))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    verified = _check_view_ref(view)
    record = {
        "type": "road_view",
        "slice": ROAD_SLICE,
        "view_id": verified.view_id, "seq": verified.seq,
        "view_filter": verified.view_filter,
    }
    record.update(_provenance_record(verified))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    verified = _check_note_ref(record_in)
    record = {
        "type": "road_note",
        "slice": ROAD_SLICE,
        "note_id": verified.note_id,
        "road_id": verified.road_id,
        "stance": verified.stance,
    }
    record.update(_provenance_record(verified))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    verified = validate_panel(panel, source)
    record = {"type": "road_panel",
              "slice": ROAD_SLICE}
    record.update(verified.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, RoadVerdict):
        verified = validate_verdict(verdict, source)
    else:
        verified = derive_verdict(_source_book(verdict), view)
    record = {"type": "road_verdict",
              "slice": ROAD_SLICE}
    record.update(verified.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, RoadIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "road_index",
              "slice": ROAD_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    verified = _source_book(book)
    record = {"type": "road_book",
              "slice": ROAD_SLICE,
              "title": verified.title}
    record.update(verified.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(road: Any, source: Any = None) -> str:
    verified = _check_road_ref(road)
    return (
        f"{verified.title} - from {verified.concordance_id}: "
        f"check {verified.check if verified.check else 'none'}, "
        f"claims "
        f"{', '.join(verified.claims) if verified.claims else 'none'}. "
        f"{verified.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The roads stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"roads stand complete.")


def view_plain_words(view: Any) -> str:
    verified = _check_view_ref(view)
    return f"View {verified.view_id}: shows {verified.view_filter} roads."


def note_plain_words(record_in: Any) -> str:
    verified = _check_note_ref(record_in)
    return (
        f"Note {verified.note_id}: {verified.stance} "
        f"{verified.road_id}, toward {verified.target}. "
        f"{verified.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, RoadIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} green roads; "
        f"red, named in its gaps: {gaps}.")

def format_road(road: Any, source: Any = None) -> str:
    verified = _check_road_ref(road)
    book = _source_book(source) if source is not None else None
    lines = [f"{verified.title} ({verified.road_id})"]
    lines.extend(plain_lines(verified))
    lines.append(verified.detail)
    if road_green(verified, book):
        lines.append(
            "This road stands complete - it walked the question "
            "sequence in the open from charted to runnable, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This road stands open - it stands named in "
            f"its gaps: {', '.join(road_gaps(verified, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    verified = _check_view_ref(view)
    return (
        f"View {verified.view_id}: filter {verified.view_filter} - "
        f"{verified.detail}")


def format_note(record_in: Any) -> str:
    verified = _check_note_ref(record_in)
    lines = [
        f"Road note {verified.stance} {verified.road_id} "
        f"({verified.note_id}): {verified.title}. {verified.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_check(source: Any, check: Any) -> str:
    road = road_for_check(source, check)
    if road is not None:
        return format_road(road, source)
    wanted = check.strip() if isinstance(check, str) else check
    return (
        f"No held road stands under check {wanted!r} yet - the "
        f"check reaches nothing in this book, and no road is "
        f"invented for it.")


def format_book(source: Any = None, concordance_id: Any = None) -> str:
    book = _source_book(source)
    roads = (roads_for_concordance(book, concordance_id)
              if concordance_id is not None else book.roads)
    lines = [f"The Road Gate (M-218) - {book.title}"]
    lines.extend(segment_of(road, book) for road in roads)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Road panel under view {panel.view_id}:"]
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
    lines = ["Road index, derived from the held roads:"]
    for entry in index.entries:
        lines.append(f"{entry.check} - {entry.title} ({entry.road_id})")
    if index.gaps:
        lines.append(
            "Red, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_road_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Road Gate (M-218)",
        f"{book.title}: {len(book.roads)} roads held, "
        f"{len(green_roads(book))} roads standing green, "
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


def parse_road_args(args: Any) -> Tuple[str, Any]:
    """Parse the /road grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("road", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("check", "concordance"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
