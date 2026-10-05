# Core runtime contracts

`runtime_settings(config)` reads packaged YAML defaults, merges `config.runtime`,
and validates operational retry/turn budgets. Invalid values raise `ValueError`.
`TurnResult` records completed/failed/cancelled status, final text/error and total
tokens. `TurnCancelled` distinguishes user interruption from ordinary failure.

`EventBus` takes callback snapshots before dispatch and isolates callback failures.
Callbacks run without the subscription lock. Sync publication cannot await async
subscribers; those are skipped with a warning. UI adapters own thread marshaling.

`Agent.chat(prompt)` serializes turns, returns final response text and sets
`last_result`. Errors raise after setting a failed/cancelled outcome. History is
JSON-serializable dictionary protocol data. Network, tools, and events run outside
the history lock. Cancellation currently interrupts retries/loop boundaries;
active I/O cancellation belongs to S06. Tool execution policy belongs to S03/S06.

`ToolPolicy(mode, approval)` supports read-only/ask/trusted. Read-only tool names
come from packaged `data/permissions.yaml`. Denial records a tool name and has no
operation side effect. The runtime consults an attached policy before execution;
CLI adapters attach it explicitly. S06 completes TUI/direct/MCP enforcement.
