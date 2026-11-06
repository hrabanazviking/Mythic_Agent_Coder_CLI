# TEAM_LOG — Team 10 · M-084 Multi-file change sets

Hammer Campaign Wave 1, team-10 worktree (`hammer/team-10`,
opened at `b58517b`, verified by hostname + rev-parse +
branch before any work). Crew cycle run as the lead's
internal six-role cycle (Charter → Design → Build → Verify
→ Record → Bank-prep); depth 2/2 cannot nest sub-crews —
stated plainly per the brief.

## Charter (intent + acceptance)

Roadmap's words (roadmap_slices.yaml M-084, Part IV):
"a change set is a named, reviewable unit across files
with its test evidence attached." Acceptance: a named set
groups one edit per file across many files; each file is
reviewed (accept/reject) on its own; the set applies
through the existing strict roads with nothing landing
from a refused set; its test evidence (command, counted
outcome, log reference) rides the set as data.

## Design (settled from the tree, M-074 shape)

* Pure core `mythic_agent/core/change_sets.py`, composing
  what already shipped — never re-deriving it:
  - per-file edits are M-071 concrete formats
    (whole-file / unified-diff / search-replace), judged
    by M-071's `apply_edit` unchanged (no fuzz, ever);
    the architect split is a plan, not a payload, and can
    never be a set member.
  - review mirrors M-074 one level up: per-file
    accept/reject decisions; every file must be decided
    (an undecided file refuses the apply and is named);
    rejecting one file never kills the rest; rejecting
    everything is an honest no-change outcome.
  - one file, one edit per set (a duplicate path refuses
    at construction — no honest order exists; sequence
    two sets instead).
  - atomic planning, journaled writing: the pure layer
    plans the whole set in memory against the files'
    true current texts — one stale file refuses the
    whole set and nothing is written; the Agent then
    writes the clean plan through the existing
    EditJournal road, one journaled write per file
    (undoable like any agent edit).
  - test evidence as data: `TestEvidence` carries the
    command, passed/failed/skipped counts, and a log
    reference; counts are validated at construction
    (non-negative whole numbers); the verdict is
    COMPUTED from the counts (any failure → "failed";
    zero tests → "no tests ran", never "passed"). A set
    with no evidence records exactly that — absence is
    never dressed as a pass.
* Agent roads (`mythic_agent/agents/llm.py`):
  `change_set_status` / `set_change_sets` (journal-first
  `change_set_setting_changed`, save-failure revert —
  the M-072..M-074 pattern verbatim), `preview_change_set`
  (build + validate + evidence record, no disk touched),
  `apply_change_set` (gate-checked; session event
  `change_set_applied` under the set's name with counts
  and the evidence record).
* Surfaces sharing one parser + formatters:
  `/changeset` on the terminal road
  (`mythic_agent/terminal.py`, incl. the /help string)
  and the TUI road (`command_handler._handle_changeset`
  + chat-screen help line, usage text, and routing).
* Setting `change_sets` ships ON in
  `mythic_agent/data/config_defaults.yaml` (beside
  `hunk_review`), gate semantics identical to M-074.

## Files

* NEW `mythic_agent/core/change_sets.py` (pure layer)
* NEW `tests/test_change_sets.py` — 47 tests
* `mythic_agent/agents/llm.py` — 4 Agent methods
* `mythic_agent/terminal.py` — /changeset branch + help
* `mythic_agent/agents/command_handler.py` — dispatch +
  `_handle_changeset`
* `mythic_agent/ui/screens/chat_screen.py` — help line,
  usage entry, system-command routing
* `mythic_agent/data/config_defaults.yaml` —
  `change_sets: true`
* `docs/DEAD_CODE_QUARANTINE.txt` — one entry added
  (see Lessons)
* `TEAM_LOG.md` — this file
* Logs in this worktree: `m084-targeted.log`,
  `m084-neighbours.log`, `m084-inventory.log`,
  `m084-deadcode-fix.log` (uncommitted evidence)

## Verify (counts from on-disk logs only)

* Slice tests: **47 passed** (`m084-targeted.log`).
* Neighbour regression set (hunk_review, edit_formats,
  hash_anchored, apply_repair, roadmap_slices):
  **236 passed** (`m084-neighbours.log`).
