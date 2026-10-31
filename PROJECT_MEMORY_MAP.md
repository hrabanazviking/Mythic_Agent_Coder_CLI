# Project Memory Map — Mythic Agent Coder CLI

*The living map of this project, kept by the Scribe's discipline
(Mythic law: the map is updated in the same session as each banked
slice, never as a later chore). Seeded 2026-10-30 at the opening of
the All-Features campaign; before this date the repo carried its
memory in `docs/OWNERSHIP.md`, `docs/REPO_CENSUS.md`, the FORGE_RECEIPT
files, and the roadmap files themselves.*

## What this is

A local-first CLI AI coding agent (`mythic-agent`, Python ≥3.10,
AGPL per repo licence file — note `pyproject.toml` metadata says
Apache-2.0 while the repo carries an AGPL `LICENSE`/`LEGAL-NOTICE.md`;
the discrepancy is recorded here as found, not resolved). Textual TUI,
six named Mythic-Engineering offices (Skald, Architect, Forge Worker,
Auditor, Cartographer, Scribe), an MCP server (`mythic-mcp`), durable
workspace sessions, and a dual-layer memory.

## Where things live

- `mythic_agent/` — the package. Entry points: `mythic`
  (`mythic_agent.cli:main`), `mythic-mcp`
  (`mythic_agent.mcp_server:main`).
- `mythic_agent/agents/` — the agent loop: `llm.py`, `tools.py`,
  `planning.py`, `parallel.py`, `context.py`, `recovery.py`,
  `tasks.py`, `command_handler.py`, `prompts.py`.
- `mythic_agent/context/` — context engine (`budget.py`, …).
- `mythic_agent/core/feature_census.py` + `mythic_agent/data/feature_census.yaml`
  — the All-Features Feature Census (M-001): the living feature × rival
  matrix as validated data; every gap row names its owning M-slice.
- `mythic_agent/core/baseline_freeze.py` + `mythic_agent/data/baseline_freeze.yaml`
  — the Baseline Freeze (M-007): suite count + startup profile + the
  scripted end-to-end steps, frozen as validated data; the recording
  itself is `scripts/baseline_e2e.py` (loopback fake provider, steps
  E-01–E-04, re-run live by `tests/test_baseline_freeze.py`). Part XI
  compares against this freeze; a re-freeze is a new slice, never an
  edit.
- `mythic_agent/core/benchmark_tasks.py` + `mythic_agent/data/benchmark_tasks.yaml`
  — the Benchmark Task Pack v1 (M-008): 20 real tasks (4 each bugfix /
  feature / refactor / test-writing / docs), each a throwaway repo with
  seed files, a reference solution, hidden grading tests, and a diff
  rubric. Proven property (tests/test_benchmark_tasks.py): grading
  FAILS on every seed alone and PASSES on every seed+solution.
  `materialize(task, root, solved=...)` writes a repo ready for
  M-042's gate runs and M-255's harness.
- `mythic_agent/core/config_catalog.py` + `mythic_agent/data/config_catalog.yaml`
  — the Config Catalogue (M-009): every current setting (35: top-level,
  github.*, runtime.*, config-managed), every environment variable the
  package names (16), and every file the configuration system reads or
  writes (10), each with its source in the tree. It is the compatibility
  contract for Part VIII's settings redesign; tests cross-check it
  against the defaults files, CONFIG_SCHEMA, and a live env-var scan.
- `mythic_agent/core/session_catalog.py` + `mythic_agent/data/session_catalog.yaml`
  — the Session Catalogue (M-010): every session/journal format (7:
  SQLite session store, session record, session export, WAL journal,
  crash report, transcript spill, session-event payload), each with
  location, version, reader, fields, and compat rule. It is the
  forward-compat contract; tests/test_session_catalog.py freezes
  literal v1 golden artefacts (raw-SQL DB, raw-JSON journal lines,
  record, crash report, spill lines) that the real readers must
  always be able to read.
- `mythic_agent/core/dependency_census.py` + `mythic_agent/data/dependency_census.yaml`
  — the Dependency Census (M-012): every unique requirement declared
  in `pyproject.toml` (29: 7 core + all extras + the hatchling build
  backend), each with declaring groups, spec, licence, necessity,
  purpose, and installed weight measured in the baseline venv (the
  six the venv does not install are honestly `unmeasured`). Its
  stdlib-first replacement list claims only two real wins —
  scipy→stdlib `wave` (scipy's sole use is one wavfile write, yet it
  is the heaviest measured dependency at 109,315 KiB) and
  requests→the already-core httpx pair — and records the rest as
  no-real-win with reasons. Tests cross-check the census against the
  live pyproject (tomllib) and the dependency audit's import scan.
- `mythic_agent/core/platform_truth.py` + `mythic_agent/data/platform_truth.yaml`
  — the Platform Truth Table (M-013): Linux/Windows/macOS ×
  install/run/TUI/voice, 12 cells, each PROVEN or NOT PROVEN with no
  inheritance — the validator refuses PROVEN on anything but
  locally measured evidence. As recorded 2026-10-31: only Linux
  install/run/TUI are PROVEN (this VM, x86_64; TUI headless via the
  Textual pilot); voice is NOT PROVEN everywhere (Linux: PortAudio
  absent, measured; Windows/macOS: the hosted matrix never installs
  the voice extra), and Windows/macOS rest on historical hosted CI
  runs from October 2026 (earlier revisions) only, so they stay NOT
  PROVEN until re-earned on the current tree (M-259 re-proves).
  Tests cross-check the table against the live CI workflow and the
  hosted run ids in docs/development/PROGRESS.md.
