# `mythic_agent.context` — interface

Context compiler package (roadmap slices 051–060). Assembles model
prompt context from pluggable, workspace-isolated sources under a token
budget. Headless: depends only on `mythic_agent.core` and the stdlib
(`ast`, `subprocess`, `threading`); never on `agents`, `ui` or
`providers`.

## Public entry points

- `ContextCompiler(workspace, config=..., estimator=..., budget_tokens=4000, max_block_tokens=2000, cancel_event=..., redactor=...)`
  — `.add_source(source)`, `.compile(query=None) -> CompiledContext`.
- `ContextBlock(name, content, priority=5, provenance=..., trimmable=True)`
  — priority `<= 0` is mandatory (never dropped).
- `CompiledContext.blocks / .total_tokens / .budget_tokens / .truncated / .dropped / .warnings`.
- `CachedSource(source, ttl_seconds=300.0)` — stale-data guard with `.invalidate()`.
- `TokenEstimator(model="cl100k_base")` — `.backend` is `"tiktoken"` or
  `"heuristic"`; `.count(text)`, `.count_message(role, content)`.
- `BudgetPlanner(estimator).allocate(total, shares)` — largest-remainder;
  always sums to `total`. `truncate_text(text, max_tokens, estimator)`.
- `group_protocol_messages(messages) -> list[MessageGroup]`;
  `truncate_groups(groups, budget, estimator)` — atomic, system always kept.
- `InstructionResolver(workspace).discover()` — instruction files with
  layers `repo`/`dir`; size-capped; malformed/skipped reported in `.warnings`.
- `apply_precedence(system_text, repo=..., dir_files=..., file_directives=...)`
  — precedence `system > repo > dir > file`; conflicts reported, winners win.
- `extract_mentions(query)` / `resolve_mentions(query, workspace)` —
  `@path` resolution; symlink escapes become warnings, never reads.
- `build_corpus(workspace)` / `score_corpus(query, docs)` / `select_files(...)` —
  deterministic tf-idf, no embeddings dependency.
- `extract_symbols(source)` / `index_workspace(workspace)` /
  `rank_by_symbol_mentions(query, index)` / `select_by_symbols(...)` — stdlib `ast`.
- `build_import_graph(workspace)` / `related_modules(graph, seed, depth)` /
  `select_related(seed, workspace, ...)` — importers + importees, local only.
- `collect_git_diff(workspace)` — staged/unstaged hunks; non-git dirs yield
  `is_git_repo=False` + warning.

## Agent integration (opt-in)

Both are inert unless the `context_compiler_enabled` runtime setting is
true (default false, declared in `mythic_agent/data/runtime_defaults.yaml`):

- `instruction_context_block(config, workspace) -> str` — called from
  `Agent.rebuild_system_prompt`; appends merged repo/dir instructions.
- `prompt_file_context(config, workspace, query, cancel_event=..., redactor=...) -> str` —
  called from `Agent._compile_prompt_context` inside `_run_turn`; compiles
  @-mentions, semantic/symbol/dependency file selection and git-diff hunks
  inside `FILE_CONTEXT_BUDGET_TOKENS` (2000).

All block content passes through `SecretRedactor` before reaching the
prompt. A failing source degrades to a warning; compilation failure
degrades to no extra context — never a broken turn.

## Invariants

- Cross-workspace isolation: every source receives the canonical
  workspace root; all reads go through `assert_within_workspace`.
- Cancellation: `threading.Event` → `ContextCompilationCancelled`.
- Determinism: scoring, allocation and ordering are stable across runs.
- No network, no provider calls, no writes outside the workspace.
