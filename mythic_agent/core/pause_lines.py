"""The pause-lines wired (roadmap slice M-208).

Part IX - The Mythic Method Engine. The roadmap
words: *destruction, irreversible infra, cost,
publishing, sending-as-user, secrets, security -
the loop cannot cross them unapproved; the lines
are data with the user's own wording preserved.*

What already ships, and what this slice adds:

* The Forge Protocol pause-lines already bind the
  work in prose - destruction, irreversible
  infrastructure, cost, public publishing, sending
  as the user, exposing secrets, weakening
  security - and this slice WIRES them into the
  loop as data, in its own module, standing in
  the M-195 copy-and-share book shape the M-207
  book stands in: one guard per campaign, and the
  guard's charge over one proposed crossing held
  as a book - a pausing. The shipped roads stand
  untouched behind their seams: this layer holds
  pausings as data over the campaign's slices and
  rewrites none of them, and the prose laws keep
  their own standing.

* No charter row names this slice: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-208 on no row, and the
  slice tests pin that absence live. The M-005
  method charter names no slice row either: its
  own words name the whole of Part IX as the
  part that executes the charter, and this slice
  is built to the roadmap words and that
  execution note together. The lines themselves
  are held as data with the user's own wording
  preserved - the pausing names its line and
  carries the wording it was checked against.

* A pausing is held whole: the slice it guards,
  named by its slice id; its title; the pause
  steps it walked, held as data in walk order;
  and the evidence it carries, held as data by
  kind. The pause walk is EXPLICIT: its sequence
  stands as data (:data:`CHECKS`,
  :data:`TRANSITIONS`) - proposed, checked,
  paused, reasked, crossed - and a pausing's
  standing is DERIVED at call time from its held
  steps and evidence alone: a pausing that opens
  anywhere but proposed, steps where the
  sequence does not allow, carries a bare claim
  in place of held evidence, or has not yet
  reached crossed stands open, named in its
  gaps. The loop cannot cross a line unapproved:
  a crossing stands complete only where the
  walk paused at the line and the approval is
  held as evidence.
* The evidence is a closed vocabulary in two
  halves: the held evidence - approval_record,
  wording_ref, crossing_ref, ledger_row,
  evidence a guard can point to - and the bare
  claims - feeling, memory, assertion, summary,
  which stand as no evidence at all. A crossing
  is judged from held evidence alone, never
  from a feeling: a pausing holding a bare
  claim stands open, named in its gaps.
* A pausing stands only for an ACTIVE slice.
  The book holds each slice it guards for as a
  reference record - its id, its title and its
  standing, active or queued, held as data
  copied from the roadmap's own telling. A
  pausing naming a slice that stands nowhere in
  the book refuses BY NAME, and a pausing for a
  slice that is not active refuses BY NAME
  beside it: the guard deals with the slice in
  hand, in roadmap order, never a queued one,
  and a slice that already stands complete is
  never crossed twice - the current pausing is
  derived, so a completed slice is never the
  current guarding twice.
* The pausing's trace is visible. A trace
  record holds one pausing's walked steps as
  one trace line, exactly as walked, beside
  the pausing. The derived trace is computed at
  call time from the pausing's held steps; a
  held trace that no longer agrees with it
  stands stale, named in the board - the trace
  is the walk itself, never a retelling of it.
* The pausing index is DERIVED at call time
  from the held pausings - one entry per
  complete pausing, under the step it stands
  at - never a second stored copy that could
  drift. A stored index, standing verdict,
  panel, trace, order or current-pausing claim
  on any record refuses by name.
* The current pausing is DERIVED at call time -
  the first held pausing, in held order, that
  does not yet stand complete - never stored
  where it could go stale: that is the slice
  the guard must look at next, and the next
  slice is dealt only when the current one
  crosses.
* The notes are held as data: a note record
  naming its pausing, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per pausing stance; holding a note
  posts none of it, the rule stands as data
  (:data:`PAUSING_RULE`), and a record claiming
  a slice was actually crossed, approved or
  reported live refuses BY NAME. The guard
  reports - and those reports, too, are held
  as data here, never sent.
* The shipped data file holds one example book
  in exactly the shape a real guard file takes,
  a loader reads a guard file anywhere on disk,
  pausings and views are shaped as session news,
  and a small in-memory registry holds records
  one by one. The agent layer owns holding a
  guard book for a session and telling from it.
  This layer reaches no live road: it crosses
  no line, approves nothing, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security, spawns
  no process and opens no network - it holds
  pausings as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The pause walk is explicit.** A pausing is
  judged against the held steps and legal steps
  alone; an illegal step stands named in its
  gaps, never silently reordered.
* **Complete stands on held evidence alone.** A
  pausing that carries a feeling, a memory, an
  assertion or a summary in place of held
  evidence stands open, named in its gaps: a
  crossing is judged from evidence, not vibes.
* **Active slices only, in roadmap order.** A
  pausing for a missing or queued slice refuses
  by name; no pausing is invented for a slice
  the guard has not dealt with.
* **Unknown stays unknown.** A pausing whose
  steps are not yet held stands with its steps
  empty - no step is invented.
* **The index, panel, verdict, trace, order
  and current pausing are derived, never
  stored.** Each is derived from the held
  pausings at call time; a stored one refuses
  by name, so it can never drift.
* **One pausing per pausing.** Two pausings
  standing for one pausing id refuse by name,
  and one note record stands per pausing
  stance.
* **The notes are data alone.** The records
  hold the feedback; holding, viewing or
  telling them crosses nothing, approves
  nothing and posts nothing.
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
    "PAUSING_RESOURCE",
    "PAUSING_SCHEMA",
    "PAUSING_SLICE",
    "PAUSING_RULE",
    "PLAIN_EXPLANATION",
    "THE_PAUSING_SLICE",
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
    "PausingRecord",
    "IndexEntry",
    "SliceRef",
    "NoteRecord",
    "PausingBook",
    "PausingIndex",
    "PausingPanel",
    "PausingPanelRow",
    "PausingRegistry",
    "PausingVerdict",
    "PausingView",
    "TargetCount",
    "trace_for_pausing",
    "trace_record",
    "board_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_pausing",
    "build_slice_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_pausing",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "pausing_for_check",
    "pausing_order",
    "pausing_record",
    "first_note",
    "format_book",
    "format_pausing",
    "format_index",
    "format_note",
    "format_check",
    "format_panel",
    "format_pausing_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "slice_record",
    "load_pausing",
    "load_pausing_file",
    "normalize_slice_state",
    "normalize_check",
    "normalize_claim_kind",
    "legal_step",
    "next_check",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_pausing",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_pausing_args",
    "green_pausings",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_pausings",
    "validate_trace",
    "validate_book",
    "validate_pausing",
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
    "pausing_gaps",
    "pausing_green",
    "pausings_for_slice",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

PAUSING_SCHEMA = "mythic.pause_lines/1"
PAUSING_SLICE = "M-208"
THE_PAUSING_SLICE = PAUSING_SLICE
PAUSING_RESOURCE = "pause_lines.yaml"
INDEX_ACTION = "index"
EXAMPLE_CHECK = "crossed"
CHECK_FIELDS = ("checks", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("reported", "held", "blocked")
SLICE_STATES = ("active", "queued")
PAUSING_RULE = (
    "pausings are held as data alone: destruction, "
    "irreversible infra, cost, publishing, "
    "sending-as-user, secrets, security - the loop "
    "cannot cross them unapproved; the lines are data "
    "with the user's own wording preserved - the pause "
    "walk stands as an explicit pause sequence - proposed, "
    "checked, paused, reasked, crossed - and a crossing "
    "completes only complete, complete being a state "
    "with evidence held - approval record, wording "
    "ref, crossing ref, ledger row - never a feeling, a memory, "
    "an assertion or a summary; holding, viewing and "
    "reading a pausing crosses nothing, approves nothing, "
    "destroys nothing and opens no network")
PLAIN_EXPLANATION = (
    "The pause-lines wired (M-208): destruction, "
    "irreversible infra, cost, publishing, "
    "sending-as-user, secrets, security - the loop "
    "cannot cross them unapproved; the lines are data "
    "with the user's own wording preserved.")
USAGE = (
    "Usage: /pauselines | /pauselines pausing <pausing-id> | "
    "/pauselines check <check> | /pauselines slice <slice-id> | "
    "/pauselines view <view-id> | /pauselines note <note-id> | "
    "/pauselines index | /pauselines panel | /pauselines verdict")

CHECKS = ("proposed", "checked", "paused", "reasked", "crossed")
HELD_EVIDENCE = ("approval_record", "wording_ref", "crossing_ref", "ledger_row")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "proposed": ("checked",),
    "checked": ("paused",),
    "paused": ("reasked", "crossed"),
    "reasked": ("checked", "paused"),
    "crossed": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a failure or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a pausing stands complete.
    A check outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_check(check: Any, failed: Any = False) -> Optional[str]:
    """The step the guard takes next, DERIVED from the sequence.

    Proposed leads to checked and checked to
    paused; at paused an unapproved crossing steps
    to reasked and an approved crossing steps to
    crossed; reasked steps back to paused for the
    re-asking; crossed is the end of the walk and
    steps nowhere. A step outside the sequence
    refuses by name.
    """
    checked = normalize_check(check)
    if checked == "proposed":
        return "checked"
    if checked == "checked":
        return "paused"
    if checked == "paused":
        return "reasked" if failed else "crossed"
    if checked == "reasked":
        return "paused"
    return None


_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "pausing_id", "seq", "slice_id", "title", "checks",
    "claims", "detail",
} | set(_PROVENANCE))
_SLICE_REF_KEYS = frozenset({
    "slice_id", "seq", "title", "state", "detail",
} | set(_PROVENANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "pausing_id", "trace", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "pausing_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered",
    "current_pausing", "next_pausing", "progress", "board",
    "current", "order", "breaks", "active"})
_LIVE_KEYS = (
    "live_pausing", "pausings_live", "live_pause",
    "pausings_propose", "proposes_slice", "proposed_live",
    "crosses_line", "crossed_live", "crosses_unapproved",
    "approves_self", "approved_live", "destroys_live",
    "publishes_live", "sends_as_user", "exposes_secret",
    "weakens_security", "runs_campaign",
    "ran_campaign", "spawns_process", "spawned_process",
    "builds_slice", "built_slice", "builds_live",
    "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "pausing_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_pausing", "sent_pausing",
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
    """A pausing's walked checks, held as data.

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
    """A pausing's asked claims: claim kinds named as data.

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
                f"{what} claims a live gate pausing or slice build "
                f"execution ({key!r} is named on it): "
                f"{PAUSING_RULE}")
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
# The held pausing: one slice cut from an active slice.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class PausingRecord:
    """One pausing slice, held as data.

    The pausing names the active slice it was
    pausinged from, by slice id, its title, its
    verifiable checks, held as data, and its
    claims, named by pausing id. The grain is
    derived, never stored: exactly one verifiable
    walk is judged against the machine. A pausing whose
    checks are not yet held stands with its
    checks empty: it stands open, named in
    its gaps, and no check is invented for it.
    The pausing is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    pausing_id: str
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
            self, "pausing_id", _clean_text(self.pausing_id, "a pausing id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "slice_id", _clean_text(self.slice_id, "an slice id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a pausing title"))
        object.__setattr__(
            self, "checks", _check_checks(self.checks))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a pausing detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.pausing_id

    @property
    def check(self) -> str:
        """The check the pausing stands at: its last walked check."""
        return self.checks[-1] if self.checks else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "pausing_id": self.pausing_id, "seq": self.seq,
            "slice_id": self.slice_id, "title": self.title,
            "checks": list(self.checks),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_pausing_ref(value: Any) -> PausingRecord:
    if not isinstance(value, PausingRecord):
        raise ValueError("a pausing must be a PausingRecord")
    return value


def validate_pausing(pausing: Any) -> PausingRecord:
    return _check_pausing_ref(pausing)


def build_pausing(record: Any = None, **kwargs: Any) -> PausingRecord:
    """Build one held pausing from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, PausingRecord):
        if kwargs:
            raise ValueError("a pausing stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a pausing must be a mapping or a PausingRecord")
    _needed(data, _RUN_KEYS, "a pausing")
    return PausingRecord(
        pausing_id=data.get("pausing_id"), seq=data.get("seq"),
        slice_id=data.get("slice_id"), title=data.get("title"),
        checks=data.get("checks"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_provenance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each pausing to the steps it took outside the machine.

    Derived from the held pausings alone: a break is
    one consecutive pair of walked checks the
    explicit gate sequence does not allow, told
    in walk order as before, then after.
    """
    found: Dict[str, Tuple[str, ...]] = {}
    for pausing in book.pausings:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(pausing.checks, pausing.checks[1:])
            if not legal_step(before, after))
        if breaks:
            found[pausing.pausing_id] = breaks
    return found

