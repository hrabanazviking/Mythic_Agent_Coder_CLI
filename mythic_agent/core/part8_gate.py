"""The Part VIII gate (All-Features roadmap slice M-200).

Part VIII - The Beautiful Face - closes here. The
roadmap's gate words: *the Stranger Test - a new user,
docs only, completes a real task in the TUI inside
thirty minutes; every stumble is a fix or a doc
correction before the gate passes.*

This module is the gate's machinery:

* A validated gate record
  (``mythic_agent/data/part8_gate.yaml``) naming the
  Part VIII slices it closes over (M-171..M-199), the
  M-199 confirmation-suite baseline it is banked
  against, and the one stranger-test exercise: a new
  user, docs only, who finished a real task in the
  TUI inside the thirty minutes - the sitting held as
  the shipped M-184 onboarding walk's own five steps
  in held order (success before configuration), the
  stranger's questions each held beside the local doc
  that answered it through the shipped M-186 road,
  the one error met held whole in the shipped M-183
  shape (what happened, what it means, the most
  likely fix, its trace folded whole), every stumble
  held with the fix or doc correction it bought, and
  one layer row for every shipped face slice
  M-171..M-199 naming the core module and slice
  constant that carry it.
* The gate's tests re-prove the exercise live on
  every run through the shipped pure roads named in
  the record - M-184's ``derive_walk`` over the
  shipped onboarding book (the recorded walk is
  exactly that walk, step for step, and its success
  stands before its configuration), M-186's
  ``derive_answer`` over the shipped help book (each
  recorded question is answered by exactly the doc
  the record names, with no gaps), M-183's
  ``build_error`` / ``error_plain_words`` /
  ``error_gaps`` (the recorded error builds whole,
  its plain telling is its own fields, and it stands
  with no gaps), and every layer row's own module,
  imported and checked against its own slice
  constant - wired by the gate's tests, so this core
  module imports no service layer at all.

Honesty rules, enforced by the validator and pinned
by tests:

* Exactly one exercise: the stranger test. It is
  ``completed`` only with its evidence kind stated -
  ``pure-roads-measured``: every step rides a real
  shipped pure road at the data level, and **no step
  is faked, stubbed, or claimed beyond what the
  tests do**. No live stranger is run, no live
  session is started, no model is called and no
  token is spent by the gate itself; the campaign
  tree is never the exercise repo.
* Docs only means docs only: the sitting's guidance
  stands as ``docs only`` and no other guidance
  stands in the record.
* Thirty minutes means thirty minutes: the limit
  stands at thirty and the recorded elapsed time
  stands inside it.
* The walk must be the shipped walk: the recorded
  step ids are exactly the M-184 walk's steps, in
  held order - success before configuration is the
  shipped ordering, not a claim.
* Every question must be answered: each recorded
  question names the one local doc that answers it,
  and the gate's tests re-derive that answer live.
* The error must stand whole: happened, meaning and
  fix each in plain words, its trace held folded and
  whole, never deleted and never invented.
* Every stumble must buy its fix: each stumble is
  recorded with its resolution, and the resolution's
  kind is ``fix`` or ``doc-correction`` - a stumble
  merely noted does not pass this gate, and the
  record holds at least one of each kind.
* The layers must close: one row for every face
  slice M-171..M-199, each naming the shipped module
  and constant that carry that slice. (Part VII's
  layers began three slices in, at the memory map;
  Part VIII's face slices ship a pure road from the
  charter on, so the layers cover the whole part.)
* The baseline section must close arithmetically:
  the M-199 confirmation suite's counted totals.
* The verdict is ``PASS`` and the validator accepts
  no other verdict: a gate that has failed is a
  defect to fix, not a record.

No agent layer is owed and none is built: the part
gates ride no live Agent road of their own (the
M-094 / M-120 / M-146 / M-170 precedent) - the
exercise rides the shipped pure roads, wired by the
gate's tests, and holds no session state. No new
setting is owed: the face layers are the roads that
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
    "PART8_GATE_SLICE",
    "PLAIN_EXPLANATION",
    "SLICE_IDS",
    "Any",
    "Dict",
    "Exercise",
    "Gate",
    "LayerRef",
    "List",
    "Optional",
    "SliceRef",
    "StrangerError",
    "StrangerQuestion",
    "Stumble",
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
GATE_RESOURCE = "part8_gate.yaml"

#: The only schema this loader accepts.
GATE_SCHEMA = "mythic.part8_gate/1"

#: The slice that owns this gate.
GATE_SLICE = "M-200"

#: The shorter name other layers cite for this slice.
PART8_GATE_SLICE = GATE_SLICE

#: The Part VIII slices this gate closes over, in roadmap order.
SLICE_IDS = tuple(f"M-{n:03d}" for n in range(171, 200))

#: The shipped face slices the exercise stands over, in order.
LAYER_SLICE_IDS = tuple(f"M-{n:03d}" for n in range(171, 200))

#: The confirmation suite the gate is banked against.
BASELINE_RESOURCE = "m199_confirmation_suite"

#: The gate's exercises, in roadmap order.
EXERCISE_IDS = ("stranger_test",)

#: Evidence kinds an exercise may honestly claim.
EVIDENCE_KINDS = ("pure-roads-measured",)

#: The only guidance a stranger test may honestly claim.
GUIDANCE_WORDS = ("docs only",)

#: The roadmap's own time limit for the stranger test, in minutes.
TIME_LIMIT_MINUTES = 30

#: The shipped M-184 onboarding walk's steps, in held order.
WALK_STEP_IDS = (
    "step-detect", "step-walk", "step-success",
    "step-offer", "step-configure")

#: The ways a stumble may honestly be closed before the gate passes.
RESOLUTION_KINDS = ("fix", "doc-correction")

#: The shipped error book's kinds (M-183).
ERROR_KINDS = (
    "refused", "missing", "broken",
    "timeout", "mismatch", "denied")

#: Each face slice's shipped road: module -> slice constant.
LAYER_ROADS = {
    "M-171": ("tui_redesign_charter", "CHARTER_SLICE"),
    "M-172": ("work_view", "WORK_VIEW_SLICE"),
    "M-173": ("slice_board", "SLICE_BOARD_SLICE"),
    "M-174": ("approval_cards", "APPROVAL_CARDS_SLICE"),
    "M-175": ("fuzzy_picker", "FUZZY_PICKER_SLICE"),
    "M-176": ("command_palace", "COMMAND_PALACE_SLICE"),
    "M-177": ("prompt_craft", "PROMPT_CRAFT_SLICE"),
    "M-178": ("status_line", "STATUS_LINE_SLICE"),
    "M-179": ("themes_grown_up", "THEMES_GROWN_UP_SLICE"),
    "M-180": ("voice_in_out", "VOICE_IN_OUT_SLICE"),
    "M-181": ("notifications_manners",
              "NOTIFICATIONS_MANNERS_SLICE"),
    "M-182": ("plain_language_skin", "PLAIN_LANGUAGE_SKIN_SLICE"),
    "M-183": ("error_kindness", "ERROR_KINDNESS_SLICE"),
    "M-184": ("onboarding_five", "ONBOARDING_FIVE_SLICE"),
    "M-185": ("tutorial_grown", "TUTORIAL_GROWN_SLICE"),
    "M-186": ("help_answers", "HELP_ANSWERS_SLICE"),
    "M-187": ("keyboard_sovereignty",
              "KEYBOARD_SOVEREIGNTY_SLICE"),
    "M-188": ("mouse_manners", "MOUSE_MANNERS_SLICE"),
    "M-189": ("session_gallery", "SESSION_GALLERY_SLICE"),
    "M-190": ("costs_face", "COSTS_FACE_SLICE"),
    "M-191": ("diff_theatre_final", "DIFF_THEATRE_FINAL_SLICE"),
    "M-192": ("multi_pane", "MULTI_PANE_SLICE"),
    "M-193": ("splash_ceremony", "SPLASH_CEREMONY_SLICE"),
    "M-194": ("small_terminal_grace",
              "SMALL_TERMINAL_GRACE_SLICE"),
    "M-195": ("copy_share", "COPY_SHARE_SLICE"),
    "M-196": ("settings_room", "SETTINGS_ROOM_SLICE"),
    "M-197": ("command_palette", "COMMAND_PALETTE_SLICE"),
    "M-198": ("ui_undo", "UI_UNDO_SLICE"),
    "M-199": ("accessibility_verification",
              "ACCESSIBILITY_VERIFICATION_SLICE"),
}

PLAIN_EXPLANATION = (
    "Part VIII gate: a new user, docs only, finished "
    "a real task in the TUI inside thirty minutes - "
    "the sitting held as the shipped M-184 onboarding "
    "walk's own steps in held order, success before "
    "configuration, the stranger's questions each "
    "answered from the local docs through M-186, the "
    "one error met held whole in M-183's shape, and "
    "every stumble closed as a fix or a doc "
    "correction - re-proven live by the gate's tests "
    "through the shipped pure roads: M-184's derived "
    "walk, M-186's derived answers, M-183's built "
    "error and its plain telling, and every face "
    "slice M-171..M-199 standing in its own shipped "
    "module under its own slice constant. This layer "
    "holds the gate record as data only; the gate's "
    "tests own the live re-proof."
)

_ID_RE = re.compile(r"^M-\d{3}$")


@dataclass(frozen=True)
class SliceRef:
    """One Part VIII slice the gate closes over."""

    slice: str
    title: str


@dataclass(frozen=True)
class LayerRef:
    """One shipped face slice's road: module and constant."""

    slice: str
    module: str
    constant: str


