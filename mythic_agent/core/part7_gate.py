"""The Part VII gate (All-Features roadmap slice M-170).

Part VII — Memory & Context — closes here. The
roadmap's gate words: *a week-old benchmark session
resumed — the coder states the situation correctly
from memory alone, then finishes the task; compaction
glass-box verified mid-run.*

This module is the gate's machinery:

* A validated gate record
  (``mythic_agent/data/part7_gate.yaml``) naming the
  Part VII slices it closes over (M-147..M-169), the
  M-169 confirmation-suite baseline it is banked
  against, and the one resumed-benchmark exercise: a
  benchmark session recorded seven days before its
  resume, holding its whole situation as the shipped
  M-153 session-memory shape (carried memory-map
  facts, open work, standing decisions — the
  transcript counted, never carried), the coder's
  resumed statement held claim by claim beside the
  recorded truth it must match, the mid-run
  compaction held as the shipped M-151 glass-box
  shape (the replaced material kept whole, the
  summary held as its versions, edited once and
  verified mid-run), the grading line of the task
  the session finishes, and one layer row for every
  shipped memory slice M-150..M-169 naming the core
  module and slice constant that carry it.
* The gate's tests re-prove the exercise live on
  every run through the shipped pure roads named in
  the record — M-153's ``build_situation`` /
  ``derive_panel`` (the recorded situation builds
  whole and its derived panel is exactly the pieces
  the statement claims), M-151's ``build_record`` /
  ``derive_panel`` / ``edit_record`` (the compaction
  builds whole, its panel closes on the record's
  counts, and an edit appends a version without
  rewriting any earlier one), M-163's
  ``handoff_from_session_situation`` (the week-old
  handoff the resume began from stands over the
  situation by its references alone), and every
  layer row's own module, imported and checked
  against its own slice constant — wired by the
  gate's tests, so this core module imports no
  service layer at all.

Honesty rules, enforced by the validator and pinned
by tests:

* Exactly one exercise: the resumed benchmark. It
  is ``completed`` only with its evidence kind
  stated — ``pure-roads-measured``: every step rides
  a real shipped pure road at the data level, and
  **no step is faked, stubbed, or claimed beyond
  what the tests do**. No live session is resumed,
  no model is called and no token is spent by the
  gate itself; the campaign tree is never the
  exercise repo.
* The week must be a week: the resumed day stands
  exactly seven days after the recorded day, and
  the situation's saved day is the recorded day.
* The statement must be correct from memory alone:
  one claim per situation piece, every claim's
  stated words equal to its truth words, and every
  truth cross-checked against the situation piece
  itself — a record cannot lie in both places. The
  transcript is counted, never carried: no
  transcript content stands anywhere in the record.
* The compaction must be glass-box: the replaced
  material is held whole, the summary stands as at
  least two versions (the compaction's own and the
  mid-run edit — shown and editable, never a silent
  rewrite), the stored counts are the material's own
  counts, and the verification stage is ``mid-run``.
* The task must finish: the grading line closes
  with every grading test passed, from a pause
  where fewer passed.
* The layers must close: one row for every memory
  slice M-150..M-169, each naming the shipped
  module and constant that carry that slice.
* The baseline section must close arithmetically:
  the M-169 confirmation suite's counted totals.
* The verdict is ``PASS`` and the validator accepts
  no other verdict: a gate that has failed is a
  defect to fix, not a record.

No agent layer is owed and none is built: the part
gates ride no live Agent road of their own (the
M-094 / M-120 / M-146 precedent) — the exercise
rides the shipped pure roads, wired by the gate's
tests, and holds no session state. No new setting
is owed: the memory layers are the roads that
already ship.
"""

from __future__ import annotations

__all__ = [
    "BASELINE_RESOURCE",
    "EVIDENCE_KINDS",
    "EXERCISE_IDS",
    "GATE_RESOURCE",
    "GATE_SCHEMA",
    "GATE_SLICE",
    "LAYER_SLICE_IDS",
    "PART7_GATE_SLICE",
    "PLAIN_EXPLANATION",
    "SLICE_IDS",
    "Any",
    "CompactionCheck",
    "Dict",
    "Exercise",
    "Gate",
    "LayerRef",
    "List",
    "MemoryNote",
    "OpenWork",
    "Optional",
    "Situation",
    "SliceRef",
    "StandingDecision",
    "StatementClaim",
    "Tuple",
    "gate_record",
    "load_gate",
    "plain_words",
    "render_markdown",
    "validate_gate",
]

import re
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .validation import ValidationError

#: Resource name of the gate data file inside ``mythic_agent/data``.
GATE_RESOURCE = "part7_gate.yaml"

#: The only schema this loader accepts.
GATE_SCHEMA = "mythic.part7_gate/1"

#: The slice that owns this gate.
GATE_SLICE = "M-170"

#: The shorter name other layers cite for this slice.
PART7_GATE_SLICE = GATE_SLICE

#: The Part VII slices this gate closes over, in roadmap order.
SLICE_IDS = tuple(f"M-{n:03d}" for n in range(147, 170))

#: The shipped memory slices the exercise stands over, in order.
LAYER_SLICE_IDS = tuple(f"M-{n:03d}" for n in range(150, 170))

