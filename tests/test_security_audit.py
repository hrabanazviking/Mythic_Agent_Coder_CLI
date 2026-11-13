"""M-260 Security audit - pure-layer tests.

TIER: unit

The Part V doctrine + M-118 red-team pack + an
independent read of the sandbox/jail code,
findings fixed or roaded with owners: a finding
counts FIXED only on the audit's own independent
read resting on held local evidence, and a
roaded finding with no owner named stands open.
"""
import pytest

from mythic_agent.core.security_audit import (
    AREAS,
    BARE_CLAIMS,
    DISPOSITIONS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    STAGES,
    AreaEntry,
    AreaRegistry,
    FindingRecord,
    default_registry,
    derive_standing,
    derive_verdict,
    format_area,
    format_areas,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(area="S-03",
                run="audit-2026-11-a",
                date="2026-11-13", disposition="FIXED",
                owner="yrsa",
                proof_kind="independent-read",
                stages=STAGES,
                claims=("local_run_ref", "report_ref"))
    base.update(kw)
    return FindingRecord(**base)


def roaded_record(**kw):
    base = dict(area="S-05",
                run="audit-2026-11-a",
                date="2026-11-13", disposition="ROADED",
                owner="yrsa",
                proof_kind="independent-read",
                stages=STAGES,
                claims=("report_ref",))
    base.update(kw)
    return FindingRecord(**base)


def full_book(**overrides):
    records = []
    for area_id in default_registry().combinations():
        if area_id in ("S-01", "S-02", "S-03"):
            kw = dict(area=area_id, run="audit-2026-11-a",
                      date="2026-11-13", disposition="FIXED",
                      owner="yrsa",
                      proof_kind="independent-read",
                      stages=STAGES,
                      claims=("local_run_ref", "report_ref"))
        else:
            kw = dict(area=area_id, run="audit-2026-11-a",
                      date="2026-11-13", disposition="ROADED",
                      owner="yrsa",
                      proof_kind="independent-read",
                      stages=STAGES,
                      claims=("report_ref",))
        kw.update(overrides.get(area_id, {}))
        records.append(FindingRecord(**kw))
    return records


def test_registry_holds_twelve_areas_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 12
    assert reg.ids()[0] == "S-01"
    assert reg.ids()[-1] == "S-12"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_areas_cover_the_doctrine_sources():
    reg = default_registry()
    pairs = {(e.doctrine, e.subject) for e in reg.entries()}
    assert len(pairs) == 12
    assert reg.get("S-01").doctrine == "M-095"
    assert reg.get("S-01").subject == "permission-profiles"
    assert reg.get("S-03").subject == "os-sandbox"
    assert reg.get("S-05").subject == "path-jail"
    assert reg.get("S-11").doctrine == "M-118"
    assert reg.get("S-11").subject == "red-team-pack"
    assert reg.get("S-12").doctrine == "M-119"
    assert DISPOSITIONS == ("FIXED", "ROADED")


def test_registry_unknown_area_refused_by_name():
    with pytest.raises(ValidationError, match="unknown area: S-99"):
        default_registry().get("S-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate area"):
        AreaRegistry(AREAS + AREAS[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        AreaRegistry([AreaEntry("S-01", "M-095", "permission-profiles", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        AreaRegistry([AreaEntry("S-01", "M-095", "permission-profiles", "published", "why")])


def test_entry_unknown_doctrine_refused():
    with pytest.raises(ValidationError, match="unknown area doctrine"):
        AreaRegistry([AreaEntry("S-01", "M-999", "permission-profiles", "listed", "why")])


def test_record_fixed_independent_read_stands_held():
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


def test_record_fixed_on_historical_evidence_stands_open():
    standing = derive_standing(fresh_record(proof_kind="historical-only"))
    assert not standing.held
    assert any("no inheritance" in g for g in standing.gaps)


def test_record_fixed_without_local_evidence_stands_open():
    standing = derive_standing(fresh_record(claims=("report_ref",)))
    assert not standing.held
    assert any("no held local evidence" in g for g in standing.gaps)


def test_record_fixed_on_bare_claims_stands_open():
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
    assert any("no audit date" in g for g in standing.gaps)


def test_record_unknown_disposition_refused():
    with pytest.raises(ValidationError, match="unknown record disposition"):
        derive_standing(fresh_record(disposition="MAYBE"))


def test_verdict_full_book_ready_with_roaded_areas():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.fixed_areas == ("S-01", "S-02", "S-03")
    assert len(verdict.roaded_areas) == 9
    assert verdict.missing_areas == ()


def test_verdict_missing_area_stops_the_audit():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_areas == ("S-12",)
    assert any("S-12" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_audit():
    verdict = derive_verdict(full_book(**{"S-02": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("S-02 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_area_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two findings" in g for g in verdict.gaps)


def test_report_ready_and_shared_states():
    report = prepare_report("audit-a", "S-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("local_run_ref",))
    assert report.state == "ready"
    shared = prepare_report("audit-a", "S-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("local_run_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_and_short_certified_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("audit-a", "S-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("local_run_ref",), state="sealed")
    with pytest.raises(ValidationError, match="audit closed"):
        prepare_report("audit-a", "S-01", "findings", "2026-11-13",
                       3, 5, 12, claims=("local_run_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("audit-a", "S-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("feeling",))
    assert "S-01" in format_area(default_registry().get("S-01"))
    assert "S-12" in format_areas()
    assert "FIXED" in format_record(fresh_record())
    assert "ROADED" in format_records([roaded_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)
