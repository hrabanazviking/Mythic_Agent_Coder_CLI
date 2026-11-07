"""M-101 Hooks - the full lifecycle - pure-layer tests.

TIER: integration

The pure layer is the seven lifecycle events as
data, a hook (one event, one user script command)
validated as data, a mechanical verdict for one
finished run read from its exit code and JSON
output alone, and a block shaped as news with the
reason the coder must answer. Decisions are
mechanical, a block always carries a reason, an
error blocks only before the act or at a gate,
and malformed data raises.
"""

import pytest

from mythic_agent.core.hooks import (
    DECISIONS,
    ERROR_BLOCKING_EVENTS,
    HOOK_EVENTS,
    HOOKS_SLICE,
    NO_REASON,
    PLAIN_EXPLANATION,
    SETTING_KEY,
    USAGE,
    Hook,
    HookVerdict,
    block_record,
    build_hook,
    build_hooks,
    evaluate_result,
    format_block,
    format_hook,
    format_hooks,
    format_verdict,
    hook_label,
    hooks_from_config,
    normalize_event,
    parse_hook_output,
    parse_hooks_args,
    select_hooks,
    validate_hook,
    validate_hooks,
)


def _hook(**overrides):
    spec = {"event": "pre_tool", "command": "lint.sh"}
    spec.update(overrides)
    return validate_hook(spec)


# -- names and constants ---------------------------------------------------


def test_constants_and_usage():
    assert HOOKS_SLICE == "M-101"
    assert SETTING_KEY == "hooks"
    assert HOOK_EVENTS == (
        "pre_tool", "post_tool", "pre_edit", "post_edit",
        "on_test", "on_commit", "on_session")
    assert DECISIONS == ("allow", "block", "error")
    assert ERROR_BLOCKING_EVENTS == frozenset(
        {"pre_tool", "pre_edit", "on_test", "on_commit"})
    assert NO_REASON == "the hook blocked giving no reason"
    assert USAGE.startswith("Usage: /hooks")
    assert "pre_tool" in PLAIN_EXPLANATION
    assert "must answer" in PLAIN_EXPLANATION


def test_normalize_event_case_and_dashes():
    assert normalize_event("pre_tool") == "pre_tool"
    assert normalize_event("PRE-TOOL") == "pre_tool"
    assert normalize_event(" On-Test ") == "on_test"
    assert normalize_event("on_session") == "on_session"


def test_normalize_event_unknown_raises():
    for bad in ("pre_frobnicate", "", "tool", None, 7):
        with pytest.raises(ValueError):
            normalize_event(bad)


# -- the Hook dataclass ------------------------------------------------------


def test_hook_defaults_and_record():
    hook = Hook(event="pre-tool", command="  lint.sh  ")
    assert hook.event == "pre_tool"
    assert hook.command == "lint.sh"
    assert hook.name == ""
    assert hook.enabled is True
    assert hook.timeout_seconds == 30
    assert hook.label == "lint.sh"
    assert hook.to_record() == {
        "event": "pre_tool", "command": "lint.sh", "name": "",
        "enabled": True, "timeout_seconds": 30}


def test_hook_named_label_and_stripping():
    hook = Hook(event="on_test", command="pytest -q", name="  tests  ")
    assert hook.name == "tests"
    assert hook.label == "tests"
    assert hook_label(hook) == "tests"
    assert hook_label(" plain label ") == "plain label"
    with pytest.raises(ValueError):
        hook_label("")


def test_hook_blank_command_and_bad_event_raise():
    with pytest.raises(ValueError):
        Hook(event="pre_tool", command="   ")
    with pytest.raises(ValueError):
        Hook(event="pre_tool", command="")
    with pytest.raises(ValueError):
        Hook(event="whenever", command="lint.sh")
    with pytest.raises(ValueError):
        Hook(event="pre_tool", command="lint.sh", name=7)


