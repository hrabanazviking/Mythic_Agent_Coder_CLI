"""M-028 — Mid-session model switching.

TIER: integration

Covers the M-028 surface:

* the pure resolver (``mythic_agent.core.model_switch``): provider
  switches resolve through the M-019 registry data (endpoint +
  default model, aliases included); the doors the live session
  cannot speak (native_sdk, ollama_native) are refused plainly;
  unknown providers, empty models, bad URLs and empty requests are
  refused before anything mutates; a custom door's provider is
  inferred only by exact endpoint equality, never guessed,
* the slash-argument parser shared by both surfaces (legacy
  positionals + --provider/--model/--base-url/--reason),
* ``Agent.switch_model``: between-turns only; the session, its
  history/plan context, its token count and the live crew survive
  untouched; the switch is journaled as a ``model_switched``
  session event carrying from/to and the reason if given; a failed
  save restores the previous selection exactly and journals a
  compensating ``model_switch_reverted`` event; a resumed session
  in a fresh agent keeps both the history and the new selection,
* the surfaces: the terminal ``/model`` and the TUI ``/model``
  (system-command road through the CommandHandler + chat-screen
  routing), which share the parser and the record formatter.
"""

from __future__ import annotations

import copy

import pytest

from mythic_agent.core.model_switch import (
    SWITCHABLE_DIALECTS,
    format_switch_record,
    infer_provider,
    parse_switch_args,
    resolve_switch,
)
from mythic_agent.core.provider_registry import load_registry
from mythic_agent.core.sessions import SessionStore

CURRENT = {"model": "deepseek-chat", "base_url": "https://api.deepseek.com/v1"}