#: The confirmation suite the gate is banked against.
BASELINE_RESOURCE = "m169_confirmation_suite"

#: The gate's exercises, in roadmap order.
EXERCISE_IDS = ("resumed_benchmark",)

#: Evidence kinds an exercise may honestly claim.
EVIDENCE_KINDS = ("pure-roads-measured",)

#: The claim kinds: one per kind of situation piece.
CLAIM_KINDS = ("memory", "slice", "decision")

#: The shipped project memory map's sections (M-150).
MAP_SECTIONS = ("architecture", "decision", "gotcha", "location")

#: The shipped session store's statuses (M-153).
SESSION_STATUSES = (
    "idle", "running", "completed", "failed",
    "cancelled", "interrupted")

#: The states one open piece of work may stand in (M-153).
OPEN_STATES = ("open", "in-progress", "blocked")

#: Each memory slice's shipped road: module -> slice constant.
LAYER_ROADS = {
    "M-150": ("project_memory_map", "PROJECT_MEMORY_MAP_SLICE"),
    "M-151": ("compaction_glassbox", "COMPACTION_GLASSBOX_SLICE"),
    "M-152": ("graph_retrieval", "GRAPH_RETRIEVAL_SLICE"),
    "M-153": ("session_memory", "SESSION_MEMORY_SLICE"),
    "M-154": ("cross_project_memory", "CROSS_PROJECT_SLICE"),
    "M-155": ("self_improving_ledger", "SELF_IMPROVING_SLICE"),
    "M-156": ("decision_records", "DECISION_RECORDS_SLICE"),
    "M-157": ("forget_quarantine", "FORGET_QUARANTINE_SLICE"),
    "M-158": ("context_recipes", "CONTEXT_RECIPES_SLICE"),
    "M-159": ("pinning_protection", "PINNING_PROTECTION_SLICE"),
    "M-160": ("token_thrift", "TOKEN_THRIFT_SLICE"),
    "M-161": ("long_session_endurance",
              "LONG_SESSION_ENDURANCE_SLICE"),
    "M-162": ("multi_session_projects",
              "MULTI_SESSION_PROJECTS_SLICE"),
    "M-163": ("handoff_summaries", "HANDOFF_SUMMARIES_SLICE"),
    "M-164": ("memory_import_export", "MEMORY_IMPORT_EXPORT_SLICE"),
    "M-165": ("subconscious_v2", "SUBCONSCIOUS_V2_SLICE"),
    "M-166": ("contradiction_watch", "CONTRADICTION_WATCH_SLICE"),
    "M-167": ("private_by_architecture",
              "PRIVATE_BY_ARCHITECTURE_SLICE"),
    "M-168": ("memory_doctor", "MEMORY_DOCTOR_SLICE"),
    "M-169": ("cold_start", "COLD_START_SLICE"),
}

PLAIN_EXPLANATION = (
    "Part VII gate: a benchmark session recorded a "
    "week before its resume — the coder states the "
    "situation correctly from memory alone, claim by "
    "claim against the recorded truth, the compaction "
    "glass-box verified mid-run with its replaced "
    "material whole and its summary standing as its "
    "versions, and the task then finished with its "
    "grading line closed — re-proven live by the "
    "gate's tests through the shipped pure roads: "
    "M-153's situation and panel, M-151's record, "
    "panel and edit road, M-163's handoff raised over "
    "the situation, and every memory slice "
    "M-150..M-169 standing in its own shipped module "
    "under its own slice constant. This layer holds "
    "the gate record as data only; the gate's tests "
    "own the live re-proof."
)

_ID_RE = re.compile(r"^M-\d{3}$")


@dataclass(frozen=True)
class SliceRef:
    """One Part VII slice the gate closes over."""

    slice: str
    title: str


@dataclass(frozen=True)
class LayerRef:
    """One shipped memory slice's road: module and constant."""

    slice: str
    module: str
    constant: str


@dataclass(frozen=True)
class MemoryNote:
    """One carried memory-map fact in the recorded situation.

    The shipped M-153 carried-memory shape: a section
    of the shipped M-150 map, a title, the fact itself
    in plain words, where it was read from, and where
    the thing it names lives.
    """

    note_id: str
    section: str
    title: str
    detail: str
    source: str
    ref: str


@dataclass(frozen=True)
class OpenWork:
    """One piece of roadmap work standing open at recording."""

    slice_id: str
    title: str
    state: str
    note: str


@dataclass(frozen=True)
class StandingDecision:
    """One decision standing as settled when the day ended."""

    decision_id: str
    title: str
    decision: str
    source: str


@dataclass(frozen=True)
class Situation:
    """The recorded situation, in the shipped M-153 shape.

    The transcript is counted, never carried: only
    ``transcript_messages`` stands here, and no
    transcript content stands anywhere in the record.
    """

    session_ref: str
    workspace: str
    title: str
    saved_on: str
    status: str
    transcript_messages: int
    memory: Tuple[MemoryNote, ...]
    open_work: Tuple[OpenWork, ...]
    decisions: Tuple[StandingDecision, ...]
    situation_id: Optional[str] = None

    def pieces(self) -> Tuple[Tuple[str, str, str, str], ...]:
        """Every carried piece: (kind, item id, title, truth)."""
        found: List[Tuple[str, str, str, str]] = []
        for note in self.memory:
            found.append(("memory", note.note_id, note.title, note.detail))
        for work in self.open_work:
            found.append(("slice", work.slice_id, work.title, work.note))
        for decision in self.decisions:
            found.append(("decision", decision.decision_id,
                          decision.title, decision.decision))
        return tuple(found)

    def piece_ids(self) -> Tuple[str, ...]:
        """The pieces' own ids, in held order (evidence refs)."""
        return tuple(piece[1] for piece in self.pieces())


