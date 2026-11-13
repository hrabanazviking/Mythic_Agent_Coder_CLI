"""M-146 — Part VI gate.

TIER: integration

The Part VI gate (``mythic_agent/data/part6_gate.yaml`` +
``mythic_agent.core.part6_gate``): a six-slice feature
built by a three-member crew in parallel worktrees —
merged clean, Auditor-approved, cost ledger complete —
evidence banked against the M-145 confirmation suite.

These tests do not take the record's word for any of it:

* the gate record loads and validates, its slices are
  M-121..M-145 with titles matching the roadmap data, and
  its baseline is the M-145 confirmation suite's counted
  totals,
* the dealing is RE-PROVEN LIVE through the shipped
  roads: the crew is the shipped M-121 casting
  (``load_casting``) and M-125's ``deal_tasks`` deals
  every feature slice to exactly the member the record
  names, every deal an office fit,
* the worktrees are RE-PROVEN LIVE through M-124:
  each wave builds as a shipped ``WorktreePlan``, the
  coordinator holds no worktree, every branch and path
  is the shipped convention (``suggest_branch`` /
  ``suggest_path``), and ``merge_plan_for`` derives
  every merge step in slice order, merged by the
  coordinator,
* the merges are RE-PROVEN LIVE through M-128:
  ``MergeDiscipline``'s judge derives no verdict from
  the record's steps and merges, and every member's
  line completes,
* the audit is RE-PROVEN LIVE through M-130: an
  ``AuditorLedger`` built from the record's cases,
  checks and results reports clean — no verdicts, and
  every gate state passed (the record's results name
  no evidence prose of their own, so each shipped
  result is built carrying the record's own outcome
  as its evidence words),
* the cost ledger is RE-PROVEN LIVE through M-140:
  ``derive_ledger`` over the record's run records,
  priced by the shared rate table (``core/costs``),
  closes exactly on the record's totals,
* the honesty bounds hold: the evidence kind is
  pure-roads-measured — every step rides a real shipped
  pure road at the data level, nothing is faked, no
  live crew is spawned, no git command is run, no
  model is called, and the campaign tree is never the
  exercise repo.
"""

from __future__ import annotations

import copy

import pytest

