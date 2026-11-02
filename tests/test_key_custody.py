"""M-032 — Key custody via Kista.

TIER: integration

Covers the M-032 surface:

* the pure layer (``mythic_agent.core.key_custody``): a config
  ``api_keys`` value may be a Kista reference (``kista:<name>``)
  instead of a secret — names are validated, malformed
  references raise; references resolve through Kista's vault
  file first, then the environment under the reference's own
  name; a name Kista does not hold resolves to None and no
  other door's key is substituted,
* custody status: every door's key location is named (kista /
  environment / legacy plaintext / missing / not-needed) with
  its presence, and no key value ever appears in a status,
  a record, a journal event, or a formatted surface,
* adoption: a legacy plaintext key is deposited in the vault
  file (private permissions) and the config is left holding
  only the reference — refused plainly, changing nothing,
  when the door already holds a reference, stores no key, has
  no vault configured, or would collide with a different key
  under the same name,
* ``Agent`` changes: ``kista_status`` and
  ``adopt_key_for_kista`` (journaled ``key_custody_changed``,
  a failed save restores the config and journals the revert),
  and ``resolve_api_key`` reading through custody,
* the surfaces: the terminal ``/kista`` and the TUI ``/kista``
  (system-command road), sharing the parser and formatters,
* the config contract: ``MYTHIC_KISTA_FILE`` is catalogued
  (M-009) and the ``api_keys`` catalogue entry tells the
  Kista truth.
"""

from __future__ import annotations

import json
import os
import stat

import pytest

from mythic_agent.core.key_custody import (
    PLAIN_EXPLANATION,
    VAULT_ENV,
    adopt,
    custody_entries,
    deposit,
    format_custody,
    format_custody_change,
    is_reference,
    key_env_for,
    load_vault,
    make_reference,
    missing_key_message,
    parse_kista_args,
    plan_adoption,
    reference_name,
    resolve_reference,
    stored_key_for,
    suggested_reference,
    vault_path,
)
from mythic_agent.core.sessions import SessionStore

DEEPSEEK = "https://api.deepseek.com/v1"
OPENAI = "https://api.openai.com/v1"
SECRET = "fixture-key-0123456789abcdef"
OTHER_SECRET = "fixture-other-key-fedcba9876543210"


