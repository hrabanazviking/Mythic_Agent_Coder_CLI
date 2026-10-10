"""Ollama local provider adapter (Slice 35).

Stdlib-only adapter for a locally running Ollama server
(``http://localhost:11434`` by default). Needs no API key and no
third-party SDK; offline-first, matching Mythic's local model policy.
"""


from __future__ import annotations

__all__ = [
    "Any",
    "OllamaProvider",
    "Provider",
    "ProviderError",
]

import json
import urllib.request
from typing import Any

from .base import Provider, ProviderError


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

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """POST JSON and return the decoded body; single seam for tests."""
        try:
            request = urllib.request.Request(
                self.host + path,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST")
        except (OSError, ValueError) as exc:
            raise ProviderError(
                f"Ollama host is malformed ({self.host!r}): {exc}. "
                "Use an http(s) URL such as 'http://localhost:11434'.") from exc
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as reply:
                raw = reply.read().decode("utf-8")
        except OSError as exc:
            raise ProviderError(
                f"Ollama is unreachable at {self.host}. "
                "Start it with `ollama serve` and pull a model with "
                "`ollama pull <model>`.") from exc
        try:
            return json.loads(raw)
        except ValueError as exc:  # json.JSONDecodeError subclasses ValueError
            raise ProviderError(
                f"Ollama returned malformed JSON from {self.host}.") from exc
