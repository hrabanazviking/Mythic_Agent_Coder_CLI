"""M-258 Performance budgets - pure-layer tests.

TIER: unit

Cold start, repo-map build on a 100k-file repo, TUI
frame health, memory ceiling - measured on the VM,
Mimir-class ARM, and the laptop; budgets from
measurement: a measure whose run rests on no held
measurement evidence, or whose measurement stands
over its budget on any machine, holds the whole
book open.
"""
import pytest

from mythic_agent.core.performance_budgets import (
    BARE_CLAIMS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    MACHINES,
    MEASURES,
    STAGES,
    BudgetEntry,
    BudgetRecord,
    BudgetRegistry,
    default_registry,
    derive_standing,
    derive_verdict,
    format_measure,
    format_measures,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(measure="cold_start", machine="vm",
                run="bench-2026-11-a",
                date="2026-11-13", measured=800, limit=1000,
                stages=STAGES,
                claims=("measurement_log_ref", "benchmark_ref"))
    base.update(kw)
    return BudgetRecord(**base)


def full_book(**overrides):
    records = []
    for measure, machine in default_registry().combinations():
        kw = dict(measure=measure, machine=machine,
                  run="bench-2026-11-a",
                  date="2026-11-13", measured=800, limit=1000,
                  stages=STAGES,
                  claims=("measurement_log_ref", "benchmark_ref"))
        kw.update(overrides.get(f"{measure}/{machine}", {}))
        records.append(BudgetRecord(**kw))
    return records


def test_registry_holds_four_measures_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 4
    assert reg.ids()[0] == "cold_start"
    assert reg.ids()[-1] == "memory_ceiling"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_measure_units_and_machines():
    reg = default_registry()
    assert reg.get("cold_start").unit == "milliseconds"
    assert reg.get("memory_ceiling").unit == "megabytes"
    assert reg.get("repo_map_100k").label == "Repo-map build on a 100k-file repo"
    assert tuple(m.id for m in MACHINES) == ("vm", "mimir_arm", "laptop")


def test_registry_unknown_measure_refused_by_name():
    with pytest.raises(ValidationError, match="unknown measure: warp_drive"):
        default_registry().get("warp_drive")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate measure"):
        BudgetRegistry(MEASURES + MEASURES[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing label"):
        BudgetRegistry([BudgetEntry(
            "cold_start", "", "milliseconds", "listed", "why")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        BudgetRegistry([BudgetEntry(
            "cold_start", "X", "milliseconds", "published", "why")])


def test_record_complete_within_budget_stands_held():
    standing = derive_standing(fresh_record())
    assert standing.held
    assert standing.grade == "held"
    assert standing.gaps == ()


def test_record_incomplete_walk_stands_open():
    standing = derive_standing(fresh_record(stages=STAGES[:3]))
    assert not standing.held
    assert any("not held" in g for g in standing.gaps)


def test_record_bad_stage_step_stands_open():
    bad = ("named", "compared", "judged", "held")
    standing = derive_standing(fresh_record(stages=bad))
    assert not standing.held
    assert any("not in the walk" in g for g in standing.gaps)


def test_record_over_budget_stops_the_claim():
    standing = derive_standing(fresh_record(measured=1200))
    assert not standing.held
    assert any("over its budget" in g for g in standing.gaps)


def test_record_without_measurement_evidence_stands_open():
    standing = derive_standing(fresh_record(claims=("benchmark_ref",)))
    assert not standing.held
    assert any("no held measurement evidence" in g for g in standing.gaps)


def test_record_bare_claims_only_stand_open():
    standing = derive_standing(fresh_record(claims=("feeling",)))
    assert not standing.held
    assert any("bare claims only" in g for g in standing.gaps)


def test_record_unknown_evidence_kind_refused():
    with pytest.raises(ValidationError, match="unknown record evidence kind"):
        derive_standing(fresh_record(claims=("rumour",)))


def test_record_bad_date_refused():
    with pytest.raises(ValidationError, match="unknown measurement date"):
        derive_standing(fresh_record(date="13/11/2026"))


def test_record_negative_measurement_refused():
    with pytest.raises(ValidationError, match="negative"):
        derive_standing(fresh_record(measured=-1))


def test_record_unknown_machine_refused():
    with pytest.raises(ValidationError, match="unknown machine: toaster"):
        derive_standing(fresh_record(machine="toaster"))


def test_verdict_ready_when_every_combination_held():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.over_combinations == ()
    assert verdict.missing_combinations == ()


def test_verdict_one_over_budget_stops_the_whole_book():
    verdict = derive_verdict(full_book(
        **{"tui_frame/laptop": dict(measured=1200)}))
    assert not verdict.ready
    assert verdict.over_combinations == ("tui_frame/laptop",)


def test_verdict_missing_combination_stops_the_book():
    verdict = derive_verdict(full_book()[:11])
    assert not verdict.ready
    assert verdict.missing_combinations == ("memory_ceiling/laptop",)


def test_verdict_open_record_stops_the_book():
    verdict = derive_verdict(full_book(
        **{"cold_start/vm": dict(claims=("summary",))}))
    assert not verdict.ready
    assert any("cold_start/vm stands open" in g for g in verdict.gaps)


def test_prepare_report_all_within_may_certify():
    draft = prepare_report(
        "bench-2026-11", "release-1", "every combination within budget",
        "2026-11-13", 12, 12, claims=("measurement_log_ref",),
        certified=True)
    assert draft.state == "ready"
    assert draft.certified


def test_prepare_report_certify_short_of_within_refused():
    with pytest.raises(ValidationError, match="stops the certification"):
        prepare_report(
            "bench-2026-11", "release-1", "mostly within",
            "2026-11-13", 11, 12, claims=("measurement_log_ref",),
            certified=True)


def test_prepare_report_sealed_state_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report(
            "bench-2026-11", "release-1", "every combination within budget",
            "2026-11-13", 12, 12, claims=("measurement_log_ref",),
            state="sealed")


def test_prepare_report_bare_claim_refused():
    with pytest.raises(ValidationError, match="held measurements only"):
        prepare_report(
            "bench-2026-11", "release-1", "every combination within budget",
            "2026-11-13", 12, 12, claims=("feeling",))


def test_format_roads_name_the_measure_and_machine():
    line = format_record(fresh_record())
    assert "cold_start/vm" in line
    assert "800 of budget 1000 milliseconds" in line
    assert "held as measured" in line
    measure_line = format_measure(default_registry().get("memory_ceiling"))
    assert "Memory ceiling" in measure_line
    assert "megabytes" in measure_line
    assert len(format_measures().splitlines()) == 4
    assert len(format_records(full_book()).splitlines()) == 12
    assert HELD_EVIDENCE[0] == "measurement_log_ref"
    assert BARE_CLAIMS[-1] == "summary"
    assert "measurement_log_ref" in EVIDENCE_KINDS
    assert MEASURES[0].id == "cold_start"
