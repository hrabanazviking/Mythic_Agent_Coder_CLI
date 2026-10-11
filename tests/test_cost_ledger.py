"""TIER: unit

Unit tests for slice 046 (cost accounting).

No network, no sockets, no real keys: pricing math runs against the
shared ``core.costs`` table; persistence targets temporary workspaces.
Billing is pinned against the table as the explicit baseline (exact
decimal assertions); ledger throughput is measured locally as a
performance sanity gate — real local numbers, never invented provider
benchmarks.
"""

import json

import pytest

from mythic_agent.core import costs as core_costs
from mythic_agent.providers import cost_ledger
from mythic_agent.providers.base import ChatUsage, ProviderError
from mythic_agent.providers.cost_ledger import CostLedger


# ----------------------------------------------------------------------
# strip_vendor_prefix()
# ----------------------------------------------------------------------

def test_strip_vendor_prefix():
    assert cost_ledger.strip_vendor_prefix("openrouter/gpt-4o") == "gpt-4o"
    assert cost_ledger.strip_vendor_prefix("gpt-4o") == "gpt-4o"
    with pytest.raises(ProviderError):
        cost_ledger.strip_vendor_prefix("")


# ----------------------------------------------------------------------
# Billing math pinned to the shared table (explicit baseline)
# ----------------------------------------------------------------------

def test_price_baseline_matches_shared_table():
    # Baseline: the shared core.costs table and formula.
    rate = core_costs.PRICING["gpt-4o"]
    expected = round(1000 / 1_000_000 * rate["input"]
                     + 250 / 1_000_000 * rate["output"], 6)
    ledger = CostLedger(workspace_root="/tmp/mythic-cost-unused")
    record = ledger.record("openai", "gpt-4o",
                           ChatUsage(prompt_tokens=1000,
                                     completion_tokens=250))
    assert record.cost_usd == expected
    assert record.priced is True


def test_cached_tokens_bill_at_input_rate():
    rate = core_costs.PRICING["claude-3-5-sonnet"]
    ledger = CostLedger(workspace_root="/tmp/mythic-cost-unused")
    record = ledger.record(
        "anthropic", "claude-3-5-sonnet",
        ChatUsage(prompt_tokens=100, completion_tokens=10, cached_tokens=50))
    expected = round(150 / 1_000_000 * rate["input"]
                     + 10 / 1_000_000 * rate["output"], 6)
    assert record.cost_usd == expected


def test_vendor_prefix_prices_through():
    ledger = CostLedger(workspace_root="/tmp/mythic-cost-unused")
    record = ledger.record("openrouter", "openrouter/gpt-4o-mini",
                           ChatUsage(prompt_tokens=1000,
                                     completion_tokens=1000))
    rate = core_costs.PRICING["gpt-4o-mini"]
    expected = round(1000 / 1_000_000 * rate["input"]
                     + 1000 / 1_000_000 * rate["output"], 6)
    assert record.cost_usd == expected
    assert record.model == "openrouter/gpt-4o-mini"  # verbatim attribution


def test_unknown_model_bills_zero_and_flagged(tmp_path):
    ledger = CostLedger(workspace_root=tmp_path)
    record = ledger.record("mystery", "fictional-model-9000",
                           ChatUsage(prompt_tokens=10, completion_tokens=5))
    assert record.cost_usd == 0.0
    assert record.priced is False
    assert ledger.unpriced_models() == ["fictional-model-9000"]


def test_estimated_usage_still_priced_but_flagged(tmp_path):
    ledger = CostLedger(workspace_root=tmp_path)
    record = ledger.record("openai", "gpt-4o-mini",
                           ChatUsage(prompt_tokens=0, completion_tokens=100,
                                     estimated=True))
    assert record.estimated is True
    assert record.priced is True
    assert record.cost_usd > 0.0


