"""M-170 - Part VII gate.

TIER: integration

The Part VII gate (``mythic_agent/data/part7_gate.yaml`` +
``mythic_agent.core.part7_gate``): a week-old benchmark
session resumed - the coder states the situation correctly
from memory alone, then finishes the task; compaction
glass-box verified mid-run - evidence banked against the
M-169 confirmation suite.

These tests do not take the record's word for any of it:

* the gate record loads and validates, its slices are
  M-147..M-169 with titles matching the roadmap data, its
  layers are M-150..M-169, and its baseline is the M-169
  confirmation suite's counted totals,
* the layers are RE-PROVEN LIVE: every layer row's own
  module imports and its own slice constant names the
  row's slice,
* the situation and statement are RE-PROVEN LIVE through
  M-153: the recorded situation builds whole through
  ``build_situation`` and its derived panel is exactly
  the pieces the statement claims, row for row, each
  row's words the claim's truth,
* the compaction is RE-PROVEN LIVE through M-151:
  ``build_record`` builds it whole, ``derive_panel``
  closes on the record's own counts, and ``edit_record``
  appends the mid-run version without rewriting the
  compaction's own version,
* the handoff is RE-PROVEN LIVE through M-163:
  ``handoff_from_session_situation`` raises the week-old
  handoff over the situation by its references alone,
  its evidence exactly the situation's own ids,
* the honesty bounds hold: the evidence kind is
  pure-roads-measured - every step rides a real shipped
  pure road at the data level, nothing is faked, no live
  session is resumed, no model is called, and the
  campaign tree is never the exercise repo.
"""

from __future__ import annotations

import copy
from datetime import date

import pytest

