# TEAM_LOG — Team 06 — M-080 Commit craft

Campaign: Mythic Coder Hammer Campaign, Wave 1, purplelongship.
Worktree: `~/mythic-hammer/team-06`, branch `hammer/team-06`,
base `b58517b` (verified at opening: hostname purplelongship,
HEAD b58517b, branch hammer/team-06).
Crew cycle run as one lead wearing the six Mythic roles in
sequence (depth 2/2 — the crew cannot nest as sub-agents):
Charter → Design → Build → Verify → Record → Bank-prep.

## Charter (intent + acceptance)

Roadmap's words (M-080): "commit-splitting by concern,
message drafting from the actual diff, and the house rules
wired in (fetch + remote-diff before push, never force-push,
verify the remote moved)."

Acceptance: a working-tree change splits into per-concern
commits; every drafted message is read off its group's own
diff; a push through the new road fetches first, reads the
remote-diff, refuses anything that would need force, and
proves with ls-remote that the remote moved — with tests
proving each refusal. Adjacency law honoured: M-078
(auto-commit discipline, Team 04, parallel from same base)
is NOT in this tree; its commit trigger is read through a
named seam and flagged DEPENDS-ON-M-078 (below).

## Design (settled from the tree)

Shape follows M-074 exactly: pure core module + Agent
methods + terminal & TUI surfaces sharing one parser and
formatters + a gate setting + tests.

- Splitting rides the hunk layer, never re-derives it:
  every hunk is parsed and count-proven by M-074's
  `hunk_review.split_diff` unchanged. One file belongs to
  exactly one concern (code / tests / docs / config, judged
  from its path alone), so a file's hunks are never split
  across commits — stated plainly in the module.
- Drafting is deterministic from the diff: verb from the
  change kind (all-new = Add, all-deleted = Remove, else
  Update), names from the group's files (3 named, rest
  counted), body = per-file (+a -r) counts from the diff.
- Push discipline is pure judgements + a thin git road:
  `validate_push_args` refuses every force spelling,
  `+` refspecs, deletion refspecs, --mirror/--delete;
  `judge_push` refuses no-head and diverged, returns
  up-to-date as an honest no-send; `verify_remote_moved`
  proves the ls-remote after-state equals the pushed head
  and differs from the before-state.
- The existing TUI `/commit` road (stage-everything +
  bare `git push`, no fetch/verify) is left untouched —
  M-080 builds its own layer beside it; rewiring that
  road is a coordinator decision, not taken here.
- M-078 seam: `commit_craft.auto_commit_trigger()` returns
  {"slice": "M-078", "available": False, note...}; surfaced
  in `Agent.commit_craft_status()` and the show surface.
  **DEPENDS-ON-M-078**: when M-078 banks, the coordinator
  wires its trigger to `plan_commit_split` /
  `commit_craft_group`; nothing of M-078's internals was
  invented here.

## Files

- NEW `mythic_agent/core/commit_craft.py` — pure layer:
  `split_files`, `classify_concern`, `plan_commits`,
  `draft_subject` / `draft_message`, `validate_push_args`,
  `judge_push`, `verify_remote_moved`,
  `auto_commit_trigger` (M-078 seam), git readings
  (`run_git`, `collect_working_diff`, `current_branch`,
  `ls_remote_head`, `remote_tracking_head`, `ahead_behind`,
  `remote_diff_stat`), gate (`enabled_from_config`,
  `set_enabled`, `BoolChange`), surface parser/formatters
  (`parse_commitcraft_args`, `format_commit_craft`,
  `format_plan`, `format_commit_record`,
  `format_push_record`, `format_setting_change`).
- `mythic_agent/agents/llm.py` — Agent methods:
  `commit_craft_status`, `set_commit_craft` (journal-first,
  save-failure revert, M-074 pattern),
  `plan_commit_split` (journaled `commit_craft_planned`),
  `commit_craft_group` (re-plans from the live tree, stages
  exactly the group's files, proves the index holds exactly
  that group before committing, journaled
  `commit_craft_committed`), `push_with_house_rules`
  (ls-remote before → fetch → remote-diff → judge → push
  with explicit refspec → ls-remote verify; journaled
  `commit_craft_pushed`).
- `mythic_agent/terminal.py` — `/commitcraft` road +
  help line.
