"""The Part VI gate (All-Features roadmap slice M-146).

Part VI — The Crew — closes here. The roadmap's gate
words: *a six-slice feature built by a three-member crew
in parallel worktrees — merged clean, Auditor-approved,
cost ledger complete.*

This module is the gate's machinery:

* A validated gate record
  (``mythic_agent/data/part6_gate.yaml``) naming the
  Part VI slices it closes over (M-121..M-145), the
  M-145 confirmation-suite baseline it is banked
  against, and the one crew-build exercise: a six-slice
  feature (M-124, M-125, M-126, M-128, M-133, M-140)
  dealt by the shipped M-125 dealer to three members of
  the shipped M-121 casting, each building in its own
  worktree on its own branch under the shipped M-124
  discipline, every merge recorded under the shipped
  M-128 discipline, the Auditor's checks (M-130) carried
  per feature slice, and the Scribe's cost ledger
  (M-140) holding one priced run record per dealt pair.
* The gate's tests re-prove the exercise live on every
  run through the shipped pure roads named in the
  record — M-121's ``load_casting``, M-125's
  ``deal_tasks``, M-124's ``WorktreePlan`` /
  ``merge_plan_for``, M-128's ``MergeDiscipline``
  judge, M-130's ``AuditorLedger`` report and M-140's
  ``derive_ledger`` over the shared rate table
  (``core/costs`` pricing, the same table the cost
  court prices by) — wired by the gate's tests, so
  this core module imports no service layer beyond
  the shared pricing road its validator prices by.

Honesty rules, enforced by the validator and pinned
by tests:

* Exactly one exercise: the crew build. It is
  ``completed`` only with its evidence kind stated —
  ``pure-roads-measured``: every step rides a real
  shipped pure road at the data level, and **no step
  is faked, stubbed, or claimed beyond what the tests
  do**. No live crew is spawned, no git command is
  run, no model is called and no token is spent by
  the gate itself; the exercise's token counts are
  the record's own, priced by the shared rate table
  exactly as the shipped cost court prices any run
  record. The campaign tree is never the exercise
  repo.
* The dealing must close: the dealt pairs are
  exactly the feature slices, each dealt to the
  member holding the office the slice's work fits.
* The worktrees must close: the waves assign each
  dealt pair exactly once, each member on its own
  conventional branch (``crew/<member>/<slice>``) at
  its own conventional path (``worktrees/<member>``),
  and the coordinator holds no worktree.
* The merges must be clean: every dealt pair merged
  with a passed test gate and a green outcome, and
  ``merge_verdicts`` is 0 — the shipped M-128 judge
  derives no verdict and every line completes, proven
  live by the tests.
* The audit must approve: one case per feature
  slice, each carrying the two required checks
  (``suite-green``, ``banking-order-kept``), every
  result passed, and ``audit_verdicts`` is 0 — the
  shipped M-130 report is clean and every gate state
  passed, proven live by the tests.
* The cost ledger must close exactly: one priced
  run record per dealt pair, the call / input /
  output totals the entries' own sums, and
  ``cost_total_usd`` the shared rate table's own
  pricing of those entries.
* The baseline section must close arithmetically:
  the M-145 confirmation suite's counted totals
  (7247 collected, 7244 passed, 2 failed — the two
  long-classified environment cases — 1 skipped).
* The verdict is ``PASS`` and the validator accepts
  no other verdict: a gate that has failed is a
  defect to fix, not a record.

No agent layer is owed and none is built: the part
gates ride no live Agent road of their own (the
M-094 / M-120 precedent) — the exercise rides the
shipped pure roads, wired by the gate's tests, and
holds no session state. No new setting is owed: the
casting, dealing, worktrees, merge discipline,
auditor and cost court are the roads that already
ship.
"""

from __future__ import annotations

__all__ = [
    "BASELINE_RESOURCE",
    "EVIDENCE_KINDS",
    "EXERCISE_IDS",
    "GATE_RESOURCE",
    "GATE_SCHEMA",
    "GATE_SLICE",
    "PART6_GATE_SLICE",
    "PLAIN_EXPLANATION",
    "SLICE_IDS",
    "Any",
    "AuditCase",
    "AuditCheck",
    "AuditResult",
    "CostEntry",
    "DealtPair",
    "Dict",
    "Exercise",
    "FeatureSlice",
    "Gate",
    "List",
    "MergeRecord",
    "Optional",
    "SliceRef",
    "Tuple",
    "WorktreeAssignment",
    "WorktreeWave",
    "gate_record",
    "load_gate",
    "plain_words",
    "render_markdown",
    "validate_gate",
]

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .costs import price as _shared_price
from .validation import ValidationError

