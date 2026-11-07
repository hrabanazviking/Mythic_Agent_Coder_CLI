"""M-115 - Offline and degraded grace.

TIER: unit (pure layer)

Covers the M-115 pure layer
(``mythic_agent.core.offline_grace``): failure kinds
held as validated data with the capability each one
loses stated in plain words, a mechanical judge that
derives the degradation state from given evidence
only, the session-news record, the deterministic
registry, and the shared /grace parser + formatters.
The agent layer is a later slice; nothing here wires
the Agent, TUI or terminal.
"""

from __future__ import annotations

import pytest

from mythic_agent.core.offline_grace import (
    FAILURE_KINDS,
    KEPT_CAPABILITIES,
    LOST_CAPABILITIES,
    OFFLINE_GRACE_SLICE,
    PLAIN_EXPLANATION,
    STATES,
    USAGE,
    DegradationAssessment,
    DegradationFailure,
    DegradationRegistry,
    build_failure,
    degradation_record,
    format_assessment,
    format_failure,
    format_failures,
    format_grace_record,
    format_grace_screen,
    judge_degradation,
    normalize_failure_kind,
    normalize_lsp_status,
    normalize_network_status,
    normalize_provider_status,
    parse_grace_args,
    plain_words,
    validate_failure,
)

FULL = {"provider": "reachable", "lsp": "up", "network": "up"}


# -- vocabulary and failure data -------------------------------------


def test_slice_and_vocabulary():
    assert OFFLINE_GRACE_SLICE == "M-115"
    assert FAILURE_KINDS == ("provider_down", "lsp_down", "network_down")
    assert STATES == ("full", "degraded", "unknown")
    assert set(LOST_CAPABILITIES) == set(FAILURE_KINDS)
    assert set(KEPT_CAPABILITIES) == set(FAILURE_KINDS)
    assert "what it lost" in PLAIN_EXPLANATION


def test_normalize_failure_kind_aliases_and_refusal():
    assert normalize_failure_kind("Provider-Unreachable") == "provider_down"
    assert normalize_failure_kind("LSP") == "lsp_down"
    assert normalize_failure_kind("net down") == "network_down"
    with pytest.raises(ValueError):
        normalize_failure_kind("disk_full")
    with pytest.raises(ValueError):
        normalize_failure_kind("")
    with pytest.raises(ValueError):
        normalize_failure_kind(None)


def test_status_normalizers():
    assert normalize_provider_status(None) == "unknown"
    assert normalize_provider_status("needs_key") == "needs-key"
    assert normalize_provider_status("REACHABLE") == "reachable"
    assert normalize_lsp_status("running") == "up"
    assert normalize_lsp_status(None) == "unknown"
    assert normalize_network_status("offline") == "down"
    with pytest.raises(ValueError):
        normalize_provider_status("flaky")
    with pytest.raises(ValueError):
        normalize_lsp_status("flaky")
    with pytest.raises(ValueError):
        normalize_network_status(3)


def test_failure_validation_and_record():
    failure = build_failure("lsp_down", "  pyright exited  ")
    assert failure.detail == "pyright exited"
    assert "diagnostics" in failure.lost[0]
    record = failure.to_record()
    assert record["kind"] == "lsp_down"
    assert record["lost"] == list(failure.lost)
    assert validate_failure({"failure": "provider", "evidence": "refused"}).detail == "refused"
    assert validate_failure("network").kind == "network_down"


def test_failure_refusals():
    with pytest.raises(ValueError):
        DegradationFailure(kind="unknown_thing")
    with pytest.raises(ValueError):
        DegradationFailure(kind="lsp_down", detail=3)
    with pytest.raises(ValueError):
        validate_failure({"kind": "lsp_down", "bogus": 1})
    with pytest.raises(ValueError):
        validate_failure({"kind": "lsp_down", "failure": "provider_down"})
    with pytest.raises(ValueError):
        validate_failure({"detail": "no kind"})
    with pytest.raises(ValueError):
        validate_failure(42)


# -- the judge ---------------------------------------------------------


def test_judge_full_only_from_full_evidence():
    result = judge_degradation(FULL)
    assert result.state == "full"
    assert result.failures == ()
    assert result.unknowns == ()
    assert result.lost == ()
    assert "full" in plain_words(result)


def test_judge_each_failure_kind():
    provider = judge_degradation({**FULL, "provider": "unreachable"})
    assert provider.state == "degraded"
    assert provider.failure_kinds == ("provider_down",)
    assert any("model answers" in phrase for phrase in provider.lost)
    lsp = judge_degradation({**FULL, "lsp": "down"})
    assert lsp.failure_kinds == ("lsp_down",)
    assert any("navigation" in phrase for phrase in lsp.lost)
    assert any("rename" in phrase for phrase in lsp.lost)
    network = judge_degradation({**FULL, "network": "down"})
    assert network.failure_kinds == ("network_down",)
    assert any("remote provider" in phrase for phrase in network.lost)


def test_judge_needs_key_is_provider_down_said_honestly():
    result = judge_degradation({**FULL, "provider": "needs-key"})
    assert result.failure_kinds == ("provider_down",)
    assert any("needs-key" in reason and "missing key" in reason for reason in result.reasons)


def test_judge_combination_in_roadmap_order():
    result = judge_degradation({"network": "down", "lsp": "down", "provider": "unreachable", "network_detail": "no route"})
    assert result.state == "degraded"
    assert result.failure_kinds == FAILURE_KINDS
    assert result.failures[-1].detail == "no route"
    assert len(result.lost) == len(set(result.lost))
    assert result.kept


