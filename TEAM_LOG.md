# TEAM_LOG — team-01 — M-075 Checkpoints v2

Hammer Campaign Wave 1, team-01 (lead). Worktree
`~/mythic-hammer/team-01`, branch `hammer/team-01`,
opened at b58517b (M-074 banked; 74/272). The six
Mythic roles ran as this team's disciplined internal
cycle (agent depth cannot nest further — no sub-crews
were spawned).

## Charter (acceptance)
The roadmap's words: named checkpoints ("before the
auth rework") capturing working tree + session state;
restore is one command, and the journal shows the
whole checkpoint tree.

## Design — settled from the tree before building
Inspected first: `core/journal.py` + `core/sessions.py`
(the existing "checkpoint" is an unnamed, automatic
WAL crash-safety mechanism for the session transcript
— it captures no working tree), `core/edits.py`
(EditJournal: per-edit undo, SQLite under
`MYTHIC_DIR/"edits"/workspace_id`), `core/hunk_review.py`
(M-074: the established slice shape), the Agent session
plumbing (`_checkpoint`, `_session_store`, `export`),
`context/gitdiff.py` (git handled gracefully when
absent — so checkpoints must not require git).

Settled shape:
* **What a checkpoint captures:** the whole working
  tree as a manifest over a content-addressed blob
  store — every in-scope file's bytes (hash, size,
  mode) and symlinks as links (never followed) — plus,
  when a session is attached, the session state
  (messages, status, token count, outcome, read back
  through SessionStore.export). `.git`/`__pycache__`
  and kin (SKIP_DIRS) are out of scope and named so;
  empty directories are not captured (the git rule).
  A file over the 32 MiB cap, an unreadable file, or
  >20000 entries refuses the whole take, naming
  itself — whole or refused, never partial.
* **Where it is stored:** `CheckpointStore` under
  `MYTHIC_DIR/"checkpoints"/workspace_id(root)` —
  the EditJournal's neighbourhood: `checkpoints.sqlite`
  (name UNIQUE, parent_id, manifest, session JSON,
  tree hash; meta table holds the head) + flat `blobs/`
  keyed by sha256 (identical files share one blob).
* **The tree:** each checkpoint's parent is the head
  at take time; restore moves the head to the restored
  checkpoint, so take-after-restore grows a branch.
* **How restore judges a dirty tree:** the tree is
  clean exactly when it matches the head checkpoint's
  manifest. Dirty restore refuses, names up to 5
  changed files (+count of the rest) and the remedy;
  trailing `discard` throws the un-checkpointed
  changes away on purpose, counted in the outcome.
  All blobs are verified present (and re-hashed at
  write time) before/while applying — a damaged
  checkpoint refuses, never half-restores by surprise.
* **Session honesty:** session state is restored only
  into the session it was captured from; a foreign
  session's checkpoint restores the tree and says so,
  naming the captured session.
* **Journal presentation:** `format_checkpoint_tree`
  renders the whole tree (roots first, branches
  indented, head marked `*`) as the `/checkpoint` show
  surface; takes/restores/setting changes are also
  journaled on the session (`checkpoint_created`,
  `checkpoint_restored`, `checkpoints_setting_changed`
  / `..._reverted`) in the M-074 pattern.
* **Gate:** setting `checkpoints`, ships ON;
  `enabled_from_config`/`set_enabled`/`BoolChange`
  mirror M-074 exactly (malformed stored value raises).

## Files changed
* NEW `mythic_agent/core/checkpoints.py` (813 lines):
  pure manifest maths (`capture_manifest`, `tree_hash`,
  `diff_manifests`, `validate_name`,
  `validate_session_snapshot`) + `CheckpointStore`
  (create/get/list/head/plan_restore/restore) + gate +
  `parse_checkpoint_args` + formatters
  (`format_checkpoints`, `format_checkpoint_tree`,
  `format_checkpoint_created`,
  `format_checkpoint_restored`, `format_setting_change`).
* `mythic_agent/agents/llm.py`: Agent
  `checkpoint_status` / `set_checkpoints` (journaled,
  save-failure revert) / `take_checkpoint` /
  `restore_checkpoint` (M-074 pattern, beside
  `apply_hunk_review`).
* `mythic_agent/terminal.py`: `/checkpoint` road +
  help-string entry.
* `mythic_agent/agents/command_handler.py`: dispatch +
  `_handle_checkpoint` (TUI road, same parser/formatters).
* `mythic_agent/ui/screens/chat_screen.py`: help line,
  usage entry, system-command routing list.
* `mythic_agent/data/config_defaults.yaml`:
  `checkpoints: true` (after `hunk_review`).
* NEW `tests/test_checkpoints.py`: 38 tests.
* Logs: `hidden_files/m075-*.log`.

## Verify — counts from on-disk logs (laptop, venv-hammer)
* Targeted: `tests/test_checkpoints.py` — **38 passed**
  (`hidden_files/m075-targeted.log`).
