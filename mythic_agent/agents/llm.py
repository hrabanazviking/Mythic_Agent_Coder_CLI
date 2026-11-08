
__all__ = [
    "AGENT_REGISTRY",
    "APIConnectionError",
    "APIStatusError",
    "Agent",
    "AgentManager",
    "Any",
    "Callable",
    "CancellableChatClient",
    "CoreMemoryManager",
    "DEFAULT_SYSTEM_PROMPT",
    "Path",
    "ProviderCredentialsError",
    "SecretRedactor",
    "SessionStore",
    "ToolPolicy",
    "TurnCancelled",
    "TurnResult",
    "agent_manager",
    "build_provider_client",
    "config_manager",
    "diagnose_provider",
    "execute_tool",
    "get_agent_tools",
    "get_vector_provider",
    "is_loopback_url",
    "policy_mode",
    "protect_logging",
    "publish_sync",
    "resolve_api_key",
    "runtime_settings",
    "subscribe",
]
import json
import os
import time
import logging
import threading
import queue
import random
from pathlib import Path
from typing import Any, Callable

from openai import APIConnectionError, APIStatusError

from .tools import execute_tool, get_agent_tools
from ..core.config_manager import config_manager
from ..constants import DEFAULT_SYSTEM_PROMPT
from ..core.secure_api import publish_sync, subscribe
from ..core.runtime import TurnCancelled, TurnResult, runtime_settings
from ..core.redaction import SecretRedactor, protect_logging
from ..core.sessions import SessionStore
from ..core.policy import ToolPolicy, policy_mode
from ..core.execution import CancellableChatClient, is_loopback_url
from ..core.exceptions import MythicProviderError
from ..memory.core_memory import CoreMemoryManager
from ..memory.vector_db import get_vector_provider

# Global registry of live sub-agent instances keyed by name.
AGENT_REGISTRY: dict[str, "Agent"] = {}

# Placeholder credential for loopback endpoints. The OpenAI-compatible SDK
# requires a non-empty key string, but local endpoints need no real
# credential; this value is never sent to a remote host.
_LOOPBACK_API_KEY = "local"


class ProviderCredentialsError(MythicProviderError, RuntimeError):
    """A remote endpoint needs a credential and none is configured.

    Raised before any network request, with a redacted remedy. Loopback
    endpoints never raise this: they may operate without auth.
    """


def _key_env_hint(base_url: str) -> str:
    """Name the environment variable that carries this endpoint's key."""
    if "deepseek" in base_url:
        return "DEEPSEEK_API_KEY"
    if "openrouter" in base_url:
        return "OPENROUTER_API_KEY"
    if "anthropic" in base_url:
        return "ANTHROPIC_API_KEY"
    return "OPENAI_API_KEY"


def _missing_key_remedy(base_url: str) -> str:
    """The one plain remedy for a door with no key (M-032).

    The wording is M-032's :func:`missing_key_message`: it asks
    once, kindly, naming the Kista reference to add and the
    environment variable — config files hold references, never
    secrets. Loopback endpoints need no key.
    """
    from ..core.key_custody import missing_key_message

    return missing_key_message(base_url)


def resolve_api_key(config: dict[str, Any], base_url: str) -> str | None:
    """Return the configured credential for an endpoint, if any.

    A stored Kista reference (M-032) resolves through Kista —
    its vault file, then the environment under the reference's
    own name; an unresolved reference returns None here (no
    other door's key, and not the door's hint variable either,
    is substituted for the key the reference names). A legacy
    plaintext stored key is itself. Otherwise the provider's
    environment variable answers. Returns None when nothing is
    configured; it is the caller's job to decide whether that
    is an error (remote) or fine (loopback).
    """
    from ..core.key_custody import is_reference, stored_key_for

    stored = config.get("api_keys", {}).get(base_url)
    if stored:
        resolved = stored_key_for(config, base_url)
        if resolved:
            return resolved
        if is_reference(stored):
            return None
    return os.environ.get(_key_env_hint(base_url))


def build_provider_client(config: dict[str, Any],
                          cancel: threading.Event | None = None) -> CancellableChatClient:
    """Construct the provider HTTP client honoring S07 admission rules.

    Loopback endpoints operate without auth (an inert placeholder satisfies
    the SDK) and never consult proxy environment. Remote endpoints without
    a configured credential fail here, before any network request, with a
    redacted remedy; invented dummy credentials are never substituted.
    """
    base_url = config.get("base_url", config_manager.DEFAULT_BASE_URL)
    settings = runtime_settings(config)
    cancel = cancel if cancel is not None else threading.Event()
    if is_loopback_url(base_url):
        api_key = resolve_api_key(config, base_url) or _LOOPBACK_API_KEY
        return CancellableChatClient(base_url, api_key, cancel,
                                     settings["request_timeout"],
                                     settings["cancellation_poll_interval"],
                                     trust_env=False)
    api_key = resolve_api_key(config, base_url)
    if not api_key:
        raise ProviderCredentialsError(_missing_key_remedy(base_url))
    return CancellableChatClient(base_url, api_key, cancel,
                                 settings["request_timeout"],
                                 settings["cancellation_poll_interval"])


def diagnose_provider(config: dict[str, Any]) -> dict[str, Any]:
    """Offline provider diagnostics: configuration only, no network.

    Reports configured values separately from anything verified live, and
    never includes key material.
    """
    base_url = config.get("base_url", config_manager.DEFAULT_BASE_URL)
    model = config.get("model", "") or ""
    loopback = is_loopback_url(base_url)
    settings = runtime_settings(config)
    return {
        "base_url": base_url,
        "base_url_valid": config_manager._valid_url(base_url),
        "loopback": loopback,
        "model": model,
        "model_configured": bool(model.strip()),
        "api_key_configured": bool(resolve_api_key(config, base_url)),
        "auth_required": not loopback,
        "streaming": bool(config.get("streaming", False)),
        "retry_budget": settings["max_retries"],
        "request_timeout": settings["request_timeout"],
    }


def _retry_delay(exc: Exception, attempt: int, settings: dict[str, Any]) -> float:
    """Capped backoff for one retry: server Retry-After wins when present.

    Thin wrapper over :func:`mythic_agent.core.retry_honesty.delay_for`
    (M-035); the semantics are unchanged.
    """
    from ..core.retry_honesty import delay_for

    return delay_for(exc, attempt, settings)


def _is_transient(exc: Exception) -> bool:
    """Classify provider errors: retry connection issues and 408/409/429/5xx.

    Auth (401/403), bad model (404), invalid requests (400/422), and
    capability failures fail promptly and are never retried. Thin
    wrapper over :func:`mythic_agent.core.retry_honesty.is_transient_error`
    (M-035); the classification is unchanged.
    """
    from ..core.retry_honesty import is_transient_error

    return is_transient_error(exc)


class _StreamAccumulator:
    """Accumulate SSE text/tool deltas into one normalized assistant message.

    Text fragments publish incrementally (each exactly once); indexed tool
    name/argument fragments reassemble per tool-call index. Tools execute
    only after the completed response validates: incomplete fragments or a
    malformed stream raise before anything becomes executable.
    """

    def __init__(self, agent_name: str):
        self._agent_name = agent_name
        self.reset()

    def reset(self) -> None:
        self._content: list[str] = []
        self._tool_calls: dict[int, dict[str, str]] = {}
        self._finish_reason: str | None = None
        self._usage: Any = None
        self._chunks_seen = 0

    @property
    def emitted(self) -> bool:
        """True once any chunk arrived: never retry after a partial response."""
        return self._chunks_seen > 0

    @property
    def text(self) -> str:
        return "".join(self._content)

    def __call__(self, chunk: Any) -> None:
        self._chunks_seen += 1
        for choice in chunk.choices or []:
            if choice.finish_reason:
                self._finish_reason = choice.finish_reason
            delta = choice.delta
            if delta is None:
                continue
            content = getattr(delta, "content", None)
            if content:
                self._content.append(content)
                publish_sync("agent_chat_chunk", agent_name=self._agent_name, text=content)
            for call in getattr(delta, "tool_calls", None) or []:
                index = getattr(call, "index", 0) or 0
                slot = self._tool_calls.setdefault(index, {"id": "", "name": "", "arguments": ""})
                if call.id:
                    slot["id"] = call.id
                function = call.function
                if function is not None:
                    if function.name:
                        slot["name"] = function.name
                    if function.arguments:
                        slot["arguments"] += function.arguments
        usage = getattr(chunk, "usage", None)
        if usage is not None:
            self._usage = usage

    def message(self) -> dict[str, Any]:
        """Return the normalized assistant message; raise on malformed streams."""
        if not self._chunks_seen:
            raise RuntimeError("Provider returned an empty stream")
        calls = []
        for index in sorted(self._tool_calls):
            slot = self._tool_calls[index]
            if not slot["id"] or not slot["name"]:
                raise RuntimeError(
                    "Provider stream ended with incomplete tool call fragments; "
                    "refusing to execute partial calls")
            calls.append({"id": slot["id"], "type": "function",
                          "function": {"name": slot["name"], "arguments": slot["arguments"]}})
        text = self.text
        if not text and not calls:
            raise RuntimeError("Provider returned an empty assistant response")
        message: dict[str, Any] = {"role": "assistant", "content": text or None}
        if calls:
            message["tool_calls"] = calls
        return message

def _role_route_for(config: dict, name: str):
    """The explicit role route for crew member *name*, or None (M-029).

    Shared by :class:`Agent` (route changes reaching live members)
    and :class:`AgentManager` (routes applied at spawn): the route
    is read from *config* — the manager has no config of its own, so
    it passes the freshly loaded one. An office with no explicit
    route, a name no office claims, and a malformed stored route
    all yield None here: spawn never breaks over routing, and the
    malformed route still surfaces at set/show time.
    """
    from ..core.role_routing import office_for_agent_name, resolve_route

    office = office_for_agent_name(name)
    if office is None:
        return None
    try:
        route = resolve_route(config, office)
    except ValueError:
        return None
    return route if route.source == "route" else None




class _CheckpointTimelineAdapter:
    """M-075 checkpoints speaking the M-077 seam (banking wiring).

    Coordinator wiring at M-077 banking: M-077's undo
    timeline reads its checkpoint strand through the
    ``checkpoint_timeline_source`` seam and M-075
    (Checkpoints v2) is banked, so the Agent carries
    this adapter by default (see the Agent property).
    Entries are M-075's own checkpoints (id as text,
    name as label; certainty is not claimed, so the
    seam's honest ``unknown`` default stands). Restore
    maps the seam id back to the checkpoint's name and
    drives the Agent's own M-075 restore road, whose
    dirty-tree judgement and gate refusals propagate
    unchanged; the outcome is returned in plain words,
    as the seam requires.
    """

    def __init__(self, agent: Any) -> None:
        self._agent = agent

    def list_checkpoint_entries(self) -> list[dict[str, Any]]:
        from ..core import checkpoints

        store = checkpoints.CheckpointStore(
            self._agent.project_root)
        return [{"id": str(cp.id), "name": cp.name}
                for cp in store.list_checkpoints()]

    def restore_checkpoint(self, checkpoint_id: str) -> str:
        from ..core import checkpoints

        store = checkpoints.CheckpointStore(
            self._agent.project_root)
        for cp in store.list_checkpoints():
            if str(cp.id) == str(checkpoint_id):
                record = self._agent.restore_checkpoint(cp.name)
                return (f"Restored checkpoint {cp.name!r}: "
                        f"{record['restored']} file(s) restored, "
                        f"{record['removed']} removed, "
                        f"{record['unchanged']} unchanged.")
        raise ValueError(
            f"no checkpoint with id {checkpoint_id!r} in "
            "this workspace; nothing was restored")

class Agent:
    def __init__(self, project_root: Path | None = None, name: str = "Primary", config: dict[str, Any] | None = None):
        import copy
        self.config = copy.deepcopy(config) if config is not None else config_manager.load_config()
        self.redactor = SecretRedactor(self.config)
        protect_logging(self.redactor)
        from ..core.workspace import resolve_workspace, workspace_id
        self.project_root = resolve_workspace(project_root, self.config)
        self.name = name

        self.total_tokens = 0
        if "api_keys" not in self.config:
            self.config["api_keys"] = {}
            
        self.messages = []
        self.inbox = queue.Queue()
        self._lock = threading.Lock()
        self._turn_lock = threading.Lock()
        self._cancel = threading.Event()
        self._pending_history_action = None
        self.session_id = None
        self._session_store = None
        self._session_status = "idle"
        self._closed = False
        self.last_result = TurnResult("idle")
        self.last_retry_report = None
        from ..core.rate_limit_weather import shared_board

        # M-036: the crew-shared rate-limit weather board — one
        # member's limit signal is every member's weather.
        self._weather_board = shared_board()
        self.tui_app = None
        self.tool_policy = ToolPolicy("read-only")
        self._permission_override = None
        self._current_plan = None  # M-100: the held plan (Plan or None)
        self._background_registry = None  # M-103: held jobs registry
        self._background_processes: dict[str, Any] = {}
        self._background_lock = threading.RLock()
        self._background_announced: set[str] = set()
        self.active_task_start_time = None
        self.rebuild_system_prompt()
        
        self.core_memory = CoreMemoryManager(
            self.name, workspace_id=workspace_id(self.project_root)
        )
        
        # Initialize Vector DB
        base_url = self.config.get("base_url", config_manager.DEFAULT_BASE_URL)
        api_key = self.get_api_key(base_url)
        provider = self.config.get("vector_db_provider", "lightweight")
        self.vector_db = get_vector_provider(provider, self.name, base_url, api_key)
        if hasattr(self.vector_db, "bind_execution"):
            self.vector_db.bind_execution(self._cancel, self.config)
        
        self.inject_mythic_agents()
        
        # Subscribe to Parity Commands
        subscribe("agent_clear_history", self._handle_clear_history)
        subscribe("agent_compact_history", self._handle_compact_history)

    def attach_session(self, store: SessionStore | None = None, resume: str | None = None) -> str:
        """Attach once; retain the lease until close so stale clients cannot overwrite."""
        with self._turn_lock:
            if self.session_id or self._closed:
                raise RuntimeError("Agent already attached or closed")
            store = store or SessionStore(self.project_root, config_manager.MYTHIC_DIR, self.redactor)
            if store.workspace != self.project_root:
                raise ValueError("Session store belongs to a different workspace")
            if resume is not None:
                data = store.resume(resume)
                with self._lock:
                    self.messages = data["context"]
                self.total_tokens = data["total_tokens"]
                self._session_status = data["status"]
                outcome = data["outcome"] or {}
                self.last_result = TurnResult(data["status"], outcome.get("text", ""),
                                              outcome.get("error"), self.total_tokens)
                session_id = resume
            else:
                session_id = store.create(self.history_snapshot(), {
                    "agent_name": self.name, "model": self.config.get("model"),
                    "base_url": self.config.get("base_url"),
                })
            self._session_store, self.session_id = store, session_id
            if resume is not None:
                self._restore_salvaged_partial()
            self._load_project_policy_at_start()
            return session_id

    def _restore_salvaged_partial(self) -> None:
        """Restore a killed stream's partial on resume (M-034).

        The ``stream_interrupted`` checkpoint is the journal's
        record of a stream that died mid-answer. When the live
        turn lived long enough, it salvaged the partial itself
        (see :meth:`_request_streaming`); when the process died
        with the turn, the checkpoint is all that remains. On
        resume, the latest such checkpoint whose partial is not
        already present as a salvage message in the loaded
        context is salvaged here — appended through
        :meth:`_append_message`, so the restore itself is
        journaled, and recorded with a
        ``stream_salvaged_on_resume`` event. A failure to scan
        never breaks a normal resume: it is logged, and the
        session continues without the restore.
        """
        from ..core.streaming_discipline import (
            is_partial_message,
            partial_text_of,
            salvage_message,
        )

        try:
            if not self._session_store or not self.session_id:
                return
            events = self._session_store.export(self.session_id)["events"]
            partial_text = None
            for event in events:
                if event.get("type") == "stream_interrupted":
                    text = event.get("partial_text")
                    if isinstance(text, str) and text.strip():
                        partial_text = text
            if partial_text is None:
                return
            for message in self.history_snapshot():
                if is_partial_message(message) \
                        and partial_text_of(message) == partial_text:
                    return  # already salvaged in the loaded context
            message = salvage_message(partial_text)
            if message is None:
                return
            self._append_message(message)
            self._checkpoint({"type": "stream_salvaged_on_resume",
                              "partial_chars": len(partial_text)})
        except Exception:
            logging.exception(
                "Salvaged-partial restore failed; resume continues "
                "without it")

    def close(self) -> None:
        from ..core.secure_api import unsubscribe
        with self._turn_lock:
            if self._session_store and self.session_id:
                self._session_store.release(self.session_id)
            self._closed = True
            unsubscribe("agent_clear_history", self._handle_clear_history)
            unsubscribe("agent_compact_history", self._handle_compact_history)

    def bind_tui(self, app: Any, mode: str | None = None) -> None:
        """Bind human approvals to this agent's cancellation event."""
        from .tools import prompt_approval_sync
        self.tui_app = app
        mode = mode or policy_mode(self.config, override=self._permission_override)
        def approve(name, arguments):
            # M-096: a remembered approval with the exact
            # scope answers first - the standing answer the
            # user already gave for this command in this
            # project - and the prompt is never raised.
            if self.remembered_approval_allows_tool(name, arguments):
                # M-109: a remembered approval is a human
                # approval already given - it is trailed as
                # one, through the audit road.
                self._note_audit_approval(
                    name, True, "a remembered approval")
                return True
            # M-116: the fresh ask is shaped as one
            # approval moment from this real call and
            # held for the session before the prompt
            # is raised - shaping is news, never a gate.
            self._note_approval_moment(name, arguments)
            settings = runtime_settings(self.config)
            description = self.redactor.text(name + ": " + json.dumps(arguments, ensure_ascii=False))
            decided = prompt_approval_sync(description, app, self._cancel, settings["approval_timeout"])
            # M-109: the human's answer at the prompt is
            # trailed as an approval, granted or refused.
            self._note_audit_approval(
                name, decided, "the approval prompt")
            return decided
        self.tool_policy = ToolPolicy(mode, approve)

    def change_workspace(self, root: Path | str) -> None:
        """Switch only between turns; start isolated context and keep the old transcript."""
        from ..core.workspace import resolve_workspace
        root = resolve_workspace(root)
        if root == self.project_root:
            return
        if not self._turn_lock.acquire(blocking=False):
            raise RuntimeError("Stop the current turn before changing workspace")
        try:
            if self._closed:
                raise RuntimeError("Agent is closed")
            messages = self.history_snapshot()[:1]
            if self._session_store:
                store = SessionStore(root, config_manager.MYTHIC_DIR, self.redactor)
                new_id = store.create(messages, {"agent_name": self.name,
                    "model": self.config.get("model"), "base_url": self.config.get("base_url")})
                self._session_store.release(self.session_id)
                self._session_store, self.session_id = store, new_id
            self.project_root = root
            with self._lock:
                self.messages = messages
            self.total_tokens = 0
            self._session_status = "idle"
            self.last_result = TurnResult("idle")
        finally:
            self._turn_lock.release()

    def _checkpoint(self, event: dict[str, Any] | None = None, outcome: dict[str, Any] | None = None,
                    context: list[dict[str, Any]] | None = None) -> None:
        if self._session_store:
            if self._session_store.workspace != self.project_root:
                raise ValueError("Workspace changed without rotating the session")
            self._session_store.checkpoint(self.session_id, context if context is not None else self.history_snapshot(),
                                           self._session_status, self.total_tokens, outcome, event)

    def _append_message(self, message: dict[str, Any]) -> None:
        context = self.history_snapshot() + [message]
        self._checkpoint({"type": "message", "message": message}, context=context)
        with self._lock:
            self.messages = context
        
    def _handle_clear_history(self, target_agent: str, force: bool = False) -> None:
        if target_agent != self.name:
            return
        if not force and not self._turn_lock.acquire(blocking=False):
            self._pending_history_action = "clear"
            return
        try:
            context = self.history_snapshot()[:1]
            self._checkpoint({"type": "context_cleared"}, context=context)
            with self._lock:
                self.messages = context
        finally:
            if not force:
                self._turn_lock.release()
        publish_sync("agent_chat_chunk", agent_name=self.name,
                     text="\nConversation cleared.\n")

    def _handle_compact_history(self, target_agent: str, force: bool = False) -> None:
        if target_agent != self.name:
            return
        if not force and not self._turn_lock.acquire(blocking=False):
            self._pending_history_action = "compact"
            return
        try:
            with self._lock:
                boundaries = [i for i, message in enumerate(self.messages)
                              if message.get("role") == "user"]
                if len(boundaries) < 2:
                    return
                boundary = boundaries[-1]
                archived = self.messages[1:boundary]
            # Preserve complete turns before changing the selected context.
            try:
                self.vector_db.insert("Archived Context: " + json.dumps(archived))
            except Exception:
                logging.exception("Archival failed; context preserved")
                return
            context = self.history_snapshot()[:1] + self.history_snapshot()[boundary:]
            self._checkpoint({"type": "context_compacted", "archived_messages": len(archived)}, context=context)
            with self._lock:
                self.messages = context
        finally:
            if not force:
                self._turn_lock.release()
        publish_sync("agent_chat_chunk", agent_name=self.name,
                     text="\nOlder complete turns archived.\n")

    def cancel(self) -> None:
        """Interrupt retry waits and stop at the next runtime boundary."""
        self._cancel.set()

    def history_snapshot(self) -> list[dict[str, Any]]:
        import copy
        with self._lock:
            return copy.deepcopy(self.messages)

    def add_context(self, content: str) -> None:
        """Add explicit user context between complete turns."""
        with self._turn_lock:
            self._append_message({"role": "user", "content": content})

    def get_user_context(self) -> str:
        user_name = self.config.get("user_name", "").strip()
        user_data = self.config.get("user_data", "").strip()
        if not user_name and not user_data:
            return ""
        
        context = "\n\nUSER CONTEXT:\n"
        if user_name:
            context += f"The user's name is {user_name}.\n"
        if user_data:
            context += f"Data about the user:\n{user_data}\n"
        return context

    def rebuild_system_prompt(self) -> None:
        if self.name == "Primary":
            system_prompt = self.config.get("system_prompt", DEFAULT_SYSTEM_PROMPT)
        else:
            sub_agents = self.config.get("sub_agents", [])
            sub_config = next((s for s in sub_agents if s.get("name") == self.name), None)
            system_prompt = sub_config.get("prompt", "You are a helpful sub-agent.") if sub_config else "You are a helpful sub-agent."

        global_rules = self.config.get("global_rules", "").strip()
        status_rule = "You MUST use the `update_status` tool to autosave your current project status and keep track of what is going on."
        diff_rule = "CRITICAL: If you modify any files during your turn, you MUST include a summary of the files changed at the very end of your final response, explicitly showing the (+X, -Y) lines added and removed. The write_file and replace_file_content tools will tell you these numbers upon success. Format it exactly like this:\n[bold cyan]Files Changed:[/bold cyan]\n[green]+ X[/green] [red]- Y[/red] path/to/file.py"
        
        if global_rules:
            system_prompt += f"\n\nGLOBAL RULES (You must strictly follow these):\n{global_rules}\n- {status_rule}\n- {diff_rule}"
        else:
            system_prompt += f"\n\nGLOBAL RULES:\n- {status_rule}\n- {diff_rule}"

        if self.config.get("mythic_engineering_mode"):
            system_prompt += "\n\n=== MYTHIC ENGINEERING MODE PROTOCOL ACTIVATED ===\n"
            
            # Dynamically resolve the path to the skill file relative to the mythic_agent package
            # mythic-agent/mythic_agent/agents/llm.py -> parent.parent.parent -> mythic-agent
            try:
                from ..resources import engineering_protocol
                system_prompt += "\n[CORE PROTOCOL LOADED FROM DISK]\n"
                system_prompt += engineering_protocol()
            except Exception as e:
                logging.error(f"Failed to load Mythic Engineering skill file: {e}. Using fallback.")
                system_prompt += "\n[FALLBACK CORE PROTOCOL]\n"
                system_prompt += "You are the orchestrator of an Architecture-First, intuition-led, document-guided development process."
                system_prompt += "\n1. Vision before implementation. Architecture before patching."
                system_prompt += "\n2. MD Protocol: Markdown as living memory (README.md, ARCHITECTURE.md, etc)."
                system_prompt += "\n3. ALWAYS delegate and consult your 6 included Sub-Agents (Skald, Architect, Forge Worker, Auditor, Cartographer, Scribe) using the delegate_task tool when tackling large problems."
                system_prompt += "\n4. Reality outranks theory. Refactor by ownership. Invariants matter."

        system_prompt += self.get_user_context()
        
        if hasattr(self, "core_memory"):
            system_prompt += self.core_memory.format_for_prompt()

        system_prompt += self._instruction_context_block()

        with self._lock:
            if not self.messages:
                self.messages.append({"role": "system", "content": system_prompt})
            elif self.messages[0].get("role") == "system":
                self.messages[0]["content"] = system_prompt
            else:
                self.messages.insert(0, {"role": "system", "content": system_prompt})
        self._checkpoint({"type": "system_prompt_updated", "message": self.history_snapshot()[0]})
            
    def _instruction_context_block(self) -> str:
        """Repository instruction layers for the system prompt (Slice 054/055).

        Inert unless the ``context_compiler_enabled`` runtime setting is
        true.  Failures degrade to no extra context, never a broken prompt.
        """
        try:
            settings = runtime_settings(self.config)
        except Exception:
            return ""
        if not settings.get("context_compiler_enabled") or not self.project_root:
            return ""
        try:
            from mythic_agent.context import instruction_context_block
            return instruction_context_block(self.config, self.project_root)
        except Exception:
            logging.exception("Context compiler instruction hook failed; continuing")
            return ""

    def _compile_prompt_context(self, prompt: str) -> str:
        """File context for one user query (Slices 056-060).

        Inert unless ``context_compiler_enabled`` is true or the turn is
        already cancelled.  Failures degrade to no extra context.
        """
        try:
            settings = runtime_settings(self.config)
        except Exception:
            return ""
        if not settings.get("context_compiler_enabled") or not self.project_root:
            return ""
        if self._cancel.is_set():
            return ""
        try:
            from mythic_agent.context import prompt_file_context
            return prompt_file_context(self.config, self.project_root, prompt,
                                       cancel_event=self._cancel,
                                       redactor=self.redactor)
        except Exception:
            logging.exception("Context compiler prompt hook failed; continuing")
            return ""

    def inject_mythic_agents(self) -> None:
        """Inject the core Mythic Engineering sub-agents if they don't exist."""
        from ..constants import DEFAULT_SUBAGENTS
        
        current_agents = self.config.get("sub_agents", [])
        existing_names = {a.get("name") for a in current_agents}
        
        added = False
        for agent in DEFAULT_SUBAGENTS:
            if agent["name"] not in existing_names:
                current_agents.append(agent)
                added = True
                
        if added:
            self.config["sub_agents"] = current_agents
        
    def save_config(self) -> bool:
        return config_manager.save_config(self.config)
        
    def get_api_key(self, base_url: str) -> str | None:
        return resolve_api_key(self.config, base_url)

    def get_client(self) -> CancellableChatClient:
        return build_provider_client(self.config, self._cancel)
        
    def set_model(self, model: str, base_url: str, api_key: str | None = None) -> None:
        """Legacy spelling of :meth:`switch_model` (model + door URL).

        Kept for the callers that predate M-028; the switch is now
        journaled like every other switch when a session is attached.
        """
        self.switch_model(model, base_url=base_url, api_key=api_key)

    def switch_model(self, model: str | None = None, *, provider: str | None = None,
                     base_url: str | None = None, api_key: str | None = None,
                     reason: str | None = None) -> dict[str, Any]:
        """Change this agent's model and/or provider mid-session (M-028).

        The session, its history and plan context, its token count,
        and the whole live crew survive the switch untouched — only
        this agent's own model/provider selection changes. The
        switch happens only between turns: called while a turn is
        running it raises and changes nothing.

        The request is validated by
        :func:`mythic_agent.core.model_switch.resolve_switch` before
        anything mutates (unknown providers and doors the live
        session cannot speak are refused plainly, with nothing
        changed). When a session is attached, the switch is then
        journaled *first* — a ``model_switched`` checkpoint event
        carrying the from/to selections and the reason if given, on
        the unchanged history — and only then applied and saved; if
        the save fails, the previous selection is restored exactly
        and a compensating ``model_switch_reverted`` event is
        journaled, so the journal never claims a switch that did
        not take effect.

        Returns the switch record (from/to/reason/session_id/
        journaled) built by the resolver.
        """
        import copy

        from ..core.model_switch import resolve_switch

        if api_key is not None and not isinstance(api_key, str):
            raise ValueError("API key must be text")
        target = resolve_switch(self.config, model=model, provider=provider,
                                base_url=base_url, reason=reason)
        if not self._turn_lock.acquire(blocking=False):
            raise RuntimeError(
                "Finish the current turn before switching models; "
                "the session, its plan and the crew are unchanged.")
        try:
            if self._closed:
                raise RuntimeError("Agent is closed")
            journaled = False
            if self._session_store and self.session_id:
                self._checkpoint(target.event())
                journaled = True
            previous = copy.deepcopy(self.config)
            self.config["model"] = target.to_model
            self.config["base_url"] = target.to_base_url
            if "api_keys" not in self.config:
                self.config["api_keys"] = {}
            if api_key:
                self.config["api_keys"][target.to_base_url] = api_key
            if not self.save_config():
                self.config = previous
                if journaled:
                    try:
                        self._checkpoint({
                            "type": "model_switch_reverted",
                            "to": {"model": target.from_model,
                                   "base_url": target.from_base_url,
                                   "provider": target.from_provider},
                            "reason": "The model preference could not be "
                                      "saved; the previous selection was "
                                      "preserved.",
                        })
                    except Exception:
                        pass  # the RuntimeError below is the truth owed
                raise RuntimeError(
                    "Model preference could not be saved; "
                    "previous settings were preserved")
            self.redactor = SecretRedactor(self.config)
            protect_logging(self.redactor)
            return target.record(self.session_id, journaled)
        finally:
            self._turn_lock.release()

    def active_provider(self) -> str | None:
        """The registry provider this agent's current door is, or None.

        Exact endpoint inference over the M-019 registry data (see
        :func:`mythic_agent.core.model_switch.infer_provider`): a
        custom door truthfully has no provider name.
        """
        from ..core.model_switch import infer_provider

        return infer_provider(self.config.get("base_url"))

    def role_route(self, office_or_name: str) -> dict[str, Any]:
        """The effective route for an office or crew member (M-029).

        Accepts an office id (``architect``) or a crew member's name
        (``Architect - Rúnhild Svartdóttir``); a name no office
        claims raises KeyError. The route is the office's explicit
        ``role_routes`` entry when one is set, else the session
        default — the fallback is part of the answer, never hidden.
        """
        from ..core.role_routing import (
            office_for_agent_name,
            office_ids,
            resolve_route,
        )

        office = office_or_name
        if office not in office_ids():
            office = office_for_agent_name(office_or_name)
            if office is None:
                raise KeyError(
                    f"No office claims {office_or_name!r}; routes are "
                    "set per office (architect, forge_worker, "
                    "cartographer, auditor, scribe, skald, guardian, "
                    "polymath)")
        route = resolve_route(self.config, office)
        return {"office": route.office, **route.selection(),
                "source": route.source}

    def set_role_route(self, office: str, *, model: str | None = None,
                       provider: str | None = None,
                       base_url: str | None = None) -> dict[str, Any]:
        """Set one office's model route (M-029).

        The change is validated by
        :mod:`mythic_agent.core.role_routing` (through the M-028
        resolver) before anything mutates. When a session is
        attached, the change is journaled first as a
        ``role_route_changed`` event; if the config save fails, the
        previous routes are restored exactly and a compensating
        ``role_route_reverted`` event is journaled. Crew members
        take the new route when spawned, or at once if they are
        already spawned and idle (see :meth:`_apply_role_routes`).
        """
        return self._change_role_route(office, model=model,
                                       provider=provider,
                                       base_url=base_url, clear=False)

    def clear_role_route(self, office: str) -> dict[str, Any]:
        """Clear one office's route back to the session default (M-029)."""
        return self._change_role_route(office, clear=True)

    def _change_role_route(self, office: str, *, model: str | None = None,
                           provider: str | None = None,
                           base_url: str | None = None,
                           clear: bool = False) -> dict[str, Any]:
        import copy

        from ..core import role_routing

        if clear:
            new_routes, change = role_routing.clear_route(self.config, office)
        else:
            new_routes, change = role_routing.set_route(
                self.config, office, model=model, provider=provider,
                base_url=base_url)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[role_routing.ROUTES_KEY] = new_routes
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "role_route_reverted",
                        "office": change.office,
                        "reason": "The route change could not be "
                                  "saved; the previous routes were "
                                  "preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Role route could not be saved; previous routes "
                "were preserved")
        self._apply_role_routes()
        return change.record(self.session_id, journaled)

    def fallback_status(self) -> dict[str, Any]:
        """The fallback chain and its standing permission (M-030).

        The chain exactly as stored (validated — a malformed
        stored chain raises, never vanishes), the permission
        exactly as stored, and the session's current door. This is
        the answer ``/fallback`` shows; nothing about it is hidden.
        """
        from ..core import fallback_chain
        from ..core.model_switch import infer_provider

        entries = fallback_chain.chain_from_config(self.config)
        return {
            "permission": fallback_chain.permission_from_config(self.config),
            "chain": [entry.selection() for entry in entries],
            "current": {"model": self.config.get("model"),
                        "base_url": self.config.get("base_url"),
                        "provider": infer_provider(self.config.get("base_url"))},
        }

    def set_fallback_permission(self, enabled: bool) -> dict[str, Any]:
        """Give or withdraw standing fallback permission (M-030).

        Validated by :mod:`mythic_agent.core.fallback_chain` before
        anything mutates; journaled first as a
        ``fallback_permission_changed`` event when a session is
        attached; a failed save restores the previous value exactly
        and journals a compensating ``fallback_change_reverted``.
        """
        return self._change_fallback("permission", enabled=enabled)

    def add_fallback_entry(self, *, model: str | None = None,
                           provider: str | None = None,
                           base_url: str | None = None) -> dict[str, Any]:
        """Append one door to the fallback chain (M-030).

        The entry is validated through the M-028 resolver (native
        doors refused plainly, the current door refused, duplicates
        refused) before anything mutates; journaled first as a
        ``fallback_chain_changed`` event; a failed save restores
        the previous chain exactly and journals the revert.
        """
        return self._change_fallback("add", model=model,
                                     provider=provider, base_url=base_url)

    def clear_fallback_chain(self) -> dict[str, Any]:
        """Empty the fallback chain (M-030). Journaled like any change."""
        return self._change_fallback("clear")

    def _change_fallback(self, action: str, *, enabled: bool | None = None,
                         model: str | None = None,
                         provider: str | None = None,
                         base_url: str | None = None) -> dict[str, Any]:
        import copy

        from ..core import fallback_chain

        if action == "permission":
            new_value, change = fallback_chain.set_permission(
                self.config, enabled)
            key = fallback_chain.PERMISSION_KEY
        elif action == "add":
            new_value, change = fallback_chain.set_chain_entry(
                self.config, model=model, provider=provider,
                base_url=base_url)
            key = fallback_chain.CHAIN_KEY
        elif action == "clear":
            new_value, change = fallback_chain.clear_chain(self.config)
            key = fallback_chain.CHAIN_KEY
        else:  # pragma: no cover - internal dispatch only
            raise ValueError(f"Unknown fallback change {action!r}")
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[key] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "fallback_change_reverted",
                        "kind": change.kind,
                        "reason": "The fallback change could not be "
                                  "saved; the previous chain and "
                                  "permission were preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Fallback change could not be saved; previous "
                "settings were preserved")
        return change.record(self.session_id, journaled)

    def cost_routing_status(self) -> dict[str, Any]:
        """The cost-routing setting and its candidate doors (M-031).

        The setting exactly as stored (validated — a malformed
        stored value raises, never vanishes), every configured
        door the router may choose between with its costs-table
        yardstick price (None = unpriced, never claimed cheaper),
        and the task classes. This is the answer ``/costroute``
        shows; nothing about it is hidden.
        """
        from ..core import cost_routing

        return {
            "enabled": cost_routing.enabled_from_config(self.config),
            "doors": [
                {**door.selection(),
                 "unit_cost": cost_routing.unit_cost(door.model)}
                for door in cost_routing.candidate_doors(self.config)],
            "task_classes": [
                {"id": task.id, "title": task.title, "plain": task.plain}
                for task in cost_routing.TASK_CLASSES],
        }

    def set_cost_routing(self, enabled: bool) -> dict[str, Any]:
        """Turn cost-aware routing on or off (M-031).

        Validated by :mod:`mythic_agent.core.cost_routing` before
        anything mutates; journaled first as a
        ``cost_routing_changed`` event when a session is attached;
        a failed save restores the previous value exactly and
        journals a compensating ``cost_routing_reverted``.
        """
        import copy

        from ..core import cost_routing

        new_value, change = cost_routing.set_enabled(self.config, enabled)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[cost_routing.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "cost_routing_reverted",
                        "reason": "The cost-routing change could not "
                                  "be saved; the previous setting "
                                  "was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Cost-routing change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def cost_decision(self, task_class: str) -> Any:
        """The router's decision for *task_class* (M-031).

        Pure over this agent's config: the chosen door, the
        current door, both yardstick prices, and the plain-words
        reason — whether or not anything is later applied.
        """
        from ..core.cost_routing import choose_route

        return choose_route(self.config, task_class)

    def cost_route(self, task_class: str) -> dict[str, Any]:
        """Decide for *task_class* and apply a changed door (M-031).

        When the decision prefers a different door, the switch is
        applied through M-028's :meth:`switch_model` with the
        decision's own reason, so it is journaled as a
        ``model_switched`` event and preserves the session, the
        plan, and the crew exactly as any switch does. When the
        decision keeps the current door, nothing is applied and
        nothing is journaled — no switch happened.
        """
        decision = self.cost_decision(task_class)
        record = decision.record()
        record["decision"] = decision
        record["applied"] = False
        record["switch"] = None
        if decision.changed:
            record["switch"] = self.switch_model(
                model=decision.chosen.model,
                base_url=decision.chosen.base_url,
                reason=decision.reason)
            record["applied"] = True
        return record

    def edit_format_status(self) -> dict[str, Any]:
        """The edit-format setting, the formats, and the tasks (M-071).

        The setting exactly as stored (validated — a malformed
        stored value raises, never vanishes), the current
        model's proven strength (M-027 truth), every format
        and every task kind. This is the answer ``/editformat``
        shows; nothing about it is hidden.
        """
        from ..core import edit_formats

        model = self.config.get("model")
        return {
            "setting": edit_formats.setting_from_config(self.config),
            "model": model,
            "strength": edit_formats.model_strength(model),
            "formats": [
                {"id": fmt.id, "title": fmt.title, "plain": fmt.plain,
                 "appliable": fmt.appliable,
                 "strength_floor": fmt.strength_floor}
                for fmt in edit_formats.list_formats()],
            "task_kinds": [
                {"id": kind.id, "title": kind.title, "plain": kind.plain}
                for kind in edit_formats.list_task_kinds()],
        }

    def set_edit_format(self, value: str) -> dict[str, Any]:
        """Pin the edit-format setting, or return it to auto (M-071).

        Validated by :mod:`mythic_agent.core.edit_formats`
        before anything mutates; journaled first as an
        ``edit_format_setting_changed`` event when a session
        is attached; a failed save restores the previous
        value exactly and journals a compensating
        ``edit_format_setting_reverted``.
        """
        import copy

        from ..core import edit_formats

        new_value, change = edit_formats.set_setting(self.config, value)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[edit_formats.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "edit_format_setting_reverted",
                        "reason": "The edit-format change could not "
                                  "be saved; the previous setting "
                                  "was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Edit format change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def choose_edit_format(self, task_kind: str,
                           model: str | None = None) -> dict[str, Any]:
        """Pick the edit format for *task_kind* — and journal it (M-071).

        The roadmap's word is that the choice is journaled:
        when a session is attached the pick is recorded as an
        ``edit_format_chosen`` session event with its
        plain-words reason, its task, and the model's proven
        strength. Without a session the choice is still made
        and returned, honestly marked not journaled. The
        model defaults to the session's current model.
        """
        from ..core.edit_formats import choose_format

        choice = choose_format(
            task_kind,
            model=model if model is not None else self.config.get("model"),
            config=self.config)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(choice.event())
            journaled = True
        record = choice.record(self.session_id, journaled)
        record["choice"] = choice
        return record

    def apply_edit_format(self, path: str, format_id: str,
                          payload: str) -> dict[str, Any]:
        """Apply an edit payload in *format_id* to *path* (M-071).

        The pure appliers judge the payload against the
        file's true current text — a refusal (a stale diff,
        a search block that does not match exactly once)
        writes nothing at all. A successful apply is written
        through the existing EditJournal road, so it is
        journaled and undoable exactly like any agent edit,
        and recorded on the session as an
        ``edit_format_applied`` event when one is attached.
        """
        from ..core.edit_formats import apply_edit
        from ..core.edits import EditJournal
        from ..core.file_guardians import explicit_from_config
        from ..core.workspace import resolve_file

        target = resolve_file(self.project_root, path, write=True)
        # M-087: large-file and binary care judges the
        # file from its true bytes before any edit road
        # runs - a binary refuses outright, whatever the
        # gate says, and a large file whose care gate is
        # off refuses with the guard's own explanation.
        # The assessment rides along below: a large file
        # on the chunk road warns before saving, exactly
        # as a generated file does (M-086).
        care_assessment = None
        if target.exists():
            from ..core import large_file_care as _lfc
            care_assessment = _lfc.assess_edit(
                _lfc.classify_bytes(path, target.read_bytes()),
                config=self.config)
            if not care_assessment.allowed:
                raise ValueError(care_assessment.warning)
        target = resolve_file(self.project_root, path, write=True)
        current = (target.read_text(encoding="utf-8")
                   if target.exists() else None)
        new_text, units = apply_edit(format_id, current, payload)
        # M-086: a hand-edit to a generated file warns
        # before saving - the assessment is computed from
        # the file's true current text, before any write,
        # and the warning rides the returned record (and
        # the session, when one is attached). The edit
        # itself still applies: the warning is honesty,
        # not a refusal.
        gen_assessment = None
        if current is not None:
            from ..core import generated_code as _gc
            gen_assessment = _gc.assess_edit(
                _gc.classify_text(path, current), config=self.config)
        # M-079: the guardians judge the apply by the
        # operation it truly is — a whole-file format is an
        # overwrite, a diff or a search block is in-place,
        # a missing file is a creation — and the journal
        # enforces the verdict under this config's word.
        operation = ("create" if current is None else
                     "overwrite" if format_id == "whole-file"
                     else "inplace")
        EditJournal(self.project_root,
                    explicit_word=explicit_from_config(self.config)
                    ).write(path, new_text, operation=operation)
        record: dict[str, Any] = {
            "path": path, "format": format_id, "units": units,
            "changed": current != new_text, "journaled": False,
            "generated_warning": (gen_assessment.warning
                                  if gen_assessment is not None
                                  and gen_assessment.warns else None),
            "large_file_warning": (care_assessment.warning
                                   if care_assessment is not None
                                   and care_assessment.warns else None)}
        if (gen_assessment is not None and gen_assessment.warns
                and self._session_store and self.session_id):
            self._checkpoint(gen_assessment.record())
        if (care_assessment is not None and care_assessment.warns
                and self._session_store and self.session_id):
            self._checkpoint(care_assessment.record())
        if self._session_store and self.session_id:
            self._checkpoint({"type": "edit_format_applied",
                              "path": path, "format": format_id,
                              "units": units})
            record["journaled"] = True
        return record

    def hash_anchor_status(self) -> dict[str, Any]:
        """The hash-anchored-edits gate, in plain data (M-072).

        The setting exactly as stored (validated — a malformed
        stored value raises, never vanishes) and the plain
        explanation. This is the answer ``/hashanchor`` shows.
        """
        from ..core import hash_anchored

        return {
            "enabled": hash_anchored.enabled_from_config(self.config),
            "explanation": hash_anchored.PLAIN_EXPLANATION,
        }

    def set_hash_anchored(self, enabled: bool) -> dict[str, Any]:
        """Turn hash-anchored edits on or off (M-072).

        Validated by :mod:`mythic_agent.core.hash_anchored`
        before anything mutates; journaled first as a
        ``hash_anchored_setting_changed`` event when a session
        is attached; a failed save restores the previous value
        exactly and journals a compensating
        ``hash_anchored_setting_reverted``.
        """
        import copy

        from ..core import hash_anchored

        new_value, change = hash_anchored.set_enabled(
            self.config, enabled)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[hash_anchored.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "hash_anchored_setting_reverted",
                        "reason": "The hash-anchored change could "
                                  "not be saved; the previous "
                                  "setting was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Hash-anchored change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def _write_hash_anchored(self, path: str, new_text: str,
                             applied: Any,
                             current: str | None) -> dict[str, Any]:
        """Write one judged anchored edit via EditJournal (M-072)."""
        from ..core.edits import EditJournal
        from ..core.file_guardians import explicit_from_config

        # M-079: a span covering the whole file is an
        # overwrite; a partial span is an in-place edit.
        line_count = len(current.splitlines()) if current else 0
        operation = ("overwrite" if applied.start <= 1
                     and applied.end >= max(line_count, 1)
                     else "inplace")
        EditJournal(self.project_root,
                    explicit_word=explicit_from_config(self.config)
                    ).write(path, new_text, operation=operation)
        record: dict[str, Any] = {
            "path": path, "start": applied.start, "end": applied.end,
            "before": applied.before.hash, "after": applied.after_hash,
            "units": applied.units, "changed": current != new_text,
            "journaled": False}
        if self._session_store and self.session_id:
            self._checkpoint(applied.event(path))
            record["journaled"] = True
        return record

    def apply_hash_anchored_range(self, path: str, start: int,
                                  end: int, expected: str,
                                  replacement: str) -> dict[str, Any]:
        """Apply a range edit under its lines' anchor (M-072).

        Refuses — writing nothing — when the gate is off, and
        when the range's current anchor differs from
        *expected* (a moved target, named in the refusal).
        A successful apply rides the EditJournal road and is
        recorded as a ``hash_anchored_applied`` session event.
        """
        from ..core import hash_anchored
        from ..core.workspace import resolve_file

        if not hash_anchored.enabled_from_config(self.config):
            raise ValueError(
                "hash-anchored edits are off — turn them on with "
                "/hashanchor on; nothing was changed")
        target = resolve_file(self.project_root, path, write=True)
        if not target.exists():
            raise ValueError(
                f"an anchored edit needs an existing file; "
                f"{path} does not exist — nothing was changed")
        current = target.read_text(encoding="utf-8")
        new_text, applied = hash_anchored.apply_anchored_range(
            current, start, end, expected, replacement)
        return self._write_hash_anchored(path, new_text, applied,
                                          current)

    def apply_hash_anchored_search(self, path: str, search: str,
                                   expected: str,
                                   replacement: str) -> dict[str, Any]:
        """Apply a search edit under its block's anchor (M-072).

        The search text must match exactly once and its lines'
        anchor must match *expected*; any other outcome
        refuses and writes nothing. Success rides EditJournal.
        """
        from ..core import hash_anchored
        from ..core.workspace import resolve_file

        if not hash_anchored.enabled_from_config(self.config):
            raise ValueError(
                "hash-anchored edits are off — turn them on with "
                "/hashanchor on; nothing was changed")
        target = resolve_file(self.project_root, path, write=True)
        if not target.exists():
            raise ValueError(
                f"an anchored edit needs an existing file; "
                f"{path} does not exist — nothing was changed")
        current = target.read_text(encoding="utf-8")
        new_text, applied = hash_anchored.apply_anchored_search(
            current, search, expected, replacement)
        return self._write_hash_anchored(path, new_text, applied,
                                          current)

    def repair_loop_status(self) -> dict[str, Any]:
        """The apply-repair-loop gate, in plain data (M-073).

        The setting exactly as stored (validated — a malformed
        stored value raises, never vanishes) and the plain
        explanation. This is the answer ``/repairloop`` shows.
        """
        from ..core import apply_repair

        return {
            "enabled": apply_repair.enabled_from_config(self.config),
            "explanation": apply_repair.PLAIN_EXPLANATION,
        }

    def set_apply_repair(self, enabled: bool) -> dict[str, Any]:
        """Turn the apply-failure repair loop on or off (M-073).

        Validated by :mod:`mythic_agent.core.apply_repair`
        before anything mutates; journaled first as an
        ``apply_repair_setting_changed`` event when a session
        is attached; a failed save restores the previous
        value exactly and journals a compensating
        ``apply_repair_setting_reverted``.
        """
        import copy

        from ..core import apply_repair

        new_value, change = apply_repair.set_enabled(
            self.config, enabled)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[apply_repair.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "apply_repair_setting_reverted",
                        "reason": "The repair-loop change could "
                                  "not be saved; the previous "
                                  "setting was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Repair-loop change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)


    def hunk_review_status(self) -> dict[str, Any]:
        """The hunk-review gate, in plain data (M-074).

        The setting exactly as stored (validated — a malformed
        stored value raises, never vanishes) and the plain
        explanation. This is the answer ``/hunkreview`` shows.
        """
        from ..core import hunk_review

        return {
            "enabled": hunk_review.enabled_from_config(self.config),
            "explanation": hunk_review.PLAIN_EXPLANATION,
        }

    def set_hunk_review(self, enabled: bool) -> dict[str, Any]:
        """Turn hunk-level review on or off (M-074).

        Validated by :mod:`mythic_agent.core.hunk_review`
        before anything mutates; journaled first as a
        ``hunk_review_setting_changed`` event when a session
        is attached; a failed save restores the previous
        value exactly and journals a compensating
        ``hunk_review_setting_reverted``.
        """
        import copy

        from ..core import hunk_review

        new_value, change = hunk_review.set_enabled(
            self.config, enabled)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[hunk_review.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "hunk_review_setting_reverted",
                        "reason": "The hunk-review change could "
                                  "not be saved; the previous "
                                  "setting was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Hunk-review change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def guardian_status(self) -> dict[str, Any]:
        """The guardians and the explicit word (M-079).

        Whether the user's explicit word is on record
        (validated — a malformed stored value raises, never
        vanishes), the guarded kinds, and the plain
        explanation. This is the answer ``/guardians`` shows.
        """
        from ..core import file_guardians

        return {
            "explicit_word": file_guardians.explicit_from_config(
                self.config),
            "guarded_kinds": list(file_guardians.GUARDED_KINDS),
            "explanation": file_guardians.PLAIN_EXPLANATION,
        }

    def set_guardian_word(self, given: bool) -> dict[str, Any]:
        """Give or take back the explicit word (M-079).

        Validated by :mod:`mythic_agent.core.file_guardians`
        before anything mutates; journaled first as a
        ``guardian_word_changed`` event when a session is
        attached; a failed save restores the previous value
        exactly and journals a compensating
        ``guardian_word_reverted``.
        """
        import copy

        from ..core import file_guardians

        new_value, change = file_guardians.set_explicit_word(
            self.config, given)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[file_guardians.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "guardian_word_reverted",
                        "reason": "The explicit-word change could "
                                  "not be saved; the previous "
                                  "setting was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Explicit-word change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def split_for_review(self, payload: str) -> dict[str, Any]:
        """Split a unified diff into its reviewable hunks (M-074).

        Purely a read: each hunk as data — its header, its
        old side (what it matches) and its new side (what it
        becomes) — for the approval surface to show one hunk
        at a time. A malformed diff refuses here, before any
        decision is made on it.
        """
        from ..core import hunk_review

        hunks = hunk_review.split_diff(payload)
        return {"count": len(hunks), "hunks": [
            {"index": hunk.index, "header": hunk.header(),
             "old_start": hunk.old_start,
             "old_count": hunk.old_count,
             "new_start": hunk.new_start,
             "new_count": hunk.new_count,
             "old_side": hunk.old_side, "new_side": hunk.new_side,
             "body": list(hunk.body)} for hunk in hunks]}

    def apply_hunk_review(
            self, path: str, payload: str,
            decisions: Any) -> dict[str, Any]:
        """Apply a hunk-by-hunk reviewed diff to *path* (M-074).

        *decisions* names every hunk: ``(index, "accept")``,
        ``(index, "reject")``, or ``(index, "edit", body)``
        for an edited hunk (its new body, judged at edit
        time — an edit may change what a hunk becomes, never
        what it matches). Rejecting one hunk never kills the
        rest: the accepted and edited hunks are judged by
        M-071's strict applier, unchanged, and written
        through the EditJournal road; rejected hunks simply
        never land. An undecided hunk, a stale accepted
        hunk, and the gate being off all refuse and write
        nothing. The whole review is recorded on the session
        as a ``hunk_review_applied`` event with its counts
        when a session is attached — including an
        all-rejected review, which is an honest no-change
        outcome, not an error.
        """
        from ..core import hunk_review
        from ..core.edits import EditJournal
        from ..core.workspace import resolve_file

        if not hunk_review.enabled_from_config(self.config):
            raise ValueError(
                "hunk review is off — turn it on with "
                "/hunkreview on; nothing was changed")
        target = resolve_file(self.project_root, path, write=True)
        if not target.exists():
            raise ValueError(
                f"a hunk review needs an existing file; "
                f"{path} does not exist — nothing was changed")
        current = target.read_text(encoding="utf-8")
        review = hunk_review.start_review(payload)
        for item in decisions:
            if len(item) == 3 and item[1] == "edit":
                review = hunk_review.edit_hunk(
                    review, item[0], item[2])
            elif len(item) == 2:
                review = hunk_review.decide(review, item[0], item[1])
            else:
                raise ValueError(
                    "each decision is (index, 'accept'), "
                    "(index, 'reject'), or (index, 'edit', body); "
                    f"got {item!r}")
        new_text, outcome = hunk_review.apply_review(current, review)
        if outcome.applied:
            # M-079: a reviewed hunk apply modifies the file
            # in place — judged as such by the guardians.
            from ..core.file_guardians import explicit_from_config

            EditJournal(
                self.project_root,
                explicit_word=explicit_from_config(self.config)
            ).write(path, new_text, operation="inplace")
        record: dict[str, Any] = {
            "path": path, "applied": outcome.applied,
            "rejected": outcome.rejected,
            "edited": outcome.edited, "changed": outcome.changed,
            "journaled": False}
        if self._session_store and self.session_id:
            event = review.event()
            event["path"] = path
            event["applied"] = outcome.applied
            event["changed"] = outcome.changed
            self._checkpoint(event)
            record["journaled"] = True
        return record

    def change_set_status(self) -> dict[str, Any]:
        """The change-set gate, in plain data (M-084).

        The setting exactly as stored (validated — a malformed
        stored value raises, never vanishes) and the plain
        explanation. This is the answer ``/changeset`` shows.
        """
        from ..core import change_sets

        return {
            "enabled": change_sets.enabled_from_config(self.config),
            "explanation": change_sets.PLAIN_EXPLANATION,
        }

    def set_change_sets(self, enabled: bool) -> dict[str, Any]:
        """Turn multi-file change sets on or off (M-084).

        Validated by :mod:`mythic_agent.core.change_sets`
        before anything mutates; journaled first as a
        ``change_set_setting_changed`` event when a session
        is attached; a failed save restores the previous
        value exactly and journals a compensating
        ``change_set_setting_reverted``.
        """
        import copy

        from ..core import change_sets

        new_value, change = change_sets.set_enabled(
            self.config, enabled)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[change_sets.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "change_set_setting_reverted",
                        "reason": "The change-set change could "
                                  "not be saved; the previous "
                                  "setting was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Change-set change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def preview_change_set(
            self, name: str, edits: Any,
            evidence: Any = None) -> dict[str, Any]:
        """Show a change set as a reviewable unit (M-084).

        Purely a read: the set is built and validated (its
        name, one edit per file, each format concrete) and
        returned as data — each file with its format, plus
        the attached evidence's record when *evidence* (a
        mapping with command / passed / failed / skipped /
        log_ref) is given. Nothing is read from disk and
        nothing is written.
        """
        from ..core import change_sets

        change_set = change_sets.start_change_set(
            name, [change_sets.make_edit(*edit) for edit in edits])
        if evidence is not None:
            change_set = change_sets.attach_evidence(
                change_set, change_sets.make_evidence(**evidence))
        return {"name": change_set.name,
                "files": [edit.record()
                          for edit in change_set.edits],
                "evidence": (change_set.evidence.record()
                             if change_set.evidence is not None
                             else None)}

    def apply_change_set(
            self, name: str, edits: Any, decisions: Any,
            evidence: Any = None) -> dict[str, Any]:
        """Apply a named multi-file change set (M-084).

        *edits* is a list of ``(path, format_id, payload)``
        triples — one edit per file, each in an M-071
        concrete format; *decisions* names every file:
        ``(index, "accept")`` or ``(index, "reject")``.
        Rejecting one file never kills the rest: the
        accepted files are planned in memory through
        M-071's strict appliers against the files' true
        current text — one stale file refuses the whole
        set and writes nothing — and only a clean plan is
        written, through the EditJournal road, one
        journaled write per file. An undecided file and
        the gate being off also refuse and write nothing.
        *evidence*, when given, is a mapping with the test
        command and its passed / failed / skipped counts
        (plus a log reference); it is validated, attached
        to the set, and carried in the session record —
        a set applied without evidence records exactly
        that. The whole set is recorded on the session as
        a ``change_set_applied`` event under its name when
        a session is attached — including an all-rejected
        set, which is an honest no-change outcome.
        """
        from ..core import change_sets
        from ..core.edits import EditJournal
        from ..core.workspace import resolve_file

        if not change_sets.enabled_from_config(self.config):
            raise ValueError(
                "change sets are off — turn them on with "
                "/changeset on; nothing was changed")
        change_set = change_sets.start_change_set(
            name, [change_sets.make_edit(*edit) for edit in edits])
        for item in decisions:
            if len(item) != 2:
                raise ValueError(
                    "each decision is (index, 'accept') or "
                    f"(index, 'reject'); got {item!r}")
            change_set = change_sets.decide(
                change_set, item[0], item[1])
        if evidence is not None:
            change_set = change_sets.attach_evidence(
                change_set, change_sets.make_evidence(**evidence))
        currents: dict[str, Any] = {}
        for edit in change_set.edits:
            target = resolve_file(
                self.project_root, edit.path, write=True)
            currents[edit.path] = (
                target.read_text(encoding="utf-8")
                if target.exists() else None)
        new_texts, outcome = change_sets.apply_change_set(
            change_set, currents)
        journal = EditJournal(self.project_root)
        for path, new_text in new_texts.items():
            journal.write(path, new_text)
        record: dict[str, Any] = {
            "name": change_set.name,
            "applied": outcome.applied,
            "rejected": outcome.rejected,
            "units": outcome.units,
            "changed_files": outcome.changed_files,
            "changed": outcome.changed,
            "evidence": (change_set.evidence.record()
                         if change_set.evidence is not None
                         else None),
            "journaled": False}
        if self._session_store and self.session_id:
            event = change_set.event()
            event["applied"] = outcome.applied
            event["units"] = outcome.units
            event["changed_files"] = outcome.changed_files
            event["changed"] = outcome.changed
            self._checkpoint(event)
            record["journaled"] = True
        return record

    def rename_move_status(self) -> dict[str, Any]:
        """The rename/move gate, in plain data (M-085).

        The setting exactly as stored (validated — a
        malformed stored value raises, never vanishes) and
        the plain explanation. This is the answer
        ``/rename`` shows.
        """
        from ..core import rename_move

        return {
            "enabled": rename_move.enabled_from_config(self.config),
            "explanation": rename_move.PLAIN_EXPLANATION,
        }

    def set_rename_move(self, enabled: bool) -> dict[str, Any]:
        """Turn rename/move on or off (M-085).

        Validated by :mod:`mythic_agent.core.rename_move`
        before anything mutates; journaled first as a
        ``rename_move_setting_changed`` event when a session
        is attached; a failed save restores the previous
        value exactly and journals a compensating
        ``rename_move_setting_reverted``.
        """
        import copy

        from ..core import rename_move

        new_value, change = rename_move.set_enabled(
            self.config, enabled)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[rename_move.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "rename_move_setting_reverted",
                        "reason": "The rename/move change could "
                                  "not be saved; the previous "
                                  "setting was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Rename/move change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def _rename_move_plan(self, source: Any, destination: Any):
        """Plan a move against the real workspace (M-085).

        Existing paths and directory-ness come from disk;
        referencing files come from Part III's symbol graph
        (its file edges inverted: whose edges name the
        source), their true current text read from disk.
        A graph that cannot be built is reported, never
        hidden: the plan then carries no computed reference
        updates and the warning rides the returned record.
        """
        import os

        from ..core import rename_move
        from ..core.workspace import resolve_file

        root = self.project_root
        existing: list[str] = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(
                d for d in dirnames if not d.startswith("."))
            rel_dir = os.path.relpath(dirpath, root)
            for name in dirnames:
                existing.append(
                    name if rel_dir == "."
                    else f"{rel_dir}/{name}")
            for name in sorted(filenames):
                existing.append(
                    name if rel_dir == "."
                    else f"{rel_dir}/{name}")
        referencing: list[str] = []
        graph_warning = None
        try:
            from ..context.symbol_graph import build_symbol_graph

            graph = build_symbol_graph(root)
            edges = graph.file_edges()
            referencing = sorted(
                path for path, targets in edges.items()
                if source in targets and path != source)
        except Exception as exc:
            graph_warning = (
                f"symbol graph unavailable ({exc}); reference "
                "updates were not computed")
        texts: dict[str, str] = {}
        for path in referencing:
            target = resolve_file(root, path)
            if target.exists():
                texts[path] = target.read_text(encoding="utf-8")
        plan = rename_move.plan_move(
            source, destination, existing=existing,
            referencing=referencing, texts=texts,
            is_directory=(root / source).is_dir()
            if isinstance(source, str) else False)
        return plan, graph_warning

    def preview_rename_move(
            self, source: str, destination: str) -> dict[str, Any]:
        """Show a rename/move as a planned edit (M-085).

        Purely a read: the plan is computed whole against
        the real workspace - the git mv command, the graph
        reference updates with their counts, and every
        warning - and returned as data. Nothing moves and
        nothing is written.
        """
        plan, graph_warning = self._rename_move_plan(
            source, destination)
        record = plan.record()
        record["graph_warning"] = graph_warning
        record["journaled"] = False
        return record

    def rename_move_file(
            self, source: str, destination: str) -> dict[str, Any]:
        """Execute one rename/move as a first-class edit (M-085).

        The plan is computed whole first (one refusal —
        a missing source, an existing destination, a move
        onto itself - and nothing moves). The file itself
        moves only by ``git mv``, so its history is
        preserved; a source git does not track refuses in
        git's own words and nothing else is written. The
        reference updates the plan computed from Part
        III's graph are then written through the
        EditJournal road, and the move is recorded on the
        session as a ``file_moved`` event when a session
        is attached. The gate being off refuses and moves
        nothing.
        """
        import subprocess

        from ..core import rename_move
        from ..core.edits import EditJournal

        if not rename_move.enabled_from_config(self.config):
            raise ValueError(
                "rename/move is off — turn it on with "
                "/rename on; nothing was changed")
        plan, graph_warning = self._rename_move_plan(
            source, destination)
        destination_path = self.project_root / plan.destination
        if destination_path.parent != self.project_root:
            destination_path.parent.mkdir(
                parents=True, exist_ok=True)
        result = subprocess.run(
            ["git", "-C", str(self.project_root), "mv",
             plan.source, plan.destination],
            capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(
                f"git mv refused the move ({plan.source} -> "
                f"{plan.destination}): "
                f"{detail or 'no reason given'}; "
                "the file was not moved")
        journal = EditJournal(self.project_root)
        for update in plan.updates:
            journal.write(update.path, update.new_text)
        record = plan.record()
        record["graph_warning"] = graph_warning
        record["journaled"] = False
        if self._session_store and self.session_id:
            event = plan.record()
            if graph_warning:
                event["graph_warning"] = graph_warning
            self._checkpoint(event)
            record["journaled"] = True
        return record

    def generated_code_status(self) -> dict[str, Any]:
        """The generated-code gate, in plain data (M-086).

        The setting exactly as stored (validated - a
        malformed stored value raises, never vanishes) and
        the plain explanation. This is the answer
        ``/generated`` shows.
        """
        from ..core import generated_code

        return {
            "enabled": generated_code.enabled_from_config(self.config),
            "explanation": generated_code.PLAIN_EXPLANATION,
        }

    def set_generated_code(self, enabled: bool) -> dict[str, Any]:
        """Turn generated-code honesty on or off (M-086).

        Validated by :mod:`mythic_agent.core.generated_code`
        before anything mutates; journaled first as a
        ``generated_code_setting_changed`` event when a
        session is attached; a failed save restores the
        previous value exactly and journals a compensating
        ``generated_code_setting_reverted``.
        """
        import copy

        from ..core import generated_code

        new_value, change = generated_code.set_enabled(
            self.config, enabled)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[generated_code.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "generated_code_setting_reverted",
                        "reason": "The generated-code change could "
                                  "not be saved; the previous "
                                  "setting was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Generated-code change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def check_generated_code(self, path: str) -> dict[str, Any]:
        """Classify one real file from its own face (M-086).

        A pure read: the file's true current text is
        classified by its head marker, the generator the
        marker names is recorded exactly (or honestly as
        unknown), and a hand-edit to it is assessed under
        this config - the warning computed before any
        save. A missing file refuses; nothing is written.
        """
        from ..core import generated_code
        from ..core.workspace import resolve_file

        target = resolve_file(self.project_root, path)
        if not target.exists():
            raise ValueError(f"{path} does not exist; nothing was checked")
        record = generated_code.classify_text(
            path, target.read_text(encoding="utf-8"))
        assessment = generated_code.assess_edit(record, config=self.config)
        data = record.record()
        data["assessment"] = assessment.record()
        data["journaled"] = False
        return data

    def mark_generated_file(
            self, path: str, generator: str) -> dict[str, Any]:
        """Mark one real file as generated by *generator* (M-086).

        The registration is judged against the file's own
        face first: a marker already present governs, and
        a conflicting generator name refuses and writes
        nothing. An unmarked file gains the one header
        line in its own comment style, written through
        the EditJournal road; an already-marked file is
        left byte-identical. The mark is recorded on the
        session as a ``generated_file`` event when one is
        attached. The gate being off refuses and marks
        nothing.
        """
        from ..core import generated_code
        from ..core.edits import EditJournal
        from ..core.workspace import resolve_file

        if not generated_code.enabled_from_config(self.config):
            raise ValueError(
                "generated-code honesty is off - turn it on with "
                "/generated on; nothing was changed")
        target = resolve_file(self.project_root, path, write=True)
        if not target.exists():
            raise ValueError(f"{path} does not exist; nothing was marked")
        text = target.read_text(encoding="utf-8")
        record = generated_code.register_generated(
            path, generator, text=text)
        marked = record.marker is None
        if marked:
            header = generated_code.marker_header(path, record.generator)
            EditJournal(self.project_root).write(path, header + "\n" + text)
        data = record.record()
        if marked:
            data["marker"] = {"line": 1, "form": "generated_by",
                               "generator": record.generator,
                               "text": generated_code.marker_header(
                                   path, record.generator)}
        data["marked"] = marked
        data["journaled"] = False
        if self._session_store and self.session_id:
            event = record.record()
            event["marked"] = marked
            self._checkpoint(event)
            data["journaled"] = True
        return data

    def large_file_care_status(self) -> dict[str, Any]:
        """The large-file care gate, in plain data (M-087).

        The setting exactly as stored (validated - a
        malformed stored value raises, never vanishes) and
        the plain explanation. This is the answer
        ``/largefile`` shows.
        """
        from ..core import large_file_care

        return {
            "enabled": large_file_care.enabled_from_config(self.config),
            "explanation": large_file_care.PLAIN_EXPLANATION,
        }

    def set_large_file_care(self, enabled: bool) -> dict[str, Any]:
        """Turn large-file and binary care on or off (M-087).

        Validated by :mod:`mythic_agent.core.large_file_care`
        before anything mutates; journaled first as a
        ``large_file_care_setting_changed`` event when a
        session is attached; a failed save restores the
        previous value exactly and journals a compensating
        ``large_file_care_setting_reverted``.
        """
        import copy

        from ..core import large_file_care

        new_value, change = large_file_care.set_enabled(
            self.config, enabled)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[large_file_care.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "large_file_care_setting_reverted",
                        "reason": "The large-file care change could "
                                  "not be saved; the previous "
                                  "setting was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Large-file care change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def check_large_file(self, path: str) -> dict[str, Any]:
        """Classify one real file from its true bytes (M-087).

        A pure read: the file's bytes are classified once -
        binary or text, small or large - with the guard's
        own explanation, a text edit is assessed under
        this config, and a large text file also returns
        its anchored chunk plan. A missing file refuses;
        nothing is written.
        """
        from ..core import large_file_care
        from ..core.workspace import resolve_file

        target = resolve_file(self.project_root, path)
        if not target.exists():
            raise ValueError(f"{path} does not exist; nothing was checked")
        record = large_file_care.classify_bytes(path, target.read_bytes())
        assessment = large_file_care.assess_edit(record, config=self.config)
        data = record.record()
        data["assessment"] = assessment.record()
        data["chunks"] = []
        data["chunk_plan"] = None
        if record.edit_mode == "anchored_chunks":
            chunks = large_file_care.split_chunks(
                target.read_text(encoding="utf-8"))
            data["chunks"] = [c.record() for c in chunks]
            data["chunk_plan"] = large_file_care.format_chunk_plan(chunks)
        data["journaled"] = False
        return data

    def apply_large_file_chunk_edit(
            self, path: str, chunk_index: int, anchor: str,
            replacement: str) -> dict[str, Any]:
        """Edit one anchored chunk of a large file (M-087).

        The gate being off refuses and edits nothing. The
        file is judged from its true bytes first: a binary
        refuses in the guard's own words, and a file on
        the whole-file road refuses here - the ordinary
        edit roads are its road. The pure layer applies
        the replacement only when the anchor still
        matches the chunk the file holds now; a mismatch
        names both anchors and writes nothing. A clean
        edit is written through the EditJournal road and
        recorded on the session as a
        ``large_file_chunk_edited`` event when one is
        attached.
        """
        from ..core import large_file_care
        from ..core.edits import EditJournal
        from ..core.workspace import resolve_file

        if not large_file_care.enabled_from_config(self.config):
            raise ValueError(
                "large-file care is off - turn it on with "
                "/largefile on; nothing was changed")
        target = resolve_file(self.project_root, path, write=True)
        if not target.exists():
            raise ValueError(f"{path} does not exist; nothing was edited")
        record = large_file_care.classify_bytes(path, target.read_bytes())
        if record.is_binary:
            raise ValueError(record.explanation)
        if record.edit_mode != "anchored_chunks":
            raise ValueError(
                f"{path} is on the whole-file road; chunk edits "
                "are for large files - use the ordinary edit roads")
        text = target.read_text(encoding="utf-8")
        new_text = large_file_care.apply_chunk_edit(
            text, chunk_index, anchor, replacement)
        EditJournal(self.project_root).write(path, new_text)
        data = record.record()
        data["chunk_index"] = chunk_index
        data["anchor"] = anchor
        data["journaled"] = False
        if self._session_store and self.session_id:
            self._checkpoint({
                "type": "large_file_chunk_edited",
                "path": path, "chunk_index": chunk_index,
                "anchor": anchor})
            data["journaled"] = True
        return data


    # -- M-088: the stash shelf against the real tree --

    def _stash_shelf_dir(self):
        """The shelf's home for this workspace, on disk."""
        from ..core.config_manager import config_manager
        from ..core.workspace import workspace_id

        directory = (config_manager.MYTHIC_DIR / "stash-shelf"
                     / workspace_id(self.project_root))
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        return directory

    def _stash_tree(self) -> dict[str, Any]:
        """The real working tree as path -> text (M-088).

        Text work-in-progress only: symlinks, files that
        do not decode as UTF-8 (binaries), the checkpoint
        store's skipped directories, and the agent's own
        state directory when it lives inside the tree
        are left out of the shelf's judgement.
        """
        import os
        from pathlib import Path

        from ..core import checkpoints
        from ..core.config_manager import config_manager

        root = Path(self.project_root).resolve()
        state_rel = None
        try:
            state_rel = config_manager.MYTHIC_DIR.resolve().relative_to(root)
        except (ValueError, OSError):
            state_rel = None
        tree: dict[str, Any] = {}
        for dirpath, dirnames, filenames in os.walk(root):
            here = Path(dirpath)
            kept = []
            for dirname in sorted(dirnames):
                if dirname in checkpoints.SKIP_DIRS:
                    continue
                candidate = here / dirname
                if candidate.is_symlink():
                    continue
                if state_rel is not None:
                    rel = candidate.relative_to(root)
                    if rel == state_rel or state_rel in rel.parents:
                        continue
                    if rel in state_rel.parents:
                        kept.append(dirname)
                        continue
                kept.append(dirname)
            dirnames[:] = kept
            for filename in sorted(filenames):
                candidate = here / filename
                if candidate.is_symlink():
                    continue
                try:
                    data = candidate.read_bytes()
                except OSError:
                    continue
                try:
                    text = data.decode("utf-8")
                except UnicodeDecodeError:
                    continue
                tree[str(candidate.relative_to(root))] = text
        return tree

    def _stash_base(self, establish: bool = False):
        """The shelf's base: the last clean tree state.

        Stored as one JSON file beside the journal. When
        no base has been recorded yet and *establish* is
        true, the tree as it stands now becomes the base
        - the first clean state the shelf has seen - and
        is written to disk before anything is judged.
        """
        import json

        from ..core.edits import atomic_write

        base_file = self._stash_shelf_dir() / "base.json"
        if base_file.exists():
            return json.loads(base_file.read_text(encoding="utf-8"))
        if not establish:
            return None
        base = self._stash_tree()
        atomic_write(base_file,
                     json.dumps(base, sort_keys=True).encode("utf-8"),
                     0o600)
        return base

    def _stash_load(self):
        """The shelf rebuilt from its journal file."""
        from ..core import stash_shelf

        journal = self._stash_shelf_dir() / "shelf.journal"
        if not journal.exists():
            return stash_shelf.Shelf(), 0
        return stash_shelf.Shelf.from_journal_text(
            journal.read_text(encoding="utf-8"))

    def _stash_save(self, shelf) -> None:
        """Write the shelf's journal whole, atomically."""
        from ..core.edits import atomic_write

        journal = self._stash_shelf_dir() / "shelf.journal"
        atomic_write(journal,
                     shelf.to_journal_text().encode("utf-8"), 0o600)

    def _stash_apply_tree(self, before, after) -> None:
        """Move the real tree from *before* to *after*.

        Only paths that differ are touched: changed or
        new paths are written, vanished paths removed.
        """
        for path in sorted(set(before) | set(after)):
            if before.get(path) == after.get(path):
                continue
            target = self.project_root / path
            if path in after:
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.is_symlink():
                    target.unlink()
                target.write_text(after[path], encoding="utf-8")
            elif target.is_symlink() or target.exists():
                target.unlink()

    def stash_shelf_status(self) -> dict[str, Any]:
        """The stash shelf gate and contents (M-088).

        The setting exactly as stored (validated - a
        malformed stored value raises, never vanishes),
        the plain explanation, every shelved entry as a
        record, and the journal's corrupt-line count,
        reported rather than hidden. The first status
        read establishes the base from the tree as it
        stands. This is the answer ``/stash`` shows.
        """
        from ..core import stash_shelf

        shelf, corrupt = self._stash_load()
        base = self._stash_base(establish=True)
        return {
            "enabled": stash_shelf.enabled_from_config(self.config),
            "explanation": stash_shelf.PLAIN_EXPLANATION,
            "count": len(shelf),
            "names": shelf.names(),
            "entries": [entry.record() for entry in shelf.entries()],
            "corrupt_lines": corrupt,
            "base_files": len(base),
        }

    def set_stash_shelf(self, enabled: bool) -> dict[str, Any]:
        """Turn the stash shelf on or off (M-088).

        Validated by :mod:`mythic_agent.core.stash_shelf`
        before anything mutates; journaled first as a
        ``stash_shelf_setting_changed`` event when a
        session is attached; a failed save restores the
        previous value exactly and journals a compensating
        ``stash_shelf_setting_reverted``.
        """
        import copy

        from ..core import stash_shelf

        new_value, change = stash_shelf.set_enabled(
            self.config, enabled)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[stash_shelf.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "stash_shelf_setting_reverted",
                        "reason": "The stash shelf change could "
                                  "not be saved; the previous "
                                  "setting was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Stash shelf change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def shelve_stash(self, name: str) -> dict[str, Any]:
        """Shelve the tree's work-in-progress by name (M-088).

        The difference between the working tree and its
        base is captured under *name* in the journal on
        disk first - the entry is durable before the
        tree moves - and the tree then goes back to its
        base exactly. Shelving nothing, or a name already
        on the shelf, refuses and changes nothing. With
        the gate off this refuses and shelves nothing.
        The shelve is recorded on the session as a
        ``stash_shelved`` event when one is attached.
        """
        from ..core import stash_shelf

        if not stash_shelf.enabled_from_config(self.config):
            raise ValueError(
                "the stash shelf is off - turn it on with "
                "/stash on; nothing was shelved")
        base = self._stash_base(establish=True)
        working = self._stash_tree()
        entry = stash_shelf.build_entry(
            name, base, working, session_id=self.session_id)
        shelf, _corrupt = self._stash_load()
        shelf.shelve(entry)
        self._stash_save(shelf)
        cleaned = stash_shelf.clean_tree(base, entry)
        self._stash_apply_tree(working, cleaned)
        record: dict[str, Any] = {
            "type": "stash_shelved", "name": entry.name,
            "files": entry.file_count, "bytes": entry.total_bytes,
            "entry": entry.record(), "journaled": False}
        if self._session_store and self.session_id:
            event = {key: value for key, value in record.items()
                     if key not in ("journaled", "entry")}
            self._checkpoint(event)
            record["journaled"] = True
        return record

    def restore_stash(self, name: str,
                      discard: bool = False) -> dict[str, Any]:
        """Restore one shelved entry into the tree (M-088).

        Judged against the tree as it stands now: a path
        that moved since the shelve is a conflict - the
        restore refuses, names every conflicted path,
        and changes nothing - unless *discard* throws
        those changes away on purpose, counted in the
        record. A restored entry leaves the shelf. With
        the gate off this refuses and restores nothing.
        The restore is recorded on the session as a
        ``stash_restored`` event when one is attached.
        """
        from ..core import stash_shelf

        if not stash_shelf.enabled_from_config(self.config):
            raise ValueError(
                "the stash shelf is off - turn it on with "
                "/stash on; nothing was restored")
        base = self._stash_base(establish=True)
        working = self._stash_tree()
        shelf, _corrupt = self._stash_load()
        entry = shelf.get(name)
        conflicts = stash_shelf.restore_conflicts(entry, base, working)
        restored = shelf.restore(name, base, working, discard=discard)
        self._stash_save(shelf)
        self._stash_apply_tree(working, restored)
        record: dict[str, Any] = {
            "type": "stash_restored", "name": entry.name,
            "files": entry.file_count, "conflicts": conflicts,
            "discarded": len(conflicts) if discard else 0,
            "entry": entry.record(), "journaled": False}
        if self._session_store and self.session_id:
            event = {key: value for key, value in record.items()
                     if key not in ("journaled", "entry")}
            self._checkpoint(event)
            record["journaled"] = True
        return record

    def drop_stash(self, name: str) -> dict[str, Any]:
        """Drop one shelved entry; the tree is untouched (M-088).

        The entry leaves the journal on disk and the
        drop is recorded on the session as a
        ``stash_dropped`` event when one is attached.
        A name that is not on the shelf refuses.
        """
        shelf, _corrupt = self._stash_load()
        entry = shelf.drop(name)
        self._stash_save(shelf)
        record: dict[str, Any] = {
            "type": "stash_dropped", "name": entry.name,
            "files": entry.file_count,
            "entry": entry.record(), "journaled": False}
        if self._session_store and self.session_id:
            event = {key: value for key, value in record.items()
                     if key not in ("journaled", "entry")}
            self._checkpoint(event)
            record["journaled"] = True
        return record

    # -- M-089: patch export/import against real files --

    def patch_exchange_status(self) -> dict[str, Any]:
        """The patch-exchange gate, in plain data (M-089).

        The setting exactly as stored (validated - a
        malformed stored value raises, never vanishes) and
        the plain explanation. This is the answer ``/patch``
        shows. The agent holds no persistent named change
        sets (M-084 sets are transient values the layer
        builds), so the status names the gate only.
        """
        from ..core import patch_exchange

        return {
            "enabled": patch_exchange.enabled_from_config(self.config),
            "explanation": patch_exchange.PLAIN_EXPLANATION,
        }

    def set_patch_exchange(self, enabled: bool) -> dict[str, Any]:
        """Turn patch export/import on or off (M-089).

        Validated by :mod:`mythic_agent.core.patch_exchange`
        before anything mutates; journaled first as a
        ``patch_exchange_setting_changed`` event when a
        session is attached; a failed save restores the
        previous value exactly and journals a compensating
        ``patch_exchange_setting_reverted``.
        """
        import copy

        from ..core import patch_exchange

        new_value, change = patch_exchange.set_enabled(
            self.config, enabled)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[patch_exchange.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "patch_exchange_setting_reverted",
                        "reason": "The patch exchange change could "
                                  "not be saved; the previous "
                                  "setting was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Patch exchange change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def export_patch_to_file(self, change_set: Any,
                             destination: Any) -> dict[str, Any]:
        """Export a decided change set to a patch file (M-089).

        The agent layer holds no persistent named change
        sets - an M-084 change set is a value the layer
        builds (``preview_change_set`` / ``apply_change_set``),
        never a stored shelf - so export takes the set
        itself plus the destination path. The set is
        judged by the pure layer unchanged: an undecided
        file refuses and is named, an all-rejected set
        refuses, and with the gate off this refuses and
        writes nothing. The patch text is written to the
        real file at *destination* (workspace-relative
        paths resolve against the project root), and the
        export is recorded on the session as a
        ``patch_exported`` event when one is attached.
        """
        from pathlib import Path

        from ..core import patch_exchange
        from ..core.edits import atomic_write

        if not patch_exchange.enabled_from_config(self.config):
            raise ValueError(
                "patch exchange is off - turn it on with "
                "/patch on; nothing was exported")
        text = patch_exchange.export_patch(change_set)
        dest = Path(destination)
        if not dest.is_absolute():
            dest = Path(self.project_root) / dest
        dest.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(dest, text.encode("utf-8"), 0o644)
        patch = patch_exchange.parse_patch(text)
        record: dict[str, Any] = {
            "type": "patch_exported", "name": patch.name,
            "path": str(dest),
            "files": [edit.path for edit in patch.edits],
            "rejected_files": list(patch.rejected),
            "evidence": patch.evidence, "journaled": False}
        if self._session_store and self.session_id:
            event = {key: value for key, value in record.items()
                     if key != "journaled"}
            self._checkpoint(event)
            record["journaled"] = True
        return record

    def import_patch_from_file(self, source: Any) -> dict[str, Any]:
        """Import a patch file into the real tree (M-089).

        The file at *source* (workspace-relative paths
        resolve against the project root) is read, proven
        by the pure layer (magic, header checksum, every
        payload anchor), rebuilt through M-084, and planned
        against the real working tree's current file texts:
        one stale file refuses the whole import and writes
        nothing. A clean plan is written through the
        EditJournal road, one journaled write per file,
        and the import is recorded on the session as a
        ``patch_imported`` event when one is attached.
        With the gate off this refuses and imports nothing;
        a missing file refuses plainly.
        """
        from pathlib import Path

        from ..core import patch_exchange
        from ..core.edits import EditJournal
        from ..core.workspace import resolve_file

        if not patch_exchange.enabled_from_config(self.config):
            raise ValueError(
                "patch exchange is off - turn it on with "
                "/patch on; nothing was imported")
        src = Path(source)
        if not src.is_absolute():
            src = Path(self.project_root) / src
        if not src.exists():
            raise ValueError(
                f"no patch file at {source} - nothing was imported")
        text = src.read_text(encoding="utf-8")
        patch = patch_exchange.parse_patch(text)
        currents: dict[str, Any] = {}
        for edit in patch.edits:
            target = resolve_file(
                self.project_root, edit.path, write=True)
            currents[edit.path] = (
                target.read_text(encoding="utf-8")
                if target.exists() else None)
        new_texts, outcome = patch_exchange.import_patch(text, currents)
        journal = EditJournal(self.project_root)
        for path, new_text in new_texts.items():
            journal.write(path, new_text)
        record: dict[str, Any] = {
            "type": "patch_imported", "name": patch.name,
            "source": str(src), "applied": outcome.applied,
            "units": outcome.units,
            "changed_files": outcome.changed_files,
            "changed": outcome.changed,
            "files": [edit.path for edit in patch.edits],
            "rejected_files": list(patch.rejected),
            "evidence": patch.evidence, "journaled": False}
        if self._session_store and self.session_id:
            event = {key: value for key, value in record.items()
                     if key != "journaled"}
            self._checkpoint(event)
            record["journaled"] = True
        return record

    def conflict_workbench_status(self) -> dict[str, Any]:
        """The conflict-workbench gate, in plain data (M-081)."""
        from ..core import conflict_workbench

        return {
            "enabled": conflict_workbench.enabled_from_config(self.config),
            "explanation": conflict_workbench.PLAIN_EXPLANATION,
        }

    def set_conflict_workbench(self, enabled: bool) -> dict[str, Any]:
        """Turn the conflict workbench on or off (M-081).

        Validated before anything mutates; journaled first
        as a ``conflict_workbench_setting_changed`` event
        when a session is attached; a failed save restores
        the previous value and journals the revert.
        """
        import copy

        from ..core import conflict_workbench

        new_value, change = conflict_workbench.set_enabled(
            self.config, enabled)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[conflict_workbench.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "conflict_workbench_setting_reverted",
                        "reason": "The conflict-workbench change could "
                                  "not be saved; the previous "
                                  "setting was preserved.",
                    })
                except Exception:
                    pass
            raise RuntimeError(
                "Conflict-workbench change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def conflict_workbench_view(self) -> dict[str, Any]:
        """The live conflict workbench for this workspace (M-081).

        Purely a read of the real repository state: the
        operation in progress, each conflicted file with
        its regions and both sides' derived intent
        summaries.
        """
        from ..core import conflict_workbench

        workbench = conflict_workbench.detect_workbench(self.project_root)
        return {"operation": workbench.operation,
                "conflicted": workbench.conflicted,
                "files": [
                    {"path": f.path, "regions": f.region_count,
                     "ours_intent": f.ours_intent,
                     "theirs_intent": f.theirs_intent,
                     "places": [
                         {"index": r.index, "ours_label": r.ours_label,
                          "theirs_label": r.theirs_label,
                          "ours": list(r.ours),
                          "theirs": list(r.theirs)}
                         for r in f.regions]}
                    for f in workbench.files]}

    def resolve_conflict(self, path: str,
                         decisions: Any) -> dict[str, Any]:
        """Resolve one conflicted file, as a decision list (M-081).

        *decisions* names every conflicted place:
        ``(index, "ours")``, ``(index, "theirs")``,
        ``(index, "both")``, or ``(index, "edit", text)``.
        The resolved text is proven marker-free by the pure
        layer, written through the EditJournal road, staged
        so git records the file resolved, and then tested
        by re-reading the real index — the file must no
        longer be unmerged. The resolution is journaled as
        a ``conflict_resolution_applied`` event when a
        session is attached. A pending place, surviving
        markers, the gate being off, or a file that is not
        conflicted all refuse and write nothing.
        """
        import subprocess

        from ..core import conflict_workbench
        from ..core.edits import EditJournal
        from ..core.workspace import resolve_file

        if not conflict_workbench.enabled_from_config(self.config):
            raise ValueError(
                "conflict workbench is off — turn it on with "
                "/conflicts on; nothing was changed")
        workbench = conflict_workbench.detect_workbench(self.project_root)
        match = [f for f in workbench.files if f.path == path]
        if not match:
            raise ValueError(
                f"{path} is not a conflicted file in this "
                "repository — nothing was changed")
        conflict_file = match[0]
        target = resolve_file(self.project_root, path, write=True)
        current = target.read_text(encoding="utf-8")
        resolution = conflict_workbench.start_resolution(conflict_file)
        for item in decisions:
            if len(item) == 3 and item[1] == "edit":
                resolution = conflict_workbench.edit_resolution(
                    resolution, item[0], item[2])
            elif len(item) == 2:
                resolution = conflict_workbench.decide_resolution(
                    resolution, item[0], item[1])
            else:
                raise ValueError(
                    "each decision is (index, 'ours'), "
                    "(index, 'theirs'), (index, 'both'), or "
                    f"(index, 'edit', text); got {item!r}")
        new_text, outcome = conflict_workbench.apply_resolution(
            current, resolution)
        EditJournal(self.project_root).write(path, new_text)
        subprocess.run(["git", "-C", str(self.project_root),
                        "add", "--", path],
                       capture_output=True, timeout=15, check=True)
        after = conflict_workbench.detect_workbench(self.project_root)
        verified = all(f.path != path for f in after.files)
        if not verified:
            raise RuntimeError(
                f"resolution of {path} was written and staged but "
                "the file is still unmerged in the index; the "
                "resolution was not proven")
        record: dict[str, Any] = {
            "path": path, "applied": outcome.applied,
            "changed": outcome.changed, "verified": verified,
            "journaled": False}
        if self._session_store and self.session_id:
            event = resolution.event()
            event["verified"] = verified
            self._checkpoint(event)
            record["journaled"] = True
        return record

    def commit_craft_status(self) -> dict[str, Any]:
        """The commit-craft gate and seam, in data (M-080).

        The setting exactly as stored (validated — a
        malformed stored value raises, never vanishes),
        the plain explanation, and the M-078 auto-commit
        trigger seam, reported honestly through
        :mod:`mythic_agent.core.commit_craft`. This is
        the answer ``/commitcraft`` shows.
        """
        from ..core import commit_craft

        return {
            "enabled": commit_craft.enabled_from_config(self.config),
            "explanation": commit_craft.PLAIN_EXPLANATION,
            "auto_commit_trigger": commit_craft.auto_commit_trigger(),
        }

    def set_commit_craft(self, enabled: bool) -> dict[str, Any]:
        """Turn commit craft on or off (M-080).

        Validated by :mod:`mythic_agent.core.commit_craft`
        before anything mutates; journaled first as a
        ``commit_craft_setting_changed`` event when a
        session is attached; a failed save restores the
        previous value exactly and journals a compensating
        ``commit_craft_setting_reverted``.
        """
        import copy

        from ..core import commit_craft

        new_value, change = commit_craft.set_enabled(
            self.config, enabled)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[commit_craft.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "commit_craft_setting_reverted",
                        "reason": "The commit-craft change could "
                                  "not be saved; the previous "
                                  "setting was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Commit-craft change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def plan_commit_split(self) -> dict[str, Any]:
        """Draft the commit split for the working tree (M-080).

        Purely a read: the tree's diff is collected, its
        hunks are judged by the M-074 hunk layer, and the
        files are grouped by concern, each group carrying
        a message drafted from its own actual diff. The
        plan is recorded on the session as a
        ``commit_craft_planned`` event when one is
        attached. Nothing is staged or committed.
        """
        from ..core import commit_craft

        diff_text, untracked, warnings = (
            commit_craft.collect_working_diff(self.project_root))
        plan = commit_craft.plan_commits(diff_text, untracked)
        record = plan.record()
        record["warnings"] = warnings
        record["journaled"] = False
        if self._session_store and self.session_id:
            self._checkpoint({
                "type": "commit_craft_planned",
                "concerns": record["concerns"],
                "files": record["files"],
                "added": record["added"],
                "removed": record["removed"],
            })
            record["journaled"] = True
        return record

    def commit_craft_group(
            self, concern: str,
            message: str | None = None) -> dict[str, Any]:
        """Commit one concern group of the split (M-080).

        The plan is re-drafted from the tree as it stands
        — a stale plan is never committed from. Only the
        group's own files are staged (``git add`` on
        exactly those paths), the index is proven to hold
        exactly that group before the commit is made —
        an index carrying other staged work refuses,
        untouched — and the commit is made under the
        given message or the group's drafted one. The
        rest of the split stays in the working tree. The
        commit is recorded as a ``commit_craft_committed``
        session event with its true new head.
        """
        from ..core import commit_craft

        if not commit_craft.enabled_from_config(self.config):
            raise ValueError(
                "commit craft is off — turn it on with "
                "/commitcraft on; nothing was changed")
        diff_text, untracked, _warnings = (
            commit_craft.collect_working_diff(self.project_root))
        plan = commit_craft.plan_commits(diff_text, untracked)
        group = plan.group(concern)
        paths = [change.path for change in group.files]
        code, _out, err = commit_craft.run_git(
            self.project_root, "add", "--", *paths)
        if code != 0:
            raise RuntimeError(
                f"staging the {concern} group failed: "
                f"{err.strip()}; nothing was committed")
        code, out, err = commit_craft.run_git(
            self.project_root, "diff", "--cached", "--name-only")
        staged = {line for line in out.splitlines() if line}
        if code != 0 or staged != set(paths):
            raise ValueError(
                "the index holds staged changes beyond the "
                f"{concern} group ({sorted(staged)}); commit "
                "craft commits one concern at a time and "
                "leaves the index as it found it; nothing "
                "was committed")
        text = message or commit_craft.draft_message(group)
        code, _out, err = commit_craft.run_git(
            self.project_root, "commit", "-m", text)
        if code != 0:
            raise RuntimeError(
                f"the {concern} commit failed: {err.strip()}")
        code, out, _err = commit_craft.run_git(
            self.project_root, "rev-parse", "HEAD")
        sha = out.strip()
        record: dict[str, Any] = {
            "concern": concern, "files": paths, "sha": sha,
            "subject": text.splitlines()[0] if text else "",
            "message": text, "added": group.added,
            "removed": group.removed, "journaled": False}
        if self._session_store and self.session_id:
            self._checkpoint({
                "type": "commit_craft_committed",
                "concern": concern, "files": paths, "sha": sha,
                "subject": record["subject"]})
            record["journaled"] = True
        return record

    def push_with_house_rules(
            self, remote: str = "origin") -> dict[str, Any]:
        """Push the current branch under the house rules (M-080).

        The rules, wired in, in order: the remote is read
        with ``ls-remote`` before and after; the remote
        is fetched; the remote-diff (ahead/behind and the
        diffstat against the remote branch) is read
        before anything is sent; the push is judged by
        :func:`mythic_agent.core.commit_craft.judge_push`
        — a diverged remote refuses, because pushing past
        it would need force and this road never
        force-pushes; the push itself is built with an
        explicit refspec and judged by
        ``validate_push_args``; and afterwards
        ``ls-remote`` must show the remote holding
        exactly the pushed head, moved from where it
        stood, or the push is reported as unverified and
        raised. An up-to-date remote is an honest
        no-send outcome, returned, not an error. A landed
        push is recorded as a ``commit_craft_pushed``
        session event with the before/after heads.
        """
        from ..core import commit_craft

        if not commit_craft.enabled_from_config(self.config):
            raise ValueError(
                "commit craft is off — turn it on with "
                "/commitcraft on; nothing was pushed")
        branch = commit_craft.current_branch(self.project_root)
        if not branch:
            raise ValueError(
                "the tree is on a detached head — there is "
                "no branch to push; nothing was pushed")
        code, out, _err = commit_craft.run_git(
            self.project_root, "rev-parse", "HEAD")
        local_head = out.strip() if code == 0 else ""
        before = commit_craft.ls_remote_head(
            self.project_root, remote, branch)
        code, _out, err = commit_craft.run_git(
            self.project_root, "fetch", remote)
        if code != 0:
            raise RuntimeError(
                f"fetch from {remote} failed: {err.strip()}; "
                "the house rules read the remote-diff before "
                "any push; nothing was pushed")
        remote_head = commit_craft.remote_tracking_head(
            self.project_root, remote, branch)
        ahead, behind = commit_craft.ahead_behind(
            self.project_root, remote, branch)
        stat = commit_craft.remote_diff_stat(
            self.project_root, remote, branch)
        verdict = commit_craft.judge_push(
            local_head, remote_head or None, behind == 0)
        record: dict[str, Any] = {
            "remote": remote, "branch": branch,
            "pushed": False, "before": before or None,
            "after": before or None, "ahead": ahead,
            "behind": behind, "remote_diff_stat": stat,
            "verdict": verdict.record(), "journaled": False}
        if verdict.kind == "up-to-date":
            return record
        if not verdict.allowed:
            raise ValueError(verdict.reason)
        args = ["push", remote, f"HEAD:refs/heads/{branch}"]
        commit_craft.validate_push_args(args)
        code, _out, err = commit_craft.run_git(
            self.project_root, *args)
        if code != 0:
            raise RuntimeError(
                f"git push failed: {err.strip()}; the push "
                "is not claimed")
        after = commit_craft.ls_remote_head(
            self.project_root, remote, branch)
        verify = commit_craft.verify_remote_moved(
            before or None, after or None, local_head)
        record["after"] = after or None
        record["verify"] = verify.record()
        if not verify.verified:
            raise RuntimeError(
                verify.reason + "; the push is not claimed")
        record["pushed"] = True
        if self._session_store and self.session_id:
            self._checkpoint({
                "type": "commit_craft_pushed",
                "remote": remote, "branch": branch,
                "before": before or None, "after": after,
                "ahead": ahead})
            record["journaled"] = True
        return record

    def checkpoint_status(self) -> dict[str, Any]:
        """The checkpoints gate and tree, in plain data (M-075).

        The setting exactly as stored (validated — a
        malformed stored value raises, never vanishes), the
        plain explanation, and the whole checkpoint tree:
        every checkpoint as a record with its parent, the
        head among them. This is the answer ``/checkpoint``
        shows.
        """
        from ..core import checkpoints

        store = checkpoints.CheckpointStore(self.project_root)
        records = store.list_checkpoints()
        head = store.head()
        return {
            "enabled": checkpoints.enabled_from_config(self.config),
            "explanation": checkpoints.PLAIN_EXPLANATION,
            "count": len(records),
            "head": head.name if head else None,
            "head_id": head.id if head else None,
            "checkpoints": records,
        }

    def set_checkpoints(self, enabled: bool) -> dict[str, Any]:
        """Turn named checkpoints on or off (M-075).

        Validated by :mod:`mythic_agent.core.checkpoints`
        before anything mutates; journaled first as a
        ``checkpoints_setting_changed`` event when a session
        is attached; a failed save restores the previous
        value exactly and journals a compensating
        ``checkpoints_setting_reverted``.
        """
        import copy

        from ..core import checkpoints

        new_value, change = checkpoints.set_enabled(
            self.config, enabled)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[checkpoints.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "checkpoints_setting_reverted",
                        "reason": "The checkpoints change could "
                                  "not be saved; the previous "
                                  "setting was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Checkpoints change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def take_checkpoint(self, name: str) -> dict[str, Any]:
        """Freeze the working tree under *name* (M-075).

        Captures the whole tree and — when a session is
        attached — the session state (its messages, status,
        token count and outcome, read back through the
        session store's own export). The take is journaled
        on the session as a ``checkpoint_created`` event.
        With the gate off, or a name already taken, this
        refuses and captures nothing.
        """
        from ..core import checkpoints

        if not checkpoints.enabled_from_config(self.config):
            raise ValueError(
                "checkpoints are off — turn them on with "
                "/checkpoint on; nothing was captured")
        snapshot = None
        if self._session_store and self.session_id:
            exported = self._session_store.export(self.session_id)
            snapshot = {
                "session_id": exported["id"],
                "status": exported["status"],
                "total_tokens": exported["total_tokens"],
                "messages": exported["context"],
                "outcome": exported.get("outcome"),
            }
        store = checkpoints.CheckpointStore(self.project_root)
        checkpoint = store.create(name, snapshot)
        record: dict[str, Any] = {
            "type": "checkpoint_created", "name": checkpoint.name,
            "checkpoint_id": checkpoint.id,
            "parent_name": checkpoint.parent_name,
            "files": checkpoint.file_count,
            "bytes": checkpoint.total_bytes,
            "session_captured": snapshot is not None,
            "journaled": False}
        if self._session_store and self.session_id:
            event = {key: value for key, value in record.items()
                     if key != "journaled"}
            self._checkpoint(event)
            record["journaled"] = True
        return record

    def restore_checkpoint(self, name: str,
                           discard: bool = False) -> dict[str, Any]:
        """Bring one checkpoint's tree and session back (M-075).

        One command, judged honestly by the store: a tree
        changed since the last checkpoint was taken or
        restored refuses (naming the changed files) unless
        *discard* throws those changes away on purpose,
        counted in the record. The session state comes
        back only into the session it was captured from;
        a checkpoint from another session restores the
        tree and says so. The restore is journaled on the
        session as a ``checkpoint_restored`` event with
        its counts.
        """
        import copy

        from ..core import checkpoints
        from ..core.sessions import SessionStore

        if not checkpoints.enabled_from_config(self.config):
            raise ValueError(
                "checkpoints are off — turn them on with "
                "/checkpoint on; nothing was restored")
        store = checkpoints.CheckpointStore(self.project_root)
        checkpoint, outcome = store.restore(name, discard=discard)
        record: dict[str, Any] = {
            "type": "checkpoint_restored", "name": checkpoint.name,
            "checkpoint_id": checkpoint.id,
            "restored": outcome.restored,
            "removed": outcome.removed,
            "unchanged": outcome.unchanged,
            "discarded_changes": outcome.discarded_changes,
            "session_restored": False, "journaled": False}
        if checkpoint.session is not None:
            snapshot = checkpoint.session
            if self._session_store and self.session_id:
                if snapshot["session_id"] == self.session_id:
                    with self._lock:
                        self.messages = copy.deepcopy(
                            snapshot["messages"])
                    self.total_tokens = snapshot["total_tokens"]
                    if snapshot["status"] in SessionStore.STATUSES:
                        self._session_status = snapshot["status"]
                    record["session_restored"] = True
                else:
                    record["session_note"] = (
                        "Session state was captured from session "
                        f"{snapshot['session_id']}, not the "
                        "attached session; the tree was restored "
                        "and the session left as it stands.")
            else:
                record["session_note"] = (
                    "The checkpoint carries session state, but "
                    "no session is attached; the tree alone "
                    "was restored.")
        if self._session_store and self.session_id:
            event = {key: value for key, value in record.items()
                     if key != "journaled"}
            self._checkpoint(event)
            record["journaled"] = True
        return record

    def session_branching_status(self) -> dict[str, Any]:
        """The session-branching gate, in plain data (M-076).

        The setting exactly as stored (validated — a
        malformed stored value raises, never vanishes) and
        the plain explanation. This is the answer
        ``/branch`` shows.
        """
        from ..core import session_branching

        return {
            "enabled": session_branching.enabled_from_config(self.config),
            "explanation": session_branching.PLAIN_EXPLANATION,
        }

    def set_session_branching(self, enabled: bool) -> dict[str, Any]:
        """Turn session branching on or off (M-076).

        Validated by
        :mod:`mythic_agent.core.session_branching` before
        anything mutates; journaled first as a
        ``session_branching_setting_changed`` event when a
        session is attached; a failed save restores the
        previous value exactly and journals a compensating
        ``session_branching_setting_reverted``.
        """
        import copy

        from ..core import session_branching

        new_value, change = session_branching.set_enabled(
            self.config, enabled)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[session_branching.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "session_branching_setting_reverted",
                        "reason": "The session-branching change could "
                                  "not be saved; the previous "
                                  "setting was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Session-branching change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def fork_session(self, at_index: int,
                     name: str | None = None) -> dict[str, Any]:
        """Fork the attached session at a message (M-076).

        The branch is a new stored session sharing this
        session's history up to and including the fork
        message; this session continues untouched, and the
        two diverge independently from here. The fork is
        recorded on this session as a
        ``session_branch_forked`` event naming the child,
        and on the child (by the store) as
        ``session_branched``. With the gate off, or with
        no session attached, the fork refuses and creates
        nothing.
        """
        from ..core import session_branching

        if not session_branching.enabled_from_config(self.config):
            raise ValueError(
                "session branching is off — turn it on with "
                "/branch on; nothing was changed")
        if not self._session_store or not self.session_id:
            raise ValueError(
                "no session is attached to fork; nothing "
                "was changed")
        branch_id = self._session_store.branch(
            self.session_id, at_index, name=name)
        record: dict[str, Any] = {
            "type": "session_branch_forked",
            "parent_session_id": self.session_id,
            "branch_session_id": branch_id,
            "fork_index": at_index,
            "fork_role": self._session_store.load(
                branch_id)["context"][-1]["role"],
            "branch_name": name.strip() if isinstance(name, str) else None,
            "shared_messages": at_index + 1,
            "session_id": self.session_id,
            "journaled": False,
        }
        self._checkpoint({
            "type": "session_branch_forked",
            "branch_session_id": branch_id,
            "fork_index": at_index,
            "branch_name": record["branch_name"],
        })
        record["journaled"] = True
        return record

    def compare_sessions(self, first_id: str,
                         second_id: str) -> dict[str, Any]:
        """Compare two stored sessions' histories (M-076).

        A pure read: the true shared prefix, the first
        divergence, and each side's own messages after the
        shared history — judged by
        :mod:`mythic_agent.core.session_branching`.
        Available whether the branching gate is on or off:
        comparing what already exists creates nothing.
        """
        from ..core import session_branching

        if not self._session_store:
            raise ValueError(
                "no session store is attached; nothing "
                "to compare against")
        first = self._session_store.load(first_id)
        second = self._session_store.load(second_id)
        comparison = session_branching.compare_contexts(
            first["context"], second["context"])
        return comparison.record(first_id, second_id)

    def list_session_branches(
            self, session_id: str | None = None) -> dict[str, Any]:
        """The branches forked from a session (M-076).

        Defaults to the attached session. A pure read over
        the store's session list, judged by
        :mod:`mythic_agent.core.session_branching`.
        """
        if not self._session_store:
            raise ValueError(
                "no session store is attached; nothing "
                "to list branches from")
        parent_id = session_id or self.session_id
        if not parent_id:
            raise ValueError(
                "no session is attached and none was named; "
                "nothing to list branches for")
        branches = self._session_store.branches_of(parent_id)
        return {"parent_session_id": parent_id,
                "branches": branches, "count": len(branches)}


    # ------------------------------------------------ M-077: undo grown up

    def _checkpoint_timeline_source(self) -> Any:
        """The checkpoint seam source, if one is wired (M-077).

        M-075 (Checkpoints v2) wires its source under the
        ``checkpoint_timeline_source`` attribute named by
        the seam in :mod:`mythic_agent.core.undo_timeline`
        — the source object itself, or a zero-argument
        callable returning it. With no source wired the
        checkpoint strand is honestly empty and the edit
        and command strands walk alone; nothing about
        M-075's internals is guessed at here.
        """
        from ..core.undo_timeline import CHECKPOINT_SOURCE_ATTR

        source = getattr(self, CHECKPOINT_SOURCE_ATTR, None)
        if callable(source) and not hasattr(
                source, "list_checkpoint_entries"):
            source = source()
        return source

    @property
    def checkpoint_timeline_source(self) -> Any:
        """The checkpoint seam source this agent carries.

        Wired at M-077 banking to M-075's checkpoints
        through :class:`_CheckpointTimelineAdapter`.
        Assigning a source replaces the wiring (the
        seam's own tests do exactly this); assigning
        ``None`` unwires the strand explicitly, and
        checkpoint restores then refuse with the
        DEPENDS-ON-M-075 word, as the seam promises.
        """
        if "_checkpoint_source_override" in self.__dict__:
            return self.__dict__["_checkpoint_source_override"]
        return _CheckpointTimelineAdapter(self)

    @checkpoint_timeline_source.setter
    def checkpoint_timeline_source(self, source: Any) -> None:
        self.__dict__["_checkpoint_source_override"] = source

    def _undo_store_and_entries(self) -> tuple[Any, Any]:
        from ..core.edits import EditJournal
        from ..core.undo_timeline import (
            UndoStore,
            checkpoint_entries_from_source,
        )

        checkpoints = checkpoint_entries_from_source(
            self._checkpoint_timeline_source())
        store = UndoStore(self.project_root)
        entries = store.timeline(
            EditJournal(self.project_root).entries(), checkpoints)
        return store, entries

    def undo_timeline_status(self) -> dict[str, Any]:
        """The undo-timeline gate and timeline (M-077).

        The setting exactly as stored (validated — a
        malformed stored value raises), the plain
        explanation, the timeline entries newest first,
        and whether a checkpoint source is wired through
        the seam.
        """
        from ..core import undo_timeline

        _, entries = self._undo_store_and_entries()
        return {
            "enabled": undo_timeline.enabled_from_config(self.config),
            "explanation": undo_timeline.PLAIN_EXPLANATION,
            "entries": [entry.to_dict() for entry in entries],
            "checkpoint_wired":
                self._checkpoint_timeline_source() is not None,
        }

    def set_undo_timeline(self, enabled: bool) -> dict[str, Any]:
        """Turn the undo timeline on or off (M-077).

        Validated by :mod:`mythic_agent.core.undo_timeline`
        before anything mutates; journaled first as an
        ``undo_timeline_setting_changed`` event when a
        session is attached; a failed save restores the
        previous value exactly and journals a compensating
        ``undo_timeline_setting_reverted``.
        """
        import copy

        from ..core import undo_timeline

        new_value, change = undo_timeline.set_enabled(
            self.config, enabled)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[undo_timeline.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "undo_timeline_setting_reverted",
                        "reason": "The undo-timeline change could "
                                  "not be saved; the previous "
                                  "setting was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Undo-timeline change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def _require_undo_timeline(self) -> None:
        from ..core import undo_timeline

        if not undo_timeline.enabled_from_config(self.config):
            raise ValueError(
                "undo timeline is off — /undo keeps its "
                "original last-edit behaviour; turn the "
                "timeline on with /undo on; nothing was changed")

    def _journal_undo(self, event: dict[str, Any]) -> bool:
        if self._session_store and self.session_id:
            self._checkpoint(event)
            return True
        return False

    def undo_newest(self) -> dict[str, Any]:
        """Undo the newest entry on the shared timeline (M-077)."""
        self._require_undo_timeline()
        store, entries = self._undo_store_and_entries()
        if not entries:
            return {"kind": None, "changed": False, "journaled": False,
                    "message": "Nothing to undo: the timeline "
                               "holds no edits, commands, or "
                               "checkpoints yet."}
        return self._undo_timeline_entry(store, entries, entries[0])

    def undo_kind(self, kind: str) -> dict[str, Any]:
        """Undo the newest entry of one strand (M-077).

        The walk order still governs: a newer entry of
        another strand blocks it and is named.
        """
        self._require_undo_timeline()
        store, entries = self._undo_store_and_entries()
        for entry in entries:
            if entry.kind == kind:
                return self._undo_timeline_entry(store, entries, entry)
        return {"kind": kind, "changed": False, "journaled": False,
                "message": f"Nothing to undo: the timeline "
                           f"holds no {kind} entry."}

    def restore_checkpoint_via_seam(
            self, checkpoint_id: str) -> dict[str, Any]:
        """Restore a checkpoint through the seam (M-077).

        The restore itself is M-075's road, driven through
        :class:`CheckpointTimelineSource`; with no source
        wired this refuses and says so (DEPENDS-ON-M-075).
        """
        self._require_undo_timeline()
        source = self._checkpoint_timeline_source()
        if source is None:
            raise ValueError(
                "no checkpoint source is wired yet — the "
                "checkpoint strand is DEPENDS-ON-M-075 "
                "(Checkpoints v2); nothing was changed")
        _, entries = self._undo_store_and_entries()
        target = None
        for entry in entries:
            if entry.kind == "checkpoint" \
                    and entry.ref_id == checkpoint_id:
                target = entry
                break
        if target is None:
            raise ValueError(
                f"there is no checkpoint {checkpoint_id!r} on "
                f"the timeline; nothing was changed")
        message = source.restore_checkpoint(checkpoint_id)
        journaled = self._journal_undo(target.event())
        return {"kind": "checkpoint", "ref_id": checkpoint_id,
                "label": target.label,
                "certainty": target.certainty, "changed": True,
                "message": message, "journaled": journaled}

    def _undo_timeline_entry(self, store: Any, entries: Any,
                             target: Any) -> dict[str, Any]:
        from ..core.edits import EditJournal
        from ..core.undo_timeline import judge_walk

        judge_walk(list(entries), target)
        if target.kind == "checkpoint":
            return self.restore_checkpoint_via_seam(target.ref_id)
        if target.kind == "edit":
            journal = EditJournal(self.project_root)
            live = journal.entries()
            if not live or str(live[-1]["id"]) != target.ref_id:
                raise ValueError(
                    "undo refused: the edit strand has moved "
                    "since the timeline was read; nothing was "
                    "changed")
            message = journal.undo()
            changed = message.startswith("Restored")
            journaled = False
            if changed:
                journaled = self._journal_undo(target.event())
            return {"kind": "edit", "ref_id": target.ref_id,
                    "label": target.label, "certainty": "certain",
                    "changed": changed, "message": message,
                    "journaled": journaled}
        outcome = store.undo_footprint(int(target.ref_id))
        journaled = self._journal_undo({
            "type": "undo_performed", "kind": "command",
            "ref_id": target.ref_id, "label": target.label,
            "certainty": outcome.certainty,
            "restored": outcome.restored,
            "deleted": outcome.deleted,
            "recreated": outcome.recreated})
        record = outcome.record(self.session_id, journaled)
        record["label"] = target.label
        return record

    def auto_commit_status(self) -> dict[str, Any]:
        """The auto-commit discipline, in plain data (M-078).

        The gate and the protected-branch standing word
        exactly as stored (validated — a malformed stored
        value raises, never vanishes), the protected set,
        the working branch, the branch checked out in the
        project now (None outside a repository or on a
        detached head), and the plain explanation. This is
        the answer ``/autocommit`` shows.
        """
        from ..core import auto_commit

        return {
            "enabled": auto_commit.enabled_from_config(self.config),
            "allow_protected": auto_commit.allow_protected_from_config(
                self.config),
            "protected": list(auto_commit.protected_from_config(
                self.config)),
            "working_branch": auto_commit.working_branch_from_config(
                self.config),
            "current_branch": self._auto_commit_branch(),
            "explanation": auto_commit.PLAIN_EXPLANATION,
        }

    def _auto_commit_git(self, *args: str):
        """Run one git command in the project; (rc, out, err)."""
        import subprocess

        try:
            result = subprocess.run(
                ["git", "-C", str(self.project_root), *args],
                capture_output=True, text=True, timeout=30)
        except FileNotFoundError:
            raise ValueError(
                "auto-commit needs git on this machine; git "
                "was not found — nothing was committed")
        return result.returncode, result.stdout.strip(), \
            result.stderr.strip()

    def _auto_commit_branch(self) -> str | None:
        """The branch checked out in the project, or None."""
        try:
            code, out, _ = self._auto_commit_git(
                "rev-parse", "--abbrev-ref", "HEAD")
        except ValueError:
            return None
        if code != 0 or not out or out == "HEAD":
            return None
        return out

    def _set_auto_commit_setting(self, change, key: str,
                                 new_value: bool,
                                 label: str) -> dict[str, Any]:
        """Journal-first setting change with save revert (M-078)."""
        import copy

        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[key] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "auto_commit_setting_reverted",
                        "reason": f"The {label} change could not "
                                  "be saved; the previous "
                                  "setting was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                f"{label} change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def set_auto_commit(self, enabled: bool) -> dict[str, Any]:
        """Turn the auto-commit discipline on or off (M-078).

        Validated by :mod:`mythic_agent.core.auto_commit`
        before anything mutates; journaled first as an
        ``auto_commit_setting_changed`` event when a session
        is attached; a failed save restores the previous
        value exactly and journals a compensating
        ``auto_commit_setting_reverted``.
        """
        from ..core import auto_commit

        new_value, change = auto_commit.set_enabled(
            self.config, enabled)
        return self._set_auto_commit_setting(
            change, auto_commit.SETTING_KEY, new_value, "Auto-commit")

    def set_auto_commit_allow_protected(
            self, allowed: bool) -> dict[str, Any]:
        """Give or withdraw the protected-branch word (M-078).

        The explicit standing setting under which an
        accepted edit set may land on a protected branch
        itself. Journaled first as an
        ``auto_commit_protected_setting_changed`` event; a
        failed save restores the previous value exactly.
        """
        from ..core import auto_commit

        new_value, change = auto_commit.set_allow_protected(
            self.config, allowed)
        return self._set_auto_commit_setting(
            change, auto_commit.ALLOW_PROTECTED_KEY, new_value,
            "Protected-branch auto-commit")

    def commit_accepted_edits(
            self, files: Any, summary: str) -> dict[str, Any]:
        """Land one accepted edit set as its own commit (M-078).

        The set's written message is composed from
        *summary* plus the files it carries, judged by
        :mod:`mythic_agent.core.auto_commit` into a plan —
        on the current branch when it is ordinary, on the
        working branch when the current branch is
        protected, on the protected branch itself only
        under the user's standing word — and exactly that
        plan is executed: only the accepted files are
        staged, and the commit is recorded on the session
        as an ``auto_commit_committed`` event. With the
        gate off, a blank message, a bad file set, a
        detached head, or no repository at all, this
        refuses and commits nothing. An accepted set that
        leaves nothing staged is an honest no-commit
        record, not an error.
        """
        from ..core import auto_commit

        if not auto_commit.enabled_from_config(self.config):
            raise ValueError(
                "auto-commit is off — turn it on with "
                "/autocommit on; nothing was committed")
        code, _, _ = self._auto_commit_git(
            "rev-parse", "--git-dir")
        if code != 0:
            raise ValueError(
                "auto-commit needs a git repository; the "
                "project is not inside one — nothing was "
                "committed")
        _, branch, _ = self._auto_commit_git(
            "rev-parse", "--abbrev-ref", "HEAD")
        message = auto_commit.build_message(summary, files)
        plan = auto_commit.plan_commit(
            self.config, branch, files, message)
        # M-110: every file in the plan is screened for
        # commit by secret shape before anything is
        # staged, switched or committed - a file whose
        # name or text matches a secret pattern refuses
        # the whole commit, its refusal is published as
        # a secret_refusal session event, and nothing is
        # committed. A file the plan names but the disk
        # no longer holds (an accepted deletion) is
        # screened by its name alone.
        refused = []
        for name in plan.files:
            try:
                body = (self.project_root / name).read_bytes().decode(
                    "utf-8", errors="replace")
            except OSError:
                body = ""
            outcome = self.screen_file(name, body)
            if outcome["record"] is not None:
                refused.append(outcome["screening"])
        if refused:
            named = "; ".join(
                f"{item['filename']} ({', '.join(item['kinds'])})"
                for item in refused)
            raise ValueError(
                "auto-commit refused by secret hygiene: "
                f"{named} - the files are named, their "
                "content is never shown; nothing was committed")
        switched = False
        if plan.switch_needed:
            code, _, _ = self._auto_commit_git(
                "show-ref", "--verify",
                f"refs/heads/{plan.target_branch}")
            if code == 0:
                code, _, err = self._auto_commit_git(
                    "switch", plan.target_branch)
            else:
                code, _, err = self._auto_commit_git(
                    "switch", "-c", plan.target_branch)
            if code != 0:
                raise RuntimeError(
                    "auto-commit could not move onto the "
                    f"working branch {plan.target_branch!r}: "
                    f"{err} — nothing was committed")
            switched = True
        code, _, err = self._auto_commit_git("add", "--", *plan.files)
        if code != 0:
            raise RuntimeError(
                f"auto-commit could not stage the accepted "
                f"files: {err} — nothing was committed")
        _, staged, _ = self._auto_commit_git(
            "diff", "--cached", "--name-only")
        if not staged:
            outcome = auto_commit.CommitOutcome(
                committed=False, branch=plan.branch,
                target_branch=plan.target_branch,
                on_protected=plan.on_protected, switched=switched,
                files=plan.files, message=plan.message,
                reason="the accepted edits left nothing "
                       "to commit on "
                       f"{plan.target_branch}")
        else:
            code, _, err = self._auto_commit_git(
                "commit", "-m", plan.message)
            if code != 0:
                raise RuntimeError(
                    f"auto-commit's commit failed: {err} — "
                    "nothing was committed")
            _, short, _ = self._auto_commit_git(
                "rev-parse", "--short", "HEAD")
            outcome = auto_commit.CommitOutcome(
                committed=True, branch=plan.branch,
                target_branch=plan.target_branch,
                on_protected=plan.on_protected, switched=switched,
                files=plan.files, message=plan.message,
                commit=short)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(outcome.event())
            journaled = True
        return outcome.record(self.session_id, journaled)

    def pr_craft_status(self) -> dict[str, Any]:
        """The PR-craft gate, in plain data (M-082).

        The setting exactly as stored (validated — a
        malformed stored value raises, never vanishes) and
        the plain explanation. This is the answer
        ``/prcraft`` shows.
        """
        from ..core import pr_craft

        return {
            "enabled": pr_craft.enabled_from_config(self.config),
            "explanation": pr_craft.PLAIN_EXPLANATION,
        }

    def set_pr_craft(self, enabled: bool) -> dict[str, Any]:
        """Turn PR craft on or off (M-082).

        Validated by :mod:`mythic_agent.core.pr_craft`
        before anything mutates; journaled first as a
        ``pr_craft_setting_changed`` event when a session
        is attached; a failed save restores the previous
        value exactly and journals a compensating
        ``pr_craft_setting_reverted``.
        """
        import copy

        from ..core import pr_craft

        new_value, change = pr_craft.set_enabled(
            self.config, enabled)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[pr_craft.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "pr_craft_setting_reverted",
                        "reason": "The PR-craft change could "
                                  "not be saved; the previous "
                                  "setting was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "PR-craft change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def _pr_craft_runner(self, runner: Any) -> Any:
        """The GitHub runner for M-082: injected, or the real gh road."""
        if runner is not None:
            return runner
        from ..integrations.github import _run_gh

        return lambda args: _run_gh(*args)

    def _require_pr_craft(self) -> None:
        from ..core import pr_craft

        if not pr_craft.enabled_from_config(self.config):
            raise ValueError(
                "PR craft is off — turn it on with /prcraft "
                "on; nothing was fetched or sent")

    def fetch_pull_request(self, number: int,
                           runner: Any = None) -> dict[str, Any]:
        """Fetch a pull request as data (M-082).

        A read through the user's own gh road; the fetch is
        recorded on the session as a ``pr_fetched`` event
        when a session is attached. With the gate off this
        refuses and fetches nothing.
        """
        from ..core import pr_craft

        self._require_pr_craft()
        pr = pr_craft.fetch_pull_request(
            self._pr_craft_runner(runner), number)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint({
                "type": "pr_fetched", "number": pr.number,
                "title": pr.title, "state": pr.state})
            journaled = True
        return pr.record(self.session_id, journaled)

    def fetch_review_tasks(self, number: int,
                           runner: Any = None) -> dict[str, Any]:
        """Fetch a PR's review comments, as tasks (M-082).

        One task per comment, carrying its author, words,
        and place; the fetch is recorded on the session as
        a ``pr_review_tasks_fetched`` event with its count
        when a session is attached. With the gate off this
        refuses and fetches nothing.
        """
        from ..core import pr_craft

        self._require_pr_craft()
        comments = pr_craft.fetch_review_comments(
            self._pr_craft_runner(runner), number)
        tasks = pr_craft.comments_to_tasks(comments)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint({
                "type": "pr_review_tasks_fetched",
                "pr_number": number, "comments": len(tasks)})
            journaled = True
        return {"pr_number": number, "count": len(tasks),
                "tasks": tasks, "journaled": journaled}

    def prepare_pr_draft(self, title: str, body: str, base: str,
                         head: str,
                         draft: bool = False) -> dict[str, Any]:
        """Prepare a PR draft (M-082). Sends nothing.

        The draft is recorded on the session as a
        ``pr_draft_prepared`` event when a session is
        attached. Creating the PR is a separate road —
        :meth:`post_pr_draft` — and posts only at the
        user's word.
        """
        from ..core import pr_craft

        prepared = pr_craft.prepare_pr(title, body, base, head,
                                       draft=draft)
        journaled = False
        if self._session_store and self.session_id:
            event = {k: v for k, v in
                     prepared.record(None, False).items()
                     if k not in ("session_id", "journaled")}
            self._checkpoint(event)
            journaled = True
        return prepared.record(self.session_id, journaled)

    def post_pr_draft(self, title: str, body: str, base: str,
                      head: str, draft: bool = False,
                      word: str = "",
                      runner: Any = None) -> dict[str, Any]:
        """Create a PR — only at the user's word (M-082).

        *word* is the user's own word authorising this
        post. With no word, the draft is unarmed and the
        post refuses before the GitHub runner is touched:
        nothing is sent. The word is never journaled; the
        ``pr_posted`` event carries only that a word was
        recorded.
        """
        from ..core import pr_craft

        self._require_pr_craft()
        prepared = pr_craft.arm_pr_draft(
            pr_craft.prepare_pr(title, body, base, head,
                                draft=draft), word)
        posted = pr_craft.post_pr(
            self._pr_craft_runner(runner), prepared)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint({
                "type": "pr_posted",
                "number": posted.get("number"),
                "url": posted.get("url"), "armed": True})
            journaled = True
        return prepared.post_record(self.session_id, journaled,
                                    posted)

    def prepare_review_draft(self, pr_number: int, verdict: str,
                             body: str,
                             notes: Any = ()) -> dict[str, Any]:
        """Prepare a review draft (M-082). Sends nothing.

        *notes* are ``(path, line, body)`` line notes; they
        ride in the review's body when it posts. The draft
        is recorded as a ``pr_review_draft_prepared``
        event when a session is attached.
        """
        from ..core import pr_craft

        prepared = pr_craft.prepare_review(pr_number, verdict,
                                           body, notes=notes)
        journaled = False
        if self._session_store and self.session_id:
            event = {k: v for k, v in
                     prepared.record(None, False).items()
                     if k not in ("session_id", "journaled")}
            self._checkpoint(event)
            journaled = True
        return prepared.record(self.session_id, journaled)

    def post_review_draft(self, pr_number: int, verdict: str,
                          body: str, notes: Any = (),
                          word: str = "",
                          runner: Any = None) -> dict[str, Any]:
        """Post a review — only at the user's word (M-082).

        With no word recorded, the post refuses before the
        GitHub runner is touched: nothing is sent. A
        posted review is recorded as a ``pr_review_posted``
        event (the word itself is never journaled).
        """
        from ..core import pr_craft

        self._require_pr_craft()
        prepared = pr_craft.arm_review_draft(
            pr_craft.prepare_review(pr_number, verdict, body,
                                    notes=notes), word)
        pr_craft.post_review(self._pr_craft_runner(runner),
                             prepared)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint({
                "type": "pr_review_posted",
                "pr_number": pr_number, "verdict": verdict,
                "armed": True})
            journaled = True
        return prepared.post_record(self.session_id, journaled)

    def prepare_reply_draft(self, pr_number: int, comment_id: Any,
                            body: str) -> dict[str, Any]:
        """Prepare a reply draft (M-082). Sends nothing."""
        from ..core import pr_craft

        prepared = pr_craft.prepare_reply(pr_number, comment_id,
                                          body)
        journaled = False
        if self._session_store and self.session_id:
            event = {k: v for k, v in
                     prepared.record(None, False).items()
                     if k not in ("session_id", "journaled")}
            self._checkpoint(event)
            journaled = True
        return prepared.record(self.session_id, journaled)

    def post_reply_draft(self, pr_number: int, comment_id: Any,
                         body: str, word: str = "",
                         runner: Any = None) -> dict[str, Any]:
        """Post a reply — only at the user's word (M-082).

        With no word recorded, the post refuses before the
        GitHub runner is touched: nothing is sent. A
        posted reply is recorded as a ``pr_reply_posted``
        event (the word itself is never journaled).
        """
        from ..core import pr_craft

        self._require_pr_craft()
        prepared = pr_craft.arm_reply_draft(
            pr_craft.prepare_reply(pr_number, comment_id, body),
            word)
        pr_craft.post_reply(self._pr_craft_runner(runner),
                            prepared)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint({
                "type": "pr_reply_posted",
                "pr_number": pr_number,
                "comment_id": prepared.comment_id,
                "armed": True})
            journaled = True
        return prepared.post_record(self.session_id, journaled)


    def issue_slice_status(self) -> dict[str, Any]:
        """The issue-to-slice gate, in plain data (M-083).

        The setting exactly as stored (validated — a malformed
        stored value raises, never vanishes) and the plain
        explanation. This is the answer ``/issueslice`` shows.
        """
        from ..core import issue_slice

        return {
            "enabled": issue_slice.enabled_from_config(self.config),
            "explanation": issue_slice.PLAIN_EXPLANATION,
        }

    def set_issue_slice(self, enabled: bool) -> dict[str, Any]:
        """Turn issue-to-slice on or off (M-083).

        Validated by :mod:`mythic_agent.core.issue_slice`
        before anything mutates; journaled first as a
        ``issue_slice_setting_changed`` event when a session
        is attached; a failed save restores the previous
        value exactly and journals a compensating
        ``issue_slice_setting_reverted``.
        """
        import copy

        from ..core import issue_slice

        new_value, change = issue_slice.set_enabled(
            self.config, enabled)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[issue_slice.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "issue_slice_setting_reverted",
                        "reason": "The issue-to-slice change could "
                                  "not be saved; the previous "
                                  "setting was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Issue-to-slice change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def plan_issue_slice(
            self, source: str, number: int,
            fetcher: Any = None) -> dict[str, Any]:
        """Fetch an issue through the seam and plan it (M-083).

        The issue comes from *source* — ``github`` today,
        through the existing gh road; ``samverk`` is the
        seam's named Part X source (M-242) and refuses
        honestly until that road provides the surfaces.
        *fetcher* is the seam's test door, forwarded to
        :func:`mythic_agent.core.issue_slice.fetch_issue`;
        no caller in the app passes one. The planned slice
        — the roadmap slice's shape, status ``planned``,
        with acceptance checks drafted from the issue's own
        words, each keeping the verbatim excerpt it came
        from — is recorded on the session as an
        ``issue_slice_planned`` event when a session is
        attached, and returned as a plain record. Planning
        files nothing: the record is product output data,
        never an edit to the campaign's roadmap file. The
        gate off refuses and says so.
        """
        from ..core import issue_slice

        if not issue_slice.enabled_from_config(self.config):
            raise ValueError(
                "issue-to-slice is off — turn it on with "
                "/issueslice on; nothing was planned")
        issue = issue_slice.fetch_issue(source, number,
                                        fetcher=fetcher)
        return self._record_planned_slice(issue_slice.plan_slice(issue))

    def draft_slice_from_issue(
            self, record: dict[str, Any],
            source: str = "github") -> dict[str, Any]:
        """Plan a slice from an already-fetched issue record (M-083).

        The offline twin of :meth:`plan_issue_slice`: the
        record is the shape a fetcher returns (``number``,
        ``title``, ``body``, ``state``, ``labels``, ``url``),
        for callers that already hold the issue — a webhook
        door (Part X) or a test. Same gate, same journal,
        same planned-slice record.
        """
        from ..core import issue_slice

        if not issue_slice.enabled_from_config(self.config):
            raise ValueError(
                "issue-to-slice is off — turn it on with "
                "/issueslice on; nothing was planned")
        issue = issue_slice.issue_from_record(record, source=source)
        return self._record_planned_slice(issue_slice.plan_slice(issue))

    def _record_planned_slice(self, plan: Any) -> dict[str, Any]:
        """Journal a planned slice and shape its record (M-083)."""
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(plan.event())
            journaled = True
        return plan.record(self.session_id, journaled)

    def _repair_offered(self, path: str,
                        packet: Any) -> dict[str, Any]:
        """Journal a repair packet and shape its record (M-073)."""
        from ..core.apply_repair import format_packet

        journaled = False
        if self._session_store and self.session_id:
            event = packet.event()
            event["path"] = path
            self._checkpoint(event)
            journaled = True
        return {"path": path, "applied": False, "repaired": False,
                "exhausted": False, "packet": packet,
                "packet_text": format_packet(packet),
                "journaled": journaled}

    def _repair_journal(self, event_type: str, path: str,
                        road: str) -> None:
        if self._session_store and self.session_id:
            self._checkpoint({"type": event_type, "path": path,
                              "road": road})

    def apply_edit_format_with_repair(
            self, path: str, format_id: str, payload: str,
            retry_payload: str | None = None) -> dict[str, Any]:
        """Apply a format payload, with the repair loop (M-073).

        With the gate off this is exactly
        :meth:`apply_edit_format` — a refusal stays the plain
        M-071 refusal and no packet is made. With the gate on,
        a refusal becomes a repair packet (journaled as
        ``apply_repair_offered``, carrying the true current
        text of the refused target): with no *retry_payload*
        the packet is returned and nothing is written; with
        one, exactly one honest retry rides on it — a repaired
        apply rides the EditJournal road and is journaled as
        ``apply_repair_applied``, and a second refusal is
        journaled as ``apply_repair_exhausted`` and raises the
        exhaustion error. There is no second retry.
        """
        from ..core import apply_repair
        from ..core.edits import EditJournal
        from ..core.file_guardians import GuardianRefusal
        from ..core.workspace import resolve_file

        if not apply_repair.enabled_from_config(self.config):
            return self.apply_edit_format(path, format_id, payload)
        target = resolve_file(self.project_root, path, write=True)
        current = (target.read_text(encoding="utf-8")
                   if target.exists() else None)
        try:
            return {**self.apply_edit_format(path, format_id, payload),
                    "repaired": False}
        except GuardianRefusal:
            raise  # M-079: no packet repairs a guardian refusal
        except ValueError as exc:
            reason = str(exc)
        target_range = apply_repair.target_range_for_format(
            format_id, current or "", payload)
        packet = apply_repair.build_packet(
            "edit_format", reason, current or "",
            *(target_range if target_range else (None, None)))
        record = self._repair_offered(path, packet)
        if retry_payload is None:
            return record
        self._repair_journal("apply_repair_retried", path, packet.road)
        try:
            new_text, units, spent = apply_repair.retry_edit_format(
                current or "", packet, format_id, retry_payload)
        except ValueError:
            self._repair_journal(
                "apply_repair_exhausted", path, packet.road)
            raise
        from ..core.file_guardians import explicit_from_config

        operation = ("create" if current is None else
                     "overwrite" if format_id == "whole-file"
                     else "inplace")
        EditJournal(self.project_root,
                    explicit_word=explicit_from_config(self.config)
                    ).write(path, new_text, operation=operation)
        self._repair_journal("apply_repair_applied", path, packet.road)
        record.update({"applied": True, "repaired": True,
                       "format": format_id, "units": units,
                       "changed": current != new_text,
                       "packet": spent})
        return record

    def apply_hash_anchored_range_with_repair(
            self, path: str, start: int, end: int, expected: str,
            replacement: str, retry_expected: str | None = None,
            retry_replacement: str | None = None) -> dict[str, Any]:
        """Apply an anchored range edit, with the repair loop (M-073).

        The M-072 judgement is unchanged. A moved target's
        refusal becomes a repair packet over the refused
        range's true current text; *retry_expected* (the new
        anchor the coder reads from that text) buys exactly
        one honest retry, with *retry_replacement* or the
        original replacement. Gate-off refusals (the repair
        gate or the hash-anchor gate) stay plain refusals and
        make no packet.
        """
        from ..core import apply_repair, hash_anchored
        from ..core.file_guardians import GuardianRefusal
        from ..core.workspace import resolve_file

        if not apply_repair.enabled_from_config(self.config):
            return self.apply_hash_anchored_range(
                path, start, end, expected, replacement)
        if not hash_anchored.enabled_from_config(self.config):
            raise ValueError(
                "hash-anchored edits are off — turn them on with "
                "/hashanchor on; nothing was changed")
        target = resolve_file(self.project_root, path, write=True)
        if not target.exists():
            raise ValueError(
                f"an anchored edit needs an existing file; "
                f"{path} does not exist — nothing was changed")
        current = target.read_text(encoding="utf-8")
        try:
            new_text, applied = hash_anchored.apply_anchored_range(
                current, start, end, expected, replacement)
            return {**self._write_hash_anchored(
                path, new_text, applied, current),
                "applied": True, "repaired": False}
        except GuardianRefusal:
            raise  # M-079: no packet repairs a guardian refusal
        except ValueError as exc:
            reason = str(exc)
        packet = apply_repair.build_packet(
            "anchored_range", reason, current, start, end)
        record = self._repair_offered(path, packet)
        if retry_expected is None:
            return record
        self._repair_journal("apply_repair_retried", path, packet.road)
        try:
            new_text, applied, spent = apply_repair.retry_anchored_range(
                current, packet, start, end, retry_expected,
                replacement if retry_replacement is None
                else retry_replacement)
        except ValueError:
            self._repair_journal(
                "apply_repair_exhausted", path, packet.road)
            raise
        record.update(self._write_hash_anchored(
            path, new_text, applied, current))
        self._repair_journal("apply_repair_applied", path, packet.road)
        record.update({"applied": True, "repaired": True,
                       "packet": spent})
        return record

    def apply_hash_anchored_search_with_repair(
            self, path: str, search: str, expected: str,
            replacement: str, retry_search: str | None = None,
            retry_expected: str | None = None,
            retry_replacement: str | None = None) -> dict[str, Any]:
        """Apply an anchored search edit, with the repair loop (M-073).

        The M-072 judgement is unchanged (exactly one match,
        under its anchor). A refusal becomes a repair packet —
        over the matched block's true lines when the search
        text is found, over the file's head when it is not —
        and *retry_expected* buys exactly one honest retry,
        optionally with a corrected *retry_search* and
        *retry_replacement* read from the packet's true text.
        """
        from ..core import apply_repair, hash_anchored
        from ..core.file_guardians import GuardianRefusal
        from ..core.workspace import resolve_file

        if not apply_repair.enabled_from_config(self.config):
            return self.apply_hash_anchored_search(
                path, search, expected, replacement)
        if not hash_anchored.enabled_from_config(self.config):
            raise ValueError(
                "hash-anchored edits are off — turn them on with "
                "/hashanchor on; nothing was changed")
        target = resolve_file(self.project_root, path, write=True)
        if not target.exists():
            raise ValueError(
                f"an anchored edit needs an existing file; "
                f"{path} does not exist — nothing was changed")
        current = target.read_text(encoding="utf-8")
        try:
            new_text, applied = hash_anchored.apply_anchored_search(
                current, search, expected, replacement)
            return {**self._write_hash_anchored(
                path, new_text, applied, current),
                "applied": True, "repaired": False}
        except GuardianRefusal:
            raise  # M-079: no packet repairs a guardian refusal
        except ValueError as exc:
            reason = str(exc)
        lines = current.split("\n")
        needle = search.split("\n") if search else []
        hits = [i for i in range(0, len(lines) - len(needle) + 1)
                if needle and lines[i:i + len(needle)] == needle]
        if hits:
            packet = apply_repair.build_packet(
                "anchored_search", reason, current,
                hits[0] + 1, hits[0] + len(needle))
        else:
            packet = apply_repair.build_packet(
                "anchored_search", reason, current)
        record = self._repair_offered(path, packet)
        if retry_expected is None:
            return record
        self._repair_journal("apply_repair_retried", path, packet.road)
        try:
            new_text, applied, spent = \
                apply_repair.retry_anchored_search(
                    current, packet,
                    search if retry_search is None else retry_search,
                    retry_expected,
                    replacement if retry_replacement is None
                    else retry_replacement)
        except ValueError:
            self._repair_journal(
                "apply_repair_exhausted", path, packet.road)
            raise
        record.update(self._write_hash_anchored(
            path, new_text, applied, current))
        self._repair_journal("apply_repair_applied", path, packet.road)
        record.update({"applied": True, "repaired": True,
                       "packet": spent})
        return record

    def vision_status(self) -> dict[str, Any]:
        """The current model's sight truth and the offer (M-037).

        The current model's recorded vision truth exactly as
        M-027 stores it (True / False / None — unknown is
        shown as unknown, never upgraded), every configured
        door whose model is known to see, the switch the gate
        would offer, and the plain explanation. This is the
        answer ``/vision`` shows; nothing about it is hidden.
        """
        from ..core import vision_routing
        from ..core.model_capabilities import load_capabilities

        caps = load_capabilities()
        model = self.config.get("model")
        vision = caps.for_model(model).vision if model else None
        seeing = [
            door.selection()
            for door in vision_routing.candidate_doors(self.config)
            if caps.for_model(door.model).vision is True]
        suggestion = vision_routing.suggest_switch(self.config, caps)
        return {
            "model": model,
            "vision": vision,
            "seeing_doors": seeing,
            "suggestion": (suggestion.selection()
                           if suggestion is not None else None),
            "plain_explanation": vision_routing.PLAIN_EXPLANATION,
        }

    def vision_decision(self, parts: Any) -> Any:
        """The routing gate's decision for *parts* (M-037).

        Pure over this agent's config: whether the image parts
        may go to the current model, what its capability record
        says, the plain-words reason, and the configured
        known-seeing door a switch is offered to when the gate
        refuses.
        """
        from ..core.vision_routing import route_images

        return route_images(self.config, parts)

    def _outgoing_image_parts(self) -> list[Any]:
        """Every image part in the conversation about to be sent.

        History messages whose content is a list of canonical
        content parts contribute their parts; plain-text
        content contributes none. This is the set the vision
        gate judges before a request leaves for the door.
        """
        parts: list[Any] = []
        for message in self.history_snapshot():
            if not isinstance(message, dict):
                continue
            content = message.get("content")
            if isinstance(content, list):
                parts.extend(content)
        return parts

    def gate_image_parts(self, parts: Any) -> Any:
        """Gate *parts* before any image work is sent (M-037).

        Returns the routing decision when the gate allows the
        parts (including the no-images case — text work is
        never gated). When the gate refuses, the refusal is
        journaled first as a ``vision_refused`` checkpoint
        event when a session is attached — announced on the
        record, never silent — and RuntimeError is raised with
        the decision's plain reason; nothing is sent and
        nothing about the session changes.
        """
        decision = self.vision_decision(parts)
        if decision.allowed:
            return decision
        if self._session_store and self.session_id:
            try:
                self._checkpoint({
                    "type": "vision_refused",
                    **decision.record(),
                })
            except Exception:
                pass  # the refusal itself is the truth owed
        raise RuntimeError(decision.reason)

    def apply_vision_switch(self) -> dict[str, Any]:
        """Take the switch the vision gate offers (M-037).

        The offered door — a configured door the live session
        can speak whose model is known to see — is applied
        through M-028's :meth:`switch_model` with the gate's
        own reason, so it is journaled as a ``model_switched``
        event and preserves the session, the plan, and the
        crew exactly as any switch does. When the current
        model is already known to see, or no configured door
        qualifies, this refuses plainly and changes nothing.
        """
        from ..core.vision_routing import gate_for_model, suggest_switch

        current = gate_for_model(self.config.get("model"), 1)
        if current.allowed:
            raise RuntimeError(
                f"The current model ({current.model}) is already "
                "known to see, so there is no vision switch to "
                "take; the session is unchanged.")
        suggestion = suggest_switch(self.config)
        if suggestion is None:
            raise RuntimeError(
                "No door you have set up is known to see, so "
                "there is no vision switch to take; set up a "
                "door whose model is known to see (see /vision), "
                "then switch with /model. The session is "
                "unchanged.")
        return self.switch_model(
            model=suggestion.model,
            base_url=suggestion.base_url,
            reason=(
                "Vision input routing (M-037): the previous "
                "model is not known to see, and "
                f"{suggestion.model} is a configured door whose "
                "capability record says it can see."))

    def context_strategy(self, model: str | None = None) -> dict[str, Any]:
        """The long-context strategy for a model (M-038).

        The strategy plan chosen from the model's recorded
        M-027 context size — map-first for a known
        million-class window, aggressive repo-map + retrieval
        for a known smaller window, and an honest ``unknown``
        (with the shipped default budget) when the size is not
        recorded. With *model* given, that model's strategy is
        previewed; otherwise the session's current model is
        judged. This is the answer ``/longcontext`` shows; the
        same plan drives the live file-context budget in
        ``context.runtime.prompt_file_context``.
        """
        from ..core import long_context

        plan = long_context.strategy_for_model(
            self.config.get("model") if model is None else model)
        return {
            "model": plan.model,
            "context_tokens": plan.context_tokens,
            "strategy": plan.strategy,
            "plan": plan.record(),
            "plain_explanation": long_context.PLAIN_EXPLANATION,
        }

    def provider_health(self, probe: bool = True) -> dict[str, Any]:
        """The per-provider health board for this session (M-039).

        Every M-019 registry door side by side: reachable /
        unreachable with a measured latency and the probe's
        own last error, ``needs-key`` with its M-032 custody
        state for a remote door whose key is not held, and an
        honest ``unknown`` for a door that was not probed.
        The crew's shared M-036 weather board's remembered
        state rides along where it has seen a door. With
        ``probe`` false no door is probed and every entry is
        ``unknown`` — the offline board.
        """
        from ..core import provider_health
        from ..core.rate_limit_weather import shared_board

        board = provider_health.build_board(
            self.config, weather_board=shared_board(), probe=probe)
        return {
            "board": board.record(),
            "plain_explanation": provider_health.PLAIN_EXPLANATION,
        }

    def offline_status(self, probe: bool = True) -> dict[str, Any]:
        """Whether the app is offline, read plainly (M-040).

        The M-039 health board for this session, assessed by
        the M-040 offline-truth layer: ``online`` when a door
        answered, ``offline`` — with the exact declaration
        and the non-model tools that still work — when a
        probed board shows no door can serve, and ``unknown``
        when the board cannot honestly say (never probed, or
        a keyed door the board cannot probe still standing).
        With ``probe`` false the board is unprobed and the
        state is ``unknown``, never ``offline``.
        """
        from ..core import offline_honesty, provider_health
        from ..core.rate_limit_weather import shared_board

        board = provider_health.build_board(
            self.config, weather_board=shared_board(), probe=probe)
        assessment = offline_honesty.assess_board(board)
        return {
            "assessment": assessment.record(),
            "board": board.record(),
            "plain_explanation": offline_honesty.PLAIN_EXPLANATION,
        }

    def test_kit(self, provider: str, base_url: str | None = None,
                 model: str | None = None) -> dict[str, Any]:
        """Run the new-provider test kit for one door (M-041).

        The five kit checks (registry, chat, tools, streaming,
        errors) proven against the named registry entry's door
        — or against *base_url* when given — with the evidence
        stated plainly per check. A check the door does not
        claim is skipped with the reason; a dialect the
        universal adapter cannot serve is ``not-proven``,
        never passed. An unknown provider name raises
        KeyError. No key value rides the report.
        """
        from ..core import provider_test_kit

        report = provider_test_kit.run_kit(
            provider, base_url=base_url, model=model)
        return {
            "report": report.record(),
            "plain_explanation": provider_test_kit.PLAIN_EXPLANATION,
        }

    def repo_map_status(self, query: str = "") -> dict[str, Any]:
        """The repo map for this workspace, made visible (M-045).

        M-044's map built for the session's workspace —
        ranked for *query* when one is given — presented
        through the M-045 view: entries in display order
        (pinned files first, each with its true rank, score,
        and reasons), the omitted and skipped files named,
        and any pinned file the build left out explained.
        The view never re-ranks: its scores are the map's
        own. This is the answer ``/map`` browses.
        """
        from ..context import repo_map_view
        from ..context.repo_map import build_repo_map

        repo_map = build_repo_map(self.project_root, query=query or "")
        view = repo_map_view.build_map_view(
            repo_map, repo_map_view.pins_from_config(self.config))
        return {
            "view": view.record(),
            "plain_explanation": repo_map_view.PLAIN_EXPLANATION,
        }

    def structural_search(self, pattern: str,
                          language: str) -> dict[str, Any]:
        """Search this workspace by code shape (M-047).

        An ast-grep-style pattern — code in *language*
        itself, with ``$NAME`` matching and capturing one
        node and ``$$$`` / ``$$$NAME`` matching zero or more
        siblings — run over every file of that language in
        the session's workspace, through the M-043 parse
        foundation. The result names every match with its
        captures and spans, and every file it honestly
        skipped, with the reason. A pattern that does not
        parse in its language raises PatternError (a
        ValueError); a grammar-less language raises
        ParseUnavailableError; an uncatalogued language
        raises KeyError. Search only — nothing is edited.
        """
        from ..tools import structural_search as search_module

        compiled = search_module.compile_pattern(pattern, language)
        result = search_module.search_workspace(
            self.project_root, compiled)
        return {
            "result": result.record(),
            "plain_explanation": search_module.PLAIN_EXPLANATION,
        }

    def structural_rewrite(self, pattern: str, replacement: str,
                           language: str,
                           apply: bool = False) -> dict[str, Any]:
        """Rewrite this workspace by code shape (M-048).

        The M-047 pattern, answered with a replacement
        template in the same pattern language: every match
        in the session's workspace becomes a site whose
        metavariables are filled from that match's captures,
        with a per-site diff preview and the file's hash at
        plan time. Preview by default — planning writes
        nothing. With *apply*, each file is written through
        the edit journal only when it still matches its
        plan hash; a changed file, and sites overlapping
        another match, are refused plainly in the result,
        never force-edited. A replacement that does not
        parse, names a metavariable the pattern never
        captures, or uses an unnamed ``$$$`` raises
        PatternError (a ValueError); a grammar-less language
        raises ParseUnavailableError; an uncatalogued
        language raises KeyError. The returned record
        carries the previews either way.
        """
        from ..tools import structural_rewrite as rewrite_module

        plan = rewrite_module.plan_rewrite(
            self.project_root, pattern, replacement, language)
        if not apply:
            return {
                "result": plan.record(),
                "plain_explanation": rewrite_module.PLAIN_EXPLANATION,
            }
        result = rewrite_module.apply_rewrite(self.project_root, plan)
        return {
            "result": result.record(),
            "plain_explanation": rewrite_module.PLAIN_EXPLANATION,
        }

    def lsp_status(self) -> dict[str, Any]:
        """Which language servers this machine has (M-049).

        The discovery board: every catalogued server with
        its installed state — a server that is not installed
        is named with its install remedy, never hidden. This
        is the answer ``/lsp`` browses.
        """
        from ..integrations import lsp as lsp_module

        return {
            "servers": lsp_module.discover_servers(),
            "plain_explanation": lsp_module.PLAIN_EXPLANATION,
        }

    def lsp_diagnostics(self, path: str) -> dict[str, Any]:
        """One workspace file's language-server diagnostics (M-049).

        The file is resolved inside this session's workspace;
        a path escaping it is refused. The report is honest
        about absence: no catalogued server for the file's
        language, or a server that is not installed, comes
        back as the report's status with its reason — never
        as an empty, supposedly-clean diagnostic list. A
        server that runs and fails raises LSPError.
        """
        from ..core.workspace import assert_within_workspace
        from ..integrations import lsp as lsp_module

        resolved = assert_within_workspace(self.project_root, path)
        if not resolved.is_file():
            raise ValueError(f"no such file to check: {path}")
        report = lsp_module.diagnostics_for_file(
            resolved, root=self.project_root)
        return {
            "report": report.record(),
            "plain_explanation": lsp_module.PLAIN_EXPLANATION,
        }

    def _lsp_navigation_file(self, path: str) -> Any:
        from ..core.workspace import assert_within_workspace

        resolved = assert_within_workspace(self.project_root, path)
        if not resolved.is_file():
            raise ValueError(f"no such file to check: {path}")
        return resolved

    def lsp_definition(self, path: str, line: int,
                       character: int) -> dict[str, Any]:
        """Where a name is defined, per the language server (M-050).

        The file is resolved inside this session's workspace;
        a path escaping it is refused. Absence is honest: a
        missing server comes back as the report's status,
        never as a found answer.
        """
        from ..integrations import lsp as lsp_module

        resolved = self._lsp_navigation_file(path)
        report = lsp_module.definition_for_file(
            resolved, line, character, root=self.project_root)
        return {
            "report": report.record(),
            "plain_explanation": lsp_module.NAVIGATION_PLAIN_EXPLANATION,
        }

    def lsp_references(self, path: str, line: int,
                       character: int) -> dict[str, Any]:
        """Every use of a name, per the language server (M-050)."""
        from ..integrations import lsp as lsp_module

        resolved = self._lsp_navigation_file(path)
        report = lsp_module.references_for_file(
            resolved, line, character, root=self.project_root)
        return {
            "report": report.record(),
            "plain_explanation": lsp_module.NAVIGATION_PLAIN_EXPLANATION,
        }

    def lsp_hover(self, path: str, line: int,
                  character: int) -> dict[str, Any]:
        """What the language server says about a spot (M-050)."""
        from ..integrations import lsp as lsp_module

        resolved = self._lsp_navigation_file(path)
        report = lsp_module.hover_for_file(
            resolved, line, character, root=self.project_root)
        return {
            "report": report.record(),
            "plain_explanation": lsp_module.NAVIGATION_PLAIN_EXPLANATION,
        }

    def lsp_rename(self, path: str, line: int, character: int,
                   new_name: str, apply: bool = False) -> dict[str, Any]:
        """Plan (or apply) a server rename of a name (M-051).

        Preview by default: the report carries the server's
        per-file plan with its diff previews and nothing is
        written. With *apply* true the plan is applied
        through the house edit journal (plan-time hashes
        checked per file; a changed file is refused whole).
        Absence is honest exactly as on the navigation road:
        a missing server is the report's status, never a
        faked rename by text substitution.
        """
        from ..integrations import lsp as lsp_module

        resolved = self._lsp_navigation_file(path)
        report = lsp_module.rename_for_file(
            resolved, line, character, new_name,
            root=self.project_root, apply=apply)
        return {
            "report": report.record(),
            "plain_explanation": lsp_module.RENAME_PLAIN_EXPLANATION,
        }

    def lsp_code_actions(self, path: str, line: int, character: int,
                         apply_index: int | None = None
                         ) -> dict[str, Any]:
        """The server's code actions at a spot (M-051).

        Lists the actions as plain records; with
        *apply_index* (0-based, into the listed actions)
        the chosen action's edit is applied through the
        edit journal. A command-only action is reported
        honestly in the report's apply_note — its command
        is never executed.
        """
        from ..integrations import lsp as lsp_module

        resolved = self._lsp_navigation_file(path)
        report = lsp_module.code_actions_for_file(
            resolved, line, character, root=self.project_root,
            apply_index=apply_index)
        return {
            "report": report.record(),
            "plain_explanation": lsp_module.RENAME_PLAIN_EXPLANATION,
        }

    def edit_truth(self, path: str) -> dict[str, Any]:
        """One file's standing edit-time truth account (M-052).

        Every leg that truly runs reports its current
        error findings; a leg that cannot run — no
        language server installed, no linter configured —
        reports its absence as its status, never as a
        clean file. The file is resolved inside this
        session's workspace; a path escaping it is refused.
        """
        from ..core.workspace import assert_within_workspace
        from ..tools import edit_truth as truth_module

        resolved = assert_within_workspace(self.project_root, path)
        if not resolved.is_file():
            raise ValueError(f"no such file to check: {path}")
        report = truth_module.check_file_now(
            resolved, root=self.project_root)
        return {
            "report": report.record(),
            "plain_explanation": truth_module.PLAIN_EXPLANATION,
        }

    def type_depth(self, path: str | None = None) -> dict[str, Any]:
        """A standing type account — one file's, or the workspace's (M-063).

        The runners are mypy and pyright, whichever truly
        exist; a runner that is not installed reports
        not-installed and a live type verdict without one
        is NOT PROVEN, never a clean bill. Findings are
        triaged by kind into the review. A named file is
        resolved inside this session's workspace; a path
        escaping it is refused. A switched-off road reads
        nothing.
        """
        from ..tools import type_depth as depth_module

        enabled = depth_module.enabled_from_config(
            getattr(self, "config", None))
        if path is not None:
            from ..core.workspace import assert_within_workspace

            resolved = assert_within_workspace(self.project_root, path)
            if not resolved.is_file():
                raise ValueError(f"no such file to check: {path}")
            report = depth_module.type_depth(
                self.project_root, resolved, enabled=enabled)
        else:
            report = depth_module.type_depth(
                self.project_root, enabled=enabled)
        return {
            "report": report.record(),
            "plain_explanation": depth_module.PLAIN_EXPLANATION,
        }

    def format_covenant(self, path: str, *, apply: bool = False) -> dict[str, Any]:
        """One touched file's formatter-covenant account (M-053).

        The file the user names on this road is itself the
        touched file — their own act names it. The preview
        runs the project's own configured formatter (never
        an invented style, never on untouched code) and
        separates the format diff from the logic diff;
        *apply* writes only through the edit journal, and
        only while the file still matches the preview.
        A project with no formatter configured, or the
        covenant switched off in config, is reported
        plainly and nothing is formatted.
        """
        from ..core.workspace import assert_within_workspace
        from ..tools import format_covenant as covenant_module

        resolved = assert_within_workspace(self.project_root, path)
        if not resolved.is_file():
            raise ValueError(f"no such file to format-check: {path}")
        report = covenant_module.format_covenant_report(
            resolved, root=self.project_root, touched=[resolved],
            apply=apply,
            enabled=covenant_module.enabled_from_config(
                getattr(self, "config", None)))
        return {
            "report": report.record(),
            "plain_explanation": covenant_module.PLAIN_EXPLANATION,
        }

    def debugger_status(self) -> dict[str, Any]:
        """Which debug adapters this machine has (M-054).

        The discovery board: every catalogued adapter with
        its installed state — an adapter that is not
        installed is named with its install remedy, never
        hidden. This is the answer ``/debug`` browses.
        """
        from ..tools import debugger as debugger_module

        return {
            "adapters": debugger_module.discover_adapters(),
            "plain_explanation": debugger_module.PLAIN_EXPLANATION,
        }

    def debug_run(self, path: str, *, breakpoints: Any = None,
                  steps: Any = None,
                  stop_on_exception: bool = False) -> dict[str, Any]:
        """Run one workspace program under the debugger (M-054).

        The program is resolved inside this session's
        workspace; a path escaping it is refused. The
        report is honest about absence: no catalogued
        adapter, or an adapter that is not installed,
        comes back as the report's status with its reason
        — never as a faked session with invented frames.
        An adapter that runs and fails raises DAPError.
        Breakpoints name lines in the program file itself.
        """
        from ..core.workspace import assert_within_workspace
        from ..tools import debugger as debugger_module

        resolved = assert_within_workspace(self.project_root, path)
        if not resolved.is_file():
            raise ValueError(f"no such file to debug: {path}")
        report = debugger_module.run_debug_session(
            resolved, root=self.project_root,
            breakpoints=list(breakpoints or []),
            steps=list(steps or []),
            stop_on_exception=bool(stop_on_exception),
            enabled=debugger_module.enabled_from_config(
                getattr(self, "config", None)))
        return {
            "report": report.record(),
            "plain_explanation": debugger_module.PLAIN_EXPLANATION,
        }

    def debug_loop(self, test: str, *, breakpoints: Any = None) -> dict[str, Any]:
        """Re-run one failing test under the debugger (M-055).

        The test node names a file inside this session's
        workspace (a path escaping it is refused) and,
        after ``::``, the test itself. The re-run launches
        the pytest module under M-054's adapter with
        exception stops on; the report's evidence is the
        stop's frames and locals exactly as the adapter
        reported them. Absence is honest: an adapter that
        is not installed, a re-run that never stops, and
        the loop switched off each come back as the
        report's status — never as invented evidence.
        """
        from ..core.workspace import assert_within_workspace
        from ..tools import debug_loop as loop_module

        file_part, _name = loop_module.split_test_node(test)
        resolved = assert_within_workspace(self.project_root, file_part)
        report = loop_module.debug_failing_test(
            test, root=self.project_root,
            breakpoints=list(breakpoints or []),
            enabled=loop_module.enabled_from_config(
                getattr(self, "config", None)))
        return {
            "report": report.record(),
            "plain_explanation": loop_module.PLAIN_EXPLANATION,
        }

    def test_intel_status(self) -> dict[str, Any]:
        """The test-intelligence board for this project (M-056).

        Discovery is pytest's own collection for this
        session's workspace, and the history account is the
        recorded history store's — a switched-off road
        reports disabled discovery, never an invented list.
        """
        from ..tools import test_intelligence as intel_module

        return intel_module.board_report(
            self.project_root,
            enabled=intel_module.enabled_from_config(
                getattr(self, "config", None)))

    def test_intel_select(self, changed_files: Any) -> dict[str, Any]:
        """Select the tests a change touches (M-056).

        Changed files are resolved inside this session's
        workspace where they exist there; the selection is
        the symbol graph's answer or the honest whole-suite
        fallback with its reason.
        """
        from ..tools import test_intelligence as intel_module

        report = intel_module.select_tests(
            list(changed_files or []), root=self.project_root,
            enabled=intel_module.enabled_from_config(
                getattr(self, "config", None)))
        return {
            "selection": report.record(),
            "plain_explanation": intel_module.PLAIN_EXPLANATION,
        }

    def test_intel_history(self) -> dict[str, Any]:
        """The recorded test history and its flaky marks (M-056)."""
        from ..tools import test_intelligence as intel_module

        report = intel_module.history_report(self.project_root)
        return {
            "history": report.record(),
            "plain_explanation": intel_module.PLAIN_EXPLANATION,
        }

    def coverage_status(self) -> dict[str, Any]:
        """The coverage board for this project (M-057).

        Whether coverage.py data exists for this session's
        workspace and what it totals — a switched-off road
        reports disabled, never an estimated percentage.
        """
        from ..tools import coverage_sight as coverage_module

        return coverage_module.board_report(
            self.project_root,
            enabled=coverage_module.enabled_from_config(
                getattr(self, "config", None)))

    def coverage_check(self, changed_files: Any) -> dict[str, Any]:
        """Lay coverage over the files a change touched (M-057).

        The overlay is coverage.py's own measured lines;
        a touched file whose measured lines never ran is
        flagged to the Auditor in the audit log as part of
        the check, and the report says how many flags were
        written.
        """
        from ..tools import coverage_sight as coverage_module

        report = coverage_module.coverage_check(
            list(changed_files or []), root=self.project_root,
            enabled=coverage_module.enabled_from_config(
                getattr(self, "config", None)))
        return {
            "report": report.record(),
            "plain_explanation": coverage_module.PLAIN_EXPLANATION,
        }

    def local_search(self, query: str, mode: str = "text",
                     language: Any = None) -> dict[str, Any]:
        """Beyond-grep local search over this workspace (M-058).

        One search, three modes: text (an in-process
        ripgrep-class regex search over every text file),
        fuzzy (subsequence matching with an auditable
        score), and structural (delegated to M-047's
        engine, which needs *language*). Results are
        ranked by the M-046 symbol graph and every match
        carries its score and reasons; a switched-off
        road reports disabled, and a refused pattern
        raises — it is never searched another way.
        """
        from ..tools import local_search as search_module

        report = search_module.search(
            self.project_root, query, mode=mode, language=language,
            enabled=search_module.enabled_from_config(
                getattr(self, "config", None)))
        return {
            "report": report.record(),
            "plain_explanation": search_module.PLAIN_EXPLANATION,
        }

    def web_search(self, query: str) -> dict[str, Any]:
        """Search the web once, through the configured endpoint (M-059).

        The query text goes to the ``web_search_endpoint``
        host (the shipped default is DuckDuckGo's keyless
        HTML road) and nowhere else; the results come back
        as numbered citations. When a session is attached,
        the sources are cited into the session journal as
        a ``web_citation`` checkpoint event before the
        status is returned. A failed call is an honest
        error report; a switched-off road sends nothing.
        """
        from ..tools import web_search as web_module

        report = web_module.web_search(
            query,
            endpoint=web_module.endpoint_from_config(
                getattr(self, "config", None)),
            enabled=web_module.enabled_from_config(
                getattr(self, "config", None)))
        self._journal_web_citation(report)
        return {
            "report": report.record(),
            "plain_explanation": web_module.PLAIN_EXPLANATION,
        }

    def web_fetch(self, url: str) -> dict[str, Any]:
        """Fetch one http(s) page's readable text (M-059).

        Only the named page is requested; its title and
        text come back under the module's caps, and the
        page is cited into the session journal as a
        ``web_citation`` event when a session is attached.
        Non-http(s) URLs are refused before anything is
        sent; a failed call is an honest error report.
        """
        from ..tools import web_search as web_module

        report = web_module.web_fetch(
            url,
            enabled=web_module.enabled_from_config(
                getattr(self, "config", None)))
        self._journal_web_citation(report)
        return {
            "report": report.record(),
            "plain_explanation": web_module.PLAIN_EXPLANATION,
        }

    def docs_list(self) -> dict[str, Any]:
        """The offline docs shelf's catalogue (M-060).

        The workspace's own docs (root and ``docs/`` doc
        files) plus any offline doc packs under
        ``.mythic/docpacks/``, each with its title and
        source. Nothing is fetched; a switched-off road
        reads nothing.
        """
        from ..tools import docs_at_hand as docs_module

        report = docs_module.docs_list(
            self.project_root,
            enabled=docs_module.enabled_from_config(
                getattr(self, "config", None)))
        return {
            "report": report.record(),
            "plain_explanation": docs_module.PLAIN_EXPLANATION,
        }

    def docs_search(self, query: str) -> dict[str, Any]:
        """Rank the offline docs shelf against a query (M-060)."""
        from ..tools import docs_at_hand as docs_module

        report = docs_module.docs_search(
            self.project_root, query,
            enabled=docs_module.enabled_from_config(
                getattr(self, "config", None)))
        return {
            "report": report.record(),
            "plain_explanation": docs_module.PLAIN_EXPLANATION,
        }

    def docs_read(self, name: str) -> dict[str, Any]:
        """Read one shelf doc whole, by path, name or title (M-060).

        A name matching nothing is an honest error report;
        a name matching several docs is refused with the
        candidates named — a doc is never guessed.
        """
        from ..tools import docs_at_hand as docs_module

        report = docs_module.docs_read(
            self.project_root, name,
            enabled=docs_module.enabled_from_config(
                getattr(self, "config", None)))
        return {
            "report": report.record(),
            "plain_explanation": docs_module.PLAIN_EXPLANATION,
        }

    def dependency_sight(self, package: str | None = None) -> dict[str, Any]:
        """The declared dependency graph, or one package's account (M-061).

        The graph is read from this workspace's own
        ``pyproject.toml`` — groups, specs, and the
        honestly measured installed version (unknown when
        a package is not installed). A named package adds
        its blast radius (workspace files importing it,
        counted from the tree), its local changelog
        mentions, and its local vulnerability-data state.
        Changelogs and vulnerability data are local files
        only; a switched-off road reads nothing.
        """
        from ..tools import dependency_sight as deps_module

        report = deps_module.dependency_sight(
            self.project_root, package,
            enabled=deps_module.enabled_from_config(
                getattr(self, "config", None)))
        return {
            "report": report.record(),
            "plain_explanation": deps_module.PLAIN_EXPLANATION,
        }

    def dependency_proposal(self, package: str,
                            target_version: str) -> dict[str, Any]:
        """Draft one upgrade proposal — data only, never applied (M-061).

        The proposal carries the declared spec(s), the
        installed version, the target, the counted blast
        radius, and whether anything else pins the
        package. An undeclared package is refused
        plainly; nothing is written on this road.
        """
        from ..tools import dependency_sight as deps_module

        report = deps_module.dependency_proposal(
            self.project_root, package, target_version,
            enabled=deps_module.enabled_from_config(
                getattr(self, "config", None)))
        return {
            "report": report.record(),
            "plain_explanation": deps_module.PLAIN_EXPLANATION,
        }

    def code_sensing(self, mode: str = "show") -> dict[str, Any]:
        """A structural sensing report — dead code + duplication (M-062).

        Dead code is sensed by the shipped dead-code
        scanner over this workspace's top-level Python
        packages; duplication clusters are function bodies
        whose AST structure matches exactly once names and
        literal values are normalised away, at or above
        the slice's size floor. Sensing only — nothing is
        deleted or edited on this road; a switched-off
        road reads nothing.
        """
        from ..tools import code_sensing as sensing_module

        report = sensing_module.code_sensing(
            self.project_root, mode,
            enabled=sensing_module.enabled_from_config(
                getattr(self, "config", None)))
        return {
            "report": report.record(),
            "plain_explanation": sensing_module.PLAIN_EXPLANATION,
        }

    def mojo_sight(self, mode: str = "show",
                   target: str | None = None,
                   term: str = "") -> dict[str, Any]:
        """A Mojo account — scan, one file, or knowledge (M-064).

        Mojo files are recognised through the tree-sitter
        foundation's catalogue and parsed via its grammar
        where one truly loads; no Mojo grammar package
        exists today, so files are read by the honestly
        named mojo-scan structural backend and a
        grammar-backed parse is NOT PROVEN. Removed syntax
        is flagged with its replacement from the house
        Mojo skills, whose distilled knowledge the
        knowledge road searches. Read-only — nothing is
        edited on this road; a switched-off road reads
        nothing.
        """
        from ..tools import mojo_sight as mojo_module

        report = mojo_module.mojo_sight(
            self.project_root, mode, target=target, term=term,
            enabled=mojo_module.enabled_from_config(
                getattr(self, "config", None)))
        return {
            "report": report.record(),
            "plain_explanation": mojo_module.PLAIN_EXPLANATION,
        }

    def sql_sight(self, mode: str = "show",
                  db: str | None = None,
                  query: str = "") -> dict[str, Any]:
        """A SQL account — schemas, explain, or migrations (M-065).

        Workspace-local SQLite databases are opened
        through read-only connections only; a query is
        explained, never executed, and write-shaped
        statements are refused; migration files are read
        as code, never applied. Read-only — nothing is
        written on this road; a switched-off road reads
        nothing.
        """
        from ..tools import sql_sight as sql_module

        report = sql_module.sql_sight(
            self.project_root, mode, db=db, query=query,
            enabled=sql_module.enabled_from_config(
                getattr(self, "config", None)))
        return {
            "report": report.record(),
            "plain_explanation": sql_module.PLAIN_EXPLANATION,
        }

    def config_sight(self, mode: str = "show",
                     target: str | None = None) -> dict[str, Any]:
        """A config account — structure of config/infra files (M-066).

        YAML, TOML, INI, systemd units, Dockerfiles and
        compose files are parsed structurally (kinds and
        sizes, never scalar values); nothing a file
        describes is executed. Docker artifacts in a
        workspace marked as Volmarr's project raise the
        coder's own no-Docker-law warning. Read-only —
        nothing is written on this road; a switched-off
        road reads nothing.
        """
        from ..tools import config_sight as config_module

        report = config_module.config_sight(
            self.project_root, mode, target=target,
            enabled=config_module.enabled_from_config(
                getattr(self, "config", None)))
        return {
            "report": report.record(),
            "plain_explanation": config_module.PLAIN_EXPLANATION,
        }

    def asset_sight(self, mode: str = "show",
                    target: str | None = None) -> dict[str, Any]:
        """An asset account — images, archives, large files (M-067).

        Images are described from their headers, archives
        from their member listings, and large files by
        size and kind; every asset carries the role the
        map notes for it. Nothing is decoded, extracted
        or dumped. Read-only — nothing is written on this
        road; a switched-off road reads nothing.
        """
        from ..tools import asset_sight as asset_module

        report = asset_module.asset_sight(
            self.project_root, mode, target=target,
            enabled=asset_module.enabled_from_config(
                getattr(self, "config", None)))
        return {
            "report": report.record(),
            "plain_explanation": asset_module.PLAIN_EXPLANATION,
        }

    def language_packs(self, mode: str = "show",
                       language: str | None = None) -> dict[str, Any]:
        """A language-packs account — toolchains as data (M-068).

        Every pack declares one language's toolchain — its
        language server, formatters, and test runners — in
        data; the report describes each declared command
        and PATH-checks its binary. Nothing is executed on
        this road; a switched-off road does not even load
        the pack data.
        """
        from ..tools import language_packs as packs_module

        report = packs_module.language_packs_report(
            self.project_root, mode, language=language,
            enabled=packs_module.enabled_from_config(
                getattr(self, "config", None)))
        return {
            "report": report.record(),
            "plain_explanation": packs_module.PLAIN_EXPLANATION,
        }

    def intelligence_cache(self, mode: str = "show",
                           target: str | None = None) -> dict[str, Any]:
        """An intelligence-cache account — results per file hash (M-069).

        Parse, graph, and language-server results are cached
        under the workspace's .mythic/intelligence-cache/,
        keyed by each file's SHA-256 content hash; a changed
        file's entry is evicted on lookup, never served.
        Warming writes cache entries only, never a source
        file; a switched-off road reads and writes nothing.
        """
        from ..tools import intelligence_cache as cache_module

        report = cache_module.intelligence_cache_report(
            self.project_root, mode, target=target,
            enabled=cache_module.enabled_from_config(
                getattr(self, "config", None)))
        return {
            "report": report.record(),
            "plain_explanation": cache_module.PLAIN_EXPLANATION,
        }

    def _journal_web_citation(self, report: Any) -> None:
        """Cite one web report's sources into the journal (M-059)."""
        if report.status != "ok":
            return
        if getattr(self, "_session_store", None) and \
                getattr(self, "session_id", None):
            self._checkpoint(report.citation_event())
            report.journaled = True

    def lsp_workspace_symbols(self, query: str = "") -> dict[str, Any]:
        """The workspace's symbols, per the language server (M-050)."""
        from ..integrations import lsp as lsp_module

        report = lsp_module.workspace_symbols_for(
            root=self.project_root, query=query)
        return {
            "report": report.record(),
            "plain_explanation": lsp_module.NAVIGATION_PLAIN_EXPLANATION,
        }

    def repo_map_detail(self, path: str) -> dict[str, Any]:
        """One file's full account from the repo map (M-045).

        The map is built with no task query, so the detail
        is the file's standing account: its rank, its score
        arithmetic, its definitions, its references, and
        every reason — or, when the build did not rank it,
        its honest state (omitted over the budget, skipped
        with the build's reason, or absent). The name is
        resolved as the user gave it: an exact path, or a
        unique file name or path tail.
        """
        from ..context import repo_map_view
        from ..context.repo_map import build_repo_map

        repo_map = build_repo_map(self.project_root)
        detail = repo_map_view.resolve_detail(
            repo_map, repo_map_view.pins_from_config(self.config), path)
        return {
            "detail": detail.record(),
            "plain_explanation": repo_map_view.PLAIN_EXPLANATION,
        }

    def repo_map_pins(self) -> dict[str, Any]:
        """The session's pinned map files (M-045).

        The validated pins exactly as stored — a malformed
        stored list raises, never vanishes.
        """
        from ..context import repo_map_view

        return {
            "pins": list(repo_map_view.pins_from_config(self.config)),
            "plain_explanation": repo_map_view.PLAIN_EXPLANATION,
        }

    def pin_repo_map_file(self, path: str) -> dict[str, Any]:
        """Pin one workspace file to the map view (M-045).

        The path is validated by the view layer (relative,
        inside the workspace, not already pinned) and the
        file must exist in this workspace — pinning a file
        that is not there is refused plainly. The change is
        journaled first as a ``repo_map_pins_changed``
        event when a session is attached; a failed save
        restores the previous pins exactly.
        """
        from ..context import repo_map_view
        from ..core.workspace import assert_within_workspace

        named = repo_map_view.normalize_pin_path(path)
        try:
            resolved = assert_within_workspace(
                self.project_root, self.project_root / named)
        except Exception as exc:
            raise ValueError(
                f"Cannot pin {named}: it is not inside this "
                f"workspace. {exc}") from exc
        if not resolved.is_file():
            raise ValueError(
                f"Cannot pin {named}: no such file exists in "
                "this workspace, so there is nothing to pin.")
        return self._change_repo_map_pins("pin", named)

    def unpin_repo_map_file(self, path: str) -> dict[str, Any]:
        """Unpin one file (M-045). Journaled like any pin change."""
        return self._change_repo_map_pins("unpin", path)

    def _change_repo_map_pins(self, action: str,
                              path: str) -> dict[str, Any]:
        import copy

        from ..context import repo_map_view

        if action == "pin":
            new_value, change = repo_map_view.pin_file(self.config, path)
        elif action == "unpin":
            new_value, change = repo_map_view.unpin_file(self.config, path)
        else:  # pragma: no cover - internal dispatch only
            raise ValueError(f"Unknown repo-map pin change {action!r}")
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[repo_map_view.PINS_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "repo_map_pins_change_reverted",
                        "action": change.kind,
                        "path": change.path,
                        "reason": "The pin change could not be "
                                  "saved; the previous pins were "
                                  "preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Pin change could not be saved; previous pins "
                "were preserved")
        return change.record(self.session_id, journaled)

    def salvaged_partial(self) -> dict[str, Any] | None:
        """The salvaged partial answer waiting in this history (M-034).

        The last marked partial assistant message in the live
        history, as a record with its history ``index``, its
        verbatim ``partial_text``, and the session's current
        ``model`` — or None when no interrupted answer is
        waiting. This is what ``/resume-thought show`` reads.
        """
        from ..core.streaming_discipline import find_partial

        found = find_partial(self.history_snapshot())
        if found is None:
            return None
        index, text = found
        return {"index": index, "partial_text": text,
                "model": self.config.get("model")}

    def resume_thought(self) -> str:
        """Continue the salvaged partial answer (M-034).

        Refuses plainly — raising RuntimeError, changing
        nothing, journaling nothing — when no salvaged partial
        waits in the history, or when the current model's
        streaming truth (M-027) is not known-true: a resume is
        offered only where the door is known to allow it (see
        :func:`mythic_agent.core.streaming_discipline.can_resume`).
        Otherwise the resume is journaled *first* as a
        ``thought_resumed`` checkpoint event, and the
        continuation runs as an ordinary turn through
        :meth:`chat` with the core layer's resume prompt — the
        partial itself stays in the history above it, marked as
        partial, and the continuation is appended after it.
        Returns the continuation's text.
        """
        from ..core.streaming_discipline import can_resume, resume_prompt

        partial = self.salvaged_partial()
        if partial is None:
            raise RuntimeError(
                "No interrupted answer is waiting to be resumed: "
                "this conversation holds no partial answer, so "
                "there is no thought to continue. Nothing was "
                "changed.")
        decision = can_resume(self.config.get("model"))
        if not decision.allowed:
            raise RuntimeError(decision.reason)
        if self._session_store and self.session_id:
            self._checkpoint({
                "type": "thought_resumed",
                "model": decision.model,
                "partial_chars": len(partial["partial_text"]),
            })
        return self.chat(resume_prompt(partial["partial_text"]))

    def retry_status(self) -> dict[str, Any]:
        """The retry bounds and the last request's report (M-035).

        The bounds the current runtime settings imply (named,
        with their planned and worst-case wait totals), the
        last finished retry report for a provider request in
        this session (None until a request finishes), and the
        plain explanation. This is the answer ``/retry``
        shows; nothing about it is hidden.
        """
        from ..core.retry_honesty import (
            MUTATING_RULE,
            PLAIN_EXPLANATION,
            bounds_from_settings,
        )

        bounds = bounds_from_settings(runtime_settings(self.config))
        return {
            "bounds": bounds,
            "report": self.last_retry_report,
            "last_report": self.last_retry_report,
            "plain_explanation": PLAIN_EXPLANATION,
            "mutating_rule": MUTATING_RULE,
        }

    # -- M-036: rate-limit weather -------------------------------------

    def _weather_key(self) -> str:
        """The weather-board key for this agent's current door."""
        from ..core.rate_limit_weather import weather_key_for

        return weather_key_for(self.config)

    def _note_limit_error(self, exc: Exception) -> None:
        """Record a failed request's limit signal (M-036).

        Only a real signal is recorded — a 429, or the limit
        headers the door actually sent; any other failure
        records nothing. When the door newly turns limited,
        the turn is journaled as a ``rate_limit_seen``
        checkpoint. Recording never raises: the failure being
        handled is the truth owed, not the weather.
        """
        try:
            key = self._weather_key()
            before = self._weather_board.weather_for(key)
            weather = self._weather_board.record_error(key, exc)
        except Exception:
            return
        if weather is None:
            return
        if weather.state == "limited" and before.state != "limited" \
                and self._session_store and self.session_id:
            try:
                self._checkpoint({
                    "type": "rate_limit_seen",
                    "provider": key,
                    "limited_until": weather.limited_until,
                    "source": weather.source,
                })
            except Exception:
                pass  # the weather is recorded; the request's
                # own outcome is handled by the caller

    def _note_weather_success(self) -> None:
        """Record that this agent's door just answered (M-036)."""
        try:
            self._weather_board.record_success(self._weather_key())
        except Exception:
            pass

    def weather_status(self) -> dict[str, Any]:
        """The shared board's weather, in plain data (M-036).

        Every recorded door's weather (state, the quota the
        door itself reported, its reset when known), this
        agent's own door and its queue decision, and the
        plain explanation. This is the answer ``/weather``
        shows; nothing about it is hidden, and a door with no
        recorded signal is honestly ``unknown``.
        """
        from ..core.rate_limit_weather import (
            PLAIN_EXPLANATION,
            QUEUE_MAX_WAIT_S,
            queue_decision,
        )

        now = time.time()
        key = self._weather_key()
        weather = self._weather_board.weather_for(key, now=now)
        decision = queue_decision(weather, now=now)
        return {
            "providers": [
                entry.to_dict(now)
                for entry in self._weather_board.snapshot(now=now)],
            "current_provider": key,
            "current": weather.to_dict(now),
            "decision": decision,
            "queue_max_wait_s": QUEUE_MAX_WAIT_S,
            "plain_explanation": PLAIN_EXPLANATION,
        }

    def _queue_around_rate_limit(self) -> None:
        """Queue this request around a known limit (M-036).

        When the current door's recorded weather says it is
        limited until a known reset within the queueing
        bound, the request waits — announced on the chat
        surface and journaled as ``rate_limit_queued`` —
        until the reset passes. The wait rides the agent's
        cancel event, so a cancelled queue sends nothing and
        raises TurnCancelled. Every other weather (clear,
        unknown, a reset beyond the bound, or no known reset)
        proceeds at once: the decision's reason has already
        been surfaced by /weather, and M-035's retries /
        M-030's fallback walk own what happens next.
        """
        from ..core.rate_limit_weather import queue_decision

        key = self._weather_key()
        weather = self._weather_board.weather_for(key)
        decision = queue_decision(weather, now=time.time())
        if decision.action != "wait":
            return
        if self._session_store and self.session_id:
            try:
                self._checkpoint({
                    "type": "rate_limit_queued",
                    "provider": key,
                    "wait_s": decision.wait_s,
                    "limited_until": decision.limited_until,
                })
            except Exception:
                pass  # the wait itself is the road; a journal
                # failure must not un-queue the request
        publish_sync(
            "agent_chat_chunk", agent_name=self.name,
            text=f"\nRate-limit weather: {decision.reason} "
                 f"Waiting {decision.wait_s:.0f}s before "
                 f"sending.\n")
        if self._cancel.wait(decision.wait_s):
            raise TurnCancelled(
                "Turn cancelled while queued around a rate limit")

    def _make_retry_event(self, exc: Exception, attempt: int,
                          limit: int, decision: str,
                          delay: float | None = None) -> Any:
        """One retry event for *exc* at 0-based loop *attempt* (M-035)."""
        from ..core.retry_honesty import RetryEvent, classify_error

        failure = classify_error(exc)
        return RetryEvent(
            attempt=attempt + 1, limit=limit, kind=failure.kind,
            status=failure.status, error=str(exc), delay=delay,
            decision=decision)

    def _emit_retrying(self, recorder: Any, exc: Exception, attempt: int,
                       settings: dict[str, Any]) -> float:
        """Record, announce, and journal one retrying event (M-035).

        Returns the wait before the next attempt. The formatted
        event sentence — attempt and budget, the reason, and
        the wait — is published on the chat-tool channel, and
        the event is journaled as a ``retry_attempt`` session
        event when a session store is attached; a journaling
        failure never breaks the request.
        """
        from ..core.retry_honesty import format_retry_event

        delay = _retry_delay(exc, attempt, settings)
        event = self._make_retry_event(
            exc, attempt, settings["max_retries"], "retrying",
            delay=delay)
        recorder.record(event)
        publish_sync("agent_chat_tool", agent_name=self.name,
                     text=f"\n{format_retry_event(event)}\n")
        if self._session_store and self.session_id:
            try:
                self._checkpoint({"type": "retry_attempt",
                                  **event.record()})
            except Exception:
                pass  # journaling never breaks the request
        return delay

    def _finish_retry(self, recorder: Any, stopped_reason: str,
                      attempts_made: int) -> Any:
        """Finish a request's retry report and keep it (M-035).

        The finished report becomes ``last_retry_report``; when
        the request used at least one retry, its termination is
        journaled as a ``retry_stopped`` session event when a
        session store is attached (a journaling failure never
        breaks the request).
        """
        report = recorder.finish(stopped_reason, attempts_made)
        self.last_retry_report = report
        if report.retries_used >= 1 \
                and self._session_store and self.session_id:
            try:
                self._checkpoint({
                    "type": "retry_stopped",
                    "stopped_reason": report.stopped_reason,
                    "retries_used": report.retries_used,
                    "attempts_made": report.attempts_made,
                    "succeeded": report.succeeded,
                    "events": [event.record()
                               for event in report.events],
                })
            except Exception:
                pass  # journaling never breaks the request
        return report

    def kista_status(self) -> dict[str, Any]:
        """Where every door's key lives, and whether one is held (M-032).

        The custody board exactly as :mod:`mythic_agent.core.
        key_custody` reads it — per door: Kista reference,
        environment, legacy plaintext, missing, or not-needed
        (loopback) — plus whether Kista's vault file is
        configured. No key value is ever part of the answer;
        this is what ``/kista`` shows.
        """
        from ..core import key_custody

        return {
            "entries": [entry.record() for entry in
                        key_custody.custody_entries(self.config)],
            "vault_configured": key_custody.vault_path() is not None,
            "vault_file": (str(key_custody.vault_path())
                           if key_custody.vault_path() is not None
                           else None),
        }

    def adopt_key_for_kista(self, base_url: str | None = None
                            ) -> dict[str, Any]:
        """Move a door's stored plaintext key into Kista (M-032).

        The move is validated by :mod:`mythic_agent.core.
        key_custody` before anything happens (a door already
        holding a reference, a door with no stored key, an
        unconfigured vault file, or a name Kista already holds
        a different key under are each refused plainly, changing
        nothing). The adoption is then journaled *first* as a
        ``key_custody_changed`` event — door and reference
        only, never the key — the key is deposited in Kista's
        vault file, and the config is left holding only the
        reference; a failed save restores the previous config
        exactly and journals a compensating
        ``key_custody_reverted`` event (the copy Kista now
        holds stays held — custody was never the config's to
        lose).
        """
        import copy

        from ..core import key_custody

        change = key_custody.plan_adoption(self.config, base_url)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        reference, change = key_custody.adopt(self.config, base_url)
        previous = copy.deepcopy(self.config)
        if "api_keys" not in self.config:
            self.config["api_keys"] = {}
        self.config["api_keys"][change.base_url] = reference
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "key_custody_reverted",
                        "base_url": change.base_url,
                        "reference": change.reference,
                        "reason": "The config change could not be "
                                  "saved; the previous config was "
                                  "preserved. The key itself is "
                                  "held by Kista either way.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Key custody change could not be saved; previous "
                "config was preserved")
        self.redactor = SecretRedactor(self.config)
        protect_logging(self.redactor)
        return change.record(self.session_id, journaled)

    def _apply_role_route_to(self, member: Any) -> None:
        """Apply *member*'s office route to its config, if one is set."""
        route = _role_route_for(self.config, member.name)
        if route is None:
            return
        member.config["model"] = route.model
        member.config["base_url"] = route.base_url

    def _apply_role_routes(self) -> None:
        """Apply stored routes to live, idle crew members (M-029).

        A spawned member whose office holds an explicit route gets
        that route's model and door in its own config. Busy members
        are left untouched — their route lands at their next spawn.
        The Primary agent itself is never re-routed here: its
        selection is the session default (M-028 owns it).
        """
        for member_name, member in list(AGENT_REGISTRY.items()):
            if member is self or member_name == self.name:
                continue
            if member._turn_lock.locked():
                continue
            self._apply_role_route_to(member)

    def fetch_models(self, base_url: str, api_key: str) -> list[str]:
        settings = runtime_settings(self.config)
        loopback = is_loopback_url(base_url)
        if not api_key and not loopback:
            raise ProviderCredentialsError(_missing_key_remedy(base_url))
        client = CancellableChatClient(base_url, api_key or _LOOPBACK_API_KEY, self._cancel,
                                       settings["request_timeout"], settings["cancellation_poll_interval"],
                                       trust_env=not loopback)
        try:
            models_response = client.models.list()
            return [m.id for m in models_response.data]
        except TurnCancelled:
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to fetch models: {e}")



    def chat(self, prompt: str | None) -> str:
        """Execute one serialized turn and preserve the tool protocol."""
        with self._turn_lock:
            if self._closed:
                raise RuntimeError("Agent is closed")
            self._cancel.clear()
            try:
                self._session_status = "running"
                self._checkpoint({"type": "turn_started"})
                text = self._run_turn(prompt)
                self.last_result = TurnResult("completed", text, total_tokens=self.total_tokens)
                self._session_status = "completed"
                outcome = {"status": "completed", "text": text}
                self._checkpoint({"type": "turn_finished", "outcome": outcome}, outcome)
                return text
            except (Exception, KeyboardInterrupt) as exc:
                cancelled = isinstance(exc, (TurnCancelled, KeyboardInterrupt))
                status = "cancelled" if cancelled else "failed"
                self.last_result = TurnResult(status, error=str(exc), total_tokens=self.total_tokens)
                self._session_status = status
                try:
                    self._finish_pending_calls(("Turn cancelled" if cancelled else "Turn failed")
                                               + "; result unavailable. Inspect workspace before retrying.")
                    outcome = {"status": status, "error": str(exc)}
                    self._checkpoint({"type": "turn_finished", "outcome": outcome}, outcome)
                except Exception:
                    logging.exception("Failed to checkpoint interrupted turn; previous checkpoint preserved")
                if isinstance(exc, KeyboardInterrupt):
                    self.cancel()
                    raise TurnCancelled("Turn cancelled by user") from exc
                raise
            finally:
                action = self._pending_history_action
                self._pending_history_action = None
                if action == "clear":
                    self._handle_clear_history(self.name, force=True)
                elif action == "compact":
                    self._handle_compact_history(self.name, force=True)

    def _finish_pending_calls(self, reason: str) -> None:
        with self._lock:
            pending = {}
            for message in self.messages:
                if message.get("role") == "assistant":
                    pending.update({call["id"]: call for call in message.get("tool_calls", [])})
                elif message.get("role") == "tool":
                    pending.pop(message.get("tool_call_id"), None)
        recovered = [{"role": "tool", "tool_call_id": call_id, "content": reason} for call_id in pending]
        if recovered:
            with self._lock:
                self.messages.extend(recovered)
            self._checkpoint({"type": "pending_calls_closed", "messages": recovered})

    def _run_turn(self, prompt: str | None) -> str:
        settings = runtime_settings(self.config)
        if prompt:
            recalled = self._recall(prompt)
            file_context = self._compile_prompt_context(prompt)
            self._append_message({"role": "user", "content": prompt + file_context + recalled})
        for _ in range(settings["max_tool_rounds"]):
            self._check_cancelled()
            response, streamed = self._request_with_fallback(settings)
            self._check_cancelled()
            if not response.choices:
                raise RuntimeError("Provider returned no response choices")
            message = self._normalize_message(response.choices[0].message)
            usage = getattr(response, "usage", None)
            if usage:
                self.total_tokens += getattr(usage, "total_tokens", 0) or 0
                publish_sync("agent_token_update", agent_name=self.name,
                             total_tokens=self.total_tokens)
            calls = message.get("tool_calls", [])
            if not message.get("content") and not calls:
                raise RuntimeError("Provider returned an empty assistant response")
            self._append_message(message)
            text = message.get("content") or ""
            if text and not streamed:
                # Streaming already emitted each text delta exactly once.
                publish_sync("agent_chat_chunk", agent_name=self.name, text=text)
            if text:
                publish_sync("agent_chat_spoken", agent_name=self.name, text=text)
            if not calls:
                return text
            for call in calls:
                if self._cancel.is_set():
                    result = "Tool cancelled before execution."
                else:
                    result = self._execute_call(call)
                self._append_message({"role": "tool", "tool_call_id": call["id"],
                                      "content": result})
            self._check_cancelled()
        raise RuntimeError("Configured tool round budget exhausted; inspect progress and continue explicitly")

    def _check_cancelled(self) -> None:
        if self._cancel.is_set():
            raise TurnCancelled("Turn cancelled by user")

    def _recall(self, prompt: str) -> str:
        try:
            results = self.vector_db.search(prompt, top_k=2)
            if results:
                return "\n\n[Archival memory]\n" + "\n".join(r["text"] for r in results)
        except TurnCancelled:
            raise
        except Exception:
            logging.exception("Archival recall failed; continuing without retrieval")
        return ""

    def _request_response(self, client: CancellableChatClient,
                          settings: dict[str, Any]) -> tuple[Any, bool]:
        """Return ``(response, streamed)`` for one model call.

        ``streamed`` is True when the response was assembled from SSE
        deltas; callers must not re-emit its text as a single chunk.
        """
        if self.config.get("streaming"):
            return self._request_streaming(client, settings), True
        from ..core.retry_honesty import RetryRecorder

        recorder = RetryRecorder()
        limit = settings["max_retries"]
        for attempt in range(limit + 1):
            try:
                self._check_cancelled()
            except TurnCancelled:
                self._finish_retry(recorder, "cancelled", attempt)
                raise
            try:
                response = client.chat.completions.create(
                    model=self.config.get("model", config_manager.DEFAULT_MODEL),
                    messages=self.history_snapshot(), tools=get_agent_tools(),
                    stream=False, timeout=settings["request_timeout"],
                )
                self._note_weather_success()
                self._finish_retry(recorder, "succeeded", attempt + 1)
                return response, False
            except TurnCancelled:
                self._finish_retry(recorder, "cancelled", attempt + 1)
                raise
            except (APIConnectionError, APIStatusError) as exc:
                self._note_limit_error(exc)
                if not _is_transient(exc):
                    recorder.record(self._make_retry_event(
                        exc, attempt, limit, "stopped-not-transient"))
                    self._finish_retry(recorder, "not-transient",
                                       attempt + 1)
                    raise
                if attempt == limit:
                    recorder.record(self._make_retry_event(
                        exc, attempt, limit, "stopped-budget-exhausted"))
                    self._finish_retry(recorder, "budget-exhausted",
                                       attempt + 1)
                    raise
                delay = self._emit_retrying(recorder, exc, attempt, settings)
                if self._cancel.wait(delay):
                    recorder.record(self._make_retry_event(
                        exc, attempt, limit, "stopped-cancelled"))
                    self._finish_retry(recorder, "cancelled", attempt + 1)
                    raise TurnCancelled("Turn cancelled during retry") from exc
            except Exception:
                self._finish_retry(recorder, "failed", attempt + 1)
                raise
        raise RuntimeError("Provider retry budget exhausted")

    def _request_with_fallback(self, settings: dict[str, Any]) -> tuple[Any, bool]:
        """One provider request, with the M-030 fallback walk.

        The request goes to the session's current door first (the
        client is built from the current selection, and the
        request's own retry budget runs first — a walk is what
        happens *after* a door has honestly failed, never instead
        of its retries). Any failure of that request — connection,
        status (including rate-limit 429s that exhausted retries),
        credentials, or an empty/garbled response — is handed to
        :meth:`_walk_fallback`; a cancellation is never walked.

        Before anything is queued or sent, the conversation's
        image parts are gated by M-037's vision routing: a
        model that is not known to see never receives them.
        A refusal is not a provider failure — it is raised
        plainly, journaled as ``vision_refused``, and never
        walked to a fallback door.
        """
        self.gate_image_parts(self._outgoing_image_parts())
        self._queue_around_rate_limit()
        try:
            client = self.get_client()
            return self._request_response(client, settings)
        except TurnCancelled:
            raise
        except Exception as exc:
            return self._walk_fallback(exc, settings)

    def _walk_fallback(self, exc: Exception,
                       settings: dict[str, Any]) -> tuple[Any, bool]:
        """Walk the fallback chain after a provider failure (M-030).

        With no standing permission, or an empty chain, the
        original failure is re-raised untouched — the chain never
        stirs uninvited. Otherwise each door in the user's order
        is walked to in turn: the walk is **announced first**
        (published to the chat surface and journaled as a
        ``fallback_walked`` session event naming the failed door,
        its error, and the door being tried), the selection is
        applied and saved, and the request is retried on the new
        door. A door that also fails is announced as failed by the
        next walk's record. If every door fails, the original
        selection is restored and saved, a
        ``fallback_exhausted`` event is journaled, and the last
        failure is raised — the session is left exactly where it
        was, with every walk on the record.
        """
        import copy

        from ..core import fallback_chain
        from ..core.model_switch import infer_provider

        entries = fallback_chain.walk_entries(self.config)
        if not fallback_chain.permission_from_config(self.config) \
                or not entries:
            raise exc
        original = copy.deepcopy(self.config)
        last_exc: Exception = exc
        for position, entry in enumerate(entries, start=1):
            record = {
                "from": {"model": self.config.get("model"),
                         "base_url": self.config.get("base_url"),
                         "provider": infer_provider(
                             self.config.get("base_url"))},
                "to": entry.selection(),
                "error": str(last_exc),
                "position": position,
            }
            if self._session_store and self.session_id:
                self._checkpoint({"type": "fallback_walked", **record})
            publish_sync(
                "agent_chat_chunk", agent_name=self.name,
                text=f"\n{fallback_chain.format_walk(record)}\n")
            previous = copy.deepcopy(self.config)
            self.config["model"] = entry.model
            self.config["base_url"] = entry.base_url
            if not self.save_config():
                self.config = previous
                last_exc = RuntimeError(
                    "Fallback walk to "
                    f"{entry.model} ({entry.base_url}) could not be "
                    "saved; that door was skipped")
                continue
            self.redactor = SecretRedactor(self.config)
            protect_logging(self.redactor)
            try:
                client = self.get_client()
                return self._request_response(client, settings)
            except TurnCancelled:
                raise
            except Exception as next_exc:
                last_exc = next_exc
                continue
        # Every door failed: restore the original selection so the
        # session is left where it was, and put the exhaustion on
        # the journal beside the walks that led to it.
        self.config = original
        self.save_config()
        self.redactor = SecretRedactor(self.config)
        protect_logging(self.redactor)
        if self._session_store and self.session_id:
            try:
                self._checkpoint({
                    "type": "fallback_exhausted",
                    "error": str(last_exc),
                    "doors_tried": len(entries),
                })
            except Exception:
                pass  # the failure below is the truth owed
        raise last_exc

    def _request_streaming(self, client: CancellableChatClient,
                           settings: dict[str, Any]) -> Any:
        """Assemble one normalized response from SSE text/tool deltas.

        Retries apply only before the first chunk: once a partial response
        is emitted the request is never retried. Malformed or incomplete
        streams raise before any tool fragment becomes executable.
        """
        from types import SimpleNamespace

        from ..core.retry_honesty import RetryRecorder

        accumulator = _StreamAccumulator(self.name)
        recorder = RetryRecorder()
        limit = settings["max_retries"]
        for attempt in range(limit + 1):
            try:
                self._check_cancelled()
            except TurnCancelled:
                self._finish_retry(recorder, "cancelled", attempt)
                raise
            accumulator.reset()
            try:
                client.stream_chat(
                    accumulator,
                    model=self.config.get("model", config_manager.DEFAULT_MODEL),
                    messages=self.history_snapshot(), tools=get_agent_tools(),
                    stream_options={"include_usage": True},
                    timeout=settings["request_timeout"],
                )
            except TurnCancelled:
                from ..core.streaming_discipline import (
                    salvage_message,
                    salvage_notice,
                )

                salvaged = salvage_message(accumulator.text)
                self._checkpoint({"type": "stream_interrupted",
                                  "partial_text": accumulator.text,
                                  "salvaged": salvaged is not None})
                if salvaged is not None:
                    # M-034 salvage: the partial becomes a marked
                    # partial assistant message in the conversation
                    # (journaled by _append_message as a message
                    # event), and the interrupt surfaces honestly —
                    # what was kept, that it is partial, and how to
                    # resume. The salvage carries no tool calls, so
                    # the turn's turn_finished checkpoint (chat())
                    # holds a consistent history with no dangling
                    # calls.
                    self._append_message(salvaged)
                    publish_sync(
                        "agent_chat_chunk", agent_name=self.name,
                        text=f"\n{salvage_notice(accumulator.text)}\n")
                self._finish_retry(recorder, "cancelled", attempt + 1)
                raise
            except (APIConnectionError, APIStatusError) as exc:
                self._note_limit_error(exc)
                if accumulator.emitted:
                    recorder.record(self._make_retry_event(
                        exc, attempt, limit, "stopped-partial-streamed"))
                    self._finish_retry(recorder, "partial-streamed",
                                       attempt + 1)
                    raise
                if not _is_transient(exc):
                    recorder.record(self._make_retry_event(
                        exc, attempt, limit, "stopped-not-transient"))
                    self._finish_retry(recorder, "not-transient",
                                       attempt + 1)
                    raise
                if attempt == limit:
                    recorder.record(self._make_retry_event(
                        exc, attempt, limit, "stopped-budget-exhausted"))
                    self._finish_retry(recorder, "budget-exhausted",
                                       attempt + 1)
                    raise
                delay = self._emit_retrying(recorder, exc, attempt, settings)
                if self._cancel.wait(delay):
                    recorder.record(self._make_retry_event(
                        exc, attempt, limit, "stopped-cancelled"))
                    self._finish_retry(recorder, "cancelled", attempt + 1)
                    raise TurnCancelled("Turn cancelled during retry") from exc
                continue
            except Exception as exc:
                self._finish_retry(recorder, "failed", attempt + 1)
                raise RuntimeError(f"Provider stream failed: {exc}") from exc
            try:
                message = accumulator.message()
            except Exception:
                self._finish_retry(recorder, "failed", attempt + 1)
                raise
            usage = accumulator._usage
            self._note_weather_success()
            self._finish_retry(recorder, "succeeded", attempt + 1)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=message,
                                         finish_reason=accumulator._finish_reason)],
                usage=SimpleNamespace(
                    total_tokens=getattr(usage, "total_tokens", 0) or 0,
                    prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                    completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
                ) if usage is not None else None,
            )
        raise RuntimeError("Provider retry budget exhausted")

    @staticmethod
    def _normalize_message(message: Any) -> dict[str, Any]:
        raw = message if isinstance(message, dict) else message.model_dump(exclude_none=True)
        normalized = {"role": "assistant", "content": raw.get("content")}
        if raw.get("tool_calls"):
            normalized["tool_calls"] = [
                {"id": call["id"], "type": "function",
                 "function": {"name": call["function"]["name"],
                              "arguments": call["function"]["arguments"]}}
                for call in raw["tool_calls"]
            ]
        return normalized

    def _execute_call(self, call: dict[str, Any]) -> str:
        name = call["function"]["name"]
        publish_sync("agent_chat_tool", agent_name=self.name,
                     text=f"\n> Executing {name} ...\n")
        # M-109: every call through this funnel is trailed
        # exactly once, from the finally block below - the
        # kind is read from the tool itself (run_command is
        # a command, write_file / replace_file_content are
        # edits, every other tool is a tool call) and the
        # outcome word from what the call actually did.
        # The note never carries the result's text: a
        # result may be a whole file, and the trail names
        # the act, never its contents.
        parsed: dict[str, Any] = {}
        outcome = "completed"
        try:
            arguments = json.loads(call["function"]["arguments"])
            if not isinstance(arguments, dict):
                outcome = "refused: tool arguments must be a JSON object"
                return "Tool arguments must be a JSON object."
            parsed = arguments
            result = execute_tool(name, arguments, self.project_root, self.tui_app, agent=self)
            text = result if isinstance(result, str) else json.dumps(result)
            if text.startswith("Permission denied"):
                outcome = "permission denied; no operation was performed"
            elif text.startswith(("Error:", "Failed")):
                outcome = "failed"
            # M-110: a tool result is an output, and outputs
            # are fed through the hygiene redaction before
            # they travel anywhere - the caller stores this
            # text in the transcript as the tool message and
            # checkpoints it to the session journal, so this
            # one feeding covers the tool-result road and
            # the transcript road for tool content together.
            return self._hygiene_redact(text)
        except KeyboardInterrupt:
            self.cancel()
            outcome = "interrupted by user"
            return "Tool interrupted by user."
        except TurnCancelled:
            outcome = "cancelled"
            raise
        except Exception as exc:
            logging.warning("Tool %s failed: %s", name, type(exc).__name__)
            outcome = "failed"
            return self._hygiene_redact(f"Tool {name} failed: {exc}")
        finally:
            self._note_audit_tool_call(name, parsed, outcome)
            self._note_doctrine_command(name, parsed)

    # -- M-090: editor bridges lite against the real editor --

    def _editor_bridge_dir(self):
        """The editor-bridge scratch home for this workspace."""
        from ..core.config_manager import config_manager
        from ..core.workspace import workspace_id

        directory = (config_manager.MYTHIC_DIR / "editor-bridge"
                     / workspace_id(self.project_root))
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        return directory

    def editor_bridge_status(self) -> dict[str, Any]:
        """The editor-bridge gate and editor, in plain data (M-090).

        The setting exactly as stored (validated - a
        malformed stored value raises, never vanishes), the
        plain explanation, and the editor resolved honestly
        from the process environment: no editor configured
        is reported as None plus the remedy, never raised
        here and never guessed.
        """
        import os

        from ..core import editor_bridge

        editor = None
        editor_error = None
        try:
            choice = editor_bridge.resolve_editor(dict(os.environ))
        except ValueError as exc:
            editor_error = str(exc)
        else:
            editor = {"source": choice.source, "raw": choice.raw,
                      "name": choice.name,
                      "argv": list(choice.argv)}
        return {
            "enabled": editor_bridge.enabled_from_config(self.config),
            "explanation": editor_bridge.PLAIN_EXPLANATION,
            "editor": editor,
            "editor_error": editor_error,
        }

    def set_editor_bridge(self, enabled: bool) -> dict[str, Any]:
        """Turn editor bridges on or off (M-090).

        Validated by :mod:`mythic_agent.core.editor_bridge`
        before anything mutates; journaled first as an
        ``editor_bridge_setting_changed`` event when a
        session is attached; a failed save restores the
        previous value exactly and journals a compensating
        ``editor_bridge_setting_reverted``.
        """
        import copy

        from ..core import editor_bridge

        new_value, change = editor_bridge.set_enabled(
            self.config, enabled)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[editor_bridge.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "editor_bridge_setting_reverted",
                        "reason": "The editor bridge change could "
                                  "not be saved; the previous "
                                  "setting was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Editor bridge change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def _run_editor_round_trip(self, kind: str, label: str,
                               original: str,
                               environ=None) -> dict[str, Any]:
        """Run one prepared round-trip through the real editor.

        Gate first, then the editor resolved from *environ*
        (the process environment when it is None), a real
        scratch file under the agent state dir, the real
        editor process, and the pure layer's judgement. A
        changed file is written to the real file through
        the EditJournal; a prompt writes no file and its
        judged text rides the returned record.
        """
        import os
        import subprocess

        from ..core import editor_bridge
        from ..core.edits import EditJournal
        from ..core.workspace import resolve_file

        if not editor_bridge.enabled_from_config(self.config):
            raise ValueError(
                "editor bridge is off - turn it on with "
                "/editor on; nothing was edited")
        env = dict(os.environ) if environ is None else dict(environ)
        choice = editor_bridge.resolve_editor(env)
        if kind == "file":
            trip = editor_bridge.prepare_file_round_trip(label, original)
        else:
            trip = editor_bridge.prepare_prompt_round_trip(label, original)
        scratch = self._editor_bridge_dir() / trip.scratch_name
        scratch.write_text(trip.original, encoding="utf-8")
        try:
            completed = subprocess.run(
                editor_bridge.editor_command(env, str(scratch)))
            if completed.returncode != 0:
                raise ValueError(
                    f"editor {choice.name} exited with code "
                    f"{completed.returncode}; nothing was written")
            returned = scratch.read_text(encoding="utf-8")
        finally:
            try:
                scratch.unlink()
            except OSError:
                pass
        outcome = editor_bridge.judge_round_trip(trip, returned)
        if kind == "file" and outcome.status == "changed":
            journal = EditJournal(self.project_root)
            journal.write(trip.label, outcome.text)
        record: dict[str, Any] = outcome.record(trip)
        record["text"] = outcome.text
        record["editor"] = choice.name
        record["editor_source"] = choice.source
        record["journaled"] = False
        if self._session_store and self.session_id:
            event = outcome.record(trip)
            event["editor"] = choice.name
            event["editor_source"] = choice.source
            self._checkpoint(event)
            record["journaled"] = True
        return record

    def edit_file_in_editor(self, path, environ=None) -> dict[str, Any]:
        """Round-trip a real file through the user's editor (M-090).

        The file's true current text travels; a changed
        result lands through the EditJournal, an unchanged
        result writes nothing, and an emptied file refuses
        so the original stands. A missing file refuses
        plainly. With the gate off this refuses and
        launches nothing.
        """
        from ..core.workspace import resolve_file

        target = resolve_file(self.project_root, str(path), write=True)
        if not target.exists():
            raise ValueError(
                f"no file at {path} - nothing was edited")
        current = target.read_text(encoding="utf-8")
        return self._run_editor_round_trip(
            "file", str(path), current, environ=environ)

    def edit_prompt_in_editor(self, draft, label: str = "chat draft",
                              environ=None) -> dict[str, Any]:
        """Round-trip a prompt draft through the editor (M-090).

        No file is written: a changed draft returns as the
        record's text, an unchanged draft returns as it
        stood, and an emptied draft is a cancellation.
        With the gate off this refuses and launches
        nothing.
        """
        return self._run_editor_round_trip(
            "prompt", label, draft, environ=environ)


    # -- M-091: diff theatre in the TUI --

    def diff_theatre_status(self) -> dict[str, Any]:
        """The diff-theatre gate, in plain data (M-091).

        The setting exactly as stored (validated - a
        malformed stored value raises, never vanishes)
        and the plain explanation.
        """
        from ..core import diff_theatre

        return {
            "enabled": diff_theatre.enabled_from_config(self.config),
            "explanation": diff_theatre.PLAIN_EXPLANATION,
        }

    def set_diff_theatre(self, enabled: bool) -> dict[str, Any]:
        """Turn diff theatre on or off (M-091).

        Validated by :mod:`mythic_agent.core.diff_theatre`
        before anything mutates; journaled first as a
        ``diff_theatre_setting_changed`` event when a
        session is attached; a failed save restores the
        previous value exactly and journals a compensating
        ``diff_theatre_setting_reverted``.
        """
        import copy

        from ..core import diff_theatre

        new_value, change = diff_theatre.set_enabled(
            self.config, enabled)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[diff_theatre.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "diff_theatre_setting_reverted",
                        "reason": "The diff theatre change could "
                                  "not be saved; the previous "
                                  "setting was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Diff theatre change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def show_diff_theatre(self, before: str, after: str,
                          view: str = "unified",
                          ignore_whitespace: bool = False,
                          before_label: str = "before",
                          after_label: str = "after",
                          ) -> dict[str, Any]:
        """Stage one change in the diff theatre (M-091).

        Gate first: with diff theatre off this refuses and
        stages nothing. The change is staged once by the
        pure layer from the true before/after texts and
        rendered in the staged view; the staged record is
        journaled as a ``diff_theatre`` session event when
        a session is attached, and the rendered text rides
        the returned record.
        """
        from ..core import diff_theatre

        if not diff_theatre.enabled_from_config(self.config):
            raise ValueError(
                "diff theatre is off - turn it on with "
                "/diff on; nothing was staged")
        theatre = diff_theatre.build_theatre(
            before, after, view=view,
            ignore_whitespace=ignore_whitespace,
            before_label=before_label, after_label=after_label)
        record: dict[str, Any] = theatre.record()
        record["rendered"] = diff_theatre.render(theatre)
        record["journaled"] = False
        if self._session_store and self.session_id:
            self._checkpoint(theatre.record())
            record["journaled"] = True
        return record

    # -- M-092: blame and history sight --

    def blame_sight_status(self) -> dict[str, Any]:
        """The blame-sight gate, in plain data (M-092).

        The setting exactly as stored (validated - a
        malformed stored value raises, never vanishes)
        and the plain explanation.
        """
        from ..core import blame_sight

        return {
            "enabled": blame_sight.enabled_from_config(self.config),
            "explanation": blame_sight.PLAIN_EXPLANATION,
        }

    def set_blame_sight(self, enabled: bool) -> dict[str, Any]:
        """Turn blame sight on or off (M-092).

        Validated by :mod:`mythic_agent.core.blame_sight`
        before anything mutates; journaled first as a
        ``blame_sight_setting_changed`` event when a
        session is attached; a failed save restores the
        previous value exactly and journals a compensating
        ``blame_sight_setting_reverted``.
        """
        import copy

        from ..core import blame_sight

        new_value, change = blame_sight.set_enabled(
            self.config, enabled)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[blame_sight.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "blame_sight_setting_reverted",
                        "reason": "The blame sight change could "
                                  "not be saved; the previous "
                                  "setting was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Blame sight change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def _blame_journal_entries(self, path: str) -> list[dict[str, Any]]:
        """The journal's own records for *path* (M-092).

        Two real sources, neither dressed up: the edit
        journal's entries for this file (file-level
        records - the edit journal keeps no line numbers,
        so they can name the file but never a line or a
        session), and the session store's events across
        its sessions, each enriched with the session it
        belongs to so a line-covering record can name its
        writing session. A source that cannot be read
        contributes nothing - never a guessed record.
        """
        entries: list[dict[str, Any]] = []
        try:
            from ..core.edits import EditJournal

            for row in EditJournal(self.project_root).entries():
                if str(row.get("path")) == path:
                    entries.append({"type": "edit_journal",
                                    "path": path})
        except Exception:
            pass
        if self._session_store:
            try:
                sessions = self._session_store.list_sessions()
            except Exception:
                sessions = []
            for info in sessions:
                sid = info.get("id")
                if not sid:
                    continue
                try:
                    events = self._session_store.export(sid)["events"]
                except Exception:
                    continue
                for event in events:
                    if isinstance(event, dict):
                        record = dict(event)
                        record.setdefault("session_id", sid)
                        entries.append(record)
        return entries

    def show_blame_sight(self, path: str,
                         line: int | None = None,
                         ) -> dict[str, Any]:
        """Ask why a line is the way it is (M-092).

        Gate first: with blame sight off this refuses and
        blames nothing. The blame is real - ``git blame
        --porcelain`` run in the project through
        commit_craft's git road, parsed by the pure layer,
        never invented; a file git cannot blame refuses
        with git's own words. The journal's records for
        the file are matched by the pure layer: a record
        naming the file and covering the line names the
        writing session, and the note says exactly how
        far the journal reaches when it does not. The
        sight is journaled as a ``blame_sight`` session
        event when a session is attached, and the rendered
        text rides the returned record.
        """
        from ..core import blame_sight
        from ..core.commit_craft import run_git

        if not blame_sight.enabled_from_config(self.config):
            raise ValueError(
                "blame sight is off - turn it on with "
                "/blame on; nothing was blamed")
        code, out, err = run_git(
            self.project_root, "blame", "--porcelain", "--", path)
        if code != 0:
            raise ValueError(
                "git blame could not read " + str(path) + ": "
                + (err.strip() or "git blame failed"))
        lines = blame_sight.parse_blame_porcelain(out)
        if not lines:
            raise ValueError(
                f"git blame returned no lines for {path}; "
                "nothing was blamed")
        entries = self._blame_journal_entries(path)
        if line is not None:
            sight = blame_sight.explain_line(lines, line, entries)
            record: dict[str, Any] = sight.record()
            record["rendered"] = blame_sight.format_history_sight(sight)
            event = sight.record()
        else:
            record = {"type": "blame_sight", "path": path,
                      "line_no": None, "lines": len(lines)}
            record["rendered"] = blame_sight.format_blame(lines, path)
            event = {"type": "blame_sight", "path": path,
                     "lines": len(lines)}
        record["journaled"] = False
        if self._session_store and self.session_id:
            self._checkpoint(event)
            record["journaled"] = True
        return record


    # -- M-093: guarded mass edits --

    def mass_edit_guard_status(self) -> dict[str, Any]:
        """The mass-edit gate, in plain data (M-093).

        The setting exactly as stored (validated - a
        malformed stored value raises, never vanishes)
        and the plain explanation.
        """
        from ..core import mass_edit_guard

        return {
            "enabled": mass_edit_guard.enabled_from_config(self.config),
            "explanation": mass_edit_guard.PLAIN_EXPLANATION,
        }

    def set_mass_edit_guard(self, enabled: bool) -> dict[str, Any]:
        """Turn the mass edit guard on or off (M-093).

        Validated by :mod:`mythic_agent.core.mass_edit_guard`
        before anything mutates; journaled first as a
        ``mass_edit_guard_setting_changed`` event when a
        session is attached; a failed save restores the
        previous value exactly and journals a compensating
        ``mass_edit_guard_setting_reverted``.
        """
        import copy

        from ..core import mass_edit_guard

        new_value, change = mass_edit_guard.set_enabled(
            self.config, enabled)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[mass_edit_guard.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "mass_edit_guard_setting_reverted",
                        "reason": "The mass edit guard change could "
                                  "not be saved; the previous "
                                  "setting was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Mass edit guard change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def apply_mass_edit(self, edits: Any,
                        approval: Any = None) -> dict[str, Any]:
        """Apply a guarded mass edit (M-093).

        *edits* is a list of proposed new texts, each a
        ``(path, new_text)`` pair or a mapping with
        ``path`` and ``after``. Gate first: with the
        guard off this refuses and changes nothing. The
        dry-run report is built by the pure layer from
        the files' true current texts - never from a
        caller's claim - and when the report requires
        an approval, an approval covering the report's
        fingerprint is required BEFORE any byte moves:
        an unapproved mass apply refuses with every
        file untouched. An approved (or approval-free)
        plan lands through the EditJournal road, one
        journaled write per changed file; a file
        proposed unchanged is listed in the report and
        never written. The apply is recorded on the
        session as a ``mass_edit`` event carrying the
        report record and the approval fingerprint
        when a session is attached.
        """
        from ..core import mass_edit_guard
        from ..core.edits import EditJournal
        from ..core.workspace import resolve_file

        if not mass_edit_guard.enabled_from_config(self.config):
            raise ValueError(
                "mass edit guard is off - turn it on with "
                "/massedit on; nothing was changed")
        plan: list[dict[str, Any]] = []
        afters: dict[str, str] = {}
        for item in edits or []:
            if isinstance(item, dict):
                path = item.get("path")
                after = item.get("after")
            else:
                try:
                    path, after = item
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        "each mass edit is a (path, new text) "
                        "pair or a mapping with path and "
                        f"after; got {item!r}") from exc
            if not isinstance(after, str):
                raise ValueError(
                    f"{path}: the new text must be a string")
            target = resolve_file(
                self.project_root, str(path), write=True)
            before = (target.read_text(encoding="utf-8")
                      if target.exists() else "")
            cleaned = str(path).strip()
            if cleaned.startswith("./"):
                cleaned = cleaned[2:]
            plan.append({"path": path, "before": before,
                         "after": after})
            afters[cleaned] = after
        report = mass_edit_guard.build_report(plan)
        mass_edit_guard.require_approval(report, approval)
        fingerprint = None
        if isinstance(approval, mass_edit_guard.Approval):
            fingerprint = approval.fingerprint
        elif isinstance(approval, dict):
            fingerprint = approval.get("fingerprint")
        journal = EditJournal(self.project_root)
        applied: list[str] = []
        for entry in report.changed_files:
            journal.write(entry.path, afters[entry.path])
            applied.append(entry.path)
        record: dict[str, Any] = {
            "type": "mass_edit",
            "report": report.record(),
            "approval_fingerprint": fingerprint,
            "applied": applied,
            "rendered": mass_edit_guard.format_report(report),
            "journaled": False}
        if self._session_store and self.session_id:
            event = {"type": "mass_edit",
                     "report": report.record(),
                     "approval_fingerprint": fingerprint,
                     "applied": applied}
            self._checkpoint(event)
            record["journaled"] = True
        return record

    # -- M-095: permission profiles --

    def permission_profile_status(self) -> dict[str, Any]:
        """The session's posture, in plain data (M-095).

        The stored profile exactly as the pure layer
        resolves it (a malformed stored value raises,
        never vanishes), the ToolPolicy mode it rides
        as, the one status-line sentence, and the plain
        explanation.
        """
        from ..core import permission_profiles

        profile = permission_profiles.stored_profile(self.config)
        return {
            "profile": profile.to_record(),
            "policy_mode": permission_profiles.policy_mode_for(
                profile),
            "status_line":
                permission_profiles.format_permission_profile(
                    self.config),
            "explanation": permission_profiles.PLAIN_EXPLANATION,
        }

    def set_permission_profile(self, profile: Any) -> dict[str, Any]:
        """Change the session's posture (M-095).

        *profile* is a shipped posture's name, a
        validated Profile, or a custom posture mapping -
        resolved and validated by the pure layer before
        anything mutates, so an unknown name refuses
        with the config untouched. The change is
        journaled first as the pure layer's
        ``permission_profile_changed`` record when a
        session is attached; the live ToolPolicy is
        rebuilt in the new posture's mode, keeping the
        approval road it already had; a failed save
        restores the previous setting and the previous
        policy exactly and journals a compensating
        ``permission_profile_reverted``.
        """
        import copy

        from ..core import permission_profiles
        from ..core.policy import ToolPolicy

        if isinstance(profile, permission_profiles.Profile):
            target = profile
        elif isinstance(profile, dict):
            target = permission_profiles.validate_profile(profile)
        else:
            target = permission_profiles.profile_named(profile)
        previous_profile = permission_profiles.stored_profile(
            self.config)
        change = permission_profiles.profile_change_record(
            previous_profile, target)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change)
            journaled = True
        previous_config = copy.deepcopy(self.config)
        previous_policy = self.tool_policy
        if target.custom:
            self.config[permission_profiles.SETTING_KEY] = {
                "name": target.id,
                "title": target.title,
                "tools": target.tools,
                "paths": target.paths,
                "network": target.network,
                "commands": target.commands,
            }
        else:
            self.config[permission_profiles.SETTING_KEY] = target.id
        self.tool_policy = ToolPolicy(
            permission_profiles.policy_mode_for(target),
            previous_policy.approval)
        if not self.save_config():
            self.config = previous_config
            self.tool_policy = previous_policy
            if journaled:
                try:
                    self._checkpoint({
                        "type": "permission_profile_reverted",
                        "from": target.id,
                        "to": previous_profile.id,
                        "reason": "The permission profile change "
                                  "could not be saved; the "
                                  "previous posture was "
                                  "preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Permission profile change could not be saved; "
                "previous posture was preserved")
        return {**change, "session_id": self.session_id,
                "journaled": journaled}

    # -- M-096: remembered approvals --

    def remembered_approvals_status(self) -> dict[str, Any]:
        """The remembered approvals, in plain data (M-096).

        The validated stored list exactly as the pure
        layer resolves it (malformed stored data raises,
        never vanishes), its count, the one listing
        screen rendered from that same list, and the
        plain explanation.
        """
        from ..core import remembered_approvals

        approvals = remembered_approvals.stored_approvals(
            self.config)
        return {
            "approvals": [a.to_record() for a in approvals],
            "count": len(approvals),
            "screen":
                remembered_approvals.format_remembered_approvals(
                    approvals),
            "explanation": remembered_approvals.PLAIN_EXPLANATION,
        }

    def remember_command_approval(self, spec: Any,
                                  explicit: Any = False
                                  ) -> dict[str, Any]:
        """Remember one approval with an exact scope (M-096).

        *spec* is a scope mapping (command + args pattern
        + path) or a validated Scope, resolved by the pure
        layer before anything mutates. Nothing is
        remembered silently: the pure layer refuses
        unless *explicit* is exactly True - the recorded
        answer to a question the user was actually asked
        - and a duplicate scope refuses too. The change
        is journaled first as the pure layer's
        ``remembered`` change record when a session is
        attached; the stored list is the scopes' plain
        records under the setting key; a failed save
        restores the previous config exactly and journals
        a compensating ``remembered_approval_reverted``.
        """
        import copy

        from ..core import remembered_approvals

        current = remembered_approvals.stored_approvals(
            self.config)
        updated = remembered_approvals.remember_approval(
            current, spec, explicit=explicit)
        approval = updated[-1]
        change = remembered_approvals.approval_change_record(
            "remembered", approval, total=len(updated))
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change)
            journaled = True
        previous_config = copy.deepcopy(self.config)
        self.config[remembered_approvals.SETTING_KEY] = [
            a.scope.to_record() for a in updated]
        if not self.save_config():
            self.config = previous_config
            if journaled:
                try:
                    self._checkpoint({
                        "type": "remembered_approval_reverted",
                        "action": "remembered",
                        "id": approval.id,
                        "reason": "The remembered approval "
                                  "could not be saved; nothing "
                                  "was remembered.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Remembered approval could not be saved; "
                "nothing was remembered")
        return {**change, "session_id": self.session_id,
                "journaled": journaled}

    def revoke_remembered_approval(self, approval_id: Any
                                   ) -> dict[str, Any]:
        """Revoke one remembered approval by its id (M-096).

        The id is the one the listing shows (or a unique
        prefix of it), resolved by the pure layer before
        anything mutates - an unknown or ambiguous id
        refuses and removes nothing. Journal-first,
        stored as the remaining scopes' plain records,
        and a failed save restores the previous config
        exactly and journals a compensating
        ``remembered_approval_reverted``, exactly as
        remembering does.
        """
        import copy

        from ..core import remembered_approvals

        current = remembered_approvals.stored_approvals(
            self.config)
        updated = remembered_approvals.revoke_approval(
            current, approval_id)
        remaining = {a.id for a in updated}
        removed = next(a for a in current if a.id not in remaining)
        change = remembered_approvals.approval_change_record(
            "revoked", removed, total=len(updated))
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change)
            journaled = True
        previous_config = copy.deepcopy(self.config)
        self.config[remembered_approvals.SETTING_KEY] = [
            a.scope.to_record() for a in updated]
        if not self.save_config():
            self.config = previous_config
            if journaled:
                try:
                    self._checkpoint({
                        "type": "remembered_approval_reverted",
                        "action": "revoked",
                        "id": removed.id,
                        "reason": "The revocation could not be "
                                  "saved; the remembered "
                                  "approval was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Remembered approval revocation could not be "
                "saved; the approval was preserved")
        return {**change, "session_id": self.session_id,
                "journaled": journaled}

    def clear_remembered_approvals(self) -> dict[str, Any]:
        """Revoke every remembered approval at once (M-096).

        Journal-first as one ``remembered_approvals_cleared``
        record naming how many were cleared; a failed save
        restores the previous config exactly and journals
        a compensating ``remembered_approvals_clear_reverted``.
        Clearing an empty list changes nothing, journals
        nothing and saves nothing - it simply reports zero.
        """
        import copy

        from ..core import remembered_approvals

        current = remembered_approvals.stored_approvals(
            self.config)
        record: dict[str, Any] = {
            "type": "remembered_approvals_cleared",
            "cleared": len(current),
            "total": 0,
        }
        if not current:
            return {**record, "session_id": self.session_id,
                    "journaled": False}
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(record)
            journaled = True
        previous_config = copy.deepcopy(self.config)
        self.config[remembered_approvals.SETTING_KEY] = []
        if not self.save_config():
            self.config = previous_config
            if journaled:
                try:
                    self._checkpoint({
                        "type":
                            "remembered_approvals_clear_reverted",
                        "cleared": len(current),
                        "reason": "The clear could not be saved; "
                                  "the remembered approvals "
                                  "were preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Remembered approvals clear could not be "
                "saved; the approvals were preserved")
        return {**record, "session_id": self.session_id,
                "journaled": journaled}

    def remembered_approval_for(self, command: Any, args: Any,
                                path: Any):
        """The remembered approval covering a call, or None.

        The consultation the live approval road makes
        (M-096): the stored list is validated fresh (a
        malformed stored list raises, never silently
        allows or silently forgets), and the pure layer's
        exact match decides - command, args pattern and
        project path all exact, or no match.
        """
        from ..core import remembered_approvals

        approvals = remembered_approvals.stored_approvals(
            self.config)
        return remembered_approvals.find_match(
            approvals, command, list(args), path)

    def remembered_approval_allows_tool(self, name: str,
                                        arguments: Any) -> bool:
        """True when a tool call sits in a remembered scope.

        Only ``run_command`` carries a shell command a
        remembered scope can name: its command string is
        split the way a shell splits it, the first word
        is the command, the rest are the args, and the
        project is this agent's own project root. Every
        other tool, an unparseable command string, and an
        empty one answer False - the ordinary approval
        prompt decides those, exactly as before. A
        malformed stored list raises out of the stored
        validation; ToolPolicy.authorize catches that as
        a refusal, so a corrupt memory fails closed,
        never open.
        """
        import shlex

        if name != "run_command" or not isinstance(arguments, dict):
            return False
        command_text = arguments.get("command")
        if not isinstance(command_text, str):
            return False
        try:
            parts = shlex.split(command_text)
        except ValueError:
            return False
        if not parts:
            return False
        return self.remembered_approval_for(
            parts[0], parts[1:], str(self.project_root)) is not None

    # -- M-097: the OS sandbox --

    def os_sandbox_status(self) -> dict[str, Any]:
        """The OS sandbox gate and truth, in plain data (M-097).

        The gate exactly as stored (validated - a malformed
        stored value raises, never vanishes), the whole
        per-platform truth table as records, the one screen
        rendered from that same table, and the plain
        explanation.
        """
        from ..core import os_sandbox

        return {
            "enabled": os_sandbox.enabled_from_config(self.config),
            "truth": [entry.to_record()
                      for entry in os_sandbox.PLATFORM_TRUTH],
            "screen": os_sandbox.format_os_sandbox(self.config),
            "explanation": os_sandbox.PLAIN_EXPLANATION,
        }

    def set_os_sandbox(self, enabled: bool) -> dict[str, Any]:
        """Turn the OS sandbox gate on or off (M-097).

        Validated by :mod:`mythic_agent.core.os_sandbox`
        before anything mutates (a no-op change refuses);
        journaled first as the pure layer's
        ``os_sandbox_setting_changed`` event when a session
        is attached; the stored value is the plain bool
        under the setting key; a failed save restores the
        previous config exactly and journals a compensating
        ``os_sandbox_setting_reverted``.
        """
        import copy

        from ..core import os_sandbox

        new_value, change = os_sandbox.set_enabled(
            self.config, enabled)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[os_sandbox.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "os_sandbox_setting_reverted",
                        "reason": "The OS sandbox change could "
                                  "not be saved; the previous "
                                  "setting was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "OS sandbox change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def os_sandbox_plan(self, command: Any, *,
                        platform: Any = None,
                        network: Any = "deny",
                        require_confined: Any = False):
        """One command's confinement plan, purely (M-097).

        The pure layer's plan itself - mechanism, argv
        prefix, network stance, and whether it honestly
        confines - with nothing executed or changed.
        """
        from ..core import os_sandbox

        return os_sandbox.build_confinement_plan(
            command, platform=platform, network=network,
            require_confined=require_confined)

    def run_os_sandboxed(self, command: Any, *,
                         cwd: Any = None, network: Any = "deny",
                         require_confined: Any = False,
                         timeout: Any = None) -> dict[str, Any]:
        """Run *command* under its confinement plan (M-097).

        The run-under-plan road: the plan comes from the
        pure layer and the execution rides the elder
        :class:`mythic_agent.core.sandbox.Sandbox` runner,
        so its denylist, timeout and memory cap apply on
        every road. With the gate off, the command takes
        the elder road unchanged and the record says
        ``confined`` is False and why. With the gate on,
        a Linux plan executes through its argv prefix
        (``unshare`` namespaces; a fresh net namespace
        when the stance is deny) with the plan's env
        additions; the seccomp baseline is rendered to a
        filter-data file and named in the record, but no
        seccomp installation is claimed - ``setpriv``
        rejected a plain-name filter on this box
        (``invalid filter``, measured), so namespaces are
        the executed confinement and ``seccomp_installed``
        is honestly False. A plan that confines nothing
        (Windows today) runs the elder road with
        ``confined`` False, unless ``require_confined``
        was asked for, in which case the pure layer
        refuses before anything runs. Confinement is
        never claimed proven: the record carries the
        plan's own support level. The plan is journaled
        on the session when one is attached.
        """
        import shlex
        import tempfile

        from ..core import os_sandbox
        from ..core.sandbox import Sandbox

        if not isinstance(command, str) or not command.strip():
            raise ValueError(
                "a sandboxed command must be non-empty text")
        workdir = str(cwd) if cwd is not None else str(self.project_root)
        enabled = os_sandbox.enabled_from_config(self.config)
        if not enabled:
            result = Sandbox(
                no_network=(network == "deny")).run(
                    command, cwd=workdir, timeout=timeout)
            record: dict[str, Any] = {
                "type": "os_sandbox_run", "slice": "M-097",
                "command": command, "executed": command,
                "gate_enabled": False, "confined": False,
                "platform": os_sandbox.current_platform(),
                "support": None, "network": network,
                "plan": None, "seccomp_installed": False,
                "note": "the OS sandbox gate is off - the "
                        "command took the elder Sandbox "
                        "guardrail road unchanged",
                "returncode": result.returncode,
                "stdout": result.stdout, "stderr": result.stderr,
                "timed_out": result.timed_out, "ok": result.ok,
            }
            if self._session_store and self.session_id:
                self._checkpoint(record)
            return record
        plan = os_sandbox.build_confinement_plan(
            command, network=network,
            require_confined=require_confined)
        if not plan.confined:
            result = Sandbox(
                env=plan.env(),
                no_network=(network == "deny")).run(
                    command, cwd=workdir, timeout=timeout)
            record = {
                "type": "os_sandbox_run", "slice": "M-097",
                "command": command, "executed": command,
                "gate_enabled": True, "confined": False,
                "platform": plan.platform,
                "support": plan.support, "network": plan.network,
                "plan": plan.to_record(),
                "seccomp_installed": False,
                "note": "this platform's plan confines "
                        "nothing yet - the command took the "
                        "elder Sandbox guardrail road and "
                        "the record says so",
                "returncode": result.returncode,
                "stdout": result.stdout, "stderr": result.stderr,
                "timed_out": result.timed_out, "ok": result.ok,
            }
            if self._session_store and self.session_id:
                self._checkpoint(os_sandbox.confinement_plan_record(plan))
            return record
        seccomp_path = None
        if plan.platform == "linux":
            fd, seccomp_path = tempfile.mkstemp(
                prefix="mythic-seccomp-", suffix=".txt")
            with open(fd, "w", encoding="utf-8") as handle:
                handle.write(
                    "\n".join(os_sandbox.SECCOMP_BASELINE_SYSCALLS)
                    + "\n")
        executed = shlex.join(plan.argv())
        result = Sandbox(
            env=plan.env(),
            no_network=(network == "deny")).run(
                executed, cwd=workdir, timeout=timeout)
        record = {
            "type": "os_sandbox_run", "slice": "M-097",
            "command": command, "executed": executed,
            "gate_enabled": True, "confined": True,
            "platform": plan.platform, "support": plan.support,
            "network": plan.network, "plan": plan.to_record(),
            "seccomp_filter_file": seccomp_path,
            "seccomp_installed": False,
            "note": "executed under the plan's namespace "
                    "prefix; the seccomp baseline was "
                    "rendered as filter data only - no "
                    "seccomp installation and no proven "
                    "confinement is claimed",
            "returncode": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr,
            "timed_out": result.timed_out, "ok": result.ok,
        }
        if self._session_store and self.session_id:
            self._checkpoint(os_sandbox.confinement_plan_record(plan))
        return record

    # -- M-098: network gates --

    def network_gates_status(self) -> dict[str, Any]:
        """The network gates, in plain data (M-098).

        The gate exactly as stored (validated - a
        malformed stored value or allowlist entry raises,
        never vanishes), the allowlist entries as plain
        records, the one screen rendered from that same
        gate, and the plain explanation.
        """
        from ..core import network_gates

        gates = network_gates.gates_from_config(self.config)
        return {
            "enabled": network_gates.enabled_from_config(self.config),
            "entries": [e.to_record() for e in gates.entries],
            "screen": network_gates.format_network_gates(self.config),
            "explanation": network_gates.PLAIN_EXPLANATION,
        }

    def set_network_gates(self, enabled: bool) -> dict[str, Any]:
        """Turn the network gates on or off (M-098).

        Validated by :mod:`mythic_agent.core.network_gates`
        before anything mutates (a no-op change refuses);
        journaled first as the pure layer's
        ``network_gates_setting_changed`` event when a
        session is attached; the stored value is the plain
        bool under the setting key; a failed save restores
        the previous config exactly and journals a
        compensating ``network_gates_setting_reverted``.
        """
        import copy

        from ..core import network_gates

        new_value, change = network_gates.set_enabled(
            self.config, enabled)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[network_gates.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "network_gates_setting_reverted",
                        "reason": "The network gates change could "
                                  "not be saved; the previous "
                                  "setting was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Network gates change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def add_network_allowlist_entry(self, entry_spec: Any) -> dict[str, Any]:
        """Allow one tool to reach one domain (M-098).

        The entry is validated by the pure layer before
        anything mutates (a malformed entry refuses, and
        an entry already on the list refuses as a
        duplicate); journaled first as a
        ``network_allowlist_changed`` record when a session
        is attached; the stored list is the entries' plain
        records under the allowlist key; a failed save
        restores the previous config exactly and journals
        a compensating ``network_allowlist_reverted``.
        """
        import copy

        from ..core import network_gates

        entry = network_gates.validate_entry(entry_spec)
        gates = network_gates.gates_from_config(self.config)
        if entry in gates.entries:
            raise ValueError(
                f"the network allowlist already grants tool "
                f"{entry.tool!r} a reach to {entry.domain!r}")
        record = entry.to_record()
        change: dict[str, Any] = {
            "type": "network_allowlist_changed",
            "action": "allow",
            "entry": record,
        }
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change)
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[network_gates.ALLOWLIST_KEY] = [
            e.to_record() for e in gates.entries] + [record]
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "network_allowlist_reverted",
                        "action": "allow",
                        "entry": record,
                        "reason": "The network allowlist change "
                                  "could not be saved; the "
                                  "previous allowlist was "
                                  "preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Network allowlist change could not be saved; "
                "previous allowlist was preserved")
        return {**change, "session_id": self.session_id,
                "journaled": journaled}

    def check_network_reach(self, tool: Any, target: Any,
                            command: Any = None):
        """Decide one outbound reach (M-098).

        The pure layer's decision itself, computed always:
        a malformed tool raises, and a target whose host
        cannot be read is a denied decision, never an
        exception. With the gate on, a denied reach is
        news: its refusal record is published as a session
        event when a session is attached. With the gate
        off, the decision is returned unpublished - the
        gate is off, and the status screen says so plainly.
        """
        from ..core import network_gates

        gates = network_gates.gates_from_config(self.config)
        enabled = network_gates.enabled_from_config(self.config)
        decision = network_gates.check_network(
            tool, target, gates.entries)
        if enabled and not decision.allowed:
            record = network_gates.refusal_record(
                decision, command=command)
            if self._session_store and self.session_id:
                self._checkpoint(record)
        return decision

    # -- M-099: path jail --

    def path_jail_status(self) -> dict[str, Any]:
        """The path jail, in plain data (M-099).

        The gate exactly as stored (validated - a
        malformed stored value or grant raises, never
        vanishes), the grant roots as plain path
        strings, the session workspace resolved, the
        one screen rendered from that same jail, and
        the plain explanation.
        """
        from ..core import path_jail

        jail = path_jail.jail_from_config(self.config)
        workspace = path_jail.resolve_workspace_root(
            str(self.project_root))
        return {
            "enabled": path_jail.enabled_from_config(self.config),
            "grants": list(jail.grants),
            "workspace": workspace,
            "screen": path_jail.format_path_jail(
                self.config, workspace),
            "explanation": path_jail.PLAIN_EXPLANATION,
        }

    def set_path_jail(self, enabled: bool) -> dict[str, Any]:
        """Turn the path jail on or off (M-099).

        Validated by :mod:`mythic_agent.core.path_jail`
        before anything mutates (a no-op change refuses);
        journaled first as the pure layer's
        ``path_jail_setting_changed`` event when a
        session is attached; the stored value is the
        plain bool under the setting key; a failed save
        restores the previous config exactly and journals
        a compensating ``path_jail_setting_reverted``.
        """
        import copy

        from ..core import path_jail

        new_value, change = path_jail.set_enabled(
            self.config, enabled)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[path_jail.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "path_jail_setting_reverted",
                        "reason": "The path jail change could "
                                  "not be saved; the previous "
                                  "setting was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Path jail change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def add_path_grant(self, grant_spec: Any) -> dict[str, Any]:
        """Grant one named directory to the path jail (M-099).

        The grant is validated by the pure layer before
        anything mutates (a malformed grant refuses, and
        a grant already named refuses as a duplicate);
        journaled first as a ``path_grants_changed``
        record when a session is attached; the stored
        list is the grants' plain path strings under the
        grants key; a failed save restores the previous
        config exactly and journals a compensating
        ``path_grants_reverted``.
        """
        import copy

        from ..core import path_jail

        grant = path_jail.validate_grant(grant_spec)
        jail = path_jail.jail_from_config(self.config)
        if grant in jail.grants:
            raise ValueError(
                f"the path grants already name {grant!r}")
        change: dict[str, Any] = {
            "type": "path_grants_changed",
            "action": "grant",
            "grant": grant,
        }
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change)
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[path_jail.GRANTS_KEY] = list(jail.grants) + [grant]
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "path_grants_reverted",
                        "action": "grant",
                        "grant": grant,
                        "reason": "The path grant change "
                                  "could not be saved; the "
                                  "previous grants were "
                                  "preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Path grant change could not be saved; "
                "previous grants were preserved")
        return {**change, "session_id": self.session_id,
                "journaled": journaled}

    def check_path_jail(self, path: Any, workspace_root: Any = None):
        """Decide one file-tool path (M-099).

        The pure layer's decision itself, computed
        always, judged against this agent's project
        root unless *workspace_root* names another:
        the candidate is resolved (every symlink
        followed) before judging, and a malformed
        candidate is a denied decision, never an
        exception. With the gate on, a denied path is
        news: its refusal record is published as a
        session event when a session is attached.
        With the gate off, the decision is returned
        unpublished - the gate is off, and the status
        screen says so plainly. This is the judgement
        road the /pathjail check surface rides; the
        elder workspace road keeps its own write rules
        on the live file tools (see TEAM_LOG boundary).
        """
        from ..core import path_jail

        jail = path_jail.jail_from_config(self.config)
        enabled = path_jail.enabled_from_config(self.config)
        root = (workspace_root if workspace_root is not None
                else str(self.project_root))
        decision = jail.check(path, root)
        if enabled and not decision.allowed:
            record = path_jail.refusal_record(decision)
            if self._session_store and self.session_id:
                self._checkpoint(record)
        return decision



    # -- M-100: plan mode --

    def _held_plan(self):
        """The plan this agent currently holds, or None (M-100).

        The current plan lives in the agent layer alone -
        it is session state, not a stored setting - and it
        exists only as a pure-layer :class:`Plan`, built
        through ``validate_plan`` / ``build_plan`` and
        approved through ``approve``.
        """
        return getattr(self, "_current_plan", None)

    def current_plan(self):
        """The held plan itself, or None (M-100)."""
        return self._held_plan()

    def plan_mode_status(self) -> dict[str, Any]:
        """Plan mode, in plain data (M-100).

        The gate exactly as stored (validated - a
        malformed stored value raises, never vanishes),
        the held plan as its plain record (or None), the
        one screen rendered from that same gate and plan,
        whether the build gate is open, and the plain
        explanation.
        """
        from ..core import plan_mode

        plan = self._held_plan()
        enabled = plan_mode.enabled_from_config(self.config)
        return {
            "enabled": enabled,
            "plan": plan.to_record() if plan is not None else None,
            "screen": plan_mode.format_plan_mode(self.config, plan),
            "explanation": plan_mode.PLAIN_EXPLANATION,
            "can_build": plan_mode.can_build(enabled, plan),
        }

    def set_plan_mode(self, enabled: bool) -> dict[str, Any]:
        """Turn plan mode on or off (M-100).

        Validated by :mod:`mythic_agent.core.plan_mode`
        before anything mutates (a no-op change refuses);
        journaled first as the pure layer's
        ``plan_mode_setting_changed`` event when a session
        is attached; the stored value is the plain bool
        under the setting key; a failed save restores the
        previous config exactly and journals a compensating
        ``plan_mode_setting_reverted``.
        """
        import copy

        from ..core import plan_mode

        new_value, change = plan_mode.set_enabled(
            self.config, enabled)
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change.event())
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[plan_mode.SETTING_KEY] = new_value
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "plan_mode_setting_reverted",
                        "reason": "The plan mode change could "
                                  "not be saved; the previous "
                                  "setting was preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Plan mode change could not be saved; previous "
                "setting was preserved")
        return change.record(self.session_id, journaled)

    def set_current_plan(self, plan_spec: Any):
        """Hold one plan as the current plan (M-100).

        The plan is built through the pure layer's
        ``validate_plan`` - a mapping is validated whole
        (one malformed piece refuses the whole plan and
        nothing is held), a :class:`Plan` passes through
        as itself. A plan starts unapproved unless its
        own record says otherwise; approval is a separate
        act (see :meth:`approve_current_plan`). Returns
        the held plan itself.
        """
        from ..core import plan_mode

        plan = plan_mode.validate_plan(plan_spec)
        self._current_plan = plan
        return plan

    def build_current_plan(self, title: Any, intent: Any,
                           slices: Any):
        """Build and hold a plan from its pieces (M-100).

        The plan is built through the pure layer's
        ``build_plan`` (title, intent, and the ordered
        slice specs, each validated to Part IX form) and
        held as the current plan, unapproved. Returns the
        held plan itself.
        """
        from ..core import plan_mode

        plan = plan_mode.build_plan(title, intent, slices)
        self._current_plan = plan
        return plan

    def approve_current_plan(self):
        """Approve the held plan - the one gate opens (M-100).

        Approval goes through the pure layer's ``approve``:
        the held plan is replaced by its approved copy, so
        the approval belongs to this plan alone. With no
        plan held there is nothing to approve and the call
        refuses plainly. Returns the approved plan itself.
        """
        from ..core import plan_mode

        plan = self._held_plan()
        if plan is None:
            raise ValueError(
                "there is no plan to approve - set a plan first")
        approved = plan_mode.approve(plan)
        self._current_plan = approved
        return approved

    def check_plan_effect(self, effect: Any) -> str:
        """Decide one tool effect before it runs (M-100).

        The pure layer's decision itself - ``allow`` or
        ``deny`` - computed always: an unknown effect
        raises, never guessed at. With the gate on, a
        denied effect is news: its refusal record is
        published as a session event when a session is
        attached. With the gate off, the decision is
        computed but returned unpublished - the gate is
        off, and the status screen says so plainly.
        """
        from ..core import plan_mode

        enabled = plan_mode.enabled_from_config(self.config)
        decision = plan_mode.decide(enabled, effect)
        if enabled and decision == "deny":
            record = plan_mode.refusal_record(effect=effect)
            if self._session_store and self.session_id:
                self._checkpoint(record)
        return decision

    def check_plan_build(self) -> bool:
        """Whether building may begin (M-100).

        The pure layer's ``can_build`` answer, computed
        always against the held plan: out of plan posture
        building is the normal posture; in posture only an
        approved held plan opens the gate. With the gate
        on, a refused build is news: its refusal record is
        published as a session event when a session is
        attached. With the gate off, the answer is computed
        but returned unpublished.
        """
        from ..core import plan_mode

        enabled = plan_mode.enabled_from_config(self.config)
        plan = self._held_plan()
        allowed = plan_mode.can_build(enabled, plan)
        if enabled and not allowed:
            record = plan_mode.refusal_for_build(
                enabled, plan).to_record()
            if self._session_store and self.session_id:
                self._checkpoint(record)
        return allowed

    # -- M-101: hooks --

    def hooks_status(self) -> dict[str, Any]:
        """The configured hooks, in plain data (M-101).

        The hooks exactly as stored (validated whole -
        one malformed stored hook raises, never silently
        narrows what was configured), as their plain
        records, the one screen rendered from that same
        list, and the plain explanation. Hooks carry no
        gate of their own: the list itself is the setting.
        """
        from ..core import hooks

        configured = hooks.hooks_from_config(self.config)
        return {
            "hooks": [h.to_record() for h in configured],
            "screen": hooks.format_hooks(configured),
            "explanation": hooks.PLAIN_EXPLANATION,
        }

    def configured_hooks(self):
        """The configured hooks themselves (M-101)."""
        from ..core import hooks

        return hooks.hooks_from_config(self.config)

    def run_hooks(self, event: Any, stdin_text: str = "") -> list:
        """Run the hooks for one lifecycle event (M-101).

        The enabled hooks for *event* run in listed
        order, each through a real subprocess bounded by
        its own timeout, in this agent's workspace, with
        *stdin_text* as its standard input. Each finished
        run is judged by the pure layer alone. A verdict
        that blocks is news: its block record is published
        as a session event when a session is attached, so
        the reason the coder must answer can never be
        lost as a mere log line. An error after the act
        (post_tool, post_edit, on_session) blocks nothing
        in the pure layer's own judgement and so publishes
        nothing - it rides back in the returned verdicts.
        An unknown event and a malformed stored hook list
        both raise before anything runs. Returns the
        verdicts, in run order.
        """
        from ..core import hooks

        canonical = hooks.normalize_event(event)
        configured = hooks.hooks_from_config(self.config)
        selected = hooks.select_hooks(configured, canonical)
        verdicts = []
        for hook in selected:
            verdict = self._run_one_hook(hook, stdin_text=stdin_text)
            verdicts.append(verdict)
            # M-109: a hook run is a command by a hook - it
            # joins the audit trail with that actor.
            self._note_audit_hook(hook, verdict)
            record = hooks.block_record(verdict)
            if record is not None and self._session_store and self.session_id:
                self._checkpoint(record)
        return verdicts

    def _run_one_hook(self, hook: Any, stdin_text: str = ""):
        """Run one hook's command and judge it (M-101).

        The command runs through the shell it was written
        for, exactly as the elder sandbox road runs
        commands. A run that outlives its timeout is
        judged as an error with exit code 124 (the shell's
        own timeout verdict) and the timeout named in its
        reason; a command the OS cannot start at all is
        judged as an error with exit code 127. Neither is
        dressed up as an allow.
        """
        import subprocess

        from ..core import hooks

        try:
            completed = subprocess.run(
                hook.command, shell=True,
                cwd=str(self.project_root), input=stdin_text,
                capture_output=True, text=True,
                timeout=hook.timeout_seconds)
            return hooks.evaluate_result(
                hook.event, hook, completed.returncode,
                stdout=completed.stdout or "",
                stderr=completed.stderr or "")
        except subprocess.TimeoutExpired as exc:
            out = exc.stdout if isinstance(exc.stdout, str) else ""
            err = exc.stderr if isinstance(exc.stderr, str) else ""
            reason = ((err.strip() + " ") if err.strip() else "") + (
                f"the hook timed out after "
                f"{hook.timeout_seconds}s")
            return hooks.evaluate_result(
                hook.event, hook, 124, stdout=out, stderr=reason)
        except OSError as exc:
            return hooks.evaluate_result(
                hook.event, hook, 127, stdout="",
                stderr=f"the hook could not be run: {exc}")

    # -- M-102: hook packs --

    def hook_packs_status(self) -> dict[str, Any]:
        """The hook packs, in plain data (M-102).

        The shipped shelf as plain pack records, which
        of them are fully installed - every hook of the
        pack present among the configured hooks, judged
        by event and command exactly as the pure layer's
        install judges presence - the configured hooks
        as plain records, the one screen rendered from
        that same shelf, and the plain explanation. A
        malformed stored hook list raises, never silently
        narrows what was configured.
        """
        from ..core import hook_packs, hooks

        configured = hooks.hooks_from_config(self.config)
        present = {(h.event, h.command) for h in configured}
        installed = {
            pack.name: all(
                (hook.event, hook.command) in present
                for hook in pack.hooks)
            for pack in hook_packs.SHIPPED_PACKS}
        return {
            "packs": [p.to_record() for p in hook_packs.SHIPPED_PACKS],
            "installed": installed,
            "hooks": [h.to_record() for h in configured],
            "screen": hook_packs.format_hook_packs(),
            "explanation": hook_packs.PLAIN_EXPLANATION,
        }

    def install_hook_pack(self, pack_spec: Any) -> dict[str, Any]:
        """Install one hook pack into the hooks (M-102).

        The pack is resolved by the pure layer (a Pack,
        a shipped name read case-insensitively with
        dashes as underscores, or a pack mapping) and
        the merge is computed by the pure layer's
        ``install_pack`` before anything mutates: the
        existing hooks are validated whole, a pack hook
        whose name already names a different configured
        hook refuses, and a hook already present by
        event and command is skipped. A pack that is
        already fully installed changes nothing and
        writes nothing - no journal entry, no save - and
        the returned record says so (``changed`` False).
        Otherwise the install is journaled first as a
        ``hook_pack_installed`` record when a session is
        attached; the stored list is the merged hooks'
        plain records under the M-101 ``hooks`` setting;
        a failed save restores the previous config
        exactly and journals a compensating
        ``hook_pack_install_reverted``.
        """
        import copy

        from ..core import hook_packs, hooks

        pack = hook_packs.resolve_pack(pack_spec)
        existing = hooks.hooks_from_config(self.config)
        merged = hook_packs.install_pack(existing, pack)
        added = list(merged[len(existing):])
        if not added:
            return {
                "type": "hook_pack_installed",
                "action": "install",
                "pack": pack.name,
                "added": [],
                "changed": False,
                "session_id": self.session_id,
                "journaled": False,
            }
        change: dict[str, Any] = {
            "type": "hook_pack_installed",
            "action": "install",
            "pack": pack.name,
            "added": [h.to_record() for h in added],
        }
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change)
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[hooks.SETTING_KEY] = [
            h.to_record() for h in merged]
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "hook_pack_install_reverted",
                        "action": "install",
                        "pack": pack.name,
                        "reason": "The hook pack install could "
                                  "not be saved; the previous "
                                  "hooks were preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Hook pack install could not be saved; previous "
                "hooks were preserved")
        return {**change, "changed": True,
                "session_id": self.session_id,
                "journaled": journaled}

    # -- M-103: background tasks --

    def _background_jobs(self):
        """The held background-job registry (M-103).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds pure-layer Jobs in creation order.
        It is created on first use, so an agent whose
        ``__init__`` never ran still holds exactly one.
        """
        registry = getattr(self, "_background_registry", None)
        if registry is None:
            from ..core.background_tasks import BackgroundJobRegistry
            registry = BackgroundJobRegistry()
            self._background_registry = registry
        return registry

    def _background_lock_for(self):
        lock = getattr(self, "_background_lock", None)
        if lock is None:
            lock = threading.RLock()
            self._background_lock = lock
        return lock

    def background_jobs_status(self) -> dict[str, Any]:
        """Background jobs, in plain data (M-103).

        Every held job as its plain record, in creation
        order, the one screen rendered from that same
        registry, and the plain explanation.
        """
        from ..core import background_tasks

        registry = self._background_jobs()
        return {
            "jobs": [j.to_record() for j in registry.list_jobs()],
            "screen": background_tasks.format_background(registry),
            "explanation": background_tasks.PLAIN_EXPLANATION,
        }

    def get_background_job(self, job_id: Any):
        """The one held job an id names (M-103).

        An unknown id raises KeyError, exactly as the
        pure registry answers.
        """
        return self._background_jobs().get(job_id)

    def background_job_tail(self, job_id: Any = None,
                            count: int = 10) -> str:
        """One job's live tail, in plain words (M-103).

        With no id the newest held job is tailed; with
        no jobs held at all the call refuses plainly.
        An unknown id raises KeyError.
        """
        from ..core import background_tasks

        registry = self._background_jobs()
        if job_id is None:
            jobs = registry.list_jobs()
            if not jobs:
                raise ValueError(
                    "there are no background jobs to tail yet")
            job = jobs[-1]
        else:
            job = registry.get(job_id)
        return background_tasks.format_tail(job, count)

    def start_background_job(self, spec: Any) -> dict[str, Any]:
        """Start one background job for real (M-103).

        *spec* is a JobSpec, a spec mapping, a bare argv
        list, or a command string (split the way a shell
        splits it, then run with no shell at all). The
        job is created and moved to running in the held
        registry first; the command then runs as a real
        subprocess (``shell=False``, stderr folded into
        stdout) in the spec's cwd or this agent's
        workspace. A reader thread feeds each output
        line into the job's bounded tail as it arrives;
        when the process exits the reader judges it
        through the pure layer's ``finish_job`` and
        publishes the completion as session news. A
        command the OS cannot start at all is judged
        failed with exit code 127, the house error
        verdict. Returns the job's plain record as it
        stands when the call returns - a fast job may
        already be finished in it.
        """
        import shlex
        import subprocess

        from ..core import background_tasks

        if isinstance(spec, str):
            spec = shlex.split(spec)
        registry = self._background_jobs()
        lock = self._background_lock_for()
        with lock:
            job = registry.create(spec)
            job = registry.start(job.job_id)
        cwd = job.spec.cwd or str(self.project_root)
        try:
            proc = subprocess.Popen(
                list(job.spec.argv), shell=False, cwd=cwd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1)
        except OSError:
            with lock:
                finished = registry.finish(job.job_id, 127)
            self._publish_background_completion(finished)
            # M-109: a command the OS could not start was
            # still commanded - the trail names the attempt
            # and its honest ending.
            self._note_audit_background_job(job.job_id)
            return finished.to_record()
        processes = getattr(self, "_background_processes", None)
        if processes is None:
            processes = {}
            self._background_processes = processes
        with lock:
            processes[job.job_id] = proc
        reader = threading.Thread(
            target=self._background_reader,
            args=(job.job_id, proc), daemon=True,
            name=f"mythic-background-{job.job_id}")
        reader.start()
        self._keeper_note_background_activity(job.job_id)
        # M-109: the started command joins the audit trail
        # here, where the job visibly lives.
        self._note_audit_background_job(job.job_id)
        with lock:
            return registry.get(job.job_id).to_record()

    def _background_reader(self, job_id: str, proc: Any) -> None:
        """Feed one job's tail, then land its ending (M-103).

        Runs on the job's reader thread. Output lines
        land in the bounded tail while the job runs.
        At exit: a job whose kill was requested is
        cancelled through ``apply_kill``; any other job
        is judged by its exit code through the pure
        registry's finish. Either ending is published
        as session news exactly once.
        """
        registry = self._background_jobs()
        lock = self._background_lock_for()
        try:
            if proc.stdout is not None:
                for line in proc.stdout:
                    with lock:
                        try:
                            registry.append_output(job_id, line)
                        except (KeyError, ValueError):
                            pass  # the job already ended; drop the line
                    self._keeper_note_background_activity(job_id)
            exit_code = proc.wait()
        except Exception:
            exit_code = proc.poll()
            if not isinstance(exit_code, int):
                exit_code = 1
        landed = None
        with lock:
            try:
                current = registry.get(job_id)
            except KeyError:
                return
            processes = getattr(self, "_background_processes", {})
            processes.pop(job_id, None)
            if current.state == "running":
                if current.kill.requested:
                    landed = registry.apply_kill(job_id)
                else:
                    landed = registry.finish(job_id, exit_code)
            else:
                landed = current
        if landed is not None and landed.is_terminal:
            self._publish_background_completion(landed)

    def _publish_background_completion(self, job: Any) -> None:
        """Publish one finished job as session news (M-103).

        The pure layer's completion record - the
        ``background_job_completed`` session event -
        is journaled through the same checkpoint road
        every sibling slice uses, when a session is
        attached. Each job is announced at most once,
        however many roads land its ending.
        """
        from ..core import background_tasks

        self._keeper_note_background_activity(job.job_id)
        record = background_tasks.completion_record(job)
        if record is None:
            return
        lock = self._background_lock_for()
        announced = getattr(self, "_background_announced", None)
        if announced is None:
            announced = set()
            self._background_announced = announced
        with lock:
            if job.job_id in announced:
                return
            announced.add(job.job_id)
        if self._session_store and self.session_id:
            self._checkpoint(record)

    def kill_background_job(self, job_id: Any,
                            reason: str = "") -> dict[str, Any]:
        """Kill one background job for real (M-103).

        The kill is first a request, recorded on the
        job in the held registry with its reason - the
        job's state does not change yet. The real
        process is then terminated (``terminate()``,
        escalating to ``kill()`` if it ignores the
        request), and the recorded kill lands through
        the pure layer's ``apply_kill``: the job is
        cancelled, and its completion is published as
        session news. The reader thread may land the
        same ending first; the job is cancelled exactly
        once either way. A finished job refuses, as the
        pure layer refuses, and an unknown id raises
        KeyError. Returns the job's plain record.
        """
        import subprocess

        registry = self._background_jobs()
        lock = self._background_lock_for()
        with lock:
            registry.request_kill(job_id, reason)
            processes = getattr(self, "_background_processes", {})
            proc = processes.get(registry.get(job_id).job_id)
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
        landed = None
        with lock:
            current = registry.get(job_id)
            if current.kill.requested and current.state in (
                    "queued", "running"):
                landed = registry.apply_kill(current.job_id)
            else:
                landed = current
        if landed is not None and landed.is_terminal:
            self._publish_background_completion(landed)
        with lock:
            return registry.get(job_id).to_record()
    # -- M-104: the keeper --

    def _keeper_registry(self):
        """The held keeper watch registry (M-104).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds pure-layer watch targets in
        registration order. It is created on first
        use, so an agent whose ``__init__`` never ran
        still holds exactly one.
        """
        registry = getattr(self, "_keeper_watch_registry", None)
        if registry is None:
            from ..core.keeper import KeeperRegistry
            registry = KeeperRegistry()
            self._keeper_watch_registry = registry
        return registry

    def _keeper_job_links(self) -> dict:
        """Watch id -> the job currently doing its work (M-104).

        A keeper restart starts a replacement job
        under a fresh job id; the link records which
        job a watch's heartbeats now follow, so the
        restarted work keeps feeding its own watch.
        """
        links = getattr(self, "_keeper_links", None)
        if links is None:
            links = {}
            self._keeper_links = links
        return links

    def keeper_status(self, now: Any = None) -> dict[str, Any]:
        """Keeper watches, in plain data (M-104).

        Every held watch as its plain record, in
        registration order, every watch's verdict at
        ``now`` (the current moment when none is
        named), the one screen rendered from that
        same registry, and the plain explanation.
        Judging changes nothing: a status read never
        restarts, reports, or publishes.
        """
        from ..core import keeper

        moment = time.time() if now is None else now
        registry = self._keeper_registry()
        return {
            "targets": [t.to_record() for t in registry.list_targets()],
            "verdicts": [v.to_record() for v in registry.check(moment)],
            "screen": keeper.format_keeper(registry, moment),
            "explanation": keeper.PLAIN_EXPLANATION,
            "now": moment,
        }

    def get_keeper_target(self, target_id: Any):
        """The one held watch an id names (M-104).

        An unknown id raises KeyError, exactly as the
        pure registry answers.
        """
        return self._keeper_registry().get(target_id)

    def register_keeper_watch(self, spec: Any = None,
                              **kwargs: Any) -> dict[str, Any]:
        """Register one keeper watch for the session (M-104).

        *spec* is a WatchTarget, a target mapping, or
        field words given as keyword arguments - the
        pure layer's ``build_watch_target`` readings.
        A watch that names no last activity is stamped
        with the registration moment: a watch starts
        alive, and only quiet after that moment can
        ever judge it stalled. Returns the held
        target's plain record.
        """
        from dataclasses import replace

        from ..core import keeper

        target = keeper.build_watch_target(spec, **kwargs)
        if target.last_activity_at == 0.0:
            target = replace(target, last_activity_at=time.time())
        return self._keeper_registry().register(target).to_record()

    def keeper_heartbeat(self, target_id: Any,
                         at: Any = None) -> dict[str, Any]:
        """Record one sign of life on a held watch (M-104).

        The heartbeat lands at ``at`` or the current
        moment. Time never runs backwards - the pure
        layer refuses an earlier moment - and an
        unknown id raises KeyError. Returns the held
        target's plain record.
        """
        moment = time.time() if at is None else at
        updated = self._keeper_registry().heartbeat(target_id, moment)
        return updated.to_record()

    def _keeper_note_background_activity(self, job_id: str) -> None:
        """Feed one background job's life to its watch (M-104).

        Called where a held job visibly lives: when
        it starts, when an output line lands in its
        tail, and when its ending is published. A job
        feeds the watch registered under its own id,
        and a watch whose work the keeper restarted
        follows the replacement job through the link
        the restart recorded. No watch, no feeding -
        the note is silent when nothing watches the
        job.
        """
        registry = getattr(self, "_keeper_watch_registry", None)
        if registry is None:
            return
        links = getattr(self, "_keeper_links", {})
        for target in registry.list_targets(kind="background_job"):
            if links.get(target.target_id, target.target_id) != job_id:
                continue
            try:
                registry.heartbeat(target.target_id, time.time())
            except (KeyError, ValueError):
                pass  # a raced heartbeat never breaks the job's road

    def keeper_check(self, now: Any = None) -> dict[str, Any]:
        """Judge every held watch once, and act (M-104).

        Every watch is judged at ``now`` (the current
        moment when none is named) by the pure layer's
        mechanical reading. Where a verdict owes an
        action, its intervention record is published
        as a ``keeper_intervention`` session event -
        news, never just a log line, and at most once
        per watch per owed state. Where the owed
        action is a restart and the watched work has
        an in-world handle - a held background job -
        the restart is carried out for real (see
        :meth:`_carry_keeper_restart`) and spent on
        the watch through the pure layer's restart
        recording; a watch with no in-world handle is
        carried by its published intervention, which
        puts the owed restart before the session. A
        report is carried by its publication alone.
        Returns the verdicts, the intervention
        records, and the screen rendered after any
        restarts landed.
        """
        from ..core import keeper

        moment = time.time() if now is None else now
        registry = self._keeper_registry()
        verdicts = registry.check(moment)
        interventions: list[dict[str, Any]] = []
        for verdict in verdicts:
            if verdict.action == "none":
                continue
            target = registry.get(verdict.target_id)
            record = keeper.intervention_record(verdict, target)
            if record is None:
                continue
            interventions.append(record)
            self._publish_keeper_intervention(record)
            if verdict.action == "restart" \
                    and self._carry_keeper_restart(target):
                current = registry.get(target.target_id)
                try:
                    registry.restart(
                        target.target_id,
                        max(moment, current.last_activity_at))
                except ValueError:
                    pass  # the restart landed in the world; the
                    # watch's bound is the pure layer's to judge
        screen_now = max(
            [moment]
            + [t.last_activity_at for t in registry.list_targets()])
        return {
            "targets": [t.to_record() for t in registry.list_targets()],
            "verdicts": [v.to_record() for v in verdicts],
            "interventions": interventions,
            "screen": keeper.format_keeper(registry, screen_now),
            "explanation": keeper.PLAIN_EXPLANATION,
            "now": moment,
        }

    def _carry_keeper_restart(self, target: Any) -> bool:
        """Restart one stalled watch's work in the world (M-104).

        Only a background-job watch has an in-world
        handle here: the held job the watch names (or
        the replacement job a previous restart linked
        to it). A job still running is killed first -
        it has gone quiet past its bound, and the kill
        lands its cancellation as session news - then
        a fresh job is started from the same spec, and
        the watch is linked to the replacement so its
        heartbeats keep feeding the watch. A finished
        job is restarted the same way: a fresh run of
        the same spec. Returns True when a fresh job
        was started.
        """
        if target.kind != "background_job":
            return False
        registry = getattr(self, "_background_registry", None)
        if registry is None:
            return False
        links = self._keeper_job_links()
        job_id = links.get(target.target_id, target.target_id)
        try:
            job = registry.get(job_id)
        except KeyError:
            return False
        if job.state in ("queued", "running"):
            try:
                self.kill_background_job(job.job_id, "keeper restart")
            except (KeyError, ValueError):
                pass  # a job that ended on its own restarts below
        record = self.start_background_job({
            "argv": list(job.spec.argv),
            "cwd": job.spec.cwd,
            "label": job.spec.label,
        })
        links[target.target_id] = record["job_id"]
        return True

    def _publish_keeper_intervention(self, record: dict[str, Any]) -> None:
        """Publish one owed intervention as session news (M-104).

        The pure layer's intervention record - the
        ``keeper_intervention`` session event - is
        journaled through the same checkpoint road
        every sibling slice uses, when a session is
        attached. Each owed state is announced at
        most once: the announcement is keyed by the
        watch, the action owed, and the restarts
        already spent, so a later stall after a
        restart is new news while a repeated check of
        the same stall is not.
        """
        announced = getattr(self, "_keeper_announced", None)
        if announced is None:
            announced = set()
            self._keeper_announced = announced
        key = (record["target_id"], record["action"], record["restarts"])
        if key in announced:
            return
        announced.add(key)
        if self._session_store and self.session_id:
            self._checkpoint(record)

    # -- M-105: scheduled work --

    def _scheduled_registry(self):
        """The held scheduled-work registry (M-105).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds pure-layer scheduled jobs in
        registration order, with each held job's
        recorded run moments alongside it. It is
        created on first use, so an agent whose
        ``__init__`` never ran still holds exactly one.
        """
        registry = getattr(self, "_scheduled_work_registry", None)
        if registry is None:
            from ..core.scheduled_work import ScheduledWorkRegistry
            registry = ScheduledWorkRegistry()
            self._scheduled_work_registry = registry
        return registry

    def scheduled_work_status(self, now: Any = None) -> dict[str, Any]:
        """Scheduled work, in plain data (M-105).

        Every held job as its plain record, in
        registration order, every held job's recorded
        last run, every job's verdict at ``now``
        (the current moment when none is named),
        the one screen rendered from that same
        registry, and the plain explanation. Judging
        changes nothing: a status read never runs,
        records, or publishes.
        """
        from datetime import datetime

        from ..core import scheduled_work

        moment = datetime.now() if now is None else now
        registry = self._scheduled_registry()
        return {
            "jobs": [j.to_record() for j in registry.list_jobs()],
            "last_runs": {
                j.job_id: (
                    registry.last_run(j.job_id).isoformat()
                    if registry.last_run(j.job_id) is not None
                    else None)
                for j in registry.list_jobs()},
            "verdicts": [v.to_record() for v in registry.check(moment)],
            "screen": scheduled_work.format_scheduled_work(
                registry, moment),
            "explanation": scheduled_work.PLAIN_EXPLANATION,
            "now": moment,
        }

    def get_scheduled_job(self, job_id: Any):
        """The one held job an id names (M-105).

        An unknown id raises KeyError, exactly as the
        pure registry answers.
        """
        return self._scheduled_registry().get(job_id)

    def get_scheduled_verdict(self, job_id: Any, now: Any = None):
        """The one held job's verdict at a moment (M-105).

        The verdict is the registry's own judgement,
        against the job's recorded last run, so a
        recorded run moves it exactly as a check
        moves it. An unknown id raises KeyError.
        """
        from datetime import datetime

        moment = datetime.now() if now is None else now
        registry = self._scheduled_registry()
        job = registry.get(job_id)
        for verdict in registry.check(moment):
            if verdict.job_id == job.job_id:
                return verdict
        raise KeyError(f"unknown scheduled job: {job_id!r}")

    def register_scheduled_job(self, spec: Any = None,
                               **kwargs: Any) -> dict[str, Any]:
        """Register one scheduled job for the session (M-105).

        *spec* is a ScheduledJob, a job mapping, or
        field words given as keyword arguments - the
        pure layer's ``build_scheduled_job`` readings.
        The job is held as data only: registering
        runs nothing and starts no timer. Returns the
        held job's plain record.
        """
        from ..core import scheduled_work

        job = scheduled_work.build_scheduled_job(spec, **kwargs)
        return self._scheduled_registry().register(job).to_record()

    def record_scheduled_run(self, job_id: Any,
                             at: Any = None) -> dict[str, Any]:
        """Record one real run moment for a held job (M-105).

        The run lands at ``at`` or the current
        moment. Time never runs backwards - the pure
        registry refuses an earlier moment - and an
        unknown id raises KeyError. Returns the held
        job's plain record.
        """
        from datetime import datetime

        moment = datetime.now() if at is None else at
        updated = self._scheduled_registry().record_run(job_id, moment)
        return updated.to_record()

    def scheduled_check(self, now: Any = None) -> dict[str, Any]:
        """Judge every held job once, and act (M-105).

        Every job is judged at ``now`` (the current
        moment when none is named) by the pure
        layer's mechanical reading, against its own
        recorded last run. Where a verdict owes an
        action, its due record is published as a
        ``scheduled_job_due`` session event - news,
        never just a log line, and at most once per
        job per owed due moment. Where the owed
        action is a run, the job is carried out in
        the world as a real background job through
        the M-103 road (see
        :meth:`_carry_scheduled_run`) and the run is
        recorded on the registry at the judgement
        moment, so the same slot is never owed
        twice. A job that needs approval is
        published as waiting and never run, and no
        run is recorded for it. Returns the
        verdicts, the due records, the background
        jobs started, and the screen rendered after
        any runs landed.
        """
        from datetime import datetime

        from ..core import scheduled_work

        moment = datetime.now() if now is None else now
        registry = self._scheduled_registry()
        verdicts = registry.check(moment)
        records: list[dict[str, Any]] = []
        started: list[dict[str, Any]] = []
        for verdict in verdicts:
            if verdict.action == "none":
                continue
            job = registry.get(verdict.job_id)
            record = scheduled_work.due_record(verdict, job)
            if record is None:
                continue
            records.append(record)
            self._publish_scheduled_due(record)
            if verdict.action == "run":
                started.append(self._carry_scheduled_run(job, moment))
        return {
            "jobs": [j.to_record() for j in registry.list_jobs()],
            "verdicts": [v.to_record() for v in verdicts],
            "due_records": records,
            "started": started,
            "screen": scheduled_work.format_scheduled_work(
                registry, moment),
            "explanation": scheduled_work.PLAIN_EXPLANATION,
            "now": moment,
        }

    def _carry_scheduled_run(self, job: Any,
                             moment: Any) -> dict[str, Any]:
        """Carry one due job out in the world (M-105).

        The job's argv - a list of words, never a
        shell string - is started as a real
        background job through the M-103 road, in
        the job's cwd when it names one. The run is
        then recorded on the held registry at the
        judgement moment: the moment the check found
        owed is the moment the run answers. Returns
        the started background job's plain record.
        """
        record = self.start_background_job({
            "argv": list(job.argv),
            "cwd": job.cwd,
            "label": job.display_label,
        })
        registry = self._scheduled_registry()
        try:
            registry.record_run(job.job_id, moment)
        except ValueError:
            pass  # the run landed in the world; the
            # registry's clock is the pure layer's to judge
        return record

    def _publish_scheduled_due(self, record: dict[str, Any]) -> None:
        """Publish one owed due moment as session news (M-105).

        The pure layer's due record - the
        ``scheduled_job_due`` session event - is
        journaled through the same checkpoint road
        every sibling slice uses, when a session is
        attached. Each owed due moment is announced
        at most once: the announcement is keyed by
        the job, its due moment, and the action
        owed, so the next slot's due moment is new
        news while a repeated check of the same
        moment is not.
        """
        announced = getattr(self, "_scheduled_announced", None)
        if announced is None:
            announced = set()
            self._scheduled_announced = announced
        key = (record["job_id"], record["due_at"], record["action"])
        if key in announced:
            return
        announced.add(key)
        if self._session_store and self.session_id:
            self._checkpoint(record)

    # -- M-106: headless fleet mode --

    def _fleet_registry(self):
        """The held fleet registry (M-106).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds pure-layer fleet tasks in
        registration order, with each task's recorded
        verdict and artefact bundle alongside it. It
        is created on first use, so an agent whose
        ``__init__`` never ran still holds exactly one.
        """
        registry = getattr(self, "_fleet_mode_registry", None)
        if registry is None:
            from ..core.fleet_mode import FleetRegistry
            registry = FleetRegistry()
            self._fleet_mode_registry = registry
        return registry

    def fleet_status(self) -> dict[str, Any]:
        """The held fleet, in plain data (M-106).

        Every held task as its plain record, in
        registration order, every recorded verdict,
        every recorded artefact bundle, the fleet
        verdict judged mechanically from those
        verdicts, its honest exit code, the one screen
        rendered from that same registry, and the
        plain explanation. Reading changes nothing: a
        status read never runs, records, or publishes.
        """
        from ..core import fleet_mode

        registry = self._fleet_registry()
        verdict = registry.fleet_verdict()
        return {
            "tasks": [t.to_record() for t in registry.list_tasks()],
            "verdicts": [v.to_record() for v in registry.list_verdicts()],
            "bundles": [b.to_record() for b in registry.list_bundles()],
            "fleet_verdict": verdict.to_record(),
            "exit_code": verdict.exit_code,
            "verdict_screen": fleet_mode.format_fleet_verdict(registry),
            "screen": fleet_mode.format_fleet_mode(registry),
            "explanation": fleet_mode.PLAIN_EXPLANATION,
        }

    def get_fleet_task(self, task_id: Any):
        """The one held task an id names (M-106).

        An unknown id raises KeyError, exactly as the
        pure registry answers.
        """
        return self._fleet_registry().get(task_id)

    def get_fleet_verdict(self, task_id: Any):
        """One held task's recorded verdict, or None (M-106).

        The verdict is the one the fleet check
        recorded from the task's real run; a task that
        has not been run yet holds none. An unknown id
        raises KeyError.
        """
        return self._fleet_registry().get_verdict(task_id)

    def register_fleet_task(self, spec: Any = None,
                            **kwargs: Any) -> dict[str, Any]:
        """Register one fleet task for the session (M-106).

        *spec* is a FleetTask, a task mapping, or field
        words given as keyword arguments - the pure
        layer's ``build_fleet_task`` readings. The task
        is held as data only: registering runs nothing
        and starts no process. A task names what to run
        as an argv list - never a shell string - so a
        prompt with no argv refuses plainly at this
        boundary rather than being held as a run that
        could ever be reported passed. Returns the
        held task's plain record.
        """
        from ..core import fleet_mode

        task = fleet_mode.build_fleet_task(spec, **kwargs)
        return self._fleet_registry().register(task).to_record()

    def record_fleet_bundle(self, spec: Any = None,
                            **kwargs: Any) -> dict[str, Any]:
        """Record one held task's artefact bundle (M-106).

        The bundle names the task's artefacts, as data
        only - no file is read or written. A task the
        registry does not hold raises KeyError.
        Returns the held bundle's plain record.
        """
        registry = self._fleet_registry()
        return registry.record_bundle(spec, **kwargs).to_record()

    def fleet_resume_plan(self,
                          retry_failures: Any = False) -> dict[str, Any]:
        """What remains to run, in plain data (M-106).

        The plan is computed by the pure layer from the
        recorded verdicts alone: a passed task is never
        remaining; failed and error tasks remain only
        when ``retry_failures`` is exactly True and are
        otherwise held back and named. The resume news
        record rides along - the pure layer's
        ``fleet_resume`` record when something remains,
        else None. Asking changes nothing: a plan read
        never runs, records, or publishes.
        """
        from ..core import fleet_mode

        registry = self._fleet_registry()
        plan = registry.resume_plan(retry_failures)
        return {
            "plan": plan.to_record(),
            "remaining": list(plan.remaining_ids),
            "passed": list(plan.passed_ids),
            "held_back": list(plan.held_back_ids),
            "retry_failures": plan.retry_failures,
            "news_record": registry.resume_record(retry_failures),
            "screen": fleet_mode.format_resume_plan(plan),
            "explanation": fleet_mode.PLAIN_EXPLANATION,
        }

    def fleet_check(self, retry_failures: Any = False,
                    timeout: Any = None) -> dict[str, Any]:
        """Carry the held fleet out in the world (M-106).

        The pure layer's resume plan governs what runs:
        a passed task is never run again, and failed or
        error tasks run again only when
        ``retry_failures`` is exactly True. Every
        remaining task is started first - as a REAL
        background job through the M-103 road, its argv
        exec'd directly, never through a shell, in its
        repo when it names one - so the fleet runs in
        parallel; this call then waits for each job's
        real ending and judges the task from that ending
        alone (see :meth:`_judge_fleet_job`). A verdict
        is never invented: a completed job passes its
        task, a failed job fails it with the job's own
        exit code, and a cancelled job - or one still
        unfinished when a named ``timeout`` (in seconds)
        runs out - is an error, with the reason stated
        in words. Every verdict is recorded on the held
        registry, every task completion is published as
        a ``fleet_task_completed`` session event, and a
        fleet verdict this check changed is published
        as a ``fleet_verdict`` session event. Returns
        the verdicts recorded by this check, the
        background jobs started, the fleet verdict, its
        honest exit code, and the screen rendered after
        the runs landed.
        """
        from ..core import fleet_mode

        registry = self._fleet_registry()
        before = registry.fleet_verdict().to_record()
        plan = registry.resume_plan(retry_failures)
        started: list[dict[str, Any]] = []
        job_ids: dict[str, str] = {}
        for task_id in plan.remaining_ids:
            task = registry.get(task_id)
            record = self.start_background_job({
                "argv": list(task.argv),
                "cwd": task.cwd,
                "label": task.display_label,
            })
            started.append(record)
            job_ids[task_id] = record["job_id"]
        deadline = None
        if timeout is not None:
            import time
            deadline = time.monotonic() + float(timeout)
        verdicts: list[dict[str, Any]] = []
        for task_id in plan.remaining_ids:
            task = registry.get(task_id)
            job = self._wait_fleet_job(job_ids[task_id], deadline)
            verdict = self._judge_fleet_job(task, job)
            recorded = registry.record_verdict(verdict)
            verdicts.append(recorded.to_record())
            self._publish_fleet_completion(recorded, job_ids[task_id])
        after = registry.fleet_verdict()
        if after.to_record() != before:
            self._publish_fleet_verdict(after)
        return {
            "tasks": [t.to_record() for t in registry.list_tasks()],
            "verdicts": verdicts,
            "started": started,
            "fleet_verdict": after.to_record(),
            "exit_code": after.exit_code,
            "screen": fleet_mode.format_fleet_mode(registry),
            "explanation": fleet_mode.PLAIN_EXPLANATION,
        }

    def _wait_fleet_job(self, job_id: str, deadline: Any):
        """Wait for one background job's real ending (M-106).

        Polls the held M-103 registry until the job
        reaches a terminal state and returns the job;
        when a deadline is named and passes first,
        returns None - the caller judges that an error
        in words rather than inventing an outcome. With
        no deadline the wait is for the job's own
        ending, however long it takes.
        """
        import time

        while True:
            job = self.get_background_job(job_id)
            if job.is_terminal:
                return job
            if deadline is not None and time.monotonic() >= deadline:
                return None
            time.sleep(0.02)

    def _judge_fleet_job(self, task: Any, job: Any):
        """Judge one fleet task from its job's ending (M-106).

        The verdict is the background job's own outcome,
        read mechanically: completed is passed with the
        job's exit code (0, as the pure layer requires
        of a completed job), failed is failed with the
        job's own exit code, and cancelled - or no
        ending at all before the wait ran out - is an
        error, with the reason stated in the verdict's
        own words. Nothing here passes a task the world
        did not pass.
        """
        from ..core.fleet_mode import build_task_verdict

        if job is None:
            return build_task_verdict({
                "task_id": task.task_id, "status": "error",
                "detail": "the background job did not finish "
                          "before the fleet wait ran out; no "
                          "outcome was invented for it"})
        if job.state == "completed":
            return build_task_verdict({
                "task_id": task.task_id, "status": "passed",
                "exit_code": job.exit_code})
        if job.state == "failed":
            return build_task_verdict({
                "task_id": task.task_id, "status": "failed",
                "exit_code": job.exit_code,
                "detail": f"the command ended failed with "
                          f"exit code {job.exit_code}"})
        return build_task_verdict({
            "task_id": task.task_id, "status": "error",
            "exit_code": job.exit_code,
            "detail": f"the background job ended {job.state} "
                      "before the command finished"})

    def _publish_fleet_completion(self, verdict: Any,
                                  job_id: str) -> None:
        """Publish one task's completion as session news (M-106).

        The ``fleet_task_completed`` session event is
        journaled through the same checkpoint road every
        sibling slice uses, when a session is attached.
        Each run is announced at most once: the
        announcement is keyed by the background job that
        carried the task out, so a retried task's new run
        is new news while the same run's ending can never
        be announced twice.
        """
        from ..core import fleet_mode

        announced = getattr(self, "_fleet_announced", None)
        if announced is None:
            announced = set()
            self._fleet_announced = announced
        if job_id in announced:
            return
        announced.add(job_id)
        if self._session_store and self.session_id:
            task = self._fleet_registry().get(verdict.task_id)
            self._checkpoint({
                "type": "fleet_task_completed",
                "news": True,
                "surface": "session_event",
                "slice": fleet_mode.FLEET_MODE_SLICE,
                "task_id": verdict.task_id,
                "label": verdict.label,
                "status": verdict.status,
                "exit_code": verdict.exit_code,
                "headline": fleet_mode.format_fleet_task(task, verdict),
            })

    def _publish_fleet_verdict(self, verdict: Any) -> None:
        """Publish a changed fleet verdict as session news (M-106).

        The ``fleet_verdict`` session event - the pure
        layer's own verdict record, with its news words
        added - is journaled through the same checkpoint
        road every sibling slice uses, when a session is
        attached. It is published only by a check that
        changed the verdict, so an unchanged fleet is
        never announced again.
        """
        from ..core import fleet_mode

        if self._session_store and self.session_id:
            record = verdict.to_record()
            record["news"] = True
            record["surface"] = "session_event"
            record["headline"] = fleet_mode.format_fleet_verdict(verdict)
            self._checkpoint(record)

    # -- M-107: budgets as guardrails --

    def _budget_registry(self):
        """The held budget registry (M-107).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds pure-layer budgets in registration
        order, with each budget's latest recorded
        usage reading alongside it. It is created on
        first use, so an agent whose ``__init__`` never
        ran still holds exactly one; the moment it is
        created is also stamped, so the session's
        elapsed time can be read from a real clock
        (see :meth:`budget_live_usage`).
        """
        registry = getattr(self, "_budgets_registry", None)
        if registry is None:
            import time

            from ..core.budgets import BudgetRegistry
            registry = BudgetRegistry()
            self._budgets_registry = registry
            self._budgets_clock_started = time.time()
        return registry

    def budget_status(self) -> dict[str, Any]:
        """The held budgets, in plain data (M-107).

        Every held budget as its plain record, in
        registration order, every budget's recorded
        usage reading (or None where none is held),
        every verdict judged mechanically from the
        recorded readings, the one screen rendered
        from that same registry, and the plain
        explanation. Judging changes nothing: a
        status read never records, pauses, or
        publishes.
        """
        from ..core import budgets

        registry = self._budget_registry()
        usage: dict[str, Any] = {}
        for budget in registry.list_budgets():
            reading = registry.get_usage(budget.budget_id)
            usage[budget.budget_id] = (
                reading.to_record() if reading is not None else None)
        return {
            "budgets": [b.to_record() for b in registry.list_budgets()],
            "usage": usage,
            "verdicts": [v.to_record() for v in registry.list_verdicts()],
            "screen": budgets.format_budgets_screen(registry),
            "explanation": budgets.PLAIN_EXPLANATION,
        }

    def get_budget(self, budget_id: Any):
        """The one held budget an id names (M-107).

        An unknown id raises KeyError, exactly as the
        pure registry answers.
        """
        return self._budget_registry().get(budget_id)

    def get_budget_usage(self, budget_id: Any):
        """One held budget's recorded usage, or None (M-107).

        The reading is the one recorded on the
        registry - by :meth:`record_budget_usage` or
        :meth:`refresh_budget_usage`; a budget with
        no recorded reading holds none. An unknown
        id raises KeyError.
        """
        return self._budget_registry().get_usage(budget_id)

    def get_budget_verdict(self, budget_id: Any):
        """The one held budget's verdict, judged now (M-107).

        The verdict is the registry's own judgement
        against the budget's recorded reading, so a
        recorded reading moves it exactly as a check
        moves it. An unknown id raises KeyError.
        """
        return self._budget_registry().check(budget_id)

    def register_budget(self, spec: Any = None,
                        **kwargs: Any) -> dict[str, Any]:
        """Register one budget for the session (M-107).

        *spec* is a Budget, a budget mapping, or
        field words given as keyword arguments - the
        pure layer's ``build_budget`` readings. The
        budget is held as data only: registering
        spends nothing, records no usage, and pauses
        nothing. A budget names no default limits -
        a dimension it leaves unnamed is unlimited
        on that dimension. Returns the held budget's
        plain record.
        """
        from ..core import budgets

        budget = budgets.build_budget(spec, **kwargs)
        return self._budget_registry().register(budget).to_record()

    def record_budget_usage(self, budget_id: Any, spec: Any = None,
                            **kwargs: Any) -> dict[str, Any]:
        """Record one real usage reading for a held budget (M-107).

        *spec* is a BudgetUsage, a usage mapping, or
        usage field words - the pure layer's
        ``build_usage`` readings, in the costs road's
        vocabulary (tokens counted, cost in US
        dollars, elapsed time in seconds, commands
        counted). The reading replaces the budget's
        latest held reading; recording judges
        nothing and publishes nothing - the pause,
        when one is owed, is carried out by
        :meth:`budget_check` at its resting point.
        A budget the registry does not hold raises
        KeyError. Returns the recorded reading's
        plain record.
        """
        registry = self._budget_registry()
        return registry.record_usage(
            budget_id, spec, **kwargs).to_record()

    def budget_live_usage(self):
        """The session's real usage reading, from the real roads (M-107).

        Every number is read from a road that really
        counted it - nothing here is invented:
        tokens and cost come from the costs road
        (``core/costs.py``), as its workspace
        ledger's recorded token sums and its total
        cost in dollars (a model its pricing table
        does not know is billed unknown at zero
        there, so no price is invented here either);
        elapsed time is the real clock time since
        this session's budget guardrails were first
        held; commands are the held background jobs -
        the session's real command road (M-103) -
        counted as they are held. Reading changes
        nothing: no reading is recorded by asking.
        """
        import time

        from ..core.budgets import BudgetUsage
        from ..core.costs import CostTracker

        self._budget_registry()
        tracker = CostTracker(self.project_root)
        tokens = 0
        for aggregate in tracker.by_model().values():
            tokens += aggregate["input_tokens"] + aggregate["output_tokens"]
        commands = 0
        background = getattr(self, "_background_registry", None)
        if background is not None:
            commands = len(background.list_jobs())
        started = getattr(self, "_budgets_clock_started", time.time())
        return BudgetUsage(
            tokens_used=tokens,
            cost_used=tracker.total(),
            time_used_seconds=max(0.0, time.time() - started),
            commands_used=commands)

    def refresh_budget_usage(self, budget_id: Any) -> dict[str, Any]:
        """Feed one held budget the session's real usage (M-107).

        The live reading (see :meth:`budget_live_usage`)
        is recorded as the budget's latest reading,
        replacing any older one. A budget the
        registry does not hold raises KeyError.
        Returns the recorded reading's plain record.
        """
        registry = self._budget_registry()
        return registry.record_usage(
            budget_id, self.budget_live_usage()).to_record()

    def budget_check(self, budget_id: Any = None) -> dict[str, Any]:
        """Judge the held budgets once, and act (M-107).

        Every held budget - or the one budget an id
        names - is judged against its recorded
        reading by the pure layer's mechanical
        reading. Where a verdict is exceeded, the
        budget is carried out in the world as a
        graceful pause at this resting point: the
        pure layer's ``budget_paused`` record is
        published as a ``budget_paused`` session
        event - news, never just a log line, and at
        most once per budget per exceeded moment -
        and the budget is named among the paused in
        the return. A warning verdict rides along
        as its ``budget_report`` record, as data.
        Nothing is killed mid-edit and no in-flight
        work is interrupted: the pause lands here,
        between pieces of work, exactly as the pure
        layer's headline states it. An unknown id
        raises KeyError. Returns the verdicts, the
        pause records, the report records, the
        paused budget ids, and the screen rendered
        after the judgements landed.
        """
        from ..core import budgets

        registry = self._budget_registry()
        if budget_id is not None:
            verdicts = [registry.check(budget_id)]
        else:
            verdicts = list(registry.list_verdicts())
        paused: list[dict[str, Any]] = []
        reports: list[dict[str, Any]] = []
        for verdict in verdicts:
            record = budgets.budget_report_record(None, None, verdict)
            if record is None:
                continue
            if record["type"] == "budget_paused":
                paused.append(record)
                self._publish_budget_paused(record)
            else:
                reports.append(record)
        return {
            "budgets": [b.to_record() for b in registry.list_budgets()],
            "verdicts": [v.to_record() for v in verdicts],
            "paused": paused,
            "reports": reports,
            "paused_ids": [record["budget_id"] for record in paused],
            "screen": budgets.format_budgets_screen(registry),
            "explanation": budgets.PLAIN_EXPLANATION,
        }

    def _publish_budget_paused(self, record: dict[str, Any]) -> None:
        """Publish one reached budget as session news (M-107).

        The pure layer's paused record - the
        ``budget_paused`` session event - is
        journaled through the same checkpoint road
        every sibling slice uses, when a session is
        attached. Each exceeded moment is announced
        at most once: the announcement is keyed by
        the budget, the dimensions it exceeded, and
        the amounts it was read at, so a budget that
        spends further past its limit is a new
        exceeded moment and new news, while a
        repeated check of the same reading is not.
        """
        from ..core import budgets

        announced = getattr(self, "_budget_announced", None)
        if announced is None:
            announced = set()
            self._budget_announced = announced
        readings = record["readings"]
        key = (
            record["budget_id"],
            tuple(record["exceeded"]),
            tuple(
                (dimension, readings[dimension]["used"])
                for dimension in budgets.BUDGET_DIMENSIONS),
        )
        if key in announced:
            return
        announced.add(key)
        if self._session_store and self.session_id:
            self._checkpoint(record)

    # -- M-108: the kill switch everywhere --

    def _kill_switch_registry(self):
        """The held kill-switch registry (M-108).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds pure-layer halts in the order
        pulled, with the verdict each pull earned
        alongside it. It is created on first use, so
        an agent whose ``__init__`` never ran still
        holds exactly one.
        """
        registry = getattr(self, "_kill_switch_halts_registry", None)
        if registry is None:
            from ..core.kill_switch import HaltRegistry
            registry = HaltRegistry()
            self._kill_switch_halts_registry = registry
        return registry

    def kill_switch_status(self) -> dict[str, Any]:
        """The pulled halts, in plain data (M-108).

        Every held halt as its plain record, in the
        order pulled, every judged verdict held
        alongside its halt, the one screen rendered
        from that same registry, and the plain
        explanation. Reading changes nothing: a
        status read registers, judges, halts, or
        publishes nothing.
        """
        from ..core import kill_switch

        registry = self._kill_switch_registry()
        return {
            "halts": [h.to_record() for h in registry.list_halts()],
            "verdicts": [v.to_record() for v in registry.list_verdicts()],
            "screen": kill_switch.format_halts_screen(registry),
            "explanation": kill_switch.PLAIN_EXPLANATION,
        }

    def get_halt(self, halt_id: Any):
        """The one held halt an id names (M-108).

        An unknown id raises KeyError, exactly as the
        pure registry answers.
        """
        return self._kill_switch_registry().get(halt_id)

    def get_halt_verdict(self, halt_id: Any):
        """One held halt's judged verdict, or None (M-108).

        The verdict is the historical reading judged
        at the halt's pull, against that moment's
        holdings - it is never re-judged from later
        holdings. A halt that has not been pulled
        through :meth:`pull_kill_switch` holds no
        verdict. An unknown id raises KeyError.
        """
        return self._kill_switch_registry().get_verdict(halt_id)

    def _kill_switch_holdings(self):
        """The session's real holdings, from the real roads (M-108).

        Every reading comes from a road that really
        holds it - nothing here is invented:

        * the coder is active when its turn lock is
          held - a turn in flight holds it;
        * background jobs are the held M-103 jobs,
          each with its real lifecycle state;
        * crew tasks are the held M-106 tasks: a task
          with a finished verdict is finished, a task
          backed by a live background job (the road a
          fleet check runs a task through, the job
          carrying the task's display label) is
          running, and any other task is merely
          queued - a plan, not running work;
        * pending approvals are read from the
          approval road itself: approvals are asked
          one at a time under the tools layer's
          approval lock, so a pending approval exists
          exactly while that lock is held, and there
          is never more than one.

        Reading changes nothing.
        """
        from ..core.kill_switch import build_holdings

        turn_lock = getattr(self, "_turn_lock", None)
        coder_active = bool(
            turn_lock is not None and turn_lock.locked())
        jobs: list = []
        background = getattr(self, "_background_registry", None)
        if background is not None:
            jobs = [
                (job.job_id, job.state)
                for job in background.list_jobs()]
        crew: list = []
        fleet = getattr(self, "_fleet_mode_registry", None)
        if fleet is not None:
            active_labels = set()
            if background is not None:
                for job in background.list_jobs():
                    if job.state in ("queued", "running"):
                        active_labels.add(job.label)
            for task in fleet.list_tasks():
                verdict = fleet.get_verdict(task.task_id)
                status = verdict.status if verdict is not None else None
                if status in ("passed", "failed", "error", "skipped"):
                    crew.append((task.task_id, status))
                elif task.display_label in active_labels:
                    crew.append((task.task_id, "running"))
                else:
                    crew.append((task.task_id, "queued"))
        pending = 0
        try:
            from . import tools as _agent_tools

            if _agent_tools._approval_lock.locked():
                pending = 1
        except Exception:
            pending = 0
        return build_holdings({
            "coder_active": coder_active,
            "background_jobs": jobs,
            "crew_tasks": crew,
            "pending_approvals": pending})

    def pull_kill_switch(self, spec: Any = None,
                         **kwargs: Any) -> dict[str, Any]:
        """Pull the kill switch, and carry the halt out (M-108).

        *spec* is a Halt, a halt mapping, or field
        words - the pure layer's ``build_halt``
        readings; with nothing named, the halt names
        all four targets. The halt is registered,
        the session's holdings are read from the real
        roads (see :meth:`_kill_switch_holdings`),
        and the pure layer judges the pull against
        that moment's holdings. The halt is then
        carried out in the world through the real
        roads, for the targets named:

        * background jobs - every held job the
          holdings showed live is killed through the
          M-103 road (:meth:`kill_background_job`:
          the kill is recorded as a request, the real
          process is terminated, the kill is applied
          and the job's completion is published);
        * the crew - a running crew task is carried
          by a background job, so its job is killed
          through that same road; a crew with no live
          backing job has nothing running to kill,
          and the verdict says so (nothing held, or
          already stopped) rather than claiming a
          halt that never happened;
        * the coder and pending approvals - the
          coder's own cancellation event is set
          (:meth:`cancel`): in-flight work stops at
          the next runtime boundary, and a pending
          approval, which waits on that same event,
          is refused - it raises its cancellation and
          is never answered as approved. There is no
          separate approval road to fake: refusing an
          approval rides the coder's cancellation
          event because that is the road approvals
          are bound to.

        The pure layer's ``kill_switch_pulled`` record
        is published as session news through the
        checkpoint road, and the return names the
        jobs actually killed and any kill that
        refused, in words. Returns the halt, its
        verdict, the news record, the killed job ids,
        the kill refusals, whether the cancellation
        event was set, the screen rendered after the
        pull landed, and the plain explanation.
        """
        from ..core import kill_switch

        halt = kill_switch.build_halt(spec, **kwargs)
        registry = self._kill_switch_registry()
        held = registry.register(halt)
        holdings = self._kill_switch_holdings()
        verdict = registry.judge(held.halt_id, holdings)
        record = registry.record(held.halt_id)
        targets = set(held.targets)
        killed: list[str] = []
        kill_errors: list[str] = []
        if targets & {"background_jobs", "crew"}:
            background = getattr(self, "_background_registry", None)
            if background is not None:
                if "background_jobs" in targets:
                    wanted = list(holdings.background_active_ids)
                else:
                    running = set(holdings.crew_running_ids)
                    labels = set()
                    fleet = getattr(self, "_fleet_mode_registry", None)
                    if fleet is not None:
                        for task in fleet.list_tasks():
                            if task.task_id in running:
                                labels.add(task.display_label)
                    wanted = [
                        job.job_id for job in background.list_jobs()
                        if job.state in ("queued", "running")
                        and job.label in labels]
                for job_id in wanted:
                    try:
                        self.kill_background_job(
                            job_id, held.reason or "kill switch pulled")
                        killed.append(job_id)
                    except Exception as exc:
                        kill_errors.append(f"{job_id}: {exc}")
        cancel_set = False
        if targets & {"coder", "approvals"}:
            self.cancel()
            cancel_set = True
        self._publish_kill_switch_pulled(record)
        return {
            "halt": held.to_record(),
            "verdict": verdict.to_record(),
            "record": record,
            "killed_job_ids": killed,
            "kill_errors": kill_errors,
            "cancel_set": cancel_set,
            "screen": kill_switch.format_halts_screen(registry),
            "explanation": kill_switch.PLAIN_EXPLANATION,
        }

    def _publish_kill_switch_pulled(self, record: dict[str, Any]) -> None:
        """Publish one pulled switch as session news (M-108).

        The pure layer's ``kill_switch_pulled`` record
        is journaled through the same checkpoint road
        every sibling slice uses, when a session is
        attached. Each pull is announced at most
        once: the announcement is keyed by the halt
        id, and every pull holds a fresh id.
        """
        announced = getattr(self, "_kill_switch_announced", None)
        if announced is None:
            announced = set()
            self._kill_switch_announced = announced
        if record["halt_id"] in announced:
            return
        announced.add(record["halt_id"])
        if self._session_store and self.session_id:
            self._checkpoint(record)

    # -- M-109: the audit trail --

    def _audit_registry(self):
        """The held audit registry (M-109).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds pure-layer audit entries in append
        order. It is created on first use, so an agent
        whose ``__init__`` never ran still holds
        exactly one.
        """
        registry = getattr(self, "_audit_trail_registry", None)
        if registry is None:
            from ..core.audit_trail import AuditRegistry
            registry = AuditRegistry()
            self._audit_trail_registry = registry
        return registry

    def audit_status(self) -> dict[str, Any]:
        """The audit trail, in plain data (M-109).

        Every held entry as its plain record, in
        append order, the whole-trail export rendered
        from that same registry, the one screen, and
        the plain explanation. Reading changes
        nothing: a status read appends nothing and
        publishes nothing.
        """
        from ..core import audit_trail

        registry = self._audit_registry()
        return {
            "entries": [e.to_record() for e in registry.list_entries()],
            "export": registry.export(),
            "screen": audit_trail.format_audit_screen(registry),
            "explanation": audit_trail.PLAIN_EXPLANATION,
        }

    def get_audit_entry(self, entry_id: Any):
        """The one held entry an id names (M-109).

        An unknown id raises KeyError, exactly as the
        pure registry answers.
        """
        return self._audit_registry().get(entry_id)

    def audit_export(self) -> dict[str, Any]:
        """The whole trail, exported for review (M-109).

        The export as plain data - every held entry,
        in append order, with the counts by kind and
        by actor - and as the pure layer's text
        export, both from that same registry.
        Exporting changes nothing and publishes
        nothing: asking reads the trail out, it does
        not carry it anywhere.
        """
        from ..core import audit_trail

        registry = self._audit_registry()
        return {
            "export": registry.export(),
            "text": audit_trail.format_export(registry),
            "screen": audit_trail.format_audit_screen(registry),
            "explanation": audit_trail.PLAIN_EXPLANATION,
        }

    def record_audit_entry(self, spec: Any = None,
                           **kwargs: Any) -> dict[str, Any]:
        """Record one entry on the session's trail (M-109).

        *spec* is an AuditEntry, an entry mapping, or
        entry field words - the pure layer's
        ``build_entry`` readings. The entry is
        appended to the held trail (append-only: an
        id the trail already holds refuses, exactly
        as the pure registry refuses) and its
        ``audit_recorded`` record is published as
        session news through the checkpoint road.
        This is the explicit road: it records exactly
        the act its caller names, so callers name
        real acts only - the session's own acts are
        fed by the feeding roads below, as they
        happen. Returns the held entry, its news
        record, the screen rendered after the entry
        landed, and the plain explanation.
        """
        from ..core import audit_trail

        entry = audit_trail.build_entry(spec, **kwargs)
        registry = self._audit_registry()
        held = registry.append(entry)
        record = registry.record(held.entry_id)
        self._publish_audit_record(record)
        return {
            "entry": held.to_record(),
            "record": record,
            "screen": audit_trail.format_audit_screen(registry),
            "explanation": audit_trail.PLAIN_EXPLANATION,
        }

    def _record_audit_note(self, kind: str, actor: str,
                           summary: str, target: str = "",
                           detail: str = "") -> None:
        """Feed one real act to the trail (M-109).

        The feeding roads call this as an act happens.
        Recording never breaks the road it rides on:
        a note that cannot be recorded is dropped, and
        the act itself - which already happened, or
        was already refused - stays the truth owed.
        The explicit road (:meth:`record_audit_entry`)
        refuses loudly instead; only these
        as-it-happens notes are silent.
        """
        try:
            registry = self._audit_registry()
            held = registry.append({
                "kind": kind, "actor": actor,
                "summary": summary, "target": target,
                "detail": detail})
            self._publish_audit_record(registry.record(held.entry_id))
        except Exception:
            pass  # the act is the truth owed, not the note

    def _note_audit_tool_call(self, name: str,
                              arguments: dict[str, Any],
                              outcome: str) -> None:
        """Trail one executed tool call (M-109).

        Called once per call from
        :meth:`_execute_call`, the funnel every tool
        call in a session travels. The kind is the
        tool's own: ``run_command`` is a command,
        ``write_file`` and ``replace_file_content``
        are edits, every other tool is a tool call.
        The actor is the coder - or the crew, when
        this agent is a named subagent rather than
        the Primary: a spawned agent's acts are crew
        acts, and its trail says so. The target names
        what the act touched - the command line, the
        file, or the tool - and the detail is the
        outcome word alone; a tool result's text is
        never trailed, because a result may be a
        whole file's contents. Programmatic
        ``apply_*`` edit calls under the funnel are
        the machinery an edit travels, not separate
        session acts, and are not trailed separately -
        the tool call that drove them is.
        """
        actor = "coder" if self.name == "Primary" else "crew"
        if name == "run_command":
            command = arguments.get("command")
            target = (command.strip()[:200]
                      if isinstance(command, str) else "")
            summary = (f"ran command {target}" if target
                       else "ran a command with run_command")
            self._record_audit_note(
                "command", actor, summary, target=target,
                detail=outcome)
        elif name in ("write_file", "replace_file_content"):
            path = arguments.get("path")
            target = (path.strip()[:200]
                      if isinstance(path, str) else "")
            summary = (f"edited {target} with {name}" if target
                       else f"edited a file with {name}")
            self._record_audit_note(
                "edit", actor, summary, target=target,
                detail=outcome)
        else:
            self._record_audit_note(
                "tool_call", actor, f"ran tool {name}",
                target=name, detail=outcome)

    def _note_audit_approval(self, name: str, approved: bool,
                             via: str) -> None:
        """Trail one human approval decision (M-109).

        Called from the approval callbacks the tree
        actually builds - the TUI road in
        :meth:`bind_tui` and the terminal road in
        ``terminal.configured_agent`` - at the moment
        the human's answer lands: a remembered
        approval answering, or the prompt answered
        granted or refused. The actor is the human.
        A decision never reached (a prompt cancelled
        before any answer) is not an approval and is
        never trailed as one.
        """
        word = "approved" if approved else "refused"
        self._record_audit_note(
            "approval", "human", f"{word} tool {name}",
            target=name, detail=f"{word} via {via}")

    def _note_audit_background_job(self, job_id: str) -> None:
        """Trail one started background command (M-109).

        Called from :meth:`start_background_job` where
        the job visibly lives - started, or refused
        by the OS before it could start (its honest
        127 ending, held as a failed job). The actor
        is the crew when the job carries a held fleet
        task's display label - the reading M-108's
        holdings use to tell running crew work - and
        the coder otherwise: a fleet command is crew
        work, and the trail says which it was rather
        than guessing.
        """
        try:
            job = self._background_jobs().get(job_id)
        except Exception:
            return
        actor = "coder"
        fleet = getattr(self, "_fleet_mode_registry", None)
        if fleet is not None:
            try:
                labels = {t.display_label
                          for t in fleet.list_tasks()}
            except Exception:
                labels = set()
            if job.label in labels:
                actor = "crew"
        self._record_audit_note(
            "command", actor,
            f"started background command {job.label}",
            target=job.spec.command_text[:200],
            detail=f"background job {job.job_id} ({job.state})")

    def _note_audit_hook(self, hook: Any, verdict: Any) -> None:
        """Trail one hook run (M-109).

        Called from :meth:`run_hooks` as each hook's
        run is judged: a hook run is a command, and
        its actor is the hook. Hooks fire only
        through ``run_hooks`` in this tree - there is
        no other hook firing road - so no hook act is
        trailed from anywhere else.
        """
        self._record_audit_note(
            "command", "hook",
            f"ran hook {verdict.hook} for {verdict.event}",
            target=str(hook.command)[:200],
            detail=(f"decision {verdict.decision}, "
                    f"exit {verdict.exit_code}"))

    def _publish_audit_record(self, record: dict[str, Any]) -> None:
        """Publish one recorded entry as session news (M-109).

        The pure layer's ``audit_recorded`` record is
        journaled through the same checkpoint road
        every sibling slice uses, when a session is
        attached. Each entry is announced at most
        once: the announcement is keyed by the entry
        id, and every appended entry holds a fresh id.
        """
        announced = getattr(self, "_audit_announced", None)
        if announced is None:
            announced = set()
            self._audit_announced = announced
        if record["entry_id"] in announced:
            return
        announced.add(record["entry_id"])
        if self._session_store and self.session_id:
            self._checkpoint(record)


    # -- M-110: secret hygiene in action --

    def _hygiene_registry(self):
        """The held secret-hygiene registry (M-110).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds pure-layer file screenings in the
        order judged. It is created on first use, so
        an agent whose ``__init__`` never ran still
        holds exactly one.
        """
        registry = getattr(self, "_secret_hygiene_registry", None)
        if registry is None:
            from ..core.secret_hygiene import HygieneRegistry
            registry = HygieneRegistry()
            self._secret_hygiene_registry = registry
        return registry

    def secret_hygiene_status(self) -> dict[str, Any]:
        """Secret hygiene, in plain data (M-110).

        Every held screening as its plain record, in
        the order judged, the one screen rendered
        from that same registry, and the plain
        explanation. Reading changes nothing: a
        status read screens, registers, or publishes
        nothing.
        """
        from ..core import secret_hygiene

        registry = self._hygiene_registry()
        return {
            "screenings": [s.to_record() for s in registry.list_screenings()],
            "screen": secret_hygiene.format_secrets_screen(registry),
            "explanation": secret_hygiene.PLAIN_EXPLANATION,
        }

    def get_screening(self, screening_id: Any):
        """The one held screening an id names (M-110).

        An unknown id raises KeyError, exactly as the
        pure registry answers.
        """
        return self._hygiene_registry().get(screening_id)

    def screen_file(self, filename: Any, text: Any = "") -> dict[str, Any]:
        """Screen one file for commit, and hold the verdict (M-110).

        The file's name and text are judged by the
        pure layer and the verdict is held for the
        session. A refused verdict is published as a
        ``secret_refusal`` session event through the
        checkpoint road - a refusal is always news,
        never lost as a log line. The screened text is
        read only to locate secret shapes in it: the
        held verdict names the file and the pattern
        kinds only, and the content is never stored,
        logged or shown. Returns the held screening,
        its refusal record (None when clean), the
        screen rendered after the verdict landed, and
        the plain explanation.
        """
        from ..core import secret_hygiene

        registry = self._hygiene_registry()
        held = registry.screen(filename, text)
        record = registry.record(held.screening_id)
        self._publish_secret_refusal(record)
        return {
            "screening": held.to_record(),
            "record": record,
            "screen": secret_hygiene.format_secrets_screen(registry),
            "explanation": secret_hygiene.PLAIN_EXPLANATION,
        }

    def screen_project_file(self, filename: Any) -> dict[str, Any]:
        """Screen one real file in the project (M-110).

        The named file is read from the project root
        and screened through :meth:`screen_file`. A
        name that escapes the project, or a file the
        project does not hold, refuses plainly and
        screens nothing - a file that cannot be read
        cannot honestly be screened for content.
        """
        from pathlib import Path

        name = str(filename).strip()
        root = Path(self.project_root).resolve()
        candidate = (root / name).resolve()
        if candidate != root and root not in candidate.parents:
            raise ValueError(
                f"secret hygiene can only screen files inside "
                f"the project, got {filename!r}")
        if not candidate.is_file():
            raise ValueError(
                f"no such file in the project to screen: {name}")
        body = candidate.read_bytes().decode("utf-8", errors="replace")
        return self.screen_file(name, body)

    def redact_output(self, text: Any) -> str:
        """One output text, hygiene-redacted (M-110).

        The pure layer's redaction: every secret-shaped
        span replaced with the one fixed marker, so the
        returned text can never echo a secret the shapes
        know. Ordinary text is returned untouched.
        """
        from ..core.secret_hygiene import redact_secrets

        return redact_secrets(text)

    def _hygiene_redact(self, text: str) -> str:
        """Feed one real output through the hygiene redaction (M-110).

        The feeding roads call this as an output is
        produced. It composes with the shipped
        redaction layer rather than replacing it: the
        shipped layer (``core/redaction.py``) already
        guards the logging road through
        ``protect_logging``, session exports and
        listings through ``SessionStore``'s sanitizer,
        and terminal display through the agent's
        redactor - all on the shipped scanner's shapes
        plus configured and environment secrets. This
        feeding adds the pure layer's wider reading
        (the scanner's shapes plus the .env-style
        assignment shape) on the road the shipped
        layer does not itself pass through: a tool
        result, at the funnel, before it enters the
        transcript. Redaction here never breaks the
        road it rides on: a text the pure layer
        refuses (a non-text) is passed through the
        shipped redactor instead, so an output is
        never lost to a hygiene note.
        """
        try:
            from ..core.secret_hygiene import redact_secrets

            return redact_secrets(text)
        except Exception:
            try:
                return self.redactor.text(text)
            except Exception:
                return text

    def _publish_secret_refusal(self, record: Any) -> None:
        """Publish one refused screening as session news (M-110).

        The pure layer's ``secret_refusal`` record is
        journaled through the same checkpoint road
        every sibling slice uses, when a session is
        attached. Each screening's refusal is
        announced at most once: the announcement is
        keyed by the screening id, and every held
        screening holds a fresh id. A clean screening
        owes no news - its record is None and nothing
        is published.
        """
        if record is None:
            return
        announced = getattr(self, "_secret_hygiene_announced", None)
        if announced is None:
            announced = set()
            self._secret_hygiene_announced = announced
        if record["screening_id"] in announced:
            return
        announced.add(record["screening_id"])
        if self._session_store and self.session_id:
            self._checkpoint(record)

    # -- M-111: destructive-command doctrine --

    def _doctrine_registry(self):
        """The held doctrine registry (M-111).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds pure-layer judgements in the order
        judged. It is created on first use, so an
        agent whose ``__init__`` never ran still
        holds exactly one.
        """
        registry = getattr(self, "_destructive_doctrine_registry", None)
        if registry is None:
            from ..core.destructive_doctrine import DoctrineRegistry
            registry = DoctrineRegistry()
            self._destructive_doctrine_registry = registry
        return registry

    def doctrine_status(self) -> dict[str, Any]:
        """The doctrine judgements, in plain data (M-111).

        Every held judgement as its plain record, in
        the order judged, the one screen rendered
        from that same registry, and the plain
        explanation. Reading changes nothing: a
        status read judges, registers, or publishes
        nothing.
        """
        from ..core import destructive_doctrine

        registry = self._doctrine_registry()
        return {
            "judgements": [j.to_record() for j in registry.list_judgements()],
            "screen": destructive_doctrine.format_doctrine_screen(registry),
            "explanation": destructive_doctrine.PLAIN_EXPLANATION,
        }

    def get_judgement(self, judgement_id: Any):
        """The one held judgement an id names (M-111).

        An unknown id raises KeyError, exactly as the
        pure registry answers.
        """
        return self._doctrine_registry().get(judgement_id)

    def judge_command(self, command: Any, argv: Any = None) -> dict[str, Any]:
        """Judge one command against the ladder, and hold it (M-111).

        The command is judged by the pure layer and
        the judgement is held for the session. A
        judgement on the costly or irreversible rung
        is published as a ``destructive_act`` session
        event through the checkpoint road - its
        headline names an irreversible act's targets
        in plain words first. Judging runs nothing:
        the shipped sandbox denylist and the
        permission-profile roads still refuse and ask
        on the execution road exactly as before; this
        layer classifies and announces, it does not
        replace them. Returns the held judgement, its
        news record, the screen rendered after the
        judgement landed, and the plain explanation.
        """
        from ..core import destructive_doctrine

        registry = self._doctrine_registry()
        held = registry.judge(command, argv)
        record = registry.record(held.judgement_id)
        self._publish_doctrine_record(record)
        return {
            "judgement": held.to_record(),
            "record": record,
            "screen": destructive_doctrine.format_doctrine_screen(registry),
            "explanation": destructive_doctrine.PLAIN_EXPLANATION,
        }

    def _note_doctrine_command(self, name: str,
                               arguments: dict[str, Any]) -> None:
        """Judge one real command on the funnel (M-111).

        Called once per call from
        :meth:`_execute_call`, the funnel every tool
        call in a session travels, beside the M-109
        audit note. Only ``run_command`` carries a
        command to judge - every other tool is not a
        command, and this layer judges commands
        alone. The judgement is held for the session
        whatever the call's outcome was: a command
        the sandbox denylist refused was still
        judged, and its rung is still the truth owed.
        Judging never breaks the road it rides on: a
        command that cannot be judged is dropped,
        and the call itself stays the truth owed.
        """
        if name != "run_command":
            return
        command = arguments.get("command")
        if not isinstance(command, str) or not command.strip():
            return
        try:
            registry = self._doctrine_registry()
            held = registry.judge(command.strip())
            self._publish_doctrine_record(
                registry.record(held.judgement_id))
        except Exception:
            pass  # the call is the truth owed, not the judgement

    def _publish_doctrine_record(self, record: dict[str, Any]) -> None:
        """Publish one weighty judgement as session news (M-111).

        The pure layer's ``destructive_act`` record is
        journaled through the same checkpoint road
        every sibling slice uses, when a session is
        attached - for the rungs that carry weight:
        a costly act, and an irreversible act whose
        headline names its targets in plain words
        first. A reversible act needs no approval and
        owes no news, and an unclassified command is
        held and shown on the screen but never
        announced as an act this layer understands.
        Each judgement is announced at most once: the
        announcement is keyed by the judgement id,
        and every held judgement holds a fresh id.
        """
        if record.get("rung") not in ("costly", "irreversible"):
            return
        announced = getattr(self, "_doctrine_announced", None)
        if announced is None:
            announced = set()
            self._doctrine_announced = announced
        if record["judgement_id"] in announced:
            return
        announced.add(record["judgement_id"])
        if self._session_store and self.session_id:
            self._checkpoint(record)
    # -- M-112: rollback drills --

    def _drill_registry(self):
        """The held drill registry (M-112).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds pure-layer drill results in the
        order reported. It is created on first use,
        so an agent whose ``__init__`` never ran
        still holds exactly one.
        """
        registry = getattr(self, "_rollback_drill_registry", None)
        if registry is None:
            from ..core.rollback_drills import DrillRegistry
            registry = DrillRegistry()
            self._rollback_drill_registry = registry
        return registry

    def rollback_status(self) -> dict[str, Any]:
        """The drill results, in plain data (M-112).

        Every held result as its plain record, in
        the order reported, the one screen rendered
        from that same registry, and the plain
        explanation. Reading changes nothing: a
        status read judges, registers, or publishes
        nothing.
        """
        from ..core import rollback_drills

        registry = self._drill_registry()
        return {
            "results": [r.to_record() for r in registry.list_results()],
            "screen": rollback_drills.format_rollback_screen(registry),
            "explanation": rollback_drills.PLAIN_EXPLANATION,
        }

    def get_drill_run(self, run_id: Any):
        """The one held drill result an id names (M-112).

        An unknown id raises KeyError, exactly as the
        pure registry answers.
        """
        return self._drill_registry().get(run_id)

    def register_drill_result(self, result: Any = None,
                              **kwargs: Any) -> dict[str, Any]:
        """Hold one reported drill result, and announce it (M-112).

        The result is validated and held by the pure
        registry, and its ``rollback_drill_run``
        record is published as a session event
        through the checkpoint road, so the run's
        outcome is news, never just a log line.
        Returns the held result, its news record,
        the screen rendered after it landed, and the
        plain explanation.
        """
        from ..core import rollback_drills

        registry = self._drill_registry()
        held = registry.register(result, **kwargs)
        record = registry.record(held.run_id)
        self._publish_drill_record(record)
        return {
            "result": held.to_record(),
            "record": record,
            "screen": rollback_drills.format_rollback_screen(registry),
            "explanation": rollback_drills.PLAIN_EXPLANATION,
        }

    def judge_drill_run(self, drill_id: Any,
                        steps_passed: Any) -> dict[str, Any]:
        """Judge one drill run from its reported count (M-112).

        The pure judge reads the count a real test
        run reported against the held drill's own
        step count - recovered only when every step
        passed, never rounded up - and the result is
        held for the session and published as a
        ``rollback_drill_run`` session event. This
        layer judges counts, as data: it scripts no
        disaster and restores nothing itself - the
        drills are run in tests against the real
        recovery roads, and their reported counts
        are what is judged here. Returns the held
        result, its news record, the screen rendered
        after the judgement landed, and the plain
        explanation.
        """
        from ..core import rollback_drills

        registry = self._drill_registry()
        held = registry.judge(drill_id, steps_passed)
        record = registry.record(held.run_id)
        self._publish_drill_record(record)
        return {
            "result": held.to_record(),
            "record": record,
            "screen": rollback_drills.format_rollback_screen(registry),
            "explanation": rollback_drills.PLAIN_EXPLANATION,
        }

    def _publish_drill_record(self, record: dict[str, Any]) -> None:
        """Publish one drill run as session news (M-112).

        The pure layer's ``rollback_drill_run``
        record is journaled through the same
        checkpoint road every sibling slice uses,
        when a session is attached - for EVERY
        judged run, as the pure layer shapes it:
        a drill's outcome is owed in plain words
        whether it recovered whole, in part, or
        not at all. Each run is announced at most
        once: the announcement is keyed by the run
        id, and every held result holds a fresh id.
        """
        if record.get("type") != "rollback_drill_run":
            return
        announced = getattr(self, "_rollback_announced", None)
        if announced is None:
            announced = set()
            self._rollback_announced = announced
        if record["run_id"] in announced:
            return
        announced.add(record["run_id"])
        if self._session_store and self.session_id:
            self._checkpoint(record)

    # -- M-113: multi-repo workspaces --

    def _multi_repo_registry(self):
        """The held multi-repo registry (M-113).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds pure-layer repos and cross-repo
        sets in the order they were registered and
        built. It is created on first use, so an
        agent whose ``__init__`` never ran still
        holds exactly one. The attribute is named
        ``_multi_repo_store``, never the method's
        own name (the M-108 lesson).
        """
        registry = getattr(self, "_multi_repo_store", None)
        if registry is None:
            from ..core.multi_repo import MultiRepoRegistry
            registry = MultiRepoRegistry()
            self._multi_repo_store = registry
        return registry

    def multi_repo_status(self) -> dict[str, Any]:
        """The held repos and sets, in plain data (M-113).

        Every held repo and cross-repo set as its
        plain record, in the order held, the one
        screen rendered from that same registry,
        and the plain explanation. Reading changes
        nothing: a status read registers, builds,
        or publishes nothing.
        """
        from ..core import multi_repo

        registry = self._multi_repo_registry()
        return {
            "repos": [r.to_record() for r in registry.list_repos()],
            "sets": [s.to_record() for s in registry.list_sets()],
            "screen": multi_repo.format_multi_repo_screen(registry),
            "explanation": multi_repo.PLAIN_EXPLANATION,
        }

    def get_held_repo(self, repo_id: Any):
        """The one held repo an id names (M-113).

        An id no held repo carries refuses plainly,
        exactly as the pure registry answers.
        """
        return self._multi_repo_registry().get_repo(repo_id)

    def get_cross_repo_set(self, set_id: Any):
        """The one held cross-repo set an id names (M-113).

        An unknown id raises KeyError, exactly as
        the pure registry answers.
        """
        return self._multi_repo_registry().get(set_id)

    def multi_repo_workspace(self, name: Any):
        """The held repos as one workspace (M-113).

        Built from the registry's held repos, in
        registration order - the workspace a
        cross-repo set is built against.
        """
        return self._multi_repo_registry().workspace(name)

    def register_repo(self, repo: Any = None,
                      **kwargs: Any) -> dict[str, Any]:
        """Hold one repo for the session (M-113).

        The entry is validated and held by the pure
        registry; a duplicate repo id refuses.
        Registering a repo publishes nothing: a repo
        joining the workspace is setup, not news -
        the news this slice publishes is the
        cross-repo change set. Returns the held
        repo, the screen rendered after it landed,
        and the plain explanation.
        """
        from ..core import multi_repo

        registry = self._multi_repo_registry()
        held = registry.register_repo(repo, **kwargs)
        return {
            "repo": held.to_record(),
            "screen": multi_repo.format_multi_repo_screen(registry),
            "explanation": multi_repo.PLAIN_EXPLANATION,
        }

    def hold_cross_repo_set(self, cross: Any) -> dict[str, Any]:
        """Hold one built cross-repo set, and announce it (M-113).

        The set is held by the pure registry under
        its id or the next deterministic one, and
        its ``multi_repo_change_set`` record is
        published as a session event through the
        checkpoint road, so a cross-repo change is
        news, never just a log line. Returns the
        held set, its news record, the screen
        rendered after it landed, and the plain
        explanation.
        """
        from ..core import multi_repo

        registry = self._multi_repo_registry()
        held = registry.register(cross)
        record = registry.record(held.set_id)
        self._publish_multi_repo_record(record)
        return {
            "set": held.to_record(),
            "record": record,
            "screen": multi_repo.format_multi_repo_screen(registry),
            "explanation": multi_repo.PLAIN_EXPLANATION,
        }

    def register_cross_repo_set(self, workspace: Any, name: Any,
                                members: Any) -> dict[str, Any]:
        """Build one cross-repo set and hold it (M-113).

        The set is built on the pure layer's road -
        ONE M-084 change set spanning the named
        repos, each member judged by M-084's
        ``make_edit`` unchanged, a repo the
        workspace does not hold refusing plainly
        and a read-only repo refusing its member at
        build time - then held for the session and
        published as a ``multi_repo_change_set``
        session event. This layer builds and holds
        the set as data: it writes no file in any
        repo - planning and applying ride M-084's
        roads, exercised in this slice's tests
        against real on-disk repos. Returns the
        held set, its news record, the screen, and
        the plain explanation.
        """
        from ..core import multi_repo

        registry = self._multi_repo_registry()
        held = registry.build_and_register(workspace, name, members)
        record = registry.record(held.set_id)
        self._publish_multi_repo_record(record)
        return {
            "set": held.to_record(),
            "record": record,
            "screen": multi_repo.format_multi_repo_screen(registry),
            "explanation": multi_repo.PLAIN_EXPLANATION,
        }

    def _publish_multi_repo_record(self, record: dict[str, Any]) -> None:
        """Publish one cross-repo set as session news (M-113).

        The pure layer's ``multi_repo_change_set``
        record is journaled through the same
        checkpoint road every sibling slice uses,
        when a session is attached - for EVERY held
        set, as the pure layer shapes it: a
        cross-repo change is owed in plain words
        whether it is already reviewed whole or
        still holds undecided files. Each set is
        announced at most once: the announcement is
        keyed by the set id, and every held set
        holds a fresh id.
        """
        if record.get("type") != "multi_repo_change_set":
            return
        announced = getattr(self, "_multi_repo_announced", None)
        if announced is None:
            announced = set()
            self._multi_repo_announced = announced
        if record["set_id"] in announced:
            return
        announced.add(record["set_id"])
        if self._session_store and self.session_id:
            self._checkpoint(record)

    # -- M-114: remote and SSH work --

    def _remote_work_registry(self):
        """The held remote-work registry (M-114).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds pure-layer targets and work plans
        in the order they were registered and built.
        It is created on first use, so an agent whose
        ``__init__`` never ran still holds exactly
        one. The attribute is named
        ``_remote_work_store``, never the method's
        own name (the M-108 lesson).
        """
        registry = getattr(self, "_remote_work_store", None)
        if registry is None:
            from ..core.remote_work import RemoteWorkRegistry
            registry = RemoteWorkRegistry()
            self._remote_work_store = registry
        return registry

    def remote_work_status(self) -> dict[str, Any]:
        """The held targets and plans, in plain data (M-114).

        Every held target and work plan as its plain
        record, in the order held, the one screen
        rendered from that same registry, and the
        plain explanation. Reading changes nothing:
        a status read registers, judges, or
        publishes nothing.
        """
        from ..core import remote_work

        registry = self._remote_work_registry()
        return {
            "targets": [t.to_record() for t in registry.list_targets()],
            "plans": [p.to_record() for p in registry.list_plans()],
            "screen": remote_work.format_remote_screen(registry),
            "explanation": remote_work.PLAIN_EXPLANATION,
        }

    def get_remote_target(self, target_id: Any):
        """The one held target an id names (M-114).

        An id no held target carries refuses plainly,
        exactly as the pure registry answers.
        """
        return self._remote_work_registry().get_target(target_id)

    def get_remote_work_plan(self, plan_id: Any):
        """The one held work plan an id names (M-114).

        An unknown id raises KeyError, exactly as
        the pure registry answers.
        """
        return self._remote_work_registry().get(plan_id)

    def register_remote_target(self, target: Any = None,
                               **kwargs: Any) -> dict[str, Any]:
        """Hold one remote target for the session (M-114).

        The target is validated and held by the pure
        registry; a duplicate target id refuses.
        Registering a target publishes nothing: a
        target joining the session is setup, not
        news - the news this slice publishes is the
        judged work plan. Returns the held target,
        the screen rendered after it landed, and the
        plain explanation.
        """
        from ..core import remote_work

        registry = self._remote_work_registry()
        held = registry.register_target(target, **kwargs)
        return {
            "target": held.to_record(),
            "screen": remote_work.format_remote_screen(registry),
            "explanation": remote_work.PLAIN_EXPLANATION,
        }

    def hold_remote_work_plan(self, plan: Any) -> dict[str, Any]:
        """Judge one built work plan whole and hold it (M-114).

        The plan is judged whole by the pure judge
        against the target this session holds under
        the plan's own target id - an unknown target,
        a step outside the target's remote workspace
        root, or a file operation that would copy a
        file back to this machine refuses, and a
        refusal holds nothing and publishes nothing.
        A judged plan is held by the pure registry
        and published as its ``remote_work_plan``
        session-news record through the checkpoint
        road. This layer opens no connection and
        runs nothing: holding, judging and
        publishing is the slice's agent work.
        Returns the held plan, its news record, the
        screen rendered after it landed, and the
        plain explanation.
        """
        from ..core import remote_work

        registry = self._remote_work_registry()
        judged = remote_work.judge_work_plan(plan, registry)
        held = registry.register(judged)
        record = registry.record(held.plan_id)
        self._publish_remote_work_record(record)
        return {
            "plan": held.to_record(),
            "record": record,
            "screen": remote_work.format_remote_screen(registry),
            "explanation": remote_work.PLAIN_EXPLANATION,
        }

    def judge_remote_work_plan(self, target: Any, name: Any,
                               steps: Any) -> dict[str, Any]:
        """Build one work plan, judge it whole, and hold it (M-114).

        The plan is built naming the ONE target -
        a held target id or a RemoteTarget - and
        judged by the pure judge in one move, on the
        pure registry's ``build_and_register`` road:
        an unknown target, a shell-string command
        (the M-103 rule), a step outside the remote
        workspace root, or a file operation that
        would copy a file back to this machine
        refuses, and a refusal holds nothing and
        publishes nothing. A judged plan is held for
        the session and published as a
        ``remote_work_plan`` session event. This
        layer opens no SSH connection and runs no
        remote command: no shipped transport road
        exists to carry one, and none is faked.
        Returns the held plan, its news record, the
        screen, and the plain explanation.
        """
        from ..core import remote_work

        registry = self._remote_work_registry()
        held = registry.build_and_register(target, name, steps)
        record = registry.record(held.plan_id)
        self._publish_remote_work_record(record)
        return {
            "plan": held.to_record(),
            "record": record,
            "screen": remote_work.format_remote_screen(registry),
            "explanation": remote_work.PLAIN_EXPLANATION,
        }

    def _publish_remote_work_record(self, record: dict[str, Any]) -> None:
        """Publish one remote work plan as session news (M-114).

        The pure layer's ``remote_work_plan`` record
        is journaled through the same checkpoint
        road every sibling slice uses, when a
        session is attached - for EVERY judged plan,
        as the pure layer shapes it: remote work is
        owed in plain words, its headline always
        stating that every file and command stays on
        that machine. Each plan is announced at most
        once: the announcement is keyed by the plan
        id, and every held plan holds a fresh id.
        """
        if record.get("type") != "remote_work_plan":
            return
        announced = getattr(self, "_remote_work_announced", None)
        if announced is None:
            announced = set()
            self._remote_work_announced = announced
        if record["plan_id"] in announced:
            return
        announced.add(record["plan_id"])
        if self._session_store and self.session_id:
            self._checkpoint(record)

    # -- M-115: offline and degraded grace --

    def _degradation_registry(self):
        """The held degradation registry (M-115).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds pure-layer degradation assessments
        in the order they were judged. It is created
        on first use, so an agent whose ``__init__``
        never ran still holds exactly one. The
        attribute is named ``_degradation_store``,
        never the method's own name (the M-108
        lesson).
        """
        registry = getattr(self, "_degradation_store", None)
        if registry is None:
            from ..core.offline_grace import DegradationRegistry
            registry = DegradationRegistry()
            self._degradation_store = registry
        return registry

    def grace_status(self) -> dict[str, Any]:
        """The held degradation records, in plain data (M-115).

        Every held assessment as its plain record, in
        the order judged, the one screen rendered
        from that same registry, and the plain
        explanation. Reading changes nothing: a
        status read judges, registers, or publishes
        nothing.
        """
        from ..core import offline_grace

        registry = self._degradation_registry()
        return {
            "records": [a.to_record() for a in registry.list_records()],
            "screen": offline_grace.format_grace_screen(registry),
            "explanation": offline_grace.PLAIN_EXPLANATION,
        }

    def get_grace_record(self, record_id: Any):
        """The one held assessment an id names (M-115).

        An unknown id raises KeyError, exactly as the
        pure registry answers.
        """
        return self._degradation_registry().get(record_id)

    def register_grace_assessment(self, assessment: Any) -> dict[str, Any]:
        """Hold one judged assessment for the session (M-115).

        The assessment is held by the pure registry
        under its id or a fresh deterministic one - a
        duplicate id refuses, and a refusal holds
        nothing new and publishes nothing - and a
        held assessment is published as its
        ``degradation_change`` session-news record
        through the checkpoint road, so what the
        coder lost is news, never just a log line.
        Returns the held assessment, its news record,
        the screen rendered after it landed, and the
        plain explanation.
        """
        from ..core import offline_grace

        registry = self._degradation_registry()
        held = registry.register(assessment)
        record = registry.record(held.record_id)
        self._publish_degradation_record(record)
        return {
            "assessment": held.to_record(),
            "record": record,
            "screen": offline_grace.format_grace_screen(registry),
            "explanation": offline_grace.PLAIN_EXPLANATION,
        }

    def judge_degradation(self, evidence: Any) -> dict[str, Any]:
        """Judge evidence and hold the assessment (M-115).

        The pure judge derives the state from the
        given evidence only - full only when the
        provider, the language server and the network
        all affirmatively answer, a dimension whose
        evidence is unknown named unknown and never
        guessed up or down, and one failure never
        inventing another - and the assessment is
        held for the session and published as a
        ``degradation_change`` session event. Bad
        evidence refuses plainly, and a refusal holds
        nothing and publishes nothing. This layer
        gathers no evidence itself and probes
        nothing: judging held evidence is the slice's
        agent work. Returns the held assessment, its
        news record, the screen, and the plain
        explanation.
        """
        from ..core import offline_grace

        registry = self._degradation_registry()
        held = registry.judge_and_register(evidence)
        record = registry.record(held.record_id)
        self._publish_degradation_record(record)
        return {
            "assessment": held.to_record(),
            "record": record,
            "screen": offline_grace.format_grace_screen(registry),
            "explanation": offline_grace.PLAIN_EXPLANATION,
        }

    def _publish_degradation_record(self, record: dict[str, Any]) -> None:
        """Publish one degradation change as session news (M-115).

        The pure layer's ``degradation_change``
        record is journaled through the same
        checkpoint road every sibling slice uses,
        when a session is attached - for EVERY judged
        assessment, as the pure layer shapes it: a
        degradation is owed in plain words, its
        headline always stating what was lost. Each
        record is announced at most once: the
        announcement is keyed by the record id, and
        every held record holds a fresh id.
        """
        if record.get("type") != "degradation_change":
            return
        announced = getattr(self, "_degradation_announced", None)
        if announced is None:
            announced = set()
            self._degradation_announced = announced
        if record["record_id"] in announced:
            return
        announced.add(record["record_id"])
        if self._session_store and self.session_id:
            self._checkpoint(record)

    # -- M-116: approval by phone-sized moments --

    def _approval_moment_registry(self):
        """The held approval-moment registry (M-116).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds pure-layer moment assessments in
        the order they were judged. It is created on
        first use, so an agent whose ``__init__``
        never ran still holds exactly one. The
        attribute is named ``_approval_moment_store``,
        never the method's own name (the M-108
        lesson).
        """
        registry = getattr(self, "_approval_moment_store", None)
        if registry is None:
            from ..core.approval_moments import ApprovalMomentRegistry
            registry = ApprovalMomentRegistry()
            self._approval_moment_store = registry
        return registry

    def approval_moment_status(self) -> dict[str, Any]:
        """The held approval moments, in plain data (M-116).

        Every held assessment as its plain record, in
        the order judged, the one screen rendered
        from that same registry, and the plain
        explanation. Reading changes nothing: a
        status read judges, registers, or publishes
        nothing.
        """
        from ..core import approval_moments

        registry = self._approval_moment_registry()
        return {
            "records": [a.to_record() for a in registry.list_records()],
            "screen": approval_moments.format_moment_screen(registry),
            "explanation": approval_moments.PLAIN_EXPLANATION,
        }

    def get_approval_moment(self, record_id: Any):
        """The one held assessment an id names (M-116).

        An unknown id raises KeyError, exactly as the
        pure registry answers.
        """
        return self._approval_moment_registry().get(record_id)

    def register_approval_moment(self, assessment: Any) -> dict[str, Any]:
        """Hold one judged moment for the session (M-116).

        The assessment is held by the pure registry
        under its id or a fresh deterministic one - a
        duplicate id refuses, and a refusal holds
        nothing new and publishes nothing - and a
        held assessment is published as its
        ``approval_moment`` session-news record
        through the checkpoint road, so an approval
        ask is announced as the complete question it
        is, never lost as a bare prompt. Returns the
        held assessment, its news record, the screen
        rendered after it landed, and the plain
        explanation.
        """
        from ..core import approval_moments

        registry = self._approval_moment_registry()
        held = registry.register(assessment)
        record = registry.record(held.record_id)
        self._publish_approval_moment_record(record)
        return {
            "assessment": held.to_record(),
            "record": record,
            "screen": approval_moments.format_moment_screen(registry),
            "explanation": approval_moments.PLAIN_EXPLANATION,
        }

    def judge_approval_moment(self, proposal: Any) -> dict[str, Any]:
        """Judge a moment proposal and hold it (M-116).

        The pure judge derives completeness from the
        given proposal only - one question, full
        context (what, where, what it does), every
        choice stating its effect, the whole text
        within one phone-sized moment - and invents
        no context, choice or effect the proposal
        does not carry. The assessment is held for
        the session and published as an
        ``approval_moment`` session event. A bad
        proposal refuses plainly, and a refusal holds
        nothing and publishes nothing. Returns the
        held assessment, its news record, the screen,
        and the plain explanation.
        """
        from ..core import approval_moments

        registry = self._approval_moment_registry()
        held = registry.judge_and_register(proposal)
        record = registry.record(held.record_id)
        self._publish_approval_moment_record(record)
        return {
            "assessment": held.to_record(),
            "record": record,
            "screen": approval_moments.format_moment_screen(registry),
            "explanation": approval_moments.PLAIN_EXPLANATION,
        }

    def approval_moment_for_call(self, name: Any, arguments: Any):
        """Shape one approval moment from a real tool call (M-116).

        The moment is built from the call the
        ``ToolPolicy`` ask road actually carries -
        the tool ``name`` and its ``arguments`` - and
        from nothing else. What is asked is the call
        itself. Where it acts is named only when the
        arguments themselves name a place (a path, a
        file, a directory); what it does is named
        only when the arguments themselves carry the
        act (a command). A part the real call does
        not name is left empty, so the judge honestly
        names it missing - this layer invents no
        context. The two choices are the approval
        road's own: approve lets this call run, deny
        stops it, each stating that effect. Shaping
        registers and publishes nothing.
        """
        from ..core.approval_moments import build_choice, build_moment

        tool = name.strip() if isinstance(name, str) else ""
        args = arguments if isinstance(arguments, dict) else {}
        where = ""
        for key in ("path", "file_path", "file", "directory",
                    "cwd", "root", "destination"):
            value = args.get(key)
            if isinstance(value, str) and value.strip():
                where = value.strip()
                break
        does = ""
        for key in ("command", "cmd"):
            value = args.get(key)
            if isinstance(value, str) and value.strip():
                does = value.strip()
                break
        choices = ()
        if tool:
            choices = (
                build_choice(
                    "approve", "Approve it",
                    f"the {tool} call runs"),
                build_choice(
                    "deny", "Deny it",
                    f"the {tool} call does not run"),
            )
        return build_moment(
            what=f"Run {tool}?" if tool else "",
            where=where, what_it_does=does, choices=choices)

    def judge_approval_call(self, name: Any,
                            arguments: Any) -> dict[str, Any]:
        """Shape, judge and hold the moment of one real call (M-116).

        The moment is shaped from the real call alone
        (see :meth:`approval_moment_for_call`), judged
        by the pure judge, held for the session, and
        published as an ``approval_moment`` session
        event. Returns the held assessment, its news
        record, the screen, and the plain explanation.
        """
        return self.judge_approval_moment(
            self.approval_moment_for_call(name, arguments))

    def _note_approval_moment(self, name: Any, arguments: Any) -> None:
        """Shape and hold the moment of one fresh ask (M-116).

        Called from :meth:`bind_tui` at the moment a
        fresh approval ask is raised on the live
        ``ToolPolicy`` road - after a remembered
        approval has had its say (a standing answer
        raises no fresh ask, so it shapes no moment)
        and before the prompt itself. Shaping is
        news, never a gate: a failure to shape must
        never turn an ask into a refusal, so a
        shaping failure is swallowed here and the
        prompt road decides, exactly as it did
        before this slice.
        """
        try:
            self.judge_approval_call(name, arguments)
        except Exception:
            pass

    def _publish_approval_moment_record(self, record: dict[str, Any]) -> None:
        """Publish one judged moment as session news (M-116).

        The pure layer's ``approval_moment`` record
        is journaled through the same checkpoint
        road every sibling slice uses, when a session
        is attached - for EVERY judged moment, as the
        pure layer shapes it: an approval ask is owed
        as one complete question, its headline always
        stating the question whole or naming what it
        lacks. Each record is announced at most once:
        the announcement is keyed by the record id,
        and every held record holds a fresh id.
        """
        if record.get("type") != "approval_moment":
            return
        announced = getattr(self, "_approval_moment_announced", None)
        if announced is None:
            announced = set()
            self._approval_moment_announced = announced
        if record["record_id"] in announced:
            return
        announced.add(record["record_id"])
        if self._session_store and self.session_id:
            self._checkpoint(record)

    # -- M-119: policy as code --

    def _policy_registry(self):
        """The held project-policy registry (M-119).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds pure-layer policies in the order
        they were loaded. It is created on first use,
        so an agent whose ``__init__`` never ran still
        holds exactly one. The attribute is named
        ``_policy_store``, never the method's own
        name (the M-108 lesson).
        """
        registry = getattr(self, "_policy_store", None)
        if registry is None:
            from ..core.policy_file import PolicyRegistry
            registry = PolicyRegistry()
            self._policy_store = registry
        return registry

    def _policy_applications(self) -> dict[str, Any]:
        """Application outcomes by policy id (M-119)."""
        outcomes = getattr(self, "_policy_outcome_store", None)
        if outcomes is None:
            outcomes = {}
            self._policy_outcome_store = outcomes
        return outcomes

    def project_policy_path(self):
        """The policy file path in this workspace (M-119)."""
        from ..core.policy_file import default_policy_path
        return default_policy_path(self.project_root)

    def policy_on_disk(self):
        """The policy the file on disk names, or None (M-119).

        A missing file is None - no policy, never an
        invented one. A present file that fails
        validation raises the pure layer's
        ValidationError naming the file and reason.
        """
        from ..core.policy_file import load_policy_file
        return load_policy_file(self.project_policy_path())

    def get_project_policy(self, policy_id: Any):
        """The one held policy an id names (M-119).

        An unknown id raises KeyError, exactly as the
        pure registry answers.
        """
        return self._policy_registry().get(policy_id)

    def project_policy_status(self) -> dict[str, Any]:
        """The project policy, in plain data (M-119).

        The held policies as plain records with their
        application outcomes, the policy the file on
        disk names today (or the plain no-policy state,
        or the refusal reason when the file on disk
        fails validation), the one screen rendered
        from the held-or-disk policy, and the plain
        explanation. Reading applies, registers, and
        publishes nothing.
        """
        from ..core import policy_file

        registry = self._policy_registry()
        outcomes = self._policy_applications()
        held = []
        for pid in registry.policy_ids():
            entry: dict[str, Any] = {
                "policy_id": pid,
                "policy": registry.get(pid).to_record()}
            if pid in outcomes:
                entry["application"] = outcomes[pid]
            held.append(entry)
        refusal = None
        disk_policy = None
        try:
            disk_policy = self.policy_on_disk()
        except ValueError as exc:
            refusal = str(exc)
        shown = disk_policy
        if shown is None and held:
            shown = registry.get(registry.policy_ids()[-1])
        if refusal is not None:
            screen = "Project policy refused: " + refusal
        else:
            screen = policy_file.format_policy_screen(shown)
        return {
            "held": held,
            "disk": (disk_policy.to_record()
                     if disk_policy is not None else None),
            "refusal": refusal,
            "path": str(self.project_policy_path()),
            "screen": screen,
            "explanation": policy_file.PLAIN_EXPLANATION,
        }

    def set_hooks(self, hooks: Any) -> dict[str, Any]:
        """Replace the configured hooks whole (M-119).

        This is the M-101/M-102 storage road, in the
        exact shape :meth:`install_hook_pack` applies
        it: the hooks are validated by the pure M-101
        layer before anything mutates; the change is
        journaled first as a ``hooks_changed`` record
        when a session is attached; the stored list is
        the hooks' plain records under the M-101
        ``hooks`` setting; a failed save restores the
        previous config exactly and journals a
        compensating ``hooks_reverted``. Hooks already
        exactly as named change nothing and write
        nothing (the M-102 already-installed precedent).
        """
        import copy

        from ..core import hooks as hooks_module

        target = hooks_module.validate_hooks([
            h.to_record() if isinstance(h, hooks_module.Hook) else h
            for h in (hooks or ())])
        existing = hooks_module.hooks_from_config(self.config)
        if list(existing) == list(target):
            return {"type": "hooks_changed", "changed": False,
                    "hooks": [h.to_record() for h in target],
                    "session_id": self.session_id,
                    "journaled": False}
        change: dict[str, Any] = {
            "type": "hooks_changed",
            "hooks": [h.to_record() for h in target]}
        journaled = False
        if self._session_store and self.session_id:
            self._checkpoint(change)
            journaled = True
        previous = copy.deepcopy(self.config)
        self.config[hooks_module.SETTING_KEY] = [
            h.to_record() for h in target]
        if not self.save_config():
            self.config = previous
            if journaled:
                try:
                    self._checkpoint({
                        "type": "hooks_reverted",
                        "reason": "The hooks change could not "
                                  "be saved; the previous "
                                  "hooks were preserved.",
                    })
                except Exception:
                    pass  # the RuntimeError below is the truth owed
            raise RuntimeError(
                "Hooks change could not be saved; previous "
                "hooks were preserved")
        return {**change, "changed": True,
                "session_id": self.session_id,
                "journaled": journaled}

    def _publish_policy_record(self, record: dict[str, Any]) -> None:
        """Publish one applied policy as session news (M-119).

        The pure layer's ``project_policy`` record is
        journaled through the same checkpoint road
        every sibling slice uses, when a session is
        attached. Each policy is announced at most
        once: the announcement is keyed by the policy
        record id, and every held policy holds a fresh
        id.
        """
        if record.get("type") != "project_policy":
            return
        announced = getattr(self, "_policy_announced", None)
        if announced is None:
            announced = set()
            self._policy_announced = announced
        if record["policy_id"] in announced:
            return
        announced.add(record["policy_id"])
        if self._session_store and self.session_id:
            self._checkpoint(record)

    def _publish_policy_refusal(self, reason: str) -> None:
        """Publish one whole-policy refusal as news (M-119)."""
        if self._session_store and self.session_id:
            self._checkpoint({
                "type": "project_policy_refused",
                "session_event": "project_policy_refused",
                "news": True,
                "slice": "M-119",
                "reason": reason,
                "headline": (
                    "Project policy refused whole - nothing "
                    "was applied: " + reason),
            })

    def _apply_policy_plan(self, plan: Any) -> list:
        """Apply one policy plan, step by step (M-119).

        The fixed order is posture, jail, grants,
        hooks - each step through its own shipped
        journal-first road, never a direct settings
        write. A step the live settings already match
        exactly is recorded ``satisfied`` and is not
        forced through a road that refuses no-ops.
        Steps follow the change-set precedent: one
        step's refusal or save failure is recorded
        with its reason, that road's own revert
        behaviour governs that step, and the
        remaining steps still run. Returns the step
        outcomes, in order.
        """
        from ..core import hooks as hooks_module
        from ..core import path_jail, permission_profiles

        settings = plan.settings()
        steps: list[dict[str, Any]] = []

        def run(step: str, fn: Any) -> None:
            try:
                detail = fn()
                steps.append({"step": step, "status": "applied",
                              "detail": detail})
            except (ValueError, KeyError, RuntimeError) as exc:
                steps.append({"step": step, "status": "failed",
                              "reason": str(exc)})

        if "permission_profile" in settings:
            wanted = settings["permission_profile"]
            if self.config.get(
                    permission_profiles.SETTING_KEY) == wanted:
                steps.append({"step": "posture",
                              "status": "satisfied"})
            else:
                run("posture", lambda: self.set_permission_profile(
                    wanted)["type"])
        if "path_jail" in settings:
            wanted_jail = settings["path_jail"]
            if path_jail.enabled_from_config(self.config) == wanted_jail:
                steps.append({"step": "jail", "status": "satisfied"})
            else:
                run("jail", lambda: self.set_path_jail(
                    wanted_jail)["type"])
            grant_steps: list[dict[str, Any]] = []
            current = list(path_jail.grants_from_config(self.config))
            for grant in settings.get("path_grants", []):
                if grant in current:
                    grant_steps.append(
                        {"grant": grant, "status": "satisfied"})
                    continue
                try:
                    self.add_path_grant(grant)
                    current.append(grant)
                    grant_steps.append(
                        {"grant": grant, "status": "applied"})
                except (ValueError, KeyError, RuntimeError) as exc:
                    grant_steps.append(
                        {"grant": grant, "status": "failed",
                         "reason": str(exc)})
            failed = [g for g in grant_steps
                      if g["status"] == "failed"]
            steps.append({
                "step": "grants",
                "status": "failed" if failed else "applied",
                "grants": grant_steps})
        if "hooks" in settings:
            wanted_hooks = settings["hooks"]
            if self.config.get(hooks_module.SETTING_KEY) == wanted_hooks:
                steps.append({"step": "hooks", "status": "satisfied"})
            else:
                def apply_hooks() -> str:
                    outcome = self.set_hooks(wanted_hooks)
                    return "changed" if outcome["changed"] else "satisfied"
                try:
                    detail = apply_hooks()
                    steps.append({
                        "step": "hooks",
                        "status": ("applied" if detail == "changed"
                                   else "satisfied")})
                except (ValueError, KeyError, RuntimeError) as exc:
                    steps.append({"step": "hooks", "status": "failed",
                                  "reason": str(exc)})
        return steps

    def apply_project_policy(self) -> dict[str, Any]:
        """Load the workspace policy file and apply it (M-119).

        The file at the workspace root is loaded whole
        through the pure layer first. No file is a
        plain no-policy outcome: nothing applied,
        nothing invented, nothing published. A file
        that fails validation is refused whole: no
        step runs, the refusal is published as session
        news with the validator's reason, and the
        outcome says so plainly. A valid policy is
        registered for the session, its plan applied
        step by step through the shipped roads (see
        :meth:`_apply_policy_plan`), every step's
        outcome held with the policy's record, and the
        applied policy published as ``policy_record``
        session news, deduped per policy record id.
        """
        from ..core import policy_file

        path = str(self.project_policy_path())
        try:
            policy = self.policy_on_disk()
        except ValueError as exc:
            reason = str(exc)
            self._publish_policy_refusal(reason)
            headline = ("Project policy refused whole - nothing "
                        "was applied: " + reason)
            return {"status": "refused", "reason": reason,
                    "policy_id": None, "steps": [], "path": path,
                    "headline": headline, "screen": headline}
        if policy is None:
            return {"status": "no_policy", "reason": None,
                    "policy_id": None, "steps": [], "path": path,
                    "headline": policy_file.format_policy(None),
                    "screen": policy_file.format_policy_screen(None)}
        registry = self._policy_registry()
        policy_id = registry.register(policy)
        plan = policy_file.application_plan(policy)
        steps = self._apply_policy_plan(plan)
        complete = all(
            step["status"] in ("applied", "satisfied")
            for step in steps)
        status = "applied" if complete else "partial"
        record = policy_file.policy_record(policy)
        record["policy_id"] = policy_id
        record["steps"] = steps
        record["applied"] = complete
        self._policy_applications()[policy_id] = {
            "status": status, "steps": steps}
        self._publish_policy_record(record)
        lines = [policy_file.format_policy(policy), "",
                 "Policy application (" + status + "):"]
        if not steps:
            lines.append("  no sections - nothing to set.")
        for step in steps:
            line = f"  {step['step']}: {step['status']}"
            if step["status"] == "failed":
                line += " - " + step.get("reason", "")
            lines.append(line)
        return {"status": status, "reason": None,
                "policy_id": policy_id, "record": record,
                "policy": policy.to_record(), "steps": steps,
                "path": path,
                "headline": policy_file.plain_words(policy),
                "screen": "\n".join(lines)}

    def _load_project_policy_at_start(self) -> None:
        """Apply the workspace policy at session start (M-119).

        Called from :meth:`attach_session` once the
        session is attached, so an applied policy and
        a refusal both publish as session news on the
        new session. A failure here never breaks the
        session itself (the salvaged-restore
        precedent): the apply road has already
        published any refusal it owes.
        """
        try:
            self.apply_project_policy()
        except Exception:
            pass

    # -- M-121: agents as files --

    def _crew_registry(self):
        """The held crew registry (M-121).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds pure-layer crew members in the
        order they joined. It is created on first
        use, so an agent whose ``__init__`` never ran
        still holds exactly one. The attribute is
        named ``_crew_store``, never the method's own
        name (the M-108 lesson).
        """
        registry = getattr(self, "_crew_store", None)
        if registry is None:
            from ..core.crew_members import CrewRegistry
            registry = CrewRegistry()
            self._crew_store = registry
        return registry

    def crew_status(self) -> dict[str, Any]:
        """The crew, in plain data (M-121).

        The members held this session as plain
        records, the shipped casting as plain records
        (the existing characters, as data), the one
        screen - rendered from the held registry, or
        from the shipped casting when nothing is held
        yet - and the plain explanation. Reading
        registers, spawns, and publishes nothing.
        """
        from ..core import crew_members

        registry = self._crew_registry()
        held = registry.list_members()
        casting = crew_members.load_casting()
        shown = registry if held else casting
        return {
            "members": [m.to_record() for m in held],
            "casting": [m.to_record() for m in casting.members],
            "screen": crew_members.format_crew_screen(shown),
            "explanation": crew_members.PLAIN_EXPLANATION,
        }

    def get_crew_member(self, member_id: Any):
        """The one held member an id names (M-121).

        An unknown id raises KeyError, exactly as the
        pure registry answers.
        """
        return self._crew_registry().get(member_id)

    def find_crew_member(self, member_id: Any):
        """One member by id: held first, then the casting (M-121).

        The session's held registry answers first; a
        member the session has not taken up is read
        from the shipped casting. An id neither holds
        raises KeyError.
        """
        try:
            return self._crew_registry().get(member_id)
        except KeyError:
            from ..core.crew_members import load_casting
            return load_casting().get(member_id)

    def crew_member_for_office(self, office: Any):
        """The member holding one office (M-121).

        The held registry answers first; with no held
        member for the office, the shipped casting
        answers. An office no member holds raises
        KeyError; the ``primary`` office raises
        ValueError, as the pure layer refuses it.
        """
        held = self._crew_registry().list_members(office)
        if held:
            return held[0]
        from ..core.crew_members import load_casting
        return load_casting().by_office(office)

    def register_crew_member(self, member: Any) -> dict[str, Any]:
        """Hold one crew member for the session (M-121).

        The member is held by the pure registry under
        its id or a fresh deterministic one - a
        duplicate id or name refuses, and a refusal
        holds nothing new and publishes nothing - and
        a held member is published as its
        ``casting_record`` session-news record through
        the checkpoint road, so a member joining is
        news with its shape attached. Returns the held
        member, its news record, the screen rendered
        after it landed, and the plain explanation.
        """
        from ..core import crew_members

        registry = self._crew_registry()
        held = registry.register(member)
        record = crew_members.casting_record(held)
        self._publish_crew_record(record)
        return {
            "member": held.to_record(),
            "record": record,
            "screen": crew_members.format_crew_screen(registry),
            "explanation": crew_members.PLAIN_EXPLANATION,
        }

    def load_crew_casting(self, casting: Any = None) -> dict[str, Any]:
        """Hold a whole casting for the session (M-121).

        With no casting named, the shipped casting is
        loaded through the pure layer - the existing
        characters as the first castings. A casting
        loaded from a file (the pure layer's
        ``load_casting_file`` road) may be passed
        instead, so a new member joins from a file,
        not a code change. Every member is held in
        file order and published as its
        ``casting_record`` session news, deduped per
        member id. The pure registry refuses a
        duplicate id or name whole - a casting the
        session already holds cannot be loaded twice.
        Returns the held members, their news records,
        the count, the screen, and the explanation.
        """
        from ..core import crew_members

        registry = self._crew_registry()
        casting = casting if casting is not None \
            else crew_members.load_casting()
        held = registry.register_casting(casting)
        records = [crew_members.casting_record(m) for m in held]
        for record in records:
            self._publish_crew_record(record)
        return {
            "members": [m.to_record() for m in held],
            "records": records,
            "count": len(held),
            "screen": crew_members.format_crew_screen(registry),
            "explanation": crew_members.PLAIN_EXPLANATION,
        }

    def spawn_crew_member(self, member_id: Any,
                          task: Any = None) -> dict[str, Any]:
        """Spawn one held crew member from its record (M-121).

        The spawn rides the one shipped road -
        :meth:`AgentManager.spawn_subagent` - fed the
        member's own name, so the member's prompt is
        the shipped ``DEFAULT_SUBAGENTS`` entry its
        record names and its office route is applied
        by the road itself through the M-029
        ``office_for_agent_name`` mapping. The policy
        handed to the road is the member record's own
        posture, read through the M-095 vocabulary
        (``policy_mode_for`` of the shipped profile).
        A member record carrying an explicit model
        route has that route set on the spawned
        member's config, in the same assignment the
        spawn road makes for office routes; a member
        on the session default is left exactly as the
        road routed it. A *task*, when named, is
        queued to the spawned member's inbox in the
        delegation road's own words.

        The spawn road only spawns names the session
        config carries: a held member whose name no
        ``sub_agents`` entry names - a new member
        that arrived as a file, whose prompt prose no
        shipped entry carries yet - is refused by the
        road itself, and this method reports that
        plainly (``spawned`` False, with the reason)
        instead of inventing a spawn. A successful
        spawn publishes the member's ``casting_record``
        as session news, deduped per member id.
        """
        from ..core import crew_members
        from ..core.permission_profiles import (
            builtin_profile,
            policy_mode_for,
        )
        from ..core.policy import ToolPolicy

        registry = self._crew_registry()
        held = registry.get(member_id)
        record = crew_members.casting_record(held)
        mode = policy_mode_for(builtin_profile(held.posture))
        policy = ToolPolicy(mode)
        spawned = agent_manager.spawn_subagent(
            held.name, self.project_root, policy=policy,
            tui_app=self.tui_app)
        if spawned is None:
            return {
                "spawned": False,
                "member": held.to_record(),
                "record": record,
                "policy_mode": mode,
                "reason": (
                    f"No sub-agent named {held.name!r} is "
                    "configured in this session, so the "
                    "spawn road refused it - a member "
                    "record alone does not create a "
                    "spawnable sub-agent; the shipped "
                    "castings ride the shipped "
                    "DEFAULT_SUBAGENTS entries, and a new "
                    "member spawns once its name is "
                    "carried there."),
                "screen": crew_members.format_crew_screen(registry),
                "explanation": crew_members.PLAIN_EXPLANATION,
            }
        if held.model_route is not None:
            spawned.config["model"] = held.model_route.model
            spawned.config["base_url"] = held.model_route.base_url
        queued = False
        if task is not None:
            spawned.inbox.put(f"Task from {self.name}:\n{task}")
            queued = True
        self._publish_crew_record(record)
        return {
            "spawned": True,
            "member": held.to_record(),
            "record": record,
            "agent_name": spawned.name,
            "policy_mode": mode,
            "route_words": held.route_words,
            "task_queued": queued,
            "screen": crew_members.format_crew_screen(registry),
            "explanation": crew_members.PLAIN_EXPLANATION,
        }

    def _publish_crew_record(self, record: dict[str, Any]) -> None:
        """Publish one crew member as session news (M-121).

        The pure layer's ``casting_record`` is
        journaled through the same checkpoint road
        every sibling slice uses, when a session is
        attached. Each member is announced at most
        once: the announcement is keyed by the member
        record id, and every held member holds an id.
        """
        if record.get("type") != "crew_member":
            return
        announced = getattr(self, "_crew_announced", None)
        if announced is None:
            announced = set()
            self._crew_announced = announced
        member_id = record.get("member_id")
        if member_id is not None:
            if member_id in announced:
                return
            announced.add(member_id)
        if self._session_store and self.session_id:
            self._checkpoint(record)

    # -- M-122: the six offices formalised --

    def _offices_registry(self):
        """The held offices registry (M-122).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds pure-layer office definitions in
        the order they were taken up. It is created
        on first use, so an agent whose ``__init__``
        never ran still holds exactly one. The
        attribute is named ``_offices_store``, never
        the method's own name (the M-108 lesson).
        """
        registry = getattr(self, "_offices_store", None)
        if registry is None:
            from ..core.offices import OfficeRegistry
            registry = OfficeRegistry()
            self._offices_store = registry
        return registry

    def offices_status(self) -> dict[str, Any]:
        """The offices, in plain data (M-122).

        The definitions held this session as plain
        records, the shipped book as plain records
        (the six offices formalised, as data), the
        one screen - rendered from the held registry,
        or from the shipped book when nothing is held
        yet - and the plain explanation. Reading
        registers and publishes nothing.
        """
        from ..core import offices

        registry = self._offices_registry()
        held = registry.list_definitions()
        book = offices.load_offices()
        shown = registry if held else book
        return {
            "offices": [d.to_record() for d in held],
            "book": [d.to_record() for d in book.definitions],
            "screen": offices.format_offices_screen(shown),
            "explanation": offices.PLAIN_EXPLANATION,
        }

    def get_office_definition(self, office: Any):
        """The one held definition an office names (M-122).

        An office the session does not hold raises
        KeyError, exactly as the pure registry
        answers; an unformalised office raises
        ValueError, as the pure layer refuses it.
        """
        return self._offices_registry().get(office)

    def find_office_definition(self, office: Any):
        """One office definition: held first, then the book (M-122).

        The session's held registry answers first; an
        office the session has not taken up is read
        from the shipped book. An office neither
        holds raises KeyError; an unformalised office
        raises ValueError.
        """
        try:
            return self._offices_registry().get(office)
        except KeyError:
            from ..core.offices import load_offices
            return load_offices().get(office)

    def office_handoffs(self, office: Any):
        """Every hand-off contract one office hands out (M-122).

        Read from the held definition when the
        session holds the office, and from the
        shipped book otherwise. Reading registers
        and publishes nothing.
        """
        return self.find_office_definition(office).handoffs

    def office_contract(self, from_office: Any, to_office: Any):
        """The hand-off contract between two offices (M-122).

        Read from the held definition when the
        session holds the from-office, and from the
        shipped book otherwise; no contract between
        the two raises KeyError. Reading registers
        and publishes nothing.
        """
        return self.find_office_definition(from_office).contract_to(to_office)

    def register_office(self, definition: Any) -> dict[str, Any]:
        """Hold one formalised office for the session (M-122).

        The definition is held by the pure registry
        under its office id - a duplicate office
        refuses, and a refusal holds nothing new and
        publishes nothing - and a held office is
        published as its ``office_record``
        session-news record through the checkpoint
        road, so an office taken up is news with its
        shape attached. Returns the held definition,
        its news record, the screen rendered after it
        landed, and the plain explanation.
        """
        from ..core import offices

        registry = self._offices_registry()
        held = registry.register(definition)
        record = offices.office_record(held)
        self._publish_office_record(record)
        return {
            "office": held.to_record(),
            "record": record,
            "screen": offices.format_offices_screen(registry),
            "explanation": offices.PLAIN_EXPLANATION,
        }

    def load_offices_book(self, book: Any = None) -> dict[str, Any]:
        """Hold a whole offices book for the session (M-122).

        With no book named, the shipped book is
        loaded through the pure layer - the six
        offices formalised. A book loaded from a file
        (the pure layer's ``load_offices_file`` road)
        may be passed instead, so an offices file
        formalising fewer offices is held as it
        stands. Every definition is held in file
        order and published as its ``office_record``
        session news, deduped per office id. The pure
        registry refuses a duplicate office - a book
        the session already holds cannot be loaded
        twice. Returns the held definitions, their
        news records, the count, the screen, and the
        explanation.
        """
        from ..core import offices

        registry = self._offices_registry()
        book = book if book is not None else offices.load_offices()
        held = registry.register_book(book)
        records = [offices.office_record(d) for d in held]
        for record in records:
            self._publish_office_record(record)
        return {
            "offices": [d.to_record() for d in held],
            "records": records,
            "count": len(held),
            "screen": offices.format_offices_screen(registry),
            "explanation": offices.PLAIN_EXPLANATION,
        }

    def _publish_office_record(self, record: dict[str, Any]) -> None:
        """Publish one formalised office as session news (M-122).

        The pure layer's ``office_record`` is
        journaled through the same checkpoint road
        every sibling slice uses, when a session is
        attached. Each office is announced at most
        once: the announcement is keyed by the
        record's office id, and every office record
        carries one. A foreign record type is never
        published on this road.
        """
        if record.get("type") != "office":
            return
        announced = getattr(self, "_offices_announced", None)
        if announced is None:
            announced = set()
            self._offices_announced = announced
        office_id = record.get("office")
        if office_id is not None:
            if office_id in announced:
                return
            announced.add(office_id)
        if self._session_store and self.session_id:
            self._checkpoint(record)


    # -- M-123: custom offices --

    def _custom_offices_registry(self):
        """The held custom offices registry (M-123).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds pure-layer custom office definitions
        in the order they were taken up, beside the
        session OfficeRegistry (M-122) and never in
        it: a custom office is a user-defined role,
        not a formalised office. It is created on
        first use, so an agent whose ``__init__``
        never ran still holds exactly one. The
        attribute is named ``_custom_offices_store``,
        never the method's own name (the M-108 lesson).
        """
        registry = getattr(self, "_custom_offices_store", None)
        if registry is None:
            from ..core.custom_offices import CustomOfficeRegistry
            registry = CustomOfficeRegistry()
            self._custom_offices_store = registry
        return registry

    def custom_offices_status(self) -> dict[str, Any]:
        """The custom offices, in plain data (M-123).

        The definitions held this session as plain
        records, the shipped custom book as plain
        records (the roadmap's example custom offices,
        as data), the one screen - rendered from the
        held registry, or from the shipped book when
        nothing is held yet - and the plain
        explanation. A custom office is user-defined,
        not formalised: its records state that
        plainly (``formal`` false, ``custom`` true).
        Reading registers and publishes nothing.
        """
        from ..core import custom_offices

        registry = self._custom_offices_registry()
        held = registry.list_definitions()
        book = custom_offices.load_custom_offices()
        shown = registry if held else book
        return {
            "offices": [d.to_record() for d in held],
            "book": [d.to_record() for d in book.definitions],
            "screen": custom_offices.format_custom_offices_screen(shown),
            "explanation": custom_offices.PLAIN_EXPLANATION,
        }

    def get_custom_office_definition(self, office: Any):
        """The one held custom definition an office names (M-123).

        An office the session does not hold raises
        KeyError, exactly as the pure registry
        answers; a shipped office id raises ValueError,
        as the pure layer refuses it - a custom office
        never names a shipped office.
        """
        return self._custom_offices_registry().get(office)

    def find_custom_office_definition(self, office: Any):
        """One custom office definition: held first, then the book (M-123).

        The session's held registry answers first; an
        office the session has not taken up is read
        from the shipped custom book. An office
        neither holds raises KeyError; a shipped
        office id raises ValueError.
        """
        try:
            return self._custom_offices_registry().get(office)
        except KeyError:
            from ..core.custom_offices import load_custom_offices
            return load_custom_offices().get(office)

    def custom_office_handoffs(self, office: Any):
        """Every hand-off contract one custom office hands out (M-123).

        Read from the held definition when the
        session holds the office, and from the
        shipped book otherwise. Reading registers
        and publishes nothing.
        """
        return self.find_custom_office_definition(office).handoffs

    def custom_office_contract(self, from_office: Any, to_office: Any):
        """The hand-off contract between two offices (M-123).

        The from-office is a custom office; the target
        may be a formalised office or a custom office.
        Read from the held definition when the session
        holds the from-office, and from the shipped
        book otherwise; no contract between the two
        raises KeyError. Reading registers and
        publishes nothing.
        """
        return self.find_custom_office_definition(from_office).contract_to(to_office)

    def register_custom_office(self, definition: Any) -> dict[str, Any]:
        """Hold one custom office for the session (M-123).

        The definition is held by the pure registry
        under its custom office id - a duplicate
        office refuses, a definition naming a shipped
        office refuses, and a refusal holds nothing
        new and publishes nothing - and a held office
        is published as its ``custom_office_record``
        session-news record through the checkpoint
        road, so a custom office taken up is news with
        its shape attached. Returns the held
        definition, its news record, the screen
        rendered after it landed, and the plain
        explanation. Holding a custom office casts no
        member and spawns nothing: a custom office is
        a user-defined role, not a formalised office
        and not a cast member, and no spawn road is
        owed or built for it - spawning stays the
        M-121 crew road's.
        """
        from ..core import custom_offices

        registry = self._custom_offices_registry()
        held = registry.register(definition)
        record = custom_offices.custom_office_record(held)
        self._publish_custom_office_record(record)
        return {
            "office": held.to_record(),
            "record": record,
            "screen": custom_offices.format_custom_offices_screen(registry),
            "explanation": custom_offices.PLAIN_EXPLANATION,
        }

    def load_custom_offices_book(self, book: Any = None) -> dict[str, Any]:
        """Hold a whole custom offices book for the session (M-123).

        With no book named, the shipped book is
        loaded through the pure layer - the roadmap's
        example custom offices. A book loaded from a
        file (the pure layer's
        ``load_custom_offices_file`` road) may be
        passed instead, so a custom offices file
        defining new offices is held as it stands.
        Every definition is held in file order and
        published as its ``custom_office_record``
        session news, deduped per office id. The pure
        registry refuses a duplicate office - a book
        the session already holds cannot be loaded
        twice. Returns the held definitions, their
        news records, the count, the screen, and the
        explanation.
        """
        from ..core import custom_offices

        registry = self._custom_offices_registry()
        book = book if book is not None else custom_offices.load_custom_offices()
        held = registry.register_book(book)
        records = [custom_offices.custom_office_record(d) for d in held]
        for record in records:
            self._publish_custom_office_record(record)
        return {
            "offices": [d.to_record() for d in held],
            "records": records,
            "count": len(held),
            "screen": custom_offices.format_custom_offices_screen(registry),
            "explanation": custom_offices.PLAIN_EXPLANATION,
        }

    def _publish_custom_office_record(self, record: dict[str, Any]) -> None:
        """Publish one custom office as session news (M-123).

        The pure layer's ``custom_office_record`` is
        journaled through the same checkpoint road
        every sibling slice uses, when a session is
        attached. Each office is announced at most
        once: the announcement is keyed by the
        record's office id, and every custom office
        record carries one. A foreign record type is
        never published on this road.
        """
        if record.get("type") != "custom_office":
            return
        announced = getattr(self, "_custom_offices_announced", None)
        if announced is None:
            announced = set()
            self._custom_offices_announced = announced
        office_id = record.get("office")
        if office_id is not None:
            if office_id in announced:
                return
            announced.add(office_id)
        if self._session_store and self.session_id:
            self._checkpoint(record)

    # -- M-124: parallel worktrees --

    def _worktrees_registry(self):
        """The held worktrees registry (M-124).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds pure-layer worktree assignments in
        the order they were taken up, beside the
        session crew registry (M-121) and never in
        it: a worktree assignment is the plan's
        record of who writes in which tree, not a
        cast member. It is created on first use, so
        an agent whose ``__init__`` never ran still
        holds exactly one. The attribute is named
        ``_worktrees_store``, never the method's own
        name (the M-108 lesson).
        """
        registry = getattr(self, "_worktrees_store", None)
        if registry is None:
            from ..core.worktrees import WorktreeRegistry
            registry = WorktreeRegistry()
            self._worktrees_store = registry
        return registry

    def worktrees_status(self) -> dict[str, Any]:
        """The worktrees, in plain data (M-124).

        The assignments held this session as plain
        records, the shipped example plan as plain
        records (the M-121 casting dealt one
        worktree each, as data), the one screen -
        rendered from the held registry, or from
        the shipped example plan when nothing is
        held yet - and the plain explanation.
        Reading registers and publishes nothing,
        runs no git command and creates no
        worktree: this layer holds the plan as
        data only.
        """
        from ..core import worktrees

        registry = self._worktrees_registry()
        held = registry.list_assignments()
        plan = worktrees.load_worktree_plan()
        shown = registry if held else plan
        return {
            "assignments": [a.to_record() for a in held],
            "plan": [a.to_record() for a in plan.assignments],
            "screen": worktrees.format_worktrees_screen(shown),
            "explanation": worktrees.PLAIN_EXPLANATION,
        }

    def get_worktree_assignment(self, member: Any):
        """The one held assignment a member holds (M-124).

        A member the session does not hold raises
        KeyError, exactly as the pure registry
        answers.
        """
        return self._worktrees_registry().by_member(member)

    def find_worktree_assignment(self, member: Any):
        """One assignment: held first, then the example plan (M-124).

        The session's held registry answers first;
        a member the session has not taken up is
        read from the shipped example plan. A
        member neither holds raises KeyError.
        Reading registers and publishes nothing.
        """
        try:
            return self._worktrees_registry().by_member(member)
        except KeyError:
            from ..core.worktrees import load_worktree_plan
            return load_worktree_plan().get(member)

    def worktree_plan(self):
        """The session's worktree plan, as data (M-124).

        When the session holds assignments, the
        plan is those assignments under the
        coordinator the session's loaded plan
        named - the house coordinator word until
        a plan names another - so the merge plan
        is derived from what the session actually
        holds. With nothing held, the shipped
        example plan answers. Reading registers
        and publishes nothing.
        """
        from ..core.worktrees import WorktreePlan, load_worktree_plan

        held = self._worktrees_registry().list_assignments()
        if not held:
            return load_worktree_plan()
        coordinator = getattr(
            self, "_worktrees_coordinator", None) or "coordinator"
        return WorktreePlan(assignments=held, coordinator=coordinator)

    def worktree_merge_plan(self):
        """The coordinator merge plan, in slice order (M-124).

        Derived from the session's plan - the held
        assignments when the session holds any,
        the shipped example plan otherwise - every
        step merged by the coordinator only. The
        plan is derived, never stored, and reading
        it carries out no merge and runs no git:
        merges are carried out by the coordinator
        through the git roads, never by this layer.
        """
        from ..core.worktrees import merge_plan_for

        return merge_plan_for(self.worktree_plan())

    def register_worktree_assignment(self, assignment: Any) -> dict[str, Any]:
        """Hold one worktree assignment for the session (M-124).

        The assignment is held by the pure registry
        under its id or a fresh deterministic one -
        a member, branch or path already held
        refuses (never two writers in one tree),
        and a refusal holds nothing new and
        publishes nothing - and a held assignment
        is published as its ``worktree_record``
        session-news record through the checkpoint
        road, so an assignment taken up is news
        with its shape attached. Returns the held
        assignment, its news record, the screen
        rendered after it landed, and the plain
        explanation. Holding an assignment creates
        no worktree and runs no git command, and
        no spawn road is owed or built for it: the
        registry holds the plan as data, and
        spawning stays the M-121 crew road's.
        """
        from ..core import worktrees

        registry = self._worktrees_registry()
        held = registry.register(assignment)
        record = worktrees.worktree_record(held)
        self._publish_worktree_record(record)
        return {
            "assignment": held.to_record(),
            "record": record,
            "screen": worktrees.format_worktrees_screen(registry),
            "explanation": worktrees.PLAIN_EXPLANATION,
        }

    def load_worktrees_plan(self, plan: Any = None) -> dict[str, Any]:
        """Hold a whole worktree plan for the session (M-124).

        With no plan named, the shipped example
        plan is loaded through the pure layer - the
        M-121 casting dealt one worktree each. A
        plan loaded from a file (the pure layer's
        ``load_worktree_plan_file`` road) may be
        passed instead, so a real wave's plan is
        held as it stands. Every assignment is
        held in file order and published as its
        ``worktree_record`` session news, deduped
        per member, and the plan's coordinator is
        remembered as session state so the merge
        plan is derived under the coordinator the
        plan named. The pure registry refuses a
        member, branch or path already held - a
        plan the session already holds cannot be
        loaded twice. Returns the held assignments,
        their news records, the count, the screen,
        and the explanation. Holding a plan creates
        no worktree and runs no git command.
        """
        from ..core import worktrees

        registry = self._worktrees_registry()
        plan = plan if plan is not None else worktrees.load_worktree_plan()
        held = registry.register_plan(plan)
        self._worktrees_coordinator = plan.coordinator
        records = [worktrees.worktree_record(a) for a in held]
        for record in records:
            self._publish_worktree_record(record)
        return {
            "assignments": [a.to_record() for a in held],
            "records": records,
            "count": len(held),
            "screen": worktrees.format_worktrees_screen(registry),
            "explanation": worktrees.PLAIN_EXPLANATION,
        }

    def _publish_worktree_record(self, record: dict[str, Any]) -> None:
        """Publish one worktree assignment as session news (M-124).

        The pure layer's ``worktree_record`` is
        journaled through the same checkpoint road
        every sibling slice uses, when a session is
        attached. Each member is announced at most
        once: the announcement is keyed by the
        record's member id, and every worktree
        record carries one. A foreign record type
        is never published on this road.
        """
        if record.get("type") != "worktree_assignment":
            return
        announced = getattr(self, "_worktrees_announced", None)
        if announced is None:
            announced = set()
            self._worktrees_announced = announced
        member_id = record.get("member")
        if member_id is not None:
            if member_id in announced:
                return
            announced.add(member_id)
        if self._session_store and self.session_id:
            self._checkpoint(record)
    # -- M-125: task dealing --

    def _task_dealing_registry(self):
        """The held task-dealing registry (M-125).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds pure-layer dealt assignments in
        the order they were dealt, beside the session
        worktree registry (M-124) and never in it: a
        dealt assignment is the dealing's record of
        who takes which slice, not a worktree
        assignment. It is created on first use, so
        an agent whose ``__init__`` never ran still
        holds exactly one. The attribute is named
        ``_task_dealing_store``, never the method's
        own name (the M-108 lesson).
        """
        registry = getattr(self, "_task_dealing_store", None)
        if registry is None:
            from ..core.task_dealing import TaskDealingRegistry
            registry = TaskDealingRegistry()
            self._task_dealing_store = registry
        return registry

    def task_dealing_status(self) -> dict[str, Any]:
        """The task dealing, in plain data (M-125).

        The assignments held this session as plain
        records, the session plan's tasks as plain
        records (the shipped example plan - the next
        ten roadmap slices - until a plan is loaded),
        the one screen - rendered from the held
        registry, or from the shipped example
        dealing when nothing is held yet - and the
        plain explanation. Reading registers and
        publishes nothing, starts no crew and spawns
        nothing: this layer holds the dealing as
        data only. There is no Part VIII board yet;
        the screen is where the dealing is visible.
        """
        from ..core import task_dealing

        registry = self._task_dealing_registry()
        held = registry.list_assignments()
        plan = self.dealing_plan()
        screen = task_dealing.format_dealing_screen(registry) \
            if held else task_dealing.format_dealing_screen()
        return {
            "assignments": [a.to_record() for a in held],
            "plan": [t.to_record() for t in plan.tasks],
            "screen": screen,
            "explanation": task_dealing.PLAIN_EXPLANATION,
        }

    def get_dealt_assignment(self, slice_id: Any):
        """The one held assignment a slice holds (M-125).

        A slice the session does not hold raises
        KeyError, exactly as the pure registry
        answers.
        """
        return self._task_dealing_registry().by_slice(slice_id)

    def find_dealt_assignment(self, slice_id: Any):
        """One dealt assignment: held first, then the example (M-125).

        The session's held registry answers first;
        a slice the session has not dealt is read
        from the shipped example dealing. A slice
        neither holds raises KeyError. Reading
        registers and publishes nothing.
        """
        try:
            return self._task_dealing_registry().by_slice(slice_id)
        except KeyError:
            from ..core.crew_members import load_casting
            from ..core.task_dealing import (
                deal_tasks, load_dealing_plan)
            dealing = deal_tasks(
                load_dealing_plan(), load_casting().members)
            return dealing.get(slice_id)

    def find_dealt_assignments(self, member: Any):
        """Every assignment one member holds (M-125).

        The session's held registry answers when the
        session holds any dealing; otherwise the
        shipped example dealing answers. A member
        holding nothing in the answering dealing
        raises KeyError naming the member. Reading
        registers and publishes nothing.
        """
        from ..core.crew_members import (
            load_casting, normalize_member_id)
        from ..core.task_dealing import (
            deal_tasks, load_dealing_plan)

        wanted = normalize_member_id(member)
        registry = self._task_dealing_registry()
        if registry.list_assignments():
            found = registry.by_member(wanted)
        else:
            dealing = deal_tasks(
                load_dealing_plan(), load_casting().members)
            found = tuple(
                a for a in dealing.assignments if a.member == wanted)
        if not found:
            raise KeyError(
                f"no assignment holds the member: {wanted!r}")
        return found

    def dealing_plan(self):
        """The session's dealing plan, as data (M-125).

        The plan the session loaded through
        :meth:`deal_task_dealing_plan`, or the
        shipped example plan until one is loaded.
        Reading registers and publishes nothing.
        """
        from ..core.task_dealing import load_dealing_plan

        plan = getattr(self, "_task_dealing_plan", None)
        if plan is None:
            return load_dealing_plan()
        return plan

    def dealing_loads(self) -> dict[str, Any]:
        """The whole crew's loads from what is held (M-125).

        Every shipped member's count of dealt slices
        held this session - the current load the
        next dealing is dealt under - read through
        the pure layer's member_loads against the
        shipped casting. Members holding nothing
        read 0. Reading registers and publishes
        nothing.
        """
        from ..core.crew_members import load_casting
        from ..core.task_dealing import member_loads

        return member_loads(
            load_casting().members, self._task_dealing_registry())

    def register_dealt_assignment(self, assignment: Any) -> dict[str, Any]:
        """Hold one dealt assignment for the session (M-125).

        The assignment is held by the pure registry
        under its id or a fresh deterministic one -
        a slice already dealt refuses (a held slice
        moves only by an explicit re-deal), and a
        refusal holds nothing new and publishes
        nothing - and a held assignment is published
        as its ``dealing_record`` session-news record
        through the checkpoint road, so a slice dealt
        is news with its shape attached. Returns the
        held assignment, its news record, the screen
        rendered after it landed, and the plain
        explanation. Holding an assignment starts no
        crew and spawns nothing: the registry holds
        the dealing as data.
        """
        from ..core import task_dealing

        registry = self._task_dealing_registry()
        held = registry.register(assignment)
        record = task_dealing.dealing_record(held)
        self._publish_dealing_record(record)
        return {
            "assignment": held.to_record(),
            "record": record,
            "screen": task_dealing.format_dealing_screen(registry),
            "explanation": task_dealing.PLAIN_EXPLANATION,
        }

    def deal_task_dealing_plan(self, plan: Any = None) -> dict[str, Any]:
        """Deal a whole plan to the crew for the session (M-125).

        With no plan named, the shipped example plan
        is dealt through the pure layer - the next
        ten roadmap slices, each to the member whose
        office its work fits. A plan loaded from a
        file (the pure layer's
        ``load_dealing_plan_file`` road) may be
        passed instead, so a real plan is dealt as
        it stands. The dealing is derived by the
        pure ``deal_tasks`` judge under the loads
        the session already holds, every assignment
        is held in plan order and published as its
        ``dealing_record`` session news, deduped per
        slice and member, and the plan is remembered
        as the session's plan. The pure registry
        refuses a slice already dealt - a plan the
        session already dealt cannot be dealt twice;
        the human re-deals a slice explicitly.
        Returns the held assignments, their news
        records, the count, the screen, and the
        explanation. Dealing starts no crew and
        spawns nothing.
        """
        from ..core import task_dealing
        from ..core.crew_members import load_casting

        registry = self._task_dealing_registry()
        plan = plan if plan is not None \
            else task_dealing.load_dealing_plan()
        members = load_casting().members
        loads = {
            member.member_id: len(registry.by_member(member.member_id))
            for member in members}
        dealing = task_dealing.deal_tasks(plan, members, loads=loads)
        held = registry.register_dealing(dealing)
        self._task_dealing_plan = plan
        records = [task_dealing.dealing_record(a) for a in held]
        for record in records:
            self._publish_dealing_record(record)
        return {
            "assignments": [a.to_record() for a in held],
            "records": records,
            "count": len(held),
            "screen": task_dealing.format_dealing_screen(registry),
            "explanation": task_dealing.PLAIN_EXPLANATION,
        }

    def redeal_task_assignment(self, slice_id: Any,
                               member: Any) -> dict[str, Any]:
        """Re-deal one held slice to another member (M-125).

        The human's re-deal, carried out: the named
        slice, held this session, moves to the named
        member of the shipped casting, carrying that
        member's cast office, and the held loads are
        recomputed by the pure registry. A member
        the casting does not hold refuses, and a
        slice the session does not hold raises
        KeyError, exactly as the pure registry
        answers. The moved assignment is published
        as its ``dealing_record`` session news - a
        re-deal to a new member is news again; the
        announcement is deduped per slice and
        member. Returns the moved assignment, its
        news record, the screen rendered after it
        landed, and the plain explanation.
        """
        from ..core import task_dealing
        from ..core.crew_members import load_casting, normalize_member_id

        wanted = normalize_member_id(member)
        offices = {
            member.member_id: member.office
            for member in load_casting().members}
        if wanted not in offices:
            raise ValueError(
                f"the member {wanted!r} is not in the shipped "
                f"casting; a slice is re-dealt to a crew member")
        registry = self._task_dealing_registry()
        moved = registry.redeal(slice_id, wanted, offices[wanted])
        record = task_dealing.dealing_record(moved)
        self._publish_dealing_record(record)
        return {
            "assignment": moved.to_record(),
            "record": record,
            "screen": task_dealing.format_dealing_screen(registry),
            "explanation": task_dealing.PLAIN_EXPLANATION,
        }

    def _publish_dealing_record(self, record: dict[str, Any]) -> None:
        """Publish one dealt assignment as session news (M-125).

        The pure layer's ``dealing_record`` is
        journaled through the same checkpoint road
        every sibling slice uses, when a session is
        attached. Each (slice, member) pair is
        announced at most once: the announcement is
        keyed by the record's slice and member, so a
        slice re-dealt to a new member is announced
        again for that member, and every dealing
        record carries both. A foreign record type
        is never published on this road.
        """
        if record.get("type") != "task_dealing":
            return
        announced = getattr(self, "_task_dealing_announced", None)
        if announced is None:
            announced = set()
            self._task_dealing_announced = announced
        key = (record.get("slice_id"), record.get("member"))
        if key in announced:
            return
        announced.add(key)
        if self._session_store and self.session_id:
            self._checkpoint(record)


    # -- M-126: crew comms --

    def _crew_comms_registry(self):
        """The held crew-comms registry (M-126).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds pure-layer hand-offs in the order
        they were handed, beside the session dealing
        registry (M-125) and never in it: a hand-off
        is the crew's traffic, not a dealt assignment.
        It is created on first use, so an agent whose
        ``__init__`` never ran still holds exactly
        one. The attribute is named
        ``_crew_comms_store``, never the method's own
        name (the M-108 lesson).
        """
        registry = getattr(self, "_crew_comms_store", None)
        if registry is None:
            from ..core.crew_comms import CrewCommsRegistry
            registry = CrewCommsRegistry()
            self._crew_comms_store = registry
        return registry

    def crew_comms_status(self) -> dict[str, Any]:
        """The crew comms, in plain data (M-126).

        The hand-offs held this session as plain
        records, the session ledger's hand-offs as
        plain records (the shipped example ledger -
        six hand-offs among the M-121 casting - until
        a ledger is recorded), the one batch of the
        questions waiting for the human as its batch
        record, the one screen - rendered from the
        held registry, or from the shipped example
        ledger when nothing is held yet - and the
        plain explanation. Reading registers and
        publishes nothing, spawns no crew and
        delivers no message: this layer holds the
        hand-offs as data only. There is no Part
        VIII board yet; the screen is where the
        hand-offs and the batch are visible.
        """
        from ..core import crew_comms

        registry = self._crew_comms_registry()
        held = registry.list_handoffs()
        ledger = self.comms_ledger()
        screen = crew_comms.format_comms_screen(registry) \
            if held else crew_comms.format_comms_screen()
        return {
            "handoffs": [h.to_record() for h in held],
            "ledger": [h.to_record() for h in ledger.handoffs],
            "batch": crew_comms.batch_record(self.human_question_batch()),
            "screen": screen,
            "explanation": crew_comms.PLAIN_EXPLANATION,
        }

    def get_handoff(self, handoff_id: Any):
        """The one held hand-off an id names (M-126).

        A hand-off the session does not hold raises
        KeyError, exactly as the pure registry
        answers.
        """
        return self._crew_comms_registry().get(handoff_id)

    def find_handoffs(self, member: Any):
        """Every hand-off one member sent or received (M-126).

        The session's held registry answers when the
        session holds any hand-off; otherwise the
        shipped example ledger answers. The human
        reads as a recipient: finding the human's
        hand-offs finds every hand-off addressed to
        the human. A member holding nothing in the
        answering set raises KeyError. Reading
        registers and publishes nothing.
        """
        from ..core.crew_comms import (
            load_comms_ledger, normalize_recipient)

        wanted = normalize_recipient(member)
        registry = self._crew_comms_registry()
        if registry.list_handoffs():
            found = registry.for_member(wanted)
        else:
            found = tuple(
                h for h in load_comms_ledger().handoffs
                if h.sender == wanted or h.recipient == wanted)
        if not found:
            raise KeyError(
                f"no hand-off holds the member: {wanted!r}")
        return found

    def comms_ledger(self):
        """The session's comms ledger, as data (M-126).

        The ledger the session recorded through
        :meth:`record_comms_ledger`, or the shipped
        example ledger until one is recorded.
        Reading registers and publishes nothing.
        """
        from ..core.crew_comms import load_comms_ledger

        ledger = getattr(self, "_crew_comms_ledger", None)
        if ledger is None:
            return load_comms_ledger()
        return ledger

    def human_question_batch(self):
        """The one batch of questions waiting for the human (M-126).

        Derived by the pure layer from what the
        session holds - the held registry when the
        session holds any hand-off, otherwise the
        shipped example ledger - every waiting
        question in hand-off order, each with its
        full context. Reading registers, publishes
        and asks nothing: asking is
        :meth:`ask_batched_human_questions`' road.
        """
        from ..core.crew_comms import batch_human_questions

        registry = self._crew_comms_registry()
        if registry.list_handoffs():
            return registry.batch()
        return batch_human_questions(self.comms_ledger())

    def register_handoff(self, handoff: Any) -> dict[str, Any]:
        """Hold one hand-off for the session (M-126).

        The hand-off is held by the pure registry
        under its id or a fresh deterministic one -
        a supplied id already held refuses, and a
        refusal holds nothing new and publishes
        nothing - and a held hand-off is published
        as its ``handoff_record`` session-news record
        through the checkpoint road, so a hand-off
        made is news with its shape attached. Returns
        the held hand-off, its news record, the
        screen rendered after it landed, and the
        plain explanation. Holding a hand-off spawns
        no crew and delivers no message: the registry
        holds the hand-off as data.
        """
        from ..core import crew_comms

        registry = self._crew_comms_registry()
        held = registry.register(handoff)
        record = crew_comms.handoff_record(held)
        self._publish_comms_record(record)
        return {
            "handoff": held.to_record(),
            "record": record,
            "screen": crew_comms.format_comms_screen(registry),
            "explanation": crew_comms.PLAIN_EXPLANATION,
        }

    def record_comms_ledger(self, ledger: Any = None) -> dict[str, Any]:
        """Record a whole ledger of hand-offs for the session (M-126).

        With no ledger named, the shipped example
        ledger is recorded through the pure layer -
        six hand-offs among the M-121 casting. A
        ledger loaded from a file (the pure layer's
        ``load_comms_ledger_file`` road) may be
        passed instead, so a real ledger is recorded
        as it stands. Every hand-off is held in
        ledger order and published as its
        ``handoff_record`` session news, deduped per
        hand-off id, the ledger is remembered as the
        session's ledger, and the same ledger
        recorded twice refuses - a ledger is recorded
        once, never duplicated into the session.
        Returns the held hand-offs, their news
        records, the count, the screen, and the
        explanation. Recording spawns no crew and
        delivers no message.
        """
        from ..core import crew_comms

        ledger = ledger if ledger is not None \
            else crew_comms.load_comms_ledger()
        fingerprint = tuple(
            (h.sender, h.recipient, h.kind, h.slice_id,
             h.title, h.body) for h in ledger.handoffs)
        recorded = getattr(self, "_crew_comms_recorded", None)
        if recorded is None:
            recorded = set()
            self._crew_comms_recorded = recorded
        if fingerprint in recorded:
            raise ValueError(
                "this comms ledger is already recorded for "
                "the session; a ledger is recorded once")
        registry = self._crew_comms_registry()
        held = registry.register_ledger(ledger)
        recorded.add(fingerprint)
        self._crew_comms_ledger = ledger
        records = [crew_comms.handoff_record(h) for h in held]
        for record in records:
            self._publish_comms_record(record)
        return {
            "handoffs": [h.to_record() for h in held],
            "records": records,
            "count": len(held),
            "screen": crew_comms.format_comms_screen(registry),
            "explanation": crew_comms.PLAIN_EXPLANATION,
        }

    def ask_batched_human_questions(self) -> dict[str, Any]:
        """Ask the human the waiting questions, once, together (M-126).

        The batching rule carried out: the batch is
        derived from what the session holds by
        :meth:`human_question_batch` - every waiting
        question, in hand-off order, each with its
        sender, slice, title and body - and published
        as ONE ``human_question_batch`` session-news
        record holding them all, never one record per
        question. The announcement is deduped per
        batch: asking again while the same questions
        wait publishes nothing new, and a batch grown
        by a newly held question is a new ask. With
        no waiting question nothing is published and
        the count is 0. Returns the batch, its news
        record, the count, the batched-ask screen,
        and the plain explanation.
        """
        from ..core import crew_comms

        batch = self.human_question_batch()
        record = crew_comms.batch_record(batch)
        if batch.questions:
            self._publish_batch_record(record)
        return {
            "batch": batch.to_record(),
            "record": record,
            "count": len(batch.questions),
            "screen": crew_comms.format_human_batch(batch),
            "explanation": crew_comms.PLAIN_EXPLANATION,
        }

    def _publish_comms_record(self, record: dict[str, Any]) -> None:
        """Publish one hand-off as session news (M-126).

        The pure layer's ``handoff_record`` is
        journaled through the same checkpoint road
        every sibling slice uses, when a session is
        attached. Each hand-off id is announced at
        most once. A foreign record type is never
        published on this road.
        """
        if record.get("type") != "crew_handoff":
            return
        announced = getattr(self, "_crew_comms_announced", None)
        if announced is None:
            announced = set()
            self._crew_comms_announced = announced
        key = record.get("handoff_id")
        if key in announced:
            return
        announced.add(key)
        if self._session_store and self.session_id:
            self._checkpoint(record)

    def _publish_batch_record(self, record: dict[str, Any]) -> None:
        """Publish one batched ask as session news (M-126).

        The pure layer's ``batch_record`` is journaled
        through the same checkpoint road, when a
        session is attached - ONE event holding every
        waiting question, so the human is asked once.
        Each batch is announced at most once: the
        announcement is keyed by the batch's questions
        (sender, slice, title), so a batch grown by a
        newly held question announces again as the new
        batch it is. A foreign record type is never
        published on this road.
        """
        if record.get("type") != "human_question_batch":
            return
        announced = getattr(self, "_crew_comms_batch_announced", None)
        if announced is None:
            announced = set()
            self._crew_comms_batch_announced = announced
        key = tuple(
            (q.get("sender"), q.get("slice_id"), q.get("title"))
            for q in record.get("questions", []))
        if key in announced:
            return
        announced.add(key)
        if self._session_store and self.session_id:
            self._checkpoint(record)

    # -- M-127: cycle and deadlock watch --

    def _deadlock_watch_registry(self):
        """The held deadlock-watch registry (M-127).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds pure-layer delegations and claims in
        the order they were given, beside the session
        comms registry (M-126) and never in it: the
        watch's evidence is the coordinator's, not the
        crew's traffic. It is created on first use, so
        an agent whose ``__init__`` never ran still
        holds exactly one. The attribute is named
        ``_deadlock_watch_store``, never the method's
        own name (the M-108 lesson).
        """
        registry = getattr(self, "_deadlock_watch_store", None)
        if registry is None:
            from ..core.deadlock_watch import DeadlockWatchRegistry
            registry = DeadlockWatchRegistry()
            self._deadlock_watch_store = registry
        return registry

    def deadlock_status(self) -> dict[str, Any]:
        """The deadlock watch, in plain data (M-127).

        The delegations and claims held this session
        as plain records, the session watch's evidence
        as plain records (the shipped example watch -
        five delegations and five claims among the
        M-121 casting, kept by the guardian - until a
        watch is recorded), the derived report as its
        one report record, the one screen - rendered
        from the held registry, or from the shipped
        example watch when nothing is held yet - and
        the plain explanation. Reading registers and
        publishes nothing, spawns no crew, stops no
        member and runs no git: this layer holds the
        watch as data only. There is no Part VIII
        board yet; the screen is where the findings
        are visible.
        """
        from ..core import deadlock_watch

        registry = self._deadlock_watch_registry()
        held_delegations = registry.list_delegations()
        held_claims = registry.list_claims()
        watch = self.deadlock_watch()
        screen = deadlock_watch.format_deadlock_screen(registry) \
            if held_delegations or held_claims \
            else deadlock_watch.format_deadlock_screen()
        return {
            "delegations": [d.to_record() for d in held_delegations],
            "claims": [c.to_record() for c in held_claims],
            "watch": {
                "keeper": watch.keeper,
                "delegations": [
                    d.to_record() for d in watch.delegations],
                "claims": [c.to_record() for c in watch.claims],
            },
            "report": deadlock_watch.report_record(
                self.deadlock_report()),
            "screen": screen,
            "explanation": deadlock_watch.PLAIN_EXPLANATION,
        }

    def get_delegation(self, delegation_id: Any):
        """The one held delegation an id names (M-127).

        A delegation the session does not hold raises
        KeyError, exactly as the pure registry answers.
        """
        return self._deadlock_watch_registry().get_delegation(
            delegation_id)

    def get_claim(self, claim_id: Any):
        """The one held claim an id names (M-127).

        A claim the session does not hold raises
        KeyError, exactly as the pure registry answers.
        """
        return self._deadlock_watch_registry().get_claim(claim_id)

    def find_findings(self, member: Any):
        """Every finding one member is held in (M-127).

        The session's held registry answers when the
        session holds any evidence; otherwise the
        shipped example watch answers. A member held
        in no finding in the answering set raises
        KeyError. Reading registers and publishes
        nothing.
        """
        from ..core.crew_members import normalize_member_id
        from ..core.deadlock_watch import load_deadlock_watch

        wanted = normalize_member_id(member)
        registry = self._deadlock_watch_registry()
        if registry.list_delegations() or registry.list_claims():
            found = registry.for_member(wanted)
        else:
            found = load_deadlock_watch().report().for_member(wanted)
        if not found:
            raise KeyError(
                f"no finding holds the member: {wanted!r}")
        return found

    def deadlock_watch(self):
        """The session's deadlock watch, as data (M-127).

        The watch the session recorded through
        :meth:`record_deadlock_watch`, or the shipped
        example watch until one is recorded. Reading
        registers and publishes nothing.
        """
        from ..core.deadlock_watch import load_deadlock_watch

        watch = getattr(self, "_deadlock_watch_held", None)
        if watch is None:
            return load_deadlock_watch()
        return watch

    def deadlock_report(self):
        """The report the watch's evidence yields (M-127).

        Derived by the pure layer from what the
        session holds - the held registry when the
        session holds any evidence, otherwise the
        shipped example watch - every hazard the
        evidence holds, in detection order: delegation
        cycles, then merge conflicts, then duplicated
        work. Reading registers and publishes nothing:
        publishing is :meth:`report_deadlock`' road.
        """
        from ..core.deadlock_watch import load_deadlock_watch

        registry = self._deadlock_watch_registry()
        if registry.list_delegations() or registry.list_claims():
            return registry.report()
        return load_deadlock_watch().report()

    def register_delegation(self, delegation: Any) -> dict[str, Any]:
        """Hold one delegation for the session (M-127).

        The delegation is held by the pure registry
        under its id or a fresh deterministic one - a
        supplied id already held refuses, and a
        refusal holds nothing new and publishes
        nothing - and a held delegation is published
        as its ``delegation_record`` session-news
        record through the checkpoint road, so
        evidence given is news with its shape
        attached. Returns the held delegation, its
        news record, the screen rendered after it
        landed, and the plain explanation. Holding a
        delegation spawns no crew and stops no
        member: the registry holds the evidence as
        data.
        """
        from ..core import deadlock_watch

        registry = self._deadlock_watch_registry()
        held = registry.register_delegation(delegation)
        record = deadlock_watch.delegation_record(held)
        self._publish_deadlock_record(record)
        return {
            "delegation": held.to_record(),
            "record": record,
            "screen": deadlock_watch.format_deadlock_screen(registry),
            "explanation": deadlock_watch.PLAIN_EXPLANATION,
        }

    def register_claim(self, claim: Any) -> dict[str, Any]:
        """Hold one claim for the session (M-127).

        The claim is held by the pure registry under
        its id or a fresh deterministic one - a
        supplied id already held refuses, and a
        refusal holds nothing new and publishes
        nothing - and a held claim is published as
        its ``claim_record`` session-news record
        through the checkpoint road, so evidence given
        is news with its shape attached. Returns the
        held claim, its news record, the screen
        rendered after it landed, and the plain
        explanation. Holding a claim spawns no crew,
        stops no member and runs no git: the registry
        holds the evidence as data.
        """
        from ..core import deadlock_watch

        registry = self._deadlock_watch_registry()
        held = registry.register_claim(claim)
        record = deadlock_watch.claim_record(held)
        self._publish_deadlock_record(record)
        return {
            "claim": held.to_record(),
            "record": record,
            "screen": deadlock_watch.format_deadlock_screen(registry),
            "explanation": deadlock_watch.PLAIN_EXPLANATION,
        }

    def record_deadlock_watch(self, watch: Any = None) -> dict[str, Any]:
        """Record a whole watch of evidence for the session (M-127).

        With no watch named, the shipped example
        watch is recorded through the pure layer -
        five delegations and five claims among the
        M-121 casting, kept by the guardian. A watch
        loaded from a file (the pure layer's
        ``load_deadlock_watch_file`` road) may be
        passed instead, so a real watch is recorded as
        it stands. Every delegation and claim is held
        in watch order and published as its
        ``delegation_record`` / ``claim_record``
        session news, deduped per evidence id, the
        watch is remembered as the session's watch,
        and the same watch recorded twice refuses - a
        watch is recorded once, never duplicated into
        the session. Returns the held delegations, the
        held claims, their news records, the count of
        evidence held, the screen, and the
        explanation. Recording spawns no crew, stops
        no member and runs no git.
        """
        from ..core import deadlock_watch

        watch = watch if watch is not None \
            else deadlock_watch.load_deadlock_watch()
        fingerprint = (
            tuple((d.delegator, d.delegatee, d.slice_id)
                  for d in watch.delegations),
            tuple((c.member, c.slice_id, c.path)
                  for c in watch.claims))
        recorded = getattr(self, "_deadlock_watch_recorded", None)
        if recorded is None:
            recorded = set()
            self._deadlock_watch_recorded = recorded
        if fingerprint in recorded:
            raise ValueError(
                "this deadlock watch is already recorded for "
                "the session; a watch is recorded once")
        registry = self._deadlock_watch_registry()
        delegations, claims = registry.register_watch(watch)
        recorded.add(fingerprint)
        self._deadlock_watch_held = watch
        records = [
            deadlock_watch.delegation_record(d) for d in delegations]
        records += [
            deadlock_watch.claim_record(c) for c in claims]
        for record in records:
            self._publish_deadlock_record(record)
        return {
            "delegations": [d.to_record() for d in delegations],
            "claims": [c.to_record() for c in claims],
            "records": records,
            "count": len(delegations) + len(claims),
            "screen": deadlock_watch.format_deadlock_screen(registry),
            "explanation": deadlock_watch.PLAIN_EXPLANATION,
        }

    def report_deadlock(self) -> dict[str, Any]:
        """Report the watch's findings to the coordinator (M-127).

        The report is derived from what the session
        holds by :meth:`deadlock_report` - every
        hazard the evidence holds, in detection
        order - and published as session news: each
        finding as its ``finding_record``, then the
        report itself as ONE ``report_record`` session
        event holding every finding, never one report
        per finding. The announcements are deduped:
        reporting again while the same evidence is
        held publishes nothing new, and a report grown
        by newly held evidence announces as the new
        report it is. Returns the report, its news
        record, the count of findings, the findings
        screen, and the plain explanation. Reporting
        spawns no crew, stops no member and runs no
        git: the coordinator acts on the findings
        through later roads.
        """
        from ..core import deadlock_watch

        report = self.deadlock_report()
        for finding in report.findings:
            self._publish_finding_record(
                deadlock_watch.finding_record(finding))
        record = deadlock_watch.report_record(report)
        self._publish_report_record(record)
        return {
            "report": report.to_record(),
            "record": record,
            "count": len(report.findings),
            "screen": deadlock_watch.format_findings(report),
            "explanation": deadlock_watch.PLAIN_EXPLANATION,
        }

    def _publish_deadlock_record(self, record: dict[str, Any]) -> None:
        """Publish one piece of watch evidence as session news (M-127).

        The pure layer's ``delegation_record`` and
        ``claim_record`` are journaled through the
        same checkpoint road every sibling slice
        uses, when a session is attached. Each piece
        of evidence is announced at most once, under
        its own id. A foreign record type is never
        published on this road.
        """
        if record.get("type") == "crew_delegation":
            key = ("crew_delegation", record.get("delegation_id"))
        elif record.get("type") == "crew_claim":
            key = ("crew_claim", record.get("claim_id"))
        else:
            return
        announced = getattr(self, "_deadlock_announced", None)
        if announced is None:
            announced = set()
            self._deadlock_announced = announced
        if key in announced:
            return
        announced.add(key)
        if self._session_store and self.session_id:
            self._checkpoint(record)

    def _publish_finding_record(self, record: dict[str, Any]) -> None:
        """Publish one finding as session news (M-127).

        The pure layer's ``finding_record`` is
        journaled through the same checkpoint road,
        when a session is attached. Each finding is
        announced at most once: the announcement is
        keyed by the finding's whole shape (kind,
        members, slices, paths, title), so the same
        hazard derived again from the same evidence
        is not news twice. A foreign record type is
        never published on this road.
        """
        if record.get("type") != "deadlock_finding":
            return
        announced = getattr(self, "_deadlock_finding_announced", None)
        if announced is None:
            announced = set()
            self._deadlock_finding_announced = announced
        key = (
            record.get("kind"), tuple(record.get("members", [])),
            tuple(record.get("slice_ids", [])),
            tuple(record.get("paths", [])), record.get("title"))
        if key in announced:
            return
        announced.add(key)
        if self._session_store and self.session_id:
            self._checkpoint(record)

    def _publish_report_record(self, record: dict[str, Any]) -> None:
        """Publish one watch report as session news (M-127).

        The pure layer's ``report_record`` is
        journaled through the same checkpoint road,
        when a session is attached - ONE event holding
        every finding, so the coordinator is told
        once. Each report is announced at most once:
        the announcement is keyed by the report's
        findings, so a report grown by newly held
        evidence announces again as the new report it
        is. A foreign record type is never published
        on this road.
        """
        if record.get("type") != "deadlock_report":
            return
        announced = getattr(self, "_deadlock_report_announced", None)
        if announced is None:
            announced = set()
            self._deadlock_report_announced = announced
        key = tuple(
            (f.get("kind"), tuple(f.get("members", [])),
             tuple(f.get("slice_ids", [])),
             tuple(f.get("paths", [])), f.get("title"))
            for f in record.get("findings", []))
        if key in announced:
            return
        announced.add(key)
        if self._session_store and self.session_id:
            self._checkpoint(record)

    # -- M-128: merge discipline --

    def _merge_discipline_registry(self):
        """The held merge-discipline registry (M-128).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds pure-layer steps and recorded merges
        in the order they were given, beside the
        session deadlock-watch registry (M-127) and
        never in it: the merging evidence is the
        coordinator's, held under the discipline this
        slice names. It is created on first use, so an
        agent whose ``__init__`` never ran still holds
        exactly one. The attribute is named
        ``_merge_discipline_store``, never the
        method's own name (the M-108 lesson).
        """
        registry = getattr(self, "_merge_discipline_store", None)
        if registry is None:
            from ..core.merge_discipline import (
                MergeDisciplineRegistry,
            )
            registry = MergeDisciplineRegistry()
            self._merge_discipline_store = registry
        return registry

    def merge_status(self) -> dict[str, Any]:
        """The merge discipline, in plain data (M-128).

        The steps and recorded merges held this
        session as plain records, the session plan's
        evidence as plain records (the shipped
        example plan - seven steps and five merges
        among the M-121 casting, kept by the
        forge_worker - until a plan is recorded), the
        derived report as its one report record, the
        one screen - rendered from the held registry,
        or from the shipped example plan when nothing
        is held yet - and the plain explanation.
        Reading registers and publishes nothing,
        executes no git, performs no merge and spawns
        or stops no crew: this layer holds the
        merging as data only. There is no Part VIII
        board yet; the screen is where the verdicts
        are visible.
        """
        from ..core import merge_discipline

        registry = self._merge_discipline_registry()
        held_steps = registry.list_steps()
        held_attempts = registry.list_attempts()
        plan = self.merge_discipline()
        screen = merge_discipline.format_merge_screen(registry) \
            if held_steps or held_attempts \
            else merge_discipline.format_merge_screen()
        return {
            "steps": [s.to_record() for s in held_steps],
            "attempts": [a.to_record() for a in held_attempts],
            "plan": {
                "keeper": plan.keeper,
                "steps": [s.to_record() for s in plan.steps],
                "merges": [m.to_record() for m in plan.merges],
            },
            "report": merge_discipline.report_record(
                self.merge_report()),
            "screen": screen,
            "explanation": merge_discipline.PLAIN_EXPLANATION,
        }

    def get_merge_step(self, step_id: Any):
        """The one held step an id names (M-128).

        A step the session does not hold raises
        KeyError, exactly as the pure registry answers.
        """
        return self._merge_discipline_registry().get_step(step_id)

    def get_merge_attempt(self, attempt_id: Any):
        """The one held recorded merge an id names (M-128).

        A merge the session does not hold raises
        KeyError, exactly as the pure registry answers.
        """
        return self._merge_discipline_registry().get_attempt(
            attempt_id)

    def find_verdicts(self, member: Any):
        """Every verdict on one member's line (M-128).

        The session's held registry answers when the
        session holds any evidence; otherwise the
        shipped example plan answers. A member held
        in no verdict in the answering set raises
        KeyError. Reading registers and publishes
        nothing.
        """
        from ..core.crew_members import normalize_member_id
        from ..core.merge_discipline import load_merge_discipline

        wanted = normalize_member_id(member)
        registry = self._merge_discipline_registry()
        if registry.list_steps() or registry.list_attempts():
            found = registry.for_member(wanted)
        else:
            found = load_merge_discipline().report().for_member(wanted)
        if not found:
            raise KeyError(
                f"no verdict stands on the member's line: {wanted!r}")
        return found

    def merge_discipline(self):
        """The session's merge plan and ledger, as data (M-128).

        The plan the session recorded through
        :meth:`record_merge_discipline`, or the
        shipped example plan until one is recorded.
        Reading registers and publishes nothing.
        """
        from ..core.merge_discipline import load_merge_discipline

        plan = getattr(self, "_merge_discipline_held", None)
        if plan is None:
            return load_merge_discipline()
        return plan

    def merge_report(self):
        """The report the plan's evidence yields (M-128).

        Derived by the pure layer from what the
        session holds - the held registry when the
        session holds any evidence, otherwise the
        shipped example plan - every verdict the
        evidence holds, in judgement order:
        out-of-order verdicts, then missing-gate
        verdicts, then line-stopped verdicts, with
        every line's state beside them. Reading
        registers and publishes nothing: publishing
        is :meth:`report_merge`' road.
        """
        from ..core.merge_discipline import load_merge_discipline

        registry = self._merge_discipline_registry()
        if registry.list_steps() or registry.list_attempts():
            return registry.report()
        return load_merge_discipline().report()

    def register_merge_step(self, step: Any) -> dict[str, Any]:
        """Hold one merge step for the session (M-128).

        The step is held by the pure registry under
        its id or a fresh deterministic one - a
        supplied id already held refuses, a line
        planning one slice twice refuses, and a
        refusal holds nothing new and publishes
        nothing - and a held step is published as its
        ``step_record`` session-news record through
        the checkpoint road, so evidence given is
        news with its shape attached. Returns the held
        step, its news record, the screen rendered
        after it landed, and the plain explanation.
        Holding a step executes no git and performs no
        merge: the registry holds the evidence as data.
        """
        from ..core import merge_discipline

        registry = self._merge_discipline_registry()
        held = registry.register_step(step)
        record = merge_discipline.step_record(held)
        self._publish_merge_record(record)
        return {
            "step": held.to_record(),
            "record": record,
            "screen": merge_discipline.format_merge_screen(registry),
            "explanation": merge_discipline.PLAIN_EXPLANATION,
        }

    def register_merge_attempt(self, attempt: Any) -> dict[str, Any]:
        """Hold one recorded merge for the session (M-128).

        The merge is held by the pure registry under
        its id or a fresh deterministic one - a
        supplied id already held refuses, and a
        refusal holds nothing new and publishes
        nothing - and a held merge is published as
        its ``attempt_record`` session-news record
        through the checkpoint road, so evidence given
        is news with its shape attached. Returns the
        held merge, its news record, the screen
        rendered after it landed, and the plain
        explanation. Holding a merge executes no git
        and performs no merge itself: the registry
        holds the evidence as data.
        """
        from ..core import merge_discipline

        registry = self._merge_discipline_registry()
        held = registry.register_attempt(attempt)
        record = merge_discipline.attempt_record(held)
        self._publish_merge_record(record)
        return {
            "attempt": held.to_record(),
            "record": record,
            "screen": merge_discipline.format_merge_screen(registry),
            "explanation": merge_discipline.PLAIN_EXPLANATION,
        }

    def record_merge_discipline(
            self, plan: Any = None) -> dict[str, Any]:
        """Record a whole plan and ledger for the session (M-128).

        With no plan named, the shipped example plan
        is recorded through the pure layer - seven
        steps and five merges among the M-121 casting,
        kept by the forge_worker. A plan loaded from a
        file (the pure layer's
        ``load_merge_discipline_file`` road) may be
        passed instead, so a real plan is recorded as
        it stands. Every step and merge is held in
        plan order and published as its
        ``step_record`` / ``attempt_record`` session
        news, deduped per evidence id, the plan is
        remembered as the session's plan, and the same
        plan recorded twice refuses - a plan is
        recorded once, never duplicated into the
        session. Returns the held steps, the held
        merges, their news records, the count of
        evidence held, the screen, and the
        explanation. Recording executes no git,
        performs no merge and spawns or stops no crew.
        """
        from ..core import merge_discipline

        plan = plan if plan is not None \
            else merge_discipline.load_merge_discipline()
        fingerprint = (
            tuple((s.member, s.slice_id, s.branch)
                  for s in plan.steps),
            tuple((m.member, m.slice_id, m.branch, m.gate,
                    m.outcome) for m in plan.merges))
        recorded = getattr(self, "_merge_discipline_recorded", None)
        if recorded is None:
            recorded = set()
            self._merge_discipline_recorded = recorded
        if fingerprint in recorded:
            raise ValueError(
                "this merge plan is already recorded for "
                "the session; a plan is recorded once")
        registry = self._merge_discipline_registry()
        steps, attempts = registry.register_plan(plan)
        recorded.add(fingerprint)
        self._merge_discipline_held = plan
        records = [
            merge_discipline.step_record(s) for s in steps]
        records += [
            merge_discipline.attempt_record(a) for a in attempts]
        for record in records:
            self._publish_merge_record(record)
        return {
            "steps": [s.to_record() for s in steps],
            "attempts": [a.to_record() for a in attempts],
            "records": records,
            "count": len(steps) + len(attempts),
            "screen": merge_discipline.format_merge_screen(registry),
            "explanation": merge_discipline.PLAIN_EXPLANATION,
        }

    def report_merge(self) -> dict[str, Any]:
        """Report the discipline's verdicts to the coordinator (M-128).

        The report is derived from what the session
        holds by :meth:`merge_report` - every verdict
        the evidence holds, in judgement order - and
        published as session news: each verdict as its
        ``verdict_record``, then the report itself as
        ONE ``report_record`` session event holding
        every verdict and every line, never one report
        per verdict. The announcements are deduped:
        reporting again while the same evidence is
        held publishes nothing new, and a report grown
        by newly held evidence announces as the new
        report it is. Returns the report, its news
        record, the count of verdicts, the verdicts
        screen, and the plain explanation. Reporting
        executes no git and performs no merge: the
        coordinator acts on the verdicts through later
        roads.
        """
        from ..core import merge_discipline

        report = self.merge_report()
        for verdict in report.verdicts:
            self._publish_verdict_record(
                merge_discipline.verdict_record(verdict))
        record = merge_discipline.report_record(report)
        self._publish_merge_report_record(record)
        return {
            "report": report.to_record(),
            "record": record,
            "count": len(report.verdicts),
            "screen": merge_discipline.format_verdicts(report),
            "explanation": merge_discipline.PLAIN_EXPLANATION,
        }

    def _publish_merge_record(self, record: dict[str, Any]) -> None:
        """Publish one piece of merge evidence as session news (M-128).

        The pure layer's ``step_record`` and
        ``attempt_record`` are journaled through the
        same checkpoint road every sibling slice uses,
        when a session is attached. Each piece of
        evidence is announced at most once, under its
        own id. A foreign record type is never
        published on this road.
        """
        if record.get("type") == "merge_step":
            key = ("merge_step", record.get("step_id"))
        elif record.get("type") == "merge_attempt":
            key = ("merge_attempt", record.get("attempt_id"))
        else:
            return
        announced = getattr(self, "_merge_announced", None)
        if announced is None:
            announced = set()
            self._merge_announced = announced
        if key in announced:
            return
        announced.add(key)
        if self._session_store and self.session_id:
            self._checkpoint(record)

    def _publish_verdict_record(self, record: dict[str, Any]) -> None:
        """Publish one verdict as session news (M-128).

        The pure layer's ``verdict_record`` is
        journaled through the same checkpoint road,
        when a session is attached. Each verdict is
        announced at most once: the announcement is
        keyed by the verdict's whole shape (kind,
        member, slice, branch, title), so the same
        judgement derived again from the same evidence
        is not news twice. A foreign record type is
        never published on this road.
        """
        if record.get("type") != "merge_verdict":
            return
        announced = getattr(self, "_merge_verdict_announced", None)
        if announced is None:
            announced = set()
            self._merge_verdict_announced = announced
        key = (
            record.get("kind"), record.get("member"),
            record.get("slice_id"), record.get("branch"),
            record.get("title"))
        if key in announced:
            return
        announced.add(key)
        if self._session_store and self.session_id:
            self._checkpoint(record)

    def _publish_merge_report_record(
            self, record: dict[str, Any]) -> None:
        """Publish one merge report as session news (M-128).

        The pure layer's ``report_record`` is journaled
        through the same checkpoint road, when a
        session is attached - ONE event holding every
        verdict and every line, so the coordinator is
        told once. Each report is announced at most
        once: the announcement is keyed by the
        report's verdicts and lines, so a report grown
        by newly held evidence announces again as the
        new report it is. A foreign record type is
        never published on this road.
        """
        if record.get("type") != "merge_report":
            return
        announced = getattr(self, "_merge_report_announced", None)
        if announced is None:
            announced = set()
            self._merge_report_announced = announced
        key = (
            tuple(
                (v.get("kind"), v.get("member"),
                 v.get("slice_id"), v.get("branch"),
                 v.get("title"))
                for v in record.get("verdicts", [])),
            tuple(
                (line.get("member"),
                 tuple(line.get("merged", [])),
                 line.get("stopped_slice"))
                for line in record.get("lines", [])))
        if key in announced:
            return
        announced.add(key)
        if self._session_store and self.session_id:
            self._checkpoint(record)

    # -- M-129: heterogeneous crews --

    def _hetero_crew_registry(self):
        """The held heterogeneous-crew registry (M-129).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds pure-layer assignments, budgets and
        readings in the order they were given, beside
        the session merge-discipline registry (M-128)
        and never in it: the crew's routes are the
        coordinator's evidence, held under the
        heterogeneity this slice names. It is created
        on first use, so an agent whose ``__init__``
        never ran still holds exactly one. The
        attribute is named ``_hetero_crew_store``,
        never the method's own name (the M-108
        lesson).
        """
        registry = getattr(self, "_hetero_crew_store", None)
        if registry is None:
            from ..core.heterogeneous_crews import (
                HeterogeneousCrewRegistry,
            )
            registry = HeterogeneousCrewRegistry()
            self._hetero_crew_store = registry
        return registry

    def hetero_status(self) -> dict[str, Any]:
        """The heterogeneous crew, in plain data (M-129).

        The assignments, budgets and readings held
        this session as plain records, the session
        plan's evidence as plain records (the shipped
        example plan - four assignments, two budgets
        and two readings among the M-121 casting, kept
        by the architect - until a plan is recorded),
        the derived report as its one report record,
        the one screen - rendered from the held
        registry, or from the shipped example plan
        when nothing is held yet - and the plain
        explanation. Reading registers and publishes
        nothing, spawns no crew, calls no provider
        and performs no routing or billing: this
        layer holds the crew as data only. There is
        no Part VIII board yet; the screen is where
        the verdicts are visible.
        """
        from ..core import heterogeneous_crews

        registry = self._hetero_crew_registry()
        held_assignments = registry.list_assignments()
        held_budgets = registry.list_budgets()
        held_readings = registry.list_readings()
        plan = self.heterogeneous_crew()
        held = held_assignments or held_budgets or held_readings
        screen = heterogeneous_crews.format_hetero_screen(registry) \
            if held \
            else heterogeneous_crews.format_hetero_screen()
        return {
            "assignments": [
                a.to_record() for a in held_assignments],
            "budgets": [b.to_record() for b in held_budgets],
            "readings": [r.to_record() for r in held_readings],
            "plan": {
                "keeper": plan.keeper,
                "assignments": [
                    a.to_record() for a in plan.assignments],
                "budgets": [b.to_record() for b in plan.budgets],
                "readings": [
                    r.to_record() for r in plan.readings],
            },
            "report": heterogeneous_crews.report_record(
                self.hetero_report()),
            "screen": screen,
            "explanation": heterogeneous_crews.PLAIN_EXPLANATION,
        }

    def get_hetero_assignment(self, assignment_id: Any):
        """The one held assignment an id names (M-129).

        An assignment the session does not hold raises
        KeyError, exactly as the pure registry answers.
        """
        return self._hetero_crew_registry().get_assignment(
            assignment_id)

    def get_hetero_budget(self, budget_id: Any):
        """The one held budget an id names (M-129).

        A budget the session does not hold raises
        KeyError, exactly as the pure registry answers.
        """
        return self._hetero_crew_registry().get_budget(budget_id)

    def get_hetero_reading(self, reading_id: Any):
        """The one held usage reading an id names (M-129).

        A reading the session does not hold raises
        KeyError, exactly as the pure registry answers.
        """
        return self._hetero_crew_registry().get_reading(reading_id)

    def find_hetero_verdicts(self, member: Any):
        """Every verdict on one member's route (M-129).

        The session's held registry answers when the
        session holds any evidence; otherwise the
        shipped example plan answers. A member held
        in no verdict in the answering set raises
        KeyError. Reading registers and publishes
        nothing.
        """
        from ..core.crew_members import normalize_member_id
        from ..core.heterogeneous_crews import (
            load_heterogeneous_crew,
        )

        wanted = normalize_member_id(member)
        registry = self._hetero_crew_registry()
        if registry.list_assignments() or registry.list_budgets() \
                or registry.list_readings():
            found = registry.for_member(wanted)
        else:
            found = load_heterogeneous_crew().report().for_member(
                wanted)
        if not found:
            raise KeyError(
                f"no verdict stands on the member's route: "
                f"{wanted!r}")
        return found

    def heterogeneous_crew(self):
        """The session's crew plan, as data (M-129).

        The plan the session recorded through
        :meth:`record_heterogeneous_crew`, or the
        shipped example plan until one is recorded.
        Reading registers and publishes nothing.
        """
        from ..core.heterogeneous_crews import (
            load_heterogeneous_crew,
        )

        plan = getattr(self, "_hetero_crew_held", None)
        if plan is None:
            return load_heterogeneous_crew()
        return plan

    def hetero_report(self):
        """The report the plan's evidence yields (M-129).

        Derived by the pure layer from what the
        session holds - the held registry when the
        session holds any evidence, otherwise the
        shipped example plan - every verdict the
        evidence holds, in judgement order:
        unknown-route verdicts, then missing-budget
        verdicts, then over-budget verdicts, with
        every route's state beside them. Reading
        registers and publishes nothing: publishing
        is :meth:`report_hetero`' road.
        """
        from ..core.heterogeneous_crews import (
            load_heterogeneous_crew,
        )

        registry = self._hetero_crew_registry()
        if registry.list_assignments() or registry.list_budgets() \
                or registry.list_readings():
            return registry.report()
        return load_heterogeneous_crew().report()

    def register_hetero_assignment(
            self, assignment: Any) -> dict[str, Any]:
        """Hold one assignment for the session (M-129).

        The assignment is held by the pure registry
        under its id or a fresh deterministic one - a
        supplied id already held refuses, a member
        assigned twice refuses, and a refusal holds
        nothing new and publishes nothing - and a
        held assignment is published as its
        ``assignment_record`` session-news record
        through the checkpoint road, so evidence
        given is news with its shape attached.
        Returns the held assignment, its news record,
        the screen rendered after it landed, and the
        plain explanation. Holding an assignment
        spawns no crew and calls no provider: the
        registry holds the evidence as data.
        """
        from ..core import heterogeneous_crews

        registry = self._hetero_crew_registry()
        held = registry.register_assignment(assignment)
        record = heterogeneous_crews.assignment_record(held)
        self._publish_hetero_record(record)
        return {
            "assignment": held.to_record(),
            "record": record,
            "screen": heterogeneous_crews.format_hetero_screen(
                registry),
            "explanation": heterogeneous_crews.PLAIN_EXPLANATION,
        }

    def register_hetero_budget(
            self, budget: Any) -> dict[str, Any]:
        """Hold one Part V budget for the session (M-129).

        The budget is held by the pure registry under
        its own M-107 budget id - a budget naming no
        id refuses, an id already held refuses, and a
        refusal holds nothing new. Budgets are the
        M-107 layer's own records, so holding one
        publishes no session news on this slice's
        roads: the news this slice publishes is its
        assignments, readings, verdicts and reports.
        Returns the held budget, the screen rendered
        after it landed, and the plain explanation.
        """
        from ..core import heterogeneous_crews

        registry = self._hetero_crew_registry()
        held = registry.register_budget(budget)
        return {
            "budget": held.to_record(),
            "screen": heterogeneous_crews.format_hetero_screen(
                registry),
            "explanation": heterogeneous_crews.PLAIN_EXPLANATION,
        }

    def register_hetero_reading(
            self, reading: Any) -> dict[str, Any]:
        """Hold one usage reading for the session (M-129).

        The reading is held by the pure registry
        under its id or a fresh deterministic one - a
        supplied id already held refuses, two
        readings for one member refuse, and a refusal
        holds nothing new and publishes nothing - and
        a held reading is published as its
        ``reading_record`` session-news record
        through the checkpoint road. Returns the held
        reading, its news record, the screen rendered
        after it landed, and the plain explanation.
        Holding a reading bills nothing: the registry
        holds the evidence as data.
        """
        from ..core import heterogeneous_crews

        registry = self._hetero_crew_registry()
        held = registry.register_reading(reading)
        record = heterogeneous_crews.reading_record(held)
        self._publish_hetero_record(record)
        return {
            "reading": held.to_record(),
            "record": record,
            "screen": heterogeneous_crews.format_hetero_screen(
                registry),
            "explanation": heterogeneous_crews.PLAIN_EXPLANATION,
        }

    def record_heterogeneous_crew(
            self, plan: Any = None) -> dict[str, Any]:
        """Record a whole crew plan for the session (M-129).

        With no plan named, the shipped example plan
        is recorded through the pure layer - four
        assignments, two budgets and two readings
        among the M-121 casting, kept by the
        architect. A plan loaded from a file (the
        pure layer's ``load_heterogeneous_crew_file``
        road) may be passed instead, so a real crew
        plan is recorded as it stands. Every budget,
        assignment and reading is held in plan order;
        every assignment and reading is published as
        its ``assignment_record`` / ``reading_record``
        session news, deduped per evidence id (the
        budgets are the M-107 layer's own records and
        are held without news, exactly as
        :meth:`register_hetero_budget` holds one);
        the plan is remembered as the session's plan,
        and the same plan recorded twice refuses - a
        plan is recorded once, never duplicated into
        the session. Returns the held assignments,
        budgets and readings, their news records, the
        count of evidence held, the screen, and the
        explanation. Recording spawns no crew, calls
        no provider and bills nothing.
        """
        from ..core import heterogeneous_crews

        plan = plan if plan is not None \
            else heterogeneous_crews.load_heterogeneous_crew()
        fingerprint = (
            tuple((a.member, a.provider, a.model, a.budget_id)
                  for a in plan.assignments),
            tuple((b.budget_id, b.scope, b.token_limit,
                    b.cost_limit, b.time_limit_seconds,
                    b.command_limit) for b in plan.budgets),
            tuple((r.member, r.usage.tokens_used,
                    r.usage.cost_used, r.usage.time_used_seconds,
                    r.usage.commands_used)
                  for r in plan.readings))
        recorded = getattr(self, "_hetero_crew_recorded", None)
        if recorded is None:
            recorded = set()
            self._hetero_crew_recorded = recorded
        if fingerprint in recorded:
            raise ValueError(
                "this crew plan is already recorded for "
                "the session; a plan is recorded once")
        registry = self._hetero_crew_registry()
        assignments, budgets, readings = registry.register_plan(plan)
        recorded.add(fingerprint)
        self._hetero_crew_held = plan
        records = [
            heterogeneous_crews.assignment_record(a)
            for a in assignments]
        records += [
            heterogeneous_crews.reading_record(r) for r in readings]
        for record in records:
            self._publish_hetero_record(record)
        return {
            "assignments": [a.to_record() for a in assignments],
            "budgets": [b.to_record() for b in budgets],
            "readings": [r.to_record() for r in readings],
            "records": records,
            "count": len(assignments) + len(budgets) + len(readings),
            "screen": heterogeneous_crews.format_hetero_screen(
                registry),
            "explanation": heterogeneous_crews.PLAIN_EXPLANATION,
        }

    def report_hetero(self) -> dict[str, Any]:
        """Report the crew's verdicts to the coordinator (M-129).

        The report is derived from what the session
        holds by :meth:`hetero_report` - every verdict
        the evidence holds, in judgement order - and
        published as session news: each verdict as its
        ``verdict_record``, then the report itself as
        ONE ``report_record`` session event holding
        every verdict and every route, never one
        report per verdict. The announcements are
        deduped: reporting again while the same
        evidence is held publishes nothing new, and a
        report grown by newly held evidence announces
        as the new report it is. Returns the report,
        its news record, the count of verdicts, the
        verdicts screen, and the plain explanation.
        Reporting spawns no crew and calls no
        provider: the coordinator acts on the verdicts
        through later roads.
        """
        from ..core import heterogeneous_crews

        report = self.hetero_report()
        for verdict in report.verdicts:
            self._publish_hetero_verdict_record(
                heterogeneous_crews.verdict_record(verdict))
        record = heterogeneous_crews.report_record(report)
        self._publish_hetero_report_record(record)
        return {
            "report": report.to_record(),
            "record": record,
            "count": len(report.verdicts),
            "screen": heterogeneous_crews.format_verdicts(report),
            "explanation": heterogeneous_crews.PLAIN_EXPLANATION,
        }

    def _publish_hetero_record(self, record: dict[str, Any]) -> None:
        """Publish one piece of crew evidence as session news (M-129).

        The pure layer's ``assignment_record`` and
        ``reading_record`` are journaled through the
        same checkpoint road every sibling slice uses,
        when a session is attached. Each piece of
        evidence is announced at most once, under its
        own id. A foreign record type is never
        published on this road.
        """
        if record.get("type") == "hetero_assignment":
            key = ("hetero_assignment", record.get("assignment_id"))
        elif record.get("type") == "hetero_reading":
            key = ("hetero_reading", record.get("reading_id"))
        else:
            return
        announced = getattr(self, "_hetero_announced", None)
        if announced is None:
            announced = set()
            self._hetero_announced = announced
        if key in announced:
            return
        announced.add(key)
        if self._session_store and self.session_id:
            self._checkpoint(record)

    def _publish_hetero_verdict_record(
            self, record: dict[str, Any]) -> None:
        """Publish one verdict as session news (M-129).

        The pure layer's ``verdict_record`` is
        journaled through the same checkpoint road,
        when a session is attached. Each verdict is
        announced at most once: the announcement is
        keyed by the verdict's whole shape (kind,
        member, provider, model, title), so the same
        judgement derived again from the same evidence
        is not news twice. A foreign record type is
        never published on this road.
        """
        if record.get("type") != "hetero_verdict":
            return
        announced = getattr(self, "_hetero_verdict_announced", None)
        if announced is None:
            announced = set()
            self._hetero_verdict_announced = announced
        key = (
            record.get("kind"), record.get("member"),
            record.get("provider"), record.get("model"),
            record.get("title"))
        if key in announced:
            return
        announced.add(key)
        if self._session_store and self.session_id:
            self._checkpoint(record)

    def _publish_hetero_report_record(
            self, record: dict[str, Any]) -> None:
        """Publish one hetero report as session news (M-129).

        The pure layer's ``report_record`` is journaled
        through the same checkpoint road, when a
        session is attached - ONE event holding every
        verdict and every route, so the coordinator is
        told once. Each report is announced at most
        once: the announcement is keyed by the
        report's verdicts and routes, so a report
        grown by newly held evidence announces again
        as the new report it is. A foreign record type
        is never published on this road.
        """
        if record.get("type") != "hetero_report":
            return
        announced = getattr(self, "_hetero_report_announced", None)
        if announced is None:
            announced = set()
            self._hetero_report_announced = announced
        key = (
            tuple(
                (v.get("kind"), v.get("member"),
                 v.get("provider"), v.get("model"),
                 v.get("title"))
                for v in record.get("verdicts", [])),
            tuple(
                (route.get("member"), route.get("provider"),
                 route.get("model"), route.get("budget_status"))
                for route in record.get("routes", [])))
        if key in announced:
            return
        announced.add(key)
        if self._session_store and self.session_id:
            self._checkpoint(record)


    # -- M-130: the Auditor's veto --

    def _auditor_veto_registry(self):
        """The held Auditor's-veto registry (M-130).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds pure-layer cases, checks and results
        in the order they were given, beside the
        session heterogeneous-crew registry (M-129)
        and never in it: the audit is the
        coordinator's evidence, held under the veto
        this slice names. It is created on first use,
        so an agent whose ``__init__`` never ran still
        holds exactly one. The attribute is named
        ``_auditor_veto_store``, never the method's
        own name (the M-108 lesson).
        """
        registry = getattr(self, "_auditor_veto_store", None)
        if registry is None:
            from ..core.auditor_veto import (
                AuditorVetoRegistry,
            )
            registry = AuditorVetoRegistry()
            self._auditor_veto_store = registry
        return registry

    def veto_status(self) -> dict[str, Any]:
        """The Auditor's veto, in plain data (M-130).

        The cases, checks and results held this
        session as plain records, the session ledger's
        evidence as plain records (the shipped example
        ledger - three cases, six checks and five
        results among the Part VI slices, kept by the
        auditor - until a ledger is recorded), the
        derived report as its one report record, the
        one screen - rendered from the held registry,
        or from the shipped example ledger when nothing
        is held yet - and the plain explanation.
        Reading registers and publishes nothing, runs
        no check and banks nothing: this layer holds
        the audit as data only. There is no Part VIII
        board yet; the screen is where the verdicts
        are visible.
        """
        from ..core import auditor_veto

        registry = self._auditor_veto_registry()
        held_cases = registry.list_cases()
        held_checks = registry.list_checks()
        held_results = registry.list_results()
        ledger = self.auditor_ledger()
        held = held_cases or held_checks or held_results
        screen = auditor_veto.format_veto_screen(registry) \
            if held \
            else auditor_veto.format_veto_screen()
        return {
            "cases": [c.to_record() for c in held_cases],
            "checks": [c.to_record() for c in held_checks],
            "results": [r.to_record() for r in held_results],
            "ledger": {
                "keeper": ledger.keeper,
                "cases": [c.to_record() for c in ledger.cases],
                "checks": [c.to_record() for c in ledger.checks],
                "results": [
                    r.to_record() for r in ledger.results],
            },
            "report": auditor_veto.report_record(
                self.veto_report()),
            "screen": screen,
            "explanation": auditor_veto.PLAIN_EXPLANATION,
        }

    def get_veto_case(self, case_id: Any):
        """The one held case an id names (M-130).

        A case the session does not hold raises
        KeyError, exactly as the pure registry answers.
        """
        return self._auditor_veto_registry().get_case(
            case_id)

    def get_veto_check(self, check_id: Any):
        """The one held check an id names (M-130).

        A check the session does not hold raises
        KeyError, exactly as the pure registry answers.
        """
        return self._auditor_veto_registry().get_check(
            check_id)

    def get_veto_result(self, result_id: Any):
        """The one held result an id names (M-130).

        A result the session does not hold raises
        KeyError, exactly as the pure registry answers.
        """
        return self._auditor_veto_registry().get_result(
            result_id)

    def find_veto_verdicts(self, slice_id: Any):
        """Every verdict on one slice (M-130).

        The session's held registry answers when the
        session holds any evidence; otherwise the
        shipped example ledger answers. A slice held
        in no verdict in the answering set raises
        KeyError. Reading registers and publishes
        nothing.
        """
        from ..core.auditor_veto import (
            load_auditor_ledger,
        )
        from ..core.worktrees import normalize_slice_id

        wanted = normalize_slice_id(slice_id)
        registry = self._auditor_veto_registry()
        if registry.list_cases() or registry.list_checks() \
                or registry.list_results():
            found = registry.for_slice(wanted)
        else:
            found = load_auditor_ledger().report().for_slice(
                wanted)
        if not found:
            raise KeyError(
                f"no veto stands on the slice: "
                f"{wanted!r}")
        return found

    def auditor_ledger(self):
        """The session's veto ledger, as data (M-130).

        The ledger the session recorded through
        :meth:`record_auditor_ledger`, or the shipped
        example ledger until one is recorded. Reading
        registers and publishes nothing.
        """
        from ..core.auditor_veto import (
            load_auditor_ledger,
        )

        ledger = getattr(self, "_auditor_veto_held", None)
        if ledger is None:
            return load_auditor_ledger()
        return ledger

    def veto_report(self):
        """The report the ledger's evidence yields (M-130).

        Derived by the pure layer from what the
        session holds - the held registry when the
        session holds any evidence, otherwise the
        shipped example ledger - every verdict the
        evidence holds, in judgement order:
        failed-check verdicts, then unproven-check
        verdicts, with every case's gate beside them.
        Reading registers and publishes nothing:
        publishing is :meth:`report_veto`' road.
        """
        from ..core.auditor_veto import (
            load_auditor_ledger,
        )

        registry = self._auditor_veto_registry()
        if registry.list_cases() or registry.list_checks() \
                or registry.list_results():
            return registry.report()
        return load_auditor_ledger().report()

    def register_veto_case(
            self, case: Any) -> dict[str, Any]:
        """Hold one case for the session (M-130).

        The case is held by the pure registry under
        its id or a fresh deterministic one - a
        supplied id already held refuses, a slice
        audited twice refuses, and a refusal holds
        nothing new and publishes nothing - and a
        held case is published as its ``case_record``
        session-news record through the checkpoint
        road, so evidence given is news with its
        shape attached. Returns the held case, its
        news record, the screen rendered after it
        landed, and the plain explanation. Holding a
        case runs no check: the registry holds the
        evidence as data.
        """
        from ..core import auditor_veto

        registry = self._auditor_veto_registry()
        held = registry.register_case(case)
        record = auditor_veto.case_record(held)
        self._publish_veto_record(record)
        return {
            "case": held.to_record(),
            "record": record,
            "screen": auditor_veto.format_veto_screen(
                registry),
            "explanation": auditor_veto.PLAIN_EXPLANATION,
        }

    def register_veto_check(
            self, check: Any) -> dict[str, Any]:
        """Hold one check for the session (M-130).

        The check is held by the pure registry under
        its id or a fresh deterministic one - a
        supplied id already held refuses, a check
        carried twice by one slice refuses, and a
        refusal holds nothing new and publishes
        nothing - and a held check is published as
        its ``check_record`` session-news record
        through the checkpoint road. Returns the held
        check, its news record, the screen rendered
        after it landed, and the plain explanation.
        Holding a check runs nothing: the registry
        holds the evidence as data.
        """
        from ..core import auditor_veto

        registry = self._auditor_veto_registry()
        held = registry.register_check(check)
        record = auditor_veto.check_record(held)
        self._publish_veto_record(record)
        return {
            "check": held.to_record(),
            "record": record,
            "screen": auditor_veto.format_veto_screen(
                registry),
            "explanation": auditor_veto.PLAIN_EXPLANATION,
        }

    def register_veto_result(
            self, result: Any) -> dict[str, Any]:
        """Hold one result for the session (M-130).

        The result is held by the pure registry under
        its id or a fresh deterministic one - a
        supplied id already held refuses, two results
        for one check refuse, and a refusal holds
        nothing new and publishes nothing - and a
        held result is published as its
        ``result_record`` session-news record through
        the checkpoint road. Returns the held result,
        its news record, the screen rendered after it
        landed, and the plain explanation. Holding a
        result executes no suite: the registry holds
        the evidence as data.
        """
        from ..core import auditor_veto

        registry = self._auditor_veto_registry()
        held = registry.register_result(result)
        record = auditor_veto.result_record(held)
        self._publish_veto_record(record)
        return {
            "result": held.to_record(),
            "record": record,
            "screen": auditor_veto.format_veto_screen(
                registry),
            "explanation": auditor_veto.PLAIN_EXPLANATION,
        }

    def record_auditor_ledger(
            self, ledger: Any = None) -> dict[str, Any]:
        """Record a whole veto ledger for the session (M-130).

        With no ledger named, the shipped example
        ledger is recorded through the pure layer -
        three cases, six checks and five results
        among the Part VI slices, kept by the
        auditor. A ledger loaded from a file (the
        pure layer's ``load_auditor_ledger_file``
        road) may be passed instead, so a real veto
        ledger is recorded as it stands. Every case,
        check and result is held in ledger order and
        published as its ``case_record`` /
        ``check_record`` / ``result_record`` session
        news, deduped per evidence id; the ledger is
        remembered as the session's ledger, and the
        same ledger recorded twice refuses - a ledger
        is recorded once, never duplicated into the
        session. Returns the held cases, checks and
        results, their news records, the count of
        evidence held, the screen, and the
        explanation. Recording runs no check, executes
        no suite and banks nothing.
        """
        from ..core import auditor_veto

        ledger = ledger if ledger is not None \
            else auditor_veto.load_auditor_ledger()
        fingerprint = (
            tuple((c.slice_id, c.title, c.builder)
                  for c in ledger.cases),
            tuple((c.slice_id, c.name, c.required)
                  for c in ledger.checks),
            tuple((r.slice_id, r.check, r.outcome,
                    r.evidence)
                  for r in ledger.results))
        recorded = getattr(self, "_auditor_veto_recorded", None)
        if recorded is None:
            recorded = set()
            self._auditor_veto_recorded = recorded
        if fingerprint in recorded:
            raise ValueError(
                "this veto ledger is already recorded for "
                "the session; a ledger is recorded once")
        registry = self._auditor_veto_registry()
        cases, checks, results = registry.register_ledger(ledger)
        recorded.add(fingerprint)
        self._auditor_veto_held = ledger
        records = [
            auditor_veto.case_record(c) for c in cases]
        records += [
            auditor_veto.check_record(c) for c in checks]
        records += [
            auditor_veto.result_record(r) for r in results]
        for record in records:
            self._publish_veto_record(record)
        return {
            "cases": [c.to_record() for c in cases],
            "checks": [c.to_record() for c in checks],
            "results": [r.to_record() for r in results],
            "records": records,
            "count": len(cases) + len(checks) + len(results),
            "screen": auditor_veto.format_veto_screen(
                registry),
            "explanation": auditor_veto.PLAIN_EXPLANATION,
        }

    def report_veto(self) -> dict[str, Any]:
        """Report the vetoes to the coordinator (M-130).

        The report is derived from what the session
        holds by :meth:`veto_report` - every verdict
        the evidence holds, in judgement order - and
        published as session news: each verdict as its
        ``verdict_record``, then the report itself as
        ONE ``report_record`` session event holding
        every verdict and every gate, never one report
        per verdict. The announcements are deduped:
        reporting again while the same evidence is
        held publishes nothing new, and a report grown
        by newly held evidence announces as the new
        report it is. Returns the report, its news
        record, the count of verdicts, the verdicts
        screen, and the plain explanation. Reporting
        runs no check and banks nothing: the
        coordinator acts on the verdicts through later
        roads.
        """
        from ..core import auditor_veto

        report = self.veto_report()
        for verdict in report.verdicts:
            self._publish_veto_verdict_record(
                auditor_veto.verdict_record(verdict))
        record = auditor_veto.report_record(report)
        self._publish_veto_report_record(record)
        return {
            "report": report.to_record(),
            "record": record,
            "count": len(report.verdicts),
            "screen": auditor_veto.format_verdicts(report),
            "explanation": auditor_veto.PLAIN_EXPLANATION,
        }

    def _publish_veto_record(self, record: dict[str, Any]) -> None:
        """Publish one piece of audit evidence as session news (M-130).

        The pure layer's ``case_record``,
        ``check_record`` and ``result_record`` are
        journaled through the same checkpoint road
        every sibling slice uses, when a session is
        attached. Each piece of evidence is announced
        at most once, under its own id. A foreign
        record type is never published on this road.
        """
        if record.get("type") == "veto_case":
            key = ("veto_case", record.get("case_id"))
        elif record.get("type") == "veto_check":
            key = ("veto_check", record.get("check_id"))
        elif record.get("type") == "veto_result":
            key = ("veto_result", record.get("result_id"))
        else:
            return
        announced = getattr(self, "_veto_announced", None)
        if announced is None:
            announced = set()
            self._veto_announced = announced
        if key in announced:
            return
        announced.add(key)
        if self._session_store and self.session_id:
            self._checkpoint(record)

    def _publish_veto_verdict_record(
            self, record: dict[str, Any]) -> None:
        """Publish one verdict as session news (M-130).

        The pure layer's ``verdict_record`` is
        journaled through the same checkpoint road,
        when a session is attached. Each verdict is
        announced at most once: the announcement is
        keyed by the verdict's whole shape (kind,
        slice, check, title), so the same judgement
        derived again from the same evidence is not
        news twice. A foreign record type is never
        published on this road.
        """
        if record.get("type") != "veto_verdict":
            return
        announced = getattr(self, "_veto_verdict_announced", None)
        if announced is None:
            announced = set()
            self._veto_verdict_announced = announced
        key = (
            record.get("kind"), record.get("slice_id"),
            record.get("check"), record.get("title"))
        if key in announced:
            return
        announced.add(key)
        if self._session_store and self.session_id:
            self._checkpoint(record)

    def _publish_veto_report_record(
            self, record: dict[str, Any]) -> None:
        """Publish one veto report as session news (M-130).

        The pure layer's ``report_record`` is journaled
        through the same checkpoint road, when a
        session is attached - ONE event holding every
        verdict and every gate, so the coordinator is
        told once. Each report is announced at most
        once: the announcement is keyed by the
        report's verdicts and gates, so a report
        grown by newly held evidence announces again
        as the new report it is. A foreign record type
        is never published on this road.
        """
        if record.get("type") != "veto_report":
            return
        announced = getattr(self, "_veto_report_announced", None)
        if announced is None:
            announced = set()
            self._veto_report_announced = announced
        key = (
            tuple(
                (v.get("kind"), v.get("slice_id"),
                 v.get("check"), v.get("title"))
                for v in record.get("verdicts", [])),
            tuple(
                (gate.get("slice_id"), gate.get("status"),
                 gate.get("proven"), gate.get("failed"),
                 gate.get("unproven"))
                for gate in record.get("gates", [])))
        if key in announced:
            return
        announced.add(key)
        if self._session_store and self.session_id:
            self._checkpoint(record)


    # -- M-131: research swarms --

    def _research_swarm_registry(self):
        """The held research-swarm registry (M-131).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds the pure-layer question, assignments
        and findings in the order they were given,
        beside the session Auditor's-veto registry
        (M-130) and never in it: the swarm is the
        coordinator's fan-out, held under the
        research this slice names. It is created on
        first use, so an agent whose ``__init__``
        never ran still holds exactly one. The
        attribute is named ``_research_swarm_store``,
        never the method's own name (the M-108
        lesson).
        """
        registry = getattr(self, "_research_swarm_store", None)
        if registry is None:
            from ..core.research_swarms import (
                ResearchSwarmRegistry,
            )
            registry = ResearchSwarmRegistry()
            self._research_swarm_store = registry
        return registry

    def _held_swarm_question(self, registry):
        """The held swarm question, or None (M-131).

        The pure registry raises KeyError when no
        question is held; the agent layer reads that
        as no question held yet, so the status and
        screen roads can speak plainly about a swarm
        whose pieces arrived before its question.
        """
        try:
            return registry.question()
        except KeyError:
            return None

    def _swarm_screen(self, registry):
        """The swarm screen for the held registry (M-131).

        The full pure-layer screen is rendered from
        the held registry once its question is held.
        While pieces are held without a question, the
        screen is the findings view of the pieces held
        so far - an honest partial screen, never the
        shipped example standing in for evidence the
        session does not hold.
        """
        from ..core import research_swarms

        if self._held_swarm_question(registry) is not None:
            return research_swarms.format_swarm_screen(registry)
        partial = research_swarms.ResearchSwarm(
            assignments=registry.list_assignments(),
            findings=registry.list_findings(),
            leader="")
        return research_swarms.format_findings(partial)

    def swarm_status(self) -> dict[str, Any]:
        """The research swarm, in plain data (M-131).

        The question, assignments and findings held
        this session as plain records (no question
        record until one is held), the session swarm's
        pieces as plain records (the shipped example
        swarm - one cartographer-led question, three
        assignments and three findings - until a swarm
        is recorded), the derived digest as its one
        digest record (None while pieces are held
        without a question, since no digest can be
        derived from a swarm whose question is not
        held), the one screen - rendered from the held
        registry, or from the shipped example swarm
        when nothing is held yet - and the plain
        explanation. Reading registers and publishes
        nothing, runs no research, calls no model and
        spawns no crew: this layer holds the swarm as
        data only. There is no Part VIII board yet;
        the screen is where the digest is visible.
        """
        from ..core import research_swarms

        registry = self._research_swarm_registry()
        held_question = self._held_swarm_question(registry)
        held_assignments = registry.list_assignments()
        held_findings = registry.list_findings()
        swarm = self.research_swarm()
        held = (held_question is not None or held_assignments
                or held_findings)
        if held and held_question is not None:
            screen = research_swarms.format_swarm_screen(
                registry)
            digest = research_swarms.digest_record(
                self.swarm_digest())
        elif held:
            screen = self._swarm_screen(registry)
            digest = None
        else:
            screen = research_swarms.format_swarm_screen()
            digest = research_swarms.digest_record(
                self.swarm_digest())
        return {
            "question": (
                held_question.to_record()
                if held_question is not None else None),
            "assignments": [
                a.to_record() for a in held_assignments],
            "findings": [f.to_record() for f in held_findings],
            "swarm": {
                "leader": swarm.leader,
                "question": (
                    swarm.question.to_record()
                    if swarm.question is not None else None),
                "assignments": [
                    a.to_record() for a in swarm.assignments],
                "findings": [
                    f.to_record() for f in swarm.findings],
            },
            "digest": digest,
            "screen": screen,
            "explanation": research_swarms.PLAIN_EXPLANATION,
        }

    def get_swarm_assignment(self, assignment_id: Any):
        """The one held assignment an id names (M-131).

        An assignment the session does not hold raises
        KeyError, exactly as the pure registry answers.
        """
        return self._research_swarm_registry().get_assignment(
            assignment_id)

    def get_swarm_finding(self, finding_id: Any):
        """The one held finding an id names (M-131).

        A finding the session does not hold raises
        KeyError, exactly as the pure registry answers.
        """
        return self._research_swarm_registry().get_finding(
            finding_id)

    def find_swarm_findings(self, member: Any):
        """Every finding one member returned (M-131).

        The session's held registry answers when the
        session holds any piece of the swarm; otherwise
        the shipped example swarm answers. A member
        holding no finding in the answering set raises
        KeyError. Reading registers and publishes
        nothing.
        """
        from ..core.crew_members import normalize_member_id
        from ..core.research_swarms import (
            load_research_swarm,
        )

        wanted = normalize_member_id(member)
        registry = self._research_swarm_registry()
        held = (self._held_swarm_question(registry) is not None
                or registry.list_assignments()
                or registry.list_findings())
        if held:
            found = registry.findings_for(wanted)
        else:
            found = tuple(
                finding for finding
                in load_research_swarm().findings
                if finding.member == wanted)
        if not found:
            raise KeyError(
                f"no finding from the member: {wanted!r}")
        return found

    def research_swarm(self):
        """The session's research swarm, as data (M-131).

        The swarm the session recorded through
        :meth:`record_research_swarm`, or the shipped
        example swarm until one is recorded. Reading
        registers and publishes nothing.
        """
        from ..core.research_swarms import (
            load_research_swarm,
        )

        swarm = getattr(self, "_research_swarm_held", None)
        if swarm is None:
            return load_research_swarm()
        return swarm

    def swarm_digest(self):
        """The digest the swarm's findings yield (M-131).

        Derived by the pure layer from what the
        session holds - the held registry when the
        session holds any piece of the swarm,
        otherwise the shipped example swarm. A
        registry holding pieces but no question
        answers exactly as the pure registry answers:
        KeyError, since no digest can be derived from
        a swarm whose question is not held. Reading
        registers and publishes nothing: publishing
        is :meth:`report_swarm_digest`' road.
        """
        from ..core.research_swarms import (
            digest_swarm,
            load_research_swarm,
        )

        registry = self._research_swarm_registry()
        held = (self._held_swarm_question(registry) is not None
                or registry.list_assignments()
                or registry.list_findings())
        if held:
            return registry.digest()
        return digest_swarm(load_research_swarm())

    def register_swarm_assignment(
            self, assignment: Any) -> dict[str, Any]:
        """Hold one swarm assignment for the session (M-131).

        The assignment is held by the pure registry
        under its id or a fresh deterministic one - a
        supplied id already held refuses, a member
        dealt twice refuses, and a refusal holds
        nothing new and publishes nothing - and a
        held assignment is published as its
        ``assignment_record`` session-news record
        through the checkpoint road, so evidence
        given is news with its shape attached.
        Returns the held assignment, its news record,
        the screen rendered after it landed, and the
        plain explanation. Holding an assignment runs
        no research and spawns no crew: the registry
        holds the swarm as data.
        """
        from ..core import research_swarms

        registry = self._research_swarm_registry()
        held = registry.register_assignment(assignment)
        record = research_swarms.assignment_record(held)
        self._publish_swarm_record(record)
        return {
            "assignment": held.to_record(),
            "record": record,
            "screen": self._swarm_screen(registry),
            "explanation": research_swarms.PLAIN_EXPLANATION,
        }

    def register_swarm_finding(
            self, finding: Any) -> dict[str, Any]:
        """Hold one swarm finding for the session (M-131).

        The finding is held by the pure registry
        under its id or a fresh deterministic one - a
        supplied id already held refuses, a finding
        from a member who holds no assignment refuses,
        two findings from one member refuse, and a
        refusal holds nothing new and publishes
        nothing - and a held finding is published as
        its ``finding_record`` session-news record
        through the checkpoint road. Returns the held
        finding, its news record, the screen rendered
        after it landed, and the plain explanation.
        Holding a finding runs no research and calls
        no model: the registry holds the swarm as
        data.
        """
        from ..core import research_swarms

        registry = self._research_swarm_registry()
        held = registry.register_finding(finding)
        record = research_swarms.finding_record(held)
        self._publish_swarm_record(record)
        return {
            "finding": held.to_record(),
            "record": record,
            "screen": self._swarm_screen(registry),
            "explanation": research_swarms.PLAIN_EXPLANATION,
        }

    def record_research_swarm(
            self, swarm: Any = None) -> dict[str, Any]:
        """Record a whole research swarm for the session (M-131).

        With no swarm named, the shipped example
        swarm is recorded through the pure layer -
        one cartographer-led question, three
        assignments and three findings. A swarm
        loaded from a file (the pure layer's
        ``load_research_swarm_file`` road) may be
        passed instead, so a real swarm is recorded
        as it stands. The question, every assignment
        and every finding is held in swarm order and
        published as its ``question_record`` /
        ``assignment_record`` / ``finding_record``
        session news, deduped per piece id; the swarm
        is remembered as the session's swarm, and the
        same swarm recorded twice refuses - a swarm
        is recorded once, never duplicated into the
        session. Returns the held question,
        assignments and findings, their news records,
        the count of pieces held, the screen, and the
        explanation. Recording runs no research,
        calls no model and spawns no crew.
        """
        from ..core import research_swarms

        swarm = swarm if swarm is not None \
            else research_swarms.load_research_swarm()
        fingerprint = (
            (swarm.question.text, swarm.question.leader)
            if swarm.question is not None else None,
            tuple((a.member, a.focus, a.brief)
                  for a in swarm.assignments),
            tuple((f.member, f.summary, tuple(f.sources))
                  for f in swarm.findings))
        recorded = getattr(self, "_research_swarm_recorded", None)
        if recorded is None:
            recorded = set()
            self._research_swarm_recorded = recorded
        if fingerprint in recorded:
            raise ValueError(
                "this research swarm is already recorded for "
                "the session; a swarm is recorded once")
        registry = self._research_swarm_registry()
        held_swarm = registry.register_swarm(swarm)
        recorded.add(fingerprint)
        self._research_swarm_held = swarm
        records = [
            research_swarms.question_record(held_swarm.question)]
        records += [
            research_swarms.assignment_record(a)
            for a in held_swarm.assignments]
        records += [
            research_swarms.finding_record(f)
            for f in held_swarm.findings]
        for record in records:
            self._publish_swarm_record(record)
        return {
            "question": held_swarm.question.to_record(),
            "assignments": [
                a.to_record() for a in held_swarm.assignments],
            "findings": [
                f.to_record() for f in held_swarm.findings],
            "records": records,
            "count": len(records),
            "screen": research_swarms.format_swarm_screen(
                registry),
            "explanation": research_swarms.PLAIN_EXPLANATION,
        }

    def report_swarm_digest(self) -> dict[str, Any]:
        """Report the swarm's digest as session news (M-131).

        The digest is derived from what the session
        holds by :meth:`swarm_digest` and published
        as ONE ``digest_record`` session event - the
        swarm's one digested answer, with its sources
        and its completeness, never one event per
        finding. The announcement is deduped:
        reporting again while the same findings are
        held publishes nothing new, and a digest grown
        by a newly held finding announces as the new
        digest it is. Returns the digest, its news
        record, its completeness, the digest screen,
        and the plain explanation. Reporting runs no
        research, calls no model and spawns no crew:
        the human acts on the digest through later
        roads.
        """
        from ..core import research_swarms

        digest = self.swarm_digest()
        record = research_swarms.digest_record(digest)
        self._publish_swarm_digest_record(record)
        registry = self._research_swarm_registry()
        if self._held_swarm_question(registry) is not None:
            screen = research_swarms.format_digest(registry)
        else:
            screen = research_swarms.format_digest()
        return {
            "digest": digest.to_record(),
            "record": record,
            "complete": digest.complete,
            "screen": screen,
            "explanation": research_swarms.PLAIN_EXPLANATION,
        }

    def _publish_swarm_record(self, record: dict[str, Any]) -> None:
        """Publish one piece of the swarm as session news (M-131).

        The pure layer's ``question_record``,
        ``assignment_record`` and ``finding_record``
        are journaled through the same checkpoint
        road every sibling slice uses, when a session
        is attached. Each piece is announced at most
        once, under its own id. A foreign record type
        is never published on this road.
        """
        if record.get("type") == "swarm_question":
            key = ("swarm_question", record.get("question_id"))
        elif record.get("type") == "swarm_assignment":
            key = ("swarm_assignment", record.get("assignment_id"))
        elif record.get("type") == "swarm_finding":
            key = ("swarm_finding", record.get("finding_id"))
        else:
            return
        announced = getattr(self, "_swarm_announced", None)
        if announced is None:
            announced = set()
            self._swarm_announced = announced
        if key in announced:
            return
        announced.add(key)
        if self._session_store and self.session_id:
            self._checkpoint(record)

    def _publish_swarm_digest_record(
            self, record: dict[str, Any]) -> None:
        """Publish one swarm digest as session news (M-131).

        The pure layer's ``digest_record`` is
        journaled through the same checkpoint road,
        when a session is attached - ONE event holding
        the whole digested answer, so the human is
        told once. Each digest is announced at most
        once: the announcement is keyed by the
        digest's whole shape (question, answer,
        sources, completeness, who is still out), so
        a digest grown by a newly held finding
        announces again as the new digest it is. A
        foreign record type is never published on
        this road.
        """
        if record.get("type") != "swarm_digest":
            return
        announced = getattr(self, "_swarm_digest_announced", None)
        if announced is None:
            announced = set()
            self._swarm_digest_announced = announced
        key = (
            record.get("question"), record.get("answer"),
            tuple(record.get("sources", [])),
            record.get("complete"),
            tuple(record.get("missing", [])))
        if key in announced:
            return
        announced.add(key)
        if self._session_store and self.session_id:
            self._checkpoint(record)

    # -- M-132: review panels --

    def _review_panel_registry(self):
        """The held review-panel registry (M-132).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds the pure-layer change and reviews
        in the order they were given, beside the
        session research-swarm registry (M-131) and
        never in it: the panel is two reviewers'
        reading of one change, held under the review
        this slice names. It is created on first
        use, so an agent whose ``__init__`` never
        ran still holds exactly one. The attribute
        is named ``_review_panel_store``, never the
        method's own name (the M-108 lesson).
        """
        registry = getattr(self, "_review_panel_store", None)
        if registry is None:
            from ..core.review_panels import (
                ReviewPanelRegistry,
            )
            registry = ReviewPanelRegistry()
            self._review_panel_store = registry
        return registry

    def _held_panel_change(self, registry):
        """The held panel change, or None (M-132).

        The pure registry raises KeyError when no
        change is held; the agent layer reads that
        as no change held yet, so the status and
        screen roads can speak plainly about a
        panel whose reviews arrived before its
        change.
        """
        try:
            return registry.change()
        except KeyError:
            return None

    def _panel_screen(self, registry):
        """The panel screen for the held registry (M-132).

        The full pure-layer screen is rendered from
        the held registry once its change is held.
        While reviews are held without a change, the
        screen is the reviews view of the pieces
        held so far - an honest partial screen,
        never the shipped example standing in for
        evidence the session does not hold.
        """
        from ..core import review_panels

        if self._held_panel_change(registry) is not None:
            return review_panels.format_panel_screen(registry)
        partial = review_panels.ReviewPanel(
            reviews=registry.list_reviews())
        return review_panels.format_reviews(partial)

    def panel_status(self) -> dict[str, Any]:
        """The review panel, in plain data (M-132).

        The change and reviews held this session as
        plain records (no change record until one
        is held), the session panel's pieces as
        plain records (the shipped example panel -
        the session-branching restore guard, two
        reviews on two different models - until a
        panel is recorded), the derived outcome as
        its one outcome record (None while pieces
        are held without a change, since no outcome
        can be derived from a panel whose change is
        not held), the one screen - rendered from
        the held registry, or from the shipped
        example panel when nothing is held yet -
        and the plain explanation. Reading registers
        and publishes nothing, runs no review, calls
        no model, executes no change and spawns no
        crew: this layer holds the panel as data
        only. There is no Part VIII board yet; the
        screen is where the outcome is visible.
        """
        from ..core import review_panels

        registry = self._review_panel_registry()
        held_change = self._held_panel_change(registry)
        held_reviews = registry.list_reviews()
        panel = self.review_panel()
        held = (held_change is not None or held_reviews)
        if held and held_change is not None:
            screen = review_panels.format_panel_screen(
                registry)
            outcome = review_panels.outcome_record(
                self.panel_outcome())
        elif held:
            screen = self._panel_screen(registry)
            outcome = None
        else:
            screen = review_panels.format_panel_screen()
            outcome = review_panels.outcome_record(
                self.panel_outcome())
        return {
            "change": (
                held_change.to_record()
                if held_change is not None else None),
            "reviews": [r.to_record() for r in held_reviews],
            "panel": {
                "change": (
                    panel.change.to_record()
                    if panel.change is not None else None),
                "reviews": [
                    r.to_record() for r in panel.reviews],
            },
            "outcome": outcome,
            "screen": screen,
            "explanation": review_panels.PLAIN_EXPLANATION,
        }

    def get_panel_review(self, review_id: Any):
        """The one held review an id names (M-132).

        A review the session does not hold raises
        KeyError, exactly as the pure registry
        answers.
        """
        return self._review_panel_registry().get_review(
            review_id)

    def find_panel_reviews(self, member: Any):
        """Every review one reviewer returned (M-132).

        The session's held registry answers when the
        session holds any piece of the panel;
        otherwise the shipped example panel answers.
        A reviewer holding no review in the
        answering set raises KeyError. Reading
        registers and publishes nothing.
        """
        from ..core.crew_members import normalize_member_id
        from ..core.review_panels import (
            load_review_panel,
        )

        wanted = normalize_member_id(member)
        registry = self._review_panel_registry()
        held = (self._held_panel_change(registry) is not None
                or registry.list_reviews())
        if held:
            found = registry.reviews_for(wanted)
        else:
            found = tuple(
                review for review
                in load_review_panel().reviews
                if review.reviewer == wanted)
        if not found:
            raise KeyError(
                f"no review from the reviewer: {wanted!r}")
        return found

    def review_panel(self):
        """The session's review panel, as data (M-132).

        The panel the session recorded through
        :meth:`record_review_panel`, or the shipped
        example panel until one is recorded. Reading
        registers and publishes nothing.
        """
        from ..core.review_panels import (
            load_review_panel,
        )

        panel = getattr(self, "_review_panel_held", None)
        if panel is None:
            return load_review_panel()
        return panel

    def panel_outcome(self):
        """The outcome the panel's verdicts yield (M-132).

        Derived by the pure layer from what the
        session holds - the held registry when the
        session holds any piece of the panel,
        otherwise the shipped example panel. A
        registry holding pieces but no change
        answers exactly as the pure registry
        answers: KeyError, since no outcome can be
        derived from a panel whose change is not
        held. Reading registers and publishes
        nothing: publishing is
        :meth:`report_panel_outcome`' road.
        """
        from ..core.review_panels import (
            load_review_panel,
            outcome_of_panel,
        )

        registry = self._review_panel_registry()
        held = (self._held_panel_change(registry) is not None
                or registry.list_reviews())
        if held:
            return registry.outcome()
        return outcome_of_panel(load_review_panel())

    def hold_panel_change(
            self, change: Any) -> dict[str, Any]:
        """Hold the panel's one change for the session (M-132).

        The change is held by the pure registry
        under its id or the deterministic change id
        - a second change refuses, and a refusal
        holds nothing new and publishes nothing -
        and a held change is published as its
        ``change_record`` session-news record
        through the checkpoint road, so evidence
        given is news with its shape attached.
        Returns the held change, its news record,
        the screen rendered after it landed, and
        the plain explanation. Holding a change
        runs no review and executes nothing: the
        registry holds the panel as data.
        """
        from ..core import review_panels

        registry = self._review_panel_registry()
        held = registry.hold_change(change)
        record = review_panels.change_record(held)
        self._publish_panel_record(record)
        return {
            "change": held.to_record(),
            "record": record,
            "screen": self._panel_screen(registry),
            "explanation": review_panels.PLAIN_EXPLANATION,
        }

    def register_panel_review(
            self, review: Any) -> dict[str, Any]:
        """Hold one panel review for the session (M-132).

        The review is held by the pure registry
        under its id or a fresh deterministic one -
        a supplied id already held refuses, a
        reviewer reporting twice refuses, a second
        review riding a model already ridden
        refuses, a third review refuses, and a
        refusal holds nothing new and publishes
        nothing - and a held review is published as
        its ``review_record`` session-news record
        through the checkpoint road. Returns the
        held review, its news record, the screen
        rendered after it landed, and the plain
        explanation. Holding a review runs no
        review and calls no model: the registry
        holds the panel as data.
        """
        from ..core import review_panels

        registry = self._review_panel_registry()
        held = registry.register_review(review)
        record = review_panels.review_record(held)
        self._publish_panel_record(record)
        return {
            "review": held.to_record(),
            "record": record,
            "screen": self._panel_screen(registry),
            "explanation": review_panels.PLAIN_EXPLANATION,
        }

    def record_review_panel(
            self, panel: Any = None) -> dict[str, Any]:
        """Record a whole review panel for the session (M-132).

        With no panel named, the shipped example
        panel is recorded through the pure layer -
        the session-branching restore guard, two
        reviews on two different models, a
        disagreement surfaced. A panel loaded from
        a file (the pure layer's
        ``load_review_panel_file`` road) may be
        passed instead, so a real panel is recorded
        as it stands. The change and every review
        are held in panel order and published as
        their ``change_record`` / ``review_record``
        session news, deduped per piece id; the
        panel is remembered as the session's panel,
        and the same panel recorded twice refuses -
        a panel is recorded once, never duplicated
        into the session. Returns the held change
        and reviews, their news records, the count
        of pieces held, the screen, and the
        explanation. Recording runs no review,
        calls no model, executes no change and
        spawns no crew.
        """
        from ..core import review_panels

        panel = panel if panel is not None \
            else review_panels.load_review_panel()
        fingerprint = (
            (panel.change.title, panel.change.summary)
            if panel.change is not None else None,
            tuple((r.reviewer, r.provider, r.model,
                   r.verdict, r.notes)
                  for r in panel.reviews))
        recorded = getattr(self, "_review_panel_recorded", None)
        if recorded is None:
            recorded = set()
            self._review_panel_recorded = recorded
        if fingerprint in recorded:
            raise ValueError(
                "this review panel is already recorded for "
                "the session; a panel is recorded once")
        registry = self._review_panel_registry()
        held_panel = registry.register_panel(panel)
        recorded.add(fingerprint)
        self._review_panel_held = panel
        records = [
            review_panels.change_record(held_panel.change)]
        records += [
            review_panels.review_record(r)
            for r in held_panel.reviews]
        for record in records:
            self._publish_panel_record(record)
        return {
            "change": held_panel.change.to_record(),
            "reviews": [
                r.to_record() for r in held_panel.reviews],
            "records": records,
            "count": len(records),
            "screen": review_panels.format_panel_screen(
                registry),
            "explanation": review_panels.PLAIN_EXPLANATION,
        }

    def report_panel_outcome(self) -> dict[str, Any]:
        """Report the panel's outcome as session news (M-132).

        The outcome is derived from what the session
        holds by :meth:`panel_outcome` and published
        as ONE ``outcome_record`` session event -
        the panel's one derived outcome, naming both
        positions when the reviewers disagree, never
        one event per review. The announcement is
        deduped: reporting again while the same
        reviews are held publishes nothing new, and
        an outcome grown by a newly held review
        announces as the new outcome it is. Returns
        the outcome, its news record, its
        completeness, the outcome screen, and the
        plain explanation. Reporting runs no review,
        calls no model, executes no change and
        spawns no crew: the human acts on the
        outcome through later roads.
        """
        from ..core import review_panels

        outcome = self.panel_outcome()
        record = review_panels.outcome_record(outcome)
        self._publish_panel_outcome_record(record)
        registry = self._review_panel_registry()
        if self._held_panel_change(registry) is not None:
            screen = review_panels.format_outcome(registry)
        else:
            screen = review_panels.format_outcome()
        return {
            "outcome": outcome.to_record(),
            "record": record,
            "complete": outcome.complete,
            "screen": screen,
            "explanation": review_panels.PLAIN_EXPLANATION,
        }

    def _publish_panel_record(self, record: dict[str, Any]) -> None:
        """Publish one piece of the panel as session news (M-132).

        The pure layer's ``change_record`` and
        ``review_record`` are journaled through the
        same checkpoint road every sibling slice
        uses, when a session is attached. Each piece
        is announced at most once, under its own id.
        A foreign record type is never published on
        this road.
        """
        if record.get("type") == "panel_change":
            key = ("panel_change", record.get("change_id"))
        elif record.get("type") == "panel_review":
            key = ("panel_review", record.get("review_id"))
        else:
            return
        announced = getattr(self, "_panel_announced", None)
        if announced is None:
            announced = set()
            self._panel_announced = announced
        if key in announced:
            return
        announced.add(key)
        if self._session_store and self.session_id:
            self._checkpoint(record)

    def _publish_panel_outcome_record(
            self, record: dict[str, Any]) -> None:
        """Publish one panel outcome as session news (M-132).

        The pure layer's ``outcome_record`` is
        journaled through the same checkpoint road,
        when a session is attached - ONE event
        holding the whole derived outcome, so the
        human is told once. Each outcome is
        announced at most once: the announcement is
        keyed by the outcome's whole shape (title,
        kind, verdict, reviewers, verdicts,
        completeness), so an outcome grown by a
        newly held review announces again as the
        new outcome it is. A foreign record type is
        never published on this road.
        """
        if record.get("type") != "panel_outcome":
            return
        announced = getattr(
            self, "_panel_outcome_announced", None)
        if announced is None:
            announced = set()
            self._panel_outcome_announced = announced
        key = (
            record.get("title"), record.get("outcome"),
            record.get("verdict"),
            tuple(record.get("reviewers", [])),
            tuple(record.get("verdicts", [])),
            record.get("complete"))
        if key in announced:
            return
        announced.add(key)
        if self._session_store and self.session_id:
            self._checkpoint(record)



    # -- M-133: crew memory --

    def _crew_memory_registry(self):
        """The held crew-memory registry (M-133).

        The registry lives in the agent layer alone -
        it is session state, not a stored setting -
        and holds the pure-layer notebooks entry by
        entry, beside the session review-panel
        registry (M-132) and never in it: the memory
        is what the crew has learned, held under the
        memory this slice names. It is created on
        first use, so an agent whose ``__init__``
        never ran still holds exactly one. The
        attribute is named ``_crew_memory_store``,
        never the method's own name (the M-108
        lesson).
        """
        registry = getattr(self, "_crew_memory_store", None)
        if registry is None:
            from ..core.crew_memory import (
                CrewMemoryRegistry,
            )
            registry = CrewMemoryRegistry()
            self._crew_memory_store = registry
        return registry

    def crew_memory(self):
        """The session's crew memory, as data (M-133).

        The held registry's union view when the
        session holds any entry - the memory the
        session has actually gathered - otherwise
        the memory recorded whole through
        :meth:`record_crew_memory`, or the shipped
        example memory until one is recorded.
        Reading registers and publishes nothing.
        """
        from ..core.crew_memory import load_crew_memory

        registry = self._crew_memory_registry()
        if registry.list_entries():
            return registry.memory()
        memory = getattr(self, "_crew_memory_held", None)
        if memory is None:
            return load_crew_memory()
        return memory

    def crew_memory_status(self) -> dict[str, Any]:
        """The crew memory, in plain data (M-133).

        The entries and notebooks held this session
        as plain records, the session memory's pieces
        as plain records (the shipped example memory
        - the auditor's broken-checkpoint-chain fact,
        the guardian's portaudio-env-import fact and
        the scribe's verify-remote-moved fact - until
        entries are held), its whole-memory record,
        the one screen - rendered from the held
        registry, or from the shipped example memory
        when nothing is held yet - and the plain
        explanation. Reading registers and publishes
        nothing, persists nothing, syncs nothing and
        spawns no crew: this layer holds the memory
        as data only. There is no Part VIII board
        yet; the screen is where the memory is
        visible.
        """
        from ..core import crew_memory as crew_memory_module

        registry = self._crew_memory_registry()
        held_entries = registry.list_entries()
        held_notebooks = registry.list_notebooks()
        memory = self.crew_memory()
        if held_entries:
            screen = crew_memory_module.format_memory_screen(
                registry)
        else:
            screen = crew_memory_module.format_memory_screen()
        return {
            "entries": [e.to_record() for e in held_entries],
            "notebooks": [
                n.to_record() for n in held_notebooks],
            "memory": {
                "members": list(memory.members()),
                "entries": [
                    e.to_record() for e in memory.entries()],
                "notebooks": [
                    n.to_record() for n in memory.notebooks],
            },
            "memory_record": crew_memory_module.memory_record(
                memory),
            "screen": screen,
            "explanation": crew_memory_module.PLAIN_EXPLANATION,
        }

    def get_memory_entry(self, entry_id: Any):
        """The one entry an id names (M-133).

        The session's held registry answers when the
        session holds any entry; otherwise the
        shipped example memory answers. A held
        session answers for its own memory alone: an
        entry the held memory does not hold raises
        KeyError, with no silent fall back to the
        example, exactly as the pure layer answers.
        Reading registers and publishes nothing.
        """
        from ..core.crew_memory import load_crew_memory

        registry = self._crew_memory_registry()
        if registry.list_entries():
            return registry.get_entry(entry_id)
        return load_crew_memory().entry_for(entry_id)

    def search_crew_memory(
            self, query: Any, asking_member: Any = None):
        """Search the shared memory, findable by all (M-133).

        The session's held registry answers when the
        session holds any entry; otherwise the
        shipped example memory answers. The asking
        member, when named, is validated and then
        deliberately does not narrow the search: a
        fact recorded by one member is found when
        queried as another. Reading registers and
        publishes nothing.
        """
        from ..core.crew_memory import (
            load_crew_memory,
            search_memory,
        )

        registry = self._crew_memory_registry()
        if registry.list_entries():
            return registry.search(
                query, asking_member=asking_member)
        return search_memory(
            load_crew_memory(), query,
            asking_member=asking_member)

    def find_memory_entries_by_tag(self, tag: Any):
        """Every entry carrying one tag (M-133).

        The session's held registry answers when the
        session holds any entry; otherwise the
        shipped example memory answers. Reading
        registers and publishes nothing.
        """
        from ..core.crew_memory import (
            find_entries,
            load_crew_memory,
        )

        registry = self._crew_memory_registry()
        if registry.list_entries():
            return registry.find_by_tag(tag)
        return find_entries(load_crew_memory(), tag)

    def register_memory_entry(
            self, entry: Any) -> dict[str, Any]:
        """Hold one memory entry for the session (M-133).

        The entry is held by the pure registry in
        its member's notebook, under its id or the
        deterministic entry-N id - a duplicate entry
        id anywhere refuses, the same fact already
        standing in that member's notebook refuses,
        and a refusal holds nothing new and publishes
        nothing - and a held entry is published as
        its ``entry_record`` session-news record
        through the checkpoint road, so a fact given
        is news with its shape attached. Returns the
        held entry, its news record, the screen
        rendered after it landed, and the plain
        explanation. Holding an entry persists
        nothing and calls no model: the registry
        holds the memory as data.
        """
        from ..core import crew_memory as crew_memory_module

        registry = self._crew_memory_registry()
        held = registry.register_entry(entry)
        record = crew_memory_module.entry_record(held)
        self._publish_memory_record(record)
        return {
            "entry": held.to_record(),
            "record": record,
            "screen": crew_memory_module.format_memory_screen(
                registry),
            "explanation": crew_memory_module.PLAIN_EXPLANATION,
        }

    def record_member_notebook(
            self, notebook: Any) -> dict[str, Any]:
        """Record one member's notebook for the session (M-133).

        The notebook is held whole by the pure
        registry - a member who already holds a
        notebook here refuses, a duplicate entry id
        anywhere refuses, the same fact twice in the
        notebook refuses, and a refusal holds nothing
        new and publishes nothing - and every held
        entry is published as its ``entry_record``
        session-news record through the checkpoint
        road, in notebook order. Returns the held
        notebook, its entries, their news records,
        the count of entries held, the screen, and
        the plain explanation. Recording persists
        nothing and spawns no crew.
        """
        from ..core import crew_memory as crew_memory_module

        registry = self._crew_memory_registry()
        held = registry.register_notebook(notebook)
        records = [
            crew_memory_module.entry_record(entry)
            for entry in held.entries]
        for record in records:
            self._publish_memory_record(record)
        return {
            "notebook": held.to_record(),
            "entries": [e.to_record() for e in held.entries],
            "records": records,
            "count": len(records),
            "screen": crew_memory_module.format_memory_screen(
                registry),
            "explanation": crew_memory_module.PLAIN_EXPLANATION,
        }

    def record_crew_memory(
            self, memory: Any = None) -> dict[str, Any]:
        """Record a whole crew memory for the session (M-133).

        With no memory named, the shipped example
        memory is recorded through the pure layer -
        the auditor's, guardian's and scribe's
        notebooks, three facts findable by all. A
        memory loaded from a file (the pure layer's
        ``load_crew_memory_file`` road) may be passed
        instead, so a real memory is recorded as it
        stands. Every entry is held and published as
        its ``entry_record`` session news, in shared
        order; the memory is remembered as the
        session's, and the same memory recorded twice
        refuses - fingerprinted on its entry ids - a
        memory is recorded once, never duplicated
        into the session. Returns the held memory,
        its entries, their news records, the count of
        entries held, the screen, and the explanation.
        Recording persists nothing, syncs nothing and
        spawns no crew.
        """
        from ..core import crew_memory as crew_memory_module

        memory = memory if memory is not None \
            else crew_memory_module.load_crew_memory()
        fingerprint = tuple(
            entry.entry_id for entry in memory.entries())
        recorded = getattr(self, "_crew_memory_recorded", None)
        if recorded is None:
            recorded = set()
            self._crew_memory_recorded = recorded
        if fingerprint in recorded:
            raise ValueError(
                "this crew memory is already recorded for "
                "the session; a memory is recorded once")
        registry = self._crew_memory_registry()
        held_memory = registry.register_memory(memory)
        recorded.add(fingerprint)
        self._crew_memory_held = memory
        records = [
            crew_memory_module.entry_record(entry)
            for entry in held_memory.entries()]
        for record in records:
            self._publish_memory_record(record)
        return {
            "memory": held_memory.to_record(),
            "entries": [
                e.to_record() for e in held_memory.entries()],
            "records": records,
            "count": len(records),
            "screen": crew_memory_module.format_memory_screen(
                registry),
            "explanation": crew_memory_module.PLAIN_EXPLANATION,
        }

    def report_crew_memory(self) -> dict[str, Any]:
        """Report the crew memory as session news (M-133).

        The memory the session holds - the held
        registry's union view, or the session memory
        (the shipped example until one is recorded) -
        is published as ONE ``memory_record`` session
        event holding the whole memory, never one
        event per entry. The announcement is deduped
        per whole memory shape: reporting again while
        the same memory is held publishes nothing
        new, and a memory grown by a newly held entry
        announces as the new memory it is. Returns
        the memory, its news record, its entry count,
        the screen, and the plain explanation.
        Reporting persists nothing, syncs nothing and
        spawns no crew: the human acts on the memory
        through later roads.
        """
        from ..core import crew_memory as crew_memory_module

        memory = self.crew_memory()
        record = crew_memory_module.memory_record(memory)
        self._publish_memory_report_record(record)
        registry = self._crew_memory_registry()
        if registry.list_entries():
            screen = crew_memory_module.format_memory_screen(
                registry)
        else:
            screen = crew_memory_module.format_memory_screen()
        return {
            "memory": memory.to_record(),
            "record": record,
            "entry_count": len(memory.entries()),
            "screen": screen,
            "explanation": crew_memory_module.PLAIN_EXPLANATION,
        }

    def _publish_memory_record(self, record: dict[str, Any]) -> None:
        """Publish one memory entry as session news (M-133).

        The pure layer's ``entry_record`` is journaled
        through the same checkpoint road every sibling
        slice uses, when a session is attached. Each
        entry is announced at most once, under its own
        id. A foreign record type is never published
        on this road.
        """
        if record.get("type") != "crew_memory_entry":
            return
        announced = getattr(self, "_memory_announced", None)
        if announced is None:
            announced = set()
            self._memory_announced = announced
        key = ("crew_memory_entry", record.get("entry_id"))
        if key in announced:
            return
        announced.add(key)
        if self._session_store and self.session_id:
            self._checkpoint(record)

    def _publish_memory_report_record(
            self, record: dict[str, Any]) -> None:
        """Publish one whole crew memory as session news (M-133).

        The pure layer's ``memory_record`` is journaled
        through the same checkpoint road, when a session
        is attached - ONE event holding the whole shared
        memory, so the human is told once. Each memory
        is announced at most once: the announcement is
        keyed by the memory's whole shape (its members,
        its entry ids, its entry count), so a memory
        grown by a newly held entry announces again as
        the new memory it is. A foreign record type is
        never published on this road.
        """
        if record.get("type") != "crew_memory":
            return
        announced = getattr(
            self, "_memory_report_announced", None)
        if announced is None:
            announced = set()
            self._memory_report_announced = announced
        key = (
            tuple(record.get("members", [])),
            tuple(record.get("entry_ids", [])),
            record.get("entry_count"))
        if key in announced:
            return
        announced.add(key)
        if self._session_store and self.session_id:
            self._checkpoint(record)


class AgentManager:
    """Central orchestrator for all agents, routing and dynamically instantiating subagents."""
    def __init__(self):
        subscribe("ui_chat_request", self.handle_chat_request)
        subscribe("ui_ghost_chat_request", self.handle_ghost_chat_request)
        subscribe("config_reload_requested", self._on_config_reload)
        subscribe("system_command_executed", self._on_system_command)
        
    def _on_system_command(self, command: str, args: str):
        if command == "/stop":
            for name, agent in list(AGENT_REGISTRY.items()):
                agent.cancel()
                # Keep the cancelled inputs available for lifecycle receipts in S08.
                if not hasattr(agent, "cancelled_inputs"):
                    agent.cancelled_inputs = []
                while True:
                    try:
                        pending = agent.inbox.get_nowait()
                    except queue.Empty:
                        break
                    agent.inbox.task_done()
                    if pending is None:
                        agent.inbox.put(None)
                        break
                    agent.cancelled_inputs.append(pending)
                publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\nStopped active work for {name}. You can continue.\n")
                    
    def _on_config_reload(self, config: dict):
        for name, agent in AGENT_REGISTRY.items():
            agent.config = config
            agent.rebuild_system_prompt()
            if agent.tui_app:
                agent.bind_tui(agent.tui_app)
            logging.info(f"Hot-reloaded config for live agent: {name}")
        
    def spawn_subagent(self, name: str, project_root: Path | None = None, *, policy: ToolPolicy | None = None, tui_app: Any = None) -> Agent | None:
        if name in AGENT_REGISTRY:
            existing = AGENT_REGISTRY[name]
            inherited = policy or ToolPolicy("read-only")
            if existing._turn_lock.locked() or (project_root is not None and existing.project_root != Path(project_root).resolve()):
                logging.warning("Agent is busy or belongs to another workspace; delegation refused")
                return None
            existing.tool_policy = inherited.fork()
            existing._permission_override = inherited.mode
            existing.tui_app = tui_app
            _route = _role_route_for(config_manager.load_config(), name)
            if _route is not None:
                existing.config["model"] = _route.model
                existing.config["base_url"] = _route.base_url
            if tui_app:
                existing.bind_tui(tui_app, mode=inherited.mode)
            return existing
            
        config = config_manager.load_config()
        sub_agents = config.get("sub_agents", [])
        sub_config = next((s for s in sub_agents if s.get("name") == name), None)
        
        if not sub_config:
            logging.error(f"Cannot spawn unknown subagent: {name}")
            return None
            
        logging.info(f"Dynamically spawning subagent: {name}")
        sub_agent = Agent(project_root=project_root, name=name)
        _route = _role_route_for(config, name)
        if _route is not None:
            sub_agent.config["model"] = _route.model
            sub_agent.config["base_url"] = _route.base_url
        sub_agent.tool_policy = (policy or ToolPolicy("read-only")).fork()
        sub_agent._permission_override = sub_agent.tool_policy.mode
        if tui_app:
            sub_agent.bind_tui(tui_app, mode=sub_agent.tool_policy.mode)
        AGENT_REGISTRY[name] = sub_agent
        from ..core.thread_audit import THREAD_REGISTRY
        sub_thread = threading.Thread(target=self._run_agent_loop, args=(sub_agent,),
                                      name=f"mythic-subagent-loop:{name}", daemon=True)
        THREAD_REGISTRY.assert_single_owner(f"mythic-subagent-loop:{name}")
        sub_thread.start()
        THREAD_REGISTRY.register(sub_thread, f"mythic-subagent-loop:{name}")
        from ..core.lifecycle import register_thread
        register_thread(sub_thread, threading.Event(),
                        name=f"mythic-subagent-loop:{name}",
                        on_stop=lambda: sub_agent.inbox.put(None))
        
        # Publish creation message to UI
        publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\n[bold green]✦ A new subagent has been awakened: {name}[/bold green]\n")
        return sub_agent

    def spawn_ghost_agent(self, original_agent: Agent) -> Agent:
        ghost_name = f"[Ghost] {original_agent.name}"
        if ghost_name in AGENT_REGISTRY:
            existing = AGENT_REGISTRY[ghost_name]
            existing.tool_policy = original_agent.tool_policy.fork()
            existing._permission_override = existing.tool_policy.mode
            if original_agent.tui_app:
                existing.bind_tui(original_agent.tui_app, mode=existing.tool_policy.mode)
            return existing
            
        logging.info(f"Dynamically spawning ghost agent: {ghost_name}")
        ghost_agent = Agent(project_root=original_agent.project_root)
        ghost_agent.name = ghost_name
        ghost_agent.tool_policy = original_agent.tool_policy.fork()
        ghost_agent._permission_override = ghost_agent.tool_policy.mode
        if original_agent.tui_app:
            ghost_agent.bind_tui(original_agent.tui_app, mode=ghost_agent.tool_policy.mode)
        
        # Inherit memory context completely
        import copy
        ghost_agent.messages = original_agent.history_snapshot()
        # Re-build system prompt if needed, but it's copied in messages
        
        AGENT_REGISTRY[ghost_name] = ghost_agent
        from ..core.thread_audit import THREAD_REGISTRY
        ghost_thread = threading.Thread(target=self._run_agent_loop, args=(ghost_agent,),
                                        name=f"mythic-ghost-loop:{ghost_name}", daemon=True)
        THREAD_REGISTRY.assert_single_owner(f"mythic-ghost-loop:{ghost_name}")
        ghost_thread.start()
        THREAD_REGISTRY.register(ghost_thread, f"mythic-ghost-loop:{ghost_name}")
        from ..core.lifecycle import register_thread
        register_thread(ghost_thread, threading.Event(),
                        name=f"mythic-ghost-loop:{ghost_name}",
                        on_stop=lambda: ghost_agent.inbox.put(None))
        
        # Publish creation message to UI
        publish_sync("agent_chat_chunk", agent_name=original_agent.name, text=f"\n[bold magenta]✦ A ghost thread has been spun up to assist you: {ghost_name}[/bold magenta]\n")
        return ghost_agent

    def handle_ghost_chat_request(self, user_input: str, target_agent: str = "Primary"):
        original = AGENT_REGISTRY.get(target_agent)
        if not original:
            # Fallback to normal if it doesn't exist yet
            self.handle_chat_request(user_input, target_agent)
            return
            
        ghost = self.spawn_ghost_agent(original)
        
        # Give the ghost agent awareness of what the original agent is currently doing
        latest_work = [m for m in original.history_snapshot() if m.get("role") in ("assistant", "tool")][-3:]
        if latest_work:
            import json
            awareness = []
            for m in latest_work:
                role = m.get("role") if isinstance(m, dict) else getattr(m, "role", "")
                content = m.get("content") if isinstance(m, dict) else getattr(m, "content", None)
                tool_calls = m.get("tool_calls") if isinstance(m, dict) else getattr(m, "tool_calls", None)
                if role == "tool":
                    awareness.append(f"Tool Result: {str(content)[:200]}...")
                elif tool_calls:
                    try:
                        names = [t.function.name for t in tool_calls]
                    except Exception:
                        names = [str(tool_calls)[:100]]
                    awareness.append(f"Agent called tools: {names}")
                elif content:
                    awareness.append(f"Agent thought: {str(content)[:200]}...")
                    
            awareness_text = "\n".join(awareness)
            user_input = f"[SYSTEM: For your awareness, your original working copy is currently doing this in the background:\n{awareness_text}]\n\n{user_input}"
            
        ghost.inbox.put(user_input)

    def handle_chat_request(self, user_input: str, target_agent: str = "Primary"):
        agent = AGENT_REGISTRY.get(target_agent)
        
        if not agent and target_agent != "Primary":
            primary = AGENT_REGISTRY.get("Primary")
            root = primary.project_root if primary else None
            agent = self.spawn_subagent(target_agent, root, policy=primary.tool_policy if primary else None,
                                       tui_app=primary.tui_app if primary else None)
            
        if not agent:
            logging.error(f"Target agent {target_agent} could not be resolved.")
            publish_sync("agent_chat_error", agent_name=target_agent, error=f"Agent {target_agent} not found.")
            return
            
        agent.inbox.put(user_input)
        
    def _run_agent_loop(self, agent: "Agent"):
        while True:
            try:
                while True:
                    try:
                        prompt = agent.inbox.get()
                        if prompt is None:
                            publish_sync("agent_chat_chunk", agent_name="Primary", text=f"\n[bold red]✦ The subagent {agent.name} has been terminated and put to rest.[/bold red]\n")
                            try:
                                from ..core.lifecycle import unregister_thread
                                unregister_thread(threading.current_thread())
                            except Exception:
                                pass
                            return # Cleanly exit thread
                            
                        agent.active_task_start_time = time.time()
                        publish_sync("agent_chat_tool", agent_name=agent.name, text=f"\n[dim][~] {agent.name} began executing a background task...[/dim]")
                        publish_sync("agent_status_changed", agent_name=agent.name, is_active=True)
                        task_start = agent.active_task_start_time
                        agent.chat(prompt)
                        publish_sync("agent_chat_complete", agent_name=agent.name)

                        elapsed = time.time() - (task_start or time.time())
                        publish_sync("agent_chat_tool", agent_name=agent.name, text=f"\n[dim][+] {agent.name} finished background task in {elapsed:.1f}s.[/dim]")
                    except Exception as e:
                        logging.exception(f"Error in chat execution for {agent.name}: {e}")
                        publish_sync("agent_chat_error", agent_name=agent.name, error=str(e))
                    finally:
                        agent.active_task_start_time = None
                        publish_sync("agent_status_changed", agent_name=agent.name, is_active=False)
                        if hasattr(agent.inbox, "task_done"):
                            agent.inbox.task_done()
            except Exception as outer_e:
                logging.critical(f"FATAL THREAD ERROR in {agent.name}: {outer_e}. Resurrecting thread...")
                time.sleep(2)

# Instantiate the singleton router
agent_manager = AgentManager()
