"""Resumes (roadmap slice M-219).

Part IX - The Mythic Method Engine. The roadmap
words: **a campaign paused mid-slice resumes from journal + map with the situation restated in plain words before work continues.*

What already ships, and what this slice adds:

* The resumes book already ships as data
  (M-201, ``core/resumes.py``): a roadmap/resume
  file (parts, slices, acceptance checks, state) the
  app reads. This slice WIRES the daybook that book's
  daybook invites - several resumes held across
  pauses with one journal over them - as data, in its
  own module, standing in the M-195 copy-and-share
  book daybook the M-219 book stands in: one resumekeeper
  per daybook, and the resumekeeper's charge over one
  resume across its pause held as a book - a
  resume. The shipped resumes stand untouched behind
  their seams: this layer holds resumes as data
  over the daybook's pauses and rewrites none of them,
  and the resumes book keeps its own standing.
  Resumes stand on the journal AS DATA alone: a
  resume carries a journal ref, a reference held in
  this book; holding, viewing or telling a resume
  runs no resume live, moves no keeper and files
  nothing.
* No charter row names this slice: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-219 on no row, and the
  slice tests pin that absence live. The M-005
  method charter names no slice row either: its
  own words name the whole of Part IX as the
  part that executes the charter, and this slice
  is built to the roadmap words and that
  execution note together.

* A resume is held whole: the slice it
  answers for, named by its slice id; its title;
  the resume steps it walked, held as data in
  walk order; and the evidence it carries, held
  as data by pause. The resume walk is EXPLICIT:
  its sequence stands as data
  (:data:`CHECKS`, :data:`TRANSITIONS`) -
  paused, journalled, mapped, restated, resumed -
  and a resume's standing is DERIVED at
  call time from its held steps and evidence
  alone: a resume that opens anywhere but
  paused, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet reached resumed stands
  open, named in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - pause_ref,
  journal_ref, keeper_record, resume_ref, evidence
  a resumekeeper can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A resume is
  restated from held evidence alone, never
  from a feeling: a resume holding a
  bare claim stands open, named in its gaps.
* A resume stands only for an ACTIVE
  slice. The book holds each slice it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  resume naming a slice that stands
  nowhere in the book refuses BY NAME, and a
  resume for a slice that is not active
  refuses BY NAME beside it: the resumekeeper deals with
  the slice in hand, in roadmap order, never a
  queued one, and a slice whose resume already
  stands complete is never mapped twice - the
  current resume is derived, so a
  completed slice is never the current resume
  twice.
* The resume's trace is visible. A trace
  record holds one resume's walked steps
  as one trace line, exactly as walked, beside
  the resume. The derived trace is
  computed at call time from the resume's
  held steps; a held trace that no longer agrees
  with it stands stale, named in the journal - the
  trace is the walk itself, never a retelling
  of it.
* The resume index is DERIVED at call
  time from the held resumes - one entry
  per complete resume, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, order or current-resume
  claim on any record refuses by name.
* The current resume is DERIVED at call
  time - the first held resume, in held
  order, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its resume, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per resume stance; holding
  a note posts none of it, the rule stands as
  data (:data:`RESUME_RULE`), and a record
  claiming a resume was actually resumed,
  captured or promoted live refuses BY NAME.
  The resumekeeper reports - and those reports, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the daybook a real resume
  file takes, a loader reads a file anywhere on
  disk, resumes and views are journalled as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a resume book for a session and
  telling from it. This layer reaches no live
  resume: it writes no resume live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no resumekeeper, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds resumes
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The resume walk is explicit.** A
  resume is restated against the held
  steps and legal steps alone; an illegal step
  stands named in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  resume that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, named in its gaps:
  a resume is restated from evidence, not
  vibes.
* **Active slices only, in roadmap order.** A
  resume for a missing or queued slice
  refuses by name; no resume is invented
  for a slice the resumekeeper has not dealt with.
* **Unknown stays unknown.** A resume
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, order
  and current resume are derived, never
  stored.** Each is derived from the held
  resumes at call time; a stored one
  refuses by name, so it can never drift.
* **One resume per resume.** Two
  resumes standing for one resume id
  refuse by name, and one note record stands per
  resume stance.
* **The notes are data alone.** The records
  hold the feedback; holding, viewing or telling
  them writes nothing, files nothing and posts
  nothing.
"""


from __future__ import annotations

