# Mythic Agent architecture

## Product boundary

Mythic Agent is a local coding harness. Humans use a terminal chat loop or the
Textual interface. AI agents use a noninteractive CLI with structured output or
the MCP integration. All interfaces must share workspace resolution, turn
processing, tool execution, permission policy, persistence, and error semantics.
The Viking identity is presentation and configurable character data; reliability
contracts apply independently of the selected persona.

## Current source map

| Domain | Current owners | Responsibility |
| --- | --- | --- |
| Launch | `cli.py`, `core/engine.py` | Entry point, bootstrap, crash handling |
| Runtime | `agents/llm.py` | Prompt, history, provider calls, agent registry/workers |
| Tools | `agents/tools.py` | Schemas, files, commands, memory and integrations |
| Commands | `agents/command_handler.py` | Human slash commands and Git workflows |
| Policy/execution | `core/policy.py`, `core/execution.py` | Explicit decisions, owned processes/requests and cleanup |
| Persistence | `core/sessions.py`, `core/edits.py`, `core/storage.py` | Leased transcripts, edit journal, atomic private writes |
| Diagnostics | `core/redaction.py`, `core/runtime.py` | Redacted errors, outcomes and finite budgets |
| Config | `core/config_manager.py`, packaged `data/*.yaml`, `constants.py` | Settings, defaults, persona profiles |
| Events | `core/secure_api.py` | In-process publish/subscribe |
| Memory | `memory/core_memory.py`, `memory/vector_db.py` | Core blocks and retrieval |
| Human UI | `ui/main_app.py`, `ui/screens/`, `ui/components/` | Textual views and input |
| Integrations | `mcp_server.py`, `core/audio.py`, `core/tts.py` | MCP and optional voice |
| Resources | `data/data_loader.py`, character/skill Markdown | Data ingestion and prompts |

`arcanum/` is an adjacent project, not part of the core turn pipeline. Existing
root experiments and historical proposals are reference material, not CI gates.

## Target boundaries

1. **Interface adapters** parse human input or machine requests and render typed
   runtime events. They do not implement a second provider/tool loop.
2. **Runtime** owns one turn at a time per agent, dictionary protocol messages,
   tool-call/result ordering, lifecycle, cancellation, and completion status.
3. **Provider adapter** owns endpoint/model configuration, credentials, timeout,
   transient retry classification, streaming, and normalized usage.
4. **Workspace/tool services** resolve paths, validate arguments, apply policy,
   perform atomic journaled edits, and execute commands with cancellation. Shell
   execution is explicitly powerful; path containment is not an OS sandbox.
5. **Persistence** stores versioned sessions and edit receipts with workspace
   identity. Raw transcript durability is separate from selected model context.
6. **Memory/context** selects relevant information and compacts complete protocol
   turns without losing the stored transcript. Retrieval can operate offline.
7. **Configuration/resources** load portable defaults and preserve custom data.
   Optional integrations fail independently with actionable diagnostics.

The event bus remains an adapter API. Its subscriptions need snapshot dispatch
and explicit cleanup; it is not the durable session store or a cross-process API.

## Turn flow and invariants

Input -> workspace/session selection -> prompt/context assembly -> provider ->
normalized assistant message -> validated/policy-approved tool calls -> matching
tool result messages -> provider continuation -> completion -> persistence.

- Every tool call has exactly one result with its call ID before another user turn.
- History contains serializable dictionaries, never opaque SDK objects.
- A denied operation has no side effects and yields a visible refusal.
- An agent edit never changes unrelated Git history or staged contents.
- A workspace switch cannot silently expose a different project's memory.
- Failure and cancellation produce terminal statuses; they are not success.
- Human terminal rendering cannot contaminate JSON/JSONL output or MCP stdout.
- A completed slice has evidence and a verified remote revision.

## Compatibility and migration

Keep `mythic`, `mythic-mcp`, `Agent.chat`, `execute_tool`, and current slash
commands as supported entry points, adapting them to the services above. Keep the
TUI default launch. Add explicit chat/run modes for terminals and machines.
Migrate settings/session formats additively; preserve malformed originals for
diagnosis. Preserve legacy memory and offer an explicit migration rather than
silently copying global memory into every workspace.

Detailed implementation and verification order: [ROADMAP.md](ROADMAP.md).
