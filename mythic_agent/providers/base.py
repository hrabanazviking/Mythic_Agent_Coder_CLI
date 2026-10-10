"""Abstract provider interface for LLM backends (Slices 35, 026).

A :class:`Provider` exposes two things:

* :meth:`Provider.chat` — one non-streaming completion over an
  OpenAI-style ``messages`` list, returning the assistant text.
* :meth:`Provider.capabilities` — a stable map of feature flags so
  callers can adapt (streaming, tool calling, vision, JSON mode).

Providers must raise :class:`ProviderError` (or a subclass) for any
failure — auth, transport, or malformed responses — and must never
emit credentials in error text.

Slice 026 (Provider Contract V2) hardens the contract:

* :func:`Provider.validate_messages` — chat input must be a list of
  dicts with a valid ``role`` and usable ``content``; malformed input
  raises :class:`ProviderError` before any transport happens.
* :class:`ChatUsage` / :class:`ToolCall` — normalized dataclasses for
  token usage and tool calls, shared by every adapter.
* :meth:`Provider.iter_chunks` — streaming seam. The default
  implementation raises :class:`ProviderError` ("streaming unsupported");
  adapters with real streaming override it.
* ``__init_subclass__`` validates capability flags at class definition
  time: ``capabilities()`` must return exactly the ``CAPABILITY_FLAGS``
  keys with boolean values, or the subclass definition fails loudly.
* :meth:`Provider.__init__` accepts ``timeout`` / ``max_retries`` knobs
  stored as plain attributes for adapters to honor.
"""


from __future__ import annotations

__all__ = [
    "ABC",
    "Any",
    "ChatUsage",
    "Optional",
    "Provider",
    "ProviderError",
    "ProviderNotConfigured",
    "ProviderNotFound",
    "ToolCall",
    "abstractmethod",
]

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional

from ..core.exceptions import MythicProviderError


class ProviderError(MythicProviderError, RuntimeError):
    """Any provider-side failure (auth, transport, malformed response)."""


class ProviderNotConfigured(ProviderError):
    """A credential or SDK the provider needs is missing.

    Raised before any network traffic, with a remedy that never includes
    key material.
    """


class ProviderNotFound(ProviderError):
    """No registered provider matches the requested name."""


@dataclass
class ChatUsage:
    """Normalized token-usage record for one completion.

    Adapters that receive usage metadata from their backend should
    populate this; ``total_tokens`` is derived when omitted.
    """

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def __post_init__(self) -> None:
        if self.total_tokens == 0 and (
            self.prompt_tokens != 0 or self.completion_tokens != 0
        ):
            self.total_tokens = self.prompt_tokens + self.completion_tokens


@dataclass
class ToolCall:
    """Normalized tool-call request emitted by an assistant message."""

    id: str = ""
    name: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)


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

    #: Roles accepted by :meth:`validate_messages`.
    VALID_ROLES = ("system", "user", "assistant", "tool", "developer")

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 2,
    ) -> None:
        if timeout is None or timeout <= 0:
            raise ValueError(f"timeout must be positive, got {timeout!r}")
        if max_retries is None or max_retries < 0:
            raise ValueError(f"max_retries must be >= 0, got {max_retries!r}")
        self.api_key = api_key if api_key is not None else self._resolve_key()
        self.model = model or self.default_model
        self.timeout = timeout
        self.max_retries = max_retries

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Validate capability flags at class definition time.

        When a concrete subclass can be constructed with no arguments and
        its :meth:`capabilities` is callable, the returned mapping must
        have exactly the ``CAPABILITY_FLAGS`` keys with boolean values.
        A violation raises :class:`TypeError` immediately — a bad
        adapter fails at import/definition time, never at runtime.
        Subclasses that cannot be probed (abstract, or requiring
        constructor arguments) are skipped.
        """
        super().__init_subclass__(**kwargs)
        try:
            probe = cls()
        except Exception:
            return  # cannot probe without constructor arguments; skip
        try:
            capabilities = probe.capabilities()
        except Exception:
            return  # capabilities() itself refused; leave it to runtime
        expected = set(Provider.CAPABILITY_FLAGS)
        ok = (
            isinstance(capabilities, dict)
            and set(capabilities.keys()) == expected
            and all(isinstance(value, bool) for value in capabilities.values())
        )
        if not ok:
            raise TypeError(
                f"{cls.__name__}.capabilities() must return exactly the "
                f"CAPABILITY_FLAGS keys {sorted(expected)} with boolean "
                f"values; got {capabilities!r}"
            )

    def _resolve_key(self) -> Optional[str]:
        if not self.api_key_env:
            return None
        value = os.environ.get(self.api_key_env)
        return value if value else None

    @staticmethod
    def validate_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Check OpenAI-style chat input; raise :class:`ProviderError` if bad.

        Every item must be a dict with a ``role`` in
        :attr:`VALID_ROLES` and a ``content`` that is a string or a list
        of content parts (vision). Returns ``messages`` unchanged so
        call sites can write ``messages = self.validate_messages(messages)``.
        """
        if not isinstance(messages, list) or not messages:
            raise ProviderError(
                "messages must be a non-empty list of message dicts")
        for index, message in enumerate(messages):
            where = f"messages[{index}]"
            if not isinstance(message, dict):
                raise ProviderError(
                    f"{where} must be a dict, got {type(message).__name__}")
            role = message.get("role")
            if role not in Provider.VALID_ROLES:
                raise ProviderError(
                    f"{where} has invalid role {role!r}; expected one of "
                    f"{list(Provider.VALID_ROLES)}")
            content = message.get("content", None)
            if not isinstance(content, (str, list)):
                raise ProviderError(
                    f"{where} has invalid content: expected str or list, "
                    f"got {type(content).__name__}")
        return messages

    @abstractmethod
    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        """Return the assistant's reply text for ``messages``.

        ``messages`` uses the OpenAI chat shape:
        ``[{"role": "system"|"user"|"assistant", "content": "..."}]``.
        Implementations must call :meth:`validate_messages` first and
        raise :class:`ProviderError` (or a subclass) on any failure.
        """
        raise NotImplementedError

    def iter_chunks(
        self, messages: list[dict[str, Any]], **kwargs: Any
    ) -> Iterator[str]:
        """Yield assistant text chunks for ``messages`` (streaming seam).

        The default implementation raises :class:`ProviderError`
        because streaming is unsupported; adapters with real streaming
        override this method. Callers should check
        ``require_capability("streaming")`` first.
        """
        raise ProviderError(
            f"Provider {self.name!r}: streaming unsupported "
            f"(iter_chunks is not implemented)")

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
