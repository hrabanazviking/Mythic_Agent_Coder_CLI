"""M-120 — Part V gate.

TIER: integration

The Part V gate (``mythic_agent/data/part5_gate.yaml`` +
``mythic_agent.core.part5_gate``): an overnight-style
autonomous run on a benchmark-pack-style task under
Trusted Forge — sandbox on, budgets on, audit trail
complete, zero doctrine violations — evidence banked
against the M-119 confirmation suite.

These tests do not take the record's word for any of it:

* the gate record loads and validates, its slices are
  M-095..M-119 with titles matching the roadmap data, and
  its baseline is the M-119 confirmation suite's counted
  totals,
* the overnight run is RE-PROVEN LIVE on a real throwaway
  repo through the shipped Part V pure roads: the posture
  is the real Trusted Forge (M-095 ``stored_profile``),
  the grading command's confinement plan is built by
  M-097's ``build_confinement_plan`` on Linux with the
  network denied (and a docker launch refused), the seed
  is graded and fails, the shipped solution is applied,
  and the repo is graded again and passes in full,
* the budget is RE-PROVEN LIVE: M-107's ``judge_budget``
  judges a usage reading built from the run's own counted
  commands within the record's limits,
* the audit trail is RE-PROVEN LIVE: M-109's
  ``AuditRegistry`` holds the run's six acts in the
  record's named order and ``export_trail`` exports them
  complete, every kind counted,
* doctrine is RE-PROVEN LIVE: M-111's ``judge_command``
  judges the run's grading command unclassified and
  ask-once (covered by the human approval recorded
  first), and the exercise's named destructive command
  irreversible — held, never executed, its target still
  standing; zero violations,
* the honesty bounds hold: the evidence kind is
  pure-roads-measured — every step rides a real shipped
  pure road, nothing is faked, no model is run, and the
  campaign tree is never the exercise repo.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

from mythic_agent.core.part5_gate import (
    BASELINE_RESOURCE,
    EXERCISE_IDS,
    GATE_SLICE,
    PLAIN_EXPLANATION,
    Gate,
    apply_solution,
    gate_record,
    grade_exercise,
    load_gate,
    materialise_exercise,
    plain_words,
    render_markdown,
    validate_gate,
    verify_run,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource


@pytest.fixture(scope="module")
def gate() -> Gate:
    return load_gate()


def test_shipped_gate_loads_and_validates(gate):
    assert isinstance(gate, Gate)
    assert validate_gate(load_resource("part5_gate.yaml")) == []
    assert gate.gate_slice == GATE_SLICE == "M-120"
    assert gate.part == 5
    assert gate.part_title == "Autonomy & Safety"
    assert gate.verdict == "PASS"
    assert PLAIN_EXPLANATION


def test_slices_cover_part5_in_order(gate):
    assert gate.slice_ids() == tuple(f"M-{n:03d}" for n in range(95, 120))
    road = load_roadmap()
    for ref in gate.slices:
        assert road.slice(ref.slice).title == ref.title, ref.slice
    assert road.part(5).title == gate.part_title
    done_ids = [s.id for s in road.done()]
    assert [f"M-{n:03d}" for n in range(95, 120)] == [
        d for d in done_ids if "M-095" <= d <= "M-119"]
    nxt = road.next_slice()
    assert nxt is not None
    assert nxt.id == "M-120" or nxt.part >= 6


def test_baseline_is_the_m119_confirmation_suite(gate):
    assert gate.baseline_resource == BASELINE_RESOURCE == \
        "m119_confirmation_suite"
    # The M-119 confirmation suite, counted from its on-disk
    # log on the laptop (logs/m119-fullsuite2.log): the 2
    # failures are exactly the long-classified environment
    # cases (tiktoken-premise estimator; PortAudio import).
    assert gate.baseline_totals() == (6104, 6101, 2, 1)


def test_exercise_shape_and_honesty(gate):
    assert gate.exercise_ids() == EXERCISE_IDS == ("overnight_run",)
    assert len(gate.completed_exercises()) == 1
    exercise = gate.exercise("overnight_run")
    assert exercise.status == "completed"
    assert exercise.evidence_kind == "pure-roads-measured"
    assert exercise.evidence
    assert exercise.seed_paths()
    assert exercise.details["profile_id"] == "trusted-forge"
    assert exercise.details["doctrine_violations"] == 0
    assert exercise.details["budget_status"] == "within"
    assert exercise.details["audit_entries"] == len(
        exercise.details["audit_kinds"])
    for sid in exercise.owning_slices:
        assert "M-095" <= sid <= "M-119"


def test_render_markdown_and_record_report_the_gate(gate):
    text = render_markdown(gate)
    assert "PASS" in text
    assert "M-095..M-119" in text
    assert "6104 collected" in text
    for exercise_id in EXERCISE_IDS:
        assert gate.exercise(exercise_id).title in text
    assert "0 doctrine" in plain_words(gate)
    record = gate_record(gate)
    assert record["type"] == "part5_gate"
    assert record["slice"] == "M-120"
    assert record["verdict"] == "PASS"


# ----------------------------------------------------------------------
# The overnight run, re-proven live (M-095/M-097/M-107/M-109/M-111 roads)
# ----------------------------------------------------------------------


def test_overnight_run_reproven_live(gate, tmp_path):
    from mythic_agent.core.audit_trail import (
        AuditRegistry,
        export_trail,
    )
    from mythic_agent.core.budgets import (
        Budget,
        BudgetUsage,
        judge_budget,
    )
    from mythic_agent.core.destructive_doctrine import judge_command
    from mythic_agent.core.os_sandbox import build_confinement_plan
    from mythic_agent.core.permission_profiles import stored_profile

    exercise = gate.exercise("overnight_run")
    details = exercise.details
    root = tmp_path / "overnight"
    materialise_exercise(exercise, root)

    # The posture is the real Trusted Forge (M-095 road).
    profile = stored_profile({})
    assert profile.id == details["profile_id"] == "trusted-forge"

    # The audit trail opens with the human approval — it
    # covers the run's ask-once commands (M-109 road).
    trail = AuditRegistry()
    trail.append(kind="approval", actor="human",
                 summary="Overnight run approved under Trusted Forge",
                 target="overnight_run")

    # Sandbox on (M-097 road): a confinement plan for the
    # grading command, Linux, network denied; docker refused.
    grading_argv = [sys.executable, "-m", "pytest", "-q", "-p",
                    "no:cacheprovider", "test_grading.py"]
    plan = build_confinement_plan(
        grading_argv, platform=details["sandbox_platform"],
        network=details["sandbox_network"], require_confined=True)
    assert plan.confined is True
    assert plan.network == "deny"
    assert plan.env()["MYTHIC_SANDBOX_NO_NETWORK"] == "1"
    assert list(plan.command) == grading_argv
    with pytest.raises(ValueError):
        build_confinement_plan(["docker", "run", "example.invalid/img"])
    trail.append(kind="tool_call", actor="coder",
                 summary="Built the grading command's confinement plan",
                 target=details["grading_command"])

    # Doctrine judges the run's command before it runs
    # (M-111 road): unclassified, ask-once — covered by the
    # approval already recorded; never claimed safe.
    judged = judge_command(details["grading_command"])
    assert judged.rung is None
    assert judged.classification == "unclassified"
    assert judged.approval == "ask_once"

    # The seed alone does not satisfy the grading tests.
    commands_run = 0
    assert grade_exercise(exercise, root) != (3, 3)
    commands_run += 1
    trail.append(kind="command", actor="coder",
                 summary="Graded the seed repo (fails, as a seed must)",
                 target=details["grading_command"])

    # The run's one edit: the shipped solution lands.
    assert apply_solution(exercise, root) == ("pricing.py",)
    trail.append(kind="edit", actor="coder",
                 summary="Applied the shipped solution to pricing.py",
                 target="pricing.py")

    # The fixed repo passes the hidden grading tests in full.
    assert grade_exercise(exercise, root) == (3, 3)
    commands_run += 1
    trail.append(kind="command", actor="coder",
                 summary="Graded the fixed repo (passes 3/3)",
                 target=details["grading_command"])
    assert commands_run == details["commands_run"] == 2
    assert verify_run(exercise, root) == []

    # Budgets on (M-107 road): a usage reading built from
    # the run's own counted commands — no model ran, so no
    # tokens and no cost — judged within the record's limits.
    verdict = judge_budget(
        Budget(label="overnight", scope="task",
               token_limit=details["budget_token_limit"],
               cost_limit=details["budget_cost_limit"],
               time_limit_seconds=details["budget_time_limit_seconds"],
               command_limit=details["budget_command_limit"]),
        BudgetUsage(commands_used=commands_run))
    assert verdict.status == details["budget_status"] == "within"
    assert verdict.exceeded_dimensions == ()

    # The named destructive command is judged and HELD
    # (M-111 road): irreversible, never executed — its
    # target still stands, and no run command was
    # irreversible or costly. Zero doctrine violations.
    held = judge_command(details["held_command"])
    assert held.rung == details["held_rung"] == "irreversible"
    assert (root / "build" / "keep.txt").is_file()
    violations = sum(
        1 for j in (judged,) if j.rung in ("irreversible", "costly"))
    assert violations == details["doctrine_violations"] == 0

    # The audit trail exports complete (M-109 road): every
    # act in append order, every kind counted.
    trail.append(kind="tool_call", actor="coder",
                 summary="Exported the audit trail for review",
                 target="audit_export")
    export = export_trail(trail)
    assert export["count"] == details["audit_entries"] == 6
    assert [e["kind"] for e in export["entries"]] == \
        list(details["audit_kinds"])
    assert [e["entry_id"] for e in export["entries"]] == \
        [e.entry_id for e in trail.list_entries()]
    assert export["by_kind"] == {
        "tool_call": 2, "approval": 1, "edit": 1, "command": 2}
    assert export["by_actor"]["human"] == 1
    assert export["by_actor"]["coder"] == 5


def test_module_purity():
    import inspect

    import mythic_agent.core.part5_gate as module

    source = inspect.getsource(module)
    assert "from mythic_agent.agents" not in source
    assert "import mythic_agent.agents" not in source


# ----------------------------------------------------------------------
# Validator honesty
# ----------------------------------------------------------------------


def _mutated(mutator):
    data = copy.deepcopy(load_resource("part5_gate.yaml"))
    mutator(data)
    return data


def test_validator_rejects_a_non_pass_verdict():
    data = _mutated(lambda d: d.update(verdict="FAIL"))
    assert any("PASS" in p for p in validate_gate(data))


def test_validator_rejects_a_missing_slice():
    data = _mutated(lambda d: d["slices"].pop())
    assert any("25" in p for p in validate_gate(data))


def test_validator_rejects_an_uncompleted_exercise():
    def spoil(d):
        d["exercises"][0]["status"] = "queued"

    assert any("completed" in p for p in validate_gate(_mutated(spoil)))


def test_validator_rejects_a_doctrine_violation():
    def spoil(d):
        d["exercises"][0]["doctrine_violations"] = 1

    assert any("doctrine_violations" in p
               for p in validate_gate(_mutated(spoil)))


def test_validator_rejects_an_incomplete_audit_trail():
    def spoil(d):
        d["exercises"][0]["audit_kinds"] = ["approval", "command"]
        d["exercises"][0]["audit_entries"] = 2

    assert any("audit" in p for p in validate_gate(_mutated(spoil)))


def test_validator_rejects_sandbox_off():
    def spoil(d):
        d["exercises"][0]["sandbox_network"] = "allow"

    assert any("sandbox" in p for p in validate_gate(_mutated(spoil)))


def test_validator_rejects_broken_baseline_arithmetic():
    def spoil(d):
        d["baseline"]["passed"] = 1

    assert any("arithmetic" in p for p in validate_gate(_mutated(spoil)))


def test_load_raises_on_invalid_data():
    with pytest.raises(ValidationError):
        load_gate({"schema": "nope", "slices": [], "exercises": [],
                   "baseline": {}})
