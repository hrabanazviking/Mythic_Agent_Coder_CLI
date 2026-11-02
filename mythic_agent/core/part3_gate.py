"""The Part III gate (All-Features roadmap slice M-070).

Part III — Code Intelligence — closes here. The roadmap's gate
words: *on the benchmark pack — a cross-file rename, a
structural codemod, and a debugger-caught bug, all completed
with the new senses, evidence banked against the M-007
baseline.*

This module is the gate's machinery:

* A validated gate record
  (``mythic_agent/data/part3_gate.yaml``) naming the Part III
  slices it closes over (M-043..M-069), the M-007 baseline
  freeze it is banked against, and the three exercises, each
  carrying its own benchmark-pack-style throwaway repo (seed
  files + hidden grading tests, the M-008 pattern).
* The exercise runners' shared roads the gate's tests use:
  :func:`materialise_exercise` writes an exercise's repo,
  :func:`grade_exercise` runs its hidden grading tests in a
  subprocess, and :func:`verify_rename` judges a renamed repo
  by its files, never by a report's word. The exercises
  themselves ride their owning slices' shipped machinery —
  the LSP rename road (M-051), the structural rewrite road
  (M-048), and the debugger in the loop (M-055) — wired by
  the gate's tests, so this core module imports no service
  layer.

Honesty rules, enforced by the validator and pinned by tests:

* Exactly three exercises, in roadmap order: rename, codemod,
  debug. Each is ``completed`` only with its evidence kind
  stated — the rename is ``fake-server-measured`` and the
  debug catch is ``fake-adapter-measured``: both ride a fake
  server/adapter speaking the real protocol (the M-051/M-055
  test pattern), and **no live language server and no real
  debugpy session is claimed** by this gate.
* The baseline section must close arithmetically and is
  cross-checked against the live M-007 freeze by the gate's
  tests.
* The verdict is ``PASS`` and the validator accepts no other
  verdict: a gate that has failed is a defect to fix, not a
  record.
"""

from __future__ import annotations

__all__ = [
    "EXERCISE_IDS",
    "EVIDENCE_KINDS",
    "GATE_RESOURCE",
    "GATE_SCHEMA",
    "GATE_SLICE",
    "Any",
    "Dict",
    "Exercise",
    "ExerciseFile",
    "Gate",
    "List",
    "Optional",
    "SliceRef",
    "Tuple",
    "grade_exercise",
    "load_gate",
    "materialise_exercise",
    "render_markdown",
    "validate_gate",
    "verify_rename",
]

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .validation import ValidationError

#: Resource name of the gate data file inside ``mythic_agent/data``.
GATE_RESOURCE = "part3_gate.yaml"

#: The only schema this loader accepts.
GATE_SCHEMA = "mythic.part3_gate/1"

#: The slice that owns this gate.
GATE_SLICE = "M-070"

#: The gate's exercises, in roadmap order.
EXERCISE_IDS = ("rename", "codemod", "debug")

#: Evidence kinds an exercise may honestly claim.
EVIDENCE_KINDS = (
    "fake-server-measured", "structural-measured",
    "fake-adapter-measured")

_ID_RE = re.compile(r"^M-\d{3}$")


@dataclass(frozen=True)
class SliceRef:
    """One Part III slice the gate closes over."""

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
    grading_file: Optional[ExerciseFile]
    grading_tests: int
    details: Dict[str, Any]

    def seed_paths(self) -> Tuple[str, ...]:
        """The exercise repo's seed file paths, in order."""
        return tuple(f.path for f in self.seed_files)


@dataclass(frozen=True)
class Gate:
    """The validated Part III gate record."""

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
        """The gated slices, in road order (M-043..M-069)."""
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
        """The M-007 baseline totals: collected/passed/failed/skipped."""
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


def grade_exercise(exercise: Exercise, root: Path) -> Tuple[int, int]:
    """Grade the repo at *root* with *exercise*'s hidden tests.

    Runs ``python -m pytest -q test_grading.py`` in a
    subprocess. Returns ``(passed, total)`` where total is
    the grading file's own ``def test_`` count; an exercise
    with no grading file, or a run that cannot collect,
    counts as zero passed, never as a pass.
    """
    if exercise.grading_file is None:
        return 0, 0
    total = exercise.grading_file.content.count("def test_")
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             exercise.grading_file.path],
            cwd=str(root), capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return 0, total
    match = re.search(r"(\d+) passed", proc.stdout)
    passed = int(match.group(1)) if match else 0
    if proc.returncode != 0:
        return min(passed, total), total
    return passed, total


