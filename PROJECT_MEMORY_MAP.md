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
- `mythic_agent/providers/` — provider adapters + negotiation
  (structured output, vision, reasoning, streaming, usage, health,
  failover — the MIM-026–050 Pantheon work).
- `arcanum/arcanum.py` — the 116 KB arcanum (M-011 owes its map).
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
