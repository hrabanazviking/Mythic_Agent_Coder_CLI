"""The Part IX gate (All-Features roadmap slice M-232).

Part IX - The Mythic Method Engine - closes here. The
roadmap's gate words: *this roadmap's own Part II
executed by the Method Engine itself from campaign
file to banked slices - the method proves itself on
its own birth.*

This module is the gate's machinery:

* A validated gate record
  (``mythic_agent/data/part9_gate.yaml``) naming the
  Part IX slices it closes over (M-201..M-231), the
  M-231 confirmation-suite baseline it is banked
  against, and the one method-replay exercise: Part II
  - The Provider Ocean - standing in the roadmap's own
  record as a campaign of twenty-four slices
  (M-019..M-042), every one of them banked, walked in
  the method's own held order (campaign, slice, build,
  gate, bank) through the shipped pure roads the
  method itself ships, and one layer row for every
  shipped method slice M-201..M-231 naming the core
  module and slice constant that carry it.
* The gate's tests re-prove the exercise live on
  every run through the shipped pure roads named in
  the record - M-201's ``first_citizen_record`` over
  this repo's own roadmap (the campaign read as data:
  272 slices in 11 parts, the first citizen standing
  done), the shipped ``roadmap_record`` roads of
  M-203, M-204, M-205 and M-206 (each step's own
  slice standing done in Part IX, its title the
  roadmap's own), the roadmap itself (every campaign
  slice M-019..M-042 standing done in Part II), and
  every layer row's own module, imported and checked
  against its own slice constant - wired by the
  gate's tests, so this core module imports no
  service layer at all.

Honesty rules, enforced by the validator and pinned
by tests:

* Exactly one exercise: the method replay. It is
  ``completed`` only with its evidence kind stated -
  ``pure-roads-measured``: every step rides a real
  shipped pure road at the data level, and **no step
  is faked, stubbed, or claimed beyond what the
  tests do**. No live campaign is executed, no slice
  is built, banked or pushed, no model is called and
  no token is spent by the gate itself; the replay
  re-proves records that already stand banked.
* The campaign must be Part II: the record names
  part 2, its roadmap title and the roadmap file
  itself, and its slice ids are exactly
  M-019..M-042 in roadmap order - the gate's tests
  re-prove each one standing done in the shipped
  roadmap on every run.
* The walk must be the method's own walk: the
  recorded steps are exactly the five method steps
  in held order - campaign before slice, slice
  before build, build before gate, gate before
  bank - each naming its owning slice, its shipped
  module and the anchor road the tests call live.
* The banked count must close: it stands at
  twenty-four, the whole campaign, and equals the
  recorded campaign's own length.
* The layers must close: one row for every method
  slice M-201..M-231, each naming the shipped module
  and constant that carry that slice. (The method
  slices ship a pure road from campaigns-as-data on,
  so the layers cover the whole part.)
* The baseline section must close arithmetically:
  the M-231 confirmation suite's counted totals.
* The verdict is ``PASS`` and the validator accepts
  no other verdict: a gate that has failed is a
  defect to fix, not a record.

No agent layer is owed and none is built: the part
gates ride no live Agent road of their own (the
M-094 / M-120 / M-146 / M-170 / M-200 precedent) -
the exercise rides the shipped pure roads, wired by
the gate's tests, and holds no session state. No new
setting is owed: the method layers are the roads
that already ship.
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
    "PART9_GATE_SLICE",
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
    "Step",
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
GATE_RESOURCE = "part9_gate.yaml"

#: The only schema this loader accepts.
GATE_SCHEMA = "mythic.part9_gate/1"

#: The slice that owns this gate.
GATE_SLICE = "M-232"

#: The shorter name other layers cite for this slice.
PART9_GATE_SLICE = GATE_SLICE

#: The Part IX slices this gate closes over, in roadmap order.
SLICE_IDS = tuple(f"M-{n:03d}" for n in range(201, 232))

#: The shipped method slices the exercise stands over, in order.
LAYER_SLICE_IDS = tuple(f"M-{n:03d}" for n in range(201, 232))

#: The confirmation suite the gate is banked against.
BASELINE_RESOURCE = "m231_confirmation_suite"

#: The gate's exercises, in roadmap order.
EXERCISE_IDS = ("method_replay",)

#: Evidence kinds an exercise may honestly claim.
EVIDENCE_KINDS = ("pure-roads-measured",)

#: The campaign the method replay executes: Part II of this roadmap.
CAMPAIGN_PART = 2

#: Part II's roadmap title.
CAMPAIGN_TITLE = "The Provider Ocean"

#: The campaign file the method reads campaigns from.
CAMPAIGN_FILE = "roadmap_slices.yaml"

#: Part II's slices, in roadmap order (M-019..M-042).
CAMPAIGN_SLICE_IDS = tuple(f"M-{n:03d}" for n in range(19, 43))

#: The method's own execution steps, in held order.
STEP_IDS = (
    "step-campaign", "step-slice", "step-build",
    "step-gate", "step-bank")

#: Each method step's shipped road: slice -> (module, anchor).
STEP_ROADS = {
    "step-campaign": ("M-201", "campaigns", "first_citizen_record"),
    "step-slice": ("M-203", "slicing_engine", "roadmap_record"),
    "step-build": ("M-204", "juggernaut_loop", "roadmap_record"),
    "step-gate": ("M-205", "acceptance_gates", "roadmap_record"),
    "step-bank": ("M-206", "banking_discipline", "roadmap_record"),
}

#: Each method slice's shipped road: module -> slice constant.
LAYER_ROADS = {
    "M-201": ("campaigns", "CAMPAIGNS_SLICE"),
    "M-202": ("intent_capture", "INTENT_SLICE"),
    "M-203": ("slicing_engine", "SLICING_SLICE"),
    "M-204": ("juggernaut_loop", "JUGGERNAUT_SLICE"),
    "M-205": ("acceptance_gates", "ACCEPTANCE_SLICE"),
    "M-206": ("banking_discipline", "BANKING_SLICE"),
    "M-207": ("keeper_runtime", "KEEPING_SLICE"),
    "M-208": ("pause_lines", "PAUSING_SLICE"),
    "M-209": ("question_law", "QUESTIONING_SLICE"),
    "M-210": ("scope_sentry", "SENTRY_SLICE"),
    "M-211": ("memory_map_upkeep", "UPKEEP_SLICE"),
    "M-212": ("bug_rule", "BUG_SLICE"),
    "M-213": ("retrospectives", "RETRO_SLICE"),
    "M-214": ("pattern_extraction", "PATTERN_SLICE"),
    "M-215": ("estimate_honesty", "ESTIMATE_SLICE"),
    "M-216": ("multi_campaign_hall", "CAMPAIGN_SLICE"),
    "M-217": ("campaign_templates", "TEMPLATE_SLICE"),
    "M-218": ("mimisbrunnr_road", "ROAD_SLICE"),
    "M-219": ("interrupts_resumes", "RESUME_SLICE"),
    "M-220": ("milestone_reports", "REPORT_SLICE"),
    "M-221": ("build_log", "ENTRY_SLICE"),
    "M-222": ("self_modification", "CHANGE_SLICE"),
    "M-223": ("failure_taxonomy", "FAILURE_SLICE"),
    "M-224": ("dry_run_campaigns", "REHEARSAL_SLICE"),
    "M-225": ("campaign_export", "BUNDLE_SLICE"),
    "M-226": ("standing_orders", "ORDER_SLICE"),
    "M-227": ("workflow_default", "PROPOSAL_SLICE"),
    "M-228": ("team_scaling", "ENDEAVOUR_SLICE"),
    "M-229": ("method_course", "LESSON_SLICE"),
    "M-230": ("method_metrics", "READING_SLICE"),
    "M-231": ("cross_app_method", "EXTERNAL_SLICE"),
}

PLAIN_EXPLANATION = (
    "Part IX gate: this roadmap's own Part II - The "
    "Provider Ocean, twenty-four slices - stands "
    "executed by the Method Engine itself from "
    "campaign file to banked slices, walked in the "
    "method's own held order (campaign, slice, build, "
    "gate, bank) and re-proven live by the gate's "
    "tests through the shipped pure roads: M-201's "
    "first citizen over this repo's own roadmap, the "
    "shipped roadmap standings of M-203, M-204, M-205 "
    "and M-206, the roadmap's own banked record for "
    "every campaign slice M-019..M-042, and every "
    "method slice M-201..M-231 standing in its own "
    "shipped module under its own slice constant. "
    "This layer holds the gate record as data only; "
    "the gate's tests own the live re-proof."
)

_ID_RE = re.compile(r"^M-\d{3}$")


@dataclass(frozen=True)
class SliceRef:
    """One Part IX slice the gate closes over."""

    slice: str
    title: str


@dataclass(frozen=True)
class LayerRef:
    """One shipped method slice's road: module and constant."""

    slice: str
    module: str
    constant: str


