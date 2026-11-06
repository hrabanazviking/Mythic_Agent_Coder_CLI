# TEAM_LOG — Team 08 · M-082 PR craft

Hammer Campaign Wave 1, purplelongship, worktree
`~/mythic-hammer/team-08`, branch `hammer/team-08`, base
`b58517b` (74/272 banked at opening). Crew cycle run as one
lead's internal six roles (Charter → Design → Build →
Verify → Record → Bank-prep); no nested sub-agents were
spawned (depth limit), so the six Mythic roles were one
cycle, not six separate workers.

## Charter (intent + acceptance)

Roadmap's words (roadmap_slices.yaml M-082 + the roadmap
section): create, review, and respond to pull requests —
review comments fetched as tasks; a review pass posts only
at the user's word (sending as the user is a standing
pause-line). Acceptance: the create/review/respond
machinery exists as drafts + gated posts; review comments
land as tasks; no test makes a live GitHub call; the
user-word gate is proven by a fake runner recording zero
calls on every unarmed post.

## Design (settled from the tree)

* Existing GitHub integration: `integrations/github.py`
  (Slice 36) shells to the user's own `gh` CLI — bare PR
  create / issue list / runs / one comment post, each
  sending the moment it is called, no draft stage, no
  fetch of a PR or its review comments. M-009 catalogue
  carries `github.repo_url` (S-17), `github.token` (S-18,
  secret, Kista-bound), runtime `github_timeout` (S-28).
  M-082 keeps that auth posture: all traffic rides the
  user's `gh` through ONE injectable runner seam
  (argv in, stdout out) in the new pure core; the Agent's
  default runner is `integrations.github._run_gh`.
* Campaign shape followed M-074 exactly: pure core module
  + Agent methods + terminal & TUI surfaces sharing one
  parser/formatters + one setting + tests.
* Tasks surface: review comments become task dicts in the
  shape of the house task records (task_id / name / state
  "queued" / kind "review_comment", plus pr_number,
  comment_id, author, body, path, line, url) — one task
  per comment, faithfully; a review with no words makes
  no task (nothing to act on), and that is stated in the
  module, not silent.
