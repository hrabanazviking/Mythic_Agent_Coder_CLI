"""Google (Gemini) provider adapter (Slice 35; hardened R-030; v2 M-022).

Native Gemini adapter: no real calls are made unless the optional
``google-generativeai`` SDK is installed and an API key is configured.
When the SDK is absent :meth:`GoogleProvider.chat` raises
:class:`ProviderNotConfigured` before any network traffic.

Hardened behavior (documented; covered by
``tests/test_google_hardening.py``):

* Role mapping: ``assistant`` → Gemini ``"model"``; ``system`` blocks
  merge into ``system_instruction`` (passed to
  ``GenerativeModel`` only when present, omitted entirely when absent).
* Safety-blocked responses (no ``.text`` / ``finish_reason`` SAFETY)
  and empty candidate lists raise :class:`ProviderError` with a clear
  message — never a raw :class:`ValueError`/:class:`AttributeError`
  from the SDK.
* SDK exceptions are mapped to :class:`ProviderError` subclasses
  (:class:`GoogleAuthError`, :class:`GoogleRateLimitError`); error text
  is built from the exception type and status code only and never
  carries key material.
* :meth:`_client` calls ``genai.configure(api_key=...)`` exactly once
  per call, with the provider's key.
* Structured output (slice 041): ``chat(..., generation_config={...})``
  passes the dict through to ``generate_content`` — the shape
  :mod:`mythic_agent.providers.structured_output` negotiates
  (``response_mime_type`` / ``response_schema``); a non-dict value
  raises :class:`ProviderError` before any network traffic.

All-Features slice M-022 grows this adapter into the native Gemini
dialect — handled natively, never through the OpenAI-compatible shim:

* **Function calling.** ``capabilities()["tool_calling"]`` was already
  honestly ``True`` in the registry; it is now true in fact.
  ``chat(..., tools=[...])`` accepts the normalized tool specs the
  rest of the package uses (``name`` / ``description`` /
  ``parameters``, or the ``input_schema`` spelling) and emits one
  Gemini tool with ``function_declarations``. ``tool_choice`` (alias
  ``tool_config``) accepts ``"auto"`` / ``"any"`` / ``"none"``, a
  ``{"type": "tool", "name": ...}`` dict, or a native
  ``function_calling_config`` dict, and becomes Gemini's
  ``tool_config``. Assistant messages carrying ``tool_calls`` become
  ``function_call`` parts in a ``"model"`` turn; ``tool``-role
  messages become ``function_response`` parts in a ``"user"`` turn.
  Gemini function responses are keyed by function *name* (the API
  issues no call ids), so a tool message must name its function —
  directly (``name`` / ``tool_name`` / ``function_name``) or through a
  ``tool_call_id`` that an earlier assistant ``tool_calls`` entry in
  the same conversation carried. A tool result that cannot be paired
  with a function name is rejected with :class:`ProviderError`,
  never silently dropped or degraded to anonymous text (the R-030
  degradation survives only for non-tool roles such as
  ``"developer"``). Responses surface their function calls two ways:
  :meth:`GoogleProvider.chat_with_tools` returns a
  :class:`GoogleChatResult`, and every :meth:`chat` call records them
  on ``provider.last_tool_calls``. Gemini issues no call ids, so a
  parsed call's ``id`` is its function name — the pairing key a
  generic tool loop needs, and exactly what ``function_response``
  routing consumes. A response holding text returns that text exactly
  as before; a function-call-only response makes :meth:`chat` return
  ``""`` (the calls are the answer — read ``last_tool_calls``), while
  :meth:`_extract_text` keeps its R-030 contract of raising when a
  response carries no text.
* **Long-context handling.** The shipped Gemini models are 1M-class:
  :meth:`probe_context_window` reports the model registry's window
  for the call's model (1,048,576 for every shipped Gemini model), so
  :mod:`mythic_agent.providers.context_windows` plans against the
  real window, not the 128k generic fallback. Before any client is
  built, ``chat`` estimates the prompt size with the package's
  documented ``len(text) // 4`` heuristic and *refuses* a prompt whose
  estimate exceeds the known window — with the estimate, the window,
  and the remedy in the message — instead of silently truncating the
  conversation or letting the API fail opaquely; unknown models are
  never refused on a guessed window. For genuinely long prompts,
  ``chat(..., cached_content="cachedContents/...")`` passes Gemini
  context caching through to ``generate_content`` (validated as a
  non-empty string before any client is built), and the response's
  ``cachedContentTokenCount`` is parsed into
  :attr:`GoogleChatResult.usage` as ``cached_tokens``.
* **Grounding toggles, where offered.** ``chat(..., grounding=True)``
  (alias ``google_search=True``) adds Gemini's
  ``google_search_retrieval`` tool alongside any function tools;
  ``grounding={...}`` supplies the retrieval config dict (or a native
  ``{"google_search_retrieval": {...}}`` shape). Grounding is a
  toggle, never on by default, and a malformed toggle raises
  :class:`ProviderError` before any client is built. The response's
  grounding metadata (web search queries and kin), when the API
  returns it, is surfaced as a plain dict on
  :attr:`GoogleChatResult.grounding_metadata` and on
  ``provider.last_grounding_metadata``.
"""