@dataclass(frozen=True)
class StatementClaim:
    """One claim of the resumed statement, beside its truth."""

    kind: str
    item_id: str
    title: str
    stated: str
    truth: str


@dataclass(frozen=True)
class CompactionCheck:
    """The mid-run compaction, in the shipped M-151 shape."""

    record_id: str
    title: str
    source: str
    journal_ref: str
    journal_position: int
    replaced: Tuple[str, ...]
    summary_versions: Tuple[str, ...]
    replaced_count: int
    version_count: int
    verified_stage: str

    @property
    def summary(self) -> str:
        """The current summary: the last version, derived."""
        return self.summary_versions[-1]


@dataclass(frozen=True)
class Exercise:
    """One gate exercise: its claim, its evidence, its proof."""

    id: str
    title: str
    owning_slices: Tuple[str, ...]
    status: str
    evidence_kind: str
    evidence: str
    recorded_on: str
    resumed_on: str
    situation: Situation
    statement: Tuple[StatementClaim, ...]
    compaction: CompactionCheck
    grading_task: str
    grading_total: int
    grading_at_pause: int
    grading_passed: int
    handoff_title: str
    handoff_session_ref: str
    handoff_project: str
    handoff_branch: str
    handoff_done: Tuple[str, ...]
    handoff_doing: Tuple[str, ...]
    handoff_blocked: Tuple[str, ...]
    handoff_needs_you: Tuple[str, ...]
    handoff_evidence_refs: Tuple[str, ...]
    handoff_written_by: str
    handoff_written_on: str
    handoff_source: str

    def claim_count(self) -> int:
        """How many claims the resumed statement holds."""
        return len(self.statement)

    def handoff_claim_ids(self) -> Tuple[str, ...]:
        """Every claim id the handoff carries, in section order."""
        return (self.handoff_done + self.handoff_doing
                + self.handoff_blocked + self.handoff_needs_you)


