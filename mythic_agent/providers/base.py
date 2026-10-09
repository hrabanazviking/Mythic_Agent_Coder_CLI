"""Abstract provider interface for LLM backends (Slice 35).

A :class:`Provider` exposes two things:

* :meth:`Provider.chat` — one non-streaming completion over an
  OpenAI-style ``messages`` list, returning the assistant text.
* :meth:`Provider.capabilities` — a stable map of feature flags so
  callers can adapt (streaming, tool calling, vision, JSON mode).

Providers must raise :class:`ProviderError` (or a subclass) for any
failure — auth, transport, or malformed responses — and must never
emit credentials in error text.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any, Optional


class ProviderError(RuntimeError):
    """Any provider-side failure (auth, transport, malformed response)."""


class ProviderNotConfigured(ProviderError):
    """A credential or SDK the provider needs is missing.

    Raised before any network traffic, with a remedy that never includes
    key material.
    """


class ProviderNotFound(ProviderError):
    """No registered provider matches the requested name."""


class Provider(ABC):
    """Abstract LLM provider: chat completions plus capability detection."""

    #: Canonical registry name, e.g. ``"anthropic"``.
    name: str = "unknown"

    #: Fallback model when the caller does not name one.
    default_model: str = ""

    #: Environment variable consulted for this provider's API key.
    api_key_env: Optional[str] = None

    #: Known capability flags; concrete providers set these in
    #: ``capabilities()``. Values must always be booleans.
    CAPABILITY_FLAGS = ("streaming", "tool_calling", "vision", "json_mode")

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        self.api_key = api_key if api_key is not None else self._resolve_key()
        self.model = model or self.default_model

    def _resolve_key(self) -> Optional[str]:
        if not self.api_key_env:
            return None
        value = os.environ.get(self.api_key_env)
        return value if value else None

    @abstractmethod
    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        """Return the assistant's reply text for ``messages``.

        ``messages`` uses the OpenAI chat shape:
        ``[{"role": "system"|"user"|"assistant", "content": "..."}]``.
        """
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> dict[str, bool]:
        """Return the provider's feature flags keyed by CAPABILITY_FLAGS."""
        raise NotImplementedError

    def require_capability(self, flag: str) -> None:
        """Raise if this provider lacks ``flag``; callers use it to adapt."""
        if flag not in self.CAPABILITY_FLAGS:
            raise ValueError(f"Unknown capability flag: {flag!r}")
        if not self.capabilities().get(flag, False):
            raise ProviderError(
                f"Provider {self.name!r} does not support capability {flag!r}")

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<{type(self).__name__} name={self.name!r} model={self.model!r}>"