@dataclass(frozen=True)
class StrangerQuestion:
    """One question the stranger asked, and the doc that answered it."""

    question: str
    doc_id: str


@dataclass(frozen=True)
class StrangerError:
    """The one error the stranger met, in the shipped M-183 shape."""

    error_id: str
    seq: int
    kind: str
    title: str
    happened: str
    meaning: str
    fix: str
    trace: Tuple[str, ...]
    detail: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str

    def mapping(self) -> Dict[str, Any]:
        """The error as the shipped M-183 builder takes it."""
        return {
            "error_id": self.error_id, "seq": self.seq,
            "kind": self.kind, "title": self.title,
            "happened": self.happened, "meaning": self.meaning,
            "fix": self.fix, "trace": list(self.trace),
            "detail": self.detail,
            "recorded_on": self.recorded_on, "actor": self.actor,
            "source": self.source,
            "origin_session": self.origin_session}


@dataclass(frozen=True)
class Stumble:
    """One stumble, and the fix or doc correction it bought."""

    stumble_id: str
    where: str
    what: str
    resolution_kind: str
    resolution: str


@dataclass(frozen=True)
class Exercise:
    """One gate exercise: its claim, its evidence, its proof."""

    id: str
    title: str
    owning_slices: Tuple[str, ...]
    status: str
    evidence_kind: str
    evidence: str
    walked_on: str
    stranger: str
    guidance: str
    task: str
    limit_minutes: int
    elapsed_minutes: int
    walk_step_ids: Tuple[str, ...]
    questions: Tuple[StrangerQuestion, ...]
    error: StrangerError
    stumbles: Tuple[Stumble, ...]

    def question_count(self) -> int:
        """How many questions the stranger asked the docs."""
        return len(self.questions)

    def stumble_kinds(self) -> Tuple[str, ...]:
        """The resolution kinds the stumbles closed with, in order."""
        return tuple(s.resolution_kind for s in self.stumbles)


