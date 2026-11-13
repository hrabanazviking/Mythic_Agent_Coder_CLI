"""Team-of-one scaling (roadmap slice M-228).

Part IX - The Mythic Method Engine. The roadmap
words: **the same machinery serves a hobby repo and a 500-slice epic without ceremony change - grain follows the work, not the ego of the tool.***

What already ships, and what this campaign adds:

* The endeavours book already ships as data
  (M-201, ``core/milestones.py``): a roadmap/endeavour
  file (parts, campaigns, acceptance stages, state) the
  app reads. This campaign WIRES the book that book's
  book invites - several endeavours held across
  campaigns with one ledger over them - as data, in its
  own module, standing in the M-195 copy-and-share
  book book the M-228 book stands in: one steward
  per book, and the steward's charge over one
  endeavour across its campaign held as a book - a
  endeavour. The shipped endeavours stand untouched behind
  their seams: this layer holds endeavours as data
  over the book's campaigns and rewrites none of them,
  and the endeavours book keeps its own standing.
  Endeavours stand on the ledger AS DATA alone: a
  endeavour carries a ledger ref, a reference held in
  this book; holding, viewing or telling a endeavour
  campaigns no endeavour live, moves no keeper and files
  nothing.
* No charter row names this campaign: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-228 on no row, and the
  campaign tests pin that absence live. The M-005
  method charter names no campaign row either: its
  own words name the whole of Part IX as the
  part that executes the charter, and this campaign
  is built to the roadmap words and that
  execution note together.

* A endeavour is held whole: the campaign it
  answers for, named by its campaign id; its title;
  the endeavour steps it walked, held as data in
  walk endeavour; and the evidence it carries, held
  as data by campaign. The endeavour walk is EXPLICIT:
  its sequence stands as data
  (:data:`STAGES`, :data:`TRANSITIONS`) -
  scoped, sized, grained, matched, served -
  and a endeavour's standing is DERIVED at
  call time from its held steps and evidence
  alone: a endeavour that opens anywhere but
  scoped, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet scoped served stands
  open, named in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - scope_ref,
  size_ref, grain_ref, crew_ref, endeavour_ref, evidence
  a steward can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A endeavour is
  matched from held evidence alone, never
  from a feeling: a endeavour holding a
  bare claim stands open, named in its gaps.
* A endeavour stands only for an ACTIVE
  campaign. The book holds each campaign it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  endeavour naming a campaign that stands
  nowhere in the book refuses BY NAME, and a
  endeavour for a campaign that is not active
  refuses BY NAME beside it: the steward deals with
  the campaign in hand, in roadmap endeavour, never a
  queued one, and a campaign whose endeavour already
  stands complete is never grained twice - the
  current endeavour is derived, so a
  completed campaign is never the current endeavour
  twice.
* The endeavour's trace is visible. A trace
  record holds one endeavour's walked steps
  as one trace line, exactly as walked, beside
  the endeavour. The derived trace is
  computed at call time from the endeavour's
  held steps; a held trace that no longer agrees
  with it stands stale, named in the ledger - the
  trace is the walk itself, never a retelling
  of it.
* The endeavour index is DERIVED at call
  time from the held endeavours - one endeavour
  per complete endeavour, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, endeavour or current-endeavour
  claim on any record refuses by name.
* The current endeavour is DERIVED at call
  time - the first held endeavour, in held
  endeavour, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its endeavour, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per endeavour stance; holding
  a note posts none of it, the rule stands as
  data (:data:`ENDEAVOUR_RULE`), and a record
  claiming a endeavour was actually served,
  captured or promoted live refuses BY NAME.
  The steward endeavours - and those endeavours, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the book a real endeavour
  file takes, a loader reads a file anywhere on
  disk, endeavours and views are sized as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a endeavour book for a session and
  telling from it. This layer reaches no live
  endeavour: it writes no endeavour live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no steward, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds endeavours
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The endeavour walk is explicit.** A
  endeavour is matched against the held
  steps and legal steps alone; an illegal step
  stands named in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  endeavour that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, named in its gaps:
  a endeavour is matched from evidence, not
  vibes.
* **Active campaigns only, in roadmap endeavour.** A
  endeavour for a missing or queued campaign
  refuses by name; no endeavour is invented
  for a campaign the steward has not sized with.
* **Unknown stays unknown.** A endeavour
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, endeavour
  and current endeavour are derived, never
  stored.** Each is derived from the held
  endeavours at call time; a stored one
  refuses by name, so it can never drift.
* **One endeavour per endeavour.** Two
  endeavours standing for one endeavour id
  refuse by name, and one note record stands per
  endeavour stance.
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
    "ENDEAVOUR_RESOURCE",
    "ENDEAVOUR_SCHEMA",
    "ENDEAVOUR_SLICE",
    "ENDEAVOUR_RULE",
    "PLAIN_EXPLANATION",
    "THE_ENDEAVOUR_SLICE",
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
    "EndeavourRecord",
    "IndexEndeavour",
    "CampaignRef",
    "NoteRecord",
    "EndeavourBook",
    "EndeavourIndex",
    "EndeavourPanel",
    "EndeavourPanelRow",
    "EndeavourRegistry",
    "EndeavourVerdict",
    "EndeavourView",
    "TargetCount",
    "trace_for_endeavour",
    "trace_record",
    "ledger_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_endeavour",
    "build_campaign_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_endeavour",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "endeavour_for_check",
    "endeavour_endeavour",
    "endeavour_record",
    "first_note",
    "format_book",
    "format_endeavour",
    "format_index",
    "format_note",
    "format_stage",
    "format_panel",
    "format_endeavour_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "campaign_record",
    "load_endeavour",
    "load_endeavour_file",
    "normalize_campaign_state",
    "normalize_stage",
    "normalize_claim_kind",
    "legal_step",
    "next_stage",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_endeavour",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_endeavour_args",
    "green_endeavours",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_endeavours",
    "validate_trace",
    "validate_book",
    "validate_endeavour",
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
    "endeavour_gaps",
    "endeavour_green",
    "endeavours_for_campaign",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

ENDEAVOUR_SCHEMA = "mythic.team_scaling/1"
ENDEAVOUR_SLICE = "M-228"
THE_ENDEAVOUR_SLICE = ENDEAVOUR_SLICE
ENDEAVOUR_RESOURCE = "team_scaling.yaml"
INDEX_ACTION = "index"
EXAMPLE_STAGE = "served"
STAGE_FIELDS = ("stages", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("served", "held", "blocked")
CAMPAIGN_STATES = ("live", "dormant")
ENDEAVOUR_RULE = 'endeavours are held as data alone: several endeavours across campaigns stand with one ledger, stewards per endeavour, and the human sees the whole forge at a campaign - an endeavour stands as data, held by reference (an endeavour ref), never taken live - the endeavour walk stands as an explicit endeavour sequence - scoped, sized, grained, matched, served - and an endeavour completes only complete, complete being a state with evidence held - scope ref, size ref, grain ref, crew ref, endeavour ref - never a feeling, a memory, an assertion or a summary; the same machinery serves a hobby repo and a 500-slice epic without ceremony change - grain follows the work, not the ego of the tool - and an endeavour grained for a crew it does not have, or served with ceremony the work does not need, stands open, named in its gaps; holding, viewing and reading an endeavour starts no work live, assigns no crew, spends nothing, spawns no process and opens no network'
PLAIN_EXPLANATION = 'Team-of-one scaling (M-228): the same machinery serves a hobby repo and a 500-slice epic without ceremony change - grain follows the work, not the ego of the tool.'
USAGE = 'Usage: /scaling | /scaling endeavour <endeavour-id> | /scaling stage <stage> | /scaling campaign <campaign-id> | /scaling view <view-id> | /scaling note <note-id> | /scaling index | /scaling panel | /scaling verdict'

STAGES = ("scoped", "sized", "grained", "matched", "served")
HELD_EVIDENCE = ("scope_ref", "size_ref", "grain_ref", "crew_ref", "endeavour_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "scoped": ("sized",),
    "sized": ("grained",),
    "grained": ("matched",),
    "matched": ("scoped", "served"),
    "served": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a endeavour or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a endeavour stands complete.
    A stage outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_stage(stage: Any, failed: Any = False) -> Optional[str]:
    """The step the steward takes next, DERIVED from the sequence.

    Banked leads to sized and sized to
    grained; grained leads to matched; at
    matched a follow-up banking steps back to scoped and a finished endeavour steps to served;
    served is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    matched = normalize_stage(stage)
    if matched == "scoped":
        return "sized"
    if matched == "sized":
        return "grained"
    if matched == "grained":
        return "matched"
    if matched == "matched":
        return "scoped" if failed else "served"
    return None


_SERVEDANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "endeavour_id", "seq", "campaign_id", "title", "stages",
    "claims", "detail",
} | set(_SERVEDANCE))
_SLICE_REF_KEYS = frozenset({
    "campaign_id", "seq", "title", "state", "detail",
} | set(_SERVEDANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "endeavour_id", "trace", "detail",
} | set(_SERVEDANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_SERVEDANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "endeavour_id", "stance", "target", "title",
    "detail",
} | set(_SERVEDANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "endeavours", "coverage", "covered", "uncovered",
    "current_endeavour", "next_endeavour", "progress", "ledger",
    "current", "endeavour", "breaks", "live"})
_LIVE_KEYS = (
    "live_endeavour", "endeavours_live", "live_question",
    "endeavours_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "endeavours_live",
    "resumed_live", "runs_endeavour", "paused_live",
    "runs_endeavour", "ran_endeavour", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "endeavour_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_endeavour", "sent_endeavour",
    "posts_note", "posted_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_endeavour", "filed_live", "spawns_steward", "spawned_steward", "sends_endeavour", "sent_endeavour", "writes_endeavour", "wrote_endeavour")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_stages(value: Any) -> Tuple[str, ...]:
    """A endeavour's walked stages, held as data.

    The stages stand as a list of stage names in
    walk endeavour, each one a stage of the explicit
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
    """A endeavour's asked claims: claim campaigns named as data.

    Each claim names one campaign from the served
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


