"""Cross-app method (roadmap slice M-244).

Part X - Bridges. The roadmap
words: **every bridge's credential resolves through Kista; a bridge without a key asks once.******

What already ships, and what this bridge adds:

* Mythic's bridge faces already ship (M-233 consuming, M-234 serving, M-235 the registry, M-236 the skills standard, M-237 the custom commands, M-238 the installable bundles, M-239 the VS Code family companions book, M-240 the generic companions book, M-241 the rival importers book, M-242 the Samverk bridge book, M-243 the Samtal bridge book, ``mythic_agent/core/samtal_bridge.py`` the nearest kin) and the seams this slice answers already stand in the tree: the key-custody book (``mythic_agent/core/key_custody.py``, M-032) already resolves a Kista reference for every provider door, holds config files to references and never secrets, and names the one kind ask a missing key gets, and each bridge book before this one (M-242 the Samverk bridge book, M-243 the Samtal bridge book) already refuses a credential named in its records by name and names Kista as its custody road - this slice is that custody road's own bridge book: every bridge's credential resolves through Kista, and a bridge without a key asks once, each bridge's credential resolution held as data under one resolution record, the bridge, key, vault, grant and scope declared BEFORE any standing is granted, the resolution a local record - Kista's own road provides the surfaces as data here - with no credential resolved live, no key read and no key asked for live. The bridge book WIRES that key-keeper face as data, in its own module, standing in the M-195 copy-and-share
  book book the M-244 book stands in: one tracker
  per book, and the tracker's charge over one
  resolution across its bridge held as a book - a
  resolution. The shipped resolutions stand untouched behind
  their seams: this layer holds resolutions as data
  over the book's bridges and rewrites none of them,
  and the resolutions book keeps its own standing.
  Resolutions stand on the ledger AS DATA alone: a
  resolution carries a ledger ref, a reference held in
  this book; holding, viewing or telling a resolution
  bridges no resolution live, moves no keeper and files
  nothing.
* No charter row names this bridge: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-244 on no row, and the
  bridge tests pin that absence live. The M-005
  method charter names no bridge row either: its
  own words name the whole of Part IX (M-201
  to M-232) as the part that executes the
  charter; Part X stands on the roadmap's own
  words, and this slice is built to those words.

* A resolution is held whole: the bridge it
  answers for, named by its bridge id; its title;
  the resolution steps it walked, held as data in
  walk resolution; and the evidence it carries, held
  as data by bridge. The resolution walk is EXPLICIT:
  its sequence stands as data
  (:data:`STAGES`, :data:`TRANSITIONS`) -
  named, sought, resolved, confirmed, held -
  and a resolution's standing is DERIVED at
  call time from its held steps and evidence
  alone: a resolution that opens anywhere but
  named, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet named held stands
  open, named in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - bridge_ref,
  key_ref, vault_ref, grant_ref, custody_ref, evidence
  a tracker can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A resolution is
  confirmed from held evidence alone, never
  from a feeling: a resolution holding a
  bare claim stands open, named in its gaps.
* A resolution stands only for an ACTIVE
  bridge. The book holds each bridge it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  resolution naming a bridge that stands
  nowhere in the book refuses BY NAME, and a
  resolution for a bridge that is not active
  refuses BY NAME beside it: the tracker deals with
  the bridge in hand, in roadmap resolution, never a
  queued one, and a bridge whose resolution already
  stands complete is never resolved twice - the
  current resolution is derived, so a
  completed bridge is never the current resolution
  twice.
* The resolution's trace is visible. A trace
  record holds one resolution's walked steps
  as one trace line, exactly as walked, beside
  the resolution. The derived trace is
  computed at call time from the resolution's
  held steps; a held trace that no longer agrees
  with it stands stale, named in the ledger - the
  trace is the walk itself, never a retelling
  of it.
* The resolution index is DERIVED at call
  time from the held resolutions - one resolution
  per complete resolution, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, resolution or current-resolution
  claim on any record refuses by name.
* The current resolution is DERIVED at call
  time - the first held resolution, in held
  resolution, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its resolution, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per resolution stance; holding
  a note posts none of it, the rule stands as
  data (:data:`RESOLUTION_RULE`), and a record
  claiming a resolution was actually held,
  captured or promoted live refuses BY NAME.
  The tracker resolutions - and those resolutions, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the book a real resolution
  file takes, a loader reads a file anywhere on
  disk, resolutions and views are sought as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a resolution book for a session and
  telling from it. This layer reaches no live
  resolution: it writes no resolution live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no tracker, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds resolutions
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The resolution walk is explicit.** A
  resolution is confirmed against the held
  steps and legal steps alone; an illegal step
  stands named in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  resolution that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, named in its gaps:
  a resolution is confirmed from evidence, not
  vibes.
* **Active bridges only, in roadmap resolution.** A
  resolution for a missing or queued bridge
  refuses by name; no resolution is invented
  for a bridge the tracker has not sought with.
* **Unknown stays unknown.** A resolution
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, resolution
  and current resolution are derived, never
  stored.** Each is derived from the held
  resolutions at call time; a stored one
  refuses by name, so it can never drift.
* **One resolution per resolution.** Two
  resolutions standing for one resolution id
  refuse by name, and one note record stands per
  resolution stance.
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
    "RESOLUTION_RESOURCE",
    "RESOLUTION_SCHEMA",
    "RESOLUTION_SLICE",
    "RESOLUTION_RULE",
    "PLAIN_EXPLANATION",
    "THE_RESOLUTION_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "COMPLETE_WORDS",
    "BRIDGE_STATES",
    "CUSTODIES",
    "Any",
    "Dict",
    "List",
    "Optional",
    "TraceRecord",
    "ResolutionRecord",
    "IndexResolution",
    "BridgeRef",
    "NoteRecord",
    "ResolutionBook",
    "ResolutionIndex",
    "ResolutionPanel",
    "ResolutionPanelRow",
    "ResolutionRegistry",
    "ResolutionVerdict",
    "ResolutionView",
    "TargetCount",
    "trace_for_resolution",
    "trace_record",
    "ledger_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_resolution",
    "build_bridge_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_resolution",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "resolution_for_check",
    "resolution_resolution",
    "resolution_record",
    "first_note",
    "format_book",
    "format_resolution",
    "format_index",
    "format_note",
    "format_stage",
    "format_panel",
    "format_resolution_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "bridge_record",
    "load_resolution",
    "load_resolution_file",
    "normalize_bridge_state",
    "normalize_custody",
    "normalize_stage",
    "normalize_claim_kind",
    "legal_step",
    "next_stage",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_resolution",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_resolution_args",
    "green_resolutions",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_resolutions",
    "validate_trace",
    "validate_book",
    "validate_resolution",
    "validate_bridge_ref",
    "validate_note",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
    "resolution_gaps",
    "resolution_green",
    "resolutions_for_bridge",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

RESOLUTION_SCHEMA = "mythic.kista_keykeeper/1"
RESOLUTION_SLICE = "M-244"
THE_RESOLUTION_SLICE = RESOLUTION_SLICE
RESOLUTION_RESOURCE = "kista_keykeeper.yaml"
INDEX_ACTION = "index"
EXAMPLE_STAGE = "held"
STAGE_FIELDS = ("stages", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("held", "held", "blocked")
BRIDGE_STATES = ("live", "dormant")
CUSTODIES = ("kista", "environment", "missing")
RESOLUTION_RULE = "resolutions are held as data alone: every bridge's credential resolves through Kista, and a bridge without a key asks once (the custodies kista, environment and missing, one custody held per bridge as data) - one resolution shelf per book, and the shelf charge over one resolution held as a resolution - a resolution stands as data, held by reference (a bridge ref), never resolved live - the resolution walk stands as an explicit resolution sequence - named, sought, resolved, confirmed, held - and a resolution completes only complete, complete being a state with evidence held - bridge ref, key ref, vault ref, grant ref, scope ref, custody ref - never a feeling, a memory, an assertion or a summary; a key value itself is never held here - only its Kista reference is held, the secret lands nowhere, its custody road being Kista (M-032) - and a resolution confirmed without resolving, or held before it is confirmed, stands open, named in its gaps; a resolution on a missing-key bridge stands complete only with its custody held as a custody_ref, its one ask held as data; defining, reading, listing and telling a resolution resolves no credential live, reads no key, asks for no key and writes nothing outside held records"
PLAIN_EXPLANATION = "Kista key-keeper (M-244): every bridge's credential resolves through Kista; a bridge without a key asks once."
USAGE = 'Usage: /kistakeykeeper | /kistakeykeeper resolution <resolution-id> | /kistakeykeeper stage <stage> | /kistakeykeeper bridge <bridge-id> | /kistakeykeeper view <view-id> | /kistakeykeeper note <note-id> | /kistakeykeeper index | /kistakeykeeper panel | /kistakeykeeper verdict'

STAGES = ("named", "sought", "resolved", "confirmed", "held")
HELD_EVIDENCE = ("bridge_ref", "key_ref", "vault_ref", "grant_ref", "scope_ref", "custody_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "named": ("sought",),
    "sought": ("resolved",),
    "resolved": ("confirmed",),
    "confirmed": ("named", "held"),
    "held": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a resolution or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a resolution stands complete.
    A stage outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_stage(stage: Any, failed: Any = False) -> Optional[str]:
    """The step the tracker takes next, DERIVED from the sequence.

    Banked leads to sought and sought to
    resolved; resolved leads to confirmed; at
    confirmed a follow-up banking steps back to named and a finished resolution steps to held;
    held is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    confirmed = normalize_stage(stage)
    if confirmed == "named":
        return "sought"
    if confirmed == "sought":
        return "resolved"
    if confirmed == "resolved":
        return "confirmed"
    if confirmed == "confirmed":
        return "named" if failed else "held"
    return None


