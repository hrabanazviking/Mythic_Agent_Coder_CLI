"""
TIER: unit
Benchmark Task Pack gate (All-Features roadmap slice M-008).

The shipped pack (``mythic_agent/data/benchmark_tasks.yaml``) is the
yardstick for Parts II-XI: twenty real tasks, four each of bugfix,
feature, refactor, test-writing, and docs, every one in a throwaway
repo. The pack's proven property is checked here, live, for every
task: materialise the seed repo, drop in the hidden grading tests,
and they FAIL; write the reference solution over the seed, and they
PASS. A yardstick that cannot tell solved from unsolved measures
nothing.
"""

import copy
import subprocess
import sys

import pytest

from mythic_agent.core.benchmark_tasks import (
    CATEGORIES,
    BenchmarkPack,
    load_pack,
    materialize,
    render_markdown,
    validate_pack,
)
from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource


@pytest.fixture(scope="module")
def pack() -> BenchmarkPack:
    return load_pack()


def _run_grading(root) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
         "test_grading.py"],
        capture_output=True, text=True, timeout=120, cwd=root,
    )


def test_shipped_pack_loads_and_validates(pack):
    assert isinstance(pack, BenchmarkPack)
    assert validate_pack(load_resource("benchmark_tasks.yaml")) == []
    assert pack.created


def test_pack_is_twenty_tasks_four_per_category(pack):
    assert len(pack.tasks) == 20
    assert pack.task_ids() == tuple(f"B-{n:02d}" for n in range(1, 21))
    assert pack.category_counts() == tuple((c, 4) for c in CATEGORIES)


def test_every_task_is_complete_and_materialisable(pack):
    for task in pack.tasks:
        assert task.prompt.strip() and task.title.strip()
        assert task.seed_paths(), task.id
        assert task.solution_files, task.id
        assert "def test_" in task.grading_tests
        assert len(task.rubric) >= 2


@pytest.mark.parametrize("index", range(20))
def test_grading_fails_on_the_seed_alone(pack, tmp_path, index):
    task = pack.tasks[index]
    root = materialize(task, tmp_path / "repo", solved=False)
    result = _run_grading(root)
    assert result.returncode != 0, (
        f"{task.id}: grading passed on the unsolved seed\n"
        + result.stdout + result.stderr
    )


@pytest.mark.parametrize("index", range(20))
def test_grading_passes_with_the_reference_solution(pack, tmp_path, index):
    task = pack.tasks[index]
    root = materialize(task, tmp_path / "repo", solved=True)
    result = _run_grading(root)
    assert result.returncode == 0, (
        f"{task.id}: grading failed on the reference solution\n"
        + result.stdout + result.stderr
    )


@pytest.mark.parametrize("index", [12, 13, 14, 15])  # B-13..B-16, test-writing
def test_written_solution_tests_themselves_pass(pack, tmp_path, index):
    """For test-writing tasks the solution IS a test file: it must pass."""
    task = pack.tasks[index]
    root = materialize(task, tmp_path / "repo", solved=True)
    target = task.solution_files[0].path
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", target],
        capture_output=True, text=True, timeout=120, cwd=root,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_render_covers_every_task_and_category(pack):
    text = render_markdown(pack)
    for task in pack.tasks:
        assert task.id in text and task.title in text
    for category in CATEGORIES:
        assert category in text


def _tampered(mutator):
    data = copy.deepcopy(load_resource("benchmark_tasks.yaml"))
    mutator(data)
    return data


def test_validation_rejects_a_missing_task():
    data = _tampered(lambda d: d["tasks"].pop())
    problems = validate_pack(data)
    assert any("exactly 20" in p for p in problems)
    with pytest.raises(ValidationError):
        load_pack(data)


def test_validation_rejects_a_category_imbalance():
    data = _tampered(lambda d: d["tasks"][0].update(category="docs"))
    problems = validate_pack(data)
    assert any("exactly 4" in p for p in problems)


def test_validation_rejects_an_unsafe_path():
    def mutate(d):
        d["tasks"][0]["seed_files"][0]["path"] = "../escape.py"

    problems = validate_pack(_tampered(mutate))
    assert any("repo-relative" in p for p in problems)


def test_validation_rejects_empty_grading_tests():
    data = _tampered(lambda d: d["tasks"][0].update(grading_tests=""))
    problems = validate_pack(data)
    assert any("grading_tests" in p for p in problems)


def test_validation_rejects_a_thin_rubric():
    data = _tampered(lambda d: d["tasks"][0].update(rubric=["only one"]))
    problems = validate_pack(data)
    assert any("rubric" in p for p in problems)


def test_validation_rejects_a_gap_in_task_ids():
    data = _tampered(lambda d: d["tasks"][1].update(id="B-09"))
    problems = validate_pack(data)
    assert any("sequential" in p for p in problems)
