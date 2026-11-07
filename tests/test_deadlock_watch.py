"""M-127 Cycle and deadlock detection - pure-layer tests.

TIER: integration

The pure layer is the coordinator's watch as data:
the evidence (delegations between members, and the
claims members hold on slices at paths) validated
as data, the shipped example watch held in a data
file, a loader that reads a watch from any file,
the findings derived mechanically from the evidence
alone - a delegation cycle, a merge conflict and
duplicated work, the roadmap's three hazards - a
finding record and a report record shaped as
session news, and a registry. Nothing here spawns
a crew, stops a member, runs git or claims a Part
VIII board: detection is data only, and the
coordinator acts on the findings through later
roads.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.crew_members import load_casting
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.deadlock_watch import (
    FINDING_KINDS,
    PLAIN_EXPLANATION,
    USAGE,
    WATCH_RESOURCE,
    WATCH_SCHEMA,
    WATCH_SLICE,
    Claim,
    DeadlockWatch,
    DeadlockWatchRegistry,
    Delegation,
    Finding,
    WatchReport,
    build_claim,
    build_delegation,
    build_finding,
    claim_record,
    delegation_record,
    detect_findings,
    finding_record,
    format_deadlock_screen,
    format_finding,
    format_findings,
    format_kinds,
    load_deadlock_watch,
    load_deadlock_watch_file,
    normalize_finding_kind,
    normalize_slice_id,
    parse_deadlock_args,
    plain_words,
    report_plain_words,
    report_record,
    validate_claim,
    validate_delegation,
    validate_finding,
    validate_report,
    validate_watch,
)

ROOT = Path(__file__).resolve().parents[1]


def _casting():
    return load_casting().members


def _delegation(**kwargs):
    kwargs.setdefault("delegator", "scribe")
    kwargs.setdefault("delegatee", "auditor")
    kwargs.setdefault("slice_id", "M-127")
    return Delegation(**kwargs)


def _claim(**kwargs):
    kwargs.setdefault("member", "scribe")
    kwargs.setdefault("slice_id", "M-127")
    kwargs.setdefault("path", "mythic_agent/core/keeper.py")
    return Claim(**kwargs)


def _watch_data():
    return {
        "schema": WATCH_SCHEMA, "slice": WATCH_SLICE,
        "keeper": "guardian",
        "delegations": [
            {"delegator": "auditor", "delegatee": "scribe",
             "slice_id": "M-127"},
            {"delegator": "scribe", "delegatee": "auditor",
             "slice_id": "M-127"},
        ],
        "claims": [
            {"member": "guardian", "slice_id": "M-127",
             "path": "mythic_agent/core/deadlock_watch.py"},
        ]}


def _write_watch(tmp_path, data):
    path = tmp_path / "watch.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def _clean_evidence():
    return {
        "delegations": [
            {"delegator": "scribe", "delegatee": "auditor",
             "slice_id": "M-127"},
            {"delegator": "auditor", "delegatee": "guardian",
             "slice_id": "M-127"},
        ],
        "claims": [
            {"member": "scribe", "slice_id": "M-127",
             "path": "mythic_agent/core/keeper.py"},
            {"member": "auditor", "slice_id": "M-128",
             "path": "mythic_agent/core/metrics.py"},
        ]}


# -- constants and word readings --------------------------------------------


def test_constants_and_usage():
    assert WATCH_SLICE == "M-127"
    assert WATCH_SCHEMA == "mythic.deadlock_watch/1"
    assert WATCH_RESOURCE == "deadlock_watch.yaml"
    assert FINDING_KINDS == (
        "delegation_cycle", "merge_conflict", "duplicated_work")
    assert USAGE.startswith("Usage: /deadlock")
    assert "kinds" in USAGE
    assert "coordinator, not by the human" in PLAIN_EXPLANATION
    assert "no Part VIII board" in PLAIN_EXPLANATION
    assert "spawns no crew" in PLAIN_EXPLANATION
    assert "runs no git" in PLAIN_EXPLANATION
    assert "as data only" in PLAIN_EXPLANATION


def test_kind_readings_and_refusals():
    assert normalize_finding_kind("cycle") == "delegation_cycle"
    assert normalize_finding_kind("Deadlock") == "delegation_cycle"
    assert normalize_finding_kind("delegation-cycles") == \
        "delegation_cycle"
    assert normalize_finding_kind("CONFLICTS") == "merge_conflict"
    assert normalize_finding_kind("merge_conflict") == \
        "merge_conflict"
    assert normalize_finding_kind("duplicate") == "duplicated_work"
    assert normalize_finding_kind("Duplicated-Work") == \
        "duplicated_work"
    for bad in ("stall", "wait", "", None, 3):
        with pytest.raises(ValueError):
            normalize_finding_kind(bad)
    # Slice readings are composed from the M-124 layer.
    assert normalize_slice_id("m-127") == "M-127"
    with pytest.raises(ValueError):
        normalize_slice_id("127")


# -- the evidence records ----------------------------------------------------


def test_delegation_and_claim_construction_and_records():
    delegation = _delegation()
    assert delegation.is_self_delegation is False
    record = delegation.to_record()
    assert record["type"] == "crew_delegation"
    assert record["slice"] == "M-127"
    assert record["delegator"] == "scribe"
    # A self-delegation is well-formed evidence: the
    # detector, not the validator, catches it.
    assert _delegation(delegatee="scribe").is_self_delegation is True
    claim = _claim()
    claim_record_dict = claim.to_record()
    assert claim_record_dict["type"] == "crew_claim"
    assert claim_record_dict["path"] == \
        "mythic_agent/core/keeper.py"
    news = delegation_record(delegation)
    assert news["news"] is True
    assert news["headline"] == "scribe delegates M-127 to auditor."
    news = claim_record(claim)
    assert news["news"] is True
    assert "scribe holds M-127" in news["headline"]


def test_evidence_refusals():
    with pytest.raises(ValueError):
        _delegation(delegator="bad member")
    with pytest.raises(ValueError):
        _delegation(slice_id="M-999")
    with pytest.raises(ValueError):
        _delegation(slice_id="127")
    with pytest.raises(ValueError):
        _claim(member="")
    with pytest.raises(ValueError):
        _claim(path="/absolute/path.py")
    with pytest.raises(ValueError):
        _claim(path="mythic_agent/../secret.py")
    with pytest.raises(ValueError):
        _claim(path="mythic_agent\\core\\keeper.py")


def test_evidence_validator_aliases_and_refusals():
    delegation = validate_delegation(
        {"from_member": "scribe", "to_member": "auditor",
         "slice": "m-127", "id": "delegation-9"})
    assert delegation.delegator == "scribe"
    assert delegation.delegatee == "auditor"
    assert delegation.slice_id == "M-127"
    assert delegation.delegation_id == "delegation-9"
    assert build_delegation(delegation) is delegation
    assert build_delegation(
        delegator="scribe", delegatee="auditor",
        slice_id="M-127") == _delegation()
    with pytest.raises(ValueError):
        validate_delegation(
            {"delegator": "scribe", "from_member": "auditor",
             "delegatee": "auditor", "slice_id": "M-127"})
    with pytest.raises(ValueError):
        validate_delegation(
            {"delegator": "scribe", "delegatee": "auditor",
             "slice_id": "M-127", "surprise": 1})
    with pytest.raises(ValueError):
        validate_delegation({"delegator": "scribe"})
    with pytest.raises(ValueError):
        validate_delegation("not a delegation")
    claim = validate_claim(
        {"member_id": "scribe", "slice": "m-127",
         "worktree_path": "mythic_agent/core/keeper.py",
         "id": "claim-9"})
    assert claim.member == "scribe"
    assert claim.claim_id == "claim-9"
    assert build_claim(claim) is claim
    with pytest.raises(ValueError):
        validate_claim(
            {"member": "scribe", "slice_id": "M-127",
             "path": "a/b.py", "worktree_path": "a/c.py"})
    with pytest.raises(ValueError):
        validate_claim({"member": "scribe"})


# -- the shipped example watch -----------------------------------------------


def test_shipped_watch_loads_as_the_example():
    watch = load_deadlock_watch()
    assert watch.keeper == "guardian"
    assert len(watch.delegations) == 5
    assert len(watch.claims) == 5
    assert [(d.delegator, d.delegatee) for d in watch.delegations] == [
        ("cartographer", "architect"),
        ("architect", "forge_worker"),
        ("forge_worker", "cartographer"),
        ("scribe", "auditor"),
        ("auditor", "guardian"),
    ]
    assert [c.path for c in watch.claims_for("guardian")] == [
        "mythic_agent/core/deadlock_watch.py"]
    assert len(watch.delegations_for("auditor")) == 2
    # Every member named is a shipped member.
    member_ids = {m.member_id for m in _casting()}
    for delegation in watch.delegations:
        assert delegation.delegator in member_ids
        assert delegation.delegatee in member_ids
    for claim in watch.claims:
        assert claim.member in member_ids
    assert validate_watch(
        yaml.safe_load(
            (ROOT / "mythic_agent" / "data" / WATCH_RESOURCE)
            .read_text(encoding="utf-8")),
        require_example=True) == []


def test_shipped_example_check_refuses_drift():
    data = yaml.safe_load(
        (ROOT / "mythic_agent" / "data" / WATCH_RESOURCE)
        .read_text(encoding="utf-8"))
    data["claims"][0]["path"] = "mythic_agent/core/other.py"
    problems = validate_watch(data, require_example=True)
    assert any("exactly the five claims" in p for p in problems)
    # The same file is a well-formed watch without the check.
    assert validate_watch(data) == []
    data = yaml.safe_load(
        (ROOT / "mythic_agent" / "data" / WATCH_RESOURCE)
        .read_text(encoding="utf-8"))
    data["keeper"] = "scribe"
    problems = validate_watch(data, require_example=True)
    assert any("kept by the guardian" in p for p in problems)


def test_example_watch_yields_exactly_three_findings():
    watch = load_deadlock_watch()
    report = watch.report()
    assert [f.kind for f in report.findings] == [
        "delegation_cycle", "merge_conflict", "duplicated_work"]
    cycle, conflict, duplicated = report.findings
    assert cycle.members == (
        "architect", "forge_worker", "cartographer")
    assert cycle.slice_ids == ("M-127",)
    assert conflict.members == ("auditor", "forge_worker")
    assert conflict.paths == ("mythic_agent/core/engine.py",)
    assert conflict.slice_ids == ("M-129", "M-130")
    assert duplicated.members == ("scribe", "skald")
    assert duplicated.slice_ids == ("M-131",)
    assert duplicated.paths == (
        "mythic_agent/core/keeper.py",
        "mythic_agent/core/metrics.py")
    assert report.is_clean is False
    assert validate_report(watch, report) == []


# -- the detector --------------------------------------------------------------


def test_cycle_is_caught_canonically_and_deterministically():
    evidence = {"delegations": [
        {"delegator": "scribe", "delegatee": "auditor",
         "slice_id": "M-127"},
        {"delegator": "auditor", "delegatee": "guardian",
         "slice_id": "M-128"},
        {"delegator": "guardian", "delegatee": "scribe",
         "slice_id": "M-129"},
    ], "claims": []}
    findings = detect_findings(evidence)
    assert [f.kind for f in findings] == ["delegation_cycle"]
    # Named from its smallest member, in delegation order.
    assert findings[0].members == ("auditor", "guardian", "scribe")
    assert findings[0].slice_ids == ("M-127", "M-128", "M-129")
    assert "auditor -> guardian -> scribe -> auditor" in \
        findings[0].title
    # The same evidence always yields the same findings.
    assert detect_findings(evidence) == findings


def test_self_delegation_is_a_cycle_of_one():
    findings = detect_findings({"delegations": [
        {"delegator": "auditor", "delegatee": "auditor",
         "slice_id": "M-127"}], "claims": []})
    assert [f.kind for f in findings] == ["delegation_cycle"]
    assert findings[0].members == ("auditor",)


def test_two_disjoint_cycles_are_both_caught_in_order():
    findings = detect_findings({"delegations": [
        {"delegator": "scribe", "delegatee": "skald",
         "slice_id": "M-127"},
        {"delegator": "skald", "delegatee": "scribe",
         "slice_id": "M-127"},
        {"delegator": "auditor", "delegatee": "guardian",
         "slice_id": "M-128"},
        {"delegator": "guardian", "delegatee": "auditor",
         "slice_id": "M-128"},
    ], "claims": []})
    assert [f.members for f in findings] == [
        ("auditor", "guardian"), ("scribe", "skald")]


def test_clean_chain_and_single_holdings_are_not_flagged():
    assert detect_findings(_clean_evidence()) == ()
    report = WatchReport(findings=detect_findings(_clean_evidence()))
    assert report.is_clean is True
    assert validate_report(_clean_evidence(), report) == []


def test_merge_conflict_is_caught_and_needs_two_members():
    findings = detect_findings({"delegations": [], "claims": [
        {"member": "scribe", "slice_id": "M-127",
         "path": "mythic_agent/core/engine.py"},
        {"member": "auditor", "slice_id": "M-128",
         "path": "mythic_agent/core/engine.py"},
    ]})
    assert [f.kind for f in findings] == ["merge_conflict"]
    assert findings[0].members == ("auditor", "scribe")
    assert findings[0].slice_ids == ("M-127", "M-128")
    # One member holding its own path on two slices is
    # that member's own work, never a conflict.
    assert detect_findings({"delegations": [], "claims": [
        {"member": "scribe", "slice_id": "M-127",
         "path": "mythic_agent/core/engine.py"},
        {"member": "scribe", "slice_id": "M-128",
         "path": "mythic_agent/core/engine.py"},
    ]}) == ()


def test_duplicated_work_is_caught_and_needs_two_members():
    findings = detect_findings({"delegations": [], "claims": [
        {"member": "scribe", "slice_id": "M-131",
         "path": "mythic_agent/core/keeper.py"},
        {"member": "skald", "slice_id": "M-131",
         "path": "mythic_agent/core/metrics.py"},
    ]})
    assert [f.kind for f in findings] == ["duplicated_work"]
    assert findings[0].members == ("scribe", "skald")
    assert findings[0].paths == (
        "mythic_agent/core/keeper.py",
        "mythic_agent/core/metrics.py")
    # One member holding its own slice at two paths is
    # that member's own work, never duplication.
    assert detect_findings({"delegations": [], "claims": [
        {"member": "scribe", "slice_id": "M-131",
         "path": "mythic_agent/core/keeper.py"},
        {"member": "scribe", "slice_id": "M-131",
         "path": "mythic_agent/core/metrics.py"},
    ]}) == ()
    # The same slice and the same path held by two
    # members is both hazards, each named once.
    both = detect_findings({"delegations": [], "claims": [
        {"member": "scribe", "slice_id": "M-131",
         "path": "mythic_agent/core/keeper.py"},
        {"member": "skald", "slice_id": "M-131",
         "path": "mythic_agent/core/keeper.py"},
    ]})
    assert [f.kind for f in both] == [
        "merge_conflict", "duplicated_work"]


def test_validate_report_names_a_missing_or_extra_finding():
    data = _watch_data()
    evidence = {"delegations": data["delegations"],
                "claims": data["claims"]}
    report = WatchReport(findings=detect_findings(evidence))
    assert validate_report(evidence, report) == []
    missing = WatchReport(findings=())
    problems = validate_report(evidence, missing)
    assert any("exactly the evidence's findings" in p
               for p in problems)
    extra = WatchReport(findings=report.findings + detect_findings(
        {"delegations": [], "claims": [
            {"member": "scribe", "slice_id": "M-140",
             "path": "mythic_agent/core/engine.py"},
            {"member": "skald", "slice_id": "M-140",
             "path": "mythic_agent/core/engine.py"},
        ]}))
    assert validate_report(evidence, extra) != []
    assert validate_report(evidence, "not a report") != []


def test_finding_validation_and_refusals():
    finding = build_finding(
        kind="conflict", members=["scribe", "auditor"],
        slices=["m-128", "M-127"], paths=["a/b.py"],
        title="Merge conflict on a/b.py",
        detail="scribe and auditor hold a/b.py.")
    assert finding.kind == "merge_conflict"
    assert finding.slice_ids == ("M-127", "M-128")
    assert validate_finding(finding) is finding
    with pytest.raises(ValueError):
        build_finding(
            kind="stall", members=["scribe"], slice_ids=[],
            paths=[], title="T", detail="D")
    with pytest.raises(ValueError):
        build_finding(
            kind="cycle", members=["scribe", "scribe"],
            slice_ids=[], paths=[], title="T", detail="D")
    with pytest.raises(ValueError):
        validate_finding(
            {"kind": "cycle", "members": ["scribe"],
             "slice_ids": [], "paths": [], "title": "T",
             "detail": "D", "surprise": 1})
    with pytest.raises(ValueError):
        validate_finding("not a finding")


# -- the watch file ------------------------------------------------------------


def test_watch_construction_refusals():
    with pytest.raises(ValueError):
        DeadlockWatch(keeper="guardian")
    with pytest.raises(ValueError):
        DeadlockWatch(
            delegations=[_delegation()], keeper="bad keeper")
    watch = DeadlockWatch(
        delegations=[_delegation()], keeper="guardian")
    assert watch.claims == ()
    assert watch.report().is_clean is True


def test_watch_mapping_refusals():
    data = _watch_data()
    assert validate_watch(data) == []
    bad_schema = dict(data, schema="mythic.other/1")
    assert any("schema" in p for p in validate_watch(bad_schema))
    bad_slice = dict(data, slice="M-126")
    assert any("slice" in p for p in validate_watch(bad_slice))
    unknown = dict(data, surprise=1)
    assert any("unknown" in p for p in validate_watch(unknown))
    no_keeper = {k: v for k, v in data.items() if k != "keeper"}
    assert any("keeper" in p for p in validate_watch(no_keeper))
    empty = dict(data, delegations=[], claims=[])
    assert any("at least one" in p for p in validate_watch(empty))
    bad_entry = dict(data, delegations=[{"delegator": "scribe"}])
    assert any("delegation 1" in p for p in validate_watch(bad_entry))
    assert validate_watch("not a watch") != []
    with pytest.raises(ValidationError):
        load_deadlock_watch(bad_schema)


def test_watch_file_on_disk_roundtrip_and_refusals(tmp_path):
    path = _write_watch(tmp_path, _watch_data())
    watch = load_deadlock_watch_file(path)
    assert watch.keeper == "guardian"
    assert [f.kind for f in watch.report().findings] == [
        "delegation_cycle"]
    assert watch.report().findings[0].members == (
        "auditor", "scribe")
    bad = _write_watch(tmp_path, dict(_watch_data(), keeper=None))
    with pytest.raises(ValidationError):
        load_deadlock_watch_file(bad)
    with pytest.raises(FileNotFoundError):
        load_deadlock_watch_file(tmp_path / "missing.yaml")


# -- the registry ----------------------------------------------------------------


def test_registry_deterministic_ids_and_refusals():
    registry = DeadlockWatchRegistry()
    first = registry.register_delegation(_delegation())
    second = registry.register_delegation(
        _delegation(delegator="auditor", delegatee="guardian"))
    claim = registry.register_claim(_claim())
    assert first.delegation_id == "delegation-1"
    assert second.delegation_id == "delegation-2"
    assert claim.claim_id == "claim-1"
    supplied = registry.register_delegation(
        _delegation(delegation_id="delegation-4",
                    delegator="guardian", delegatee="scribe"))
    assert supplied.delegation_id == "delegation-4"
    # The sequence skips a number a supplied id took.
    assert registry.register_delegation(
        _delegation(delegator="scribe", delegatee="guardian")
    ).delegation_id == "delegation-3"
    assert registry.register_delegation(
        _delegation(delegator="guardian", delegatee="auditor")
    ).delegation_id == "delegation-5"
    with pytest.raises(ValueError):
        registry.register_delegation(
            _delegation(delegation_id="delegation-4"))
    assert registry.get_delegation("delegation-4") is supplied
    assert registry.get_claim("claim-1") is claim
    with pytest.raises(KeyError):
        registry.get_delegation("delegation-99")
    with pytest.raises(KeyError):
        registry.get_claim("claim-99")
    assert len(registry.list_delegations()) == 5
    assert len(registry.list_claims()) == 1


def test_registry_holds_a_watch_and_reports():
    registry = DeadlockWatchRegistry()
    delegations, claims = registry.register_watch(
        load_deadlock_watch())
    assert len(delegations) == 5 and len(claims) == 5
    assert delegations[0].delegation_id == "delegation-1"
    assert claims[0].claim_id == "claim-1"
    assert [f.kind for f in registry.findings()] == [
        "delegation_cycle", "merge_conflict", "duplicated_work"]
    assert [f.kind for f in registry.for_member("auditor")] == [
        "merge_conflict"]
    assert registry.for_member("polymath") == ()
    assert validate_report(registry, registry.report()) == []
    with pytest.raises(ValueError):
        registry.register_watch("not a watch")
    # Repetition alone never makes a hazard: the same
    # delegation registered twice is two records of
    # one edge, and the detector reads member sets.
    solo = DeadlockWatchRegistry()
    solo.register_claim(_claim())
    solo.register_claim(_claim())
    assert solo.findings() == ()


# -- records, plain words, formatters, parser -------------------------------------


def test_records_and_plain_words():
    watch = load_deadlock_watch()
    report = watch.report()
    record = report_record(report)
    assert record["type"] == "deadlock_report"
    assert record["slice"] == "M-127"
    assert record["count"] == 3
    assert record["clean"] is False
    assert record["cycles"] == 1
    assert record["merge_conflicts"] == 1
    assert record["duplicated_work"] == 1
    assert record["news"] is True
    assert "3 hazards caught for the coordinator" in \
        record["headline"]
    assert report_plain_words(
        WatchReport(findings=())) == \
        "The watch is clean: no hazard is caught."
    finding = report.findings[0]
    assert "Delegation cycle" in plain_words(finding)
    news = finding_record(finding)
    assert news["type"] == "deadlock_finding"
    assert news["kind"] == "delegation_cycle"
    assert news["members"] == [
        "architect", "forge_worker", "cartographer"]
    assert news["news"] is True
    assert report.by_kind("deadlock") == (finding,)
    assert report.for_member("cartographer") == (finding,)
    assert report.for_member("auditor") == (report.findings[1],)


def test_formatters():
    assert format_findings([]) == (
        "Deadlock watch: clean. No delegation cycle, "
        "merge conflict or duplicated work is caught.")
    text = format_findings()
    assert text.startswith("Deadlock watch: 3 hazards caught")
    assert "delegation_cycle" in text
    assert "merge_conflict" in text
    assert "duplicated_work" in text
    finding = load_deadlock_watch().report().findings[1]
    assert format_finding(finding).startswith(
        "  merge_conflict: Merge conflict on")
    kinds = format_kinds()
    assert kinds.startswith("Finding kinds:")
    assert "duplicated_work" in kinds
    screen = format_deadlock_screen()
    assert screen.startswith("Deadlock watch (M-127) - ")
    assert PLAIN_EXPLANATION in screen
    assert "Deadlock watch: 3 hazards caught" in screen
    assert USAGE in screen
    clean_screen = format_deadlock_screen(
        WatchReport(findings=()))
    assert "Deadlock watch: clean." in clean_screen


def test_parser():
    assert parse_deadlock_args("") == ("show", None)
    assert parse_deadlock_args(None) == ("show", None)
    assert parse_deadlock_args("show") == ("show", None)
    assert parse_deadlock_args("list") == ("show", None)
    assert parse_deadlock_args("findings") == ("show", None)
    assert parse_deadlock_args("show scribe") == ("show", "scribe")
    assert parse_deadlock_args("scribe") == ("show", "scribe")
    assert parse_deadlock_args("kinds") == ("kinds", None)
    for bad in ("show scribe auditor", "kinds please",
                "dance party", "show bad member", 3):
        with pytest.raises(ValueError):
            parse_deadlock_args(bad)


def test_module_purity():
    source = (
        ROOT / "mythic_agent" / "core" / "deadlock_watch.py"
    ).read_text(encoding="utf-8")
    assert "subprocess" not in source
    assert "Popen" not in source
    assert "os.system" not in source
    assert "agents.llm" not in source
    assert "import os" not in source
