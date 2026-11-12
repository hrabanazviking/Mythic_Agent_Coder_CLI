"""Slice tests for M-247 CI bridges (pure layer)."""
import pytest

from mythic_agent.core.ci_bridges import (
    BARE_CLAIMS,
    CONCLUSIONS,
    HELD_EVIDENCE,
    PROVIDERS,
    STAGES,
    CIRecord,
    ProviderEntry,
    ProviderRegistry,
    WorkflowDraft,
    default_registry,
    derive_standing,
    format_provider,
    format_providers,
    format_record,
    propose_draft,
)
from mythic_agent.core.validation import ValidationError


def held_record(**kw):
    base = dict(provider="github_actions", workflow="CI", ref="main",
                conclusion="passed", stages=STAGES, claims=("run_ref",))
    base.update(kw)
    return CIRecord(**base)


def test_registry_holds_four_providers():
    reg = default_registry()
    assert reg.ids() == ("github_actions", "gitlab_ci",
                         "bitbucket_pipelines", "local_manual")


def test_registry_unknown_provider_refused_by_name():
    with pytest.raises(ValidationError, match="unknown ci provider: circle"):
        default_registry().get("circle")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate ci provider"):
        ProviderRegistry(PROVIDERS + PROVIDERS[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing label"):
        ProviderRegistry([ProviderEntry("x", "", "run", "why")])


def test_provider_words_differ_by_provider():
    reg = default_registry()
    assert reg.get("github_actions").run_word == "workflow run"
    assert reg.get("gitlab_ci").run_word == "pipeline"


def test_held_record_stands_held():
    standing = derive_standing(held_record())
    assert standing.held and standing.stage == "held" and standing.gaps == ()


def test_bare_claims_only_stands_open():
    standing = derive_standing(held_record(claims=("assertion",)))
    assert not standing.held
    assert any("bare claims" in g for g in standing.gaps)


def test_no_evidence_stands_open():
    standing = derive_standing(held_record(claims=()))
    assert not standing.held
    assert any("no held evidence" in g for g in standing.gaps)


def test_unfinished_walk_stands_open():
    standing = derive_standing(held_record(stages=("seen", "fetched")))
    assert not standing.held and standing.stage == "fetched"


def test_walk_must_open_at_seen():
    standing = derive_standing(held_record(stages=("fetched", "read", "held")))
    assert not standing.held
    assert any("open at seen" in g for g in standing.gaps)


def test_walk_rejects_skipped_stage():
    standing = derive_standing(held_record(stages=("seen", "read", "held")))
    assert not standing.held
    assert any("not in the walk" in g for g in standing.gaps)


def test_record_unknown_provider_refused():
    with pytest.raises(ValidationError, match="unknown ci provider"):
        derive_standing(held_record(provider="circle"))


def test_record_names_workflow_and_ref():
    with pytest.raises(ValidationError, match="no workflow"):
        held_record(workflow=" ").validate()
    with pytest.raises(ValidationError, match="no ref"):
        held_record(ref="").validate()


def test_record_conclusion_must_be_known():
    with pytest.raises(ValidationError, match="unknown ci conclusion"):
        held_record(conclusion="green").validate()
    for conclusion in CONCLUSIONS:
        held_record(conclusion=conclusion).validate()


def test_record_claim_kind_must_be_known():
    with pytest.raises(ValidationError, match="unknown ci evidence kind"):
        held_record(claims=("vibes",)).validate()
    for kind in HELD_EVIDENCE + BARE_CLAIMS:
        held_record(claims=(kind,)).validate()


def test_draft_defaults_to_manual_dispatch():
    draft = propose_draft("github_actions", "CI", "add a cache step")
    assert draft.trigger == "workflow_dispatch" and draft.applied is False


def test_draft_automatic_trigger_refused():
    with pytest.raises(ValidationError, match="manually"):
        propose_draft("github_actions", "CI", "x", trigger="push")


def test_draft_never_applied():
    with pytest.raises(ValidationError, match="drafts only"):
        WorkflowDraft("github_actions", "CI", "x", applied=True).validate()


def test_draft_names_workflow_and_change():
    with pytest.raises(ValidationError, match="no workflow"):
        propose_draft("github_actions", " ", "x")
    with pytest.raises(ValidationError, match="no change"):
        propose_draft("github_actions", "CI", " ")


def test_format_lines():
    reg = default_registry()
    assert "GitHub Actions" in format_provider(reg.get("github_actions"))
    assert format_providers(reg).count("\n") == 3
    line = format_record(held_record())
    assert "held as fact" in line and "passed" in line
    open_line = format_record(held_record(claims=()))
    assert "open:" in open_line
