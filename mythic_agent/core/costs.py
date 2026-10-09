"""Cost tracking for model API usage.

Records input/output token counts per model, prices them against a
pricing table, and persists a running ledger in the workspace
``.mythic/costs.json``.  Models not in the table are billed as
``"unknown"`` (zero cost, flagged in the ledger).

Usage:
    from mythic_agent.core.costs import CostTracker
    tracker = CostTracker(workspace_root)
    tracker.record("gpt-4", input_tokens=1000, output_tokens=250)
    print(tracker.total())       # -> 0.02...
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


#: Price per 1M tokens (USD).  Kept conservative; update when vendors move.
PRICING: dict[str, dict[str, float]] = {
    "gpt-4": {"input": 30.0, "output": 60.0},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    "gpt-4o": {"input": 2.50, "output": 10.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "o1": {"input": 15.0, "output": 60.0},
    "o1-mini": {"input": 1.10, "output": 4.40},
    "claude-3-opus": {"input": 15.0, "output": 75.0},
    "claude-3-sonnet": {"input": 3.0, "output": 15.0},
    "claude-3-haiku": {"input": 0.25, "output": 1.25},
    "claude-3-5-sonnet": {"input": 3.0, "output": 15.0},
    "claude-3-5-haiku": {"input": 0.80, "output": 4.0},
    "claude-3-7-sonnet": {"input": 3.0, "output": 15.0},
    "qwen-2.5-72b": {"input": 0.35, "output": 0.40},
    "deepseek-chat": {"input": 0.14, "output": 0.28},
    "deepseek-reasoner": {"input": 0.55, "output": 2.19},
    "llama-3.3-70b": {"input": 0.35, "output": 0.40},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.0},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
}


@dataclass
class UsageRecord:
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": self.cost_usd,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> "UsageRecord":
        return cls(
            model=obj["model"],
            input_tokens=int(obj["input_tokens"]),
            output_tokens=int(obj["output_tokens"]),
            cost_usd=float(obj["cost_usd"]),
            timestamp=obj.get("timestamp", ""),
        )


def price(model: str, input_tokens: int, output_tokens: int) -> tuple[float, bool]:
    """Return (cost_usd, known).  Unknown models bill at 0.0."""
    rate = PRICING.get(model)
    if rate is None:
        return 0.0, False
    cost = input_tokens / 1_000_000 * rate["input"] + output_tokens / 1_000_000 * rate["output"]
    return round(cost, 6), True


class CostTracker:
    """Accumulate token usage and cost, persisted per workspace."""

    def __init__(self, workspace_root: str | Path | None = None) -> None:
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        self.ledger_path = self.workspace_root / ".mythic" / "costs.json"
        self._records: list[UsageRecord] = []
        self._unknown_models: set[str] = set()
        self._load()

    # -- recording -----------------------------------------------------------
    def record(self, model: str, input_tokens: int, output_tokens: int) -> UsageRecord:
        if not model:
            raise ValueError("model is required")
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError("token counts must be non-negative")
        cost, known = price(model, input_tokens, output_tokens)
        if not known:
            self._unknown_models.add(model)
        rec = UsageRecord(model=model, input_tokens=input_tokens, output_tokens=output_tokens, cost_usd=cost)
        self._records.append(rec)
        self._save()
        return rec

    # -- summaries -----------------------------------------------------------
    def total(self) -> float:
        return round(sum(r.cost_usd for r in self._records), 6)

    def by_model(self) -> dict[str, dict[str, Any]]:
        summary: dict[str, dict[str, Any]] = {}
        for rec in self._records:
            agg = summary.setdefault(
                rec.model,
                {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0},
            )
            agg["calls"] += 1
            agg["input_tokens"] += rec.input_tokens
            agg["output_tokens"] += rec.output_tokens
            agg["cost_usd"] = round(agg["cost_usd"] + rec.cost_usd, 6)
        return summary

    @property
    def unknown_models(self) -> set[str]:
        return set(self._unknown_models)

    @property
    def records(self) -> list[UsageRecord]:
        return list(self._records)

    # -- rendering -----------------------------------------------------------
    def render(self) -> str:
        lines = ["Model usage and cost:"]
        per = self.by_model()
        if not per:
            lines.append("  (no usage recorded)")
        else:
            for model in sorted(per):
                agg = per[model]
                lines.append(
                    f"  {model}: {agg['calls']} call(s), "
                    f"{agg['input_tokens']} in / {agg['output_tokens']} out tokens, "
                    f"${agg['cost_usd']:.4f}"
                )
        lines.append(f"Total: ${self.total():.4f}")
        if self._unknown_models:
            lines.append("Unpriced models (billed $0): " + ", ".join(sorted(self._unknown_models)))
        return "\n".join(lines)

    # -- persistence ---------------------------------------------------------
    def _save(self) -> None:
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "records": [r.to_dict() for r in self._records],
            "unknown_models": sorted(self._unknown_models),
        }
        self.ledger_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _load(self) -> None:
        if not self.ledger_path.exists():
            return
        try:
            payload = json.loads(self.ledger_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        self._records = [UsageRecord.from_dict(r) for r in payload.get("records", [])]
        self._unknown_models = set(payload.get("unknown_models", []))
