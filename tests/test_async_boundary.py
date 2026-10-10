"""R-015 async boundary audit: the sync/async bridge contract.

Contract under test (see ``run_cancellable_async`` docstring):

* Exceptions from the coroutine propagate UNCHANGED through the bridge --
  same object, same type, same message -- whether or not the caller sits
  inside a running event loop.
* A call from inside a running event loop is offloaded to a worker thread
  that owns its loop, so the caller never sees an "event loop is already
  running" style error.  (A committed suite,
  ``test_async_operation_cancel_drains_cleanup_and_supports_embedding_loop``,
  requires embedded calls to succeed; the bridge documents this instead of
  raising.)
* Cancellation through the bridge raises ``TurnCancelled`` on the sync side.
* Return values pass through unchanged.
* An ordinary coroutine failure must NOT poison the caller's shared cancel
  event (only genuine cancellation or a caller-side interrupt marks it).
"""
import asyncio
import functools
import threading
import time

import pytest

from mythic_agent.core.execution import run_cancellable_async
from mythic_agent.core.runtime import TurnCancelled


class BoomError(Exception):
    """Custom exception class: must survive the bridge with identity intact."""


def test_exception_identity_preserved_no_loop():
    """No running loop: the exact exception object propagates unchanged."""
    instance = BoomError("kablam")

    async def operation():
        raise instance

    with pytest.raises(BoomError) as excinfo:
        run_cancellable_async(operation, threading.Event())
    assert excinfo.value is instance
    assert excinfo.value.args == ("kablam",)


def test_exception_identity_preserved_from_running_loop():
    """Inside a running loop: same object, same type, same message."""
    instance = BoomError("kablam-in-loop")

    async def operation():
        raise instance

    async def caller():
        return run_cancellable_async(operation, threading.Event())

    with pytest.raises(BoomError) as excinfo:
        asyncio.run(caller())
    assert excinfo.value is instance
    assert excinfo.value.args == ("kablam-in-loop",)


def test_in_loop_call_succeeds_without_loop_confusion():
    """Embedded calls are offloaded to a worker thread; no loop error leaks.

    The bridge detects the running loop and drives the coroutine on a fresh
    loop in an owned thread, so sync code embedded in async contexts keeps
    working instead of hitting "event loop is already running".
    """
    async def operation():
        await asyncio.sleep(0.01)
        return {"embedded": True}

    async def caller():
        return run_cancellable_async(operation, threading.Event())

    assert asyncio.run(caller()) == {"embedded": True}


def test_cancel_through_bridge_raises_turn_cancelled_no_loop():
    """Cancel mid-flight on the direct path: TurnCancelled on the sync side."""
    cancel, started = threading.Event(), threading.Event()

    async def operation():
        started.set()
        await asyncio.sleep(60)

    def target():
        with pytest.raises(TurnCancelled):
            run_cancellable_async(operation, cancel)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    assert started.wait(5)
    cancel.set()
    thread.join(timeout=10)
    assert not thread.is_alive()


def test_cancel_through_bridge_raises_turn_cancelled_from_running_loop():
    """Cancel mid-flight on the embedded path: TurnCancelled on the sync side."""
    cancel, started = threading.Event(), threading.Event()

    async def operation():
        started.set()
        await asyncio.sleep(60)

    def setter():
        assert started.wait(5)
        time.sleep(0.2)
        cancel.set()

    async def caller():
        with pytest.raises(TurnCancelled):
            run_cancellable_async(operation, cancel)

    thread = threading.Thread(target=setter, daemon=True)
    thread.start()
    asyncio.run(caller())
    thread.join(timeout=10)
    assert not thread.is_alive()


def test_return_values_pass_through_unchanged():
    """Return values cross the bridge untouched on both paths."""
    payload = {"a": [1, 2, 3], "b": "text"}

    async def operation():
        return payload

    assert run_cancellable_async(operation, threading.Event()) == payload

    async def caller():
        return run_cancellable_async(operation, threading.Event())

    assert asyncio.run(caller()) == payload


def test_ordinary_exception_does_not_poison_shared_cancel_event():
    """A failed coroutine must not mark the caller's cancel event as set.

    Regression test: the embedded branch used to ``cancel.set()`` on ANY
    exception, so one failed request would masquerade as a user stop and
    break the caller's retry policy.
    """
    cancel = threading.Event()

    async def operation():
        raise ValueError("ordinary failure, not a cancellation")

    async def caller():
        with pytest.raises(ValueError, match="ordinary failure"):
            run_cancellable_async(operation, cancel)

    asyncio.run(caller())
    assert not cancel.is_set(), "ordinary coroutine failure poisoned the cancel event"


def test_genuine_cancellation_still_marks_shared_event_from_running_loop():
    """The narrowed handler keeps propagating real cancellation outward."""
    cancel = threading.Event()

    async def operation():
        await asyncio.sleep(60)

    def setter():
        time.sleep(0.2)
        cancel.set()

    async def caller():
        with pytest.raises(TurnCancelled):
            run_cancellable_async(operation, cancel)

    thread = threading.Thread(target=setter, daemon=True)
    thread.start()
    asyncio.run(caller())
    thread.join(timeout=10)
    assert cancel.is_set()


def test_publish_sync_handles_async_subscriber_without_qualname(caplog):
    """publish_sync must warn (not error) for async subscribers lacking __qualname__."""
    import logging
    from mythic_agent.core.secure_api import publish_sync, subscribe, unsubscribe

    async def _partial_target(**kwargs):
        raise AssertionError("must never be awaited from publish_sync")

    partial_cb = functools.partial(_partial_target)  # no __qualname__
    assert asyncio.iscoroutinefunction(partial_cb)
    received = []
    event = "r015-fixture-event"

    def sync_cb(**kwargs):
        received.append(kwargs)

    subscribe(event, partial_cb)
    subscribe(event, sync_cb)
    try:
        with caplog.at_level(logging.WARNING, logger="mythic_secure_api"):
            publish_sync(event, value=42)  # must not raise
    finally:
        unsubscribe(event, partial_cb)
        unsubscribe(event, sync_cb)
    assert received == [{"value": 42}], "sync subscriber was not called"
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING and "skipped" in r.message]
    assert warnings, "expected a skip warning for the async subscriber"
    errors = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert not errors, f"unexpected error logs: {[r.message for r in errors]}"
