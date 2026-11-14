"""M-232 - Part IX gate.

TIER: integration

The Part IX gate (``mythic_agent/data/part9_gate.yaml`` +
``mythic_agent.core.part9_gate``): this roadmap's own
Part II executed by the Method Engine itself from
campaign file to banked slices - the method proves
itself on its own birth - evidence banked against the
M-231 confirmation suite.

These tests do not take the record's word for any of it:

* the gate record loads and validates, its slices are
  M-201..M-231 with titles matching the roadmap data, its
  layers are M-201..M-231, and its baseline is the M-231
  confirmation suite's counted totals,
* the layers are RE-PROVEN LIVE: every layer row's own
  module imports and its own slice constant names the
  row's slice,
* the campaign is RE-PROVEN LIVE through the roadmap:
  every recorded campaign slice M-019..M-042 stands
  done in Part II of the shipped roadmap,
* the walk is RE-PROVEN LIVE through the method roads:
  each recorded step's shipped anchor is called and
  reports its own slice standing done in Part IX, and
  the campaign step rides M-201's first citizen over
  this repo's own roadmap,
* the honesty bounds hold: the evidence kind is
  pure-roads-measured - every step rides a real shipped
  pure road at the data level, nothing is faked, no live
  campaign is executed, no slice is built or banked by
  the gate itself, no model is called.
"""

from __future__ import annotations

import copy
from datetime import date

import pytest

