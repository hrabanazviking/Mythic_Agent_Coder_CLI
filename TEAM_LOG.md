# TEAM_LOG — Team 02, Slice M-076 Session Branching (Hammer Campaign, Wave 1)

Crew cycle run as the lead's disciplined internal six-role cycle
(Charter → Design → Build → Verify → Record → Bank-prep); agent
depth cannot nest further, so no sub-agents were spawned.

## Charter (intent + acceptance)
Roadmap's words: fork a session at any message ("try the other
road from here") — branches share history, diverge honestly,
and can be compared. Acceptance: (1) a fork at message index N
creates a new session holding exactly the parent's messages
0..N; (2) afterwards the two sessions are fully independent;
(3) lineage is discoverable (children of a parent, root/depth
for nested branches); (4) any two sessions can be compared
(shared prefix, first divergence, each side's own messages);
(5) the frozen v1 session formats (M-010) still read branches;
(6) terminal + TUI surfaces share one parser/formatters;
(7) a gate setting ships in config defaults.

## Design settled from the tree
- Inspected: `core/sessions.py` (SessionStore: SQLite v1,
  create/checkpoint/resume/release, leases, WAL-journaled
  checkpoints, events table), `data/session_catalog.yaml`
  (M-010 formats J-01..J-07 + compat rules), `core/transcript`
  handling via the catalog, M-074's full shape (pure core +
  Agent methods + terminal/TUI sharing parser/formatters +
  setting + tests), Agent session machinery
  (`attach_session`, `_checkpoint`, `_append_message`).
- Settled: NO format change. A branch is an ordinary new v1
  session created through the store's own create/checkpoint
  road; lineage rides in the record's existing `metadata`
  dict under a `branch` key — v1 readers carry it (catalogue
  compat rule: required keys never shrink; superset, never
  reshaping). M-010 golden artefacts untouched and their tests
  pass. Branch metadata: parent_session_id, fork_index,
  fork_role, branch_name, root_session_id, depth.
- Fork semantics: 0-based index, branch keeps messages up to
  AND including the fork message; the prefix must itself pass
  `validate_messages` (a fork landing mid-orphaned-tool-result
  refuses as a broken history). Branch starts `idle`,
  total_tokens 0 (the parent's token total belongs to the
  parent's whole road; a prefix share is not knowable — never
  guessed), lease released so it can be resumed like any
  stored session. The parent is only read by the store; the
  Agent additionally journals `session_branch_forked` on the
  parent session when forking its own attached session.
- Comparison: whole-message equality over the contexts;
  shared prefix counted exactly; `diverged_at` is the first
  differing index, or None when one context is the other's
  prefix (reported honestly as "no divergence yet" /
  identical), never smoothed into a fake difference.
- Gate: `session_branching` ships ON (defaults file edited);
  gate off refuses FORKS through the Agent only — compare
  and list are pure reads of what exists and stay available.

## Files changed
- NEW `mythic_agent/core/session_branching.py` (597 lines):
  pure layer — fork_context, shared_prefix_length,
  compare_contexts/BranchComparison, branch_metadata,
  branch_info, children_of, gate (enabled_from_config,
  set_enabled, BoolChange), and the /branch parser +
  formatters (parse_branch_args, format_branching,
  format_fork, format_comparison, format_branch_list,
  format_setting_change); format_branching's worked example
  exercises every public road.
- `mythic_agent/core/sessions.py`: SessionStore.branch()
  (lazy-imports the pure layer — no import cycle) +
  SessionStore.branches_of().
- `mythic_agent/agents/llm.py`: Agent.session_branching_status,
  set_session_branching (journal-first + save-failure revert,
  the established pattern), fork_session, compare_sessions,
  list_session_branches.
- `mythic_agent/terminal.py`: `/branch` in _slash + help line.
- `mythic_agent/agents/command_handler.py`: _handle_branch +
  dispatch.
- `mythic_agent/ui/screens/chat_screen.py`: /branch help line,
  help-dict entry, system-command routing list.