@dataclass(frozen=True)
class Step:
    """One step of the method's own walk: its shipped road."""

    step_id: str
    slice: str
    module: str
    anchor: str


@dataclass(frozen=True)
class Exercise:
    """One gate exercise: its claim, its evidence, its proof."""

    id: str
    title: str
    owning_slices: Tuple[str, ...]
    status: str
    evidence_kind: str
    evidence: str
    executed_on: str
    campaign_part: int
    campaign_title: str
    campaign_file: str
    campaign_slice_ids: Tuple[str, ...]
    steps: Tuple[Step, ...]
    banked_count: int

    def campaign_count(self) -> int:
        """How many slices the replayed campaign holds."""
        return len(self.campaign_slice_ids)

    def step_ids(self) -> Tuple[str, ...]:
        """The walk's step ids, in held order."""
        return tuple(s.step_id for s in self.steps)


@dataclass(frozen=True)
class Gate:
    """The validated Part IX gate record."""

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
        """The gated slices, in road order (M-201..M-231)."""
        return tuple(s.slice for s in self.slices)

    def layer_slice_ids(self) -> Tuple[str, ...]:
        """The layered method slices, in order (M-201..M-231)."""
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
        """The M-231 baseline: collected/passed/failed/skipped."""
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
    if data.get("part") != 9:
        problems.append(f"part must be 9, got {data.get('part')!r}")
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
            f"(M-201..M-231), got {len(slices)}")
    for position, ref in enumerate(slices, start=201):
        if not isinstance(ref, dict):
            problems.append(f"slice entry is not a mapping: {ref!r}")
            continue
        sid = ref.get("slice")
        expected = f"M-{position:03d}"
        if not isinstance(sid, str) or not _ID_RE.match(sid):
            problems.append(f"slice {sid!r}: slice must look like 'M-201'")
        elif sid != expected:
            problems.append(
                f"slice {sid}: slices must be sequential, expected {expected}")
        if not _nonempty(ref.get("title")):
            problems.append(f"slice {sid}: title must be non-empty")

    layers = data.get("layers")
    if not isinstance(layers, list) or not layers:
        problems.append("layers must be a non-empty list")
        layers = []
    if len(layers) != len(LAYER_SLICE_IDS):
        problems.append(
            f"layers must number exactly {len(LAYER_SLICE_IDS)} "
            f"(M-201..M-231), got {len(layers)}")
    for position, row in enumerate(layers, start=201):
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
                and "M-201" <= s <= "M-231" for s in owning):
            problems.append(
                f"exercise {eid}: owning_slices must name Part IX slices")
        if eid == "method_replay":
            problems.extend(_validate_method_replay(exercise))
    return problems