#: Resource name of the gate data file inside ``mythic_agent/data``.
GATE_RESOURCE = "part6_gate.yaml"

#: The only schema this loader accepts.
GATE_SCHEMA = "mythic.part6_gate/1"

#: The slice that owns this gate.
GATE_SLICE = "M-146"

#: The shorter name other layers cite for this slice.
PART6_GATE_SLICE = GATE_SLICE

#: The Part VI slices this gate closes over, in roadmap order.
SLICE_IDS = tuple(f"M-{n:03d}" for n in range(121, 146))

#: The confirmation suite the gate is banked against.
BASELINE_RESOURCE = "m145_confirmation_suite"

#: The gate's exercises, in roadmap order.
EXERCISE_IDS = ("crew_build",)

#: Evidence kinds an exercise may honestly claim.
EVIDENCE_KINDS = ("pure-roads-measured",)

#: The Auditor's required checks, carried per feature slice.
REQUIRED_CHECKS = ("suite-green", "banking-order-kept")

PLAIN_EXPLANATION = (
    "Part VI gate: a six-slice feature built by a "
    "three-member crew in parallel worktrees, "
    "re-proven live by the gate's tests through the "
    "shipped pure roads — the M-125 dealer dealing "
    "every feature slice to the office-fitted member "
    "of the M-121 casting, each member building in "
    "its own worktree on its own branch under M-124 "
    "with the coordinator holding no worktree and "
    "merging every step, every merge clean under the "
    "M-128 judge with zero verdicts, the M-130 "
    "Auditor approving every feature slice with both "
    "required checks passed and zero verdicts, and "
    "the M-140 Scribe's ledger complete with its "
    "totals closing exactly over the shared rate "
    "table. This layer holds the gate record as data "
    "only; the gate's tests own the live re-proof."
)

_ID_RE = re.compile(r"^M-\d{3}$")


@dataclass(frozen=True)
class SliceRef:
    """One Part VI slice the gate closes over."""

    slice: str
    title: str


@dataclass(frozen=True)
class FeatureSlice:
    """One slice of the exercise's six-slice feature."""

    slice: str
    title: str
    office: str


@dataclass(frozen=True)
class DealtPair:
    """One feature slice dealt to one crew member."""

    slice: str
    member: str


@dataclass(frozen=True)
class WorktreeAssignment:
    """One member's worktree for one slice, in one wave."""

    member: str
    slice: str
    branch: str
    path: str


@dataclass(frozen=True)
class WorktreeWave:
    """One wave of worktree assignments, in held order."""

    wave: int
    assignments: Tuple[WorktreeAssignment, ...]


@dataclass(frozen=True)
class MergeRecord:
    """One recorded merge of one dealt pair."""

    member: str
    slice: str
    branch: str
    gate: str
    outcome: str


@dataclass(frozen=True)
class AuditCase:
    """One feature slice standing before the Auditor."""

    slice: str
    title: str
    builder: str


@dataclass(frozen=True)
class AuditCheck:
    """One check a feature slice carries before the Auditor."""

    slice: str
    name: str
    required: bool


@dataclass(frozen=True)
class AuditResult:
    """What the Auditor's run of one check found."""

    slice: str
    check: str
    outcome: str


