"""Human and machine adapters over the shared Agent runtime."""

import asyncio
import json
import shlex
import sys
from pathlib import Path
from typing import Any

from .agents.llm import Agent
from .core.config_manager import config_manager
from .core.edits import EditJournal
from .core.policy import ToolPolicy, policy_mode
from .core.execution import run_cancellable_async, run_process
from .core.runtime import TurnCancelled, runtime_settings
from .core.redaction import SecretRedactor, redact_text
from .core.sessions import SessionStore
from .core.secure_api import subscribe, unsubscribe
from .core.workspace import resolve_file, resolve_workspace


def _approve(name: str, arguments: dict[str, Any], cancel=None, timeout=300) -> bool:
    if not sys.stdin.isatty() or not sys.stderr.isatty():
        return False
    sys.stderr.write(f"\nApprove {name}: {json.dumps(arguments, ensure_ascii=False)} [y/N]? ")
    sys.stderr.flush()
    try:
        if cancel is None:
            return input().strip().lower() in {"y", "yes"}
        from prompt_toolkit import PromptSession
        from prompt_toolkit.output.defaults import create_output
        async def answer():
            session = PromptSession(output=create_output(stdout=sys.stderr))
            return await asyncio.wait_for(session.prompt_async(""), timeout=timeout)
        value = run_cancellable_async(answer, cancel)
        return value.strip().lower() in {"y", "yes"}
    except (EOFError, OSError, asyncio.TimeoutError):
        return False


def configured_agent(args: Any, default_permission: str) -> Agent:
    config = config_manager.load_config()
    for name in ("model", "base_url"):
        value = getattr(args, name, None)
        if value:
            config[name] = value
    agent = Agent(project_root=args.workspace, config=config)
    mode = args.permission or policy_mode(config, machine=default_permission == "read-only")
    agent.tool_policy = ToolPolicy(mode, lambda name, arguments: _approve(
        name, agent.redactor.sanitize(arguments), agent._cancel,
        runtime_settings(agent.config)["approval_timeout"]))
    try:
        agent.attach_session(resume=getattr(args, "resume", None))
    except Exception:
        agent.close()
        raise
    return agent


def _release(agent: Agent) -> None:
    agent.close()


def recover_crashed_sessions(agent: Agent, interactive: bool = False,
                             console: Any = None) -> list[str]:
    """Startup crash check: replay journaled checkpoints left by a dead process.

    When ``interactive`` and stdin is a TTY the user is asked first; otherwise
    recovery is automatic.  Returns the recovered session ids.
    """
    store = getattr(agent, "_session_store", None)
    if store is None:
        return []
    pending = store.check_recovery()
    if not pending:
        return []
    notice = (f"[!] Detected {len(pending)} uncommitted checkpoint(s) from a "
              "previous crash. Session state may otherwise be lost.")
    if console is not None:
        console.print(notice)
    else:
        sys.stderr.write(notice + "\n")
    proceed = True
    if interactive and sys.stdin.isatty():
        try:
            answer = input("Recover them now? [Y/n] ").strip().lower()
        except (EOFError, OSError):
            answer = "n"
        proceed = answer in {"", "y", "yes"}
    if not proceed:
        return []
    recovered = store.recover_pending()
    done = f"[+] Recovered {len(recovered)} crashed session checkpoint(s)."
    if console is not None:
        console.print(done)
    else:
        sys.stderr.write(done + "\n")
    return recovered


