"""M-271 Retro and lessons - pure-layer tests.

TIER: unit

The campaign retrospective written into the self-improving
ledger, lesson by lesson, patterns worth keeping named as
skill candidates: a pattern counts KEPT only on held proof
measured in the campaign itself resting on held evidence
written in the ledger, a roaded lesson only where its road
rests on held evidence and its owner is named, and a dropped
lesson only with its owner and reason recorded - a dropped
lesson admitted in the open is honest.
"""
import pytest

from mythic_agent.core.retro_lessons import (
    RETRO_ENTRIES,
    BARE_CLAIMS,
    DISPOSITIONS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    STAGES,
    RetroEntry,
    RetroRegistry,
    RetroRecord,
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
    base = dict(lesson="L-03",
                work="retro-2026-11-a",
                date="2026-11-13", disposition="KEPT",
                owner="yrsa",
                proof_kind="kept-and-held",
                stages=STAGES,
                claims=("ledger_ref", "test_ref"))
    base.update(kw)
    return RetroRecord(**base)


def roaded_record(**kw):
    base = dict(lesson="L-05",
                work="retro-2026-11-a",
                date="2026-11-13", disposition="ROADED",
                owner="yrsa",
                proof_kind="roaded-open",
                stages=STAGES,
                claims=("test_ref",))
    base.update(kw)
    return RetroRecord(**base)


def dropped_record(**kw):
    base = dict(lesson="L-07",
                work="retro-2026-11-a",
                date="2026-11-13", disposition="DROPPED",
                owner="yrsa",
                proof_kind="none",
                stages=STAGES,
                claims=("test_ref",))
    base.update(kw)
    return RetroRecord(**base)


def full_book(**overrides):
    records = []
    for lesson_id in default_registry().combinations():
        if lesson_id in ("L-01", "L-02", "L-03"):
            kw = dict(lesson=lesson_id, work="retro-2026-11-a",
                      date="2026-11-13", disposition="KEPT",
                      owner="yrsa",
                      proof_kind="kept-and-held",
                      stages=STAGES,
                      claims=("ledger_ref", "test_ref"))
        elif lesson_id in ("L-04", "L-05", "L-06", "L-07"):
            kw = dict(lesson=lesson_id, work="retro-2026-11-a",
                      date="2026-11-13", disposition="ROADED",
                      owner="yrsa",
                      proof_kind="roaded-open",
                      stages=STAGES,
                      claims=("test_ref",))
        else:
            kw = dict(lesson=lesson_id, work="retro-2026-11-a",
                      date="2026-11-13", disposition="DROPPED",
                      owner="yrsa",
                      proof_kind="none",
                      stages=STAGES,
                      claims=("test_ref",))
        kw.update(overrides.get(lesson_id, {}))
        records.append(RetroRecord(**kw))
    return records


def test_registry_holds_twelve_lessons_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 12
    assert reg.ids()[0] == "L-01"
    assert reg.ids()[-1] == "L-12"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_lessons_cover_the_doctrine_sources():
    reg = default_registry()
    pairs = {(e.doctrine, e.subject) for e in reg.entries()}
    assert len(pairs) == 12
    assert reg.get("L-01").doctrine == "campaign-evidence"
    assert reg.get("L-01").subject == "banking-discipline"
    assert reg.get("L-02").subject == "stall-guard"
    assert reg.get("L-03").subject == "verify-from-disk"
    assert reg.get("L-04").subject == "closure-heals"
    assert reg.get("L-11").doctrine == "self-improving"
    assert reg.get("L-11").subject == "honest-boundary"
    assert reg.get("L-12").doctrine == "self-improving"
    assert DISPOSITIONS == ("KEPT", "ROADED", "DROPPED")


def test_registry_unknown_lesson_refused_by_name():
    with pytest.raises(ValidationError, match="unknown lesson: C-99"):
        default_registry().get("C-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate lesson"):
        RetroRegistry(RETRO_ENTRIES + RETRO_ENTRIES[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        RetroRegistry([RetroEntry("L-01", "campaign-evidence", "banking-discipline", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        RetroRegistry([RetroEntry("L-01", "campaign-evidence", "banking-discipline", "published", "why")])
    with pytest.raises(ValidationError, match="labelled"):
        RetroRegistry([RetroEntry("L-01", "campaign-evidence", "banking-discipline", "listed", "why", labelled=False)])
    with pytest.raises(ValidationError, match="evidenced"):
        RetroRegistry([RetroEntry("L-01", "campaign-evidence", "banking-discipline", "listed", "why", evidenced=False)])


def test_entry_unknown_doctrine_refused():
    with pytest.raises(ValidationError, match="unknown lesson doctrine"):
        RetroRegistry([RetroEntry("L-01", "M-999", "banking-discipline", "listed", "why")])


def test_record_kept_measured_and_held_stands_held():
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


def test_record_kept_on_roaded_proof_stands_open():
    standing = derive_standing(fresh_record(proof_kind="roaded-open"))
    assert not standing.held
    assert any("tells the truth" in g for g in standing.gaps)


def test_record_kept_without_ledger_ref_stands_open():
    standing = derive_standing(fresh_record(claims=("test_ref",)))
    assert not standing.held
    assert any("no held" in g for g in standing.gaps)


def test_record_kept_on_bare_claims_stands_open():
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


def test_record_dropped_silent_stands_open():
    standing = derive_standing(dropped_record(claims=()))
    assert not standing.held
    assert any("silent" in g for g in standing.gaps)


def test_record_without_date_stands_open():
    standing = derive_standing(fresh_record(date=""))
    assert not standing.held
    assert any("no report date" in g for g in standing.gaps)


def test_record_unknown_disposition_refused():
    with pytest.raises(ValidationError, match="unknown record disposition"):
        derive_standing(fresh_record(disposition="MAYBE"))


def test_verdict_full_book_kept_with_roaded_lessons():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.kept_lessons == ("L-01", "L-02", "L-03")
    assert len(verdict.roaded_lessons) == 4
    assert len(verdict.dropped_lessons) == 5
    assert verdict.missing_lessons == ()


def test_verdict_missing_lesson_stops_the_report():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_lessons == ("L-12",)
    assert any("L-12" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_report():
    verdict = derive_verdict(full_book(**{"L-02": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("L-02 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_lesson_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two records" in g for g in verdict.gaps)


def test_report_kept_and_shared_states():
    report = prepare_report("retro-a", "L-01", "lessons as dispositioned",
                            "2026-11-13", 3, 4, 5, 12,
                            claims=("ledger_ref",))
    assert report.state == "ready"
    shared = prepare_report("retro-a", "L-01", "lessons as dispositioned",
                            "2026-11-13", 3, 4, 5, 12,
                            claims=("ledger_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_and_short_certified_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("retro-a", "L-01", "lessons", "2026-11-13",
                       3, 4, 5, 12, claims=("ledger_ref",), state="sealed")
    with pytest.raises(ValidationError, match="retro complete"):
        prepare_report("retro-a", "L-01", "lessons", "2026-11-13",
                       3, 2, 2, 12, claims=("ledger_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("retro-a", "L-01", "lessons", "2026-11-13",
                       3, 4, 5, 12, claims=("feeling",))
    assert "L-01" in format_entry(default_registry().get("L-01"))
    assert "L-12" in format_entries()
    assert "KEPT" in format_record(fresh_record())
    assert "ROADED" in format_records([roaded_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)
    from pathlib import Path as _P
    _src = (_P(__file__).resolve().parent.parent
            / "mythic_agent" / "core" / "retro_lessons.py").read_text(
                encoding="utf-8")
    assert "open(" not in _src
    assert "socket" not in _src
    assert "subprocess" not in _src
    assert "urllib" not in _src


