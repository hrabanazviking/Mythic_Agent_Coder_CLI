"""M-263 The docs completion - pure-layer tests.

TIER: unit

User guide, method guide, bridge guides and per-part
interface notes reconciled with shipped code: a guide
counts RECONCILED only on reconciliation against the
shipped code itself resting on held code evidence, and
a roaded guide with no owner named stands open.
"""
import pytest

from mythic_agent.core.docs_completion import (
    GUIDES,
    BARE_CLAIMS,
    DISPOSITIONS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    STAGES,
    GuideEntry,
    GuideRegistry,
    DocRecord,
    default_registry,
    derive_standing,
    derive_verdict,
    format_guide,
    format_guides,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(guide="D-03",
                work="docs-2026-11-a",
                date="2026-11-13", disposition="RECONCILED",
                owner="yrsa",
                proof_kind="reconciled-with-code",
                stages=STAGES,
                claims=("code_ref", "journal_ref"))
    base.update(kw)
    return DocRecord(**base)


def roaded_record(**kw):
    base = dict(guide="D-05",
                work="docs-2026-11-a",
                date="2026-11-13", disposition="ROADED",
                owner="yrsa",
                proof_kind="reconciled-with-code",
                stages=STAGES,
                claims=("journal_ref",))
    base.update(kw)
    return DocRecord(**base)


def full_book(**overrides):
    records = []
    for guide_id in default_registry().combinations():
        if guide_id in ("D-01", "D-02", "D-03"):
            kw = dict(guide=guide_id, work="docs-2026-11-a",
                      date="2026-11-13", disposition="RECONCILED",
                      owner="yrsa",
                      proof_kind="reconciled-with-code",
                      stages=STAGES,
                      claims=("code_ref", "journal_ref"))
        else:
            kw = dict(guide=guide_id, work="docs-2026-11-a",
                      date="2026-11-13", disposition="ROADED",
                      owner="yrsa",
                      proof_kind="reconciled-with-code",
                      stages=STAGES,
                      claims=("journal_ref",))
        kw.update(overrides.get(guide_id, {}))
        records.append(DocRecord(**kw))
    return records


def test_registry_holds_twelve_guides_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 12
    assert reg.ids()[0] == "D-01"
    assert reg.ids()[-1] == "D-12"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_guides_cover_the_doctrine_sources():
    reg = default_registry()
    pairs = {(e.doctrine, e.subject) for e in reg.entries()}
    assert len(pairs) == 12
    assert reg.get("D-01").doctrine == "shipped-code"
    assert reg.get("D-01").subject == "user-guide"
    assert reg.get("D-03").subject == "bridge-guides"
    assert reg.get("D-05").subject == "install-and-setup"
    assert reg.get("D-11").doctrine == "method"
    assert reg.get("D-11").subject == "jarl-mode-guide"
    assert reg.get("D-12").doctrine == "shipped-code"
    assert DISPOSITIONS == ("RECONCILED", "ROADED")


def test_registry_unknown_guide_refused_by_name():
    with pytest.raises(ValidationError, match="unknown guide: D-99"):
        default_registry().get("D-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate guide"):
        GuideRegistry(GUIDES + GUIDES[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        GuideRegistry([GuideEntry("D-01", "M-199", "keyboard-task", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        GuideRegistry([GuideEntry("D-01", "shipped-code", "user-guide", "published", "why")])


def test_entry_unknown_doctrine_refused():
    with pytest.raises(ValidationError, match="unknown guide doctrine"):
        GuideRegistry([GuideEntry("D-01", "M-999", "keyboard-task", "listed", "why")])


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


def test_record_reconciled_on_historical_evidence_stands_open():
    standing = derive_standing(fresh_record(proof_kind="historical-only"))
    assert not standing.held
    assert any("no inheritance" in g for g in standing.gaps)


def test_record_reconciled_without_code_evidence_stands_open():
    standing = derive_standing(fresh_record(claims=("journal_ref",)))
    assert not standing.held
    assert any("no held code evidence" in g for g in standing.gaps)


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
    assert any("no docs date" in g for g in standing.gaps)


def test_record_unknown_disposition_refused():
    with pytest.raises(ValidationError, match="unknown record disposition"):
        derive_standing(fresh_record(disposition="MAYBE"))


def test_verdict_full_book_ready_with_roaded_guides():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.reconciled_guides == ("D-01", "D-02", "D-03")
    assert len(verdict.roaded_guides) == 9
    assert verdict.missing_guides == ()


def test_verdict_missing_guide_stops_the_docs():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_guides == ("D-12",)
    assert any("D-12" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_docs():
    verdict = derive_verdict(full_book(**{"D-02": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("D-02 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_guide_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two findings" in g for g in verdict.gaps)


def test_report_ready_and_shared_states():
    report = prepare_report("docs-a", "D-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("code_ref",))
    assert report.state == "ready"
    shared = prepare_report("docs-a", "D-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("code_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_and_short_certified_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("docs-a", "D-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("code_ref",), state="sealed")
    with pytest.raises(ValidationError, match="docs complete"):
        prepare_report("docs-a", "D-01", "findings", "2026-11-13",
                       3, 5, 12, claims=("code_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("docs-a", "D-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("feeling",))
    assert "D-01" in format_guide(default_registry().get("D-01"))
    assert "D-12" in format_guides()
    assert "RECONCILED" in format_record(fresh_record())
    assert "ROADED" in format_records([roaded_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)

# ---------------------------------------------------------------------
