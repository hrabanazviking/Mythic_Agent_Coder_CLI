"""The never-leave-a-bug rule (roadmap slice M-212).

Part IX - The Mythic Method Engine. The roadmap
words: *a bug discovered mid-slice is fixed in
scope or commissioned as a new slice on the spot
- the loop has no "note it and move on" state.*

What already ships, and what this slice adds:

* The never-leave-a-bug rule already binds the work in
  prose - when the human asks a question, the
  question is answered first, plainly and fully,
  its first sentence the direct answer itself,
  and only then does work resume - and this
  slice WIRES it into the loop as data, in its
  own module, standing in the M-195 copy-and-
  share book shape the M-211 book stands in: one
  scribe per campaign, and the scribe's
  charge over one named question held as a
  book - a bug. The shipped roads stand
  untouched behind their seams: this layer holds
  bugs as data over the campaign's
  slices and rewrites none of them, and the
  prose law keeps its own standing.

* No charter row names this slice: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-212 on no row, and the
  slice tests pin that absence live. The M-005
  method charter names no slice row either: its
  own words name the whole of Part IX as the
  part that executes the charter, and this slice
  is built to the roadmap words and that
  execution note together. The law itself is
  held as data in the roadmap's own wording -
  the bug names its question and carries
  the answer it was fixed against.

* A bug is held whole: the slice it
  answers for, named by its slice id; its title;
  the question steps it walked, held as data in
  walk order; and the evidence it carries, held
  as data by kind. The question walk is
  EXPLICIT: its sequence stands as data
  (:data:`CHECKS`, :data:`TRANSITIONS`) -
  discovered, triaged, fixed, verified, closed -
  and a bug's standing is DERIVED at
  call time from its held steps and evidence
  alone: a bug that opens anywhere but discovered, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet reached closed
  stands open, named in its gaps. The campaign
  pauses for the question: an answer stands
  complete only where the walk triaged, the
  answer was fixed plain-first - its first
  sentence the direct answer - and the delivery
  is held as evidence.
* The evidence is a closed vocabulary in two
  halves: the held evidence - fix_ref,
  slice_ref, test_record, commission_ref,
  evidence an scribe can point to - and the
  bare claims - feeling, memory, assertion,
  summary, which stand as no evidence at all. An
  answer is fixed from held evidence alone,
  never from a feeling: a bug holding a
  bare claim stands open, named in its gaps.
* A bug stands only for an ACTIVE slice.
  The book holds each slice it answers for as a
  reference record - its id, its title and its
  standing, active or queued, held as data
  copied from the roadmap's own telling. A
  bug naming a slice that stands nowhere
  in the book refuses BY NAME, and a bug
  for a slice that is not active refuses BY NAME
  beside it: the scribe deals with the slice
  in hand, in roadmap order, never a queued one,
  and a slice whose question already stands
  complete is never answered twice - the current
  bug is derived, so a completed slice
  is never the current answering twice.
* The bug's trace is visible. A trace
  record holds one bug's walked steps as
  one trace line, exactly as walked, beside the
  bug. The derived trace is computed at
  call time from the bug's held steps; a
  held trace that no longer agrees with it
  stands stale, named in the board - the trace
  is the walk itself, never a retelling of it.
* The bug index is DERIVED at call time
  from the held bugs - one entry per
  complete bug, under the step it stands
  at - never a second stored copy that could
  drift. A stored index, standing verdict,
  panel, trace, order or current-bug
  claim on any record refuses by name.
* The current bug is DERIVED at call
  time - the first held bug, in held
  order, that does not yet stand complete - never
  stored where it could go stale: that is the
  question the scribe must answer next, and
  the next slice is dealt only when the current
  one resumes.
* The notes are held as data: a note record
  naming its bug, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per bug stance; holding a
  note posts none of it, the rule stands as data
  (:data:`BUG_RULE`), and a record
  claiming a question was actually answered,
  verified or closed live refuses BY NAME.
  The scribe reports - and those reports, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the shape a real answer file takes,
  a loader reads an answer file anywhere on
  disk, bugs and views are shaped as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding an answer book for a session and
  telling from it. This layer reaches no live
  road: it answers no question live, pauses no
  campaign, resumes no work, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security, spawns
  no process and opens no network - it holds
  bugs as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The question walk is explicit.** A
  bug is fixed against the held steps
  and legal steps alone; an illegal step stands
  named in its gaps, never silently reordered.
* **Complete stands on held evidence alone.** A
  bug that carries a feeling, a memory,
  an assertion or a summary in place of held
  evidence stands open, named in its gaps: an
  answer is fixed from evidence, not vibes.
* **Active slices only, in roadmap order.** A
  bug for a missing or queued slice
  refuses by name; no bug is invented
  for a slice the scribe has not dealt with.
* **Unknown stays unknown.** A bug whose
  steps are not yet held stands with its steps
  empty - no step is invented.
* **The index, panel, verdict, trace, order
  and current bug are derived, never
  stored.** Each is derived from the held
  bugs at call time; a stored one
  refuses by name, so it can never drift.
* **One bug per bug.** Two
  bugs standing for one bug id
  refuse by name, and one note record stands per
  bug stance.
* **The notes are data alone.** The records
  hold the feedback; holding, viewing or telling
  them answers nothing, pauses nothing and posts
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
    "BUG_RESOURCE",
    "BUG_SCHEMA",
    "BUG_SLICE",
    "BUG_RULE",
    "PLAIN_EXPLANATION",
    "THE_BUG_SLICE",
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
    "BugRecord",
    "IndexEntry",
    "SliceRef",
    "NoteRecord",
    "BugBook",
    "BugIndex",
    "BugPanel",
    "BugPanelRow",
    "BugRegistry",
    "BugVerdict",
    "BugView",
    "TargetCount",
    "trace_for_bug",
    "trace_record",
    "board_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_bug",
    "build_slice_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_bug",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "bug_for_check",
    "bug_order",
    "bug_record",
    "first_note",
    "format_book",
    "format_bug",
    "format_index",
    "format_note",
    "format_check",
    "format_panel",
    "format_bug_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "slice_record",
    "load_bug",
    "load_bug_file",
    "normalize_slice_state",
    "normalize_check",
    "normalize_claim_kind",
    "legal_step",
    "next_check",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_bug",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_bug_args",
    "green_bugs",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_bugs",
    "validate_trace",
    "validate_book",
    "validate_bug",
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
    "bug_gaps",
    "bug_green",
    "bugs_for_slice",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

BUG_SCHEMA = "mythic.bug_rule/1"
BUG_SLICE = "M-212"
THE_BUG_SLICE = BUG_SLICE
BUG_RESOURCE = "bug_rule.yaml"
INDEX_ACTION = "index"
EXAMPLE_CHECK = "closed"
CHECK_FIELDS = ("checks", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("closed", "held", "blocked")
SLICE_STATES = ("active", "queued")
BUG_RULE = (
    "bugs are held as data alone: a bug "
    "discovered mid-slice is fixed in scope or "
    "commissioned as a new slice on the spot - "
    "the loop has no note-it-and-move-on state - "
    "the bug walk stands as an explicit bug "
    "sequence - discovered, triaged, fixed, "
    "verified, closed - and a fix completes "
    "only complete, complete being a state "
    "with evidence held - slice ref, fix ref, "
    "test record, commission ref - never a "
    "feeling, a memory, an assertion or a "
    "summary; holding, viewing and reading a "
    "bug fixes no bug live, commissions no "
    "slice, files no report and opens no network")
PLAIN_EXPLANATION = (
    "The never-leave-a-bug rule (M-212): a bug "
    "discovered mid-slice is fixed in scope or "
    "commissioned as a new slice on the spot - "
    "the loop has no note-it-and-move-on state.")
USAGE = (
    "Usage: /bugrule | /bugrule bug <bug-id> | "
    "/bugrule check <check> | /bugrule slice <slice-id> | "
    "/bugrule view <view-id> | /bugrule note <note-id> | "
    "/bugrule index | /bugrule panel | /bugrule verdict")

CHECKS = ("discovered", "triaged", "fixed", "verified", "closed")
HELD_EVIDENCE = ("slice_ref", "fix_ref", "test_record", "commission_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "discovered": ("triaged",),
    "triaged": ("fixed",),
    "fixed": ("verified",),
    "verified": ("discovered", "closed"),
    "closed": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a failure or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a bug stands complete.
    A check outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_check(check: Any, failed: Any = False) -> Optional[str]:
    """The step the scribe takes next, DERIVED from the sequence.

    Banked leads to triaged and triaged to
    fixed; fixed leads to verified; at
    verified a follow-up banking steps back to discovered and a finished fix steps to closed;
    closed is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    verified = normalize_check(check)
    if verified == "discovered":
        return "triaged"
    if verified == "triaged":
        return "fixed"
    if verified == "fixed":
        return "verified"
    if verified == "verified":
        return "discovered" if failed else "closed"
    return None


