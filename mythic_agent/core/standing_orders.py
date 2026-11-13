"""Standing orders (roadmap slice M-226).

Part IX - The Mythic Method Engine. The roadmap
words: **slice orders classified (code, test, environment, provider, scope) with the remedy each class has earned historically — the loop learns its own weather..*

What already ships, and what this campaign adds:

* The orders book already ships as data
  (M-201, ``core/milestones.py``): a roadmap/order
  file (parts, campaigns, acceptance stages, state) the
  app reads. This campaign WIRES the book that book's
  book invites - several orders held across
  campaigns with one ledger over them - as data, in its
  own module, standing in the M-195 copy-and-share
  book book the M-226 book stands in: one taxonomist
  per book, and the taxonomist's charge over one
  order across its campaign held as a book - a
  order. The shipped orders stand untouched behind
  their seams: this layer holds orders as data
  over the book's campaigns and rewrites none of them,
  and the orders book keeps its own standing.
  Orders stand on the ledger AS DATA alone: a
  order carries a ledger ref, a reference held in
  this book; holding, viewing or telling a order
  campaigns no order live, moves no keeper and files
  nothing.
* No charter row names this campaign: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-226 on no row, and the
  campaign tests pin that absence live. The M-005
  method charter names no campaign row either: its
  own words name the whole of Part IX as the
  part that executes the charter, and this campaign
  is built to the roadmap words and that
  execution note together.

* A order is held whole: the campaign it
  answers for, named by its campaign id; its title;
  the order steps it walked, held as data in
  walk order; and the evidence it carries, held
  as data by campaign. The order walk is EXPLICIT:
  its sequence stands as data
  (:data:`STAGES`, :data:`TRANSITIONS`) -
  stated, recorded, bound, honoured, kept -
  and a order's standing is DERIVED at
  call time from its held steps and evidence
  alone: a order that opens anywhere but
  stated, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet stated kept stands
  open, named in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - word_ref,
  book_ref, campaign_ref, proof_ref, order_ref, evidence
  a lawkeeper can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A order is
  honoured from held evidence alone, never
  from a feeling: a order holding a
  bare claim stands open, named in its gaps.
* A order stands only for an ACTIVE
  campaign. The book holds each campaign it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  order naming a campaign that stands
  nowhere in the book refuses BY NAME, and a
  order for a campaign that is not active
  refuses BY NAME beside it: the taxonomist deals with
  the campaign in hand, in roadmap order, never a
  queued one, and a campaign whose order already
  stands complete is never bound twice - the
  current order is derived, so a
  completed campaign is never the current order
  twice.
* The order's trace is visible. A trace
  record holds one order's walked steps
  as one trace line, exactly as walked, beside
  the order. The derived trace is
  computed at call time from the order's
  held steps; a held trace that no longer agrees
  with it stands stale, named in the ledger - the
  trace is the walk itself, never a retelling
  of it.
* The order index is DERIVED at call
  time from the held orders - one order
  per complete order, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, order or current-order
  claim on any record refuses by name.
* The current order is DERIVED at call
  time - the first held order, in held
  order, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its order, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per order stance; holding
  a note posts none of it, the rule stands as
  data (:data:`ORDER_RULE`), and a record
  claiming a order was actually kept,
  captured or promoted live refuses BY NAME.
  The taxonomist orders - and those orders, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the book a real order
  file takes, a loader reads a file anywhere on
  disk, orders and views are recorded as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a order book for a session and
  telling from it. This layer reaches no live
  order: it writes no order live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no taxonomist, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds orders
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The order walk is explicit.** A
  order is honoured against the held
  steps and legal steps alone; an illegal step
  stands named in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  order that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, named in its gaps:
  a order is honoured from evidence, not
  vibes.
* **Active campaigns only, in roadmap order.** A
  order for a missing or queued campaign
  refuses by name; no order is invented
  for a campaign the taxonomist has not recorded with.
* **Unknown stays unknown.** A order
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, order
  and current order are derived, never
  stored.** Each is derived from the held
  orders at call time; a stored one
  refuses by name, so it can never drift.
* **One order per order.** Two
  orders standing for one order id
  refuse by name, and one note record stands per
  order stance.
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
    "ORDER_RESOURCE",
    "ORDER_SCHEMA",
    "ORDER_SLICE",
    "ORDER_RULE",
    "PLAIN_EXPLANATION",
    "THE_ORDER_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "COMPLETE_WORDS",
    "CAMPAIGN_STATES",
    "Any",
    "Dict",
    "List",
    "Optional",
    "TraceRecord",
    "OrderRecord",
    "IndexOrder",
    "CampaignRef",
    "NoteRecord",
    "OrderBook",
    "OrderIndex",
    "OrderPanel",
    "OrderPanelRow",
    "OrderRegistry",
    "OrderVerdict",
    "OrderView",
    "TargetCount",
    "trace_for_order",
    "trace_record",
    "ledger_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_order",
    "build_campaign_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_order",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "order_for_check",
    "order_order",
    "order_record",
    "first_note",
    "format_book",
    "format_order",
    "format_index",
    "format_note",
    "format_stage",
    "format_panel",
    "format_order_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "campaign_record",
    "load_order",
    "load_order_file",
    "normalize_campaign_state",
    "normalize_stage",
    "normalize_claim_kind",
    "legal_step",
    "next_stage",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_order",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_order_args",
    "green_orders",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_orders",
    "validate_trace",
    "validate_book",
    "validate_order",
    "validate_campaign_ref",
    "validate_note",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
    "order_gaps",
    "order_green",
    "orders_for_campaign",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

ORDER_SCHEMA = "mythic.standing_orders/1"
ORDER_SLICE = "M-226"
THE_ORDER_SLICE = ORDER_SLICE
ORDER_RESOURCE = "standing_orders.yaml"
INDEX_ACTION = "index"
EXAMPLE_STAGE = "kept"
STAGE_FIELDS = ("stages", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("kept", "held", "blocked")
CAMPAIGN_STATES = ("live", "dormant")
ORDER_RULE = 'orders are held as data alone: several orders across campaigns stand with one ledger, lawkeepers per order, and the human sees the whole forge at a campaign - an order stands as data, held by reference (an order ref), never taken live - the order walk stands as an explicit order sequence - stated, recorded, bound, honoured, kept - and an order completes only complete, complete being a state with evidence held - word ref, book ref, campaign ref, proof ref, order ref - never a feeling, a memory, an assertion or a summary; user-level laws are stored once and binding every campaign, and the app keeps the user laws so the user need never repeat them; holding, viewing and reading an order runs no law live, approves nothing, spends nothing, spawns no process and opens no network'
PLAIN_EXPLANATION = 'Standing orders (M-226): user-level laws (no-Docker, README guardian, manual-only workflows, keeper law) stored once and binding every campaign.'
USAGE = 'Usage: /orders | /orders order <order-id> | /orders stage <stage> | /orders campaign <campaign-id> | /orders view <view-id> | /orders note <note-id> | /orders index | /orders panel | /orders verdict'

STAGES = ("stated", "recorded", "bound", "honoured", "kept")
HELD_EVIDENCE = ("word_ref", "book_ref", "campaign_ref", "proof_ref", "order_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "stated": ("recorded",),
    "recorded": ("bound",),
    "bound": ("honoured",),
    "honoured": ("stated", "kept"),
    "kept": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a order or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a order stands complete.
    A stage outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_stage(stage: Any, failed: Any = False) -> Optional[str]:
    """The step the taxonomist takes next, DERIVED from the sequence.

    Banked leads to recorded and recorded to
    bound; bound leads to honoured; at
    honoured a follow-up banking steps back to stated and a finished order steps to kept;
    kept is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    honoured = normalize_stage(stage)
    if honoured == "stated":
        return "recorded"
    if honoured == "recorded":
        return "bound"
    if honoured == "bound":
        return "honoured"
    if honoured == "honoured":
        return "stated" if failed else "kept"
    return None


_KEPTANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "order_id", "seq", "campaign_id", "title", "stages",
    "claims", "detail",
} | set(_KEPTANCE))
_SLICE_REF_KEYS = frozenset({
    "campaign_id", "seq", "title", "state", "detail",
} | set(_KEPTANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "order_id", "trace", "detail",
} | set(_KEPTANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_KEPTANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "order_id", "stance", "target", "title",
    "detail",
} | set(_KEPTANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "orders", "coverage", "covered", "uncovered",
    "current_order", "next_order", "progress", "ledger",
    "current", "order", "breaks", "live"})
_LIVE_KEYS = (
    "live_order", "orders_live", "live_question",
    "orders_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "orders_live",
    "resumed_live", "runs_order", "paused_live",
    "runs_order", "ran_order", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "order_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_order", "sent_order",
    "posts_note", "posted_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_order", "filed_live", "spawns_taxonomist", "spawned_taxonomist", "sends_order", "sent_order", "writes_order", "wrote_order")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_stages(value: Any) -> Tuple[str, ...]:
    """A order's walked stages, held as data.

    The stages stand as a list of stage names in
    walk order, each one a stage of the explicit
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
    """A order's asked claims: claim campaigns named as data.

    Each claim names one campaign from the kept
    vocabulary - the human campaigns the gate may ask
    and the code campaigns it must never ask, both
    held honestly as data - and a campaign outside
    the vocabulary refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("claims must be a list of claim campaigns")
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


def _keptance(mapping: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key in _KEPTANCE:
        if key == "recorded_on":
            out[key] = _clean_text(mapping.get(key), "a recorded_on campaign")
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
                f"{what} claims a live gate order or campaign build "
                f"execution ({key!r} is named on it): "
                f"{ORDER_RULE}")
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


def normalize_campaign_state(value: Any) -> str:
    state = _clean_text(value, "an campaign state").lower()
    if state not in CAMPAIGN_STATES:
        raise ValueError(
            f"campaign state {state!r} is not one of the held "
            f"states: " + ", ".join(CAMPAIGN_STATES))
    return state


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
    campaign = _clean_text(value, "a claim campaign").lower()
    if campaign not in CLAIM_KINDS:
        raise ValueError(
            f"claim campaign {campaign!r} is not one of the held "
            f"campaigns: " + ", ".join(CLAIM_KINDS))
    return campaign

