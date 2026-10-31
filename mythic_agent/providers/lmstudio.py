"""LM Studio provider adapter (Slice R-036).

Subclass of :class:`mythic_agent.providers.openai_compat.LocalCompatProvider`
pointed at LM Studio's built-in OpenAI-compatible local server, default
``http://localhost:1234/v1``.

``api_key_env = None``: LM Studio performs no auth, so no
``Authorization`` header is ever sent — inherited from
:class:`OpenAICompatProvider._headers`, which omits the header entirely
when no key is configured.

Auth, retries, error mapping and the ``transport=`` fake-transport seam
are inherited unchanged from :class:`OpenAICompatProvider`.

M-024 (Local runtimes II) adds the discovery kindness on top of the
shared :class:`LocalCompatProvider` surface, using LM Studio's native
REST API (served at the host root, outside the ``/v1`` prefix):

* :meth:`LMStudioProvider.downloaded_models` — every model LM Studio
  has on disk, via ``GET /api/v0/models`` (each entry carries a
  ``state`` of ``loaded`` / ``not-loaded``),
* :meth:`LMStudioProvider.loaded_models` — the subset whose native
  ``state`` is ``loaded``,
* :meth:`LMStudioProvider.show_model` — one model's native detail via
  ``GET /api/v0/models/<id>``; a model the server does not have
  answers 404, surfaced as an honest not-present error,
* :meth:`LMStudioProvider.discover` — host + served + downloaded +
  loaded in one snapshot.

Honesty rule for older LM Studio builds without the native API
(``/api/v0/models`` answering 404): the native surface is recorded
as absent and the snapshot falls back to what the compatible door
itself proves — ``/v1/models`` lists the models LM Studio is
serving (its loaded models), so ``loaded`` falls back to the served
list and ``downloaded`` falls back to the served list as a floor
(LM Studio cannot serve a model it has not downloaded). Nothing is
invented beyond that floor.
"""


from __future__ import annotations

__all__ = [
    "Any",
    "LMStudioProvider",
    "Provider",
    "ProviderError",
]

import urllib.parse
from typing import Any, Callable, Optional

try:
    import httpx2
except ImportError:  # pragma: no cover - declared fallback pattern
    import httpx as httpx2  # type: ignore[no-redef]

from .base import Provider, ProviderError
from .openai_compat import LocalCompatProvider


class LMStudioProvider(LocalCompatProvider):
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

    # -- M-024 remedies -----------------------------------------------------

    def _start_remedy(self) -> str:
        return ("Start LM Studio and turn on its local server "
                "(Developer tab, Start Server, default "
                "http://localhost:1234), then try again.")

    def _absent_remedy(self, name: str) -> str:
        return (f"Download {name!r} in LM Studio's model library and "
                "load it (or enable just-in-time loading), then try "
                "again.")

    # -- native API transport seam ------------------------------------------

    def _root_get(self, path: str) -> tuple[int, Any]:
        """GET against the host root (native ``/api/v0`` routes).

        The single native-GET seam: tests stub this method instead of
        opening sockets. Live use performs one real httpx2 GET with
        the configured timeout and maps transport failures to
        :class:`ProviderError` (unreachable + the start remedy).
        """
        url = self.base_url.rsplit("/v1", 1)[0].rstrip("/") + path
        try:
            with httpx2.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=self._headers())
        except httpx2.HTTPError as exc:
            raise ProviderError(
                f"{self.name} is unreachable at {self.base_url}: "
                f"{type(exc).__name__}. {self._start_remedy()}") from exc
        try:
            return response.status_code, response.json()
        except ValueError:
            return response.status_code, None

    def _native_models(self) -> Optional[list[dict[str, Any]]]:
        """Native ``GET /api/v0/models`` entries, or None when absent.

        ``None`` means this LM Studio build does not offer the native
        API (it answered 404) — an honest unknown, kept distinct from
        an empty library, which is ``[]``.
        """
        status, body = self._root_get("/api/v0/models")
        if status == 404:
            return None
        if status != 200:
            raise ProviderError(
                f"{self.name} at {self.base_url} answered HTTP "
                f"{status} for its native model list.")
        if not isinstance(body, dict) or not isinstance(
                body.get("data"), list):
            return []
        return [entry for entry in body["data"]
                if isinstance(entry, dict) and entry.get("id")]

    # -- M-024 discovery ------------------------------------------------------

    def downloaded_models(self) -> list[str]:
        """Ids of every model LM Studio has downloaded.

        Falls back to the served list when the native API is absent
        (see the module docstring's honesty rule).
        """
        native = self._native_models()
        if native is None:
            return self.served_models()
        return [entry["id"] for entry in native]

    def loaded_models(self) -> list[str]:
        """Ids of the models loaded in memory right now.

        Falls back to the served list when the native API is absent:
        LM Studio's ``/v1/models`` lists its loaded models.
        """
        native = self._native_models()
        if native is None:
            return self.served_models()
        return [entry["id"] for entry in native
                if entry.get("state") == "loaded"]

    def model_present(self, name: str) -> bool:
        """True when ``name`` is downloaded in LM Studio."""
        wanted = (name or "").strip()
        if not wanted:
            raise ProviderError("No model name given to look for.")
        return wanted in self.downloaded_models()

    def show_model(self, name: str) -> dict[str, Any]:
        """Native detail for one model via ``GET /api/v0/models/<id>``.

        A model LM Studio does not have answers 404, surfaced as an
        honest not-present :class:`ProviderError` carrying the
        download remedy — never a silent empty dict.
        """
        wanted = (name or "").strip()
        if not wanted:
            raise ProviderError("No model name given to show.")
        status, body = self._root_get(
            "/api/v0/models/" + urllib.parse.quote(wanted, safe=""))
        if status == 404:
            raise ProviderError(
                f"Model {wanted!r} is not present in LM Studio at "
                f"{self.base_url}. " + self._absent_remedy(wanted))
        if status != 200:
            raise ProviderError(
                f"{self.name} at {self.base_url} answered HTTP "
                f"{status} for model {wanted!r}.")
        if not isinstance(body, dict):
            raise ProviderError(
                f"{self.name} returned a non-object model record "
                f"for {wanted!r}.")
        return body

    def discover(self) -> dict[str, Any]:
        """One-call snapshot: host, served, downloaded, and loaded."""
        return {"host": self.base_url,
                "served": self.served_models(),
                "downloaded": self.downloaded_models(),
                "loaded": self.loaded_models()}
