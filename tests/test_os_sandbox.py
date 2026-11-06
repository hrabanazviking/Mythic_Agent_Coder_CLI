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


# -- agent layer: status, set, run road, surfaces (M-097) ---------------

from mythic_agent.core import os_sandbox as osb
from mythic_agent.core.sessions import SessionStore


def _store_for(tmp_path):
    return SessionStore(tmp_path, tmp_path / "state")


class TestOsSandboxAgent:
    def test_status_defaults_on_with_truth(self, agent):
        status = agent.os_sandbox_status()
        assert status["enabled"] is True
        assert [e["platform"] for e in status["truth"]] == list(PLATFORMS)
        assert status["screen"] == format_os_sandbox(agent.config)
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_status_reflects_off(self, agent):
        agent.config[SETTING_KEY] = False
        assert agent.os_sandbox_status()["enabled"] is False

    def test_status_malformed_config_raises(self, agent):
        agent.config[SETTING_KEY] = "yes"
        with pytest.raises(ValueError):
            agent.os_sandbox_status()

    def test_set_off_then_on(self, agent):
        record = agent.set_os_sandbox(False)
        assert record["type"] == "os_sandbox_setting_changed"
        assert record["from"] is True and record["to"] is False
        assert record["journaled"] is False
        assert agent.config[SETTING_KEY] is False
        record = agent.set_os_sandbox(True)
        assert record["from"] is False and record["to"] is True
        assert format_gate_change(record) == "The OS sandbox is now on."

    def test_set_noop_refuses_and_changes_nothing(self, agent):
        with pytest.raises(ValueError, match="already on"):
            agent.set_os_sandbox(True)
        assert SETTING_KEY not in agent.config
        with pytest.raises(ValueError):
            agent.set_os_sandbox("off")

    def test_set_journals_on_the_session(self, agent, tmp_path):
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.set_os_sandbox(False)
        assert record["journaled"] is True
        events = [e for e in store.export(session_id)["events"]
                  if e["type"] == "os_sandbox_setting_changed"]
        assert len(events) == 1
        assert events[0]["from"] is True and events[0]["to"] is False
        agent.close()

    def test_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.set_os_sandbox(False)
        assert SETTING_KEY not in agent.config
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["os_sandbox_setting_changed",
                              "os_sandbox_setting_reverted"]
        agent.close()

    def test_plan_road_is_pure(self, agent):
        plan = agent.os_sandbox_plan("git status", platform="windows")
        assert plan.confined is False
        plan = agent.os_sandbox_plan(["git", "status"])
        assert plan.platform == "linux" and plan.confined is True


