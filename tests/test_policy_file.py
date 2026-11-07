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
