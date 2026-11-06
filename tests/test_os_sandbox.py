"""M-097 The OS sandbox (native) - pure-layer tests.

TIER: integration

The pure layer plans confinement and tells the
per-platform truth: no Docker ever, unknown
platforms refuse, the network stance is explicit
in every plan, and the truth table never claims
proven for a platform this Linux box cannot
measure.
"""

import pytest

from mythic_agent.core.os_sandbox import (
    FORBIDDEN_LAUNCHERS,
    NETWORK_STANCES,
    PLAIN_EXPLANATION,
    PLATFORMS,
    PLATFORM_TRUTH,
    SECCOMP_BASELINE_SYSCALLS,
    SETTING_KEY,
    build_confinement_plan,
    confinement_plan_record,
    current_platform,
    enabled_from_config,
    format_confinement_plan,
    format_gate_change,
    format_os_sandbox,
    format_platform_truth,
    normalize_platform,
    parse_sandbox_args,
    platform_truth_entry,
    set_enabled,
    validate_truth_records,
)


def records():
    return [e.to_record() for e in PLATFORM_TRUTH]


# -- platform names -------------------------------------------------------


def test_platform_aliases_resolve():
    assert normalize_platform("linux") == "linux"
    assert normalize_platform("Darwin") == "macos"
    assert normalize_platform("win32") == "windows"
    assert normalize_platform(" OSX ") == "macos"


def test_unknown_platform_refuses_plainly():
    with pytest.raises(ValueError) as exc:
        normalize_platform("plan9")
    assert "linux" in str(exc.value)
    with pytest.raises(ValueError):
        normalize_platform("")
    with pytest.raises(ValueError):
        normalize_platform(None)


def test_current_platform_is_linux_on_this_box():
    assert current_platform() == "linux"


# -- the truth table ------------------------------------------------------


def test_truth_table_covers_three_platforms_once():
    assert tuple(e.platform for e in PLATFORM_TRUTH) == PLATFORMS
    assert validate_truth_records(records()) == []


def test_truth_table_claims_proven_nowhere():
    assert all(e.support != "proven" for e in PLATFORM_TRUTH)
    by_platform = {e.platform: e.support for e in PLATFORM_TRUTH}
    assert by_platform == {
        "linux": "limited", "macos": "planned", "windows": "limited"}


def test_only_linux_carries_a_measured_note():
    measured = [e.platform for e in PLATFORM_TRUTH
                if e.evidence_kind == "local-measured"]
    assert measured == ["linux"]


def test_truth_entry_lookup_and_reason_present():
    for platform in PLATFORMS:
        entry = platform_truth_entry(platform)
        assert entry.mechanism and entry.reason
    assert platform_truth_entry("darwin").platform == "macos"


def test_validator_refuses_proven_off_linux():
    doctored = records()
    for record in doctored:
        if record["platform"] == "macos":
            record["support"] = "proven"
            record["evidence_kind"] = "local-measured"
    problems = validate_truth_records(doctored)
    assert any("only linux" in p for p in problems)


def test_validator_refuses_proven_without_measurement():
    doctored = records()
    for record in doctored:
        if record["platform"] == "linux":
            record["support"] = "proven"
            record["evidence_kind"] = "none"
    problems = validate_truth_records(doctored)
    assert any("local-measured" in p for p in problems)


def test_validator_refuses_container_mechanism_and_gaps():
    doctored = records()
    doctored[0]["mechanism"] = "run it in docker"
    problems = validate_truth_records(doctored)
    assert any("no Docker" in p for p in problems)
    problems = validate_truth_records(records()[:2])
    assert any("missing" in p for p in problems)
    doctored = records()
    doctored[0]["surprise"] = 1
    assert validate_truth_records(doctored)


# -- linux plans ------------------------------------------------------------


def test_linux_plan_uses_namespaces_and_denies_network():
    plan = build_confinement_plan("git status", platform="linux")
    assert plan.argv_prefix[0] == "unshare"
    assert "--mount" in plan.argv_prefix and "--pid" in plan.argv_prefix
    assert "--net" in plan.argv_prefix
    assert plan.network == "deny"
    assert plan.confined is True
    assert plan.argv() == plan.argv_prefix + ("git", "status")
    assert plan.env()["MYTHIC_SANDBOX_NO_NETWORK"] == "1"


def test_linux_plan_network_allow_drops_net_namespace():
    plan = build_confinement_plan(
        ["curl", "https://example.invalid"], platform="linux",
        network="allow")
    assert "--net" not in plan.argv_prefix
    assert plan.network == "allow"
    assert "MYTHIC_SANDBOX_NO_NETWORK" not in plan.env()


def test_linux_plan_names_seccomp_as_plan_data():
    plan = build_confinement_plan("ls", platform="linux")
    notes = " ".join(plan.enforcement_notes)
    assert "seccomp" in notes and "setpriv" in notes
    assert "read" in SECCOMP_BASELINE_SYSCALLS
    assert "execve" in SECCOMP_BASELINE_SYSCALLS


def test_default_platform_and_network_are_honest():
    plan = build_confinement_plan("git status")
    assert plan.platform == "linux"  # this campaign's box
    assert plan.network == "deny"


# -- macos + windows plans --------------------------------------------------


def test_macos_plan_is_sandbox_exec_with_profile():
    plan = build_confinement_plan("git status", platform="macos")
    assert plan.argv_prefix[0] == "sandbox-exec"
    assert plan.profile_text is not None
    assert "(deny default)" in plan.profile_text
    assert "(deny network*)" in plan.profile_text
    assert plan.support == "planned"
    allowed = build_confinement_plan(
        "git status", platform="darwin", network="allow")
    assert "(allow network*)" in allowed.profile_text


