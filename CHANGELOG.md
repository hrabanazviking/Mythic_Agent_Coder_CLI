# Changelog

All notable changes to Mythic Agent are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning follows [SemVer](https://semver.org/spec/v2.0.0.html). The version
lives in exactly one place — `mythic_agent/__version__.py` — and is resolved
into `pyproject.toml` dynamically by hatchling. Dates are in the user's
release timezone at release time; entries marked *Unreleased* have not been
released.

---

## [Unreleased]

### Added

- **Forge 2026-10-11 dusk — roadmap slices 041–060 ("Pantheon & Well").**
  Twenty slices in two campaigns, full suite **1407 passed / 2 skipped /
  0 failed** (2 skips pre-existing: live tier, missing `textual`):
  - **Provider Pantheon negotiation layer** (`mythic_agent/providers/`):
    041 structured-output negotiation (`structured_output.py` — schema→payload
    transform + JSON-fence fallback parse; also fixed Google advertising
    `json_mode: True` with no wire shape by adding the Gemini
    `generation_config` mapping + a type guard in `GoogleProvider.chat()`);
    042 vision negotiation (`vision.py` — canonical parts → per-family wire
    shapes, strip-or-raise downgrade, 20 MB cap, MIME allowlist);
    043 reasoning-mode negotiation (`reasoning.py` — normalized
    ReasoningConfig → OpenAI/OpenRouter/Anthropic/DeepSeek shapes);
    044 streaming normalization (`streaming.py` — SSE/NDJSON → normalized
    StreamEvent, cancel-safe `collect()`); 045 usage normalization
    (`usage.py` — per-family usage mapping into ChatUsage, additive
    `cached_tokens` + `estimated` fields on ChatUsage, heuristic flagged);
    046 cost accounting (`cost_ledger.py` — usage × shared price table,
    JSON persistence, per-model/per-provider rollups, exact-decimal
    assertions against the price table); 047 provider health scoring
    (`health.py` — 200-sample sliding window, 300 s half-life decay,
    0.65·success + 0.35·latency); 048 provider failover (`failover.py` —
    healthiest-first routing, consecutive-failure circuit breaker,
    half-open cooldown, `FailoverExhausted` with per-provider errors);
    049 provider conformance suite (`conformance.py` — 12-check contract
    harness over fake fixtures, JSON reports, 10/10 providers PASS);
    050 Pantheon Gate — receipt at `docs/FORGE_RECEIPT_041_050.md`, user
    guide `docs/PROVIDER_NEGOTIATION.md`, `docs/PUBLIC_API.md` regenerated
    (1116 public names), `docs/OWNERSHIP.md` re-baselined.
  - **Context compiler** (new package `mythic_agent/context/`, 11 modules,
    `INTERFACE.md`; wired into `mythic_agent/agents/llm.py` behind opt-in
    runtime setting `context_compiler_enabled`, default `false`):
    051 ContextCompiler (ordered blocks from pluggable sources,
    per-source failure → warning, stale TTL wrapper, cancellation via
    threading.Event); 052 TokenBudgetPlanner (tiktoken-when-importable,
    deterministic `len//4` heuristic live path, largest-remainder
    allocation, word-boundary truncation); 053 protocol-group preservation
    (atomic groups never split); 054 repository instruction resolver
    (AGENTS.md/.mythic/.muserules, size-capped, symlink-escape blocked);
    055 instruction precedence (system > repo > dir > file, conflicts
    recorded, provenance); 056 explicit file context (@-mention
    resolution, workspace containment); 057 semantic selection (local
    tf-idf, no embeddings); 058 symbol-aware selection (ast defs/classes);
    059 dependency-aware selection (ast import graph); 060 git-diff-aware
    context (staged/unstaged hunks, secret-redacted, non-git graceful).
    All blocks pass through SecretRedactor; compilation failure degrades
    to no extra context, never a broken turn.
  - 258 new tests (135 provider + 123 context), normal/failure/
    cancellation/boundary per slice; fake-transport seams only — no live
    provider calls, no invented benchmarks.
  - **Unresolved limitations:** no adapter implements `iter_chunks` yet
    (conformance marks streaming `skipped`); reasoning covers 4 families,
    others raise ProviderError; usage estimates are flagged heuristics;
    `tiktoken` not installed so heuristic estimator is live; corpus walks
    capped (200 files / 64 KiB); git-diff source sees tracked-file diffs
    only; `file` precedence layer is API-ready but the current hook
    supplies only system/repo/dir layers.

- **Forge 2026-10-10 dusk — roadmap slices 021–040 (Bedrock tail +
  Provider Pantheon head).** Twenty slices, full suite
  **1149 passed / 2 skipped / 0 failed**:
  - R-021 Secret Redaction Audit: new `google_api_key` (AIza) and
    `xai_key` scanner patterns; `_sensitive_names` extended
    (client_secret, token variants, x-api-key); 20 adversarial gate
    tests; audit finding — raw SDK exceptions leaked key material,
    fixed by R-029/R-030.
  - R-022 Static Analysis Gate: `scripts/static_gate.py` (stdlib-only;
    compile + SyntaxWarning-as-error + no bare-except/eval/exec);
    180 files, 0 hard findings.
  - R-023 Test Taxonomy Rebuild: `TIER: unit/integration/live` lines in
    all test modules; tier markers registered; live tier auto-skips
    without `MYTHIC_LIVE_TESTS=1`; `docs/TEST_TAXONOMY.md`.
  - R-024 Coverage Gap Assault: measured providers baseline (63%) in
    `docs/COVERAGE_BASELINE.md`; closed the stable ollama gap;
    subprocess coverage ratchet gate (now 66%).
  - R-025 Bedrock Gate: receipt `docs/FORGE_RECEIPT_021_025.md`.
  - R-026 Provider Contract V2: message validation, `ChatUsage` /
    `ToolCall` dataclasses, `iter_chunks()` seam, definition-time
    capability-flag validation, timeout/retry knobs.
  - R-027/R-028 OpenAI + OpenAI-compatible local adapters (httpx2):
    auth/error mapping, 429/5xx retry with backoff+jitter, header
    redaction, fake-transport seams; `local-openai` preset.
  - R-029 Anthropic hardening: SDK error mapping
    (`AnthropicAuthError`/`AnthropicRateLimitError`, no key material);
    fixed silently-dropped tool blocks (now `ProviderError`);
    `tool_calling` flag corrected to False.
  - R-030 Gemini hardening: safety-block diagnosis, empty-candidates
    error, role-degradation policy documented, `configure` called once.
  - R-031–R-036 OpenRouter / DeepSeek (reasoning_content fallback) /
    Ollama hardening (fixed 2 real host-validation bugs) /
    llama.cpp / vLLM (token-abc123 convention) / LM Studio adapters.
  - R-037 Capability Discovery (live `/v1/models` probe, TTL cache,
    graceful degradation); R-038 Model Capability Registry (18-pattern
    table); R-039 Context-Window Discovery (registry → probe → 128k
    default, message truncation); R-040 Tool-Call Negotiation
    (OpenAI/Anthropic payload shapes, `ToolCall` normalization).
  - Registry: 3 → 10 adapters with new aliases
    (`gpt`, `llamacpp`/`llama-cpp`, `lm-studio`); R-017 protocol gate
    extended to all 10.

- **Forge 2026-10-10 dawn — Campaign I "Bedrock Truth" (roadmap slices
  001–020).** Twenty hardening slices, each with focused tests:
  - R-001 Repository Truth Census: `core/repo_census.py` (deterministic
    digest, snapshot/verify, CLI); receipt `docs/REPO_CENSUS.md`
    (88 files, 13150 code lines, 123 classes, 806 functions).
  - R-006 Dead-Code Quarantine: stdlib-ast scanner
    `core/dead_code_scan.py`; inventory `docs/DEAD_CODE_QUARANTINE.txt`
    (81 items); gate test fails on new dead code; removed 2 safe
    private helpers (`_timeout_output`, `_use_color`).
  - R-002 Architecture Conformance Audit: `core/arch_conformance.py`
    (20 layering rules as data, import-graph gate); fixed 3 real
    violations — `core/engine.py→terminal` and
    `core/validation.py→agents.tools` dependency inversions eliminated
    via new `core/recovery.py` / `core/tool_schemas.py`; 2 broken
    relative imports in `ui/screens/chat_screen.py` fixed.
  - R-007 Type Coverage: ast-based measurement
    `core/type_coverage.py`; params 870/925 → 901/942, returns
    666/795 → 712/807 across 7 annotated core modules; ratchet gate.
  - R-004 Dependency/Extras Audit: declared `httpx`/`httpx2` (both —
    `httpx2` is openai 3.x's real installed fork, plain `httpx` the
    fallback), `anthropic`/`google` extras, `torch` in voice-cloning,
    Apache-2.0 license metadata; restored the
    try/except-ImportError httpx fallback in `core/execution.py`
    (bare `import httpx` broke provider-live checks where only
    httpx2 is installed); fallback-shape gate test.
  - R-003 Public API Inventory: `__all__` on 82 modules (875→907
    public names); generated `docs/PUBLIC_API.md`; rot-check gate.
  - R-008 Exception Taxonomy V2: `core/exceptions.py` (`MythicError`
    + 10 domain categories with machine codes and `to_dict()`);
    15 existing exception classes migrated with multiple inheritance
    preserving old `except` clauses.
  - R-009 Configuration Schema V2: `CONFIG_SCHEMA` derived from
    `config_defaults.yaml` (parity-tested); `validate_config()`
    dotted-path problems; strict mode (`MYTHIC_STRICT_CONFIG`)
    rejecting unknown keys with difflib hints;
    `redacted_summary()` for safe logging.
  - R-010 Resource Loading Hardening: 1 MiB size cap, strict typed
    loaders (missing/malformed/oversized/traversal rejected),
    traversal-safe `resource_path()` / `load_resource()`.
  - R-011 Deterministic Startup: `core/determinism.py`; fixed
    `mythic costs --json` nondeterministic ordering; volatile
    machine-output fields documented.
  - R-012 Shutdown Correctness: `core/lifecycle.py` (bounded
    `shutdown_all`, idempotent `install_atexit`); all daemon
    threads registered with stop events.
  - R-013 Cancellation Correctness: `grep_search` cancel checks;
    `TurnCancelled` no longer swallowed; cancel-event poisoning
    fixed (ordinary failures no longer mark the shared event).
  - R-014 Thread Ownership Audit: `core/thread_audit.py`
    (`ThreadRegistry`, `LoopAffinity`, diagnostics); named threads
    at all spawn sites.
  - R-015 Async Boundary Audit: bridge contract documented and
    tested (exception identity preserved; in-loop offload codified).
  - R-016 Serialization Invariants: `canonical_json()`,
    `strict_json_loads()`, `decode_json_bytes()` in storage;
    `session_to_dict/from_dict`, `config_to_dict/from_dict`;
    fixed unchecked session timestamps and `UsageRecord.from_dict`
    bare-KeyError.
  - R-017 Provider Protocol Invariants: signature/exception/registry
    conformance gate (no network); fixed `ollama._post` leaking
    raw `ValueError`/`JSONDecodeError` (now `ProviderError`).
  - R-018 Workspace Identity Invariants: canonical `workspace_id()`,
    `assert_within_workspace()` containment, `SecurityError` on
    escapes.
  - R-019 Session Identity Invariants: corrupt storage/row errors
    now name the file/session (were raw `sqlite3.DatabaseError` /
    `JSONDecodeError`); stale-lock semantics proven by tests.
  - R-020 Edit Journal Integrity: 8 attack scenarios all held;
    added `auto_vacuum_threshold` bounding tombstone growth.
  - R-005 Source Ownership Map: `scripts/gen_ownership.py`;
    generated `docs/OWNERSHIP.md` (95 modules).
- **Slice 2 (S08) — Agent lifecycle and controlled orchestration.**
  Typed task IDs with queued/running/completed/failed/cancelled states,
  parent/child relationships, registry locking, delegation-cycle detection,
  cancellation propagation, and configured concurrency/turn/tool budgets
  (`mythic_agent/agents/tasks.py`). 16 tests.
- **Slice 7 (S13) — Stable machine API, MCP, and extension contracts.**
  Versioned MCP tools on the shared workspace/policy/session/task services:
  `mythic_task_status`, `mythic_task_cancel`, `mythic_capabilities`, plus the
  memory/delegation tools over stdio without loading the TUI.
- **Slice 10 — Crash recovery and auto-save.** Durable crash handling with
  safe auto-save and recovery of in-flight work.
- **Slice 11 — Health checks and self-diagnostics.** New `mythic doctor`
  command (`mythic_agent/doctor.py`): checks config, providers, tools,
  sessions, disk, and dependencies; `--json` for machines, `--fix` for safe
  auto-repairs, `--live` for opt-in live provider checks, `--check` to run
  named checks only. 6 tests.
- **Slice 12 — Structured logging everywhere.** JSON and text formatters
  with file output (`mythic_agent/core/mythic_logging.py`). 6 tests.
- **Slice 13 — Graceful degradation.** Optional integrations report as
  unavailable instead of breaking core flows.
- **Slice 14 — Input validation and security hardening.** Stricter input
  validation across tool boundaries.
- **Slice 28 — Benchmark suite.** `mythic_agent/bench.py` measures startup,
  import, and memory as JSON so performance claims stay measured.
- **Slice 39 — Shell completions.** Bash, zsh, and fish completions in
  `completions/` (`mythic.bash`, `_mythic.zsh`, `mythic.fish`).
- **Slice 8 (S14) — Release readiness, part 1.** This changelog,
  `docs/RELEASE_CHECKLIST.md` with measured quality gates, and
  single-sourced versioning: `mythic_agent/__version__.py` is now the one
  place the version lives; `pyproject.toml` resolves it dynamically.
- **Slice 49 (1.0 packaging).** Verified entry points (`mythic`,
  `mythic-mcp`), wheel/sdist resource inclusion, and README build metadata;
  packaging checklist recorded in `docs/RELEASE_CHECKLIST.md`.
- **Slice 50 — Documentation and launch, part 1.** New comprehensive
  `docs/USER_GUIDE.md`, `docs/API.md`, and README feature additions
  (doctor, tasks, cache, costs, metrics, review, tutorial, completions, MCP).
- Working-tree commands landed during the surge: `mythic cache`
  (inspect/clear the LLM response cache), `mythic costs` (model API cost
  ledger), `mythic metrics` (recorded metrics and traces), `mythic review`
  (static review of Python files), `mythic tutorial` (interactive first-run
  tutorial), `mythic theme` (list/apply color themes), and
  `mythic sessions --search` (filter sessions).

### Changed

- Version is now single-sourced: bump `mythic_agent/__version__.py` only;
  `mythic --version` falls back to it in source checkouts instead of a
  hardcoded string in `cli.py`.

### Fixed

- Test suite health: per-test 120s timeout via `pytest-timeout` so a stalled
  test fails loudly instead of hanging the suite.

---

## [0.1.0] — Roadmap foundation (S01–S06)

### Added

- **S01 — Reproducible installation and automated baseline.** Lightweight
  core install with separate `tui`, `voice`, `knowledge`, `mcp`, and `dev`
  extras; lazy-loaded optional front ends; personas and the engineering
  protocol packaged into wheels; Linux/macOS/Windows × Python 3.10/3.13 CI.
- **S02 — Repaired shared conversation runtime.** First-turn fix, normalized
  SDK messages, one assistant message per text+tool-calls group, typed
  outcomes, finite tool/retry budgets, transient-error classification, and
  cancellation at loop/retry boundaries.
- **S03 — Workspace boundaries, safe edits, trustworthy undo.** Explicit
  workspace resolution, traversal/symlink escape refusal, atomic writes,
  workspace-scoped private SQLite edit journal, stale-undo refusal, no
  implicit Git commits during tool writes.
- **S04 — Terminal chat and noninteractive CLI.** `mythic chat`, `mythic
  run` (stdin/prompt, `--workspace`, endpoint/model selection, explicit
  permission mode, plain/JSON/JSONL output, stable exit codes), `mythic
  tui`; slash commands `/help /clear /compact /session /model /status /add
  /stop /undo /quit`.
- **S05 — Durable sessions, resume, robust configuration.** Workspace-scoped
  versioned SQLite session store with exclusive leases, atomic config
  saves with recoverable backups, credential redaction in exports/logs,
  `MYTHIC_HOME` isolation, additive config migrations.
- **S06 — Permission policy and cancellable execution.** Explicit
  read-only/ask/trusted modes wired through all tool paths (TUI, CLI, MCP,
  delegation), owned process/request services with full output and exit
  codes, cancellation that cleans owned process groups/jobs.

[Unreleased]: https://github.com/hrabanazviking/Mythic_Agent_Coder_CLI/compare/v0.1.0...development
[0.1.0]: https://github.com/hrabanazviking/Mythic_Agent_Coder_CLI/releases/tag/v0.1.0