@dataclass(frozen=True)
class CostEntry:
    """One priced run record: one member's run on one slice."""

    member: str
    entry_id: str
    slice: str
    model: str
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class Exercise:
    """One gate exercise: its crew, its claim, its evidence."""

    id: str
    title: str
    owning_slices: Tuple[str, ...]
    status: str
    evidence_kind: str
    evidence: str
    crew: Tuple[str, ...]
    coordinator: str
    feature_slices: Tuple[FeatureSlice, ...]
    dealt: Tuple[DealtPair, ...]
    worktree_waves: Tuple[WorktreeWave, ...]
    merges: Tuple[MergeRecord, ...]
    merge_verdicts: int
    audit_cases: Tuple[AuditCase, ...]
    audit_checks: Tuple[AuditCheck, ...]
    audit_results: Tuple[AuditResult, ...]
    audit_verdicts: int
    cost_entries: Tuple[CostEntry, ...]
    cost_calls: int
    cost_input_tokens: int
    cost_output_tokens: int
    cost_total_usd: float

    def feature_slice_ids(self) -> Tuple[str, ...]:
        """The feature's slices, in held order."""
        return tuple(f.slice for f in self.feature_slices)

    def dealt_pairs(self) -> Tuple[Tuple[str, str], ...]:
        """The dealt (slice, member) pairs, in held order."""
        return tuple((d.slice, d.member) for d in self.dealt)

    def cost_totals(self) -> Tuple[int, int, int]:
        """The cost entries' own sums: calls/input/output."""
        return (
            len(self.cost_entries),
            sum(e.input_tokens for e in self.cost_entries),
            sum(e.output_tokens for e in self.cost_entries))


@dataclass(frozen=True)
class Gate:
    """The validated Part VI gate record."""

    gate_slice: str
    part: int
    part_title: str
    verdict: str
    gate_note: str
    baseline_resource: str
    baseline: Tuple[int, int, int, int]
    slices: Tuple[SliceRef, ...]
    exercises: Tuple[Exercise, ...]

    def slice_ids(self) -> Tuple[str, ...]:
        """The gated slices, in road order (M-121..M-145)."""
        return tuple(s.slice for s in self.slices)

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
        """The M-145 baseline: collected/passed/failed/skipped."""
        return self.baseline


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: Any) -> bool:
    return (isinstance(value, (int, float))
            and not isinstance(value, bool))


def _usd(value: float) -> str:
    """A USD total in plain words, trailing zeros trimmed."""
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return text if text else "0"


def _pairs(entries: Any, first: str, second: str) -> List[Tuple[Any, Any]]:
    """(first, second) pairs from a list of mappings, safely."""
    pairs: List[Tuple[Any, Any]] = []
    if isinstance(entries, list):
        for entry in entries:
            if isinstance(entry, dict):
                pairs.append((entry.get(first), entry.get(second)))
    return pairs


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
    if data.get("part") != 6:
        problems.append(f"part must be 6, got {data.get('part')!r}")
    if data.get("verdict") != "PASS":
        problems.append(
            "verdict must be 'PASS' (a failed gate is a defect, not a "
            f"record), got {data.get('verdict')!r}")
    for key in ("part_title", "gate_note"):
        if not isinstance(data.get(key), str) or not data[key]:
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
            f"(M-121..M-145), got {len(slices)}")
    slice_titles: Dict[str, Any] = {}
    for position, ref in enumerate(slices, start=121):
        if not isinstance(ref, dict):
            problems.append(f"slice entry is not a mapping: {ref!r}")
            continue
        sid = ref.get("slice")
        expected = f"M-{position:03d}"
        if not isinstance(sid, str) or not _ID_RE.match(sid):
            problems.append(f"slice {sid!r}: slice must look like 'M-121'")
        elif sid != expected:
            problems.append(
                f"slice {sid}: slices must be sequential, expected {expected}")
        if not isinstance(ref.get("title"), str) or not ref["title"]:
            problems.append(f"slice {sid}: title must be non-empty")
        if isinstance(sid, str):
            slice_titles[sid] = ref.get("title")

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
            if not isinstance(exercise.get(key), str) or not exercise[key]:
                problems.append(f"exercise {eid}: {key} must be non-empty")
        owning = exercise.get("owning_slices")
        if not isinstance(owning, list) or not owning or not all(
                isinstance(s, str) and _ID_RE.match(s)
                and "M-121" <= s <= "M-145" for s in owning):
            problems.append(
                f"exercise {eid}: owning_slices must name Part VI slices")
        if eid == "crew_build":
            problems.extend(_validate_crew_build(exercise, slice_titles))
    return problems


