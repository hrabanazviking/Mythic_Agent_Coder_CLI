"""Provider failover routing (Slice 048).

:class:`FailoverRouter` tries providers in health-aware order with an
explicit :class:`FailoverPolicy` and per-provider circuit breakers:

* **Ordering**: candidate names are sorted by
  :class:`~mythic_agent.providers.health.ProviderHealth` score,
  healthiest first. Providers with an open circuit breaker sort last
  (they are still eligible as a last resort only when every other
  candidate is also broken — documented below).
* **Retry semantics**: each candidate is tried at most once per
  :meth:`FailoverRouter.chat` call. "Retry" here means the operation
  is retried on the *next* provider (failover), never hammered on the
  same one — same-provider transport retries belong to the adapter's
  own ``max_retries`` layer (:mod:`mythic_agent.providers.openai_compat`).
* **Circuit breaker**: ``breaker_threshold`` consecutive failures open
  the breaker for ``cooldown_s`` seconds; a success closes it. While
  open, the provider is skipped entirely (fail-fast — no doomed
  attempts are burned); after the cooldown it becomes eligible again
  (half-open). If *every* candidate's breaker is open, the call fails
  fast with :class:`FailoverExhausted` naming the breakered providers
  instead of waiting out cooldowns.
* **Attribution**: every attempt (provider, outcome, latency, error)
  is recorded into the health tracker and returned in
  :class:`FailoverResult`, so failover decisions stay inspectable.

When every candidate fails, :class:`FailoverExhausted` is raised
carrying the per-provider errors — callers always learn *why* each
provider failed, never a bare "all failed".

FAKE FIXTURES ONLY: the router takes a ``provider_factory`` callable,
so tests inject scripted fake providers. No live provider calls
happen in this module or its tests.
"""


from __future__ import annotations

__all__ = [
    "FailoverExhausted",
    "FailoverPolicy",
    "FailoverResult",
    "FailoverRouter",
    "Provider",
    "ProviderError",
]

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from .base import Provider, ProviderError
from .health import ProviderHealth


class FailoverExhausted(ProviderError):
    """Every failover candidate failed.

    ``attempts`` is the ordered list of per-provider attempt dicts
    (``{"provider", "ok", "latency_s", "error"}``).
    """

    def __init__(self, message: str,
                 attempts: list[dict[str, Any]]) -> None:
        super().__init__(message)
        self.attempts = attempts


@dataclass(frozen=True)
class FailoverPolicy:
    """Explicit failover policy knobs."""

    #: Max provider candidates tried per call.
    max_attempts: int = 3
    #: Seconds an open breaker stays open before half-open retry.
    cooldown_s: float = 30.0
    #: Consecutive failures that open the breaker.
    breaker_threshold: int = 3

    def __post_init__(self) -> None:
        if self.max_attempts <= 0:
            raise ValueError(
                f"max_attempts must be positive, got {self.max_attempts!r}")
        if self.cooldown_s <= 0:
            raise ValueError(
                f"cooldown_s must be positive, got {self.cooldown_s!r}")
        if self.breaker_threshold <= 0:
            raise ValueError(
                "breaker_threshold must be positive, "
                f"got {self.breaker_threshold!r}")


@dataclass
class FailoverResult:
    """Outcome of one :meth:`FailoverRouter.chat` call."""

    #: Assistant text from the winning provider.
    text: str
    #: Name of the provider that answered.
    provider: str
    #: Ordered attempt records (provider/ok/latency_s/error).
    attempts: list[dict[str, Any]] = field(default_factory=list)


class _CircuitBreaker:
    """Per-provider consecutive-failure breaker with cooldown."""

    def __init__(self, threshold: int, cooldown_s: float,
                 clock: Callable[[], float]) -> None:
        self._threshold = threshold
        self._cooldown_s = cooldown_s
        self._clock = clock
        self._failures = 0
        self._opened_at: Optional[float] = None

    def allow(self, now: float) -> bool:
        if self._opened_at is None:
            return True
        return (now - self._opened_at) >= self._cooldown_s

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None

    def record_failure(self, now: float) -> None:
        self._failures += 1
        if self._failures >= self._threshold:
            self._opened_at = now


