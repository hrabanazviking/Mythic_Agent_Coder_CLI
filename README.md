
![https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/media/venice-studio-fac0e110-eb29-4de6-9b3f-33ce69fe3309.png](https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/media/venice-studio-fac0e110-eb29-4de6-9b3f-33ce69fe3309.png)

---

# ⚔️ Mythic Agent CLI ⚔️

Welcome to **Mythic Agent**, an ultra-advanced, Viking-themed AI coding assistant right in your terminal. Designed with both intuition and rigorous architecture in mind, Mythic Agent is more than just a chatbot—it is a complete, multi-agent forge capable of managing entire repositories, running shell commands, coordinating sub-agents, and embracing the true spirit of the **Mythic Engineering** protocol.

---

## 🌟 Key Features

### 🛡️ The Viking TUI (Terminal User Interface)
Built on `Textual`, Mythic Agent features a gorgeous, fully interactive TUI styled with the **Tokyo Night** theme. Command your agent with a beautiful, heavy-bordered aesthetic, all from the comfort of your command line.

### 🧠 Mythic Engineering Mode
Enable the **Mythic Engineering Mode** directly from the sidebar to supercharge your AI. Following the MD Protocol, the agent switches to an **Architecture-First** mindset and delegates complex tasks to six highly specialized, built-in Sub-Agents:
1. **Skald** - The Visionary Poetess
2. **Architect** - The Dominant Designer
3. **Forge Worker** - The Fiery Builder
4. **Auditor** - The Merciless Verifier
5. **Cartographer** - The Sensual Wayfinder
6. **Scribe** - The Gentle Guardian of Memory

### 🐙 Seamless GitHub Integration
Forget switching contexts to authenticate or run raw git commands. 
- Easily configure your GitHub Repo and Personal Access Token (PAT) directly inside the TUI.
- Instantly use high-level slash commands:
  - `/commit <message>` - Automatically stages, commits, and pushes to remote.
  - `/issue <title>` - Instantly opens a GitHub issue.
  - `/pr <title>` - Instantly creates a Pull Request.
  - `/status` - Checks your local Git status.
  - `/gh <command>` - Runs raw GitHub CLI commands automatically authenticated via your saved PAT.

### 🛠️ Advanced Claude-Code Capabilities
Mythic Agent incorporates premium developer features:
- **Command Approvals:** Any destructive or terminal command the AI wishes to run requires your explicit approval via a modal.
- `/doctor` - Automatically catches terminal errors and fixes them.
- `/undo` - Restores the last unchanged agent file edit from its workspace journal.
- `/add <file>` - Explicitly pull specific files into the agent's context.

### 🌐 Multi-Provider Divine Sources
Mythic Agent supports multiple LLM endpoints out of the box. Easily configure:
- OpenRouter (for Claude 3.5 Sonnet, Llama 3, etc.)
- DeepSeek
- OpenAI
- OpenCode Go

### 🆕 Recent Features
- **`mythic doctor`** — System health checks (config, providers, tools, sessions, disk, dependencies) with `--json` for machines, `--fix` for safe auto-repairs, and `--live` for opt-in live provider checks.
- **Agent lifecycle & orchestration** — Typed task IDs with queued/running/completed/failed/cancelled states, delegation-cycle detection, cancellation propagation, and per-agent turn/tool budgets. Inspect via the MCP `mythic_task_status` / `mythic_task_cancel` tools.
- **`mythic cache`** — Inspect or clear the LLM response cache (`--stats`, `--clear`) so you never pay twice for identical requests.
- **`mythic costs`** — A model API cost ledger per workspace; unknown pricing is reported as unknown, never invented.
- **`mythic metrics`** — Recorded timers, counters, gauges, and traces for the workspace.
- **`mythic review`** — Static review of Python files with severity filtering and JSON output.
- **`mythic theme`** — List and apply color themes for the interface.
- **`mythic tutorial`** — Interactive first-run tutorial from any terminal.
- **Shell completions** — Ready-made completions for bash, zsh, and fish in `completions/`.
- **MCP server (`mythic-mcp`)** — External AI agents get the same workspace/policy/session/task services over stdio, with versioned tool contracts.
- **`mythic sessions --search`** — Filter workspace sessions by id, status, model, or metadata.

See the [User Guide](docs/USER_GUIDE.md) and [API reference](docs/API.md) for the full tour.

---

## 🧭 Current Development Status | 13 November 2026

> **Current source-and-history audit, not a stable-release certification.** This report is pinned to `main` at [`7e40feee`](../../commit/7e40feeec13c666eaeb2b45ec67b8bbd60429fcb), integrated **2026-11-13 12:22 UTC**. It cross-checks the recursive source tree, the 272-slice campaign, representative implementation and test modules, command wiring, local receipts, the November commit/PR history, hosted CI, package metadata and release information. The **6 November snapshot below remains as historical documentation** and is superseded by the newer counts here. This README audit did *not* execute a fresh complete test suite, a live-provider benchmark, a physical cross-platform gate or an independent security penetration test.

