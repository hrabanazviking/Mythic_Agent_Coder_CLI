"""The Part II gate (All-Features roadmap slice M-042).

Part II — The Provider Ocean — closes here. The roadmap's gate
words: *the same benchmark task (M-008) completed through five
different providers + Ollama + Aesir, evidence banked.*

The fixed task is B-01 (the one-based pagination bugfix): one
seed file, one solution file, and four hidden grading tests.
This module is the gate's machinery:

* A validated gate record
  (``mythic_agent/data/part2_gate.yaml``) naming the seven
  doors, the Part II slices it closes over (M-019..M-041), and
  every other registry entry it honestly does **not** claim.
* The completion runner the gate's tests exercise live: a
  task prompt built from the pack (prompt + seed contents) is
  sent through a shipped adapter's ``chat()``, the reply is
  reduced to code (:func:`extract_code` — a fenced block when
  the reply fences one, else the reply itself), the code is
  materialised over the task's seed repo, and the task's own
  hidden grading tests are run in a subprocess
  (:func:`grade_materialised`). A door *completes* the task
  only when every grading test passes.

Honesty rules, enforced by the validator and pinned by tests:

* Exactly seven named doors, in roadmap order: five
  OpenAI-compatible providers, then Ollama, then Aesir. Each
  door's dialect and road are stated and cross-checked
  against the live registry by the gate's tests.
* Every named door's evidence kind is ``loopback-measured``:
  the completion is proven over loopback through the shipped
  adapter against a scripted door answering with the
  reference solution, as a real model door would. **No live
  vendor service is claimed** — each door records its live
  status as ``not-proven`` with the reason.
* Every registry entry that is not a named door is recorded
  ``not-proven`` with its reason; the gate claims no
  benchmark completion for it.
* The verdict is ``PASS`` and the validator accepts no other
  verdict: a gate that has failed is a defect to fix, not a
  record.
"""

from __future__ import annotations

__all__ = [
    "GATE_RESOURCE",
    "GATE_SCHEMA",
    "GATE_SLICE",
    "ROADS",
    "STATUSES",
    "Any",
    "BenchmarkTask",
    "Completion",
    "Dict",
    "Door",
    "Gate",
    "List",
    "Optional",
    "SliceRef",
    "Tuple",
    "Unproven",
    "extract_code",
    "grade_materialised",
    "load_gate",
    "prompt_for_task",
    "render_markdown",
    "run_completion",
    "validate_gate",
]

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .benchmark_tasks import BenchmarkTask, materialize
from .validation import ValidationError

#: Resource name of the gate data file inside ``mythic_agent/data``.
GATE_RESOURCE = "part2_gate.yaml"

#: The only schema this loader accepts.
GATE_SCHEMA = "mythic.part2_gate/1"

#: The slice that owns this gate.
GATE_SLICE = "M-042"

#: The adapter roads a named door may be proven through.
ROADS = ("universal_adapter", "ollama_adapter", "aesir_adapter")

#: Door / unproven statuses the gate knows.
STATUSES = ("completed", "not-proven")

_ID_RE = re.compile(r"^M-\d{3}$")
_FENCE_RE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL)


@dataclass(frozen=True)
class SliceRef:
    """One Part II slice the gate closes over."""

    slice: str
    title: str


@dataclass(frozen=True)
class Door:
    """One named door's banked completion evidence."""

    provider: str
    dialect: str
    road: str
    status: str
    evidence_kind: str
    grading_passed: int
    grading_total: int
    live_status: str
    live_reason: str
    evidence: str


@dataclass(frozen=True)
class Unproven:
    """One registry entry the gate honestly does not claim."""

    provider: str
    dialect: str
    status: str
    reason: str


