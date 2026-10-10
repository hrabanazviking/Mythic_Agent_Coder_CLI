"""Provider registry: resolve adapters by canonical name (Slice 35).

>>> from mythic_agent.providers.registry import get_provider, list_providers
>>> "ollama" in list_providers()
True
"""


from __future__ import annotations

__all__ = [
    "AnthropicProvider",
    "Any",
    "GoogleProvider",
    "OllamaProvider",
    "Provider",
    "ProviderNotFound",
    "get_provider",
    "list_providers",
]

from typing import Any

from .anthropic import AnthropicProvider
from .base import Provider, ProviderNotFound
from .google import GoogleProvider
from .ollama import OllamaProvider

_REGISTRY: dict[str, type[Provider]] = {
    AnthropicProvider.name: AnthropicProvider,
    GoogleProvider.name: GoogleProvider,
    OllamaProvider.name: OllamaProvider,
}

#: Friendly aliases accepted by :func:`get_provider`.
_ALIASES = {
    "claude": "anthropic",
    "gemini": "google",
    "local": "ollama",
}


def list_providers() -> list[str]:
    """Return the canonical names of all registered providers, sorted."""
    return sorted(_REGISTRY)


def get_provider(name: str, **kwargs: Any) -> Provider:
    """Instantiate the provider registered under ``name`` (case-insensitive).

    Accepts aliases (``claude``, ``gemini``, ``local``). ``kwargs`` are
    forwarded to the provider constructor (``api_key=``, ``model=``,
    ``host=`` for Ollama, ...). Raises :class:`ProviderNotFound` for
    unknown names.
    """
    key = (name or "").strip().lower()
    key = _ALIASES.get(key, key)
    provider_cls = _REGISTRY.get(key)
    if provider_cls is None:
        raise ProviderNotFound(
            f"Unknown provider {name!r}. Available: {', '.join(list_providers())}")
    return provider_cls(**kwargs)


__all__ = ["get_provider", "list_providers",
           "AnthropicProvider", "GoogleProvider", "OllamaProvider",
           "Provider", "ProviderNotFound"]