from mythic_agent.core.part6_gate import (
    BASELINE_RESOURCE,
    EXERCISE_IDS,
    GATE_SLICE,
    PLAIN_EXPLANATION,
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
    assert validate_gate(load_resource("part6_gate.yaml")) == []
    assert gate.gate_slice == GATE_SLICE == "M-146"
    assert gate.part == 6
    assert gate.part_title == "The Crew"
    assert gate.verdict == "PASS"
    assert PLAIN_EXPLANATION


def test_slices_cover_part6_in_order(gate):
    assert gate.slice_ids() == tuple(f"M-{n:03d}" for n in range(121, 146))
    road = load_roadmap()
    for ref in gate.slices:
        assert road.slice(ref.slice).title == ref.title, ref.slice
    assert road.part(6).title == gate.part_title
    done_ids = [s.id for s in road.done()]
    assert [f"M-{n:03d}" for n in range(121, 146)] == [
        d for d in done_ids if "M-121" <= d <= "M-145"]
    nxt = road.next_slice()
    assert nxt is not None
    assert nxt.id == "M-146" or nxt.part >= 7


def test_baseline_is_the_m145_confirmation_suite(gate):
    assert gate.baseline_resource == BASELINE_RESOURCE == \
        "m145_confirmation_suite"
    # The M-145 confirmation suite, counted from its on-disk
    # log on the laptop (logs/m145-fullsuite2.log): the 2
    # failures are exactly the long-classified environment
    # cases (tiktoken-premise estimator; PortAudio import).
    assert gate.baseline_totals() == (7247, 7244, 2, 1)


def test_exercise_shape_and_honesty(gate):
    assert gate.exercise_ids() == EXERCISE_IDS == ("crew_build",)
    assert len(gate.completed_exercises()) == 1
    exercise = gate.exercise("crew_build")
    assert exercise.status == "completed"
    assert exercise.evidence_kind == "pure-roads-measured"
    assert exercise.evidence
    assert exercise.crew == ("forge_worker", "architect", "scribe")
    assert exercise.coordinator == "polymath"
    assert exercise.coordinator not in exercise.crew
    assert exercise.feature_slice_ids() == (
        "M-124", "M-125", "M-126", "M-128", "M-133", "M-140")
    assert exercise.merge_verdicts == 0
    assert exercise.audit_verdicts == 0
    assert exercise.cost_totals() == (
        exercise.cost_calls, exercise.cost_input_tokens,
        exercise.cost_output_tokens) == (6, 445000, 112000)
    assert exercise.cost_total_usd == 2.04745
    for sid in exercise.owning_slices:
        assert "M-121" <= sid <= "M-145"


def test_render_markdown_and_record_report_the_gate(gate):
    text = render_markdown(gate)
    assert "PASS" in text
    assert "M-121..M-145" in text
    assert "7247 collected" in text
    for exercise_id in EXERCISE_IDS:
        assert gate.exercise(exercise_id).title in text
    words = plain_words(gate)
    assert "0 merge verdicts" in words
    assert "0 audit verdicts" in words
    assert "$2.04745" in words
    record = gate_record(gate)
    assert record["type"] == "part6_gate"
    assert record["slice"] == "M-146"
    assert record["verdict"] == "PASS"


# ----------------------------------------------------------------------
# The crew build, re-proven live (M-121/M-124/M-125/M-128/M-130/M-140)
# ----------------------------------------------------------------------


def test_dealing_and_worktrees_reproven_live(gate):
    from mythic_agent.core.crew_members import load_casting
    from mythic_agent.core.task_dealing import build_task, deal_tasks
    from mythic_agent.core.worktrees import (
        WorktreePlan,
        build_assignment,
        merge_plan_for,
        suggest_branch,
        suggest_path,
    )

    exercise = gate.exercise("crew_build")

    # The crew is the shipped M-121 casting, no other crew.
    casting = load_casting()
    crew = [m for m in casting.members if m.member_id in exercise.crew]
    assert {m.member_id for m in crew} == set(exercise.crew)
    assert casting.get(exercise.coordinator).office == "polymath"

    # The dealing is the shipped M-125 dealer's own: every
    # feature slice dealt to the record's member, every
    # deal an office fit, two slices per member.
    tasks = [build_task({"slice": f.slice, "title": f.title,
                         "office": f.office})
             for f in exercise.feature_slices]
    dealing = deal_tasks(tasks, crew)
    assert [(a.slice_id, a.member) for a in dealing.assignments] == \
        list(exercise.dealt_pairs())
    assert all(a.fit for a in dealing.assignments)
    assert dealing.undealt == ()
    assert dealing.loads() == {
        "forge_worker": 2, "architect": 2, "scribe": 2}

    # The worktrees are shipped M-124 plans, one per wave:
    # the coordinator holds no worktree, every branch and
    # path is the shipped convention, and the derived
    # merge plan covers each wave in slice order, every
    # step merged by the coordinator.
    assigned = []
    for wave in exercise.worktree_waves:
        plan = WorktreePlan(
            assignments=tuple(
                build_assignment({
                    "member": a.member,
                    "office": casting.get(a.member).office,
                    "slice": a.slice, "branch": a.branch,
                    "path": a.path})
                for a in wave.assignments),
            coordinator=exercise.coordinator)
        assert exercise.coordinator not in {
            a.member for a in plan.assignments}
        for assignment in plan.assignments:
            assert assignment.branch == suggest_branch(
                assignment.member, assignment.slice_id)
            assert assignment.path == suggest_path(assignment.member)
        steps = merge_plan_for(plan)
        assert [s.slice_id for s in steps] == sorted(
            a.slice_id for a in plan.assignments)
        assert all(s.merger == exercise.coordinator for s in steps)
        assigned.extend(
            (a.slice_id, a.member) for a in plan.assignments)
    assert sorted(assigned) == sorted(exercise.dealt_pairs())


def test_merges_and_audit_reproven_live(gate):
    from mythic_agent.core.auditor_veto import (
        AuditorLedger,
        build_case,
        build_check,
        build_result,
    )
    from mythic_agent.core.merge_discipline import (
        MergeDiscipline,
        build_attempt,
        build_step,
    )

    exercise = gate.exercise("crew_build")

    # The merges are judged by the shipped M-128 judge:
    # the record's steps and merges derive no verdict,
    # and every member's line completes.
    discipline = MergeDiscipline(
        steps=tuple(build_step(
            {"member": m.member, "slice": m.slice,
             "branch": m.branch}) for m in exercise.merges),
        merges=tuple(build_attempt(
            {"member": m.member, "slice": m.slice,
             "branch": m.branch, "gate": m.gate,
             "outcome": m.outcome}) for m in exercise.merges),
        keeper=exercise.coordinator)
    report = discipline.report()
    assert report.is_clean
    assert len(report.verdicts) == exercise.merge_verdicts == 0
    assert all(line.is_complete for line in report.lines)
    assert {line.member: line.merged for line in report.lines} == {
        "forge_worker": ("M-124", "M-128"),
        "architect": ("M-125", "M-126"),
        "scribe": ("M-133", "M-140")}

    # The audit is judged by the shipped M-130 Auditor:
    # the record's cases, checks and results report
    # clean, and every gate state passed.
    ledger = AuditorLedger(
        cases=tuple(build_case(
            {"slice": c.slice, "title": c.title,
             "builder": c.builder}) for c in exercise.audit_cases),
        checks=tuple(build_check(
            {"slice": c.slice, "name": c.name,
             "required": c.required}) for c in exercise.audit_checks),
        results=tuple(build_result(
            {"slice": r.slice, "check": r.check,
             "outcome": r.outcome,
             "evidence": f"the gate record's own result: "
                         f"{r.check} {r.outcome} for {r.slice}"})
            for r in exercise.audit_results),
        keeper="auditor")
    veto_report = ledger.report()
    assert veto_report.is_clean
    assert len(veto_report.verdicts) == exercise.audit_verdicts == 0
    assert [g.slice_id for g in veto_report.gates] == \
        list(exercise.feature_slice_ids())
    assert all(g.is_passed for g in veto_report.gates)
    assert all(g.required == 2 and g.proven == 2
               for g in veto_report.gates)


def test_cost_ledger_reproven_live(gate):
    from mythic_agent.core.cost_court import build_entry, derive_ledger
    from mythic_agent.core.costs import price

    exercise = gate.exercise("crew_build")
    entries = [build_entry(
        {"member": e.member, "entry_id": e.entry_id,
         "slice": e.slice, "model": e.model,
         "input_tokens": e.input_tokens,
         "output_tokens": e.output_tokens})
        for e in exercise.cost_entries]
    assert all(e.priced for e in entries)

    # The ledger is the shipped M-140 derivation over the
    # shared rate table, and it closes exactly on the
    # record's totals — cost included.
    ledger = derive_ledger(entries)
    assert ledger.keeper == "scribe"
    assert ledger.total_calls == exercise.cost_calls == 6
    assert ledger.total_input_tokens == exercise.cost_input_tokens
    assert ledger.total_output_tokens == exercise.cost_output_tokens
    assert ledger.total_cost_usd == exercise.cost_total_usd == 2.04745
    assert {(r.slice_id, r.member) for r in ledger.rows} == \
        set(exercise.dealt_pairs())
    direct = round(sum(
        price(e.model, e.input_tokens, e.output_tokens)[0]
        for e in exercise.cost_entries), 6)
    assert direct == exercise.cost_total_usd


def test_module_purity():
    import inspect

    import mythic_agent.core.part6_gate as module

    source = inspect.getsource(module)
    assert "from mythic_agent.agents" not in source
    assert "import mythic_agent.agents" not in source


# ----------------------------------------------------------------------
# Validator honesty
# ----------------------------------------------------------------------


def _mutated(mutator):
    data = copy.deepcopy(load_resource("part6_gate.yaml"))
    mutator(data)
    return data


def test_validator_rejects_a_non_pass_verdict():
    data = _mutated(lambda d: d.update(verdict="FAIL"))
    assert any("PASS" in p for p in validate_gate(data))


def test_validator_rejects_a_missing_slice():
    data = _mutated(lambda d: d["slices"].pop())
    assert any("25" in p for p in validate_gate(data))


def test_validator_rejects_broken_baseline_arithmetic():
    def spoil(d):
        d["baseline"]["passed"] = 1

    assert any("arithmetic" in p for p in validate_gate(_mutated(spoil)))


def test_validator_rejects_an_uncompleted_exercise():
    def spoil(d):
        d["exercises"][0]["status"] = "queued"

    assert any("completed" in p for p in validate_gate(_mutated(spoil)))


def test_validator_rejects_a_merge_not_green():
    def spoil(d):
        d["exercises"][0]["merges"][0]["outcome"] = "red"

    assert any("green" in p for p in validate_gate(_mutated(spoil)))


def test_validator_rejects_a_missing_audit_check():
    def spoil(d):
        d["exercises"][0]["audit_checks"].pop()

    assert any("audit" in p for p in validate_gate(_mutated(spoil)))


def test_validator_rejects_cost_totals_not_closing():
    def spoil(d):
        d["exercises"][0]["cost_input_tokens"] += 1

    assert any("cost" in p for p in validate_gate(_mutated(spoil)))

    def spoil_total(d):
        d["exercises"][0]["cost_total_usd"] = 9.99

    assert any("cost_total_usd" in p
               for p in validate_gate(_mutated(spoil_total)))


def test_load_raises_on_invalid_data():
    with pytest.raises(ValidationError):
        load_gate({"schema": "nope", "slices": [], "exercises": [],
                   "baseline": {}})
