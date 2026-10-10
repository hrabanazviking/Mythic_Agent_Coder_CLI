"""OpenRouter provider adapter (Slice R-031).

Subclass of :class:`mythic_agent.providers.openai_compat.OpenAICompatProvider`
pointed at the OpenRouter OpenAI-compatible gateway
(``https://openrouter.ai/api/v1``).

OpenRouter identifies calling apps for its rankings/analytics through two
required-by-policy headers:

* ``HTTP-Referer`` — the caller's site URL. Default:
  ``https://github.com/hrabanazviking/Mythic_Agent_Coder_CLI``.
* ``X-Title`` — the calling app name. Default: ``Mythic Agent Coder CLI``.

Both defaults are documented here and are overridable per-instance via the
``http_referer=`` / ``x_title=`` constructor kwargs. They are sent on every
request — OpenRouter's gateway expects them unconditionally.

Auth, retries, error mapping and the fake-transport seam are inherited
unchanged from :class:`OpenAICompatProvider`.
"""


from __future__ import annotations

__all__ = [
    "Any",
    "OpenRouterProvider",
    "Provider",
    "ProviderError",
]

from typing import Any, Callable, Optional

from .base import Provider, ProviderError
from .openai_compat import OpenAICompatProvider

#: Default ``HTTP-Referer`` header value sent to OpenRouter.
#: Overridable with the ``http_referer=`` constructor kwarg.
DEFAULT_HTTP_REFERER = "https://github.com/hrabanazviking/Mythic_Agent_Coder_CLI"

#: Default ``X-Title`` header value sent to OpenRouter.
#: Overridable with the ``x_title=`` constructor kwarg.
DEFAULT_X_TITLE = "Mythic Agent Coder CLI"


class OpenRouterProvider(OpenAICompatProvider):
    """OpenRouter gateway adapter (OpenAI chat-completions shape).

    ``name = "openrouter"``, ``api_key_env = "OPENROUTER_API_KEY"``,
    ``default_model = "openrouter/auto"`` (OpenRouter's auto-router).
    """

    name = "openrouter"
    default_model = "openrouter/auto"
    api_key_env = "OPENROUTER_API_KEY"

    #: Class-level default endpoint; subclasses override this.
    base_url_default = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key_env: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 2,
        transport: Optional[Callable[..., tuple[int, Any]]] = None,
        http_referer: Optional[str] = None,
        x_title: Optional[str] = None,
    ) -> None:
        super().__init__(api_key=api_key, model=model, base_url=base_url,
                         timeout=timeout, max_retries=max_retries,
                         transport=transport)
        if api_key_env is not None:
            self.api_key_env = api_key_env
        #: OpenRouter app-identification headers (always sent).
        self.http_referer = http_referer or DEFAULT_HTTP_REFERER
        self.x_title = x_title or DEFAULT_X_TITLE

    def _headers(self) -> dict[str, str]:
        headers = super()._headers()
        headers["HTTP-Referer"] = self.http_referer
        headers["X-Title"] = self.x_title
        return headers