def test_hook_timeout_bounds():
    assert Hook(event="pre_tool", command="x", timeout_seconds=1)
    assert Hook(event="pre_tool", command="x", timeout_seconds=600)
    for bad in (0, 601, -5, "30", 30.5, None):
        with pytest.raises(ValueError):
            Hook(event="pre_tool", command="x", timeout_seconds=bad)


def test_hook_timeout_bool_and_enabled_non_bool_raise():
    with pytest.raises(ValueError):
        Hook(event="pre_tool", command="x", timeout_seconds=True)
    with pytest.raises(ValueError):
        Hook(event="pre_tool", command="x", enabled="yes")
    with pytest.raises(ValueError):
        Hook(event="pre_tool", command="x", enabled=1)


# -- validate / build from mappings -------------------------------------------


def test_validate_hook_ok_and_passthrough():
    hook = _hook(name="lint", timeout_seconds=45)
    assert isinstance(hook, Hook)
    assert hook.name == "lint"
    assert hook.timeout_seconds == 45
    assert validate_hook(hook) is hook
    assert build_hook("on_commit", "sign.sh") == Hook(
        event="on_commit", command="sign.sh")


def test_validate_hook_aliases():
    hook = validate_hook(
        {"event": "pre_edit", "script": "fmt.sh", "timeout": 10})
    assert hook.command == "fmt.sh"
    assert hook.timeout_seconds == 10
    same = validate_hook(
        {"event": "pre_edit", "command": "fmt.sh", "script": "fmt.sh",
         "timeout_seconds": 10, "timeout": 10})
    assert same.command == "fmt.sh"


def test_validate_hook_conflicting_aliases_raise():
    with pytest.raises(ValueError):
        validate_hook({"event": "pre_edit", "command": "a.sh",
                       "script": "b.sh"})
    with pytest.raises(ValueError):
        validate_hook({"event": "pre_edit", "command": "a.sh",
                       "timeout_seconds": 10, "timeout": 20})


def test_validate_hook_unknown_and_missing_keys_raise():
    with pytest.raises(ValueError):
        _hook(telemetry="off")
    with pytest.raises(ValueError):
        validate_hook({"command": "lint.sh"})
    with pytest.raises(ValueError):
        validate_hook({"event": "pre_tool"})
    with pytest.raises(ValueError):
        validate_hook("not a mapping")


def test_validate_hooks_list_rules():
    assert validate_hooks(None) == ()
    assert build_hooks(None) == ()
    assert validate_hooks([]) == ()
    hooks = validate_hooks([
        {"event": "pre_tool", "command": "a.sh"},
        {"event": "on_test", "command": "b.sh"}])
    assert [h.command for h in hooks] == ["a.sh", "b.sh"]
    with pytest.raises(ValueError):
        validate_hooks([{"event": "pre_tool", "command": "a.sh"},
                        {"event": "nope", "command": "b.sh"}])
    with pytest.raises(ValueError):
        validate_hooks("a.sh")


def test_hooks_from_config():
    assert hooks_from_config({}) == ()
    assert hooks_from_config({SETTING_KEY: None}) == ()
    hooks = hooks_from_config({SETTING_KEY: [
        {"event": "pre_tool", "command": "a.sh"}]})
    assert len(hooks) == 1 and hooks[0].command == "a.sh"
    with pytest.raises(ValueError):
        hooks_from_config({SETTING_KEY: [{"event": "pre_tool"}]})
    with pytest.raises(ValueError):
        hooks_from_config({SETTING_KEY: "a.sh"})


def test_select_hooks_enabled_in_listed_order():
    hooks = validate_hooks([
        {"event": "pre_tool", "command": "first.sh"},
        {"event": "post_tool", "command": "other.sh"},
        {"event": "pre_tool", "command": "off.sh", "enabled": False},
        {"event": "pre-tool", "command": "second.sh"}])
    selected = select_hooks(hooks, "PRE-TOOL")
    assert [h.command for h in selected] == ["first.sh", "second.sh"]
    assert select_hooks(hooks, "on_commit") == ()
    with pytest.raises(ValueError):
        select_hooks(hooks, "whenever")


