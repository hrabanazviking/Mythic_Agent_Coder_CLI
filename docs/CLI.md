# Human chat and machine use

Install core with `pip install -e .` from the source checkout. Core includes the
terminal chat and run adapters. `pip install -e '.[tui]'` adds the default Textual
front end. `mythic --help` and `mythic --version` never start agents.

## Terminal conversation

```sh
mythic chat --workspace ./my-project
mythic chat --workspace ./my-project --base-url http://localhost:1234/v1 --model local-model
```

Use configured provider settings or per-invocation model/endpoint overrides. The
default chat permission mode is `ask`; file reads are allowed and other tools ask
for approval when stdin is a real terminal. EOF/Ctrl+D or `/quit` leaves; Ctrl+C
interrupts the current turn and returns to input. Active subprocess termination
is being completed in S06, so boundary cancellation is the current guarantee.

Supported commands: `/help`, `/clear`, `/compact`, `/session`, `/model <name> [url]`, `/status`,
`/add <path>`, `/stop`, `/undo`, `/quit`, `/exit`. Quote paths containing spaces.
`/model` explicitly saves the selected model; invocation overrides remain temporary.
`/add` supplies complete file text from the workspace. `/undo` restores only the
last unchanged journaled agent edit and leaves Git history/index alone. Unknown
slash commands are reported rather than sent to the model.

## One-shot tasks

```sh
mythic run --workspace ./my-project --format json "Inspect the test failures"
mythic run --workspace ./my-project --permission trusted --format json "Fix the parser and run its tests"
mythic run --workspace ./my-project --format jsonl < task.txt
```

`run` accepts a positional prompt or full stdin when omitted. It defaults to
`read-only`; writes/commands/delegation/external integrations are denied. `ask`
without an interactive terminal produces a refusal instead of waiting.
`trusted` is explicit authorization to invoke all configured tools, including
shell commands. Workspace file containment is not an operating-system sandbox.
S06 extends this CLI policy to the other front ends and direct integration paths.

Plain output contains final response text; diagnostics go to stderr. JSON output
is one result object. JSONL emits typed tool progress, text and usage events,
followed by one terminal result. Events currently arrive per provider response;
streamed HTTP deltas are S07. Consumers must parse `type` and ignore unknown
optional fields rather than interpreting terminal formatting.

## Version 1 result contract

| Field | Meaning |
| --- | --- |
| `schema_version` | Integer `1` |
| `type` | `result` for the terminal outcome |
| `status` | `completed`, `failed`, `invalid_input`, `approval_required`, `cancelled` |
| `text` | Final response text, or empty when unavailable |
| `error` | Error/refusal explanation or null |
| `workspace` | Resolved workspace or null if initialization failed |
| `model` | Selected model or null before initialization |
| `total_tokens` | Provider-reported cumulative token count; zero if unavailable |
| `permission` | Effective CLI mode or null before initialization |
| `denied_tools` | Tool names refused during the task |
| `session_id` | Persistent workspace session ID, or null before attachment |

| Exit | Meaning |
| --- | --- |
| 0 | Completed without permission refusals |
| 1 | Runtime/provider/configuration failure |
| 2 | Invalid CLI syntax, empty prompt or missing TUI dependency |
| 3 | At least one tool required authorization and was denied |
| 130 | User cancellation |

Argparse syntax failures use ordinary stderr/help and exit 2. Valid run invocations
use the selected result format even for provider/configuration errors. A model's
answer is not evidence that generated code passes tests; inspect tool results and
run the relevant project gates. Autonomous completion receipts are S12.

## Portable state and optional TUI

`MYTHIC_HOME` selects the application state directory (default `~/.mythic`). An
explicit state directory does not import the legacy home configuration. Credentials remain supplied by
existing provider settings/environment; no key is created by CLI launch.

Configuration reads normalize settings in memory and retain customized prompts
and unknown fields. Reads never rewrite the source. Explicit saves use a private
atomic write and process lock; an invalid/older original gets a recovery copy
before replacement. Defaults live in packaged `data/config_defaults.yaml`.
`MYTHIC_MODEL`, `MYTHIC_BASE_URL` and `MYTHIC_WORKSPACE` override loaded settings
in memory. CLI flags take precedence; `/model` explicitly saves a preference.

## Durable sessions

Every terminal chat/run and primary TUI session receives a workspace-scoped ID.
List or export without a provider request:

```sh
mythic sessions --workspace ./my-project
mythic sessions --workspace ./my-project --export <session-id> > transcript.json
mythic run --workspace ./my-project --resume <session-id> --format json "Continue the work"
mythic chat --workspace ./my-project --resume <session-id>
mythic tui --workspace ./my-project --resume <session-id>
```

Use `/session` in terminal chat to see its ID. Resume selects the current provider
settings/CLI overrides and restores saved context/token totals; session metadata
is descriptive and never restores credentials. IDs are 32 lowercase hexadecimal
characters. Another workspace cannot load the ID, and another live client cannot
resume it while its lease is held. Close the other client before resuming.

SQLite transactions checkpoint user/assistant/tool messages and turn outcomes
under `MYTHIC_HOME/sessions/<workspace-id>/`. Failed/cancelled turns remain
available. After an abrupt exit, missing tool results become explicit interrupted
diagnostics. Recovery never repeats a tool: inspect actual workspace state before
asking the model to retry an interrupted edit or command.

Exports include selected `context`, the latest `outcome`, and ordered append-only
`events`. `/clear` and `/compact` change selected context and retain full historical
events. The private local database keeps original text; exported data and logs
redact configured/environment credentials, common token forms and URL credentials.
This does not detect every possible secret embedded in arbitrary source text.
POSIX files use mode 600 and session directories mode 700; Windows uses the user's
application-state location and inherited account ACLs, not POSIX mode guarantees.
Managed secondary-agent lifecycle/session integration remains S08, and workspace
core/vector memory migration remains S11.

```sh
mythic tui --workspace ./my-project
```

Default `mythic` also launches the TUI. Setup preserves the existing provider
choice. TUI keyboard/approval/lifecycle polish is tracked separately in S06/S09.
