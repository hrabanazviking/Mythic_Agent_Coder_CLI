"""The Part V gate (All-Features roadmap slice M-120).

Part V — Autonomy & Safety — closes here. The roadmap's gate
words: *an overnight-style autonomous run on the benchmark
pack under Trusted Forge — sandbox on, budgets on, audit
trail complete, zero doctrine violations.*

This module is the gate's machinery:

* A validated gate record
  (``mythic_agent/data/part5_gate.yaml``) naming the Part V
  slices it closes over (M-095..M-119), the M-119
  confirmation-suite baseline it is banked against, and the
  one overnight-run exercise, carrying its own
  benchmark-pack-style throwaway repo (seed files + hidden
  grading tests, the M-008 pattern), the shipped solution
  the run applies, and the exact run shape the gate banks:
  the Trusted Forge posture, the sandbox stance, the budget
  limits, the audit trail's entry kinds in append order,
  and the one destructive command the run holds.
* The exercise runners' shared roads the gate's tests use:
  :func:`materialise_exercise` writes an exercise's repo,
  :func:`apply_solution` lands its shipped solution files,
  :func:`grade_exercise` runs its hidden grading tests in
  a subprocess, and :func:`verify_run` judges a finished
  repo by its files, never by a report's word. The exercise
  itself rides the shipped Part V pure roads — M-095's
  permission profiles (``stored_profile``), M-097's OS
  sandbox plans (``build_confinement_plan``), M-107's
  budget judge (``judge_budget``), M-109's audit trail
  (``AuditRegistry`` / ``export_trail``) and M-111's
  destructive-command doctrine (``judge_command``) —
  wired by the gate's tests, so this core module imports
  no service layer.

Honesty rules, enforced by the validator and pinned by tests:

* Exactly one exercise: the overnight run. It is
  ``completed`` only with its evidence kind stated —
  ``pure-roads-measured``: every step rides a real shipped
  pure road against a real throwaway repository, and **no
  step is faked, stubbed, or claimed beyond what the tests
  do**. No model is run and no token is spent; the budget
  reading the tests judge is built from the run's own
  counted commands. The campaign tree is never the
  exercise repo.
* The gate banks **zero doctrine violations**: the
  record's ``doctrine_violations`` must be 0, every
  command the run executes is judged on the ladder by the
  tests, and the one destructive command the exercise
  names is judged irreversible and held — never executed.
* The audit trail must be complete: the record names the
  exact entry kinds in append order, the approval comes
  first (it covers the run's ask-once commands), and every
  audit kind the trail vocabulary holds appears at least
  once.
* The baseline section must close arithmetically: the
  M-119 confirmation suite's counted totals (6104
  collected, 6101 passed, 2 failed — the two long-classified
  environment cases — 1 skipped).
* The verdict is ``PASS`` and the validator accepts no
  other verdict: a gate that has failed is a defect to
  fix, not a record.

No agent layer is owed and none is built: the part gates
ride no live Agent road of their own (the M-094 / M-117
precedent) — the exercise rides the shipped pure roads,
wired by the gate's tests, and holds no session state.
No new setting is owed: the run's posture, sandbox,
budgets and audit trail are the settings and roads that
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
    "PART5_GATE_SLICE",
    "PLAIN_EXPLANATION",
    "SLICE_IDS",
    "Any",
    "Dict",
    "Exercise",
    "ExerciseFile",
    "Gate",
    "List",
    "Optional",
    "SliceRef",
    "Tuple",
    "apply_solution",
    "gate_record",
    "grade_exercise",
    "load_gate",
    "materialise_exercise",
    "plain_words",
    "render_markdown",
    "validate_gate",
    "verify_run",
]

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .audit_trail import AUDIT_KINDS
from .validation import ValidationError

#: Resource name of the gate data file inside ``mythic_agent/data``.
GATE_RESOURCE = "part5_gate.yaml"

#: The only schema this loader accepts.
GATE_SCHEMA = "mythic.part5_gate/1"

#: The slice that owns this gate.
GATE_SLICE = "M-120"

#: The shorter name other layers cite for this slice.
PART5_GATE_SLICE = GATE_SLICE

#: The Part V slices this gate closes over, in roadmap order.
SLICE_IDS = tuple(f"M-{n:03d}" for n in range(95, 120))

#: The confirmation suite the gate is banked against.
BASELINE_RESOURCE = "m119_confirmation_suite"

#: The gate's exercises, in roadmap order.
EXERCISE_IDS = ("overnight_run",)

#: Evidence kinds an exercise may honestly claim.
EVIDENCE_KINDS = ("pure-roads-measured",)

PLAIN_EXPLANATION = (
    "Part V gate: an overnight-style autonomous run on a "
    "benchmark-pack-style task under the Trusted Forge "
    "posture, re-proven live by the gate's tests through "
    "the shipped pure roads — an OS sandbox confinement "
    "plan with the network denied, a budget judged within "
    "its limits from the run's own counted commands, an "
    "append-only audit trail that exports complete, and "
    "every command judged on the destructive-command "
    "ladder with zero doctrine violations, the one named "
    "destructive command judged irreversible and held, "
    "never executed. This layer holds the gate record as "
    "data only; the gate's tests own the live re-proof."
)

_ID_RE = re.compile(r"^M-\d{3}$")


@dataclass(frozen=True)
class SliceRef:
    """One Part V slice the gate closes over."""

    slice: str
    title: str


@dataclass(frozen=True)
class ExerciseFile:
    """One file of an exercise's throwaway repo."""

    path: str
    content: str


