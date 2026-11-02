"""
TIER: unit
Baseline Freeze gate (All-Features roadmap slice M-007).

The shipped freeze (``mythic_agent/data/baseline_freeze.yaml``) is
the "before" evidence for Part XI: the full-suite count with every
counted failure named and classified, a startup profile with at
least three real timed runs and their context, and the scripted
end-to-end steps the recording script (``scripts/baseline_e2e.py``)
asserts. The recording itself is re-run here, live, so the frozen
steps are proven — not merely described.
"""

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from mythic_agent.core.baseline_freeze import (
    BaselineFreeze,
    load_freeze,
    render_markdown,
    validate_freeze,
)
from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def freeze() -> BaselineFreeze:
    return load_freeze()


def test_shipped_freeze_loads_and_validates(freeze):
    assert isinstance(freeze, BaselineFreeze)
    assert validate_freeze(load_resource("baseline_freeze.yaml")) == []
    assert freeze.frozen and freeze.base_commit


def test_suite_arithmetic_closes(freeze):
    collected, passed, failed, skipped = freeze.suite_totals()
    assert passed + failed + skipped == collected
    assert collected > 1000  # the freeze is the real full suite, not a subset


def test_every_counted_failure_is_named_and_classified(freeze):
    assert len(freeze.known_failures) == freeze.suite.failed
    assert len(freeze.failure_names()) == len(set(freeze.failure_names()))
    for _name, classification, explanation in freeze.known_failures:
        assert classification.strip() and explanation.strip()


def test_startup_profile_has_real_runs(freeze):
    runs = freeze.startup.runs_s
    assert len(runs) >= 3
    assert all(r > 0 for r in runs)
    assert freeze.startup.median_s() == sorted(runs)[len(runs) // 2] or len(runs) % 2 == 0
    assert freeze.startup.context.strip()


def test_e2e_steps_are_sequential(freeze):
    assert [s.id for s in freeze.e2e_steps] == [
        f"E-{n:02d}" for n in range(1, len(freeze.e2e_steps) + 1)
    ]
    for step in freeze.e2e_steps:
        assert step.command.strip() and step.expected.strip()


def test_e2e_script_exists_and_is_stdlib_only(freeze):
    script = REPO_ROOT / freeze.e2e_script
    assert script.exists()
    assert "ThreadingHTTPServer" in script.read_text(encoding="utf-8")


def test_e2e_recording_actually_passes(freeze):
    """The frozen steps, re-run live against the loopback fixture."""
    script = REPO_ROOT / freeze.e2e_script
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True, text=True, timeout=300, cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["all_passed"] is True
    assert [s["id"] for s in report["steps"]] == [s.id for s in freeze.e2e_steps]
    assert all(s["passed"] for s in report["steps"])


def test_render_covers_suite_failures_and_steps(freeze):
    text = render_markdown(freeze)
    assert str(freeze.suite.passed) in text
    for name in freeze.failure_names():
        assert name in text
    for step in freeze.e2e_steps:
        assert step.id in text and step.name in text
    assert str(freeze.startup.median_s()) in text


def _tampered(mutator):
    data = copy.deepcopy(load_resource("baseline_freeze.yaml"))
    mutator(data)
    return data


def test_validation_rejects_broken_suite_arithmetic():
    data = _tampered(lambda d: d["suite"].update(passed=d["suite"]["passed"] + 1))
    problems = validate_freeze(data)
    assert any("arithmetic" in p for p in problems)
    with pytest.raises(ValidationError):
        load_freeze(data)


def test_validation_rejects_an_unnamed_failure():
    data = _tampered(lambda d: d["known_failures"].pop())
    problems = validate_freeze(data)
    assert any("name every counted failure" in p for p in problems)


def test_validation_rejects_an_unclassified_failure():
    data = _tampered(lambda d: d["known_failures"][0].update(classification=""))
    problems = validate_freeze(data)
    assert any("classification must be non-empty" in p for p in problems)


def test_validation_rejects_a_thin_startup_profile():
    data = _tampered(lambda d: d["startup"].update(runs_s=[0.5]))
    problems = validate_freeze(data)
    assert any("at least three" in p for p in problems)


def test_validation_rejects_a_step_numbering_gap():
    data = _tampered(lambda d: d["e2e_steps"][1].update(id="E-09"))
    problems = validate_freeze(data)
    assert any("sequential" in p for p in problems)
