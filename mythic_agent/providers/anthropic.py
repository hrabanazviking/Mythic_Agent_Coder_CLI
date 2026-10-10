"""Anthropic (Claude) provider adapter (Slice 35).

Native Messages API adapter: no real calls are made unless the optional
``anthropic`` SDK is installed and an API key is configured. When the SDK
is absent :meth:`AnthropicProvider.chat` raises
:class:`ProviderNotConfigured` before any network traffic.
"""


from __future__ import annotations

__all__ = [
    "AnthropicProvider",
    "Any",
    "Optional",
    "Provider",
    "ProviderError",
    "ProviderNotConfigured",
]

from typing import Any, Optional

from .base import Provider, ProviderError, ProviderNotConfigured


def _anthropic_messages(messages: list[dict[str, Any]]) -> tuple[Optional[str], list[dict[str, Any]]]:
    """Split OpenAI-style messages into (system, anthropic-messages)."""
    system_parts: list[str] = []
    converted: list[dict[str, Any]] = []
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content") or ""
        if role == "system":
            system_parts.append(str(content))
        elif role in ("user", "assistant"):
            converted.append({"role": role, "content": str(content)})
        # Tool roles are not supported natively; callers should consult
        # capabilities() before sending tool transcripts.
    system = "\n\n".join(system_parts) or None
    return system, converted


class AnthropicProvider(Provider):
    """Claude adapter over the native Anthropic Messages API."""

    name = "anthropic"
    default_model = "claude-sonnet-4-5"
    api_key_env = "ANTHROPIC_API_KEY"

    def capabilities(self) -> dict[str, bool]:
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
        system, converted = _anthropic_messages(messages)
        if not converted:
            raise ProviderError("No user/assistant messages to send")
        model = kwargs.pop("model", None) or self.model
        if not model:
            raise ProviderError("No model configured for anthropic provider")
        client = self._client()
        response = self._send(client, model=model, system=system,
                              messages=converted, **kwargs)
        return self._extract_text(response)

    def _send(self, client: Any, **params: Any) -> Any:
        """Single seam for tests to stub the network call."""
        return client.messages.create(max_tokens=params.pop("max_tokens", 1024),
                                      **params)

    @staticmethod
    def _extract_text(response: Any) -> str:
        blocks = getattr(response, "content", None) or []
        text = "".join(
            getattr(block, "text", "") or ""
            for block in blocks
            if getattr(block, "type", "") == "text")
        if not text:
            raise ProviderError("Anthropic returned no text content")
        return text
