"""Slice 47: cost tracking."""

import pytest

from mythic_agent.core.costs import PRICING, CostTracker, price


def test_price_known_model():
    cost, known = price("gpt-4", 1_000_000, 1_000_000)
    assert known
    assert cost == pytest.approx(90.0)


def test_price_unknown_model():
    cost, known = price("no-such-model", 1000, 1000)
    assert not known
    assert cost == 0.0


def test_record_and_total(tmp_path):
    t = CostTracker(tmp_path)
    t.record("gpt-4o", input_tokens=1_000_000, output_tokens=1_000_000)
    assert t.total() == pytest.approx(12.5)


def test_by_model_aggregation(tmp_path):
    t = CostTracker(tmp_path)
    t.record("gpt-4o-mini", 100, 100)
    t.record("gpt-4o-mini", 100, 100)
    t.record("claude-3-haiku", 100, 100)
    agg = t.by_model()
    assert agg["gpt-4o-mini"]["calls"] == 2
    assert agg["claude-3-haiku"]["calls"] == 1
    assert agg["gpt-4o-mini"]["input_tokens"] == 200


def test_unknown_models_tracked(tmp_path):
    t = CostTracker(tmp_path)
    t.record("mystery-model", 100, 100)
    assert "mystery-model" in t.unknown_models
    assert t.total() == 0.0
    assert "mystery-model" in t.render()


def test_persists_ledger(tmp_path):
    t = CostTracker(tmp_path)
    t.record("gpt-4", 500, 500)
    t2 = CostTracker(tmp_path)
    assert len(t2.records) == 1
    assert t2.records[0].model == "gpt-4"
    assert t2.total() == t.total()


def test_rejects_negative_tokens(tmp_path):
    t = CostTracker(tmp_path)
    with pytest.raises(ValueError):
        t.record("gpt-4", -1, 10)
    with pytest.raises(ValueError):
        t.record("gpt-4", 10, -1)


def test_rejects_empty_model(tmp_path):
    t = CostTracker(tmp_path)
    with pytest.raises(ValueError):
        t.record("", 10, 10)


def test_render_empty(tmp_path):
    t = CostTracker(tmp_path)
    text = t.render()
    assert "no usage recorded" in text
    assert "Total: $0.0000" in text


def test_pricing_table_has_core_models():
    for model in ("gpt-4", "gpt-4o", "claude-3-sonnet", "claude-3-haiku"):
        assert model in PRICING
        assert PRICING[model]["input"] >= 0
        assert PRICING[model]["output"] >= 0