def _servedance(mapping: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key in _SERVEDANCE:
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
                f"{what} claims a live gate endeavour or campaign build "
                f"execution ({key!r} is named on it): "
                f"{ENDEAVOUR_RULE}")
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
# The held endeavour: one campaign cut from an active campaign.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class EndeavourRecord:
    """One endeavour campaign, held as data.

    The endeavour names the active campaign it was
    held from, by campaign id, its title, its
    verifiable stages, held as data, and its
    claims, named by endeavour id. The grain is
    derived, never stored: exactly one verifiable
    walk is grained against the machine. A endeavour whose
    stages are not yet held stands with its
    stages empty: it stands open, named in
    its gaps, and no stage is invented for it.
    The endeavour is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    endeavour_id: str
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
            self, "endeavour_id", _clean_text(self.endeavour_id, "a endeavour id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "campaign_id", _clean_text(self.campaign_id, "an campaign id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a endeavour title"))
        object.__setattr__(
            self, "stages", _check_stages(self.stages))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a endeavour detail"))
        for key in _SERVEDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.endeavour_id

    @property
    def stage(self) -> str:
        """The stage the endeavour stands at: its last walked stage."""
        return self.stages[-1] if self.stages else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "endeavour_id": self.endeavour_id, "seq": self.seq,
            "campaign_id": self.campaign_id, "title": self.title,
            "stages": list(self.stages),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _SERVEDANCE:
            record[key] = getattr(self, key)
        return record


def _check_endeavour_ref(value: Any) -> EndeavourRecord:
    if not isinstance(value, EndeavourRecord):
        raise ValueError("a endeavour must be a EndeavourRecord")
    return value


def validate_endeavour(endeavour: Any) -> EndeavourRecord:
    return _check_endeavour_ref(endeavour)


def build_endeavour(record: Any = None, **kwargs: Any) -> EndeavourRecord:
    """Build one held endeavour from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, EndeavourRecord):
        if kwargs:
            raise ValueError("a endeavour stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a endeavour must be a mapping or a EndeavourRecord")
    _needed(data, _RUN_KEYS, "a endeavour")
    return EndeavourRecord(
        endeavour_id=data.get("endeavour_id"), seq=data.get("seq"),
        campaign_id=data.get("campaign_id"), title=data.get("title"),
        stages=data.get("stages"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_servedance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each endeavour to the steps it took outside the machine.

    Derived from the held endeavours alone: a break is
    one consecutive pair of walked stages the
    explicit gate sequence does not allow, told
    in walk endeavour as before, then after.
    """
    found: Dict[str, Tuple[str, ...]] = {}
    for endeavour in book.endeavours:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(endeavour.stages, endeavour.stages[1:])
            if not legal_step(before, after))
        if breaks:
            found[endeavour.endeavour_id] = breaks
    return found

def endeavour_gaps(endeavour: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a endeavour from standing complete.

    Guarded from the endeavour's own held fields alone -
    its walked steps against the explicit question
    sequence, and its served evidence against the
    served vocabulary: the endeavour opens at
    named, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a endeavour stands complete only when it has
    scoped served. The source names nothing
    further: no gap is borrowed from another
    endeavour.
    """
    matched = _check_endeavour_ref(endeavour)
    gaps: List[str] = []
    if not matched.stages:
        gaps.append(
            "has passed through no step: the endeavour has not started")
        return tuple(gaps)
    if matched.stages[0] != "scoped":
        gaps.append(
            f"opens at {matched.stages[0]}, not at scoped: "
            f"the endeavour opens with the reflection")
    for before, after in zip(matched.stages, matched.stages[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"endeavour sequence does not allow")
    for campaign in matched.claims:
        if campaign in BARE_CLAIMS:
            gaps.append(
                f"carries a {campaign} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if matched.stages[-1] != "served":
        gaps.append(
            f"has not reached served: the endeavour stands "
            f"at {matched.stages[-1]}")
    return tuple(gaps)

def endeavour_green(endeavour: Any, source: Any = None) -> bool:
    return not endeavour_gaps(endeavour, source)


def plain_lines(endeavour: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the endeavour's own fields."""
    matched = _check_endeavour_ref(endeavour)
    return (
        f"Endeavour: {matched.title}",
        f"Campaign: {matched.campaign_id}",
        f"Stage: {matched.stage if matched.stage else 'none'}",
        f"Claims: "
        f"{', '.join(matched.claims) if matched.claims else 'none'}",
    )


def segment_of(endeavour: Any, source: Any = None) -> str:
    matched = _check_endeavour_ref(endeavour)
    gaps = endeavour_gaps(matched, source)
    return (
        f"{matched.endeavour_id}: {matched.title} - campaign: "
        f"'{matched.campaign_id}' - stage: "
        f"'{matched.stage if matched.stage else 'none'}' - "
        f"stages: {len(matched.stages)} - claims: "
        f"'{', '.join(matched.claims) if matched.claims else 'none'}' - "
        f"detail: '{matched.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held campaign reference: the active campaign a book endeavours from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CampaignRef:
    """One campaign a endeavour book endeavours from, held as a reference.

    The record names the campaign, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 campaign book's own telling. A endeavour
    stands only from an active reference: the
    book refuses a endeavour naming no held reference,
    and a endeavour from an queued one, BY NAME.
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
        for key in _SERVEDANCE:
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
        for key in _SERVEDANCE:
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
        **_servedance(data))


# ---------------------------------------------------------------------
# The held trace trace: the human approves the trace, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TraceRecord:
    """One trace trace, held as data.

    The record names its campaign and the trace the
    human active - the campaign's endeavour ids in
    derived claim endeavour, held exactly as
    active. The trace is of the set and its
    endeavour, never of a step: when the derived
    trace moves, this record stands stale, named
    in the ledger, until a new trace is active.
    """

    trace_id: str
    seq: int
    endeavour_id: str
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
            self, "endeavour_id", _clean_text(self.endeavour_id, "an campaign id"))
        object.__setattr__(
            self, "trace", _clean_text(self.trace, "an active trace"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an trace detail"))
        for key in _SERVEDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.trace_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "trace_id": self.trace_id, "seq": self.seq,
            "endeavour_id": self.endeavour_id, "trace": self.trace,
            "detail": self.detail,
        }
        for key in _SERVEDANCE:
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
        endeavour_id=data.get("endeavour_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_servedance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a endeavour, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One endeavour stance, held as data.

    The record names its endeavour, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per endeavour stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    endeavour_id: str
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
            self, "endeavour_id", _clean_text(self.endeavour_id, "a endeavour id"))
        object.__setattr__(self, "stance", normalize_stance(self.stance))
        object.__setattr__(
            self, "target", _clean_text(self.target, "a stance target"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a stance title"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a stance detail"))
        for key in _SERVEDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.note_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "note_id": self.note_id, "seq": self.seq,
            "endeavour_id": self.endeavour_id, "stance": self.stance,
            "target": self.target, "title": self.title,
            "detail": self.detail,
        }
        for key in _SERVEDANCE:
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
        endeavour_id=data.get("endeavour_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_servedance(data))


# ---------------------------------------------------------------------
# The held view: which campaigns a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class EndeavourView:
    """A view over the book: every endeavour, the green, the rest."""

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
        for key in _SERVEDANCE:
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
        for key in _SERVEDANCE:
            record[key] = getattr(self, key)
        return record


def _check_view_ref(value: Any) -> EndeavourView:
    if not isinstance(value, EndeavourView):
        raise ValueError("a view must be an EndeavourView")
    return value


def validate_view(view: Any) -> EndeavourView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> EndeavourView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, EndeavourView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an EndeavourView")
    _needed(data, _VIEW_KEYS, "a view")
    return EndeavourView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_servedance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class EndeavourPanelRow:
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


def _row_for_endeavour(endeavour: EndeavourRecord,
                     source: Any = None) -> EndeavourPanelRow:
    return EndeavourPanelRow(
        item_id=endeavour.endeavour_id,
        standing="complete" if endeavour_green(endeavour, source) else "open",
        label=endeavour.title, segment=segment_of(endeavour, source),
        recorded_on=endeavour.recorded_on)


def _check_row_ref(value: Any) -> EndeavourPanelRow:
    if not isinstance(value, EndeavourPanelRow):
        raise ValueError("a panel row must be an EndeavourPanelRow")
    return value


def validate_row(row: Any, endeavour: Any = None,
                 source: Any = None) -> EndeavourPanelRow:
    matched = _check_row_ref(row)
    if endeavour is not None:
        derived = _row_for_endeavour(_check_endeavour_ref(endeavour), source)
        if matched != derived:
            raise ValueError(
                f"panel row {matched.item_id!r} does not agree with "
                f"the row derived from its endeavour")
    return matched


def build_row(row: Any = None, endeavour: Any = None,
              source: Any = None,
              **kwargs: Any) -> EndeavourPanelRow:
    if endeavour is not None:
        derived = _row_for_endeavour(_check_endeavour_ref(endeavour), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            EndeavourPanelRow(**kwargs))
        return validate_row(built, endeavour, source)
    if isinstance(row, EndeavourPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return EndeavourPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on campaign"))
    if row is None and kwargs:
        return EndeavourPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an EndeavourPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[EndeavourPanelRow, ...]
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
        f"The endeavour book holds {total_items} endeavours as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown endeavours "
        f"stand complete.",
        "Rows stand in held endeavour, the endeavour the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its endeavour's own fields "
        "- the campaign it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any endeavour.",
        "Completeness is grained from the held records alone: "
        "a endeavour that steps outside the endeavour sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not scoped served stands open, named in its "
        "gaps, and the endeavour index is derived from the "
        "held endeavours, never stored where it could drift.",
    )

@dataclass(frozen=True)
class EndeavourPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[EndeavourPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> EndeavourView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, EndeavourView):
        return view
    return book.view_for(view)


def shown_endeavours(source: Any, view: Any = None
                   ) -> Tuple[EndeavourRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.endeavours
    if resolved.view_filter == "complete":
        return tuple(g for g in book.endeavours if endeavour_green(g, book))
    return tuple(g for g in book.endeavours if not endeavour_green(g, book))


def endeavours_for_campaign(source: Any, campaign_id: Any
                      ) -> Tuple[EndeavourRecord, ...]:
    wanted = _clean_text(campaign_id, "an campaign id")
    return tuple(
        g for g in _source_book(source).endeavours if g.campaign_id == wanted)


def green_endeavours(source: Any) -> Tuple[EndeavourRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.endeavours if endeavour_green(g, book))


def current_endeavour(source: Any) -> Optional[EndeavourRecord]:
    """The book's current endeavour, DERIVED at call time.

    The first held endeavour, in held endeavour, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held endeavours alone, so it can
    never go stale against them. A book whose every
    endeavour stands complete has no current endeavour.
    """
    book = _source_book(source)
    for endeavour in book.endeavours:
        if not endeavour_green(endeavour, book):
            return endeavour
    return None


def derive_panel(source: Any, view: Any = None) -> EndeavourPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_endeavours(book, resolved)
    rows = tuple(_row_for_endeavour(endeavour, book) for endeavour in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.endeavours), default="")
    green = sum(1 for g in shown if endeavour_green(g, book))
    return EndeavourPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.endeavours), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.endeavours), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> EndeavourPanel:
    if not isinstance(value, EndeavourPanel):
        raise ValueError("a panel must be an EndeavourPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> EndeavourPanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 endeavour).
    """
    matched = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(matched.view_id)
                if matched.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(matched, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {matched.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return matched


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> EndeavourPanel:
    if isinstance(panel, EndeavourPanel):
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
        built = EndeavourPanel(
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
    raise ValueError("a panel must be a mapping, an EndeavourPanel, or derived")


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
        return "served"
    if green_shown == 0:
        return "blocked"
    return "held"


@dataclass(frozen=True)
class EndeavourVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> EndeavourVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_endeavours(book, resolved)
    green = sum(1 for g in shown if endeavour_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return EndeavourVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> EndeavourVerdict:
    if not isinstance(value, EndeavourVerdict):
        raise ValueError("a verdict must be an EndeavourVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> EndeavourVerdict:
    matched = _check_verdict_ref(verdict)
    if matched.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {matched.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(matched.view_id)
                if matched.view_id is not None else None)
        derived = derive_verdict(book, view)
        if matched != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return matched


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> EndeavourVerdict:
    if isinstance(verdict, EndeavourVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = EndeavourVerdict(
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
        "a verdict must be a mapping, an EndeavourVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held campaigns' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEndeavour:
    stage: str
    endeavour_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "stage": self.stage, "endeavour_id": self.endeavour_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class EndeavourIndex:
    """The endeavour index, derived from the held endeavours.

    The index names one endeavour per green endeavour, in
    held endeavour - the endeavour's own one verifiable
    stage, its endeavour id and its title - and the
    endeavours that do not stand complete, named in its
    gaps. Nothing here is stored on any endeavour: the
    index is derived at call time from the held
    records alone, so it can never drift from them.
    """

    endeavours: Tuple[IndexEndeavour, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "endeavours": [e.to_record() for e in self.endeavours],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> EndeavourIndex:
    """Derive the endeavour index from the book's held endeavours."""
    book = _source_book(source)
    endeavours = tuple(
        IndexEndeavour(stage=g.stage, endeavour_id=g.endeavour_id,
                   title=g.title)
        for g in book.endeavours if endeavour_green(g, book))
    gaps = tuple(
        g.endeavour_id for g in book.endeavours if not endeavour_green(g, book))
    return EndeavourIndex(endeavours=endeavours, gaps=gaps)


def endeavour_for_check(source: Any, stage: Any) -> Optional[EndeavourRecord]:
    """The first held endeavour one stage reaches, or none - honestly."""
    if stage is None:
        return None
    if not isinstance(stage, str):
        raise ValueError("an stage must be a string naming the stage")
    wanted = stage.strip()
    if not wanted:
        return None
    for endeavour in _source_book(source).endeavours:
        if endeavour.stage == wanted:
            return endeavour
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held endeavour: the endeavour
    that took it and the step it took, before,
    then after. A book whose endeavours all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{endeavour_id}: {step}"
        for endeavour_id, steps in _breaks_map(book).items()
        for step in steps)

def endeavour_endeavour(source: Any,
              campaign_id: Any = None) -> Tuple[EndeavourRecord, ...]:
    """The held endeavours in their held endeavour, DERIVED at call time.

    Endeavours stand in the endeavour the book holds them -
    the endeavour their campaigns were taken - optionally
    for one campaign alone. Nothing here is stored:
    the endeavour is the book's own held endeavour, told.
    """
    book = _source_book(source)
    endeavours = list(book.endeavours)
    if campaign_id is not None:
        wanted = _clean_text(campaign_id, "a campaign id")
        endeavours = [r for r in endeavours if r.campaign_id == wanted]
    return tuple(endeavours)

def trace_of(source: Any, endeavour_id: Any) -> str:
    """One endeavour's trace, DERIVED at call time.

    The endeavour's walked stages joined as one trace
    line, in walk endeavour. A endeavour that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is named
    elsewhere.
    """
    endeavour = _source_book(source).endeavour_for(endeavour_id)
    return " > ".join(endeavour.stages)

def trace_for_endeavour(source: Any,
                  endeavour_id: Any) -> Optional[TraceRecord]:
    """The held trace for one endeavour, or none - honestly."""
    wanted = _clean_text(endeavour_id, "a endeavour id")
    for record in _source_book(source).traces:
        if record.endeavour_id == wanted:
            return record
    return None

def trace_current(source: Any, endeavour_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_endeavour(source, endeavour_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, endeavour_id)

def note_for_endeavour(source: Any, endeavour_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one endeavour (and stance, when named)."""
    wanted = _clean_text(endeavour_id, "a endeavour id")
    for record in _source_book(source).notes:
        if record.endeavour_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the campaign targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def ledger_record(source: Any = None) -> Dict[str, Any]:
    """The endeavour ledger, DERIVED here from the held endeavours alone.

    The ledger counts the held endeavours by their
    derived completeness - green and red - names
    the current endeavour, the first that does not yet
    stand complete, tells each held endeavour's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held endeavours took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.endeavours
            if ("complete" if endeavour_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "endeavour_records": number})
    current = current_endeavour(book)
    traces = []
    for endeavour in book.endeavours:
        trace = trace_for_endeavour(book, endeavour.endeavour_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, endeavour.endeavour_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"endeavour_id": endeavour.endeavour_id, "trace": standing})
    return {
        "type": "endeavour_well",
        "campaign": ENDEAVOUR_SLICE,
        "standings": standings,
        "total": len(book.endeavours),
        "current_endeavour": current.endeavour_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This campaign's own roadmap standing, proved from the roadmap itself.

    The record loads this campaign's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 campaigns in 11 parts,
    the scoped prefix, the next campaign where the
    endeavour endeavours, and M-228's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(ENDEAVOUR_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "endeavour_roadmap",
        "campaign": ENDEAVOUR_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m228_title": own.title,
        "m228_part": own.part,
        "m228_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: campaigns, endeavours, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or endeavour ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class EndeavourBook:
    title: str
    campaigns: Tuple[CampaignRef, ...] = ()
    endeavours: Tuple[EndeavourRecord, ...] = ()
    views: Tuple[EndeavourView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[EndeavourPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        campaigns = tuple(_check_campaign_ref(g) for g in self.campaigns)
        endeavours = tuple(_check_endeavour_ref(g) for g in self.endeavours)
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
        endeavour_ids = set()
        endeavour_seqs = set()
        for endeavour in endeavours:
            if endeavour.endeavour_id in endeavour_ids:
                raise ValueError(
                    f"two endeavours stand under id {endeavour.endeavour_id!r}")
            if endeavour.seq in endeavour_seqs:
                raise ValueError(
                    f"two endeavours stand at sequence {endeavour.seq}")
            endeavour_ids.add(endeavour.endeavour_id)
            endeavour_seqs.add(endeavour.seq)
        by_slice = {ref.campaign_id: ref for ref in campaigns}
        for endeavour in (endeavours if campaigns else ()):

            ref = by_slice.get(endeavour.campaign_id)
            if ref is None:
                raise ValueError(
                    f"endeavour {endeavour.endeavour_id!r} is held from campaign "
                    f"{endeavour.campaign_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "live":
                raise ValueError(
                    f"endeavour {endeavour.endeavour_id!r} is held from campaign "
                    f"{endeavour.campaign_id!r}, which is not active: "
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
            target = (record.endeavour_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for endeavour "
                    f"{record.endeavour_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per endeavour target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_endeavours = set()
        endeavour_ids = {endeavour.endeavour_id for endeavour in endeavours}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.endeavour_id in trace_endeavours:
                raise ValueError(
                    f"two traces stand for endeavour "
                    f"{record.endeavour_id!r}: one trace stands "
                    f"per endeavour walk")
            if endeavours and record.endeavour_id not in endeavour_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces endeavour "
                    f"{record.endeavour_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_endeavours.add(record.endeavour_id)
        object.__setattr__(
            self, "campaigns", tuple(sorted(campaigns, key=lambda g: g.seq)))
        object.__setattr__(
            self, "endeavour_records", tuple(sorted(endeavours, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.endeavours + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.endeavour_id for g in self.endeavours) + tuple(
            v.view_id for v in self.views)

    def endeavour_ids(self) -> Tuple[str, ...]:
        return tuple(g.endeavour_id for g in self.endeavours)

    def campaign_ids(self) -> Tuple[str, ...]:
        return tuple(g.campaign_id for g in self.campaigns)

    def endeavour_for(self, endeavour_id: Any) -> EndeavourRecord:
        wanted = _clean_text(endeavour_id, "a endeavour id")
        for endeavour in self.endeavours:
            if endeavour.endeavour_id == wanted:
                return endeavour
        raise KeyError(f"no endeavour named {wanted!r} stands in this book")

    def slice_for(self, campaign_id: Any) -> CampaignRef:
        wanted = _clean_text(campaign_id, "an campaign id")
        for ref in self.campaigns:
            if ref.campaign_id == wanted:
                return ref
        raise KeyError(f"no campaign named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> EndeavourView:
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
        for endeavour in self.endeavours:
            if endeavour.endeavour_id == wanted:
                return endeavour
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "campaigns": [g.to_record() for g in self.campaigns],
            "endeavour_records": [g.to_record() for g in self.endeavours],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: EndeavourBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: EndeavourBook) -> None:
    if book.title != "Team-of-one scaling at the M-228 slice run":
        raise ValueError("the shipped example book carries another title")
    if len(book.campaigns) != 3 or len(book.endeavours) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three campaign references, five endeavours and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m227-campaign":
        raise ValueError("the pinned panel is panel-m227-campaign")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.stage for e in index.endeavours] != ["served", "served", "served"]:
        raise ValueError("the shipped example book index must derive the three held complete endeavours in held endeavour")
    if index.gaps != ("endeavour-bare-endeavour", "endeavour-leaping-endeavour"):
        raise ValueError("the shipped example book must leave the bare and leaping endeavours honestly open, named in its gaps")
    found = endeavour_for_check(book, EXAMPLE_STAGE)
    if found is None or found.endeavour_id != "endeavour-held-endeavour":
        raise ValueError("the shipped example book must reach its opening endeavour under the example stage")
    if trace_of(book, "endeavour-held-endeavour") != "scoped > sized > grained > matched > served":
        raise ValueError("the shipped example book must derive the opening endeavour's trace from its walked steps")
    if not trace_current(book, "endeavour-held-endeavour"):
        raise ValueError("the shipped example book must hold the opening endeavour's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note endeavour")

def validate_book(data: Any, *, require_example: bool = False) -> EndeavourBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, EndeavourBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a endeavour book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live campaign build or execution "
                f"({key!r} is named on it): {ENDEAVOUR_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its endeavours under a view")
    if "endeavour_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held endeavours at call time")
    if "ledger" in data or "current_endeavour" in data:
        raise ValueError(
            "a book stores no ledger and no current endeavour: both are "
            "derived from its held endeavours at call time")
    if "trace" in data or "endeavour" in data:
        raise ValueError(
            "a book stores no trace and no endeavour: both are derived "
            "from its held endeavours at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != ENDEAVOUR_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{ENDEAVOUR_SCHEMA!r}")
    if data.get("campaign") is not None and (
            data["campaign"] != ENDEAVOUR_SLICE):
        raise ValueError(
            f"a book's campaign must be {ENDEAVOUR_SLICE!r}")
    head = data.get("endeavour_head") or data.get("team_scaling") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's endeavour head must be a mapping")
    title = head.get("title") or data.get("title")
    campaigns = tuple(build_campaign_ref(g) for g in data.get("campaigns") or ())
    endeavours = tuple(build_endeavour(g) for g in data.get("endeavour_records") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = EndeavourBook(
        title=title, campaigns=campaigns, endeavours=endeavours, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = EndeavourBook(
        title=book.title, campaigns=book.campaigns, endeavours=book.endeavours,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> EndeavourBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (EndeavourBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an EndeavourBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> EndeavourBook:
    return validate_book(data, require_example=require_example)


def load_endeavour(
        data: Optional[Dict[str, Any]] = None) -> EndeavourBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(ENDEAVOUR_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_endeavour_file(path: Any) -> EndeavourBook:
    """Load one endeavour file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: campaign references, endeavours and views held one by one.
# ---------------------------------------------------------------------

class EndeavourRegistry:
    """An in-memory holding of campaign references, endeavours and views.

    The registry is the pure layer's model of a
    session's endeavour book: campaign references are
    held under their ids, endeavours are held under
    their ids, one endeavour per id and per sequence,
    and views are held in sized endeavour, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[CampaignRef] = []
        self._endeavours: List[EndeavourRecord] = []
        self._views: List[EndeavourView] = []
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
        """Hold one campaign reference, grained whole before held."""
        matched = _check_campaign_ref(item)
        return self._register(
            self._slices, matched, "campaign_id", "campaign reference")

    def register_endeavour(self, item: Any) -> EndeavourRecord:
        """Hold one endeavour, grained whole before held."""
        matched = _check_endeavour_ref(item)
        return self._register(
            self._endeavours, matched, "endeavour_id", "endeavour")

    def register_view(self, view: Any) -> EndeavourView:
        """Hold one view; a view naming no id takes a fresh one."""
        matched = _check_view_ref(view)
        if not matched.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            matched = build_view({**matched.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, matched, "view_id", "view")

    def register_book(self, book: Any) -> EndeavourBook:
        """Hold a whole book's records, under its title."""
        matched = build_book(book)
        if self._title is not None and matched.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {matched.title!r}")
        for ref in matched.campaigns:
            self.register_campaign_ref(ref)
        for endeavour in matched.endeavours:
            self.register_endeavour(endeavour)
        for view in matched.views:
            self.register_view(view)
        self._title = matched.title
        return self.book()

    def book(self) -> EndeavourBook:
        return EndeavourBook(
            title=self._title or "An unheld endeavour book",
            campaigns=tuple(self._slices), endeavours=tuple(self._endeavours),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[CampaignRef, ...]:
        return tuple(self._slices)

    def list_endeavours(self) -> Tuple[EndeavourRecord, ...]:
        return tuple(self._endeavours)

    def list_views(self) -> Tuple[EndeavourView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._endeavours) + tuple(self._views)

    def get_slice(self, campaign_id: Any) -> CampaignRef:
        return self.book().slice_for(campaign_id)

    def get_endeavour(self, endeavour_id: Any) -> EndeavourRecord:
        return self.book().endeavour_for(endeavour_id)

    def get_view(self, view_id: Any) -> EndeavourView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the ledger target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> EndeavourBook:
    if source is None:
        return load_endeavour()
    if isinstance(source, EndeavourBook):
        return source
    if isinstance(source, EndeavourRegistry):
        return source.book()
    return build_book(source)


def _servedance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _SERVEDANCE}


def endeavour_record(endeavour: Any, source: Any = None) -> Dict[str, Any]:
    matched = _check_endeavour_ref(endeavour)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "endeavour_endeavour",
        "campaign": ENDEAVOUR_SLICE,
        "endeavour_id": matched.endeavour_id,
        "campaign_id": matched.campaign_id,
        "title": matched.title,
        "segment": segment_of(matched, book),
        "complete": endeavour_green(matched, book),
        "gaps": list(endeavour_gaps(matched, book)),
    }
    record.update(_servedance_record(matched))
    return record


def campaign_record(ref: Any) -> Dict[str, Any]:
    matched = _check_campaign_ref(ref)
    record = {
        "type": "endeavour_run",
        "campaign": ENDEAVOUR_SLICE,
        "campaign_id": matched.campaign_id,
        "title": matched.title,
        "state": matched.state,
    }
    record.update(_servedance_record(matched))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    matched = _check_trace_ref(record_in)
    record = {
        "type": "endeavour_trace",
        "campaign": ENDEAVOUR_SLICE,
        "trace_id": matched.trace_id,
        "endeavour_id": matched.endeavour_id,
        "trace": matched.trace,
    }
    record.update(_servedance_record(matched))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    matched = _check_view_ref(view)
    record = {
        "type": "endeavour_view",
        "campaign": ENDEAVOUR_SLICE,
        "view_id": matched.view_id, "seq": matched.seq,
        "view_filter": matched.view_filter,
    }
    record.update(_servedance_record(matched))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    matched = _check_note_ref(record_in)
    record = {
        "type": "endeavour_note",
        "campaign": ENDEAVOUR_SLICE,
        "note_id": matched.note_id,
        "endeavour_id": matched.endeavour_id,
        "stance": matched.stance,
    }
    record.update(_servedance_record(matched))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    matched = validate_panel(panel, source)
    record = {"type": "endeavour_panel",
              "campaign": ENDEAVOUR_SLICE}
    record.update(matched.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, EndeavourVerdict):
        matched = validate_verdict(verdict, source)
    else:
        matched = derive_verdict(_source_book(verdict), view)
    record = {"type": "endeavour_verdict",
              "campaign": ENDEAVOUR_SLICE}
    record.update(matched.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, EndeavourIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "endeavour_index",
              "campaign": ENDEAVOUR_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    matched = _source_book(book)
    record = {"type": "endeavour_book",
              "campaign": ENDEAVOUR_SLICE,
              "title": matched.title}
    record.update(matched.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(endeavour: Any, source: Any = None) -> str:
    matched = _check_endeavour_ref(endeavour)
    return (
        f"{matched.title} - from {matched.campaign_id}: "
        f"stage {matched.stage if matched.stage else 'none'}, "
        f"claims "
        f"{', '.join(matched.claims) if matched.claims else 'none'}. "
        f"{matched.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The endeavours stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"endeavours stand complete.")


def view_plain_words(view: Any) -> str:
    matched = _check_view_ref(view)
    return f"View {matched.view_id}: shows {matched.view_filter} endeavours."


def note_plain_words(record_in: Any) -> str:
    matched = _check_note_ref(record_in)
    return (
        f"Note {matched.note_id}: {matched.stance} "
        f"{matched.endeavour_id}, toward {matched.target}. "
        f"{matched.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, EndeavourIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.endeavours)} green endeavours; "
        f"red, named in its gaps: {gaps}.")

def format_endeavour(endeavour: Any, source: Any = None) -> str:
    matched = _check_endeavour_ref(endeavour)
    book = _source_book(source) if source is not None else None
    lines = [f"{matched.title} ({matched.endeavour_id})"]
    lines.extend(plain_lines(matched))
    lines.append(matched.detail)
    if endeavour_green(matched, book):
        lines.append(
            "This endeavour stands complete - it walked the question "
            "sequence in the open from scoped to served, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This endeavour stands open - it stands named in "
            f"its gaps: {', '.join(endeavour_gaps(matched, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    matched = _check_view_ref(view)
    return (
        f"View {matched.view_id}: filter {matched.view_filter} - "
        f"{matched.detail}")


def format_note(record_in: Any) -> str:
    matched = _check_note_ref(record_in)
    lines = [
        f"Endeavour note {matched.stance} {matched.endeavour_id} "
        f"({matched.note_id}): {matched.title}. {matched.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_stage(source: Any, stage: Any) -> str:
    endeavour = endeavour_for_check(source, stage)
    if endeavour is not None:
        return format_endeavour(endeavour, source)
    wanted = stage.strip() if isinstance(stage, str) else stage
    return (
        f"No held endeavour stands under stage {wanted!r} yet - the "
        f"stage reaches nothing in this book, and no endeavour is "
        f"invented for it.")


def format_book(source: Any = None, campaign_id: Any = None) -> str:
    book = _source_book(source)
    endeavours = (endeavours_for_campaign(book, campaign_id)
              if campaign_id is not None else book.endeavours)
    lines = [f"The Endeavour Gate (M-228) - {book.title}"]
    lines.extend(segment_of(endeavour, book) for endeavour in endeavours)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Endeavour panel under view {panel.view_id}:"]
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
    lines = ["Endeavour index, derived from the held endeavours:"]
    for endeavour in index.endeavours:
        lines.append(f"{endeavour.stage} - {endeavour.title} ({endeavour.endeavour_id})")
    if index.gaps:
        lines.append(
            "Red, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_endeavour_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Endeavour Gate (M-228)",
        f"{book.title}: {len(book.endeavours)} endeavours held, "
        f"{len(green_endeavours(book))} endeavours standing green, "
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


def parse_endeavour_args(args: Any) -> Tuple[str, Any]:
    """Parse the /endeavour grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("endeavour", "view", "note"):
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
