"""Method metrics (roadmap slice M-230).

Part IX - The Mythic Method Engine. The roadmap
words: **slices banked, gate pass rate, repair rounds, calibration - the method's own health on the metrics board.*****

What already ships, and what this campaign adds:

* The readings book already ships as data
  (M-201, ``core/milestones.py``): a roadmap/reading
  file (parts, campaigns, acceptance stages, state) the
  app reads. This campaign WIRES the book that book's
  book invites - several readings held across
  campaigns with one ledger over them - as data, in its
  own module, standing in the M-195 copy-and-share
  book book the M-230 book stands in: one watcher
  per book, and the watcher's charge over one
  reading across its campaign held as a book - a
  reading. The shipped readings stand untouched behind
  their seams: this layer holds readings as data
  over the book's campaigns and rewrites none of them,
  and the readings book keeps its own standing.
  Readings stand on the ledger AS DATA alone: a
  reading carries a ledger ref, a reference held in
  this book; holding, viewing or telling a reading
  campaigns no reading live, moves no keeper and files
  nothing.
* No charter row names this campaign: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-230 on no row, and the
  campaign tests pin that absence live. The M-005
  method charter names no campaign row either: its
  own words name the whole of Part IX as the
  part that executes the charter, and this campaign
  is built to the roadmap words and that
  execution note together.

* A reading is held whole: the campaign it
  answers for, named by its campaign id; its title;
  the reading steps it walked, held as data in
  walk reading; and the evidence it carries, held
  as data by campaign. The reading walk is EXPLICIT:
  its sequence stands as data
  (:data:`STAGES`, :data:`TRANSITIONS`) -
  taken, checked, weighed, calibrated, posted -
  and a reading's standing is DERIVED at
  call time from its held steps and evidence
  alone: a reading that opens anywhere but
  taken, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet taken posted stands
  open, named in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - metrics_ref,
  count_ref, gate_ref, repair_ref, reading_ref, evidence
  a watcher can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A reading is
  calibrated from held evidence alone, never
  from a feeling: a reading holding a
  bare claim stands open, named in its gaps.
* A reading stands only for an ACTIVE
  campaign. The book holds each campaign it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  reading naming a campaign that stands
  nowhere in the book refuses BY NAME, and a
  reading for a campaign that is not active
  refuses BY NAME beside it: the watcher deals with
  the campaign in hand, in roadmap reading, never a
  queued one, and a campaign whose reading already
  stands complete is never weighed twice - the
  current reading is derived, so a
  completed campaign is never the current reading
  twice.
* The reading's trace is visible. A trace
  record holds one reading's walked steps
  as one trace line, exactly as walked, beside
  the reading. The derived trace is
  computed at call time from the reading's
  held steps; a held trace that no longer agrees
  with it stands stale, named in the ledger - the
  trace is the walk itself, never a retelling
  of it.
* The reading index is DERIVED at call
  time from the held readings - one reading
  per complete reading, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, reading or current-reading
  claim on any record refuses by name.
* The current reading is DERIVED at call
  time - the first held reading, in held
  reading, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its reading, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per reading stance; holding
  a note posts none of it, the rule stands as
  data (:data:`READING_RULE`), and a record
  claiming a reading was actually posted,
  captured or promoted live refuses BY NAME.
  The watcher readings - and those readings, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the book a real reading
  file takes, a loader reads a file anywhere on
  disk, readings and views are checked as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a reading book for a session and
  telling from it. This layer reaches no live
  reading: it writes no reading live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no watcher, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds readings
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The reading walk is explicit.** A
  reading is calibrated against the held
  steps and legal steps alone; an illegal step
  stands named in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  reading that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, named in its gaps:
  a reading is calibrated from evidence, not
  vibes.
* **Active campaigns only, in roadmap reading.** A
  reading for a missing or queued campaign
  refuses by name; no reading is invented
  for a campaign the watcher has not checked with.
* **Unknown stays unknown.** A reading
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, reading
  and current reading are derived, never
  stored.** Each is derived from the held
  readings at call time; a stored one
  refuses by name, so it can never drift.
* **One reading per reading.** Two
  readings standing for one reading id
  refuse by name, and one note record stands per
  reading stance.
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
    "READING_RESOURCE",
    "READING_SCHEMA",
    "READING_SLICE",
    "READING_RULE",
    "PLAIN_EXPLANATION",
    "THE_READING_SLICE",
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
    "ReadingRecord",
    "IndexReading",
    "CampaignRef",
    "NoteRecord",
    "ReadingBook",
    "ReadingIndex",
    "ReadingPanel",
    "ReadingPanelRow",
    "ReadingRegistry",
    "ReadingVerdict",
    "ReadingView",
    "TargetCount",
    "trace_for_reading",
    "trace_record",
    "ledger_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_reading",
    "build_campaign_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_reading",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "reading_for_check",
    "reading_reading",
    "reading_record",
    "first_note",
    "format_book",
    "format_reading",
    "format_index",
    "format_note",
    "format_stage",
    "format_panel",
    "format_reading_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "campaign_record",
    "load_reading",
    "load_reading_file",
    "normalize_campaign_state",
    "normalize_stage",
    "normalize_claim_kind",
    "legal_step",
    "next_stage",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_reading",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_reading_args",
    "green_readings",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_readings",
    "validate_trace",
    "validate_book",
    "validate_reading",
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
    "reading_gaps",
    "reading_green",
    "readings_for_campaign",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

READING_SCHEMA = "mythic.method_metrics/1"
READING_SLICE = "M-230"
THE_READING_SLICE = READING_SLICE
READING_RESOURCE = "method_metrics.yaml"
INDEX_ACTION = "index"
EXAMPLE_STAGE = "posted"
STAGE_FIELDS = ("stages", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("posted", "held", "blocked")
CAMPAIGN_STATES = ("live", "dormant")
READING_RULE = "readings are held as data alone: several readings across campaigns stand with one ledger, watchers per reading, and the human sees the whole forge at a campaign - a reading stands as data, held by reference (a reading ref), never taken live - the reading walk stands as an explicit reading sequence - taken, checked, weighed, calibrated, posted - and a reading completes only complete, complete being a state with evidence held - metrics ref, count ref, gate ref, repair ref, reading ref - never a feeling, a memory, an assertion or a summary; slices banked, gate pass rate, repair rounds, calibration - the method's own health on the metrics board - and a reading weighed without checking, or posted before it is calibrated, stands open, named in its gaps; holding, viewing and reading a reading starts no work live, assigns no watcher, spends nothing, spawns no process and opens no network"
PLAIN_EXPLANATION = "Method metrics (M-230): slices banked, gate pass rate, repair rounds, calibration - the method's own health on the metrics board."
USAGE = 'Usage: /metrics | /metrics reading <reading-id> | /metrics stage <stage> | /metrics campaign <campaign-id> | /metrics view <view-id> | /metrics note <note-id> | /metrics index | /metrics panel | /metrics verdict'

STAGES = ("taken", "checked", "weighed", "calibrated", "posted")
HELD_EVIDENCE = ("metrics_ref", "count_ref", "gate_ref", "repair_ref", "reading_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "taken": ("checked",),
    "checked": ("weighed",),
    "weighed": ("calibrated",),
    "calibrated": ("taken", "posted"),
    "posted": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a reading or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a reading stands complete.
    A stage outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_stage(stage: Any, failed: Any = False) -> Optional[str]:
    """The step the watcher takes next, DERIVED from the sequence.

    Banked leads to checked and checked to
    weighed; weighed leads to calibrated; at
    calibrated a follow-up banking steps back to taken and a finished reading steps to posted;
    posted is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    calibrated = normalize_stage(stage)
    if calibrated == "taken":
        return "checked"
    if calibrated == "checked":
        return "weighed"
    if calibrated == "weighed":
        return "calibrated"
    if calibrated == "calibrated":
        return "taken" if failed else "posted"
    return None


_POSTEDANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "reading_id", "seq", "campaign_id", "title", "stages",
    "claims", "detail",
} | set(_POSTEDANCE))
_SLICE_REF_KEYS = frozenset({
    "campaign_id", "seq", "title", "state", "detail",
} | set(_POSTEDANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "reading_id", "trace", "detail",
} | set(_POSTEDANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_POSTEDANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "reading_id", "stance", "target", "title",
    "detail",
} | set(_POSTEDANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "readings", "coverage", "covered", "uncovered",
    "current_reading", "next_reading", "progress", "ledger",
    "current", "reading", "breaks", "live"})
_LIVE_KEYS = (
    "live_reading", "readings_live", "live_question",
    "readings_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "readings_live",
    "resumed_live", "runs_reading", "paused_live",
    "runs_reading", "ran_reading", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "reading_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_reading", "sent_reading",
    "posts_note", "posted_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_reading", "filed_live", "spawns_watcher", "spawned_watcher", "sends_reading", "sent_reading", "writes_reading", "wrote_reading")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_stages(value: Any) -> Tuple[str, ...]:
    """A reading's walked stages, held as data.

    The stages stand as a list of stage names in
    walk reading, each one a stage of the explicit
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
    """A reading's asked claims: claim campaigns named as data.

    Each claim names one campaign from the posted
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


