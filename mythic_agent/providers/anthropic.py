"""Anthropic (Claude) provider adapter (Slice 35; hardened R-029; v2 M-021).

Native Messages API adapter: no real calls are made unless the optional
``anthropic`` SDK is installed and an API key is configured. When the SDK
is absent :meth:`AnthropicProvider.chat` raises
:class:`ProviderNotConfigured` before any network traffic.

Hardened behavior (R-029; covered by
``tests/test_anthropic_hardening.py``):

* SDK exceptions are mapped to :class:`ProviderError` subclasses
  (:class:`AnthropicAuthError`, :class:`AnthropicRateLimitError`);
  error text is built from the exception type and status code only and
  never carries key material.
* Malformed responses (no content blocks, non-iterable ``content``)
  raise :class:`ProviderError`, never a raw
  :class:`AttributeError`/:class:`TypeError`.
* Multiple ``system`` blocks merge into one ``"\\n\\n"``-joined system
  prompt.
* The model can be overridden per call via ``chat(..., model=...)``;
  an empty model raises :class:`ProviderError`.
* JSON mode is unsupported: ``capabilities()["json_mode"]`` is
  ``False`` and :meth:`chat` raises :class:`ProviderError` when a
  JSON-mode parameter (``response_format``) is passed, so the emitted
  request never carries JSON-mode params.

All-Features slice M-021 grows this adapter into the native v2 dialect
— handled natively, never through the OpenAI-compatible shim:

* **Tool use.** ``capabilities()["tool_calling"]`` is now ``True``.
  ``chat(..., tools=[...])`` accepts the normalized tool specs the
  rest of the package uses (``name`` / ``description`` /
  ``parameters``, or Anthropic's own ``input_schema`` spelling) and
  emits Anthropic tool definitions via
  :mod:`mythic_agent.providers.tool_negotiation`. ``tool_choice``
  accepts ``"auto"`` / ``"any"`` / ``"none"`` or a native dict.
  Assistant messages carrying ``tool_calls`` become ``tool_use``
  content blocks; ``tool``-role messages become ``tool_result``
  blocks inside a user turn — a tool message WITHOUT a tool-use id
  is still rejected with :class:`ProviderError`, never silently
  dropped. Responses surface their tool calls two ways:
  :meth:`AnthropicProvider.chat_with_tools` returns an
  :class:`AnthropicChatResult`, and every :meth:`chat` call records
  them on ``provider.last_tool_calls``. A response holding text
  returns that text exactly as before; a tool-use-only response
  makes :meth:`chat` return ``""`` (the calls are the answer —
  read ``last_tool_calls``), while :meth:`_extract_text` keeps its
  R-029 contract of raising when a response carries no text.
* **Prompt caching.** ``chat(..., prompt_cache=True)`` (alias
  ``cache_system=True``) marks the merged system prompt — and the
  last tool definition, when tools are sent — with Anthropic's
  ephemeral ``cache_control``. A single message may also carry
  ``cache_control={"type": "ephemeral"}`` (or ``cache=True``),
  which is attached to that message's last content block. Cache
  token counts the API reports (``cache_creation_input_tokens`` +
  ``cache_read_input_tokens``) are parsed into
  :attr:`AnthropicChatResult.usage` as ``cached_tokens``.
* **Extended thinking.** ``chat(..., thinking=...)`` accepts
  ``True`` (the documented default budget), an int budget, a native
  dict (``{"type": "enabled", "budget_tokens": N}`` /
  ``{"type": "disabled"}``), or a
  :class:`mythic_agent.providers.reasoning.ReasoningConfig`
  (``reasoning=`` is accepted as an alias kwarg). The budget must be
  a positive int strictly below the call's ``max_tokens`` (the
  Messages API rule); violations raise :class:`ProviderError`
  before any client is built. ``thinking`` blocks in a response are
  never concatenated into the reply text: the text is the ``text``
  blocks only, and the thinking text is available separately on
  :attr:`AnthropicChatResult.thinking`.
"""


