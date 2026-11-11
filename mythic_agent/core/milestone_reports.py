"""Reports (roadmap slice M-220).

Part IX - The Mythic Method Engine. The roadmap
words: **at part boundaries the coordinator reports plainly — done with evidence, partial with its road, blocked with what it needs.*

What already ships, and what this slice adds:

* The reports book already ships as data
  (M-201, ``core/milestones.py``): a roadmap/report
  file (parts, slices, acceptance checks, state) the
  app reads. This slice WIRES the milestone that book's
  milestone invites - several reports held across
  boundaries with one chronicle over them - as data, in its
  own module, standing in the M-195 copy-and-share
  book milestone the M-220 book stands in: one reportkeeper
  per milestone, and the reportkeeper's charge over one
  report across its boundary held as a book - a
  report. The shipped reports stand untouched behind
  their seams: this layer holds reports as data
  over the milestone's boundaries and rewrites none of them,
  and the reports book keeps its own standing.
  Reports stand on the chronicle AS DATA alone: a
  report carries a chronicle ref, a reference held in
  this book; holding, viewing or telling a report
  runs no report live, moves no keeper and files
  nothing.
* No charter row names this slice: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-220 on no row, and the
  slice tests pin that absence live. The M-005
  method charter names no slice row either: its
  own words name the whole of Part IX as the
  part that executes the charter, and this slice
  is built to the roadmap words and that
  execution note together.

* A report is held whole: the slice it
  answers for, named by its slice id; its title;
  the report steps it walked, held as data in
  walk order; and the evidence it carries, held
  as data by boundary. The report walk is EXPLICIT:
  its sequence stands as data
  (:data:`CHECKS`, :data:`TRANSITIONS`) -
  reached, gathered, weighed, stated, reported -
  and a report's standing is DERIVED at
  call time from its held steps and evidence
  alone: a report that opens anywhere but
  reached, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet reached reported stands
  open, named in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - boundary_ref,
  evidence_ref, keeper_record, report_ref, evidence
  a reportkeeper can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A report is
  stated from held evidence alone, never
  from a feeling: a report holding a
  bare claim stands open, named in its gaps.
* A report stands only for an ACTIVE
  slice. The book holds each slice it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  report naming a slice that stands
  nowhere in the book refuses BY NAME, and a
  report for a slice that is not active
  refuses BY NAME beside it: the reportkeeper deals with
  the slice in hand, in roadmap order, never a
  queued one, and a slice whose report already
  stands complete is never weighed twice - the
  current report is derived, so a
  completed slice is never the current report
  twice.
* The report's trace is visible. A trace
  record holds one report's walked steps
  as one trace line, exactly as walked, beside
  the report. The derived trace is
  computed at call time from the report's
  held steps; a held trace that no longer agrees
  with it stands stale, named in the chronicle - the
  trace is the walk itself, never a retelling
  of it.
* The report index is DERIVED at call
  time from the held reports - one entry
  per complete report, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, order or current-report
  claim on any record refuses by name.
* The current report is DERIVED at call
  time - the first held report, in held
  order, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its report, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per report stance; holding
  a note posts none of it, the rule stands as
  data (:data:`REPORT_RULE`), and a record
  claiming a report was actually reported,
  captured or promoted live refuses BY NAME.
  The reportkeeper reports - and those reports, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the milestone a real report
  file takes, a loader reads a file anywhere on
  disk, reports and views are gathered as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a report book for a session and
  telling from it. This layer reaches no live
  report: it writes no report live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no reportkeeper, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds reports
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The report walk is explicit.** A
  report is stated against the held
  steps and legal steps alone; an illegal step
  stands named in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  report that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, named in its gaps:
  a report is stated from evidence, not
  vibes.
* **Active slices only, in roadmap order.** A
  report for a missing or queued slice
  refuses by name; no report is invented
  for a slice the reportkeeper has not dealt with.
* **Unknown stays unknown.** A report
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, order
  and current report are derived, never
  stored.** Each is derived from the held
  reports at call time; a stored one
  refuses by name, so it can never drift.
* **One report per report.** Two
  reports standing for one report id
  refuse by name, and one note record stands per
  report stance.
* **The notes are data alone.** The records
  hold the feedback; holding, viewing or telling
  them writes nothing, files nothing and posts
  nothing.
"""


from __future__ import annotations

