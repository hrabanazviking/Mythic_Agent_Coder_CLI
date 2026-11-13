"""M-267 Cost-of-quality report - pure-layer tests.

TIER: unit

Benchmark scores against spend per model route - the
honest shopping guide for the user's own money: a route
counts PROVEN only on scores measured against spend
actually paid resting on held evidence, and a roaded
route with no owner named stands open.
"""
import pytest

from mythic_agent.core.cost_of_quality import (
    ROUTES,
    BARE_CLAIMS,
    DISPOSITIONS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    STAGES,
    CostOfQualityEntry,
    CostOfQualityRegistry,
    CostOfQualityRecord,
    default_registry,
    derive_standing,
    derive_verdict,
    format_route,
    format_routes,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(route="Q-03",
                work="cost-2026-11-a",
                date="2026-11-13", disposition="PROVEN",
                owner="yrsa",
                proof_kind="measured-and-priced",
                stages=STAGES,
                claims=("benchmark_ref", "spend_ref"))
    base.update(kw)
    return CostOfQualityRecord(**base)


def roaded_record(**kw):
    base = dict(route="Q-05",
                work="cost-2026-11-a",
                date="2026-11-13", disposition="ROADED",
                owner="yrsa",
                proof_kind="measured-and-priced",
                stages=STAGES,
                claims=("spend_ref",))
    base.update(kw)
    return CostOfQualityRecord(**base)


def full_book(**overrides):
    records = []
    for route_id in default_registry().combinations():
        if route_id in ("Q-01", "Q-02", "Q-03"):
            kw = dict(route=route_id, work="cost-2026-11-a",
                      date="2026-11-13", disposition="PROVEN",
                      owner="yrsa",
                      proof_kind="measured-and-priced",
                      stages=STAGES,
                      claims=("benchmark_ref", "spend_ref"))
        else:
            kw = dict(route=route_id, work="cost-2026-11-a",
                      date="2026-11-13", disposition="ROADED",
                      owner="yrsa",
                      proof_kind="measured-and-priced",
                      stages=STAGES,
                      claims=("spend_ref",))
        kw.update(overrides.get(route_id, {}))
        records.append(CostOfQualityRecord(**kw))
    return records


def test_registry_holds_twelve_routes_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 12
    assert reg.ids()[0] == "Q-01"
    assert reg.ids()[-1] == "Q-12"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_routes_cover_the_doctrine_sources():
    reg = default_registry()
    pairs = {(e.doctrine, e.subject) for e in reg.entries()}
    assert len(pairs) == 12
    assert reg.get("Q-01").doctrine == "honest-shopping"
    assert reg.get("Q-01").subject == "local-free-route"
    assert reg.get("Q-02").subject == "local-aesir-route"
    assert reg.get("Q-03").subject == "cheap-cloud-route"
    assert reg.get("Q-04").subject == "mid-cloud-route"
    assert reg.get("Q-11").doctrine == "standing-law"
    assert reg.get("Q-11").subject == "spend-ledger-route"
    assert reg.get("Q-12").doctrine == "proof-duty"
    assert DISPOSITIONS == ("PROVEN", "ROADED")


def test_registry_unknown_route_refused_by_name():
    with pytest.raises(ValidationError, match="unknown route: Q-99"):
        default_registry().get("Q-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate route"):
        CostOfQualityRegistry(ROUTES + ROUTES[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        CostOfQualityRegistry([CostOfQualityEntry("Q-01", "honest-shopping", "local-free-route", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        CostOfQualityRegistry([CostOfQualityEntry("Q-01", "honest-shopping", "local-free-route", "published", "why")])
    with pytest.raises(ValidationError, match="benchmarked"):
        CostOfQualityRegistry([CostOfQualityEntry("Q-01", "honest-shopping", "local-free-route", "listed", "why", benchmarked=False)])
    with pytest.raises(ValidationError, match="priced"):
        CostOfQualityRegistry([CostOfQualityEntry("Q-01", "honest-shopping", "local-free-route", "listed", "why", priced=False)])


def test_entry_unknown_doctrine_refused():
    with pytest.raises(ValidationError, match="unknown route doctrine"):
        CostOfQualityRegistry([CostOfQualityEntry("Q-01", "M-999", "local-free-route", "listed", "why")])


def test_record_proven_measured_and_priced_stands_held():
    standing = derive_standing(fresh_record())
    assert standing.held
    assert standing.grade == "held"
    assert standing.gaps == ()


def test_record_incomplete_walk_stands_open():
    standing = derive_standing(fresh_record(stages=STAGES[:3]))
    assert not standing.held
    assert any("not held" in g for g in standing.gaps)


def test_record_bad_stage_step_stands_open():
    bad = ("named", "priced", "dispositioned", "held")
    standing = derive_standing(fresh_record(stages=bad))
    assert not standing.held
    assert any("not in the walk" in g for g in standing.gaps)


def test_record_proven_on_vendor_claim_stands_open():
    standing = derive_standing(fresh_record(proof_kind="vendor-claim-only"))
    assert not standing.held
    assert any("no vendor word" in g for g in standing.gaps)


def test_record_proven_without_benchmark_evidence_stands_open():
    standing = derive_standing(fresh_record(claims=("spend_ref",)))
    assert not standing.held
    assert any("no held benchmark evidence" in g for g in standing.gaps)


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
    assert any("no report date" in g for g in standing.gaps)


def test_record_unknown_disposition_refused():
    with pytest.raises(ValidationError, match="unknown record disposition"):
        derive_standing(fresh_record(disposition="MAYBE"))


def test_verdict_full_book_ready_with_roaded_routes():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.proven_routes == ("Q-01", "Q-02", "Q-03")
    assert len(verdict.roaded_routes) == 9
    assert verdict.missing_routes == ()


def test_verdict_missing_route_stops_the_report():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_routes == ("Q-12",)
    assert any("Q-12" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_report():
    verdict = derive_verdict(full_book(**{"Q-02": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("Q-02 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_route_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two findings" in g for g in verdict.gaps)


def test_report_ready_and_shared_states():
    report = prepare_report("cost-a", "Q-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("benchmark_ref",))
    assert report.state == "ready"
    shared = prepare_report("cost-a", "Q-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("benchmark_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_and_short_certified_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("cost-a", "Q-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("benchmark_ref",), state="sealed")
    with pytest.raises(ValidationError, match="cost report complete"):
        prepare_report("cost-a", "Q-01", "findings", "2026-11-13",
                       3, 5, 12, claims=("benchmark_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("cost-a", "Q-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("feeling",))
    assert "Q-01" in format_route(default_registry().get("Q-01"))
    assert "Q-12" in format_routes()
    assert "PROVEN" in format_record(fresh_record())
    assert "ROADED" in format_records([roaded_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)
    from pathlib import Path as _P
    _src = (_P(__file__).resolve().parent.parent
            / "mythic_agent" / "core" / "cost_of_quality.py").read_text(
                encoding="utf-8")
    assert "open(" not in _src
    assert "socket" not in _src
    assert "subprocess" not in _src
    assert "urllib" not in _src
