"""Patterns (roadmap slice M-214).

Part IX - The Mythic Method Engine. The roadmap
words: *repeated successful manoeuvres become
candidate skills (Part X) drafted by the Scribe
for approval.*

What already ships, and what this slice adds:

* The Self-Improving ledger already ships as
  data (M-155, ``core/self_improving_ledger.py``):
  candidate memories captured after significant
  work, promoted only by an explicit decision.
  This slice WIRES the inflow the ledger's own
  docstring names - M-214 patterns flowing
  here - as data, in its own module, standing in
  the M-195 copy-and-share book shape the M-213
  book stands in: one scribe per campaign, and the
  scribe's charge over one closed slice's manoeuvre
  held as a book - a pattern. The shipped
  roads stand untouched behind their seams: this
  layer holds patterns as data over the
  campaign's slices and rewrites none of them,
  and the ledger keeps its own standing. Manoeuvres
  flow to the ledger AS DATA alone: a manoeuvre
  carries a ledger ref, a reference held in this
  book; holding, viewing or telling a
  pattern writes no ledger file live,
  captures no candidate and promotes nothing.

* No charter row names this slice: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-214 on no row, and the
  slice tests pin that absence live. The M-005
  method charter names no slice row either: its
  own words name the whole of Part IX as the
  part that executes the charter, and this slice
  is built to the roadmap words and that
  execution note together.

* A pattern is held whole: the slice it
  answers for, named by its slice id; its title;
  the manoeuvre steps it walked, held as data in
  walk order; and the evidence it carries, held
  as data by kind. The manoeuvre walk is EXPLICIT:
  its sequence stands as data
  (:data:`CHECKS`, :data:`TRANSITIONS`) -
  spotted, repeated, drafted, judged, approved -
  and a pattern's standing is DERIVED at
  call time from its held steps and evidence
  alone: a pattern that opens anywhere but
  spotted, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet reached approved stands
  open, named in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - slice_ref,
  manoeuvre_ref, test_record, skill_ref, evidence
  a scribe can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A manoeuvre is
  judged from held evidence alone, never
  from a feeling: a pattern holding a
  bare claim stands open, named in its gaps.
* A pattern stands only for an ACTIVE
  slice. The book holds each slice it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  pattern naming a slice that stands
  nowhere in the book refuses BY NAME, and a
  pattern for a slice that is not active
  refuses BY NAME beside it: the scribe deals with
  the slice in hand, in roadmap order, never a
  queued one, and a slice whose manoeuvre already
  stands complete is never drafted twice - the
  current pattern is derived, so a
  completed slice is never the current manoeuvre
  twice.
* The pattern's trace is visible. A trace
  record holds one pattern's walked steps
  as one trace line, exactly as walked, beside
  the pattern. The derived trace is
  computed at call time from the pattern's
  held steps; a held trace that no longer agrees
  with it stands stale, named in the board - the
  trace is the walk itself, never a retelling
  of it.
* The pattern index is DERIVED at call
  time from the held patterns - one entry
  per complete pattern, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, order or current-pattern
  claim on any record refuses by name.
* The current pattern is DERIVED at call
  time - the first held pattern, in held
  order, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its pattern, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per pattern stance; holding
  a note posts none of it, the rule stands as
  data (:data:`PATTERN_RULE`), and a record
  claiming a manoeuvre was actually approved,
  captured or promoted live refuses BY NAME.
  The scribe reports - and those reports, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the shape a real pattern
  file takes, a loader reads a file anywhere on
  disk, patterns and views are shaped as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a pattern book for a session and
  telling from it. This layer reaches no live
  road: it writes no manoeuvre live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no scribe, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds patterns
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The manoeuvre walk is explicit.** A
  pattern is judged against the held
  steps and legal steps alone; an illegal step
  stands named in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  pattern that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, named in its gaps:
  a manoeuvre is judged from evidence, not
  vibes.
* **Active slices only, in roadmap order.** A
  pattern for a missing or queued slice
  refuses by name; no pattern is invented
  for a slice the scribe has not dealt with.
* **Unknown stays unknown.** A pattern
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, order
  and current pattern are derived, never
  stored.** Each is derived from the held
  patterns at call time; a stored one
  refuses by name, so it can never drift.
* **One pattern per pattern.** Two
  patterns standing for one pattern id
  refuse by name, and one note record stands per
  pattern stance.
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
    "PATTERN_RESOURCE",
    "PATTERN_SCHEMA",
    "PATTERN_SLICE",
    "PATTERN_RULE",
    "PLAIN_EXPLANATION",
    "THE_PATTERN_SLICE",
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
    "PatternRecord",
    "IndexEntry",
    "SliceRef",
    "NoteRecord",
    "PatternBook",
    "PatternIndex",
    "PatternPanel",
    "PatternPanelRow",
    "PatternRegistry",
    "PatternVerdict",
    "PatternView",
    "TargetCount",
    "trace_for_pattern",
    "trace_record",
    "board_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_pattern",
    "build_slice_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_pattern",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "pattern_for_check",
    "pattern_order",
    "pattern_record",
    "first_note",
    "format_book",
    "format_pattern",
    "format_index",
    "format_note",
    "format_check",
    "format_panel",
    "format_pattern_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "slice_record",
    "load_pattern",
    "load_pattern_file",
    "normalize_slice_state",
    "normalize_check",
    "normalize_claim_kind",
    "legal_step",
    "next_check",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_pattern",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_pattern_args",
    "green_patterns",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_patterns",
    "validate_trace",
    "validate_book",
    "validate_pattern",
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
    "pattern_gaps",
    "pattern_green",
    "patterns_for_slice",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

PATTERN_SCHEMA = "mythic.pattern_extraction/1"
PATTERN_SLICE = "M-214"
THE_PATTERN_SLICE = PATTERN_SLICE
PATTERN_RESOURCE = "pattern_extraction.yaml"
INDEX_ACTION = "index"
EXAMPLE_CHECK = "approved"
CHECK_FIELDS = ("checks", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("approved", "held", "blocked")
SLICE_STATES = ("active", "queued")
PATTERN_RULE = (
    "patterns are held as data alone: repeated "
    "successful manoeuvres become candidate "
    "skills drafted by the Scribe for approval - "
    "a draft stands as data, held by reference "
    "(a skill ref), never written live - the "
    "pattern walk stands as an explicit pattern "
    "sequence - spotted, repeated, drafted, "
    "judged, approved - and a pattern completes "
    "only complete, complete being a state with "
    "evidence held - slice ref, manoeuvre ref, "
    "test record, skill ref - never a feeling, "
    "a memory, an assertion or a summary; "
    "holding, viewing and reading a pattern "
    "writes no skill live, approves nothing, "
    "spawns no process and opens no network")
PLAIN_EXPLANATION = (
    "Pattern extraction (M-214): repeated "
    "successful manoeuvres become candidate "
    "skills (Part X) drafted by the Scribe "
    "for approval.")
USAGE = (
    "Usage: /patterns | /patterns pattern <pattern-id> | "
    "/patterns check <check> | /patterns slice <slice-id> | "
    "/patterns view <view-id> | /patterns note <note-id> | "
    "/patterns index | /patterns panel | /patterns verdict")

CHECKS = ("spotted", "repeated", "drafted", "judged", "approved")
HELD_EVIDENCE = ("slice_ref", "manoeuvre_ref", "test_record", "skill_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "spotted": ("repeated",),
    "repeated": ("drafted",),
    "drafted": ("judged",),
    "judged": ("spotted", "approved"),
    "approved": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a failure or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a pattern stands complete.
    A check outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_check(check: Any, failed: Any = False) -> Optional[str]:
    """The step the scribe takes next, DERIVED from the sequence.

    Banked leads to repeated and repeated to
    drafted; drafted leads to judged; at
    judged a follow-up banking steps back to spotted and a finished manoeuvre steps to approved;
    approved is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    judged = normalize_check(check)
    if judged == "spotted":
        return "repeated"
    if judged == "repeated":
        return "drafted"
    if judged == "drafted":
        return "judged"
    if judged == "judged":
        return "spotted" if failed else "approved"
    return None


