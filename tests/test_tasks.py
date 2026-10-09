"""Tests for mythic_agent.agents.tasks (SLICE 2 — S08 Agent lifecycle)."""

import threading

import pytest

from mythic_agent.agents.tasks import (
    AgentBudgets,
    TaskRecord,
    TaskRegistry,
    TaskState,
    get_registry,
)


@pytest.fixture()
def registry() -> TaskRegistry:
    return TaskRegistry()


# ----------------------------------------------------------------------
# basic CRUD roundtrip
# ----------------------------------------------------------------------
def test_create_get_update_roundtrip(registry):
    record = registry.create("hello-world")
    assert isinstance(record.task_id, str) and record.task_id
    assert record.name == "hello-world"
    assert record.parent_id is None
    assert record.state is TaskState.QUEUED
    assert record.result is None
    assert record.error is None

    fetched = registry.get(record.task_id)
    assert fetched is not None
    assert fetched.task_id == record.task_id
    assert fetched.name == "hello-world"

    updated = registry.update_state(
        record.task_id, TaskState.RUNNING
    )
    assert updated.state is TaskState.RUNNING
    assert updated.updated_at >= record.updated_at

    updated = registry.update_state(
        record.task_id, TaskState.COMPLETED, result={"ok": True}
    )
    assert updated.state is TaskState.COMPLETED
    assert updated.result == {"ok": True}

    failed = registry.create("boom")
    updated = registry.update_state(
        failed.task_id, TaskState.FAILED, error="kaboom"
    )
    assert updated.state is TaskState.FAILED
    assert updated.error == "kaboom"

    assert registry.get("no-such-task") is None


def test_task_ids_are_unique(registry):
    ids = {registry.create(f"t{i}").task_id for i in range(200)}
    assert len(ids) == 200


def test_get_returns_snapshot_not_live_record(registry):
    record = registry.create("snap")
    fetched = registry.get(record.task_id)
    assert fetched is not None
    fetched.name = "mutated"
    refetched = registry.get(record.task_id)
    assert refetched is not None
    assert refetched.name == "snap"


def test_unknown_task_errors(registry):
    with pytest.raises(KeyError):
        registry.update_state("missing", TaskState.RUNNING)
    with pytest.raises(KeyError):
        registry.cancel("missing")
    with pytest.raises(KeyError):
        registry.create("orphan", parent_id="missing-parent")


# ----------------------------------------------------------------------
# parent / child relationships
# ----------------------------------------------------------------------
def test_parent_child_relationships(registry):
    parent = registry.create("parent")
    child1 = registry.create("child1", parent_id=parent.task_id)
    child2 = registry.create("child2", parent_id=parent.task_id)
    grandchild = registry.create(
        "grandchild", parent_id=child1.task_id
    )

    assert child1.parent_id == parent.task_id
    assert child2.parent_id == parent.task_id
    assert grandchild.parent_id == child1.task_id

    children = registry.list_by_parent(parent.task_id)
    assert {c.task_id for c in children} == {
        child1.task_id,
        child2.task_id,
    }

    grandchildren = registry.list_by_parent(child1.task_id)
    assert [g.task_id for g in grandchildren] == [grandchild.task_id]

    assert registry.list_by_parent(child2.task_id) == []


# ----------------------------------------------------------------------
# cycle detection
# ----------------------------------------------------------------------
def test_cycle_detection_rejects_child_under_cycle(registry):
    a = registry.create("A")
    b = registry.create("B", parent_id=a.task_id)
    c = registry.create("C", parent_id=b.task_id)

    # Healthy chain: no cycle detected.
    assert registry._would_cycle(c.task_id) is False

    # Simulate corruption: A -> B -> C -> A (C becomes A's parent).
    registry._tasks[a.task_id].parent_id = c.task_id
    assert registry._would_cycle(a.task_id) is True
    assert registry._would_cycle(c.task_id) is True

    # Any new child attached under the cycle must be rejected.
    with pytest.raises(ValueError):
        registry.create("D", parent_id=c.task_id)


def test_self_parent_cycle_rejected(registry):
    a = registry.create("A")
    registry._tasks[a.task_id].parent_id = a.task_id
    assert registry._would_cycle(a.task_id) is True
    with pytest.raises(ValueError):
        registry.create("child-of-self", parent_id=a.task_id)