@dataclass(frozen=True)
class Exercise:
    """One gate exercise: its repo, its claim, its evidence."""

    id: str
    title: str
    owning_slices: Tuple[str, ...]
    status: str
    evidence_kind: str
    evidence: str
    seed_files: Tuple[ExerciseFile, ...]
    solution_files: Tuple[ExerciseFile, ...]
    grading_file: Optional[ExerciseFile]
    grading_tests: int
    details: Dict[str, Any]

    def seed_paths(self) -> Tuple[str, ...]:
        """The exercise repo's seed file paths, in order."""
        return tuple(f.path for f in self.seed_files)


@dataclass(frozen=True)
class Gate:
    """The validated Part V gate record."""

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
        """The gated slices, in road order (M-095..M-119)."""
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
        """The M-119 baseline: collected/passed/failed/skipped."""
        return self.baseline


def materialise_exercise(exercise: Exercise, root: Path) -> Path:
    """Write *exercise*'s throwaway repo under *root*.

    Seed files plus the hidden grading file (when the
    exercise carries one). Returns *root*. Nothing outside
    *root* is written.
    """
    root.mkdir(parents=True, exist_ok=True)
    files = list(exercise.seed_files)
    if exercise.grading_file is not None:
        files.append(exercise.grading_file)
    for repo_file in files:
        target = root / repo_file.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(repo_file.content, encoding="utf-8")
    return root


def apply_solution(exercise: Exercise, root: Path) -> Tuple[str, ...]:
    """Land *exercise*'s shipped solution files at *root*.

    Returns the paths written, in order. Nothing outside
    *root* is written.
    """
    written = []
    for repo_file in exercise.solution_files:
        target = root / repo_file.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(repo_file.content, encoding="utf-8")
        written.append(repo_file.path)
    return tuple(written)


