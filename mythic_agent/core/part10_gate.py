"""The Part X gate (All-Features roadmap slice M-254).

Part X - Bridges - closes here. The roadmap's gate
words: *one campaign slice executed across bridges -
issue from a host, build locally, PR raised, stand-up
posted to Samtal - with credentials never leaving
Kista.*

This module is the gate's machinery:

* A validated gate record
  (``mythic_agent/data/part10_gate.yaml``) naming the
  Part X slices it closes over (M-233..M-253), the
  M-253 confirmation-suite baseline it is banked
  against, and the one bridge-campaign exercise: a
  single campaign slice walked across the bridges in
  held order - issue from a host, build locally, PR
  raised, stand-up posted to Samtal - through the
  shipped pure roads the bridges themselves ship, and
  one layer row for every shipped bridge slice
  M-233..M-253 naming the core module and slice
  constant that carry it.
* The gate's tests re-prove the exercise live on
  every run through the shipped pure roads named in
  the record - the shipped ``roadmap_record`` roads
  of M-242, M-233, M-244 and M-243 (each step's own
  slice standing done in Part X, its title the
  roadmap's own), the roadmap itself (every gated
  slice M-233..M-253 standing done in Part X), and
  every layer row's own module, imported and checked
  against its own slice constant - wired by the
  gate's tests, so this core module imports no
  service layer at all.

Honesty rules, enforced by the validator and pinned
by tests:

* Exactly one exercise: the bridge campaign. It is
  ``completed`` only with its evidence kind stated -
  ``pure-roads-measured``: every stage rides a real
  shipped pure road at the data level, and **no stage
  is faked, stubbed, or claimed beyond what the
  tests do**. No host API is called, no issue is
  fetched, no PR is raised, no stand-up is posted and
  no credential is read out of Kista by the gate
  itself; the exercise re-proves records that
  already stand banked.
* Credentials never leave Kista: the exercise pins
  the invariant as data - the credential rule
  ``credentials-never-leave-kista`` and the Kista
  refs the stages rest on (``kista:github``,
  ``kista:samtal``) - and the PR stage rides the
  shipped M-244 Kista road, the slice whose whole
  charge is that keys are named by ref and never
  carried across a bridge in the clear.
* The walk must be the bridge walk: the recorded
  steps are exactly the four stages in held order -
  issue before build, build before PR, PR before
  stand-up - each naming its owning slice, its
  shipped module and the anchor road the tests call
  live.
* The layers must close: one row for every bridge
  slice M-233..M-253, each naming the shipped module
  and constant that carry that slice.
* The baseline section must close arithmetically:
  the M-253 confirmation suite's counted totals.
* The verdict is ``PASS`` and the validator accepts
  no other verdict: a gate that has failed is a
  defect to fix, not a record.

No agent layer is owed and none is built: the part
gates ride no live Agent road of their own (the
M-094 / M-120 / M-146 / M-170 / M-200 precedent) -
the exercise rides the shipped pure roads, wired by
the gate's tests, and holds no session state. No new
setting is owed: the bridge layers are the roads
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
    "PART10_GATE_SLICE",
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
GATE_RESOURCE = "part10_gate.yaml"

#: The only schema this loader accepts.
GATE_SCHEMA = "mythic.part10_gate/1"

#: The slice that owns this gate.
GATE_SLICE = "M-254"

#: The shorter name other layers cite for this slice.
PART10_GATE_SLICE = GATE_SLICE

#: The Part X slices this gate closes over, in roadmap order.
SLICE_IDS = tuple(f"M-{n:03d}" for n in range(233, 254))

#: The shipped bridge slices the exercise stands over, in order.
LAYER_SLICE_IDS = tuple(f"M-{n:03d}" for n in range(233, 254))

#: The confirmation suite the gate is banked against.
BASELINE_RESOURCE = "m253_confirmation_suite"

#: The gate's exercises, in roadmap order.
EXERCISE_IDS = ("bridge_campaign",)

#: Evidence kinds an exercise may honestly claim.
EVIDENCE_KINDS = ("pure-roads-measured",)

#: The host the campaign slice's issue arrives from.
HOST_SLICE = "M-246"

#: The host's name, as the bridges name it.
HOST_NAME = "github"

#: The credential invariant the whole walk stands under.
CREDENTIAL_RULE = "credentials-never-leave-kista"

#: The Kista refs the stages rest on, in walk order.
KISTA_REFS = ("kista:github", "kista:samtal")

#: The bridge walk's stages, in held order.
STEP_IDS = (
    "step-issue", "step-build", "step-pr",
    "step-standup")

#: Each stage's shipped road: slice -> (module, anchor).
STEP_ROADS = {
    "step-issue": ("M-242", "samverk_bridge", "roadmap_record"),
    "step-build": ("M-233", "mcp_client", "roadmap_record"),
    "step-pr": ("M-244", "kista_keykeeper", "roadmap_record"),
    "step-standup": ("M-243", "samtal_bridge", "roadmap_record"),
}

#: Each bridge slice's shipped road: module -> slice constant.
LAYER_ROADS = {
    "M-233": ("mcp_client", "CONNECTION_SLICE"),
    "M-234": ("mcp_server_v2", "EXPOSURE_SLICE"),
    "M-235": ("mcp_registry", "LISTING_SLICE"),
    "M-236": ("skills_standard", "PACK_SLICE"),
    "M-237": ("custom_commands", "TEMPLATE_SLICE"),
    "M-238": ("plugin_bundles", "BUNDLE_SLICE"),
    "M-239": ("vscode_companions", "COMPANION_SLICE"),
    "M-240": ("ide_companions", "ENDPOINT_SLICE"),
    "M-241": ("rival_importers", "IMPORTER_SLICE"),
    "M-242": ("samverk_bridge", "EXCHANGE_SLICE"),
    "M-243": ("samtal_bridge", "DISPATCH_SLICE"),
    "M-244": ("kista_keykeeper", "RESOLUTION_SLICE"),
    "M-245": ("aesir_deepening", "AESIR_SLICE"),
    "M-246": ("git_host_parity", "GIT_HOST_SLICE"),
    "M-247": ("ci_bridges", "CI_BRIDGE_SLICE"),
    "M-248": ("issue_trackers", "ISSUE_TRACKER_SLICE"),
    "M-249": ("wyrd_seam", "WYRD_SEAM_SLICE"),
    "M-250": ("webhook_doors", "WEBHOOK_DOORS_SLICE"),
    "M-251": ("export_everything", "EXPORT_EVERYTHING_SLICE"),
    "M-252": ("docs_mcp_pattern", "DOCS_MCP_PATTERN_SLICE"),
    "M-253": ("bridge_permissions", "BRIDGE_PERMISSIONS_SLICE"),
}

PLAIN_EXPLANATION = (
    "Part X gate: one campaign slice stands executed "
    "across bridges - issue from a host, build "
    "locally, PR raised, stand-up posted to Samtal - "
    "walked in the bridge walk's held order (issue, "
    "build, PR, stand-up) with credentials never "
    "leaving Kista, and re-proven live by the gate's "
    "tests through the shipped pure roads: the "
    "shipped roadmap standings of M-242, M-233, M-244 "
    "and M-243, the roadmap's own banked record for "
    "every gated slice M-233..M-253, and every bridge "
    "slice M-233..M-253 standing in its own shipped "
    "module under its own slice constant. This layer "
    "holds the gate record as data only; the gate's "
    "tests own the live re-proof."
)

_ID_RE = re.compile(r"^M-\d{3}$")


@dataclass(frozen=True)
class SliceRef:
    """One Part X slice the gate closes over."""

    slice: str
    title: str


@dataclass(frozen=True)
class LayerRef:
    """One shipped bridge slice's road: module and constant."""

    slice: str
    module: str
    constant: str