# ----------------------------------------------------------------------
# cancellation
# ----------------------------------------------------------------------
def test_cancel_propagates_to_children(registry):
    parent = registry.create("parent")
    child1 = registry.create("child1", parent_id=parent.task_id)
    child2 = registry.create("child2", parent_id=parent.task_id)
    grandchild = registry.create("grandchild", parent_id=child1.task_id)
    unrelated = registry.create("unrelated")

    registry.update_state(child1.task_id, TaskState.RUNNING)
    registry.update_state(grandchild.task_id, TaskState.RUNNING)

    cancelled = registry.cancel(parent.task_id)
    cancelled_ids = {r.task_id for r in cancelled}
    assert cancelled_ids == {
        parent.task_id,
        child1.task_id,
        child2.task_id,
        grandchild.task_id,
    }

    for tid in cancelled_ids:
        record = registry.get(tid)
        assert record is not None
        assert record.state is TaskState.CANCELLED

    # Unrelated task untouched.
    assert registry.get(unrelated.task_id).state is TaskState.QUEUED


def test_cancel_skips_terminal_tasks(registry):
    parent = registry.create("parent")
    done = registry.create("done", parent_id=parent.task_id)
    registry.update_state(done.task_id, TaskState.COMPLETED, result=42)

    registry.cancel(parent.task_id)

    done_record = registry.get(done.task_id)
    assert done_record is not None
    assert done_record.state is TaskState.COMPLETED
    assert done_record.result == 42
    assert registry.get(parent.task_id).state is TaskState.CANCELLED


# ----------------------------------------------------------------------
# concurrency
# ----------------------------------------------------------------------
def test_concurrent_creation_no_duplicates_or_corruption():
    registry = TaskRegistry()
    per_thread = 100
    threads = 10
    created = []
    created_lock = threading.Lock()

    def worker(n):
        local = []
        for i in range(per_thread):
            local.append(registry.create(f"worker-{n}-task-{i}").task_id)
        with created_lock:
            created.extend(local)

    handles = [threading.Thread(target=worker, args=(n,)) for n in range(threads)]
    for h in handles:
        h.start()
    for h in handles:
        h.join()

    assert len(created) == threads * per_thread
    assert len(set(created)) == len(created), "duplicate task ids!"
    assert len(registry.list_all()) == threads * per_thread
    for tid in created:
        assert registry.get(tid) is not None


def test_concurrent_state_updates_are_safe():
    registry = TaskRegistry()
    record = registry.create("shared")
    threads = 8
    iterations = 50

    def worker(n):
        for i in range(iterations):
            registry.update_state(
                record.task_id, TaskState.RUNNING, result=f"w{n}-{i}"
            )

    handles = [threading.Thread(target=worker, args=(n,)) for n in range(threads)]
    for h in handles:
        h.start()
    for h in handles:
        h.join()

    final = registry.get(record.task_id)
    assert final is not None
    assert final.state is TaskState.RUNNING
    assert final.result is not None


# ----------------------------------------------------------------------
# budgets and registry singleton
# ----------------------------------------------------------------------
def test_agent_budgets_defaults():
    budgets = AgentBudgets()
    assert budgets.max_turns == 50
    assert budgets.max_tool_calls == 100
    assert budgets.max_concurrent == 5


def test_agent_budgets_custom():
    budgets = AgentBudgets(max_turns=10, max_tool_calls=20, max_concurrent=2)
    assert budgets.max_turns == 10
    assert budgets.max_tool_calls == 20
    assert budgets.max_concurrent == 2


def test_get_registry_singleton():
    assert get_registry() is get_registry()
    assert isinstance(get_registry(), TaskRegistry)


def test_task_state_values():
    assert TaskState.QUEUED.value == "queued"
    assert TaskState.RUNNING.value == "running"
    assert TaskState.COMPLETED.value == "completed"
    assert TaskState.FAILED.value == "failed"
    assert TaskState.CANCELLED.value == "cancelled"


def test_task_record_defaults():
    record = TaskRecord(name="bare")
    assert record.parent_id is None
    assert record.state is TaskState.QUEUED
    assert record.result is None
    assert record.error is None
    assert record.created_at is not None
    assert record.updated_at is not None
