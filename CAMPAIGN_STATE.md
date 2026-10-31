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
- The clone was shallow (depth 1) at the opening; **`git fetch
  --unshallow origin` succeeded 2026-10-30 ~21:05 EDT** (transport
  healed) and the clone now has full history. The two ownership
  tests that read full git history pass again, and
  `docs/OWNERSHIP.md` was regenerated truthfully in M-001.
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
| M-001 | The Feature Census (matrix as data, 10 rivals) | **DONE** — banked 2026-10-30 21:2x EDT (`b599572`): `mythic_agent/data/feature_census.yaml` (38 features × 11 rivals; YAML because the repo gitignores `*.json` and its data shelf ships YAML) + validated loader `mythic_agent/core/feature_census.py` + 12 tests. Mythic tally from the matrix (counted from the data): 13 HAVE, 1 BETTER (cost honesty), 15 PARTIAL, 9 MISSING — 24 gap rows, every one carrying its owning slice |
| M-002 | The Concordance | **DONE** — banked this opening; `docs/CONCORDANCE_MIMISBRUNNR_FEATURE_ROADMAP.md` |
| M-003 | The Gap Audit | **DONE** — banked 2026-10-30 (`e689fd8`): `mythic_agent/data/gap_audit.yaml` + validated loader `mythic_agent/core/gap_audit.py` + 10 tests. All 24 census gaps traced to an owning module (existing verified present / proposed verified absent) with roadmap part. The 5 unclassified baseline failures are classified WITH evidence in the audit data: 2 product defects FIXED in-slice (explicit empty model name silently replaced by the default in the Anthropic+Google providers; truncate_text marker hard-cut overshooting an exact-backend budget), 1 test-timing (the TUI approval test's single early click raced the approval modal's mount/layout in full-suite context — hardened in-slice with a bounded click-retry, assertions unchanged), 1 environment (coverage ratchet: `coverage` absent from the baseline venv — healed in the untracked venv, ratchet re-verified green solo). Final clean full suite (2026-10-30 22:15 EDT, log hidden_files/m003-fullsuite-2212.log): **1428 passed, 2 failed, 1 skipped** (1431 collected, 295 s) — the 2 failures are exactly the long-classified environment cases (PortAudio public-api import; tiktoken-premise estimator test), and all 5 formerly-unclassified failures pass. HONESTY NOTE: two earlier suite summaries this tick were corrupted by concurrent same-tree runs and diverged background outputs (a contaminated 9-failure run, and a false 1433/2/1 excerpt whose on-disk log actually read 1427/3/1); both were discarded — only numbers read from an on-disk log in a foreground check are recorded here. |
| M-004 | UX Principles charter | **DONE** — banked 2026-10-30 (`a8d38df`): `mythic_agent/data/ux_charter.yaml` (9 principles, K-01–K-09; the roadmap's 5 named mandates carried exactly once each by K-01–K-05, plus honesty-over-polish, every-error-carries-its-fix, local-sovereignty/secrets-in-Kista, calm-by-default) + validated loader `mythic_agent/core/ux_charter.py` (sequential K-numbering, mandate-exactly-once, every review_check a question, applies_to naming real parts) + 11 tests; OWNERSHIP.md + PUBLIC_API.md regenerated in-slice (1149 → 1162 public names). Full suite (2026-10-30, log hidden_files/m004-fullsuite-final.log): **1439 passed, 2 failed, 1 skipped** (1442 collected) — the 2 failures are exactly the long-classified environment cases (PortAudio public-api import; tiktoken-premise estimator test). NOTE: this tick's first suite run exposed 3 real in-slice failures (ownership map + public-api inventory stale for the new module), fixed in-slice by regenerating both docs; that run's delivered stdout tail (1439/2/1) was a diverged view and was NOT trusted — only the on-disk log's 1436/5/1 was acted on, and the final numbers above are likewise read from the on-disk final log. |
| M-005 | The Method Charter in-app | **DONE** — banked 2026-10-30 (`1224ecd`): `mythic_agent/data/method_charter.yaml` (Volmarr's six Forge Protocol plugs summarised in stack order as tenets F-01–F-06, each with directives Part IX's engine can execute; F-05 carries the 8 pause lines exactly; plus the definition of done) + validated loader `mythic_agent/core/method_charter.py` (stack order + sequential F-numbering + every tenet carries directives + pause lines exactly and only on the autonomy tenet) + 12 tests; OWNERSHIP.md + PUBLIC_API.md regenerated in-slice (1162 → 1176 public names). Full suite (2026-10-30, log hidden_files/m005-fullsuite.log): **1451 passed, 2 failed, 1 skipped** (1454 collected, 317 s) — the 2 failures are exactly the long-classified environment cases (PortAudio public-api import; tiktoken-premise estimator test). In-slice lessons applied from earlier slices: render_markdown genuinely uses `directives()`/`pause_lines()` (dead-code gate), and the slice was committed before the ownership regen (generator needs git history for the new module). |
| M-006 | Terminology bridge | **DONE** — banked 2026-10-30 (`7956921`): `mythic_agent/data/terminology.yaml` (22 terms, T-01–T-22: every field term — checkpoint→Waymark, hook→Trigger-rune, skill→Craft-plug, plan mode→The Drawing Board, plus the census vocabulary — given its Mythic name) + validated/searchable loader `mythic_agent/core/terminology.py` (`find()` resolves common name, Mythic name, and aliases normalised; validator enforces sequential T-numbering, the roadmap's 4 named terms exactly once, and no name/alias collision that would make a search ambiguous) + 13 tests; OWNERSHIP.md + PUBLIC_API.md regenerated in-slice (1176 → 1189 public names). Full suite (2026-10-30, log hidden_files/m006-fullsuite.log): **1464 passed, 2 failed, 1 skipped** (1467 collected, 392 s) — the 2 failures are exactly the long-classified environment cases (PortAudio public-api import; tiktoken-premise estimator test). |
| M-007 | Baseline freeze | **DONE** — banked 2026-10-30 (`da80dc3`): the "before" evidence for Part XI frozen as validated data — `mythic_agent/data/baseline_freeze.yaml` + loader `mythic_agent/core/baseline_freeze.py` + 13 tests. Contents: (1) full suite counted fresh this tick on the pre-slice tree (log hidden_files/m007-baseline-fullsuite.log): **1464 passed, 2 failed, 1 skipped** (1467 collected, 347.9 s) — the 2 failures are exactly the long-classified environment cases, each named+classified in the freeze data (validator enforces: suite arithmetic closes, every counted failure named); (2) startup profile measured fresh: `python -m mythic_agent.cli --help` ×5 runs [0.793, 1.092, 0.335, 1.373, 0.785]s, median 0.793s, recorded WITH its contention context (several campaigns share this VM; the 2026-10-09 quiet-machine profile was 0.19–0.22s); (3) scripted end-to-end task: `scripts/baseline_e2e.py` (stdlib-only, loopback fake provider, steps E-01–E-04: one-shot reply / read-only write refusal exit 3 / trusted write executes / resume+sessions) — verified standalone from the on-disk report (hidden_files/m007-e2e-report.json): **4/4 passed, exit 0**, and re-run live inside the slice's test. OWNERSHIP.md + PUBLIC_API.md regenerated in-slice (1189 → 1202 public names). Full suite after banking (log hidden_files/m007-fullsuite.log): **1476 passed, 3 failed, 1 skipped** (1480 collected, 363.7 s) — the 2 known-env failures plus ONE load flake: `test_startup_determinism::test_doctor_checks_deterministic` failed because the doctor workspace message embeds free disk space, which crossed a 0.1 GB boundary (106.7→106.8 GB) between the test's two back-to-back runs under concurrent multi-campaign disk load; solo re-run passes (31 passed incl. all M-007 tests + ownership), both inventory gates pass solo. LESSON SEALED IN THIS SLICE: a backgrounded run's delivered stdout excerpt this tick showed an e2e report (durations ~3–7 s, all-pass) that the ON-DISK report contradicted (durations 17–24 s, E-04 failed — the script's original E-04 expectation was wrong: each `run` creates its own session, so `sessions` correctly lists 3, not 1; fixed in-slice in script + freeze data). Only on-disk logs/reports were trusted, per the transport-war rule. |
| M-008 | Benchmark task pack v1 | **DONE** — banked 2026-10-30 (`e91a21b`): `mythic_agent/data/benchmark_tasks.yaml` (20 real tasks, B-01–B-20: 4 each bugfix / feature / refactor / test-writing / docs; every task carries its throwaway seed repo, a reference solution, hidden grading tests, and a ≥2-criterion diff rubric) + validated loader `mythic_agent/core/benchmark_tasks.py` (`materialize()` writes a seed or solved repo with grading tests dropped in) + 54 tests. The pack's yardstick property is proven live for every task: grading FAILS on the seed alone and PASSES on seed+solution, and the four test-writing solutions' own suites pass. OWNERSHIP.md + PUBLIC_API.md regenerated in-slice (1202 → 1218 public names). Full suite (log hidden_files/m008-fullsuite.log): **1531 passed, 2 failed, 1 skipped** (1534 collected, 266 s) — the 2 failures are exactly the long-classified environment cases (PortAudio public-api import; tiktoken-premise estimator test). Transport note: this tick's first full-suite run died with its shell session at ~56% (log incomplete, no process left); the counted run was relaunched detached (setsid) and read from the on-disk log only. |
| M-009 | Config archaeology | **DONE** — banked 2026-10-30 (`4e3254f`): `mythic_agent/data/config_catalog.yaml` + validated loader `mythic_agent/core/config_catalog.py` + 14 tests. Catalogue counted from the tree: 35 settings (16 top-level from config_defaults.yaml + 2 github.* + 13 runtime from runtime_defaults.yaml + 4 config-managed keys from CONFIG_SCHEMA), 16 environment variables (every literal env name in the package's env-reading modules, incl. provider key envs; MYTHIC_HEADLESS_MODE and MYTHIC_SANDBOX_NO_NETWORK honestly recorded as written-not-read markers), 10 files (3 package-data, user config, legacy config, lock, recovery backups, status dir, agent.log, workspace instruction files with all 7 INSTRUCTION_FILENAMES). Tests cross-check the catalogue against the live defaults files, CONFIG_SCHEMA, a live env-var scan, and the instruction filenames — a new setting/key/var cannot land uncatalogued. The catalogue is the compatibility contract for Part VIII. OWNERSHIP.md + PUBLIC_API.md regenerated in-slice (1218 → 1231 public names). Full suite (log hidden_files/m009-fullsuite.log): **1545 passed, 2 failed, 1 skipped** (1548 collected, 555 s) — the 2 failures are exactly the long-classified environment cases (PortAudio public-api import; tiktoken-premise estimator test). In-slice fix: the dead-code gate flagged `env_names()` — render_markdown now builds its env section from that accessor. |
| M-010 | Session archaeology | **NEXT** |
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

*Post-M-001 verification (2026-10-30 ~21:20 EDT): full suite ran
**1412 passed, 8 failed, 1 skipped** (1421 collected, 469 s). Of the
8 failures: 7 are baseline-classified (PortAudio env; the estimator
premise inversion; 5 still-unclassified — M-003's queue, unchanged)
and 2 baseline failures are HEALED (both ownership tests, via the
unshallow above). The 1 new failure was M-001's own
`test_no_new_dead_code_beyond_quarantine` (two census helper methods
referenced only from tests): fixed in-slice before banking
(`render_markdown` now renders the gap list from `gaps()`; the
redundant `by_state` was removed) and re-verified in the targeted
set — 52 passed with the PortAudio env case the sole failure.*

*State as of the campaign opening, 2026-10-30 ~21:05 EDT; M-001
banked by the keeper the same night (see ledger).*
*Post-bank verification (same night): after the M-002 + opening
commits, the doc/ownership/public-api subset re-ran — 63 passed,
3 failed, the failures being exactly the three already-classified
environment cases above. The opening commits broke nothing.*
