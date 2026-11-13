"""M-256 Published-yardstick runs - pure-layer tests.

TIER: unit

SWE-bench-style public sets run where licences allow,
results reported with model, cost, and date -
comparable to the field's claims, never inflated: a
set whose licence is not held is listed-only and can
hold no run, and a report missing its model, cost or
date stands open.
"""
import pytest

from mythic_agent.core.published_yardstick import (
    BARE_CLAIMS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    LICENCE_STANDINGS,
    REPORT_STATES,
    STAGES,
    YARDSTICKS,
    RunDraft,
    RunRecord,
    YardstickEntry,
    YardstickRegistry,
    default_registry,
    derive_standing,
    format_record,
    format_records,
    format_yardstick,
    format_yardsticks,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(yardstick="swe_bench", run="2026-11-a",
                model="mythic-coder-7b", cost=12.5,
                date="2026-11-12", score=42.5,
                stages=STAGES,
                claims=("licence_ref", "run_log_ref"))
    base.update(kw)
    return RunRecord(**base)


def test_registry_holds_four_yardsticks_listed_only():
    reg = default_registry()
    assert reg.ids() == ("swe_bench", "swe_bench_lite",
                         "swe_bench_verified",
                         "swe_bench_multimodal")
    assert all(e.standing == "listed" for e in reg.entries())


def test_registry_unknown_yardstick_refused_by_name():
    with pytest.raises(ValidationError, match="unknown yardstick: guess"):
        default_registry().get("guess")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate yardstick"):
        YardstickRegistry(YARDSTICKS + YARDSTICKS[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing label"):
        YardstickRegistry([YardstickEntry(
            "x", "", "run", "MIT", "held", 100, "listed", "why")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        YardstickRegistry([YardstickEntry(
            "x", "X", "run", "MIT", "held", 100, "published", "why")])


def test_licence_standings_held_and_listed_only():
    reg = default_registry()
    assert reg.get("swe_bench").licence == "MIT"
    assert reg.get("swe_bench").licence_standing == "held"
    assert reg.get("swe_bench_lite").licence_standing == "held"
    assert reg.get("swe_bench_verified").licence_standing == "held"
    multi = reg.get("swe_bench_multimodal")
    assert multi.licence_standing == "listed_only"
    assert LICENCE_STANDINGS == ("held", "listed_only")
    assert all(e.max_score == 100 for e in reg.entries())


def test_fresh_record_stands_held():
    standing = derive_standing(fresh_record())
    assert standing.held is True
    assert standing.grade == "held"
    assert standing.stage == "held"
    assert standing.gaps == ()


def test_walk_skip_gap_named():
    standing = derive_standing(
        fresh_record(stages=("named", "run", "reported", "held")))
    assert standing.held is False
    assert any("named -> run" in g for g in standing.gaps)


def test_unheld_stage_stands_open():
    standing = derive_standing(
        fresh_record(stages=("named", "licensed", "run")))
    assert standing.held is False
    assert any("not held" in g for g in standing.gaps)


def test_listed_only_yardstick_never_held():
    standing = derive_standing(
        fresh_record(yardstick="swe_bench_multimodal"))
    assert standing.held is False
    assert any("listed-only" in g for g in standing.gaps)


def test_licence_without_licence_evidence_gap_named():
    standing = derive_standing(
        fresh_record(claims=("run_log_ref", "report_ref")))
    assert standing.held is False
    assert any("licence rests on no held licence evidence" in g
               for g in standing.gaps)


def test_bare_claims_only_stands_open():
    standing = derive_standing(
        fresh_record(claims=("feeling", "summary")))
    assert standing.held is False
    assert any("no held evidence" in g for g in standing.gaps)
    assert any("bare claims only" in g for g in standing.gaps)


def test_report_missing_model_stands_open():
    standing = derive_standing(fresh_record(model=""))
    assert standing.held is False
    assert any("names no model" in g for g in standing.gaps)


def test_report_missing_cost_stands_open():
    standing = derive_standing(fresh_record(cost=None))
    assert standing.held is False
    assert any("names no cost" in g for g in standing.gaps)


def test_report_missing_date_stands_open():
    standing = derive_standing(fresh_record(date=""))
    assert standing.held is False
    assert any("names no run date" in g for g in standing.gaps)


def test_missing_score_stands_open():
    standing = derive_standing(fresh_record(score=None))
    assert standing.held is False
    assert any("reports no score" in g for g in standing.gaps)


def test_bad_dates_refused():
    for bad in ("2026-13-40", "12 Nov 2026", "2026/11/12"):
        with pytest.raises(ValidationError, match="unknown run date"):
            derive_standing(fresh_record(date=bad))


def test_bad_costs_refused():
    with pytest.raises(ValidationError, match="cost is negative"):
        derive_standing(fresh_record(cost=-1.0))
    with pytest.raises(ValidationError, match="unknown run cost"):
        derive_standing(fresh_record(cost="free"))


def test_score_bounds_refused():
    with pytest.raises(ValidationError, match="never inflated"):
        derive_standing(fresh_record(score=100.5))
    with pytest.raises(ValidationError, match="score is negative"):
        derive_standing(fresh_record(score=-1.0))


def test_unknown_evidence_kind_refused():
    with pytest.raises(ValidationError, match="unknown run evidence kind"):
        derive_standing(fresh_record(claims=("hunch",)))


def test_unknown_model_type_refused():
    with pytest.raises(ValidationError, match="unknown run model"):
        derive_standing(fresh_record(model=42))


def test_evidence_kinds_partition():
    assert set(HELD_EVIDENCE) | set(BARE_CLAIMS) == set(EVIDENCE_KINDS)
    assert "licence_ref" in HELD_EVIDENCE
    assert "licence_ref" not in BARE_CLAIMS


def test_report_ready_and_shared():
    draft = prepare_report(
        "swe_bench", "swe_bench", "2026-11-a",
        "42.5 resolved, reported as run",
        "mythic-coder-7b", 12.5, "2026-11-12", 42.5,
        claims=("licence_ref", "report_ref"))
    assert draft.state == "ready"
    shared = prepare_report(
        "swe_bench", "swe_bench", "2026-11-a",
        "42.5 resolved, reported as run",
        "mythic-coder-7b", 12.5, "2026-11-12", 42.5,
        claims=("licence_ref", "report_ref"), state="shared")
    assert shared.state == "shared"
    assert REPORT_STATES == ("ready", "shared")


def test_report_sealed_state_and_inflated_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report(
            "swe_bench", "swe_bench", "2026-11-a", "x",
            "mythic-coder-7b", 12.5, "2026-11-12", 42.5,
            claims=("licence_ref",), state="sealed")
    draft = RunDraft(
        "swe_bench", "swe_bench", "2026-11-a",
        "beat the whole field", "mythic-coder-7b", 12.5,
        "2026-11-12", 42.5, ("licence_ref",), inflated=True)
    with pytest.raises(ValidationError, match="never inflated"):
        draft.validate()


def test_report_refusals_and_formats():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report(
            "swe_bench", "swe_bench", "2026-11-a",
            "we feel it did well", "mythic-coder-7b", 12.5,
            "2026-11-12", 42.5, claims=("feeling",))
    with pytest.raises(ValidationError, match="never inflated"):
        prepare_report(
            "swe_bench", "swe_bench", "2026-11-a", "x",
            "mythic-coder-7b", 12.5, "2026-11-12", 140.0,
            claims=("licence_ref",))
    with pytest.raises(ValidationError, match="names no model"):
        prepare_report(
            "swe_bench", "swe_bench", "2026-11-a", "x",
            "", 12.5, "2026-11-12", 42.5,
            claims=("licence_ref",))
    with pytest.raises(ValidationError, match="cost is negative"):
        prepare_report(
            "swe_bench", "swe_bench", "2026-11-a", "x",
            "mythic-coder-7b", -2.0, "2026-11-12", 42.5,
            claims=("licence_ref",))
    text = format_record(fresh_record())
    assert "swe_bench/2026-11-a" in text
    assert "score 42.5 of 100" in text
    assert "held as reported" in text
    open_text = format_record(fresh_record(model=""))
    assert "open:" in open_text
    assert "SWE-bench Verified" in format_yardsticks()
    joined = format_records([fresh_record(),
                             fresh_record(run="2026-11-b")])
    assert joined.count("\n") == 1
    assert "listed_only" in format_yardstick(
        default_registry().get("swe_bench_multimodal"))