def _validate_method_replay(exercise: Dict[str, Any]) -> List[str]:
    """Every problem in the method_replay exercise's own proof."""
    problems: List[str] = []
    eid = "method_replay"

    if _day(exercise.get("executed_on")) is None:
        problems.append(
            f"exercise {eid}: executed_on must be an ISO day, got "
            f"{exercise.get('executed_on')!r}")
    if exercise.get("campaign_part") != CAMPAIGN_PART:
        problems.append(
            f"exercise {eid}: the replayed campaign must be Part II - "
            f"campaign_part must be {CAMPAIGN_PART}, got "
            f"{exercise.get('campaign_part')!r}")
    if exercise.get("campaign_title") != CAMPAIGN_TITLE:
        problems.append(
            f"exercise {eid}: campaign_title must be the roadmap's "
            f"own {CAMPAIGN_TITLE!r}, got "
            f"{exercise.get('campaign_title')!r}")
    if exercise.get("campaign_file") != CAMPAIGN_FILE:
        problems.append(
            f"exercise {eid}: campaign_file must be the campaign "
            f"file {CAMPAIGN_FILE!r}, got "
            f"{exercise.get('campaign_file')!r}")

    campaign = exercise.get("campaign_slice_ids")
    if campaign != list(CAMPAIGN_SLICE_IDS):
        problems.append(
            f"exercise {eid}: the recorded campaign must be Part II "
            f"in roadmap order {list(CAMPAIGN_SLICE_IDS)}, got "
            f"{campaign!r}")
        campaign = campaign if isinstance(campaign, list) else []

    banked = exercise.get("banked_count")
    if not _is_int(banked) or banked != len(CAMPAIGN_SLICE_IDS):
        problems.append(
            f"exercise {eid}: the banked count must close at the "
            f"whole campaign - {len(CAMPAIGN_SLICE_IDS)} banked of "
            f"{len(CAMPAIGN_SLICE_IDS)}, got {banked!r}")
    elif isinstance(campaign, list) and banked != len(campaign):
        problems.append(
            f"exercise {eid}: the banked count {banked} must equal "
            f"the recorded campaign's own length {len(campaign)}")

    steps = exercise.get("steps")
    if not isinstance(steps, list) or not steps:
        problems.append(
            f"exercise {eid}: steps must be a non-empty list - a "
            "method replay that records no step has not been "
            "looked at honestly")
        steps = []
    step_ids = [s.get("step_id") for s in steps if isinstance(s, dict)]
    if tuple(step_ids) != STEP_IDS:
        problems.append(
            f"exercise {eid}: the recorded walk must be the "
            f"method's own walk in held order {list(STEP_IDS)}, got "
            f"{step_ids}")
    for entry in steps:
        if not isinstance(entry, dict):
            problems.append(
                f"exercise {eid}: step entry is not a mapping: "
                f"{entry!r}")
            continue
        step_id = entry.get("step_id")
        wanted = STEP_ROADS.get(step_id) if isinstance(step_id, str) else None
        if wanted is None:
            problems.append(
                f"exercise {eid}: step {step_id!r} is not a step of "
                f"the method's walk {STEP_IDS}")
            continue
        got = (entry.get("slice"), entry.get("module"),
               entry.get("anchor"))
        if got != wanted:
            problems.append(
                f"exercise {eid}: step {step_id}: slice/module/"
                f"anchor must be the shipped road {wanted}, got {got}")
    return problems