### 📊 Progress at a glance

| Measure | Verified repository snapshot |
| --- | --- |
| **All-Features campaign** | **260/272 slices banked (95.6%)**, **12 queued (4.4%)**, from [`mythic_agent/data/roadmap_slices.yaml`](mythic_agent/data/roadmap_slices.yaml). This is **180 additional done slices** since the previous 80/272 report. |
| **Parts complete in the campaign ledger** | **I–X: 10 of 11 parts**. Part IV Editor; V Autonomy & Safety; VI Crew; VII Memory & Context; VIII UX; IX Mythic Method; and X Bridges have all closed since the old snapshot. |
| **Active part** | **XI: The Proof Spine (M-255–272)**, with **6 of 18** banked. M-255–260 are recorded done; **M-261 Privacy audit** is next. |
| **Git integration** | Default branch remains `development`. [PR #10](../../pull/10) merged the feature-roadmap campaign to `development` on Nov 13; [PR #11](../../pull/11) then merged it to `main`. The earlier Nov 8 wave came through [PR #8](../../pull/8) and [PR #9](../../pull/9). |
| **Tree inventory** | **1,842 tracked blobs; 761 Python files; 351 Python test modules; 781 tracked files under `logs/`**, counted from the recursive `main` tree. These are inventory figures, not coverage percentages. |
| **Generated inventories** | [`docs/PUBLIC_API.md`](docs/PUBLIC_API.md) reports **13,378 AST-inventoried public names**; [`docs/OWNERSHIP.md`](docs/OWNERSHIP.md) maps **378 source modules** (both regenerated Nov 13). An inventory name is not necessarily an externally supported stable API. |
| **Version/license/release** | Package source is still **`0.1.0`** ([`__version__.py`](mythic_agent/__version__.py)); [`LICENSE`](LICENSE) and [`pyproject.toml`](pyproject.toml) identify **Apache-2.0**; **no published GitHub Release** was found. |
| **Latest committed local suite receipt** | The [M-260 closing entry](CAMPAIGN_STATE.md) cites [`logs/m260-fullsuite.log`](logs/m260-fullsuite.log): **12,826 passed / 6 failed / 1 skipped**. Its authors classify **five failures as closure-healed** and one as environment-specific. That is **not evidence of a fresh clean post-fix full-suite rerun**. |
| **Hosted CI** | Last listed [GitHub Actions run](../../actions/runs/39840813835): **22 Oct 2026, failed**. [`.github/workflows/ci.yml`](.github/workflows/ci.yml) is now **manual-dispatch only**, so subsequent merges do not have fresh hosted Linux/macOS/Windows × Python 3.10/3.13 coverage. |

### ⚒️ What has actually changed in the source

The **80 → 260** leap is accompanied by extensive new `mythic_agent/core/` implementation modules, tests, session-level registries, command-handler and terminal/TUI routes, Part acceptance gates, evidence journals and regenerated API/ownership inventories. All the feature groups below are **banked campaign implementations**. That phrase does **not** mean every external system or real-life use case has been exercised end-to-end.

#### Part IV — The Editor's Hand (M-081–094) closed

After M-071–080's edit formats, checkpoints, session branching, hunk review, guarded commits and file guardians, the second wave adds **conflict workbench, pull-request craft, issue-to-slice mapping, named multi-file change sets, first-class renames/moves, generated-code honesty, binary/large-file care, stash shelf, patch exchange, editor bridges, TUI diff theatre, blame/history inspection and guarded mass edits**. Representative code: [`conflict_workbench.py`](mythic_agent/core/conflict_workbench.py), [`pr_craft.py`](mythic_agent/core/pr_craft.py), [`change_sets.py`](mythic_agent/core/change_sets.py), [`rename_move.py`](mythic_agent/core/rename_move.py), [`patch_exchange.py`](mythic_agent/core/patch_exchange.py), [`mass_edit_guard.py`](mythic_agent/core/mass_edit_guard.py). The [M-094 Part IV gate](mythic_agent/core/part4_gate.py) records an editor exercise with scope-limited proof; it is not proof of every live git-host edge case.

#### Part V — Autonomy & Safety (M-095–120) closed in the ledger

The new architecture covers **permission profiles, scoped remembered approvals, OS sandbox plans, network gates, path jail, plan mode, full hook lifecycle/packs, background tasks, Keeper, scheduled work and fleet mode, cost/time/token budgets, kill switch, audit trail, secret hygiene, destructive-command ladder, rollback drills, multi-repo/remote work, offline grace, safety regression tests, red-team pack and policy as code**. See [`os_sandbox.py`](mythic_agent/core/os_sandbox.py), [`network_gates.py`](mythic_agent/core/network_gates.py), [`path_jail.py`](mythic_agent/core/path_jail.py), [`kill_switch.py`](mythic_agent/core/kill_switch.py), [`audit_trail.py`](mythic_agent/core/audit_trail.py), and [the Part V gate record](mythic_agent/data/part5_gate.yaml).

**Important confinement boundary:** `os_sandbox.py` distinguishes *pure construction of a platform-specific confinement plan* from executing commands through an enforcing launcher. Its own platform-truth notes do not claim universally proven OS confinement. The Part V gate explicitly describes a controlled, pure-road exercise **without a live model run or token spend**. A banked M-097/M-120 is not a guarantee of production-grade kernel isolation on Linux, macOS and Windows.

#### Part VI — The Crew (M-121–146) closed

The six Mythic Engineering offices are extended into a broader crew structure: **agents-as-files, custom offices, parallel worktrees, task dealing, crew communication, cycle/deadlock detection, merge discipline, heterogeneous agents, Auditor veto, research swarms, review panels, crew memory, stand-ups, scaling, character voices, external agents, replay, cost court, self-building workflows, solo mode, templates, graceful interruption and schedules**. Code anchors: [`crew_members.py`](mythic_agent/core/crew_members.py), [`worktrees.py`](mythic_agent/core/worktrees.py), [`task_dealing.py`](mythic_agent/core/task_dealing.py), [`auditor_veto.py`](mythic_agent/core/auditor_veto.py), [`stand_ups.py`](mythic_agent/core/stand_ups.py) and [the Part VI gate](mythic_agent/core/part6_gate.py). These contracts, records and tests are meaningful, but do not independently demonstrate a days-long unattended live crew campaign.

#### Part VII — Memory & Context (M-147–170) closed

New layers include **visible context budgets, `@`-mentions and instruction-file unification, Project Memory Map, glass-box compaction, code-graph retrieval, across-day sessions, cross-project memory, Self-Improving ledger, decision records, forgetting/quarantine, context recipes, pinning, token thrift, long-session durability, multi-session projects, handoff summaries, memory import/export, subconscious v2, contradiction watch, privacy-by-architecture and Memory Doctor**. See [`project_memory_map.py`](mythic_agent/core/project_memory_map.py), [`session_memory.py`](mythic_agent/core/session_memory.py), [`cross_project_memory.py`](mythic_agent/core/cross_project_memory.py), [`private_by_architecture.py`](mythic_agent/core/private_by_architecture.py) and [the Part VII gate](mythic_agent/core/part7_gate.py). The final **network-capture privacy audit remains queued as M-261**.

#### Part VIII — The Beautiful Face (M-171–200) closed

The Textual/terminal experience gains the **streaming work view, Slice Board, approval cards, fuzzy picker, slash-command palace, prompt craft, truthful status line, grown-up themes, voice interfaces, restrained notifications, plain-language presentation, onboarding/tutorial/help, keyboard/mouse flows, session gallery, cost face, final diff theatre, multi-pane layout, small-terminal support, copy/share, settings room, command palette, UI undo and accessibility verification**. Relevant locations: [`chat_screen.py`](mythic_agent/ui/screens/chat_screen.py), [`terminal.py`](mythic_agent/terminal.py), [`slice_board.py`](mythic_agent/core/slice_board.py), [`command_palette.py`](mythic_agent/core/command_palette.py), [Part VIII gate](mythic_agent/core/part8_gate.py). **M-262 final accessibility gate** and **M-266 clean-machine Stranger Fleet Test** are still to come.

#### Part IX — The Mythic Method Engine (M-201–232) closed

This is the major Mythic Engineering orchestration wave: **campaigns-as-data, intent capture, slicing engine, Juggernaut loop, per-slice acceptance gates, evidence banking, Keeper runtime, pause-lines, question/scope rules, memory-map upkeep, never-leave-a-bug discipline, retrospectives, pattern extraction, estimate honesty, multi-campaign hall, templates, the separate 500-slice road as a campaign, multi-day interrupts/resumes, milestone reports, plain-language build logs, guarded self-modification, failure taxonomy, dry-run campaigns, exports, standing orders, manual-dispatch CI convention, team-of-one scaling, teaching the method, method metrics and cross-app method**. See [`campaigns.py`](mythic_agent/core/campaigns.py), [`slicing_engine.py`](mythic_agent/core/slicing_engine.py), [`juggernaut_loop.py`](mythic_agent/core/juggernaut_loop.py), [`acceptance_gates.py`](mythic_agent/core/acceptance_gates.py), [`banking_discipline.py`](mythic_agent/core/banking_discipline.py) and [the Part IX gate](mythic_agent/core/part9_gate.py). Numerous modules are **validated record/state-machine and report layers**; banking such a layer does not prove autonomous live orchestration has already run without intervention.

#### Part X — Bridges (M-233–254) closed in the ledger

The tree now holds **MCP client and server v2, MCP registry, skill packs, custom commands, plugin bundles, VS Code and generic IDE protocols, rival configuration importers, Samverk and Samtal bridges, Kista key custody, Aesir model-routing deepening, GitHub/GitLab/Bitbucket parity models, CI and issue-tracker bridges, WYRD seam, webhook proposal gates, export-everything, docs-MCP pattern and a bridge-permissions audit**. Representative files: [`mcp_client.py`](mythic_agent/core/mcp_client.py), [`samverk_bridge.py`](mythic_agent/core/samverk_bridge.py), [`samtal_bridge.py`](mythic_agent/core/samtal_bridge.py), [`kista_keykeeper.py`](mythic_agent/core/kista_keykeeper.py), [`ci_bridges.py`](mythic_agent/core/ci_bridges.py), [`bridge_permissions.py`](mythic_agent/core/bridge_permissions.py).

**Read the gate's scope carefully:** [`part10_gate.yaml`](mythic_agent/data/part10_gate.yaml) calls its PASS a **pure-road/data-level exercise**. It explicitly states that the gate does **not** invoke a live host API, fetch an issue, raise a real PR, post to Samtal or read a Kista credential. Its proof is useful for structure and invariants; actual authorized multi-service workflows still need integration evidence.

#### Part XI — The Proof Spine (M-255–260) underway

| Slice | Source and operator surface now present | Still requires independent proof |
| --- | --- | --- |
| **M-255 — Benchmark harness** | [`benchmark_harness.py`](mythic_agent/core/benchmark_harness.py): run-kind registry, task/test/diff-rubric evidence records and reports; `/benchmarkharness` | Real repeatable autonomous task runs and scored artifacts |
| **M-256 — Published yardsticks** | [`published_yardstick.py`](mythic_agent/core/published_yardstick.py): license-aware SWE-bench-family run records with model, cost, date and scores; `/publishedyardstick` | Executed public benchmark runs; no leaderboard score can be inferred from a schema |
| **M-257 — Regression court** | [`regression_court.py`](mythic_agent/core/regression_court.py): Part I–XI gate-record battery and fail-closed decisions; `/regressioncourt` | A wholly green exact-commit full regression battery |
| **M-258 — Performance budgets** | [`performance_budgets.py`](mythic_agent/core/performance_budgets.py): 4 measures × VM/ARM/laptop = 12 evidence slots; `/performancebudgets` | Physical timing/memory results from all three named environments |
| **M-259 — Platform matrix final** | [`platform_matrix_final.py`](mythic_agent/core/platform_matrix_final.py): 12 Linux/Windows/macOS × install/run/TUI/voice cells with `PROVEN`/`NOT PROVEN` evidence rules; `/platformmatrixfinal` | Actual platform runs that make each cell provable |
| **M-260 — Security audit** | [`security_audit.py`](mythic_agent/core/security_audit.py): 12 doctrine/red-team audit areas, owner/disposition/evidence requirements; `/securityaudit` | A genuinely independent code-security audit with remediated or assigned findings |

**Command wiring checked:** the `/benchmarkharness`, `/publishedyardstick`, `/regressioncourt`, `/performancebudgets`, `/platformmatrixfinal` and `/securityaudit` routes are present in the [command handler](mythic_agent/agents/command_handler.py), [terminal](mythic_agent/terminal.py) and [TUI chat screen](mythic_agent/ui/screens/chat_screen.py). Tests for the newest pure books and agent/surface layers are committed. This confirms **source integration**, not that the interactive commands were freshly executed in this audit.

### 🧪 What the evidence proves, and the remaining blockers

1. **Extensive local regression receipts exist, but the newest recorded full run is not clean.** [M-260 closure](../../commit/72d65683e11123fd2334f44f1f3e7d4f1c678dfa) records **12,826 passed, 6 failed, 1 skipped** in **1,499.31 seconds**. Five failures are described as closure-healed and one environment-specific, **without a newer all-green full-suite rerun in that receipt**. The [Part X gate baseline](mythic_agent/data/part10_gate.yaml) is likewise **12,507 passed / 2 failed / 1 skipped**. Banked slices and green release validation are different states.
2. **Hosted CI is stale and failed on its most recent run (22 October).** The current workflow is **`workflow_dispatch` only**. Its six-job OS/Python matrix has **not** independently certified the November head. [`tests/test_session_identity.py`](tests/test_session_identity.py) still imports the POSIX-only `fcntl` module at top level, a concrete Windows collection problem requiring repair and a hosted rerun.
3. **Part gates prove bounded exercises and invariants, not universally live outcomes.** Several gate documents explicitly rely on deterministic throwaway examples, pure-domain roads and records rather than live models, services or physical devices. Their PASS labels should be preserved **with evidence-kind qualifications**, not promoted into claims of completed production deployment.
4. **Security and privacy require deployed-environment evidence.** Permission checks, data-layer sandbox plans, policy checks, audit records and red-team fixtures are present. They are no substitute for reviewing the actual launcher and confinement implementation, validating network denial/credential boundaries and conducting the queued captured-network privacy audit.
5. **Release and documentation reconciliation remains.** The package is `0.1.0` and there is no GitHub Release. [`ROADMAP.md`](ROADMAP.md), [`docs/development/PROGRESS.md`](docs/development/PROGRESS.md), release guidance and previous dated README notes need a current traceable update. The [All-Features narrative roadmap](docs/MYTHIC_CODER_FEATURE_ROADMAP_2026-10-30.md) calls the repo “AGPL” while the actual [license](LICENSE) and [packaging metadata](pyproject.toml) say **Apache-2.0**. Treat this as a **documentation contradiction**, not a license change.
6. **Logs and source should have deliberate artifact retention.** The tree includes **781 committed `logs/` items**. Historical receipts are valuable, but log file count or repository bulk is not a release gate and deserves a retention/size review.

### 🧭 Next twelve slices and the practical release gate

| Queue | Delivery and required evidence |
| --- | --- |
| **M-261 Privacy audit** | Real network capture during a fully permitted benchmark; verify no unapproved phone-home and preserve reproducible capture evidence. |
| **M-262 Accessibility final** | Timed keyboard-only TUI tasks and accessible terminal/platform validation on shipped surfaces. |
| **M-263–264 Docs / README care** | Reconcile user, architecture, method, bridge, security, license and release instructions to actual code, with additive history. **This independent README update does not auto-bank M-264.** |
| **M-265–266 Migration / Stranger Fleet** | Prove historical workspace sessions/journals/configs/memory migrate; then complete docs-only onboarding, headless CI and a crew campaign on a clean system. |
| **M-267–268 Cost / changelog truth** | Publish reproducible scores, costs, dates and model routes; label each release feature PROVEN, PARTIAL or NOT PROVEN. |
| **M-269–270 Release shaping / roadmap audit** | Align version/package/distribution; verify every slice's evidence, run final exact-SHA tests and platform matrix, publish an evidence index. |
| **M-271–272 Lessons / report to Volmarr** | Bank retrospective patterns into the Self-Improving ledger and produce a candid plain-language capability/evidence report. |

**Parallel must-fix work:** repair the Windows `fcntl` import and all repeatable platform failures; execute a **fresh full suite after the closure patches**; run the **six hosted CI jobs against the intended release SHA**; install wheels outside the checkout; exercise models, memory resumes, permission/sandbox enforcement, real crew task flow and permissioned Samverk/Samtal/Kista bridges end-to-end; audit privacy/security against real captures; and resolve the documentary Apache-2.0/AGPL conflict before release-facing publication.

### 🔎 Evidence index and scope

- **Current campaign truth:** [`mythic_agent/data/roadmap_slices.yaml`](mythic_agent/data/roadmap_slices.yaml); **banking narratives and local receipts:** [`CAMPAIGN_STATE.md`](CAMPAIGN_STATE.md) and [`TEAM_LOG.md`](TEAM_LOG.md).
- **Integration history:** [PR #10](../../pull/10), [PR #11](../../pull/11), [M-260 closure commit](../../commit/72d65683e11123fd2334f44f1f3e7d4f1c678dfa).
- **Acceptance scope:** [Part V gate](mythic_agent/data/part5_gate.yaml), [Part IX gate](mythic_agent/data/part9_gate.yaml), [Part X gate](mythic_agent/data/part10_gate.yaml); **inventory sources:** [Public API](docs/PUBLIC_API.md), [Ownership](docs/OWNERSHIP.md).
- **Validation boundaries:** [M-260 local log](logs/m260-fullsuite.log), [CI workflow](.github/workflows/ci.yml), [latest failed hosted run](../../actions/runs/39840813835), [Windows-sensitive test](tests/test_session_identity.py).

*Only this README addition is in scope. No source file, test, log, roadmap status, release version, license, existing README history or branch convention is changed. “Done” means the campaign has banked the slice; it does not replace separate live acceptance and release proof.*

---

## 🧭 Current Development Status | 6 November 2026

> **Active alpha, rapidly advancing, not yet a verified stable release.** This is a source-and-repository-evidence snapshot of the feature campaign through **M-080**, reviewed against the committed Python implementation, test inventory, recent commits/merges, roadmap data and hosted CI history. It is **not** a claim that a fresh end-to-end test suite, live provider test or cross-platform release gate was run on this exact revision.

### 📊 Progress at a glance

| Measure | Verified repository state |
| --- | --- |
| All-Features campaign | **80 / 272 slices marked done (29.4%)**; **192 queued** in [the machine-readable roadmap](mythic_agent/data/roadmap_slices.yaml) |
| Finished campaign parts | **I: Census & Charter (M-001–018), II: Provider Ocean (M-019–042), III: Code Intelligence (M-043–070)** |
| Active campaign part | **IV: The Editor's Hand (M-071–094)**, with M-071–080 marked done (**10 / 24**) |
| Next planned slice | **M-081: Conflict workbench**, followed by PR craft (M-082), issue-to-slice (M-083) and named multi-file change sets (M-084) |
| Separate elder roadmap | **MIM-001–050 of 500** receipted in the Mímisbrunnr programme; **MIM-051–500** remain unreceipted. These are *not* additive to the 80 M-slices; see the [concordance](docs/CONCORDANCE_MIMISBRUNNR_FEATURE_ROADMAP.md). |
| Package version | **0.1.0**, from [the version source](mythic_agent/__version__.py); alpha source project, **no GitHub release published** at this snapshot |
| Repository scale | **568 tracked files**, including **401 Python files** and **171 maintained Python test files**; [public API inventory](docs/PUBLIC_API.md) lists **2,620 public names** (inventory, *not* a stability guarantee) |
| Branch and integration status | Development occurs on the default `development` branch; the latest code was merged to `main` via [PR #7](../../pull/7) on **2026-11-06**. Code reviewed through `1e8237c` (`development`) and its subsequent `main` merge. |

### ⚒️ What the codebase has actually gained

**The working foundation.** The package has a real `mythic` entry point, optional Textual TUI, interactive terminal chat, machine-readable `mythic run`, workspace-scoped sessions, journaled file edits, user approval policies, cancellable execution, task/sub-agent tracking, an MCP server entry point, diagnostics, cost/metrics tools and optional memory/context capabilities. The [architecture](ARCHITECTURE.md), [CLI guide](docs/CLI.md), [user guide](docs/USER_GUIDE.md) and [development progress record](docs/development/PROGRESS.md) describe the contracts and their earlier evidence. The configurable six-agent Mythic Engineering cast is part of the existing product; making the complete Forge Protocol the universal autonomous operating loop remains later roadmap work.

**Provider expansion, M-019–042.** [The adapter registry](mythic_agent/providers/registry.py) now names **16 provider/endpoint adapters**, including OpenAI, Anthropic, Google, DeepSeek, OpenRouter, Ollama, LM Studio, llama.cpp, vLLM and Project Aesir. The work includes capability negotiation, structured output, tools, vision, reasoning, streaming, usage/cost accounting, retries, health and fallback mechanics. **Registered ≠ live-verified**: credentials, actual provider behavior, optional dependencies and hardware-specific compatibility still require individual proof.

**Code intelligence, M-043–070.** Tree-sitter foundations, repository maps, symbol graphs, structural search/rewrite, LSP diagnostics/navigation/rename, debugging through DAP, test feedback, code-sensing and specialised source views are represented by implementation modules and regression tests. [The Part III gate](mythic_agent/data/part3_gate.yaml) records a **PASS using controlled throwaway repositories and fake protocol-speaking LSP/DAP servers**. That proves the tested integration shapes; it does **not** establish that every real language server, debugger adapter or platform was exercised.

**The Editor's Hand, M-071–080.** The newest integrated feature wave is especially substantial:

| Slice | Implementation now present |
| --- | --- |
| **M-071** | Several strict edit formats: whole-file, unified-diff, search/replace and architect/editor planning |
| **M-072** | Hash-anchored file edits that reject stale or changed targets |
| **M-073** | Bounded repair packets with true current-text context after failed edits |
| **M-074** | Per-hunk accept/reject/edit review, followed by journaled application |
| **M-075** | Named working-tree and session checkpoints, branching checkpoint history and guarded restore |
| **M-076** | Fork, inspect and compare persistent session branches |
| **M-077** | Expanded undo timeline for edits, recorded command footprints and checkpoints, with certainty explicitly qualified |
| **M-078** | Opt-in auto-commit planning on a working branch, with protected-branch rules |
| **M-079** | README and licence file guardians in the edit journal, with an explicit-authorisation override |
| **M-080** | Diff-grounded commit splitting/message drafting plus safer push discipline, including remote checks and post-push verification |

The new implementation is visible in [`core/`](mythic_agent/core), with command paths in [the handler](mythic_agent/agents/command_handler.py), [terminal](mythic_agent/terminal.py) and [TUI](mythic_agent/ui/screens/chat_screen.py). Dedicated tests include `test_checkpoints.py`, `test_session_branching.py`, `test_undo_timeline.py`, `test_auto_commit.py`, `test_file_guardians.py` and `test_commit_craft.py`. The [current defaults](mythic_agent/data/config_defaults.yaml) enable checkpoints, branching, expanded undo, hunk review and commit craft, while **auto-commit remains off by default** and explicit guardian permission remains off by default.

### 🧪 Quality and release-readiness: evidence, not wishful thinking

- **Local campaign receipts:** [`CAMPAIGN_STATE.md`](CAMPAIGN_STATE.md) records M-075's whole-suite confirmation as **3,884 passed, 3 failed, 1 skipped** (3,888 collected). Its authors classified two failures as environment-specific and the third as a ledger-consistency failure addressed by the closing record. **That is a historical receipt, not a clean run on M-080.** Newer M-076–080 closure commits, tests and regenerated roadmap/API/ownership inventories are present, but the root campaign's detailed closure narrative has not yet been extended to M-080.
- **Hosted CI is not currently green or current.** The latest visible [Actions run, 22 October 2026](../../actions/runs/39840813835), failed across **all six** Linux/macOS/Windows × Python 3.10/3.13 jobs. Sample logged causes include coverage-report parsing, ownership-map assertions and Windows test collection failing because `tests/test_session_identity.py` imports POSIX-only `fcntl` unconditionally. That import is still in the reviewed source. The current [workflow](.github/workflows/ci.yml) uses **manual `workflow_dispatch` only**; recent November commits therefore do not prove a fresh hosted matrix.
- **Tests and generated inventories are extensive but distinct from release approval.** `tests/` contains 171 Python test modules, and [`PUBLIC_API.md`](docs/PUBLIC_API.md) plus [`OWNERSHIP.md`](docs/OWNERSHIP.md) were regenerated on 6 November. No complete suite, wheel-install matrix, real-provider matrix or physical cross-platform acceptance test was independently executed as part of *this README audit*.
- **Release documentation needs a reconciliation pass.** [`ROADMAP.md`](ROADMAP.md), [`docs/development/PROGRESS.md`](docs/development/PROGRESS.md) and [`docs/RELEASE_CHECKLIST.md`](docs/RELEASE_CHECKLIST.md) still carry older checkpoints/results. [The 272-slice roadmap's introduction](docs/MYTHIC_CODER_FEATURE_ROADMAP_2026-10-30.md) calls the repository “AGPL”, whereas the actual [`LICENSE`](LICENSE), [`pyproject.toml`](pyproject.toml) and this README currently identify **Apache-2.0**. This is a *documentation inconsistency*, not a licence change; resolve it deliberately without silently editing legal files.

### 🧱 What is next, and what is **not** finished

**Immediate engineering queue:** begin **M-081 conflict workbench**; then M-082–094 progressively finish the Git/PR, review, large-file, patch and editor experience, ending in the **Part IV acceptance gate**. For a release-quality baseline, also fix the Windows `fcntl` test portability issue, re-run the full suite, regenerate/verify the source inventories, run the six-platform/Python-version CI matrix on the **exact candidate commit**, and update the campaign ledger and release checklist with reproducible evidence.

**Later major parts remain queued:** Part V autonomy/permissions and **native OS sandboxing** (M-095–120); Part VI collaborative agent crews (M-121–146); Part VII memory/context (M-147–170); Part VIII UX (M-171–200); Part IX Mythic Engineering as the governing workflow (M-201–226); Part X extensions/integrations (M-227–252); and Part XI final reliability, security, privacy and release gates (M-253–272). The current shell denylist/timeouts and permission checks should **not** be mistaken for the future M-097 kernel/OS confinement boundary.

**How to read progress:** `done` in [the slice ledger](mythic_agent/data/roadmap_slices.yaml) means the campaign has banked that slice, **not** that the complete product is stable, every model has been tested live, every GitHub Actions job is green or all future roadmap gates are met. For detailed priorities and historical receipts, consult [the governing 272-slice roadmap](docs/MYTHIC_CODER_FEATURE_ROADMAP_2026-10-30.md), [the campaign state](CAMPAIGN_STATE.md), [the elder 500-slice roadmap](MYTHIC_AGENT_CODER_CLI_500_SLICE_ULTIMATE_MIMISBRUNNR_ROADMAP.md) and [the concordance](docs/CONCORDANCE_MIMISBRUNNR_FEATURE_ROADMAP.md).

*Audit scope: default-branch repository tree, package/test/module inventory, core implementations and entry-point wiring, YAML status, project documents, recent commit history, merged PRs, GitHub Actions runs and representative job logs. No source files, licence files, generated inventories or tests were changed for this status report.*

---


---

![https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/media/venice-studio-e04bc550-a7a5-4423-ab48-33d912f0a27a.png](https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/media/venice-studio-e04bc550-a7a5-4423-ab48-33d912f0a27a.png)

---

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/hrabanazviking/Mythic_Agent_Coder_CLI.git
   cd Mythic_Agent_Coder_CLI
   ```

2. **Install the CLI globally:**
   ```bash
    pip install -e '.[tui]'
   ```

3. **Summon the Agent:**
   ```bash
   mythic
   ```

### First-Time Configuration

Core-only installation uses `pip install -e .` and supports `mythic chat`,
`mythic run`, `mythic --help`, and `mythic --version` without UI or speech packages.
Use `mythic run --format json "your task"` for AI callers; it defaults to read-only.
See [the human/machine CLI guide](docs/CLI.md) for permissions, stdin, JSONL and
durable workspace sessions (`--resume`, `mythic sessions --export`), recovery and
exit codes. Optional integrations are
installed with the `mcp`, `knowledge`, `voice`, and `voice-cloning` extras.
Human TUI/terminal and machine callers share tool permissions. Ctrl+C in terminal
or `/stop` in TUI cancels active owned requests, approvals and commands; command
results include exit status and captured output. Direct/machine effects require
an explicit policy; delegated agents inherit the caller's mode.
See [the development roadmap](ROADMAP.md) for active reliability work and
[the developer guide](docs/DEVELOPMENT.md) for test/build commands. This is an
alpha; roadmap features are only available once their implementation is recorded.

When you run `mythic` for the first time, press **`F2`** to open the **Setup Wizard**.
Here, you can:
- Select your Provider and enter your API Key.
- Fetch and select the desired AI Model.
- Edit the primary System Prompt (By default: A super smart, pretty, modern Viking female coder).
- Add Global Rules that apply to all sub-agents.
- Summon custom Warriors (Sub-Agents) or use the default Mythic Engineering team.

---

![https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/media/venice-studio-0210d1c9-7baf-43e4-9e85-507ef55b57f1.png](https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/media/venice-studio-0210d1c9-7baf-43e4-9e85-507ef55b57f1.png)

---

## 📜 How to Use

Simply launch `mythic` in your project's directory and type naturally! You can ask the agent to:
- `"Read my src/main.py and find the bug."`
- `"Create a new React component for a login screen."`
- `"Run the tests and fix any failing ones."`

### Runic Commands (Slash Commands)
You can type these at any time in the chat input:
- `/help` - View all available commands.
- `/setup` (or `F2`) - Open the Setup Wizard.
- `/clear` - Clear the current conversation history.
- `/add <file>` - Add a specific file to the context.
- `/commit <msg>` - Auto-commit and push changes to GitHub.
- `/issue <title>` - Create a GitHub issue.
- `/pr <title>` - Create a GitHub Pull Request.
- `/status` - Check Git status.
- `/gh <cmd>` - Run native GitHub CLI commands.
- `/test` - Run your project's test suite natively.
- `/undo` - Roll back the last agent file edit.
- `/doctor` - Auto-fix a command output.
- `/quit` - Leave Valhalla (Exit the app).

---

![https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/media/venice-studio-9839cf70-13ab-4cc0-aeda-a80e54537ad5.png](https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/media/venice-studio-9839cf70-13ab-4cc0-aeda-a80e54537ad5.png)

---

![https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/media/venice-studio-c37f94ae-d9a4-4be7-970c-254e49cf39b3.png](https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/media/venice-studio-c37f94ae-d9a4-4be7-970c-254e49cf39b3.png)

---

![https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/media/venice-studio-9fc2a590-2a63-430a-90de-ed5a3dbf07d5.png](https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/media/venice-studio-9fc2a590-2a63-430a-90de-ed5a3dbf07d5.png)

---

![https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/media/venice-studio-ee72688e-d3cd-44fd-bbdd-6a7b6b6013ec.png](https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/media/venice-studio-ee72688e-d3cd-44fd-bbdd-6a7b6b6013ec.png)

---

![https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/media/venice-studio-9969954d-00e4-4fd5-a447-a9aad1ad8a62.png](https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/media/venice-studio-9969954d-00e4-4fd5-a447-a9aad1ad8a62.png)

---

![https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/Viking_Apache_V2_1.jpg](https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/Viking_Apache_V2_1.jpg)

---

## ⚖️ License

Copyright (c) 2026 Volmarr Wyrd

Mythic Agent Coder CLI is licensed under the **Apache License, Version 2.0**. See the [LICENSE](LICENSE) file for the full license text and [NOTICE](NOTICE) for the project attribution.

For third-party material adapted into this codebase, see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Per the Apache-2.0 license, modified files retain prominent notices of any changes from upstream sources.

Unless required by applicable law or agreed to in writing, this project is distributed on an "AS IS" BASIS, without warranties or conditions of any kind, either express or implied.

---

## Distribution and Privacy Position

Mythic Agent Coder CLI is published here as source code and project material.

The author does not require users to provide age, identity, government ID, biometric data, or similar personal information in order to access or use the source code in this repository.

The author may decline to provide official binaries, installers, hosted services, app-store releases, or other official distribution channels where doing so would require age verification, identity verification, or similar personal-data collection.

Any third party who forks, packages, redistributes, deploys, hosts, or otherwise makes this software available does so independently and is solely responsible for compliance with applicable law, platform policy, and distribution requirements in their own jurisdiction and context.

See [LEGAL-NOTICE.md](LEGAL-NOTICE.md) for details.

---

## ☕ Support the Project

If you enjoy my open-source projects and want to help support continued development, research, testing, and experimentation, you can leave a tip through PayPal:

**[Support my work on PayPal.Me](https://www.paypal.com/paypalme/volmarrwyrd)**

Support is always appreciated, but never required. Using, sharing, testing, contributing to, or starring the projects helps too. 🖤⚙️ᚱ

---

![https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/image-23-RuneForgeAI.jpg](https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/image-23-RuneForgeAI.jpg)

---

![https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/IMG_0407.jpeg](https://raw.githubusercontent.com/hrabanazviking/Mythic_Agent_Coder_CLI/refs/heads/development/IMG_0407.jpeg)

---
