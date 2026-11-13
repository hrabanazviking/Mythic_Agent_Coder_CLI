"""M-262 Accessibility final gate - pure-layer tests.

TIER: unit

The Part V doctrine + M-118 red-team pack + an
shipped-TUI re-run of the sandbox/jail code,
findings clean or roaded with owners: a finding
counts PASSED only on the gate's own independent
read resting on held local evidence, and a
roaded finding with no owner named stands open.
"""
import pytest

from mythic_agent.core.accessibility_final import (
    CHECKS,
    BARE_CLAIMS,
    DISPOSITIONS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    STAGES,
    CheckEntry,
    CheckRegistry,
    GateRecord,
    default_registry,
    derive_standing,
    derive_verdict,
    format_check,
    format_checks,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(check="A-03",
                task="tui-2026-11-a",
                date="2026-11-13", disposition="PASSED",
                owner="yrsa",
                proof_kind="shipped-tui-rerun",
                stages=STAGES,
                claims=("rerun_ref", "journal_ref"))
    base.update(kw)
    return GateRecord(**base)


def roaded_record(**kw):
    base = dict(check="A-05",
                task="tui-2026-11-a",
                date="2026-11-13", disposition="ROADED",
                owner="yrsa",
                proof_kind="shipped-tui-rerun",
                stages=STAGES,
                claims=("journal_ref",))
    base.update(kw)
    return GateRecord(**base)


def full_book(**overrides):
    records = []
    for check_id in default_registry().combinations():
        if check_id in ("A-01", "A-02", "A-03"):
            kw = dict(check=check_id, task="tui-2026-11-a",
                      date="2026-11-13", disposition="PASSED",
                      owner="yrsa",
                      proof_kind="shipped-tui-rerun",
                      stages=STAGES,
                      claims=("rerun_ref", "journal_ref"))
        else:
            kw = dict(check=check_id, task="tui-2026-11-a",
                      date="2026-11-13", disposition="ROADED",
                      owner="yrsa",
                      proof_kind="shipped-tui-rerun",
                      stages=STAGES,
                      claims=("journal_ref",))
        kw.update(overrides.get(check_id, {}))
        records.append(GateRecord(**kw))
    return records


def test_registry_holds_twelve_checks_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 12
    assert reg.ids()[0] == "A-01"
    assert reg.ids()[-1] == "A-12"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_checks_cover_the_doctrine_sources():
    reg = default_registry()
    pairs = {(e.doctrine, e.subject) for e in reg.entries()}
    assert len(pairs) == 12
    assert reg.get("A-01").doctrine == "M-199"
    assert reg.get("A-01").subject == "keyboard-task"
    assert reg.get("A-03").subject == "contrast-body"
    assert reg.get("A-05").subject == "reduced-motion"
    assert reg.get("A-11").doctrine == "M-016"
    assert reg.get("A-11").subject == "setup-traversal"
    assert reg.get("A-12").doctrine == "M-199"
    assert DISPOSITIONS == ("PASSED", "ROADED")


def test_registry_unknown_check_refused_by_name():
    with pytest.raises(ValidationError, match="unknown check: A-99"):
        default_registry().get("A-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate check"):
        CheckRegistry(CHECKS + CHECKS[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        CheckRegistry([CheckEntry("A-01", "M-199", "keyboard-task", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        CheckRegistry([CheckEntry("A-01", "M-199", "keyboard-task", "published", "why")])


def test_entry_unknown_doctrine_refused():
    with pytest.raises(ValidationError, match="unknown check doctrine"):
        CheckRegistry([CheckEntry("A-01", "M-999", "keyboard-task", "listed", "why")])


def test_record_passed_shipped_rerun_stands_held():
    standing = derive_standing(fresh_record())
    assert standing.held
    assert standing.grade == "held"
    assert standing.gaps == ()


def test_record_incomplete_walk_stands_open():
    standing = derive_standing(fresh_record(stages=STAGES[:3]))
    assert not standing.held
    assert any("not held" in g for g in standing.gaps)


def test_record_bad_stage_step_stands_open():
    bad = ("named", "judged", "dispositioned", "held")
    standing = derive_standing(fresh_record(stages=bad))
    assert not standing.held
    assert any("not in the walk" in g for g in standing.gaps)


def test_record_clean_on_historical_evidence_stands_open():
    standing = derive_standing(fresh_record(proof_kind="historical-only"))
    assert not standing.held
    assert any("no inheritance" in g for g in standing.gaps)


def test_record_clean_without_local_evidence_stands_open():
    standing = derive_standing(fresh_record(claims=("journal_ref",)))
    assert not standing.held
    assert any("no held rerun evidence" in g for g in standing.gaps)


def test_record_clean_on_bare_claims_stands_open():
    standing = derive_standing(fresh_record(claims=("feeling",)))
    assert not standing.held
    assert any("bare claims only" in g for g in standing.gaps)


def test_record_roaded_with_owner_stands_held():
    standing = derive_standing(roaded_record())
    assert standing.held
    assert standing.grade == "held"


def test_record_roaded_without_owner_stands_open():
    standing = derive_standing(roaded_record(owner=""))
    assert not standing.held
    assert any("not a road" in g for g in standing.gaps)


def test_record_roaded_silent_stands_open():
    standing = derive_standing(roaded_record(claims=()))
    assert not standing.held
    assert any("silent" in g for g in standing.gaps)


def test_record_without_date_stands_open():
    standing = derive_standing(fresh_record(date=""))
    assert not standing.held
    assert any("no gate date" in g for g in standing.gaps)


def test_record_unknown_disposition_refused():
    with pytest.raises(ValidationError, match="unknown record disposition"):
        derive_standing(fresh_record(disposition="MAYBE"))


def test_verdict_full_book_ready_with_roaded_checks():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.passed_checks == ("A-01", "A-02", "A-03")
    assert len(verdict.roaded_checks) == 9
    assert verdict.missing_checks == ()


def test_verdict_missing_check_stops_the_gate():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_checks == ("A-12",)
    assert any("A-12" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_gate():
    verdict = derive_verdict(full_book(**{"A-02": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("A-02 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_check_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two findings" in g for g in verdict.gaps)


def test_report_ready_and_shared_states():
    report = prepare_report("gate-a", "A-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("rerun_ref",))
    assert report.state == "ready"
    shared = prepare_report("gate-a", "A-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("rerun_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_and_short_certified_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("gate-a", "A-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("rerun_ref",), state="sealed")
    with pytest.raises(ValidationError, match="gate closed"):
        prepare_report("gate-a", "A-01", "findings", "2026-11-13",
                       3, 5, 12, claims=("rerun_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("gate-a", "A-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("feeling",))
    assert "A-01" in format_check(default_registry().get("A-01"))
    assert "A-12" in format_checks()
    assert "PASSED" in format_record(fresh_record())
    assert "ROADED" in format_records([roaded_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)

# ---------------------------------------------------------------------
