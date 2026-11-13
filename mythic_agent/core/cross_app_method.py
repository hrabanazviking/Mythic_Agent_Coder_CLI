"""Cross-app method (roadmap slice M-231).

Part IX - The Mythic Method Engine. The roadmap
words: **campaigns can name slices that live in other tools (a Samtal slice, a Sagnaskemma slice) as tracked externals — the forge sees Volmarr's whole workshop.******

What already ships, and what this campaign adds:

* The externals book already ships as data
  (M-201, ``core/milestones.py``): a roadmap/external
  file (parts, campaigns, acceptance stages, state) the
  app reads. This campaign WIRES the book that book's
  book invites - several externals held across
  campaigns with one ledger over them - as data, in its
  own module, standing in the M-195 copy-and-share
  book book the M-231 book stands in: one tracker
  per book, and the tracker's charge over one
  external across its campaign held as a book - a
  external. The shipped externals stand untouched behind
  their seams: this layer holds externals as data
  over the book's campaigns and rewrites none of them,
  and the externals book keeps its own standing.
  Externals stand on the ledger AS DATA alone: a
  external carries a ledger ref, a reference held in
  this book; holding, viewing or telling a external
  campaigns no external live, moves no keeper and files
  nothing.
* No charter row names this campaign: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-231 on no row, and the
  campaign tests pin that absence live. The M-005
  method charter names no campaign row either: its
  own words name the whole of Part IX as the
  part that executes the charter, and this campaign
  is built to the roadmap words and that
  execution note together.

* A external is held whole: the campaign it
  answers for, named by its campaign id; its title;
  the external steps it walked, held as data in
  walk external; and the evidence it carries, held
  as data by campaign. The external walk is EXPLICIT:
  its sequence stands as data
  (:data:`STAGES`, :data:`TRANSITIONS`) -
  named, linked, verified, tracked, held -
  and a external's standing is DERIVED at
  call time from its held steps and evidence
  alone: a external that opens anywhere but
  named, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet named held stands
  open, named in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - tool_ref,
  slice_ref, link_ref, status_ref, external_ref, evidence
  a tracker can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A external is
  tracked from held evidence alone, never
  from a feeling: a external holding a
  bare claim stands open, named in its gaps.
* A external stands only for an ACTIVE
  campaign. The book holds each campaign it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  external naming a campaign that stands
  nowhere in the book refuses BY NAME, and a
  external for a campaign that is not active
  refuses BY NAME beside it: the tracker deals with
  the campaign in hand, in roadmap external, never a
  queued one, and a campaign whose external already
  stands complete is never verified twice - the
  current external is derived, so a
  completed campaign is never the current external
  twice.
* The external's trace is visible. A trace
  record holds one external's walked steps
  as one trace line, exactly as walked, beside
  the external. The derived trace is
  computed at call time from the external's
  held steps; a held trace that no longer agrees
  with it stands stale, named in the ledger - the
  trace is the walk itself, never a retelling
  of it.
* The external index is DERIVED at call
  time from the held externals - one external
  per complete external, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, external or current-external
  claim on any record refuses by name.
* The current external is DERIVED at call
  time - the first held external, in held
  external, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its external, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per external stance; holding
  a note posts none of it, the rule stands as
  data (:data:`EXTERNAL_RULE`), and a record
  claiming a external was actually held,
  captured or promoted live refuses BY NAME.
  The tracker externals - and those externals, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the book a real external
  file takes, a loader reads a file anywhere on
  disk, externals and views are linked as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a external book for a session and
  telling from it. This layer reaches no live
  external: it writes no external live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no tracker, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds externals
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The external walk is explicit.** A
  external is tracked against the held
  steps and legal steps alone; an illegal step
  stands named in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  external that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, named in its gaps:
  a external is tracked from evidence, not
  vibes.
* **Active campaigns only, in roadmap external.** A
  external for a missing or queued campaign
  refuses by name; no external is invented
  for a campaign the tracker has not linked with.
* **Unknown stays unknown.** A external
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, external
  and current external are derived, never
  stored.** Each is derived from the held
  externals at call time; a stored one
  refuses by name, so it can never drift.
* **One external per external.** Two
  externals standing for one external id
  refuse by name, and one note record stands per
  external stance.
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
    "EXTERNAL_RESOURCE",
    "EXTERNAL_SCHEMA",
    "EXTERNAL_SLICE",
    "EXTERNAL_RULE",
    "PLAIN_EXPLANATION",
    "THE_EXTERNAL_SLICE",
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
    "ExternalRecord",
    "IndexExternal",
    "CampaignRef",
    "NoteRecord",
    "ExternalBook",
    "ExternalIndex",
    "ExternalPanel",
    "ExternalPanelRow",
    "ExternalRegistry",
    "ExternalVerdict",
    "ExternalView",
    "TargetCount",
    "trace_for_external",
    "trace_record",
    "ledger_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_external",
    "build_campaign_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_external",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "external_for_check",
    "external_external",
    "external_record",
    "first_note",
    "format_book",
    "format_external",
    "format_index",
    "format_note",
    "format_stage",
    "format_panel",
    "format_external_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "campaign_record",
    "load_external",
    "load_external_file",
    "normalize_campaign_state",
    "normalize_stage",
    "normalize_claim_kind",
    "legal_step",
    "next_stage",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_external",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_external_args",
    "green_externals",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_externals",
    "validate_trace",
    "validate_book",
    "validate_external",
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
    "external_gaps",
    "external_green",
    "externals_for_campaign",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

EXTERNAL_SCHEMA = "mythic.cross_app_method/1"
EXTERNAL_SLICE = "M-231"
THE_EXTERNAL_SLICE = EXTERNAL_SLICE
EXTERNAL_RESOURCE = "cross_app_method.yaml"
INDEX_ACTION = "index"
EXAMPLE_STAGE = "held"
STAGE_FIELDS = ("stages", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("held", "held", "blocked")
CAMPAIGN_STATES = ("live", "dormant")
EXTERNAL_RULE = "externals are held as data alone: campaigns name slices that live in other tools as tracked externals, trackers per external, and the human sees the whole workshop at a campaign - an external stands as data, held by reference (an external ref), never fetched live - the external walk stands as an explicit external sequence - named, linked, verified, tracked, held - and an external completes only complete, complete being a state with evidence held - tool ref, slice ref, link ref, status ref, external ref - never a feeling, a memory, an assertion or a summary; campaigns can name slices that live in other tools (a Samtal slice, a Sagnaskemma slice) as tracked externals - the forge sees Volmarr's whole workshop - and an external tracked without verifying, or held before it is tracked, stands open, named in its gaps; holding, viewing and telling an external starts no work live, assigns no tracker, spends nothing, spawns no process and opens no network"
PLAIN_EXPLANATION = "Cross-app method (M-231): campaigns can name slices that live in other tools (a Samtal slice, a Sagnaskemma slice) as tracked externals — the forge sees Volmarr's whole workshop."
USAGE = 'Usage: /crossapp | /crossapp external <external-id> | /crossapp stage <stage> | /crossapp campaign <campaign-id> | /crossapp view <view-id> | /crossapp note <note-id> | /crossapp index | /crossapp panel | /crossapp verdict'

STAGES = ("named", "linked", "verified", "tracked", "held")
HELD_EVIDENCE = ("tool_ref", "slice_ref", "link_ref", "status_ref", "external_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "named": ("linked",),
    "linked": ("verified",),
    "verified": ("tracked",),
    "tracked": ("named", "held"),
    "held": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a external or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a external stands complete.
    A stage outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_stage(stage: Any, failed: Any = False) -> Optional[str]:
    """The step the tracker takes next, DERIVED from the sequence.

    Banked leads to linked and linked to
    verified; verified leads to tracked; at
    tracked a follow-up banking steps back to named and a finished external steps to held;
    held is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    tracked = normalize_stage(stage)
    if tracked == "named":
        return "linked"
    if tracked == "linked":
        return "verified"
    if tracked == "verified":
        return "tracked"
    if tracked == "tracked":
        return "named" if failed else "held"
    return None


_HELDANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "external_id", "seq", "campaign_id", "title", "stages",
    "claims", "detail",
} | set(_HELDANCE))
_SLICE_REF_KEYS = frozenset({
    "campaign_id", "seq", "title", "state", "detail",
} | set(_HELDANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "external_id", "trace", "detail",
} | set(_HELDANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_HELDANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "external_id", "stance", "target", "title",
    "detail",
} | set(_HELDANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "externals", "coverage", "covered", "uncovered",
    "current_external", "next_external", "progress", "ledger",
    "current", "external", "breaks", "live"})
_LIVE_KEYS = (
    "live_external", "externals_live", "live_question",
    "externals_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "externals_live",
    "resumed_live", "runs_external", "paused_live",
    "runs_external", "ran_external", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "external_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_external", "sent_external",
    "posts_note", "held_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_external", "filed_live", "spawns_tracker", "spawned_tracker", "sends_external", "sent_external", "writes_external", "wrote_external")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_stages(value: Any) -> Tuple[str, ...]:
    """A external's walked stages, held as data.

    The stages stand as a list of stage names in
    walk external, each one a stage of the explicit
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
    """A external's asked claims: claim campaigns named as data.

    Each claim names one campaign from the held
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


def _heldance(mapping: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key in _HELDANCE:
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
                f"{what} claims a live gate external or campaign build "
                f"execution ({key!r} is named on it): "
                f"{EXTERNAL_RULE}")
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
# The held external: one campaign cut from an active campaign.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ExternalRecord:
    """One external campaign, held as data.

    The external names the active campaign it was
    held from, by campaign id, its title, its
    verifiable stages, held as data, and its
    claims, named by external id. The grain is
    derived, never stored: exactly one verifiable
    walk is verified against the machine. A external whose
    stages are not yet held stands with its
    stages empty: it stands open, named in
    its gaps, and no stage is invented for it.
    The external is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    external_id: str
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
            self, "external_id", _clean_text(self.external_id, "a external id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "campaign_id", _clean_text(self.campaign_id, "an campaign id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a external title"))
        object.__setattr__(
            self, "stages", _check_stages(self.stages))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a external detail"))
        for key in _HELDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.external_id

    @property
    def stage(self) -> str:
        """The stage the external stands at: its last walked stage."""
        return self.stages[-1] if self.stages else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "external_id": self.external_id, "seq": self.seq,
            "campaign_id": self.campaign_id, "title": self.title,
            "stages": list(self.stages),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _HELDANCE:
            record[key] = getattr(self, key)
        return record


def _check_external_ref(value: Any) -> ExternalRecord:
    if not isinstance(value, ExternalRecord):
        raise ValueError("a external must be a ExternalRecord")
    return value


def validate_external(external: Any) -> ExternalRecord:
    return _check_external_ref(external)


def build_external(record: Any = None, **kwargs: Any) -> ExternalRecord:
    """Build one held external from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, ExternalRecord):
        if kwargs:
            raise ValueError("a external stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a external must be a mapping or a ExternalRecord")
    _needed(data, _RUN_KEYS, "a external")
    return ExternalRecord(
        external_id=data.get("external_id"), seq=data.get("seq"),
        campaign_id=data.get("campaign_id"), title=data.get("title"),
        stages=data.get("stages"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_heldance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each external to the steps it took outside the machine.

    Derived from the held externals alone: a break is
    one consecutive pair of walked stages the
    explicit gate sequence does not allow, told
    in walk external as before, then after.
    """
    found: Dict[str, Tuple[str, ...]] = {}
    for external in book.externals:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(external.stages, external.stages[1:])
            if not legal_step(before, after))
        if breaks:
            found[external.external_id] = breaks
    return found

def external_gaps(external: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a external from standing complete.

    Guarded from the external's own held fields alone -
    its walked steps against the explicit question
    sequence, and its held evidence against the
    held vocabulary: the external opens at
    named, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a external stands complete only when it has
    named held. The source names nothing
    further: no gap is borrowed from another
    external.
    """
    tracked = _check_external_ref(external)
    gaps: List[str] = []
    if not tracked.stages:
        gaps.append(
            "has passed through no step: the external has not started")
        return tuple(gaps)
    if tracked.stages[0] != "named":
        gaps.append(
            f"opens at {tracked.stages[0]}, not at named: "
            f"the external opens with the reflection")
    for before, after in zip(tracked.stages, tracked.stages[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"external sequence does not allow")
    for campaign in tracked.claims:
        if campaign in BARE_CLAIMS:
            gaps.append(
                f"carries a {campaign} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if tracked.stages[-1] != "held":
        gaps.append(
            f"has not reached held: the external stands "
            f"at {tracked.stages[-1]}")
    return tuple(gaps)

def external_green(external: Any, source: Any = None) -> bool:
    return not external_gaps(external, source)


def plain_lines(external: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the external's own fields."""
    tracked = _check_external_ref(external)
    return (
        f"External: {tracked.title}",
        f"Campaign: {tracked.campaign_id}",
        f"Stage: {tracked.stage if tracked.stage else 'none'}",
        f"Claims: "
        f"{', '.join(tracked.claims) if tracked.claims else 'none'}",
    )


def segment_of(external: Any, source: Any = None) -> str:
    tracked = _check_external_ref(external)
    gaps = external_gaps(tracked, source)
    return (
        f"{tracked.external_id}: {tracked.title} - campaign: "
        f"'{tracked.campaign_id}' - stage: "
        f"'{tracked.stage if tracked.stage else 'none'}' - "
        f"stages: {len(tracked.stages)} - claims: "
        f"'{', '.join(tracked.claims) if tracked.claims else 'none'}' - "
        f"detail: '{tracked.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held campaign reference: the active campaign a book externals from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CampaignRef:
    """One campaign a external book externals from, held as a reference.

    The record names the campaign, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 campaign book's own telling. A external
    stands only from an active reference: the
    book refuses a external naming no held reference,
    and a external from an queued one, BY NAME.
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
        for key in _HELDANCE:
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
        for key in _HELDANCE:
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
        **_heldance(data))


# ---------------------------------------------------------------------
# The held trace trace: the human approves the trace, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TraceRecord:
    """One trace trace, held as data.

    The record names its campaign and the trace the
    human active - the campaign's external ids in
    derived claim external, held exactly as
    active. The trace is of the set and its
    external, never of a step: when the derived
    trace moves, this record stands stale, named
    in the ledger, until a new trace is active.
    """

    trace_id: str
    seq: int
    external_id: str
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
            self, "external_id", _clean_text(self.external_id, "an campaign id"))
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
            "external_id": self.external_id, "trace": self.trace,
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
        external_id=data.get("external_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a external, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One external stance, held as data.

    The record names its external, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per external stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    external_id: str
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
            self, "external_id", _clean_text(self.external_id, "a external id"))
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
            "external_id": self.external_id, "stance": self.stance,
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
        external_id=data.get("external_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The held view: which campaigns a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ExternalView:
    """A view over the book: every external, the green, the rest."""

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


def _check_view_ref(value: Any) -> ExternalView:
    if not isinstance(value, ExternalView):
        raise ValueError("a view must be an ExternalView")
    return value


def validate_view(view: Any) -> ExternalView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> ExternalView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, ExternalView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an ExternalView")
    _needed(data, _VIEW_KEYS, "a view")
    return ExternalView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_heldance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ExternalPanelRow:
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


def _row_for_external(external: ExternalRecord,
                     source: Any = None) -> ExternalPanelRow:
    return ExternalPanelRow(
        item_id=external.external_id,
        standing="complete" if external_green(external, source) else "open",
        label=external.title, segment=segment_of(external, source),
        recorded_on=external.recorded_on)


def _check_row_ref(value: Any) -> ExternalPanelRow:
    if not isinstance(value, ExternalPanelRow):
        raise ValueError("a panel row must be an ExternalPanelRow")
    return value


def validate_row(row: Any, external: Any = None,
                 source: Any = None) -> ExternalPanelRow:
    tracked = _check_row_ref(row)
    if external is not None:
        derived = _row_for_external(_check_external_ref(external), source)
        if tracked != derived:
            raise ValueError(
                f"panel row {tracked.item_id!r} does not agree with "
                f"the row derived from its external")
    return tracked


def build_row(row: Any = None, external: Any = None,
              source: Any = None,
              **kwargs: Any) -> ExternalPanelRow:
    if external is not None:
        derived = _row_for_external(_check_external_ref(external), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            ExternalPanelRow(**kwargs))
        return validate_row(built, external, source)
    if isinstance(row, ExternalPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return ExternalPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on campaign"))
    if row is None and kwargs:
        return ExternalPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an ExternalPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[ExternalPanelRow, ...]
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
        f"The external book holds {total_items} externals as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown externals "
        f"stand complete.",
        "Rows stand in held external, the external the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its external's own fields "
        "- the campaign it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any external.",
        "Completeness is verified from the held records alone: "
        "a external that steps outside the external sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not named held stands open, named in its "
        "gaps, and the external index is derived from the "
        "held externals, never stored where it could drift.",
    )

@dataclass(frozen=True)
class ExternalPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[ExternalPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> ExternalView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, ExternalView):
        return view
    return book.view_for(view)


def shown_externals(source: Any, view: Any = None
                   ) -> Tuple[ExternalRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.externals
    if resolved.view_filter == "complete":
        return tuple(g for g in book.externals if external_green(g, book))
    return tuple(g for g in book.externals if not external_green(g, book))


def externals_for_campaign(source: Any, campaign_id: Any
                      ) -> Tuple[ExternalRecord, ...]:
    wanted = _clean_text(campaign_id, "an campaign id")
    return tuple(
        g for g in _source_book(source).externals if g.campaign_id == wanted)


def green_externals(source: Any) -> Tuple[ExternalRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.externals if external_green(g, book))


def current_external(source: Any) -> Optional[ExternalRecord]:
    """The book's current external, DERIVED at call time.

    The first held external, in held external, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held externals alone, so it can
    never go stale against them. A book whose every
    external stands complete has no current external.
    """
    book = _source_book(source)
    for external in book.externals:
        if not external_green(external, book):
            return external
    return None


def derive_panel(source: Any, view: Any = None) -> ExternalPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_externals(book, resolved)
    rows = tuple(_row_for_external(external, book) for external in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.externals), default="")
    green = sum(1 for g in shown if external_green(g, book))
    return ExternalPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.externals), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.externals), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> ExternalPanel:
    if not isinstance(value, ExternalPanel):
        raise ValueError("a panel must be an ExternalPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> ExternalPanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 external).
    """
    tracked = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(tracked.view_id)
                if tracked.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(tracked, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {tracked.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return tracked


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> ExternalPanel:
    if isinstance(panel, ExternalPanel):
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
        built = ExternalPanel(
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
    raise ValueError("a panel must be a mapping, an ExternalPanel, or derived")


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
class ExternalVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> ExternalVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_externals(book, resolved)
    green = sum(1 for g in shown if external_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return ExternalVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> ExternalVerdict:
    if not isinstance(value, ExternalVerdict):
        raise ValueError("a verdict must be an ExternalVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> ExternalVerdict:
    tracked = _check_verdict_ref(verdict)
    if tracked.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {tracked.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(tracked.view_id)
                if tracked.view_id is not None else None)
        derived = derive_verdict(book, view)
        if tracked != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return tracked


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> ExternalVerdict:
    if isinstance(verdict, ExternalVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = ExternalVerdict(
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
        "a verdict must be a mapping, an ExternalVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held campaigns' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexExternal:
    stage: str
    external_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "stage": self.stage, "external_id": self.external_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class ExternalIndex:
    """The external index, derived from the held externals.

    The index names one external per green external, in
    held external - the external's own one verifiable
    stage, its external id and its title - and the
    externals that do not stand complete, named in its
    gaps. Nothing here is stored on any external: the
    index is derived at call time from the held
    records alone, so it can never drift from them.
    """

    externals: Tuple[IndexExternal, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "externals": [e.to_record() for e in self.externals],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> ExternalIndex:
    """Derive the external index from the book's held externals."""
    book = _source_book(source)
    externals = tuple(
        IndexExternal(stage=g.stage, external_id=g.external_id,
                   title=g.title)
        for g in book.externals if external_green(g, book))
    gaps = tuple(
        g.external_id for g in book.externals if not external_green(g, book))
    return ExternalIndex(externals=externals, gaps=gaps)


def external_for_check(source: Any, stage: Any) -> Optional[ExternalRecord]:
    """The first held external one stage reaches, or none - honestly."""
    if stage is None:
        return None
    if not isinstance(stage, str):
        raise ValueError("an stage must be a string naming the stage")
    wanted = stage.strip()
    if not wanted:
        return None
    for external in _source_book(source).externals:
        if external.stage == wanted:
            return external
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held external: the external
    that took it and the step it took, before,
    then after. A book whose externals all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{external_id}: {step}"
        for external_id, steps in _breaks_map(book).items()
        for step in steps)

def external_external(source: Any,
              campaign_id: Any = None) -> Tuple[ExternalRecord, ...]:
    """The held externals in their held external, DERIVED at call time.

    Externals stand in the external the book holds them -
    the external their campaigns were named - optionally
    for one campaign alone. Nothing here is stored:
    the external is the book's own held external, told.
    """
    book = _source_book(source)
    externals = list(book.externals)
    if campaign_id is not None:
        wanted = _clean_text(campaign_id, "a campaign id")
        externals = [r for r in externals if r.campaign_id == wanted]
    return tuple(externals)

def trace_of(source: Any, external_id: Any) -> str:
    """One external's trace, DERIVED at call time.

    The external's walked stages joined as one trace
    line, in walk external. A external that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is named
    elsewhere.
    """
    external = _source_book(source).external_for(external_id)
    return " > ".join(external.stages)

def trace_for_external(source: Any,
                  external_id: Any) -> Optional[TraceRecord]:
    """The held trace for one external, or none - honestly."""
    wanted = _clean_text(external_id, "a external id")
    for record in _source_book(source).traces:
        if record.external_id == wanted:
            return record
    return None

def trace_current(source: Any, external_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_external(source, external_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, external_id)

def note_for_external(source: Any, external_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one external (and stance, when named)."""
    wanted = _clean_text(external_id, "a external id")
    for record in _source_book(source).notes:
        if record.external_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the campaign targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def ledger_record(source: Any = None) -> Dict[str, Any]:
    """The external ledger, DERIVED here from the held externals alone.

    The ledger counts the held externals by their
    derived completeness - green and red - names
    the current external, the first that does not yet
    stand complete, tells each held external's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held externals took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.externals
            if ("complete" if external_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "external_records": number})
    current = current_external(book)
    traces = []
    for external in book.externals:
        trace = trace_for_external(book, external.external_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, external.external_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"external_id": external.external_id, "trace": standing})
    return {
        "type": "external_well",
        "campaign": EXTERNAL_SLICE,
        "standings": standings,
        "total": len(book.externals),
        "current_external": current.external_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This campaign's own roadmap standing, proved from the roadmap itself.

    The record loads this campaign's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 campaigns in 11 parts,
    the named prefix, the next campaign where the
    external externals, and M-231's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(EXTERNAL_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "external_roadmap",
        "campaign": EXTERNAL_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m231_title": own.title,
        "m231_part": own.part,
        "m231_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: campaigns, externals, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or external ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ExternalBook:
    title: str
    campaigns: Tuple[CampaignRef, ...] = ()
    externals: Tuple[ExternalRecord, ...] = ()
    views: Tuple[ExternalView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[ExternalPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        campaigns = tuple(_check_campaign_ref(g) for g in self.campaigns)
        externals = tuple(_check_external_ref(g) for g in self.externals)
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
        external_ids = set()
        external_seqs = set()
        for external in externals:
            if external.external_id in external_ids:
                raise ValueError(
                    f"two externals stand under id {external.external_id!r}")
            if external.seq in external_seqs:
                raise ValueError(
                    f"two externals stand at sequence {external.seq}")
            external_ids.add(external.external_id)
            external_seqs.add(external.seq)
        by_slice = {ref.campaign_id: ref for ref in campaigns}
        for external in (externals if campaigns else ()):

            ref = by_slice.get(external.campaign_id)
            if ref is None:
                raise ValueError(
                    f"external {external.external_id!r} is held from campaign "
                    f"{external.campaign_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "live":
                raise ValueError(
                    f"external {external.external_id!r} is held from campaign "
                    f"{external.campaign_id!r}, which is not active: "
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
            target = (record.external_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for external "
                    f"{record.external_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per external target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_externals = set()
        external_ids = {external.external_id for external in externals}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.external_id in trace_externals:
                raise ValueError(
                    f"two traces stand for external "
                    f"{record.external_id!r}: one trace stands "
                    f"per external walk")
            if externals and record.external_id not in external_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces external "
                    f"{record.external_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_externals.add(record.external_id)
        object.__setattr__(
            self, "campaigns", tuple(sorted(campaigns, key=lambda g: g.seq)))
        object.__setattr__(
            self, "external_records", tuple(sorted(externals, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.externals + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.external_id for g in self.externals) + tuple(
            v.view_id for v in self.views)

    def external_ids(self) -> Tuple[str, ...]:
        return tuple(g.external_id for g in self.externals)

    def campaign_ids(self) -> Tuple[str, ...]:
        return tuple(g.campaign_id for g in self.campaigns)

    def external_for(self, external_id: Any) -> ExternalRecord:
        wanted = _clean_text(external_id, "a external id")
        for external in self.externals:
            if external.external_id == wanted:
                return external
        raise KeyError(f"no external named {wanted!r} stands in this book")

    def slice_for(self, campaign_id: Any) -> CampaignRef:
        wanted = _clean_text(campaign_id, "an campaign id")
        for ref in self.campaigns:
            if ref.campaign_id == wanted:
                return ref
        raise KeyError(f"no campaign named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> ExternalView:
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
        for external in self.externals:
            if external.external_id == wanted:
                return external
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "campaigns": [g.to_record() for g in self.campaigns],
            "external_records": [g.to_record() for g in self.externals],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: ExternalBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: ExternalBook) -> None:
    if book.title != "Cross-app method at the M-231 slice run":
        raise ValueError("the shipped example book carries another title")
    if len(book.campaigns) != 3 or len(book.externals) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three campaign references, five externals and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m230-campaign":
        raise ValueError("the pinned panel is panel-m230-campaign")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.stage for e in index.externals] != ["held", "held", "held"]:
        raise ValueError("the shipped example book index must derive the three held complete externals in held external")
    if index.gaps != ("external-bare-external", "external-leaping-external"):
        raise ValueError("the shipped example book must leave the bare and leaping externals honestly open, named in its gaps")
    found = external_for_check(book, EXAMPLE_STAGE)
    if found is None or found.external_id != "external-held-external":
        raise ValueError("the shipped example book must reach its opening external under the example stage")
    if trace_of(book, "external-held-external") != "named > linked > verified > tracked > held":
        raise ValueError("the shipped example book must derive the opening external's trace from its walked steps")
    if not trace_current(book, "external-held-external"):
        raise ValueError("the shipped example book must hold the opening external's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note external")

def validate_book(data: Any, *, require_example: bool = False) -> ExternalBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, ExternalBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a external book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live campaign build or execution "
                f"({key!r} is named on it): {EXTERNAL_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its externals under a view")
    if "external_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held externals at call time")
    if "ledger" in data or "current_external" in data:
        raise ValueError(
            "a book stores no ledger and no current external: both are "
            "derived from its held externals at call time")
    if "trace" in data or "external" in data:
        raise ValueError(
            "a book stores no trace and no external: both are derived "
            "from its held externals at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != EXTERNAL_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{EXTERNAL_SCHEMA!r}")
    if data.get("campaign") is not None and (
            data["campaign"] != EXTERNAL_SLICE):
        raise ValueError(
            f"a book's campaign must be {EXTERNAL_SLICE!r}")
    head = data.get("external_head") or data.get("cross_app_method") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's external head must be a mapping")
    title = head.get("title") or data.get("title")
    campaigns = tuple(build_campaign_ref(g) for g in data.get("campaigns") or ())
    externals = tuple(build_external(g) for g in data.get("external_records") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = ExternalBook(
        title=title, campaigns=campaigns, externals=externals, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = ExternalBook(
        title=book.title, campaigns=book.campaigns, externals=book.externals,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> ExternalBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (ExternalBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an ExternalBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> ExternalBook:
    return validate_book(data, require_example=require_example)


def load_external(
        data: Optional[Dict[str, Any]] = None) -> ExternalBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(EXTERNAL_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_external_file(path: Any) -> ExternalBook:
    """Load one external file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: campaign references, externals and views held one by one.
# ---------------------------------------------------------------------

class ExternalRegistry:
    """An in-memory holding of campaign references, externals and views.

    The registry is the pure layer's model of a
    session's external book: campaign references are
    held under their ids, externals are held under
    their ids, one external per id and per sequence,
    and views are held in linked external, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[CampaignRef] = []
        self._externals: List[ExternalRecord] = []
        self._views: List[ExternalView] = []
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
        """Hold one campaign reference, verified whole before held."""
        tracked = _check_campaign_ref(item)
        return self._register(
            self._slices, tracked, "campaign_id", "campaign reference")

    def register_external(self, item: Any) -> ExternalRecord:
        """Hold one external, verified whole before held."""
        tracked = _check_external_ref(item)
        return self._register(
            self._externals, tracked, "external_id", "external")

    def register_view(self, view: Any) -> ExternalView:
        """Hold one view; a view naming no id takes a fresh one."""
        tracked = _check_view_ref(view)
        if not tracked.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            tracked = build_view({**tracked.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, tracked, "view_id", "view")

    def register_book(self, book: Any) -> ExternalBook:
        """Hold a whole book's records, under its title."""
        tracked = build_book(book)
        if self._title is not None and tracked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {tracked.title!r}")
        for ref in tracked.campaigns:
            self.register_campaign_ref(ref)
        for external in tracked.externals:
            self.register_external(external)
        for view in tracked.views:
            self.register_view(view)
        self._title = tracked.title
        return self.book()

    def book(self) -> ExternalBook:
        return ExternalBook(
            title=self._title or "An unheld external book",
            campaigns=tuple(self._slices), externals=tuple(self._externals),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[CampaignRef, ...]:
        return tuple(self._slices)

    def list_externals(self) -> Tuple[ExternalRecord, ...]:
        return tuple(self._externals)

    def list_views(self) -> Tuple[ExternalView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._externals) + tuple(self._views)

    def get_slice(self, campaign_id: Any) -> CampaignRef:
        return self.book().slice_for(campaign_id)

    def get_external(self, external_id: Any) -> ExternalRecord:
        return self.book().external_for(external_id)

    def get_view(self, view_id: Any) -> ExternalView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the ledger target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> ExternalBook:
    if source is None:
        return load_external()
    if isinstance(source, ExternalBook):
        return source
    if isinstance(source, ExternalRegistry):
        return source.book()
    return build_book(source)


def _heldance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _HELDANCE}


def external_record(external: Any, source: Any = None) -> Dict[str, Any]:
    tracked = _check_external_ref(external)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "external_external",
        "campaign": EXTERNAL_SLICE,
        "external_id": tracked.external_id,
        "campaign_id": tracked.campaign_id,
        "title": tracked.title,
        "segment": segment_of(tracked, book),
        "complete": external_green(tracked, book),
        "gaps": list(external_gaps(tracked, book)),
    }
    record.update(_heldance_record(tracked))
    return record


def campaign_record(ref: Any) -> Dict[str, Any]:
    tracked = _check_campaign_ref(ref)
    record = {
        "type": "external_run",
        "campaign": EXTERNAL_SLICE,
        "campaign_id": tracked.campaign_id,
        "title": tracked.title,
        "state": tracked.state,
    }
    record.update(_heldance_record(tracked))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    tracked = _check_trace_ref(record_in)
    record = {
        "type": "external_trace",
        "campaign": EXTERNAL_SLICE,
        "trace_id": tracked.trace_id,
        "external_id": tracked.external_id,
        "trace": tracked.trace,
    }
    record.update(_heldance_record(tracked))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    tracked = _check_view_ref(view)
    record = {
        "type": "external_view",
        "campaign": EXTERNAL_SLICE,
        "view_id": tracked.view_id, "seq": tracked.seq,
        "view_filter": tracked.view_filter,
    }
    record.update(_heldance_record(tracked))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    tracked = _check_note_ref(record_in)
    record = {
        "type": "external_note",
        "campaign": EXTERNAL_SLICE,
        "note_id": tracked.note_id,
        "external_id": tracked.external_id,
        "stance": tracked.stance,
    }
    record.update(_heldance_record(tracked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    tracked = validate_panel(panel, source)
    record = {"type": "external_panel",
              "campaign": EXTERNAL_SLICE}
    record.update(tracked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, ExternalVerdict):
        tracked = validate_verdict(verdict, source)
    else:
        tracked = derive_verdict(_source_book(verdict), view)
    record = {"type": "external_verdict",
              "campaign": EXTERNAL_SLICE}
    record.update(tracked.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, ExternalIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "external_index",
              "campaign": EXTERNAL_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    tracked = _source_book(book)
    record = {"type": "external_book",
              "campaign": EXTERNAL_SLICE,
              "title": tracked.title}
    record.update(tracked.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(external: Any, source: Any = None) -> str:
    tracked = _check_external_ref(external)
    return (
        f"{tracked.title} - from {tracked.campaign_id}: "
        f"stage {tracked.stage if tracked.stage else 'none'}, "
        f"claims "
        f"{', '.join(tracked.claims) if tracked.claims else 'none'}. "
        f"{tracked.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The externals stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"externals stand complete.")


def view_plain_words(view: Any) -> str:
    tracked = _check_view_ref(view)
    return f"View {tracked.view_id}: shows {tracked.view_filter} externals."


def note_plain_words(record_in: Any) -> str:
    tracked = _check_note_ref(record_in)
    return (
        f"Note {tracked.note_id}: {tracked.stance} "
        f"{tracked.external_id}, toward {tracked.target}. "
        f"{tracked.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, ExternalIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.externals)} green externals; "
        f"red, named in its gaps: {gaps}.")

def format_external(external: Any, source: Any = None) -> str:
    tracked = _check_external_ref(external)
    book = _source_book(source) if source is not None else None
    lines = [f"{tracked.title} ({tracked.external_id})"]
    lines.extend(plain_lines(tracked))
    lines.append(tracked.detail)
    if external_green(tracked, book):
        lines.append(
            "This external stands complete - it walked the question "
            "sequence in the open from named to held, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This external stands open - it stands named in "
            f"its gaps: {', '.join(external_gaps(tracked, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    tracked = _check_view_ref(view)
    return (
        f"View {tracked.view_id}: filter {tracked.view_filter} - "
        f"{tracked.detail}")


def format_note(record_in: Any) -> str:
    tracked = _check_note_ref(record_in)
    lines = [
        f"External note {tracked.stance} {tracked.external_id} "
        f"({tracked.note_id}): {tracked.title}. {tracked.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or external it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_stage(source: Any, stage: Any) -> str:
    external = external_for_check(source, stage)
    if external is not None:
        return format_external(external, source)
    wanted = stage.strip() if isinstance(stage, str) else stage
    return (
        f"No held external stands under stage {wanted!r} yet - the "
        f"stage reaches nothing in this book, and no external is "
        f"invented for it.")


def format_book(source: Any = None, campaign_id: Any = None) -> str:
    book = _source_book(source)
    externals = (externals_for_campaign(book, campaign_id)
              if campaign_id is not None else book.externals)
    lines = [f"The External Gate (M-231) - {book.title}"]
    lines.extend(segment_of(external, book) for external in externals)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"External panel under view {panel.view_id}:"]
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
    lines = ["External index, derived from the held externals:"]
    for external in index.externals:
        lines.append(f"{external.stage} - {external.title} ({external.external_id})")
    if index.gaps:
        lines.append(
            "Red, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_external_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The External Gate (M-231)",
        f"{book.title}: {len(book.externals)} externals held, "
        f"{len(green_externals(book))} externals standing green, "
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


def parse_external_args(args: Any) -> Tuple[str, Any]:
    """Parse the /external grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("external", "view", "note"):
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