# -- parse_hook_output -----------------------------------------------------------


def test_parse_output_decision_block():
    assert parse_hook_output(
        '{"decision": "block", "reason": "no lint"}') == (
            "block", "no lint")


def test_parse_output_block_true_and_reason_aliases():
    assert parse_hook_output('{"block": true, "message": "halt"}') == (
        "block", "halt")
    assert parse_hook_output('{"block": false}') == ("", "")


def test_parse_output_stdout_first_then_stderr():
    assert parse_hook_output("", '{"decision": "block", "reason": "e"}') == (
        "block", "e")
    assert parse_hook_output(
        '{"decision": "allow"}',
        '{"decision": "block", "reason": "e"}') == ("allow", "")


def test_parse_output_allow_and_no_record():
    assert parse_hook_output('{"decision": "allow", "reason": "ok"}') == (
        "allow", "ok")
    assert parse_hook_output("just prose", "more prose") == ("", "")
    assert parse_hook_output("", "") == ("", "")
    assert parse_hook_output('[1, 2, 3]') == ("", "")
    assert parse_hook_output('noise {"decision": "block", "reason": "r"} tail') == (
        "block", "r")


# -- evaluate_result: the mechanical verdict --------------------------------------


def test_evaluate_exit_zero_allows():
    verdict = evaluate_result("pre_tool", _hook(), 0, stdout="done")
    assert verdict.decision == "allow"
    assert verdict.blocks is False
    assert verdict.allowed is True
    assert verdict.event == "pre_tool"
    assert verdict.hook == "lint.sh"
    assert verdict.exit_code == 0


def test_evaluate_exit_two_blocks_with_stderr_reason():
    verdict = evaluate_result(
        "pre_edit", _hook(), 2, stdout="out words", stderr="stop: bad edit")
    assert verdict.decision == "block"
    assert verdict.blocks is True
    assert verdict.reason == "stop: bad edit"


def test_evaluate_exit_two_reason_fallbacks():
    verdict = evaluate_result("on_test", _hook(), 2, stdout="stdout reason")
    assert verdict.reason == "stdout reason"
    verdict = evaluate_result("on_test", _hook(), 2)
    assert verdict.decision == "block"
    assert verdict.reason == "the hook blocked giving no reason"
    assert verdict.reason == NO_REASON


def test_evaluate_json_block_at_any_exit_code():
    payload = '{"decision": "block", "reason": "policy says no"}'
    for code in (0, 1, 2, 7):
        verdict = evaluate_result("post_tool", _hook(), code, stdout=payload)
        assert verdict.decision == "block"
        assert verdict.blocks is True
        assert verdict.reason == "policy says no"
    verdict = evaluate_result(
        "pre_tool", _hook(), 0, stdout='{"block": true}')
    assert verdict.decision == "block"
    assert verdict.reason == NO_REASON


def test_evaluate_error_blocks_before_the_act_and_at_gates():
    for event in ("pre_tool", "pre_edit", "on_test", "on_commit"):
        verdict = evaluate_result(event, _hook(), 1, stderr="boom")
        assert verdict.decision == "error"
        assert verdict.blocks is True
        assert verdict.reason == "boom"


def test_evaluate_error_is_news_only_after_the_act():
    for event in ("post_tool", "post_edit", "on_session"):
        verdict = evaluate_result(event, _hook(), 3)
        assert verdict.decision == "error"
        assert verdict.blocks is False
        assert verdict.reason == "the hook failed with exit code 3"


def test_evaluate_non_int_exit_code_raises():
    for bad in ("0", 0.0, None, True, [0]):
        with pytest.raises(ValueError):
            evaluate_result("pre_tool", _hook(), bad)
    with pytest.raises(ValueError):
        evaluate_result("whenever", _hook(), 0)