@dataclass(frozen=True)
class Gate:
    """The validated Part VIII gate record."""

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
        """The gated slices, in road order (M-171..M-199)."""
        return tuple(s.slice for s in self.slices)

    def layer_slice_ids(self) -> Tuple[str, ...]:
        """The layered face slices, in order (M-171..M-199)."""
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
        """The M-199 baseline: collected/passed/failed/skipped."""
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
    if data.get("part") != 8:
        problems.append(f"part must be 8, got {data.get('part')!r}")
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
            f"(M-171..M-199), got {len(slices)}")
    slice_titles: Dict[str, Any] = {}
    for position, ref in enumerate(slices, start=171):
        if not isinstance(ref, dict):
            problems.append(f"slice entry is not a mapping: {ref!r}")
            continue
        sid = ref.get("slice")
        expected = f"M-{position:03d}"
        if not isinstance(sid, str) or not _ID_RE.match(sid):
            problems.append(f"slice {sid!r}: slice must look like 'M-171'")
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
            f"(M-171..M-199), got {len(layers)}")
    for position, row in enumerate(layers, start=171):
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
                and "M-171" <= s <= "M-199" for s in owning):
            problems.append(
                f"exercise {eid}: owning_slices must name Part VIII slices")
        if eid == "stranger_test":
            problems.extend(_validate_stranger_test(exercise))
    return problems


