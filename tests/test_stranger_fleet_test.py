"""M-266 Stranger fleet test - pure-layer tests.

TIER: unit

M-200's stranger + a headless CI run + a crew campaign,
all from docs alone, on a clean machine: an exercise
counts PROVEN only on a docs-only clean-machine run
resting on held evidence, and a roaded exercise with
no owner named stands open.
"""
import pytest

from mythic_agent.core.stranger_fleet_test import (
    EXERCISES,
    BARE_CLAIMS,
    DISPOSITIONS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    STAGES,
    StrangerFleetEntry,
    StrangerFleetRegistry,
    StrangerFleetRecord,
    default_registry,
    derive_standing,
    derive_verdict,
    format_exercise,
    format_exercises,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(exercise="F-02",
                work="fleet-2026-11-a",
                date="2026-11-13", disposition="PROVEN",
                owner="yrsa",
                proof_kind="docs-only-clean-machine",
                stages=STAGES,
                claims=("run_ref", "report_ref"))
    base.update(kw)
    return StrangerFleetRecord(**base)


def roaded_record(**kw):
    base = dict(exercise="F-03",
                work="fleet-2026-11-a",
                date="2026-11-13", disposition="ROADED",
                owner="yrsa",
                proof_kind="docs-only-clean-machine",
                stages=STAGES,
                claims=("report_ref",))
    base.update(kw)
    return StrangerFleetRecord(**base)


def full_book(**overrides):
    records = []
    for exercise_id in default_registry().combinations():
        if exercise_id in ("F-01",):
            kw = dict(exercise=exercise_id, work="fleet-2026-11-a",
                      date="2026-11-13", disposition="PROVEN",
                      owner="yrsa",
                      proof_kind="docs-only-clean-machine",
                      stages=STAGES,
                      claims=("run_ref", "report_ref"))
        else:
            kw = dict(exercise=exercise_id, work="fleet-2026-11-a",
                      date="2026-11-13", disposition="ROADED",
                      owner="yrsa",
                      proof_kind="docs-only-clean-machine",
                      stages=STAGES,
                      claims=("report_ref",))
        kw.update(overrides.get(exercise_id, {}))
        records.append(StrangerFleetRecord(**kw))
    return records


def test_registry_holds_three_exercises_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 3
    assert reg.ids()[0] == "F-01"
    assert reg.ids()[-1] == "F-03"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 3


def test_registry_exercises_cover_the_doctrine_sources():
    reg = default_registry()
    pairs = {(e.doctrine, e.subject) for e in reg.entries()}
    assert len(pairs) == 3
    assert reg.get("F-01").doctrine == "stranger-duty"
    assert reg.get("F-01").subject == "stranger-task"
    assert reg.get("F-02").subject == "headless-ci-run"
    assert reg.get("F-03").subject == "crew-campaign"
    assert reg.get("F-02").doctrine == "ci-duty"
    assert reg.get("F-03").doctrine == "crew-duty"
    assert all(e.docs_only and e.clean_machine for e in reg.entries())
    assert DISPOSITIONS == ("PROVEN", "ROADED")


def test_registry_unknown_exercise_refused_by_name():
    with pytest.raises(ValidationError, match="unknown exercise: F-99"):
        default_registry().get("F-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate exercise"):
        StrangerFleetRegistry(EXERCISES + EXERCISES[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        StrangerFleetRegistry([StrangerFleetEntry("F-01", "stranger-duty", "stranger-task", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        StrangerFleetRegistry([StrangerFleetEntry("F-01", "stranger-duty", "stranger-task", "published", "why")])
    with pytest.raises(ValidationError, match="docs-only"):
        StrangerFleetRegistry([StrangerFleetEntry("F-01", "stranger-duty", "stranger-task", "listed", "why", docs_only=False)])
    with pytest.raises(ValidationError, match="clean-machine"):
        StrangerFleetRegistry([StrangerFleetEntry("F-01", "stranger-duty", "stranger-task", "listed", "why", clean_machine=False)])


def test_entry_unknown_doctrine_refused():
    with pytest.raises(ValidationError, match="unknown exercise doctrine"):
        StrangerFleetRegistry([StrangerFleetEntry("F-01", "M-999", "session-store", "listed", "why")])


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


def test_record_proven_on_secondhand_evidence_stands_open():
    standing = derive_standing(fresh_record(proof_kind="secondhand-only"))
    assert not standing.held
    assert any("no secondhand proof" in g for g in standing.gaps)


def test_record_proven_without_run_evidence_stands_open():
    standing = derive_standing(fresh_record(claims=("report_ref",)))
    assert not standing.held
    assert any("no held run evidence" in g for g in standing.gaps)


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
    assert any("no fleet date" in g for g in standing.gaps)


def test_record_unknown_disposition_refused():
    with pytest.raises(ValidationError, match="unknown record disposition"):
        derive_standing(fresh_record(disposition="MAYBE"))


def test_verdict_full_book_ready_with_roaded_exercises():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.proven_exercises == ("F-01",)
    assert len(verdict.roaded_exercises) == 2
    assert verdict.missing_exercises == ()


def test_verdict_missing_exercise_stops_the_fleet():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_exercises == ("F-03",)
    assert any("F-03" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_fleet():
    verdict = derive_verdict(full_book(**{"F-01": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("F-01 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_exercise_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two findings" in g for g in verdict.gaps)


def test_report_ready_and_shared_states():
    report = prepare_report("fleet-a", "F-01", "findings as dispositioned",
                            "2026-11-13", 1, 2, 3,
                            claims=("run_ref",))
    assert report.state == "ready"
    shared = prepare_report("fleet-a", "F-01", "findings as dispositioned",
                            "2026-11-13", 1, 2, 3,
                            claims=("run_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_and_short_certified_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("fleet-a", "F-01", "findings", "2026-11-13",
                       1, 2, 3, claims=("run_ref",), state="sealed")
    with pytest.raises(ValidationError, match="fleet test complete"):
        prepare_report("fleet-a", "F-01", "findings", "2026-11-13",
                       1, 1, 3, claims=("run_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("fleet-a", "F-01", "findings", "2026-11-13",
                       1, 2, 3, claims=("feeling",))
    assert "F-01" in format_exercise(default_registry().get("F-01"))
    assert "F-03" in format_exercises()
    assert "PROVEN" in format_record(fresh_record())
    assert "ROADED" in format_records([roaded_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)
    from pathlib import Path as _P
    _src = (_P(__file__).resolve().parent.parent
            / "mythic_agent" / "core" / "stranger_fleet_test.py").read_text(
                encoding="utf-8")
    assert "open(" not in _src
    assert "socket" not in _src
    assert "subprocess" not in _src
    assert "urllib" not in _src
