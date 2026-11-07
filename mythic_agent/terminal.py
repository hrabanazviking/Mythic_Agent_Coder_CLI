"""Human and machine adapters over the shared Agent runtime."""

__all__ = [
    "Agent",
    "Any",
    "EditJournal",
    "Path",
    "SecretRedactor",
    "SessionStore",
    "ToolPolicy",
    "TurnCancelled",
    "chat_loop",
    "config_manager",
    "configured_agent",
    "policy_mode",
    "recover_crashed_sessions",
    "redact_text",
    "resolve_file",
    "resolve_workspace",
    "run_cancellable_async",
    "run_once",
    "run_process",
    "runtime_settings",
    "session_command",
    "subscribe",
    "unsubscribe",
]

import asyncio
import json
import shlex
import sys
from pathlib import Path
from typing import Any

from .agents.llm import Agent
from .core.config_manager import config_manager
from .core.recovery import recover_crashed_sessions
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
    def approve(name, arguments):
        # M-096: an exact remembered approval for this
        # command in this project answers first; every
        # other call takes the ordinary prompt road.
        if agent.remembered_approval_allows_tool(name, arguments):
            # M-109: a remembered approval is a human
            # approval already given - trailed as one.
            agent._note_audit_approval(
                name, True, "a remembered approval")
            return True
        decided = _approve(
            name, agent.redactor.sanitize(arguments), agent._cancel,
            runtime_settings(agent.config)["approval_timeout"])
        # M-109: the human's answer at the prompt is
        # trailed as an approval, granted or refused.
        agent._note_audit_approval(
            name, decided, "the approval prompt")
        return decided
    agent.tool_policy = ToolPolicy(mode, approve)
    try:
        agent.attach_session(resume=getattr(args, "resume", None))
    except Exception:
        agent.close()
        raise
    return agent


