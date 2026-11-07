"""M-119 - Policy as code.

TIER: integration

The checked-in project policy file
(``mythic-policy.yaml`` +
``mythic_agent.core.policy_file``): posture,
jail + grants and hooks in one file, in the
exact shapes the shipped M-095 / M-099 / M-101
roads consume, so a team's rules travel with
the repo.

These tests do not take the layer's word for
any of it:

* the shipped example policy loads and
  validates clean, and answers the queued
  M-119 roadmap entry,
* every section round-trips into the exact
  settings shapes the real roads consume,
  proved through the roads' own readers and
  validators (stored_profile, jail readers,
  hooks_from_config) - never copies,
* the validator refuses, each as its own
  test: an unknown posture name, a malformed
  custom posture, a non-absolute jail grant,
  a hook record M-101 refuses, unknown
  top-level and jail keys, a wrong schema,
  a policy that turns the jail off, and a
  grant of the filesystem root,
* no file and an empty policy both yield no
  plan - never an invented default,
* the application plan is data-only and
  complete: every section in the file appears
  under its shipped settings key, nothing
  extra appears,
* live re-proofs compose the real roads: a
  policy posture feeds the real M-095
  decide(), and a policy grant feeds the real
  M-099 check_path(),
* and a module-purity pin holds the layer to
  data only: no agent / UI imports, no file
  writes, no session state.
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from mythic_agent.core.hooks import hooks_from_config
from mythic_agent.core.path_jail import (
    check_path,
    enabled_from_config,
    grants_from_config,
)
from mythic_agent.core.permission_profiles import decide, stored_profile
from mythic_agent.core.policy_file import (
    EXAMPLE_RESOURCE,
    PLAIN_EXPLANATION,
    POLICY_FILENAME,
    POLICY_FILE_SLICE,
    POLICY_SCHEMA,
    USAGE,
    PolicyRegistry,
    application_plan,
    default_policy_path,
    format_plan,
    format_policy,
    format_policy_screen,
    load_example_policy,
    load_policy_file,
    parse_policy_args,
    plain_words,
    policy_record,
    validate_policy,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource

REPO_ROOT = Path(__file__).resolve().parent.parent

EXAMPLE = {
    "schema": POLICY_SCHEMA,
    "name": "example-forge-policy",
    "posture": "trusted-forge",
    "jail": {"enabled": True, "grants": ["/srv/shared-assets"]},
    "hooks": [{
        "event": "pre_tool",
        "command": "python3 scripts/policy_check.py",
        "name": "example-check",
        "enabled": True,
        "timeout_seconds": 30,
    }],
}


def _example():
    return copy.deepcopy(EXAMPLE)


def test_roadmap_entry_is_the_queued_m119_slice():
    roadmap = load_roadmap()
    entry = roadmap.slice("M-119")
    assert entry.title == "Policy as code"
    assert POLICY_FILE_SLICE == "M-119"
    assert POLICY_FILENAME == "mythic-policy.yaml"


def test_shipped_example_loads_and_validates_clean():
    policy = load_example_policy()
    assert policy.name == "example-forge-policy"
    assert policy.sections == ("posture", "jail", "hooks")
    assert policy.posture is not None
    assert policy.posture.id == "trusted-forge"
    assert policy.jail_enabled is True
    assert policy.grants == ("/srv/shared-assets",)
    assert policy.hooks is not None and len(policy.hooks) == 1
    # The shipped resource is exactly the example shape.
    assert load_resource(EXAMPLE_RESOURCE) == EXAMPLE


def test_sections_round_trip_through_the_real_roads():
    plan = application_plan(validate_policy(_example()))
    settings = plan.settings()
    # Posture: the plan value is what M-095's stored road reads.
    assert stored_profile(settings).id == "trusted-forge"
    # Jail: the plan values are what M-099's config readers read.
    assert enabled_from_config(settings) is True
    assert grants_from_config(settings) == ("/srv/shared-assets",)
    # Hooks: the plan value is what M-101's config reader reads.
    hooks = hooks_from_config(settings)
    assert len(hooks) == 1
    assert hooks[0].event == "pre_tool"
    assert hooks[0].to_record() == EXAMPLE["hooks"][0]


def test_custom_posture_round_trips_in_the_m095_shape():
    data = _example()
    data["posture"] = {
        "name": "night-watch", "title": "Night Watch",
        "tools": "read_only", "paths": "read",
        "network": "deny", "commands": "deny",
    }
    policy = validate_policy(data)
    settings = application_plan(policy).settings()
    profile = stored_profile(settings)
    assert profile.custom is True
    assert profile.id == "night-watch"
    assert settings["permission_profile"] == data["posture"]


def test_plan_is_complete_and_carries_nothing_extra():
    plan = application_plan(validate_policy(_example()))
    assert plan.keys() == (
        "permission_profile", "path_jail", "path_grants", "hooks")
    partial = validate_policy({"posture": "read-only-scout"})
    assert application_plan(partial).keys() == ("permission_profile",)
    assert application_plan(partial).settings() == {
        "permission_profile": "read-only-scout"}


def test_no_file_means_no_policy_and_no_plan(tmp_path):
    missing = default_policy_path(tmp_path)
    assert load_policy_file(missing) is None
    assert format_policy(None).startswith("No project policy")
    assert format_plan(None) == "No project policy: no plan."


def test_empty_policy_means_empty_plan():
    for data in ({}, None, {"schema": POLICY_SCHEMA}):
        policy = validate_policy(data)
        assert policy.sections == ()
        plan = application_plan(policy)
        assert plan.empty and plan.settings() == {}


def test_load_policy_file_from_disk(tmp_path):
    target = default_policy_path(tmp_path)
    target.write_text(
        "schema: mythic.policy_file/1\nname: disk-policy\n"
        "posture: read-only-scout\n", encoding="utf-8")
    policy = load_policy_file(target)
    assert policy is not None and policy.name == "disk-policy"
    assert policy.posture is not None
    assert policy.posture.id == "read-only-scout"
    empty = tmp_path / "empty.yaml"
    empty.write_text("", encoding="utf-8")
    loaded = load_policy_file(empty)
    assert loaded is not None and loaded.sections == ()


def test_refuses_unknown_posture_name():
    data = _example()
    data["posture"] = "no-such-posture"
    with pytest.raises(ValidationError):
        validate_policy(data)


def test_refuses_malformed_custom_posture():
    data = _example()
    data["posture"] = {
        "name": "night-watch", "title": "Night Watch",
        "tools": "everything", "paths": "read",
        "network": "deny", "commands": "deny",
    }
    with pytest.raises(ValidationError):
        validate_policy(data)
    data["posture"] = {"name": "trusted-forge", "title": "Fake",
                        "tools": "all", "paths": "write",
                        "network": "ask", "commands": "ask"}
    with pytest.raises(ValidationError):
        validate_policy(data)


def test_refuses_relative_jail_grant():
    data = _example()
    data["jail"] = {"enabled": True, "grants": ["relative/dir"]}
    with pytest.raises(ValidationError):
        validate_policy(data)


def test_refuses_hook_record_m101_refuses():
    data = _example()
    data["hooks"] = [{"event": "no_such_event", "command": "x"}]
    with pytest.raises(ValidationError):
        validate_policy(data)
    data["hooks"] = [{"event": "pre_tool"}]
    with pytest.raises(ValidationError):
        validate_policy(data)
    data["hooks"] = [{"event": "pre_tool", "command": "x",
                       "bogus": 1}]
    with pytest.raises(ValidationError):
        validate_policy(data)


def test_refuses_unknown_top_level_key():
    data = _example()
    data["surprise_setting"] = True
    with pytest.raises(ValidationError):
        validate_policy(data)


def test_refuses_unknown_jail_key():
    data = _example()
    data["jail"] = {"enabled": True, "extra": 1}
    with pytest.raises(ValidationError):
        validate_policy(data)


def test_refuses_wrong_schema_and_non_mapping():
    data = _example()
    data["schema"] = "mythic.policy_file/99"
    with pytest.raises(ValidationError):
        validate_policy(data)
    with pytest.raises(ValidationError):
        validate_policy(["not", "a", "mapping"])


def test_refuses_policy_that_turns_the_jail_off():
    data = _example()
    data["jail"] = {"enabled": False, "grants": []}
    with pytest.raises(ValidationError) as caught:
        validate_policy(data)
    assert "may not be turned off" in str(caught.value)


def test_refuses_filesystem_root_grant():
    data = _example()
    data["jail"] = {"enabled": True, "grants": ["/"]}
    with pytest.raises(ValidationError) as caught:
        validate_policy(data)
    assert "filesystem root" in str(caught.value)


def test_malformed_yaml_file_refuses(tmp_path):
    target = default_policy_path(tmp_path)
    target.write_text("posture: [unclosed\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_policy_file(target)


def test_live_reproof_posture_feeds_real_decide(tmp_path):
    policy = validate_policy({"posture": "read-only-scout"})
    settings = application_plan(policy).settings()
    profile = stored_profile(settings)
    assert decide(profile, "path_write") == "deny"
    assert decide(profile, "network") == "deny"
    assert decide(profile, "tool", read_only_tool=True) == "allow"
    assert decide(profile, "tool", read_only_tool=False) == "deny"


def test_live_reproof_grant_feeds_real_path_jail(tmp_path):
    workspace = tmp_path / "ws"
    granted = tmp_path / "granted"
    granted.mkdir()
    (workspace).mkdir()
    data = _example()
    data["jail"] = {"enabled": True, "grants": [str(granted)]}
    settings = application_plan(validate_policy(data)).settings()
    grants = grants_from_config(settings)
    inside = check_path(str(granted / "note.txt"), str(workspace), grants)
    assert inside.allowed and inside.granted_by == str(granted)
    outside = check_path("/etc/hostname", str(workspace), grants)
    assert not outside.allowed


def test_record_and_plain_words():
    policy = validate_policy(_example())
    record = policy_record(policy)
    assert record["type"] == "project_policy"
    assert record["news"] is True
    assert record["slice"] == "M-119"
    assert record["plan_keys"] == [
        "permission_profile", "path_jail", "path_grants", "hooks"]
    assert "Trusted Forge" in plain_words(policy)
    assert "no sections" in plain_words(validate_policy({}))
    assert PLAIN_EXPLANATION and USAGE.startswith("Usage: /policy")


def test_registry_deterministic_ids():
    registry = PolicyRegistry()
    first = registry.register(validate_policy({"posture": "trusted-forge"}))
    second = registry.register(validate_policy({}))
    assert (first, second) == ("policy-1", "policy-2")
    assert registry.policy_ids() == ("policy-1", "policy-2")
    assert registry.get("policy-1").posture.id == "trusted-forge"
    named = registry.register(validate_policy({}), policy_id="policy-9")
    assert named == "policy-9"
    with pytest.raises(ValidationError):
        registry.register(validate_policy({}), policy_id="policy-9")
    with pytest.raises(KeyError):
        registry.get("policy-99")


def test_parser_and_formatters():
    assert parse_policy_args("") == {"action": "show"}
    assert parse_policy_args("show") == {"action": "show"}
    assert parse_policy_args("plan") == {"action": "plan"}
    assert parse_policy_args("sections") == {"action": "sections"}
    with pytest.raises(ValidationError):
        parse_policy_args("frobnicate")
    policy = validate_policy(_example())
    screen = format_policy_screen(policy)
    assert "Policy as code (M-119)" in screen
    assert "path_grants" in format_plan(policy)
    assert "example-check" in format_policy(policy)


def test_module_purity():
    import inspect

    import mythic_agent.core.policy_file as module

    source = inspect.getsource(module)
    body = source.split('"""', 2)[-1]
    assert "import subprocess" not in source
    assert "from mythic_agent.agents" not in source
    assert "from mythic_agent.ui" not in source
    assert "from .agent" not in source
    assert "open(" not in body
    assert "ToolPolicy(" not in body
    assert not hasattr(module, "SESSION")


