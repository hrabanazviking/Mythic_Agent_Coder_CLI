"""LM Studio provider adapter (Slice R-036).

Subclass of :class:`mythic_agent.providers.openai_compat.OpenAICompatProvider`
pointed at LM Studio's built-in OpenAI-compatible local server, default
``http://localhost:1234/v1``.

``api_key_env = None``: LM Studio performs no auth, so no
``Authorization`` header is ever sent — inherited from
:class:`OpenAICompatProvider._headers`, which omits the header entirely
when no key is configured.

Auth, retries, error mapping and the ``transport=`` fake-transport seam
are inherited unchanged from :class:`OpenAICompatProvider`.
"""


from __future__ import annotations

__all__ = [
    "Any",
    "LMStudioProvider",
    "Provider",
    "ProviderError",
]

from typing import Any, Callable, Optional

from .base import Provider, ProviderError
from .openai_compat import OpenAICompatProvider


class LMStudioProvider(OpenAICompatProvider):
    """LM Studio local-server adapter (OpenAI chat-completions shape).

    ``name = "lmstudio"``, ``api_key_env = None``,
    ``default_model = "lmstudio-local"`` (LM Studio names models after
    their loaded identifier; pass ``model=`` to target a specific one).
    """

    name = "lmstudio"
    default_model = "lmstudio-local"
    api_key_env = None

    #: Class-level default endpoint; subclasses override this.
    base_url_default = "http://localhost:1234/v1"

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
