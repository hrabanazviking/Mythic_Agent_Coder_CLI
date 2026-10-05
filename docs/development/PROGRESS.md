# Development progress

## Roadmap foundation — 2026-10-04

- Baseline: `e197deffcd34061c8f1c813186046c3b61eeada1`, development.
- Read the current source, empty TODO, rules, README and historical proposals.
- Published full roadmap, actual architecture, scope/authorization and backlog.
- Implementation and regression evidence are still pending.
- Remote receipts are recorded in the following work order after push verification.

## Slice receipt requirements

Record intent/work-order revision, changed behavior, actual commands/results,
remaining limitations, implementation revision and verified remote/CI evidence.
Do not equate local tests with real-provider or physical cross-platform testing.

## S01 — lightweight installation and automated baseline

- Work order: `9ef73da290f1157a6f23762d33c2334c0fe0be0c`, pushed and remote-verified.
- Core dependencies now exclude TUI, Torch, speech, database and MCP packages;
  capabilities are retained as extras. Help/version import no settings/runtime.
- Built wheels include 9 persona Markdown profiles, existing character art and
  engineering protocol; UI/resource access works independently of working directory.
- `python -m pytest`: 3 passed on local Linux/Python 3.13.13.
- `python -m build`: wheel and sdist built successfully.
- Installed core wheel in a fresh environment; entry-point help/version and resource
  checks passed outside checkout; Textual and Torch verified absent.
- Added Linux/macOS/Windows × Python 3.10/3.13 CI. Hosted results pending push.
- This slice does not claim repaired chat execution; S02 owns that critical fix.

### S01 portability follow-up

- Hosted run `37258467107`: Linux/macOS Python 3.13 passed all gates. Windows
  failed checkout on a historical filename colon; Python 3.10 failed resolution
  because textual-image 0.13+ requires Python 3.12.
- Preserved the historical document with a Windows-compatible name and selected
  textual-image 0.12 for Python <3.12. Repair matrix pending its push.

## S02 — shared runtime repair

- Work order: `12af961a9989e712df101d9eb50256eef9ea18b1`, pushed and remote-verified.
- Provider requests now run for ordinary first turns; final text is returned.
- Assistant text+calls are one dictionary message; every tool has a matching result.
  Invalid JSON/unknown tools/operation exceptions no longer break result ordering.
- History/registry consumers use serializable snapshots. Turns serialize separately
  from state locks; events/retrieval/provider/tools do not run under state locks.
- No automatic message-count deletion. Manual compaction archives complete earlier
  turns; clearing during a tool turn is deferred until completion.
- Added typed outcomes, configurable finite tool/retry budgets, transient-status
  retry classification and cancellation at loop/retry boundaries.
- Local `python -m pytest`: 24 passed. `python -m build`: wheel+sdist passed.
- Tests cover real SDK message normalization with fake responses, HTTP status
  classification, multiple tools, concurrent turns, reentrant history callbacks,
  history preservation, budgets, cancellation/recovery and failure outcomes.
- Active I/O cancellation, provider capability/token settings, policies and
  durable full sessions remain S05–S07 work. No live-provider claim.

### Hosted receipts and urgent main repair

- S01 portability repair `1abaab0c43a2041557fd1e3f538c87eb7c004d87` passed all six
  jobs in hosted run `37258887547` (Linux/macOS/Windows, Python 3.10 and 3.13).
- S02 `8fe242fe408b8a15634555b862b26d95a535ef47` passed all six jobs in hosted
  run `37258957751`, including 24 tests, builds and installed-wheel smoke checks.
- User's urgent screenshot showed main pulling the invalid colon filename.
  Main's merged tree predated the development repair. Reproduced with a new
  path regression check; preserved identical document bytes and pushed the main
  repair `cb7d19b365064153f6f57a8acfa013d2cea9f98b`. Remote main was verified.
  Four local main tests passed; main hosted run `37259244508` pending.
- Added the tracked Windows-path regression check to development and enabled
  main CI. User's physical GitHub Desktop retry is not claimed as tested.

- Main repair run `37259244508` passed all six hosted platform/Python jobs,
  including Windows checkout, tests, distributions and installed-wheel checks.

## S03 — contained atomic edits and journal undo

- Work order: `4742e21c3c6d5680adf91f6cc31523aa733cddb4`, pushed and remote-verified.
- Explicit workspace wins over stored settings; default is the launching project.
- File schemas/types are validated; traversal/foreign-drive/symlink escapes and
  Git metadata writes are refused. Full file/search/command outputs are preserved.
- File edits no longer auto-stage/commit. Atomic writes record before/after bytes
  and modes in a workspace-scoped private SQLite journal protected by file locks.
- Journal recovery reconciles prepared edit/undo receipts without erasing divergent
  work. Undo checks current content/mode and preserves HEAD/index/unrelated files.
