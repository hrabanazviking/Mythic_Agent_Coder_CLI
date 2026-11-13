"""Campaigns (roadmap slice M-216).

Part IX - The Mythic Method Engine. The roadmap
words: **several campaigns across repos with one board; keepers per campaign; the human sees the whole forge at a glance.*

What already ships, and what this slice adds:

* The campaigns book already ships as data
  (M-201, ``core/campaigns.py``): a roadmap/campaign
  file (parts, slices, acceptance checks, state) the
  app reads. This slice WIRES the hall that book's
  shape invites - several campaigns held across
  repos with one board over them - as data, in its
  own module, standing in the M-195 copy-and-share
  book shape the M-215 book stands in: one hallkeeper
  per hall, and the hallkeeper's charge over one
  campaign across its repo held as a book - a
  campaign. The shipped roads stand untouched behind
  their seams: this layer holds campaigns as data
  over the hall's repos and rewrites none of them,
  and the campaigns book keeps its own standing.
  Campaigns stand on the board AS DATA alone: a
  campaign carries a board ref, a reference held in
  this book; holding, viewing or telling a campaign
  runs no campaign live, moves no keeper and files
  nothing.
* No charter row names this slice: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-216 on no row, and the
  slice tests pin that absence live. The M-005
  method charter names no slice row either: its
  own words name the whole of Part IX as the
  part that executes the charter, and this slice
  is built to the roadmap words and that
  execution note together.

* A campaign is held whole: the slice it
  answers for, named by its slice id; its title;
  the campaign steps it walked, held as data in
  walk order; and the evidence it carries, held
  as data by kind. The campaign walk is EXPLICIT:
  its sequence stands as data
  (:data:`CHECKS`, :data:`TRANSITIONS`) -
  gathered, boarded, kept, reported, glanced -
  and a campaign's standing is DERIVED at
  call time from its held steps and evidence
  alone: a campaign that opens anywhere but
  gathered, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet reached glanced stands
  open, named in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - repo_ref,
  board_ref, keeper_record, glance_ref, evidence
  a hallkeeper can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A campaign is
  reported from held evidence alone, never
  from a feeling: a campaign holding a
  bare claim stands open, named in its gaps.
* A campaign stands only for an ACTIVE
  slice. The book holds each slice it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  campaign naming a slice that stands
  nowhere in the book refuses BY NAME, and a
  campaign for a slice that is not active
  refuses BY NAME beside it: the hallkeeper deals with
  the slice in hand, in roadmap order, never a
  queued one, and a slice whose campaign already
  stands complete is never kept twice - the
  current campaign is derived, so a
  completed slice is never the current campaign
  twice.
* The campaign's trace is visible. A trace
  record holds one campaign's walked steps
  as one trace line, exactly as walked, beside
  the campaign. The derived trace is
  computed at call time from the campaign's
  held steps; a held trace that no longer agrees
  with it stands stale, named in the board - the
  trace is the walk itself, never a retelling
  of it.
* The campaign index is DERIVED at call
  time from the held campaigns - one entry
  per complete campaign, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, order or current-campaign
  claim on any record refuses by name.
* The current campaign is DERIVED at call
  time - the first held campaign, in held
  order, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its campaign, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per campaign stance; holding
  a note posts none of it, the rule stands as
  data (:data:`CAMPAIGN_RULE`), and a record
  claiming a campaign was actually glanced,
  captured or promoted live refuses BY NAME.
  The hallkeeper reports - and those reports, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the shape a real campaign
  file takes, a loader reads a file anywhere on
  disk, campaigns and views are shaped as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a campaign book for a session and
  telling from it. This layer reaches no live
  road: it writes no campaign live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no hallkeeper, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds campaigns
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The campaign walk is explicit.** A
  campaign is reported against the held
  steps and legal steps alone; an illegal step
  stands named in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  campaign that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, named in its gaps:
  a campaign is reported from evidence, not
  vibes.
* **Active slices only, in roadmap order.** A
  campaign for a missing or queued slice
  refuses by name; no campaign is invented
  for a slice the hallkeeper has not dealt with.
* **Unknown stays unknown.** A campaign
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, order
  and current campaign are derived, never
  stored.** Each is derived from the held
  campaigns at call time; a stored one
  refuses by name, so it can never drift.
* **One campaign per campaign.** Two
  campaigns standing for one campaign id
  refuse by name, and one note record stands per
  campaign stance.
* **The notes are data alone.** The records
  hold the feedback; holding, viewing or telling
  them writes nothing, files nothing and posts
  nothing.
"""


from __future__ import annotations

