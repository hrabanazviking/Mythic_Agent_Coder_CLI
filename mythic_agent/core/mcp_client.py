"""Cross-app method (roadmap slice M-233).

Part X - Bridges. The roadmap
words: **Mythic *consumes* MCP servers (tools, resources, prompts) with per-server permissions under the same policy system — the missing half of its MCP face.******

What already ships, and what this server adds:

* Mythic's server face already ships (``mythic_agent/mcp_server.py``, the ``mythic-mcp`` server): Mythic *serves* its core-memory, archival, task and capability tools to outside agents, every call authorised through the machine ToolPolicy (``core/policy.py``). This slice builds the missing half - the client: Mythic *consumes* other MCP servers, their tools, resources and prompts held as data under per-server permissions in that same policy system. The connections book WIRES that consuming face as data, in its own module, standing in the M-195 copy-and-share
  book book the M-233 book stands in: one tracker
  per book, and the tracker's charge over one
  connection across its server held as a book - a
  connection. The shipped connections stand untouched behind
  their seams: this layer holds connections as data
  over the book's servers and rewrites none of them,
  and the connections book keeps its own standing.
  Connections stand on the ledger AS DATA alone: a
  connection carries a ledger ref, a reference held in
  this book; holding, viewing or telling a connection
  servers no connection live, moves no keeper and files
  nothing.
* No charter row names this server: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-233 on no row, and the
  server tests pin that absence live. The M-005
  method charter names no server row either: its
  own words name the whole of Part IX (M-201
  to M-232) as the part that executes the
  charter; Part X stands on the roadmap's own
  words, and this slice is built to those words.

* A connection is held whole: the server it
  answers for, discovered by its server id; its title;
  the connection steps it walked, held as data in
  walk connection; and the evidence it carries, held
  as data by server. The connection walk is EXPLICIT:
  its sequence stands as data
  (:data:`STAGES`, :data:`TRANSITIONS`) -
  discovered, inspected, permitted, connected, held -
  and a connection's standing is DERIVED at
  call time from its held steps and evidence
  alone: a connection that opens anywhere but
  discovered, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet discovered held stands
  open, discovered in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - tools_ref,
  resources_ref, prompts_ref, manifest_ref, policy_ref, evidence
  a tracker can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A connection is
  connected from held evidence alone, never
  from a feeling: a connection holding a
  bare claim stands open, discovered in its gaps.
* A connection stands only for an ACTIVE
  server. The book holds each server it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  connection naming a server that stands
  nowhere in the book refuses BY NAME, and a
  connection for a server that is not active
  refuses BY NAME beside it: the tracker deals with
  the server in hand, in roadmap connection, never a
  queued one, and a server whose connection already
  stands complete is never permitted twice - the
  current connection is derived, so a
  completed server is never the current connection
  twice.
* The connection's trace is visible. A trace
  record holds one connection's walked steps
  as one trace line, exactly as walked, beside
  the connection. The derived trace is
  computed at call time from the connection's
  held steps; a held trace that no longer agrees
  with it stands stale, discovered in the ledger - the
  trace is the walk itself, never a retelling
  of it.
* The connection index is DERIVED at call
  time from the held connections - one connection
  per complete connection, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, connection or current-connection
  claim on any record refuses by name.
* The current connection is DERIVED at call
  time - the first held connection, in held
  connection, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its connection, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per connection stance; holding
  a note posts none of it, the rule stands as
  data (:data:`CONNECTION_RULE`), and a record
  claiming a connection was actually held,
  captured or promoted live refuses BY NAME.
  The tracker connections - and those connections, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the book a real connection
  file takes, a loader reads a file anywhere on
  disk, connections and views are inspected as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a connection book for a session and
  telling from it. This layer reaches no live
  connection: it writes no connection live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no tracker, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds connections
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The connection walk is explicit.** A
  connection is connected against the held
  steps and legal steps alone; an illegal step
  stands discovered in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  connection that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, discovered in its gaps:
  a connection is connected from evidence, not
  vibes.
* **Active servers only, in roadmap connection.** A
  connection for a missing or queued server
  refuses by name; no connection is invented
  for a server the tracker has not inspected with.
* **Unknown stays unknown.** A connection
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, connection
  and current connection are derived, never
  stored.** Each is derived from the held
  connections at call time; a stored one
  refuses by name, so it can never drift.
* **One connection per connection.** Two
  connections standing for one connection id
  refuse by name, and one note record stands per
  connection stance.
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
    "CONNECTION_RESOURCE",
    "CONNECTION_SCHEMA",
    "CONNECTION_SLICE",
    "CONNECTION_RULE",
    "PLAIN_EXPLANATION",
    "THE_CONNECTION_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "COMPLETE_WORDS",
    "SERVER_STATES",
    "PERMISSION_MODES",
    "Any",
    "Dict",
    "List",
    "Optional",
    "TraceRecord",
    "ConnectionRecord",
    "IndexConnection",
    "ServerRef",
    "NoteRecord",
    "ConnectionBook",
    "ConnectionIndex",
    "ConnectionPanel",
    "ConnectionPanelRow",
    "ConnectionRegistry",
    "ConnectionVerdict",
    "ConnectionView",
    "TargetCount",
    "trace_for_connection",
    "trace_record",
    "ledger_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_connection",
    "build_server_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_connection",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "connection_for_check",
    "connection_connection",
    "connection_record",
    "first_note",
    "format_book",
    "format_connection",
    "format_index",
    "format_note",
    "format_stage",
    "format_panel",
    "format_connection_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "server_record",
    "load_connection",
    "load_connection_file",
    "normalize_server_state",
    "normalize_permission",
    "normalize_stage",
    "normalize_claim_kind",
    "legal_step",
    "next_stage",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_connection",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_connection_args",
    "green_connections",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_connections",
    "validate_trace",
    "validate_book",
    "validate_connection",
    "validate_server_ref",
    "validate_note",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
    "connection_gaps",
    "connection_green",
    "connections_for_server",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

CONNECTION_SCHEMA = "mythic.mcp_client/1"
CONNECTION_SLICE = "M-233"
THE_CONNECTION_SLICE = CONNECTION_SLICE
CONNECTION_RESOURCE = "mcp_client.yaml"
INDEX_ACTION = "index"
EXAMPLE_STAGE = "held"
STAGE_FIELDS = ("stages", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("held", "held", "blocked")
SERVER_STATES = ("live", "dormant")
PERMISSION_MODES = ("read-only", "ask", "trusted")
CONNECTION_RULE = "connections are held as data alone: Mythic consumes MCP servers - tools, resources and prompts - under per-server permissions held in the same policy system as every Mythic tool (the ToolPolicy modes read-only, ask and trusted, one mode held per server as data) - one client per book, and the client charge over one connection held as a connection - a connection stands as data, held by reference (a manifest ref), never dialled live - the connection walk stands as an explicit connection sequence - discovered, inspected, permitted, connected, held - and a connection completes only complete, complete being a state with evidence held - tools ref, resources ref, prompts ref, manifest ref, policy ref - never a feeling, a memory, an assertion or a summary; Mythic *consumes* MCP servers (tools, resources, prompts) with per-server permissions under the same policy system - the missing half of its MCP face - and a connection connected without permitting, or held before it is connected, stands open, named in its gaps; a connection on an ask-mode server stands complete only with its policy decision held as a policy_ref; holding, viewing and telling a connection connects to no server live, calls no tool, reads no resource, sends no prompt, spends nothing, spawns no process and opens no network"
PLAIN_EXPLANATION = "MCP client (M-233): Mythic consumes MCP servers (tools, resources, prompts) with per-server permissions under the same policy system — the missing half of its MCP face."
USAGE = 'Usage: /mcpclient | /mcpclient connection <connection-id> | /mcpclient stage <stage> | /mcpclient server <server-id> | /mcpclient view <view-id> | /mcpclient note <note-id> | /mcpclient index | /mcpclient panel | /mcpclient verdict'

STAGES = ("discovered", "inspected", "permitted", "connected", "held")
HELD_EVIDENCE = ("tools_ref", "resources_ref", "prompts_ref", "manifest_ref", "policy_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "discovered": ("inspected",),
    "inspected": ("permitted",),
    "permitted": ("connected",),
    "connected": ("discovered", "held"),
    "held": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a connection or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a connection stands complete.
    A stage outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_stage(stage: Any, failed: Any = False) -> Optional[str]:
    """The step the tracker takes next, DERIVED from the sequence.

    Banked leads to inspected and inspected to
    permitted; permitted leads to connected; at
    connected a follow-up banking steps back to discovered and a finished connection steps to held;
    held is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    connected = normalize_stage(stage)
    if connected == "discovered":
        return "inspected"
    if connected == "inspected":
        return "permitted"
    if connected == "permitted":
        return "connected"
    if connected == "connected":
        return "discovered" if failed else "held"
    return None


_HELDANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "connection_id", "seq", "server_id", "title", "stages",
    "claims", "detail",
} | set(_HELDANCE))
_SLICE_REF_KEYS = frozenset({
    "server_id", "seq", "title", "state", "permission", "detail",
} | set(_HELDANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "connection_id", "trace", "detail",
} | set(_HELDANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_HELDANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "connection_id", "stance", "target", "title",
    "detail",
} | set(_HELDANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "connections", "coverage", "covered", "uncovered",
    "current_connection", "next_connection", "progress", "ledger",
    "current", "connection", "breaks", "live"})
_LIVE_KEYS = (
    "live_connection", "connections_live", "live_question",
    "connections_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "connections_live",
    "resumed_live", "runs_connection", "paused_live",
    "runs_connection", "ran_connection", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "connection_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_connection", "sent_connection",
    "posts_note", "held_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_connection", "filed_live", "spawns_tracker", "spawned_tracker", "sends_connection", "sent_connection", "writes_connection", "wrote_connection")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_stages(value: Any) -> Tuple[str, ...]:
    """A connection's walked stages, held as data.

    The stages stand as a list of stage names in
    walk connection, each one a stage of the explicit
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
    """A connection's asked claims: claim servers discovered as data.

    Each claim names one server from the held
    vocabulary - the human servers the gate may ask
    and the code servers it must never ask, both
    held honestly as data - and a server outside
    the vocabulary refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("claims must be a list of claim servers")
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
            out[key] = _clean_text(mapping.get(key), "a recorded_on server")
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
                f"{what} claims a live gate connection or server build "
                f"execution ({key!r} is discovered on it): "
                f"{CONNECTION_RULE}")
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


def normalize_server_state(value: Any) -> str:
    state = _clean_text(value, "an server state").lower()
    if state not in SERVER_STATES:
        raise ValueError(
            f"server state {state!r} is not one of the held "
            f"states: " + ", ".join(SERVER_STATES))
    return state


