"""Human and machine adapters over the shared Agent runtime."""

import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

from .agents.llm import Agent
from .core.config_manager import config_manager
from .core.edits import EditJournal
from .core.policy import ToolPolicy
from .core.runtime import TurnCancelled
from .core.secure_api import subscribe, unsubscribe
from .core.workspace import resolve_file


def _approve(name: str, arguments: dict[str, Any]) -> bool:
    if not sys.stdin.isatty():
        return False
    sys.stderr.write(f"\nApprove {name}: {json.dumps(arguments, ensure_ascii=False)} [y/N]? ")
    sys.stderr.flush()
    return input().strip().lower() in {"y", "yes"}


def configured_agent(args: Any, default_permission: str) -> Agent:
    config = config_manager.load_config()
    for name in ("model", "base_url"):
        value = getattr(args, name, None)
        if value:
            config[name] = value
    agent = Agent(project_root=args.workspace, config=config)
    agent.tool_policy = ToolPolicy(args.permission or default_permission, _approve)
    return agent


def _release(agent: Agent) -> None:
    unsubscribe("agent_clear_history", agent._handle_clear_history)
    unsubscribe("agent_compact_history", agent._handle_compact_history)


def _json_line(value: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(value, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _event_callbacks(agent: Agent) -> dict[str, Any]:
    callbacks = {}
    names = {"agent_chat_chunk": "assistant_delta", "agent_chat_tool": "tool_progress",
             "agent_tool_denied": "permission_denied", "agent_token_update": "usage"}
    for event, kind in names.items():
        def callback(_kind=kind, **payload):
            if payload.get("agent_name") == agent.name:
                _json_line({"schema_version": 1, "type": _kind, **payload})
        callbacks[event] = callback
        subscribe(event, callback)
    return callbacks


def _result(agent: Agent | None, status: str, text: str = "", error: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": 1, "type": "result", "status": status,
        "text": text, "error": error,
        "workspace": str(agent.project_root) if agent else None,
        "model": agent.config.get("model") if agent else None,
        "total_tokens": agent.total_tokens if agent else 0,
        "permission": agent.tool_policy.mode if agent else None,
        "denied_tools": list(agent.tool_policy.denials) if agent else [],
    }


def _render_result(result: dict[str, Any], output_format: str) -> int:
    if output_format in {"json", "jsonl"}:
        _json_line(result)
    else:
        if result["text"]:
            sys.stdout.write(result["text"] + "\n")
        if result["error"]:
            sys.stderr.write(result["error"] + "\n")
    return {"completed": 0, "failed": 1, "invalid_input": 2,
            "approval_required": 3, "cancelled": 130}[result["status"]]


def run_once(args: Any) -> int:
    agent = None
    callbacks = {}
    try:
        prompt = args.prompt if args.prompt is not None else sys.stdin.read()
        if not prompt.strip():
            return _render_result(_result(None, "invalid_input", error="A nonempty prompt is required."), args.format)
        agent = configured_agent(args, "read-only")
        if args.format == "jsonl":
            callbacks = _event_callbacks(agent)
        text = agent.chat(prompt)
        if agent.tool_policy.denials:
            result = _result(agent, "approval_required", text,
                             "Some tools were denied by permission policy; inspect denied_tools.")
        else:
            result = _result(agent, "completed", text)
    except (TurnCancelled, KeyboardInterrupt):
        if agent:
            agent.cancel()
        result = _result(agent, "cancelled", error="Turn cancelled by user.")
    except Exception as exc:
        result = _result(agent, "failed", error=str(exc))
    finally:
        for event, callback in callbacks.items():
            unsubscribe(event, callback)
        if agent:
            _release(agent)
    return _render_result(result, args.format)


def _slash(agent: Agent, line: str) -> tuple[bool, bool, str]:
    command, _, arguments = line.partition(" ")
    if command in {"/quit", "/exit"}:
        return True, True, ""
    if command == "/help":
        return True, False, "/help /clear /model <name> [url] /status /add <path> /stop /undo /quit"
    if command == "/clear":
        agent._handle_clear_history(agent.name)
        return True, False, "Conversation cleared."
    if command == "/stop":
        agent.cancel()
        return True, False, "Stopped. Use Ctrl+C to interrupt an active turn."
    if command == "/model":
        values = shlex.split(arguments)
        if not values:
            return True, False, f"Model: {agent.config['model']} ({agent.config['base_url']})"
        if len(values) > 2:
            return True, False, "Usage: /model <name> [url]"
        agent.set_model(values[0], values[1] if len(values) == 2 else agent.config["base_url"])
        return True, False, f"Model changed to {values[0]}."
    if command == "/status":
        result = subprocess.run(["git", "status", "--short", "--branch"], cwd=agent.project_root,
                                capture_output=True, text=True, timeout=15)
        return True, False, result.stdout + result.stderr
    if command == "/add":
        values = shlex.split(arguments)
        if len(values) != 1:
            return True, False, "Usage: /add <path>"
        path = resolve_file(agent.project_root, values[0])
        content = path.read_text(encoding="utf-8")
        agent.add_context(f"File context ({path.relative_to(agent.project_root)}):\n{content}")
        return True, False, f"Added {values[0]} to context."
    if command == "/undo":
        if agent.tool_policy.mode == "read-only":
            return True, False, "Undo requires ask or trusted permission mode."
        return True, False, EditJournal(agent.project_root).undo()
    return True, False, f"Unknown command: {command}. Use /help."


def chat_loop(args: Any) -> int:
    from rich.console import Console
    from rich.markdown import Markdown
    console = Console()
    try:
        agent = configured_agent(args, "ask")
    except Exception as exc:
        sys.stderr.write(str(exc) + "\n")
        return 1
    session = None
    if sys.stdin.isatty():
        from prompt_toolkit import PromptSession
        session = PromptSession()
    console.print(f"Mythic chat · {agent.project_root} · {agent.config['model']}")
    console.print("Use /help for commands, /quit or Ctrl+D to leave, Ctrl+C to interrupt.")
    try:
        while True:
            try:
                line = session.prompt("You> ") if session else sys.stdin.readline()
                if not session and not line:
                    break
                line = line.strip()
                if not line:
                    continue
                if line.startswith("/"):
                    _, quit_chat, text = _slash(agent, line)
                    if text:
                        console.print(text, markup=False)
                    if quit_chat:
                        break
                    continue
                agent.tool_policy.denials.clear()
                text = agent.chat(line)
                console.print(Markdown(text))
                if agent.tool_policy.denials:
                    console.print("Tools denied: " + ", ".join(agent.tool_policy.denials), markup=False)
            except EOFError:
                break
            except (KeyboardInterrupt, TurnCancelled):
                agent.cancel()
                console.print("Turn cancelled. You can continue or /quit.")
            except Exception as exc:
                console.print(f"Error: {exc}", markup=False)
    finally:
        _release(agent)
    return 0
