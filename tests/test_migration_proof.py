"""M-265 Migration proof - pure-layer tests.

TIER: unit

A workspace from the current release opens in the new
one - sessions, journals, configs, memories intact: an
area counts PROVEN only on the old workspace actually
opening in the new release resting on held workspace
evidence, and a roaded area with no owner named stands
open.
"""
import pytest

from mythic_agent.core.migration_proof import (
    AREAS,
    BARE_CLAIMS,
    DISPOSITIONS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    STAGES,
    MigrationEntry,
    MigrationRegistry,
    MigrationRecord,
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
    base = dict(area="G-03",
                work="migration-2026-11-a",
                date="2026-11-13", disposition="PROVEN",
                owner="yrsa",
                proof_kind="opened-in-new-release",
                stages=STAGES,
                claims=("workspace_ref", "journal_ref"))
    base.update(kw)
    return MigrationRecord(**base)


def roaded_record(**kw):
    base = dict(area="G-05",
                work="migration-2026-11-a",
                date="2026-11-13", disposition="ROADED",
                owner="yrsa",
                proof_kind="opened-in-new-release",
                stages=STAGES,
                claims=("journal_ref",))
    base.update(kw)
    return MigrationRecord(**base)


def full_book(**overrides):
    records = []
    for area_id in default_registry().combinations():
        if area_id in ("G-01", "G-02", "G-03"):
            kw = dict(area=area_id, work="migration-2026-11-a",
                      date="2026-11-13", disposition="PROVEN",
                      owner="yrsa",
                      proof_kind="opened-in-new-release",
                      stages=STAGES,
                      claims=("workspace_ref", "journal_ref"))
        else:
            kw = dict(area=area_id, work="migration-2026-11-a",
                      date="2026-11-13", disposition="ROADED",
                      owner="yrsa",
                      proof_kind="opened-in-new-release",
                      stages=STAGES,
                      claims=("journal_ref",))
        kw.update(overrides.get(area_id, {}))
        records.append(MigrationRecord(**kw))
    return records


def test_registry_holds_twelve_areas_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 12
    assert reg.ids()[0] == "G-01"
    assert reg.ids()[-1] == "G-12"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_areas_cover_the_doctrine_sources():
    reg = default_registry()
    pairs = {(e.doctrine, e.subject) for e in reg.entries()}
    assert len(pairs) == 12
    assert reg.get("G-01").doctrine == "forward-compat"
    assert reg.get("G-01").subject == "session-store"
    assert reg.get("G-02").subject == "journal-store"
    assert reg.get("G-03").subject == "config-store"
    assert reg.get("G-04").subject == "memory-store"
    assert reg.get("G-11").doctrine == "standing-law"
    assert reg.get("G-11").subject == "key-vault-refs"
    assert reg.get("G-12").doctrine == "proof-duty"
    assert DISPOSITIONS == ("PROVEN", "ROADED")


def test_registry_unknown_area_refused_by_name():
    with pytest.raises(ValidationError, match="unknown area: G-99"):
        default_registry().get("G-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate area"):
        MigrationRegistry(AREAS + AREAS[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        MigrationRegistry([MigrationEntry("G-01", "forward-compat", "session-store", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        MigrationRegistry([MigrationEntry("G-01", "forward-compat", "session-store", "published", "why")])


def test_entry_unknown_doctrine_refused():
    with pytest.raises(ValidationError, match="unknown area doctrine"):
        MigrationRegistry([MigrationEntry("G-01", "M-999", "session-store", "listed", "why")])


def test_record_proven_in_new_release_stands_held():
    standing = derive_standing(fresh_record())
    assert standing.held
    assert standing.grade == "held"
    assert standing.gaps == ()


def test_record_incomplete_walk_stands_open():
    standing = derive_standing(fresh_record(stages=STAGES[:3]))
    assert not standing.held
    assert any("not held" in g for g in standing.gaps)


def test_record_bad_stage_step_stands_open():
    bad = ("named", "checked", "dispositioned", "held")
    standing = derive_standing(fresh_record(stages=bad))
    assert not standing.held
    assert any("not in the walk" in g for g in standing.gaps)


def test_record_proven_on_historical_evidence_stands_open():
    standing = derive_standing(fresh_record(proof_kind="historical-only"))
    assert not standing.held
    assert any("no inheritance" in g for g in standing.gaps)


def test_record_proven_without_workspace_evidence_stands_open():
    standing = derive_standing(fresh_record(claims=("journal_ref",)))
    assert not standing.held
    assert any("no held workspace evidence" in g for g in standing.gaps)


def test_record_proven_on_bare_claims_stands_open():
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
    assert any("no migration date" in g for g in standing.gaps)


def test_record_unknown_disposition_refused():
    with pytest.raises(ValidationError, match="unknown record disposition"):
        derive_standing(fresh_record(disposition="MAYBE"))


def test_verdict_full_book_ready_with_roaded_areas():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.proven_areas == ("G-01", "G-02", "G-03")
    assert len(verdict.roaded_areas) == 9
    assert verdict.missing_areas == ()


def test_verdict_missing_area_stops_the_migration():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_areas == ("G-12",)
    assert any("G-12" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_migration():
    verdict = derive_verdict(full_book(**{"G-02": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("G-02 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_area_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two findings" in g for g in verdict.gaps)


def test_report_ready_and_shared_states():
    report = prepare_report("migration-a", "G-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("workspace_ref",))
    assert report.state == "ready"
    shared = prepare_report("migration-a", "G-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("workspace_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_and_short_certified_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("migration-a", "G-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("workspace_ref",), state="sealed")
    with pytest.raises(ValidationError, match="migration complete"):
        prepare_report("migration-a", "G-01", "findings", "2026-11-13",
                       3, 5, 12, claims=("workspace_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("migration-a", "G-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("feeling",))
    assert "G-01" in format_area(default_registry().get("G-01"))
    assert "G-12" in format_areas()
    assert "PROVEN" in format_record(fresh_record())
    assert "ROADED" in format_records([roaded_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)
    from pathlib import Path as _P
    _src = (_P(__file__).resolve().parent.parent
            / "mythic_agent" / "core" / "migration_proof.py").read_text(
                encoding="utf-8")
    assert "open(" not in _src
    assert "socket" not in _src
    assert "subprocess" not in _src
    assert "urllib" not in _src