@dataclass(frozen=True)
class Step:
    """One stage of the bridge walk: its shipped road."""

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
    host_slice: str
    host_name: str
    credential_rule: str
    kista_refs: Tuple[str, ...]
    steps: Tuple[Step, ...]

    def step_ids(self) -> Tuple[str, ...]:
        """The walk's step ids, in held order."""
        return tuple(s.step_id for s in self.steps)

    def stage_count(self) -> int:
        """How many stages the bridge walk holds."""
        return len(self.steps)


@dataclass(frozen=True)
class Gate:
    """The validated Part X gate record."""

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
        """The gated slices, in road order (M-233..M-253)."""
        return tuple(s.slice for s in self.slices)

    def layer_slice_ids(self) -> Tuple[str, ...]:
        """The layered bridge slices, in order (M-233..M-253)."""
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
        """The M-253 baseline: collected/passed/failed/skipped."""
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
    if data.get("part") != 10:
        problems.append(f"part must be 10, got {data.get('part')!r}")
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
            f"(M-233..M-253), got {len(slices)}")
    for position, ref in enumerate(slices, start=233):
        if not isinstance(ref, dict):
            problems.append(f"slice entry is not a mapping: {ref!r}")
            continue
        sid = ref.get("slice")
        expected = f"M-{position:03d}"
        if not isinstance(sid, str) or not _ID_RE.match(sid):
            problems.append(f"slice {sid!r}: slice must look like 'M-233'")
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
            f"(M-233..M-253), got {len(layers)}")
    for position, row in enumerate(layers, start=233):
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
                and "M-233" <= s <= "M-253" for s in owning):
            problems.append(
                f"exercise {eid}: owning_slices must name Part X slices")
        if eid == "bridge_campaign":
            problems.extend(_validate_bridge_campaign(exercise))
    return problems


