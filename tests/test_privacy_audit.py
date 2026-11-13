"""M-261 Privacy audit - pure-layer tests.

TIER: unit

The Part V doctrine + M-118 red-team pack + an
network capture of the sandbox/jail code,
findings clean or roaded with owners: a finding
counts CLEAN only on the audit's own independent
read resting on held local evidence, and a
roaded finding with no owner named stands open.
"""
import pytest

from mythic_agent.core.privacy_audit import (
    SURFACES,
    BARE_CLAIMS,
    DISPOSITIONS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    STAGES,
    SurfaceEntry,
    SurfaceRegistry,
    CaptureRecord,
    default_registry,
    derive_standing,
    derive_verdict,
    format_surface,
    format_surfaces,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(surface="P-03",
                run="bench-2026-11-a",
                date="2026-11-13", disposition="CLEAN",
                owner="yrsa",
                proof_kind="network-capture",
                stages=STAGES,
                claims=("capture_ref", "journal_ref"))
    base.update(kw)
    return CaptureRecord(**base)


def roaded_record(**kw):
    base = dict(surface="P-05",
                run="bench-2026-11-a",
                date="2026-11-13", disposition="ROADED",
                owner="yrsa",
                proof_kind="network-capture",
                stages=STAGES,
                claims=("journal_ref",))
    base.update(kw)
    return CaptureRecord(**base)


def full_book(**overrides):
    records = []
    for surface_id in default_registry().combinations():
        if surface_id in ("P-01", "P-02", "P-03"):
            kw = dict(surface=surface_id, run="bench-2026-11-a",
                      date="2026-11-13", disposition="CLEAN",
                      owner="yrsa",
                      proof_kind="network-capture",
                      stages=STAGES,
                      claims=("capture_ref", "journal_ref"))
        else:
            kw = dict(surface=surface_id, run="bench-2026-11-a",
                      date="2026-11-13", disposition="ROADED",
                      owner="yrsa",
                      proof_kind="network-capture",
                      stages=STAGES,
                      claims=("journal_ref",))
        kw.update(overrides.get(surface_id, {}))
        records.append(CaptureRecord(**kw))
    return records


def test_registry_holds_twelve_surfaces_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 12
    assert reg.ids()[0] == "P-01"
    assert reg.ids()[-1] == "P-12"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_surfaces_cover_the_doctrine_sources():
    reg = default_registry()
    pairs = {(e.doctrine, e.subject) for e in reg.entries()}
    assert len(pairs) == 12
    assert reg.get("P-01").doctrine == "M-015"
    assert reg.get("P-01").subject == "telemetry"
    assert reg.get("P-03").subject == "benchmark-run"
    assert reg.get("P-05").subject == "dns-lookups"
    assert reg.get("P-11").doctrine == "M-098"
    assert reg.get("P-11").subject == "plugin-loads"
    assert reg.get("P-12").doctrine == "M-119"
    assert DISPOSITIONS == ("CLEAN", "ROADED")


def test_registry_unknown_surface_refused_by_name():
    with pytest.raises(ValidationError, match="unknown surface: P-99"):
        default_registry().get("P-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate surface"):
        SurfaceRegistry(SURFACES + SURFACES[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        SurfaceRegistry([SurfaceEntry("P-01", "M-015", "telemetry", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        SurfaceRegistry([SurfaceEntry("P-01", "M-015", "telemetry", "published", "why")])


def test_entry_unknown_doctrine_refused():
    with pytest.raises(ValidationError, match="unknown surface doctrine"):
        SurfaceRegistry([SurfaceEntry("P-01", "M-999", "permission-profiles", "listed", "why")])


def test_record_clean_network_capture_stands_held():
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
    assert any("no held capture evidence" in g for g in standing.gaps)


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
    assert any("no capture date" in g for g in standing.gaps)


def test_record_unknown_disposition_refused():
    with pytest.raises(ValidationError, match="unknown record disposition"):
        derive_standing(fresh_record(disposition="MAYBE"))


def test_verdict_full_book_ready_with_roaded_surfaces():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.clean_surfaces == ("P-01", "P-02", "P-03")
    assert len(verdict.roaded_surfaces) == 9
    assert verdict.missing_surfaces == ()


def test_verdict_missing_surface_stops_the_audit():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_surfaces == ("P-12",)
    assert any("P-12" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_audit():
    verdict = derive_verdict(full_book(**{"P-02": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("P-02 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_surface_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two findings" in g for g in verdict.gaps)


def test_report_ready_and_shared_states():
    report = prepare_report("audit-a", "P-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("capture_ref",))
    assert report.state == "ready"
    shared = prepare_report("audit-a", "P-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("capture_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_and_short_certified_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("audit-a", "P-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("capture_ref",), state="sealed")
    with pytest.raises(ValidationError, match="audit closed"):
        prepare_report("audit-a", "P-01", "findings", "2026-11-13",
                       3, 5, 12, claims=("capture_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("audit-a", "P-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("feeling",))
    assert "P-01" in format_surface(default_registry().get("P-01"))
    assert "P-12" in format_surfaces()
    assert "CLEAN" in format_record(fresh_record())
    assert "ROADED" in format_records([roaded_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)

# ---------------------------------------------------------------------