def _validate_crew_build(exercise: Dict[str, Any],
                         slice_titles: Dict[str, Any]) -> List[str]:
    """Every problem in the crew_build exercise's own arithmetic."""
    problems: List[str] = []
    eid = "crew_build"

    crew = exercise.get("crew")
    if not isinstance(crew, list) or not crew or not all(
            isinstance(m, str) and m for m in crew) \
            or len(set(crew)) != len(crew):
        problems.append(
            f"exercise {eid}: crew must be a non-empty list of "
            "distinct member ids")
        crew = []
    crew_set = set(crew)
    coordinator = exercise.get("coordinator")
    if not isinstance(coordinator, str) or not coordinator:
        problems.append(
            f"exercise {eid}: coordinator must name the member who "
            "coordinates (and merges)")
    elif coordinator in crew_set:
        problems.append(
            f"exercise {eid}: the coordinator {coordinator!r} holds "
            "no crew seat — the coordinator merges, and is not one "
            "of the building crew")

    features = exercise.get("feature_slices")
    if not isinstance(features, list) or not features:
        problems.append(
            f"exercise {eid}: feature_slices must be a non-empty list")
        features = []
    feature_office: Dict[str, Any] = {}
    for entry in features:
        if not isinstance(entry, dict):
            problems.append(
                f"exercise {eid}: feature entry is not a mapping: {entry!r}")
            continue
        sid = entry.get("slice")
        if not isinstance(sid, str) or not _ID_RE.match(sid) \
                or not ("M-121" <= sid <= "M-145"):
            problems.append(
                f"exercise {eid}: feature slice {sid!r} must name a "
                "Part VI slice")
        if sid in feature_office:
            problems.append(
                f"exercise {eid}: feature slice {sid} is named twice")
        feature_office[sid] = entry.get("office")
        if not isinstance(entry.get("title"), str) or not entry["title"]:
            problems.append(
                f"exercise {eid}: feature slice {sid}: title must be "
                "non-empty")
        elif sid in slice_titles and entry["title"] != slice_titles[sid]:
            problems.append(
                f"exercise {eid}: feature slice {sid}: title "
                f"{entry['title']!r} is not the gated slice's title "
                f"{slice_titles[sid]!r}")
        if entry.get("office") not in crew_set:
            problems.append(
                f"exercise {eid}: feature slice {sid}: office "
                f"{entry.get('office')!r} is held by no crew member")

    dealt = exercise.get("dealt")
    if not isinstance(dealt, list) or not dealt:
        problems.append(f"exercise {eid}: dealt must be a non-empty list")
        dealt = []
    dealt_map: Dict[Any, Any] = {}
    for pair in _pairs(dealt, "slice", "member"):
        if pair[0] in dealt_map:
            problems.append(
                f"exercise {eid}: slice {pair[0]} is dealt twice — "
                "one slice, one member")
        dealt_map[pair[0]] = pair[1]
    if set(dealt_map) != set(feature_office):
        problems.append(
            f"exercise {eid}: dealt pairs must cover exactly the "
            f"feature slices, got dealt {sorted(map(str, dealt_map))} "
            f"for features {sorted(map(str, feature_office))}")
    for sid, member in dealt_map.items():
        if member not in crew_set:
            problems.append(
                f"exercise {eid}: slice {sid} is dealt to "
                f"{member!r}, who is not in the crew")
        elif sid in feature_office and member != feature_office[sid]:
            problems.append(
                f"exercise {eid}: slice {sid} is dealt to {member!r} "
                f"but its work fits the office "
                f"{feature_office[sid]!r} — every deal must be an "
                "office fit")
    if crew_set and set(dealt_map.values()) != crew_set:
        problems.append(
            f"exercise {eid}: every crew member must be dealt at "
            "least one slice — the crew builds together")

    waves = exercise.get("worktree_waves")
    if not isinstance(waves, list) or not waves:
        problems.append(
            f"exercise {eid}: worktree_waves must be a non-empty list")
        waves = []
    assigned: Dict[Tuple[Any, Any], Dict[str, Any]] = {}
    member_paths: Dict[Any, Any] = {}
    for position, wave in enumerate(waves, start=1):
        if not isinstance(wave, dict):
            problems.append(
                f"exercise {eid}: wave entry is not a mapping: {wave!r}")
            continue
        if wave.get("wave") != position:
            problems.append(
                f"exercise {eid}: worktree waves must be numbered "
                f"from 1 in order, got {wave.get('wave')!r} at "
                f"position {position}")
        assignments = wave.get("assignments")
        if not isinstance(assignments, list) or not assignments:
            problems.append(
                f"exercise {eid}: wave {position}: assignments must "
                "be a non-empty list")
            continue
        for entry in assignments:
            if not isinstance(entry, dict):
                problems.append(
                    f"exercise {eid}: wave {position}: assignment is "
                    f"not a mapping: {entry!r}")
                continue
            member, sid = entry.get("member"), entry.get("slice")
            key = (sid, member)
            if key in assigned:
                problems.append(
                    f"exercise {eid}: dealt pair {sid} / {member} is "
                    "assigned a worktree twice")
            assigned[key] = entry
            if member == coordinator:
                problems.append(
                    f"exercise {eid}: the coordinator {member!r} "
                    "holds a worktree — the coordinator merges and "
                    "holds no worktree")
            if entry.get("branch") != f"crew/{member}/{str(sid).lower()}":
                problems.append(
                    f"exercise {eid}: assignment {sid} / {member}: "
                    f"branch must be the member's own conventional "
                    f"branch crew/{member}/{str(sid).lower()}, got "
                    f"{entry.get('branch')!r}")
            if entry.get("path") != f"worktrees/{member}":
                problems.append(
                    f"exercise {eid}: assignment {sid} / {member}: "
                    f"path must be the member's own worktree "
                    f"worktrees/{member}, got {entry.get('path')!r}")
            if member in member_paths \
                    and member_paths[member] != entry.get("path"):
                problems.append(
                    f"exercise {eid}: member {member} holds two "
                    "worktree paths — one member, one tree")
            member_paths[member] = entry.get("path")
    dealt_keys = {(sid, member) for sid, member in dealt_map.items()}
    if set(assigned) != dealt_keys:
        problems.append(
            f"exercise {eid}: worktree waves must assign each dealt "
            f"pair exactly once, got {sorted(map(str, assigned))} for "
            f"dealt {sorted(map(str, dealt_keys))}")
    if len(set(member_paths.values())) != len(member_paths):
        problems.append(
            f"exercise {eid}: two members share one worktree path — "
            "never two writers in one tree")

    merges = exercise.get("merges")
    if not isinstance(merges, list) or not merges:
        problems.append(f"exercise {eid}: merges must be a non-empty list")
        merges = []
    merge_keys = set()
    for entry in merges:
        if not isinstance(entry, dict):
            problems.append(
                f"exercise {eid}: merge entry is not a mapping: {entry!r}")
            continue
        key = (entry.get("slice"), entry.get("member"))
        if key in merge_keys:
            problems.append(
                f"exercise {eid}: dealt pair {key[0]} / {key[1]} is "
                "merged twice")
        merge_keys.add(key)
        held = assigned.get(key)
        if held is not None and entry.get("branch") != held.get("branch"):
            problems.append(
                f"exercise {eid}: merge {key[0]} / {key[1]}: branch "
                f"{entry.get('branch')!r} is not the pair's worktree "
                f"branch {held.get('branch')!r}")
        if entry.get("gate") != "passed" or entry.get("outcome") != "green":
            problems.append(
                f"exercise {eid}: merge {key[0]} / {key[1]}: every "
                "merge must carry a passed test gate and a green "
                f"outcome, got gate {entry.get('gate')!r} / outcome "
                f"{entry.get('outcome')!r}")
    if merge_keys != dealt_keys:
        problems.append(
            f"exercise {eid}: merges must cover every dealt pair "
            f"exactly, got {sorted(map(str, merge_keys))} for dealt "
            f"{sorted(map(str, dealt_keys))}")
    if exercise.get("merge_verdicts") != 0:
        problems.append(
            f"exercise {eid}: merge_verdicts must be 0 — the gate "
            "banks a clean merge, every line complete, got "
            f"{exercise.get('merge_verdicts')!r}")

    cases = exercise.get("audit_cases")
    if not isinstance(cases, list) or not cases:
        problems.append(
            f"exercise {eid}: audit_cases must be a non-empty list")
        cases = []
    case_slices = set()
    for entry in cases:
        if not isinstance(entry, dict):
            problems.append(
                f"exercise {eid}: audit case is not a mapping: {entry!r}")
            continue
        sid = entry.get("slice")
        if sid in case_slices:
            problems.append(
                f"exercise {eid}: slice {sid} stands before the "
                "Auditor twice")
        case_slices.add(sid)
        feature = next(
            (f for f in features
             if isinstance(f, dict) and f.get("slice") == sid), None)
        if feature is not None and entry.get("title") != feature.get("title"):
            problems.append(
                f"exercise {eid}: audit case {sid}: title "
                f"{entry.get('title')!r} is not the feature slice's "
                f"title {feature.get('title')!r}")
        if sid in dealt_map and entry.get("builder") != dealt_map[sid]:
            problems.append(
                f"exercise {eid}: audit case {sid}: builder "
                f"{entry.get('builder')!r} is not the member the "
                f"slice was dealt to ({dealt_map[sid]!r})")
    if case_slices != set(feature_office):
        problems.append(
            f"exercise {eid}: audit cases must cover every feature "
            f"slice exactly, got {sorted(map(str, case_slices))} for "
            f"features {sorted(map(str, feature_office))}")

    checks = exercise.get("audit_checks")
    if not isinstance(checks, list) or not checks:
        problems.append(
            f"exercise {eid}: audit_checks must be a non-empty list")
        checks = []
    check_keys = set()
    for entry in checks:
        if not isinstance(entry, dict):
            problems.append(
                f"exercise {eid}: audit check is not a mapping: {entry!r}")
            continue
        key = (entry.get("slice"), entry.get("name"))
        if key in check_keys:
            problems.append(
                f"exercise {eid}: audit check {key[0]} / {key[1]} is "
                "carried twice")
        check_keys.add(key)
        if entry.get("required") is not True:
            problems.append(
                f"exercise {eid}: audit check {key[0]} / {key[1]}: "
                "the gate's checks are required — required must be "
                f"true, got {entry.get('required')!r}")
    wanted_checks = {(sid, name) for sid in feature_office
                     for name in REQUIRED_CHECKS}
    if check_keys != wanted_checks:
        problems.append(
            f"exercise {eid}: audit checks must carry both required "
            f"checks {REQUIRED_CHECKS} for every feature slice, got "
            f"{sorted(map(str, check_keys))}")

    results = exercise.get("audit_results")
    if not isinstance(results, list) or not results:
        problems.append(
            f"exercise {eid}: audit_results must be a non-empty list")
        results = []
    result_keys = set()
    for entry in results:
        if not isinstance(entry, dict):
            problems.append(
                f"exercise {eid}: audit result is not a mapping: "
                f"{entry!r}")
            continue
        key = (entry.get("slice"), entry.get("check"))
        if key in result_keys:
            problems.append(
                f"exercise {eid}: audit check {key[0]} / {key[1]} "
                "holds two results")
        result_keys.add(key)
        if entry.get("outcome") != "passed":
            problems.append(
                f"exercise {eid}: audit result {key[0]} / {key[1]}: "
                "every required check must pass — outcome must be "
                f"'passed', got {entry.get('outcome')!r}")
    if result_keys != check_keys:
        problems.append(
            f"exercise {eid}: audit results must cover every audit "
            f"check exactly, got {sorted(map(str, result_keys))} for "
            f"checks {sorted(map(str, check_keys))}")
    if exercise.get("audit_verdicts") != 0:
        problems.append(
            f"exercise {eid}: audit_verdicts must be 0 — the gate "
            "banks the Auditor's approval, got "
            f"{exercise.get('audit_verdicts')!r}")

    entries = exercise.get("cost_entries")
    if not isinstance(entries, list) or not entries:
        problems.append(
            f"exercise {eid}: cost_entries must be a non-empty list")
        entries = []
    entry_keys = set()
    entry_ids = set()
    total_input = 0
    total_output = 0
    total_cost = 0.0
    costs_close = True
    for entry in entries:
        if not isinstance(entry, dict):
            problems.append(
                f"exercise {eid}: cost entry is not a mapping: {entry!r}")
            costs_close = False
            continue
        key = (entry.get("slice"), entry.get("member"))
        if key in entry_keys:
            problems.append(
                f"exercise {eid}: cost entries hold the dealt pair "
                f"{key[0]} / {key[1]} twice")
        entry_keys.add(key)
        if entry.get("entry_id") in entry_ids:
            problems.append(
                f"exercise {eid}: cost entry id "
                f"{entry.get('entry_id')!r} is named twice")
        entry_ids.add(entry.get("entry_id"))
        if not isinstance(entry.get("model"), str) or not entry["model"]:
            problems.append(
                f"exercise {eid}: cost entry {key[0]} / {key[1]}: "
                "model must be non-empty")
            costs_close = False
        if not _is_int(entry.get("input_tokens")) \
                or entry.get("input_tokens", -1) < 0 \
                or not _is_int(entry.get("output_tokens")) \
                or entry.get("output_tokens", -1) < 0:
            problems.append(
                f"exercise {eid}: cost entry {key[0]} / {key[1]}: "
                "token counts must be non-negative integers")
            costs_close = False
        else:
            total_input += entry["input_tokens"]
            total_output += entry["output_tokens"]
            cost, known = _shared_price(
                entry["model"], entry["input_tokens"],
                entry["output_tokens"])
            total_cost += cost
            if not known:
                problems.append(
                    f"exercise {eid}: cost entry {key[0]} / {key[1]}: "
                    f"model {entry['model']!r} is not priced by the "
                    "shared rate table — an unpriced run cannot close "
                    "the ledger")
                costs_close = False
    if entry_keys != dealt_keys:
        problems.append(
            f"exercise {eid}: cost entries must hold one priced run "
            f"record for every dealt pair, got "
            f"{sorted(map(str, entry_keys))} for dealt "
            f"{sorted(map(str, dealt_keys))}")
    if exercise.get("cost_calls") != len(entries):
        problems.append(
            f"exercise {eid}: cost_calls must count the cost entries "
            f"({len(entries)}), got {exercise.get('cost_calls')!r}")
    if exercise.get("cost_input_tokens") != total_input:
        problems.append(
            f"exercise {eid}: cost_input_tokens must equal the "
            f"entries' own sum ({total_input}), got "
            f"{exercise.get('cost_input_tokens')!r}")
    if exercise.get("cost_output_tokens") != total_output:
        problems.append(
            f"exercise {eid}: cost_output_tokens must equal the "
            f"entries' own sum ({total_output}), got "
            f"{exercise.get('cost_output_tokens')!r}")
    stated_cost = exercise.get("cost_total_usd")
    if not _is_number(stated_cost):
        problems.append(
            f"exercise {eid}: cost_total_usd must be a number, got "
            f"{stated_cost!r}")
    elif costs_close and round(float(stated_cost), 6) != round(total_cost, 6):
        problems.append(
            f"exercise {eid}: cost_total_usd must be the shared rate "
            f"table's pricing of the entries ({_usd(round(total_cost, 6))}), "
            f"got {stated_cost!r}")
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
            crew=tuple(raw["crew"]), coordinator=raw["coordinator"],
            feature_slices=tuple(
                FeatureSlice(slice=f["slice"], title=f["title"],
                             office=f["office"])
                for f in raw["feature_slices"]),
            dealt=tuple(
                DealtPair(slice=d["slice"], member=d["member"])
                for d in raw["dealt"]),
            worktree_waves=tuple(
                WorktreeWave(
                    wave=w["wave"],
                    assignments=tuple(
                        WorktreeAssignment(
                            member=a["member"], slice=a["slice"],
                            branch=a["branch"], path=a["path"])
                        for a in w["assignments"]))
                for w in raw["worktree_waves"]),
            merges=tuple(
                MergeRecord(member=m["member"], slice=m["slice"],
                            branch=m["branch"], gate=m["gate"],
                            outcome=m["outcome"])
                for m in raw["merges"]),
            merge_verdicts=raw["merge_verdicts"],
            audit_cases=tuple(
                AuditCase(slice=c["slice"], title=c["title"],
                          builder=c["builder"])
                for c in raw["audit_cases"]),
            audit_checks=tuple(
                AuditCheck(slice=c["slice"], name=c["name"],
                           required=c["required"])
                for c in raw["audit_checks"]),
            audit_results=tuple(
                AuditResult(slice=r["slice"], check=r["check"],
                            outcome=r["outcome"])
                for r in raw["audit_results"]),
            audit_verdicts=raw["audit_verdicts"],
            cost_entries=tuple(
                CostEntry(member=e["member"], entry_id=e["entry_id"],
                          slice=e["slice"], model=e["model"],
                          input_tokens=e["input_tokens"],
                          output_tokens=e["output_tokens"])
                for e in raw["cost_entries"]),
            cost_calls=raw["cost_calls"],
            cost_input_tokens=raw["cost_input_tokens"],
            cost_output_tokens=raw["cost_output_tokens"],
            cost_total_usd=raw["cost_total_usd"]))
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
        exercises=tuple(exercises))


