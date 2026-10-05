# Agents, tools and commands

Runtime turns live in `llm.py`; JSON tool schemas/execution live in `tools.py`;
human slash adapters live in `command_handler.py`. Use the core workspace, edit
journal, runtime settings/outcomes and event APIs. Preserve serializable tool
protocols and keep UI callbacks outside state locks. Do not make file edits into
implicit Git operations. `INTERFACE.md` documents supported entry points.
