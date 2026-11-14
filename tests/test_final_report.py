"""M-272 Final report to Volmarr - pure-layer tests.

TIER: unit

The final report, plain language first - what the coder can
now do, where it beats the field, where it does not yet -
with the evidence index: a section counts PROVEN only on
held proof measured in the campaign itself resting on held
evidence in the index, a partial section only where the
proven part rests on held evidence and its owner is named,
and a not proven section only with its owner and reason
recorded - a not proven section admitted in the open is
honest.
"""
import pytest

from mythic_agent.core.final_report import (
    FINAL_REPORT_ENTRIES,
    BARE_CLAIMS,
    DISPOSITIONS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    STAGES,
    FinalReportEntry,
    FinalReportRegistry,
    FinalReportRecord,
    default_registry,
    derive_standing,
    derive_verdict,
    format_entry,
    format_entries,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(section="F-03",
                work="report-2026-11-a",
                date="2026-11-13", disposition="PROVEN",
                owner="yrsa",
                proof_kind="proven-and-held",
                stages=STAGES,
                claims=("evidence_ref", "test_ref"))
    base.update(kw)
    return FinalReportRecord(**base)


def partial_record(**kw):
    base = dict(section="F-05",
                work="report-2026-11-a",
                date="2026-11-13", disposition="PARTIAL",
                owner="yrsa",
                proof_kind="partially-held",
                stages=STAGES,
                claims=("test_ref",))
    base.update(kw)
    return FinalReportRecord(**base)


def not_proven_record(**kw):
    base = dict(section="F-07",
                work="report-2026-11-a",
                date="2026-11-13", disposition="NOT_PROVEN",
                owner="yrsa",
                proof_kind="none",
                stages=STAGES,
                claims=("test_ref",))
    base.update(kw)
    return FinalReportRecord(**base)


def full_book(**overrides):
    records = []
    for section_id in default_registry().combinations():
        if section_id in ("F-01", "F-02", "F-03"):
            kw = dict(section=section_id, work="report-2026-11-a",
                      date="2026-11-13", disposition="PROVEN",
                      owner="yrsa",
                      proof_kind="proven-and-held",
                      stages=STAGES,
                      claims=("evidence_ref", "test_ref"))
        elif section_id in ("F-04", "F-05", "F-06", "F-07"):
            kw = dict(section=section_id, work="report-2026-11-a",
                      date="2026-11-13", disposition="PARTIAL",
                      owner="yrsa",
                      proof_kind="partially-held",
                      stages=STAGES,
                      claims=("test_ref",))
        else:
            kw = dict(section=section_id, work="report-2026-11-a",
                      date="2026-11-13", disposition="NOT_PROVEN",
                      owner="yrsa",
                      proof_kind="none",
                      stages=STAGES,
                      claims=("test_ref",))
        kw.update(overrides.get(section_id, {}))
        records.append(FinalReportRecord(**kw))
    return records


def test_registry_holds_twelve_sections_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 12
    assert reg.ids()[0] == "F-01"
    assert reg.ids()[-1] == "F-12"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_sections_cover_the_doctrine_sources():
    reg = default_registry()
    pairs = {(e.doctrine, e.subject) for e in reg.entries()}
    assert len(pairs) == 12
    assert reg.get("F-01").doctrine == "plain-language"
    assert reg.get("F-01").subject == "what-it-can-do"
    assert reg.get("F-02").subject == "provider-ocean"
    assert reg.get("F-03").subject == "code-intelligence"
    assert reg.get("F-04").subject == "editors-hand"
    assert reg.get("F-11").doctrine == "field-honesty"
    assert reg.get("F-11").subject == "where-it-falls-short"
    assert reg.get("F-12").doctrine == "report-duty"
    assert DISPOSITIONS == ("PROVEN", "PARTIAL", "NOT_PROVEN")


def test_registry_unknown_section_refused_by_name():
    with pytest.raises(ValidationError, match="unknown section: C-99"):
        default_registry().get("C-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate section"):
        FinalReportRegistry(FINAL_REPORT_ENTRIES + FINAL_REPORT_ENTRIES[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        FinalReportRegistry([FinalReportEntry("F-01", "plain-language", "what-it-can-do", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        FinalReportRegistry([FinalReportEntry("F-01", "plain-language", "what-it-can-do", "published", "why")])
    with pytest.raises(ValidationError, match="labelled"):
        FinalReportRegistry([FinalReportEntry("F-01", "plain-language", "what-it-can-do", "listed", "why", labelled=False)])
    with pytest.raises(ValidationError, match="evidenced"):
        FinalReportRegistry([FinalReportEntry("F-01", "plain-language", "what-it-can-do", "listed", "why", evidenced=False)])


def test_entry_unknown_doctrine_refused():
    with pytest.raises(ValidationError, match="unknown section doctrine"):
        FinalReportRegistry([FinalReportEntry("F-01", "M-999", "what-it-can-do", "listed", "why")])


def test_record_proven_measured_and_held_stands_held():
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


def test_record_proven_on_partial_proof_stands_open():
    standing = derive_standing(fresh_record(proof_kind="partially-held"))
    assert not standing.held
    assert any("tells the truth" in g for g in standing.gaps)


def test_record_proven_without_evidence_ref_stands_open():
    standing = derive_standing(fresh_record(claims=("test_ref",)))
    assert not standing.held
    assert any("no held" in g for g in standing.gaps)


def test_record_proven_on_bare_claims_stands_open():
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


def test_verdict_full_book_proven_with_partial_sections():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.proven_sections == ("F-01", "F-02", "F-03")
    assert len(verdict.partial_sections) == 4
    assert len(verdict.not_proven_sections) == 5
    assert verdict.missing_sections == ()


def test_verdict_missing_section_stops_the_report():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_sections == ("F-12",)
    assert any("F-12" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_report():
    verdict = derive_verdict(full_book(**{"F-02": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("F-02 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_section_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two records" in g for g in verdict.gaps)


def test_report_proven_and_shared_states():
    report = prepare_report("report-a", "F-01", "sections as dispositioned",
                            "2026-11-13", 3, 4, 5, 12,
                            claims=("evidence_ref",))
    assert report.state == "ready"
    shared = prepare_report("report-a", "F-01", "sections as dispositioned",
                            "2026-11-13", 3, 4, 5, 12,
                            claims=("evidence_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_and_short_certified_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("report-a", "F-01", "sections", "2026-11-13",
                       3, 4, 5, 12, claims=("evidence_ref",), state="sealed")
    with pytest.raises(ValidationError, match="report complete"):
        prepare_report("report-a", "F-01", "sections", "2026-11-13",
                       3, 2, 2, 12, claims=("evidence_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("report-a", "F-01", "sections", "2026-11-13",
                       3, 4, 5, 12, claims=("feeling",))
    assert "F-01" in format_entry(default_registry().get("F-01"))
    assert "F-12" in format_entries()
    assert "PROVEN" in format_record(fresh_record())
    assert "PARTIAL" in format_records([partial_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)
    from pathlib import Path as _P
    _src = (_P(__file__).resolve().parent.parent
            / "mythic_agent" / "core" / "final_report.py").read_text(
                encoding="utf-8")
    assert "open(" not in _src
    assert "socket" not in _src
    assert "subprocess" not in _src
    assert "urllib" not in _src