def test_verdict_record_shape():
    verdict = evaluate_result("on_commit", _hook(name="sign"), 2, stderr="unsigned")
    record = verdict.to_record()
    assert record == {
        "type": "hook_verdict", "slice": "M-101", "event": "on_commit",
        "hook": "sign", "decision": "block", "reason": "unsigned",
        "exit_code": 2, "blocks": True}
    with pytest.raises(ValueError):
        HookVerdict(event="pre_tool", hook="x", decision="shrug",
                    reason="", exit_code=0)
    with pytest.raises(ValueError):
        HookVerdict(event="pre_tool", hook="x", decision="allow",
                    reason="", exit_code="0")


# -- blocks as news ------------------------------------------------------------------


def test_block_record_only_when_blocking():
    blocking = evaluate_result("pre_tool", _hook(name="lint"), 2, stderr="no")
    assert block_record(blocking) == {
        "type": "hook_block", "news": True, "event": "pre_tool",
        "hook": "lint", "reason": "no"}
    allowed = evaluate_result("pre_tool", _hook(), 0)
    assert block_record(allowed) is None
    news_only = evaluate_result("post_tool", _hook(), 1, stderr="late boom")
    assert news_only.decision == "error"
    assert block_record(news_only) is None
    gate_error = evaluate_result("on_test", _hook(), 1, stderr="crash")
    assert block_record(gate_error)["type"] == "hook_block"
    with pytest.raises(ValueError):
        block_record({"type": "hook_block"})


# -- the /hooks surface --------------------------------------------------------------


def test_format_hooks_empty_starts_with_none_configured():
    assert format_hooks([]).startswith("Hooks: none configured.")
    assert format_hooks(()).startswith("Hooks: none configured.")
    assert format_hooks({}).startswith("Hooks: none configured.")
    assert format_hooks(None).startswith("Hooks: none configured.")


def test_format_hooks_lists_in_order():
    hooks = validate_hooks([
        {"event": "pre_tool", "command": "a.sh", "name": "alpha"},
        {"event": "on_test", "command": "b.sh", "enabled": False}])
    text = format_hooks(hooks)
    assert text.startswith("Hooks: 2 configured.")
    assert text.index("a.sh") < text.index("b.sh")
    assert "alpha" in text and "disabled" in text
    assert format_hooks({SETTING_KEY: [
        {"event": "pre_tool", "command": "a.sh"}]}) == format_hooks(
            validate_hooks([{"event": "pre_tool", "command": "a.sh"}]))
    assert format_hook(hooks[0]).startswith("pre_tool: 'alpha' a.sh")


def test_format_verdict_words():
    allowed = evaluate_result("pre_tool", _hook(), 0)
    assert format_verdict(allowed).startswith("Hook allowed:")
    blocked = evaluate_result("pre_tool", _hook(), 2, stderr="halt")
    text = format_verdict(blocked)
    assert text.startswith("Hook block:") and "halt" in text
    gate = evaluate_result("on_test", _hook(), 1, stderr="crash")
    assert "blocks the work" in format_verdict(gate)
    late = evaluate_result("post_tool", _hook(), 1, stderr="crash")
    assert "news only" in format_verdict(late)
    with pytest.raises(ValueError):
        format_verdict({"type": "hook_verdict"})


def test_format_block_headline_and_refusals():
    blocked = evaluate_result("pre_edit", _hook(name="fmt"), 2, stderr="unformatted")
    headline = format_block(blocked)
    assert headline.startswith("Hook block: pre_edit hook 'fmt'")
    assert "unformatted" in headline
    assert format_block(block_record(blocked)) == headline
    allowed = evaluate_result("pre_edit", _hook(), 0)
    with pytest.raises(ValueError):
        format_block(allowed)
    with pytest.raises(ValueError):
        format_block({"type": "something_else"})


