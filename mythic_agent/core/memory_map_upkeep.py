"""The memory-map upkeep (roadmap slice M-211).

Part IX - The Mythic Method Engine. The roadmap
words: *the Scribe updates the Project Memory Map in
the same session as each banked slice (Mythic
law) - the map is never a later chore.*

What already ships, and what this slice adds:

* The memory-map upkeep already binds the work in
  prose - when the human asks a question, the
  question is answered first, plainly and fully,
  its first sentence the direct answer itself,
  and only then does work resume - and this
  slice WIRES it into the loop as data, in its
  own module, standing in the M-195 copy-and-
  share book shape the M-210 book stands in: one
  scribe per campaign, and the scribe's
  charge over one named question held as a
  book - a upkeep. The shipped roads stand
  untouched behind their seams: this layer holds
  upkeeps as data over the campaign's
  slices and rewrites none of them, and the
  prose law keeps its own standing.

* No charter row names this slice: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-211 on no row, and the
  slice tests pin that absence live. The M-005
  method charter names no slice row either: its
  own words name the whole of Part IX as the
  part that executes the charter, and this slice
  is built to the roadmap words and that
  execution note together. The law itself is
  held as data in the roadmap's own wording -
  the upkeep names its question and carries
  the answer it was mapped against.

* A upkeep is held whole: the slice it
  answers for, named by its slice id; its title;
  the question steps it walked, held as data in
  walk order; and the evidence it carries, held
  as data by kind. The question walk is
  EXPLICIT: its sequence stands as data
  (:data:`CHECKS`, :data:`TRANSITIONS`) -
  banked, noted, mapped, checked, sealed -
  and a upkeep's standing is DERIVED at
  call time from its held steps and evidence
  alone: a upkeep that opens anywhere but banked, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet reached sealed
  stands open, named in its gaps. The campaign
  pauses for the question: an answer stands
  complete only where the walk noted, the
  answer was mapped plain-first - its first
  sentence the direct answer - and the delivery
  is held as evidence.
* The evidence is a closed vocabulary in two
  halves: the held evidence - map_ref,
  slice_ref, entry_record, ledger_row,
  evidence an scribe can point to - and the
  bare claims - feeling, memory, assertion,
  summary, which stand as no evidence at all. An
  answer is mapped from held evidence alone,
  never from a feeling: a upkeep holding a
  bare claim stands open, named in its gaps.
* A upkeep stands only for an ACTIVE slice.
  The book holds each slice it answers for as a
  reference record - its id, its title and its
  standing, active or queued, held as data
  copied from the roadmap's own telling. A
  upkeep naming a slice that stands nowhere
  in the book refuses BY NAME, and a upkeep
  for a slice that is not active refuses BY NAME
  beside it: the scribe deals with the slice
  in hand, in roadmap order, never a queued one,
  and a slice whose question already stands
  complete is never answered twice - the current
  upkeep is derived, so a completed slice
  is never the current answering twice.
* The upkeep's trace is visible. A trace
  record holds one upkeep's walked steps as
  one trace line, exactly as walked, beside the
  upkeep. The derived trace is computed at
  call time from the upkeep's held steps; a
  held trace that no longer agrees with it
  stands stale, named in the board - the trace
  is the walk itself, never a retelling of it.
* The upkeep index is DERIVED at call time
  from the held upkeeps - one entry per
  complete upkeep, under the step it stands
  at - never a second stored copy that could
  drift. A stored index, standing verdict,
  panel, trace, order or current-upkeep
  claim on any record refuses by name.
* The current upkeep is DERIVED at call
  time - the first held upkeep, in held
  order, that does not yet stand complete - never
  stored where it could go stale: that is the
  question the scribe must answer next, and
  the next slice is dealt only when the current
  one resumes.
* The notes are held as data: a note record
  naming its upkeep, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per upkeep stance; holding a
  note posts none of it, the rule stands as data
  (:data:`UPKEEP_RULE`), and a record
  claiming a question was actually answered,
  checked or sealed live refuses BY NAME.
  The scribe reports - and those reports, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the shape a real answer file takes,
  a loader reads an answer file anywhere on
  disk, upkeeps and views are shaped as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding an answer book for a session and
  telling from it. This layer reaches no live
  road: it answers no question live, pauses no
  campaign, resumes no work, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security, spawns
  no process and opens no network - it holds
  upkeeps as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The question walk is explicit.** A
  upkeep is mapped against the held steps
  and legal steps alone; an illegal step stands
  named in its gaps, never silently reordered.
* **Complete stands on held evidence alone.** A
  upkeep that carries a feeling, a memory,
  an assertion or a summary in place of held
  evidence stands open, named in its gaps: an
  answer is mapped from evidence, not vibes.
* **Active slices only, in roadmap order.** A
  upkeep for a missing or queued slice
  refuses by name; no upkeep is invented
  for a slice the scribe has not dealt with.
* **Unknown stays unknown.** A upkeep whose
  steps are not yet held stands with its steps
  empty - no step is invented.
* **The index, panel, verdict, trace, order
  and current upkeep are derived, never
  stored.** Each is derived from the held
  upkeeps at call time; a stored one
  refuses by name, so it can never drift.
* **One upkeep per upkeep.** Two
  upkeeps standing for one upkeep id
  refuse by name, and one note record stands per
  upkeep stance.
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
    "UPKEEP_RESOURCE",
    "UPKEEP_SCHEMA",
    "UPKEEP_SLICE",
    "UPKEEP_RULE",
    "PLAIN_EXPLANATION",
    "THE_UPKEEP_SLICE",
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
    "UpkeepRecord",
    "IndexEntry",
    "SliceRef",
    "NoteRecord",
    "UpkeepBook",
    "UpkeepIndex",
    "UpkeepPanel",
    "UpkeepPanelRow",
    "UpkeepRegistry",
    "UpkeepVerdict",
    "UpkeepView",
    "TargetCount",
    "trace_for_upkeep",
    "trace_record",
    "board_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_upkeep",
    "build_slice_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_upkeep",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "upkeep_for_check",
    "upkeep_order",
    "upkeep_record",
    "first_note",
    "format_book",
    "format_upkeep",
    "format_index",
    "format_note",
    "format_check",
    "format_panel",
    "format_upkeep_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "slice_record",
    "load_upkeep",
    "load_upkeep_file",
    "normalize_slice_state",
    "normalize_check",
    "normalize_claim_kind",
    "legal_step",
    "next_check",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_upkeep",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_upkeep_args",
    "green_upkeeps",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_upkeeps",
    "validate_trace",
    "validate_book",
    "validate_upkeep",
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
    "upkeep_gaps",
    "upkeep_green",
    "upkeeps_for_slice",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

UPKEEP_SCHEMA = "mythic.memory_map_upkeep/1"
UPKEEP_SLICE = "M-211"
THE_UPKEEP_SLICE = UPKEEP_SLICE
UPKEEP_RESOURCE = "memory_map_upkeep.yaml"
INDEX_ACTION = "index"
EXAMPLE_CHECK = "sealed"
CHECK_FIELDS = ("checks", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("sealed", "held", "blocked")
SLICE_STATES = ("active", "queued")
UPKEEP_RULE = (
    "upkeeps are held as data alone: the Scribe "
    "updates the Project Memory Map in the same "
    "session as each banked slice - the map is "
    "never a later chore - the upkeep walk stands "
    "as an explicit upkeep sequence - banked, "
    "noted, mapped, checked, sealed - and an "
    "update completes only complete, complete "
    "being a state with evidence held - slice "
    "ref, map ref, entry record, ledger row - "
    "never a feeling, a memory, an assertion or "
    "a summary; holding, viewing and reading an "
    "upkeep updates no map live, banks no slice, "
    "files no report and opens no network")
PLAIN_EXPLANATION = (
    "The memory-map upkeep (M-211): the Scribe "
    "updates the Project Memory Map in the same "
    "session as each banked slice (Mythic law) - "
    "the map is never a later chore.")
USAGE = (
    "Usage: /mapupkeep | /mapupkeep upkeep <upkeep-id> | "
    "/mapupkeep check <check> | /mapupkeep slice <slice-id> | "
    "/mapupkeep view <view-id> | /mapupkeep note <note-id> | "
    "/mapupkeep index | /mapupkeep panel | /mapupkeep verdict")

CHECKS = ("banked", "noted", "mapped", "checked", "sealed")
HELD_EVIDENCE = ("slice_ref", "map_ref", "entry_record", "ledger_row")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "banked": ("noted",),
    "noted": ("mapped",),
    "mapped": ("checked",),
    "checked": ("banked", "sealed"),
    "sealed": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a failure or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a upkeep stands complete.
    A check outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_check(check: Any, failed: Any = False) -> Optional[str]:
    """The step the scribe takes next, DERIVED from the sequence.

    Banked leads to noted and noted to
    mapped; mapped leads to checked; at
    checked a follow-up banking steps back to banked and a finished update steps to sealed;
    sealed is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    checked = normalize_check(check)
    if checked == "banked":
        return "noted"
    if checked == "noted":
        return "mapped"
    if checked == "mapped":
        return "checked"
    if checked == "checked":
        return "banked" if failed else "sealed"
    return None


