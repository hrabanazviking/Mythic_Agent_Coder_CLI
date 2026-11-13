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
        return True, False, "/help /clear /compact /model <name> [url] /route [office] /fallback [on|off|add|clear] /costroute [on|off|<task-class>] /editformat [auto|<format>|<task-kind>] /hashanchor [on|off] /repairloop [on|off] /hunkreview [on|off] /changeset [on|off] /rename [on|off|<old-path> <new-path>] /generated [on|off|<path>|mark <path> <generator>] /largefile [on|off|<path>]/largefile [on|off|<path>] /stash [show|on|off|shelve <name>|restore <name>|drop <name>] /patch [show|on|off|export <set name>|import <patch file>] /editor [show|on|off|file <path>|prompt] /diff [show|on|off|unified|side-by-side|whitespace|whitespace off] /blame [show|on|off|<path> [<line>]] /massedit [show|on|off] /posture [show|<profile name>] /remember [list|forget <id>|clear] /sandbox [show|on|off|truth|plan <command>] /network [show|on|off|list|check <tool> <host>|allow <tool> <domain>] /pathjail [show|on|off|grants|check <path>|grant <abs-path>] /plan [show|on|off|approve|build|check <effect>] /hooks [show|show <event>|check <event>] /hookpacks [show|show <pack>|install <pack>] /background [show|show <job>|tail [<job>]|kill <job>|start <command...>] /keeper [show|show <target>|check|heartbeat <target>] /schedule [show|show <job>|check] /fleet [show|show <task>|verdict|resume] /budgets [show|show <budget>|check|check <budget>] /halt [show|show <halt>|pull|pull <target>] /audit [show|show <entry>|export] /secrets [show|show <screening>|check <file>] /doctrine [show|show <judgement>|ladder|check <command>] /rollback [show|show <run>|drills|run <drill>] /multirepo [show|show <set>|repos] /remote [show|show <plan>|targets] /grace [show|show <record>|failures] /moment [show|show <record>|parts] /policy [show|plan|sections|apply] /crew [show|show <member>|office <office>] /offices [show|show <office>|handoffs <office>|contract <from> <to>] /offices custom [show|show <office>|handoffs <office>|contract <from> <to>] /worktrees [show|show <member>|plan|merges] /dealing [show|show <member>|plan|loads] /comms [show|show <member>|ask|kinds] /deadlock [show|show <member>|kinds] /merge [show|show <member>|lines|kinds] /hetero [show|show <member>|routes|kinds] /veto [show|show <slice>|gates|kinds] /swarm [show|show <member>|digest|sources|kinds] /panel [show|show <reviewer>|outcome|verdicts|kinds] /memory [show|show <member>|search <words>|tag <tag>|entry <entry-id>|members] /standup [show|digest|done|doing|blocked|needs-you|entry <entry-id>|kinds] /crewsize [show|recommend <case-id>|case <case-id>|solo|pair|crew|full-crew|kinds] /voices [show|profile <member-id>|report <report-id>|plain|warm|wry|grim|registers] /externals [show|seat <member-id>|check <member-id>|mcp|transports] /replay [show|step <step-id>|trace <step-id>] /foster [show|report <report-id>|redeal <slice-id>|escalation <report-id>] /costcourt [show|entry <entry-id>|member <member-id>|slice <slice-id>|ledger] /dogfood [show|entry <entry-id>|member <member-id>|slice <slice-id>|part <part-number>|ledger] /solo [show|capability <capability-id>|member <member-id>|report <member-id>|ledger] /templates [show|template <template>|member <member-id>|roster <template>|index] /interrupts [show|interrupt <interrupt-id>|member <member-id>|slice <slice-id>|report <interrupt-id>|index] /crewschedules [show|attachment <attachment-id>|template <template>|job <job-id>|report <attachment-id>|index] /contextbudget [show|item <item-id>|kind <kind>|meter|panel] /mentions [show|mention <mention-id>|kind <kind>|plan <mention-id>|parse <text>|index] /instructionfiles [show|entry <file-id>|origin <origin>|layer <layer>|panel] /memorymap [show|entry <entry-id>|section <section>|panel] /glassbox [show|record <record-id>|versions <record-id>|panel] /graphsearch [show|node <node-id>|seeds|panel] /daymemory [show|situation <situation-id>|memory|slices|decisions|panel] /crossmemory [show|lesson <lesson-id>|offers|accepted <project>|panel] /ledger [show|candidate <candidate-id>|decisions|standing|panel] /decisions [show|record <record-id>|adr <record-id>|accepted|panel] /forget [show|entry <entry-id>|forgotten|quarantined|panel] /recipes [show|recipe <recipe-id>|summon <recipe name>|panel] /pins [show|pin <pin-id>|kind <kind>|panel] /thrift [show|record <record-id>|road <road>|panel|costs] /endurance [show|record <record-id>|kind <kind>|panel|verdict] /multisession [show|session <session-id>|branch <branch>|panel|isolation] /handoffsummary [show|handoff <handoff-id>|session <session-ref>|panel|verdict] /memoryxport [show|package <package-id>|project <project>|panel|verdict] /subconscious [show|memory <memory-id>|layer <core|subconscious>|source <source-kind>|panel|verdict] /contradiction [show|watch <watch-id>|kind <memory-kind>|panel|verdict] /private [show|posting <posting-id>|kind <memory-kind>|home <home>|panel|verdict] /memorydoctor [show|finding <finding-id>|check <check>|store <store>|panel|verdict|repairs] /coldstart [show|record <record-id>|project <project-ref>|panel|verdict|stages] /workview [show|event <event-id>|detail [<event-id>]|kind <kind>|panel|verdict] /sliceboard [show|card <slice-id>|column <column>|action <action-id>|panel|verdict] /approvalcards [show|card <card-id>|decision <decision-id>|panel|verdict] /fuzzypicker [show|candidate <candidate-id>|search <search-id>|find <words>|kind <kind>|panel|verdict] /commandpalace [show|entry <entry-id>|browse <browse-id>|visit <words>|kind <kind>|panel|verdict] /promptcraft [show|item <item-id>|view <view-id>|project <project>|kind <kind>|panel|verdict] /statusline [show|fact <fact-id>|view <view-id>|kind <kind>|line|panel|verdict] /themesgrownup [show|theme <theme-id>|view <view-id>|mode <mode>|panel|verdict] /voiceinout [show|dictation <dictation-id>|standup <standup-id>|action <action-id>|view <view-id>|kind <kind>|panel|verdict] /manners [show|job <job-id>|channel <channel-id>|rule <rule-id>|view <view-id>|kind <kind>|panel|verdict] /skin [show|report <report-id>|approval <approval-id>|standup <standup-id>|term <term-id>|view <view-id>|kind <kind>|panel|verdict|unfold <item-id>|register] /errors [show|error <error-id>|trace <error-id>|view <view-id>|kind <kind>|panel|verdict] /onboard [show|detection <detection-id>|walk|offer <offer-id>|view <view-id>|outcome <outcome>|panel|verdict] /lessons [show|lesson <lesson-id>|play|scratch <scratch-id>|view <view-id>|readiness <readiness>|panel|verdict] /helpask [show|doc <doc-id>|ask <words>|screen <screen>|view <view-id>|standing <standing>|panel|verdict|coverage] /keymap [show|act <act-id>|key <key>|area <area>|view <view-id>|mode <mode-id>|print|panel|verdict] /mouse [show|gesture <gesture-id>|road <road>|area <area>|view <view-id>|link <link-id>|guide|panel|verdict] /gallery [show|card <card-id>|road <road>|outcome <outcome>|view <view-id>|action <action-id>|index|panel|verdict] /costs [show|line <line-id>|budget <budget>|scope <scope>|view <view-id>|warning <warning-id>|index|panel|verdict] /theatre [show|hunk <hunk-id>|target <target>|kind <kind>|view <view-id>|comment <comment-id>|index|panel|verdict] /panes [show|pane <pane-id>|target <target>|kind <kind>|layout <layout-id>|note <note-id>|index|panel|verdict] /smallterminal [show|fold <fold-id>|preserves <preserves>|kind <kind>|view <view-id>|note <note-id>|index|panel|verdict] /copyshare [show|clip <clip-id>|markdown <markdown>|kind <kind>|view <view-id>|note <note-id>|index|panel|verdict] /settingsroom [show|setting <setting-id>|meaning <meaning>|section <section>|view <view-id>|note <note-id>|index|panel|verdict] /commandpalette [show|entry <entry-id>|keywords <keywords>|kind <kind>|view <view-id>|note <note-id>|index|panel|verdict] /uiundo [show|pane <pane-id>|state <state>|kind <kind>|view <view-id>|note <note-id>|index|panel|verdict] /accessverify [show|gate <gate-id>|evidence <evidence>|kind <kind>|view <view-id>|note <note-id>|index|panel|verdict] /campaigns [show|slice <slice-id>|checks <checks>|state <state>|view <view-id>|note <note-id>|index|panel|verdict] /intent [show|intent <intent-id>|citation <citation>|project <project>|view <view-id>|note <note-id>|index|panel|verdict] /slicing [show|draft <draft-id>|outcome <outcome>|intent <intent-id>|view <view-id>|note <note-id>|index|panel|verdict] /juggernaut [show|run <run-id>|phase <phase>|slice <slice-id>|view <view-id>|note <note-id>|index|panel|verdict] /acceptance [show|audit <audit-id>|check <check>|slice <slice-id>|view <view-id>|note <note-id>|index|panel|verdict] /banking [show|banking <banking-id>|check <check>|slice <slice-id>|view <view-id>|note <note-id>|index|panel|verdict] /keepruntime [show|keeping <keeping-id>|check <check>|slice <slice-id>|view <view-id>|note <note-id>|index|panel|verdict] /pauselines [show|pausing <pausing-id>|check <check>|slice <slice-id>|view <view-id>|note <note-id>|index|panel|verdict] /questionlaw [show|questioning <questioning-id>|check <check>|slice <slice-id>|view <view-id>|note <note-id>|index|panel|verdict] /scopesentry [show|sentry <sentry-id>|check <check>|slice <slice-id>|view <view-id>|note <note-id>|index|panel|verdict] /mapupkeep [show|upkeep <upkeep-id>|check <check>|slice <slice-id>|view <view-id>|note <note-id>|index|panel|verdict] /bugrule [show|bug <bug-id>|check <check>|slice <slice-id>|view <view-id>|note <note-id>|index|panel|verdict] /retrospectives [show|retro <retro-id>|check <check>|slice <slice-id>|view <view-id>|note <note-id>|index|panel|verdict] /patterns [show|pattern <pattern-id>|check <check>|slice <slice-id>|view <view-id>|note <note-id>|index|panel|verdict] /estimates [show|estimate <estimate-id>|check <check>|slice <slice-id>|view <view-id>|note <note-id>|index|panel|verdict] /hall [show|campaign <campaign-id>|check <check>|repo <repo-id>|view <view-id>|note <note-id>|index|panel|verdict] /shapes [show|template <template-id>|check <check>|kind <kind-id>|view <view-id>|note <note-id>|index|panel|verdict] /mimis [show|road <road-id>|check <check>|concordance <concordance-id>|view <view-id>|note <note-id>|index|panel|verdict] /resumes [show|resume <resume-id>|check <check>|pause <pause-id>|view <view-id>|note <note-id>|index|panel|verdict] /milestones [show|report <report-id>|check <check>|boundary <boundary-id>|view <view-id>|note <note-id>|index|panel|verdict] /log [show|entry <entry-id>|check <check>|day <day-id>|view <view-id>|note <note-id>|index|panel|verdict] /selfmod [show|change <change-id>|check <check>|tool <tool-id>|view <view-id>|note <note-id>|index|panel|verdict] /failures [show|failure <failure-id>|stage <stage>|run <run-id>|view <view-id>|note <note-id>|index|panel|verdict] /dryrun [show|rehearsal <rehearsal-id>|stage <stage>|campaign <campaign-id>|view <view-id>|note <note-id>|index|panel|verdict] /export [show|bundle <bundle-id>|stage <stage>|campaign <campaign-id>|view <view-id>|note <note-id>|index|panel|verdict] /orders [show|order <order-id>|stage <stage>|campaign <campaign-id>|view <view-id>|note <note-id>|index|panel|verdict] /workflow [show|proposal <proposal-id>|stage <stage>|campaign <campaign-id>|view <view-id>|note <note-id>|index|panel|verdict] /scaling [show|endeavour <endeavour-id>|stage <stage>|campaign <campaign-id>|view <view-id>|note <note-id>|index|panel|verdict] /course [show|lesson <lesson-id>|stage <stage>|campaign <campaign-id>|view <view-id>|note <note-id>|index|panel|verdict] /metrics [show|reading <reading-id>|stage <stage>|campaign <campaign-id>|view <view-id>|note <note-id>|index|panel|verdict] /crossapp [show|external <external-id>|stage <stage>|campaign <campaign-id>|view <view-id>|note <note-id>|index|panel|verdict] /mcpclient [show|connection <connection-id>|stage <stage>|server <server-id>|view <view-id>|note <note-id>|index|panel|verdict] /mcpregistry [show|listing <listing-id>|stage <stage>|entry <entry-id>|view <view-id>|note <note-id>|index|panel|verdict] /skillsstandard [show|pack <pack-id>|stage <stage>|skill <skill-id>|view <view-id>|note <note-id>|index|panel|verdict] /customcommands [show|template <template-id>|stage <stage>|command <command-id>|view <view-id>|note <note-id>|index|panel|verdict] /pluginbundles [show|bundle <bundle-id>|stage <stage>|plugin <plugin-id>|view <view-id>|note <note-id>|index|panel|verdict] /vscodecompanions [show|companion <companion-id>|stage <stage>|editor <editor-id>|view <view-id>|note <note-id>|index|panel|verdict] /idecompanions [show|endpoint <endpoint-id>|stage <stage>|host <host-id>|view <view-id>|note <note-id>|index|panel|verdict] /rivalimporters [show|importer <importer-id>|stage <stage>|source <source-id>|view <view-id>|note <note-id>|index|panel|verdict] /samverkbridge [show|exchange <exchange-id>|stage <stage>|repo <repo-id>|view <view-id>|note <note-id>|index|panel|verdict] /samtalbridge [show|dispatch <dispatch-id>|stage <stage>|hall <hall-id>|view <view-id>|note <note-id>|index|panel|verdict] /kistakeykeeper [show|resolution <resolution-id>|stage <stage>|bridge <bridge-id>|view <view-id>|note <note-id>|index|panel|verdict] /aesirdeepening [show|report|selections|selection <office>|ask <office>|index|verdict] /githostparity [show|hosts|host <host>|record <host>|standing <host>|index|verdict] /cibridges [show|providers|provider <provider>|record <provider> <workflow>|standing <provider> <workflow>|draft [<provider> <workflow>]|index|verdict] /issuetrackers [show|trackers|tracker <tracker>|record <tracker> <issue>|standing <tracker> <issue>|draft [<tracker> <issue>]|index|verdict] /wyrdseam [show|sources|source <source>|snapshot <source> <node>|standing <source> <node>|advice [<campaign>]|index|verdict] /webhookdoors [show|sources|source <source>|event <source> <event>|standing <source> <event>|propose [<campaign>]|index|verdict] /exporteverything [show|kinds|kind <kind>|record <kind> <record>|standing <kind> <record>|prepare [<bundle>]|index|verdict] /docsmcp [show|projects|project <project>|record <project> <record>|standing <project> <record>|propose [<bridge>]|index|verdict] /bridgeaudit [show|bridges|bridge <bridge>|record <bridge> <record>|standing <bridge> <record>|report [<bridge>]|index|verdict] /benchmarkharness [show|kinds|kind <kind>|record <kind> <run>|standing <kind> <run>|report [<kind>]|index|verdict] /publishedyardstick [show|yardsticks|yardstick <yardstick>|record <yardstick> <run>|standing <yardstick> <run>|report [<yardstick>]|index|verdict] /regressioncourt [show|parts|part <part>|record <part> <run>|standing <part> <run>|draft [<battery>]|index|verdict] /performancebudgets [show|measures|measure <measure>|record <measure> <machine>|standing <measure> <machine>|report [<book>]|index|verdict] /platformmatrixfinal [show|cells|cell <cell>|record <cell>|standing <cell>|report [<book>]|index|verdict] /securityaudit [show|areas|area <area>|record <area>|standing <area>|report [<book>]|index|verdict] /privacyaudit [show|surfaces|surface <surface>|record <surface>|standing <surface>|report [<book>]|index|verdict] /accessibilityfinal [show|checks|check <check>|record <check>|standing <check>|report [<book>]|index|verdict] /docscompletion [show|guides|guide <guide>|record <guide>|standing <guide>|report [<book>]|index|verdict] /mcpserver [show|exposure <exposure-id>|stage <stage>|service <service-id>|view <view-id>|note <note-id>|index|panel|verdict] /ceremony [show|moment <moment-id>|alternative <alternative>|kind <kind>|view <view-id>|note <note-id>|index|panel|verdict] /issueslice [on|off|github <number>] /prcraft [on|off|tasks <pr>] /commitcraft [on|off|plan|commit <concern>|push] /guardians [word on|word off|check <path>] /autocommit [on|off|allow-protected|block-protected] /checkpoint [take <name>|restore <name> [discard]|on|off] /branch [on|off|fork <index> [name]|list|compare <id> <id>] /kista [adopt] /resume-thought [show] /retry [show] /vision [show|switch] /longcontext [show|<model>] /offline [show] /testkit <provider> [url] /map [task|show <path>|pin <path>|unpin <path>|pins] /ssearch <language> <pattern> /srewrite [apply] <language> <pattern> => <replacement> /lsp [show|check <path>|def <path> <line> <col>|refs <path> <line> <col>|hover <path> <line> <col>|symbols [query]] /truth <path> /format <path> [apply] /status /session /add <path> /stop /undo [list|edit|command|checkpoint <id>|<count>|on|off] /quit"
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
    if command == "/fuzzypicker":
        # M-175 terminal road: show the fuzzy
        # everything picker held this session - files,
        # symbols, commands, sessions, models and
        # themes under one fuzzy finder grammar (the
        # shipped example book when none is held) -
        # show one candidate whole, one held search
        # record, the panel an on-the-spot search
        # derives, the book's candidates of one kind,
        # the panel derived from the whole book, or
        # the verdict derived for the whole book, on
        # the pure layer's parser + formatters. This
        # road sends nothing, posts nothing, schedules
        # nothing, persists nothing, renders no live
        # UI, opens nothing the picker finds and
        # executes nothing - findings are held as data
        # only, and a search commits no choice at all.
        from .core.fuzzy_picker import build_search as _build_fpsearch, format_book as _fmt_fpbook, format_candidate as _fmt_fpcandidate, format_panel as _fmt_fppanel, format_search as _fmt_fpsearch, format_verdict as _fmt_fpverdict, parse_fuzzy_picker_args as _parse_fp
        try:
            _act, _tgt = _parse_fp(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "candidate":
            try:
                _candidate = agent.get_fuzzy_candidate(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_fpcandidate(_candidate)
        if _act == "search":
            try:
                _search = agent.get_fuzzy_search(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_fpsearch(_search)
        if _act == "find":
            try:
                _search = _build_fpsearch({
                    "seq": 1, "text": _tgt,
                    "kind_filter": "all",
                    "detail": "An on-the-spot search from "
                              "the terminal road.",
                    "recorded_on": "2026-11-09",
                    "actor": "the jarl",
                    "source": "fuzzy picker",
                    "origin_session": "session-m175"})
            except ValueError as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_fppanel(
                agent.fuzzy_picker_book(), _search)
        if _act == "kind":
            return True, False, _fmt_fpbook(
                agent.fuzzy_picker_book(), _tgt)
        if _act == "panel":
            return True, False, _fmt_fppanel(agent.fuzzy_picker_book())
        if _act == "verdict":
            return True, False, _fmt_fpverdict(agent.fuzzy_picker_book())
        return True, False, agent.fuzzy_picker_status()["screen"]
    if command == "/commandpalace":
        # M-176 terminal road: show the slash-command
        # palace held this session - every shipped
        # command and every custom command under one
        # browsing grammar (the shipped example book
        # when none is held) - show one entry whole,
        # one held browse record, the panel an
        # on-the-spot visit derives, the book entries
        # of one kind, the panel derived from the
        # whole book, or the verdict derived for the
        # whole book, on the pure layer parser +
        # formatters. This road sends nothing, posts
        # nothing, schedules nothing, persists
        # nothing, renders no live UI, opens nothing
        # the palace finds and executes nothing - an
        # entry held here is a listing, never the act
        # of opening the thing found, and a browse
        # commits no choice at all.
        from .core.command_palace import build_browse as _build_cpbrowse, format_book as _fmt_cpbook, format_browse as _fmt_cpbrowse, format_entry as _fmt_cpentry, format_panel as _fmt_cppanel, format_verdict as _fmt_cpverdict, parse_command_palace_args as _parse_cp
        try:
            _act, _tgt = _parse_cp(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "entry":
            try:
                _entry = agent.get_palace_entry(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_cpentry(_entry)
        if _act == "browse":
            try:
                _browse = agent.get_palace_browse(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_cpbrowse(_browse)
        if _act == "visit":
            try:
                _browse = _build_cpbrowse({
                    "seq": 1, "text": _tgt,
                    "kind_filter": "all",
                    "detail": "An on-the-spot browse from "
                              "the terminal road.",
                    "recorded_on": "2026-11-09",
                    "actor": "the jarl",
                    "source": "command palace",
                    "origin_session": "session-m176"})
            except ValueError as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_cppanel(
                agent.command_palace_book(), _browse)
        if _act == "kind":
            return True, False, _fmt_cpbook(
                agent.command_palace_book(), _tgt)
        if _act == "panel":
            return True, False, _fmt_cppanel(agent.command_palace_book())
        if _act == "verdict":
            return True, False, _fmt_cpverdict(agent.command_palace_book())
        return True, False, agent.command_palace_status()["screen"]
    if command == "/promptcraft":
        # M-177 terminal road: show the prompt craft
        # held this session - the input box's craft as
        # data: multi-line drafts, history per project,
        # pasted images and dropped files (the shipped
        # example book when none is held) - show one
        # item whole, one held view record, the panel
        # an on-the-spot project view derives, the book
        # items of one kind, the panel derived from
        # the whole book, or the verdict derived for
        # the whole book, on the pure layer parser +
        # formatters. This road edits no live input
        # box, pastes nothing, drops nothing, dictates
        # nothing (dictation is M-180's road), opens no
        # dropped file, sends nothing, posts nothing,
        # schedules nothing, persists nothing and
        # renders no live UI - an item held here is a
        # finding, never the act of typing, pasting or
        # sending the prompt found.
        from .core.prompt_craft import build_view as _build_pcview, format_book as _fmt_pcbook, format_item as _fmt_pcitem, format_panel as _fmt_pcpanel, format_verdict as _fmt_pcverdict, format_view as _fmt_pcview, parse_prompt_craft_args as _parse_pc
        try:
            _act, _tgt = _parse_pc(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "item":
            try:
                _item = agent.get_craft_item(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pcitem(_item)
        if _act == "view":
            try:
                _view = agent.get_craft_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pcview(_view)
        if _act == "project":
            try:
                _view = _build_pcview({
                    "seq": 1, "project_filter": _tgt,
                    "detail": "An on-the-spot view from "
                              "the terminal road.",
                    "recorded_on": "2026-11-09",
                    "actor": "the jarl",
                    "source": "prompt craft",
                    "origin_session": "session-m177"})
            except ValueError as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pcpanel(
                agent.prompt_craft_book(), _view)
        if _act == "kind":
            return True, False, _fmt_pcbook(
                agent.prompt_craft_book(), _tgt)
        if _act == "panel":
            return True, False, _fmt_pcpanel(agent.prompt_craft_book())
        if _act == "verdict":
            return True, False, _fmt_pcverdict(agent.prompt_craft_book())
        return True, False, agent.prompt_craft_status()["screen"]
    if command == "/statusline":
        # M-178 terminal road: show the status line
        # held this session - the six facts as data:
        # the model, the posture, the context meter,
        # the cost so far, the crew state and the
        # sandbox state (the shipped example book when
        # none is held) - show one fact whole, one
        # held view record, the book facts of one
        # kind, the status line derived from the whole
        # book, the panel derived from the whole book,
        # or the verdict derived for the whole book,
        # on the pure layer parser + formatters. This
        # road measures nothing live, reads no live
        # model, context, cost, crew or sandbox state,
        # binds no key, opens no panel, sends nothing,
        # posts nothing, schedules nothing, persists
        # nothing, renders no live UI and rebuilds no
        # live screen - a fact held here is a finding,
        # never the live state of the screen it
        # describes.
        from .core.status_line import format_book as _fmt_slbook, format_fact as _fmt_slfact, format_line as _fmt_slline, format_panel as _fmt_slpanel, format_verdict as _fmt_slverdict, format_view as _fmt_slview, parse_status_line_args as _parse_sl
        try:
            _act, _tgt = _parse_sl(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "fact":
            try:
                _fact = agent.get_status_fact(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_slfact(_fact)
        if _act == "view":
            try:
                _view = agent.get_status_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_slview(_view)
        if _act == "kind":
            return True, False, _fmt_slbook(
                agent.status_line_book(), _tgt)
        if _act == "line":
            return True, False, _fmt_slline(agent.status_line_book())
        if _act == "panel":
            return True, False, _fmt_slpanel(agent.status_line_book())
        if _act == "verdict":
            return True, False, _fmt_slverdict(agent.status_line_book())
        return True, False, agent.status_line_status()["screen"]
    if command == "/themesgrownup":
        # M-179 terminal road: show the themes grown
        # up held this session - the theme system
        # judged under the Design Lawbook discipline
        # as data (the shipped example book when none
        # is held) - show one theme whole, one held
        # view record, the book themes of one mode,
        # the panel derived from the whole book, or
        # the verdict derived for the whole book, on
        # the pure layer parser + formatters. This
        # road repaints no live UI, applies no theme
        # live, measures no running screen, reads no
        # live theme, sends nothing, posts nothing,
        # schedules nothing, persists nothing and
        # renders no live UI - a theme held here is a
        # finding, never the live face of the app.
        from .core.themes_grown_up import format_book as _fmt_tgbook, format_panel as _fmt_tgpanel, format_theme as _fmt_tgtheme, format_verdict as _fmt_tgverdict, format_view as _fmt_tgview, parse_themes_grown_up_args as _parse_tg
        try:
            _act, _tgt = _parse_tg(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "theme":
            try:
                _theme = agent.get_theme_profile(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_tgtheme(_theme)
        if _act == "view":
            try:
                _view = agent.get_theme_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_tgview(_view)
        if _act == "mode":
            return True, False, _fmt_tgbook(
                agent.themes_grown_up_book(), _tgt)
        if _act == "panel":
            return True, False, _fmt_tgpanel(agent.themes_grown_up_book())
        if _act == "verdict":
            return True, False, _fmt_tgverdict(agent.themes_grown_up_book())
        return True, False, agent.themes_grown_up_status()["screen"]
    if command == "/voiceinout":
        # M-180 terminal road: show the voice in
        # and out held this session - push-to-talk
        # dictation for prompts and spoken stand-ups
        # via the existing TTS (direct catalog
        # casting, the house voice law), voice an
        # extra door and never the only door (the
        # shipped example book when none is held) -
        # show one dictation whole, one stand-up,
        # one voice action, one held view record,
        # the book items of one kind, the panel
        # derived from the whole book, or the
        # verdict derived for the whole book, on the
        # pure layer parser + formatters. This road
        # captures no live audio, builds no TTS
        # engine, speaks nothing live, sends no
        # prompt, posts nothing, schedules nothing,
        # persists nothing and renders no live
        # speech - a dictation held here is a draft,
        # never a send.
        from .core.voice_in_out import format_action as _fmt_viaction, format_book as _fmt_vibook, format_dictation as _fmt_vidictation, format_panel as _fmt_vipanel, format_standup as _fmt_vistandup, format_verdict as _fmt_viverdict, format_view as _fmt_viview, parse_voice_in_out_args as _parse_vi
        try:
            _act, _tgt = _parse_vi(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "dictation":
            try:
                _item = agent.get_dictation_session(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_vidictation(_item)
        if _act == "standup":
            try:
                _item = agent.get_spoken_standup(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_vistandup(_item)
        if _act == "action":
            try:
                _item = agent.get_voice_action(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_viaction(_item)
        if _act == "view":
            try:
                _view = agent.get_voice_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_viview(_view)
        if _act == "kind":
            return True, False, _fmt_vibook(
                agent.voice_in_out_book(), _tgt)
        if _act == "panel":
            return True, False, _fmt_vipanel(agent.voice_in_out_book())
        if _act == "verdict":
            return True, False, _fmt_viverdict(agent.voice_in_out_book())
        return True, False, agent.voice_in_out_status()["screen"]

    if command == "/manners":
        # M-181 terminal road: show the
        # notifications manners held this session -
        # long jobs announce completion (terminal
        # bell/OS notification, once), failures
        # announce once with the one action that
        # matters, and silence is the default posture
        # (the shipped example book when none is
        # held) - show one job whole, one channel,
        # one manners rule, one held view record, the
        # book items of one kind, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer
        # parser + formatters. This road rings no
        # bell, posts no notification, schedules
        # nothing and persists nothing - announcements
        # travel the agent's announce road alone.
        from .core.notifications_manners import format_book as _fmt_nmbook, format_channel as _fmt_nmchannel, format_job as _fmt_nmjob, format_panel as _fmt_nmpanel, format_rule as _fmt_nmrule, format_verdict as _fmt_nmverdict, format_view as _fmt_nmview, parse_notifications_manners_args as _parse_nm
        try:
            _act, _tgt = _parse_nm(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "job":
            try:
                _item = agent.get_job_notice(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_nmjob(_item)
        if _act == "channel":
            try:
                _item = agent.get_channel_notice(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_nmchannel(_item)
        if _act == "rule":
            try:
                _item = agent.get_manners_rule(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_nmrule(_item)
        if _act == "view":
            try:
                _view = agent.get_notifications_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_nmview(_view)
        if _act == "kind":
            return True, False, _fmt_nmbook(
                agent.notifications_manners_book(), _tgt)
        if _act == "panel":
            return True, False, _fmt_nmpanel(agent.notifications_manners_book())
        if _act == "verdict":
            return True, False, _fmt_nmverdict(agent.notifications_manners_book())
        return True, False, agent.notifications_manners_status()["screen"]

    if command == "/skin":
        # M-182 terminal road: show the plain-
        # language skin held this session - reports,
        # approvals and stand-ups in plain everyday
        # words in Jarl mode, technical detail folded
        # behind the unfold keypress (the shipped
        # example book when none is held) - show one
        # report whole, one approval ask, one stand-up,
        # one lexicon term, one held view record, the
        # book items of one kind, the panel derived
        # from the whole book, the verdict derived for
        # the whole book, one item unfolded whole, or
        # the register the session stands in, on the
        # pure layer parser + formatters. This road
        # approves nothing, sends nothing, schedules
        # nothing and persists nothing - rendering and
        # unfolding are words only.
        from .core.plain_language_skin import format_approval as _fmt_skapproval, format_book as _fmt_skbook, format_panel as _fmt_skpanel, format_report as _fmt_skreport, format_standup as _fmt_skstandup, format_term as _fmt_skterm, format_verdict as _fmt_skverdict, format_view as _fmt_skview, parse_plain_language_skin_args as _parse_sk
        try:
            _act, _tgt = _parse_sk(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "report":
            try:
                _item = agent.get_skin_report(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_skreport(
                _item, agent.plain_language_skin_book())
        if _act == "approval":
            try:
                _item = agent.get_skin_approval(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_skapproval(
                _item, agent.plain_language_skin_book())
        if _act == "standup":
            try:
                _item = agent.get_skin_standup(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_skstandup(
                _item, agent.plain_language_skin_book())
        if _act == "term":
            try:
                _item = agent.get_skin_term(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_skterm(_item)
        if _act == "view":
            try:
                _view = agent.get_skin_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_skview(_view)
        if _act == "kind":
            return True, False, _fmt_skbook(
                agent.plain_language_skin_book(), _tgt)
        if _act == "panel":
            return True, False, _fmt_skpanel(agent.plain_language_skin_book())
        if _act == "verdict":
            return True, False, _fmt_skverdict(agent.plain_language_skin_book())
        if _act == "unfold":
            try:
                _res = agent.unfold_plain_language_skin_item(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _res["text"]
        if _act == "register":
            return True, False, (
                "Register: " + agent.plain_language_skin_register())
        return True, False, agent.plain_language_skin_status()["screen"]

    if command == "/errors":
        # M-183 terminal road: show the error book
        # held this session - every error told in
        # plain words, what happened, what it means
        # and the most likely fix, technical trace
        # folded behind the trace keypress, no raw
        # stack ever landing unaccompanied (the
        # shipped example book when none is held) -
        # show one error whole, one error's trace
        # unfolded whole, one held view record, the
        # book errors of one kind, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser
        # + formatters. This road fixes nothing, sends
        # nothing, schedules nothing and persists
        # nothing - telling and unfolding are words
        # only.
        from .core.error_kindness import format_book as _fmt_ekbook, format_error as _fmt_ekerror, format_panel as _fmt_ekpanel, format_verdict as _fmt_ekverdict, format_view as _fmt_ekview, parse_error_kindness_args as _parse_ek
        try:
            _act, _tgt = _parse_ek(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "error":
            try:
                _item = agent.get_kindness_error(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_ekerror(_item)
        if _act == "trace":
            try:
                _res = agent.trace_error_kindness_error(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _res["text"]
        if _act == "view":
            try:
                _view = agent.get_kindness_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_ekview(_view)
        if _act == "kind":
            return True, False, _fmt_ekbook(
                agent.error_kindness_book(), _tgt)
        if _act == "panel":
            return True, False, _fmt_ekpanel(agent.error_kindness_book())
        if _act == "verdict":
            return True, False, _fmt_ekverdict(agent.error_kindness_book())
        return True, False, agent.error_kindness_status()["screen"]

    if command == "/onboard":
        # M-184 terminal road: show the onboarding
        # book held this session - the first run held
        # as data: providers detected by named probes,
        # found or absent and never faked, Kista
        # key-keeping offered as data, one tiny real
        # task walked in held steps, success before
        # configuration, always (the shipped example
        # book when none is held) - show one detection
        # whole, the walk in held order, one Kista
        # offer, one held view record, the book
        # detections of one outcome, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser
        # + formatters. This road detects nothing
        # live, keeps no key, runs no task, configures
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.onboarding_five import format_book as _fmt_obbook, format_detection as _fmt_obdet, format_offer as _fmt_oboffer, format_panel as _fmt_obpanel, format_verdict as _fmt_obverdict, format_view as _fmt_obview, format_walk as _fmt_obwalk, parse_onboarding_args as _parse_ob
        try:
            _act, _tgt = _parse_ob(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "detection":
            try:
                _item = agent.get_onboarding_detection(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_obdet(_item)
        if _act == "walk":
            return True, False, _fmt_obwalk(agent.onboarding_five_book())
        if _act == "offer":
            try:
                _offer = agent.get_onboarding_offer(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_oboffer(_offer)
        if _act == "view":
            try:
                _view = agent.get_onboarding_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_obview(_view)
        if _act == "outcome":
            return True, False, _fmt_obbook(
                agent.onboarding_five_book(), _tgt)
        if _act == "panel":
            return True, False, _fmt_obpanel(agent.onboarding_five_book())
        if _act == "verdict":
            return True, False, _fmt_obverdict(agent.onboarding_five_book())
        return True, False, agent.onboarding_five_status()["screen"]

    if command == "/lessons":
        # M-185 terminal road: show the tutorial
        # book held this session - the grown tutorial
        # held as data: interactive lessons per feature
        # family, ready or blocked and never faked, the
        # scratch repo a lesson runs inside held as
        # data, the play in held steps under the
        # scratch-repo rule (the shipped example book
        # when none is held) - show one lesson whole,
        # the play in held order, one scratch repo, one
        # held view record, the book lessons of one
        # readiness, the panel derived from the whole
        # book, or the verdict derived for the whole
        # book, on the pure layer parser + formatters.
        # This road runs no lesson, opens no repo,
        # writes nothing to any real workspace and
        # persists nothing - holding and telling are
        # words only.
        from .core.tutorial_grown import format_book as _fmt_tgbook, format_lesson as _fmt_tglesson, format_scratch as _fmt_tgscratch, format_panel as _fmt_tgpanel, format_verdict as _fmt_tgverdict, format_view as _fmt_tgview, format_play as _fmt_tgplay, parse_tutorial_args as _parse_tg
        try:
            _act, _tgt = _parse_tg(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "lesson":
            try:
                _item = agent.get_tutorial_lesson(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_tglesson(_item)
        if _act == "play":
            return True, False, _fmt_tgplay(agent.tutorial_grown_book())
        if _act == "scratch":
            try:
                _scratch = agent.get_tutorial_scratch(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_tgscratch(_scratch)
        if _act == "view":
            try:
                _view = agent.get_tutorial_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_tgview(_view)
        if _act == "readiness":
            return True, False, _fmt_tgbook(
                agent.tutorial_grown_book(), _tgt)
        if _act == "panel":
            return True, False, _fmt_tgpanel(agent.tutorial_grown_book())
        if _act == "verdict":
            return True, False, _fmt_tgverdict(agent.tutorial_grown_book())
        return True, False, agent.tutorial_grown_status()["screen"]

    if command == "/helpask":
        # M-186 terminal road: show the help book held
        # this session - help that answers held as data:
        # one help entry per screen, the local docs the
        # question box answers from, current or stale
        # and stale never answering (the shipped example
        # book when none is held) - show one doc whole,
        # answer one question from the held docs alone,
        # show one screen's held help or name it
        # uncovered, one held view record, the book docs
        # of one standing, the panel derived from the
        # whole book, the verdict derived for the whole
        # book, or the screen coverage, on the pure
        # layer parser + formatters. This road searches
        # nothing live, calls no model, opens no network
        # and persists nothing - holding and telling are
        # words only.
        from .core.help_answers import format_answer as _fmt_habook_answer, format_book as _fmt_habook, format_coverage as _fmt_hacoverage, format_doc as _fmt_hadoc, format_panel as _fmt_hapanel, format_screen as _fmt_hascreen, format_verdict as _fmt_haverdict, format_view as _fmt_haview, parse_help_args as _parse_ha
        try:
            _act, _tgt = _parse_ha(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "doc":
            try:
                _item = agent.get_help_doc(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_hadoc(_item)
        if _act == "ask":
            return True, False, _fmt_habook_answer(
                agent.help_answers_book(), _tgt)
        if _act == "screen":
            try:
                return True, False, _fmt_hascreen(
                    agent.help_answers_book(), _tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
        if _act == "view":
            try:
                _view = agent.get_help_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_haview(_view)
        if _act == "standing":
            return True, False, _fmt_habook(
                agent.help_answers_book(), _tgt)
        if _act == "panel":
            return True, False, _fmt_hapanel(agent.help_answers_book())
        if _act == "verdict":
            return True, False, _fmt_haverdict(agent.help_answers_book())
        if _act == "coverage":
            return True, False, _fmt_hacoverage(agent.help_answers_book())
        return True, False, agent.help_answers_status()["screen"]

    if command == "/keymap":
        # M-187 terminal road: show the keymap book
        # held this session - keyboard sovereignty
        # held as data: one record per act with the
        # key that reaches it, an act naming no key
        # standing unreachable, and the vim-mode
        # prompt option held as data (the shipped
        # example book when none is held) - show one
        # act whole, the act one key reaches, the
        # acts of one area, one held view record, one
        # held mode record, the keymap printed from
        # the whole book, the panel derived from the
        # whole book, or the verdict derived for the
        # whole book, on the pure layer parser +
        # formatters. This road presses no keys,
        # renders no live UI, changes no prompt mode
        # and persists nothing - holding and telling
        # are words only.
        from .core.keyboard_sovereignty import format_act as _fmt_kbact, format_book as _fmt_kbbook, format_key as _fmt_kbkey, format_keymap as _fmt_kbkeymap, format_mode as _fmt_kbmode, format_panel as _fmt_kbpanel, format_verdict as _fmt_kbverdict, format_view as _fmt_kbview, parse_keyboard_args as _parse_kb
        try:
            _act, _tgt = _parse_kb(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "act":
            try:
                _item = agent.get_keyboard_act(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_kbact(_item)
        if _act == "key":
            return True, False, _fmt_kbkey(
                agent.keyboard_sovereignty_book(), _tgt)
        if _act == "area":
            return True, False, _fmt_kbbook(
                agent.keyboard_sovereignty_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_keyboard_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_kbview(_view)
        if _act == "mode":
            try:
                _mode = agent.keyboard_sovereignty_book().mode_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_kbmode(_mode)
        if _act == "print":
            return True, False, _fmt_kbkeymap(agent.keyboard_sovereignty_book())
        if _act == "panel":
            return True, False, _fmt_kbpanel(agent.keyboard_sovereignty_book())
        if _act == "verdict":
            return True, False, _fmt_kbverdict(agent.keyboard_sovereignty_book())
        return True, False, agent.keyboard_sovereignty_status()["screen"]

    if command == "/mouse":
        # M-188 terminal road: show the mouse book
        # held this session - mouse manners held as
        # data: one record per gesture with the mouse
        # road that reaches it, a gesture naming no
        # road standing unwired, and the file links
        # held as data beside them (the shipped
        # example book when none is held) - show one
        # gesture whole, the gesture one road reaches,
        # the gestures of one area, one held view
        # record, one held link record, the guide
        # derived from the whole book, the panel
        # derived from the whole book, or the verdict
        # derived for the whole book, on the pure
        # layer parser + formatters. This road moves
        # no pointer, renders no live UI, opens no
        # file and persists nothing - holding and
        # telling are words only.
        from .core.mouse_manners import format_gesture as _fmt_mmg, format_book as _fmt_mmbook, format_road as _fmt_mmroad, format_guide as _fmt_mmguide, format_link as _fmt_mmlink, format_panel as _fmt_mmpanel, format_verdict as _fmt_mmverdict, format_view as _fmt_mmview, parse_mouse_args as _parse_mm
        try:
            _act, _tgt = _parse_mm(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "gesture":
            try:
                _item = agent.get_mouse_gesture(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_mmg(_item)
        if _act == "road":
            return True, False, _fmt_mmroad(
                agent.mouse_manners_book(), _tgt)
        if _act == "area":
            return True, False, _fmt_mmbook(
                agent.mouse_manners_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_mouse_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_mmview(_view)
        if _act == "link":
            try:
                _link = agent.mouse_manners_book().link_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_mmlink(_link)
        if _act == "guide":
            return True, False, _fmt_mmguide(agent.mouse_manners_book())
        if _act == "panel":
            return True, False, _fmt_mmpanel(agent.mouse_manners_book())
        if _act == "verdict":
            return True, False, _fmt_mmverdict(agent.mouse_manners_book())
        return True, False, agent.mouse_manners_status()["screen"]

    if command == "/gallery":
        # M-189 terminal road: show the gallery book
        # held this session - session gallery held as
        # data: one record per card with the gallery
        # road that reaches it, a card naming no
        # road standing unwired, and the file actions
        # held as data beside them (the shipped
        # example book when none is held) - show one
        # card whole, the card one road reaches,
        # the cards of one outcome, one held view
        # record, one held action record, the index
        # derived from the whole book, the panel
        # derived from the whole book, or the verdict
        # derived for the whole book, on the pure
        # layer parser + formatters. This road moves
        # no pointer, renders no live UI, opens no
        # file and persists nothing - holding and
        # telling are words only.
        from .core.session_gallery import format_card as _fmt_sgg, format_book as _fmt_sgbook, format_road as _fmt_sgroad, format_index as _fmt_sgindex, format_action as _fmt_sgaction, format_panel as _fmt_sgpanel, format_verdict as _fmt_sgverdict, format_view as _fmt_sgview, parse_gallery_args as _parse_mm
        try:
            _act, _tgt = _parse_mm(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "card":
            try:
                _item = agent.get_gallery_card(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_sgg(_item)
        if _act == "road":
            return True, False, _fmt_sgroad(
                agent.session_gallery_book(), _tgt)
        if _act == "outcome":
            return True, False, _fmt_sgbook(
                agent.session_gallery_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_gallery_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_sgview(_view)
        if _act == "action":
            try:
                _action = agent.session_gallery_book().action_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_sgaction(_action)
        if _act == "index":
            return True, False, _fmt_sgindex(agent.session_gallery_book())
        if _act == "panel":
            return True, False, _fmt_sgpanel(agent.session_gallery_book())
        if _act == "verdict":
            return True, False, _fmt_sgverdict(agent.session_gallery_book())
        return True, False, agent.session_gallery_status()["screen"]

    if command == "/costs":
        # M-190 terminal budget: show the costs book
        # held this session - costs face held as
        # data: one record per line with the costs
        # budget that reaches it, a line naming no
        # budget standing unwired, and the file warnings
        # held as data beside them (the shipped
        # example book when none is held) - show one
        # line whole, the line one budget reaches,
        # the lines of one scope, one held view
        # record, one held warning record, the index
        # derived from the whole book, the panel
        # derived from the whole book, or the verdict
        # derived for the whole book, on the pure
        # layer parser + formatters. This budget moves
        # no pointer, renders no live UI, opens no
        # file and persists nothing - holding and
        # telling are words only.
        from .core.costs_face import format_line as _fmt_sgg, format_book as _fmt_sgbook, format_budget as _fmt_sgbudget, format_index as _fmt_sgindex, format_warning as _fmt_sgwarning, format_panel as _fmt_sgpanel, format_verdict as _fmt_sgverdict, format_view as _fmt_sgview, parse_costs_args as _parse_mm
        try:
            _act, _tgt = _parse_mm(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "line":
            try:
                _item = agent.get_costs_line(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_sgg(_item)
        if _act == "budget":
            return True, False, _fmt_sgbudget(
                agent.costs_face_book(), _tgt)
        if _act == "scope":
            return True, False, _fmt_sgbook(
                agent.costs_face_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_costs_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_sgview(_view)
        if _act == "warning":
            try:
                _warning = agent.costs_face_book().warning_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_sgwarning(_warning)
        if _act == "index":
            return True, False, _fmt_sgindex(agent.costs_face_book())
        if _act == "panel":
            return True, False, _fmt_sgpanel(agent.costs_face_book())
        if _act == "verdict":
            return True, False, _fmt_sgverdict(agent.costs_face_book())
        return True, False, agent.costs_face_status()["screen"]


    if command == "/theatre":
        # M-191 terminal target: show the theatre book
        # held this session - session theatre held as
        # data: one record per hunk with the theatre
        # target that reaches it, a hunk naming no
        # target standing unwired, and the file comments
        # held as data beside them (the shipped
        # example book when none is held) - show one
        # hunk whole, the hunk one target reaches,
        # the hunks of one kind, one held view
        # record, one held stance record, the index
        # derived from the whole book, the panel
        # derived from the whole book, or the verdict
        # derived for the whole book, on the pure
        # layer parser + formatters. This target moves
        # no pointer, renders no live UI, opens no
        # file and persists nothing - holding and
        # telling are words only.
        from .core.diff_theatre_final import format_hunk as _fmt_sgg, format_book as _fmt_sgbook, format_target as _fmt_sgtarget, format_index as _fmt_sgindex, format_comment as _fmt_sgcomment, format_panel as _fmt_sgpanel, format_verdict as _fmt_sgverdict, format_view as _fmt_sgview, parse_theatre_args as _parse_mm
        try:
            _act, _tgt = _parse_mm(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "hunk":
            try:
                _item = agent.get_theatre_hunk(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_sgg(_item)
        if _act == "target":
            return True, False, _fmt_sgtarget(
                agent.diff_theatre_final_book(), _tgt)
        if _act == "kind":
            return True, False, _fmt_sgbook(
                agent.diff_theatre_final_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_theatre_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_sgview(_view)
        if _act == "comment":
            try:
                _comment = agent.diff_theatre_final_book().comment_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_sgcomment(_comment)
        if _act == "index":
            return True, False, _fmt_sgindex(agent.diff_theatre_final_book())
        if _act == "panel":
            return True, False, _fmt_sgpanel(agent.diff_theatre_final_book())
        if _act == "verdict":
            return True, False, _fmt_sgverdict(agent.diff_theatre_final_book())
        return True, False, agent.diff_theatre_final_status()["screen"]

    if command == "/panes":
        # M-192 terminal target: show the pane book
        # held this session - session pane held as
        # data: one record per pane with the pane
        # target that reaches it, a pane naming no
        # target standing unwired, and the file notes
        # held as data beside them (the shipped
        # example book when none is held) - show one
        # pane whole, the pane one target reaches,
        # the panes of one kind, one held layout
        # record, one held stance record, the index
        # derived from the whole book, the panel
        # derived from the whole book, or the verdict
        # derived for the whole book, on the pure
        # layer parser + formatters. This target moves
        # no pointer, renders no live UI, opens no
        # file and persists nothing - holding and
        # telling are words only.
        from .core.multi_pane import format_pane as _fmt_mpg, format_book as _fmt_mpbook, format_target as _fmt_mptarget, format_index as _fmt_mpindex, format_note as _fmt_mpnote, format_panel as _fmt_mppanel, format_verdict as _fmt_mpverdict, format_layout as _fmt_mplayout, parse_pane_args as _parse_mp
        try:
            _act, _tgt = _parse_mp(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "pane":
            try:
                _item = agent.get_pane_pane(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_mpg(_item)
        if _act == "target":
            return True, False, _fmt_mptarget(
                agent.multi_pane_book(), _tgt)
        if _act == "kind":
            return True, False, _fmt_mpbook(
                agent.multi_pane_book(), _tgt)
        if _act == "layout":
            try:
                _layout = agent.get_pane_layout(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_mplayout(_layout)
        if _act == "note":
            try:
                _note = agent.multi_pane_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_mpnote(_note)
        if _act == "index":
            return True, False, _fmt_mpindex(agent.multi_pane_book())
        if _act == "panel":
            return True, False, _fmt_mppanel(agent.multi_pane_book())
        if _act == "verdict":
            return True, False, _fmt_mpverdict(agent.multi_pane_book())
        return True, False, agent.multi_pane_status()["screen"]

    if command == "/ceremony":
        # M-193 terminal target: show the moment book
        # held this session - session moment held as
        # data: one record per moment with the moment
        # target that reaches it, a moment naming no
        # target standing unwired, and the file notes
        # held as data beside them (the shipped
        # example book when none is held) - show one
        # moment whole, the moment one target reaches,
        # the moments of one kind, one held view
        # record, one held stance record, the index
        # derived from the whole book, the panel
        # derived from the whole book, or the verdict
        # derived for the whole book, on the pure
        # layer parser + formatters. This target moves
        # no pointer, renders no live UI, opens no
        # file and persists nothing - holding and
        # telling are words only.
        from .core.splash_ceremony import format_moment as _fmt_scg, format_book as _fmt_scbook, format_alternative as _fmt_sctarget, format_index as _fmt_scindex, format_note as _fmt_scnote, format_panel as _fmt_scpanel, format_verdict as _fmt_scverdict, format_view as _fmt_scview, parse_ceremony_args as _parse_sc
        try:
            _act, _tgt = _parse_sc(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "moment":
            try:
                _item = agent.get_ceremony_moment(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_scg(_item)
        if _act == "alternative":
            return True, False, _fmt_sctarget(
                agent.splash_ceremony_book(), _tgt)
        if _act == "kind":
            return True, False, _fmt_scbook(
                agent.splash_ceremony_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_ceremony_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_scview(_view)
        if _act == "note":
            try:
                _note = agent.splash_ceremony_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_scnote(_note)
        if _act == "index":
            return True, False, _fmt_scindex(agent.splash_ceremony_book())
        if _act == "panel":
            return True, False, _fmt_scpanel(agent.splash_ceremony_book())
        if _act == "verdict":
            return True, False, _fmt_scverdict(agent.splash_ceremony_book())
        return True, False, agent.splash_ceremony_status()["screen"]

    if command == "/smallterminal":
        # M-194 terminal target: show the fold book
        # held this session - session fold held as
        # data: one record per fold with the fold
        # target that reaches it, a fold naming no
        # target standing unwired, and the file notes
        # held as data beside them (the shipped
        # example book when none is held) - show one
        # fold whole, the fold one target reaches,
        # the folds of one kind, one held view
        # record, one held stance record, the index
        # derived from the whole book, the panel
        # derived from the whole book, or the verdict
        # derived for the whole book, on the pure
        # layer parser + formatters. This target moves
        # no pointer, renders no live UI, opens no
        # file and persists nothing - holding and
        # telling are words only.
        from .core.small_terminal_grace import format_fold as _fmt_scg, format_book as _fmt_scbook, format_preserves as _fmt_sctarget, format_index as _fmt_scindex, format_note as _fmt_scnote, format_panel as _fmt_scpanel, format_verdict as _fmt_scverdict, format_view as _fmt_scview, parse_grace_args as _parse_sc
        try:
            _act, _tgt = _parse_sc(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "fold":
            try:
                _item = agent.get_grace_fold(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_scg(_item)
        if _act == "preserves":
            return True, False, _fmt_sctarget(
                agent.small_terminal_grace_book(), _tgt)
        if _act == "kind":
            return True, False, _fmt_scbook(
                agent.small_terminal_grace_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_grace_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_scview(_view)
        if _act == "note":
            try:
                _note = agent.small_terminal_grace_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_scnote(_note)
        if _act == "index":
            return True, False, _fmt_scindex(agent.small_terminal_grace_book())
        if _act == "panel":
            return True, False, _fmt_scpanel(agent.small_terminal_grace_book())
        if _act == "verdict":
            return True, False, _fmt_scverdict(agent.small_terminal_grace_book())
        return True, False, agent.small_terminal_grace_status()["screen"]

    if command == "/copyshare":
        # M-195 terminal target: show the clip book
        # held this session - session clip held as
        # data: one record per clip with the clip
        # target that reaches it, a clip naming no
        # target standing unwired, and the file notes
        # held as data beside them (the shipped
        # example book when none is held) - show one
        # clip whole, the clip one target reaches,
        # the clips of one kind, one held view
        # record, one held stance record, the index
        # derived from the whole book, the panel
        # derived from the whole book, or the verdict
        # derived for the whole book, on the pure
        # layer parser + formatters. This target moves
        # no pointer, renders no live UI, opens no
        # file and persists nothing - holding and
        # telling are words only.
        from .core.copy_share import format_clip as _fmt_scg, format_book as _fmt_scbook, format_markdown as _fmt_sctarget, format_index as _fmt_scindex, format_note as _fmt_scnote, format_panel as _fmt_scpanel, format_verdict as _fmt_scverdict, format_view as _fmt_scview, parse_share_args as _parse_sc
        try:
            _act, _tgt = _parse_sc(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "clip":
            try:
                _item = agent.get_share_clip(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_scg(_item)
        if _act == "markdown":
            return True, False, _fmt_sctarget(
                agent.copy_share_book(), _tgt)
        if _act == "kind":
            return True, False, _fmt_scbook(
                agent.copy_share_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_share_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_scview(_view)
        if _act == "note":
            try:
                _note = agent.copy_share_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_scnote(_note)
        if _act == "index":
            return True, False, _fmt_scindex(agent.copy_share_book())
        if _act == "panel":
            return True, False, _fmt_scpanel(agent.copy_share_book())
        if _act == "verdict":
            return True, False, _fmt_scverdict(agent.copy_share_book())
        return True, False, agent.copy_share_status()["screen"]

    if command == "/settingsroom":
        # M-196 terminal target: show the settings book
        # held this session - the settings room held as
        # data: one record per setting with the setting
        # meaning that reaches it, a setting naming no
        # meaning standing incomplete, and the notes
        # held as data beside them (the shipped
        # example book when none is held) - show one
        # setting whole, the setting one meaning reaches,
        # the settings of one section, one held view
        # record, one held stance record, the index
        # derived from the whole book, the panel
        # derived from the whole book, or the verdict
        # derived for the whole book, on the pure
        # layer parser + formatters. This target changes
        # no setting, applies nothing, writes no
        # config and persists nothing - holding and
        # telling are words only.
        from .core.settings_room import format_setting as _fmt_rg, format_book as _fmt_rbook, format_meaning as _fmt_rtarget, format_index as _fmt_rindex, format_note as _fmt_rnote, format_panel as _fmt_rpanel, format_verdict as _fmt_rverdict, format_view as _fmt_rview, parse_room_args as _parse_r
        try:
            _act, _tgt = _parse_r(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "setting":
            try:
                _item = agent.get_room_setting(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_rg(_item)
        if _act == "meaning":
            return True, False, _fmt_rtarget(
                agent.settings_room_book(), _tgt)
        if _act == "section":
            return True, False, _fmt_rbook(
                agent.settings_room_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_room_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_rview(_view)
        if _act == "note":
            try:
                _note = agent.settings_room_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_rnote(_note)
        if _act == "index":
            return True, False, _fmt_rindex(agent.settings_room_book())
        if _act == "panel":
            return True, False, _fmt_rpanel(agent.settings_room_book())
        if _act == "verdict":
            return True, False, _fmt_rverdict(agent.settings_room_book())
        return True, False, agent.settings_room_status()["screen"]

    if command == "/commandpalette":
        # M-197 terminal target: show the palette book
        # held this session - the command palette held as
        # data: one record per entry with the entry
        # words that reach it, an entry naming no
        # words standing incomplete, and the notes
        # held as data beside them (the shipped
        # example book when none is held) - show one
        # entry whole, the entry one set of words reaches,
        # the entries of one kind, one held view
        # record, one held stance record, the index
        # derived from the whole book, the panel
        # derived from the whole book, or the verdict
        # derived for the whole book, on the pure
        # layer parser + formatters. This target executes
        # no command, runs no action, navigates
        # nowhere and persists nothing - holding and
        # telling are words only.
        from .core.command_palette import format_entry as _fmt_pg, format_book as _fmt_pbook, format_keywords as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_palette_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "entry":
            try:
                _item = agent.get_palette_entry(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item)
        if _act == "keywords":
            return True, False, _fmt_ptarget(
                agent.command_palette_book(), _tgt)
        if _act == "kind":
            return True, False, _fmt_pbook(
                agent.command_palette_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_palette_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.command_palette_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.command_palette_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.command_palette_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.command_palette_book())
        return True, False, agent.command_palette_status()["screen"]


    if command == "/uiundo":
        # M-198 terminal target: show the undo book
        # held this session - the command undo held as
        # data: one record per pane with the pane
        # words that reach it, an pane naming no
        # words standing incomplete, and the notes
        # held as data beside them (the shipped
        # example book when none is held) - show one
        # pane whole, the pane one set of words reaches,
        # the panes of one kind, one held view
        # record, one held stance record, the index
        # derived from the whole book, the panel
        # derived from the whole book, or the verdict
        # derived for the whole book, on the pure
        # layer parser + formatters. This target executes
        # no command, runs no action, navigates
        # nowhere and persists nothing - holding and
        # telling are words only.
        from .core.ui_undo import format_pane as _fmt_pg, format_book as _fmt_pbook, format_state as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_undo_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "pane":
            try:
                _item = agent.get_undo_pane(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item)
        if _act == "state":
            return True, False, _fmt_ptarget(
                agent.ui_undo_book(), _tgt)
        if _act == "kind":
            return True, False, _fmt_pbook(
                agent.ui_undo_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_undo_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.ui_undo_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.ui_undo_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.ui_undo_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.ui_undo_book())
        return True, False, agent.ui_undo_status()["screen"]




    if command == "/accessverify":
        # M-199 terminal target: show the verification book
        # held this session - the accessibility verification held as
        # data: one record per gate with the gate
        # words that reach it, an gate naming no
        # words standing incomplete, and the notes
        # held as data beside them (the shipped
        # example book when none is held) - show one
        # gate whole, the gate one set of words reaches,
        # the gates of one kind, one held view
        # record, one held stance record, the index
        # derived from the whole book, the panel
        # derived from the whole book, or the verdict
        # derived for the whole book, on the pure
        # layer parser + formatters. This target executes
        # no command, runs no action, navigates
        # nowhere and persists nothing - holding and
        # telling are words only.
        from .core.accessibility_verification import format_gate as _fmt_pg, format_book as _fmt_pbook, format_evidence as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_verify_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "gate":
            try:
                _item = agent.get_verify_gate(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item)
        if _act == "evidence":
            return True, False, _fmt_ptarget(
                agent.access_verify_book(), _tgt)
        if _act == "kind":
            return True, False, _fmt_pbook(
                agent.access_verify_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_verify_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.access_verify_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.access_verify_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.access_verify_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.access_verify_book())
        return True, False, agent.access_verify_status()["screen"]



    if command == "/campaigns":
        # M-201 terminal target: show the campaign book
        # held this session - campaigns as data: one
        # record per slice, held whole with its title,
        # the part it stands in, its state, its evidence
        # held honestly and the acceptance checks it
        # carries, and the notes held as data beside
        # them (the shipped example book when none is
        # held) - show one slice whole, the slice one
        # checks line reaches, the slices of one state,
        # one held view record, one held stance record,
        # the index derived from the whole book, the
        # panel derived from the whole book, or the
        # verdict derived for the whole book, on the
        # pure layer parser + formatters. This target
        # executes no campaign, runs nothing, banks
        # nothing, pushes nothing and persists nothing
        # - holding and telling are words only.
        from .core.campaigns import format_slice as _fmt_pg, format_book as _fmt_pbook, format_checks as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_campaign_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "slice":
            try:
                _item = agent.get_campaign_slice(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item)
        if _act == "checks":
            return True, False, _fmt_ptarget(
                agent.campaigns_book(), _tgt)
        if _act == "state":
            return True, False, _fmt_pbook(
                agent.campaigns_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_campaign_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.campaigns_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.campaigns_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.campaigns_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.campaigns_book())
        return True, False, agent.campaigns_status()["screen"]
    if command == "/intent":
        # M-202 terminal target: show the intent book
        # held this session - intents as data: one
        # record per slice, held whole with its title,
        # the part it stands in, its state, its evidence
        # held honestly and the acceptance checks it
        # carries, and the notes held as data beside
        # them (the shipped example book when none is
        # held) - show one slice whole, the slice one
        # checks line reaches, the slices of one state,
        # one held view record, one held stance record,
        # the index derived from the whole book, the
        # panel derived from the whole book, or the
        # verdict derived for the whole book, on the
        # pure layer parser + formatters. This target
        # executes no intent, runs nothing, banks
        # nothing, pushes nothing and persists nothing
        # - holding and telling are words only.
        from .core.intent_capture import format_intent as _fmt_pg, format_book as _fmt_pbook, format_citation as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_intent_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "intent":
            try:
                _item = agent.get_intent(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item)
        if _act == "citation":
            return True, False, _fmt_ptarget(
                agent.intent_book(), _tgt)
        if _act == "project":
            return True, False, _fmt_pbook(
                agent.intent_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_intent_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.intent_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.intent_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.intent_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.intent_book())
        return True, False, agent.intent_status()["screen"]
    if command == "/slicing":
        # M-203 terminal target: show the slicing book
        # held this session - draft slices as data: one
        # record per draft, held whole with the approved
        # intent it was drafted from, its one verifiable
        # outcome at the house grain and its dependencies,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one draft whole, the draft one outcome line
        # reaches, the drafts of one intent, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no slice,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.slicing_engine import format_draft as _fmt_pg, format_book as _fmt_pbook, format_outcome as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_slicing_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "draft":
            try:
                _item = agent.get_slicing_draft(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.slicing_book())
        if _act == "outcome":
            return True, False, _fmt_ptarget(
                agent.slicing_book(), _tgt)
        if _act == "intent":
            return True, False, _fmt_pbook(
                agent.slicing_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_slicing_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.slicing_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.slicing_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.slicing_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.slicing_book())
        return True, False, agent.slicing_status()["screen"]
    if command == "/juggernaut":
        # M-204 terminal target: show the juggernaut book
        # held this session - run slices as data: one
        # record per run, held whole with the active
        # slice it was runed from, its one verifiable
        # phase at the house grain and its questions,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one run whole, the run one phase line
        # reaches, the runs of one slice, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no slice,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.juggernaut_loop import format_run as _fmt_pg, format_book as _fmt_pbook, format_phase as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_juggernaut_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "run":
            try:
                _item = agent.get_juggernaut_run(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.juggernaut_book())
        if _act == "phase":
            return True, False, _fmt_ptarget(
                agent.juggernaut_book(), _tgt)
        if _act == "slice":
            return True, False, _fmt_pbook(
                agent.juggernaut_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_juggernaut_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.juggernaut_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.juggernaut_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.juggernaut_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.juggernaut_book())
        return True, False, agent.juggernaut_status()["screen"]
    if command == "/acceptance":
        # M-205 terminal target: show the acceptance book
        # held this session - audit slices as data: one
        # record per audit, held whole with the active
        # slice it was audited from, its one verifiable
        # check at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one audit whole, the audit one check line
        # reaches, the audits of one slice, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no slice,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.acceptance_gates import format_audit as _fmt_pg, format_book as _fmt_pbook, format_check as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_acceptance_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "audit":
            try:
                _item = agent.get_acceptance_audit(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.acceptance_book())
        if _act == "check":
            return True, False, _fmt_ptarget(
                agent.acceptance_book(), _tgt)
        if _act == "slice":
            return True, False, _fmt_pbook(
                agent.acceptance_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_acceptance_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.acceptance_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.acceptance_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.acceptance_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.acceptance_book())
        return True, False, agent.acceptance_status()["screen"]
    if command == "/banking":
        # M-206 terminal target: show the banking book
        # held this session - banking slices as data: one
        # record per banking, held whole with the active
        # slice it was bankinged from, its one verifiable
        # check at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one banking whole, the banking one check line
        # reaches, the bankings of one slice, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no slice,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.banking_discipline import format_banking as _fmt_pg, format_book as _fmt_pbook, format_check as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_banking_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "banking":
            try:
                _item = agent.get_banking_banking(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.banking_book())
        if _act == "check":
            return True, False, _fmt_ptarget(
                agent.banking_book(), _tgt)
        if _act == "slice":
            return True, False, _fmt_pbook(
                agent.banking_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_banking_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.banking_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.banking_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.banking_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.banking_book())
        return True, False, agent.banking_status()["screen"]
    if command == "/keepruntime":
        # M-207 terminal target: show the keeping book
        # held this session - keeping slices as data: one
        # record per keeping, held whole with the active
        # slice it was keepinged from, its one verifiable
        # check at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one keeping whole, the keeping one check line
        # reaches, the keepings of one slice, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no slice,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.keeper_runtime import format_keeping as _fmt_pg, format_book as _fmt_pbook, format_check as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_keeping_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "keeping":
            try:
                _item = agent.get_keeping_keeping(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.keeping_book())
        if _act == "check":
            return True, False, _fmt_ptarget(
                agent.keeping_book(), _tgt)
        if _act == "slice":
            return True, False, _fmt_pbook(
                agent.keeping_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_keeping_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.keeping_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.keeping_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.keeping_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.keeping_book())
        return True, False, agent.keeping_status()["screen"]
    if command == "/pauselines":
        # M-208 terminal target: show the pausing book
        # held this session - pausing slices as data: one
        # record per pausing, held whole with the active
        # slice it was pausinged from, its one verifiable
        # check at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one pausing whole, the pausing one check line
        # reaches, the pausings of one slice, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no slice,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.pause_lines import format_pausing as _fmt_pg, format_book as _fmt_pbook, format_check as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_pausing_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "pausing":
            try:
                _item = agent.get_pausing_pausing(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.pausing_book())
        if _act == "check":
            return True, False, _fmt_ptarget(
                agent.pausing_book(), _tgt)
        if _act == "slice":
            return True, False, _fmt_pbook(
                agent.pausing_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_pausing_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.pausing_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.pausing_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.pausing_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.pausing_book())
        return True, False, agent.pausing_status()["screen"]
    if command == "/questionlaw":
        # M-209 terminal target: show the questioning book
        # held this session - questioning slices as data: one
        # record per questioning, held whole with the active
        # slice it was questioninged from, its one verifiable
        # check at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one questioning whole, the questioning one check line
        # reaches, the questionings of one slice, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no slice,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.question_law import format_questioning as _fmt_pg, format_book as _fmt_pbook, format_check as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_questioning_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "questioning":
            try:
                _item = agent.get_questioning_questioning(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.questioning_book())
        if _act == "check":
            return True, False, _fmt_ptarget(
                agent.questioning_book(), _tgt)
        if _act == "slice":
            return True, False, _fmt_pbook(
                agent.questioning_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_questioning_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.questioning_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.questioning_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.questioning_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.questioning_book())
        return True, False, agent.questioning_status()["screen"]
    if command == "/scopesentry":
        # M-210 terminal target: show the sentry book
        # held this session - sentry slices as data: one
        # record per sentry, held whole with the active
        # slice it was sentryed from, its one verifiable
        # check at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one sentry whole, the sentry one check line
        # reaches, the sentries of one slice, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no slice,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.scope_sentry import format_sentry as _fmt_pg, format_book as _fmt_pbook, format_check as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_sentry_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "sentry":
            try:
                _item = agent.get_sentry_sentry(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.sentry_book())
        if _act == "check":
            return True, False, _fmt_ptarget(
                agent.sentry_book(), _tgt)
        if _act == "slice":
            return True, False, _fmt_pbook(
                agent.sentry_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_sentry_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.sentry_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.sentry_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.sentry_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.sentry_book())
        return True, False, agent.sentry_status()["screen"]
    if command == "/mapupkeep":
        # M-211 terminal target: show the upkeep book
        # held this session - upkeep slices as data: one
        # record per upkeep, held whole with the active
        # slice it was upkeeped from, its one verifiable
        # check at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one upkeep whole, the upkeep one check line
        # reaches, the upkeeps of one slice, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no slice,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.memory_map_upkeep import format_upkeep as _fmt_pg, format_book as _fmt_pbook, format_check as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_upkeep_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "upkeep":
            try:
                _item = agent.get_upkeep_upkeep(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.upkeep_book())
        if _act == "check":
            return True, False, _fmt_ptarget(
                agent.upkeep_book(), _tgt)
        if _act == "slice":
            return True, False, _fmt_pbook(
                agent.upkeep_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_upkeep_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.upkeep_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.upkeep_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.upkeep_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.upkeep_book())
        return True, False, agent.upkeep_status()["screen"]
    if command == "/bugrule":
        # M-212 terminal target: show the bug book
        # held this session - bug slices as data: one
        # record per bug, held whole with the active
        # slice it was buged from, its one verifiable
        # check at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one bug whole, the bug one check line
        # reaches, the bugs of one slice, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no slice,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.bug_rule import format_bug as _fmt_pg, format_book as _fmt_pbook, format_check as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_bug_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "bug":
            try:
                _item = agent.get_bug_bug(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.bug_book())
        if _act == "check":
            return True, False, _fmt_ptarget(
                agent.bug_book(), _tgt)
        if _act == "slice":
            return True, False, _fmt_pbook(
                agent.bug_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_bug_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.bug_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.bug_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.bug_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.bug_book())
        return True, False, agent.bug_status()["screen"]
    if command == "/retrospectives":
        # M-213 terminal target: show the retro book
        # held this session - retro slices as data: one
        # record per retro, held whole with the active
        # slice it was held from, its one verifiable
        # check at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one retro whole, the retro one check line
        # reaches, the retros of one slice, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no slice,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.retrospectives import format_retro as _fmt_pg, format_book as _fmt_pbook, format_check as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_retro_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "retro":
            try:
                _item = agent.get_retro_retro(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.retro_book())
        if _act == "check":
            return True, False, _fmt_ptarget(
                agent.retro_book(), _tgt)
        if _act == "slice":
            return True, False, _fmt_pbook(
                agent.retro_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_retro_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.retro_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.retro_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.retro_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.retro_book())
        return True, False, agent.retro_status()["screen"]
    if command == "/patterns":
        # M-214 terminal target: show the pattern book
        # held this session - pattern slices as data: one
        # record per pattern, held whole with the active
        # slice it was held from, its one verifiable
        # check at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one pattern whole, the pattern one check line
        # reaches, the patterns of one slice, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no slice,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.pattern_extraction import format_pattern as _fmt_pg, format_book as _fmt_pbook, format_check as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_pattern_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "pattern":
            try:
                _item = agent.get_pattern_pattern(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.pattern_book())
        if _act == "check":
            return True, False, _fmt_ptarget(
                agent.pattern_book(), _tgt)
        if _act == "slice":
            return True, False, _fmt_pbook(
                agent.pattern_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_pattern_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.pattern_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.pattern_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.pattern_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.pattern_book())
        return True, False, agent.pattern_status()["screen"]
    if command == "/estimates":
        # M-215 terminal target: show the estimate book
        # held this session - estimate slices as data: one
        # record per estimate, held whole with the active
        # slice it was held from, its one verifiable
        # check at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one estimate whole, the estimate one check line
        # reaches, the estimates of one slice, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no slice,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.estimate_honesty import format_estimate as _fmt_pg, format_book as _fmt_pbook, format_check as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_estimate_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "estimate":
            try:
                _item = agent.get_estimate_estimate(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.estimate_book())
        if _act == "check":
            return True, False, _fmt_ptarget(
                agent.estimate_book(), _tgt)
        if _act == "slice":
            return True, False, _fmt_pbook(
                agent.estimate_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_estimate_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.estimate_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.estimate_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.estimate_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.estimate_book())
        return True, False, agent.estimate_status()["screen"]
    if command == "/hall":
        # M-216 terminal target: show the campaign book
        # held this session - campaign slices as data: one
        # record per campaign, held whole with the active
        # slice it was held from, its one verifiable
        # check at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one campaign whole, the campaign one check line
        # reaches, the campaigns of one slice, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no slice,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.multi_campaign_hall import format_campaign as _fmt_pg, format_book as _fmt_pbook, format_check as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_campaign_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "campaign":
            try:
                _item = agent.get_hall_campaign(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.hall_book())
        if _act == "check":
            return True, False, _fmt_ptarget(
                agent.hall_book(), _tgt)
        if _act == "repo":
            return True, False, _fmt_pbook(
                agent.hall_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_hall_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.hall_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.hall_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.hall_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.hall_book())
        return True, False, agent.hall_status()["screen"]
    if command == "/shapes":
        # M-217 terminal target: show the template book
        # held this session - template slices as data: one
        # record per template, held whole with the active
        # slice it was held from, its one verifiable
        # check at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one template whole, the template one check line
        # reaches, the templates of one slice, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no slice,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.campaign_templates import format_template as _fmt_pg, format_book as _fmt_pbook, format_check as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_template_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "template":
            try:
                _item = agent.get_shape_template(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.shape_book())
        if _act == "check":
            return True, False, _fmt_ptarget(
                agent.shape_book(), _tgt)
        if _act == "kind":
            return True, False, _fmt_pbook(
                agent.shape_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_shape_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.shape_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.shape_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.shape_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.shape_book())
        return True, False, agent.shape_status()["screen"]
    if command == "/mimis":
        # M-218 terminal target: show the road book
        # held this session - road slices as data: one
        # record per road, held whole with the active
        # slice it was held from, its one verifiable
        # check at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one road whole, the road one check line
        # reaches, the roads of one slice, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no slice,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.mimisbrunnr_road import format_road as _fmt_pg, format_book as _fmt_pbook, format_check as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_road_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "road":
            try:
                _item = agent.get_mimis_road(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.mimis_book())
        if _act == "check":
            return True, False, _fmt_ptarget(
                agent.mimis_book(), _tgt)
        if _act == "concordance":
            return True, False, _fmt_pbook(
                agent.mimis_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_mimis_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.mimis_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.mimis_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.mimis_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.mimis_book())
        return True, False, agent.mimis_status()["screen"]
    if command == "/resumes":
        # M-219 terminal target: show the resume book
        # held this session - resume slices as data: one
        # record per resume, held whole with the active
        # slice it was held from, its one verifiable
        # check at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one resume whole, the resume one check line
        # reaches, the resumes of one slice, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no slice,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.interrupts_resumes import format_resume as _fmt_pg, format_book as _fmt_pbook, format_check as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_resume_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "resume":
            try:
                _item = agent.get_daybook_resume(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.daybook_book())
        if _act == "check":
            return True, False, _fmt_ptarget(
                agent.daybook_book(), _tgt)
        if _act == "pause":
            return True, False, _fmt_pbook(
                agent.daybook_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_daybook_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.daybook_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.daybook_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.daybook_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.daybook_book())
        return True, False, agent.daybook_status()["screen"]
    if command == "/milestones":
        # M-220 terminal target: show the report book
        # held this session - report slices as data: one
        # record per report, held whole with the active
        # slice it was held from, its one verifiable
        # check at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one report whole, the report one check line
        # reaches, the reports of one slice, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no slice,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.milestone_reports import format_report as _fmt_pg, format_book as _fmt_pbook, format_check as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_report_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "report":
            try:
                _item = agent.get_milestone_report(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.milestone_book())
        if _act == "check":
            return True, False, _fmt_ptarget(
                agent.milestone_book(), _tgt)
        if _act == "boundary":
            return True, False, _fmt_pbook(
                agent.milestone_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_milestone_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.milestone_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.milestone_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.milestone_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.milestone_book())
        return True, False, agent.milestone_status()["screen"]
    if command == "/log":
        # M-221 terminal target: show the entry book
        # held this session - entry slices as data: one
        # record per entry, held whole with the active
        # slice it was held from, its one verifiable
        # check at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one entry whole, the entry one check line
        # reaches, the entries of one slice, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no slice,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.build_log import format_entry as _fmt_pg, format_book as _fmt_pbook, format_check as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_entry_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "entry":
            try:
                _item = agent.get_log_entry(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.log_book())
        if _act == "check":
            return True, False, _fmt_ptarget(
                agent.log_book(), _tgt)
        if _act == "day":
            return True, False, _fmt_pbook(
                agent.log_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_log_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.log_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.log_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.log_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.log_book())
        return True, False, agent.log_status()["screen"]
    if command == "/selfmod":
        # M-222 terminal target: show the change book
        # held this session - change slices as data: one
        # record per change, held whole with the active
        # slice it was held from, its one verifiable
        # check at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one change whole, the change one check line
        # reaches, the changes of one slice, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no slice,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.self_modification import format_change as _fmt_pg, format_book as _fmt_pbook, format_check as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_change_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "change":
            try:
                _item = agent.get_selfmod_change(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.selfmod_book())
        if _act == "check":
            return True, False, _fmt_ptarget(
                agent.selfmod_book(), _tgt)
        if _act == "tool":
            return True, False, _fmt_pbook(
                agent.selfmod_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_selfmod_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.selfmod_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.selfmod_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.selfmod_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.selfmod_book())
        return True, False, agent.selfmod_status()["screen"]
    if command == "/failures":
        # M-223 terminal target: show the failure book
        # held this session - failure runs as data: one
        # record per failure, held whole with the active
        # run it was held from, its one verifiable
        # stage at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one failure whole, the failure one stage line
        # reaches, the failures of one run, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no run,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.failure_taxonomy import format_failure as _fmt_pg, format_book as _fmt_pbook, format_stage as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_failure_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "failure":
            try:
                _item = agent.get_failtax_failure(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.failtax_book())
        if _act == "stage":
            return True, False, _fmt_ptarget(
                agent.failtax_book(), _tgt)
        if _act == "run":
            return True, False, _fmt_pbook(
                agent.failtax_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_failtax_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.failtax_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.failtax_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.failtax_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.failtax_book())
        return True, False, agent.failtax_status()["screen"]
    if command == "/dryrun":
        # M-224 terminal target: show the rehearsal book
        # held this session - rehearsal campaigns as data: one
        # record per rehearsal, held whole with the active
        # campaign it was held from, its one verifiable
        # stage at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one rehearsal whole, the rehearsal one stage line
        # reaches, the rehearsals of one campaign, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no campaign,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.dry_run_campaigns import format_rehearsal as _fmt_pg, format_book as _fmt_pbook, format_stage as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_rehearsal_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "rehearsal":
            try:
                _item = agent.get_dryrun_rehearsal(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.dryrun_book())
        if _act == "stage":
            return True, False, _fmt_ptarget(
                agent.dryrun_book(), _tgt)
        if _act == "campaign":
            return True, False, _fmt_pbook(
                agent.dryrun_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_dryrun_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.dryrun_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.dryrun_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.dryrun_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.dryrun_book())
        return True, False, agent.dryrun_status()["screen"]
    if command == "/export":
        # M-225 terminal target: show the bundle book
        # held this session - bundle campaigns as data: one
        # record per bundle, held whole with the active
        # campaign it was held from, its one verifiable
        # stage at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one bundle whole, the bundle one stage line
        # reaches, the bundles of one campaign, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no campaign,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.campaign_export import format_bundle as _fmt_pg, format_book as _fmt_pbook, format_stage as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_bundle_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "bundle":
            try:
                _item = agent.get_export_bundle(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.export_book())
        if _act == "stage":
            return True, False, _fmt_ptarget(
                agent.export_book(), _tgt)
        if _act == "campaign":
            return True, False, _fmt_pbook(
                agent.export_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_export_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.export_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.export_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.export_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.export_book())
        return True, False, agent.export_status()["screen"]
    if command == "/orders":
        # M-226 terminal target: show the order book
        # held this session - order campaigns as data: one
        # record per order, held whole with the active
        # campaign it was held from, its one verifiable
        # stage at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one order whole, the order one stage line
        # reaches, the orders of one campaign, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no campaign,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.standing_orders import format_order as _fmt_pg, format_book as _fmt_pbook, format_stage as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_order_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "order":
            try:
                _item = agent.get_orders_order(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.orders_book())
        if _act == "stage":
            return True, False, _fmt_ptarget(
                agent.orders_book(), _tgt)
        if _act == "campaign":
            return True, False, _fmt_pbook(
                agent.orders_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_orders_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.orders_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.orders_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.orders_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.orders_book())
        return True, False, agent.orders_status()["screen"]
    if command == "/workflow":
        # M-227 terminal target: show the proposal book
        # held this session - proposal campaigns as data: one
        # record per proposal, held whole with the active
        # campaign it was held from, its one verifiable
        # stage at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one proposal whole, the proposal one stage line
        # reaches, the proposals of one campaign, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no campaign,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.workflow_default import format_proposal as _fmt_pg, format_book as _fmt_pbook, format_stage as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_proposal_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "proposal":
            try:
                _item = agent.get_workflow_proposal(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.workflow_book())
        if _act == "stage":
            return True, False, _fmt_ptarget(
                agent.workflow_book(), _tgt)
        if _act == "campaign":
            return True, False, _fmt_pbook(
                agent.workflow_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_workflow_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.workflow_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.workflow_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.workflow_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.workflow_book())
        return True, False, agent.workflow_status()["screen"]
    if command == "/scaling":
        # M-228 terminal target: show the endeavour book
        # held this session - endeavour campaigns as data: one
        # record per endeavour, held whole with the active
        # campaign it was held from, its one verifiable
        # stage at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one endeavour whole, the endeavour one stage line
        # reaches, the endeavours of one campaign, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no campaign,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.team_scaling import format_endeavour as _fmt_pg, format_book as _fmt_pbook, format_stage as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_endeavour_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "endeavour":
            try:
                _item = agent.get_scaling_endeavour(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.scaling_book())
        if _act == "stage":
            return True, False, _fmt_ptarget(
                agent.scaling_book(), _tgt)
        if _act == "campaign":
            return True, False, _fmt_pbook(
                agent.scaling_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_scaling_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.scaling_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.scaling_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.scaling_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.scaling_book())
        return True, False, agent.scaling_status()["screen"]
    if command == "/course":
        # M-229 terminal target: show the lesson book
        # held this session - lesson campaigns as data: one
        # record per lesson, held whole with the active
        # campaign it was held from, its one verifiable
        # stage at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one lesson whole, the lesson one stage line
        # reaches, the lessons of one campaign, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no campaign,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.method_course import format_lesson as _fmt_pg, format_book as _fmt_pbook, format_stage as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_lesson_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "lesson":
            try:
                _item = agent.get_course_lesson(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.course_book())
        if _act == "stage":
            return True, False, _fmt_ptarget(
                agent.course_book(), _tgt)
        if _act == "campaign":
            return True, False, _fmt_pbook(
                agent.course_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_course_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.course_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.course_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.course_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.course_book())
        return True, False, agent.course_status()["screen"]
    if command == "/metrics":
        # M-230 terminal target: show the reading book
        # held this session - reading campaigns as data: one
        # record per reading, held whole with the active
        # campaign it was held from, its one verifiable
        # stage at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one reading whole, the reading one stage line
        # reaches, the readings of one campaign, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no campaign,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.method_metrics import format_reading as _fmt_pg, format_book as _fmt_pbook, format_stage as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_reading_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "reading":
            try:
                _item = agent.get_metrics_reading(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.metrics_book())
        if _act == "stage":
            return True, False, _fmt_ptarget(
                agent.metrics_book(), _tgt)
        if _act == "campaign":
            return True, False, _fmt_pbook(
                agent.metrics_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_metrics_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.metrics_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.metrics_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.metrics_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.metrics_book())
        return True, False, agent.metrics_status()["screen"]
    if command == "/crossapp":
        # M-231 terminal target: show the external book
        # held this session - external campaigns as data: one
        # record per external, held whole with the active
        # campaign it was held from, its one verifiable
        # stage at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one external whole, the external one stage line
        # reaches, the externals of one campaign, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no campaign,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.cross_app_method import format_external as _fmt_pg, format_book as _fmt_pbook, format_stage as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_external_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "external":
            try:
                _item = agent.get_crossapp_external(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.crossapp_book())
        if _act == "stage":
            return True, False, _fmt_ptarget(
                agent.crossapp_book(), _tgt)
        if _act == "campaign":
            return True, False, _fmt_pbook(
                agent.crossapp_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_crossapp_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.crossapp_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.crossapp_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.crossapp_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.crossapp_book())
        return True, False, agent.crossapp_status()["screen"]
    if command == "/mcpclient":
        # M-233 terminal target: show the connection book
        # held this session - connection servers as data: one
        # record per connection, held whole with the active
        # server it was held from, its one verifiable
        # stage at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one connection whole, the connection one stage line
        # reaches, the connections of one server, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no server,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.mcp_client import format_connection as _fmt_pg, format_book as _fmt_pbook, format_stage as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_connection_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "connection":
            try:
                _item = agent.get_mcpclient_connection(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.mcpclient_book())
        if _act == "stage":
            return True, False, _fmt_ptarget(
                agent.mcpclient_book(), _tgt)
        if _act == "server":
            return True, False, _fmt_pbook(
                agent.mcpclient_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_mcpclient_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.mcpclient_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.mcpclient_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.mcpclient_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.mcpclient_book())
        return True, False, agent.mcpclient_status()["screen"]
    if command == "/mcpregistry":
        # M-235 terminal target: show the listing book
        # held this session - listing entrys as data: one
        # record per listing, held whole with the active
        # entry it was held from, its one verifiable
        # stage at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one listing whole, the listing one stage line
        # reaches, the listings of one entry, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no entry,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.mcp_registry import format_listing as _fmt_pg, format_book as _fmt_pbook, format_stage as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_listing_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "listing":
            try:
                _item = agent.get_mcpregistry_listing(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.mcpregistry_book())
        if _act == "stage":
            return True, False, _fmt_ptarget(
                agent.mcpregistry_book(), _tgt)
        if _act == "entry":
            return True, False, _fmt_pbook(
                agent.mcpregistry_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_mcpregistry_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.mcpregistry_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.mcpregistry_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.mcpregistry_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.mcpregistry_book())
        return True, False, agent.mcpregistry_status()["screen"]
    if command == "/skillsstandard":
        # M-236 terminal target: show the pack book
        # held this session - pack skills as data: one
        # record per pack, held whole with the active
        # skill it was held from, its one verifiable
        # stage at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one pack whole, the pack one stage line
        # reaches, the packs of one skill, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no skill,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.skills_standard import format_pack as _fmt_pg, format_book as _fmt_pbook, format_stage as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_pack_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "pack":
            try:
                _item = agent.get_skillsstandard_pack(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.skillsstandard_book())
        if _act == "stage":
            return True, False, _fmt_ptarget(
                agent.skillsstandard_book(), _tgt)
        if _act == "skill":
            return True, False, _fmt_pbook(
                agent.skillsstandard_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_skillsstandard_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.skillsstandard_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.skillsstandard_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.skillsstandard_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.skillsstandard_book())
        return True, False, agent.skillsstandard_status()["screen"]
    if command == "/customcommands":
        # M-237 terminal target: show the template book
        # held this session - template commands as data: one
        # record per template, held whole with the active
        # command it was held from, its one verifiable
        # stage at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one template whole, the template one stage line
        # reaches, the templates of one command, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no command,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.custom_commands import format_template as _fmt_pg, format_book as _fmt_pbook, format_stage as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_template_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "template":
            try:
                _item = agent.get_customcommands_template(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.customcommands_book())
        if _act == "stage":
            return True, False, _fmt_ptarget(
                agent.customcommands_book(), _tgt)
        if _act == "command":
            return True, False, _fmt_pbook(
                agent.customcommands_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_customcommands_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.customcommands_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.customcommands_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.customcommands_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.customcommands_book())
        return True, False, agent.customcommands_status()["screen"]
    if command == "/pluginbundles":
        # M-238 terminal target: show the bundle book
        # held this session - bundle plugins as data: one
        # record per bundle, held whole with the active
        # plugin it was held from, its one verifiable
        # stage at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one bundle whole, the bundle one stage line
        # reaches, the bundles of one plugin, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no plugin,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.plugin_bundles import format_bundle as _fmt_pg, format_book as _fmt_pbook, format_stage as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_bundle_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "bundle":
            try:
                _item = agent.get_pluginbundles_bundle(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.pluginbundles_book())
        if _act == "stage":
            return True, False, _fmt_ptarget(
                agent.pluginbundles_book(), _tgt)
        if _act == "plugin":
            return True, False, _fmt_pbook(
                agent.pluginbundles_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_pluginbundles_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.pluginbundles_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.pluginbundles_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.pluginbundles_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.pluginbundles_book())
        return True, False, agent.pluginbundles_status()["screen"]
    if command == "/vscodecompanions":
        # M-239 terminal target: show the companion book
        # held this session - companion editors as data: one
        # record per companion, held whole with the active
        # editor it was held from, its one verifiable
        # stage at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one companion whole, the companion one stage line
        # reaches, the companions of one editor, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no editor,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.vscode_companions import format_companion as _fmt_pg, format_book as _fmt_pbook, format_stage as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_companion_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "companion":
            try:
                _item = agent.get_vscodecompanions_companion(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.vscodecompanions_book())
        if _act == "stage":
            return True, False, _fmt_ptarget(
                agent.vscodecompanions_book(), _tgt)
        if _act == "editor":
            return True, False, _fmt_pbook(
                agent.vscodecompanions_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_vscodecompanions_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.vscodecompanions_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.vscodecompanions_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.vscodecompanions_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.vscodecompanions_book())
        return True, False, agent.vscodecompanions_status()["screen"]
    if command == "/idecompanions":
        # M-240 terminal target: show the endpoint book
        # held this session - endpoint hosts as data: one
        # record per endpoint, held whole with the active
        # host it was held from, its one verifiable
        # stage at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one endpoint whole, the endpoint one stage line
        # reaches, the endpoints of one host, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no host,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.ide_companions import format_endpoint as _fmt_pg, format_book as _fmt_pbook, format_stage as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_endpoint_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "endpoint":
            try:
                _item = agent.get_idecompanions_endpoint(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.idecompanions_book())
        if _act == "stage":
            return True, False, _fmt_ptarget(
                agent.idecompanions_book(), _tgt)
        if _act == "host":
            return True, False, _fmt_pbook(
                agent.idecompanions_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_idecompanions_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.idecompanions_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.idecompanions_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.idecompanions_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.idecompanions_book())
        return True, False, agent.idecompanions_status()["screen"]
    if command == "/rivalimporters":
        # M-241 terminal target: show the importer book
        # held this session - importer sources as data: one
        # record per importer, held whole with the active
        # source it was held from, its one verifiable
        # stage at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one importer whole, the importer one stage line
        # reaches, the importers of one source, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no source,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.rival_importers import format_importer as _fmt_pg, format_book as _fmt_pbook, format_stage as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_importer_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "importer":
            try:
                _item = agent.get_rivalimporters_importer(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.rivalimporters_book())
        if _act == "stage":
            return True, False, _fmt_ptarget(
                agent.rivalimporters_book(), _tgt)
        if _act == "source":
            return True, False, _fmt_pbook(
                agent.rivalimporters_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_rivalimporters_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.rivalimporters_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.rivalimporters_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.rivalimporters_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.rivalimporters_book())
        return True, False, agent.rivalimporters_status()["screen"]
    if command == "/samverkbridge":
        # M-242 terminal target: show the exchange book
        # held this session - exchange repos as data: one
        # record per exchange, held whole with the active
        # repo it was held from, its one verifiable
        # stage at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one exchange whole, the exchange one stage line
        # reaches, the exchanges of one repo, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no repo,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.samverk_bridge import format_exchange as _fmt_pg, format_book as _fmt_pbook, format_stage as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_exchange_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "exchange":
            try:
                _item = agent.get_samverkbridge_exchange(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.samverkbridge_book())
        if _act == "stage":
            return True, False, _fmt_ptarget(
                agent.samverkbridge_book(), _tgt)
        if _act == "repo":
            return True, False, _fmt_pbook(
                agent.samverkbridge_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_samverkbridge_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.samverkbridge_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.samverkbridge_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.samverkbridge_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.samverkbridge_book())
        return True, False, agent.samverkbridge_status()["screen"]
    if command == "/samtalbridge":
        # M-243 terminal target: show the dispatch book
        # held this session - dispatch halls as data: one
        # record per dispatch, held whole with the active
        # hall it was held from, its one verifiable
        # stage at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one dispatch whole, the dispatch one stage line
        # reaches, the dispatches of one hall, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no hall,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.samtal_bridge import format_dispatch as _fmt_pg, format_book as _fmt_pbook, format_stage as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_dispatch_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "dispatch":
            try:
                _item = agent.get_samtalbridge_dispatch(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.samtalbridge_book())
        if _act == "stage":
            return True, False, _fmt_ptarget(
                agent.samtalbridge_book(), _tgt)
        if _act == "hall":
            return True, False, _fmt_pbook(
                agent.samtalbridge_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_samtalbridge_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.samtalbridge_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.samtalbridge_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.samtalbridge_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.samtalbridge_book())
        return True, False, agent.samtalbridge_status()["screen"]
    if command == "/kistakeykeeper":
        # M-244 terminal target: show the resolution book
        # held this session - resolution bridges as data: one
        # record per resolution, held whole with the active
        # bridge it was held from, its one verifiable
        # stage at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one resolution whole, the resolution one stage line
        # reaches, the resolutions of one bridge, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no bridge,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.kista_keykeeper import format_resolution as _fmt_pg, format_book as _fmt_pbook, format_stage as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_resolution_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "resolution":
            try:
                _item = agent.get_kistakeykeeper_resolution(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.kistakeykeeper_book())
        if _act == "stage":
            return True, False, _fmt_ptarget(
                agent.kistakeykeeper_book(), _tgt)
        if _act == "bridge":
            return True, False, _fmt_pbook(
                agent.kistakeykeeper_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_kistakeykeeper_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.kistakeykeeper_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.kistakeykeeper_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.kistakeykeeper_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.kistakeykeeper_book())
        return True, False, agent.kistakeykeeper_status()["screen"]
    if command == "/aesirdeepening":
        # M-245 terminal road: show the Aesir deepening
        # held this session - per-role selections as
        # data: one record per crew office, naming
        # whether an Aesir session is selectable for
        # that role and why, beside the capability
        # report held this session (the shipped
        # selection book when none is held) - show the
        # held or silent report, the whole book, one
        # office's selection, the ask derived for one
        # office, the index derived from the whole
        # book, or the verdict derived for the session,
        # on the agent-layer parser + the pure
        # formatters. This road opens no session, calls
        # no model, probes no server, rewrites no route
        # and persists nothing - holding and telling
        # are words only.
        from .core.aesir_deepening import format_ask as _fmt_aask, format_selection as _fmt_asel, format_selections as _fmt_asels
        from .agents.llm import parse_aesirdeepening_args as _parse_a
        try:
            _act, _tgt, _needs, _model = _parse_a(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "report":
            return True, False, agent.aesirdeepening_status()["report_text"]
        if _act == "selections":
            return True, False, _fmt_asels(agent.aesirdeepening_book())
        if _act == "selection":
            try:
                _sel = agent.get_aesirdeepening_selection(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_asel(_sel)
        if _act == "ask":
            try:
                _ask = agent.aesirdeepening_ask(_tgt, needs=_needs, model=_model)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_aask(_ask)
        if _act == "index":
            return True, False, agent.aesirdeepening_index()["index_text"]
        if _act == "verdict":
            return True, False, agent.aesirdeepening_verdict()["verdict_text"]
        return True, False, agent.aesirdeepening_status()["screen"]
    if command == "/githostparity":
        # M-246 terminal road: show the git host parity
        # held this session - the forge's git hosts as
        # registry entries like providers: one entry per
        # host, naming the word that host gives the
        # request craft, beside the parity records held
        # this session (no record held when none is
        # held) - show the whole shipped registry, one
        # host's entry, the record held for one host,
        # the standing derived for one host, the index
        # derived over every host, or the verdict
        # derived for the session, on the agent-layer
        # parser + the pure formatters. This road calls
        # no host API, clones nothing, pushes nothing,
        # probes no network and persists nothing -
        # holding and telling are words only.
        from .core.git_host_parity import format_host as _fmt_ghost, format_hosts as _fmt_ghosts, format_parity as _fmt_gparity
        from .agents.llm import parse_githostparity_args as _parse_g
        try:
            _act, _tgt, _needs, _model = _parse_g(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "hosts":
            return True, False, _fmt_ghosts(agent.githostparity_hosts())
        if _act == "host":
            try:
                _entry = agent.get_githostparity_host(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_ghost(_entry)
        if _act == "record":
            try:
                _rec = agent.get_githostparity_record(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_gparity(_rec)
        if _act == "standing":
            try:
                _standing = agent.githostparity_standing(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            _text = (f"{_standing.host}: parity {_standing.standing} "
                     f"(stage: {_standing.stage or 'none'})")
            for _gap in _standing.gaps:
                _text += f"\n  gap: {_gap}"
            return True, False, _text
        if _act == "index":
            return True, False, agent.githostparity_index()["index_text"]
        if _act == "verdict":
            return True, False, agent.githostparity_verdict()["verdict_text"]
        return True, False, agent.githostparity_status()["screen"]
    if command == "/cibridges":
        # M-247 terminal road: show the CI bridges
        # held this session - the CI providers as
        # registry entries: one entry per provider,
        # naming the word that provider gives a single
        # run, beside the run records held this session
        # (no record held when none is held) - show the
        # whole shipped registry, one provider's entry,
        # the record held for one provider and workflow,
        # the standing derived for one run, the workflow
        # drafts held, the index derived over every held
        # record, or the verdict derived for the session,
        # on the agent-layer parser + the pure
        # formatters. This road calls no CI API, fetches
        # no run, changes no workflow, dispatches
        # nothing, probes no network and persists
        # nothing - holding and telling are words only.
        from .core.ci_bridges import format_provider as _fmt_ciprov, format_providers as _fmt_ciprovs, format_record as _fmt_cirec
        from .agents.llm import parse_cibridges_args as _parse_ci
        try:
            _act, _tgt, _needs, _model = _parse_ci(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "providers":
            return True, False, _fmt_ciprovs(agent.cibridges_providers())
        if _act == "provider":
            try:
                _entry = agent.get_cibridges_provider(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_ciprov(_entry)
        if _act == "record":
            try:
                _rec = agent.get_cibridges_record(*_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_cirec(_rec)
        if _act == "standing":
            try:
                _standing = agent.cibridges_standing(*_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            _text = (f"{_tgt[0]}/{_tgt[1]}: CI "
                     f"{'held as fact' if _standing.held else 'open'} "
                     f"(stage: {_standing.stage})")
            for _gap in _standing.gaps:
                _text += f"\n  gap: {_gap}"
            return True, False, _text
        if _act == "drafts":
            _drafts = agent.cibridges_drafts()
            if not _drafts:
                return True, False, ("Workflow drafts: none held this "
                                     "session - workflow changes are "
                                     "proposed only as drafts, and a "
                                     "draft is never applied here.")
            return True, False, "\n".join(
                f"{_d.provider}/{_d.workflow}: draft - {_d.change} "
                f"(trigger: {_d.trigger}; a draft is never applied here)"
                for _d in _drafts)
        if _act == "draft":
            try:
                _d = agent.get_cibridges_draft(*_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, (
                f"{_d.provider}/{_d.workflow}: draft - {_d.change} "
                f"(trigger: {_d.trigger}; a draft is never applied here)")
        if _act == "index":
            return True, False, agent.cibridges_index()["index_text"]
        if _act == "verdict":
            return True, False, agent.cibridges_verdict()["verdict_text"]
        return True, False, agent.cibridges_status()["screen"]
    if command == "/issuetrackers":
        # M-248 terminal road: show the issue trackers
        # held this session - the issue trackers as
        # registry entries: one entry per tracker,
        # naming the word that tracker gives a single
        # run, beside the issue records held this session
        # (no record held when none is held) - show the
        # whole shipped registry, one tracker's entry,
        # the record held for one tracker and issue_key,
        # the standing derived for one issue, the issue_key
        # drafts held, the index derived over every held
        # record, or the verdict derived for the session,
        # on the agent-layer parser + the pure
        # formatters. This road calls no tracker API, fetches
        # no run, changes no issue_key, dispatches
        # nothing, probes no network and persists
        # nothing - holding and telling are words only.
        from .core.issue_trackers import format_tracker as _fmt_ciprov, format_trackers as _fmt_ciprovs, format_record as _fmt_cirec
        from .agents.llm import parse_issuetrackers_args as _parse_ci
        try:
            _act, _tgt, _needs, _model = _parse_ci(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "trackers":
            return True, False, _fmt_ciprovs(agent.issuetrackers_trackers())
        if _act == "tracker":
            try:
                _entry = agent.get_issuetrackers_tracker(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_ciprov(_entry)
        if _act == "record":
            try:
                _rec = agent.get_issuetrackers_record(*_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_cirec(_rec)
        if _act == "standing":
            try:
                _standing = agent.issuetrackers_standing(*_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            _text = (f"{_tgt[0]}/{_tgt[1]}: issue "
                     f"{'held as fact' if _standing.held else 'open'} "
                     f"(stage: {_standing.stage})")
            for _gap in _standing.gaps:
                _text += f"\n  gap: {_gap}"
            return True, False, _text
        if _act == "drafts":
            _drafts = agent.issuetrackers_drafts()
            if not _drafts:
                return True, False, ("Write drafts: none held this "
                                     "session - tracker writes are "
                                     "proposed only as drafts, and a "
                                     "draft is never applied here.")
            return True, False, "\n".join(
                f"{_d.tracker}/{_d.issue_key}: draft - {_d.change} "
                f"(approval: {_d.approval}; a draft is never applied here)"
                for _d in _drafts)
        if _act == "draft":
            try:
                _d = agent.get_issuetrackers_draft(*_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, (
                f"{_d.tracker}/{_d.issue_key}: draft - {_d.change} "
                f"(approval: {_d.approval}; a draft is never applied here)")
        if _act == "index":
            return True, False, agent.issuetrackers_index()["index_text"]
        if _act == "verdict":
            return True, False, agent.issuetrackers_verdict()["verdict_text"]
        return True, False, agent.issuetrackers_status()["screen"]
    if command == "/wyrdseam":
        # M-249 terminal road: show the WYRD seam held
        # this session - the world-state sources as
        # registry entries: one entry per source, naming
        # the word that source gives a single telling,
        # beside the node snapshots held this session
        # (no snapshot recorded when none is held) - show
        # the whole shipped registry, one source's entry,
        # the snapshot held for one source and node, the
        # standing derived for one node, the campaign
        # advice held, the index derived over every held
        # snapshot, or the verdict derived for the
        # session, on the agent-layer parser + the pure
        # formatters. This road calls no WYRD engine API,
        # probes no machine, measures no load, reroutes
        # no campaign, probes no network and persists
        # nothing - holding and telling are words only.
        from .core.wyrd_seam import format_source as _fmt_ciprov, format_sources as _fmt_ciprovs, format_snapshot as _fmt_cirec
        from .agents.llm import parse_wyrdseam_args as _parse_ci
        try:
            _act, _tgt, _needs, _model = _parse_ci(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "sources":
            return True, False, _fmt_ciprovs(agent.wyrdseam_sources())
        if _act == "source":
            try:
                _entry = agent.get_wyrdseam_source(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_ciprov(_entry)
        if _act == "snapshot":
            try:
                _rec = agent.get_wyrdseam_snapshot(*_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_cirec(_rec)
        if _act == "standing":
            try:
                _standing = agent.wyrdseam_standing(*_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            _text = (f"{_tgt[0]}/{_tgt[1]}: world-state "
                     f"{'current as recorded' if _standing.held else 'open'} "
                     f"(stage: {_standing.stage}; "
                     f"freshness: {_standing.freshness})")
            for _gap in _standing.gaps:
                _text += f"\n  gap: {_gap}"
            return True, False, _text
        if _act == "advices":
            _drafts = agent.wyrdseam_advices()
            if not _drafts:
                return True, False, ("Campaign advice: none held this "
                                     "session - the seam proposes campaign "
                                     "moves only as advice, and advice is "
                                     "never applied here.")
            return True, False, "\n".join(
                f"{_d.campaign} -> {_d.node}: advice - {_d.advice} "
                f"(approval: {_d.approval}; advice is never applied here)"
                for _d in _drafts)
        if _act == "advice":
            try:
                _d = agent.get_wyrdseam_advice(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, (
                f"{_d.campaign} -> {_d.node}: advice - {_d.advice} "
                f"(approval: {_d.approval}; advice is never applied here)")
        if _act == "index":
            return True, False, agent.wyrdseam_index()["index_text"]
        if _act == "verdict":
            return True, False, agent.wyrdseam_verdict()["verdict_text"]
        return True, False, agent.wyrdseam_status()["screen"]
    if command == "/webhookdoors":
        # M-249 terminal road: show the webhook doors held
        # this session - the webhook sources as
        # registry entries: one entry per source, naming
        # the word that source gives a single telling,
        # beside the event events held this session
        # (no event recorded when none is held) - show
        # the whole shipped registry, one source's entry,
        # the event held for one source and event, the
        # standing derived for one event, the campaign
        # proposal held, the index derived over every held
        # event, or the verdict derived for the
        # session, on the agent-layer parser + the pure
        # formatters. This road calls no host API,
        # opens no listener, starts nothing, builds unbidden
        # no campaign, probes no network and persists
        # nothing - holding and telling are words only.
        from .core.webhook_doors import format_source as _fmt_ciprov, format_sources as _fmt_ciprovs, format_event as _fmt_cirec
        from .agents.llm import parse_webhookdoors_args as _parse_ci
        try:
            _act, _tgt, _needs, _model = _parse_ci(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "sources":
            return True, False, _fmt_ciprovs(agent.webhookdoors_sources())
        if _act == "source":
            try:
                _entry = agent.get_webhookdoors_source(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_ciprov(_entry)
        if _act == "event":
            try:
                _rec = agent.get_webhookdoors_event(*_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_cirec(_rec)
        if _act == "standing":
            try:
                _standing = agent.webhookdoors_standing(*_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            _text = (f"{_tgt[0]}/{_tgt[1]}: webhook "
                     f"{'held as recorded' if _standing.held else 'open'} "
                     f"(stage: {_standing.stage}; "
                     f"freshness: {_standing.freshness})")
            for _gap in _standing.gaps:
                _text += f"\n  gap: {_gap}"
            return True, False, _text
        if _act == "proposals":
            _drafts = agent.webhookdoors_proposals()
            if not _drafts:
                return True, False, ("Campaign proposal: none held this "
                                     "session - the doors proposes campaign "
                                     "moves only as proposals, and a proposal is "
                                     "never applied here.")
            return True, False, "\n".join(
                f"{_d.campaign} -> {_d.event}: proposal - {_d.proposal} "
                f"(approval: {_d.approval}; proposal is never applied here)"
                for _d in _drafts)
        if _act == "propose":
            try:
                _d = agent.get_webhookdoors_proposal(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, (
                f"{_d.campaign} -> {_d.event}: proposal - {_d.proposal} "
                f"(approval: {_d.approval}; proposal is never applied here)")
        if _act == "index":
            return True, False, agent.webhookdoors_index()["index_text"]
        if _act == "verdict":
            return True, False, agent.webhookdoors_verdict()["verdict_text"]
        return True, False, agent.webhookdoors_status()["screen"]
    if command == "/exporteverything":
        # M-251 terminal road: show the export everything held
        # this session - the export kinds as
        # registry entries: one entry per kind, naming
        # the word that kind gives a single telling,
        # beside the record records held this session
        # (no record recorded when none is held) - show
        # the whole shipped registry, one kind's entry,
        # the record held for one kind and record, the
        # standing derived for one record, the bundle
        # draft held, the index derived over every held
        # record, or the verdict derived for the
        # session, on the agent-layer parser + the pure
        # formatters. This road calls no host API,
        # performs no export, starts nothing, exports here
        # no bundle, probes no network and persists
        # nothing - holding and telling are words only.
        from .core.export_everything import format_kind as _fmt_ciprov, format_kinds as _fmt_ciprovs, format_record as _fmt_cirec
        from .agents.llm import parse_exporteverything_args as _parse_ci
        try:
            _act, _tgt, _needs, _model = _parse_ci(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "kinds":
            return True, False, _fmt_ciprovs(agent.exporteverything_kinds())
        if _act == "kind":
            try:
                _entry = agent.get_exporteverything_kind(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_ciprov(_entry)
        if _act == "record":
            try:
                _rec = agent.get_exporteverything_record(*_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_cirec(_rec)
        if _act == "standing":
            try:
                _standing = agent.exporteverything_standing(*_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            _text = (f"{_tgt[0]}/{_tgt[1]}: export "
                     f"{'held as open' if _standing.held else 'open'} "
                     f"(stage: {_standing.stage}; "
                     f"freshness: {_standing.freshness})")
            for _gap in _standing.gaps:
                _text += f"\n  gap: {_gap}"
            return True, False, _text
        if _act == "drafts":
            _drafts = agent.exporteverything_drafts()
            if not _drafts:
                return True, False, ("Bundle draft: none held this "
                                     "session - the doors prepares bundle "
                                     "moves only as drafts, and a draft is "
                                     "never exported here.")
            return True, False, "\n".join(
                f"{_d.bundle} -> {_d.record}: draft - {_d.draft} "
                f"(state: {_d.state}; draft is never exported here)"
                for _d in _drafts)
        if _act == "prepare":
            try:
                _d = agent.get_exporteverything_draft(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, (
                f"{_d.bundle} -> {_d.record}: draft - {_d.draft} "
                f"(state: {_d.state}; draft is never exported here)")
        if _act == "index":
            return True, False, agent.exporteverything_index()["index_text"]
        if _act == "verdict":
            return True, False, agent.exporteverything_verdict()["verdict_text"]
        return True, False, agent.exporteverything_status()["screen"]
    if command == "/bridgeaudit":
        # M-253 terminal road: show the bridge permissions audit held
        # this session - the export bridges as
        # registry entries: one entry per bridge, naming
        # the word that bridge gives a single telling,
        # beside the record records held this session
        # (no record recorded when none is held) - show
        # the whole shipped registry, one bridge's entry,
        # the record held for one bridge and record, the
        # standing derived for one record, the bridge
        # report held, the index derived over every held
        # record, or the verdict derived for the
        # session, on the agent-layer parser + the pure
        # formatters. This road calls no host API,
        # performs no export, starts nothing, exports here
        # no bridge, probes no network and persists
        # nothing - holding and telling are words only.
        from .core.bridge_permissions import format_bridge as _fmt_ciprov, format_bridges as _fmt_ciprovs, format_record as _fmt_cirec
        from .agents.llm import parse_bridgeaudit_args as _parse_ci
        try:
            _act, _tgt, _needs, _model = _parse_ci(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "bridges":
            return True, False, _fmt_ciprovs(agent.bridgeaudit_bridges())
        if _act == "bridge":
            try:
                _entry = agent.get_bridgeaudit_bridge(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_ciprov(_entry)
        if _act == "record":
            try:
                _rec = agent.get_bridgeaudit_record(*_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_cirec(_rec)
        if _act == "standing":
            try:
                _standing = agent.bridgeaudit_standing(*_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            _text = (f"{_tgt[0]}/{_tgt[1]}: audit "
                     f"{'held as audited' if _standing.held else 'open'} "
                     f"(stage: {_standing.stage}; "
                     f"freshness: {_standing.freshness})")
            for _gap in _standing.gaps:
                _text += f"\n  gap: {_gap}"
            return True, False, _text
        if _act == "reports":
            _reports = agent.bridgeaudit_reports()
            if not _reports:
                return True, False, ("Bridge report: none held this "
                                     "session - the doors reports bridge "
                                     "moves only as reports, and a report is "
                                     "never a grant here.")
            return True, False, "\n".join(
                f"{_d.bridge} -> {_d.record}: report - {_d.report} "
                f"(state: {_d.state}; report is never a grant here)"
                for _d in _reports)
        if _act == "report":
            try:
                _d = agent.get_bridgeaudit_report(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, (
                f"{_d.bridge} -> {_d.record}: report - {_d.report} "
                f"(state: {_d.state}; report is never a grant here)")
        if _act == "index":
            return True, False, agent.bridgeaudit_index()["index_text"]
        if _act == "verdict":
            return True, False, agent.bridgeaudit_verdict()["verdict_text"]
        return True, False, agent.bridgeaudit_status()["screen"]


    if command == "/benchmarkharness":
        # M-255 terminal road: show the benchmark harness held
        # this session - the run kinds as
        # registry entries: one entry per kind, naming
        # the word that kind gives a single run,
        # beside the run records held this session
        # (no run recorded when none is held) - show
        # the whole shipped registry, one kind's entry,
        # the record held for one kind and run, the
        # standing derived for one run, the run
        # report held, the index derived over every held
        # record, or the verdict derived for the
        # session, on the agent-layer parser + the pure
        # formatters. This road runs no task,
        # creates no sandbox, executes no grading test, inflates
        # no result, probes no network and persists
        # nothing - holding and telling are words only.
        from .core.benchmark_harness import format_kind as _fmt_bhkind, format_kinds as _fmt_bhkinds, format_record as _fmt_bhrec
        from .agents.llm import parse_benchmarkharness_args as _parse_bh
        try:
            _act, _tgt, _needs, _model = _parse_bh(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "kinds":
            return True, False, _fmt_bhkinds(agent.benchmarkharness_kinds())
        if _act == "kind":
            try:
                _entry = agent.get_benchmarkharness_kind(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_bhkind(_entry)
        if _act == "record":
            try:
                _rec = agent.get_benchmarkharness_record(*_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_bhrec(_rec)
        if _act == "standing":
            try:
                _standing = agent.benchmarkharness_standing(*_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            _text = (f"{_tgt[0]}/{_tgt[1]}: run "
                     f"{'passed as graded' if _standing.held else 'open'} "
                     f"(stage: {_standing.stage}; "
                     f"grade: {_standing.grade})")
            for _gap in _standing.gaps:
                _text += f"\n  gap: {_gap}"
            return True, False, _text
        if _act == "reports":
            _reports = agent.benchmarkharness_reports()
            if not _reports:
                return True, False, ("Run report: none held this "
                                     "session - the harness reports run "
                                     "moves only as reports, and a report is "
                                     "never inflated here.")
            return True, False, "\n".join(
                f"{_d.kind} -> {_d.run}: report - {_d.report} "
                f"(state: {_d.state}; report is never inflated here)"
                for _d in _reports)
        if _act == "report":
            try:
                _d = agent.get_benchmarkharness_report(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, (
                f"{_d.kind} -> {_d.run}: report - {_d.report} "
                f"(state: {_d.state}; report is never inflated here)")
        if _act == "index":
            return True, False, agent.benchmarkharness_index()["index_text"]
        if _act == "verdict":
            return True, False, agent.benchmarkharness_verdict()["verdict_text"]
        return True, False, agent.benchmarkharness_status()["screen"]


    if command == "/publishedyardstick":
        # M-256 terminal road: show the published yardsticks held
        # this session - the public sets as
        # registry entries: one entry per set, naming
        # the word that set gives a single run and the
        # standing of its licence,
        # beside the run records held this session
        # (no run recorded when none is held) - show
        # the whole shipped registry, one yardstick's entry,
        # the record held for one yardstick and run, the
        # standing derived for one run, the run
        # report held, the index derived over every held
        # record, or the verdict derived for the
        # session, on the agent-layer parser + the pure
        # formatters. This road runs no benchmark,
        # downloads no set, executes no grading test, inflates
        # no result, probes no network and persists
        # nothing - holding and telling are words only.
        from .core.published_yardstick import format_yardstick as _fmt_pyyard, format_yardsticks as _fmt_pyyards, format_record as _fmt_pyrec
        from .agents.llm import parse_publishedyardstick_args as _parse_py
        try:
            _act, _tgt, _needs, _model = _parse_py(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "yardsticks":
            return True, False, _fmt_pyyards(agent.publishedyardstick_yardsticks())
        if _act == "yardstick":
            try:
                _entry = agent.get_publishedyardstick_yardstick(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pyyard(_entry)
        if _act == "record":
            try:
                _rec = agent.get_publishedyardstick_record(*_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pyrec(_rec)
        if _act == "standing":
            try:
                _standing = agent.publishedyardstick_standing(*_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            _text = (f"{_tgt[0]}/{_tgt[1]}: run "
                     f"{'held as reported' if _standing.held else 'open'} "
                     f"(stage: {_standing.stage}; "
                     f"grade: {_standing.grade})")
            for _gap in _standing.gaps:
                _text += f"\n  gap: {_gap}"
            return True, False, _text
        if _act == "reports":
            _reports = agent.publishedyardstick_reports()
            if not _reports:
                return True, False, ("Run report: none held this "
                                     "session - the yardsticks report run "
                                     "moves only as reports, and a report is "
                                     "never inflated here.")
            return True, False, "\n".join(
                f"{_d.yardstick} -> {_d.run}: report - {_d.report} "
                f"(state: {_d.state}; report is never inflated here)"
                for _d in _reports)
        if _act == "report":
            try:
                _d = agent.get_publishedyardstick_report(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, (
                f"{_d.yardstick} -> {_d.run}: report - {_d.report} "
                f"(state: {_d.state}; report is never inflated here)")
        if _act == "index":
            return True, False, agent.publishedyardstick_index()["index_text"]
        if _act == "verdict":
            return True, False, agent.publishedyardstick_verdict()["verdict_text"]
        return True, False, agent.publishedyardstick_status()["screen"]

    if command == "/regressioncourt":
        # M-257 terminal road: show the regression court held
        # this session - the public sets as
        # registry entries: one entry per set, naming
        # the word that set gives a single run and the
        # standing of its gate,
        # beside the run records held this session
        # (no run recorded when none is held) - show
        # the whole shipped registry, one part's entry,
        # the record held for one part and run, the
        # standing derived for one run, the run
        # verdict held, the index derived over every held
        # record, or the verdict derived for the
        # session, on the agent-layer parser + the pure
        # formatters. This road runs no benchmark,
        # downloads no set, executes no grading test, inflates
        # no result, probes no network and persists
        # nothing - holding and telling are words only.
        from .core.regression_court import format_part as _fmt_rcpart, format_parts as _fmt_rcparts, format_record as _fmt_rcrec
        from .agents.llm import parse_regressioncourt_args as _parse_rc
        try:
            _act, _tgt, _needs, _model = _parse_rc(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "parts":
            return True, False, _fmt_rcparts(agent.regressioncourt_parts())
        if _act == "part":
            try:
                _entry = agent.get_regressioncourt_part(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_rcpart(_entry)
        if _act == "record":
            try:
                _rec = agent.get_regressioncourt_record(*_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_rcrec(_rec)
        if _act == "standing":
            try:
                _standing = agent.regressioncourt_standing(*_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            _text = (f"{_tgt[0]}/{_tgt[1]}: run "
                     f"{'held as re-run' if _standing.held else 'open'} "
                     f"(stage: {_standing.stage}; "
                     f"grade: {_standing.grade})")
            for _gap in _standing.gaps:
                _text += f"\n  gap: {_gap}"
            return True, False, _text
        if _act == "drafts":
            _verdicts = agent.regressioncourt_drafts()
            if not _verdicts:
                return True, False, ("Run verdict: none held this "
                                     "session - the parts verdict run "
                                     "moves only as verdicts, and a verdict is "
                                     "never inflated here.")
            return True, False, "\n".join(
                f"{_d.battery} -> {_d.entry}: verdict - {_d.verdict} "
                f"(state: {_d.state}; verdict is never inflated here)"
                for _d in _verdicts)
        if _act == "draft":
            try:
                _d = agent.get_regressioncourt_draft(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, (
                f"{_d.battery} -> {_d.entry}: verdict - {_d.verdict} "
                f"(state: {_d.state}; verdict is never inflated here)")
        if _act == "index":
            return True, False, agent.regressioncourt_index()["index_text"]
        if _act == "verdict":
            return True, False, agent.regressioncourt_verdict()["verdict_text"]
        return True, False, agent.regressioncourt_status()["screen"]

    if command == "/performancebudgets":
        # M-258 terminal road: show the performance budgets held
        # this session - the public sets as
        # registry entries: one entry per set, naming
        # the word that set gives a single run and the
        # standing of its gate,
        # beside the run records held this session
        # (no run recorded when none is held) - show
        # the whole shipped registry, one measure's entry,
        # the record held for one measure and run, the
        # standing derived for one run, the run
        # verdict held, the index derived over every held
        # record, or the verdict derived for the
        # session, on the agent-layer parser + the pure
        # formatters. This road runs no benchmark,
        # downloads no set, executes no grading test, inflates
        # no result, probes no network and persists
        # nothing - holding and telling are words only.
        from .core.performance_budgets import format_measure as _fmt_rcpart, format_measures as _fmt_rcparts, format_record as _fmt_rcrec
        from .agents.llm import parse_performancebudgets_args as _parse_rc
        try:
            _act, _tgt, _needs, _model = _parse_rc(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "measures":
            return True, False, _fmt_rcparts(agent.performancebudgets_measures())
        if _act == "measure":
            try:
                _entry = agent.get_performancebudgets_measure(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_rcpart(_entry)
        if _act == "record":
            try:
                _rec = agent.get_performancebudgets_record(*_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_rcrec(_rec)
        if _act == "standing":
            try:
                _standing = agent.performancebudgets_standing(*_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            _text = (f"{_tgt[0]}/{_tgt[1]}: run "
                     f"{'held as measured' if _standing.held else 'open'} "
                     f"(stage: {_standing.stage}; "
                     f"grade: {_standing.grade})")
            for _gap in _standing.gaps:
                _text += f"\n  gap: {_gap}"
            return True, False, _text
        if _act == "reports":
            _reports = agent.performancebudgets_reports()
            if not _reports:
                return True, False, ("Run verdict: none held this "
                                     "session - the measures verdict run "
                                     "moves only as verdicts, and a verdict is "
                                     "never inflated here.")
            return True, False, "\n".join(
                f"{_d.book} -> {_d.entry}: verdict - {_d.report} "
                f"(state: {_d.state}; verdict is never inflated here)"
                for _d in _reports)
        if _act == "report":
            try:
                _d = agent.get_performancebudgets_report(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, (
                f"{_d.book} -> {_d.entry}: verdict - {_d.report} "
                f"(state: {_d.state}; verdict is never inflated here)")
        if _act == "index":
            return True, False, agent.performancebudgets_index()["index_text"]
        if _act == "verdict":
            return True, False, agent.performancebudgets_verdict()["verdict_text"]
        return True, False, agent.performancebudgets_status()["screen"]

    if command == "/platformmatrixfinal":
        # M-259 terminal road: show the platform matrix final held
        # this session - the public sets as
        # registry entries: one entry per set, naming
        # the word that set gives a single run and the
        # standing of its gate,
        # beside the run records held this session
        # (no run recorded when none is held) - show
        # the whole shipped registry, one cell's entry,
        # the record held for one cell and run, the
        # standing derived for one run, the run
        # verdict held, the index derived over every held
        # record, or the verdict derived for the
        # session, on the agent-layer parser + the pure
        # formatters. This road runs no benchmark,
        # downloads no set, executes no grading test, inflates
        # no result, probes no network and persists
        # nothing - holding and telling are words only.
        from .core.platform_matrix_final import format_cell as _fmt_rcpart, format_cells as _fmt_rcparts, format_record as _fmt_rcrec
        from .agents.llm import parse_platformmatrixfinal_args as _parse_rc
        try:
            _act, _tgt, _needs, _model = _parse_rc(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "cells":
            return True, False, _fmt_rcparts(agent.platformmatrixfinal_cells())
        if _act == "cell":
            try:
                _entry = agent.get_platformmatrixfinal_cell(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_rcpart(_entry)
        if _act == "record":
            try:
                _rec = agent.get_platformmatrixfinal_record(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_rcrec(_rec)
        if _act == "standing":
            try:
                _standing = agent.platformmatrixfinal_standing(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            _text = (f"{_tgt}: run "
                     f"{'held as answered' if _standing.held else 'open'} "
                     f"(stage: {_standing.stage}; "
                     f"grade: {_standing.grade})")
            for _gap in _standing.gaps:
                _text += f"\n  gap: {_gap}"
            return True, False, _text
        if _act == "reports":
            _reports = agent.platformmatrixfinal_reports()
            if not _reports:
                return True, False, ("Run verdict: none held this "
                                     "session - the cells verdict run "
                                     "moves only as verdicts, and a verdict is "
                                     "never inflated here.")
            return True, False, "\n".join(
                f"{_d.book} -> {_d.entry}: verdict - {_d.report} "
                f"(state: {_d.state}; verdict is never inflated here)"
                for _d in _reports)
        if _act == "report":
            try:
                _d = agent.get_platformmatrixfinal_report(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, (
                f"{_d.book} -> {_d.entry}: verdict - {_d.report} "
                f"(state: {_d.state}; verdict is never inflated here)")
        if _act == "index":
            return True, False, agent.platformmatrixfinal_index()["index_text"]
        if _act == "verdict":
            return True, False, agent.platformmatrixfinal_verdict()["verdict_text"]
        return True, False, agent.platformmatrixfinal_status()["screen"]

    if command == "/securityaudit":
        # M-260 terminal road: show the security audit held
        # this session - the public sets as
        # registry entries: one entry per set, naming
        # the word that set gives a single run and the
        # standing of its gate,
        # beside the run records held this session
        # (no run recorded when none is held) - show
        # the whole shipped registry, one area's entry,
        # the record held for one area and run, the
        # standing derived for one run, the run
        # verdict held, the index derived over every held
        # record, or the verdict derived for the
        # session, on the agent-layer parser + the pure
        # formatters. This road runs no benchmark,
        # downloads no set, executes no grading test, inflates
        # no result, probes no network and persists
        # nothing - holding and telling are words only.
        from .core.security_audit import format_area as _fmt_rcpart, format_areas as _fmt_rcparts, format_record as _fmt_rcrec
        from .agents.llm import parse_securityaudit_args as _parse_rc
        try:
            _act, _tgt, _needs, _model = _parse_rc(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "areas":
            return True, False, _fmt_rcparts(agent.securityaudit_areas())
        if _act == "area":
            try:
                _entry = agent.get_securityaudit_area(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_rcpart(_entry)
        if _act == "record":
            try:
                _rec = agent.get_securityaudit_record(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_rcrec(_rec)
        if _act == "standing":
            try:
                _standing = agent.securityaudit_standing(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            _text = (f"{_tgt}: run "
                     f"{'held as answered' if _standing.held else 'open'} "
                     f"(stage: {_standing.stage}; "
                     f"grade: {_standing.grade})")
            for _gap in _standing.gaps:
                _text += f"\n  gap: {_gap}"
            return True, False, _text
        if _act == "reports":
            _reports = agent.securityaudit_reports()
            if not _reports:
                return True, False, ("Run verdict: none held this "
                                     "session - the areas verdict run "
                                     "moves only as verdicts, and a verdict is "
                                     "never inflated here.")
            return True, False, "\n".join(
                f"{_d.book} -> {_d.entry}: verdict - {_d.report} "
                f"(state: {_d.state}; verdict is never inflated here)"
                for _d in _reports)
        if _act == "report":
            try:
                _d = agent.get_securityaudit_report(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, (
                f"{_d.book} -> {_d.entry}: verdict - {_d.report} "
                f"(state: {_d.state}; verdict is never inflated here)")
        if _act == "index":
            return True, False, agent.securityaudit_index()["index_text"]
        if _act == "verdict":
            return True, False, agent.securityaudit_verdict()["verdict_text"]
        return True, False, agent.securityaudit_status()["screen"]

    if command == "/privacyaudit":
        # M-261 terminal road: show the privacy audit held
        # this session - the public sets as
        # registry entries: one entry per set, naming
        # the word that set gives a single run and the
        # standing of its gate,
        # beside the run records held this session
        # (no run recorded when none is held) - show
        # the whole shipped registry, one surface's entry,
        # the record held for one surface and run, the
        # standing derived for one run, the run
        # verdict held, the index derived over every held
        # record, or the verdict derived for the
        # session, on the agent-layer parser + the pure
        # formatters. This road runs no benchmark,
        # downloads no set, executes no grading test, inflates
        # no result, probes no network and persists
        # nothing - holding and telling are words only.
        from .core.privacy_audit import format_surface as _fmt_rcpart, format_surfaces as _fmt_rcparts, format_record as _fmt_rcrec
        from .agents.llm import parse_privacyaudit_args as _parse_rc
        try:
            _act, _tgt, _needs, _model = _parse_rc(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "surfaces":
            return True, False, _fmt_rcparts(agent.privacyaudit_surfaces())
        if _act == "surface":
            try:
                _entry = agent.get_privacyaudit_surface(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_rcpart(_entry)
        if _act == "record":
            try:
                _rec = agent.get_privacyaudit_record(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_rcrec(_rec)
        if _act == "standing":
            try:
                _standing = agent.privacyaudit_standing(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            _text = (f"{_tgt}: run "
                     f"{'held as answered' if _standing.held else 'open'} "
                     f"(stage: {_standing.stage}; "
                     f"grade: {_standing.grade})")
            for _gap in _standing.gaps:
                _text += f"\n  gap: {_gap}"
            return True, False, _text
        if _act == "reports":
            _reports = agent.privacyaudit_reports()
            if not _reports:
                return True, False, ("Run verdict: none held this "
                                     "session - the surfaces verdict run "
                                     "moves only as verdicts, and a verdict is "
                                     "never inflated here.")
            return True, False, "\n".join(
                f"{_d.book} -> {_d.entry}: verdict - {_d.report} "
                f"(state: {_d.state}; verdict is never inflated here)"
                for _d in _reports)
        if _act == "report":
            try:
                _d = agent.get_privacyaudit_report(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, (
                f"{_d.book} -> {_d.entry}: verdict - {_d.report} "
                f"(state: {_d.state}; verdict is never inflated here)")
        if _act == "index":
            return True, False, agent.privacyaudit_index()["index_text"]
        if _act == "verdict":
            return True, False, agent.privacyaudit_verdict()["verdict_text"]
        return True, False, agent.privacyaudit_status()["screen"]

    if command == "/accessibilityfinal":
        # M-262 terminal road: show the accessibility final gate held
        # this session - the public sets as
        # registry entries: one entry per set, naming
        # the word that set gives a single run and the
        # standing of its gate,
        # beside the run records held this session
        # (no run recorded when none is held) - show
        # the whole shipped registry, one check's entry,
        # the record held for one check and run, the
        # standing derived for one run, the run
        # verdict held, the index derived over every held
        # record, or the verdict derived for the
        # session, on the agent-layer parser + the pure
        # formatters. This road runs no benchmark,
        # downloads no set, executes no grading test, inflates
        # no result, probes no network and persists
        # nothing - holding and telling are words only.
        from .core.accessibility_final import format_check as _fmt_rcpart, format_checks as _fmt_rcparts, format_record as _fmt_rcrec
        from .agents.llm import parse_accessibilityfinal_args as _parse_rc
        try:
            _act, _tgt, _needs, _model = _parse_rc(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "checks":
            return True, False, _fmt_rcparts(agent.accessibilityfinal_checks())
        if _act == "check":
            try:
                _entry = agent.get_accessibilityfinal_check(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_rcpart(_entry)
        if _act == "record":
            try:
                _rec = agent.get_accessibilityfinal_record(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_rcrec(_rec)
        if _act == "standing":
            try:
                _standing = agent.accessibilityfinal_standing(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            _text = (f"{_tgt}: run "
                     f"{'held as answered' if _standing.held else 'open'} "
                     f"(stage: {_standing.stage}; "
                     f"grade: {_standing.grade})")
            for _gap in _standing.gaps:
                _text += f"\n  gap: {_gap}"
            return True, False, _text
        if _act == "reports":
            _reports = agent.accessibilityfinal_reports()
            if not _reports:
                return True, False, ("Run verdict: none held this "
                                     "session - the checks verdict run "
                                     "moves only as verdicts, and a verdict is "
                                     "never inflated here.")
            return True, False, "\n".join(
                f"{_d.book} -> {_d.entry}: verdict - {_d.report} "
                f"(state: {_d.state}; verdict is never inflated here)"
                for _d in _reports)
        if _act == "report":
            try:
                _d = agent.get_accessibilityfinal_report(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, (
                f"{_d.book} -> {_d.entry}: verdict - {_d.report} "
                f"(state: {_d.state}; verdict is never inflated here)")
        if _act == "index":
            return True, False, agent.accessibilityfinal_index()["index_text"]
        if _act == "verdict":
            return True, False, agent.accessibilityfinal_verdict()["verdict_text"]
        return True, False, agent.accessibilityfinal_status()["screen"]

    if command == "/docscompletion":
        # M-263 terminal road: show the docs completion held
        # this session - the public sets as
        # registry entries: one entry per set, naming
        # the word that set gives a single run and the
        # standing of its gate,
        # beside the run records held this session
        # (no run recorded when none is held) - show
        # the whole shipped registry, one guide's entry,
        # the record held for one guide and run, the
        # standing derived for one run, the run
        # verdict held, the index derived over every held
        # record, or the verdict derived for the
        # session, on the agent-layer parser + the pure
        # formatters. This road runs no benchmark,
        # downloads no set, executes no grading test, inflates
        # no result, probes no network and persists
        # nothing - holding and telling are words only.
        from .core.docs_completion import format_guide as _fmt_rcpart, format_guides as _fmt_rcparts, format_record as _fmt_rcrec
        from .agents.llm import parse_docscompletion_args as _parse_rc
        try:
            _act, _tgt, _needs, _model = _parse_rc(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "guides":
            return True, False, _fmt_rcparts(agent.docscompletion_guides())
        if _act == "guide":
            try:
                _entry = agent.get_docscompletion_guide(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_rcpart(_entry)
        if _act == "record":
            try:
                _rec = agent.get_docscompletion_record(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_rcrec(_rec)
        if _act == "standing":
            try:
                _standing = agent.docscompletion_standing(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            _text = (f"{_tgt}: run "
                     f"{'held as answered' if _standing.held else 'open'} "
                     f"(stage: {_standing.stage}; "
                     f"grade: {_standing.grade})")
            for _gap in _standing.gaps:
                _text += f"\n  gap: {_gap}"
            return True, False, _text
        if _act == "reports":
            _reports = agent.docscompletion_reports()
            if not _reports:
                return True, False, ("Run verdict: none held this "
                                     "session - the guides verdict run "
                                     "moves only as verdicts, and a verdict is "
                                     "never inflated here.")
            return True, False, "\n".join(
                f"{_d.book} -> {_d.entry}: verdict - {_d.report} "
                f"(state: {_d.state}; verdict is never inflated here)"
                for _d in _reports)
        if _act == "report":
            try:
                _d = agent.get_docscompletion_report(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, (
                f"{_d.book} -> {_d.entry}: verdict - {_d.report} "
                f"(state: {_d.state}; verdict is never inflated here)")
        if _act == "index":
            return True, False, agent.docscompletion_index()["index_text"]
        if _act == "verdict":
            return True, False, agent.docscompletion_verdict()["verdict_text"]
        return True, False, agent.docscompletion_status()["screen"]

    if command == "/docsmcp":
        # M-252 terminal road: show the docs MCP pattern held
        # this session - the export projects as
        # registry entries: one entry per project, naming
        # the word that project gives a single telling,
        # beside the record records held this session
        # (no record recorded when none is held) - show
        # the whole shipped registry, one project's entry,
        # the record held for one project and record, the
        # standing derived for one record, the bridge
        # proposal held, the index derived over every held
        # record, or the verdict derived for the
        # session, on the agent-layer parser + the pure
        # formatters. This road calls no host API,
        # performs no export, starts nothing, exports here
        # no bridge, probes no network and persists
        # nothing - holding and telling are words only.
        from .core.docs_mcp_pattern import format_project as _fmt_ciprov, format_projects as _fmt_ciprovs, format_record as _fmt_cirec
        from .agents.llm import parse_docsmcp_args as _parse_ci
        try:
            _act, _tgt, _needs, _model = _parse_ci(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "projects":
            return True, False, _fmt_ciprovs(agent.docsmcp_projects())
        if _act == "project":
            try:
                _entry = agent.get_docsmcp_project(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_ciprov(_entry)
        if _act == "record":
            try:
                _rec = agent.get_docsmcp_record(*_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_cirec(_rec)
        if _act == "standing":
            try:
                _standing = agent.docsmcp_standing(*_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            _text = (f"{_tgt[0]}/{_tgt[1]}: attachment "
                     f"{'held as bridge' if _standing.held else 'open'} "
                     f"(stage: {_standing.stage}; "
                     f"freshness: {_standing.freshness})")
            for _gap in _standing.gaps:
                _text += f"\n  gap: {_gap}"
            return True, False, _text
        if _act == "proposals":
            _proposals = agent.docsmcp_proposals()
            if not _proposals:
                return True, False, ("Bridge proposal: none held this "
                                     "session - the doors proposes bridge "
                                     "moves only as proposals, and a proposal is "
                                     "never attached here.")
            return True, False, "\n".join(
                f"{_d.bridge} -> {_d.record}: proposal - {_d.proposal} "
                f"(state: {_d.state}; proposal is never attached here)"
                for _d in _proposals)
        if _act == "propose":
            try:
                _d = agent.get_docsmcp_proposal(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, (
                f"{_d.bridge} -> {_d.record}: proposal - {_d.proposal} "
                f"(state: {_d.state}; proposal is never attached here)")
        if _act == "index":
            return True, False, agent.docsmcp_index()["index_text"]
        if _act == "verdict":
            return True, False, agent.docsmcp_verdict()["verdict_text"]
        return True, False, agent.docsmcp_status()["screen"]
    if command == "/mcpserver":
        # M-234 terminal target: show the exposure book
        # held this session - exposure services as data: one
        # record per exposure, held whole with the active
        # service it was held from, its one verifiable
        # stage at the house grain and its claims,
        # and the notes held as data beside them (the
        # shipped example book when none is held) - show
        # one exposure whole, the exposure one stage line
        # reaches, the exposures of one service, one held
        # view record, one held stance record, the index
        # derived from the whole book, the panel derived
        # from the whole book, or the verdict derived
        # for the whole book, on the pure layer parser +
        # formatters. This target builds no service,
        # executes nothing, banks nothing, pushes
        # nothing and persists nothing - holding and
        # telling are words only.
        from .core.mcp_server_v2 import format_exposure as _fmt_pg, format_book as _fmt_pbook, format_stage as _fmt_ptarget, format_index as _fmt_pindex, format_note as _fmt_pnote, format_panel as _fmt_ppanel, format_verdict as _fmt_pverdict, format_view as _fmt_pview, parse_exposure_args as _parse_p
        try:
            _act, _tgt = _parse_p(arguments)
        except ValueError as _exc:
            return True, False, str(_exc)
        if _act == "exposure":
            try:
                _item = agent.get_mcpserver_exposure(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pg(_item, agent.mcpserver_book())
        if _act == "stage":
            return True, False, _fmt_ptarget(
                agent.mcpserver_book(), _tgt)
        if _act == "service":
            return True, False, _fmt_pbook(
                agent.mcpserver_book(), _tgt)
        if _act == "view":
            try:
                _view = agent.get_mcpserver_view(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pview(_view)
        if _act == "note":
            try:
                _note = agent.mcpserver_book().note_for(_tgt)
            except (KeyError, ValueError) as _exc:
                return True, False, str(_exc)
            return True, False, _fmt_pnote(_note)
        if _act == "index":
            return True, False, _fmt_pindex(agent.mcpserver_book())
        if _act == "panel":
            return True, False, _fmt_ppanel(agent.mcpserver_book())
        if _act == "verdict":
            return True, False, _fmt_pverdict(agent.mcpserver_book())
        return True, False, agent.mcpserver_status()["screen"]
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
