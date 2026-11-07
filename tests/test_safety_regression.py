"""M-117 - Safety regression suite.

TIER: integration

The Part V safety regression gate
(``mythic_agent/data/safety_regression.yaml`` +
``mythic_agent.core.safety_regression``): every
doctrine rule shipped by the Part V safety slices
M-103..M-116 held as one named rule, each rule
naming the shipped module that carries it and the
exact tests that pin it, banked against the M-116
confirmation suite.

These tests do not take the record's word for any
of it:

* the gate record loads and validates, its slices
  are M-103..M-116 with titles matching the roadmap
  data, and its baseline is the M-116 confirmation
  suite's counted totals,
* every rule's named pinning tests truly exist in
  its named test file, and every rule's named module
  truly imports, states its own slice, and explains
  itself in plain words - a rule whose pins are gone
  fails here, which is what makes the suite a gate
  and not documentation,
* the sharpest doctrines are RE-PROVEN LIVE against
  the shipped pure roads: a bare yes/no approval is
  judged incomplete (M-116), an unknown command is
  unclassified and never safe (M-111), and a secret
  shape is redacted and never echoed (M-110),
* the honesty bounds hold: the validator accepts no
  verdict but PASS, refuses a slice with no rule, a
  rule with no pinning test, a duplicated rule id,
  and a baseline that does not close arithmetically.
"""

from __future__ import annotations

import copy
import importlib
from pathlib import Path

import pytest

