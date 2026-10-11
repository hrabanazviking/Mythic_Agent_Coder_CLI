"""Usage normalization (Slice 045).

Per-adapter usage-field mapping into :class:`base.ChatUsage`
(including cached tokens), with a heuristic estimation fallback when
the backend reports no usage metadata.

Wire shapes handled:

* OpenAI-family: ``usage`` / ``{"prompt_tokens", "completion_tokens",
  "total_tokens"}`` (also the shape some local servers emit).
* ``anthropic``: ``{"input_tokens", "output_tokens",
  "cache_creation_input_tokens", "cache_read_input_tokens"}`` — cached
  tokens land in :attr:`ChatUsage.cached_tokens` (they are already
  counted inside ``prompt_tokens`` by the API; kept separately for
  cost accounting).
* ``google``: ``usageMetadata`` with ``promptTokenCount`` /
  ``candidatesTokenCount`` / ``totalTokenCount`` /
  ``cachedContentTokenCount``.
* ``ollama``: ``{"prompt_eval_count", "eval_count"}`` from ``/api/chat``.

Heuristic estimation (:func:`estimate_tokens`): when ``raw`` is None or
carries no recognizable counts, tokens are estimated from the reply
text as ``len(text) // 4`` (documented rough English heuristic, ~4
characters per token); the resulting :class:`ChatUsage` has
``estimated=True`` so cost accounting never mistakes it for a
measured value. Empty text estimates 0.

Malformed usage (negative counts, non-integer counts) raises
:class:`ProviderError`; usage metadata must never silently corrupt
cost records.
"""


from __future__ import annotations

__all__ = [
    "Provider",
    "ProviderError",
    "estimate_tokens",
    "normalize",
    "normalize_usage_dict",
]

from typing import Any, Optional

from .base import ChatUsage, Provider, ProviderError


def estimate_tokens(text: str) -> int:
    """Heuristic token estimate for ``text``.

    Rough English heuristic: ~4 characters per token. Returns 0 for
    empty text. Documented as an estimate — callers must treat it as
    such (the :class:`ChatUsage` ``estimated`` flag exists for this).
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


def _as_non_negative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ProviderError(
            f"Usage field {field!r} must be an int, "
            f"got {type(value).__name__}.")
    if value < 0:
        raise ProviderError(
            f"Usage field {field!r} must be non-negative, got {value}.")
    return value


def normalize_usage_dict(raw: dict[str, Any], family: str) -> ChatUsage:
    """Map a raw usage dict of ``family`` into :class:`ChatUsage`.

    ``family``: ``"openai"``, ``"anthropic"``, ``"google"`` or
    ``"ollama"``. Unknown families fall back to generic
    prompt/completion key sniffing. Raises :class:`ProviderError` on
    malformed counts.
    """
    if family == "anthropic":
        prompt = _as_non_negative_int(raw.get("input_tokens", 0),
                                      "input_tokens")
        completion = _as_non_negative_int(raw.get("output_tokens", 0),
                                          "output_tokens")
        cached = (_as_non_negative_int(
            raw.get("cache_creation_input_tokens", 0),
            "cache_creation_input_tokens")
            + _as_non_negative_int(
                raw.get("cache_read_input_tokens", 0),
                "cache_read_input_tokens"))
        return ChatUsage(prompt_tokens=prompt, completion_tokens=completion,
                         cached_tokens=cached)
    if family == "google":
        prompt = _as_non_negative_int(raw.get("promptTokenCount", 0),
                                      "promptTokenCount")
        completion = _as_non_negative_int(
            raw.get("candidatesTokenCount", 0), "candidatesTokenCount")
        total = raw.get("totalTokenCount")
        cached = _as_non_negative_int(
            raw.get("cachedContentTokenCount", 0),
            "cachedContentTokenCount")
        usage = ChatUsage(prompt_tokens=prompt,
                          completion_tokens=completion,
                          cached_tokens=cached)
        if isinstance(total, int) and not isinstance(total, bool) \
                and total >= 0:
            usage.total_tokens = total
        return usage
    if family == "ollama":
        prompt = _as_non_negative_int(raw.get("prompt_eval_count", 0),
                                      "prompt_eval_count")
        completion = _as_non_negative_int(raw.get("eval_count", 0),
                                          "eval_count")
        return ChatUsage(prompt_tokens=prompt,
                         completion_tokens=completion)
    # OpenAI shape and generic sniffing.
    prompt_keys = ("prompt_tokens", "input_tokens", "promptTokenCount")
    completion_keys = ("completion_tokens", "output_tokens",
                       "candidatesTokenCount")
    prompt = next((raw[k] for k in prompt_keys if k in raw), 0)
    completion = next((raw[k] for k in completion_keys if k in raw), 0)
    return ChatUsage(
        prompt_tokens=_as_non_negative_int(prompt, "prompt_tokens"),
        completion_tokens=_as_non_negative_int(completion,
                                               "completion_tokens"))


def _family_of(provider: Provider) -> str:
    name = (getattr(provider, "name", "") or "").lower()
    if name in ("anthropic", "claude"):
        return "anthropic"
    if name in ("google", "gemini"):
        return "google"
    if name == "ollama":
        return "ollama"
    return "openai"


def _usage_dict_from(provider: Provider, raw: Any) -> Optional[dict]:
    """Extract the usage dict from a raw response body, or None."""
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ProviderError(
            "Cannot normalize usage: expected a dict response body, "
            f"got {type(raw).__name__}.")
    name = (getattr(provider, "name", "") or "").lower()
    if name in ("anthropic", "claude"):
        return raw  # usage fields live at the top level
    if name in ("google", "gemini"):
        nested = raw.get("usageMetadata")
        return nested if isinstance(nested, dict) else None
    if name == "ollama":
        return raw  # eval counts live at the top level
    nested = raw.get("usage")
    return nested if isinstance(nested, dict) else None


def normalize(
    provider: Provider,
    raw: Any,
    *,
    fallback_text: str = "",
) -> ChatUsage:
    """Normalize a raw response body into :class:`ChatUsage`.

    When ``raw`` carries no recognizable usage metadata, falls back to
    :func:`estimate_tokens` over ``fallback_text`` and marks the record
    ``estimated=True``.
    """
    usage_dict = _usage_dict_from(provider, raw)
    if usage_dict is None:
        tokens = estimate_tokens(fallback_text or "")
        # Split the estimate across prompt/completion proportionally to
        # nothing better: attribute all to completion (the measured
        # reply) and leave prompt at 0.
        return ChatUsage(prompt_tokens=0, completion_tokens=tokens,
                         estimated=True)
    return normalize_usage_dict(usage_dict, _family_of(provider))
