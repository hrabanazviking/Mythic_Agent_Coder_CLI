"""The Baseline Freeze (All-Features roadmap slice M-007).

The "before" evidence for the whole road, frozen as validated data:
the full-suite count, the startup profile, and the scripted
end-to-end task recording — all measured on the campaign machine on
the freeze date, all re-checkable. Part XI (M-255+) compares its
"after" numbers against this file; nothing in here may be edited to
make a later comparison kinder — a re-freeze is a new slice, never a
quiet edit.

Data lives in ``mythic_agent/data/baseline_freeze.yaml``; the
end-to-end recording itself is ``scripts/baseline_e2e.py`` (stdlib
only, loopback fake provider). This module loads, validates, and
renders the freeze. Validation enforces the honesty rules:

* Suite arithmetic must close: passed + failed + skipped == collected,
  and every counted failure is named in ``known_failures`` (and vice
  versa) — an unnamed failure cannot hide in a total.
* Every known failure carries a classification and an explanation.
* The startup profile carries at least three timed runs, all
  positive, with the context they were measured under stated.
* The end-to-end steps are ``E-01``..``E-NN`` sequential, each with
  the command shape, the expected exit code, and the expected
  outcome the recording script asserts.
"""

from __future__ import annotations

__all__ = [
    "FREEZE_RESOURCE",
    "FREEZE_SCHEMA",
    "Any",
    "BaselineFreeze",
    "Dict",
    "E2EStep",
    "List",
    "Optional",
    "StartupProfile",
    "SuiteResult",
    "load_freeze",
    "render_markdown",
    "validate_freeze",
]

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .validation import ValidationError

#: Resource name of the freeze data file inside ``mythic_agent/data``.
FREEZE_RESOURCE = "baseline_freeze.yaml"

#: The only schema this loader accepts.
FREEZE_SCHEMA = "mythic.baseline_freeze/1"

_ID_RE = re.compile(r"^E-\d{2}$")


@dataclass(frozen=True)
class SuiteResult:
    """The frozen full-suite count."""

    command: str
    collected: int
    passed: int
    failed: int
    skipped: int
    duration_s: float
    log: str


@dataclass(frozen=True)
class StartupProfile:
    """Timed CLI startup runs, with their measurement context."""

    command: str
    runs_s: Tuple[float, ...]
    context: str

    def median_s(self) -> float:
        ordered = sorted(self.runs_s)
        mid = len(ordered) // 2
        if len(ordered) % 2:
            return ordered[mid]
        return round((ordered[mid - 1] + ordered[mid]) / 2, 3)


@dataclass(frozen=True)
class E2EStep:
    """One scripted end-to-end step and the outcome it must produce."""

    id: str
    name: str
    command: str
    expected_exit: int
    expected: str


@dataclass(frozen=True)
class BaselineFreeze:
    """The validated baseline freeze: suite + startup + e2e recording."""

    frozen: str
    base_commit: str
    environment: str
    suite: SuiteResult
    known_failures: Tuple[Tuple[str, str, str], ...]
    startup: StartupProfile
    e2e_script: str
    e2e_steps: Tuple[E2EStep, ...]

    def suite_totals(self) -> Tuple[int, int, int, int]:
        """(collected, passed, failed, skipped), as counted at the freeze."""
        s = self.suite
        return (s.collected, s.passed, s.failed, s.skipped)

    def failure_names(self) -> Tuple[str, ...]:
        """The named known failures, in freeze order."""
        return tuple(name for name, _, _ in self.known_failures)


def validate_freeze(data: Any) -> List[str]:
    """Return a list of human-readable problems with freeze *data*."""
    problems: List[str] = []
    if not isinstance(data, dict):
        return [f"freeze root must be a mapping, got {type(data).__name__}"]
    if data.get("schema") != FREEZE_SCHEMA:
        problems.append(
            f"schema must be {FREEZE_SCHEMA!r}, got {data.get('schema')!r}"
        )
    for key in ("frozen", "base_commit", "environment", "e2e_script"):
        if not isinstance(data.get(key), str) or not data[key]:
            problems.append(f"{key} must be a non-empty string")

    suite = data.get("suite")
    if not isinstance(suite, dict):
        problems.append("suite must be a mapping")
        suite = {}
    counts: Dict[str, int] = {}
    for key in ("collected", "passed", "failed", "skipped"):
        value = suite.get(key)
        if not isinstance(value, int) or value < 0:
            problems.append(f"suite.{key} must be a non-negative integer")
        else:
            counts[key] = value
    if len(counts) == 4 and (
        counts["passed"] + counts["failed"] + counts["skipped"] != counts["collected"]
    ):
        problems.append(
            "suite arithmetic does not close: passed + failed + skipped "
            f"({counts['passed'] + counts['failed'] + counts['skipped']}) "
            f"!= collected ({counts['collected']})"
        )
    if not isinstance(suite.get("command"), str) or not suite.get("command"):
        problems.append("suite.command must be a non-empty string")
    if not isinstance(suite.get("log"), str) or not suite.get("log"):
        problems.append("suite.log must be a non-empty string")
    duration = suite.get("duration_s")
    if not isinstance(duration, (int, float)) or duration <= 0:
        problems.append("suite.duration_s must be a positive number")

    failures = data.get("known_failures")
    if not isinstance(failures, list):
        problems.append("known_failures must be a list")
        failures = []
    if len(counts) == 4 and len(failures) != counts["failed"]:
        problems.append(
            f"known_failures must name every counted failure: "
            f"{len(failures)} named, suite failed = {counts.get('failed')}"
        )
    seen: set = set()
    for entry in failures:
        if not isinstance(entry, dict):
            problems.append(f"known failure is not a mapping: {entry!r}")
            continue
        for key in ("test", "classification", "explanation"):
            if not isinstance(entry.get(key), str) or not entry[key]:
                problems.append(f"known failure {entry.get('test')!r}: {key} must be non-empty")
        name = entry.get("test")
        if isinstance(name, str):
            if name in seen:
                problems.append(f"known failure {name!r} is named twice")
            seen.add(name)

    startup = data.get("startup")
    if not isinstance(startup, dict):
        problems.append("startup must be a mapping")
        startup = {}
    runs = startup.get("runs_s")
    if not isinstance(runs, list) or len(runs) < 3:
        problems.append("startup.runs_s must list at least three timed runs")
    elif any(not isinstance(r, (int, float)) or r <= 0 for r in runs):
        problems.append("startup.runs_s must all be positive numbers")
    for key in ("command", "context"):
        if not isinstance(startup.get(key), str) or not startup.get(key):
            problems.append(f"startup.{key} must be a non-empty string")

    steps = data.get("e2e_steps")
    if not isinstance(steps, list) or not steps:
        problems.append("e2e_steps must be a non-empty list")
        return problems
    for position, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            problems.append(f"e2e step is not a mapping: {step!r}")
            continue
        sid = step.get("id")
        expected = f"E-{position:02d}"
        if not isinstance(sid, str) or not _ID_RE.match(sid):
            problems.append(f"e2e step {sid!r}: id must look like 'E-01'")
        elif sid != expected:
            problems.append(
                f"e2e step {sid}: ids must be sequential, expected {expected}"
            )
        for key in ("name", "command", "expected"):
            if not isinstance(step.get(key), str) or not step[key]:
                problems.append(f"e2e step {sid}: {key} must be non-empty")
        if not isinstance(step.get("expected_exit"), int):
            problems.append(f"e2e step {sid}: expected_exit must be an integer")
    return problems


