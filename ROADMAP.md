# Mythic Agent: complete development roadmap

Created 2026-10-04 from revision `e197deff`. Status: implementation in progress.

## Intended experience

Launch Mythic in a repository, converse naturally, inspect its work, approve
operations according to an explicit policy, interrupt it, resume later, and keep
your own Git workflow. An external AI can perform the same work through a stable
CLI/API without a terminal, hidden modals, or ambiguous completion. Local and
hosted OpenAI-compatible models remain configurable. Mythic Engineering and
custom personas add useful structure while the ordinary coding loop stays simple.

The quality bar is a dependable alpha-to-stable coding harness, not a claim that
every provider, platform, or arbitrary generated program is infallible. Voice,
images, PostgreSQL, and character flourishes are optional capabilities. They
cannot obstruct installation, a chat turn, or machine use.

## Execution contract

Execute these slices in order unless new evidence requires a documented change.
Each slice has a work-order document committed and pushed before implementation.
Implement -> targeted regression/integration tests -> appropriate full gates ->
review diff and docs -> record results -> commit -> push `development` -> verify
remote HEAD -> automatically start the next slice. Failed gates must be repaired
before pushing the implementation. Never force-push or erase user work.

Keep `TODO.md` and `docs/development/PROGRESS.md` current. Keep evidence distinct:
source findings, local fake-provider tests, real-provider tests, hosted CI, and
physical platform tests are different claims. A test without external credentials
is a valid core gate; do not quietly spend money or invent live-provider evidence.
If an external dependency blocks one optional gate, document it and continue
independent authorized work. Stop only for a genuine required decision/blocker,
an explicit user stop, or fulfilled acceptance gates.

## Milestone A: trustworthy foundation

### S01 — Reproducible installation and automated baseline

**Owners:** packaging, launch, verification. **Scope:** `pyproject.toml`, `cli.py`,
tests, CI, packaged resources. **Depends:** roadmap publication.

Make a lightweight core install; separate TUI, voice, database, MCP, and developer
extras. Lazy-load optional front ends so help/version never start workers or
import Torch. Define a safe automated test directory while preserving interactive
experiments. Add a platform/Python CI matrix and build/install verification.
Verify personas and the engineering skill are available in built wheels, not
only editable checkouts. Add reproducible developer commands.

**Done:** clean core wheel installs; help/version work outside the repo with no
credentials/UI/audio; imports and resource tests pass; CI runs the maintained suite.

### S02 — Repair the shared conversation runtime

**Owners:** runtime, event bus. **Scope:** `agents/llm.py`, `core/secure_api.py`.
**Depends:** S01.

Fix the first-turn indentation defect. Normalize SDK messages to dictionaries.
Add one assistant message containing both text and tool calls, then one result
per call. Validate malformed arguments and unknown tools without crashing a
worker. Serialize turns; keep subscriber calls and network work outside state
locks. Classify failure clearly. Preserve protocol groups when compacting and
when handling inbox steering. Provide an explicit bounded/cancellable lifecycle.

**Done:** fake-provider first turn, multiple turns, text+tools, tool failures,
reentrant callbacks, and history serialization pass without network credentials.

### S03 — Workspace boundaries, safe edits, and trustworthy undo

**Owners:** workspace/tool services, Git commands. **Scope:** new workspace/edit
services, `agents/tools.py`, command handler. **Depends:** S02.

Resolve the explicit workspace first, then settings/current directory; validate
file tools against it, including symlink escapes and platform path forms. Write
atomically and journal before/after content. Refuse stale undo when the user has
edited the file afterward. Stop implicit Git commits during tool writes. Replace
destructive `/undo` behavior with restoration of the last agent edit only. Match
blocks exactly and reject empty/ambiguous targets. Retain full file/tool outputs
or provide artifact references instead of silent data loss.

**Done:** traversal/symlink tests, edit/replace/undo tests with dirty and staged
user files, and interrupted-write tests pass; Git HEAD/index remain unchanged.

## Milestone B: one harness for humans and machines

### S04 — Terminal chat and noninteractive CLI

**Owners:** launch/interface adapters. **Scope:** `cli.py`, new CLI adapters,
runtime result/events. **Depends:** S02–S03.

Keep the default TUI; add `mythic chat`, `mythic run`, stdin/prompt input,
`--workspace`, endpoint/model selection, and explicit permission mode. Add plain
and versioned JSON/JSONL output with stable success/error/cancelled exits. Handle
EOF, Ctrl+C, empty input, and missing optional packages cleanly. Provide slash
help, clear, model, status, add, stop, and undo through shared command services.