__all__ = [
    "CHECK_FIELDS",
    "CHECKS",
    "CLAIM_BOUNDARYS",
    "HELD_EVIDENCE",
    "BARE_CLAIMS",
    "TRANSITIONS",
    "EXAMPLE_CHECK",
    "STANCES",
    "INDEX_ACTION",
    "REPORT_RESOURCE",
    "REPORT_SCHEMA",
    "REPORT_SLICE",
    "REPORT_RULE",
    "PLAIN_EXPLANATION",
    "THE_REPORT_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "COMPLETE_WORDS",
    "BOUNDARY_STATES",
    "Any",
    "Dict",
    "List",
    "Optional",
    "TraceRecord",
    "ReportRecord",
    "IndexEntry",
    "BoundaryRef",
    "NoteRecord",
    "ReportBook",
    "ReportIndex",
    "ReportPanel",
    "ReportPanelRow",
    "ReportRegistry",
    "ReportVerdict",
    "ReportView",
    "TargetCount",
    "trace_for_report",
    "trace_record",
    "chronicle_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_report",
    "build_boundary_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_report",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "report_for_check",
    "report_order",
    "report_record",
    "first_note",
    "format_book",
    "format_report",
    "format_index",
    "format_note",
    "format_check",
    "format_panel",
    "format_report_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "boundary_record",
    "load_report",
    "load_report_file",
    "normalize_boundary_state",
    "normalize_check",
    "normalize_claim_boundary",
    "legal_step",
    "next_check",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_report",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_report_args",
    "green_reports",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_reports",
    "validate_trace",
    "validate_book",
    "validate_report",
    "validate_boundary_ref",
    "validate_note",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
    "report_gaps",
    "report_green",
    "reports_for_boundary",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

REPORT_SCHEMA = "mythic.milestone_reports/1"
REPORT_SLICE = "M-220"
THE_REPORT_SLICE = REPORT_SLICE
REPORT_RESOURCE = "milestone_reports.yaml"
INDEX_ACTION = "index"
EXAMPLE_CHECK = "reported"
CHECK_FIELDS = ("checks", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("reported", "held", "blocked")
BOUNDARY_STATES = ("live", "dormant")
REPORT_RULE = 'reports are held as data alone: several reports across boundaries stand with one chronicle, keepers per report, and the human sees the whole forge at a run - a run stands as data, held by reference (a run ref), never taken live - the report walk stands as an explicit report sequence - reached, gathered, weighed, stated, reported - and a report completes only complete, complete being a state with evidence held - boundary ref, chronicle ref, keeper record, run ref - never a feeling, a memory, an assertion or a summary; holding, viewing and reading a report runs no report live, approves nothing, spawns no process and opens no network'
PLAIN_EXPLANATION = "Milestone reports (M-220): at part boundaries the coordinator reports plainly — done with evidence, partial with its road, blocked with what it needs."
USAGE = 'Usage: /milestones | /milestones report <report-id> | /milestones check <check> | /milestones boundary <boundary-id> | /milestones view <view-id> | /milestones note <note-id> | /milestones index | /milestones panel | /milestones verdict'

CHECKS = ("reached", "gathered", "weighed", "stated", "reported")
HELD_EVIDENCE = ("boundary_ref", "evidence_ref", "keeper_record", "report_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_BOUNDARYS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "reached": ("gathered",),
    "gathered": ("weighed",),
    "weighed": ("stated",),
    "stated": ("reached", "reported"),
    "reported": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a failure or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a report stands complete.
    A check outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_check(check: Any, failed: Any = False) -> Optional[str]:
    """The step the reportkeeper takes next, DERIVED from the sequence.

    Banked leads to gathered and gathered to
    weighed; weighed leads to stated; at
    stated a follow-up banking steps back to reached and a finished report steps to reported;
    reported is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    stated = normalize_check(check)
    if stated == "reached":
        return "gathered"
    if stated == "gathered":
        return "weighed"
    if stated == "weighed":
        return "stated"
    if stated == "stated":
        return "reached" if failed else "reported"
    return None


_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "report_id", "seq", "boundary_id", "title", "checks",
    "claims", "detail",
} | set(_PROVENANCE))
_SLICE_REF_KEYS = frozenset({
    "boundary_id", "seq", "title", "state", "detail",
} | set(_PROVENANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "report_id", "trace", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "report_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered",
    "current_report", "next_report", "progress", "chronicle",
    "current", "order", "breaks", "live"})
_LIVE_KEYS = (
    "live_report", "reports_live", "live_question",
    "reports_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "reports_live",
    "resumed_live", "boundaries_report", "paused_live",
    "runs_report", "ran_report", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "report_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_report", "sent_report",
    "posts_note", "posted_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_report", "filed_live", "spawns_reportkeeper", "spawned_reportkeeper", "sends_report", "sent_report", "writes_report", "wrote_report")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_checks(value: Any) -> Tuple[str, ...]:
    """A report's walked checks, held as data.

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
    """A report's asked claims: claim boundaries named as data.

    Each claim names one boundary from the reported
    vocabulary - the human boundaries the gate may ask
    and the code boundaries it must never ask, both
    held honestly as data - and a boundary outside
    the vocabulary refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("claims must be a list of claim boundaries")
    return tuple(normalize_claim_boundary(v) for v in value)

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
                f"{what} claims a live gate report or slice build "
                f"execution ({key!r} is named on it): "
                f"{REPORT_RULE}")
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


def normalize_boundary_state(value: Any) -> str:
    state = _clean_text(value, "an slice state").lower()
    if state not in BOUNDARY_STATES:
        raise ValueError(
            f"slice state {state!r} is not one of the held "
            f"states: " + ", ".join(BOUNDARY_STATES))
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


def normalize_claim_boundary(value: Any) -> str:
    boundary = _clean_text(value, "a claim boundary").lower()
    if boundary not in CLAIM_BOUNDARYS:
        raise ValueError(
            f"claim boundary {boundary!r} is not one of the held "
            f"boundaries: " + ", ".join(CLAIM_BOUNDARYS))
    return boundary

# ---------------------------------------------------------------------
# The held report: one slice cut from an active slice.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ReportRecord:
    """One report slice, held as data.

    The report names the active slice it was
    held from, by slice id, its title, its
    verifiable checks, held as data, and its
    claims, named by report id. The grain is
    derived, never stored: exactly one verifiable
    walk is weighed against the machine. A report whose
    checks are not yet held stands with its
    checks empty: it stands open, named in
    its gaps, and no check is invented for it.
    The report is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    report_id: str
    seq: int
    boundary_id: str
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
            self, "report_id", _clean_text(self.report_id, "a report id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "boundary_id", _clean_text(self.boundary_id, "an slice id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a report title"))
        object.__setattr__(
            self, "checks", _check_checks(self.checks))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a report detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.report_id

    @property
    def check(self) -> str:
        """The check the report stands at: its last walked check."""
        return self.checks[-1] if self.checks else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "report_id": self.report_id, "seq": self.seq,
            "boundary_id": self.boundary_id, "title": self.title,
            "checks": list(self.checks),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_report_ref(value: Any) -> ReportRecord:
    if not isinstance(value, ReportRecord):
        raise ValueError("a report must be a ReportRecord")
    return value


def validate_report(report: Any) -> ReportRecord:
    return _check_report_ref(report)


def build_report(record: Any = None, **kwargs: Any) -> ReportRecord:
    """Build one held report from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, ReportRecord):
        if kwargs:
            raise ValueError("a report stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a report must be a mapping or a ReportRecord")
    _needed(data, _RUN_KEYS, "a report")
    return ReportRecord(
        report_id=data.get("report_id"), seq=data.get("seq"),
        boundary_id=data.get("boundary_id"), title=data.get("title"),
        checks=data.get("checks"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_provenance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each report to the steps it took outside the machine.

    Derived from the held reports alone: a break is
    one consecutive pair of walked checks the
    explicit gate sequence does not allow, told
    in walk order as before, then after.
    """
    found: Dict[str, Tuple[str, ...]] = {}
    for report in book.reports:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(report.checks, report.checks[1:])
            if not legal_step(before, after))
        if breaks:
            found[report.report_id] = breaks
    return found

def report_gaps(report: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a report from standing complete.

    Weighed from the report's own held fields alone -
    its walked steps against the explicit question
    sequence, and its carried evidence against the
    reported vocabulary: the report opens at
    named, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a report stands complete only when it has
    reached reported. The source names nothing
    further: no gap is borrowed from another
    report.
    """
    stated = _check_report_ref(report)
    gaps: List[str] = []
    if not stated.checks:
        gaps.append(
            "has passed through no step: the report has not started")
        return tuple(gaps)
    if stated.checks[0] != "reached":
        gaps.append(
            f"opens at {stated.checks[0]}, not at reached: "
            f"the report opens with the reflection")
    for before, after in zip(stated.checks, stated.checks[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"report sequence does not allow")
    for boundary in stated.claims:
        if boundary in BARE_CLAIMS:
            gaps.append(
                f"carries a {boundary} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if stated.checks[-1] != "reported":
        gaps.append(
            f"has not reached reported: the report stands "
            f"at {stated.checks[-1]}")
    return tuple(gaps)

def report_green(report: Any, source: Any = None) -> bool:
    return not report_gaps(report, source)


def plain_lines(report: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the report's own fields."""
    stated = _check_report_ref(report)
    return (
        f"Report: {stated.title}",
        f"Boundary: {stated.boundary_id}",
        f"Check: {stated.check if stated.check else 'none'}",
        f"Claims: "
        f"{', '.join(stated.claims) if stated.claims else 'none'}",
    )


def segment_of(report: Any, source: Any = None) -> str:
    stated = _check_report_ref(report)
    gaps = report_gaps(stated, source)
    return (
        f"{stated.report_id}: {stated.title} - slice: "
        f"'{stated.boundary_id}' - check: "
        f"'{stated.check if stated.check else 'none'}' - "
        f"checks: {len(stated.checks)} - claims: "
        f"'{', '.join(stated.claims) if stated.claims else 'none'}' - "
        f"detail: '{stated.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held slice reference: the active slice a book reports from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class BoundaryRef:
    """One slice a report book reports from, held as a reference.

    The record names the slice, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 slice book's own telling. A report
    stands only from an active reference: the
    book refuses a report naming no held reference,
    and a report from an queued one, BY NAME.
    """

    boundary_id: str
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
            self, "boundary_id", _clean_text(self.boundary_id, "an slice id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(
            self, "state", normalize_boundary_state(self.state))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an slice detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.boundary_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "boundary_id": self.boundary_id, "seq": self.seq,
            "title": self.title, "state": self.state,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_boundary_ref(value: Any) -> BoundaryRef:
    if not isinstance(value, BoundaryRef):
        raise ValueError("a slice reference must be an BoundaryRef")
    return value


def validate_boundary_ref(ref: Any) -> BoundaryRef:
    return _check_boundary_ref(ref)


def build_boundary_ref(record: Any = None, **kwargs: Any) -> BoundaryRef:
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, BoundaryRef):
        if kwargs:
            raise ValueError(
                "a slice reference stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError(
            "a slice reference must be a mapping or an BoundaryRef")
    _needed(data, _SLICE_REF_KEYS, "a slice reference")
    return BoundaryRef(
        boundary_id=data.get("boundary_id"), seq=data.get("seq"),
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
    human active - the slice's report ids in
    derived claim order, held exactly as
    active. The trace is of the set and its
    order, never of a step: when the derived
    trace moves, this record stands stale, named
    in the chronicle, until a new trace is active.
    """

    trace_id: str
    seq: int
    report_id: str
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
            self, "report_id", _clean_text(self.report_id, "an slice id"))
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
            "report_id": self.report_id, "trace": self.trace,
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
        report_id=data.get("report_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a report, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One report stance, held as data.

    The record names its report, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per report stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    report_id: str
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
            self, "report_id", _clean_text(self.report_id, "a report id"))
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
            "report_id": self.report_id, "stance": self.stance,
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
        report_id=data.get("report_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which slices a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ReportView:
    """A view over the book: every report, the green, the rest."""

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


def _check_view_ref(value: Any) -> ReportView:
    if not isinstance(value, ReportView):
        raise ValueError("a view must be an ReportView")
    return value


def validate_view(view: Any) -> ReportView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> ReportView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, ReportView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an ReportView")
    _needed(data, _VIEW_KEYS, "a view")
    return ReportView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ReportPanelRow:
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


def _row_for_report(report: ReportRecord,
                     source: Any = None) -> ReportPanelRow:
    return ReportPanelRow(
        item_id=report.report_id,
        standing="complete" if report_green(report, source) else "open",
        label=report.title, segment=segment_of(report, source),
        recorded_on=report.recorded_on)


def _check_row_ref(value: Any) -> ReportPanelRow:
    if not isinstance(value, ReportPanelRow):
        raise ValueError("a panel row must be an ReportPanelRow")
    return value


def validate_row(row: Any, report: Any = None,
                 source: Any = None) -> ReportPanelRow:
    stated = _check_row_ref(row)
    if report is not None:
        derived = _row_for_report(_check_report_ref(report), source)
        if stated != derived:
            raise ValueError(
                f"panel row {stated.item_id!r} does not agree with "
                f"the row derived from its report")
    return stated


def build_row(row: Any = None, report: Any = None,
              source: Any = None,
              **kwargs: Any) -> ReportPanelRow:
    if report is not None:
        derived = _row_for_report(_check_report_ref(report), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            ReportPanelRow(**kwargs))
        return validate_row(built, report, source)
    if isinstance(row, ReportPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return ReportPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return ReportPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an ReportPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[ReportPanelRow, ...]
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
        f"The report book holds {total_items} reports as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown reports "
        f"stand complete.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its report's own fields "
        "- the slice it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any report.",
        "Completeness is weighed from the held records alone: "
        "a report that steps outside the report sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not reached reported stands open, named in its "
        "gaps, and the report index is derived from the "
        "held reports, never stored where it could drift.",
    )

@dataclass(frozen=True)
class ReportPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[ReportPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> ReportView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, ReportView):
        return view
    return book.view_for(view)


def shown_reports(source: Any, view: Any = None
                   ) -> Tuple[ReportRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.reports
    if resolved.view_filter == "complete":
        return tuple(g for g in book.reports if report_green(g, book))
    return tuple(g for g in book.reports if not report_green(g, book))


def reports_for_boundary(source: Any, boundary_id: Any
                      ) -> Tuple[ReportRecord, ...]:
    wanted = _clean_text(boundary_id, "an slice id")
    return tuple(
        g for g in _source_book(source).reports if g.boundary_id == wanted)


def green_reports(source: Any) -> Tuple[ReportRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.reports if report_green(g, book))


def current_report(source: Any) -> Optional[ReportRecord]:
    """The book's current report, DERIVED at call time.

    The first held report, in held order, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held reports alone, so it can
    never go stale against them. A book whose every
    report stands complete has no current report.
    """
    book = _source_book(source)
    for report in book.reports:
        if not report_green(report, book):
            return report
    return None


def derive_panel(source: Any, view: Any = None) -> ReportPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_reports(book, resolved)
    rows = tuple(_row_for_report(report, book) for report in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.reports), default="")
    green = sum(1 for g in shown if report_green(g, book))
    return ReportPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.reports), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.reports), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> ReportPanel:
    if not isinstance(value, ReportPanel):
        raise ValueError("a panel must be an ReportPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> ReportPanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 report).
    """
    stated = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(stated.view_id)
                if stated.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(stated, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {stated.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return stated


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> ReportPanel:
    if isinstance(panel, ReportPanel):
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
        built = ReportPanel(
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
    raise ValueError("a panel must be a mapping, an ReportPanel, or derived")


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
        return "reported"
    if green_shown == 0:
        return "blocked"
    return "held"


@dataclass(frozen=True)
class ReportVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> ReportVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_reports(book, resolved)
    green = sum(1 for g in shown if report_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return ReportVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> ReportVerdict:
    if not isinstance(value, ReportVerdict):
        raise ValueError("a verdict must be an ReportVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> ReportVerdict:
    stated = _check_verdict_ref(verdict)
    if stated.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {stated.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(stated.view_id)
                if stated.view_id is not None else None)
        derived = derive_verdict(book, view)
        if stated != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return stated


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> ReportVerdict:
    if isinstance(verdict, ReportVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = ReportVerdict(
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
        "a verdict must be a mapping, an ReportVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held slices' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    check: str
    report_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "check": self.check, "report_id": self.report_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class ReportIndex:
    """The report index, derived from the held reports.

    The index names one entry per green report, in
    held order - the report's own one verifiable
    check, its report id and its title - and the
    reports that do not stand complete, named in its
    gaps. Nothing here is stored on any report: the
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


def derive_index(source: Any) -> ReportIndex:
    """Derive the report index from the book's held reports."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(check=g.check, report_id=g.report_id,
                   title=g.title)
        for g in book.reports if report_green(g, book))
    gaps = tuple(
        g.report_id for g in book.reports if not report_green(g, book))
    return ReportIndex(entries=entries, gaps=gaps)


def report_for_check(source: Any, check: Any) -> Optional[ReportRecord]:
    """The first held report one check reaches, or none - honestly."""
    if check is None:
        return None
    if not isinstance(check, str):
        raise ValueError("an check must be a string naming the check")
    wanted = check.strip()
    if not wanted:
        return None
    for report in _source_book(source).reports:
        if report.check == wanted:
            return report
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held order: the report
    that took it and the step it took, before,
    then after. A book whose reports all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{report_id}: {step}"
        for report_id, steps in _breaks_map(book).items()
        for step in steps)

def report_order(source: Any,
              boundary_id: Any = None) -> Tuple[ReportRecord, ...]:
    """The held reports in their held order, DERIVED at call time.

    Reports stand in the order the book holds them -
    the order their slices were taken - optionally
    for one slice alone. Nothing here is stored:
    the order is the book's own held order, told.
    """
    book = _source_book(source)
    reports = list(book.reports)
    if boundary_id is not None:
        wanted = _clean_text(boundary_id, "a slice id")
        reports = [r for r in reports if r.boundary_id == wanted]
    return tuple(reports)

def trace_of(source: Any, report_id: Any) -> str:
    """One report's trace, DERIVED at call time.

    The report's walked checks joined as one trace
    line, in walk order. A report that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is named
    elsewhere.
    """
    report = _source_book(source).report_for(report_id)
    return " > ".join(report.checks)

def trace_for_report(source: Any,
                  report_id: Any) -> Optional[TraceRecord]:
    """The held trace for one report, or none - honestly."""
    wanted = _clean_text(report_id, "a report id")
    for record in _source_book(source).traces:
        if record.report_id == wanted:
            return record
    return None

def trace_current(source: Any, report_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_report(source, report_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, report_id)

def note_for_report(source: Any, report_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one report (and stance, when named)."""
    wanted = _clean_text(report_id, "a report id")
    for record in _source_book(source).notes:
        if record.report_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the slice targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def chronicle_record(source: Any = None) -> Dict[str, Any]:
    """The report chronicle, DERIVED here from the held reports alone.

    The chronicle counts the held reports by their
    derived completeness - green and red - names
    the current report, the first that does not yet
    stand complete, tells each held report's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held reports took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.reports
            if ("complete" if report_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "report_records": number})
    current = current_report(book)
    traces = []
    for report in book.reports:
        trace = trace_for_report(book, report.report_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, report.report_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"report_id": report.report_id, "trace": standing})
    return {
        "type": "report_well",
        "slice": REPORT_SLICE,
        "standings": standings,
        "total": len(book.reports),
        "current_report": current.report_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This slice's own roadmap standing, proved from the roadmap itself.

    The record loads this boundary's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 slices in 11 parts,
    the reached prefix, the next slice where the
    report reports, and M-220's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(REPORT_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "report_roadmap",
        "slice": REPORT_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m220_title": own.title,
        "m220_part": own.part,
        "m220_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: slices, reports, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or order ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ReportBook:
    title: str
    slices: Tuple[BoundaryRef, ...] = ()
    reports: Tuple[ReportRecord, ...] = ()
    views: Tuple[ReportView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[ReportPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        slices = tuple(_check_boundary_ref(g) for g in self.slices)
        reports = tuple(_check_report_ref(g) for g in self.reports)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        traces = tuple(_check_trace_ref(a) for a in self.traces)
        panels = tuple(_check_panel_ref(pn) for pn in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for ref in slices:
            if ref.boundary_id in seen_ids:
                raise ValueError(
                    f"two slice references stand under id {ref.boundary_id!r}")
            if ref.seq in seen_seqs:
                raise ValueError(
                    f"two slice references stand at sequence {ref.seq}")
            seen_ids.add(ref.boundary_id)
            seen_seqs.add(ref.seq)
        report_ids = set()
        report_seqs = set()
        for report in reports:
            if report.report_id in report_ids:
                raise ValueError(
                    f"two reports stand under id {report.report_id!r}")
            if report.seq in report_seqs:
                raise ValueError(
                    f"two reports stand at sequence {report.seq}")
            report_ids.add(report.report_id)
            report_seqs.add(report.seq)
        by_slice = {ref.boundary_id: ref for ref in slices}
        for report in (reports if slices else ()):

            ref = by_slice.get(report.boundary_id)
            if ref is None:
                raise ValueError(
                    f"report {report.report_id!r} is held from slice "
                    f"{report.boundary_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "live":
                raise ValueError(
                    f"report {report.report_id!r} is held from slice "
                    f"{report.boundary_id!r}, which is not active: "
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
            target = (record.report_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for report "
                    f"{record.report_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per report target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_reports = set()
        report_ids = {report.report_id for report in reports}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.report_id in trace_reports:
                raise ValueError(
                    f"two traces stand for report "
                    f"{record.report_id!r}: one trace stands "
                    f"per report walk")
            if reports and record.report_id not in report_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces report "
                    f"{record.report_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_reports.add(record.report_id)
        object.__setattr__(
            self, "boundaries", tuple(sorted(slices, key=lambda g: g.seq)))
        object.__setattr__(
            self, "report_records", tuple(sorted(reports, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.reports + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.report_id for g in self.reports) + tuple(
            v.view_id for v in self.views)

    def report_ids(self) -> Tuple[str, ...]:
        return tuple(g.report_id for g in self.reports)

    def boundary_ids(self) -> Tuple[str, ...]:
        return tuple(g.boundary_id for g in self.slices)

    def report_for(self, report_id: Any) -> ReportRecord:
        wanted = _clean_text(report_id, "a report id")
        for report in self.reports:
            if report.report_id == wanted:
                return report
        raise KeyError(f"no report named {wanted!r} stands in this book")

    def slice_for(self, boundary_id: Any) -> BoundaryRef:
        wanted = _clean_text(boundary_id, "an slice id")
        for ref in self.slices:
            if ref.boundary_id == wanted:
                return ref
        raise KeyError(f"no slice named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> ReportView:
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
        for report in self.reports:
            if report.report_id == wanted:
                return report
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "boundaries": [g.to_record() for g in self.slices],
            "report_records": [g.to_record() for g in self.reports],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: ReportBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: ReportBook) -> None:
    if book.title != "Milestone reports at the M-220 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.slices) != 3 or len(book.reports) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three slice references, five reports and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m219-boundary":
        raise ValueError("the pinned panel is panel-m219-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.check for e in index.entries] != ["reported", "reported", "reported"]:
        raise ValueError("the shipped example book index must derive the three held complete reports in held order")
    if index.gaps != ("report-bare-report", "report-leaping-report"):
        raise ValueError("the shipped example book must leave the bare and leaping reports honestly open, named in its gaps")
    found = report_for_check(book, EXAMPLE_CHECK)
    if found is None or found.report_id != "report-held-report":
        raise ValueError("the shipped example book must reach its opening report under the example check")
    if trace_of(book, "report-held-report") != "reached > gathered > weighed > stated > reported":
        raise ValueError("the shipped example book must derive the opening report's trace from its walked steps")
    if not trace_current(book, "report-held-report"):
        raise ValueError("the shipped example book must hold the opening report's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note report")

def validate_book(data: Any, *, require_example: bool = False) -> ReportBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, ReportBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a report book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live slice build or execution "
                f"({key!r} is named on it): {REPORT_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its reports under a view")
    if "report_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held reports at call time")
    if "chronicle" in data or "current_report" in data:
        raise ValueError(
            "a book stores no chronicle and no current report: both are "
            "derived from its held reports at call time")
    if "trace" in data or "order" in data:
        raise ValueError(
            "a book stores no trace and no order: both are derived "
            "from its held reports at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != REPORT_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{REPORT_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != REPORT_SLICE):
        raise ValueError(
            f"a book's slice must be {REPORT_SLICE!r}")
    head = data.get("report_head") or data.get("milestone_reports") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's report head must be a mapping")
    title = head.get("title") or data.get("title")
    slices = tuple(build_boundary_ref(g) for g in data.get("boundaries") or ())
    reports = tuple(build_report(g) for g in data.get("report_records") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = ReportBook(
        title=title, slices=slices, reports=reports, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = ReportBook(
        title=book.title, slices=book.slices, reports=book.reports,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> ReportBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (ReportBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an ReportBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> ReportBook:
    return validate_book(data, require_example=require_example)


def load_report(
        data: Optional[Dict[str, Any]] = None) -> ReportBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(REPORT_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_report_file(path: Any) -> ReportBook:
    """Load one report file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: slice references, reports and views held one by one.
# ---------------------------------------------------------------------

class ReportRegistry:
    """An in-memory holding of slice references, reports and views.

    The registry is the pure layer's model of a
    session's report book: slice references are
    held under their ids, reports are held under
    their ids, one report per id and per sequence,
    and views are held in gathered order, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[BoundaryRef] = []
        self._reports: List[ReportRecord] = []
        self._views: List[ReportView] = []
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

    def register_boundary_ref(self, item: Any) -> BoundaryRef:
        """Hold one slice reference, weighed whole before held."""
        stated = _check_boundary_ref(item)
        return self._register(
            self._slices, stated, "boundary_id", "slice reference")

    def register_report(self, item: Any) -> ReportRecord:
        """Hold one report, weighed whole before held."""
        stated = _check_report_ref(item)
        return self._register(
            self._reports, stated, "report_id", "report")

    def register_view(self, view: Any) -> ReportView:
        """Hold one view; a view naming no id takes a fresh one."""
        stated = _check_view_ref(view)
        if not stated.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            stated = build_view({**stated.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, stated, "view_id", "view")

    def register_book(self, book: Any) -> ReportBook:
        """Hold a whole book's records, under its title."""
        stated = build_book(book)
        if self._title is not None and stated.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {stated.title!r}")
        for ref in stated.slices:
            self.register_boundary_ref(ref)
        for report in stated.reports:
            self.register_report(report)
        for view in stated.views:
            self.register_view(view)
        self._title = stated.title
        return self.book()

    def book(self) -> ReportBook:
        return ReportBook(
            title=self._title or "An unheld report book",
            slices=tuple(self._slices), reports=tuple(self._reports),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[BoundaryRef, ...]:
        return tuple(self._slices)

    def list_reports(self) -> Tuple[ReportRecord, ...]:
        return tuple(self._reports)

    def list_views(self) -> Tuple[ReportView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._reports) + tuple(self._views)

    def get_slice(self, boundary_id: Any) -> BoundaryRef:
        return self.book().slice_for(boundary_id)

    def get_report(self, report_id: Any) -> ReportRecord:
        return self.book().report_for(report_id)

    def get_view(self, view_id: Any) -> ReportView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the chronicle target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> ReportBook:
    if source is None:
        return load_report()
    if isinstance(source, ReportBook):
        return source
    if isinstance(source, ReportRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def report_record(report: Any, source: Any = None) -> Dict[str, Any]:
    stated = _check_report_ref(report)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "report_report",
        "slice": REPORT_SLICE,
        "report_id": stated.report_id,
        "boundary_id": stated.boundary_id,
        "title": stated.title,
        "segment": segment_of(stated, book),
        "complete": report_green(stated, book),
        "gaps": list(report_gaps(stated, book)),
    }
    record.update(_provenance_record(stated))
    return record


def boundary_record(ref: Any) -> Dict[str, Any]:
    stated = _check_boundary_ref(ref)
    record = {
        "type": "report_slice",
        "slice": REPORT_SLICE,
        "boundary_id": stated.boundary_id,
        "title": stated.title,
        "state": stated.state,
    }
    record.update(_provenance_record(stated))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    stated = _check_trace_ref(record_in)
    record = {
        "type": "report_trace",
        "slice": REPORT_SLICE,
        "trace_id": stated.trace_id,
        "report_id": stated.report_id,
        "trace": stated.trace,
    }
    record.update(_provenance_record(stated))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    stated = _check_view_ref(view)
    record = {
        "type": "report_view",
        "slice": REPORT_SLICE,
        "view_id": stated.view_id, "seq": stated.seq,
        "view_filter": stated.view_filter,
    }
    record.update(_provenance_record(stated))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    stated = _check_note_ref(record_in)
    record = {
        "type": "report_note",
        "slice": REPORT_SLICE,
        "note_id": stated.note_id,
        "report_id": stated.report_id,
        "stance": stated.stance,
    }
    record.update(_provenance_record(stated))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    stated = validate_panel(panel, source)
    record = {"type": "report_panel",
              "slice": REPORT_SLICE}
    record.update(stated.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, ReportVerdict):
        stated = validate_verdict(verdict, source)
    else:
        stated = derive_verdict(_source_book(verdict), view)
    record = {"type": "report_verdict",
              "slice": REPORT_SLICE}
    record.update(stated.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, ReportIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "report_index",
              "slice": REPORT_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    stated = _source_book(book)
    record = {"type": "report_book",
              "slice": REPORT_SLICE,
              "title": stated.title}
    record.update(stated.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(report: Any, source: Any = None) -> str:
    stated = _check_report_ref(report)
    return (
        f"{stated.title} - from {stated.boundary_id}: "
        f"check {stated.check if stated.check else 'none'}, "
        f"claims "
        f"{', '.join(stated.claims) if stated.claims else 'none'}. "
        f"{stated.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The reports stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"reports stand complete.")


def view_plain_words(view: Any) -> str:
    stated = _check_view_ref(view)
    return f"View {stated.view_id}: shows {stated.view_filter} reports."


def note_plain_words(record_in: Any) -> str:
    stated = _check_note_ref(record_in)
    return (
        f"Note {stated.note_id}: {stated.stance} "
        f"{stated.report_id}, toward {stated.target}. "
        f"{stated.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, ReportIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} green reports; "
        f"red, named in its gaps: {gaps}.")

def format_report(report: Any, source: Any = None) -> str:
    stated = _check_report_ref(report)
    book = _source_book(source) if source is not None else None
    lines = [f"{stated.title} ({stated.report_id})"]
    lines.extend(plain_lines(stated))
    lines.append(stated.detail)
    if report_green(stated, book):
        lines.append(
            "This report stands complete - it walked the question "
            "sequence in the open from reached to reported, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This report stands open - it stands named in "
            f"its gaps: {', '.join(report_gaps(stated, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    stated = _check_view_ref(view)
    return (
        f"View {stated.view_id}: filter {stated.view_filter} - "
        f"{stated.detail}")


def format_note(record_in: Any) -> str:
    stated = _check_note_ref(record_in)
    lines = [
        f"Report note {stated.stance} {stated.report_id} "
        f"({stated.note_id}): {stated.title}. {stated.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_check(source: Any, check: Any) -> str:
    report = report_for_check(source, check)
    if report is not None:
        return format_report(report, source)
    wanted = check.strip() if isinstance(check, str) else check
    return (
        f"No held report stands under check {wanted!r} yet - the "
        f"check reaches nothing in this book, and no report is "
        f"invented for it.")


def format_book(source: Any = None, boundary_id: Any = None) -> str:
    book = _source_book(source)
    reports = (reports_for_boundary(book, boundary_id)
              if boundary_id is not None else book.reports)
    lines = [f"The Report Gate (M-220) - {book.title}"]
    lines.extend(segment_of(report, book) for report in reports)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Report panel under view {panel.view_id}:"]
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
    lines = ["Report index, derived from the held reports:"]
    for entry in index.entries:
        lines.append(f"{entry.check} - {entry.title} ({entry.report_id})")
    if index.gaps:
        lines.append(
            "Red, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_report_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Report Gate (M-220)",
        f"{book.title}: {len(book.reports)} reports held, "
        f"{len(green_reports(book))} reports standing green, "
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


def parse_report_args(args: Any) -> Tuple[str, Any]:
    """Parse the /report grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("report", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("check", "boundary"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