@dataclass(frozen=True)
class Gate:
    """The validated Part II gate record."""

    gate_slice: str
    part: int
    part_title: str
    verdict: str
    gate_note: str
    task_id: str
    task_title: str
    task_category: str
    grading_total: int
    solution_files: Tuple[str, ...]
    slices: Tuple[SliceRef, ...]
    doors: Tuple[Door, ...]
    unproven: Tuple[Unproven, ...]

    def slice_ids(self) -> Tuple[str, ...]:
        """The gated slices, in road order (M-019..M-041)."""
        return tuple(s.slice for s in self.slices)

    def door_names(self) -> Tuple[str, ...]:
        """The named doors, in gate order."""
        return tuple(d.provider for d in self.doors)

    def completed_doors(self) -> Tuple[Door, ...]:
        """Every door whose completion the gate banks."""
        return tuple(d for d in self.doors if d.status == "completed")

    def compatible_doors(self) -> Tuple[Door, ...]:
        """The named doors proven through the universal adapter."""
        return tuple(d for d in self.doors if d.road == "universal_adapter")

    def unproven_names(self) -> Tuple[str, ...]:
        """Every registry entry the gate does not claim, in order."""
        return tuple(u.provider for u in self.unproven)


@dataclass(frozen=True)
class Completion:
    """One live completion run's outcome for one door."""

    provider: str
    passed: int
    total: int

    @property
    def completed(self) -> bool:
        """True only when every grading test passed."""
        return self.total > 0 and self.passed == self.total


def extract_code(reply: str) -> str:
    """Reduce a model *reply* to the code it carries.

    A fenced block (``` or ```python) yields its contents;
    anything else is taken as the code itself, stripped. An
    empty reply yields an empty string — grading, not this
    function, judges it.
    """
    text = (reply or "").strip()
    match = _FENCE_RE.search(text)
    if match:
        return match.group(1).strip() + "\n"
    return text + ("\n" if text else "")


def prompt_for_task(task: BenchmarkTask) -> str:
    """The one prompt every gate door receives for *task*.

    The task's own prompt, then each seed file's contents —
    exactly what a coding session would put before the model.
    The reply is expected to be the corrected file's full
    contents (see :func:`extract_code`).
    """
    parts = [task.prompt, ""]
    for repo_file in task.seed_files:
        parts.append(f"File {repo_file.path}:")
        parts.append(repo_file.content)
    parts.append(
        "Reply with the corrected file's full contents only.")
    return "\n".join(parts)


def grade_materialised(task: BenchmarkTask, code: str,
                       root: Path) -> Tuple[int, int]:
    """Materialise *code* over *task*'s seed and grade it.

    The seed repo is written under *root*, the code replaces
    the task's (single) solution file, and the task's hidden
    grading tests run in a subprocess
    (``python -m pytest -q test_grading.py``). Returns
    ``(passed, total)`` where total counts the grading
    module's own ``def test_`` functions; a grading run that
    cannot even collect counts as zero passed, never as a
    pass.
    """
    total = task.grading_tests.count("def test_")
    if len(task.solution_files) != 1:
        return 0, total
    materialize(task, root, solved=False)
    target = root / task.solution_files[0].path
    target.write_text(code, encoding="utf-8")
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             "test_grading.py"],
            cwd=str(root), capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return 0, total
    match = re.search(r"(\d+) passed", proc.stdout)
    passed = int(match.group(1)) if match else 0
    if proc.returncode != 0:
        # A failing run's "N passed" is partial credit only when
        # it is real; completion requires the full count, which
        # run_completion / the validator compare exactly.
        return min(passed, total), total
    return passed, total