_HELDANCE = ("recorded_on", "actor", "repo", "origin_session")
_RUN_KEYS = frozenset({
    "resolution_id", "seq", "bridge_id", "title", "stages",
    "claims", "detail",
} | set(_HELDANCE))
_SLICE_REF_KEYS = frozenset({
    "bridge_id", "seq", "title", "state", "custody", "detail",
} | set(_HELDANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "resolution_id", "trace", "detail",
} | set(_HELDANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_HELDANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "resolution_id", "stance", "target", "title",
    "detail",
} | set(_HELDANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "resolutions", "coverage", "covered", "uncovered",
    "current_resolution", "next_resolution", "progress", "ledger",
    "current", "resolution", "breaks", "live"})
_LIVE_KEYS = (
    "live_resolution", "resolutions_live", "live_question",
    "resolutions_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "resolutions_live",
    "resumed_live", "runs_resolution", "paused_live",
    "runs_resolution", "ran_resolution", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "resolution_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_resolution", "sent_resolution",
    "posts_note", "held_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_resolution", "filed_live", "spawns_tracker", "spawned_tracker", "sends_resolution", "sent_resolution", "writes_resolution", "wrote_resolution")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_stages(value: Any) -> Tuple[str, ...]:
    """A resolution's walked stages, held as data.

    The stages stand as a list of stage names in
    walk resolution, each one a stage of the explicit
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
    """A resolution's asked claims: claim bridges named as data.

    Each claim names one bridge from the held
    vocabulary - the human bridges the gate may ask
    and the code bridges it must never ask, both
    held honestly as data - and a bridge outside
    the vocabulary refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("claims must be a list of claim bridges")
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
            out[key] = _clean_text(mapping.get(key), "a recorded_on bridge")
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
                f"{what} claims a live gate resolution or bridge build "
                f"execution ({key!r} is named on it): "
                f"{RESOLUTION_RULE}")
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


def normalize_bridge_state(value: Any) -> str:
    state = _clean_text(value, "an bridge state").lower()
    if state not in BRIDGE_STATES:
        raise ValueError(
            f"bridge state {state!r} is not one of the held "
            f"states: " + ", ".join(BRIDGE_STATES))
    return state


def normalize_custody(value: Any) -> str:
    custody = _clean_text(value, "a custody").lower()
    if custody not in CUSTODIES:
        raise ValueError(
            f"custody {custody!r} is not one of the "
            f"bridge resolution custodys: " + ", ".join(CUSTODIES))
    return custody


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
    bridge = _clean_text(value, "a claim bridge").lower()
    if bridge not in CLAIM_KINDS:
        raise ValueError(
            f"claim bridge {bridge!r} is not one of the held "
            f"bridges: " + ", ".join(CLAIM_KINDS))
    return bridge