def test_record_rejects_bad_input(tmp_path):
    ledger = CostLedger(workspace_root=tmp_path)
    with pytest.raises(ProviderError):
        ledger.record("openai", "gpt-4o", "not-usage")  # type: ignore[arg-type]
    with pytest.raises(ProviderError):
        ledger.record("openai", "gpt-4o",
                      ChatUsage(prompt_tokens=-1, completion_tokens=0))
    with pytest.raises(ProviderError):
        ledger.record("openai", "", ChatUsage(prompt_tokens=1))


# ----------------------------------------------------------------------
# Summaries
# ----------------------------------------------------------------------

def test_totals_and_breakdowns(tmp_path):
    ledger = CostLedger(workspace_root=tmp_path)
    ledger.record("openai", "gpt-4o-mini",
                  ChatUsage(prompt_tokens=1000, completion_tokens=0))
    ledger.record("openai", "gpt-4o-mini",
                  ChatUsage(prompt_tokens=1000, completion_tokens=0))
    ledger.record("mystery", "fictional-model-9000",
                  ChatUsage(prompt_tokens=5, completion_tokens=5))
    rate = core_costs.PRICING["gpt-4o-mini"]
    expected = round(2 * 1000 / 1_000_000 * rate["input"], 6)
    assert ledger.total() == expected
    by_model = ledger.by_model()
    assert by_model["gpt-4o-mini"]["calls"] == 2
    assert by_model["fictional-model-9000"]["unpriced_calls"] == 1
    by_provider = ledger.by_provider()
    assert by_provider["openai"]["calls"] == 2
    assert by_provider["mystery"]["unpriced_calls"] == 1


def test_render_lists_totals(tmp_path):
    ledger = CostLedger(workspace_root=tmp_path)
    ledger.record("openai", "gpt-4o-mini",
                  ChatUsage(prompt_tokens=1000, completion_tokens=0))
    text = ledger.render()
    assert "openai" in text and "Total:" in text


def test_empty_render(tmp_path):
    ledger = CostLedger(workspace_root=tmp_path)
    assert "Total: $0.0000" in ledger.render()


# ----------------------------------------------------------------------
# Persistence
# ----------------------------------------------------------------------

def test_ledger_persists_and_reloads(tmp_path):
    first = CostLedger(workspace_root=tmp_path)
    first.record("openai", "gpt-4o-mini",
                 ChatUsage(prompt_tokens=100, completion_tokens=50))
    second = CostLedger(workspace_root=tmp_path)
    assert len(second.records) == 1
    assert second.total() == first.total()
    assert second.records[0].provider == "openai"


def test_corrupt_ledger_file_loads_empty(tmp_path):
    ledger_path = tmp_path / ".mythic" / "cost_ledger.json"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text("{not valid json", encoding="utf-8")
    ledger = CostLedger(workspace_root=tmp_path)
    assert ledger.records == []
    # Recording still works afterwards (file is rewritten).
    ledger.record("openai", "gpt-4o-mini", ChatUsage(prompt_tokens=1))
    assert len(CostLedger(workspace_root=tmp_path).records) == 1


def test_malformed_entries_skipped_on_load(tmp_path):
    ledger_path = tmp_path / ".mythic" / "cost_ledger.json"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": 1, "records": [
        {"provider": "openai", "model": "gpt-4o-mini",
         "prompt_tokens": 1, "completion_tokens": 1},
        {"provider": "openai"},  # malformed: missing fields
    ]}
    ledger_path.write_text(json.dumps(payload), encoding="utf-8")
    ledger = CostLedger(workspace_root=tmp_path)
    assert len(ledger.records) == 1


# ----------------------------------------------------------------------
# Throughput measurement (real local measurement)
# ----------------------------------------------------------------------

def test_measure_record_throughput_sane():
    ledger = CostLedger(workspace_root="/tmp/mythic-cost-unused")
    rate = ledger.measure_record_throughput(calls=200)
    # Sanity gate: at least 20 priced+persisted records/second on any
    # reasonable machine; the observed value is reported, not asserted
    # as a benchmark claim.
    assert rate > 20, f"ledger throughput unexpectedly low: {rate}/s"
    print(f"\n[measured] CostLedger.record throughput: {rate:.0f} records/s")