* Dead-code gate after the quarantine fix, re-run with
  the slice tests: **53 passed** (`m084-deadcode-fix.log`).
* Inventory set (`m084-inventory.log`): 23 passed,
  8 failed — every failure a named integration delta
  below, none a slice defect.

## Inventory deltas (for the coordinator — NOT edited here)

1. **Config catalogue (M-009):** add setting **S-64**
   `change_sets`, top-level bool, default True, source
   `mythic_agent/data/config_defaults.yaml`, effect text
   = the module's PLAIN_EXPLANATION road (gate on:
   named multi-file sets reviewed per file, planned
   atomically through M-071's strict appliers, written
   via EditJournal, evidence carried as data with a
   computed verdict; /changeset shows + toggles the
   gate, journaled with save-failure revert). Until
   then `tests/test_config_catalog.py` fails 3 tests
   (`change_sets` uncatalogued in defaults + schema
   checks) — expected delta, named not chased.
2. **PUBLIC_API.md:** regenerate — new public names in
   `mythic_agent.core.change_sets` (CHANGE_SETS_SLICE,
   DECISIONS, PLAIN_EXPLANATION, SETTING_KEY, USAGE,
   BoolChange, ChangeSet, ChangeSetOutcome, FileEdit,
   TestEvidence, apply_change_set, attach_evidence,
   decide, enabled_from_config, format_change_set,
   format_change_sets, format_evidence,
   format_setting_change, make_edit, make_evidence,
   parse_changeset_args, set_enabled, start_change_set)
   + Agent methods change_set_status / set_change_sets /
   preview_change_set / apply_change_set. Until then
   `tests/test_public_api.py` fails 2 tests — expected.
3. **OWNERSHIP.md:** regenerate after this slice commits
   (the generator needs git history for the new module —
   it currently raises ZeroHistoryError on
   `change_sets.py`, the known pre-commit state from
   M-005's lesson). Until then `tests/test_ownership.py`
   fails 2 tests — expected.
4. **Roadmap data:** flip M-084 to done (74 → 75) in
   `mythic_agent/data/roadmap_slices.yaml` at banking.
5. **CAMPAIGN_STATE.md:** M-084 ledger row at banking.

## Dependency flags

* Builds on M-071 (format appliers), M-072/M-073
  (composition-compatible; anchored/repair roads remain
  per-file and unchanged), M-074 (review pattern).
  No slice in Wave 1 depends on M-084. M-085
  (rename/move) is independent of this slice.
* No new dependencies; stdlib + existing package only.

## Lessons

* Dead-code gate: `preview_change_set` is an Agent API
  surface exercised by tests only — the gate flagged it
  as the one new dead item (`apply_change_set` is
  referenced in-package). Remedy followed M-074's
  precedent exactly: recorded in
  `docs/DEAD_CODE_QUARANTINE.txt`
  (llm.py:1555:preview_change_set:method); gate green on
  re-run. `change_set_status`/`set_change_sets` are
  referenced by both surfaces and needed no entry.
* Transfer war, relearned: 1500-byte base64 chunks of
  the gzipped test file failed sha256 twice (whole
  writes discarded, nothing bad landed); 750-byte
  pieces, each a standalone sha256-verified file.write,
  then on-device concatenation + whole-file sha256,
  landed clean — one 750-byte edits piece still slipped
  twice and landed at 375-byte sub-pieces. The sha256
  guard on every hop is load-bearing.
* The ownership generator's ZeroHistoryError on an
  uncommitted new module is the expected pre-banking
  state, not a defect — it heals at commit + regen,
  exactly as recorded since M-005.

## Banking packet

* Branch `hammer/team-10`, one commit, style
  "M-084 ..." (see git log). Never pushed.
* Coordinator: integrate in roadmap order after
  M-075..M-083; apply the five inventory deltas above;
  run the full suite on the laptop; the three
  config-catalogue + two public-api + two ownership
  failures listed here must heal at regen, and any
  other failure is new.

* Final combined run on the finished tree (slice + neighbours + dead-code gate + roadmap data): **289 passed** (`m084-final.log`).