from __future__ import annotations

__all__ = [
    "AnthropicAuthError",
    "AnthropicChatResult",
    "AnthropicProvider",
    "AnthropicRateLimitError",
    "Any",
    "ChatUsage",
    "Optional",
    "Provider",
    "ProviderError",
    "ProviderNotConfigured",
    "ToolCall",
]

import json
from dataclasses import dataclass, field
from typing import Any, Optional

from .base import ChatUsage, Provider, ProviderError, ProviderNotConfigured, ToolCall

#: Ephemeral cache marker, in Anthropic's documented shape. Always
#: copied before use — callers must never receive this dict itself.
_CACHE_CONTROL = {"type": "ephemeral"}

#: Thinking budget used when thinking is switched on without one
#: (mirrors mythic_agent.providers.reasoning.DEFAULT_THINKING_BUDGET).
_DEFAULT_THINKING_BUDGET = 1024


class AnthropicAuthError(ProviderError):
    """The Anthropic API rejected the request's credentials (HTTP 401/403)."""


class AnthropicRateLimitError(ProviderError):
    """The Anthropic API rate-limited the request (HTTP 429)."""


@dataclass
class AnthropicChatResult:
    """Full result of one native Anthropic completion (M-021).

    ``text`` is the concatenated ``text`` blocks (``""`` when the
    assistant answered with tool calls only). ``tool_calls`` are the
    response's ``tool_use`` blocks, normalized to
    :class:`~mythic_agent.providers.base.ToolCall`. ``thinking`` is
    the concatenated ``thinking`` blocks, kept separate from the
    reply text. ``usage`` is the response's usage record when the
    backend reported one (cache counts included), else ``None``.
    """

    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    thinking: str = ""
    usage: Optional[ChatUsage] = None
    stop_reason: Optional[str] = None


def _map_sdk_error(exc: BaseException) -> ProviderError:
    """Map a raw SDK exception onto a ProviderError subclass.

    The message is built from the exception *type name* and *status
    code* only — never from ``str(exc)`` — so SDK error text (which may
    echo request details) can never leak key material into our errors.
    """
    status = getattr(exc, "status_code", None)
    response = getattr(exc, "response", None)
    if status is None and response is not None:
        status = getattr(response, "status_code", None)
    name = type(exc).__name__.lower()
    if status in (401, 403) or "auth" in name or "permission" in name:
        return AnthropicAuthError(
            "Anthropic rejected the request: authentication failed "
            f"({type(exc).__name__}). Check that ANTHROPIC_API_KEY is valid.")
    if status == 429 or "ratelimit" in name or "rate_limit" in name:
        return AnthropicRateLimitError(
            "Anthropic rate-limited the request "
            f"({type(exc).__name__}); back off and retry later.")
    return ProviderError(
        f"Anthropic request failed: {type(exc).__name__}")


