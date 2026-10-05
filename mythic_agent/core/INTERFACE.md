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
the history lock. Cancellation interrupts owned provider/embedding/retrieval I/O,
retry waits, approvals and process execution. Cancellation is checked again before
accepting a provider response or executing a tool.

`ToolPolicy(mode, approval)` supports read-only/ask/trusted. Read-only tool names
come from packaged `data/permissions.yaml`. Denial records a tool name and has no
operation side effect. The shared tool executor checks schema and policy once
before effects; default direct agents/callers are read-only. Legacy slash/MCP
mutators check the same policy. Approval requires boolean True; closed/broken
callbacks refuse, and TurnCancelled propagates. `fork()` preserves mode/callback
with independent denials. `policy_mode` separates machine defaults from human
legacy auto-accept and gives explicit overrides precedence.

`run_process(command, workspace, shell=False, cancel=None, timeout=300, ...)`
captures complete combined output with incremental progress and returns
`ProcessResult(status, returncode, output, raw_output)`. Status is completed,
failed, timed_out or cancelled; render always includes status/exit code. It owns
a POSIX session/process group or a Windows kill-on-close job. Windows starts
suspended, assigns the job, then resumes the owned primary thread to prevent a
child spawning before ownership. Finally closes/reaps owned resources/descendants,
including when the parent exits first. Approved detached POSIX children are outside
the group contract; the runner is not an OS sandbox. Progress adapter failure
cannot discard capture or abandon the command.

`run_cancellable_async(factory, cancel, interval)` creates a request task and
cancellation watcher, cancels and drains both before closing the owned loop.
An existing caller loop uses an owned worker thread with resources created there.
`CancellableChatClient` preserves injectable `.chat.completions.create`, embeddings
and model-list seams; each request owns/closes an AsyncOpenAI client. Retrieval
HTTP uses the same owned coroutine lifecycle. Streaming/capabilities remain S07.

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
event. The lease is process-wide across agent worker threads; the turn lock
serializes checkpoints. `resume` closes pending tool groups with interrupted diagnostics, never
executes tools. `list_sessions()` and `export(id)` are redacted read snapshots;
export retains append-only history independently of selected context. Unknown
storage versions/malformed checkpoints fail without replacing original data.

`SecretRedactor(config)` redacts configured/environment credentials, token forms
and URL credentials. `protect_logging` protects formatted records/tracebacks.
Local transcripts intentionally retain original text; exports and diagnostics
are redacted. Neither function is a general source-code secret scanner.
