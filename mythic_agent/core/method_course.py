"""The method, teachable (roadmap slice M-229).

Part IX - The Mythic Method Engine. The roadmap
words: **`mythic tutorial` gains the Method course - a newcomer learns campaigns by running a tiny one.****

What already ships, and what this campaign adds:

* The lessons book already ships as data
  (M-201, ``core/milestones.py``): a roadmap/lesson
  file (parts, campaigns, acceptance stages, state) the
  app reads. This campaign WIRES the book that book's
  book invites - several lessons held across
  campaigns with one ledger over them - as data, in its
  own module, standing in the M-195 copy-and-share
  book book the M-229 book stands in: one mentor
  per book, and the mentor's charge over one
  lesson across its campaign held as a book - a
  lesson. The shipped lessons stand untouched behind
  their seams: this layer holds lessons as data
  over the book's campaigns and rewrites none of them,
  and the lessons book keeps its own standing.
  Lessons stand on the ledger AS DATA alone: a
  lesson carries a ledger ref, a reference held in
  this book; holding, viewing or telling a lesson
  campaigns no lesson live, moves no keeper and files
  nothing.
* No charter row names this campaign: the M-171 TUI
  redesign charter binds Part VIII alone (M-172
  to M-200) and names M-229 on no row, and the
  campaign tests pin that absence live. The M-005
  method charter names no campaign row either: its
  own words name the whole of Part IX as the
  part that executes the charter, and this campaign
  is built to the roadmap words and that
  execution note together.

* A lesson is held whole: the campaign it
  answers for, named by its campaign id; its title;
  the lesson steps it walked, held as data in
  walk lesson; and the evidence it carries, held
  as data by campaign. The lesson walk is EXPLICIT:
  its sequence stands as data
  (:data:`STAGES`, :data:`TRANSITIONS`) -
  begun, guided, practised, proven, taught -
  and a lesson's standing is DERIVED at
  call time from its held steps and evidence
  alone: a lesson that opens anywhere but
  begun, steps where the sequence does not
  allow, carries a bare claim in place of held
  evidence, or has not yet begun taught stands
  open, named in its gaps.
* The evidence is a closed vocabulary in two
  halves: the held evidence - course_ref,
  guide_ref, practice_ref, proof_ref, lesson_ref, evidence
  a mentor can point to - and the bare claims -
  feeling, memory, assertion, summary, which
  stand as no evidence at all. A lesson is
  proven from held evidence alone, never
  from a feeling: a lesson holding a
  bare claim stands open, named in its gaps.
* A lesson stands only for an ACTIVE
  campaign. The book holds each campaign it answers
  for as a reference record - its id, its title
  and its standing, active or queued, held as
  data copied from the roadmap's own telling. A
  lesson naming a campaign that stands
  nowhere in the book refuses BY NAME, and a
  lesson for a campaign that is not active
  refuses BY NAME beside it: the mentor deals with
  the campaign in hand, in roadmap lesson, never a
  queued one, and a campaign whose lesson already
  stands complete is never practised twice - the
  current lesson is derived, so a
  completed campaign is never the current lesson
  twice.
* The lesson's trace is visible. A trace
  record holds one lesson's walked steps
  as one trace line, exactly as walked, beside
  the lesson. The derived trace is
  computed at call time from the lesson's
  held steps; a held trace that no longer agrees
  with it stands stale, named in the ledger - the
  trace is the walk itself, never a retelling
  of it.
* The lesson index is DERIVED at call
  time from the held lessons - one lesson
  per complete lesson, under the step it
  stands at - never a second stored copy that
  could drift. A stored index, standing verdict,
  panel, trace, lesson or current-lesson
  claim on any record refuses by name.
* The current lesson is DERIVED at call
  time - the first held lesson, in held
  lesson, that does not yet stand complete - never
  stored where it could go stale.
* The notes are held as data: a note record
  naming its lesson, its stance - note,
  concern, praise, question, a closed
  vocabulary - and what it feeds back toward,
  one record per lesson stance; holding
  a note posts none of it, the rule stands as
  data (:data:`LESSON_RULE`), and a record
  claiming a lesson was actually taught,
  captured or promoted live refuses BY NAME.
  The mentor lessons - and those lessons, too,
  are held as data here, never sent.
* The shipped data file holds one example book
  in exactly the book a real lesson
  file takes, a loader reads a file anywhere on
  disk, lessons and views are guided as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding a lesson book for a session and
  telling from it. This layer reaches no live
  lesson: it writes no lesson live, files nothing
  to the ledger, captures no candidate, promotes
  nothing, spawns no mentor, destroys nothing,
  publishes nothing, sends nothing as the user,
  exposes no secret, weakens no security and
  opens no network - it holds lessons
  as data and tells them.

Honesty rules, enforced here and pinned by tests:

* **The lesson walk is explicit.** A
  lesson is proven against the held
  steps and legal steps alone; an illegal step
  stands named in its gaps, never silently
  reordered.
* **Complete stands on held evidence alone.** A
  lesson that carries a feeling, a
  memory, an assertion or a summary in place of
  held evidence stands open, named in its gaps:
  a lesson is proven from evidence, not
  vibes.
* **Active campaigns only, in roadmap lesson.** A
  lesson for a missing or queued campaign
  refuses by name; no lesson is invented
  for a campaign the mentor has not guided with.
* **Unknown stays unknown.** A lesson
  whose steps are not yet held stands with its
  steps empty - no step is invented.
* **The index, panel, verdict, trace, lesson
  and current lesson are derived, never
  stored.** Each is derived from the held
  lessons at call time; a stored one
  refuses by name, so it can never drift.
* **One lesson per lesson.** Two
  lessons standing for one lesson id
  refuse by name, and one note record stands per
  lesson stance.
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
    "LESSON_RESOURCE",
    "LESSON_SCHEMA",
    "LESSON_SLICE",
    "LESSON_RULE",
    "PLAIN_EXPLANATION",
    "THE_LESSON_SLICE",
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
    "LessonRecord",
    "IndexLesson",
    "CampaignRef",
    "NoteRecord",
    "LessonBook",
    "LessonIndex",
    "LessonPanel",
    "LessonPanelRow",
    "LessonRegistry",
    "LessonVerdict",
    "LessonView",
    "TargetCount",
    "trace_for_lesson",
    "trace_record",
    "ledger_record",
    "book_record",
    "build_trace",
    "build_book",
    "build_lesson",
    "build_campaign_ref",
    "build_note",
    "build_panel",
    "build_row",
    "build_verdict",
    "build_view",
    "current_lesson",
    "transition_breaks",
    "derive_index",
    "derive_panel",
    "derive_verdict",
    "lesson_for_check",
    "lesson_lesson",
    "lesson_record",
    "first_note",
    "format_book",
    "format_lesson",
    "format_index",
    "format_note",
    "format_stage",
    "format_panel",
    "format_lesson_screen",
    "format_verdict",
    "format_view",
    "index_plain_words",
    "index_record",
    "campaign_record",
    "load_lesson",
    "load_lesson_file",
    "normalize_campaign_state",
    "normalize_stage",
    "normalize_claim_kind",
    "legal_step",
    "next_stage",
    "normalize_stance",
    "normalize_view_filter",
    "note_for_lesson",
    "note_plain_words",
    "note_record",
    "panel_plain_words",
    "panel_record",
    "parse_lesson_args",
    "green_lessons",
    "plain_lines",
    "plain_words",
    "roadmap_record",
    "segment_of",
    "trace_of",
    "trace_current",
    "shown_lessons",
    "validate_trace",
    "validate_book",
    "validate_lesson",
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
    "lesson_gaps",
    "lesson_green",
    "lessons_for_campaign",
]

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

LESSON_SCHEMA = "mythic.method_course/1"
LESSON_SLICE = "M-229"
THE_LESSON_SLICE = LESSON_SLICE
LESSON_RESOURCE = "method_course.yaml"
INDEX_ACTION = "index"
EXAMPLE_STAGE = "taught"
STAGE_FIELDS = ("stages", "claims")
COMPLETE_WORDS = ("complete", "open")
STANCES = ("note", "concern", "praise", "question")
VIEW_FILTERS = ("all", "complete", "open")
VERDICT_WORDS = ("taught", "held", "blocked")
CAMPAIGN_STATES = ("live", "dormant")
LESSON_RULE = 'lessons are held as data alone: several lessons across campaigns stand with one ledger, mentors per lesson, and the human sees the whole forge at a campaign - a lesson stands as data, held by reference (a lesson ref), never taken live - the lesson walk stands as an explicit lesson sequence - begun, guided, practised, proven, taught - and a lesson completes only complete, complete being a state with evidence held - course ref, guide ref, practice ref, proof ref, lesson ref - never a feeling, a memory, an assertion or a summary; `mythic tutorial` gains the Method course - a newcomer learns campaigns by running a tiny one - and a lesson practised without guidance, or taught before it is proven, stands open, named in its gaps; holding, viewing and reading a lesson starts no work live, assigns no mentor, spends nothing, spawns no process and opens no network'
PLAIN_EXPLANATION = 'The method, teachable (M-229): `mythic tutorial` gains the Method course - a newcomer learns campaigns by running a tiny one.'
USAGE = 'Usage: /course | /course lesson <lesson-id> | /course stage <stage> | /course campaign <campaign-id> | /course view <view-id> | /course note <note-id> | /course index | /course panel | /course verdict'

STAGES = ("begun", "guided", "practised", "proven", "taught")
HELD_EVIDENCE = ("course_ref", "guide_ref", "practice_ref", "proof_ref", "lesson_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
CLAIM_KINDS = HELD_EVIDENCE + BARE_CLAIMS
TRANSITIONS = {
    "begun": ("guided",),
    "guided": ("practised",),
    "practised": ("proven",),
    "proven": ("begun", "taught"),
    "taught": (),
}


def legal_step(before: Any, after: Any) -> bool:
    """Whether the gate sequence allows one step, DERIVED.

    The machine stands as data in TRANSITIONS:
    inspect steps only to build, build only to
    test, test to repair on a lesson or to
    continue on a pass, repair back to build or
    test for the rerun, and continue steps
    nowhere - it is where a lesson stands complete.
    A stage outside the machine allows nothing.
    """
    return after in TRANSITIONS.get(before, ())


def next_stage(stage: Any, failed: Any = False) -> Optional[str]:
    """The step the mentor takes next, DERIVED from the sequence.

    Banked leads to guided and guided to
    practised; practised leads to proven; at
    proven a follow-up banking steps back to begun and a finished lesson steps to taught;
    taught is the end of the walk and steps
    nowhere. A step outside the sequence refuses
    by name.
    """
    proven = normalize_stage(stage)
    if proven == "begun":
        return "guided"
    if proven == "guided":
        return "practised"
    if proven == "practised":
        return "proven"
    if proven == "proven":
        return "begun" if failed else "taught"
    return None


_TAUGHTANCE = ("recorded_on", "actor", "source", "origin_session")
_RUN_KEYS = frozenset({
    "lesson_id", "seq", "campaign_id", "title", "stages",
    "claims", "detail",
} | set(_TAUGHTANCE))
_SLICE_REF_KEYS = frozenset({
    "campaign_id", "seq", "title", "state", "detail",
} | set(_TAUGHTANCE))
_TRACE_KEYS = frozenset({
    "trace_id", "seq", "lesson_id", "trace", "detail",
} | set(_TAUGHTANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_TAUGHTANCE))
_ACTION_KEYS = frozenset({
    "note_id", "seq", "lesson_id", "stance", "target", "title",
    "detail",
} | set(_TAUGHTANCE))
_DERIVED_KEYS = frozenset({
    "standing", "complete", "greens", "gaps", "segment",
    "plain_lines", "telling", "verdict", "index",
    "lessons", "coverage", "covered", "uncovered",
    "current_lesson", "next_lesson", "progress", "ledger",
    "current", "lesson", "breaks", "live"})
_LIVE_KEYS = (
    "live_lesson", "lessons_live", "live_question",
    "lessons_raise", "raises_slice", "raised_live",
    "answers_live", "answers_question", "answered_live",
    "delivers_live", "delivered_live", "lessons_live",
    "resumed_live", "runs_lesson", "paused_live",
    "runs_lesson", "ran_lesson", "spawns_process",
    "spawned_process", "builds_slice", "built_slice",
    "builds_live", "executes_slice", "executed_slice",
    "executes_live", "live_execution",
    "banks_slice", "banked_live", "lesson_live",
    "pushes_slice", "pushed_live", "merges_live",
    "merged_live", "opens_network", "writes_file",
    "write_file", "sends_lesson", "sent_lesson",
    "posts_note", "posted_note", "traces_live",
    "traced_live", "writes_ledger", "wrote_ledger", "files_lesson", "filed_live", "spawns_mentor", "spawned_mentor", "sends_lesson", "sent_lesson", "writes_lesson", "wrote_lesson")


# ---------------------------------------------------------------------
# Small judges, in the sibling trace.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_stages(value: Any) -> Tuple[str, ...]:
    """A lesson's walked stages, held as data.

    The stages stand as a list of stage names in
    walk lesson, each one a stage of the explicit
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
    """A lesson's asked claims: claim campaigns named as data.

    Each claim names one campaign from the taught
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


def _taughtance(mapping: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key in _TAUGHTANCE:
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
                f"{what} claims a live gate lesson or campaign build "
                f"execution ({key!r} is named on it): "
                f"{LESSON_RULE}")
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
# The held lesson: one campaign cut from an active campaign.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class LessonRecord:
    """One lesson campaign, held as data.

    The lesson names the active campaign it was
    held from, by campaign id, its title, its
    verifiable stages, held as data, and its
    claims, named by lesson id. The grain is
    derived, never stored: exactly one verifiable
    walk is practised against the machine. A lesson whose
    stages are not yet held stands with its
    stages empty: it stands open, named in
    its gaps, and no stage is invented for it.
    The lesson is local data alone - no live build
    stands behind it: holding it builds nothing.
    """

    lesson_id: str
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
            self, "lesson_id", _clean_text(self.lesson_id, "a lesson id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "campaign_id", _clean_text(self.campaign_id, "an campaign id"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a lesson title"))
        object.__setattr__(
            self, "stages", _check_stages(self.stages))
        object.__setattr__(
            self, "claims", _check_claims(self.claims))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a lesson detail"))
        for key in _TAUGHTANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.lesson_id

    @property
    def stage(self) -> str:
        """The stage the lesson stands at: its last walked stage."""
        return self.stages[-1] if self.stages else ""

    def to_record(self) -> Dict[str, Any]:
        record = {
            "lesson_id": self.lesson_id, "seq": self.seq,
            "campaign_id": self.campaign_id, "title": self.title,
            "stages": list(self.stages),
            "claims": list(self.claims),
            "detail": self.detail,
        }
        for key in _TAUGHTANCE:
            record[key] = getattr(self, key)
        return record


def _check_lesson_ref(value: Any) -> LessonRecord:
    if not isinstance(value, LessonRecord):
        raise ValueError("a lesson must be a LessonRecord")
    return value


def validate_lesson(lesson: Any) -> LessonRecord:
    return _check_lesson_ref(lesson)


def build_lesson(record: Any = None, **kwargs: Any) -> LessonRecord:
    """Build one held lesson from a mapping or fields."""
    if record is None:
        data = dict(kwargs)
    elif isinstance(record, LessonRecord):
        if kwargs:
            raise ValueError("a lesson stands whole or by fields, not both")
        return record
    elif isinstance(record, dict):
        data = dict(record)
        data.update(kwargs)
    else:
        raise ValueError("a lesson must be a mapping or a LessonRecord")
    _needed(data, _RUN_KEYS, "a lesson")
    return LessonRecord(
        lesson_id=data.get("lesson_id"), seq=data.get("seq"),
        campaign_id=data.get("campaign_id"), title=data.get("title"),
        stages=data.get("stages"),
        claims=data.get("claims"),
        detail=data.get("detail"),
        **_taughtance(data))


def _breaks_map(book: Any) -> Dict[str, Tuple[str, ...]]:
    """Map each lesson to the steps it took outside the machine.

    Derived from the held lessons alone: a break is
    one consecutive pair of walked stages the
    explicit gate sequence does not allow, told
    in walk lesson as before, then after.
    """
    found: Dict[str, Tuple[str, ...]] = {}
    for lesson in book.lessons:
        breaks = tuple(
            f"{before} > {after}"
            for before, after in zip(lesson.stages, lesson.stages[1:])
            if not legal_step(before, after))
        if breaks:
            found[lesson.lesson_id] = breaks
    return found

def lesson_gaps(lesson: Any, source: Any = None) -> Tuple[str, ...]:
    """The gaps that keep a lesson from standing complete.

    Guarded from the lesson's own held fields alone -
    its walked steps against the explicit question
    sequence, and its taught evidence against the
    taught vocabulary: the lesson opens at
    named, steps only where the sequence
    allows, carries held evidence and no bare claim,
    and a lesson stands complete only when it has
    begun taught. The source names nothing
    further: no gap is borrowed from another
    lesson.
    """
    proven = _check_lesson_ref(lesson)
    gaps: List[str] = []
    if not proven.stages:
        gaps.append(
            "has passed through no step: the lesson has not started")
        return tuple(gaps)
    if proven.stages[0] != "begun":
        gaps.append(
            f"opens at {proven.stages[0]}, not at begun: "
            f"the lesson opens with the reflection")
    for before, after in zip(proven.stages, proven.stages[1:]):
        if not legal_step(before, after):
            gaps.append(
                f"steps from {before} to {after}, which the "
                f"lesson sequence does not allow")
    for campaign in proven.claims:
        if campaign in BARE_CLAIMS:
            gaps.append(
                f"carries a {campaign} claim, a bare claim with no "
                f"held proof: complete stands on held proof alone")
    if proven.stages[-1] != "taught":
        gaps.append(
            f"has not reached taught: the lesson stands "
            f"at {proven.stages[-1]}")
    return tuple(gaps)

def lesson_green(lesson: Any, source: Any = None) -> bool:
    return not lesson_gaps(lesson, source)


def plain_lines(lesson: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the lesson's own fields."""
    proven = _check_lesson_ref(lesson)
    return (
        f"Lesson: {proven.title}",
        f"Campaign: {proven.campaign_id}",
        f"Stage: {proven.stage if proven.stage else 'none'}",
        f"Claims: "
        f"{', '.join(proven.claims) if proven.claims else 'none'}",
    )


