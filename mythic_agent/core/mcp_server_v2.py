"""Cross-app method (roadmap slice M-234).

Part X - Bridges. The roadmap
words: **the existing `mythic-mcp` gains campaign, board, and memory-map services with versioned contracts; external agents (Hermes-class) can be dealt slices.******

What already ships, and what this service adds:

* Mythic's client face already ships (M-233, ``mythic_agent/core/mcp_client.py``): Mythic *consumes* other MCP services under per-service permissions in the same policy system. This slice builds the serving half in its v2 form - the server: the existing ``mythic-mcp`` server (``mythic_agent/mcp_server.py``) gains campaign, board, and memory-map services with versioned contracts, and external agents (Hermes-class) can be dealt slices, the dealings held as data under versioned contracts in that same policy system. The exposures book WIRES that serving face as data, in its own module, standing in the M-195 copy-and-share
  book book the M-234 book stands in: one tracker
  per book, and the tracker's charge over one
  exposure across its service held as a book - a
  exposure. The shipped exposures stand untouched behind
  their seams: this layer holds exposures as data
  over the book's services and rewrites none of them,
  and the exposures book keeps its own standing.
  Exposures stand on the ledger AS DATA alone: a
  exposure carries a ledger ref, a reference held in
  this book; holding, viewing or telling a exposure
  services no exposure live, moves no keeper and files
  nothing.
* No charter row names this service: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-234 on no row, and the
  service tests pin that absence live. The M-005
  method charter names no service row either: its
  own words name the whole of Part IX (M-201
  to M-232) as the part that executes the
  charter; Part X stands on the roadmap's own
  words, and this slice is built to those words.

* A exposure is held whole: the service it
  answers for, declared by its service id; its title;
  the exposure steps it walked, held as data in
  walk exposure; and the evidence it carries, held
  as data by service. The exposure walk is EXPLICIT:
  its sequence stands as data
  (:data:`STAGES`, :data:`TRANSITIONS`) -
  declared, contracted, authorised, served, held -
  and a exposure's standing is DERIVED at
  call time from its held steps and evidence
  alone: a exposure that opens anywhere but
  declared, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet declared held stands
  open, declared in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - campaign_ref,
  board_ref, memorymap_ref, contract_ref, policy_ref, evidence
  a tracker can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A exposure is
  served from held evidence alone, never
  from a feeling: a exposure holding a
  bare claim stands open, declared in its gaps.
* A exposure stands only for an ACTIVE
  service. The book holds each service it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  exposure naming a service that stands
  nowhere in the book refuses BY NAME, and a
  exposure for a service that is not active
  refuses BY NAME beside it: the tracker deals with
  the service in hand, in roadmap exposure, never a
  queued one, and a service whose exposure already
  stands complete is never authorised twice - the
  current exposure is derived, so a
  completed service is never the current exposure
  twice.
* The exposure's trace is visible. A trace
  record holds one exposure's walked steps
  as one trace line, exactly as walked, beside
  the exposure. The derived trace is
  computed at call time from the exposure's
  held steps; a held trace that no longer agrees
  with it stands stale, declared in the ledger - the
  trace is the walk itself, never a retelling
  of it.
* The exposure index is DERIVED at call
  time from the held exposures - one exposure
  per complete exposure, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, exposure or current-exposure
  claim on any record refuses by name.
* The current exposure is DERIVED at call
  time - the first held exposure, in held
  exposure, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its exposure, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per exposure stance; holding
  a note posts none of it, the rule stands as
  data (:data:`EXPOSURE_RULE`), and a record
  claiming a exposure was actually held,
  captured or promoted live refuses BY NAME.
  The tracker exposures - and those exposures, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the book a real exposure
  file takes, a loader reads a file anywhere on
  disk, exposures and views are contracted as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a exposure book for a session and
  telling from it. This layer reaches no live
  exposure: it writes no exposure live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no tracker, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds exposures
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The exposure walk is explicit.** A
  exposure is served against the held
  steps and legal steps alone; an illegal step
  stands declared in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  exposure that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, declared in its gaps:
  a exposure is served from evidence, not
  vibes.
* **Active services only, in roadmap exposure.** A
  exposure for a missing or queued service
  refuses by name; no exposure is invented
  for a service the tracker has not contracted with.
* **Unknown stays unknown.** A exposure
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, exposure
  and current exposure are derived, never
  stored.** Each is derived from the held
  exposures at call time; a stored one
  refuses by name, so it can never drift.
* **One exposure per exposure.** Two
  exposures standing for one exposure id
  refuse by name, and one note record stands per
  exposure stance.
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
    "EXPOSURE_RESOURCE",
    "EXPOSURE_SCHEMA",
    "EXPOSURE_SLICE",
    "EXPOSURE_RULE",
    "PLAIN_EXPLANATION",
    "THE_EXPOSURE_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "COMPLETE_WORDS",
    "SERVICE_STATES",
    "CONTRACT_VERSIONS",
    "Any",
    "Dict",
    "List",
    "Optional",
    "TraceRecord",
    "ExposureRecord",
    "IndexExposure",
    "ServiceRef",
    "NoteRecord",
    "ExposureBook",
    "ExposureIndex",
    "ExposurePanel",
    "ExposurePanelRow",
    "ExposureRegistry",
    "ExposureVerdict",
    "ExposureView",
    "TargetCount",
    "trace_for_exposure",
    "trace_record",
    "ledger_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_exposure",
    "build_service_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_exposure",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "exposure_for_check",
    "exposure_exposure",
    "exposure_record",
    "first_note",
    "format_book",
    "format_exposure",
    "format_index",
    "format_note",
    "format_stage",
    "format_panel",
    "format_exposure_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "service_record",
    "load_exposure",
    "load_exposure_file",
    "normalize_service_state",
    "normalize_contract",
    "normalize_stage",
    "normalize_claim_kind",
    "legal_step",
    "next_stage",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_exposure",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_exposure_args",
    "green_exposures",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_exposures",
    "validate_trace",
    "validate_book",
    "validate_exposure",
    "validate_service_ref",
    "validate_note",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
    "exposure_gaps",
    "exposure_green",
    "exposures_for_service",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

EXPOSURE_SCHEMA = "mythic.mcp_server_v2/1"
EXPOSURE_SLICE = "M-234"
THE_EXPOSURE_SLICE = EXPOSURE_SLICE
EXPOSURE_RESOURCE = "mcp_server_v2.yaml"
INDEX_ACTION = "index"
EXAMPLE_STAGE = "held"
STAGE_FIELDS = ("stages", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("held", "held", "blocked")
SERVICE_STATES = ("live", "dormant")
CONTRACT_VERSIONS = ("v1", "v2")
EXPOSURE_RULE = "exposures are held as data alone: the existing mythic-mcp gains campaign, board, and memory-map services with versioned contracts (the contract versions v1 and v2, one version held per service as data) - one server per book, and the server charge over one exposure held as an exposure - an exposure stands as data, held by reference (a contract ref), never served live - the exposure walk stands as an explicit exposure sequence - declared, contracted, authorised, served, held - and an exposure completes only complete, complete being a state with evidence held - campaign ref, board ref, memorymap ref, contract ref, policy ref - never a feeling, a memory, an assertion or a summary; the existing mythic-mcp gains campaign, board, and memory-map services with versioned contracts; external agents (Hermes-class) can be dealt slices - and an exposure served without authorising, or held before it is served, stands open, named in its gaps; an exposure on a legacy v1-contract service stands complete only with its contract migration held as a contract_ref; holding, viewing and telling an exposure serves no service live, deals no slice to any external agent, calls no tool, reads no resource, sends no prompt, spends nothing, spawns no process and opens no network"
PLAIN_EXPLANATION = "MCP server v2 (M-234): the existing mythic-mcp gains campaign, board, and memory-map services with versioned contracts; external agents (Hermes-class) can be dealt slices."
USAGE = 'Usage: /mcpserver | /mcpserver exposure <exposure-id> | /mcpserver stage <stage> | /mcpserver service <service-id> | /mcpserver view <view-id> | /mcpserver note <note-id> | /mcpserver index | /mcpserver panel | /mcpserver verdict'

STAGES = ("declared", "contracted", "authorised", "served", "held")
HELD_EVIDENCE = ("campaign_ref", "board_ref", "memorymap_ref", "contract_ref", "policy_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "declared": ("contracted",),
    "contracted": ("authorised",),
    "authorised": ("served",),
    "served": ("declared", "held"),
    "held": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a exposure or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a exposure stands complete.
    A stage outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_stage(stage: Any, failed: Any = False) -> Optional[str]:
    """The step the tracker takes next, DERIVED from the sequence.

    Banked leads to contracted and contracted to
    authorised; authorised leads to served; at
    served a follow-up banking steps back to declared and a finished exposure steps to held;
    held is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    served = normalize_stage(stage)
    if served == "declared":
        return "contracted"
    if served == "contracted":
        return "authorised"
    if served == "authorised":
        return "served"
    if served == "served":
        return "declared" if failed else "held"
    return None


_HELDANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "exposure_id", "seq", "service_id", "title", "stages",
    "claims", "detail",
} | set(_HELDANCE))
_SLICE_REF_KEYS = frozenset({
    "service_id", "seq", "title", "state", "contract", "detail",
} | set(_HELDANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "exposure_id", "trace", "detail",
} | set(_HELDANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_HELDANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "exposure_id", "stance", "target", "title",
    "detail",
} | set(_HELDANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "exposures", "coverage", "covered", "uncovered",
    "current_exposure", "next_exposure", "progress", "ledger",
    "current", "exposure", "breaks", "live"})
_LIVE_KEYS = (
    "live_exposure", "exposures_live", "live_question",
    "exposures_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "exposures_live",
    "resumed_live", "runs_exposure", "paused_live",
    "runs_exposure", "ran_exposure", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "exposure_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_exposure", "sent_exposure",
    "posts_note", "held_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_exposure", "filed_live", "spawns_tracker", "spawned_tracker", "sends_exposure", "sent_exposure", "writes_exposure", "wrote_exposure")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_stages(value: Any) -> Tuple[str, ...]:
    """A exposure's walked stages, held as data.

    The stages stand as a list of stage names in
    walk exposure, each one a stage of the explicit
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
    """A exposure's asked claims: claim services declared as data.

    Each claim names one service from the held
    vocabulary - the human services the gate may ask
    and the code services it must never ask, both
    held honestly as data - and a service outside
    the vocabulary refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("claims must be a list of claim services")
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
            out[key] = _clean_text(mapping.get(key), "a recorded_on service")
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
                f"{what} claims a live gate exposure or service build "
                f"execution ({key!r} is declared on it): "
                f"{EXPOSURE_RULE}")
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


def normalize_service_state(value: Any) -> str:
    state = _clean_text(value, "an service state").lower()
    if state not in SERVICE_STATES:
        raise ValueError(
            f"service state {state!r} is not one of the held "
            f"states: " + ", ".join(SERVICE_STATES))
    return state