def _release(agent: Agent) -> None:
    agent.close()


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
        return True, False, "/help /clear /compact /model <name> [url] /route [office] /fallback [on|off|add|clear] /costroute [on|off|<task-class>] /editformat [auto|<format>|<task-kind>] /hashanchor [on|off] /repairloop [on|off] /hunkreview [on|off] /changeset [on|off] /rename [on|off|<old-path> <new-path>] /generated [on|off|<path>|mark <path> <generator>] /largefile [on|off|<path>]/largefile [on|off|<path>] /stash [show|on|off|shelve <name>|restore <name>|drop <name>] /patch [show|on|off|export <set name>|import <patch file>] /editor [show|on|off|file <path>|prompt] /diff [show|on|off|unified|side-by-side|whitespace|whitespace off] /blame [show|on|off|<path> [<line>]] /massedit [show|on|off] /posture [show|<profile name>] /remember [list|forget <id>|clear] /sandbox [show|on|off|truth|plan <command>] /network [show|on|off|list|check <tool> <host>|allow <tool> <domain>] /pathjail [show|on|off|grants|check <path>|grant <abs-path>] /plan [show|on|off|approve|build|check <effect>] /hooks [show|show <event>|check <event>] /hookpacks [show|show <pack>|install <pack>] /background [show|show <job>|tail [<job>]|kill <job>|start <command...>] /keeper [show|show <target>|check|heartbeat <target>] /schedule [show|show <job>|check] /fleet [show|show <task>|verdict|resume] /budgets [show|show <budget>|check|check <budget>] /halt [show|show <halt>|pull|pull <target>] /audit [show|show <entry>|export] /secrets [show|show <screening>|check <file>] /doctrine [show|show <judgement>|ladder|check <command>] /rollback [show|show <run>|drills|run <drill>] /multirepo [show|show <set>|repos] /remote [show|show <plan>|targets] /grace [show|show <record>|failures] /moment [show|show <record>|parts] /policy [show|plan|sections|apply] /crew [show|show <member>|office <office>] /offices [show|show <office>|handoffs <office>|contract <from> <to>] /offices custom [show|show <office>|handoffs <office>|contract <from> <to>] /worktrees [show|show <member>|plan|merges] /issueslice [on|off|github <number>] /prcraft [on|off|tasks <pr>] /commitcraft [on|off|plan|commit <concern>|push] /guardians [word on|word off|check <path>] /autocommit [on|off|allow-protected|block-protected] /checkpoint [take <name>|restore <name> [discard]|on|off] /branch [on|off|fork <index> [name]|list|compare <id> <id>] /kista [adopt] /resume-thought [show] /retry [show] /vision [show|switch] /longcontext [show|<model>] /offline [show] /testkit <provider> [url] /map [task|show <path>|pin <path>|unpin <path>|pins] /ssearch <language> <pattern> /srewrite [apply] <language> <pattern> => <replacement> /lsp [show|check <path>|def <path> <line> <col>|refs <path> <line> <col>|hover <path> <line> <col>|symbols [query]] /truth <path> /format <path> [apply] /status /session /add <path> /stop /undo [list|edit|command|checkpoint <id>|<count>|on|off] /quit"
        return True, False, "/help /clear /compact /model <name> [url] /route [office] /fallback [on|off|add|clear] /costroute [on|off|<task-class>] /editformat [auto|<format>|<task-kind>] /hashanchor [on|off] /repairloop [on|off] /hunkreview [on|off] /issueslice [on|off|github <number>] /prcraft [on|off|tasks <pr>] /checkpoint [take <name>|restore <name> [discard]|on|off] /branch [on|off|fork <index> [name]|list|compare <id> <id>] /kista [adopt] /resume-thought [show] /retry [show] /vision [show|switch] /longcontext [show|<model>] /offline [show] /testkit <provider> [url] /map [task|show <path>|pin <path>|unpin <path>|pins] /ssearch <language> <pattern> /srewrite [apply] <language> <pattern> => <replacement> /lsp [show|check <path>|def <path> <line> <col>|refs <path> <line> <col>|hover <path> <line> <col>|symbols [query]] /truth <path> /format <path> [apply] /status /session /add <path> /stop /undo [list|edit|command|checkpoint <id>|<count>|on|off] /quit"
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
    if command == "/route":
        from .core.role_routing import (
            format_route_change,
            format_routes,
            parse_route_args,
            resolve_route,
        )
        try:
            request = parse_route_args(arguments)
        except (ValueError, KeyError) as exc:
            return True, False, str(exc)
        if request["action"] == "list":
            return True, False, format_routes(agent.config)
        if request["action"] == "show":
            try:
                route = resolve_route(agent.config, request["office"])
                shown = agent.role_route(request["office"])
            except ValueError as exc:
                return True, False, str(exc)
            assert shown["source"] == route.source
            return True, False, f"{route.office}: {route.describe()}"
        try:
            if request["action"] == "clear":
                record = agent.clear_role_route(request["office"])
            else:
                record = agent.set_role_route(
                    request["office"], model=request["model"],
                    provider=request["provider"],
                    base_url=request["base_url"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_route_change(record)
    if command == "/fallback":
        from .core.fallback_chain import (
            chain_from_config,
            format_chain,
            format_fallback_change,
            parse_fallback_args,
            permission_from_config,
        )
        try:
            request = parse_fallback_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.fallback_status()
            assert status["permission"] == permission_from_config(agent.config)
            assert [(c["model"], c["base_url"]) for c in status["chain"]] == [
                (e.model, e.base_url) for e in chain_from_config(agent.config)]
            return True, False, format_chain(agent.config)
        try:
            if request["action"] == "permission":
                record = agent.set_fallback_permission(request["enabled"])
            elif request["action"] == "clear":
                record = agent.clear_fallback_chain()
            else:
                record = agent.add_fallback_entry(
                    model=request["model"], provider=request["provider"],
                    base_url=request["base_url"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_fallback_change(record)
    if command == "/costroute":
        from .core.cost_routing import (
            candidate_doors,
            enabled_from_config,
            format_cost_change,
            format_cost_routing,
            format_decision,
            parse_cost_args,
        )
        try:
            request = parse_cost_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.cost_routing_status()
            assert status["enabled"] == enabled_from_config(agent.config)
            assert [d["model"] for d in status["doors"]] == [
                d.model for d in candidate_doors(agent.config)]
            return True, False, format_cost_routing(agent.config)
        try:
            if request["action"] == "setting":
                record = agent.set_cost_routing(request["enabled"])
                return True, False, format_cost_change(record)
            applied = agent.cost_route(request["task_class"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_decision(applied["decision"])
    if command == "/editformat":
        from .core.edit_formats import (
            format_choice,
            format_edit_formats,
            format_setting_change,
            parse_editformat_args,
            setting_from_config,
        )
        try:
            request = parse_editformat_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.edit_format_status()
            assert status["setting"] == setting_from_config(agent.config)
            return True, False, format_edit_formats(agent.config)
        try:
            if request["action"] == "setting":
                record = agent.set_edit_format(request["value"])
                return True, False, format_setting_change(record)
            record = agent.choose_edit_format(request["task_kind"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_choice(record["choice"])
    if command == "/hashanchor":
        from .core.hash_anchored import (
            enabled_from_config,
            format_hash_anchored,
            format_setting_change,
            parse_hashanchor_args,
        )
        try:
            request = parse_hashanchor_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.hash_anchor_status()
            assert status["enabled"] == enabled_from_config(agent.config)
            return True, False, format_hash_anchored(agent.config)
        try:
            record = agent.set_hash_anchored(request["enabled"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_setting_change(record)
    if command == "/repairloop":
        from .core.apply_repair import (
            enabled_from_config,
            format_apply_repair,
            format_setting_change,
            parse_repairloop_args,
        )
        try:
            request = parse_repairloop_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.repair_loop_status()
            assert status["enabled"] == enabled_from_config(agent.config)
            return True, False, format_apply_repair(agent.config)
        try:
            record = agent.set_apply_repair(request["enabled"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_setting_change(record)
    if command == "/hunkreview":
        from .core.hunk_review import (
            enabled_from_config,
            format_hunk_review,
            format_setting_change,
            parse_hunkreview_args,
        )
        try:
            request = parse_hunkreview_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.hunk_review_status()
            assert status["enabled"] == enabled_from_config(agent.config)
            return True, False, format_hunk_review(agent.config)
        try:
            record = agent.set_hunk_review(request["enabled"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_setting_change(record)
    if command == "/changeset":
        from .core.change_sets import (
            enabled_from_config,
            format_change_sets,
            format_setting_change,
            parse_changeset_args,
        )
        try:
            request = parse_changeset_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.change_set_status()
            assert status["enabled"] == enabled_from_config(agent.config)
            return True, False, format_change_sets(agent.config)
        try:
            record = agent.set_change_sets(request["enabled"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_setting_change(record)
    if command == "/rename":
        from .core.rename_move import (
            enabled_from_config,
            format_move_record,
            format_rename_move,
            format_setting_change,
            parse_rename_args,
        )
        try:
            request = parse_rename_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.rename_move_status()
            assert status["enabled"] == enabled_from_config(agent.config)
            return True, False, format_rename_move(agent.config)
        try:
            if request["action"] in ("on", "off"):
                record = agent.set_rename_move(request["action"] == "on")
                return True, False, format_setting_change(record)
            record = agent.rename_move_file(
                request["source"], request["destination"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_move_record(record)
    if command == "/generated":
        from .core.generated_code import (
            enabled_from_config,
            format_generated_code,
            format_generated_record,
            format_setting_change,
            parse_generated_args,
        )
        try:
            request = parse_generated_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.generated_code_status()
            assert status["enabled"] == enabled_from_config(agent.config)
            return True, False, format_generated_code(agent.config)
        try:
            if request["action"] in ("on", "off"):
                record = agent.set_generated_code(request["action"] == "on")
                return True, False, format_setting_change(record)
            if request["action"] == "check":
                data = agent.check_generated_code(request["path"])
            else:
                data = agent.mark_generated_file(
                    request["path"], request["generator"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_generated_record(data)
    if command == "/largefile":
        from .core.large_file_care import (
            enabled_from_config,
            format_file_care,
            format_large_file_care,
            format_setting_change,
            parse_largefile_args,
        )
        try:
            request = parse_largefile_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.large_file_care_status()
            assert status["enabled"] == enabled_from_config(agent.config)
            return True, False, format_large_file_care(agent.config)
        try:
            if request["action"] in ("on", "off"):
                record = agent.set_large_file_care(request["action"] == "on")
                return True, False, format_setting_change(record)
            data = agent.check_large_file(request["path"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        text = format_file_care(data)
        if data.get("chunk_plan"):
            text = text + "\n" + data["chunk_plan"]
        return True, False, text

    if command == "/stash":
        from .core.stash_shelf import (
            enabled_from_config,
            format_setting_change,
            format_shelf_entry,
            format_shelf_list,
            format_stash_shelf,
            parse_stash_args,
        )
        try:
            request = parse_stash_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.stash_shelf_status()
            assert status["enabled"] == enabled_from_config(agent.config)
            return True, False, (format_stash_shelf(agent.config)
                                 + "\n" + format_shelf_list(
                                     status["entries"]))
        try:
            if request["action"] in ("on", "off"):
                record = agent.set_stash_shelf(request["action"] == "on")
                return True, False, format_setting_change(record)
            if request["action"] == "shelve":
                record = agent.shelve_stash(request["name"])
                return True, False, (
                    f"Shelved {record['name']!r} - the tree is back "
                    "to its base.\n" + format_shelf_entry(record["entry"]))
            if request["action"] == "restore":
                record = agent.restore_stash(request["name"])
                return True, False, (
                    f"Restored {record['name']!r}: {record['files']} "
                    "file(s) back in the tree, off the shelf.")
            record = agent.drop_stash(request["name"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, (
            f"Dropped {record['name']!r} from the stash shelf; "
            "the tree was not changed.")
    if command == "/patch":
        from .core.patch_exchange import (
            enabled_from_config,
            format_patch_exchange,
            format_setting_change,
            parse_patch_args,
        )
        try:
            request = parse_patch_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.patch_exchange_status()
            assert status["enabled"] == enabled_from_config(agent.config)
            return True, False, format_patch_exchange(agent.config)
        try:
            if request["action"] in ("on", "off"):
                record = agent.set_patch_exchange(request["action"] == "on")
                return True, False, format_setting_change(record)
            if request["action"] == "import":
                record = agent.import_patch_from_file(request["ref"])
                return True, False, (
                    f"Imported patch {record['name']!r} from "
                    f"{record['source']}: {record['applied']} file(s) "
                    f"applied, {record['changed_files']} changed.")
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, (
            f"There is no change set named {request['name']!r} held "
            "by this session - change sets are values the agent layer "
            "builds and applies (M-084), not a stored shelf; export "
            "one through the agent road (export_patch_to_file) with "
            "the set itself. Nothing was exported.")
    if command == "/editor":
        from .core.editor_bridge import (
            enabled_from_config,
            format_editor_bridge,
            format_setting_change,
            parse_editor_args,
        )
        try:
            request = parse_editor_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.editor_bridge_status()
            assert status["enabled"] == enabled_from_config(agent.config)
            return True, False, format_editor_bridge(agent.config)
        try:
            if request["action"] in ("on", "off"):
                record = agent.set_editor_bridge(request["action"] == "on")
                return True, False, format_setting_change(record)
            if request["action"] == "file":
                record = agent.edit_file_in_editor(request["path"])
                text = (f"Editor round-trip (file) {record['label']}: "
                        f"{record['status']}\n  {record['reason']}")
                if record["status"] == "changed":
                    text += "\n  The changed text was written to the file."
                return True, False, text
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, (
            "This surface holds no draft - a prompt round-trip runs "
            "through the agent road (edit_prompt_in_editor) with the "
            "draft text itself. Nothing was sent.")
    if command == "/diff":
        from .core.diff_theatre import (
            enabled_from_config,
            format_diff_theatre,
            format_setting_change,
            parse_diff_args,
        )
        try:
            request = parse_diff_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.diff_theatre_status()
            assert status["enabled"] == enabled_from_config(agent.config)
            return True, False, format_diff_theatre(agent.config)
        demo_before = "alpha\nbeta old gamma\ndelta\n"
        demo_after = "alpha\nbeta new gamma\ndelta\n"
        try:
            if request["action"] in ("on", "off"):
                record = agent.set_diff_theatre(request["action"] == "on")
                return True, False, format_setting_change(record)
            if request["action"] == "view":
                record = agent.show_diff_theatre(
                    demo_before, demo_after, view=request["view"])
                return True, False, record["rendered"]
            record = agent.show_diff_theatre(
                demo_before, demo_after,
                ignore_whitespace=request["ignore_whitespace"])
            return True, False, record["rendered"]
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
    if command == "/blame":
        from .core.blame_sight import (
            enabled_from_config,
            format_blame_sight,
            format_setting_change,
            parse_blame_args,
        )
        try:
            request = parse_blame_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.blame_sight_status()
            assert status["enabled"] == enabled_from_config(agent.config)
            return True, False, format_blame_sight(agent.config)
        try:
            if request["action"] in ("on", "off"):
                record = agent.set_blame_sight(request["action"] == "on")
                return True, False, format_setting_change(record)
            record = agent.show_blame_sight(
                request["path"], request["line"])
            return True, False, record["rendered"]
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
    if command == "/massedit":
        from .core.mass_edit_guard import (
            enabled_from_config,
            format_mass_edit_guard,
            format_setting_change,
            parse_mass_edit_args,
        )
        try:
            request = parse_mass_edit_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.mass_edit_guard_status()
            assert status["enabled"] == enabled_from_config(agent.config)
            return True, False, format_mass_edit_guard(agent.config)
        try:
            record = agent.set_mass_edit_guard(request["action"] == "on")
            return True, False, format_setting_change(record)
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
    if command == "/posture":
        from .core.permission_profiles import (
            format_permission_profiles,
            format_profile_change,
            parse_posture_args,
            policy_mode_for,
            stored_profile,
        )
        try:
            request = parse_posture_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.permission_profile_status()
            assert status["policy_mode"] == policy_mode_for(
                stored_profile(agent.config))
            return True, False, format_permission_profiles(
                agent.config)
        try:
            record = agent.set_permission_profile(
                request["profile"])
            return True, False, format_profile_change(record)
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
    if command == "/remember":
        from .core.remembered_approvals import (
            PLAIN_EXPLANATION,
            USAGE,
            parse_remember_args,
            stored_approvals,
        )
        try:
            request = parse_remember_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "list":
            status = agent.remembered_approvals_status()
            assert status["count"] == len(
                stored_approvals(agent.config))
            return True, False, (
                "Remembered approvals (M-096) - "
                + PLAIN_EXPLANATION + "\n\n"
                + status["screen"] + "\n\n" + USAGE + "\n"
                "An approval is remembered only by your "
                "explicit yes at the approval prompt; "
                "/remember itself never creates one.")
        try:
            if request["action"] == "forget":
                record = agent.revoke_remembered_approval(
                    request["id"])
                args_text = " ".join(
                    record["args_pattern"]) or "(no args)"
                return True, False, (
                    f"Revoked remembered approval: "
                    f"{record['command']} {args_text} in "
                    f"{record['path']} [{record['id'][:12]}] - "
                    f"{record['total']} remembered now.")
            record = agent.clear_remembered_approvals()
            return True, False, (
                f"Cleared {record['cleared']} remembered "
                f"approval(s); none remain.")
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
    if command == "/sandbox":
        from .core.os_sandbox import (
            enabled_from_config,
            format_confinement_plan,
            format_gate_change,
            format_platform_truth,
            parse_sandbox_args,
        )
        try:
            request = parse_sandbox_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.os_sandbox_status()
            assert status["enabled"] == enabled_from_config(agent.config)
            return True, False, status["screen"]
        if request["action"] == "truth":
            return True, False, format_platform_truth()
        if request["action"] == "plan":
            try:
                plan = agent.os_sandbox_plan(
                    request["command"], platform=request["platform"])
            except ValueError as exc:
                return True, False, str(exc)
            return True, False, format_confinement_plan(plan)
        try:
            record = agent.set_os_sandbox(request["action"] == "on")
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_gate_change(record)
    if command == "/network":
        from .core.network_gates import (
            enabled_from_config,
            format_allowlist,
            format_gate_change,
            format_network_decision,
            gates_from_config,
            parse_network_args,
        )
        try:
            request = parse_network_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.network_gates_status()
            assert status["enabled"] == enabled_from_config(agent.config)
            return True, False, status["screen"]
        if request["action"] == "list":
            return True, False, format_allowlist(
                gates_from_config(agent.config).entries)
        if request["action"] == "check":
            try:
                decision = agent.check_network_reach(
                    request["tool"], request["target"])
            except ValueError as exc:
                return True, False, str(exc)
            return True, False, format_network_decision(decision)
        if request["action"] == "allow":
            try:
                record = agent.add_network_allowlist_entry(request["entry"])
            except (ValueError, KeyError, RuntimeError) as exc:
                return True, False, str(exc)
            entry = record["entry"]
            return True, False, (
                f"Network allowlist: {entry['tool']}: "
                f"{entry['domain']} added.")
        try:
            record = agent.set_network_gates(request["action"] == "on")
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_gate_change(record)
    if command == "/pathjail":
        from .core.path_jail import (
            enabled_from_config,
            format_gate_change,
            format_grants,
            format_jail_decision,
            grants_from_config,
            parse_pathjail_args,
        )
        try:
            request = parse_pathjail_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.path_jail_status()
            assert status["enabled"] == enabled_from_config(agent.config)
            return True, False, status["screen"]
        if request["action"] == "grants":
            return True, False, format_grants(
                grants_from_config(agent.config))
        if request["action"] == "check":
            try:
                decision = agent.check_path_jail(request["path"])
            except ValueError as exc:
                return True, False, str(exc)
            return True, False, format_jail_decision(decision)
        if request["action"] == "grant":
            try:
                record = agent.add_path_grant(request["grant"])
            except (ValueError, KeyError, RuntimeError) as exc:
                return True, False, str(exc)
            return True, False, f"Path grant: {record['grant']} added."
        try:
            record = agent.set_path_jail(request["action"] == "on")
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_gate_change(record)
    if command == "/plan":
        from .core.plan_mode import (
            enabled_from_config,
            format_gate_change,
            format_plan,
            format_refusal,
            parse_plan_args,
            refusal_for_build,
            refusal_for_effect,
        )
        try:
            request = parse_plan_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.plan_mode_status()
            assert status["enabled"] == enabled_from_config(agent.config)
            return True, False, status["screen"]
        if request["action"] == "check":
            try:
                decision = agent.check_plan_effect(request["effect"])
            except ValueError as exc:
                return True, False, str(exc)
            if decision == "allow":
                return True, False, (
                    f"Plan allowed: a {request['effect']} effect "
                    f"is allowed.")
            return True, False, format_refusal(
                refusal_for_effect(
                    enabled_from_config(agent.config),
                    request["effect"])) + "."
        if request["action"] == "approve":
            try:
                plan = agent.approve_current_plan()
            except ValueError as exc:
                return True, False, str(exc)
            return True, False, (
                f"Plan approved: {plan.title} - building is now "
                f"allowed in plan posture.\n" + format_plan(plan))
        if request["action"] == "build":
            if agent.check_plan_build():
                return True, False, (
                    "Building allowed: the build gate is open.")
            return True, False, format_refusal(
                refusal_for_build(
                    enabled_from_config(agent.config),
                    agent.current_plan())) + "."
        try:
            record = agent.set_plan_mode(request["action"] == "on")
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_gate_change(record)
    if command == "/hooks":
        from .core.hooks import (
            format_hooks,
            format_verdict,
            hooks_from_config,
            parse_hooks_args,
        )
        try:
            action, event = parse_hooks_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if action == "show":
            try:
                status = agent.hooks_status()
            except ValueError as exc:
                return True, False, str(exc)
            if event is None:
                return True, False, status["screen"]
            try:
                named = [h for h in hooks_from_config(agent.config)
                         if h.event == event]
            except ValueError as exc:
                return True, False, str(exc)
            return True, False, format_hooks(named)
        try:
            verdicts = agent.run_hooks(event)
        except ValueError as exc:
            return True, False, str(exc)
        if not verdicts:
            return True, False, (
                f"No hooks are configured for {event}; "
                f"nothing ran.")
        return True, False, "\n".join(
            format_verdict(v) for v in verdicts)
    if command == "/hookpacks":
        from .core.hook_packs import (
            format_pack,
            get_pack,
            parse_hook_packs_args,
        )
        from .core.hooks import format_hooks
        try:
            action, pack_name = parse_hook_packs_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if action == "show":
            if pack_name is None:
                try:
                    status = agent.hook_packs_status()
                except ValueError as exc:
                    return True, False, str(exc)
                return True, False, status["screen"]
            pack = get_pack(pack_name)
            return True, False, (
                format_pack(pack) + "\n"
                + format_hooks(list(pack.hooks)))
        try:
            record = agent.install_hook_pack(pack_name)
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        if not record["changed"]:
            return True, False, (
                f"Hook pack {pack_name} is already installed; "
                f"nothing changed.")
        return True, False, (
            f"Hook pack installed: {pack_name} "
            f"({len(record['added'])} hook(s) added).")
    if command == "/background":
        from .core.background_tasks import (
            format_completion,
            format_job,
            parse_background_args,
        )
        try:
            action, target = parse_background_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if action == "show":
            if target is None:
                return True, False, agent.background_jobs_status()["screen"]
            try:
                job = agent.get_background_job(target)
            except KeyError as exc:
                return True, False, str(exc)
            return True, False, format_job(job)
        if action == "tail":
            try:
                return True, False, agent.background_job_tail(target)
            except (KeyError, ValueError) as exc:
                return True, False, str(exc)
        if action == "kill":
            try:
                agent.kill_background_job(target)
                job = agent.get_background_job(target)
            except (KeyError, ValueError) as exc:
                return True, False, str(exc)
            return True, False, format_completion(job)
        try:
            argv = shlex.split(target)
        except ValueError as exc:
            return True, False, str(exc)
        try:
            record = agent.start_background_job(argv)
        except (ValueError, OSError) as exc:
            return True, False, str(exc)
        job = agent.get_background_job(record["job_id"])
        return True, False, f"Background job started: {format_job(job)}"
    if command == "/keeper":
        import time as _time

        from .core.keeper import format_watch_target, parse_keeper_args
        try:
            action, target = parse_keeper_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if action == "show":
            if target is None:
                return True, False, agent.keeper_status()["screen"]
            try:
                watched = agent.get_keeper_target(target)
            except KeyError as exc:
                return True, False, str(exc)
            return True, False, format_watch_target(watched, _time.time())
        if action == "check":
            return True, False, agent.keeper_check()["screen"]
        try:
            agent.keeper_heartbeat(target)
            watched = agent.get_keeper_target(target)
        except (KeyError, ValueError) as exc:
            return True, False, str(exc)
        return True, False, format_watch_target(watched, _time.time())
    if command == "/schedule":
        from .core.scheduled_work import (
            format_verdict,
            parse_schedule_args,
        )
        try:
            action, target = parse_schedule_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if action == "show":
            if target is None:
                return True, False, agent.scheduled_work_status()["screen"]
            try:
                verdict = agent.get_scheduled_verdict(target)
            except KeyError as exc:
                return True, False, str(exc)
            return True, False, format_verdict(verdict)
        return True, False, agent.scheduled_check()["screen"]
    if command == "/fleet":
        from .core.fleet_mode import (
            format_fleet_task,
            parse_fleet_args,
        )
        try:
            action, target = parse_fleet_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if action == "show":
            if target is None:
                return True, False, agent.fleet_status()["screen"]
            try:
                task = agent.get_fleet_task(target)
                verdict = agent.get_fleet_verdict(target)
            except KeyError as exc:
                return True, False, str(exc)
            return True, False, format_fleet_task(task, verdict)
        if action == "verdict":
            return True, False, agent.fleet_status()["verdict_screen"]
        return True, False, agent.fleet_resume_plan()["screen"]
    if command == "/budgets":
        from .core.budgets import (
            format_budget,
            parse_budgets_args,
        )
        try:
            action, target = parse_budgets_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if action == "show":
            if target is None:
                return True, False, agent.budget_status()["screen"]
            try:
                budget = agent.get_budget(target)
                verdict = agent.get_budget_verdict(target)
            except KeyError as exc:
                return True, False, str(exc)
            return True, False, format_budget(budget, verdict)
        if target is None:
            return True, False, agent.budget_check()["screen"]
        try:
            return True, False, agent.budget_check(target)["screen"]
        except KeyError as exc:
            return True, False, str(exc)
    if command == "/halt":
        from .core.kill_switch import (
            format_halt,
            parse_halt_args,
        )
        try:
            action, target = parse_halt_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if action == "show":
            if target is None:
                return True, False, agent.kill_switch_status()["screen"]
            try:
                halt = agent.get_halt(target)
                verdict = agent.get_halt_verdict(target)
            except KeyError as exc:
                return True, False, str(exc)
            return True, False, format_halt(halt, verdict)
        spec: dict = {"actor": "user"}
        if target is not None:
            spec["targets"] = [target]
        return True, False, agent.pull_kill_switch(spec)["screen"]
    if command == "/audit":
        from .core.audit_trail import (
            format_entry,
            parse_audit_args,
        )
        try:
            action, target = parse_audit_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if action == "export":
            return True, False, agent.audit_export()["text"]
        if target is None:
            return True, False, agent.audit_status()["screen"]
        try:
            entry = agent.get_audit_entry(target)
        except KeyError as exc:
            return True, False, str(exc)
        return True, False, format_entry(entry)
    if command == "/secrets":
        # M-110 terminal road: show the held screenings,
        # show one screening, or screen one project file.
        from .core.secret_hygiene import format_screening as _fmt_scr, parse_secrets_args as _parse_sec
        try:
            _act, _tgt = _parse_sec(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "check":
            try:
                _res = agent.screen_project_file(_tgt)
            except ValueError as _exc:
                return True, False, str(_exc)
            return True, False, _res["screen"]
        if _tgt is None:
            return True, False, agent.secret_hygiene_status()["screen"]
        try:
            _one = agent.get_screening(_tgt)
        except KeyError as _exc:
            return True, False, str(_exc)
        return True, False, _fmt_scr(_one)
    if command == "/doctrine":
        # M-111 terminal road: show the held judgements,
        # show one judgement, show the ladder alone, or
        # judge one command now and hold the judgement.
        from .core.destructive_doctrine import format_judgement as _fmt_jdg, format_ladder as _fmt_lad, parse_doctrine_args as _parse_doc
        try:
            _act, _tgt = _parse_doc(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "ladder":
            return True, False, _fmt_lad()
        if _act == "check":
            return True, False, agent.judge_command(_tgt)["screen"]
        if _tgt is None:
            return True, False, agent.doctrine_status()["screen"]
        try:
            _one = agent.get_judgement(_tgt)
        except KeyError as _exc:
            return True, False, str(_exc)
        return True, False, _fmt_jdg(_one)
    if command == "/rollback":
        # M-112 terminal road: show the held results,
        # show one run, show the drill book alone, or
        # name the one drill a run would exercise.
        from .core.rollback_drills import format_drill as _fmt_drl, format_drills as _fmt_drls, format_result as _fmt_res, parse_rollback_args as _parse_rb
        try:
            _act, _tgt = _parse_rb(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "drills":
            return True, False, _fmt_drls()
        if _act == "run":
            return True, False, _fmt_drl(_tgt)
        if _tgt is None:
            return True, False, agent.rollback_status()["screen"]
        try:
            _one = agent.get_drill_run(_tgt)
        except KeyError as _exc:
            return True, False, str(_exc)
        return True, False, _fmt_res(_one)
    if command == "/multirepo":
        # M-113 terminal road: show the workspace and
        # its sets, show one set, or show the held
        # repos alone.
        from .core.multi_repo import format_cross_set as _fmt_xset, format_repos as _fmt_repos, parse_multirepo_args as _parse_mr
        try:
            _act, _tgt = _parse_mr(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "repos":
            return True, False, _fmt_repos(agent._multi_repo_registry())
        if _tgt is None:
            return True, False, agent.multi_repo_status()["screen"]
        try:
            _one = agent.get_cross_repo_set(_tgt)
        except KeyError as _exc:
            return True, False, str(_exc)
        return True, False, _fmt_xset(_one)
    if command == "/remote":
        # M-114 terminal road: show the targets and
        # their plans, show one plan, or show the
        # held targets alone.
        from .core.remote_work import format_targets as _fmt_tgts, format_work_plan as _fmt_plan, parse_remote_args as _parse_rw
        try:
            _act, _tgt = _parse_rw(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "targets":
            return True, False, _fmt_tgts(agent._remote_work_registry())
        if _tgt is None:
            return True, False, agent.remote_work_status()["screen"]
        try:
            _one = agent.get_remote_work_plan(_tgt)
        except KeyError as _exc:
            return True, False, str(_exc)
        return True, False, _fmt_plan(_one)
    if command == "/grace":
        # M-115 terminal road: show the records held
        # this session, show one record, or show the
        # failure kinds alone.
        from .core.offline_grace import format_assessment as _fmt_assess, format_failures as _fmt_fails, parse_grace_args as _parse_grace
        try:
            _act, _tgt = _parse_grace(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "failures":
            return True, False, _fmt_fails()
        if _tgt is None:
            return True, False, agent.grace_status()["screen"]
        try:
            _one = agent.get_grace_record(_tgt)
        except KeyError as _exc:
            return True, False, str(_exc)
        return True, False, _fmt_assess(_one)
    if command == "/moment":
        # M-116 terminal road: show the moments held
        # this session, show one moment, or show the
        # required parts alone.
        from .core.approval_moments import format_assessment as _fmt_moment_assess, format_parts as _fmt_mparts, parse_moment_args as _parse_moment
        try:
            _act, _tgt = _parse_moment(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "parts":
            return True, False, _fmt_mparts()
        if _tgt is None:
            return True, False, agent.approval_moment_status()["screen"]
        try:
            _one = agent.get_approval_moment(_tgt)
        except KeyError as _exc:
            return True, False, str(_exc)
        return True, False, _fmt_moment_assess(_one)
    if command == "/policy":
        # M-119 terminal road: show the current policy
        # state, the data-only plan for the file on
        # disk, its sections, or load and apply it.
        from .core.policy_file import format_plan as _fmt_pol_plan, format_policy_sections as _fmt_pol_sections, parse_policy_args as _parse_policy
        try:
            _req = _parse_policy(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _req["action"] == "show":
            return True, False, agent.project_policy_status()["screen"]
        if _req["action"] == "apply":
            return True, False, agent.apply_project_policy()["screen"]
        try:
            _pol = agent.policy_on_disk()
        except ValueError as _exc:
            return True, False, "Project policy refused: " + str(_exc)
        if _req["action"] == "plan":
            return True, False, _fmt_pol_plan(_pol)
        return True, False, _fmt_pol_sections(_pol)
    if command == "/crew":
        # M-121 terminal road: show the crew held
        # this session (the shipped casting when none
        # is held), show one member, or show the
        # member holding one office.
        from .core.crew_members import format_member as _fmt_crew_member, parse_crew_args as _parse_crew
        try:
            _act, _tgt = _parse_crew(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "office":
            try:
                _one = agent.crew_member_for_office(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_crew_member(_one)
        if _tgt is None:
            return True, False, agent.crew_status()["screen"]
        try:
            _one = agent.find_crew_member(_tgt)
        except (KeyError, ValueError) as _exc:
            return True, False, str(_exc)
        return True, False, _fmt_crew_member(_one)
    if command == "/offices":
        # M-122 terminal road: show the offices held
        # this session (the shipped book when none is
        # held), show one office, show one office's
        # hand-offs, or show one hand-off contract.
        # M-123 terminal road: /offices custom shows
        # the custom offices held this session (the
        # shipped custom book when none is held), one
        # custom office, its hand-offs, or one contract,
        # on the pure layer's custom parser + formatters.
        _words = arguments.strip().split() if arguments else []
        if _words and _words[0].lower() == "custom":
            from .core.custom_offices import format_custom_office as _fmt_custom, parse_custom_offices_args as _parse_custom
            try:
                _act, _tgt = _parse_custom(" ".join(_words[1:]))
            except ValueError as _exc:
                return True, False, str(_exc)
            if _act == "handoffs":
                try:
                    _one = agent.find_custom_office_definition(_tgt)
                except (KeyError, ValueError) as _exc:
                    return True, False, str(_exc)
                _lines = [_fmt_custom(_one)]
                for _c in _one.handoffs:
                    _lines.append(f"  -> {_c.to_office}: {_c.artifact} - {_c.condition}")
                return True, False, "\n".join(_lines)
            if _act == "contract":
                _from, _to = _tgt
                try:
                    _c = agent.custom_office_contract(_from, _to)
                except (KeyError, ValueError) as _exc:
                    return True, False, str(_exc)
                return True, False, f"  {_from} -> {_to}: {_c.artifact} - {_c.condition}"
            if _tgt is None:
                return True, False, agent.custom_offices_status()["screen"]
            try:
                _one = agent.find_custom_office_definition(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_custom(_one)
        from .core.offices import format_office as _fmt_office, parse_offices_args as _parse_offices
        try:
            _act, _tgt = _parse_offices(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "handoffs":
            try:
                _one = agent.find_office_definition(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            _lines = [_fmt_office(_one)]
            for _c in _one.handoffs:
                _lines.append(f"  -> {_c.to_office}: {_c.artifact} - {_c.condition}")
            return True, False, "\n".join(_lines)
        if _act == "contract":
            _from, _to = _tgt
            try:
                _c = agent.office_contract(_from, _to)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, f"  {_from} -> {_to}: {_c.artifact} - {_c.condition}"
        if _tgt is None:
            return True, False, agent.offices_status()["screen"]
        try:
            _one = agent.find_office_definition(_tgt)
        except (KeyError, ValueError) as _exc:
            return True, False, str(_exc)
        return True, False, _fmt_office(_one)
    if command == "/worktrees":
        # M-124 terminal road: show the worktree
        # assignments held this session (the shipped
        # example plan when none is held), show one
        # member's assignment, show the whole plan,
        # or show the coordinator merge plan derived
        # in slice order, on the pure layer's parser
        # + formatters. This road runs no git command
        # and creates no worktree; the registry holds
        # the plan as data.
        from .core.worktrees import format_assignment as _fmt_wt, format_assignments as _fmt_wts, format_merge_plan as _fmt_merges, parse_worktrees_args as _parse_wt
        try:
            _act, _tgt = _parse_wt(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "plan":
            _plan = agent.worktree_plan()
            return True, False, _fmt_wts(_plan) + f"\nCoordinator: {_plan.coordinator} - the coordinator merges, and holds no worktree in the plan."
        if _act == "merges":
            return True, False, _fmt_merges(agent.worktree_plan())
        if _tgt is None:
            return True, False, agent.worktrees_status()["screen"]
        try:
            _one = agent.find_worktree_assignment(_tgt)
        except (KeyError, ValueError) as _exc:
            return True, False, str(_exc)
        return True, False, _fmt_wt(_one)
    if command == "/conflicts":
        from .core.conflict_workbench import (
            enabled_from_config,
            format_conflict_workbench,
            format_setting_change,
            parse_conflicts_args,
        )
        try:
            request = parse_conflicts_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.conflict_workbench_status()
            assert status["enabled"] == enabled_from_config(agent.config)
            return True, False, format_conflict_workbench(
                agent.config, agent.project_root)
        try:
            record = agent.set_conflict_workbench(request["enabled"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_setting_change(record)
    if command == "/checkpoint":
        from .core.checkpoints import (
            enabled_from_config,
            format_checkpoint_created,
            format_checkpoint_restored,
            format_checkpoints,
            format_setting_change,
            parse_checkpoint_args,
        )
        try:
            request = parse_checkpoint_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.checkpoint_status()
            assert status["enabled"] == enabled_from_config(agent.config)
            return True, False, format_checkpoints(
                agent.config, status["checkpoints"], status["head_id"])
        try:
            if request["action"] == "setting":
                record = agent.set_checkpoints(request["enabled"])
                return True, False, format_setting_change(record)
            if request["action"] == "take":
                taken = agent.take_checkpoint(request["name"])
                return True, False, format_checkpoint_created(taken)
            restored = agent.restore_checkpoint(
                request["name"], request["discard"])
            return True, False, format_checkpoint_restored(restored)
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
    if command == "/branch":
        from .core.session_branching import (
            enabled_from_config,
            format_branch_list,
            format_branching,
            format_comparison,
            format_fork,
            format_setting_change,
            parse_branch_args,
        )
        try:
            request = parse_branch_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.session_branching_status()
            assert status["enabled"] == enabled_from_config(agent.config)
            return True, False, format_branching(agent.config)
        try:
            if request["action"] == "setting":
                record = agent.set_session_branching(request["enabled"])
                return True, False, format_setting_change(record)
            if request["action"] == "fork":
                record = agent.fork_session(request["at_index"], request["name"])
                return True, False, format_fork(record)
            if request["action"] == "list":
                return True, False, format_branch_list(agent.list_session_branches())
            record = agent.compare_sessions(request["first_id"], request["second_id"])
            return True, False, format_comparison(record)
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)

    if command == "/autocommit":
        from .core.auto_commit import (
            enabled_from_config,
            format_auto_commit,
            format_setting_change,
            parse_autocommit_args,
        )
        try:
            request = parse_autocommit_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.auto_commit_status()
            assert status["enabled"] == enabled_from_config(agent.config)
            return True, False, format_auto_commit(agent.config)
        try:
            if request["action"] == "setting":
                record = agent.set_auto_commit(request["enabled"])
            else:
                record = agent.set_auto_commit_allow_protected(
                    request["allowed"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_setting_change(record)
    if command == "/guardians":
        from .core.file_guardians import (
            explicit_from_config,
            format_guard_check,
            format_guardians,
            format_setting_change,
            parse_guardians_args,
        )
        try:
            request = parse_guardians_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.guardian_status()
            assert status["explicit_word"] == explicit_from_config(agent.config)
            return True, False, format_guardians(agent.config)
        if request["action"] == "check":
            return True, False, format_guard_check(agent.config, request["path"])
        try:
            record = agent.set_guardian_word(request["enabled"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_setting_change(record)
    if command == "/commitcraft":
        from .core.commit_craft import (
            enabled_from_config,
            format_commit_craft,
            format_commit_record,
            format_plan,
            format_push_record,
            format_setting_change,
            parse_commitcraft_args,
        )
        try:
            request = parse_commitcraft_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.commit_craft_status()
            assert status["enabled"] == enabled_from_config(agent.config)
            return True, False, format_commit_craft(agent.config)
        if request["action"] == "setting":
            try:
                record = agent.set_commit_craft(request["enabled"])
            except (ValueError, KeyError, RuntimeError) as exc:
                return True, False, str(exc)
            return True, False, format_setting_change(record)
        if request["action"] == "plan":
            try:
                record = agent.plan_commit_split()
            except (ValueError, RuntimeError) as exc:
                return True, False, str(exc)
            return True, False, format_plan(record)
        if request["action"] == "commit":
            try:
                record = agent.commit_craft_group(request["concern"])
            except (ValueError, RuntimeError) as exc:
                return True, False, str(exc)
            return True, False, format_commit_record(record)
        try:
            record = agent.push_with_house_rules()
        except (ValueError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_push_record(record)
    if command == "/prcraft":
        from .core.pr_craft import (
            enabled_from_config,
            format_pr_craft,
            format_setting_change,
            format_tasks,
            parse_prcraft_args,
        )
        try:
            request = parse_prcraft_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.pr_craft_status()
            assert status["enabled"] == enabled_from_config(agent.config)
            return True, False, format_pr_craft(agent.config)
        if request["action"] == "tasks":
            try:
                fetched = agent.fetch_review_tasks(request["number"])
            except (ValueError, KeyError, RuntimeError) as exc:
                return True, False, str(exc)
            return True, False, format_tasks(fetched["tasks"])
        try:
            record = agent.set_pr_craft(request["enabled"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_setting_change(record)
    if command == "/issueslice":
        from .core.issue_slice import (
            enabled_from_config,
            format_issue_slice,
            format_plan_record,
            format_setting_change,
            parse_issueslice_args,
        )
        try:
            request = parse_issueslice_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.issue_slice_status()
            assert status["enabled"] == enabled_from_config(agent.config)
            return True, False, format_issue_slice(agent.config)
        if request["action"] == "plan":
            try:
                record = agent.plan_issue_slice(
                    request["source"], request["number"])
            except (ValueError, RuntimeError) as exc:
                return True, False, str(exc)
            return True, False, format_plan_record(record)
        try:
            record = agent.set_issue_slice(request["enabled"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_setting_change(record)
    if command == "/kista":
        from .core.key_custody import (
            custody_entries,
            format_custody,
            format_custody_change,
            parse_kista_args,
        )
        try:
            request = parse_kista_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.kista_status()
            assert [e["base_url"] for e in status["entries"]] == [
                e.base_url for e in custody_entries(agent.config)]
            return True, False, format_custody(agent.config)
        try:
            record = agent.adopt_key_for_kista(request["base_url"])
        except (ValueError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_custody_change(record)
    if command == "/retry":
        from .core.retry_honesty import (
            bounds_from_settings,
            format_retry_status,
            parse_retry_args,
        )
        try:
            request = parse_retry_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.retry_status()
            assert status["bounds"] == bounds_from_settings(
                runtime_settings(agent.config))
            assert status["report"] is agent.last_retry_report
            return True, False, format_retry_status(
                status["bounds"], status["report"])
    if command == "/weather":
        from .core.rate_limit_weather import (
            format_weather_status,
            parse_weather_args,
        )
        try:
            request = parse_weather_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.weather_status()
            board = agent._weather_board
            assert [p["provider"] for p in status["providers"]] == [
                w.provider for w in board.snapshot()]
            assert status["current_provider"] == agent._weather_key()
            return True, False, format_weather_status(
                board, extra_providers=[status["current_provider"]])
    if command == "/vision":
        from .core.model_capabilities import load_capabilities
        from .core.vision_routing import (
            format_vision_status,
            parse_vision_args,
            suggest_switch,
        )
        try:
            request = parse_vision_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.vision_status()
            caps = load_capabilities()
            model = agent.config.get("model")
            assert status["vision"] == (
                caps.for_model(model).vision if model else None)
            suggestion = suggest_switch(agent.config, caps)
            assert status["suggestion"] == (
                suggestion.selection() if suggestion is not None else None)
            return True, False, format_vision_status(status)
        try:
            record = agent.apply_vision_switch()
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        from .core.model_switch import format_switch_record
        return True, False, format_switch_record(record)
    if command == "/longcontext":
        from .core.long_context import (
            format_longcontext_status,
            parse_longcontext_args,
            strategy_for_model,
        )
        try:
            request = parse_longcontext_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        status = agent.context_strategy(request["model"])
        plan = strategy_for_model(request["model"]
                                  if request["model"] is not None
                                  else agent.config.get("model"))
        assert status["plan"] == plan.record()
        assert status["strategy"] == plan.strategy
        return True, False, format_longcontext_status(status)
    if command == "/offline":
        from .core.offline_honesty import (
            format_offline_status,
            parse_offline_args,
        )
        try:
            request = parse_offline_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.offline_status()
            from .core.offline_honesty import assess_board
            from .core.provider_health import Board, HealthEntry
            entries = tuple(HealthEntry(**e)
                            for e in status["board"]["entries"])
            board = Board(entries=entries,
                          generated_at=status["board"]["generated_at"])
            assert status["assessment"] == assess_board(board).record()
            return True, False, format_offline_status(status)
    if command == "/testkit":
        from .core.provider_test_kit import (
            format_kit_status,
            parse_kit_args,
        )
        try:
            request = parse_kit_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "run":
            try:
                status = agent.test_kit(request["provider"],
                                        base_url=request["base_url"])
            except KeyError as exc:
                return True, False, str(exc)
            return True, False, format_kit_status(status)
    if command == "/ssearch":
        from .tools.structural_search import (
            format_search_status,
            parse_search_args,
        )
        try:
            request = parse_search_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        try:
            status = agent.structural_search(
                request["pattern"], request["language"])
        except (ValueError, KeyError) as exc:
            return True, False, str(exc)
        return True, False, format_search_status(status)
    if command == "/srewrite":
        from .tools.structural_rewrite import (
            format_rewrite_status,
            parse_rewrite_args,
        )
        try:
            request = parse_rewrite_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        try:
            status = agent.structural_rewrite(
                request["pattern"], request["replacement"],
                request["language"],
                apply=request["action"] == "apply")
        except (ValueError, KeyError) as exc:
            return True, False, str(exc)
        return True, False, format_rewrite_status(status)
    if command == "/truth":
        from .tools.edit_truth import format_truth_report, parse_truth_args
        try:
            request = parse_truth_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        try:
            status = agent.edit_truth(request["path"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_truth_report(status)
    if command == "/format":
        from .tools.format_covenant import format_format_report, parse_format_args
        try:
            request = parse_format_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        try:
            status = agent.format_covenant(
                request["path"], apply=request["action"] == "apply")
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_format_report(status)
    if command == "/debug":
        from .tools.debugger import (
            format_debug_board, format_debug_report, parse_debug_args)
        try:
            request = parse_debug_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            return True, False, format_debug_board(agent.debugger_status())
        try:
            status = agent.debug_run(
                request["program"], breakpoints=request["breakpoints"],
                steps=request["steps"],
                stop_on_exception=request["stop_on_exception"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_debug_report(status)
    if command == "/debugloop":
        from .tools.debug_loop import (
            format_debug_loop_board, format_debug_loop_report,
            parse_debug_loop_args)
        try:
            request = parse_debug_loop_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            return True, False, format_debug_loop_board(agent.debugger_status())
        try:
            status = agent.debug_loop(
                request["test"], breakpoints=request["breakpoints"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_debug_loop_report(status)
    if command == "/testintel":
        from .tools.test_intelligence import (
            format_test_intel_board, format_test_intel_history,
            format_test_intel_selection, parse_test_intel_args)
        try:
            request = parse_test_intel_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            return True, False, format_test_intel_board(agent.test_intel_status())
        if request["action"] == "history":
            return True, False, format_test_intel_history(agent.test_intel_history())
        try:
            status = agent.test_intel_select(request["changed"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_test_intel_selection(status)
    if command == "/coverage":
        from .tools.coverage_sight import (
            format_coverage_board, format_coverage_overlay,
            parse_coverage_args)
        try:
            request = parse_coverage_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            return True, False, format_coverage_board(agent.coverage_status())
        try:
            status = agent.coverage_check(request["changed"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_coverage_overlay(status)
    if command == "/search":
        from .tools.local_search import (
            format_local_search, parse_local_search_args)
        try:
            request = parse_local_search_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        try:
            status = agent.local_search(
                request["query"], mode=request["mode"],
                language=request["language"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_local_search(status)
    if command == "/web":
        from .tools.web_search import format_web_report, parse_web_args
        try:
            request = parse_web_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        try:
            if request["action"] == "search":
                status = agent.web_search(request["query"])
            else:
                status = agent.web_fetch(request["url"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_web_report(status)
    if command == "/docs":
        from .tools.docs_at_hand import (
            format_docs_report, parse_docs_args)
        try:
            request = parse_docs_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        try:
            if request["action"] == "list":
                status = agent.docs_list()
            elif request["action"] == "search":
                status = agent.docs_search(request["query"])
            else:
                status = agent.docs_read(request["name"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_docs_report(status)
    if command == "/deps":
        from .tools.dependency_sight import (
            format_deps_report, parse_deps_args)
        try:
            request = parse_deps_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        try:
            if request["action"] == "show":
                status = agent.dependency_sight()
            elif request["action"] == "package":
                status = agent.dependency_sight(request["package"])
            else:
                status = agent.dependency_proposal(
                    request["package"], request["version"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_deps_report(status)
    if command == "/sensing":
        from .tools.code_sensing import (
            format_sensing_report, parse_sensing_args)
        try:
            request = parse_sensing_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        try:
            status = agent.code_sensing(request["action"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_sensing_report(status)
    if command == "/types":
        from .tools.type_depth import (
            format_type_report, parse_types_args)
        try:
            request = parse_types_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        try:
            status = agent.type_depth(request["path"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_type_report(status)
    if command == "/mojo":
        from .tools.mojo_sight import (
            format_mojo_report, parse_mojo_args)
        try:
            request = parse_mojo_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        try:
            status = agent.mojo_sight(
                request["action"], target=request.get("target"),
                term=request.get("term", ""))
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_mojo_report(status)
    if command == "/sql":
        from .tools.sql_sight import (
            format_sql_report, parse_sql_args)
        try:
            request = parse_sql_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        try:
            status = agent.sql_sight(
                request["action"], db=request.get("db"),
                query=request.get("query", ""))
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_sql_report(status)
    if command == "/config":
        from .tools.config_sight import (
            format_config_report, parse_config_args)
        try:
            request = parse_config_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        try:
            status = agent.config_sight(
                request["action"], target=request.get("target"))
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_config_report(status)
    if command == "/assets":
        from .tools.asset_sight import (
            format_asset_report, parse_assets_args)
        try:
            request = parse_assets_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        try:
            status = agent.asset_sight(
                request["action"], target=request.get("target"))
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_asset_report(status)
    if command == "/langpacks":
        from .tools.language_packs import (
            format_language_pack_report, parse_langpacks_args)
        try:
            request = parse_langpacks_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        try:
            status = agent.language_packs(
                request["action"], language=request.get("language"))
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_language_pack_report(status)
    if command == "/intelcache":
        from .tools.intelligence_cache import (
            format_intelligence_cache_report, parse_intelcache_args)
        try:
            request = parse_intelcache_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        try:
            status = agent.intelligence_cache(
                request["action"], target=request.get("target"))
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_intelligence_cache_report(status)
    if command == "/lsp":
        from .integrations.lsp import (
            format_lsp_code_actions,
            format_lsp_diagnostics,
            format_lsp_navigation,
            format_lsp_rename,
            format_lsp_status,
            parse_lsp_args,
        )
        try:
            request = parse_lsp_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            return True, False, format_lsp_status(agent.lsp_status())
        if request["action"] == "check":
            try:
                status = agent.lsp_diagnostics(request["path"])
            except (ValueError, KeyError, RuntimeError) as exc:
                return True, False, str(exc)
            return True, False, format_lsp_diagnostics(status)
        if request["action"] == "rename":
            try:
                status = agent.lsp_rename(
                    request["path"], request["line"],
                    request["character"], request["new_name"],
                    apply=request["apply"])
            except (ValueError, KeyError, RuntimeError) as exc:
                return True, False, str(exc)
            return True, False, format_lsp_rename(status)
        if request["action"] == "code_actions":
            try:
                status = agent.lsp_code_actions(
                    request["path"], request["line"],
                    request["character"],
                    apply_index=request["apply_index"])
            except (ValueError, KeyError, RuntimeError) as exc:
                return True, False, str(exc)
            return True, False, format_lsp_code_actions(status)
        try:
            if request["action"] == "definition":
                status = agent.lsp_definition(
                    request["path"], request["line"],
                    request["character"])
            elif request["action"] == "references":
                status = agent.lsp_references(
                    request["path"], request["line"],
                    request["character"])
            elif request["action"] == "hover":
                status = agent.lsp_hover(
                    request["path"], request["line"],
                    request["character"])
            else:
                status = agent.lsp_workspace_symbols(request["query"])
        except (ValueError, KeyError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_lsp_navigation(status)
    if command == "/map":
        from .context.repo_map import build_repo_map
        from .context.repo_map_view import (
            build_map_view,
            format_map_change,
            format_map_detail,
            format_map_pins,
            format_map_view,
            parse_map_args,
            pins_from_config,
            resolve_detail,
        )
        try:
            request = parse_map_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "list":
            status = agent.repo_map_status(request["query"])
            view = build_map_view(
                build_repo_map(agent.project_root,
                               query=request["query"]),
                pins_from_config(agent.config))
            assert status["view"] == view.record()
            return True, False, format_map_view(status)
        if request["action"] == "detail":
            try:
                status = agent.repo_map_detail(request["path"])
            except ValueError as exc:
                return True, False, str(exc)
            detail = resolve_detail(
                build_repo_map(agent.project_root),
                pins_from_config(agent.config), request["path"])
            assert status["detail"] == detail.record()
            return True, False, format_map_detail(status)
        if request["action"] == "pins":
            status = agent.repo_map_pins()
            assert status["pins"] == list(pins_from_config(agent.config))
            return True, False, format_map_pins(status)
        try:
            if request["action"] == "pin":
                record = agent.pin_repo_map_file(request["path"])
            else:
                record = agent.unpin_repo_map_file(request["path"])
        except (ValueError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_map_change(record)
    if command == "/resume-thought":
        from .core.streaming_discipline import (
            can_resume,
            find_partial,
            format_resume_status,
            parse_resume_args,
        )
        try:
            request = parse_resume_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            partial = agent.salvaged_partial()
            found = find_partial(agent.history_snapshot())
            assert (found is None) == (partial is None)
            decision = can_resume(agent.config.get("model"))
            return True, False, format_resume_status(partial, decision)
        try:
            text = agent.resume_thought()
        except RuntimeError as exc:
            return True, False, str(exc)
        return True, False, text
    if command == "/model":
        from .core.model_switch import format_switch_record, parse_switch_args
        try:
            request = parse_switch_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if not any(request.values()):
            provider = agent.active_provider()
            label = f" via {provider}" if provider else ""
            return True, False, f"Model: {agent.config['model']}{label} ({agent.config['base_url']})"
        try:
            record = agent.switch_model(
                request["model"], provider=request["provider"],
                base_url=request["base_url"], reason=request["reason"])
        except (ValueError, RuntimeError) as exc:
            return True, False, str(exc)
        return True, False, format_switch_record(record)
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
        from .core.undo_timeline import (
            TimelineEntry,
            enabled_from_config,
            format_setting_change,
            format_undo_outcome,
            format_undo_timeline,
            parse_undo_args,
        )
        if not agent.tool_policy.authorize("undo_edit", {}):
            return True, False, "Permission denied for undo_edit; no operation was performed."
        try:
            request = parse_undo_args(arguments)
        except ValueError as exc:
            return True, False, str(exc)
        if request["action"] == "show":
            status = agent.undo_timeline_status()
            entries = [TimelineEntry(**entry)
                       for entry in status["entries"]]
            return True, False, format_undo_timeline(
                agent.config, entries,
                checkpoint_wired=status["checkpoint_wired"])
        if request["action"] == "setting":
            try:
                record = agent.set_undo_timeline(request["enabled"])
            except (ValueError, KeyError, RuntimeError) as exc:
                return True, False, str(exc)
            return True, False, format_setting_change(record)
        if not enabled_from_config(agent.config):
            if request["action"] == "next" and request["count"] == 1:
                return True, False, EditJournal(agent.project_root).undo()
            return True, False, (
                "Undo timeline is off — /undo keeps its original "
                "last-edit behaviour; turn it on with /undo on.")
        try:
            if request["action"] == "kind":
                return True, False, format_undo_outcome(
                    agent.undo_kind(request["kind"]))
            if request["action"] == "checkpoint":
                return True, False, format_undo_outcome(
                    agent.restore_checkpoint_via_seam(
                        request["checkpoint_id"]))
            messages = []
            for _ in range(request["count"]):
                record = agent.undo_newest()
                messages.append(format_undo_outcome(record))
                if not record.get("changed"):
                    break
            return True, False, "\n".join(messages)
        except ValueError as exc:
            return True, False, str(exc)
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
    # M-095: the posture is always visible - the status
    # line carries it from the first moment of the chat.
    # A failure to render it claims nothing and never
    # blocks the chat (the M-040 pattern).
    try:
        from .core.permission_profiles import (
            format_permission_profile,
        )
        console.print(
            format_permission_profile(agent.config),
            markup=False)
    except Exception:
        pass
    console.print("Use /help for commands, /quit or Ctrl+D to leave, Ctrl+C to interrupt.")
    # M-040: at session start, say it once and exactly when the
    # app is offline — a probed board with no door that can
    # serve — instead of letting each request die on its own
    # error. Any failure to assess claims nothing and never
    # blocks the chat.
    try:
        _offline = agent.offline_status()
        if _offline["assessment"]["state"] == "offline":
            from .core.offline_honesty import format_offline_status
            console.print(format_offline_status(_offline), markup=False)
    except Exception:
        pass
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
