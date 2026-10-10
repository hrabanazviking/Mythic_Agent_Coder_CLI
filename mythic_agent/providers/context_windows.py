"""Context-window resolution and message truncation (Slice R-039).

:func:`resolve` finds the context window (in tokens) for a model:
the static :mod:`~mythic_agent.providers.model_registry` table wins,
then an optional provider probe hook ``probe_context_window(model)``,
then :data:`DEFAULT_CONTEXT_WINDOW`.

Where the 128000 default comes from: it is the module constant
:data:`DEFAULT_CONTEXT_WINDOW`, chosen to mirror the OpenAI gpt-4o-class
context window — the most common modern default across OpenAI-family
providers. It is a deliberate, documented fallback constant, not a
measured value; prefer the registry or the provider's probe hook
whenever a real number is available.

:func:`truncate_messages` drops oldest non-system messages until the
conversation fits ``max_tokens``. Token estimation is the documented
heuristic ``len(text) // 4`` (roughly four characters per token for
typical English text); callers may inject their own estimator.
System messages are NEVER dropped, and a single oversized message is
kept as-is (documented: truncating the only user turn would destroy
the request, so the caller — not this function — decides what to do
about overflow).
"""


from __future__ import annotations

__all__ = [
    "DEFAULT_CONTEXT_WINDOW",
    "Provider",
    "ProviderError",
    "resolve",
    "truncate_messages",
]

from typing import Any, Callable, Optional

from . import model_registry
from .base import Provider, ProviderError


#: Fallback context window (tokens) when neither the model registry nor
#: a provider probe hook knows the model. Mirrors the OpenAI
#: gpt-4o-class context window — the most common modern default across
#: OpenAI-family providers. A documented constant, not a measurement.
DEFAULT_CONTEXT_WINDOW = 128_000


def resolve(model: object, provider: Optional[Provider] = None) -> int:
    """Return the context window (tokens) for ``model``.

    1. :mod:`~mythic_agent.providers.model_registry` — static table,
       first match wins.
    2. ``provider.probe_context_window(model)`` when the provider
       exposes that hook — must return a positive int, else
       :class:`ProviderError`.
    3. :data:`DEFAULT_CONTEXT_WINDOW`.
    """
    if model_registry.known(model):
        _, window = model_registry.lookup(model)
        return window
    hook: Optional[Callable[[object], object]] = (
        getattr(provider, "probe_context_window", None) if provider else None
    )
    if callable(hook):
        value = hook(model)
        if isinstance(value, int) and value > 0:
            return value
        raise ProviderError(
            f"Provider {getattr(provider, 'name', '?')!r} probe hook "
            f"returned an invalid context window: {value!r}")
    return DEFAULT_CONTEXT_WINDOW


def _message_text(message: dict[str, Any]) -> str:
    """Extract plain text from an OpenAI-style message dict."""
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                parts.append(part["text"])
            elif isinstance(part, str):
                parts.append(part)
        return "".join(parts)
    return ""


def truncate_messages(
    messages: list[dict[str, Any]],
    max_tokens: int,
    estimate: Optional[Callable[[str], int]] = None,
) -> list[dict[str, Any]]:
    """Drop oldest non-system messages until the list fits ``max_tokens``.

    Token cost per message is ``estimate(text)``; the default estimator
    is ``len(text) // 4`` — a documented heuristic of roughly four
    characters per token for typical English text. System messages are
    never dropped. When only one non-system message remains and it
    still exceeds ``max_tokens``, it is kept unchanged (documented:
    the single remaining turn is the whole request — dropping it would
    destroy the conversation, so overflow is the caller's problem).
    Original message order is preserved among the survivors.
    """
    if max_tokens is None or max_tokens < 0:
        raise ProviderError(f"max_tokens must be >= 0, got {max_tokens!r}")
    estimator = estimate or (lambda text: len(text) // 4)
    costs = [max(0, estimator(_message_text(message))) for message in messages]
    kept = list(range(len(messages)))
    # Drop from the front, skipping system messages; stop before the
    # last non-system message so an oversized single turn survives.
    while kept and sum(costs[i] for i in kept) > max_tokens:
        droppable = [i for i in kept
                     if messages[i].get("role") != "system"]
        if len(droppable) <= 1:
            break
        kept.remove(droppable[0])
    return [messages[i] for i in kept]