**Done:** subprocess tests exercise a real local fake HTTP provider and tools;
machine stdout parses cleanly; a scripted human loop performs multiple turns.

### S05 — Durable sessions, resume, and robust configuration

**Owners:** persistence/config. **Scope:** new session store, config manager,
CLI and runtime hooks. **Depends:** S04.

Use workspace IDs and session IDs, versioned transcripts, atomic save, and locks.
Resume after restart; list/export sessions; preserve complete raw history and
operation receipts. Support an isolated portable config directory, environment
overrides, validation, additive migrations, private temporary files, and recovery
without silently overwriting corrupt/customized data. Separate secrets from
exported settings/transcripts and ensure logs do not disclose credentials.

**Done:** restart/resume, concurrent save, malformed config/transcript, permission,
workspace isolation, and redaction tests pass; legacy data remains recoverable.

### S06 — Permission policy and cancellable command execution

**Owners:** tools/runtime/adapters. **Scope:** policy service, process runner,
approval UI/CLI adapters. **Depends:** S04–S05.

Wire policy through all tool paths, including GitHub and delegated tools. Offer
documented read-only, interactive approval, and explicitly trusted modes. Machines
must receive a refusal/approval-needed result rather than a hidden prompt. Show
command exit codes, preserve outputs, stream progress, stop active subprocesses
and descendants where supported, and allow cancelling HTTP/retry waits. Explain
the distinction between tool policy/workspace containment and OS sandboxing.

**Done:** denied tools have no effects; CLI/TUI approvals reach the same executor;
timeout/cancel tests leave no test child process; a fresh turn works after stop.

## Milestone C: capable, resilient coding

### S07 — Provider adapters, streaming, and diagnostics

**Owners:** provider/runtime. **Scope:** endpoint adapter, setup, doctor command.
**Depends:** S06.

Explicit timeout/retry/token settings from data; fail fast for auth, bad models,
invalid requests, and missing capabilities. Retry transient errors with cancellable
backoff and a finite budget. Stream text/tool deltas into normalized messages.
Support OpenAI-compatible hosted/local endpoints without dummy remote credentials;
report tool support and model limits. Track actual usage; report unknown cost
instead of inventing blended pricing. Add offline configuration diagnostics and
explicit live connectivity checks. Model discovery must handle provider failure.

**Done:** local HTTP fixtures cover 401/429/5xx, timeouts, streaming fragmented
tool arguments, usage, empty responses, missing keys, and recovery. Live-provider
checks are separately recorded and require available user-authorized credentials.

### S08 — Agent lifecycle and controlled orchestration

**Owners:** orchestration. **Scope:** `AgentManager`, registry, delegation tools.
**Depends:** S05–S07.

Track typed task IDs, queued/running/completed/failed/cancelled status and parent
relationships. Lock registry creation and snapshots; prevent duplicate workers
and recursive delegation cycles. Add configured concurrency/turn/tool budgets,
clear result delivery, task inspection, cancellation, and graceful shutdown.
Ghost context uses serializable snapshots and workspace-scoped identity. Agents
share explicit artifacts; conflicting edits require conflict detection/ownership.

**Done:** simultaneous spawn/delegate/message/cancel tests, nested delegation,
result routing without UI, ghost history, and clean shutdown pass deterministically.

### S09 — Human interface polish and UI stability

**Owners:** Textual interface. **Scope:** screens/components, shared adapters.
**Depends:** S04–S08.

Responsive layout, usable small terminals, keyboard navigation, multiline/paste,
visible workspace/model/task state, readable diffs/tool output, pending input,
and dependable stop/resume/approval behavior. Escape model/file markup. Bind and
unsubscribe events safely on mount/unmount; prevent UI calls from wrong threads.
Handle absent images/audio/clipboard gracefully; setup preserves customized
personas and reports invalid values. Keep Viking theming and optional character
art, while help and empty/error states explain actionable next steps.

**Done:** Textual pilot tests cover startup/setup/chat/tools/approval/stop, rapid
switching, small-terminal layout and optional dependency failures; physical terminal
verification is recorded separately when available.

### S10 — Repository workflows and configurable integrations

**Owners:** commands/integrations. **Scope:** Git/GitHub services, knowledge DB,
data loader. **Depends:** S06–S09.

Centralize command routing across front ends. Preview commit scope, capture Git
errors, respect staged work, allow explicit push, and avoid unsolicited destructive
Git operations. Read project test commands from config or detected manifests.
Honor workspace for all `gh` invocations; never log tokens. Replace machine-specific
DB hosts/users/models with opt-in configuration; enforce read-only SQL at the
database transaction, not a keyword blacklist. Make disabled integrations visible
and portable. Test data ingestion and report unsupported/malformed input clearly.

