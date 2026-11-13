"""Workflow default honoured (roadmap slice M-227).

Part IX - The Mythic Method Engine. The roadmap
words: **repositories' CI is proposed as manual-dispatch by default on Volmarr's projects (his standing ruling), and the coder says so when it writes a workflow.**

What already ships, and what this campaign adds:

* The proposals book already ships as data
  (M-201, ``core/milestones.py``): a roadmap/proposal
  file (parts, campaigns, acceptance stages, state) the
  app reads. This campaign WIRES the book that book's
  book invites - several proposals held across
  campaigns with one ledger over them - as data, in its
  own module, standing in the M-195 copy-and-share
  book book the M-227 book stands in: one dispatcher
  per book, and the dispatcher's charge over one
  proposal across its campaign held as a book - a
  proposal. The shipped proposals stand untouched behind
  their seams: this layer holds proposals as data
  over the book's campaigns and rewrites none of them,
  and the proposals book keeps its own standing.
  Proposals stand on the ledger AS DATA alone: a
  proposal carries a ledger ref, a reference held in
  this book; holding, viewing or telling a proposal
  campaigns no proposal live, moves no keeper and files
  nothing.
* No charter row names this campaign: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-227 on no row, and the
  campaign tests pin that absence live. The M-005
  method charter names no campaign row either: its
  own words name the whole of Part IX as the
  part that executes the charter, and this campaign
  is built to the roadmap words and that
  execution note together.

* A proposal is held whole: the campaign it
  answers for, named by its campaign id; its title;
  the proposal steps it walked, held as data in
  walk proposal; and the evidence it carries, held
  as data by campaign. The proposal walk is EXPLICIT:
  its sequence stands as data
  (:data:`STAGES`, :data:`TRANSITIONS`) -
  proposed, checked, declared, manual, upheld -
  and a proposal's standing is DERIVED at
  call time from its held steps and evidence
  alone: a proposal that opens anywhere but
  proposed, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet proposed upheld stands
  open, named in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - workflow_ref,
  dispatch_ref, repo_ref, trigger_ref, proposal_ref, evidence
  a dispatcher can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A proposal is
  manual from held evidence alone, never
  from a feeling: a proposal holding a
  bare claim stands open, named in its gaps.
* A proposal stands only for an ACTIVE
  campaign. The book holds each campaign it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  proposal naming a campaign that stands
  nowhere in the book refuses BY NAME, and a
  proposal for a campaign that is not active
  refuses BY NAME beside it: the dispatcher deals with
  the campaign in hand, in roadmap proposal, never a
  queued one, and a campaign whose proposal already
  stands complete is never declared twice - the
  current proposal is derived, so a
  completed campaign is never the current proposal
  twice.
* The proposal's trace is visible. A trace
  record holds one proposal's walked steps
  as one trace line, exactly as walked, beside
  the proposal. The derived trace is
  computed at call time from the proposal's
  held steps; a held trace that no longer agrees
  with it stands stale, named in the ledger - the
  trace is the walk itself, never a retelling
  of it.
* The proposal index is DERIVED at call
  time from the held proposals - one proposal
  per complete proposal, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, proposal or current-proposal
  claim on any record refuses by name.
* The current proposal is DERIVED at call
  time - the first held proposal, in held
  proposal, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its proposal, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per proposal stance; holding
  a note posts none of it, the rule stands as
  data (:data:`PROPOSAL_RULE`), and a record
  claiming a proposal was actually upheld,
  captured or promoted live refuses BY NAME.
  The dispatcher proposals - and those proposals, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the book a real proposal
  file takes, a loader reads a file anywhere on
  disk, proposals and views are checked as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a proposal book for a session and
  telling from it. This layer reaches no live
  proposal: it writes no proposal live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no dispatcher, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds proposals
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The proposal walk is explicit.** A
  proposal is manual against the held
  steps and legal steps alone; an illegal step
  stands named in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  proposal that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, named in its gaps:
  a proposal is manual from evidence, not
  vibes.
* **Active campaigns only, in roadmap proposal.** A
  proposal for a missing or queued campaign
  refuses by name; no proposal is invented
  for a campaign the dispatcher has not checked with.
* **Unknown stays unknown.** A proposal
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, proposal
  and current proposal are derived, never
  stored.** Each is derived from the held
  proposals at call time; a stored one
  refuses by name, so it can never drift.
* **One proposal per proposal.** Two
  proposals standing for one proposal id
  refuse by name, and one note record stands per
  proposal stance.
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
    "PROPOSAL_RESOURCE",
    "PROPOSAL_SCHEMA",
    "PROPOSAL_SLICE",
    "PROPOSAL_RULE",
    "PLAIN_EXPLANATION",
    "THE_PROPOSAL_SLICE",
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
    "ProposalRecord",
    "IndexProposal",
    "CampaignRef",
    "NoteRecord",
    "ProposalBook",
    "ProposalIndex",
    "ProposalPanel",
    "ProposalPanelRow",
    "ProposalRegistry",
    "ProposalVerdict",
    "ProposalView",
    "TargetCount",
    "trace_for_proposal",
    "trace_record",
    "ledger_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_proposal",
    "build_campaign_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_proposal",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "proposal_for_check",
    "proposal_proposal",
    "proposal_record",
    "first_note",
    "format_book",
    "format_proposal",
    "format_index",
    "format_note",
    "format_stage",
    "format_panel",
    "format_proposal_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "campaign_record",
    "load_proposal",
    "load_proposal_file",
    "normalize_campaign_state",
    "normalize_stage",
    "normalize_claim_kind",
    "legal_step",
    "next_stage",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_proposal",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_proposal_args",
    "green_proposals",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_proposals",
    "validate_trace",
    "validate_book",
    "validate_proposal",
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
    "proposal_gaps",
    "proposal_green",
    "proposals_for_campaign",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

PROPOSAL_SCHEMA = "mythic.workflow_default/1"
PROPOSAL_SLICE = "M-227"
THE_PROPOSAL_SLICE = PROPOSAL_SLICE
PROPOSAL_RESOURCE = "workflow_default.yaml"
INDEX_ACTION = "index"
EXAMPLE_STAGE = "upheld"
STAGE_FIELDS = ("stages", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("upheld", "held", "blocked")
CAMPAIGN_STATES = ("live", "dormant")
PROPOSAL_RULE = 'proposals are held as data alone: several proposals across campaigns stand with one ledger, dispatchers per proposal, and the human sees the whole forge at a campaign - a proposal stands as data, held by reference (a proposal ref), never taken live - the proposal walk stands as an explicit proposal sequence - proposed, checked, declared, manual, upheld - and a proposal completes only complete, complete being a state with evidence held - workflow ref, dispatch ref, repo ref, trigger ref, proposal ref - never a feeling, a memory, an assertion or a summary; repositories CI is proposed as manual-dispatch by default on Volmarr projects (his standing ruling), and the coder says so when it writes a workflow, and a proposal whose triggers run on push or pull request by default stands open, named in its gaps; holding, viewing and reading a proposal writes no workflow live, approves nothing, spends nothing, spawns no process and opens no network'
PLAIN_EXPLANATION = "Workflow default honoured (M-227): repositories' CI is proposed as manual-dispatch by default on Volmarr's projects (his standing ruling), and the coder says so when it writes a workflow."
USAGE = 'Usage: /workflow | /workflow proposal <proposal-id> | /workflow stage <stage> | /workflow campaign <campaign-id> | /workflow view <view-id> | /workflow note <note-id> | /workflow index | /workflow panel | /workflow verdict'

STAGES = ("proposed", "checked", "declared", "manual", "upheld")
HELD_EVIDENCE = ("workflow_ref", "dispatch_ref", "repo_ref", "trigger_ref", "proposal_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "proposed": ("checked",),
    "checked": ("declared",),
    "declared": ("manual",),
    "manual": ("proposed", "upheld"),
    "upheld": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a proposal or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a proposal stands complete.
    A stage outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_stage(stage: Any, failed: Any = False) -> Optional[str]:
    """The step the dispatcher takes next, DERIVED from the sequence.

    Banked leads to checked and checked to
    declared; declared leads to manual; at
    manual a follow-up banking steps back to proposed and a finished proposal steps to upheld;
    upheld is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    manual = normalize_stage(stage)
    if manual == "proposed":
        return "checked"
    if manual == "checked":
        return "declared"
    if manual == "declared":
        return "manual"
    if manual == "manual":
        return "proposed" if failed else "upheld"
    return None


_UPHELDANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "proposal_id", "seq", "campaign_id", "title", "stages",
    "claims", "detail",
} | set(_UPHELDANCE))
_SLICE_REF_KEYS = frozenset({
    "campaign_id", "seq", "title", "state", "detail",
} | set(_UPHELDANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "proposal_id", "trace", "detail",
} | set(_UPHELDANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_UPHELDANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "proposal_id", "stance", "target", "title",
    "detail",
} | set(_UPHELDANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "proposals", "coverage", "covered", "uncovered",
    "current_proposal", "next_proposal", "progress", "ledger",
    "current", "proposal", "breaks", "live"})
_LIVE_KEYS = (
    "live_proposal", "proposals_live", "live_question",
    "proposals_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "proposals_live",
    "resumed_live", "runs_proposal", "paused_live",
    "runs_proposal", "ran_proposal", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "proposal_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_proposal", "sent_proposal",
    "posts_note", "posted_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_proposal", "filed_live", "spawns_dispatcher", "spawned_dispatcher", "sends_proposal", "sent_proposal", "writes_proposal", "wrote_proposal")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_stages(value: Any) -> Tuple[str, ...]:
    """A proposal's walked stages, held as data.

    The stages stand as a list of stage names in
    walk proposal, each one a stage of the explicit
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
    """A proposal's asked claims: claim campaigns named as data.

    Each claim names one campaign from the upheld
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