# -- pure parser extension (agent-layer vocabulary) -----------------------


def test_parser_apply_and_load_verbs():
    assert parse_policy_args("apply") == {"action": "apply"}
    assert parse_policy_args("load") == {"action": "apply"}
    assert parse_policy_args("APPLY") == {"action": "apply"}
    assert "apply" in USAGE


def test_sections_formatter():
    from mythic_agent.core.policy_file import format_policy_sections
    policy = validate_policy(_example())
    text = format_policy_sections(policy)
    assert "posture" in text and "jail" in text and "hooks" in text
    assert "no sections" in format_policy_sections(validate_policy({}))
    assert "No project policy" in format_policy_sections(None)


# -- agent layer -----------------------------------------------------------
#
# The agent holds a PolicyRegistry for the session
# (session state only, no new setting): the policy
# file at the workspace root is loaded whole through
# the pure layer, a valid policy's plan is applied in
# the fixed order posture, jail + grants, hooks - each
# step through its own shipped journal-first road - and
# the applied policy is published as policy_record
# session news, deduped per policy record id. No file
# is a plain no-policy outcome; an invalid file is
# refused whole, applying nothing.

import os as _os

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _write_policy(agent, data):
    import yaml
    path = Path(agent.project_root) / POLICY_FILENAME
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def _policy_data(grant):
    return {
        "schema": POLICY_SCHEMA,
        "name": "team-policy",
        "posture": "read-only-scout",
        "jail": {"enabled": True, "grants": [str(grant)]},
        "hooks": [{
            "event": "pre_tool",
            "command": "python3 scripts/policy_check.py",
            "name": "team-check",
            "enabled": True,
            "timeout_seconds": 30,
        }],
    }


