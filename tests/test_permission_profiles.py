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
