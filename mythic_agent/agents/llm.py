
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
