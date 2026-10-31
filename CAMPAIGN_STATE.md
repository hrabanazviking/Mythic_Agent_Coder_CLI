# Campaign State — Mythic Agent Coder: The All-Features Road

*The keeper's resume point. Keep current after every slice.
Campaign opened 2026-10-30 by Volmarr's word ("push the mythic coder
roadmap to the repo and then you can begin the slices for that one
too"). Portable plain markdown by design — any agent (Yrsa's crews or
Volmarr's Hermes) can pick this campaign up from this file alone.*

## The roads

- **All-Features Roadmap (governing):** 272 slices, 11 parts,
  M-001–M-272. Shelf copy:
  `~/workspace/your_files/mythic-coder/MYTHIC_CODER_FEATURE_ROADMAP_2026-10-30.md`;
  in-repo copy filed on `main` at `d06c009` (docs/).
- **Mimisbrunnr Roadmap (elder, Volmarr's own):** 500 slices,
  20 campaigns, MIM-001–MIM-500, in-repo at
  `MYTHIC_AGENT_CODER_CLI_500_SLICE_ULTIMATE_MIMISBRUNNR_ROADMAP.md`.
  Progress: **MIM-001–050 DONE** (receipted Oct 2026,
  `docs/FORGE_RECEIPT_021_025.md`, `docs/FORGE_RECEIPT_041_050.md`);
  MIM-051–500 carved, unstarted.
- **The binding:** `docs/CONCORDANCE_MIMISBRUNNR_FEATURE_ROADMAP.md`
  (slice M-002, banked this opening). Citation discipline: elder
  slices MIM-###, younger slices M-###. Conflicts are listed there,
  never silently resolved; the one supersession (MIM-142 container
  sandbox vs the no-Docker law) is recorded with its authority.

## Working tree

- Clone: `~/workspace/mythic-coder-build/`, branch
  **`yrsa/feature-roadmap-build`** off `development`
  (`2068fdab54562f4b9ebe26284e34d8667f8717bc`). Default branch is
  `development`; `main` (`d06c0098`) rides one commit ahead (the
  roadmap filing). **Nothing is pushed** — build pushes await
  Volmarr's word.
- The clone is **shallow (depth 1)** with its object store completed
  from the parent's push clone — see "Transport war" below. When
  GitHub transport is healthy, run `git fetch --unshallow origin`
  (this also repairs the two ownership tests that read full git
  history).
- Baseline venv: `.venv-baseline/` in the tree (untracked) — Python
  3.12 with pytest + all optional extras installed from PyPI
  (2026-10-30). Reuse it for suite runs; delete it freely.

## Baseline (counted 2026-10-30, this VM, full extras)

Full suite (`pytest tests/`, per-test timeout 120 s):
**1399 passed, 9 failed, 1 skipped — 1409 collected, 441 s.**
(The repo's own Oct 2026 gate record was 1147/2/0; the suite has
grown ~260 tests since. Without the extras installed, 26 test files
fail collection outright — dependencies are part of the baseline.)

The 9 failures, classified:
- **Environment (proven, 4):**
  `test_public_api::test_all_names_exist_and_are_public` (PortAudio
  system library absent → `mythic_agent.core.audio` import fails);
  `test_ownership::test_ownership_names_come_from_real_git_log` and
  `test_ownership::test_doc_is_fresh` (shallow clone — full history
  absent); `test_context_compiler::
  test_estimator_heuristic_backend_when_tiktoken_absent` (premise
  inverted — tiktoken IS installed here).
- **Unclassified (5) — the campaign's first investigation queue:**
  `test_provider_protocol::test_empty_model_name_raises_provider_error`
  [AnthropicProvider] and [GoogleProvider] (most code-smelling of
  the nine; belongs to Part II's road);
  `test_context_compiler::test_truncate_text_boundary_behavior`;
  `test_coverage_assault::test_providers_coverage_ratchet`;
  `test_policy::test_tui_approval_controls_the_shared_executor_and_cancels`
  (possibly load/timing — this VM runs several campaigns at once).
  Per the never-leave-a-bug law these are commissioned, not noted:
  M-003's gap audit classifies them; any proven defect is fixed in
  its owning part's first slice or commissioned on the spot.

## Slice ledger — Part I (The Census & The Charter)

| Slice | Intent | Status |
|---|---|---|
| M-001 | The Feature Census (matrix as data, 10 rivals) | **NEXT** — inputs staged: roadmap §2 census summary; `docs/REPO_CENSUS.md` is the repo-side mirror to reconcile against |
| M-002 | The Concordance | **DONE** — banked this opening; `docs/CONCORDANCE_MIMISBRUNNR_FEATURE_ROADMAP.md` |
| M-003 | The Gap Audit | queued (classifies the 5 unclassified baseline failures en route) |
| M-004 | UX Principles charter | queued |
| M-005 | The Method Charter in-app | queued |
| M-006 | Terminology bridge | queued |
| M-007 | Baseline freeze | **PARTIAL** — the counted baseline above is its first evidence; the scripted end-to-end task recording is still owed |
| M-008 | Benchmark task pack v1 | queued |
| M-009 | Config archaeology | queued |
| M-010 | Session archaeology | queued |
| M-011 | The arcanum review | queued |
| M-012 | Dependency census | queued (the baseline venv work above is raw material) |
| M-013 | Platform truth table | queued — one cell earned this opening: Linux x86_64 install/run = PROVEN (with extras); voice = NOT PROVEN (no PortAudio) |
| M-014 | Rivals' config import study | queued |
| M-015 | Telemetry honesty review | queued |
| M-016 | Accessibility baseline | queued |
| M-017 | The roadmap made data | queued |
| M-018 | Part I gate | queued |

Parts II–XI: untouched. The campaign runs Part I in order; the
keeper takes the next unbanked slice from this ledger each tick.

## Transport war (opening night, recorded so no one re-fights it)

GitHub bulk transfer from this VM was severely degraded on
2026-10-30 (several campaigns sharing the box): full clones failed
or corrupted (`fetch-pack: invalid index-pack output`), single
requests stalled past 45 s, and long-running shell sessions'
filesystem views repeatedly diverged from the foreground view —
**several plausible-looking outputs from backgrounded commands were
wrong** (wrong HEADs, wrong trees, files that do not exist). What
worked, and is the standing recipe until transport heals:
`git ls-remote` for truth (foreground), a `--depth 1
--filter=blob:none` fetch for refs+trees (seconds), and completing
the object store from a sibling clone's `.git/objects` on local
disk. PyPI was unaffected and fast. Every number in this file was
re-measured in the foreground or read from a checked-out file.

## Laws in force (from the roadmap + Volmarr's standing rulings)

Mythic Engineering is the method, not a mode · plain language first ·
local sovereignty (no feature requires one vendor; Project Aesir is
a first-class provider-to-be, M-025) · secrets live in Kista · the
honesty machinery stays (unknown = unknown, NOT PROVEN is a result) ·
nothing already shipped is removed · the Design Lawbook binds the
TUI · **no Docker, ever** · README.md is never overwritten ·
per-slice commits banked locally; pushes only at Volmarr's word ·
every discovered bug fixed in scope or commissioned on the spot.

*State as of the campaign opening, 2026-10-30 ~21:05 EDT.*
