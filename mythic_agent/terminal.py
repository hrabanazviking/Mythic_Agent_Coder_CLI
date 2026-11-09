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
        return True, False, "/help /clear /compact /model <name> [url] /route [office] /fallback [on|off|add|clear] /costroute [on|off|<task-class>] /editformat [auto|<format>|<task-kind>] /hashanchor [on|off] /repairloop [on|off] /hunkreview [on|off] /changeset [on|off] /rename [on|off|<old-path> <new-path>] /generated [on|off|<path>|mark <path> <generator>] /largefile [on|off|<path>]/largefile [on|off|<path>] /stash [show|on|off|shelve <name>|restore <name>|drop <name>] /patch [show|on|off|export <set name>|import <patch file>] /editor [show|on|off|file <path>|prompt] /diff [show|on|off|unified|side-by-side|whitespace|whitespace off] /blame [show|on|off|<path> [<line>]] /massedit [show|on|off] /posture [show|<profile name>] /remember [list|forget <id>|clear] /sandbox [show|on|off|truth|plan <command>] /network [show|on|off|list|check <tool> <host>|allow <tool> <domain>] /pathjail [show|on|off|grants|check <path>|grant <abs-path>] /plan [show|on|off|approve|build|check <effect>] /hooks [show|show <event>|check <event>] /hookpacks [show|show <pack>|install <pack>] /background [show|show <job>|tail [<job>]|kill <job>|start <command...>] /keeper [show|show <target>|check|heartbeat <target>] /schedule [show|show <job>|check] /fleet [show|show <task>|verdict|resume] /budgets [show|show <budget>|check|check <budget>] /halt [show|show <halt>|pull|pull <target>] /audit [show|show <entry>|export] /secrets [show|show <screening>|check <file>] /doctrine [show|show <judgement>|ladder|check <command>] /rollback [show|show <run>|drills|run <drill>] /multirepo [show|show <set>|repos] /remote [show|show <plan>|targets] /grace [show|show <record>|failures] /moment [show|show <record>|parts] /policy [show|plan|sections|apply] /crew [show|show <member>|office <office>] /offices [show|show <office>|handoffs <office>|contract <from> <to>] /offices custom [show|show <office>|handoffs <office>|contract <from> <to>] /worktrees [show|show <member>|plan|merges] /dealing [show|show <member>|plan|loads] /comms [show|show <member>|ask|kinds] /deadlock [show|show <member>|kinds] /merge [show|show <member>|lines|kinds] /hetero [show|show <member>|routes|kinds] /veto [show|show <slice>|gates|kinds] /swarm [show|show <member>|digest|sources|kinds] /panel [show|show <reviewer>|outcome|verdicts|kinds] /memory [show|show <member>|search <words>|tag <tag>|entry <entry-id>|members] /standup [show|digest|done|doing|blocked|needs-you|entry <entry-id>|kinds] /crewsize [show|recommend <case-id>|case <case-id>|solo|pair|crew|full-crew|kinds] /voices [show|profile <member-id>|report <report-id>|plain|warm|wry|grim|registers] /externals [show|seat <member-id>|check <member-id>|mcp|transports] /replay [show|step <step-id>|trace <step-id>] /foster [show|report <report-id>|redeal <slice-id>|escalation <report-id>] /costcourt [show|entry <entry-id>|member <member-id>|slice <slice-id>|ledger] /dogfood [show|entry <entry-id>|member <member-id>|slice <slice-id>|part <part-number>|ledger] /solo [show|capability <capability-id>|member <member-id>|report <member-id>|ledger] /templates [show|template <template>|member <member-id>|roster <template>|index] /interrupts [show|interrupt <interrupt-id>|member <member-id>|slice <slice-id>|report <interrupt-id>|index] /crewschedules [show|attachment <attachment-id>|template <template>|job <job-id>|report <attachment-id>|index] /contextbudget [show|item <item-id>|kind <kind>|meter|panel] /mentions [show|mention <mention-id>|kind <kind>|plan <mention-id>|parse <text>|index] /instructionfiles [show|entry <file-id>|origin <origin>|layer <layer>|panel] /memorymap [show|entry <entry-id>|section <section>|panel] /glassbox [show|record <record-id>|versions <record-id>|panel] /graphsearch [show|node <node-id>|seeds|panel] /daymemory [show|situation <situation-id>|memory|slices|decisions|panel] /crossmemory [show|lesson <lesson-id>|offers|accepted <project>|panel] /ledger [show|candidate <candidate-id>|decisions|standing|panel] /decisions [show|record <record-id>|adr <record-id>|accepted|panel] /forget [show|entry <entry-id>|forgotten|quarantined|panel] /recipes [show|recipe <recipe-id>|summon <recipe name>|panel] /pins [show|pin <pin-id>|kind <kind>|panel] /thrift [show|record <record-id>|road <road>|panel|costs] /endurance [show|record <record-id>|kind <kind>|panel|verdict] /multisession [show|session <session-id>|branch <branch>|panel|isolation] /handoffsummary [show|handoff <handoff-id>|session <session-ref>|panel|verdict] /memoryxport [show|package <package-id>|project <project>|panel|verdict] /subconscious [show|memory <memory-id>|layer <core|subconscious>|source <source-kind>|panel|verdict] /contradiction [show|watch <watch-id>|kind <memory-kind>|panel|verdict] /private [show|posting <posting-id>|kind <memory-kind>|home <home>|panel|verdict] /memorydoctor [show|finding <finding-id>|check <check>|store <store>|panel|verdict|repairs] /coldstart [show|record <record-id>|project <project-ref>|panel|verdict|stages] /workview [show|event <event-id>|detail [<event-id>]|kind <kind>|panel|verdict] /sliceboard [show|card <slice-id>|column <column>|action <action-id>|panel|verdict] /approvalcards [show|card <card-id>|decision <decision-id>|panel|verdict] /issueslice [on|off|github <number>] /prcraft [on|off|tasks <pr>] /commitcraft [on|off|plan|commit <concern>|push] /guardians [word on|word off|check <path>] /autocommit [on|off|allow-protected|block-protected] /checkpoint [take <name>|restore <name> [discard]|on|off] /branch [on|off|fork <index> [name]|list|compare <id> <id>] /kista [adopt] /resume-thought [show] /retry [show] /vision [show|switch] /longcontext [show|<model>] /offline [show] /testkit <provider> [url] /map [task|show <path>|pin <path>|unpin <path>|pins] /ssearch <language> <pattern> /srewrite [apply] <language> <pattern> => <replacement> /lsp [show|check <path>|def <path> <line> <col>|refs <path> <line> <col>|hover <path> <line> <col>|symbols [query]] /truth <path> /format <path> [apply] /status /session /add <path> /stop /undo [list|edit|command|checkpoint <id>|<count>|on|off] /quit"
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
    if command == "/dealing":
        # M-125 terminal road: show the dealt
        # assignments held this session (the shipped
        # example dealing when none is held), show
        # one member's assignments, show the whole
        # plan, or show the crew's loads, on the pure
        # layer's parser + formatters. This road
        # starts no crew and spawns nothing; the
        # registry holds the dealing as data, and
        # there is no Part VIII board yet - this
        # screen is where the dealing is visible.
        from .core.task_dealing import format_assignments as _fmt_dealt, format_loads as _fmt_loads, format_tasks as _fmt_tasks, parse_dealing_args as _parse_dealing
        try:
            _act, _tgt = _parse_dealing(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "plan":
            _plan = agent.dealing_plan()
            return True, False, _fmt_tasks(_plan) + f"\nDealer: {_plan.dealer} - the dealer deals by office fit and current load, and the human may re-deal any slice."
        if _act == "loads":
            return True, False, _fmt_loads(agent.dealing_loads())
        if _tgt is None:
            return True, False, agent.task_dealing_status()["screen"]
        try:
            _held = agent.find_dealt_assignments(_tgt)
        except (KeyError, ValueError) as _exc:
            return True, False, str(_exc)
        return True, False, _fmt_dealt(_held)
    if command == "/comms":
        # M-126 terminal road: show the hand-offs
        # held this session (the shipped example
        # ledger when none is held), show one
        # member's hand-offs, show the one batched
        # ask of the questions waiting for the human,
        # or show the kinds, on the pure layer's
        # parser + formatters. This road spawns no
        # crew and delivers no message; the registry
        # holds the hand-offs as data, and there is
        # no Part VIII board yet - this screen is
        # where the hand-offs and the batch are
        # visible.
        from .core.crew_comms import format_handoffs as _fmt_comms, format_human_batch as _fmt_batch, format_kinds as _fmt_kinds, parse_comms_args as _parse_comms
        try:
            _act, _tgt = _parse_comms(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "ask":
            return True, False, _fmt_batch(agent.human_question_batch())
        if _act == "kinds":
            return True, False, _fmt_kinds()
        if _tgt is None:
            return True, False, agent.crew_comms_status()["screen"]
        try:
            _held = agent.find_handoffs(_tgt)
        except (KeyError, ValueError) as _exc:
            return True, False, str(_exc)
        return True, False, _fmt_comms(_held)
    if command == "/deadlock":
        # M-127 terminal road: show the findings of
        # the watch held this session (the shipped
        # example watch when none is held), show one
        # member's findings, or show the kinds, on
        # the pure layer's parser + formatters. This
        # road spawns no crew, stops no member and
        # runs no git; the registry holds the evidence
        # as data, and there is no Part VIII board
        # yet - this screen is where the findings are
        # visible.
        from .core.deadlock_watch import format_findings as _fmt_findings, format_kinds as _fmt_dw_kinds, parse_deadlock_args as _parse_deadlock
        try:
            _act, _tgt = _parse_deadlock(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "kinds":
            return True, False, _fmt_dw_kinds()
        if _tgt is None:
            return True, False, agent.deadlock_status()["screen"]
        try:
            _held = agent.find_findings(_tgt)
        except (KeyError, ValueError) as _exc:
            return True, False, str(_exc)
        return True, False, _fmt_findings(_held)
    if command == "/merge":
        # M-128 terminal road: show the verdicts of
        # the plan held this session (the shipped
        # example plan when none is held), show one
        # member's verdicts, show every line's state,
        # or show the kinds, on the pure layer's
        # parser + formatters. This road executes no
        # git and performs no merge; the registry
        # holds the evidence as data, and there is no
        # Part VIII board yet - this screen is where
        # the verdicts are visible.
        from .core.merge_discipline import format_lines as _fmt_lines, format_kinds as _fmt_md_kinds, format_verdicts as _fmt_verdicts, parse_merge_args as _parse_merge
        try:
            _act, _tgt = _parse_merge(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "kinds":
            return True, False, _fmt_md_kinds()
        if _act == "lines":
            return True, False, _fmt_lines(agent.merge_report())
        if _tgt is None:
            return True, False, agent.merge_status()["screen"]
        try:
            _held = agent.find_verdicts(_tgt)
        except (KeyError, ValueError) as _exc:
            return True, False, str(_exc)
        return True, False, _fmt_verdicts(_held)
    if command == "/hetero":
        # M-129 terminal road: show the verdicts of
        # the crew plan held this session (the
        # shipped example plan when none is held),
        # show one member's verdicts, show every
        # route's state, or show the kinds, on the
        # pure layer's parser + formatters. This
        # road spawns no crew and calls no provider;
        # the registry holds the evidence as data,
        # and there is no Part VIII board yet - this
        # screen is where the verdicts are visible.
        from .core.heterogeneous_crews import format_routes as _fmt_routes, format_kinds as _fmt_hetero_kinds, format_verdicts as _fmt_hetero_verdicts, parse_hetero_args as _parse_hetero
        try:
            _act, _tgt = _parse_hetero(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "kinds":
            return True, False, _fmt_hetero_kinds()
        if _act == "routes":
            return True, False, _fmt_routes(agent.hetero_report())
        if _tgt is None:
            return True, False, agent.hetero_status()["screen"]
        try:
            _held = agent.find_hetero_verdicts(_tgt)
        except (KeyError, ValueError) as _exc:
            return True, False, str(_exc)
        return True, False, _fmt_hetero_verdicts(_held)
    if command == "/veto":
        # M-130 terminal road: show the verdicts of
        # the veto ledger held this session (the
        # shipped example ledger when none is held),
        # show one slice's verdicts, show every
        # case's gate, or show the kinds, on the pure
        # layer's parser + formatters. This road runs
        # no check and banks nothing; the registry
        # holds the evidence as data, and there is no
        # Part VIII board yet - this screen is where
        # the verdicts are visible.
        from .core.auditor_veto import format_gates as _fmt_gates, format_kinds as _fmt_veto_kinds, format_verdicts as _fmt_veto_verdicts, parse_veto_args as _parse_veto
        try:
            _act, _tgt = _parse_veto(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "kinds":
            return True, False, _fmt_veto_kinds()
        if _act == "gates":
            return True, False, _fmt_gates(agent.veto_report())
        if _tgt is None:
            return True, False, agent.veto_status()["screen"]
        try:
            _held = agent.find_veto_verdicts(_tgt)
        except (KeyError, ValueError) as _exc:
            return True, False, str(_exc)
        return True, False, _fmt_veto_verdicts(_held)
    if command == "/swarm":
        # M-131 terminal road: show the swarm held
        # this session (the shipped example swarm
        # when none is held), show one member's
        # finding, show the digested answer, show
        # its sources, or show the focus kinds, on
        # the pure layer's parser + formatters. This
        # road runs no research, calls no model and
        # spawns no crew; the registry holds the
        # swarm as data, and there is no Part VIII
        # board yet - this screen is where the
        # digest is visible.
        from .core.research_swarms import digest_plain_words as _digest_words, format_finding as _fmt_finding, format_focus_kinds as _fmt_swarm_kinds, parse_swarm_args as _parse_swarm
        try:
            _act, _tgt = _parse_swarm(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "kinds":
            return True, False, _fmt_swarm_kinds()
        if _act == "digest":
            try:
                _dig = agent.swarm_digest()
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            _lines = [_digest_words(_dig), "Sources:"]
            _lines.extend(f"- {_src}" for _src in _dig.sources)
            return True, False, "\n".join(_lines)
        if _act == "sources":
            try:
                _dig = agent.swarm_digest()
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            if not _dig.sources:
                return True, False, "No sources are cited yet."
            return True, False, "\n".join(
                f"- {_src}" for _src in _dig.sources)
        if _tgt is None:
            return True, False, agent.swarm_status()["screen"]
        try:
            _held = agent.find_swarm_findings(_tgt)
        except (KeyError, ValueError) as _exc:
            return True, False, str(_exc)
        return True, False, "\n".join(
            _fmt_finding(_f) for _f in _held)
    if command == "/panel":
        # M-132 terminal road: show the panel held
        # this session (the shipped example panel
        # when none is held), show one reviewer's
        # review, show the derived outcome, show
        # the positions it holds, or show the
        # verdict kinds, on the pure layer's parser
        # + formatters. This road runs no review,
        # calls no model, executes no change and
        # spawns no crew; the registry holds the
        # panel as data, and there is no Part VIII
        # board yet - this screen is where the
        # outcome is visible.
        from .core.review_panels import format_review as _fmt_review, format_verdict_kinds as _fmt_panel_kinds, outcome_plain_words as _outcome_words, parse_panel_args as _parse_panel
        try:
            _act, _tgt = _parse_panel(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "kinds":
            return True, False, _fmt_panel_kinds()
        if _act == "outcome":
            try:
                _out = agent.panel_outcome()
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            _lines = [_outcome_words(_out)]
            if _out.reviewers:
                _lines.append("Positions:")
                _lines.extend(
                    f"- {_r} holds {_v}" for _r, _v in zip(
                        _out.reviewers, _out.verdicts))
            return True, False, "\n".join(_lines)
        if _act == "verdicts":
            try:
                _out = agent.panel_outcome()
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            if not _out.verdicts:
                return True, False, "No verdicts are held yet."
            return True, False, "\n".join(
                f"- {_r}: {_v}" for _r, _v in zip(
                    _out.reviewers, _out.verdicts))
        if _tgt is None:
            return True, False, agent.panel_status()["screen"]
        try:
            _held = agent.find_panel_reviews(_tgt)
        except (KeyError, ValueError) as _exc:
            return True, False, str(_exc)
        return True, False, "\n".join(
            _fmt_review(_r) for _r in _held)
    if command == "/memory":
        # M-133 terminal road: show the memory held
        # this session (the shipped example memory
        # when none is held), show one member's
        # notebook, search every notebook, find by
        # tag, show one entry, or list the notebook
        # holders, on the pure layer's parser +
        # formatters. This road persists nothing,
        # syncs nothing, calls no model and spawns
        # no crew; the registry holds the memory as
        # data, and there is no Part VIII board yet -
        # this screen is where the memory is visible.
        from .core.crew_memory import format_entry as _fmt_entry, format_notebook as _fmt_notebook, parse_memory_args as _parse_memory
        try:
            _act, _tgt = _parse_memory(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "members":
            _mem = agent.crew_memory()
            if not _mem.members():
                return True, False, "No notebooks are held yet."
            return True, False, "\n".join(
                f"- {_m}" for _m in _mem.members())
        if _act == "search":
            _found = agent.search_crew_memory(_tgt)
            if not _found:
                return True, False, "No facts match that search."
            return True, False, "\n".join(
                _fmt_entry(_e) for _e in _found)
        if _act == "tag":
            _found = agent.find_memory_entries_by_tag(_tgt)
            if not _found:
                return True, False, "No facts match that search."
            return True, False, "\n".join(
                _fmt_entry(_e) for _e in _found)
        if _act == "entry":
            try:
                _entry = agent.get_memory_entry(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_entry(_entry)
        if _tgt is None:
            return True, False, agent.crew_memory_status()["screen"]
        try:
            _notebook = agent.crew_memory().notebook_for(_tgt)
        except (KeyError, ValueError) as _exc:
            return True, False, str(_exc)
        return True, False, _fmt_notebook(_notebook)
    if command == "/standup":
        # M-134 terminal road: show the stand-up held
        # this session (the shipped example stand-up
        # when none is held), show its derived digest,
        # show one state's section, show one entry, or
        # list the four states, on the pure layer's
        # parser + formatters. This road schedules
        # nothing, sends nothing, posts nothing, calls
        # no model and persists nothing; the registry
        # holds the stand-up as data, and there is no
        # Part VIII board yet - this screen is where
        # the digest is visible.
        from .core.stand_ups import format_digest as _fmt_digest, format_entries as _fmt_entries, format_entry as _fmt_entry, format_status_kinds as _fmt_kinds, parse_stand_up_args as _parse_standup
        try:
            _act, _tgt = _parse_standup(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "kinds":
            return True, False, _fmt_kinds()
        if _act == "digest":
            try:
                return True, False, _fmt_digest(agent.stand_up())
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
        if _act == "section":
            try:
                return True, False, _fmt_entries(agent.stand_up(), _tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
        if _act == "entry":
            try:
                _entry = agent.get_stand_up_entry(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_entry(_entry)
        return True, False, agent.stand_up_status()["screen"]
    if command == "/crewsize":
        # M-135 terminal road: show the sizing book
        # held this session (the shipped example book
        # when none is held), show one case's derived
        # recommendation, show one case, show one size
        # band, or list the four size bands, on the
        # pure layer's parser + formatters. This road
        # spawns nothing, sizes no live crew, calls no
        # model and persists nothing; the registry
        # holds the sizing as data, and there is no
        # Part VIII board yet - this screen is where
        # the sizing is visible.
        from .core.crew_sizing import format_shape as _fmt_case, format_shapes as _fmt_band, format_size_kinds as _fmt_kinds, parse_crew_size_args as _parse_crewsize, recommendation_plain_words as _rec_words
        try:
            _act, _tgt = _parse_crewsize(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "kinds":
            return True, False, _fmt_kinds()
        if _act == "recommend":
            try:
                _case = agent.get_sizing_case(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _rec_words(_case)
        if _act == "case":
            try:
                _case = agent.get_sizing_case(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_case(_case)
        if _act == "band":
            return True, False, _fmt_band(agent.crew_sizing(), _tgt)
        return True, False, agent.crew_sizing_status()["screen"]
    if command == "/voices":
        # M-136 terminal road: show the voice book
        # held this session (the shipped example book
        # when none is held), show one member's voice,
        # show one report, show one register's voices,
        # or list the four registers, on the pure
        # layer's parser + formatters. This road
        # generates nothing, calls no model and
        # persists nothing; the registry holds the
        # voices as data, and there is no Part VIII
        # board yet - this screen is where the voices
        # are visible.
        from .core.character_voices import format_profile as _fmt_profile, format_profiles as _fmt_profiles, format_registers as _fmt_registers, format_report as _fmt_vreport, parse_voice_args as _parse_voices
        try:
            _act, _tgt = _parse_voices(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "registers":
            return True, False, _fmt_registers()
        if _act == "profile":
            try:
                _profile = agent.get_voice_profile(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_profile(_profile)
        if _act == "report":
            try:
                _report = agent.voice_report(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_vreport(_report)
        if _act == "register":
            return True, False, _fmt_profiles(agent.character_voices(), _tgt)
        return True, False, agent.character_voices_status()["screen"]
    if command == "/externals":
        # M-137 terminal road: show the seat book
        # held this session (the shipped example book
        # when none is held), show one member's seat,
        # derive one seat's check, show one
        # transport's seats, or list the transports,
        # on the pure layer's parser + formatters.
        # This road opens no MCP session, calls no
        # model and persists nothing; the registry
        # holds the seats as data, and there is no
        # Part VIII board yet - this screen is where
        # the seats are visible.
        from .core.external_agents import format_check as _fmt_echeck, format_seat as _fmt_eseat, format_seats as _fmt_eseats, format_transports as _fmt_etransports, parse_external_args as _parse_externals
        try:
            _act, _tgt = _parse_externals(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "transports":
            return True, False, _fmt_etransports()
        if _act == "seat":
            try:
                _seat = agent.get_external_seat(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_eseat(_seat)
        if _act == "check":
            try:
                _check = agent.external_seat_check(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_echeck(_check)
        if _act == "transport":
            return True, False, _fmt_eseats(agent.external_agents(), _tgt)
        return True, False, agent.external_agents_status()["screen"]
    if command == "/replay":
        # M-138 terminal road: show the replay book
        # held this session (the shipped example book
        # when none is held), show one step, or derive
        # one decision's trace, on the pure layer's
        # parser + formatters. This road reads no live
        # journal, re-executes nothing, calls no model
        # and persists nothing; the registry holds the
        # steps as data, and there is no Part VIII board
        # yet - this screen is where the replay is
        # visible.
        from .core.crew_replay import format_step as _fmt_rstep, format_steps as _fmt_rsteps, format_trace as _fmt_rtrace, parse_replay_args as _parse_replay
        try:
            _act, _tgt = _parse_replay(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "step":
            try:
                _step = agent.get_replay_step(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_rstep(_step)
        if _act == "trace":
            try:
                _trace = agent.replay_trace(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_rtrace(_trace)
        return True, False, agent.crew_replay_status()["screen"]
    if command == "/foster":
        # M-139 terminal road: show the fostering book
        # held this session (the shipped example book
        # when none is held), show one failure report,
        # show the re-deal a slice holds, or derive one
        # failure's escalation, on the pure layer's
        # parser + formatters. This road re-deals no
        # task to a live agent, delivers no escalation,
        # calls no model and persists nothing; the
        # registry holds the dealings and reports as
        # data, and there is no Part VIII board yet -
        # this screen is where the fostering is
        # visible.
        from .core.failure_fostering import format_escalation as _fmt_fesc, format_redeal as _fmt_fredeal, format_report as _fmt_freport, parse_fostering_args as _parse_foster
        try:
            _act, _tgt = _parse_foster(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "report":
            try:
                _report = agent.get_failure_report(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_freport(_report)
        if _act == "redeal":
            try:
                _book = agent.failure_fostering()
                _redeal = None
                if _book is not None:
                    for _held_redeal in _book.redeals:
                        if _held_redeal.slice_id == _tgt:
                            _redeal = _held_redeal
                            break
                if _redeal is None:
                    raise KeyError(
                        f"no re-deal in the book: {_tgt!r}")
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_fredeal(_redeal)
        if _act == "escalation":
            try:
                _escalation = agent.fostering_escalation(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_fesc(_escalation)
        return True, False, agent.failure_fostering_status()["screen"]
    if command == "/costcourt":
        # M-140 terminal road: show the court book
        # held this session (the shipped example book
        # when none is held), show one run record, one
        # member's records or one slice's records, or
        # show the Scribe's ledger derived from the
        # whole book, on the pure layer's parser +
        # formatters. This road calls no model, bills
        # no one, charges nothing and persists
        # nothing; the registry holds the records as
        # data, and there is no Part VIII board yet -
        # this screen is where the court is visible.
        from .core.cost_court import format_entries as _fmt_centries, format_entry as _fmt_centry, format_ledger as _fmt_cledger, parse_cost_court_args as _parse_court
        try:
            _act, _tgt = _parse_court(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "entry":
            try:
                _entry = agent.get_cost_entry(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_centry(_entry)
        if _act == "member":
            return True, False, _fmt_centries(agent.cost_court(), _tgt)
        if _act == "slice":
            _held = agent.cost_court().entries_on(_tgt)
            if _held:
                return True, False, "\n".join(
                    _fmt_centry(_e) for _e in _held)
            return True, False, "No run records are held."
        if _act == "ledger":
            try:
                _ledger = agent.scribe_ledger()
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_cledger(_ledger)
        return True, False, agent.cost_court_status()["screen"]
    if command == "/dogfood":
        # M-141 terminal road: show the dogfood book
        # held this session (the shipped example book
        # when none is held), show one build record, one
        # member's records or one slice's records, show
        # one part's report, or show the coordinator's
        # ledger derived from the whole book, on the
        # pure layer's parser + formatters. This road
        # builds nothing live, runs no crew, calls no
        # model, spawns no agent, merges or banks
        # nothing and persists nothing; the registry
        # holds the records as data, and there is no
        # Part VIII board yet - this screen is where
        # the dogfood is visible.
        from .core.dogfood import format_entries as _fmt_dentries, format_entry as _fmt_dentry, format_ledger as _fmt_dledger, format_report as _fmt_dreport, parse_dogfood_args as _parse_dogfood
        try:
            _act, _tgt = _parse_dogfood(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "entry":
            try:
                _entry = agent.get_dogfood_entry(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_dentry(_entry)
        if _act == "member":
            return True, False, _fmt_dentries(agent.dogfood(), _tgt)
        if _act == "slice":
            _held = agent.dogfood().entries_on(_tgt)
            if _held:
                return True, False, "\n".join(
                    _fmt_dentry(_e) for _e in _held)
            return True, False, "No build records are held."
        if _act == "part":
            try:
                _report = agent.dogfood_report(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_dreport(_report)
        if _act == "ledger":
            try:
                _ledger = agent.coordinator_ledger()
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_dledger(_ledger)
        return True, False, agent.dogfood_status()["screen"]
    if command == "/solo":
        # M-142 terminal road: show the solo mode book
        # held this session (the shipped example book
        # when none is held), show one capability
        # record, one member's amplified records or one
        # member's report, or show the parity ledger
        # derived from the whole book, on the pure
        # layer's parser + formatters. This road
        # disables no crew, spawns no agent, runs no
        # agent, calls no model and persists nothing;
        # the registry holds the records as data, and
        # there is no Part VIII board yet - this screen
        # is where the solo mode is visible.
        from .core.solo_mode import format_capabilities as _fmt_scaps, format_capability as _fmt_scap, format_ledger as _fmt_sledger, format_report as _fmt_sreport, parse_solo_mode_args as _parse_solo
        try:
            _act, _tgt = _parse_solo(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "capability":
            try:
                _cap = agent.get_solo_capability(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_scap(_cap)
        if _act == "member":
            return True, False, _fmt_scaps(agent.solo_mode(), _tgt)
        if _act == "report":
            try:
                _report = agent.solo_mode_report(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_sreport(_report)
        if _act == "ledger":
            try:
                _ledger = agent.parity_ledger()
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_sledger(_ledger)
        return True, False, agent.solo_mode_status()["screen"]
    if command == "/templates":
        # M-143 terminal road: show the crew template
        # book held this session (the shipped example
        # book when none is held), show one formation
        # record summoned by name, one member's
        # formations or one formation's derived roster,
        # or show the template index derived from the
        # whole book, on the pure layer's parser +
        # formatters. This road summons no crew, spawns
        # no agent, runs no agent, calls no model and
        # persists nothing; the registry holds the
        # records as data, and there is no Part VIII
        # board yet - this screen is where the crew
        # templates are visible.
        from .core.crew_templates import format_index as _fmt_tindex, format_roster as _fmt_troster, format_template as _fmt_ttemplate, format_templates as _fmt_ttemplates, parse_crew_templates_args as _parse_templates
        try:
            _act, _tgt = _parse_templates(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "template":
            try:
                _template = agent.get_crew_template(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_ttemplate(_template)
        if _act == "member":
            return True, False, _fmt_ttemplates(agent.crew_templates(), _tgt)
        if _act == "roster":
            try:
                _roster = agent.crew_template_roster(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_troster(_roster)
        if _act == "index":
            try:
                _index = agent.crew_template_index()
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_tindex(_index)
        return True, False, agent.crew_templates_status()["screen"]
    if command == "/interrupts":
        # M-144 terminal road: show the crew interrupt
        # book held this session (the shipped example
        # book when none is held), show one pause
        # record, one member's pauses, one slice's
        # pauses or one pause's derived consistency
        # report, or show the interrupt index derived
        # from the whole book, on the pure layer's
        # parser + formatters. This road pauses no
        # member, halts no crew, signals no process,
        # touches no worktree, writes no journal and
        # persists nothing; the registry holds the
        # records as data, and there is no Part VIII
        # board yet - this screen is where the crew
        # interrupts are visible.
        from .core.crew_interrupts import format_index as _fmt_iindex, format_interrupt as _fmt_iinterrupt, format_interrupts as _fmt_iinterrupts, format_report as _fmt_ireport, parse_crew_interrupts_args as _parse_interrupts
        try:
            _act, _tgt = _parse_interrupts(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "interrupt":
            try:
                _interrupt = agent.get_crew_interrupt(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_iinterrupt(_interrupt)
        if _act == "member":
            return True, False, _fmt_iinterrupts(agent.crew_interrupts(), _tgt)
        if _act == "slice":
            _held = agent.crew_interrupts_for_slice(_tgt)
            if _held:
                return True, False, "\n".join(_fmt_iinterrupt(_e) for _e in _held)
            return True, False, "No interrupt records are held."
        if _act == "report":
            try:
                _report = agent.crew_interrupt_report(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_ireport(_report)
        if _act == "index":
            try:
                _index = agent.crew_interrupt_index()
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_iindex(_index)
        return True, False, agent.crew_interrupts_status()["screen"]
    if command == "/crewschedules":
        # M-145 terminal road: show the crew schedule
        # book held this session (the shipped example
        # book when none is held), show one attachment
        # record, one formation's attachments, one
        # job's attachment or one attachment's derived
        # report, or show the attachment index derived
        # from the whole book, on the pure layer's
        # parser + formatters. This road starts no
        # timer, runs no job, summons no crew, spawns
        # no agent and persists nothing; the registry
        # holds the records as data, and there is no
        # Part VIII board yet - this screen is where
        # the crew on schedule attachments are visible.
        from .core.crew_schedules import format_attachment as _fmt_sattachment, format_attachments as _fmt_sattachments, format_index as _fmt_sindex, format_report as _fmt_sreport, parse_crew_schedules_args as _parse_schedules
        try:
            _act, _tgt = _parse_schedules(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "attachment":
            try:
                _attachment = agent.get_crew_schedule(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_sattachment(_attachment)
        if _act == "template":
            return True, False, _fmt_sattachments(agent.crew_schedules(), _tgt)
        if _act == "job":
            try:
                _attachment = agent.get_crew_schedule_for_job(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_sattachment(_attachment)
        if _act == "report":
            try:
                _report = agent.crew_schedule_report(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_sreport(_report)
        if _act == "index":
            try:
                _index = agent.crew_schedule_index()
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_sindex(_index)
        return True, False, agent.crew_schedules_status()["screen"]
    if command == "/contextbudget":
        # M-147 terminal road: show the context budget
        # panel held this session (the shipped example
        # panel when none is held), show one context
        # item, one kind's items, the meter derived
        # from the whole panel or the panel derived
        # from the whole book, on the pure layer's
        # parser + formatters. This road compiles no
        # context, assembles no prompt, calls no model
        # and persists nothing; the registry holds the
        # items as data, and there is no Part VIII board
        # yet - this screen is where the context budget
        # account is visible.
        from .core.context_budget import format_item as _fmt_cbitem, format_items as _fmt_cbitems, format_meter as _fmt_cbmeter, format_panel as _fmt_cbpanel, parse_context_budget_args as _parse_cb
        try:
            _act, _tgt = _parse_cb(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "item":
            try:
                _item = agent.get_context_budget_item(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_cbitem(_item)
        if _act == "kind":
            return True, False, _fmt_cbitems(agent.context_budget_panel(), _tgt)
        if _act == "meter":
            try:
                _meter = agent.context_budget_meter()
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_cbmeter(_meter)
        if _act == "panel":
            try:
                _view = agent.context_budget_view()
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_cbpanel(_view)
        return True, False, agent.context_budget_status()["screen"]
    if command == "/mentions":
        # M-148 terminal road: show the mention canon
        # held this session (the shipped example canon
        # when none is held), show one mention, one
        # kind's mentions, the plan derived for one
        # mention, the mentions the grammar reads out
        # of a text (holding none of them), or the
        # index derived from the whole book, on the
        # pure layer's parser + formatters. This road
        # reads no file, fetches no page, compiles no
        # context, calls no model and persists nothing;
        # parsing and planning pull nothing in by
        # themselves, and there is no Part VIII board
        # yet - this screen is where the mention canon
        # is visible.
        from .core.mentions import format_index as _fmt_mindex, format_mention as _fmt_mention, format_mentions as _fmt_mentions, format_plan as _fmt_mplan, parse_mentions as _parse_mtext, parse_mentions_args as _parse_m
        try:
            _act, _tgt = _parse_m(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "mention":
            try:
                _entry = agent.get_mention(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_mention(_entry)
        if _act == "kind":
            return True, False, _fmt_mentions(agent.mentions_canon(), _tgt)
        if _act == "plan":
            try:
                _plan = agent.mention_plan(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_mplan(_plan)
        if _act == "parse":
            try:
                _found = _parse_mtext(_tgt)
            except ValueError as _exc:
                return True, False, str(_exc)
            return True, False, "\n".join(
                _fmt_mention(entry) for entry in _found) or (
                "No mentions stand in that text.")
        if _act == "index":
            return True, False, _fmt_mindex(agent.mentions_canon())
        return True, False, agent.mentions_status()["screen"]
    if command == "/instructionfiles":
        # M-149 terminal road: show the instruction files
        # held this session (the shipped example book when
        # none is held), show one entry, one origin's files,
        # one layer's files, or the panel derived from the
        # whole book, on the pure layer's parser +
        # formatters. This road writes no file, renames no
        # file, applies no instruction itself beyond what
        # the elder road already does, and persists nothing;
        # a foreign file stays a foreign file here, honoured
        # on its own turf - and there is no Part VIII board
        # yet, so this screen is where the instruction files
        # account is visible.
        from .core.instruction_files import format_entries as _fmt_ifentries, format_entry as _fmt_ifentry, format_panel as _fmt_ifpanel, parse_instruction_files_args as _parse_if
        try:
            _act, _tgt = _parse_if(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "entry":
            try:
                _entry = agent.get_instruction_file(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_ifentry(_entry)
        if _act == "origin":
            return True, False, _fmt_ifentries(
                agent.instruction_files_book(), _tgt)
        if _act == "layer":
            try:
                _entries = agent.instruction_files_for_layer(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, "\n".join(
                _fmt_ifentry(entry) for entry in _entries) or (
                "No instruction files are held.")
        if _act == "panel":
            return True, False, _fmt_ifpanel(
                agent.instruction_files_book())
        return True, False, agent.instruction_files_status()["screen"]
    if command == "/memorymap":
        # M-150 terminal road: show the project memory map
        # held this session (the shipped example book when
        # none is held), show one entry, one section's
        # entries, or the panel derived from the whole
        # book, kept by the Scribe, on the pure layer's
        # parser + formatters. This road writes and edits
        # no project file and persists nothing - and there
        # is no Part VIII board yet, so this screen is
        # where the project memory map is visible.
        from .core.project_memory_map import format_entries as _fmt_mmentries, format_entry as _fmt_mmentry, format_panel as _fmt_mmpanel, parse_memory_map_args as _parse_mm
        try:
            _act, _tgt = _parse_mm(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "entry":
            try:
                _entry = agent.get_memory_map_entry(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_mmentry(_entry)
        if _act == "section":
            return True, False, _fmt_mmentries(
                agent.project_memory_map_book(), _tgt)
        if _act == "panel":
            return True, False, _fmt_mmpanel(
                agent.project_memory_map_book())
        return True, False, agent.project_memory_map_status()["screen"]
    if command == "/glassbox":
        # M-151 terminal road: show the compaction
        # glass-box held this session (the shipped
        # example book when none is held), show one
        # record, one record's summary versions, or
        # the panel derived from the whole book, on
        # the pure layer's parser + formatters. This
        # road compacts no live context, calls no
        # model and persists nothing - and there is
        # no Part VIII board yet, so this screen is
        # where the glass box is visible. (/compact
        # stays the live pruner's own command; the
        # glass box is the shown, editable account
        # of compactions, as data.)
        from .core.compaction_glassbox import format_panel as _fmt_gbpanel, format_record as _fmt_gbrecord, format_versions as _fmt_gbversions, parse_glassbox_args as _parse_gb
        try:
            _act, _tgt = _parse_gb(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "record":
            try:
                _record = agent.get_compaction_record(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_gbrecord(_record)
        if _act == "versions":
            try:
                _record = agent.get_compaction_record(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_gbversions(_record)
        if _act == "panel":
            return True, False, _fmt_gbpanel(
                agent.compaction_glassbox_book())
        return True, False, agent.compaction_glassbox_status()["screen"]
    if command == "/graphsearch":
        # M-152 terminal road: show the graph
        # retrieval held this session (the shipped
        # example book when none is held), show one
        # connected piece, the latest bundle's
        # seeds, or the panel derived from the
        # latest bundle, on the pure layer's parser
        # + formatters. This road calls no model,
        # edits no code and persists nothing - and
        # there is no Part VIII board yet, so this
        # screen is where the retrieval is visible.
        from .core.graph_retrieval import format_panel as _fmt_grpanel, format_seeds as _fmt_grseeds, parse_graphsearch_args as _parse_gr
        try:
            _act, _tgt = _parse_gr(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "node":
            try:
                _node = agent.get_graph_retrieval_node(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            from .core.graph_retrieval import format_node as _fmt_grnode
            return True, False, _fmt_grnode(_node)
        if _act == "seeds":
            return True, False, _fmt_grseeds(
                agent.graph_retrieval_book())
        if _act == "panel":
            return True, False, _fmt_grpanel(
                agent.graph_retrieval_book())
        return True, False, agent.graph_retrieval_status()["screen"]
    if command == "/daymemory":
        # M-153 terminal road: show the session memory
        # held this session (the shipped example book
        # when none is held), show one situation, the
        # latest situation's carried memory, its open
        # slices, its standing decisions, or the panel
        # derived from the latest situation, on the
        # pure layer's parser + formatters. This road
        # calls no model, resumes no live session,
        # replays no transcript and persists nothing -
        # and there is no Part VIII board yet, so this
        # screen is where the situation is visible.
        from .core.session_memory import format_decisions as _fmt_smdecisions, format_memory as _fmt_smmemory, format_panel as _fmt_smpanel, format_situation as _fmt_smsituation, format_slices as _fmt_smslices, parse_session_memory_args as _parse_sm
        try:
            _act, _tgt = _parse_sm(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "situation":
            try:
                _situation = agent.get_session_situation(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_smsituation(_situation)
        if _act == "memory":
            return True, False, _fmt_smmemory(
                agent.session_memory_book())
        if _act == "slices":
            return True, False, _fmt_smslices(
                agent.session_memory_book())
        if _act == "decisions":
            return True, False, _fmt_smdecisions(
                agent.session_memory_book())
        if _act == "panel":
            return True, False, _fmt_smpanel(
                agent.session_memory_book())
        return True, False, agent.session_memory_status()["screen"]
    if command == "/crossmemory":
        # M-154 terminal road: show the cross-project
        # book held this session (the shipped example
        # book when none is held), show one shared
        # lesson with its provenance whole, the book's
        # offers, the lessons standing accepted into
        # one target project, or the exchange panel
        # derived from the whole book, on the pure
        # layer's parser + formatters. This road calls
        # no model, writes no project's files, enters
        # nothing into any project's memory and
        # persists nothing - and there is no Part VIII
        # board yet, so this screen is where the
        # exchange is visible.
        from .core.cross_project_memory import format_accepted as _fmt_cpaccepted, format_lesson as _fmt_cplesson, format_offers as _fmt_cpoffers, format_panel as _fmt_cppanel, parse_cross_project_args as _parse_cp
        try:
            _act, _tgt = _parse_cp(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "lesson":
            try:
                _lesson = agent.get_cross_project_lesson(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_cplesson(_lesson)
        if _act == "offers":
            return True, False, _fmt_cpoffers(
                agent.cross_project_book())
        if _act == "accepted":
            return True, False, _fmt_cpaccepted(
                agent.cross_project_book(), _tgt)
        if _act == "panel":
            return True, False, _fmt_cppanel(
                agent.cross_project_book())
        return True, False, agent.cross_project_status()["screen"]
    if command == "/ledger":
        # M-155 terminal road: show the self-improving
        # book held this session (the shipped example
        # book when none is held), show one candidate
        # memory with its provenance whole, the book's
        # decisions, the candidates standing as standing
        # memories, or the ledger panel derived from
        # the whole book, on the pure layer's parser +
        # formatters. This road calls no model, writes
        # no project files, updates no live memory and
        # persists nothing - and there is no Part VIII
        # board yet, so this screen is where the ledger
        # is visible.
        from .core.self_improving_ledger import format_candidate as _fmt_sicandidate, format_decisions as _fmt_sidecisions, format_panel as _fmt_sipanel, format_standing as _fmt_sistanding, parse_self_improving_args as _parse_si
        try:
            _act, _tgt = _parse_si(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "candidate":
            try:
                _candidate = agent.get_self_improving_candidate(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_sicandidate(_candidate)
        if _act == "decisions":
            return True, False, _fmt_sidecisions(
                agent.self_improving_book())
        if _act == "standing":
            return True, False, _fmt_sistanding(
                agent.self_improving_book())
        if _act == "panel":
            return True, False, _fmt_sipanel(
                agent.self_improving_book())
        return True, False, agent.self_improving_status()["screen"]
    if command == "/decisions":
        # M-156 terminal road: show the decision book
        # held this session (the shipped example book
        # when none is held), show one decision record
        # with its provenance whole, render one record
        # as the small ADR that would land in the
        # project docs, the records standing accepted,
        # or the decision panel derived from the whole
        # book, on the pure layer's parser +
        # formatters. This road calls no model, writes
        # no project docs and persists nothing - and
        # there is no Part VIII board yet, so this
        # screen is where the records are visible.
        from .core.decision_records import format_accepted as _fmt_draccepted, format_adr as _fmt_dradr, format_panel as _fmt_drpanel, format_record as _fmt_drrecord, parse_decision_records_args as _parse_dr
        try:
            _act, _tgt = _parse_dr(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "record":
            try:
                _record = agent.get_decision_record(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_drrecord(_record)
        if _act == "adr":
            try:
                _record = agent.get_decision_record(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_dradr(_record)
        if _act == "accepted":
            return True, False, _fmt_draccepted(
                agent.decision_records_book())
        if _act == "panel":
            return True, False, _fmt_drpanel(
                agent.decision_records_book())
        return True, False, agent.decision_records_status()["screen"]
    if command == "/forget":
        # M-157 terminal road: show the forget book
        # held this session (the shipped example book
        # when none is held), show one forget entry with
        # its provenance whole, the entries standing
        # forgotten, the memories still held apart in
        # quarantine, or the forget panel derived from
        # the whole book, on the pure layer's parser +
        # formatters. This road calls no model, mutates
        # no live memory and persists nothing - every
        # entry names its memory by class and reference
        # only, never its content - and there is no
        # Part VIII board yet, so this screen is where
        # the journal is visible.
        from .core.forget_quarantine import format_forgotten as _fmt_fqforgotten, format_panel as _fmt_fqpanel, format_entry as _fmt_fqentry, format_quarantined as _fmt_fqquarantined, parse_forget_args as _parse_fq
        try:
            _act, _tgt = _parse_fq(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "entry":
            try:
                _entry = agent.get_forget_entry(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_fqentry(_entry)
        if _act == "forgotten":
            return True, False, _fmt_fqforgotten(
                agent.forget_quarantine_book())
        if _act == "quarantined":
            return True, False, _fmt_fqquarantined(
                agent.forget_quarantine_book())
        if _act == "panel":
            return True, False, _fmt_fqpanel(
                agent.forget_quarantine_book())
        return True, False, agent.forget_quarantine_status()["screen"]
    if command == "/recipes":
        # M-158 terminal road: show the recipe book
        # held this session (the shipped example book
        # when none is held), show one context recipe
        # with its provenance whole, summon one recipe
        # by its name, or the recipe panel derived from
        # the whole book, on the pure layer's parser +
        # formatters. This road calls no model, assembles
        # no live context, edits no code and persists
        # nothing - a recipe is held and summoned as data
        # only - and there is no Part VIII board yet, so
        # this screen is where the book is visible.
        from .core.context_recipes import format_panel as _fmt_crpanel, format_recipe as _fmt_crrecipe, format_summon as _fmt_crsummon, parse_recipe_args as _parse_cr
        try:
            _act, _tgt = _parse_cr(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "recipe":
            try:
                _recipe = agent.get_context_recipe(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_crrecipe(_recipe)
        if _act == "summon":
            try:
                _recipe = agent.context_recipes_book().recipe_named(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_crsummon(_recipe)
        if _act == "panel":
            return True, False, _fmt_crpanel(
                agent.context_recipes_book())
        return True, False, agent.context_recipes_status()["screen"]
    if command == "/pins":
        # M-159 terminal road: show the pinning book
        # held this session (the shipped example book
        # when none is held), show one pin with its
        # provenance whole, show the pins of one kind,
        # or the pin panel derived from the whole book,
        # on the pure layer's parser + formatters. This
        # road calls no model, compacts nothing, drops
        # nothing, edits no code and persists nothing -
        # a pin is held as data only - and there is no
        # Part VIII board yet, so this screen is where
        # the book is visible.
        from .core.pinning_protection import format_panel as _fmt_pnpanel, format_pin as _fmt_pnpin, format_pins as _fmt_pnpins, parse_pin_args as _parse_pn
        try:
            _act, _tgt = _parse_pn(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "pin":
            try:
                _pin = agent.get_pin(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnpin(_pin)
        if _act == "kind":
            return True, False, _fmt_pnpins(
                agent.pinning_protection_book(), _tgt)
        if _act == "panel":
            return True, False, _fmt_pnpanel(
                agent.pinning_protection_book())
        return True, False, agent.pinning_protection_status()["screen"]
    if command == "/thrift":
        # M-160 terminal road: show the thrift book
        # held this session (the shipped example book
        # when none is held), show one record with its
        # provenance whole, show the records of one
        # road, the thrift panel derived from the whole
        # book, or the thrift cost line derived for the
        # whole book, on the pure layer's parser +
        # formatters. This road calls no model, reads
        # no file, edits no code and persists nothing -
        # thrift is held as data only - and there is no
        # Part VIII board yet, so this screen is where
        # the book is visible.
        from .core.token_thrift import format_cost_line as _fmt_ttline, format_panel as _fmt_ttpanel, format_thrift_record as _fmt_ttrec, format_thrift_records as _fmt_ttrecs, parse_thrift_args as _parse_tt
        try:
            _act, _tgt = _parse_tt(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "record":
            try:
                _rec = agent.get_thrift_record(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_ttrec(_rec)
        if _act == "road":
            return True, False, _fmt_ttrecs(
                agent.token_thrift_book(), _tgt)
        if _act == "panel":
            return True, False, _fmt_ttpanel(
                agent.token_thrift_book())
        if _act == "costs":
            return True, False, _fmt_ttline(
                agent.token_thrift_book())
        return True, False, agent.token_thrift_status()["screen"]
    if command == "/endurance":
        # M-161 terminal road: show the endurance book
        # held this session (the shipped example book
        # when none is held), show one record with its
        # provenance whole, show the records of one
        # kind, the endurance panel derived from the
        # whole book, or the endurance verdict derived
        # for the whole book, on the pure layer's parser
        # + formatters. This road runs no live session,
        # appends to no live journal, times no live
        # retrieval and persists nothing - endurance is
        # held as data only - and there is no Part VIII
        # board yet, so this screen is where the book
        # is visible.
        from .core.long_session_endurance import format_endurance_record as _fmt_elrec, format_endurance_records as _fmt_elrecs, format_panel as _fmt_elpanel, format_verdict as _fmt_elverdict, parse_endurance_args as _parse_el
        try:
            _act, _tgt = _parse_el(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "record":
            try:
                _rec = agent.get_endurance_record(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_elrec(_rec)
        if _act == "kind":
            return True, False, _fmt_elrecs(
                agent.long_session_endurance_book(), _tgt)
        if _act == "panel":
            return True, False, _fmt_elpanel(
                agent.long_session_endurance_book())
        if _act == "verdict":
            return True, False, _fmt_elverdict(
                agent.long_session_endurance_book())
        return True, False, agent.long_session_endurance_status()["screen"]
    if command == "/multisession":
        # M-162 terminal road: show the multi-session
        # book held this session (the shipped example
        # book when none is held), show one session
        # with its provenance whole, show the session
        # standing on one branch, the multi-session
        # panel derived from the whole book, or the
        # isolation verdict derived for the whole book,
        # on the pure layer's parser + formatters. This
        # road spawns no live session, appends to no
        # live journal and persists nothing - parallel
        # sessions are held as data only - and there is
        # no Part VIII board yet, so this screen is
        # where the book is visible.
        from .core.multi_session_projects import format_isolation as _fmt_miso, format_parallel_session as _fmt_mses, format_parallel_sessions as _fmt_msess, format_panel as _fmt_mspanel, parse_multisession_args as _parse_ms
        try:
            _act, _tgt = _parse_ms(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "session":
            try:
                _ses = agent.get_parallel_session(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_mses(_ses)
        if _act == "branch":
            return True, False, _fmt_msess(
                agent.multi_session_projects_book(), _tgt)
        if _act == "panel":
            return True, False, _fmt_mspanel(
                agent.multi_session_projects_book())
        if _act == "isolation":
            return True, False, _fmt_miso(
                agent.multi_session_projects_book())
        return True, False, agent.multi_session_projects_status()["screen"]
    if command == "/handoffsummary":
        # M-163 terminal road: show the handoff book
        # held this session (the shipped example book
        # when none is held), show one handoff with
        # its provenance whole, show the handoff ending
        # one session, the handoff panel derived from
        # the whole book, or the handoff verdict
        # derived for the whole book, on the pure
        # layer's parser + formatters. This road sends
        # nothing, posts nothing, schedules nothing and
        # persists nothing - handoffs are held as data
        # only - and there is no Part VIII board yet,
        # so this screen is where the book is visible.
        from .core.handoff_summaries import format_handoff as _fmt_hho, format_handoffs as _fmt_hhos, format_panel as _fmt_hpanel, format_verdict as _fmt_hverdict, parse_handoffsummary_args as _parse_hs
        try:
            _act, _tgt = _parse_hs(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "handoff":
            try:
                _ho = agent.get_handoff_summary(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_hho(_ho)
        if _act == "session":
            return True, False, _fmt_hhos(
                agent.handoff_summaries_book(), _tgt)
        if _act == "panel":
            return True, False, _fmt_hpanel(
                agent.handoff_summaries_book())
        if _act == "verdict":
            return True, False, _fmt_hverdict(
                agent.handoff_summaries_book())
        return True, False, agent.handoff_summaries_status()["screen"]
    if command == "/memoryxport":
        # M-164 terminal road: show the memory export
        # book held this session (the shipped example
        # book when none is held), show one package with
        # its provenance whole, show the packages packing
        # one project, the memory panel derived from the
        # whole book, or the portability verdict derived
        # for the whole book, on the pure layer's parser
        # + formatters. This road sends nothing, posts
        # nothing, schedules nothing, persists nothing
        # and writes no live memory - packages are held
        # as data only - and there is no Part VIII board
        # yet, so this screen is where the book is visible.
        from .core.memory_import_export import format_package as _fmt_mpkg, format_packages as _fmt_mpkgs, format_panel as _fmt_mxpanel, format_verdict as _fmt_mxverdict, parse_memoryxport_args as _parse_mx
        try:
            _act, _tgt = _parse_mx(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "package":
            try:
                _pkg = agent.get_memory_package(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_mpkg(_pkg)
        if _act == "project":
            return True, False, _fmt_mpkgs(
                agent.memory_import_export_book(), _tgt)
        if _act == "panel":
            return True, False, _fmt_mxpanel(
                agent.memory_import_export_book())
        if _act == "verdict":
            return True, False, _fmt_mxverdict(
                agent.memory_import_export_book())
        return True, False, agent.memory_import_export_status()["screen"]
    if command == "/subconscious":
        # M-165 terminal road: show the subconscious
        # book held this session (the shipped example
        # book when none is held), show one memory with
        # its provenance whole, show one layer's
        # memories, show the memories earned from one
        # kind, the subconscious panel derived from the
        # whole book, or the freshness verdict derived
        # for the whole book, on the pure layer's parser
        # + formatters. This road sends nothing, posts
        # nothing, schedules nothing, persists nothing
        # and writes no live memory - memories are held
        # as data only - and there is no Part VIII board
        # yet, so this screen is where the book is visible.
        from .core.subconscious_v2 import format_memories as _fmt_smems, format_memory as _fmt_smem, format_panel as _fmt_spanel, format_verdict as _fmt_sverdict, parse_subconscious_args as _parse_sub
        try:
            _act, _tgt = _parse_sub(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "memory":
            try:
                _mem = agent.get_subconscious_memory(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_smem(_mem)
        if _act == "layer":
            return True, False, _fmt_smems(
                agent.subconscious_book(), layer=_tgt)
        if _act == "source":
            return True, False, _fmt_smems(
                agent.subconscious_book(), source_kind=_tgt)
        if _act == "panel":
            return True, False, _fmt_spanel(
                agent.subconscious_book())
        if _act == "verdict":
            return True, False, _fmt_sverdict(
                agent.subconscious_book())
        return True, False, agent.subconscious_status()["screen"]
    if command == "/contradiction":
        # M-166 terminal road: show the contradiction
        # book held this session (the shipped example
        # book when none is held), show one watch with
        # its correction shown, show the watches over
        # one holding kind, the contradiction panel
        # derived from the whole book, or the
        # correction verdict derived for the whole
        # book, on the pure layer's parser +
        # formatters. This road sends nothing, posts
        # nothing, schedules nothing, persists nothing
        # and overwrites no stored memory - watches
        # are held as data only, and the correction
        # stands on this layer's map alone - and there
        # is no Part VIII board yet, so this screen is
        # where the book is visible.
        from .core.contradiction_watch import format_panel as _fmt_cpanel, format_verdict as _fmt_cverdict, format_watch as _fmt_cwatch, format_watches as _fmt_cwatches, parse_contradiction_args as _parse_con
        try:
            _act, _tgt = _parse_con(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "watch":
            try:
                _watch = agent.get_contradiction_watch(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_cwatch(_watch)
        if _act == "kind":
            return True, False, _fmt_cwatches(
                agent.contradiction_book(), kind=_tgt)
        if _act == "panel":
            return True, False, _fmt_cpanel(
                agent.contradiction_book())
        if _act == "verdict":
            return True, False, _fmt_cverdict(
                agent.contradiction_book())
        return True, False, agent.contradiction_status()["screen"]
    if command == "/private":
        # M-167 terminal road: show the privacy book
        # held this session (the shipped example book
        # when none is held), show one posting with
        # its boundary shown, show the postings over
        # one holding kind or living in one store, the
        # privacy panel derived from the whole book,
        # or the privacy verdict derived for the whole
        # book, on the pure layer's parser +
        # formatters. This road sends nothing, posts
        # nothing, schedules nothing, persists nothing,
        # syncs nothing and moves no memory - postings
        # are held as data only, and a posting opens
        # no road itself - and there is no Part VIII
        # board yet, so this screen is where the book
        # is visible.
        from .core.private_by_architecture import format_panel as _fmt_ppanel, format_posting as _fmt_pposting, format_postings as _fmt_ppostings, format_verdict as _fmt_pverdict, parse_privacy_args as _parse_pri
        try:
            _act, _tgt = _parse_pri(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "posting":
            try:
                _posting = agent.get_privacy_posting(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pposting(_posting)
        if _act == "kind":
            return True, False, _fmt_ppostings(
                agent.privacy_book(), kind=_tgt)
        if _act == "home":
            return True, False, _fmt_ppostings(
                agent.privacy_book(), home=_tgt)
        if _act == "panel":
            return True, False, _fmt_ppanel(
                agent.privacy_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(
                agent.privacy_book())
        return True, False, agent.privacy_status()["screen"]
    if command == "/memorydoctor":
        # M-168 terminal road: show the doctor book
        # held this session (the shipped example book
        # when none is held), show one finding with
        # its repair shown, show the findings one
        # check raised or living in one store, the
        # doctor panel derived from the whole book,
        # the doctor verdict derived for the whole
        # book, or the repairs derived from the whole
        # book, on the pure layer's parser +
        # formatters. This road sends nothing, posts
        # nothing, schedules nothing, persists
        # nothing and writes no live memory -
        # findings are held as data only, and a
        # repair applied on the agent road marks a
        # held finding repaired in the session's own
        # book and rewrites no live store - and
        # there is no Part VIII board yet, so this
        # screen is where the book is visible.
        from .core.memory_doctor import format_finding as _fmt_dfinding, format_findings as _fmt_dfindings, format_panel as _fmt_dpanel, format_repairs as _fmt_drepairs, format_verdict as _fmt_dverdict, parse_memory_doctor_args as _parse_doc
        try:
            _act, _tgt = _parse_doc(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "finding":
            try:
                _finding = agent.get_memory_finding(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_dfinding(_finding)
        if _act == "check":
            return True, False, _fmt_dfindings(
                agent.memory_doctor_book(), check=_tgt)
        if _act == "store":
            return True, False, _fmt_dfindings(
                agent.memory_doctor_book(), store=_tgt)
        if _act == "panel":
            return True, False, _fmt_dpanel(
                agent.memory_doctor_book())
        if _act == "verdict":
            return True, False, _fmt_dverdict(
                agent.memory_doctor_book())
        if _act == "repairs":
            return True, False, _fmt_drepairs(
                agent.memory_doctor_book())
        return True, False, agent.memory_doctor_status()["screen"]
    if command == "/coldstart":
        # M-169 terminal road: show the cold-start
        # book held this session (the shipped example
        # book when none is held), show one record
        # with its derived plan shown, show the
        # opening one project stands under, the
        # readiness panel derived from the whole
        # book, the verdict derived for the whole
        # book, or every record's derived stage plan,
        # on the pure layer's parser + formatters.
        # This road sends nothing, posts nothing,
        # schedules nothing, persists nothing, starts
        # no thread and rebuilds no live map -
        # openings are held as data only, and a stage
        # marked done on the agent road marks it on
        # the session's own book alone - and there is
        # no Part VIII board yet, so this screen is
        # where the book is visible.
        from .core.cold_start import format_panel as _fmt_cspanel, format_record as _fmt_csrecord, format_verdict as _fmt_csverdict, parse_cold_start_args as _parse_cs, stage_plan_of as _cs_plan
        try:
            _act, _tgt = _parse_cs(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "record":
            try:
                _record = agent.get_cold_start_record(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_csrecord(_record)
        if _act == "project":
            try:
                _record = agent.cold_start_for_project(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_csrecord(_record)
        if _act == "panel":
            return True, False, _fmt_cspanel(agent.cold_start_book())
        if _act == "verdict":
            return True, False, _fmt_csverdict(agent.cold_start_book())
        if _act == "stages":
            return True, False, "\n".join(
                f"{r.record_id or '-'}: {', '.join(_cs_plan(r))}"
                for r in agent.cold_start_book().records)
        return True, False, agent.cold_start_status()["screen"]
    if command == "/workview":
        # M-172 terminal road: show the work book
        # held this session as a calm narrative
        # stream (the shipped example book when none
        # is held), show one event with its detail
        # still held back, show the whole stream or
        # one event with the tool detail on the
        # one-keystroke-away detail road, show one
        # kind's actions, the work panel derived
        # from the whole book, or the verdict
        # derived for the whole book, on the pure
        # layer's parser + formatters. This road
        # sends nothing, posts nothing, schedules
        # nothing, persists nothing and runs no tool
        # - actions are held as data only, the
        # narrative never carries the detail, and
        # the slice board is M-173's road, so this
        # screen is where the book is visible.
        from .core.work_view import format_event as _fmt_wvevent, format_event_detail as _fmt_wvdetail, format_panel as _fmt_wvpanel, format_stream as _fmt_wvstream, format_verdict as _fmt_wvverdict, parse_work_view_args as _parse_wv
        try:
            _act, _tgt = _parse_wv(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "event":
            try:
                _event = agent.get_work_view_event(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_wvevent(_event)
        if _act == "detail" and _tgt is not None:
            try:
                _event = agent.get_work_view_event(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_wvdetail(_event)
        if _act == "detail":
            return True, False, _fmt_wvstream(
                agent.work_view_book(), detail=True)
        if _act == "kind":
            return True, False, _fmt_wvstream(
                agent.work_view_book(), kind=_tgt)
        if _act == "panel":
            return True, False, _fmt_wvpanel(agent.work_view_book())
        if _act == "verdict":
            return True, False, _fmt_wvverdict(agent.work_view_book())
        return True, False, agent.work_view_status()["screen"]
    if command == "/sliceboard":
        # M-173 terminal road: show the slice board
        # held this session as a visible board (the
        # shipped example board when none is held),
        # show one effective card, one column's
        # cards, one held hand action, the board
        # panel derived from the whole board, or the
        # verdict derived for the whole board, on
        # the pure layer's parser + formatters. This
        # road sends nothing, posts nothing,
        # schedules nothing, persists nothing and
        # runs no build - plans are held as data
        # only, and a hand action moves the held
        # board alone, never the shipped roadmap.
        from .core.slice_board import format_action as _fmt_sbaction, format_board as _fmt_sbboard, format_card as _fmt_sbcard, format_panel as _fmt_sbpanel, format_verdict as _fmt_sbverdict, parse_slice_board_args as _parse_sb
        try:
            _act, _tgt = _parse_sb(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "card":
            try:
                _card = agent.get_slice_board_card(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_sbcard(_card)
        if _act == "column":
            return True, False, _fmt_sbboard(
                agent.slice_board_board(), column=_tgt)
        if _act == "action":
            try:
                _action = agent.get_slice_board_action(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_sbaction(_action)
        if _act == "panel":
            return True, False, _fmt_sbpanel(agent.slice_board_board())
        if _act == "verdict":
            return True, False, _fmt_sbverdict(agent.slice_board_board())
        return True, False, agent.slice_board_status()["screen"]
    if command == "/approvalcards":
        # M-174 terminal road: show the approval
        # cards held this session as perfected cards
        # (the shipped example book when none is
        # held), show one card whole - its target and
        # consequence as their own lines, its context
        # on the card, its derived remembered scope
        # and its exactly equal keyboard and mouse
        # paths - show one held decision record, the
        # panel derived from the whole book, or the
        # verdict derived for the whole book, on the
        # pure layer's parser + formatters. This road
        # sends nothing, posts nothing, schedules
        # nothing, persists nothing, renders no live
        # UI, executes no approval and saves no
        # remembered approval - questions are held
        # as data only.
        from .core.approval_cards import format_card as _fmt_accard, format_decision as _fmt_acdecision, format_panel as _fmt_acpanel, format_verdict as _fmt_acverdict, parse_approval_cards_args as _parse_ac
        try:
            _act, _tgt = _parse_ac(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "card":
            try:
                _card = agent.get_approval_card(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_accard(_card)
        if _act == "decision":
            try:
                _decision = agent.get_approval_decision(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_acdecision(_decision)
        if _act == "panel":
            return True, False, _fmt_acpanel(agent.approval_cards_book())
        if _act == "verdict":
            return True, False, _fmt_acverdict(agent.approval_cards_book())
        return True, False, agent.approval_cards_status()["screen"]
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
