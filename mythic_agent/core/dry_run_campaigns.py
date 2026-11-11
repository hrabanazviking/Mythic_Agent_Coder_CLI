"""Dry-run campaigns (roadmap slice M-224).

Part IX - The Mythic Method Engine. The roadmap
words: **slice rehearsals classified (code, test, environment, provider, scope) with the remedy each class has earned historically — the loop learns its own weather..*

What already ships, and what this campaign adds:

* The rehearsals book already ships as data
  (M-201, ``core/milestones.py``): a roadmap/rehearsal
  file (parts, campaigns, acceptance stages, state) the
  app reads. This campaign WIRES the book that book's
  book invites - several rehearsals held across
  campaigns with one ledger over them - as data, in its
  own module, standing in the M-195 copy-and-share
  book book the M-224 book stands in: one taxonomist
  per book, and the taxonomist's charge over one
  rehearsal across its campaign held as a book - a
  rehearsal. The shipped rehearsals stand untouched behind
  their seams: this layer holds rehearsals as data
  over the book's campaigns and rewrites none of them,
  and the rehearsals book keeps its own standing.
  Rehearsals stand on the ledger AS DATA alone: a
  rehearsal carries a ledger ref, a reference held in
  this book; holding, viewing or telling a rehearsal
  campaigns no rehearsal live, moves no keeper and files
  nothing.
* No charter row names this campaign: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-224 on no row, and the
  campaign tests pin that absence live. The M-005
  method charter names no campaign row either: its
  own words name the whole of Part IX as the
  part that executes the charter, and this campaign
  is built to the roadmap words and that
  execution note together.

* A rehearsal is held whole: the campaign it
  answers for, named by its campaign id; its title;
  the rehearsal steps it walked, held as data in
  walk order; and the evidence it carries, held
  as data by campaign. The rehearsal walk is EXPLICIT:
  its sequence stands as data
  (:data:`STAGES`, :data:`TRANSITIONS`) -
  planned, dealt, gated, mocked, proven -
  and a rehearsal's standing is DERIVED at
  call time from its held steps and evidence
  alone: a rehearsal that opens anywhere but
  planned, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet planned proven stands
  open, named in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - run_ref,
  class_ref, keeper_record, rehearsal_ref, evidence
  a taxonomist can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A rehearsal is
  mocked from held evidence alone, never
  from a feeling: a rehearsal holding a
  bare claim stands open, named in its gaps.
* A rehearsal stands only for an ACTIVE
  campaign. The book holds each campaign it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  rehearsal naming a campaign that stands
  nowhere in the book refuses BY NAME, and a
  rehearsal for a campaign that is not active
  refuses BY NAME beside it: the taxonomist deals with
  the campaign in hand, in roadmap order, never a
  queued one, and a campaign whose rehearsal already
  stands complete is never gated twice - the
  current rehearsal is derived, so a
  completed campaign is never the current rehearsal
  twice.
* The rehearsal's trace is visible. A trace
  record holds one rehearsal's walked steps
  as one trace line, exactly as walked, beside
  the rehearsal. The derived trace is
  computed at call time from the rehearsal's
  held steps; a held trace that no longer agrees
  with it stands stale, named in the ledger - the
  trace is the walk itself, never a retelling
  of it.
* The rehearsal index is DERIVED at call
  time from the held rehearsals - one rehearsal
  per complete rehearsal, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, order or current-rehearsal
  claim on any record refuses by name.
* The current rehearsal is DERIVED at call
  time - the first held rehearsal, in held
  order, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its rehearsal, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per rehearsal stance; holding
  a note posts none of it, the rule stands as
  data (:data:`REHEARSAL_RULE`), and a record
  claiming a rehearsal was actually proven,
  captured or promoted live refuses BY NAME.
  The taxonomist rehearsals - and those rehearsals, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the book a real rehearsal
  file takes, a loader reads a file anywhere on
  disk, rehearsals and views are dealt as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a rehearsal book for a session and
  telling from it. This layer reaches no live
  rehearsal: it writes no rehearsal live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no taxonomist, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds rehearsals
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The rehearsal walk is explicit.** A
  rehearsal is mocked against the held
  steps and legal steps alone; an illegal step
  stands named in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  rehearsal that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, named in its gaps:
  a rehearsal is mocked from evidence, not
  vibes.
* **Active campaigns only, in roadmap order.** A
  rehearsal for a missing or queued campaign
  refuses by name; no rehearsal is invented
  for a campaign the taxonomist has not dealt with.
* **Unknown stays unknown.** A rehearsal
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, order
  and current rehearsal are derived, never
  stored.** Each is derived from the held
  rehearsals at call time; a stored one
  refuses by name, so it can never drift.
* **One rehearsal per rehearsal.** Two
  rehearsals standing for one rehearsal id
  refuse by name, and one note record stands per
  rehearsal stance.
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
    "REHEARSAL_RESOURCE",
    "REHEARSAL_SCHEMA",
    "REHEARSAL_SLICE",
    "REHEARSAL_RULE",
    "PLAIN_EXPLANATION",
    "THE_REHEARSAL_SLICE",
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
    "RehearsalRecord",
    "IndexRehearsal",
    "CampaignRef",
    "NoteRecord",
    "RehearsalBook",
    "RehearsalIndex",
    "RehearsalPanel",
    "RehearsalPanelRow",
    "RehearsalRegistry",
    "RehearsalVerdict",
    "RehearsalView",
    "TargetCount",
    "trace_for_rehearsal",
    "trace_record",
    "ledger_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_rehearsal",
    "build_campaign_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_rehearsal",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "rehearsal_for_check",
    "rehearsal_order",
    "rehearsal_record",
    "first_note",
    "format_book",
    "format_rehearsal",
    "format_index",
    "format_note",
    "format_stage",
    "format_panel",
    "format_rehearsal_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "campaign_record",
    "load_rehearsal",
    "load_rehearsal_file",
    "normalize_campaign_state",
    "normalize_stage",
    "normalize_claim_kind",
    "legal_step",
    "next_stage",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_rehearsal",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_rehearsal_args",
    "green_rehearsals",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_rehearsals",
    "validate_trace",
    "validate_book",
    "validate_rehearsal",
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
    "rehearsal_gaps",
    "rehearsal_green",
    "rehearsals_for_campaign",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

REHEARSAL_SCHEMA = "mythic.dry_run_campaigns/1"
REHEARSAL_SLICE = "M-224"
THE_REHEARSAL_SLICE = REHEARSAL_SLICE
REHEARSAL_RESOURCE = "dry_run_campaigns.yaml"
INDEX_ACTION = "index"
EXAMPLE_STAGE = "proven"
STAGE_FIELDS = ("stages", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("proven", "held", "blocked")
CAMPAIGN_STATES = ("live", "dormant")
REHEARSAL_RULE = 'rehearsals are held as data alone: several rehearsals across campaigns stand with one ledger, rehearsers per rehearsal, and the human sees the whole forge at a campaign - a rehearsal stands as data, held by reference (a proof ref), never taken live - the rehearsal walk stands as an explicit rehearsal sequence - planned, dealt, gated, mocked, proven - and a rehearsal completes only complete, complete being a state with evidence held - plan ref, dealing ref, gate ref, mock ref, proof ref - never a feeling, a memory, an assertion or a summary; models are mocked so no money moves, and the shape is proven before any coin is spent; holding, viewing and reading a rehearsal runs no campaign live, approves nothing, spends nothing, spawns no process and opens no network'
PLAIN_EXPLANATION = "Dry-run campaigns (M-224): a campaign can be rehearsed (plan, dealing, gates) with models mocked — the shape proven before money moves.."
USAGE = 'Usage: /dryrun | /dryrun rehearsal <rehearsal-id> | /dryrun stage <stage> | /dryrun campaign <campaign-id> | /dryrun view <view-id> | /dryrun note <note-id> | /dryrun index | /dryrun panel | /dryrun verdict'

STAGES = ("planned", "dealt", "gated", "mocked", "proven")
HELD_EVIDENCE = ("plan_ref", "dealing_ref", "gate_ref", "mock_ref", "proof_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "planned": ("dealt",),
    "dealt": ("gated",),
    "gated": ("mocked",),
    "mocked": ("planned", "proven"),
    "proven": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a rehearsal or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a rehearsal stands complete.
    A stage outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_stage(stage: Any, failed: Any = False) -> Optional[str]:
    """The step the taxonomist takes next, DERIVED from the sequence.

    Banked leads to dealt and dealt to
    gated; gated leads to mocked; at
    mocked a follow-up banking steps back to planned and a finished rehearsal steps to proven;
    proven is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    mocked = normalize_stage(stage)
    if mocked == "planned":
        return "dealt"
    if mocked == "dealt":
        return "gated"
    if mocked == "gated":
        return "mocked"
    if mocked == "mocked":
        return "planned" if failed else "proven"
    return None


