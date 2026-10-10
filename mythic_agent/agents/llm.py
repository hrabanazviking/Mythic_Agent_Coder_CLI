
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
    return (
        f"No API key configured for {base_url}. "
        f"Store one for this endpoint in settings, or export {_key_env_hint(base_url)}. "
        "Local loopback endpoints (127.0.0.1, localhost) need no key."
    )


def resolve_api_key(config: dict[str, Any], base_url: str) -> str | None:
    """Return the configured credential for an endpoint, if any.

    Checks the per-endpoint stored keys first, then the provider's
    environment variable. Returns None when nothing is configured; it is
    the caller's job to decide whether that is an error (remote) or fine
    (loopback).
    """
    stored_key = config.get("api_keys", {}).get(base_url)
    if stored_key:
        return stored_key
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


def _retry_after_seconds(exc: Exception) -> float | None:
    """Bounded Retry-After hint in seconds, or None when absent/unparseable.

    Only the numeric (delay-seconds) form is honored; HTTP-date forms are
    ignored rather than misinterpreted.
    """
    try:
        headers = getattr(getattr(exc, "response", None), "headers", None)
        if not headers:
            return None
        value = headers.get("retry-after")
        if value is None:
            return None
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return None


def _retry_delay(exc: Exception, attempt: int, settings: dict[str, Any]) -> float:
    """Capped backoff for one retry: server Retry-After wins when present."""
    cap = settings["retry_delay_cap"]
    hinted = _retry_after_seconds(exc)
    if hinted is not None:
        return min(cap, hinted)
    return min(cap, settings["retry_delay"] * 2 ** attempt)


def _is_transient(exc: Exception) -> bool:
    """Classify provider errors: retry connection issues and 408/409/429/5xx.

    Auth (401/403), bad model (404), invalid requests (400/422), and
    capability failures fail promptly and are never retried.
    """
    from openai import APIConnectionError, APIStatusError
    if isinstance(exc, APIConnectionError):
        return True
    if isinstance(exc, APIStatusError):
        return exc.status_code in (408, 409, 429) or exc.status_code >= 500
    return False


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
            return session_id

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
        
        with self._lock:
            if not self.messages:
                self.messages.append({"role": "system", "content": system_prompt})
            elif self.messages[0].get("role") == "system":
                self.messages[0]["content"] = system_prompt
            else:
                self.messages.insert(0, {"role": "system", "content": system_prompt})
        self._checkpoint({"type": "system_prompt_updated", "message": self.history_snapshot()[0]})
            
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
        import copy
        if not isinstance(model, str) or not model.strip() or not config_manager._valid_url(base_url):
            raise ValueError("Model must be nonempty and endpoint must be an HTTP(S) URL")
        if api_key is not None and not isinstance(api_key, str):
            raise ValueError("API key must be text")
        previous = copy.deepcopy(self.config)
        self.config["model"] = model
        self.config["base_url"] = base_url
        if "api_keys" not in self.config:
            self.config["api_keys"] = {}
        if api_key:
            self.config["api_keys"][base_url] = api_key
        if not self.save_config():
            self.config = previous
            raise RuntimeError("Model preference could not be saved; previous settings were preserved")
        self.redactor = SecretRedactor(self.config)
        protect_logging(self.redactor)

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
            self._append_message({"role": "user", "content": prompt + recalled})
        client = self.get_client()
        for _ in range(settings["max_tool_rounds"]):
            self._check_cancelled()
            response, streamed = self._request_response(client, settings)
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
        for attempt in range(settings["max_retries"] + 1):
            self._check_cancelled()
            try:
                return client.chat.completions.create(
                    model=self.config.get("model", config_manager.DEFAULT_MODEL),
                    messages=self.history_snapshot(), tools=get_agent_tools(),
                    stream=False, timeout=settings["request_timeout"],
                ), False
            except (APIConnectionError, APIStatusError) as exc:
                if not _is_transient(exc) or attempt == settings["max_retries"]:
                    raise
                delay = _retry_delay(exc, attempt, settings)
                publish_sync("agent_chat_tool", agent_name=self.name,
                             text=f"\nProvider temporarily unavailable; retry {attempt + 1}.\n")
                if self._cancel.wait(delay):
                    raise TurnCancelled("Turn cancelled during retry") from exc
        raise RuntimeError("Provider retry budget exhausted")

    def _request_streaming(self, client: CancellableChatClient,
                           settings: dict[str, Any]) -> Any:
        """Assemble one normalized response from SSE text/tool deltas.

        Retries apply only before the first chunk: once a partial response
        is emitted the request is never retried. Malformed or incomplete
        streams raise before any tool fragment becomes executable.
        """
        from types import SimpleNamespace
        accumulator = _StreamAccumulator(self.name)
        for attempt in range(settings["max_retries"] + 1):
            self._check_cancelled()
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
                self._checkpoint({"type": "stream_interrupted",
                                  "partial_text": accumulator.text})
                raise
            except (APIConnectionError, APIStatusError) as exc:
                if not _is_transient(exc) or accumulator.emitted \
                        or attempt == settings["max_retries"]:
                    raise
                delay = _retry_delay(exc, attempt, settings)
                publish_sync("agent_chat_tool", agent_name=self.name,
                             text=f"\nProvider temporarily unavailable; retry {attempt + 1}.\n")
                if self._cancel.wait(delay):
                    raise TurnCancelled("Turn cancelled during retry") from exc
                continue
            except Exception as exc:
                raise RuntimeError(f"Provider stream failed: {exc}") from exc
            message = accumulator.message()
            usage = accumulator._usage
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
        sub_agent.tool_policy = (policy or ToolPolicy("read-only")).fork()
        sub_agent._permission_override = sub_agent.tool_policy.mode
        if tui_app:
            sub_agent.bind_tui(tui_app, mode=sub_agent.tool_policy.mode)
        AGENT_REGISTRY[name] = sub_agent
        from ..core.thread_audit import THREAD_REGISTRY
        sub_thread = threading.Thread(target=self._run_agent_loop, args=(sub_agent,),
                                      name=f"mythic-subagent-loop:{name}", daemon=True)
        THREAD_REGISTRY.assert_single_owner(sub_thread.name)
        sub_thread.start()
        THREAD_REGISTRY.register(sub_thread)
        
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
        THREAD_REGISTRY.assert_single_owner(ghost_thread.name)
        ghost_thread.start()
        THREAD_REGISTRY.register(ghost_thread)
        
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
