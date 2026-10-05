# Development roadmap and continuous implementation

Date: 2026-10-04. Starting revision: `e197deffcd34061c8f1c813186046c3b61eeada1`.
Branch: `development`.

## Authorization and intent

Volmarr requested a complete roadmap, bug fixes, robustness improvements, and
continued development of this CLI coding harness for humans and AI agents. He
explicitly requested completing and pushing each slice, then automatically
continuing to the next slice. This authorizes implementation and ordinary pushes
to `development` after documentation and verification. Do not request approval
again for this work. Destructive actions outside this scope still require consent.

## Orientation and findings

Read `TODO.md` (empty), `RULES.AI.md`, README, historical audit/refactor proposals,
and the current entry points, configuration, event bus, agent loop, tools, memory,
and UI imports. Historical audits contain inferred files that do not exist; use
the actual source and new regression tests as evidence.

Confirmed by source inspection:

- `Agent.chat()` only calls the provider inside the `len(messages) > 100` branch.
  New conversations cannot execute their normal first turn.
- Tool calls are appended as SDK objects alongside dictionaries, breaking
  consumers that assume dictionary messages. Text and tool calls are also added
  as two assistant messages instead of one protocol message.
- Tools receive `tui_app=None` from the runtime, bypassing command approval.
- `/undo` executes `git reset --hard HEAD~1`, affecting unrelated changes/history.
- File tools allow traversal and absolute paths; file writes make implicit Git
  commits and can commit unrelated staged changes.
- The CLI eagerly imports the TUI and offers no implemented machine-readable run
  mode or terminal chat loop despite unused prompt-toolkit scaffolding.
- All installations require speech, Torch, database, and UI packages.
- Config writes use one predictable temporary name; migration rewrites settings
  while reading. Default config version and migration target disagree.
- Agent memory is keyed only by agent name, so distinct workspaces share memory.
- Retries include permanent errors; loop counters reset and do not terminate.
- Shutdown uses queued sentinels without interrupting active HTTP/backoff/tools.
- Root `test_*.py` files include interactive experiments and import-time app runs;
  they are not a safe automated test suite. Preserve them as historical material.
- There is no CI workflow, maintained architecture map, or actionable backlog.

These are findings, not claims of reproduced failures or finished repairs.

## Work order

Publish `ROADMAP.md`, `ARCHITECTURE.md`, and actionable `TODO.md` before changing
code. Execute S01 onward in dependency order. Before each slice, publish a short
work order describing owners, target files, invariants, and regression gates.
After each slice: review, test, update progress, commit, push, verify the remote
revision, and proceed. Never skip a failed gate or mark planned work complete.

## Constraints

Keep the Viking identity and existing interfaces where practical. Preserve user
files, customized prompts, credentials, and Git history. Use dynamic paths and
internal APIs. Do not delete historical scripts or modules. Optional integrations
must not prevent the core harness from working. Avoid provider charges during
development: use mock clients or local protocol fixtures for mandatory gates.
Record actual platform evidence; do not claim mobile/native support without it.

## Owning files and acceptance

The slice ownership, file scope, dependency order, and definition of done are in
`ROADMAP.md`. Progress and the next concrete task are in `TODO.md`; receipts are
in `docs/development/PROGRESS.md`. The roadmap is complete only when its core
release gates are fulfilled, all required work is pushed, and remaining optional
integrations and external validation limits are accurately stated.
