"""Static model capability registry (Slice R-038).

:data:`MODEL_TABLE` maps model-id patterns to (capability flags,
context window). It is pure data: no network, no side effects.
:func:`lookup` returns the first matching entry's flags and window;
unknown models get all-False flags and an 8192-token window.

Context-window values are the vendors' documented maximum context
lengths for the named model family (not measured at runtime). Where a
family ships several variants, the value is the most common documented
maximum for that family.
"""


from __future__ import annotations

__all__ = [
    "MODEL_TABLE",
    "Provider",
    "ProviderError",
    "known",
    "lookup",
    "validate_table",
]

import re
from typing import Optional

from .base import Provider, ProviderError


def _flags(
    *,
    streaming: bool,
    tool_calling: bool,
    vision: bool,
    json_mode: bool,
) -> dict[str, bool]:
    return {
        "streaming": streaming,
        "tool_calling": tool_calling,
        "vision": vision,
        "json_mode": json_mode,
    }


#: (compiled regex, flags with ALL four CAPABILITY_FLAGS, context window).
#: First match wins; order the specific before the general.
MODEL_TABLE: list[tuple["re.Pattern[str]", dict[str, bool], int]] = [
    # OpenAI GPT-5 family — 400k context.
    (re.compile(r"^gpt-5", re.IGNORECASE),
     _flags(streaming=True, tool_calling=True, vision=True, json_mode=True),
     400_000),
    # OpenAI GPT-4o family — 128k context.
    (re.compile(r"^gpt-4o", re.IGNORECASE),
     _flags(streaming=True, tool_calling=True, vision=True, json_mode=True),
     128_000),
    # Older GPT-4 / GPT-3.5 (turbo/vision variants) — 128k context.
    (re.compile(r"^gpt-4", re.IGNORECASE),
     _flags(streaming=True, tool_calling=True, vision=True, json_mode=True),
     128_000),
    (re.compile(r"^gpt-3\.5", re.IGNORECASE),
     _flags(streaming=True, tool_calling=True, vision=False, json_mode=True),
     16_385),
    # Anthropic Claude 4.x flagships — 200k context.
    (re.compile(r"^claude-(sonnet|opus)-4", re.IGNORECASE),
     _flags(streaming=True, tool_calling=True, vision=True, json_mode=False),
     200_000),
    # Older Claude families — 200k context.
    (re.compile(r"^claude", re.IGNORECASE),
     _flags(streaming=True, tool_calling=True, vision=True, json_mode=False),
     200_000),
    # Google Gemini 2.5 Pro — 1M context.
    (re.compile(r"^gemini-2\.5-pro", re.IGNORECASE),
     _flags(streaming=True, tool_calling=True, vision=True, json_mode=True),
     1_048_576),
    # Google Gemini 2.0 Flash — 1M context.
    (re.compile(r"^gemini-2\.0-flash", re.IGNORECASE),
     _flags(streaming=True, tool_calling=True, vision=True, json_mode=True),
     1_048_576),
    # Other Gemini models — 1M context.
    (re.compile(r"^gemini", re.IGNORECASE),
     _flags(streaming=True, tool_calling=True, vision=True, json_mode=True),
     1_048_576),
    # DeepSeek chat (V3.x) — 128k context.
    (re.compile(r"^deepseek-chat", re.IGNORECASE),
     _flags(streaming=True, tool_calling=True, vision=False, json_mode=True),
     128_000),
    # DeepSeek reasoner (R1) — reasoning models expose no function
    # calling or structured JSON in the public API; 128k context.
    (re.compile(r"^deepseek-reasoner", re.IGNORECASE),
     _flags(streaming=True, tool_calling=False, vision=False, json_mode=False),
     128_000),
    # Other DeepSeek models — 128k context.
    (re.compile(r"^deepseek", re.IGNORECASE),
     _flags(streaming=True, tool_calling=True, vision=False, json_mode=True),
     128_000),
    # Meta Llama 3.1 — 128k context.
    (re.compile(r"^llama-?3\.1", re.IGNORECASE),
     _flags(streaming=True, tool_calling=True, vision=False, json_mode=True),
     131_072),
    # Other Llama models — 128k context.
    (re.compile(r"^llama", re.IGNORECASE),
     _flags(streaming=True, tool_calling=True, vision=False, json_mode=True),
     131_072),
    # Qwen 3 — 32k native context.
    (re.compile(r"^qwen-?3", re.IGNORECASE),
     _flags(streaming=True, tool_calling=True, vision=False, json_mode=True),
     32_768),
    # Other Qwen models — 32k context.
    (re.compile(r"^qwen", re.IGNORECASE),
     _flags(streaming=True, tool_calling=True, vision=False, json_mode=True),
     32_768),
    # Mistral Large — 128k context.
    (re.compile(r"^mistral-large", re.IGNORECASE),
     _flags(streaming=True, tool_calling=True, vision=False, json_mode=True),
     128_000),
    # Other Mistral models — 128k context.
    (re.compile(r"^mistral", re.IGNORECASE),
     _flags(streaming=True, tool_calling=True, vision=False, json_mode=True),
     128_000),
]

#: Flags and window returned for models matching no table entry.
_UNKNOWN_FLAGS = _flags(streaming=False, tool_calling=False,
                        vision=False, json_mode=False)
_UNKNOWN_WINDOW = 8_192


def _find(model: str) -> Optional[tuple[dict[str, bool], int]]:
    for pattern, flags, window in MODEL_TABLE:
        if pattern.search(model):
            return dict(flags), window
    return None


def known(model: object) -> bool:
    """True when ``model`` matches a :data:`MODEL_TABLE` entry."""
    return isinstance(model, str) and bool(model) and _find(model) is not None


def lookup(model: object) -> tuple[dict[str, bool], int]:
    """Return ``(flags, context_window)`` for ``model``.

    First matching table entry wins. Unknown or non-string models get
    all-False flags and an 8192-token window.
    """
    if isinstance(model, str) and model:
        found = _find(model)
        if found is not None:
            return found
    return dict(_UNKNOWN_FLAGS), _UNKNOWN_WINDOW


def validate_table() -> None:
    """Assert every entry is well-formed; raise AssertionError otherwise.

    Checks: compiled regex, flags contain exactly the four
    ``CAPABILITY_FLAGS`` keys with boolean values, and a positive
    integer context window. Tests call this directly.
    """
    expected = set(Provider.CAPABILITY_FLAGS)
    for index, (pattern, flags, window) in enumerate(MODEL_TABLE):
        where = f"MODEL_TABLE[{index}]"
        assert isinstance(pattern, re.Pattern), \
            f"{where}: pattern is not a compiled regex"
        assert isinstance(flags, dict) and set(flags) == expected, \
            f"{where}: flags must have exactly the CAPABILITY_FLAGS keys"
        assert all(isinstance(value, bool) for value in flags.values()), \
            f"{where}: every flag must be a bool"
        assert isinstance(window, int) and window > 0, \
            f"{where}: context window must be a positive int"