def _cache_control_of(message: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Return a validated cache_control dict for one message, or None."""
    marker = message.get("cache_control")
    if marker is None and message.get("cache"):
        marker = dict(_CACHE_CONTROL)
    if marker is None:
        return None
    if not isinstance(marker, dict) or marker.get("type") != "ephemeral":
        raise ProviderError(
            "cache_control must be {'type': 'ephemeral'} for the "
            f"Anthropic adapter, got {marker!r}")
    return {"type": "ephemeral"}


def _tool_use_block(call: Any) -> dict[str, Any]:
    """Normalize one assistant tool call into an Anthropic tool_use block."""
    if isinstance(call, ToolCall):
        call_id, name, arguments = call.id, call.name, call.arguments
    elif isinstance(call, dict):
        call_id = call.get("id") or call.get("tool_call_id") or ""
        name = call.get("name") or ""
        arguments = call.get("input", call.get("arguments", {}))
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments) if arguments.strip() else {}
            except ValueError as exc:
                raise ProviderError(
                    "tool call arguments are not valid JSON") from exc
    else:
        raise ProviderError(
            f"tool_calls entries must be dicts or ToolCall, got "
            f"{type(call).__name__}")
    if not isinstance(name, str) or not name:
        raise ProviderError("tool_use block needs a non-empty tool name")
    if not isinstance(arguments, dict):
        raise ProviderError("tool_use block 'input' must be a JSON object")
    return {"type": "tool_use", "id": str(call_id), "name": name,
            "input": arguments}


def _content_blocks(message: dict[str, Any]) -> Any:
    """Convert one user/assistant message's content to Anthropic shape.

    Plain string content with no tool calls and no cache marker keeps
    the v1 string shape exactly. Anything richer becomes a block list.
    """
    content = message.get("content") or ""
    calls = message.get("tool_calls") or []
    marker = _cache_control_of(message)
    if isinstance(content, list):
        blocks: list[dict[str, Any]] = []
        for part in content:
            if isinstance(part, str):
                blocks.append({"type": "text", "text": part})
            elif isinstance(part, dict):
                kind = part.get("type")
                if kind == "text":
                    blocks.append({"type": "text",
                                   "text": str(part.get("text", ""))})
                elif kind in ("tool_use", "tool_result", "image"):
                    blocks.append(dict(part))
                else:
                    raise ProviderError(
                        f"unsupported Anthropic content block type {kind!r}")
            else:
                raise ProviderError(
                    "content parts must be strings or block dicts, got "
                    f"{type(part).__name__}")
        for call in calls:
            blocks.append(_tool_use_block(call))
        if marker is not None:
            if not blocks:
                blocks.append({"type": "text", "text": ""})
            blocks[-1]["cache_control"] = marker
        return blocks
    if not calls and marker is None:
        return str(content)
    blocks = []
    if str(content):
        blocks.append({"type": "text", "text": str(content)})
    for call in calls:
        blocks.append(_tool_use_block(call))
    if marker is not None:
        if not blocks:
            blocks.append({"type": "text", "text": ""})
        blocks[-1]["cache_control"] = marker
    return blocks


def _anthropic_messages(
    messages: list[dict[str, Any]],
    prompt_cache: bool = False,
) -> tuple[Any, list[dict[str, Any]]]:
    """Split OpenAI-style messages into (system, anthropic-messages).

    Multiple ``system`` blocks merge into one ``"\\n\\n"``-joined system
    prompt — a plain string, or, when ``prompt_cache`` is set, one
    text block carrying the ephemeral cache marker.

    ``tool``-role messages become ``tool_result`` blocks in a user
    turn and must name their tool use (``tool_use_id`` /
    ``tool_call_id`` / ``id``): without an id the result cannot be
    paired with its call, so it is rejected with
    :class:`ProviderError` — never silently dropped. Roles other
    than ``system``/``user``/``assistant``/``tool`` are likewise
    rejected.
    """
    system_parts: list[str] = []
    converted: list[dict[str, Any]] = []
    for message in messages:
        role = message.get("role", "user")
        if role == "system":
            content = message.get("content") or ""
            if isinstance(content, list):
                content = "".join(
                    str(part.get("text", "")) if isinstance(part, dict)
                    else str(part) for part in content)
            system_parts.append(str(content))
        elif role in ("user", "assistant"):
            converted.append({"role": role,
                              "content": _content_blocks(message)})
        elif role == "tool":
            tool_use_id = (message.get("tool_use_id")
                           or message.get("tool_call_id")
                           or message.get("id") or "")
            if not tool_use_id:
                raise ProviderError(
                    "Anthropic tool_result messages must name their "
                    "tool use ('tool_use_id'): a tool result without "
                    "an id cannot be paired with its tool_use block "
                    "and is rejected, never dropped.")
            content = message.get("content") or ""
            block: dict[str, Any] = {
                "type": "tool_result",
                "tool_use_id": str(tool_use_id),
                "content": content if isinstance(content, list) else str(content),
            }
            if message.get("is_error"):
                block["is_error"] = True
            marker = _cache_control_of(message)
            if marker is not None:
                block["cache_control"] = marker
            converted.append({"role": "user", "content": [block]})
        else:
            raise ProviderError(
                f"Anthropic adapter does not support role {role!r}: "
                "send system/user/assistant turns, assistant tool_calls, "
                "or tool-role results carrying a tool_use_id.")
    joined = "\n\n".join(system_parts) or None
    if joined is not None and prompt_cache:
        return ([{"type": "text", "text": joined,
                  "cache_control": dict(_CACHE_CONTROL)}], converted)
    return joined, converted


def _thinking_param(value: Any, max_tokens: int) -> Optional[dict[str, Any]]:
    """Validate a thinking request into Anthropic's native shape.

    Accepts True (default budget), an int budget, a native dict, or a
    ReasoningConfig-shaped object (``mode`` / ``budget_tokens``).
    Returns None when thinking is off. An enabled budget must be a
    positive int strictly below ``max_tokens`` (the Messages API
    rule); every violation raises :class:`ProviderError`.
    """
    if value is None or value is False:
        return None
    if value is True:
        budget: Optional[int] = _DEFAULT_THINKING_BUDGET
        enabled = True
    elif isinstance(value, int) and not isinstance(value, bool):
        budget, enabled = value, True
    elif isinstance(value, dict):
        kind = value.get("type")
        if kind == "disabled":
            if "budget_tokens" in value:
                raise ProviderError(
                    "thinking {'type': 'disabled'} must not carry "
                    "budget_tokens")
            return {"type": "disabled"}
        if kind != "enabled":
            raise ProviderError(
                "thinking dict must be {'type': 'enabled', "
                f"'budget_tokens': N}} or {{'type': 'disabled'}}, got {value!r}")
        budget, enabled = value.get("budget_tokens"), True
    elif hasattr(value, "mode") and hasattr(value, "budget_tokens"):
        if value.mode == "off":
            return None
        budget, enabled = value.budget_tokens, True
    else:
        raise ProviderError(
            "thinking must be True, an int budget, a native thinking "
            f"dict, or a ReasoningConfig; got {type(value).__name__}")
    if budget is None:
        budget = _DEFAULT_THINKING_BUDGET
    if not isinstance(budget, int) or isinstance(budget, bool) or budget <= 0:
        raise ProviderError(
            f"thinking budget_tokens must be a positive int, got {budget!r}")
    if budget >= max_tokens:
        raise ProviderError(
            f"thinking budget_tokens ({budget}) must be smaller than "
            f"max_tokens ({max_tokens}) for the Anthropic Messages API; "
            "raise max_tokens or lower the thinking budget.")
    return {"type": "enabled", "budget_tokens": budget}


def _tools_param(tools: Any, prompt_cache: bool) -> list[dict[str, Any]]:
    """Normalize tool specs into Anthropic tool definitions.

    Reuses tool_negotiation's Anthropic dialect (specs may spell the
    schema ``parameters`` or ``input_schema``). When ``prompt_cache``
    is set, the last definition carries the ephemeral cache marker —
    Anthropic caches the tool list at its final definition.
    """
    if not isinstance(tools, list) or not tools:
        raise ProviderError("tools must be a non-empty list of tool specs")
    normalized: list[dict[str, Any]] = []
    for index, tool in enumerate(tools):
        if not isinstance(tool, dict):
            raise ProviderError(
                f"tools[{index}] must be a dict, got {type(tool).__name__}")
        spec = dict(tool)
        if "input_schema" in spec and "parameters" not in spec:
            spec["parameters"] = spec.pop("input_schema")
        else:
            spec.pop("input_schema", None)
        normalized.append(spec)
    from .tool_negotiation import negotiate
    probe = AnthropicProvider.__new__(AnthropicProvider)
    payload = negotiate(probe, normalized)["tools"]
    if prompt_cache and payload:
        payload[-1] = {**payload[-1],
                       "cache_control": dict(_CACHE_CONTROL)}
    return payload


def _tool_choice_param(value: Any) -> dict[str, Any]:
    """Validate a tool_choice request into Anthropic's native shape."""
    if isinstance(value, str):
        if value in ("auto", "any", "none"):
            return {"type": value}
        raise ProviderError(
            f"tool_choice string must be 'auto', 'any' or 'none', "
            f"got {value!r}")
    if isinstance(value, dict):
        kind = value.get("type")
        if kind in ("auto", "any", "none"):
            return {"type": kind}
        if kind == "tool":
            name = value.get("name")
            if not isinstance(name, str) or not name:
                raise ProviderError(
                    "tool_choice {'type': 'tool'} needs a non-empty 'name'")
            return {"type": "tool", "name": name}
        raise ProviderError(
            f"tool_choice type must be auto/any/none/tool, got {kind!r}")
    raise ProviderError(
        f"tool_choice must be a string or dict, got {type(value).__name__}")


