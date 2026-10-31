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

M-026 adds the browsable catalogue: :meth:`OpenRouterProvider.catalogue`
(plus ``catalogue_entry`` / ``search_catalogue``) reads the gateway's
public ``GET /models`` door and normalises exactly what it reports.
"""


from __future__ import annotations

__all__ = [
    "Any",
    "OpenRouterProvider",
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

    # -- the browsable catalogue (M-026) -----------------------------------
    #
    # OpenRouter's catalogue door (GET /models) is public — browsing
    # needs no key — and reports each model as it stands: id, name,
    # context length, architecture (modality, input/output
    # modalities), per-token pricing as decimal strings, and the top
    # provider's max completion tokens. The normalisation below
    # carries exactly those reported fields; anything the door does
    # not report is None — unknown = unknown, never guessed
    # (per-model capability truth is M-027's road).

    def _get_json(self, path: str) -> tuple[int, Any]:
        """GET ``base_url + path``; the single seam tests stub.

        Returns ``(status, parsed_json)`` — a non-200 status is the
        gateway's own answer and is returned, not raised. A transport
        failure raises :class:`ProviderError` (unreachable + the
        remedy); a malformed JSON body on a 200 raises likewise.
        """
        url = self.base_url + path
        try:
            with httpx2.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=self._headers())
        except httpx2.HTTPError as exc:
            raise ProviderError(
                f"{self.name} is unreachable at {self.base_url}: "
                f"{type(exc).__name__}. Check your network connection, "
                "then try again.") from exc
        try:
            return response.status_code, response.json()
        except ValueError:
            if response.status_code == 200:
                raise ProviderError(
                    f"{self.name} returned malformed JSON from "
                    f"{self.base_url}.") from None
            return response.status_code, None

    @staticmethod
    def _catalogue_entry(raw: Any) -> Optional[dict[str, Any]]:
        """Normalise one raw catalogue record; None if it has no id."""
        if not isinstance(raw, dict):
            return None
        model_id = raw.get("id")
        if not isinstance(model_id, str) or not model_id:
            return None
        arch = raw.get("architecture")
        if not isinstance(arch, dict):
            arch = {}
        pricing = raw.get("pricing")
        if not isinstance(pricing, dict):
            pricing = {}
        top = raw.get("top_provider")
        if not isinstance(top, dict):
            top = {}

        def _text(value: Any) -> Optional[str]:
            return value if isinstance(value, str) and value else None

        def _count(value: Any) -> Optional[int]:
            return value if isinstance(value, int) and value > 0 else None

        def _texts(value: Any) -> Optional[list]:
            if isinstance(value, list) and value and all(
                    isinstance(v, str) for v in value):
                return list(value)
            return None

        return {
            "id": model_id,
            "name": _text(raw.get("name")),
            "context_length": _count(raw.get("context_length")),
            "modality": _text(arch.get("modality")),
            "input_modalities": _texts(arch.get("input_modalities")),
            "output_modalities": _texts(arch.get("output_modalities")),
            "prompt_price": _text(pricing.get("prompt")),
            "completion_price": _text(pricing.get("completion")),
            "max_completion_tokens": _count(
                top.get("max_completion_tokens")),
        }

    def catalogue(self) -> list[dict[str, Any]]:
        """The gateway's live model catalogue, as it reports it.

        One normalised entry per model (see :meth:`_catalogue_entry`);
        records without a usable id are skipped, never repaired.
        An unreachable gateway, a non-200 answer, or a malformed
        body is a :class:`ProviderError` saying so — browsing never
        falls back to a stale or invented list.
        """
        status, body = self._get_json("/models")
        if status != 200:
            raise ProviderError(
                f"{self.name} at {self.base_url} answered HTTP "
                f"{status} for its model catalogue.")
        if not isinstance(body, dict) or not isinstance(
                body.get("data"), list):
            raise ProviderError(
                f"{self.name} returned a malformed model catalogue "
                f"from {self.base_url}.")
        entries = []
        for raw in body["data"]:
            entry = self._catalogue_entry(raw)
            if entry is not None:
                entries.append(entry)
        return entries

    def catalogue_entry(self, model_id: str) -> dict[str, Any]:
        """One catalogue entry by exact id; absent = honest error."""
        wanted = (model_id or "").strip()
        if not wanted:
            raise ProviderError("No model id given to look up.")
        for entry in self.catalogue():
            if entry["id"] == wanted:
                return entry
        raise ProviderError(
            f"Model {wanted!r} is not in the {self.name} catalogue. "
            "Browse it with /gateway list, or search with "
            "/gateway search <text>.")

    def search_catalogue(self, query: str) -> list[dict[str, Any]]:
        """Catalogue entries whose id or name contains ``query``."""
        needle = (query or "").strip().lower()
        if not needle:
            raise ProviderError("No search text given.")
        return [entry for entry in self.catalogue()
                if needle in entry["id"].lower()
                or needle in (entry["name"] or "").lower()]
