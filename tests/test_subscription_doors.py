"""
TIER: unit
Subscription Doors Study gate (All-Features roadmap slice M-033).

The shipped study (``mythic_agent/data/subscription_doors.yaml``)
records, clean-room from the vendors' own public documentation
and legal pages, the OAuth-style subscription sign-ins some rivals
use — and verdicted each one: built only where the provider's
terms allow, else NOT OFFERED with the reason. These tests
cross-check the study against the live tree it must serve: the
studied rivals must appear in the M-001 feature census; every
Mythic provider a door claims to map to must exist in the M-019
registry (and must still authenticate by API key — no subscription
auth has shipped); and no door may claim to be built.
"""

import copy

import pytest

from mythic_agent.core.feature_census import load_census
from mythic_agent.core.provider_registry import load_registry
from mythic_agent.core.subscription_doors import (
    DOOR_IDS,
    NEVER_BORROW,
    NEVER_IMPERSONATE,
    SubscriptionDoors,
    load_study,
    render_markdown,
    validate_study,
)
from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource


@pytest.fixture(scope="module")
def study() -> SubscriptionDoors:
    return load_study()


def test_shipped_study_loads_and_validates(study):
    assert isinstance(study, SubscriptionDoors)
    assert validate_study(load_resource("subscription_doors.yaml")) == []
    assert study.counts() == (5, 6, 6)


def test_doors_are_the_studied_five_in_order(study):
    assert study.door_ids() == DOOR_IDS
    assert [d.vendor for d in study.doors] == [
        "Anthropic", "OpenAI", "OpenAI", "Google", "GitHub",
    ]


def test_verdicts_are_the_recorded_truth(study):
    assert study.verdicts() == (
        "not_offered",
        "first_party_only",
        "allowed_via_programme",
        "not_offered",
        "not_offered",
    )
    assert [d.door for d in study.not_offered()] == [
        "anthropic-claude-subscription",
        "google-sign-in",
        "github-copilot-sign-in",
    ]


def test_nothing_is_built(study):
    assert all(d.built is False for d in study.doors)
    allowed = [
        d for d in study.doors if d.verdict == "allowed_via_programme"
    ]
    assert len(allowed) == 1
    assert allowed[0].door == "openai-sign-in-with-chatgpt"
    assert "NOT BUILT" in allowed[0].mythic_action


def test_rivals_appear_in_the_feature_census(study):
    census_rivals = {r.id for r in load_census().rivals}
    for slug in {d.rival for d in study.doors}:
        assert slug in census_rivals
    assert {d.rival for d in study.doors} == {
        "claude-code", "codex-cli", "gemini-cli", "copilot-cli",
    }


def test_mapped_providers_exist_and_still_use_api_keys(study):
    registry = load_registry()
    assert study.provider_names() == (
        "anthropic", "openai", "openai", "google", "none",
    )
    for name in study.provider_names():
        if name == "none":
            continue
        assert name in registry.names()
        # The registry truth: every mapped provider still
        # authenticates by API key — no subscription door has
        # shipped behind this study's back.
        assert registry.provider(name).auth_style == "api_key_env"


def test_anthropic_door_records_the_prohibition(study):
    door = study.doors[0]
    assert door.verdict == "not_offered"
    assert "not permitted" in door.verdict_reason
    assert "Consumer Terms" in door.verdict_reason
    assert "API key" in door.mythic_action


def test_openai_doors_distinguish_first_party_from_programme(study):
    first_party, programme = study.doors[1], study.doors[2]
    assert first_party.verdict == "first_party_only"
    assert "auth store" in first_party.verdict_reason
    assert programme.verdict == "allowed_via_programme"
    assert "open-source" in programme.verdict_reason
    assert "Kista" in programme.mythic_action


def test_google_door_records_the_withdrawal(study):
    door = study.doors[3]
    assert door.verdict == "not_offered"
    assert "2026-06-18" in door.verdict_reason
    assert "policy-violating" in door.verdict_reason


def test_copilot_door_honestly_has_no_mythic_provider(study):
    door = study.doors[4]
    assert door.mythic_provider == "none"
    assert door.verdict == "not_offered"
    assert "Copilot Requests" in door.flow


def test_rules_carry_the_never_rules_verbatim(study):
    assert NEVER_BORROW in study.rule_texts()
    assert NEVER_IMPERSONATE in study.rule_texts()


def test_render_covers_every_entry(study):
    text = render_markdown(study)
    for door in study.doors:
        assert door.id in text and door.name in text
        assert door.verdict_reason in text
        assert door.mythic_action in text
    for finding in study.findings:
        assert finding.id in text and finding.finding in text
    for rule_text in study.rule_texts():
        assert rule_text in text
    assert "NOT OFFERED: 3 of 5 doors." in text


def _tampered(mutator):
    data = copy.deepcopy(load_resource("subscription_doors.yaml"))
    mutator(data)
    return data


def test_validation_rejects_an_unknown_verdict():
    data = _tampered(lambda d: d["doors"][0].update(verdict="maybe"))
    problems = validate_study(data)
    assert any("verdict" in p for p in problems)
    with pytest.raises(ValidationError):
        load_study(data)


def test_validation_rejects_a_built_door():
    data = _tampered(lambda d: d["doors"][2].update(built=True))
    problems = validate_study(data)
    assert any("built must be false" in p for p in problems)
    with pytest.raises(ValidationError):
        load_study(data)


def test_validation_rejects_dropping_the_never_borrow_rule():
    data = _tampered(lambda d: d["rules"][0].update(
        rule="borrowing a credential is fine, politely"))
    problems = validate_study(data)
    assert any("never-borrow" in p for p in problems)


def test_validation_rejects_dropping_the_never_impersonate_rule():
    data = _tampered(lambda d: d["rules"][1].update(
        rule="impersonation is fine, politely"))
    problems = validate_study(data)
    assert any("never-impersonate" in p for p in problems)


def test_validation_rejects_a_reasonless_not_offered_door():
    data = _tampered(lambda d: d["doors"][0].update(verdict_reason=""))
    problems = validate_study(data)
    assert any("verdict_reason" in p for p in problems)


def test_validation_rejects_reordering_the_doors():
    def swap(d):
        d["doors"][0], d["doors"][1] = d["doors"][1], d["doors"][0]
        d["doors"][0]["id"] = "D-01"
        d["doors"][1]["id"] = "D-02"

    problems = validate_study(_tampered(swap))
    assert any("study order" in p for p in problems)