def store_for(tmp_path, workspace=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state")


# ----------------------------------------------------------------------
# The resolver
# ----------------------------------------------------------------------

class TestResolveSwitch:
    def test_model_only_keeps_the_door(self):
        target = resolve_switch(CURRENT, model="deepseek-reasoner")
        assert target.to_model == "deepseek-reasoner"
        assert target.to_base_url == CURRENT["base_url"]
        assert target.from_provider == "deepseek"
        assert target.to_provider == "deepseek"
        assert target.reason is None

    def test_provider_switch_takes_endpoint_and_default_model(self):
        target = resolve_switch(CURRENT, provider="groq")
        assert target.to_provider == "groq"
        assert target.to_base_url == "https://api.groq.com/openai/v1"
        assert target.to_model == "llama-3.3-70b-versatile"

    def test_provider_switch_with_explicit_model(self):
        target = resolve_switch(CURRENT, provider="openrouter",
                                model="acme/acme-coder-1")
        assert target.to_base_url == "https://openrouter.ai/api/v1"
        assert target.to_model == "acme/acme-coder-1"

    def test_provider_alias_resolves(self):
        target = resolve_switch(CURRENT, provider="gpt")
        assert target.to_provider == "openai"
        assert target.to_model == "gpt-5"

    def test_aesir_is_switchable(self):
        target = resolve_switch(CURRENT, provider="aesir")
        assert target.to_base_url == "http://127.0.0.1:18434/v1"
        assert target.to_model == "aesir-local"

    @pytest.mark.parametrize("provider", ["anthropic", "google", "ollama"])
    def test_native_doors_are_refused_plainly(self, provider):
        with pytest.raises(ValueError, match="cannot use"):
            resolve_switch(CURRENT, provider=provider)

    def test_every_registry_dialect_is_classified(self):
        registry = load_registry()
        for entry in registry.providers:
            if entry.dialect in SWITCHABLE_DIALECTS:
                target = resolve_switch(CURRENT, provider=entry.name)
                assert target.to_provider == entry.name
                assert target.to_base_url == entry.endpoint
            else:
                with pytest.raises(ValueError):
                    resolve_switch(CURRENT, provider=entry.name)

    def test_unknown_provider_names_the_registry(self):
        with pytest.raises(ValueError, match="Unknown provider 'acme'"):
            resolve_switch(CURRENT, provider="acme")

    def test_custom_door_infers_its_registry_provider(self):
        target = resolve_switch(
            CURRENT, model="llama-3.3-70b-versatile",
            base_url="https://api.groq.com/openai/v1")
        assert target.to_provider == "groq"

    def test_custom_door_without_registry_entry_has_no_provider(self):
        target = resolve_switch(
            CURRENT, model="qwen3-8b", base_url="http://localhost:9999/v1")
        assert target.to_provider is None
        assert target.to_base_url == "http://localhost:9999/v1"

    def test_base_url_wins_over_provider_endpoint(self):
        target = resolve_switch(
            CURRENT, provider="groq", model="m",
            base_url="http://localhost:9999/v1")
        assert target.to_base_url == "http://localhost:9999/v1"
        assert target.to_provider is None

    def test_nothing_to_switch_is_refused(self):
        with pytest.raises(ValueError, match="Nothing to switch"):
            resolve_switch(CURRENT)

    @pytest.mark.parametrize("model", ["", "   ", 7])
    def test_empty_or_nonstr_model_is_refused(self, model):
        with pytest.raises(ValueError, match="Model must be nonempty"):
            resolve_switch(CURRENT, model=model)

    @pytest.mark.parametrize("url", ["", "ftp://x", "localhost:1", 7])
    def test_invalid_url_is_refused(self, url):
        with pytest.raises(ValueError, match="Endpoint must be"):
            resolve_switch(CURRENT, model="m", base_url=url)

    def test_reason_is_stripped_and_blank_reason_is_none(self):
        target = resolve_switch(CURRENT, model="m", reason="  cheaper scout  ")
        assert target.reason == "cheaper scout"
        target = resolve_switch(CURRENT, model="m", reason="   ")
        assert target.reason is None

    def test_nonstr_reason_is_refused(self):
        with pytest.raises(ValueError, match="reason must be text"):
            resolve_switch(CURRENT, model="m", reason=7)

    def test_event_shape_is_exact(self):
        target = resolve_switch(CURRENT, provider="groq", reason="speed")
        assert target.event() == {
            "type": "model_switched",
            "from": {"model": "deepseek-chat",
                     "base_url": "https://api.deepseek.com/v1",
                     "provider": "deepseek"},
            "to": {"model": "llama-3.3-70b-versatile",
                   "base_url": "https://api.groq.com/openai/v1",
                   "provider": "groq"},
            "reason": "speed",
        }


class TestInferProvider:
    def test_exact_endpoint_matches(self):
        assert infer_provider("https://api.deepseek.com/v1") == "deepseek"
        assert infer_provider("http://localhost:11434") == "ollama"

    @pytest.mark.parametrize("url", ["http://localhost:9999/v1", "",
                                     "not a url", None, 7])
    def test_no_match_is_none_never_a_guess(self, url):
        assert infer_provider(url) is None


# ----------------------------------------------------------------------
# The shared slash-argument parser
# ----------------------------------------------------------------------

class TestParseSwitchArgs:
    def test_empty_is_show(self):
        assert parse_switch_args("") == {
            "model": None, "provider": None, "base_url": None, "reason": None}
        assert parse_switch_args(None)["model"] is None

    def test_legacy_positionals(self):
        parsed = parse_switch_args("qwen3-8b")
        assert parsed["model"] == "qwen3-8b"
        parsed = parse_switch_args("qwen3-8b http://localhost:1234/v1")
        assert parsed["base_url"] == "http://localhost:1234/v1"

    def test_flags(self):
        parsed = parse_switch_args(
            "--provider groq --model llama --base-url http://x.test/v1")
        assert parsed == {"model": "llama", "provider": "groq",
                          "base_url": "http://x.test/v1", "reason": None}

    def test_reason_consumes_the_rest_of_the_line(self):
        parsed = parse_switch_args(
            "--provider groq --reason the big door is rate-limited today")
        assert parsed["provider"] == "groq"
        assert parsed["reason"] == "the big door is rate-limited today"

    @pytest.mark.parametrize("text", [
        "--provider",                       # missing value
        "--model",                          # missing value
        "--reason",                         # missing reason
        "--bogus x",                        # unknown flag
        "--provider groq --provider xai",   # flag twice
        "a b c",                            # too many positionals
        "a --model b",                      # model twice (positional + flag)
        "a http://x.test/v1 --base-url http://y.test/v1",  # url twice
        "'unbalanced",                      # shlex error
    ])
    def test_usage_errors(self, text):
        with pytest.raises(ValueError):
            parse_switch_args(text)


class TestFormatSwitchRecord:
    def test_sentence_names_both_sides_session_and_reason(self):
        record = {
            "from": {"model": "a", "base_url": "http://a/v1", "provider": None},
            "to": {"model": "b", "base_url": "https://api.groq.com/openai/v1",
                   "provider": "groq"},
            "reason": "speed", "session_id": "s" * 32, "journaled": True}
        text = format_switch_record(record)
        assert "a (http://a/v1)" in text
        assert "b via groq" in text
        assert "Session " + "s" * 32 + " kept" in text
        assert "Reason: speed" in text

    def test_sentence_without_session_or_reason(self):
        record = {
            "from": {"model": "a", "base_url": "http://a/v1", "provider": "x"},
            "to": {"model": "b", "base_url": "http://a/v1", "provider": "x"},
            "reason": None, "session_id": None, "journaled": False}
        text = format_switch_record(record)
        assert "Session" not in text
        assert "Reason" not in text


# ----------------------------------------------------------------------
# Agent.switch_model
# ----------------------------------------------------------------------

class TestAgentSwitch:
    def test_provider_switch_without_session(self, agent):
        record = agent.switch_model(provider="groq", reason="scout work")
        assert agent.config["model"] == "llama-3.3-70b-versatile"
        assert agent.config["base_url"] == "https://api.groq.com/openai/v1"
        assert agent.active_provider() == "groq"
        assert record["journaled"] is False
        assert record["from"]["provider"] is None  # localhost:1 is custom
        assert record["to"]["provider"] == "groq"
        assert record["reason"] == "scout work"

    def test_switch_journals_and_preserves_the_session(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.add_context("Plan: 1) read the code 2) fix the bug 3) test it")
        before = agent.history_snapshot()
        agent.total_tokens = 42
        record = agent.switch_model(provider="groq", reason="cheaper scout")
        assert record["journaled"] is True
        assert record["session_id"] == session_id
        assert agent.session_id == session_id
        assert agent.history_snapshot() == before
        assert agent.total_tokens == 42
        exported = store.export(session_id)
        assert exported["context"] == before
        switches = [e for e in exported["events"]
                    if e["type"] == "model_switched"]
        assert len(switches) == 1
        assert switches[0]["to"]["provider"] == "groq"
        assert switches[0]["reason"] == "cheaper scout"
        counts = store.session_event_counts(session_id)
        assert counts["by_type"]["model_switched"] == 1
        assert not store.journal.pending()
        agent.close()

    def test_resumed_session_keeps_history_and_new_selection(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.add_context("Plan: keep me across the switch")
        before = agent.history_snapshot()
        saved = {}
        monkeypatch.setattr(
            llm.config_manager, "save_config",
            lambda config: saved.update(copy.deepcopy(config)) or True)
        agent.switch_model(provider="groq")
        agent.close()

        store2 = store_for(tmp_path)
        resumed = llm.Agent(project_root=tmp_path, config=saved)
        try:
            resumed.attach_session(store2, resume=session_id)
            assert resumed.history_snapshot() == before
            assert resumed.config["model"] == "llama-3.3-70b-versatile"
            assert resumed.active_provider() == "groq"
        finally:
            resumed.close()

    def test_crew_survives_a_primary_switch(self, agent, tmp_path):
        from mythic_agent.agents import llm
        from mythic_agent.core.secure_api import unsubscribe

        crew = llm.Agent(project_root=tmp_path, name="Forge Worker")
        try:
            crew_config = copy.deepcopy(crew.config)
            crew_history = crew.history_snapshot()
            llm.AGENT_REGISTRY["Forge Worker"] = crew
            sub_agents_before = copy.deepcopy(agent.config.get("sub_agents"))
            agent.switch_model(provider="groq")
            assert llm.AGENT_REGISTRY["Forge Worker"] is crew
            assert crew.config == crew_config
            assert crew.history_snapshot() == crew_history
            assert agent.config.get("sub_agents") == sub_agents_before
        finally:
            llm.AGENT_REGISTRY.pop("Forge Worker", None)
            unsubscribe("agent_clear_history", crew._handle_clear_history)
            unsubscribe("agent_compact_history", crew._handle_compact_history)

    def test_switch_during_a_turn_is_refused_and_changes_nothing(
            self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        before_config = copy.deepcopy(agent.config)
        events_before = len(store.export(session_id)["events"])
        agent._turn_lock.acquire()
        try:
            with pytest.raises(RuntimeError, match="Finish the current turn"):
                agent.switch_model(provider="groq")
        finally:
            agent._turn_lock.release()
        assert agent.config == before_config
        assert len(store.export(session_id)["events"]) == events_before
        agent.close()

    def test_refused_provider_changes_nothing(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        before_config = copy.deepcopy(agent.config)
        before_history = agent.history_snapshot()
        events_before = len(store.export(session_id)["events"])
        with pytest.raises(ValueError, match="cannot use"):
            agent.switch_model(provider="anthropic")
        assert agent.config == before_config
        assert agent.history_snapshot() == before_history
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
            agent.switch_model(provider="groq")
        assert agent.config == before
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["model_switched", "model_switch_reverted"]
        agent.close()

    def test_set_model_legacy_spelling_still_switches_and_journals(
            self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.set_model("changed", "http://localhost:2/v1")
        assert agent.config["model"] == "changed"
        assert agent.config["base_url"] == "http://localhost:2/v1"
        switches = [e for e in store.export(session_id)["events"]
                    if e["type"] == "model_switched"]
        assert len(switches) == 1
        assert switches[0]["to"]["model"] == "changed"
        assert switches[0]["reason"] is None
        agent.close()


# ----------------------------------------------------------------------
# The surfaces
# ----------------------------------------------------------------------

class TestTerminalSlash:
    def test_show(self, agent):
        from mythic_agent.terminal import _slash

        handled, quit_chat, text = _slash(agent, "/model")
        assert handled and not quit_chat
        assert "test-model" in text and "http://localhost:1/v1" in text

    def test_switch_with_provider_and_reason(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(
            agent, "/model --provider groq --reason cheaper scout")
        assert "llama-3.3-70b-versatile via groq" in text
        assert "Reason: cheaper scout" in text
        assert agent.config["model"] == "llama-3.3-70b-versatile"

    def test_legacy_positional_switch(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/model other http://localhost:9/v1")
        assert "Model changed to" not in text  # new shared sentence
        assert "other (http://localhost:9/v1)" in text
        assert agent.config["base_url"] == "http://localhost:9/v1"

    def test_refusal_is_the_message_and_nothing_changes(self, agent):
        from mythic_agent.terminal import _slash

        before = copy.deepcopy(agent.config)
        _, _, text = _slash(agent, "/model --provider anthropic")
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


class TestModelCommand:
    def test_show_is_default(self, handler, agent):
        handler._handle_model("")
        text = _published_text(handler)
        assert "test-model" in text and "http://localhost:1/v1" in text

    def test_switch_via_provider(self, handler, agent):
        handler._handle_model("--provider groq --reason speed")
        text = _published_text(handler)
        assert "llama-3.3-70b-versatile via groq" in text
        assert agent.config["model"] == "llama-3.3-70b-versatile"

    def test_refusal_is_published_verbatim(self, handler, agent):
        before = copy.deepcopy(agent.config)
        handler._handle_model("--provider ollama")
        assert "cannot use" in _published_text(handler)
        assert agent.config == before

    def test_usage_error_is_published(self, handler, agent):
        handler._handle_model("--bogus x")
        assert "Unknown switch flag" in _published_text(handler)


class TestChatScreenRouting:
    def test_model_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/model --provider groq", _FakeLog())
        assert calls == [("/model", "--provider groq")]
