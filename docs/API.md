# Mythic Agent — API Reference

This document covers the machine-facing contracts of Mythic Agent: the
`mythic run` CLI contract, the MCP server tools, and the Python entry
points. The human TUI and terminal chat are documented in
`docs/USER_GUIDE.md`; the plain human/machine CLI guide is `docs/CLI.md`.

Conventions:

- Version: `mythic --version` reports the installed metadata, falling back
  to `mythic_agent.__version__.__version__` (the single version source) in
  source checkouts.
- MCP capability report: `mythic_capabilities` returns
  `{"version", "api_version": "1.0", "interfaces", "tools", "features"}`.
- All machine interfaces share the execution contracts in `ARCHITECTURE.md`.

## 1. `mythic run` — machine CLI contract

One-shot task execution for scripts and AI callers.

```
mythic run [--workspace DIR] [--model NAME] [--base-url URL]
           [--resume SESSION_ID] [--permission read-only|ask|trusted]
           [--format plain|json|jsonl] [prompt]
```

- `prompt` positional; when omitted, the full prompt is read from stdin.
- Output formats:
  - `plain` (default): human-readable text on stdout.
  - `json`: one versioned result object with `status`
    (`success` | `error` | `cancelled`), plus `output`, `session_id`,
    `usage`, and `error` fields.
  - `jsonl`: newline-delimited JSON events, one per provider response, then
    a final result object.
- Exit codes: `0` success · `1` error · `2` CLI usage error ·
  `3` approval-required (a tool was denied under the active policy).
- Permission default for `run` is `read-only`; `ask` without an interactive
  terminal yields a structured refusal rather than blocking; `trusted`
  explicitly authorizes all configured tools including shell commands.
- `Ctrl+C` / EOF behavior, session resume, and redaction rules are
  documented in `docs/CLI.md`.

### Other machine-friendly commands

| Command | Output |
|---|---|
| `mythic sessions [--workspace DIR] [--search Q]` | JSON session list |
| `mythic sessions --export SESSION_ID` | Complete redacted transcript (JSON) |
| `mythic doctor --json` | Health checks as JSON: name, status, message, fix hint |
| `mythic cache --json` | Cache stats: entries, hits, misses, size, TTL |
| `mythic cache --clear [--json]` | Drops cached responses; reports count |
| `mythic costs --json` | `{"total_usd", "by_model", "unknown_models"}` |
| `mythic metrics --json` | Timers, counters, gauges, traces |
| `mythic review PATH [--severity info|warning|error] [--json]` | Static review issues as JSON |

## 2. MCP server — `mythic-mcp`

Install the `mcp` extra, then run `mythic-mcp` (stdio transport). The server
invokes the same workspace/policy/session/task services as the CLI — there
is no independent memory behavior and no UI is loaded.

**Permission model.** Every tool is permission-checked before effects. The
default machine policy is read-only: mutating tools return a structured
denial naming the required authorization. Configure the machine permission
mode (or `MYTHIC_PERMISSION`) to allow effects; delegated agents inherit a
policy snapshot.

### Tools

**Memory**

- `mythic_core_memory_read(agent_name="Primary") -> str`
  Read the Core OS Memory block for an agent.
- `mythic_core_memory_append(block_name, content, agent_name="Primary") -> str`
  Append text to a memory block. Valid blocks: `persona`, `human`,
  `project`, `long_term_notes`.
- `mythic_archival_search(query, top_k=5, agent_name="Primary") -> str`
  Semantic search over archival memory; results include relevance scores.
- `mythic_archival_insert(text, agent_name="Primary") -> str`
  Persist a new memory into archival storage.
- `mythic_update_project_status(project_name, status_markdown) -> str`
  Create or update a Markdown status file for a project (filename is
  sanitized).

**Delegation and tasks**

- `mythic_delegate_to_subagent(sub_agent_name, task_description, sender_name="ExternalAgent") -> str`
  Spawn a sub-agent (e.g. `Skald`, `Architect`, `Forge Worker`) in the
  background and assign it a task. Delegation cycles are detected and
  refused.
