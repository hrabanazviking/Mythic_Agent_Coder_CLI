# TEAM_LOG — team-09 — M-083 Issue-to-slice

Crew note: the six Mythic roles ran as this lead's internal
cycle (sub-agents cannot nest at depth 2/2): Charter ->
Design -> Build -> Verify -> Record -> Bank-prep.

## Charter (intent + acceptance)
Roadmap: "a GitHub issue (or Samverk issue, Part X) becomes
a planned slice with acceptance checks drafted from its
text." Acceptance: (1) an issue fetched through a source
seam becomes a planned slice in the house format (M-017
roadmap-slice shape: title/summary/status, status
"planned"); (2) every acceptance check is drafted from the
issue's own text — task-list items, bullets under an
acceptance heading, or the title as fallback — and carries
its verbatim source excerpt; untraceable checks refuse;
(3) GitHub fetches now via the existing gh road; the
Samverk source is a named seam for Part X (M-242) that
refuses honestly, its internals never invented; (4) the
M-074 campaign shape: pure core + Agent methods + terminal
& TUI surfaces sharing one parser/formatters + setting.

## Design (settled from the tree)
- Existing GitHub road: integrations/github.py (gh wrapper,
  list_issues/create_pr; no single-issue fetch) — added
  view_issue (gh issue view --json ...,body,...).
- Slice shape: core/roadmap_slices.py RoadmapSlice
  (title/summary/status; STATUSES done|queued) — planned
  slices use status "planned", deliberately outside the
  ledger's statuses so they can never be mistaken for the
  approved road. A planned slice is product output data,
  never an edit to roadmap_slices.yaml.
- Part X Samverk: M-242 "Samverk bridge ... once Samverk's
  own road provides the surfaces" — the seam registry
  (SOURCES in core/issue_slice.py) names github (available,
  road M-083) and samverk (unavailable, road M-242).

## Build (files)
- NEW mythic_agent/core/issue_slice.py (sha256
  d94305c8...): IssueRecord, AcceptanceCheck,
  PlannedSlice, draft_acceptance_checks,
  validate_checks_trace, plan_slice, the source seam
  (available_sources/fetch_issue, injectable fetcher),
  gate (issue_to_slice, ships ON), /issueslice parser +
  formatters incl. a worked sample on the show surface.
- mythic_agent/integrations/github.py: + view_issue.
- mythic_agent/agents/llm.py: + issue_slice_status /
  set_issue_slice (journal-first, save-failure revert) /
  plan_issue_slice (seam fetch + plan + journal
  issue_slice_planned) / draft_slice_from_issue.
- mythic_agent/agents/command_handler.py: + /issueslice
  routing + _handle_issueslice (show/setting/plan).
- mythic_agent/terminal.py: + /issueslice branch + help.
- mythic_agent/ui/screens/chat_screen.py: + help line,
  usage entry, system-command routing for /issueslice.
- mythic_agent/data/config_defaults.yaml: issue_to_slice:
  true.

## Verify (counts from on-disk logs in this worktree)
- py_compile of all 6 touched modules: OK.
- Show-surface smoke (log /tmp/m083/smoke.log on device):
  format_issue_slice({}) renders the seam registry and a
  sample issue planned with 3 traced checks.
- m083-targeted.log: tests/test_github.py +
  tests/test_hunk_review.py — 58 passed (regression: the
  shared files this slice touched did not break M-074 or
  the gh road).
- m083-catalogue.log: tests/test_config_catalog.py —
  11 passed, 3 failed, ALL 3 the named inventory delta
  below (KeyError 'issue_to_slice').

## Inventory deltas (coordinator, at integration)
- config_catalog.yaml: add setting S-64 issue_to_slice
  (bool, top-level, default True, source
  config_defaults.yaml, M-083 effect text per
  PLAIN_EXPLANATION in core/issue_slice.py). Until then
  test_config_catalog.py fails exactly 3 tests (above).
- OWNERSHIP.md / PUBLIC_API.md: regenerate — new module
  mythic_agent/core/issue_slice.py, new Agent methods
  (issue_slice_status, set_issue_slice, plan_issue_slice,
  draft_slice_from_issue), github.view_issue.
- roadmap_slices.yaml: flip M-083 to done at banking.
- CAMPAIGN_STATE.md: ledger row for M-083.

## Remainder — stated exactly
- tests/test_issue_slice.py (the slice's own test file,
  ~46 tests mirroring test_hunk_review.py: pure drafting
  + trace refusal, seam incl. Samverk refusal, stubbed
  view_issue, Agent gate/plan/journal, terminal + TUI +
  chat routing, defaults) was authored but its transfer
  to the laptop was interrupted: one chunk of the
  compressed file was removed by a safety filter mid-
  transfer and, per instruction, was not re-sent or
  recreated. Chunk p_ts_0 landed verified; the rest was
  not sent. OWED: land tests/test_issue_slice.py and run
  it (expected green against the shipped code; the
  catalogue assertion was deliberately left out of it —
  S-64 is the delta above). Until it lands, the slice's
  verification stands on the smoke + regression counts
  above, NOT on its own test file. This is the one open
  item; everything else in the slice is built and wired.

## Dependency flags / lessons
- Depends on: Slice 36 gh road (present), M-017 shape
  (present). Part X M-242 owns the Samverk fetcher when
  its road lands: replace _samverk_fetcher's refusal.
- Transfer lesson (re-proven): 2000-byte base64 chunks
  slipped in re-emission (whole-file sha mismatch twice);
  500-byte pieces with per-piece sha256 landed 36/36
  clean. Keep pieces at ~500 bytes for this road.
- No Docker used. No README touched. Nothing pushed.