def load_gate(data: Optional[Dict[str, Any]] = None) -> Gate:
    """Load and validate the shipped Part VI gate (or *data*)."""
    raw = data if data is not None else load_resource(GATE_RESOURCE)
    problems = validate_gate(raw)
    if problems:
        raise ValidationError(
            "part VI gate failed validation: " + "; ".join(problems))
    return _to_gate(raw)  # type: ignore[arg-type]


def plain_words(gate: Gate) -> str:
    """The gate stated in plain words, from its own accessors."""
    collected, passed, failed, skipped = gate.baseline_totals()
    exercise = gate.exercise(EXERCISE_IDS[0])
    calls, inputs, outputs = exercise.cost_totals()
    return (
        f"Part VI gate ({gate.gate_slice}): {gate.verdict}. "
        f"{len(gate.slice_ids())} slices gated "
        f"({gate.slice_ids()[0]}..{gate.slice_ids()[-1]}); the "
        f"six-slice crew feature completed by a "
        f"{len(exercise.crew)}-member crew — merged clean with "
        f"{exercise.merge_verdicts} merge verdicts, "
        f"Auditor-approved with {exercise.audit_verdicts} audit "
        f"verdicts, and the cost ledger complete ({calls} calls, "
        f"{inputs} input tokens, {outputs} output tokens, "
        f"${_usd(exercise.cost_total_usd)}), banked against the "
        f"M-145 confirmation suite ({collected} collected, "
        f"{passed} passed, {failed} failed, {skipped} skipped).")


