"""Ollama local provider adapter (Slices 35, R-033).

Stdlib-only adapter for a locally running Ollama server
(``http://localhost:11434`` by default). Needs no API key and no
third-party SDK; offline-first, matching Mythic's local model policy.

R-033 hardening:

* malformed host URLs (unknown scheme, missing scheme, empty host)
  are rejected up front with :class:`ProviderError` — before any socket
  is opened, so a typo'd host never produces a misleading
  "connection refused" style error,
* connection failures (including ``ECONNREFUSED``) map to
  :class:`ProviderError` with a ``ollama serve`` remedy,
* malformed JSON bodies map to :class:`ProviderError`,
* the configured ``timeout`` is honored on every socket operation,
* :meth:`OllamaProvider.list_models` lists installed models via
  ``GET /api/tags``; the ``_post`` / ``_get`` transport seams are the
  single stub points tests use (no live server required).
"""


from __future__ import annotations

__all__ = [
    "Any",
    "OllamaProvider",
    "Provider",
    "ProviderError",
]

import json
import urllib.parse
import urllib.request
from typing import Any

from .base import Provider, ProviderError

#: Schemes the Ollama adapter will speak to.
_ALLOWED_SCHEMES = ("http", "https")


class OllamaProvider(Provider):
    """Local Ollama adapter over the ``/api/chat`` endpoint (non-streaming)."""

    name = "ollama"
    default_model = "llama3.1"
    api_key_env = None  # local endpoint; no credential required

    def __init__(self, api_key: None = None, model: str | None = None,
                 host: str = "http://localhost:11434", timeout: float = 120.0) -> None:
        super().__init__(api_key=None, model=model)
        self.host = host.rstrip("/")
        self.timeout = timeout

    def capabilities(self) -> dict[str, bool]:
        return {"streaming": True, "tool_calling": True,
                "vision": True, "json_mode": True}

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        model = kwargs.pop("model", None) or self.model
        if not model:
            raise ProviderError("No model configured for ollama provider")
        normalized = [{"role": m.get("role", "user"),
                       "content": m.get("content") or ""}
                      for m in messages]
        payload = {"model": model, "messages": normalized, "stream": False}
        if "options" in kwargs:
            payload["options"] = kwargs.pop("options")
        response = self._post("/api/chat", payload)
        message = response.get("message", {})
        text = (message.get("content") or "").strip()
        if not text:
            raise ProviderError("Ollama returned no assistant text")
        return text

    def list_models(self) -> list[str]:
        """Return the names of models installed on the Ollama server.

        Queries the server's native ``GET /api/tags`` endpoint
        (``{"models": [{"name": ...}, ...]}``). Live use performs a real
        GET; unit tests stub the ``_get`` seam — no socket is opened.
        """
        response = self._get("/api/tags")
        models = response.get("models", [])
        names = [m.get("name") for m in models
                 if isinstance(m, dict) and m.get("name")]
        if not names:
            raise ProviderError(
                f"Ollama at {self.host} reported no installed models.")
        return names

    # -- transport seams ----------------------------------------------------

    def _validate_host(self) -> None:
        """Reject malformed host URLs before any socket is opened."""
        try:
            parsed = urllib.parse.urlparse(self.host)
        except ValueError as exc:
            raise ProviderError(
                f"Ollama host is malformed ({self.host!r}): {exc}. "
                "Use an http(s) URL such as 'http://localhost:11434'."
            ) from exc
        if parsed.scheme not in _ALLOWED_SCHEMES or not parsed.hostname:
            raise ProviderError(
                f"Ollama host is malformed ({self.host!r}): expected an "
                "http(s) URL with a host, such as "
                "'http://localhost:11434'.")

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """POST JSON and return the decoded body; single seam for tests."""
        self._validate_host()
        data = json.dumps(payload).encode("utf-8")
        try:
            request = urllib.request.Request(
                self.host + path, data=data,
                headers={"Content-Type": "application/json"}, method="POST")
        except (OSError, ValueError) as exc:
            raise ProviderError(
                f"Ollama host is malformed ({self.host!r}): {exc}. "
                "Use an http(s) URL such as 'http://localhost:11434'.") from exc
        return self._read_json(request)

    def _get(self, path: str) -> dict[str, Any]:
        """GET JSON and return the decoded body; single seam for tests.

        Live use performs a real GET against the Ollama host honoring
        the configured timeout; unit tests stub this method directly.
        """
        self._validate_host()
        try:
            request = urllib.request.Request(
                self.host + path,
                headers={"Accept": "application/json"}, method="GET")
        except (OSError, ValueError) as exc:
            raise ProviderError(
                f"Ollama host is malformed ({self.host!r}): {exc}. "
                "Use an http(s) URL such as 'http://localhost:11434'.") from exc
        return self._read_json(request)

    def _read_json(self, request: urllib.request.Request) -> dict[str, Any]:
        """Open ``request`` with the configured timeout; decode the body."""
        try:
            with urllib.request.urlopen(request,
                                        timeout=self.timeout) as reply:
                raw = reply.read().decode("utf-8")
        except ConnectionRefusedError as exc:
            raise ProviderError(
                f"Ollama connection refused at {self.host}: the server is "
                "not listening on that address/port. Start it with "
                "`ollama serve` and pull a model with "
                "`ollama pull <model>`.") from exc
        except OSError as exc:
            raise ProviderError(
                f"Ollama is unreachable at {self.host}. "
                "Start it with `ollama serve` and pull a model with "
                "`ollama pull <model>`.") from exc
        try:
            decoded = json.loads(raw)
        except ValueError as exc:  # json.JSONDecodeError subclasses ValueError
            raise ProviderError(
                f"Ollama returned malformed JSON from {self.host}.") from exc
        if not isinstance(decoded, dict):
            raise ProviderError(
                f"Ollama returned a non-object JSON body from {self.host}.")
        return decoded