def _validate_bridge_campaign(exercise: Dict[str, Any]) -> List[str]:
    """Every problem in the bridge_campaign exercise's own proof."""
    problems: List[str] = []
    eid = "bridge_campaign"

    if _day(exercise.get("executed_on")) is None:
        problems.append(
            f"exercise {eid}: executed_on must be an ISO day, got "
            f"{exercise.get('executed_on')!r}")
    if exercise.get("host_slice") != HOST_SLICE:
        problems.append(
            f"exercise {eid}: the issue must arrive from a host - "
            f"host_slice must be {HOST_SLICE} (the git-host parity "
            f"slice), got {exercise.get('host_slice')!r}")
    if exercise.get("host_name") != HOST_NAME:
        problems.append(
            f"exercise {eid}: host_name must be the host the bridges "
            f"name {HOST_NAME!r}, got {exercise.get('host_name')!r}")
    if exercise.get("credential_rule") != CREDENTIAL_RULE:
        problems.append(
            f"exercise {eid}: credentials never leave Kista - "
            f"credential_rule must be {CREDENTIAL_RULE!r}, got "
            f"{exercise.get('credential_rule')!r}")
    if exercise.get("kista_refs") != list(KISTA_REFS):
        problems.append(
            f"exercise {eid}: the stages must rest on the Kista refs "
            f"{list(KISTA_REFS)}, got {exercise.get('kista_refs')!r}")

    steps = exercise.get("steps")
    if not isinstance(steps, list) or not steps:
        problems.append(
            f"exercise {eid}: steps must be a non-empty list - a "
            "bridge campaign that records no stage has not been "
            "looked at honestly")
        steps = []
    step_ids = [s.get("step_id") for s in steps if isinstance(s, dict)]
    if tuple(step_ids) != STEP_IDS:
        problems.append(
            f"exercise {eid}: the recorded walk must be the "
            f"bridge walk in held order {list(STEP_IDS)}, got "
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
                f"exercise {eid}: step {step_id!r} is not a stage of "
                f"the bridge walk {STEP_IDS}")
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
            host_slice=raw["host_slice"],
            host_name=raw["host_name"],
            credential_rule=raw["credential_rule"],
            kista_refs=tuple(raw["kista_refs"]),
            steps=tuple(
                Step(step_id=s["step_id"], slice=s["slice"],
                     module=s["module"], anchor=s["anchor"])
                for s in raw["steps"])))
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
    """Load and validate the shipped Part X gate (or *data*)."""
    raw = data if data is not None else load_resource(GATE_RESOURCE)
    problems = validate_gate(raw)
    if problems:
        raise ValidationError(
            "part X gate failed validation: " + "; ".join(problems))
    return _to_gate(raw)  # type: ignore[arg-type]


def plain_words(gate: Gate) -> str:
    """The gate stated in plain words, from its own accessors."""
    collected, passed, failed, skipped = gate.baseline_totals()
    exercise = gate.exercise(EXERCISE_IDS[0])
    return (
        f"Part X gate ({gate.gate_slice}): {gate.verdict}. "
        f"{len(gate.slice_ids())} slices gated "
        f"({gate.slice_ids()[0]}..{gate.slice_ids()[-1]}); one "
        f"campaign slice executed across bridges: issue from "
        f"{exercise.host_name} (host slice {exercise.host_slice}), "
        f"build locally, PR raised, stand-up posted to Samtal - "
        f"{exercise.stage_count()} stages "
        f"({', '.join(exercise.step_ids())}) in held order on "
        f"{exercise.executed_on}, credentials never leaving Kista "
        f"(refs {', '.join(exercise.kista_refs)}), banked against "
        f"the M-253 confirmation suite ({collected} collected, "
        f"{passed} passed, {failed} failed, {skipped} skipped).")


def gate_record(gate: Gate) -> Dict[str, Any]:
    """The session-news record of the gate."""
    return {
        "type": "part10_gate",
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
        "# Part X Gate - Bridges (M-254)",
        "",
        f"*Gate slice {gate.gate_slice}, part {gate.part} - "
        f"{gate.part_title}. Verdict: **{gate.verdict}**.*",
        "",
        gate.gate_note,
        "",
        f"**Slices gated:** {len(gate.slice_ids())} "
        f"({gate.slice_ids()[0]}..{gate.slice_ids()[-1]}).",
        "",
        f"**Bridge layers closed:** {len(gate.layer_slice_ids())} "
        f"({gate.layer_slice_ids()[0]}..{gate.layer_slice_ids()[-1]}).",
        "",
        f"**Baseline (M-253 confirmation suite, "
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
            f"{exercise.executed_on}; issue from {exercise.host_name} "
            f"(host slice {exercise.host_slice}); credential rule "
            f"{exercise.credential_rule}; Kista refs "
            f"{', '.join(exercise.kista_refs)}; "
            f"{exercise.stage_count()} stages: "
            f"{', '.join(exercise.step_ids())}): "
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
