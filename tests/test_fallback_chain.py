"""M-030 — Fallback chains.

TIER: integration

Covers the M-030 surface:

* the pure layer (``mythic_agent.core.fallback_chain``): the chain
  and its standing permission are config data, validated — a
  malformed stored chain raises, never vanishes; entries resolve
  through the M-028 switch resolver (provider names take the
  registry endpoint + default model, native doors refused plainly,
  the session's own current door refused, duplicates refused); a
  provider is inferred from its door, never stored; the walk list
  is the user's order with the current door excluded,
* ``Agent`` chain/permission changes: journaled as
  ``fallback_chain_changed`` / ``fallback_permission_changed``
  session events, saved to config, a failed save restores the
  previous settings exactly and journals the revert,
* the live walk: ``Agent._run_turn`` (via
  ``_request_with_fallback``) — with standing permission a failed
  provider request walks the chain in order, every walk announced
  on the chat surface and journaled as ``fallback_walked`` before
  the new door is tried; without permission (or with an empty
  chain) the original failure is raised untouched; when every
  door fails the original selection is restored, a
  ``fallback_exhausted`` event is journaled, and the last failure
  is raised,
* the surfaces: the terminal ``/fallback`` and the TUI
  ``/fallback`` (system-command road through the CommandHandler +
  chat-screen routing), which share the parser and formatters,
* the config contract: ``fallback_chain`` + ``fallback_permission``
  ship in the defaults and are catalogued (M-009).
"""

from __future__ import annotations

import copy
from types import SimpleNamespace

import pytest

from mythic_agent.core.fallback_chain import (
    chain_from_config,
    clear_chain,
    format_chain,
    format_fallback_change,
    format_walk,
    parse_fallback_args,
    permission_from_config,
    resolve_entry,
    set_chain_entry,
    set_permission,
    walk_entries,
)
from mythic_agent.core.sessions import SessionStore

CURRENT = {"model": "deepseek-chat", "base_url": "https://api.deepseek.com/v1"}
GROQ = {"model": "llama-3.3-70b-versatile",
        "base_url": "https://api.groq.com/openai/v1"}
CUSTOM = {"model": "qwen3-8b", "base_url": "http://localhost:9999/v1"}


def config_with(chain=None, permission=None):
    config = dict(CURRENT)
    if chain is not None:
        config["fallback_chain"] = chain
    if permission is not None:
        config["fallback_permission"] = permission
    return config


