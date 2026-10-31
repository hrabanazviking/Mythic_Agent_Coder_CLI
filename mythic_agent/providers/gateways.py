"""Gateway provider presets (All-Features slice M-026).

M-026 makes the gateways first-class: OpenRouter (its own module,
with the browsable catalogue) and its kin — Groq, Together,
Fireworks, xAI, and Mistral — as preset subclasses of
:class:`mythic_agent.providers.openai_compat.OpenAICompatProvider`,
one per gateway, each carrying only its endpoint, key env, and
default model. Nothing else is subclassed: auth, retries, error
mapping, capabilities, and the transport seam are the shared
adapter's, unchanged.

Admission evidence (2026-10-31, this campaign): every endpoint
below was probed live from this machine — each answered HTTP 401
to an unauthenticated ``GET /models``, which is exactly a live
OpenAI-compatible gateway door asking for its bearer key.
OpenRouter's catalogue door answers 200 without a key (see
``openrouter.py``). Key env names and default models are the
vendors' own documented ones. A gateway's live model catalogue is
whatever its ``/models`` door reports at run time (M-027 owns
per-model capability truth); the registry's static model list for
each kin gateway is deliberately just its default model.
"""


from __future__ import annotations

__all__ = [
    "Any",
    "FireworksProvider",
    "GroqProvider",
    "MistralProvider",
    "Provider",
    "ProviderError",
    "TogetherProvider",
    "XAIProvider",
]

from typing import Any, Callable, Optional

from .base import Provider, ProviderError
from .openai_compat import OpenAICompatProvider


class _GatewayProvider(OpenAICompatProvider):
    """Shared shape of the M-026 kin gateways: a pure preset.

    Subclasses set ``name``, ``default_model``, ``api_key_env`` and
    ``base_url_default`` and nothing else — the preset IS the data,
    pinned against the registry entry by the registry tests.
    """

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


class GroqProvider(_GatewayProvider):
    """Groq gateway adapter. ``name = "groq"``,
    ``api_key_env = "GROQ_API_KEY"``,
    ``default_model = "llama-3.3-70b-versatile"``."""

    name = "groq"
    default_model = "llama-3.3-70b-versatile"
    api_key_env = "GROQ_API_KEY"
    base_url_default = "https://api.groq.com/openai/v1"


class TogetherProvider(_GatewayProvider):
    """Together gateway adapter. ``name = "together"``,
    ``api_key_env = "TOGETHER_API_KEY"``,
    ``default_model = "meta-llama/Llama-3.3-70B-Instruct-Turbo"``."""

    name = "together"
    default_model = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
    api_key_env = "TOGETHER_API_KEY"
    base_url_default = "https://api.together.xyz/v1"


class FireworksProvider(_GatewayProvider):
    """Fireworks gateway adapter. ``name = "fireworks"``,
    ``api_key_env = "FIREWORKS_API_KEY"``,
    ``default_model = "accounts/fireworks/models/llama-v3p3-70b-instruct"``."""

    name = "fireworks"
    default_model = "accounts/fireworks/models/llama-v3p3-70b-instruct"
    api_key_env = "FIREWORKS_API_KEY"
    base_url_default = "https://api.fireworks.ai/inference/v1"


class XAIProvider(_GatewayProvider):
    """xAI gateway adapter. ``name = "xai"``,
    ``api_key_env = "XAI_API_KEY"``, ``default_model = "grok-4"``."""

    name = "xai"
    default_model = "grok-4"
    api_key_env = "XAI_API_KEY"
    base_url_default = "https://api.x.ai/v1"


class MistralProvider(_GatewayProvider):
    """Mistral gateway adapter. ``name = "mistral"``,
    ``api_key_env = "MISTRAL_API_KEY"``,
    ``default_model = "mistral-large-latest"``."""

    name = "mistral"
    default_model = "mistral-large-latest"
    api_key_env = "MISTRAL_API_KEY"
    base_url_default = "https://api.mistral.ai/v1"
