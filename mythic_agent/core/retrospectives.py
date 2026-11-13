"""Retrospectives (roadmap slice M-213).

Part IX - The Mythic Method Engine. The roadmap
words: *at part and campaign close, the crew
writes what was learned; lessons flow to the
Self-Improving ledger (M-155).*

What already ships, and what this slice adds:

* The Self-Improving ledger already ships as
  data (M-155, ``core/self_improving_ledger.py``):
  candidate memories captured after significant
  work, promoted only by an explicit decision.
  This slice WIRES the inflow the ledger's own
  docstring names - M-213 retrospectives flowing
  here - as data, in its own module, standing in
  the M-195 copy-and-share book shape the M-212
  book stands in: one crew per campaign, and the
  crew's charge over one closed slice's lesson
  held as a book - a retrospective. The shipped
  roads stand untouched behind their seams: this
  layer holds retrospectives as data over the
  campaign's slices and rewrites none of them,
  and the ledger keeps its own standing. Lessons
  flow to the ledger AS DATA alone: a lesson
  carries a ledger ref, a reference held in this
  book; holding, viewing or telling a
  retrospective writes no ledger file live,
  captures no candidate and promotes nothing.

* No charter row names this slice: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-213 on no row, and the
  slice tests pin that absence live. The M-005
  method charter names no slice row either: its
  own words name the whole of Part IX as the
  part that executes the charter, and this slice
  is built to the roadmap words and that
  execution note together.

* A retrospective is held whole: the slice it
  answers for, named by its slice id; its title;
  the lesson steps it walked, held as data in
  walk order; and the evidence it carries, held
  as data by kind. The lesson walk is EXPLICIT:
  its sequence stands as data
  (:data:`CHECKS`, :data:`TRANSITIONS`) -
  opened, reflected, written, distilled, filed -
  and a retrospective's standing is DERIVED at
  call time from its held steps and evidence
  alone: a retrospective that opens anywhere but
  opened, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet reached filed stands
  open, named in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - slice_ref,
  lesson_ref, test_record, ledger_ref, evidence
  a crew can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A lesson is
  distilled from held evidence alone, never
  from a feeling: a retrospective holding a
  bare claim stands open, named in its gaps.
* A retrospective stands only for an ACTIVE
  slice. The book holds each slice it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  retrospective naming a slice that stands
  nowhere in the book refuses BY NAME, and a
  retrospective for a slice that is not active
  refuses BY NAME beside it: the crew deals with
  the slice in hand, in roadmap order, never a
  queued one, and a slice whose lesson already
  stands complete is never written twice - the
  current retrospective is derived, so a
  completed slice is never the current lesson
  twice.
* The retrospective's trace is visible. A trace
  record holds one retrospective's walked steps
  as one trace line, exactly as walked, beside
  the retrospective. The derived trace is
  computed at call time from the retrospective's
  held steps; a held trace that no longer agrees
  with it stands stale, named in the board - the
  trace is the walk itself, never a retelling
  of it.
* The retrospective index is DERIVED at call
  time from the held retrospectives - one entry
  per complete retrospective, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, order or current-retrospective
  claim on any record refuses by name.
* The current retrospective is DERIVED at call
  time - the first held retrospective, in held
  order, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its retrospective, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per retrospective stance; holding
  a note posts none of it, the rule stands as
  data (:data:`RETRO_RULE`), and a record
  claiming a lesson was actually filed,
  captured or promoted live refuses BY NAME.
  The crew reports - and those reports, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the shape a real retrospective
  file takes, a loader reads a file anywhere on
  disk, retrospectives and views are shaped as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a retrospective book for a session and
  telling from it. This layer reaches no live
  road: it writes no lesson live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no crew, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds retrospectives
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The lesson walk is explicit.** A
  retrospective is distilled against the held
  steps and legal steps alone; an illegal step
  stands named in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  retrospective that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, named in its gaps:
  a lesson is distilled from evidence, not
  vibes.
* **Active slices only, in roadmap order.** A
  retrospective for a missing or queued slice
  refuses by name; no retrospective is invented
  for a slice the crew has not dealt with.
* **Unknown stays unknown.** A retrospective
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, order
  and current retrospective are derived, never
  stored.** Each is derived from the held
  retrospectives at call time; a stored one
  refuses by name, so it can never drift.
* **One retrospective per retrospective.** Two
  retrospectives standing for one retro id
  refuse by name, and one note record stands per
  retrospective stance.
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
    "RETRO_RESOURCE",
    "RETRO_SCHEMA",
    "RETRO_SLICE",
    "RETRO_RULE",
    "PLAIN_EXPLANATION",
    "THE_RETRO_SLICE",
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
    "RetroRecord",
    "IndexEntry",
    "SliceRef",
    "NoteRecord",
    "RetroBook",
    "RetroIndex",
    "RetroPanel",
    "RetroPanelRow",
    "RetroRegistry",
    "RetroVerdict",
    "RetroView",
    "TargetCount",
    "trace_for_retro",
    "trace_record",
    "board_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_retro",
    "build_slice_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_retro",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "retro_for_check",
    "retro_order",
    "retro_record",
    "first_note",
    "format_book",
    "format_retro",
    "format_index",
    "format_note",
    "format_check",
    "format_panel",
    "format_retro_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "slice_record",
    "load_retro",
    "load_retro_file",
    "normalize_slice_state",
    "normalize_check",
    "normalize_claim_kind",
    "legal_step",
    "next_check",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_retro",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_retro_args",
    "green_retros",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_retros",
    "validate_trace",
    "validate_book",
    "validate_retro",
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
    "retro_gaps",
    "retro_green",
    "retros_for_slice",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

RETRO_SCHEMA = "mythic.retrospectives/1"
RETRO_SLICE = "M-213"
THE_RETRO_SLICE = RETRO_SLICE
RETRO_RESOURCE = "retrospectives.yaml"
INDEX_ACTION = "index"
EXAMPLE_CHECK = "filed"
CHECK_FIELDS = ("checks", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("filed", "held", "blocked")
SLICE_STATES = ("active", "queued")
RETRO_RULE = (
    "retrospectives are held as data alone: at "
    "part and campaign close the crew writes "
    "what was learned - lessons flow to the "
    "Self-Improving ledger (M-155) as data, held "
    "by reference (a ledger ref), never written "
    "live - the retrospective walk stands as an "
    "explicit retro sequence - opened, reflected, "
    "written, distilled, filed - and a lesson "
    "completes only complete, complete being a "
    "state with evidence held - slice ref, lesson "
    "ref, test record, ledger ref - never a "
    "feeling, a memory, an assertion or a "
    "summary; holding, viewing and reading a "
    "retrospective writes no lesson live, files "
    "nothing to the ledger, spawns no crew and "
    "opens no network")
PLAIN_EXPLANATION = (
    "Retrospectives (M-213): at part and campaign "
    "close, the crew writes what was learned; "
    "lessons flow to the Self-Improving ledger "
    "(M-155).")
USAGE = (
    "Usage: /retrospectives | /retrospectives retro <retro-id> | "
    "/retrospectives check <check> | /retrospectives slice <slice-id> | "
    "/retrospectives view <view-id> | /retrospectives note <note-id> | "
    "/retrospectives index | /retrospectives panel | /retrospectives verdict")

CHECKS = ("opened", "reflected", "written", "distilled", "filed")
HELD_EVIDENCE = ("slice_ref", "lesson_ref", "test_record", "ledger_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "opened": ("reflected",),
    "reflected": ("written",),
    "written": ("distilled",),
    "distilled": ("opened", "filed"),
    "filed": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a failure or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a retro stands complete.
    A check outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_check(check: Any, failed: Any = False) -> Optional[str]:
    """The step the scribe takes next, DERIVED from the sequence.

    Banked leads to reflected and reflected to
    written; written leads to distilled; at
    distilled a follow-up banking steps back to opened and a finished lesson steps to filed;
    filed is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    distilled = normalize_check(check)
    if distilled == "opened":
        return "reflected"
    if distilled == "reflected":
        return "written"
    if distilled == "written":
        return "distilled"
    if distilled == "distilled":
        return "opened" if failed else "filed"
    return None