- Updated slash undo, MCP workspace resolver and UI/README descriptions.
- Local `python -m pytest`: 48 passed; wheel and sdist builds passed. Tests include
  dirty/staged Git preservation, atomic failure, prepared-receipt recovery,
  concurrent journals, stale undo, permissions, path escapes and full content.
- Windows symlink/POSIX mode tests state platform limitations. Shell execution
  remains a powerful non-sandboxed operation pending S06 policy/process work.

- S03 revision `80afc0cbd492fe6f843b28af6b3e6ec584b5f259` passed all six hosted
  jobs in run `37259636657` (48 tests, builds and installed-core smoke checks).

## S04 — human terminal chat and machine task runs

- Work order: `323ef28db40a22f2862e21eb87cd0192ad3514c4`, pushed and remote-verified.
- Added `mythic chat`, `mythic run` and explicit `mythic tui`; default remains TUI.
  Core works without optional UI/speech dependencies. Help/version stay import-light.
- Run supports prompt/stdin, workspace/model/endpoint overrides, plain/JSON/JSONL
  results and documented exits. Chat supports repeated turns and core slash commands.
- CLI attaches explicit read-only/ask/trusted tool policy. Noninteractive approval
  never blocks; denied tools return structured approval-required status and exit 3.
- `MYTHIC_HOME` isolates state and skips legacy-home import. Invocation provider
  overrides are temporary; explicit human `/model` remains a saved preference.
- KeyboardInterrupt closes pending tool-call/result groups so another turn works.
- Local maintained suite: 61 passed. Built wheel+sdist. Installed the core wheel
  in an independent environment and ran all 12 CLI HTTP/subprocess tests from
  outside checkout; Textual verified absent.
- HTTP fixtures ran only on localhost and exercised actual SDK requests, tool
  execution/refusal, stdin, output parsing, chat clear/add/undo, auth failure, and
  settings preservation. No hosted-provider credentials or charges.
- Versioned result/exit contracts and examples are in `docs/CLI.md`. Durable
  resume, unified TUI/direct/MCP policy, active process stop and streamed HTTP are
  separate S05–S07/S13 work; current JSONL events are per provider response.

### S04 hosted Windows approval repair

- Run `37260418519`: all four Linux/macOS jobs passed; Windows jobs exposed
  inherited console stdin with captured output and EOF during approval. The
  failure was an incorrect completed/exit-0 result, not a file mutation.
- Approval now requires interactive stdin and prompt stderr; EOF/closed input
  yields a recorded denial. Added deterministic regressions for both cases.
- Integrated the user's main-to-development merge (`4329310`) with a normal merge
  before pushing, preserving their commits and the urgent main repair record.

- Final S04 repair revision `2f5570a3c6c43f218a3408844bea07c61aed9d38` passed
  all six hosted jobs in run `37260742450`. Local suite: 63 passed; wheel+sdist
  passed; installed core wheel: 14 CLI tests passed outside checkout.
- S05 work order is published. Temporary probes reproduced destructive config
  read migration/custom-prompt healing and malformed version fallback; these are
  pending repairs, not finished implementation.

## S05 — durable sessions and configuration recovery

- Configuration reads no longer rewrite files or replace untagged custom prompts.
  Known fields normalize in memory; unknown data/invalid fields stay recoverable.
  Current/default schema agree at 3; defaults are packaged YAML. Explicit root,
  `MYTHIC_HOME` and temporary environment/CLI overrides are documented.
- Explicit settings saves use unique private temporary files, fsync/atomic replace
  and process locks. Invalid/old originals get recoverable byte-identical backups.
  Failed saves preserve previous settings and UI/model callers no longer claim success.
- Added workspace-scoped versioned SQLite session service with exclusive leases,
  protocol validation and transactional context/outcome/transcript checkpoints.
  Run/chat/primary TUI attach; CLI can list/export/resume. Failed/cancelled turns
  survive restart. Interrupted missing tool results become diagnostic results,
  without rerunning edits or commands that may already have completed.
- Context clear/compaction retain historical transcript events. Failed context
  persistence keeps live/durable context intact. Workspace switches start a new
  session; direct workspace mutation is refused before provider/tool work.
- Configured/environment credentials, token forms and URL credentials are redacted
  from exports/CLI events/logs/crash reports. Raw local transcripts keep original
  text in private application state. This is not an arbitrary-source secret scanner.
- Local suite: 113 passed; wheel+sdist builds passed. All 113 tests also passed
  against the installed core wheel outside checkout, with Textual verified absent.
- New gates cover malformed config/transcripts, custom prompts, atomic failure,
  process-concurrent saves, leases, abrupt exit/recovery, two-invocation resume,
  tool completion preservation, list/export, failures/cancellation, workspace
  rotation/isolation, complete history and diagnostic/export redaction.
- Hosted receipt pending the implementation push. Managed secondary-agent session
  lifecycle remains S08; workspace core/vector memory remains S11. All provider
  fixtures were local/fake; no live-provider claim or credential provisioning.
