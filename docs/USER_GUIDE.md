# Mythic Agent — User Guide

Welcome to **Mythic Agent**, a Viking-themed AI coding assistant for your
terminal. This guide covers installation, daily use, machine use, and
troubleshooting. It describes measured behavior on the current release; see
`CHANGELOG.md` for what changed.

## 1. Installation

**Requirements:** Python 3.10 or later.

```sh
git clone https://github.com/hrabanazviking/Mythic_Agent_Coder_CLI.git
cd Mythic_Agent_Coder_CLI

# Core only (terminal chat + machine runs, no TUI):
pip install -e .

# With the Textual terminal UI (recommended for interactive use):
pip install -e '.[tui]'
```

Optional extras:

| Extra | What it adds |
|---|---|
| `tui` | The Textual terminal user interface (default launch mode) |
| `mcp` | The `mythic-mcp` Model Context Protocol server |
| `knowledge` | Knowledge-database integrations |
| `voice` | Voice input/output |
| `voice-cloning` | Voice cloning (separate platform/runtime requirements) |
| `dev` | pytest, build tooling |

Shell completions are in `completions/` — source `mythic.bash`,
`_mythic.zsh`, or `mythic.fish` for your shell.

```sh
# bash
source completions/mythic.bash
# zsh
source completions/_mythic.zsh
# fish
source completions/mythic.fish
```

## 2. First run

Launch `mythic` in your project's directory. Press **F2** (or run
`mythic tutorial`) to open the setup wizard, where you can:

- Select your provider and enter your API key.
- Fetch and select the model.
- Edit the primary system prompt.
- Add global rules applied to all sub-agents.
- Configure sub-agents (or use the default Mythic Engineering team).

`mythic tutorial` walks first-time users through the same setup
interactively from any terminal.

Your configuration lives under `MYTHIC_HOME` (defaults to a platform
application directory) so settings are portable and isolated per
environment. Configuration files are validated and migrated additively —
unknown or customized fields are never silently discarded.

## 3. Interfaces at a glance

| Command | Who it's for | What it does |
|---|---|---|
| `mythic` (or `mythic tui`) | Humans | Full Textual terminal UI |
| `mythic chat` | Humans | Lightweight terminal conversation loop |
| `mythic run "task"` | Humans & AI callers | One-shot task with plain/JSON/JSONL output |
| `mythic-mcp` | AI agents | MCP server over stdio |
| `mythic doctor` | Everyone | System health checks |
| `mythic sessions` | Everyone | List/export workspace sessions |

`mythic --help` and `mythic --version` never start agents, touch the
network, or require credentials.

## 4. Chatting in the terminal

```sh
mythic chat --workspace ./my-project
mythic chat --workspace ./my-project --base-url http://localhost:1234/v1 --model local-model
```

Slash commands available in the chat loop:

| Command | Effect |
|---|---|
| `/help` | Show all commands |
| `/setup` (F2) | Open the setup wizard |
| `/clear` | Clear conversation history |
| `/compact` | Archive earlier turns (history stays complete) |
| `/session` | Show current session info |
| `/model <name> [url]` | Switch model (saved as a preference) |
| `/status` | Show workspace, model, and task state |
| `/add <path>` | Pull a file into context |
| `/stop` | Cancel the active request |
| `/undo` | Restore the last unchanged agent file edit |
| `/quit`, `/exit` | Leave |

**Permissions.** Human chat defaults to `ask` mode: reads are allowed, and
anything that writes files, runs commands, or calls external services asks
for approval on a real terminal. A saved auto-accept preference switches to
`trusted`. `--permission read-only|ask|trusted` overrides for one
invocation. Denied tools return a structured refusal — never a hidden
prompt.

**Undo.** `/undo` restores only the last unchanged agent edit from the
workspace journal. If you edited the file yourself afterward, undo refuses
rather than destroying your work. Git history and the index are never
touched by tool writes.

## 5. One-shot runs (for scripts and AI callers)

```sh
mythic run --workspace ./my-project --format json "Inspect the test failures"
mythic run --workspace ./my-project --format jsonl < task.txt
```

- `run` reads the prompt from the argument or from stdin when omitted.
- `--format plain|json|jsonl`; JSON/JSONL carries a versioned result schema
  with `status` (`success` / `error` / `cancelled`).
- `--resume <session-id>` continues a previous session.
- The machine default permission is **read-only**. `ask` without an
  interactive terminal refuses instead of waiting; `trusted` explicitly
  authorizes all configured tools, including shell commands.
