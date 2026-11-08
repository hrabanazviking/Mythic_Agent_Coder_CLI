"""M-130 The Auditor's veto - pure-layer tests.

TIER: integration

The pure layer is the Auditor's gate as data: the
evidence (cases - which slices stand before the
Auditor, with their titles and builders - the
checks each slice carries, and the results - what
the Auditor's run of each check found, passed or
failed, with the evidence for it) validated as
data, the shipped example veto ledger held in a
data file, a loader that reads a ledger from any
file, the verdicts and gate states derived
mechanically from the evidence alone - a
failed_check veto and an unproven_check veto, the
roadmap's two judgements - a verdict record and a
report record shaped as session news, and a
registry. Nothing here runs a check, executes a
test suite, banks a slice or claims a Part VIII
board: the veto is data only, and the coordinator
acts on the verdicts through later roads.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.crew_members import load_casting
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.auditor_veto import (
    PLAIN_EXPLANATION,
    USAGE,
    VERDICT_KINDS,
    VETO_RESOURCE,
    VETO_SCHEMA,
    VETO_SLICE,
    AuditCase,
    AuditCheck,
    AuditResult,
    AuditorLedger,
    AuditorVetoRegistry,
    GateState,
    VetoReport,
    VetoVerdict,
    build_case,
    build_check,
    build_result,
    build_verdict,
    case_record,
    check_record,
    format_gates,
    format_kinds,
    format_verdict,
    format_verdicts,
    format_veto_screen,
    judge_veto,
    load_auditor_ledger,
    load_auditor_ledger_file,
    normalize_check_name,
    normalize_outcome,
    normalize_verdict_kind,
    parse_veto_args,
    plain_words,
    report_plain_words,
    report_record,
    result_record,
    validate_case,
    validate_check,
    validate_ledger,
    validate_report,
    validate_result,
    validate_verdict,
    verdict_record,
)

ROOT = Path(__file__).resolve().parents[1]


def _case(**kwargs):
    kwargs.setdefault("slice_id", "M-140")
    kwargs.setdefault("title", "Some later slice")
    kwargs.setdefault("builder", "forge_worker")
    return AuditCase(**kwargs)


def _check(**kwargs):
    kwargs.setdefault("slice_id", "M-140")
    kwargs.setdefault("name", "suite-green")
    return AuditCheck(**kwargs)


def _result(**kwargs):
    kwargs.setdefault("slice_id", "M-140")
    kwargs.setdefault("check", "suite-green")
    kwargs.setdefault("outcome", "passed")
    kwargs.setdefault("evidence", "Run on the laptop: all passed.")
    return AuditResult(**kwargs)


def _ledger_data():
    return {
        "schema": VETO_SCHEMA, "slice": VETO_SLICE,
        "keeper": "auditor",
        "cases": [
            {"slice_id": "M-140", "title": "Some later slice",
             "builder": "forge_worker"},
        ],
        "checks": [
            {"slice_id": "M-140", "name": "suite-green"},
        ],
        "results": [
            {"slice_id": "M-140", "check": "suite-green",
             "outcome": "passed",
             "evidence": "Run on the laptop: all passed."},
        ]}


def _write_ledger(tmp_path, data):
    path = tmp_path / "ledger.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def _clean_evidence():
    return {
        "cases": [
            {"slice_id": "M-140", "title": "Some later slice",
             "builder": "forge_worker"},
            {"slice_id": "M-141", "title": "Another slice",
             "builder": "scribe"},
        ],
        "checks": [
            {"slice_id": "M-140", "name": "suite-green"},
            {"slice_id": "M-141", "name": "suite-green"},
        ],
        "results": [
            {"slice_id": "M-140", "check": "suite-green",
             "outcome": "passed", "evidence": "All passed."},
            {"slice_id": "M-141", "check": "suite-green",
             "outcome": "passed", "evidence": "All passed."},
        ]}


# -- constants and word readings --------------------------------------------


def test_constants_and_usage():
    assert VETO_SLICE == "M-130"
    assert VETO_SCHEMA == "mythic.auditor_veto/1"
    assert VETO_RESOURCE == "auditor_veto.yaml"
    assert VERDICT_KINDS == ("failed_check", "unproven_check")
    assert "no slice is done" in PLAIN_EXPLANATION.lower()
    assert "no Part VIII board" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /veto")
    screen = format_veto_screen()
    assert USAGE in screen
    assert PLAIN_EXPLANATION in screen
    # The Auditor is the shipped M-121 casting's member,
    # composed by import, never re-cast here.
    casting = load_casting()
    auditor = casting.get("auditor")
    assert auditor.office == "auditor"


def test_word_readings_and_refusals():
    assert normalize_check_name("Suite Green") == "suite-green"
    assert normalize_check_name("suite_green") == "suite-green"
    assert normalize_check_name("banking-order-kept") == \
        "banking-order-kept"
    for bad in ("", "  ", "-leading", "trailing-", "two--dash",
                "bang!", "a/b", None, 7):
        with pytest.raises(ValueError):
            normalize_check_name(bad)
    assert normalize_outcome("passed") == "passed"
    assert normalize_outcome("GREEN") == "passed"
    assert normalize_outcome("fail") == "failed"
    assert normalize_outcome("red") == "failed"
    for bad in ("maybe", "skipped", "", None):
        with pytest.raises(ValueError):
            normalize_outcome(bad)
    assert normalize_verdict_kind("failed") == "failed_check"
    assert normalize_verdict_kind("Failed-Check") == "failed_check"
    assert normalize_verdict_kind("no_evidence") == \
        "unproven_check"
    assert normalize_verdict_kind("unchecked") == "unproven_check"
    for bad in ("passed", "waived", "", None):
        with pytest.raises(ValueError):
            normalize_verdict_kind(bad)


def test_construction_and_records():
    case = _case(case_id="case-9")
    assert case.slice_id == "M-140"
    assert case.to_record() == {
        "type": "veto_case", "slice": "M-130",
        "case_id": "case-9", "slice_id": "M-140",
        "title": "Some later slice", "builder": "forge_worker"}
    check = _check()
    assert check.required is True
    assert check.to_record()["type"] == "veto_check"
    assert check.to_record()["name"] == "suite-green"
    result = _result()
    assert result.to_record()["type"] == "veto_result"
    assert result.to_record()["outcome"] == "passed"
    # Slice ids read as the M-124 layer reads them.
    assert _case(slice_id="m-141").slice_id == "M-141"
    with pytest.raises(ValueError):
        _case(slice_id="M-999")
    with pytest.raises(ValueError):
        _case(builder="not a member!")


def test_evidence_refusals():
    with pytest.raises(ValueError):
        validate_case({"slice_id": "M-140", "title": "T",
                       "builder": "scribe", "surprise": 1})
    with pytest.raises(ValueError):
        validate_case({"slice_id": "M-140", "slice": "M-141",
                       "title": "T", "builder": "scribe"})
    with pytest.raises(ValueError):
        validate_case({"slice_id": "M-140", "builder": "scribe"})
    with pytest.raises(ValueError):
        validate_check({"slice_id": "M-140", "name": "x",
                        "required": "yes"})
    with pytest.raises(ValueError):
        validate_check({"slice_id": "M-140", "check": "a",
                        "check_name": "b"})
    with pytest.raises(ValueError):
        validate_result({"slice_id": "M-140",
                         "check": "suite-green",
                         "outcome": "passed"})
    with pytest.raises(ValueError):
        validate_result({"slice_id": "M-140",
                         "check": "suite-green",
                         "outcome": "maybe",
                         "evidence": "It seemed fine."})
    with pytest.raises(ValueError):
        validate_result({"slice_id": "M-140",
                         "check": "suite-green",
                         "outcome": "passed", "evidence": ""})
    with pytest.raises(ValueError):
        validate_result({"slice_id": "M-140",
                         "check": "suite-green",
                         "outcome": "passed", "status": "failed",
                         "evidence": "Two spellings disagree."})
    with pytest.raises(ValueError):
        validate_case("not a mapping")


def test_validator_aliases():
    case = validate_case({
        "slice": "m-140", "title": "T", "builder_id": "scribe",
        "id": "case-3"})
    assert case == AuditCase(
        case_id="case-3", slice_id="M-140", title="T",
        builder="scribe")
    check = validate_check({
        "slice": "M-140", "check_name": "Suite_Green",
        "is_required": False})
    assert check.name == "suite-green"
    assert check.required is False
    result = validate_result({
        "slice": "M-140", "name": "suite-green",
        "status": "green", "note": "All passed."})
    assert result.outcome == "passed"
    assert result.evidence == "All passed."
    assert build_case(case) is case
    assert build_check({"slice_id": "M-140",
                        "name": "suite-green"}) == _check()
    assert build_result(result) is result
    with pytest.raises(ValueError):
        build_case(42)


# -- the shipped example ----------------------------------------------------


def test_shipped_ledger_loads_as_the_example():
    ledger = load_auditor_ledger()
    assert ledger.keeper == "auditor"
    assert [c.slice_id for c in ledger.cases] == [
        "M-127", "M-128", "M-129"]
    assert len(ledger.checks) == 6
    assert len(ledger.results) == 5
    raw = yaml.safe_load(
        (ROOT / "mythic_agent" / "data" / VETO_RESOURCE)
        .read_text(encoding="utf-8"))
    assert validate_ledger(raw, require_example=True) == []
    assert ledger.case_for("M-128").builder == "forge_worker"
    assert [c.name for c in ledger.checks_for("M-127")] == [
        "suite-green", "neighbour-suites-green"]
    with pytest.raises(KeyError):
        ledger.case_for("M-130")


def test_shipped_example_check_refuses_drift():
    raw = yaml.safe_load(
        (ROOT / "mythic_agent" / "data" / VETO_RESOURCE)
        .read_text(encoding="utf-8"))
    drifted = dict(raw, keeper="scribe")
    assert validate_ledger(drifted, require_example=True)
    with pytest.raises(ValidationError):
        load_auditor_ledger(drifted)
    short = yaml.safe_load(yaml.safe_dump(raw))
    short["results"] = short["results"][:-1]
    assert validate_ledger(short, require_example=True)
    flipped = yaml.safe_load(yaml.safe_dump(raw))
    flipped["results"][3]["outcome"] = "passed"
    assert validate_ledger(flipped, require_example=True)


def test_example_ledger_yields_exactly_two_verdicts():
    report = load_auditor_ledger().report()
    assert [(v.kind, v.slice_id, v.check) for v in report.verdicts] \
        == [("failed_check", "M-129", "suite-green"),
            ("unproven_check", "M-127", "suite-green")]
    assert report.vetoed is True
    assert report.is_clean is False
    assert report.slices == ("M-127", "M-128", "M-129")
    record = report.to_record()
    assert record["count"] == 2
    assert record["failed_check"] == 1
    assert record["unproven_check"] == 1
    gate = report.gate_for("M-128")
    assert gate.status == "passed" and gate.is_passed
    assert (gate.required, gate.proven) == (2, 2)
    gate127 = report.gate_for("M-127")
    assert gate127.status == "vetoed"
    assert (gate127.proven, gate127.failed,
            gate127.unproven) == (1, 0, 1)
    gate129 = report.gate_for("M-129")
    assert (gate129.proven, gate129.failed,
            gate129.unproven) == (1, 1, 0)
    assert [v.kind for v in report.by_kind("failed")] == [
        "failed_check"]
    assert [v.slice_id for v in report.for_slice("m-127")] == [
        "M-127"]
    with pytest.raises(KeyError):
        report.gate_for("M-130")


# -- the judge ---------------------------------------------------------------


def test_clean_evidence_yields_no_verdicts():
    evidence = _clean_evidence()
    assert judge_veto(evidence) == ()
    report = AuditorLedger(
        cases=evidence["cases"], checks=evidence["checks"],
        results=evidence["results"],
        keeper="auditor").report()
    assert report.is_clean and not report.vetoed
    assert all(g.is_passed for g in report.gates)
    assert format_verdicts(evidence).startswith(
        "The Auditor's veto: clean.")


def test_failed_verdicts_come_first_and_optional_never_vetoes():
    evidence = {
        "cases": [
            {"slice_id": "M-140", "title": "First",
             "builder": "scribe"},
            {"slice_id": "M-141", "title": "Second",
             "builder": "forge_worker"},
        ],
        "checks": [
            {"slice_id": "M-140", "name": "suite-green"},
            {"slice_id": "M-140", "name": "style-pass",
             "required": False},
            {"slice_id": "M-141", "name": "suite-green"},
        ],
        "results": [
            {"slice_id": "M-141", "check": "suite-green",
             "outcome": "failed", "evidence": "Two failed."},
            {"slice_id": "M-140", "check": "style-pass",
             "outcome": "failed",
             "evidence": "Style only; not required."},
        ]}
    verdicts = judge_veto(evidence)
    # Judgement order is by kind, not by case order, and
    # the optional check's failure earns no verdict.
    assert [(v.kind, v.slice_id) for v in verdicts] == [
        ("failed_check", "M-141"),
        ("unproven_check", "M-140")]
    report = AuditorLedger(
        cases=evidence["cases"], checks=evidence["checks"],
        results=evidence["results"], keeper="auditor").report()
    gate = report.gate_for("M-140")
    assert (gate.required, gate.proven, gate.failed,
            gate.unproven) == (1, 0, 0, 1)


def test_stray_evidence_judges_nothing():
    evidence = _clean_evidence()
    evidence["checks"].append(
        {"slice_id": "M-150", "name": "suite-green"})
    evidence["results"].append(
        {"slice_id": "M-150", "check": "suite-green",
         "outcome": "failed", "evidence": "No case stands."})
    evidence["results"].append(
        {"slice_id": "M-140", "check": "never-carried",
         "outcome": "failed", "evidence": "Not carried."})
    assert judge_veto(evidence) == ()


def test_verdict_and_gate_state_validation():
    verdict = build_verdict(
        kind="failed", slice_id="m-129", check="Suite Green",
        title="T", detail="D")
    assert verdict.kind == "failed_check"
    assert verdict.slice_id == "M-129"
    assert verdict.check == "suite-green"
    with pytest.raises(ValueError):
        validate_verdict({"kind": "waived",
                          "slice_id": "M-129",
                          "check": "suite-green",
                          "title": "T", "detail": "D"})
    with pytest.raises(ValueError):
        GateState(slice_id="M-140", title="T",
                  builder="scribe", status="passed",
                  required=2, proven=1, failed=0, unproven=0)
    with pytest.raises(ValueError):
        GateState(slice_id="M-140", title="T",
                  builder="scribe", status="passed",
                  required=1, proven=0, failed=1, unproven=0)
    with pytest.raises(ValueError):
        GateState(slice_id="M-140", title="T",
                  builder="scribe", status="vetoed",
                  required=-1, proven=0, failed=0, unproven=0)
    gate = GateState(
        slice_id="M-140", title="T", builder="scribe",
        status="vetoed", required=1, proven=0, failed=0,
        unproven=1)
    assert gate.to_record()["type"] == "veto_gate"


def test_report_validation_names_a_wrong_report():
    ledger = load_auditor_ledger()
    report = ledger.report()
    assert validate_report(ledger, report) == []
    shrunk = VetoReport(
        verdicts=report.verdicts[:1], gates=report.gates,
        vetoed=True, slices=report.slices)
    problems = validate_report(ledger, shrunk)
    assert problems and "does not hold exactly" in problems[0]
    assert validate_report(ledger, "not a report")


# -- the ledger --------------------------------------------------------------


def test_ledger_construction_and_mapping_refusals():
    data = _ledger_data()
    ledger = AuditorLedger(
        cases=data["cases"], checks=data["checks"],
        results=data["results"], keeper="auditor")
    assert ledger.report().is_clean
    assert validate_ledger(data) == []
    with pytest.raises(ValueError):
        AuditorLedger(cases=[], keeper="auditor")
    with pytest.raises(ValueError):
        AuditorLedger(
            cases=[_case(), _case()], checks=[_check()],
            keeper="auditor")
    with pytest.raises(ValueError):
        AuditorLedger(
            cases=[_case()], checks=[_check(), _check()],
            keeper="auditor")
    with pytest.raises(ValueError):
        AuditorLedger(
            cases=[_case()], checks=[_check()],
            results=[_result(), _result()], keeper="auditor")
    with pytest.raises(ValueError):
        AuditorLedger(cases=[_case()], keeper="auditor")
    bad = dict(data, schema="mythic.other/1")
    assert validate_ledger(bad)
    bad = dict(data, slice="M-131")
    assert validate_ledger(bad)
    bad = dict(data, surprise=[])
    assert validate_ledger(bad)
    bad = _ledger_data()
    bad["cases"] = bad["cases"] + [bad["cases"][0]]
    assert any("audited twice" in p
               for p in validate_ledger(bad))
    bad = _ledger_data()
    bad["checks"] = []
    assert any("carries no checks" in p
               for p in validate_ledger(bad))
    assert validate_ledger("not a mapping")


def test_ledger_file_roundtrip_and_refusals(tmp_path):
    path = _write_ledger(tmp_path, _ledger_data())
    ledger = load_auditor_ledger_file(path)
    assert ledger.keeper == "auditor"
    assert ledger.report().is_clean
    with pytest.raises(FileNotFoundError):
        load_auditor_ledger_file(tmp_path / "missing.yaml")
    bad = _ledger_data()
    bad["keeper"] = "not a member!"
    path = _write_ledger(tmp_path, bad)
    with pytest.raises(ValidationError):
        load_auditor_ledger_file(path)


# -- the registry ------------------------------------------------------------


def test_registry_deterministic_ids_and_refusals():
    registry = AuditorVetoRegistry()
    case = registry.register_case(_case())
    assert case.case_id == "case-1"
    check = registry.register_check(_check())
    assert check.check_id == "check-1"
    result = registry.register_result(_result())
    assert result.result_id == "result-1"
    named = registry.register_case(_case(
        case_id="case-3", slice_id="M-141",
        title="Another slice", builder="scribe"))
    assert named.case_id == "case-3"
    fresh = registry.register_case(_case(
        slice_id="M-142", title="Third slice",
        builder="cartographer"))
    assert fresh.case_id == "case-2"
    with pytest.raises(ValueError):
        registry.register_case(_case())
    with pytest.raises(ValueError):
        registry.register_case(_case(
            case_id="case-1", slice_id="M-150",
            title="Fourth slice"))
    with pytest.raises(ValueError):
        registry.register_check(_check())
    with pytest.raises(ValueError):
        registry.register_result(_result())
    assert registry.get_case("case-1") is case
    assert registry.get_check("check-1") is check
    assert registry.get_result("result-1") is result
    with pytest.raises(KeyError):
        registry.get_case("case-99")
    assert [c.slice_id for c in registry.list_cases()] == [
        "M-140", "M-141", "M-142"]


def test_registry_holds_a_ledger_and_judges_it():
    registry = AuditorVetoRegistry()
    cases, checks, results = registry.register_ledger(
        load_auditor_ledger())
    assert len(cases) == 3 and len(checks) == 6
    assert len(results) == 5
    assert [v.kind for v in registry.verdicts()] == [
        "failed_check", "unproven_check"]
    report = registry.report()
    assert report.gate_for("M-128").is_passed
    assert [v.check for v in registry.for_slice("M-127")] == [
        "suite-green"]
    with pytest.raises(ValueError):
        registry.register_ledger("not a ledger")
    with pytest.raises(ValueError):
        registry.register_ledger(load_auditor_ledger())


# -- records, formatters, parser --------------------------------------------


def test_records_and_plain_words():
    case = case_record(_case())
    assert case["news"] is True
    assert "stands before the Auditor" in case["headline"]
    check = check_record(_check())
    assert "carries the Auditor's suite-green check" in \
        check["headline"]
    optional = check_record(_check(name="style-pass",
                                   required=False))
    assert "(not required)" in optional["headline"]
    result = result_record(_result(outcome="failed"))
    assert result["headline"].endswith(": failed.")
    ledger = load_auditor_ledger()
    verdict = ledger.report().verdicts[0]
    record = verdict_record(verdict)
    assert record["type"] == "veto_verdict"
    assert record["headline"] == plain_words(verdict)
    assert format_verdict(verdict).startswith(
        "  failed_check: Vetoed: M-129")
    report = report_record(ledger.report())
    assert report["type"] == "veto_report"
    assert report["count"] == 2
    assert len(report["verdicts"]) == 2
    assert len(report["gates"]) == 3
    assert "2 vetoes stand" in report_plain_words(
        ledger.report())
    clean = AuditorLedger(
        cases=_clean_evidence()["cases"],
        checks=_clean_evidence()["checks"],
        results=_clean_evidence()["results"],
        keeper="auditor").report()
    assert report_plain_words(clean).startswith("No veto stands")


def test_formatters():
    text = format_verdicts()
    assert "The Auditor's veto: 2 vetoes stand" in text
    assert "failed_check" in text and "unproven_check" in text
    gates = format_gates()
    assert "M-128 (Merge discipline): passed - 2 of 2" in gates
    assert "M-127 (Cycle and deadlock detection grown): " \
        "VETOED - 0 failed, 1 unproven" in gates
    assert format_gates(AuditorVetoRegistry()) == \
        "Slice gates: no case is held yet."
    assert format_kinds().startswith("Verdict kinds:")
    screen = format_veto_screen()
    assert screen.startswith("The Auditor's veto (M-130) - ")
    assert "Slice gates:" in screen


def test_parser():
    assert parse_veto_args("") == ("show", None)
    assert parse_veto_args(None) == ("show", None)
    assert parse_veto_args("show") == ("show", None)
    assert parse_veto_args("verdicts") == ("show", None)
    assert parse_veto_args("show m-127") == ("show", "M-127")
    assert parse_veto_args("M-129") == ("show", "M-129")
    assert parse_veto_args("gates") == ("gates", None)
    assert parse_veto_args("kinds") == ("kinds", None)
    for bad in ("dance", "dance party", "show M-999",
                "show M-127 extra", "gates now", 42):
        with pytest.raises(ValueError) as excinfo:
            parse_veto_args(bad)
        assert str(excinfo.value) == USAGE


def test_module_purity():
    source = (
        ROOT / "mythic_agent" / "core" / "auditor_veto.py"
    ).read_text(encoding="utf-8")
    assert "subprocess" not in source
    assert "Popen" not in source
    assert "os.system" not in source
    assert "agents.llm" not in source
    assert "import os" not in source


# -- agent layer -----------------------------------------------------------
#
# M-130 agent layer: the agent holds an
# AuditorVetoRegistry for the session (session
# state only, no new setting), a ledger is recorded
# by being registered - published as its case_record
# / check_record / result_record session news
# through the checkpoint road, deduped per evidence
# id - the verdicts are published as verdict_record
# session news and the report as ONE report_record
# session event holding every verdict and gate,
# deduped per report, and the /veto surface rides
# both roads on the pure parser + formatters.
# Status, find, ledger and report reads register
# and publish nothing. This layer runs no check,
# executes no test suite, banks nothing and builds
# no board - Part VIII does not exist yet, so the
# screen is where the verdicts are visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _veto_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


class TestVetoAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.veto_status()
        assert status["cases"] == []
        assert status["checks"] == []
        assert status["results"] == []
        assert status["ledger"]["keeper"] == "auditor"
        assert len(status["ledger"]["cases"]) == 3
        assert len(status["ledger"]["checks"]) == 6
        assert len(status["ledger"]["results"]) == 5
        assert status["report"]["type"] == "veto_report"
        assert status["report"]["count"] == 2
        assert status["report"]["vetoed"] is True
        assert "The Auditor's veto: 2 vetoes stand" in \
            status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        assert agent._auditor_veto_registry() is \
            agent._auditor_veto_registry()
        assert agent._auditor_veto_store is \
            agent._auditor_veto_registry()

    def test_reads_register_and_publish_nothing(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.veto_status()
        found = agent.find_veto_verdicts("M-129")
        assert [v.kind for v in found] == ["failed_check"]
        assert agent.auditor_ledger().keeper == "auditor"
        report = agent.veto_report()
        assert [v.kind for v in report.verdicts] == [
            "failed_check", "unproven_check"]
        registry = agent._auditor_veto_registry()
        assert registry.list_cases() == ()
        assert registry.list_checks() == ()
        assert registry.list_results() == ()
        for kind in ("veto_case", "veto_check",
                     "veto_result", "veto_verdict",
                     "veto_report"):
            assert _veto_events(store, session_id, kind) == []
        agent.close()

    def test_unheld_evidence_raises_keyerror(self, agent):
        with pytest.raises(KeyError):
            agent.get_veto_case("case-1")
        with pytest.raises(KeyError):
            agent.get_veto_check("check-1")
        with pytest.raises(KeyError):
            agent.get_veto_result("result-1")

    def test_find_passing_slice_raises_keyerror(self, agent):
        with pytest.raises(KeyError):
            agent.find_veto_verdicts("M-128")

    def test_status_after_register_shows_the_held_evidence(
            self, agent):
        agent.register_veto_case(_case())
        agent.register_veto_check(_check())
        agent.register_veto_result(_result())
        status = agent.veto_status()
        assert [c["slice_id"] for c in status["cases"]] == [
            "M-140"]
        assert [c["name"] for c in status["checks"]] == [
            "suite-green"]
        assert "The Auditor's veto: clean." in status["screen"]
        assert len(status["ledger"]["cases"]) == 3


class TestVetoAgentRegister:
    def test_register_case_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_veto_case(_case())
        assert outcome["case"]["case_id"] == "case-1"
        assert outcome["record"]["type"] == "veto_case"
        events = _veto_events(store, session_id, "veto_case")
        assert len(events) == 1
        assert events[0]["slice_id"] == "M-140"
        # The same record is never published twice.
        agent._publish_veto_record(outcome["record"])
        assert len(_veto_events(
            store, session_id, "veto_case")) == 1
        # A foreign record type is refused on this road.
        agent._publish_veto_record(
            verdict_record(build_verdict(
                kind="failed_check", slice_id="M-140",
                check="suite-green", title="T", detail="D")))
        assert _veto_events(store, session_id, "veto_verdict") \
            == []
        agent.close()

    def test_register_check_and_result_publish_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_veto_case(_case())
        check_outcome = agent.register_veto_check(_check())
        assert check_outcome["check"]["check_id"] == "check-1"
        result_outcome = agent.register_veto_result(_result())
        assert result_outcome["result"]["result_id"] == \
            "result-1"
        assert len(_veto_events(
            store, session_id, "veto_check")) == 1
        assert len(_veto_events(
            store, session_id, "veto_result")) == 1
        agent._publish_veto_record(result_outcome["record"])
        assert len(_veto_events(
            store, session_id, "veto_result")) == 1
        agent.close()

    def test_record_ledger_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_auditor_ledger()
        assert outcome["count"] == 14
        assert len(outcome["cases"]) == 3
        assert len(outcome["checks"]) == 6
        assert len(outcome["results"]) == 5
        assert len(_veto_events(
            store, session_id, "veto_case")) == 3
        assert len(_veto_events(
            store, session_id, "veto_check")) == 6
        assert len(_veto_events(
            store, session_id, "veto_result")) == 5
        assert agent.auditor_ledger().keeper == "auditor"
        agent.close()

    def test_record_same_ledger_twice_refuses(self, agent):
        agent.record_auditor_ledger()
        with pytest.raises(ValueError):
            agent.record_auditor_ledger()

    def test_ledger_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_ledger(tmp_path, _ledger_data())
        ledger = load_auditor_ledger_file(path)
        outcome = agent.record_auditor_ledger(ledger)
        assert outcome["count"] == 3
        assert agent.veto_report().is_clean

    def test_find_prefers_the_held_evidence(self, agent):
        agent.register_veto_case(_case(
            slice_id="M-129", title="Heterogeneous crews",
            builder="scribe"))
        agent.register_veto_check(_check(slice_id="M-129"))
        agent.register_veto_result(_result(slice_id="M-129"))
        # The held evidence answers now: M-129 is proven
        # there, so the example's veto no longer answers.
        with pytest.raises(KeyError):
            agent.find_veto_verdicts("M-129")


class TestVetoAgentReport:
    def test_report_publishes_one_report_event_for_all_verdicts(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.record_auditor_ledger()
        outcome = agent.report_veto()
        assert outcome["count"] == 2
        assert outcome["record"]["type"] == "veto_report"
        assert outcome["record"]["count"] == 2
        assert "The Auditor's veto: 2 vetoes stand" in \
            outcome["screen"]
        verdicts = _veto_events(store, session_id, "veto_verdict")
        assert len(verdicts) == 2
        reports = _veto_events(store, session_id, "veto_report")
        # ONE report event holds both verdicts and all gates.
        assert len(reports) == 1
        assert reports[0]["count"] == 2
        assert len(reports[0]["verdicts"]) == 2
        assert len(reports[0]["gates"]) == 3
        # Reporting again on the same evidence publishes
        # nothing new.
        agent.report_veto()
        assert len(_veto_events(
            store, session_id, "veto_verdict")) == 2
        assert len(_veto_events(
            store, session_id, "veto_report")) == 1
        # Newly held evidence grows the report: a new report.
        agent.register_veto_case(_case(
            slice_id="M-131", title="Research swarms",
            builder="cartographer"))
        agent.register_veto_check(_check(slice_id="M-131"))
        agent.register_veto_result(_result(
            slice_id="M-131", outcome="failed",
            evidence="The swarm returned no sources."))
        outcome = agent.report_veto()
        assert outcome["count"] == 3
        assert len(_veto_events(
            store, session_id, "veto_report")) == 2
        agent.close()

    def test_report_with_clean_evidence_publishes_a_clean_report_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_veto_case(_case())
        agent.register_veto_check(_check())
        agent.register_veto_result(_result())
        outcome = agent.report_veto()
        assert outcome["count"] == 0
        assert outcome["record"]["clean"] is True
        assert outcome["screen"].startswith(
            "The Auditor's veto: clean.")
        assert _veto_events(store, session_id, "veto_verdict") \
            == []
        reports = _veto_events(store, session_id, "veto_report")
        assert len(reports) == 1
        assert reports[0]["clean"] is True
        agent.report_veto()
        assert len(_veto_events(
            store, session_id, "veto_report")) == 1
        agent.close()

    def test_no_run_or_banking_road_for_veto(self, agent):
        # This layer holds the audit as data: it runs no
        # check, executes no test suite, banks nothing
        # and builds no board - Part VIII does not exist
        # yet, and the banking road is a later slice.
        assert not hasattr(agent, "run_veto_check")
        assert not hasattr(agent, "execute_suite")
        assert not hasattr(agent, "veto_board")


class TestVetoTerminalSurface:
    def test_show_gates_and_kinds(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/veto")
        assert "The Auditor's veto: 2 vetoes stand" in text
        _, _, text = _slash(agent, "/veto show M-129")
        assert "The Auditor's veto: 1 vetoes stand" in text
        assert "failed_check" in text
        _, _, text = _slash(agent, "/veto gates")
        assert "M-128 (Merge discipline): passed" in text
        assert "VETOED" in text
        _, _, text = _slash(agent, "/veto kinds")
        assert text.startswith("Verdict kinds:")

    def test_bare_slice_shows_theirs(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/veto M-127")
        assert "unproven_check" in text
        _, _, text = _slash(agent, "/veto M-129")
        assert "failed_check" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert "/veto [show|show <slice>|gates|kinds]" in text
        _, _, text = _slash(agent, "/veto dance")
        assert text == USAGE
        _, _, text = _slash(agent, "/veto dance party")
        assert text == USAGE


@pytest.fixture()
def veto_handler(agent, monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.agents.llm import AGENT_REGISTRY
    published = []
    monkeypatch.setattr(
        handler_module, "publish_sync",
        lambda event, **kwargs: published.append((event, kwargs)))
    AGENT_REGISTRY["Primary"] = agent
    instance = CommandHandler.__new__(CommandHandler)
    instance.published = published
    yield instance
    AGENT_REGISTRY.pop("Primary", None)


def _veto_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestVetoCommand:
    def test_show_is_default(self, veto_handler, agent):
        veto_handler._handle_veto("")
        assert "The Auditor's veto: 2 vetoes stand" in \
            _veto_published_text(veto_handler)

    def test_show_one_gates_and_kinds(self, veto_handler, agent):
        veto_handler._handle_veto("show M-129")
        assert "failed_check" in _veto_published_text(veto_handler)
        veto_handler._handle_veto("gates")
        assert "VETOED" in _veto_published_text(veto_handler)
        veto_handler._handle_veto("kinds")
        assert "Verdict kinds:" in _veto_published_text(
            veto_handler)

    def test_bad_grammar_is_published(self, veto_handler, agent):
        veto_handler._handle_veto("dance party")
        assert USAGE in _veto_published_text(veto_handler)


class TestChatScreenRoutingVeto:
    def test_veto_routes_as_system_command(self, monkeypatch):
        from mythic_agent.ui.screens import chat_screen
        from mythic_agent.ui.screens.chat_screen import MainChatScreen

        class _FakeLog:
            def __init__(self):
                self.lines = []

            def write(self, *args, **kwargs):
                self.lines.append(" ".join(str(a) for a in args))

        calls = []
        monkeypatch.setattr(
            chat_screen.SecureAPI, "publish_system_command",
            staticmethod(lambda cmd, args: calls.append((cmd, args))))
        screen = MainChatScreen.__new__(MainChatScreen)
        screen.handle_command("/veto kinds", _FakeLog())
        assert calls == [("/veto", "kinds")]
