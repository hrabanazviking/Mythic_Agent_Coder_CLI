"""Google (Gemini) provider adapter (Slice 35; hardened R-030).

Native Gemini adapter: no real calls are made unless the optional
``google-generativeai`` SDK is installed and an API key is configured.
When the SDK is absent :meth:`GoogleProvider.chat` raises
:class:`ProviderNotConfigured` before any network traffic.

Hardened behavior (documented; covered by
``tests/test_google_hardening.py``):

* Role mapping: ``assistant`` → Gemini ``"model"``; ``system`` blocks
  merge into ``system_instruction`` (passed to
  ``GenerativeModel`` only when present, omitted entirely when absent).
* Tool transcripts DEGRADE to user text (documented in
  :func:`_gemini_contents`): the adapter does not implement native
  tool calling, so tool roles arrive as plain ``"user"`` parts rather
  than being dropped or sent as tool blocks.
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
"""


from __future__ import annotations

__all__ = [
    "Any",
    "GoogleAuthError",
    "GoogleProvider",
    "GoogleRateLimitError",
    "Optional",
    "Provider",
    "ProviderError",
    "ProviderNotConfigured",
]

from typing import Any, Optional

from .base import Provider, ProviderError, ProviderNotConfigured


class GoogleAuthError(ProviderError):
    """The Google API rejected the request's credentials (HTTP 401/403)."""


class GoogleRateLimitError(ProviderError):
    """The Google API rate-limited the request (HTTP 429)."""


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


def _gemini_contents(messages: list[dict[str, Any]]) -> tuple[Optional[str], list[dict[str, Any]]]:
    """Split OpenAI-style messages into (system_instruction, gemini contents).

    Role mapping: ``"assistant"`` → ``"model"``; ``"user"`` stays
    ``"user"``. Multiple ``system`` blocks merge into one
    ``"\\n\\n"``-joined ``system_instruction``.

    DEGRADATION POLICY (documented behavior): roles other than
    ``system``/``assistant``/``user`` — e.g. ``"tool"`` transcripts or
    ``"developer"`` — degrade to plain ``"user"`` text parts. This
    adapter does not implement native Gemini tool calling, so tool
    transcripts are preserved as readable user text rather than being
    silently dropped or sent as tool blocks. Callers needing real tool
    calling must consult ``capabilities()`` and route elsewhere.
    """
    system_parts: list[str] = []
    contents: list[dict[str, Any]] = []
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content") or ""
        if role == "system":
            system_parts.append(str(content))
        elif role == "assistant":
            contents.append({"role": "model", "parts": [str(content)]})
        else:  # "user" and tool transcripts degrade to user text
            contents.append({"role": "user", "parts": [str(content)]})
    system = "\n\n".join(system_parts) or None
    return system, contents


class GoogleProvider(Provider):
    """Gemini adapter over the native Google Generative AI SDK."""

    name = "google"
    default_model = "gemini-2.0-flash"
    api_key_env = "GOOGLE_API_KEY"

    def capabilities(self) -> dict[str, bool]:
        return {"streaming": True, "tool_calling": True,
                "vision": True, "json_mode": True}

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
        system, contents = _gemini_contents(messages)
        if not contents:
            raise ProviderError("No user/assistant messages to send")
        named = kwargs.pop("model", None)
        if named == "":
            # An explicitly empty model name is bad input, not a request
            # for the default (M-003 gap audit): reject it before any
            # client is built, per the provider protocol.
            raise ProviderError("No model configured for google provider")
        model = named or self.model
        if not model:
            raise ProviderError("No model configured for google provider")
        generation_config = kwargs.get("generation_config")
        if generation_config is not None and not isinstance(
                generation_config, dict):
            raise ProviderError(
                "generation_config must be a dict, got "
                f"{type(generation_config).__name__}.")
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
        return self._extract_text(response)

    def _send(self, gemini_model: Any, contents: list[dict[str, Any]], **kwargs: Any) -> Any:
        """Single seam for tests to stub the network call."""
        return gemini_model.generate_content(contents, **kwargs)

    @staticmethod
    def _extract_text(response: Any) -> str:
        candidates = getattr(response, "candidates", None)
        if candidates is not None and not candidates:
            raise ProviderError(
                "Google returned no candidates (empty candidate list); "
                "the prompt may have been blocked or the model produced "
                "nothing.")
        try:
            text = response.text
        except (AttributeError, ValueError) as exc:
            # The real SDK raises ValueError on .text for blocked/empty
            # responses; never let that raw error reach the caller.
            raise ProviderError(_safety_diagnosis(response)) from exc
        if not text:
            raise ProviderError(_safety_diagnosis(response))
        return str(text)