from __future__ import annotations

__all__ = [
    "Any",
    "ChatUsage",
    "GoogleAuthError",
    "GoogleChatResult",
    "GoogleProvider",
    "GoogleRateLimitError",
    "Optional",
    "Provider",
    "ProviderError",
    "ProviderNotConfigured",
    "ToolCall",
]

import json
from dataclasses import dataclass, field
from typing import Any, Optional

from . import model_registry
from .base import ChatUsage, Provider, ProviderError, ProviderNotConfigured, ToolCall

#: Context window claimed for a model the registry does not know.
#: This is the package's documented generic fallback (the
#: context_windows module's DEFAULT_CONTEXT_WINDOW value, mirrored
#: here to avoid an import cycle at module load); it is a planning
#: fallback, never a claim about a Gemini model, and the overflow
#: guard never refuses a prompt on its strength.
_GENERIC_FALLBACK_WINDOW = 128_000


class GoogleAuthError(ProviderError):
    """The Google API rejected the request's credentials (HTTP 401/403)."""


class GoogleRateLimitError(ProviderError):
    """The Google API rate-limited the request (HTTP 429)."""


@dataclass
class GoogleChatResult:
    """Full result of one native Gemini completion (M-022).

    ``text`` is the concatenated text parts (``""`` when the model
    answered with function calls only). ``tool_calls`` are the
    response's ``function_call`` parts, normalized to
    :class:`~mythic_agent.providers.base.ToolCall` (``id`` is the
    function name — Gemini issues no call ids). ``usage`` is the
    response's usage record when the backend reported one (cached
    content counts included), else ``None``. ``grounding_metadata``
    is the response's grounding metadata as a plain dict when the
    API returned any, else ``None``.
    """

    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage: Optional[ChatUsage] = None
    finish_reason: Optional[str] = None
    grounding_metadata: Optional[dict[str, Any]] = None


def _map_genai_error(exc: BaseException) -> ProviderError:
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
    if (status in (401, 403) or "auth" in name or "permission" in name
            or "apikey" in name or "api_key" in name):
        return GoogleAuthError(
            "Google rejected the request: authentication failed "
            f"({type(exc).__name__}). Check that GOOGLE_API_KEY is valid.")
    if (status == 429 or "ratelimit" in name or "rate_limit" in name
            or "resourceexhausted" in name):
        return GoogleRateLimitError(
            "Google rate-limited the request "
            f"({type(exc).__name__}); back off and retry later.")
    return ProviderError(
        f"Google request failed: {type(exc).__name__}")


def _safety_diagnosis(response: Any) -> str:
    """Explain a text-less Gemini response: safety block or plain emptiness."""
    reason = getattr(response, "finish_reason", None)
    if reason is None:
        candidates = getattr(response, "candidates", None) or []
        first = candidates[0] if candidates else None
        reason = getattr(first, "finish_reason", None)
    if reason is not None and "SAFETY" in str(reason).upper():
        return ("Google blocked the response for safety reasons "
                "(finish_reason=SAFETY); no text is available. "
                "Rephrase the prompt or adjust safety settings.")
    return "Google returned no text content"


