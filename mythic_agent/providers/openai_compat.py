"""OpenAI-compatible provider adapter (Slices 027, 028).

:class:`OpenAICompatProvider` implements :meth:`Provider.chat` over the
OpenAI ``/v1/chat/completions`` REST shape using ``httpx2`` (the venv
ships httpx2 2.13.1 and no plain httpx; the repo's declared
try/except fallback pattern is used, with httpx2 always tried first).

Transport is stdlib-shaped through one seam so tests never touch the
network: inject ``_post`` (or a ``transport=`` callable) returning
``(status_code, parsed_json_body)``.

Security rules (enforced by tests):

* the API key never appears in raised error text — any accidental echo
  of the key in a body/status is redacted,
* 401/403 map to :class:`ProviderError` auth failures,
* 429 and 5xx are retried with backoff + jitter honoring
  ``max_retries``; other 4xx map to :class:`ProviderError` carrying the
  status code but no body secrets.

Slice 028 generalizes the adapter into a reusable base:
:class:`GenericLocalCompatProvider` presets a local endpoint with no
auth header when no key is configured, and the module docstring shows
how OpenRouter / DeepSeek / local servers subclass it.

All-Features slice M-020 completes the road: the per-provider quirks
that used to live only in subclasses are declared in the provider
registry data (``mythic_agent/data/provider_registry.yaml``), and
:class:`UniversalOpenAICompatProvider` is constructed purely from a
registry entry — name, endpoint, key env, default model, capabilities,
and quirks all come from the data. One adapter therefore serves every
``openai_compatible`` door in the registry, preset-identical in its
observable behaviour (headers, text extraction, capabilities).
"""


from __future__ import annotations

__all__ = [
    "Any",
    "DEFAULT_HTTP_REFERER",
    "DEFAULT_X_TITLE",
    "GenericLocalCompatProvider",
    "OpenAICompatProvider",
    "PLACEHOLDER_API_KEY",
    "Provider",
    "ProviderDef",
    "ProviderError",
    "UniversalOpenAICompatProvider",
]

import json
import random
import time
from typing import Any, Callable, Optional

try:
    import httpx2
except ImportError:  # pragma: no cover - declared fallback pattern
    import httpx as httpx2  # type: ignore[no-redef]

from ..core.provider_registry import ProviderDef, load_registry
from .base import Provider, ProviderError

#: Default ``HTTP-Referer`` header value for the registry quirk
#: ``app-identification-headers`` (OpenRouter's app identification).
#: Matches the preset OpenRouter adapter's documented default.
DEFAULT_HTTP_REFERER = "https://github.com/hrabanazviking/Mythic_Agent_Coder_CLI"

#: Default ``X-Title`` header value for the same quirk.
DEFAULT_X_TITLE = "Mythic Agent Coder CLI"

#: Placeholder key sent for the registry quirk
#: ``placeholder-bearer-auth`` (vLLM accepts any well-formed bearer
#: value and never validates it; this is the literal placeholder
#: vLLM's own examples document).
PLACEHOLDER_API_KEY = "token-" + "abc123"


#: Statuses worth retrying: rate limits and server-side failures.
RETRIABLE_STATUSES = frozenset({408, 409, 425, 429, 500, 502, 503, 504})

_REDACTED = "***REDACTED***"


