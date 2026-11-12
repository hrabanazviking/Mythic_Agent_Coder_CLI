"""Cross-app method (roadmap slice M-243).

Part X - Bridges. The roadmap
words: **a seat in a hall can summon the coder; stand-ups and milestone reports post to the hall; approvals can be given in the hall under the same scope rules.******

What already ships, and what this hall adds:

* Mythic's hall faces already ship (M-233 consuming, M-234 serving, M-235 the registry, M-236 the skills standard, M-237 the custom commands, M-238 the installable bundles, M-239 the VS Code family companions book, M-240 the generic companions book, M-241 the rival importers book, M-242 the Samverk bridge book, ``mythic_agent/core/samverk_bridge.py`` the nearest kin) and the seams this slice answers already stand in the tree: the cross-app method book (``mythic_agent/core/cross_app_method.py``, M-231) already names Samtal slices as tracked externals the forge can see, and the hall itself - Samtal, Volmarr's own longhouse - stands as the place his seats gather - this slice is that hall's bridge book: a seat in a hall can summon the coder, stand-ups and milestone reports post to the hall, and approvals can be given in the hall under the same scope rules, each piece of hall work held as data under one dispatch record, the hall, seat, report, approval and scope declared BEFORE any standing is granted, the dispatch a local record - the hall's own road provides the surfaces as data here - with no coder summoned live, no report posted live and no approval given live. The bridge book WIRES that hall face as data, in its own module, standing in the M-195 copy-and-share
  book book the M-243 book stands in: one tracker
  per book, and the tracker's charge over one
  dispatch across its hall held as a book - a
  dispatch. The shipped dispatches stand untouched behind
  their seams: this layer holds dispatches as data
  over the book's halls and rewrites none of them,
  and the dispatches book keeps its own standing.
  Dispatches stand on the ledger AS DATA alone: a
  dispatch carries a ledger ref, a reference held in
  this book; holding, viewing or telling a dispatch
  halls no dispatch live, moves no keeper and files
  nothing.
* No charter row names this hall: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-243 on no row, and the
  hall tests pin that absence live. The M-005
  method charter names no hall row either: its
  own words name the whole of Part IX (M-201
  to M-232) as the part that executes the
  charter; Part X stands on the roadmap's own
  words, and this slice is built to those words.

* A dispatch is held whole: the hall it
  answers for, summoned by its hall id; its title;
  the dispatch steps it walked, held as data in
  walk dispatch; and the evidence it carries, held
  as data by hall. The dispatch walk is EXPLICIT:
  its sequence stands as data
  (:data:`STAGES`, :data:`TRANSITIONS`) -
  summoned, heard, answered, approved, held -
  and a dispatch's standing is DERIVED at
  call time from its held steps and evidence
  alone: a dispatch that opens anywhere but
  summoned, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet summoned held stands
  open, summoned in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - hall_ref,
  seat_ref, report_ref, approval_ref, reach_ref, evidence
  a tracker can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A dispatch is
  approved from held evidence alone, never
  from a feeling: a dispatch holding a
  bare claim stands open, summoned in its gaps.
* A dispatch stands only for an ACTIVE
  hall. The book holds each hall it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  dispatch naming a hall that stands
  nowhere in the book refuses BY NAME, and a
  dispatch for a hall that is not active
  refuses BY NAME beside it: the tracker deals with
  the hall in hand, in roadmap dispatch, never a
  queued one, and a hall whose dispatch already
  stands complete is never answered twice - the
  current dispatch is derived, so a
  completed hall is never the current dispatch
  twice.
* The dispatch's trace is visible. A trace
  record holds one dispatch's walked steps
  as one trace line, exactly as walked, beside
  the dispatch. The derived trace is
  computed at call time from the dispatch's
  held steps; a held trace that no longer agrees
  with it stands stale, summoned in the ledger - the
  trace is the walk itself, never a retelling
  of it.
* The dispatch index is DERIVED at call
  time from the held dispatches - one dispatch
  per complete dispatch, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, dispatch or current-dispatch
  claim on any record refuses by name.
* The current dispatch is DERIVED at call
  time - the first held dispatch, in held
  dispatch, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its dispatch, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per dispatch stance; holding
  a note posts none of it, the rule stands as
  data (:data:`DISPATCH_RULE`), and a record
  claiming a dispatch was actually held,
  captured or promoted live refuses BY NAME.
  The tracker dispatches - and those dispatches, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the book a real dispatch
  file takes, a loader reads a file anywhere on
  disk, dispatches and views are heard as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a dispatch book for a session and
  telling from it. This layer reaches no live
  dispatch: it writes no dispatch live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no tracker, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds dispatches
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The dispatch walk is explicit.** A
  dispatch is approved against the held
  steps and legal steps alone; an illegal step
  stands summoned in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  dispatch that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, summoned in its gaps:
  a dispatch is approved from evidence, not
  vibes.
* **Active halls only, in roadmap dispatch.** A
  dispatch for a missing or queued hall
  refuses by name; no dispatch is invented
  for a hall the tracker has not heard with.
* **Unknown stays unknown.** A dispatch
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, dispatch
  and current dispatch are derived, never
  stored.** Each is derived from the held
  dispatches at call time; a stored one
  refuses by name, so it can never drift.
* **One dispatch per dispatch.** Two
  dispatches standing for one dispatch id
  refuse by name, and one note record stands per
  dispatch stance.
* **The notes are data alone.** The records
  hold the feedback; holding, viewing or telling
  them writes nothing, files nothing and posts
  nothing.
"""


from __future__ import annotations