from mythic_agent.core.safety_regression import (
    BASELINE_RESOURCE,
    EVIDENCE_KIND,
    GATE_RESOURCE,
    GATE_SLICE,
    PLAIN_EXPLANATION,
    RULE_IDS,
    SLICE_IDS,
    Gate,
    format_gate_screen,
    format_rule,
    format_rules,
    gate_record,
    load_gate,
    plain_words,
    render_markdown,
    validate_gate,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Each gated slice's module stem and the slice constant it states.
SLICE_CONSTANTS = {
    "M-103": ("background_tasks", "BACKGROUND_TASKS_SLICE"),
    "M-104": ("keeper", "KEEPER_SLICE"),
    "M-105": ("scheduled_work", "SCHEDULED_WORK_SLICE"),
    "M-106": ("fleet_mode", "FLEET_MODE_SLICE"),
    "M-107": ("budgets", "BUDGETS_SLICE"),
    "M-108": ("kill_switch", "KILL_SWITCH_SLICE"),
    "M-109": ("audit_trail", "AUDIT_TRAIL_SLICE"),
    "M-110": ("secret_hygiene", "SECRET_HYGIENE_SLICE"),
    "M-111": ("destructive_doctrine", "DESTRUCTIVE_DOCTRINE_SLICE"),
    "M-112": ("rollback_drills", "ROLLBACK_DRILLS_SLICE"),
    "M-113": ("multi_repo", "MULTI_REPO_SLICE"),
    "M-114": ("remote_work", "REMOTE_WORK_SLICE"),
    "M-115": ("offline_grace", "OFFLINE_GRACE_SLICE"),
    "M-116": ("approval_moments", "APPROVAL_MOMENTS_SLICE"),
}


@pytest.fixture(scope="module")
def gate() -> Gate:
    return load_gate()


def test_shipped_gate_loads_and_validates(gate):
    assert isinstance(gate, Gate)
    assert validate_gate(load_resource(GATE_RESOURCE)) == []
    assert gate.gate_slice == GATE_SLICE == "M-117"
    assert gate.part == 5
    assert gate.part_title == "Autonomy & Safety"
    assert gate.verdict == "PASS"
    assert PLAIN_EXPLANATION


def test_slices_cover_the_safety_doctrines_in_order(gate):
    assert gate.slice_ids() == SLICE_IDS
    assert SLICE_IDS == tuple(f"M-{n:03d}" for n in range(103, 117))
    road = load_roadmap()
    for ref in gate.slices:
        assert road.slice(ref.slice).title == ref.title, ref.slice
    assert road.part(5).title == gate.part_title
    done_ids = [s.id for s in road.done()]
    assert [f"M-{n:03d}" for n in range(103, 117)] == [
        d for d in done_ids if "M-103" <= d <= "M-116"]


def test_baseline_is_the_m116_confirmation_suite(gate):
    assert gate.baseline_resource == BASELINE_RESOURCE
    assert BASELINE_RESOURCE == "m116_confirmation_suite"
    # The M-116 confirmation suite, counted from its on-disk
    # log on the laptop (logs/m116-fullsuite2.log): the 2
    # failures are exactly the long-classified environment
    # cases (tiktoken-premise estimator; PortAudio import).
    assert gate.baseline_totals() == (6021, 6018, 2, 1)
    collected, passed, failed, skipped = gate.baseline_totals()
    assert collected == passed + failed + skipped


def test_every_slice_carries_exactly_one_rule(gate):
    assert gate.rule_ids() == RULE_IDS
    assert len(gate.rules) == 14
    for slice_id in SLICE_IDS:
        rules = gate.rules_for(slice_id)
        assert len(rules) == 1, slice_id
    # 43 named pinning tests: three per rule, four for the
    # kill switch (R-06), whose doctrine has four clauses.
    assert gate.pin_count() == 43


def test_every_pinning_test_truly_exists(gate):
    for rule in gate.rules:
        test_path = REPO_ROOT / rule.test_file
        assert test_path.is_file(), rule.test_file
        text = test_path.read_text(encoding="utf-8")
        for name in rule.tests:
            assert f"def {name}(" in text, (
                f"{rule.id}: pinning test {name} is gone from "
                f"{rule.test_file} - the doctrine lost its pin")


def test_every_carrier_module_states_its_slice(gate):
    for rule in gate.rules:
        module_path = REPO_ROOT / rule.module
        assert module_path.is_file(), rule.module
        stem, constant = SLICE_CONSTANTS[rule.slice]
        assert rule.module == f"mythic_agent/core/{stem}.py"
        module = importlib.import_module(f"mythic_agent.core.{stem}")
        assert getattr(module, constant) == rule.slice
        assert getattr(module, "PLAIN_EXPLANATION")


def test_rule_lookup_and_unknown_rule(gate):
    rule = gate.rule("R-09")
    assert rule.slice == "M-111"
    assert rule.pin_count() == 3
    with pytest.raises(KeyError):
        gate.rule("R-99")


def test_plain_words_record_and_render(gate):
    words = plain_words(gate)
    assert "M-117" in words
    assert "PASS" in words
    assert "43 named tests" in words
    record = gate_record(gate)
    assert record["type"] == "safety_regression_gate"
    assert record["news"] is True
    assert record["slice"] == "M-117"
    assert record["rules"] == 14
    assert record["pinning_tests"] == 43
    assert record["headline"] == words
    text = render_markdown(gate)
    assert "PASS" in text
    assert "M-103..M-116" in text
    assert "6021 collected" in text
    for rule in gate.rules:
        assert rule.rule in text
    screen = format_gate_screen(gate)
    assert format_rule(gate.rule("R-01")) in screen
    assert format_rules(gate).count("\n") == 13


def test_validator_refuses_a_failed_verdict():
    raw = copy.deepcopy(load_resource(GATE_RESOURCE))
    raw["verdict"] = "FAIL"
    problems = validate_gate(raw)
    assert any("verdict" in p for p in problems)
    with pytest.raises(ValidationError):
        load_gate(raw)


def test_validator_refuses_a_slice_with_no_rule():
    raw = copy.deepcopy(load_resource(GATE_RESOURCE))
    raw["rules"] = [r for r in raw["rules"] if r["slice"] != "M-108"]
    problems = validate_gate(raw)
    assert any("M-108" in p and "no rule" in p for p in problems)


def test_validator_refuses_a_rule_with_no_test():
    raw = copy.deepcopy(load_resource(GATE_RESOURCE))
    raw["rules"][0]["tests"] = []
    problems = validate_gate(raw)
    assert any("no pinning test" in p for p in problems)


def test_validator_refuses_duplicate_and_reordered_rules():
    raw = copy.deepcopy(load_resource(GATE_RESOURCE))
    raw["rules"].append(copy.deepcopy(raw["rules"][0]))
    problems = validate_gate(raw)
    assert any("named twice" in p or "rule ids" in p for p in problems)
    raw = copy.deepcopy(load_resource(GATE_RESOURCE))
    raw["rules"][0], raw["rules"][1] = raw["rules"][1], raw["rules"][0]
    problems = validate_gate(raw)
    assert any("rule ids" in p for p in problems)


def test_validator_refuses_broken_baseline_arithmetic():
    raw = copy.deepcopy(load_resource(GATE_RESOURCE))
    raw["baseline"]["passed"] += 1
    problems = validate_gate(raw)
    assert any("close arithmetically" in p for p in problems)


def test_validator_refuses_wrong_evidence_kind():
    raw = copy.deepcopy(load_resource(GATE_RESOURCE))
    raw["rules"][0]["evidence_kind"] = "documentation"
    problems = validate_gate(raw)
    assert any("evidence_kind" in p for p in problems)
    assert EVIDENCE_KIND == "tests-verified"


# ----------------------------------------------------------------------
# The sharpest doctrines, re-proven live on the shipped pure roads.
# ----------------------------------------------------------------------


def test_live_approval_bare_yes_no_is_never_complete():
    from mythic_agent.core.approval_moments import judge_moment

    assessment = judge_moment({"choices": [
        {"key": "yes"}, {"key": "no"}]})
    assert assessment.state == "incomplete"
    assert "what" in assessment.missing
    assert "choice_effects" in assessment.missing


def test_live_unknown_command_is_unclassified_never_safe():
    from mythic_agent.core.destructive_doctrine import judge_command

    judged = judge_command("frobnicate --all")
    assert judged.rung is None
    assert judged.classification == "unclassified"
    assert judged.needs_approval


def test_live_secret_shape_is_redacted_never_echoed():
    from mythic_agent.core.secret_hygiene import (
        REDACTION_MARKER,
        redact_secrets,
        secret_kinds_in,
    )

    fake = "sk-" + "FAKE0" * 8
    assert secret_kinds_in(f"key is {fake}")
    out = redact_secrets(f"before {fake} after")
    assert out == f"before {REDACTION_MARKER} after"
    assert fake not in out


def test_module_purity():
    import inspect

    import mythic_agent.core.safety_regression as module

    source = inspect.getsource(module)
    assert "import subprocess" not in source
    assert "from mythic_agent.agents" not in source
    assert "import os" not in source.split('"""', 2)[-1]
