"""Cross-app method (roadmap slice M-240).

Part X - Bridges. The roadmap
words: **an editor-agnostic protocol any IDE plugin can speak; terminal-first remains complete without any IDE.******

What already ships, and what this host adds:

* Mythic's bridge faces already ship (M-233 consuming, M-234 serving, M-235 the registry, M-236 the skills standard, M-237 the custom commands, M-238 the installable bundles, M-239 the family companions book, ``mythic_agent/core/vscode_companions.py`` the nearest kin) and the host embryos already stand in the tree: the VS Code family tasks and keybindings at ``editors/vscode-extension`` and the vim embryo at ``editors/vim-plugin``, with the M-090 editor bridge (``mythic_agent/core/editor_bridge.py``) holding the $EDITOR round-trip. This slice builds the generic road M-239 deferred to this slice: an editor-agnostic protocol any IDE plugin can speak, the JetBrains family (IntelliJ, PyCharm, Rider and their kin) named first-class beside a generic host any other IDE can stand as, each protocol exchange held as data under one endpoint record, the capability, message, request, response and session declared BEFORE any exchange is granted, the endpoint a local protocol record - terminal-first remains complete without any IDE, no network opened - with nothing opened, sent or shown live. The endpoints book WIRES that protocol face as data, in its own module, standing in the M-195 copy-and-share
  book book the M-240 book stands in: one tracker
  per book, and the tracker's charge over one
  endpoint across its host held as a book - a
  endpoint. The shipped endpoints stand untouched behind
  their seams: this layer holds endpoints as data
  over the book's hosts and rewrites none of them,
  and the endpoints book keeps its own standing.
  Endpoints stand on the ledger AS DATA alone: a
  endpoint carries a ledger ref, a reference held in
  this book; holding, viewing or telling a endpoint
  hosts no endpoint live, moves no keeper and files
  nothing.
* No charter row names this host: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-240 on no row, and the
  host tests pin that absence live. The M-005
  method charter names no host row either: its
  own words name the whole of Part IX (M-201
  to M-232) as the part that executes the
  charter; Part X stands on the roadmap's own
  words, and this slice is built to those words.

* A endpoint is held whole: the host it
  answers for, declared by its host id; its title;
  the endpoint steps it walked, held as data in
  walk endpoint; and the evidence it carries, held
  as data by host. The endpoint walk is EXPLICIT:
  its sequence stands as data
  (:data:`STAGES`, :data:`TRANSITIONS`) -
  declared, negotiated, bound, exchanged, held -
  and a endpoint's standing is DERIVED at
  call time from its held steps and evidence
  alone: a endpoint that opens anywhere but
  declared, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet declared held stands
  open, declared in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - capability_ref,
  message_ref, request_ref, response_ref, channel_ref, evidence
  a tracker can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A endpoint is
  exchanged from held evidence alone, never
  from a feeling: a endpoint holding a
  bare claim stands open, declared in its gaps.
* A endpoint stands only for an ACTIVE
  host. The book holds each host it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  endpoint naming a host that stands
  nowhere in the book refuses BY NAME, and a
  endpoint for a host that is not active
  refuses BY NAME beside it: the tracker deals with
  the host in hand, in roadmap endpoint, never a
  queued one, and a host whose endpoint already
  stands complete is never bound twice - the
  current endpoint is derived, so a
  completed host is never the current endpoint
  twice.
* The endpoint's trace is visible. A trace
  record holds one endpoint's walked steps
  as one trace line, exactly as walked, beside
  the endpoint. The derived trace is
  computed at call time from the endpoint's
  held steps; a held trace that no longer agrees
  with it stands stale, declared in the ledger - the
  trace is the walk itself, never a retelling
  of it.
* The endpoint index is DERIVED at call
  time from the held endpoints - one endpoint
  per complete endpoint, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, endpoint or current-endpoint
  claim on any record refuses by name.
* The current endpoint is DERIVED at call
  time - the first held endpoint, in held
  endpoint, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its endpoint, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per endpoint stance; holding
  a note posts none of it, the rule stands as
  data (:data:`ENDPOINT_RULE`), and a record
  claiming a endpoint was actually held,
  captured or promoted live refuses BY NAME.
  The tracker endpoints - and those endpoints, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the book a real endpoint
  file takes, a loader reads a file anywhere on
  disk, endpoints and views are negotiated as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a endpoint book for a session and
  telling from it. This layer reaches no live
  endpoint: it writes no endpoint live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no tracker, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds endpoints
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The endpoint walk is explicit.** A
  endpoint is exchanged against the held
  steps and legal steps alone; an illegal step
  stands declared in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  endpoint that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, declared in its gaps:
  a endpoint is exchanged from evidence, not
  vibes.
* **Active hosts only, in roadmap endpoint.** A
  endpoint for a missing or queued host
  refuses by name; no endpoint is invented
  for a host the tracker has not negotiated with.
* **Unknown stays unknown.** A endpoint
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, endpoint
  and current endpoint are derived, never
  stored.** Each is derived from the held
  endpoints at call time; a stored one
  refuses by name, so it can never drift.
* **One endpoint per endpoint.** Two
  endpoints standing for one endpoint id
  refuse by name, and one note record stands per
  endpoint stance.
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
    "ENDPOINT_RESOURCE",
    "ENDPOINT_SCHEMA",
    "ENDPOINT_SLICE",
    "ENDPOINT_RULE",
    "PLAIN_EXPLANATION",
    "THE_ENDPOINT_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "COMPLETE_WORDS",
    "HOST_STATES",
    "CHANNELS",
    "Any",
    "Dict",
    "List",
    "Optional",
    "TraceRecord",
    "EndpointRecord",
    "IndexEndpoint",
    "HostRef",
    "NoteRecord",
    "EndpointBook",
    "EndpointIndex",
    "EndpointPanel",
    "EndpointPanelRow",
    "EndpointRegistry",
    "EndpointVerdict",
    "EndpointView",
    "TargetCount",
    "trace_for_endpoint",
    "trace_record",
    "ledger_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_endpoint",
    "build_host_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_endpoint",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "endpoint_for_check",
    "endpoint_endpoint",
    "endpoint_record",
    "first_note",
    "format_book",
    "format_endpoint",
    "format_index",
    "format_note",
    "format_stage",
    "format_panel",
    "format_endpoint_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "host_record",
    "load_endpoint",
    "load_endpoint_file",
    "normalize_host_state",
    "normalize_channel",
    "normalize_stage",
    "normalize_claim_kind",
    "legal_step",
    "next_stage",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_endpoint",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_endpoint_args",
    "green_endpoints",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_endpoints",
    "validate_trace",
    "validate_book",
    "validate_endpoint",
    "validate_host_ref",
    "validate_note",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
    "endpoint_gaps",
    "endpoint_green",
    "endpoints_for_host",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

ENDPOINT_SCHEMA = "mythic.ide_companions/1"
ENDPOINT_SLICE = "M-240"
THE_ENDPOINT_SLICE = ENDPOINT_SLICE
ENDPOINT_RESOURCE = "ide_companions.yaml"
INDEX_ACTION = "index"
EXAMPLE_STAGE = "held"
STAGE_FIELDS = ("stages", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("held", "held", "blocked")
HOST_STATES = ("live", "dormant")
CHANNELS = ("direct", "bridged", "unlinked")
ENDPOINT_RULE = "endpoints are held as data alone: an editor-agnostic protocol any IDE plugin can speak, the JetBrains family named beside the generic road (the channels direct, bridged and unlinked, one channel held per host as data) - one endpoint shelf per book, and the shelf charge over one endpoint held as an endpoint - an endpoint stands as data, held by reference (a capability ref), never spoken live - the endpoint walk stands as an explicit endpoint sequence - declared, negotiated, bound, exchanged, held - and an endpoint completes only complete, complete being a state with evidence held - capability ref, message ref, request ref, response ref, session ref, channel ref - never a feeling, a memory, an assertion or a summary; an editor-agnostic protocol any IDE plugin can speak - and an endpoint exchanged without binding, or held before it is exchanged, stands open, named in its gaps; an endpoint on an unlinked host stands complete only with its channel held as a channel_ref; defining, reading, listing and telling an endpoint opens no socket live, sends no message, shows no session, spawns no IDE, opens no network and writes nothing outside held records"
PLAIN_EXPLANATION = "IDE companions (M-240): an editor-agnostic protocol any IDE plugin can speak - the JetBrains family named beside the generic road; terminal-first remains complete without any IDE."
USAGE = 'Usage: /idecompanions | /idecompanions endpoint <endpoint-id> | /idecompanions stage <stage> | /idecompanions host <host-id> | /idecompanions view <view-id> | /idecompanions note <note-id> | /idecompanions index | /idecompanions panel | /idecompanions verdict'

STAGES = ("declared", "negotiated", "bound", "exchanged", "held")
HELD_EVIDENCE = ("capability_ref", "message_ref", "request_ref", "response_ref", "session_ref", "channel_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "declared": ("negotiated",),
    "negotiated": ("bound",),
    "bound": ("exchanged",),
    "exchanged": ("declared", "held"),
    "held": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a endpoint or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a endpoint stands complete.
    A stage outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_stage(stage: Any, failed: Any = False) -> Optional[str]:
    """The step the tracker takes next, DERIVED from the sequence.

    Banked leads to negotiated and negotiated to
    bound; bound leads to exchanged; at
    exchanged a follow-up banking steps back to declared and a finished endpoint steps to held;
    held is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    exchanged = normalize_stage(stage)
    if exchanged == "declared":
        return "negotiated"
    if exchanged == "negotiated":
        return "bound"
    if exchanged == "bound":
        return "exchanged"
    if exchanged == "exchanged":
        return "declared" if failed else "held"
    return None


_HELDANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "endpoint_id", "seq", "host_id", "title", "stages",
    "claims", "detail",
} | set(_HELDANCE))
_SLICE_REF_KEYS = frozenset({
    "host_id", "seq", "title", "state", "channel", "detail",
} | set(_HELDANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "endpoint_id", "trace", "detail",
} | set(_HELDANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_HELDANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "endpoint_id", "stance", "target", "title",
    "detail",
} | set(_HELDANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "endpoints", "coverage", "covered", "uncovered",
    "current_endpoint", "next_endpoint", "progress", "ledger",
    "current", "endpoint", "breaks", "live"})
_LIVE_KEYS = (
    "live_endpoint", "endpoints_live", "live_question",
    "endpoints_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "endpoints_live",
    "resumed_live", "runs_endpoint", "paused_live",
    "runs_endpoint", "ran_endpoint", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "endpoint_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_endpoint", "sent_endpoint",
    "posts_note", "held_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_endpoint", "filed_live", "spawns_tracker", "spawned_tracker", "sends_endpoint", "sent_endpoint", "writes_endpoint", "wrote_endpoint")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_stages(value: Any) -> Tuple[str, ...]:
    """A endpoint's walked stages, held as data.

    The stages stand as a list of stage names in
    walk endpoint, each one a stage of the explicit
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
    """A endpoint's asked claims: claim hosts declared as data.

    Each claim names one host from the held
    vocabulary - the human hosts the gate may ask
    and the code hosts it must never ask, both
    held honestly as data - and a host outside
    the vocabulary refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("claims must be a list of claim hosts")
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
            out[key] = _clean_text(mapping.get(key), "a recorded_on host")
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
                f"{what} claims a live gate endpoint or host build "
                f"execution ({key!r} is declared on it): "
                f"{ENDPOINT_RULE}")
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