# ---------------------------------------------------------------------
# The held order: one campaign cut from an active campaign.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class OrderRecord:
    """One order campaign, held as data.

    The order names the active campaign it was
    held from, by campaign id, its title, its
    verifiable stages, held as data, and its
    claims, named by order id. The grain is
    derived, never stored: exactly one verifiable
    walk is bound against the machine. A order whose
    stages are not yet held stands with its
    stages empty: it stands open, named in
    its gaps, and no stage is invented for it.
    The order is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    order_id: str
    seq: int
    campaign_id: str
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
            self, "order_id", _clean_text(self.order_id, "a order id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "campaign_id", _clean_text(self.campaign_id, "an campaign id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a order title"))
        object.__setattr__(
            self, "stages", _check_stages(self.stages))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a order detail"))
        for key in _KEPTANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.order_id

    @property
    def stage(self) -> str:
        """The stage the order stands at: its last walked stage."""
        return self.stages[-1] if self.stages else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "order_id": self.order_id, "seq": self.seq,
            "campaign_id": self.campaign_id, "title": self.title,
            "stages": list(self.stages),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _KEPTANCE:
            record[key] = getattr(self, key)
        return record


def _check_order_ref(value: Any) -> OrderRecord:
    if not isinstance(value, OrderRecord):
        raise ValueError("a order must be a OrderRecord")
    return value


def validate_order(order: Any) -> OrderRecord:
    return _check_order_ref(order)


def build_order(record: Any = None, **kwargs: Any) -> OrderRecord:
    """Build one held order from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, OrderRecord):
        if kwargs:
            raise ValueError("a order stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a order must be a mapping or a OrderRecord")
    _needed(data, _RUN_KEYS, "a order")
    return OrderRecord(
        order_id=data.get("order_id"), seq=data.get("seq"),
        campaign_id=data.get("campaign_id"), title=data.get("title"),
        stages=data.get("stages"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_keptance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each order to the steps it took outside the machine.

    Derived from the held orders alone: a break is
    one consecutive pair of walked stages the
    explicit gate sequence does not allow, told
    in walk order as before, then after.
    """
    found: Dict[str, Tuple[str, ...]] = {}
    for order in book.orders:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(order.stages, order.stages[1:])
            if not legal_step(before, after))
        if breaks:
            found[order.order_id] = breaks
    return found

def order_gaps(order: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a order from standing complete.

    Guarded from the order's own held fields alone -
    its walked steps against the explicit question
    sequence, and its kept evidence against the
    kept vocabulary: the order opens at
    named, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a order stands complete only when it has
    stated kept. The source names nothing
    further: no gap is borrowed from another
    order.
    """
    honoured = _check_order_ref(order)
    gaps: List[str] = []
    if not honoured.stages:
        gaps.append(
            "has passed through no step: the order has not started")
        return tuple(gaps)
    if honoured.stages[0] != "stated":
        gaps.append(
            f"opens at {honoured.stages[0]}, not at stated: "
            f"the order opens with the reflection")
    for before, after in zip(honoured.stages, honoured.stages[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"order sequence does not allow")
    for campaign in honoured.claims:
        if campaign in BARE_CLAIMS:
            gaps.append(
                f"carries a {campaign} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if honoured.stages[-1] != "kept":
        gaps.append(
            f"has not reached kept: the order stands "
            f"at {honoured.stages[-1]}")
    return tuple(gaps)

def order_green(order: Any, source: Any = None) -> bool:
    return not order_gaps(order, source)


def plain_lines(order: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the order's own fields."""
    honoured = _check_order_ref(order)
    return (
        f"Order: {honoured.title}",
        f"Campaign: {honoured.campaign_id}",
        f"Stage: {honoured.stage if honoured.stage else 'none'}",
        f"Claims: "
        f"{', '.join(honoured.claims) if honoured.claims else 'none'}",
    )


def segment_of(order: Any, source: Any = None) -> str:
    honoured = _check_order_ref(order)
    gaps = order_gaps(honoured, source)
    return (
        f"{honoured.order_id}: {honoured.title} - campaign: "
        f"'{honoured.campaign_id}' - stage: "
        f"'{honoured.stage if honoured.stage else 'none'}' - "
        f"stages: {len(honoured.stages)} - claims: "
        f"'{', '.join(honoured.claims) if honoured.claims else 'none'}' - "
        f"detail: '{honoured.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held campaign reference: the active campaign a book orders from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CampaignRef:
    """One campaign a order book orders from, held as a reference.

    The record names the campaign, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 campaign book's own telling. A order
    stands only from an active reference: the
    book refuses a order naming no held reference,
    and a order from an queued one, BY NAME.
    """

    campaign_id: str
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
            self, "campaign_id", _clean_text(self.campaign_id, "an campaign id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(
            self, "state", normalize_campaign_state(self.state))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an campaign detail"))
        for key in _KEPTANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.campaign_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "campaign_id": self.campaign_id, "seq": self.seq,
            "title": self.title, "state": self.state,
            "detail": self.detail,
        }
        for key in _KEPTANCE:
            record[key] = getattr(self, key)
        return record


def _check_campaign_ref(value: Any) -> CampaignRef:
    if not isinstance(value, CampaignRef):
        raise ValueError("a campaign reference must be an CampaignRef")
    return value


def validate_campaign_ref(ref: Any) -> CampaignRef:
    return _check_campaign_ref(ref)


def build_campaign_ref(record: Any = None, **kwargs: Any) -> CampaignRef:
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, CampaignRef):
        if kwargs:
            raise ValueError(
                "a campaign reference stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError(
            "a campaign reference must be a mapping or an CampaignRef")
    _needed(data, _SLICE_REF_KEYS, "a campaign reference")
    return CampaignRef(
        campaign_id=data.get("campaign_id"), seq=data.get("seq"),
        title=data.get("title"), state=data.get("state"),
        detail=data.get("detail"),
        **_keptance(data))


# ---------------------------------------------------------------------
# The held trace trace: the human approves the trace, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TraceRecord:
    """One trace trace, held as data.

    The record names its campaign and the trace the
    human active - the campaign's order ids in
    derived claim order, held exactly as
    active. The trace is of the set and its
    order, never of a step: when the derived
    trace moves, this record stands stale, named
    in the ledger, until a new trace is active.
    """

    trace_id: str
    seq: int
    order_id: str
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
            self, "order_id", _clean_text(self.order_id, "an campaign id"))
        object.__setattr__(
            self, "trace", _clean_text(self.trace, "an active trace"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an trace detail"))
        for key in _KEPTANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.trace_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "trace_id": self.trace_id, "seq": self.seq,
            "order_id": self.order_id, "trace": self.trace,
            "detail": self.detail,
        }
        for key in _KEPTANCE:
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
        order_id=data.get("order_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_keptance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a order, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One order stance, held as data.

    The record names its order, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per order stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    order_id: str
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
            self, "order_id", _clean_text(self.order_id, "a order id"))
        object.__setattr__(self, "stance", normalize_stance(self.stance))
        object.__setattr__(
            self, "target", _clean_text(self.target, "a stance target"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a stance title"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a stance detail"))
        for key in _KEPTANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.note_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "note_id": self.note_id, "seq": self.seq,
            "order_id": self.order_id, "stance": self.stance,
            "target": self.target, "title": self.title,
            "detail": self.detail,
        }
        for key in _KEPTANCE:
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
        order_id=data.get("order_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_keptance(data))


# ---------------------------------------------------------------------
# The held view: which campaigns a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class OrderView:
    """A view over the book: every order, the green, the rest."""

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
        for key in _KEPTANCE:
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
        for key in _KEPTANCE:
            record[key] = getattr(self, key)
        return record


def _check_view_ref(value: Any) -> OrderView:
    if not isinstance(value, OrderView):
        raise ValueError("a view must be an OrderView")
    return value


def validate_view(view: Any) -> OrderView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> OrderView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, OrderView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an OrderView")
    _needed(data, _VIEW_KEYS, "a view")
    return OrderView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_keptance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class OrderPanelRow:
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


def _row_for_order(order: OrderRecord,
                     source: Any = None) -> OrderPanelRow:
    return OrderPanelRow(
        item_id=order.order_id,
        standing="complete" if order_green(order, source) else "open",
        label=order.title, segment=segment_of(order, source),
        recorded_on=order.recorded_on)


def _check_row_ref(value: Any) -> OrderPanelRow:
    if not isinstance(value, OrderPanelRow):
        raise ValueError("a panel row must be an OrderPanelRow")
    return value


def validate_row(row: Any, order: Any = None,
                 source: Any = None) -> OrderPanelRow:
    honoured = _check_row_ref(row)
    if order is not None:
        derived = _row_for_order(_check_order_ref(order), source)
        if honoured != derived:
            raise ValueError(
                f"panel row {honoured.item_id!r} does not agree with "
                f"the row derived from its order")
    return honoured


def build_row(row: Any = None, order: Any = None,
              source: Any = None,
              **kwargs: Any) -> OrderPanelRow:
    if order is not None:
        derived = _row_for_order(_check_order_ref(order), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            OrderPanelRow(**kwargs))
        return validate_row(built, order, source)
    if isinstance(row, OrderPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return OrderPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on campaign"))
    if row is None and kwargs:
        return OrderPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an OrderPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[OrderPanelRow, ...]
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
        f"The order book holds {total_items} orders as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown orders "
        f"stand complete.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its order's own fields "
        "- the campaign it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any order.",
        "Completeness is bound from the held records alone: "
        "a order that steps outside the order sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not stated kept stands open, named in its "
        "gaps, and the order index is derived from the "
        "held orders, never stored where it could drift.",
    )

@dataclass(frozen=True)
class OrderPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[OrderPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> OrderView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, OrderView):
        return view
    return book.view_for(view)


def shown_orders(source: Any, view: Any = None
                   ) -> Tuple[OrderRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.orders
    if resolved.view_filter == "complete":
        return tuple(g for g in book.orders if order_green(g, book))
    return tuple(g for g in book.orders if not order_green(g, book))


def orders_for_campaign(source: Any, campaign_id: Any
                      ) -> Tuple[OrderRecord, ...]:
    wanted = _clean_text(campaign_id, "an campaign id")
    return tuple(
        g for g in _source_book(source).orders if g.campaign_id == wanted)


def green_orders(source: Any) -> Tuple[OrderRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.orders if order_green(g, book))


def current_order(source: Any) -> Optional[OrderRecord]:
    """The book's current order, DERIVED at call time.

    The first held order, in held order, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held orders alone, so it can
    never go stale against them. A book whose every
    order stands complete has no current order.
    """
    book = _source_book(source)
    for order in book.orders:
        if not order_green(order, book):
            return order
    return None


def derive_panel(source: Any, view: Any = None) -> OrderPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_orders(book, resolved)
    rows = tuple(_row_for_order(order, book) for order in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.orders), default="")
    green = sum(1 for g in shown if order_green(g, book))
    return OrderPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.orders), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.orders), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> OrderPanel:
    if not isinstance(value, OrderPanel):
        raise ValueError("a panel must be an OrderPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> OrderPanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 order).
    """
    honoured = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(honoured.view_id)
                if honoured.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(honoured, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {honoured.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return honoured


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> OrderPanel:
    if isinstance(panel, OrderPanel):
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
        built = OrderPanel(
            panel_id=_clean_text(data.get("panel_id"), "a panel id"),
            view_id=data.get("view_id"),
            view_filter=normalize_view_filter(data.get("view_filter")),
            rows=rows,
            total_items=_check_count(
                data.get("total_items"), "a total_items count"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            target_counts=counts,
            as_of=_clean_text(data.get("as_of"), "an as_of campaign"),
            account=_check_lines(data.get("account"), "the account"))
        return validate_panel(built, source)
    if panel is None and source is not None:
        return derive_panel(source, kwargs.get("view"))
    raise ValueError("a panel must be a mapping, an OrderPanel, or derived")


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
        return "kept"
    if green_shown == 0:
        return "blocked"
    return "held"


@dataclass(frozen=True)
class OrderVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> OrderVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_orders(book, resolved)
    green = sum(1 for g in shown if order_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return OrderVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> OrderVerdict:
    if not isinstance(value, OrderVerdict):
        raise ValueError("a verdict must be an OrderVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> OrderVerdict:
    honoured = _check_verdict_ref(verdict)
    if honoured.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {honoured.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(honoured.view_id)
                if honoured.view_id is not None else None)
        derived = derive_verdict(book, view)
        if honoured != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return honoured


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> OrderVerdict:
    if isinstance(verdict, OrderVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = OrderVerdict(
            verdict=_clean_text(data.get("verdict"), "a verdict"),
            view_id=data.get("view_id"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            green_shown=_check_count(
                data.get("green_shown"), "a green_shown count"),
            latest_on=_clean_text(data.get("latest_on"), "a latest campaign"))
        return validate_verdict(built, source)
    if verdict is None and source is not None:
        return derive_verdict(source, kwargs.get("view"))
    raise ValueError(
        "a verdict must be a mapping, an OrderVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held campaigns' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexOrder:
    stage: str
    order_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "stage": self.stage, "order_id": self.order_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class OrderIndex:
    """The order index, derived from the held orders.

    The index names one order per green order, in
    held order - the order's own one verifiable
    stage, its order id and its title - and the
    orders that do not stand complete, named in its
    gaps. Nothing here is stored on any order: the
    index is derived at call time from the held
    records alone, so it can never drift from them.
    """

    orders: Tuple[IndexOrder, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "orders": [e.to_record() for e in self.orders],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> OrderIndex:
    """Derive the order index from the book's held orders."""
    book = _source_book(source)
    orders = tuple(
        IndexOrder(stage=g.stage, order_id=g.order_id,
                   title=g.title)
        for g in book.orders if order_green(g, book))
    gaps = tuple(
        g.order_id for g in book.orders if not order_green(g, book))
    return OrderIndex(orders=orders, gaps=gaps)


def order_for_check(source: Any, stage: Any) -> Optional[OrderRecord]:
    """The first held order one stage reaches, or none - honestly."""
    if stage is None:
        return None
    if not isinstance(stage, str):
        raise ValueError("an stage must be a string naming the stage")
    wanted = stage.strip()
    if not wanted:
        return None
    for order in _source_book(source).orders:
        if order.stage == wanted:
            return order
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held order: the order
    that took it and the step it took, before,
    then after. A book whose orders all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{order_id}: {step}"
        for order_id, steps in _breaks_map(book).items()
        for step in steps)

def order_order(source: Any,
              campaign_id: Any = None) -> Tuple[OrderRecord, ...]:
    """The held orders in their held order, DERIVED at call time.

    Orders stand in the order the book holds them -
    the order their campaigns were taken - optionally
    for one campaign alone. Nothing here is stored:
    the order is the book's own held order, told.
    """
    book = _source_book(source)
    orders = list(book.orders)
    if campaign_id is not None:
        wanted = _clean_text(campaign_id, "a campaign id")
        orders = [r for r in orders if r.campaign_id == wanted]
    return tuple(orders)

def trace_of(source: Any, order_id: Any) -> str:
    """One order's trace, DERIVED at call time.

    The order's walked stages joined as one trace
    line, in walk order. A order that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is named
    elsewhere.
    """
    order = _source_book(source).order_for(order_id)
    return " > ".join(order.stages)

def trace_for_order(source: Any,
                  order_id: Any) -> Optional[TraceRecord]:
    """The held trace for one order, or none - honestly."""
    wanted = _clean_text(order_id, "a order id")
    for record in _source_book(source).traces:
        if record.order_id == wanted:
            return record
    return None

def trace_current(source: Any, order_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_order(source, order_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, order_id)

def note_for_order(source: Any, order_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one order (and stance, when named)."""
    wanted = _clean_text(order_id, "a order id")
    for record in _source_book(source).notes:
        if record.order_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the campaign targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def ledger_record(source: Any = None) -> Dict[str, Any]:
    """The order ledger, DERIVED here from the held orders alone.

    The ledger counts the held orders by their
    derived completeness - green and red - names
    the current order, the first that does not yet
    stand complete, tells each held order's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held orders took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.orders
            if ("complete" if order_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "order_records": number})
    current = current_order(book)
    traces = []
    for order in book.orders:
        trace = trace_for_order(book, order.order_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, order.order_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"order_id": order.order_id, "trace": standing})
    return {
        "type": "order_well",
        "campaign": ORDER_SLICE,
        "standings": standings,
        "total": len(book.orders),
        "current_order": current.order_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This campaign's own roadmap standing, proved from the roadmap itself.

    The record loads this campaign's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 campaigns in 11 parts,
    the stated prefix, the next campaign where the
    order orders, and M-226's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(ORDER_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "order_roadmap",
        "campaign": ORDER_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m226_title": own.title,
        "m226_part": own.part,
        "m226_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: campaigns, orders, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or order ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class OrderBook:
    title: str
    campaigns: Tuple[CampaignRef, ...] = ()
    orders: Tuple[OrderRecord, ...] = ()
    views: Tuple[OrderView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[OrderPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        campaigns = tuple(_check_campaign_ref(g) for g in self.campaigns)
        orders = tuple(_check_order_ref(g) for g in self.orders)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        traces = tuple(_check_trace_ref(a) for a in self.traces)
        panels = tuple(_check_panel_ref(pn) for pn in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for ref in campaigns:
            if ref.campaign_id in seen_ids:
                raise ValueError(
                    f"two campaign references stand under id {ref.campaign_id!r}")
            if ref.seq in seen_seqs:
                raise ValueError(
                    f"two campaign references stand at sequence {ref.seq}")
            seen_ids.add(ref.campaign_id)
            seen_seqs.add(ref.seq)
        order_ids = set()
        order_seqs = set()
        for order in orders:
            if order.order_id in order_ids:
                raise ValueError(
                    f"two orders stand under id {order.order_id!r}")
            if order.seq in order_seqs:
                raise ValueError(
                    f"two orders stand at sequence {order.seq}")
            order_ids.add(order.order_id)
            order_seqs.add(order.seq)
        by_slice = {ref.campaign_id: ref for ref in campaigns}
        for order in (orders if campaigns else ()):

            ref = by_slice.get(order.campaign_id)
            if ref is None:
                raise ValueError(
                    f"order {order.order_id!r} is held from campaign "
                    f"{order.campaign_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "live":
                raise ValueError(
                    f"order {order.order_id!r} is held from campaign "
                    f"{order.campaign_id!r}, which is not active: "
                    f"no campaign is held from an queued campaign")
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
            target = (record.order_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for order "
                    f"{record.order_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per order target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_orders = set()
        order_ids = {order.order_id for order in orders}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.order_id in trace_orders:
                raise ValueError(
                    f"two traces stand for order "
                    f"{record.order_id!r}: one trace stands "
                    f"per order walk")
            if orders and record.order_id not in order_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces order "
                    f"{record.order_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_orders.add(record.order_id)
        object.__setattr__(
            self, "campaigns", tuple(sorted(campaigns, key=lambda g: g.seq)))
        object.__setattr__(
            self, "order_records", tuple(sorted(orders, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.orders + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.order_id for g in self.orders) + tuple(
            v.view_id for v in self.views)

    def order_ids(self) -> Tuple[str, ...]:
        return tuple(g.order_id for g in self.orders)

    def campaign_ids(self) -> Tuple[str, ...]:
        return tuple(g.campaign_id for g in self.campaigns)

    def order_for(self, order_id: Any) -> OrderRecord:
        wanted = _clean_text(order_id, "a order id")
        for order in self.orders:
            if order.order_id == wanted:
                return order
        raise KeyError(f"no order named {wanted!r} stands in this book")

    def slice_for(self, campaign_id: Any) -> CampaignRef:
        wanted = _clean_text(campaign_id, "an campaign id")
        for ref in self.campaigns:
            if ref.campaign_id == wanted:
                return ref
        raise KeyError(f"no campaign named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> OrderView:
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
        for order in self.orders:
            if order.order_id == wanted:
                return order
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "campaigns": [g.to_record() for g in self.campaigns],
            "order_records": [g.to_record() for g in self.orders],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: OrderBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: OrderBook) -> None:
    if book.title != "Standing orders at the M-226 slice run":
        raise ValueError("the shipped example book carries another title")
    if len(book.campaigns) != 3 or len(book.orders) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three campaign references, five orders and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m225-campaign":
        raise ValueError("the pinned panel is panel-m225-campaign")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.stage for e in index.orders] != ["kept", "kept", "kept"]:
        raise ValueError("the shipped example book index must derive the three held complete orders in held order")
    if index.gaps != ("order-bare-order", "order-leaping-order"):
        raise ValueError("the shipped example book must leave the bare and leaping orders honestly open, named in its gaps")
    found = order_for_check(book, EXAMPLE_STAGE)
    if found is None or found.order_id != "order-held-order":
        raise ValueError("the shipped example book must reach its opening order under the example stage")
    if trace_of(book, "order-held-order") != "stated > recorded > bound > honoured > kept":
        raise ValueError("the shipped example book must derive the opening order's trace from its walked steps")
    if not trace_current(book, "order-held-order"):
        raise ValueError("the shipped example book must hold the opening order's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note order")

def validate_book(data: Any, *, require_example: bool = False) -> OrderBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, OrderBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a order book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live campaign build or execution "
                f"({key!r} is named on it): {ORDER_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its orders under a view")
    if "order_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held orders at call time")
    if "ledger" in data or "current_order" in data:
        raise ValueError(
            "a book stores no ledger and no current order: both are "
            "derived from its held orders at call time")
    if "trace" in data or "order" in data:
        raise ValueError(
            "a book stores no trace and no order: both are derived "
            "from its held orders at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != ORDER_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{ORDER_SCHEMA!r}")
    if data.get("campaign") is not None and (
            data["campaign"] != ORDER_SLICE):
        raise ValueError(
            f"a book's campaign must be {ORDER_SLICE!r}")
    head = data.get("order_head") or data.get("standing_orders") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's order head must be a mapping")
    title = head.get("title") or data.get("title")
    campaigns = tuple(build_campaign_ref(g) for g in data.get("campaigns") or ())
    orders = tuple(build_order(g) for g in data.get("order_records") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = OrderBook(
        title=title, campaigns=campaigns, orders=orders, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = OrderBook(
        title=book.title, campaigns=book.campaigns, orders=book.orders,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> OrderBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (OrderBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an OrderBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> OrderBook:
    return validate_book(data, require_example=require_example)


def load_order(
        data: Optional[Dict[str, Any]] = None) -> OrderBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(ORDER_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_order_file(path: Any) -> OrderBook:
    """Load one order file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: campaign references, orders and views held one by one.
# ---------------------------------------------------------------------

class OrderRegistry:
    """An in-memory holding of campaign references, orders and views.

    The registry is the pure layer's model of a
    session's order book: campaign references are
    held under their ids, orders are held under
    their ids, one order per id and per sequence,
    and views are held in recorded order, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[CampaignRef] = []
        self._orders: List[OrderRecord] = []
        self._views: List[OrderView] = []
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

    def register_campaign_ref(self, item: Any) -> CampaignRef:
        """Hold one campaign reference, bound whole before held."""
        honoured = _check_campaign_ref(item)
        return self._register(
            self._slices, honoured, "campaign_id", "campaign reference")

    def register_order(self, item: Any) -> OrderRecord:
        """Hold one order, bound whole before held."""
        honoured = _check_order_ref(item)
        return self._register(
            self._orders, honoured, "order_id", "order")

    def register_view(self, view: Any) -> OrderView:
        """Hold one view; a view naming no id takes a fresh one."""
        honoured = _check_view_ref(view)
        if not honoured.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            honoured = build_view({**honoured.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, honoured, "view_id", "view")

    def register_book(self, book: Any) -> OrderBook:
        """Hold a whole book's records, under its title."""
        honoured = build_book(book)
        if self._title is not None and honoured.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {honoured.title!r}")
        for ref in honoured.campaigns:
            self.register_campaign_ref(ref)
        for order in honoured.orders:
            self.register_order(order)
        for view in honoured.views:
            self.register_view(view)
        self._title = honoured.title
        return self.book()

    def book(self) -> OrderBook:
        return OrderBook(
            title=self._title or "An unheld order book",
            campaigns=tuple(self._slices), orders=tuple(self._orders),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[CampaignRef, ...]:
        return tuple(self._slices)

    def list_orders(self) -> Tuple[OrderRecord, ...]:
        return tuple(self._orders)

    def list_views(self) -> Tuple[OrderView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._orders) + tuple(self._views)

    def get_slice(self, campaign_id: Any) -> CampaignRef:
        return self.book().slice_for(campaign_id)

    def get_order(self, order_id: Any) -> OrderRecord:
        return self.book().order_for(order_id)

    def get_view(self, view_id: Any) -> OrderView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the ledger target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> OrderBook:
    if source is None:
        return load_order()
    if isinstance(source, OrderBook):
        return source
    if isinstance(source, OrderRegistry):
        return source.book()
    return build_book(source)


def _keptance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _KEPTANCE}


def order_record(order: Any, source: Any = None) -> Dict[str, Any]:
    honoured = _check_order_ref(order)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "order_order",
        "campaign": ORDER_SLICE,
        "order_id": honoured.order_id,
        "campaign_id": honoured.campaign_id,
        "title": honoured.title,
        "segment": segment_of(honoured, book),
        "complete": order_green(honoured, book),
        "gaps": list(order_gaps(honoured, book)),
    }
    record.update(_keptance_record(honoured))
    return record


def campaign_record(ref: Any) -> Dict[str, Any]:
    honoured = _check_campaign_ref(ref)
    record = {
        "type": "order_run",
        "campaign": ORDER_SLICE,
        "campaign_id": honoured.campaign_id,
        "title": honoured.title,
        "state": honoured.state,
    }
    record.update(_keptance_record(honoured))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    honoured = _check_trace_ref(record_in)
    record = {
        "type": "order_trace",
        "campaign": ORDER_SLICE,
        "trace_id": honoured.trace_id,
        "order_id": honoured.order_id,
        "trace": honoured.trace,
    }
    record.update(_keptance_record(honoured))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    honoured = _check_view_ref(view)
    record = {
        "type": "order_view",
        "campaign": ORDER_SLICE,
        "view_id": honoured.view_id, "seq": honoured.seq,
        "view_filter": honoured.view_filter,
    }
    record.update(_keptance_record(honoured))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    honoured = _check_note_ref(record_in)
    record = {
        "type": "order_note",
        "campaign": ORDER_SLICE,
        "note_id": honoured.note_id,
        "order_id": honoured.order_id,
        "stance": honoured.stance,
    }
    record.update(_keptance_record(honoured))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    honoured = validate_panel(panel, source)
    record = {"type": "order_panel",
              "campaign": ORDER_SLICE}
    record.update(honoured.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, OrderVerdict):
        honoured = validate_verdict(verdict, source)
    else:
        honoured = derive_verdict(_source_book(verdict), view)
    record = {"type": "order_verdict",
              "campaign": ORDER_SLICE}
    record.update(honoured.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, OrderIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "order_index",
              "campaign": ORDER_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    honoured = _source_book(book)
    record = {"type": "order_book",
              "campaign": ORDER_SLICE,
              "title": honoured.title}
    record.update(honoured.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(order: Any, source: Any = None) -> str:
    honoured = _check_order_ref(order)
    return (
        f"{honoured.title} - from {honoured.campaign_id}: "
        f"stage {honoured.stage if honoured.stage else 'none'}, "
        f"claims "
        f"{', '.join(honoured.claims) if honoured.claims else 'none'}. "
        f"{honoured.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The orders stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"orders stand complete.")


def view_plain_words(view: Any) -> str:
    honoured = _check_view_ref(view)
    return f"View {honoured.view_id}: shows {honoured.view_filter} orders."


def note_plain_words(record_in: Any) -> str:
    honoured = _check_note_ref(record_in)
    return (
        f"Note {honoured.note_id}: {honoured.stance} "
        f"{honoured.order_id}, toward {honoured.target}. "
        f"{honoured.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, OrderIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.orders)} green orders; "
        f"red, named in its gaps: {gaps}.")

def format_order(order: Any, source: Any = None) -> str:
    honoured = _check_order_ref(order)
    book = _source_book(source) if source is not None else None
    lines = [f"{honoured.title} ({honoured.order_id})"]
    lines.extend(plain_lines(honoured))
    lines.append(honoured.detail)
    if order_green(honoured, book):
        lines.append(
            "This order stands complete - it walked the question "
            "sequence in the open from stated to kept, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This order stands open - it stands named in "
            f"its gaps: {', '.join(order_gaps(honoured, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    honoured = _check_view_ref(view)
    return (
        f"View {honoured.view_id}: filter {honoured.view_filter} - "
        f"{honoured.detail}")


def format_note(record_in: Any) -> str:
    honoured = _check_note_ref(record_in)
    lines = [
        f"Order note {honoured.stance} {honoured.order_id} "
        f"({honoured.note_id}): {honoured.title}. {honoured.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_stage(source: Any, stage: Any) -> str:
    order = order_for_check(source, stage)
    if order is not None:
        return format_order(order, source)
    wanted = stage.strip() if isinstance(stage, str) else stage
    return (
        f"No held order stands under stage {wanted!r} yet - the "
        f"stage reaches nothing in this book, and no order is "
        f"invented for it.")


def format_book(source: Any = None, campaign_id: Any = None) -> str:
    book = _source_book(source)
    orders = (orders_for_campaign(book, campaign_id)
              if campaign_id is not None else book.orders)
    lines = [f"The Order Gate (M-226) - {book.title}"]
    lines.extend(segment_of(order, book) for order in orders)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Order panel under view {panel.view_id}:"]
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
    lines = ["Order index, derived from the held orders:"]
    for order in index.orders:
        lines.append(f"{order.stage} - {order.title} ({order.order_id})")
    if index.gaps:
        lines.append(
            "Red, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_order_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Order Gate (M-226)",
        f"{book.title}: {len(book.orders)} orders held, "
        f"{len(green_orders(book))} orders standing green, "
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


def parse_order_args(args: Any) -> Tuple[str, Any]:
    """Parse the /order grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("order", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("stage", "campaign"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