@dataclass(frozen=True)
class Gate:
    """The validated Part VII gate record."""

    gate_slice: str
    part: int
    part_title: str
    verdict: str
    gate_note: str
    baseline_resource: str
    baseline: Tuple[int, int, int, int]
    slices: Tuple[SliceRef, ...]
    layers: Tuple[LayerRef, ...]
    exercises: Tuple[Exercise, ...]

    def slice_ids(self) -> Tuple[str, ...]:
        """The gated slices, in road order (M-147..M-169)."""
        return tuple(s.slice for s in self.slices)

    def layer_slice_ids(self) -> Tuple[str, ...]:
        """The layered memory slices, in order (M-150..M-169)."""
        return tuple(row.slice for row in self.layers)

    def exercise_ids(self) -> Tuple[str, ...]:
        """The gate's exercises, in roadmap order."""
        return tuple(e.id for e in self.exercises)

    def exercise(self, exercise_id: str) -> Exercise:
        """The exercise named *exercise_id* (KeyError if absent)."""
        for exercise in self.exercises:
            if exercise.id == exercise_id:
                return exercise
        raise KeyError(f"no exercise {exercise_id!r}")

    def completed_exercises(self) -> Tuple[Exercise, ...]:
        """Every exercise whose completion the gate banks."""
        return tuple(e for e in self.exercises if e.status == "completed")

    def baseline_totals(self) -> Tuple[int, int, int, int]:
        """The M-169 baseline: collected/passed/failed/skipped."""
        return self.baseline


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _day(value: Any) -> Optional[date]:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def validate_gate(data: Any) -> List[str]:
    """Return a list of human-readable problems with gate *data*."""
    problems: List[str] = []
    if not isinstance(data, dict):
        return [f"gate root must be a mapping, got {type(data).__name__}"]
    if data.get("schema") != GATE_SCHEMA:
        problems.append(
            f"schema must be {GATE_SCHEMA!r}, got {data.get('schema')!r}")
    if data.get("gate_slice") != GATE_SLICE:
        problems.append(
            f"gate_slice must be {GATE_SLICE!r}, got {data.get('gate_slice')!r}")
    if data.get("part") != 7:
        problems.append(f"part must be 7, got {data.get('part')!r}")
    if data.get("verdict") != "PASS":
        problems.append(
            "verdict must be 'PASS' (a failed gate is a defect, not a "
            f"record), got {data.get('verdict')!r}")
    for key in ("part_title", "gate_note"):
        if not _nonempty(data.get(key)):
            problems.append(f"{key} must be a non-empty string")

    baseline = data.get("baseline")
    if not isinstance(baseline, dict):
        problems.append("baseline must be a mapping")
    else:
        if baseline.get("resource") != BASELINE_RESOURCE:
            problems.append(
                f"baseline.resource must be {BASELINE_RESOURCE!r}, got "
                f"{baseline.get('resource')!r}")
        counts = [baseline.get(k) for k in
                  ("collected", "passed", "failed", "skipped")]
        if not all(_is_int(c) and c >= 0 for c in counts):
            problems.append("baseline counts must be non-negative integers")
        elif counts[0] != counts[1] + counts[2] + counts[3]:
            problems.append(
                "baseline arithmetic does not close: collected must equal "
                f"passed + failed + skipped, got {counts}")

    slices = data.get("slices")
    if not isinstance(slices, list) or not slices:
        problems.append("slices must be a non-empty list")
        slices = []
    if len(slices) != len(SLICE_IDS):
        problems.append(
            f"slices must number exactly {len(SLICE_IDS)} "
            f"(M-147..M-169), got {len(slices)}")
    slice_titles: Dict[str, Any] = {}
    for position, ref in enumerate(slices, start=147):
        if not isinstance(ref, dict):
            problems.append(f"slice entry is not a mapping: {ref!r}")
            continue
        sid = ref.get("slice")
        expected = f"M-{position:03d}"
        if not isinstance(sid, str) or not _ID_RE.match(sid):
            problems.append(f"slice {sid!r}: slice must look like 'M-147'")
        elif sid != expected:
            problems.append(
                f"slice {sid}: slices must be sequential, expected {expected}")
        if not _nonempty(ref.get("title")):
            problems.append(f"slice {sid}: title must be non-empty")
        if isinstance(sid, str):
            slice_titles[sid] = ref.get("title")

    layers = data.get("layers")
    if not isinstance(layers, list) or not layers:
        problems.append("layers must be a non-empty list")
        layers = []
    if len(layers) != len(LAYER_SLICE_IDS):
        problems.append(
            f"layers must number exactly {len(LAYER_SLICE_IDS)} "
            f"(M-150..M-169), got {len(layers)}")
    for position, row in enumerate(layers, start=150):
        if not isinstance(row, dict):
            problems.append(f"layer entry is not a mapping: {row!r}")
            continue
        sid = row.get("slice")
        expected = f"M-{position:03d}"
        if sid != expected:
            problems.append(
                f"layer {sid!r}: layers must be sequential, "
                f"expected {expected}")
            continue
        wanted = LAYER_ROADS[expected]
        if (row.get("module"), row.get("constant")) != wanted:
            problems.append(
                f"layer {sid}: module/constant must be the shipped "
                f"road {wanted}, got ({row.get('module')!r}, "
                f"{row.get('constant')!r})")

    exercises = data.get("exercises")
    if not isinstance(exercises, list) or not exercises:
        problems.append("exercises must be a non-empty list")
        exercises = []
    ids = [e.get("id") for e in exercises if isinstance(e, dict)]
    if tuple(ids) != EXERCISE_IDS:
        problems.append(
            f"exercises must be exactly {EXERCISE_IDS} in order, got {ids}")
    for exercise in exercises:
        if not isinstance(exercise, dict):
            problems.append(f"exercise entry is not a mapping: {exercise!r}")
            continue
        eid = exercise.get("id")
        if exercise.get("status") != "completed":
            problems.append(
                f"exercise {eid}: status must be 'completed', "
                f"got {exercise.get('status')!r}")
        if exercise.get("evidence_kind") not in EVIDENCE_KINDS:
            problems.append(
                f"exercise {eid}: evidence_kind must be one of "
                f"{EVIDENCE_KINDS}, got {exercise.get('evidence_kind')!r}")
        for key in ("title", "evidence"):
            if not _nonempty(exercise.get(key)):
                problems.append(f"exercise {eid}: {key} must be non-empty")
        owning = exercise.get("owning_slices")
        if not isinstance(owning, list) or not owning or not all(
                isinstance(s, str) and _ID_RE.match(s)
                and "M-147" <= s <= "M-169" for s in owning):
            problems.append(
                f"exercise {eid}: owning_slices must name Part VII slices")
        if eid == "resumed_benchmark":
            problems.extend(
                _validate_resumed_benchmark(exercise, slice_titles))
    return problems


