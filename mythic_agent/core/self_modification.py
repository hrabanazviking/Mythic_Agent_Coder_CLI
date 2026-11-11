"""Changes (roadmap slice M-222).

Part IX - The Mythic Method Engine. The roadmap
words: **Mythic improving *itself* under campaign rules (M-141) with the Auditor doubled — the forge may sharpen its own hammer only on the record..*

What already ships, and what this slice adds:

* The changes book already ships as data
  (M-201, ``core/milestones.py``): a roadmap/change
  file (parts, slices, acceptance checks, state) the
  app reads. This slice WIRES the book that book's
  book invites - several changes held across
  tools with one ledger over them - as data, in its
  own module, standing in the M-195 copy-and-share
  book book the M-222 book stands in: one guardkeeper
  per book, and the guardkeeper's charge over one
  change across its tool held as a book - a
  change. The shipped changes stand untouched behind
  their seams: this layer holds changes as data
  over the book's tools and rewrites none of them,
  and the changes book keeps its own standing.
  Changes stand on the ledger AS DATA alone: a
  change carries a ledger ref, a reference held in
  this book; holding, viewing or telling a change
  runs no change live, moves no keeper and files
  nothing.
* No charter row names this slice: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-222 on no row, and the
  slice tests pin that absence live. The M-005
  method charter names no slice row either: its
  own words name the whole of Part IX as the
  part that executes the charter, and this slice
  is built to the roadmap words and that
  execution note together.

* A change is held whole: the slice it
  answers for, named by its slice id; its title;
  the change steps it walked, held as data in
  walk order; and the evidence it carries, held
  as data by tool. The change walk is EXPLICIT:
  its sequence stands as data
  (:data:`CHECKS`, :data:`TRANSITIONS`) -
  proposed, drafted, guarded, tested, adopted -
  and a change's standing is DERIVED at
  call time from its held steps and evidence
  alone: a change that opens anywhere but
  proposed, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet proposed adopted stands
  open, named in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - tool_ref,
  draft_ref, keeper_record, change_ref, evidence
  a guardkeeper can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A change is
  tested from held evidence alone, never
  from a feeling: a change holding a
  bare claim stands open, named in its gaps.
* A change stands only for an ACTIVE
  slice. The book holds each slice it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  change naming a slice that stands
  nowhere in the book refuses BY NAME, and a
  change for a slice that is not active
  refuses BY NAME beside it: the guardkeeper deals with
  the slice in hand, in roadmap order, never a
  queued one, and a slice whose change already
  stands complete is never guarded twice - the
  current change is derived, so a
  completed slice is never the current change
  twice.
* The change's trace is visible. A trace
  record holds one change's walked steps
  as one trace line, exactly as walked, beside
  the change. The derived trace is
  computed at call time from the change's
  held steps; a held trace that no longer agrees
  with it stands stale, named in the ledger - the
  trace is the walk itself, never a retelling
  of it.
* The change index is DERIVED at call
  time from the held changes - one change
  per complete change, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, order or current-change
  claim on any record refuses by name.
* The current change is DERIVED at call
  time - the first held change, in held
  order, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its change, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per change stance; holding
  a note posts none of it, the rule stands as
  data (:data:`CHANGE_RULE`), and a record
  claiming a change was actually adopted,
  captured or promoted live refuses BY NAME.
  The guardkeeper changes - and those changes, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the book a real change
  file takes, a loader reads a file anywhere on
  disk, changes and views are drafted as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a change book for a session and
  telling from it. This layer reaches no live
  change: it writes no change live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no guardkeeper, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds changes
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The change walk is explicit.** A
  change is tested against the held
  steps and legal steps alone; an illegal step
  stands named in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  change that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, named in its gaps:
  a change is tested from evidence, not
  vibes.
* **Active slices only, in roadmap order.** A
  change for a missing or queued slice
  refuses by name; no change is invented
  for a slice the guardkeeper has not dealt with.
* **Unknown stays unknown.** A change
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, order
  and current change are derived, never
  stored.** Each is derived from the held
  changes at call time; a stored one
  refuses by name, so it can never drift.
* **One change per change.** Two
  changes standing for one change id
  refuse by name, and one note record stands per
  change stance.
* **The notes are data alone.** The records
  hold the feedback; holding, viewing or telling
  them writes nothing, files nothing and posts
  nothing.
"""


from __future__ import annotations