def run_completion(provider: str, adapter: Any, task: BenchmarkTask,
                   root: Path) -> Completion:
    """Run *task* through *adapter* and grade the reply.

    *adapter* is any shipped provider adapter (duck-typed on
    its ``chat(messages) -> str`` protocol — constructed by
    the caller through the door's own road, so this core
    module imports no provider package). The reply is
    materialised and graded by :func:`grade_materialised`.
    """
    reply = adapter.chat(
        [{"role": "user", "content": prompt_for_task(task)}])
    passed, total = grade_materialised(task, extract_code(reply), root)
    return Completion(provider=provider, passed=passed, total=total)


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
    if data.get("part") != 2:
        problems.append(f"part must be 2, got {data.get('part')!r}")
    if data.get("verdict") != "PASS":
        problems.append(
            "verdict must be 'PASS' (a failed gate is a defect, not a "
            f"record), got {data.get('verdict')!r}")
    for key in ("part_title", "gate_note"):
        if not isinstance(data.get(key), str) or not data[key]:
            problems.append(f"{key} must be a non-empty string")

    task = data.get("benchmark_task")
    grading_total: Optional[int] = None
    if not isinstance(task, dict):
        problems.append("benchmark_task must be a mapping")
    else:
        if task.get("id") != "B-01":
            problems.append(
                f"benchmark_task.id must be 'B-01', got {task.get('id')!r}")
        for key in ("title", "category"):
            if not isinstance(task.get(key), str) or not task[key]:
                problems.append(f"benchmark_task.{key} must be non-empty")
        grading_total = task.get("grading_tests")
        if not isinstance(grading_total, int) or grading_total <= 0:
            problems.append("benchmark_task.grading_tests must be a positive int")
            grading_total = None
        sols = task.get("solution_files")
        if (not isinstance(sols, list) or len(sols) != 1
                or not all(isinstance(s, str) and s for s in sols)):
            problems.append("benchmark_task.solution_files must list exactly one file")

    slices = data.get("slices")
    if not isinstance(slices, list) or not slices:
        problems.append("slices must be a non-empty list")
        slices = []
    if len(slices) != 23:
        problems.append(
            f"slices must number exactly 23 (M-019..M-041), got {len(slices)}")
    for position, ref in enumerate(slices, start=19):
        if not isinstance(ref, dict):
            problems.append(f"slice entry is not a mapping: {ref!r}")
            continue
        sid = ref.get("slice")
        expected = f"M-{position:03d}"
        if not isinstance(sid, str) or not _ID_RE.match(sid):
            problems.append(f"slice {sid!r}: slice must look like 'M-019'")
        elif sid != expected:
            problems.append(
                f"slice {sid}: slices must be sequential, expected {expected}")
        if not isinstance(ref.get("title"), str) or not ref["title"]:
            problems.append(f"slice {sid}: title must be non-empty")

    doors = data.get("doors")
    if not isinstance(doors, list) or not doors:
        problems.append("doors must be a non-empty list")
        doors = []
    if len(doors) != 7:
        problems.append(
            "doors must number exactly 7 (five providers + Ollama + "
            f"Aesir), got {len(doors)}")
    roads_seen: List[str] = []
    for door in doors:
        if not isinstance(door, dict):
            problems.append(f"door entry is not a mapping: {door!r}")
            continue
        name = door.get("provider")
        if not isinstance(name, str) or not name:
            problems.append("door provider must be a non-empty string")
        if door.get("road") not in ROADS:
            problems.append(
                f"door {name}: road must be one of {ROADS}, "
                f"got {door.get('road')!r}")
        else:
            roads_seen.append(door["road"])
        if door.get("status") != "completed":
            problems.append(
                f"door {name}: status must be 'completed', "
                f"got {door.get('status')!r}")
        if door.get("evidence_kind") != "loopback-measured":
            problems.append(
                f"door {name}: evidence_kind must be 'loopback-measured' "
                "(no live vendor call is claimed by this gate), got "
                f"{door.get('evidence_kind')!r}")
        if door.get("live_status") != "not-proven":
            problems.append(
                f"door {name}: live_status must be 'not-proven' (the "
                "gate proves completion over loopback, never a live "
                f"vendor call), got {door.get('live_status')!r}")
        for key in ("dialect", "live_reason", "evidence"):
            if not isinstance(door.get(key), str) or not door[key]:
                problems.append(f"door {name}: {key} must be non-empty")
        passed = door.get("grading_passed")
        total = door.get("grading_total")
        if not isinstance(passed, int) or not isinstance(total, int):
            problems.append(f"door {name}: grading counts must be integers")
        elif grading_total is not None and (
                total != grading_total or passed != total):
            problems.append(
                f"door {name}: a completed door must grade in full "
                f"({grading_total}/{grading_total}), got {passed}/{total}")
    if roads_seen:
        if roads_seen.count("universal_adapter") != 5:
            problems.append(
                "exactly five doors must ride the universal_adapter road, "
                f"got {roads_seen.count('universal_adapter')}")
        if roads_seen.count("ollama_adapter") != 1:
            problems.append("exactly one door must ride the ollama_adapter road")
        if roads_seen.count("aesir_adapter") != 1:
            problems.append("exactly one door must ride the aesir_adapter road")

    unproven = data.get("unproven_providers")
    if not isinstance(unproven, list) or not unproven:
        problems.append("unproven_providers must be a non-empty list")
        unproven = []
    door_names = {d.get("provider") for d in doors if isinstance(d, dict)}
    for entry in unproven:
        if not isinstance(entry, dict):
            problems.append(f"unproven entry is not a mapping: {entry!r}")
            continue
        name = entry.get("provider")
        if name in door_names:
            problems.append(
                f"unproven provider {name!r} is also a named door — a "
                "door cannot be both completed and not proven")
        if entry.get("status") != "not-proven":
            problems.append(
                f"unproven {name}: status must be 'not-proven', "
                f"got {entry.get('status')!r}")
        for key in ("dialect", "reason"):
            if not isinstance(entry.get(key), str) or not entry[key]:
                problems.append(f"unproven {name}: {key} must be non-empty")
    return problems


