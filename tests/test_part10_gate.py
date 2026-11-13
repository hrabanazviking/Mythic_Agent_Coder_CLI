"""M-254 - Part X gate.

TIER: integration

The Part X gate (``mythic_agent/data/part10_gate.yaml`` +
``mythic_agent.core.part10_gate``): one campaign slice
executed across bridges - issue from a host, build
locally, PR raised, stand-up posted to Samtal - with
credentials never leaving Kista - evidence banked
against the M-253 confirmation suite.

These tests do not take the record's word for any of it:

* the gate record loads and validates, its slices are
  M-233..M-253 with titles matching the roadmap data, its
  layers are M-233..M-253, and its baseline is the M-253
  confirmation suite's counted totals,
* the layers are RE-PROVEN LIVE: every layer row's own
  module imports and its own slice constant names the
  row's slice,
* the walk is RE-PROVEN LIVE through the bridge roads:
  each recorded step's shipped anchor is called and
  reports its own slice standing done in Part X,
* the honesty bounds hold: the evidence kind is
  pure-roads-measured - every stage rides a real shipped
  pure road at the data level, nothing is faked, no host
  API is called, no PR is raised, no stand-up is posted
  and no credential is read out of Kista by the gate
  itself.
"""

from __future__ import annotations

import copy
from datetime import date

import pytest