def test_parse_hooks_args_show_forms():
    assert parse_hooks_args("") == ("show", None)
    assert parse_hooks_args(None) == ("show", None)
    assert parse_hooks_args("list") == ("show", None)
    assert parse_hooks_args("show") == ("show", None)
    assert parse_hooks_args("show pre_tool") == ("show", "pre_tool")
    assert parse_hooks_args("show ON-TEST") == ("show", "on_test")
    assert parse_hooks_args("pre_edit") == ("show", "pre_edit")
    assert parse_hooks_args("on-session") == ("show", "on_session")


def test_parse_hooks_args_check_and_errors():
    assert parse_hooks_args("check on_commit") == ("check", "on_commit")
    assert parse_hooks_args("check pre-tool") == ("check", "pre_tool")
    for bad in ("frobnicate", "check", "check whenever", "show a b",
                "check pre_tool extra", "on", "off"):
        with pytest.raises(ValueError) as excinfo:
            parse_hooks_args(bad)
        assert str(excinfo.value) == USAGE

# -- agent layer: status, the live run road, surfaces (M-101) ---

import copy as _copy
import sys as _sys

from mythic_agent.core.sessions import SessionStore

_PY = _sys.executable


def _cmd(code):
    return f"{_PY} -c '{code}'"


ALLOW_CMD = _cmd("import sys; sys.exit(0)")
BLOCK_CMD = _cmd(
    'import sys; sys.stderr.write("no way"); sys.exit(2)')
JSON_BLOCK_CMD = (
    "echo '{\"decision\": \"block\", "
    "\"reason\": \"policy says no\"}'")
ERROR_CMD = _cmd(
    'import sys; sys.stderr.write("boom"); sys.exit(1)')
SLEEP_CMD = _cmd("import time; time.sleep(5)")


class _OfflineMemory:
    def __init__(self):
        self.archived = []

    def search(self, query, top_k=2):
        return []

    def insert(self, text, metadata=None):
        self.archived.append(text)


@pytest.fixture()
def agent(tmp_path, monkeypatch):
    from mythic_agent.agents import llm
    from mythic_agent.core.secure_api import unsubscribe

    config = {"model": "test-model", "base_url": "http://localhost:1/v1", "api_keys": {}}
    monkeypatch.setattr(llm.config_manager, "MYTHIC_DIR", tmp_path / "state")
    monkeypatch.setattr(llm.config_manager, "load_config", lambda: _copy.deepcopy(config))
    monkeypatch.setattr(llm.config_manager, "save_config", lambda config: True)
    monkeypatch.setattr(llm, "get_vector_provider", lambda *args: _OfflineMemory())
    instance = llm.Agent(project_root=tmp_path)
    from mythic_agent.core.policy import ToolPolicy
    instance.tool_policy = ToolPolicy("trusted")
    yield instance
    unsubscribe("agent_clear_history", instance._handle_clear_history)
    unsubscribe("agent_compact_history", instance._handle_compact_history)


def _store_for(tmp_path):
    return SessionStore(tmp_path, tmp_path / "state")


def _events(store, session_id, type_name):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == type_name]


def _configure(agent, *specs):
    agent.config[SETTING_KEY] = list(specs)


class TestHooksAgentStatus:
    def test_status_defaults_to_none_configured(self, agent):
        status = agent.hooks_status()
        assert status["hooks"] == []
        assert status["screen"].startswith("Hooks: none configured.")
        assert status["explanation"] == PLAIN_EXPLANATION
        assert agent.configured_hooks() == ()

    def test_status_reflects_the_configured_hooks(self, agent):
        _configure(agent,
                   {"event": "pre_tool", "command": "a.sh", "name": "alpha"},
                   {"event": "on_test", "command": "b.sh", "enabled": False})
        status = agent.hooks_status()
        assert [h["command"] for h in status["hooks"]] == ["a.sh", "b.sh"]
        assert status["hooks"][0]["name"] == "alpha"
        assert status["screen"].startswith("Hooks: 2 configured.")
        assert [h.command for h in agent.configured_hooks()] == ["a.sh", "b.sh"]

    def test_status_malformed_config_raises(self, agent):
        _configure(agent, {"event": "pre_tool"})
        with pytest.raises(ValueError):
            agent.hooks_status()
        agent.config[SETTING_KEY] = "a.sh"
        with pytest.raises(ValueError):
            agent.hooks_status()