def _situation_pieces(situation: Dict[str, Any], eid: str,
                      slice_titles: Dict[str, Any],
                      problems: List[str]) -> List[Tuple[str, Any, Any, Any]]:
    """The recorded situation's pieces: (kind, id, title, truth)."""
    pieces: List[Tuple[str, Any, Any, Any]] = []
    memory = situation.get("memory")
    if not isinstance(memory, list) or not memory:
        problems.append(
            f"exercise {eid}: situation memory must be a non-empty list")
        memory = []
    seen_notes = set()
    for note in memory:
        if not isinstance(note, dict):
            problems.append(
                f"exercise {eid}: memory entry is not a mapping: {note!r}")
            continue
        nid = note.get("note_id")
        if not _nonempty(nid):
            problems.append(
                f"exercise {eid}: memory note must name a note_id")
        elif nid in seen_notes:
            problems.append(
                f"exercise {eid}: memory note {nid} is carried twice")
        seen_notes.add(nid)
        if note.get("section") not in MAP_SECTIONS:
            problems.append(
                f"exercise {eid}: memory note {nid}: section must be "
                f"one of {MAP_SECTIONS}, got {note.get('section')!r}")
        for key in ("title", "detail", "source", "ref"):
            if not _nonempty(note.get(key)):
                problems.append(
                    f"exercise {eid}: memory note {nid}: {key} must "
                    "be non-empty")
        pieces.append(("memory", nid, note.get("title"), note.get("detail")))
    if situation.get("total_memory") != len(memory):
        problems.append(
            f"exercise {eid}: situation total_memory must be its own "
            f"notes' count ({len(memory)}), got "
            f"{situation.get('total_memory')!r}")

    work = situation.get("open_work")
    if not isinstance(work, list) or not work:
        problems.append(
            f"exercise {eid}: situation open_work must be a non-empty list")
        work = []
    seen_work = set()
    for entry in work:
        if not isinstance(entry, dict):
            problems.append(
                f"exercise {eid}: open work entry is not a mapping: "
                f"{entry!r}")
            continue
        sid = entry.get("slice_id")
        if not isinstance(sid, str) or not _ID_RE.match(sid) \
                or not ("M-147" <= sid <= "M-169"):
            problems.append(
                f"exercise {eid}: open work slice {sid!r} must name "
                "a Part VII slice")
        if sid in seen_work:
            problems.append(
                f"exercise {eid}: open work slice {sid} stands twice")
        seen_work.add(sid)
        if entry.get("state") not in OPEN_STATES:
            problems.append(
                f"exercise {eid}: open work {sid}: state must be one "
                f"of {OPEN_STATES}, got {entry.get('state')!r}")
        if not _nonempty(entry.get("note")):
            problems.append(
                f"exercise {eid}: open work {sid}: note must be non-empty")
        if sid in slice_titles and entry.get("title") != slice_titles[sid]:
            problems.append(
                f"exercise {eid}: open work {sid}: title "
                f"{entry.get('title')!r} is not the gated slice's "
                f"title {slice_titles[sid]!r}")
        pieces.append(("slice", sid, entry.get("title"), entry.get("note")))
    if situation.get("total_slices") != len(work):
        problems.append(
            f"exercise {eid}: situation total_slices must be its own "
            f"open work's count ({len(work)}), got "
            f"{situation.get('total_slices')!r}")

    decisions = situation.get("decisions")
    if not isinstance(decisions, list) or not decisions:
        problems.append(
            f"exercise {eid}: situation decisions must be a "
            "non-empty list")
        decisions = []
    seen_decisions = set()
    for entry in decisions:
        if not isinstance(entry, dict):
            problems.append(
                f"exercise {eid}: decision entry is not a mapping: "
                f"{entry!r}")
            continue
        did = entry.get("decision_id")
        if not _nonempty(did):
            problems.append(
                f"exercise {eid}: standing decision must name a "
                "decision_id")
        elif did in seen_decisions:
            problems.append(
                f"exercise {eid}: standing decision {did} stands twice")
        seen_decisions.add(did)
        for key in ("title", "decision", "source"):
            if not _nonempty(entry.get(key)):
                problems.append(
                    f"exercise {eid}: standing decision {did}: {key} "
                    "must be non-empty")
        pieces.append(("decision", did, entry.get("title"),
                       entry.get("decision")))
    if situation.get("total_decisions") != len(decisions):
        problems.append(
            f"exercise {eid}: situation total_decisions must be "
            f"its own decisions' count ({len(decisions)}), got "
            f"{situation.get('total_decisions')!r}")
    return pieces


