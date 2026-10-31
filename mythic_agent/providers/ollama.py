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

M-023 (Local runtimes I) adds the discovery kindness on top:

* :meth:`OllamaProvider.running_models` — models actually loaded in
  memory right now, via ``GET /api/ps`` (an empty list is an honest
  answer, never an error),
* :meth:`OllamaProvider.pull_model` — ``POST /api/pull`` so a model
  can be fetched without leaving the app (the TUI's ``/ollama pull``),
* :meth:`OllamaProvider.model_present` / :meth:`OllamaProvider.ensure_model`
  / :meth:`OllamaProvider.show_model` — honest "model not present"
  answers: presence is checked against ``/api/tags``, detail comes
  from ``POST /api/show``, and an HTTP error body from the server
  (e.g. a 404 ``model not found``) is surfaced as itself — with the
  ``ollama pull`` remedy — instead of being misreported as an
  unreachable server,
* :meth:`OllamaProvider.discover` — the one-call snapshot (installed
  + running) the TUI's ``/ollama`` list renders.
"""


from __future__ import annotations

__all__ = [
    "Any",
    "OllamaProvider",
    "Provider",
    "ProviderError",
]

import json
import urllib.error
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
        names = self._installed_names()
        if not names:
            raise ProviderError(
                f"Ollama at {self.host} reported no installed models.")
        return names

    def _installed_names(self) -> list[str]:
        """Installed model names from ``GET /api/tags``; empty is honest."""
        response = self._get("/api/tags")
        models = response.get("models", [])
        if not isinstance(models, list):
            return []
        return [m.get("name") for m in models
                if isinstance(m, dict) and m.get("name")]

    @staticmethod
    def _name_matches(installed: str, wanted: str) -> bool:
        """True when ``wanted`` names ``installed`` (``:latest`` implied)."""
        return installed == wanted or installed == f"{wanted}:latest"

    def model_present(self, name: str) -> bool:
        """True when ``name`` is installed on the server (``/api/tags``)."""
        wanted = (name or "").strip()
        if not wanted:
            raise ProviderError("No model name given to look for.")
        return any(self._name_matches(installed, wanted)
                   for installed in self._installed_names())

    def ensure_model(self, name: str) -> str:
        """Return ``name`` if installed; else an honest not-present error."""
        wanted = (name or "").strip()
        if not wanted:
            raise ProviderError("No model configured for ollama provider")
        if not self.model_present(wanted):
            raise ProviderError(
                f"Model {wanted!r} is not present in Ollama at {self.host}. "
                f"Pull it with `ollama pull {wanted}` or from the TUI with "
                f"`/ollama pull {wanted}`.")
        return wanted

    def running_models(self) -> list[str]:
        """Names of models loaded in memory right now (``GET /api/ps``).

        Unlike :meth:`list_models`, an empty answer is a normal state
        (nothing loaded yet), so this returns ``[]`` rather than raising.
        """
        response = self._get("/api/ps")
        models = response.get("models", [])
        if not isinstance(models, list):
            return []
        return [m.get("name") for m in models
                if isinstance(m, dict) and m.get("name")]

    def discover(self) -> dict[str, Any]:
        """One-call discovery snapshot: host, installed, and running models."""
        return {"host": self.host,
                "installed": self._installed_names(),
                "running": self.running_models()}

    def show_model(self, name: str) -> dict[str, Any]:
        """Server detail for one model via ``POST /api/show``.

        A model the server does not have answers 404, which the
        transport maps to a "model not present" :class:`ProviderError`
        carrying the pull remedy — never a silent empty dict.
        """
        wanted = (name or "").strip()
        if not wanted:
            raise ProviderError("No model name given to show.")
        return self._post("/api/show", {"name": wanted})

    def pull_model(self, name: str) -> dict[str, Any]:
        """Pull ``name`` onto the server via ``POST /api/pull``.

        Non-streaming: the call returns when the pull finishes, with
        the server's final status body (``{"status": "success"}``).
        """
        wanted = (name or "").strip()
        if not wanted:
            raise ProviderError("No model name given to pull.")
        return self._post("/api/pull", {"name": wanted, "stream": False})

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
        except urllib.error.HTTPError as exc:
            # The server answered and said no — surface ITS answer
            # (HTTPError is an OSError subclass, so this must come
            # before the unreachable mapping below).
            detail = ""
            try:
                body = exc.read().decode("utf-8")
                parsed = json.loads(body)
                if isinstance(parsed, dict) and parsed.get("error"):
                    detail = str(parsed["error"])
                elif body.strip():
                    detail = body.strip()
            except Exception:
                detail = ""
            if exc.code == 404 or "not found" in detail.lower():
                raise ProviderError(
                    f"Ollama at {self.host} reports the model is not "
                    f"present ({detail or 'not found'}). Pull it with "
                    "`ollama pull <model>` or from the TUI with "
                    "`/ollama pull <model>`.") from exc
            raise ProviderError(
                f"Ollama at {self.host} answered HTTP {exc.code}"
                + (f": {detail}" if detail else ".")) from exc
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
