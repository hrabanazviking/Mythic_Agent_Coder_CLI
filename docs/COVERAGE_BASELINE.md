# Coverage Baseline — providers package (R-024 / roadmap 024)

Measured 2026-10-10 dusk forge with `coverage 7.16.2` (venv-local) over
`tests/test_providers.py`, `tests/test_provider_protocol.py`,
`tests/test_provider_adapters.py`, `tests/test_anthropic_hardening.py`,
`tests/test_redaction_audit.py`.

Extended 2026-10-10 (R-036) with `tests/test_local_provider_adapters.py`;
extended 2026-10-11 (forge 041–050) with `tests/test_structured_output.py`,
`tests/test_vision_negotiation.py`, `tests/test_reasoning_negotiation.py`,
`tests/test_streaming_normalization.py`, `tests/test_usage_normalization.py`,
`tests/test_cost_ledger.py`, `tests/test_provider_health.py`,
`tests/test_provider_failover.py`, `tests/test_provider_conformance.py`.

## Per-module (at measurement time)

| Module | Stmts | Missed | Cover | Missing |
|--------|-------|--------|-------|---------|
| `mythic_agent/providers/__init__.py` | 0 | 0 | 100% | — |
| `mythic_agent/providers/anthropic.py` | 73 | 1 | 99% | 161 (worker C in-flight) |
| `mythic_agent/providers/base.py` | 85 | 25 | 71% | worker B in-flight (contract V2) |
| `mythic_agent/providers/google.py` | 87 | 24 | 72% | worker C in-flight (hardening) |
| `mythic_agent/providers/ollama.py` | 44 | 1 | 98% | 51 (closed by R-024) |
| `mythic_agent/providers/openai_compat.py` | 97 | 97 | 0% | worker B in-flight (new adapter) |
| `mythic_agent/providers/registry.py` | 19 | 0 | 100% | — |
| **TOTAL** | **405** | **148** | **63%** | |

## Ratchet

`tests/test_coverage_assault.py::test_providers_coverage_ratchet` asserts the
package total stays at or above **63%**. The in-flight worker modules
(base, google, openai_compat) carry their own test requirements in their
slice briefs; as they land, this baseline is re-measured upward at the
R-025 Bedrock Gate.
