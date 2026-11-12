"""M-250 Webhook doors - pure-layer tests.

TIER: unit

Inbound events enter a campaign only as a recorded event
with provenance and a timestamp; an absent event reads
as unknown and a stale one as stale, never as a fact,
and the doors only propose campaigns - nothing builds
unbidden.
"""
import pytest

from mythic_agent.core.webhook_doors import (
    BARE_CLAIMS,
    EVENT_KINDS,
    FRESH_LIMIT_SECONDS,
    HELD_EVIDENCE,
    SOURCES,
    STAGES,
    InboundEvent,
    ProposalDraft,
    SourceEntry,
    SourceRegistry,
    default_registry,
    derive_standing,
    format_event,
    format_source,
    format_sources,
    propose_proposal,
)
from mythic_agent.core.validation import ValidationError


def fresh_event(**kw):
    base = dict(source="github", event="pr-42",
                kind="pr_opened", title="Fix the seam",
                subject="PR 42 in mythic-coder",
                observed_at="2026-11-12T12:00:00", age_seconds=60,
                stages=STAGES, claims=("payload_ref",))
    base.update(kw)
    return InboundEvent(**base)


def test_registry_holds_four_sources_recorded_only():
    reg = default_registry()
    assert reg.ids() == ("github", "gitlab",
                         "bitbucket", "generic")
    assert all(e.transport == "recorded" for e in reg.entries())


def test_registry_unknown_source_refused_by_name():
    with pytest.raises(ValidationError, match="unknown webhook source: guess"):
        default_registry().get("guess")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate webhook source"):
        SourceRegistry(SOURCES + SOURCES[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing label"):
        SourceRegistry([SourceEntry("x", "", "event", "recorded", "why")])


def test_entry_live_transport_refused():
    with pytest.raises(ValidationError, match="recorded data only"):
        SourceRegistry([SourceEntry("x", "X", "event", "live", "why")])


def test_source_words_differ_by_source():
    reg = default_registry()
    assert reg.get("github").event_word == "event"
    assert reg.get("gitlab").event_word == "event"
    assert reg.get("bitbucket").event_word == "event"
    assert reg.get("generic").event_word == "delivery"


def test_fresh_held_event_stands_held():
    standing = derive_standing(fresh_event())
    assert standing.held and standing.stage == "held"
    assert standing.freshness == "current" and standing.gaps == ()


def test_bare_claims_only_stands_open():
    standing = derive_standing(fresh_event(claims=("assertion",)))
    assert not standing.held
    assert any("bare claims" in g for g in standing.gaps)


def test_no_evidence_stands_open():
    standing = derive_standing(fresh_event(claims=()))
    assert not standing.held
    assert any("no held evidence" in g for g in standing.gaps)


def test_unfinished_walk_stands_open():
    standing = derive_standing(fresh_event(stages=("received", "recorded")))
    assert not standing.held and standing.stage == "recorded"


def test_walk_must_open_at_received():
    standing = derive_standing(
        fresh_event(stages=("recorded", "checked", "held")))
    assert not standing.held
    assert any("open at received" in g for g in standing.gaps)


def test_walk_rejects_skipped_stage():
    standing = derive_standing(
        fresh_event(stages=("received", "checked", "held")))
    assert not standing.held
    assert any("not in the walk" in g for g in standing.gaps)


def test_stale_event_stands_open_as_stale():
    standing = derive_standing(
        fresh_event(age_seconds=FRESH_LIMIT_SECONDS + 1))
    assert not standing.held and standing.freshness == "stale"
    assert any("stale" in g for g in standing.gaps)
    fresh = derive_standing(
        fresh_event(age_seconds=FRESH_LIMIT_SECONDS))
    assert fresh.held and fresh.freshness == "current"


def test_unknown_kind_or_no_subject_stands_open():
    standing = derive_standing(fresh_event(kind="unknown"))
    assert not standing.held
    assert any("kind" in g for g in standing.gaps)
    standing = derive_standing(fresh_event(subject=""))
    assert not standing.held
    assert any("subject" in g for g in standing.gaps)


def test_event_unknown_source_and_missing_fields_refused():
    with pytest.raises(ValidationError, match="unknown webhook source"):
        derive_standing(fresh_event(source="guess"))
    with pytest.raises(ValidationError, match="no event"):
        fresh_event(event=" ").validate()
    with pytest.raises(ValidationError, match="no observed time"):
        fresh_event(observed_at="").validate()


def test_event_kind_words_must_be_known():
    with pytest.raises(ValidationError, match="unknown webhook event kind"):
        fresh_event(kind="green").validate()
    for kind in EVENT_KINDS:
        fresh_event(kind=kind).validate()


def test_event_claim_kind_and_age_must_be_known():
    with pytest.raises(ValidationError, match="unknown webhook evidence kind"):
        fresh_event(claims=("vibes",)).validate()
    for kind in HELD_EVIDENCE + BARE_CLAIMS:
        fresh_event(claims=(kind,)).validate()
    with pytest.raises(ValidationError, match="non-negative"):
        fresh_event(age_seconds=-1).validate()


def test_proposal_defaults_to_pending_approval():
    draft = propose_proposal("mythic-coder", "github", "pr-42",
                             "build the seam fix")
    assert draft.approval == "pending" and draft.applied is False


def test_proposal_unapproved_execution_refused():
    with pytest.raises(ValidationError, match="by approval only"):
        propose_proposal("c", "github", "pr-1", "x", approval="executed")
    approved = propose_proposal("c", "github", "pr-1", "x", approval="approved")
    assert approved.approval == "approved" and approved.applied is False


def test_proposal_never_applied_and_format_lines():
    with pytest.raises(ValidationError, match="proposals only"):
        ProposalDraft("c", "github", "pr-1", "x", applied=True).validate()
    with pytest.raises(ValidationError, match="no campaign"):
        propose_proposal(" ", "github", "pr-1", "x")
    with pytest.raises(ValidationError, match="no event"):
        propose_proposal("c", "github", " ", "x")
    with pytest.raises(ValidationError, match="proposes nothing"):
        propose_proposal("c", "github", "pr-1", " ")
    reg = default_registry()
    assert "GitHub" in format_source(reg.get("github"))
    assert "via recorded" in format_source(reg.get("generic"))
    assert format_sources(reg).count("\n") == 3
    line = format_event(fresh_event())
    assert "held as recorded" in line and "pr-42" in line
    open_line = format_event(fresh_event(claims=()))
    assert "open:" in open_line