def _validate_resumed_benchmark(exercise: Dict[str, Any],
                                slice_titles: Dict[str, Any]) -> List[str]:
    """Every problem in the resumed_benchmark exercise's own proof."""
    problems: List[str] = []
    eid = "resumed_benchmark"

    recorded = _day(exercise.get("recorded_on"))
    resumed = _day(exercise.get("resumed_on"))
    if recorded is None:
        problems.append(
            f"exercise {eid}: recorded_on must be an ISO day, got "
            f"{exercise.get('recorded_on')!r}")
    if resumed is None:
        problems.append(
            f"exercise {eid}: resumed_on must be an ISO day, got "
            f"{exercise.get('resumed_on')!r}")
    if recorded is not None and resumed is not None \
            and (resumed - recorded).days != 7:
        problems.append(
            f"exercise {eid}: the week must be a week - resumed_on "
            f"{exercise.get('resumed_on')!r} must stand exactly "
            f"seven days after recorded_on "
            f"{exercise.get('recorded_on')!r}, got "
            f"{(resumed - recorded).days} days")

    situation = exercise.get("situation")
    if not isinstance(situation, dict):
        problems.append(f"exercise {eid}: situation must be a mapping")
        return problems
    if "transcript" in situation:
        problems.append(
            f"exercise {eid}: the transcript is counted, never "
            "carried - no transcript content stands in the record")
    for key in ("session_ref", "workspace", "title"):
        if not _nonempty(situation.get(key)):
            problems.append(
                f"exercise {eid}: situation {key} must be non-empty")
    if situation.get("status") not in SESSION_STATUSES:
        problems.append(
            f"exercise {eid}: situation status must be one of "
            f"{SESSION_STATUSES}, got {situation.get('status')!r}")
    if situation.get("saved_on") != exercise.get("recorded_on"):
        problems.append(
            f"exercise {eid}: the situation's saved day must be "
            f"the recorded day {exercise.get('recorded_on')!r}, got "
            f"{situation.get('saved_on')!r}")
    if not _is_int(situation.get("transcript_messages")) \
            or situation.get("transcript_messages", -1) < 0:
        problems.append(
            f"exercise {eid}: situation transcript_messages must "
            "be a non-negative integer - the transcript counted, "
            "never carried")
    pieces = _situation_pieces(situation, eid, slice_titles, problems)
    piece_map = {(kind, item): (title, truth)
                 for kind, item, title, truth in pieces}

    statement = exercise.get("statement")
    if not isinstance(statement, list) or not statement:
        problems.append(
            f"exercise {eid}: statement must be a non-empty list")
        statement = []
    claim_keys = set()
    for claim in statement:
        if not isinstance(claim, dict):
            problems.append(
                f"exercise {eid}: statement claim is not a mapping: "
                f"{claim!r}")
            continue
        kind, item = claim.get("kind"), claim.get("item_id")
        if kind not in CLAIM_KINDS:
            problems.append(
                f"exercise {eid}: claim kind must be one of "
                f"{CLAIM_KINDS}, got {kind!r}")
        key = (kind, item)
        if key in claim_keys:
            problems.append(
                f"exercise {eid}: claim {kind} / {item} is stated twice")
        claim_keys.add(key)
        held = piece_map.get(key)
        if held is None:
            problems.append(
                f"exercise {eid}: claim {kind} / {item} names no "
                "piece of the recorded situation")
            continue
        title, truth = held
        if claim.get("title") != title:
            problems.append(
                f"exercise {eid}: claim {kind} / {item}: title "
                f"{claim.get('title')!r} is not the piece's title "
                f"{title!r}")
        if claim.get("truth") != truth:
            problems.append(
                f"exercise {eid}: claim {kind} / {item}: truth "
                "does not match the situation piece itself - a "
                "record cannot lie in both places")
        if claim.get("stated") != claim.get("truth"):
            problems.append(
                f"exercise {eid}: claim {kind} / {item}: the "
                "statement must be correct from memory alone - "
                f"stated {claim.get('stated')!r} is not its truth")
    if claim_keys != set(piece_map):
        problems.append(
            f"exercise {eid}: the statement must hold one claim "
            f"per situation piece, got claims "
            f"{sorted(map(str, claim_keys))} for pieces "
            f"{sorted(map(str, piece_map))}")

    compaction = exercise.get("compaction")
    if not isinstance(compaction, dict):
        problems.append(f"exercise {eid}: compaction must be a mapping")
        compaction = {}
    for key in ("record_id", "title", "source", "journal_ref"):
        if not _nonempty(compaction.get(key)):
            problems.append(
                f"exercise {eid}: compaction {key} must be non-empty")
    if not _is_int(compaction.get("journal_position")) \
            or compaction.get("journal_position", -1) < 0:
        problems.append(
            f"exercise {eid}: compaction journal_position must be "
            "a non-negative integer")
    replaced = compaction.get("replaced")
    if not isinstance(replaced, list) or not replaced or not all(
            _nonempty(piece) for piece in replaced):
        problems.append(
            f"exercise {eid}: compaction replaced material must "
            "be held whole - a non-empty list of pieces")
        replaced = []
    versions = compaction.get("summary_versions")
    if not isinstance(versions, list) or len(versions) < 2 or not all(
            _nonempty(version) for version in versions):
        problems.append(
            f"exercise {eid}: compaction summary must stand as "
            "at least two versions (the compaction's own and the "
            "mid-run edit), never a silent rewrite")
        versions = []
    elif len(set(versions)) != len(versions):
        problems.append(
            f"exercise {eid}: compaction summary versions must "
            "each differ - a version that changes nothing is no "
            "version")
    if compaction.get("replaced_count") != len(replaced):
        problems.append(
            f"exercise {eid}: compaction replaced_count must be "
            f"the material's own count ({len(replaced)}), got "
            f"{compaction.get('replaced_count')!r}")
    if compaction.get("version_count") != len(versions):
        problems.append(
            f"exercise {eid}: compaction version_count must be "
            f"the versions' own count ({len(versions)}), got "
            f"{compaction.get('version_count')!r}")
    if compaction.get("verified_stage") != "mid-run":
        problems.append(
            f"exercise {eid}: compaction verification stage must "
            f"be 'mid-run', got {compaction.get('verified_stage')!r}")

    handoff = exercise.get("handoff")
    if not isinstance(handoff, dict):
        problems.append(f"exercise {eid}: handoff must be a mapping")
        handoff = {}
    for key in ("title", "project", "branch", "written_by", "source"):
        if not _nonempty(handoff.get(key)):
            problems.append(
                f"exercise {eid}: handoff {key} must be non-empty")
    if handoff.get("session_ref") != situation.get("session_ref"):
        problems.append(
            f"exercise {eid}: handoff session_ref must be the "
            f"situation's own session {situation.get('session_ref')!r}, "
            f"got {handoff.get('session_ref')!r}")
    if handoff.get("written_on") != exercise.get("recorded_on"):
        problems.append(
            f"exercise {eid}: handoff written_on must be the "
            f"recorded day {exercise.get('recorded_on')!r} - the "
            "week-old handoff the resume began from, got "
            f"{handoff.get('written_on')!r}")
    evidence_refs = [item for _k, item, _t, _w in pieces]
    if handoff.get("evidence_refs") != evidence_refs:
        problems.append(
            f"exercise {eid}: handoff evidence_refs must be the "
            f"situation's own references alone, in held order "
            f"{evidence_refs}, got {handoff.get('evidence_refs')!r}")
    claim_ids: List[Any] = []
    for section in ("done", "doing", "blocked", "needs_you"):
        named = handoff.get(section)
        if not isinstance(named, list) or not all(
                isinstance(c, str) and c for c in named):
            problems.append(
                f"exercise {eid}: handoff {section} must be a list "
                "of claim ids")
            named = []
        claim_ids.extend(named)
    if len(set(claim_ids)) != len(claim_ids):
        problems.append(
            f"exercise {eid}: a handoff names one claim in two "
            "sections")
    if not claim_ids:
        problems.append(
            f"exercise {eid}: the handoff must carry at least "
            "one claim - a handoff that states nothing hands "
            "off nothing")
    for claim_id in claim_ids:
        if claim_id not in evidence_refs:
            problems.append(
                f"exercise {eid}: handoff claim {claim_id!r} "
                "stands on no evidence the situation names")

    grading = exercise.get("grading")
    if not isinstance(grading, dict):
        problems.append(f"exercise {eid}: grading must be a mapping")
        grading = {}
    if not _nonempty(grading.get("task")):
        problems.append(f"exercise {eid}: grading task must be non-empty")
    total = grading.get("total")
    at_pause = grading.get("at_pause")
    passed = grading.get("passed")
    if not _is_int(total) or total <= 0:
        problems.append(
            f"exercise {eid}: grading total must be a positive "
            f"integer, got {total!r}")
        total = 0
    if not _is_int(at_pause) or not _is_int(passed):
        problems.append(
            f"exercise {eid}: grading at_pause and passed must "
            "be integers")
    else:
        if not 0 <= at_pause < total:
            problems.append(
                f"exercise {eid}: the task paused short of done - "
                f"grading at_pause must stand below the total "
                f"({total}) from a pause where fewer passed, got "
                f"{at_pause!r}")
        if passed != total:
            problems.append(
                f"exercise {eid}: the task must finish - grading "
                f"passed must close the line at the total "
                f"({total}), got {passed!r}")
    return problems


