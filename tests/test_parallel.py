"""Tests for parallel tool execution with dependency ordering (Slice 17)."""

import time

import pytest

from mythic_agent.agents.parallel import (
    DependencyError,
    ParallelExecutor,
    ToolCall,
    ToolResult,
    referenced_ids,
)


def _fake_executor(record=None, delay=0.0):
    """Build an execute callable that echoes the call and records order."""
    def execute(call: ToolCall) -> ToolResult:
        if record is not None:
            record.append(call.name)
        if delay:
            time.sleep(delay)
        return ToolResult(call=call, output=f"result-of-{call.name}")
    return execute


def test_independent_calls_run_in_parallel():
    executor = ParallelExecutor(max_workers=4,
                                execute=_fake_executor(delay=0.2))
    calls = [ToolCall(name=f"tool-{i}", arguments={"n": i}) for i in range(4)]
    start = time.monotonic()
    results = executor.execute_all(calls)
    elapsed = time.monotonic() - start
    assert elapsed < 0.6  # serial would take 0.8s
    assert [r.call.name for r in results] == [f"tool-{i}" for i in range(4)]
    assert all(r.ok for r in results)


def test_results_returned_in_input_order():
    completions = []

    def execute(call: ToolCall) -> ToolResult:
        # Later calls finish first, so completion order differs from input order.
        time.sleep(0.05 * (3 - int(call.name.rsplit("-", 1)[1])))
        completions.append(call.name)
        return ToolResult(call=call, output=call.name)

    executor = ParallelExecutor(max_workers=4, execute=execute)
    calls = [ToolCall(name=f"t-{i}") for i in range(3)]
    results = executor.execute_all(calls)
    assert [r.call.name for r in results] == ["t-0", "t-1", "t-2"]
    assert completions != ["t-0", "t-1", "t-2"]  # finished out of order


def test_dependency_runs_sequentially_with_resolved_output():
    record = []

    def execute(call: ToolCall) -> ToolResult:
        record.append(call.name)
        if call.name == "list":
            return ToolResult(call=call, output="alpha,beta")
        return ToolResult(call=call, output=f"saw[{call.arguments['items']}]")

    calls = [
        ToolCall(name="list", id="list", arguments={}),
        ToolCall(name="process", id="process",
                 arguments={"items": "${list.output}"}),
    ]
    executor = ParallelExecutor(execute=execute)
    results = executor.execute_all(calls)
    assert record == ["list", "process"]
    by_id = {r.call.id: r for r in results}
    assert by_id["process"].output == "saw[alpha,beta]"
    assert by_id["process"].ok


def test_chained_dependencies_execute_in_order():
    record = []

    def execute(call: ToolCall) -> ToolResult:
        record.append(call.name)
        return ToolResult(call=call, output=f"out-{call.name}")

    calls = [
        ToolCall(name="third", id="c3", arguments={"v": "${c2.output}"}),
        ToolCall(name="first", id="c1", arguments={}),
        ToolCall(name="second", id="c2", arguments={"v": "${c1.output}"}),
    ]
    results = ParallelExecutor(execute=execute).execute_all(calls)
    assert record == ["first", "second", "third"]
    # Input order preserved in results even though execution was reordered.
    assert [r.call.id for r in results] == ["c3", "c1", "c2"]
    assert results[0].output == "out-third"


def test_unknown_reference_raises_dependency_error():
    calls = [ToolCall(name="x", id="a", arguments={"v": "${ghost.output}"})]
    with pytest.raises(DependencyError, match="unknown"):
        ParallelExecutor(execute=_fake_executor()).execute_all(calls)


def test_circular_dependency_raises():
    calls = [
        ToolCall(name="x", id="a", arguments={"v": "${b.output}"}),
        ToolCall(name="y", id="b", arguments={"v": "${a.output}"}),
    ]
    with pytest.raises(DependencyError, match="[Cc]ircular"):
        ParallelExecutor(execute=_fake_executor()).execute_all(calls)


def test_self_dependency_raises():
    calls = [ToolCall(name="x", id="a", arguments={"v": "${a.output}"})]
    with pytest.raises(DependencyError, match="itself"):
        ParallelExecutor(execute=_fake_executor()).execute_all(calls)


def test_duplicate_ids_raise():
    calls = [ToolCall(name="x", id="dup"), ToolCall(name="y", id="dup")]
    with pytest.raises(DependencyError, match="[Dd]uplicate"):
        ParallelExecutor(execute=_fake_executor()).execute_all(calls)


def test_tool_exception_becomes_failed_result_not_crash():
    def execute(call: ToolCall) -> ToolResult:
        if call.name == "bad":
            raise RuntimeError("boom")
        return ToolResult(call=call, output="fine")

    calls = [ToolCall(name="bad", id="bad"), ToolCall(name="good", id="good")]
    results = ParallelExecutor(execute=execute).execute_all(calls)
    by_id = {r.call.id: r for r in results}
    assert by_id["bad"].ok is False
    assert "boom" in (by_id["bad"].error or "")
    assert by_id["good"].ok is True


def test_auto_generated_ids_are_unique_and_referenced():
    calls = [
        ToolCall(name="first"),
        ToolCall(name="second", arguments={"v": "${call-0.output}"}),
    ]
    results = ParallelExecutor(execute=_fake_executor()).execute_all(calls)
    assert len({r.call.id for r in results}) == 2
    assert results[1].ok


def test_referenced_ids_detects_placeholders():
    call = ToolCall(name="x", arguments={"a": "${one.output}", "b": ["${two.output}"]})
    assert referenced_ids(call) == {"one", "two"}
    assert referenced_ids(ToolCall(name="y", arguments={"a": "plain"})) == set()


def test_empty_call_list_returns_empty():
    assert ParallelExecutor(execute=_fake_executor()).execute_all([]) == []


def test_max_workers_default_and_configurable():
    assert ParallelExecutor(execute=_fake_executor()).max_workers == 4
    assert ParallelExecutor(max_workers=8, execute=_fake_executor()).max_workers == 8
    with pytest.raises(ValueError):
        ParallelExecutor(max_workers=0, execute=_fake_executor())