def normalize_permission(value: Any) -> str:
    mode = _clean_text(value, "a permission mode").lower()
    if mode not in PERMISSION_MODES:
        raise ValueError(
            f"permission mode {mode!r} is not one of the policy "
            f"modes: " + ", ".join(PERMISSION_MODES))
    return mode


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
    server = _clean_text(value, "a claim server").lower()
    if server not in CLAIM_KINDS:
        raise ValueError(
            f"claim server {server!r} is not one of the held "
            f"servers: " + ", ".join(CLAIM_KINDS))
    return server

# ---------------------------------------------------------------------
# The held connection: one server cut from an active server.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ConnectionRecord:
    """One connection server, held as data.

    The connection names the active server it was
    held from, by server id, its title, its
    verifiable stages, held as data, and its
    claims, discovered by connection id. The grain is
    derived, never stored: exactly one verifiable
    walk is permitted against the machine. A connection whose
    stages are not yet held stands with its
    stages empty: it stands open, discovered in
    its gaps, and no stage is invented for it.
    The connection is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    connection_id: str
    seq: int
    server_id: str
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
            self, "connection_id", _clean_text(self.connection_id, "a connection id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "server_id", _clean_text(self.server_id, "an server id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a connection title"))
        object.__setattr__(
            self, "stages", _check_stages(self.stages))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a connection detail"))
        for key in _HELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.connection_id

    @property
    def stage(self) -> str:
        """The stage the connection stands at: its last walked stage."""
        return self.stages[-1] if self.stages else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "connection_id": self.connection_id, "seq": self.seq,
            "server_id": self.server_id, "title": self.title,
            "stages": list(self.stages),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _HELDANCE:
            record[key] = getattr(self, key)
        return record


def _check_policy_ref(value: Any) -> ConnectionRecord:
    if not isinstance(value, ConnectionRecord):
        raise ValueError("a connection must be a ConnectionRecord")
    return value


def validate_connection(connection: Any) -> ConnectionRecord:
    return _check_policy_ref(connection)


def build_connection(record: Any = None, **kwargs: Any) -> ConnectionRecord:
    """Build one held connection from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, ConnectionRecord):
        if kwargs:
            raise ValueError("a connection stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a connection must be a mapping or a ConnectionRecord")
    _needed(data, _RUN_KEYS, "a connection")
    return ConnectionRecord(
        connection_id=data.get("connection_id"), seq=data.get("seq"),
        server_id=data.get("server_id"), title=data.get("title"),
        stages=data.get("stages"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_heldance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each connection to the steps it took outside the machine.

    Derived from the held connections alone: a break is
    one consecutive pair of walked stages the
    explicit gate sequence does not allow, told
    in walk connection as before, then after.
    """
    found: Dict[str, Tuple[str, ...]] = {}
    for connection in book.connections:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(connection.stages, connection.stages[1:])
            if not legal_step(before, after))
        if breaks:
            found[connection.connection_id] = breaks
    return found

def connection_gaps(connection: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a connection from standing complete.

    Guarded from the connection's own held fields alone -
    its walked steps against the explicit question
    sequence, and its held evidence against the
    held vocabulary: the connection opens at
    discovered, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a connection stands complete only when it has
    discovered held. The source names nothing
    further: no gap is borrowed from another
    connection.
    """
    connected = _check_policy_ref(connection)
    gaps: List[str] = []
    if not connected.stages:
        gaps.append(
            "has passed through no step: the connection has not started")
        return tuple(gaps)
    if connected.stages[0] != "discovered":
        gaps.append(
            f"opens at {connected.stages[0]}, not at discovered: "
            f"the connection opens with the reflection")
    for before, after in zip(connected.stages, connected.stages[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"connection sequence does not allow")
    for server in connected.claims:
        if server in BARE_CLAIMS:
            gaps.append(
                f"carries a {server} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if source is not None:
        try:
            _ref = _source_book(source).slice_for(connected.server_id)
        except Exception:
            _ref = None
        if _ref is not None and _ref.permission == "ask" and \
                "policy_ref" not in connected.claims:
            gaps.append(
                "stands permitted on an ask-mode server with no "
                "policy_ref held: per-server permission under the "
                "policy system is unproven")
    if connected.stages[-1] != "held":
        gaps.append(
            f"has not reached held: the connection stands "
            f"at {connected.stages[-1]}")
    return tuple(gaps)

def connection_green(connection: Any, source: Any = None) -> bool:
    return not connection_gaps(connection, source)


def plain_lines(connection: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the connection's own fields."""
    connected = _check_policy_ref(connection)
    return (
        f"Connection: {connected.title}",
        f"Server: {connected.server_id}",
        f"Stage: {connected.stage if connected.stage else 'none'}",
        f"Claims: "
        f"{', '.join(connected.claims) if connected.claims else 'none'}",
    )


def segment_of(connection: Any, source: Any = None) -> str:
    connected = _check_policy_ref(connection)
    gaps = connection_gaps(connected, source)
    return (
        f"{connected.connection_id}: {connected.title} - server: "
        f"'{connected.server_id}' - stage: "
        f"'{connected.stage if connected.stage else 'none'}' - "
        f"stages: {len(connected.stages)} - claims: "
        f"'{', '.join(connected.claims) if connected.claims else 'none'}' - "
        f"detail: '{connected.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held server reference: the active server a book connections from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ServerRef:
    """One server a connection book connections from, held as a reference.

    The record names the server, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 server book's own telling. A connection
    stands only from an active reference: the
    book refuses a connection naming no held reference,
    and a connection from an queued one, BY NAME.
    """

    server_id: str
    seq: int
    title: str
    state: str
    permission: str = "trusted"
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "server_id", _clean_text(self.server_id, "an server id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(
            self, "state", normalize_server_state(self.state))
        object.__setattr__(
            self, "permission", normalize_permission(self.permission))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an server detail"))
        for key in _HELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.server_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "server_id": self.server_id, "seq": self.seq,
            "title": self.title, "state": self.state,
            "permission": self.permission,
            "detail": self.detail,
        }
        for key in _HELDANCE:
            record[key] = getattr(self, key)
        return record


def _check_server_ref(value: Any) -> ServerRef:
    if not isinstance(value, ServerRef):
        raise ValueError("a server reference must be an ServerRef")
    return value


def validate_server_ref(ref: Any) -> ServerRef:
    return _check_server_ref(ref)


def build_server_ref(record: Any = None, **kwargs: Any) -> ServerRef:
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, ServerRef):
        if kwargs:
            raise ValueError(
                "a server reference stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError(
            "a server reference must be a mapping or an ServerRef")
    _needed(data, _SLICE_REF_KEYS, "a server reference")
    return ServerRef(
        server_id=data.get("server_id"), seq=data.get("seq"),
        title=data.get("title"), state=data.get("state"), permission=data.get("permission") or "trusted",
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held trace trace: the human approves the trace, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TraceRecord:
    """One trace trace, held as data.

    The record names its server and the trace the
    human active - the server's connection ids in
    derived claim connection, held exactly as
    active. The trace is of the set and its
    connection, never of a step: when the derived
    trace moves, this record stands stale, discovered
    in the ledger, until a new trace is active.
    """

    trace_id: str
    seq: int
    connection_id: str
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
            self, "connection_id", _clean_text(self.connection_id, "an server id"))
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
            "connection_id": self.connection_id, "trace": self.trace,
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
        connection_id=data.get("connection_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a connection, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One connection stance, held as data.

    The record names its connection, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per connection stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    connection_id: str
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
            self, "connection_id", _clean_text(self.connection_id, "a connection id"))
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
            "connection_id": self.connection_id, "stance": self.stance,
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
        connection_id=data.get("connection_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held view: which servers a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ConnectionView:
    """A view over the book: every connection, the green, the rest."""

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


def _check_view_ref(value: Any) -> ConnectionView:
    if not isinstance(value, ConnectionView):
        raise ValueError("a view must be an ConnectionView")
    return value


def validate_view(view: Any) -> ConnectionView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> ConnectionView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, ConnectionView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an ConnectionView")
    _needed(data, _VIEW_KEYS, "a view")
    return ConnectionView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ConnectionPanelRow:
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


def _row_for_connection(connection: ConnectionRecord,
                     source: Any = None) -> ConnectionPanelRow:
    return ConnectionPanelRow(
        item_id=connection.connection_id,
        standing="complete" if connection_green(connection, source) else "open",
        label=connection.title, segment=segment_of(connection, source),
        recorded_on=connection.recorded_on)


def _check_row_ref(value: Any) -> ConnectionPanelRow:
    if not isinstance(value, ConnectionPanelRow):
        raise ValueError("a panel row must be an ConnectionPanelRow")
    return value


def validate_row(row: Any, connection: Any = None,
                 source: Any = None) -> ConnectionPanelRow:
    connected = _check_row_ref(row)
    if connection is not None:
        derived = _row_for_connection(_check_policy_ref(connection), source)
        if connected != derived:
            raise ValueError(
                f"panel row {connected.item_id!r} does not agree with "
                f"the row derived from its connection")
    return connected


def build_row(row: Any = None, connection: Any = None,
              source: Any = None,
              **kwargs: Any) -> ConnectionPanelRow:
    if connection is not None:
        derived = _row_for_connection(_check_policy_ref(connection), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            ConnectionPanelRow(**kwargs))
        return validate_row(built, connection, source)
    if isinstance(row, ConnectionPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return ConnectionPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on server"))
    if row is None and kwargs:
        return ConnectionPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an ConnectionPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[ConnectionPanelRow, ...]
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
        f"The connection book holds {total_items} connections as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown connections "
        f"stand complete.",
        "Rows stand in held connection, the connection the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its connection's own fields "
        "- the server it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any connection.",
        "Completeness is permitted from the held records alone: "
        "a connection that steps outside the connection sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not discovered held stands open, discovered in its "
        "gaps, and the connection index is derived from the "
        "held connections, never stored where it could drift.",
    )

@dataclass(frozen=True)
class ConnectionPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[ConnectionPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> ConnectionView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, ConnectionView):
        return view
    return book.view_for(view)


def shown_connections(source: Any, view: Any = None
                   ) -> Tuple[ConnectionRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.connections
    if resolved.view_filter == "complete":
        return tuple(g for g in book.connections if connection_green(g, book))
    return tuple(g for g in book.connections if not connection_green(g, book))


def connections_for_server(source: Any, server_id: Any
                      ) -> Tuple[ConnectionRecord, ...]:
    wanted = _clean_text(server_id, "an server id")
    return tuple(
        g for g in _source_book(source).connections if g.server_id == wanted)


def green_connections(source: Any) -> Tuple[ConnectionRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.connections if connection_green(g, book))


def current_connection(source: Any) -> Optional[ConnectionRecord]:
    """The book's current connection, DERIVED at call time.

    The first held connection, in held connection, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held connections alone, so it can
    never go stale against them. A book whose every
    connection stands complete has no current connection.
    """
    book = _source_book(source)
    for connection in book.connections:
        if not connection_green(connection, book):
            return connection
    return None


def derive_panel(source: Any, view: Any = None) -> ConnectionPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_connections(book, resolved)
    rows = tuple(_row_for_connection(connection, book) for connection in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.connections), default="")
    green = sum(1 for g in shown if connection_green(g, book))
    return ConnectionPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.connections), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.connections), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> ConnectionPanel:
    if not isinstance(value, ConnectionPanel):
        raise ValueError("a panel must be an ConnectionPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> ConnectionPanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 connection).
    """
    connected = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(connected.view_id)
                if connected.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(connected, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {connected.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return connected


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> ConnectionPanel:
    if isinstance(panel, ConnectionPanel):
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
        built = ConnectionPanel(
            panel_id=_clean_text(data.get("panel_id"), "a panel id"),
            view_id=data.get("view_id"),
            view_filter=normalize_view_filter(data.get("view_filter")),
            rows=rows,
            total_items=_check_count(
                data.get("total_items"), "a total_items count"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            target_counts=counts,
            as_of=_clean_text(data.get("as_of"), "an as_of server"),
            account=_check_lines(data.get("account"), "the account"))
        return validate_panel(built, source)
    if panel is None and source is not None:
        return derive_panel(source, kwargs.get("view"))
    raise ValueError("a panel must be a mapping, an ConnectionPanel, or derived")


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
class ConnectionVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> ConnectionVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_connections(book, resolved)
    green = sum(1 for g in shown if connection_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return ConnectionVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> ConnectionVerdict:
    if not isinstance(value, ConnectionVerdict):
        raise ValueError("a verdict must be an ConnectionVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> ConnectionVerdict:
    connected = _check_verdict_ref(verdict)
    if connected.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {connected.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(connected.view_id)
                if connected.view_id is not None else None)
        derived = derive_verdict(book, view)
        if connected != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return connected


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> ConnectionVerdict:
    if isinstance(verdict, ConnectionVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = ConnectionVerdict(
            verdict=_clean_text(data.get("verdict"), "a verdict"),
            view_id=data.get("view_id"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            green_shown=_check_count(
                data.get("green_shown"), "a green_shown count"),
            latest_on=_clean_text(data.get("latest_on"), "a latest server"))
        return validate_verdict(built, source)
    if verdict is None and source is not None:
        return derive_verdict(source, kwargs.get("view"))
    raise ValueError(
        "a verdict must be a mapping, an ConnectionVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held servers' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexConnection:
    stage: str
    connection_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "stage": self.stage, "connection_id": self.connection_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class ConnectionIndex:
    """The connection index, derived from the held connections.

    The index names one connection per green connection, in
    held connection - the connection's own one verifiable
    stage, its connection id and its title - and the
    connections that do not stand complete, discovered in its
    gaps. Nothing here is stored on any connection: the
    index is derived at call time from the held
    records alone, so it can never drift from them.
    """

    connections: Tuple[IndexConnection, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "connections": [e.to_record() for e in self.connections],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> ConnectionIndex:
    """Derive the connection index from the book's held connections."""
    book = _source_book(source)
    connections = tuple(
        IndexConnection(stage=g.stage, connection_id=g.connection_id,
                   title=g.title)
        for g in book.connections if connection_green(g, book))
    gaps = tuple(
        g.connection_id for g in book.connections if not connection_green(g, book))
    return ConnectionIndex(connections=connections, gaps=gaps)


def connection_for_check(source: Any, stage: Any) -> Optional[ConnectionRecord]:
    """The first held connection one stage reaches, or none - honestly."""
    if stage is None:
        return None
    if not isinstance(stage, str):
        raise ValueError("an stage must be a string naming the stage")
    wanted = stage.strip()
    if not wanted:
        return None
    for connection in _source_book(source).connections:
        if connection.stage == wanted:
            return connection
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held connection: the connection
    that took it and the step it took, before,
    then after. A book whose connections all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{connection_id}: {step}"
        for connection_id, steps in _breaks_map(book).items()
        for step in steps)

def connection_connection(source: Any,
              server_id: Any = None) -> Tuple[ConnectionRecord, ...]:
    """The held connections in their held connection, DERIVED at call time.

    Connections stand in the connection the book holds them -
    the connection their servers were discovered - optionally
    for one server alone. Nothing here is stored:
    the connection is the book's own held connection, told.
    """
    book = _source_book(source)
    connections = list(book.connections)
    if server_id is not None:
        wanted = _clean_text(server_id, "a server id")
        connections = [r for r in connections if r.server_id == wanted]
    return tuple(connections)

def trace_of(source: Any, connection_id: Any) -> str:
    """One connection's trace, DERIVED at call time.

    The connection's walked stages joined as one trace
    line, in walk connection. A connection that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is discovered
    elsewhere.
    """
    connection = _source_book(source).connection_for(connection_id)
    return " > ".join(connection.stages)

def trace_for_connection(source: Any,
                  connection_id: Any) -> Optional[TraceRecord]:
    """The held trace for one connection, or none - honestly."""
    wanted = _clean_text(connection_id, "a connection id")
    for record in _source_book(source).traces:
        if record.connection_id == wanted:
            return record
    return None

def trace_current(source: Any, connection_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_connection(source, connection_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, connection_id)

def note_for_connection(source: Any, connection_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one connection (and stance, when discovered)."""
    wanted = _clean_text(connection_id, "a connection id")
    for record in _source_book(source).notes:
        if record.connection_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the server targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def ledger_record(source: Any = None) -> Dict[str, Any]:
    """The connection ledger, DERIVED here from the held connections alone.

    The ledger counts the held connections by their
    derived completeness - green and red - names
    the current connection, the first that does not yet
    stand complete, tells each held connection's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held connections took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.connections
            if ("complete" if connection_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "connection_records": number})
    current = current_connection(book)
    traces = []
    for connection in book.connections:
        trace = trace_for_connection(book, connection.connection_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, connection.connection_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"connection_id": connection.connection_id, "trace": standing})
    return {
        "type": "connection_well",
        "server": CONNECTION_SLICE,
        "standings": standings,
        "total": len(book.connections),
        "current_connection": current.connection_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This server's own roadmap standing, proved from the roadmap itself.

    The record loads this server's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 servers in 11 parts,
    the discovered prefix, the next server where the
    connection connections, and M-233's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(CONNECTION_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "connection_roadmap",
        "server": CONNECTION_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m233_title": own.title,
        "m233_part": own.part,
        "m233_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: servers, connections, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or connection ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ConnectionBook:
    title: str
    servers: Tuple[ServerRef, ...] = ()
    connections: Tuple[ConnectionRecord, ...] = ()
    views: Tuple[ConnectionView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[ConnectionPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        servers = tuple(_check_server_ref(g) for g in self.servers)
        connections = tuple(_check_policy_ref(g) for g in self.connections)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        traces = tuple(_check_trace_ref(a) for a in self.traces)
        panels = tuple(_check_panel_ref(pn) for pn in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for ref in servers:
            if ref.server_id in seen_ids:
                raise ValueError(
                    f"two server references stand under id {ref.server_id!r}")
            if ref.seq in seen_seqs:
                raise ValueError(
                    f"two server references stand at sequence {ref.seq}")
            seen_ids.add(ref.server_id)
            seen_seqs.add(ref.seq)
        connection_ids = set()
        connection_seqs = set()
        for connection in connections:
            if connection.connection_id in connection_ids:
                raise ValueError(
                    f"two connections stand under id {connection.connection_id!r}")
            if connection.seq in connection_seqs:
                raise ValueError(
                    f"two connections stand at sequence {connection.seq}")
            connection_ids.add(connection.connection_id)
            connection_seqs.add(connection.seq)
        by_slice = {ref.server_id: ref for ref in servers}
        for connection in (connections if servers else ()):

            ref = by_slice.get(connection.server_id)
            if ref is None:
                raise ValueError(
                    f"connection {connection.connection_id!r} is held from server "
                    f"{connection.server_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "live":
                raise ValueError(
                    f"connection {connection.connection_id!r} is held from server "
                    f"{connection.server_id!r}, which is not active: "
                    f"no server is held from an queued server")
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
            target = (record.connection_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for connection "
                    f"{record.connection_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per connection target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_connections = set()
        connection_ids = {connection.connection_id for connection in connections}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.connection_id in trace_connections:
                raise ValueError(
                    f"two traces stand for connection "
                    f"{record.connection_id!r}: one trace stands "
                    f"per connection walk")
            if connections and record.connection_id not in connection_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces connection "
                    f"{record.connection_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_connections.add(record.connection_id)
        object.__setattr__(
            self, "servers", tuple(sorted(servers, key=lambda g: g.seq)))
        object.__setattr__(
            self, "connection_records", tuple(sorted(connections, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.connections + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.connection_id for g in self.connections) + tuple(
            v.view_id for v in self.views)

    def connection_ids(self) -> Tuple[str, ...]:
        return tuple(g.connection_id for g in self.connections)

    def server_ids(self) -> Tuple[str, ...]:
        return tuple(g.server_id for g in self.servers)

    def connection_for(self, connection_id: Any) -> ConnectionRecord:
        wanted = _clean_text(connection_id, "a connection id")
        for connection in self.connections:
            if connection.connection_id == wanted:
                return connection
        raise KeyError(f"no connection discovered {wanted!r} stands in this book")

    def slice_for(self, server_id: Any) -> ServerRef:
        wanted = _clean_text(server_id, "an server id")
        for ref in self.servers:
            if ref.server_id == wanted:
                return ref
        raise KeyError(f"no server discovered {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> ConnectionView:
        wanted = _clean_text(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view discovered {wanted!r} stands in this book")

    def note_for(self, note_id: Any) -> NoteRecord:
        wanted = _clean_text(note_id, "a stance id")
        for record in self.notes:
            if record.note_id == wanted:
                return record
        raise KeyError(f"no stance discovered {wanted!r} stands in this book")

    def trace_for(self, trace_id: Any) -> TraceRecord:
        wanted = _clean_text(trace_id, "an trace id")
        for record in self.traces:
            if record.trace_id == wanted:
                return record
        raise KeyError(f"no trace discovered {wanted!r} stands in this book")

    def item_for(self, item_id: Any) -> Any:
        wanted = _clean_text(item_id, "an item id")
        for connection in self.connections:
            if connection.connection_id == wanted:
                return connection
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item discovered {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "servers": [g.to_record() for g in self.servers],
            "connection_records": [g.to_record() for g in self.connections],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: ConnectionBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: ConnectionBook) -> None:
    if book.title != "MCP client at the M-233 slice run":
        raise ValueError("the shipped example book carries another title")
    if len(book.servers) != 3 or len(book.connections) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three server references, five connections and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-filesystem":
        raise ValueError("the pinned panel is panel-filesystem")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.stage for e in index.connections] != ["held", "held", "held"]:
        raise ValueError("the shipped example book index must derive the three held complete connections in held connection")
    if index.gaps != ("connection-bare-connection", "connection-leaping-connection"):
        raise ValueError("the shipped example book must leave the bare and leaping connections honestly open, discovered in its gaps")
    found = connection_for_check(book, EXAMPLE_STAGE)
    if found is None or found.connection_id != "connection-held-connection":
        raise ValueError("the shipped example book must reach its opening connection under the example stage")
    if trace_of(book, "connection-held-connection") != "discovered > inspected > permitted > connected > held":
        raise ValueError("the shipped example book must derive the opening connection's trace from its walked steps")
    if not trace_current(book, "connection-held-connection"):
        raise ValueError("the shipped example book must hold the opening connection's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note connection")

def validate_book(data: Any, *, require_example: bool = False) -> ConnectionBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, ConnectionBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a connection book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live server build or execution "
                f"({key!r} is discovered on it): {CONNECTION_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its connections under a view")
    if "connection_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held connections at call time")
    if "ledger" in data or "current_connection" in data:
        raise ValueError(
            "a book stores no ledger and no current connection: both are "
            "derived from its held connections at call time")
    if "trace" in data or "connection" in data:
        raise ValueError(
            "a book stores no trace and no connection: both are derived "
            "from its held connections at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != CONNECTION_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{CONNECTION_SCHEMA!r}")
    if data.get("server") is not None and (
            data["server"] != CONNECTION_SLICE):
        raise ValueError(
            f"a book's server must be {CONNECTION_SLICE!r}")
    head = data.get("connection_head") or data.get("mcp_client") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's connection head must be a mapping")
    title = head.get("title") or data.get("title")
    servers = tuple(build_server_ref(g) for g in data.get("servers") or ())
    connections = tuple(build_connection(g) for g in data.get("connection_records") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = ConnectionBook(
        title=title, servers=servers, connections=connections, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = ConnectionBook(
        title=book.title, servers=book.servers, connections=book.connections,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> ConnectionBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (ConnectionBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an ConnectionBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> ConnectionBook:
    return validate_book(data, require_example=require_example)


def load_connection(
        data: Optional[Dict[str, Any]] = None) -> ConnectionBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(CONNECTION_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_connection_file(path: Any) -> ConnectionBook:
    """Load one connection file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: server references, connections and views held one by one.
# ---------------------------------------------------------------------

class ConnectionRegistry:
    """An in-memory holding of server references, connections and views.

    The registry is the pure layer's model of a
    session's connection book: server references are
    held under their ids, connections are held under
    their ids, one connection per id and per sequence,
    and views are held in inspected connection, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[ServerRef] = []
        self._connections: List[ConnectionRecord] = []
        self._views: List[ConnectionView] = []
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

    def register_server_ref(self, item: Any) -> ServerRef:
        """Hold one server reference, permitted whole before held."""
        connected = _check_server_ref(item)
        return self._register(
            self._slices, connected, "server_id", "server reference")

    def register_connection(self, item: Any) -> ConnectionRecord:
        """Hold one connection, permitted whole before held."""
        connected = _check_policy_ref(item)
        return self._register(
            self._connections, connected, "connection_id", "connection")

    def register_view(self, view: Any) -> ConnectionView:
        """Hold one view; a view naming no id takes a fresh one."""
        connected = _check_view_ref(view)
        if not connected.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            connected = build_view({**connected.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, connected, "view_id", "view")

    def register_book(self, book: Any) -> ConnectionBook:
        """Hold a whole book's records, under its title."""
        connected = build_book(book)
        if self._title is not None and connected.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {connected.title!r}")
        for ref in connected.servers:
            self.register_server_ref(ref)
        for connection in connected.connections:
            self.register_connection(connection)
        for view in connected.views:
            self.register_view(view)
        self._title = connected.title
        return self.book()

    def book(self) -> ConnectionBook:
        return ConnectionBook(
            title=self._title or "An unheld connection book",
            servers=tuple(self._slices), connections=tuple(self._connections),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[ServerRef, ...]:
        return tuple(self._slices)

    def list_connections(self) -> Tuple[ConnectionRecord, ...]:
        return tuple(self._connections)

    def list_views(self) -> Tuple[ConnectionView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._connections) + tuple(self._views)

    def get_slice(self, server_id: Any) -> ServerRef:
        return self.book().slice_for(server_id)

    def get_connection(self, connection_id: Any) -> ConnectionRecord:
        return self.book().connection_for(connection_id)

    def get_view(self, view_id: Any) -> ConnectionView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the ledger target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> ConnectionBook:
    if source is None:
        return load_connection()
    if isinstance(source, ConnectionBook):
        return source
    if isinstance(source, ConnectionRegistry):
        return source.book()
    return build_book(source)


def _heldance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _HELDANCE}


def connection_record(connection: Any, source: Any = None) -> Dict[str, Any]:
    connected = _check_policy_ref(connection)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "connection_connection",
        "server": CONNECTION_SLICE,
        "connection_id": connected.connection_id,
        "server_id": connected.server_id,
        "title": connected.title,
        "segment": segment_of(connected, book),
        "complete": connection_green(connected, book),
        "gaps": list(connection_gaps(connected, book)),
    }
    record.update(_heldance_record(connected))
    return record


def server_record(ref: Any) -> Dict[str, Any]:
    connected = _check_server_ref(ref)
    record = {
        "type": "connection_run",
        "server": CONNECTION_SLICE,
        "server_id": connected.server_id,
        "title": connected.title,
        "state": connected.state, "permission": connected.permission,
    }
    record.update(_heldance_record(connected))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    connected = _check_trace_ref(record_in)
    record = {
        "type": "connection_trace",
        "server": CONNECTION_SLICE,
        "trace_id": connected.trace_id,
        "connection_id": connected.connection_id,
        "trace": connected.trace,
    }
    record.update(_heldance_record(connected))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    connected = _check_view_ref(view)
    record = {
        "type": "connection_view",
        "server": CONNECTION_SLICE,
        "view_id": connected.view_id, "seq": connected.seq,
        "view_filter": connected.view_filter,
    }
    record.update(_heldance_record(connected))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    connected = _check_note_ref(record_in)
    record = {
        "type": "connection_note",
        "server": CONNECTION_SLICE,
        "note_id": connected.note_id,
        "connection_id": connected.connection_id,
        "stance": connected.stance,
    }
    record.update(_heldance_record(connected))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    connected = validate_panel(panel, source)
    record = {"type": "connection_panel",
              "server": CONNECTION_SLICE}
    record.update(connected.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, ConnectionVerdict):
        connected = validate_verdict(verdict, source)
    else:
        connected = derive_verdict(_source_book(verdict), view)
    record = {"type": "connection_verdict",
              "server": CONNECTION_SLICE}
    record.update(connected.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, ConnectionIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "connection_index",
              "server": CONNECTION_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    connected = _source_book(book)
    record = {"type": "connection_book",
              "server": CONNECTION_SLICE,
              "title": connected.title}
    record.update(connected.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(connection: Any, source: Any = None) -> str:
    connected = _check_policy_ref(connection)
    return (
        f"{connected.title} - from {connected.server_id}: "
        f"stage {connected.stage if connected.stage else 'none'}, "
        f"claims "
        f"{', '.join(connected.claims) if connected.claims else 'none'}. "
        f"{connected.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The connections stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"connections stand complete.")


def view_plain_words(view: Any) -> str:
    connected = _check_view_ref(view)
    return f"View {connected.view_id}: shows {connected.view_filter} connections."


def note_plain_words(record_in: Any) -> str:
    connected = _check_note_ref(record_in)
    return (
        f"Note {connected.note_id}: {connected.stance} "
        f"{connected.connection_id}, toward {connected.target}. "
        f"{connected.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, ConnectionIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.connections)} green connections; "
        f"red, discovered in its gaps: {gaps}.")

def format_connection(connection: Any, source: Any = None) -> str:
    connected = _check_policy_ref(connection)
    book = _source_book(source) if source is not None else None
    lines = [f"{connected.title} ({connected.connection_id})"]
    lines.extend(plain_lines(connected))
    lines.append(connected.detail)
    if connection_green(connected, book):
        lines.append(
            "This connection stands complete - it walked the question "
            "sequence in the open from discovered to held, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This connection stands open - it stands discovered in "
            f"its gaps: {', '.join(connection_gaps(connected, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    connected = _check_view_ref(view)
    return (
        f"View {connected.view_id}: filter {connected.view_filter} - "
        f"{connected.detail}")


def format_note(record_in: Any) -> str:
    connected = _check_note_ref(record_in)
    lines = [
        f"Connection note {connected.stance} {connected.connection_id} "
        f"({connected.note_id}): {connected.title}. {connected.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or connection it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_stage(source: Any, stage: Any) -> str:
    connection = connection_for_check(source, stage)
    if connection is not None:
        return format_connection(connection, source)
    wanted = stage.strip() if isinstance(stage, str) else stage
    return (
        f"No held connection stands under stage {wanted!r} yet - the "
        f"stage reaches nothing in this book, and no connection is "
        f"invented for it.")


def format_book(source: Any = None, server_id: Any = None) -> str:
    book = _source_book(source)
    connections = (connections_for_server(book, server_id)
              if server_id is not None else book.connections)
    lines = [f"The MCP Client (M-233) - {book.title}"]
    lines.extend(segment_of(connection, book) for connection in connections)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Connection panel under view {panel.view_id}:"]
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
    lines = ["Connection index, derived from the held connections:"]
    for connection in index.connections:
        lines.append(f"{connection.stage} - {connection.title} ({connection.connection_id})")
    if index.gaps:
        lines.append(
            "Red, discovered honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_connection_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The MCP Client (M-233)",
        f"{book.title}: {len(book.connections)} connections held, "
        f"{len(green_connections(book))} connections standing green, "
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


def parse_connection_args(args: Any) -> Tuple[str, Any]:
    """Parse the /connection grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("connection", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("stage", "server"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