def _validate_stranger_test(exercise: Dict[str, Any]) -> List[str]:
    """Every problem in the stranger_test exercise's own proof."""
    problems: List[str] = []
    eid = "stranger_test"

    if _day(exercise.get("walked_on")) is None:
        problems.append(
            f"exercise {eid}: walked_on must be an ISO day, got "
            f"{exercise.get('walked_on')!r}")
    for key in ("stranger", "task"):
        if not _nonempty(exercise.get(key)):
            problems.append(f"exercise {eid}: {key} must be non-empty")
    if exercise.get("guidance") not in GUIDANCE_WORDS:
        problems.append(
            f"exercise {eid}: the stranger test is docs only - "
            f"guidance must be one of {GUIDANCE_WORDS}, got "
            f"{exercise.get('guidance')!r}")
    limit = exercise.get("limit_minutes")
    elapsed = exercise.get("elapsed_minutes")
    if limit != TIME_LIMIT_MINUTES:
        problems.append(
            f"exercise {eid}: the limit must stand at the roadmap's "
            f"thirty minutes ({TIME_LIMIT_MINUTES}), got {limit!r}")
    if not _is_int(elapsed) or not _is_int(limit):
        problems.append(
            f"exercise {eid}: elapsed and limit minutes must be integers")
    elif not 0 < elapsed <= limit:
        problems.append(
            f"exercise {eid}: the task must finish inside thirty "
            f"minutes - elapsed {elapsed} must stand inside the "
            f"limit {limit}")

    if exercise.get("walk_step_ids") != list(WALK_STEP_IDS):
        problems.append(
            f"exercise {eid}: the recorded walk must be the shipped "
            f"M-184 walk in held order {list(WALK_STEP_IDS)}, got "
            f"{exercise.get('walk_step_ids')!r}")

    questions = exercise.get("questions")
    if not isinstance(questions, list) or not questions:
        problems.append(
            f"exercise {eid}: questions must be a non-empty list")
        questions = []
    seen_docs = set()
    for entry in questions:
        if not isinstance(entry, dict):
            problems.append(
                f"exercise {eid}: question entry is not a mapping: "
                f"{entry!r}")
            continue
        if not _nonempty(entry.get("question")):
            problems.append(
                f"exercise {eid}: every question must be non-empty")
        doc_id = entry.get("doc_id")
        if not _nonempty(doc_id):
            problems.append(
                f"exercise {eid}: every question must name the local "
                "doc that answered it - a question the docs cannot "
                "answer is a stumble, not an answer")
        elif doc_id in seen_docs:
            problems.append(
                f"exercise {eid}: doc {doc_id} answers two questions")
        seen_docs.add(doc_id)

    error = exercise.get("error")
    if not isinstance(error, dict):
        problems.append(f"exercise {eid}: error must be a mapping")
        error = {}
    for key in ("error_id", "title", "happened", "meaning", "fix",
                "detail", "actor", "source", "origin_session"):
        if not _nonempty(error.get(key)):
            problems.append(
                f"exercise {eid}: error {key} must be non-empty")
    if error.get("kind") not in ERROR_KINDS:
        problems.append(
            f"exercise {eid}: error kind must be one of "
            f"{ERROR_KINDS}, got {error.get('kind')!r}")
    if not _is_int(error.get("seq")) or error.get("seq", 0) < 1:
        problems.append(
            f"exercise {eid}: error seq must be a positive integer")
    trace = error.get("trace")
    if not isinstance(trace, list) or not trace or not all(
            _nonempty(line) for line in trace):
        problems.append(
            f"exercise {eid}: the error's trace must be held folded "
            "and whole - a non-empty list of lines, never deleted "
            "and never invented")
    if error.get("recorded_on") != exercise.get("walked_on"):
        problems.append(
            f"exercise {eid}: the error's recorded day must be the "
            f"sitting's own day {exercise.get('walked_on')!r}, got "
            f"{error.get('recorded_on')!r}")

    stumbles = exercise.get("stumbles")
    if not isinstance(stumbles, list) or not stumbles:
        problems.append(
            f"exercise {eid}: stumbles must be a non-empty list - "
            "a stranger test that records no stumble has not been "
            "looked at honestly")
        stumbles = []
    seen_stumbles = set()
    kinds = set()
    for entry in stumbles:
        if not isinstance(entry, dict):
            problems.append(
                f"exercise {eid}: stumble entry is not a mapping: "
                f"{entry!r}")
            continue
        stumble_id = entry.get("stumble_id")
        if not _nonempty(stumble_id):
            problems.append(
                f"exercise {eid}: every stumble must name a stumble_id")
        elif stumble_id in seen_stumbles:
            problems.append(
                         f"exercise {eid}: stumble {stumble_id} stands twice")
        seen_stumbles.add(stumble_id)
        if entry.get("where") not in WALK_STEP_IDS:
            problems.append(
                f"exercise {eid}: stumble {stumble_id}: where must "
                f"name a step of the shipped walk {WALK_STEP_IDS}, "
                f"got {entry.get('where')!r}")
        if not _nonempty(entry.get("what")):
            problems.append(
                f"exercise {eid}: stumble {stumble_id}: what must "
                "be non-empty")
        kind = entry.get("resolution_kind")
        if kind not in RESOLUTION_KINDS:
            problems.append(
                f"exercise {eid}: stumble {stumble_id}: every "
                "stumble is a fix or a doc correction before the "
                "gate passes - resolution_kind must be one of "
                f"{RESOLUTION_KINDS}, got {kind!r}")
        kinds.add(kind)
        if not _nonempty(entry.get("resolution")):
            problems.append(
                f"exercise {eid}: stumble {stumble_id}: resolution "
                "must be non-empty - a stumble merely noted does "
                "not pass this gate")
    if stumbles and not set(RESOLUTION_KINDS) <= kinds:
        problems.append(
            f"exercise {eid}: the record must hold at least one "
            f"fix and at least one doc correction, got kinds "
            f"{sorted(map(str, kinds))}")
    return problems