_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "rehearsal_id", "seq", "campaign_id", "title", "stages",
    "claims", "detail",
} | set(_PROVENANCE))
_SLICE_REF_KEYS = frozenset({
    "campaign_id", "seq", "title", "state", "detail",
} | set(_PROVENANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "rehearsal_id", "trace", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "rehearsal_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "rehearsals", "coverage", "covered", "uncovered",
    "current_rehearsal", "next_rehearsal", "progress", "ledger",
    "current", "order", "breaks", "live"})
_LIVE_KEYS = (
    "live_rehearsal", "rehearsals_live", "live_question",
    "rehearsals_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "rehearsals_live",
    "resumed_live", "runs_rehearsal", "paused_live",
    "runs_rehearsal", "ran_rehearsal", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "rehearsal_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_rehearsal", "sent_rehearsal",
    "posts_note", "posted_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_rehearsal", "filed_live", "spawns_taxonomist", "spawned_taxonomist", "sends_rehearsal", "sent_rehearsal", "writes_rehearsal", "wrote_rehearsal")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_stages(value: Any) -> Tuple[str, ...]:
    """A rehearsal's walked stages, held as data.

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
    """A rehearsal's asked claims: claim campaigns named as data.

    Each claim names one campaign from the proven
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


def _provenance(mapping: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key in _PROVENANCE:
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
                f"{what} claims a live gate rehearsal or campaign build "
                f"execution ({key!r} is named on it): "
                f"{REHEARSAL_RULE}")
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
# The held rehearsal: one campaign cut from an active campaign.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class RehearsalRecord:
    """One rehearsal campaign, held as data.

    The rehearsal names the active campaign it was
    held from, by campaign id, its title, its
    verifiable stages, held as data, and its
    claims, named by rehearsal id. The grain is
    derived, never stored: exactly one verifiable
    walk is gated against the machine. A rehearsal whose
    stages are not yet held stands with its
    stages empty: it stands open, named in
    its gaps, and no stage is invented for it.
    The rehearsal is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    rehearsal_id: str
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
            self, "rehearsal_id", _clean_text(self.rehearsal_id, "a rehearsal id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "campaign_id", _clean_text(self.campaign_id, "an campaign id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a rehearsal title"))
        object.__setattr__(
            self, "stages", _check_stages(self.stages))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a rehearsal detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.rehearsal_id

    @property
    def stage(self) -> str:
        """The stage the rehearsal stands at: its last walked stage."""
        return self.stages[-1] if self.stages else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "rehearsal_id": self.rehearsal_id, "seq": self.seq,
            "campaign_id": self.campaign_id, "title": self.title,
            "stages": list(self.stages),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_rehearsal_ref(value: Any) -> RehearsalRecord:
    if not isinstance(value, RehearsalRecord):
        raise ValueError("a rehearsal must be a RehearsalRecord")
    return value


def validate_rehearsal(rehearsal: Any) -> RehearsalRecord:
    return _check_rehearsal_ref(rehearsal)


def build_rehearsal(record: Any = None, **kwargs: Any) -> RehearsalRecord:
    """Build one held rehearsal from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, RehearsalRecord):
        if kwargs:
            raise ValueError("a rehearsal stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a rehearsal must be a mapping or a RehearsalRecord")
    _needed(data, _RUN_KEYS, "a rehearsal")
    return RehearsalRecord(
        rehearsal_id=data.get("rehearsal_id"), seq=data.get("seq"),
        campaign_id=data.get("campaign_id"), title=data.get("title"),
        stages=data.get("stages"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_provenance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each rehearsal to the steps it took outside the machine.

    Derived from the held rehearsals alone: a break is
    one consecutive pair of walked stages the
    explicit gate sequence does not allow, told
    in walk order as before, then after.
    """
    found: Dict[str, Tuple[str, ...]] = {}
    for rehearsal in book.rehearsals:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(rehearsal.stages, rehearsal.stages[1:])
            if not legal_step(before, after))
        if breaks:
            found[rehearsal.rehearsal_id] = breaks
    return found

def rehearsal_gaps(rehearsal: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a rehearsal from standing complete.

    Guarded from the rehearsal's own held fields alone -
    its walked steps against the explicit question
    sequence, and its carried evidence against the
    proven vocabulary: the rehearsal opens at
    named, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a rehearsal stands complete only when it has
    planned proven. The source names nothing
    further: no gap is borrowed from another
    rehearsal.
    """
    mocked = _check_rehearsal_ref(rehearsal)
    gaps: List[str] = []
    if not mocked.stages:
        gaps.append(
            "has passed through no step: the rehearsal has not started")
        return tuple(gaps)
    if mocked.stages[0] != "planned":
        gaps.append(
            f"opens at {mocked.stages[0]}, not at planned: "
            f"the rehearsal opens with the reflection")
    for before, after in zip(mocked.stages, mocked.stages[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"rehearsal sequence does not allow")
    for campaign in mocked.claims:
        if campaign in BARE_CLAIMS:
            gaps.append(
                f"carries a {campaign} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if mocked.stages[-1] != "proven":
        gaps.append(
            f"has not reached proven: the rehearsal stands "
            f"at {mocked.stages[-1]}")
    return tuple(gaps)

def rehearsal_green(rehearsal: Any, source: Any = None) -> bool:
    return not rehearsal_gaps(rehearsal, source)


def plain_lines(rehearsal: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the rehearsal's own fields."""
    mocked = _check_rehearsal_ref(rehearsal)
    return (
        f"Rehearsal: {mocked.title}",
        f"Campaign: {mocked.campaign_id}",
        f"Stage: {mocked.stage if mocked.stage else 'none'}",
        f"Claims: "
        f"{', '.join(mocked.claims) if mocked.claims else 'none'}",
    )


def segment_of(rehearsal: Any, source: Any = None) -> str:
    mocked = _check_rehearsal_ref(rehearsal)
    gaps = rehearsal_gaps(mocked, source)
    return (
        f"{mocked.rehearsal_id}: {mocked.title} - campaign: "
        f"'{mocked.campaign_id}' - stage: "
        f"'{mocked.stage if mocked.stage else 'none'}' - "
        f"stages: {len(mocked.stages)} - claims: "
        f"'{', '.join(mocked.claims) if mocked.claims else 'none'}' - "
        f"detail: '{mocked.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held campaign reference: the active campaign a book rehearsals from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CampaignRef:
    """One campaign a rehearsal book rehearsals from, held as a reference.

    The record names the campaign, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 campaign book's own telling. A rehearsal
    stands only from an active reference: the
    book refuses a rehearsal naming no held reference,
    and a rehearsal from an queued one, BY NAME.
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
        for key in _PROVENANCE:
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
        for key in _PROVENANCE:
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
        **_provenance(data))


# ---------------------------------------------------------------------
# The held trace trace: the human approves the trace, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TraceRecord:
    """One trace trace, held as data.

    The record names its campaign and the trace the
    human active - the campaign's rehearsal ids in
    derived claim order, held exactly as
    active. The trace is of the set and its
    order, never of a step: when the derived
    trace moves, this record stands stale, named
    in the ledger, until a new trace is active.
    """

    trace_id: str
    seq: int
    rehearsal_id: str
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
            self, "rehearsal_id", _clean_text(self.rehearsal_id, "an campaign id"))
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
            "rehearsal_id": self.rehearsal_id, "trace": self.trace,
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
        rehearsal_id=data.get("rehearsal_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a rehearsal, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One rehearsal stance, held as data.

    The record names its rehearsal, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per rehearsal stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    rehearsal_id: str
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
            self, "rehearsal_id", _clean_text(self.rehearsal_id, "a rehearsal id"))
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
            "rehearsal_id": self.rehearsal_id, "stance": self.stance,
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
        rehearsal_id=data.get("rehearsal_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which campaigns a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class RehearsalView:
    """A view over the book: every rehearsal, the green, the rest."""

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


def _check_view_ref(value: Any) -> RehearsalView:
    if not isinstance(value, RehearsalView):
        raise ValueError("a view must be an RehearsalView")
    return value


def validate_view(view: Any) -> RehearsalView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> RehearsalView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, RehearsalView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an RehearsalView")
    _needed(data, _VIEW_KEYS, "a view")
    return RehearsalView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class RehearsalPanelRow:
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


def _row_for_rehearsal(rehearsal: RehearsalRecord,
                     source: Any = None) -> RehearsalPanelRow:
    return RehearsalPanelRow(
        item_id=rehearsal.rehearsal_id,
        standing="complete" if rehearsal_green(rehearsal, source) else "open",
        label=rehearsal.title, segment=segment_of(rehearsal, source),
        recorded_on=rehearsal.recorded_on)


def _check_row_ref(value: Any) -> RehearsalPanelRow:
    if not isinstance(value, RehearsalPanelRow):
        raise ValueError("a panel row must be an RehearsalPanelRow")
    return value


def validate_row(row: Any, rehearsal: Any = None,
                 source: Any = None) -> RehearsalPanelRow:
    mocked = _check_row_ref(row)
    if rehearsal is not None:
        derived = _row_for_rehearsal(_check_rehearsal_ref(rehearsal), source)
        if mocked != derived:
            raise ValueError(
                f"panel row {mocked.item_id!r} does not agree with "
                f"the row derived from its rehearsal")
    return mocked


def build_row(row: Any = None, rehearsal: Any = None,
              source: Any = None,
              **kwargs: Any) -> RehearsalPanelRow:
    if rehearsal is not None:
        derived = _row_for_rehearsal(_check_rehearsal_ref(rehearsal), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            RehearsalPanelRow(**kwargs))
        return validate_row(built, rehearsal, source)
    if isinstance(row, RehearsalPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return RehearsalPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on campaign"))
    if row is None and kwargs:
        return RehearsalPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an RehearsalPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[RehearsalPanelRow, ...]
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
        f"The rehearsal book holds {total_items} rehearsals as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown rehearsals "
        f"stand complete.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its rehearsal's own fields "
        "- the campaign it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any rehearsal.",
        "Completeness is gated from the held records alone: "
        "a rehearsal that steps outside the rehearsal sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not planned proven stands open, named in its "
        "gaps, and the rehearsal index is derived from the "
        "held rehearsals, never stored where it could drift.",
    )

@dataclass(frozen=True)
class RehearsalPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[RehearsalPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> RehearsalView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, RehearsalView):
        return view
    return book.view_for(view)


def shown_rehearsals(source: Any, view: Any = None
                   ) -> Tuple[RehearsalRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.rehearsals
    if resolved.view_filter == "complete":
        return tuple(g for g in book.rehearsals if rehearsal_green(g, book))
    return tuple(g for g in book.rehearsals if not rehearsal_green(g, book))


def rehearsals_for_campaign(source: Any, campaign_id: Any
                      ) -> Tuple[RehearsalRecord, ...]:
    wanted = _clean_text(campaign_id, "an campaign id")
    return tuple(
        g for g in _source_book(source).rehearsals if g.campaign_id == wanted)


def green_rehearsals(source: Any) -> Tuple[RehearsalRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.rehearsals if rehearsal_green(g, book))


def current_rehearsal(source: Any) -> Optional[RehearsalRecord]:
    """The book's current rehearsal, DERIVED at call time.

    The first held rehearsal, in held order, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held rehearsals alone, so it can
    never go stale against them. A book whose every
    rehearsal stands complete has no current rehearsal.
    """
    book = _source_book(source)
    for rehearsal in book.rehearsals:
        if not rehearsal_green(rehearsal, book):
            return rehearsal
    return None


def derive_panel(source: Any, view: Any = None) -> RehearsalPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_rehearsals(book, resolved)
    rows = tuple(_row_for_rehearsal(rehearsal, book) for rehearsal in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.rehearsals), default="")
    green = sum(1 for g in shown if rehearsal_green(g, book))
    return RehearsalPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.rehearsals), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.rehearsals), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> RehearsalPanel:
    if not isinstance(value, RehearsalPanel):
        raise ValueError("a panel must be an RehearsalPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> RehearsalPanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 rehearsal).
    """
    mocked = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(mocked.view_id)
                if mocked.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(mocked, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {mocked.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return mocked


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> RehearsalPanel:
    if isinstance(panel, RehearsalPanel):
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
        built = RehearsalPanel(
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
    raise ValueError("a panel must be a mapping, an RehearsalPanel, or derived")


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
        return "proven"
    if green_shown == 0:
        return "blocked"
    return "held"


@dataclass(frozen=True)
class RehearsalVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> RehearsalVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_rehearsals(book, resolved)
    green = sum(1 for g in shown if rehearsal_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return RehearsalVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> RehearsalVerdict:
    if not isinstance(value, RehearsalVerdict):
        raise ValueError("a verdict must be an RehearsalVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> RehearsalVerdict:
    mocked = _check_verdict_ref(verdict)
    if mocked.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {mocked.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(mocked.view_id)
                if mocked.view_id is not None else None)
        derived = derive_verdict(book, view)
        if mocked != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return mocked


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> RehearsalVerdict:
    if isinstance(verdict, RehearsalVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = RehearsalVerdict(
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
        "a verdict must be a mapping, an RehearsalVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held campaigns' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexRehearsal:
    stage: str
    rehearsal_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "stage": self.stage, "rehearsal_id": self.rehearsal_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class RehearsalIndex:
    """The rehearsal index, derived from the held rehearsals.

    The index names one rehearsal per green rehearsal, in
    held order - the rehearsal's own one verifiable
    stage, its rehearsal id and its title - and the
    rehearsals that do not stand complete, named in its
    gaps. Nothing here is stored on any rehearsal: the
    index is derived at call time from the held
    records alone, so it can never drift from them.
    """

    rehearsals: Tuple[IndexRehearsal, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "rehearsals": [e.to_record() for e in self.rehearsals],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> RehearsalIndex:
    """Derive the rehearsal index from the book's held rehearsals."""
    book = _source_book(source)
    rehearsals = tuple(
        IndexRehearsal(stage=g.stage, rehearsal_id=g.rehearsal_id,
                   title=g.title)
        for g in book.rehearsals if rehearsal_green(g, book))
    gaps = tuple(
        g.rehearsal_id for g in book.rehearsals if not rehearsal_green(g, book))
    return RehearsalIndex(rehearsals=rehearsals, gaps=gaps)


def rehearsal_for_check(source: Any, stage: Any) -> Optional[RehearsalRecord]:
    """The first held rehearsal one stage reaches, or none - honestly."""
    if stage is None:
        return None
    if not isinstance(stage, str):
        raise ValueError("an stage must be a string naming the stage")
    wanted = stage.strip()
    if not wanted:
        return None
    for rehearsal in _source_book(source).rehearsals:
        if rehearsal.stage == wanted:
            return rehearsal
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held order: the rehearsal
    that took it and the step it took, before,
    then after. A book whose rehearsals all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{rehearsal_id}: {step}"
        for rehearsal_id, steps in _breaks_map(book).items()
        for step in steps)

def rehearsal_order(source: Any,
              campaign_id: Any = None) -> Tuple[RehearsalRecord, ...]:
    """The held rehearsals in their held order, DERIVED at call time.

    Rehearsals stand in the order the book holds them -
    the order their campaigns were taken - optionally
    for one campaign alone. Nothing here is stored:
    the order is the book's own held order, told.
    """
    book = _source_book(source)
    rehearsals = list(book.rehearsals)
    if campaign_id is not None:
        wanted = _clean_text(campaign_id, "a campaign id")
        rehearsals = [r for r in rehearsals if r.campaign_id == wanted]
    return tuple(rehearsals)

def trace_of(source: Any, rehearsal_id: Any) -> str:
    """One rehearsal's trace, DERIVED at call time.

    The rehearsal's walked stages joined as one trace
    line, in walk order. A rehearsal that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is named
    elsewhere.
    """
    rehearsal = _source_book(source).rehearsal_for(rehearsal_id)
    return " > ".join(rehearsal.stages)

def trace_for_rehearsal(source: Any,
                  rehearsal_id: Any) -> Optional[TraceRecord]:
    """The held trace for one rehearsal, or none - honestly."""
    wanted = _clean_text(rehearsal_id, "a rehearsal id")
    for record in _source_book(source).traces:
        if record.rehearsal_id == wanted:
            return record
    return None

def trace_current(source: Any, rehearsal_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_rehearsal(source, rehearsal_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, rehearsal_id)

def note_for_rehearsal(source: Any, rehearsal_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one rehearsal (and stance, when named)."""
    wanted = _clean_text(rehearsal_id, "a rehearsal id")
    for record in _source_book(source).notes:
        if record.rehearsal_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the campaign targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def ledger_record(source: Any = None) -> Dict[str, Any]:
    """The rehearsal ledger, DERIVED here from the held rehearsals alone.

    The ledger counts the held rehearsals by their
    derived completeness - green and red - names
    the current rehearsal, the first that does not yet
    stand complete, tells each held rehearsal's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held rehearsals took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.rehearsals
            if ("complete" if rehearsal_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "rehearsal_records": number})
    current = current_rehearsal(book)
    traces = []
    for rehearsal in book.rehearsals:
        trace = trace_for_rehearsal(book, rehearsal.rehearsal_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, rehearsal.rehearsal_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"rehearsal_id": rehearsal.rehearsal_id, "trace": standing})
    return {
        "type": "rehearsal_well",
        "campaign": REHEARSAL_SLICE,
        "standings": standings,
        "total": len(book.rehearsals),
        "current_rehearsal": current.rehearsal_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This campaign's own roadmap standing, proved from the roadmap itself.

    The record loads this campaign's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 campaigns in 11 parts,
    the planned prefix, the next campaign where the
    rehearsal rehearsals, and M-224's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(REHEARSAL_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "rehearsal_roadmap",
        "campaign": REHEARSAL_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m224_title": own.title,
        "m224_part": own.part,
        "m224_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: campaigns, rehearsals, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or order ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class RehearsalBook:
    title: str
    campaigns: Tuple[CampaignRef, ...] = ()
    rehearsals: Tuple[RehearsalRecord, ...] = ()
    views: Tuple[RehearsalView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[RehearsalPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        campaigns = tuple(_check_campaign_ref(g) for g in self.campaigns)
        rehearsals = tuple(_check_rehearsal_ref(g) for g in self.rehearsals)
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
        rehearsal_ids = set()
        rehearsal_seqs = set()
        for rehearsal in rehearsals:
            if rehearsal.rehearsal_id in rehearsal_ids:
                raise ValueError(
                    f"two rehearsals stand under id {rehearsal.rehearsal_id!r}")
            if rehearsal.seq in rehearsal_seqs:
                raise ValueError(
                    f"two rehearsals stand at sequence {rehearsal.seq}")
            rehearsal_ids.add(rehearsal.rehearsal_id)
            rehearsal_seqs.add(rehearsal.seq)
        by_slice = {ref.campaign_id: ref for ref in campaigns}
        for rehearsal in (rehearsals if campaigns else ()):

            ref = by_slice.get(rehearsal.campaign_id)
            if ref is None:
                raise ValueError(
                    f"rehearsal {rehearsal.rehearsal_id!r} is held from campaign "
                    f"{rehearsal.campaign_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "live":
                raise ValueError(
                    f"rehearsal {rehearsal.rehearsal_id!r} is held from campaign "
                    f"{rehearsal.campaign_id!r}, which is not active: "
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
            target = (record.rehearsal_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for rehearsal "
                    f"{record.rehearsal_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per rehearsal target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_rehearsals = set()
        rehearsal_ids = {rehearsal.rehearsal_id for rehearsal in rehearsals}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.rehearsal_id in trace_rehearsals:
                raise ValueError(
                    f"two traces stand for rehearsal "
                    f"{record.rehearsal_id!r}: one trace stands "
                    f"per rehearsal walk")
            if rehearsals and record.rehearsal_id not in rehearsal_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces rehearsal "
                    f"{record.rehearsal_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_rehearsals.add(record.rehearsal_id)
        object.__setattr__(
            self, "campaigns", tuple(sorted(campaigns, key=lambda g: g.seq)))
        object.__setattr__(
            self, "rehearsal_records", tuple(sorted(rehearsals, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.rehearsals + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.rehearsal_id for g in self.rehearsals) + tuple(
            v.view_id for v in self.views)

    def rehearsal_ids(self) -> Tuple[str, ...]:
        return tuple(g.rehearsal_id for g in self.rehearsals)

    def campaign_ids(self) -> Tuple[str, ...]:
        return tuple(g.campaign_id for g in self.campaigns)

    def rehearsal_for(self, rehearsal_id: Any) -> RehearsalRecord:
        wanted = _clean_text(rehearsal_id, "a rehearsal id")
        for rehearsal in self.rehearsals:
            if rehearsal.rehearsal_id == wanted:
                return rehearsal
        raise KeyError(f"no rehearsal named {wanted!r} stands in this book")

    def slice_for(self, campaign_id: Any) -> CampaignRef:
        wanted = _clean_text(campaign_id, "an campaign id")
        for ref in self.campaigns:
            if ref.campaign_id == wanted:
                return ref
        raise KeyError(f"no campaign named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> RehearsalView:
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
        for rehearsal in self.rehearsals:
            if rehearsal.rehearsal_id == wanted:
                return rehearsal
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "campaigns": [g.to_record() for g in self.campaigns],
            "rehearsal_records": [g.to_record() for g in self.rehearsals],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: RehearsalBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: RehearsalBook) -> None:
    if book.title != "Dry-run campaigns at the M-224 slice run":
        raise ValueError("the shipped example book carries another title")
    if len(book.campaigns) != 3 or len(book.rehearsals) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three campaign references, five rehearsals and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m223-campaign":
        raise ValueError("the pinned panel is panel-m223-campaign")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.stage for e in index.rehearsals] != ["proven", "proven", "proven"]:
        raise ValueError("the shipped example book index must derive the three held complete rehearsals in held order")
    if index.gaps != ("rehearsal-bare-rehearsal", "rehearsal-leaping-rehearsal"):
        raise ValueError("the shipped example book must leave the bare and leaping rehearsals honestly open, named in its gaps")
    found = rehearsal_for_check(book, EXAMPLE_STAGE)
    if found is None or found.rehearsal_id != "rehearsal-held-rehearsal":
        raise ValueError("the shipped example book must reach its opening rehearsal under the example stage")
    if trace_of(book, "rehearsal-held-rehearsal") != "planned > dealt > gated > mocked > proven":
        raise ValueError("the shipped example book must derive the opening rehearsal's trace from its walked steps")
    if not trace_current(book, "rehearsal-held-rehearsal"):
        raise ValueError("the shipped example book must hold the opening rehearsal's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note rehearsal")

def validate_book(data: Any, *, require_example: bool = False) -> RehearsalBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, RehearsalBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a rehearsal book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live campaign build or execution "
                f"({key!r} is named on it): {REHEARSAL_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its rehearsals under a view")
    if "rehearsal_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held rehearsals at call time")
    if "ledger" in data or "current_rehearsal" in data:
        raise ValueError(
            "a book stores no ledger and no current rehearsal: both are "
            "derived from its held rehearsals at call time")
    if "trace" in data or "order" in data:
        raise ValueError(
            "a book stores no trace and no order: both are derived "
            "from its held rehearsals at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != REHEARSAL_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{REHEARSAL_SCHEMA!r}")
    if data.get("campaign") is not None and (
            data["campaign"] != REHEARSAL_SLICE):
        raise ValueError(
            f"a book's campaign must be {REHEARSAL_SLICE!r}")
    head = data.get("rehearsal_head") or data.get("dry_run_campaigns") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's rehearsal head must be a mapping")
    title = head.get("title") or data.get("title")
    campaigns = tuple(build_campaign_ref(g) for g in data.get("campaigns") or ())
    rehearsals = tuple(build_rehearsal(g) for g in data.get("rehearsal_records") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = RehearsalBook(
        title=title, campaigns=campaigns, rehearsals=rehearsals, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = RehearsalBook(
        title=book.title, campaigns=book.campaigns, rehearsals=book.rehearsals,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> RehearsalBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (RehearsalBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an RehearsalBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> RehearsalBook:
    return validate_book(data, require_example=require_example)


def load_rehearsal(
        data: Optional[Dict[str, Any]] = None) -> RehearsalBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(REHEARSAL_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_rehearsal_file(path: Any) -> RehearsalBook:
    """Load one rehearsal file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: campaign references, rehearsals and views held one by one.
# ---------------------------------------------------------------------

class RehearsalRegistry:
    """An in-memory holding of campaign references, rehearsals and views.

    The registry is the pure layer's model of a
    session's rehearsal book: campaign references are
    held under their ids, rehearsals are held under
    their ids, one rehearsal per id and per sequence,
    and views are held in dealt order, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[CampaignRef] = []
        self._rehearsals: List[RehearsalRecord] = []
        self._views: List[RehearsalView] = []
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
        """Hold one campaign reference, gated whole before held."""
        mocked = _check_campaign_ref(item)
        return self._register(
            self._slices, mocked, "campaign_id", "campaign reference")

    def register_rehearsal(self, item: Any) -> RehearsalRecord:
        """Hold one rehearsal, gated whole before held."""
        mocked = _check_rehearsal_ref(item)
        return self._register(
            self._rehearsals, mocked, "rehearsal_id", "rehearsal")

    def register_view(self, view: Any) -> RehearsalView:
        """Hold one view; a view naming no id takes a fresh one."""
        mocked = _check_view_ref(view)
        if not mocked.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            mocked = build_view({**mocked.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, mocked, "view_id", "view")

    def register_book(self, book: Any) -> RehearsalBook:
        """Hold a whole book's records, under its title."""
        mocked = build_book(book)
        if self._title is not None and mocked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {mocked.title!r}")
        for ref in mocked.campaigns:
            self.register_campaign_ref(ref)
        for rehearsal in mocked.rehearsals:
            self.register_rehearsal(rehearsal)
        for view in mocked.views:
            self.register_view(view)
        self._title = mocked.title
        return self.book()

    def book(self) -> RehearsalBook:
        return RehearsalBook(
            title=self._title or "An unheld rehearsal book",
            campaigns=tuple(self._slices), rehearsals=tuple(self._rehearsals),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[CampaignRef, ...]:
        return tuple(self._slices)

    def list_rehearsals(self) -> Tuple[RehearsalRecord, ...]:
        return tuple(self._rehearsals)

    def list_views(self) -> Tuple[RehearsalView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._rehearsals) + tuple(self._views)

    def get_slice(self, campaign_id: Any) -> CampaignRef:
        return self.book().slice_for(campaign_id)

    def get_rehearsal(self, rehearsal_id: Any) -> RehearsalRecord:
        return self.book().rehearsal_for(rehearsal_id)

    def get_view(self, view_id: Any) -> RehearsalView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the ledger target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> RehearsalBook:
    if source is None:
        return load_rehearsal()
    if isinstance(source, RehearsalBook):
        return source
    if isinstance(source, RehearsalRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def rehearsal_record(rehearsal: Any, source: Any = None) -> Dict[str, Any]:
    mocked = _check_rehearsal_ref(rehearsal)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "rehearsal_rehearsal",
        "campaign": REHEARSAL_SLICE,
        "rehearsal_id": mocked.rehearsal_id,
        "campaign_id": mocked.campaign_id,
        "title": mocked.title,
        "segment": segment_of(mocked, book),
        "complete": rehearsal_green(mocked, book),
        "gaps": list(rehearsal_gaps(mocked, book)),
    }
    record.update(_provenance_record(mocked))
    return record


def campaign_record(ref: Any) -> Dict[str, Any]:
    mocked = _check_campaign_ref(ref)
    record = {
        "type": "rehearsal_run",
        "campaign": REHEARSAL_SLICE,
        "campaign_id": mocked.campaign_id,
        "title": mocked.title,
        "state": mocked.state,
    }
    record.update(_provenance_record(mocked))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    mocked = _check_trace_ref(record_in)
    record = {
        "type": "rehearsal_trace",
        "campaign": REHEARSAL_SLICE,
        "trace_id": mocked.trace_id,
        "rehearsal_id": mocked.rehearsal_id,
        "trace": mocked.trace,
    }
    record.update(_provenance_record(mocked))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    mocked = _check_view_ref(view)
    record = {
        "type": "rehearsal_view",
        "campaign": REHEARSAL_SLICE,
        "view_id": mocked.view_id, "seq": mocked.seq,
        "view_filter": mocked.view_filter,
    }
    record.update(_provenance_record(mocked))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    mocked = _check_note_ref(record_in)
    record = {
        "type": "rehearsal_note",
        "campaign": REHEARSAL_SLICE,
        "note_id": mocked.note_id,
        "rehearsal_id": mocked.rehearsal_id,
        "stance": mocked.stance,
    }
    record.update(_provenance_record(mocked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    mocked = validate_panel(panel, source)
    record = {"type": "rehearsal_panel",
              "campaign": REHEARSAL_SLICE}
    record.update(mocked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, RehearsalVerdict):
        mocked = validate_verdict(verdict, source)
    else:
        mocked = derive_verdict(_source_book(verdict), view)
    record = {"type": "rehearsal_verdict",
              "campaign": REHEARSAL_SLICE}
    record.update(mocked.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, RehearsalIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "rehearsal_index",
              "campaign": REHEARSAL_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    mocked = _source_book(book)
    record = {"type": "rehearsal_book",
              "campaign": REHEARSAL_SLICE,
              "title": mocked.title}
    record.update(mocked.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(rehearsal: Any, source: Any = None) -> str:
    mocked = _check_rehearsal_ref(rehearsal)
    return (
        f"{mocked.title} - from {mocked.campaign_id}: "
        f"stage {mocked.stage if mocked.stage else 'none'}, "
        f"claims "
        f"{', '.join(mocked.claims) if mocked.claims else 'none'}. "
        f"{mocked.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The rehearsals stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"rehearsals stand complete.")


def view_plain_words(view: Any) -> str:
    mocked = _check_view_ref(view)
    return f"View {mocked.view_id}: shows {mocked.view_filter} rehearsals."


def note_plain_words(record_in: Any) -> str:
    mocked = _check_note_ref(record_in)
    return (
        f"Note {mocked.note_id}: {mocked.stance} "
        f"{mocked.rehearsal_id}, toward {mocked.target}. "
        f"{mocked.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, RehearsalIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.rehearsals)} green rehearsals; "
        f"red, named in its gaps: {gaps}.")

def format_rehearsal(rehearsal: Any, source: Any = None) -> str:
    mocked = _check_rehearsal_ref(rehearsal)
    book = _source_book(source) if source is not None else None
    lines = [f"{mocked.title} ({mocked.rehearsal_id})"]
    lines.extend(plain_lines(mocked))
    lines.append(mocked.detail)
    if rehearsal_green(mocked, book):
        lines.append(
            "This rehearsal stands complete - it walked the question "
            "sequence in the open from planned to proven, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This rehearsal stands open - it stands named in "
            f"its gaps: {', '.join(rehearsal_gaps(mocked, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    mocked = _check_view_ref(view)
    return (
        f"View {mocked.view_id}: filter {mocked.view_filter} - "
        f"{mocked.detail}")


def format_note(record_in: Any) -> str:
    mocked = _check_note_ref(record_in)
    lines = [
        f"Rehearsal note {mocked.stance} {mocked.rehearsal_id} "
        f"({mocked.note_id}): {mocked.title}. {mocked.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_stage(source: Any, stage: Any) -> str:
    rehearsal = rehearsal_for_check(source, stage)
    if rehearsal is not None:
        return format_rehearsal(rehearsal, source)
    wanted = stage.strip() if isinstance(stage, str) else stage
    return (
        f"No held rehearsal stands under stage {wanted!r} yet - the "
        f"stage reaches nothing in this book, and no rehearsal is "
        f"invented for it.")


def format_book(source: Any = None, campaign_id: Any = None) -> str:
    book = _source_book(source)
    rehearsals = (rehearsals_for_campaign(book, campaign_id)
              if campaign_id is not None else book.rehearsals)
    lines = [f"The Rehearsal Gate (M-224) - {book.title}"]
    lines.extend(segment_of(rehearsal, book) for rehearsal in rehearsals)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Rehearsal panel under view {panel.view_id}:"]
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
    lines = ["Rehearsal index, derived from the held rehearsals:"]
    for rehearsal in index.rehearsals:
        lines.append(f"{rehearsal.stage} - {rehearsal.title} ({rehearsal.rehearsal_id})")
    if index.gaps:
        lines.append(
            "Red, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_rehearsal_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Rehearsal Gate (M-224)",
        f"{book.title}: {len(book.rehearsals)} rehearsals held, "
        f"{len(green_rehearsals(book))} rehearsals standing green, "
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


def parse_rehearsal_args(args: Any) -> Tuple[str, Any]:
    """Parse the /rehearsal grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("rehearsal", "view", "note"):
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