def _upheldance(mapping: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key in _UPHELDANCE:
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
                f"{what} claims a live gate proposal or campaign build "
                f"execution ({key!r} is named on it): "
                f"{PROPOSAL_RULE}")
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
# The held proposal: one campaign cut from an active campaign.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ProposalRecord:
    """One proposal campaign, held as data.

    The proposal names the active campaign it was
    held from, by campaign id, its title, its
    verifiable stages, held as data, and its
    claims, named by proposal id. The grain is
    derived, never stored: exactly one verifiable
    walk is declared against the machine. A proposal whose
    stages are not yet held stands with its
    stages empty: it stands open, named in
    its gaps, and no stage is invented for it.
    The proposal is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    proposal_id: str
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
            self, "proposal_id", _clean_text(self.proposal_id, "a proposal id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "campaign_id", _clean_text(self.campaign_id, "an campaign id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a proposal title"))
        object.__setattr__(
            self, "stages", _check_stages(self.stages))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a proposal detail"))
        for key in _UPHELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.proposal_id

    @property
    def stage(self) -> str:
        """The stage the proposal stands at: its last walked stage."""
        return self.stages[-1] if self.stages else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "proposal_id": self.proposal_id, "seq": self.seq,
            "campaign_id": self.campaign_id, "title": self.title,
            "stages": list(self.stages),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _UPHELDANCE:
            record[key] = getattr(self, key)
        return record


def _check_proposal_ref(value: Any) -> ProposalRecord:
    if not isinstance(value, ProposalRecord):
        raise ValueError("a proposal must be a ProposalRecord")
    return value


def validate_proposal(proposal: Any) -> ProposalRecord:
    return _check_proposal_ref(proposal)


def build_proposal(record: Any = None, **kwargs: Any) -> ProposalRecord:
    """Build one held proposal from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, ProposalRecord):
        if kwargs:
            raise ValueError("a proposal stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a proposal must be a mapping or a ProposalRecord")
    _needed(data, _RUN_KEYS, "a proposal")
    return ProposalRecord(
        proposal_id=data.get("proposal_id"), seq=data.get("seq"),
        campaign_id=data.get("campaign_id"), title=data.get("title"),
        stages=data.get("stages"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_upheldance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each proposal to the steps it took outside the machine.

    Derived from the held proposals alone: a break is
    one consecutive pair of walked stages the
    explicit gate sequence does not allow, told
    in walk proposal as before, then after.
    """
    found: Dict[str, Tuple[str, ...]] = {}
    for proposal in book.proposals:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(proposal.stages, proposal.stages[1:])
            if not legal_step(before, after))
        if breaks:
            found[proposal.proposal_id] = breaks
    return found

def proposal_gaps(proposal: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a proposal from standing complete.

    Guarded from the proposal's own held fields alone -
    its walked steps against the explicit question
    sequence, and its upheld evidence against the
    upheld vocabulary: the proposal opens at
    named, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a proposal stands complete only when it has
    proposed upheld. The source names nothing
    further: no gap is borrowed from another
    proposal.
    """
    manual = _check_proposal_ref(proposal)
    gaps: List[str] = []
    if not manual.stages:
        gaps.append(
            "has passed through no step: the proposal has not started")
        return tuple(gaps)
    if manual.stages[0] != "proposed":
        gaps.append(
            f"opens at {manual.stages[0]}, not at proposed: "
            f"the proposal opens with the reflection")
    for before, after in zip(manual.stages, manual.stages[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"proposal sequence does not allow")
    for campaign in manual.claims:
        if campaign in BARE_CLAIMS:
            gaps.append(
                f"carries a {campaign} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if manual.stages[-1] != "upheld":
        gaps.append(
            f"has not reached upheld: the proposal stands "
            f"at {manual.stages[-1]}")
    return tuple(gaps)

def proposal_green(proposal: Any, source: Any = None) -> bool:
    return not proposal_gaps(proposal, source)


def plain_lines(proposal: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the proposal's own fields."""
    manual = _check_proposal_ref(proposal)
    return (
        f"Proposal: {manual.title}",
        f"Campaign: {manual.campaign_id}",
        f"Stage: {manual.stage if manual.stage else 'none'}",
        f"Claims: "
        f"{', '.join(manual.claims) if manual.claims else 'none'}",
    )


def segment_of(proposal: Any, source: Any = None) -> str:
    manual = _check_proposal_ref(proposal)
    gaps = proposal_gaps(manual, source)
    return (
        f"{manual.proposal_id}: {manual.title} - campaign: "
        f"'{manual.campaign_id}' - stage: "
        f"'{manual.stage if manual.stage else 'none'}' - "
        f"stages: {len(manual.stages)} - claims: "
        f"'{', '.join(manual.claims) if manual.claims else 'none'}' - "
        f"detail: '{manual.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held campaign reference: the active campaign a book proposals from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CampaignRef:
    """One campaign a proposal book proposals from, held as a reference.

    The record names the campaign, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 campaign book's own telling. A proposal
    stands only from an active reference: the
    book refuses a proposal naming no held reference,
    and a proposal from an queued one, BY NAME.
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
        for key in _UPHELDANCE:
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
        for key in _UPHELDANCE:
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
        **_upheldance(data))


# ---------------------------------------------------------------------
# The held trace trace: the human approves the trace, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TraceRecord:
    """One trace trace, held as data.

    The record names its campaign and the trace the
    human active - the campaign's proposal ids in
    derived claim proposal, held exactly as
    active. The trace is of the set and its
    proposal, never of a step: when the derived
    trace moves, this record stands stale, named
    in the ledger, until a new trace is active.
    """

    trace_id: str
    seq: int
    proposal_id: str
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
            self, "proposal_id", _clean_text(self.proposal_id, "an campaign id"))
        object.__setattr__(
            self, "trace", _clean_text(self.trace, "an active trace"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an trace detail"))
        for key in _UPHELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.trace_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "trace_id": self.trace_id, "seq": self.seq,
            "proposal_id": self.proposal_id, "trace": self.trace,
            "detail": self.detail,
        }
        for key in _UPHELDANCE:
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
        proposal_id=data.get("proposal_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_upheldance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a proposal, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One proposal stance, held as data.

    The record names its proposal, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per proposal stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    proposal_id: str
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
            self, "proposal_id", _clean_text(self.proposal_id, "a proposal id"))
        object.__setattr__(self, "stance", normalize_stance(self.stance))
        object.__setattr__(
            self, "target", _clean_text(self.target, "a stance target"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a stance title"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a stance detail"))
        for key in _UPHELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.note_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "note_id": self.note_id, "seq": self.seq,
            "proposal_id": self.proposal_id, "stance": self.stance,
            "target": self.target, "title": self.title,
            "detail": self.detail,
        }
        for key in _UPHELDANCE:
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
        proposal_id=data.get("proposal_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_upheldance(data))


# ---------------------------------------------------------------------
# The held view: which campaigns a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ProposalView:
    """A view over the book: every proposal, the green, the rest."""

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
        for key in _UPHELDANCE:
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
        for key in _UPHELDANCE:
            record[key] = getattr(self, key)
        return record


def _check_view_ref(value: Any) -> ProposalView:
    if not isinstance(value, ProposalView):
        raise ValueError("a view must be an ProposalView")
    return value


def validate_view(view: Any) -> ProposalView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> ProposalView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, ProposalView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an ProposalView")
    _needed(data, _VIEW_KEYS, "a view")
    return ProposalView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_upheldance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ProposalPanelRow:
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


def _row_for_proposal(proposal: ProposalRecord,
                     source: Any = None) -> ProposalPanelRow:
    return ProposalPanelRow(
        item_id=proposal.proposal_id,
        standing="complete" if proposal_green(proposal, source) else "open",
        label=proposal.title, segment=segment_of(proposal, source),
        recorded_on=proposal.recorded_on)


def _check_row_ref(value: Any) -> ProposalPanelRow:
    if not isinstance(value, ProposalPanelRow):
        raise ValueError("a panel row must be an ProposalPanelRow")
    return value


def validate_row(row: Any, proposal: Any = None,
                 source: Any = None) -> ProposalPanelRow:
    manual = _check_row_ref(row)
    if proposal is not None:
        derived = _row_for_proposal(_check_proposal_ref(proposal), source)
        if manual != derived:
            raise ValueError(
                f"panel row {manual.item_id!r} does not agree with "
                f"the row derived from its proposal")
    return manual


def build_row(row: Any = None, proposal: Any = None,
              source: Any = None,
              **kwargs: Any) -> ProposalPanelRow:
    if proposal is not None:
        derived = _row_for_proposal(_check_proposal_ref(proposal), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            ProposalPanelRow(**kwargs))
        return validate_row(built, proposal, source)
    if isinstance(row, ProposalPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return ProposalPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on campaign"))
    if row is None and kwargs:
        return ProposalPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an ProposalPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[ProposalPanelRow, ...]
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
        f"The proposal book holds {total_items} proposals as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown proposals "
        f"stand complete.",
        "Rows stand in held proposal, the proposal the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its proposal's own fields "
        "- the campaign it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any proposal.",
        "Completeness is declared from the held records alone: "
        "a proposal that steps outside the proposal sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not proposed upheld stands open, named in its "
        "gaps, and the proposal index is derived from the "
        "held proposals, never stored where it could drift.",
    )

@dataclass(frozen=True)
class ProposalPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[ProposalPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> ProposalView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, ProposalView):
        return view
    return book.view_for(view)


def shown_proposals(source: Any, view: Any = None
                   ) -> Tuple[ProposalRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.proposals
    if resolved.view_filter == "complete":
        return tuple(g for g in book.proposals if proposal_green(g, book))
    return tuple(g for g in book.proposals if not proposal_green(g, book))


def proposals_for_campaign(source: Any, campaign_id: Any
                      ) -> Tuple[ProposalRecord, ...]:
    wanted = _clean_text(campaign_id, "an campaign id")
    return tuple(
        g for g in _source_book(source).proposals if g.campaign_id == wanted)


def green_proposals(source: Any) -> Tuple[ProposalRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.proposals if proposal_green(g, book))


def current_proposal(source: Any) -> Optional[ProposalRecord]:
    """The book's current proposal, DERIVED at call time.

    The first held proposal, in held proposal, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held proposals alone, so it can
    never go stale against them. A book whose every
    proposal stands complete has no current proposal.
    """
    book = _source_book(source)
    for proposal in book.proposals:
        if not proposal_green(proposal, book):
            return proposal
    return None


def derive_panel(source: Any, view: Any = None) -> ProposalPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_proposals(book, resolved)
    rows = tuple(_row_for_proposal(proposal, book) for proposal in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.proposals), default="")
    green = sum(1 for g in shown if proposal_green(g, book))
    return ProposalPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.proposals), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.proposals), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> ProposalPanel:
    if not isinstance(value, ProposalPanel):
        raise ValueError("a panel must be an ProposalPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> ProposalPanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 proposal).
    """
    manual = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(manual.view_id)
                if manual.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(manual, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {manual.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return manual


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> ProposalPanel:
    if isinstance(panel, ProposalPanel):
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
        built = ProposalPanel(
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
    raise ValueError("a panel must be a mapping, an ProposalPanel, or derived")


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
        return "upheld"
    if green_shown == 0:
        return "blocked"
    return "held"


@dataclass(frozen=True)
class ProposalVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> ProposalVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_proposals(book, resolved)
    green = sum(1 for g in shown if proposal_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return ProposalVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> ProposalVerdict:
    if not isinstance(value, ProposalVerdict):
        raise ValueError("a verdict must be an ProposalVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> ProposalVerdict:
    manual = _check_verdict_ref(verdict)
    if manual.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {manual.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(manual.view_id)
                if manual.view_id is not None else None)
        derived = derive_verdict(book, view)
        if manual != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return manual


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> ProposalVerdict:
    if isinstance(verdict, ProposalVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = ProposalVerdict(
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
        "a verdict must be a mapping, an ProposalVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held campaigns' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexProposal:
    stage: str
    proposal_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "stage": self.stage, "proposal_id": self.proposal_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class ProposalIndex:
    """The proposal index, derived from the held proposals.

    The index names one proposal per green proposal, in
    held proposal - the proposal's own one verifiable
    stage, its proposal id and its title - and the
    proposals that do not stand complete, named in its
    gaps. Nothing here is stored on any proposal: the
    index is derived at call time from the held
    records alone, so it can never drift from them.
    """

    proposals: Tuple[IndexProposal, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "proposals": [e.to_record() for e in self.proposals],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> ProposalIndex:
    """Derive the proposal index from the book's held proposals."""
    book = _source_book(source)
    proposals = tuple(
        IndexProposal(stage=g.stage, proposal_id=g.proposal_id,
                   title=g.title)
        for g in book.proposals if proposal_green(g, book))
    gaps = tuple(
        g.proposal_id for g in book.proposals if not proposal_green(g, book))
    return ProposalIndex(proposals=proposals, gaps=gaps)


def proposal_for_check(source: Any, stage: Any) -> Optional[ProposalRecord]:
    """The first held proposal one stage reaches, or none - honestly."""
    if stage is None:
        return None
    if not isinstance(stage, str):
        raise ValueError("an stage must be a string naming the stage")
    wanted = stage.strip()
    if not wanted:
        return None
    for proposal in _source_book(source).proposals:
        if proposal.stage == wanted:
            return proposal
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held proposal: the proposal
    that took it and the step it took, before,
    then after. A book whose proposals all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{proposal_id}: {step}"
        for proposal_id, steps in _breaks_map(book).items()
        for step in steps)

def proposal_proposal(source: Any,
              campaign_id: Any = None) -> Tuple[ProposalRecord, ...]:
    """The held proposals in their held proposal, DERIVED at call time.

    Proposals stand in the proposal the book holds them -
    the proposal their campaigns were taken - optionally
    for one campaign alone. Nothing here is stored:
    the proposal is the book's own held proposal, told.
    """
    book = _source_book(source)
    proposals = list(book.proposals)
    if campaign_id is not None:
        wanted = _clean_text(campaign_id, "a campaign id")
        proposals = [r for r in proposals if r.campaign_id == wanted]
    return tuple(proposals)

def trace_of(source: Any, proposal_id: Any) -> str:
    """One proposal's trace, DERIVED at call time.

    The proposal's walked stages joined as one trace
    line, in walk proposal. A proposal that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is named
    elsewhere.
    """
    proposal = _source_book(source).proposal_for(proposal_id)
    return " > ".join(proposal.stages)

def trace_for_proposal(source: Any,
                  proposal_id: Any) -> Optional[TraceRecord]:
    """The held trace for one proposal, or none - honestly."""
    wanted = _clean_text(proposal_id, "a proposal id")
    for record in _source_book(source).traces:
        if record.proposal_id == wanted:
            return record
    return None

def trace_current(source: Any, proposal_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_proposal(source, proposal_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, proposal_id)

def note_for_proposal(source: Any, proposal_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one proposal (and stance, when named)."""
    wanted = _clean_text(proposal_id, "a proposal id")
    for record in _source_book(source).notes:
        if record.proposal_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the campaign targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def ledger_record(source: Any = None) -> Dict[str, Any]:
    """The proposal ledger, DERIVED here from the held proposals alone.

    The ledger counts the held proposals by their
    derived completeness - green and red - names
    the current proposal, the first that does not yet
    stand complete, tells each held proposal's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held proposals took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.proposals
            if ("complete" if proposal_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "proposal_records": number})
    current = current_proposal(book)
    traces = []
    for proposal in book.proposals:
        trace = trace_for_proposal(book, proposal.proposal_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, proposal.proposal_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"proposal_id": proposal.proposal_id, "trace": standing})
    return {
        "type": "proposal_well",
        "campaign": PROPOSAL_SLICE,
        "standings": standings,
        "total": len(book.proposals),
        "current_proposal": current.proposal_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This campaign's own roadmap standing, proved from the roadmap itself.

    The record loads this campaign's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 campaigns in 11 parts,
    the proposed prefix, the next campaign where the
    proposal proposals, and M-227's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(PROPOSAL_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "proposal_roadmap",
        "campaign": PROPOSAL_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m227_title": own.title,
        "m227_part": own.part,
        "m227_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: campaigns, proposals, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or proposal ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ProposalBook:
    title: str
    campaigns: Tuple[CampaignRef, ...] = ()
    proposals: Tuple[ProposalRecord, ...] = ()
    views: Tuple[ProposalView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[ProposalPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        campaigns = tuple(_check_campaign_ref(g) for g in self.campaigns)
        proposals = tuple(_check_proposal_ref(g) for g in self.proposals)
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
        proposal_ids = set()
        proposal_seqs = set()
        for proposal in proposals:
            if proposal.proposal_id in proposal_ids:
                raise ValueError(
                    f"two proposals stand under id {proposal.proposal_id!r}")
            if proposal.seq in proposal_seqs:
                raise ValueError(
                    f"two proposals stand at sequence {proposal.seq}")
            proposal_ids.add(proposal.proposal_id)
            proposal_seqs.add(proposal.seq)
        by_slice = {ref.campaign_id: ref for ref in campaigns}
        for proposal in (proposals if campaigns else ()):

            ref = by_slice.get(proposal.campaign_id)
            if ref is None:
                raise ValueError(
                    f"proposal {proposal.proposal_id!r} is held from campaign "
                    f"{proposal.campaign_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "live":
                raise ValueError(
                    f"proposal {proposal.proposal_id!r} is held from campaign "
                    f"{proposal.campaign_id!r}, which is not active: "
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
            target = (record.proposal_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for proposal "
                    f"{record.proposal_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per proposal target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_proposals = set()
        proposal_ids = {proposal.proposal_id for proposal in proposals}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.proposal_id in trace_proposals:
                raise ValueError(
                    f"two traces stand for proposal "
                    f"{record.proposal_id!r}: one trace stands "
                    f"per proposal walk")
            if proposals and record.proposal_id not in proposal_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces proposal "
                    f"{record.proposal_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_proposals.add(record.proposal_id)
        object.__setattr__(
            self, "campaigns", tuple(sorted(campaigns, key=lambda g: g.seq)))
        object.__setattr__(
            self, "proposal_records", tuple(sorted(proposals, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.proposals + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.proposal_id for g in self.proposals) + tuple(
            v.view_id for v in self.views)

    def proposal_ids(self) -> Tuple[str, ...]:
        return tuple(g.proposal_id for g in self.proposals)

    def campaign_ids(self) -> Tuple[str, ...]:
        return tuple(g.campaign_id for g in self.campaigns)

    def proposal_for(self, proposal_id: Any) -> ProposalRecord:
        wanted = _clean_text(proposal_id, "a proposal id")
        for proposal in self.proposals:
            if proposal.proposal_id == wanted:
                return proposal
        raise KeyError(f"no proposal named {wanted!r} stands in this book")

    def slice_for(self, campaign_id: Any) -> CampaignRef:
        wanted = _clean_text(campaign_id, "an campaign id")
        for ref in self.campaigns:
            if ref.campaign_id == wanted:
                return ref
        raise KeyError(f"no campaign named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> ProposalView:
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
        for proposal in self.proposals:
            if proposal.proposal_id == wanted:
                return proposal
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "campaigns": [g.to_record() for g in self.campaigns],
            "proposal_records": [g.to_record() for g in self.proposals],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: ProposalBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: ProposalBook) -> None:
    if book.title != "Workflow default honoured at the M-227 slice run":
        raise ValueError("the shipped example book carries another title")
    if len(book.campaigns) != 3 or len(book.proposals) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three campaign references, five proposals and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m226-campaign":
        raise ValueError("the pinned panel is panel-m226-campaign")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.stage for e in index.proposals] != ["upheld", "upheld", "upheld"]:
        raise ValueError("the shipped example book index must derive the three held complete proposals in held proposal")
    if index.gaps != ("proposal-bare-proposal", "proposal-leaping-proposal"):
        raise ValueError("the shipped example book must leave the bare and leaping proposals honestly open, named in its gaps")
    found = proposal_for_check(book, EXAMPLE_STAGE)
    if found is None or found.proposal_id != "proposal-held-proposal":
        raise ValueError("the shipped example book must reach its opening proposal under the example stage")
    if trace_of(book, "proposal-held-proposal") != "proposed > checked > declared > manual > upheld":
        raise ValueError("the shipped example book must derive the opening proposal's trace from its walked steps")
    if not trace_current(book, "proposal-held-proposal"):
        raise ValueError("the shipped example book must hold the opening proposal's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note proposal")

def validate_book(data: Any, *, require_example: bool = False) -> ProposalBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, ProposalBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a proposal book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live campaign build or execution "
                f"({key!r} is named on it): {PROPOSAL_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its proposals under a view")
    if "proposal_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held proposals at call time")
    if "ledger" in data or "current_proposal" in data:
        raise ValueError(
            "a book stores no ledger and no current proposal: both are "
            "derived from its held proposals at call time")
    if "trace" in data or "proposal" in data:
        raise ValueError(
            "a book stores no trace and no proposal: both are derived "
            "from its held proposals at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != PROPOSAL_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{PROPOSAL_SCHEMA!r}")
    if data.get("campaign") is not None and (
            data["campaign"] != PROPOSAL_SLICE):
        raise ValueError(
            f"a book's campaign must be {PROPOSAL_SLICE!r}")
    head = data.get("proposal_head") or data.get("workflow_default") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's proposal head must be a mapping")
    title = head.get("title") or data.get("title")
    campaigns = tuple(build_campaign_ref(g) for g in data.get("campaigns") or ())
    proposals = tuple(build_proposal(g) for g in data.get("proposal_records") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = ProposalBook(
        title=title, campaigns=campaigns, proposals=proposals, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = ProposalBook(
        title=book.title, campaigns=book.campaigns, proposals=book.proposals,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> ProposalBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (ProposalBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an ProposalBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> ProposalBook:
    return validate_book(data, require_example=require_example)


def load_proposal(
        data: Optional[Dict[str, Any]] = None) -> ProposalBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(PROPOSAL_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_proposal_file(path: Any) -> ProposalBook:
    """Load one proposal file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: campaign references, proposals and views held one by one.
# ---------------------------------------------------------------------

class ProposalRegistry:
    """An in-memory holding of campaign references, proposals and views.

    The registry is the pure layer's model of a
    session's proposal book: campaign references are
    held under their ids, proposals are held under
    their ids, one proposal per id and per sequence,
    and views are held in checked proposal, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[CampaignRef] = []
        self._proposals: List[ProposalRecord] = []
        self._views: List[ProposalView] = []
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
        """Hold one campaign reference, declared whole before held."""
        manual = _check_campaign_ref(item)
        return self._register(
            self._slices, manual, "campaign_id", "campaign reference")

    def register_proposal(self, item: Any) -> ProposalRecord:
        """Hold one proposal, declared whole before held."""
        manual = _check_proposal_ref(item)
        return self._register(
            self._proposals, manual, "proposal_id", "proposal")

    def register_view(self, view: Any) -> ProposalView:
        """Hold one view; a view naming no id takes a fresh one."""
        manual = _check_view_ref(view)
        if not manual.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            manual = build_view({**manual.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, manual, "view_id", "view")

    def register_book(self, book: Any) -> ProposalBook:
        """Hold a whole book's records, under its title."""
        manual = build_book(book)
        if self._title is not None and manual.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {manual.title!r}")
        for ref in manual.campaigns:
            self.register_campaign_ref(ref)
        for proposal in manual.proposals:
            self.register_proposal(proposal)
        for view in manual.views:
            self.register_view(view)
        self._title = manual.title
        return self.book()

    def book(self) -> ProposalBook:
        return ProposalBook(
            title=self._title or "An unheld proposal book",
            campaigns=tuple(self._slices), proposals=tuple(self._proposals),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[CampaignRef, ...]:
        return tuple(self._slices)

    def list_proposals(self) -> Tuple[ProposalRecord, ...]:
        return tuple(self._proposals)

    def list_views(self) -> Tuple[ProposalView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._proposals) + tuple(self._views)

    def get_slice(self, campaign_id: Any) -> CampaignRef:
        return self.book().slice_for(campaign_id)

    def get_proposal(self, proposal_id: Any) -> ProposalRecord:
        return self.book().proposal_for(proposal_id)

    def get_view(self, view_id: Any) -> ProposalView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the ledger target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> ProposalBook:
    if source is None:
        return load_proposal()
    if isinstance(source, ProposalBook):
        return source
    if isinstance(source, ProposalRegistry):
        return source.book()
    return build_book(source)


def _upheldance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _UPHELDANCE}


def proposal_record(proposal: Any, source: Any = None) -> Dict[str, Any]:
    manual = _check_proposal_ref(proposal)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "proposal_proposal",
        "campaign": PROPOSAL_SLICE,
        "proposal_id": manual.proposal_id,
        "campaign_id": manual.campaign_id,
        "title": manual.title,
        "segment": segment_of(manual, book),
        "complete": proposal_green(manual, book),
        "gaps": list(proposal_gaps(manual, book)),
    }
    record.update(_upheldance_record(manual))
    return record


def campaign_record(ref: Any) -> Dict[str, Any]:
    manual = _check_campaign_ref(ref)
    record = {
        "type": "proposal_run",
        "campaign": PROPOSAL_SLICE,
        "campaign_id": manual.campaign_id,
        "title": manual.title,
        "state": manual.state,
    }
    record.update(_upheldance_record(manual))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    manual = _check_trace_ref(record_in)
    record = {
        "type": "proposal_trace",
        "campaign": PROPOSAL_SLICE,
        "trace_id": manual.trace_id,
        "proposal_id": manual.proposal_id,
        "trace": manual.trace,
    }
    record.update(_upheldance_record(manual))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    manual = _check_view_ref(view)
    record = {
        "type": "proposal_view",
        "campaign": PROPOSAL_SLICE,
        "view_id": manual.view_id, "seq": manual.seq,
        "view_filter": manual.view_filter,
    }
    record.update(_upheldance_record(manual))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    manual = _check_note_ref(record_in)
    record = {
        "type": "proposal_note",
        "campaign": PROPOSAL_SLICE,
        "note_id": manual.note_id,
        "proposal_id": manual.proposal_id,
        "stance": manual.stance,
    }
    record.update(_upheldance_record(manual))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    manual = validate_panel(panel, source)
    record = {"type": "proposal_panel",
              "campaign": PROPOSAL_SLICE}
    record.update(manual.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, ProposalVerdict):
        manual = validate_verdict(verdict, source)
    else:
        manual = derive_verdict(_source_book(verdict), view)
    record = {"type": "proposal_verdict",
              "campaign": PROPOSAL_SLICE}
    record.update(manual.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, ProposalIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "proposal_index",
              "campaign": PROPOSAL_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    manual = _source_book(book)
    record = {"type": "proposal_book",
              "campaign": PROPOSAL_SLICE,
              "title": manual.title}
    record.update(manual.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(proposal: Any, source: Any = None) -> str:
    manual = _check_proposal_ref(proposal)
    return (
        f"{manual.title} - from {manual.campaign_id}: "
        f"stage {manual.stage if manual.stage else 'none'}, "
        f"claims "
        f"{', '.join(manual.claims) if manual.claims else 'none'}. "
        f"{manual.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The proposals stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"proposals stand complete.")


def view_plain_words(view: Any) -> str:
    manual = _check_view_ref(view)
    return f"View {manual.view_id}: shows {manual.view_filter} proposals."


def note_plain_words(record_in: Any) -> str:
    manual = _check_note_ref(record_in)
    return (
        f"Note {manual.note_id}: {manual.stance} "
        f"{manual.proposal_id}, toward {manual.target}. "
        f"{manual.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, ProposalIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.proposals)} green proposals; "
        f"red, named in its gaps: {gaps}.")

def format_proposal(proposal: Any, source: Any = None) -> str:
    manual = _check_proposal_ref(proposal)
    book = _source_book(source) if source is not None else None
    lines = [f"{manual.title} ({manual.proposal_id})"]
    lines.extend(plain_lines(manual))
    lines.append(manual.detail)
    if proposal_green(manual, book):
        lines.append(
            "This proposal stands complete - it walked the question "
            "sequence in the open from proposed to upheld, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This proposal stands open - it stands named in "
            f"its gaps: {', '.join(proposal_gaps(manual, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    manual = _check_view_ref(view)
    return (
        f"View {manual.view_id}: filter {manual.view_filter} - "
        f"{manual.detail}")


def format_note(record_in: Any) -> str:
    manual = _check_note_ref(record_in)
    lines = [
        f"Proposal note {manual.stance} {manual.proposal_id} "
        f"({manual.note_id}): {manual.title}. {manual.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_stage(source: Any, stage: Any) -> str:
    proposal = proposal_for_check(source, stage)
    if proposal is not None:
        return format_proposal(proposal, source)
    wanted = stage.strip() if isinstance(stage, str) else stage
    return (
        f"No held proposal stands under stage {wanted!r} yet - the "
        f"stage reaches nothing in this book, and no proposal is "
        f"invented for it.")


def format_book(source: Any = None, campaign_id: Any = None) -> str:
    book = _source_book(source)
    proposals = (proposals_for_campaign(book, campaign_id)
              if campaign_id is not None else book.proposals)
    lines = [f"The Proposal Gate (M-227) - {book.title}"]
    lines.extend(segment_of(proposal, book) for proposal in proposals)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Proposal panel under view {panel.view_id}:"]
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
    lines = ["Proposal index, derived from the held proposals:"]
    for proposal in index.proposals:
        lines.append(f"{proposal.stage} - {proposal.title} ({proposal.proposal_id})")
    if index.gaps:
        lines.append(
            "Red, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_proposal_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Proposal Gate (M-227)",
        f"{book.title}: {len(book.proposals)} proposals held, "
        f"{len(green_proposals(book))} proposals standing green, "
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


def parse_proposal_args(args: Any) -> Tuple[str, Any]:
    """Parse the /proposal grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("proposal", "view", "note"):
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
