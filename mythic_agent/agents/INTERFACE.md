# Agent and tool interfaces

`Agent(project_root=None, name="Primary")` resolves explicit workspace first,
stored workspace second, current directory last. `chat()` uses the core runtime
contracts; `history_snapshot()` returns detached dictionary messages.

`attach_session(store=None, resume=None)` opts an embedding agent into durable
workspace sessions; CLI/primary TUI bootstrap attach automatically. It returns
the session ID and restores validated context/outcome/token count when resumed.
An attached agent holds the process lease until `close()`, which also unsubscribes
history callbacks. `change_workspace(root)` rotates to a new session with only the
system context between turns and preserves the old transcript. Direct root mutation
on an attached agent fails before provider/tool execution. `save_config()` returns
bool; `set_model` raises and restores the live selection if preference save fails.

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
