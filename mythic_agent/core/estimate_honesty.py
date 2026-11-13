"""Estimates (roadmap slice M-215).

Part IX - The Mythic Method Engine. The roadmap
words: *slice forecasts (time/tokens) recorded
against outcomes; the app shows its own
calibration, improving visibly or not at all.*

What already ships, and what this slice adds:

* The Self-Improving ledger already ships as
  data (M-155, ``core/self_improving_ledger.py``):
  candidate memories captured after significant
  work, promoted only by an explicit decision.
  This slice WIRES the inflow the ledger's own
  docstring names - M-215 estimates flowing
  here - as data, in its own module, standing in
  the M-195 copy-and-share book shape the M-214
  book stands in: one estimator per campaign, and the
  estimator's charge over one closed slice's forecast
  held as a book - a estimate. The shipped
  roads stand untouched behind their seams: this
  layer holds estimates as data over the
  campaign's slices and rewrites none of them,
  and the ledger keeps its own standing. Forecasts
  flow to the ledger AS DATA alone: a forecast
  carries a ledger ref, a reference held in this
  book; holding, viewing or telling a
  estimate writes no ledger file live,
  captures no candidate and promotes nothing.

* No charter row names this slice: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-215 on no row, and the
  slice tests pin that absence live. The M-005
  method charter names no slice row either: its
  own words name the whole of Part IX as the
  part that executes the charter, and this slice
  is built to the roadmap words and that
  execution note together.

* A estimate is held whole: the slice it
  answers for, named by its slice id; its title;
  the forecast steps it walked, held as data in
  walk order; and the evidence it carries, held
  as data by kind. The forecast walk is EXPLICIT:
  its sequence stands as data
  (:data:`CHECKS`, :data:`TRANSITIONS`) -
  predicted, recorded, measured, compared, calibrated -
  and a estimate's standing is DERIVED at
  call time from its held steps and evidence
  alone: a estimate that opens anywhere but
  predicted, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet reached calibrated stands
  open, named in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - slice_ref,
  outcome_ref, test_record, calibration_ref, evidence
  a estimator can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A forecast is
  compared from held evidence alone, never
  from a feeling: a estimate holding a
  bare claim stands open, named in its gaps.
* A estimate stands only for an ACTIVE
  slice. The book holds each slice it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  estimate naming a slice that stands
  nowhere in the book refuses BY NAME, and a
  estimate for a slice that is not active
  refuses BY NAME beside it: the estimator deals with
  the slice in hand, in roadmap order, never a
  queued one, and a slice whose forecast already
  stands complete is never measured twice - the
  current estimate is derived, so a
  completed slice is never the current forecast
  twice.
* The estimate's trace is visible. A trace
  record holds one estimate's walked steps
  as one trace line, exactly as walked, beside
  the estimate. The derived trace is
  computed at call time from the estimate's
  held steps; a held trace that no longer agrees
  with it stands stale, named in the board - the
  trace is the walk itself, never a retelling
  of it.
* The estimate index is DERIVED at call
  time from the held estimates - one entry
  per complete estimate, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, order or current-estimate
  claim on any record refuses by name.
* The current estimate is DERIVED at call
  time - the first held estimate, in held
  order, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its estimate, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per estimate stance; holding
  a note posts none of it, the rule stands as
  data (:data:`ESTIMATE_RULE`), and a record
  claiming a forecast was actually calibrated,
  captured or promoted live refuses BY NAME.
  The estimator reports - and those reports, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the shape a real estimate
  file takes, a loader reads a file anywhere on
  disk, estimates and views are shaped as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a estimate book for a session and
  telling from it. This layer reaches no live
  road: it writes no forecast live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no estimator, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds estimates
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The forecast walk is explicit.** A
  estimate is compared against the held
  steps and legal steps alone; an illegal step
  stands named in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  estimate that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, named in its gaps:
  a forecast is compared from evidence, not
  vibes.
* **Active slices only, in roadmap order.** A
  estimate for a missing or queued slice
  refuses by name; no estimate is invented
  for a slice the estimator has not dealt with.
* **Unknown stays unknown.** A estimate
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, order
  and current estimate are derived, never
  stored.** Each is derived from the held
  estimates at call time; a stored one
  refuses by name, so it can never drift.
* **One estimate per estimate.** Two
  estimates standing for one estimate id
  refuse by name, and one note record stands per
  estimate stance.
* **The notes are data alone.** The records
  hold the feedback; holding, viewing or telling
  them writes nothing, files nothing and posts
  nothing.
"""


from __future__ import annotations

