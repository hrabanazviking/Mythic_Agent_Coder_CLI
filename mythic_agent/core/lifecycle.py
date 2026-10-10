"""Cooperative thread lifecycle registry (R-012).

Daemon threads cannot be killed from the outside; the only safe shutdown is
cooperative. Every worker thread that outlives the request that spawned it is
registered here together with a stop signal (a ``threading.Event`` and/or an
``on_stop`` callback). :func:`shutdown_all` sets every stop signal, runs every
``on_stop`` callback, then joins each thread against a bounded total budget.
Threads that ignore the signal are *reported* in the return value, never
waited on forever, so interpreter shutdown can never hang here.

Usage at a spawn site::

    thread = threading.Thread(target=work, name="mythic-worker", daemon=True)
    thread.start()
    register_thread(thread, stop_event)

Or in one step::

    spawn_managed(work, name="mythic-worker", on_stop=inbox.put-None-ish)

Wire :func:`install_atexit` once per process entry point (``cli.main``,
``engine.initialize``, ``mcp_server.main``) so interpreter exit always runs
:func:`shutdown_all`. It is idempotent and exception-safe.
"""

from __future__ import annotations

__all__ = [
    "ManagedThread",
    "install_atexit",
    "register_thread",
    "registry_snapshot",
    "shutdown_all",
    "spawn_managed",
    "unregister_thread",
]

import atexit
import logging
import threading
import time

log = logging.getLogger(__name__)


class ManagedThread:
    """A registered worker thread plus its cooperative stop signal."""

    __slots__ = ("name", "on_stop", "stop", "thread")

    def __init__(self, thread: threading.Thread,
                 stop: threading.Event | None = None,
                 on_stop=None,
                 name: str | None = None) -> None:
        self.thread = thread
        # A fresh event is harmless for threads whose real stop signal is
        # delivered via on_stop; setting it is always safe.
        self.stop = stop if stop is not None else threading.Event()
        self.on_stop = on_stop
        self.name = name or thread.name

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"ManagedThread(name={self.name!r}, alive={self.thread.is_alive()})"


_registry: list[ManagedThread] = []
_lock = threading.Lock()
_atexit_installed = False
_atexit_timeout = 5.0


def register_thread(thread: threading.Thread,
                    stop: threading.Event | None = None,
                    *,
                    on_stop=None,
                    name: str | None = None) -> ManagedThread:
    """Register an already-started (or soon-to-start) thread for shutdown.

    Registering the same thread twice returns the existing entry.
    """
    with _lock:
        for existing in _registry:
            if existing.thread is thread:
                return existing
        managed = ManagedThread(thread, stop=stop, on_stop=on_stop, name=name)
        _registry.append(managed)
        return managed


def unregister_thread(thread: threading.Thread) -> bool:
    """Remove *thread* from the registry. Returns True when it was present."""
    with _lock:
        for index, managed in enumerate(_registry):
            if managed.thread is thread:
                del _registry[index]
                return True
    return False


def registry_snapshot() -> list[ManagedThread]:
    """Return a copy of the current registry (for tests and diagnostics)."""
    with _lock:
        return list(_registry)


def spawn_managed(target, *,
                  name: str,
                  args: tuple = (),
                  kwargs: dict | None = None,
                  stop: threading.Event | None = None,
                  on_stop=None,
                  daemon: bool = True) -> ManagedThread:
    """Create, register, and start a worker thread in one step."""
    stop_event = stop if stop is not None else threading.Event()
    thread = threading.Thread(target=target, name=name, args=args,
                              kwargs=kwargs or {}, daemon=daemon)
    managed = register_thread(thread, stop_event, on_stop=on_stop, name=name)
    thread.start()
    return managed


def shutdown_all(timeout: float = 5.0) -> list[str]:
    """Signal every registered thread to stop, then join within *timeout*.

    The timeout is a *total* budget shared by all joins: each thread gets the
    remaining time, so this call can never take longer than ``timeout``
    plus the (bounded) cost of the stop callbacks. Idempotent (a second call
    finds an empty registry and returns ``[]``) and exception-safe: failures
    in one thread's signal or join never abort the rest.

    Returns the names of threads still alive afterwards -- threads that
    refused the stop signal. They are reported, not waited on.
    """
    with _lock:
        pending = _registry[:]
        _registry.clear()
    if not pending:
        return []
    try:
        budget = float(timeout)
    except (TypeError, ValueError):
        budget = 5.0
    if budget < 0:
        budget = 0.0
    deadline = time.monotonic() + budget

    # Signal first, join later: every thread gets the maximum chance to
    # observe the stop signal before its join budget starts shrinking.
    for managed in pending:
        try:
            managed.stop.set()
        except Exception:
            log.debug("lifecycle: stop.set() failed for %s", managed.name,
                      exc_info=True)
        if managed.on_stop is not None:
            try:
                managed.on_stop()
            except Exception:
                log.debug("lifecycle: on_stop failed for %s", managed.name,
                          exc_info=True)

    refused: list[str] = []
    for managed in pending:
        thread = managed.thread
        try:
            if not thread.is_alive():
                continue
            remaining = deadline - time.monotonic()
            thread.join(timeout=max(0.0, remaining))
            if thread.is_alive():
                refused.append(managed.name)
        except Exception:
            log.debug("lifecycle: join failed for %s", managed.name,
                      exc_info=True)
    if refused:
        log.warning("lifecycle: %d thread(s) refused to stop within %.1fs: %s",
                    len(refused), budget, ", ".join(refused))
    return refused


def install_atexit(timeout: float = 5.0) -> None:
    """Install the atexit shutdown hook exactly once per process.

    Safe to call from every entry point; later calls are no-ops. The hook
    itself is exception-safe and bounded by *timeout*.
    """
    global _atexit_installed, _atexit_timeout
    with _lock:
        if _atexit_installed:
            return
        _atexit_installed = True
        _atexit_timeout = timeout

    def _hook() -> None:
        try:
            shutdown_all(timeout=_atexit_timeout)
        except Exception:
            log.debug("lifecycle: atexit shutdown failed", exc_info=True)

    atexit.register(_hook)
