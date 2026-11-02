# Mythic Agent Coder — The All-Features Roadmap

*Take every feature the world's CLI coding apps have — Claude Code, Codex
CLI, Gemini/Antigravity CLI, OpenCode, Aider, Copilot CLI, Goose, Cline,
Cursor CLI and their kin — and forge them into Mythic Agent Coder in their
best, kindest-to-use form, until it is the most powerful coding CLI of
them all. And its way of working is not theirs: it codes by Mythic
Engineering.*

Commissioned by Volmarr, 2026-10-30. Governing repo:
`hrabanazviking/Mythic_Agent_Coder_CLI` (default branch `development`,
AGPL). Companion to Volmarr's own 500-slice Mimisbrunnr roadmap already in
that repo — Part I opens with the concordance between the two roads, so
nothing he carved is lost or silently replaced.

---

## 1. What stands today (measured, 2026-10-30)

Mythic Agent Coder is already a real, working forge, built out in October
2026 (50 slices, full suite green in its day, dogfooded on itself):

- **Textual TUI** (Tokyo Night), chat/setup/splash screens, themes,
  subagent editor, splash + interactive tutorial.
- **Mythic Engineering Mode** with six named sub-agents — Skald,
  Architect, Forge Worker, Auditor, Cartographer, Scribe — plus castable
  agent characters.
- **Tools & safety**: shell/file tools with approval modals, policy
  modes, `/undo` from a workspace journal, crash-recovery journal,
  `mythic doctor` (with `--fix`, `--json`, `--live`).
- **GitHub in the TUI**: `/commit`, `/issue`, `/pr`, `/status`, `/gh`.
- **Providers**: OpenRouter, DeepSeek, OpenAI, OpenCode Go — four doors.
- **Machine face**: `mythic run --format json` (read-only by default),
  durable workspace sessions (`--resume`, export, search), JSONL,
  exit-code discipline.
- **MCP server** (`mythic-mcp`) exposing workspace/policy/session/task
  services with versioned contracts; typed task lifecycle with budgets,
  cancellation, delegation-cycle detection.
- **Memory**: dual-layer vector RAG subconscious + core memory;
  auto-compacting context engine; response cache (`mythic cache`);
  cost ledger (`mythic costs`, unknown prices reported as unknown);
  metrics; static `mythic review`; voice/TTS extras; shell completions.

## 2. The field in 2026 (the census this roadmap answers)

The serious CLI coding agents — Claude Code, Codex CLI, Gemini CLI (now
Antigravity), OpenCode, Aider, Copilot CLI, Goose, Cline, Amp, Pi, Omp —
have converged on a feature canon, with a few frontier edges:

- **Universal canon**: agentic read/edit/run loop; plan mode; permission
  prompts with modes; project instruction files (AGENTS.md and kin);
  slash commands; subagents; MCP (client *and* server); hooks; skills/
  plugins; checkpoints/undo; session resume and search; context
  compaction; streaming TUI with diffs; git auto-commit and PR flows;
  headless/CI scripting; cost and usage reporting; image input; web
  search/fetch; custom commands; model switching; sandboxing.
- **Frontier edges** (held by one or two, claimed by few): 75+ provider
  registries and local models (OpenCode); OS-level kernel sandbox
  (Codex); a token-ranked **repo map** of the whole codebase (Aider);
  LSP integration — diagnostics, references, rename (OpenCode, Omp);
  AST-aware and hash-anchored edits, ast-grep structural rewrite
  (Omp, Aider's edit formats); a real debugger over DAP (Omp);
  formatter/linter feedback loops; agent *teams* with parallel
  worktrees (Claude Code); 1M-token contexts; background tasks;
  voice input; IDE bridges.

Mythic Agent holds much of the canon already. Its gaps are named plainly:
four providers where the field has seventy-five; no repo map; no LSP,
no AST edits, no debugger; checkpoints thinner than the field's; no
hooks; no MCP *client*; no OS sandbox; no agent-team worktrees; and —
its birthright advantage still only half-built — the Mythic Engineering
method exists as a *mode*, not yet as the app's whole way of working.

## 3. The laws of this road

1. **Mythic Engineering is the method, not a mode.** The default loop of
   the whole app is the Forge Protocol: the human speaks plain intent
   (what, why, what success is); the coder builds the plan, the slices,
   the memory map; builds → tests → repairs → continues on its own
   inside the project; pauses only at the standing lines (destruction,
   irreversible infrastructure, cost, public publishing, sending as the
   user, secrets, weakened security). Part IX makes this machinery
   first-class.
2. **Every feature in its kindest form.** Parity is the floor, not the
   ceiling: where the field's form is clumsy (permission fatigue, opaque
   compaction, cryptic config), Mythic's form is the one a tired human
   at midnight would choose. Plain language first, always — the user
   should never need to learn jargon to command the forge.
