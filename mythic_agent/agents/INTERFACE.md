# Agent and tool interfaces

`Agent(project_root=None, name="Primary")` resolves explicit workspace first,
stored workspace second, current directory last. `chat()` uses the core runtime
contracts; `history_snapshot()` returns detached dictionary messages.

`get_agent_tools()` exposes JSON function schemas. `execute_tool(name, arguments,
project_root, tui_app, agent)` validates those schemas and returns complete text
results/errors. File paths must resolve within the workspace; writes cannot target
Git metadata. File write/replace operations use `EditJournal`, preserve permissions,
and do not stage or commit. `auto_git_commit` remains a compatibility callable,
but file tools do not invoke it. `truncate_output` now preserves complete output.

`EditJournal(root).undo()` restores only the last unchanged agent edit, including
an explicitly requested removal of an unchanged agent-created file. It refuses
content/mode conflicts and never alters Git HEAD/index. Journal recovery compares
bytes before choosing a receipt status; it does not rewrite divergent files.

Shell policy and active subprocess cancellation are S06. Workspace containment
does not make shell execution an OS sandbox. Knowledge/GitHub/delegation contracts
are being hardened in their separate roadmap slices.
