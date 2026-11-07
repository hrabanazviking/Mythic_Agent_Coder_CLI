
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
                return True
            settings = runtime_settings(self.config)
            description = self.redactor.text(name + ": " + json.dumps(arguments, ensure_ascii=False))
            return prompt_approval_sync(description, app, self._cancel, settings["approval_timeout"])
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
        try:
            arguments = json.loads(call["function"]["arguments"])
            if not isinstance(arguments, dict):
                return "Tool arguments must be a JSON object."
            result = execute_tool(name, arguments, self.project_root, self.tui_app, agent=self)
            return result if isinstance(result, str) else json.dumps(result)
        except KeyboardInterrupt:
            self.cancel()
            return "Tool interrupted by user."
        except TurnCancelled:
            raise
        except Exception as exc:
            logging.warning("Tool %s failed: %s", name, type(exc).__name__)
            return f"Tool {name} failed: {exc}"

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