def test_judge_unknown_never_invents():
    result = judge_degradation({})
    assert result.state == "unknown"
    assert result.unknowns == ("provider", "lsp", "network")
    assert result.failures == ()
    partial = judge_degradation({"provider": "reachable"})
    assert partial.state == "unknown"
    assert partial.unknowns == ("lsp", "network")
    mixed = judge_degradation({"provider": "unreachable"})
    assert mixed.state == "degraded"
    assert mixed.unknowns == ("lsp", "network")
    assert "unknown" in plain_words(judge_degradation({}))


def test_judge_one_failure_never_invents_another():
    result = judge_degradation({**FULL, "network": "down"})
    assert result.failure_kinds == ("network_down",)
    local = judge_degradation({"provider": "reachable", "lsp": "up", "network": "down"})
    assert "provider_down" not in local.failure_kinds


def test_judge_refusals():
    with pytest.raises(ValueError):
        judge_degradation({"provider": "reachable", "bogus": "up"})
    with pytest.raises(ValueError):
        judge_degradation({"provider": "reachable", "provider_status": "unreachable"})
    with pytest.raises(ValueError):
        judge_degradation({"provider": "flaky"})
    with pytest.raises(ValueError):
        judge_degradation("down")
    with pytest.raises(ValueError):
        judge_degradation({**FULL, "lsp_detail": 3, "lsp": "down"})


def test_assessment_self_consistency_refusals():
    with pytest.raises(ValueError):
        DegradationAssessment(state="full", failures=(DegradationFailure(kind="lsp_down"),))
    with pytest.raises(ValueError):
        DegradationAssessment(state="degraded")
    with pytest.raises(ValueError):
        DegradationAssessment(state="unknown")
    with pytest.raises(ValueError):
        DegradationAssessment(state="sideways")
    with pytest.raises(ValueError):
        DegradationAssessment(state="degraded", failures=(DegradationFailure(kind="lsp_down"), DegradationFailure(kind="lsp_down")))


# -- record, registry, surface ----------------------------------------


def test_degradation_record_is_session_news():
    result = judge_degradation({**FULL, "lsp": "down"})
    record = degradation_record(result)
    assert record["type"] == "degradation_change"
    assert record["session_event"] == "degradation_change"
    assert record["news"] is True
    assert record["slice"] == "M-115"
    assert record["failure_kinds"] == ["lsp_down"]
    assert record["lost"] == list(result.lost)
    assert "What it lost" in record["headline"]
    with pytest.raises(ValueError):
        degradation_record({"state": "degraded"})


def test_registry_deterministic_ids():
    registry = DegradationRegistry()
    first = registry.judge_and_register(FULL)
    second = registry.judge_and_register({**FULL, "lsp": "down"})
    assert (first.record_id, second.record_id) == ("grace-1", "grace-2")
    assert len(registry) == 2
    assert registry.get("grace-2").failure_kinds == ("lsp_down",)
    assert registry.record("grace-1")["state"] == "full"
    assert [item.record_id for item in registry.list_records()] == ["grace-1", "grace-2"]


def test_registry_supplied_id_skips_and_duplicates_refuse():
    registry = DegradationRegistry()
    held = registry.register(judge_degradation(FULL))
    assert held.record_id == "grace-1"
    custom = registry.register(DegradationAssessment(state="full", record_id="grace-2"))
    assert custom.record_id == "grace-2"
    nxt = registry.judge_and_register(FULL)
    assert nxt.record_id == "grace-3"
    with pytest.raises(ValueError):
        registry.register(DegradationAssessment(state="full", record_id="grace-2"))
    with pytest.raises(KeyError):
        registry.get("grace-99")
    with pytest.raises(ValueError):
        registry.register({"state": "full"})


def test_parser_grammar():
    assert parse_grace_args("") == ("show", None)
    assert parse_grace_args(None) == ("show", None)
    assert parse_grace_args("show") == ("show", None)
    assert parse_grace_args("failures") == ("failures", None)
    assert parse_grace_args("show grace-1") == ("show", "grace-1")
    assert parse_grace_args("grace-1") == ("show", "grace-1")
    for bad in ("show failures", "failures now", "show a b", "two words", 3):
        with pytest.raises(ValueError) as excinfo:
            parse_grace_args(bad)
        assert USAGE in str(excinfo.value)


def test_formatters_state_the_loss_in_words():
    assert "diagnostics" in format_failure("lsp_down")
    assert "lost:" in format_failure("provider_down")
    assert "still stands:" in format_failure("network_down")
    kinds = format_failures()
    assert "3 kinds" in kinds
    result = judge_degradation({**FULL, "provider": "unreachable"})
    text = format_assessment(result)
    assert "model answers" in text
    assert "lost:" in text
    with pytest.raises(ValueError):
        format_assessment({"state": "degraded"})


def test_screen_and_record_formatter():
    empty = format_grace_screen()
    assert "no records held" in empty
    assert USAGE in empty
    registry = DegradationRegistry()
    registry.judge_and_register({**FULL, "network": "down"})
    screen = format_grace_screen(registry)
    assert "1 held" in screen
    assert "network is down" in screen
    record = registry.record("grace-1")
    assert format_grace_record(record) == record["headline"]
    with pytest.raises(ValueError):
        format_grace_record({"type": "other"})
    with pytest.raises(ValueError):
        format_grace_screen(42)


def test_assessment_record_shape():
    result = judge_degradation({**FULL, "network": "down", "provider_detail": "unused"})
    record = result.to_record()
    assert record["type"] == "degradation_assessment"
    assert record["slice"] == "M-115"
    assert record["failure_kinds"] == ["network_down"]
    assert record["unknowns"] == []