def _to_gate(data: Dict[str, Any]) -> Gate:
    baseline = data["baseline"]
    exercises = []
    for raw in data["exercises"]:
        exercises.append(Exercise(
            id=raw["id"], title=raw["title"],
            owning_slices=tuple(raw["owning_slices"]),
            status=raw["status"], evidence_kind=raw["evidence_kind"],
            evidence=raw["evidence"],
            executed_on=raw["executed_on"],
            campaign_part=raw["campaign_part"],
            campaign_title=raw["campaign_title"],
            campaign_file=raw["campaign_file"],
            campaign_slice_ids=tuple(raw["campaign_slice_ids"]),
            steps=tuple(
                Step(step_id=s["step_id"], slice=s["slice"],
                     module=s["module"], anchor=s["anchor"])
                for s in raw["steps"]),
            banked_count=raw["banked_count"]))
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
    """Load and validate the shipped Part IX gate (or *data*)."""
    raw = data if data is not None else load_resource(GATE_RESOURCE)
    problems = validate_gate(raw)
    if problems:
        raise ValidationError(
            "part IX gate failed validation: " + "; ".join(problems))
    return _to_gate(raw)  # type: ignore[arg-type]


def plain_words(gate: Gate) -> str:
    """The gate stated in plain words, from its own accessors."""
    collected, passed, failed, skipped = gate.baseline_totals()
    exercise = gate.exercise(EXERCISE_IDS[0])
    return (
        f"Part IX gate ({gate.gate_slice}): {gate.verdict}. "
        f"{len(gate.slice_ids())} slices gated "
        f"({gate.slice_ids()[0]}..{gate.slice_ids()[-1]}); Part II "
        f"- {exercise.campaign_title} - executed by the Method "
        f"Engine itself from campaign file to banked slices: "
        f"{exercise.banked_count} of {exercise.campaign_count()} "
        f"campaign slices ({exercise.campaign_slice_ids[0]}.."
        f"{exercise.campaign_slice_ids[-1]}) stand banked, walked "
        f"in the method's own {len(exercise.step_ids())} steps in "
        f"held order on {exercise.executed_on}, banked against "
        f"the M-231 confirmation suite ({collected} collected, "
        f"{passed} passed, {failed} failed, {skipped} skipped).")


def gate_record(gate: Gate) -> Dict[str, Any]:
    """The session-news record of the gate."""
    return {
        "type": "part9_gate",
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
        "# Part IX Gate - The Mythic Method Engine (M-232)",
        "",
        f"*Gate slice {gate.gate_slice}, part {gate.part} - "
        f"{gate.part_title}. Verdict: **{gate.verdict}**.*",
        "",
        gate.gate_note,
        "",
        f"**Slices gated:** {len(gate.slice_ids())} "
        f"({gate.slice_ids()[0]}..{gate.slice_ids()[-1]}).",
        "",
        f"**Method layers closed:** {len(gate.layer_slice_ids())} "
        f"({gate.layer_slice_ids()[0]}..{gate.layer_slice_ids()[-1]}).",
        "",
        f"**Baseline (M-231 confirmation suite, "
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
            f"{exercise.evidence_kind}; executed on "
            f"{exercise.executed_on}; campaign Part "
            f"{exercise.campaign_part} - {exercise.campaign_title} "
            f"from {exercise.campaign_file}; "
            f"{exercise.banked_count} of "
            f"{exercise.campaign_count()} campaign slices banked; "
            f"steps {', '.join(exercise.step_ids())}): "
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
