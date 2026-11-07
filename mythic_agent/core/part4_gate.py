"""The Part IV gate (All-Features roadmap slice M-094).

Part IV — The Editor's Hand — closes here. The roadmap's gate
words: *benchmark refactor task completed with zero failed
applies, hunk review used, auto-commits clean, checkpoint
restore proven mid-task.*

This module is the gate's machinery:

* A validated gate record
  (``mythic_agent/data/part4_gate.yaml``) naming the Part IV
  slices it closes over (M-071..M-093), the M-093
  confirmation-suite baseline it is banked against, and the
  one benchmark refactor exercise, carrying its own
  benchmark-pack-style throwaway repo (seed files + hidden
  grading tests, the M-008 pattern) and the exact payloads
  the refactor rides on.
* The exercise runners' shared roads the gate's tests use:
  :func:`materialise_exercise` writes an exercise's repo,
  :func:`grade_exercise` runs its hidden grading tests in a
  subprocess, and :func:`verify_refactor` judges a refactored
  repo by its files, never by a report's word. The exercise
  itself rides the shipped Part IV agent roads — M-074's
  hunk review (``Agent.apply_hunk_review``), M-071's edit
  formats (``Agent.apply_edit_format``), M-075's named
  checkpoints (``Agent.take_checkpoint`` /
  ``Agent.restore_checkpoint``) and M-078's auto-commit
  (``Agent.commit_accepted_edits``) — wired by the gate's
  tests, so this core module imports no service layer.

Honesty rules, enforced by the validator and pinned by tests:

* Exactly one exercise: the benchmark refactor. It is
  ``completed`` only with its evidence kind stated —
  ``agent-roads-measured``: every step rides a real Agent
  road against a real throwaway git repository, and **no
  step is faked, stubbed, or claimed beyond what the tests
  do**. The auto-commit lands on the exercise repo's own
  working branch (``feature/refactor``), never on a
  protected branch, and the campaign tree is never the
  exercise repo.
* The gate banks **zero failed applies**: the record's
  ``failed_applies`` must be 0 and its ``attempted_applies``
  must count the refactor's real applies (2 — one
  hunk-reviewed unified diff, one search-and-replace).
* Hunk review must be genuinely used both ways: at least
  one hunk accepted and at least one rejected, the rejected
  hunk's change named and proven absent from the file.
* The baseline section must close arithmetically: the
  M-093 confirmation suite's counted totals (4811
  collected, 4808 passed, 2 failed — the two long-classified
  environment cases — 1 skipped).
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
    "verify_refactor",
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
GATE_RESOURCE = "part4_gate.yaml"

#: The only schema this loader accepts.
GATE_SCHEMA = "mythic.part4_gate/1"

#: The slice that owns this gate.
GATE_SLICE = "M-094"

#: The gate's exercises, in roadmap order.
EXERCISE_IDS = ("refactor",)

#: Evidence kinds an exercise may honestly claim.
EVIDENCE_KINDS = ("agent-roads-measured",)

_ID_RE = re.compile(r"^M-\d{3}$")


@dataclass(frozen=True)
class SliceRef:
    """One Part IV slice the gate closes over."""

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
    """The validated Part IV gate record."""

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
        """The gated slices, in road order (M-071..M-093)."""
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
        """The M-093 baseline: collected/passed/failed/skipped."""
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


def verify_refactor(exercise: Exercise, root: Path) -> List[str]:
    """Problems with the refactor of *exercise*'s repo at *root*.

    An empty list means the refactor truly landed: the old
    name appears in no seed source file, the new name
    appears in every seed source file, and the rejected
    hunk's change is absent from the file it targeted —
    judged from the files themselves.
    """
    old = exercise.details.get("old_name")
    new = exercise.details.get("new_name")
    rejected = exercise.details.get("rejected_marker")
    problems: List[str] = []
    if not isinstance(old, str) or not old or not isinstance(new, str) \
            or not new:
        return ["the refactor exercise names no old/new name to verify"]
    for seed in exercise.seed_files:
        if not seed.path.endswith(".py"):
            continue
        target = root / seed.path
        if not target.is_file():
            problems.append(f"{seed.path}: missing after the refactor")
            continue
        text = target.read_text(encoding="utf-8")
        if old in text:
            problems.append(
                f"{seed.path}: the old name {old!r} is still present")
        if new not in text:
            problems.append(
                f"{seed.path}: the new name {new!r} is absent")
    if isinstance(rejected, str) and rejected:
        pricing = root / "pricing.py"
        if pricing.is_file() and rejected in pricing.read_text(
                encoding="utf-8"):
            problems.append(
                f"pricing.py: the rejected hunk's change {rejected!r} "
                "landed — hunk review was not honoured")
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
    if data.get("part") != 4:
        problems.append(f"part must be 4, got {data.get('part')!r}")
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
        if baseline.get("resource") != "m093_confirmation_suite":
            problems.append(
                "baseline.resource must be 'm093_confirmation_suite', got "
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
    if len(slices) != 23:
        problems.append(
            f"slices must number exactly 23 (M-071..M-093), got {len(slices)}")
    for position, ref in enumerate(slices, start=71):
        if not isinstance(ref, dict):
            problems.append(f"slice entry is not a mapping: {ref!r}")
            continue
        sid = ref.get("slice")
        expected = f"M-{position:03d}"
        if not isinstance(sid, str) or not _ID_RE.match(sid):
            problems.append(f"slice {sid!r}: slice must look like 'M-071'")
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
                and "M-071" <= s <= "M-093" for s in owning):
            problems.append(
                f"exercise {eid}: owning_slices must name Part IV slices")
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
        if eid == "refactor":
            if exercise.get("attempted_applies") != 2:
                problems.append(
                    "exercise refactor: attempted_applies must be 2 (one "
                    "hunk-reviewed diff, one search-and-replace), got "
                    f"{exercise.get('attempted_applies')!r}")
            if exercise.get("failed_applies") != 0:
                problems.append(
                    "exercise refactor: failed_applies must be 0 — the "
                    "gate banks zero failed applies, got "
                    f"{exercise.get('failed_applies')!r}")
            proposed = exercise.get("hunks_proposed")
            accepted = exercise.get("hunks_accepted")
            rejected_n = exercise.get("hunks_rejected")
            if not all(isinstance(v, int) for v in
                       (proposed, accepted, rejected_n)):
                problems.append(
                    "exercise refactor: hunk counts must be integers")
            else:
                if accepted + rejected_n != proposed:
                    problems.append(
                        "exercise refactor: accepted + rejected hunks "
                        f"must equal the proposed hunks, got {accepted} + "
                        f"{rejected_n} != {proposed}")
                if accepted < 1 or rejected_n < 1:
                    problems.append(
                        "exercise refactor: hunk review must be used "
                        "both ways — at least one hunk accepted and at "
                        "least one rejected")
            for key in ("checkpoint_name", "commit_branch",
                        "rejected_marker"):
                if not isinstance(exercise.get(key), str) \
                        or not exercise[key]:
                    problems.append(
                        f"exercise refactor: {key} must be non-empty")
            py_seeds = [s for s in seeds if isinstance(s, dict)
                        and str(s.get("path", "")).endswith(".py")]
            if len(py_seeds) != 2:
                problems.append(
                    "exercise refactor: seed source files must number "
                    f"exactly 2 (the refactor reaches across both), "
                    f"got {len(py_seeds)}")
            old, new = exercise.get("old_name"), exercise.get("new_name")
            if not old or not new or old == new:
                problems.append(
                    "exercise refactor: old_name and new_name must differ")
            elif seeds and not all(
                    isinstance(s, dict) and old in str(s.get("content", ""))
                    for s in seeds if str(s.get("path", "")).endswith(".py")):
                problems.append(
                    "exercise refactor: the old name must appear in "
                    "every seed source file — a rename with a one-file "
                    "reach is not a refactor")
            for key in ("diff_payload", "search_payload"):
                if not isinstance(exercise.get(key), str) \
                        or not exercise[key]:
                    problems.append(
                        f"exercise refactor: {key} must be non-empty — "
                        "the gate carries the exact payloads it applies")
    return problems


_DETAIL_KEYS = (
    "old_name", "new_name", "attempted_applies", "failed_applies",
    "hunks_proposed", "hunks_accepted", "hunks_rejected",
    "checkpoint_name", "commit_branch", "rejected_marker",
    "diff_payload", "search_payload")


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
    """Load and validate the shipped Part IV gate (or *data*)."""
    raw = data if data is not None else load_resource(GATE_RESOURCE)
    problems = validate_gate(raw)
    if problems:
        raise ValidationError(
            "part IV gate failed validation: " + "; ".join(problems))
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
        "# Part IV Gate — The Editor's Hand (M-094)",
        "",
        f"*Gate slice {gate.gate_slice}, part {gate.part} — "
        f"{gate.part_title}. Verdict: **{gate.verdict}**.*",
        "",
        gate.gate_note,
        "",
        f"**Slices gated:** {len(gate.slice_ids())} "
        f"({gate.slice_ids()[0]}..{gate.slice_ids()[-1]}).",
        "",
        f"**Baseline (M-093 confirmation suite, "
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
    ]
    return "\n".join(lines)