def _to_situation(raw: Dict[str, Any]) -> Situation:
    return Situation(
        session_ref=raw["session_ref"], workspace=raw["workspace"],
        title=raw["title"], saved_on=raw["saved_on"],
        status=raw["status"],
        transcript_messages=raw["transcript_messages"],
        memory=tuple(
            MemoryNote(note_id=n["note_id"], section=n["section"],
                       title=n["title"], detail=n["detail"],
                       source=n["source"], ref=n["ref"])
            for n in raw["memory"]),
        open_work=tuple(
            OpenWork(slice_id=w["slice_id"], title=w["title"],
                     state=w["state"], note=w["note"])
            for w in raw["open_work"]),
        decisions=tuple(
            StandingDecision(decision_id=d["decision_id"],
                             title=d["title"], decision=d["decision"],
                             source=d["source"])
            for d in raw["decisions"]),
        situation_id=raw.get("situation_id"))


def _to_gate(data: Dict[str, Any]) -> Gate:
    baseline = data["baseline"]
    exercises = []
    for raw in data["exercises"]:
        compaction = raw["compaction"]
        grading = raw["grading"]
        handoff = raw["handoff"]
        exercises.append(Exercise(
            id=raw["id"], title=raw["title"],
            owning_slices=tuple(raw["owning_slices"]),
            status=raw["status"], evidence_kind=raw["evidence_kind"],
            evidence=raw["evidence"],
            recorded_on=raw["recorded_on"], resumed_on=raw["resumed_on"],
            situation=_to_situation(raw["situation"]),
            statement=tuple(
                StatementClaim(kind=c["kind"], item_id=c["item_id"],
                               title=c["title"], stated=c["stated"],
                               truth=c["truth"])
                for c in raw["statement"]),
            compaction=CompactionCheck(
                record_id=compaction["record_id"],
                title=compaction["title"], source=compaction["source"],
                journal_ref=compaction["journal_ref"],
                journal_position=compaction["journal_position"],
                replaced=tuple(compaction["replaced"]),
                summary_versions=tuple(compaction["summary_versions"]),
                replaced_count=compaction["replaced_count"],
                version_count=compaction["version_count"],
                verified_stage=compaction["verified_stage"]),
            grading_task=grading["task"], grading_total=grading["total"],
            grading_at_pause=grading["at_pause"],
            grading_passed=grading["passed"],
            handoff_title=handoff["title"],
            handoff_session_ref=handoff["session_ref"],
            handoff_project=handoff["project"],
            handoff_branch=handoff["branch"],
            handoff_done=tuple(handoff["done"]),
            handoff_doing=tuple(handoff["doing"]),
            handoff_blocked=tuple(handoff["blocked"]),
            handoff_needs_you=tuple(handoff["needs_you"]),
            handoff_evidence_refs=tuple(handoff["evidence_refs"]),
            handoff_written_by=handoff["written_by"],
            handoff_written_on=handoff["written_on"],
            handoff_source=handoff["source"]))
    return Gate(
        gate_slice=data["gate_slice"], part=data["part"],
        part_title=data["part_title"], verdict=data["verdict"],
        gate_note=data["gate_note"],
        baseline_resource=baseline["resource"],
        baseline=(baseline["collected"], baseline["passed"],
                  baseline["failed"], baseline["skipped"]),
        slices=tuple(
            SliceRef(slice=s["slice"], title=s["title"])
            for s in data["slices"]),
        layers=tuple(
            LayerRef(slice=row["slice"], module=row["module"],
                     constant=row["constant"])
            for row in data["layers"]),
        exercises=tuple(exercises))


