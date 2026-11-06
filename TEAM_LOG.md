# TEAM_LOG — Team 03 · M-077 Undo grown up

Campaign: Mythic Coder Hammer Campaign, Wave 1 (10 teams,
purplelongship). Worktree `~/mythic-hammer/team-03`, branch
`hammer/team-03`, base `b58517b` (74/272 banked at opening).
Crew cycle run as one lead wearing the six Mythic roles in
sequence (Charter → Design → Build → Verify → Record →
Bank-prep); depth-2 cannot nest sub-crews — stated plainly
per the brief.

## Charter (intent + acceptance)

Roadmap's words (mythic_agent/data/roadmap_slices.yaml,
M-077): "`/undo` walks edits, commands, and checkpoints as
one timeline; undo of a *command's* effects is attempted
via its recorded footprint, labelled certain or
best-effort."

Acceptance: (1) one timeline over the three strands,
newest first, undo walked from the top; (2) edits undo
through the existing EditJournal, unchanged; (3) commands
run through the agent's `run_command` tool record a
footprint (files created/changed/deleted, judged from
before/after workspace snapshots, before-contents backed
up) and undo restores it, labelled certain or
best-effort by the footprint's completeness; (4) bare
`/undo` keeps its legacy meaning (the newest entry — in
the old contract tests, an edit, with EditJournal's exact
words); (5) the checkpoint strand is built against a
named seam only, M-075's internals never invented.

## Design (settled from the tree)