def normalize_host_state(value: Any) -> str:
    state = _clean_text(value, "an host state").lower()
    if state not in HOST_STATES:
        raise ValueError(
            f"host state {state!r} is not one of the held "
            f"states: " + ", ".join(HOST_STATES))
    return state


def normalize_channel(value: Any) -> str:
    channel = _clean_text(value, "a channel").lower()
    if channel not in CHANNELS:
        raise ValueError(
            f"channel {channel!r} is not one of the "
            f"host endpoint channels: " + ", ".join(CHANNELS))
    return channel


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
    host = _clean_text(value, "a claim host").lower()
    if host not in CLAIM_KINDS:
        raise ValueError(
            f"claim host {host!r} is not one of the held "
            f"hosts: " + ", ".join(CLAIM_KINDS))
    return host

# ---------------------------------------------------------------------
# The held endpoint: one host cut from an active host.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class EndpointRecord:
    """One endpoint host, held as data.

    The endpoint names the active host it was
    held from, by host id, its title, its
    verifiable stages, held as data, and its
    claims, declared by endpoint id. The grain is
    derived, never stored: exactly one verifiable
    walk is bound against the machine. A endpoint whose
    stages are not yet held stands with its
    stages empty: it stands open, declared in
    its gaps, and no stage is invented for it.
    The endpoint is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    endpoint_id: str
    seq: int
    host_id: str
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
            self, "endpoint_id", _clean_text(self.endpoint_id, "a endpoint id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "host_id", _clean_text(self.host_id, "an host id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a endpoint title"))
        object.__setattr__(
            self, "stages", _check_stages(self.stages))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a endpoint detail"))
        for key in _HELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.endpoint_id

    @property
    def stage(self) -> str:
        """The stage the endpoint stands at: its last walked stage."""
        return self.stages[-1] if self.stages else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "endpoint_id": self.endpoint_id, "seq": self.seq,
            "host_id": self.host_id, "title": self.title,
            "stages": list(self.stages),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _HELDANCE:
            record[key] = getattr(self, key)
        return record


def _check_channel_ref(value: Any) -> EndpointRecord:
    if not isinstance(value, EndpointRecord):
        raise ValueError("a endpoint must be a EndpointRecord")
    return value


def validate_endpoint(endpoint: Any) -> EndpointRecord:
    return _check_channel_ref(endpoint)


def build_endpoint(record: Any = None, **kwargs: Any) -> EndpointRecord:
    """Build one held endpoint from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, EndpointRecord):
        if kwargs:
            raise ValueError("a endpoint stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a endpoint must be a mapping or a EndpointRecord")
    _needed(data, _RUN_KEYS, "a endpoint")
    return EndpointRecord(
        endpoint_id=data.get("endpoint_id"), seq=data.get("seq"),
        host_id=data.get("host_id"), title=data.get("title"),
        stages=data.get("stages"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_heldance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each endpoint to the steps it took outside the machine.

    Derived from the held endpoints alone: a break is
    one consecutive pair of walked stages the
    explicit gate sequence does not allow, told
    in walk endpoint as before, then after.
    """
    declared: Dict[str, Tuple[str, ...]] = {}
    for endpoint in book.endpoints:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(endpoint.stages, endpoint.stages[1:])
            if not legal_step(before, after))
        if breaks:
            declared[endpoint.endpoint_id] = breaks
    return declared

def endpoint_gaps(endpoint: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a endpoint from standing complete.

    Guarded from the endpoint's own held fields alone -
    its walked steps against the explicit question
    sequence, and its held evidence against the
    held vocabulary: the endpoint opens at
    declared, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a endpoint stands complete only when it has
    declared held. The source names nothing
    further: no gap is borrowed from another
    endpoint.
    """
    exchanged = _check_channel_ref(endpoint)
    gaps: List[str] = []
    if not exchanged.stages:
        gaps.append(
            "has passed through no step: the endpoint has not started")
        return tuple(gaps)
    if exchanged.stages[0] != "declared":
        gaps.append(
            f"opens at {exchanged.stages[0]}, not at declared: "
            f"the endpoint opens with the reflection")
    for before, after in zip(exchanged.stages, exchanged.stages[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"endpoint sequence does not allow")
    for host in exchanged.claims:
        if host in BARE_CLAIMS:
            gaps.append(
                f"carries a {host} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if source is not None:
        try:
            _ref = _source_book(source).slice_for(exchanged.host_id)
        except Exception:
            _ref = None
        if _ref is not None and _ref.channel == "unlinked" and \
                "channel_ref" not in exchanged.claims:
            gaps.append(
                "stands exchanged on an unlinked host with no "
                "channel_ref held: the channel for the "
                "host is unlinked")
    if exchanged.stages[-1] != "held":
        gaps.append(
            f"has not reached held: the endpoint stands "
            f"at {exchanged.stages[-1]}")
    return tuple(gaps)

def endpoint_green(endpoint: Any, source: Any = None) -> bool:
    return not endpoint_gaps(endpoint, source)


def plain_lines(endpoint: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the endpoint's own fields."""
    exchanged = _check_channel_ref(endpoint)
    return (
        f"Endpoint: {exchanged.title}",
        f"Host: {exchanged.host_id}",
        f"Stage: {exchanged.stage if exchanged.stage else 'none'}",
        f"Claims: "
        f"{', '.join(exchanged.claims) if exchanged.claims else 'none'}",
    )


def segment_of(endpoint: Any, source: Any = None) -> str:
    exchanged = _check_channel_ref(endpoint)
    gaps = endpoint_gaps(exchanged, source)
    return (
        f"{exchanged.endpoint_id}: {exchanged.title} - host: "
        f"'{exchanged.host_id}' - stage: "
        f"'{exchanged.stage if exchanged.stage else 'none'}' - "
        f"stages: {len(exchanged.stages)} - claims: "
        f"'{', '.join(exchanged.claims) if exchanged.claims else 'none'}' - "
        f"detail: '{exchanged.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held host reference: the active host a book endpoints from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class HostRef:
    """One host a endpoint book endpoints from, held as a reference.

    The record names the host, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 host book's own telling. A endpoint
    stands only from an active reference: the
    book refuses a endpoint naming no held reference,
    and a endpoint from an queued one, BY NAME.
    """

    host_id: str
    seq: int
    title: str
    state: str
    channel: str = "direct"
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "host_id", _clean_text(self.host_id, "an host id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(
            self, "state", normalize_host_state(self.state))
        object.__setattr__(
            self, "channel", normalize_channel(self.channel))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an host detail"))
        for key in _HELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.host_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "host_id": self.host_id, "seq": self.seq,
            "title": self.title, "state": self.state,
            "channel": self.channel,
            "detail": self.detail,
        }
        for key in _HELDANCE:
            record[key] = getattr(self, key)
        return record


def _check_host_ref(value: Any) -> HostRef:
    if not isinstance(value, HostRef):
        raise ValueError("a host reference must be an HostRef")
    return value


def validate_host_ref(ref: Any) -> HostRef:
    return _check_host_ref(ref)


def build_host_ref(record: Any = None, **kwargs: Any) -> HostRef:
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, HostRef):
        if kwargs:
            raise ValueError(
                "a host reference stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError(
            "a host reference must be a mapping or an HostRef")
    _needed(data, _SLICE_REF_KEYS, "a host reference")
    return HostRef(
        host_id=data.get("host_id"), seq=data.get("seq"),
        title=data.get("title"), state=data.get("state"), channel=data.get("channel") or "direct",
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held trace trace: the human approves the trace, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TraceRecord:
    """One trace trace, held as data.

    The record names its host and the trace the
    human active - the host's endpoint ids in
    derived claim endpoint, held exactly as
    active. The trace is of the set and its
    endpoint, never of a step: when the derived
    trace moves, this record stands stale, declared
    in the ledger, until a new trace is active.
    """

    trace_id: str
    seq: int
    endpoint_id: str
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
            self, "endpoint_id", _clean_text(self.endpoint_id, "an host id"))
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
            "endpoint_id": self.endpoint_id, "trace": self.trace,
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
        endpoint_id=data.get("endpoint_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a endpoint, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One endpoint stance, held as data.

    The record names its endpoint, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per endpoint stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    endpoint_id: str
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
            self, "endpoint_id", _clean_text(self.endpoint_id, "a endpoint id"))
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
            "endpoint_id": self.endpoint_id, "stance": self.stance,
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
        endpoint_id=data.get("endpoint_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held view: which hosts a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class EndpointView:
    """A view over the book: every endpoint, the green, the rest."""

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


def _check_view_ref(value: Any) -> EndpointView:
    if not isinstance(value, EndpointView):
        raise ValueError("a view must be an EndpointView")
    return value


def validate_view(view: Any) -> EndpointView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> EndpointView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, EndpointView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an EndpointView")
    _needed(data, _VIEW_KEYS, "a view")
    return EndpointView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class EndpointPanelRow:
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


def _row_for_endpoint(endpoint: EndpointRecord,
                     source: Any = None) -> EndpointPanelRow:
    return EndpointPanelRow(
        item_id=endpoint.endpoint_id,
        standing="complete" if endpoint_green(endpoint, source) else "open",
        label=endpoint.title, segment=segment_of(endpoint, source),
        recorded_on=endpoint.recorded_on)


def _check_row_ref(value: Any) -> EndpointPanelRow:
    if not isinstance(value, EndpointPanelRow):
        raise ValueError("a panel row must be an EndpointPanelRow")
    return value


def validate_row(row: Any, endpoint: Any = None,
                 source: Any = None) -> EndpointPanelRow:
    exchanged = _check_row_ref(row)
    if endpoint is not None:
        derived = _row_for_endpoint(_check_channel_ref(endpoint), source)
        if exchanged != derived:
            raise ValueError(
                f"panel row {exchanged.item_id!r} does not agree with "
                f"the row derived from its endpoint")
    return exchanged


def build_row(row: Any = None, endpoint: Any = None,
              source: Any = None,
              **kwargs: Any) -> EndpointPanelRow:
    if endpoint is not None:
        derived = _row_for_endpoint(_check_channel_ref(endpoint), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            EndpointPanelRow(**kwargs))
        return validate_row(built, endpoint, source)
    if isinstance(row, EndpointPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return EndpointPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on host"))
    if row is None and kwargs:
        return EndpointPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an EndpointPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[EndpointPanelRow, ...]
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
        f"The endpoint book holds {total_items} endpoints as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown endpoints "
        f"stand complete.",
        "Rows stand in held endpoint, the endpoint the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its endpoint's own fields "
        "- the host it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any endpoint.",
        "Completeness is bound from the held records alone: "
        "a endpoint that steps outside the endpoint sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not declared held stands open, declared in its "
        "gaps, and the endpoint index is derived from the "
        "held endpoints, never stored where it could drift.",
    )

@dataclass(frozen=True)
class EndpointPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[EndpointPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> EndpointView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, EndpointView):
        return view
    return book.view_for(view)


def shown_endpoints(source: Any, view: Any = None
                   ) -> Tuple[EndpointRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.endpoints
    if resolved.view_filter == "complete":
        return tuple(g for g in book.endpoints if endpoint_green(g, book))
    return tuple(g for g in book.endpoints if not endpoint_green(g, book))


def endpoints_for_host(source: Any, host_id: Any
                      ) -> Tuple[EndpointRecord, ...]:
    wanted = _clean_text(host_id, "an host id")
    return tuple(
        g for g in _source_book(source).endpoints if g.host_id == wanted)


def green_endpoints(source: Any) -> Tuple[EndpointRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.endpoints if endpoint_green(g, book))


def current_endpoint(source: Any) -> Optional[EndpointRecord]:
    """The book's current endpoint, DERIVED at call time.

    The first held endpoint, in held endpoint, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held endpoints alone, so it can
    never go stale against them. A book whose every
    endpoint stands complete has no current endpoint.
    """
    book = _source_book(source)
    for endpoint in book.endpoints:
        if not endpoint_green(endpoint, book):
            return endpoint
    return None


def derive_panel(source: Any, view: Any = None) -> EndpointPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_endpoints(book, resolved)
    rows = tuple(_row_for_endpoint(endpoint, book) for endpoint in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.endpoints), default="")
    green = sum(1 for g in shown if endpoint_green(g, book))
    return EndpointPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.endpoints), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.endpoints), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> EndpointPanel:
    if not isinstance(value, EndpointPanel):
        raise ValueError("a panel must be an EndpointPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> EndpointPanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 endpoint).
    """
    exchanged = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(exchanged.view_id)
                if exchanged.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(exchanged, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {exchanged.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return exchanged


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> EndpointPanel:
    if isinstance(panel, EndpointPanel):
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
        built = EndpointPanel(
            panel_id=_clean_text(data.get("panel_id"), "a panel id"),
            view_id=data.get("view_id"),
            view_filter=normalize_view_filter(data.get("view_filter")),
            rows=rows,
            total_items=_check_count(
                data.get("total_items"), "a total_items count"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            target_counts=counts,
            as_of=_clean_text(data.get("as_of"), "an as_of host"),
            account=_check_lines(data.get("account"), "the account"))
        return validate_panel(built, source)
    if panel is None and source is not None:
        return derive_panel(source, kwargs.get("view"))
    raise ValueError("a panel must be a mapping, an EndpointPanel, or derived")


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
class EndpointVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> EndpointVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_endpoints(book, resolved)
    green = sum(1 for g in shown if endpoint_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return EndpointVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> EndpointVerdict:
    if not isinstance(value, EndpointVerdict):
        raise ValueError("a verdict must be an EndpointVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> EndpointVerdict:
    exchanged = _check_verdict_ref(verdict)
    if exchanged.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {exchanged.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(exchanged.view_id)
                if exchanged.view_id is not None else None)
        derived = derive_verdict(book, view)
        if exchanged != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return exchanged


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> EndpointVerdict:
    if isinstance(verdict, EndpointVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = EndpointVerdict(
            verdict=_clean_text(data.get("verdict"), "a verdict"),
            view_id=data.get("view_id"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            green_shown=_check_count(
                data.get("green_shown"), "a green_shown count"),
            latest_on=_clean_text(data.get("latest_on"), "a latest host"))
        return validate_verdict(built, source)
    if verdict is None and source is not None:
        return derive_verdict(source, kwargs.get("view"))
    raise ValueError(
        "a verdict must be a mapping, an EndpointVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held hosts' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEndpoint:
    stage: str
    endpoint_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "stage": self.stage, "endpoint_id": self.endpoint_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class EndpointIndex:
    """The endpoint index, derived from the held endpoints.

    The index names one endpoint per green endpoint, in
    held endpoint - the endpoint's own one verifiable
    stage, its endpoint id and its title - and the
    endpoints that do not stand complete, declared in its
    gaps. Nothing here is stored on any endpoint: the
    index is derived at call time from the held
    records alone, so it can never drift from them.
    """

    endpoints: Tuple[IndexEndpoint, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "endpoints": [e.to_record() for e in self.endpoints],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> EndpointIndex:
    """Derive the endpoint index from the book's held endpoints."""
    book = _source_book(source)
    endpoints = tuple(
        IndexEndpoint(stage=g.stage, endpoint_id=g.endpoint_id,
                   title=g.title)
        for g in book.endpoints if endpoint_green(g, book))
    gaps = tuple(
        g.endpoint_id for g in book.endpoints if not endpoint_green(g, book))
    return EndpointIndex(endpoints=endpoints, gaps=gaps)


def endpoint_for_check(source: Any, stage: Any) -> Optional[EndpointRecord]:
    """The first held endpoint one stage reaches, or none - honestly."""
    if stage is None:
        return None
    if not isinstance(stage, str):
        raise ValueError("an stage must be a string naming the stage")
    wanted = stage.strip()
    if not wanted:
        return None
    for endpoint in _source_book(source).endpoints:
        if endpoint.stage == wanted:
            return endpoint
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held endpoint: the endpoint
    that took it and the step it took, before,
    then after. A book whose endpoints all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{endpoint_id}: {step}"
        for endpoint_id, steps in _breaks_map(book).items()
        for step in steps)

def endpoint_endpoint(source: Any,
              host_id: Any = None) -> Tuple[EndpointRecord, ...]:
    """The held endpoints in their held endpoint, DERIVED at call time.

    Endpoints stand in the endpoint the book holds them -
    the endpoint their hosts were declared - optionally
    for one host alone. Nothing here is stored:
    the endpoint is the book's own held endpoint, told.
    """
    book = _source_book(source)
    endpoints = list(book.endpoints)
    if host_id is not None:
        wanted = _clean_text(host_id, "a host id")
        endpoints = [r for r in endpoints if r.host_id == wanted]
    return tuple(endpoints)

def trace_of(source: Any, endpoint_id: Any) -> str:
    """One endpoint's trace, DERIVED at call time.

    The endpoint's walked stages exchanged as one trace
    line, in walk endpoint. A endpoint that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is declared
    elsewhere.
    """
    endpoint = _source_book(source).endpoint_for(endpoint_id)
    return " > ".join(endpoint.stages)

def trace_for_endpoint(source: Any,
                  endpoint_id: Any) -> Optional[TraceRecord]:
    """The held trace for one endpoint, or none - honestly."""
    wanted = _clean_text(endpoint_id, "a endpoint id")
    for record in _source_book(source).traces:
        if record.endpoint_id == wanted:
            return record
    return None

def trace_current(source: Any, endpoint_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_endpoint(source, endpoint_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, endpoint_id)

def note_for_endpoint(source: Any, endpoint_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one endpoint (and stance, when declared)."""
    wanted = _clean_text(endpoint_id, "a endpoint id")
    for record in _source_book(source).notes:
        if record.endpoint_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the host targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def ledger_record(source: Any = None) -> Dict[str, Any]:
    """The endpoint ledger, DERIVED here from the held endpoints alone.

    The ledger counts the held endpoints by their
    derived completeness - green and red - names
    the current endpoint, the first that does not yet
    stand complete, tells each held endpoint's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held endpoints took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.endpoints
            if ("complete" if endpoint_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "endpoint_records": number})
    current = current_endpoint(book)
    traces = []
    for endpoint in book.endpoints:
        trace = trace_for_endpoint(book, endpoint.endpoint_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, endpoint.endpoint_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"endpoint_id": endpoint.endpoint_id, "trace": standing})
    return {
        "type": "endpoint_well",
        "host": ENDPOINT_SLICE,
        "standings": standings,
        "total": len(book.endpoints),
        "current_endpoint": current.endpoint_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This host's own roadmap standing, proved from the roadmap itself.

    The record loads this host's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 hosts in 11 parts,
    the declared prefix, the next host where the
    endpoint endpoints, and M-240's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(ENDPOINT_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "endpoint_roadmap",
        "host": ENDPOINT_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m240_title": own.title,
        "m240_part": own.part,
        "m240_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: hosts, endpoints, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or endpoint ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class EndpointBook:
    title: str
    hosts: Tuple[HostRef, ...] = ()
    endpoints: Tuple[EndpointRecord, ...] = ()
    views: Tuple[EndpointView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[EndpointPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        hosts = tuple(_check_host_ref(g) for g in self.hosts)
        endpoints = tuple(_check_channel_ref(g) for g in self.endpoints)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        traces = tuple(_check_trace_ref(a) for a in self.traces)
        panels = tuple(_check_panel_ref(pn) for pn in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for ref in hosts:
            if ref.host_id in seen_ids:
                raise ValueError(
                    f"two host references stand under id {ref.host_id!r}")
            if ref.seq in seen_seqs:
                raise ValueError(
                    f"two host references stand at sequence {ref.seq}")
            seen_ids.add(ref.host_id)
            seen_seqs.add(ref.seq)
        endpoint_ids = set()
        endpoint_seqs = set()
        for endpoint in endpoints:
            if endpoint.endpoint_id in endpoint_ids:
                raise ValueError(
                    f"two endpoints stand under id {endpoint.endpoint_id!r}")
            if endpoint.seq in endpoint_seqs:
                raise ValueError(
                    f"two endpoints stand at sequence {endpoint.seq}")
            endpoint_ids.add(endpoint.endpoint_id)
            endpoint_seqs.add(endpoint.seq)
        by_slice = {ref.host_id: ref for ref in hosts}
        for endpoint in (endpoints if hosts else ()):

            ref = by_slice.get(endpoint.host_id)
            if ref is None:
                raise ValueError(
                    f"endpoint {endpoint.endpoint_id!r} is held from host "
                    f"{endpoint.host_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "live":
                raise ValueError(
                    f"endpoint {endpoint.endpoint_id!r} is held from host "
                    f"{endpoint.host_id!r}, which is not active: "
                    f"no host is held from an queued host")
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
            target = (record.endpoint_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for endpoint "
                    f"{record.endpoint_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per endpoint target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_endpoints = set()
        endpoint_ids = {endpoint.endpoint_id for endpoint in endpoints}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.endpoint_id in trace_endpoints:
                raise ValueError(
                    f"two traces stand for endpoint "
                    f"{record.endpoint_id!r}: one trace stands "
                    f"per endpoint walk")
            if endpoints and record.endpoint_id not in endpoint_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces endpoint "
                    f"{record.endpoint_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_endpoints.add(record.endpoint_id)
        object.__setattr__(
            self, "hosts", tuple(sorted(hosts, key=lambda g: g.seq)))
        object.__setattr__(
            self, "endpoint_records", tuple(sorted(endpoints, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.endpoints + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.endpoint_id for g in self.endpoints) + tuple(
            v.view_id for v in self.views)

    def endpoint_ids(self) -> Tuple[str, ...]:
        return tuple(g.endpoint_id for g in self.endpoints)

    def host_ids(self) -> Tuple[str, ...]:
        return tuple(g.host_id for g in self.hosts)

    def endpoint_for(self, endpoint_id: Any) -> EndpointRecord:
        wanted = _clean_text(endpoint_id, "a endpoint id")
        for endpoint in self.endpoints:
            if endpoint.endpoint_id == wanted:
                return endpoint
        raise KeyError(f"no endpoint declared {wanted!r} stands in this book")

    def slice_for(self, host_id: Any) -> HostRef:
        wanted = _clean_text(host_id, "an host id")
        for ref in self.hosts:
            if ref.host_id == wanted:
                return ref
        raise KeyError(f"no host declared {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> EndpointView:
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
        for endpoint in self.endpoints:
            if endpoint.endpoint_id == wanted:
                return endpoint
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item declared {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "hosts": [g.to_record() for g in self.hosts],
            "endpoint_records": [g.to_record() for g in self.endpoints],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: EndpointBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: EndpointBook) -> None:
    if book.title != "IDE companions at the M-240 slice run":
        raise ValueError("the shipped example book carries another title")
    if len(book.hosts) != 3 or len(book.endpoints) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three host references, five endpoints and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-ide":
        raise ValueError("the pinned panel is panel-ide")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.stage for e in index.endpoints] != ["held", "held", "held"]:
        raise ValueError("the shipped example book index must derive the three held complete endpoints in held endpoint")
    if index.gaps != ("endpoint-bare-endpoint", "endpoint-leaping-endpoint"):
        raise ValueError("the shipped example book must leave the bare and leaping endpoints honestly open, declared in its gaps")
    declared = endpoint_for_check(book, EXAMPLE_STAGE)
    if declared is None or declared.endpoint_id != "endpoint-held-endpoint":
        raise ValueError("the shipped example book must reach its opening endpoint under the example stage")
    if trace_of(book, "endpoint-held-endpoint") != "declared > negotiated > bound > exchanged > held":
        raise ValueError("the shipped example book must derive the opening endpoint's trace from its walked steps")
    if not trace_current(book, "endpoint-held-endpoint"):
        raise ValueError("the shipped example book must hold the opening endpoint's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note endpoint")

def validate_book(data: Any, *, require_example: bool = False) -> EndpointBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, EndpointBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a endpoint book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live host build or execution "
                f"({key!r} is declared on it): {ENDPOINT_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its endpoints under a view")
    if "endpoint_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held endpoints at call time")
    if "ledger" in data or "current_endpoint" in data:
        raise ValueError(
            "a book stores no ledger and no current endpoint: both are "
            "derived from its held endpoints at call time")
    if "trace" in data or "endpoint" in data:
        raise ValueError(
            "a book stores no trace and no endpoint: both are derived "
            "from its held endpoints at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != ENDPOINT_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{ENDPOINT_SCHEMA!r}")
    if data.get("host") is not None and (
            data["host"] != ENDPOINT_SLICE):
        raise ValueError(
            f"a book's host must be {ENDPOINT_SLICE!r}")
    head = data.get("endpoint_head") or data.get("ide_companions") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's endpoint head must be a mapping")
    title = head.get("title") or data.get("title")
    hosts = tuple(build_host_ref(g) for g in data.get("hosts") or ())
    endpoints = tuple(build_endpoint(g) for g in data.get("endpoint_records") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = EndpointBook(
        title=title, hosts=hosts, endpoints=endpoints, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = EndpointBook(
        title=book.title, hosts=book.hosts, endpoints=book.endpoints,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> EndpointBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (EndpointBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an EndpointBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> EndpointBook:
    return validate_book(data, require_example=require_example)


def load_endpoint(
        data: Optional[Dict[str, Any]] = None) -> EndpointBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(ENDPOINT_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_endpoint_file(path: Any) -> EndpointBook:
    """Load one endpoint file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: host references, endpoints and views held one by one.
# ---------------------------------------------------------------------

class EndpointRegistry:
    """An in-memory holding of host references, endpoints and views.

    The registry is the pure layer's model of a
    session's endpoint book: host references are
    held under their ids, endpoints are held under
    their ids, one endpoint per id and per sequence,
    and views are held in negotiated endpoint, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[HostRef] = []
        self._endpoints: List[EndpointRecord] = []
        self._views: List[EndpointView] = []
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

    def register_host_ref(self, item: Any) -> HostRef:
        """Hold one host reference, bound whole before held."""
        exchanged = _check_host_ref(item)
        return self._register(
            self._slices, exchanged, "host_id", "host reference")

    def register_endpoint(self, item: Any) -> EndpointRecord:
        """Hold one endpoint, bound whole before held."""
        exchanged = _check_channel_ref(item)
        return self._register(
            self._endpoints, exchanged, "endpoint_id", "endpoint")

    def register_view(self, view: Any) -> EndpointView:
        """Hold one view; a view naming no id takes a fresh one."""
        exchanged = _check_view_ref(view)
        if not exchanged.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            exchanged = build_view({**exchanged.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, exchanged, "view_id", "view")

    def register_book(self, book: Any) -> EndpointBook:
        """Hold a whole book's records, under its title."""
        exchanged = build_book(book)
        if self._title is not None and exchanged.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {exchanged.title!r}")
        for ref in exchanged.hosts:
            self.register_host_ref(ref)
        for endpoint in exchanged.endpoints:
            self.register_endpoint(endpoint)
        for view in exchanged.views:
            self.register_view(view)
        self._title = exchanged.title
        return self.book()

    def book(self) -> EndpointBook:
        return EndpointBook(
            title=self._title or "An unheld endpoint book",
            hosts=tuple(self._slices), endpoints=tuple(self._endpoints),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[HostRef, ...]:
        return tuple(self._slices)

    def list_endpoints(self) -> Tuple[EndpointRecord, ...]:
        return tuple(self._endpoints)

    def list_views(self) -> Tuple[EndpointView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._endpoints) + tuple(self._views)

    def get_slice(self, host_id: Any) -> HostRef:
        return self.book().slice_for(host_id)

    def get_endpoint(self, endpoint_id: Any) -> EndpointRecord:
        return self.book().endpoint_for(endpoint_id)

    def get_view(self, view_id: Any) -> EndpointView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the ledger target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> EndpointBook:
    if source is None:
        return load_endpoint()
    if isinstance(source, EndpointBook):
        return source
    if isinstance(source, EndpointRegistry):
        return source.book()
    return build_book(source)


def _heldance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _HELDANCE}


def endpoint_record(endpoint: Any, source: Any = None) -> Dict[str, Any]:
    exchanged = _check_channel_ref(endpoint)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "endpoint_endpoint",
        "host": ENDPOINT_SLICE,
        "endpoint_id": exchanged.endpoint_id,
        "host_id": exchanged.host_id,
        "title": exchanged.title,
        "segment": segment_of(exchanged, book),
        "complete": endpoint_green(exchanged, book),
        "gaps": list(endpoint_gaps(exchanged, book)),
    }
    record.update(_heldance_record(exchanged))
    return record


def host_record(ref: Any) -> Dict[str, Any]:
    exchanged = _check_host_ref(ref)
    record = {
        "type": "endpoint_run",
        "host": ENDPOINT_SLICE,
        "host_id": exchanged.host_id,
        "title": exchanged.title,
        "state": exchanged.state, "channel": exchanged.channel,
    }
    record.update(_heldance_record(exchanged))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    exchanged = _check_trace_ref(record_in)
    record = {
        "type": "endpoint_trace",
        "host": ENDPOINT_SLICE,
        "trace_id": exchanged.trace_id,
        "endpoint_id": exchanged.endpoint_id,
        "trace": exchanged.trace,
    }
    record.update(_heldance_record(exchanged))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    exchanged = _check_view_ref(view)
    record = {
        "type": "endpoint_view",
        "host": ENDPOINT_SLICE,
        "view_id": exchanged.view_id, "seq": exchanged.seq,
        "view_filter": exchanged.view_filter,
    }
    record.update(_heldance_record(exchanged))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    exchanged = _check_note_ref(record_in)
    record = {
        "type": "endpoint_note",
        "host": ENDPOINT_SLICE,
        "note_id": exchanged.note_id,
        "endpoint_id": exchanged.endpoint_id,
        "stance": exchanged.stance,
    }
    record.update(_heldance_record(exchanged))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    exchanged = validate_panel(panel, source)
    record = {"type": "endpoint_panel",
              "host": ENDPOINT_SLICE}
    record.update(exchanged.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, EndpointVerdict):
        exchanged = validate_verdict(verdict, source)
    else:
        exchanged = derive_verdict(_source_book(verdict), view)
    record = {"type": "endpoint_verdict",
              "host": ENDPOINT_SLICE}
    record.update(exchanged.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, EndpointIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "endpoint_index",
              "host": ENDPOINT_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    exchanged = _source_book(book)
    record = {"type": "endpoint_book",
              "host": ENDPOINT_SLICE,
              "title": exchanged.title}
    record.update(exchanged.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(endpoint: Any, source: Any = None) -> str:
    exchanged = _check_channel_ref(endpoint)
    return (
        f"{exchanged.title} - from {exchanged.host_id}: "
        f"stage {exchanged.stage if exchanged.stage else 'none'}, "
        f"claims "
        f"{', '.join(exchanged.claims) if exchanged.claims else 'none'}. "
        f"{exchanged.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The endpoints stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"endpoints stand complete.")


def view_plain_words(view: Any) -> str:
    exchanged = _check_view_ref(view)
    return f"View {exchanged.view_id}: shows {exchanged.view_filter} endpoints."


def note_plain_words(record_in: Any) -> str:
    exchanged = _check_note_ref(record_in)
    return (
        f"Note {exchanged.note_id}: {exchanged.stance} "
        f"{exchanged.endpoint_id}, toward {exchanged.target}. "
        f"{exchanged.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, EndpointIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.endpoints)} green endpoints; "
        f"red, declared in its gaps: {gaps}.")

def format_endpoint(endpoint: Any, source: Any = None) -> str:
    exchanged = _check_channel_ref(endpoint)
    book = _source_book(source) if source is not None else None
    lines = [f"{exchanged.title} ({exchanged.endpoint_id})"]
    lines.extend(plain_lines(exchanged))
    lines.append(exchanged.detail)
    if endpoint_green(exchanged, book):
        lines.append(
            "This endpoint stands complete - it walked the question "
            "sequence in the open from declared to held, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This endpoint stands open - it stands declared in "
            f"its gaps: {', '.join(endpoint_gaps(exchanged, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    exchanged = _check_view_ref(view)
    return (
        f"View {exchanged.view_id}: filter {exchanged.view_filter} - "
        f"{exchanged.detail}")


def format_note(record_in: Any) -> str:
    exchanged = _check_note_ref(record_in)
    lines = [
        f"Endpoint note {exchanged.stance} {exchanged.endpoint_id} "
        f"({exchanged.note_id}): {exchanged.title}. {exchanged.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or endpoint it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_stage(source: Any, stage: Any) -> str:
    endpoint = endpoint_for_check(source, stage)
    if endpoint is not None:
        return format_endpoint(endpoint, source)
    wanted = stage.strip() if isinstance(stage, str) else stage
    return (
        f"No held endpoint stands under stage {wanted!r} yet - the "
        f"stage reaches nothing in this book, and no endpoint is "
        f"invented for it.")


def format_book(source: Any = None, host_id: Any = None) -> str:
    book = _source_book(source)
    endpoints = (endpoints_for_host(book, host_id)
              if host_id is not None else book.endpoints)
    lines = [f"The IDE Companions (M-240) - {book.title}"]
    lines.extend(segment_of(endpoint, book) for endpoint in endpoints)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Endpoint panel under view {panel.view_id}:"]
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
    lines = ["Endpoint index, derived from the held endpoints:"]
    for endpoint in index.endpoints:
        lines.append(f"{endpoint.stage} - {endpoint.title} ({endpoint.endpoint_id})")
    if index.gaps:
        lines.append(
            "Red, declared honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_endpoint_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The IDE Companions (M-240)",
        f"{book.title}: {len(book.endpoints)} endpoints held, "
        f"{len(green_endpoints(book))} endpoints standing green, "
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


def parse_endpoint_args(args: Any) -> Tuple[str, Any]:
    """Parse the /endpoint grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("endpoint", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("stage", "host"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