- `mythic_agent/data/config_defaults.yaml`: `session_branching: true`.
- NEW `tests/test_session_branching.py`: 47 tests.
- Logs in worktree: m076-targeted.log, m076-neighbours.log,
  m076-gates.log, m076-deadcode.log, m076-arch.log.
- Write road note: files were landed via system.run heredocs
  (quoted delimiter) and in-place python patch scripts rather
  than hand-carried base64 file.write chunks — the campaign's
  own recorded lesson is that hand-re-emitted base64 corrupts;
  every file was compile-checked and test-verified on disk.

## Verify (counts read from on-disk logs only, run on the laptop)
- Targeted: tests/test_session_branching.py — **47 passed**
  (m076-targeted.log). One test-authoring fix during the run
  (a malformed-lineage expectation ordering), no product defect.
- Neighbours: test_sessions + test_session_catalog (M-010
  golden v1 artefacts) + test_session_identity +
  test_hunk_review — **100 passed** (m076-neighbours.log).
- Dead-code gate: **6 passed** (m076-deadcode.log) — no new
  quarantine entries needed; every new public name is exercised
  by a surface.
- Arch conformance + roadmap slices: **24 passed** (m076-arch.log).
- Inventory gates: 7 failed / 24 passed (m076-gates.log) — ALL
  seven are the expected pending-inventory deltas below, none
  touch M-076 behaviour.

## Inventory deltas for the coordinator (do NOT regenerate here)
1. Config catalogue (mythic_agent/data/config_catalog.yaml):
   add **S-64** — name `session_branching`, scope top-level,
   type bool, default 'True', source config_defaults.yaml,
   effect: 'Session branching (M-076): when true, the /branch
   road is open — a session forks at any message into a new
   v1 session sharing the parent's history up to and
   including the fork message, lineage (parent, fork index
   and role, root, depth) recorded in the branch's metadata,
   the fork journaled session_branched on the child and
   session_branch_forked on the parent; branches diverge
   independently and any two sessions can be compared by
   shared prefix and first divergence. When false, forks
   through the agent refuse and say so, while comparing and
   listing stay available.' Fixes the 3 test_config_catalog
   failures in m076-gates.log.
2. PUBLIC_API.md: regenerate — new public names:
   mythic_agent.core.session_branching (SESSION_BRANCHING_SLICE,
   PLAIN_EXPLANATION, SETTING_KEY, USAGE, BoolChange,
   BranchComparison, branch_info, branch_metadata, children_of,
   compare_contexts, enabled_from_config, fork_context,
   format_branch_list, format_branching, format_comparison,
   format_fork, format_setting_change, parse_branch_args,
   set_enabled, shared_prefix_length + re-exported typing
   names per generator convention); Agent methods
   session_branching_status / set_session_branching /
   fork_session / compare_sessions / list_session_branches;
   SessionStore.branch / branches_of. Fixes the 2
   test_public_api failures.
3. OWNERSHIP.md: regenerate (new module
   mythic_agent/core/session_branching.py; its zero-git-history
   failure resolves once this commit lands). Fixes the 2
   test_ownership failures.
4. Roadmap data: flip M-076 queued → done (done count
   74 → 75 at integration, in roadmap order after M-075).
5. CAMPAIGN_STATE.md: ledger row + count, coordinator's hand.

## Dependency flags
- None blocking. Independent of M-075 (team-01) — branching
  forks sessions, not checkpoints; no shared files with the
  other Wave-1 slices beyond the inventory surfaces above.
- Session-format: no change, no flagged delta — proof is the
  M-010 golden tests passing unchanged (in neighbours run).

## Lessons
- Heredoc + patch-script writes over device system.run are
  byte-reliable where hand-carried base64 is not; compile +
  targeted tests on disk are the verification, as always.
- A branch's honest token count is 0/unknown, not a share of
  the parent's total — recording the parent's total on the
  child would have been a quiet lie the comparison surface
  would then repeat.