def grade_exercise(exercise: Exercise, root: Path) -> Tuple[int, int]:
    """Grade the repo at *root* with *exercise*'s hidden tests.

    Runs the exercise's own grading command in a
    subprocess. Returns ``(passed, total)`` where total is
    the grading file's own ``def test_`` count; an exercise
    with no grading file, or a run that cannot collect,
    counts as zero passed, never as a pass.
    """
    if exercise.grading_file is None:
        return 0, 0
    total = exercise.grading_file.content.count("def test_")
    command = str(exercise.details.get("grading_command") or "")
    argv = [sys.executable] + command.split()[1:] \
        if command.startswith("python ") else None
    if argv is None:
        return 0, total
    try:
        proc = subprocess.run(
            argv, cwd=str(root), capture_output=True, text=True,
            timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return 0, total
    match = re.search(r"(\d+) passed", proc.stdout)
    passed = int(match.group(1)) if match else 0
    if proc.returncode != 0:
        return min(passed, total), total
    return passed, total


def verify_run(exercise: Exercise, root: Path) -> List[str]:
    """Problems with the finished run of *exercise* at *root*.

    An empty list means the run truly landed: every
    solution file's content is on disk exactly, and the
    held command's named target still stands — judged
    from the files themselves.
    """
    problems: List[str] = []
    for repo_file in exercise.solution_files:
        target = root / repo_file.path
        if not target.is_file():
            problems.append(f"{repo_file.path}: missing after the run")
            continue
        if target.read_text(encoding="utf-8") != repo_file.content:
            problems.append(
                f"{repo_file.path}: the shipped solution did not land")
    held = exercise.details.get("held_command")
    if isinstance(held, str) and held.startswith("rm -rf "):
        target_name = held.split()[-1]
        if not (root / target_name).is_dir():
            problems.append(
                f"{target_name}: the held command's target is gone — "
                "the held command was executed, not held")
    return problems


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: Any) -> bool:
    return (isinstance(value, (int, float))
            and not isinstance(value, bool))


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
    if data.get("part") != 5:
        problems.append(f"part must be 5, got {data.get('part')!r}")
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
            f"(M-095..M-119), got {len(slices)}")
    for position, ref in enumerate(slices, start=95):
        if not isinstance(ref, dict):
            problems.append(f"slice entry is not a mapping: {ref!r}")
            continue
        sid = ref.get("slice")
        expected = f"M-{position:03d}"
        if not isinstance(sid, str) or not _ID_RE.match(sid):
            problems.append(f"slice {sid!r}: slice must look like 'M-095'")
        elif sid != expected:
            problems.append(
                f"slice {sid}: slices must be sequential, expected {expected}")
        if not isinstance(ref.get("title"), str) or not ref["title"]:
            problems.append(f"slice {sid}: title must be non-empty")

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
                and "M-095" <= s <= "M-119" for s in owning):
            problems.append(
                f"exercise {eid}: owning_slices must name Part V slices")
        for key in ("seed_files", "solution_files"):
            files = exercise.get(key)
            if not isinstance(files, list) or not files:
                problems.append(f"exercise {eid}: {key} must be non-empty")
                continue
            for repo_file in files:
                if not isinstance(repo_file, dict) \
                        or not repo_file.get("path") \
                        or not isinstance(repo_file.get("content"), str) \
                        or not repo_file["content"]:
                    problems.append(
                        f"exercise {eid}: every {key} file needs a path "
                        "and non-empty content")
        seeds = exercise.get("seed_files") or []
        solutions = exercise.get("solution_files") or []
        seed_paths = {s.get("path") for s in seeds if isinstance(s, dict)}
        for repo_file in solutions:
            if isinstance(repo_file, dict) \
                    and repo_file.get("path") not in seed_paths:
                problems.append(
                    f"exercise {eid}: solution file "
                    f"{repo_file.get('path')!r} names no seed file — a "
                    "solution that creates its target is not a fix")
        grading = exercise.get("grading_file")
        grading_tests = exercise.get("grading_tests")
        if grading is None:
            problems.append(
                f"exercise {eid}: the gate's run is graded — a grading "
                "file is owed")
        elif not isinstance(grading, dict) or not grading.get("path") \
                or not isinstance(grading.get("content"), str):
            problems.append(
                f"exercise {eid}: grading_file needs a path and content")
        elif grading_tests != grading["content"].count("def test_"):
            problems.append(
                f"exercise {eid}: grading_tests must count the grading "
                f"file's own tests ({grading['content'].count('def test_')}), "
                f"got {grading_tests!r}")
        if eid == "overnight_run":
            if exercise.get("profile_id") != "trusted-forge":
                problems.append(
                    "exercise overnight_run: profile_id must be "
                    "'trusted-forge' — the roadmap's gate runs under "
                    f"Trusted Forge, got {exercise.get('profile_id')!r}")
            if exercise.get("sandbox_platform") != "linux" \
                    or exercise.get("sandbox_network") != "deny":
                problems.append(
                    "exercise overnight_run: the sandbox must be on — "
                    "platform 'linux' with network 'deny', got "
                    f"{exercise.get('sandbox_platform')!r} / "
                    f"{exercise.get('sandbox_network')!r}")
            command = exercise.get("grading_command")
            if not isinstance(command, str) or "pytest" not in command \
                    or "test_grading.py" not in command:
                problems.append(
                    "exercise overnight_run: grading_command must name "
                    "the pytest run of the hidden grading file")
            if not _is_int(exercise.get("commands_run")) \
                    or exercise.get("commands_run", 0) < 1:
                problems.append(
                    "exercise overnight_run: commands_run must count "
                    "the run's real commands (at least the two grading "
                    f"runs), got {exercise.get('commands_run')!r}")
            held = exercise.get("held_command")
            if not isinstance(held, str) or not held:
                problems.append(
                    "exercise overnight_run: held_command must name "
                    "the destructive command the run holds")
            if exercise.get("held_rung") != "irreversible":
                problems.append(
                    "exercise overnight_run: held_rung must be "
                    "'irreversible' — the held command is judged on "
                    f"the top rung, got {exercise.get('held_rung')!r}")
            if exercise.get("doctrine_violations") != 0:
                problems.append(
                    "exercise overnight_run: doctrine_violations must "
                    "be 0 — the gate banks zero doctrine violations, "
                    f"got {exercise.get('doctrine_violations')!r}")
            limits = [exercise.get(k) for k in (
                "budget_token_limit", "budget_cost_limit",
                "budget_time_limit_seconds", "budget_command_limit")]
            if not all(_is_number(v) and v > 0 for v in limits):
                problems.append(
                    "exercise overnight_run: every budget limit must "
                    "be a positive number — budgets are on")
            if exercise.get("budget_status") != "within":
                problems.append(
                    "exercise overnight_run: budget_status must be "
                    "'within' — the run finishes inside its budget, "
                    f"got {exercise.get('budget_status')!r}")
            kinds = exercise.get("audit_kinds")
            if not isinstance(kinds, list) or not kinds:
                problems.append(
                    "exercise overnight_run: audit_kinds must name "
                    "the trail's entries in append order")
                kinds = []
            else:
                if kinds[0] != "approval":
                    problems.append(
                        "exercise overnight_run: the audit trail must "
                        "open with the human approval — it covers the "
                        "run's ask-once commands")
                unknown = [k for k in kinds if k not in AUDIT_KINDS]
                if unknown:
                    problems.append(
                        f"exercise overnight_run: unknown audit kinds "
                        f"{unknown}")
                missing = [k for k in AUDIT_KINDS if k not in kinds]
                if missing:
                    problems.append(
                        "exercise overnight_run: the audit trail is "
                        f"incomplete — kinds never recorded: {missing}")
            if exercise.get("audit_entries") != len(kinds):
                problems.append(
                    "exercise overnight_run: audit_entries must count "
                    f"the trail's entries ({len(kinds)}), got "
                    f"{exercise.get('audit_entries')!r}")
    return problems


