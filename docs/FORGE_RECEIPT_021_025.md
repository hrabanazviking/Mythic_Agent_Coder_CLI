# Forge Receipt — roadmap slices 021–025 + dusk-run close (R-025 Bedrock Gate)

**Run:** mythic-coder-dusk-forge, 2026-10-10 17:41 EDT
**Branch:** `development` | **Scope:** roadmap slices 021–040 (20 slices)

## What this gate reviewed

Roadmap slices 001–025 ("Bedrock Truth" campaign body + tail) plus the
dusk run's Provider Pantheon head (026–040). Slices 001–020 were forged by
the dawn run; 021–040 by this run.

## Full-suite result

- **1147 passed, 2 skipped, 0 failed** (full `pytest tests/`, per-test 120s
  timeout; second run after fixing 2 integration fallouts — see below).
- First full run: 1147 passed / 2 failed. Both failures were honest
  integration consequences, fixed, re-run green:
  1. `TestLlamaCpp::test_name_is_registry_safe` asserted the `llama.cpp`
     name was *absent* from the registry — true only pre-integration.
     Rewrote to assert registered-exactly-once + alias resolution.
  2. `test_ownership.py::test_doc_is_fresh` — `docs/OWNERSHIP.md` went
     stale after the registry-integration commit; regenerated.
- Skips (2, both legitimate): live-tier probe (needs `MYTHIC_LIVE_TESTS=1`),
  textual import (optional TUI extra not installed).

## Invariants verified (no regressions)

- Static gate: 180 files, **0 hard findings** (compile, SyntaxWarning,
  bare-except, eval/exec); 51 print() in CLI surfaces; 7 TODO debt markers.
- Dead-code quarantine current; architecture conformance green; repo
  census green; public API doc resynced (965 names); ownership map fresh.
- No new test skips except the live-tier machinery (conftest).
- `README.md` and the 500-slice roadmap file untouched (verified by diff).
- No force-push; 25 commits, all pushed and verified via `git ls-remote`.

## Integration gaps found and closed

- R-017 protocol test and `test_providers.py` hardcoded the 3 old
  adapters — extended to all 10 (the protocol gate now covers the pantheon).
- `test_registry_rejects_unknown_provider` used `"deepseek"` as its unknown
  name — now a real provider; switched to a truly unknown name.
- R-021 audit finding (raw SDK exceptions leaking key material) — fixed by
  R-029/R-030 `_map_sdk_error`; `redact_text` proven as defense-in-depth.

## Measurements

- Providers coverage: **66%** (ratchet floor 63%, re-measured upward from
  the 63% R-024 baseline as worker tests landed).
- Test count: 875 passed / 1 skipped (dawn baseline) → **1147 passed /
  2 skipped** (+272 tests, all real).

## Remaining debt / limitations

- No live-provider validation performed (no credentials, no network in
  tests — by design; roadmap prime directive 10/11 honored).
- `probe_capabilities()` and the doctor's live check are explicitly
  live-only and untested against real endpoints.
- Model capability registry is a curated table (18 patterns); unknown
  models degrade to (all-False, 8192) by design.
- vLLM `token-abc123` placeholder and `len//4` token estimator are
  documented heuristics, not measurements.
- `GenericLocalCompatProvider` name `local-openai` coexists with the
  `local`→`ollama` alias (distinct names, no clash; documented).

## Artifacts

- 20 slice commits (R-021…R-040) + integration/ownership/chore commits.
- `docs/TEST_TAXONOMY.md`, `docs/COVERAGE_BASELINE.md`,
  `scripts/static_gate.py`, `CHANGELOG.md` run entry.
- This receipt: `docs/FORGE_RECEIPT_021_025.md`.