- `mythic_agent/agents/command_handler.py` — dispatch +
  `_handle_commitcraft`.
- `mythic_agent/ui/screens/chat_screen.py` — help line,
  usage entry, system-command routing for `/commitcraft`.
- `mythic_agent/data/config_defaults.yaml` — `commit_craft: true`.
- NEW `tests/test_commit_craft.py` — 60 tests. All git
  tests use throwaway repos under tmp_path; all push tests
  use a local bare repo as the remote (never the real
  origin).

## Verify (counts from on-disk logs in this worktree)

- `m080-test.log`: tests/test_commit_craft.py —
  **60 passed**.
- `m080-neighbours.log`: test_hunk_review +
  test_edit_formats + test_apply_repair +
  test_hash_anchored — **223 passed**.
- `m080-gates.log`: test_dead_code +
  test_arch_conformance + test_static_gate —
  **21 passed** (no dead-code quarantine needed: every
  public road is surface-wired).
- `m080-inventory.log`: test_config_catalog +
  test_config + test_public_api + test_ownership +
  test_roadmap_slices — **47 passed, 7 failed**, every
  failure a pending-inventory delta (below), none a
  product defect.

## Inventory deltas (for the coordinator — NOT edited here)

Shared surfaces were not touched, per parallel discipline.
At integration please regenerate / apply:

1. `mythic_agent/data/config_catalog.yaml` — add S-64:
   name `commit_craft`, scope top-level, type bool,
   default 'True', source
   mythic_agent/data/config_defaults.yaml, effect:
   'Commit craft (M-080): when true, the commitcraft road
   is open — a working-tree change is split into commits
   by concern (code, tests, docs, config), each message
   drafted from its own actual diff (verb, file names, and
   per-file counts read off the diff; every hunk judged by
   the M-074 hunk layer), one group committed at a time
   with the index proven to hold exactly that group, and
   pushes follow the house rules wired in as refusals:
   fetch first, the remote-diff read before pushing, never
   force-push (a diverged remote refuses), and ls-remote
   verification afterwards that the remote moved to the
   pushed head; an up-to-date remote is an honest no-send.
   Commit craft never commits on its own — the auto-commit
   trigger is M-078's seam (DEPENDS-ON-M-078), reported
   unavailable until it banks. /commitcraft shows the gate,
   a worked split-and-draft example, plans the split,
   commits one concern group, and pushes under the house
   rules (journaled, with a save-failure revert); when
   false, commits and pushes through the agent refuse and
   say so, while the pure planning maths stays readable.'
   (This heals the 3 test_config_catalog failures.)
2. `docs/PUBLIC_API.md` — regenerate: commit_craft adds
   its public names (module `__all__`: 40 names incl. the
   typing re-exports, matching the M-074 convention).
   (Heals the 2 test_public_api failures.)
3. `docs/OWNERSHIP.md` — regenerate after the banking
   commit lands (the new module has zero git history
   until then). (Heals the 2 test_ownership failures.)
4. `mythic_agent/data/roadmap_slices.yaml` — flip M-080
   to done at banking.
5. `CAMPAIGN_STATE.md` (VM keeper copy) — M-080 ledger row.

## Dependency flags

- **DEPENDS-ON-M-078** (Team 04, in flight): the
  auto-commit trigger seam above. M-080's drafting and
  push halves are fully independent and complete; only
  the *trigger* waits on M-078.

## Lessons

- Chunked base64 re-emission slips even at 2.4k chars:
  one chunk arrived with 2401 data characters and was
  refused by device validation; a verbatim retry landed.
  The sha256-on-final guard caught nothing because
  nothing bad ever landed — keep both guards.
- Test-writing trap: "tests/test_app.py" contains the
  substring "app.py" — a status assertion on substrings
  lies. Assert on split lines/paths, not substrings.
- The agent fixture's session state lives inside the
  throwaway repo in git tests; a committed `.gitignore`
  for `state/` in the seed repo is what a real repo
  would carry, and it keeps the split honest.

## Banking packet

- Commit on `hammer/team-06` (local only, never pushed):
  "M-080 Commit craft — ..." (see git log).
- Coordinator: integrate in roadmap order after M-079;
  apply the inventory deltas above; run the FULL suite
  on this laptop per banking; push the campaign branch
  with explicit refspec + ls-remote verify (the house
  rules this slice builds).
