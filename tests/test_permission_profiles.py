"""M-095 Permission profiles — pure-layer tests.

The shipped postures bind exactly what the roadmap names
(tools, paths, network, commands), custom postures are held
to the same vocabulary, decisions are mechanical, ask stays
ask, and the status line says the posture in one sentence.
"""

import pytest

from mythic_agent.core.permission_profiles import (
    BUILTIN_PROFILE_IDS,
    DEFAULT_PROFILE_ID,
    PLAIN_EXPLANATION,
    SETTING_KEY,
    builtin_profile,
    decide,
    format_permission_profile,
    policy_mode_for,
    profile_change_record,
    profile_named,
    stored_profile,
    validate_profile,
)

CUSTOM_SPEC = {
    "name": "night-watch",
    "title": "Night Watch",
    "tools": "read_only",
    "paths": "read",
    "network": "ask",
    "commands": "deny",
}


# -- the shipped postures --------------------------------------------


def test_three_shipped_postures_by_id():
    assert BUILTIN_PROFILE_IDS == (
        "read-only-scout",
        "trusted-forge",
        "full-autonomy",
    )


def test_scout_bindings():
    scout = builtin_profile("read-only-scout")
    assert scout.title == "Read-Only Scout"
    assert (scout.tools, scout.paths, scout.network, scout.commands) == (
        "read_only",
        "read",
        "deny",
        "deny",
    )
    assert scout.custom is False


def test_trusted_forge_bindings():
    forge = builtin_profile("trusted-forge")
    assert forge.title == "Trusted Forge"
    assert (forge.tools, forge.paths, forge.network, forge.commands) == (
        "all",
        "write",
        "ask",
        "ask",
    )


def test_full_autonomy_bindings():
    auto = builtin_profile("full-autonomy")
    assert auto.title == "Full Autonomy"
    assert (auto.tools, auto.paths, auto.network, auto.commands) == (
        "all",
        "write",
        "allow",
        "allow",
    )


def test_default_posture_is_trusted_forge():
    assert DEFAULT_PROFILE_ID == "trusted-forge"
    assert stored_profile({}).id == "trusted-forge"


def test_profile_named_by_title_case_insensitive():
    assert profile_named("trusted forge").id == "trusted-forge"
    assert profile_named("FULL AUTONOMY").id == "full-autonomy"
    assert profile_named(" read-only-scout ").id == "read-only-scout"


def test_profile_named_unknown_raises():
    with pytest.raises(ValueError):
        profile_named("root-shell")
    with pytest.raises(ValueError):
        profile_named("")
    with pytest.raises(ValueError):
        builtin_profile("nope")


# -- decisions ---------------------------------------------------------


def test_scout_decisions():
    scout = builtin_profile("read-only-scout")
    assert decide(scout, "tool", read_only_tool=True) == "allow"
    assert decide(scout, "tool", read_only_tool=False) == "deny"
    assert decide(scout, "path_read") == "allow"
    assert decide(scout, "path_write") == "deny"
    assert decide(scout, "network") == "deny"
    assert decide(scout, "command") == "deny"


def test_trusted_forge_ask_stays_ask():
    forge = builtin_profile("trusted-forge")
    assert decide(forge, "tool", read_only_tool=False) == "allow"
    assert decide(forge, "path_write") == "allow"
    assert decide(forge, "network") == "ask"
    assert decide(forge, "command") == "ask"


def test_full_autonomy_decisions():
    auto = builtin_profile("full-autonomy")
    assert decide(auto, "tool") == "allow"
    assert decide(auto, "path_write") == "allow"
    assert decide(auto, "network") == "allow"
    assert decide(auto, "command") == "allow"


def test_decide_unknown_kind_raises():
    with pytest.raises(ValueError):
        decide(builtin_profile("trusted-forge"), "teleport")


def test_policy_mode_mapping():
    assert policy_mode_for(builtin_profile("read-only-scout")) == "read-only"
    assert policy_mode_for(builtin_profile("trusted-forge")) == "ask"
    assert policy_mode_for(builtin_profile("full-autonomy")) == "trusted"


# -- custom postures ---------------------------------------------------


def test_custom_profile_validates():
    profile = validate_profile(dict(CUSTOM_SPEC))
    assert profile.id == "night-watch"
    assert profile.title == "Night Watch"
    assert profile.custom is True
    assert decide(profile, "network") == "ask"
    assert decide(profile, "command") == "deny"
    assert policy_mode_for(profile) == "read-only"


def test_custom_profile_unknown_key_refuses():
    spec = dict(CUSTOM_SPEC, telemetry="off")
    with pytest.raises(ValueError):
        validate_profile(spec)


