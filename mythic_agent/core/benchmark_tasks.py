"""The Benchmark Task Pack v1 (All-Features roadmap slice M-008).

Twenty real tasks — four each of bugfix, feature, refactor,
test-writing, and docs — each in its own throwaway repo. This pack is
the yardstick every later part is measured with: Part II's gate
(M-042) runs one of these tasks through five providers plus Ollama
plus Aesir, and Part XI's harness (M-255) automates the whole pack.

Data lives in ``mythic_agent/data/benchmark_tasks.yaml``. Every task
carries its seed repo (the files the throwaway repo starts with), a
reference solution (files written over the seed), hidden grading
tests (a pytest module the harness drops into the repo), and a diff
review rubric. This module loads, validates, and renders the pack.

Validation enforces the yardstick's honesty rules:

* Exactly twenty tasks, ids ``B-01``..``B-20`` sequential, titles
  unique — a benchmark that silently loses a task measures nothing.
* The five roadmap categories, exactly four tasks each.
* Every file path is repo-relative and safe (no absolute paths, no
  ``..``), no path repeats inside one file list, and every file's
  content is non-empty — a throwaway repo must be materialisable
  exactly as written.
* The grading tests are a real pytest module (they define tests),
  and the rubric carries at least two review criteria — grading is
  tests *plus* diff review, per M-255's charge.
"""

from __future__ import annotations

__all__ = [
    "CATEGORIES",
    "PACK_RESOURCE",
    "PACK_SCHEMA",
    "TASK_COUNT",
    "Any",
    "BenchmarkPack",
    "BenchmarkTask",
    "Dict",
    "List",
    "Optional",
    "RepoFile",
    "Tuple",
    "load_pack",
    "materialize",
    "render_markdown",
    "validate_pack",
]

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .validation import ValidationError

#: Resource name of the pack data file inside ``mythic_agent/data``.
PACK_RESOURCE = "benchmark_tasks.yaml"

#: The only schema this loader accepts.
PACK_SCHEMA = "mythic.benchmark_tasks/1"

#: The roadmap's five task kinds for M-008, in roadmap order.
CATEGORIES = ("bugfix", "feature", "refactor", "test-writing", "docs")

#: The pack is twenty tasks: four of each category.
TASK_COUNT = 20
PER_CATEGORY = 4

_DIFFICULTIES = ("easy", "medium", "hard")
_ID_RE = re.compile(r"^B-\d{2}$")


@dataclass(frozen=True)
class RepoFile:
    """One file of a throwaway repo: a relative path and its content."""

    path: str
    content: str


@dataclass(frozen=True)
class BenchmarkTask:
    """One benchmark task: prompt, seed repo, solution, grading."""

    id: str
    title: str
    category: str
    difficulty: str
    prompt: str
    seed_files: Tuple[RepoFile, ...]
    solution_files: Tuple[RepoFile, ...]
    grading_tests: str
    rubric: Tuple[str, ...]

    def seed_paths(self) -> Tuple[str, ...]:
        """The seed repo's file paths, in pack order."""
        return tuple(f.path for f in self.seed_files)


@dataclass(frozen=True)
class BenchmarkPack:
    """The validated benchmark task pack."""

    created: str
    tasks: Tuple[BenchmarkTask, ...]

    def task_ids(self) -> Tuple[str, ...]:
        """Every task id, in pack order."""
        return tuple(t.id for t in self.tasks)

    def tasks_by_category(self, category: str) -> Tuple[BenchmarkTask, ...]:
        """The tasks of one category, in pack order."""
        return tuple(t for t in self.tasks if t.category == category)

    def category_counts(self) -> Tuple[Tuple[str, int], ...]:
        """(category, count) pairs in roadmap category order."""
        return tuple(
            (category, len(self.tasks_by_category(category)))
            for category in CATEGORIES
        )


def materialize(task: BenchmarkTask, root: Path, *, solved: bool = False) -> Path:
    """Write *task*'s throwaway repo under *root* and return *root*.

    The seed files are written first; with ``solved=True`` the
    reference solution files are written over them. The grading
    tests land at ``test_grading.py`` in the repo root, ready for
    ``pytest test_grading.py``. Paths were validated repo-relative
    and safe at load time, so every write stays under *root*.
    """
    root.mkdir(parents=True, exist_ok=True)
    files = list(task.seed_files)
    if solved:
        files.extend(task.solution_files)
    for repo_file in files:
        target = root / repo_file.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(repo_file.content, encoding="utf-8")
    (root / "test_grading.py").write_text(task.grading_tests, encoding="utf-8")
    return root


def _check_file_list(task_id: Any, key: str, files: Any) -> List[str]:
    problems: List[str] = []
    if not isinstance(files, list) or not files:
        return [f"task {task_id}: {key} must be a non-empty list"]
    seen: set = set()
    for entry in files:
        if not isinstance(entry, dict):
            problems.append(f"task {task_id}: {key} entry is not a mapping: {entry!r}")
            continue
        path = entry.get("path")
        if not isinstance(path, str) or not path:
            problems.append(f"task {task_id}: {key} entry has no path")
            continue
        if path.startswith("/") or ".." in Path(path).parts:
            problems.append(f"task {task_id}: {key} path {path!r} is not repo-relative and safe")
        if path in seen:
            problems.append(f"task {task_id}: {key} path {path!r} repeats")
        seen.add(path)
        if not isinstance(entry.get("content"), str) or not entry["content"]:
            problems.append(f"task {task_id}: {key} file {path!r} has empty content")
    return problems