def _parse_usage(response: Any) -> Optional[ChatUsage]:
    """Parse a response's usage record (cache counts included)."""
    usage = getattr(response, "usage", None)
    if usage is None:
        return None
    def _int(name: str) -> int:
        if isinstance(usage, dict):
            value = usage.get(name, 0)
        else:
            value = getattr(usage, name, 0)
        return int(value) if isinstance(value, int) else 0
    return ChatUsage(
        prompt_tokens=_int("input_tokens"),
        completion_tokens=_int("output_tokens"),
        cached_tokens=(_int("cache_creation_input_tokens")
                       + _int("cache_read_input_tokens")),
    )


def _extract_blocks(response: Any) -> AnthropicChatResult:
    """Split a response's content blocks into text / tools / thinking."""
    try:
        blocks = getattr(response, "content", None) or []
        text_parts: list[str] = []
        thinking_parts: list[str] = []
        calls: list[ToolCall] = []
        for block in blocks:
            kind = getattr(block, "type", "")
            if kind == "text":
                text_parts.append(getattr(block, "text", "") or "")
            elif kind == "thinking":
                thinking_parts.append(getattr(block, "thinking", "") or "")
            elif kind == "tool_use":
                arguments = getattr(block, "input", {})
                if not isinstance(arguments, dict):
                    raise ProviderError(
                        "Anthropic tool_use block 'input' must be a "
                        "JSON object")
                calls.append(ToolCall(
                    id=str(getattr(block, "id", "") or ""),
                    name=str(getattr(block, "name", "") or ""),
                    arguments=arguments))
    except ProviderError:
        raise
    except (AttributeError, TypeError) as exc:
        raise ProviderError(
            "Anthropic returned a malformed response "
            f"({type(exc).__name__}); expected a list of content blocks") from exc
    return AnthropicChatResult(
        text="".join(text_parts), tool_calls=calls,
        thinking="".join(thinking_parts), usage=_parse_usage(response),
        stop_reason=getattr(response, "stop_reason", None))


