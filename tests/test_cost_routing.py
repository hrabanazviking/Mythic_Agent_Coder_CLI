"""M-031 — Cost-aware routing.

TIER: integration

Covers the M-031 surface:

* the pure layer (``mythic_agent.core.cost_routing``): the
  ``cost_routing`` setting is config data, off by default, a
  malformed stored value raises; the candidate pool is exactly
  the doors the user configured (current door, the M-030
  fallback chain, the M-029 role routes) and only doors the
  live session can speak (M-028's bound); adequacy is M-027
  capability truth (only known-true counts — unknown is never
  adequate where a capability is required); price is the
  ``mythic costs`` yardstick (an unpriced model is never
  cheaper; an unpriced current door defeats any proven saving;
  a tie keeps the current door); every decision carries its
  plain-words reason,
* ``Agent`` changes: ``set_cost_routing`` journaled as
  ``cost_routing_changed``, saved, a failed save restores the
  previous setting and journals the revert; ``cost_route``
  applies a preferred door through M-028's journaled switch
  with the decision's own reason, and applies nothing when the
  decision keeps the current door,
* the surfaces: the terminal ``/costroute`` and the TUI
  ``/costroute`` (system-command road through the CommandHandler
  + chat-screen routing), which share the parser and formatters,
* the config contract: ``cost_routing`` ships in the defaults
  (False) and is catalogued (M-009).
"""

from __future__ import annotations

import copy

import pytest

from mythic_agent.core.cost_routing import (
    PLAIN_EXPLANATION,
    TASK_CLASS_IDS,
    candidate_doors,
    choose_route,
    door_adequate,
    enabled_from_config,
    format_cost_change,
    format_cost_routing,
    format_decision,
    get_task_class,
    parse_cost_args,
    set_enabled,
    unit_cost,
)
from mythic_agent.core.model_capabilities import load_capabilities
from mythic_agent.core.sessions import SessionStore

OPENAI = "https://api.openai.com/v1"
DEEPSEEK = "https://api.deepseek.com/v1"
OLLAMA = "http://localhost:11434"


def config_with(current=("gpt-4o", OPENAI), chain=(), routes=None,
                enabled=True):
    config = {"model": current[0], "base_url": current[1],
              "fallback_chain": [{"model": m, "base_url": u}
                                 for m, u in chain],
              "role_routes": routes or {}}
    if enabled is not None:
        config["cost_routing"] = enabled
    return config


