"""Effects require one explicit decision across direct, human and MCP adapters."""

import asyncio
import importlib.util
import json
import sys
import threading
import types
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock

import pytest

from mythic_agent.agents.tools import execute_tool, prompt_approval_sync, auto_git_commit
from mythic_agent.core.policy import ToolPolicy, policy_mode
from mythic_agent.core.runtime import TurnCancelled


@pytest.mark.parametrize("name,args", [
    ("write_file", {"path": "new", "content": "x"}),
    ("replace_file_content", {"path": "new", "target_content": "x", "replacement_content": "y"}),
    ("run_command", {"command": "fixture command"}),
    ("github_execute", {"command": "gh issue create"}),
    ("delegate_task", {"sub_agent_name": "Architect", "task_description": "fixture"}),
    ("delegate_parallel_tasks", {"delegations": [{"sub_agent_name": "Architect", "task_description": "fixture"}]}),
    ("send_message", {"recipient": "Architect", "message": "fixture"}),
    ("core_memory_append", {"block": "persona", "content": "x"}),
    ("core_memory_replace", {"block": "persona", "content": "x"}),
    ("archival_memory_insert", {"text": "x"}),
    ("update_status", {"project": "fixture", "status": "x"}),
    ("clear_context", {}),
])
def test_direct_mutators_without_policy_are_refused_before_effects(agent, monkeypatch, name, args):
    from mythic_agent.agents import tools, llm
    forbidden = Mock(side_effect=AssertionError("Unauthorized effect"))
    monkeypatch.setattr(tools, "EditJournal", forbidden)
    monkeypatch.setattr(tools, "run_process", forbidden)
    monkeypatch.setattr(llm.agent_manager, "spawn_subagent", forbidden)
    result = execute_tool(name, args, agent.project_root)
    assert "Permission denied" in result
    forbidden.assert_not_called()
    assert not (agent.project_root / "new").exists()


def test_attached_policy_is_checked_once_and_denials_are_recorded(agent):
    approval = Mock(return_value=True)
    agent.tool_policy = ToolPolicy("ask", approval)
    result = execute_tool("write_file", {"path": "created", "content": "value"}, agent=agent)
    assert "Successfully wrote" in result
    assert approval.call_count == 1
    approval.return_value = False
    assert "Permission denied" in execute_tool("write_file", {"path": "created", "content": "bad"}, agent=agent)
    assert (agent.project_root / "created").read_text() == "value"
    assert agent.tool_policy.denials == ["write_file"]


def test_missing_ui_broken_callback_and_truthy_nonbool_do_not_approve():
    assert prompt_approval_sync("fixture", None) is False
    for callback in (Mock(side_effect=EOFError), Mock(side_effect=ValueError), Mock(return_value="yes")):
        policy = ToolPolicy("ask", callback)
        assert policy.authorize("write_file", {}) is False
        assert policy.denials == ["write_file"]


def test_approval_timeout_cancel_and_late_allow_cannot_execute():
    callbacks = []
    class UI:
        def call_from_thread(self, method, *args):
            return method(*args)
        def action_request_approval(self, text, approve, reject):
            callbacks.append(approve)
            return object()
        def action_cancel_approval(self, modal):
            pass
    ui = UI()
    assert prompt_approval_sync("fixture", ui, timeout=0.05) is False
    callbacks[-1]()  # A late UI click cannot revive an expired request.
    cancel = threading.Event()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(prompt_approval_sync, "fixture", ui, cancel, 5)
        cancel.set()
        with pytest.raises(TurnCancelled):
            future.result(timeout=2)


def test_legacy_git_helper_defaults_to_refusal(agent, monkeypatch):
    from mythic_agent.agents import tools
    forbidden = Mock()
    monkeypatch.setattr(tools, "run_process", forbidden)
    assert "Permission denied" in auto_git_commit(agent.project_root, agent.project_root / "x", "fixture")
    forbidden.assert_not_called()


@pytest.mark.parametrize("method", ["_handle_gh", "_handle_commit", "_handle_test", "_handle_doctor", "_handle_undo", "_handle_issue", "_handle_pr"])
def test_private_slash_mutators_consult_policy(agent, monkeypatch, method):
    from mythic_agent.agents.command_handler import CommandHandler
    handler = CommandHandler.__new__(CommandHandler)
    handler.project_root, handler.policy = agent.project_root, ToolPolicy("read-only")
    forbidden = Mock()
    monkeypatch.setattr(handler, "_run", forbidden)
    getattr(handler, method)("fixture")
    assert handler.policy.denials
    forbidden.assert_not_called()


def test_delegation_and_ghost_inherit_permission_without_sharing_receipts(agent, monkeypatch):
    from mythic_agent.agents import llm
    monkeypatch.setattr(llm.config_manager, "load_config", lambda: agent.config.copy())
    monkeypatch.setattr(llm, "AGENT_REGISTRY", {})
    monkeypatch.setattr(llm.threading, "Thread", Mock())
    policy = ToolPolicy("ask", Mock(return_value=False))
    name = next(entry["name"] for entry in agent.config["sub_agents"] if entry["name"].startswith("Architect"))
    child = llm.agent_manager.spawn_subagent(name, agent.project_root, policy=policy)
    assert child.tool_policy.mode == "ask"
    assert child.tool_policy.authorize("write_file", {}) is False
    assert policy.denials == []
    agent.tool_policy = policy
    ghost = llm.agent_manager.spawn_ghost_agent(agent)
    assert ghost.tool_policy.mode == "ask"
    assert ghost.tool_policy.authorize("run_command", {}) is False
    # Independently loaded legacy defaults/hot reload cannot grant extra privilege.
    llm.agent_manager._on_config_reload({**agent.config, "auto_accept_permissions": True})
    for inherited in (child, ghost):
        inherited.bind_tui(object())
        assert inherited.tool_policy.mode == "ask"
    child.close()
    ghost.close()