def pausing_gaps(pausing: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a pausing from standing complete.

    Judged from the pausing's own held fields alone -
    its walked steps against the explicit pause
    sequence, and its carried evidence against the
    closed vocabulary: the pausing opens at
    proposed, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a pausing stands complete only when it has
    reached crossed. The source names nothing
    further: no gap is borrowed from another
    pausing.
    """
    checked = _check_pausing_ref(pausing)
    gaps: List[str] = []
    if not checked.checks:
        gaps.append(
            "has passed through no step: the pausing has not started")
        return tuple(gaps)
    if checked.checks[0] != "proposed":
        gaps.append(
            f"opens at {checked.checks[0]}, not at proposed: "
            f"the pausing opens with the proposal")
    for before, after in zip(checked.checks, checked.checks[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"pause sequence does not allow")
    for kind in checked.claims:
        if kind in BARE_CLAIMS:
            gaps.append(
                f"carries a {kind} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if checked.checks[-1] != "crossed":
        gaps.append(
            f"has not reached crossed: the pausing stands "
            f"at {checked.checks[-1]}")
    return tuple(gaps)

def pausing_green(pausing: Any, source: Any = None) -> bool:
    return not pausing_gaps(pausing, source)


def plain_lines(pausing: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the pausing's own fields."""
    checked = _check_pausing_ref(pausing)
    return (
        f"Pausing: {checked.title}",
        f"Slice: {checked.slice_id}",
        f"Check: {checked.check if checked.check else 'none'}",
        f"Claims: "
        f"{', '.join(checked.claims) if checked.claims else 'none'}",
    )


def segment_of(pausing: Any, source: Any = None) -> str:
    checked = _check_pausing_ref(pausing)
    gaps = pausing_gaps(checked, source)
    return (
        f"{checked.pausing_id}: {checked.title} - slice: "
        f"'{checked.slice_id}' - check: "
        f"'{checked.check if checked.check else 'none'}' - "
        f"checks: {len(checked.checks)} - claims: "
        f"'{', '.join(checked.claims) if checked.claims else 'none'}' - "
        f"detail: '{checked.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held slice reference: the active slice a book pausings from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class SliceRef:
    """One slice a pausing book pausings from, held as a reference.

    The record names the slice, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 slice book's own telling. A pausing
    stands only from an active reference: the
    book refuses a pausing naming no held reference,
    and a pausing from an queued one, BY NAME.
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
    human active - the slice's pausing ids in
    derived claim order, held exactly as
    active. The trace is of the set and its
    order, never of a step: when the derived
    trace moves, this record stands stale, named
    in the board, until a new trace is active.
    """

    trace_id: str
    seq: int
    pausing_id: str
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
            self, "pausing_id", _clean_text(self.pausing_id, "an slice id"))
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
            "pausing_id": self.pausing_id, "trace": self.trace,
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
        pausing_id=data.get("pausing_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a pausing, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One pausing stance, held as data.

    The record names its pausing, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per pausing stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    pausing_id: str
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
            self, "pausing_id", _clean_text(self.pausing_id, "a pausing id"))
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
            "pausing_id": self.pausing_id, "stance": self.stance,
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
        pausing_id=data.get("pausing_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which slices a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class PausingView:
    """A view over the book: every pausing, the green, the rest."""

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


def _check_view_ref(value: Any) -> PausingView:
    if not isinstance(value, PausingView):
        raise ValueError("a view must be an PausingView")
    return value


def validate_view(view: Any) -> PausingView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> PausingView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, PausingView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an PausingView")
    _needed(data, _VIEW_KEYS, "a view")
    return PausingView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class PausingPanelRow:
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


def _row_for_pausing(pausing: PausingRecord,
                     source: Any = None) -> PausingPanelRow:
    return PausingPanelRow(
        item_id=pausing.pausing_id,
        standing="complete" if pausing_green(pausing, source) else "open",
        label=pausing.title, segment=segment_of(pausing, source),
        recorded_on=pausing.recorded_on)


def _check_row_ref(value: Any) -> PausingPanelRow:
    if not isinstance(value, PausingPanelRow):
        raise ValueError("a panel row must be an PausingPanelRow")
    return value


def validate_row(row: Any, pausing: Any = None,
                 source: Any = None) -> PausingPanelRow:
    checked = _check_row_ref(row)
    if pausing is not None:
        derived = _row_for_pausing(_check_pausing_ref(pausing), source)
        if checked != derived:
            raise ValueError(
                f"panel row {checked.item_id!r} does not agree with "
                f"the row derived from its pausing")
    return checked


def build_row(row: Any = None, pausing: Any = None,
              source: Any = None,
              **kwargs: Any) -> PausingPanelRow:
    if pausing is not None:
        derived = _row_for_pausing(_check_pausing_ref(pausing), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            PausingPanelRow(**kwargs))
        return validate_row(built, pausing, source)
    if isinstance(row, PausingPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return PausingPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return PausingPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an PausingPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[PausingPanelRow, ...]
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
        f"The pausing book holds {total_items} pausings as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown pausings "
        f"stand complete.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its pausing's own fields "
        "- the slice it guards, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any pausing.",
        "Completeness is judged from the held records alone: "
        "a pausing that steps outside the pause sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not reached crossed stands open, named in its "
        "gaps, and the pausing index is derived from the "
        "held pausings, never stored where it could drift.",
    )

@dataclass(frozen=True)
class PausingPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[PausingPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> PausingView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, PausingView):
        return view
    return book.view_for(view)


def shown_pausings(source: Any, view: Any = None
                   ) -> Tuple[PausingRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.pausings
    if resolved.view_filter == "complete":
        return tuple(g for g in book.pausings if pausing_green(g, book))
    return tuple(g for g in book.pausings if not pausing_green(g, book))


def pausings_for_slice(source: Any, slice_id: Any
                      ) -> Tuple[PausingRecord, ...]:
    wanted = _clean_text(slice_id, "an slice id")
    return tuple(
        g for g in _source_book(source).pausings if g.slice_id == wanted)


def green_pausings(source: Any) -> Tuple[PausingRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.pausings if pausing_green(g, book))


def current_pausing(source: Any) -> Optional[PausingRecord]:
    """The book's current pausing, DERIVED at call time.

    The first held pausing, in held order, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held pausings alone, so it can
    never go stale against them. A book whose every
    pausing stands complete has no current pausing.
    """
    book = _source_book(source)
    for pausing in book.pausings:
        if not pausing_green(pausing, book):
            return pausing
    return None


def derive_panel(source: Any, view: Any = None) -> PausingPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_pausings(book, resolved)
    rows = tuple(_row_for_pausing(pausing, book) for pausing in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.pausings), default="")
    green = sum(1 for g in shown if pausing_green(g, book))
    return PausingPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.pausings), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.pausings), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> PausingPanel:
    if not isinstance(value, PausingPanel):
        raise ValueError("a panel must be an PausingPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> PausingPanel:
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
                **kwargs: Any) -> PausingPanel:
    if isinstance(panel, PausingPanel):
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
        built = PausingPanel(
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
    raise ValueError("a panel must be a mapping, an PausingPanel, or derived")


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
class PausingVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> PausingVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_pausings(book, resolved)
    green = sum(1 for g in shown if pausing_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return PausingVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> PausingVerdict:
    if not isinstance(value, PausingVerdict):
        raise ValueError("a verdict must be an PausingVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> PausingVerdict:
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
                  **kwargs: Any) -> PausingVerdict:
    if isinstance(verdict, PausingVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = PausingVerdict(
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
        "a verdict must be a mapping, an PausingVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held slices' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    check: str
    pausing_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "check": self.check, "pausing_id": self.pausing_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class PausingIndex:
    """The pausing index, derived from the held pausings.

    The index names one entry per green pausing, in
    held order - the pausing's own one verifiable
    check, its pausing id and its title - and the
    pausings that do not stand complete, named in its
    gaps. Nothing here is stored on any pausing: the
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


def derive_index(source: Any) -> PausingIndex:
    """Derive the pausing index from the book's held pausings."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(check=g.check, pausing_id=g.pausing_id,
                   title=g.title)
        for g in book.pausings if pausing_green(g, book))
    gaps = tuple(
        g.pausing_id for g in book.pausings if not pausing_green(g, book))
    return PausingIndex(entries=entries, gaps=gaps)


def pausing_for_check(source: Any, check: Any) -> Optional[PausingRecord]:
    """The first held pausing one check reaches, or none - honestly."""
    if check is None:
        return None
    if not isinstance(check, str):
        raise ValueError("an check must be a string naming the check")
    wanted = check.strip()
    if not wanted:
        return None
    for pausing in _source_book(source).pausings:
        if pausing.check == wanted:
            return pausing
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held order: the pausing
    that took it and the step it took, before,
    then after. A book whose pausings all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{pausing_id}: {step}"
        for pausing_id, steps in _breaks_map(book).items()
        for step in steps)

def pausing_order(source: Any,
              slice_id: Any = None) -> Tuple[PausingRecord, ...]:
    """The held pausings in their held order, DERIVED at call time.

    Pausings stand in the order the book holds them -
    the order their slices were taken - optionally
    for one slice alone. Nothing here is stored:
    the order is the book's own held order, told.
    """
    book = _source_book(source)
    pausings = list(book.pausings)
    if slice_id is not None:
        wanted = _clean_text(slice_id, "a slice id")
        pausings = [r for r in pausings if r.slice_id == wanted]
    return tuple(pausings)

def trace_of(source: Any, pausing_id: Any) -> str:
    """One pausing's trace, DERIVED at call time.

    The pausing's walked checks joined as one trace
    line, in walk order. A pausing that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is named
    elsewhere.
    """
    pausing = _source_book(source).pausing_for(pausing_id)
    return " > ".join(pausing.checks)

def trace_for_pausing(source: Any,
                  pausing_id: Any) -> Optional[TraceRecord]:
    """The held trace for one pausing, or none - honestly."""
    wanted = _clean_text(pausing_id, "a pausing id")
    for record in _source_book(source).traces:
        if record.pausing_id == wanted:
            return record
    return None

def trace_current(source: Any, pausing_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_pausing(source, pausing_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, pausing_id)

def note_for_pausing(source: Any, pausing_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one pausing (and stance, when named)."""
    wanted = _clean_text(pausing_id, "a pausing id")
    for record in _source_book(source).notes:
        if record.pausing_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the slice targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def board_record(source: Any = None) -> Dict[str, Any]:
    """The pausing board, DERIVED here from the held pausings alone.

    The board counts the held pausings by their
    derived completeness - green and red - names
    the current pausing, the first that does not yet
    stand complete, tells each held pausing's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held pausings took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.pausings
            if ("complete" if pausing_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "pausings": number})
    current = current_pausing(book)
    traces = []
    for pausing in book.pausings:
        trace = trace_for_pausing(book, pausing.pausing_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, pausing.pausing_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"pausing_id": pausing.pausing_id, "trace": standing})
    return {
        "type": "pausing_board",
        "slice": PAUSING_SLICE,
        "standings": standings,
        "total": len(book.pausings),
        "current_pausing": current.pausing_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This slice's own roadmap standing, proved from the roadmap itself.

    The record loads this repo's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 slices in 11 parts,
    the banked prefix, the next slice where the
    campaign resumes, and M-208's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(PAUSING_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "pausing_roadmap",
        "slice": PAUSING_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m208_title": own.title,
        "m208_part": own.part,
        "m208_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: slices, pausings, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or order ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class PausingBook:
    title: str
    slices: Tuple[SliceRef, ...] = ()
    pausings: Tuple[PausingRecord, ...] = ()
    views: Tuple[PausingView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[PausingPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        slices = tuple(_check_slice_ref(g) for g in self.slices)
        pausings = tuple(_check_pausing_ref(g) for g in self.pausings)
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
        pausing_ids = set()
        pausing_seqs = set()
        for pausing in pausings:
            if pausing.pausing_id in pausing_ids:
                raise ValueError(
                    f"two pausings stand under id {pausing.pausing_id!r}")
            if pausing.seq in pausing_seqs:
                raise ValueError(
                    f"two pausings stand at sequence {pausing.seq}")
            pausing_ids.add(pausing.pausing_id)
            pausing_seqs.add(pausing.seq)
        by_slice = {ref.slice_id: ref for ref in slices}
        for pausing in (pausings if slices else ()):

            ref = by_slice.get(pausing.slice_id)
            if ref is None:
                raise ValueError(
                    f"pausing {pausing.pausing_id!r} is pausinged from slice "
                    f"{pausing.slice_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "active":
                raise ValueError(
                    f"pausing {pausing.pausing_id!r} is pausinged from slice "
                    f"{pausing.slice_id!r}, which is not active: "
                    f"no slice is pausinged from an queued slice")
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
            target = (record.pausing_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for pausing "
                    f"{record.pausing_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per pausing target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_pausings = set()
        pausing_ids = {pausing.pausing_id for pausing in pausings}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.pausing_id in trace_pausings:
                raise ValueError(
                    f"two traces stand for pausing "
                    f"{record.pausing_id!r}: one trace stands "
                    f"per pausing walk")
            if pausings and record.pausing_id not in pausing_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces pausing "
                    f"{record.pausing_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_pausings.add(record.pausing_id)
        object.__setattr__(
            self, "slices", tuple(sorted(slices, key=lambda g: g.seq)))
        object.__setattr__(
            self, "pausings", tuple(sorted(pausings, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.pausings + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.pausing_id for g in self.pausings) + tuple(
            v.view_id for v in self.views)

    def pausing_ids(self) -> Tuple[str, ...]:
        return tuple(g.pausing_id for g in self.pausings)

    def slice_ids(self) -> Tuple[str, ...]:
        return tuple(g.slice_id for g in self.slices)

    def pausing_for(self, pausing_id: Any) -> PausingRecord:
        wanted = _clean_text(pausing_id, "a pausing id")
        for pausing in self.pausings:
            if pausing.pausing_id == wanted:
                return pausing
        raise KeyError(f"no pausing named {wanted!r} stands in this book")

    def slice_for(self, slice_id: Any) -> SliceRef:
        wanted = _clean_text(slice_id, "an slice id")
        for ref in self.slices:
            if ref.slice_id == wanted:
                return ref
        raise KeyError(f"no slice named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> PausingView:
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
        for pausing in self.pausings:
            if pausing.pausing_id == wanted:
                return pausing
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "slices": [g.to_record() for g in self.slices],
            "pausings": [g.to_record() for g in self.pausings],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: PausingBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: PausingBook) -> None:
    if book.title != "The pause-lines wired at the M-207 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.slices) != 3 or len(book.pausings) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three slice references, five pausings and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m207-boundary":
        raise ValueError("the pinned panel is panel-m207-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.check for e in index.entries] != ["crossed", "crossed", "crossed"]:
        raise ValueError("the shipped example book index must derive the three held complete pausings in held order")
    if index.gaps != ("pausing-bare-crossing", "pausing-leaping-crossing"):
        raise ValueError("the shipped example book must leave the bare and leaping pausings honestly open, named in its gaps")
    found = pausing_for_check(book, EXAMPLE_CHECK)
    if found is None or found.pausing_id != "pausing-approved-crossing":
        raise ValueError("the shipped example book must reach its opening pausing under the example check")
    if trace_of(book, "pausing-approved-crossing") != "proposed > checked > paused > crossed":
        raise ValueError("the shipped example book must derive the opening pausing's trace from its walked steps")
    if not trace_current(book, "pausing-approved-crossing"):
        raise ValueError("the shipped example book must hold the opening pausing's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note road")

def validate_book(data: Any, *, require_example: bool = False) -> PausingBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, PausingBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a pausing book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live slice build or execution "
                f"({key!r} is named on it): {PAUSING_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its pausings under a view")
    if "pausing_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held pausings at call time")
    if "board" in data or "current_pausing" in data:
        raise ValueError(
            "a book stores no board and no current pausing: both are "
            "derived from its held pausings at call time")
    if "trace" in data or "order" in data:
        raise ValueError(
            "a book stores no trace and no order: both are derived "
            "from its held pausings at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != PAUSING_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{PAUSING_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != PAUSING_SLICE):
        raise ValueError(
            f"a book's slice must be {PAUSING_SLICE!r}")
    head = data.get("pausing_head") or data.get("pause_lines") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's pausing head must be a mapping")
    title = head.get("title") or data.get("title")
    slices = tuple(build_slice_ref(g) for g in data.get("slices") or ())
    pausings = tuple(build_pausing(g) for g in data.get("pausings") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = PausingBook(
        title=title, slices=slices, pausings=pausings, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = PausingBook(
        title=book.title, slices=book.slices, pausings=book.pausings,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> PausingBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (PausingBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an PausingBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> PausingBook:
    return validate_book(data, require_example=require_example)


def load_pausing(
        data: Optional[Dict[str, Any]] = None) -> PausingBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(PAUSING_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_pausing_file(path: Any) -> PausingBook:
    """Load one pausing file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: slice references, pausings and views held one by one.
# ---------------------------------------------------------------------

class PausingRegistry:
    """An in-memory holding of slice references, pausings and views.

    The registry is the pure layer's model of a
    session's pausing book: slice references are
    held under their ids, pausings are held under
    their ids, one pausing per id and per sequence,
    and views are held in recorded order, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[SliceRef] = []
        self._pausings: List[PausingRecord] = []
        self._views: List[PausingView] = []
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

    def register_pausing(self, item: Any) -> PausingRecord:
        """Hold one pausing, judged whole before held."""
        checked = _check_pausing_ref(item)
        return self._register(
            self._pausings, checked, "pausing_id", "pausing")

    def register_view(self, view: Any) -> PausingView:
        """Hold one view; a view naming no id takes a fresh one."""
        checked = _check_view_ref(view)
        if not checked.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            checked = build_view({**checked.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, checked, "view_id", "view")

    def register_book(self, book: Any) -> PausingBook:
        """Hold a whole book's records, under its title."""
        checked = build_book(book)
        if self._title is not None and checked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {checked.title!r}")
        for ref in checked.slices:
            self.register_slice_ref(ref)
        for pausing in checked.pausings:
            self.register_pausing(pausing)
        for view in checked.views:
            self.register_view(view)
        self._title = checked.title
        return self.book()

    def book(self) -> PausingBook:
        return PausingBook(
            title=self._title or "An unheld pausing book",
            slices=tuple(self._slices), pausings=tuple(self._pausings),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[SliceRef, ...]:
        return tuple(self._slices)

    def list_pausings(self) -> Tuple[PausingRecord, ...]:
        return tuple(self._pausings)

    def list_views(self) -> Tuple[PausingView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._pausings) + tuple(self._views)

    def get_slice(self, slice_id: Any) -> SliceRef:
        return self.book().slice_for(slice_id)

    def get_pausing(self, pausing_id: Any) -> PausingRecord:
        return self.book().pausing_for(pausing_id)

    def get_view(self, view_id: Any) -> PausingView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the journal target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> PausingBook:
    if source is None:
        return load_pausing()
    if isinstance(source, PausingBook):
        return source
    if isinstance(source, PausingRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def pausing_record(pausing: Any, source: Any = None) -> Dict[str, Any]:
    checked = _check_pausing_ref(pausing)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "pausing_pausing",
        "slice": PAUSING_SLICE,
        "pausing_id": checked.pausing_id,
        "slice_id": checked.slice_id,
        "title": checked.title,
        "segment": segment_of(checked, book),
        "complete": pausing_green(checked, book),
        "gaps": list(pausing_gaps(checked, book)),
    }
    record.update(_provenance_record(checked))
    return record


def slice_record(ref: Any) -> Dict[str, Any]:
    checked = _check_slice_ref(ref)
    record = {
        "type": "pausing_slice",
        "slice": PAUSING_SLICE,
        "slice_id": checked.slice_id,
        "title": checked.title,
        "state": checked.state,
    }
    record.update(_provenance_record(checked))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_trace_ref(record_in)
    record = {
        "type": "pausing_trace",
        "slice": PAUSING_SLICE,
        "trace_id": checked.trace_id,
        "pausing_id": checked.pausing_id,
        "trace": checked.trace,
    }
    record.update(_provenance_record(checked))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    checked = _check_view_ref(view)
    record = {
        "type": "pausing_view",
        "slice": PAUSING_SLICE,
        "view_id": checked.view_id, "seq": checked.seq,
        "view_filter": checked.view_filter,
    }
    record.update(_provenance_record(checked))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    checked = _check_note_ref(record_in)
    record = {
        "type": "pausing_note",
        "slice": PAUSING_SLICE,
        "note_id": checked.note_id,
        "pausing_id": checked.pausing_id,
        "stance": checked.stance,
    }
    record.update(_provenance_record(checked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    checked = validate_panel(panel, source)
    record = {"type": "pausing_panel",
              "slice": PAUSING_SLICE}
    record.update(checked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, PausingVerdict):
        checked = validate_verdict(verdict, source)
    else:
        checked = derive_verdict(_source_book(verdict), view)
    record = {"type": "pausing_verdict",
              "slice": PAUSING_SLICE}
    record.update(checked.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, PausingIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "pausing_index",
              "slice": PAUSING_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    checked = _source_book(book)
    record = {"type": "pausing_book",
              "slice": PAUSING_SLICE,
              "title": checked.title}
    record.update(checked.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(pausing: Any, source: Any = None) -> str:
    checked = _check_pausing_ref(pausing)
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
        f"The pausings stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"pausings stand complete.")


def view_plain_words(view: Any) -> str:
    checked = _check_view_ref(view)
    return f"View {checked.view_id}: shows {checked.view_filter} pausings."


def note_plain_words(record_in: Any) -> str:
    checked = _check_note_ref(record_in)
    return (
        f"Note {checked.note_id}: {checked.stance} "
        f"{checked.pausing_id}, toward {checked.target}. "
        f"{checked.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, PausingIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} green pausings; "
        f"red, named in its gaps: {gaps}.")

def format_pausing(pausing: Any, source: Any = None) -> str:
    checked = _check_pausing_ref(pausing)
    book = _source_book(source) if source is not None else None
    lines = [f"{checked.title} ({checked.pausing_id})"]
    lines.extend(plain_lines(checked))
    lines.append(checked.detail)
    if pausing_green(checked, book):
        lines.append(
            "This pausing stands complete - it walked the pause "
            "sequence in the open from proposed to crossed, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This pausing stands open - it stands named in "
            f"its gaps: {', '.join(pausing_gaps(checked, book))}, and "
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
        f"Pausing note {checked.stance} {checked.pausing_id} "
        f"({checked.note_id}): {checked.title}. {checked.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_check(source: Any, check: Any) -> str:
    pausing = pausing_for_check(source, check)
    if pausing is not None:
        return format_pausing(pausing, source)
    wanted = check.strip() if isinstance(check, str) else check
    return (
        f"No held pausing stands under check {wanted!r} yet - the "
        f"check reaches nothing in this book, and no pausing is "
        f"invented for it.")


def format_book(source: Any = None, slice_id: Any = None) -> str:
    book = _source_book(source)
    pausings = (pausings_for_slice(book, slice_id)
              if slice_id is not None else book.pausings)
    lines = [f"The Pause Gate (M-208) - {book.title}"]
    lines.extend(segment_of(pausing, book) for pausing in pausings)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Pausing panel under view {panel.view_id}:"]
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
    lines = ["Pausing index, derived from the held pausings:"]
    for entry in index.entries:
        lines.append(f"{entry.check} - {entry.title} ({entry.pausing_id})")
    if index.gaps:
        lines.append(
            "Red, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_pausing_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Pause Gate (M-208)",
        f"{book.title}: {len(book.pausings)} pausings held, "
        f"{len(green_pausings(book))} pausings standing green, "
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


def parse_pausing_args(args: Any) -> Tuple[str, Any]:
    """Parse the /pausing grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("pausing", "view", "note"):
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
