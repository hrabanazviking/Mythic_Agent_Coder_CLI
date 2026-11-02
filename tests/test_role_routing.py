"""M-029 — Role routing.

TIER: integration

Covers the M-029 surface:

* the offices (``mythic_agent.core.role_routing``): the crew's real
  offices, taken from the shipped sub-agent definitions — every
  ``DEFAULT_SUBAGENTS`` name maps to exactly one office, and every
  office but Primary is held by at least one shipped sub-agent,
* the pure resolver: an office with no route truthfully resolves to
  the session default (source shown, never hidden); an explicit
  route is validated through the M-028 switch resolver (provider
  names take the registry endpoint + default model, native doors
  refused plainly, the Primary office refused — its selection IS
  the session default); malformed stored routes raise, never
  vanish; a route's provider is inferred from its door, never
  stored,
* ``Agent.set_role_route`` / ``clear_role_route``: journaled as a
  ``role_route_changed`` session event, saved to config, a failed
  save restores the previous routes exactly and journals the
  revert; routes apply to a crew member at spawn and to live idle
  members at once, never to a busy member mid-turn,
* the surfaces: the terminal ``/route`` and the TUI ``/route``
  (system-command road through the CommandHandler + chat-screen
  routing), which share the parser and the formatters,
* the config contract: ``role_routes`` ships in the defaults and
  is catalogued (M-009).
"""

from __future__ import annotations

import copy

import pytest

from mythic_agent.core.role_routing import (
    OFFICES,
    clear_route,
    effective_routes,
    format_route_change,
    format_routes,
    get_office,
    office_for_agent_name,
    office_ids,
    parse_route_args,
    resolve_route,
    routes_from_config,
    set_route,
)
from mythic_agent.core.sessions import SessionStore

CONFIG = {"model": "deepseek-chat", "base_url": "https://api.deepseek.com/v1"}


