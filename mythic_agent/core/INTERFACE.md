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

`ConfigManager(root=None).load_config()` preserves source bytes, unknown fields and
custom prompts; it normalizes types/migrations in memory. Explicit root overrides
`MYTHIC_HOME`, which overrides the home default. `save_config(dict)` returns bool,
backs up originals requiring recovery, and uses private atomic writes/process
locking. A failed save must not be presented as a saved setting. Packaged defaults
and current schema version are identical. Runtime duration settings must be finite.

`SessionStore(workspace, state_root, redactor)` owns a versioned private SQLite
database per workspace. `create(context, metadata)` and `resume(id)` acquire an
exclusive process lease retained until `release(id)`. `checkpoint` requires the
lease and atomically records validated protocol context/outcome and a transcript
event. `resume` closes pending tool groups with interrupted diagnostics, never
executes tools. `list_sessions()` and `export(id)` are redacted read snapshots;
export retains append-only history independently of selected context. Unknown
storage versions/malformed checkpoints fail without replacing original data.

`SecretRedactor(config)` redacts configured/environment credentials, token forms
and URL credentials. `protect_logging` protects formatted records/tracebacks.
Local transcripts intentionally retain original text; exports and diagnostics
are redacted. Neither function is a general source-code secret scanner.
