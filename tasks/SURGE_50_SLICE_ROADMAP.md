# SURGE: 50-Slice Roadmap — Mythic_Agent_Coder_CLI

**Goal 3 of Volmarr's coding surge (2026-10-09).**
Make the program work properly according to all data in the repo, then massively improve it.

**Baseline (2026-10-09):**
- Existing roadmap S01–S06 complete and pushed (packaging, runtime repair, workspace safety, terminal chat, sessions, permissions).
- S07 work order published, implementation started, not complete.
- S08–S14 pending.
- 78 Python files (~3,851 lines in `mythic_agent/`), 164 tests, many failing in `tests/test_cli.py` (provider auth for local fake endpoints, hanging test).
- Local venv at `./venv` with core+dev dependencies installed.

**Execution contract (from TASK_development_roadmap.md + surge rules):**
Each slice: work order → implement → targeted tests → full gates → review → commit → push `development` → verify remote HEAD → next slice. Never force-push. Preserve Volmarr's edits. Mythic Engineering 6-phase per slice: Skald → Rúnhild → Eldra → Sólrún → Védis → Scribe.

---

## PHASE A — Complete the existing roadmap (slices 1–8)

### Slice 1: S07 — Provider adapters, streaming, diagnostics (finish)
**Problem:** S07 work order published; local fake-endpoint tests fail with "No API key found" for `http://127.0.0.1` endpoints. Streaming, retry budgets, and diagnostics incomplete.
**Work:**
- Allow local/OpenAI-compatible endpoints without API keys (detect loopback, skip auth).
- Implement streaming text/tool deltas into normalized protocol messages.
- Finite retry budget with cancellable backoff; fail fast on 401/invalid model.
- Track real token usage; report unknown cost instead of inventing pricing.
- `mythic doctor --provider` offline diagnostics + live connectivity check.
**Gates:** `tests/test_cli.py` provider tests pass; new streaming/retry tests; no real-provider charges (fake HTTP fixtures only).

### Slice 2: S08 — Agent lifecycle and controlled orchestration
**Problem:** `AGENT_REGISTRY` is a bare global dict; no typed task IDs, no duplicate-worker prevention, no delegation-cycle detection.
**Work:**
- Typed `TaskId`, task states (queued/running/completed/failed/cancelled), parent links.
- Registry with locking; reject duplicate workers and recursive delegation.
- Concurrency/turn/tool budgets per agent; cancellation propagation; graceful shutdown.
- Serializable ghost-context snapshots, workspace-scoped identity.
**Gates:** spawn/delegate/message/cancel tests, nested delegation, cycle rejection, clean shutdown.

### Slice 3: S09 — Human interface polish and UI stability
**Problem:** TUI event bind/unbind races, small-terminal layout issues, UI calls from wrong threads.
**Work:**
- Safe mount/unmount event subscription; thread-guard all UI calls.
- Responsive layout down to 80x24; multiline input, paste handling.
- Readable diffs and tool output rendering; pending-input indicator.
- Dependable stop/resume/approval modals; escape markup in model output.
**Gates:** Textual pilot tests (startup, chat, approval, stop, rapid switching, small terminal).

### Slice 4: S10 — Repository workflows and configurable integrations
**Problem:** Git/GitHub commands scattered; tokens risk logging; DB config machine-specific.
**Work:**
- Centralize command routing across TUI/CLI/MCP.
- Commit-scope preview; capture Git errors; never touch unrelated staged work.
- Workspace-scoped `gh` invocations; redact tokens from all logs.
- Read-only SQL enforced at transaction level; opt-in DB configuration.
**Gates:** temp-repo Git tests preserve dirty/index; fake GitHub adapter verifies args and refusals.

### Slice 5: S11 — Useful context, memory, and repository instructions
**Problem:** Memory keyed only by agent name (cross-workspace leakage); no repo-instruction provenance.
**Work:**
- Workspace-isolated memory namespaces; sanitize agent identifiers.
- Repository instructions (`AGENTS.md` etc.) loaded with file provenance.
- Context assembler respects model limits without cutting protocol groups.
- Offline-capable retrieval; embedding endpoint configured separately from chat.
**Gates:** cross-workspace isolation, corrupt-memory recovery, offline recall, overflow handling.

### Slice 6: S12 — Resumable roadmap/slice execution inside Mythic
**Problem:** Volmarr's desired "do slices automatically" loop is not a feature.
**Work:**
- Versioned plan/task state with checkpoints; pause/stop/resume.
- Execute → checks → review → commit/push per authorization → verify → next.
- Failure repair budgets; approval handoff; human steering commands.
- Push verification required; a model's claim never marks completion.
**Gates:** end-to-end fake-provider/temp-Git tests: two slices, failed-test recovery, restart resume.

