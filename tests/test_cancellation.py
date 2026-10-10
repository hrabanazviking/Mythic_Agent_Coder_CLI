"""R-013 cancellation correctness: real threads, real cancel events, real time bounds.

Every test here drives an actual cancellable operation on a real thread, sets
the ``threading.Event`` mid-flight (or before/after), and asserts the
operation genuinely stops instead of merely threading the event through.
"""
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from mythic_agent.core.execution import run_cancellable_async, run_process
from mythic_agent.core.runtime import TurnCancelled


def python_command(script):
    return [sys.executable, "-u", "-c", script]


def make_agent(tmp_path, cancel):
    from mythic_agent.core.policy import ToolPolicy
    return SimpleNamespace(_cancel=cancel, tool_policy=ToolPolicy("trusted"),
                           name="TestAgent", project_root=tmp_path, config={})


# ---------------------------------------------------------------------------
# run_process
# ---------------------------------------------------------------------------

def test_run_process_cancel_midflight_stops_promptly(tmp_path):
    """A sleeping child must die promptly when cancel is set mid-flight."""
    cancel = threading.Event()
    script = "import time; print('started', flush=True); time.sleep(60)"
    outcome = {}

    def target():
        outcome["result"] = run_process(python_command(script), tmp_path,
                                        cancel=cancel, timeout=120)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    time.sleep(1.0)  # let the child actually start sleeping
    mark = time.monotonic()
    cancel.set()
    thread.join(timeout=20)
    stopped_in = time.monotonic() - mark
    assert not thread.is_alive(), "run_process ignored a mid-flight cancel"
    assert outcome["result"].status == "cancelled"
    assert "started" in outcome["result"].output, "partial output was lost on cancel"
    assert stopped_in < 10, f"cancel took {stopped_in:.2f}s for a 60s sleep"


def test_run_process_cancel_before_start_is_clean_noop(tmp_path):
    """A pre-set event must prevent the child from ever spawning."""
    cancel = threading.Event()
    cancel.set()
    marker = tmp_path / "must-not-exist.txt"
    script = f"open({str(marker)!r}, 'w').write('x')"
    started = time.monotonic()
    result = run_process(python_command(script), tmp_path, cancel=cancel, timeout=30)
    elapsed = time.monotonic() - started
    assert result.status == "cancelled"
    assert result.returncode is None
    assert not marker.exists(), "pre-cancelled run_process still spawned the child"
    assert elapsed < 5, "cancel-before-start was not immediate"


def test_run_process_cancel_after_complete_is_noop(tmp_path):
    """Setting cancel after completion must not rewrite the finished result."""
    cancel = threading.Event()
    result = run_process(python_command("print('done42')"), tmp_path,
                         cancel=cancel, timeout=30)
    cancel.set()  # too late: the process already finished
    assert result.status == "completed"
    assert result.returncode == 0
    assert "done42" in result.output


# ---------------------------------------------------------------------------
# run_cancellable_async bridge
# ---------------------------------------------------------------------------

def test_bridge_cancel_midflight_raises_turn_cancelled_promptly():
    """Bridge cancel mid-flight: TurnCancelled, fast, and the coroutine drains."""
    import asyncio
    cancel, started, cleaned = threading.Event(), threading.Event(), threading.Event()

    async def operation():
        started.set()
        try:
            await asyncio.sleep(60)
        finally:
            cleaned.set()

    outcome = {}

    def target():
        with pytest.raises(TurnCancelled):
            run_cancellable_async(operation, cancel)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    assert started.wait(5), "bridged operation never started"
    mark = time.monotonic()
    cancel.set()
    thread.join(timeout=20)
    stopped_in = time.monotonic() - mark
    assert not thread.is_alive(), "bridge ignored a mid-flight cancel"
    assert stopped_in < 5, f"bridge cancel took {stopped_in:.2f}s for a 60s sleep"
    assert cleaned.is_set(), "owned coroutine was not drained before TurnCancelled"
    assert outcome == {}


def test_bridge_cancel_before_start_never_runs_factory():
    """A pre-set event must raise before the factory is even invoked."""
    cancel = threading.Event()
    cancel.set()
    called = []

    async def operation():
        called.append(True)
        return "must-not-run"

    with pytest.raises(TurnCancelled):
        run_cancellable_async(operation, cancel)
    assert not called, "factory ran despite cancel-before-start"