_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "upkeep_id", "seq", "slice_id", "title", "checks",
    "claims", "detail",
} | set(_PROVENANCE))
_SLICE_REF_KEYS = frozenset({
    "slice_id", "seq", "title", "state", "detail",
} | set(_PROVENANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "upkeep_id", "trace", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "upkeep_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered",
    "current_upkeep", "next_upkeep", "progress", "board",
    "current", "order", "breaks", "active"})
_LIVE_KEYS = (
    "live_upkeep", "upkeeps_live", "live_question",
    "upkeeps_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "resumes_live",
    "resumed_live", "pauses_campaign", "paused_live",
    "runs_campaign", "ran_campaign", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "upkeep_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_upkeep", "sent_upkeep",
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
    """A upkeep's walked checks, held as data.

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
    """A upkeep's asked claims: claim kinds named as data.

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
                f"{what} claims a live gate upkeep or slice build "
                f"execution ({key!r} is named on it): "
                f"{UPKEEP_RULE}")
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
# The held upkeep: one slice cut from an active slice.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class UpkeepRecord:
    """One upkeep slice, held as data.

    The upkeep names the active slice it was
    upkeeped from, by slice id, its title, its
    verifiable checks, held as data, and its
    claims, named by upkeep id. The grain is
    derived, never stored: exactly one verifiable
    walk is mapped against the machine. A upkeep whose
    checks are not yet held stands with its
    checks empty: it stands open, named in
    its gaps, and no check is invented for it.
    The upkeep is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    upkeep_id: str
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
            self, "upkeep_id", _clean_text(self.upkeep_id, "a upkeep id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "slice_id", _clean_text(self.slice_id, "an slice id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a upkeep title"))
        object.__setattr__(
            self, "checks", _check_checks(self.checks))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a upkeep detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.upkeep_id

    @property
    def check(self) -> str:
        """The check the upkeep stands at: its last walked check."""
        return self.checks[-1] if self.checks else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "upkeep_id": self.upkeep_id, "seq": self.seq,
            "slice_id": self.slice_id, "title": self.title,
            "checks": list(self.checks),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_upkeep_ref(value: Any) -> UpkeepRecord:
    if not isinstance(value, UpkeepRecord):
        raise ValueError("a upkeep must be a UpkeepRecord")
    return value


def validate_upkeep(upkeep: Any) -> UpkeepRecord:
    return _check_upkeep_ref(upkeep)


def build_upkeep(record: Any = None, **kwargs: Any) -> UpkeepRecord:
    """Build one held upkeep from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, UpkeepRecord):
        if kwargs:
            raise ValueError("a upkeep stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a upkeep must be a mapping or a UpkeepRecord")
    _needed(data, _RUN_KEYS, "a upkeep")
    return UpkeepRecord(
        upkeep_id=data.get("upkeep_id"), seq=data.get("seq"),
        slice_id=data.get("slice_id"), title=data.get("title"),
        checks=data.get("checks"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_provenance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each upkeep to the steps it took outside the machine.

    Derived from the held upkeeps alone: a break is
    one consecutive pair of walked checks the
    explicit gate sequence does not allow, told
    in walk order as before, then after.
    """
    found: Dict[str, Tuple[str, ...]] = {}
    for upkeep in book.upkeeps:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(upkeep.checks, upkeep.checks[1:])
            if not legal_step(before, after))
        if breaks:
            found[upkeep.upkeep_id] = breaks
    return found

def upkeep_gaps(upkeep: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a upkeep from standing complete.

    Mapped from the upkeep's own held fields alone -
    its walked steps against the explicit question
    sequence, and its carried evidence against the
    closed vocabulary: the upkeep opens at
    named, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a upkeep stands complete only when it has
    reached sealed. The source names nothing
    further: no gap is borrowed from another
    upkeep.
    """
    checked = _check_upkeep_ref(upkeep)
    gaps: List[str] = []
    if not checked.checks:
        gaps.append(
            "has passed through no step: the upkeep has not started")
        return tuple(gaps)
    if checked.checks[0] != "banked":
        gaps.append(
            f"opens at {checked.checks[0]}, not at banked: "
            f"the upkeep opens with the question")
    for before, after in zip(checked.checks, checked.checks[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"upkeep sequence does not allow")
    for kind in checked.claims:
        if kind in BARE_CLAIMS:
            gaps.append(
                f"carries a {kind} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if checked.checks[-1] != "sealed":
        gaps.append(
            f"has not reached sealed: the upkeep stands "
            f"at {checked.checks[-1]}")
    return tuple(gaps)

def upkeep_green(upkeep: Any, source: Any = None) -> bool:
    return not upkeep_gaps(upkeep, source)


def plain_lines(upkeep: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the upkeep's own fields."""
    checked = _check_upkeep_ref(upkeep)
    return (
        f"Upkeep: {checked.title}",
        f"Slice: {checked.slice_id}",
        f"Check: {checked.check if checked.check else 'none'}",
        f"Claims: "
        f"{', '.join(checked.claims) if checked.claims else 'none'}",
    )


def segment_of(upkeep: Any, source: Any = None) -> str:
    checked = _check_upkeep_ref(upkeep)
    gaps = upkeep_gaps(checked, source)
    return (
        f"{checked.upkeep_id}: {checked.title} - slice: "
        f"'{checked.slice_id}' - check: "
        f"'{checked.check if checked.check else 'none'}' - "
        f"checks: {len(checked.checks)} - claims: "
        f"'{', '.join(checked.claims) if checked.claims else 'none'}' - "
        f"detail: '{checked.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held slice reference: the active slice a book upkeeps from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class SliceRef:
    """One slice a upkeep book upkeeps from, held as a reference.

    The record names the slice, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 slice book's own telling. A upkeep
    stands only from an active reference: the
    book refuses a upkeep naming no held reference,
    and a upkeep from an queued one, BY NAME.
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
    human active - the slice's upkeep ids in
    derived claim order, held exactly as
    active. The trace is of the set and its
    order, never of a step: when the derived
    trace moves, this record stands stale, named
    in the board, until a new trace is active.
    """

    trace_id: str
    seq: int
    upkeep_id: str
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
            self, "upkeep_id", _clean_text(self.upkeep_id, "an slice id"))
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
            "upkeep_id": self.upkeep_id, "trace": self.trace,
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
        upkeep_id=data.get("upkeep_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a upkeep, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One upkeep stance, held as data.

    The record names its upkeep, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per upkeep stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    upkeep_id: str
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
            self, "upkeep_id", _clean_text(self.upkeep_id, "a upkeep id"))
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
            "upkeep_id": self.upkeep_id, "stance": self.stance,
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
        upkeep_id=data.get("upkeep_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which slices a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class UpkeepView:
    """A view over the book: every upkeep, the green, the rest."""

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


def _check_view_ref(value: Any) -> UpkeepView:
    if not isinstance(value, UpkeepView):
        raise ValueError("a view must be an UpkeepView")
    return value


def validate_view(view: Any) -> UpkeepView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> UpkeepView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, UpkeepView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an UpkeepView")
    _needed(data, _VIEW_KEYS, "a view")
    return UpkeepView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class UpkeepPanelRow:
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


def _row_for_upkeep(upkeep: UpkeepRecord,
                     source: Any = None) -> UpkeepPanelRow:
    return UpkeepPanelRow(
        item_id=upkeep.upkeep_id,
        standing="complete" if upkeep_green(upkeep, source) else "open",
        label=upkeep.title, segment=segment_of(upkeep, source),
        recorded_on=upkeep.recorded_on)


def _check_row_ref(value: Any) -> UpkeepPanelRow:
    if not isinstance(value, UpkeepPanelRow):
        raise ValueError("a panel row must be an UpkeepPanelRow")
    return value


def validate_row(row: Any, upkeep: Any = None,
                 source: Any = None) -> UpkeepPanelRow:
    checked = _check_row_ref(row)
    if upkeep is not None:
        derived = _row_for_upkeep(_check_upkeep_ref(upkeep), source)
        if checked != derived:
            raise ValueError(
                f"panel row {checked.item_id!r} does not agree with "
                f"the row derived from its upkeep")
    return checked


def build_row(row: Any = None, upkeep: Any = None,
              source: Any = None,
              **kwargs: Any) -> UpkeepPanelRow:
    if upkeep is not None:
        derived = _row_for_upkeep(_check_upkeep_ref(upkeep), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            UpkeepPanelRow(**kwargs))
        return validate_row(built, upkeep, source)
    if isinstance(row, UpkeepPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return UpkeepPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return UpkeepPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an UpkeepPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[UpkeepPanelRow, ...]
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
        f"The upkeep book holds {total_items} upkeeps as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown upkeeps "
        f"stand complete.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its upkeep's own fields "
        "- the slice it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any upkeep.",
        "Completeness is mapped from the held records alone: "
        "a upkeep that steps outside the upkeep sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not reached sealed stands open, named in its "
        "gaps, and the upkeep index is derived from the "
        "held upkeeps, never stored where it could drift.",
    )

@dataclass(frozen=True)
class UpkeepPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[UpkeepPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> UpkeepView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, UpkeepView):
        return view
    return book.view_for(view)


def shown_upkeeps(source: Any, view: Any = None
                   ) -> Tuple[UpkeepRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.upkeeps
    if resolved.view_filter == "complete":
        return tuple(g for g in book.upkeeps if upkeep_green(g, book))
    return tuple(g for g in book.upkeeps if not upkeep_green(g, book))


def upkeeps_for_slice(source: Any, slice_id: Any
                      ) -> Tuple[UpkeepRecord, ...]:
    wanted = _clean_text(slice_id, "an slice id")
    return tuple(
        g for g in _source_book(source).upkeeps if g.slice_id == wanted)


def green_upkeeps(source: Any) -> Tuple[UpkeepRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.upkeeps if upkeep_green(g, book))


def current_upkeep(source: Any) -> Optional[UpkeepRecord]:
    """The book's current upkeep, DERIVED at call time.

    The first held upkeep, in held order, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held upkeeps alone, so it can
    never go stale against them. A book whose every
    upkeep stands complete has no current upkeep.
    """
    book = _source_book(source)
    for upkeep in book.upkeeps:
        if not upkeep_green(upkeep, book):
            return upkeep
    return None


def derive_panel(source: Any, view: Any = None) -> UpkeepPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_upkeeps(book, resolved)
    rows = tuple(_row_for_upkeep(upkeep, book) for upkeep in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.upkeeps), default="")
    green = sum(1 for g in shown if upkeep_green(g, book))
    return UpkeepPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.upkeeps), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.upkeeps), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> UpkeepPanel:
    if not isinstance(value, UpkeepPanel):
        raise ValueError("a panel must be an UpkeepPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> UpkeepPanel:
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
                **kwargs: Any) -> UpkeepPanel:
    if isinstance(panel, UpkeepPanel):
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
        built = UpkeepPanel(
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
    raise ValueError("a panel must be a mapping, an UpkeepPanel, or derived")


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
        return "sealed"
    if green_shown == 0:
        return "blocked"
    return "held"


@dataclass(frozen=True)
class UpkeepVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> UpkeepVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_upkeeps(book, resolved)
    green = sum(1 for g in shown if upkeep_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return UpkeepVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> UpkeepVerdict:
    if not isinstance(value, UpkeepVerdict):
        raise ValueError("a verdict must be an UpkeepVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> UpkeepVerdict:
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
                  **kwargs: Any) -> UpkeepVerdict:
    if isinstance(verdict, UpkeepVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = UpkeepVerdict(
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
        "a verdict must be a mapping, an UpkeepVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held slices' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    check: str
    upkeep_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "check": self.check, "upkeep_id": self.upkeep_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class UpkeepIndex:
    """The upkeep index, derived from the held upkeeps.

    The index names one entry per green upkeep, in
    held order - the upkeep's own one verifiable
    check, its upkeep id and its title - and the
    upkeeps that do not stand complete, named in its
    gaps. Nothing here is stored on any upkeep: the
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


def derive_index(source: Any) -> UpkeepIndex:
    """Derive the upkeep index from the book's held upkeeps."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(check=g.check, upkeep_id=g.upkeep_id,
                   title=g.title)
        for g in book.upkeeps if upkeep_green(g, book))
    gaps = tuple(
        g.upkeep_id for g in book.upkeeps if not upkeep_green(g, book))
    return UpkeepIndex(entries=entries, gaps=gaps)


def upkeep_for_check(source: Any, check: Any) -> Optional[UpkeepRecord]:
    """The first held upkeep one check reaches, or none - honestly."""
    if check is None:
        return None
    if not isinstance(check, str):
        raise ValueError("an check must be a string naming the check")
    wanted = check.strip()
    if not wanted:
        return None
    for upkeep in _source_book(source).upkeeps:
        if upkeep.check == wanted:
            return upkeep
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held order: the upkeep
    that took it and the step it took, before,
    then after. A book whose upkeeps all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{upkeep_id}: {step}"
        for upkeep_id, steps in _breaks_map(book).items()
        for step in steps)

def upkeep_order(source: Any,
              slice_id: Any = None) -> Tuple[UpkeepRecord, ...]:
    """The held upkeeps in their held order, DERIVED at call time.

    Upkeeps stand in the order the book holds them -
    the order their slices were taken - optionally
    for one slice alone. Nothing here is stored:
    the order is the book's own held order, told.
    """
    book = _source_book(source)
    upkeeps = list(book.upkeeps)
    if slice_id is not None:
        wanted = _clean_text(slice_id, "a slice id")
        upkeeps = [r for r in upkeeps if r.slice_id == wanted]
    return tuple(upkeeps)

def trace_of(source: Any, upkeep_id: Any) -> str:
    """One upkeep's trace, DERIVED at call time.

    The upkeep's walked checks joined as one trace
    line, in walk order. A upkeep that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is named
    elsewhere.
    """
    upkeep = _source_book(source).upkeep_for(upkeep_id)
    return " > ".join(upkeep.checks)

def trace_for_upkeep(source: Any,
                  upkeep_id: Any) -> Optional[TraceRecord]:
    """The held trace for one upkeep, or none - honestly."""
    wanted = _clean_text(upkeep_id, "a upkeep id")
    for record in _source_book(source).traces:
        if record.upkeep_id == wanted:
            return record
    return None

def trace_current(source: Any, upkeep_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_upkeep(source, upkeep_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, upkeep_id)

def note_for_upkeep(source: Any, upkeep_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one upkeep (and stance, when named)."""
    wanted = _clean_text(upkeep_id, "a upkeep id")
    for record in _source_book(source).notes:
        if record.upkeep_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the slice targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def board_record(source: Any = None) -> Dict[str, Any]:
    """The upkeep board, DERIVED here from the held upkeeps alone.

    The board counts the held upkeeps by their
    derived completeness - green and red - names
    the current upkeep, the first that does not yet
    stand complete, tells each held upkeep's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held upkeeps took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.upkeeps
            if ("complete" if upkeep_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "upkeeps": number})
    current = current_upkeep(book)
    traces = []
    for upkeep in book.upkeeps:
        trace = trace_for_upkeep(book, upkeep.upkeep_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, upkeep.upkeep_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"upkeep_id": upkeep.upkeep_id, "trace": standing})
    return {
        "type": "upkeep_board",
        "slice": UPKEEP_SLICE,
        "standings": standings,
        "total": len(book.upkeeps),
        "current_upkeep": current.upkeep_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This slice's own roadmap standing, proved from the roadmap itself.

    The record loads this repo's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 slices in 11 parts,
    the banked prefix, the next slice where the
    campaign resumes, and M-211's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(UPKEEP_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "upkeep_roadmap",
        "slice": UPKEEP_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m211_title": own.title,
        "m211_part": own.part,
        "m211_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: slices, upkeeps, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or order ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class UpkeepBook:
    title: str
    slices: Tuple[SliceRef, ...] = ()
    upkeeps: Tuple[UpkeepRecord, ...] = ()
    views: Tuple[UpkeepView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[UpkeepPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        slices = tuple(_check_slice_ref(g) for g in self.slices)
        upkeeps = tuple(_check_upkeep_ref(g) for g in self.upkeeps)
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
        upkeep_ids = set()
        upkeep_seqs = set()
        for upkeep in upkeeps:
            if upkeep.upkeep_id in upkeep_ids:
                raise ValueError(
                    f"two upkeeps stand under id {upkeep.upkeep_id!r}")
            if upkeep.seq in upkeep_seqs:
                raise ValueError(
                    f"two upkeeps stand at sequence {upkeep.seq}")
            upkeep_ids.add(upkeep.upkeep_id)
            upkeep_seqs.add(upkeep.seq)
        by_slice = {ref.slice_id: ref for ref in slices}
        for upkeep in (upkeeps if slices else ()):

            ref = by_slice.get(upkeep.slice_id)
            if ref is None:
                raise ValueError(
                    f"upkeep {upkeep.upkeep_id!r} is upkeeped from slice "
                    f"{upkeep.slice_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "active":
                raise ValueError(
                    f"upkeep {upkeep.upkeep_id!r} is upkeeped from slice "
                    f"{upkeep.slice_id!r}, which is not active: "
                    f"no slice is upkeeped from an queued slice")
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
            target = (record.upkeep_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for upkeep "
                    f"{record.upkeep_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per upkeep target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_upkeeps = set()
        upkeep_ids = {upkeep.upkeep_id for upkeep in upkeeps}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.upkeep_id in trace_upkeeps:
                raise ValueError(
                    f"two traces stand for upkeep "
                    f"{record.upkeep_id!r}: one trace stands "
                    f"per upkeep walk")
            if upkeeps and record.upkeep_id not in upkeep_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces upkeep "
                    f"{record.upkeep_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_upkeeps.add(record.upkeep_id)
        object.__setattr__(
            self, "slices", tuple(sorted(slices, key=lambda g: g.seq)))
        object.__setattr__(
            self, "upkeeps", tuple(sorted(upkeeps, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.upkeeps + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.upkeep_id for g in self.upkeeps) + tuple(
            v.view_id for v in self.views)

    def upkeep_ids(self) -> Tuple[str, ...]:
        return tuple(g.upkeep_id for g in self.upkeeps)

    def slice_ids(self) -> Tuple[str, ...]:
        return tuple(g.slice_id for g in self.slices)

    def upkeep_for(self, upkeep_id: Any) -> UpkeepRecord:
        wanted = _clean_text(upkeep_id, "a upkeep id")
        for upkeep in self.upkeeps:
            if upkeep.upkeep_id == wanted:
                return upkeep
        raise KeyError(f"no upkeep named {wanted!r} stands in this book")

    def slice_for(self, slice_id: Any) -> SliceRef:
        wanted = _clean_text(slice_id, "an slice id")
        for ref in self.slices:
            if ref.slice_id == wanted:
                return ref
        raise KeyError(f"no slice named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> UpkeepView:
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
        for upkeep in self.upkeeps:
            if upkeep.upkeep_id == wanted:
                return upkeep
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "slices": [g.to_record() for g in self.slices],
            "upkeeps": [g.to_record() for g in self.upkeeps],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: UpkeepBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: UpkeepBook) -> None:
    if book.title != "The memory-map upkeep at the M-210 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.slices) != 3 or len(book.upkeeps) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three slice references, five upkeeps and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m210-boundary":
        raise ValueError("the pinned panel is panel-m210-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.check for e in index.entries] != ["sealed", "sealed", "sealed"]:
        raise ValueError("the shipped example book index must derive the three held complete upkeeps in held order")
    if index.gaps != ("upkeep-bare-update", "upkeep-leaping-update"):
        raise ValueError("the shipped example book must leave the bare and leaping upkeeps honestly open, named in its gaps")
    found = upkeep_for_check(book, EXAMPLE_CHECK)
    if found is None or found.upkeep_id != "upkeep-held-update":
        raise ValueError("the shipped example book must reach its opening upkeep under the example check")
    if trace_of(book, "upkeep-held-update") != "banked > noted > mapped > checked > sealed":
        raise ValueError("the shipped example book must derive the opening upkeep's trace from its walked steps")
    if not trace_current(book, "upkeep-held-update"):
        raise ValueError("the shipped example book must hold the opening upkeep's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note road")

def validate_book(data: Any, *, require_example: bool = False) -> UpkeepBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, UpkeepBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a upkeep book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live slice build or execution "
                f"({key!r} is named on it): {UPKEEP_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its upkeeps under a view")
    if "upkeep_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held upkeeps at call time")
    if "board" in data or "current_upkeep" in data:
        raise ValueError(
            "a book stores no board and no current upkeep: both are "
            "derived from its held upkeeps at call time")
    if "trace" in data or "order" in data:
        raise ValueError(
            "a book stores no trace and no order: both are derived "
            "from its held upkeeps at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != UPKEEP_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{UPKEEP_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != UPKEEP_SLICE):
        raise ValueError(
            f"a book's slice must be {UPKEEP_SLICE!r}")
    head = data.get("upkeep_head") or data.get("memory_map_upkeep") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's upkeep head must be a mapping")
    title = head.get("title") or data.get("title")
    slices = tuple(build_slice_ref(g) for g in data.get("slices") or ())
    upkeeps = tuple(build_upkeep(g) for g in data.get("upkeeps") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = UpkeepBook(
        title=title, slices=slices, upkeeps=upkeeps, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = UpkeepBook(
        title=book.title, slices=book.slices, upkeeps=book.upkeeps,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> UpkeepBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (UpkeepBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an UpkeepBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> UpkeepBook:
    return validate_book(data, require_example=require_example)


def load_upkeep(
        data: Optional[Dict[str, Any]] = None) -> UpkeepBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(UPKEEP_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_upkeep_file(path: Any) -> UpkeepBook:
    """Load one upkeep file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: slice references, upkeeps and views held one by one.
# ---------------------------------------------------------------------

class UpkeepRegistry:
    """An in-memory holding of slice references, upkeeps and views.

    The registry is the pure layer's model of a
    session's upkeep book: slice references are
    held under their ids, upkeeps are held under
    their ids, one upkeep per id and per sequence,
    and views are held in recorded order, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[SliceRef] = []
        self._upkeeps: List[UpkeepRecord] = []
        self._views: List[UpkeepView] = []
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
        """Hold one slice reference, mapped whole before held."""
        checked = _check_slice_ref(item)
        return self._register(
            self._slices, checked, "slice_id", "slice reference")

    def register_upkeep(self, item: Any) -> UpkeepRecord:
        """Hold one upkeep, mapped whole before held."""
        checked = _check_upkeep_ref(item)
        return self._register(
            self._upkeeps, checked, "upkeep_id", "upkeep")

    def register_view(self, view: Any) -> UpkeepView:
        """Hold one view; a view naming no id takes a fresh one."""
        checked = _check_view_ref(view)
        if not checked.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            checked = build_view({**checked.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, checked, "view_id", "view")

    def register_book(self, book: Any) -> UpkeepBook:
        """Hold a whole book's records, under its title."""
        checked = build_book(book)
        if self._title is not None and checked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {checked.title!r}")
        for ref in checked.slices:
            self.register_slice_ref(ref)
        for upkeep in checked.upkeeps:
            self.register_upkeep(upkeep)
        for view in checked.views:
            self.register_view(view)
        self._title = checked.title
        return self.book()

    def book(self) -> UpkeepBook:
        return UpkeepBook(
            title=self._title or "An unheld upkeep book",
            slices=tuple(self._slices), upkeeps=tuple(self._upkeeps),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[SliceRef, ...]:
        return tuple(self._slices)

    def list_upkeeps(self) -> Tuple[UpkeepRecord, ...]:
        return tuple(self._upkeeps)

    def list_views(self) -> Tuple[UpkeepView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._upkeeps) + tuple(self._views)

    def get_slice(self, slice_id: Any) -> SliceRef:
        return self.book().slice_for(slice_id)

    def get_upkeep(self, upkeep_id: Any) -> UpkeepRecord:
        return self.book().upkeep_for(upkeep_id)

    def get_view(self, view_id: Any) -> UpkeepView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the journal target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> UpkeepBook:
    if source is None:
        return load_upkeep()
    if isinstance(source, UpkeepBook):
        return source
    if isinstance(source, UpkeepRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def upkeep_record(upkeep: Any, source: Any = None) -> Dict[str, Any]:
    checked = _check_upkeep_ref(upkeep)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "upkeep_upkeep",
        "slice": UPKEEP_SLICE,
        "upkeep_id": checked.upkeep_id,
        "slice_id": checked.slice_id,
        "title": checked.title,
        "segment": segment_of(checked, book),
        "complete": upkeep_green(checked, book),
        "gaps": list(upkeep_gaps(checked, book)),
    }
    record.update(_provenance_record(checked))
    return record


def slice_record(ref: Any) -> Dict[str, Any]:
    checked = _check_slice_ref(ref)
    record = {
        "type": "upkeep_slice",
        "slice": UPKEEP_SLICE,
        "slice_id": checked.slice_id,
        "title": checked.title,
        "state": checked.state,
    }
    record.update(_provenance_record(checked))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_trace_ref(record_in)
    record = {
        "type": "upkeep_trace",
        "slice": UPKEEP_SLICE,
        "trace_id": checked.trace_id,
        "upkeep_id": checked.upkeep_id,
        "trace": checked.trace,
    }
    record.update(_provenance_record(checked))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    checked = _check_view_ref(view)
    record = {
        "type": "upkeep_view",
        "slice": UPKEEP_SLICE,
        "view_id": checked.view_id, "seq": checked.seq,
        "view_filter": checked.view_filter,
    }
    record.update(_provenance_record(checked))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_note_ref(record_in)
    record = {
        "type": "upkeep_note",
        "slice": UPKEEP_SLICE,
        "note_id": checked.note_id,
        "upkeep_id": checked.upkeep_id,
        "stance": checked.stance,
    }
    record.update(_provenance_record(checked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    checked = validate_panel(panel, source)
    record = {"type": "upkeep_panel",
              "slice": UPKEEP_SLICE}
    record.update(checked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, UpkeepVerdict):
        checked = validate_verdict(verdict, source)
    else:
        checked = derive_verdict(_source_book(verdict), view)
    record = {"type": "upkeep_verdict",
              "slice": UPKEEP_SLICE}
    record.update(checked.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, UpkeepIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "upkeep_index",
              "slice": UPKEEP_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    checked = _source_book(book)
    record = {"type": "upkeep_book",
              "slice": UPKEEP_SLICE,
              "title": checked.title}
    record.update(checked.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(upkeep: Any, source: Any = None) -> str:
    checked = _check_upkeep_ref(upkeep)
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
        f"The upkeeps stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"upkeeps stand complete.")


def view_plain_words(view: Any) -> str:
    checked = _check_view_ref(view)
    return f"View {checked.view_id}: shows {checked.view_filter} upkeeps."


def note_plain_words(record_in: Any) -> str:
    checked = _check_note_ref(record_in)
    return (
        f"Note {checked.note_id}: {checked.stance} "
        f"{checked.upkeep_id}, toward {checked.target}. "
        f"{checked.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, UpkeepIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} green upkeeps; "
        f"red, named in its gaps: {gaps}.")

def format_upkeep(upkeep: Any, source: Any = None) -> str:
    checked = _check_upkeep_ref(upkeep)
    book = _source_book(source) if source is not None else None
    lines = [f"{checked.title} ({checked.upkeep_id})"]
    lines.extend(plain_lines(checked))
    lines.append(checked.detail)
    if upkeep_green(checked, book):
        lines.append(
            "This upkeep stands complete - it walked the question "
            "sequence in the open from banked to sealed, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This upkeep stands open - it stands named in "
            f"its gaps: {', '.join(upkeep_gaps(checked, book))}, and "
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
        f"Upkeep note {checked.stance} {checked.upkeep_id} "
        f"({checked.note_id}): {checked.title}. {checked.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_check(source: Any, check: Any) -> str:
    upkeep = upkeep_for_check(source, check)
    if upkeep is not None:
        return format_upkeep(upkeep, source)
    wanted = check.strip() if isinstance(check, str) else check
    return (
        f"No held upkeep stands under check {wanted!r} yet - the "
        f"check reaches nothing in this book, and no upkeep is "
        f"invented for it.")


def format_book(source: Any = None, slice_id: Any = None) -> str:
    book = _source_book(source)
    upkeeps = (upkeeps_for_slice(book, slice_id)
              if slice_id is not None else book.upkeeps)
    lines = [f"The Memory Gate (M-211) - {book.title}"]
    lines.extend(segment_of(upkeep, book) for upkeep in upkeeps)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Upkeep panel under view {panel.view_id}:"]
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
    lines = ["Upkeep index, derived from the held upkeeps:"]
    for entry in index.entries:
        lines.append(f"{entry.check} - {entry.title} ({entry.upkeep_id})")
    if index.gaps:
        lines.append(
            "Red, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_upkeep_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Memory Gate (M-211)",
        f"{book.title}: {len(book.upkeeps)} upkeeps held, "
        f"{len(green_upkeeps(book))} upkeeps standing green, "
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


def parse_upkeep_args(args: Any) -> Tuple[str, Any]:
    """Parse the /upkeep grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("upkeep", "view", "note"):
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