def _get(obj: Any, *names: str) -> Any:
    """First present attribute/key among *names* on an SDK object or dict."""
    for name in names:
        if isinstance(obj, dict):
            if obj.get(name) is not None:
                return obj[name]
        else:
            value = getattr(obj, name, None)
            if value is not None:
                return value
    return None


def _function_call_part(call: Any) -> dict[str, Any]:
    """Normalize one assistant tool call into a Gemini function_call part."""
    if isinstance(call, ToolCall):
        call_id, name, arguments = call.id, call.name, call.arguments
    elif isinstance(call, dict):
        call_id = call.get("id") or call.get("tool_call_id") or ""
        name = call.get("name") or ""
        arguments = call.get("args", call.get("arguments",
                                              call.get("input", {})))
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
        raise ProviderError("function_call part needs a non-empty tool name")
    if not isinstance(arguments, dict):
        raise ProviderError("function_call 'args' must be a JSON object")
    return {"function_call": {"name": name, "args": arguments},
            "_pairing_id": str(call_id)}


def _function_response_value(content: Any) -> dict[str, Any]:
    """Shape a tool message's content as a function_response payload."""
    if isinstance(content, dict):
        return content
    if isinstance(content, list):
        texts = [str(part.get("text", "")) if isinstance(part, dict)
                 else str(part) for part in content]
        content = "".join(texts)
    if isinstance(content, str):
        if content.strip().startswith("{"):
            try:
                parsed = json.loads(content)
            except ValueError:
                parsed = None
            if isinstance(parsed, dict):
                return parsed
        return {"result": content}
    return {"result": str(content)}


def _message_parts(
    message: dict[str, Any],
    name_by_id: dict[str, str],
) -> list[Any]:
    """Convert one non-system message's content to Gemini parts.

    Plain string content keeps the v1 shape exactly (the string itself
    is the single part). List content maps text parts to strings,
    vision-normalized image parts (``{"type": "image", "mime_type",
    "data"}``) to Gemini inline-data dicts, and native
    ``function_call`` / ``function_response`` part dicts pass through.
    Assistant ``tool_calls`` append ``function_call`` parts and record
    their pairing ids for later tool messages.
    """
    content = message.get("content")
    parts: list[Any] = []
    if isinstance(content, list):
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                kind = part.get("type")
                if kind == "text":
                    parts.append(str(part.get("text", "")))
                elif kind == "image":
                    mime = part.get("mime_type")
                    data = part.get("data")
                    if not isinstance(mime, str) or not mime \
                            or not isinstance(data, str) or not data:
                        raise ProviderError(
                            "Gemini image parts need 'mime_type' and "
                            "'data' (the vision-normalized shape)")
                    parts.append({"mime_type": mime, "data": data})
                elif kind in ("function_call", "function_response"):
                    parts.append(dict(part))
                else:
                    raise ProviderError(
                        f"unsupported Gemini content part type {kind!r}")
            else:
                raise ProviderError(
                    "content parts must be strings or part dicts, got "
                    f"{type(part).__name__}")
    elif content:
        parts.append(str(content))
    for call in message.get("tool_calls") or []:
        wrapped = _function_call_part(call)
        pairing_id = wrapped.pop("_pairing_id")
        part = wrapped
        parts.append(part)
        name = part["function_call"]["name"]
        if pairing_id:
            name_by_id[pairing_id] = name
        name_by_id.setdefault(name, name)
    if not parts:
        parts.append(str(content or ""))
    return parts