_DETAIL_KEYS = (
    "profile_id", "sandbox_platform", "sandbox_network",
    "grading_command", "commands_run", "held_command", "held_rung",
    "doctrine_violations", "budget_token_limit", "budget_cost_limit",
    "budget_time_limit_seconds", "budget_command_limit",
    "budget_status", "audit_kinds", "audit_entries")


def _to_gate(data: Dict[str, Any]) -> Gate:
    baseline = data["baseline"]
    exercises = []
    for raw in data["exercises"]:
        grading = raw.get("grading_file")
        exercises.append(Exercise(
            id=raw["id"], title=raw["title"],
            owning_slices=tuple(raw["owning_slices"]),
            status=raw["status"], evidence_kind=raw["evidence_kind"],
            evidence=raw["evidence"],
            seed_files=tuple(
                ExerciseFile(path=f["path"], content=f["content"])
                for f in raw["seed_files"]),
            solution_files=tuple(
                ExerciseFile(path=f["path"], content=f["content"])
                for f in raw["solution_files"]),
            grading_file=ExerciseFile(
                path=grading["path"], content=grading["content"])
            if grading else None,
            grading_tests=raw["grading_tests"],
            details={k: raw[k] for k in _DETAIL_KEYS if k in raw}))
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
    """Load and validate the shipped Part V gate (or *data*)."""
    raw = data if data is not None else load_resource(GATE_RESOURCE)
    problems = validate_gate(raw)
    if problems:
        raise ValidationError(
            "part V gate failed validation: " + "; ".join(problems))
    return _to_gate(raw)  # type: ignore[arg-type]


def plain_words(gate: Gate) -> str:
    """The gate stated in plain words, from its own accessors."""
    collected, passed, failed, skipped = gate.baseline_totals()
    exercise = gate.exercise(EXERCISE_IDS[0])
    return (
        f"Part V gate ({gate.gate_slice}): {gate.verdict}. "
        f"{len(gate.slice_ids())} slices gated "
        f"({gate.slice_ids()[0]}..{gate.slice_ids()[-1]}); the "
        f"overnight run under Trusted Forge completed with "
        f"sandbox on, budgets on, the audit trail complete "
        f"({exercise.details['audit_entries']} entries) and "
        f"{exercise.details['doctrine_violations']} doctrine "
        f"violations, banked against the M-119 confirmation "
        f"suite ({collected} collected, {passed} passed, "
        f"{failed} failed, {skipped} skipped).")


def gate_record(gate: Gate) -> Dict[str, Any]:
    """The session-news record of the gate."""
    return {
        "type": "part5_gate",
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
        "# Part V Gate — Autonomy & Safety (M-120)",
        "",
        f"*Gate slice {gate.gate_slice}, part {gate.part} — "
        f"{gate.part_title}. Verdict: **{gate.verdict}**.*",
        "",
        gate.gate_note,
        "",
        f"**Slices gated:** {len(gate.slice_ids())} "
        f"({gate.slice_ids()[0]}..{gate.slice_ids()[-1]}).",
        "",
        f"**Baseline (M-119 confirmation suite, "
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
            f"{exercise.evidence_kind}; seed files "
            f"{', '.join(exercise.seed_paths())}): {exercise.evidence}")
    lines += [
        "",
        f"*{len(gate.completed_exercises())} of "
        f"{len(gate.exercise_ids())} exercises completed.*",
        "",
        plain_words(gate),
        "",
    ]
    return "\n".join(lines)
