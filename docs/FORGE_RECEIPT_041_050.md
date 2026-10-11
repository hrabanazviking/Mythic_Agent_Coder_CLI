# Forge Receipt — Slices 041–050 (Provider Negotiation & Pantheon Gate)

**Branch:** `forge-041-050` (from `development` @ `1e4adbc`)
**Date:** 2026-10-11
**Worker:** Worker A, Mythic Coder dusk forge

## Commits

| Commit | Content |
|---|---|
| `282dea2` | Slices 041–044: structured-output, vision, reasoning, streaming negotiation |
| `3e5d402` | Slices 045–046: usage normalization (`ChatUsage` +cached/estimated), cost accounting |
| `f07b8ad` | Slices 047–049: health scoring, failover router, conformance suite |
| `542cce5` | Gate repairs: Google `json_mode` wire shape, doc-sync gates, dead-code |
| `94be877` | Gate repairs 2: coverage-ratchet test list extended, OWNERSHIP regen, baseline doc |

## New modules (`mythic_agent/providers/`)

| Slice | Module | Public surface |
|---|---|---|
| 041 | `structured_output.py` | `negotiate`, `prepare`, `parse_json`, `system_prompt_fallback` |
| 042 | `vision.py` | `normalize`, `VisionPayload`, `has_images`, `MAX_IMAGE_BYTES` |
| 043 | `reasoning.py` | `ReasoningConfig`, `negotiate`, `DEFAULT_THINKING_BUDGET` |
| 044 | `streaming.py` | `parse_openai_sse`, `parse_ndjson`, `parse_ollama_ndjson`, `iter_events`, `collect`, `StreamEvent`, `CancelledStream` |
| 045 | `usage.py` | `normalize`, `normalize_usage_dict`, `estimate_tokens` |
| 046 | `cost_ledger.py` | `CostLedger`, `CallCost`, `strip_vendor_prefix` |
| 047 | `health.py` | `ProviderHealth` (sliding window, decay-weighted 0..1 score) |
| 048 | `failover.py` | `FailoverRouter`, `FailoverPolicy`, `FailoverResult`, `FailoverExhausted` |
| 049 | `conformance.py` | `run_conformance`, `run_pantheon`, `render`, `write_report`, `ConformanceReport` |

`base.py`: `ChatUsage` gains additive `cached_tokens` and `estimated` fields.
`google.py`: `generation_config` type guard + documented passthrough (slice 041 repair).

## Tests

9 new test files, **135 tests**, all passing:

- `test_structured_output.py` (23), `test_vision_negotiation.py` (19)
- `test_reasoning_negotiation.py` (16), `test_streaming_normalization.py` (22)
- `test_usage_normalization.py` (16), `test_cost_ledger.py` (15)
- `test_provider_health.py` (13), `test_provider_failover.py` (12)
- `test_provider_conformance.py` (11)

Coverage: normal / failure / cancellation / boundary behavior per slice;
fake fixtures only — no live provider calls, no network, no real keys.

## Measurements (real, local — never invented)

- Billing math pinned against the shared `core.costs` table by
  exact-decimal assertions (`test_price_baseline_matches_shared_table`,
  `test_cached_tokens_bill_at_input_rate`, `test_vendor_prefix_prices_through`).
- Ledger throughput measured locally in `test_measure_record_throughput_sane`
  (sanity gate > 20 records/s incl. JSON persistence; observed value printed).
- Pantheon conformance sweep: **10/10 providers PASS, 0 failed checks**
  (12 checks each; skips only for live-transport seams never fired here).

## Full suite

`PYTHONPATH=/tmp/wt-041-050 venv/bin/pytest -q -p no:cacheprovider`
(run in an isolated git worktree; the venv's editable install is
path-based so `PYTHONPATH` takes precedence — verified import path).

Final result: **1284 passed, 2 skipped, 0 failed** (full run after all
gate repairs; 2 skips are pre-existing: live-tier opt-in and missing
`textual`). An earlier run caught 7 gate failures total across two
passes — dead-code quarantine, OWNERSHIP.md freshness (twice),
PUBLIC_API.md total, and the providers coverage ratchet — all
repaired and re-verified green.

## Integration gaps found and closed (slice 050)

1. **Google `json_mode` had no wire shape** — `GoogleProvider`
   advertised `json_mode: True` but `structured_output.negotiate()`
   raised "wire shape unknown". Repaired: Gemini `generation_config`
   mapping + passthrough guard in `google.py`; covered by
   negotiate→chat end-to-end test with a stubbed SDK. Conformance now
   10/10.
2. **Dead-code gate** flagged test-only `measure_record_throughput` —
   inlined into the test; no public API change.
3. **Doc drift** — `PUBLIC_API.md` total updated to 1018 (scan-verified),
   `OWNERSHIP.md` regenerated via `scripts/gen_ownership.py`,
   new `docs/PROVIDER_NEGOTIATION.md` user guide.

## Invariants verified

- Workspace: `CostLedger` persists under `<workspace>/.mythic/cost_ledger.json`
  (same pattern as `core.costs`); conformance uses temp dirs only.
- Secrets: no key material in any error string (module code never
  touches credentials); existing redaction tests still green.
- Cancellation: `streaming.collect(cancel=...)` → `CancelledStream`
  with partial text; generator `close()` is safe.
- Machine output: conformance reports serialize to JSON
  (`write_report`); `PUBLIC_API.md` scan count matches live (1018).
- `README.md` untouched; tracked file `main` untouched; no pushes,
  no force-pushes, no rebases.

## Limitations / remaining debt

- Streaming `iter_chunks` seam: no adapter implements it yet — all
  streaming-capable adapters raise `ProviderError` from the base
  implementation. Conformance marks this `skipped` (honest, not hidden);
  wiring real SSE streaming through adapters is future work.
- Reasoning negotiation covers OpenAI / OpenRouter / Anthropic /
  DeepSeek shapes only; other adapters raise `ProviderError`
  (documented as unsupported).
- Usage estimation is a documented `len//4` heuristic flagged
  `estimated=True` — never presented as measured.
- Health-score formula weights (0.65/0.35, 2 s latency scale, 300 s
  half-life) are documented choices, not tuned against production data.
- Vision wire shapes follow vendor docs but were verified against fake
  fixtures only — no live vision calls were made.

## Operational note for the coordinator

During this run a second worker (slices 051–060, branch
`forge-051-060`) was found sharing the same working tree; my first
commit accidentally landed on its branch. Repaired without touching
its work: backed my files up, restored its tree to `64c52ef`
(`reset --soft`, then index reset — its uncommitted changes intact),
moved my work to an isolated worktree (`/tmp/wt-041-050`), and
re-committed on `forge-041-050` from `development`. Recommend
per-worker worktrees (or separate clones) for future parallel forges.
