"""Per-call cost accounting over normalized usage (Slice 046).

:class:`CostLedger` prices one call as ``usage x model price``:

* The price source is the shared :mod:`mythic_agent.core.costs` table
  (:func:`~mythic_agent.core.costs.price`) — the single source of
  truth for per-1M-token rates. This module adds provider attribution
  and per-call records on top; it never duplicates the rate table.
* Vendor prefixes are stripped before lookup (``"openrouter/gpt-4o"``
  prices as ``"gpt-4o"``).
* Cached tokens bill at the input rate (no discounted cache tier
  exists in the shared table; documented here).
* Estimated usage (``ChatUsage.estimated``) is still priced, but the
  record keeps ``estimated=True`` so reports can separate measured
  from heuristic cost.

Records persist as JSON (default
``<workspace>/.mythic/cost_ledger.json``); the file format is
versioned (``"version": 1``) and corrupt files load as an empty
ledger rather than crashing the caller.

Reproducible measurement: the billing formula is pinned against the
shared table by exact-decimal assertions in
``tests/test_cost_ledger.py`` (the baseline), and ledger throughput
is measured locally (records/second) as a performance sanity gate —
real local measurements, never invented provider benchmarks.
"""


from __future__ import annotations

__all__ = [
    "CallCost",
    "CostLedger",
    "Provider",
    "ProviderError",
    "strip_vendor_prefix",
]

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from ..core.costs import price as _price
from .base import ChatUsage, Provider, ProviderError


#: Version tag written into persisted ledger files.
LEDGER_VERSION = 1


