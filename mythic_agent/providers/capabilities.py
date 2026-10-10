"""Live capability discovery by probing a provider's model list (Slice R-037).

:func:`probe_capabilities` performs a **live** ``GET {base_url}/models``
against providers that expose a ``base_url`` attribute and maps the
returned model ids to capability flags via substring matching.

LIVE-ONLY: when the provider exposes no injectable ``_transport`` seam,
this function performs a real HTTPS GET with the provider's timeout.
Never call it in unit tests without a fake ``transport=`` seam — the
test suite covers the mapping, TTL, and degradation logic entirely
through the :class:`~mythic_agent.providers.openai_compat.OpenAICompatProvider`
fake-transport seam, so no invented live results ever enter the tests.

Design:

* results are cached per ``(provider.name, base_url)`` with a TTL
  (default 300 s, injectable clock for tests);
* on any probe failure the provider's static ``capabilities()`` are
  returned unchanged (graceful degradation);
* providers without ``base_url`` raise :class:`ProviderError` —
  there is nothing to probe.
"""


from __future__ import annotations

__all__ = [
    "Provider",
    "ProviderError",
    "invalidate",
    "probe_capabilities",
]

import time
from typing import Any, Callable, Optional

from .base import Provider, ProviderError


#: Default cache lifetime, seconds.
DEFAULT_TTL = 300.0

#: Substring -> capability flags granted when a model id contains it.
#: Matching is case-insensitive; flags accumulate (OR) over all ids.
_SUBSTRING_FLAGS: tuple[tuple[str, dict[str, bool]], ...] = (
    # Vision-capable families.
    ("vision", {"vision": True}),
    ("gpt-4o", {"vision": True}),
    ("gpt-5", {"vision": True}),
    ("4o", {"vision": True}),
    ("claude-opus", {"vision": True}),
    ("claude-sonnet", {"vision": True}),
    ("claude-3", {"vision": True}),
    ("gemini", {"vision": True}),
    ("llava", {"vision": True}),
    ("llama3.2", {"vision": True}),
    # Tool-calling families.
    ("gpt-4", {"tool_calling": True}),
    ("gpt-5", {"tool_calling": True}),
    ("gpt-3.5", {"tool_calling": True}),
    ("claude", {"tool_calling": True}),
    ("gemini", {"tool_calling": True}),
    ("llama3", {"tool_calling": True}),
    ("llama-3", {"tool_calling": True}),
    ("qwen", {"tool_calling": True}),
    ("mistral", {"tool_calling": True}),
    ("deepseek", {"tool_calling": True}),
    ("function", {"tool_calling": True}),
    # JSON-mode families.
    ("gpt-4", {"json_mode": True}),
    ("gpt-5", {"json_mode": True}),
    ("gpt-3.5", {"json_mode": True}),
    ("claude", {"json_mode": True}),
    ("gemini", {"json_mode": True}),
    ("deepseek", {"json_mode": True}),
    ("llama", {"json_mode": True}),
    ("mistral", {"json_mode": True}),
    ("qwen", {"json_mode": True}),
    # Streaming families (near-universal; listed for explicitness).
    ("gpt", {"streaming": True}),
    ("claude", {"streaming": True}),
    ("gemini", {"streaming": True}),
    ("llama", {"streaming": True}),
    ("mistral", {"streaming": True}),
    ("qwen", {"streaming": True}),
    ("deepseek", {"streaming": True}),
    ("phi", {"streaming": True}),
    ("mixtral", {"streaming": True}),
)

#: Cache of ``(provider.name, base_url) -> (expires_at, flags)``.
_CACHE: dict[tuple[str, str], tuple[float, dict[str, bool]]] = {}


def _blank_flags() -> dict[str, bool]:
    return {flag: False for flag in Provider.CAPABILITY_FLAGS}


def _map_model_ids(model_ids: list[str]) -> dict[str, bool]:
    """OR the substring-flag rules over every model id."""
    flags = _blank_flags()
    for model_id in model_ids:
        lowered = model_id.lower()
        for substring, granted in _SUBSTRING_FLAGS:
            if substring in lowered:
                for flag, value in granted.items():
                    flags[flag] = flags[flag] or value
    return flags


def _fetch_model_ids(provider: Provider, base_url: str) -> list[str]:
    """Return the model ids from ``GET {base_url}/models``.

    Uses the provider's injectable ``_transport`` seam
    (``(path, payload, headers) -> (status, body)``) when present —
    that is how tests drive this without touching the network.
    Otherwise performs a real httpx2 GET (the LIVE-ONLY path).
    """
    headers: dict[str, str] = {}
    seam = getattr(provider, "_transport", None)
    if callable(seam):
        status, body = seam("/models", {}, headers)
    else:  # pragma: no cover - live path; never exercised in tests
        try:
            import httpx2
        except ImportError:  # pragma: no cover - declared fallback pattern
            import httpx as httpx2  # type: ignore[no-redef]
        try:
            with httpx2.Client(timeout=provider.timeout) as client:
                response = client.get(base_url + "/models", headers=headers)
        except httpx2.HTTPError as exc:
            raise ProviderError(
                f"{provider.name} model probe failed: "
                f"{type(exc).__name__}") from exc
        status, body = response.status_code, response.json()
    if status != 200:
        raise ProviderError(
            f"{provider.name} model probe returned HTTP {status}.")
    try:
        entries = body["data"]
        return [str(entry["id"]) for entry in entries]
    except (TypeError, KeyError, IndexError) as exc:
        raise ProviderError(
            f"{provider.name} model probe returned a malformed body.") from exc


def probe_capabilities(
    provider: Provider,
    *,
    ttl: float = DEFAULT_TTL,
    clock: Optional[Callable[[], float]] = None,
) -> dict[str, bool]:
    """Discover capability flags by probing ``GET {base_url}/models``.

    LIVE-ONLY: with no injected ``_transport`` seam this performs a
    real HTTPS GET against the provider's ``base_url``. Never call it
    in unit tests without a fake ``transport=`` seam.

    Successful results are cached per ``(provider.name, base_url)``
    for ``ttl`` seconds (``clock`` is an injectable monotonic source
    for tests). Any probe failure — transport error, non-200 status,
    malformed body — returns ``provider.capabilities()`` unchanged
    (graceful degradation). Providers without ``base_url`` raise
    :class:`ProviderError`.
    """
    base_url = getattr(provider, "base_url", None)
    if not base_url:
        raise ProviderError(
            f"Provider {provider.name!r} exposes no base_url; "
            "live capability discovery is unsupported.")
    now = clock or time.monotonic
    key = (provider.name, base_url)
    cached = _CACHE.get(key)
    if cached is not None:
        expires_at, flags = cached
        if expires_at > now():
            return dict(flags)
    try:
        model_ids = _fetch_model_ids(provider, base_url)
    except ProviderError:
        return dict(provider.capabilities())
    flags = _map_model_ids(model_ids)
    _CACHE[key] = (now() + ttl, flags)
    return dict(flags)


def invalidate(provider: Provider) -> None:
    """Drop the cached probe result for ``provider`` (tests use this)."""
    base_url = getattr(provider, "base_url", "") or ""
    _CACHE.pop((provider.name, base_url), None)