__all__ = [
    "CHECK_FIELDS",
    "CHECKS",
    "CLAIM_PAUSES",
    "HELD_EVIDENCE",
    "BARE_CLAIMS",
    "TRANSITIONS",
    "EXAMPLE_CHECK",
    "STANCES",
    "INDEX_ACTION",
    "RESUME_RESOURCE",
    "RESUME_SCHEMA",
    "RESUME_SLICE",
    "RESUME_RULE",
    "PLAIN_EXPLANATION",
    "THE_RESUME_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "COMPLETE_WORDS",
    "PAUSE_STATES",
    "Any",
    "Dict",
    "List",
    "Optional",
    "TraceRecord",
    "ResumeRecord",
    "IndexEntry",
    "PauseRef",
    "NoteRecord",
    "ResumeBook",
    "ResumeIndex",
    "ResumePanel",
    "ResumePanelRow",
    "ResumeRegistry",
    "ResumeVerdict",
    "ResumeView",
    "TargetCount",
    "trace_for_resume",
    "trace_record",
    "journal_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_resume",
    "build_pause_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_resume",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "resume_for_check",
    "resume_order",
    "resume_record",
    "first_note",
    "format_book",
    "format_resume",
    "format_index",
    "format_note",
    "format_check",
    "format_panel",
    "format_resume_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "pause_record",
    "load_resume",
    "load_resume_file",
    "normalize_pause_state",
    "normalize_check",
    "normalize_claim_pause",
    "legal_step",
    "next_check",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_resume",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_resume_args",
    "green_resumes",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_resumes",
    "validate_trace",
    "validate_book",
    "validate_resume",
    "validate_pause_ref",
    "validate_note",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
    "resume_gaps",
    "resume_green",
    "resumes_for_pause",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

RESUME_SCHEMA = "mythic.interrupts_resumes/1"
RESUME_SLICE = "M-219"
THE_RESUME_SLICE = RESUME_SLICE
RESUME_RESOURCE = "interrupts_resumes.yaml"
INDEX_ACTION = "index"
EXAMPLE_CHECK = "resumed"
CHECK_FIELDS = ("checks", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("resumed", "held", "blocked")
PAUSE_STATES = ("live", "dormant")
RESUME_RULE = 'resumes are held as data alone: several resumes across pauses stand with one journal, keepers per resume, and the human sees the whole forge at a run - a run stands as data, held by reference (a run ref), never taken live - the resume walk stands as an explicit resume sequence - paused, journalled, mapped, restated, resumed - and a resume completes only complete, complete being a state with evidence held - pause ref, journal ref, keeper record, run ref - never a feeling, a memory, an assertion or a summary; holding, viewing and reading a resume runs no resume live, approves nothing, spawns no process and opens no network'
PLAIN_EXPLANATION = "Interrupts and resumes across days (M-219): a campaign paused mid-slice resumes from journal + map with the situation restated in plain words before work continues."
USAGE = 'Usage: /resumes | /resumes resume <resume-id> | /resumes check <check> | /resumes pause <pause-id> | /resumes view <view-id> | /resumes note <note-id> | /resumes index | /resumes panel | /resumes verdict'

CHECKS = ("paused", "journalled", "mapped", "restated", "resumed")
HELD_EVIDENCE = ("pause_ref", "journal_ref", "keeper_record", "resume_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_PAUSES = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "paused": ("journalled",),
    "journalled": ("mapped",),
    "mapped": ("restated",),
    "restated": ("paused", "resumed"),
    "resumed": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a failure or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a resume stands complete.
    A check outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_check(check: Any, failed: Any = False) -> Optional[str]:
    """The step the resumekeeper takes next, DERIVED from the sequence.

    Banked leads to journalled and journalled to
    mapped; mapped leads to restated; at
    restated a follow-up banking steps back to paused and a finished resume steps to resumed;
    resumed is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    restated = normalize_check(check)
    if restated == "paused":
        return "journalled"
    if restated == "journalled":
        return "mapped"
    if restated == "mapped":
        return "restated"
    if restated == "restated":
        return "paused" if failed else "resumed"
    return None


_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "resume_id", "seq", "pause_id", "title", "checks",
    "claims", "detail",
} | set(_PROVENANCE))
_SLICE_REF_KEYS = frozenset({
    "pause_id", "seq", "title", "state", "detail",
} | set(_PROVENANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "resume_id", "trace", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "resume_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered",
    "current_resume", "next_resume", "progress", "journal",
    "current", "order", "breaks", "live"})
_LIVE_KEYS = (
    "live_resume", "resumes_live", "live_question",
    "resumes_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "resumes_live",
    "resumed_live", "pauses_resume", "paused_live",
    "runs_resume", "ran_resume", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "resume_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_resume", "sent_resume",
    "posts_note", "posted_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_resume", "filed_live", "spawns_resumekeeper", "spawned_resumekeeper", "sends_resume", "sent_resume", "writes_resume", "wrote_resume")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_checks(value: Any) -> Tuple[str, ...]:
    """A resume's walked checks, held as data.

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
    """A resume's asked claims: claim pauses named as data.

    Each claim names one pause from the resumed
    vocabulary - the human pauses the gate may ask
    and the code pauses it must never ask, both
    held honestly as data - and a pause outside
    the vocabulary refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("claims must be a list of claim pauses")
    return tuple(normalize_claim_pause(v) for v in value)

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
                f"{what} claims a live gate resume or slice build "
                f"execution ({key!r} is named on it): "
                f"{RESUME_RULE}")
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


def normalize_pause_state(value: Any) -> str:
    state = _clean_text(value, "an slice state").lower()
    if state not in PAUSE_STATES:
        raise ValueError(
            f"slice state {state!r} is not one of the held "
            f"states: " + ", ".join(PAUSE_STATES))
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


def normalize_claim_pause(value: Any) -> str:
    pause = _clean_text(value, "a claim pause").lower()
    if pause not in CLAIM_PAUSES:
        raise ValueError(
            f"claim pause {pause!r} is not one of the held "
            f"pauses: " + ", ".join(CLAIM_PAUSES))
    return pause

# ---------------------------------------------------------------------
# The held resume: one slice cut from an active slice.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ResumeRecord:
    """One resume slice, held as data.

    The resume names the active slice it was
    held from, by slice id, its title, its
    verifiable checks, held as data, and its
    claims, named by resume id. The grain is
    derived, never stored: exactly one verifiable
    walk is mapped against the machine. A resume whose
    checks are not yet held stands with its
    checks empty: it stands open, named in
    its gaps, and no check is invented for it.
    The resume is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    resume_id: str
    seq: int
    pause_id: str
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
            self, "resume_id", _clean_text(self.resume_id, "a resume id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "pause_id", _clean_text(self.pause_id, "an slice id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a resume title"))
        object.__setattr__(
            self, "checks", _check_checks(self.checks))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a resume detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.resume_id

    @property
    def check(self) -> str:
        """The check the resume stands at: its last walked check."""
        return self.checks[-1] if self.checks else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "resume_id": self.resume_id, "seq": self.seq,
            "pause_id": self.pause_id, "title": self.title,
            "checks": list(self.checks),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_resume_ref(value: Any) -> ResumeRecord:
    if not isinstance(value, ResumeRecord):
        raise ValueError("a resume must be a ResumeRecord")
    return value


def validate_resume(resume: Any) -> ResumeRecord:
    return _check_resume_ref(resume)


def build_resume(record: Any = None, **kwargs: Any) -> ResumeRecord:
    """Build one held resume from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, ResumeRecord):
        if kwargs:
            raise ValueError("a resume stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a resume must be a mapping or a ResumeRecord")
    _needed(data, _RUN_KEYS, "a resume")
    return ResumeRecord(
        resume_id=data.get("resume_id"), seq=data.get("seq"),
        pause_id=data.get("pause_id"), title=data.get("title"),
        checks=data.get("checks"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_provenance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each resume to the steps it took outside the machine.

    Derived from the held resumes alone: a break is
    one consecutive pair of walked checks the
    explicit gate sequence does not allow, told
    in walk order as before, then after.
    """
    found: Dict[str, Tuple[str, ...]] = {}
    for resume in book.resumes:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(resume.checks, resume.checks[1:])
            if not legal_step(before, after))
        if breaks:
            found[resume.resume_id] = breaks
    return found

def resume_gaps(resume: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a resume from standing complete.

    Mapped from the resume's own held fields alone -
    its walked steps against the explicit question
    sequence, and its carried evidence against the
    resumed vocabulary: the resume opens at
    named, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a resume stands complete only when it has
    reached resumed. The source names nothing
    further: no gap is borrowed from another
    resume.
    """
    restated = _check_resume_ref(resume)
    gaps: List[str] = []
    if not restated.checks:
        gaps.append(
            "has passed through no step: the resume has not started")
        return tuple(gaps)
    if restated.checks[0] != "paused":
        gaps.append(
            f"opens at {restated.checks[0]}, not at paused: "
            f"the resume opens with the reflection")
    for before, after in zip(restated.checks, restated.checks[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"resume sequence does not allow")
    for pause in restated.claims:
        if pause in BARE_CLAIMS:
            gaps.append(
                f"carries a {pause} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if restated.checks[-1] != "resumed":
        gaps.append(
            f"has not reached resumed: the resume stands "
            f"at {restated.checks[-1]}")
    return tuple(gaps)

def resume_green(resume: Any, source: Any = None) -> bool:
    return not resume_gaps(resume, source)


def plain_lines(resume: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the resume's own fields."""
    restated = _check_resume_ref(resume)
    return (
        f"Resume: {restated.title}",
        f"Pause: {restated.pause_id}",
        f"Check: {restated.check if restated.check else 'none'}",
        f"Claims: "
        f"{', '.join(restated.claims) if restated.claims else 'none'}",
    )


def segment_of(resume: Any, source: Any = None) -> str:
    restated = _check_resume_ref(resume)
    gaps = resume_gaps(restated, source)
    return (
        f"{restated.resume_id}: {restated.title} - slice: "
        f"'{restated.pause_id}' - check: "
        f"'{restated.check if restated.check else 'none'}' - "
        f"checks: {len(restated.checks)} - claims: "
        f"'{', '.join(restated.claims) if restated.claims else 'none'}' - "
        f"detail: '{restated.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held slice reference: the active slice a book resumes from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class PauseRef:
    """One slice a resume book resumes from, held as a reference.

    The record names the slice, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 slice book's own telling. A resume
    stands only from an active reference: the
    book refuses a resume naming no held reference,
    and a resume from an queued one, BY NAME.
    """

    pause_id: str
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
            self, "pause_id", _clean_text(self.pause_id, "an slice id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(
            self, "state", normalize_pause_state(self.state))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an slice detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.pause_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "pause_id": self.pause_id, "seq": self.seq,
            "title": self.title, "state": self.state,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_pause_ref(value: Any) -> PauseRef:
    if not isinstance(value, PauseRef):
        raise ValueError("a slice reference must be an PauseRef")
    return value


def validate_pause_ref(ref: Any) -> PauseRef:
    return _check_pause_ref(ref)


def build_pause_ref(record: Any = None, **kwargs: Any) -> PauseRef:
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, PauseRef):
        if kwargs:
            raise ValueError(
                "a slice reference stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError(
            "a slice reference must be a mapping or an PauseRef")
    _needed(data, _SLICE_REF_KEYS, "a slice reference")
    return PauseRef(
        pause_id=data.get("pause_id"), seq=data.get("seq"),
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
    human active - the slice's resume ids in
    derived claim order, held exactly as
    active. The trace is of the set and its
    order, never of a step: when the derived
    trace moves, this record stands stale, named
    in the journal, until a new trace is active.
    """

    trace_id: str
    seq: int
    resume_id: str
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
            self, "resume_id", _clean_text(self.resume_id, "an slice id"))
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
            "resume_id": self.resume_id, "trace": self.trace,
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
        resume_id=data.get("resume_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a resume, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One resume stance, held as data.

    The record names its resume, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per resume stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    resume_id: str
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
            self, "resume_id", _clean_text(self.resume_id, "a resume id"))
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
            "resume_id": self.resume_id, "stance": self.stance,
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
        resume_id=data.get("resume_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which slices a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ResumeView:
    """A view over the book: every resume, the green, the rest."""

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


def _check_view_ref(value: Any) -> ResumeView:
    if not isinstance(value, ResumeView):
        raise ValueError("a view must be an ResumeView")
    return value


def validate_view(view: Any) -> ResumeView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> ResumeView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, ResumeView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an ResumeView")
    _needed(data, _VIEW_KEYS, "a view")
    return ResumeView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ResumePanelRow:
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


def _row_for_resume(resume: ResumeRecord,
                     source: Any = None) -> ResumePanelRow:
    return ResumePanelRow(
        item_id=resume.resume_id,
        standing="complete" if resume_green(resume, source) else "open",
        label=resume.title, segment=segment_of(resume, source),
        recorded_on=resume.recorded_on)


def _check_row_ref(value: Any) -> ResumePanelRow:
    if not isinstance(value, ResumePanelRow):
        raise ValueError("a panel row must be an ResumePanelRow")
    return value


def validate_row(row: Any, resume: Any = None,
                 source: Any = None) -> ResumePanelRow:
    restated = _check_row_ref(row)
    if resume is not None:
        derived = _row_for_resume(_check_resume_ref(resume), source)
        if restated != derived:
            raise ValueError(
                f"panel row {restated.item_id!r} does not agree with "
                f"the row derived from its resume")
    return restated


def build_row(row: Any = None, resume: Any = None,
              source: Any = None,
              **kwargs: Any) -> ResumePanelRow:
    if resume is not None:
        derived = _row_for_resume(_check_resume_ref(resume), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            ResumePanelRow(**kwargs))
        return validate_row(built, resume, source)
    if isinstance(row, ResumePanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return ResumePanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return ResumePanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an ResumePanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[ResumePanelRow, ...]
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
        f"The resume book holds {total_items} resumes as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown resumes "
        f"stand complete.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its resume's own fields "
        "- the slice it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any resume.",
        "Completeness is mapped from the held records alone: "
        "a resume that steps outside the resume sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not reached resumed stands open, named in its "
        "gaps, and the resume index is derived from the "
        "held resumes, never stored where it could drift.",
    )

@dataclass(frozen=True)
class ResumePanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[ResumePanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> ResumeView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, ResumeView):
        return view
    return book.view_for(view)


def shown_resumes(source: Any, view: Any = None
                   ) -> Tuple[ResumeRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.resumes
    if resolved.view_filter == "complete":
        return tuple(g for g in book.resumes if resume_green(g, book))
    return tuple(g for g in book.resumes if not resume_green(g, book))


def resumes_for_pause(source: Any, pause_id: Any
                      ) -> Tuple[ResumeRecord, ...]:
    wanted = _clean_text(pause_id, "an slice id")
    return tuple(
        g for g in _source_book(source).resumes if g.pause_id == wanted)


def green_resumes(source: Any) -> Tuple[ResumeRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.resumes if resume_green(g, book))


def current_resume(source: Any) -> Optional[ResumeRecord]:
    """The book's current resume, DERIVED at call time.

    The first held resume, in held order, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held resumes alone, so it can
    never go stale against them. A book whose every
    resume stands complete has no current resume.
    """
    book = _source_book(source)
    for resume in book.resumes:
        if not resume_green(resume, book):
            return resume
    return None


def derive_panel(source: Any, view: Any = None) -> ResumePanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_resumes(book, resolved)
    rows = tuple(_row_for_resume(resume, book) for resume in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.resumes), default="")
    green = sum(1 for g in shown if resume_green(g, book))
    return ResumePanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.resumes), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.resumes), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> ResumePanel:
    if not isinstance(value, ResumePanel):
        raise ValueError("a panel must be an ResumePanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> ResumePanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 resume).
    """
    restated = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(restated.view_id)
                if restated.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(restated, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {restated.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return restated


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> ResumePanel:
    if isinstance(panel, ResumePanel):
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
        built = ResumePanel(
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
    raise ValueError("a panel must be a mapping, an ResumePanel, or derived")


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
        return "resumed"
    if green_shown == 0:
        return "blocked"
    return "held"


@dataclass(frozen=True)
class ResumeVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> ResumeVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_resumes(book, resolved)
    green = sum(1 for g in shown if resume_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return ResumeVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> ResumeVerdict:
    if not isinstance(value, ResumeVerdict):
        raise ValueError("a verdict must be an ResumeVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> ResumeVerdict:
    restated = _check_verdict_ref(verdict)
    if restated.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {restated.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(restated.view_id)
                if restated.view_id is not None else None)
        derived = derive_verdict(book, view)
        if restated != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return restated


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> ResumeVerdict:
    if isinstance(verdict, ResumeVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = ResumeVerdict(
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
        "a verdict must be a mapping, an ResumeVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held slices' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    check: str
    resume_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "check": self.check, "resume_id": self.resume_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class ResumeIndex:
    """The resume index, derived from the held resumes.

    The index names one entry per green resume, in
    held order - the resume's own one verifiable
    check, its resume id and its title - and the
    resumes that do not stand complete, named in its
    gaps. Nothing here is stored on any resume: the
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


def derive_index(source: Any) -> ResumeIndex:
    """Derive the resume index from the book's held resumes."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(check=g.check, resume_id=g.resume_id,
                   title=g.title)
        for g in book.resumes if resume_green(g, book))
    gaps = tuple(
        g.resume_id for g in book.resumes if not resume_green(g, book))
    return ResumeIndex(entries=entries, gaps=gaps)


def resume_for_check(source: Any, check: Any) -> Optional[ResumeRecord]:
    """The first held resume one check reaches, or none - honestly."""
    if check is None:
        return None
    if not isinstance(check, str):
        raise ValueError("an check must be a string naming the check")
    wanted = check.strip()
    if not wanted:
        return None
    for resume in _source_book(source).resumes:
        if resume.check == wanted:
            return resume
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held order: the resume
    that took it and the step it took, before,
    then after. A book whose resumes all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{resume_id}: {step}"
        for resume_id, steps in _breaks_map(book).items()
        for step in steps)

def resume_order(source: Any,
              pause_id: Any = None) -> Tuple[ResumeRecord, ...]:
    """The held resumes in their held order, DERIVED at call time.

    Resumes stand in the order the book holds them -
    the order their slices were taken - optionally
    for one slice alone. Nothing here is stored:
    the order is the book's own held order, told.
    """
    book = _source_book(source)
    resumes = list(book.resumes)
    if pause_id is not None:
        wanted = _clean_text(pause_id, "a slice id")
        resumes = [r for r in resumes if r.pause_id == wanted]
    return tuple(resumes)

def trace_of(source: Any, resume_id: Any) -> str:
    """One resume's trace, DERIVED at call time.

    The resume's walked checks joined as one trace
    line, in walk order. A resume that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is named
    elsewhere.
    """
    resume = _source_book(source).resume_for(resume_id)
    return " > ".join(resume.checks)

def trace_for_resume(source: Any,
                  resume_id: Any) -> Optional[TraceRecord]:
    """The held trace for one resume, or none - honestly."""
    wanted = _clean_text(resume_id, "a resume id")
    for record in _source_book(source).traces:
        if record.resume_id == wanted:
            return record
    return None

def trace_current(source: Any, resume_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_resume(source, resume_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, resume_id)

def note_for_resume(source: Any, resume_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one resume (and stance, when named)."""
    wanted = _clean_text(resume_id, "a resume id")
    for record in _source_book(source).notes:
        if record.resume_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the slice targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def journal_record(source: Any = None) -> Dict[str, Any]:
    """The resume journal, DERIVED here from the held resumes alone.

    The journal counts the held resumes by their
    derived completeness - green and red - names
    the current resume, the first that does not yet
    stand complete, tells each held resume's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held resumes took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.resumes
            if ("complete" if resume_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "resume_records": number})
    current = current_resume(book)
    traces = []
    for resume in book.resumes:
        trace = trace_for_resume(book, resume.resume_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, resume.resume_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"resume_id": resume.resume_id, "trace": standing})
    return {
        "type": "resume_well",
        "slice": RESUME_SLICE,
        "standings": standings,
        "total": len(book.resumes),
        "current_resume": current.resume_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This slice's own roadmap standing, proved from the roadmap itself.

    The record loads this pause's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 slices in 11 parts,
    the paused prefix, the next slice where the
    resume resumes, and M-219's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(RESUME_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "resume_roadmap",
        "slice": RESUME_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m219_title": own.title,
        "m219_part": own.part,
        "m219_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: slices, resumes, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or order ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ResumeBook:
    title: str
    slices: Tuple[PauseRef, ...] = ()
    resumes: Tuple[ResumeRecord, ...] = ()
    views: Tuple[ResumeView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[ResumePanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        slices = tuple(_check_pause_ref(g) for g in self.slices)
        resumes = tuple(_check_resume_ref(g) for g in self.resumes)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        traces = tuple(_check_trace_ref(a) for a in self.traces)
        panels = tuple(_check_panel_ref(pn) for pn in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for ref in slices:
            if ref.pause_id in seen_ids:
                raise ValueError(
                    f"two slice references stand under id {ref.pause_id!r}")
            if ref.seq in seen_seqs:
                raise ValueError(
                    f"two slice references stand at sequence {ref.seq}")
            seen_ids.add(ref.pause_id)
            seen_seqs.add(ref.seq)
        resume_ids = set()
        resume_seqs = set()
        for resume in resumes:
            if resume.resume_id in resume_ids:
                raise ValueError(
                    f"two resumes stand under id {resume.resume_id!r}")
            if resume.seq in resume_seqs:
                raise ValueError(
                    f"two resumes stand at sequence {resume.seq}")
            resume_ids.add(resume.resume_id)
            resume_seqs.add(resume.seq)
        by_slice = {ref.pause_id: ref for ref in slices}
        for resume in (resumes if slices else ()):

            ref = by_slice.get(resume.pause_id)
            if ref is None:
                raise ValueError(
                    f"resume {resume.resume_id!r} is held from slice "
                    f"{resume.pause_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "live":
                raise ValueError(
                    f"resume {resume.resume_id!r} is held from slice "
                    f"{resume.pause_id!r}, which is not active: "
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
            target = (record.resume_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for resume "
                    f"{record.resume_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per resume target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_resumes = set()
        resume_ids = {resume.resume_id for resume in resumes}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.resume_id in trace_resumes:
                raise ValueError(
                    f"two traces stand for resume "
                    f"{record.resume_id!r}: one trace stands "
                    f"per resume walk")
            if resumes and record.resume_id not in resume_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces resume "
                    f"{record.resume_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_resumes.add(record.resume_id)
        object.__setattr__(
            self, "pauses", tuple(sorted(slices, key=lambda g: g.seq)))
        object.__setattr__(
            self, "resume_records", tuple(sorted(resumes, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.resumes + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.resume_id for g in self.resumes) + tuple(
            v.view_id for v in self.views)

    def resume_ids(self) -> Tuple[str, ...]:
        return tuple(g.resume_id for g in self.resumes)

    def pause_ids(self) -> Tuple[str, ...]:
        return tuple(g.pause_id for g in self.slices)

    def resume_for(self, resume_id: Any) -> ResumeRecord:
        wanted = _clean_text(resume_id, "a resume id")
        for resume in self.resumes:
            if resume.resume_id == wanted:
                return resume
        raise KeyError(f"no resume named {wanted!r} stands in this book")

    def slice_for(self, pause_id: Any) -> PauseRef:
        wanted = _clean_text(pause_id, "an slice id")
        for ref in self.slices:
            if ref.pause_id == wanted:
                return ref
        raise KeyError(f"no slice named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> ResumeView:
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
        for resume in self.resumes:
            if resume.resume_id == wanted:
                return resume
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "pauses": [g.to_record() for g in self.slices],
            "resume_records": [g.to_record() for g in self.resumes],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: ResumeBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: ResumeBook) -> None:
    if book.title != "Interrupts and resumes across days at the M-219 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.slices) != 3 or len(book.resumes) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three slice references, five resumes and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m218-boundary":
        raise ValueError("the pinned panel is panel-m218-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.check for e in index.entries] != ["resumed", "resumed", "resumed"]:
        raise ValueError("the shipped example book index must derive the three held complete resumes in held order")
    if index.gaps != ("resume-bare-resume", "resume-leaping-resume"):
        raise ValueError("the shipped example book must leave the bare and leaping resumes honestly open, named in its gaps")
    found = resume_for_check(book, EXAMPLE_CHECK)
    if found is None or found.resume_id != "resume-held-resume":
        raise ValueError("the shipped example book must reach its opening resume under the example check")
    if trace_of(book, "resume-held-resume") != "paused > journalled > mapped > restated > resumed":
        raise ValueError("the shipped example book must derive the opening resume's trace from its walked steps")
    if not trace_current(book, "resume-held-resume"):
        raise ValueError("the shipped example book must hold the opening resume's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note resume")

def validate_book(data: Any, *, require_example: bool = False) -> ResumeBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, ResumeBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a resume book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live slice build or execution "
                f"({key!r} is named on it): {RESUME_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its resumes under a view")
    if "resume_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held resumes at call time")
    if "journal" in data or "current_resume" in data:
        raise ValueError(
            "a book stores no journal and no current resume: both are "
            "derived from its held resumes at call time")
    if "trace" in data or "order" in data:
        raise ValueError(
            "a book stores no trace and no order: both are derived "
            "from its held resumes at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != RESUME_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{RESUME_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != RESUME_SLICE):
        raise ValueError(
            f"a book's slice must be {RESUME_SLICE!r}")
    head = data.get("resume_head") or data.get("interrupts_resumes") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's resume head must be a mapping")
    title = head.get("title") or data.get("title")
    slices = tuple(build_pause_ref(g) for g in data.get("pauses") or ())
    resumes = tuple(build_resume(g) for g in data.get("resume_records") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = ResumeBook(
        title=title, slices=slices, resumes=resumes, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = ResumeBook(
        title=book.title, slices=book.slices, resumes=book.resumes,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> ResumeBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (ResumeBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an ResumeBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> ResumeBook:
    return validate_book(data, require_example=require_example)


def load_resume(
        data: Optional[Dict[str, Any]] = None) -> ResumeBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(RESUME_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_resume_file(path: Any) -> ResumeBook:
    """Load one resume file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: slice references, resumes and views held one by one.
# ---------------------------------------------------------------------

class ResumeRegistry:
    """An in-memory holding of slice references, resumes and views.

    The registry is the pure layer's model of a
    session's resume book: slice references are
    held under their ids, resumes are held under
    their ids, one resume per id and per sequence,
    and views are held in journalled order, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[PauseRef] = []
        self._resumes: List[ResumeRecord] = []
        self._views: List[ResumeView] = []
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

    def register_pause_ref(self, item: Any) -> PauseRef:
        """Hold one slice reference, mapped whole before held."""
        restated = _check_pause_ref(item)
        return self._register(
            self._slices, restated, "pause_id", "slice reference")

    def register_resume(self, item: Any) -> ResumeRecord:
        """Hold one resume, mapped whole before held."""
        restated = _check_resume_ref(item)
        return self._register(
            self._resumes, restated, "resume_id", "resume")

    def register_view(self, view: Any) -> ResumeView:
        """Hold one view; a view naming no id takes a fresh one."""
        restated = _check_view_ref(view)
        if not restated.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            restated = build_view({**restated.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, restated, "view_id", "view")

    def register_book(self, book: Any) -> ResumeBook:
        """Hold a whole book's records, under its title."""
        restated = build_book(book)
        if self._title is not None and restated.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {restated.title!r}")
        for ref in restated.slices:
            self.register_pause_ref(ref)
        for resume in restated.resumes:
            self.register_resume(resume)
        for view in restated.views:
            self.register_view(view)
        self._title = restated.title
        return self.book()

    def book(self) -> ResumeBook:
        return ResumeBook(
            title=self._title or "An unheld resume book",
            slices=tuple(self._slices), resumes=tuple(self._resumes),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[PauseRef, ...]:
        return tuple(self._slices)

    def list_resumes(self) -> Tuple[ResumeRecord, ...]:
        return tuple(self._resumes)

    def list_views(self) -> Tuple[ResumeView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._resumes) + tuple(self._views)

    def get_slice(self, pause_id: Any) -> PauseRef:
        return self.book().slice_for(pause_id)

    def get_resume(self, resume_id: Any) -> ResumeRecord:
        return self.book().resume_for(resume_id)

    def get_view(self, view_id: Any) -> ResumeView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the journal target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> ResumeBook:
    if source is None:
        return load_resume()
    if isinstance(source, ResumeBook):
        return source
    if isinstance(source, ResumeRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def resume_record(resume: Any, source: Any = None) -> Dict[str, Any]:
    restated = _check_resume_ref(resume)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "resume_resume",
        "slice": RESUME_SLICE,
        "resume_id": restated.resume_id,
        "pause_id": restated.pause_id,
        "title": restated.title,
        "segment": segment_of(restated, book),
        "complete": resume_green(restated, book),
        "gaps": list(resume_gaps(restated, book)),
    }
    record.update(_provenance_record(restated))
    return record


def pause_record(ref: Any) -> Dict[str, Any]:
    restated = _check_pause_ref(ref)
    record = {
        "type": "resume_slice",
        "slice": RESUME_SLICE,
        "pause_id": restated.pause_id,
        "title": restated.title,
        "state": restated.state,
    }
    record.update(_provenance_record(restated))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    restated = _check_trace_ref(record_in)
    record = {
        "type": "resume_trace",
        "slice": RESUME_SLICE,
        "trace_id": restated.trace_id,
        "resume_id": restated.resume_id,
        "trace": restated.trace,
    }
    record.update(_provenance_record(restated))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    restated = _check_view_ref(view)
    record = {
        "type": "resume_view",
        "slice": RESUME_SLICE,
        "view_id": restated.view_id, "seq": restated.seq,
        "view_filter": restated.view_filter,
    }
    record.update(_provenance_record(restated))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    restated = _check_note_ref(record_in)
    record = {
        "type": "resume_note",
        "slice": RESUME_SLICE,
        "note_id": restated.note_id,
        "resume_id": restated.resume_id,
        "stance": restated.stance,
    }
    record.update(_provenance_record(restated))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    restated = validate_panel(panel, source)
    record = {"type": "resume_panel",
              "slice": RESUME_SLICE}
    record.update(restated.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, ResumeVerdict):
        restated = validate_verdict(verdict, source)
    else:
        restated = derive_verdict(_source_book(verdict), view)
    record = {"type": "resume_verdict",
              "slice": RESUME_SLICE}
    record.update(restated.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, ResumeIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "resume_index",
              "slice": RESUME_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    restated = _source_book(book)
    record = {"type": "resume_book",
              "slice": RESUME_SLICE,
              "title": restated.title}
    record.update(restated.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(resume: Any, source: Any = None) -> str:
    restated = _check_resume_ref(resume)
    return (
        f"{restated.title} - from {restated.pause_id}: "
        f"check {restated.check if restated.check else 'none'}, "
        f"claims "
        f"{', '.join(restated.claims) if restated.claims else 'none'}. "
        f"{restated.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The resumes stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"resumes stand complete.")


def view_plain_words(view: Any) -> str:
    restated = _check_view_ref(view)
    return f"View {restated.view_id}: shows {restated.view_filter} resumes."


def note_plain_words(record_in: Any) -> str:
    restated = _check_note_ref(record_in)
    return (
        f"Note {restated.note_id}: {restated.stance} "
        f"{restated.resume_id}, toward {restated.target}. "
        f"{restated.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, ResumeIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} green resumes; "
        f"red, named in its gaps: {gaps}.")

def format_resume(resume: Any, source: Any = None) -> str:
    restated = _check_resume_ref(resume)
    book = _source_book(source) if source is not None else None
    lines = [f"{restated.title} ({restated.resume_id})"]
    lines.extend(plain_lines(restated))
    lines.append(restated.detail)
    if resume_green(restated, book):
        lines.append(
            "This resume stands complete - it walked the question "
            "sequence in the open from paused to resumed, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This resume stands open - it stands named in "
            f"its gaps: {', '.join(resume_gaps(restated, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    restated = _check_view_ref(view)
    return (
        f"View {restated.view_id}: filter {restated.view_filter} - "
        f"{restated.detail}")


def format_note(record_in: Any) -> str:
    restated = _check_note_ref(record_in)
    lines = [
        f"Resume note {restated.stance} {restated.resume_id} "
        f"({restated.note_id}): {restated.title}. {restated.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_check(source: Any, check: Any) -> str:
    resume = resume_for_check(source, check)
    if resume is not None:
        return format_resume(resume, source)
    wanted = check.strip() if isinstance(check, str) else check
    return (
        f"No held resume stands under check {wanted!r} yet - the "
        f"check reaches nothing in this book, and no resume is "
        f"invented for it.")


def format_book(source: Any = None, pause_id: Any = None) -> str:
    book = _source_book(source)
    resumes = (resumes_for_pause(book, pause_id)
              if pause_id is not None else book.resumes)
    lines = [f"The Resume Gate (M-219) - {book.title}"]
    lines.extend(segment_of(resume, book) for resume in resumes)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Resume panel under view {panel.view_id}:"]
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
    lines = ["Resume index, derived from the held resumes:"]
    for entry in index.entries:
        lines.append(f"{entry.check} - {entry.title} ({entry.resume_id})")
    if index.gaps:
        lines.append(
            "Red, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_resume_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Resume Gate (M-219)",
        f"{book.title}: {len(book.resumes)} resumes held, "
        f"{len(green_resumes(book))} resumes standing green, "
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


def parse_resume_args(args: Any) -> Tuple[str, Any]:
    """Parse the /resume grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("resume", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("check", "pause"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
