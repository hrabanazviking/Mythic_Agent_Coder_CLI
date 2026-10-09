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