def store_for(tmp_path, workspace=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state")


RICH = config_with(chain=[("gpt-4o-mini", OPENAI),
                          ("deepseek-chat", DEEPSEEK)])


# ----------------------------------------------------------------------
# The setting, as data
# ----------------------------------------------------------------------

class TestSetting:
    def test_absent_means_off(self):
        assert enabled_from_config({}) is False

    def test_stored_bool_reads_back(self):
        assert enabled_from_config({"cost_routing": True}) is True
        assert enabled_from_config({"cost_routing": False}) is False

    def test_malformed_stored_setting_raises(self):
        with pytest.raises(ValueError, match="must be true or false"):
            enabled_from_config({"cost_routing": "yes"})

    def test_set_enabled_is_pure_and_records_the_change(self):
        config = {"cost_routing": False}
        value, change = set_enabled(config, True)
        assert value is True
        assert config == {"cost_routing": False}
        assert change.event() == {"type": "cost_routing_changed",
                                  "from": False, "to": True}
        assert change.record("s" * 32, True)["to"] is True

    def test_set_enabled_refuses_no_change_and_non_bool(self):
        with pytest.raises(ValueError, match="already off"):
            set_enabled({"cost_routing": False}, False)
        with pytest.raises(ValueError, match="must be true or false"):
            set_enabled({}, 1)


# ----------------------------------------------------------------------
# Task classes, prices, adequacy
# ----------------------------------------------------------------------

class TestTruthSources:
    def test_task_classes_are_the_five_named(self):
        assert TASK_CLASS_IDS == ("general", "coding", "reasoning",
                                  "vision", "long_context")

    def test_unknown_task_class_raises_with_the_list(self):
        with pytest.raises(ValueError, match="Unknown task class"):
            get_task_class("telepathy")

    def test_unit_cost_comes_from_the_costs_table(self):
        assert unit_cost("gpt-4o") == pytest.approx(12.50)
        assert unit_cost("deepseek-chat") == pytest.approx(0.42)
        assert unit_cost("gpt-4o-mini") == pytest.approx(0.75)

    def test_unpriced_model_has_no_cost(self):
        assert unit_cost("test-model") is None
        assert unit_cost("no-such-model") is None

    def test_adequacy_only_counts_known_truth(self):
        caps = load_capabilities()
        coding = get_task_class("coding")
        vision = get_task_class("vision")
        reasoning = get_task_class("reasoning")
        long_context = get_task_class("long_context")
        general = get_task_class("general")
        assert door_adequate(caps.for_model("deepseek-chat"), coding)
        assert not door_adequate(caps.for_model("deepseek-chat"), vision)
        # reasoning is unknown (null) for gpt-4o: NOT adequate.
        assert not door_adequate(caps.for_model("gpt-4o"), reasoning)
        assert door_adequate(caps.for_model("deepseek-reasoner"), reasoning)
        # deepseek-reasoner is known NOT to call tools.
        assert not door_adequate(caps.for_model("deepseek-reasoner"), coding)
        assert door_adequate(caps.for_model("gemini-1.5-flash"), long_context)
        assert not door_adequate(caps.for_model("gpt-4o"), long_context)
        # An unlisted model is all-unknown: adequate only for general.
        assert door_adequate(caps.for_model("no-such-model"), general)
        assert not door_adequate(caps.for_model("no-such-model"), coding)


# ----------------------------------------------------------------------
# The candidate pool
# ----------------------------------------------------------------------

class TestCandidates:
    def test_pool_is_current_then_chain_then_routes_deduped(self):
        config = config_with(
            chain=[("gpt-4o-mini", OPENAI), ("gpt-4o", OPENAI)],
            routes={"cartographer": {"model": "deepseek-chat",
                                     "base_url": DEEPSEEK},
                    "scribe": {"model": "gpt-4o-mini",
                               "base_url": OPENAI}})
        doors = candidate_doors(config)
        assert [(d.model, d.source) for d in doors] == [
            ("gpt-4o", "current door"),
            ("gpt-4o-mini", "fallback chain"),
            ("deepseek-chat", "route for cartographer"),
        ]
        assert doors[0].provider == "openai"
        assert doors[2].provider == "deepseek"

    def test_provider_is_inferred_never_stored(self):
        doors = candidate_doors(config_with(
            chain=[("qwen3-8b", "http://localhost:9999/v1")]))
        assert doors[1].provider is None
        assert doors[1].selection()["provider"] is None

    def test_malformed_chain_surfaces(self):
        config = config_with()
        config["fallback_chain"] = [{"model": "x"}]
        with pytest.raises(ValueError, match="no door URL"):
            candidate_doors(config)


# ----------------------------------------------------------------------
# The decision
# ----------------------------------------------------------------------

class TestChooseRoute:
    def test_off_keeps_current_and_explains_in_plain_words(self):
        decision = choose_route(config_with(enabled=False), "coding")
        assert decision.changed is False
        assert decision.chosen.model == "gpt-4o"
        assert "off" in decision.reason
        assert PLAIN_EXPLANATION.split(":")[0] in decision.reason

    def test_cheapest_adequate_wins_for_coding(self):
        decision = choose_route(RICH, "coding")
        assert decision.changed is True
        assert decision.chosen.model == "deepseek-chat"
        assert decision.chosen_cost == pytest.approx(0.42)
        assert decision.current_cost == pytest.approx(12.50)
        assert "cheaper" in decision.reason

    def test_vision_skips_a_model_known_not_to_see(self):
        decision = choose_route(RICH, "vision")
        assert decision.changed is True
        assert decision.chosen.model == "gpt-4o-mini"

    def test_reasoning_with_no_known_reasoner_keeps_current(self):
        decision = choose_route(RICH, "reasoning")
        assert decision.changed is False
        assert "no cheaper adequate door can be proven" in decision.reason

    def test_reasoning_routes_to_a_known_reasoner(self):
        config = config_with(chain=[("deepseek-reasoner", DEEPSEEK)])
        decision = choose_route(config, "reasoning")
        assert decision.changed is True
        assert decision.chosen.model == "deepseek-reasoner"
        assert "not known to be adequate" in decision.reason

    def test_long_context_needs_a_known_large_context(self):
        decision = choose_route(RICH, "long_context")
        assert decision.changed is False

    def test_current_already_cheapest_adequate_stays(self):
        config = config_with(current=("deepseek-chat", DEEPSEEK),
                             chain=[("gpt-4o-mini", OPENAI)])
        decision = choose_route(config, "coding")
        assert decision.changed is False
        assert "already the cheapest adequate door" in decision.reason

    def test_unpriced_current_defeats_a_proven_saving(self):
        # For general work the unpriced current door IS adequate
        # (no capability is required), so the only question is
        # price — and with its price unknown, no saving over it
        # can be proven.
        config = config_with(current=("test-model", "http://localhost:1/v1"),
                             chain=[("deepseek-chat", DEEPSEEK)])
        decision = choose_route(config, "general")
        assert decision.changed is False
        assert "price is not in the costs data" in decision.reason

    def test_unpriced_and_inadequate_current_yields_to_adequacy(self):
        # For coding work the same unpriced current door is not
        # known to be adequate at all, so adequacy alone routes.
        config = config_with(current=("test-model", "http://localhost:1/v1"),
                             chain=[("deepseek-chat", DEEPSEEK)])
        decision = choose_route(config, "coding")
        assert decision.changed is True
        assert decision.chosen.model == "deepseek-chat"
        assert "not known to be adequate" in decision.reason

    def test_unpriced_candidate_is_never_preferred(self):
        config = config_with(chain=[("mystery-model", "http://localhost:9/v1")])
        decision = choose_route(config, "general")
        assert decision.changed is False
        assert decision.chosen.model == "gpt-4o"

    def test_native_dialect_door_is_not_a_candidate(self):
        # gpt-4o-mini is priced and vision-adequate, but the Ollama
        # door speaks a dialect the live session cannot (M-028).
        config = config_with(chain=[("gpt-4o-mini", OLLAMA)])
        decision = choose_route(config, "vision")
        assert decision.changed is False
        assert decision.chosen.model == "gpt-4o"

    def test_route_doors_are_candidates(self):
        config = config_with(routes={
            "cartographer": {"model": "deepseek-chat",
                             "base_url": DEEPSEEK}})
        decision = choose_route(config, "general")
        assert decision.changed is True
        assert decision.chosen.model == "deepseek-chat"
        assert decision.chosen.source == "route for cartographer"

    def test_no_configured_door_raises(self):
        with pytest.raises(ValueError, match="No door is configured"):
            choose_route({"cost_routing": True}, "general")

    def test_decision_record_round_trips_the_facts(self):
        record = choose_route(RICH, "coding").record()
        assert record["task_class"] == "coding"
        assert record["changed"] is True
        assert record["chosen"]["model"] == "deepseek-chat"
        assert record["current"]["provider"] == "openai"


# ----------------------------------------------------------------------
# The /costroute grammar + formatters
# ----------------------------------------------------------------------

class TestParseAndFormat:
    @pytest.mark.parametrize("text,action", [
        ("", "show"), ("show", "show"), ("on", "setting"),
        ("off", "setting"), ("coding", "decide"),
        ("VISION", "decide"),
    ])
    def test_parse_actions(self, text, action):
        assert parse_cost_args(text)["action"] == action

    def test_parse_rejects_extra_words_and_unknown_classes(self):
        with pytest.raises(ValueError, match="Usage"):
            parse_cost_args("on please")
        with pytest.raises(ValueError, match="Unknown task class"):
            parse_cost_args("telepathy")
        with pytest.raises(ValueError, match="must be text"):
            parse_cost_args(7)

    def test_format_cost_routing_shows_state_doors_classes(self):
        text = format_cost_routing(RICH)
        assert "Cost-aware routing: ON" in text
        assert PLAIN_EXPLANATION in text
        assert "gpt-4o-mini via openai" in text
        assert "$0.42 on the costs yardstick" in text
        assert "long_context" in text
        off = format_cost_routing(config_with(enabled=False))
        assert "OFF (the default)" in off

    def test_format_decision_names_the_outcome_and_reason(self):
        text = format_decision(choose_route(RICH, "coding"))
        assert "switch to deepseek-chat via deepseek" in text
        assert "cheaper" in text
        stayed = format_decision(choose_route(RICH, "reasoning"))
        assert "stay on gpt-4o via openai" in stayed

    def test_format_cost_change_sentences(self):
        _, change = set_enabled({"cost_routing": False}, True)
        assert "now ON" in format_cost_change(change.record("s" * 32, True))
        _, change = set_enabled({"cost_routing": True}, False)
        assert "now OFF" in format_cost_change(change.record(None, False))


# ----------------------------------------------------------------------
# Agent setting changes + applied routing
# ----------------------------------------------------------------------

class TestAgentCostRouting:
    def test_status_defaults_off_with_the_fixture_door(self, agent):
        status = agent.cost_routing_status()
        assert status["enabled"] is False
        assert status["doors"][0]["model"] == "test-model"
        assert status["doors"][0]["unit_cost"] is None
        assert [t["id"] for t in status["task_classes"]] == list(TASK_CLASS_IDS)

    def test_set_without_session(self, agent):
        record = agent.set_cost_routing(True)
        assert record["journaled"] is False
        assert agent.config["cost_routing"] is True
        with pytest.raises(ValueError, match="already on"):
            agent.set_cost_routing(True)

    def test_set_journals_on_the_session(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.set_cost_routing(True)
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "cost_routing_changed" in types
        agent.close()

    def test_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.set_cost_routing(True)
        assert agent.config.get("cost_routing") is not True
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["cost_routing_changed",
                              "cost_routing_reverted"]
        agent.close()

    def _rich_agent(self, agent):
        agent.config.update({
            "model": "gpt-4o", "base_url": OPENAI, "cost_routing": True,
            "fallback_chain": [{"model": "deepseek-chat",
                                "base_url": DEEPSEEK}],
            "role_routes": {}})
        return agent

    def test_cost_route_applies_the_switch_with_its_reason(
            self, agent, tmp_path):
        agent = self._rich_agent(agent)
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.cost_route("coding")
        assert record["applied"] is True
        assert record["chosen"]["model"] == "deepseek-chat"
        assert agent.config["model"] == "deepseek-chat"
        assert agent.config["base_url"] == DEEPSEEK
        switches = [e for e in store.export(session_id)["events"]
                    if e["type"] == "model_switched"]
        assert len(switches) == 1
        assert "cheaper" in switches[0]["reason"]
        agent.close()

    def test_cost_route_keeps_current_and_journals_no_switch(
            self, agent, tmp_path):
        agent = self._rich_agent(agent)
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.cost_route("reasoning")
        assert record["applied"] is False
        assert record["switch"] is None
        assert agent.config["model"] == "gpt-4o"
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "model_switched" not in types
        agent.close()

    def test_cost_route_off_applies_nothing(self, agent):
        agent = self._rich_agent(agent)
        agent.config["cost_routing"] = False
        record = agent.cost_route("coding")
        assert record["applied"] is False
        assert agent.config["model"] == "gpt-4o"


# ----------------------------------------------------------------------
# Surfaces
# ----------------------------------------------------------------------

class TestTerminalSurface:
    def test_show_on_and_decide(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/costroute")
        assert "OFF (the default)" in text
        _, _, text = _slash(agent, "/costroute on")
        assert "now ON" in text
        agent.config.update({
            "model": "gpt-4o", "base_url": OPENAI,
            "fallback_chain": [{"model": "deepseek-chat",
                                "base_url": DEEPSEEK}],
            "role_routes": {}})
        _, _, text = _slash(agent, "/costroute coding")
        assert "switch to deepseek-chat" in text
        assert agent.config["model"] == "deepseek-chat"

    def test_usage_error_is_the_message(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/costroute telepathy")
        assert "Unknown task class" in text


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


class TestCostRouteCommand:
    def test_show_is_default(self, handler, agent):
        handler._handle_costroute("")
        assert "OFF (the default)" in _published_text(handler)

    def test_on_and_decide_via_the_handler(self, handler, agent):
        handler._handle_costroute("on")
        assert "now ON" in _published_text(handler)
        agent.config.update({
            "model": "gpt-4o", "base_url": OPENAI,
            "fallback_chain": [{"model": "deepseek-chat",
                                "base_url": DEEPSEEK}],
            "role_routes": {}})
        handler._handle_costroute("coding")
        assert "switch to deepseek-chat" in _published_text(handler)
        assert agent.config["model"] == "deepseek-chat"

    def test_usage_error_is_published(self, handler, agent):
        handler._handle_costroute("bogus-class")
        assert "Unknown task class" in _published_text(handler)


class TestChatScreenRouting:
    def test_costroute_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/costroute on", _FakeLog())
        assert calls == [("/costroute", "on")]


# ----------------------------------------------------------------------
# The config contract
# ----------------------------------------------------------------------

class TestConfigContract:
    def test_defaults_ship_the_setting_off(self):
        from mythic_agent.core import config_manager

        assert config_manager.CONFIG_SCHEMA["cost_routing"]["type"] is bool
        assert config_manager.CONFIG_SCHEMA["cost_routing"]["default"] is False

    def test_catalogue_carries_the_setting(self):
        from mythic_agent.core.config_catalog import load_catalog

        by_name = {s.name: s for s in load_catalog().settings}
        assert by_name["cost_routing"].id == "S-39"
        assert by_name["cost_routing"].type == "bool"