class TestRunHooks:
    def test_no_hooks_for_the_event_runs_nothing(self, agent):
        _configure(agent, {"event": "pre_tool", "command": ALLOW_CMD})
        assert agent.run_hooks("on_commit") == []

    def test_unknown_event_raises_before_anything_runs(self, agent):
        _configure(agent, {"event": "pre_tool", "command": ALLOW_CMD})
        with pytest.raises(ValueError):
            agent.run_hooks("whenever")

    def test_allow_verdict_from_a_real_command(self, agent):
        _configure(agent, {"event": "pre_tool", "command": ALLOW_CMD,
                           "name": "ok-hook"})
        verdicts = agent.run_hooks("pre_tool")
        assert len(verdicts) == 1
        assert verdicts[0].decision == "allow"
        assert verdicts[0].blocks is False
        assert verdicts[0].hook == "ok-hook"
        assert verdicts[0].exit_code == 0

    def test_exit_two_blocks_and_publishes_news(self, agent, tmp_path):
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        _configure(agent, {"event": "pre_tool", "command": BLOCK_CMD,
                           "name": "lint"})
        verdicts = agent.run_hooks("pre-tool")
        assert verdicts[0].decision == "block"
        assert verdicts[0].reason == "no way"
        events = _events(store, session_id, "hook_block")
        assert len(events) == 1
        assert events[0]["news"] is True
        assert events[0]["event"] == "pre_tool"
        assert events[0]["hook"] == "lint"
        assert events[0]["reason"] == "no way"
        agent.close()

    def test_json_block_at_exit_zero_blocks_and_publishes(self, agent, tmp_path):
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        _configure(agent, {"event": "on_test", "command": JSON_BLOCK_CMD})
        verdicts = agent.run_hooks("on_test")
        assert verdicts[0].decision == "block"
        assert verdicts[0].reason == "policy says no"
        events = _events(store, session_id, "hook_block")
        assert len(events) == 1 and events[0]["reason"] == "policy says no"
        agent.close()

    def test_allow_publishes_nothing(self, agent, tmp_path):
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        _configure(agent, {"event": "pre_tool", "command": ALLOW_CMD})
        agent.run_hooks("pre_tool")
        assert _events(store, session_id, "hook_block") == []
        agent.close()

    def test_error_after_the_act_is_news_only(self, agent, tmp_path):
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        _configure(agent, {"event": "post_tool", "command": ERROR_CMD})
        verdicts = agent.run_hooks("post_tool")
        assert verdicts[0].decision == "error"
        assert verdicts[0].blocks is False
        assert verdicts[0].reason == "boom"
        assert _events(store, session_id, "hook_block") == []
        agent.close()

    def test_error_at_a_gate_blocks_and_publishes(self, agent, tmp_path):
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        _configure(agent, {"event": "on_commit", "command": ERROR_CMD})
        verdicts = agent.run_hooks("on_commit")
        assert verdicts[0].decision == "error"
        assert verdicts[0].blocks is True
        events = _events(store, session_id, "hook_block")
        assert len(events) == 1 and events[0]["reason"] == "boom"
        agent.close()

    def test_disabled_and_other_event_hooks_never_run(self, agent):
        _configure(agent,
                   {"event": "pre_tool", "command": BLOCK_CMD,
                    "enabled": False},
                   {"event": "post_tool", "command": BLOCK_CMD},
                   {"event": "pre_tool", "command": ALLOW_CMD})
        verdicts = agent.run_hooks("pre_tool")
        assert len(verdicts) == 1 and verdicts[0].decision == "allow"

    def test_hooks_run_in_configured_order(self, agent):
        _configure(agent,
                   {"event": "pre_tool", "command": ALLOW_CMD, "name": "first"},
                   {"event": "pre_tool", "command": BLOCK_CMD, "name": "second"})
        verdicts = agent.run_hooks("pre_tool")
        assert [v.hook for v in verdicts] == ["first", "second"]
        assert [v.decision for v in verdicts] == ["allow", "block"]

    def test_timeout_is_an_error_that_blocks_before_the_act(self, agent):
        _configure(agent, {"event": "pre_edit", "command": SLEEP_CMD,
                           "timeout_seconds": 1})
        verdicts = agent.run_hooks("pre_edit")
        assert verdicts[0].decision == "error"
        assert verdicts[0].exit_code == 124
        assert verdicts[0].blocks is True
        assert "timed out after 1s" in verdicts[0].reason

    def test_malformed_stored_hooks_raise_on_run(self, agent):
        _configure(agent, {"event": "pre_tool"})
        with pytest.raises(ValueError):
            agent.run_hooks("pre_tool")