def _postedance(mapping: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key in _POSTEDANCE:
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
                f"{what} claims a live gate reading or campaign build "
                f"execution ({key!r} is named on it): "
                f"{READING_RULE}")
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
# The held reading: one campaign cut from an active campaign.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ReadingRecord:
    """One reading campaign, held as data.

    The reading names the active campaign it was
    held from, by campaign id, its title, its
    verifiable stages, held as data, and its
    claims, named by reading id. The grain is
    derived, never stored: exactly one verifiable
    walk is weighed against the machine. A reading whose
    stages are not yet held stands with its
    stages empty: it stands open, named in
    its gaps, and no stage is invented for it.
    The reading is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    reading_id: str
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
            self, "reading_id", _clean_text(self.reading_id, "a reading id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "campaign_id", _clean_text(self.campaign_id, "an campaign id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a reading title"))
        object.__setattr__(
            self, "stages", _check_stages(self.stages))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a reading detail"))
        for key in _POSTEDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.reading_id

    @property
    def stage(self) -> str:
        """The stage the reading stands at: its last walked stage."""
        return self.stages[-1] if self.stages else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "reading_id": self.reading_id, "seq": self.seq,
            "campaign_id": self.campaign_id, "title": self.title,
            "stages": list(self.stages),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _POSTEDANCE:
            record[key] = getattr(self, key)
        return record


def _check_reading_ref(value: Any) -> ReadingRecord:
    if not isinstance(value, ReadingRecord):
        raise ValueError("a reading must be a ReadingRecord")
    return value


def validate_reading(reading: Any) -> ReadingRecord:
    return _check_reading_ref(reading)


def build_reading(record: Any = None, **kwargs: Any) -> ReadingRecord:
    """Build one held reading from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, ReadingRecord):
        if kwargs:
            raise ValueError("a reading stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a reading must be a mapping or a ReadingRecord")
    _needed(data, _RUN_KEYS, "a reading")
    return ReadingRecord(
        reading_id=data.get("reading_id"), seq=data.get("seq"),
        campaign_id=data.get("campaign_id"), title=data.get("title"),
        stages=data.get("stages"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_postedance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each reading to the steps it took outside the machine.

    Derived from the held readings alone: a break is
    one consecutive pair of walked stages the
    explicit gate sequence does not allow, told
    in walk reading as before, then after.
    """
    found: Dict[str, Tuple[str, ...]] = {}
    for reading in book.readings:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(reading.stages, reading.stages[1:])
            if not legal_step(before, after))
        if breaks:
            found[reading.reading_id] = breaks
    return found

def reading_gaps(reading: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a reading from standing complete.

    Guarded from the reading's own held fields alone -
    its walked steps against the explicit question
    sequence, and its posted evidence against the
    posted vocabulary: the reading opens at
    named, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a reading stands complete only when it has
    taken posted. The source names nothing
    further: no gap is borrowed from another
    reading.
    """
    calibrated = _check_reading_ref(reading)
    gaps: List[str] = []
    if not calibrated.stages:
        gaps.append(
            "has passed through no step: the reading has not started")
        return tuple(gaps)
    if calibrated.stages[0] != "taken":
        gaps.append(
            f"opens at {calibrated.stages[0]}, not at taken: "
            f"the reading opens with the reflection")
    for before, after in zip(calibrated.stages, calibrated.stages[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"reading sequence does not allow")
    for campaign in calibrated.claims:
        if campaign in BARE_CLAIMS:
            gaps.append(
                f"carries a {campaign} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if calibrated.stages[-1] != "posted":
        gaps.append(
            f"has not reached posted: the reading stands "
            f"at {calibrated.stages[-1]}")
    return tuple(gaps)

def reading_green(reading: Any, source: Any = None) -> bool:
    return not reading_gaps(reading, source)


def plain_lines(reading: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the reading's own fields."""
    calibrated = _check_reading_ref(reading)
    return (
        f"Reading: {calibrated.title}",
        f"Campaign: {calibrated.campaign_id}",
        f"Stage: {calibrated.stage if calibrated.stage else 'none'}",
        f"Claims: "
        f"{', '.join(calibrated.claims) if calibrated.claims else 'none'}",
    )


def segment_of(reading: Any, source: Any = None) -> str:
    calibrated = _check_reading_ref(reading)
    gaps = reading_gaps(calibrated, source)
    return (
        f"{calibrated.reading_id}: {calibrated.title} - campaign: "
        f"'{calibrated.campaign_id}' - stage: "
        f"'{calibrated.stage if calibrated.stage else 'none'}' - "
        f"stages: {len(calibrated.stages)} - claims: "
        f"'{', '.join(calibrated.claims) if calibrated.claims else 'none'}' - "
        f"detail: '{calibrated.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held campaign reference: the active campaign a book readings from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CampaignRef:
    """One campaign a reading book readings from, held as a reference.

    The record names the campaign, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 campaign book's own telling. A reading
    stands only from an active reference: the
    book refuses a reading naming no held reference,
    and a reading from an queued one, BY NAME.
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
        for key in _POSTEDANCE:
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
        for key in _POSTEDANCE:
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
        **_postedance(data))


# ---------------------------------------------------------------------
# The held trace trace: the human approves the trace, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TraceRecord:
    """One trace trace, held as data.

    The record names its campaign and the trace the
    human active - the campaign's reading ids in
    derived claim reading, held exactly as
    active. The trace is of the set and its
    reading, never of a step: when the derived
    trace moves, this record stands stale, named
    in the ledger, until a new trace is active.
    """

    trace_id: str
    seq: int
    reading_id: str
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
            self, "reading_id", _clean_text(self.reading_id, "an campaign id"))
        object.__setattr__(
            self, "trace", _clean_text(self.trace, "an active trace"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an trace detail"))
        for key in _POSTEDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.trace_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "trace_id": self.trace_id, "seq": self.seq,
            "reading_id": self.reading_id, "trace": self.trace,
            "detail": self.detail,
        }
        for key in _POSTEDANCE:
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
        reading_id=data.get("reading_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_postedance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a reading, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One reading stance, held as data.

    The record names its reading, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per reading stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    reading_id: str
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
            self, "reading_id", _clean_text(self.reading_id, "a reading id"))
        object.__setattr__(self, "stance", normalize_stance(self.stance))
        object.__setattr__(
            self, "target", _clean_text(self.target, "a stance target"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a stance title"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a stance detail"))
        for key in _POSTEDANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.note_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "note_id": self.note_id, "seq": self.seq,
            "reading_id": self.reading_id, "stance": self.stance,
            "target": self.target, "title": self.title,
            "detail": self.detail,
        }
        for key in _POSTEDANCE:
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
        reading_id=data.get("reading_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_postedance(data))


# ---------------------------------------------------------------------
# The held view: which campaigns a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ReadingView:
    """A view over the book: every reading, the green, the rest."""

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
        for key in _POSTEDANCE:
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
        for key in _POSTEDANCE:
            record[key] = getattr(self, key)
        return record


def _check_view_ref(value: Any) -> ReadingView:
    if not isinstance(value, ReadingView):
        raise ValueError("a view must be an ReadingView")
    return value


def validate_view(view: Any) -> ReadingView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> ReadingView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, ReadingView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an ReadingView")
    _needed(data, _VIEW_KEYS, "a view")
    return ReadingView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_postedance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ReadingPanelRow:
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


def _row_for_reading(reading: ReadingRecord,
                     source: Any = None) -> ReadingPanelRow:
    return ReadingPanelRow(
        item_id=reading.reading_id,
        standing="complete" if reading_green(reading, source) else "open",
        label=reading.title, segment=segment_of(reading, source),
        recorded_on=reading.recorded_on)


def _check_row_ref(value: Any) -> ReadingPanelRow:
    if not isinstance(value, ReadingPanelRow):
        raise ValueError("a panel row must be an ReadingPanelRow")
    return value


def validate_row(row: Any, reading: Any = None,
                 source: Any = None) -> ReadingPanelRow:
    calibrated = _check_row_ref(row)
    if reading is not None:
        derived = _row_for_reading(_check_reading_ref(reading), source)
        if calibrated != derived:
            raise ValueError(
                f"panel row {calibrated.item_id!r} does not agree with "
                f"the row derived from its reading")
    return calibrated


def build_row(row: Any = None, reading: Any = None,
              source: Any = None,
              **kwargs: Any) -> ReadingPanelRow:
    if reading is not None:
        derived = _row_for_reading(_check_reading_ref(reading), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            ReadingPanelRow(**kwargs))
        return validate_row(built, reading, source)
    if isinstance(row, ReadingPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return ReadingPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on campaign"))
    if row is None and kwargs:
        return ReadingPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an ReadingPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[ReadingPanelRow, ...]
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
        f"The reading book holds {total_items} readings as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown readings "
        f"stand complete.",
        "Rows stand in held reading, the reading the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its reading's own fields "
        "- the campaign it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any reading.",
        "Completeness is weighed from the held records alone: "
        "a reading that steps outside the reading sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not taken posted stands open, named in its "
        "gaps, and the reading index is derived from the "
        "held readings, never stored where it could drift.",
    )

@dataclass(frozen=True)
class ReadingPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[ReadingPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> ReadingView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, ReadingView):
        return view
    return book.view_for(view)


def shown_readings(source: Any, view: Any = None
                   ) -> Tuple[ReadingRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.readings
    if resolved.view_filter == "complete":
        return tuple(g for g in book.readings if reading_green(g, book))
    return tuple(g for g in book.readings if not reading_green(g, book))


def readings_for_campaign(source: Any, campaign_id: Any
                      ) -> Tuple[ReadingRecord, ...]:
    wanted = _clean_text(campaign_id, "an campaign id")
    return tuple(
        g for g in _source_book(source).readings if g.campaign_id == wanted)


def green_readings(source: Any) -> Tuple[ReadingRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.readings if reading_green(g, book))


def current_reading(source: Any) -> Optional[ReadingRecord]:
    """The book's current reading, DERIVED at call time.

    The first held reading, in held reading, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held readings alone, so it can
    never go stale against them. A book whose every
    reading stands complete has no current reading.
    """
    book = _source_book(source)
    for reading in book.readings:
        if not reading_green(reading, book):
            return reading
    return None


def derive_panel(source: Any, view: Any = None) -> ReadingPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_readings(book, resolved)
    rows = tuple(_row_for_reading(reading, book) for reading in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.readings), default="")
    green = sum(1 for g in shown if reading_green(g, book))
    return ReadingPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.readings), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.readings), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> ReadingPanel:
    if not isinstance(value, ReadingPanel):
        raise ValueError("a panel must be an ReadingPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> ReadingPanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 reading).
    """
    calibrated = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(calibrated.view_id)
                if calibrated.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(calibrated, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {calibrated.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return calibrated


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> ReadingPanel:
    if isinstance(panel, ReadingPanel):
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
        built = ReadingPanel(
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
    raise ValueError("a panel must be a mapping, an ReadingPanel, or derived")


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
        return "posted"
    if green_shown == 0:
        return "blocked"
    return "held"


@dataclass(frozen=True)
class ReadingVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> ReadingVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_readings(book, resolved)
    green = sum(1 for g in shown if reading_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return ReadingVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> ReadingVerdict:
    if not isinstance(value, ReadingVerdict):
        raise ValueError("a verdict must be an ReadingVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> ReadingVerdict:
    calibrated = _check_verdict_ref(verdict)
    if calibrated.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {calibrated.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(calibrated.view_id)
                if calibrated.view_id is not None else None)
        derived = derive_verdict(book, view)
        if calibrated != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return calibrated


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> ReadingVerdict:
    if isinstance(verdict, ReadingVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = ReadingVerdict(
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
        "a verdict must be a mapping, an ReadingVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held campaigns' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexReading:
    stage: str
    reading_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "stage": self.stage, "reading_id": self.reading_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class ReadingIndex:
    """The reading index, derived from the held readings.

    The index names one reading per green reading, in
    held reading - the reading's own one verifiable
    stage, its reading id and its title - and the
    readings that do not stand complete, named in its
    gaps. Nothing here is stored on any reading: the
    index is derived at call time from the held
    records alone, so it can never drift from them.
    """

    readings: Tuple[IndexReading, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "readings": [e.to_record() for e in self.readings],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> ReadingIndex:
    """Derive the reading index from the book's held readings."""
    book = _source_book(source)
    readings = tuple(
        IndexReading(stage=g.stage, reading_id=g.reading_id,
                   title=g.title)
        for g in book.readings if reading_green(g, book))
    gaps = tuple(
        g.reading_id for g in book.readings if not reading_green(g, book))
    return ReadingIndex(readings=readings, gaps=gaps)


def reading_for_check(source: Any, stage: Any) -> Optional[ReadingRecord]:
    """The first held reading one stage reaches, or none - honestly."""
    if stage is None:
        return None
    if not isinstance(stage, str):
        raise ValueError("an stage must be a string naming the stage")
    wanted = stage.strip()
    if not wanted:
        return None
    for reading in _source_book(source).readings:
        if reading.stage == wanted:
            return reading
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held reading: the reading
    that took it and the step it took, before,
    then after. A book whose readings all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{reading_id}: {step}"
        for reading_id, steps in _breaks_map(book).items()
        for step in steps)

def reading_reading(source: Any,
              campaign_id: Any = None) -> Tuple[ReadingRecord, ...]:
    """The held readings in their held reading, DERIVED at call time.

    Readings stand in the reading the book holds them -
    the reading their campaigns were taken - optionally
    for one campaign alone. Nothing here is stored:
    the reading is the book's own held reading, told.
    """
    book = _source_book(source)
    readings = list(book.readings)
    if campaign_id is not None:
        wanted = _clean_text(campaign_id, "a campaign id")
        readings = [r for r in readings if r.campaign_id == wanted]
    return tuple(readings)

def trace_of(source: Any, reading_id: Any) -> str:
    """One reading's trace, DERIVED at call time.

    The reading's walked stages joined as one trace
    line, in walk reading. A reading that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is named
    elsewhere.
    """
    reading = _source_book(source).reading_for(reading_id)
    return " > ".join(reading.stages)

def trace_for_reading(source: Any,
                  reading_id: Any) -> Optional[TraceRecord]:
    """The held trace for one reading, or none - honestly."""
    wanted = _clean_text(reading_id, "a reading id")
    for record in _source_book(source).traces:
        if record.reading_id == wanted:
            return record
    return None

def trace_current(source: Any, reading_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_reading(source, reading_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, reading_id)

def note_for_reading(source: Any, reading_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one reading (and stance, when named)."""
    wanted = _clean_text(reading_id, "a reading id")
    for record in _source_book(source).notes:
        if record.reading_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the campaign targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def ledger_record(source: Any = None) -> Dict[str, Any]:
    """The reading ledger, DERIVED here from the held readings alone.

    The ledger counts the held readings by their
    derived completeness - green and red - names
    the current reading, the first that does not yet
    stand complete, tells each held reading's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held readings took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.readings
            if ("complete" if reading_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "reading_records": number})
    current = current_reading(book)
    traces = []
    for reading in book.readings:
        trace = trace_for_reading(book, reading.reading_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, reading.reading_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"reading_id": reading.reading_id, "trace": standing})
    return {
        "type": "reading_well",
        "campaign": READING_SLICE,
        "standings": standings,
        "total": len(book.readings),
        "current_reading": current.reading_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This campaign's own roadmap standing, proved from the roadmap itself.

    The record loads this campaign's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 campaigns in 11 parts,
    the taken prefix, the next campaign where the
    reading readings, and M-230's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(READING_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "reading_roadmap",
        "campaign": READING_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m230_title": own.title,
        "m230_part": own.part,
        "m230_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: campaigns, readings, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or reading ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class ReadingBook:
    title: str
    campaigns: Tuple[CampaignRef, ...] = ()
    readings: Tuple[ReadingRecord, ...] = ()
    views: Tuple[ReadingView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[ReadingPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        campaigns = tuple(_check_campaign_ref(g) for g in self.campaigns)
        readings = tuple(_check_reading_ref(g) for g in self.readings)
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
        reading_ids = set()
        reading_seqs = set()
        for reading in readings:
            if reading.reading_id in reading_ids:
                raise ValueError(
                    f"two readings stand under id {reading.reading_id!r}")
            if reading.seq in reading_seqs:
                raise ValueError(
                    f"two readings stand at sequence {reading.seq}")
            reading_ids.add(reading.reading_id)
            reading_seqs.add(reading.seq)
        by_slice = {ref.campaign_id: ref for ref in campaigns}
        for reading in (readings if campaigns else ()):

            ref = by_slice.get(reading.campaign_id)
            if ref is None:
                raise ValueError(
                    f"reading {reading.reading_id!r} is held from campaign "
                    f"{reading.campaign_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "live":
                raise ValueError(
                    f"reading {reading.reading_id!r} is held from campaign "
                    f"{reading.campaign_id!r}, which is not active: "
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
            target = (record.reading_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for reading "
                    f"{record.reading_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per reading target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_readings = set()
        reading_ids = {reading.reading_id for reading in readings}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.reading_id in trace_readings:
                raise ValueError(
                    f"two traces stand for reading "
                    f"{record.reading_id!r}: one trace stands "
                    f"per reading walk")
            if readings and record.reading_id not in reading_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces reading "
                    f"{record.reading_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_readings.add(record.reading_id)
        object.__setattr__(
            self, "campaigns", tuple(sorted(campaigns, key=lambda g: g.seq)))
        object.__setattr__(
            self, "reading_records", tuple(sorted(readings, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.readings + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.reading_id for g in self.readings) + tuple(
            v.view_id for v in self.views)

    def reading_ids(self) -> Tuple[str, ...]:
        return tuple(g.reading_id for g in self.readings)

    def campaign_ids(self) -> Tuple[str, ...]:
        return tuple(g.campaign_id for g in self.campaigns)

    def reading_for(self, reading_id: Any) -> ReadingRecord:
        wanted = _clean_text(reading_id, "a reading id")
        for reading in self.readings:
            if reading.reading_id == wanted:
                return reading
        raise KeyError(f"no reading named {wanted!r} stands in this book")

    def slice_for(self, campaign_id: Any) -> CampaignRef:
        wanted = _clean_text(campaign_id, "an campaign id")
        for ref in self.campaigns:
            if ref.campaign_id == wanted:
                return ref
        raise KeyError(f"no campaign named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> ReadingView:
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
        for reading in self.readings:
            if reading.reading_id == wanted:
                return reading
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "campaigns": [g.to_record() for g in self.campaigns],
            "reading_records": [g.to_record() for g in self.readings],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: ReadingBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: ReadingBook) -> None:
    if book.title != "Method metrics at the M-230 slice run":
        raise ValueError("the shipped example book carries another title")
    if len(book.campaigns) != 3 or len(book.readings) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three campaign references, five readings and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m229-campaign":
        raise ValueError("the pinned panel is panel-m229-campaign")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.stage for e in index.readings] != ["posted", "posted", "posted"]:
        raise ValueError("the shipped example book index must derive the three held complete readings in held reading")
    if index.gaps != ("reading-bare-reading", "reading-leaping-reading"):
        raise ValueError("the shipped example book must leave the bare and leaping readings honestly open, named in its gaps")
    found = reading_for_check(book, EXAMPLE_STAGE)
    if found is None or found.reading_id != "reading-held-reading":
        raise ValueError("the shipped example book must reach its opening reading under the example stage")
    if trace_of(book, "reading-held-reading") != "taken > checked > weighed > calibrated > posted":
        raise ValueError("the shipped example book must derive the opening reading's trace from its walked steps")
    if not trace_current(book, "reading-held-reading"):
        raise ValueError("the shipped example book must hold the opening reading's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note reading")

def validate_book(data: Any, *, require_example: bool = False) -> ReadingBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, ReadingBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a reading book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live campaign build or execution "
                f"({key!r} is named on it): {READING_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its readings under a view")
    if "reading_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held readings at call time")
    if "ledger" in data or "current_reading" in data:
        raise ValueError(
            "a book stores no ledger and no current reading: both are "
            "derived from its held readings at call time")
    if "trace" in data or "reading" in data:
        raise ValueError(
            "a book stores no trace and no reading: both are derived "
            "from its held readings at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != READING_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{READING_SCHEMA!r}")
    if data.get("campaign") is not None and (
            data["campaign"] != READING_SLICE):
        raise ValueError(
            f"a book's campaign must be {READING_SLICE!r}")
    head = data.get("reading_head") or data.get("method_metrics") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's reading head must be a mapping")
    title = head.get("title") or data.get("title")
    campaigns = tuple(build_campaign_ref(g) for g in data.get("campaigns") or ())
    readings = tuple(build_reading(g) for g in data.get("reading_records") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = ReadingBook(
        title=title, campaigns=campaigns, readings=readings, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = ReadingBook(
        title=book.title, campaigns=book.campaigns, readings=book.readings,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> ReadingBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (ReadingBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an ReadingBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> ReadingBook:
    return validate_book(data, require_example=require_example)


def load_reading(
        data: Optional[Dict[str, Any]] = None) -> ReadingBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(READING_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_reading_file(path: Any) -> ReadingBook:
    """Load one reading file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: campaign references, readings and views held one by one.
# ---------------------------------------------------------------------

class ReadingRegistry:
    """An in-memory holding of campaign references, readings and views.

    The registry is the pure layer's model of a
    session's reading book: campaign references are
    held under their ids, readings are held under
    their ids, one reading per id and per sequence,
    and views are held in checked reading, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[CampaignRef] = []
        self._readings: List[ReadingRecord] = []
        self._views: List[ReadingView] = []
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
        """Hold one campaign reference, weighed whole before held."""
        calibrated = _check_campaign_ref(item)
        return self._register(
            self._slices, calibrated, "campaign_id", "campaign reference")

    def register_reading(self, item: Any) -> ReadingRecord:
        """Hold one reading, weighed whole before held."""
        calibrated = _check_reading_ref(item)
        return self._register(
            self._readings, calibrated, "reading_id", "reading")

    def register_view(self, view: Any) -> ReadingView:
        """Hold one view; a view naming no id takes a fresh one."""
        calibrated = _check_view_ref(view)
        if not calibrated.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            calibrated = build_view({**calibrated.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, calibrated, "view_id", "view")

    def register_book(self, book: Any) -> ReadingBook:
        """Hold a whole book's records, under its title."""
        calibrated = build_book(book)
        if self._title is not None and calibrated.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {calibrated.title!r}")
        for ref in calibrated.campaigns:
            self.register_campaign_ref(ref)
        for reading in calibrated.readings:
            self.register_reading(reading)
        for view in calibrated.views:
            self.register_view(view)
        self._title = calibrated.title
        return self.book()

    def book(self) -> ReadingBook:
        return ReadingBook(
            title=self._title or "An unheld reading book",
            campaigns=tuple(self._slices), readings=tuple(self._readings),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[CampaignRef, ...]:
        return tuple(self._slices)

    def list_readings(self) -> Tuple[ReadingRecord, ...]:
        return tuple(self._readings)

    def list_views(self) -> Tuple[ReadingView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._readings) + tuple(self._views)

    def get_slice(self, campaign_id: Any) -> CampaignRef:
        return self.book().slice_for(campaign_id)

    def get_reading(self, reading_id: Any) -> ReadingRecord:
        return self.book().reading_for(reading_id)

    def get_view(self, view_id: Any) -> ReadingView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the ledger target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> ReadingBook:
    if source is None:
        return load_reading()
    if isinstance(source, ReadingBook):
        return source
    if isinstance(source, ReadingRegistry):
        return source.book()
    return build_book(source)


def _postedance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _POSTEDANCE}


def reading_record(reading: Any, source: Any = None) -> Dict[str, Any]:
    calibrated = _check_reading_ref(reading)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "reading_reading",
        "campaign": READING_SLICE,
        "reading_id": calibrated.reading_id,
        "campaign_id": calibrated.campaign_id,
        "title": calibrated.title,
        "segment": segment_of(calibrated, book),
        "complete": reading_green(calibrated, book),
        "gaps": list(reading_gaps(calibrated, book)),
    }
    record.update(_postedance_record(calibrated))
    return record


def campaign_record(ref: Any) -> Dict[str, Any]:
    calibrated = _check_campaign_ref(ref)
    record = {
        "type": "reading_run",
        "campaign": READING_SLICE,
        "campaign_id": calibrated.campaign_id,
        "title": calibrated.title,
        "state": calibrated.state,
    }
    record.update(_postedance_record(calibrated))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    calibrated = _check_trace_ref(record_in)
    record = {
        "type": "reading_trace",
        "campaign": READING_SLICE,
        "trace_id": calibrated.trace_id,
        "reading_id": calibrated.reading_id,
        "trace": calibrated.trace,
    }
    record.update(_postedance_record(calibrated))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    calibrated = _check_view_ref(view)
    record = {
        "type": "reading_view",
        "campaign": READING_SLICE,
        "view_id": calibrated.view_id, "seq": calibrated.seq,
        "view_filter": calibrated.view_filter,
    }
    record.update(_postedance_record(calibrated))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    calibrated = _check_note_ref(record_in)
    record = {
        "type": "reading_note",
        "campaign": READING_SLICE,
        "note_id": calibrated.note_id,
        "reading_id": calibrated.reading_id,
        "stance": calibrated.stance,
    }
    record.update(_postedance_record(calibrated))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    calibrated = validate_panel(panel, source)
    record = {"type": "reading_panel",
              "campaign": READING_SLICE}
    record.update(calibrated.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, ReadingVerdict):
        calibrated = validate_verdict(verdict, source)
    else:
        calibrated = derive_verdict(_source_book(verdict), view)
    record = {"type": "reading_verdict",
              "campaign": READING_SLICE}
    record.update(calibrated.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, ReadingIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "reading_index",
              "campaign": READING_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    calibrated = _source_book(book)
    record = {"type": "reading_book",
              "campaign": READING_SLICE,
              "title": calibrated.title}
    record.update(calibrated.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(reading: Any, source: Any = None) -> str:
    calibrated = _check_reading_ref(reading)
    return (
        f"{calibrated.title} - from {calibrated.campaign_id}: "
        f"stage {calibrated.stage if calibrated.stage else 'none'}, "
        f"claims "
        f"{', '.join(calibrated.claims) if calibrated.claims else 'none'}. "
        f"{calibrated.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The readings stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"readings stand complete.")


def view_plain_words(view: Any) -> str:
    calibrated = _check_view_ref(view)
    return f"View {calibrated.view_id}: shows {calibrated.view_filter} readings."


def note_plain_words(record_in: Any) -> str:
    calibrated = _check_note_ref(record_in)
    return (
        f"Note {calibrated.note_id}: {calibrated.stance} "
        f"{calibrated.reading_id}, toward {calibrated.target}. "
        f"{calibrated.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, ReadingIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.readings)} green readings; "
        f"red, named in its gaps: {gaps}.")

def format_reading(reading: Any, source: Any = None) -> str:
    calibrated = _check_reading_ref(reading)
    book = _source_book(source) if source is not None else None
    lines = [f"{calibrated.title} ({calibrated.reading_id})"]
    lines.extend(plain_lines(calibrated))
    lines.append(calibrated.detail)
    if reading_green(calibrated, book):
        lines.append(
            "This reading stands complete - it walked the question "
            "sequence in the open from taken to posted, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This reading stands open - it stands named in "
            f"its gaps: {', '.join(reading_gaps(calibrated, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    calibrated = _check_view_ref(view)
    return (
        f"View {calibrated.view_id}: filter {calibrated.view_filter} - "
        f"{calibrated.detail}")


def format_note(record_in: Any) -> str:
    calibrated = _check_note_ref(record_in)
    lines = [
        f"Reading note {calibrated.stance} {calibrated.reading_id} "
        f"({calibrated.note_id}): {calibrated.title}. {calibrated.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_stage(source: Any, stage: Any) -> str:
    reading = reading_for_check(source, stage)
    if reading is not None:
        return format_reading(reading, source)
    wanted = stage.strip() if isinstance(stage, str) else stage
    return (
        f"No held reading stands under stage {wanted!r} yet - the "
        f"stage reaches nothing in this book, and no reading is "
        f"invented for it.")


def format_book(source: Any = None, campaign_id: Any = None) -> str:
    book = _source_book(source)
    readings = (readings_for_campaign(book, campaign_id)
              if campaign_id is not None else book.readings)
    lines = [f"The Reading Gate (M-230) - {book.title}"]
    lines.extend(segment_of(reading, book) for reading in readings)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Reading panel under view {panel.view_id}:"]
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
    lines = ["Reading index, derived from the held readings:"]
    for reading in index.readings:
        lines.append(f"{reading.stage} - {reading.title} ({reading.reading_id})")
    if index.gaps:
        lines.append(
            "Red, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_reading_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Reading Gate (M-230)",
        f"{book.title}: {len(book.readings)} readings held, "
        f"{len(green_readings(book))} readings standing green, "
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


def parse_reading_args(args: Any) -> Tuple[str, Any]:
    """Parse the /reading grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("reading", "view", "note"):
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
