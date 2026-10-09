"""Tests for the Mythic Engineering slice runner (S12)."""

import json
import sys

import pytest

from mythic_agent.core import config_manager as cm_module
from mythic_agent.workflow import (
    CheckpointError,
    GateResult,
    SliceDefinition,
    SliceResult,
    SliceRunner,
)


@pytest.fixture
def runner(tmp_path, monkeypatch):
    """SliceRunner whose checkpoints live in a throwaway directory."""
    state = tmp_path / "mythic-state"
    monkeypatch.setattr(cm_module.config_manager, "MYTHIC_DIR", state)
    return SliceRunner()


def _def(name="slice-x", gates=("true", "true"), **kwargs):
    return SliceDefinition(
        name=name,
        description="test slice",
        acceptance_gates=list(gates),
        **kwargs,
    )


def test_successful_run(runner, tmp_path):
    checkpoint = tmp_path / "mythic-state" / "slices" / "slice-x.json"
    result = runner.run(_def())
    assert isinstance(result, SliceResult)
    assert result.success is True
    assert result.total_gates == 2
    assert result.completed_gates == 2
    assert len(result.gate_results) == 2
    assert all(g.passed for g in result.gate_results)
    assert checkpoint.exists()
    payload = json.loads(checkpoint.read_text())
    assert payload["complete"] is True
    assert payload["completed_gates"] == 2


def test_failed_gate_stops_execution(runner):
    result = runner.run(_def(gates=("true", "exit 3", "true")))
    assert result.success is False
    # Third gate must never have run; completed_gates counts the last
    # successfully completed gate so resume() re-attempts the failed one.
    assert len(result.gate_results) == 2
    assert result.completed_gates == 1
    assert [g.passed for g in result.gate_results] == [True, False]
    assert result.gate_results[1].returncode == 3
    assert "STOPPED at gate 2/3" in result.log


def test_gate_result_captures_output(runner):
    result = runner.run(_def(gates=("echo hello-stdout", "echo boom 1>&2; exit 1")))
    assert result.success is False
    first, second = result.gate_results
    assert isinstance(first, GateResult)
    assert "hello-stdout" in first.stdout
    assert "boom" in second.stderr
    assert second.command == "echo boom 1>&2; exit 1"


def test_checkpoint_written_after_each_gate(runner, tmp_path):
    result = runner.run(_def(name="gated", gates=("true", "exit 7")))
    payload = json.loads(
        (tmp_path / "mythic-state" / "slices" / "gated.json").read_text()
    )
    assert payload["definition"]["acceptance_gates"] == ["true", "exit 7"]
    # Gate 1 passed, gate 2 failed: last completed gate is 1, so resume()
    # will re-attempt the failed gate.
    assert payload["completed_gates"] == 1
    assert payload["complete"] is False
    assert len(payload["gate_results"]) == 2


def test_resume_after_failure(runner, tmp_path):
    """A failing gate that is fixed externally passes on resume."""
    marker = tmp_path / "marker.txt"
    gate = (
        f"{sys.executable} -c "
        f"\"import sys, pathlib; p = pathlib.Path(r'{marker}'); "
        f"sys.exit(0 if p.exists() else 1)\""
    )
    definition = _def(name="resumable", gates=("true", gate, "true"))

    first = runner.run(definition)
    assert first.success is False
    assert first.completed_gates == 1

    # External fix: the gate's precondition is now satisfied.
    marker.touch()
    resumed = runner.resume("resumable")
    assert resumed.success is True
    assert resumed.completed_gates == 3
    # Gate 1 was not re-executed; the failed gate 2 was re-attempted and its
    # full history is preserved: [g1, g2-fail, g2-pass, g3].
    assert len(resumed.gate_results) == 4
    assert [g.index for g in resumed.gate_results] == [0, 1, 1, 2]
    assert [g.passed for g in resumed.gate_results] == [True, False, True, True]
    assert "[gate 1/3] $ true" in resumed.log  # prior log preserved


def test_resume_completed_slice_returns_stored_result(runner, tmp_path):
    counter = tmp_path / "count.txt"
    gate = f"echo run >> {counter}"
    runner.run(_def(name="done", gates=(gate,)))
    assert counter.read_text().count("run") == 1
    resumed = runner.resume("done")
    assert resumed.success is True
    # No gates re-executed.
    assert counter.read_text().count("run") == 1
    assert "COMPLETE" in resumed.log


def test_resume_unknown_slice_raises(runner):
    with pytest.raises(CheckpointError, match="No checkpoint"):
        runner.resume("no-such-slice")


def test_resume_corrupted_checkpoint_raises(runner, tmp_path):
    path = tmp_path / "mythic-state" / "slices" / "broken.json"
    path.parent.mkdir(parents=True)
    path.write_text("{not valid json")
    with pytest.raises(CheckpointError, match="corrupted"):
        runner.resume("broken")


def test_gate_timeout_fails_gate(runner):
    definition = _def(gates=("sleep 30",))
    result = runner.run(definition, timeout=0.3)
    assert result.success is False
    assert result.gate_results[0].returncode == 124
    assert "TIMEOUT" in result.gate_results[0].stderr


def test_work_order_path_sets_gate_cwd(runner, tmp_path):
    order = tmp_path / "work-order.md"
    order.write_text("# work order")
    definition = _def(
        gates=("pwd",), work_order_path=str(order), name="cwd-slice"
    )
    result = runner.run(definition)
    assert result.success is True
    assert tmp_path.as_posix() in result.gate_results[0].stdout
