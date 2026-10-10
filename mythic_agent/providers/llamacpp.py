"""llama.cpp server provider adapter (Slice R-034).

Subclass of :class:`mythic_agent.providers.openai_compat.OpenAICompatProvider`
pointed at a locally running ``llama-server`` (llama.cpp's OpenAI-compatible
HTTP server), default ``http://localhost:8080/v1``.

``api_key_env = None``: llama-server performs no auth, so no
``Authorization`` header is ever sent. :meth:`health` probes the server's
native ``GET /health`` endpoint (which lives outside the ``/v1`` chat
prefix) through a stubbed ``_http_get`` seam — unit tests stub that seam
rather than opening a socket.

Auth, retries, error mapping and the ``transport=`` fake-transport seam
are inherited unchanged from :class:`OpenAICompatProvider`.
"""


from __future__ import annotations

__all__ = [
    "Any",
    "LlamaCppProvider",
    "Provider",
    "ProviderError",
]

from typing import Any, Callable, Optional

try:
    import httpx2
except ImportError:  # pragma: no cover - declared fallback pattern
    import httpx as httpx2  # type: ignore[no-redef]

from .base import Provider, ProviderError
from .openai_compat import OpenAICompatProvider


class LlamaCppProvider(OpenAICompatProvider):
    """llama.cpp ``llama-server`` adapter (OpenAI chat-completions shape).

    ``name = "llama.cpp"`` — the dotted form is registry-safe (no clash
    with any registered provider name).
    """

    name = "llama.cpp"
    default_model = "llama.cpp-local"
    api_key_env = None

    #: Class-level default endpoint; subclasses override this.
    base_url_default = "http://localhost:8080/v1"

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

    def health(self) -> bool:
        """Probe the server's ``GET /health`` endpoint; True when up.

        ``/health`` is a llama-server-native route served at the host
        root (not under ``/v1``). A 200 means the server is loaded and
        ready; anything else — or a transport failure — means it is not
        usable for completions.
        """
        try:
            status, _ = self._http_get("/health")
        except ProviderError:
            return False
        return status == 200

    def _http_get(self, path: str) -> tuple[int, Any]:
        """GET against the host root (``/v1``-prefixed chat paths excluded).

        The single GET seam: tests stub this method instead of opening
        sockets. Live use performs one real httpx2 GET with the
        configured timeout and maps failures to :class:`ProviderError`.
        """
        url = self.base_url.rsplit("/v1", 1)[0].rstrip("/") + path
        try:
            with httpx2.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=self._headers())
        except httpx2.HTTPError as exc:
            raise ProviderError(
                f"{self.name} health check failed: "
                f"{type(exc).__name__}") from exc
        try:
            return response.status_code, response.json()
        except ValueError:
            return response.status_code, None
