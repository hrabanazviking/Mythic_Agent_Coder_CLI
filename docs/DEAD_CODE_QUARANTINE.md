# Dead-Code Quarantine

Snapshot of dead-code findings for the `mythic_agent/` package,
taken 2026-10-10. Every item below was produced by a
real scan (`mythic_agent.core.dead_code_scan.scan`); nothing here is
invented. Items are quarantined (recorded, not deleted) unless noted.

## Scan parameters

- Scanner: stdlib-`ast` based, `mythic_agent/core/dead_code_scan.py`
  (`vulture` is not installed in the forge venv and offline installs
  are not permitted, so the scanner is dependency-free).
- Root scanned: `mythic_agent/` (85 modules). `tests/`, `docs/`, and
  generated `__pycache__/` are NOT scanned.
- Definition = a symbol is *dead* when it is defined in the package
  but never referenced anywhere else in the package.
- References counted: `Name` loads, attribute accesses
  (`obj.method` marks `method`), decorators, base classes, keyword
  argument names, `getattr(obj, "name")` string arguments,
  identifier-like string constants, and `from m import X` imports
  (the source name `X` counts as referenced).
- Whitelist (never reported): dunder names; names listed in a
  module's `__all__`; every export of `__init__.py` files;
  console-script entry points from `pyproject.toml`
  (`mythic_agent.cli:main`, `mythic_agent.mcp_server:main`);
  `main`/`main_cli`/`run_main` hooks; `register_*` plugin entry
  points; any decorated function (decorators receive the function
  at definition time: `@mcp.tool()`, `@_rule`, `@health_check`,
  `@property`, ...); AST `visit_*` methods and `visit_*` aliases;
  Textual framework hooks (`on_*`, `action_*`, `watch_*`,
  `validate_*`, `render_*`, `compose`) and framework class
  variables (`CSS`, `BINDINGS`, `DEFAULT_CSS`, `DEFAULT_THEME`,
  ctypes `_fields_`); `from __future__ import annotations`.
- Caveats: docstrings are not parsed for references (except
  identifier-like string constants); dynamically computed names
  (`getattr` with a non-literal) are not tracked; only
  module/class-level assignments count as variables (function
  locals are excluded).

## Findings: 76 item(s)

| file | line | name | kind |
| ---- | ---- | ---- | ---- |
| `mythic_agent/agents/context.py` | 69 | `ContextBuilder` | class |
| `mythic_agent/agents/context.py` | 101 | `add_system` | method |
| `mythic_agent/agents/context.py` | 105 | `add_tool_pair` | method |
| `mythic_agent/agents/parallel.py` | 81 | `ParallelExecutor` | class |
| `mythic_agent/agents/parallel.py` | 124 | `execute_all` | method |
| `mythic_agent/agents/planning.py` | 140 | `Planner` | class |
| `mythic_agent/agents/planning.py` | 148 | `create_plan` | method |
| `mythic_agent/agents/planning.py` | 175 | `next_step` | method |
| `mythic_agent/agents/planning.py` | 184 | `mark_done` | method |
| `mythic_agent/agents/planning.py` | 193 | `mark_failed` | method |
| `mythic_agent/agents/prompts.py` | 59 | `FEW_SHOT_EXAMPLES` | variable |
| `mythic_agent/agents/prompts.py` | 184 | `for_provider` | function |
| `mythic_agent/agents/tasks.py` | 58 | `AgentBudgets` | class |
| `mythic_agent/agents/tasks.py` | 61 | `max_turns` | variable |
| `mythic_agent/agents/tasks.py` | 62 | `max_tool_calls` | variable |
| `mythic_agent/agents/tasks.py` | 63 | `max_concurrent` | variable |
| `mythic_agent/agents/tasks.py` | 113 | `list_all` | method |
| `mythic_agent/agents/tasks.py` | 118 | `list_by_parent` | method |
| `mythic_agent/agents/tasks.py` | 130 | `update_state` | method |
| `mythic_agent/agents/tools.py` | 61 | `auto_git_commit` | function |
| `mythic_agent/agents/tools.py` | 83 | `validate_tool_arguments` | function |
| `mythic_agent/cli.py` | 44 | `print_help` | function |
| `mythic_agent/core/audit.py` | 57 | `AuditLog` | class |
| `mythic_agent/core/audit.py` | 79 | `log_tool_execution` | method |
| `mythic_agent/core/audit.py` | 82 | `log_file_write` | method |
| `mythic_agent/core/audit.py` | 85 | `log_permission_decision` | method |
| `mythic_agent/core/dead_code_scan.py` | 343 | `write_quarantine` | function |
| `mythic_agent/core/dead_code_scan.py` | 355 | `load_quarantine` | function |
| `mythic_agent/core/execution.py` | 158 | `raw_output` | variable |
| `mythic_agent/core/journal.py` | 46 | `CorruptJournalLine` | class |
| `mythic_agent/core/journal.py` | 150 | `has_pending` | method |
| `mythic_agent/core/journal.py` | 165 | `discard` | method |
| `mythic_agent/core/metrics.py` | 57 | `inc` | method |
| `mythic_agent/core/metrics.py` | 233 | `save` | method |
| `mythic_agent/core/mythic_logging.py` | 122 | `get_logger` | function |
| `mythic_agent/core/notifications.py` | 111 | `notify_all` | function |
| `mythic_agent/core/sandbox.py` | 75 | `Sandbox` | class |
| `mythic_agent/core/sandbox.py` | 175 | `dry_run` | method |
| `mythic_agent/core/secrets_audit.py` | 105 | `has_secrets` | function |
| `mythic_agent/core/secrets_audit.py` | 133 | `audit_report` | function |
| `mythic_agent/core/secrets_audit.py` | 148 | `scan_mapping` | function |
| `mythic_agent/core/transcript.py` | 29 | `BoundedTranscript` | class |
| `mythic_agent/core/transcript.py` | 72 | `get_all` | method |
| `mythic_agent/core/type_coverage.py` | 203 | `module_named` | method |
| `mythic_agent/core/type_coverage.py` | 258 | `measure` | function |
| `mythic_agent/core/type_coverage.py` | 297 | `mypy_check` | function |
| `mythic_agent/data/data_loader.py` | 87 | `data_loader` | variable |
| `mythic_agent/doctor.py` | 45 | `fix_applied` | variable |
| `mythic_agent/integrations/github.py` | 99 | `add_pr_comment` | function |
| `mythic_agent/knowledge/graph.py` | 161 | `explain` | method |
| `mythic_agent/knowledge/graph.py` | 172 | `architecture_summary` | method |
| `mythic_agent/knowledge/graph.py` | 209 | `save` | method |
| `mythic_agent/memory/core_memory.py` | 87 | `save` | method |
| `mythic_agent/memory/long_term.py` | 91 | `forget` | method |
| `mythic_agent/memory/long_term.py` | 163 | `recall` | method |
| `mythic_agent/memory/long_term.py` | 180 | `recall_with_scores` | method |
| `mythic_agent/memory/long_term.py` | 226 | `import_facts` | method |
| `mythic_agent/memory/preferences.py` | 44 | `PreferenceStore` | class |
| `mythic_agent/memory/preferences.py` | 135 | `forget` | method |
| `mythic_agent/memory/preferences.py` | 147 | `suggest` | method |
| `mythic_agent/memory/preferences.py` | 167 | `learn_from_turn` | method |
| `mythic_agent/memory/scopes.py` | 70 | `scoped_agent_key` | function |
| `mythic_agent/memory/vector_db.py` | 107 | `save` | method |
| `mythic_agent/providers/base.py` | 78 | `require_capability` | method |
| `mythic_agent/tools/code_index.py` | 139 | `invalidate` | method |
| `mythic_agent/tools/code_index.py` | 153 | `find_definition` | method |
| `mythic_agent/tools/code_index.py` | 174 | `find_references` | method |
| `mythic_agent/tools/code_index.py` | 196 | `invalidate_stale` | method |
| `mythic_agent/tools/code_index.py` | 217 | `refresh_mtime` | function |
| `mythic_agent/tutorials.py` | 1 | `TUTORIALS` | variable |
| `mythic_agent/ui/main_app.py` | 36 | `SCREENS` | variable |
| `mythic_agent/ui/main_app.py` | 78 | `copy_to_clipboard` | method |
| `mythic_agent/ui/markdown.py` | 27 | `render_markdown` | function |
| `mythic_agent/ui/screens/chat_screen.py` | 62 | `run_tui` | function |
| `mythic_agent/ui/shortcuts.py` | 68 | `effective_shortcuts` | function |
| `mythic_agent/ui/themes.py` | 76 | `to_textual_kwargs` | function |

