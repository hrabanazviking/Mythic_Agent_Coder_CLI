"""M-037 — Vision input routing.

TIER: integration

Covers the M-037 surface:

* the pure layer (``mythic_agent.core.vision_routing``): image
  parts are counted with the same definition the elder vision
  negotiation uses; the gate is M-027 capability truth — only
  a model whose ``vision`` record is known-true may receive
  image work, known-false and unknown (including unlisted)
  refuse plainly naming the model and its record, and text
  work is never gated; the offered switch is a configured
  door (the M-031 candidate pool) the live session can speak
  (M-028's bound) whose model is known to see — a native door
  is never offered; with no qualifying door the refusal names
  known-seeing models from the capability data instead,
* the wiring into ``providers.vision.normalize``: a named
  model that is not known to see is refused before family
  shaping on the raise road, while the explicit strip
  downgrade keeps its counted-drop behaviour and an unnamed
  provider keeps the elder negotiation's behaviour,
* ``Agent`` changes: ``vision_status`` tells the truth about
  the current model; ``gate_image_parts`` journals a refusal
  as ``vision_refused`` and raises plainly; the offered
  switch is applied through M-028's journaled
  ``switch_model``,
* the surfaces: the terminal ``/vision`` and the TUI
  ``/vision`` (system-command road through the CommandHandler
  + chat-screen routing), which share the parser and
  formatters.
"""

from __future__ import annotations

import base64

import pytest

from mythic_agent.core.model_capabilities import load_capabilities
from mythic_agent.core.sessions import SessionStore
from mythic_agent.core.vision_routing import (
    PLAIN_EXPLANATION,
    VISION_SLICE,
    count_image_parts,
    format_vision_decision,
    format_vision_status,
    gate_for_model,
    known_seeing_models,
    parse_vision_args,
    route_images,
    suggest_switch,
)
from mythic_agent.providers import vision as vision_module
from mythic_agent.providers.base import Provider, ProviderError

OPENAI = "https://api.openai.com/v1"
DEEPSEEK = "https://api.deepseek.com/v1"
OLLAMA = "http://localhost:11434"
CUSTOM = "http://localhost:9999/v1"

_TINY_B64 = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64).decode()
_DATA_URL = f"data:image/png;base64,{_TINY_B64}"


def image_part():
    return {"type": "image_url", "image_url": {"url": _DATA_URL}}


def parts_with_images(count=1):
    return [{"type": "text", "text": "Describe this."}] + [
        image_part() for _ in range(count)]


def config_with(current=("deepseek-chat", DEEPSEEK), chain=(), routes=None):
    return {"model": current[0], "base_url": current[1],
            "fallback_chain": [{"model": m, "base_url": u}
                               for m, u in chain],
            "role_routes": routes or {}}