def _gemini_contents(messages: list[dict[str, Any]]) -> tuple[Optional[str], list[dict[str, Any]]]:
    """Split OpenAI-style messages into (system_instruction, gemini contents).

    Role mapping: ``"assistant"`` → ``"model"``; ``"user"`` stays
    ``"user"``. Multiple ``system`` blocks merge into one
    ``"\\n\\n"``-joined ``system_instruction``.

    NATIVE TOOL DIALECT (M-022): assistant ``tool_calls`` become
    ``function_call`` parts; ``"tool"`` messages become
    ``function_response`` parts, paired by function name — taken from
    the message's ``name`` / ``tool_name`` / ``function_name``, or
    resolved from its ``tool_call_id`` / ``tool_use_id`` / ``id``
    against the assistant calls earlier in the same conversation
    (including the name-as-id pairing this adapter itself emits). A
    tool message that names no function and matches no earlier call
    is rejected with :class:`ProviderError` — never dropped, never
    degraded to anonymous text.

    DEGRADATION POLICY (documented behavior, non-tool roles only):
    roles other than ``system``/``assistant``/``user``/``tool`` — e.g.
    ``"developer"`` — degrade to plain ``"user"`` text parts rather
    than being silently dropped.
    """
    system_parts: list[str] = []
    contents: list[dict[str, Any]] = []
    name_by_id: dict[str, str] = {}
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content")
        if role == "system":
            if isinstance(content, list):
                content = "".join(
                    str(part.get("text", "")) if isinstance(part, dict)
                    else str(part) for part in content)
            system_parts.append(str(content or ""))
        elif role == "assistant":
            contents.append({"role": "model",
                             "parts": _message_parts(message, name_by_id)})
        elif role == "tool":
            name = (message.get("name") or message.get("tool_name")
                    or message.get("function_name") or "")
            if not name:
                ref = (message.get("tool_call_id")
                       or message.get("tool_use_id")
                       or message.get("id") or "")
                name = name_by_id.get(str(ref), "") if ref else ""
            if not name:
                raise ProviderError(
                    "Gemini function_response messages must name their "
                    "function ('name', or a 'tool_call_id' matching an "
                    "earlier assistant tool call): Gemini keys tool "
                    "results by function name, so an unnamed result "
                    "cannot be paired and is rejected, never dropped.")
            contents.append({"role": "user", "parts": [
                {"function_response": {
                    "name": str(name),
                    "response": _function_response_value(content)}}]})
        else:  # "user" and non-tool roles degrade to user text
            contents.append({"role": "user",
                             "parts": _message_parts(message, name_by_id)})
    system = "\n\n".join(system_parts) or None
    return system, contents


def _tools_param(tools: Any) -> list[dict[str, Any]]:
    """Normalize tool specs into Gemini's function_declarations tool."""
    if not isinstance(tools, list) or not tools:
        raise ProviderError("tools must be a non-empty list of tool specs")
    declarations: list[dict[str, Any]] = []
    for index, tool in enumerate(tools):
        if not isinstance(tool, dict):
            raise ProviderError(
                f"tools[{index}] must be a dict, got {type(tool).__name__}")
        spec = dict(tool)
        if "parameters" not in spec and "input_schema" in spec:
            spec["parameters"] = spec.pop("input_schema")
        else:
            spec.pop("input_schema", None)
        name = spec.get("name")
        if not isinstance(name, str) or not name:
            raise ProviderError(
                f"tools[{index}] must define a non-empty string 'name'")
        parameters = spec.get("parameters", {"type": "object"})
        if not isinstance(parameters, dict):
            raise ProviderError(
                f"tools[{index}]['parameters'] must be a JSON-schema dict")
        description = spec.get("description", "")
        if not isinstance(description, str):
            raise ProviderError(
                f"tools[{index}]['description'] must be a string")
        declarations.append({"name": name, "description": description,
                             "parameters": parameters})
    return [{"function_declarations": declarations}]


def _tool_config_param(value: Any) -> dict[str, Any]:
    """Validate a tool_choice request into Gemini's tool_config shape."""
    if isinstance(value, str):
        modes = {"auto": "AUTO", "any": "ANY", "none": "NONE"}
        if value not in modes:
            raise ProviderError(
                f"tool_choice string must be 'auto', 'any' or 'none', "
                f"got {value!r}")
        return {"function_calling_config": {"mode": modes[value]}}
    if isinstance(value, dict):
        if "function_calling_config" in value:
            config = value["function_calling_config"]
            if not isinstance(config, dict) \
                    or config.get("mode") not in ("AUTO", "ANY", "NONE"):
                raise ProviderError(
                    "tool_config 'function_calling_config' needs a "
                    "'mode' of AUTO, ANY or NONE")
            return {"function_calling_config": dict(config)}
        if "mode" in value:
            mode = str(value["mode"]).upper()
            if mode not in ("AUTO", "ANY", "NONE"):
                raise ProviderError(
                    f"tool_config mode must be AUTO, ANY or NONE, "
                    f"got {value['mode']!r}")
            config: dict[str, Any] = {"mode": mode}
            allowed = value.get("allowed_function_names")
            if allowed is not None:
                config["allowed_function_names"] = list(allowed)
            return {"function_calling_config": config}
        kind = value.get("type")
        if kind in ("auto", "any", "none"):
            return _tool_config_param(kind)
        if kind == "tool":
            name = value.get("name")
            if not isinstance(name, str) or not name:
                raise ProviderError(
                    "tool_choice {'type': 'tool'} needs a non-empty 'name'")
            return {"function_calling_config": {
                "mode": "ANY", "allowed_function_names": [name]}}
        raise ProviderError(
            f"tool_choice dict is not a recognized shape: {value!r}")
    raise ProviderError(
        f"tool_choice must be a string or dict, got {type(value).__name__}")


