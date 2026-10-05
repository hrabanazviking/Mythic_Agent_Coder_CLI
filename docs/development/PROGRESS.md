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