# ---------------------------------------------------------------------
# The held resolution: one bridge cut from an active bridge.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ResolutionRecord:
    """One resolution bridge, held as data.

    The resolution names the active bridge it was
    held from, by bridge id, its title, its
    verifiable stages, held as data, and its
    claims, named by resolution id. The grain is
    derived, never stored: exactly one verifiable
    walk is resolved against the machine. A resolution whose
    stages are not yet held stands with its
    stages empty: it stands open, named in
    its gaps, and no stage is invented for it.
    The resolution is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    resolution_id: str
    seq: int
    bridge_id: str
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
            self, "resolution_id", _clean_text(self.resolution_id, "a resolution id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "bridge_id", _clean_text(self.bridge_id, "an bridge id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a resolution title"))
        object.__setattr__(
            self, "stages", _check_stages(self.stages))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a resolution detail"))
        for key in _HELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.resolution_id

    @property
    def stage(self) -> str:
        """The stage the resolution stands at: its last walked stage."""
        return self.stages[-1] if self.stages else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "resolution_id": self.resolution_id, "seq": self.seq,
            "bridge_id": self.bridge_id, "title": self.title,
            "stages": list(self.stages),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _HELDANCE:
            record[key] = getattr(self, key)
        return record


def _check_custody_ref(value: Any) -> ResolutionRecord:
    if not isinstance(value, ResolutionRecord):
        raise ValueError("a resolution must be a ResolutionRecord")
    return value


def validate_resolution(resolution: Any) -> ResolutionRecord:
    return _check_custody_ref(resolution)


def build_resolution(record: Any = None, **kwargs: Any) -> ResolutionRecord:
    """Build one held resolution from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, ResolutionRecord):
        if kwargs:
            raise ValueError("a resolution stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a resolution must be a mapping or a ResolutionRecord")
    _needed(data, _RUN_KEYS, "a resolution")
    return ResolutionRecord(
        resolution_id=data.get("resolution_id"), seq=data.get("seq"),
        bridge_id=data.get("bridge_id"), title=data.get("title"),
        stages=data.get("stages"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_heldance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each resolution to the steps it took outside the machine.

    Derived from the held resolutions alone: a break is
    one consecutive pair of walked stages the
    explicit gate sequence does not allow, told
    in walk resolution as before, then after.
    """
    named: Dict[str, Tuple[str, ...]] = {}
    for resolution in book.resolutions:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(resolution.stages, resolution.stages[1:])
            if not legal_step(before, after))
        if breaks:
            named[resolution.resolution_id] = breaks
    return named

def resolution_gaps(resolution: Any, bridge: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a resolution from standing complete.

    Guarded from the resolution's own held fields alone -
    its walked steps against the explicit question
    sequence, and its held evidence against the
    held vocabulary: the resolution opens at
    named, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a resolution stands complete only when it has
    named held. The bridge names nothing
    further: no gap is borrowed from another
    resolution.
    """
    confirmed = _check_custody_ref(resolution)
    gaps: List[str] = []
    if not confirmed.stages:
        gaps.append(
            "has passed through no step: the resolution has not started")
        return tuple(gaps)
    if confirmed.stages[0] != "named":
        gaps.append(
            f"opens at {confirmed.stages[0]}, not at named: "
            f"the resolution opens with the reflection")
    for before, after in zip(confirmed.stages, confirmed.stages[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"resolution sequence does not allow")
    for bridge in confirmed.claims:
        if bridge in BARE_CLAIMS:
            gaps.append(
                f"carries a {bridge} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if bridge is not None:
        try:
            _ref = _bridge_book(bridge).slice_for(confirmed.bridge_id)
        except Exception:
            _ref = None
        if _ref is not None and _ref.custody == "missing" and \
                "custody_ref" not in confirmed.claims:
            gaps.append(
                "stands confirmed on an missing bridge with no "
                "custody_ref held: the custody for the "
                "bridge is missing")
    if confirmed.stages[-1] != "held":
        gaps.append(
            f"has not reached held: the resolution stands "
            f"at {confirmed.stages[-1]}")
    return tuple(gaps)

def resolution_green(resolution: Any, bridge: Any = None) -> bool:
    return not resolution_gaps(resolution, bridge)


def plain_lines(resolution: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the resolution's own fields."""
    confirmed = _check_custody_ref(resolution)
    return (
        f"Resolution: {confirmed.title}",
        f"Bridge: {confirmed.bridge_id}",
        f"Stage: {confirmed.stage if confirmed.stage else 'none'}",
        f"Claims: "
        f"{', '.join(confirmed.claims) if confirmed.claims else 'none'}",
    )


def segment_of(resolution: Any, bridge: Any = None) -> str:
    confirmed = _check_custody_ref(resolution)
    gaps = resolution_gaps(confirmed, bridge)
    return (
        f"{confirmed.resolution_id}: {confirmed.title} - bridge: "
        f"'{confirmed.bridge_id}' - stage: "
        f"'{confirmed.stage if confirmed.stage else 'none'}' - "
        f"stages: {len(confirmed.stages)} - claims: "
        f"'{', '.join(confirmed.claims) if confirmed.claims else 'none'}' - "
        f"detail: '{confirmed.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held bridge reference: the active bridge a book resolutions from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class BridgeRef:
    """One bridge a resolution book resolutions from, held as a reference.

    The record names the bridge, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 bridge book's own telling. A resolution
    stands only from an active reference: the
    book refuses a resolution naming no held reference,
    and a resolution from an queued one, BY NAME.
    """

    bridge_id: str
    seq: int
    title: str
    state: str
    custody: str = "kista"
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    repo: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "bridge_id", _clean_text(self.bridge_id, "an bridge id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(
            self, "state", normalize_bridge_state(self.state))
        object.__setattr__(
            self, "custody", normalize_custody(self.custody))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an bridge detail"))
        for key in _HELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.bridge_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "bridge_id": self.bridge_id, "seq": self.seq,
            "title": self.title, "state": self.state,
            "custody": self.custody,
            "detail": self.detail,
        }
        for key in _HELDANCE:
            record[key] = getattr(self, key)
        return record


def _check_bridge_ref(value: Any) -> BridgeRef:
    if not isinstance(value, BridgeRef):
        raise ValueError("a bridge reference must be an BridgeRef")
    return value


def validate_bridge_ref(ref: Any) -> BridgeRef:
    return _check_bridge_ref(ref)


def build_bridge_ref(record: Any = None, **kwargs: Any) -> BridgeRef:
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, BridgeRef):
        if kwargs:
            raise ValueError(
                "a bridge reference stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError(
            "a bridge reference must be a mapping or an BridgeRef")
    _needed(data, _SLICE_REF_KEYS, "a bridge reference")
    return BridgeRef(
        bridge_id=data.get("bridge_id"), seq=data.get("seq"),
        title=data.get("title"), state=data.get("state"), custody=data.get("custody") or "kista",
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held trace trace: the human approves the trace, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TraceRecord:
    """One trace trace, held as data.

    The record names its bridge and the trace the
    human active - the bridge's resolution ids in
    derived claim resolution, held exactly as
    active. The trace is of the set and its
    resolution, never of a step: when the derived
    trace moves, this record stands stale, named
    in the ledger, until a new trace is active.
    """

    trace_id: str
    seq: int
    resolution_id: str
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
            self, "resolution_id", _clean_text(self.resolution_id, "an bridge id"))
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
            "resolution_id": self.resolution_id, "trace": self.trace,
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
        resolution_id=data.get("resolution_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a resolution, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One resolution stance, held as data.

    The record names its resolution, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per resolution stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    resolution_id: str
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
            self, "resolution_id", _clean_text(self.resolution_id, "a resolution id"))
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
            "resolution_id": self.resolution_id, "stance": self.stance,
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
        resolution_id=data.get("resolution_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held view: which bridges a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ResolutionView:
    """A view over the book: every resolution, the green, the rest."""

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


def _check_view_ref(value: Any) -> ResolutionView:
    if not isinstance(value, ResolutionView):
        raise ValueError("a view must be an ResolutionView")
    return value


def validate_view(view: Any) -> ResolutionView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> ResolutionView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, ResolutionView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an ResolutionView")
    _needed(data, _VIEW_KEYS, "a view")
    return ResolutionView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ResolutionPanelRow:
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


def _row_for_resolution(resolution: ResolutionRecord,
                     bridge: Any = None) -> ResolutionPanelRow:
    return ResolutionPanelRow(
        item_id=resolution.resolution_id,
        standing="complete" if resolution_green(resolution, bridge) else "open",
        label=resolution.title, segment=segment_of(resolution, bridge),
        recorded_on=resolution.recorded_on)


def _check_row_ref(value: Any) -> ResolutionPanelRow:
    if not isinstance(value, ResolutionPanelRow):
        raise ValueError("a panel row must be an ResolutionPanelRow")
    return value


def validate_row(row: Any, resolution: Any = None,
                 bridge: Any = None) -> ResolutionPanelRow:
    confirmed = _check_row_ref(row)
    if resolution is not None:
        derived = _row_for_resolution(_check_custody_ref(resolution), bridge)
        if confirmed != derived:
            raise ValueError(
                f"panel row {confirmed.item_id!r} does not agree with "
                f"the row derived from its resolution")
    return confirmed


def build_row(row: Any = None, resolution: Any = None,
              bridge: Any = None,
              **kwargs: Any) -> ResolutionPanelRow:
    if resolution is not None:
        derived = _row_for_resolution(_check_custody_ref(resolution), bridge)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            ResolutionPanelRow(**kwargs))
        return validate_row(built, resolution, bridge)
    if isinstance(row, ResolutionPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return ResolutionPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on bridge"))
    if row is None and kwargs:
        return ResolutionPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an ResolutionPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[ResolutionPanelRow, ...]
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
        f"The resolution book holds {total_items} resolutions as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown resolutions "
        f"stand complete.",
        "Rows stand in held resolution, the resolution the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its resolution's own fields "
        "- the bridge it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any resolution.",
        "Completeness is resolved from the held records alone: "
        "a resolution that steps outside the resolution sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not named held stands open, named in its "
        "gaps, and the resolution index is derived from the "
        "held resolutions, never stored where it could drift.",
    )

@dataclass(frozen=True)
class ResolutionPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[ResolutionPanelRow, ...]
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


def _resolve_view(bridge: Any, view: Any) -> ResolutionView:
    book = _bridge_book(bridge)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, ResolutionView):
        return view
    return book.view_for(view)


def shown_resolutions(bridge: Any, view: Any = None
                   ) -> Tuple[ResolutionRecord, ...]:
    book = _bridge_book(bridge)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.resolutions
    if resolved.view_filter == "complete":
        return tuple(g for g in book.resolutions if resolution_green(g, book))
    return tuple(g for g in book.resolutions if not resolution_green(g, book))


def resolutions_for_bridge(bridge: Any, bridge_id: Any
                      ) -> Tuple[ResolutionRecord, ...]:
    wanted = _clean_text(bridge_id, "an bridge id")
    return tuple(
        g for g in _bridge_book(bridge).resolutions if g.bridge_id == wanted)


def green_resolutions(bridge: Any) -> Tuple[ResolutionRecord, ...]:
    book = _bridge_book(bridge)
    return tuple(g for g in book.resolutions if resolution_green(g, book))


def current_resolution(bridge: Any) -> Optional[ResolutionRecord]:
    """The book's current resolution, DERIVED at call time.

    The first held resolution, in held resolution, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held resolutions alone, so it can
    never go stale against them. A book whose every
    resolution stands complete has no current resolution.
    """
    book = _bridge_book(bridge)
    for resolution in book.resolutions:
        if not resolution_green(resolution, book):
            return resolution
    return None


def derive_panel(bridge: Any, view: Any = None) -> ResolutionPanel:
    book = _bridge_book(bridge)
    resolved = _resolve_view(book, view)
    shown = shown_resolutions(book, resolved)
    rows = tuple(_row_for_resolution(resolution, book) for resolution in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.resolutions), default="")
    green = sum(1 for g in shown if resolution_green(g, book))
    return ResolutionPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.resolutions), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.resolutions), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> ResolutionPanel:
    if not isinstance(value, ResolutionPanel):
        raise ValueError("a panel must be an ResolutionPanel")
    return value