* Dead-code fix re-run: test_checkpoints + test_dead_code
  — **44 passed** (`hidden_files/m075-deadfix.log`).
* Wide bundle (checkpoints, hunk_review, edits, journal,
  journal_integrity, recovery, edit_formats) —
  **216 passed** (`hidden_files/m075-wide.log`).
* Neighbours (hunk_review + sessions) — **75 passed**
  (`hidden_files/m075-neighbours.log`).
* Gate bundle — **7 failed, 34 passed**, every failure
  one of the inventory deltas below
  (`hidden_files/m075-gates2.log`).

## In-slice defect found and FIXED in scope
The dead-code gate flagged
`checkpoints.py: Checkpoint.as_dict` as new dead code.
Fixed by removal (not quarantine): nothing consumed
it; `checkpoint_status` returns the Checkpoint records
themselves. Gate re-proven green (44 passed above).

## Inventory deltas — for the coordinator's integration
(Shared surfaces NOT edited in this worktree, per
parallel discipline.)
1. **config_catalog.yaml** — add setting **S-64**:
   name `checkpoints`, scope top-level, type bool,
   default 'True', source
   mythic_agent/data/config_defaults.yaml, effect:
   'Named checkpoints (M-075): when true, the checkpoint
   road is open — /checkpoint take <name> captures the
   whole working tree (content-addressed blobs; files
   with their modes, symlinks as links; .git and cache
   directories out of scope) plus the attached session
   state under a name the user chooses, as a new node in
   the workspace checkpoint tree whose parent is the
   checkpoint that was current; /checkpoint restore
   <name> brings that tree and session back in one
   command, judged honestly — a tree changed since the
   last take or restore refuses and names the changed
   files, unless the trailing word discard throws those
   changes away on purpose, counted in the outcome;
   session state returns only to the session it was
   captured from; takes, restores and gate changes are
   journaled on the session (checkpoint_created,
   checkpoint_restored, checkpoints_setting_changed).
   /checkpoint shows the gate and the whole checkpoint
   tree (the journal view) and turns the gate on or off
   (journaled, with a save-failure revert); when false,
   takes and restores through the agent refuse and say
   so, while the tree stays readable.'
   Fixes: test_config_catalog x3 failures.
2. **PUBLIC_API.md** — regen: new module
   `mythic_agent/core/checkpoints.py`, 30 public names
   in its `__all__` (CHECKPOINTS_SLICE, MAX_FILE_BYTES,
   MAX_FILES, MAX_NAME_CHARS, PLAIN_EXPLANATION,
   SETTING_KEY, SKIP_DIRS, USAGE, Any, BoolChange,
   Checkpoint, CheckpointStore, Dict, List, Optional,
   RestoreOutcome, Tuple, capture_manifest,
   diff_manifests, enabled_from_config,
   format_checkpoint_created, format_checkpoint_restored,
   format_checkpoint_tree, format_checkpoints,
   format_setting_change, parse_checkpoint_args,
   set_enabled, tree_hash, validate_name,
   validate_session_snapshot) + 4 Agent methods
   (checkpoint_status, set_checkpoints, take_checkpoint,
   restore_checkpoint). Fixes: test_public_api x2.
3. **OWNERSHIP.md** — regen: new module
   `mythic_agent/core/checkpoints.py` (slice M-075).
   Fixes: test_ownership x2.
4. **roadmap_slices.yaml** — flip M-075 status
   queued -> done (75/272 at banking).
These 7 test failures (config_catalog 3, public_api 2,
ownership 2) are expected pre-integration and must go
green at the coordinator's regen, exactly as M-074's did.

## Dependency flags for other teams
* **team-02 (M-076 Session branching):** the session
  half of your road now exists — a checkpoint carries a
  judged session snapshot
  (`validate_session_snapshot`: session_id, status,
  total_tokens, messages, outcome) inside
  `CheckpointStore`; `Agent.restore_checkpoint` shows
  the restore-into-own-session pattern. Branch from
  these, do not duplicate the snapshot shape.
* **team-03 (M-077 Undo grown up, checkpoint half):**
  unblocked. `CheckpointStore.plan_restore` /
  `restore(name, discard)` + `diff_manifests` are the
  judged-restore machinery; the dirty-tree refusal text
  names the exact command form
  (`/checkpoint restore <name> discard`).
* All teams: new config key `checkpoints` (default
  true) is in config_defaults.yaml only; the catalogue
  entry is delta S-64 above — do not add it yourselves.

## Lessons
* MYTHIC_DIR inside the workspace makes a checkpoint
  try to freeze its own store (and the live session
  DB). Tests must park state outside the captured tree
  — the production shape (~/.mythic vs the project).
  The `live_agent` fixture in tests/test_checkpoints.py
  is the pattern.
* The dead-code gate is a real slice gate, not an
  inventory regen: an unconsumed helper is a defect to
  remove in-slice, not a quarantine entry.
* Heredoc file transfer (quoted delimiter) over
  device system.run is byte-exact for multi-hundred-line
  sources, including quotes and `$` — no base64 needed.
