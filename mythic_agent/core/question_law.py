"""The question law (roadmap slice M-209).

Part IX - The Mythic Method Engine. The roadmap
words: *when the human asks a question mid-campaign,
the campaign pauses and the question is answered
first, plainly and fully - then work resumes
(Volmarr's supreme law, as a feature).*

What already ships, and what this slice adds:

* The question law already binds the work in
  prose - when the human asks a question, the
  question is answered first, plainly and fully,
  its first sentence the direct answer itself,
  and only then does work resume - and this
  slice WIRES it into the loop as data, in its
  own module, standing in the M-195 copy-and-
  share book shape the M-208 book stands in: one
  answerer per campaign, and the answerer's
  charge over one raised question held as a
  book - a questioning. The shipped roads stand
  untouched behind their seams: this layer holds
  questionings as data over the campaign's
  slices and rewrites none of them, and the
  prose law keeps its own standing.

* No charter row names this slice: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-209 on no row, and the
  slice tests pin that absence live. The M-005
  method charter names no slice row either: its
  own words name the whole of Part IX as the
  part that executes the charter, and this slice
  is built to the roadmap words and that
  execution note together. The law itself is
  held as data in the roadmap's own wording -
  the questioning names its question and carries
  the answer it was judged against.

* A questioning is held whole: the slice it
  answers for, named by its slice id; its title;
  the question steps it walked, held as data in
  walk order; and the evidence it carries, held
  as data by kind. The question walk is
  EXPLICIT: its sequence stands as data
  (:data:`CHECKS`, :data:`TRANSITIONS`) -
  raised, paused, drafted, delivered, resumed -
  and a questioning's standing is DERIVED at
  call time from its held steps and evidence
  alone: a questioning that opens anywhere but
  raised, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet reached resumed
  stands open, named in its gaps. The campaign
  pauses for the question: an answer stands
  complete only where the walk paused, the
  answer was drafted plain-first - its first
  sentence the direct answer - and the delivery
  is held as evidence.
* The evidence is a closed vocabulary in two
  halves: the held evidence - question_ref,
  answer_record, delivery_ref, ledger_row,
  evidence an answerer can point to - and the
  bare claims - feeling, memory, assertion,
  summary, which stand as no evidence at all. An
  answer is judged from held evidence alone,
  never from a feeling: a questioning holding a
  bare claim stands open, named in its gaps.
* A questioning stands only for an ACTIVE slice.
  The book holds each slice it answers for as a
  reference record - its id, its title and its
  standing, active or queued, held as data
  copied from the roadmap's own telling. A
  questioning naming a slice that stands nowhere
  in the book refuses BY NAME, and a questioning
  for a slice that is not active refuses BY NAME
  beside it: the answerer deals with the slice
  in hand, in roadmap order, never a queued one,
  and a slice whose question already stands
  complete is never answered twice - the current
  questioning is derived, so a completed slice
  is never the current answering twice.
* The questioning's trace is visible. A trace
  record holds one questioning's walked steps as
  one trace line, exactly as walked, beside the
  questioning. The derived trace is computed at
  call time from the questioning's held steps; a
  held trace that no longer agrees with it
  stands stale, named in the board - the trace
  is the walk itself, never a retelling of it.
* The questioning index is DERIVED at call time
  from the held questionings - one entry per
  complete questioning, under the step it stands
  at - never a second stored copy that could
  drift. A stored index, standing verdict,
  panel, trace, order or current-questioning
  claim on any record refuses by name.
* The current questioning is DERIVED at call
  time - the first held questioning, in held
  order, that does not yet stand complete - never
  stored where it could go stale: that is the
  question the answerer must answer next, and
  the next slice is dealt only when the current
  one resumes.
* The notes are held as data: a note record
  naming its questioning, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per questioning stance; holding a
  note posts none of it, the rule stands as data
  (:data:`QUESTIONING_RULE`), and a record
  claiming a question was actually answered,
  delivered or reported live refuses BY NAME.
  The answerer reports - and those reports, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the shape a real answer file takes,
  a loader reads an answer file anywhere on
  disk, questionings and views are shaped as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding an answer book for a session and
  telling from it. This layer reaches no live
  road: it answers no question live, pauses no
  campaign, resumes no work, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security, spawns
  no process and opens no network - it holds
  questionings as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The question walk is explicit.** A
  questioning is judged against the held steps
  and legal steps alone; an illegal step stands
  named in its gaps, never silently reordered.
* **Complete stands on held evidence alone.** A
  questioning that carries a feeling, a memory,
  an assertion or a summary in place of held
  evidence stands open, named in its gaps: an
  answer is judged from evidence, not vibes.
* **Active slices only, in roadmap order.** A
  questioning for a missing or queued slice
  refuses by name; no questioning is invented
  for a slice the answerer has not dealt with.
* **Unknown stays unknown.** A questioning whose
  steps are not yet held stands with its steps
  empty - no step is invented.
* **The index, panel, verdict, trace, order
  and current questioning are derived, never
  stored.** Each is derived from the held
  questionings at call time; a stored one
  refuses by name, so it can never drift.
* **One questioning per questioning.** Two
  questionings standing for one questioning id
  refuse by name, and one note record stands per
  questioning stance.
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
    "QUESTIONING_RESOURCE",
    "QUESTIONING_SCHEMA",
    "QUESTIONING_SLICE",
    "QUESTIONING_RULE",
    "PLAIN_EXPLANATION",
    "THE_QUESTIONING_SLICE",
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
    "QuestioningRecord",
    "IndexEntry",
    "SliceRef",
    "NoteRecord",
    "QuestioningBook",
    "QuestioningIndex",
    "QuestioningPanel",
    "QuestioningPanelRow",
    "QuestioningRegistry",
    "QuestioningVerdict",
    "QuestioningView",
    "TargetCount",
    "trace_for_questioning",
    "trace_record",
    "board_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_questioning",
    "build_slice_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_questioning",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "questioning_for_check",
    "questioning_order",
    "questioning_record",
    "first_note",
    "format_book",
    "format_questioning",
    "format_index",
    "format_note",
    "format_check",
    "format_panel",
    "format_questioning_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "slice_record",
    "load_questioning",
    "load_questioning_file",
    "normalize_slice_state",
    "normalize_check",
    "normalize_claim_kind",
    "legal_step",
    "next_check",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_questioning",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_questioning_args",
    "green_questionings",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_questionings",
    "validate_trace",
    "validate_book",
    "validate_questioning",
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
    "questioning_gaps",
    "questioning_green",
    "questionings_for_slice",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

QUESTIONING_SCHEMA = "mythic.question_law/1"
QUESTIONING_SLICE = "M-209"
THE_QUESTIONING_SLICE = QUESTIONING_SLICE
QUESTIONING_RESOURCE = "question_law.yaml"
INDEX_ACTION = "index"
EXAMPLE_CHECK = "resumed"
CHECK_FIELDS = ("checks", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("reported", "held", "blocked")
SLICE_STATES = ("active", "queued")
QUESTIONING_RULE = (
    "questionings are held as data alone: when the human "
    "asks a question mid-campaign, the campaign pauses "
    "and the question is answered first, plainly and "
    "fully - then work resumes - the question "
    "walk stands as an explicit question sequence - raised, "
    "paused, drafted, delivered, resumed - and an answer "
    "completes only complete, complete being a state "
    "with evidence held - question ref, answer "
    "record, delivery ref, ledger row - never a feeling, a memory, "
    "an assertion or a summary; holding, viewing and "
    "reading a questioning answers nothing live, pauses "
    "no campaign, resumes no work and opens no network")
PLAIN_EXPLANATION = (
    "The question law (M-209): when the human asks a "
    "question mid-campaign, the campaign pauses and "
    "the question is answered first, plainly and "
    "fully - then work resumes (Volmarr's supreme "
    "law, as a feature).")
USAGE = (
    "Usage: /questionlaw | /questionlaw questioning <questioning-id> | "
    "/questionlaw check <check> | /questionlaw slice <slice-id> | "
    "/questionlaw view <view-id> | /questionlaw note <note-id> | "
    "/questionlaw index | /questionlaw panel | /questionlaw verdict")

CHECKS = ("raised", "paused", "drafted", "delivered", "resumed")
HELD_EVIDENCE = ("answer_record", "question_ref", "delivery_ref", "ledger_row")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "raised": ("paused",),
    "paused": ("drafted",),
    "drafted": ("delivered",),
    "delivered": ("raised", "resumed"),
    "resumed": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a failure or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a questioning stands complete.
    A check outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_check(check: Any, failed: Any = False) -> Optional[str]:
    """The step the answerer takes next, DERIVED from the sequence.

    Raised leads to paused and paused to
    drafted; drafted leads to delivered; at
    delivered a follow-up question steps back to
    raised and a finished answer steps to resumed;
    resumed is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    checked = normalize_check(check)
    if checked == "raised":
        return "paused"
    if checked == "paused":
        return "drafted"
    if checked == "drafted":
        return "delivered"
    if checked == "delivered":
        return "raised" if failed else "resumed"
    return None


