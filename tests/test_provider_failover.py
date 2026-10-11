"""TIER: unit

Unit tests for slice 048 (provider failover).

Fake fixtures only: scripted fake providers stand in for real
adapters; the clock is injectable for deterministic breaker tests.
No live provider calls, no network.
"""

import pytest

from mythic_agent.providers.base import Provider, ProviderError
from mythic_agent.providers.failover import (
    FailoverExhausted,
    FailoverPolicy,
    FailoverRouter,
)
from mythic_agent.providers.health import ProviderHealth


# ----------------------------------------------------------------------
# Fakes
# ----------------------------------------------------------------------

class _ScriptedProvider(Provider):
    """Provider with a scripted outcome queue.

    Each entry is either a string (chat returns it) or an exception
    instance (chat raises it).
    """

    name = "scripted"

    def __init__(self, outcomes):
        super().__init__()
        self._outcomes = list(outcomes)
        self.calls = 0

    def capabilities(self):
        return {"streaming": False, "tool_calling": False,
                "vision": False, "json_mode": False}

    def chat(self, messages, **kwargs):
        self.calls += 1
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


def _router(**kwargs):
    return FailoverRouter(**kwargs)


# ----------------------------------------------------------------------
# Policy validation
# ----------------------------------------------------------------------

def test_policy_validation():
    with pytest.raises(ValueError):
        FailoverPolicy(max_attempts=0)
    with pytest.raises(ValueError):
        FailoverPolicy(cooldown_s=0)
    with pytest.raises(ValueError):
        FailoverPolicy(breaker_threshold=-1)


# ----------------------------------------------------------------------
# Ordering
# ----------------------------------------------------------------------

def test_healthiest_first():
    now = [1000.0]
    health = ProviderHealth(clock=lambda: now[0])
    for _ in range(10):
        health.record("good", ok=True, latency_s=0.1)
    for _ in range(10):
        health.record("bad", ok=False, latency_s=0.1)
    router = _router(health=health, clock=lambda: now[0])
    assert router.order(["bad", "unknown", "good"]) == [
        "good", "unknown", "bad"]


def test_order_dedupes_and_rejects_empty():
    router = _router()
    assert router.order(["a", "b", "a"]) == ["a", "b"]
    with pytest.raises(FailoverExhausted):
        router.order([])


# ----------------------------------------------------------------------
# Failover behavior
# ----------------------------------------------------------------------

def test_first_healthy_provider_wins():
    providers = {
        "a": _ScriptedProvider([ProviderError("a is down")]),
        "b": _ScriptedProvider(["answer from b"]),
    }
    router = _router()
    result = router.chat(["a", "b"], [{"role": "user", "content": "hi"}],
                         provider_factory=providers.__getitem__)
    assert result.text == "answer from b"
    assert result.provider == "b"
    assert [a["provider"] for a in result.attempts] == ["a", "b"]
    assert result.attempts[0]["ok"] is False
    assert result.attempts[1]["ok"] is True
    assert providers["a"].calls == 1
    assert providers["b"].calls == 1


def test_all_fail_raises_with_per_provider_errors():
    providers = {
        "a": _ScriptedProvider([ProviderError("a down")]),
        "b": _ScriptedProvider([ProviderError("b down")]),
    }
    router = _router()
    with pytest.raises(FailoverExhausted) as excinfo:
        router.chat(["a", "b"], [{"role": "user", "content": "hi"}],
                    provider_factory=providers.__getitem__)
    assert "a down" in str(excinfo.value)
    assert "b down" in str(excinfo.value)
    assert len(excinfo.value.attempts) == 2


def test_max_attempts_bounds_candidates():
    providers = {name: _ScriptedProvider([ProviderError(f"{name} down")])
                 for name in ("a", "b", "c")}
    router = _router(policy=FailoverPolicy(max_attempts=2))
    with pytest.raises(FailoverExhausted) as excinfo:
        router.chat(["a", "b", "c"], [{"role": "user", "content": "hi"}],
                    provider_factory=providers.__getitem__)
    assert len(excinfo.value.attempts) == 2
    assert providers["c"].calls == 0


