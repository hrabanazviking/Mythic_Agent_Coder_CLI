"""M-115 - Offline and degraded grace.

TIER: integration

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


# -- agent layer -----------------------------------------------------------
#
# The agent holds a DegradationRegistry for the
# session (session state only, no new setting):
# evidence is judged by the pure judge and every
# judged assessment - full, degraded or unknown -
# is published as degradation_change session news,
# deduped per record id. The honest boundary of
# this layer: it gathers no evidence itself and
# probes nothing - judging held evidence, in plain
# words, is the slice's agent work.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _grace_events(store, session_id):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == "degradation_change"]


def _held_records(agent):
    return agent._degradation_registry().list_records()


class TestGraceAgentStatus:
    def test_status_starts_empty(self, agent):
        status = agent.grace_status()
        assert status["records"] == []
        assert "no records held" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["screen"] == format_grace_screen(
            agent._degradation_registry())

    def test_registry_is_one_per_agent(self, agent):
        assert agent._degradation_registry() is agent._degradation_registry()
        # The M-108 lesson: the attribute never shares the method name.
        assert agent._degradation_store is agent._degradation_registry()

    def test_unknown_record_raises_keyerror(self, agent):
        with pytest.raises(KeyError):
            agent.get_grace_record("grace-99")


class TestGraceAgentJudging:
    def test_full_judged_held_and_published_once(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.judge_degradation(FULL)
        assert outcome["assessment"]["record_id"] == "grace-1"
        assert outcome["assessment"]["state"] == "full"
        assert outcome["record"]["type"] == "degradation_change"
        assert outcome["record"]["news"] is True
        assert outcome["record"]["state"] == "full"
        assert "nothing is lost" in outcome["record"]["headline"]
        events = _grace_events(store, session_id)
        assert len(events) == 1
        assert events[0]["record_id"] == "grace-1"
        agent._publish_degradation_record(outcome["record"])
        agent.grace_status()
        agent.get_grace_record("grace-1")
        assert len(_grace_events(store, session_id)) == 1
        assert agent.get_grace_record("grace-1").state == "full"

    def test_each_failure_kind_judged_and_published(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        provider = agent.judge_degradation({**FULL, "provider": "unreachable"})
        assert provider["assessment"]["failure_kinds"] == ["provider_down"]
        assert any("model answers" in phrase
                   for phrase in provider["record"]["lost"])
        lsp = agent.judge_degradation({**FULL, "lsp": "down"})
        assert lsp["assessment"]["failure_kinds"] == ["lsp_down"]
        assert any("navigation" in phrase for phrase in lsp["record"]["lost"])
        network = agent.judge_degradation({**FULL, "network": "down"})
        assert network["assessment"]["failure_kinds"] == ["network_down"]
        assert [item.record_id for item in _held_records(agent)] == [
            "grace-1", "grace-2", "grace-3"]
        assert len(_grace_events(store, session_id)) == 3

    def test_needs_key_judged_honestly(self, agent):
        outcome = agent.judge_degradation({**FULL, "provider": "needs-key"})
        assert outcome["assessment"]["failure_kinds"] == ["provider_down"]
        assert any("needs-key" in reason and "missing key" in reason
                   for reason in outcome["record"]["reasons"])

    def test_unknown_state_is_honest(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.judge_degradation({})
        assert outcome["assessment"]["state"] == "unknown"
        assert outcome["assessment"]["unknowns"] == ["provider", "lsp", "network"]
        assert outcome["record"]["failure_kinds"] == []
        assert "unknown" in outcome["record"]["headline"]
        assert "full -" not in outcome["record"]["headline"]
        assert len(_grace_events(store, session_id)) == 1

    def test_register_prebuilt_assessment_published(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_grace_assessment(
            judge_degradation({**FULL, "lsp": "down"}))
        assert outcome["assessment"]["record_id"] == "grace-1"
        assert outcome["record"]["type"] == "degradation_change"
        assert len(_grace_events(store, session_id)) == 1
        with pytest.raises(ValueError):
            agent.register_grace_assessment(DegradationAssessment(
                state="full", record_id="grace-1"))
        assert len(_held_records(agent)) == 1
        assert len(_grace_events(store, session_id)) == 1

    def test_bad_evidence_holds_and_publishes_nothing(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValueError):
            agent.judge_degradation({"provider": "flaky"})
        with pytest.raises(ValueError):
            agent.judge_degradation({"bogus": "up"})
        assert _held_records(agent) == ()
        assert _grace_events(store, session_id) == []

    def test_status_read_publishes_nothing(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.judge_degradation({**FULL, "network": "down"})
        assert len(_grace_events(store, session_id)) == 1
        agent.grace_status()
        agent.get_grace_record("grace-1")
        agent.grace_status()
        assert len(_grace_events(store, session_id)) == 1

    def test_judge_without_session_holds_quietly(self, agent):
        outcome = agent.judge_degradation({**FULL, "lsp": "down"})
        assert outcome["assessment"]["record_id"] == "grace-1"
        assert "1 held" in outcome["screen"]
        assert len(_held_records(agent)) == 1


class TestGraceTerminalSurface:
    def test_show_is_the_whole_slice(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/grace")
        assert text.startswith("Offline and degraded grace (M-115) - ")
        assert "no records held" in text
        assert USAGE in text

    def test_help_line_names_grace(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert "/grace [show|show <record>|failures]" in text

    def test_failures_via_the_terminal(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/grace failures")
        assert text.startswith("Degraded grace failures: 3 kinds.")
        assert "diagnostics" in text
        assert _held_records(agent) == ()

    def test_show_one_via_the_terminal(self, agent):
        from mythic_agent.terminal import _slash
        agent.judge_degradation({**FULL, "provider": "unreachable"})
        _, _, text = _slash(agent, "/grace show grace-1")
        assert text.startswith("grace-1: Degradation: degraded")
        assert "model answers" in text
        _, _, text = _slash(agent, "/grace grace-1")
        assert "lost:" in text

    def test_unknown_and_bad_grammar_via_the_terminal(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/grace show grace-99")
        assert "unknown degradation record" in text
        _, _, text = _slash(agent, "/grace failures now")
        assert text == USAGE
        _, _, text = _slash(agent, "/grace drop grace-1")
        assert text == USAGE


@pytest.fixture()
def grace_handler(agent, monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.agents.llm import AGENT_REGISTRY
    published = []
    monkeypatch.setattr(
        handler_module, "publish_sync",
        lambda event, **kwargs: published.append((event, kwargs)))
    AGENT_REGISTRY["Primary"] = agent
    instance = CommandHandler.__new__(CommandHandler)
    instance.published = published
    yield instance
    AGENT_REGISTRY.pop("Primary", None)


def _grace_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestGraceCommand:
    def test_show_is_default(self, grace_handler, agent):
        grace_handler._handle_grace("")
        assert "no records held" in _grace_published_text(grace_handler)

    def test_failures_via_the_handler(self, grace_handler, agent):
        grace_handler._handle_grace("failures")
        assert "Degraded grace failures: 3 kinds." in (
            _grace_published_text(grace_handler))
        assert _held_records(agent) == ()

    def test_show_one_via_the_handler(self, grace_handler, agent):
        agent.judge_degradation({**FULL, "network": "down"})
        grace_handler._handle_grace("show grace-1")
        assert "grace-1: Degradation: degraded" in (
            _grace_published_text(grace_handler))
        assert "remote provider" in _grace_published_text(grace_handler)

    def test_bad_grammar_and_unknown_are_published(
            self, grace_handler, agent):
        grace_handler._handle_grace("failures now")
        assert "Usage: /grace" in _grace_published_text(grace_handler)
        grace_handler._handle_grace("show grace-99")
        assert "unknown degradation record" in _grace_published_text(
            grace_handler)


class TestChatScreenRoutingGrace:
    def test_grace_routes_as_system_command(self, monkeypatch):
        from mythic_agent.ui.screens import chat_screen
        from mythic_agent.ui.screens.chat_screen import MainChatScreen

        class _FakeLog:
            def __init__(self):
                self.lines = []

            def write(self, *args, **kwargs):
                self.lines.append(" ".join(str(a) for a in args))

        calls = []
        monkeypatch.setattr(
            chat_screen.SecureAPI, "publish_system_command",
            staticmethod(lambda cmd, args: calls.append((cmd, args))))
        screen = MainChatScreen.__new__(MainChatScreen)
        screen.handle_command("/grace failures", _FakeLog())
        assert calls == [("/grace", "failures")]
