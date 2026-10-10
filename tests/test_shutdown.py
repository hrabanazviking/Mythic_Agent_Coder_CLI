"""R-012: shutdown correctness for the lifecycle thread registry.

* Registered threads with cooperative stop signals terminate within the
  shutdown budget.
* ``shutdown_all()`` is idempotent (a second call finds an empty registry).
* A thread that ignores its stop signal is *reported*, never waited on
  forever.
* A full interpreter exit does not hang when managed threads are registered
  (verified in a subprocess).
"""

import os
import subprocess
import sys
import textwrap
import threading
import time

import pytest

from mythic_agent.core import lifecycle
from mythic_agent.core.lifecycle import (
    install_atexit,
    register_thread,
    registry_snapshot,
    shutdown_all,
    spawn_managed,
    unregister_thread,
)


@pytest.fixture(autouse=True)
def clean_registry():
    """Each test starts and ends with an empty registry."""
    shutdown_all(timeout=0.1)
    yield
    shutdown_all(timeout=2.0)


def _cooperative_worker(stop: threading.Event, started: threading.Event):
    started.set()
    while not stop.is_set():
        time.sleep(0.005)


def test_registered_thread_terminates_within_timeout():
    stop = threading.Event()
    started = threading.Event()
    thread = threading.Thread(target=_cooperative_worker, args=(stop, started),
                              name="test-cooperative", daemon=True)
    thread.start()
    assert started.wait(timeout=5)
    register_thread(thread, stop, name="test-cooperative")
    refused = shutdown_all(timeout=5.0)
    assert refused == []
    assert not thread.is_alive()


def test_shutdown_all_is_idempotent():
    stop = threading.Event()
    started = threading.Event()
    thread = threading.Thread(target=_cooperative_worker, args=(stop, started),
                              name="test-idempotent", daemon=True)
    thread.start()
    assert started.wait(timeout=5)
    register_thread(thread, stop, name="test-idempotent")
    assert shutdown_all(timeout=5.0) == []
    assert shutdown_all(timeout=5.0) == []
    assert shutdown_all(timeout=5.0) == []


def test_stubborn_thread_is_reported_not_hung():
    stop = threading.Event()
    started = threading.Event()

    def stubborn(stop_event, started_event):
        started_event.set()
        while True:  # deliberately ignores the stop signal
            time.sleep(0.01)

    thread = threading.Thread(target=stubborn, args=(stop, started),
                              name="test-stubborn", daemon=True)
    thread.start()
    assert started.wait(timeout=5)
    register_thread(thread, stop, name="test-stubborn")
    started_at = time.monotonic()
    refused = shutdown_all(timeout=0.5)
    elapsed = time.monotonic() - started_at
    assert refused == ["test-stubborn"]
    assert elapsed < 5.0, f"shutdown_all hung for {elapsed:.1f}s"
    # Registry was drained even though the thread survived.
    assert registry_snapshot() == []
    assert shutdown_all(timeout=0.5) == []


def test_register_same_thread_twice_returns_existing():
    stop = threading.Event()
    started = threading.Event()
    thread = threading.Thread(target=_cooperative_worker, args=(stop, started),
                              daemon=True)
    thread.start()
    assert started.wait(timeout=5)
    first = register_thread(thread, stop)
    second = register_thread(thread, stop)
    assert first is second
    assert len(registry_snapshot()) == 1
    assert shutdown_all(timeout=5.0) == []


def test_unregister_removes_thread():
    stop = threading.Event()
    started = threading.Event()
    thread = threading.Thread(target=_cooperative_worker, args=(stop, started),
                              daemon=True)
    thread.start()
    assert started.wait(timeout=5)
    register_thread(thread, stop)
    assert unregister_thread(thread) is True
    assert unregister_thread(thread) is False
    assert registry_snapshot() == []
    # Not registered anymore: shutdown leaves it alone (still alive).
    assert shutdown_all(timeout=0.5) == []
    assert thread.is_alive()
    stop.set()
    thread.join(timeout=5)


def test_spawn_managed_registers_and_starts():
    stop = threading.Event()
    started = threading.Event()
    managed = spawn_managed(_cooperative_worker, name="test-spawned",
                            args=(stop, started), stop=stop)
    assert started.wait(timeout=5)
    assert managed.thread.is_alive()
    assert any(m.name == "test-spawned" for m in registry_snapshot())
    assert shutdown_all(timeout=5.0) == []
    assert not managed.thread.is_alive()


def test_install_atexit_is_idempotent():
    install_atexit(timeout=1.0)
    install_atexit(timeout=1.0)  # second call must be a no-op, not an error


def _run_script(script: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env["PYTHONPATH"] = repo_root + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run([sys.executable, "-c", script],
                          capture_output=True, text=True, timeout=20, env=env)
def test_interpreter_exit_does_not_hang():
    """A process that registers a managed thread must exit promptly."""
    script = textwrap.dedent("""\
        import threading, time
        from mythic_agent.core.lifecycle import install_atexit, register_thread, shutdown_all
        stop = threading.Event()
        def work():
            while not stop.is_set():
                time.sleep(0.01)
        thread = threading.Thread(target=work, name="subproc-worker", daemon=True)
        thread.start()
        register_thread(thread, stop, name="subproc-worker")
        install_atexit(timeout=2.0)
        # Cooperative: atexit will stop it. Exit without joining explicitly.
    """)
    proc = _run_script(script)
    assert proc.returncode == 0, proc.stderr
    assert "refused to stop" not in proc.stderr


def test_interpreter_exit_with_stubborn_thread_still_exits():
    """Even a thread that ignores its stop signal cannot hang interpreter exit."""
    script = textwrap.dedent("""\
        import threading, time
        from mythic_agent.core.lifecycle import install_atexit, register_thread
        def work():
            while True:
                time.sleep(0.01)
        thread = threading.Thread(target=work, name="subproc-stubborn", daemon=True)
        thread.start()
        register_thread(thread, threading.Event(), name="subproc-stubborn")
        install_atexit(timeout=1.0)
    """)
    started = time.monotonic()
    proc = _run_script(script)
    elapsed = time.monotonic() - started
    assert proc.returncode == 0, proc.stderr
    assert elapsed < 15.0, f"interpreter exit hung for {elapsed:.1f}s"