class TestRunOsSandboxed:
    def test_echo_runs_under_the_namespace_prefix(self, agent):
        record = agent.run_os_sandboxed("echo SANDBOX_HELLO")
        assert record["confined"] is True
        assert record["gate_enabled"] is True
        assert record["executed"].startswith("unshare")
        assert record["returncode"] == 0 and record["ok"] is True
        assert "SANDBOX_HELLO" in record["stdout"]
        assert record["plan"]["network"] == "deny"
        assert record["support"] == "limited"  # never proven

    def test_seccomp_is_rendered_data_never_claimed_installed(self, agent):
        record = agent.run_os_sandboxed("echo hi")
        assert record["seccomp_installed"] is False
        assert "not installed" in record["note"] or (
            "no seccomp installation" in record["note"])
        from pathlib import Path
        rendered = Path(record["seccomp_filter_file"]).read_text()
        assert "execve" in rendered and "read" in rendered

    def test_network_marker_rides_the_confined_run(self, agent):
        record = agent.run_os_sandboxed("printenv MYTHIC_SANDBOX_NO_NETWORK")
        assert record["stdout"].strip() == "1"
        record = agent.run_os_sandboxed(
            "printenv MYTHIC_SANDBOX_NO_NETWORK || true", network="allow")
        assert record["stdout"].strip() == ""
        assert "--net" not in record["executed"]

    def test_gate_off_takes_the_elder_road_unchanged(self, agent):
        agent.config[SETTING_KEY] = False
        record = agent.run_os_sandboxed("echo ELDER_ROAD")
        assert record["confined"] is False
        assert record["gate_enabled"] is False
        assert record["executed"] == "echo ELDER_ROAD"
        assert "ELDER_ROAD" in record["stdout"]
        assert "elder" in record["note"]

    def test_unconfined_platform_reports_honestly(self, agent, monkeypatch):
        monkeypatch.setattr(osb, "current_platform", lambda: "windows")
        record = agent.run_os_sandboxed("echo WIN_ROAD")
        assert record["confined"] is False
        assert record["platform"] == "windows"
        assert "WIN_ROAD" in record["stdout"]

    def test_require_confined_refuses_unconfined(self, agent, monkeypatch):
        monkeypatch.setattr(osb, "current_platform", lambda: "windows")
        with pytest.raises(ValueError, match="cannot confine"):
            agent.run_os_sandboxed("echo x", require_confined=True)

    def test_denylist_still_refuses_under_confinement(self, agent):
        from mythic_agent.core.sandbox import SandboxError
        with pytest.raises(SandboxError):
            agent.run_os_sandboxed("rm -rf /tmp/whatever")

    def test_docker_still_refuses(self, agent):
        with pytest.raises(ValueError, match="no Docker"):
            agent.run_os_sandboxed("docker run img")

    def test_empty_command_refuses(self, agent):
        with pytest.raises(ValueError):
            agent.run_os_sandboxed("  ")

    def test_run_journals_the_plan(self, agent, tmp_path):
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.run_os_sandboxed("echo JOURNALED")
        events = [e for e in store.export(session_id)["events"]
                  if e["type"] == "os_sandbox_plan"]
        assert len(events) == 1 and events[0]["confined"] is True
        agent.close()


class TestSandboxTerminalSurface:
    def test_show_is_the_whole_slice(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/sandbox")
        assert "M-097" in text and "Setting: on (os_sandbox)" in text
        assert "unshare" in text

    def test_truth_shows_the_table(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/sandbox truth")
        assert "platform truth" in text and "windows" in text

    def test_plan_renders_the_prefix(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/sandbox plan git status")
        assert "Would run: unshare" in text
        _, _, text = _slash(agent, "/sandbox plan windows -- git status")
        assert "no confined argv" in text

    def test_gate_via_the_terminal(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/sandbox off")
        assert text == "The OS sandbox is now off."
        assert agent.config[SETTING_KEY] is False
        _, _, text = _slash(agent, "/sandbox off")
        assert "already off" in text
        _, _, text = _slash(agent, "/sandbox on")
        assert text == "The OS sandbox is now on."

    def test_bad_grammar_is_the_usage(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/sandbox frobnicate")
        assert text.startswith("Usage: /sandbox")


@pytest.fixture()
def sandbox_handler(agent, monkeypatch):
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


def _sandbox_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestSandboxCommand:
    def test_show_is_default(self, sandbox_handler, agent):
        sandbox_handler._handle_sandbox("")
        text = _sandbox_published_text(sandbox_handler)
        assert "M-097" in text and "Setting: on" in text

    def test_truth_and_plan(self, sandbox_handler, agent):
        sandbox_handler._handle_sandbox("truth")
        assert "platform truth" in _sandbox_published_text(sandbox_handler)
        sandbox_handler._handle_sandbox("plan git status")
        assert "Would run: unshare" in _sandbox_published_text(
            sandbox_handler)

    def test_gate_via_the_handler(self, sandbox_handler, agent):
        sandbox_handler._handle_sandbox("off")
        assert "now off" in _sandbox_published_text(sandbox_handler)
        assert agent.config[SETTING_KEY] is False

    def test_bad_grammar_is_published(self, sandbox_handler, agent):
        sandbox_handler._handle_sandbox("frobnicate")
        assert "Usage: /sandbox" in _sandbox_published_text(sandbox_handler)