_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "bug_id", "seq", "slice_id", "title", "checks",
    "claims", "detail",
} | set(_PROVENANCE))
_SLICE_REF_KEYS = frozenset({
    "slice_id", "seq", "title", "state", "detail",
} | set(_PROVENANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "bug_id", "trace", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "bug_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered",
    "current_bug", "next_bug", "progress", "board",
    "current", "order", "breaks", "active"})
_LIVE_KEYS = (
    "live_bug", "bugs_live", "live_question",
    "bugs_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "resumes_live",
    "resumed_live", "pauses_campaign", "paused_live",
    "runs_campaign", "ran_campaign", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "bug_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_bug", "sent_bug",
    "posts_note", "posted_note", "traces_live",
    "traced_live")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_checks(value: Any) -> Tuple[str, ...]:
    """A bug's walked checks, held as data.

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
    """A bug's asked claims: claim kinds named as data.

    Each claim names one kind from the closed
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
                f"{what} claims a live gate bug or slice build "
                f"execution ({key!r} is named on it): "
                f"{BUG_RULE}")
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
# The held bug: one slice cut from an active slice.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class BugRecord:
    """One bug slice, held as data.

    The bug names the active slice it was
    buged from, by slice id, its title, its
    verifiable checks, held as data, and its
    claims, named by bug id. The grain is
    derived, never stored: exactly one verifiable
    walk is fixed against the machine. A bug whose
    checks are not yet held stands with its
    checks empty: it stands open, named in
    its gaps, and no check is invented for it.
    The bug is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    bug_id: str
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
            self, "bug_id", _clean_text(self.bug_id, "a bug id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "slice_id", _clean_text(self.slice_id, "an slice id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a bug title"))
        object.__setattr__(
            self, "checks", _check_checks(self.checks))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a bug detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.bug_id

    @property
    def check(self) -> str:
        """The check the bug stands at: its last walked check."""
        return self.checks[-1] if self.checks else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "bug_id": self.bug_id, "seq": self.seq,
            "slice_id": self.slice_id, "title": self.title,
            "checks": list(self.checks),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_bug_ref(value: Any) -> BugRecord:
    if not isinstance(value, BugRecord):
        raise ValueError("a bug must be a BugRecord")
    return value


def validate_bug(bug: Any) -> BugRecord:
    return _check_bug_ref(bug)


def build_bug(record: Any = None, **kwargs: Any) -> BugRecord:
    """Build one held bug from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, BugRecord):
        if kwargs:
            raise ValueError("a bug stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a bug must be a mapping or a BugRecord")
    _needed(data, _RUN_KEYS, "a bug")
    return BugRecord(
        bug_id=data.get("bug_id"), seq=data.get("seq"),
        slice_id=data.get("slice_id"), title=data.get("title"),
        checks=data.get("checks"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_provenance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each bug to the steps it took outside the machine.

    Derived from the held bugs alone: a break is
    one consecutive pair of walked checks the
    explicit gate sequence does not allow, told
    in walk order as before, then after.
    """
    found: Dict[str, Tuple[str, ...]] = {}
    for bug in book.bugs:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(bug.checks, bug.checks[1:])
            if not legal_step(before, after))
        if breaks:
            found[bug.bug_id] = breaks
    return found

def bug_gaps(bug: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a bug from standing complete.

    Mapped from the bug's own held fields alone -
    its walked steps against the explicit question
    sequence, and its carried evidence against the
    closed vocabulary: the bug opens at
    named, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a bug stands complete only when it has
    reached closed. The source names nothing
    further: no gap is borrowed from another
    bug.
    """
    verified = _check_bug_ref(bug)
    gaps: List[str] = []
    if not verified.checks:
        gaps.append(
            "has passed through no step: the bug has not started")
        return tuple(gaps)
    if verified.checks[0] != "discovered":
        gaps.append(
            f"opens at {verified.checks[0]}, not at discovered: "
            f"the bug opens with the question")
    for before, after in zip(verified.checks, verified.checks[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"bug sequence does not allow")
    for kind in verified.claims:
        if kind in BARE_CLAIMS:
            gaps.append(
                f"carries a {kind} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if verified.checks[-1] != "closed":
        gaps.append(
            f"has not reached closed: the bug stands "
            f"at {verified.checks[-1]}")
    return tuple(gaps)

def bug_green(bug: Any, source: Any = None) -> bool:
    return not bug_gaps(bug, source)


def plain_lines(bug: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the bug's own fields."""
    verified = _check_bug_ref(bug)
    return (
        f"Bug: {verified.title}",
        f"Slice: {verified.slice_id}",
        f"Check: {verified.check if verified.check else 'none'}",
        f"Claims: "
        f"{', '.join(verified.claims) if verified.claims else 'none'}",
    )


def segment_of(bug: Any, source: Any = None) -> str:
    verified = _check_bug_ref(bug)
    gaps = bug_gaps(verified, source)
    return (
        f"{verified.bug_id}: {verified.title} - slice: "
        f"'{verified.slice_id}' - check: "
        f"'{verified.check if verified.check else 'none'}' - "
        f"checks: {len(verified.checks)} - claims: "
        f"'{', '.join(verified.claims) if verified.claims else 'none'}' - "
        f"detail: '{verified.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held slice reference: the active slice a book bugs from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class SliceRef:
    """One slice a bug book bugs from, held as a reference.

    The record names the slice, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 slice book's own telling. A bug
    stands only from an active reference: the
    book refuses a bug naming no held reference,
    and a bug from an queued one, BY NAME.
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
    human active - the slice's bug ids in
    derived claim order, held exactly as
    active. The trace is of the set and its
    order, never of a step: when the derived
    trace moves, this record stands stale, named
    in the board, until a new trace is active.
    """

    trace_id: str
    seq: int
    bug_id: str
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
            self, "bug_id", _clean_text(self.bug_id, "an slice id"))
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
            "bug_id": self.bug_id, "trace": self.trace,
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
        bug_id=data.get("bug_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a bug, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One bug stance, held as data.

    The record names its bug, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per bug stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    bug_id: str
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
            self, "bug_id", _clean_text(self.bug_id, "a bug id"))
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
            "bug_id": self.bug_id, "stance": self.stance,
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
        bug_id=data.get("bug_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which slices a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class BugView:
    """A view over the book: every bug, the green, the rest."""

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


def _check_view_ref(value: Any) -> BugView:
    if not isinstance(value, BugView):
        raise ValueError("a view must be an BugView")
    return value


def validate_view(view: Any) -> BugView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> BugView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, BugView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an BugView")
    _needed(data, _VIEW_KEYS, "a view")
    return BugView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class BugPanelRow:
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


def _row_for_bug(bug: BugRecord,
                     source: Any = None) -> BugPanelRow:
    return BugPanelRow(
        item_id=bug.bug_id,
        standing="complete" if bug_green(bug, source) else "open",
        label=bug.title, segment=segment_of(bug, source),
        recorded_on=bug.recorded_on)


def _check_row_ref(value: Any) -> BugPanelRow:
    if not isinstance(value, BugPanelRow):
        raise ValueError("a panel row must be an BugPanelRow")
    return value


def validate_row(row: Any, bug: Any = None,
                 source: Any = None) -> BugPanelRow:
    verified = _check_row_ref(row)
    if bug is not None:
        derived = _row_for_bug(_check_bug_ref(bug), source)
        if verified != derived:
            raise ValueError(
                f"panel row {verified.item_id!r} does not agree with "
                f"the row derived from its bug")
    return verified


def build_row(row: Any = None, bug: Any = None,
              source: Any = None,
              **kwargs: Any) -> BugPanelRow:
    if bug is not None:
        derived = _row_for_bug(_check_bug_ref(bug), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            BugPanelRow(**kwargs))
        return validate_row(built, bug, source)
    if isinstance(row, BugPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return BugPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return BugPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an BugPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[BugPanelRow, ...]
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
        f"The bug book holds {total_items} bugs as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown bugs "
        f"stand complete.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its bug's own fields "
        "- the slice it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any bug.",
        "Completeness is fixed from the held records alone: "
        "a bug that steps outside the bug sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not reached closed stands open, named in its "
        "gaps, and the bug index is derived from the "
        "held bugs, never stored where it could drift.",
    )

@dataclass(frozen=True)
class BugPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[BugPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> BugView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, BugView):
        return view
    return book.view_for(view)


def shown_bugs(source: Any, view: Any = None
                   ) -> Tuple[BugRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.bugs
    if resolved.view_filter == "complete":
        return tuple(g for g in book.bugs if bug_green(g, book))
    return tuple(g for g in book.bugs if not bug_green(g, book))


def bugs_for_slice(source: Any, slice_id: Any
                      ) -> Tuple[BugRecord, ...]:
    wanted = _clean_text(slice_id, "an slice id")
    return tuple(
        g for g in _source_book(source).bugs if g.slice_id == wanted)


def green_bugs(source: Any) -> Tuple[BugRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.bugs if bug_green(g, book))


def current_bug(source: Any) -> Optional[BugRecord]:
    """The book's current bug, DERIVED at call time.

    The first held bug, in held order, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held bugs alone, so it can
    never go stale against them. A book whose every
    bug stands complete has no current bug.
    """
    book = _source_book(source)
    for bug in book.bugs:
        if not bug_green(bug, book):
            return bug
    return None


def derive_panel(source: Any, view: Any = None) -> BugPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_bugs(book, resolved)
    rows = tuple(_row_for_bug(bug, book) for bug in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.bugs), default="")
    green = sum(1 for g in shown if bug_green(g, book))
    return BugPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.bugs), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.bugs), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> BugPanel:
    if not isinstance(value, BugPanel):
        raise ValueError("a panel must be an BugPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> BugPanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 lesson).
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
                **kwargs: Any) -> BugPanel:
    if isinstance(panel, BugPanel):
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
        built = BugPanel(
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
    raise ValueError("a panel must be a mapping, an BugPanel, or derived")


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
        return "closed"
    if green_shown == 0:
        return "blocked"
    return "held"


@dataclass(frozen=True)
class BugVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> BugVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_bugs(book, resolved)
    green = sum(1 for g in shown if bug_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return BugVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> BugVerdict:
    if not isinstance(value, BugVerdict):
        raise ValueError("a verdict must be an BugVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> BugVerdict:
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
                  **kwargs: Any) -> BugVerdict:
    if isinstance(verdict, BugVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = BugVerdict(
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
        "a verdict must be a mapping, an BugVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held slices' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    check: str
    bug_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "check": self.check, "bug_id": self.bug_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class BugIndex:
    """The bug index, derived from the held bugs.

    The index names one entry per green bug, in
    held order - the bug's own one verifiable
    check, its bug id and its title - and the
    bugs that do not stand complete, named in its
    gaps. Nothing here is stored on any bug: the
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


def derive_index(source: Any) -> BugIndex:
    """Derive the bug index from the book's held bugs."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(check=g.check, bug_id=g.bug_id,
                   title=g.title)
        for g in book.bugs if bug_green(g, book))
    gaps = tuple(
        g.bug_id for g in book.bugs if not bug_green(g, book))
    return BugIndex(entries=entries, gaps=gaps)


def bug_for_check(source: Any, check: Any) -> Optional[BugRecord]:
    """The first held bug one check reaches, or none - honestly."""
    if check is None:
        return None
    if not isinstance(check, str):
        raise ValueError("an check must be a string naming the check")
    wanted = check.strip()
    if not wanted:
        return None
    for bug in _source_book(source).bugs:
        if bug.check == wanted:
            return bug
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held order: the bug
    that took it and the step it took, before,
    then after. A book whose bugs all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{bug_id}: {step}"
        for bug_id, steps in _breaks_map(book).items()
        for step in steps)

def bug_order(source: Any,
              slice_id: Any = None) -> Tuple[BugRecord, ...]:
    """The held bugs in their held order, DERIVED at call time.

    Bugs stand in the order the book holds them -
    the order their slices were taken - optionally
    for one slice alone. Nothing here is stored:
    the order is the book's own held order, told.
    """
    book = _source_book(source)
    bugs = list(book.bugs)
    if slice_id is not None:
        wanted = _clean_text(slice_id, "a slice id")
        bugs = [r for r in bugs if r.slice_id == wanted]
    return tuple(bugs)

def trace_of(source: Any, bug_id: Any) -> str:
    """One bug's trace, DERIVED at call time.

    The bug's walked checks joined as one trace
    line, in walk order. A bug that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is named
    elsewhere.
    """
    bug = _source_book(source).bug_for(bug_id)
    return " > ".join(bug.checks)

def trace_for_bug(source: Any,
                  bug_id: Any) -> Optional[TraceRecord]:
    """The held trace for one bug, or none - honestly."""
    wanted = _clean_text(bug_id, "a bug id")
    for record in _source_book(source).traces:
        if record.bug_id == wanted:
            return record
    return None

def trace_current(source: Any, bug_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_bug(source, bug_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, bug_id)

def note_for_bug(source: Any, bug_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one bug (and stance, when named)."""
    wanted = _clean_text(bug_id, "a bug id")
    for record in _source_book(source).notes:
        if record.bug_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the slice targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def board_record(source: Any = None) -> Dict[str, Any]:
    """The bug board, DERIVED here from the held bugs alone.

    The board counts the held bugs by their
    derived completeness - green and red - names
    the current bug, the first that does not yet
    stand complete, tells each held bug's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held bugs took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.bugs
            if ("complete" if bug_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "bugs": number})
    current = current_bug(book)
    traces = []
    for bug in book.bugs:
        trace = trace_for_bug(book, bug.bug_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, bug.bug_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"bug_id": bug.bug_id, "trace": standing})
    return {
        "type": "bug_board",
        "slice": BUG_SLICE,
        "standings": standings,
        "total": len(book.bugs),
        "current_bug": current.bug_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This slice's own roadmap standing, proved from the roadmap itself.

    The record loads this repo's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 slices in 11 parts,
    the discovered prefix, the next slice where the
    campaign resumes, and M-212's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(BUG_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "bug_roadmap",
        "slice": BUG_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m212_title": own.title,
        "m212_part": own.part,
        "m212_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: slices, bugs, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or order ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class BugBook:
    title: str
    slices: Tuple[SliceRef, ...] = ()
    bugs: Tuple[BugRecord, ...] = ()
    views: Tuple[BugView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[BugPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        slices = tuple(_check_slice_ref(g) for g in self.slices)
        bugs = tuple(_check_bug_ref(g) for g in self.bugs)
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
        bug_ids = set()
        bug_seqs = set()
        for bug in bugs:
            if bug.bug_id in bug_ids:
                raise ValueError(
                    f"two bugs stand under id {bug.bug_id!r}")
            if bug.seq in bug_seqs:
                raise ValueError(
                    f"two bugs stand at sequence {bug.seq}")
            bug_ids.add(bug.bug_id)
            bug_seqs.add(bug.seq)
        by_slice = {ref.slice_id: ref for ref in slices}
        for bug in (bugs if slices else ()):

            ref = by_slice.get(bug.slice_id)
            if ref is None:
                raise ValueError(
                    f"bug {bug.bug_id!r} is buged from slice "
                    f"{bug.slice_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "active":
                raise ValueError(
                    f"bug {bug.bug_id!r} is buged from slice "
                    f"{bug.slice_id!r}, which is not active: "
                    f"no slice is buged from an queued slice")
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
            target = (record.bug_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for bug "
                    f"{record.bug_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per bug target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_bugs = set()
        bug_ids = {bug.bug_id for bug in bugs}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.bug_id in trace_bugs:
                raise ValueError(
                    f"two traces stand for bug "
                    f"{record.bug_id!r}: one trace stands "
                    f"per bug walk")
            if bugs and record.bug_id not in bug_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces bug "
                    f"{record.bug_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_bugs.add(record.bug_id)
        object.__setattr__(
            self, "slices", tuple(sorted(slices, key=lambda g: g.seq)))
        object.__setattr__(
            self, "bugs", tuple(sorted(bugs, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.bugs + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.bug_id for g in self.bugs) + tuple(
            v.view_id for v in self.views)

    def bug_ids(self) -> Tuple[str, ...]:
        return tuple(g.bug_id for g in self.bugs)

    def slice_ids(self) -> Tuple[str, ...]:
        return tuple(g.slice_id for g in self.slices)

    def bug_for(self, bug_id: Any) -> BugRecord:
        wanted = _clean_text(bug_id, "a bug id")
        for bug in self.bugs:
            if bug.bug_id == wanted:
                return bug
        raise KeyError(f"no bug named {wanted!r} stands in this book")

    def slice_for(self, slice_id: Any) -> SliceRef:
        wanted = _clean_text(slice_id, "an slice id")
        for ref in self.slices:
            if ref.slice_id == wanted:
                return ref
        raise KeyError(f"no slice named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> BugView:
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
        for bug in self.bugs:
            if bug.bug_id == wanted:
                return bug
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "slices": [g.to_record() for g in self.slices],
            "bugs": [g.to_record() for g in self.bugs],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: BugBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: BugBook) -> None:
    if book.title != "The never-leave-a-bug rule at the M-211 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.slices) != 3 or len(book.bugs) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three slice references, five bugs and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m211-boundary":
        raise ValueError("the pinned panel is panel-m211-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.check for e in index.entries] != ["closed", "closed", "closed"]:
        raise ValueError("the shipped example book index must derive the three held complete bugs in held order")
    if index.gaps != ("bug-bare-fix", "bug-leaping-fix"):
        raise ValueError("the shipped example book must leave the bare and leaping bugs honestly open, named in its gaps")
    found = bug_for_check(book, EXAMPLE_CHECK)
    if found is None or found.bug_id != "bug-held-fix":
        raise ValueError("the shipped example book must reach its opening bug under the example check")
    if trace_of(book, "bug-held-fix") != "discovered > triaged > fixed > verified > closed":
        raise ValueError("the shipped example book must derive the opening bug's trace from its walked steps")
    if not trace_current(book, "bug-held-fix"):
        raise ValueError("the shipped example book must hold the opening bug's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note road")

def validate_book(data: Any, *, require_example: bool = False) -> BugBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, BugBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a bug book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live slice build or execution "
                f"({key!r} is named on it): {BUG_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its bugs under a view")
    if "bug_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held bugs at call time")
    if "board" in data or "current_bug" in data:
        raise ValueError(
            "a book stores no board and no current bug: both are "
            "derived from its held bugs at call time")
    if "trace" in data or "order" in data:
        raise ValueError(
            "a book stores no trace and no order: both are derived "
            "from its held bugs at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != BUG_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{BUG_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != BUG_SLICE):
        raise ValueError(
            f"a book's slice must be {BUG_SLICE!r}")
    head = data.get("bug_head") or data.get("bug_rule") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's bug head must be a mapping")
    title = head.get("title") or data.get("title")
    slices = tuple(build_slice_ref(g) for g in data.get("slices") or ())
    bugs = tuple(build_bug(g) for g in data.get("bugs") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = BugBook(
        title=title, slices=slices, bugs=bugs, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = BugBook(
        title=book.title, slices=book.slices, bugs=book.bugs,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> BugBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (BugBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an BugBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> BugBook:
    return validate_book(data, require_example=require_example)


def load_bug(
        data: Optional[Dict[str, Any]] = None) -> BugBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(BUG_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_bug_file(path: Any) -> BugBook:
    """Load one bug file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: slice references, bugs and views held one by one.
# ---------------------------------------------------------------------

class BugRegistry:
    """An in-memory holding of slice references, bugs and views.

    The registry is the pure layer's model of a
    session's bug book: slice references are
    held under their ids, bugs are held under
    their ids, one bug per id and per sequence,
    and views are held in recorded order, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[SliceRef] = []
        self._bugs: List[BugRecord] = []
        self._views: List[BugView] = []
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
        """Hold one slice reference, fixed whole before held."""
        verified = _check_slice_ref(item)
        return self._register(
            self._slices, verified, "slice_id", "slice reference")

    def register_bug(self, item: Any) -> BugRecord:
        """Hold one bug, fixed whole before held."""
        verified = _check_bug_ref(item)
        return self._register(
            self._bugs, verified, "bug_id", "bug")

    def register_view(self, view: Any) -> BugView:
        """Hold one view; a view naming no id takes a fresh one."""
        verified = _check_view_ref(view)
        if not verified.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            verified = build_view({**verified.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, verified, "view_id", "view")

    def register_book(self, book: Any) -> BugBook:
        """Hold a whole book's records, under its title."""
        verified = build_book(book)
        if self._title is not None and verified.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {verified.title!r}")
        for ref in verified.slices:
            self.register_slice_ref(ref)
        for bug in verified.bugs:
            self.register_bug(bug)
        for view in verified.views:
            self.register_view(view)
        self._title = verified.title
        return self.book()

    def book(self) -> BugBook:
        return BugBook(
            title=self._title or "An unheld bug book",
            slices=tuple(self._slices), bugs=tuple(self._bugs),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[SliceRef, ...]:
        return tuple(self._slices)

    def list_bugs(self) -> Tuple[BugRecord, ...]:
        return tuple(self._bugs)

    def list_views(self) -> Tuple[BugView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._bugs) + tuple(self._views)

    def get_slice(self, slice_id: Any) -> SliceRef:
        return self.book().slice_for(slice_id)

    def get_bug(self, bug_id: Any) -> BugRecord:
        return self.book().bug_for(bug_id)

    def get_view(self, view_id: Any) -> BugView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the journal target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> BugBook:
    if source is None:
        return load_bug()
    if isinstance(source, BugBook):
        return source
    if isinstance(source, BugRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def bug_record(bug: Any, source: Any = None) -> Dict[str, Any]:
    verified = _check_bug_ref(bug)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "bug_bug",
        "slice": BUG_SLICE,
        "bug_id": verified.bug_id,
        "slice_id": verified.slice_id,
        "title": verified.title,
        "segment": segment_of(verified, book),
        "complete": bug_green(verified, book),
        "gaps": list(bug_gaps(verified, book)),
    }
    record.update(_provenance_record(verified))
    return record


def slice_record(ref: Any) -> Dict[str, Any]:
    verified = _check_slice_ref(ref)
    record = {
        "type": "bug_slice",
        "slice": BUG_SLICE,
        "slice_id": verified.slice_id,
        "title": verified.title,
        "state": verified.state,
    }
    record.update(_provenance_record(verified))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    verified = _check_trace_ref(record_in)
    record = {
        "type": "bug_trace",
        "slice": BUG_SLICE,
        "trace_id": verified.trace_id,
        "bug_id": verified.bug_id,
        "trace": verified.trace,
    }
    record.update(_provenance_record(verified))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    verified = _check_view_ref(view)
    record = {
        "type": "bug_view",
        "slice": BUG_SLICE,
        "view_id": verified.view_id, "seq": verified.seq,
        "view_filter": verified.view_filter,
    }
    record.update(_provenance_record(verified))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    verified = _check_note_ref(record_in)
    record = {
        "type": "bug_note",
        "slice": BUG_SLICE,
        "note_id": verified.note_id,
        "bug_id": verified.bug_id,
        "stance": verified.stance,
    }
    record.update(_provenance_record(verified))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    verified = validate_panel(panel, source)
    record = {"type": "bug_panel",
              "slice": BUG_SLICE}
    record.update(verified.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, BugVerdict):
        verified = validate_verdict(verdict, source)
    else:
        verified = derive_verdict(_source_book(verdict), view)
    record = {"type": "bug_verdict",
              "slice": BUG_SLICE}
    record.update(verified.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, BugIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "bug_index",
              "slice": BUG_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    verified = _source_book(book)
    record = {"type": "bug_book",
              "slice": BUG_SLICE,
              "title": verified.title}
    record.update(verified.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(bug: Any, source: Any = None) -> str:
    verified = _check_bug_ref(bug)
    return (
        f"{verified.title} - from {verified.slice_id}: "
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
        f"The bugs stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"bugs stand complete.")


def view_plain_words(view: Any) -> str:
    verified = _check_view_ref(view)
    return f"View {verified.view_id}: shows {verified.view_filter} bugs."


def note_plain_words(record_in: Any) -> str:
    verified = _check_note_ref(record_in)
    return (
        f"Note {verified.note_id}: {verified.stance} "
        f"{verified.bug_id}, toward {verified.target}. "
        f"{verified.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, BugIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} green bugs; "
        f"red, named in its gaps: {gaps}.")

def format_bug(bug: Any, source: Any = None) -> str:
    verified = _check_bug_ref(bug)
    book = _source_book(source) if source is not None else None
    lines = [f"{verified.title} ({verified.bug_id})"]
    lines.extend(plain_lines(verified))
    lines.append(verified.detail)
    if bug_green(verified, book):
        lines.append(
            "This bug stands complete - it walked the question "
            "sequence in the open from discovered to closed, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This bug stands open - it stands named in "
            f"its gaps: {', '.join(bug_gaps(verified, book))}, and "
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
        f"Bug note {verified.stance} {verified.bug_id} "
        f"({verified.note_id}): {verified.title}. {verified.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_check(source: Any, check: Any) -> str:
    bug = bug_for_check(source, check)
    if bug is not None:
        return format_bug(bug, source)
    wanted = check.strip() if isinstance(check, str) else check
    return (
        f"No held bug stands under check {wanted!r} yet - the "
        f"check reaches nothing in this book, and no bug is "
        f"invented for it.")


def format_book(source: Any = None, slice_id: Any = None) -> str:
    book = _source_book(source)
    bugs = (bugs_for_slice(book, slice_id)
              if slice_id is not None else book.bugs)
    lines = [f"The Bug Gate (M-212) - {book.title}"]
    lines.extend(segment_of(bug, book) for bug in bugs)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Bug panel under view {panel.view_id}:"]
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
    lines = ["Bug index, derived from the held bugs:"]
    for entry in index.entries:
        lines.append(f"{entry.check} - {entry.title} ({entry.bug_id})")
    if index.gaps:
        lines.append(
            "Red, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_bug_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Bug Gate (M-212)",
        f"{book.title}: {len(book.bugs)} bugs held, "
        f"{len(green_bugs(book))} bugs standing green, "
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


def parse_bug_args(args: Any) -> Tuple[str, Any]:
    """Parse the /bug grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("bug", "view", "note"):
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