def test_windows_plan_confines_nothing_and_says_so():
    plan = build_confinement_plan("git status", platform="windows")
    assert plan.argv_prefix == ()
    assert plan.confined is False
    assert "job" in plan.explanation.lower()
    assert plan.network == "deny"  # stance recorded even unenforced


def test_require_confined_refuses_unconfined_platforms():
    with pytest.raises(ValueError):
        build_confinement_plan(
            "git status", platform="windows", require_confined=True)
    with pytest.raises(ValueError):
        build_confinement_plan(
            "git status", platform="macos", require_confined=True)
    plan = build_confinement_plan(
        "git status", platform="linux", require_confined=True)
    assert plan.confined is True


# -- refusals -----------------------------------------------------------------


def test_no_docker_ever():
    for launcher in FORBIDDEN_LAUNCHERS:
        with pytest.raises(ValueError):
            build_confinement_plan(f"{launcher} run img", platform="linux")
        with pytest.raises(ValueError):
            build_confinement_plan(["/usr/bin/" + launcher, "ps"])
    for platform in PLATFORMS:
        plan = build_confinement_plan("git status", platform=platform)
        blob = " ".join(plan.argv()).lower()
        blob += (plan.profile_text or "").lower()
        blob += plan.mechanism.lower()
        for launcher in FORBIDDEN_LAUNCHERS:
            assert launcher not in blob


def test_bad_commands_and_stances_refuse():
    with pytest.raises(ValueError):
        build_confinement_plan("")
    with pytest.raises(ValueError):
        build_confinement_plan([])
    with pytest.raises(ValueError):
        build_confinement_plan("git status", network="sometimes")
    with pytest.raises(ValueError):
        build_confinement_plan("git status", platform="plan9")


def test_every_plan_states_its_network_stance():
    for platform in PLATFORMS:
        for stance in NETWORK_STANCES:
            plan = build_confinement_plan(
                "git status", platform=platform, network=stance)
            assert plan.network == stance
            assert stance in format_confinement_plan(plan)
            assert confinement_plan_record(plan)["network"] == stance


# -- the gate -----------------------------------------------------------------


def test_gate_defaults_on_and_reads_bool():
    assert SETTING_KEY == "os_sandbox"
    assert enabled_from_config({}) is True
    assert enabled_from_config({SETTING_KEY: False}) is False
    with pytest.raises(ValueError):
        enabled_from_config({SETTING_KEY: "yes"})


def test_set_enabled_is_pure_and_names_noops():
    config = {}
    value, change = set_enabled(config, False)
    assert value is False and change.before is True and change.after is False
    assert config == {}  # pure: the caller's config is untouched
    assert change.event()["type"] == "os_sandbox_setting_changed"
    with pytest.raises(ValueError):
        set_enabled({}, True)  # already on
    with pytest.raises(ValueError):
        set_enabled({}, "off")


def test_format_gate_change_speaks_plainly():
    _, change = set_enabled({}, False)
    assert format_gate_change(change.record("s1", True)) == (
        "The OS sandbox is now off.")


# -- the /sandbox grammar ------------------------------------------------------


def test_parse_show_gate_and_truth():
    assert parse_sandbox_args("") == {"action": "show"}
    assert parse_sandbox_args("show") == {"action": "show"}
    assert parse_sandbox_args("on") == {"action": "on"}
    assert parse_sandbox_args("off") == {"action": "off"}
    assert parse_sandbox_args("truth") == {"action": "truth"}


def test_parse_plan_forms():
    parsed = parse_sandbox_args("plan git status")
    assert parsed == {"action": "plan", "platform": None,
                      "command": ["git", "status"]}
    parsed = parse_sandbox_args("plan macos -- git status")
    assert parsed["platform"] == "macos"
    assert parsed["command"] == ["git", "status"]
    plan = build_confinement_plan(
        parsed["command"], platform=parsed["platform"])
    assert plan.platform == "macos"


def test_parse_refuses_unknown_grammar():
    with pytest.raises(ValueError):
        parse_sandbox_args("frobnicate")
    with pytest.raises(ValueError):
        parse_sandbox_args("plan")
    with pytest.raises(ValueError):
        parse_sandbox_args("plan plan9 -- git status")


# -- formatters and records ------------------------------------------------------


def test_format_truth_and_whole_slice():
    truth = format_platform_truth()
    for platform in PLATFORMS:
        assert platform in truth
    assert "limited" in truth and "planned" in truth
    whole = format_os_sandbox({})
    assert "M-097" in whole and PLAIN_EXPLANATION in whole
    assert "Setting: on (os_sandbox)" in whole
    assert "unshare" in whole
    off = format_os_sandbox({SETTING_KEY: False})
    assert "Setting: off (os_sandbox)" in off


def test_format_plan_renders_argv_and_profile():
    linux = format_confinement_plan(
        build_confinement_plan("git status", platform="linux"))
    assert "Would run: unshare" in linux
    macos = format_confinement_plan(
        build_confinement_plan("git status", platform="macos"))
    assert "sandbox-exec" in macos and "(version 1)" in macos
    windows = format_confinement_plan(
        build_confinement_plan("git status", platform="windows"))
    assert "no confined argv" in windows


def test_plan_record_is_journal_shaped():
    record = confinement_plan_record(
        build_confinement_plan("git status", platform="linux"))
    assert record["type"] == "os_sandbox_plan"
    assert record["slice"] == "M-097"
    assert record["platform"] == "linux"
    assert record["confined"] is True
    assert record["argv"][0] == "unshare"
