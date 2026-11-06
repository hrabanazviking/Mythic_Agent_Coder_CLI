# TEAM 04 — TEAM_LOG — M-078 Auto-commit discipline (Aider's crown)

Campaign: Mythic Coder HAMMER, wave 1, team-04 worktree
(`~/mythic-hammer/team-04`, branch `hammer/team-04`, base `b58517b`).
Crew cycle run as one agent's internal cycle (depth 2/2 cannot nest
sub-agents): Charter → Design → Build → Verify → Record → Bank-prep.

## Charter (intent + acceptance)

Roadmap's words: every accepted edit set lands as its own commit with
a written message — on a working branch by default, never on the
user's protected branches unasked. Acceptance: (1) one accepted edit
set = one commit carrying exactly the accepted files and a written
message that names them; (2) protected branches (main, master,
development, develop + user-named) are never committed to without the
explicit standing setting `auto_commit_allow_protected`; on a
protected branch the default road moves the commit onto the working
branch; (3) blank message / empty or escaping file set / detached
head refuse and commit nothing; (4) the discipline ships OFF —
`/autocommit on` is the standing word; (5) tests use throwaway git
repos only, never the campaign tree.

## Design (settled from the tree)

Inspected first: M-074's shape (pure core + Agent methods + terminal
& TUI surfaces sharing one parser/formatters + setting + tests) and
followed it exactly. Findings that shaped the build:

- Accepted edits are known through the EditJournal road
  (M-071..M-074 Agent apply methods); this slice's Agent road,
  `commit_accepted_edits(files, summary)`, is the commit step an
  accepted set lands through.
- No git discipline existed: `context/gitdiff.py` only reads diffs;
  `agents/tools.py::auto_git_commit` commits a single file onto
  whatever branch is checked out, protected or not (see Dependency
  flags). No protected-branch notion existed anywhere in config —
  this slice introduces it.
- Core stays pure (judges, never runs git): `plan_commit` returns a
  `CommitPlan` (current branch, target branch, on_protected,
  switch_needed, judged files, written message). The Agent executes
  exactly that plan: switch if planned, stage exactly the accepted
  files, one commit, journal `auto_commit_committed`.

## Files

- NEW `mythic_agent/core/auto_commit.py` — pure discipline layer:
  settings readers/validators (`enabled_from_config`,
  `allow_protected_from_config`, `protected_from_config`,
  `working_branch_from_config`, `is_protected`), `set_enabled` /
  `set_allow_protected` (SettingChange, journal-first pattern),
  `validate_files` / `validate_message` / `build_message`,
  `plan_commit`, `CommitPlan`, `CommitOutcome`, and the
  `/autocommit` parser + formatters (`parse_autocommit_args`,
  `format_auto_commit`, `format_plan`, `format_commit_record`,
  `format_setting_change`).
- `mythic_agent/agents/llm.py` — Agent: `auto_commit_status`,
  `set_auto_commit`, `set_auto_commit_allow_protected` (both
  journal-first with save-failure revert), `commit_accepted_edits`
  (gate → repo/branch checks → plan → optional switch → stage
  exactly the accepted files → one commit → journaled outcome;
  nothing staged = honest no-commit record), private helpers
  `_auto_commit_git`, `_auto_commit_branch`,
  `_set_auto_commit_setting`.
- `mythic_agent/terminal.py` — `/autocommit` road + help line.
- `mythic_agent/agents/command_handler.py` — TUI dispatch +
  `_handle_autocommit`.
- `mythic_agent/ui/screens/chat_screen.py` — help line, usage
  entry, system-command routing for `/autocommit`.
- `mythic_agent/data/config_defaults.yaml` — new settings (below).
- NEW `tests/test_auto_commit.py` — 46 tests; all git work in
  throwaway repos under tmp_path.

## Verify (counts from on-disk logs only)

- `tests/test_auto_commit.py`: **46 passed**
  (log: `hidden_files/m078-targeted.log`). First run was 44 passed /
  2 failed — both failures were bugs in my own test assertions
  (a regex that did not match the refusal's exact wording; a
  substring check where "test_app.py" contains "app.py"), fixed in
  the tests, product code untouched.
- Neighbours on the touched surfaces (hunk review, apply repair,
  policy, edit formats, hash anchored): **253 passed**
  (`hidden_files/m078-neighbours.log`).
- Asset/dependency sight: **51 passed** (`hidden_files/m078-sight.log`).
- Catalogue: 3 failed / 11 passed (`hidden_files/m078-catalog.log`) —
  the named integration delta below, proven: with the slice stashed,
  the same file is 14 passed; the only failing assertions name the
  new `auto_commit*` defaults keys.

## Inventory deltas (for the coordinator — shared surfaces NOT edited)

- `config_catalog.yaml`: add catalogue entries for the four new
  settings (next free id after S-63): `auto_commit` (bool, default
  False), `auto_commit_allow_protected` (bool, default False),
  `auto_commit_branch` (string, default `mythic/working`),
  `auto_commit_protected` (list, default
  `[main, master, development, develop]`). Until then
  `tests/test_config_catalog.py` fails exactly 3 tests
  (every-defaults-key / every-schema-key / types-and-defaults).
- `mythic_agent/data/roadmap_slices.yaml`: flip M-078 queued → done.
- `docs/PUBLIC_API.md` + `docs/OWNERSHIP.md`: regenerate — new
  module `mythic_agent/core/auto_commit.py` and its public names
  (see Files), new Agent methods `auto_commit_status`,
  `set_auto_commit`, `set_auto_commit_allow_protected`,
  `commit_accepted_edits`; new session events
  `auto_commit_setting_changed`,
  `auto_commit_protected_setting_changed`,
  `auto_commit_setting_reverted`, `auto_commit_committed`;
  new command `/autocommit`.
- `CAMPAIGN_STATE.md`: M-078 row → DONE, count 74 → 75.

## Dependency flags

- LEGACY HAZARD (commission, not fixed here): `agents/tools.py`'s
  exported `auto_git_commit` still commits onto any checked-out
  branch — including protected ones — with no branch discipline.
  The disciplined road as of this slice is
  `Agent.commit_accepted_edits`. Hardening or retiring the legacy
  helper touches PUBLIC_API and `tests/test_policy.py` and was left
  for the coordinator rather than changed mid-wave under 10 teams.
- M-076 (session branching, team-02) is complementary: when a
  session branch exists, a future slice may prefer it as the
  working branch; M-078's default is the named
  `auto_commit_branch` (`mythic/working`), created on demand.
- M-080 (Commit craft) builds on this slice's message discipline
  (`build_message`); M-206's banking road names M-078 explicitly.

## Lessons

- Device `file.write` base64 re-emission slipped twice at ~1.1k
  chars (sha256 guard caught both, nothing bad landed). Reliable
  road: land a tiny receiver in small (170-byte) verified chunks,
  serve it from tmux, POST files from the VM through the tunnel
  proxy, verify the on-device receipts log sha256 per file.
- Test-assertion traps: substring checks on filenames
  ("app.py" ⊂ "test_app.py") and regexes written from paraphrase
  instead of the product's exact refusal wording.

## Bank-prep packet

- Branch: `hammer/team-04` (local commit only, never pushed).
- Commit style: `M-078 ...` (see `git log` on this branch).
- Ready for coordinator integration + the inventory deltas above;
  full suite is the coordinator's banking step on this laptop.