def _grounding_tool(value: Any) -> Optional[dict[str, Any]]:
    """Validate a grounding toggle into its google_search_retrieval tool."""
    if value is None or value is False:
        return None
    if value is True:
        return {"google_search_retrieval": {}}
    if isinstance(value, dict):
        if "google_search_retrieval" in value:
            inner = value["google_search_retrieval"]
            if not isinstance(inner, dict):
                raise ProviderError(
                    "grounding 'google_search_retrieval' must be a dict")
            return {"google_search_retrieval": dict(inner)}
        return {"google_search_retrieval": dict(value)}
    raise ProviderError(
        "grounding must be True, a retrieval-config dict, or absent; "
        f"got {type(value).__name__}")


def _estimate_prompt_tokens(messages: list[dict[str, Any]]) -> int:
    """Documented heuristic estimate: ~4 chars per token (len // 4)."""
    chars = 0
    for message in messages:
        content = message.get("content")
        if isinstance(content, str):
            chars += len(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, str):
                    chars += len(part)
                elif isinstance(part, dict):
                    chars += len(str(part.get("text", "")))
        for call in message.get("tool_calls") or []:
            args = call.arguments if isinstance(call, ToolCall) \
                else call.get("arguments", {}) if isinstance(call, dict) else {}
            chars += len(json.dumps(args, default=str))
    return chars // 4


def _parse_usage(response: Any) -> Optional[ChatUsage]:
    """Parse a response's usage metadata (cached counts included)."""
    raw = _get(response, "usage_metadata", "usageMetadata")
    if raw is None:
        return None
    def _int(*names: str) -> int:
        value = _get(raw, *names)
        return int(value) if isinstance(value, int) else 0
    return ChatUsage(
        prompt_tokens=_int("prompt_token_count", "promptTokenCount"),
        completion_tokens=_int("candidates_token_count",
                               "candidatesTokenCount"),
        total_tokens=_int("total_token_count", "totalTokenCount"),
        cached_tokens=_int("cached_content_token_count",
                           "cachedContentTokenCount"),
    )


def _grounding_dict(raw: Any) -> Optional[dict[str, Any]]:
    """Convert SDK grounding metadata (object or dict) to a plain dict."""
    if raw is None:
        return None
    if isinstance(raw, dict):
        return dict(raw)
    out: dict[str, Any] = {}
    for key in ("web_search_queries", "search_entry_point",
                "grounding_chunks", "grounding_supports",
                "retrieval_queries"):
        value = getattr(raw, key, None)
        if value is not None:
            out[key] = list(value) if isinstance(value, (list, tuple)) \
                else value
    return out or {"present": True}


