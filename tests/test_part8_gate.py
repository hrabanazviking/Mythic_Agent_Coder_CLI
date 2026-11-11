"""M-200 - Part VIII gate.

TIER: integration

The Part VIII gate (``mythic_agent/data/part8_gate.yaml`` +
``mythic_agent.core.part8_gate``): the Stranger Test - a new
user, docs only, completes a real task in the TUI inside
thirty minutes; every stumble is a fix or a doc correction
before the gate passes - evidence banked against the M-199
confirmation suite.

These tests do not take the record's word for any of it:

* the gate record loads and validates, its slices are
  M-171..M-199 with titles matching the roadmap data, its
  layers are M-171..M-199, and its baseline is the M-199
  confirmation suite's counted totals,
* the layers are RE-PROVEN LIVE: every layer row's own
  module imports and its own slice constant names the
  row's slice,
* the walk is RE-PROVEN LIVE through M-184: the recorded
  walk is exactly the shipped onboarding walk, step for
  step, its success standing before its configuration,
* the questions are RE-PROVEN LIVE through M-186: each
  recorded question is answered by exactly the doc the
  record names, with no gaps, and a question the docs
  cannot answer honestly reports its gap,
* the error is RE-PROVEN LIVE through M-183: the recorded
  error builds whole in the shipped shape, stands with
  no gaps, and its plain telling is its own fields,
* the honesty bounds hold: the evidence kind is
  pure-roads-measured - every step rides a real shipped
  pure road at the data level, nothing is faked, no live
  stranger is run, no live session is started, no model
  is called, and the campaign tree is never the exercise
  repo.
"""

from __future__ import annotations

import copy
from datetime import date

import pytest

