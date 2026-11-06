# TEAM_LOG — Team 07 — M-081 Conflict workbench

## Charter (intent + acceptance)
Roadmap: "merge/rebase conflicts presented as decisions with both
sides' intent summarised; resolution is edited, tested, and journaled
like any change." Acceptance: real merge AND rebase conflicts in
throwaway repos are detected; both sides' intent is derived from the
actual commits/diffs (never invented); a resolution is decided per
conflicted place (ours/theirs/both/edit), written through EditJournal,
staged, verified against the real index, and journaled.

## Crew note
Six Mythic roles run as this team's internal cycle (sub-agents cannot
nest at this depth): Charter → Design → Build → Verify → Record →
Bank-prep, as below.

## Design (settled from the tree, M-074 shape)
- Pure core `mythic_agent/core/conflict_workbench.py`: marker parsing
  (two-way + diff3) into regions as data; `detect_workbench` reads real
  repo state (unmerged paths via `git diff --diff-filter=U`, operation
  from MERGE_HEAD / rebase-merge / etc., index stages 1/2/3);
  `summarise_side` builds intent mechanically — side commit subject,
  author, short sha (from `git log -1 <ref>`) plus +/- line counts of
  that side's stage against the base stage (difflib). Deleted side,
  missing base, missing commit are each stated plainly.
- Decisions: `Resolution` value; `decide_resolution` (ours/theirs/
  both), `edit_resolution` (edited text judged at edit time — marker-
  carrying text refuses); `apply_resolution` refuses pending places
  (named) and any resolved text still carrying a marker.
- Agent (`mythic_agent/agents/llm.py`): `conflict_workbench_status`,
  `set_conflict_workbench` (journal-first, save-failure revert — the
  M-074 pattern), `conflict_workbench_view`, `resolve_conflict` —
  gate-checked; resolution rides EditJournal, then `git add`, then a
  re-detection proves the file left the unmerged list ("tested"),
  then a `conflict_resolution_applied` session event.
- Surfaces sharing one parser/formatters: terminal `/conflicts`
  (`mythic_agent/terminal.py`), TUI `/conflicts`
  (`agents/command_handler.py` `_handle_conflicts` + routing), and
  chat-screen help/usage/routing (`ui/screens/chat_screen.py`).
- Setting `conflict_workbench: true` in `config_defaults.yaml`.
- Dead-code gate: the two approval-surface Agent methods
  (`conflict_workbench_view`, `resolve_conflict`) recorded in
  `docs/DEAD_CODE_QUARANTINE.txt`, the M-074 remedy.

## Files
- NEW `mythic_agent/core/conflict_workbench.py`
- NEW `tests/test_conflict_workbench.py` (39 tests)
- `mythic_agent/agents/llm.py`, `mythic_agent/terminal.py`,
  `mythic_agent/agents/command_handler.py`,
  `mythic_agent/ui/screens/chat_screen.py`,
  `mythic_agent/data/config_defaults.yaml`,
  `docs/DEAD_CODE_QUARANTINE.txt`

## Verify (counts from on-disk logs in this worktree)
- `m081-test.log`: tests/test_conflict_workbench.py — **39 passed**.
- `m081-gates2.log`: test_dead_code + test_arch_conformance —
  **17 passed** (after the quarantine recording).
- `m081-final.log`: combined targeted set — **120 passed, 7 failed**;
  all 7 failures are pending-inventory deltas below, nothing else.

## Inventory deltas (coordinator regenerates at integration)
1. `config_catalog.yaml`: add setting **S-64 `conflict_workbench`**
   (top-level bool, default True, source config_defaults.yaml; effect
   = the module's PLAIN_EXPLANATION road: /conflicts shows/decides,
   resolutions via EditJournal + staged + index-verified + journaled).
   Until then 3 config-catalog tests fail (defaults/schema keys
   uncatalogued) — expected.
2. `PUBLIC_API.md`: regenerate — new module
   `mythic_agent.core.conflict_workbench` public names. Until then
   2 public-api tests fail — expected.
3. `OWNERSHIP.md`: regenerate — new module has zero git history until
   this slice commits, and is absent from the doc. Until regen,
   2 ownership tests fail — expected.
4. `roadmap_slices.yaml`: flip M-081 queued → done at banking.

## Dependency flags
- None on other Wave-1 slices. Builds on banked M-071 (strict diff
  road is adjacent, not reused — conflicts are marker-based, not
  diff-based), M-074 pattern, and the EditJournal road.
- Known scope limit, stated honestly: delete/modify conflicts (a side
  with no stage) are detected with their intent summary ("this side
  deleted the file") but carry no marker regions, so
  `resolve_conflict` cannot decide them place-by-place; content
  conflicts are the workbench's road in this slice.

## Lessons
- Rebase intent: during rebase the incoming ref comes from
  rebase-merge/head-name; `git log -1` on that ref resolves the
  replayed branch's tip commit, which is the honest theirs-commit.
- The dead-code gate flags new Agent API methods even when tests
  exercise them; the quarantine recording (M-074's remedy) is the
  in-slice fix, not an integration delta.

## Bank-prep packet
Commit on `hammer/team-07`, style "M-081 ...". Coordinator: apply the
4 inventory deltas above, run the full suite, then bank in roadmap
order after M-080.