def _to_freeze(data: Dict[str, Any]) -> BaselineFreeze:
    suite = data["suite"]
    startup = data["startup"]
    return BaselineFreeze(
        frozen=data["frozen"],
        base_commit=data["base_commit"],
        environment=data["environment"],
        suite=SuiteResult(
            command=suite["command"],
            collected=suite["collected"],
            passed=suite["passed"],
            failed=suite["failed"],
            skipped=suite["skipped"],
            duration_s=float(suite["duration_s"]),
            log=suite["log"],
        ),
        known_failures=tuple(
            (f["test"], f["classification"], f["explanation"])
            for f in data["known_failures"]
        ),
        startup=StartupProfile(
            command=startup["command"],
            runs_s=tuple(float(r) for r in startup["runs_s"]),
            context=startup["context"],
        ),
        e2e_script=data["e2e_script"],
        e2e_steps=tuple(
            E2EStep(
                id=s["id"],
                name=s["name"],
                command=s["command"],
                expected_exit=s["expected_exit"],
                expected=s["expected"],
            )
            for s in data["e2e_steps"]
        ),
    )


def load_freeze(data: Optional[Dict[str, Any]] = None) -> BaselineFreeze:
    """Load and validate the shipped baseline freeze (or *data*).

    Raises :class:`~mythic_agent.core.validation.ValidationError`
    listing every problem when the data is not a well-formed freeze.
    """
    raw = data if data is not None else load_resource(FREEZE_RESOURCE)
    problems = validate_freeze(raw)
    if problems:
        raise ValidationError(
            "baseline freeze failed validation: " + "; ".join(problems)
        )
    return _to_freeze(raw)  # type: ignore[arg-type]


def render_markdown(freeze: BaselineFreeze) -> str:
    """Render the freeze as markdown: suite, failures, startup, steps.

    Built from :meth:`BaselineFreeze.suite_totals`,
    :meth:`BaselineFreeze.failure_names`, and
    :meth:`StartupProfile.median_s`, so the rendered page itself is
    computed from the same accessors the tests pin.
    """
    collected, passed, failed, skipped = freeze.suite_totals()
    lines = [
        "# Baseline Freeze — the \"before\" evidence (M-007)",
        "",
        f"*Frozen {freeze.frozen} at {freeze.base_commit}. "
        "Part XI compares against this page.*",
        "",
        freeze.environment,
        "",
        "## Full suite",
        "",
        f"- Command: `{freeze.suite.command}`",
        f"- Collected {collected}: **{passed} passed, {failed} failed, "
        f"{skipped} skipped** in {freeze.suite.duration_s}s",
        f"- Log: `{freeze.suite.log}`",
        "",
        "## Known failures (every counted failure, named)",
        "",
    ]
    explanations = {name: (cls, why) for name, cls, why in freeze.known_failures}
    for name in freeze.failure_names():
        cls, why = explanations[name]
        lines.append(f"- `{name}` — {cls}: {why}")
    lines += [
        "",
        "## Startup profile",
        "",
        f"- Command: `{freeze.startup.command}`",
        f"- Runs (s): {', '.join(str(r) for r in freeze.startup.runs_s)}",
        f"- Median: {freeze.startup.median_s()}s",
        f"- Context: {freeze.startup.context}",
        "",
        "## Scripted end-to-end task",
        "",
        f"Recording script: `{freeze.e2e_script}` (loopback fake provider; "
        "no network, no key). Steps:",
        "",
    ]
    for step in freeze.e2e_steps:
        lines.append(
            f"- {step.id} **{step.name}** — `{step.command}` → "
            f"exit {step.expected_exit}: {step.expected}"
        )
    lines.append("")
    return "\n".join(lines)