def test_stop_cancels_active_agent_without_queuing_shutdown(agent, monkeypatch):
    from mythic_agent.agents import llm
    monkeypatch.setattr(llm, "AGENT_REGISTRY", {agent.name: agent})
    agent.inbox.put("queued request")
    llm.agent_manager._on_system_command("/stop", "")
    assert agent._cancel.is_set() and agent.inbox.empty()
    assert agent.cancelled_inputs == ["queued request"]
    assert agent.inbox.unfinished_tasks == 0
    assert llm.AGENT_REGISTRY[agent.name] is agent


def test_mcp_mutators_refuse_before_initializing_memory_or_agents(agent, monkeypatch):
    class FakeMCP:
        def __init__(self, *args):
            pass
        def tool(self):
            return lambda function: function
    fake = types.ModuleType("mcp.server.fastmcp")
    fake.FastMCP = FakeMCP
    monkeypatch.setitem(sys.modules, "mcp.server.fastmcp", fake)
    monkeypatch.setenv("MYTHIC_HEADLESS_MODE", "0")
    path = Path(importlib.util.find_spec("mythic_agent.mcp_server").origin)
    spec = importlib.util.spec_from_file_location("mythic_agent._mcp_policy_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    forbidden = Mock(side_effect=AssertionError("Unauthorized MCP effect"))
    monkeypatch.setattr(module, "CoreMemoryManager", forbidden)
    monkeypatch.setattr(module, "get_vector_provider", forbidden)
    monkeypatch.setattr(module.agent_manager, "spawn_subagent", forbidden)
    for mode in ("read-only", "ask"):
        monkeypatch.setattr(module, "machine_policy", lambda: ToolPolicy(mode))
        for result in (module.mythic_core_memory_append("persona", "x"),
                       module.mythic_archival_insert("x"), module.mythic_update_project_status("fixture", "x"),
                       module.mythic_delegate_to_subagent("Architect", "fixture")):
            assert "Permission denied" in result
    forbidden.assert_not_called()


def test_tui_approval_controls_the_shared_executor_and_cancels(agent):
    pytest.importorskip("textual")
    from textual.app import App
    from mythic_agent.ui.components.modals import CommandApproval
    class UI(App):
        requests = 0
        def action_request_approval(self, text, approve, reject):
            self.requests += 1
            modal = CommandApproval(text, approve, reject)
            self.push_screen(modal)
            return modal
        def action_cancel_approval(self, modal):
            if self.screen is modal:
                modal.action_reject()
    async def scenario():
        app = UI()
        async with app.run_test() as pilot:
            agent.bind_tui(app, mode="ask")
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(execute_tool, "write_file", {"path": "approved", "content": "[red]literal"}, agent=agent)
                for _ in range(20):
                    await pilot.pause(0.05)
                    if isinstance(app.screen, CommandApproval):
                        break
                assert await pilot.click("#allow")
                for _ in range(20):
                    await pilot.pause(0.05)
                    if future.done():
                        break
                assert "Successfully wrote" in future.result(timeout=3)
                assert app.requests == 1
                future = pool.submit(execute_tool, "write_file", {"path": "cancelled", "content": "x"}, agent=agent)
                for _ in range(20):
                    await pilot.pause(0.05)
                    if isinstance(app.screen, CommandApproval):
                        break
                agent.cancel()
                for _ in range(20):
                    await pilot.pause(0.05)
                    if future.done():
                        break
                with pytest.raises(TurnCancelled):
                    future.result(timeout=3)
                assert not (agent.project_root / "cancelled").exists()
    asyncio.run(scenario())


def test_explicit_override_and_machine_default_do_not_gain_legacy_trust():
    config = {"auto_accept_permissions": True}
    assert policy_mode(config) == "trusted"
    assert policy_mode(config, machine=True) == "read-only"
    assert policy_mode(config, override="read-only") == "read-only"


def test_terminal_approval_timeout_and_cancel_release_prompt(monkeypatch):
    from mythic_agent.terminal import _approve
    import prompt_toolkit
    from prompt_toolkit.output import defaults, DummyOutput
    monkeypatch.setattr(defaults, "create_output", lambda **kwargs: DummyOutput())
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(sys.stderr, "isatty", lambda: True)
    started, cleaned = threading.Event(), threading.Event()
    class Prompt:
        def __init__(self, **kwargs):
            pass
        async def prompt_async(self, text):
            started.set()
            try:
                await asyncio.sleep(60)
            finally:
                cleaned.set()
    monkeypatch.setattr(prompt_toolkit, "PromptSession", Prompt)
    assert _approve("write_file", {}, threading.Event(), timeout=0.05) is False
    assert cleaned.is_set()
    started.clear()
    cleaned.clear()
    cancel = threading.Event()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_approve, "write_file", {}, cancel, 5)
        assert started.wait(2)
        cancel.set()
        with pytest.raises(TurnCancelled):
            future.result(timeout=2)
    assert cleaned.is_set()