_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "pattern_id", "seq", "slice_id", "title", "checks",
    "claims", "detail",
} | set(_PROVENANCE))
_SLICE_REF_KEYS = frozenset({
    "slice_id", "seq", "title", "state", "detail",
} | set(_PROVENANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "pattern_id", "trace", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "pattern_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered",
    "current_pattern", "next_pattern", "progress", "board",
    "current", "order", "breaks", "active"})
_LIVE_KEYS = (
    "live_pattern", "patterns_live", "live_question",
    "patterns_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "resumes_live",
    "resumed_live", "pauses_campaign", "paused_live",
    "runs_campaign", "ran_campaign", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "pattern_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_pattern", "sent_pattern",
    "posts_note", "posted_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_manoeuvre", "filed_live", "spawns_scribe", "spawned_scribe", "sends_manoeuvre", "sent_manoeuvre", "writes_manoeuvre", "wrote_manoeuvre")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_checks(value: Any) -> Tuple[str, ...]:
    """A pattern's walked checks, held as data.

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
    """A pattern's asked claims: claim kinds named as data.

    Each claim names one kind from the approved
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
                f"{what} claims a live gate pattern or slice build "
                f"execution ({key!r} is named on it): "
                f"{PATTERN_RULE}")
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
# The held pattern: one slice cut from an active slice.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class PatternRecord:
    """One pattern slice, held as data.

    The pattern names the active slice it was
    held from, by slice id, its title, its
    verifiable checks, held as data, and its
    claims, named by pattern id. The grain is
    derived, never stored: exactly one verifiable
    walk is drafted against the machine. A pattern whose
    checks are not yet held stands with its
    checks empty: it stands open, named in
    its gaps, and no check is invented for it.
    The pattern is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    pattern_id: str
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
            self, "pattern_id", _clean_text(self.pattern_id, "a pattern id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "slice_id", _clean_text(self.slice_id, "an slice id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a pattern title"))
        object.__setattr__(
            self, "checks", _check_checks(self.checks))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a pattern detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.pattern_id

    @property
    def check(self) -> str:
        """The check the pattern stands at: its last walked check."""
        return self.checks[-1] if self.checks else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "pattern_id": self.pattern_id, "seq": self.seq,
            "slice_id": self.slice_id, "title": self.title,
            "checks": list(self.checks),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_pattern_ref(value: Any) -> PatternRecord:
    if not isinstance(value, PatternRecord):
        raise ValueError("a pattern must be a PatternRecord")
    return value


def validate_pattern(pattern: Any) -> PatternRecord:
    return _check_pattern_ref(pattern)


def build_pattern(record: Any = None, **kwargs: Any) -> PatternRecord:
    """Build one held pattern from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, PatternRecord):
        if kwargs:
            raise ValueError("a pattern stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a pattern must be a mapping or a PatternRecord")
    _needed(data, _RUN_KEYS, "a pattern")
    return PatternRecord(
        pattern_id=data.get("pattern_id"), seq=data.get("seq"),
        slice_id=data.get("slice_id"), title=data.get("title"),
        checks=data.get("checks"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_provenance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each pattern to the steps it took outside the machine.

    Derived from the held patterns alone: a break is
    one consecutive pair of walked checks the
    explicit gate sequence does not allow, told
    in walk order as before, then after.
    """
    found: Dict[str, Tuple[str, ...]] = {}
    for pattern in book.patterns:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(pattern.checks, pattern.checks[1:])
            if not legal_step(before, after))
        if breaks:
            found[pattern.pattern_id] = breaks
    return found

def pattern_gaps(pattern: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a pattern from standing complete.

    Mapped from the pattern's own held fields alone -
    its walked steps against the explicit question
    sequence, and its carried evidence against the
    approved vocabulary: the pattern opens at
    named, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a pattern stands complete only when it has
    reached approved. The source names nothing
    further: no gap is borrowed from another
    pattern.
    """
    judged = _check_pattern_ref(pattern)
    gaps: List[str] = []
    if not judged.checks:
        gaps.append(
            "has passed through no step: the pattern has not started")
        return tuple(gaps)
    if judged.checks[0] != "spotted":
        gaps.append(
            f"opens at {judged.checks[0]}, not at spotted: "
            f"the pattern opens with the reflection")
    for before, after in zip(judged.checks, judged.checks[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"pattern sequence does not allow")
    for kind in judged.claims:
        if kind in BARE_CLAIMS:
            gaps.append(
                f"carries a {kind} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if judged.checks[-1] != "approved":
        gaps.append(
            f"has not reached approved: the pattern stands "
            f"at {judged.checks[-1]}")
    return tuple(gaps)

def pattern_green(pattern: Any, source: Any = None) -> bool:
    return not pattern_gaps(pattern, source)


def plain_lines(pattern: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the pattern's own fields."""
    judged = _check_pattern_ref(pattern)
    return (
        f"Pattern: {judged.title}",
        f"Slice: {judged.slice_id}",
        f"Check: {judged.check if judged.check else 'none'}",
        f"Claims: "
        f"{', '.join(judged.claims) if judged.claims else 'none'}",
    )


def segment_of(pattern: Any, source: Any = None) -> str:
    judged = _check_pattern_ref(pattern)
    gaps = pattern_gaps(judged, source)
    return (
        f"{judged.pattern_id}: {judged.title} - slice: "
        f"'{judged.slice_id}' - check: "
        f"'{judged.check if judged.check else 'none'}' - "
        f"checks: {len(judged.checks)} - claims: "
        f"'{', '.join(judged.claims) if judged.claims else 'none'}' - "
        f"detail: '{judged.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held slice reference: the active slice a book patterns from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class SliceRef:
    """One slice a pattern book patterns from, held as a reference.

    The record names the slice, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 slice book's own telling. A pattern
    stands only from an active reference: the
    book refuses a pattern naming no held reference,
    and a pattern from an queued one, BY NAME.
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
    human active - the slice's pattern ids in
    derived claim order, held exactly as
    active. The trace is of the set and its
    order, never of a step: when the derived
    trace moves, this record stands stale, named
    in the board, until a new trace is active.
    """

    trace_id: str
    seq: int
    pattern_id: str
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
            self, "pattern_id", _clean_text(self.pattern_id, "an slice id"))
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
            "pattern_id": self.pattern_id, "trace": self.trace,
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
        pattern_id=data.get("pattern_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a pattern, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One pattern stance, held as data.

    The record names its pattern, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per pattern stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    pattern_id: str
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
            self, "pattern_id", _clean_text(self.pattern_id, "a pattern id"))
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
            "pattern_id": self.pattern_id, "stance": self.stance,
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
        pattern_id=data.get("pattern_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which slices a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class PatternView:
    """A view over the book: every pattern, the green, the rest."""

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


def _check_view_ref(value: Any) -> PatternView:
    if not isinstance(value, PatternView):
        raise ValueError("a view must be an PatternView")
    return value


def validate_view(view: Any) -> PatternView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> PatternView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, PatternView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an PatternView")
    _needed(data, _VIEW_KEYS, "a view")
    return PatternView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class PatternPanelRow:
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


def _row_for_pattern(pattern: PatternRecord,
                     source: Any = None) -> PatternPanelRow:
    return PatternPanelRow(
        item_id=pattern.pattern_id,
        standing="complete" if pattern_green(pattern, source) else "open",
        label=pattern.title, segment=segment_of(pattern, source),
        recorded_on=pattern.recorded_on)


def _check_row_ref(value: Any) -> PatternPanelRow:
    if not isinstance(value, PatternPanelRow):
        raise ValueError("a panel row must be an PatternPanelRow")
    return value


def validate_row(row: Any, pattern: Any = None,
                 source: Any = None) -> PatternPanelRow:
    judged = _check_row_ref(row)
    if pattern is not None:
        derived = _row_for_pattern(_check_pattern_ref(pattern), source)
        if judged != derived:
            raise ValueError(
                f"panel row {judged.item_id!r} does not agree with "
                f"the row derived from its pattern")
    return judged


def build_row(row: Any = None, pattern: Any = None,
              source: Any = None,
              **kwargs: Any) -> PatternPanelRow:
    if pattern is not None:
        derived = _row_for_pattern(_check_pattern_ref(pattern), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            PatternPanelRow(**kwargs))
        return validate_row(built, pattern, source)
    if isinstance(row, PatternPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return PatternPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return PatternPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an PatternPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[PatternPanelRow, ...]
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
        f"The pattern book holds {total_items} patterns as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown patterns "
        f"stand complete.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its pattern's own fields "
        "- the slice it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any pattern.",
        "Completeness is drafted from the held records alone: "
        "a pattern that steps outside the pattern sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not reached approved stands open, named in its "
        "gaps, and the pattern index is derived from the "
        "held patterns, never stored where it could drift.",
    )

@dataclass(frozen=True)
class PatternPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[PatternPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> PatternView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, PatternView):
        return view
    return book.view_for(view)


def shown_patterns(source: Any, view: Any = None
                   ) -> Tuple[PatternRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.patterns
    if resolved.view_filter == "complete":
        return tuple(g for g in book.patterns if pattern_green(g, book))
    return tuple(g for g in book.patterns if not pattern_green(g, book))


def patterns_for_slice(source: Any, slice_id: Any
                      ) -> Tuple[PatternRecord, ...]:
    wanted = _clean_text(slice_id, "an slice id")
    return tuple(
        g for g in _source_book(source).patterns if g.slice_id == wanted)


def green_patterns(source: Any) -> Tuple[PatternRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.patterns if pattern_green(g, book))


def current_pattern(source: Any) -> Optional[PatternRecord]:
    """The book's current pattern, DERIVED at call time.

    The first held pattern, in held order, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held patterns alone, so it can
    never go stale against them. A book whose every
    pattern stands complete has no current pattern.
    """
    book = _source_book(source)
    for pattern in book.patterns:
        if not pattern_green(pattern, book):
            return pattern
    return None


def derive_panel(source: Any, view: Any = None) -> PatternPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_patterns(book, resolved)
    rows = tuple(_row_for_pattern(pattern, book) for pattern in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.patterns), default="")
    green = sum(1 for g in shown if pattern_green(g, book))
    return PatternPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.patterns), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.patterns), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> PatternPanel:
    if not isinstance(value, PatternPanel):
        raise ValueError("a panel must be an PatternPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> PatternPanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 manoeuvre).
    """
    judged = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(judged.view_id)
                if judged.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(judged, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {judged.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return judged


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> PatternPanel:
    if isinstance(panel, PatternPanel):
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
        built = PatternPanel(
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
    raise ValueError("a panel must be a mapping, an PatternPanel, or derived")


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
        return "approved"
    if green_shown == 0:
        return "blocked"
    return "held"


@dataclass(frozen=True)
class PatternVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> PatternVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_patterns(book, resolved)
    green = sum(1 for g in shown if pattern_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return PatternVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> PatternVerdict:
    if not isinstance(value, PatternVerdict):
        raise ValueError("a verdict must be an PatternVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> PatternVerdict:
    judged = _check_verdict_ref(verdict)
    if judged.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {judged.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(judged.view_id)
                if judged.view_id is not None else None)
        derived = derive_verdict(book, view)
        if judged != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return judged


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> PatternVerdict:
    if isinstance(verdict, PatternVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = PatternVerdict(
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
        "a verdict must be a mapping, an PatternVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held slices' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    check: str
    pattern_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "check": self.check, "pattern_id": self.pattern_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class PatternIndex:
    """The pattern index, derived from the held patterns.

    The index names one entry per green pattern, in
    held order - the pattern's own one verifiable
    check, its pattern id and its title - and the
    patterns that do not stand complete, named in its
    gaps. Nothing here is stored on any pattern: the
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


def derive_index(source: Any) -> PatternIndex:
    """Derive the pattern index from the book's held patterns."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(check=g.check, pattern_id=g.pattern_id,
                   title=g.title)
        for g in book.patterns if pattern_green(g, book))
    gaps = tuple(
        g.pattern_id for g in book.patterns if not pattern_green(g, book))
    return PatternIndex(entries=entries, gaps=gaps)


def pattern_for_check(source: Any, check: Any) -> Optional[PatternRecord]:
    """The first held pattern one check reaches, or none - honestly."""
    if check is None:
        return None
    if not isinstance(check, str):
        raise ValueError("an check must be a string naming the check")
    wanted = check.strip()
    if not wanted:
        return None
    for pattern in _source_book(source).patterns:
        if pattern.check == wanted:
            return pattern
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held order: the pattern
    that took it and the step it took, before,
    then after. A book whose patterns all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{pattern_id}: {step}"
        for pattern_id, steps in _breaks_map(book).items()
        for step in steps)

def pattern_order(source: Any,
              slice_id: Any = None) -> Tuple[PatternRecord, ...]:
    """The held patterns in their held order, DERIVED at call time.

    Patterns stand in the order the book holds them -
    the order their slices were taken - optionally
    for one slice alone. Nothing here is stored:
    the order is the book's own held order, told.
    """
    book = _source_book(source)
    patterns = list(book.patterns)
    if slice_id is not None:
        wanted = _clean_text(slice_id, "a slice id")
        patterns = [r for r in patterns if r.slice_id == wanted]
    return tuple(patterns)

def trace_of(source: Any, pattern_id: Any) -> str:
    """One pattern's trace, DERIVED at call time.

    The pattern's walked checks joined as one trace
    line, in walk order. A pattern that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is named
    elsewhere.
    """
    pattern = _source_book(source).pattern_for(pattern_id)
    return " > ".join(pattern.checks)

def trace_for_pattern(source: Any,
                  pattern_id: Any) -> Optional[TraceRecord]:
    """The held trace for one pattern, or none - honestly."""
    wanted = _clean_text(pattern_id, "a pattern id")
    for record in _source_book(source).traces:
        if record.pattern_id == wanted:
            return record
    return None

def trace_current(source: Any, pattern_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_pattern(source, pattern_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, pattern_id)

def note_for_pattern(source: Any, pattern_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one pattern (and stance, when named)."""
    wanted = _clean_text(pattern_id, "a pattern id")
    for record in _source_book(source).notes:
        if record.pattern_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the slice targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def board_record(source: Any = None) -> Dict[str, Any]:
    """The pattern board, DERIVED here from the held patterns alone.

    The board counts the held patterns by their
    derived completeness - green and red - names
    the current pattern, the first that does not yet
    stand complete, tells each held pattern's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held patterns took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.patterns
            if ("complete" if pattern_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "pattern_records": number})
    current = current_pattern(book)
    traces = []
    for pattern in book.patterns:
        trace = trace_for_pattern(book, pattern.pattern_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, pattern.pattern_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"pattern_id": pattern.pattern_id, "trace": standing})
    return {
        "type": "pattern_board",
        "slice": PATTERN_SLICE,
        "standings": standings,
        "total": len(book.patterns),
        "current_pattern": current.pattern_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This slice's own roadmap standing, proved from the roadmap itself.

    The record loads this repo's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 slices in 11 parts,
    the spotted prefix, the next slice where the
    campaign resumes, and M-214's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(PATTERN_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "pattern_roadmap",
        "slice": PATTERN_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m214_title": own.title,
        "m214_part": own.part,
        "m214_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: slices, patterns, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or order ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class PatternBook:
    title: str
    slices: Tuple[SliceRef, ...] = ()
    patterns: Tuple[PatternRecord, ...] = ()
    views: Tuple[PatternView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[PatternPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        slices = tuple(_check_slice_ref(g) for g in self.slices)
        patterns = tuple(_check_pattern_ref(g) for g in self.patterns)
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
        pattern_ids = set()
        pattern_seqs = set()
        for pattern in patterns:
            if pattern.pattern_id in pattern_ids:
                raise ValueError(
                    f"two patterns stand under id {pattern.pattern_id!r}")
            if pattern.seq in pattern_seqs:
                raise ValueError(
                    f"two patterns stand at sequence {pattern.seq}")
            pattern_ids.add(pattern.pattern_id)
            pattern_seqs.add(pattern.seq)
        by_slice = {ref.slice_id: ref for ref in slices}
        for pattern in (patterns if slices else ()):

            ref = by_slice.get(pattern.slice_id)
            if ref is None:
                raise ValueError(
                    f"pattern {pattern.pattern_id!r} is held from slice "
                    f"{pattern.slice_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "active":
                raise ValueError(
                    f"pattern {pattern.pattern_id!r} is held from slice "
                    f"{pattern.slice_id!r}, which is not active: "
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
            target = (record.pattern_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for pattern "
                    f"{record.pattern_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per pattern target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_patterns = set()
        pattern_ids = {pattern.pattern_id for pattern in patterns}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.pattern_id in trace_patterns:
                raise ValueError(
                    f"two traces stand for pattern "
                    f"{record.pattern_id!r}: one trace stands "
                    f"per pattern walk")
            if patterns and record.pattern_id not in pattern_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces pattern "
                    f"{record.pattern_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_patterns.add(record.pattern_id)
        object.__setattr__(
            self, "slices", tuple(sorted(slices, key=lambda g: g.seq)))
        object.__setattr__(
            self, "pattern_records", tuple(sorted(patterns, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.patterns + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.pattern_id for g in self.patterns) + tuple(
            v.view_id for v in self.views)

    def pattern_ids(self) -> Tuple[str, ...]:
        return tuple(g.pattern_id for g in self.patterns)

    def slice_ids(self) -> Tuple[str, ...]:
        return tuple(g.slice_id for g in self.slices)

    def pattern_for(self, pattern_id: Any) -> PatternRecord:
        wanted = _clean_text(pattern_id, "a pattern id")
        for pattern in self.patterns:
            if pattern.pattern_id == wanted:
                return pattern
        raise KeyError(f"no pattern named {wanted!r} stands in this book")

    def slice_for(self, slice_id: Any) -> SliceRef:
        wanted = _clean_text(slice_id, "an slice id")
        for ref in self.slices:
            if ref.slice_id == wanted:
                return ref
        raise KeyError(f"no slice named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> PatternView:
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
        for pattern in self.patterns:
            if pattern.pattern_id == wanted:
                return pattern
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "slices": [g.to_record() for g in self.slices],
            "pattern_records": [g.to_record() for g in self.patterns],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: PatternBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: PatternBook) -> None:
    if book.title != "Pattern extraction at the M-213 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.slices) != 3 or len(book.patterns) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three slice references, five patterns and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m213-boundary":
        raise ValueError("the pinned panel is panel-m213-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.check for e in index.entries] != ["approved", "approved", "approved"]:
        raise ValueError("the shipped example book index must derive the three held complete patterns in held order")
    if index.gaps != ("pattern-bare-manoeuvre", "pattern-leaping-manoeuvre"):
        raise ValueError("the shipped example book must leave the bare and leaping patterns honestly open, named in its gaps")
    found = pattern_for_check(book, EXAMPLE_CHECK)
    if found is None or found.pattern_id != "pattern-held-manoeuvre":
        raise ValueError("the shipped example book must reach its opening pattern under the example check")
    if trace_of(book, "pattern-held-manoeuvre") != "spotted > repeated > drafted > judged > approved":
        raise ValueError("the shipped example book must derive the opening pattern's trace from its walked steps")
    if not trace_current(book, "pattern-held-manoeuvre"):
        raise ValueError("the shipped example book must hold the opening pattern's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note road")

def validate_book(data: Any, *, require_example: bool = False) -> PatternBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, PatternBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a pattern book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live slice build or execution "
                f"({key!r} is named on it): {PATTERN_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its patterns under a view")
    if "pattern_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held patterns at call time")
    if "board" in data or "current_pattern" in data:
        raise ValueError(
            "a book stores no board and no current pattern: both are "
            "derived from its held patterns at call time")
    if "trace" in data or "order" in data:
        raise ValueError(
            "a book stores no trace and no order: both are derived "
            "from its held patterns at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != PATTERN_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{PATTERN_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != PATTERN_SLICE):
        raise ValueError(
            f"a book's slice must be {PATTERN_SLICE!r}")
    head = data.get("pattern_head") or data.get("pattern_extraction") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's pattern head must be a mapping")
    title = head.get("title") or data.get("title")
    slices = tuple(build_slice_ref(g) for g in data.get("slices") or ())
    patterns = tuple(build_pattern(g) for g in data.get("pattern_records") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = PatternBook(
        title=title, slices=slices, patterns=patterns, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = PatternBook(
        title=book.title, slices=book.slices, patterns=book.patterns,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> PatternBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (PatternBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an PatternBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> PatternBook:
    return validate_book(data, require_example=require_example)


def load_pattern(
        data: Optional[Dict[str, Any]] = None) -> PatternBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(PATTERN_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_pattern_file(path: Any) -> PatternBook:
    """Load one pattern file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: slice references, patterns and views held one by one.
# ---------------------------------------------------------------------

class PatternRegistry:
    """An in-memory holding of slice references, patterns and views.

    The registry is the pure layer's model of a
    session's pattern book: slice references are
    held under their ids, patterns are held under
    their ids, one pattern per id and per sequence,
    and views are held in recorded order, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[SliceRef] = []
        self._patterns: List[PatternRecord] = []
        self._views: List[PatternView] = []
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
        """Hold one slice reference, drafted whole before held."""
        judged = _check_slice_ref(item)
        return self._register(
            self._slices, judged, "slice_id", "slice reference")

    def register_pattern(self, item: Any) -> PatternRecord:
        """Hold one pattern, drafted whole before held."""
        judged = _check_pattern_ref(item)
        return self._register(
            self._patterns, judged, "pattern_id", "pattern")

    def register_view(self, view: Any) -> PatternView:
        """Hold one view; a view naming no id takes a fresh one."""
        judged = _check_view_ref(view)
        if not judged.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            judged = build_view({**judged.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, judged, "view_id", "view")

    def register_book(self, book: Any) -> PatternBook:
        """Hold a whole book's records, under its title."""
        judged = build_book(book)
        if self._title is not None and judged.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {judged.title!r}")
        for ref in judged.slices:
            self.register_slice_ref(ref)
        for pattern in judged.patterns:
            self.register_pattern(pattern)
        for view in judged.views:
            self.register_view(view)
        self._title = judged.title
        return self.book()

    def book(self) -> PatternBook:
        return PatternBook(
            title=self._title or "An unheld pattern book",
            slices=tuple(self._slices), patterns=tuple(self._patterns),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[SliceRef, ...]:
        return tuple(self._slices)

    def list_patterns(self) -> Tuple[PatternRecord, ...]:
        return tuple(self._patterns)

    def list_views(self) -> Tuple[PatternView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._patterns) + tuple(self._views)

    def get_slice(self, slice_id: Any) -> SliceRef:
        return self.book().slice_for(slice_id)

    def get_pattern(self, pattern_id: Any) -> PatternRecord:
        return self.book().pattern_for(pattern_id)

    def get_view(self, view_id: Any) -> PatternView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the journal target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> PatternBook:
    if source is None:
        return load_pattern()
    if isinstance(source, PatternBook):
        return source
    if isinstance(source, PatternRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def pattern_record(pattern: Any, source: Any = None) -> Dict[str, Any]:
    judged = _check_pattern_ref(pattern)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "pattern_pattern",
        "slice": PATTERN_SLICE,
        "pattern_id": judged.pattern_id,
        "slice_id": judged.slice_id,
        "title": judged.title,
        "segment": segment_of(judged, book),
        "complete": pattern_green(judged, book),
        "gaps": list(pattern_gaps(judged, book)),
    }
    record.update(_provenance_record(judged))
    return record


def slice_record(ref: Any) -> Dict[str, Any]:
    judged = _check_slice_ref(ref)
    record = {
        "type": "pattern_slice",
        "slice": PATTERN_SLICE,
        "slice_id": judged.slice_id,
        "title": judged.title,
        "state": judged.state,
    }
    record.update(_provenance_record(judged))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    judged = _check_trace_ref(record_in)
    record = {
        "type": "pattern_trace",
        "slice": PATTERN_SLICE,
        "trace_id": judged.trace_id,
        "pattern_id": judged.pattern_id,
        "trace": judged.trace,
    }
    record.update(_provenance_record(judged))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    judged = _check_view_ref(view)
    record = {
        "type": "pattern_view",
        "slice": PATTERN_SLICE,
        "view_id": judged.view_id, "seq": judged.seq,
        "view_filter": judged.view_filter,
    }
    record.update(_provenance_record(judged))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    judged = _check_note_ref(record_in)
    record = {
        "type": "pattern_note",
        "slice": PATTERN_SLICE,
        "note_id": judged.note_id,
        "pattern_id": judged.pattern_id,
        "stance": judged.stance,
    }
    record.update(_provenance_record(judged))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    judged = validate_panel(panel, source)
    record = {"type": "pattern_panel",
              "slice": PATTERN_SLICE}
    record.update(judged.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, PatternVerdict):
        judged = validate_verdict(verdict, source)
    else:
        judged = derive_verdict(_source_book(verdict), view)
    record = {"type": "pattern_verdict",
              "slice": PATTERN_SLICE}
    record.update(judged.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, PatternIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "pattern_index",
              "slice": PATTERN_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    judged = _source_book(book)
    record = {"type": "pattern_book",
              "slice": PATTERN_SLICE,
              "title": judged.title}
    record.update(judged.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(pattern: Any, source: Any = None) -> str:
    judged = _check_pattern_ref(pattern)
    return (
        f"{judged.title} - from {judged.slice_id}: "
        f"check {judged.check if judged.check else 'none'}, "
        f"claims "
        f"{', '.join(judged.claims) if judged.claims else 'none'}. "
        f"{judged.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The patterns stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"patterns stand complete.")


def view_plain_words(view: Any) -> str:
    judged = _check_view_ref(view)
    return f"View {judged.view_id}: shows {judged.view_filter} patterns."


def note_plain_words(record_in: Any) -> str:
    judged = _check_note_ref(record_in)
    return (
        f"Note {judged.note_id}: {judged.stance} "
        f"{judged.pattern_id}, toward {judged.target}. "
        f"{judged.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, PatternIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} green patterns; "
        f"red, named in its gaps: {gaps}.")

def format_pattern(pattern: Any, source: Any = None) -> str:
    judged = _check_pattern_ref(pattern)
    book = _source_book(source) if source is not None else None
    lines = [f"{judged.title} ({judged.pattern_id})"]
    lines.extend(plain_lines(judged))
    lines.append(judged.detail)
    if pattern_green(judged, book):
        lines.append(
            "This pattern stands complete - it walked the question "
            "sequence in the open from spotted to approved, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This pattern stands open - it stands named in "
            f"its gaps: {', '.join(pattern_gaps(judged, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    judged = _check_view_ref(view)
    return (
        f"View {judged.view_id}: filter {judged.view_filter} - "
        f"{judged.detail}")


def format_note(record_in: Any) -> str:
    judged = _check_note_ref(record_in)
    lines = [
        f"Pattern note {judged.stance} {judged.pattern_id} "
        f"({judged.note_id}): {judged.title}. {judged.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_check(source: Any, check: Any) -> str:
    pattern = pattern_for_check(source, check)
    if pattern is not None:
        return format_pattern(pattern, source)
    wanted = check.strip() if isinstance(check, str) else check
    return (
        f"No held pattern stands under check {wanted!r} yet - the "
        f"check reaches nothing in this book, and no pattern is "
        f"invented for it.")


def format_book(source: Any = None, slice_id: Any = None) -> str:
    book = _source_book(source)
    patterns = (patterns_for_slice(book, slice_id)
              if slice_id is not None else book.patterns)
    lines = [f"The Pattern Gate (M-214) - {book.title}"]
    lines.extend(segment_of(pattern, book) for pattern in patterns)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Pattern panel under view {panel.view_id}:"]
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
    lines = ["Pattern index, derived from the held patterns:"]
    for entry in index.entries:
        lines.append(f"{entry.check} - {entry.title} ({entry.pattern_id})")
    if index.gaps:
        lines.append(
            "Red, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_pattern_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Pattern Gate (M-214)",
        f"{book.title}: {len(book.patterns)} patterns held, "
        f"{len(green_patterns(book))} patterns standing green, "
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


def parse_pattern_args(args: Any) -> Tuple[str, Any]:
    """Parse the /pattern grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("pattern", "view", "note"):
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