def store_for(tmp_path, workspace=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state")


def config_with(stored=SECRET, base_url=DEEPSEEK):
    return {"model": "deepseek-chat", "base_url": base_url,
            "api_keys": {base_url: stored} if stored is not None else {}}


# ----------------------------------------------------------------------
# References: names, never secrets
# ----------------------------------------------------------------------

class TestReferences:
    def test_is_reference(self):
        assert is_reference("kista:DEEPSEEK_API_KEY")
        assert not is_reference(SECRET)
        assert not is_reference(None)
        assert not is_reference(42)

    def test_make_and_read_a_reference(self):
        ref = make_reference("DEEPSEEK_API_KEY")
        assert ref == "kista:DEEPSEEK_API_KEY"
        assert reference_name(ref) == "DEEPSEEK_API_KEY"

    @pytest.mark.parametrize("bad", [
        "kista:", "kista:  ", "kista:has space", "kista:key=value",
        "plain-name", "", None, 7,
    ])
    def test_malformed_references_raise(self, bad):
        with pytest.raises(ValueError):
            reference_name(bad)

    @pytest.mark.parametrize("bad", [
        "has space", "key=value", "", "  ", "-leading-dash", None, 7,
    ])
    def test_invalid_key_names_raise(self, bad):
        with pytest.raises(ValueError):
            make_reference(bad)

    def test_suggested_reference_comes_from_the_registry(self):
        assert suggested_reference(DEEPSEEK) == "kista:DEEPSEEK_API_KEY"
        assert suggested_reference(OPENAI) == "kista:OPENAI_API_KEY"
        assert key_env_for("https://api.anthropic.com/v1") == \
            "ANTHROPIC_API_KEY"
        # A custom door falls back to the compatible default name.
        assert key_env_for("http://localhost:9999/v1") == "OPENAI_API_KEY"


# ----------------------------------------------------------------------
# Resolution through Kista's doors
# ----------------------------------------------------------------------

class TestResolution:
    def test_environment_resolves_under_the_references_own_name(self):
        env = {"DEEPSEEK_API_KEY": SECRET}
        assert resolve_reference("kista:DEEPSEEK_API_KEY",
                                 environ=env) == SECRET

    def test_vault_file_answers_before_the_environment(self, tmp_path):
        vault = tmp_path / "kista.json"
        vault.write_text(json.dumps({"DEEPSEEK_API_KEY": SECRET}))
        env = {"DEEPSEEK_API_KEY": OTHER_SECRET}
        assert resolve_reference("kista:DEEPSEEK_API_KEY",
                                 environ=env, vault_file=vault) == SECRET

    def test_unheld_name_resolves_to_none_never_another_key(self):
        env = {"OPENAI_API_KEY": OTHER_SECRET, "DEEPSEEK_API_KEY": ""}
        assert resolve_reference("kista:DEEPSEEK_API_KEY",
                                 environ=env) is None

    def test_vault_path_comes_from_the_environment(self, tmp_path):
        target = tmp_path / "vault.json"
        assert vault_path(environ={}) is None
        assert vault_path(environ={VAULT_ENV: str(target)}) == target
        assert vault_path(str(target), environ={}) == target

    def test_malformed_vault_raises_naming_the_file(self, tmp_path):
        vault = tmp_path / "kista.json"
        vault.write_text("{not json")
        with pytest.raises(ValueError, match="Kista vault file"):
            load_vault(vault)
        vault.write_text(json.dumps({"NAME": 42}))
        with pytest.raises(ValueError, match="must hold a JSON object"):
            load_vault(vault)
        assert SECRET not in str(load_vault.__doc__ or "")

    def test_missing_vault_file_is_an_empty_vault(self, tmp_path):
        assert load_vault(tmp_path / "absent.json") == {}

    def test_deposit_writes_a_private_vault(self, tmp_path):
        vault = tmp_path / "sub" / "kista.json"
        assert deposit(vault, "DEEPSEEK_API_KEY", SECRET) == \
            "DEEPSEEK_API_KEY"
        assert load_vault(vault) == {"DEEPSEEK_API_KEY": SECRET}
        mode = stat.S_IMODE(os.stat(vault).st_mode)
        assert mode == 0o600

    def test_stored_key_for_reads_references_and_legacy(self):
        env = {"DEEPSEEK_API_KEY": SECRET}
        cfg = config_with("kista:DEEPSEEK_API_KEY")
        assert stored_key_for(cfg, DEEPSEEK, environ=env) == SECRET
        assert stored_key_for(cfg, DEEPSEEK, environ={}) is None
        legacy = config_with(SECRET)
        assert stored_key_for(legacy, DEEPSEEK, environ={}) == SECRET
        assert stored_key_for(config_with(None), DEEPSEEK,
                              environ=env) is None


# ----------------------------------------------------------------------
# Custody status — where keys live, never what they are
# ----------------------------------------------------------------------

class TestCustodyStatus:
    def test_kista_door_present_and_absent(self):
        cfg = config_with("kista:DEEPSEEK_API_KEY")
        (entry,) = custody_entries(cfg, environ={"DEEPSEEK_API_KEY": SECRET})
        assert entry.custody == "kista"
        assert entry.present is True
        assert entry.reference == "kista:DEEPSEEK_API_KEY"
        (entry,) = custody_entries(cfg, environ={})
        assert entry.custody == "kista"
        assert entry.present is False

    def test_legacy_plaintext_is_named_what_it_is(self):
        (entry,) = custody_entries(config_with(SECRET), environ={})
        assert entry.custody == "plaintext"
        assert entry.present is True
        assert "plain text" in entry.describe()

    def test_current_door_answers_environment_missing_loopback(self):
        cfg = {"model": "m", "base_url": DEEPSEEK, "api_keys": {}}
        (entry,) = custody_entries(cfg, environ={"DEEPSEEK_API_KEY": SECRET})
        assert (entry.custody, entry.present) == ("environment", True)
        (entry,) = custody_entries(cfg, environ={})
        assert (entry.custody, entry.present) == ("missing", False)
        local = {"model": "m", "base_url": "http://localhost:11434",
                 "api_keys": {}}
        (entry,) = custody_entries(local, environ={})
        assert (entry.custody, entry.present) == ("not-needed", True)

    def test_malformed_stored_reference_raises(self):
        with pytest.raises(ValueError, match="Malformed Kista"):
            custody_entries(config_with("kista:has space"), environ={})

    def test_no_key_value_ever_appears_in_status_output(self):
        cfg = config_with(SECRET)
        cfg["api_keys"]["https://api.openai.com/v1"] = \
            "kista:OPENAI_API_KEY"
        text = format_custody(cfg, environ={"OPENAI_API_KEY": OTHER_SECRET})
        assert SECRET not in text
        assert OTHER_SECRET not in text
        assert PLAIN_EXPLANATION in text
        assert "plain text" in text
        assert "kista:OPENAI_API_KEY" in text
        for entry in custody_entries(
                cfg, environ={"OPENAI_API_KEY": OTHER_SECRET}):
            assert SECRET not in json.dumps(entry.record())
            assert OTHER_SECRET not in json.dumps(entry.record())


# ----------------------------------------------------------------------
# Adoption — a plaintext key moves into Kista
# ----------------------------------------------------------------------

class TestAdoption:
    def test_adopt_deposits_and_returns_only_the_reference(self, tmp_path):
        vault = tmp_path / "kista.json"
        cfg = config_with(SECRET)
        reference, change = adopt(cfg, vault_file=vault)
        assert reference == "kista:DEEPSEEK_API_KEY"
        assert load_vault(vault) == {"DEEPSEEK_API_KEY": SECRET}
        # Pure regarding config: the secret still sits in the
        # caller's config until the caller writes the reference.
        assert cfg["api_keys"][DEEPSEEK] == SECRET
        assert change.event() == {
            "type": "key_custody_changed", "base_url": DEEPSEEK,
            "reference": "kista:DEEPSEEK_API_KEY"}
        assert SECRET not in json.dumps(change.event())

    def test_adopt_refuses_a_door_already_in_kista(self, tmp_path):
        cfg = config_with("kista:DEEPSEEK_API_KEY")
        with pytest.raises(ValueError, match="already lives in Kista"):
            adopt(cfg, vault_file=tmp_path / "k.json")

    def test_adopt_refuses_when_nothing_is_stored(self, tmp_path):
        with pytest.raises(ValueError, match="nothing to move"):
            adopt(config_with(None), vault_file=tmp_path / "k.json")

    def test_adopt_refuses_without_a_vault_and_changes_nothing(
            self, tmp_path):
        cfg = config_with(SECRET)
        with pytest.raises(ValueError, match="not configured"):
            plan_adoption(cfg, environ={})
        assert not (tmp_path / "k.json").exists()

    def test_adopt_refuses_a_name_collision(self, tmp_path):
        vault = tmp_path / "kista.json"
        vault.write_text(json.dumps({"DEEPSEEK_API_KEY": OTHER_SECRET}))
        with pytest.raises(ValueError, match="different key"):
            adopt(config_with(SECRET), vault_file=vault)
        assert load_vault(vault) == {"DEEPSEEK_API_KEY": OTHER_SECRET}

    def test_adopt_the_same_key_twice_is_harmless(self, tmp_path):
        vault = tmp_path / "kista.json"
        adopt(config_with(SECRET), vault_file=vault)
        reference, _ = adopt(config_with(SECRET), vault_file=vault)
        assert reference == "kista:DEEPSEEK_API_KEY"
        assert load_vault(vault) == {"DEEPSEEK_API_KEY": SECRET}


# ----------------------------------------------------------------------
# The missing-key remedy and the /kista grammar + formatters
# ----------------------------------------------------------------------

class TestRemedyAndGrammar:
    def test_missing_key_message_asks_once_kindly(self):
        text = missing_key_message(DEEPSEEK)
        assert "No API key configured" in text
        assert "kista:DEEPSEEK_API_KEY" in text
        assert "export DEEPSEEK_API_KEY" in text
        assert SECRET not in text

    def test_loopback_needs_no_key(self):
        assert "need no key" in missing_key_message(
            "http://localhost:11434")

    @pytest.mark.parametrize("text,action,target", [
        ("", "show", None), ("show", "show", None),
        ("adopt", "adopt", None),
        ("adopt https://api.openai.com/v1", "adopt", OPENAI),
    ])
    def test_parse_actions(self, text, action, target):
        request = parse_kista_args(text)
        assert request["action"] == action
        assert request["base_url"] == target

    def test_parse_rejects_unknown_and_extra_words(self):
        with pytest.raises(ValueError, match="Usage"):
            parse_kista_args("steal")
        with pytest.raises(ValueError, match="Usage"):
            parse_kista_args("adopt two words here")
        with pytest.raises(ValueError, match="must be text"):
            parse_kista_args(9)

    def test_format_custody_change_sentence(self):
        record = {"base_url": DEEPSEEK,
                  "reference": "kista:DEEPSEEK_API_KEY",
                  "session_id": "s" * 32}
        text = format_custody_change(record)
        assert "now lives in Kista" in text
        assert "holds only that reference" in text
        assert SECRET not in text


# ----------------------------------------------------------------------
# Agent custody: status, adoption, resolution
# ----------------------------------------------------------------------

class TestAgentCustody:
    def _agent_with_key(self, agent, monkeypatch, tmp_path):
        vault = tmp_path / "kista.json"
        monkeypatch.setenv(VAULT_ENV, str(vault))
        agent.config.update({
            "model": "deepseek-chat", "base_url": DEEPSEEK,
            "api_keys": {DEEPSEEK: SECRET}})
        return vault

    def test_status_names_plaintext_and_the_vault(self, agent,
                                                   monkeypatch, tmp_path):
        self._agent_with_key(agent, monkeypatch, tmp_path)
        status = agent.kista_status()
        assert status["vault_configured"] is True
        (entry,) = status["entries"]
        assert entry["custody"] == "plaintext"
        assert entry["present"] is True
        assert SECRET not in json.dumps(status)

    def test_adopt_journals_and_leaves_only_the_reference(
            self, agent, monkeypatch, tmp_path):
        vault = self._agent_with_key(agent, monkeypatch, tmp_path)
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.adopt_key_for_kista()
        assert record["reference"] == "kista:DEEPSEEK_API_KEY"
        assert record["journaled"] is True
        assert agent.config["api_keys"][DEEPSEEK] == \
            "kista:DEEPSEEK_API_KEY"
        assert load_vault(vault) == {"DEEPSEEK_API_KEY": SECRET}
        events = store.export(session_id)["events"]
        custody = [e for e in events
                   if e["type"] == "key_custody_changed"]
        assert len(custody) == 1
        assert SECRET not in json.dumps(events)
        # And the session now resolves its key through Kista.
        assert agent.get_api_key(DEEPSEEK) == SECRET
        agent.close()

    def test_adopt_without_session_still_moves_the_key(
            self, agent, monkeypatch, tmp_path):
        vault = self._agent_with_key(agent, monkeypatch, tmp_path)
        record = agent.adopt_key_for_kista()
        assert record["journaled"] is False
        assert load_vault(vault) == {"DEEPSEEK_API_KEY": SECRET}

    def test_save_failure_restores_config_and_journals_revert(
            self, agent, monkeypatch, tmp_path):
        from mythic_agent.agents import llm

        self._agent_with_key(agent, monkeypatch, tmp_path)
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.adopt_key_for_kista()
        assert agent.config["api_keys"][DEEPSEEK] == SECRET
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["key_custody_changed",
                              "key_custody_reverted"]
        agent.close()

    def test_resolve_api_key_reads_through_kista(
            self, agent, monkeypatch, tmp_path):
        from mythic_agent.agents.llm import resolve_api_key

        vault = tmp_path / "kista.json"
        vault.write_text(json.dumps({"DEEPSEEK_API_KEY": SECRET}))
        monkeypatch.setenv(VAULT_ENV, str(vault))
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        cfg = config_with("kista:DEEPSEEK_API_KEY")
        assert resolve_api_key(cfg, DEEPSEEK) == SECRET

    def test_unresolved_reference_never_falls_back_to_the_hint(
            self, monkeypatch):
        from mythic_agent.agents.llm import resolve_api_key

        monkeypatch.setenv("DEEPSEEK_API_KEY", OTHER_SECRET)
        monkeypatch.delenv(VAULT_ENV, raising=False)
        cfg = config_with("kista:SOME_OTHER_KEY")
        # The reference names SOME_OTHER_KEY, which Kista does
        # not hold; the door's own hint variable must not be
        # substituted for the key the reference names.
        assert resolve_api_key(cfg, DEEPSEEK) is None


# ----------------------------------------------------------------------
# Surfaces
# ----------------------------------------------------------------------

class TestTerminalSurface:
    def test_show_and_adopt(self, agent, monkeypatch, tmp_path):
        from mythic_agent.terminal import _slash

        vault = tmp_path / "kista.json"
        monkeypatch.setenv(VAULT_ENV, str(vault))
        agent.config.update({
            "model": "deepseek-chat", "base_url": DEEPSEEK,
            "api_keys": {DEEPSEEK: SECRET}})
        _, _, text = _slash(agent, "/kista")
        assert "Key custody (Kista)" in text
        assert "plain text" in text
        assert SECRET not in text
        _, _, text = _slash(agent, "/kista adopt")
        assert "now lives in Kista" in text
        assert agent.config["api_keys"][DEEPSEEK] == \
            "kista:DEEPSEEK_API_KEY"
        _, _, text = _slash(agent, "/kista adopt")
        assert "already lives in Kista" in text

    def test_usage_error_is_the_message(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/kista steal")
        assert "Usage" in text


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


class TestKistaCommand:
    def test_show_is_default(self, handler, agent):
        handler._handle_kista("")
        text = _published_text(handler)
        assert "Key custody (Kista)" in text
        assert "no key held" in text or "no key needed" in text

    def test_adopt_through_the_handler(self, handler, agent,
                                       monkeypatch, tmp_path):
        vault = tmp_path / "kista.json"
        monkeypatch.setenv(VAULT_ENV, str(vault))
        agent.config.update({
            "model": "deepseek-chat", "base_url": DEEPSEEK,
            "api_keys": {DEEPSEEK: SECRET}})
        handler._handle_kista("adopt")
        text = _published_text(handler)
        assert "now lives in Kista" in text
        assert SECRET not in text
        assert load_vault(vault) == {"DEEPSEEK_API_KEY": SECRET}
