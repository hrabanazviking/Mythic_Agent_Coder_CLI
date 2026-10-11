"""Token budget planning (Slice 052).

:class:`TokenEstimator` counts tokens with ``tiktoken`` when it is
importable and falls back to a deterministic character heuristic
otherwise (``tiktoken`` is an optional extra, not a hard dependency).
:class:`BudgetPlanner` splits a total budget across named sources by
share and :func:`truncate_text` trims text to a token budget on a word
boundary with an explicit marker.
"""

from __future__ import annotations

__all__ = [
    "BudgetPlanner",
    "TokenEstimator",
    "truncate_text",
]

from dataclasses import dataclass, field
from typing import Mapping


_HEURISTIC_CHARS_PER_TOKEN = 4
_MESSAGE_OVERHEAD = 3


class TokenEstimator:
    """Count tokens, preferring ``tiktoken`` with a deterministic fallback.

    The heuristic fallback (``len(text) // 4``) is stable across runs and
    platforms; when ``tiktoken`` is available the estimator reports
    ``backend == "tiktoken"`` and uses the named encoding (deterministic
    for a fixed model/encoding name).
    """

    def __init__(self, model: str = "cl100k_base", prefer_tiktoken: bool = True) -> None:
        self.model = model
        self._encoding = None
        self.backend = "heuristic"
        if prefer_tiktoken:
            try:
                import tiktoken
            except ImportError:
                tiktoken = None  # optional: precise counting; heuristic fallback below
            if tiktoken is not None:
                try:
                    self._encoding = tiktoken.get_encoding(model)
                except Exception:
                    self._encoding = None
                else:
                    self.backend = "tiktoken"

    def count(self, text: str) -> int:
        """Token count for *text* (never negative)."""
        if not text:
            return 0
        if self._encoding is not None:
            try:
                return len(self._encoding.encode(text))
            except Exception:
                pass
        return max(1, len(text) // _HEURISTIC_CHARS_PER_TOKEN)

    def count_message(self, role: str, content: str) -> int:
        """Token count for one chat message, including framing overhead."""
        return self.count(f"{role}: {content}") + _MESSAGE_OVERHEAD


def truncate_text(
    text: str,
    max_tokens: int,
    estimator: TokenEstimator,
    *,
    marker: str = "... [truncated]",
) -> str:
    """Trim *text* to fit *max_tokens*, preferring a word boundary.

    Returns *text* unchanged when it already fits.  A zero or negative
    budget yields ``""``; when even the marker does not fit, as much of
    the marker as fits is returned (possibly ``""``).
    """
    if max_tokens <= 0:
        return ""
    if estimator.count(text) <= max_tokens:
        return text
    marker_cost = estimator.count(marker)
    if marker_cost >= max_tokens:
        # Marker alone does not fit: hard-cut the marker itself.
        approx_chars = max_tokens * _HEURISTIC_CHARS_PER_TOKEN
        return marker[:approx_chars]
    # Binary-search the longest prefix whose *full result* (prefix + marker)
    # fits; searching on the concatenated string avoids integer-division
    # rounding surprises between the two parts.
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if estimator.count(text[:mid] + marker) <= max_tokens:
            lo = mid
        else:
            hi = mid - 1
    prefix = text[:lo].rstrip()
    cut = prefix.rfind(" ")
    if cut > len(prefix) // 2:
        prefix = prefix[:cut].rstrip()
    result = prefix + marker
    # Defensive: word-boundary cuts only shorten, but a non-monotonic
    # estimator must never let an oversized result through.
    while prefix and estimator.count(result) > max_tokens:
        prefix = prefix[:-1].rstrip()
        result = prefix + marker
    return result


@dataclass
class BudgetPlanner:
    """Split a token budget across named sources and trim to fit."""

    estimator: TokenEstimator = field(default_factory=TokenEstimator)

    def allocate(self, total: int, shares: Mapping[str, float]) -> dict[str, int]:
        """Divide *total* tokens across *shares* (largest-remainder method).

        Shares are normalized; negative shares and an empty mapping raise
        :class:`ValueError`.  A zero total yields zero for every source.
        The allocated amounts always sum to *total*.
        """
        if not shares:
            raise ValueError("shares must not be empty")
        if total < 0:
            raise ValueError("total must be non-negative")
        weights = dict(shares)
        for name, weight in weights.items():
            if weight < 0:
                raise ValueError(f"negative share for source {name!r}")
        weight_sum = sum(weights.values())
        if weight_sum <= 0:
            raise ValueError("shares must sum to a positive value")
        exact = {name: total * weight / weight_sum for name, weight in weights.items()}
        floors = {name: int(value) for name, value in exact.items()}
        remainder = total - sum(floors.values())
        # Largest fractional remainder first; ties broken by name for determinism.
        order = sorted(exact, key=lambda n: (exact[n] - floors[n], n), reverse=True)
        for name in order[:remainder]:
            floors[name] += 1
        return floors