def normalize_contract(value: Any) -> str:
    version = _clean_text(value, "a contract version").lower()
    if version not in CONTRACT_VERSIONS:
        raise ValueError(
            f"contract version {version!r} is not one of the "
            f"versioned contracts: " + ", ".join(CONTRACT_VERSIONS))
    return version


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
    service = _clean_text(value, "a claim service").lower()
    if service not in CLAIM_KINDS:
        raise ValueError(
            f"claim service {service!r} is not one of the held "
            f"services: " + ", ".join(CLAIM_KINDS))
    return service

# ---------------------------------------------------------------------
# The held exposure: one service cut from an active service.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ExposureRecord:
    """One exposure service, held as data.

    The exposure names the active service it was
    held from, by service id, its title, its
    verifiable stages, held as data, and its
    claims, declared by exposure id. The grain is
    derived, never stored: exactly one verifiable
    walk is authorised against the machine. A exposure whose
    stages are not yet held stands with its
    stages empty: it stands open, declared in
    its gaps, and no stage is invented for it.
    The exposure is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    exposure_id: str
    seq: int
    service_id: str
    title: str
    stages: Tuple[str, ...] = ()
    claims: Tuple[str, ...] = ()
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "exposure_id", _clean_text(self.exposure_id, "a exposure id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "service_id", _clean_text(self.service_id, "an service id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a exposure title"))
        object.__setattr__(
            self, "stages", _check_stages(self.stages))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a exposure detail"))
        for key in _HELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.exposure_id

    @property
    def stage(self) -> str:
        """The stage the exposure stands at: its last walked stage."""
        return self.stages[-1] if self.stages else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "exposure_id": self.exposure_id, "seq": self.seq,
            "service_id": self.service_id, "title": self.title,
            "stages": list(self.stages),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _HELDANCE:
            record[key] = getattr(self, key)
        return record


def _check_policy_ref(value: Any) -> ExposureRecord:
    if not isinstance(value, ExposureRecord):
        raise ValueError("a exposure must be a ExposureRecord")
    return value


def validate_exposure(exposure: Any) -> ExposureRecord:
    return _check_policy_ref(exposure)


def build_exposure(record: Any = None, **kwargs: Any) -> ExposureRecord:
    """Build one held exposure from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, ExposureRecord):
        if kwargs:
            raise ValueError("a exposure stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a exposure must be a mapping or a ExposureRecord")
    _needed(data, _RUN_KEYS, "a exposure")
    return ExposureRecord(
        exposure_id=data.get("exposure_id"), seq=data.get("seq"),
        service_id=data.get("service_id"), title=data.get("title"),
        stages=data.get("stages"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_heldance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each exposure to the steps it took outside the machine.

    Derived from the held exposures alone: a break is
    one consecutive pair of walked stages the
    explicit gate sequence does not allow, told
    in walk exposure as before, then after.
    """
    found: Dict[str, Tuple[str, ...]] = {}
    for exposure in book.exposures:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(exposure.stages, exposure.stages[1:])
            if not legal_step(before, after))
        if breaks:
            found[exposure.exposure_id] = breaks
    return found

def exposure_gaps(exposure: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a exposure from standing complete.

    Guarded from the exposure's own held fields alone -
    its walked steps against the explicit question
    sequence, and its held evidence against the
    held vocabulary: the exposure opens at
    declared, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a exposure stands complete only when it has
    declared held. The source names nothing
    further: no gap is borrowed from another
    exposure.
    """
    served = _check_policy_ref(exposure)
    gaps: List[str] = []
    if not served.stages:
        gaps.append(
            "has passed through no step: the exposure has not started")
        return tuple(gaps)
    if served.stages[0] != "declared":
        gaps.append(
            f"opens at {served.stages[0]}, not at declared: "
            f"the exposure opens with the reflection")
    for before, after in zip(served.stages, served.stages[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"exposure sequence does not allow")
    for service in served.claims:
        if service in BARE_CLAIMS:
            gaps.append(
                f"carries a {service} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if source is not None:
        try:
            _ref = _source_book(source).slice_for(served.service_id)
        except Exception:
            _ref = None
        if _ref is not None and _ref.contract == "v1" and \
                "contract_ref" not in served.claims:
            gaps.append(
                "stands served on a legacy v1-contract service with no "
                "contract_ref held: the versioned contract for the "
                "service is unproven")
    if served.stages[-1] != "held":
        gaps.append(
            f"has not reached held: the exposure stands "
            f"at {served.stages[-1]}")
    return tuple(gaps)

def exposure_green(exposure: Any, source: Any = None) -> bool:
    return not exposure_gaps(exposure, source)


def plain_lines(exposure: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the exposure's own fields."""
    served = _check_policy_ref(exposure)
    return (
        f"Exposure: {served.title}",
        f"Service: {served.service_id}",
        f"Stage: {served.stage if served.stage else 'none'}",
        f"Claims: "
        f"{', '.join(served.claims) if served.claims else 'none'}",
    )


def segment_of(exposure: Any, source: Any = None) -> str:
    served = _check_policy_ref(exposure)
    gaps = exposure_gaps(served, source)
    return (
        f"{served.exposure_id}: {served.title} - service: "
        f"'{served.service_id}' - stage: "
        f"'{served.stage if served.stage else 'none'}' - "
        f"stages: {len(served.stages)} - claims: "
        f"'{', '.join(served.claims) if served.claims else 'none'}' - "
        f"detail: '{served.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held service reference: the active service a book exposures from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ServiceRef:
    """One service a exposure book exposures from, held as a reference.

    The record names the service, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 service book's own telling. A exposure
    stands only from an active reference: the
    book refuses a exposure naming no held reference,
    and a exposure from an queued one, BY NAME.
    """

    service_id: str
    seq: int
    title: str
    state: str
    contract: str = "v2"
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "service_id", _clean_text(self.service_id, "an service id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(
            self, "state", normalize_service_state(self.state))
        object.__setattr__(
            self, "contract", normalize_contract(self.contract))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an service detail"))
        for key in _HELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.service_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "service_id": self.service_id, "seq": self.seq,
            "title": self.title, "state": self.state,
            "contract": self.contract,
            "detail": self.detail,
        }
        for key in _HELDANCE:
            record[key] = getattr(self, key)
        return record


def _check_service_ref(value: Any) -> ServiceRef:
    if not isinstance(value, ServiceRef):
        raise ValueError("a service reference must be an ServiceRef")
    return value


def validate_service_ref(ref: Any) -> ServiceRef:
    return _check_service_ref(ref)


def build_service_ref(record: Any = None, **kwargs: Any) -> ServiceRef:
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, ServiceRef):
        if kwargs:
            raise ValueError(
                "a service reference stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError(
            "a service reference must be a mapping or an ServiceRef")
    _needed(data, _SLICE_REF_KEYS, "a service reference")
    return ServiceRef(
        service_id=data.get("service_id"), seq=data.get("seq"),
        title=data.get("title"), state=data.get("state"), contract=data.get("contract") or "v2",
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held trace trace: the human approves the trace, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TraceRecord:
    """One trace trace, held as data.

    The record names its service and the trace the
    human active - the service's exposure ids in
    derived claim exposure, held exactly as
    active. The trace is of the set and its
    exposure, never of a step: when the derived
    trace moves, this record stands stale, declared
    in the ledger, until a new trace is active.
    """

    trace_id: str
    seq: int
    exposure_id: str
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
            self, "exposure_id", _clean_text(self.exposure_id, "an service id"))
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
            "exposure_id": self.exposure_id, "trace": self.trace,
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
        exposure_id=data.get("exposure_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a exposure, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One exposure stance, held as data.

    The record names its exposure, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per exposure stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    exposure_id: str
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
            self, "exposure_id", _clean_text(self.exposure_id, "a exposure id"))
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
            "exposure_id": self.exposure_id, "stance": self.stance,
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
        exposure_id=data.get("exposure_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held view: which services a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ExposureView:
    """A view over the book: every exposure, the green, the rest."""

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


def _check_view_ref(value: Any) -> ExposureView:
    if not isinstance(value, ExposureView):
        raise ValueError("a view must be an ExposureView")
    return value


def validate_view(view: Any) -> ExposureView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> ExposureView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, ExposureView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an ExposureView")
    _needed(data, _VIEW_KEYS, "a view")
    return ExposureView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ExposurePanelRow:
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


def _row_for_exposure(exposure: ExposureRecord,
                     source: Any = None) -> ExposurePanelRow:
    return ExposurePanelRow(
        item_id=exposure.exposure_id,
        standing="complete" if exposure_green(exposure, source) else "open",
        label=exposure.title, segment=segment_of(exposure, source),
        recorded_on=exposure.recorded_on)


def _check_row_ref(value: Any) -> ExposurePanelRow:
    if not isinstance(value, ExposurePanelRow):
        raise ValueError("a panel row must be an ExposurePanelRow")
    return value


def validate_row(row: Any, exposure: Any = None,
                 source: Any = None) -> ExposurePanelRow:
    served = _check_row_ref(row)
    if exposure is not None:
        derived = _row_for_exposure(_check_policy_ref(exposure), source)
        if served != derived:
            raise ValueError(
                f"panel row {served.item_id!r} does not agree with "
                f"the row derived from its exposure")
    return served


def build_row(row: Any = None, exposure: Any = None,
              source: Any = None,
              **kwargs: Any) -> ExposurePanelRow:
    if exposure is not None:
        derived = _row_for_exposure(_check_policy_ref(exposure), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            ExposurePanelRow(**kwargs))
        return validate_row(built, exposure, source)
    if isinstance(row, ExposurePanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return ExposurePanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on service"))
    if row is None and kwargs:
        return ExposurePanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an ExposurePanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[ExposurePanelRow, ...]
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
        f"The exposure book holds {total_items} exposures as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown exposures "
        f"stand complete.",
        "Rows stand in held exposure, the exposure the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its exposure's own fields "
        "- the service it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any exposure.",
        "Completeness is authorised from the held records alone: "
        "a exposure that steps outside the exposure sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not declared held stands open, declared in its "
        "gaps, and the exposure index is derived from the "
        "held exposures, never stored where it could drift.",
    )

@dataclass(frozen=True)
class ExposurePanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[ExposurePanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> ExposureView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, ExposureView):
        return view
    return book.view_for(view)


def shown_exposures(source: Any, view: Any = None
                   ) -> Tuple[ExposureRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.exposures
    if resolved.view_filter == "complete":
        return tuple(g for g in book.exposures if exposure_green(g, book))
    return tuple(g for g in book.exposures if not exposure_green(g, book))


def exposures_for_service(source: Any, service_id: Any
                      ) -> Tuple[ExposureRecord, ...]:
    wanted = _clean_text(service_id, "an service id")
    return tuple(
        g for g in _source_book(source).exposures if g.service_id == wanted)


def green_exposures(source: Any) -> Tuple[ExposureRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.exposures if exposure_green(g, book))


def current_exposure(source: Any) -> Optional[ExposureRecord]:
    """The book's current exposure, DERIVED at call time.

    The first held exposure, in held exposure, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held exposures alone, so it can
    never go stale against them. A book whose every
    exposure stands complete has no current exposure.
    """
    book = _source_book(source)
    for exposure in book.exposures:
        if not exposure_green(exposure, book):
            return exposure
    return None


def derive_panel(source: Any, view: Any = None) -> ExposurePanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_exposures(book, resolved)
    rows = tuple(_row_for_exposure(exposure, book) for exposure in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.exposures), default="")
    green = sum(1 for g in shown if exposure_green(g, book))
    return ExposurePanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.exposures), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.exposures), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> ExposurePanel:
    if not isinstance(value, ExposurePanel):
        raise ValueError("a panel must be an ExposurePanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> ExposurePanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 exposure).
    """
    served = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(served.view_id)
                if served.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(served, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {served.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return served


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> ExposurePanel:
    if isinstance(panel, ExposurePanel):
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
        built = ExposurePanel(
            panel_id=_clean_text(data.get("panel_id"), "a panel id"),
            view_id=data.get("view_id"),
            view_filter=normalize_view_filter(data.get("view_filter")),
            rows=rows,
            total_items=_check_count(
                data.get("total_items"), "a total_items count"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            target_counts=counts,
            as_of=_clean_text(data.get("as_of"), "an as_of service"),
            account=_check_lines(data.get("account"), "the account"))
        return validate_panel(built, source)
    if panel is None and source is not None:
        return derive_panel(source, kwargs.get("view"))
    raise ValueError("a panel must be a mapping, an ExposurePanel, or derived")


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
class ExposureVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> ExposureVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_exposures(book, resolved)
    green = sum(1 for g in shown if exposure_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return ExposureVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> ExposureVerdict:
    if not isinstance(value, ExposureVerdict):
        raise ValueError("a verdict must be an ExposureVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> ExposureVerdict:
    served = _check_verdict_ref(verdict)
    if served.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {served.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(served.view_id)
                if served.view_id is not None else None)
        derived = derive_verdict(book, view)
        if served != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return served


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> ExposureVerdict:
    if isinstance(verdict, ExposureVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = ExposureVerdict(
            verdict=_clean_text(data.get("verdict"), "a verdict"),
            view_id=data.get("view_id"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            green_shown=_check_count(
                data.get("green_shown"), "a green_shown count"),
            latest_on=_clean_text(data.get("latest_on"), "a latest service"))
        return validate_verdict(built, source)
    if verdict is None and source is not None:
        return derive_verdict(source, kwargs.get("view"))
    raise ValueError(
        "a verdict must be a mapping, an ExposureVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held services' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexExposure:
    stage: str
    exposure_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "stage": self.stage, "exposure_id": self.exposure_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class ExposureIndex:
    """The exposure index, derived from the held exposures.

    The index names one exposure per green exposure, in
    held exposure - the exposure's own one verifiable
    stage, its exposure id and its title - and the
    exposures that do not stand complete, declared in its
    gaps. Nothing here is stored on any exposure: the
    index is derived at call time from the held
    records alone, so it can never drift from them.
    """

    exposures: Tuple[IndexExposure, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "exposures": [e.to_record() for e in self.exposures],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> ExposureIndex:
    """Derive the exposure index from the book's held exposures."""
    book = _source_book(source)
    exposures = tuple(
        IndexExposure(stage=g.stage, exposure_id=g.exposure_id,
                   title=g.title)
        for g in book.exposures if exposure_green(g, book))
    gaps = tuple(
        g.exposure_id for g in book.exposures if not exposure_green(g, book))
    return ExposureIndex(exposures=exposures, gaps=gaps)


def exposure_for_check(source: Any, stage: Any) -> Optional[ExposureRecord]:
    """The first held exposure one stage reaches, or none - honestly."""
    if stage is None:
        return None
    if not isinstance(stage, str):
        raise ValueError("an stage must be a string naming the stage")
    wanted = stage.strip()
    if not wanted:
        return None
    for exposure in _source_book(source).exposures:
        if exposure.stage == wanted:
            return exposure
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held exposure: the exposure
    that took it and the step it took, before,
    then after. A book whose exposures all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{exposure_id}: {step}"
        for exposure_id, steps in _breaks_map(book).items()
        for step in steps)

def exposure_exposure(source: Any,
              service_id: Any = None) -> Tuple[ExposureRecord, ...]:
    """The held exposures in their held exposure, DERIVED at call time.

    Exposures stand in the exposure the book holds them -
    the exposure their services were declared - optionally
    for one service alone. Nothing here is stored:
    the exposure is the book's own held exposure, told.
    """
    book = _source_book(source)
    exposures = list(book.exposures)
    if service_id is not None:
        wanted = _clean_text(service_id, "a service id")
        exposures = [r for r in exposures if r.service_id == wanted]
    return tuple(exposures)

def trace_of(source: Any, exposure_id: Any) -> str:
    """One exposure's trace, DERIVED at call time.

    The exposure's walked stages joined as one trace
    line, in walk exposure. A exposure that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is declared
    elsewhere.
    """
    exposure = _source_book(source).exposure_for(exposure_id)
    return " > ".join(exposure.stages)

def trace_for_exposure(source: Any,
                  exposure_id: Any) -> Optional[TraceRecord]:
    """The held trace for one exposure, or none - honestly."""
    wanted = _clean_text(exposure_id, "a exposure id")
    for record in _source_book(source).traces:
        if record.exposure_id == wanted:
            return record
    return None

def trace_current(source: Any, exposure_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_exposure(source, exposure_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, exposure_id)

def note_for_exposure(source: Any, exposure_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one exposure (and stance, when declared)."""
    wanted = _clean_text(exposure_id, "a exposure id")
    for record in _source_book(source).notes:
        if record.exposure_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the service targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def ledger_record(source: Any = None) -> Dict[str, Any]:
    """The exposure ledger, DERIVED here from the held exposures alone.

    The ledger counts the held exposures by their
    derived completeness - green and red - names
    the current exposure, the first that does not yet
    stand complete, tells each held exposure's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held exposures took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.exposures
            if ("complete" if exposure_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "exposure_records": number})
    current = current_exposure(book)
    traces = []
    for exposure in book.exposures:
        trace = trace_for_exposure(book, exposure.exposure_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, exposure.exposure_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"exposure_id": exposure.exposure_id, "trace": standing})
    return {
        "type": "exposure_well",
        "service": EXPOSURE_SLICE,
        "standings": standings,
        "total": len(book.exposures),
        "current_exposure": current.exposure_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This service's own roadmap standing, proved from the roadmap itself.

    The record loads this service's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 services in 11 parts,
    the declared prefix, the next service where the
    exposure exposures, and M-234's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(EXPOSURE_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "exposure_roadmap",
        "service": EXPOSURE_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m234_title": own.title,
        "m234_part": own.part,
        "m234_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: services, exposures, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or exposure ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ExposureBook:
    title: str
    services: Tuple[ServiceRef, ...] = ()
    exposures: Tuple[ExposureRecord, ...] = ()
    views: Tuple[ExposureView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[ExposurePanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        services = tuple(_check_service_ref(g) for g in self.services)
        exposures = tuple(_check_policy_ref(g) for g in self.exposures)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        traces = tuple(_check_trace_ref(a) for a in self.traces)
        panels = tuple(_check_panel_ref(pn) for pn in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for ref in services:
            if ref.service_id in seen_ids:
                raise ValueError(
                    f"two service references stand under id {ref.service_id!r}")
            if ref.seq in seen_seqs:
                raise ValueError(
                    f"two service references stand at sequence {ref.seq}")
            seen_ids.add(ref.service_id)
            seen_seqs.add(ref.seq)
        exposure_ids = set()
        exposure_seqs = set()
        for exposure in exposures:
            if exposure.exposure_id in exposure_ids:
                raise ValueError(
                    f"two exposures stand under id {exposure.exposure_id!r}")
            if exposure.seq in exposure_seqs:
                raise ValueError(
                    f"two exposures stand at sequence {exposure.seq}")
            exposure_ids.add(exposure.exposure_id)
            exposure_seqs.add(exposure.seq)
        by_slice = {ref.service_id: ref for ref in services}
        for exposure in (exposures if services else ()):

            ref = by_slice.get(exposure.service_id)
            if ref is None:
                raise ValueError(
                    f"exposure {exposure.exposure_id!r} is held from service "
                    f"{exposure.service_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "live":
                raise ValueError(
                    f"exposure {exposure.exposure_id!r} is held from service "
                    f"{exposure.service_id!r}, which is not active: "
                    f"no service is held from an queued service")
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
            target = (record.exposure_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for exposure "
                    f"{record.exposure_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per exposure target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_exposures = set()
        exposure_ids = {exposure.exposure_id for exposure in exposures}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.exposure_id in trace_exposures:
                raise ValueError(
                    f"two traces stand for exposure "
                    f"{record.exposure_id!r}: one trace stands "
                    f"per exposure walk")
            if exposures and record.exposure_id not in exposure_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces exposure "
                    f"{record.exposure_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_exposures.add(record.exposure_id)
        object.__setattr__(
            self, "services", tuple(sorted(services, key=lambda g: g.seq)))
        object.__setattr__(
            self, "exposure_records", tuple(sorted(exposures, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.exposures + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.exposure_id for g in self.exposures) + tuple(
            v.view_id for v in self.views)

    def exposure_ids(self) -> Tuple[str, ...]:
        return tuple(g.exposure_id for g in self.exposures)

    def service_ids(self) -> Tuple[str, ...]:
        return tuple(g.service_id for g in self.services)

    def exposure_for(self, exposure_id: Any) -> ExposureRecord:
        wanted = _clean_text(exposure_id, "a exposure id")
        for exposure in self.exposures:
            if exposure.exposure_id == wanted:
                return exposure
        raise KeyError(f"no exposure declared {wanted!r} stands in this book")

    def slice_for(self, service_id: Any) -> ServiceRef:
        wanted = _clean_text(service_id, "an service id")
        for ref in self.services:
            if ref.service_id == wanted:
                return ref
        raise KeyError(f"no service declared {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> ExposureView:
        wanted = _clean_text(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view declared {wanted!r} stands in this book")

    def note_for(self, note_id: Any) -> NoteRecord:
        wanted = _clean_text(note_id, "a stance id")
        for record in self.notes:
            if record.note_id == wanted:
                return record
        raise KeyError(f"no stance declared {wanted!r} stands in this book")

    def trace_for(self, trace_id: Any) -> TraceRecord:
        wanted = _clean_text(trace_id, "an trace id")
        for record in self.traces:
            if record.trace_id == wanted:
                return record
        raise KeyError(f"no trace declared {wanted!r} stands in this book")

    def item_for(self, item_id: Any) -> Any:
        wanted = _clean_text(item_id, "an item id")
        for exposure in self.exposures:
            if exposure.exposure_id == wanted:
                return exposure
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item declared {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "services": [g.to_record() for g in self.services],
            "exposure_records": [g.to_record() for g in self.exposures],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: ExposureBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: ExposureBook) -> None:
    if book.title != "MCP service v2 at the M-234 slice run":
        raise ValueError("the shipped example book carries another title")
    if len(book.services) != 3 or len(book.exposures) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three service references, five exposures and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-campaign":
        raise ValueError("the pinned panel is panel-campaign")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.stage for e in index.exposures] != ["held", "held", "held"]:
        raise ValueError("the shipped example book index must derive the three held complete exposures in held exposure")
    if index.gaps != ("exposure-bare-exposure", "exposure-leaping-exposure"):
        raise ValueError("the shipped example book must leave the bare and leaping exposures honestly open, declared in its gaps")
    found = exposure_for_check(book, EXAMPLE_STAGE)
    if found is None or found.exposure_id != "exposure-held-exposure":
        raise ValueError("the shipped example book must reach its opening exposure under the example stage")
    if trace_of(book, "exposure-held-exposure") != "declared > contracted > authorised > served > held":
        raise ValueError("the shipped example book must derive the opening exposure's trace from its walked steps")
    if not trace_current(book, "exposure-held-exposure"):
        raise ValueError("the shipped example book must hold the opening exposure's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note exposure")

def validate_book(data: Any, *, require_example: bool = False) -> ExposureBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, ExposureBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a exposure book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live service build or execution "
                f"({key!r} is declared on it): {EXPOSURE_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its exposures under a view")
    if "exposure_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held exposures at call time")
    if "ledger" in data or "current_exposure" in data:
        raise ValueError(
            "a book stores no ledger and no current exposure: both are "
            "derived from its held exposures at call time")
    if "trace" in data or "exposure" in data:
        raise ValueError(
            "a book stores no trace and no exposure: both are derived "
            "from its held exposures at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != EXPOSURE_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{EXPOSURE_SCHEMA!r}")
    if data.get("service") is not None and (
            data["service"] != EXPOSURE_SLICE):
        raise ValueError(
            f"a book's service must be {EXPOSURE_SLICE!r}")
    head = data.get("exposure_head") or data.get("mcp_server_v2") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's exposure head must be a mapping")
    title = head.get("title") or data.get("title")
    services = tuple(build_service_ref(g) for g in data.get("services") or ())
    exposures = tuple(build_exposure(g) for g in data.get("exposure_records") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = ExposureBook(
        title=title, services=services, exposures=exposures, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = ExposureBook(
        title=book.title, services=book.services, exposures=book.exposures,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> ExposureBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (ExposureBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an ExposureBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> ExposureBook:
    return validate_book(data, require_example=require_example)


def load_exposure(
        data: Optional[Dict[str, Any]] = None) -> ExposureBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(EXPOSURE_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_exposure_file(path: Any) -> ExposureBook:
    """Load one exposure file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: service references, exposures and views held one by one.
# ---------------------------------------------------------------------

class ExposureRegistry:
    """An in-memory holding of service references, exposures and views.

    The registry is the pure layer's model of a
    session's exposure book: service references are
    held under their ids, exposures are held under
    their ids, one exposure per id and per sequence,
    and views are held in contracted exposure, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[ServiceRef] = []
        self._exposures: List[ExposureRecord] = []
        self._views: List[ExposureView] = []
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

    def register_service_ref(self, item: Any) -> ServiceRef:
        """Hold one service reference, authorised whole before held."""
        served = _check_service_ref(item)
        return self._register(
            self._slices, served, "service_id", "service reference")

    def register_exposure(self, item: Any) -> ExposureRecord:
        """Hold one exposure, authorised whole before held."""
        served = _check_policy_ref(item)
        return self._register(
            self._exposures, served, "exposure_id", "exposure")

    def register_view(self, view: Any) -> ExposureView:
        """Hold one view; a view naming no id takes a fresh one."""
        served = _check_view_ref(view)
        if not served.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            served = build_view({**served.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, served, "view_id", "view")

    def register_book(self, book: Any) -> ExposureBook:
        """Hold a whole book's records, under its title."""
        served = build_book(book)
        if self._title is not None and served.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {served.title!r}")
        for ref in served.services:
            self.register_service_ref(ref)
        for exposure in served.exposures:
            self.register_exposure(exposure)
        for view in served.views:
            self.register_view(view)
        self._title = served.title
        return self.book()

    def book(self) -> ExposureBook:
        return ExposureBook(
            title=self._title or "An unheld exposure book",
            services=tuple(self._slices), exposures=tuple(self._exposures),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[ServiceRef, ...]:
        return tuple(self._slices)

    def list_exposures(self) -> Tuple[ExposureRecord, ...]:
        return tuple(self._exposures)

    def list_views(self) -> Tuple[ExposureView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._exposures) + tuple(self._views)

    def get_slice(self, service_id: Any) -> ServiceRef:
        return self.book().slice_for(service_id)

    def get_exposure(self, exposure_id: Any) -> ExposureRecord:
        return self.book().exposure_for(exposure_id)

    def get_view(self, view_id: Any) -> ExposureView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the ledger target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> ExposureBook:
    if source is None:
        return load_exposure()
    if isinstance(source, ExposureBook):
        return source
    if isinstance(source, ExposureRegistry):
        return source.book()
    return build_book(source)


def _heldance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _HELDANCE}


def exposure_record(exposure: Any, source: Any = None) -> Dict[str, Any]:
    served = _check_policy_ref(exposure)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "exposure_exposure",
        "service": EXPOSURE_SLICE,
        "exposure_id": served.exposure_id,
        "service_id": served.service_id,
        "title": served.title,
        "segment": segment_of(served, book),
        "complete": exposure_green(served, book),
        "gaps": list(exposure_gaps(served, book)),
    }
    record.update(_heldance_record(served))
    return record


def service_record(ref: Any) -> Dict[str, Any]:
    served = _check_service_ref(ref)
    record = {
        "type": "exposure_run",
        "service": EXPOSURE_SLICE,
        "service_id": served.service_id,
        "title": served.title,
        "state": served.state, "contract": served.contract,
    }
    record.update(_heldance_record(served))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    served = _check_trace_ref(record_in)
    record = {
        "type": "exposure_trace",
        "service": EXPOSURE_SLICE,
        "trace_id": served.trace_id,
        "exposure_id": served.exposure_id,
        "trace": served.trace,
    }
    record.update(_heldance_record(served))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    served = _check_view_ref(view)
    record = {
        "type": "exposure_view",
        "service": EXPOSURE_SLICE,
        "view_id": served.view_id, "seq": served.seq,
        "view_filter": served.view_filter,
    }
    record.update(_heldance_record(served))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    served = _check_note_ref(record_in)
    record = {
        "type": "exposure_note",
        "service": EXPOSURE_SLICE,
        "note_id": served.note_id,
        "exposure_id": served.exposure_id,
        "stance": served.stance,
    }
    record.update(_heldance_record(served))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    served = validate_panel(panel, source)
    record = {"type": "exposure_panel",
              "service": EXPOSURE_SLICE}
    record.update(served.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, ExposureVerdict):
        served = validate_verdict(verdict, source)
    else:
        served = derive_verdict(_source_book(verdict), view)
    record = {"type": "exposure_verdict",
              "service": EXPOSURE_SLICE}
    record.update(served.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, ExposureIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "exposure_index",
              "service": EXPOSURE_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    served = _source_book(book)
    record = {"type": "exposure_book",
              "service": EXPOSURE_SLICE,
              "title": served.title}
    record.update(served.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(exposure: Any, source: Any = None) -> str:
    served = _check_policy_ref(exposure)
    return (
        f"{served.title} - from {served.service_id}: "
        f"stage {served.stage if served.stage else 'none'}, "
        f"claims "
        f"{', '.join(served.claims) if served.claims else 'none'}. "
        f"{served.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The exposures stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"exposures stand complete.")


def view_plain_words(view: Any) -> str:
    served = _check_view_ref(view)
    return f"View {served.view_id}: shows {served.view_filter} exposures."


def note_plain_words(record_in: Any) -> str:
    served = _check_note_ref(record_in)
    return (
        f"Note {served.note_id}: {served.stance} "
        f"{served.exposure_id}, toward {served.target}. "
        f"{served.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, ExposureIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.exposures)} green exposures; "
        f"red, declared in its gaps: {gaps}.")

def format_exposure(exposure: Any, source: Any = None) -> str:
    served = _check_policy_ref(exposure)
    book = _source_book(source) if source is not None else None
    lines = [f"{served.title} ({served.exposure_id})"]
    lines.extend(plain_lines(served))
    lines.append(served.detail)
    if exposure_green(served, book):
        lines.append(
            "This exposure stands complete - it walked the question "
            "sequence in the open from declared to held, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This exposure stands open - it stands declared in "
            f"its gaps: {', '.join(exposure_gaps(served, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    served = _check_view_ref(view)
    return (
        f"View {served.view_id}: filter {served.view_filter} - "
        f"{served.detail}")


def format_note(record_in: Any) -> str:
    served = _check_note_ref(record_in)
    lines = [
        f"Exposure note {served.stance} {served.exposure_id} "
        f"({served.note_id}): {served.title}. {served.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or exposure it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_stage(source: Any, stage: Any) -> str:
    exposure = exposure_for_check(source, stage)
    if exposure is not None:
        return format_exposure(exposure, source)
    wanted = stage.strip() if isinstance(stage, str) else stage
    return (
        f"No held exposure stands under stage {wanted!r} yet - the "
        f"stage reaches nothing in this book, and no exposure is "
        f"invented for it.")


def format_book(source: Any = None, service_id: Any = None) -> str:
    book = _source_book(source)
    exposures = (exposures_for_service(book, service_id)
              if service_id is not None else book.exposures)
    lines = [f"The MCP Server v2 (M-234) - {book.title}"]
    lines.extend(segment_of(exposure, book) for exposure in exposures)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Exposure panel under view {panel.view_id}:"]
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
    lines = ["Exposure index, derived from the held exposures:"]
    for exposure in index.exposures:
        lines.append(f"{exposure.stage} - {exposure.title} ({exposure.exposure_id})")
    if index.gaps:
        lines.append(
            "Red, declared honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_exposure_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The MCP Server v2 (M-234)",
        f"{book.title}: {len(book.exposures)} exposures held, "
        f"{len(green_exposures(book))} exposures standing green, "
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


def parse_exposure_args(args: Any) -> Tuple[str, Any]:
    """Parse the /exposure grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("exposure", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("stage", "service"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
