"""M-270 The roadmap audit - pure-layer tests.

TIER: unit

DONE with evidence, PARTIAL with its road, or NOT PROVEN
with its reason per roadmap part, in the closing twin: a
part counts DONE only on held proof measured in the
campaign itself resting on held evidence, a partial part
only where the done part rests on held evidence and the
rest is roaded in the open, and a not proven part only
with its owner and reason recorded - a not proven part
admitted in the open is honest.
"""
import pytest

from mythic_agent.core.roadmap_audit import (
    AUDIT_PARTS,
    BARE_CLAIMS,
    DISPOSITIONS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    STAGES,
    RoadmapAuditEntry,
    RoadmapAuditRegistry,
    RoadmapAuditRecord,
    default_registry,
    derive_standing,
    derive_verdict,
    format_part,
    format_parts,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(part="A-03",
                work="audit-2026-11-a",
                date="2026-11-13", disposition="DONE",
                owner="yrsa",
                proof_kind="done-and-held",
                stages=STAGES,
                claims=("evidence_ref", "test_ref"))
    base.update(kw)
    return RoadmapAuditRecord(**base)


def partial_record(**kw):
    base = dict(part="A-05",
                work="audit-2026-11-a",
                date="2026-11-13", disposition="PARTIAL",
                owner="yrsa",
                proof_kind="partially-held",
                stages=STAGES,
                claims=("test_ref",))
    base.update(kw)
    return RoadmapAuditRecord(**base)


def not_proven_record(**kw):
    base = dict(part="A-07",
                work="audit-2026-11-a",
                date="2026-11-13", disposition="NOT_PROVEN",
                owner="yrsa",
                proof_kind="none",
                stages=STAGES,
                claims=("test_ref",))
    base.update(kw)
    return RoadmapAuditRecord(**base)


def full_book(**overrides):
    records = []
    for part_id in default_registry().combinations():
        if part_id in ("A-01", "A-02", "A-03"):
            kw = dict(part=part_id, work="audit-2026-11-a",
                      date="2026-11-13", disposition="DONE",
                      owner="yrsa",
                      proof_kind="done-and-held",
                      stages=STAGES,
                      claims=("evidence_ref", "test_ref"))
        elif part_id in ("A-04", "A-05", "A-06", "A-07"):
            kw = dict(part=part_id, work="audit-2026-11-a",
                      date="2026-11-13", disposition="PARTIAL",
                      owner="yrsa",
                      proof_kind="partially-held",
                      stages=STAGES,
                      claims=("test_ref",))
        else:
            kw = dict(part=part_id, work="audit-2026-11-a",
                      date="2026-11-13", disposition="NOT_PROVEN",
                      owner="yrsa",
                      proof_kind="none",
                      stages=STAGES,
                      claims=("test_ref",))
        kw.update(overrides.get(part_id, {}))
        records.append(RoadmapAuditRecord(**kw))
    return records


def test_registry_holds_twelve_parts_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 12
    assert reg.ids()[0] == "A-01"
    assert reg.ids()[-1] == "A-12"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_parts_cover_the_doctrine_sources():
    reg = default_registry()
    pairs = {(e.doctrine, e.subject) for e in reg.entries()}
    assert len(pairs) == 12
    assert reg.get("A-01").doctrine == "audit-truth"
    assert reg.get("A-01").subject == "part-01"
    assert reg.get("A-02").subject == "part-02"
    assert reg.get("A-03").subject == "part-03"
    assert reg.get("A-04").subject == "part-04"
    assert reg.get("A-11").doctrine == "road-honesty"
    assert reg.get("A-11").subject == "part-11"
    assert reg.get("A-12").doctrine == "audit-duty"
    assert DISPOSITIONS == ("DONE", "PARTIAL", "NOT_PROVEN")


def test_registry_unknown_part_refused_by_name():
    with pytest.raises(ValidationError, match="unknown part: C-99"):
        default_registry().get("C-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate part"):
        RoadmapAuditRegistry(AUDIT_PARTS + AUDIT_PARTS[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        RoadmapAuditRegistry([RoadmapAuditEntry("A-01", "audit-truth", "part-01", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        RoadmapAuditRegistry([RoadmapAuditEntry("A-01", "audit-truth", "part-01", "published", "why")])
    with pytest.raises(ValidationError, match="labelled"):
        RoadmapAuditRegistry([RoadmapAuditEntry("A-01", "audit-truth", "part-01", "listed", "why", labelled=False)])
    with pytest.raises(ValidationError, match="evidenced"):
        RoadmapAuditRegistry([RoadmapAuditEntry("A-01", "audit-truth", "part-01", "listed", "why", evidenced=False)])


def test_entry_unknown_doctrine_refused():
    with pytest.raises(ValidationError, match="unknown part doctrine"):
        RoadmapAuditRegistry([RoadmapAuditEntry("A-01", "M-999", "part-01", "listed", "why")])


def test_record_done_measured_and_held_stands_held():
    standing = derive_standing(fresh_record())
    assert standing.held
    assert standing.grade == "held"
    assert standing.gaps == ()


def test_record_incomplete_walk_stands_open():
    standing = derive_standing(fresh_record(stages=STAGES[:3]))
    assert not standing.held
    assert any("not held" in g for g in standing.gaps)


def test_record_bad_stage_step_stands_open():
    bad = ("named", "evidenced", "dispositioned", "held")
    standing = derive_standing(fresh_record(stages=bad))
    assert not standing.held
    assert any("not in the walk" in g for g in standing.gaps)


def test_record_done_on_partial_proof_stands_open():
    standing = derive_standing(fresh_record(proof_kind="partially-held"))
    assert not standing.held
    assert any("tells the truth" in g for g in standing.gaps)


def test_record_done_without_evidence_ref_stands_open():
    standing = derive_standing(fresh_record(claims=("test_ref",)))
    assert not standing.held
    assert any("no held" in g for g in standing.gaps)


def test_record_done_on_bare_claims_stands_open():
    standing = derive_standing(fresh_record(claims=("feeling",)))
    assert not standing.held
    assert any("bare claims only" in g for g in standing.gaps)


def test_record_partial_with_owner_stands_held():
    standing = derive_standing(partial_record())
    assert standing.held
    assert standing.grade == "held"


def test_record_partial_without_owner_stands_open():
    standing = derive_standing(partial_record(owner=""))
    assert not standing.held
    assert any("not a road" in g for g in standing.gaps)


def test_record_not_proven_silent_stands_open():
    standing = derive_standing(not_proven_record(claims=()))
    assert not standing.held
    assert any("silent" in g for g in standing.gaps)


def test_record_without_date_stands_open():
    standing = derive_standing(fresh_record(date=""))
    assert not standing.held
    assert any("no report date" in g for g in standing.gaps)


def test_record_unknown_disposition_refused():
    with pytest.raises(ValidationError, match="unknown record disposition"):
        derive_standing(fresh_record(disposition="MAYBE"))


def test_verdict_full_book_done_with_partial_parts():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.done_parts == ("A-01", "A-02", "A-03")
    assert len(verdict.partial_parts) == 4
    assert len(verdict.not_proven_parts) == 5
    assert verdict.missing_parts == ()


def test_verdict_missing_part_stops_the_report():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_parts == ("A-12",)
    assert any("A-12" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_report():
    verdict = derive_verdict(full_book(**{"A-02": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("A-02 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_part_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two findings" in g for g in verdict.gaps)


def test_report_done_and_shared_states():
    report = prepare_report("audit-a", "A-01", "findings as dispositioned",
                            "2026-11-13", 3, 4, 5, 12,
                            claims=("evidence_ref",))
    assert report.state == "ready"
    shared = prepare_report("audit-a", "A-01", "findings as dispositioned",
                            "2026-11-13", 3, 4, 5, 12,
                            claims=("evidence_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_and_short_certified_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("audit-a", "A-01", "findings", "2026-11-13",
                       3, 4, 5, 12, claims=("evidence_ref",), state="sealed")
    with pytest.raises(ValidationError, match="part complete"):
        prepare_report("audit-a", "A-01", "findings", "2026-11-13",
                       3, 2, 2, 12, claims=("evidence_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("audit-a", "A-01", "findings", "2026-11-13",
                       3, 4, 5, 12, claims=("feeling",))
    assert "A-01" in format_part(default_registry().get("A-01"))
    assert "A-12" in format_parts()
    assert "DONE" in format_record(fresh_record())
    assert "PARTIAL" in format_records([partial_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)
    from pathlib import Path as _P
    _src = (_P(__file__).resolve().parent.parent
            / "mythic_agent" / "core" / "roadmap_audit.py").read_text(
                encoding="utf-8")
    assert "open(" not in _src
    assert "socket" not in _src
    assert "subprocess" not in _src
    assert "urllib" not in _src