class OpenAICompatProvider(Provider):
    """OpenAI chat-completions adapter (also the base for compatibles).

    Subclassing guide (slice 028):

    * **OpenRouter**: ``base_url="https://openrouter.ai/api/v1"``,
      ``api_key_env="OPENROUTER_API_KEY"``, keep the Bearer header.
    * **DeepSeek**: ``base_url="https://api.deepseek.com/v1"``,
      ``api_key_env="DEEPSEEK_API_KEY"``.
    * **Local servers** (LM Studio, llama.cpp, vLLM, text-generation-webui):
      use :class:`GenericLocalCompatProvider` or subclass with
      ``api_key_env = None`` — no ``Authorization`` header is sent when
      no key is configured.

    Example::

        class DeepSeekProvider(OpenAICompatProvider):
            name = "deepseek"
            default_model = "deepseek-chat"
            api_key_env = "DEEPSEEK_API_KEY"
            base_url_default = "https://api.deepseek.com/v1"
    """

    name = "openai"
    default_model = "gpt-5"
    api_key_env = "OPENAI_API_KEY"

    #: Class-level default endpoint; subclasses override this.
    base_url_default = "https://api.openai.com/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 2,
        transport: Optional[Callable[..., tuple[int, Any]]] = None,
    ) -> None:
        super().__init__(api_key=api_key, model=model,
                         timeout=timeout, max_retries=max_retries)
        self.base_url = (base_url or self.base_url_default).rstrip("/")
        #: Injectable transport seam: ``(path, payload, headers) ->
        #: (status_code, parsed_json)``. Tests inject a fake; the default
        #: performs a real httpx2 POST.
        self._transport = transport or self._real_post

    # -- Provider protocol ------------------------------------------------

    def capabilities(self) -> dict[str, bool]:
        return {"streaming": True, "tool_calling": True,
                "vision": True, "json_mode": True}

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        messages = self.validate_messages(messages)
        model = kwargs.pop("model", None) or self.model
        if not model:
            raise ProviderError(f"No model configured for {self.name} provider")
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": m["role"], "content": m["content"]}
                         for m in messages],
        }
        # Pass through common generation knobs unchanged.
        for knob in ("temperature", "max_tokens", "top_p",
                     "response_format", "tools", "tool_choice"):
            if knob in kwargs:
                payload[knob] = kwargs.pop(knob)
        status, body = self._request_with_retries(
            "/chat/completions", payload, self._headers())
        return self._extract_text(body, status)

    # -- transport seam ----------------------------------------------------

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _real_post(
        self, path: str, payload: dict[str, Any], headers: dict[str, str]
    ) -> tuple[int, Any]:
        """Default transport: one httpx2 POST, returning (status, json)."""
        url = self.base_url + path
        try:
            with httpx2.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)
        except httpx2.HTTPError as exc:
            raise ProviderError(
                f"{self.name} request failed: "
                f"{self._redact(type(exc).__name__)}") from exc
        try:
            return response.status_code, response.json()
        except ValueError as exc:
            raise ProviderError(
                f"{self.name} returned malformed JSON "
                f"(HTTP {response.status_code}).") from exc

    # -- request / retry / error mapping -----------------------------------

    def _request_with_retries(
        self, path: str, payload: dict[str, Any], headers: dict[str, str]
    ) -> tuple[int, Any]:
        """POST with retry on 429/5xx; maps failures to ProviderError."""
        attempts = 1 + self.max_retries
        last_status: Optional[int] = None
        last_body: Any = None
        for attempt in range(attempts):
            status, body = self._transport(path, payload, headers)
            last_status, last_body = status, body
            if status == 200:
                return status, body
            if status in (401, 403):
                raise ProviderError(
                    f"{self.name} authentication failed (HTTP {status}). "
                    "Check the API key and export it via "
                    f"{self.api_key_env or 'api_key='}.")
            if status in RETRIABLE_STATUSES and attempt < attempts - 1:
                delay = (0.5 * (2 ** attempt)) + random.uniform(0, 0.25)
                time.sleep(delay)
                continue
            raise self._http_error(status, body)
        # Unreachable in practice, but keeps the type checker honest.
        raise self._http_error(last_status or 0, last_body)

    def _http_error(self, status: int, body: Any) -> ProviderError:
        """Non-retriable HTTP failure: status code, never body secrets."""
        return ProviderError(
            f"{self.name} request failed with HTTP {status}. "
            "The response body is withheld to avoid leaking secrets.")

    def _extract_text(self, body: Any, status: int) -> str:
        """Return the assistant text from a chat-completions body."""
        try:
            choices = body["choices"]
        except (TypeError, KeyError, IndexError):
            choices = None
        if not isinstance(choices, list) or not choices:
            raise ProviderError(
                f"{self.name} returned no choices (HTTP {status}).")
        first = choices[0]
        message = first.get("message") if isinstance(first, dict) else None
        text = message.get("content") if isinstance(message, dict) else None
        text = text or ""
        if not isinstance(text, str) or not text.strip():
            raise ProviderError(
                f"{self.name} returned empty assistant text (HTTP {status}).")
        return text

    # -- redaction ----------------------------------------------------------

    def _redact(self, text: str) -> str:
        """Strip any occurrence of the API key from ``text``."""
        if not isinstance(text, str):
            return text
        if self.api_key and self.api_key in text:
            text = text.replace(self.api_key, _REDACTED)
        return text

    # -- convenience --------------------------------------------------------

    @classmethod
    def for_endpoint(
        cls,
        base_url: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> "OpenAICompatProvider":
        """Build an instance pointed at an arbitrary compatible endpoint."""
        return cls(api_key=api_key, model=model, base_url=base_url, **kwargs)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (f"<{type(self).__name__} name={self.name!r} "
                f"model={self.model!r} base_url={self.base_url!r}>")


class GenericLocalCompatProvider(OpenAICompatProvider):
    """Preset for generic local OpenAI-compatible servers.

    Points at ``http://localhost:1234/v1`` (LM Studio's default; override
    ``base_url`` for llama.cpp ``:8080``, vLLM ``:8000``, etc.) with
    ``api_key_env = None``. When no key is configured, no
    ``Authorization`` header is sent at all.
    """

    name = "local-openai"
    default_model = "local-model"
    api_key_env = None
    base_url_default = "http://localhost:1234/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 2,
        transport: Optional[Callable[..., tuple[int, Any]]] = None,
    ) -> None:
        super().__init__(api_key=api_key, model=model, base_url=base_url,
                         timeout=timeout, max_retries=max_retries,
                         transport=transport)