__all__ = [
    "CHECK_FIELDS",
    "CHECKS",
    "CLAIM_TOOLS",
    "HELD_EVIDENCE",
    "BARE_CLAIMS",
    "TRANSITIONS",
    "EXAMPLE_CHECK",
    "STANCES",
    "INDEX_ACTION",
    "CHANGE_RESOURCE",
    "CHANGE_SCHEMA",
    "CHANGE_SLICE",
    "CHANGE_RULE",
    "PLAIN_EXPLANATION",
    "THE_CHANGE_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "COMPLETE_WORDS",
    "TOOL_STATES",
    "Any",
    "Dict",
    "List",
    "Optional",
    "TraceRecord",
    "ChangeRecord",
    "IndexChange",
    "ToolRef",
    "NoteRecord",
    "ChangeBook",
    "ChangeIndex",
    "ChangePanel",
    "ChangePanelRow",
    "ChangeRegistry",
    "ChangeVerdict",
    "ChangeView",
    "TargetCount",
    "trace_for_change",
    "trace_record",
    "ledger_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_change",
    "build_tool_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_change",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "change_for_check",
    "change_order",
    "change_record",
    "first_note",
    "format_book",
    "format_change",
    "format_index",
    "format_note",
    "format_check",
    "format_panel",
    "format_change_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "tool_record",
    "load_change",
    "load_change_file",
    "normalize_tool_state",
    "normalize_check",
    "normalize_claim_tool",
    "legal_step",
    "next_check",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_change",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_change_args",
    "green_changes",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_changes",
    "validate_trace",
    "validate_book",
    "validate_change",
    "validate_tool_ref",
    "validate_note",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
    "change_gaps",
    "change_green",
    "changes_for_tool",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

CHANGE_SCHEMA = "mythic.self_modification/1"
CHANGE_SLICE = "M-222"
THE_CHANGE_SLICE = CHANGE_SLICE
CHANGE_RESOURCE = "self_modification.yaml"
INDEX_ACTION = "index"
EXAMPLE_CHECK = "adopted"
CHECK_FIELDS = ("checks", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("adopted", "held", "blocked")
TOOL_STATES = ("live", "dormant")
CHANGE_RULE = 'changes are held as data alone: several changes across tools stand with one ledger, keepers per change, and the human sees the whole forge at a run - a run stands as data, held by reference (a run ref), never taken live - the change walk stands as an explicit change sequence - proposed, drafted, guarded, tested, adopted - and a change completes only complete, complete being a state with evidence held - tool ref, ledger ref, keeper record, run ref - never a feeling, a memory, an assertion or a summary; holding, viewing and reading a change runs no change live, approves nothing, spawns no process and opens no network'
PLAIN_EXPLANATION = "Guarded self-modification (M-222): Mythic improving *itself* under campaign rules (M-141) with the Auditor doubled — the forge may sharpen its own hammer only on the record.."
USAGE = 'Usage: /selfmod | /selfmod change <change-id> | /selfmod check <check> | /selfmod tool <tool-id> | /selfmod view <view-id> | /selfmod note <note-id> | /selfmod index | /selfmod panel | /selfmod verdict'

CHECKS = ("proposed", "drafted", "guarded", "tested", "adopted")
HELD_EVIDENCE = ("tool_ref", "draft_ref", "keeper_record", "change_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_TOOLS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "proposed": ("drafted",),
    "drafted": ("guarded",),
    "guarded": ("tested",),
    "tested": ("proposed", "adopted"),
    "adopted": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a failure or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a change stands complete.
    A check outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_check(check: Any, failed: Any = False) -> Optional[str]:
    """The step the guardkeeper takes next, DERIVED from the sequence.

    Banked leads to drafted and drafted to
    guarded; guarded leads to tested; at
    tested a follow-up banking steps back to proposed and a finished change steps to adopted;
    adopted is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    tested = normalize_check(check)
    if tested == "proposed":
        return "drafted"
    if tested == "drafted":
        return "guarded"
    if tested == "guarded":
        return "tested"
    if tested == "tested":
        return "proposed" if failed else "adopted"
    return None


_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "change_id", "seq", "tool_id", "title", "checks",
    "claims", "detail",
} | set(_PROVENANCE))
_SLICE_REF_KEYS = frozenset({
    "tool_id", "seq", "title", "state", "detail",
} | set(_PROVENANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "change_id", "trace", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "change_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "changes", "coverage", "covered", "uncovered",
    "current_change", "next_change", "progress", "ledger",
    "current", "order", "breaks", "live"})
_LIVE_KEYS = (
    "live_change", "changes_live", "live_question",
    "changes_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "changes_live",
    "resumed_live", "tools_change", "paused_live",
    "runs_change", "ran_change", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "change_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_change", "sent_change",
    "posts_note", "posted_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_change", "filed_live", "spawns_guardkeeper", "spawned_guardkeeper", "sends_change", "sent_change", "writes_change", "wrote_change")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_checks(value: Any) -> Tuple[str, ...]:
    """A change's walked checks, held as data.

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
    """A change's asked claims: claim tools named as data.

    Each claim names one tool from the adopted
    vocabulary - the human tools the gate may ask
    and the code tools it must never ask, both
    held honestly as data - and a tool outside
    the vocabulary refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("claims must be a list of claim tools")
    return tuple(normalize_claim_tool(v) for v in value)

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
            out[key] = _clean_text(mapping.get(key), "a recorded_on tool")
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
                f"{what} claims a live gate change or slice build "
                f"execution ({key!r} is named on it): "
                f"{CHANGE_RULE}")
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


def normalize_tool_state(value: Any) -> str:
    state = _clean_text(value, "an slice state").lower()
    if state not in TOOL_STATES:
        raise ValueError(
            f"slice state {state!r} is not one of the held "
            f"states: " + ", ".join(TOOL_STATES))
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


def normalize_claim_tool(value: Any) -> str:
    tool = _clean_text(value, "a claim tool").lower()
    if tool not in CLAIM_TOOLS:
        raise ValueError(
            f"claim tool {tool!r} is not one of the held "
            f"tools: " + ", ".join(CLAIM_TOOLS))
    return tool

# ---------------------------------------------------------------------
# The held change: one slice cut from an active slice.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ChangeRecord:
    """One change slice, held as data.

    The change names the active slice it was
    held from, by slice id, its title, its
    verifiable checks, held as data, and its
    claims, named by change id. The grain is
    derived, never stored: exactly one verifiable
    walk is guarded against the machine. A change whose
    checks are not yet held stands with its
    checks empty: it stands open, named in
    its gaps, and no check is invented for it.
    The change is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    change_id: str
    seq: int
    tool_id: str
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
            self, "change_id", _clean_text(self.change_id, "a change id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "tool_id", _clean_text(self.tool_id, "an slice id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a change title"))
        object.__setattr__(
            self, "checks", _check_checks(self.checks))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a change detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.change_id

    @property
    def check(self) -> str:
        """The check the change stands at: its last walked check."""
        return self.checks[-1] if self.checks else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "change_id": self.change_id, "seq": self.seq,
            "tool_id": self.tool_id, "title": self.title,
            "checks": list(self.checks),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_change_ref(value: Any) -> ChangeRecord:
    if not isinstance(value, ChangeRecord):
        raise ValueError("a change must be a ChangeRecord")
    return value


def validate_change(change: Any) -> ChangeRecord:
    return _check_change_ref(change)


def build_change(record: Any = None, **kwargs: Any) -> ChangeRecord:
    """Build one held change from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, ChangeRecord):
        if kwargs:
            raise ValueError("a change stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a change must be a mapping or a ChangeRecord")
    _needed(data, _RUN_KEYS, "a change")
    return ChangeRecord(
        change_id=data.get("change_id"), seq=data.get("seq"),
        tool_id=data.get("tool_id"), title=data.get("title"),
        checks=data.get("checks"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_provenance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each change to the steps it took outside the machine.

    Derived from the held changes alone: a break is
    one consecutive pair of walked checks the
    explicit gate sequence does not allow, told
    in walk order as before, then after.
    """
    found: Dict[str, Tuple[str, ...]] = {}
    for change in book.changes:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(change.checks, change.checks[1:])
            if not legal_step(before, after))
        if breaks:
            found[change.change_id] = breaks
    return found

def change_gaps(change: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a change from standing complete.

    Guarded from the change's own held fields alone -
    its walked steps against the explicit question
    sequence, and its carried evidence against the
    adopted vocabulary: the change opens at
    named, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a change stands complete only when it has
    proposed adopted. The source names nothing
    further: no gap is borrowed from another
    change.
    """
    tested = _check_change_ref(change)
    gaps: List[str] = []
    if not tested.checks:
        gaps.append(
            "has passed through no step: the change has not started")
        return tuple(gaps)
    if tested.checks[0] != "proposed":
        gaps.append(
            f"opens at {tested.checks[0]}, not at proposed: "
            f"the change opens with the reflection")
    for before, after in zip(tested.checks, tested.checks[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"change sequence does not allow")
    for tool in tested.claims:
        if tool in BARE_CLAIMS:
            gaps.append(
                f"carries a {tool} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if tested.checks[-1] != "adopted":
        gaps.append(
            f"has not proposed adopted: the change stands "
            f"at {tested.checks[-1]}")
    return tuple(gaps)

def change_green(change: Any, source: Any = None) -> bool:
    return not change_gaps(change, source)


def plain_lines(change: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the change's own fields."""
    tested = _check_change_ref(change)
    return (
        f"Change: {tested.title}",
        f"Tool: {tested.tool_id}",
        f"Check: {tested.check if tested.check else 'none'}",
        f"Claims: "
        f"{', '.join(tested.claims) if tested.claims else 'none'}",
    )


def segment_of(change: Any, source: Any = None) -> str:
    tested = _check_change_ref(change)
    gaps = change_gaps(tested, source)
    return (
        f"{tested.change_id}: {tested.title} - slice: "
        f"'{tested.tool_id}' - check: "
        f"'{tested.check if tested.check else 'none'}' - "
        f"checks: {len(tested.checks)} - claims: "
        f"'{', '.join(tested.claims) if tested.claims else 'none'}' - "
        f"detail: '{tested.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held slice reference: the active slice a book changes from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ToolRef:
    """One slice a change book changes from, held as a reference.

    The record names the slice, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 slice book's own telling. A change
    stands only from an active reference: the
    book refuses a change naming no held reference,
    and a change from an queued one, BY NAME.
    """

    tool_id: str
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
            self, "tool_id", _clean_text(self.tool_id, "an slice id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(
            self, "state", normalize_tool_state(self.state))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an slice detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.tool_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "tool_id": self.tool_id, "seq": self.seq,
            "title": self.title, "state": self.state,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_tool_ref(value: Any) -> ToolRef:
    if not isinstance(value, ToolRef):
        raise ValueError("a slice reference must be an ToolRef")
    return value


def validate_tool_ref(ref: Any) -> ToolRef:
    return _check_tool_ref(ref)


def build_tool_ref(record: Any = None, **kwargs: Any) -> ToolRef:
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, ToolRef):
        if kwargs:
            raise ValueError(
                "a slice reference stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError(
            "a slice reference must be a mapping or an ToolRef")
    _needed(data, _SLICE_REF_KEYS, "a slice reference")
    return ToolRef(
        tool_id=data.get("tool_id"), seq=data.get("seq"),
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
    human active - the slice's change ids in
    derived claim order, held exactly as
    active. The trace is of the set and its
    order, never of a step: when the derived
    trace moves, this record stands stale, named
    in the ledger, until a new trace is active.
    """

    trace_id: str
    seq: int
    change_id: str
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
            self, "change_id", _clean_text(self.change_id, "an slice id"))
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
            "change_id": self.change_id, "trace": self.trace,
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
        change_id=data.get("change_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a change, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One change stance, held as data.

    The record names its change, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per change stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    change_id: str
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
            self, "change_id", _clean_text(self.change_id, "a change id"))
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
            "change_id": self.change_id, "stance": self.stance,
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
        change_id=data.get("change_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which slices a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ChangeView:
    """A view over the book: every change, the green, the rest."""

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


def _check_view_ref(value: Any) -> ChangeView:
    if not isinstance(value, ChangeView):
        raise ValueError("a view must be an ChangeView")
    return value


def validate_view(view: Any) -> ChangeView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> ChangeView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, ChangeView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an ChangeView")
    _needed(data, _VIEW_KEYS, "a view")
    return ChangeView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ChangePanelRow:
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


def _row_for_change(change: ChangeRecord,
                     source: Any = None) -> ChangePanelRow:
    return ChangePanelRow(
        item_id=change.change_id,
        standing="complete" if change_green(change, source) else "open",
        label=change.title, segment=segment_of(change, source),
        recorded_on=change.recorded_on)


def _check_row_ref(value: Any) -> ChangePanelRow:
    if not isinstance(value, ChangePanelRow):
        raise ValueError("a panel row must be an ChangePanelRow")
    return value


def validate_row(row: Any, change: Any = None,
                 source: Any = None) -> ChangePanelRow:
    tested = _check_row_ref(row)
    if change is not None:
        derived = _row_for_change(_check_change_ref(change), source)
        if tested != derived:
            raise ValueError(
                f"panel row {tested.item_id!r} does not agree with "
                f"the row derived from its change")
    return tested


def build_row(row: Any = None, change: Any = None,
              source: Any = None,
              **kwargs: Any) -> ChangePanelRow:
    if change is not None:
        derived = _row_for_change(_check_change_ref(change), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            ChangePanelRow(**kwargs))
        return validate_row(built, change, source)
    if isinstance(row, ChangePanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return ChangePanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on tool"))
    if row is None and kwargs:
        return ChangePanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an ChangePanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[ChangePanelRow, ...]
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
        f"The change book holds {total_items} changes as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown changes "
        f"stand complete.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its change's own fields "
        "- the slice it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any change.",
        "Completeness is guarded from the held records alone: "
        "a change that steps outside the change sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not proposed adopted stands open, named in its "
        "gaps, and the change index is derived from the "
        "held changes, never stored where it could drift.",
    )

@dataclass(frozen=True)
class ChangePanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[ChangePanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> ChangeView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, ChangeView):
        return view
    return book.view_for(view)


def shown_changes(source: Any, view: Any = None
                   ) -> Tuple[ChangeRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.changes
    if resolved.view_filter == "complete":
        return tuple(g for g in book.changes if change_green(g, book))
    return tuple(g for g in book.changes if not change_green(g, book))


def changes_for_tool(source: Any, tool_id: Any
                      ) -> Tuple[ChangeRecord, ...]:
    wanted = _clean_text(tool_id, "an slice id")
    return tuple(
        g for g in _source_book(source).changes if g.tool_id == wanted)


def green_changes(source: Any) -> Tuple[ChangeRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.changes if change_green(g, book))


def current_change(source: Any) -> Optional[ChangeRecord]:
    """The book's current change, DERIVED at call time.

    The first held change, in held order, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held changes alone, so it can
    never go stale against them. A book whose every
    change stands complete has no current change.
    """
    book = _source_book(source)
    for change in book.changes:
        if not change_green(change, book):
            return change
    return None


def derive_panel(source: Any, view: Any = None) -> ChangePanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_changes(book, resolved)
    rows = tuple(_row_for_change(change, book) for change in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.changes), default="")
    green = sum(1 for g in shown if change_green(g, book))
    return ChangePanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.changes), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.changes), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> ChangePanel:
    if not isinstance(value, ChangePanel):
        raise ValueError("a panel must be an ChangePanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> ChangePanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 change).
    """
    tested = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(tested.view_id)
                if tested.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(tested, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {tested.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return tested


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> ChangePanel:
    if isinstance(panel, ChangePanel):
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
        built = ChangePanel(
            panel_id=_clean_text(data.get("panel_id"), "a panel id"),
            view_id=data.get("view_id"),
            view_filter=normalize_view_filter(data.get("view_filter")),
            rows=rows,
            total_items=_check_count(
                data.get("total_items"), "a total_items count"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            target_counts=counts,
            as_of=_clean_text(data.get("as_of"), "an as_of tool"),
            account=_check_lines(data.get("account"), "the account"))
        return validate_panel(built, source)
    if panel is None and source is not None:
        return derive_panel(source, kwargs.get("view"))
    raise ValueError("a panel must be a mapping, an ChangePanel, or derived")


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
        return "adopted"
    if green_shown == 0:
        return "blocked"
    return "held"


@dataclass(frozen=True)
class ChangeVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> ChangeVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_changes(book, resolved)
    green = sum(1 for g in shown if change_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return ChangeVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> ChangeVerdict:
    if not isinstance(value, ChangeVerdict):
        raise ValueError("a verdict must be an ChangeVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> ChangeVerdict:
    tested = _check_verdict_ref(verdict)
    if tested.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {tested.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(tested.view_id)
                if tested.view_id is not None else None)
        derived = derive_verdict(book, view)
        if tested != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return tested


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> ChangeVerdict:
    if isinstance(verdict, ChangeVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = ChangeVerdict(
            verdict=_clean_text(data.get("verdict"), "a verdict"),
            view_id=data.get("view_id"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            green_shown=_check_count(
                data.get("green_shown"), "a green_shown count"),
            latest_on=_clean_text(data.get("latest_on"), "a latest tool"))
        return validate_verdict(built, source)
    if verdict is None and source is not None:
        return derive_verdict(source, kwargs.get("view"))
    raise ValueError(
        "a verdict must be a mapping, an ChangeVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held slices' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexChange:
    check: str
    change_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "check": self.check, "change_id": self.change_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class ChangeIndex:
    """The change index, derived from the held changes.

    The index names one change per green change, in
    held order - the change's own one verifiable
    check, its change id and its title - and the
    changes that do not stand complete, named in its
    gaps. Nothing here is stored on any change: the
    index is derived at call time from the held
    records alone, so it can never drift from them.
    """

    changes: Tuple[IndexChange, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "changes": [e.to_record() for e in self.changes],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> ChangeIndex:
    """Derive the change index from the book's held changes."""
    book = _source_book(source)
    changes = tuple(
        IndexChange(check=g.check, change_id=g.change_id,
                   title=g.title)
        for g in book.changes if change_green(g, book))
    gaps = tuple(
        g.change_id for g in book.changes if not change_green(g, book))
    return ChangeIndex(changes=changes, gaps=gaps)


def change_for_check(source: Any, check: Any) -> Optional[ChangeRecord]:
    """The first held change one check reaches, or none - honestly."""
    if check is None:
        return None
    if not isinstance(check, str):
        raise ValueError("an check must be a string naming the check")
    wanted = check.strip()
    if not wanted:
        return None
    for change in _source_book(source).changes:
        if change.check == wanted:
            return change
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held order: the change
    that took it and the step it took, before,
    then after. A book whose changes all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{change_id}: {step}"
        for change_id, steps in _breaks_map(book).items()
        for step in steps)

def change_order(source: Any,
              tool_id: Any = None) -> Tuple[ChangeRecord, ...]:
    """The held changes in their held order, DERIVED at call time.

    Changes stand in the order the book holds them -
    the order their slices were taken - optionally
    for one slice alone. Nothing here is stored:
    the order is the book's own held order, told.
    """
    book = _source_book(source)
    changes = list(book.changes)
    if tool_id is not None:
        wanted = _clean_text(tool_id, "a slice id")
        changes = [r for r in changes if r.tool_id == wanted]
    return tuple(changes)

def trace_of(source: Any, change_id: Any) -> str:
    """One change's trace, DERIVED at call time.

    The change's walked checks joined as one trace
    line, in walk order. A change that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is named
    elsewhere.
    """
    change = _source_book(source).change_for(change_id)
    return " > ".join(change.checks)

def trace_for_change(source: Any,
                  change_id: Any) -> Optional[TraceRecord]:
    """The held trace for one change, or none - honestly."""
    wanted = _clean_text(change_id, "a change id")
    for record in _source_book(source).traces:
        if record.change_id == wanted:
            return record
    return None

def trace_current(source: Any, change_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_change(source, change_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, change_id)

def note_for_change(source: Any, change_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one change (and stance, when named)."""
    wanted = _clean_text(change_id, "a change id")
    for record in _source_book(source).notes:
        if record.change_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the slice targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def ledger_record(source: Any = None) -> Dict[str, Any]:
    """The change ledger, DERIVED here from the held changes alone.

    The ledger counts the held changes by their
    derived completeness - green and red - names
    the current change, the first that does not yet
    stand complete, tells each held change's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held changes took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.changes
            if ("complete" if change_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "change_records": number})
    current = current_change(book)
    traces = []
    for change in book.changes:
        trace = trace_for_change(book, change.change_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, change.change_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"change_id": change.change_id, "trace": standing})
    return {
        "type": "change_well",
        "slice": CHANGE_SLICE,
        "standings": standings,
        "total": len(book.changes),
        "current_change": current.change_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This slice's own roadmap standing, proved from the roadmap itself.

    The record loads this tool's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 slices in 11 parts,
    the proposed prefix, the next slice where the
    change changes, and M-222's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(CHANGE_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "change_roadmap",
        "slice": CHANGE_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m222_title": own.title,
        "m222_part": own.part,
        "m222_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: slices, changes, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or order ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ChangeBook:
    title: str
    slices: Tuple[ToolRef, ...] = ()
    changes: Tuple[ChangeRecord, ...] = ()
    views: Tuple[ChangeView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[ChangePanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        slices = tuple(_check_tool_ref(g) for g in self.slices)
        changes = tuple(_check_change_ref(g) for g in self.changes)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        traces = tuple(_check_trace_ref(a) for a in self.traces)
        panels = tuple(_check_panel_ref(pn) for pn in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for ref in slices:
            if ref.tool_id in seen_ids:
                raise ValueError(
                    f"two slice references stand under id {ref.tool_id!r}")
            if ref.seq in seen_seqs:
                raise ValueError(
                    f"two slice references stand at sequence {ref.seq}")
            seen_ids.add(ref.tool_id)
            seen_seqs.add(ref.seq)
        change_ids = set()
        change_seqs = set()
        for change in changes:
            if change.change_id in change_ids:
                raise ValueError(
                    f"two changes stand under id {change.change_id!r}")
            if change.seq in change_seqs:
                raise ValueError(
                    f"two changes stand at sequence {change.seq}")
            change_ids.add(change.change_id)
            change_seqs.add(change.seq)
        by_slice = {ref.tool_id: ref for ref in slices}
        for change in (changes if slices else ()):

            ref = by_slice.get(change.tool_id)
            if ref is None:
                raise ValueError(
                    f"change {change.change_id!r} is held from slice "
                    f"{change.tool_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "live":
                raise ValueError(
                    f"change {change.change_id!r} is held from slice "
                    f"{change.tool_id!r}, which is not active: "
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
            target = (record.change_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for change "
                    f"{record.change_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per change target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_changes = set()
        change_ids = {change.change_id for change in changes}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.change_id in trace_changes:
                raise ValueError(
                    f"two traces stand for change "
                    f"{record.change_id!r}: one trace stands "
                    f"per change walk")
            if changes and record.change_id not in change_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces change "
                    f"{record.change_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_changes.add(record.change_id)
        object.__setattr__(
            self, "tools", tuple(sorted(slices, key=lambda g: g.seq)))
        object.__setattr__(
            self, "change_records", tuple(sorted(changes, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.changes + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.change_id for g in self.changes) + tuple(
            v.view_id for v in self.views)

    def change_ids(self) -> Tuple[str, ...]:
        return tuple(g.change_id for g in self.changes)

    def tool_ids(self) -> Tuple[str, ...]:
        return tuple(g.tool_id for g in self.slices)

    def change_for(self, change_id: Any) -> ChangeRecord:
        wanted = _clean_text(change_id, "a change id")
        for change in self.changes:
            if change.change_id == wanted:
                return change
        raise KeyError(f"no change named {wanted!r} stands in this book")

    def slice_for(self, tool_id: Any) -> ToolRef:
        wanted = _clean_text(tool_id, "an slice id")
        for ref in self.slices:
            if ref.tool_id == wanted:
                return ref
        raise KeyError(f"no slice named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> ChangeView:
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
        for change in self.changes:
            if change.change_id == wanted:
                return change
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "tools": [g.to_record() for g in self.slices],
            "change_records": [g.to_record() for g in self.changes],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: ChangeBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: ChangeBook) -> None:
    if book.title != "Guarded self-modification at the M-222 slice tool":
        raise ValueError("the shipped example book carries another title")
    if len(book.slices) != 3 or len(book.changes) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three slice references, five changes and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m221-tool":
        raise ValueError("the pinned panel is panel-m221-tool")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.check for e in index.changes] != ["adopted", "adopted", "adopted"]:
        raise ValueError("the shipped example book index must derive the three held complete changes in held order")
    if index.gaps != ("change-bare-change", "change-leaping-change"):
        raise ValueError("the shipped example book must leave the bare and leaping changes honestly open, named in its gaps")
    found = change_for_check(book, EXAMPLE_CHECK)
    if found is None or found.change_id != "change-held-change":
        raise ValueError("the shipped example book must reach its opening change under the example check")
    if trace_of(book, "change-held-change") != "proposed > drafted > guarded > tested > adopted":
        raise ValueError("the shipped example book must derive the opening change's trace from its walked steps")
    if not trace_current(book, "change-held-change"):
        raise ValueError("the shipped example book must hold the opening change's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note change")

def validate_book(data: Any, *, require_example: bool = False) -> ChangeBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, ChangeBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a change book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live slice build or execution "
                f"({key!r} is named on it): {CHANGE_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its changes under a view")
    if "change_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held changes at call time")
    if "ledger" in data or "current_change" in data:
        raise ValueError(
            "a book stores no ledger and no current change: both are "
            "derived from its held changes at call time")
    if "trace" in data or "order" in data:
        raise ValueError(
            "a book stores no trace and no order: both are derived "
            "from its held changes at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != CHANGE_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{CHANGE_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != CHANGE_SLICE):
        raise ValueError(
            f"a book's slice must be {CHANGE_SLICE!r}")
    head = data.get("change_head") or data.get("self_modification") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's change head must be a mapping")
    title = head.get("title") or data.get("title")
    slices = tuple(build_tool_ref(g) for g in data.get("tools") or ())
    changes = tuple(build_change(g) for g in data.get("change_records") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = ChangeBook(
        title=title, slices=slices, changes=changes, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = ChangeBook(
        title=book.title, slices=book.slices, changes=book.changes,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> ChangeBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (ChangeBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an ChangeBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> ChangeBook:
    return validate_book(data, require_example=require_example)


def load_change(
        data: Optional[Dict[str, Any]] = None) -> ChangeBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(CHANGE_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_change_file(path: Any) -> ChangeBook:
    """Load one change file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: slice references, changes and views held one by one.
# ---------------------------------------------------------------------

class ChangeRegistry:
    """An in-memory holding of slice references, changes and views.

    The registry is the pure layer's model of a
    session's change book: slice references are
    held under their ids, changes are held under
    their ids, one change per id and per sequence,
    and views are held in drafted order, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[ToolRef] = []
        self._changes: List[ChangeRecord] = []
        self._views: List[ChangeView] = []
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

    def register_tool_ref(self, item: Any) -> ToolRef:
        """Hold one slice reference, guarded whole before held."""
        tested = _check_tool_ref(item)
        return self._register(
            self._slices, tested, "tool_id", "slice reference")

    def register_change(self, item: Any) -> ChangeRecord:
        """Hold one change, guarded whole before held."""
        tested = _check_change_ref(item)
        return self._register(
            self._changes, tested, "change_id", "change")

    def register_view(self, view: Any) -> ChangeView:
        """Hold one view; a view naming no id takes a fresh one."""
        tested = _check_view_ref(view)
        if not tested.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            tested = build_view({**tested.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, tested, "view_id", "view")

    def register_book(self, book: Any) -> ChangeBook:
        """Hold a whole book's records, under its title."""
        tested = build_book(book)
        if self._title is not None and tested.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {tested.title!r}")
        for ref in tested.slices:
            self.register_tool_ref(ref)
        for change in tested.changes:
            self.register_change(change)
        for view in tested.views:
            self.register_view(view)
        self._title = tested.title
        return self.book()

    def book(self) -> ChangeBook:
        return ChangeBook(
            title=self._title or "An unheld change book",
            slices=tuple(self._slices), changes=tuple(self._changes),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[ToolRef, ...]:
        return tuple(self._slices)

    def list_changes(self) -> Tuple[ChangeRecord, ...]:
        return tuple(self._changes)

    def list_views(self) -> Tuple[ChangeView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._changes) + tuple(self._views)

    def get_slice(self, tool_id: Any) -> ToolRef:
        return self.book().slice_for(tool_id)

    def get_change(self, change_id: Any) -> ChangeRecord:
        return self.book().change_for(change_id)

    def get_view(self, view_id: Any) -> ChangeView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the ledger target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> ChangeBook:
    if source is None:
        return load_change()
    if isinstance(source, ChangeBook):
        return source
    if isinstance(source, ChangeRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def change_record(change: Any, source: Any = None) -> Dict[str, Any]:
    tested = _check_change_ref(change)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "change_change",
        "slice": CHANGE_SLICE,
        "change_id": tested.change_id,
        "tool_id": tested.tool_id,
        "title": tested.title,
        "segment": segment_of(tested, book),
        "complete": change_green(tested, book),
        "gaps": list(change_gaps(tested, book)),
    }
    record.update(_provenance_record(tested))
    return record


def tool_record(ref: Any) -> Dict[str, Any]:
    tested = _check_tool_ref(ref)
    record = {
        "type": "change_slice",
        "slice": CHANGE_SLICE,
        "tool_id": tested.tool_id,
        "title": tested.title,
        "state": tested.state,
    }
    record.update(_provenance_record(tested))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    tested = _check_trace_ref(record_in)
    record = {
        "type": "change_trace",
        "slice": CHANGE_SLICE,
        "trace_id": tested.trace_id,
        "change_id": tested.change_id,
        "trace": tested.trace,
    }
    record.update(_provenance_record(tested))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    tested = _check_view_ref(view)
    record = {
        "type": "change_view",
        "slice": CHANGE_SLICE,
        "view_id": tested.view_id, "seq": tested.seq,
        "view_filter": tested.view_filter,
    }
    record.update(_provenance_record(tested))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    tested = _check_note_ref(record_in)
    record = {
        "type": "change_note",
        "slice": CHANGE_SLICE,
        "note_id": tested.note_id,
        "change_id": tested.change_id,
        "stance": tested.stance,
    }
    record.update(_provenance_record(tested))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    tested = validate_panel(panel, source)
    record = {"type": "change_panel",
              "slice": CHANGE_SLICE}
    record.update(tested.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, ChangeVerdict):
        tested = validate_verdict(verdict, source)
    else:
        tested = derive_verdict(_source_book(verdict), view)
    record = {"type": "change_verdict",
              "slice": CHANGE_SLICE}
    record.update(tested.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, ChangeIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "change_index",
              "slice": CHANGE_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    tested = _source_book(book)
    record = {"type": "change_book",
              "slice": CHANGE_SLICE,
              "title": tested.title}
    record.update(tested.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(change: Any, source: Any = None) -> str:
    tested = _check_change_ref(change)
    return (
        f"{tested.title} - from {tested.tool_id}: "
        f"check {tested.check if tested.check else 'none'}, "
        f"claims "
        f"{', '.join(tested.claims) if tested.claims else 'none'}. "
        f"{tested.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The changes stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"changes stand complete.")


def view_plain_words(view: Any) -> str:
    tested = _check_view_ref(view)
    return f"View {tested.view_id}: shows {tested.view_filter} changes."


def note_plain_words(record_in: Any) -> str:
    tested = _check_note_ref(record_in)
    return (
        f"Note {tested.note_id}: {tested.stance} "
        f"{tested.change_id}, toward {tested.target}. "
        f"{tested.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, ChangeIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.changes)} green changes; "
        f"red, named in its gaps: {gaps}.")

def format_change(change: Any, source: Any = None) -> str:
    tested = _check_change_ref(change)
    book = _source_book(source) if source is not None else None
    lines = [f"{tested.title} ({tested.change_id})"]
    lines.extend(plain_lines(tested))
    lines.append(tested.detail)
    if change_green(tested, book):
        lines.append(
            "This change stands complete - it walked the question "
            "sequence in the open from proposed to adopted, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This change stands open - it stands named in "
            f"its gaps: {', '.join(change_gaps(tested, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    tested = _check_view_ref(view)
    return (
        f"View {tested.view_id}: filter {tested.view_filter} - "
        f"{tested.detail}")


def format_note(record_in: Any) -> str:
    tested = _check_note_ref(record_in)
    lines = [
        f"Change note {tested.stance} {tested.change_id} "
        f"({tested.note_id}): {tested.title}. {tested.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_check(source: Any, check: Any) -> str:
    change = change_for_check(source, check)
    if change is not None:
        return format_change(change, source)
    wanted = check.strip() if isinstance(check, str) else check
    return (
        f"No held change stands under check {wanted!r} yet - the "
        f"check reaches nothing in this book, and no change is "
        f"invented for it.")


def format_book(source: Any = None, tool_id: Any = None) -> str:
    book = _source_book(source)
    changes = (changes_for_tool(book, tool_id)
              if tool_id is not None else book.changes)
    lines = [f"The Change Gate (M-222) - {book.title}"]
    lines.extend(segment_of(change, book) for change in changes)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Change panel under view {panel.view_id}:"]
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
    lines = ["Change index, derived from the held changes:"]
    for change in index.changes:
        lines.append(f"{change.check} - {change.title} ({change.change_id})")
    if index.gaps:
        lines.append(
            "Red, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_change_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Change Gate (M-222)",
        f"{book.title}: {len(book.changes)} changes held, "
        f"{len(green_changes(book))} changes standing green, "
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


def parse_change_args(args: Any) -> Tuple[str, Any]:
    """Parse the /change grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("change", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("check", "tool"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