def segment_of(lesson: Any, source: Any = None) -> str:
    proven = _check_lesson_ref(lesson)
    gaps = lesson_gaps(proven, source)
    return (
        f"{proven.lesson_id}: {proven.title} - campaign: "
        f"'{proven.campaign_id}' - stage: "
        f"'{proven.stage if proven.stage else 'none'}' - "
        f"stages: {len(proven.stages)} - claims: "
        f"'{', '.join(proven.claims) if proven.claims else 'none'}' - "
        f"detail: '{proven.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held campaign reference: the active campaign a book lessons from.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CampaignRef:
    """One campaign a lesson book lessons from, held as a reference.

    The record names the campaign, the title it
    opens and its standing - active or
    queued - held as data copied from the
    M-203 campaign book's own telling. A lesson
    stands only from an active reference: the
    book refuses a lesson naming no held reference,
    and a lesson from an queued one, BY NAME.
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
        for key in _TAUGHTANCE:
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
        for key in _TAUGHTANCE:
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
        **_taughtance(data))


# ---------------------------------------------------------------------
# The held trace trace: the human approves the trace, as data.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TraceRecord:
    """One trace trace, held as data.

    The record names its campaign and the trace the
    human active - the campaign's lesson ids in
    derived claim lesson, held exactly as
    active. The trace is of the set and its
    lesson, never of a step: when the derived
    trace moves, this record stands stale, named
    in the ledger, until a new trace is active.
    """

    trace_id: str
    seq: int
    lesson_id: str
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
            self, "lesson_id", _clean_text(self.lesson_id, "an campaign id"))
        object.__setattr__(
            self, "trace", _clean_text(self.trace, "an active trace"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an trace detail"))
        for key in _TAUGHTANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.trace_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "trace_id": self.trace_id, "seq": self.seq,
            "lesson_id": self.lesson_id, "trace": self.trace,
            "detail": self.detail,
        }
        for key in _TAUGHTANCE:
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
        lesson_id=data.get("lesson_id"), trace=data.get("trace"),
        detail=data.get("detail"),
        **_taughtance(data))


# ---------------------------------------------------------------------
# The held stance: a note on a lesson, held as data beside the book.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class NoteRecord:
    """One lesson stance, held as data.

    The record names its lesson, its stance and
    what it feeds back toward, with its title and
    its detail. One record stands per lesson stance
    in a book. The record is data alone: holding
    it builds nothing and posts nothing, ever.
    """

    note_id: str
    seq: int
    lesson_id: str
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
            self, "lesson_id", _clean_text(self.lesson_id, "a lesson id"))
        object.__setattr__(self, "stance", normalize_stance(self.stance))
        object.__setattr__(
            self, "target", _clean_text(self.target, "a stance target"))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a stance title"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a stance detail"))
        for key in _TAUGHTANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.note_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "note_id": self.note_id, "seq": self.seq,
            "lesson_id": self.lesson_id, "stance": self.stance,
            "target": self.target, "title": self.title,
            "detail": self.detail,
        }
        for key in _TAUGHTANCE:
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
        lesson_id=data.get("lesson_id"), stance=data.get("stance"),
        target=data.get("target"), title=data.get("title"),
        detail=data.get("detail"),
        **_taughtance(data))


# ---------------------------------------------------------------------
# The held view: which campaigns a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class LessonView:
    """A view over the book: every lesson, the green, the rest."""

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
        for key in _TAUGHTANCE:
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
        for key in _TAUGHTANCE:
            record[key] = getattr(self, key)
        return record


def _check_view_ref(value: Any) -> LessonView:
    if not isinstance(value, LessonView):
        raise ValueError("a view must be an LessonView")
    return value


def validate_view(view: Any) -> LessonView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> LessonView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, LessonView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an LessonView")
    _needed(data, _VIEW_KEYS, "a view")
    return LessonView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_taughtance(data))


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class LessonPanelRow:
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


def _row_for_lesson(lesson: LessonRecord,
                     source: Any = None) -> LessonPanelRow:
    return LessonPanelRow(
        item_id=lesson.lesson_id,
        standing="complete" if lesson_green(lesson, source) else "open",
        label=lesson.title, segment=segment_of(lesson, source),
        recorded_on=lesson.recorded_on)


def _check_row_ref(value: Any) -> LessonPanelRow:
    if not isinstance(value, LessonPanelRow):
        raise ValueError("a panel row must be an LessonPanelRow")
    return value


def validate_row(row: Any, lesson: Any = None,
                 source: Any = None) -> LessonPanelRow:
    proven = _check_row_ref(row)
    if lesson is not None:
        derived = _row_for_lesson(_check_lesson_ref(lesson), source)
        if proven != derived:
            raise ValueError(
                f"panel row {proven.item_id!r} does not agree with "
                f"the row derived from its lesson")
    return proven


def build_row(row: Any = None, lesson: Any = None,
              source: Any = None,
              **kwargs: Any) -> LessonPanelRow:
    if lesson is not None:
        derived = _row_for_lesson(_check_lesson_ref(lesson), source)
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            LessonPanelRow(**kwargs))
        return validate_row(built, lesson, source)
    if isinstance(row, LessonPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        standing = _clean_text(data.get("standing"), "a row standing").lower()
        if standing not in COMPLETE_WORDS:
            raise ValueError(f"row standing {standing!r} is not a held word")
        return LessonPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            standing=standing,
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on campaign"))
    if row is None and kwargs:
        return LessonPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an LessonPanelRow")


@dataclass(frozen=True)
class TargetCount:
    standing: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"standing": self.standing, "items": self.items}


def _target_counts(rows: Tuple[LessonPanelRow, ...]
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
        f"The lesson book holds {total_items} lessons as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {standing_words}; {green_shown} of the shown lessons "
        f"stand complete.",
        "Rows stand in held lesson, the lesson the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its lesson's own fields "
        "- the campaign it answers for, the steps it walked in the "
        "open and the evidence it honestly carries - and no "
        "judgement is stored on any lesson.",
        "Completeness is practised from the held records alone: "
        "a lesson that steps outside the lesson sequence, "
        "carries a bare claim in place of held evidence, or has "
        "not begun taught stands open, named in its "
        "gaps, and the lesson index is derived from the "
        "held lessons, never stored where it could drift.",
    )

@dataclass(frozen=True)
class LessonPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[LessonPanelRow, ...]
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


def _resolve_view(source: Any, view: Any) -> LessonView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, LessonView):
        return view
    return book.view_for(view)


def shown_lessons(source: Any, view: Any = None
                   ) -> Tuple[LessonRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.lessons
    if resolved.view_filter == "complete":
        return tuple(g for g in book.lessons if lesson_green(g, book))
    return tuple(g for g in book.lessons if not lesson_green(g, book))


def lessons_for_campaign(source: Any, campaign_id: Any
                      ) -> Tuple[LessonRecord, ...]:
    wanted = _clean_text(campaign_id, "an campaign id")
    return tuple(
        g for g in _source_book(source).lessons if g.campaign_id == wanted)


def green_lessons(source: Any) -> Tuple[LessonRecord, ...]:
    book = _source_book(source)
    return tuple(g for g in book.lessons if lesson_green(g, book))


def current_lesson(source: Any) -> Optional[LessonRecord]:
    """The book's current lesson, DERIVED at call time.

    The first held lesson, in held lesson, that does
    not yet stand complete - where the Architect must
    look next. Nothing here is stored: the telling
    is derived from the held lessons alone, so it can
    never go stale against them. A book whose every
    lesson stands complete has no current lesson.
    """
    book = _source_book(source)
    for lesson in book.lessons:
        if not lesson_green(lesson, book):
            return lesson
    return None


def derive_panel(source: Any, view: Any = None) -> LessonPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_lessons(book, resolved)
    rows = tuple(_row_for_lesson(lesson, book) for lesson in shown)
    counts = _target_counts(rows)
    as_of = max((g.recorded_on for g in book.lessons), default="")
    green = sum(1 for g in shown if lesson_green(g, book))
    return LessonPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.lessons), total_shown=len(shown),
        target_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.lessons), len(shown), green, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> LessonPanel:
    if not isinstance(value, LessonPanel):
        raise ValueError("a panel must be an LessonPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> LessonPanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 lesson).
    """
    proven = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(proven.view_id)
                if proven.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "target_counts", "as_of", "account"):
            if getattr(proven, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {proven.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return proven


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> LessonPanel:
    if isinstance(panel, LessonPanel):
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
        built = LessonPanel(
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
    raise ValueError("a panel must be a mapping, an LessonPanel, or derived")


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
        return "taught"
    if green_shown == 0:
        return "blocked"
    return "held"


@dataclass(frozen=True)
class LessonVerdict:
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


def derive_verdict(source: Any, view: Any = None) -> LessonVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_lessons(book, resolved)
    green = sum(1 for g in shown if lesson_green(g, book))
    latest = max((g.recorded_on for g in shown), default="")
    return LessonVerdict(
        verdict=_verdict_word(len(shown), green),
        view_id=resolved.view_id, total_shown=len(shown),
        green_shown=green, latest_on=latest)


def _check_verdict_ref(value: Any) -> LessonVerdict:
    if not isinstance(value, LessonVerdict):
        raise ValueError("a verdict must be an LessonVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> LessonVerdict:
    proven = _check_verdict_ref(verdict)
    if proven.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {proven.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(proven.view_id)
                if proven.view_id is not None else None)
        derived = derive_verdict(book, view)
        if proven != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return proven


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> LessonVerdict:
    if isinstance(verdict, LessonVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = LessonVerdict(
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
        "a verdict must be a mapping, an LessonVerdict, or derived")


# ---------------------------------------------------------------------
# The index: derived from the held campaigns' citations at call time.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IndexLesson:
    stage: str
    lesson_id: str
    title: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "stage": self.stage, "lesson_id": self.lesson_id,
            "title": self.title,
        }


@dataclass(frozen=True)
class LessonIndex:
    """The lesson index, derived from the held lessons.

    The index names one lesson per green lesson, in
    held lesson - the lesson's own one verifiable
    stage, its lesson id and its title - and the
    lessons that do not stand complete, named in its
    gaps. Nothing here is stored on any lesson: the
    index is derived at call time from the held
    records alone, so it can never drift from them.
    """

    lessons: Tuple[IndexLesson, ...]
    gaps: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "lessons": [e.to_record() for e in self.lessons],
            "gaps": list(self.gaps),
        }


def derive_index(source: Any) -> LessonIndex:
    """Derive the lesson index from the book's held lessons."""
    book = _source_book(source)
    lessons = tuple(
        IndexLesson(stage=g.stage, lesson_id=g.lesson_id,
                   title=g.title)
        for g in book.lessons if lesson_green(g, book))
    gaps = tuple(
        g.lesson_id for g in book.lessons if not lesson_green(g, book))
    return LessonIndex(lessons=lessons, gaps=gaps)


def lesson_for_check(source: Any, stage: Any) -> Optional[LessonRecord]:
    """The first held lesson one stage reaches, or none - honestly."""
    if stage is None:
        return None
    if not isinstance(stage, str):
        raise ValueError("an stage must be a string naming the stage")
    wanted = stage.strip()
    if not wanted:
        return None
    for lesson in _source_book(source).lessons:
        if lesson.stage == wanted:
            return lesson
    return None


def transition_breaks(source: Any) -> Tuple[str, ...]:
    """Every step outside the gate sequence, DERIVED.

    One telling per break, in held lesson: the lesson
    that took it and the step it took, before,
    then after. A book whose lessons all walk inside
    the machine tells none.
    """
    book = _source_book(source)
    return tuple(
        f"{lesson_id}: {step}"
        for lesson_id, steps in _breaks_map(book).items()
        for step in steps)

def lesson_lesson(source: Any,
              campaign_id: Any = None) -> Tuple[LessonRecord, ...]:
    """The held lessons in their held lesson, DERIVED at call time.

    Lessons stand in the lesson the book holds them -
    the lesson their campaigns were taken - optionally
    for one campaign alone. Nothing here is stored:
    the lesson is the book's own held lesson, told.
    """
    book = _source_book(source)
    lessons = list(book.lessons)
    if campaign_id is not None:
        wanted = _clean_text(campaign_id, "a campaign id")
        lessons = [r for r in lessons if r.campaign_id == wanted]
    return tuple(lessons)

def trace_of(source: Any, lesson_id: Any) -> str:
    """One lesson's trace, DERIVED at call time.

    The lesson's walked stages joined as one trace
    line, in walk lesson. A lesson that has walked
    nowhere traces empty: the trace tells only
    what stands walked, and the walk is named
    elsewhere.
    """
    lesson = _source_book(source).lesson_for(lesson_id)
    return " > ".join(lesson.stages)

def trace_for_lesson(source: Any,
                  lesson_id: Any) -> Optional[TraceRecord]:
    """The held trace for one lesson, or none - honestly."""
    wanted = _clean_text(lesson_id, "a lesson id")
    for record in _source_book(source).traces:
        if record.lesson_id == wanted:
            return record
    return None

def trace_current(source: Any, lesson_id: Any) -> bool:
    """Whether the held trace agrees with the derived trace.

    The trace stands current only while the trace
    it holds is the trace the book derives now; a
    moved walk leaves it stale, and no trace at
    all traces nothing.
    """
    trace = trace_for_lesson(source, lesson_id)
    if trace is None:
        return False
    return trace.trace == trace_of(source, lesson_id)

def note_for_lesson(source: Any, lesson_id: Any,
                   stance: Any = None) -> Optional[NoteRecord]:
    """The held stance target for one lesson (and stance, when named)."""
    wanted = _clean_text(lesson_id, "a lesson id")
    for record in _source_book(source).notes:
        if record.lesson_id == wanted and (
                stance is None
                or record.stance == normalize_stance(stance)):
            return record
    return None


def first_note(source: Any) -> Optional[NoteRecord]:
    """The first held stance target, standing for the campaign targets, or none."""
    notes = _source_book(source).notes
    return notes[0] if notes else None


def ledger_record(source: Any = None) -> Dict[str, Any]:
    """The lesson ledger, DERIVED here from the held lessons alone.

    The ledger counts the held lessons by their
    derived completeness - green and red - names
    the current lesson, the first that does not yet
    stand complete, tells each held lesson's trace
    standing - current while its held trace
    agrees with its derived trace, stale when it
    has moved, unheld while no trace stands for
    it - and names every step the held lessons took
    outside the gate sequence. Nothing here is
    stored: the telling is derived at call time.
    """
    book = _source_book(source)
    standings = []
    for standing in COMPLETE_WORDS:
        number = sum(
            1 for g in book.lessons
            if ("complete" if lesson_green(g, book) else "open") == standing)
        standings.append({"standing": standing, "lesson_records": number})
    current = current_lesson(book)
    traces = []
    for lesson in book.lessons:
        trace = trace_for_lesson(book, lesson.lesson_id)
        if trace is None:
            standing = "unheld"
        elif trace_current(book, lesson.lesson_id):
            standing = "current"
        else:
            standing = "stale"
        traces.append({"lesson_id": lesson.lesson_id, "trace": standing})
    return {
        "type": "lesson_well",
        "campaign": LESSON_SLICE,
        "standings": standings,
        "total": len(book.lessons),
        "current_lesson": current.lesson_id if current is not None else None,
        "traces": traces,
        "breaks": list(transition_breaks(book)),
    }

def roadmap_record() -> Dict[str, Any]:
    """This campaign's own roadmap standing, proved from the roadmap itself.

    The record loads this campaign's own roadmap through
    the shipped M-017 layer for real and tells its
    counts as they stand: 272 campaigns in 11 parts,
    the begun prefix, the next campaign where the
    lesson lessons, and M-229's own ledger
    standing in Part IX.
    """
    from .roadmap_slices import load_roadmap
    roadmap = load_roadmap()
    own = roadmap.slice(LESSON_SLICE)
    next_slice = roadmap.next_slice()
    return {
        "type": "lesson_roadmap",
        "campaign": LESSON_SLICE,
        "roadmap_file": "roadmap_slices.yaml",
        "roadmap": roadmap.roadmap,
        "parts": len(roadmap.parts),
        "slices": len(roadmap.slices),
        "done": len(roadmap.done()),
        "next_slice": next_slice.id if next_slice is not None else None,
        "m229_title": own.title,
        "m229_part": own.part,
        "m229_status": own.status,
    }


# ---------------------------------------------------------------------
# The book: campaigns, lessons, views, notes and trace traces held
# together, one pinned panel at most per telling, and no verdict,
# index, trace or lesson ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class LessonBook:
    title: str
    campaigns: Tuple[CampaignRef, ...] = ()
    lessons: Tuple[LessonRecord, ...] = ()
    views: Tuple[LessonView, ...] = ()
    notes: Tuple[NoteRecord, ...] = ()
    traces: Tuple[TraceRecord, ...] = ()
    panels: Tuple[LessonPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        campaigns = tuple(_check_campaign_ref(g) for g in self.campaigns)
        lessons = tuple(_check_lesson_ref(g) for g in self.lessons)
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
        lesson_ids = set()
        lesson_seqs = set()
        for lesson in lessons:
            if lesson.lesson_id in lesson_ids:
                raise ValueError(
                    f"two lessons stand under id {lesson.lesson_id!r}")
            if lesson.seq in lesson_seqs:
                raise ValueError(
                    f"two lessons stand at sequence {lesson.seq}")
            lesson_ids.add(lesson.lesson_id)
            lesson_seqs.add(lesson.seq)
        by_slice = {ref.campaign_id: ref for ref in campaigns}
        for lesson in (lessons if campaigns else ()):

            ref = by_slice.get(lesson.campaign_id)
            if ref is None:
                raise ValueError(
                    f"lesson {lesson.lesson_id!r} is held from campaign "
                    f"{lesson.campaign_id!r}, which stands nowhere in "
                    f"this book")
            if ref.state != "live":
                raise ValueError(
                    f"lesson {lesson.lesson_id!r} is held from campaign "
                    f"{lesson.campaign_id!r}, which is not active: "
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
            target = (record.lesson_id, record.stance)
            if target in note_targets:
                raise ValueError(
                    f"two stance records stand for lesson "
                    f"{record.lesson_id!r} under stance "
                    f"{record.stance!r}: one stance stands "
                    f"per lesson target")
            note_ids.add(record.note_id)
            note_seqs.add(record.seq)
            note_targets.add(target)
        trace_ids = set()
        trace_seqs = set()
        trace_lessons = set()
        lesson_ids = {lesson.lesson_id for lesson in lessons}
        for record in traces:
            if record.trace_id in trace_ids:
                raise ValueError(
                    f"two traces stand under id {record.trace_id!r}")
            if record.seq in trace_seqs:
                raise ValueError(
                    f"two traces stand at sequence {record.seq}")
            if record.lesson_id in trace_lessons:
                raise ValueError(
                    f"two traces stand for lesson "
                    f"{record.lesson_id!r}: one trace stands "
                    f"per lesson walk")
            if lessons and record.lesson_id not in lesson_ids:
                raise ValueError(
                    f"trace {record.trace_id!r} traces lesson "
                    f"{record.lesson_id!r}, which stands nowhere in "
                    f"this book")
            trace_ids.add(record.trace_id)
            trace_seqs.add(record.seq)
            trace_lessons.add(record.lesson_id)
        object.__setattr__(
            self, "campaigns", tuple(sorted(campaigns, key=lambda g: g.seq)))
        object.__setattr__(
            self, "lesson_records", tuple(sorted(lessons, key=lambda g: g.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(
            self, "notes", tuple(sorted(notes, key=lambda m: m.seq)))
        object.__setattr__(
            self, "traces",
            tuple(sorted(traces, key=lambda a: a.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.lessons + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(g.lesson_id for g in self.lessons) + tuple(
            v.view_id for v in self.views)

    def lesson_ids(self) -> Tuple[str, ...]:
        return tuple(g.lesson_id for g in self.lessons)

    def campaign_ids(self) -> Tuple[str, ...]:
        return tuple(g.campaign_id for g in self.campaigns)

    def lesson_for(self, lesson_id: Any) -> LessonRecord:
        wanted = _clean_text(lesson_id, "a lesson id")
        for lesson in self.lessons:
            if lesson.lesson_id == wanted:
                return lesson
        raise KeyError(f"no lesson named {wanted!r} stands in this book")

    def slice_for(self, campaign_id: Any) -> CampaignRef:
        wanted = _clean_text(campaign_id, "an campaign id")
        for ref in self.campaigns:
            if ref.campaign_id == wanted:
                return ref
        raise KeyError(f"no campaign named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> LessonView:
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
        for lesson in self.lessons:
            if lesson.lesson_id == wanted:
                return lesson
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "campaigns": [g.to_record() for g in self.campaigns],
            "lesson_records": [g.to_record() for g in self.lessons],
            "views": [v.to_record() for v in self.views],
            "notes": [m.to_record() for m in self.notes],
            "traces": [a.to_record() for a in self.traces],
            "panels": [pn.to_record() for pn in self.panels],
        }


def _judge_book_panels(book: LessonBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: LessonBook) -> None:
    if book.title != "The method, teachable at the M-229 slice run":
        raise ValueError("the shipped example book carries another title")
    if len(book.campaigns) != 3 or len(book.lessons) != 5 or len(book.views) != 2:
        raise ValueError("the shipped example book must hold three campaign references, five lessons and two views")
    if len(book.notes) != 2:
        raise ValueError("the shipped example book must hold two note records")
    if len(book.traces) != 1:
        raise ValueError("the shipped example book must hold one trace record")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m228-campaign":
        raise ValueError("the pinned panel is panel-m228-campaign")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "held" or verdict.green_shown != 3:
        raise ValueError("the shipped example book verdict must stand held at three complete of five")
    index = derive_index(book)
    if [e.stage for e in index.lessons] != ["taught", "taught", "taught"]:
        raise ValueError("the shipped example book index must derive the three held complete lessons in held lesson")
    if index.gaps != ("lesson-bare-lesson", "lesson-leaping-lesson"):
        raise ValueError("the shipped example book must leave the bare and leaping lessons honestly open, named in its gaps")
    found = lesson_for_check(book, EXAMPLE_STAGE)
    if found is None or found.lesson_id != "lesson-held-lesson":
        raise ValueError("the shipped example book must reach its opening lesson under the example stage")
    if trace_of(book, "lesson-held-lesson") != "begun > guided > practised > proven > taught":
        raise ValueError("the shipped example book must derive the opening lesson's trace from its walked steps")
    if not trace_current(book, "lesson-held-lesson"):
        raise ValueError("the shipped example book must hold the opening lesson's trace current")
    first = first_note(book)
    if first is None or first.note_id != "note-note-first":
        raise ValueError("the shipped example book must hold the opening note as its first note lesson")

def validate_book(data: Any, *, require_example: bool = False) -> LessonBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, LessonBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("a lesson book must be a mapping")
    for key in _LIVE_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims a live campaign build or execution "
                f"({key!r} is named on it): {LESSON_RULE}")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its lessons under a view")
    if "lesson_index" in data or "indexes" in data:
        raise ValueError(
            "a book stores no index: the index is derived from "
            "its held lessons at call time")
    if "ledger" in data or "current_lesson" in data:
        raise ValueError(
            "a book stores no ledger and no current lesson: both are "
            "derived from its held lessons at call time")
    if "trace" in data or "lesson" in data:
        raise ValueError(
            "a book stores no trace and no lesson: both are derived "
            "from its held lessons at call time; an trace record "
            "holds the trace the human active")
    if data.get("schema") is not None and (
            data["schema"] != LESSON_SCHEMA):
        raise ValueError(
            f"a book's schema must be "
            f"{LESSON_SCHEMA!r}")
    if data.get("campaign") is not None and (
            data["campaign"] != LESSON_SLICE):
        raise ValueError(
            f"a book's campaign must be {LESSON_SLICE!r}")
    head = data.get("lesson_head") or data.get("method_course") or {}
    if not isinstance(head, dict):
        raise ValueError("a book's lesson head must be a mapping")
    title = head.get("title") or data.get("title")
    campaigns = tuple(build_campaign_ref(g) for g in data.get("campaigns") or ())
    lessons = tuple(build_lesson(g) for g in data.get("lesson_records") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    notes = tuple(build_note(m) for m in data.get("notes") or ())
    traces = tuple(build_trace(a) for a in data.get("traces") or ())
    book = LessonBook(
        title=title, campaigns=campaigns, lessons=lessons, views=views,
        notes=notes, traces=traces, panels=())
    panels = tuple(
        build_panel(pn, book) for pn in data.get("panels") or ())
    book = LessonBook(
        title=book.title, campaigns=book.campaigns, lessons=book.lessons,
        views=book.views, notes=book.notes,
        traces=book.traces, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> LessonBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (LessonBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an LessonBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> LessonBook:
    return validate_book(data, require_example=require_example)


def load_lesson(
        data: Optional[Dict[str, Any]] = None) -> LessonBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(LESSON_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_lesson_file(path: Any) -> LessonBook:
    """Load one lesson file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: campaign references, lessons and views held one by one.
# ---------------------------------------------------------------------

class LessonRegistry:
    """An in-memory holding of campaign references, lessons and views.

    The registry is the pure layer's model of a
    session's lesson book: campaign references are
    held under their ids, lessons are held under
    their ids, one lesson per id and per sequence,
    and views are held in guided lesson, one view
    per sequence and per id. Holding is data only -
    nothing held here builds anything, executes
    anything, or opens a network.
    """

    def __init__(self, book: Any = None) -> None:
        self._slices: List[CampaignRef] = []
        self._lessons: List[LessonRecord] = []
        self._views: List[LessonView] = []
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
        """Hold one campaign reference, practised whole before held."""
        proven = _check_campaign_ref(item)
        return self._register(
            self._slices, proven, "campaign_id", "campaign reference")

    def register_lesson(self, item: Any) -> LessonRecord:
        """Hold one lesson, practised whole before held."""
        proven = _check_lesson_ref(item)
        return self._register(
            self._lessons, proven, "lesson_id", "lesson")

    def register_view(self, view: Any) -> LessonView:
        """Hold one view; a view naming no id takes a fresh one."""
        proven = _check_view_ref(view)
        if not proven.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            proven = build_view({**proven.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, proven, "view_id", "view")

    def register_book(self, book: Any) -> LessonBook:
        """Hold a whole book's records, under its title."""
        proven = build_book(book)
        if self._title is not None and proven.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {proven.title!r}")
        for ref in proven.campaigns:
            self.register_campaign_ref(ref)
        for lesson in proven.lessons:
            self.register_lesson(lesson)
        for view in proven.views:
            self.register_view(view)
        self._title = proven.title
        return self.book()

    def book(self) -> LessonBook:
        return LessonBook(
            title=self._title or "An unheld lesson book",
            campaigns=tuple(self._slices), lessons=tuple(self._lessons),
            views=tuple(self._views), notes=(), traces=(), panels=())

    def list_slices(self) -> Tuple[CampaignRef, ...]:
        return tuple(self._slices)

    def list_lessons(self) -> Tuple[LessonRecord, ...]:
        return tuple(self._lessons)

    def list_views(self) -> Tuple[LessonView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._lessons) + tuple(self._views)

    def get_slice(self, campaign_id: Any) -> CampaignRef:
        return self.book().slice_for(campaign_id)

    def get_lesson(self, lesson_id: Any) -> LessonRecord:
        return self.book().lesson_for(lesson_id)

    def get_view(self, view_id: Any) -> LessonView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records traced for the ledger target.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> LessonBook:
    if source is None:
        return load_lesson()
    if isinstance(source, LessonBook):
        return source
    if isinstance(source, LessonRegistry):
        return source.book()
    return build_book(source)


def _taughtance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _TAUGHTANCE}


def lesson_record(lesson: Any, source: Any = None) -> Dict[str, Any]:
    proven = _check_lesson_ref(lesson)
    book = _source_book(source) if source is not None else None
    record = {
        "type": "lesson_lesson",
        "campaign": LESSON_SLICE,
        "lesson_id": proven.lesson_id,
        "campaign_id": proven.campaign_id,
        "title": proven.title,
        "segment": segment_of(proven, book),
        "complete": lesson_green(proven, book),
        "gaps": list(lesson_gaps(proven, book)),
    }
    record.update(_taughtance_record(proven))
    return record


def campaign_record(ref: Any) -> Dict[str, Any]:
    proven = _check_campaign_ref(ref)
    record = {
        "type": "lesson_run",
        "campaign": LESSON_SLICE,
        "campaign_id": proven.campaign_id,
        "title": proven.title,
        "state": proven.state,
    }
    record.update(_taughtance_record(proven))
    return record


def trace_record(record_in: Any) -> Dict[str, Any]:
    proven = _check_trace_ref(record_in)
    record = {
        "type": "lesson_trace",
        "campaign": LESSON_SLICE,
        "trace_id": proven.trace_id,
        "lesson_id": proven.lesson_id,
        "trace": proven.trace,
    }
    record.update(_taughtance_record(proven))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    proven = _check_view_ref(view)
    record = {
        "type": "lesson_view",
        "campaign": LESSON_SLICE,
        "view_id": proven.view_id, "seq": proven.seq,
        "view_filter": proven.view_filter,
    }
    record.update(_taughtance_record(proven))
    return record


def note_record(record_in: Any) -> Dict[str, Any]:
    proven = _check_note_ref(record_in)
    record = {
        "type": "lesson_note",
        "campaign": LESSON_SLICE,
        "note_id": proven.note_id,
        "lesson_id": proven.lesson_id,
        "stance": proven.stance,
    }
    record.update(_taughtance_record(proven))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    proven = validate_panel(panel, source)
    record = {"type": "lesson_panel",
              "campaign": LESSON_SLICE}
    record.update(proven.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, LessonVerdict):
        proven = validate_verdict(verdict, source)
    else:
        proven = derive_verdict(_source_book(verdict), view)
    record = {"type": "lesson_verdict",
              "campaign": LESSON_SLICE}
    record.update(proven.to_record())
    return record


def index_record(source: Any) -> Dict[str, Any]:
    if isinstance(source, LessonIndex):
        index = source
    else:
        index = derive_index(source)
    record = {"type": "lesson_index",
              "campaign": LESSON_SLICE}
    record.update(index.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    proven = _source_book(book)
    record = {"type": "lesson_book",
              "campaign": LESSON_SLICE,
              "title": proven.title}
    record.update(proven.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(lesson: Any, source: Any = None) -> str:
    proven = _check_lesson_ref(lesson)
    return (
        f"{proven.title} - from {proven.campaign_id}: "
        f"stage {proven.stage if proven.stage else 'none'}, "
        f"claims "
        f"{', '.join(proven.claims) if proven.claims else 'none'}. "
        f"{proven.detail}")


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The lessons stand {verdict.verdict}: "
        f"{verdict.green_shown} of {verdict.total_shown} shown "
        f"lessons stand complete.")


def view_plain_words(view: Any) -> str:
    proven = _check_view_ref(view)
    return f"View {proven.view_id}: shows {proven.view_filter} lessons."


def note_plain_words(record_in: Any) -> str:
    proven = _check_note_ref(record_in)
    return (
        f"Note {proven.note_id}: {proven.stance} "
        f"{proven.lesson_id}, toward {proven.target}. "
        f"{proven.detail}")


def index_plain_words(source: Any) -> str:
    index = (source if isinstance(source, LessonIndex)
             else derive_index(source))
    gaps = ", ".join(index.gaps) or "none"
    return (
        f"The index holds {len(index.lessons)} green lessons; "
        f"red, named in its gaps: {gaps}.")

def format_lesson(lesson: Any, source: Any = None) -> str:
    proven = _check_lesson_ref(lesson)
    book = _source_book(source) if source is not None else None
    lines = [f"{proven.title} ({proven.lesson_id})"]
    lines.extend(plain_lines(proven))
    lines.append(proven.detail)
    if lesson_green(proven, book):
        lines.append(
            "This lesson stands complete - it walked the question "
            "sequence in the open from begun to taught, "
            "and it carries held evidence alone.")
    else:
        lines.append(
            "This lesson stands open - it stands named in "
            f"its gaps: {', '.join(lesson_gaps(proven, book))}, and "
            "nothing is invented for it.")
    return "\n".join(lines)

def format_view(view: Any) -> str:
    proven = _check_view_ref(view)
    return (
        f"View {proven.view_id}: filter {proven.view_filter} - "
        f"{proven.detail}")


def format_note(record_in: Any) -> str:
    proven = _check_note_ref(record_in)
    lines = [
        f"Lesson note {proven.stance} {proven.lesson_id} "
        f"({proven.note_id}): {proven.title}. {proven.detail}"]
    lines.append(
        "This note stands held as data alone - holding "
        "or reading it builds nothing, executes nothing "
        "and posts no note.")
    return "\n".join(lines)


def format_stage(source: Any, stage: Any) -> str:
    lesson = lesson_for_check(source, stage)
    if lesson is not None:
        return format_lesson(lesson, source)
    wanted = stage.strip() if isinstance(stage, str) else stage
    return (
        f"No held lesson stands under stage {wanted!r} yet - the "
        f"stage reaches nothing in this book, and no lesson is "
        f"invented for it.")


def format_book(source: Any = None, campaign_id: Any = None) -> str:
    book = _source_book(source)
    lessons = (lessons_for_campaign(book, campaign_id)
              if campaign_id is not None else book.lessons)
    lines = [f"The Lesson Gate (M-229) - {book.title}"]
    lines.extend(segment_of(lesson, book) for lesson in lessons)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Lesson panel under view {panel.view_id}:"]
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
    lines = ["Lesson index, derived from the held lessons:"]
    for lesson in index.lessons:
        lines.append(f"{lesson.stage} - {lesson.title} ({lesson.lesson_id})")
    if index.gaps:
        lines.append(
            "Red, named honestly: "
            + ", ".join(index.gaps) + ".")
    lines.append(
        "Told from the held records alone - telling "
        "builds nothing, executes nothing and opens no network.")
    return "\n".join(lines)


def format_lesson_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "The Lesson Gate (M-229)",
        f"{book.title}: {len(book.lessons)} lessons held, "
        f"{len(green_lessons(book))} lessons standing green, "
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


def parse_lesson_args(args: Any) -> Tuple[str, Any]:
    """Parse the /lesson grammar into (stance, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("lesson", "view", "note"):
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