__all__ = [
    "STAGE_FIELDS",
    "STAGES",
    "CLAIM_KINDS",
    "HELD_EVIDENCE",
    "BARE_CLAIMS",
    "TRANSITIONS",
    "EXAMPLE_STAGE",
    "STANCES",
    "INDEX_ACTION",
    "DISPATCH_RESOURCE",
    "DISPATCH_SCHEMA",
    "DISPATCH_SLICE",
    "DISPATCH_RULE",
    "PLAIN_EXPLANATION",
    "THE_DISPATCH_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "COMPLETE_WORDS",
    "HALL_STATES",
    "REACHES",
    "Any",
    "Dict",
    "List",
    "Optional",
    "TraceRecord",
    "DispatchRecord",
    "IndexDispatch",
    "HallRef",
    "NoteRecord",
    "DispatchBook",
    "DispatchIndex",
    "DispatchPanel",
    "DispatchPanelRow",
    "DispatchRegistry",
    "DispatchVerdict",
    "DispatchView",
    "TargetCount",
    "trace_for_dispatch",
    "trace_record",
    "ledger_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_dispatch",
    "build_hall_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_dispatch",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "dispatch_for_check",
    "dispatch_dispatch",
    "dispatch_record",
    "first_note",
    "format_book",
    "format_dispatch",
    "format_index",
    "format_note",
    "format_stage",
    "format_panel",
    "format_dispatch_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "hall_record",
    "load_dispatch",
    "load_dispatch_file",
    "normalize_hall_state",
    "normalize_reach",
    "normalize_stage",
    "normalize_claim_kind",
    "legal_step",
    "next_stage",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_dispatch",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_dispatch_args",
    "green_dispatches",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_dispatches",
    "validate_trace",
    "validate_book",
    "validate_dispatch",
    "validate_hall_ref",
    "validate_note",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
    "dispatch_gaps",
    "dispatch_green",
    "dispatches_for_hall",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

DISPATCH_SCHEMA = "mythic.samtal_bridge/1"
DISPATCH_SLICE = "M-243"
THE_DISPATCH_SLICE = DISPATCH_SLICE
DISPATCH_RESOURCE = "samtal_bridge.yaml"
INDEX_ACTION = "index"
EXAMPLE_STAGE = "held"
STAGE_FIELDS = ("stages", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("held", "held", "blocked")
HALL_STATES = ("live", "dormant")
REACHES = ("direct", "relayed", "unlinked")
DISPATCH_RULE = "dispatches are held as data alone: a seat in a hall can summon the coder, stand-ups and milestone reports post to the hall, and approvals can be given in the hall under the same scope rules (the reaches direct, relayed and unlinked, one reach held per hall as data) - one dispatch shelf per book, and the shelf charge over one dispatch held as a dispatch - a dispatch stands as data, held by reference (a hall ref), never run live - the dispatch walk stands as an explicit dispatch sequence - summoned, heard, answered, approved, held - and a dispatch completes only complete, complete being a state with evidence held - hall ref, seat ref, report ref, approval ref, scope ref, reach ref - never a feeling, a memory, an assertion or a summary; a credential or key named in a hall record is never claimed held safely - it is refused by name and lands nowhere, its custody road being Kista - and a dispatch approved without answering, or held before it is approved, stands open, named in its gaps; a dispatch on an unlinked hall stands complete only with its reach held as a reach_ref; defining, reading, listing and telling a dispatch summons no coder live, posts no report to the hall, gives no approval and writes nothing outside held records"
PLAIN_EXPLANATION = "Samtal bridge (M-243): a seat in a hall can summon the coder; stand-ups and milestone reports post to the hall; approvals can be given in the hall under the same scope rules."
USAGE = 'Usage: /samtalbridge | /samtalbridge dispatch <dispatch-id> | /samtalbridge stage <stage> | /samtalbridge hall <hall-id> | /samtalbridge view <view-id> | /samtalbridge note <note-id> | /samtalbridge index | /samtalbridge panel | /samtalbridge verdict'

STAGES = ("summoned", "heard", "answered", "approved", "held")
HELD_EVIDENCE = ("hall_ref", "seat_ref", "report_ref", "approval_ref", "scope_ref", "reach_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "summoned": ("heard",),
    "heard": ("answered",),
    "answered": ("approved",),
    "approved": ("summoned", "held"),
    "held": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a dispatch or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a dispatch stands complete.
    A stage outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_stage(stage: Any, failed: Any = False) -> Optional[str]:
    """The step the tracker takes next, DERIVED from the sequence.

    Banked leads to heard and heard to
    answered; answered leads to approved; at
    approved a follow-up banking steps back to summoned and a finished dispatch steps to held;
    held is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    approved = normalize_stage(stage)
    if approved == "summoned":
        return "heard"
    if approved == "heard":
        return "answered"
    if approved == "answered":
        return "approved"
    if approved == "approved":
        return "summoned" if failed else "held"
    return None


_HELDANCE = ("recorded_on", "actor", "repo", "origin_session")
_RUN_KEYS = frozenset({
    "dispatch_id", "seq", "hall_id", "title", "stages",
    "claims", "detail",
} | set(_HELDANCE))
_SLICE_REF_KEYS = frozenset({
    "hall_id", "seq", "title", "state", "reach", "detail",
} | set(_HELDANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "dispatch_id", "trace", "detail",
} | set(_HELDANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_HELDANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "dispatch_id", "stance", "target", "title",
    "detail",
} | set(_HELDANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "dispatches", "coverage", "covered", "uncovered",
    "current_dispatch", "next_dispatch", "progress", "ledger",
    "current", "dispatch", "breaks", "live"})
_LIVE_KEYS = (
    "live_dispatch", "dispatches_live", "live_question",
    "dispatches_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "dispatches_live",
    "resumed_live", "runs_dispatch", "paused_live",
    "runs_dispatch", "ran_dispatch", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "dispatch_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_dispatch", "sent_dispatch",
    "posts_note", "held_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_dispatch", "filed_live", "spawns_tracker", "spawned_tracker", "sends_dispatch", "sent_dispatch", "writes_dispatch", "wrote_dispatch")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_stages(value: Any) -> Tuple[str, ...]:
    """A dispatch's walked stages, held as data.

    The stages stand as a list of stage names in
    walk dispatch, each one a stage of the explicit
    gate sequence; a walk not yet held stands
    honestly empty - no stage is invented - and
    a name outside the machine refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("stages must be a list of gate sequence stages")
    return tuple(normalize_stage(v) for v in value)

def _check_claims(value: Any) -> Tuple[str, ...]:
    """A dispatch's asked claims: claim halls summoned as data.

    Each claim names one hall from the held
    vocabulary - the human halls the gate may ask
    and the code halls it must never ask, both
    held honestly as data - and a hall outside
    the vocabulary refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("claims must be a list of claim halls")
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


def _heldance(mapping: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key in _HELDANCE:
        if key == "recorded_on":
            out[key] = _clean_text(mapping.get(key), "a recorded_on hall")
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
                f"{what} claims a live gate dispatch or hall build "
                f"execution ({key!r} is summoned on it): "
                f"{DISPATCH_RULE}")
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


def normalize_hall_state(value: Any) -> str:
    state = _clean_text(value, "an hall state").lower()
    if state not in HALL_STATES:
        raise ValueError(
            f"hall state {state!r} is not one of the held "
            f"states: " + ", ".join(HALL_STATES))
    return state


def normalize_reach(value: Any) -> str:
    reach = _clean_text(value, "a reach").lower()
    if reach not in REACHES:
        raise ValueError(
            f"reach {reach!r} is not one of the "
            f"hall dispatch reachs: " + ", ".join(REACHES))
    return reach


def normalize_view_filter(value: Any) -> str:
    view_filter = _clean_text(value, "a view filter").lower()
    if view_filter not in VIEW_FILTERS:
        raise ValueError(
            f"view filter {view_filter!r} is not one of the held "
            f"filters: " + ", ".join(VIEW_FILTERS))
    return view_filter


def normalize_stage(value: Any) -> str:
    stage = _clean_text(value, "a stage").lower()
    if stage not in STAGES:
        raise ValueError(
            f"stage {stage!r} is not one of the held "
            f"stages: " + ", ".join(STAGES))
    return stage


def normalize_claim_kind(value: Any) -> str:
    hall = _clean_text(value, "a claim hall").lower()
    if hall not in CLAIM_KINDS:
        raise ValueError(
            f"claim hall {hall!r} is not one of the held "
            f"halls: " + ", ".join(CLAIM_KINDS))
    return hall

# ---------------------------------------------------------------------
# The held dispatch: one hall cut from an active hall.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class DispatchRecord:
    """One dispatch hall, held as data.

    The dispatch names the active hall it was
    held from, by hall id, its title, its
    verifiable stages, held as data, and its
    claims, summoned by dispatch id. The grain is
    derived, never stored: exactly one verifiable
    walk is answered against the machine. A dispatch whose
    stages are not yet held stands with its
    stages empty: it stands open, summoned in
    its gaps, and no stage is invented for it.
    The dispatch is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    dispatch_id: str
    seq: int
    hall_id: str
    title: str
    stages: Tuple[str, ...] = ()
    claims: Tuple[str, ...] = ()
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    repo: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "dispatch_id", _clean_text(self.dispatch_id, "a dispatch id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "hall_id", _clean_text(self.hall_id, "an hall id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a dispatch title"))
        object.__setattr__(
            self, "stages", _check_stages(self.stages))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a dispatch detail"))
        for key in _HELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.dispatch_id

    @property
    def stage(self) -> str:
        """The stage the dispatch stands at: its last walked stage."""
        return self.stages[-1] if self.stages else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "dispatch_id": self.dispatch_id, "seq": self.seq,
            "hall_id": self.hall_id, "title": self.title,
            "stages": list(self.stages),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _HELDANCE:
            record[key] = getattr(self, key)
        return record


def _check_reach_ref(value: Any) -> DispatchRecord:
    if not isinstance(value, DispatchRecord):
        raise ValueError("a dispatch must be a DispatchRecord")
    return value


def validate_dispatch(dispatch: Any) -> DispatchRecord:
    return _check_reach_ref(dispatch)


def build_dispatch(record: Any = None, **kwargs: Any) -> DispatchRecord:
    """Build one held dispatch from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, DispatchRecord):
        if kwargs:
            raise ValueError("a dispatch stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a dispatch must be a mapping or a DispatchRecord")
    _needed(data, _RUN_KEYS, "a dispatch")
    return DispatchRecord(
        dispatch_id=data.get("dispatch_id"), seq=data.get("seq"),
        hall_id=data.get("hall_id"), title=data.get("title"),
        stages=data.get("stages"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_heldance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each dispatch to the steps it took outside the machine.

    Derived from the held dispatches alone: a break is
    one consecutive pair of walked stages the
    explicit gate sequence does not allow, told
    in walk dispatch as before, then after.
    """
    summoned: Dict[str, Tuple[str, ...]] = {}
    for dispatch in book.dispatches:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(dispatch.stages, dispatch.stages[1:])
            if not legal_step(before, after))
        if breaks:
            summoned[dispatch.dispatch_id] = breaks
    return summoned

def dispatch_gaps(dispatch: Any, hall: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a dispatch from standing complete.

    Guarded from the dispatch's own held fields alone -
    its walked steps against the explicit question
    sequence, and its held evidence against the
    held vocabulary: the dispatch opens at
    summoned, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a dispatch stands complete only when it has
    summoned held. The hall names nothing
    further: no gap is borrowed from another
    dispatch.
    """
    approved = _check_reach_ref(dispatch)
    gaps: List[str] = []
    if not approved.stages:
        gaps.append(
            "has passed through no step: the dispatch has not started")
        return tuple(gaps)
    if approved.stages[0] != "summoned":
        gaps.append(
            f"opens at {approved.stages[0]}, not at summoned: "
            f"the dispatch opens with the reflection")
    for before, after in zip(approved.stages, approved.stages[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"dispatch sequence does not allow")
    for hall in approved.claims:
        if hall in BARE_CLAIMS:
            gaps.append(
                f"carries a {hall} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if hall is not None:
        try:
            _ref = _hall_book(hall).slice_for(approved.hall_id)
        except Exception:
            _ref = None
        if _ref is not None and _ref.reach == "unlinked" and \
                "reach_ref" not in approved.claims:
            gaps.append(
                "stands approved on an unlinked hall with no "
                "reach_ref held: the reach for the "
                "hall is unlinked")
    if approved.stages[-1] != "held":
        gaps.append(
            f"has not reached held: the dispatch stands "
            f"at {approved.stages[-1]}")
    return tuple(gaps)

def dispatch_green(dispatch: Any, hall: Any = None) -> bool:
    return not dispatch_gaps(dispatch, hall)


def plain_lines(dispatch: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the dispatch's own fields."""
    approved = _check_reach_ref(dispatch)
    return (
        f"Dispatch: {approved.title}",
        f"Hall: {approved.hall_id}",
        f"Stage: {approved.stage if approved.stage else 'none'}",
        f"Claims: "
        f"{', '.join(approved.claims) if approved.claims else 'none'}",
    )


def segment_of(dispatch: Any, hall: Any = None) -> str:
    approved = _check_reach_ref(dispatch)
    gaps = dispatch_gaps(approved, hall)
    return (
        f"{approved.dispatch_id}: {approved.title} - hall: "
        f"'{approved.hall_id}' - stage: "
        f"'{approved.stage if approved.stage else 'none'}' - "
        f"stages: {len(approved.stages)} - claims: "
        f"'{', '.join(approved.claims) if approved.claims else 'none'}' - "
        f"detail: '{approved.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held hall reference: the active hall a book dispatches from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class HallRef:
    """One hall a dispatch book dispatches from, held as a reference.

    The record names the hall, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 hall book's own telling. A dispatch
    stands only from an active reference: the
    book refuses a dispatch naming no held reference,
    and a dispatch from an queued one, BY NAME.
    """

    hall_id: str
    seq: int
    title: str
    state: str
    reach: str = "direct"
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    repo: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "hall_id", _clean_text(self.hall_id, "an hall id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(
            self, "state", normalize_hall_state(self.state))
        object.__setattr__(
            self, "reach", normalize_reach(self.reach))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an hall detail"))
        for key in _HELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.hall_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "hall_id": self.hall_id, "seq": self.seq,
            "title": self.title, "state": self.state,
            "reach": self.reach,
            "detail": self.detail,
        }
        for key in _HELDANCE:
            record[key] = getattr(self, key)
        return record


def _check_hall_ref(value: Any) -> HallRef:
    if not isinstance(value, HallRef):
        raise ValueError("a hall reference must be an HallRef")
    return value


def validate_hall_ref(ref: Any) -> HallRef:
    return _check_hall_ref(ref)


def build_hall_ref(record: Any = None, **kwargs: Any) -> HallRef:
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, HallRef):
        if kwargs:
            raise ValueError(
                "a hall reference stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError(
            "a hall reference must be a mapping or an HallRef")
    _needed(data, _SLICE_REF_KEYS, "a hall reference")
    return HallRef(
        hall_id=data.get("hall_id"), seq=data.get("seq"),
        title=data.get("title"), state=data.get("state"), reach=data.get("reach") or "direct",
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held trace trace: the human approves the trace, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TraceRecord:
    """One trace trace, held as data.

    The record names its hall and the trace the
    human active - the hall's dispatch ids in
    derived claim dispatch, held exactly as
    active. The trace is of the set and its
    dispatch, never of a step: when the derived
    trace moves, this record stands stale, summoned
    in the ledger, until a new trace is active.
    """

    trace_id: str
    seq: int
    dispatch_id: str
    trace: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    repo: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "trace_id",
            _clean_text(self.trace_id, "an trace id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "dispatch_id", _clean_text(self.dispatch_id, "an hall id"))
        object.__setattr__(
            self, "trace", _clean_text(self.trace, "an active trace"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an trace detail"))
        for key in _HELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.trace_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "trace_id": self.trace_id, "seq": self.seq,
            "dispatch_id": self.dispatch_id, "trace": self.trace,
            "detail": self.detail,
        }
        for key in _HELDANCE:
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
        dispatch_id=data.get("dispatch_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a dispatch, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One dispatch stance, held as data.

    The record names its dispatch, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per dispatch stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    dispatch_id: str
    stance: str
    target: str
    title: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    repo: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "note_id", _clean_text(self.note_id, "a stance id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "dispatch_id", _clean_text(self.dispatch_id, "a dispatch id"))
        object.__setattr__(self, "stance", normalize_stance(self.stance))
        object.__setattr__(
            self, "target", _clean_text(self.target, "a stance target"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a stance title"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a stance detail"))
        for key in _HELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.note_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "note_id": self.note_id, "seq": self.seq,
            "dispatch_id": self.dispatch_id, "stance": self.stance,
            "target": self.target, "title": self.title,
            "detail": self.detail,
        }
        for key in _HELDANCE:
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
        dispatch_id=data.get("dispatch_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held view: which halls a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class DispatchView:
    """A view over the book: every dispatch, the green, the rest."""

    view_id: str
    seq: int
    view_filter: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    repo: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "view_id", _clean_text(self.view_id, "a view id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "view_filter", normalize_view_filter(self.view_filter))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a view detail"))
        for key in _HELDANCE:
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
        for key in _HELDANCE:
            record[key] = getattr(self, key)
        return record


def _check_view_ref(value: Any) -> DispatchView:
    if not isinstance(value, DispatchView):
        raise ValueError("a view must be an DispatchView")
    return value


def validate_view(view: Any) -> DispatchView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> DispatchView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, DispatchView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an DispatchView")
    _needed(data, _VIEW_KEYS, "a view")
    return DispatchView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class DispatchPanelRow:
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


def _row_for_dispatch(dispatch: DispatchRecord,
                     hall: Any = None) -> DispatchPanelRow:
    return DispatchPanelRow(
        item_id=dispatch.dispatch_id,
        standing="complete" if dispatch_green(dispatch, hall) else "open",
        label=dispatch.title, segment=segment_of(dispatch, hall),
        recorded_on=dispatch.recorded_on)


def _check_row_ref(value: Any) -> DispatchPanelRow:
    if not isinstance(value, DispatchPanelRow):
        raise ValueError("a panel row must be an DispatchPanelRow")
    return value


def validate_row(row: Any, dispatch: Any = None,
                 hall: Any = None) -> DispatchPanelRow:
    approved = _check_row_ref(row)
    if dispatch is not None:
        derived = _row_for_dispatch(_check_reach_ref(dispatch), hall)
        if approved != derived:
            raise ValueError(
                f"panel row {approved.item_id!r} does not agree with "
                f"the row derived from its dispatch")
    return approved


def build_row(row: Any = None, dispatch: Any = None,
              hall: Any = None,
              **kwargs: Any) -> DispatchPanelRow:
    if dispatch is not None:
        derived = _row_for_dispatch(_check_reach_ref(dispatch), hall)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            DispatchPanelRow(**kwargs))
        return validate_row(built, dispatch, hall)
    if isinstance(row, DispatchPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return DispatchPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on hall"))
    if row is None and kwargs:
        return DispatchPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an DispatchPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[DispatchPanelRow, ...]
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
        f"The dispatch book holds {total_items} dispatches as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown dispatches "
        f"stand complete.",
        "Rows stand in held dispatch, the dispatch the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its dispatch's own fields "
        "- the hall it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any dispatch.",
        "Completeness is answered from the held records alone: "
        "a dispatch that steps outside the dispatch sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not summoned held stands open, summoned in its "
        "gaps, and the dispatch index is derived from the "
        "held dispatches, never stored where it could drift.",
    )

@dataclass(frozen=True)
class DispatchPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[DispatchPanelRow, ...]
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


def _resolve_view(hall: Any, view: Any) -> DispatchView:
    book = _hall_book(hall)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, DispatchView):
        return view
    return book.view_for(view)


def shown_dispatches(hall: Any, view: Any = None
                   ) -> Tuple[DispatchRecord, ...]:
    book = _hall_book(hall)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.dispatches
    if resolved.view_filter == "complete":
        return tuple(g for g in book.dispatches if dispatch_green(g, book))
    return tuple(g for g in book.dispatches if not dispatch_green(g, book))


def dispatches_for_hall(hall: Any, hall_id: Any
                      ) -> Tuple[DispatchRecord, ...]:
    wanted = _clean_text(hall_id, "an hall id")
    return tuple(
        g for g in _hall_book(hall).dispatches if g.hall_id == wanted)


def green_dispatches(hall: Any) -> Tuple[DispatchRecord, ...]:
    book = _hall_book(hall)
    return tuple(g for g in book.dispatches if dispatch_green(g, book))


def current_dispatch(hall: Any) -> Optional[DispatchRecord]:
    """The book's current dispatch, DERIVED at call time.

    The first held dispatch, in held dispatch, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held dispatches alone, so it can
    never go stale against them. A book whose every
    dispatch stands complete has no current dispatch.
    """
    book = _hall_book(hall)
    for dispatch in book.dispatches:
        if not dispatch_green(dispatch, book):
            return dispatch
    return None


def derive_panel(hall: Any, view: Any = None) -> DispatchPanel:
    book = _hall_book(hall)
    resolved = _resolve_view(book, view)
    shown = shown_dispatches(book, resolved)
    rows = tuple(_row_for_dispatch(dispatch, book) for dispatch in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.dispatches), default="")
    green = sum(1 for g in shown if dispatch_green(g, book))
    return DispatchPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.dispatches), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.dispatches), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> DispatchPanel:
    if not isinstance(value, DispatchPanel):
        raise ValueError("a panel must be an DispatchPanel")
    return value


def validate_panel(panel: Any, hall: Any = None) -> DispatchPanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 dispatch).
    """
    approved = _check_panel_ref(panel)
    if hall is not None:
        book = _hall_book(hall)
        view = (book.view_for(approved.view_id)
                if approved.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(approved, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {approved.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return approved


def build_panel(panel: Any = None, hall: Any = None,
                **kwargs: Any) -> DispatchPanel:
    if isinstance(panel, DispatchPanel):
        if kwargs:
            raise ValueError("a panel stands whole or by fields, not both")
        return validate_panel(panel, hall)
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
        built = DispatchPanel(
            panel_id=_clean_text(data.get("panel_id"), "a panel id"),
            view_id=data.get("view_id"),
            view_filter=normalize_view_filter(data.get("view_filter")),
            rows=rows,
            total_items=_check_count(
                data.get("total_items"), "a total_items count"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            target_counts=counts,
            as_of=_clean_text(data.get("as_of"), "an as_of hall"),
            account=_check_lines(data.get("account"), "the account"))
        return validate_panel(built, hall)
    if panel is None and hall is not None:
        return derive_panel(hall, kwargs.get("view"))
    raise ValueError("a panel must be a mapping, an DispatchPanel, or derived")


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
        return "held"
    if green_shown == 0:
        return "blocked"
    return "held"


@dataclass(frozen=True)
class DispatchVerdict:
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


def derive_verdict(hall: Any, view: Any = None) -> DispatchVerdict:
    book = _hall_book(hall)
    resolved = _resolve_view(book, view)
    shown = shown_dispatches(book, resolved)
    green = sum(1 for g in shown if dispatch_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return DispatchVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> DispatchVerdict:
    if not isinstance(value, DispatchVerdict):
        raise ValueError("a verdict must be an DispatchVerdict")
    return value


def validate_verdict(verdict: Any, hall: Any = None) -> DispatchVerdict:
    approved = _check_verdict_ref(verdict)
    if approved.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {approved.verdict!r} is not a held word")
    if hall is not None:
        book = _hall_book(hall)
        view = (book.view_for(approved.view_id)
                if approved.view_id is not None else None)
        derived = derive_verdict(book, view)
        if approved != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return approved


def build_verdict(verdict: Any = None, hall: Any = None,
                  **kwargs: Any) -> DispatchVerdict:
    if isinstance(verdict, DispatchVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, hall)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = DispatchVerdict(
            verdict=_clean_text(data.get("verdict"), "a verdict"),
            view_id=data.get("view_id"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            green_shown=_check_count(
                data.get("green_shown"), "a green_shown count"),
            latest_on=_clean_text(data.get("latest_on"), "a latest hall"))
        return validate_verdict(built, hall)
    if verdict is None and hall is not None:
        return derive_verdict(hall, kwargs.get("view"))
    raise ValueError(
        "a verdict must be a mapping, an DispatchVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held halls' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexDispatch:
    stage: str
    dispatch_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "stage": self.stage, "dispatch_id": self.dispatch_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class DispatchIndex:
    """The dispatch index, derived from the held dispatches.

    The index names one dispatch per green dispatch, in
    held dispatch - the dispatch's own one verifiable
    stage, its dispatch id and its title - and the
    dispatches that do not stand complete, summoned in its
    gaps. Nothing here is stored on any dispatch: the
    index is derived at call time from the held
    records alone, so it can never drift from them.
    """

    dispatches: Tuple[IndexDispatch, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "dispatches": [e.to_record() for e in self.dispatches],
            "gaps": list(self.gaps),
        }


def derive_index(hall: Any) -> DispatchIndex:
    """Derive the dispatch index from the book's held dispatches."""
    book = _hall_book(hall)
    dispatches = tuple(
        IndexDispatch(stage=g.stage, dispatch_id=g.dispatch_id,
                   title=g.title)
        for g in book.dispatches if dispatch_green(g, book))
    gaps = tuple(
        g.dispatch_id for g in book.dispatches if not dispatch_green(g, book))
    return DispatchIndex(dispatches=dispatches, gaps=gaps)


def dispatch_for_check(hall: Any, stage: Any) -> Optional[DispatchRecord]:
    """The first held dispatch one stage reaches, or none - honestly."""
    if stage is None:
        return None
    if not isinstance(stage, str):
        raise ValueError("an stage must be a string naming the stage")
    wanted = stage.strip()
    if not wanted:
        return None
    for dispatch in _hall_book(hall).dispatches:
        if dispatch.stage == wanted:
            return dispatch
    return None


def transition_breaks(hall: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held dispatch: the dispatch
    that took it and the step it took, before,
    then after. A book whose dispatches all walk inside
    the machine tells none.
    """
    book = _hall_book(hall)
    return tuple(
        f"{dispatch_id}: {step}"
        for dispatch_id, steps in _breaks_map(book).items()
        for step in steps)

def dispatch_dispatch(hall: Any,
              hall_id: Any = None) -> Tuple[DispatchRecord, ...]:
    """The held dispatches in their held dispatch, DERIVED at call time.

    Dispatches stand in the dispatch the book holds them -
    the dispatch their halls were summoned - optionally
    for one hall alone. Nothing here is stored:
    the dispatch is the book's own held dispatch, told.
    """
    book = _hall_book(hall)
    dispatches = list(book.dispatches)
    if hall_id is not None:
        wanted = _clean_text(hall_id, "a hall id")
        dispatches = [r for r in dispatches if r.hall_id == wanted]
    return tuple(dispatches)

def trace_of(hall: Any, dispatch_id: Any) -> str:
    """One dispatch's trace, DERIVED at call time.

    The dispatch's walked stages approved as one trace
    line, in walk dispatch. A dispatch that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is summoned
    elsewhere.
    """
    dispatch = _hall_book(hall).dispatch_for(dispatch_id)
    return " > ".join(dispatch.stages)

def trace_for_dispatch(hall: Any,
                  dispatch_id: Any) -> Optional[TraceRecord]:
    """The held trace for one dispatch, or none - honestly."""
    wanted = _clean_text(dispatch_id, "a dispatch id")
    for record in _hall_book(hall).traces:
        if record.dispatch_id == wanted:
            return record
    return None

def trace_current(hall: Any, dispatch_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_dispatch(hall, dispatch_id)
    if trace is None:
        return False
    return trace.trace == trace_of(hall, dispatch_id)

def note_for_dispatch(hall: Any, dispatch_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one dispatch (and stance, when summoned)."""
    wanted = _clean_text(dispatch_id, "a dispatch id")
    for record in _hall_book(hall).notes:
        if record.dispatch_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(hall: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the hall targets, or none."""
    notes = _hall_book(hall).notes
    return notes[0] if notes else None


def ledger_record(hall: Any = None) -> Dict[str, Any]:
    """The dispatch ledger, DERIVED here from the held dispatches alone.

    The ledger counts the held dispatches by their
    derived completeness - green and red - names
    the current dispatch, the first that does not yet
    stand complete, tells each held dispatch's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held dispatches took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _hall_book(hall)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.dispatches
            if ("complete" if dispatch_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "dispatch_records": number})
    current = current_dispatch(book)
    traces = []
    for dispatch in book.dispatches:
        trace = trace_for_dispatch(book, dispatch.dispatch_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, dispatch.dispatch_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"dispatch_id": dispatch.dispatch_id, "trace": standing})
    return {
        "type": "dispatch_well",
        "repo": DISPATCH_SLICE,
        "standings": standings,
        "total": len(book.dispatches),
        "current_dispatch": current.dispatch_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This hall's own roadmap standing, proved from the roadmap itself.

    The record loads this hall's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 halls in 11 parts,
    the summoned prefix, the next hall where the
    dispatch dispatches, and M-243's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(DISPATCH_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "dispatch_roadmap",
        "repo": DISPATCH_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m243_title": own.title,
        "m243_part": own.part,
        "m243_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: halls, dispatches, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or dispatch ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class DispatchBook:
    title: str
    halls: Tuple[HallRef, ...] = ()
    dispatches: Tuple[DispatchRecord, ...] = ()
    views: Tuple[DispatchView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[DispatchPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        halls = tuple(_check_hall_ref(g) for g in self.halls)
        dispatches = tuple(_check_reach_ref(g) for g in self.dispatches)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        traces = tuple(_check_trace_ref(a) for a in self.traces)
        panels = tuple(_check_panel_ref(pn) for pn in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for ref in halls:
            if ref.hall_id in seen_ids:
                raise ValueError(
                    f"two hall references stand under id {ref.hall_id!r}")
            if ref.seq in seen_seqs:
                raise ValueError(
                    f"two hall references stand at sequence {ref.seq}")
            seen_ids.add(ref.hall_id)
            seen_seqs.add(ref.seq)
        dispatch_ids = set()
        dispatch_seqs = set()
        for dispatch in dispatches:
            if dispatch.dispatch_id in dispatch_ids:
                raise ValueError(
                    f"two dispatches stand under id {dispatch.dispatch_id!r}")
            if dispatch.seq in dispatch_seqs:
                raise ValueError(
                    f"two dispatches stand at sequence {dispatch.seq}")
            dispatch_ids.add(dispatch.dispatch_id)
            dispatch_seqs.add(dispatch.seq)
        by_slice = {ref.hall_id: ref for ref in halls}
        for dispatch in (dispatches if halls else ()):

            ref = by_slice.get(dispatch.hall_id)
            if ref is None:
                raise ValueError(
                    f"dispatch {dispatch.dispatch_id!r} is held from hall "
                    f"{dispatch.hall_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "live":
                raise ValueError(
                    f"dispatch {dispatch.dispatch_id!r} is held from hall "
                    f"{dispatch.hall_id!r}, which is not active: "
                    f"no hall is held from an queued hall")
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
            target = (record.dispatch_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for dispatch "
                    f"{record.dispatch_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per dispatch target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_dispatches = set()
        dispatch_ids = {dispatch.dispatch_id for dispatch in dispatches}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.dispatch_id in trace_dispatches:
                raise ValueError(
                    f"two traces stand for dispatch "
                    f"{record.dispatch_id!r}: one trace stands "
                    f"per dispatch walk")
            if dispatches and record.dispatch_id not in dispatch_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces dispatch "
                    f"{record.dispatch_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_dispatches.add(record.dispatch_id)
        object.__setattr__(
            self, "halls", tuple(sorted(halls, key=lambda g: g.seq)))
        object.__setattr__(
            self, "dispatch_records", tuple(sorted(dispatches, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.dispatches + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.dispatch_id for g in self.dispatches) + tuple(
            v.view_id for v in self.views)

    def dispatch_ids(self) -> Tuple[str, ...]:
        return tuple(g.dispatch_id for g in self.dispatches)

    def hall_ids(self) -> Tuple[str, ...]:
        return tuple(g.hall_id for g in self.halls)

    def dispatch_for(self, dispatch_id: Any) -> DispatchRecord:
        wanted = _clean_text(dispatch_id, "a dispatch id")
        for dispatch in self.dispatches:
            if dispatch.dispatch_id == wanted:
                return dispatch
        raise KeyError(f"no dispatch summoned {wanted!r} stands in this book")

    def slice_for(self, hall_id: Any) -> HallRef:
        wanted = _clean_text(hall_id, "an hall id")
        for ref in self.halls:
            if ref.hall_id == wanted:
                return ref
        raise KeyError(f"no hall summoned {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> DispatchView:
        wanted = _clean_text(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view summoned {wanted!r} stands in this book")

    def note_for(self, note_id: Any) -> NoteRecord:
        wanted = _clean_text(note_id, "a stance id")
        for record in self.notes:
            if record.note_id == wanted:
                return record
        raise KeyError(f"no stance summoned {wanted!r} stands in this book")

    def trace_for(self, trace_id: Any) -> TraceRecord:
        wanted = _clean_text(trace_id, "an trace id")
        for record in self.traces:
            if record.trace_id == wanted:
                return record
        raise KeyError(f"no trace summoned {wanted!r} stands in this book")

    def item_for(self, item_id: Any) -> Any:
        wanted = _clean_text(item_id, "an item id")
        for dispatch in self.dispatches:
            if dispatch.dispatch_id == wanted:
                return dispatch
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item summoned {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "halls": [g.to_record() for g in self.halls],
            "dispatch_records": [g.to_record() for g in self.dispatches],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: DispatchBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: DispatchBook) -> None:
    if book.title != "Samtal bridge at the M-243 slice run":
        raise ValueError("the shipped example book carries another title")
    if len(book.halls) != 3 or len(book.dispatches) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three hall references, five dispatches and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-samtal":
        raise ValueError("the pinned panel is panel-samtal")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.stage for e in index.dispatches] != ["held", "held", "held"]:
        raise ValueError("the shipped example book index must derive the three held complete dispatches in held dispatch")
    if index.gaps != ("dispatch-bare-dispatch", "dispatch-leaping-dispatch"):
        raise ValueError("the shipped example book must leave the bare and leaping dispatches honestly open, summoned in its gaps")
    summoned = dispatch_for_check(book, EXAMPLE_STAGE)
    if summoned is None or summoned.dispatch_id != "dispatch-held-dispatch":
        raise ValueError("the shipped example book must reach its opening dispatch under the example stage")
    if trace_of(book, "dispatch-held-dispatch") != "summoned > heard > answered > approved > held":
        raise ValueError("the shipped example book must derive the opening dispatch's trace from its walked steps")
    if not trace_current(book, "dispatch-held-dispatch"):
        raise ValueError("the shipped example book must hold the opening dispatch's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note dispatch")

def validate_book(data: Any, *, require_example: bool = False) -> DispatchBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, DispatchBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a dispatch book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live hall build or execution "
                f"({key!r} is summoned on it): {DISPATCH_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its dispatches under a view")
    if "dispatch_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held dispatches at call time")
    if "ledger" in data or "current_dispatch" in data:
        raise ValueError(
            "a book stores no ledger and no current dispatch: both are "
            "derived from its held dispatches at call time")
    if "trace" in data or "dispatch" in data:
        raise ValueError(
            "a book stores no trace and no dispatch: both are derived "
            "from its held dispatches at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != DISPATCH_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{DISPATCH_SCHEMA!r}")
    if data.get("repo") is not None and (
            data["repo"] != DISPATCH_SLICE):
        raise ValueError(
            f"a book's hall must be {DISPATCH_SLICE!r}")
    head = data.get("dispatch_head") or data.get("samtal_bridge") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's dispatch head must be a mapping")
    title = head.get("title") or data.get("title")
    halls = tuple(build_hall_ref(g) for g in data.get("halls") or ())
    dispatches = tuple(build_dispatch(g) for g in data.get("dispatch_records") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = DispatchBook(
        title=title, halls=halls, dispatches=dispatches, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = DispatchBook(
        title=book.title, halls=book.halls, dispatches=book.dispatches,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> DispatchBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (DispatchBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an DispatchBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> DispatchBook:
    return validate_book(data, require_example=require_example)


def load_dispatch(
        data: Optional[Dict[str, Any]] = None) -> DispatchBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(DISPATCH_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_dispatch_file(path: Any) -> DispatchBook:
    """Load one dispatch file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: hall references, dispatches and views held one by one.
# ---------------------------------------------------------------------

class DispatchRegistry:
    """An in-memory holding of hall references, dispatches and views.

    The registry is the pure layer's model of a
    session's dispatch book: hall references are
    held under their ids, dispatches are held under
    their ids, one dispatch per id and per sequence,
    and views are held in heard dispatch, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[HallRef] = []
        self._dispatches: List[DispatchRecord] = []
        self._views: List[DispatchView] = []
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

    def register_hall_ref(self, item: Any) -> HallRef:
        """Hold one hall reference, answered whole before held."""
        approved = _check_hall_ref(item)
        return self._register(
            self._slices, approved, "hall_id", "hall reference")

    def register_dispatch(self, item: Any) -> DispatchRecord:
        """Hold one dispatch, answered whole before held."""
        approved = _check_reach_ref(item)
        return self._register(
            self._dispatches, approved, "dispatch_id", "dispatch")

    def register_view(self, view: Any) -> DispatchView:
        """Hold one view; a view naming no id takes a fresh one."""
        approved = _check_view_ref(view)
        if not approved.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            approved = build_view({**approved.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, approved, "view_id", "view")

    def register_book(self, book: Any) -> DispatchBook:
        """Hold a whole book's records, under its title."""
        approved = build_book(book)
        if self._title is not None and approved.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {approved.title!r}")
        for ref in approved.halls:
            self.register_hall_ref(ref)
        for dispatch in approved.dispatches:
            self.register_dispatch(dispatch)
        for view in approved.views:
            self.register_view(view)
        self._title = approved.title
        return self.book()

    def book(self) -> DispatchBook:
        return DispatchBook(
            title=self._title or "An unheld dispatch book",
            halls=tuple(self._slices), dispatches=tuple(self._dispatches),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[HallRef, ...]:
        return tuple(self._slices)

    def list_dispatches(self) -> Tuple[DispatchRecord, ...]:
        return tuple(self._dispatches)

    def list_views(self) -> Tuple[DispatchView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._dispatches) + tuple(self._views)

    def get_slice(self, hall_id: Any) -> HallRef:
        return self.book().slice_for(hall_id)

    def get_dispatch(self, dispatch_id: Any) -> DispatchRecord:
        return self.book().dispatch_for(dispatch_id)

    def get_view(self, view_id: Any) -> DispatchView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the ledger target.
# ---------------------------------------------------------------------

def _hall_book(hall: Any) -> DispatchBook:
    if hall is None:
        return load_dispatch()
    if isinstance(hall, DispatchBook):
        return hall
    if isinstance(hall, DispatchRegistry):
        return hall.book()
    return build_book(hall)


def _heldance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _HELDANCE}


def dispatch_record(dispatch: Any, hall: Any = None) -> Dict[str, Any]:
    approved = _check_reach_ref(dispatch)
    book = _hall_book(hall) if hall is not None else None
    record = {
        "type": "dispatch_dispatch",
        "repo": DISPATCH_SLICE,
        "dispatch_id": approved.dispatch_id,
        "hall_id": approved.hall_id,
        "title": approved.title,
        "segment": segment_of(approved, book),
        "complete": dispatch_green(approved, book),
        "gaps": list(dispatch_gaps(approved, book)),
    }
    record.update(_heldance_record(approved))
    return record


def hall_record(ref: Any) -> Dict[str, Any]:
    approved = _check_hall_ref(ref)
    record = {
        "type": "dispatch_run",
        "repo": DISPATCH_SLICE,
        "hall_id": approved.hall_id,
        "title": approved.title,
        "state": approved.state, "reach": approved.reach,
    }
    record.update(_heldance_record(approved))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    approved = _check_trace_ref(record_in)
    record = {
        "type": "dispatch_trace",
        "repo": DISPATCH_SLICE,
        "trace_id": approved.trace_id,
        "dispatch_id": approved.dispatch_id,
        "trace": approved.trace,
    }
    record.update(_heldance_record(approved))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    approved = _check_view_ref(view)
    record = {
        "type": "dispatch_view",
        "repo": DISPATCH_SLICE,
        "view_id": approved.view_id, "seq": approved.seq,
        "view_filter": approved.view_filter,
    }
    record.update(_heldance_record(approved))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    approved = _check_note_ref(record_in)
    record = {
        "type": "dispatch_note",
        "repo": DISPATCH_SLICE,
        "note_id": approved.note_id,
        "dispatch_id": approved.dispatch_id,
        "stance": approved.stance,
    }
    record.update(_heldance_record(approved))
    return record


def panel_record(panel: Any, hall: Any = None) -> Dict[str, Any]:
    approved = validate_panel(panel, hall)
    record = {"type": "dispatch_panel",
              "repo": DISPATCH_SLICE}
    record.update(approved.to_record())
    return record


def verdict_record(verdict: Any, hall: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, DispatchVerdict):
        approved = validate_verdict(verdict, hall)
    else:
        approved = derive_verdict(_hall_book(verdict), view)
    record = {"type": "dispatch_verdict",
              "repo": DISPATCH_SLICE}
    record.update(approved.to_record())
    return record


def index_record(hall: Any) -> Dict[str, Any]:
    if isinstance(hall, DispatchIndex):
        index = hall
    else:
        index = derive_index(hall)
    record = {"type": "dispatch_index",
              "repo": DISPATCH_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    approved = _hall_book(book)
    record = {"type": "dispatch_book",
              "repo": DISPATCH_SLICE,
              "title": approved.title}
    record.update(approved.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(dispatch: Any, hall: Any = None) -> str:
    approved = _check_reach_ref(dispatch)
    return (
        f"{approved.title} - from {approved.hall_id}: "
        f"stage {approved.stage if approved.stage else 'none'}, "
        f"claims "
        f"{', '.join(approved.claims) if approved.claims else 'none'}. "
        f"{approved.detail}")


def panel_plain_words(hall: Any, view: Any = None) -> str:
    panel = derive_panel(hall, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(hall: Any, view: Any = None) -> str:
    verdict = derive_verdict(hall, view)
    return (
        f"The dispatches stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"dispatches stand complete.")


def view_plain_words(view: Any) -> str:
    approved = _check_view_ref(view)
    return f"View {approved.view_id}: shows {approved.view_filter} dispatches."


def note_plain_words(record_in: Any) -> str:
    approved = _check_note_ref(record_in)
    return (
        f"Note {approved.note_id}: {approved.stance} "
        f"{approved.dispatch_id}, toward {approved.target}. "
        f"{approved.detail}")


def index_plain_words(hall: Any) -> str:
    index = (hall if isinstance(hall, DispatchIndex)
             else derive_index(hall))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.dispatches)} green dispatches; "
        f"red, summoned in its gaps: {gaps}.")

def format_dispatch(dispatch: Any, hall: Any = None) -> str:
    approved = _check_reach_ref(dispatch)
    book = _hall_book(hall) if hall is not None else None
    lines = [f"{approved.title} ({approved.dispatch_id})"]
    lines.extend(plain_lines(approved))
    lines.append(approved.detail)
    if dispatch_green(approved, book):
        lines.append(
            "This dispatch stands complete - it walked the question "
            "sequence in the open from summoned to held, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This dispatch stands open - it stands summoned in "
            f"its gaps: {', '.join(dispatch_gaps(approved, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    approved = _check_view_ref(view)
    return (
        f"View {approved.view_id}: filter {approved.view_filter} - "
        f"{approved.detail}")


def format_note(record_in: Any) -> str:
    approved = _check_note_ref(record_in)
    lines = [
        f"Dispatch note {approved.stance} {approved.dispatch_id} "
        f"({approved.note_id}): {approved.title}. {approved.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or dispatch it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_stage(hall: Any, stage: Any) -> str:
    dispatch = dispatch_for_check(hall, stage)
    if dispatch is not None:
        return format_dispatch(dispatch, hall)
    wanted = stage.strip() if isinstance(stage, str) else stage
    return (
        f"No held dispatch stands under stage {wanted!r} yet - the "
        f"stage reaches nothing in this book, and no dispatch is "
        f"invented for it.")


def format_book(hall: Any = None, hall_id: Any = None) -> str:
    book = _hall_book(hall)
    dispatches = (dispatches_for_hall(book, hall_id)
              if hall_id is not None else book.dispatches)
    lines = [f"The Samtal Bridge (M-243) - {book.title}"]
    lines.extend(segment_of(dispatch, book) for dispatch in dispatches)
    return "\n".join(lines)


def format_panel(hall: Any = None, view: Any = None) -> str:
    panel = derive_panel(hall, view)
    lines = [f"Dispatch panel under view {panel.view_id}:"]
    lines.extend(row.segment for row in panel.rows)
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(hall: Any = None, view: Any = None) -> str:
    verdict = derive_verdict(hall, view)
    return verdict_plain_words(hall, view) + (
        f" (view {verdict.view_id}, as of {verdict.latest_on})")


def format_index(hall: Any = None) -> str:
    book = _hall_book(hall)
    index = derive_index(book)
    lines = ["Dispatch index, derived from the held dispatches:"]
    for dispatch in index.dispatches:
        lines.append(f"{dispatch.stage} - {dispatch.title} ({dispatch.dispatch_id})")
    if index.gaps:
        lines.append(
            "Red, summoned honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_dispatch_screen(hall: Any = None) -> str:
    book = _hall_book(hall)
    lines = [
        "The Samtal Bridge (M-243)",
        f"{book.title}: {len(book.dispatches)} dispatches held, "
        f"{len(green_dispatches(book))} dispatches standing green, "
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


def parse_dispatch_args(args: Any) -> Tuple[str, Any]:
    """Parse the /dispatch grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("dispatch", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("stage", "hall"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