**Done:** temporary Git repo tests preserve dirty/index state; fake GitHub/DB
adapters verify arguments and refusals; a core install needs no personal services.

### S11 — Useful context, memory, and repository instructions

**Owners:** context/memory. **Scope:** core memory, retrieval, context assembler.
**Depends:** S05, S07, S10.

Load scoped repository instructions and explicitly added files with provenance.
Separate untrusted file/tool contents from user instructions. Assemble context
according to model capability without cutting protocol groups or discarding raw
history. Persist summaries and original references. Isolate memory by workspace,
sanitize agent identifiers, and make retrieval optional/offline-capable. Configure
embedding endpoint/model separately from chat; handle zero/mismatched vectors and
embedding failure without network stalls under state locks. Support clear/export
and explicit legacy migration.

**Done:** cross-workspace isolation, corrupt memory, no-embedding offline recall,
context overflow, repository instruction scope, and full transcript retention pass.

## Milestone D: sustained autonomous work and stable delivery

### S12 — Resumable roadmap/slice execution inside Mythic

**Owners:** workflow runtime. **Scope:** versioned plan/task state, CLI/UI commands.
**Depends:** S08, S10–S11.

Implement the user's desired loop as an explicit feature: select a roadmap task,
record intent, execute, run its checks, review changes, commit/push only according
to configured authorization, verify the push, and continue to the next task.
Persist checkpoints so restart resumes safely. Add pause/stop, failure repair
budgets, approval handoff, task status, and human steering. Completion requires
passing gates and a receipt; a model's claim is insufficient. Failed push cannot
mark a slice shipped. Make dependencies and blocking conditions visible.

**Done:** fake-provider/temporary-Git end-to-end tests run two slices, recover a
failed test/push, pause/resume after restart, and preserve user changes. No feature
claims until the executable workflow passes these tests.

### S13 — Stable machine API, MCP, and extension contracts

**Owners:** external adapters. **Scope:** MCP server, tool registry/API schemas.
**Depends:** S04–S12.

Version JSON request/event/result schemas and document exit codes/capabilities.
Make MCP invoke the same workspace/policy/session/task services, avoiding import
environment mutations or independent memory behavior. Add task status/result,
run/resume/cancel and capabilities tools. Keep stdio protocol clean. Provide
well-scoped extension registration with schema validation and explicit permissions;
do not automatically execute untrusted repository plugins.

**Done:** MCP stdio/client tests and API contract fixtures exercise coding tasks,
session resume, denial, errors and cancellation without loading the TUI.

### S14 — Release readiness, documentation, and measured quality

**Owners:** verification/docs/packaging. **Scope:** CI, release metadata, examples,
README, contributor guide, interface docs. **Depends:** S01–S13.

Run Linux/macOS/Windows CI with supported Python versions; build wheels/sdist and
verify installed entry points/resources. Add bounded fault/soak scenarios for
repeated turns, cancellation, disk failure, malformed tool calls, shutdown and
concurrent agents. Record startup/tool overhead and memory rather than inventing
performance estimates. Publish tutorials for human chat, machine runs, local
providers, permissions, recovery, and autonomous slices; include troubleshooting
and migration notes. Make README claims match measured support. Preserve license
and third-party notices. Add release checklist and versioning policy.

**Done:** required CI/build/runtime/TUI/MCP gates pass on the exact final revision;
the working tree is clean and pushed; docs name any missing external/physical
platform evidence. Optional mobile environments require separate compatibility
research and evidence before support claims.

## Stable harness release gates

- A fresh core installation runs help, a machine coding task, and terminal chat.
- TUI install performs the same task and handles approvals and interruption.
- Edit/undo, workspace isolation, transcript resume, policy, provider errors,
  context protocol, concurrent lifecycle, and machine output have regression tests.
- A two-task slice workflow proves checks, push verification, and resumption.
- Human and machine interfaces share the execution contracts in `ARCHITECTURE.md`.
- Required CI, build, and installed-wheel checks pass; docs and receipts are current.
- No implicit destructive Git behavior, unattended prompts, personal-service
  dependencies, secret-bearing diagnostic output, or known core blocker remains.

## Later growth, after these gates

Prioritize from actual use: richer diff review and patch acceptance; isolated
worktrees/OS sandboxes; editor integrations; provider-specific adapters beyond
OpenAI compatibility; opt-in task collaboration; offline indexing; accessibility
and localized terminal copy; optional voice/image improvements. Each becomes a
separate evidence-based roadmap with its own acceptance gates. Do not substitute
these expansions for finishing the dependable coding harness above.