_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "questioning_id", "seq", "slice_id", "title", "checks",
    "claims", "detail",
} | set(_PROVENANCE))
_SLICE_REF_KEYS = frozenset({
    "slice_id", "seq", "title", "state", "detail",
} | set(_PROVENANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "questioning_id", "trace", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "questioning_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered",
    "current_questioning", "next_questioning", "progress", "board",
    "current", "order", "breaks", "active"})
_LIVE_KEYS = (
    "live_questioning", "questionings_live", "live_question",
    "questionings_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "resumes_live",
    "resumed_live", "pauses_campaign", "paused_live",
    "runs_campaign", "ran_campaign", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "questioning_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_questioning", "sent_questioning",
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
    """A questioning's walked checks, held as data.

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
    """A questioning's asked claims: claim kinds named as data.

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
                f"{what} claims a live gate questioning or slice build "
                f"execution ({key!r} is named on it): "
                f"{QUESTIONING_RULE}")
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
# The held questioning: one slice cut from an active slice.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class QuestioningRecord:
    """One questioning slice, held as data.

    The questioning names the active slice it was
    questioninged from, by slice id, its title, its
    verifiable checks, held as data, and its
    claims, named by questioning id. The grain is
    derived, never stored: exactly one verifiable
    walk is judged against the machine. A questioning whose
    checks are not yet held stands with its
    checks empty: it stands open, named in
    its gaps, and no check is invented for it.
    The questioning is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    questioning_id: str
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
            self, "questioning_id", _clean_text(self.questioning_id, "a questioning id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "slice_id", _clean_text(self.slice_id, "an slice id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a questioning title"))
        object.__setattr__(
            self, "checks", _check_checks(self.checks))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a questioning detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.questioning_id

    @property
    def check(self) -> str:
        """The check the questioning stands at: its last walked check."""
        return self.checks[-1] if self.checks else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "questioning_id": self.questioning_id, "seq": self.seq,
            "slice_id": self.slice_id, "title": self.title,
            "checks": list(self.checks),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_questioning_ref(value: Any) -> QuestioningRecord:
    if not isinstance(value, QuestioningRecord):
        raise ValueError("a questioning must be a QuestioningRecord")
    return value


def validate_questioning(questioning: Any) -> QuestioningRecord:
    return _check_questioning_ref(questioning)


def build_questioning(record: Any = None, **kwargs: Any) -> QuestioningRecord:
    """Build one held questioning from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, QuestioningRecord):
        if kwargs:
            raise ValueError("a questioning stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a questioning must be a mapping or a QuestioningRecord")
    _needed(data, _RUN_KEYS, "a questioning")
    return QuestioningRecord(
        questioning_id=data.get("questioning_id"), seq=data.get("seq"),
        slice_id=data.get("slice_id"), title=data.get("title"),
        checks=data.get("checks"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_provenance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each questioning to the steps it took outside the machine.

    Derived from the held questionings alone: a break is
    one consecutive pair of walked checks the
    explicit gate sequence does not allow, told
    in walk order as before, then after.
    """
    found: Dict[str, Tuple[str, ...]] = {}
    for questioning in book.questionings:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(questioning.checks, questioning.checks[1:])
            if not legal_step(before, after))
        if breaks:
            found[questioning.questioning_id] = breaks
    return found

def questioning_gaps(questioning: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a questioning from standing complete.

    Judged from the questioning's own held fields alone -
    its walked steps against the explicit question
    sequence, and its carried evidence against the
    closed vocabulary: the questioning opens at
    raised, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a questioning stands complete only when it has
    reached resumed. The source names nothing
    further: no gap is borrowed from another
    questioning.
    """
    checked = _check_questioning_ref(questioning)
    gaps: List[str] = []
    if not checked.checks:
        gaps.append(
            "has passed through no step: the questioning has not started")
        return tuple(gaps)
    if checked.checks[0] != "raised":
        gaps.append(
            f"opens at {checked.checks[0]}, not at raised: "
            f"the questioning opens with the question")
    for before, after in zip(checked.checks, checked.checks[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"question sequence does not allow")
    for kind in checked.claims:
        if kind in BARE_CLAIMS:
            gaps.append(
                f"carries a {kind} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if checked.checks[-1] != "resumed":
        gaps.append(
            f"has not reached resumed: the questioning stands "
            f"at {checked.checks[-1]}")
    return tuple(gaps)

def questioning_green(questioning: Any, source: Any = None) -> bool:
    return not questioning_gaps(questioning, source)


def plain_lines(questioning: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the questioning's own fields."""
    checked = _check_questioning_ref(questioning)
    return (
        f"Questioning: {checked.title}",
        f"Slice: {checked.slice_id}",
        f"Check: {checked.check if checked.check else 'none'}",
        f"Claims: "
        f"{', '.join(checked.claims) if checked.claims else 'none'}",
    )


def segment_of(questioning: Any, source: Any = None) -> str:
    checked = _check_questioning_ref(questioning)
    gaps = questioning_gaps(checked, source)
    return (
        f"{checked.questioning_id}: {checked.title} - slice: "
        f"'{checked.slice_id}' - check: "
        f"'{checked.check if checked.check else 'none'}' - "
        f"checks: {len(checked.checks)} - claims: "
        f"'{', '.join(checked.claims) if checked.claims else 'none'}' - "
        f"detail: '{checked.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held slice reference: the active slice a book questionings from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class SliceRef:
    """One slice a questioning book questionings from, held as a reference.

    The record names the slice, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 slice book's own telling. A questioning
    stands only from an active reference: the
    book refuses a questioning naming no held reference,
    and a questioning from an queued one, BY NAME.
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
    human active - the slice's questioning ids in
    derived claim order, held exactly as
    active. The trace is of the set and its
    order, never of a step: when the derived
    trace moves, this record stands stale, named
    in the board, until a new trace is active.
    """

    trace_id: str
    seq: int
    questioning_id: str
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
            self, "questioning_id", _clean_text(self.questioning_id, "an slice id"))
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
            "questioning_id": self.questioning_id, "trace": self.trace,
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
        questioning_id=data.get("questioning_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a questioning, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One questioning stance, held as data.

    The record names its questioning, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per questioning stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    questioning_id: str
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
            self, "questioning_id", _clean_text(self.questioning_id, "a questioning id"))
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
            "questioning_id": self.questioning_id, "stance": self.stance,
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
        questioning_id=data.get("questioning_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which slices a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class QuestioningView:
    """A view over the book: every questioning, the green, the rest."""

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


def _check_view_ref(value: Any) -> QuestioningView:
    if not isinstance(value, QuestioningView):
        raise ValueError("a view must be an QuestioningView")
    return value


def validate_view(view: Any) -> QuestioningView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> QuestioningView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, QuestioningView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an QuestioningView")
    _needed(data, _VIEW_KEYS, "a view")
    return QuestioningView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class QuestioningPanelRow:
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


def _row_for_questioning(questioning: QuestioningRecord,
                     source: Any = None) -> QuestioningPanelRow:
    return QuestioningPanelRow(
        item_id=questioning.questioning_id,
        standing="complete" if questioning_green(questioning, source) else "open",
        label=questioning.title, segment=segment_of(questioning, source),
        recorded_on=questioning.recorded_on)


def _check_row_ref(value: Any) -> QuestioningPanelRow:
    if not isinstance(value, QuestioningPanelRow):
        raise ValueError("a panel row must be an QuestioningPanelRow")
    return value


def validate_row(row: Any, questioning: Any = None,
                 source: Any = None) -> QuestioningPanelRow:
    checked = _check_row_ref(row)
    if questioning is not None:
        derived = _row_for_questioning(_check_questioning_ref(questioning), source)
        if checked != derived:
            raise ValueError(
                f"panel row {checked.item_id!r} does not agree with "
                f"the row derived from its questioning")
    return checked


def build_row(row: Any = None, questioning: Any = None,
              source: Any = None,
              **kwargs: Any) -> QuestioningPanelRow:
    if questioning is not None:
        derived = _row_for_questioning(_check_questioning_ref(questioning), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            QuestioningPanelRow(**kwargs))
        return validate_row(built, questioning, source)
    if isinstance(row, QuestioningPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return QuestioningPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return QuestioningPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an QuestioningPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[QuestioningPanelRow, ...]
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
        f"The questioning book holds {total_items} questionings as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown questionings "
        f"stand complete.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its questioning's own fields "
        "- the slice it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any questioning.",
        "Completeness is judged from the held records alone: "
        "a questioning that steps outside the question sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not reached resumed stands open, named in its "
        "gaps, and the questioning index is derived from the "
        "held questionings, never stored where it could drift.",
    )

@dataclass(frozen=True)
class QuestioningPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[QuestioningPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> QuestioningView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, QuestioningView):
        return view
    return book.view_for(view)


def shown_questionings(source: Any, view: Any = None
                   ) -> Tuple[QuestioningRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.questionings
    if resolved.view_filter == "complete":
        return tuple(g for g in book.questionings if questioning_green(g, book))
    return tuple(g for g in book.questionings if not questioning_green(g, book))


def questionings_for_slice(source: Any, slice_id: Any
                      ) -> Tuple[QuestioningRecord, ...]:
    wanted = _clean_text(slice_id, "an slice id")
    return tuple(
        g for g in _source_book(source).questionings if g.slice_id == wanted)


def green_questionings(source: Any) -> Tuple[QuestioningRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.questionings if questioning_green(g, book))


def current_questioning(source: Any) -> Optional[QuestioningRecord]:
    """The book's current questioning, DERIVED at call time.

    The first held questioning, in held order, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held questionings alone, so it can
    never go stale against them. A book whose every
    questioning stands complete has no current questioning.
    """
    book = _source_book(source)
    for questioning in book.questionings:
        if not questioning_green(questioning, book):
            return questioning
    return None


def derive_panel(source: Any, view: Any = None) -> QuestioningPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_questionings(book, resolved)
    rows = tuple(_row_for_questioning(questioning, book) for questioning in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.questionings), default="")
    green = sum(1 for g in shown if questioning_green(g, book))
    return QuestioningPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.questionings), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.questionings), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> QuestioningPanel:
    if not isinstance(value, QuestioningPanel):
        raise ValueError("a panel must be an QuestioningPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> QuestioningPanel:
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
                **kwargs: Any) -> QuestioningPanel:
    if isinstance(panel, QuestioningPanel):
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
        built = QuestioningPanel(
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
    raise ValueError("a panel must be a mapping, an QuestioningPanel, or derived")


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
class QuestioningVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> QuestioningVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_questionings(book, resolved)
    green = sum(1 for g in shown if questioning_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return QuestioningVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> QuestioningVerdict:
    if not isinstance(value, QuestioningVerdict):
        raise ValueError("a verdict must be an QuestioningVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> QuestioningVerdict:
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
                  **kwargs: Any) -> QuestioningVerdict:
    if isinstance(verdict, QuestioningVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = QuestioningVerdict(
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
        "a verdict must be a mapping, an QuestioningVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held slices' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    check: str
    questioning_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "check": self.check, "questioning_id": self.questioning_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class QuestioningIndex:
    """The questioning index, derived from the held questionings.

    The index names one entry per green questioning, in
    held order - the questioning's own one verifiable
    check, its questioning id and its title - and the
    questionings that do not stand complete, named in its
    gaps. Nothing here is stored on any questioning: the
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


def derive_index(source: Any) -> QuestioningIndex:
    """Derive the questioning index from the book's held questionings."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(check=g.check, questioning_id=g.questioning_id,
                   title=g.title)
        for g in book.questionings if questioning_green(g, book))
    gaps = tuple(
        g.questioning_id for g in book.questionings if not questioning_green(g, book))
    return QuestioningIndex(entries=entries, gaps=gaps)


def questioning_for_check(source: Any, check: Any) -> Optional[QuestioningRecord]:
    """The first held questioning one check reaches, or none - honestly."""
    if check is None:
        return None
    if not isinstance(check, str):
        raise ValueError("an check must be a string naming the check")
    wanted = check.strip()
    if not wanted:
        return None
    for questioning in _source_book(source).questionings:
        if questioning.check == wanted:
            return questioning
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held order: the questioning
    that took it and the step it took, before,
    then after. A book whose questionings all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{questioning_id}: {step}"
        for questioning_id, steps in _breaks_map(book).items()
        for step in steps)

def questioning_order(source: Any,
              slice_id: Any = None) -> Tuple[QuestioningRecord, ...]:
    """The held questionings in their held order, DERIVED at call time.

    Questionings stand in the order the book holds them -
    the order their slices were taken - optionally
    for one slice alone. Nothing here is stored:
    the order is the book's own held order, told.
    """
    book = _source_book(source)
    questionings = list(book.questionings)
    if slice_id is not None:
        wanted = _clean_text(slice_id, "a slice id")
        questionings = [r for r in questionings if r.slice_id == wanted]
    return tuple(questionings)

def trace_of(source: Any, questioning_id: Any) -> str:
    """One questioning's trace, DERIVED at call time.

    The questioning's walked checks joined as one trace
    line, in walk order. A questioning that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is named
    elsewhere.
    """
    questioning = _source_book(source).questioning_for(questioning_id)
    return " > ".join(questioning.checks)

def trace_for_questioning(source: Any,
                  questioning_id: Any) -> Optional[TraceRecord]:
    """The held trace for one questioning, or none - honestly."""
    wanted = _clean_text(questioning_id, "a questioning id")
    for record in _source_book(source).traces:
        if record.questioning_id == wanted:
            return record
    return None

def trace_current(source: Any, questioning_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_questioning(source, questioning_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, questioning_id)

def note_for_questioning(source: Any, questioning_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one questioning (and stance, when named)."""
    wanted = _clean_text(questioning_id, "a questioning id")
    for record in _source_book(source).notes:
        if record.questioning_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the slice targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def board_record(source: Any = None) -> Dict[str, Any]:
    """The questioning board, DERIVED here from the held questionings alone.

    The board counts the held questionings by their
    derived completeness - green and red - names
    the current questioning, the first that does not yet
    stand complete, tells each held questioning's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held questionings took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.questionings
            if ("complete" if questioning_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "questionings": number})
    current = current_questioning(book)
    traces = []
    for questioning in book.questionings:
        trace = trace_for_questioning(book, questioning.questioning_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, questioning.questioning_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"questioning_id": questioning.questioning_id, "trace": standing})
    return {
        "type": "questioning_board",
        "slice": QUESTIONING_SLICE,
        "standings": standings,
        "total": len(book.questionings),
        "current_questioning": current.questioning_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This slice's own roadmap standing, proved from the roadmap itself.

    The record loads this repo's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 slices in 11 parts,
    the banked prefix, the next slice where the
    campaign resumes, and M-209's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(QUESTIONING_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "questioning_roadmap",
        "slice": QUESTIONING_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m209_title": own.title,
        "m209_part": own.part,
        "m209_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: slices, questionings, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or order ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class QuestioningBook:
    title: str
    slices: Tuple[SliceRef, ...] = ()
    questionings: Tuple[QuestioningRecord, ...] = ()
    views: Tuple[QuestioningView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[QuestioningPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        slices = tuple(_check_slice_ref(g) for g in self.slices)
        questionings = tuple(_check_questioning_ref(g) for g in self.questionings)
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
        questioning_ids = set()
        questioning_seqs = set()
        for questioning in questionings:
            if questioning.questioning_id in questioning_ids:
                raise ValueError(
                    f"two questionings stand under id {questioning.questioning_id!r}")
            if questioning.seq in questioning_seqs:
                raise ValueError(
                    f"two questionings stand at sequence {questioning.seq}")
            questioning_ids.add(questioning.questioning_id)
            questioning_seqs.add(questioning.seq)
        by_slice = {ref.slice_id: ref for ref in slices}
        for questioning in (questionings if slices else ()):

            ref = by_slice.get(questioning.slice_id)
            if ref is None:
                raise ValueError(
                    f"questioning {questioning.questioning_id!r} is questioninged from slice "
                    f"{questioning.slice_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "active":
                raise ValueError(
                    f"questioning {questioning.questioning_id!r} is questioninged from slice "
                    f"{questioning.slice_id!r}, which is not active: "
                    f"no slice is questioninged from an queued slice")
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
            target = (record.questioning_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for questioning "
                    f"{record.questioning_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per questioning target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_questionings = set()
        questioning_ids = {questioning.questioning_id for questioning in questionings}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.questioning_id in trace_questionings:
                raise ValueError(
                    f"two traces stand for questioning "
                    f"{record.questioning_id!r}: one trace stands "
                    f"per questioning walk")
            if questionings and record.questioning_id not in questioning_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces questioning "
                    f"{record.questioning_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_questionings.add(record.questioning_id)
        object.__setattr__(
            self, "slices", tuple(sorted(slices, key=lambda g: g.seq)))
        object.__setattr__(
            self, "questionings", tuple(sorted(questionings, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.questionings + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.questioning_id for g in self.questionings) + tuple(
            v.view_id for v in self.views)

    def questioning_ids(self) -> Tuple[str, ...]:
        return tuple(g.questioning_id for g in self.questionings)

    def slice_ids(self) -> Tuple[str, ...]:
        return tuple(g.slice_id for g in self.slices)

    def questioning_for(self, questioning_id: Any) -> QuestioningRecord:
        wanted = _clean_text(questioning_id, "a questioning id")
        for questioning in self.questionings:
            if questioning.questioning_id == wanted:
                return questioning
        raise KeyError(f"no questioning named {wanted!r} stands in this book")

    def slice_for(self, slice_id: Any) -> SliceRef:
        wanted = _clean_text(slice_id, "an slice id")
        for ref in self.slices:
            if ref.slice_id == wanted:
                return ref
        raise KeyError(f"no slice named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> QuestioningView:
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
        for questioning in self.questionings:
            if questioning.questioning_id == wanted:
                return questioning
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "slices": [g.to_record() for g in self.slices],
            "questionings": [g.to_record() for g in self.questionings],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: QuestioningBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: QuestioningBook) -> None:
    if book.title != "The question law at the M-208 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.slices) != 3 or len(book.questionings) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three slice references, five questionings and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m208-boundary":
        raise ValueError("the pinned panel is panel-m208-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.check for e in index.entries] != ["resumed", "resumed", "resumed"]:
        raise ValueError("the shipped example book index must derive the three held complete questionings in held order")
    if index.gaps != ("questioning-bare-question", "questioning-leaping-question"):
        raise ValueError("the shipped example book must leave the bare and leaping questionings honestly open, named in its gaps")
    found = questioning_for_check(book, EXAMPLE_CHECK)
    if found is None or found.questioning_id != "questioning-answered-question":
        raise ValueError("the shipped example book must reach its opening questioning under the example check")
    if trace_of(book, "questioning-answered-question") != "raised > paused > drafted > delivered > resumed":
        raise ValueError("the shipped example book must derive the opening questioning's trace from its walked steps")
    if not trace_current(book, "questioning-answered-question"):
        raise ValueError("the shipped example book must hold the opening questioning's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note road")

def validate_book(data: Any, *, require_example: bool = False) -> QuestioningBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, QuestioningBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a questioning book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live slice build or execution "
                f"({key!r} is named on it): {QUESTIONING_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its questionings under a view")
    if "questioning_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held questionings at call time")
    if "board" in data or "current_questioning" in data:
        raise ValueError(
            "a book stores no board and no current questioning: both are "
            "derived from its held questionings at call time")
    if "trace" in data or "order" in data:
        raise ValueError(
            "a book stores no trace and no order: both are derived "
            "from its held questionings at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != QUESTIONING_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{QUESTIONING_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != QUESTIONING_SLICE):
        raise ValueError(
            f"a book's slice must be {QUESTIONING_SLICE!r}")
    head = data.get("questioning_head") or data.get("question_law") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's questioning head must be a mapping")
    title = head.get("title") or data.get("title")
    slices = tuple(build_slice_ref(g) for g in data.get("slices") or ())
    questionings = tuple(build_questioning(g) for g in data.get("questionings") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = QuestioningBook(
        title=title, slices=slices, questionings=questionings, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = QuestioningBook(
        title=book.title, slices=book.slices, questionings=book.questionings,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> QuestioningBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (QuestioningBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an QuestioningBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> QuestioningBook:
    return validate_book(data, require_example=require_example)


def load_questioning(
        data: Optional[Dict[str, Any]] = None) -> QuestioningBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(QUESTIONING_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_questioning_file(path: Any) -> QuestioningBook:
    """Load one questioning file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: slice references, questionings and views held one by one.
# ---------------------------------------------------------------------

class QuestioningRegistry:
    """An in-memory holding of slice references, questionings and views.

    The registry is the pure layer's model of a
    session's questioning book: slice references are
    held under their ids, questionings are held under
    their ids, one questioning per id and per sequence,
    and views are held in recorded order, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[SliceRef] = []
        self._questionings: List[QuestioningRecord] = []
        self._views: List[QuestioningView] = []
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
        """Hold one slice reference, judged whole before held."""
        checked = _check_slice_ref(item)
        return self._register(
            self._slices, checked, "slice_id", "slice reference")

    def register_questioning(self, item: Any) -> QuestioningRecord:
        """Hold one questioning, judged whole before held."""
        checked = _check_questioning_ref(item)
        return self._register(
            self._questionings, checked, "questioning_id", "questioning")

    def register_view(self, view: Any) -> QuestioningView:
        """Hold one view; a view naming no id takes a fresh one."""
        checked = _check_view_ref(view)
        if not checked.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            checked = build_view({**checked.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, checked, "view_id", "view")

    def register_book(self, book: Any) -> QuestioningBook:
        """Hold a whole book's records, under its title."""
        checked = build_book(book)
        if self._title is not None and checked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {checked.title!r}")
        for ref in checked.slices:
            self.register_slice_ref(ref)
        for questioning in checked.questionings:
            self.register_questioning(questioning)
        for view in checked.views:
            self.register_view(view)
        self._title = checked.title
        return self.book()

    def book(self) -> QuestioningBook:
        return QuestioningBook(
            title=self._title or "An unheld questioning book",
            slices=tuple(self._slices), questionings=tuple(self._questionings),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[SliceRef, ...]:
        return tuple(self._slices)

    def list_questionings(self) -> Tuple[QuestioningRecord, ...]:
        return tuple(self._questionings)

    def list_views(self) -> Tuple[QuestioningView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._questionings) + tuple(self._views)

    def get_slice(self, slice_id: Any) -> SliceRef:
        return self.book().slice_for(slice_id)

    def get_questioning(self, questioning_id: Any) -> QuestioningRecord:
        return self.book().questioning_for(questioning_id)

    def get_view(self, view_id: Any) -> QuestioningView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the journal target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> QuestioningBook:
    if source is None:
        return load_questioning()
    if isinstance(source, QuestioningBook):
        return source
    if isinstance(source, QuestioningRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def questioning_record(questioning: Any, source: Any = None) -> Dict[str, Any]:
    checked = _check_questioning_ref(questioning)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "questioning_questioning",
        "slice": QUESTIONING_SLICE,
        "questioning_id": checked.questioning_id,
        "slice_id": checked.slice_id,
        "title": checked.title,
        "segment": segment_of(checked, book),
        "complete": questioning_green(checked, book),
        "gaps": list(questioning_gaps(checked, book)),
    }
    record.update(_provenance_record(checked))
    return record


def slice_record(ref: Any) -> Dict[str, Any]:
    checked = _check_slice_ref(ref)
    record = {
        "type": "questioning_slice",
        "slice": QUESTIONING_SLICE,
        "slice_id": checked.slice_id,
        "title": checked.title,
        "state": checked.state,
    }
    record.update(_provenance_record(checked))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_trace_ref(record_in)
    record = {
        "type": "questioning_trace",
        "slice": QUESTIONING_SLICE,
        "trace_id": checked.trace_id,
        "questioning_id": checked.questioning_id,
        "trace": checked.trace,
    }
    record.update(_provenance_record(checked))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    checked = _check_view_ref(view)
    record = {
        "type": "questioning_view",
        "slice": QUESTIONING_SLICE,
        "view_id": checked.view_id, "seq": checked.seq,
        "view_filter": checked.view_filter,
    }
    record.update(_provenance_record(checked))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_note_ref(record_in)
    record = {
        "type": "questioning_note",
        "slice": QUESTIONING_SLICE,
        "note_id": checked.note_id,
        "questioning_id": checked.questioning_id,
        "stance": checked.stance,
    }
    record.update(_provenance_record(checked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    checked = validate_panel(panel, source)
    record = {"type": "questioning_panel",
              "slice": QUESTIONING_SLICE}
    record.update(checked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, QuestioningVerdict):
        checked = validate_verdict(verdict, source)
    else:
        checked = derive_verdict(_source_book(verdict), view)
    record = {"type": "questioning_verdict",
              "slice": QUESTIONING_SLICE}
    record.update(checked.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, QuestioningIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "questioning_index",
              "slice": QUESTIONING_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    checked = _source_book(book)
    record = {"type": "questioning_book",
              "slice": QUESTIONING_SLICE,
              "title": checked.title}
    record.update(checked.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(questioning: Any, source: Any = None) -> str:
    checked = _check_questioning_ref(questioning)
    return (
        f"{checked.title} - from {checked.slice_id}: "
        f"check {checked.check if checked.check else 'none'}, "
        f"claims "
        f"{', '.join(checked.claims) if checked.claims else 'none'}. "
        f"{checked.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The questionings stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"questionings stand complete.")


def view_plain_words(view: Any) -> str:
    checked = _check_view_ref(view)
    return f"View {checked.view_id}: shows {checked.view_filter} questionings."


def note_plain_words(record_in: Any) -> str:
    checked = _check_note_ref(record_in)
    return (
        f"Note {checked.note_id}: {checked.stance} "
        f"{checked.questioning_id}, toward {checked.target}. "
        f"{checked.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, QuestioningIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} green questionings; "
        f"red, named in its gaps: {gaps}.")

def format_questioning(questioning: Any, source: Any = None) -> str:
    checked = _check_questioning_ref(questioning)
    book = _source_book(source) if source is not None else None
    lines = [f"{checked.title} ({checked.questioning_id})"]
    lines.extend(plain_lines(checked))
    lines.append(checked.detail)
    if questioning_green(checked, book):
        lines.append(
            "This questioning stands complete - it walked the question "
            "sequence in the open from raised to resumed, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This questioning stands open - it stands named in "
            f"its gaps: {', '.join(questioning_gaps(checked, book))}, and "
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
        f"Questioning note {checked.stance} {checked.questioning_id} "
        f"({checked.note_id}): {checked.title}. {checked.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_check(source: Any, check: Any) -> str:
    questioning = questioning_for_check(source, check)
    if questioning is not None:
        return format_questioning(questioning, source)
    wanted = check.strip() if isinstance(check, str) else check
    return (
        f"No held questioning stands under check {wanted!r} yet - the "
        f"check reaches nothing in this book, and no questioning is "
        f"invented for it.")


def format_book(source: Any = None, slice_id: Any = None) -> str:
    book = _source_book(source)
    questionings = (questionings_for_slice(book, slice_id)
              if slice_id is not None else book.questionings)
    lines = [f"The Question Gate (M-209) - {book.title}"]
    lines.extend(segment_of(questioning, book) for questioning in questionings)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Questioning panel under view {panel.view_id}:"]
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
    lines = ["Questioning index, derived from the held questionings:"]
    for entry in index.entries:
        lines.append(f"{entry.check} - {entry.title} ({entry.questioning_id})")
    if index.gaps:
        lines.append(
            "Red, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_questioning_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Question Gate (M-209)",
        f"{book.title}: {len(book.questionings)} questionings held, "
        f"{len(green_questionings(book))} questionings standing green, "
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


def parse_questioning_args(args: Any) -> Tuple[str, Any]:
    """Parse the /questioning grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("questioning", "view", "note"):
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
