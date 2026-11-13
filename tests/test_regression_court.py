"""M-257 Regression court - pure-layer tests.

TIER: unit

Every part's gate results re-run as one battery; a
red anywhere stops the release, not just the part:
a part whose re-run rests on no held gate evidence,
whose counts fall short, or whose outcome stands
red holds the whole road open.
"""
import pytest

from mythic_agent.core.regression_court import (
    BARE_CLAIMS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    OUTCOMES,
    PARTS,
    STAGES,
    CourtRecord,
    PartEntry,
    PartRegistry,
    default_registry,
    derive_standing,
    derive_verdict,
    format_part,
    format_parts,
    format_record,
    format_records,
    prepare_verdict,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(part="part_01", run="court-2026-11-a",
                date="2026-11-12", outcome="green",
                passed=40, total=40,
                stages=STAGES,
                claims=("gate_log_ref", "rerun_log_ref"))
    base.update(kw)
    return CourtRecord(**base)


def full_battery(**overrides):
    records = []
    for entry in default_registry().entries():
        kw = dict(part=entry.id, run="court-2026-11-a",
                  date="2026-11-12", outcome="green",
                  passed=40, total=40, stages=STAGES,
                  claims=("gate_log_ref", "rerun_log_ref"))
        kw.update(overrides.get(entry.id, {}))
        records.append(CourtRecord(**kw))
    return records


def test_registry_holds_eleven_parts_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 11
    assert reg.ids()[0] == "part_01"
    assert reg.ids()[-1] == "part_11"
    assert all(e.standing == "listed" for e in reg.entries())


def test_registry_part_ranges_cover_the_road():
    reg = default_registry()
    assert reg.get("part_01").first_slice == "M-001"
    assert reg.get("part_11").last_slice == "M-272"
    assert reg.get("part_11").label == "The Proof Spine"


def test_registry_unknown_part_refused_by_name():
    with pytest.raises(ValidationError, match="unknown part: part_99"):
        default_registry().get("part_99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate part"):
        PartRegistry(PARTS + PARTS[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing label"):
        PartRegistry([PartEntry(
            "part_01", 1, "I", "", "M-001", "M-018", "listed", "why")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        PartRegistry([PartEntry(
            "part_01", 1, "I", "X", "M-001", "M-018", "published", "why")])


def test_record_complete_green_stands_held():
    standing = derive_standing(fresh_record())
    assert standing.held
    assert standing.grade == "held"
    assert standing.gaps == ()


def test_record_incomplete_walk_stands_open():
    standing = derive_standing(fresh_record(stages=STAGES[:3]))
    assert not standing.held
    assert any("not held" in g for g in standing.gaps)


def test_record_bad_stage_step_stands_open():
    bad = ("named", "rerun", "judged", "held")
    standing = derive_standing(fresh_record(stages=bad))
    assert not standing.held
    assert any("not in the walk" in g for g in standing.gaps)


def test_record_red_outcome_stops_the_release():
    standing = derive_standing(fresh_record(outcome="red"))
    assert not standing.held
    assert any("stops the release" in g for g in standing.gaps)


def test_record_short_counts_stand_open():
    standing = derive_standing(fresh_record(passed=39))
    assert not standing.held
    assert any("fall short" in g for g in standing.gaps)


def test_record_without_gate_evidence_stands_open():
    standing = derive_standing(fresh_record(claims=("rerun_log_ref",)))
    assert not standing.held
    assert any("no held gate evidence" in g for g in standing.gaps)


def test_record_bare_claims_only_stand_open():
    standing = derive_standing(fresh_record(claims=("feeling",)))
    assert not standing.held
    assert any("bare claims only" in g for g in standing.gaps)


def test_record_unknown_evidence_kind_refused():
    with pytest.raises(ValidationError, match="unknown record evidence kind"):
        derive_standing(fresh_record(claims=("rumour",)))


def test_record_bad_date_refused():
    with pytest.raises(ValidationError, match="unknown re-run date"):
        derive_standing(fresh_record(date="12/11/2026"))


def test_record_inflated_counts_refused():
    with pytest.raises(ValidationError, match="never inflated"):
        derive_standing(fresh_record(passed=41))


def test_record_unknown_outcome_refused():
    with pytest.raises(ValidationError, match="unknown re-run outcome"):
        derive_standing(fresh_record(outcome="amber"))


def test_verdict_ready_when_every_part_held():
    verdict = derive_verdict(full_battery())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.red_parts == ()
    assert verdict.missing_parts == ()


def test_verdict_one_red_stops_the_whole_release():
    verdict = derive_verdict(full_battery(
        part_05=dict(outcome="red", passed=38)))
    assert not verdict.ready
    assert verdict.red_parts == ("part_05",)


def test_verdict_missing_part_stops_the_release():
    verdict = derive_verdict(full_battery()[:10])
    assert not verdict.ready
    assert verdict.missing_parts == ("part_11",)


def test_verdict_open_record_stops_the_release():
    verdict = derive_verdict(full_battery(
        part_03=dict(claims=("summary",))))
    assert not verdict.ready
    assert any("part_03 stands open" in g for g in verdict.gaps)


def test_prepare_verdict_all_green_may_claim_release():
    draft = prepare_verdict(
        "court-2026-11", "release-1", "every part green",
        "2026-11-12", 11, 11, claims=("gate_log_ref",),
        released=True)
    assert draft.state == "ready"
    assert draft.released


def test_prepare_verdict_release_claim_short_of_green_refused():
    with pytest.raises(ValidationError, match="stops the release"):
        prepare_verdict(
            "court-2026-11", "release-1", "mostly green",
            "2026-11-12", 10, 11, claims=("gate_log_ref",),
            released=True)


def test_prepare_verdict_sealed_state_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_verdict(
            "court-2026-11", "release-1", "every part green",
            "2026-11-12", 11, 11, claims=("gate_log_ref",),
            state="sealed")


def test_format_roads_name_the_part_and_outcome():
    line = format_record(fresh_record())
    assert "part_01" in line
    assert "green" in line
    assert "held as re-run" in line
    part_line = format_part(default_registry().get("part_11"))
    assert "The Proof Spine" in part_line
    assert "M-255-M-272" in part_line
    assert len(format_parts().splitlines()) == 11
    assert len(format_records(full_battery()).splitlines()) == 11
    assert HELD_EVIDENCE[0] == "gate_log_ref"
    assert BARE_CLAIMS[-1] == "summary"
    assert "gate_log_ref" in EVIDENCE_KINDS
    assert OUTCOMES == ("green", "red")