## Analyst notes (verified by hand)

- `write_quarantine` / `load_quarantine` are flagged by the scanner
  itself: they are this module's public API, exercised externally
  (and by `tests/test_dead_code.py`). Quarantined, not removed.
- Many items are public API surface referenced only from `tests/`
  (which is outside the scan scope) or from external callers, e.g.
  `render_markdown` (tests/test_markdown.py), `for_provider` and
  `FEW_SHOT_EXAMPLES` (tests/test_prompts.py), `auto_git_commit`
  (tests/test_policy.py), `has_pending` / `discard`
  (tests/test_journal.py), `refresh_mtime`
  (tests/test_code_index.py), `scoped_agent_key`
  (tests/test_memory_scopes.py), `to_textual_kwargs`
  (tests/test_themes.py), `raw_output` (read in
  tests/test_execution.py), `validate_tool_arguments` (documented
  legacy-compat entry point, intentionally kept).
- Several items are referenced only inside docstrings / usage
  examples within the package (docstrings are not parsed for
  references): `Sandbox` (doctest in `sandbox.py`), `dry_run`,
  `get_all`, `measure`, `mypy_check`.
- Genuinely unused inside the package (leftovers, quarantined not
  removed): `run_tui`, `print_help`, `effective_shortcuts`,
  `copy_to_clipboard`, `SCREENS`, `TUTORIALS`, the `data_loader`
  singleton, `Planner` and its methods, `ContextBuilder`,
  `ParallelExecutor`, `AgentBudgets`, `AuditLog` and its methods,
  `PreferenceStore`, `KnowledgeGraph.explain` /
  `architecture_summary`, `secrets_audit` helpers,
  `has_secrets` / `audit_report` / `scan_mapping`.

## Removed in this slice (not quarantined)

Two trivially-safe deletions, both private helpers with zero
references anywhere in the repo (verified with repo-wide grep
over `*.py` and `*.md`, excluding this slice's own files):

1. `_timeout_output` — `mythic_agent/agents/tools.py` (was line 83).
   Unused `subprocess.TimeoutExpired` formatter; the timeout paths
   in the file log directly instead.
2. `_use_color` — `mythic_agent/core/progress.py` (was line 18).
   Unused TTY/NO_COLOR helper; `ProgressBar`/`Spinner` never called it.

## Gate

`tests/test_dead_code.py::test_no_new_dead_code_beyond_quarantine`
fails if a future scan finds any dead item not present in
`docs/DEAD_CODE_QUARANTINE.txt` (compared as `(path, name, kind)`
so that line shifts from unrelated edits do not trip the gate).
