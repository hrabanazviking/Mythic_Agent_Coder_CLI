"""Anthropic (Claude) provider adapter (Slice 35; hardened R-029).

Native Messages API adapter: no real calls are made unless the optional
``anthropic`` SDK is installed and an API key is configured. When the SDK
is absent :meth:`AnthropicProvider.chat` raises
:class:`ProviderNotConfigured` before any network traffic.

Hardened behavior (documented; covered by
``tests/test_anthropic_hardening.py``):

* Tool transcripts (role ``"tool"`` and any other non-chat role) are
  REJECTED with :class:`ProviderError` — the adapter does not implement
  native tool calling, so ``capabilities()["tool_calling"]`` is
  ``False`` and silently dropping tool blocks would corrupt the
  transcript.
* JSON mode is unsupported: ``capabilities()["json_mode"]`` is
  ``False`` and :meth:`chat` raises :class:`ProviderError` when a
  JSON-mode parameter (``response_format``) is passed, so the emitted
  request never carries JSON-mode params.
* SDK exceptions are mapped to :class:`ProviderError` subclasses
  (:class:`AnthropicAuthError`, :class:`AnthropicRateLimitError`);
  error text is built from the exception type and status code only and
  never carries key material.
* Malformed responses (no content blocks, non-text blocks only,
  non-iterable ``content``) raise :class:`ProviderError`, never a raw
  :class:`AttributeError`/:class:`TypeError`.
* Multiple ``system`` blocks merge into one ``"\\n\\n"``-joined system
  prompt.
* The model can be overridden per call via ``chat(..., model=...)``;
  an empty model raises :class:`ProviderError`.
"""


from __future__ import annotations

__all__ = [
    "AnthropicAuthError",
    "AnthropicProvider",
    "AnthropicRateLimitError",
    "Any",
    "Optional",
    "Provider",
    "ProviderError",
    "ProviderNotConfigured",
]

from typing import Any, Optional

from .base import Provider, ProviderError, ProviderNotConfigured


class AnthropicAuthError(ProviderError):
    """The Anthropic API rejected the request's credentials (HTTP 401/403)."""


class AnthropicRateLimitError(ProviderError):
    """The Anthropic API rate-limited the request (HTTP 429)."""


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


def _anthropic_messages(messages: list[dict[str, Any]]) -> tuple[Optional[str], list[dict[str, Any]]]:
    """Split OpenAI-style messages into (system, anthropic-messages).

    Multiple ``system`` blocks merge into one ``"\\n\\n"``-joined system
    prompt. Roles other than ``system``/``user``/``assistant`` (tool
    transcripts, ``developer``, ...) are rejected with
    :class:`ProviderError`: this adapter has no native tool calling, so
    silently dropping them would corrupt the transcript. Callers must
    consult ``capabilities()`` before sending tool transcripts.
    """
    system_parts: list[str] = []
    converted: list[dict[str, Any]] = []
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content") or ""
        if role == "system":
            system_parts.append(str(content))
        elif role in ("user", "assistant"):
            converted.append({"role": role, "content": str(content)})
        else:
            raise ProviderError(
                f"Anthropic adapter does not support role {role!r}: tool "
                "transcripts cannot be sent through the native Messages API "
                "without tool definitions. capabilities()['tool_calling'] "
                "is False — strip tool messages or use a tool-capable "
                "provider before calling chat().")
    system = "\n\n".join(system_parts) or None
    return system, converted


class AnthropicProvider(Provider):
    """Claude adapter over the native Anthropic Messages API."""

    name = "anthropic"
    default_model = "claude-sonnet-4-5"
    api_key_env = "ANTHROPIC_API_KEY"

    def capabilities(self) -> dict[str, bool]:
        # Honest flags: chat() is non-streaming-capable only through the
        # raw SDK seam (kept True: the underlying API supports streams),
        # tool calling is NOT implemented by this adapter (False),
        # vision blocks are not assembled by this adapter (kept True:
        # the underlying API supports them), JSON mode is unsupported.
        return {"streaming": True, "tool_calling": False,
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
        if "response_format" in kwargs:
            raise ProviderError(
                "Anthropic adapter does not support JSON mode: "
                "capabilities()['json_mode'] is False. Remove "
                "'response_format' from the request.")
        system, converted = _anthropic_messages(messages)
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
        client = self._client()
        try:
            response = self._send(client, model=model, system=system,
                                  messages=converted, **kwargs)
        except ProviderError:
            raise
        except Exception as exc:
            raise _map_sdk_error(exc) from exc
        return self._extract_text(response)

    def _send(self, client: Any, **params: Any) -> Any:
        """Single seam for tests to stub the network call."""
        return client.messages.create(max_tokens=params.pop("max_tokens", 1024),
                                      **params)

    @staticmethod
    def _extract_text(response: Any) -> str:
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
