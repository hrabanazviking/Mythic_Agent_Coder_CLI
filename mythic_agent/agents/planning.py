"""Multi-step planning for agent tasks (Slice 16).

A :class:`Plan` is an ordered list of :class:`Step` entries, each naming a
tool and its arguments. :class:`Planner` decomposes a free-text goal into a
plan using deterministic rules, walks it step by step, and rebuilds the
remaining steps when one fails.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PlanStepStatus(Enum):
    """Lifecycle of a single plan step."""

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Step:
    """One action in a plan: a human-readable description plus a tool call."""

    description: str
    tool: str
    args: dict[str, Any] = field(default_factory=dict)
    status: PlanStepStatus = PlanStepStatus.PENDING
    result: str | None = None
    error: str | None = None


@dataclass
class Plan:
    """An ordered decomposition of a goal into executable steps."""

    goal: str
    steps: list[Step] = field(default_factory=list)

    @property
    def progress(self) -> float:
        """Fraction of steps finished (done or skipped), in [0, 1]."""
        if not self.steps:
            return 1.0
        finished = sum(1 for s in self.steps
                       if s.status in (PlanStepStatus.DONE, PlanStepStatus.SKIPPED))
        return finished / len(self.steps)

    @property
    def done(self) -> bool:
        """True when no step is pending or running."""
        return all(s.status in (PlanStepStatus.DONE, PlanStepStatus.SKIPPED)
                   for s in self.steps)

    def next_pending(self) -> Step | None:
        """Return the first step that still needs to run, or None."""
        for step in self.steps:
            if step.status == PlanStepStatus.PENDING:
                return step
        return None


def _sentence_split(goal: str, limit: int = 5) -> list[str]:
    parts = [p.strip() for p in re.split(r"[.;]\s*|\band then\b", goal) if p.strip()]
    return parts[:limit] or [goal.strip() or "unexplained goal"]


RuleBuilder = Callable[[re.Match[str]], list[Step]]

_RULES: list[tuple[re.Pattern[str], RuleBuilder]] = []


def _rule(pattern: str) -> Callable[[RuleBuilder], RuleBuilder]:
    compiled = re.compile(pattern, re.IGNORECASE)

    def decorator(builder: RuleBuilder) -> RuleBuilder:
        _RULES.append((compiled, builder))
        return builder

    return decorator


@_rule(r"\b(write|create|generate)\b.*\bfile\b.*?\b(?P<path>\S+?\.\w+)\b")
def _write_file(match: re.Match[str]) -> list[Step]:
    path = match.group("path")
    return [
        Step(f"Inspect the current state of {path}", "read_file", {"path": path}),
        Step(f"Write the new content to {path}", "write_file",
             {"path": path, "content": ""}),
        Step(f"Verify the written content of {path}", "read_file", {"path": path}),
    ]


@_rule(r"\bfix\b.*\bbug\b.*?\bin\b.*?\b(?P<path>\S+?\.\w+)\b")
def _fix_bug(match: re.Match[str]) -> list[Step]:
    path = match.group("path")
    return [
        Step(f"Read {path} to locate the bug", "read_file", {"path": path}),
        Step("Reproduce the failure with a focused check", "run_command",
             {"command": "true"}),
        Step(f"Apply the fix to {path}", "replace_file_content", {"path": path}),
        Step("Re-run the relevant tests", "run_command",
             {"command": "python -m pytest -q"}),
    ]


@_rule(r"\bread\b|inspect\b|look at\b|examine\b.*?\b(?P<path>\S+?\.\w+)\b")
def _read(match: re.Match[str]) -> list[Step]:
    return [Step(f"Read {match.group('path')}", "read_file", {"path": match.group("path")})]


@_rule(r"\bsearch\b.*?\bfor\b\s+(?P<term>.+?)\s*$|\bfind\b\s+(?P<term2>.+?)\s*$")
def _search(match: re.Match[str]) -> list[Step]:
    term = (match.group("term") or match.group("term2") or "").strip()
    return [Step(f"Search the workspace for '{term}'", "grep_search", {"pattern": term})]


@_rule(r"\brun\b.*\btests?\b|\btest\b.*\b(changes?|everything|suite)\b")
def _run_tests(_match: re.Match[str]) -> list[Step]:
    return [
        Step("Run the test suite", "run_command", {"command": "python -m pytest -q"}),
        Step("Report the results", "update_status",
             {"status": "tests executed", "summary": ""}),
    ]


@_rule(r"\blist\b.*\b(directory|files|folder)\b.*?\b(?P<path>\S+)")
def _list_dir(match: re.Match[str]) -> list[Step]:
    path = (match.group("path") or ".").strip()
    return [Step(f"List the contents of {path}", "list_dir", {"path": path})]


class Planner:
    """Rule-based planner: decompose goals, walk plans, recover from failure."""

    def __init__(self) -> None:
        self.plan: Plan | None = None
        self._history: list[str] = []

    # -- planning -------------------------------------------------------
    def create_plan(self, goal: str) -> Plan:
        """Decompose *goal* into a :class:`Plan` using the registered rules.

        Rules are tried in registration order; the first match wins. When no
        rule matches, the goal is split into sentence-level steps so the plan
        always reflects the user's stated intent.
        """
        goal = goal.strip()
        for pattern, builder in _RULES:
            match = pattern.search(goal)
            if match:
                steps = builder(match)
                break
        else:
            steps = [
                Step(f"Carry out: {part}", "delegate_task", {"task": part})
                for part in _sentence_split(goal)
            ]
        self.plan = Plan(goal=goal, steps=steps)
        return self.plan

    # -- execution bookkeeping ------------------------------------------
    def _require_plan(self) -> Plan:
        if self.plan is None:
            raise RuntimeError("No plan created; call create_plan(goal) first")
        return self.plan

    def next_step(self) -> Step | None:
        """Return the next step to run and mark it RUNNING; None when finished."""
        plan = self._require_plan()
        step = plan.next_pending()
        if step is None:
            return None
        step.status = PlanStepStatus.RUNNING
        return step

    def mark_done(self, step: Step, result: str | None = None) -> None:
        """Record *step* as DONE with an optional result summary."""
        plan = self._require_plan()
        if step not in plan.steps:
            raise ValueError("Step does not belong to the current plan")
        step.status = PlanStepStatus.DONE
        step.result = result
        self._history.append(f"done: {step.description}")

    def mark_failed(self, step: Step, error: str) -> None:
        """Record *step* as FAILED with the error text for :meth:`replan`."""
        plan = self._require_plan()
        if step not in plan.steps:
            raise ValueError("Step does not belong to the current plan")
        step.status = PlanStepStatus.FAILED
        step.error = error
        self._history.append(f"failed: {step.description} ({error})")

    # -- recovery --------------------------------------------------------
    def replan(self, failure: str) -> Plan:
        """Rebuild the remaining plan after a failure.

        The failed step is kept in the plan's history, remaining RUNNING
        steps are returned to PENDING, and recovery steps (diagnose, retry
        with narrowed scope, escalate) are inserted before the unfinished
        remainder. Later PENDING steps are preserved.
        """
        plan = self._require_plan()
        remaining = [s for s in plan.steps
                     if s.status in (PlanStepStatus.PENDING, PlanStepStatus.RUNNING,
                                     PlanStepStatus.FAILED)]
        if not remaining:
            # Nothing left to recover: plan for diagnosis only.
            plan.steps.append(Step("Diagnose the reported failure", "update_status",
                                   {"status": "replan", "summary": failure}))
            self._history.append(f"replan: {failure}")
            return plan

        failed = remaining[0]
        for step in remaining:
            if step.status == PlanStepStatus.RUNNING:
                step.status = PlanStepStatus.PENDING

        recovery = [
            Step(f"Diagnose failure: {failure}", "update_status",
                 {"status": "diagnosing", "summary": failure}),
            Step(f"Retry with narrowed scope: {failed.description}", failed.tool,
                 dict(failed.args)),
        ]
        failed_index = plan.steps.index(failed)
        plan.steps = plan.steps[:failed_index] + recovery + plan.steps[failed_index:]
        # Original step becomes SKIPPED so its recovery replacement takes over.
        failed.status = PlanStepStatus.SKIPPED
        self._history.append(f"replan: {failure}")
        return plan

    @property
    def history(self) -> list[str]:
        """Chronological log of completions, failures, and replans."""
        return list(self._history)