def _to_gate(data: Dict[str, Any]) -> Gate:
    baseline = data["baseline"]
    exercises = []
    for raw in data["exercises"]:
        error = raw["error"]
        exercises.append(Exercise(
            id=raw["id"], title=raw["title"],
            owning_slices=tuple(raw["owning_slices"]),
            status=raw["status"], evidence_kind=raw["evidence_kind"],
            evidence=raw["evidence"],
            walked_on=raw["walked_on"], stranger=raw["stranger"],
            guidance=raw["guidance"], task=raw["task"],
            limit_minutes=raw["limit_minutes"],
            elapsed_minutes=raw["elapsed_minutes"],
            walk_step_ids=tuple(raw["walk_step_ids"]),
            questions=tuple(
                StrangerQuestion(question=q["question"],
                                 doc_id=q["doc_id"])
                for q in raw["questions"]),
            error=StrangerError(
                error_id=error["error_id"], seq=error["seq"],
                kind=error["kind"], title=error["title"],
                happened=error["happened"], meaning=error["meaning"],
                fix=error["fix"], trace=tuple(error["trace"]),
                detail=error["detail"],
                recorded_on=error["recorded_on"], actor=error["actor"],
                source=error["source"],
                origin_session=error["origin_session"]),
            stumbles=tuple(
                Stumble(stumble_id=s["stumble_id"], where=s["where"],
                        what=s["what"],
                        resolution_kind=s["resolution_kind"],
                        resolution=s["resolution"])
                for s in raw["stumbles"])))
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
    """Load and validate the shipped Part VIII gate (or *data*)."""
    raw = data if data is not None else load_resource(GATE_RESOURCE)
    problems = validate_gate(raw)
    if problems:
        raise ValidationError(
            "part VIII gate failed validation: " + "; ".join(problems))
    return _to_gate(raw)  # type: ignore[arg-type]


def plain_words(gate: Gate) -> str:
    """The gate stated in plain words, from its own accessors."""
    collected, passed, failed, skipped = gate.baseline_totals()
    exercise = gate.exercise(EXERCISE_IDS[0])
    return (
        f"Part VIII gate ({gate.gate_slice}): {gate.verdict}. "
        f"{len(gate.slice_ids())} slices gated "
        f"({gate.slice_ids()[0]}..{gate.slice_ids()[-1]}); a new "
        f"user, {exercise.guidance}, finished a real task in the "
        f"TUI in {exercise.elapsed_minutes} of "
        f"{exercise.limit_minutes} minutes on "
        f"{exercise.walked_on}, walking the shipped onboarding "
        f"walk's {len(exercise.walk_step_ids)} steps in held "
        f"order, its {exercise.question_count()} questions each "
        f"answered by the local docs, the one error met held "
        f"whole, and every stumble closed as a fix or a doc "
        f"correction, banked against the M-199 confirmation "
        f"suite ({collected} collected, {passed} passed, "
        f"{failed} failed, {skipped} skipped).")


def gate_record(gate: Gate) -> Dict[str, Any]:
    """The session-news record of the gate."""
    return {
        "type": "part8_gate",
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
        "# Part VIII Gate - The Beautiful Face (M-200)",
        "",
        f"*Gate slice {gate.gate_slice}, part {gate.part} - "
        f"{gate.part_title}. Verdict: **{gate.verdict}**.*",
        "",
        gate.gate_note,
        "",
        f"**Slices gated:** {len(gate.slice_ids())} "
        f"({gate.slice_ids()[0]}..{gate.slice_ids()[-1]}).",
        "",
        f"**Face layers closed:** {len(gate.layer_slice_ids())} "
        f"({gate.layer_slice_ids()[0]}..{gate.layer_slice_ids()[-1]}).",
        "",
        f"**Baseline (M-199 confirmation suite, "
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
            f"{exercise.evidence_kind}; walked on "
            f"{exercise.walked_on}; {exercise.elapsed_minutes} of "
            f"{exercise.limit_minutes} minutes; "
            f"{exercise.question_count()} questions answered; "
            f"stumbles closed as "
            f"{', '.join(exercise.stumble_kinds())}): "
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