from mythic_agent.core.part8_gate import (
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
    return load_resource("part8_gate.yaml")


def test_shipped_gate_loads_and_validates(gate, raw_gate):
    assert isinstance(gate, Gate)
    assert validate_gate(raw_gate) == []
    assert gate.gate_slice == GATE_SLICE == "M-200"
    assert gate.part == 8
    assert gate.part_title == "The Beautiful Face"
    assert gate.verdict == "PASS"
    assert PLAIN_EXPLANATION


def test_slices_cover_part8_in_order(gate):
    assert gate.slice_ids() == SLICE_IDS == tuple(
        f"M-{n:03d}" for n in range(171, 200))
    road = load_roadmap()
    for ref in gate.slices:
        assert road.slice(ref.slice).title == ref.title, ref.slice
    assert road.part(8).title == gate.part_title
    done_ids = [s.id for s in road.done()]
    assert [f"M-{n:03d}" for n in range(171, 200)] == [
        d for d in done_ids if "M-171" <= d <= "M-199"]
    nxt = road.next_slice()
    assert nxt is not None
    assert nxt.id == "M-214"


def test_baseline_is_the_m199_confirmation_suite(gate):
    assert gate.baseline_resource == BASELINE_RESOURCE == \
        "m199_confirmation_suite"
    # The M-199 confirmation suite, counted from its on-disk
    # log on the laptop (logs/m199-fullsuite2.log): the 2
    # failures are exactly the long-classified environment
    # cases (tiktoken-premise estimator; PortAudio import).
    assert gate.baseline_totals() == (9907, 9904, 2, 1)


def test_layers_close_over_every_face_slice(gate):
    import importlib

    assert gate.layer_slice_ids() == LAYER_SLICE_IDS == tuple(
        f"M-{n:03d}" for n in range(171, 200))
    for row in gate.layers:
        module = importlib.import_module(
            f"mythic_agent.core.{row.module}")
        assert getattr(module, row.constant) == row.slice, row.slice


def test_exercise_shape_and_honesty(gate):
    assert gate.exercise_ids() == EXERCISE_IDS == ("stranger_test",)
    exercise = gate.exercise("stranger_test")
    assert exercise.status == "completed"
    assert gate.completed_exercises() == (exercise,)
    assert exercise.evidence_kind == "pure-roads-measured"
    assert exercise.owning_slices == ("M-183", "M-184", "M-186")
    assert exercise.guidance == "docs only"
    assert exercise.limit_minutes == 30
    assert 0 < exercise.elapsed_minutes <= exercise.limit_minutes
    assert date.fromisoformat(exercise.walked_on)
    assert exercise.question_count() == 3
    assert set(exercise.stumble_kinds()) == {"fix", "doc-correction"}
    with pytest.raises(KeyError):
        gate.exercise("no_such_exercise")


def test_walk_reproven_live_through_m184(gate):
    from mythic_agent.core.onboarding_five import (
        derive_walk,
        load_onboarding_five,
    )

    exercise = gate.exercise("stranger_test")
    walk = derive_walk(load_onboarding_five())
    assert tuple(step.step_id for step in walk.steps) == \
        exercise.walk_step_ids == (
            "step-detect", "step-walk", "step-success",
            "step-offer", "step-configure")
    assert walk.success_seq == 3
    assert walk.configure_seq == 5
    assert walk.success_seq < walk.configure_seq
    assert walk.passes()


def test_questions_reproven_live_through_m186(gate):
    from mythic_agent.core.help_answers import (
        derive_answer,
        load_help_answers,
    )

    exercise = gate.exercise("stranger_test")
    book = load_help_answers()
    for entry in exercise.questions:
        answer = derive_answer(book, entry.question)
        assert answer.matched == (entry.doc_id,), entry.question
        assert answer.gaps == ()
    unanswered = derive_answer(book, "zxqv wjkl")
    assert unanswered.matched == ()
    assert unanswered.gaps == ("no local doc",)


def test_error_reproven_live_through_m183(gate):
    from mythic_agent.core.error_kindness import (
        build_error,
        error_gaps,
        error_plain_words,
    )

    exercise = gate.exercise("stranger_test")
    built = build_error(exercise.error.mapping())
    assert built.error_id == exercise.error.error_id
    assert built.kind == exercise.error.kind == "broken"
    assert tuple(built.trace) == exercise.error.trace
    assert error_gaps(built) == ()
    telling = error_plain_words(built)
    assert exercise.error.happened in telling
    assert exercise.error.meaning in telling
    assert exercise.error.fix in telling


def test_render_and_record(gate):
    record = gate_record(gate)
    assert record["type"] == "part8_gate"
    assert record["slice"] == "M-200"
    assert record["part"] == 8
    assert record["verdict"] == "PASS"
    assert record["baseline"] == [9907, 9904, 2, 1]
    assert record["exercises"] == ["stranger_test"]
    page = render_markdown(gate)
    assert "Part VIII Gate - The Beautiful Face (M-200)" in page
    assert "24 of 30 minutes" in page
    assert "3 questions answered" in page
    assert "9907 collected" in page
    assert "1 of 1 exercises completed" in page
    assert "docs only" in plain_words(gate)


def test_gate_core_imports_no_service_layer():
    import pathlib

    import mythic_agent.core.part8_gate as module

    source = pathlib.Path(module.__file__).read_text(encoding="utf-8")
    for name in ("onboarding_five", "help_answers", "error_kindness"):
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
    assert any("29" in p for p in problems)


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


def test_validator_rejects_guidance_beyond_docs(raw_gate):
    def guide(data):
        data["exercises"][0]["guidance"] = "a helper at the elbow"

    problems = _problems(raw_gate, guide)
    assert any("docs only" in p for p in problems)


def test_validator_rejects_over_time(raw_gate):
    def slow(data):
        data["exercises"][0]["elapsed_minutes"] = 31

    problems = _problems(raw_gate, slow)
    assert any("thirty" in p for p in problems)


def test_validator_rejects_reordered_walk(raw_gate):
    def swap(data):
        steps = data["exercises"][0]["walk_step_ids"]
        steps[0], steps[1] = steps[1], steps[0]

    problems = _problems(raw_gate, swap)
    assert any("walk" in p for p in problems)


def test_validator_rejects_unanswered_question(raw_gate):
    def blank(data):
        data["exercises"][0]["questions"][0]["doc_id"] = ""

    problems = _problems(raw_gate, blank)
    assert any("must name the local doc" in p for p in problems)


def test_validator_rejects_error_without_trace(raw_gate):
    def strip(data):
        data["exercises"][0]["error"]["trace"] = []

    problems = _problems(raw_gate, strip)
    assert any("trace" in p for p in problems)


def test_validator_rejects_stumble_without_a_fix(raw_gate):
    def note(data):
        data["exercises"][0]["stumbles"][0]["resolution_kind"] = "noted"

    problems = _problems(raw_gate, note)
    assert any("fix or a doc correction" in p for p in problems)


def test_validator_rejects_stumble_merely_noted(raw_gate):
    def blank(data):
        data["exercises"][0]["stumbles"][0]["resolution"] = ""

    problems = _problems(raw_gate, blank)
    assert any("merely noted" in p for p in problems)


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