def validate_pack(data: Any) -> List[str]:
    """Return a list of human-readable problems with pack *data*."""
    problems: List[str] = []
    if not isinstance(data, dict):
        return [f"pack root must be a mapping, got {type(data).__name__}"]
    if data.get("schema") != PACK_SCHEMA:
        problems.append(f"schema must be {PACK_SCHEMA!r}, got {data.get('schema')!r}")
    if not isinstance(data.get("created"), str) or not data["created"]:
        problems.append("created must be a non-empty string")

    tasks = data.get("tasks")
    if not isinstance(tasks, list):
        return problems + ["tasks must be a list"]
    if len(tasks) != TASK_COUNT:
        problems.append(f"pack must carry exactly {TASK_COUNT} tasks, got {len(tasks)}")

    titles: set = set()
    counts: Dict[str, int] = {category: 0 for category in CATEGORIES}
    for position, task in enumerate(tasks, start=1):
        if not isinstance(task, dict):
            problems.append(f"task is not a mapping: {task!r}")
            continue
        tid = task.get("id")
        expected = f"B-{position:02d}"
        if not isinstance(tid, str) or not _ID_RE.match(tid):
            problems.append(f"task {tid!r}: id must look like 'B-01'")
        elif tid != expected:
            problems.append(f"task {tid}: ids must be sequential, expected {expected}")
        title = task.get("title")
        if not isinstance(title, str) or not title:
            problems.append(f"task {tid}: title must be non-empty")
        elif title in titles:
            problems.append(f"task {tid}: title {title!r} is used twice")
        else:
            titles.add(title)
        category = task.get("category")
        if category not in CATEGORIES:
            problems.append(f"task {tid}: category {category!r} is not one of {CATEGORIES}")
        else:
            counts[category] += 1
        if task.get("difficulty") not in _DIFFICULTIES:
            problems.append(f"task {tid}: difficulty must be one of {_DIFFICULTIES}")
        if not isinstance(task.get("prompt"), str) or not task["prompt"]:
            problems.append(f"task {tid}: prompt must be non-empty")
        problems.extend(_check_file_list(tid, "seed_files", task.get("seed_files")))
        problems.extend(_check_file_list(tid, "solution_files", task.get("solution_files")))
        grading = task.get("grading_tests")
        if not isinstance(grading, str) or "def test_" not in grading:
            problems.append(f"task {tid}: grading_tests must be a pytest module defining tests")
        rubric = task.get("rubric")
        if (
            not isinstance(rubric, list)
            or len(rubric) < 2
            or any(not isinstance(r, str) or not r for r in rubric)
        ):
            problems.append(f"task {tid}: rubric must list at least two non-empty criteria")
    for category, count in counts.items():
        if count != PER_CATEGORY:
            problems.append(
                f"category {category!r} must carry exactly {PER_CATEGORY} tasks, got {count}"
            )
    return problems


def _to_task(raw: Dict[str, Any]) -> BenchmarkTask:
    def files(key: str) -> Tuple[RepoFile, ...]:
        return tuple(RepoFile(path=f["path"], content=f["content"]) for f in raw[key])

    return BenchmarkTask(
        id=raw["id"],
        title=raw["title"],
        category=raw["category"],
        difficulty=raw["difficulty"],
        prompt=raw["prompt"],
        seed_files=files("seed_files"),
        solution_files=files("solution_files"),
        grading_tests=raw["grading_tests"],
        rubric=tuple(raw["rubric"]),
    )


def load_pack(data: Optional[Dict[str, Any]] = None) -> BenchmarkPack:
    """Load and validate the shipped benchmark pack (or *data*).

    Raises :class:`~mythic_agent.core.validation.ValidationError`
    listing every problem when the data is not a well-formed pack.
    """
    raw = data if data is not None else load_resource(PACK_RESOURCE)
    problems = validate_pack(raw)
    if problems:
        raise ValidationError("benchmark pack failed validation: " + "; ".join(problems))
    return BenchmarkPack(
        created=raw["created"],
        tasks=tuple(_to_task(t) for t in raw["tasks"]),
    )


def render_markdown(pack: BenchmarkPack) -> str:
    """Render the pack as markdown, grouped by category.

    Built from :meth:`BenchmarkPack.task_ids`,
    :meth:`BenchmarkPack.category_counts`,
    :meth:`BenchmarkPack.tasks_by_category`, and
    :meth:`BenchmarkTask.seed_paths`, so the rendered page itself is
    computed from the same accessors the tests pin.
    """
    lines = [
        "# Benchmark Task Pack v1 — the yardstick (M-008)",
        "",
        f"*{len(pack.task_ids())} tasks ({', '.join(pack.task_ids())}), "
        f"created {pack.created}. Grading = hidden tests + diff review rubric.*",
        "",
    ]
    for category, count in pack.category_counts():
        lines.append(f"## {category} ({count})")
        lines.append("")
        for task in pack.tasks_by_category(category):
            lines.append(
                f"- {task.id} **{task.title}** ({task.difficulty}) — "
                f"seed: {', '.join(task.seed_paths())}; "
                f"rubric: {'; '.join(task.rubric)}"
            )
        lines.append("")
    return "\n".join(lines)
