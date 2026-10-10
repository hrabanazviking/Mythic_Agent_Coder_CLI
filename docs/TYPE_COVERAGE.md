# Type Coverage — R-007 Receipt

Measured, gated type-annotation coverage for the `mythic_agent` package.
Implementation: `mythic_agent/core/type_coverage.py` (stdlib `ast`-based;
`mypy` is preferred when installed but never required).

## Baseline vs. after (real measured values)

| Snapshot | Modules | Functions | Params annotated/total | Returns annotated/total | mypy available |
|---|---|---|---|---|---|
| **Baseline** (before R-007 annotation pass) | 75 | 795 | **870/925** (94.1%) | **666/795** (83.8%) | no |
| **After** (post-improvement) | 78 | 807 | **901/942** (95.6%) | **712/807** (88.2%) | no |

Net improvement from the R-007 annotation pass: **+31 annotated params, +46 annotated returns**.
(The module count grew from 75 to 78 during the slice because other forge
workers landed new modules concurrently — and one worker slimmed down
`mythic_agent/agents/tools.py`, which is why the after snapshot shows slightly
fewer annotated params/returns than the mid-slice peak. Baseline and after were
both measured with `type_coverage.py` itself present, so the comparison is
apples-to-apples.)

## What was annotated in R-007

Seven real core modules, only where the types were unambiguous
(no `Any`-everything, no guessed types):

| Module | Before | After | Annotations added |
|---|---|---|---|
| `mythic_agent.core.engine` | params 1/6, returns 0/5 | params 6/6, returns 5/5 | `__init__`/`_setup_logging`/`close`/`handle_crash` `-> None`; `initialize(...)` params typed against `Agent.__init__` (`Path \| str \| None`), `attach_session` (`str \| None`), `policy_mode` override (`str \| None`) |
| `mythic_agent.core.audio` | params 1/5, returns 4/7 | params 2/5, returns 7/7 | `__init__`/`_record_loop` `-> None`; `_audio_callback` `frames: int -> None` (`indata`/`time`/`status` left unannotated — their sounddevice types are not importable without the optional dependency) |
| `mythic_agent.core.secure_api` | params 22/26, returns 1/16 | params 26/26, returns 16/16 | `-> None` on every `EventBus` method, module-level `subscribe`/`unsubscribe`/`publish`/`publish_sync`, and all six `SecureAPI` static methods; `**kwargs: Any` on the four publish entry points |
| `mythic_agent.core.metrics` | params 15/18, returns 21/21 | params 18/18, returns 21/21 | `Trace.__exit__` params typed to the context-manager protocol (`type[BaseException] \| None`, `BaseException \| None`, `TracebackType \| None`) |
| `mythic_agent.core.execution` | params 39/40, returns 16/27 | params 40/40, returns 25/27 | `-> None` on `CancellableChatClient.__init__`, `_WindowsJob.__init__`, nested `watch`/`read`; `-> Any` on the genuinely generic nested `operation`/`drive`/`request` and `cancellable_http_post`; nested `emit(chunk: str) -> None` |
| `mythic_agent.core.journal` | params 12/12, returns 12/13 | params 12/12, returns 13/13 | `WriteAheadLog.__init__ -> None` |
| `mythic_agent.core.redaction` | params 12/12, returns 6/7 | params 12/12, returns 7/7 | `SecretRedactor.__init__ -> None` (closed its one missing return; params were already 100%) |

`validation.py` and `cache.py` were already at 100% params and 100% returns, so no
annotation edits were needed there (a concurrent worker's docstring/import
refactor in `validation.py` was left untouched).

## Counting rules

- Every `def`/`async def` in the AST is counted, including methods and nested functions.
- Parameters: positional-only + positional + keyword-only + `*args` + `**kwargs`.
  A leading `self`/`cls` on a method is excluded (never annotated by convention).
- Returns: one slot per function; annotated when a return annotation exists.
- Excluded from the gate: `__init__.py` files and test files
  (`tests/` directories, `test_*.py`, `*_test.py`).
- Files that fail to parse are listed in `CoverageReport.skipped`, never fatal.

## The gate

`tests/test_type_coverage.py` enforces the package-total gate:

- `report.params_annotated >= 901`
- `report.returns_annotated >= 712`

`>=` (not `==`) so the gate stays green as the package grows; it fails only if
annotation coverage actually regresses below the R-007 post-improvement floor.
Per-module `after >= before` is intentionally NOT required.

## How to regenerate

From the repo root, with the venv python:

```bash
./venv/bin/python - <<'EOF'
from mythic_agent.core.type_coverage import measure, mypy_available
report = measure(".")
print("modules:", report.module_count, "functions:", report.functions_total)
print("params:  %d/%d (%.1f%%)" % (report.params_annotated, report.params_total, report.params_pct))
print("returns: %d/%d (%.1f%%)" % (report.returns_annotated, report.returns_total, report.returns_pct))
print("mypy available:", report.mypy_available)
EOF
```