from mythic_agent.core.part9_gate import (
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
    return load_resource("part9_gate.yaml")


def test_shipped_gate_loads_and_validates(gate, raw_gate):
    assert isinstance(gate, Gate)
    assert validate_gate(raw_gate) == []
    assert gate.gate_slice == GATE_SLICE == "M-232"
    assert gate.part == 9
    assert gate.part_title == "The Mythic Method Engine"
    assert gate.verdict == "PASS"
    assert PLAIN_EXPLANATION


def test_slices_cover_part9_in_order(gate):
    assert gate.slice_ids() == SLICE_IDS == tuple(
        f"M-{n:03d}" for n in range(201, 232))
    road = load_roadmap()
    for ref in gate.slices:
        assert road.slice(ref.slice).title == ref.title, ref.slice
    assert road.part(9).title == gate.part_title
    done_ids = [s.id for s in road.done()]
    assert [f"M-{n:03d}" for n in range(201, 232)] == [
        d for d in done_ids if "M-201" <= d <= "M-231"]
    nxt = road.next_slice()
    assert nxt is not None
    assert nxt.id == "M-272"


def test_baseline_is_the_m231_confirmation_suite(gate):
    assert gate.baseline_resource == BASELINE_RESOURCE == \
        "m231_confirmation_suite"
    # The M-231 confirmation suite, counted from its on-disk
    # log on the laptop (logs/m231-fullsuite-conf.log): the 2
    # failures are exactly the long-classified environment
    # cases (tiktoken-premise estimator; PortAudio import).
    assert gate.baseline_totals() == (11480, 11477, 2, 1)


def test_layers_close_over_every_method_slice(gate):
    import importlib

    assert gate.layer_slice_ids() == LAYER_SLICE_IDS == tuple(
        f"M-{n:03d}" for n in range(201, 232))
    for row in gate.layers:
        module = importlib.import_module(
            f"mythic_agent.core.{row.module}")
        assert getattr(module, row.constant) == row.slice, row.slice


def test_exercise_shape_and_honesty(gate):
    assert gate.exercise_ids() == EXERCISE_IDS == ("method_replay",)
    exercise = gate.exercise("method_replay")
    assert exercise.status == "completed"
    assert gate.completed_exercises() == (exercise,)
    assert exercise.evidence_kind == "pure-roads-measured"
    assert exercise.owning_slices == (
        "M-201", "M-203", "M-204", "M-205", "M-206")
    assert exercise.campaign_part == 2
    assert exercise.campaign_title == "The Provider Ocean"
    assert exercise.campaign_file == "roadmap_slices.yaml"
    assert exercise.campaign_slice_ids == tuple(
        f"M-{n:03d}" for n in range(19, 43))
    assert exercise.campaign_count() == 24
    assert exercise.banked_count == 24
    assert exercise.step_ids() == (
        "step-campaign", "step-slice", "step-build",
        "step-gate", "step-bank")
    assert date.fromisoformat(exercise.executed_on)
    with pytest.raises(KeyError):
        gate.exercise("no_such_exercise")


def test_campaign_reproven_live_through_the_roadmap(gate):
    exercise = gate.exercise("method_replay")
    road = load_roadmap()
    part = road.part(exercise.campaign_part)
    assert part.title == exercise.campaign_title
    assert part.first_slice == exercise.campaign_slice_ids[0]
    assert part.last_slice == exercise.campaign_slice_ids[-1]
    done_ids = {s.id for s in road.done()}
    for slice_id in exercise.campaign_slice_ids:
        entry = road.slice(slice_id)
        assert entry.part == exercise.campaign_part, slice_id
        assert entry.status == "done", slice_id
        assert slice_id in done_ids, slice_id


def test_steps_reproven_live_through_the_method_roads(gate):
    import importlib

    exercise = gate.exercise("method_replay")
    road = load_roadmap()
    for step in exercise.steps:
        module = importlib.import_module(
            f"mythic_agent.core.{step.module}")
        anchor = getattr(module, step.anchor)
        record = anchor()
        assert record["slice"] == step.slice, step.step_id
        assert record["parts"] == 11, step.step_id
        assert record["slices"] == 272, step.step_id
        key = f"m{step.slice[2:]}_title"
        assert record[key] == road.slice(step.slice).title, step.step_id
        status_key = f"m{step.slice[2:]}_status"
        assert record[status_key] == "done", step.step_id


def test_campaign_step_reproven_live_through_m201(gate):
    from mythic_agent.core.campaigns import first_citizen_record

    citizen = first_citizen_record()
    assert citizen["campaign_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["m201_title"] == "Campaigns as data"
    assert citizen["m201_part"] == 9
    assert citizen["m201_status"] == "done"


def test_render_and_record(gate):
    record = gate_record(gate)
    assert record["type"] == "part9_gate"
    assert record["slice"] == "M-232"
    assert record["part"] == 9
    assert record["verdict"] == "PASS"
    assert record["baseline"] == [11480, 11477, 2, 1]
    assert record["exercises"] == ["method_replay"]
    page = render_markdown(gate)
    assert "Part IX Gate - The Mythic Method Engine (M-232)" in page
    assert "24 of 24 campaign slices banked" in page
    assert "11480 collected" in page
    assert "1 of 1 exercises completed" in page
    assert "Method Engine itself" in plain_words(gate)


def test_gate_core_imports_no_service_layer():
    import pathlib

    import mythic_agent.core.part9_gate as module

    source = pathlib.Path(module.__file__).read_text(encoding="utf-8")
    for name in ("campaigns", "slicing_engine", "juggernaut_loop",
                 "acceptance_gates", "banking_discipline"):
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


def test_validator_rejects_a_missing_slice(raw_gate):
    def drop(data):
        data["slices"] = data["slices"][:-1]

    problems = _problems(raw_gate, drop)
    assert any("31" in p for p in problems)


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


def test_validator_rejects_owning_slice_outside_part9(raw_gate):
    def stray(data):
        data["exercises"][0]["owning_slices"] = ["M-042"]

    problems = _problems(raw_gate, stray)
    assert any("Part IX" in p for p in problems)


def test_validator_rejects_wrong_campaign_part(raw_gate):
    def bend(data):
        data["exercises"][0]["campaign_part"] = 3

    problems = _problems(raw_gate, bend)
    assert any("Part II" in p for p in problems)


def test_validator_rejects_reordered_campaign(raw_gate):
    def swap(data):
        ids = data["exercises"][0]["campaign_slice_ids"]
        ids[0], ids[1] = ids[1], ids[0]

    problems = _problems(raw_gate, swap)
    assert any("campaign" in p and "roadmap order" in p for p in problems)


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


def test_validator_rejects_unclosed_banked_count(raw_gate):
    def short(data):
        data["exercises"][0]["banked_count"] = 23

    problems = _problems(raw_gate, short)
    assert any("banked count" in p for p in problems)


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