def test_custom_profile_missing_binding_refuses():
    spec = dict(CUSTOM_SPEC)
    del spec["network"]
    with pytest.raises(ValueError):
        validate_profile(spec)


def test_custom_profile_bad_vocabulary_refuses():
    with pytest.raises(ValueError):
        validate_profile(dict(CUSTOM_SPEC, network="sometimes"))
    with pytest.raises(ValueError):
        validate_profile(dict(CUSTOM_SPEC, tools="some"))
    with pytest.raises(ValueError):
        validate_profile(dict(CUSTOM_SPEC, paths="everywhere"))


def test_custom_profile_may_not_impersonate_a_shipped_one():
    with pytest.raises(ValueError):
        validate_profile(dict(CUSTOM_SPEC, name="trusted-forge"))


def test_custom_profile_bad_names_refuse():
    for bad in ("Night Watch", "-lead", "has space", "x" * 41, ""):
        with pytest.raises(ValueError):
            validate_profile(dict(CUSTOM_SPEC, name=bad))


def test_validate_profile_non_mapping_refuses():
    with pytest.raises(ValueError):
        validate_profile("night-watch")


# -- stored posture ------------------------------------------------------


def test_stored_profile_named_and_custom():
    assert stored_profile({SETTING_KEY: "full-autonomy"}).id == "full-autonomy"
    custom = stored_profile({SETTING_KEY: dict(CUSTOM_SPEC)})
    assert custom.id == "night-watch"
    assert custom.custom is True


def test_stored_profile_malformed_raises():
    with pytest.raises(ValueError):
        stored_profile({SETTING_KEY: "root-shell"})
    with pytest.raises(ValueError):
        stored_profile({SETTING_KEY: 42})
    with pytest.raises(ValueError):
        stored_profile({SETTING_KEY: {"name": "trusted-forge"}})


# -- records and the status line ----------------------------------------


def test_profile_record_shape():
    record = builtin_profile("trusted-forge").to_record()
    assert record["type"] == "permission_profile"
    assert record["id"] == "trusted-forge"
    assert record["tools"] == "all"
    assert record["custom"] is False


def test_change_record_names_from_and_to():
    record = profile_change_record(
        builtin_profile("read-only-scout"), builtin_profile("full-autonomy")
    )
    assert record["type"] == "permission_profile_changed"
    assert record["from"] == "read-only-scout"
    assert record["to"] == "full-autonomy"
    first = profile_change_record(None, builtin_profile("trusted-forge"))
    assert first["from"] is None


def test_status_line_sentences():
    assert format_permission_profile({}) == (
        "Posture: Trusted Forge (tools: all · paths: read-write · "
        "network: ask · commands: ask)"
    )
    assert format_permission_profile({SETTING_KEY: "read-only-scout"}) == (
        "Posture: Read-Only Scout (tools: read-only · paths: "
        "read-only · network: deny · commands: deny)"
    )
    assert format_permission_profile({SETTING_KEY: "full-autonomy"}) == (
        "Posture: Full Autonomy (tools: all · paths: read-write · "
        "network: allow · commands: allow)"
    )
    assert format_permission_profile({SETTING_KEY: dict(CUSTOM_SPEC)}) == (
        "Posture: Night Watch (tools: read-only · paths: read-only · "
        "network: ask · commands: deny)"
    )


def test_plain_explanation_names_the_four_bindings():
    for word in ("tools", "write", "network", "commands"):
        assert word in PLAIN_EXPLANATION


# -- agent layer: status, set, surfaces (M-095) ------------------------

from mythic_agent.core import permission_profiles as pp
from mythic_agent.core.sessions import SessionStore


def _store_for(tmp_path):
    return SessionStore(tmp_path, tmp_path / "state")


class TestPostureParser:
    def test_show_is_the_default(self):
        assert pp.parse_posture_args("") == {"action": "show"}
        assert pp.parse_posture_args("show") == {"action": "show"}

    def test_named_posture_by_id_and_title(self):
        request = pp.parse_posture_args("read-only-scout")
        assert request["action"] == "set"
        assert request["profile"].id == "read-only-scout"
        request = pp.parse_posture_args("Full Autonomy")
        assert request["profile"].id == "full-autonomy"

    def test_unknown_name_refuses_and_names_the_shipped(self):
        with pytest.raises(ValueError, match="unknown permission profile"):
            pp.parse_posture_args("root-shell")

    def test_custom_posture_through_the_parser(self):
        request = pp.parse_posture_args(
            "custom night-watch | Night Watch | read_only | "
            "read | ask | deny")
        assert request["profile"].id == "night-watch"
        assert request["profile"].custom is True

    def test_custom_with_missing_fields_is_a_usage_error(self):
        with pytest.raises(ValueError, match="Usage: /posture"):
            pp.parse_posture_args("custom night-watch | Night Watch")


