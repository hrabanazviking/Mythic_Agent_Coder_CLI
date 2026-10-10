# Test Taxonomy (R-023 / roadmap 023)

Every test module in `tests/` declares its tier in its module docstring:

```
"""
TIER: unit
...
"""
```

## Tiers

| Tier | Meaning | Examples |
|------|---------|----------|
| `unit` | Pure, hermetic, fast. No subprocesses, threads, sockets, or sqlite. Safe to run anywhere, in any order. | `test_exceptions.py`, `test_redaction_audit.py` |
| `integration` | Uses subprocesses, threads, loopback HTTP servers (`127.0.0.1`), sqlite, or asyncio loops. Still no real network and no credentials. | `test_cli.py`, `test_provider_adapters.py` |
| `live` | Touches real networks, real provider APIs, or real credentials. **Skipped by default**; runs only with `MYTHIC_LIVE_TESTS=1`. Never spends money without explicit authorization. | (none currently — the tier exists for future provider live checks) |

## Rules

1. A plain `pytest` run must never require network access or credentials.
   The `live` tier is skipped in `tests/conftest.py` unless
   `MYTHIC_LIVE_TESTS=1` is set.
2. New test modules MUST carry a `TIER:` line in the module docstring.
   `tests/test_taxonomy.py` fails the suite if any module lacks one.
3. Prefer `unit` — promote to `integration` only when the test genuinely
   needs a process, thread, loopback server, or database.
4. `live` tests MUST be marked `@pytest.mark.live`, MUST read credentials
   from the environment (never committed), and MUST be idempotent.

## Current census (2026-10-10 dusk forge)

- 68 test modules: ~45 unit, ~23 integration, 0 live.
- Two modules (`test_openai_compat.py`, `test_provider_contract_v2.py`)
  landed mid-taxonomy-rebuild from the provider worker; their TIER lines
  are added by the same run before the gate closes.