from mythic_agent.core.part10_gate import (
    BASELINE_RESOURCE,
    EXERCISE_IDS,
    GATE_SLICE,
    LAYER_SLICE_IDS,
    PLAIN_EXPLANATION,
    SLICE_IDS,
    Gate,
    gate_record,
    load_gate,
    plain_words,
    render_markdown,
    validate_gate,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource


@pytest.fixture(scope="module")
def gate() -> Gate:
    return load_gate()


@pytest.fixture(scope="module")
def raw_gate() -> dict:
    return load_resource("part10_gate.yaml")


def test_shipped_gate_loads_and_validates(gate, raw_gate):
    assert isinstance(gate, Gate)
    assert validate_gate(raw_gate) == []
    assert gate.gate_slice == GATE_SLICE == "M-254"
    assert gate.part == 10
    assert gate.part_title == "Bridges"
    assert gate.verdict == "PASS"
    assert PLAIN_EXPLANATION


def test_slices_cover_part10_in_order(gate):
    assert gate.slice_ids() == SLICE_IDS == tuple(
        f"M-{n:03d}" for n in range(233, 254))
    road = load_roadmap()
    for ref in gate.slices:
        assert road.slice(ref.slice).title == ref.title, ref.slice
    assert road.part(10).title == gate.part_title
    done_ids = [s.id for s in road.done()]
    assert [f"M-{n:03d}" for n in range(233, 254)] == [
        d for d in done_ids if "M-233" <= d <= "M-253"]
    nxt = road.next_slice()
    assert nxt is not None
    assert nxt.id == "M-254"


def test_baseline_is_the_m253_confirmation_suite(gate):
    assert gate.baseline_resource == BASELINE_RESOURCE == \
        "m253_confirmation_suite"
    # The M-253 confirmation suite, counted from its on-disk
    # log on the laptop (logs/m253-fullsuite-conf.log): the 2
    # failures are exactly the long-classified environment
    # cases (tiktoken-premise estimator; PortAudio import).
    assert gate.baseline_totals() == (12510, 12507, 2, 1)


def test_layers_close_over_every_bridge_slice(gate):
    import importlib

    assert gate.layer_slice_ids() == LAYER_SLICE_IDS == tuple(
        f"M-{n:03d}" for n in range(233, 254))
    for row in gate.layers:
        module = importlib.import_module(
            f"mythic_agent.core.{row.module}")
        assert getattr(module, row.constant) == row.slice, row.slice


def test_exercise_shape_and_honesty(gate):
    assert gate.exercise_ids() == EXERCISE_IDS == ("bridge_campaign",)
    exercise = gate.exercise("bridge_campaign")
    assert exercise.status == "completed"
    assert gate.completed_exercises() == (exercise,)
    assert exercise.evidence_kind == "pure-roads-measured"
    assert exercise.owning_slices == (
        "M-242", "M-233", "M-244", "M-243")
    assert exercise.host_slice == "M-246"
    assert exercise.host_name == "github"
    assert exercise.credential_rule == "credentials-never-leave-kista"
    assert exercise.kista_refs == ("kista:github", "kista:samtal")
    assert exercise.stage_count() == 4
    assert exercise.step_ids() == (
        "step-issue", "step-build", "step-pr",
        "step-standup")
    assert date.fromisoformat(exercise.executed_on)
    with pytest.raises(KeyError):
        gate.exercise("no_such_exercise")


def test_steps_reproven_live_through_the_bridge_roads(gate):
    import importlib

    exercise = gate.exercise("bridge_campaign")
    road = load_roadmap()
    for step in exercise.steps:
        module = importlib.import_module(
            f"mythic_agent.core.{step.module}")
        anchor = getattr(module, step.anchor)
        record = anchor()
        assert record["parts"] == 11, step.step_id
        assert record["slices"] == 272, step.step_id
        key = f"m{step.slice[2:]}_title"
        assert record[key] == road.slice(step.slice).title, step.step_id
        status_key = f"m{step.slice[2:]}_status"
        assert record[status_key] == "done", step.step_id


def test_credential_invariant_rides_the_kista_road(gate):
    from mythic_agent.core.kista_keykeeper import roadmap_record

    exercise = gate.exercise("bridge_campaign")
    pr_step = [s for s in exercise.steps if s.step_id == "step-pr"][0]
    assert pr_step.slice == "M-244"
    assert pr_step.module == "kista_keykeeper"
    record = roadmap_record()
    assert record["m244_status"] == "done"
    assert "kista" in exercise.credential_rule
    for ref in exercise.kista_refs:
        assert ref.startswith("kista:")


def test_render_and_record(gate):
    record = gate_record(gate)
    assert record["type"] == "part10_gate"
    assert record["slice"] == "M-254"
    assert record["part"] == 10
    assert record["verdict"] == "PASS"
    assert record["baseline"] == [12510, 12507, 2, 1]
    assert record["exercises"] == ["bridge_campaign"]
    page = render_markdown(gate)
    assert "Part X Gate - Bridges (M-254)" in page
    assert "credentials never leaving Kista" in page
    assert "12510 collected" in page
    assert "1 of 1 exercises completed" in page
    assert "never leaving Kista" in plain_words(gate)


def test_gate_core_imports_no_service_layer():
    import pathlib

    import mythic_agent.core.part10_gate as module

    source = pathlib.Path(module.__file__).read_text(encoding="utf-8")
    for name in ("samverk_bridge", "mcp_client", "kista_keykeeper",
                 "samtal_bridge", "git_host_parity"):
        assert f"from .{name}" not in source
        assert f"import {name}" not in source
    assert "mythic_agent.agents" not in source
    assert "from ..agents" not in source


def _problems(raw_gate, mutate) -> list:
    data = copy.deepcopy(raw_gate)
    mutate(data)
    return validate_gate(data)


def test_validator_rejects_non_pass_verdict(raw_gate):
    problems = _problems(raw_gate, lambda d: d.update(verdict="FAIL"))
    assert any("verdict" in p and "PASS" in p for p in problems)


def test_validator_rejects_wrong_part(raw_gate):
    problems = _problems(raw_gate, lambda d: d.update(part=9))
    assert any("part must be 10" in p for p in problems)


def test_validator_rejects_a_missing_slice(raw_gate):
    def drop(data):
        data["slices"] = data["slices"][:-1]

    problems = _problems(raw_gate, drop)
    assert any("21" in p for p in problems)


def test_validator_rejects_baseline_arithmetic(raw_gate):
    def bump(data):
        data["baseline"]["passed"] += 1

    problems = _problems(raw_gate, bump)
    assert any("arithmetic" in p for p in problems)


def test_validator_rejects_uncompleted_exercise(raw_gate):
    def pend(data):
        data["exercises"][0]["status"] = "pending"

    problems = _problems(raw_gate, pend)
    assert any("completed" in p for p in problems)


def test_validator_rejects_empty_evidence(raw_gate):
    def blank(data):
        data["exercises"][0]["evidence"] = ""

    problems = _problems(raw_gate, blank)
    assert any("evidence" in p for p in problems)


def test_validator_rejects_owning_slice_outside_part10(raw_gate):
    def stray(data):
        data["exercises"][0]["owning_slices"] = ["M-042"]

    problems = _problems(raw_gate, stray)
    assert any("Part X" in p for p in problems)


def test_validator_rejects_wrong_host_slice(raw_gate):
    def bend(data):
        data["exercises"][0]["host_slice"] = "M-233"

    problems = _problems(raw_gate, bend)
    assert any("host" in p for p in problems)


def test_validator_rejects_credential_leaving_kista(raw_gate):
    def bend(data):
        data["exercises"][0]["credential_rule"] = "keys-travel-with-the-pr"

    problems = _problems(raw_gate, bend)
    assert any("Kista" in p for p in problems)


def test_validator_rejects_wrong_kista_refs(raw_gate):
    def bend(data):
        data["exercises"][0]["kista_refs"] = ["kista:github"]

    problems = _problems(raw_gate, bend)
    assert any("Kista refs" in p for p in problems)


def test_validator_rejects_reordered_steps(raw_gate):
    def swap(data):
        steps = data["exercises"][0]["steps"]
        steps[0], steps[1] = steps[1], steps[0]

    problems = _problems(raw_gate, swap)
    assert any("held order" in p for p in problems)


def test_validator_rejects_wrong_step_anchor(raw_gate):
    def bend(data):
        data["exercises"][0]["steps"][0]["anchor"] = "no_such_road"

    problems = _problems(raw_gate, bend)
    assert any("shipped road" in p for p in problems)


def test_validator_rejects_wrong_layer_road(raw_gate):
    def bend(data):
        data["layers"][0]["constant"] = "WRONG_SLICE"

    problems = _problems(raw_gate, bend)
    assert any("shipped" in p for p in problems)


def test_load_gate_raises_on_invalid_data(raw_gate):
    data = copy.deepcopy(raw_gate)
    data["verdict"] = "FAIL"
    with pytest.raises(ValidationError):
        load_gate(data)