def store_for(tmp_path, workspace=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state")


# ----------------------------------------------------------------------
# The offices
# ----------------------------------------------------------------------

class TestOffices:
    def test_office_ids_in_crew_order(self):
        assert office_ids() == (
            "primary", "polymath", "architect", "auditor",
            "cartographer", "forge_worker", "scribe", "skald",
            "guardian")
        assert [o.id for o in OFFICES] == list(office_ids())

    def test_every_shipped_subagent_maps_to_an_office(self):
        from mythic_agent.constants import DEFAULT_SUBAGENTS

        assert DEFAULT_SUBAGENTS
        for sub in DEFAULT_SUBAGENTS:
            assert office_for_agent_name(sub["name"]) is not None, sub["name"]

    def test_every_nonprimary_office_is_held_by_a_shipped_subagent(self):
        from mythic_agent.constants import DEFAULT_SUBAGENTS

        held = {office_for_agent_name(s["name"]) for s in DEFAULT_SUBAGENTS}
        assert held == set(office_ids()) - {"primary"}

    def test_office_for_agent_name(self):
        assert office_for_agent_name("Primary") == "primary"
        assert office_for_agent_name(
            "Architect - Rúnhild Svartdóttir") == "architect"
        assert office_for_agent_name(
            "Forge Worker - Eldra Járnsdóttir") == "forge_worker"
        assert office_for_agent_name("Thor Guardian") == "guardian"
        assert office_for_agent_name(
            "Cartographer - Védis Eikleið") == "cartographer"

    @pytest.mark.parametrize("name", ["Nobody", "", "  ", None, 7])
    def test_unclaimed_names_are_none_never_guessed(self, name):
        assert office_for_agent_name(name) is None

    def test_unknown_office_keyerror_names_the_offices(self):
        with pytest.raises(KeyError, match="architect"):
            get_office("wizard")


# ----------------------------------------------------------------------
# Stored routes: validation and resolution
# ----------------------------------------------------------------------

class TestRoutesFromConfig:
    def test_missing_key_is_no_routes(self):
        assert routes_from_config({}) == {}
        assert routes_from_config({"role_routes": {}}) == {}
        assert routes_from_config({"role_routes": None}) == {}

    def test_valid_routes_are_normalised(self):
        config = {"role_routes": {
            "architect": {"model": " deepseek-reasoner ",
                          "base_url": " https://api.deepseek.com/v1 "}}}
        assert routes_from_config(config) == {"architect": {
            "model": "deepseek-reasoner",
            "base_url": "https://api.deepseek.com/v1"}}

    @pytest.mark.parametrize("raw", [
        {"wizard": {"model": "m", "base_url": "http://x/v1"}},
        {"architect": "deepseek-reasoner"},
        {"architect": {"base_url": "http://x/v1"}},
        {"architect": {"model": "  ", "base_url": "http://x/v1"}},
        {"architect": {"model": "m"}},
        {"architect": {"model": "m", "base_url": ""}},
    ])
    def test_malformed_stored_routes_raise_never_vanish(self, raw):
        with pytest.raises(ValueError):
            routes_from_config({"role_routes": raw})

    def test_non_mapping_routes_raise(self):
        with pytest.raises(ValueError, match="must be a mapping"):
            routes_from_config({"role_routes": ["architect"]})


class TestResolveRoute:
    def test_unrouted_office_falls_back_to_the_session_default(self):
        route = resolve_route(CONFIG, "architect")
        assert route.source == "session_default"
        assert route.model == "deepseek-chat"
        assert route.base_url == "https://api.deepseek.com/v1"
        assert route.provider == "deepseek"

    def test_explicit_route_wins_and_its_provider_is_inferred(self):
        config = {**CONFIG, "role_routes": {"forge_worker": {
            "model": "llama-3.3-70b-versatile",
            "base_url": "https://api.groq.com/openai/v1"}}}
        route = resolve_route(config, "forge_worker")
        assert route.source == "route"
        assert route.provider == "groq"
        # Neighbouring offices are untouched by the route.
        assert resolve_route(config, "scribe").source == "session_default"

    def test_custom_door_route_has_no_provider(self):
        config = {**CONFIG, "role_routes": {"cartographer": {
            "model": "qwen3-8b", "base_url": "http://localhost:9999/v1"}}}
        assert resolve_route(config, "cartographer").provider is None

    def test_effective_routes_cover_every_office_in_order(self):
        routes = effective_routes(CONFIG)
        assert [r.office for r in routes] == list(office_ids())
        assert all(r.source == "session_default" for r in routes)


# ----------------------------------------------------------------------
# Setting and clearing routes (pure)
# ----------------------------------------------------------------------

class TestSetRoute:
    def test_provider_route_takes_endpoint_and_default_model(self):
        routes, change = set_route(CONFIG, "architect", provider="groq")
        assert routes == {"architect": {
            "model": "llama-3.3-70b-versatile",
            "base_url": "https://api.groq.com/openai/v1"}}
        assert change.before.source == "session_default"
        assert change.after.provider == "groq"
        assert change.event() == {
            "type": "role_route_changed", "office": "architect",
            "from": {"model": "deepseek-chat",
                     "base_url": "https://api.deepseek.com/v1",
                     "provider": "deepseek"},
            "from_source": "session_default",
            "to": {"model": "llama-3.3-70b-versatile",
                   "base_url": "https://api.groq.com/openai/v1",
                   "provider": "groq"}}

    def test_model_only_route_keeps_the_session_door(self):
        routes, change = set_route(CONFIG, "forge_worker",
                                   model="deepseek-reasoner")
        assert routes["forge_worker"] == {
            "model": "deepseek-reasoner",
            "base_url": "https://api.deepseek.com/v1"}
        assert change.after.provider == "deepseek"

    def test_second_set_resolves_against_the_existing_route(self):
        config = {**CONFIG, "role_routes": {"architect": {
            "model": "llama-3.3-70b-versatile",
            "base_url": "https://api.groq.com/openai/v1"}}}
        routes, change = set_route(config, "architect", model="other")
        assert routes["architect"] == {
            "model": "other", "base_url": "https://api.groq.com/openai/v1"}
        assert change.before.source == "route"

    def test_set_route_is_pure(self):
        config = copy.deepcopy(CONFIG)
        set_route(config, "architect", provider="groq")
        assert config == CONFIG

    @pytest.mark.parametrize("provider", ["anthropic", "google", "ollama"])
    def test_native_doors_are_refused_plainly(self, provider):
        with pytest.raises(ValueError, match="cannot use"):
            set_route(CONFIG, "architect", provider=provider)

    def test_primary_route_is_refused_with_the_reason(self):
        with pytest.raises(ValueError, match="no route of its own"):
            set_route(CONFIG, "primary", model="x")

    def test_unknown_office_is_refused(self):
        with pytest.raises(KeyError):
            set_route(CONFIG, "wizard", model="x")

    def test_nothing_to_set_is_refused(self):
        with pytest.raises(ValueError, match="Nothing to switch"):
            set_route(CONFIG, "architect")


class TestClearRoute:
    def test_clear_returns_the_office_to_the_default(self):
        config = {**CONFIG, "role_routes": {"scribe": {
            "model": "m", "base_url": "http://localhost:9/v1"}}}
        routes, change = clear_route(config, "scribe")
        assert routes == {}
        assert change.after is None
        assert change.event()["to"] is None
        assert resolve_route({**CONFIG, "role_routes": routes},
                             "scribe").source == "session_default"

    def test_clear_without_a_route_is_refused(self):
        with pytest.raises(ValueError, match="no role route to clear"):
            clear_route(CONFIG, "scribe")

    def test_clear_primary_is_refused(self):
        with pytest.raises(ValueError, match="no route to clear"):
            clear_route(CONFIG, "primary")


# ----------------------------------------------------------------------
# The shared slash-argument parser and the formatters
# ----------------------------------------------------------------------

class TestParseRouteArgs:
    def test_empty_lists(self):
        assert parse_route_args("")["action"] == "list"
        assert parse_route_args(None)["action"] == "list"

    def test_show_one_office(self):
        parsed = parse_route_args("architect")
        assert parsed["action"] == "show"
        assert parsed["office"] == "architect"

    def test_legacy_positional_set(self):
        parsed = parse_route_args("forge_worker qwen3-8b http://localhost:9/v1")
        assert parsed["action"] == "set"
        assert parsed["model"] == "qwen3-8b"
        assert parsed["base_url"] == "http://localhost:9/v1"

    def test_flag_set(self):
        parsed = parse_route_args(
            "architect --provider groq --model llama")
        assert parsed == {"action": "set", "office": "architect",
                          "model": "llama", "provider": "groq",
                          "base_url": None}

    def test_clear(self):
        parsed = parse_route_args("clear scribe")
        assert parsed["action"] == "clear"
        assert parsed["office"] == "scribe"

    @pytest.mark.parametrize("text", [
        "clear",                              # missing office
        "clear scribe extra",                 # too many words
        "architect --provider",               # missing value
        "architect --bogus x",                # unknown flag
        "architect --provider groq --provider xai",  # flag twice
        "architect a b c",                    # too many positionals
        "architect a --model b",              # model twice
        "'unbalanced",                        # shlex error
    ])
    def test_usage_errors(self, text):
        with pytest.raises(ValueError):
            parse_route_args(text)

    def test_unknown_office_is_a_keyerror(self):
        with pytest.raises(KeyError):
            parse_route_args("wizard")


class TestFormat:
    def test_format_routes_shows_every_office_and_its_source(self):
        config = {**CONFIG, "role_routes": {"architect": {
            "model": "llama-3.3-70b-versatile",
            "base_url": "https://api.groq.com/openai/v1"}}}
        text = format_routes(config)
        assert "Architect: llama-3.3-70b-versatile via groq" in text
        assert "[role route]" in text
        assert "[session default]" in text
        for office in OFFICES:
            assert f"{office.title}:" in text

    def test_format_route_change_set_and_clear(self):
        record = {"office": "architect",
                  "from": {"model": "a", "base_url": "http://a/v1",
                           "provider": None},
                  "from_source": "session_default",
                  "to": {"model": "b",
                         "base_url": "https://api.groq.com/openai/v1",
                         "provider": "groq"},
                  "session_id": "s" * 32, "journaled": True}
        text = format_route_change(record)
        assert "Architect route changed" in text
        assert "b via groq" in text
        assert "s" * 32 in text
        cleared = format_route_change({**record, "to": None})
        assert "route cleared" in cleared
        assert "session default" in cleared


# ----------------------------------------------------------------------
# The config contract
# ----------------------------------------------------------------------

class TestConfigContract:
    def test_role_routes_ships_empty_in_the_defaults(self):
        import yaml

        from mythic_agent.resources import resource_root

        defaults = yaml.safe_load(
            (resource_root() / "config_defaults.yaml").read_text())
        assert defaults["role_routes"] == {}

    def test_role_routes_is_catalogued(self):
        from mythic_agent.core.config_catalog import load_catalog

        catalog = load_catalog()
        by_name = {s.name: s for s in catalog.settings}
        assert by_name["role_routes"].type == "dict"
        assert by_name["role_routes"].scope == "top-level"


# ----------------------------------------------------------------------
# Agent route changes: journal, save, spawn
# ----------------------------------------------------------------------

class TestAgentRoutes:
    def test_role_route_by_office_and_by_member_name(self, agent):
        by_office = agent.role_route("architect")
        assert by_office["source"] == "session_default"
        assert by_office["model"] == "test-model"
        by_name = agent.role_route("Architect - Rúnhild Svartdóttir")
        assert by_name["office"] == "architect"
        with pytest.raises(KeyError):
            agent.role_route("Nobody McUnknown")

    def test_set_route_without_session(self, agent):
        record = agent.set_role_route("architect", provider="groq")
        assert agent.config["role_routes"] == {"architect": {
            "model": "llama-3.3-70b-versatile",
            "base_url": "https://api.groq.com/openai/v1"}}
        assert record["journaled"] is False
        assert agent.role_route("architect")["source"] == "route"
        # The session's own selection is untouched by a route.
        assert agent.config["model"] == "test-model"

    def test_set_and_clear_journal_on_the_session(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.set_role_route("cartographer", model="cheap-scout")
        agent.clear_role_route("cartographer")
        events = [e for e in store.export(session_id)["events"]
                  if e["type"].startswith("role_route")]
        assert [e["type"] for e in events] == [
            "role_route_changed", "role_route_changed"]
        assert events[0]["office"] == "cartographer"
        assert events[0]["to"]["model"] == "cheap-scout"
        assert events[1]["to"] is None
        assert agent.config["role_routes"] == {}
        agent.close()

    def test_refused_route_changes_nothing(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        before = copy.deepcopy(agent.config)
        events_before = len(store.export(session_id)["events"])
        with pytest.raises(ValueError, match="cannot use"):
            agent.set_role_route("architect", provider="anthropic")
        assert agent.config == before
        assert len(store.export(session_id)["events"]) == events_before
        agent.close()

    def test_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        before = copy.deepcopy(agent.config)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.set_role_route("architect", provider="groq")
        assert agent.config == before
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["role_route_changed", "role_route_reverted"]
        agent.close()

    def test_route_applies_to_a_member_at_spawn(self, agent, tmp_path):
        from mythic_agent.agents import llm
        from mythic_agent.core.secure_api import unsubscribe

        agent.set_role_route("forge_worker", provider="groq")
        crew = llm.Agent(project_root=tmp_path, name="Forge Worker")
        try:
            agent._apply_role_route_to(crew)
            assert crew.config["model"] == "llama-3.3-70b-versatile"
            assert crew.config["base_url"] == "https://api.groq.com/openai/v1"
        finally:
            unsubscribe("agent_clear_history", crew._handle_clear_history)
            unsubscribe("agent_compact_history", crew._handle_compact_history)

    def test_route_change_reaches_idle_members_but_not_busy_ones(
            self, agent, tmp_path):
        from mythic_agent.agents import llm
        from mythic_agent.core.secure_api import unsubscribe

        idle = llm.Agent(project_root=tmp_path, name="Forge Worker")
        busy = llm.Agent(project_root=tmp_path, name="Scribe")
        try:
            llm.AGENT_REGISTRY["Forge Worker"] = idle
            llm.AGENT_REGISTRY["Scribe"] = busy
            busy._turn_lock.acquire()
            try:
                agent.set_role_route("forge_worker", provider="groq")
                agent.set_role_route("scribe", provider="groq")
            finally:
                busy._turn_lock.release()
            assert idle.config["model"] == "llama-3.3-70b-versatile"
            assert busy.config["model"] != "llama-3.3-70b-versatile"
        finally:
            llm.AGENT_REGISTRY.pop("Forge Worker", None)
            llm.AGENT_REGISTRY.pop("Scribe", None)
            for member in (idle, busy):
                unsubscribe("agent_clear_history",
                            member._handle_clear_history)
                unsubscribe("agent_compact_history",
                            member._handle_compact_history)


class TestManagerSpawnRouting:
    """Regression: spawn_subagent lives on AgentManager, which has no
    config of its own — routes there are read from the loaded config.
    (The first M-029 cut called an Agent-only helper on the manager
    and broke delegation; test_policy caught it in the full suite.)
    """

    def _setup_manager(self, agent, monkeypatch):
        from unittest.mock import Mock

        from mythic_agent.agents import llm

        monkeypatch.setattr(llm.config_manager, "load_config",
                            lambda: agent.config.copy())
        monkeypatch.setattr(llm, "AGENT_REGISTRY", {})
        monkeypatch.setattr(llm.threading, "Thread", Mock())
        return llm

    @staticmethod
    def _forget_thread(name):
        # The mocked spawn thread stays "alive" in the global thread
        # registry; forget it so neighbouring spawn tests (in any
        # file order) are not refused as duplicate owners.
        from mythic_agent.core.thread_audit import THREAD_REGISTRY

        THREAD_REGISTRY.forget(f"mythic-subagent-loop:{name}")

    def _arch_name(self, agent):
        return next(entry["name"] for entry in agent.config["sub_agents"]
                    if entry["name"].startswith("Architect"))

    def test_fresh_spawn_takes_the_office_route(self, agent, monkeypatch):
        from mythic_agent.core.policy import ToolPolicy

        llm = self._setup_manager(agent, monkeypatch)
        agent.set_role_route("architect", provider="groq")
        name = self._arch_name(agent)
        self._forget_thread(name)  # a stale mock registration may linger
        child = llm.agent_manager.spawn_subagent(
            name, agent.project_root, policy=ToolPolicy("read-only"))
        try:
            assert child is not None
            assert child.config["model"] == "llama-3.3-70b-versatile"
            assert child.config["base_url"] == \
                "https://api.groq.com/openai/v1"
        finally:
            if child is not None:
                child.close()
            self._forget_thread(name)

    def test_existing_member_is_rerouted_on_respawn(self, agent, monkeypatch):
        from mythic_agent.core.policy import ToolPolicy

        llm = self._setup_manager(agent, monkeypatch)
        # A different member than the fresh-spawn test's: the mocked
        # thread stays "alive" in the global thread registry.
        name = next(entry["name"] for entry in agent.config["sub_agents"]
                    if entry["name"].startswith("Forge Worker"))
        self._forget_thread(name)  # a stale mock registration may linger
        child = llm.agent_manager.spawn_subagent(
            name, agent.project_root, policy=ToolPolicy("read-only"))
        try:
            assert child.config["model"] == "test-model"
            agent.set_role_route("forge_worker", provider="groq")
            again = llm.agent_manager.spawn_subagent(
                name, agent.project_root, policy=ToolPolicy("read-only"))
            assert again is child
            assert child.config["model"] == "llama-3.3-70b-versatile"
        finally:
            if child is not None:
                child.close()
            self._forget_thread(name)


# ----------------------------------------------------------------------
# The surfaces
# ----------------------------------------------------------------------

class TestTerminalSlash:
    def test_list(self, agent):
        from mythic_agent.terminal import _slash

        handled, quit_chat, text = _slash(agent, "/route")
        assert handled and not quit_chat
        assert "Architect:" in text and "session default" in text

    def test_set_show_and_clear(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/route architect --provider groq")
        assert "Architect route changed" in text
        assert agent.config["role_routes"]["architect"]["model"] == \
            "llama-3.3-70b-versatile"
        _, _, text = _slash(agent, "/route architect")
        assert "llama-3.3-70b-versatile via groq" in text
        assert "[role route]" in text
        _, _, text = _slash(agent, "/route clear architect")
        assert "route cleared" in text
        assert agent.config["role_routes"] == {}

    def test_refusal_is_the_message_and_nothing_changes(self, agent):
        from mythic_agent.terminal import _slash

        before = copy.deepcopy(agent.config)
        _, _, text = _slash(agent, "/route architect --provider ollama")
        assert "cannot use" in text
        assert agent.config == before


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


class TestRouteCommand:
    def test_list_is_default(self, handler, agent):
        handler._handle_route("")
        text = _published_text(handler)
        assert "Forge Worker:" in text and "session default" in text

    def test_set_via_provider(self, handler, agent):
        handler._handle_route("cartographer --provider groq")
        text = _published_text(handler)
        assert "Cartographer route changed" in text
        assert agent.config["role_routes"]["cartographer"]["model"] == \
            "llama-3.3-70b-versatile"

    def test_refusal_is_published_verbatim(self, handler, agent):
        before = copy.deepcopy(agent.config)
        handler._handle_route("architect --provider anthropic")
        assert "cannot use" in _published_text(handler)
        assert agent.config == before

    def test_unknown_office_is_published(self, handler, agent):
        handler._handle_route("wizard")
        assert "Unknown office" in _published_text(handler)


class TestChatScreenRouting:
    def test_route_rides_the_system_command_road(self, monkeypatch):
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
        screen.handle_command("/route architect", _FakeLog())
        assert calls == [("/route", "architect")]