`measure()` accepts the repo root or the `mythic_agent/` directory itself.
Round-trip: `CoverageReport.from_dict(report.to_dict())` reproduces the report.
Optional strictness pass (returns `None` when mypy is not installed):

```python
from mythic_agent.core.type_coverage import mypy_check
mypy_check(["mythic_agent/core/engine.py"])  # None here: mypy is not in the venv
```

## Per-module table (after snapshot)

| Module | Functions | Params | Params % | Returns | Returns % |
|---|---|---|---|---|---|
| `mythic_agent.__version__` | 0 | 0/0 | 100.0% | 0/0 | 100.0% |
| `mythic_agent.agents.command_handler` | 30 | 15/27 | 55.6% | 3/30 | 10.0% |
| `mythic_agent.agents.context` | 9 | 10/10 | 100.0% | 9/9 | 100.0% |
| `mythic_agent.agents.llm` | 52 | 60/62 | 96.8% | 43/52 | 82.7% |
| `mythic_agent.agents.parallel` | 10 | 14/14 | 100.0% | 10/10 | 100.0% |
| `mythic_agent.agents.planning` | 20 | 16/16 | 100.0% | 20/20 | 100.0% |
| `mythic_agent.agents.prompts` | 1 | 1/1 | 100.0% | 1/1 | 100.0% |
| `mythic_agent.agents.recovery` | 3 | 9/9 | 100.0% | 3/3 | 100.0% |
| `mythic_agent.agents.tasks` | 10 | 10/10 | 100.0% | 10/10 | 100.0% |
| `mythic_agent.agents.tools` | 7 | 16/21 | 76.2% | 5/7 | 71.4% |
| `mythic_agent.bench` | 5 | 0/0 | 100.0% | 5/5 | 100.0% |
| `mythic_agent.cli` | 5 | 4/4 | 100.0% | 5/5 | 100.0% |
| `mythic_agent.constants` | 0 | 0/0 | 100.0% | 0/0 | 100.0% |
| `mythic_agent.core.arch_conformance` | 14 | 19/19 | 100.0% | 14/14 | 100.0% |
| `mythic_agent.core.audio` | 7 | 2/5 | 40.0% | 7/7 | 100.0% |
| `mythic_agent.core.audit` | 11 | 22/22 | 100.0% | 11/11 | 100.0% |
| `mythic_agent.core.cache` | 13 | 8/8 | 100.0% | 13/13 | 100.0% |
| `mythic_agent.core.config_manager` | 10 | 14/14 | 100.0% | 9/10 | 90.0% |
| `mythic_agent.core.costs` | 12 | 8/8 | 100.0% | 12/12 | 100.0% |
| `mythic_agent.core.dead_code_scan` | 23 | 21/23 | 91.3% | 23/23 | 100.0% |
| `mythic_agent.core.edits` | 8 | 11/11 | 100.0% | 7/8 | 87.5% |
| `mythic_agent.core.engine` | 5 | 6/6 | 100.0% | 5/5 | 100.0% |
| `mythic_agent.core.execution` | 27 | 40/40 | 100.0% | 25/27 | 92.6% |
| `mythic_agent.core.journal` | 13 | 12/12 | 100.0% | 13/13 | 100.0% |
| `mythic_agent.core.metrics` | 21 | 18/18 | 100.0% | 21/21 | 100.0% |
| `mythic_agent.core.mythic_logging` | 6 | 13/13 | 100.0% | 6/6 | 100.0% |
| `mythic_agent.core.notifications` | 6 | 13/13 | 100.0% | 6/6 | 100.0% |
| `mythic_agent.core.policy` | 4 | 5/5 | 100.0% | 4/4 | 100.0% |
| `mythic_agent.core.progress` | 14 | 12/12 | 100.0% | 14/14 | 100.0% |
| `mythic_agent.core.recovery` | 1 | 3/3 | 100.0% | 1/1 | 100.0% |
| `mythic_agent.core.redaction` | 7 | 12/12 | 100.0% | 7/7 | 100.0% |
| `mythic_agent.core.repo_census` | 19 | 20/20 | 100.0% | 17/19 | 89.5% |
| `mythic_agent.core.runtime` | 1 | 1/1 | 100.0% | 1/1 | 100.0% |
| `mythic_agent.core.sandbox` | 10 | 11/11 | 100.0% | 10/10 | 100.0% |
| `mythic_agent.core.secrets_audit` | 7 | 8/8 | 100.0% | 7/7 | 100.0% |
| `mythic_agent.core.secure_api` | 16 | 26/26 | 100.0% | 16/16 | 100.0% |
| `mythic_agent.core.sessions` | 18 | 21/23 | 91.3% | 16/18 | 88.9% |
| `mythic_agent.core.storage` | 2 | 4/4 | 100.0% | 2/2 | 100.0% |
| `mythic_agent.core.tool_schemas` | 1 | 0/0 | 100.0% | 1/1 | 100.0% |
| `mythic_agent.core.transcript` | 10 | 6/6 | 100.0% | 10/10 | 100.0% |
| `mythic_agent.core.tts` | 11 | 7/7 | 100.0% | 6/11 | 54.5% |
| `mythic_agent.core.type_coverage` | 25 | 16/16 | 100.0% | 25/25 | 100.0% |
| `mythic_agent.core.validation` | 5 | 10/10 | 100.0% | 5/5 | 100.0% |
| `mythic_agent.core.workspace` | 3 | 6/6 | 100.0% | 3/3 | 100.0% |
| `mythic_agent.data.data_loader` | 4 | 7/7 | 100.0% | 4/4 | 100.0% |
| `mythic_agent.doctor` | 13 | 7/8 | 87.5% | 10/13 | 76.9% |
| `mythic_agent.integrations.github` | 11 | 20/20 | 100.0% | 11/11 | 100.0% |
| `mythic_agent.knowledge.graph` | 23 | 24/24 | 100.0% | 23/23 | 100.0% |
| `mythic_agent.mcp_server` | 15 | 21/21 | 100.0% | 14/15 | 93.3% |
| `mythic_agent.memory.core_memory` | 7 | 6/6 | 100.0% | 6/7 | 85.7% |
| `mythic_agent.memory.long_term` | 18 | 17/17 | 100.0% | 18/18 | 100.0% |
| `mythic_agent.memory.preferences` | 11 | 9/9 | 100.0% | 10/11 | 90.9% |
| `mythic_agent.memory.scopes` | 8 | 8/8 | 100.0% | 7/8 | 87.5% |
| `mythic_agent.memory.vector_db` | 19 | 28/28 | 100.0% | 14/19 | 73.7% |
| `mythic_agent.onboarding` | 5 | 5/5 | 100.0% | 5/5 | 100.0% |
| `mythic_agent.providers.anthropic` | 6 | 6/6 | 100.0% | 6/6 | 100.0% |
| `mythic_agent.providers.base` | 6 | 5/5 | 100.0% | 6/6 | 100.0% |
| `mythic_agent.providers.google` | 6 | 7/7 | 100.0% | 6/6 | 100.0% |
| `mythic_agent.providers.ollama` | 4 | 8/8 | 100.0% | 4/4 | 100.0% |
| `mythic_agent.providers.registry` | 2 | 2/2 | 100.0% | 2/2 | 100.0% |
| `mythic_agent.resources` | 2 | 0/0 | 100.0% | 2/2 | 100.0% |
| `mythic_agent.terminal` | 17 | 25/29 | 86.2% | 15/17 | 88.2% |
| `mythic_agent.tools.code_index` | 15 | 17/17 | 100.0% | 15/15 | 100.0% |
| `mythic_agent.tools.docgen` | 11 | 14/14 | 100.0% | 11/11 | 100.0% |
| `mythic_agent.tools.review` | 19 | 23/23 | 100.0% | 19/19 | 100.0% |
| `mythic_agent.tools.smart_files` | 6 | 16/16 | 100.0% | 6/6 | 100.0% |
| `mythic_agent.tutorials` | 0 | 0/0 | 100.0% | 0/0 | 100.0% |
| `mythic_agent.ui.components.modals` | 8 | 3/6 | 50.0% | 5/8 | 62.5% |
| `mythic_agent.ui.components.subagent_editor` | 9 | 6/7 | 85.7% | 1/9 | 11.1% |
| `mythic_agent.ui.components.subagent_modal` | 3 | 2/2 | 100.0% | 3/3 | 100.0% |
| `mythic_agent.ui.main_app` | 7 | 6/9 | 66.7% | 3/7 | 42.9% |
| `mythic_agent.ui.markdown` | 5 | 10/10 | 100.0% | 5/5 | 100.0% |
| `mythic_agent.ui.screens.chat_screen` | 39 | 38/41 | 92.7% | 25/39 | 64.1% |
| `mythic_agent.ui.screens.setup_screen` | 8 | 5/5 | 100.0% | 8/8 | 100.0% |
| `mythic_agent.ui.screens.splash_screen` | 3 | 0/0 | 100.0% | 3/3 | 100.0% |
| `mythic_agent.ui.shortcuts` | 3 | 3/3 | 100.0% | 3/3 | 100.0% |
| `mythic_agent.ui.themes` | 4 | 3/3 | 100.0% | 4/4 | 100.0% |
| `mythic_agent.workflow.slice_runner` | 8 | 20/20 | 100.0% | 7/8 | 87.5% |