__all__ = [
    "CHECK_FIELDS",
    "CHECKS",
    "CLAIM_KINDS",
    "HELD_EVIDENCE",
    "BARE_CLAIMS",
    "TRANSITIONS",
    "EXAMPLE_CHECK",
    "STANCES",
    "INDEX_ACTION",
    "ESTIMATE_RESOURCE",
    "ESTIMATE_SCHEMA",
    "ESTIMATE_SLICE",
    "ESTIMATE_RULE",
    "PLAIN_EXPLANATION",
    "THE_ESTIMATE_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "COMPLETE_WORDS",
    "SLICE_STATES",
    "Any",
    "Dict",
    "List",
    "Optional",
    "TraceRecord",
    "EstimateRecord",
    "IndexEntry",
    "SliceRef",
    "NoteRecord",
    "EstimateBook",
    "EstimateIndex",
    "EstimatePanel",
    "EstimatePanelRow",
    "EstimateRegistry",
    "EstimateVerdict",
    "EstimateView",
    "TargetCount",
    "trace_for_estimate",
    "trace_record",
    "board_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_estimate",
    "build_slice_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_estimate",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "estimate_for_check",
    "estimate_order",
    "estimate_record",
    "first_note",
    "format_book",
    "format_estimate",
    "format_index",
    "format_note",
    "format_check",
    "format_panel",
    "format_estimate_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "slice_record",
    "load_estimate",
    "load_estimate_file",
    "normalize_slice_state",
    "normalize_check",
    "normalize_claim_kind",
    "legal_step",
    "next_check",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_estimate",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_estimate_args",
    "green_estimates",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_estimates",
    "validate_trace",
    "validate_book",
    "validate_estimate",
    "validate_slice_ref",
    "validate_note",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
    "estimate_gaps",
    "estimate_green",
    "estimates_for_slice",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

ESTIMATE_SCHEMA = "mythic.estimate_honesty/1"
ESTIMATE_SLICE = "M-215"
THE_ESTIMATE_SLICE = ESTIMATE_SLICE
ESTIMATE_RESOURCE = "estimate_honesty.yaml"
INDEX_ACTION = "index"
EXAMPLE_CHECK = "calibrated"
CHECK_FIELDS = ("checks", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("calibrated", "held", "blocked")
SLICE_STATES = ("active", "queued")
ESTIMATE_RULE = (
    "estimates are held as data alone: slice "
    "forecasts (time/tokens) are recorded "
    "against outcomes and the app shows its "
    "own calibration - a calibration stands "
    "as data, held by reference (a calibration "
    "ref), never applied live - the estimate "
    "walk stands as an explicit estimate "
    "sequence - predicted, recorded, measured, "
    "compared, calibrated - and an estimate "
    "completes only complete, complete being a "
    "state with evidence held - slice ref, "
    "outcome ref, test record, calibration "
    "ref - never a feeling, a memory, an "
    "assertion or a summary; holding, viewing "
    "and reading an estimate writes no "
    "calibration live, approves nothing, "
    "spawns no process and opens no network")
PLAIN_EXPLANATION = (
    "Estimate honesty (M-215): slice forecasts "
    "(time/tokens) recorded against outcomes; "
    "the app shows its own calibration, "
    "improving visibly or not at all.")
USAGE = (
    "Usage: /estimates | /estimates estimate <estimate-id> | "
    "/estimates check <check> | /estimates slice <slice-id> | "
    "/estimates view <view-id> | /estimates note <note-id> | "
    "/estimates index | /estimates panel | /estimates verdict")

CHECKS = ("predicted", "recorded", "measured", "compared", "calibrated")
HELD_EVIDENCE = ("slice_ref", "outcome_ref", "test_record", "calibration_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "predicted": ("recorded",),
    "recorded": ("measured",),
    "measured": ("compared",),
    "compared": ("predicted", "calibrated"),
    "calibrated": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a failure or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a estimate stands complete.
    A check outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_check(check: Any, failed: Any = False) -> Optional[str]:
    """The step the estimator takes next, DERIVED from the sequence.

    Banked leads to recorded and recorded to
    measured; measured leads to compared; at
    compared a follow-up banking steps back to predicted and a finished forecast steps to calibrated;
    calibrated is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    compared = normalize_check(check)
    if compared == "predicted":
        return "recorded"
    if compared == "recorded":
        return "measured"
    if compared == "measured":
        return "compared"
    if compared == "compared":
        return "predicted" if failed else "calibrated"
    return None


_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "estimate_id", "seq", "slice_id", "title", "checks",
    "claims", "detail",
} | set(_PROVENANCE))
_SLICE_REF_KEYS = frozenset({
    "slice_id", "seq", "title", "state", "detail",
} | set(_PROVENANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "estimate_id", "trace", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "estimate_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered",
    "current_estimate", "next_estimate", "progress", "board",
    "current", "order", "breaks", "active"})
_LIVE_KEYS = (
    "live_estimate", "estimates_live", "live_question",
    "estimates_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "resumes_live",
    "resumed_live", "pauses_campaign", "paused_live",
    "runs_campaign", "ran_campaign", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "estimate_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_estimate", "sent_estimate",
    "posts_note", "posted_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_forecast", "filed_live", "spawns_estimator", "spawned_estimator", "sends_forecast", "sent_forecast", "writes_forecast", "wrote_forecast")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_checks(value: Any) -> Tuple[str, ...]:
    """A estimate's walked checks, held as data.

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
    """A estimate's asked claims: claim kinds named as data.

    Each claim names one kind from the calibrated
    vocabulary - the human kinds the gate may ask
    and the code kinds it must never ask, both
    held honestly as data - and a kind outside
    the vocabulary refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("claims must be a list of claim kinds")
    return tuple(normalize_claim_kind(v) for v in value)

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
                f"{what} claims a live gate estimate or slice build "
                f"execution ({key!r} is named on it): "
                f"{ESTIMATE_RULE}")
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


def normalize_slice_state(value: Any) -> str:
    state = _clean_text(value, "an slice state").lower()
    if state not in SLICE_STATES:
        raise ValueError(
            f"slice state {state!r} is not one of the held "
            f"states: " + ", ".join(SLICE_STATES))
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


def normalize_claim_kind(value: Any) -> str:
    kind = _clean_text(value, "a claim kind").lower()
    if kind not in CLAIM_KINDS:
        raise ValueError(
            f"claim kind {kind!r} is not one of the held "
            f"kinds: " + ", ".join(CLAIM_KINDS))
    return kind

# ---------------------------------------------------------------------
# The held estimate: one slice cut from an active slice.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class EstimateRecord:
    """One estimate slice, held as data.

    The estimate names the active slice it was
    held from, by slice id, its title, its
    verifiable checks, held as data, and its
    claims, named by estimate id. The grain is
    derived, never stored: exactly one verifiable
    walk is measured against the machine. A estimate whose
    checks are not yet held stands with its
    checks empty: it stands open, named in
    its gaps, and no check is invented for it.
    The estimate is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    estimate_id: str
    seq: int
    slice_id: str
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
            self, "estimate_id", _clean_text(self.estimate_id, "a estimate id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "slice_id", _clean_text(self.slice_id, "an slice id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a estimate title"))
        object.__setattr__(
            self, "checks", _check_checks(self.checks))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a estimate detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.estimate_id

    @property
    def check(self) -> str:
        """The check the estimate stands at: its last walked check."""
        return self.checks[-1] if self.checks else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "estimate_id": self.estimate_id, "seq": self.seq,
            "slice_id": self.slice_id, "title": self.title,
            "checks": list(self.checks),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_estimate_ref(value: Any) -> EstimateRecord:
    if not isinstance(value, EstimateRecord):
        raise ValueError("a estimate must be a EstimateRecord")
    return value


def validate_estimate(estimate: Any) -> EstimateRecord:
    return _check_estimate_ref(estimate)


def build_estimate(record: Any = None, **kwargs: Any) -> EstimateRecord:
    """Build one held estimate from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, EstimateRecord):
        if kwargs:
            raise ValueError("a estimate stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a estimate must be a mapping or a EstimateRecord")
    _needed(data, _RUN_KEYS, "a estimate")
    return EstimateRecord(
        estimate_id=data.get("estimate_id"), seq=data.get("seq"),
        slice_id=data.get("slice_id"), title=data.get("title"),
        checks=data.get("checks"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_provenance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each estimate to the steps it took outside the machine.

    Derived from the held estimates alone: a break is
    one consecutive pair of walked checks the
    explicit gate sequence does not allow, told
    in walk order as before, then after.
    """
    found: Dict[str, Tuple[str, ...]] = {}
    for estimate in book.estimates:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(estimate.checks, estimate.checks[1:])
            if not legal_step(before, after))
        if breaks:
            found[estimate.estimate_id] = breaks
    return found

def estimate_gaps(estimate: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a estimate from standing complete.

    Mapped from the estimate's own held fields alone -
    its walked steps against the explicit question
    sequence, and its carried evidence against the
    calibrated vocabulary: the estimate opens at
    named, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a estimate stands complete only when it has
    reached calibrated. The source names nothing
    further: no gap is borrowed from another
    estimate.
    """
    compared = _check_estimate_ref(estimate)
    gaps: List[str] = []
    if not compared.checks:
        gaps.append(
            "has passed through no step: the estimate has not started")
        return tuple(gaps)
    if compared.checks[0] != "predicted":
        gaps.append(
            f"opens at {compared.checks[0]}, not at predicted: "
            f"the estimate opens with the reflection")
    for before, after in zip(compared.checks, compared.checks[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"estimate sequence does not allow")
    for kind in compared.claims:
        if kind in BARE_CLAIMS:
            gaps.append(
                f"carries a {kind} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if compared.checks[-1] != "calibrated":
        gaps.append(
            f"has not reached calibrated: the estimate stands "
            f"at {compared.checks[-1]}")
    return tuple(gaps)

def estimate_green(estimate: Any, source: Any = None) -> bool:
    return not estimate_gaps(estimate, source)


def plain_lines(estimate: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the estimate's own fields."""
    compared = _check_estimate_ref(estimate)
    return (
        f"Estimate: {compared.title}",
        f"Slice: {compared.slice_id}",
        f"Check: {compared.check if compared.check else 'none'}",
        f"Claims: "
        f"{', '.join(compared.claims) if compared.claims else 'none'}",
    )


def segment_of(estimate: Any, source: Any = None) -> str:
    compared = _check_estimate_ref(estimate)
    gaps = estimate_gaps(compared, source)
    return (
        f"{compared.estimate_id}: {compared.title} - slice: "
        f"'{compared.slice_id}' - check: "
        f"'{compared.check if compared.check else 'none'}' - "
        f"checks: {len(compared.checks)} - claims: "
        f"'{', '.join(compared.claims) if compared.claims else 'none'}' - "
        f"detail: '{compared.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held slice reference: the active slice a book estimates from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class SliceRef:
    """One slice a estimate book estimates from, held as a reference.

    The record names the slice, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 slice book's own telling. A estimate
    stands only from an active reference: the
    book refuses a estimate naming no held reference,
    and a estimate from an queued one, BY NAME.
    """

    slice_id: str
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
            self, "slice_id", _clean_text(self.slice_id, "an slice id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(
            self, "state", normalize_slice_state(self.state))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an slice detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.slice_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "slice_id": self.slice_id, "seq": self.seq,
            "title": self.title, "state": self.state,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_slice_ref(value: Any) -> SliceRef:
    if not isinstance(value, SliceRef):
        raise ValueError("a slice reference must be an SliceRef")
    return value


def validate_slice_ref(ref: Any) -> SliceRef:
    return _check_slice_ref(ref)


def build_slice_ref(record: Any = None, **kwargs: Any) -> SliceRef:
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, SliceRef):
        if kwargs:
            raise ValueError(
                "a slice reference stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError(
            "a slice reference must be a mapping or an SliceRef")
    _needed(data, _SLICE_REF_KEYS, "a slice reference")
    return SliceRef(
        slice_id=data.get("slice_id"), seq=data.get("seq"),
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
    human active - the slice's estimate ids in
    derived claim order, held exactly as
    active. The trace is of the set and its
    order, never of a step: when the derived
    trace moves, this record stands stale, named
    in the board, until a new trace is active.
    """

    trace_id: str
    seq: int
    estimate_id: str
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
            self, "estimate_id", _clean_text(self.estimate_id, "an slice id"))
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
            "estimate_id": self.estimate_id, "trace": self.trace,
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
        estimate_id=data.get("estimate_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a estimate, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One estimate stance, held as data.

    The record names its estimate, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per estimate stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    estimate_id: str
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
            self, "estimate_id", _clean_text(self.estimate_id, "a estimate id"))
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
            "estimate_id": self.estimate_id, "stance": self.stance,
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
        estimate_id=data.get("estimate_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which slices a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class EstimateView:
    """A view over the book: every estimate, the green, the rest."""

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


def _check_view_ref(value: Any) -> EstimateView:
    if not isinstance(value, EstimateView):
        raise ValueError("a view must be an EstimateView")
    return value


def validate_view(view: Any) -> EstimateView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> EstimateView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, EstimateView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an EstimateView")
    _needed(data, _VIEW_KEYS, "a view")
    return EstimateView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class EstimatePanelRow:
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


def _row_for_estimate(estimate: EstimateRecord,
                     source: Any = None) -> EstimatePanelRow:
    return EstimatePanelRow(
        item_id=estimate.estimate_id,
        standing="complete" if estimate_green(estimate, source) else "open",
        label=estimate.title, segment=segment_of(estimate, source),
        recorded_on=estimate.recorded_on)


def _check_row_ref(value: Any) -> EstimatePanelRow:
    if not isinstance(value, EstimatePanelRow):
        raise ValueError("a panel row must be an EstimatePanelRow")
    return value


def validate_row(row: Any, estimate: Any = None,
                 source: Any = None) -> EstimatePanelRow:
    compared = _check_row_ref(row)
    if estimate is not None:
        derived = _row_for_estimate(_check_estimate_ref(estimate), source)
        if compared != derived:
            raise ValueError(
                f"panel row {compared.item_id!r} does not agree with "
                f"the row derived from its estimate")
    return compared


def build_row(row: Any = None, estimate: Any = None,
              source: Any = None,
              **kwargs: Any) -> EstimatePanelRow:
    if estimate is not None:
        derived = _row_for_estimate(_check_estimate_ref(estimate), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            EstimatePanelRow(**kwargs))
        return validate_row(built, estimate, source)
    if isinstance(row, EstimatePanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return EstimatePanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return EstimatePanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an EstimatePanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[EstimatePanelRow, ...]
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
        f"The estimate book holds {total_items} estimates as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown estimates "
        f"stand complete.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its estimate's own fields "
        "- the slice it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any estimate.",
        "Completeness is measured from the held records alone: "
        "a estimate that steps outside the estimate sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not reached calibrated stands open, named in its "
        "gaps, and the estimate index is derived from the "
        "held estimates, never stored where it could drift.",
    )

@dataclass(frozen=True)
class EstimatePanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[EstimatePanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> EstimateView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, EstimateView):
        return view
    return book.view_for(view)


def shown_estimates(source: Any, view: Any = None
                   ) -> Tuple[EstimateRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.estimates
    if resolved.view_filter == "complete":
        return tuple(g for g in book.estimates if estimate_green(g, book))
    return tuple(g for g in book.estimates if not estimate_green(g, book))


def estimates_for_slice(source: Any, slice_id: Any
                      ) -> Tuple[EstimateRecord, ...]:
    wanted = _clean_text(slice_id, "an slice id")
    return tuple(
        g for g in _source_book(source).estimates if g.slice_id == wanted)


def green_estimates(source: Any) -> Tuple[EstimateRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.estimates if estimate_green(g, book))


def current_estimate(source: Any) -> Optional[EstimateRecord]:
    """The book's current estimate, DERIVED at call time.

    The first held estimate, in held order, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held estimates alone, so it can
    never go stale against them. A book whose every
    estimate stands complete has no current estimate.
    """
    book = _source_book(source)
    for estimate in book.estimates:
        if not estimate_green(estimate, book):
            return estimate
    return None


def derive_panel(source: Any, view: Any = None) -> EstimatePanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_estimates(book, resolved)
    rows = tuple(_row_for_estimate(estimate, book) for estimate in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.estimates), default="")
    green = sum(1 for g in shown if estimate_green(g, book))
    return EstimatePanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.estimates), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.estimates), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> EstimatePanel:
    if not isinstance(value, EstimatePanel):
        raise ValueError("a panel must be an EstimatePanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> EstimatePanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 forecast).
    """
    compared = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(compared.view_id)
                if compared.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(compared, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {compared.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return compared


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> EstimatePanel:
    if isinstance(panel, EstimatePanel):
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
        built = EstimatePanel(
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
    raise ValueError("a panel must be a mapping, an EstimatePanel, or derived")


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
        return "calibrated"
    if green_shown == 0:
        return "blocked"
    return "held"


@dataclass(frozen=True)
class EstimateVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> EstimateVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_estimates(book, resolved)
    green = sum(1 for g in shown if estimate_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return EstimateVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> EstimateVerdict:
    if not isinstance(value, EstimateVerdict):
        raise ValueError("a verdict must be an EstimateVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> EstimateVerdict:
    compared = _check_verdict_ref(verdict)
    if compared.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {compared.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(compared.view_id)
                if compared.view_id is not None else None)
        derived = derive_verdict(book, view)
        if compared != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return compared


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> EstimateVerdict:
    if isinstance(verdict, EstimateVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = EstimateVerdict(
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
        "a verdict must be a mapping, an EstimateVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held slices' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    check: str
    estimate_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "check": self.check, "estimate_id": self.estimate_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class EstimateIndex:
    """The estimate index, derived from the held estimates.

    The index names one entry per green estimate, in
    held order - the estimate's own one verifiable
    check, its estimate id and its title - and the
    estimates that do not stand complete, named in its
    gaps. Nothing here is stored on any estimate: the
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


def derive_index(source: Any) -> EstimateIndex:
    """Derive the estimate index from the book's held estimates."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(check=g.check, estimate_id=g.estimate_id,
                   title=g.title)
        for g in book.estimates if estimate_green(g, book))
    gaps = tuple(
        g.estimate_id for g in book.estimates if not estimate_green(g, book))
    return EstimateIndex(entries=entries, gaps=gaps)


def estimate_for_check(source: Any, check: Any) -> Optional[EstimateRecord]:
    """The first held estimate one check reaches, or none - honestly."""
    if check is None:
        return None
    if not isinstance(check, str):
        raise ValueError("an check must be a string naming the check")
    wanted = check.strip()
    if not wanted:
        return None
    for estimate in _source_book(source).estimates:
        if estimate.check == wanted:
            return estimate
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held order: the estimate
    that took it and the step it took, before,
    then after. A book whose estimates all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{estimate_id}: {step}"
        for estimate_id, steps in _breaks_map(book).items()
        for step in steps)

def estimate_order(source: Any,
              slice_id: Any = None) -> Tuple[EstimateRecord, ...]:
    """The held estimates in their held order, DERIVED at call time.

    Estimates stand in the order the book holds them -
    the order their slices were taken - optionally
    for one slice alone. Nothing here is stored:
    the order is the book's own held order, told.
    """
    book = _source_book(source)
    estimates = list(book.estimates)
    if slice_id is not None:
        wanted = _clean_text(slice_id, "a slice id")
        estimates = [r for r in estimates if r.slice_id == wanted]
    return tuple(estimates)

def trace_of(source: Any, estimate_id: Any) -> str:
    """One estimate's trace, DERIVED at call time.

    The estimate's walked checks joined as one trace
    line, in walk order. A estimate that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is named
    elsewhere.
    """
    estimate = _source_book(source).estimate_for(estimate_id)
    return " > ".join(estimate.checks)

def trace_for_estimate(source: Any,
                  estimate_id: Any) -> Optional[TraceRecord]:
    """The held trace for one estimate, or none - honestly."""
    wanted = _clean_text(estimate_id, "a estimate id")
    for record in _source_book(source).traces:
        if record.estimate_id == wanted:
            return record
    return None

def trace_current(source: Any, estimate_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_estimate(source, estimate_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, estimate_id)

def note_for_estimate(source: Any, estimate_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one estimate (and stance, when named)."""
    wanted = _clean_text(estimate_id, "a estimate id")
    for record in _source_book(source).notes:
        if record.estimate_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the slice targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def board_record(source: Any = None) -> Dict[str, Any]:
    """The estimate board, DERIVED here from the held estimates alone.

    The board counts the held estimates by their
    derived completeness - green and red - names
    the current estimate, the first that does not yet
    stand complete, tells each held estimate's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held estimates took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.estimates
            if ("complete" if estimate_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "estimate_records": number})
    current = current_estimate(book)
    traces = []
    for estimate in book.estimates:
        trace = trace_for_estimate(book, estimate.estimate_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, estimate.estimate_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"estimate_id": estimate.estimate_id, "trace": standing})
    return {
        "type": "estimate_board",
        "slice": ESTIMATE_SLICE,
        "standings": standings,
        "total": len(book.estimates),
        "current_estimate": current.estimate_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This slice's own roadmap standing, proved from the roadmap itself.

    The record loads this repo's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 slices in 11 parts,
    the predicted prefix, the next slice where the
    campaign resumes, and M-215's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(ESTIMATE_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "estimate_roadmap",
        "slice": ESTIMATE_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m215_title": own.title,
        "m215_part": own.part,
        "m215_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: slices, estimates, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or order ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class EstimateBook:
    title: str
    slices: Tuple[SliceRef, ...] = ()
    estimates: Tuple[EstimateRecord, ...] = ()
    views: Tuple[EstimateView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[EstimatePanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        slices = tuple(_check_slice_ref(g) for g in self.slices)
        estimates = tuple(_check_estimate_ref(g) for g in self.estimates)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        traces = tuple(_check_trace_ref(a) for a in self.traces)
        panels = tuple(_check_panel_ref(pn) for pn in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for ref in slices:
            if ref.slice_id in seen_ids:
                raise ValueError(
                    f"two slice references stand under id {ref.slice_id!r}")
            if ref.seq in seen_seqs:
                raise ValueError(
                    f"two slice references stand at sequence {ref.seq}")
            seen_ids.add(ref.slice_id)
            seen_seqs.add(ref.seq)
        estimate_ids = set()
        estimate_seqs = set()
        for estimate in estimates:
            if estimate.estimate_id in estimate_ids:
                raise ValueError(
                    f"two estimates stand under id {estimate.estimate_id!r}")
            if estimate.seq in estimate_seqs:
                raise ValueError(
                    f"two estimates stand at sequence {estimate.seq}")
            estimate_ids.add(estimate.estimate_id)
            estimate_seqs.add(estimate.seq)
        by_slice = {ref.slice_id: ref for ref in slices}
        for estimate in (estimates if slices else ()):

            ref = by_slice.get(estimate.slice_id)
            if ref is None:
                raise ValueError(
                    f"estimate {estimate.estimate_id!r} is held from slice "
                    f"{estimate.slice_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "active":
                raise ValueError(
                    f"estimate {estimate.estimate_id!r} is held from slice "
                    f"{estimate.slice_id!r}, which is not active: "
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
            target = (record.estimate_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for estimate "
                    f"{record.estimate_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per estimate target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_estimates = set()
        estimate_ids = {estimate.estimate_id for estimate in estimates}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.estimate_id in trace_estimates:
                raise ValueError(
                    f"two traces stand for estimate "
                    f"{record.estimate_id!r}: one trace stands "
                    f"per estimate walk")
            if estimates and record.estimate_id not in estimate_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces estimate "
                    f"{record.estimate_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_estimates.add(record.estimate_id)
        object.__setattr__(
            self, "slices", tuple(sorted(slices, key=lambda g: g.seq)))
        object.__setattr__(
            self, "estimate_records", tuple(sorted(estimates, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.estimates + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.estimate_id for g in self.estimates) + tuple(
            v.view_id for v in self.views)

    def estimate_ids(self) -> Tuple[str, ...]:
        return tuple(g.estimate_id for g in self.estimates)

    def slice_ids(self) -> Tuple[str, ...]:
        return tuple(g.slice_id for g in self.slices)

    def estimate_for(self, estimate_id: Any) -> EstimateRecord:
        wanted = _clean_text(estimate_id, "a estimate id")
        for estimate in self.estimates:
            if estimate.estimate_id == wanted:
                return estimate
        raise KeyError(f"no estimate named {wanted!r} stands in this book")

    def slice_for(self, slice_id: Any) -> SliceRef:
        wanted = _clean_text(slice_id, "an slice id")
        for ref in self.slices:
            if ref.slice_id == wanted:
                return ref
        raise KeyError(f"no slice named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> EstimateView:
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
        for estimate in self.estimates:
            if estimate.estimate_id == wanted:
                return estimate
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "slices": [g.to_record() for g in self.slices],
            "estimate_records": [g.to_record() for g in self.estimates],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: EstimateBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: EstimateBook) -> None:
    if book.title != "Estimate honesty at the M-214 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.slices) != 3 or len(book.estimates) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three slice references, five estimates and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m214-boundary":
        raise ValueError("the pinned panel is panel-m214-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.check for e in index.entries] != ["calibrated", "calibrated", "calibrated"]:
        raise ValueError("the shipped example book index must derive the three held complete estimates in held order")
    if index.gaps != ("estimate-bare-forecast", "estimate-leaping-forecast"):
        raise ValueError("the shipped example book must leave the bare and leaping estimates honestly open, named in its gaps")
    found = estimate_for_check(book, EXAMPLE_CHECK)
    if found is None or found.estimate_id != "estimate-held-forecast":
        raise ValueError("the shipped example book must reach its opening estimate under the example check")
    if trace_of(book, "estimate-held-forecast") != "predicted > recorded > measured > compared > calibrated":
        raise ValueError("the shipped example book must derive the opening estimate's trace from its walked steps")
    if not trace_current(book, "estimate-held-forecast"):
        raise ValueError("the shipped example book must hold the opening estimate's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note road")

def validate_book(data: Any, *, require_example: bool = False) -> EstimateBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, EstimateBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a estimate book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live slice build or execution "
                f"({key!r} is named on it): {ESTIMATE_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its estimates under a view")
    if "estimate_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held estimates at call time")
    if "board" in data or "current_estimate" in data:
        raise ValueError(
            "a book stores no board and no current estimate: both are "
            "derived from its held estimates at call time")
    if "trace" in data or "order" in data:
        raise ValueError(
            "a book stores no trace and no order: both are derived "
            "from its held estimates at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != ESTIMATE_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{ESTIMATE_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != ESTIMATE_SLICE):
        raise ValueError(
            f"a book's slice must be {ESTIMATE_SLICE!r}")
    head = data.get("estimate_head") or data.get("estimate_honesty") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's estimate head must be a mapping")
    title = head.get("title") or data.get("title")
    slices = tuple(build_slice_ref(g) for g in data.get("slices") or ())
    estimates = tuple(build_estimate(g) for g in data.get("estimate_records") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = EstimateBook(
        title=title, slices=slices, estimates=estimates, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = EstimateBook(
        title=book.title, slices=book.slices, estimates=book.estimates,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> EstimateBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (EstimateBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an EstimateBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> EstimateBook:
    return validate_book(data, require_example=require_example)


def load_estimate(
        data: Optional[Dict[str, Any]] = None) -> EstimateBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(ESTIMATE_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_estimate_file(path: Any) -> EstimateBook:
    """Load one estimate file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: slice references, estimates and views held one by one.
# ---------------------------------------------------------------------

class EstimateRegistry:
    """An in-memory holding of slice references, estimates and views.

    The registry is the pure layer's model of a
    session's estimate book: slice references are
    held under their ids, estimates are held under
    their ids, one estimate per id and per sequence,
    and views are held in recorded order, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[SliceRef] = []
        self._estimates: List[EstimateRecord] = []
        self._views: List[EstimateView] = []
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

    def register_slice_ref(self, item: Any) -> SliceRef:
        """Hold one slice reference, measured whole before held."""
        compared = _check_slice_ref(item)
        return self._register(
            self._slices, compared, "slice_id", "slice reference")

    def register_estimate(self, item: Any) -> EstimateRecord:
        """Hold one estimate, measured whole before held."""
        compared = _check_estimate_ref(item)
        return self._register(
            self._estimates, compared, "estimate_id", "estimate")

    def register_view(self, view: Any) -> EstimateView:
        """Hold one view; a view naming no id takes a fresh one."""
        compared = _check_view_ref(view)
        if not compared.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            compared = build_view({**compared.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, compared, "view_id", "view")

    def register_book(self, book: Any) -> EstimateBook:
        """Hold a whole book's records, under its title."""
        compared = build_book(book)
        if self._title is not None and compared.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {compared.title!r}")
        for ref in compared.slices:
            self.register_slice_ref(ref)
        for estimate in compared.estimates:
            self.register_estimate(estimate)
        for view in compared.views:
            self.register_view(view)
        self._title = compared.title
        return self.book()

    def book(self) -> EstimateBook:
        return EstimateBook(
            title=self._title or "An unheld estimate book",
            slices=tuple(self._slices), estimates=tuple(self._estimates),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[SliceRef, ...]:
        return tuple(self._slices)

    def list_estimates(self) -> Tuple[EstimateRecord, ...]:
        return tuple(self._estimates)

    def list_views(self) -> Tuple[EstimateView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._estimates) + tuple(self._views)

    def get_slice(self, slice_id: Any) -> SliceRef:
        return self.book().slice_for(slice_id)

    def get_estimate(self, estimate_id: Any) -> EstimateRecord:
        return self.book().estimate_for(estimate_id)

    def get_view(self, view_id: Any) -> EstimateView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the journal target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> EstimateBook:
    if source is None:
        return load_estimate()
    if isinstance(source, EstimateBook):
        return source
    if isinstance(source, EstimateRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def estimate_record(estimate: Any, source: Any = None) -> Dict[str, Any]:
    compared = _check_estimate_ref(estimate)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "estimate_estimate",
        "slice": ESTIMATE_SLICE,
        "estimate_id": compared.estimate_id,
        "slice_id": compared.slice_id,
        "title": compared.title,
        "segment": segment_of(compared, book),
        "complete": estimate_green(compared, book),
        "gaps": list(estimate_gaps(compared, book)),
    }
    record.update(_provenance_record(compared))
    return record


def slice_record(ref: Any) -> Dict[str, Any]:
    compared = _check_slice_ref(ref)
    record = {
        "type": "estimate_slice",
        "slice": ESTIMATE_SLICE,
        "slice_id": compared.slice_id,
        "title": compared.title,
        "state": compared.state,
    }
    record.update(_provenance_record(compared))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    compared = _check_trace_ref(record_in)
    record = {
        "type": "estimate_trace",
        "slice": ESTIMATE_SLICE,
        "trace_id": compared.trace_id,
        "estimate_id": compared.estimate_id,
        "trace": compared.trace,
    }
    record.update(_provenance_record(compared))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    compared = _check_view_ref(view)
    record = {
        "type": "estimate_view",
        "slice": ESTIMATE_SLICE,
        "view_id": compared.view_id, "seq": compared.seq,
        "view_filter": compared.view_filter,
    }
    record.update(_provenance_record(compared))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    compared = _check_note_ref(record_in)
    record = {
        "type": "estimate_note",
        "slice": ESTIMATE_SLICE,
        "note_id": compared.note_id,
        "estimate_id": compared.estimate_id,
        "stance": compared.stance,
    }
    record.update(_provenance_record(compared))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    compared = validate_panel(panel, source)
    record = {"type": "estimate_panel",
              "slice": ESTIMATE_SLICE}
    record.update(compared.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, EstimateVerdict):
        compared = validate_verdict(verdict, source)
    else:
        compared = derive_verdict(_source_book(verdict), view)
    record = {"type": "estimate_verdict",
              "slice": ESTIMATE_SLICE}
    record.update(compared.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, EstimateIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "estimate_index",
              "slice": ESTIMATE_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    compared = _source_book(book)
    record = {"type": "estimate_book",
              "slice": ESTIMATE_SLICE,
              "title": compared.title}
    record.update(compared.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(estimate: Any, source: Any = None) -> str:
    compared = _check_estimate_ref(estimate)
    return (
        f"{compared.title} - from {compared.slice_id}: "
        f"check {compared.check if compared.check else 'none'}, "
        f"claims "
        f"{', '.join(compared.claims) if compared.claims else 'none'}. "
        f"{compared.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The estimates stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"estimates stand complete.")


def view_plain_words(view: Any) -> str:
    compared = _check_view_ref(view)
    return f"View {compared.view_id}: shows {compared.view_filter} estimates."


def note_plain_words(record_in: Any) -> str:
    compared = _check_note_ref(record_in)
    return (
        f"Note {compared.note_id}: {compared.stance} "
        f"{compared.estimate_id}, toward {compared.target}. "
        f"{compared.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, EstimateIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} green estimates; "
        f"red, named in its gaps: {gaps}.")

def format_estimate(estimate: Any, source: Any = None) -> str:
    compared = _check_estimate_ref(estimate)
    book = _source_book(source) if source is not None else None
    lines = [f"{compared.title} ({compared.estimate_id})"]
    lines.extend(plain_lines(compared))
    lines.append(compared.detail)
    if estimate_green(compared, book):
        lines.append(
            "This estimate stands complete - it walked the question "
            "sequence in the open from predicted to calibrated, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This estimate stands open - it stands named in "
            f"its gaps: {', '.join(estimate_gaps(compared, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    compared = _check_view_ref(view)
    return (
        f"View {compared.view_id}: filter {compared.view_filter} - "
        f"{compared.detail}")


def format_note(record_in: Any) -> str:
    compared = _check_note_ref(record_in)
    lines = [
        f"Estimate note {compared.stance} {compared.estimate_id} "
        f"({compared.note_id}): {compared.title}. {compared.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_check(source: Any, check: Any) -> str:
    estimate = estimate_for_check(source, check)
    if estimate is not None:
        return format_estimate(estimate, source)
    wanted = check.strip() if isinstance(check, str) else check
    return (
        f"No held estimate stands under check {wanted!r} yet - the "
        f"check reaches nothing in this book, and no estimate is "
        f"invented for it.")


def format_book(source: Any = None, slice_id: Any = None) -> str:
    book = _source_book(source)
    estimates = (estimates_for_slice(book, slice_id)
              if slice_id is not None else book.estimates)
    lines = [f"The Estimate Gate (M-215) - {book.title}"]
    lines.extend(segment_of(estimate, book) for estimate in estimates)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Estimate panel under view {panel.view_id}:"]
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
    lines = ["Estimate index, derived from the held estimates:"]
    for entry in index.entries:
        lines.append(f"{entry.check} - {entry.title} ({entry.estimate_id})")
    if index.gaps:
        lines.append(
            "Red, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_estimate_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Estimate Gate (M-215)",
        f"{book.title}: {len(book.estimates)} estimates held, "
        f"{len(green_estimates(book))} estimates standing green, "
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


def parse_estimate_args(args: Any) -> Tuple[str, Any]:
    """Parse the /estimate grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("estimate", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("check", "slice"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