def test_failures_recorded_into_health():
    health = ProviderHealth()
    providers = {
        "a": _ScriptedProvider([ProviderError("down")]),
        "b": _ScriptedProvider(["ok"]),
    }
    router = _router(health=health)
    router.chat(["a", "b"], [{"role": "user", "content": "hi"}],
                provider_factory=providers.__getitem__)
    assert health.score("a") < health.score("b")
    assert health.stats("a")["success_rate"] == 0.0


def test_each_candidate_tried_at_most_once():
    providers = {"a": _ScriptedProvider([ProviderError("down")])}
    router = _router(policy=FailoverPolicy(max_attempts=5))
    with pytest.raises(FailoverExhausted):
        router.chat(["a", "a", "a"], [{"role": "user", "content": "hi"}],
                    provider_factory=providers.__getitem__)
    assert providers["a"].calls == 1


# ----------------------------------------------------------------------
# Circuit breaker
# ----------------------------------------------------------------------

def test_breaker_opens_after_threshold():
    now = [1000.0]
    clock = lambda: now[0]
    providers = {"a": _ScriptedProvider([ProviderError("down")]),
                 "b": _ScriptedProvider(["ok"])}
    router = _router(policy=FailoverPolicy(breaker_threshold=2,
                                          cooldown_s=60.0),
                     clock=clock)
    factory = providers.__getitem__
    messages = [{"role": "user", "content": "hi"}]
    # Two failures open a's breaker; third call skips a entirely.
    for _ in range(2):
        with pytest.raises(FailoverExhausted):
            providers["a"]._outcomes.append(ProviderError("down"))
            router.chat(["a"], messages, provider_factory=factory)
    assert providers["a"].calls == 2
    result = router.chat(["a", "b"], messages, provider_factory=factory)
    assert result.provider == "b"
    assert providers["a"].calls == 2  # a was skipped: breaker open


def test_breaker_half_opens_after_cooldown():
    now = [1000.0]
    clock = lambda: now[0]
    scripted = _ScriptedProvider([ProviderError("down")])
    providers = {"a": scripted}
    router = _router(policy=FailoverPolicy(breaker_threshold=1,
                                          cooldown_s=60.0),
                     clock=clock)
    messages = [{"role": "user", "content": "hi"}]
    with pytest.raises(FailoverExhausted):
        router.chat(["a"], messages,
                    provider_factory=providers.__getitem__)
    assert scripted.calls == 1
    # Still within cooldown: skipped.
    with pytest.raises(FailoverExhausted):
        router.chat(["a"], messages,
                    provider_factory=providers.__getitem__)
    assert scripted.calls == 1
    # Past cooldown: half-open, tried again, now succeeds.
    now[0] += 61.0
    scripted._outcomes.append("recovered")
    result = router.chat(["a"], messages,
                         provider_factory=providers.__getitem__)
    assert result.text == "recovered"
    assert scripted.calls == 2


def test_breaker_success_closes():
    now = [1000.0]
    clock = lambda: now[0]
    scripted = _ScriptedProvider([ProviderError("x"), "fine"])
    providers = {"a": scripted}
    router = _router(policy=FailoverPolicy(breaker_threshold=2),
                     clock=clock)
    messages = [{"role": "user", "content": "hi"}]
    with pytest.raises(FailoverExhausted):
        router.chat(["a"], messages,
                    provider_factory=providers.__getitem__)
    result = router.chat(["a"], messages,
                         provider_factory=providers.__getitem__)
    assert result.text == "fine"
    # Breaker closed by the success: one more failure alone won't open it.
    scripted._outcomes.append(ProviderError("y"))
    with pytest.raises(FailoverExhausted):
        router.chat(["a"], messages,
                    provider_factory=providers.__getitem__)
    assert scripted.calls == 3  # tried, not skipped