* The user-word gate (the slice's heart): every draft
  (PR / review / reply) is a frozen value with a `word`
  field, empty at preparation. `arm_*_draft(draft, word)`
  records the user's word (empty refuses). Every `post_*`
  checks the word BEFORE touching the runner — unarmed
  posts raise and the runner records zero calls. The word
  is never journaled: records/events carry `armed: true`
  only, never the word's text (pinned by test).
* Line notes honesty: `gh pr review` posts one body, so a
  review draft's line notes ride in that body, listed by
  file and line — delivered, never presented as threaded
  inline comments. Reply honesty likewise: a reply posts
  as a PR comment via `gh pr comment` (no threaded form
  exists on that road); the answered comment's id rides
  in the record.
* Setting: `pr_craft`, ships ON in config_defaults.yaml,
  M-074 gate semantics (off → agent fetch/post roads
  refuse and say so; pure draft maths stays readable;
  malformed stored value raises).

## Build (files)

* NEW `mythic_agent/core/pr_craft.py` (800 lines):
  PullRequest / ReviewComment / LineNote / PRDraft /
  ReviewDraft / ReplyDraft as frozen data; fetch +
  parse (`gh pr view --json` incl. comments/reviews);
  comments_to_tasks; prepare/arm/post for PR, review
  (VERDICTS approve/comment/request_changes → gh flags),
  and reply; setting gate; `/prcraft` parser +
  formatters; `format_pr_craft` worked example over an
  in-module FAKE runner (no live call) exercising every
  public road.
* `mythic_agent/agents/llm.py`: Agent methods
  `pr_craft_status`, `set_pr_craft` (journal-first
  `pr_craft_setting_changed`, save-failure revert +
  `pr_craft_setting_reverted`), `fetch_pull_request`
  (`pr_fetched`), `fetch_review_tasks`
  (`pr_review_tasks_fetched`), `prepare_pr_draft` /
  `post_pr_draft` (`pr_draft_prepared` / `pr_posted`),
  `prepare_review_draft` / `post_review_draft`
  (`pr_review_draft_prepared` / `pr_review_posted`),
  `prepare_reply_draft` / `post_reply_draft`
  (`pr_reply_draft_prepared` / `pr_reply_posted`), plus
  private `_pr_craft_runner` / `_require_pr_craft`.
* `mythic_agent/terminal.py`: `/prcraft` road (show /
  on / off / tasks <n>) + help-string entry.
* `mythic_agent/agents/command_handler.py`: dispatch +
  `_handle_prcraft` (show / setting / tasks).
* `mythic_agent/ui/screens/chat_screen.py`: help line,
  `/prcraft` usage entry, system-command routing list.
* `mythic_agent/data/config_defaults.yaml`: `pr_craft: true`.
* `docs/DEAD_CODE_QUARANTINE.txt`: the six programmatic
  Agent draft/post methods recorded, per the M-024 /
  M-073 / M-074 pattern (they are the gated posting API;
  surfaces call status/set/fetch, drafts/posts are called
  programmatically — and by this slice's tests).
* NEW `tests/test_pr_craft.py`: 43 tests, FakeRunner
  only — no live GitHub call anywhere in the slice.

## Verify (counts from on-disk logs only)

Venv: `PYTHONPATH=$PWD ~/mythic-hammer/repo/.venv-hammer/bin/python`
(Python 3.14, all extras), run from the team-08 worktree.
Logs in the worktree under `.m082-logs/` (untracked).

* `tests/test_pr_craft.py` alone: **43 passed**
  (`.m082-logs/` first run + final runs).
* Final consolidated targeted run — test_pr_craft +
  test_hunk_review + test_github + test_dead_code +
  test_arch_conformance + test_apply_repair +
  test_roadmap_slices + test_part3_gate:
  **205 passed** (`.m082-logs/final-targeted.log`).
* Neighbour sweep (cost_routing, fallback_chain, config,
  config_schema_v2, + the above): **244 passed**
  (`.m082-logs/neighbours.log`); test_policy: **30
  passed** (`.m082-logs/policy.log`).
* Dead-code gate: first targeted run flagged the six new
  Agent draft/post methods; recorded in the quarantine
  (above) and the gate re-ran green (49 passed incl.
  test_pr_craft, `.m082-logs/deadcode2.log`).

## Inventory deltas (coordinator integrates; NOT edited here)

From `.m082-logs/inventory-deltas.log` (config_catalog +
public_api + ownership: 7 failed, 18 passed — every
failure is one of these pending regenerations):

1. **Config catalogue (M-009)**: new setting `pr_craft`
   needs its entry — next id **S-64**, scope top-level,
   type bool, default 'True', source
   mythic_agent/data/config_defaults.yaml, effect text:
   the M-082 gate (drafts send nothing; posts only at the
   user's recorded word; off refuses agent fetch/post).
   The 3 config_catalog failures name only `pr_craft`.
2. **PUBLIC_API.md**: regenerate — live scan finds 2,461
   public names. New names are pr_craft's `__all__`
   (PR_CRAFT_SLICE, PLAIN_EXPLANATION, SETTING_KEY,
   USAGE, VERDICTS, LineNote, PRDraft, PullRequest,
   ReplyDraft, ReviewComment, ReviewDraft, arm_*,
   comments_to_tasks, enabled_from_config,
   fetch_pull_request, fetch_review_comments,
   format_pr_craft, format_pull_request,
   format_setting_change, format_tasks,
   parse_prcraft_args, parse_pull_request,
   parse_review_comments, post_pr, post_reply,
   post_review, prepare_pr, prepare_reply,
   prepare_review, set_enabled, + typing names) and the
   Agent methods listed under Build.
3. **OWNERSHIP.md**: regenerate — new module
   `mythic_agent/core/pr_craft.py` unnamed in the doc +
   freshness (both ownership failures are this).
4. **roadmap_slices.yaml**: flip M-082 queued → done at
   banking.
5. Environment note (not a delta): in the inventory run,
   `test_public_api::test_all_names_exist_and_are_public`
   also failed on the laptop's audio stack in this
   session (PortAudio init: PulseAudio server
   unreachable) — an environment failure of the known
   class, unrelated to M-082 names; the same test's
   inventory half is delta (2).

## Dependency flags

* None on other Wave-1 slices: no shared files with
  teams 01–07/09/10 beyond the standard M-074-pattern
  surfaces (llm.py, terminal.py, command_handler.py,
  chat_screen.py, config_defaults.yaml,
  DEAD_CODE_QUARANTINE.txt), which every team edits in
  its own worktree; integration merges in roadmap order.
* M-083 (Issue-to-slice, team-09) builds on GitHub reads;
  M-082's runner seam + fetch-as-data shape is the road
  it can reuse.

## Discovered issue — commission (not fixed here)

* The legacy TUI `/pr` handler
  (`command_handler._handle_pr`) creates a PR the moment
  it is called, gated only by
  `@requires_permission("github_execute")` — it bypasses
  the M-082 user-word gate that the roadmap's pause-line
  now sets for sending as the user. Evidence:
  `mythic_agent/agents/command_handler.py` `_handle_pr`
  (builds `gh pr create` and runs it directly). Not fixed
  in this slice: changing a pre-existing surface's
  behaviour mid-wave is the coordinator's/Volmarr's call;
  the M-082 `/prcraft` road is the gated one, and its
  PLAIN_EXPLANATION states the law. Recommend: route the
  legacy `/pr` through the draft+word gate or retire it
  in favour of `/prcraft`.

## Lessons

* The pause-line is a data problem before it is a UI
  problem: making the word a field on a frozen draft —
  and checking it before the runner seam — makes "posts
  only at the user's word" provable with a fake runner's
  empty call log, on every send road at once.
* Records must never carry the authorising word itself:
  `armed: true` is the whole journal truth; the word is
  the user's, and it stays out of the session record.
* The dead-code gate flags programmatic Agent APIs by
  design; the quarantine entry (M-024 pattern) is part of
  the slice shape, not an afterthought.

## Banking packet

* Commit on `hammer/team-08`: "M-082 ..." (this log
  included). Never pushed; coordinator banks onto
  `yrsa/feature-roadmap-build` in roadmap order,
  regenerates the shared inventories (deltas above),
  flips M-082 in roadmap data, and runs the full suite
  on the laptop.
* State at hand-off: slice built and targeted-green
  modulo the named inventory deltas. Live posting was
  never exercised, by design — no live GitHub call was
  made by any test or surface in this slice.
