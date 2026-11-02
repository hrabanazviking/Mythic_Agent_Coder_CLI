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

M-024 (Local runtimes II) adds the discovery kindness on top of the
shared :class:`LocalCompatProvider` surface, using llama-server's own
native routes (served at the host root, outside the ``/v1`` prefix):

* :meth:`LlamaCppProvider.served_models` — the model the server was
  launched with, via ``GET /v1/models`` (llama-server serves exactly
  one model at a time, so presence is checked against that one),
* :meth:`LlamaCppProvider.props` — the server's ``GET /props``
  record (model path, build, defaults),
* :meth:`LlamaCppProvider.discover` — host + health + served +
  model path in one snapshot; a server that is not healthy answers
  with an honest unreachable error carrying the launch remedy,
  never a snapshot dressed up as success.
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
from .openai_compat import LocalCompatProvider


class LlamaCppProvider(LocalCompatProvider):
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

    # -- M-024 remedies -----------------------------------------------------

    def _start_remedy(self) -> str:
        return ("Start the server with `llama-server -m <model.gguf>` "
                "(default http://localhost:8080), then try again.")

    def _absent_remedy(self, name: str) -> str:
        return ("llama-server serves the one model it was launched "
                f"with; restart it with `llama-server -m {name}` to "
                "serve that model.")

    # -- M-024 discovery ------------------------------------------------------

    def served_models(self) -> list[str]:
        """The served model's id via ``GET /v1/models``.

        llama-server's compatible door lists exactly the model it was
        launched with. A non-200 answer is the server's own answer,
        surfaced with its status — never dressed as unreachable.
        """
        status, body = self._http_get("/v1/models")
        if status != 200:
            raise ProviderError(
                f"{self.name} at {self.base_url} answered HTTP "
                f"{status} for its model list.")
        return self._model_ids(body)

    @staticmethod
    def _id_matches(served: str, wanted: str) -> bool:
        """True when ``wanted`` names ``served`` (basename counts).

        llama-server often reports the model's full file path as its
        id; asking for the file's basename names the same model.
        """
        if served == wanted:
            return True
        return served.rstrip("/").rsplit("/", 1)[-1] == wanted

    def model_present(self, name: str) -> bool:
        """True when ``name`` is the model llama-server is serving."""
        wanted = (name or "").strip()
        if not wanted:
            raise ProviderError("No model name given to look for.")
        return any(self._id_matches(served, wanted)
                   for served in self.served_models())

    def props(self) -> dict[str, Any]:
        """The server's native ``GET /props`` record as a dict."""
        status, body = self._http_get("/props")
        if status != 200:
            raise ProviderError(
                f"{self.name} at {self.base_url} answered HTTP "
                f"{status} for its server properties.")
        return body if isinstance(body, dict) else {}

    def discover(self) -> dict[str, Any]:
        """One-call snapshot: host, served model, and its file path.

        An unhealthy server raises the honest unreachable error —
        llama-server that is still loading a model is not ready, and
        a snapshot claiming otherwise would be a lie. A ``/props``
        failure after a healthy probe degrades to ``model_path``
        None (unknown), never to a failed discovery.
        """
        if not self.health():
            raise ProviderError(
                f"{self.name} is unreachable at {self.base_url}. "
                + self._start_remedy())
        model_path = None
        try:
            model_path = self.props().get("model_path")
        except ProviderError:
            model_path = None
        return {"host": self.base_url,
                "served": self.served_models(),
                "healthy": True,
                "model_path": model_path}

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