_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "retro_id", "seq", "slice_id", "title", "checks",
    "claims", "detail",
} | set(_PROVENANCE))
_SLICE_REF_KEYS = frozenset({
    "slice_id", "seq", "title", "state", "detail",
} | set(_PROVENANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "retro_id", "trace", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "retro_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered",
    "current_retro", "next_retro", "progress", "board",
    "current", "order", "breaks", "active"})
_LIVE_KEYS = (
    "live_retro", "retros_live", "live_question",
    "retros_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "resumes_live",
    "resumed_live", "pauses_campaign", "paused_live",
    "runs_campaign", "ran_campaign", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "retro_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_retro", "sent_retro",
    "posts_note", "posted_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_lesson", "filed_live", "spawns_crew", "spawned_crew", "sends_lesson", "sent_lesson", "writes_lesson", "wrote_lesson")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_checks(value: Any) -> Tuple[str, ...]:
    """A retro's walked checks, held as data.

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
    """A retro's asked claims: claim kinds named as data.

    Each claim names one kind from the filed
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
                f"{what} claims a live gate retro or slice build "
                f"execution ({key!r} is named on it): "
                f"{RETRO_RULE}")
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
# The held retro: one slice cut from an active slice.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class RetroRecord:
    """One retro slice, held as data.

    The retro names the active slice it was
    held from, by slice id, its title, its
    verifiable checks, held as data, and its
    claims, named by retro id. The grain is
    derived, never stored: exactly one verifiable
    walk is written against the machine. A retro whose
    checks are not yet held stands with its
    checks empty: it stands open, named in
    its gaps, and no check is invented for it.
    The retro is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    retro_id: str
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
            self, "retro_id", _clean_text(self.retro_id, "a retro id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "slice_id", _clean_text(self.slice_id, "an slice id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a retro title"))
        object.__setattr__(
            self, "checks", _check_checks(self.checks))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a retro detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.retro_id

    @property
    def check(self) -> str:
        """The check the retro stands at: its last walked check."""
        return self.checks[-1] if self.checks else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "retro_id": self.retro_id, "seq": self.seq,
            "slice_id": self.slice_id, "title": self.title,
            "checks": list(self.checks),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_retro_ref(value: Any) -> RetroRecord:
    if not isinstance(value, RetroRecord):
        raise ValueError("a retro must be a RetroRecord")
    return value


def validate_retro(retro: Any) -> RetroRecord:
    return _check_retro_ref(retro)


def build_retro(record: Any = None, **kwargs: Any) -> RetroRecord:
    """Build one held retro from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, RetroRecord):
        if kwargs:
            raise ValueError("a retro stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a retro must be a mapping or a RetroRecord")
    _needed(data, _RUN_KEYS, "a retro")
    return RetroRecord(
        retro_id=data.get("retro_id"), seq=data.get("seq"),
        slice_id=data.get("slice_id"), title=data.get("title"),
        checks=data.get("checks"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_provenance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each retro to the steps it took outside the machine.

    Derived from the held retros alone: a break is
    one consecutive pair of walked checks the
    explicit gate sequence does not allow, told
    in walk order as before, then after.
    """
    found: Dict[str, Tuple[str, ...]] = {}
    for retro in book.retros:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(retro.checks, retro.checks[1:])
            if not legal_step(before, after))
        if breaks:
            found[retro.retro_id] = breaks
    return found

def retro_gaps(retro: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a retro from standing complete.

    Mapped from the retro's own held fields alone -
    its walked steps against the explicit question
    sequence, and its carried evidence against the
    filed vocabulary: the retro opens at
    named, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a retro stands complete only when it has
    reached filed. The source names nothing
    further: no gap is borrowed from another
    retro.
    """
    distilled = _check_retro_ref(retro)
    gaps: List[str] = []
    if not distilled.checks:
        gaps.append(
            "has passed through no step: the retro has not started")
        return tuple(gaps)
    if distilled.checks[0] != "opened":
        gaps.append(
            f"opens at {distilled.checks[0]}, not at opened: "
            f"the retro opens with the reflection")
    for before, after in zip(distilled.checks, distilled.checks[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"retro sequence does not allow")
    for kind in distilled.claims:
        if kind in BARE_CLAIMS:
            gaps.append(
                f"carries a {kind} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if distilled.checks[-1] != "filed":
        gaps.append(
            f"has not reached filed: the retro stands "
            f"at {distilled.checks[-1]}")
    return tuple(gaps)

def retro_green(retro: Any, source: Any = None) -> bool:
    return not retro_gaps(retro, source)


def plain_lines(retro: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the retro's own fields."""
    distilled = _check_retro_ref(retro)
    return (
        f"Retro: {distilled.title}",
        f"Slice: {distilled.slice_id}",
        f"Check: {distilled.check if distilled.check else 'none'}",
        f"Claims: "
        f"{', '.join(distilled.claims) if distilled.claims else 'none'}",
    )


def segment_of(retro: Any, source: Any = None) -> str:
    distilled = _check_retro_ref(retro)
    gaps = retro_gaps(distilled, source)
    return (
        f"{distilled.retro_id}: {distilled.title} - slice: "
        f"'{distilled.slice_id}' - check: "
        f"'{distilled.check if distilled.check else 'none'}' - "
        f"checks: {len(distilled.checks)} - claims: "
        f"'{', '.join(distilled.claims) if distilled.claims else 'none'}' - "
        f"detail: '{distilled.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held slice reference: the active slice a book retros from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class SliceRef:
    """One slice a retro book retros from, held as a reference.

    The record names the slice, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 slice book's own telling. A retro
    stands only from an active reference: the
    book refuses a retro naming no held reference,
    and a retro from an queued one, BY NAME.
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
    human active - the slice's retro ids in
    derived claim order, held exactly as
    active. The trace is of the set and its
    order, never of a step: when the derived
    trace moves, this record stands stale, named
    in the board, until a new trace is active.
    """

    trace_id: str
    seq: int
    retro_id: str
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
            self, "retro_id", _clean_text(self.retro_id, "an slice id"))
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
            "retro_id": self.retro_id, "trace": self.trace,
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
        retro_id=data.get("retro_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a retro, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One retro stance, held as data.

    The record names its retro, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per retro stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    retro_id: str
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
            self, "retro_id", _clean_text(self.retro_id, "a retro id"))
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
            "retro_id": self.retro_id, "stance": self.stance,
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
        retro_id=data.get("retro_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which slices a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class RetroView:
    """A view over the book: every retro, the green, the rest."""

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


def _check_view_ref(value: Any) -> RetroView:
    if not isinstance(value, RetroView):
        raise ValueError("a view must be an RetroView")
    return value


def validate_view(view: Any) -> RetroView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> RetroView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, RetroView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an RetroView")
    _needed(data, _VIEW_KEYS, "a view")
    return RetroView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class RetroPanelRow:
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


def _row_for_retro(retro: RetroRecord,
                     source: Any = None) -> RetroPanelRow:
    return RetroPanelRow(
        item_id=retro.retro_id,
        standing="complete" if retro_green(retro, source) else "open",
        label=retro.title, segment=segment_of(retro, source),
        recorded_on=retro.recorded_on)


def _check_row_ref(value: Any) -> RetroPanelRow:
    if not isinstance(value, RetroPanelRow):
        raise ValueError("a panel row must be an RetroPanelRow")
    return value


def validate_row(row: Any, retro: Any = None,
                 source: Any = None) -> RetroPanelRow:
    distilled = _check_row_ref(row)
    if retro is not None:
        derived = _row_for_retro(_check_retro_ref(retro), source)
        if distilled != derived:
            raise ValueError(
                f"panel row {distilled.item_id!r} does not agree with "
                f"the row derived from its retro")
    return distilled


def build_row(row: Any = None, retro: Any = None,
              source: Any = None,
              **kwargs: Any) -> RetroPanelRow:
    if retro is not None:
        derived = _row_for_retro(_check_retro_ref(retro), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            RetroPanelRow(**kwargs))
        return validate_row(built, retro, source)
    if isinstance(row, RetroPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return RetroPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return RetroPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an RetroPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[RetroPanelRow, ...]
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
        f"The retro book holds {total_items} retros as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown retros "
        f"stand complete.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its retro's own fields "
        "- the slice it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any retro.",
        "Completeness is written from the held records alone: "
        "a retro that steps outside the retro sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not reached filed stands open, named in its "
        "gaps, and the retro index is derived from the "
        "held retros, never stored where it could drift.",
    )

@dataclass(frozen=True)
class RetroPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[RetroPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> RetroView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, RetroView):
        return view
    return book.view_for(view)


def shown_retros(source: Any, view: Any = None
                   ) -> Tuple[RetroRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.retros
    if resolved.view_filter == "complete":
        return tuple(g for g in book.retros if retro_green(g, book))
    return tuple(g for g in book.retros if not retro_green(g, book))


def retros_for_slice(source: Any, slice_id: Any
                      ) -> Tuple[RetroRecord, ...]:
    wanted = _clean_text(slice_id, "an slice id")
    return tuple(
        g for g in _source_book(source).retros if g.slice_id == wanted)


def green_retros(source: Any) -> Tuple[RetroRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.retros if retro_green(g, book))


def current_retro(source: Any) -> Optional[RetroRecord]:
    """The book's current retro, DERIVED at call time.

    The first held retro, in held order, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held retros alone, so it can
    never go stale against them. A book whose every
    retro stands complete has no current retro.
    """
    book = _source_book(source)
    for retro in book.retros:
        if not retro_green(retro, book):
            return retro
    return None


def derive_panel(source: Any, view: Any = None) -> RetroPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_retros(book, resolved)
    rows = tuple(_row_for_retro(retro, book) for retro in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.retros), default="")
    green = sum(1 for g in shown if retro_green(g, book))
    return RetroPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.retros), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.retros), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> RetroPanel:
    if not isinstance(value, RetroPanel):
        raise ValueError("a panel must be an RetroPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> RetroPanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 lesson).
    """
    distilled = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(distilled.view_id)
                if distilled.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(distilled, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {distilled.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return distilled


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> RetroPanel:
    if isinstance(panel, RetroPanel):
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
        built = RetroPanel(
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
    raise ValueError("a panel must be a mapping, an RetroPanel, or derived")


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
        return "filed"
    if green_shown == 0:
        return "blocked"
    return "held"


@dataclass(frozen=True)
class RetroVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> RetroVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_retros(book, resolved)
    green = sum(1 for g in shown if retro_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return RetroVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> RetroVerdict:
    if not isinstance(value, RetroVerdict):
        raise ValueError("a verdict must be an RetroVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> RetroVerdict:
    distilled = _check_verdict_ref(verdict)
    if distilled.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {distilled.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(distilled.view_id)
                if distilled.view_id is not None else None)
        derived = derive_verdict(book, view)
        if distilled != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return distilled


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> RetroVerdict:
    if isinstance(verdict, RetroVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = RetroVerdict(
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
        "a verdict must be a mapping, an RetroVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held slices' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    check: str
    retro_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "check": self.check, "retro_id": self.retro_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class RetroIndex:
    """The retro index, derived from the held retros.

    The index names one entry per green retro, in
    held order - the retro's own one verifiable
    check, its retro id and its title - and the
    retros that do not stand complete, named in its
    gaps. Nothing here is stored on any retro: the
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


def derive_index(source: Any) -> RetroIndex:
    """Derive the retro index from the book's held retros."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(check=g.check, retro_id=g.retro_id,
                   title=g.title)
        for g in book.retros if retro_green(g, book))
    gaps = tuple(
        g.retro_id for g in book.retros if not retro_green(g, book))
    return RetroIndex(entries=entries, gaps=gaps)


def retro_for_check(source: Any, check: Any) -> Optional[RetroRecord]:
    """The first held retro one check reaches, or none - honestly."""
    if check is None:
        return None
    if not isinstance(check, str):
        raise ValueError("an check must be a string naming the check")
    wanted = check.strip()
    if not wanted:
        return None
    for retro in _source_book(source).retros:
        if retro.check == wanted:
            return retro
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held order: the retro
    that took it and the step it took, before,
    then after. A book whose retros all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{retro_id}: {step}"
        for retro_id, steps in _breaks_map(book).items()
        for step in steps)

def retro_order(source: Any,
              slice_id: Any = None) -> Tuple[RetroRecord, ...]:
    """The held retros in their held order, DERIVED at call time.

    Retros stand in the order the book holds them -
    the order their slices were taken - optionally
    for one slice alone. Nothing here is stored:
    the order is the book's own held order, told.
    """
    book = _source_book(source)
    retros = list(book.retros)
    if slice_id is not None:
        wanted = _clean_text(slice_id, "a slice id")
        retros = [r for r in retros if r.slice_id == wanted]
    return tuple(retros)

def trace_of(source: Any, retro_id: Any) -> str:
    """One retro's trace, DERIVED at call time.

    The retro's walked checks joined as one trace
    line, in walk order. A retro that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is named
    elsewhere.
    """
    retro = _source_book(source).retro_for(retro_id)
    return " > ".join(retro.checks)

def trace_for_retro(source: Any,
                  retro_id: Any) -> Optional[TraceRecord]:
    """The held trace for one retro, or none - honestly."""
    wanted = _clean_text(retro_id, "a retro id")
    for record in _source_book(source).traces:
        if record.retro_id == wanted:
            return record
    return None

def trace_current(source: Any, retro_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_retro(source, retro_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, retro_id)

def note_for_retro(source: Any, retro_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one retro (and stance, when named)."""
    wanted = _clean_text(retro_id, "a retro id")
    for record in _source_book(source).notes:
        if record.retro_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the slice targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def board_record(source: Any = None) -> Dict[str, Any]:
    """The retro board, DERIVED here from the held retros alone.

    The board counts the held retros by their
    derived completeness - green and red - names
    the current retro, the first that does not yet
    stand complete, tells each held retro's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held retros took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.retros
            if ("complete" if retro_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "retros": number})
    current = current_retro(book)
    traces = []
    for retro in book.retros:
        trace = trace_for_retro(book, retro.retro_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, retro.retro_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"retro_id": retro.retro_id, "trace": standing})
    return {
        "type": "retro_board",
        "slice": RETRO_SLICE,
        "standings": standings,
        "total": len(book.retros),
        "current_retro": current.retro_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This slice's own roadmap standing, proved from the roadmap itself.

    The record loads this repo's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 slices in 11 parts,
    the opened prefix, the next slice where the
    campaign resumes, and M-213's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(RETRO_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "retro_roadmap",
        "slice": RETRO_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m213_title": own.title,
        "m213_part": own.part,
        "m213_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: slices, retros, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or order ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class RetroBook:
    title: str
    slices: Tuple[SliceRef, ...] = ()
    retros: Tuple[RetroRecord, ...] = ()
    views: Tuple[RetroView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[RetroPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        slices = tuple(_check_slice_ref(g) for g in self.slices)
        retros = tuple(_check_retro_ref(g) for g in self.retros)
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
        retro_ids = set()
        retro_seqs = set()
        for retro in retros:
            if retro.retro_id in retro_ids:
                raise ValueError(
                    f"two retros stand under id {retro.retro_id!r}")
            if retro.seq in retro_seqs:
                raise ValueError(
                    f"two retros stand at sequence {retro.seq}")
            retro_ids.add(retro.retro_id)
            retro_seqs.add(retro.seq)
        by_slice = {ref.slice_id: ref for ref in slices}
        for retro in (retros if slices else ()):

            ref = by_slice.get(retro.slice_id)
            if ref is None:
                raise ValueError(
                    f"retro {retro.retro_id!r} is held from slice "
                    f"{retro.slice_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "active":
                raise ValueError(
                    f"retro {retro.retro_id!r} is held from slice "
                    f"{retro.slice_id!r}, which is not active: "
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
            target = (record.retro_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for retro "
                    f"{record.retro_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per retro target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_retros = set()
        retro_ids = {retro.retro_id for retro in retros}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.retro_id in trace_retros:
                raise ValueError(
                    f"two traces stand for retro "
                    f"{record.retro_id!r}: one trace stands "
                    f"per retro walk")
            if retros and record.retro_id not in retro_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces retro "
                    f"{record.retro_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_retros.add(record.retro_id)
        object.__setattr__(
            self, "slices", tuple(sorted(slices, key=lambda g: g.seq)))
        object.__setattr__(
            self, "retros", tuple(sorted(retros, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.retros + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.retro_id for g in self.retros) + tuple(
            v.view_id for v in self.views)

    def retro_ids(self) -> Tuple[str, ...]:
        return tuple(g.retro_id for g in self.retros)

    def slice_ids(self) -> Tuple[str, ...]:
        return tuple(g.slice_id for g in self.slices)

    def retro_for(self, retro_id: Any) -> RetroRecord:
        wanted = _clean_text(retro_id, "a retro id")
        for retro in self.retros:
            if retro.retro_id == wanted:
                return retro
        raise KeyError(f"no retro named {wanted!r} stands in this book")

    def slice_for(self, slice_id: Any) -> SliceRef:
        wanted = _clean_text(slice_id, "an slice id")
        for ref in self.slices:
            if ref.slice_id == wanted:
                return ref
        raise KeyError(f"no slice named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> RetroView:
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
        for retro in self.retros:
            if retro.retro_id == wanted:
                return retro
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "slices": [g.to_record() for g in self.slices],
            "retros": [g.to_record() for g in self.retros],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: RetroBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: RetroBook) -> None:
    if book.title != "Retrospectives at the M-212 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.slices) != 3 or len(book.retros) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three slice references, five retros and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m212-boundary":
        raise ValueError("the pinned panel is panel-m212-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.check for e in index.entries] != ["filed", "filed", "filed"]:
        raise ValueError("the shipped example book index must derive the three held complete retros in held order")
    if index.gaps != ("retro-bare-lesson", "retro-leaping-lesson"):
        raise ValueError("the shipped example book must leave the bare and leaping retros honestly open, named in its gaps")
    found = retro_for_check(book, EXAMPLE_CHECK)
    if found is None or found.retro_id != "retro-held-lesson":
        raise ValueError("the shipped example book must reach its opening retro under the example check")
    if trace_of(book, "retro-held-lesson") != "opened > reflected > written > distilled > filed":
        raise ValueError("the shipped example book must derive the opening retro's trace from its walked steps")
    if not trace_current(book, "retro-held-lesson"):
        raise ValueError("the shipped example book must hold the opening retro's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note road")

def validate_book(data: Any, *, require_example: bool = False) -> RetroBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, RetroBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a retro book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live slice build or execution "
                f"({key!r} is named on it): {RETRO_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its retros under a view")
    if "retro_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held retros at call time")
    if "board" in data or "current_retro" in data:
        raise ValueError(
            "a book stores no board and no current retro: both are "
            "derived from its held retros at call time")
    if "trace" in data or "order" in data:
        raise ValueError(
            "a book stores no trace and no order: both are derived "
            "from its held retros at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != RETRO_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{RETRO_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != RETRO_SLICE):
        raise ValueError(
            f"a book's slice must be {RETRO_SLICE!r}")
    head = data.get("retro_head") or data.get("retrospectives") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's retro head must be a mapping")
    title = head.get("title") or data.get("title")
    slices = tuple(build_slice_ref(g) for g in data.get("slices") or ())
    retros = tuple(build_retro(g) for g in data.get("retros") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = RetroBook(
        title=title, slices=slices, retros=retros, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = RetroBook(
        title=book.title, slices=book.slices, retros=book.retros,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> RetroBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (RetroBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an RetroBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> RetroBook:
    return validate_book(data, require_example=require_example)


def load_retro(
        data: Optional[Dict[str, Any]] = None) -> RetroBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(RETRO_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_retro_file(path: Any) -> RetroBook:
    """Load one retro file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: slice references, retros and views held one by one.
# ---------------------------------------------------------------------

class RetroRegistry:
    """An in-memory holding of slice references, retros and views.

    The registry is the pure layer's model of a
    session's retro book: slice references are
    held under their ids, retros are held under
    their ids, one retro per id and per sequence,
    and views are held in recorded order, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[SliceRef] = []
        self._retros: List[RetroRecord] = []
        self._views: List[RetroView] = []
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
        """Hold one slice reference, written whole before held."""
        distilled = _check_slice_ref(item)
        return self._register(
            self._slices, distilled, "slice_id", "slice reference")

    def register_retro(self, item: Any) -> RetroRecord:
        """Hold one retro, written whole before held."""
        distilled = _check_retro_ref(item)
        return self._register(
            self._retros, distilled, "retro_id", "retro")

    def register_view(self, view: Any) -> RetroView:
        """Hold one view; a view naming no id takes a fresh one."""
        distilled = _check_view_ref(view)
        if not distilled.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            distilled = build_view({**distilled.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, distilled, "view_id", "view")

    def register_book(self, book: Any) -> RetroBook:
        """Hold a whole book's records, under its title."""
        distilled = build_book(book)
        if self._title is not None and distilled.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {distilled.title!r}")
        for ref in distilled.slices:
            self.register_slice_ref(ref)
        for retro in distilled.retros:
            self.register_retro(retro)
        for view in distilled.views:
            self.register_view(view)
        self._title = distilled.title
        return self.book()

    def book(self) -> RetroBook:
        return RetroBook(
            title=self._title or "An unheld retro book",
            slices=tuple(self._slices), retros=tuple(self._retros),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[SliceRef, ...]:
        return tuple(self._slices)

    def list_retros(self) -> Tuple[RetroRecord, ...]:
        return tuple(self._retros)

    def list_views(self) -> Tuple[RetroView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._retros) + tuple(self._views)

    def get_slice(self, slice_id: Any) -> SliceRef:
        return self.book().slice_for(slice_id)

    def get_retro(self, retro_id: Any) -> RetroRecord:
        return self.book().retro_for(retro_id)

    def get_view(self, view_id: Any) -> RetroView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the journal target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> RetroBook:
    if source is None:
        return load_retro()
    if isinstance(source, RetroBook):
        return source
    if isinstance(source, RetroRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def retro_record(retro: Any, source: Any = None) -> Dict[str, Any]:
    distilled = _check_retro_ref(retro)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "retro_retro",
        "slice": RETRO_SLICE,
        "retro_id": distilled.retro_id,
        "slice_id": distilled.slice_id,
        "title": distilled.title,
        "segment": segment_of(distilled, book),
        "complete": retro_green(distilled, book),
        "gaps": list(retro_gaps(distilled, book)),
    }
    record.update(_provenance_record(distilled))
    return record


def slice_record(ref: Any) -> Dict[str, Any]:
    distilled = _check_slice_ref(ref)
    record = {
        "type": "retro_slice",
        "slice": RETRO_SLICE,
        "slice_id": distilled.slice_id,
        "title": distilled.title,
        "state": distilled.state,
    }
    record.update(_provenance_record(distilled))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    distilled = _check_trace_ref(record_in)
    record = {
        "type": "retro_trace",
        "slice": RETRO_SLICE,
        "trace_id": distilled.trace_id,
        "retro_id": distilled.retro_id,
        "trace": distilled.trace,
    }
    record.update(_provenance_record(distilled))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    distilled = _check_view_ref(view)
    record = {
        "type": "retro_view",
        "slice": RETRO_SLICE,
        "view_id": distilled.view_id, "seq": distilled.seq,
        "view_filter": distilled.view_filter,
    }
    record.update(_provenance_record(distilled))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    distilled = _check_note_ref(record_in)
    record = {
        "type": "retro_note",
        "slice": RETRO_SLICE,
        "note_id": distilled.note_id,
        "retro_id": distilled.retro_id,
        "stance": distilled.stance,
    }
    record.update(_provenance_record(distilled))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    distilled = validate_panel(panel, source)
    record = {"type": "retro_panel",
              "slice": RETRO_SLICE}
    record.update(distilled.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, RetroVerdict):
        distilled = validate_verdict(verdict, source)
    else:
        distilled = derive_verdict(_source_book(verdict), view)
    record = {"type": "retro_verdict",
              "slice": RETRO_SLICE}
    record.update(distilled.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, RetroIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "retro_index",
              "slice": RETRO_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    distilled = _source_book(book)
    record = {"type": "retro_book",
              "slice": RETRO_SLICE,
              "title": distilled.title}
    record.update(distilled.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(retro: Any, source: Any = None) -> str:
    distilled = _check_retro_ref(retro)
    return (
        f"{distilled.title} - from {distilled.slice_id}: "
        f"check {distilled.check if distilled.check else 'none'}, "
        f"claims "
        f"{', '.join(distilled.claims) if distilled.claims else 'none'}. "
        f"{distilled.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The retros stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"retros stand complete.")


def view_plain_words(view: Any) -> str:
    distilled = _check_view_ref(view)
    return f"View {distilled.view_id}: shows {distilled.view_filter} retros."


def note_plain_words(record_in: Any) -> str:
    distilled = _check_note_ref(record_in)
    return (
        f"Note {distilled.note_id}: {distilled.stance} "
        f"{distilled.retro_id}, toward {distilled.target}. "
        f"{distilled.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, RetroIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} green retros; "
        f"red, named in its gaps: {gaps}.")

def format_retro(retro: Any, source: Any = None) -> str:
    distilled = _check_retro_ref(retro)
    book = _source_book(source) if source is not None else None
    lines = [f"{distilled.title} ({distilled.retro_id})"]
    lines.extend(plain_lines(distilled))
    lines.append(distilled.detail)
    if retro_green(distilled, book):
        lines.append(
            "This retro stands complete - it walked the question "
            "sequence in the open from opened to filed, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This retro stands open - it stands named in "
            f"its gaps: {', '.join(retro_gaps(distilled, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    distilled = _check_view_ref(view)
    return (
        f"View {distilled.view_id}: filter {distilled.view_filter} - "
        f"{distilled.detail}")


def format_note(record_in: Any) -> str:
    distilled = _check_note_ref(record_in)
    lines = [
        f"Retro note {distilled.stance} {distilled.retro_id} "
        f"({distilled.note_id}): {distilled.title}. {distilled.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_check(source: Any, check: Any) -> str:
    retro = retro_for_check(source, check)
    if retro is not None:
        return format_retro(retro, source)
    wanted = check.strip() if isinstance(check, str) else check
    return (
        f"No held retro stands under check {wanted!r} yet - the "
        f"check reaches nothing in this book, and no retro is "
        f"invented for it.")


def format_book(source: Any = None, slice_id: Any = None) -> str:
    book = _source_book(source)
    retros = (retros_for_slice(book, slice_id)
              if slice_id is not None else book.retros)
    lines = [f"The Retro Gate (M-213) - {book.title}"]
    lines.extend(segment_of(retro, book) for retro in retros)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Retro panel under view {panel.view_id}:"]
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
    lines = ["Retro index, derived from the held retros:"]
    for entry in index.entries:
        lines.append(f"{entry.check} - {entry.title} ({entry.retro_id})")
    if index.gaps:
        lines.append(
            "Red, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_retro_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Retro Gate (M-213)",
        f"{book.title}: {len(book.retros)} retros held, "
        f"{len(green_retros(book))} retros standing green, "
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


def parse_retro_args(args: Any) -> Tuple[str, Any]:
    """Parse the /retro grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("retro", "view", "note"):
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