def load_gate(data: Optional[Dict[str, Any]] = None) -> Gate:
    """Load and validate the shipped Part VII gate (or *data*)."""
    raw = data if data is not None else load_resource(GATE_RESOURCE)
    problems = validate_gate(raw)
    if problems:
        raise ValidationError(
            "part VII gate failed validation: " + "; ".join(problems))
    return _to_gate(raw)  # type: ignore[arg-type]


def plain_words(gate: Gate) -> str:
    """The gate stated in plain words, from its own accessors."""
    collected, passed, failed, skipped = gate.baseline_totals()
    exercise = gate.exercise(EXERCISE_IDS[0])
    situation = exercise.situation
    compaction = exercise.compaction
    return (
        f"Part VII gate ({gate.gate_slice}): {gate.verdict}. "
        f"{len(gate.slice_ids())} slices gated "
        f"({gate.slice_ids()[0]}..{gate.slice_ids()[-1]}); the "
        f"benchmark session recorded on {exercise.recorded_on} "
        f"resumed on {exercise.resumed_on}, a week later, its "
        f"situation stated correctly from memory alone "
        f"({exercise.claim_count()} claims over "
        f"{len(situation.pieces())} carried pieces), its "
        f"compaction glass-box verified mid-run "
        f"({compaction.replaced_count} replaced pieces kept "
        f"whole, the summary standing as "
        f"{compaction.version_count} versions), and its task "
        f"finished ({exercise.grading_passed} of "
        f"{exercise.grading_total} grading tests passed, from "
        f"{exercise.grading_at_pause} at the pause), banked "
        f"against the M-169 confirmation suite ({collected} "
        f"collected, {passed} passed, {failed} failed, "
        f"{skipped} skipped).")


def gate_record(gate: Gate) -> Dict[str, Any]:
    """The session-news record of the gate."""
    return {
        "type": "part7_gate",
        "slice": GATE_SLICE,
        "part": gate.part,
        "verdict": gate.verdict,
        "slices": list(gate.slice_ids()),
        "layers": list(gate.layer_slice_ids()),
        "exercises": list(gate.exercise_ids()),
        "baseline": list(gate.baseline_totals()),
        "plain": plain_words(gate),
    }


def render_markdown(gate: Gate) -> str:
    """Render the gate as markdown: verdict, exercises, baseline.

    Built from :meth:`Gate.slice_ids`, :meth:`Gate.layer_slice_ids`,
    :meth:`Gate.exercise_ids`, :meth:`Gate.completed_exercises`,
    :meth:`Gate.baseline_totals`, :meth:`Gate.exercise` and
    :func:`plain_words`, so the rendered page itself is computed
    from the same accessors the tests pin.
    """
    collected, passed, failed, skipped = gate.baseline_totals()
    lines = [
        "# Part VII Gate - Memory & Context (M-170)",
        "",
        f"*Gate slice {gate.gate_slice}, part {gate.part} - "
        f"{gate.part_title}. Verdict: **{gate.verdict}**.*",
        "",
        gate.gate_note,
        "",
        f"**Slices gated:** {len(gate.slice_ids())} "
        f"({gate.slice_ids()[0]}..{gate.slice_ids()[-1]}).",
        "",
        f"**Memory layers closed:** {len(gate.layer_slice_ids())} "
        f"({gate.layer_slice_ids()[0]}..{gate.layer_slice_ids()[-1]}).",
        "",
        f"**Baseline (M-169 confirmation suite, "
        f"{gate.baseline_resource}):** "
        f"{collected} collected - {passed} passed, {failed} failed, "
        f"{skipped} skipped.",
        "",
        "## Exercises - completed",
        "",
    ]
    for exercise_id in gate.exercise_ids():
        exercise = gate.exercise(exercise_id)
        lines.append(
            f"- **{exercise.title}** ({exercise.id}; owning slices "
            f"{', '.join(exercise.owning_slices)}; evidence kind "
            f"{exercise.evidence_kind}; recorded "
            f"{exercise.recorded_on}, resumed {exercise.resumed_on}; "
            f"{exercise.claim_count()} statement claims; grading "
            f"{exercise.grading_passed} of {exercise.grading_total}): "
            f"{exercise.evidence}")
    lines += [
        "",
        f"*{len(gate.completed_exercises())} of "
        f"{len(gate.exercise_ids())} exercises completed.*",
        "",
        plain_words(gate),
        "",
    ]
    return "\n".join(lines)
