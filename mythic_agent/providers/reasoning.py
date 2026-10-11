"""Reasoning-mode negotiation (Slice 043).

A normalized :class:`ReasoningConfig` (``{mode, budget_tokens}``) is
translated into each provider family's native reasoning wire shape:

* ``openai``: ``reasoning_effort`` (``"low"`` / ``"medium"`` / ``"high"``)
  — the documented OpenAI chat-completions knob for reasoning models.
* ``openrouter``: ``reasoning: {"effort": ...}`` — OpenRouter's
  documented reasoning parameter.
* ``anthropic``: ``thinking: {"type": "enabled", "budget_tokens": N}``
  — the documented extended-thinking shape. A budget is required by
  the API; when the caller sets none, 1024 is used (documented).
* ``deepseek``: reasoning is inherent to the model, not a wire knob.
  ``mode="on"`` on a ``*reasoner*`` model returns an empty fragment
  (nothing to send); requesting reasoning on a non-reasoner model, or
  an explicit effort/budget level, raises :class:`ProviderError`
  because DeepSeek exposes no such knob.
* every other adapter: :class:`ProviderError` — unsupported.

``mode="off"`` always returns ``{}`` for every provider.

Effort derivation for ``mode="on"`` (OpenAI/OpenRouter): the budget
picks the level — ``<= 2_048`` tokens → ``"low"``, ``<= 16_384`` →
``"medium"``, above that → ``"high"``; no budget → ``"medium"``.
Explicit ``mode`` values ``"low"``/``"medium"``/``"high"`` pass
through unchanged.

No network is touched; everything operates on in-memory shapes.
"""


from __future__ import annotations

__all__ = [
    "DEFAULT_THINKING_BUDGET",
    "Provider",
    "ProviderError",
    "ReasoningConfig",
    "negotiate",
]

from dataclasses import dataclass
from typing import Any, Optional

from .base import Provider, ProviderError


#: Anthropic thinking budget used when the caller sets none.
DEFAULT_THINKING_BUDGET = 1024

#: Budget thresholds mapping mode="on" to an effort level.
_LOW_MAX = 2_048
_MEDIUM_MAX = 16_384

_VALID_MODES = ("off", "on", "low", "medium", "high")


@dataclass(frozen=True)
class ReasoningConfig:
    """Normalized reasoning request.

    ``mode``: ``"off"`` (default), ``"on"`` (reason, provider's default
    effort), or an explicit ``"low"``/``"medium"``/``"high"`` effort.
    ``budget_tokens``: optional thinking-token budget; must be positive
    when set.
    """

    mode: str = "off"
    budget_tokens: Optional[int] = None

    def __post_init__(self) -> None:
        if self.mode not in _VALID_MODES:
            raise ValueError(
                f"mode must be one of {list(_VALID_MODES)}, "
                f"got {self.mode!r}")
        if self.budget_tokens is not None and (
                not isinstance(self.budget_tokens, int)
                or self.budget_tokens <= 0):
            raise ValueError(
                "budget_tokens must be a positive int, "
                f"got {self.budget_tokens!r}")


def _effort_for(config: ReasoningConfig) -> str:
    """Map a config to an OpenAI-style effort level."""
    if config.mode in ("low", "medium", "high"):
        return config.mode
    budget = config.budget_tokens
    if budget is None:
        return "medium"
    if budget <= _LOW_MAX:
        return "low"
    if budget <= _MEDIUM_MAX:
        return "medium"
    return "high"


def negotiate(provider: Provider, config: ReasoningConfig) -> dict[str, Any]:
    """Translate ``config`` into the provider's reasoning wire fragment.

    Returns ``{}`` when ``config.mode == "off"``. Raises
    :class:`ProviderError` for providers with no reasoning wire shape,
    and :class:`ValueError` is raised by :class:`ReasoningConfig`
    itself for malformed configs.
    """
    if not isinstance(config, ReasoningConfig):
        raise ProviderError(
            "config must be a ReasoningConfig, "
            f"got {type(config).__name__}")
    if config.mode == "off":
        return {}
    name = (getattr(provider, "name", "") or "").lower()
    if name == "openai":
        return {"reasoning_effort": _effort_for(config)}
    if name == "openrouter":
        return {"reasoning": {"effort": _effort_for(config)}}
    if name in ("anthropic", "claude"):
        budget = config.budget_tokens or DEFAULT_THINKING_BUDGET
        return {"thinking": {"type": "enabled", "budget_tokens": budget}}
    if name == "deepseek":
        model = (getattr(provider, "model", "") or "").lower()
        if config.mode != "on" or config.budget_tokens is not None:
            raise ProviderError(
                "DeepSeek exposes no reasoning-effort knob: use "
                "mode='on' with a deepseek-reasoner model.")
        if "reasoner" not in model:
            raise ProviderError(
                f"DeepSeek model {model!r} is not a reasoning model; "
                "reasoning requires a deepseek-reasoner model.")
        return {}
    raise ProviderError(
        f"Provider {provider.name!r} does not support reasoning mode; "
        "use mode='off'.")