def _parse_response(response: Any) -> GoogleChatResult:
    """Split a Gemini response into text / function calls / metadata."""
    candidates = _get(response, "candidates")
    if candidates is not None and not candidates:
        raise ProviderError(
            "Google returned no candidates (empty candidate list); "
            "the prompt may have been blocked or the model produced "
            "nothing.")
    usage = _parse_usage(response)
    if candidates:
        first = candidates[0]
        finish = _get(first, "finish_reason")
        grounding = _grounding_dict(_get(first, "grounding_metadata",
                                         "groundingMetadata"))
        content = _get(first, "content")
        parts = _get(content, "parts") if content is not None else None
        if parts is not None:
            text_parts: list[str] = []
            calls: list[ToolCall] = []
            for part in parts:
                if isinstance(part, dict):
                    if "text" in part:
                        text_parts.append(str(part.get("text") or ""))
                    elif "function_call" in part:
                        call = part["function_call"] or {}
                        args = call.get("args", {})
                        if not isinstance(args, dict):
                            raise ProviderError(
                                "Gemini function_call 'args' must be a "
                                "JSON object")
                        name = str(call.get("name") or "")
                        calls.append(ToolCall(id=name, name=name,
                                              arguments=args))
                    continue
                text = getattr(part, "text", None)
                if isinstance(text, str):
                    text_parts.append(text)
                    continue
                call = getattr(part, "function_call", None)
                if call is not None:
                    args = _get(call, "args") or {}
                    if not isinstance(args, dict):
                        raise ProviderError(
                            "Gemini function_call 'args' must be a "
                            "JSON object")
                    name = str(_get(call, "name") or "")
                    calls.append(ToolCall(id=name, name=name,
                                          arguments=args))
            result = GoogleChatResult(
                text="".join(text_parts), tool_calls=calls, usage=usage,
                finish_reason=str(finish) if finish is not None else None,
                grounding_metadata=grounding)
            if not result.text and not result.tool_calls \
                    and finish is not None \
                    and "SAFETY" in str(finish).upper():
                raise ProviderError(_safety_diagnosis(response))
            return result
    # No candidate parts to parse: fall back to the SDK's .text
    # accessor, keeping the R-030 safety/empty contracts.
    try:
        text = response.text
    except (AttributeError, ValueError) as exc:
        raise ProviderError(_safety_diagnosis(response)) from exc
    if not text:
        raise ProviderError(_safety_diagnosis(response))
    return GoogleChatResult(
        text=str(text), usage=usage,
        finish_reason=str(_get(response, "finish_reason"))
        if _get(response, "finish_reason") is not None else None)