from mythic_agent.core.part7_gate import (
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


def test_shipped_gate_loads_and_validates(gate):
    assert isinstance(gate, Gate)
    assert validate_gate(load_resource("part7_gate.yaml")) == []
    assert gate.gate_slice == GATE_SLICE == "M-170"
    assert gate.part == 7
    assert gate.part_title == "Memory & Context"
    assert gate.verdict == "PASS"
    assert PLAIN_EXPLANATION


def test_slices_cover_part7_in_order(gate):
    assert gate.slice_ids() == SLICE_IDS == tuple(
        f"M-{n:03d}" for n in range(147, 170))
    road = load_roadmap()
    for ref in gate.slices:
        assert road.slice(ref.slice).title == ref.title, ref.slice
    assert road.part(7).title == gate.part_title
    done_ids = [s.id for s in road.done()]
    assert [f"M-{n:03d}" for n in range(147, 170)] == [
        d for d in done_ids if "M-147" <= d <= "M-169"]
    nxt = road.next_slice()
    assert nxt is not None
    assert nxt.id == "M-186"


def test_baseline_is_the_m169_confirmation_suite(gate):
    assert gate.baseline_resource == BASELINE_RESOURCE == \
        "m169_confirmation_suite"
    # The M-169 confirmation suite, counted from its on-disk
    # log on the laptop (logs/m169-fullsuite2.log): the 2
    # failures are exactly the long-classified environment
    # cases (tiktoken-premise estimator; PortAudio import).
    assert gate.baseline_totals() == (8434, 8431, 2, 1)


def test_layers_close_over_every_memory_slice(gate):
    import importlib

    assert gate.layer_slice_ids() == LAYER_SLICE_IDS == tuple(
        f"M-{n:03d}" for n in range(150, 170))
    for row in gate.layers:
        module = importlib.import_module(
            f"mythic_agent.core.{row.module}")
        assert getattr(module, row.constant) == row.slice, row.slice


def test_exercise_shape_and_honesty(gate):
    assert gate.exercise_ids() == EXERCISE_IDS == ("resumed_benchmark",)
    assert len(gate.completed_exercises()) == 1
    exercise = gate.exercise("resumed_benchmark")
    assert exercise.status == "completed"
    assert exercise.evidence_kind == "pure-roads-measured"
    assert exercise.evidence
    recorded = date.fromisoformat(exercise.recorded_on)
    resumed = date.fromisoformat(exercise.resumed_on)
    assert (resumed - recorded).days == 7
    assert exercise.situation.saved_on == exercise.recorded_on
    assert exercise.situation.transcript_messages == 58
    assert exercise.claim_count() == len(exercise.situation.pieces()) == 7
    assert all(c.stated == c.truth for c in exercise.statement)
    assert exercise.compaction.replaced_count == 3
    assert exercise.compaction.version_count == 2
    assert exercise.compaction.verified_stage == "mid-run"
    assert exercise.grading_at_pause == 9
    assert exercise.grading_passed == exercise.grading_total == 12
    for sid in exercise.owning_slices:
        assert "M-147" <= sid <= "M-169"


def test_render_markdown_and_record_report_the_gate(gate):
    text = render_markdown(gate)
    assert "PASS" in text
    assert "M-147..M-169" in text
    assert "M-150..M-169" in text
    assert "8434 collected" in text
    for exercise_id in EXERCISE_IDS:
        assert gate.exercise(exercise_id).title in text
    words = plain_words(gate)
    assert "7 claims over 7 carried pieces" in words
    assert "12 of 12 grading tests passed" in words
    record = gate_record(gate)
    assert record["type"] == "part7_gate"
    assert record["slice"] == "M-170"
    assert record["verdict"] == "PASS"
    assert record["layers"] == list(LAYER_SLICE_IDS)


# ----------------------------------------------------------------------
# The resumed benchmark, re-proven live (M-151 / M-153 / M-163)
# ----------------------------------------------------------------------


def _situation_mapping(exercise):
    s = exercise.situation
    return {
        "situation_id": s.situation_id,
        "session_ref": s.session_ref,
        "workspace": s.workspace,
        "title": s.title,
        "saved_on": s.saved_on,
        "status": s.status,
        "transcript_messages": s.transcript_messages,
        "memory": [
            {"note_id": n.note_id, "section": n.section,
             "title": n.title, "detail": n.detail,
             "source": n.source, "ref": n.ref} for n in s.memory],
        "open_slices": [
            {"slice_id": w.slice_id, "title": w.title,
             "state": w.state, "note": w.note} for w in s.open_work],
        "decisions": [
            {"decision_id": d.decision_id, "title": d.title,
             "decision": d.decision, "source": d.source}
            for d in s.decisions],
    }


def test_situation_and_statement_reproven_live(gate):
    from mythic_agent.core.session_memory import (
        build_situation,
        derive_panel,
    )

    exercise = gate.exercise("resumed_benchmark")

    # The recorded situation builds whole through the
    # shipped M-153 road, its totals its own pieces' counts.
    situation = build_situation(_situation_mapping(exercise))
    assert situation.session_ref == exercise.situation.session_ref
    assert situation.saved_on == exercise.recorded_on
    assert situation.transcript_messages == 58
    assert (situation.total_memory, situation.total_slices,
            situation.total_decisions) == (3, 2, 2)

    # Its derived panel is exactly the pieces the resumed
    # statement claims - one row per claim, and every row's
    # words are the claim's truth, so the statement is the
    # situation stated correctly from memory alone.
    panel = derive_panel(situation)
    assert panel.total_items == exercise.claim_count() == 7
    assert {(r.kind, r.item_id) for r in panel.rows} == {
        (c.kind, c.item_id) for c in exercise.statement}
    for row in panel.rows:
        claim = next(
            c for c in exercise.statement
            if (c.kind, c.item_id) == (row.kind, row.item_id))
        assert row.title == claim.title
        assert row.detail == claim.truth == claim.stated


def test_compaction_reproven_live(gate):
    from mythic_agent.core.compaction_glassbox import (
        build_record,
        derive_panel,
        edit_record,
    )

    exercise = gate.exercise("resumed_benchmark")
    check = exercise.compaction
    mapping = {
        "record_id": check.record_id, "title": check.title,
        "source": check.source, "journal_ref": check.journal_ref,
        "journal_position": check.journal_position,
        "replaced": list(check.replaced),
        "summary_versions": list(check.summary_versions),
    }

    # The compaction builds whole through the shipped
    # M-151 road: the replaced material kept whole, the
    # summary standing as its versions.
    record = build_record(mapping)
    assert record.replaced == check.replaced
    assert record.replaced_count == check.replaced_count == 3
    assert record.version_count == check.version_count == 2
    assert record.summary == check.summary
    assert record.edited

    # Its panel closes on the record's own counts.
    panel = derive_panel([record])
    assert panel.total_records == 1
    assert panel.total_replaced == check.replaced_count
    assert panel.total_versions == check.version_count

    # The mid-run edit appends a version without rewriting
    # the compaction's own: a record holding only the first
    # version, edited with the second, stands exactly as
    # the gate's record stands - and the first version is
    # untouched by the edit.
    first_only = build_record(
        {**mapping, "summary_versions": [check.summary_versions[0]]})
    edited = edit_record(first_only, check.summary_versions[1])
    assert edited.summary_versions == check.summary_versions
    assert first_only.summary_versions == (check.summary_versions[0],)
    assert edited.summary_versions[0] == check.summary_versions[0]


def test_handoff_reproven_live(gate):
    from mythic_agent.core.handoff_summaries import (
        handoff_from_session_situation,
    )
    from mythic_agent.core.session_memory import build_situation

    exercise = gate.exercise("resumed_benchmark")
    situation = build_situation(_situation_mapping(exercise))

    # The resume began from the week-old handoff: raised
    # over the situation through the shipped M-163 road,
    # it stands by its references alone - its session is
    # the situation's own, its evidence is exactly the
    # ids the situation itself names, and its claims are
    # the record's claims, each standing on that evidence.
    handoff = handoff_from_session_situation(
        situation, project=exercise.handoff_project,
        branch=exercise.handoff_branch, done=exercise.handoff_done,
        doing=exercise.handoff_doing, blocked=exercise.handoff_blocked,
        needs_you=exercise.handoff_needs_you,
        written_by=exercise.handoff_written_by,
        written_on=exercise.handoff_written_on,
        source=exercise.handoff_source, title=exercise.handoff_title)
    assert handoff.session_ref == exercise.situation.session_ref
    assert handoff.written_on == exercise.recorded_on
    assert handoff.evidence_refs == exercise.handoff_evidence_refs
    assert handoff.evidence_refs == exercise.situation.piece_ids()
    assert set(handoff.done + handoff.doing + handoff.blocked
               + handoff.needs_you) == set(exercise.handoff_claim_ids())
    assert handoff.claim_count == len(exercise.handoff_claim_ids()) == 3


def test_module_purity():
    import inspect

    import mythic_agent.core.part7_gate as module

    source = inspect.getsource(module)
    assert "from mythic_agent.agents" not in source
    assert "import mythic_agent.agents" not in source
    # The gate's core imports no service layer at all: the
    # shipped pure roads are wired by these tests, never
    # by the gate module itself.
    assert "from .session_memory" not in source
    assert "from .compaction_glassbox" not in source
    assert "from .handoff_summaries" not in source


# ----------------------------------------------------------------------
# Validator honesty
# ----------------------------------------------------------------------


def _mutated(mutator):
    data = copy.deepcopy(load_resource("part7_gate.yaml"))
    mutator(data)
    return data


def test_validator_rejects_a_non_pass_verdict():
    data = _mutated(lambda d: d.update(verdict="FAIL"))
    assert any("PASS" in p for p in validate_gate(data))


def test_validator_rejects_a_missing_slice():
    data = _mutated(lambda d: d["slices"].pop())
    assert any("23" in p for p in validate_gate(data))


def test_validator_rejects_broken_baseline_arithmetic():
    def spoil(d):
        d["baseline"]["passed"] = 1

    assert any("arithmetic" in p for p in validate_gate(_mutated(spoil)))


def test_validator_rejects_an_uncompleted_exercise():
    def spoil(d):
        d["exercises"][0]["status"] = "queued"

    assert any("completed" in p for p in validate_gate(_mutated(spoil)))


def test_validator_rejects_a_short_week():
    def spoil(d):
        d["exercises"][0]["resumed_on"] = "2026-11-08"

    assert any("week" in p for p in validate_gate(_mutated(spoil)))


def test_validator_rejects_a_statement_that_lies():
    def spoil_stated(d):
        d["exercises"][0]["statement"][0]["stated"] = "different words"

    assert any("memory alone" in p
               for p in validate_gate(_mutated(spoil_stated)))

    def spoil_truth(d):
        d["exercises"][0]["statement"][0]["truth"] = "different words"
        d["exercises"][0]["statement"][0]["stated"] = "different words"

    assert any("cannot lie" in p
               for p in validate_gate(_mutated(spoil_truth)))


def test_validator_rejects_a_silent_rewrite_compaction():
    def spoil(d):
        compaction = d["exercises"][0]["compaction"]
        compaction["summary_versions"] = compaction["summary_versions"][:1]
        compaction["version_count"] = 1

    assert any("two versions" in p
               for p in validate_gate(_mutated(spoil)))


def test_validator_rejects_an_unfinished_task():
    def spoil(d):
        d["exercises"][0]["grading"]["passed"] = 11

    assert any("must finish" in p for p in validate_gate(_mutated(spoil)))


def test_validator_rejects_a_wrong_layer_road():
    def spoil(d):
        d["layers"][0]["module"] = "session_memory"

    assert any("shipped" in p and "road" in p
               for p in validate_gate(_mutated(spoil)))


def test_validator_rejects_a_carried_transcript():
    def spoil(d):
        d["exercises"][0]["situation"]["transcript"] = ["user: hello"]

    assert any("never" in p and "carried" in p
               for p in validate_gate(_mutated(spoil)))


def test_load_raises_on_invalid_data():
    with pytest.raises(ValidationError):
        load_gate({"schema": "nope", "slices": [], "layers": [],
                   "exercises": [], "baseline": {}})