- Exit codes: `0` success, `1` error, `2` usage/CLI error, `3`
  approval-required (a tool was denied).

## 6. Sessions: resume where you left off

Sessions are workspace-scoped, versioned, and stored in a private SQLite
store with exclusive leases so concurrent invocations don't corrupt them.

```sh
mythic sessions                          # list sessions as JSON
mythic sessions --export <SESSION_ID>    # export a complete transcript
mythic sessions --search "deploy"        # filter by id, status, model, metadata
mythic run --resume <SESSION_ID> "continue"
```

Exports are redacted: configured credentials, token forms, and URL
credentials never appear in exports, CLI events, logs, or crash reports.
Failed or cancelled turns survive restart — resume after an interruption
and already-completed tool calls are not executed again.

## 7. Health checks: `mythic doctor`

```sh
mythic doctor            # offline checks; no network, no agent started
mythic doctor --json     # machine-readable output
mythic doctor --fix      # auto-repair safe issues
mythic doctor --live     # also test live provider connectivity (may cost $)
mythic doctor --check config --check tools   # run only named checks
```

Checks cover configuration validity and migrations, provider
reachability/auth (no real calls unless `--live`), tool loading and schema
validity, session-store readability, workspace writability and disk space,
and optional dependency status. Each result reports `ok`, `warning`,
`fail`, or `skip` with a human fix hint.

## 8. Cache, costs, metrics

```sh
mythic cache              # cache stats: entries, hits, misses, size, TTL
mythic cache --clear      # drop all cached LLM responses
mythic costs              # model API cost ledger for the workspace
mythic metrics            # recorded timers, counters, gauges, traces
```

The LLM response cache avoids paying twice for identical requests. The
cost ledger reports totals per model and names models with unknown pricing
instead of inventing blended prices.

## 9. Review, themes, tutorial

```sh
mythic review path/to/file.py        # static review of Python issues
mythic review ./src --severity warning --json
mythic theme --list                  # available color themes
mythic theme --set tokyo_night
mythic tutorial                      # interactive first-run tutorial
```

## 10. Providers

Mythic speaks to any OpenAI-compatible endpoint: OpenRouter, DeepSeek,
OpenAI, local servers (e.g. LM Studio / llama.cpp at
`http://localhost:1234/v1`), and others. Configure once in the setup
wizard, or override per invocation:

```sh
mythic chat --base-url http://localhost:1234/v1 --model local-model
```

Timeout, retry, and token budgets are configurable; transient errors retry
with cancellable backoff inside a finite budget. Auth failures, bad models,
and invalid requests fail fast with a clear classification. Usage is
tracked honestly — unknown cost is reported as unknown, never invented.

## 11. Multi-agent orchestration

The agent can delegate to sub-agents — including the six built-in Mythic
Engineering specialists (Skald, Architect, Forge Worker, Auditor,
Cartographer, Scribe). Tasks have typed IDs and
queued/running/completed/failed/cancelled states; delegation cycles are
detected and refused; cancellation propagates to child tasks. Delegated
agents inherit the caller's permission mode — they never gain privileges
from loaded defaults. Conflicting edits are detected through ownership
tracking.

## 12. MCP server (for external AI agents)

With the `mcp` extra installed, `mythic-mcp` exposes the same
workspace/policy/session/task services over stdio — no terminal required.
See `docs/API.md` for the tool reference. The MCP server shares the
machine permission contract: mutating tools need an explicit policy, and
denials return structured results.

## 13. Troubleshooting

| Symptom | Try |
|---|---|
| `mythic` won't start | `pip install -e '.[tui]'` — the default launch needs the TUI extra |
| Provider auth errors | `mythic doctor` (offline) then `F2` setup wizard to re-enter the key |
| Hangs or stale state | `mythic doctor --fix`; check `mythic sessions` for a stuck session |
| Approval never arrives | In `ask` mode approvals need a real terminal; use `--permission trusted` explicitly for scripts |
| Undo refuses | You edited the file after the agent — undo won't clobber your work; use Git for manual history |
| Something crashed | The crash handler auto-saves; restart and resume the session |

For developers: `docs/DEVELOPMENT.md` covers test/build commands,
`docs/development/PROGRESS.md` records slice receipts, and
`docs/RELEASE_CHECKLIST.md` defines the release gates.