def verify_rename(exercise: Exercise, root: Path) -> List[str]:
    """Problems with the rename of *exercise*'s repo at *root*.

    An empty list means the rename truly landed: the old name
    appears in no seed file, and the new name appears in every
    seed file — judged from the files themselves.
    """
    old = exercise.details.get("old_name")
    new = exercise.details.get("new_name")
    problems: List[str] = []
    if not isinstance(old, str) or not old or not isinstance(new, str) \
            or not new:
        return ["the rename exercise names no old/new name to verify"]
    for seed in exercise.seed_files:
        target = root / seed.path
        if not target.is_file():
            problems.append(f"{seed.path}: missing after the rename")
            continue
        text = target.read_text(encoding="utf-8")
        if old in text:
            problems.append(
                f"{seed.path}: the old name {old!r} is still present")
        if new not in text:
            problems.append(
                f"{seed.path}: the new name {new!r} is absent")
    return problems


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
    if data.get("part") != 3:
        problems.append(f"part must be 3, got {data.get('part')!r}")
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
        if baseline.get("resource") != "baseline_freeze.yaml":
            problems.append(
                "baseline.resource must be 'baseline_freeze.yaml', got "
                f"{baseline.get('resource')!r}")
        counts = [baseline.get(k) for k in
                  ("collected", "passed", "failed", "skipped")]
        if not all(isinstance(c, int) and c >= 0 for c in counts):
            problems.append("baseline counts must be non-negative integers")
        elif counts[0] != counts[1] + counts[2] + counts[3]:
            problems.append(
                "baseline arithmetic does not close: collected must equal "
                f"passed + failed + skipped, got {counts}")

    slices = data.get("slices")
    if not isinstance(slices, list) or not slices:
        problems.append("slices must be a non-empty list")
        slices = []
    if len(slices) != 27:
        problems.append(
            f"slices must number exactly 27 (M-043..M-069), got {len(slices)}")
    for position, ref in enumerate(slices, start=43):
        if not isinstance(ref, dict):
            problems.append(f"slice entry is not a mapping: {ref!r}")
            continue
        sid = ref.get("slice")
        expected = f"M-{position:03d}"
        if not isinstance(sid, str) or not _ID_RE.match(sid):
            problems.append(f"slice {sid!r}: slice must look like 'M-043'")
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
                and "M-043" <= s <= "M-069" for s in owning):
            problems.append(
                f"exercise {eid}: owning_slices must name Part III slices")
        seeds = exercise.get("seed_files")
        if not isinstance(seeds, list) or not seeds:
            problems.append(f"exercise {eid}: seed_files must be non-empty")
            seeds = []
        for seed in seeds:
            if not isinstance(seed, dict) or not seed.get("path") \
                    or not isinstance(seed.get("content"), str) \
                    or not seed["content"]:
                problems.append(
                    f"exercise {eid}: every seed file needs a path and "
                    "non-empty content")
        grading = exercise.get("grading_file")
        grading_tests = exercise.get("grading_tests")
        if grading is None:
            if grading_tests != 0:
                problems.append(
                    f"exercise {eid}: with no grading file, grading_tests "
                    f"must be 0, got {grading_tests!r}")
        elif not isinstance(grading, dict) or not grading.get("path") \
                or not isinstance(grading.get("content"), str):
            problems.append(
                f"exercise {eid}: grading_file needs a path and content")
        elif grading_tests != grading["content"].count("def test_"):
            problems.append(
                f"exercise {eid}: grading_tests must count the grading "
                f"file's own tests ({grading['content'].count('def test_')}), "
                f"got {grading_tests!r}")
        if eid == "rename":
            if exercise.get("files") != len(seeds) or len(seeds) != 2:
                problems.append(
                    "exercise rename: files must count its 2 seed files")
            if exercise.get("sites") != 4:
                problems.append(
                    "exercise rename: sites must be 4 (definition + call, "
                    f"import + call), got {exercise.get('sites')!r}")
            old, new = exercise.get("old_name"), exercise.get("new_name")
            if not old or not new or old == new:
                problems.append(
                    "exercise rename: old_name and new_name must differ")
            elif seeds and not all(
                    isinstance(s, dict) and old in str(s.get("content", ""))
                    for s in seeds):
                problems.append(
                    "exercise rename: the old name must appear in every "
                    "seed file — a rename with a one-file reach is not "
                    "cross-file")
        if eid == "codemod":
            if exercise.get("sites") != 2:
                problems.append(
                    "exercise codemod: sites must be 2, got "
                    f"{exercise.get('sites')!r}")
            pattern = exercise.get("pattern")
            if not isinstance(pattern, str) or "legacy_add" not in pattern:
                problems.append(
                    "exercise codemod: pattern must name the legacy call")
            if not isinstance(exercise.get("replacement"), str) \
                    or not exercise["replacement"]:
                problems.append(
                    "exercise codemod: replacement must be non-empty")
        if eid == "debug":
            if not isinstance(exercise.get("frame_line"), int) \
                    or exercise["frame_line"] <= 0:
                problems.append(
                    "exercise debug: frame_line must be a positive int")
            for key in ("test_node", "local_name", "local_value",
                        "stopped_reason"):
                if not isinstance(exercise.get(key), str) \
                        or not exercise[key]:
                    problems.append(
                        f"exercise debug: {key} must be non-empty")
    return problems


_DETAIL_KEYS = (
    "old_name", "new_name", "files", "sites", "pattern", "replacement",
    "test_node", "frame_line", "local_name", "local_value",
    "stopped_reason")


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
    """Load and validate the shipped Part III gate (or *data*)."""
    raw = data if data is not None else load_resource(GATE_RESOURCE)
    problems = validate_gate(raw)
    if problems:
        raise ValidationError(
            "part III gate failed validation: " + "; ".join(problems))
    return _to_gate(raw)  # type: ignore[arg-type]


def render_markdown(gate: Gate) -> str:
    """Render the gate as markdown: verdict, exercises, baseline.

    Built from :meth:`Gate.slice_ids`, :meth:`Gate.exercise_ids`,
    :meth:`Gate.completed_exercises`, :meth:`Gate.baseline_totals`,
    and :meth:`Gate.exercise`, so the rendered page itself is
    computed from the same accessors the tests pin.
    """
    collected, passed, failed, skipped = gate.baseline_totals()
    lines = [
        "# Part III Gate — Code Intelligence (M-070)",
        "",
        f"*Gate slice {gate.gate_slice}, part {gate.part} — "
        f"{gate.part_title}. Verdict: **{gate.verdict}**.*",
        "",
        gate.gate_note,
        "",
        f"**Slices gated:** {len(gate.slice_ids())} "
        f"({gate.slice_ids()[0]}..{gate.slice_ids()[-1]}).",
        "",
        f"**Baseline (M-007 freeze, {gate.baseline_resource}):** "
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
    ]
    return "\n".join(lines)
