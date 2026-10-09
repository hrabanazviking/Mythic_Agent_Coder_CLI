"""Tests for multi-step planning (Slice 16)."""

import pytest

from mythic_agent.agents.planning import (
    Plan,
    PlanStepStatus,
    Planner,
    Step,
)


def test_write_file_goal_decomposes_into_real_steps():
    planner = Planner()
    plan = planner.create_plan("Write the file report.txt with the results")
    assert isinstance(plan, Plan)
    assert plan.goal.startswith("Write the file")
    assert len(plan.steps) >= 2
    tools = [s.tool for s in plan.steps]
    assert "read_file" in tools
    assert "write_file" in tools
    assert all(s.status == PlanStepStatus.PENDING for s in plan.steps)


def test_fix_bug_goal_includes_reproduce_and_verify():
    planner = Planner()
    plan = planner.create_plan("Fix the bug in module.py that crashes on import")
    descriptions = " ".join(s.description for s in plan.steps)
    assert "bug" in descriptions.lower() or "Reproduce" in descriptions
    assert any(s.tool == "run_command" for s in plan.steps)
    assert any(s.tool in ("read_file", "replace_file_content") for s in plan.steps)


def test_unknown_goal_falls_back_to_sentence_steps():
    planner = Planner()
    plan = planner.create_plan("Refactor the cache. Then document the API.")
    assert len(plan.steps) == 2
    assert all(s.tool == "delegate_task" for s in plan.steps)
    assert plan.steps[0].args["task"].startswith("Refactor the cache")


def test_next_step_walks_in_order_and_marks_running():
    planner = Planner()
    planner.create_plan("Run the tests")
    first = planner.next_step()
    second = planner.next_step()
    assert first is not None and second is not None
    assert first.description != second.description
    assert first.status == PlanStepStatus.RUNNING
    # Second call returned the second step because first is still RUNNING.
    assert second.status == PlanStepStatus.RUNNING


def test_next_step_returns_none_when_plan_finished():
    planner = Planner()
    planner.create_plan("Run the tests")
    while True:
        step = planner.next_step()
        if step is None:
            break
        planner.mark_done(step, result="ok")
    assert planner.plan.done
    assert planner.next_step() is None


def test_mark_done_tracks_progress_and_history():
    planner = Planner()
    plan = planner.create_plan("Run the tests")
    assert plan.progress == 0.0
    step = planner.next_step()
    planner.mark_done(step, result="42 passed")
    assert step.status == PlanStepStatus.DONE
    assert step.result == "42 passed"
    assert plan.progress == 0.5
    assert planner.history and planner.history[0].startswith("done:")


def test_mark_done_rejects_foreign_step():
    planner = Planner()
    planner.create_plan("Run the tests")
    with pytest.raises(ValueError):
        planner.mark_done(Step("rogue", "run_command"))


def test_next_step_requires_a_plan():
    with pytest.raises(RuntimeError):
        Planner().next_step()


def test_replan_inserts_recovery_and_skips_failed_step():
    planner = Planner()
    planner.create_plan("Write the file notes.txt with ideas")
    first = planner.next_step()
    planner.mark_failed(first, "permission denied")
    plan = planner.replan("permission denied on notes.txt")
    tools = [s.tool for s in plan.steps]
    assert "update_status" in tools  # diagnosis step present
    assert first.status == PlanStepStatus.SKIPPED
    # The remaining original steps are preserved after the recovery block.
    remaining = plan.steps[plan.steps.index(first) + 1:]
    assert any(s.tool == "write_file" for s in remaining)


def test_replan_with_nothing_remaining_adds_diagnosis():
    planner = Planner()
    planner.create_plan("Run the tests")
    step = planner.next_step()
    planner.mark_done(step)
    planner.mark_done(planner.next_step())
    plan = planner.replan("late failure after completion")
    assert any(s.tool == "update_status" and "Diagnose" in s.description
               for s in plan.steps)


def test_step_status_enum_values():
    assert {s.value for s in PlanStepStatus} == {
        "pending", "running", "done", "failed", "skipped"}


def test_empty_plan_is_done():
    assert Plan(goal="nothing").done is True
    assert Plan(goal="nothing").progress == 1.0