def test_bridge_cancel_after_complete_is_noop():
    """Setting cancel after the value returned must not disturb the result."""

    async def operation():
        return "finished"

    cancel = threading.Event()
    assert run_cancellable_async(operation, cancel) == "finished"
    cancel.set()  # too late
    assert run_cancellable_async(operation, threading.Event()) == "finished"


# ---------------------------------------------------------------------------
# tools.execute_tool
# ---------------------------------------------------------------------------

def test_execute_tool_cancel_before_execution_raises(tmp_path):
    from mythic_agent.agents.tools import execute_tool
    cancel = threading.Event()
    cancel.set()
    agent = make_agent(tmp_path, cancel)
    with pytest.raises(TurnCancelled):
        execute_tool("read_file", {"path": "anything.txt"}, agent=agent)


def test_execute_tool_grep_search_cancel_midflight_raises(tmp_path, monkeypatch):
    """grep_search must honor cancel during a long walk, not just at entry."""
    from mythic_agent.agents.tools import execute_tool
    for i in range(60):
        (tmp_path / f"file{i:03d}.txt").write_text("needle in a haystack\n" * 50)
    real_read_text = Path.read_text

    def slow_read_text(self, *args, **kwargs):
        time.sleep(0.02)
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", slow_read_text)
    cancel = threading.Event()
    agent = make_agent(tmp_path, cancel)
    outcome = {}

    def target():
        with pytest.raises(TurnCancelled):
            execute_tool("grep_search", {"query": "needle", "path": "."}, agent=agent)
        outcome["raised"] = True

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    time.sleep(0.2)  # let the search get underway (~1.2s of reads total)
    cancel.set()
    thread.join(timeout=20)
    assert not thread.is_alive(), "grep_search ignored a mid-flight cancel"
    assert outcome.get("raised"), "TurnCancelled was not raised by grep_search"


def test_execute_tool_grep_search_completes_without_cancel(tmp_path):
    """Control: the new cancel checks must not break the normal search path."""
    from mythic_agent.agents.tools import execute_tool
    (tmp_path / "a.txt").write_text("nothing here\n")
    (tmp_path / "b.txt").write_text("the needle hides\n")
    agent = make_agent(tmp_path, threading.Event())
    result = execute_tool("grep_search", {"query": "needle", "path": "."}, agent=agent)
    assert "b.txt" in result and "needle" in result


# ---------------------------------------------------------------------------
# command_handler cancel plumbing
# ---------------------------------------------------------------------------

def test_requires_permission_cancel_before_execution_raises():
    """The slash-command guard must refuse to run when its cancel is set."""
    from mythic_agent.agents.command_handler import requires_permission
    from mythic_agent.core.policy import ToolPolicy
    cancel = threading.Event()

    class Handler:
        def _policy(self):
            return ToolPolicy("trusted")

        def _cancel_event(self):
            return cancel

        @requires_permission("run_command")
        def _do(self, args):
            return "ran"

    handler = Handler()
    assert handler._do("x") == "ran"
    cancel.set()
    with pytest.raises(TurnCancelled):
        handler._do("x")


def test_prompt_approval_sync_cancel_before_approval_raises():
    from mythic_agent.agents.tools import prompt_approval_sync
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(TurnCancelled):
        prompt_approval_sync("do the thing", object(), cancel=cancel, timeout=5)


def test_prompt_approval_sync_cancel_midflight_raises():
    """A cancel while blocked on the approval decision must abort the wait."""
    from mythic_agent.agents.tools import prompt_approval_sync
    cancel = threading.Event()

    class FakeApp:
        def action_request_approval(self, *args):
            pass

        def call_from_thread(self, fn, *args):
            return object()  # never invokes decide: the decision never arrives

        def action_cancel_approval(self, modal):
            pass

    outcome = {}

    def target():
        with pytest.raises(TurnCancelled):
            prompt_approval_sync("do the thing", FakeApp(), cancel=cancel, timeout=30)
        outcome["raised"] = True

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    time.sleep(0.5)  # let it block inside the decision wait
    cancel.set()
    thread.join(timeout=10)
    assert not thread.is_alive(), "approval wait ignored a mid-flight cancel"
    assert outcome.get("raised")
