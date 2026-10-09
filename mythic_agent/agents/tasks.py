"""Agent task lifecycle tracking for Mythic_Agent_Coder_CLI.

This module provides a small, thread-safe registry for tracking the
lifecycle of agent tasks (including sub-agent tasks spawned by a parent).
It does not execute tasks itself; it records their state transitions so
orchestrators and the UI can observe and cancel work safely.

Thread safety:
    All public registry operations are serialized with an internal
    ``threading.Lock``.  ``TaskRecord`` instances returned by the registry
    are snapshots -- mutating them directly does not affect the registry;
    use :meth:`TaskRegistry.update_state` to change state.
"""

from __future__ import annotations

import copy
import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TaskState(str, Enum):
    """Lifecycle states for a tracked agent task."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskRecord:
    """A single task's bookkeeping record."""

    task_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    parent_id: Optional[str] = None
    name: str = "task"
    state: TaskState = TaskState.QUEUED
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)
    result: Any = None
    error: Optional[str] = None


@dataclass
class AgentBudgets:
    """Per-agent execution budgets enforced by the orchestrator."""

    max_turns: int = 50
    max_tool_calls: int = 100
    max_concurrent: int = 5


class TaskRegistry:
    """Thread-safe registry of task lifecycle records.

    Supports parent/child relationships (sub-agent tasks) with cycle
    protection, recursive cancellation, and safe concurrent creation.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._tasks: Dict[str, TaskRecord] = {}

    # ------------------------------------------------------------------
    # creation / lookup
    # ------------------------------------------------------------------
    def create(self, name: str, parent_id: Optional[str] = None) -> TaskRecord:
        """Create and register a new task, returning its record.

        Raises:
            KeyError: if ``parent_id`` does not name a known task.
            ValueError: if attaching to ``parent_id`` would create a
                parent-chain cycle (including self-parenting).
        """
        with self._lock:
            if parent_id is not None:
                if parent_id not in self._tasks:
                    raise KeyError(f"unknown parent task: {parent_id!r}")
                if self._would_cycle(parent_id):
                    raise ValueError(
                        f"creating task with parent {parent_id!r} would "
                        "introduce a parent-chain cycle"
                    )
            record = TaskRecord(name=name, parent_id=parent_id)
            self._tasks[record.task_id] = record
            logger.debug(
                "task created: %s (%s) parent=%s",
                record.task_id,
                name,
                parent_id,
            )
            return copy.deepcopy(record)

    def get(self, task_id: str) -> Optional[TaskRecord]:
        """Return a snapshot of the record for ``task_id``, or None."""
        with self._lock:
            record = self._tasks.get(task_id)
            return copy.deepcopy(record) if record is not None else None

    def list_all(self) -> List[TaskRecord]:
        """Return snapshots of every registered task."""
        with self._lock:
            return [copy.deepcopy(r) for r in self._tasks.values()]

    def list_by_parent(self, parent_id: str) -> List[TaskRecord]:
        """Return snapshots of the direct children of ``parent_id``."""
        with self._lock:
            return [
                copy.deepcopy(r)
                for r in self._tasks.values()
                if r.parent_id == parent_id
            ]

    # ------------------------------------------------------------------
    # state transitions
    # ------------------------------------------------------------------
    def update_state(
        self,
        task_id: str,
        state: TaskState,
        result: Any = None,
        error: Optional[str] = None,
    ) -> TaskRecord:
        """Transition a task to ``state``, stamping ``updated_at``.

        ``result``/``error`` are stored alongside the record.  Passing
        ``result=None`` leaves a previously stored result unchanged only
        when ``state`` is not COMPLETED; on COMPLETED the stored result
        is replaced with the given value.

        Raises:
            KeyError: if ``task_id`` is unknown.
        """
        with self._lock:
            record = self._tasks.get(task_id)
            if record is None:
                raise KeyError(f"unknown task: {task_id!r}")
            record.state = state
            record.updated_at = _utcnow()
            if result is not None or state is TaskState.COMPLETED:
                record.result = result
            if error is not None or state is TaskState.FAILED:
                record.error = error
            logger.debug("task %s -> %s", task_id, state.value)
            return copy.deepcopy(record)

    def cancel(self, task_id: str) -> List[TaskRecord]:
        """Mark a task CANCELLED, recursively cancelling its children.

        Returns snapshots of every record that was cancelled.
        Already-terminal tasks (COMPLETED/FAILED/CANCELLED) are left
        untouched.  Raises KeyError if ``task_id`` is unknown.
        """
        with self._lock:
            if task_id not in self._tasks:
                raise KeyError(f"unknown task: {task_id!r}")
            cancelled: List[TaskRecord] = []
            # Depth-first over the child tree.
            stack = [task_id]
            seen = set()
            while stack:
                current = stack.pop()
                if current in seen:
                    continue
                seen.add(current)
                record = self._tasks[current]
                if record.state in (
                    TaskState.COMPLETED,
                    TaskState.FAILED,
                    TaskState.CANCELLED,
                ):
                    continue
                record.state = TaskState.CANCELLED
                record.updated_at = _utcnow()
                cancelled.append(copy.deepcopy(record))
                for child in self._tasks.values():
                    if child.parent_id == current:
                        stack.append(child.task_id)
            logger.debug("cancelled %d task(s) under %s", len(cancelled), task_id)
            return cancelled

    # ------------------------------------------------------------------
    # cycle detection
    # ------------------------------------------------------------------
    def _would_cycle(self, parent_id: str) -> bool:
        """True if walking up from ``parent_id`` revisits a node.

        Must be called with the lock held.  A self-parent reference or any
        repeated ancestor means the chain is already cyclic and a new child
        attached below it must be rejected.
        """
        seen = set()
        current: Optional[str] = parent_id
        while current is not None:
            if current in seen:
                return True
            seen.add(current)
            record = self._tasks.get(current)
            if record is None:  # defensive: parent validated at create()
                return False
            current = record.parent_id
        return False


_registry: Optional[TaskRegistry] = None
_registry_lock = threading.Lock()


def get_registry() -> TaskRegistry:
    """Return the process-wide :class:`TaskRegistry` singleton."""
    global _registry
    if _registry is None:
        with _registry_lock:
            if _registry is None:
                _registry = TaskRegistry()
    return _registry