def validate_panel(panel: Any, bridge: Any = None) -> ResolutionPanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 resolution).
    """
    confirmed = _check_panel_ref(panel)
    if bridge is not None:
        book = _bridge_book(bridge)
        view = (book.view_for(confirmed.view_id)
                if confirmed.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(confirmed, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {confirmed.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return confirmed


def build_panel(panel: Any = None, bridge: Any = None,
                **kwargs: Any) -> ResolutionPanel:
    if isinstance(panel, ResolutionPanel):
        if kwargs:
            raise ValueError("a panel stands whole or by fields, not both")
        return validate_panel(panel, bridge)
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
        built = ResolutionPanel(
            panel_id=_clean_text(data.get("panel_id"), "a panel id"),
            view_id=data.get("view_id"),
            view_filter=normalize_view_filter(data.get("view_filter")),
            rows=rows,
            total_items=_check_count(
                data.get("total_items"), "a total_items count"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            target_counts=counts,
            as_of=_clean_text(data.get("as_of"), "an as_of bridge"),
            account=_check_lines(data.get("account"), "the account"))
        return validate_panel(built, bridge)
    if panel is None and bridge is not None:
        return derive_panel(bridge, kwargs.get("view"))
    raise ValueError("a panel must be a mapping, an ResolutionPanel, or derived")


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
class ResolutionVerdict:
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


def derive_verdict(bridge: Any, view: Any = None) -> ResolutionVerdict:
    book = _bridge_book(bridge)
    resolved = _resolve_view(book, view)
    shown = shown_resolutions(book, resolved)
    green = sum(1 for g in shown if resolution_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return ResolutionVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> ResolutionVerdict:
    if not isinstance(value, ResolutionVerdict):
        raise ValueError("a verdict must be an ResolutionVerdict")
    return value


def validate_verdict(verdict: Any, bridge: Any = None) -> ResolutionVerdict:
    confirmed = _check_verdict_ref(verdict)
    if confirmed.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {confirmed.verdict!r} is not a held word")
    if bridge is not None:
        book = _bridge_book(bridge)
        view = (book.view_for(confirmed.view_id)
                if confirmed.view_id is not None else None)
        derived = derive_verdict(book, view)
        if confirmed != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return confirmed


def build_verdict(verdict: Any = None, bridge: Any = None,
                  **kwargs: Any) -> ResolutionVerdict:
    if isinstance(verdict, ResolutionVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, bridge)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = ResolutionVerdict(
            verdict=_clean_text(data.get("verdict"), "a verdict"),
            view_id=data.get("view_id"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            green_shown=_check_count(
                data.get("green_shown"), "a green_shown count"),
            latest_on=_clean_text(data.get("latest_on"), "a latest bridge"))
        return validate_verdict(built, bridge)
    if verdict is None and bridge is not None:
        return derive_verdict(bridge, kwargs.get("view"))
    raise ValueError(
        "a verdict must be a mapping, an ResolutionVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held bridges' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexResolution:
    stage: str
    resolution_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "stage": self.stage, "resolution_id": self.resolution_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class ResolutionIndex:
    """The resolution index, derived from the held resolutions.

    The index names one resolution per green resolution, in
    held resolution - the resolution's own one verifiable
    stage, its resolution id and its title - and the
    resolutions that do not stand complete, named in its
    gaps. Nothing here is stored on any resolution: the
    index is derived at call time from the held
    records alone, so it can never drift from them.
    """

    resolutions: Tuple[IndexResolution, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "resolutions": [e.to_record() for e in self.resolutions],
            "gaps": list(self.gaps),
        }


def derive_index(bridge: Any) -> ResolutionIndex:
    """Derive the resolution index from the book's held resolutions."""
    book = _bridge_book(bridge)
    resolutions = tuple(
        IndexResolution(stage=g.stage, resolution_id=g.resolution_id,
                   title=g.title)
        for g in book.resolutions if resolution_green(g, book))
    gaps = tuple(
        g.resolution_id for g in book.resolutions if not resolution_green(g, book))
    return ResolutionIndex(resolutions=resolutions, gaps=gaps)


