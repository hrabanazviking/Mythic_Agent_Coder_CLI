"""Thread ownership audit: named-thread bookkeeping and asyncio loop affinity.

Mythic Agent runs several background threads (agent inbox loops, slash-command
workers, process-output readers, TTS/recording workers) plus short-lived
asyncio event loops owned by the sync/async bridge in ``execution.py``.

This module makes the discipline explicit and testable:

* :class:`ThreadRegistry` records named threads so each name has exactly one
  live owner.  Registering a second *live* thread under a name that already
  has one raises :class:`ThreadAffinityError` instead of silently starting a
  duplicate loop/worker thread.
* :class:`LoopAffinity` binds an asyncio event loop to the thread that created
  it and raises :class:`ThreadAffinityError` if any other thread tries to
  drive that loop (asyncio loops are not thread-safe).
* :func:`describe_threads` returns a diagnostic snapshot of all live threads.

Conventions for thread names (see individual spawn sites):

* ``mythic-slash-command-<token>`` -- one slash-command worker per dispatch
  (``agents/command_handler.py``); serialised by the handler's command lock.
* ``mythic-subagent-loop:<name>`` / ``mythic-ghost-loop:<name>`` -- one inbox
  loop thread per spawned subagent/ghost (``agents/llm.py``).
* ``mythic-process-output`` -- subprocess stdout reader (``core/execution.py``).
* ``mythic-request`` -- one-shot ThreadPoolExecutor worker that drives the
  owned event loop when the caller already has a running loop
  (``core/execution.py::run_cancellable_async``).
"""

from __future__ import annotations

import asyncio
import threading

from .exceptions import MythicError

__all__ = [
    "THREAD_REGISTRY",
    "LoopAffinity",
    "ThreadAffinityError",
    "ThreadRegistry",
    "describe_threads",
]


class ThreadAffinityError(MythicError):
    """A thread-ownership or event-loop affinity rule was violated."""


class ThreadRegistry:
    """Named-thread bookkeeping: one live owner per thread name.

    The registry is advisory -- it does not start or stop threads.  It
    records the threads spawn sites hand it, prunes dead entries on every
    mutation/query, and raises :class:`ThreadAffinityError` if a second *live*
    thread tries to claim a name that already has a live owner.  This catches
    accidental duplicate loop/worker threads at the spawn site instead of
    letting them race.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._threads: dict[str, threading.Thread] = {}

    def _prune_locked(self) -> None:
        dead = [name for name, thread in self._threads.items() if not thread.is_alive()]
        for name in dead:
            del self._threads[name]

    def register(self, thread: threading.Thread, name: str | None = None) -> threading.Thread:
        """Record ``thread`` under ``name`` (defaults to ``thread.name``).

        Renames the thread to the registered name and returns it.  Raises
        :class:`ThreadAffinityError` if another *live* thread already owns
        that name.  Safe to call before ``thread.start()``: a not-yet-started
        duplicate cannot exist yet because registration happens at the spawn
        site, and dead prior owners are pruned.
        """
        name = name or thread.name
        thread.name = name
        with self._lock:
            self._prune_locked()
            existing = self._threads.get(name)
            if existing is not None and existing.is_alive():
                raise ThreadAffinityError(
                    f"Duplicate live thread registered under name {name!r}: "
                    f"existing ident={existing.ident}, new ident={thread.ident}"
                )
            self._threads[name] = thread
        return thread

    def names(self) -> list[str]:
        """Return the names of all currently live registered threads."""
        with self._lock:
            self._prune_locked()
            return sorted(self._threads)

    def assert_single_owner(self, name: str) -> None:
        """Raise :class:`ThreadAffinityError` if a live thread already owns ``name``.

        Call this *before* creating a new thread to fail fast on accidental
        duplicate spawn attempts.
        """
        with self._lock:
            self._prune_locked()
            existing = self._threads.get(name)
            if existing is not None and existing.is_alive():
                raise ThreadAffinityError(
                    f"Thread name {name!r} already owned by live thread "
                    f"ident={existing.ident}"
                )

    def forget(self, name: str) -> None:
        """Drop the bookkeeping entry for ``name`` (the thread itself is untouched)."""
        with self._lock:
            self._threads.pop(name, None)


# Default process-wide registry shared by the spawn sites.
THREAD_REGISTRY = ThreadRegistry()


class LoopAffinity:
    """Bind an asyncio event loop to the thread that created it.

    asyncio event loops are not thread-safe: creating a loop on one thread
    and driving it (``run_until_complete``) from another is a bug.  The
    pattern is::

        loop = asyncio.new_event_loop()
        affinity = LoopAffinity()
        affinity.bind(loop)        # records the creating thread
        affinity.check()          # raises ThreadAffinityError on any other thread
        loop.run_until_complete(coro())

    A ``LoopAffinity`` instance is single-use per loop; rebinding to a
    different still-open loop raises.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._owner_ident: int | None = None

    def bind(self, loop: asyncio.AbstractEventLoop) -> None:
        """Record ``loop`` as owned by the calling thread."""
        ident = threading.get_ident()
        with self._lock:
            if self._loop is not None and self._loop is not loop:
                if not self._loop.is_closed():
                    raise ThreadAffinityError(
                        "LoopAffinity already bound to a different open loop; "
                        "use a fresh LoopAffinity per loop"
                    )
            self._loop = loop
            self._owner_ident = ident

    def owner_ident(self) -> int | None:
        """Return the ident of the thread that bound the loop, or ``None``."""
        with self._lock:
            return self._owner_ident

    def check(self) -> None:
        """Raise :class:`ThreadAffinityError` unless called on the owning thread."""
        with self._lock:
            loop = self._loop
            owner = self._owner_ident
        if loop is None or owner is None:
            raise ThreadAffinityError("LoopAffinity.check() called with no bound loop")
        current = threading.get_ident()
        if current != owner:
            raise ThreadAffinityError(
                f"Event loop {loop!r} owned by thread ident={owner} but driven "
                f"from thread ident={current}"
            )


def describe_threads() -> list[tuple[str, int | None, bool, bool]]:
    """Snapshot of live threads: ``(name, ident, daemon, alive)`` sorted by name."""
    return sorted(
        (thread.name, thread.ident, thread.daemon, thread.is_alive())
        for thread in threading.enumerate()
    )