class FailoverRouter:
    """Health-aware ordered failover across provider candidates."""

    def __init__(
        self,
        policy: Optional[FailoverPolicy] = None,
        health: Optional[ProviderHealth] = None,
        *,
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        self.policy = policy or FailoverPolicy()
        self.health = health or ProviderHealth()
        self._clock = clock or time.monotonic
        self._breakers: dict[str, _CircuitBreaker] = {}

    def _breaker(self, name: str) -> _CircuitBreaker:
        breaker = self._breakers.get(name)
        if breaker is None:
            breaker = _CircuitBreaker(
                self.policy.breaker_threshold, self.policy.cooldown_s,
                self._clock)
            self._breakers[name] = breaker
        return breaker

    def order(self, candidates: list[str]) -> list[str]:
        """Return ``candidates`` healthiest-first.

        Providers with an open breaker sort after all allowed ones.
        Duplicates are removed, order otherwise stable.
        """
        if not candidates:
            raise FailoverExhausted("No failover candidates provided.",
                                    attempts=[])
        now = self._clock()
        seen: list[str] = []
        for name in candidates:
            if name not in seen:
                seen.append(name)
        scored = []
        for name in seen:
            breaker_open = not self._breaker(name).allow(now)
            scored.append(
                (breaker_open, -self.health.score(name, at=now), name))
        scored.sort(key=lambda item: (item[0], item[1], item[2]))
        return [name for _, _, name in scored]

    def chat(
        self,
        candidates: list[str],
        messages: list[dict[str, Any]],
        provider_factory: Callable[[str], Provider],
        **kwargs: Any,
    ) -> FailoverResult:
        """Chat via the first healthy candidate that answers.

        ``provider_factory(name)`` builds the adapter (tests inject
        scripted fakes). Tries at most ``policy.max_attempts``
        candidates in :meth:`order` order. Every attempt is timed and
        recorded into the health tracker.
        """
        ordered = self.order(candidates)[:self.policy.max_attempts]
        now = self._clock()
        eligible = [name for name in ordered
                    if self._breaker(name).allow(now)]
        if not eligible:
            skipped = ", ".join(ordered)
            raise FailoverExhausted(
                "All failover candidates have open circuit breakers "
                f"(skipped: {skipped}).",
                attempts=[{"provider": name, "ok": False,
                           "latency_s": 0.0,
                           "error": "circuit breaker open; skipped"}
                          for name in ordered])
        attempts: list[dict[str, Any]] = []
        for name in eligible:
            provider = provider_factory(name)
            breaker = self._breaker(name)
            start = self._clock()
            try:
                text = provider.chat(messages, **kwargs)
            except ProviderError as exc:
                latency = self._clock() - start
                breaker.record_failure(self._clock())
                self.health.record(name, ok=False, latency_s=latency)
                attempts.append({"provider": name, "ok": False,
                                 "latency_s": round(latency, 4),
                                 "error": str(exc)})
                continue
            except Exception as exc:  # pragma: no cover - defensive
                latency = self._clock() - start
                breaker.record_failure(self._clock())
                self.health.record(name, ok=False, latency_s=latency)
                attempts.append({"provider": name, "ok": False,
                                 "latency_s": round(latency, 4),
                                 "error": f"{type(exc).__name__}: {exc}"})
                continue
            latency = self._clock() - start
            breaker.record_success()
            self.health.record(name, ok=True, latency_s=latency)
            attempts.append({"provider": name, "ok": True,
                             "latency_s": round(latency, 4),
                             "error": ""})
            return FailoverResult(text=text, provider=name,
                                  attempts=attempts)
        detail = "; ".join(
            f"{a['provider']}: {a['error']}" for a in attempts)
        raise FailoverExhausted(
            f"All {len(ordered)} failover candidate(s) failed: {detail}",
            attempts=attempts)
