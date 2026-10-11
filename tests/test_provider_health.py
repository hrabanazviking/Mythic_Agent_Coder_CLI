"""TIER: unit

Unit tests for slice 047 (provider health scoring).

Fake fixtures only: outcomes and latencies are synthetic; the clock is
injectable for deterministic decay tests. No provider is ever called.
"""

import pytest

from mythic_agent.providers.health import ProviderHealth


# ----------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------

def test_constructor_validation():
    with pytest.raises(ValueError):
        ProviderHealth(window_size=0)
    with pytest.raises(ValueError):
        ProviderHealth(half_life_s=-1.0)


def test_record_validation():
    tracker = ProviderHealth()
    with pytest.raises(ValueError):
        tracker.record("", ok=True, latency_s=0.1)
    with pytest.raises(ValueError):
        tracker.record("p", ok="yes", latency_s=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        tracker.record("p", ok=True, latency_s=-0.1)


# ----------------------------------------------------------------------
# Scoring behavior
# ----------------------------------------------------------------------

def test_unknown_provider_scores_neutral():
    tracker = ProviderHealth()
    assert tracker.score("never-seen") == 0.5


def test_all_healthy_fast_scores_near_one():
    tracker = ProviderHealth()
    for _ in range(10):
        tracker.record("fast", ok=True, latency_s=0.05)
    assert tracker.score("fast") > 0.95


def test_all_failing_scores_near_zero():
    tracker = ProviderHealth()
    for _ in range(10):
        tracker.record("dead", ok=False, latency_s=0.05)
    assert tracker.score("dead") < 0.05


def test_mixed_history_scores_between():
    tracker = ProviderHealth()
    for _ in range(5):
        tracker.record("flaky", ok=True, latency_s=0.1)
    for _ in range(5):
        tracker.record("flaky", ok=False, latency_s=0.1)
    score = tracker.score("flaky")
    assert 0.3 < score < 0.7


def test_slow_provider_scores_lower_than_fast():
    fast = ProviderHealth()
    slow = ProviderHealth()
    for _ in range(10):
        fast.record("f", ok=True, latency_s=0.1)
        slow.record("s", ok=True, latency_s=10.0)
    assert slow.score("s") < fast.score("f")


def test_score_bounded():
    tracker = ProviderHealth()
    tracker.record("p", ok=True, latency_s=0.0)
    tracker.record("p", ok=False, latency_s=1e9)
    assert 0.0 <= tracker.score("p") <= 1.0


# ----------------------------------------------------------------------
# Decay
# ----------------------------------------------------------------------

def test_recency_decay_with_injectable_clock():
    now = [1000.0]
    tracker = ProviderHealth(half_life_s=100.0, clock=lambda: now[0])
    # Ten old failures...
    for _ in range(10):
        tracker.record("p", ok=False, latency_s=0.1, at=1000.0)
    old_score = tracker.score("p")
    assert old_score < 0.2
    # ...then one recent success 1000 s later (10 half-lives on).
    now[0] = 2000.0
    tracker.record("p", ok=True, latency_s=0.1)
    new_score = tracker.score("p")
    assert new_score > old_score
    assert new_score > 0.5  # the recent success dominates


def test_stale_data_fades():
    now = [0.0]
    tracker = ProviderHealth(half_life_s=10.0, clock=lambda: now[0])
    tracker.record("p", ok=False, latency_s=0.1)
    assert tracker.score("p") < 0.5
    now[0] = 10_000.0  # far beyond the half-life
    # No new samples: weights decay equally, ratio is unchanged...
    # but the score must still be a valid number, not NaN.
    score = tracker.score("p")
    assert 0.0 <= score <= 1.0


# ----------------------------------------------------------------------
# Window cap
# ----------------------------------------------------------------------

def test_window_slides():
    tracker = ProviderHealth(window_size=5)
    for _ in range(10):
        tracker.record("p", ok=True, latency_s=0.1)
    assert tracker.stats("p")["samples"] == 5


# ----------------------------------------------------------------------
# Stats / snapshot / reset
# ----------------------------------------------------------------------

def test_stats_and_snapshot():
    tracker = ProviderHealth()
    tracker.record("a", ok=True, latency_s=0.2)
    tracker.record("a", ok=True, latency_s=0.4)
    tracker.record("b", ok=False, latency_s=0.1)
    stats = tracker.stats("a")
    assert stats["samples"] == 2
    assert stats["success_rate"] == 1.0
    assert stats["avg_latency_s"] == 0.3
    assert stats["score"] == tracker.score("a")
    snap = tracker.snapshot()
    assert sorted(snap.keys()) == ["a", "b"]
    unknown = tracker.stats("zzz")
    assert unknown["samples"] == 0
    assert unknown["score"] == 0.5


def test_reset():
    tracker = ProviderHealth()
    tracker.record("p", ok=False, latency_s=0.1)
    tracker.reset("p")
    assert tracker.score("p") == 0.5
    assert tracker.stats("p")["samples"] == 0