def _events(store, session_id, type_name):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == type_name]


class TestPolicyAgentStatus:
    def test_status_starts_with_no_policy(self, agent):
        status = agent.project_policy_status()
        assert status["held"] == []
        assert status["disk"] is None
        assert status["refusal"] is None
        assert "No project policy" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        assert (agent._policy_registry()
                is agent._policy_registry())
        assert agent._policy_store is agent._policy_registry()

    def test_unknown_policy_raises_keyerror(self, agent):
        with pytest.raises(KeyError):
            agent.get_project_policy("policy-99")

    def test_status_read_registers_and_publishes_nothing(
            self, agent, tmp_path):
        grant = tmp_path / "shared"
        grant.mkdir()
        _write_policy(agent, _policy_data(grant))
        status = agent.project_policy_status()
        assert status["disk"]["name"] == "team-policy"
        assert agent._policy_registry().policy_ids() == ()
        assert "permission_profile" not in agent.config


class TestPolicyAgentApply:
    def test_no_file_is_a_plain_no_op(self, agent):
        before = copy.deepcopy(agent.config)
        outcome = agent.apply_project_policy()
        assert outcome["status"] == "no_policy"
        assert outcome["steps"] == []
        assert "No project policy" in outcome["headline"]
        assert agent.config == before
        assert agent._policy_registry().policy_ids() == ()

    def test_valid_policy_applies_through_the_real_roads(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        grant = tmp_path / "shared"
        grant.mkdir()
        _write_policy(agent, _policy_data(grant))
        outcome = agent.apply_project_policy()
        assert outcome["status"] == "applied"
        assert outcome["policy_id"] == "policy-1"
        steps = {s["step"]: s["status"] for s in outcome["steps"]}
        assert steps == {"posture": "applied", "jail": "satisfied",
                         "grants": "applied", "hooks": "applied"}
        # The plan landed in the real settings, via the real roads.
        assert agent.config["permission_profile"] == "read-only-scout"
        assert agent.config["path_grants"] == [
            _os.path.realpath(grant)]
        assert agent.config["hooks"][0]["name"] == "team-check"
        assert agent.get_project_policy("policy-1").name == "team-policy"
        # The posture effect is live through the real M-095 judge.
        profile = stored_profile(agent.config)
        assert decide(profile, "command") == "deny"
        assert agent.permission_profile_status()["policy_mode"] == (
            "read-only")
        # The jail effect is live through the real M-099 judge.
        inside = agent.check_path_jail(str(grant / "note.txt"))
        assert inside.allowed
        outside = agent.check_path_jail("/etc/hostname")
        assert not outside.allowed
        # The applied policy was published once, as session news.
        events = _events(store, session_id, "project_policy")
        assert len(events) == 1
        assert events[0]["policy_id"] == "policy-1"
        assert events[0]["news"] is True
        assert events[0]["applied"] is True
        agent._publish_policy_record(outcome["record"])
        assert len(_events(store, session_id, "project_policy")) == 1
        agent.close()

    def test_reapply_is_satisfied_and_publishes_per_record_id(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        grant = tmp_path / "shared"
        grant.mkdir()
        _write_policy(agent, _policy_data(grant))
        agent.apply_project_policy()
        outcome = agent.apply_project_policy()
        assert outcome["policy_id"] == "policy-2"
        steps = {s["step"]: s["status"] for s in outcome["steps"]}
        assert steps == {"posture": "satisfied", "jail": "satisfied",
                         "grants": "applied", "hooks": "satisfied"}
        grant_steps = [s for s in outcome["steps"]
                       if s["step"] == "grants"][0]["grants"]
        assert grant_steps[0]["status"] == "satisfied"
        assert len(_events(store, session_id, "project_policy")) == 2
        agent.close()

    def test_session_start_loads_the_policy(self, agent, tmp_path):
        grant = tmp_path / "shared"
        grant.mkdir()
        _write_policy(agent, _policy_data(grant))
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        assert agent.config["permission_profile"] == "read-only-scout"
        assert len(_events(store, session_id, "project_policy")) == 1
        agent.close()

    def test_invalid_policy_is_refused_whole(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        data = _policy_data(tmp_path / "shared")
        data["jail"] = {"enabled": False, "grants": []}
        _write_policy(agent, data)
        before = copy.deepcopy(agent.config)
        outcome = agent.apply_project_policy()
        assert outcome["status"] == "refused"
        assert "may not be turned off" in outcome["reason"]
        assert "refused whole" in outcome["headline"]
        assert agent.config == before
        assert agent._policy_registry().policy_ids() == ()
        assert _events(store, session_id, "project_policy") == []
        refusals = _events(store, session_id, "project_policy_refused")
        assert len(refusals) == 1
        assert "may not be turned off" in refusals[0]["reason"]
        status = agent.project_policy_status()
        assert "may not be turned off" in status["refusal"]
        agent.close()


class TestPolicyAgentPartialFailure:
    def test_hooks_save_failure_reverts_that_step_only(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        grant = tmp_path / "shared"
        grant.mkdir()
        _write_policy(agent, _policy_data(grant))
        def flaky_save(config):
            # Fail only the save the hooks step makes: by then the
            # posture has landed and the policy hooks are staged.
            staged = config.get("hooks") or []
            return not (
                config.get("permission_profile") == "read-only-scout"
                and staged and staged[0].get("name") == "team-check")
        monkeypatch.setattr(llm.config_manager, "save_config", flaky_save)
        outcome = agent.apply_project_policy()
        assert outcome["status"] == "partial"
        steps = {s["step"]: s["status"] for s in outcome["steps"]}
        assert steps["posture"] == "applied"
        assert steps["grants"] == "applied"
        assert steps["hooks"] == "failed"
        failed = [s for s in outcome["steps"]
                  if s["step"] == "hooks"][0]
        assert "could not be saved" in failed["reason"]
        # The failed step reverted; the earlier steps stand.
        assert agent.config.get("hooks", []) == []
        assert agent.config["permission_profile"] == "read-only-scout"
        assert agent.config["path_grants"] == [_os.path.realpath(grant)]
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "hooks_reverted" in types
        events = _events(store, session_id, "project_policy")
        assert len(events) == 1 and events[0]["applied"] is False
        agent.close()

    def test_set_hooks_replaces_and_noops(self, agent):
        hooks = _policy_data("x")["hooks"]
        record = agent.set_hooks(hooks)
        assert record["changed"] is True
        assert agent.config["hooks"][0]["name"] == "team-check"
        assert [h.name for h in agent.configured_hooks()] == ["team-check"]
        record = agent.set_hooks(hooks)
        assert record["changed"] is False
        with pytest.raises(ValueError):
            agent.set_hooks([{"event": "nope", "command": "x"}])


class TestPolicyTerminalSurface:
    def test_show_plan_sections_apply(self, agent, tmp_path):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/policy")
        assert "No project policy" in text
        grant = tmp_path / "shared"
        grant.mkdir()
        _write_policy(agent, _policy_data(grant))
        _, _, text = _slash(agent, "/policy plan")
        assert "permission_profile" in text
        assert "nothing applied" in text
        assert "permission_profile" not in agent.config
        _, _, text = _slash(agent, "/policy sections")
        assert "posture" in text and "hooks" in text
        _, _, text = _slash(agent, "/policy apply")
        assert "posture: applied" in text
        assert agent.config["permission_profile"] == "read-only-scout"
        _, _, text = _slash(agent, "/policy show")
        assert "team-policy" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert "/policy [show|plan|sections|apply]" in text
        _, _, text = _slash(agent, "/policy frobnicate")
        assert text == USAGE


@pytest.fixture()
def policy_handler(agent, monkeypatch):
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


def _policy_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestPolicyCommand:
    def test_show_is_default(self, policy_handler, agent):
        policy_handler._handle_policy("")
        assert "No project policy" in _policy_published_text(policy_handler)

    def test_plan_sections_and_apply(self, policy_handler, agent, tmp_path):
        grant = tmp_path / "shared"
        grant.mkdir()
        _write_policy(agent, _policy_data(grant))
        policy_handler._handle_policy("plan")
        assert "permission_profile" in _policy_published_text(policy_handler)
        assert "permission_profile" not in agent.config
        policy_handler._handle_policy("sections")
        assert "posture" in _policy_published_text(policy_handler)
        policy_handler._handle_policy("apply")
        assert "posture: applied" in _policy_published_text(policy_handler)
        assert agent.config["permission_profile"] == "read-only-scout"

    def test_bad_grammar_is_published(self, policy_handler, agent):
        policy_handler._handle_policy("frobnicate")
        assert "Usage: /policy" in _policy_published_text(policy_handler)


class TestChatScreenRoutingPolicy:
    def test_policy_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/policy apply", _FakeLog())
        assert calls == [("/policy", "apply")]