- `mythic_task_status(task_id) -> str`
  JSON with `task_id`, `name`, `state`
  (`queued|running|completed|failed|cancelled`), `parent_id`, and the
  `result`/`error` when finished.
- `mythic_task_cancel(task_id) -> str`
  Cancel a running task and its children.

**Discovery**

- `mythic_capabilities() -> str`
  JSON: `version`, `api_version`, `interfaces`
  (`tui`, `terminal-chat`, `run-cli`, `mcp-stdio`), the agent `tools`
  list, and `features` (`sessions`, `permissions`, `tasks`, `doctor`,
  `completions`).

### Agent tools (available to the model inside a turn)

18 tools: `read_file`, `write_file`, `run_command`, `list_dir`,
`replace_file_content`, `grep_search`, `update_status`, `delegate_task`,
`send_message`, `core_memory_append`, `core_memory_replace`,
`archival_memory_insert`, `knowledge_db_semantic_search`,
`knowledge_db_sql_query`, `archival_memory_search`, `github_execute`,
`clear_context`, `delegate_parallel_tasks`. All are validated against
schemas and the active permission policy before any effect.

## 3. Python API

Install the package (`pip install -e .`) and import from `mythic_agent`.
Core imports stay light — importing `mythic_agent.cli` never starts
workers or pulls in Textual/Torch/audio.

```python
from mythic_agent.cli import main, package_version
from mythic_agent.mcp_server import main as mcp_main

# Run the CLI programmatically (returns a process-style exit code).
exit_code = main(["run", "--format", "json", "List the failing tests"])

# Version (installed metadata, or the single source in a checkout).
print(package_version())
```

### Task registry (Slice 2 / S08)

```python
from mythic_agent.agents.tasks import get_registry, TaskState, AgentBudgets

registry = get_registry()
task = registry.get(task_id)
print(task.state)          # TaskState.QUEUED | RUNNING | COMPLETED | FAILED | CANCELLED
registry.cancel(task_id)   # cancels the task and its children
```

### Health checks (Slice 11)

```python
from mythic_agent.doctor import run_checks, HealthStatus

results = run_checks()                    # all offline checks
results = run_checks(["config", "tools"]) # named subset
for r in results:
    print(r.name, r.status.value, r.message, r.fix_hint)
```

Register a custom check with the `@health_check("name")` decorator; run it
from `mythic doctor --check name`.

### Cache, costs, metrics

```python
from mythic_agent.core.cache import ResponseCache
from mythic_agent.core.costs import CostTracker, price
from mythic_agent.core.metrics import Metrics, Timer, Counter, Gauge

cache = ResponseCache()
print(cache.stats())          # entries, hits, misses, size_bytes, ttl_seconds
cache.clear()

tracker = CostTracker(workspace_root)
print(tracker.total(), tracker.by_model(), sorted(tracker.unknown_models))
cost, known = price("gpt-4o-mini", 1000, 200)  # (usd, price_was_known)
```

### Structured logging (Slice 12)

```python
from mythic_agent.core.mythic_logging import get_logger

log = get_logger("mythic.mycomponent")
log.info("turn completed", extra={"turn": 3, "tools": 2})
```

`JsonFormatter` and `TextFormatter` are available for file/stream handlers.

### Benchmarks (Slice 28)

```python
# Or: python -m mythic_agent.bench
from mythic_agent.bench import measure
print(measure())  # startup_help_s, import timings, peak RSS in KB
```

## 4. Extension points

- **MCP tools:** add `@mcp.tool()` functions in `mythic_agent/mcp_server.py`;
  always route through `_permission(...)` before effects.
- **Doctor checks:** `@health_check("name")` in `mythic_agent/doctor.py`
  returning a `HealthResult(status, message, fix_hint)`.
- **Agent tools:** extend `get_agent_tools()` in
  `mythic_agent/agents/tools.py` with schema-validated definitions.
- **Completions:** regenerate/edit `completions/mythic.bash`,
  `completions/_mythic.zsh`, `completions/mythic.fish` when adding
  subcommands.

Repository plugins are not auto-executed: extensions are registered
explicitly and run under the active permission policy.
