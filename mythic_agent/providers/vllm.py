"""vLLM provider adapter (Slice R-035).

Subclass of :class:`mythic_agent.providers.openai_compat.OpenAICompatProvider`
pointed at a locally running vLLM OpenAI-compatible server, default
``http://localhost:8000/v1``.

vLLM "token-abc123" placeholder convention: vLLM's server accepts
``Authorization: Bearer <anything>`` — it validates the header's presence
and shape but never checks the value against a real key. This adapter
therefore sends ``Authorization: Bearer token-abc123`` whenever no
``api_key`` is configured (the literal placeholder string vLLM's own
examples use), and ``Bearer <api_key>`` when one is. ``api_key_env`` stays
``None`` so nothing is ever pulled from the environment by accident.

Auth handling, retries, error mapping and the ``transport=``
fake-transport seam are inherited from :class:`OpenAICompatProvider`;
only header construction is overridden.
"""


from __future__ import annotations

__all__ = [
    "Any",
    "Provider",
    "ProviderError",
    "VLLMProvider",
]

from typing import Any, Callable, Optional

from .base import Provider, ProviderError
from .openai_compat import OpenAICompatProvider

#: Placeholder bearer token sent when no api_key is configured.
#: vLLM accepts any well-formed bearer token and never validates it;
#: this is the literal placeholder vLLM's own examples document.
PLACEHOLDER_API_KEY = "token-abc123"


class VLLMProvider(OpenAICompatProvider):
    """vLLM OpenAI-server adapter (OpenAI chat-completions shape).

    ``name = "vllm"``, ``api_key_env = None``,
    ``default_model`` = the model the vLLM server was launched with.
    """

    name = "vllm"
    default_model = "vllm-local"
    api_key_env = None

    #: Class-level default endpoint; subclasses override this.
    base_url_default = "http://localhost:8000/v1"

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

    def _headers(self) -> dict[str, str]:
        # vLLM expects *some* bearer token; the placeholder satisfies the
        # header shape without pretending to be a real credential.
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key or PLACEHOLDER_API_KEY}",
        }
