"""Google (Gemini) provider adapter (Slice 35).

Native Gemini adapter: no real calls are made unless the optional
``google-generativeai`` SDK is installed and an API key is configured.
When the SDK is absent :meth:`GoogleProvider.chat` raises
:class:`ProviderNotConfigured` before any network traffic.
"""

from __future__ import annotations

from typing import Any, Optional

from .base import Provider, ProviderError, ProviderNotConfigured


def _gemini_contents(messages: list[dict[str, Any]]) -> tuple[Optional[str], list[dict[str, Any]]]:
    """Split OpenAI-style messages into (system_instruction, gemini contents)."""
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
        model = kwargs.pop("model", None) or self.model
        if not model:
            raise ProviderError("No model configured for google provider")
        genai = self._client()
        model_kwargs: dict[str, Any] = {}
        if system:
            model_kwargs["system_instruction"] = system
        gemini_model = genai.GenerativeModel(model, **model_kwargs)
        response = self._send(gemini_model, contents, **kwargs)
        return self._extract_text(response)

    def _send(self, gemini_model: Any, contents: list[dict[str, Any]], **kwargs: Any) -> Any:
        """Single seam for tests to stub the network call."""
        return gemini_model.generate_content(contents, **kwargs)

    @staticmethod
    def _extract_text(response: Any) -> str:
        text = getattr(response, "text", None)
        if not text:
            raise ProviderError("Google returned no text content")
        return str(text)