- `mythic_agent/core/rival_config_study.py` + `mythic_agent/data/rival_config_study.yaml`
  — the Rivals' Config Import Study (M-014): what the config and
  instruction files of Claude Code, Codex CLI, OpenCode and Aider
  look like behaviourally, recorded clean-room from public
  documentation (formats and observable behaviour only) as the spec
  for Part X's rival importers (M-241). 4 rivals, 23 files (names,
  scopes, formats, roles), 24 key mappings — each landing on a real
  M-009 catalogue setting or honestly on `none` with the reason —
  6 findings, and per-rival importer directives that route every
  secret disguise (literal keys, env names, helper commands,
  load-time substitutions) to Kista. Tests cross-check the study
  against the live census rivals, the live config catalogue, and
  Mythic's own instruction filenames (CLAUDE.md and AGENTS.md are
  already discovered; Aider's read-list road is the outlier). The
  Gemini/Antigravity layouts M-241 also names are NOT studied here
  — the gap is recorded in the study itself.
- `mythic_agent/core/telemetry_review.py` + `mythic_agent/data/telemetry_review.yaml`
  — the Telemetry Honesty Review (M-015): what the app records
  today (10 items: metrics/traces, both cost ledgers, audit log,
  session store + WAL journal, crash reports, structured logs,
  response cache, long-term memory/preferences, transcript spill —
  every one local-file or in-memory, `leaves_machine: false`
  enforced by the validator), the only 6 outbound channels (provider
  calls — with OpenRouter's HTTP-Referer/X-Title identification
  disclosed — embeddings/knowledge search, Deepgram STT, TTS
  downloads/remote voices, the opt-in notification webhook, and
  gh-CLI GitHub operations; each user-initiated, user-configured, or
  a provider call), 5 honestly absent systems (analytics SDK, crash
  upload, update phone-home, background beacon, trackers), and 6
  honesty rules headed by the never-phones-home rule carried
  verbatim. Tests scan the package source for known telemetry
  libraries/endpoints and cross-check owner modules and cited
  destination strings against the live tree.
- `mythic_agent/providers/` — provider adapters + negotiation
  (structured output, vision, reasoning, streaming, usage, health,
  failover — the MIM-026–050 Pantheon work).
- `arcanum/arcanum.py` — the 118 KB arcanum, mapped by M-011 in
  `mythic_agent/core/arcanum_review.py` + `mythic_agent/data/arcanum_review.yaml`:
  16 banner sections, each with owns/duplicates and absorb/leave
  verdicts for Parts III/VI/VII — all leave; it is a standalone
  adjacent project (see ARCHITECTURE.md), and its two duplication
  risks (plaintext key custody, a provider-bypassing AI reading) are
  recorded as findings with Part II named as their absorbing road.
  M-011 also fixed three proven defects in the file: it did not
  compile (lost `return` + `def ai_reading` lines, restored
  byte-exact from the last compiling revision), the called-but-never-
  defined `render_celtic_cross_layout`, and the unwired
  `reversal_pct` setting.
- `tests/` — the pytest suite (testpaths = `tests` in
  `pyproject.toml`; per-test timeout 120 s by house habit). The loose
  `test_*.py` files at repo root are dev scratch, NOT the suite.
- `docs/` — interface docs, `OWNERSHIP.md`, `REPO_CENSUS.md`, gate
  receipts (`FORGE_RECEIPT_*.md`), and now
  `docs/CONCORDANCE_MIMISBRUNNR_FEATURE_ROADMAP.md`.
- `default_agent_characters/` — the castable agent characters.
- `completions/`, `editors/`, `scripts/`, `tasks/`, `media/` —
  supporting shelves.

## The two roads (both binding)

- **Mimisbrunnr (elder):**
  `MYTHIC_AGENT_CODER_CLI_500_SLICE_ULTIMATE_MIMISBRUNNR_ROADMAP.md`
  — 500 slices, 20 campaigns. Slices MIM-001–050 DONE (receipted,
  Oct 2026); 051–500 carved, unstarted.
- **All-Features (younger):** 272 slices, 11 parts (M-001–M-272),
  filed in-repo by Volmarr's push of 2026-10-30 (commit `d06c009` on
  `main`; campaign shelf copy in `~/workspace/your_files/mythic-coder/`).
- **The binding:** `docs/CONCORDANCE_MIMISBRUNNR_FEATURE_ROADMAP.md`.
  Citation discipline: elder slices are MIM-###, younger are M-###.

## Working facts & gotchas

- Default branch is `development` (origin/HEAD); `main` rides one
  commit ahead (the All-Features roadmap filing). Campaign work
  branches from `development`.
- CI is manual-dispatch only (workflow_dispatch), per Volmarr's
  standing ruling — the head commit of `development` is exactly that.
- The suite needs the optional extras installed to collect in full
  (textual, anthropic, tiktoken, mcp, psycopg, numpy/scipy,
  sounddevice…); without them ~26 test files fail collection with
  ModuleNotFoundError. `sounddevice` imports fail on machines without
  the PortAudio system library.
- House git laws bind all work here: fetch + remote-diff before any
  push, never force-push, verify the remote moved; README.md is never
  overwritten (guardian slice M-079 will make this machinery).
- No Docker, anywhere, for anything (Volmarr's law).
- Secrets live in Kista, never in plaintext config (younger road
  Law 4; machinery at M-032/M-244).

## Campaign state

The All-Features campaign's live state — baseline counts, per-slice
status, current head, next slice — is `CAMPAIGN_STATE.md` at repo
root. This map records only what endures; the state file records
what is moving.

*Seeded 2026-10-30. Amend in the same session as the work that
changes a fact here.*
