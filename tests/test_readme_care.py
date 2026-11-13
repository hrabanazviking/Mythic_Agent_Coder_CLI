"""M-264 README care - pure-layer tests.

TIER: unit

The repo README extended by hand with the new story,
nothing removed: a section counts EXTENDED only on
hand extension against the README as it stands resting
on held README evidence, and a roaded section with no
owner named stands open.
"""
import pytest

from mythic_agent.core.readme_care import (
    SECTIONS,
    BARE_CLAIMS,
    DISPOSITIONS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    STAGES,
    CareEntry,
    CareRegistry,
    CareRecord,
    default_registry,
    derive_standing,
    derive_verdict,
    format_section,
    format_sections,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(section="R-03",
                work="readme-2026-11-a",
                date="2026-11-13", disposition="EXTENDED",
                owner="yrsa",
                proof_kind="extended-by-hand",
                stages=STAGES,
                claims=("readme_ref", "journal_ref"))
    base.update(kw)
    return CareRecord(**base)


def roaded_record(**kw):
    base = dict(section="R-05",
                work="readme-2026-11-a",
                date="2026-11-13", disposition="ROADED",
                owner="yrsa",
                proof_kind="extended-by-hand",
                stages=STAGES,
                claims=("journal_ref",))
    base.update(kw)
    return CareRecord(**base)


def full_book(**overrides):
    records = []
    for section_id in default_registry().combinations():
        if section_id in ("R-01", "R-02", "R-03"):
            kw = dict(section=section_id, work="readme-2026-11-a",
                      date="2026-11-13", disposition="EXTENDED",
                      owner="yrsa",
                      proof_kind="extended-by-hand",
                      stages=STAGES,
                      claims=("readme_ref", "journal_ref"))
        else:
            kw = dict(section=section_id, work="readme-2026-11-a",
                      date="2026-11-13", disposition="ROADED",
                      owner="yrsa",
                      proof_kind="extended-by-hand",
                      stages=STAGES,
                      claims=("journal_ref",))
        kw.update(overrides.get(section_id, {}))
        records.append(CareRecord(**kw))
    return records


def test_registry_holds_twelve_sections_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 12
    assert reg.ids()[0] == "R-01"
    assert reg.ids()[-1] == "R-12"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_sections_cover_the_doctrine_sources():
    reg = default_registry()
    pairs = {(e.doctrine, e.subject) for e in reg.entries()}
    assert len(pairs) == 12
    assert reg.get("R-01").doctrine == "new-story"
    assert reg.get("R-01").subject == "opening-story"
    assert reg.get("R-03").subject == "provider-ocean-story"
    assert reg.get("R-05").subject == "sandbox-story"
    assert reg.get("R-11").doctrine == "standing-law"
    assert reg.get("R-11").subject == "care-law-note"
    assert reg.get("R-12").doctrine == "care-duty"
    assert DISPOSITIONS == ("EXTENDED", "ROADED")


def test_registry_unknown_section_refused_by_name():
    with pytest.raises(ValidationError, match="unknown section: R-99"):
        default_registry().get("R-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate section"):
        CareRegistry(SECTIONS + SECTIONS[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        CareRegistry([CareEntry("R-01", "M-199", "keyboard-task", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        CareRegistry([CareEntry("R-01", "standing-law", "opening-story", "published", "why")])


def test_entry_unknown_doctrine_refused():
    with pytest.raises(ValidationError, match="unknown section doctrine"):
        CareRegistry([CareEntry("R-01", "M-999", "keyboard-task", "listed", "why")])


def test_record_extended_by_hand_stands_held():
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


def test_record_reconciled_on_historical_evidence_stands_open():
    standing = derive_standing(fresh_record(proof_kind="historical-only"))
    assert not standing.held
    assert any("no inheritance" in g for g in standing.gaps)


def test_record_reconciled_without_code_evidence_stands_open():
    standing = derive_standing(fresh_record(claims=("journal_ref",)))
    assert not standing.held
    assert any("no held README evidence" in g for g in standing.gaps)


def test_record_reconciled_on_bare_claims_stands_open():
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
    assert any("no care date" in g for g in standing.gaps)


def test_record_unknown_disposition_refused():
    with pytest.raises(ValidationError, match="unknown record disposition"):
        derive_standing(fresh_record(disposition="MAYBE"))


def test_verdict_full_book_ready_with_roaded_sections():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.extended_sections == ("R-01", "R-02", "R-03")
    assert len(verdict.roaded_sections) == 9
    assert verdict.missing_sections == ()


def test_verdict_missing_section_stops_the_readme():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_sections == ("R-12",)
    assert any("R-12" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_readme():
    verdict = derive_verdict(full_book(**{"R-02": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("R-02 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_section_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two findings" in g for g in verdict.gaps)


def test_report_ready_and_shared_states():
    report = prepare_report("readme-a", "R-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("readme_ref",))
    assert report.state == "ready"
    shared = prepare_report("readme-a", "R-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("readme_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_and_short_certified_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("readme-a", "R-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("readme_ref",), state="sealed")
    with pytest.raises(ValidationError, match="README complete"):
        prepare_report("readme-a", "R-01", "findings", "2026-11-13",
                       3, 5, 12, claims=("readme_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("readme-a", "R-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("feeling",))
    assert "R-01" in format_section(default_registry().get("R-01"))
    assert "R-12" in format_sections()
    assert "EXTENDED" in format_record(fresh_record())
    assert "ROADED" in format_records([roaded_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)
    from pathlib import Path as _P
    _src = (_P(__file__).resolve().parent.parent
            / "mythic_agent" / "core" / "readme_care.py").read_text(
                encoding="utf-8")
    assert "README.md" not in _src
    assert "open(" not in _src
    assert "socket" not in _src
    assert "subprocess" not in _src
    assert "urllib" not in _src