def gate_record(gate: Gate) -> Dict[str, Any]:
    """The session-news record of the gate."""
    return {
        "type": "part6_gate",
        "slice": GATE_SLICE,
        "part": gate.part,
        "verdict": gate.verdict,
        "slices": list(gate.slice_ids()),
        "exercises": list(gate.exercise_ids()),
        "baseline": list(gate.baseline_totals()),
        "plain": plain_words(gate),
    }


def render_markdown(gate: Gate) -> str:
    """Render the gate as markdown: verdict, exercises, baseline.

    Built from :meth:`Gate.slice_ids`, :meth:`Gate.exercise_ids`,
    :meth:`Gate.completed_exercises`, :meth:`Gate.baseline_totals`,
    :meth:`Gate.exercise` and :func:`plain_words`, so the rendered
    page itself is computed from the same accessors the tests pin.
    """
    collected, passed, failed, skipped = gate.baseline_totals()
    lines = [
        "# Part VI Gate — The Crew (M-146)",
        "",
        f"*Gate slice {gate.gate_slice}, part {gate.part} — "
        f"{gate.part_title}. Verdict: **{gate.verdict}**.*",
        "",
        gate.gate_note,
        "",
        f"**Slices gated:** {len(gate.slice_ids())} "
        f"({gate.slice_ids()[0]}..{gate.slice_ids()[-1]}).",
        "",
        f"**Baseline (M-145 confirmation suite, "
        f"{gate.baseline_resource}):** "
        f"{collected} collected — {passed} passed, {failed} failed, "
        f"{skipped} skipped.",
        "",
        "## Exercises — completed",
        "",
    ]
    for exercise_id in gate.exercise_ids():
        exercise = gate.exercise(exercise_id)
        lines.append(
            f"- **{exercise.title}** ({exercise.id}; owning slices "
            f"{', '.join(exercise.owning_slices)}; evidence kind "
            f"{exercise.evidence_kind}; crew "
            f"{', '.join(exercise.crew)} under coordinator "
            f"{exercise.coordinator}; feature slices "
            f"{', '.join(exercise.feature_slice_ids())}): "
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