def resolution_for_check(bridge: Any, stage: Any) -> Optional[ResolutionRecord]:
    """The first held resolution one stage reaches, or none - honestly."""
    if stage is None:
        return None
    if not isinstance(stage, str):
        raise ValueError("an stage must be a string naming the stage")
    wanted = stage.strip()
    if not wanted:
        return None
    for resolution in _bridge_book(bridge).resolutions:
        if resolution.stage == wanted:
            return resolution
    return None


def transition_breaks(bridge: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held resolution: the resolution
    that took it and the step it took, before,
    then after. A book whose resolutions all walk inside
    the machine tells none.
    """
    book = _bridge_book(bridge)
    return tuple(
        f"{resolution_id}: {step}"
        for resolution_id, steps in _breaks_map(book).items()
        for step in steps)

def resolution_resolution(bridge: Any,
              bridge_id: Any = None) -> Tuple[ResolutionRecord, ...]:
    """The held resolutions in their held resolution, DERIVED at call time.

    Resolutions stand in the resolution the book holds them -
    the resolution their bridges were named - optionally
    for one bridge alone. Nothing here is stored:
    the resolution is the book's own held resolution, told.
    """
    book = _bridge_book(bridge)
    resolutions = list(book.resolutions)
    if bridge_id is not None:
        wanted = _clean_text(bridge_id, "a bridge id")
        resolutions = [r for r in resolutions if r.bridge_id == wanted]
    return tuple(resolutions)

def trace_of(bridge: Any, resolution_id: Any) -> str:
    """One resolution's trace, DERIVED at call time.

    The resolution's walked stages confirmed as one trace
    line, in walk resolution. A resolution that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is named
    elsewhere.
    """
    resolution = _bridge_book(bridge).resolution_for(resolution_id)
    return " > ".join(resolution.stages)

def trace_for_resolution(bridge: Any,
                  resolution_id: Any) -> Optional[TraceRecord]:
    """The held trace for one resolution, or none - honestly."""
    wanted = _clean_text(resolution_id, "a resolution id")
    for record in _bridge_book(bridge).traces:
        if record.resolution_id == wanted:
            return record
    return None

def trace_current(bridge: Any, resolution_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_resolution(bridge, resolution_id)
    if trace is None:
        return False
    return trace.trace == trace_of(bridge, resolution_id)

def note_for_resolution(bridge: Any, resolution_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one resolution (and stance, when named)."""
    wanted = _clean_text(resolution_id, "a resolution id")
    for record in _bridge_book(bridge).notes:
        if record.resolution_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(bridge: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the bridge targets, or none."""
    notes = _bridge_book(bridge).notes
    return notes[0] if notes else None


def ledger_record(bridge: Any = None) -> Dict[str, Any]:
    """The resolution ledger, DERIVED here from the held resolutions alone.

    The ledger counts the held resolutions by their
    derived completeness - green and red - names
    the current resolution, the first that does not yet
    stand complete, tells each held resolution's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held resolutions took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _bridge_book(bridge)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.resolutions
            if ("complete" if resolution_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "resolution_records": number})
    current = current_resolution(book)
    traces = []
    for resolution in book.resolutions:
        trace = trace_for_resolution(book, resolution.resolution_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, resolution.resolution_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"resolution_id": resolution.resolution_id, "trace": standing})
    return {
        "type": "resolution_well",
        "repo": RESOLUTION_SLICE,
        "standings": standings,
        "total": len(book.resolutions),
        "current_resolution": current.resolution_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This bridge's own roadmap standing, proved from the roadmap itself.

    The record loads this bridge's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 bridges in 11 parts,
    the named prefix, the next bridge where the
    resolution resolutions, and M-244's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(RESOLUTION_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "resolution_roadmap",
        "repo": RESOLUTION_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m244_title": own.title,
        "m244_part": own.part,
        "m244_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: bridges, resolutions, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or resolution ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ResolutionBook:
    title: str
    bridges: Tuple[BridgeRef, ...] = ()
    resolutions: Tuple[ResolutionRecord, ...] = ()
    views: Tuple[ResolutionView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[ResolutionPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        bridges = tuple(_check_bridge_ref(g) for g in self.bridges)
        resolutions = tuple(_check_custody_ref(g) for g in self.resolutions)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        traces = tuple(_check_trace_ref(a) for a in self.traces)
        panels = tuple(_check_panel_ref(pn) for pn in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for ref in bridges:
            if ref.bridge_id in seen_ids:
                raise ValueError(
                    f"two bridge references stand under id {ref.bridge_id!r}")
            if ref.seq in seen_seqs:
                raise ValueError(
                    f"two bridge references stand at sequence {ref.seq}")
            seen_ids.add(ref.bridge_id)
            seen_seqs.add(ref.seq)
        resolution_ids = set()
        resolution_seqs = set()
        for resolution in resolutions:
            if resolution.resolution_id in resolution_ids:
                raise ValueError(
                    f"two resolutions stand under id {resolution.resolution_id!r}")
            if resolution.seq in resolution_seqs:
                raise ValueError(
                    f"two resolutions stand at sequence {resolution.seq}")
            resolution_ids.add(resolution.resolution_id)
            resolution_seqs.add(resolution.seq)
        by_slice = {ref.bridge_id: ref for ref in bridges}
        for resolution in (resolutions if bridges else ()):

            ref = by_slice.get(resolution.bridge_id)
            if ref is None:
                raise ValueError(
                    f"resolution {resolution.resolution_id!r} is held from bridge "
                    f"{resolution.bridge_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "live":
                raise ValueError(
                    f"resolution {resolution.resolution_id!r} is held from bridge "
                    f"{resolution.bridge_id!r}, which is not active: "
                    f"no bridge is held from an queued bridge")
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
            target = (record.resolution_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for resolution "
                    f"{record.resolution_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per resolution target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_resolutions = set()
        resolution_ids = {resolution.resolution_id for resolution in resolutions}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.resolution_id in trace_resolutions:
                raise ValueError(
                    f"two traces stand for resolution "
                    f"{record.resolution_id!r}: one trace stands "
                    f"per resolution walk")
            if resolutions and record.resolution_id not in resolution_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces resolution "
                    f"{record.resolution_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_resolutions.add(record.resolution_id)
        object.__setattr__(
            self, "bridges", tuple(sorted(bridges, key=lambda g: g.seq)))
        object.__setattr__(
            self, "resolution_records", tuple(sorted(resolutions, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.resolutions + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.resolution_id for g in self.resolutions) + tuple(
            v.view_id for v in self.views)

    def resolution_ids(self) -> Tuple[str, ...]:
        return tuple(g.resolution_id for g in self.resolutions)

    def bridge_ids(self) -> Tuple[str, ...]:
        return tuple(g.bridge_id for g in self.bridges)

    def resolution_for(self, resolution_id: Any) -> ResolutionRecord:
        wanted = _clean_text(resolution_id, "a resolution id")
        for resolution in self.resolutions:
            if resolution.resolution_id == wanted:
                return resolution
        raise KeyError(f"no resolution named {wanted!r} stands in this book")

    def slice_for(self, bridge_id: Any) -> BridgeRef:
        wanted = _clean_text(bridge_id, "an bridge id")
        for ref in self.bridges:
            if ref.bridge_id == wanted:
                return ref
        raise KeyError(f"no bridge named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> ResolutionView:
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
        for resolution in self.resolutions:
            if resolution.resolution_id == wanted:
                return resolution
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "bridges": [g.to_record() for g in self.bridges],
            "resolution_records": [g.to_record() for g in self.resolutions],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: ResolutionBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: ResolutionBook) -> None:
    if book.title != "Kista key-keeper at the M-244 slice run":
        raise ValueError("the shipped example book carries another title")
    if len(book.bridges) != 3 or len(book.resolutions) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three bridge references, five resolutions and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-kista":
        raise ValueError("the pinned panel is panel-kista")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.stage for e in index.resolutions] != ["held", "held", "held"]:
        raise ValueError("the shipped example book index must derive the three held complete resolutions in held resolution")
    if index.gaps != ("resolution-bare-resolution", "resolution-leaping-resolution"):
        raise ValueError("the shipped example book must leave the bare and leaping resolutions honestly open, named in its gaps")
    named = resolution_for_check(book, EXAMPLE_STAGE)
    if named is None or named.resolution_id != "resolution-held-resolution":
        raise ValueError("the shipped example book must custody its opening resolution under the example stage")
    if trace_of(book, "resolution-held-resolution") != "named > sought > resolved > confirmed > held":
        raise ValueError("the shipped example book must derive the opening resolution's trace from its walked steps")
    if not trace_current(book, "resolution-held-resolution"):
        raise ValueError("the shipped example book must hold the opening resolution's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note resolution")

def validate_book(data: Any, *, require_example: bool = False) -> ResolutionBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, ResolutionBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a resolution book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live bridge build or execution "
                f"({key!r} is named on it): {RESOLUTION_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its resolutions under a view")
    if "resolution_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held resolutions at call time")
    if "ledger" in data or "current_resolution" in data:
        raise ValueError(
            "a book stores no ledger and no current resolution: both are "
            "derived from its held resolutions at call time")
    if "trace" in data or "resolution" in data:
        raise ValueError(
            "a book stores no trace and no resolution: both are derived "
            "from its held resolutions at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != RESOLUTION_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{RESOLUTION_SCHEMA!r}")
    if data.get("repo") is not None and (
            data["repo"] != RESOLUTION_SLICE):
        raise ValueError(
            f"a book's bridge must be {RESOLUTION_SLICE!r}")
    head = data.get("resolution_head") or data.get("kista_keykeeper") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's resolution head must be a mapping")
    title = head.get("title") or data.get("title")
    bridges = tuple(build_bridge_ref(g) for g in data.get("bridges") or ())
    resolutions = tuple(build_resolution(g) for g in data.get("resolution_records") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = ResolutionBook(
        title=title, bridges=bridges, resolutions=resolutions, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = ResolutionBook(
        title=book.title, bridges=book.bridges, resolutions=book.resolutions,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> ResolutionBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (ResolutionBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an ResolutionBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> ResolutionBook:
    return validate_book(data, require_example=require_example)


def load_resolution(
        data: Optional[Dict[str, Any]] = None) -> ResolutionBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(RESOLUTION_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_resolution_file(path: Any) -> ResolutionBook:
    """Load one resolution file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: bridge references, resolutions and views held one by one.
# ---------------------------------------------------------------------

class ResolutionRegistry:
    """An in-memory holding of bridge references, resolutions and views.

    The registry is the pure layer's model of a
    session's resolution book: bridge references are
    held under their ids, resolutions are held under
    their ids, one resolution per id and per sequence,
    and views are held in sought resolution, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[BridgeRef] = []
        self._resolutions: List[ResolutionRecord] = []
        self._views: List[ResolutionView] = []
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

    def register_bridge_ref(self, item: Any) -> BridgeRef:
        """Hold one bridge reference, resolved whole before held."""
        confirmed = _check_bridge_ref(item)
        return self._register(
            self._slices, confirmed, "bridge_id", "bridge reference")

    def register_resolution(self, item: Any) -> ResolutionRecord:
        """Hold one resolution, resolved whole before held."""
        confirmed = _check_custody_ref(item)
        return self._register(
            self._resolutions, confirmed, "resolution_id", "resolution")

    def register_view(self, view: Any) -> ResolutionView:
        """Hold one view; a view naming no id takes a fresh one."""
        confirmed = _check_view_ref(view)
        if not confirmed.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            confirmed = build_view({**confirmed.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, confirmed, "view_id", "view")

    def register_book(self, book: Any) -> ResolutionBook:
        """Hold a whole book's records, under its title."""
        confirmed = build_book(book)
        if self._title is not None and confirmed.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {confirmed.title!r}")
        for ref in confirmed.bridges:
            self.register_bridge_ref(ref)
        for resolution in confirmed.resolutions:
            self.register_resolution(resolution)
        for view in confirmed.views:
            self.register_view(view)
        self._title = confirmed.title
        return self.book()

    def book(self) -> ResolutionBook:
        return ResolutionBook(
            title=self._title or "An unheld resolution book",
            bridges=tuple(self._slices), resolutions=tuple(self._resolutions),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[BridgeRef, ...]:
        return tuple(self._slices)

    def list_resolutions(self) -> Tuple[ResolutionRecord, ...]:
        return tuple(self._resolutions)

    def list_views(self) -> Tuple[ResolutionView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._resolutions) + tuple(self._views)

    def get_slice(self, bridge_id: Any) -> BridgeRef:
        return self.book().slice_for(bridge_id)

    def get_resolution(self, resolution_id: Any) -> ResolutionRecord:
        return self.book().resolution_for(resolution_id)

    def get_view(self, view_id: Any) -> ResolutionView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the ledger target.
# ---------------------------------------------------------------------

def _bridge_book(bridge: Any) -> ResolutionBook:
    if bridge is None:
        return load_resolution()
    if isinstance(bridge, ResolutionBook):
        return bridge
    if isinstance(bridge, ResolutionRegistry):
        return bridge.book()
    return build_book(bridge)


def _heldance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _HELDANCE}


def resolution_record(resolution: Any, bridge: Any = None) -> Dict[str, Any]:
    confirmed = _check_custody_ref(resolution)
    book = _bridge_book(bridge) if bridge is not None else None
    record = {
        "type": "resolution_resolution",
        "repo": RESOLUTION_SLICE,
        "resolution_id": confirmed.resolution_id,
        "bridge_id": confirmed.bridge_id,
        "title": confirmed.title,
        "segment": segment_of(confirmed, book),
        "complete": resolution_green(confirmed, book),
        "gaps": list(resolution_gaps(confirmed, book)),
    }
    record.update(_heldance_record(confirmed))
    return record


def bridge_record(ref: Any) -> Dict[str, Any]:
    confirmed = _check_bridge_ref(ref)
    record = {
        "type": "resolution_run",
        "repo": RESOLUTION_SLICE,
        "bridge_id": confirmed.bridge_id,
        "title": confirmed.title,
        "state": confirmed.state, "custody": confirmed.custody,
    }
    record.update(_heldance_record(confirmed))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    confirmed = _check_trace_ref(record_in)
    record = {
        "type": "resolution_trace",
        "repo": RESOLUTION_SLICE,
        "trace_id": confirmed.trace_id,
        "resolution_id": confirmed.resolution_id,
        "trace": confirmed.trace,
    }
    record.update(_heldance_record(confirmed))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    confirmed = _check_view_ref(view)
    record = {
        "type": "resolution_view",
        "repo": RESOLUTION_SLICE,
        "view_id": confirmed.view_id, "seq": confirmed.seq,
        "view_filter": confirmed.view_filter,
    }
    record.update(_heldance_record(confirmed))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    confirmed = _check_note_ref(record_in)
    record = {
        "type": "resolution_note",
        "repo": RESOLUTION_SLICE,
        "note_id": confirmed.note_id,
        "resolution_id": confirmed.resolution_id,
        "stance": confirmed.stance,
    }
    record.update(_heldance_record(confirmed))
    return record


def panel_record(panel: Any, bridge: Any = None) -> Dict[str, Any]:
    confirmed = validate_panel(panel, bridge)
    record = {"type": "resolution_panel",
              "repo": RESOLUTION_SLICE}
    record.update(confirmed.to_record())
    return record


def verdict_record(verdict: Any, bridge: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, ResolutionVerdict):
        confirmed = validate_verdict(verdict, bridge)
    else:
        confirmed = derive_verdict(_bridge_book(verdict), view)
    record = {"type": "resolution_verdict",
              "repo": RESOLUTION_SLICE}
    record.update(confirmed.to_record())
    return record


def index_record(bridge: Any) -> Dict[str, Any]:
    if isinstance(bridge, ResolutionIndex):
        index = bridge
    else:
        index = derive_index(bridge)
    record = {"type": "resolution_index",
              "repo": RESOLUTION_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    confirmed = _bridge_book(book)
    record = {"type": "resolution_book",
              "repo": RESOLUTION_SLICE,
              "title": confirmed.title}
    record.update(confirmed.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(resolution: Any, bridge: Any = None) -> str:
    confirmed = _check_custody_ref(resolution)
    return (
        f"{confirmed.title} - from {confirmed.bridge_id}: "
        f"stage {confirmed.stage if confirmed.stage else 'none'}, "
        f"claims "
        f"{', '.join(confirmed.claims) if confirmed.claims else 'none'}. "
        f"{confirmed.detail}")


def panel_plain_words(bridge: Any, view: Any = None) -> str:
    panel = derive_panel(bridge, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(bridge: Any, view: Any = None) -> str:
    verdict = derive_verdict(bridge, view)
    return (
        f"The resolutions stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"resolutions stand complete.")


def view_plain_words(view: Any) -> str:
    confirmed = _check_view_ref(view)
    return f"View {confirmed.view_id}: shows {confirmed.view_filter} resolutions."


def note_plain_words(record_in: Any) -> str:
    confirmed = _check_note_ref(record_in)
    return (
        f"Note {confirmed.note_id}: {confirmed.stance} "
        f"{confirmed.resolution_id}, toward {confirmed.target}. "
        f"{confirmed.detail}")


def index_plain_words(bridge: Any) -> str:
    index = (bridge if isinstance(bridge, ResolutionIndex)
             else derive_index(bridge))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.resolutions)} green resolutions; "
        f"red, named in its gaps: {gaps}.")

def format_resolution(resolution: Any, bridge: Any = None) -> str:
    confirmed = _check_custody_ref(resolution)
    book = _bridge_book(bridge) if bridge is not None else None
    lines = [f"{confirmed.title} ({confirmed.resolution_id})"]
    lines.extend(plain_lines(confirmed))
    lines.append(confirmed.detail)
    if resolution_green(confirmed, book):
        lines.append(
            "This resolution stands complete - it walked the question "
            "sequence in the open from named to held, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This resolution stands open - it stands named in "
            f"its gaps: {', '.join(resolution_gaps(confirmed, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    confirmed = _check_view_ref(view)
    return (
        f"View {confirmed.view_id}: filter {confirmed.view_filter} - "
        f"{confirmed.detail}")


def format_note(record_in: Any) -> str:
    confirmed = _check_note_ref(record_in)
    lines = [
        f"Resolution note {confirmed.stance} {confirmed.resolution_id} "
        f"({confirmed.note_id}): {confirmed.title}. {confirmed.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or resolution it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_stage(bridge: Any, stage: Any) -> str:
    resolution = resolution_for_check(bridge, stage)
    if resolution is not None:
        return format_resolution(resolution, bridge)
    wanted = stage.strip() if isinstance(stage, str) else stage
    return (
        f"No held resolution stands under stage {wanted!r} yet - the "
        f"stage reaches nothing in this book, and no resolution is "
        f"invented for it.")


def format_book(bridge: Any = None, bridge_id: Any = None) -> str:
    book = _bridge_book(bridge)
    resolutions = (resolutions_for_bridge(book, bridge_id)
              if bridge_id is not None else book.resolutions)
    lines = [f"The Kista Key-keeper (M-244) - {book.title}"]
    lines.extend(segment_of(resolution, book) for resolution in resolutions)
    return "\n".join(lines)


def format_panel(bridge: Any = None, view: Any = None) -> str:
    panel = derive_panel(bridge, view)
    lines = [f"Resolution panel under view {panel.view_id}:"]
    lines.extend(row.segment for row in panel.rows)
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(bridge: Any = None, view: Any = None) -> str:
    verdict = derive_verdict(bridge, view)
    return verdict_plain_words(bridge, view) + (
        f" (view {verdict.view_id}, as of {verdict.latest_on})")


def format_index(bridge: Any = None) -> str:
    book = _bridge_book(bridge)
    index = derive_index(book)
    lines = ["Resolution index, derived from the held resolutions:"]
    for resolution in index.resolutions:
        lines.append(f"{resolution.stage} - {resolution.title} ({resolution.resolution_id})")
    if index.gaps:
        lines.append(
            "Red, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_resolution_screen(bridge: Any = None) -> str:
    book = _bridge_book(bridge)
    lines = [
        "The Kista Key-keeper (M-244)",
        f"{book.title}: {len(book.resolutions)} resolutions held, "
        f"{len(green_resolutions(book))} resolutions standing green, "
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


def parse_resolution_args(args: Any) -> Tuple[str, Any]:
    """Parse the /resolution grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("resolution", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("stage", "bridge"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