### Slice 7: S13 — Stable machine API, MCP, and extension contracts
**Problem:** MCP server exists but contracts unversioned; extension system absent.
**Work:**
- Version JSON schemas for requests/events/results; document exit codes.
- MCP tools: task status/result, run/resume/cancel, capabilities.
- Extension registration with schema validation and explicit permissions.
- No auto-execution of untrusted repo plugins.
**Gates:** MCP stdio/client tests; contract fixtures; denied-permission tests.

### Slice 8: S14 — Release readiness, documentation, measured quality
**Problem:** No release checklist, no measured quality gates.
**Work:**
- Multi-platform CI green (Linux/macOS/Windows × 3.10–3.13).
- Bounded soak tests; measured startup time and memory footprint.
- Tutorials for human and machine callers; release checklist document.
- All release gates verified: fresh install, help/machine task/chat, no destructive defaults, no secret leaks.
**Gates:** CI matrix green; soak test passes; docs complete.

---

## PHASE B — Reliability hardening (slices 9–14)

### Slice 9: Fix hanging test + test suite health
**Problem:** `test_two_process_turns_resume_transcript_and_token_total` hangs; suite aborts.
**Work:** Identify hang (likely process/session lock), fix root cause, add per-test timeouts via `pytest-timeout`, ensure `pytest tests/` completes in <5 min.

### Slice 10: Crash recovery and auto-save
**Work:** Crash-safe session journaling (write-ahead log); on startup detect unclean shutdown and offer resume; `mythic_crash_*.txt` style dumps replaced with structured crash reports.

### Slice 11: Health checks and self-diagnostics
**Work:** `mythic doctor` full system check (config, providers, tools, sessions, disk); `--fix` for safe auto-repairs; startup self-test with clear error messages.

### Slice 12: Structured logging everywhere
**Work:** Replace `print()` with structured JSON logging (per Operational_Refactoring P2); log levels; log rotation; `mythic logs` command.

### Slice 13: Graceful degradation
**Work:** Every optional integration (voice, images, DB, MCP) fails independently with clear messages; core chat never blocked by optional failures.

### Slice 14: Input validation and security hardening
**Work:** Validate all tool arguments (schema-based); sandbox file operations to workspace (already partial — complete it); secrets redaction audit; no API keys in logs/transcripts.

---

## PHASE C — Intelligence upgrades (slices 15–22)

### Slice 15: Smart context assembly
**Work:** Token-budget-aware context builder; prioritize recent + relevant; summarize old turns; never cut protocol groups.

### Slice 16: Multi-step planning
**Work:** Agent decomposes complex tasks into plans; shows plan to user; executes step-by-step with checkpoints; replans on failure.

### Slice 17: Parallel tool execution
**Work:** Independent tool calls execute concurrently; dependency graph for tool calls; configurable parallelism.

### Slice 18: Smarter file operations
**Work:** Fuzzy file finding; project-aware search (respect .gitignore); batch edits; preview diffs before apply.

### Slice 19: Code understanding
**Work:** AST-aware code reading (Python); symbol index per workspace; "find definition", "find references" tools.

### Slice 20: Error recovery intelligence
**Work:** On tool failure, agent analyzes error and retries intelligently (fix paths, try alternatives); learns from failures within session.

### Slice 21: Conversation memory
**Work:** Cross-session memory of user preferences; "you usually prefer X" suggestions; project-specific learnings persisted.

### Slice 22: Prompt optimization
**Work:** System prompt tuned for coding tasks; few-shot examples for tool use; provider-specific prompt adaptations.

---

## PHASE D — Performance (slices 23–28)

### Slice 23: LLM response caching
**Work:** Disk-based cache for identical prompts (per Operational_Refactoring P3); cache invalidation on context change; `mythic cache` management.

### Slice 24: Lazy loading
**Work:** Defer heavy imports (TUI, voice, DB) until needed; measure and document import times; `mythic --help` under 200ms.

### Slice 25: Streaming everywhere
**Work:** Stream all LLM output to TUI/terminal in real-time; progressive tool result display; cancellable streams.

### Slice 26: Startup optimization
**Work:** Profile startup; eliminate redundant config reads; parallelize init; target <1s cold start for `mythic run`.

### Slice 27: Memory efficiency
**Work:** Bound transcript memory; spill old turns to disk; measure peak RSS; target <200MB for typical sessions.