def store_for(tmp_path, workspace=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state")


# ----------------------------------------------------------------------
# Counting — the gate and the negotiation agree on what an image is
# ----------------------------------------------------------------------

class TestCounting:
    def test_slice_and_explanation(self):
        assert VISION_SLICE == "M-037"
        assert "only" in PLAIN_EXPLANATION
        assert "known" in PLAIN_EXPLANATION

    def test_counts_both_image_part_types(self):
        parts = [{"type": "text", "text": "x"}, image_part(),
                 {"type": "image_bytes", "mime_type": "image/png",
                  "data": _TINY_B64},
                 {"type": "tool_result", "text": "y"}]
        assert count_image_parts(parts) == 2

    def test_count_agrees_with_the_negotiations_has_images(self):
        for parts in ([], [{"type": "text", "text": "x"}],
                      parts_with_images(2)):
            assert (count_image_parts(parts) > 0) is \
                vision_module.has_images(parts)

    def test_non_list_parts_raise(self):
        with pytest.raises(ValueError, match="must be a list"):
            count_image_parts("not-a-list")
        with pytest.raises(ValueError, match="must be a list"):
            count_image_parts(None)


# ----------------------------------------------------------------------
# The gate — M-027 truth governs
# ----------------------------------------------------------------------

class TestGate:
    def test_no_images_never_gated(self):
        for model in ("deepseek-chat", "gpt-4o", "unlisted-model"):
            decision = gate_for_model(model, 0)
            assert decision.allowed is True
            assert decision.image_count == 0

    def test_known_seeing_model_allows(self):
        decision = gate_for_model("gpt-4o", 2)
        assert decision.allowed is True
        assert decision.vision is True
        assert "gpt-4o" in decision.reason
        assert "known to see" in decision.reason

    def test_known_blind_model_refuses_naming_the_record(self):
        decision = gate_for_model("deepseek-chat", 1)
        assert decision.allowed is False
        assert decision.vision is False
        assert "deepseek-chat" in decision.reason
        assert "cannot see" in decision.reason
        assert "not dropped silently" in decision.reason

    def test_unknown_sight_refuses_and_says_unknown(self):
        decision = gate_for_model("grok-4", 1)
        assert decision.allowed is False
        assert decision.vision is None
        assert "unknown" in decision.reason

    def test_unlisted_model_is_unknown_never_guessed(self):
        decision = gate_for_model("no-such-model", 3)
        assert decision.allowed is False
        assert decision.vision is None
        assert decision.image_count == 3

    def test_no_model_selected_refuses_images(self):
        for model in ("", None, 7):
            decision = gate_for_model(model, 1)
            assert decision.allowed is False
            assert "no model is selected" in decision.reason

    def test_known_seeing_models_come_from_the_data(self):
        seeing = known_seeing_models()
        assert "gpt-4o" in seeing
        assert "claude-sonnet-4-5" in seeing
        assert "deepseek-chat" not in seeing
        assert "llama3.1" not in seeing
        caps = load_capabilities()
        assert seeing == tuple(
            r.model for r in caps.records if r.vision is True)


# ----------------------------------------------------------------------
# The offered switch — configured, speakable, known to see
# ----------------------------------------------------------------------

class TestSuggestion:
    def test_chain_door_known_to_see_is_offered(self):
        config = config_with(chain=[("gpt-4o", OPENAI)])
        suggestion = suggest_switch(config)
        assert suggestion is not None
        assert suggestion.model == "gpt-4o"
        assert suggestion.source == "fallback chain"

    def test_native_door_is_never_offered(self):
        # The Ollama door is the registry's native-dialect door
        # with an endpoint: even a known-seeing model behind it
        # is not offered, because the live session cannot speak
        # that dialect (M-028's bound).
        config = config_with(chain=[("gpt-4o", OLLAMA)])
        assert suggest_switch(config) is None

    def test_native_door_skipped_for_a_speakable_seeing_door(self):
        config = config_with(chain=[("gpt-4o", OLLAMA),
                                    ("gpt-4o-mini", CUSTOM)])
        suggestion = suggest_switch(config)
        assert suggestion is not None
        assert suggestion.model == "gpt-4o-mini"
        assert suggestion.base_url == CUSTOM

    def test_blind_chain_doors_do_not_qualify(self):
        config = config_with(chain=[("llama3.1", "http://localhost:11434")])
        assert suggest_switch(config) is None

    def test_current_door_never_suggests_itself(self):
        config = config_with(current=("gpt-4o", OPENAI))
        assert suggest_switch(config) is None

    def test_role_route_door_can_be_offered(self):
        config = config_with(routes={
            "cartographer": {"model": "gpt-4o-mini", "base_url": OPENAI}})
        suggestion = suggest_switch(config)
        assert suggestion is not None
        assert suggestion.model == "gpt-4o-mini"


class TestRouteImages:
    def test_allowed_on_a_seeing_current_door(self):
        decision = route_images(config_with(current=("gpt-4o", OPENAI)),
                                parts_with_images())
        assert decision.allowed is True
        assert decision.suggestion is None

    def test_text_only_allowed_on_a_blind_door(self):
        decision = route_images(config_with(),
                                [{"type": "text", "text": "hello"}])
        assert decision.allowed is True

    def test_refusal_offers_the_configured_switch(self):
        decision = route_images(
            config_with(chain=[("gpt-4o", OPENAI)]), parts_with_images())
        assert decision.allowed is False
        assert decision.suggestion is not None
        assert decision.suggestion.model == "gpt-4o"
        assert "Switch offered" in decision.reason
        assert "/vision switch" in decision.reason
        record = decision.record()
        assert record["suggestion"]["model"] == "gpt-4o"
        assert record["vision"] is False

    def test_refusal_without_a_door_names_seeing_models(self):
        decision = route_images(config_with(), parts_with_images())
        assert decision.allowed is False
        assert decision.suggestion is None
        assert "No door you have set up is known to see" in decision.reason
        assert known_seeing_models()[0] in decision.reason


# ----------------------------------------------------------------------
# The wiring into the elder negotiation
# ----------------------------------------------------------------------

def _make_provider(name, model, vision_capable):
    flags = {"streaming": True, "tool_calling": False,
             "vision": vision_capable, "json_mode": False}

    def capabilities(self):
        return dict(flags)

    def chat(self, messages, **kwargs):
        raise ProviderError("fake: chat not implemented")

    return type(f"_Provider_{name}", (Provider,), {
        "name": name,
        "default_model": model,
        "capabilities": capabilities,
        "chat": chat,
    })()


class TestNormalizeWiring:
    def test_blind_model_refused_before_family_shaping(self):
        provider = _make_provider("openai", "deepseek-chat", True)
        with pytest.raises(ProviderError, match="cannot see"):
            vision_module.normalize(provider, parts_with_images())

    def test_unknown_model_refused_even_on_a_vision_family(self):
        provider = _make_provider("openai", "grok-4", True)
        with pytest.raises(ProviderError, match="unknown"):
            vision_module.normalize(provider, parts_with_images())

    def test_seeing_model_normalizes_as_before(self):
        provider = _make_provider("openai", "gpt-4o", True)
        payload = vision_module.normalize(provider, parts_with_images())
        assert payload.dropped == 0
        assert payload.content[1]["type"] == "image_url"

    def test_strip_downgrade_keeps_its_counted_behaviour(self):
        provider = _make_provider("openai", "deepseek-chat", False)
        payload = vision_module.normalize(
            provider, parts_with_images(), on_unsupported="strip")
        assert payload.dropped == 1
        assert all(p.get("type") == "text" for p in payload.content)

    def test_unnamed_provider_keeps_the_elder_behaviour(self):
        provider = _make_provider("openai", "", True)
        payload = vision_module.normalize(provider, parts_with_images())
        assert payload.dropped == 0

    def test_text_only_parts_are_never_gated(self):
        provider = _make_provider("openai", "deepseek-chat", True)
        payload = vision_module.normalize(
            provider, [{"type": "text", "text": "hello"}])
        assert payload.content == [{"type": "text", "text": "hello"}]


# ----------------------------------------------------------------------
# Grammar + formatters
# ----------------------------------------------------------------------

class TestSurfacesPure:
    @pytest.mark.parametrize("text,action", [
        ("", "show"), (None, "show"), ("show", "show"),
        ("STATUS", "show"), ("switch", "switch"), (" Switch ", "switch"),
    ])
    def test_parse_actions(self, text, action):
        assert parse_vision_args(text)["action"] == action

    def test_parse_rejects_garbage(self):
        with pytest.raises(ValueError, match="Usage: /vision"):
            parse_vision_args("peek")
        with pytest.raises(ValueError, match="must be text"):
            parse_vision_args(7)

    def test_format_decision_sentences(self):
        allowed = format_vision_decision(gate_for_model("gpt-4o", 1))
        assert "may go to gpt-4o" in allowed
        refused = format_vision_decision(gate_for_model("deepseek-chat", 1))
        assert "were NOT sent" in refused
        assert "cannot see" in refused

    def test_format_status_names_truth_doors_and_offer(self):
        status = {
            "model": "deepseek-chat", "vision": False,
            "seeing_doors": [{"model": "gpt-4o", "provider": "openai",
                              "base_url": OPENAI,
                              "source": "fallback chain"}],
            "suggestion": {"model": "gpt-4o", "base_url": OPENAI},
        }
        text = format_vision_status(status)
        assert "recorded as not able to see" in text
        assert PLAIN_EXPLANATION in text
        assert "gpt-4o via openai" in text
        assert "/vision switch" in text


# ----------------------------------------------------------------------
# Agent behaviour
# ----------------------------------------------------------------------

class TestAgentVision:
    def _rich_agent(self, agent):
        agent.config.update({
            "model": "deepseek-chat", "base_url": DEEPSEEK,
            "fallback_chain": [{"model": "gpt-4o", "base_url": OPENAI}],
            "role_routes": {}})
        return agent

    def test_status_tells_the_unknown_truth_by_default(self, agent):
        status = agent.vision_status()
        assert status["model"] == "test-model"
        assert status["vision"] is None
        assert status["seeing_doors"] == []
        assert status["suggestion"] is None
        assert status["plain_explanation"] == PLAIN_EXPLANATION

    def test_status_with_a_seeing_chain_door(self, agent):
        agent = self._rich_agent(agent)
        status = agent.vision_status()
        assert status["vision"] is False
        assert [d["model"] for d in status["seeing_doors"]] == ["gpt-4o"]
        assert status["suggestion"]["model"] == "gpt-4o"

    def test_gate_allows_a_seeing_model(self, agent):
        agent.config.update({"model": "gpt-4o", "base_url": OPENAI})
        decision = agent.gate_image_parts(parts_with_images())
        assert decision.allowed is True

    def test_gate_allows_text_on_a_blind_model(self, agent):
        agent = self._rich_agent(agent)
        decision = agent.gate_image_parts([{"type": "text", "text": "hi"}])
        assert decision.allowed is True

    def test_gate_refuses_and_journals_the_refusal(self, agent, tmp_path):
        agent = self._rich_agent(agent)
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        with pytest.raises(RuntimeError, match="cannot see"):
            agent.gate_image_parts(parts_with_images())
        events = [e for e in store.export(session_id)["events"]
                  if e["type"] == "vision_refused"]
        assert len(events) == 1
        assert events[0]["model"] == "deepseek-chat"
        assert events[0]["vision"] is False
        assert events[0]["suggestion"]["model"] == "gpt-4o"
        assert agent.config["model"] == "deepseek-chat"
        agent.close()

    def test_apply_switch_takes_the_offered_door(self, agent, tmp_path):
        agent = self._rich_agent(agent)
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.apply_vision_switch()
        assert record["to"]["model"] == "gpt-4o"
        assert agent.config["model"] == "gpt-4o"
        assert agent.config["base_url"] == OPENAI
        switches = [e for e in store.export(session_id)["events"]
                    if e["type"] == "model_switched"]
        assert len(switches) == 1
        assert "Vision input routing" in switches[0]["reason"]
        agent.close()

    def test_apply_switch_refuses_when_already_seeing(self, agent):
        agent.config.update({"model": "gpt-4o", "base_url": OPENAI})
        with pytest.raises(RuntimeError, match="already known to see"):
            agent.apply_vision_switch()
        assert agent.config["model"] == "gpt-4o"

    def test_request_path_gates_image_parts_in_the_history(self, agent):
        from unittest.mock import Mock

        agent = self._rich_agent(agent)
        agent._append_message(
            {"role": "user", "content": parts_with_images()})
        agent.get_client = Mock(
            side_effect=AssertionError("client must not be built"))
        with pytest.raises(RuntimeError, match="cannot see"):
            agent._request_with_fallback({})
        agent.get_client.assert_not_called()

    def test_request_path_passes_text_and_seeing_histories(self, agent):
        from unittest.mock import Mock

        agent.config.update({"model": "gpt-4o", "base_url": OPENAI})
        agent._append_message(
            {"role": "user", "content": parts_with_images()})
        agent.get_client = Mock(
            side_effect=AssertionError("client built — gate passed"))
        with pytest.raises(AssertionError, match="gate passed"):
            agent._request_with_fallback({})

    def test_apply_switch_refuses_without_a_qualifying_door(self, agent):
        agent = self._rich_agent(agent)
        agent.config["fallback_chain"] = []
        with pytest.raises(RuntimeError, match="No door you have set up"):
            agent.apply_vision_switch()
        assert agent.config["model"] == "deepseek-chat"


# ----------------------------------------------------------------------
# Surfaces — terminal + TUI command road
# ----------------------------------------------------------------------

class TestTerminalSurface:
    def test_show_reports_unknown_sight(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/vision")
        assert "sight unknown" in text
        assert PLAIN_EXPLANATION in text

    def test_show_offers_the_switch(self, agent):
        agent.config.update({
            "model": "deepseek-chat", "base_url": DEEPSEEK,
            "fallback_chain": [{"model": "gpt-4o", "base_url": OPENAI}],
            "role_routes": {}})
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/vision show")
        assert "recorded as not able to see" in text
        assert "Switch offered: gpt-4o" in text

    def test_switch_through_the_terminal(self, agent):
        agent.config.update({
            "model": "deepseek-chat", "base_url": DEEPSEEK,
            "fallback_chain": [{"model": "gpt-4o", "base_url": OPENAI}],
            "role_routes": {}})
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/vision switch")
        assert "gpt-4o" in text
        assert agent.config["model"] == "gpt-4o"

    def test_usage_error(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/vision bogus")
        assert "Usage: /vision" in text


@pytest.fixture()
def handler(agent, monkeypatch):
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


def _published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestVisionCommand:
    def test_show_reports_unknown_sight(self, handler):
        handler._handle_vision("")
        text = _published_text(handler)
        assert "sight unknown" in text
        assert PLAIN_EXPLANATION in text

    def test_usage_error_is_published(self, handler):
        handler._handle_vision("bogus")
        assert "Usage: /vision" in _published_text(handler)


class TestChatScreenRouting:
    def test_vision_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/vision show", _FakeLog())
        assert calls == [("/vision", "show")]
