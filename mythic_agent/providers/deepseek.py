"""DeepSeek provider adapter (Slice R-032).

Subclass of :class:`mythic_agent.providers.openai_compat.OpenAICompatProvider`
pointed at the DeepSeek OpenAI-compatible endpoint
(``https://api.deepseek.com/v1``).

DeepSeek's reasoning models (``deepseek-reasoner``) stream their chain of
thought in a ``reasoning_content`` field alongside — or instead of — the
regular ``message.content`` field of a chat-completions response. This
adapter overrides text extraction so the assistant text falls back to
``message.reasoning_content`` when ``message.content`` is absent or empty:

* ``content`` present and non-blank → returned as-is,
* otherwise ``reasoning_content`` present and non-blank → returned,
* otherwise the usual "empty assistant text" :class:`ProviderError`.

Auth, retries, error mapping and the fake-transport seam are inherited
unchanged from :class:`OpenAICompatProvider`.
"""


from __future__ import annotations

__all__ = [
    "Any",
    "DeepSeekProvider",
    "Provider",
    "ProviderError",
]

from typing import Any, Callable, Optional

from .base import Provider, ProviderError
from .openai_compat import OpenAICompatProvider


class DeepSeekProvider(OpenAICompatProvider):
    """DeepSeek adapter (OpenAI chat-completions shape + reasoning fallback).

    ``name = "deepseek"``, ``api_key_env = "DEEPSEEK_API_KEY"``,
    ``default_model = "deepseek-chat"``.
    """

    name = "deepseek"
    default_model = "deepseek-chat"
    api_key_env = "DEEPSEEK_API_KEY"

    #: Class-level default endpoint; subclasses override this.
    base_url_default = "https://api.deepseek.com/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key_env: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 2,
        transport: Optional[Callable[..., tuple[int, Any]]] = None,
    ) -> None:
        super().__init__(api_key=api_key, model=model, base_url=base_url,
                         timeout=timeout, max_retries=max_retries,
                         transport=transport)
        if api_key_env is not None:
            self.api_key_env = api_key_env

    def _extract_text(self, body: Any, status: int) -> str:
        """Assistant text, falling back to ``reasoning_content``.

        Reasoning-only responses (e.g. from ``deepseek-reasoner`` when it
        emits no final ``content``) still carry useful text in
        ``message.reasoning_content``; use it rather than failing.
        """
        try:
            choices = body["choices"]
        except (TypeError, KeyError, IndexError):
            choices = None
        if not isinstance(choices, list) or not choices:
            raise ProviderError(
                f"{self.name} returned no choices (HTTP {status}).")
        first = choices[0]
        message = first.get("message") if isinstance(first, dict) else None
        if not isinstance(message, dict):
            raise ProviderError(
                f"{self.name} returned empty assistant text (HTTP {status}).")
        text = message.get("content")
        if not isinstance(text, str) or not text.strip():
            # Reasoning models: fall back to the chain-of-thought field.
            text = message.get("reasoning_content")
        if not isinstance(text, str) or not text.strip():
            raise ProviderError(
                f"{self.name} returned empty assistant text (HTTP {status}).")
        return text