class TestPermissionProfileAgent:
    def test_status_defaults_to_trusted_forge(self, agent):
        status = agent.permission_profile_status()
        assert status["profile"]["id"] == "trusted-forge"
        assert status["policy_mode"] == "ask"
        assert status["status_line"] == (
            "Posture: Trusted Forge (tools: all · paths: "
            "read-write · network: ask · commands: ask)")
        assert status["explanation"] == pp.PLAIN_EXPLANATION

    def test_set_by_name_applies_the_policy_mode(self, agent):
        record = agent.set_permission_profile("read-only-scout")
        assert record["type"] == "permission_profile_changed"
        assert record["from"] == "trusted-forge"
        assert record["to"] == "read-only-scout"
        assert record["journaled"] is False
        assert agent.config["permission_profile"] == "read-only-scout"
        assert agent.tool_policy.mode == "read-only"
        record = agent.set_permission_profile("full-autonomy")
        assert record["from"] == "read-only-scout"
        assert agent.tool_policy.mode == "trusted"

    def test_set_custom_mapping_stores_the_whole_posture(self, agent):
        record = agent.set_permission_profile(dict(CUSTOM_SPEC))
        assert record["to"] == "night-watch"
        stored = agent.config["permission_profile"]
        assert stored["name"] == "night-watch"
        assert stored["network"] == "ask"
        status = agent.permission_profile_status()
        assert status["profile"]["custom"] is True
        assert status["policy_mode"] == "read-only"
        assert agent.tool_policy.mode == "read-only"

    def test_unknown_name_refuses_and_changes_nothing(self, agent):
        before_mode = agent.tool_policy.mode
        with pytest.raises(ValueError, match="unknown permission profile"):
            agent.set_permission_profile("root-shell")
        assert "permission_profile" not in agent.config
        assert agent.tool_policy.mode == before_mode

    def test_set_journals_on_the_session(self, agent, tmp_path):
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.set_permission_profile("full-autonomy")
        assert record["journaled"] is True
        events = [e for e in store.export(session_id)["events"]
                  if e["type"] == "permission_profile_changed"]
        assert len(events) == 1
        assert events[0]["from"] == "trusted-forge"
        assert events[0]["to"] == "full-autonomy"
        agent.close()

    def test_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        before_mode = agent.tool_policy.mode
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.set_permission_profile("full-autonomy")
        assert "permission_profile" not in agent.config
        assert agent.tool_policy.mode == before_mode
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["permission_profile_changed",
                              "permission_profile_reverted"]
        agent.close()


class TestPostureTerminalSurface:
    def test_show_lists_every_posture(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/posture")
        assert "Permission profiles (M-095)" in text
        assert "Posture: Trusted Forge" in text
        assert "Posture: Read-Only Scout" in text
        assert "Posture: Full Autonomy" in text
        assert "Tool policy mode: ask" in text

    def test_set_by_name_and_by_title(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/posture read-only-scout")
        assert text == ("Posture is now Read-Only Scout "
                        "(read-only-scout).")
        assert agent.tool_policy.mode == "read-only"
        _, _, text = _slash(agent, "/posture Full Autonomy")
        assert "Full Autonomy" in text
        assert agent.tool_policy.mode == "trusted"

    def test_set_custom_through_the_terminal(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(
            agent,
            "/posture custom night-watch | Night Watch | "
            "read_only | read | ask | deny")
        assert text == "Posture is now Night Watch (night-watch)."
        assert agent.permission_profile_status(
            )["profile"]["custom"] is True

    def test_unknown_name_is_the_message(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/posture root-shell")
        assert "unknown permission profile" in text
        assert "permission_profile" not in agent.config


@pytest.fixture()
def posture_handler(agent, monkeypatch):
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


def _posture_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestPostureCommand:
    def test_show_is_default(self, posture_handler, agent):
        posture_handler._handle_posture("")
        text = _posture_published_text(posture_handler)
        assert "Permission profiles (M-095)" in text
        assert "Posture: Trusted Forge" in text

    def test_set_via_the_handler(self, posture_handler, agent):
        posture_handler._handle_posture("read-only-scout")
        assert ("Posture is now Read-Only Scout "
                "(read-only-scout).") in _posture_published_text(
                    posture_handler)
        assert agent.tool_policy.mode == "read-only"

    def test_unknown_name_is_published(self, posture_handler, agent):
        posture_handler._handle_posture("root-shell")
        assert "unknown permission profile" in _posture_published_text(
            posture_handler)