__all__ = [
    "CHECK_FIELDS",
    "CHECKS",
    "CLAIM_KINDS",
    "HELD_EVIDENCE",
    "BARE_CLAIMS",
    "TRANSITIONS",
    "EXAMPLE_CHECK",
    "STANCES",
    "INDEX_ACTION",
    "CAMPAIGN_RESOURCE",
    "CAMPAIGN_SCHEMA",
    "CAMPAIGN_SLICE",
    "CAMPAIGN_RULE",
    "PLAIN_EXPLANATION",
    "THE_CAMPAIGN_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "COMPLETE_WORDS",
    "REPO_STATES",
    "Any",
    "Dict",
    "List",
    "Optional",
    "TraceRecord",
    "CampaignRecord",
    "IndexEntry",
    "RepoRef",
    "NoteRecord",
    "CampaignBook",
    "CampaignIndex",
    "CampaignPanel",
    "CampaignPanelRow",
    "CampaignRegistry",
    "CampaignVerdict",
    "CampaignView",
    "TargetCount",
    "trace_for_campaign",
    "trace_record",
    "board_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_campaign",
    "build_repo_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_campaign",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "campaign_for_check",
    "campaign_order",
    "campaign_record",
    "first_note",
    "format_book",
    "format_campaign",
    "format_index",
    "format_note",
    "format_check",
    "format_panel",
    "format_campaign_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "repo_record",
    "load_campaign",
    "load_campaign_file",
    "normalize_repo_state",
    "normalize_check",
    "normalize_claim_kind",
    "legal_step",
    "next_check",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_campaign",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_campaign_args",
    "green_campaigns",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_campaigns",
    "validate_trace",
    "validate_book",
    "validate_campaign",
    "validate_repo_ref",
    "validate_note",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
    "campaign_gaps",
    "campaign_green",
    "campaigns_for_repo",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

CAMPAIGN_SCHEMA = "mythic.multi_campaign_hall/1"
CAMPAIGN_SLICE = "M-216"
THE_CAMPAIGN_SLICE = CAMPAIGN_SLICE
CAMPAIGN_RESOURCE = "multi_campaign_hall.yaml"
INDEX_ACTION = "index"
EXAMPLE_CHECK = "glanced"
CHECK_FIELDS = ("checks", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("glanced", "held", "blocked")
REPO_STATES = ("live", "dormant")
CAMPAIGN_RULE = 'campaigns are held as data alone: several campaigns across repos stand with one board, keepers per campaign, and the human sees the whole forge at a glance - a glance stands as data, held by reference (a glance ref), never taken live - the campaign walk stands as an explicit campaign sequence - gathered, boarded, kept, reported, glanced - and a campaign completes only complete, complete being a state with evidence held - repo ref, board ref, keeper record, glance ref - never a feeling, a memory, an assertion or a summary; holding, viewing and reading a campaign runs no campaign live, approves nothing, spawns no process and opens no network'
PLAIN_EXPLANATION = 'Multi-campaign hall (M-216): several campaigns across repos with one board; keepers per campaign; the human sees the whole forge at a glance.'
USAGE = 'Usage: /hall | /hall campaign <campaign-id> | /hall check <check> | /hall repo <repo-id> | /hall view <view-id> | /hall note <note-id> | /hall index | /hall panel | /hall verdict'

CHECKS = ("gathered", "boarded", "kept", "reported", "glanced")
HELD_EVIDENCE = ("repo_ref", "board_ref", "keeper_record", "glance_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "gathered": ("boarded",),
    "boarded": ("kept",),
    "kept": ("reported",),
    "reported": ("gathered", "glanced"),
    "glanced": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a failure or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a campaign stands complete.
    A check outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_check(check: Any, failed: Any = False) -> Optional[str]:
    """The step the hallkeeper takes next, DERIVED from the sequence.

    Banked leads to boarded and boarded to
    kept; kept leads to reported; at
    reported a follow-up banking steps back to gathered and a finished campaign steps to glanced;
    glanced is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    reported = normalize_check(check)
    if reported == "gathered":
        return "boarded"
    if reported == "boarded":
        return "kept"
    if reported == "kept":
        return "reported"
    if reported == "reported":
        return "gathered" if failed else "glanced"
    return None


_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "campaign_id", "seq", "repo_id", "title", "checks",
    "claims", "detail",
} | set(_PROVENANCE))
_SLICE_REF_KEYS = frozenset({
    "repo_id", "seq", "title", "state", "detail",
} | set(_PROVENANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "campaign_id", "trace", "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "campaign_id", "stance", "target", "title",
    "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "entries", "coverage", "covered", "uncovered",
    "current_campaign", "next_campaign", "progress", "board",
    "current", "order", "breaks", "live"})
_LIVE_KEYS = (
    "live_campaign", "campaigns_live", "live_question",
    "campaigns_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "resumes_live",
    "resumed_live", "pauses_campaign", "paused_live",
    "runs_campaign", "ran_campaign", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "campaign_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_campaign", "sent_campaign",
    "posts_note", "posted_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_campaign", "filed_live", "spawns_hallkeeper", "spawned_hallkeeper", "sends_campaign", "sent_campaign", "writes_campaign", "wrote_campaign")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_checks(value: Any) -> Tuple[str, ...]:
    """A campaign's walked checks, held as data.

    The checks stand as a list of check names in
    walk order, each one a check of the explicit
    gate sequence; a walk not yet held stands
    honestly empty - no check is invented - and
    a name outside the machine refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("checks must be a list of gate sequence checks")
    return tuple(normalize_check(v) for v in value)

def _check_claims(value: Any) -> Tuple[str, ...]:
    """A campaign's asked claims: claim kinds named as data.

    Each claim names one kind from the glanced
    vocabulary - the human kinds the gate may ask
    and the code kinds it must never ask, both
    held honestly as data - and a kind outside
    the vocabulary refuses.
    """
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError("claims must be a list of claim kinds")
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
            out[key] = _clean_text(mapping.get(key), "a recorded_on day")
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
                f"{what} claims a live gate campaign or slice build "
                f"execution ({key!r} is named on it): "
                f"{CAMPAIGN_RULE}")
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


def normalize_repo_state(value: Any) -> str:
    state = _clean_text(value, "an slice state").lower()
    if state not in REPO_STATES:
        raise ValueError(
            f"slice state {state!r} is not one of the held "
            f"states: " + ", ".join(REPO_STATES))
    return state


def normalize_view_filter(value: Any) -> str:
    view_filter = _clean_text(value, "a view filter").lower()
    if view_filter not in VIEW_FILTERS:
        raise ValueError(
            f"view filter {view_filter!r} is not one of the held "
            f"filters: " + ", ".join(VIEW_FILTERS))
    return view_filter


def normalize_check(value: Any) -> str:
    check = _clean_text(value, "a check").lower()
    if check not in CHECKS:
        raise ValueError(
            f"check {check!r} is not one of the held "
            f"checks: " + ", ".join(CHECKS))
    return check


def normalize_claim_kind(value: Any) -> str:
    kind = _clean_text(value, "a claim kind").lower()
    if kind not in CLAIM_KINDS:
        raise ValueError(
            f"claim kind {kind!r} is not one of the held "
            f"kinds: " + ", ".join(CLAIM_KINDS))
    return kind

# ---------------------------------------------------------------------
# The held campaign: one slice cut from an active slice.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CampaignRecord:
    """One campaign slice, held as data.

    The campaign names the active slice it was
    held from, by slice id, its title, its
    verifiable checks, held as data, and its
    claims, named by campaign id. The grain is
    derived, never stored: exactly one verifiable
    walk is kept against the machine. A campaign whose
    checks are not yet held stands with its
    checks empty: it stands open, named in
    its gaps, and no check is invented for it.
    The campaign is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    campaign_id: str
    seq: int
    repo_id: str
    title: str
    checks: Tuple[str, ...] = ()
    claims: Tuple[str, ...] = ()
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "campaign_id", _clean_text(self.campaign_id, "a campaign id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "repo_id", _clean_text(self.repo_id, "an slice id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a campaign title"))
        object.__setattr__(
            self, "checks", _check_checks(self.checks))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a campaign detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.campaign_id

    @property
    def check(self) -> str:
        """The check the campaign stands at: its last walked check."""
        return self.checks[-1] if self.checks else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "campaign_id": self.campaign_id, "seq": self.seq,
            "repo_id": self.repo_id, "title": self.title,
            "checks": list(self.checks),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_campaign_ref(value: Any) -> CampaignRecord:
    if not isinstance(value, CampaignRecord):
        raise ValueError("a campaign must be a CampaignRecord")
    return value


def validate_campaign(campaign: Any) -> CampaignRecord:
    return _check_campaign_ref(campaign)


def build_campaign(record: Any = None, **kwargs: Any) -> CampaignRecord:
    """Build one held campaign from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, CampaignRecord):
        if kwargs:
            raise ValueError("a campaign stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a campaign must be a mapping or a CampaignRecord")
    _needed(data, _RUN_KEYS, "a campaign")
    return CampaignRecord(
        campaign_id=data.get("campaign_id"), seq=data.get("seq"),
        repo_id=data.get("repo_id"), title=data.get("title"),
        checks=data.get("checks"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_provenance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each campaign to the steps it took outside the machine.

    Derived from the held campaigns alone: a break is
    one consecutive pair of walked checks the
    explicit gate sequence does not allow, told
    in walk order as before, then after.
    """
    found: Dict[str, Tuple[str, ...]] = {}
    for campaign in book.campaigns:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(campaign.checks, campaign.checks[1:])
            if not legal_step(before, after))
        if breaks:
            found[campaign.campaign_id] = breaks
    return found

def campaign_gaps(campaign: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a campaign from standing complete.

    Mapped from the campaign's own held fields alone -
    its walked steps against the explicit question
    sequence, and its carried evidence against the
    glanced vocabulary: the campaign opens at
    named, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a campaign stands complete only when it has
    reached glanced. The source names nothing
    further: no gap is borrowed from another
    campaign.
    """
    reported = _check_campaign_ref(campaign)
    gaps: List[str] = []
    if not reported.checks:
        gaps.append(
            "has passed through no step: the campaign has not started")
        return tuple(gaps)
    if reported.checks[0] != "gathered":
        gaps.append(
            f"opens at {reported.checks[0]}, not at gathered: "
            f"the campaign opens with the reflection")
    for before, after in zip(reported.checks, reported.checks[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"campaign sequence does not allow")
    for kind in reported.claims:
        if kind in BARE_CLAIMS:
            gaps.append(
                f"carries a {kind} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if reported.checks[-1] != "glanced":
        gaps.append(
            f"has not reached glanced: the campaign stands "
            f"at {reported.checks[-1]}")
    return tuple(gaps)

def campaign_green(campaign: Any, source: Any = None) -> bool:
    return not campaign_gaps(campaign, source)


def plain_lines(campaign: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the campaign's own fields."""
    reported = _check_campaign_ref(campaign)
    return (
        f"Campaign: {reported.title}",
        f"Repo: {reported.repo_id}",
        f"Check: {reported.check if reported.check else 'none'}",
        f"Claims: "
        f"{', '.join(reported.claims) if reported.claims else 'none'}",
    )


def segment_of(campaign: Any, source: Any = None) -> str:
    reported = _check_campaign_ref(campaign)
    gaps = campaign_gaps(reported, source)
    return (
        f"{reported.campaign_id}: {reported.title} - slice: "
        f"'{reported.repo_id}' - check: "
        f"'{reported.check if reported.check else 'none'}' - "
        f"checks: {len(reported.checks)} - claims: "
        f"'{', '.join(reported.claims) if reported.claims else 'none'}' - "
        f"detail: '{reported.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held slice reference: the active slice a book campaigns from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class RepoRef:
    """One slice a campaign book campaigns from, held as a reference.

    The record names the slice, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 slice book's own telling. A campaign
    stands only from an active reference: the
    book refuses a campaign naming no held reference,
    and a campaign from an queued one, BY NAME.
    """

    repo_id: str
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
            self, "repo_id", _clean_text(self.repo_id, "an slice id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a title"))
        object.__setattr__(
            self, "state", normalize_repo_state(self.state))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an slice detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.repo_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "repo_id": self.repo_id, "seq": self.seq,
            "title": self.title, "state": self.state,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_repo_ref(value: Any) -> RepoRef:
    if not isinstance(value, RepoRef):
        raise ValueError("a slice reference must be an RepoRef")
    return value


def validate_repo_ref(ref: Any) -> RepoRef:
    return _check_repo_ref(ref)


def build_repo_ref(record: Any = None, **kwargs: Any) -> RepoRef:
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, RepoRef):
        if kwargs:
            raise ValueError(
                "a slice reference stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError(
            "a slice reference must be a mapping or an RepoRef")
    _needed(data, _SLICE_REF_KEYS, "a slice reference")
    return RepoRef(
        repo_id=data.get("repo_id"), seq=data.get("seq"),
        title=data.get("title"), state=data.get("state"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held trace trace: the human approves the trace, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TraceRecord:
    """One trace trace, held as data.

    The record names its slice and the trace the
    human active - the slice's campaign ids in
    derived claim order, held exactly as
    active. The trace is of the set and its
    order, never of a step: when the derived
    trace moves, this record stands stale, named
    in the board, until a new trace is active.
    """

    trace_id: str
    seq: int
    campaign_id: str
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
            self, "campaign_id", _clean_text(self.campaign_id, "an slice id"))
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
            "campaign_id": self.campaign_id, "trace": self.trace,
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
        campaign_id=data.get("campaign_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a campaign, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One campaign stance, held as data.

    The record names its campaign, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per campaign stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    campaign_id: str
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
            self, "campaign_id", _clean_text(self.campaign_id, "a campaign id"))
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
            "campaign_id": self.campaign_id, "stance": self.stance,
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
        campaign_id=data.get("campaign_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held view: which slices a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CampaignView:
    """A view over the book: every campaign, the green, the rest."""

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


def _check_view_ref(value: Any) -> CampaignView:
    if not isinstance(value, CampaignView):
        raise ValueError("a view must be an CampaignView")
    return value


def validate_view(view: Any) -> CampaignView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> CampaignView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, CampaignView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an CampaignView")
    _needed(data, _VIEW_KEYS, "a view")
    return CampaignView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CampaignPanelRow:
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


def _row_for_campaign(campaign: CampaignRecord,
                     source: Any = None) -> CampaignPanelRow:
    return CampaignPanelRow(
        item_id=campaign.campaign_id,
        standing="complete" if campaign_green(campaign, source) else "open",
        label=campaign.title, segment=segment_of(campaign, source),
        recorded_on=campaign.recorded_on)


def _check_row_ref(value: Any) -> CampaignPanelRow:
    if not isinstance(value, CampaignPanelRow):
        raise ValueError("a panel row must be an CampaignPanelRow")
    return value


def validate_row(row: Any, campaign: Any = None,
                 source: Any = None) -> CampaignPanelRow:
    reported = _check_row_ref(row)
    if campaign is not None:
        derived = _row_for_campaign(_check_campaign_ref(campaign), source)
        if reported != derived:
            raise ValueError(
                f"panel row {reported.item_id!r} does not agree with "
                f"the row derived from its campaign")
    return reported


def build_row(row: Any = None, campaign: Any = None,
              source: Any = None,
              **kwargs: Any) -> CampaignPanelRow:
    if campaign is not None:
        derived = _row_for_campaign(_check_campaign_ref(campaign), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            CampaignPanelRow(**kwargs))
        return validate_row(built, campaign, source)
    if isinstance(row, CampaignPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return CampaignPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return CampaignPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an CampaignPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[CampaignPanelRow, ...]
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
        f"The campaign book holds {total_items} campaigns as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown campaigns "
        f"stand complete.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its campaign's own fields "
        "- the slice it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any campaign.",
        "Completeness is kept from the held records alone: "
        "a campaign that steps outside the campaign sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not reached glanced stands open, named in its "
        "gaps, and the campaign index is derived from the "
        "held campaigns, never stored where it could drift.",
    )

@dataclass(frozen=True)
class CampaignPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[CampaignPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> CampaignView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, CampaignView):
        return view
    return book.view_for(view)


def shown_campaigns(source: Any, view: Any = None
                   ) -> Tuple[CampaignRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.campaigns
    if resolved.view_filter == "complete":
        return tuple(g for g in book.campaigns if campaign_green(g, book))
    return tuple(g for g in book.campaigns if not campaign_green(g, book))


def campaigns_for_repo(source: Any, repo_id: Any
                      ) -> Tuple[CampaignRecord, ...]:
    wanted = _clean_text(repo_id, "an slice id")
    return tuple(
        g for g in _source_book(source).campaigns if g.repo_id == wanted)


def green_campaigns(source: Any) -> Tuple[CampaignRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.campaigns if campaign_green(g, book))


def current_campaign(source: Any) -> Optional[CampaignRecord]:
    """The book's current campaign, DERIVED at call time.

    The first held campaign, in held order, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held campaigns alone, so it can
    never go stale against them. A book whose every
    campaign stands complete has no current campaign.
    """
    book = _source_book(source)
    for campaign in book.campaigns:
        if not campaign_green(campaign, book):
            return campaign
    return None


def derive_panel(source: Any, view: Any = None) -> CampaignPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_campaigns(book, resolved)
    rows = tuple(_row_for_campaign(campaign, book) for campaign in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.campaigns), default="")
    green = sum(1 for g in shown if campaign_green(g, book))
    return CampaignPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.campaigns), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.campaigns), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> CampaignPanel:
    if not isinstance(value, CampaignPanel):
        raise ValueError("a panel must be an CampaignPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> CampaignPanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 campaign).
    """
    reported = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(reported.view_id)
                if reported.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(reported, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {reported.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return reported


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> CampaignPanel:
    if isinstance(panel, CampaignPanel):
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
        built = CampaignPanel(
            panel_id=_clean_text(data.get("panel_id"), "a panel id"),
            view_id=data.get("view_id"),
            view_filter=normalize_view_filter(data.get("view_filter")),
            rows=rows,
            total_items=_check_count(
                data.get("total_items"), "a total_items count"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            target_counts=counts,
            as_of=_clean_text(data.get("as_of"), "an as_of day"),
            account=_check_lines(data.get("account"), "the account"))
        return validate_panel(built, source)
    if panel is None and source is not None:
        return derive_panel(source, kwargs.get("view"))
    raise ValueError("a panel must be a mapping, an CampaignPanel, or derived")


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
        return "glanced"
    if green_shown == 0:
        return "blocked"
    return "held"


@dataclass(frozen=True)
class CampaignVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> CampaignVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_campaigns(book, resolved)
    green = sum(1 for g in shown if campaign_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return CampaignVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> CampaignVerdict:
    if not isinstance(value, CampaignVerdict):
        raise ValueError("a verdict must be an CampaignVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> CampaignVerdict:
    reported = _check_verdict_ref(verdict)
    if reported.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {reported.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(reported.view_id)
                if reported.view_id is not None else None)
        derived = derive_verdict(book, view)
        if reported != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return reported


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> CampaignVerdict:
    if isinstance(verdict, CampaignVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = CampaignVerdict(
            verdict=_clean_text(data.get("verdict"), "a verdict"),
            view_id=data.get("view_id"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            green_shown=_check_count(
                data.get("green_shown"), "a green_shown count"),
            latest_on=_clean_text(data.get("latest_on"), "a latest day"))
        return validate_verdict(built, source)
    if verdict is None and source is not None:
        return derive_verdict(source, kwargs.get("view"))
    raise ValueError(
        "a verdict must be a mapping, an CampaignVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held slices' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexEntry:
    check: str
    campaign_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "check": self.check, "campaign_id": self.campaign_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class CampaignIndex:
    """The campaign index, derived from the held campaigns.

    The index names one entry per green campaign, in
    held order - the campaign's own one verifiable
    check, its campaign id and its title - and the
    campaigns that do not stand complete, named in its
    gaps. Nothing here is stored on any campaign: the
    index is derived at call time from the held
    records alone, so it can never drift from them.
    """

    entries: Tuple[IndexEntry, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "entries": [e.to_record() for e in self.entries],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> CampaignIndex:
    """Derive the campaign index from the book's held campaigns."""
    book = _source_book(source)
    entries = tuple(
        IndexEntry(check=g.check, campaign_id=g.campaign_id,
                   title=g.title)
        for g in book.campaigns if campaign_green(g, book))
    gaps = tuple(
        g.campaign_id for g in book.campaigns if not campaign_green(g, book))
    return CampaignIndex(entries=entries, gaps=gaps)


def campaign_for_check(source: Any, check: Any) -> Optional[CampaignRecord]:
    """The first held campaign one check reaches, or none - honestly."""
    if check is None:
        return None
    if not isinstance(check, str):
        raise ValueError("an check must be a string naming the check")
    wanted = check.strip()
    if not wanted:
        return None
    for campaign in _source_book(source).campaigns:
        if campaign.check == wanted:
            return campaign
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held order: the campaign
    that took it and the step it took, before,
    then after. A book whose campaigns all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{campaign_id}: {step}"
        for campaign_id, steps in _breaks_map(book).items()
        for step in steps)

def campaign_order(source: Any,
              repo_id: Any = None) -> Tuple[CampaignRecord, ...]:
    """The held campaigns in their held order, DERIVED at call time.

    Campaigns stand in the order the book holds them -
    the order their slices were taken - optionally
    for one slice alone. Nothing here is stored:
    the order is the book's own held order, told.
    """
    book = _source_book(source)
    campaigns = list(book.campaigns)
    if repo_id is not None:
        wanted = _clean_text(repo_id, "a slice id")
        campaigns = [r for r in campaigns if r.repo_id == wanted]
    return tuple(campaigns)

def trace_of(source: Any, campaign_id: Any) -> str:
    """One campaign's trace, DERIVED at call time.

    The campaign's walked checks joined as one trace
    line, in walk order. A campaign that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is named
    elsewhere.
    """
    campaign = _source_book(source).campaign_for(campaign_id)
    return " > ".join(campaign.checks)

def trace_for_campaign(source: Any,
                  campaign_id: Any) -> Optional[TraceRecord]:
    """The held trace for one campaign, or none - honestly."""
    wanted = _clean_text(campaign_id, "a campaign id")
    for record in _source_book(source).traces:
        if record.campaign_id == wanted:
            return record
    return None

def trace_current(source: Any, campaign_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_campaign(source, campaign_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, campaign_id)

def note_for_campaign(source: Any, campaign_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one campaign (and stance, when named)."""
    wanted = _clean_text(campaign_id, "a campaign id")
    for record in _source_book(source).notes:
        if record.campaign_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the slice targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def board_record(source: Any = None) -> Dict[str, Any]:
    """The campaign board, DERIVED here from the held campaigns alone.

    The board counts the held campaigns by their
    derived completeness - green and red - names
    the current campaign, the first that does not yet
    stand complete, tells each held campaign's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held campaigns took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.campaigns
            if ("complete" if campaign_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "campaign_records": number})
    current = current_campaign(book)
    traces = []
    for campaign in book.campaigns:
        trace = trace_for_campaign(book, campaign.campaign_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, campaign.campaign_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"campaign_id": campaign.campaign_id, "trace": standing})
    return {
        "type": "campaign_board",
        "slice": CAMPAIGN_SLICE,
        "standings": standings,
        "total": len(book.campaigns),
        "current_campaign": current.campaign_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This slice's own roadmap standing, proved from the roadmap itself.

    The record loads this repo's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 slices in 11 parts,
    the gathered prefix, the next slice where the
    campaign resumes, and M-216's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(CAMPAIGN_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "campaign_roadmap",
        "slice": CAMPAIGN_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m216_title": own.title,
        "m216_part": own.part,
        "m216_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: slices, campaigns, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or order ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CampaignBook:
    title: str
    slices: Tuple[RepoRef, ...] = ()
    campaigns: Tuple[CampaignRecord, ...] = ()
    views: Tuple[CampaignView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[CampaignPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        slices = tuple(_check_repo_ref(g) for g in self.slices)
        campaigns = tuple(_check_campaign_ref(g) for g in self.campaigns)
        views = tuple(_check_view_ref(v) for v in self.views)
        notes = tuple(_check_note_ref(m) for m in self.notes)
        traces = tuple(_check_trace_ref(a) for a in self.traces)
        panels = tuple(_check_panel_ref(pn) for pn in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for ref in slices:
            if ref.repo_id in seen_ids:
                raise ValueError(
                    f"two slice references stand under id {ref.repo_id!r}")
            if ref.seq in seen_seqs:
                raise ValueError(
                    f"two slice references stand at sequence {ref.seq}")
            seen_ids.add(ref.repo_id)
            seen_seqs.add(ref.seq)
        campaign_ids = set()
        campaign_seqs = set()
        for campaign in campaigns:
            if campaign.campaign_id in campaign_ids:
                raise ValueError(
                    f"two campaigns stand under id {campaign.campaign_id!r}")
            if campaign.seq in campaign_seqs:
                raise ValueError(
                    f"two campaigns stand at sequence {campaign.seq}")
            campaign_ids.add(campaign.campaign_id)
            campaign_seqs.add(campaign.seq)
        by_slice = {ref.repo_id: ref for ref in slices}
        for campaign in (campaigns if slices else ()):

            ref = by_slice.get(campaign.repo_id)
            if ref is None:
                raise ValueError(
                    f"campaign {campaign.campaign_id!r} is held from slice "
                    f"{campaign.repo_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "live":
                raise ValueError(
                    f"campaign {campaign.campaign_id!r} is held from slice "
                    f"{campaign.repo_id!r}, which is not active: "
                    f"no slice is held from an queued slice")
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
            target = (record.campaign_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for campaign "
                    f"{record.campaign_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per campaign target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_campaigns = set()
        campaign_ids = {campaign.campaign_id for campaign in campaigns}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.campaign_id in trace_campaigns:
                raise ValueError(
                    f"two traces stand for campaign "
                    f"{record.campaign_id!r}: one trace stands "
                    f"per campaign walk")
            if campaigns and record.campaign_id not in campaign_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces campaign "
                    f"{record.campaign_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_campaigns.add(record.campaign_id)
        object.__setattr__(
            self, "repos", tuple(sorted(slices, key=lambda g: g.seq)))
        object.__setattr__(
            self, "campaign_records", tuple(sorted(campaigns, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.campaigns + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.campaign_id for g in self.campaigns) + tuple(
            v.view_id for v in self.views)

    def campaign_ids(self) -> Tuple[str, ...]:
        return tuple(g.campaign_id for g in self.campaigns)

    def repo_ids(self) -> Tuple[str, ...]:
        return tuple(g.repo_id for g in self.slices)

    def campaign_for(self, campaign_id: Any) -> CampaignRecord:
        wanted = _clean_text(campaign_id, "a campaign id")
        for campaign in self.campaigns:
            if campaign.campaign_id == wanted:
                return campaign
        raise KeyError(f"no campaign named {wanted!r} stands in this book")

    def slice_for(self, repo_id: Any) -> RepoRef:
        wanted = _clean_text(repo_id, "an slice id")
        for ref in self.slices:
            if ref.repo_id == wanted:
                return ref
        raise KeyError(f"no slice named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> CampaignView:
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
        for campaign in self.campaigns:
            if campaign.campaign_id == wanted:
                return campaign
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "repos": [g.to_record() for g in self.slices],
            "campaign_records": [g.to_record() for g in self.campaigns],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: CampaignBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: CampaignBook) -> None:
    if book.title != "Multi-campaign hall at the M-215 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.slices) != 3 or len(book.campaigns) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three slice references, five campaigns and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m215-boundary":
        raise ValueError("the pinned panel is panel-m215-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.check for e in index.entries] != ["glanced", "glanced", "glanced"]:
        raise ValueError("the shipped example book index must derive the three held complete campaigns in held order")
    if index.gaps != ("campaign-bare-campaign", "campaign-leaping-campaign"):
        raise ValueError("the shipped example book must leave the bare and leaping campaigns honestly open, named in its gaps")
    found = campaign_for_check(book, EXAMPLE_CHECK)
    if found is None or found.campaign_id != "campaign-held-campaign":
        raise ValueError("the shipped example book must reach its opening campaign under the example check")
    if trace_of(book, "campaign-held-campaign") != "gathered > boarded > kept > reported > glanced":
        raise ValueError("the shipped example book must derive the opening campaign's trace from its walked steps")
    if not trace_current(book, "campaign-held-campaign"):
        raise ValueError("the shipped example book must hold the opening campaign's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note road")

def validate_book(data: Any, *, require_example: bool = False) -> CampaignBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, CampaignBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a campaign book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live slice build or execution "
                f"({key!r} is named on it): {CAMPAIGN_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its campaigns under a view")
    if "campaign_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held campaigns at call time")
    if "board" in data or "current_campaign" in data:
        raise ValueError(
            "a book stores no board and no current campaign: both are "
            "derived from its held campaigns at call time")
    if "trace" in data or "order" in data:
        raise ValueError(
            "a book stores no trace and no order: both are derived "
            "from its held campaigns at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != CAMPAIGN_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{CAMPAIGN_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != CAMPAIGN_SLICE):
        raise ValueError(
            f"a book's slice must be {CAMPAIGN_SLICE!r}")
    head = data.get("campaign_head") or data.get("multi_campaign_hall") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's campaign head must be a mapping")
    title = head.get("title") or data.get("title")
    slices = tuple(build_repo_ref(g) for g in data.get("repos") or ())
    campaigns = tuple(build_campaign(g) for g in data.get("campaign_records") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = CampaignBook(
        title=title, slices=slices, campaigns=campaigns, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = CampaignBook(
        title=book.title, slices=book.slices, campaigns=book.campaigns,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> CampaignBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (CampaignBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an CampaignBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> CampaignBook:
    return validate_book(data, require_example=require_example)


def load_campaign(
        data: Optional[Dict[str, Any]] = None) -> CampaignBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(CAMPAIGN_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_campaign_file(path: Any) -> CampaignBook:
    """Load one campaign file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: slice references, campaigns and views held one by one.
# ---------------------------------------------------------------------

class CampaignRegistry:
    """An in-memory holding of slice references, campaigns and views.

    The registry is the pure layer's model of a
    session's campaign book: slice references are
    held under their ids, campaigns are held under
    their ids, one campaign per id and per sequence,
    and views are held in boarded order, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[RepoRef] = []
        self._campaigns: List[CampaignRecord] = []
        self._views: List[CampaignView] = []
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

    def register_repo_ref(self, item: Any) -> RepoRef:
        """Hold one slice reference, kept whole before held."""
        reported = _check_repo_ref(item)
        return self._register(
            self._slices, reported, "repo_id", "slice reference")

    def register_campaign(self, item: Any) -> CampaignRecord:
        """Hold one campaign, kept whole before held."""
        reported = _check_campaign_ref(item)
        return self._register(
            self._campaigns, reported, "campaign_id", "campaign")

    def register_view(self, view: Any) -> CampaignView:
        """Hold one view; a view naming no id takes a fresh one."""
        reported = _check_view_ref(view)
        if not reported.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            reported = build_view({**reported.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, reported, "view_id", "view")

    def register_book(self, book: Any) -> CampaignBook:
        """Hold a whole book's records, under its title."""
        reported = build_book(book)
        if self._title is not None and reported.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {reported.title!r}")
        for ref in reported.slices:
            self.register_repo_ref(ref)
        for campaign in reported.campaigns:
            self.register_campaign(campaign)
        for view in reported.views:
            self.register_view(view)
        self._title = reported.title
        return self.book()

    def book(self) -> CampaignBook:
        return CampaignBook(
            title=self._title or "An unheld campaign book",
            slices=tuple(self._slices), campaigns=tuple(self._campaigns),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[RepoRef, ...]:
        return tuple(self._slices)

    def list_campaigns(self) -> Tuple[CampaignRecord, ...]:
        return tuple(self._campaigns)

    def list_views(self) -> Tuple[CampaignView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._campaigns) + tuple(self._views)

    def get_slice(self, repo_id: Any) -> RepoRef:
        return self.book().slice_for(repo_id)

    def get_campaign(self, campaign_id: Any) -> CampaignRecord:
        return self.book().campaign_for(campaign_id)

    def get_view(self, view_id: Any) -> CampaignView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the journal target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> CampaignBook:
    if source is None:
        return load_campaign()
    if isinstance(source, CampaignBook):
        return source
    if isinstance(source, CampaignRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def campaign_record(campaign: Any, source: Any = None) -> Dict[str, Any]:
    reported = _check_campaign_ref(campaign)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "campaign_campaign",
        "slice": CAMPAIGN_SLICE,
        "campaign_id": reported.campaign_id,
        "repo_id": reported.repo_id,
        "title": reported.title,
        "segment": segment_of(reported, book),
        "complete": campaign_green(reported, book),
        "gaps": list(campaign_gaps(reported, book)),
    }
    record.update(_provenance_record(reported))
    return record


def repo_record(ref: Any) -> Dict[str, Any]:
    reported = _check_repo_ref(ref)
    record = {
        "type": "campaign_slice",
        "slice": CAMPAIGN_SLICE,
        "repo_id": reported.repo_id,
        "title": reported.title,
        "state": reported.state,
    }
    record.update(_provenance_record(reported))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    reported = _check_trace_ref(record_in)
    record = {
        "type": "campaign_trace",
        "slice": CAMPAIGN_SLICE,
        "trace_id": reported.trace_id,
        "campaign_id": reported.campaign_id,
        "trace": reported.trace,
    }
    record.update(_provenance_record(reported))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    reported = _check_view_ref(view)
    record = {
        "type": "campaign_view",
        "slice": CAMPAIGN_SLICE,
        "view_id": reported.view_id, "seq": reported.seq,
        "view_filter": reported.view_filter,
    }
    record.update(_provenance_record(reported))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    reported = _check_note_ref(record_in)
    record = {
        "type": "campaign_note",
        "slice": CAMPAIGN_SLICE,
        "note_id": reported.note_id,
        "campaign_id": reported.campaign_id,
        "stance": reported.stance,
    }
    record.update(_provenance_record(reported))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    reported = validate_panel(panel, source)
    record = {"type": "campaign_panel",
              "slice": CAMPAIGN_SLICE}
    record.update(reported.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, CampaignVerdict):
        reported = validate_verdict(verdict, source)
    else:
        reported = derive_verdict(_source_book(verdict), view)
    record = {"type": "campaign_verdict",
              "slice": CAMPAIGN_SLICE}
    record.update(reported.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, CampaignIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "campaign_index",
              "slice": CAMPAIGN_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    reported = _source_book(book)
    record = {"type": "campaign_book",
              "slice": CAMPAIGN_SLICE,
              "title": reported.title}
    record.update(reported.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(campaign: Any, source: Any = None) -> str:
    reported = _check_campaign_ref(campaign)
    return (
        f"{reported.title} - from {reported.repo_id}: "
        f"check {reported.check if reported.check else 'none'}, "
        f"claims "
        f"{', '.join(reported.claims) if reported.claims else 'none'}. "
        f"{reported.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The campaigns stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"campaigns stand complete.")


def view_plain_words(view: Any) -> str:
    reported = _check_view_ref(view)
    return f"View {reported.view_id}: shows {reported.view_filter} campaigns."


def note_plain_words(record_in: Any) -> str:
    reported = _check_note_ref(record_in)
    return (
        f"Note {reported.note_id}: {reported.stance} "
        f"{reported.campaign_id}, toward {reported.target}. "
        f"{reported.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, CampaignIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.entries)} green campaigns; "
        f"red, named in its gaps: {gaps}.")

def format_campaign(campaign: Any, source: Any = None) -> str:
    reported = _check_campaign_ref(campaign)
    book = _source_book(source) if source is not None else None
    lines = [f"{reported.title} ({reported.campaign_id})"]
    lines.extend(plain_lines(reported))
    lines.append(reported.detail)
    if campaign_green(reported, book):
        lines.append(
            "This campaign stands complete - it walked the question "
            "sequence in the open from gathered to glanced, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This campaign stands open - it stands named in "
            f"its gaps: {', '.join(campaign_gaps(reported, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    reported = _check_view_ref(view)
    return (
        f"View {reported.view_id}: filter {reported.view_filter} - "
        f"{reported.detail}")


def format_note(record_in: Any) -> str:
    reported = _check_note_ref(record_in)
    lines = [
        f"Campaign note {reported.stance} {reported.campaign_id} "
        f"({reported.note_id}): {reported.title}. {reported.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_check(source: Any, check: Any) -> str:
    campaign = campaign_for_check(source, check)
    if campaign is not None:
        return format_campaign(campaign, source)
    wanted = check.strip() if isinstance(check, str) else check
    return (
        f"No held campaign stands under check {wanted!r} yet - the "
        f"check reaches nothing in this book, and no campaign is "
        f"invented for it.")


def format_book(source: Any = None, repo_id: Any = None) -> str:
    book = _source_book(source)
    campaigns = (campaigns_for_repo(book, repo_id)
              if repo_id is not None else book.campaigns)
    lines = [f"The Campaign Gate (M-216) - {book.title}"]
    lines.extend(segment_of(campaign, book) for campaign in campaigns)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Campaign panel under view {panel.view_id}:"]
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
    lines = ["Campaign index, derived from the held campaigns:"]
    for entry in index.entries:
        lines.append(f"{entry.check} - {entry.title} ({entry.campaign_id})")
    if index.gaps:
        lines.append(
            "Red, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_campaign_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Campaign Gate (M-216)",
        f"{book.title}: {len(book.campaigns)} campaigns held, "
        f"{len(green_campaigns(book))} campaigns standing green, "
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


def parse_campaign_args(args: Any) -> Tuple[str, Any]:
    """Parse the /campaign grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("campaign", "view", "note"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("check", "repo"):
        if len(parts) < 2:
            raise ValueError(USAGE)
        return (head, " ".join(parts[1:]))
    if head in ("index", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