class AnthropicProvider(Provider):
    """Claude adapter over the native Anthropic Messages API (v2, M-021)."""

    name = "anthropic"
    default_model = "claude-sonnet-4-5"
    api_key_env = "ANTHROPIC_API_KEY"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        #: Tool calls from the most recent chat call ([] when none).
        self.last_tool_calls: list[ToolCall] = []

    def capabilities(self) -> dict[str, bool]:
        # Honest flags (M-021): native tool calling IS implemented by
        # this adapter now; JSON mode remains unsupported (False).
        return {"streaming": True, "tool_calling": True,
                "vision": True, "json_mode": False}

    def _client(self) -> Any:
        try:
            import anthropic  # type: ignore[import]
        except ImportError as exc:
            raise ProviderNotConfigured(
                "The 'anthropic' package is not installed. "
                "Install it with: pip install 'mythic-agent[anthropic]' "
                "or route Anthropic through an OpenAI-compatible proxy.") from exc
        if not self.api_key:
            raise ProviderNotConfigured(
                "No Anthropic API key configured. Export ANTHROPIC_API_KEY "
                "or pass api_key= explicitly.")
        return anthropic.Anthropic(api_key=self.api_key)

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        """Return the reply text (see chat_with_tools for tool calls).

        A tool-use-only response returns ``""`` here — the tool calls
        are the answer, recorded on ``last_tool_calls``; use
        :meth:`chat_with_tools` when the calls themselves are needed.
        A response with neither text nor tool calls raises
        :class:`ProviderError`, as in v1.
        """
        result = self.chat_with_tools(messages, **kwargs)
        if result.text:
            return result.text
        if result.tool_calls:
            return ""
        raise ProviderError("Anthropic returned no text content")

    def chat_with_tools(
        self, messages: list[dict[str, Any]], **kwargs: Any
    ) -> AnthropicChatResult:
        """One native completion, returning text + tool calls + thinking."""
        if "response_format" in kwargs:
            raise ProviderError(
                "Anthropic adapter does not support JSON mode: "
                "capabilities()['json_mode'] is False. Remove "
                "'response_format' from the request.")
        prompt_cache = bool(kwargs.pop("prompt_cache", False)
                            or kwargs.pop("cache_system", False))
        thinking_value = kwargs.pop("thinking", None)
        reasoning_value = kwargs.pop("reasoning", None)
        if thinking_value is not None and reasoning_value is not None:
            raise ProviderError(
                "pass thinking controls once: 'thinking' and its "
                "'reasoning' alias were both given")
        if thinking_value is None:
            thinking_value = reasoning_value
        max_tokens = kwargs.get("max_tokens", 1024)
        if not isinstance(max_tokens, int) or max_tokens <= 0:
            raise ProviderError(
                f"max_tokens must be a positive int, got {max_tokens!r}")
        thinking = _thinking_param(thinking_value, max_tokens)
        system, converted = _anthropic_messages(messages,
                                                prompt_cache=prompt_cache)
        if not converted:
            raise ProviderError("No user/assistant messages to send")
        named = kwargs.pop("model", None)
        if named == "":
            # An explicitly empty model name is bad input, not a request
            # for the default (M-003 gap audit): reject it before any
            # client is built, per the provider protocol.
            raise ProviderError("No model configured for anthropic provider")
        model = named or self.model
        if not model:
            raise ProviderError("No model configured for anthropic provider")
        if "tools" in kwargs:
            kwargs["tools"] = _tools_param(kwargs["tools"], prompt_cache)
        if "tool_choice" in kwargs:
            kwargs["tool_choice"] = _tool_choice_param(kwargs["tool_choice"])
        if thinking is not None:
            kwargs["thinking"] = thinking
        client = self._client()
        try:
            response = self._send(client, model=model, system=system,
                                  messages=converted, **kwargs)
        except ProviderError:
            raise
        except Exception as exc:
            raise _map_sdk_error(exc) from exc
        result = _extract_blocks(response)
        self.last_tool_calls = list(result.tool_calls)
        return result

    def _send(self, client: Any, **params: Any) -> Any:
        """Single seam for tests to stub the network call."""
        return client.messages.create(max_tokens=params.pop("max_tokens", 1024),
                                      **params)

    @staticmethod
    def _extract_text(response: Any) -> str:
        """R-029 contract: the response's text, or ProviderError.

        Tool-use and thinking blocks are ignored here, exactly as in
        v1; M-021's richer surface is :meth:`chat_with_tools`.
        """
        try:
            blocks = getattr(response, "content", None) or []
            text = "".join(
                getattr(block, "text", "") or ""
                for block in blocks
                if getattr(block, "type", "") == "text")
        except (AttributeError, TypeError) as exc:
            raise ProviderError(
                "Anthropic returned a malformed response "
                f"({type(exc).__name__}); expected a list of content blocks") from exc
        if not text:
            raise ProviderError("Anthropic returned no text content")
        return text