def store_for(tmp_path, workspace=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state")


# ----------------------------------------------------------------------
# The stored chain + permission, validated as data
# ----------------------------------------------------------------------

class TestChainFromConfig:
    def test_absent_chain_is_empty(self):
        assert chain_from_config({}) == ()
        assert chain_from_config({"fallback_chain": []}) == ()

    def test_entries_keep_the_users_order_and_infer_providers(self):
        entries = chain_from_config(config_with(chain=[GROQ, CUSTOM]))
        assert [e.model for e in entries] == [GROQ["model"], CUSTOM["model"]]
        assert entries[0].provider == "groq"
        assert entries[1].provider is None  # custom door, never guessed

    @pytest.mark.parametrize("raw", [
        "groq",                                            # not a list
        ["groq"],                                          # entry not a mapping
        [{"base_url": "http://x/v1"}],                     # no model
        [{"model": "  ", "base_url": "http://x/v1"}],      # blank model
        [{"model": "m"}],                                  # no door
        [{"model": "m", "base_url": ""}],                  # blank door
        [GROQ, dict(GROQ)],                                # same door twice
    ])
    def test_malformed_stored_chain_raises_never_vanishes(self, raw):
        with pytest.raises(ValueError):
            chain_from_config(config_with(chain=raw))


class TestPermissionFromConfig:
    def test_absent_permission_is_off(self):
        assert permission_from_config({}) is False

    def test_stored_bool_is_the_answer(self):
        assert permission_from_config({"fallback_permission": True}) is True
        assert permission_from_config({"fallback_permission": False}) is False

    @pytest.mark.parametrize("raw", ["yes", 1, None])
    def test_non_bool_permission_raises(self, raw):
        with pytest.raises(ValueError):
            permission_from_config({"fallback_permission": raw})


# ----------------------------------------------------------------------
# Entry resolution (through the M-028 resolver)
# ----------------------------------------------------------------------

class TestResolveEntry:
    def test_provider_entry_takes_endpoint_and_default_model(self):
        entry = resolve_entry(CURRENT, provider="groq")
        assert entry.model == GROQ["model"]
        assert entry.base_url == GROQ["base_url"]
        assert entry.provider == "groq"

    def test_explicit_model_on_a_provider_door(self):
        entry = resolve_entry(CURRENT, provider="openrouter",
                              model="acme/acme-coder-1")
        assert entry.model == "acme/acme-coder-1"
        assert entry.provider == "openrouter"

    def test_custom_door_has_no_provider(self):
        entry = resolve_entry(CURRENT, model="qwen3-8b",
                              base_url="http://localhost:9999/v1")
        assert entry.provider is None

    @pytest.mark.parametrize("provider", ["anthropic", "google", "ollama"])
    def test_native_doors_are_refused_plainly(self, provider):
        with pytest.raises(ValueError, match="cannot use"):
            resolve_entry(CURRENT, provider=provider)

    def test_the_current_door_is_refused(self):
        with pytest.raises(ValueError, match="current door"):
            resolve_entry(CURRENT, provider="deepseek")
        with pytest.raises(ValueError, match="current door"):
            resolve_entry(CURRENT, model="deepseek-chat")

    def test_unknown_provider_names_the_registry(self):
        with pytest.raises(ValueError, match="Unknown provider 'acme'"):
            resolve_entry(CURRENT, provider="acme")


# ----------------------------------------------------------------------
# Pure changes
# ----------------------------------------------------------------------

class TestPureChanges:
    def test_set_chain_entry_appends_without_mutating_config(self):
        config = config_with(chain=[])
        stored, change = set_chain_entry(config, provider="groq")
        assert config["fallback_chain"] == []
        assert stored == [GROQ]
        assert "provider" not in stored[0]  # inferred, never stored
        assert change.kind == "chain"
        assert [e.model for e in change.after] == [GROQ["model"]]

    def test_duplicate_entry_is_refused(self):
        config = config_with(chain=[GROQ])
        with pytest.raises(ValueError, match="already in the fallback chain"):
            set_chain_entry(config, provider="groq")

    def test_clear_chain_empties_and_empty_clear_is_refused(self):
        stored, change = clear_chain(config_with(chain=[GROQ]))
        assert stored == []
        assert change.after == ()
        with pytest.raises(ValueError, match="already empty"):
            clear_chain(config_with(chain=[]))

    def test_set_permission_flips_and_same_value_is_refused(self):
        value, change = set_permission(config_with(permission=False), True)
        assert value is True
        assert change.event() == {"type": "fallback_permission_changed",
                                  "from": False, "to": True}
        with pytest.raises(ValueError, match="already off"):
            set_permission(config_with(permission=False), False)
        with pytest.raises(ValueError, match="true or false"):
            set_permission(config_with(), "yes")

    def test_chain_change_event_shape(self):
        _, change = set_chain_entry(config_with(chain=[]), provider="groq")
        event = change.event()
        assert event["type"] == "fallback_chain_changed"
        assert event["from"] == []
        assert event["to"] == [{**GROQ, "provider": "groq"}]


class TestWalkEntries:
    def test_walk_order_is_the_users_order(self):
        config = config_with(chain=[CUSTOM, GROQ])
        assert [e.model for e in walk_entries(config)] == [
            CUSTOM["model"], GROQ["model"]]

    def test_the_current_door_is_excluded_from_the_walk(self):
        config = config_with(chain=[dict(CURRENT), GROQ])
        assert [e.model for e in walk_entries(config)] == [GROQ["model"]]


# ----------------------------------------------------------------------
# The shared slash-argument parser + formatters
# ----------------------------------------------------------------------

class TestParseFallbackArgs:
    def test_empty_is_show(self):
        assert parse_fallback_args("")["action"] == "show"
        assert parse_fallback_args(None)["action"] == "show"

    def test_on_and_off(self):
        assert parse_fallback_args("on") == {
            "action": "permission", "enabled": True, "model": None,
            "provider": None, "base_url": None}
        assert parse_fallback_args("off")["enabled"] is False

    def test_clear(self):
        assert parse_fallback_args("clear")["action"] == "clear"

    def test_add_legacy_and_flags(self):
        parsed = parse_fallback_args("add qwen3-8b http://localhost:9999/v1")
        assert parsed["action"] == "add"
        assert parsed["model"] == "qwen3-8b"
        assert parsed["base_url"] == "http://localhost:9999/v1"
        parsed = parse_fallback_args("add --provider groq --model llama")
        assert parsed["provider"] == "groq" and parsed["model"] == "llama"

    @pytest.mark.parametrize("text", [
        "on now",                       # extra words after on
        "clear now",                    # extra words after clear
        "add",                          # nothing to add
        "add --reason cheaper",         # a door takes no reason
        "bogus",                        # unknown command
        "add --bogus x",                # unknown flag (switch parser)
    ])
    def test_usage_errors(self, text):
        with pytest.raises(ValueError):
            parse_fallback_args(text)


class TestFormatters:
    def test_format_chain_shows_permission_current_and_order(self):
        text = format_chain(config_with(chain=[GROQ, CUSTOM], permission=True))
        assert "standing permission ON" in text
        assert "deepseek-chat via deepseek" in text
        assert "1. llama-3.3-70b-versatile via groq" in text
        assert "2. qwen3-8b (http://localhost:9999/v1)" in text

    def test_format_chain_without_permission_or_doors_is_honest(self):
        text = format_chain(config_with(chain=[], permission=False))
        assert "standing permission OFF" in text
        assert "Chain: empty" in text
        assert "/fallback on" in text

    def test_format_walk_announces_from_error_and_to(self):
        record = {
            "from": {"model": "a", "base_url": "http://a/v1", "provider": None},
            "to": {"model": "b", "base_url": "https://api.groq.com/openai/v1",
                   "provider": "groq"},
            "error": "429 rate limited", "position": 2}
        text = format_walk(record)
        assert "Fallback walk 2" in text
        assert "a (http://a/v1) failed — 429 rate limited" in text
        assert "b via groq" in text
        assert "never silent" in text

    def test_format_fallback_change_sentences(self):
        _, change = set_permission(config_with(permission=False), True)
        assert "now ON" in format_fallback_change(change.record("s" * 32, True))
        stored, change = set_chain_entry(config_with(chain=[]), provider="groq")
        text = format_fallback_change(change.record(None, False))
        assert "door 1 in the chain" in text and "groq" in text
        _, change = clear_chain(config_with(chain=[GROQ]))
        assert "cleared" in format_fallback_change(change.record(None, False))


# ----------------------------------------------------------------------
# Agent chain/permission changes
# ----------------------------------------------------------------------

class TestAgentFallbackChanges:
    def test_status_defaults_are_off_and_empty(self, agent):
        status = agent.fallback_status()
        assert status["permission"] is False
        assert status["chain"] == []
        assert status["current"]["model"] == "test-model"

    def test_add_permission_and_clear_without_session(self, agent):
        record = agent.add_fallback_entry(provider="groq")
        assert record["journaled"] is False
        assert agent.config["fallback_chain"] == [GROQ]
        assert agent.fallback_status()["chain"][0]["provider"] == "groq"
        agent.set_fallback_permission(True)
        assert agent.config["fallback_permission"] is True
        agent.clear_fallback_chain()
        assert agent.config["fallback_chain"] == []

    def test_changes_journal_on_the_session(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.add_fallback_entry(provider="groq")
        agent.set_fallback_permission(True)
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "fallback_chain_changed" in types
        assert "fallback_permission_changed" in types
        changed = [e for e in store.export(session_id)["events"]
                   if e["type"] == "fallback_chain_changed"][0]
        assert changed["to"][0]["provider"] == "groq"
        agent.close()

    def test_refused_change_changes_nothing(self, agent):
        before = copy.deepcopy(agent.config)
        with pytest.raises(ValueError, match="cannot use"):
            agent.add_fallback_entry(provider="anthropic")
        assert agent.config == before

    def test_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        before = copy.deepcopy(agent.config)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.add_fallback_entry(provider="groq")
        assert agent.config == before
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["fallback_chain_changed",
                              "fallback_change_reverted"]
        agent.close()


# ----------------------------------------------------------------------
# The live walk
# ----------------------------------------------------------------------

def _response(text):
    return SimpleNamespace(
        choices=[SimpleNamespace(
            message={"role": "assistant", "content": text})],
        usage=None)


def _wire_doors(agent, failing):
    """Fake clients/requests keyed by the agent's current door.

    ``failing`` maps base_url -> error text; a door not in the map
    answers. Returns the list of doors actually tried, in order.
    """
    tried = []

    def get_client():
        return SimpleNamespace(door=agent.config["base_url"])

    def request(client, settings):
        tried.append(client.door)
        if client.door in failing:
            raise RuntimeError(failing[client.door])
        return _response(f"Reply from {client.door}"), False

    agent.get_client = get_client
    agent._request_response = request
    return tried


class TestLiveWalk:
    def test_walk_announces_journals_and_answers_from_the_next_door(
            self, agent, tmp_path):
        from mythic_agent.core.secure_api import subscribe, unsubscribe

        agent.config["fallback_chain"] = [
            {"model": "backup-model", "base_url": "http://localhost:2/v1"},
            {"model": "third-model", "base_url": "http://localhost:3/v1"}]
        agent.config["fallback_permission"] = True
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        tried = _wire_doors(agent, {
            "http://localhost:1/v1": "429 rate limited",
            "http://localhost:2/v1": "connection refused"})
        heard = []
        on_chunk = lambda **kw: heard.append(kw.get("text", "")) \
            if kw.get("agent_name") == agent.name else None
        subscribe("agent_chat_chunk", on_chunk)
        try:
            text = agent._run_turn("hello")
        finally:
            unsubscribe("agent_chat_chunk", on_chunk)
        assert text == "Reply from http://localhost:3/v1"
        assert tried == ["http://localhost:1/v1", "http://localhost:2/v1",
                         "http://localhost:3/v1"]
        assert agent.config["base_url"] == "http://localhost:3/v1"
        assert agent.config["model"] == "third-model"
        announcements = [t for t in heard if "Fallback walk" in t]
        assert len(announcements) == 2
        assert "429 rate limited" in announcements[0]
        assert "connection refused" in announcements[1]
        walks = [e for e in store.export(session_id)["events"]
                 if e["type"] == "fallback_walked"]
        assert len(walks) == 2
        assert walks[0]["from"]["base_url"] == "http://localhost:1/v1"
        assert walks[0]["to"]["base_url"] == "http://localhost:2/v1"
        assert walks[0]["position"] == 1
        assert walks[1]["to"]["base_url"] == "http://localhost:3/v1"
        agent.close()

    def test_without_permission_the_failure_is_the_failure(self, agent):
        agent.config["fallback_chain"] = [
            {"model": "backup-model", "base_url": "http://localhost:2/v1"}]
        agent.config["fallback_permission"] = False
        tried = _wire_doors(agent, {"http://localhost:1/v1": "429 rate limited"})
        with pytest.raises(RuntimeError, match="429 rate limited"):
            agent._run_turn("hello")
        assert tried == ["http://localhost:1/v1"]
        assert agent.config["base_url"] == "http://localhost:1/v1"

    def test_empty_chain_never_walks_even_with_permission(self, agent):
        agent.config["fallback_chain"] = []
        agent.config["fallback_permission"] = True
        tried = _wire_doors(agent, {"http://localhost:1/v1": "boom"})
        with pytest.raises(RuntimeError, match="boom"):
            agent._run_turn("hello")
        assert tried == ["http://localhost:1/v1"]

    def test_all_doors_fail_restores_the_selection_and_journals(
            self, agent, tmp_path):
        agent.config["fallback_chain"] = [
            {"model": "backup-model", "base_url": "http://localhost:2/v1"}]
        agent.config["fallback_permission"] = True
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        before = copy.deepcopy(agent.config)
        _wire_doors(agent, {"http://localhost:1/v1": "first down",
                            "http://localhost:2/v1": "second down"})
        with pytest.raises(RuntimeError, match="second down"):
            agent._run_turn("hello")
        assert agent.config == before
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "fallback_walked" in types
        assert types[-1] == "fallback_exhausted"
        agent.close()

    def test_malformed_stored_chain_surfaces_instead_of_walking(
            self, agent):
        agent.config["fallback_chain"] = [{"model": "x"}]  # no door
        agent.config["fallback_permission"] = True
        _wire_doors(agent, {"http://localhost:1/v1": "boom"})
        with pytest.raises(ValueError, match="no door URL"):
            agent._run_turn("hello")


# ----------------------------------------------------------------------
# The surfaces
# ----------------------------------------------------------------------

class TestTerminalSlash:
    def test_show(self, agent):
        from mythic_agent.terminal import _slash

        handled, quit_chat, text = _slash(agent, "/fallback")
        assert handled and not quit_chat
        assert "standing permission OFF" in text
        assert "Chain: empty" in text

    def test_add_then_on(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/fallback add --provider groq")
        assert "door 1 in the chain" in text
        assert agent.config["fallback_chain"] == [GROQ]
        _, _, text = _slash(agent, "/fallback on")
        assert "now ON" in text
        _, _, text = _slash(agent, "/fallback")
        assert "standing permission ON" in text

    def test_refusal_is_the_message_and_nothing_changes(self, agent):
        from mythic_agent.terminal import _slash

        before = copy.deepcopy(agent.config)
        _, _, text = _slash(agent, "/fallback add --provider anthropic")
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


class TestFallbackCommand:
    def test_show_is_default(self, handler, agent):
        handler._handle_fallback("")
        text = _published_text(handler)
        assert "standing permission OFF" in text

    def test_add_and_on_via_the_handler(self, handler, agent):
        handler._handle_fallback("add --provider groq")
        assert "door 1 in the chain" in _published_text(handler)
        handler._handle_fallback("on")
        assert "now ON" in _published_text(handler)
        assert agent.config["fallback_permission"] is True

    def test_refusal_is_published_verbatim(self, handler, agent):
        before = copy.deepcopy(agent.config)
        handler._handle_fallback("add --provider ollama")
        assert "cannot use" in _published_text(handler)
        assert agent.config == before

    def test_usage_error_is_published(self, handler, agent):
        handler._handle_fallback("bogus")
        assert "Unknown fallback command" in _published_text(handler)


class TestChatScreenRouting:
    def test_fallback_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/fallback on", _FakeLog())
        assert calls == [("/fallback", "on")]


# ----------------------------------------------------------------------
# The config contract
# ----------------------------------------------------------------------

class TestConfigContract:
    def test_defaults_ship_the_chain_and_permission(self):
        from mythic_agent.core import config_manager

        assert config_manager.CONFIG_SCHEMA["fallback_chain"]["type"] is list
        assert config_manager.CONFIG_SCHEMA["fallback_chain"]["default"] == []
        assert config_manager.CONFIG_SCHEMA["fallback_permission"]["type"] is bool
        assert config_manager.CONFIG_SCHEMA["fallback_permission"]["default"] is False

    def test_catalogue_carries_both_settings(self):
        from mythic_agent.core.config_catalog import load_catalog

        by_name = {s.name: s for s in load_catalog().settings}
        assert by_name["fallback_chain"].id == "S-37"
        assert by_name["fallback_chain"].type == "list"
        assert by_name["fallback_permission"].id == "S-38"
        assert by_name["fallback_permission"].type == "bool"
