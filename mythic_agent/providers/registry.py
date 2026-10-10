"""Provider registry: resolve adapters by canonical name (Slice 35).

R-026..R-040 (dusk forge 2026-10-10) grew the pantheon from 3 to 10
adapters behind the hardened Provider Contract V2.

>>> from mythic_agent.providers.registry import get_provider, list_providers
>>> "ollama" in list_providers()
True
>>> "openai" in list_providers()
True
"""


from __future__ import annotations

__all__ = [
    "AnthropicProvider",
    "Any",
    "DeepSeekProvider",
    "GenericLocalCompatProvider",
    "GoogleProvider",
    "LlamaCppProvider",
    "LMStudioProvider",
    "OllamaProvider",
    "OpenAICompatProvider",
    "OpenRouterProvider",
    "Provider",
    "ProviderNotFound",
    "VLLMProvider",
    "get_provider",
    "list_providers",
]

from typing import Any

from .anthropic import AnthropicProvider
from .base import Provider, ProviderNotFound
from .deepseek import DeepSeekProvider
from .google import GoogleProvider
from .llamacpp import LlamaCppProvider
from .lmstudio import LMStudioProvider
from .ollama import OllamaProvider
from .openai_compat import GenericLocalCompatProvider, OpenAICompatProvider
from .openrouter import OpenRouterProvider
from .vllm import VLLMProvider

_REGISTRY: dict[str, type[Provider]] = {
    AnthropicProvider.name: AnthropicProvider,
    DeepSeekProvider.name: DeepSeekProvider,
    GenericLocalCompatProvider.name: GenericLocalCompatProvider,
    GoogleProvider.name: GoogleProvider,
    LlamaCppProvider.name: LlamaCppProvider,
    LMStudioProvider.name: LMStudioProvider,
    OllamaProvider.name: OllamaProvider,
    OpenAICompatProvider.name: OpenAICompatProvider,
    OpenRouterProvider.name: OpenRouterProvider,
    VLLMProvider.name: VLLMProvider,
}

#: Friendly aliases accepted by :func:`get_provider`.
_ALIASES = {
    "claude": "anthropic",
    "gemini": "google",
    "local": "ollama",
    "gpt": "openai",
    "llama-cpp": "llama.cpp",
    "llamacpp": "llama.cpp",
    "lm-studio": "lmstudio",
}


def list_providers() -> list[str]:
    """Return the canonical names of all registered providers, sorted."""
    return sorted(_REGISTRY)


def get_provider(name: str, **kwargs: Any) -> Provider:
    """Instantiate the provider registered under ``name`` (case-insensitive).

    Accepts aliases (``claude``, ``gemini``, ``local``, ``gpt``,
    ``llamacpp``/``llama-cpp``, ``lm-studio``). ``kwargs`` are forwarded to
    the provider constructor (``api_key=``, ``model=``, ``host=`` for
    Ollama, ``base_url=`` for OpenAI-compatible adapters, ...).
    Raises :class:`ProviderNotFound` for unknown names.
    """
    key = (name or "").strip().lower()
    key = _ALIASES.get(key, key)
    provider_cls = _REGISTRY.get(key)
    if provider_cls is None:
        raise ProviderNotFound(
            f"Unknown provider {name!r}. Available: {', '.join(list_providers())}")
    return provider_cls(**kwargs)
