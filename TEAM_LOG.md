# TEAM_LOG - team-06

## M-090 Editor bridges lite (pure layer, 2026-11-06)

Built on banked base 2bb48aa (M-089 closure). Roadmap words:
`$EDITOR` round-trip for any file or prompt at any approval
point (the terminal user's oldest right).

### Pure layer (this commit)
- mythic_agent/core/editor_bridge.py: resolve_editor
  (VISUAL first, then EDITOR - the terminal's own
  precedence; whitespace counts as unset; neither set
  refuses naming the remedy, no editor ever guessed;
  the value is split the way a shell splits it, so
  `code --wait` works as written; a malformed value
  raises in the user's own terms), editor_command
  (resolved argv + scratch path), prepare_file_round_trip
  / prepare_prompt_round_trip (SHA-256 anchored; a file
  keeps its own suffix in the scratch name so the
  editor's syntax knowledge applies, a prompt travels
  as .md prose), judge_round_trip (byte-identical =
  unchanged and writes nothing; changed = the new text;
  an emptied FILE refuses - never silently truncated;
  an emptied PROMPT is a cancellation, never sent),
  editor_bridge gate (absent = on, malformed raises),
  shared /editor parser + formatters.
- tests/test_editor_bridge.py: 25 passed. Neighbours
  (editor_bridge + patch_exchange + stash_shelf +
  change_sets + roadmap_slices) 197 passed, run with
  the campaign venv (.venv-hammer; system python3 lacks
  textual and errors the chat-screen neighbour tests -
  environment, not the slice).

### Agent layer (this work, 2026-11-06)
- Agent layer DONE: editor_bridge_status (editor resolved
  honestly from os.environ - None + remedy when unset,
  never raised, never guessed) / set_editor_bridge
  (journal-first editor_bridge_setting_changed, save-
  failure restores the previous value and journals
  editor_bridge_setting_reverted) in
  mythic_agent/agents/llm.py; _editor_bridge_dir mirrors
  _stash_shelf_dir with "editor-bridge"; the real
  round-trip (gate enforced, editor resolved from the
  caller environ, real scratch file under the state
  dir, real editor process via subprocess - a non-zero
  exit raises naming the code and writes nothing,
  judged by the pure layer; a changed FILE lands
  through EditJournal, a changed PROMPT writes no file
  and its text rides the record; session event
  editor_round_trip) as edit_file_in_editor /
  edit_prompt_in_editor.
- Surfaces: /editor on the terminal road (_slash) and
  the TUI road (_handle_editor + dispatch), sharing
  parse_editor_args + the pure formatters; show asserts
  the status gate, on/off use format_setting_change,
  file reports the judged round-trip, prompt is the
  honest no-draft refusal on both surfaces;
  chat_screen help line, full usage entry, and
  system-command routing for /editor.
- tests/test_editor_bridge.py: 49 passed (25 pure +
  24 agent-layer/surface, the round-trips running a
  REAL executable fake editor script). Neighbours
  (editor_bridge + patch_exchange + stash_shelf +
  change_sets + roadmap_slices) 221 passed, run with
  the campaign venv (.venv-hammer).
- Gates: test_arch_conformance passed; test_dead_code
  fails ONLY on the new public method
  mythic_agent/agents/llm.py:edit_prompt_in_editor
  (method) - edit_file_in_editor is called by both
  surfaces and is not flagged. That is the expected
  pre-banking quarantine item (see below), not hidden.
  test_public_api / test_ownership inventory failures
  are the coordinator regen deltas below (live
  PUBLIC_API scan 2915 names vs doc 2890;
  OWNERSHIP 208 modules vs doc 207, the extra module
  being core/editor_bridge.py from the pure layer);
  test_public_api also hit an unrelated PortAudio /
  PulseAudio environment import failure for
  core.audio in this run.

### Still owed before M-090 can bank (coordinator banking deltas ONLY)
- Coordinator banking deltas at closure: catalogue
  S-82 for the editor_bridge setting, config_defaults
  editor_bridge: true, PUBLIC_API + OWNERSHIP regen,
  roadmap flip to 90 done, ledger row.
- Dead-code quarantine entry needed in
  docs/DEAD_CODE_QUARANTINE.txt (coordinator delta -
  do NOT edit it in the team worktree):
  mythic_agent/agents/llm.py:edit_prompt_in_editor (method)
