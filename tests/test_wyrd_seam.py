"""M-249 The WYRD seam - pure-layer tests.

TIER: unit

World-state enters a campaign only as a recorded snapshot
with provenance and a timestamp; an absent snapshot reads
as unknown and a stale one as stale, never as current
fact, and the seam only advises campaigns.
"""
import pytest

from mythic_agent.core.wyrd_seam import (
    AVAILABILITIES,
    BARE_CLAIMS,
    FORGE_STATES,
    FRESH_LIMIT_SECONDS,
    HELD_EVIDENCE,
    LOAD_BANDS,
    SOURCES,
    STAGES,
    AdviceDraft,
    NodeSnapshot,
    SourceEntry,
    SourceRegistry,
    default_registry,
    derive_standing,
    format_snapshot,
    format_source,
    format_sources,
    propose_advice,
)
from mythic_agent.core.validation import ValidationError


def fresh_snapshot(**kw):
    base = dict(source="wyrd_engine", node="purplelongship",
                availability="free", forge_state="hot",
                load_band="light", campaign_position="M-249 building",
                observed_at="2026-11-12T12:00:00", age_seconds=60,
                stages=STAGES, claims=("engine_ref",))
    base.update(kw)
    return NodeSnapshot(**base)


def test_registry_holds_four_sources_recorded_only():
    reg = default_registry()
    assert reg.ids() == ("wyrd_engine", "manual_report",
                         "campaign_journal", "keeper_report")
    assert all(e.transport == "recorded" for e in reg.entries())


def test_registry_unknown_source_refused_by_name():
    with pytest.raises(ValidationError, match="unknown wyrd source: guess"):
        default_registry().get("guess")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate wyrd source"):
        SourceRegistry(SOURCES + SOURCES[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing label"):
        SourceRegistry([SourceEntry("x", "", "snapshot", "recorded", "why")])


def test_entry_live_transport_refused():
    with pytest.raises(ValidationError, match="recorded data only"):
        SourceRegistry([SourceEntry("x", "X", "snapshot", "live", "why")])


def test_source_words_differ_by_source():
    reg = default_registry()
    assert reg.get("wyrd_engine").snapshot_word == "snapshot"
    assert reg.get("manual_report").snapshot_word == "report"
    assert reg.get("campaign_journal").snapshot_word == "entry"
    assert reg.get("keeper_report").snapshot_word == "report"


def test_fresh_held_snapshot_stands_held():
    standing = derive_standing(fresh_snapshot())
    assert standing.held and standing.stage == "held"
    assert standing.freshness == "current" and standing.gaps == ()


def test_bare_claims_only_stands_open():
    standing = derive_standing(fresh_snapshot(claims=("assertion",)))
    assert not standing.held
    assert any("bare claims" in g for g in standing.gaps)


def test_no_evidence_stands_open():
    standing = derive_standing(fresh_snapshot(claims=()))
    assert not standing.held
    assert any("no held evidence" in g for g in standing.gaps)


def test_unfinished_walk_stands_open():
    standing = derive_standing(fresh_snapshot(stages=("reported", "recorded")))
    assert not standing.held and standing.stage == "recorded"


def test_walk_must_open_at_reported():
    standing = derive_standing(
        fresh_snapshot(stages=("recorded", "checked", "held")))
    assert not standing.held
    assert any("open at reported" in g for g in standing.gaps)


def test_walk_rejects_skipped_stage():
    standing = derive_standing(
        fresh_snapshot(stages=("reported", "checked", "held")))
    assert not standing.held
    assert any("not in the walk" in g for g in standing.gaps)


def test_stale_snapshot_stands_open_as_stale():
    standing = derive_standing(
        fresh_snapshot(age_seconds=FRESH_LIMIT_SECONDS + 1))
    assert not standing.held and standing.freshness == "stale"
    assert any("stale" in g for g in standing.gaps)
    fresh = derive_standing(
        fresh_snapshot(age_seconds=FRESH_LIMIT_SECONDS))
    assert fresh.held and fresh.freshness == "current"


def test_unknown_availability_or_forge_stands_open():
    standing = derive_standing(fresh_snapshot(availability="unknown"))
    assert not standing.held
    assert any("availability" in g for g in standing.gaps)
    standing = derive_standing(fresh_snapshot(forge_state="unknown"))
    assert not standing.held
    assert any("forge state" in g for g in standing.gaps)


def test_snapshot_unknown_source_and_missing_fields_refused():
    with pytest.raises(ValidationError, match="unknown wyrd source"):
        derive_standing(fresh_snapshot(source="guess"))
    with pytest.raises(ValidationError, match="no node"):
        fresh_snapshot(node=" ").validate()
    with pytest.raises(ValidationError, match="no observed time"):
        fresh_snapshot(observed_at="").validate()


def test_snapshot_state_words_must_be_known():
    with pytest.raises(ValidationError, match="unknown availability"):
        fresh_snapshot(availability="green").validate()
    with pytest.raises(ValidationError, match="unknown forge state"):
        fresh_snapshot(forge_state="green").validate()
    with pytest.raises(ValidationError, match="unknown load band"):
        fresh_snapshot(load_band="green").validate()
    for availability in AVAILABILITIES:
        fresh_snapshot(availability=availability).validate()
    for forge_state in FORGE_STATES:
        fresh_snapshot(forge_state=forge_state).validate()
    for load_band in LOAD_BANDS:
        fresh_snapshot(load_band=load_band).validate()


def test_snapshot_claim_kind_and_age_must_be_known():
    with pytest.raises(ValidationError, match="unknown wyrd evidence kind"):
        fresh_snapshot(claims=("vibes",)).validate()
    for kind in HELD_EVIDENCE + BARE_CLAIMS:
        fresh_snapshot(claims=(kind,)).validate()
    with pytest.raises(ValidationError, match="non-negative"):
        fresh_snapshot(age_seconds=-1).validate()


def test_advice_defaults_to_pending_approval():
    draft = propose_advice("mythic-coder", "purplelongship",
                           "build M-249 there")
    assert draft.approval == "pending" and draft.applied is False


def test_advice_unapproved_execution_refused():
    with pytest.raises(ValidationError, match="by approval only"):
        propose_advice("c", "n", "x", approval="executed")
    approved = propose_advice("c", "n", "x", approval="approved")
    assert approved.approval == "approved" and approved.applied is False


def test_advice_never_applied_and_format_lines():
    with pytest.raises(ValidationError, match="advisory only"):
        AdviceDraft("c", "n", "x", applied=True).validate()
    with pytest.raises(ValidationError, match="no campaign"):
        propose_advice(" ", "n", "x")
    with pytest.raises(ValidationError, match="no node"):
        propose_advice("c", " ", "x")
    with pytest.raises(ValidationError, match="proposes nothing"):
        propose_advice("c", "n", " ")
    reg = default_registry()
    assert "WYRD engine" in format_source(reg.get("wyrd_engine"))
    assert "via recorded" in format_source(reg.get("keeper_report"))
    assert format_sources(reg).count("\n") == 3
    line = format_snapshot(fresh_snapshot())
    assert "current as recorded" in line and "purplelongship" in line
    open_line = format_snapshot(fresh_snapshot(claims=()))
    assert "open:" in open_line