class UniversalOpenAICompatProvider(OpenAICompatProvider):
    """The M-020 universal adapter: one instance per registry entry.

    Constructed purely from a :class:`ProviderDef` with dialect
    ``openai_compatible`` — endpoint, key env, default model, and
    capabilities come from the entry, and the entry's declared quirks
    switch on the behaviours the preset subclasses used to hard-code:

    * ``reasoning-content-fallback`` — assistant text falls back to
      ``message.reasoning_content`` when ``content`` is empty
      (DeepSeek's reasoning models).
    * ``app-identification-headers`` — every request also sends
      ``HTTP-Referer`` / ``X-Title`` (OpenRouter's app identification;
      overridable via ``http_referer=`` / ``x_title=``).
    * ``placeholder-bearer-auth`` — with no key configured, a
      placeholder bearer value is sent (vLLM's server convention).

    A non-compatible entry (``native_sdk``, ``ollama_native``) is
    refused with :class:`ProviderError`: those dialects are served by
    their own adapters, never through this shim.
    """

    def __init__(
        self,
        provider_def: ProviderDef,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 2,
        transport: Optional[Callable[..., tuple[int, Any]]] = None,
        http_referer: Optional[str] = None,
        x_title: Optional[str] = None,
    ) -> None:
        if provider_def.dialect != "openai_compatible":
            raise ProviderError(
                f"provider {provider_def.name!r} speaks dialect "
                f"{provider_def.dialect!r}, not 'openai_compatible'; "
                "the universal adapter cannot serve it"
            )
        # Instance identity must be set before Provider.__init__ reads
        # default_model / api_key_env to resolve model and key.
        self.provider_def = provider_def
        self.name = provider_def.name
        self.default_model = provider_def.default_model
        self.api_key_env = provider_def.api_key_env
        self.base_url_default = provider_def.endpoint or ""
        self.http_referer = http_referer or DEFAULT_HTTP_REFERER
        self.x_title = x_title or DEFAULT_X_TITLE
        super().__init__(api_key=api_key, model=model, base_url=base_url,
                         timeout=timeout, max_retries=max_retries,
                         transport=transport)

    @classmethod
    def from_registry(
        cls,
        name: str,
        **kwargs: Any,
    ) -> "UniversalOpenAICompatProvider":
        """Build the universal adapter for the registry entry *name*.

        Aliases resolve through the registry, exactly as in
        :meth:`ProviderRegistry.provider`; an unknown name raises
        KeyError — an unknown door is unknown, never guessed.
        """
        return cls(load_registry().provider(name), **kwargs)

    def capabilities(self) -> dict[str, bool]:
        return dict(self.provider_def.capabilities)

    def _headers(self) -> dict[str, str]:
        headers = super()._headers()
        if "Authorization" not in headers and (
            self.provider_def.has_quirk("placeholder-bearer-auth")
        ):
            headers["Authorization"] = f"Bearer {PLACEHOLDER_API_KEY}"
        if self.provider_def.has_quirk("app-identification-headers"):
            headers["HTTP-Referer"] = self.http_referer
            headers["X-Title"] = self.x_title
        return headers

    def _extract_text(self, body: Any, status: int) -> str:
        if not self.provider_def.has_quirk("reasoning-content-fallback"):
            return super()._extract_text(body, status)
        try:
            choices = body["choices"]
        except (TypeError, KeyError, IndexError):
            choices = None
        if not isinstance(choices, list) or not choices:
            raise ProviderError(
                f"{self.name} returned no choices (HTTP {status}).")
        first = choices[0]
        message = first.get("message") if isinstance(first, dict) else None
        if not isinstance(message, dict):
            raise ProviderError(
                f"{self.name} returned empty assistant text (HTTP {status}).")
        text = message.get("content")
        if not isinstance(text, str) or not text.strip():
            text = message.get("reasoning_content")
        if not isinstance(text, str) or not text.strip():
            raise ProviderError(
                f"{self.name} returned empty assistant text (HTTP {status}).")
        return text