def _to_gate(data: Dict[str, Any]) -> Gate:
    task = data["benchmark_task"]
    return Gate(
        gate_slice=data["gate_slice"],
        part=data["part"],
        part_title=data["part_title"],
        verdict=data["verdict"],
        gate_note=data["gate_note"],
        task_id=task["id"],
        task_title=task["title"],
        task_category=task["category"],
        grading_total=task["grading_tests"],
        solution_files=tuple(task["solution_files"]),
        slices=tuple(
            SliceRef(slice=s["slice"], title=s["title"])
            for s in data["slices"]),
        doors=tuple(
            Door(
                provider=d["provider"], dialect=d["dialect"],
                road=d["road"], status=d["status"],
                evidence_kind=d["evidence_kind"],
                grading_passed=d["grading_passed"],
                grading_total=d["grading_total"],
                live_status=d["live_status"],
                live_reason=d["live_reason"], evidence=d["evidence"])
            for d in data["doors"]),
        unproven=tuple(
            Unproven(
                provider=u["provider"], dialect=u["dialect"],
                status=u["status"], reason=u["reason"])
            for u in data["unproven_providers"]),
    )


def load_gate(data: Optional[Dict[str, Any]] = None) -> Gate:
    """Load and validate the shipped Part II gate (or *data*)."""
    raw = data if data is not None else load_resource(GATE_RESOURCE)
    problems = validate_gate(raw)
    if problems:
        raise ValidationError(
            "part II gate failed validation: " + "; ".join(problems))
    return _to_gate(raw)  # type: ignore[arg-type]


def render_markdown(gate: Gate) -> str:
    """Render the gate as markdown: verdict, doors, honesty record.

    Built from :meth:`Gate.slice_ids`, :meth:`Gate.door_names`,
    :meth:`Gate.completed_doors`, :meth:`Gate.compatible_doors`,
    and :meth:`Gate.unproven_names`, so the rendered page itself
    is computed from the same accessors the tests pin.
    """
    lines = [
        "# Part II Gate — The Provider Ocean (M-042)",
        "",
        f"*Gate slice {gate.gate_slice}, part {gate.part} — "
        f"{gate.part_title}. Verdict: **{gate.verdict}**.*",
        "",
        gate.gate_note,
        "",
        f"**Benchmark task:** {gate.task_id} {gate.task_title} "
        f"({gate.task_category}) — {gate.grading_total} hidden "
        f"grading tests; solution file: "
        f"{', '.join(gate.solution_files)}.",
        "",
        f"**Slices gated:** {len(gate.slice_ids())} "
        f"({gate.slice_ids()[0]}..{gate.slice_ids()[-1]}).",
        "",
        "## Doors — completed (loopback-measured)",
        "",
    ]
    for door in gate.completed_doors():
        lines.append(
            f"- **{door.provider}** ({door.dialect} via {door.road}) — "
            f"grading {door.grading_passed}/{door.grading_total}: "
            f"{door.evidence} Live service: NOT PROVEN — "
            f"{door.live_reason}")
    lines += [
        "",
        f"*{len(gate.compatible_doors())} of the named doors "
        f"({', '.join(gate.door_names())}) ride the universal "
        "adapter road; Ollama and Aesir ride their own adapters.*",
        "",
        "## Not proven by this gate",
        "",
    ]
    for entry in gate.unproven:
        lines.append(f"- **{entry.provider}** ({entry.dialect}): {entry.reason}")
    lines += [
        "",
        f"*Unproven entries: {', '.join(gate.unproven_names())}.*",
        "",
    ]
    return "\n".join(lines)
