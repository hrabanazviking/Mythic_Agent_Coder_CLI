"""Provider health scoring (Slice 047).

Sliding-window success/latency statistics per provider, reduced to a
single 0..1 score with time decay:

* Each :meth:`ProviderHealth.record` appends ``(ok, latency_s, at)``
  to the provider's window (a deque capped at ``window_size`` samples,
  default 200).
* :meth:`ProviderHealth.score` weights samples by recency:
  ``weight = 0.5 ** (age_s / half_life_s)`` (default half-life 300 s),
  so stale evidence fades and recent failures/successes dominate.
* ``score = round(0.65 * success_rate + 0.35 * latency_factor, 4)``
  where ``latency_factor = 1 / (1 + latency_ewma / 2.0)`` — a provider
  answering in ~0 s scores a factor near 1, one averaging 2 s scores
  0.5. Latency is measured over successful samples only (failures
  usually fail fast and would otherwise look "fast").
* A provider with no samples scores 0.5 (documented neutral unknown),
  never 0 or 1.

FAKE FIXTURES ONLY: this module never calls a provider. Latencies and
outcomes are recorded by the caller (adapters, the failover router, or
tests injecting synthetic data). The injectable ``clock`` (monotonic
seconds) makes decay deterministic in tests.

All inputs are validated: negative latencies, non-boolean ``ok``, and
unknown provider names (for ``score``/``stats``) raise — health data
must never silently corrupt routing decisions.
"""


from __future__ import annotations

__all__ = [
    "DEFAULT_HALF_LIFE_S",
    "DEFAULT_WINDOW_SIZE",
    "ProviderHealth",
]

import time
from collections import deque
from typing import Callable, Optional


#: Default sample window per provider.
DEFAULT_WINDOW_SIZE = 200
#: Default half-life (seconds) for recency weighting.
DEFAULT_HALF_LIFE_S = 300.0
#: Success/latency blend weights in the final score.
_SUCCESS_WEIGHT = 0.65
_LATENCY_WEIGHT = 0.35
#: Latency (s) at which the latency factor halves.
_LATENCY_SCALE_S = 2.0
#: Neutral score for providers with no recorded samples.
_UNKNOWN_SCORE = 0.5


class ProviderHealth:
    """Sliding-window health statistics and 0..1 scores per provider."""

    def __init__(
        self,
        *,
        window_size: int = DEFAULT_WINDOW_SIZE,
        half_life_s: float = DEFAULT_HALF_LIFE_S,
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        if not isinstance(window_size, int) or window_size <= 0:
            raise ValueError(
                f"window_size must be a positive int, got {window_size!r}")
        if half_life_s is None or half_life_s <= 0:
            raise ValueError(
                f"half_life_s must be positive, got {half_life_s!r}")
        self.window_size = window_size
        self.half_life_s = half_life_s
        self._clock = clock or time.monotonic
        self._samples: dict[str, deque] = {}

    # -- recording ------------------------------------------------------

    def record(
        self,
        provider_name: str,
        *,
        ok: bool,
        latency_s: float,
        at: Optional[float] = None,
    ) -> None:
        """Record one call outcome for ``provider_name``."""
        if not isinstance(provider_name, str) or not provider_name:
            raise ValueError(
                f"provider_name must be a non-empty string, "
                f"got {provider_name!r}")
        if not isinstance(ok, bool):
            raise ValueError(f"ok must be a bool, got {ok!r}")
        if not isinstance(latency_s, (int, float)) or latency_s < 0:
            raise ValueError(
                f"latency_s must be a non-negative number, "
                f"got {latency_s!r}")
        stamp = self._clock() if at is None else at
        window = self._samples.setdefault(
            provider_name, deque(maxlen=self.window_size))
        window.append((bool(ok), float(latency_s), float(stamp)))

    # -- scoring --------------------------------------------------------

    def _weights(self, provider_name: str,
                 now: float) -> list[tuple[float, bool, float]]:
        """Return [(weight, ok, latency)] newest-first with decay."""
        window = self._samples.get(provider_name)
        if not window:
            return []
        weighted = []
        for ok, latency, stamp in reversed(window):
            age = max(0.0, now - stamp)
            weight = 0.5 ** (age / self.half_life_s)
            weighted.append((weight, ok, latency))
        return weighted

    def score(self, provider_name: str,
              *, at: Optional[float] = None) -> float:
        """Return the 0..1 health score for ``provider_name``.

        Unknown providers score 0.5 (neutral). Always within [0, 1].
        """
        now = self._clock() if at is None else at
        weighted = self._weights(provider_name, now)
        if not weighted:
            return _UNKNOWN_SCORE
        total = sum(weight for weight, _, _ in weighted)
        success_rate = (sum(weight for weight, ok, _ in weighted if ok)
                        / total)
        lat_weights = [(weight, latency)
                       for weight, ok, latency in weighted if ok]
        if lat_weights:
            lat_total = sum(weight for weight, _ in lat_weights)
            latency_ewma = (sum(weight * latency
                                for weight, latency in lat_weights)
                            / lat_total)
        else:
            latency_ewma = float("inf")
        latency_factor = 1.0 / (1.0 + latency_ewma / _LATENCY_SCALE_S)
        score = (_SUCCESS_WEIGHT * success_rate
                 + _LATENCY_WEIGHT * latency_factor)
        return round(min(1.0, max(0.0, score)), 4)

    def stats(self, provider_name: str,
              *, at: Optional[float] = None) -> dict:
        """Return a machine-readable stats dict for ``provider_name``."""
        now = self._clock() if at is None else at
        weighted = self._weights(provider_name, now)
        samples = len(weighted)
        if not samples:
            return {"provider": provider_name, "samples": 0,
                    "success_rate": None, "avg_latency_s": None,
                    "score": _UNKNOWN_SCORE}
        total = sum(weight for weight, _, _ in weighted)
        success_rate = (sum(weight for weight, ok, _ in weighted if ok)
                        / total)
        ok_latencies = [latency for _, ok, latency in weighted if ok]
        avg_latency = (sum(ok_latencies) / len(ok_latencies)
                       if ok_latencies else None)
        return {
            "provider": provider_name,
            "samples": samples,
            "success_rate": round(success_rate, 4),
            "avg_latency_s": (round(avg_latency, 4)
                              if avg_latency is not None else None),
            "score": self.score(provider_name, at=now),
        }

    def snapshot(self, *, at: Optional[float] = None) -> dict:
        """Return ``{provider_name: stats}`` for every tracked provider."""
        now = self._clock() if at is None else at
        return {name: self.stats(name, at=now)
                for name in sorted(self._samples)}

    def reset(self, provider_name: str) -> None:
        """Drop all samples for ``provider_name``."""
        self._samples.pop(provider_name, None)