Inspected before designing: `core/edits.py` (EditJournal —
atomic writes, conservative undo, no read API, no
timestamps), the existing `/undo` roads (terminal →
EditJournal directly; TUI CommandHandler → EditJournal;
chat-screen usage text), `agents/tools.py` `run_command`
(no footprint recording existed — the slice's gap),
`core/journal.py` + the agent `_checkpoint` session-event
road, M-074 (`core/hunk_review.py` + Agent methods +
terminal/TUI surfaces + setting) as the campaign shape to
mirror, and the M-075 scoping note (checkpoints capture
working tree + session state; restore is one command —
Team 01's slice, in parallel, NOT in this tree).

Decisions:
- Pure core `mythic_agent/core/undo_timeline.py`:
  snapshots (`take_snapshot`, bounded — 2000 files,
  1 MB/file and 16 MB total backup caps; `.git`, caches,
  venvs, dependency trees not walked), footprints
  (`build_footprint` — certain only when both snapshots
  are complete and every changed file's before-contents
  are backed up, else best-effort with reasons carried),
  the timeline (`TimelineEntry`, `build_timeline`,
  `judge_walk` — only the newest entry undoes; a buried
  entry refuses and names its blocker), the durable
  `UndoStore` (timeline order + footprint store, SQLite
  beside the EditJournal under `~/.mythic/undo/<wsid>/`),
  command undo all-or-nothing (any footprint file changed
  since the command, or a before-image too large to back
  up, refuses the whole undo and changes nothing), gate
  (`undo_timeline`, ships ON), one parser
  (`parse_undo_args`) + formatters shared by both roads.
- Ordering across strands: the UndoStore keeps a shared
  sequence. Edits register at write time (a guarded lazy
  hook in `EditJournal.write`, the M-072 lazy-import
  pattern — a timeline failure can never break an edit);
  commands register at record time; checkpoints register
  when first listed through the seam.
- `/undo` grammar: bare = undo newest entry; `list` =
  show; `edit` / `command` = newest entry of a strand
  (walk order still governs); `checkpoint <id>` = restore
  through the seam; `<count>` = walk back that many
  entries; `on` / `off` = the gate. Gate off: bare `/undo`
  keeps the exact legacy EditJournal road, timeline forms
  refuse and say so.
- Agent: `undo_timeline_status`, `set_undo_timeline`
  (journal-first `undo_timeline_setting_changed`,
  save-failure revert, the M-074 pattern), `undo_newest`,
  `undo_kind`, `restore_checkpoint_via_seam`,
  `_checkpoint_timeline_source`. Session events:
  `undo_timeline_setting_changed` / `_reverted`,
  `command_footprint_recorded` (from the tool road when a
  session is attached), `undo_performed`.
- Recording road: `execute_tool`'s `run_command` takes a
  snapshot before the run and records the footprint
  after — agent attached + gate on only; recording never
  alters the command or its result (guarded try/except,
  the M-055/M-056 pattern).

## The checkpoint seam — DEPENDS-ON-M-075

**FLAG: DEPENDS-ON-M-075.** M-075 (Checkpoints v2, Team
01) had NOT banked when this slice finished, so the
checkpoint strand is wired through exactly one
clearly-named seam and nothing of M-075's internals is
invented:

- `CheckpointTimelineSource` (Protocol, in
  `core/undo_timeline.py`): a source offers
  `list_checkpoint_entries()` → mappings with at least
  `id` and `name`/`label` (`certainty` optional, defaults
  to the honest `unknown`) and
  `restore_checkpoint(checkpoint_id) -> str`.
- The agent reads its source from the attribute named by
  `CHECKPOINT_SOURCE_ATTR = "checkpoint_timeline_source"`
  (the object itself, or a zero-argument callable
  returning it). `checkpoint_entries_from_source`
  validates what crosses the seam: an off-seam source or
  an entry with no usable id raises — no strand is ever
  invented from an unjudged shape.
- Final wiring owed at integration: M-075's banking sets
  `agent.checkpoint_timeline_source` to its source (or
  the coordinator adapts the seam call to M-075's shipped
  shape). Until then `/undo list` states plainly "no
  checkpoint source is wired yet — DEPENDS-ON-M-075
  (Checkpoints v2); the edit and command strands are
  live", and `/undo checkpoint <id>` refuses with the
  same flag. A fake source in the tests proves listing,
  labelling, and restore through the seam.

## Files

- NEW `mythic_agent/core/undo_timeline.py` — pure core +
  UndoStore + seam + parser/formatters (see Design).
- NEW `tests/test_undo_timeline.py` — 53 tests.
- `mythic_agent/core/edits.py` — `EditJournal.entries()`
  (the edit strand's read API) + the guarded
  timeline-registration hook in `write`.
- `mythic_agent/agents/llm.py` — the Agent methods above.
- `mythic_agent/agents/tools.py` — footprint
  snapshot/record around `run_command`.
- `mythic_agent/terminal.py` — `/undo` grown to the full
  grammar + help line.
- `mythic_agent/agents/command_handler.py` —
  `_handle_undo` grown likewise (no-primary fallback
  keeps the legacy road; the pre-existing
  git-reset-never test still passes).
- `mythic_agent/ui/screens/chat_screen.py` — `/undo`
  usage text updated (routing already carried `/undo`).
- `mythic_agent/data/config_defaults.yaml` —
  `undo_timeline: true` added.
- Logs (untracked, in this worktree): `m077-test.log`,
  `m077-regress1.log`, `m077-regress2.log`,
  `m077-regress3.log`, `m077-cli.log`, `m077-gates.log`,
  `m077-static.log`.

## Verify (counts from on-disk logs only)

- `tests/test_undo_timeline.py`: **53 passed**
  (m077-test.log; first run 51 passed / 2 failed — a test
  picked the wrong checkpoint entry from the newest-first
  list, and the agent refusal did not yet carry the
  literal DEPENDS-ON-M-075 flag; both fixed, re-run
  green).
- Neighbours: test_edits + test_hunk_review +
  test_apply_repair + test_hash_anchored +
  test_edit_formats + test_journal +
  test_journal_integrity + test_policy: **304 passed**
  (m077-regress1.log).
- test_structural_rewrite + test_lsp_rename +
  test_config_catalog + test_public_api + test_ownership
  + test_roadmap_slices: **194 passed, 7 failed**
  (m077-regress2.log) — all 7 failures are the inventory
  deltas below, nothing else.
- Legacy CLI contract: test_cli
  `test_human_undo_uses_shared_journal` +
  `test_scripted_human_loop_clear_add_and_multiple_turns`:
  **2 passed** (m077-cli.log).
- Tool-road neighbours: test_execution + test_debug_loop
  + test_test_intelligence + test_cancellation:
  **72 passed, 1 skipped** (live-tier) (m077-regress3.log).
- Gates: test_dead_code + test_arch_conformance:
  **17 passed** (m077-gates.log); test_static_gate:
  **4 passed** (m077-static.log).

## Inventory deltas (for the coordinator — NOT edited here)

- PUBLIC_API.md: add `mythic_agent.core.undo_timeline`
  and its public names (module `__all__`: CERTAINTIES,
  CHECKPOINT_SOURCE_ATTR, KINDS, MAX_BACKUP_BYTES,
  MAX_SNAPSHOT_FILES, PLAIN_EXPLANATION, SETTING_KEY,
  UNDO_TIMELINE_SLICE, USAGE, BoolChange,
  CheckpointTimelineSource, CommandFootprint, FileChange,
  Snapshot, TimelineEntry, UndoOutcome, UndoStore,
  build_footprint, build_timeline,
  checkpoint_entries_from_source, enabled_from_config,
  format_setting_change, format_timeline,
  format_undo_outcome, format_undo_timeline, judge_walk,
  parse_undo_args, register_edit_entry, set_enabled,
  take_snapshot, + re-exported typing names per house
  style); Agent gains `undo_timeline_status`,
  `set_undo_timeline`, `undo_newest`, `undo_kind`,
  `restore_checkpoint_via_seam`; EditJournal gains
  `entries`. Until regen: test_public_api ×2 fail
  (expected delta, m077-regress2.log).
- OWNERSHIP.md: add `mythic_agent/core/undo_timeline.py`
  (its generator currently refuses with "module has zero
  git history" — heals when this slice commits; doc regen
  is the coordinator's). Until regen: test_ownership ×2
  fail (expected delta).
- Config catalogue (M-009): new setting **S-64**
  (next free id; S-63 was hunk_review): name
  `undo_timeline`, scope top-level, type bool, default
  'True', source mythic_agent/data/config_defaults.yaml,
  effect: 'Undo grown up (M-077): when true, /undo walks
  edits, commands, and checkpoints as one timeline,
  newest first — an edit undoes through the EditJournal,
  a command undoes through its recorded footprint (the
  files it created, changed, or deleted, judged from
  snapshots taken around its run through the agent
  run_command tool, before-contents backed up within the
  snapshot bounds), labelled certain when the snapshots
  were complete and every changed file is backed up or
  best-effort with its reasons otherwise; one file
  changed since the command refuses the whole undo;
  checkpoints join through the CheckpointTimelineSource
  seam (M-075). /undo list shows the timeline and the
  gate, /undo on/off changes it (journaled, with a
  save-failure revert); when false, /undo keeps its
  original last-edit behaviour and timeline undos
  refuse.' Until the catalogue lands: test_config_catalog
  ×3 fail (expected delta).
- Roadmap data: flip M-077 status queued → done at
  banking (roadmap_slices.yaml NOT edited here).
- CAMPAIGN_STATE.md: M-077 row/note is the coordinator's
  to write at banking.

## Dependency flags

- **DEPENDS-ON-M-075** (see the seam section): final
  checkpoint wiring owed when M-075 banks — set
  `agent.checkpoint_timeline_source` (or adapt the seam
  call to M-075's shipped shape). Everything else in
  M-077 is complete without it.
- No other dependencies. M-076 (session branching) does
  not intersect this slice's files except llm.py /
  terminal.py / command_handler.py regions (theirs are
  elsewhere in those files; integration order is the
  coordinator's).

## Banking packet

- Branch: `hammer/team-03`, one commit, message style
  "M-077 ...". Never pushed (coordinator banks).
- Suggested coordinator checks at integration: regen
  PUBLIC_API.md + OWNERSHIP.md, add catalogue S-64, flip
  M-077 in roadmap data, then the 7 delta failures above
  should go green; wire the M-075 checkpoint source when
  M-075 banks and re-run tests/test_undo_timeline.py.

## Lessons

- Base64 carried through model re-emission corrupts at
  segment joins, not randomly: 2400-byte chunks landed
  for two files, but the patcher only landed as 384-byte
  pieces — and reliably as 192-byte halves — each with
  its own sha256, concatenated on-device and verified
  against the whole-file sha256 before use. Two failures
  were my own transcription slips (a wrong tail carried
  from another chunk; a neighbouring piece's segment
  appended), each caught by the sha guard — the guard is
  load-bearing; never transfer without it.
- A timeline that spans stores needs its own shared
  sequence assigned at write/record time; merging by
  per-store ids at read time cannot order the strands
  honestly.
