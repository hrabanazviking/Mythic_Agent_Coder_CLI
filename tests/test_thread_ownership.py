"""Thread ownership audit: duplicate registration, loop affinity, diagnostics."""

import asyncio
import threading
import time

import pytest

from mythic_agent.core.exceptions import MythicError
from mythic_agent.core.runtime import TurnCancelled
from mythic_agent.core.thread_audit import (
    THREAD_REGISTRY,
    LoopAffinity,
    ThreadAffinityError,
    ThreadRegistry,
    describe_threads,
)


def _sleeping_thread(name, stop):
    def target():
        stop.wait()
    thread = threading.Thread(target=target, name=name, daemon=True)
    thread.start()
    assert thread.is_alive()
    return thread


def test_duplicate_thread_name_registration_raises():
    registry = ThreadRegistry()
    stop = threading.Event()
    first = _sleeping_thread("mythic-dup-name", stop)
    try:
        registry.register(first)
        stop2 = threading.Event()
        second = _sleeping_thread("mythic-dup-name", stop2)
        try:
            with pytest.raises(ThreadAffinityError):
                registry.register(second)
            # assert_single_owner also fails fast for a live name
            with pytest.raises(ThreadAffinityError):
                registry.assert_single_owner("mythic-dup-name")
        finally:
            stop2.set()
            second.join(timeout=2)
    finally:
        stop.set()
        first.join(timeout=2)
    # Dead owners are pruned: re-registering the same name now succeeds
    stop3 = threading.Event()
    replacement = _sleeping_thread("mythic-dup-name", stop3)
    try:
        registry.assert_single_owner("mythic-dup-name")  # must not raise
        registry.register(replacement)
        assert "mythic-dup-name" in registry.names()
    finally:
        stop3.set()
        replacement.join(timeout=2)


def test_thread_affinity_error_is_mythic_error():
    assert issubclass(ThreadAffinityError, MythicError)


def test_loop_affinity_same_thread_check_passes():
    affinity = LoopAffinity()
    loop = asyncio.new_event_loop()
    try:
        affinity.bind(loop)
        affinity.check()  # same thread: no raise
        assert affinity.owner_ident() == threading.get_ident()
    finally:
        loop.close()


def test_loop_affinity_cross_thread_drive_raises():
    affinity = LoopAffinity()
    loop = asyncio.new_event_loop()
    errors = []
    try:
        affinity.bind(loop)
        def intruder():
            try:
                affinity.check()
            except ThreadAffinityError as exc:
                errors.append(exc)
        worker = threading.Thread(target=intruder, daemon=True)
        worker.start()
        worker.join(timeout=5)
        assert len(errors) == 1, "check() must raise ThreadAffinityError on a foreign thread"
    finally:
        loop.close()


def test_loop_affinity_check_without_bind_raises():
    with pytest.raises(ThreadAffinityError):
        LoopAffinity().check()


def test_loop_affinity_rebind_to_open_loop_raises():
    affinity = LoopAffinity()
    first, second = asyncio.new_event_loop(), asyncio.new_event_loop()
    try:
        affinity.bind(first)
        with pytest.raises(ThreadAffinityError):
            affinity.bind(second)
    finally:
        first.close()
        second.close()


def test_describe_threads_reflects_reality():
    stop = threading.Event()
    thread = _sleeping_thread("mythic-describe-probe", stop)
    try:
        snapshot = describe_threads()
        by_name = {name: (ident, daemon, alive) for name, ident, daemon, alive in snapshot}
        assert "mythic-describe-probe" in by_name
        ident, daemon, alive = by_name["mythic-describe-probe"]
        assert ident == thread.ident
        assert daemon is True
        assert alive is True
    finally:
        stop.set()
        thread.join(timeout=2)


def test_global_registry_accepts_unique_name():
    stop = threading.Event()
    name = f"mythic-global-probe:{id(stop):x}"
    thread = _sleeping_thread(name, stop)
    try:
        THREAD_REGISTRY.assert_single_owner(name)
        THREAD_REGISTRY.register(thread)
        assert name in THREAD_REGISTRY.names()
    finally:
        stop.set()
        thread.join(timeout=2)
        THREAD_REGISTRY.forget(name)


def test_run_cancellable_async_regression():
    """The async bridge still works normally with loop-affinity binding in place."""
    from mythic_agent.core.execution import run_cancellable_async

    async def factory():
        await asyncio.sleep(0)
        return "affinity-ok"

    result = run_cancellable_async(factory, threading.Event())
    assert result == "affinity-ok"


def test_run_cancellable_async_pre_cancelled_regression():
    from mythic_agent.core.execution import run_cancellable_async

    async def factory():
        return "never"

    cancel = threading.Event()
    cancel.set()
    with pytest.raises(TurnCancelled):
        run_cancellable_async(factory, cancel)


def test_run_cancellable_async_from_running_loop_regression():
    """Caller already has a loop: bridge still bridges via the owned pool thread."""
    from mythic_agent.core.execution import run_cancellable_async

    async def outer():
        async def factory():
            await asyncio.sleep(0)
            return "nested-ok"
        return run_cancellable_async(factory, threading.Event())

    assert asyncio.run(outer()) == "nested-ok"