class TestHooksTerminalSurface:
    def test_show_is_the_whole_slice(self, agent):
        from mythic_agent.terminal import _slash
        _configure(agent, {"event": "pre_tool", "command": "a.sh",
                           "name": "alpha"})
        _, _, text = _slash(agent, "/hooks")
        assert text.startswith("Hooks: 1 configured.")
        assert "a.sh" in text and "alpha" in text

    def test_show_for_one_event_filters(self, agent):
        from mythic_agent.terminal import _slash
        _configure(agent,
                   {"event": "pre_tool", "command": "a.sh"},
                   {"event": "on_test", "command": "b.sh"})
        _, _, text = _slash(agent, "/hooks show on_test")
        assert "b.sh" in text and "a.sh" not in text
        _, _, text = _slash(agent, "/hooks on_commit")
        assert text.startswith("Hooks: none configured.")

    def test_check_runs_and_reports_the_verdict(self, agent):
        from mythic_agent.terminal import _slash
        _configure(agent, {"event": "pre_tool", "command": ALLOW_CMD})
        _, _, text = _slash(agent, "/hooks check pre_tool")
        assert text.startswith("Hook allowed:")

    def test_check_block_reports_the_reason(self, agent):
        from mythic_agent.terminal import _slash
        _configure(agent, {"event": "pre_tool", "command": BLOCK_CMD})
        _, _, text = _slash(agent, "/hooks check pre_tool")
        assert text.startswith("Hook block:") and "no way" in text

    def test_check_with_no_hooks_for_the_event(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/hooks check on_test")
        assert text == "No hooks are configured for on_test; nothing ran."

    def test_bad_grammar_is_the_usage(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/hooks frobnicate")
        assert text == USAGE
        _, _, text = _slash(agent, "/hooks on")
        assert text == USAGE


@pytest.fixture()
def hooks_handler(agent, monkeypatch):
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


def _hooks_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestHooksCommand:
    def test_show_is_default(self, hooks_handler, agent):
        _configure(agent, {"event": "pre_tool", "command": "a.sh"})
        hooks_handler._handle_hooks("")
        assert "Hooks: 1 configured." in _hooks_published_text(hooks_handler)

    def test_check_block_is_published(self, hooks_handler, agent):
        _configure(agent, {"event": "pre_tool", "command": BLOCK_CMD})
        hooks_handler._handle_hooks("check pre_tool")
        text = _hooks_published_text(hooks_handler)
        assert "Hook block:" in text and "no way" in text

    def test_check_with_no_hooks_is_published(self, hooks_handler, agent):
        hooks_handler._handle_hooks("check on_test")
        assert "nothing ran" in _hooks_published_text(hooks_handler)

    def test_bad_grammar_is_published(self, hooks_handler, agent):
        hooks_handler._handle_hooks("frobnicate")
        assert "Usage: /hooks" in _hooks_published_text(hooks_handler)


class TestChatScreenRoutingHooks:
    def test_hooks_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/hooks check pre_tool", _FakeLog())
        assert calls == [("/hooks", "check pre_tool")]