def _json_line(value: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(value, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _event_callbacks(agent: Agent) -> dict[str, Any]:
    callbacks = {}
    names = {"agent_chat_chunk": "assistant_delta", "agent_chat_tool": "tool_progress",
             "agent_tool_denied": "permission_denied", "agent_token_update": "usage",
             "agent_command_output": "command_output"}
    for event, kind in names.items():
        def callback(_kind=kind, **payload):
            if payload.get("agent_name") == agent.name:
                _json_line(agent.redactor.sanitize({"schema_version": 1, "type": _kind, **payload}))
        callbacks[event] = callback
        subscribe(event, callback)
    return callbacks


def _result(agent: Agent | None, status: str, text: str = "", error: str | None = None) -> dict[str, Any]:
    result = {
        "schema_version": 1, "type": "result", "status": status,
        "text": text, "error": error,
        "workspace": str(agent.project_root) if agent else None,
        "model": agent.config.get("model") if agent else None,
        "total_tokens": agent.total_tokens if agent else 0,
        "permission": agent.tool_policy.mode if agent else None,
        "denied_tools": list(agent.tool_policy.denials) if agent else [],
        "session_id": agent.session_id if agent else None,
    }
    if agent:
        return agent.redactor.sanitize(result)
    if error:
        result["error"] = redact_text(error)
    return result


# Approximate blended USD cost per 1M tokens (in+out), used only when the
# session metadata does not carry an exact figure.
_DEFAULT_COST_PER_MTOK = 3.00
_MODEL_COST_PER_MTOK = {
    "gpt-4o": 3.75,
    "gpt-4o-mini": 0.375,
    "o1": 22.50,
    "o3-mini": 1.65,
}


def _estimate_cost_usd(total_tokens: int, model: str | None) -> float:
    """Estimate session cost; exact metadata figures win over the estimate."""
    if not isinstance(total_tokens, int) or total_tokens <= 0:
        return 0.0
    rate = _DEFAULT_COST_PER_MTOK
    if model:
        lowered = model.lower()
        for key, value in _MODEL_COST_PER_MTOK.items():
            if key in lowered:
                rate = value
                break
    return round(total_tokens / 1_000_000 * rate, 4)


def _enrich_session(store: Any, session: dict[str, Any]) -> dict[str, Any]:
    """Add model, cost, and task counts to a list_sessions row."""
    metadata = session.get("metadata") or {}
    model = metadata.get("model") or metadata.get("model_name")
    cost = metadata.get("cost_usd")
    if cost is None:
        cost = _estimate_cost_usd(session.get("total_tokens", 0), model)
    enriched = dict(session)
    enriched["model"] = model
    enriched["cost_usd"] = cost
    enriched["cost_estimated"] = metadata.get("cost_usd") is None
    try:
        counts = store.session_event_counts(session["id"])
    except Exception:
        counts = {"events": 0, "tasks": 0, "turns": 0}
    enriched["task_count"] = counts.get("tasks", 0)
    enriched["turn_count"] = counts.get("turns", 0)
    enriched["event_count"] = counts.get("events", 0)
    return enriched


def _session_matches(session: dict[str, Any], query: str) -> bool:
    """Case-insensitive substring match across id, status, model, and metadata."""
    needle = query.lower()

    def _flatten(value: Any) -> str:
        if isinstance(value, dict):
            return " ".join(_flatten(v) for v in value.values())
        if isinstance(value, (list, tuple)):
            return " ".join(_flatten(v) for v in value)
        return str(value) if value is not None else ""

    haystack = " ".join([
        str(session.get("id", "")),
        str(session.get("status", "")),
        str(session.get("model", "")),
        _flatten(session.get("metadata", {})),
    ]).lower()
    return needle in haystack


def session_command(args: Any) -> int:
    """Read-only listing/export without initializing an agent or provider client."""
    try:
        config = config_manager.load_config()
        workspace = resolve_workspace(args.workspace, config)
        store = SessionStore(workspace, config_manager.MYTHIC_DIR, SecretRedactor(config))
        if args.export:
            _json_line(store.export(args.export))
        else:
            sessions = [_enrich_session(store, s) for s in store.list_sessions()]
            query = getattr(args, "search", None)
            if query:
                sessions = [s for s in sessions if _session_matches(s, query)]
            _json_line({"schema_version": 1, "workspace": str(workspace),
                        "search": query, "sessions": sessions})
        return 0
    except Exception as exc:
        _json_line({"schema_version": 1, "status": "failed", "error": redact_text(str(exc))})
        return 1


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
        recover_crashed_sessions(agent, interactive=False)
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
        return True, False, "/help /clear /compact /model <name> [url] /status /session /add <path> /stop /undo /quit"
    if command == "/clear":
        agent._handle_clear_history(agent.name)
        return True, False, "Conversation cleared."
    if command == "/stop":
        agent.cancel()
        return True, False, "Stopped. Use Ctrl+C to interrupt an active turn."
    if command == "/compact":
        agent._handle_compact_history(agent.name)
        return True, False, "Earlier complete turns archived; transcript retained."
    if command == "/session":
        return True, False, f"Session: {agent.session_id}\nResume: mythic chat --workspace {shlex.quote(str(agent.project_root))} --resume {agent.session_id}"
    if command == "/model":
        values = shlex.split(arguments)
        if not values:
            return True, False, f"Model: {agent.config['model']} ({agent.config['base_url']})"
        if len(values) > 2:
            return True, False, "Usage: /model <name> [url]"
        agent.set_model(values[0], values[1] if len(values) == 2 else agent.config["base_url"])
        return True, False, f"Model changed to {values[0]}."
    if command == "/status":
        agent._cancel.clear()
        settings = runtime_settings(agent.config)
        result = run_process(["git", "status", "--short", "--branch"], agent.project_root,
                             cancel=agent._cancel, timeout=min(15, settings["command_timeout"]),
                             grace=settings["process_kill_grace"])
        return True, False, result.render()
    if command == "/add":
        values = shlex.split(arguments)
        if len(values) != 1:
            return True, False, "Usage: /add <path>"
        path = resolve_file(agent.project_root, values[0])
        content = path.read_text(encoding="utf-8")
        agent.add_context(f"File context ({path.relative_to(agent.project_root)}):\n{content}")
        return True, False, f"Added {values[0]} to context."
    if command == "/undo":
        if not agent.tool_policy.authorize("undo_edit", {}):
            return True, False, "Permission denied for undo_edit; no operation was performed."
        return True, False, EditJournal(agent.project_root).undo()
    return True, False, f"Unknown command: {command}. Use /help."


def chat_loop(args: Any) -> int:
    from rich.console import Console
    from rich.markdown import Markdown
    console = Console()
    try:
        agent = configured_agent(args, "ask")
    except Exception as exc:
        sys.stderr.write(redact_text(str(exc)) + "\n")
        return 1
    recover_crashed_sessions(agent, interactive=True, console=console)
    session = None
    if sys.stdin.isatty():
        from prompt_toolkit import PromptSession
        session = PromptSession()
    console.print(f"Mythic chat · {agent.project_root} · {agent.config['model']}")
    console.print(f"Session: {agent.session_id}", markup=False)
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
                        console.print(agent.redactor.text(text), markup=False)
                    if quit_chat:
                        break
                    continue
                agent.tool_policy.denials.clear()
                text = agent.chat(line)
                console.print(Markdown(agent.redactor.text(text)))
                if agent.tool_policy.denials:
                    console.print("Tools denied: " + ", ".join(agent.tool_policy.denials), markup=False)
            except EOFError:
                break
            except (KeyboardInterrupt, TurnCancelled):
                agent.cancel()
                console.print("Turn cancelled. You can continue or /quit.")
            except Exception as exc:
                console.print(agent.redactor.text(f"Error: {exc}"), markup=False)
    finally:
        _release(agent)
    return 0