3. **Local sovereignty.** Any model, any provider, local first-class
   (Ollama, LM Studio, and Volmarr's own Project Aesir as a provider).
   No feature may require one vendor's account. No Docker anywhere.
4. **Secrets live in Kista.** API keys and tokens are kept by Volmarr's
   own credential keeper, never in plaintext config files.
5. **Honesty machinery stays**: unknown prices are unknown, failed
   checks are failed, NOT PROVEN is a first-class result. The Auditor's
   office is never decorative.
6. **Nothing already shipped is removed.** Legacy commands, sessions,
   and configs keep working; every addition is additive or a superset.
7. **Design law applies to the TUI**: the Cyber-Viking Visual Design
   Lawbook — theme serves the task, coherent without colour, no
   ornament that costs comprehension.

## 4. Shape of the whole

Eleven parts, **272 slices**.

| Part | Name | Slices |
|---|---|---|
| I | The Census & The Charter | M-001 – M-018 |
| II | The Provider Ocean — every model, every door | M-019 – M-042 |
| III | Code Intelligence — repo map, LSP, AST, debugger | M-043 – M-070 |
| IV | The Editor's Hand — edits, checkpoints, git craft | M-071 – M-094 |
| V | Autonomy & Safety — sandbox, permissions, hooks, headless | M-095 – M-120 |
| VI | The Crew — subagents and agent teams v2 | M-121 – M-146 |
| VII | Memory & Context — the deep mind | M-147 – M-170 |
| VIII | The Beautiful Face — the kindest TUI in the field | M-171 – M-200 |
| IX | The Mythic Method Engine — Mythic Engineering as the OS | M-201 – M-232 |
| X | Bridges — MCP both ways, IDEs, Samtal, Samverk, Kista | M-233 – M-254 |
| XI | The Proof Spine — evals, platforms, release | M-255 – M-272 |

---

## Part I — The Census & The Charter (M-001 – M-018)

*Goal: know exactly where Mythic stands against the whole field, feature
by feature, and bind this road to Volmarr's own 500-slice road — before a
single new line is written.*

- **M-001** The Feature Census: a living matrix (feature × tool × their
  form × Mythic's state: HAVE / PARTIAL / MISSING / BETTER) covering the
  ten named rivals, refreshed from their public docs; stored as data.
- **M-002** The Concordance: every campaign of Volmarr's 500-slice
  Mimisbrunnr roadmap mapped onto this road's parts (and vice versa) —
  one page where both roads can be read together; conflicts listed, none
  silently resolved.
- **M-003** The Gap Audit: each MISSING/PARTIAL census row traced to the
  module that would own its fix; the audit output seeds Parts II–X.
- **M-004** UX Principles charter: the kindness rules (plain language
  first; one-tap approvals with remembered scopes; nothing destructive
  without a named target; every refusal explains itself; every long job
  shows its slices) written as reviewable law for all later parts.
- **M-005** The Method Charter in-app: Forge Protocol, Plain-Language
  Build Protocol, Project Memory Map, Juggernaut loop, Autonomy lines,
  and the Self-Improving Forge summarised into the app's own doctrine
  file — the text Part IX's engine executes.
- **M-006** Terminology bridge: every field term (checkpoint, hook,
  skill, plan mode…) given its Mythic name *and* kept searchable by its
  common name — a user coming from any rival finds their word honoured.
- **M-007** Baseline freeze: full suite + startup profile + a scripted
  end-to-end task recorded as the "before" evidence for Part XI.
- **M-008** Benchmark task pack v1: twenty real tasks (bugfix, feature,
  refactor, test-writing, docs) in throwaway repos — the yardstick every
  later part is measured with.
- **M-009** Config archaeology: every current setting, file, and env var
  catalogued; the catalogue is the compatibility contract for Part VIII's
  settings redesign.
- **M-010** Session archaeology: existing session/journal formats proven
  readable by a forward-compat test that must never break.
- **M-011** The arcanum review: the 116 KB `arcanum.py` mapped — what it
  owns, what it duplicates, what Parts III/VI/VII should absorb or leave.
- **M-012** Dependency census: every dependency weighed (weight, licence,
  necessity); a stdlib-first replacement list where the win is real.
- **M-013** Platform truth table: Linux/Windows/macOS × install/run/TUI/
  voice — each cell PROVEN or NOT PROVEN as of today, no inheritance.
- **M-014** The rivals' config import study: what Claude Code / Codex /
  OpenCode / Aider config and instruction files look like, behaviourally
  — the spec for Part X's importers (clean-room, formats only).
- **M-015** Telemetry honesty review: what the app records today
  (metrics, costs) and the rule that it never phones home — written down.
- **M-016** Accessibility baseline: keyboard-only task completion test,
  screen-reader pass over the TUI, contrast audit — the "before" for
  Part VIII.
- **M-017** The roadmap made data: this road's slices in a machine file
  the app itself can display, check off, and report (Part IX eats first
  from its own kitchen).
- **M-018** Part I gate: census + concordance + audits published in-repo;
  baseline evidence banked; Volmarr's 500-slice file untouched.

## Part II — The Provider Ocean (M-019 – M-042)

*Goal: any model through any door — the field's widest registries hold
75+ providers; Mythic's registry is data-driven so the seventy-sixth is a
file, not a code change — and the home fires (Ollama, Aesir) are first
citizens, not afterthoughts.*

- **M-019** Provider registry as data: provider definitions (endpoints,
  auth style, model lists, capabilities) in data files; adding a
  provider never touches Python.
- **M-020** The OpenAI-compatible universal adapter: one adapter serving
  every compatible endpoint (the long tail of the field) with per-provider
  quirks declared in its registry entry.
- **M-021** Anthropic-native adapter v2: prompt caching, extended
  thinking controls, and tool-use dialect handled natively, not through
  the compatible shim.
- **M-022** Google/Gemini-native adapter: native dialect, long-context
  handling, grounding toggles where offered.
- **M-023** Local runtimes I — Ollama: discovery of running models,
  pull/list from the TUI, honest "model not present" answers.
- **M-024** Local runtimes II — LM Studio, llama.cpp servers, and any
  local OpenAI-compatible port, with the same discovery kindness.
- **M-025** **Project Aesir as a provider**: Mythic can aim at Volmarr's
  own engine (its API as it stands) — the ecosystem eats its own cooking;
  capability limits reported as Aesir reports them.
- **M-026** The gateways: OpenRouter and kin as first-class registry
  entries with their model catalogues browsable in-app.
- **M-027** Capability truth per model: context size, tool use, vision,
  reasoning, max output — stored per model, shown before selection,
  never guessed (unknown = unknown).
- **M-028** Mid-session model switching: change model or provider without
  losing the session, the plan, or the crew; the switch is a journal
  event with the reason if given.
- **M-029** Role routing: different models for different offices (a deep
  thinker for the Architect, a fast hand for grunt edits, a cheap scout
  for searches) — set per crew role, visible, changeable.
- **M-030** Fallback chains: when a provider fails or rate-limits, the
  chain walks to the next door with the user's standing permission;
  every walk is announced, never silent.
- **M-031** Cost-aware routing: with `mythic costs` data, the router can
  prefer the cheaper adequate model for a task class — a setting, off
  by default, explained in plain words.
- **M-032** Key custody via Kista: providers read their keys from
  Volmarr's Kista; config files hold references, never secrets; a
  missing key asks once, kindly.
- **M-033** Subscription doors study: OAuth-style sign-ins some rivals
  use (ChatGPT/Claude subscriptions) — studied behaviourally; built only
  where the provider's terms allow, else recorded NOT OFFERED with the
  reason.
- **M-034** Streaming discipline: token streaming with clean interrupt,
  partial-answer salvage, and resume-the-thought where the provider
  allows; a killed stream never corrupts the journal.
- **M-035** Retry and backoff honesty: bounded retries on transient
  failures only; mutating calls never silently replayed (the house rule
  from Sagnaskemma's hardening, applied here).
- **M-036** Rate-limit weather: per-provider quota/limit state surfaced
  in the status line *before* it bites; queueing of crew work around it.
- **M-037** Vision input routing: image tasks route only to models whose
  capability record says they can see; otherwise the app says so plainly
  and offers the switch.
- **M-038** Long-context strategy per model: 1M-class contexts get
  map-first loading; small contexts get aggressive repo-map + retrieval
  (Part III/VII) — the strategy is chosen from capability truth.
- **M-039** Provider health board: `mythic doctor --live` grown into a
  per-provider board (reachable, latency, last error) with --json.
- **M-040** Offline honesty: with no network and no local model, the app
  says exactly that and still offers its non-model tools (review,
  metrics, session search) instead of dying.
- **M-041** New-provider test kit: a conformance script any new registry
  entry must pass (chat, tools, streaming, errors) before it ships.
- **M-042** Part II gate: the same benchmark task (M-008) completed
  through five different providers + Ollama + Aesir, evidence banked.

## Part III — Code Intelligence (M-043 – M-070)

*Goal: the coder must **understand** code, not just grep it. This part
builds the field's frontier — repo map, language intelligence, structural
editing knowledge, and a debugger — into Mythic's hands.*

- **M-043** Tree-sitter foundation: grammar-backed parsing for the major
  languages (Python first, then JS/TS, Rust, Go, Mojo-aware), vendored
  cleanly with licences noticed.
- **M-044** The Repo Map (Aider's crown, made kinder): a token-budgeted
  map of the whole repo — files, classes, functions, signatures —
  ranked by relevance to the current task (PageRank over the reference
  graph, as the field does), refreshed incrementally.
- **M-045** Map in the TUI: the map is *visible* — browse it, pin files,
  see why the coder thinks a file matters; the ranking is explainable.
- **M-046** Symbol graph: definitions, references, imports, call edges
  extracted per language; the graph feeds the map, the search, and
  Part VI's task splitting.
- **M-047** Structural search: ast-grep-style pattern search ("find every
  call like `foo($A, $$$)`) as a tool and a TUI panel.
- **M-048** Structural rewrite: the same patterns as safe codemods with
  per-site diff preview — never a blind global replace.
- **M-049** LSP client I — diagnostics: language servers (pyright,
  typescript, rust-analyzer, gopls…) run beside the app; their
  diagnostics flow into the coder's awareness and the TUI's margin.
- **M-050** LSP client II — navigation: go-to-definition, references,
  hover, workspace symbols as agent tools ("where is this used?" gets a
  true answer).
- **M-051** LSP client III — rename and code actions: a rename propagates
  through re-exports and imports by the server's own knowledge, diffed
  for approval like any edit.
- **M-052** Edit-time truth loop: after every edit, diagnostics + the
  project's formatter/linter run; new errors return to the coder as
  facts to fix *before* the turn ends (the field's quiet superpower).
- **M-053** Formatter covenant: the project’s own formatter config is
  honoured exactly; the coder never reformats untouched code; format
  diffs are separated from logic diffs in review.
- **M-054** The Debugger (DAP): breakpoints, step, continue, variable
  inspection, exception stops for Python first (debugpy), then the
  DAP-general road — the coder can *watch* a bug happen.
- **M-055** Debugger in the loop: a failing test can be re-run under the
  debugger by the coder itself, frames and locals reported as evidence.
- **M-056** Test intelligence: test discovery per project, "run only what
  this change touches" selection from the symbol graph, flaky-test
  marking from history (never from vibes).
- **M-057** Coverage sight: line coverage overlaid on edited files; a
  change landing with zero covering tests is flagged to the Auditor.
- **M-058** Beyond-grep local search: in-process ripgrep with fuzzy and
  structural modes, results ranked by the symbol graph.
- **M-059** Web knowledge tools: web search + fetch as first-class tools
  (docs, changelogs, error lookup), results cited into the journal.
- **M-060** Docs-at-hand: the project's own docs, plus offline doc packs
  for its stack, searchable from the TUI (the Mojo Docs MCP pattern,
  generalised).
- **M-061** Dependency sight: read the dependency graph, changelogs, and
  known-vulnerability data for the project's stack; an upgrade is
  proposed with its blast radius, never applied silently.
- **M-062** Dead-code and duplication sensing: structural reports for the
  Cartographer; sensing only — deletion is always a separate, approved
  slice.
- **M-063** Type-aware Python depth: mypy/pyright findings triaged into
  the review; the coder fixes types it broke in the same turn.
- **M-064** Mojo as a first-class language: parsing via tree-sitter
  grammar where available, the house Mojo skills wired as knowledge —
  Mythic is the only CLI that truly speaks Mojo (Aesir's home tongue).
- **M-065** SQL and data sight: schema reading, query explain, migration
  files understood as code (the Muse DB pattern, productised).
- **M-066** Config and infra files: YAML/TOML/Dockerfile/systemd units
  parsed structurally, with the no-Docker law enforced as a *warning
  the coder itself raises* on Volmarr's projects.
- **M-067** Binary and asset awareness: images, archives, and large files
  are described, never dumped into context; the map notes their roles.
- **M-068** Language packs as data: per-language toolchains (server
  commands, formatters, test runners) declared in data; a new language
  is a pack, not a patch.
- **M-069** Intelligence cache: parse/graph/LSP results cached per file
  hash; a cold start on a big repo stays fast (measured in Part XI).
- **M-070** Part III gate: on the benchmark pack — a cross-file rename, a
  structural codemod, and a debugger-caught bug, all completed with the
  new senses, evidence banked against the M-007 baseline.

---

## Part IV — The Editor's Hand (M-071 – M-094)

*Goal: edits a surgeon would sign. Every edit format the field trusts,
checkpoints worthy of the name, and git craft at Aider's level and
beyond.*

- **M-071** Edit-format plurality: whole-file, unified-diff, search-and-
  replace blocks, and Aider-style architect/editor splitting — the coder
  picks per task and per model strength; the choice is journaled.
- **M-072** Hash-anchored edits: edits anchored to content hashes of the
  lines they touch (the frontier trick that cuts failed applies and
  token cost); a moved target refuses cleanly instead of mangling.
- **M-073** Apply-failure repair loop: a failed apply returns the true
  current text to the coder for one honest retry — bounded, visible,
  never a silent fuzz.
- **M-074** Hunk-level review: the approval UI shows diffs per hunk with
  accept/reject/edit per hunk; rejecting one hunk never kills the rest.
- **M-075** Checkpoints v2: named checkpoints ("before the auth rework")
  capturing working tree + session state; restore is one command, and
  the journal shows the whole checkpoint tree.
- **M-076** Session branching: fork a session at any message ("try the
  other road from here") — branches share history, diverge honestly,
  and can be compared.
- **M-077** Undo grown up: `/undo` walks edits, commands, and checkpoints
  as one timeline; undo of a *command's* effects is attempted via its
  recorded footprint, labelled certain or best-effort.
- **M-078** Auto-commit discipline (Aider's crown): every accepted edit
  set lands as its own commit with a written message — on a working
  branch by default, never on the user's protected branches unasked.
- **M-079** README and licence guardians: the coder *refuses* to
  overwrite a README (Volmarr's standing law) or touch licence files
  without explicit word; the refusal is built into the edit layer.
- **M-080** Commit craft: commit-splitting by concern, message drafting
  from the actual diff, and the house rules wired in (fetch + remote-diff
  before push, never force-push, verify the remote moved).
- **M-081** Conflict workbench: merge/rebase conflicts presented as
  decisions with both sides' intent summarised; resolution is edited,
  tested, and journaled like any change.
- **M-082** PR craft: create, review, and respond to pull requests —
  review comments fetched as tasks; a review pass posts only at the
  user's word (sending as the user is a standing pause-line).
- **M-083** Issue-to-slice: a GitHub issue (or Samverk issue, Part X)
  becomes a planned slice with acceptance checks drafted from its text.
- **M-084** Multi-file change sets: a change set is a named, reviewable
  unit across files with its test evidence attached.
- **M-085** Rename/move files as first-class edits (history-preserving
  git mv, references updated via Part III's graph).
- **M-086** Generated-code honesty: generated files are marked, their
  generator recorded; hand-edits to generated files warn before saving.
- **M-087** Large-file and binary care: big files edited by anchored
  chunks; binaries never text-edited; size guards explain themselves.
- **M-088** The stash shelf: quick-shelve work-in-progress by name,
  restore across sessions; the shelf survives crashes (journal-backed).
- **M-089** Patch export/import: a change set as a portable patch file
  with its evidence header — the hand-off format betweenmachines and
  between agents.
- **M-090** Editor bridges lite: `$EDITOR` round-trip for any file or
  prompt at any approval point (the terminal user's oldest right).
- **M-091** Diff theatre in the TUI: side-by-side and unified views,
  word-level highlighting, whitespace toggle — colour never the only
  signal.
- **M-092** Blame and history sight: "why is this line like this?" —
  blame + the journal's own record of the session that wrote it.
- **M-093** Guarded mass edits: repo-wide edits require a dry-run report
  (files, hunks, risks) approved before a single byte moves.
- **M-094** Part IV gate: benchmark refactor task completed with zero
  failed applies, hunk review used, auto-commits clean, checkpoint
  restore proven mid-task.

## Part V — Autonomy & Safety (M-095 – M-120)

*Goal: power with a steady hand. The field's safety canon — sandboxes,
permission modes, hooks — rebuilt so a human can let the forge run all
night and trust what they wake to.*

- **M-095** Permission profiles: named postures (Read-Only Scout,
  Trusted Forge, Full Autonomy, and custom) binding tools, paths,
  network, and commands; the posture is always visible in the status
  line.
- **M-096** Remembered approvals with scope: "always allow *this* command
  in *this* project" — scopes are exact (command + args pattern + path),
  listed, and revocable in one screen; nothing is remembered silently.
- **M-097** The OS sandbox (Codex's crown, native): commands run under
  OS confinement (Linux namespaces/seccomp, macOS sandbox-exec,
  Windows job objects as far as each honestly goes) — no Docker, ever;
  per-platform truth in the platform table.
- **M-098** Network gates: outbound network per-tool and per-domain
  allowlists; a sandboxed command that reaches for the net is refused
  and the refusal is news, not a log line.
- **M-099** Path jail: file tools confined to the workspace + named
  grants; escapes by symlink are checked, not assumed away.
- **M-100** Plan mode perfected: in plan posture the coder may read
  everything and write nothing; the plan it produces is slices with
  acceptance checks (Part IX form), and approving the plan is the one
  gate to building.
- **M-101** Hooks — the full lifecycle: pre/post tool, pre/post edit,
  on-test, on-commit, on-session events running user scripts; hook
  output can block with a reason the coder must answer.
- **M-102** Hook packs: the house hooks (run tests after edits, guard
  the README, verify pushes) shipped as installable packs.
- **M-103** Background tasks: long commands (builds, suites, servers)
  run as managed background jobs with live output tails, kill, and
  completion events into the session.
- **M-104** The Keeper pattern built in: a watcher that notices stalled
  work (a dead background job, a crew member gone quiet) and restarts
  or reports per the user's standing keeper law — timers that *work*,
  not timers that watch.
- **M-105** Scheduled work: cron-style jobs ("run the suite at dawn",
  "check the upstream repo weekly") as data, with the same approval
  lines as live work.
- **M-106** Headless fleet mode: `mythic run` grown for CI — parallel
  tasks across repos, machine-readable verdicts, artefact bundles,
  honest exit codes; a fleet run is resumable.
- **M-107** Budgets as guardrails: per-task and per-session token, cost,
  time, and command budgets; hitting a budget is a graceful pause with
  a report, never a mid-edit death.
- **M-108** The kill switch everywhere: one key/command halts the coder,
  the crew, background jobs, and pending approvals — tested, instant.
- **M-109** Audit trail: every tool call, approval, edit, and command in
  the journal with actor (human/coder/crew/hook) — exportable for
  review; the trail is append-only.
- **M-110** Secret hygiene in action: the coder never echoes secrets,
  redacts known key shapes from outputs and logs, and refuses to commit
  files matching secret patterns (with the file named, content never
  shown).
- **M-111** Destructive-command doctrine: a written ladder (reversible →
  costly → irreversible) with the approval each rung needs; `rm -rf`
  class acts always name their targets in plain words first.
- **M-112** Rollback drills: scripted disasters (bad mass edit, wrong
  branch push attempt, corrupted session) recovered in tests.
- **M-113** Multi-repo workspaces: several repos under one session with
  per-repo policies; cross-repo changes are one change set, reviewed
  whole.
- **M-114** Remote and SSH work: run the coder against a project on
  another machine (Mimir, purplelongship) through one connection —
  files and commands stay on that machine.
- **M-115** Offline and degraded grace: provider down, LSP down, net
  down — each failure narrows the coder honestly and says what it lost.
- **M-116** Approval by phone-sized moments: approvals are single,
  complete questions with full context (Volmarr's law for his own
  Muse, applied to his coder): what, where, what it does, one tap.
- **M-117** Safety regression suite: every doctrine rule above as a test;
  the suite is a release gate, not documentation.
- **M-118** Third-party red-team pack: crafted prompt-injection and
  tool-abuse attempts (from files, web pages, issues) the coder must
  refuse or defang — run in CI.
- **M-119** Policy as code: project policies in a checked-in file
  (postures, jails, hooks) so a team's rules travel with the repo.
- **M-120** Part V gate: an overnight-style autonomous run on the
  benchmark pack under Trusted Forge — sandbox on, budgets on, audit
  trail complete, zero doctrine violations.

## Part VI — The Crew (M-121 – M-146)

*Goal: the six offices become a true crew system — file-defined agents,
parallel worktrees, teams that divide a roadmap and merge without
bloodshed. Claude Code's agent teams and Aider's architect/editor are
the floor.*

- **M-121** Agents as files: crew members defined in data (name, office,
  model route, tools, posture, character) — the existing characters
  become the first castings; new members are files, not code.
- **M-122** The six offices formalised: Skald (intent & vision),
  Architect (design), Forge Worker (build), Auditor (verify),
  Cartographer (map & research), Scribe (memory & docs) — duties,
  tools, and hand-off contracts per office.
- **M-123** Custom offices: user-defined roles beyond the six (a
  "Gatekeeper" for security review, a "Benchmarker") with the same
  contract machinery.
- **M-124** Parallel worktrees: each building crew member works in its
  own git worktree on its own branch (the house law from bitter
  experience); the coordinator merges — never two writers in one tree.
- **M-125** Task dealing: a plan's slices are dealt to the crew by
  office fit and current load; the dealing is visible on the board
  (Part VIII) and re-dealable by the human.
- **M-126** Crew comms: structured hand-offs (findings, diffs, questions)
  between members; a member's question to the human is batched and
  asked once, with full context.
- **M-127** Cycle and deadlock detection grown: delegation cycles,
  merge conflicts between members, and duplicated work are caught by
  the coordinator, not by the human.
- **M-128** Merge discipline: member branches merge in slice order with
  tests at each merge; a red merge stops the line, not the whole crew.
- **M-129** Heterogeneous crews: members on different models/providers
  (a Claude Architect, a local-LLM Forge Worker) — routing from
  Part II, budgets from Part V.
- **M-130** The Auditor's veto: no slice is "done" until the Auditor's
  checks pass; the veto is a real gate in the engine, not a custom.
- **M-131** Research swarms: Cartographer-led fan-out for questions
  (docs, options, comparisons) returning one digested answer with
  sources — the deep-research pattern as a crew formation.
- **M-132** Review panels: two Auditors with different models review the
  same change; disagreements are surfaced, not averaged away.
- **M-133** Crew memory: shared project memory (Part VII) with
  per-member notebooks; a member's hard-won fact is findable by all.
- **M-134** Stand-ups: the coordinator's progress digest in plain words
  (done, doing, blocked, needs-you) on demand and at slice boundaries.
- **M-135** Crew sizing honesty: the app recommends crew size by task
  shape and says when one pair of hands beats six.
- **M-136** Agent character voices: cast members keep their written
  characters (the house cast) in how they report — flavour in the
  reporting, never in the code or the facts.
- **M-137** External agents as crew: an outside agent (over MCP, Part X)
  can hold a seat with the same contracts and budgets.
- **M-138** Crew replay: a crew run's hand-offs replayable from the
  journal — how a decision happened is auditable.
- **M-139** Failure fostering: a failed member's task is re-dealt with
  its failure report attached; the same failure twice escalates to the
  human with both reports.
- **M-140** Cost court: crew runs report cost per member per slice; the
  Scribe keeps the ledger that Part XI's efficiency work reads.
- **M-141** The Mythic Coder building itself: the standing dogfood —
  each part of this road is built by the crew it improves, under the
  coordinator's discipline (as the October forge proved it can).
- **M-142** Solo mode dignity: with the crew off, the single coder loses
  nothing — crew is an amplifier, never a requirement.
- **M-143** Crew templates: saved formations (Duo, Full Six, Research
  Swarm, Review Panel) summonable by name.
- **M-144** Interrupts with grace: pausing one member, the whole crew,
  or one slice — each leaves its worktree and journal consistent.
- **M-145** Crew on schedule: formations can be attached to Part V's
  scheduled jobs (a dawn Auditor sweep over yesterday's commits).
- **M-146** Part VI gate: a six-slice feature built by a three-member
  crew in parallel worktrees — merged clean, Auditor-approved, cost
  ledger complete.

---

## Part VII — Memory & Context (M-147 – M-170)

*Goal: a mind that doesn't merely hold more, but holds the **right**
things — the repo map for breadth, retrieval for depth, a memory map
for the project, and compaction that shows its work.*

- **M-147** Context budget made visible: a live meter and a "what's in
  the context and why" panel — every file, note, and map section
  accounted for in tokens.
- **M-148** The @-mention canon: `@file`, `@folder`, `@symbol`, `@url`,
  `@image`, `@session`, `@issue` — one grammar for pulling anything
  into context, in TUI and headless alike.
- **M-149** Instruction files unified: AGENTS.md (the AAIF standard),
  RULES.AI.md (ours), CLAUDE.md and kin read in one precedence order,
  shown in the panel with their sources — foreign projects' files are
  honoured on their own turf.
- **M-150** Project Memory Map (Mythic law): every project grows a
  living map — architecture, decisions, gotchas, where things live —
  maintained by the Scribe as work proceeds, diffs reviewable.
- **M-151** Compaction v2, glass-box: when context compacts, the summary
  is shown, editable, and kept in the journal beside what it replaced;
  nothing the coder "forgets" is unrecoverable.
- **M-152** Retrieval over the code graph: vector RAG (existing) married
  to Part III's symbol graph — retrieval returns *connected* code, not
  confetti.
- **M-153** Session memory across days: resumable sessions carry their
  memory map, open slices, and standing decisions; `--resume` restores
  the *situation*, not just the transcript.
- **M-154** Cross-project memory: lessons learned in one repo (a flaky
  test's true cause, a library's trap) are offerable to other projects
  — with provenance, never as silent contamination.
- **M-155** The Self-Improving ledger: after significant work, durable
  lessons and reusable patterns are captured as candidate memories;
  the human (or standing rule) promotes them — Part IX's learning loop.
- **M-156** Decision records: choices made in session (library picked,
  road not taken, why) written as small ADRs into the project docs by
  the Scribe.
- **M-157** Forget and quarantine: any memory can be inspected, edited,
  or forgotten on the user's word, with the forgetting itself journaled
  (what class of thing, never its content).
- **M-158** Context recipes: saved bundles ("the auth stack", "the Mojo
  build") summonable by name into any session.
- **M-159** Pinning and protection: files/facts the compaction may never
  drop (the task, the laws, the failing test) — pins are visible.
- **M-160** Token thrift: diff-first reading, map-first loading, and
  hash-anchored edits measured as a cost line in `mythic costs` — thrift
  is a reported virtue.
- **M-161** Long-session endurance: a 500-turn session stays responsive;
  journal and retrieval performance budgets set and measured.
- **M-162** Multi-session per project: parallel sessions on one repo
  (different branches) with shared memory map and no journal crosstalk.
- **M-163** Handoff summaries: ending a session writes "where things
  stand" for the next session or the next human — the stand-up (M-134)
  in durable form.
- **M-164** Memory import/export: a project's memory map + ledger as
  portable files (they ride with the repo if the user wishes).
- **M-165** The subconscious v2: the dual-layer vector memory gains
  provenance (where each memory came from), confidence, and decay —
  stale memories fade unless re-earned.
- **M-166** Contradiction watch: when new evidence contradicts a stored
  memory, the newer truth wins *visibly* — the map shows the correction.
- **M-167** Private by architecture: memories live in the workspace/
  user stores; nothing syncs anywhere unless Part X's bridges are
  explicitly opened by the user.
- **M-168** Memory Doctor: `mythic doctor` gains memory checks (corrupt
  stores, orphaned vectors, map drift) with safe repairs.
- **M-169** Cold-start kindness: opening a huge, old project rebuilds
  its map in the background while the coder is already useful.
- **M-170** Part VII gate: a week-old benchmark session resumed — the
  coder states the situation correctly from memory alone, then finishes
  the task; compaction glass-box verified mid-run.

## Part VIII — The Beautiful Face (M-171 – M-200)

*Goal: the nicest-to-use coding CLI in the field. Not the flashiest —
the one whose every surface respects the human: plain words, visible
state, one-tap decisions, beauty that never costs comprehension.*

- **M-171** The TUI redesign charter: every screen re-judged against
  M-004's kindness rules and the Visual Design Lawbook; a written
  verdict per screen before code moves.
- **M-172** Streaming work view: the coder's actions stream as a calm
  narrative (reading…, editing `auth.py`…, running tests…) with tool
  detail one keystroke away, never in the face.
- **M-173** The Slice Board: plans and roadmaps as a visible board
  (queued / building / verifying / banked) — the Mythic way of working
  *seen*; the human can re-order, pause, or strike a slice by hand.
- **M-174** Approval cards perfected: one decision per card, full
  context on the card, remembered-scope offered precisely, keyboard
  and mouse equal.
- **M-175** The fuzzy everything picker: files, symbols, commands,
  sessions, models, themes — one fuzzy finder grammar everywhere.
- **M-176** Slash-command palace: every command discoverable from `/`
  with plain-language descriptions and examples; custom commands
  (Part X skills) join the same palace.
- **M-177** Prompt craft: multi-line editing, history per project,
  image paste, file drop, dictation (M-180) — the input box is a small
  editor, not a slot.
- **M-178** Status line of truth: model, posture, context meter, cost
  so far, crew state, sandbox state — six facts, always visible, each
  opening its panel on a keypress.
- **M-179** Themes grown up: the theme system gains the Design Lawbook's
  discipline (darkness ladders, accent budgets), plus a high-contrast
  and a no-colour theme that lose nothing.
- **M-180** Voice in and out: push-to-talk dictation for prompts, and
  spoken stand-ups via the existing TTS (direct catalog casting, the
  house voice law) — voice is an extra door, never the only door.
- **M-181** Notifications with manners: long jobs announce completion
  (terminal bell/OS notification, once), failures announce once with
  the one action that matters; silence is the default posture.
- **M-182** The plain-language skin: a "Jarl mode" register — reports,
  approvals, and stand-ups in plain everyday words, technical detail
  folded behind a keypress. (Volmarr's standing law for his own Muse,
  built into his own coder.)
- **M-183** Error kindness: every error states what happened, what it
  means, and the most likely fix in plain words — technical trace one
  key away; no raw stack ever lands on a user unaccompanied.
- **M-184** Onboarding in five minutes: first run detects providers,
  offers Kista key-keeping, walks one tiny real task — success before
  configuration, always.
- **M-185** The tutorial grown: interactive lessons per feature family,
  runnable inside a scratch repo; `mythic tutorial` becomes the manual
  you play.
- **M-186** Help that answers: `?` anywhere gives help *for that
  screen*; a question box ("how do I undo a commit?") answered from
  the local docs by the coder itself.
- **M-187** Keyboard sovereignty: every act reachable by keyboard; a
  printable keymap; vim-mode prompt option for those whose hands
  speak it.
- **M-188** Mouse manners: click, drag-select, scroll, and links that
  open files at line numbers in the user's editor.
- **M-189** Session gallery: past sessions as browsable cards (task,
  outcome, cost, duration) with resume/fork/export — history as a
  library, not a log file.
- **M-190** The costs face: live spend per session and per slice, with
  the honesty rule kept (unknown = unknown) and budgets from M-107 as
  gentle warnings before walls.
- **M-191** Diff theatre final form (with M-091): the review screen a
  user would *choose* to read code in — folding, intra-line colour,
  jump-to-file, comment-on-hunk feeding back to the coder.
- **M-192** Multi-pane working: chat, board, files, and terminal panes
  in the layouts the field loves — plus the Mythic layout (board
  left, work centre, crew right).
- **M-193** Splash and ceremony, restrained: the forge's face keeps its
  beauty inside the Lawbook's budgets — ceremony at start and at a
  roadmap's completion, quiet the rest of the time.
- **M-194** Small-terminal grace: the TUI folds gracefully to 80×24 and
  to a phone-over-SSH width without losing the work.
- **M-195** Copy and share: any answer, diff, or report copyable as
  clean markdown; a shareable session summary generated on command.
- **M-196** Settings as one room: every setting in one searchable
  screen, each with its plain-language meaning and its current source
  (default/project/user/session) shown.
- **M-197** Command palette: Ctrl-K over everything — commands,
  actions, navigation, settings — the one door frequent hands use.
- **M-198** Undo of UI itself: closing a pane or clearing a view is
  never destructive to work; view state per session persists.
- **M-199** Accessibility verification: M-016's tests re-run as gates —
  keyboard-only completion, contrast, reduced motion, no-colour play.
- **M-200** Part VIII gate: the Stranger Test — a new user, docs only,
  completes a real task in the TUI inside thirty minutes; every stumble
  is a fix or a doc correction before the gate passes.

## Part IX — The Mythic Method Engine (M-201 – M-232)

*Goal: the differentiator made machinery. Other CLIs have "plan mode";
Mythic **is** a method — intent → plan → slices → build → verify → bank,
with memory maps, keepers, and self-improvement — running every project
the way Volmarr's forges already run.*

- **M-201** Campaigns as data: a roadmap/campaign file (parts, slices,
  acceptance checks, state) the app reads, displays (M-173), executes,
  and keeps current — this roadmap is its first citizen (M-017).
- **M-202** Intent capture (PROJECT_FORGE form): a new project opens
  with what/why/success in the user's plain words, stored verbatim;
  the coder's plan must cite it.
- **M-203** The slicing engine: from an approved intent, the Architect
  drafts slices sized to the house grain (one verifiable outcome each)
  with dependencies — the human approves the *shape*, not every step.
- **M-204** The Juggernaut loop as runtime: inspect → build → test →
  repair → continue, per slice, without asking file/framework questions
  the code can answer; the loop's state machine is explicit and visible.
- **M-205** Acceptance gates per slice: each slice carries its checks;
  the Auditor (M-130) runs them; a slice banks only green — "banked"
  is a state with evidence, not a feeling.
- **M-206** Banking discipline: banked slices commit (M-078) and, where
  the user has so ruled, push with remote verification — the app knows
  the house git laws and recites them in its plan.
- **M-207** Keeper runtime: Part V's keeper specialised — a campaign's
  keeper restarts stalled slices, deals the next slice when one banks,
  and only ever reports milestones, blockers, and completion.
- **M-208** The pause-lines wired: destruction, irreversible infra,
  cost, publishing, sending-as-user, secrets, security — the loop
  *cannot* cross them unapproved; the lines are data with the user's
  own wording preserved.
- **M-209** Question law: when the human asks a question mid-campaign,
  the campaign pauses and the question is answered first, plainly and
  fully — then work resumes (Volmarr's supreme law, as a feature).
- **M-210** Scope sentry: work drifting beyond the named target (wrong
  repo, wrong branch, extra features unasked) is caught against the
  campaign file and stopped with a report.
- **M-211** Memory-map upkeep: the Scribe updates the Project Memory
  Map in the same session as each banked slice (Mythic law) — the map
  is never a later chore.
- **M-212** The never-leave-a-bug rule: a bug discovered mid-slice is
  fixed in scope or commissioned as a new slice on the spot — the loop
  has no "note it and move on" state.
- **M-213** Retrospectives: at part and campaign close, the crew writes
  what was learned; lessons flow to the Self-Improving ledger (M-155).
- **M-214** Pattern extraction: repeated successful manoeuvres become
  candidate skills (Part X) drafted by the Scribe for approval.
- **M-215** Estimate honesty: slice forecasts (time/tokens) recorded
  against outcomes; the app shows its own calibration, improving
  visibly or not at all.
- **M-216** Multi-campaign hall: several campaigns across repos with
  one board; keepers per campaign; the human sees the whole forge at
  a glance.
- **M-217** Campaign templates: house shapes (feature build, bug hunt,
  migration, hardening, docs) as starting campaign files.
- **M-218** The 500-slice road as a campaign: Volmarr's Mimisbrunnr
  roadmap loadable as a campaign file (via the M-002 concordance) —
  his own road, runnable.
- **M-219** Interrupts and resumes across days: a campaign paused
  mid-slice resumes from journal + map with the situation restated in
  plain words before work continues.
- **M-220** Milestone reports: at part boundaries the coordinator
  reports plainly — done with evidence, partial with its road, blocked
  with what it needs.
- **M-221** The plain-language build log: the campaign's diary in the
  user's words (their domain terms preserved, per the Plain-Language
  Protocol) — readable by the human it was built for.
- **M-222** Guarded self-modification: Mythic improving *itself* under
  campaign rules (M-141) with the Auditor doubled — the forge may
  sharpen its own hammer only on the record.
- **M-223** Failure taxonomy: slice failures classified (code, test,
  environment, provider, scope) with the remedy each class has earned
  historically — the loop learns its own weather.
- **M-224** Dry-run campaigns: a campaign can be rehearsed (plan,
  dealing, gates) with models mocked — the shape proven before money
  moves.
- **M-225** Campaign export: the whole campaign (file, journal, map,
  evidence) as a portable bundle — a project's memory, ownable.
- **M-226** Standing orders: user-level laws (no-Docker, README
  guardian, manual-only workflows, keeper law) stored once and binding
  every campaign — the app keeps the user's laws so the user needn't
  repeat them. **Never make the user say it twice** is a feature.
- **M-227** Workflow default honoured: repositories' CI is proposed as
  manual-dispatch by default on Volmarr's projects (his standing
  ruling), and the coder says so when it writes a workflow.
- **M-228** Team-of-one scaling: the same machinery serves a hobby repo
  and a 500-slice epic without ceremony change — grain follows the
  work, not the tool's ego.
- **M-229** The method, teachable: `mythic tutorial` gains the Method
  course — a newcomer learns campaigns by running a tiny one.
- **M-230** Method metrics: slices banked, gate pass rate, repair
  rounds, calibration — the method's own health on the metrics board.
- **M-231** Cross-app method: campaigns can name slices that live in
  other tools (a Samtal slice, a Sagnaskemma slice) as tracked
  externals — the forge sees Volmarr's whole workshop.
- **M-232** Part IX gate: this roadmap's own Part II executed *by the
  Method Engine itself* from campaign file to banked slices — the
  method proves itself on its own birth.

---

## Part X — Bridges (M-233 – M-254)

*Goal: the forge plays well with the whole workshop and the wider
world — MCP in both directions, IDE companions, the ecosystem's own
hearths (Samverk, Samtal, Kista, Aesir), and painless arrival for users
of rival tools.*

- **M-233** MCP client: Mythic *consumes* MCP servers (tools, resources,
  prompts) with per-server permissions under the same policy system —
  the missing half of its MCP face.
- **M-234** MCP server v2: the existing `mythic-mcp` gains campaign,
  board, and memory-map services with versioned contracts; external
  agents (Hermes-class) can be dealt slices.
- **M-235** MCP registry kindness: known servers browsable and addable
  from the TUI with their tools listed before trust is granted.
- **M-236** Skills standard: reusable skill packs (the Agent Skills
  form) loadable per project and per user; Volmarr's own skill library
  is the first citizen.
- **M-237** Custom commands: user/project slash commands as small files
  (prompt templates with arguments) joining the M-176 palace.
- **M-238** Plugin bundles: skills + commands + hooks + agents in one
  installable bundle with a manifest and provenance; local-first, no
  store required.
- **M-239** IDE companions I — VS Code family: open-file-at-line,
  selection-into-context, and diff-in-editor bridges.
- **M-240** IDE companions II — JetBrains and the generic road: an
  editor-agnostic protocol any IDE plugin can speak; terminal-first
  remains complete without any IDE.
- **M-241** Rival importers: settings, commands, instruction files, and
  MCP configs imported from Claude Code, Codex, OpenCode, Aider, and
  Gemini/Antigravity layouts (per M-014's study) — arriving users keep
  their habits.
- **M-242** Samverk bridge: repos, issues, and PRs on Volmarr's own
  forge with the same craft as GitHub's (Part IV), once Samverk's own
  road provides the surfaces.
- **M-243** Samtal bridge: a seat in a hall can summon the coder;
  stand-ups and milestone reports post to the hall; approvals can be
  given in the hall under the same scope rules.
- **M-244** Kista as the key-keeper (with M-032): every bridge's
  credential resolves through Kista; a bridge without a key asks once.
- **M-245** Aesir deepening (with M-025): Aesir sessions selectable per
  role; its honest capability reports shape what the router asks of it.
- **M-246** GitHub/GitLab/Bitbucket parity: the forge's git craft is
  host-agnostic; hosts are registry entries like providers.
- **M-247** CI bridges: read CI results as facts into the session;
  propose workflow changes only as drafts (and manual-dispatch by
  default on Volmarr's repos, M-227).
- **M-248** Issue trackers beyond git hosts: Linear/Jira-class bridges
  as MCP-first integrations, read-mostly, write by approval.
- **M-249** The WYRD seam: world-state from Volmarr's WYRD engine can
  inform long campaigns (which machine is free, which forge is hot) —
  the workshop aware of itself.
- **M-250** Webhook doors: inbound events (a PR opened, an issue filed)
  can *propose* campaigns — proposals only; nothing builds unbidden.
- **M-251** Export everything: sessions, campaigns, memories, and
  configs export in open formats; leaving is as easy as arriving
  (the Interoperability Principle).
- **M-252** Docs MCP pattern generalised: any project's docs MCP (like
  the Mojo one) attachable as a knowledge bridge in one step.
- **M-253** Bridge permissions audit: one screen listing every bridge,
  its keys' home (Kista refs), its scopes, its last use.
- **M-254** Part X gate: one campaign slice executed across bridges —
  issue from a host, build locally, PR raised, stand-up posted to
  Samtal — with credentials never leaving Kista.

## Part XI — The Proof Spine (M-255 – M-272)

*Goal: close the way this house closes — with evidence. Benchmarks
against the field's yardsticks, platform truth, security proof, and a
release that tells the truth about itself.*

- **M-255** The benchmark harness: M-008's pack automated — task,
  sandbox repo, run, grade (tests + diff review rubric) — repeatable
  per part and per release.
- **M-256** Published-yardstick runs: SWE-bench-style public sets run
  where licences allow, results reported with model, cost, and date —
  comparable to the field's claims, never inflated.
- **M-257** Regression court: every part's gate results re-run as one
  battery; a red anywhere stops the release, not just the part.
- **M-258** Performance budgets: cold start, repo-map build on a
  100k-file repo, TUI frame health, memory ceiling — measured on the
  VM, Mimir-class ARM, and the laptop; budgets from measurement.
- **M-259** Platform matrix final: M-013's table re-proven cell by
  cell; unproven cells ship labelled NOT PROVEN, not silent.
- **M-260** Security audit: the Part V doctrine + M-118 red-team pack +
  an independent read of the sandbox/jail code, findings fixed or
  roaded with owners.
- **M-261** Privacy audit: no phone-home verified by network capture
  during a full benchmark run; the capture is the evidence.
- **M-262** Accessibility final gate: M-199's checks on the shipped
  TUI, with the keyboard-only task timed.
- **M-263** The docs completion: user guide, method guide, bridge
  guides, and per-part interface notes reconciled with shipped code —
  the Scribe's closing duty, H7-style.
- **M-264** README care: the repo README extended **by hand** with the
  new story — nothing removed, per Volmarr's standing law.
- **M-265** Migration proof: a workspace from the current release opens
  in the new one — sessions, journals, configs, memories intact —
  proven by the M-010 forward-compat tests grown teeth.
- **M-266** The Stranger Fleet Test: M-200's stranger + a headless CI
  run + a crew campaign, all from docs alone, on a clean machine.
- **M-267** Cost-of-quality report: benchmark scores against spend per
  model route — the honest shopping guide for the user's own money.
- **M-268** Changelog that tells the truth: proven / partial / NOT
  PROVEN per feature family, in the release itself.
- **M-269** Version and release shaping: the release cut on
  `development` per house discipline, tagged, with the evidence index.
- **M-270** The roadmap's own audit: every slice marked DONE with
  evidence, PARTIAL with its road, or NOT PROVEN with its reason — in
  this file's closing twin.
- **M-271** Retro and lessons: the campaign retrospective written into
  the Self-Improving ledger; patterns worth keeping named as skills.
- **M-272** Final report to Volmarr: plain language first — what the
  coder can now do, where it beats the field, where it does not yet —
  with the evidence index.

---

## 5. Order and dependencies (the short truth)

Part I first (the census steers everything). Part II early — every other
part spends models. Part III before IV (edits need intelligence) and
before VI's deep dealing. Part V's doctrines (M-095–M-101, M-107–M-111)
land before VI's autonomy widens. Part VII after III (retrieval needs
the graph). Part VIII continuously, its gate late. Part IX can begin its
data forms (M-201–M-203) as soon as Part I banks, and grows teeth as
II–VII land. Part X as surfaces allow (Samverk's bridge waits on
Samverk's own road). Part XI closes. Keeper discipline throughout:
contract, build, test, bank, continue — every project in motion guarded
by a 10-minute keeper that *continues* stalled work, per Volmarr's
standing law — and every discovered bug fixed in its slice or
commissioned on the spot, never merely noted.

## 6. What this roadmap deliberately does not do

- No hosted cloud version, no accounts business, no telemetry: Mythic
  is a sovereign local tool, in the house's image.
- No Docker, anywhere, for anything (Volmarr's law) — sandboxing is
  native or it is honestly absent on that platform.
- No model training: Mythic wields models; Aesir is where models are
  *run* sovereignly, and this road feeds it work (M-025), not rivalry.
- No copying of rivals' code or closed assets: features are studied as
  behaviours from public documentation and rebuilt clean-room.
- No removal of the fun: the cast, the ceremony, the Viking soul stay —
  disciplined by the design law, never despite it.

## 7. First steps when the word is given

1. File this roadmap into the repo (`docs/` beside ROADMAP.md) by hand,
   extending — never overwriting — what stands there; Volmarr's
   500-slice Mimisbrunnr file untouched.
2. Open the campaign: campaign file (M-201 form, back-fitted), state
   file, and a 10-minute keeper in the house pattern.
3. Strike M-001 (the Census) and M-002 (the Concordance) first — know
   the field and honour the old road before building the new one.

*Carved 2026-10-30, at Volmarr's word, by Yrsa.*