class GoogleProvider(Provider):
    """Gemini adapter over the native Google Generative AI SDK (v2, M-022)."""

    name = "google"
    default_model = "gemini-2.0-flash"
    api_key_env = "GOOGLE_API_KEY"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        #: Function calls from the most recent chat call ([] when none).
        self.last_tool_calls: list[ToolCall] = []
        #: Grounding metadata from the most recent call (None when none).
        self.last_grounding_metadata: Optional[dict[str, Any]] = None
        #: Usage record from the most recent call (None when unreported).
        self.last_usage: Optional[ChatUsage] = None

    def capabilities(self) -> dict[str, bool]:
        return {"streaming": True, "tool_calling": True,
                "vision": True, "json_mode": True}

    def probe_context_window(self, model: object = None) -> int:
        """Context window (tokens) for *model* (default: this provider's).

        The model registry's documented window for known models —
        1,048,576 for every Gemini family it lists. Unknown models get
        the package's generic 128k planning fallback; that value is a
        fallback, not a claim, and the overflow guard in :meth:`chat`
        refuses prompts only on a *known* window.
        """
        name = model if isinstance(model, str) and model else self.model
        if model_registry.known(name):
            _, window = model_registry.lookup(name)
            return window
        return _GENERIC_FALLBACK_WINDOW

    def context_window(self, model: object = None) -> int:
        """Alias of :meth:`probe_context_window` for direct callers."""
        return self.probe_context_window(model)

    def _client(self) -> Any:
        try:
            import google.generativeai as genai  # type: ignore[import]
        except ImportError as exc:
            raise ProviderNotConfigured(
                "The 'google-generativeai' package is not installed. "
                "Install it with: pip install 'mythic-agent[google]' "
                "or route Gemini through an OpenAI-compatible proxy.") from exc
        if not self.api_key:
            raise ProviderNotConfigured(
                "No Google API key configured. Export GOOGLE_API_KEY "
                "or pass api_key= explicitly.")
        genai.configure(api_key=self.api_key)
        return genai

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        """Return the reply text (see chat_with_tools for function calls).

        A function-call-only response returns ``""`` here — the calls
        are the answer, recorded on ``last_tool_calls``; use
        :meth:`chat_with_tools` when the calls themselves are needed.
        A response with neither text nor function calls raises
        :class:`ProviderError`, as in v1.
        """
        result = self.chat_with_tools(messages, **kwargs)
        if result.text:
            return result.text
        if result.tool_calls:
            return ""
        raise ProviderError("Google returned no text content")

    def chat_with_tools(
        self, messages: list[dict[str, Any]], **kwargs: Any
    ) -> GoogleChatResult:
        """One native completion, returning text + function calls."""
        grounding_value = kwargs.pop("grounding", None)
        search_value = kwargs.pop("google_search", None)
        if grounding_value is not None and search_value is not None:
            raise ProviderError(
                "pass the grounding toggle once: 'grounding' and its "
                "'google_search' alias were both given")
        if grounding_value is None:
            grounding_value = search_value
        grounding_tool = _grounding_tool(grounding_value)
        if "tool_choice" in kwargs and "tool_config" in kwargs:
            raise ProviderError(
                "pass tool choice once: 'tool_choice' and its "
                "'tool_config' spelling were both given")
        cached_content = kwargs.pop("cached_content", None)
        if cached_content is not None and (
                not isinstance(cached_content, str) or not cached_content):
            raise ProviderError(
                "cached_content must be a non-empty string naming a "
                "Gemini cached content (e.g. 'cachedContents/...'), got "
                f"{cached_content!r}")
        named = kwargs.pop("model", None)
        if named == "":
            # An explicitly empty model name is bad input, not a request
            # for the default (M-003 gap audit): reject it before any
            # client is built, per the provider protocol.
            raise ProviderError("No model configured for google provider")
        model = named or self.model
        if not model:
            raise ProviderError("No model configured for google provider")
        # Long-context guard: refuse — never truncate — a prompt whose
        # estimated size exceeds the model's KNOWN window. Validation
        # happens before any client is built, like every v2 check.
        if model_registry.known(model):
            window = self.context_window(model)
            estimate = _estimate_prompt_tokens(messages)
            if estimate > window:
                raise ProviderError(
                    f"prompt estimate ~{estimate} tokens exceeds the "
                    f"known {window}-token context window of {model}; "
                    "nothing was sent and nothing was truncated — "
                    "shorten the conversation, split the task, or pass "
                    "cached_content= for a Gemini context cache "
                    "(long-context strategy is M-038's road).")
        system, contents = _gemini_contents(messages)
        if not contents:
            raise ProviderError("No user/assistant messages to send")
        generation_config = kwargs.get("generation_config")
        if generation_config is not None and not isinstance(
                generation_config, dict):
            raise ProviderError(
                "generation_config must be a dict, got "
                f"{type(generation_config).__name__}.")
        tools_payload: list[dict[str, Any]] = []
        if "tools" in kwargs:
            tools_payload.extend(_tools_param(kwargs.pop("tools")))
        if grounding_tool is not None:
            tools_payload.append(grounding_tool)
        if tools_payload:
            kwargs["tools"] = tools_payload
        if "tool_choice" in kwargs:
            kwargs["tool_config"] = _tool_config_param(
                kwargs.pop("tool_choice"))
        elif "tool_config" in kwargs:
            kwargs["tool_config"] = _tool_config_param(
                kwargs.pop("tool_config"))
        if cached_content is not None:
            kwargs["cached_content"] = cached_content
        genai = self._client()
        model_kwargs: dict[str, Any] = {}
        if system:
            model_kwargs["system_instruction"] = system
        gemini_model = genai.GenerativeModel(model, **model_kwargs)
        try:
            response = self._send(gemini_model, contents, **kwargs)
        except ProviderError:
            raise
        except Exception as exc:
            raise _map_genai_error(exc) from exc
        result = _parse_response(response)
        self.last_tool_calls = list(result.tool_calls)
        self.last_grounding_metadata = result.grounding_metadata
        self.last_usage = result.usage
        return result

    def _send(self, gemini_model: Any, contents: list[dict[str, Any]], **kwargs: Any) -> Any:
        """Single seam for tests to stub the network call."""
        return gemini_model.generate_content(contents, **kwargs)

    @staticmethod
    def _extract_text(response: Any) -> str:
        """R-030 contract: the response's text, or ProviderError.

        Function-call parts are ignored here, exactly as tool blocks
        are for Anthropic's helper; M-022's richer surface is
        :meth:`chat_with_tools`.
        """
        result = _parse_response(response)
        if not result.text:
            raise ProviderError(_safety_diagnosis(response))
        return result.text
