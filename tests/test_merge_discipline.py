"""M-128 Merge discipline - pure-layer tests.

TIER: integration

The pure layer is the merging of member branches
as data: the evidence (steps - which member merges
which slice from which branch - and the merges as
recorded, each with its test gate and outcome)
validated as data, the shipped example plan and
ledger held in a data file, a loader that reads a
plan from any file, the verdicts and line states
derived mechanically from the evidence alone - an
out-of-order merge, a merge with no passing test
gate, and a red merge stopping only its own line,
the roadmap's three judgements - a verdict record
and a report record shaped as session news, and a
registry. Nothing here executes git, performs a
real merge, spawns or stops a crew or claims a Part
VIII board: discipline is data only, and the
coordinator acts on the verdicts through later
roads.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.crew_members import load_casting
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.merge_discipline import (
    DISCIPLINE_RESOURCE,
    DISCIPLINE_SCHEMA,
    DISCIPLINE_SLICE,
    PLAIN_EXPLANATION,
    USAGE,
    VERDICT_KINDS,
    LineState,
    MergeAttempt,
    MergeDiscipline,
    MergeDisciplineRegistry,
    MergeReport,
    MergeStep,
    MergeVerdict,
    attempt_record,
    build_attempt,
    build_step,
    build_verdict,
    format_kinds,
    format_lines,
    format_merge_screen,
    format_verdict,
    format_verdicts,
    judge_merges,
    load_merge_discipline,
    load_merge_discipline_file,
    normalize_gate,
    normalize_outcome,
    normalize_slice_id,
    normalize_verdict_kind,
    parse_merge_args,
    plain_words,
    report_plain_words,
    report_record,
    step_record,
    validate_attempt,
    validate_plan,
    validate_report,
    validate_step,
    validate_verdict,
    verdict_record,
)

ROOT = Path(__file__).resolve().parents[1]


def _casting():
    return load_casting().members


def _step(**kwargs):
    kwargs.setdefault("member", "scribe")
    kwargs.setdefault("slice_id", "M-126")
    kwargs.setdefault("branch", "crew/scribe/m-126")
    return MergeStep(**kwargs)


def _attempt(**kwargs):
    kwargs.setdefault("member", "scribe")
    kwargs.setdefault("slice_id", "M-126")
    kwargs.setdefault("branch", "crew/scribe/m-126")
    kwargs.setdefault("gate", "passed")
    kwargs.setdefault("outcome", "green")
    return MergeAttempt(**kwargs)


def _plan_data():
    return {
        "schema": DISCIPLINE_SCHEMA, "slice": DISCIPLINE_SLICE,
        "keeper": "forge_worker",
        "steps": [
            {"member": "scribe", "slice_id": "M-126",
             "branch": "crew/scribe/m-126"},
            {"member": "scribe", "slice_id": "M-133",
             "branch": "crew/scribe/m-133"},
        ],
        "merges": [
            {"member": "scribe", "slice_id": "M-126",
             "branch": "crew/scribe/m-126", "gate": "passed",
             "outcome": "green"},
        ]}


def _write_plan(tmp_path, data):
    path = tmp_path / "plan.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def _clean_evidence():
    return {
        "steps": [
            {"member": "forge_worker", "slice_id": "M-125",
             "branch": "crew/forge_worker/m-125"},
            {"member": "scribe", "slice_id": "M-126",
             "branch": "crew/scribe/m-126"},
        ],
        "merges": [
            {"member": "forge_worker", "slice_id": "M-125",
             "branch": "crew/forge_worker/m-125",
             "gate": "passed", "outcome": "green"},
            {"member": "scribe", "slice_id": "M-126",
             "branch": "crew/scribe/m-126",
             "gate": "passed", "outcome": "green"},
        ]}


# -- constants and word readings --------------------------------------------


def test_constants_and_usage():
    assert DISCIPLINE_SLICE == "M-128"
    assert DISCIPLINE_SCHEMA == "mythic.merge_discipline/1"
    assert DISCIPLINE_RESOURCE == "merge_discipline.yaml"
    assert VERDICT_KINDS == (
        "out_of_order", "missing_test_gate", "line_stopped")
    assert USAGE.startswith("Usage: /merge")
    assert "lines" in USAGE and "kinds" in USAGE
    assert "in slice order" in PLAIN_EXPLANATION
    assert "test gate recorded at each merge" in PLAIN_EXPLANATION
    assert "stops only its own line" in PLAIN_EXPLANATION
    assert "not the whole crew" in PLAIN_EXPLANATION
    assert "no Part VIII board" in PLAIN_EXPLANATION
    assert "as data only" in PLAIN_EXPLANATION
    assert "executes no git" in PLAIN_EXPLANATION
    assert "performs no real merge" in PLAIN_EXPLANATION


def test_kind_gate_outcome_readings_and_refusals():
    assert normalize_verdict_kind("order") == "out_of_order"
    assert normalize_verdict_kind("Out-Of-Order") == "out_of_order"
    assert normalize_verdict_kind("gate") == "missing_test_gate"
    assert normalize_verdict_kind("UNTESTED") == \
        "missing_test_gate"
    assert normalize_verdict_kind("red") == "line_stopped"
    assert normalize_verdict_kind("Line-Stopped") == "line_stopped"
    for bad in ("stall", "blocked", "", None, 3):
        with pytest.raises(ValueError):
            normalize_verdict_kind(bad)
    assert normalize_gate("Passed") == "passed"
    assert normalize_gate("pass") == "passed"
    assert normalize_gate("FAIL") == "failed"
    assert normalize_gate("none") == "missing"
    assert normalize_gate("absent") == "missing"
    for bad in ("green", "skipped", "", None):
        with pytest.raises(ValueError):
            normalize_gate(bad)
    assert normalize_outcome("GREEN") == "green"
    assert normalize_outcome("failed") == "red"
    assert normalize_outcome("Conflicted") == "red"
    for bad in ("yellow", "passed", "", None):
        with pytest.raises(ValueError):
            normalize_outcome(bad)
    # Slice readings are composed from the M-124 layer.
    assert normalize_slice_id("m-128") == "M-128"
    with pytest.raises(ValueError):
        normalize_slice_id("128")


# -- the evidence records ----------------------------------------------------


def test_step_and_attempt_construction_and_records():
    step = _step()
    record = step.to_record()
    assert record["type"] == "merge_step"
    assert record["slice"] == "M-128"
    assert record["branch"] == "crew/scribe/m-126"
    attempt = _attempt()
    assert attempt.is_red is False and attempt.is_gated is True
    assert _attempt(outcome="red").is_red is True
    assert _attempt(gate="missing").is_gated is False
    attempt_dict = attempt.to_record()
    assert attempt_dict["type"] == "merge_attempt"
    assert attempt_dict["gate"] == "passed"
    news = step_record(step)
    assert news["news"] is True
    assert news["headline"] == \
        "scribe merges M-126 from crew/scribe/m-126."
    news = attempt_record(attempt)
    assert news["news"] is True
    assert "recorded green with gate passed" in news["headline"]


def test_evidence_refusals():
    with pytest.raises(ValueError):
        _step(member="bad member")
    with pytest.raises(ValueError):
        _step(slice_id="M-999")
    with pytest.raises(ValueError):
        _step(branch="bad branch")
    with pytest.raises(ValueError):
        _step(branch="crew//m-126")
    with pytest.raises(ValueError):
        _attempt(gate="skipped")
    with pytest.raises(ValueError):
        _attempt(outcome="yellow")
    with pytest.raises(ValueError):
        _attempt(member="")


def test_evidence_validator_aliases_and_refusals():
    step = validate_step(
        {"member_id": "scribe", "slice": "m-126",
         "branch": "crew/scribe/m-126", "id": "step-9"})
    assert step.member == "scribe"
    assert step.slice_id == "M-126"
    assert step.step_id == "step-9"
    assert build_step(step) is step
    assert build_step(
        member="scribe", slice_id="M-126",
        branch="crew/scribe/m-126") == _step()
    with pytest.raises(ValueError):
        validate_step(
            {"member": "scribe", "member_id": "auditor",
             "slice_id": "M-126", "branch": "crew/scribe/m-126"})
    with pytest.raises(ValueError):
        validate_step(
            {"member": "scribe", "slice_id": "M-126",
             "branch": "crew/scribe/m-126", "surprise": 1})
    with pytest.raises(ValueError):
        validate_step({"member": "scribe"})
    with pytest.raises(ValueError):
        validate_step("not a step")
    attempt = validate_attempt(
        {"member_id": "scribe", "slice": "m-126",
         "branch": "crew/scribe/m-126", "test_gate": "pass",
         "result": "green", "id": "attempt-9"})
    assert attempt.gate == "passed"
    assert attempt.attempt_id == "attempt-9"
    assert build_attempt(attempt) is attempt
    with pytest.raises(ValueError):
        validate_attempt(
            {"member": "scribe", "slice_id": "M-126",
             "branch": "crew/scribe/m-126", "gate": "passed",
             "test_gate": "failed", "outcome": "green"})
    with pytest.raises(ValueError):
        validate_attempt({"member": "scribe"})


# -- the shipped example plan --------------------------------------------------


def test_shipped_plan_loads_as_the_example():
    plan = load_merge_discipline()
    assert plan.keeper == "forge_worker"
    assert len(plan.steps) == 7
    assert len(plan.merges) == 5
    assert [(s.member, s.slice_id) for s in plan.steps] == [
        ("forge_worker", "M-125"), ("scribe", "M-126"),
        ("guardian", "M-127"), ("forge_worker", "M-128"),
        ("auditor", "M-130"), ("auditor", "M-132"),
        ("scribe", "M-133"),
    ]
    assert [m.slice_id for m in plan.merges_for("scribe")] == [
        "M-133", "M-126"]
    assert len(plan.steps_for("auditor")) == 2
    # Every member named is a shipped member.
    member_ids = {m.member_id for m in _casting()}
    for step in plan.steps:
        assert step.member in member_ids
    for merge in plan.merges:
        assert merge.member in member_ids
    assert validate_plan(
        yaml.safe_load(
            (ROOT / "mythic_agent" / "data" / DISCIPLINE_RESOURCE)
            .read_text(encoding="utf-8")),
        require_example=True) == []


def test_shipped_example_check_refuses_drift():
    data = yaml.safe_load(
        (ROOT / "mythic_agent" / "data" / DISCIPLINE_RESOURCE)
        .read_text(encoding="utf-8"))
    data["steps"][0]["branch"] = "crew/forge_worker/other"
    problems = validate_plan(data, require_example=True)
    assert any("exactly the seven steps" in p for p in problems)
    # The same file is a well-formed plan without the check.
    assert validate_plan(data) == []
    data = yaml.safe_load(
        (ROOT / "mythic_agent" / "data" / DISCIPLINE_RESOURCE)
        .read_text(encoding="utf-8"))
    data["keeper"] = "scribe"
    problems = validate_plan(data, require_example=True)
    assert any("kept by the forge_worker" in p for p in problems)


def test_example_plan_yields_exactly_three_verdicts():
    plan = load_merge_discipline()
    report = plan.report()
    assert [v.kind for v in report.verdicts] == [
        "out_of_order", "missing_test_gate", "line_stopped"]
    order, gate, stopped = report.verdicts
    assert (order.member, order.slice_id) == ("scribe", "M-133")
    assert (gate.member, gate.slice_id) == ("scribe", "M-126")
    assert (stopped.member, stopped.slice_id) == (
        "forge_worker", "M-128")
    forge = report.line_for("forge_worker")
    assert forge.merged == ("M-125",)
    assert forge.stopped is True
    assert forge.stopped_slice == "M-128"
    assert forge.next_slice == "M-128"
    auditor = report.line_for("auditor")
    assert auditor.merged == ("M-130",)
    assert auditor.stopped is False
    assert auditor.next_slice == "M-132"
    assert report.line_for("guardian").merged == ()
    assert report.line_for("scribe").next_slice == "M-126"
    assert report.is_clean is False
    assert validate_report(plan, report) == []
    with pytest.raises(KeyError):
        report.line_for("polymath")


# -- the judge -------------------------------------------------------------------


def test_green_merges_advance_the_line_in_order():
    evidence = _clean_evidence()
    assert judge_merges(evidence) == ()
    report = MergeDiscipline(
        steps=[build_step(s) for s in evidence["steps"]],
        merges=[build_attempt(m) for m in evidence["merges"]],
        keeper="forge_worker").report()
    assert report.is_clean is True
    assert report.line_for("forge_worker").merged == ("M-125",)
    assert report.line_for("forge_worker").is_complete is True
    assert report.line_for("scribe").next_slice is None
    assert validate_report(evidence, report) == []
    # The same evidence always yields the same verdicts.
    assert judge_merges(evidence) == judge_merges(evidence)


def test_out_of_order_merge_is_refused_and_advances_nothing():
    evidence = {
        "steps": [
            {"member": "scribe", "slice_id": "M-126",
             "branch": "crew/scribe/m-126"},
            {"member": "scribe", "slice_id": "M-133",
             "branch": "crew/scribe/m-133"},
        ],
        "merges": [
            {"member": "scribe", "slice_id": "M-133",
             "branch": "crew/scribe/m-133", "gate": "passed",
             "outcome": "green"},
        ]}
    verdicts = judge_merges(evidence)
    assert [v.kind for v in verdicts] == ["out_of_order"]
    assert "before M-126" in verdicts[0].title
    plan = MergeDiscipline(
        steps=[build_step(s) for s in evidence["steps"]],
        merges=[build_attempt(m) for m in evidence["merges"]],
        keeper="forge_worker")
    line = plan.report().line_for("scribe")
    assert line.merged == ()
    assert line.next_slice == "M-126"
    assert line.pending == ("M-126", "M-133")


def test_unplanned_slice_merge_is_out_of_order():
    verdicts = judge_merges({"steps": [
        {"member": "scribe", "slice_id": "M-126",
         "branch": "crew/scribe/m-126"}], "merges": [
        {"member": "scribe", "slice_id": "M-133",
         "branch": "crew/scribe/m-133", "gate": "passed",
         "outcome": "green"},
        {"member": "auditor", "slice_id": "M-130",
         "branch": "crew/auditor/m-130", "gate": "passed",
         "outcome": "green"},
    ]})
    assert [v.kind for v in verdicts] == [
        "out_of_order", "out_of_order"]
    assert all("no planned step" in v.title for v in verdicts)


def test_missing_and_failed_gates_are_flagged():
    base_step = {"member": "scribe", "slice_id": "M-126",
                 "branch": "crew/scribe/m-126"}
    for gate in ("missing", "failed"):
        verdicts = judge_merges({"steps": [base_step], "merges": [
            {"member": "scribe", "slice_id": "M-126",
             "branch": "crew/scribe/m-126", "gate": gate,
             "outcome": "green"}]})
        assert [v.kind for v in verdicts] == ["missing_test_gate"]
    # An ungated merge advances nothing: the gated retry lands.
    plan = MergeDiscipline(
        steps=[build_step(base_step)],
        merges=[
            _attempt(gate="missing"),
            _attempt(gate="passed"),
        ], keeper="forge_worker")
    assert plan.report().line_for("scribe").merged == ("M-126",)


def test_red_merge_stops_only_its_own_line():
    plan = load_merge_discipline()
    report = plan.report()
    # forge_worker's red M-128 stops forge_worker's line...
    assert report.line_for("forge_worker").stopped is True
    # ...and no other line: auditor's later green merge
    # still advanced, and the untouched lines stand open.
    assert report.line_for("auditor").merged == ("M-130",)
    assert report.line_for("auditor").stopped is False
    assert report.line_for("guardian").stopped is False
    assert report.line_for("scribe").stopped is False
    stopped = report.by_kind("red")
    assert len(stopped) == 1
    assert stopped[0].member == "forge_worker"
    assert "stops the line, not the whole crew" in \
        stopped[0].detail


def test_later_merge_on_a_stopped_line_is_flagged():
    evidence = {
        "steps": [
            {"member": "forge_worker", "slice_id": "M-125",
             "branch": "crew/forge_worker/m-125"},
            {"member": "forge_worker", "slice_id": "M-128",
             "branch": "crew/forge_worker/m-128"},
            {"member": "forge_worker", "slice_id": "M-134",
             "branch": "crew/forge_worker/m-134"},
        ],
        "merges": [
            {"member": "forge_worker", "slice_id": "M-125",
             "branch": "crew/forge_worker/m-125",
             "gate": "passed", "outcome": "green"},
            {"member": "forge_worker", "slice_id": "M-128",
             "branch": "crew/forge_worker/m-128",
             "gate": "passed", "outcome": "red"},
            {"member": "forge_worker", "slice_id": "M-134",
             "branch": "crew/forge_worker/m-134",
             "gate": "passed", "outcome": "green"},
        ]}
    verdicts = judge_merges(evidence)
    assert [v.kind for v in verdicts] == [
        "line_stopped", "line_stopped"]
    assert "on a stopped line" in verdicts[1].title
    plan = MergeDiscipline(
        steps=[build_step(s) for s in evidence["steps"]],
        merges=[build_attempt(m) for m in evidence["merges"]],
        keeper="forge_worker")
    line = plan.report().line_for("forge_worker")
    assert line.merged == ("M-125",)
    assert line.pending == ("M-128", "M-134")


def test_red_out_of_order_or_ungated_does_not_stop_the_line():
    # Precedence along a line: order is judged before
    # the gate, and the gate before the outcome - a
    # red merge that was never the line's next gated
    # merge stops nothing.
    evidence = {
        "steps": [
            {"member": "scribe", "slice_id": "M-126",
             "branch": "crew/scribe/m-126"},
            {"member": "scribe", "slice_id": "M-133",
             "branch": "crew/scribe/m-133"},
        ],
        "merges": [
            {"member": "scribe", "slice_id": "M-133",
             "branch": "crew/scribe/m-133", "gate": "passed",
             "outcome": "red"},
            {"member": "scribe", "slice_id": "M-126",
             "branch": "crew/scribe/m-126", "gate": "missing",
             "outcome": "red"},
            {"member": "scribe", "slice_id": "M-126",
             "branch": "crew/scribe/m-126", "gate": "passed",
             "outcome": "green"},
        ]}
    assert [v.kind for v in judge_merges(evidence)] == [
        "out_of_order", "missing_test_gate"]
    plan = MergeDiscipline(
        steps=[build_step(s) for s in evidence["steps"]],
        merges=[build_attempt(m) for m in evidence["merges"]],
        keeper="forge_worker")
    line = plan.report().line_for("scribe")
    assert line.stopped is False
    assert line.merged == ("M-126",)


def test_validate_report_names_a_missing_or_extra_verdict():
    data = _plan_data()
    evidence = {"steps": data["steps"], "merges": data["merges"]}
    report = MergeDiscipline(
        steps=[build_step(s) for s in evidence["steps"]],
        merges=[build_attempt(m) for m in evidence["merges"]],
        keeper="forge_worker").report()
    assert validate_report(evidence, report) == []
    wrong = MergeReport(verdicts=report.verdicts, lines=())
    assert validate_report(evidence, wrong) != []
    extra = MergeReport(
        verdicts=report.verdicts + judge_merges(_clean_evidence() | {
            "merges": [{"member": "scribe", "slice_id": "M-126",
                         "branch": "crew/scribe/m-126",
                         "gate": "missing", "outcome": "green"}]}),
        lines=report.lines)
    assert validate_report(evidence, extra) != []
    assert validate_report(evidence, "not a report") != []


def test_verdict_validation_and_refusals():
    verdict = build_verdict(
        kind="red", member="scribe", slice="m-128",
        branch="crew/scribe/m-128",
        title="Line stopped: scribe merge of M-128 went red",
        detail="The merge went red.")
    assert verdict.kind == "line_stopped"
    assert verdict.slice_id == "M-128"
    assert validate_verdict(verdict) is verdict
    with pytest.raises(ValueError):
        build_verdict(
            kind="stall", member="scribe", slice_id="M-128",
            branch="crew/scribe/m-128", title="T", detail="D")
    with pytest.raises(ValueError):
        validate_verdict(
            {"kind": "red", "member": "scribe",
             "slice_id": "M-128", "branch": "crew/scribe/m-128",
             "title": "T", "detail": "D", "surprise": 1})
    with pytest.raises(ValueError):
        validate_verdict("not a verdict")
    with pytest.raises(ValueError):
        LineState(member="scribe", stopped=True)


# -- the plan file -----------------------------------------------------------------


def test_plan_construction_refusals():
    with pytest.raises(ValueError):
        MergeDiscipline(keeper="forge_worker")
    with pytest.raises(ValueError):
        MergeDiscipline(steps=[_step()], keeper="bad keeper")
    with pytest.raises(ValueError):
        MergeDiscipline(
            steps=[_step(), _step()], keeper="forge_worker")
    plan = MergeDiscipline(steps=[_step()], keeper="forge_worker")
    assert plan.merges == ()
    assert plan.report().is_clean is True
    assert plan.report().line_for("scribe").next_slice == "M-126"


def test_plan_mapping_refusals():
    data = _plan_data()
    assert validate_plan(data) == []
    bad_schema = dict(data, schema="mythic.other/1")
    assert any("schema" in p for p in validate_plan(bad_schema))
    bad_slice = dict(data, slice="M-127")
    assert any("slice" in p for p in validate_plan(bad_slice))
    unknown = dict(data, surprise=1)
    assert any("unknown" in p for p in validate_plan(unknown))
    no_keeper = {k: v for k, v in data.items() if k != "keeper"}
    assert any("keeper" in p for p in validate_plan(no_keeper))
    empty = dict(data, steps=[])
    assert any("at least one step" in p for p in validate_plan(empty))
    bad_entry = dict(data, steps=[{"member": "scribe"}])
    assert any("step 1" in p for p in validate_plan(bad_entry))
    duplicated = dict(data, steps=data["steps"] + data["steps"][:1])
    assert any("one slice twice" in p for p in validate_plan(duplicated))
    assert validate_plan("not a plan") != []
    with pytest.raises(ValidationError):
        load_merge_discipline(bad_schema)


def test_plan_file_on_disk_roundtrip_and_refusals(tmp_path):
    path = _write_plan(tmp_path, _plan_data())
    plan = load_merge_discipline_file(path)
    assert plan.keeper == "forge_worker"
    assert plan.report().is_clean is True
    assert plan.report().line_for("scribe").merged == ("M-126",)
    bad = _write_plan(tmp_path, dict(_plan_data(), keeper=None))
    with pytest.raises(ValidationError):
        load_merge_discipline_file(bad)
    with pytest.raises(FileNotFoundError):
        load_merge_discipline_file(tmp_path / "missing.yaml")


# -- the registry --------------------------------------------------------------------


def test_registry_deterministic_ids_and_refusals():
    registry = MergeDisciplineRegistry()
    first = registry.register_step(_step())
    second = registry.register_step(_step(
        member="auditor", slice_id="M-130",
        branch="crew/auditor/m-130"))
    attempt = registry.register_attempt(_attempt())
    assert first.step_id == "step-1"
    assert second.step_id == "step-2"
    assert attempt.attempt_id == "attempt-1"
    supplied = registry.register_step(_step(
        step_id="step-4", member="guardian", slice_id="M-127",
        branch="crew/guardian/m-127"))
    assert supplied.step_id == "step-4"
    # The sequence skips a number a supplied id took.
    assert registry.register_step(_step(
        member="skald", slice_id="M-130",
        branch="crew/skald/m-130")).step_id == "step-3"
    assert registry.register_step(_step(
        member="polymath", slice_id="M-129",
        branch="crew/polymath/m-129")).step_id == "step-5"
    with pytest.raises(ValueError):
        registry.register_step(_step(
            step_id="step-4", member="guardian",
            slice_id="M-131", branch="crew/guardian/m-131"))
    with pytest.raises(ValueError):
        registry.register_step(_step())
    assert registry.get_step("step-4") is supplied
    assert registry.get_attempt("attempt-1") is attempt
    with pytest.raises(KeyError):
        registry.get_step("step-99")
    with pytest.raises(KeyError):
        registry.get_attempt("attempt-99")
    assert len(registry.list_steps()) == 5
    assert len(registry.list_attempts()) == 1


def test_registry_holds_a_plan_and_reports():
    registry = MergeDisciplineRegistry()
    steps, attempts = registry.register_plan(load_merge_discipline())
    assert len(steps) == 7 and len(attempts) == 5
    assert steps[0].step_id == "step-1"
    assert attempts[0].attempt_id == "attempt-1"
    assert [v.kind for v in registry.verdicts()] == [
        "out_of_order", "missing_test_gate", "line_stopped"]
    assert [v.kind for v in registry.for_member("scribe")] == [
        "out_of_order", "missing_test_gate"]
    assert registry.for_member("guardian") == ()
    assert registry.report().line_for("auditor").merged == ("M-130",)
    assert validate_report(registry, registry.report()) == []
    with pytest.raises(ValueError):
        registry.register_plan("not a plan")


# -- records, plain words, formatters, parser -----------------------------------------


def test_records_and_plain_words():
    plan = load_merge_discipline()
    report = plan.report()
    record = report_record(report)
    assert record["type"] == "merge_report"
    assert record["slice"] == "M-128"
    assert record["count"] == 3
    assert record["clean"] is False
    assert record["out_of_order"] == 1
    assert record["missing_test_gate"] == 1
    assert record["line_stopped"] == 1
    assert len(record["lines"]) == 4
    assert record["news"] is True
    assert "3 verdicts stand for the coordinator" in \
        record["headline"]
    assert report_plain_words(MergeReport(verdicts=())) == \
        "The merge ledger is clean: every line advances in order."
    verdict = report.verdicts[2]
    assert "Line stopped" in plain_words(verdict)
    news = verdict_record(verdict)
    assert news["type"] == "merge_verdict"
    assert news["kind"] == "line_stopped"
    assert news["member"] == "forge_worker"
    assert news["news"] is True
    assert report.by_kind("red") == (verdict,)
    assert report.for_member("forge_worker") == (verdict,)
    assert report.for_member("scribe") == tuple(report.verdicts[:2])


def test_formatters():
    assert format_verdicts([]) == (
        "Merge discipline: clean. No out-of-order merge, "
        "missing test gate or stopped line stands.")
    text = format_verdicts()
    assert text.startswith("Merge discipline: 3 verdicts stand")
    assert "out_of_order" in text
    assert "missing_test_gate" in text
    assert "line_stopped" in text
    verdict = load_merge_discipline().report().verdicts[0]
    assert format_verdict(verdict).startswith(
        "  out_of_order: Out of order:")
    lines = format_lines()
    assert "forge_worker: merged M-125; stopped at M-128." in lines
    assert "auditor: merged M-130; next M-132." in lines
    assert "guardian: merged none; next M-127." in lines
    assert format_lines(MergeReport()) == \
        "Merge lines: no line is planned yet."
    kinds = format_kinds()
    assert kinds.startswith("Verdict kinds:")
    assert "line_stopped" in kinds
    screen = format_merge_screen()
    assert screen.startswith("Merge discipline (M-128) - ")
    assert PLAIN_EXPLANATION in screen
    assert "Merge discipline: 3 verdicts stand" in screen
    assert "Merge lines:" in screen
    assert USAGE in screen
    clean_screen = format_merge_screen(MergeReport(verdicts=()))
    assert "Merge discipline: clean." in clean_screen


def test_parser():
    assert parse_merge_args("") == ("show", None)
    assert parse_merge_args(None) == ("show", None)
    assert parse_merge_args("show") == ("show", None)
    assert parse_merge_args("list") == ("show", None)
    assert parse_merge_args("verdicts") == ("show", None)
    assert parse_merge_args("show scribe") == ("show", "scribe")
    assert parse_merge_args("scribe") == ("show", "scribe")
    assert parse_merge_args("lines") == ("lines", None)
    assert parse_merge_args("kinds") == ("kinds", None)
    for bad in ("show scribe auditor", "kinds please",
                "lines please", "dance party", "show bad member", 3):
        with pytest.raises(ValueError):
            parse_merge_args(bad)


def test_module_purity():
    source = (
        ROOT / "mythic_agent" / "core" / "merge_discipline.py"
    ).read_text(encoding="utf-8")
    assert "subprocess" not in source
    assert "Popen" not in source
    assert "os.system" not in source
    assert "agents.llm" not in source
    assert "import os" not in source