### Slice 28: Benchmark suite
**Work:** `mythic bench` command; measures turn latency, tool execution time, memory; regression tracking in CI.

---

## PHASE E — UX excellence (slices 29–34)

### Slice 29: Command palette
**Work:** Ctrl+K fuzzy command palette in TUI; searchable actions; keyboard-first navigation.

### Slice 30: Themes
**Work:** Multiple color themes (Tokyo Night, Viking Dark, Light); `mythic theme` command; custom theme support.

### Slice 31: Keyboard shortcuts
**Work:** Documented shortcut system; customizable bindings; vim/emacs input modes.

### Slice 32: Rich markdown rendering
**Work:** Syntax-highlighted code blocks; collapsible sections; clickable file links in TUI.

### Slice 33: Session dashboard
**Work:** TUI sidebar shows sessions, tasks, costs, model; quick-switch; session search.

### Slice 34: Onboarding
**Work:** First-run tutorial; interactive setup verification; `mythic tutorial` command; contextual help.

---

## PHASE F — Integrations (slices 35–40)

### Slice 35: More LLM providers
**Work:** Anthropic, Google, Mistral, Ollama, LM Studio adapters; unified provider interface; per-provider capability detection.

### Slice 36: GitHub deep integration
**Work:** PR creation with diffs; issue management; code review comments; Actions status; `mythic gh` enhancements.

### Slice 37: Webhooks and notifications
**Work:** Task completion webhooks; desktop notifications; configurable notification rules.

### Slice 38: Editor integrations
**Work:** VS Code extension (basic); Neovim plugin; `--editor` flag to open files.

### Slice 39: Shell completions
**Work:** Bash/zsh/fish completions for all commands and flags; auto-generated from CLI spec.

### Slice 40: Docker support
**Work:** Official Dockerfile; `mythic` in container with workspace mounting; documented container workflows.

---

## PHASE G — Memory & knowledge (slices 41–44)

### Slice 41: Project knowledge graphs
**Work:** Build symbol/dependency graph per workspace; "how does X work?" queries; architecture summaries.

### Slice 42: Long-term memory
**Work:** Cross-project learnings; user coding style inference; persistent preferences with privacy controls.

### Slice 43: Documentation generation
**Work:** `mythic docs` generates project documentation from code; keeps docs in sync; architecture diagrams.

### Slice 44: Code review mode
**Work:** `mythic review` analyzes changes; suggests improvements; checks against project conventions; severity levels.

---

## PHASE H — Safety & observability (slices 45–48)

### Slice 45: Execution sandboxing
**Work:** Optional sandboxed command execution (containers/restricted users); network isolation modes; resource limits.

### Slice 46: Audit logging
**Work:** Complete audit trail of all tool executions; tamper-evident logs; `mythic audit` viewer; export for compliance.

### Slice 47: Cost tracking
**Work:** Real token/cost tracking per session/project; budget alerts; `mythic costs` dashboard; cost attribution.

### Slice 48: Metrics and tracing
**Work:** OpenTelemetry integration; turn-level traces; performance dashboards; opt-in anonymous usage stats.

---

## PHASE I — Release (slices 49–50)

### Slice 49: 1.0 packaging
**Work:** Stable release process; changelog generation; version bumping; PyPI publishing workflow; signed releases.

### Slice 50: Documentation and launch
**Work:** Complete user guide; API reference; video tutorials (scripts); migration guide; 1.0 announcement; final quality gate (all 164+ tests green, CI green, docs complete).

---

## Slice tracking

| # | Slice | Status |
|---|-------|--------|
| 1 | S07 finish | ⬜ |
| 2 | S08 orchestration | ⬜ |
| 3 | S09 TUI polish | ⬜ |
| 4 | S10 repo workflows | ⬜ |
| 5 | S11 memory/context | ⬜ |
| 6 | S12 slice execution | ⬜ |
| 7 | S13 MCP/contracts | ⬜ |
| 8 | S14 release readiness | ⬜ |
| 9 | Test suite health | ⬜ |
| 10 | Crash recovery | ⬜ |
| 11 | Health checks | ⬜ |
| 12 | Structured logging | ⬜ |
| 13 | Graceful degradation | ⬜ |
| 14 | Input validation | ⬜ |
| 15–22 | Intelligence | ⬜ |
| 23–28 | Performance | ⬜ |
| 29–34 | UX | ⬜ |
| 35–40 | Integrations | ⬜ |
| 41–44 | Memory/knowledge | ⬜ |
| 45–48 | Safety/observability | ⬜ |
| 49–50 | Release | ⬜ |