@dataclass
class CallCost:
    """One priced provider call."""

    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cached_tokens: int = 0
    cost_usd: float = 0.0
    priced: bool = False
    estimated: bool = False
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> "CallCost":
        try:
            return cls(
                provider=str(obj["provider"]),
                model=str(obj["model"]),
                prompt_tokens=int(obj["prompt_tokens"]),
                completion_tokens=int(obj["completion_tokens"]),
                cached_tokens=int(obj.get("cached_tokens", 0)),
                cost_usd=float(obj.get("cost_usd", 0.0)),
                priced=bool(obj.get("priced", False)),
                estimated=bool(obj.get("estimated", False)),
                timestamp=str(obj.get("timestamp", "")),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderError(
                f"Malformed cost-ledger record: {exc}") from exc


def strip_vendor_prefix(model: str) -> str:
    """Strip an OpenRouter-style ``vendor/`` prefix for price lookup."""
    if not isinstance(model, str) or not model:
        raise ProviderError(
            f"model must be a non-empty string, got {model!r}")
    return model.split("/")[-1]


class CostLedger:
    """Accumulate per-call costs with provider attribution."""

    def __init__(self, workspace_root: Optional[str | Path] = None) -> None:
        self.workspace_root = Path(workspace_root) if workspace_root \
            else Path.cwd()
        self.ledger_path = (self.workspace_root / ".mythic"
                            / "cost_ledger.json")
        self._records: list[CallCost] = []
        self._load()

    # -- recording --------------------------------------------------------

    def record(
        self,
        provider_name: str,
        model: str,
        usage: ChatUsage,
        *,
        timestamp: Optional[str] = None,
    ) -> CallCost:
        """Price one call and append it to the ledger.

        ``provider_name``/``model`` are recorded verbatim; pricing
        looks up the vendor-stripped model id in the shared table.
        """
        if not isinstance(usage, ChatUsage):
            raise ProviderError(
                "usage must be a ChatUsage, "
                f"got {type(usage).__name__}")
        if usage.prompt_tokens < 0 or usage.completion_tokens < 0 \
                or usage.cached_tokens < 0:
            raise ProviderError("token counts must be non-negative")
        priced_model = strip_vendor_prefix(model)
        # Cached tokens bill at the input rate: priced as extra prompt
        # tokens (documented; the shared table has no cache tier).
        cost, known = _price(
            priced_model,
            usage.prompt_tokens + usage.cached_tokens,
            usage.completion_tokens)
        record = CallCost(
            provider=str(provider_name or "unknown"),
            model=str(model),
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            cached_tokens=usage.cached_tokens,
            cost_usd=cost,
            priced=known,
            estimated=bool(usage.estimated),
            timestamp=timestamp or datetime.now(
                timezone.utc).isoformat(),
        )
        self._records.append(record)
        self._save()
        return record

    # -- summaries ---------------------------------------------------------

    def total(self) -> float:
        return round(sum(r.cost_usd for r in self._records), 6)

    def by_model(self) -> dict[str, dict[str, Any]]:
        summary: dict[str, dict[str, Any]] = {}
        for record in self._records:
            agg = summary.setdefault(record.model, {
                "calls": 0, "prompt_tokens": 0, "completion_tokens": 0,
                "cost_usd": 0.0, "unpriced_calls": 0})
            agg["calls"] += 1
            agg["prompt_tokens"] += record.prompt_tokens
            agg["completion_tokens"] += record.completion_tokens
            agg["cost_usd"] = round(agg["cost_usd"] + record.cost_usd, 6)
            if not record.priced:
                agg["unpriced_calls"] += 1
        return summary

    def by_provider(self) -> dict[str, dict[str, Any]]:
        summary: dict[str, dict[str, Any]] = {}
        for record in self._records:
            agg = summary.setdefault(record.provider, {
                "calls": 0, "cost_usd": 0.0, "unpriced_calls": 0})
            agg["calls"] += 1
            agg["cost_usd"] = round(agg["cost_usd"] + record.cost_usd, 6)
            if not record.priced:
                agg["unpriced_calls"] += 1
        return summary

    @property
    def records(self) -> list[CallCost]:
        return list(self._records)

    def unpriced_models(self) -> list[str]:
        return sorted({r.model for r in self._records if not r.priced})

    def render(self) -> str:
        lines = ["Provider call costs:"]
        for provider in sorted(self.by_provider()):
            agg = self.by_provider()[provider]
            lines.append(
                f"  {provider}: {agg['calls']} call(s), "
                f"${agg['cost_usd']:.4f}")
        lines.append(f"Total: ${self.total():.4f}")
        unpriced = self.unpriced_models()
        if unpriced:
            lines.append("Unpriced models (billed $0): "
                         + ", ".join(unpriced))
        return "\n".join(lines)

    # -- throughput measurement --------------------------------------------

    def measure_record_throughput(self, calls: int = 1000) -> float:
        """Measure local ``record()`` throughput (records/second).

        Uses the real ``record()`` path (pricing math + JSON
        persistence) against a throwaway temporary workspace, so the
        measurement exercises production code and never touches the
        caller's ledger file. The returned value is the observed local
        rate — never a claim about any provider.
        """
        import tempfile
        with tempfile.TemporaryDirectory(
                prefix="mythic-cost-bench-") as tmpdir:
            probe = CostLedger(workspace_root=tmpdir)
            sample = ChatUsage(prompt_tokens=100, completion_tokens=50)
            start = time.perf_counter()
            for _ in range(calls):
                probe.record("bench", "gpt-4o-mini", sample)
            elapsed = time.perf_counter() - start
        return calls / elapsed if elapsed > 0 else float("inf")

    # -- persistence ---------------------------------------------------------

    def _save(self) -> None:
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": LEDGER_VERSION,
            "records": [r.to_dict() for r in self._records],
        }
        self.ledger_path.write_text(json.dumps(payload, indent=2),
                                    encoding="utf-8")

    def _load(self) -> None:
        if not self.ledger_path.exists():
            return
        try:
            payload = json.loads(
                self.ledger_path.read_text(encoding="utf-8"))
            entries = payload.get("records", [])
        except (json.JSONDecodeError, OSError, AttributeError):
            return  # corrupt file -> empty ledger, never a crash
        records: list[CallCost] = []
        for entry in entries:
            try:
                records.append(CallCost.from_dict(entry))
            except ProviderError:
                continue  # skip malformed entries, keep the rest
        self._records = records
