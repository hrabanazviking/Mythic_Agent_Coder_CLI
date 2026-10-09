# Mythic Agent — Release Checklist (S14)

This checklist gates any release candidate of `mythic-agent`. Every item must
be checked against the exact revision being released; a green gate on a
different revision does not count. Evidence (commands, revisions, hosted run
IDs) is recorded in `docs/development/PROGRESS.md`; evidence is not the same
as the claim that gates pass.

## 0. Versioning policy

- The version lives in exactly one place: `mythic_agent/__version__.py`
  (`__version__`).
- `pyproject.toml` resolves the version dynamically via
  `[tool.hatch.version] path = "mythic_agent/__version__.py"`.
- `mythic --version` reports installed metadata when installed, otherwise the
  single-sourced version with a `(source checkout)` suffix.
- Version bump procedure:
  1. Edit `mythic_agent/__version__.py` only — never `pyproject.toml`'s
     version field (there is none; it is `dynamic`).
  2. Add a `CHANGELOG.md` entry under `## [x.y.z] - YYYY-MM-DD`.
  3. Rebuild (`python -m build`) and confirm `mythic --version` reports the
     new version from a fresh install.
- SemVer is used: `MAJOR.MINOR.PATCH`. Pre-1.0, `MINOR` bumps mark
  user-visible behavior changes; `PATCH` bumps mark fixes.
- Do not hand-edit built distributions; always rebuild from the tagged tree.

## 1. Pre-release code gates

- [ ] Working tree clean on the release branch; no uncommitted changes.
- [ ] Release revision pushed to `origin/development`; `git ls-remote`
      confirms the remote HEAD equals the local release SHA.
- [ ] No debug prints, `TODO`-as-code, or experimental flags in the
      shipped code paths.
- [ ] `mythic --help` and `mythic --version` run with no network, no
      credentials, and no optional UI/audio packages installed.
- [ ] `mythic --version` output matches `mythic_agent/__version__.py`.

## 2. Test gates (measured, not claimed)

- [ ] Full local suite green: `python -m pytest` — record pass/fail counts
      and duration on the exact release revision.
- [ ] Suite completes without hangs or manual intervention
      (per-test timeout 120s via `pytest-timeout`).
- [ ] Installed-core gate: `pip install <wheel>` into a fresh environment,
      then run the maintained CLI/subprocess tests from outside the checkout;
      record which optional tests were legitimately skipped (e.g. Textual
      pilot) versus failed.
- [ ] Hosted CI matrix green on the release revision:
      Linux/macOS/Windows × Python 3.10/3.13 (GitHub Actions run ID recorded).
- [ ] Hosted runs include: maintained test suite, wheel+sdist builds, and
      installed-wheel smoke checks.
- [ ] Any failed gate is repaired and re-run on a new revision; the checklist
      is re-executed against the new revision.

## 3. Packaging gates (1.0)

- [ ] `python -m build` produces `mythic_agent-<version>-py3-none-any.whl`
      and `mythic_agent-<version>.tar.gz` with no warnings.
- [ ] Entry points verified from a fresh install:
      - `mythic --help` and `mythic --version` exit 0.
      - `mythic-mcp --help` (or `--version`) exits 0.
- [ ] Wheel contains packaged resources, verified by importing from outside
      the source checkout:
      - persona Markdown profiles under `mythic_agent/resources/characters/`
      - the Mythic Engineering protocol (`engineering.md`)
- [ ] sdist includes tests, docs, top-level Markdown, `LICENSE`, `NOTICE`,
      and `.github/` (see `[tool.hatch.build.targets.sdist]` in
      `pyproject.toml`).
- [ ] README renders: the `readme = "README.md"` field is valid Markdown and
      builds cleanly (hatchling validates at build time; confirm no
      build-time readme warnings).
- [ ] Note: the build backend is hatchling, so `MANIFEST.in` is not used —
      sdist contents are declared in `pyproject.toml` only. Do not add a
      stale `MANIFEST.in`.
- [ ] Fresh editable install check: `pip install -e .` in a clean venv
      succeeds and `mythic --version` reports the release version.

## 4. Security gates

- [ ] No secrets, API keys, tokens, or personal data in the shipped tree or
      in built distributions (search for `sk-`, `ghp_`, `AKIA`, private keys).
- [ ] `mythic doctor` passes its config/secrets checks: credentials are
      redacted from exports, CLI events, logs, and crash reports.
- [ ] Tool policy defaults are safe: `run`/MCP default to read-only;
      human chat/TUI default to ask; trusted mode requires explicit choice.
- [ ] File tools remain workspace-contained (traversal/symlink/Git-metadata
      escapes refused); edits are atomic with journal undo.
- [ ] No implicit destructive Git behavior: no auto-stage, auto-commit, or
      auto-push on tool writes; `/commit` and explicit push only.
- [ ] Dependencies have no known critical advisories for the pinned ranges
      at release time (record the check date/source).

## 5. Documentation gates

- [ ] `CHANGELOG.md` updated: every user-visible change since the last
      release, grouped under Added/Changed/Fixed/Security.
- [ ] `README.md` claims match measured support only — no feature is
      documented as available unless its implementation and gates are
      recorded in `docs/development/PROGRESS.md`.
- [ ] `docs/USER_GUIDE.md` covers install, first run, chat, run, sessions,
      doctor, cache, permissions, providers, MCP, and troubleshooting.
- [ ] `docs/API.md` covers the machine CLI contract (formats, exit codes),
      MCP tools, and the Python entry points, with version notes.
- [ ] `docs/CLI.md` matches the actual CLI flags on the release revision
      (run a diff of `mythic <cmd> --help` output against documented flags).
- [ ] Migration notes added when a release changes config schema, session
      format, or CLI flags/exit codes.
- [ ] `LICENSE`, `NOTICE`, and `THIRD_PARTY_NOTICES.md` are current; modified
      third-party files retain change notices.

## 6. Performance gates (measured)

- [ ] Startup overhead measured and recorded: `python -m mythic_agent.bench`
      (or `mythic_agent/bench.py`) — cold `--help`/`--version` wall time.
- [ ] Import-time budget: `import mythic_agent.cli` does not import Textual,
      Torch, or audio packages (optional front ends lazy-load).
- [ ] Memory footprint recorded from the benchmark module on the release
      revision; no unbounded growth across repeated turns in soak tests.
- [ ] Bounded soak scenario passes: repeated turns, cancellation, malformed
      tool calls, and concurrent agents without leaks or hangs.
- [ ] No invented performance claims: docs quote only measured numbers with
      the revision and machine class.

## 7. Release acceptance gates (the stable harness gates)

- [ ] A fresh core installation runs help, a machine coding task
      (`mythic run --format json`), and terminal chat (`mythic chat`).
- [ ] A TUI install performs the same task and handles approvals and
      interruption.
- [ ] Edit/undo, workspace isolation, transcript resume, policy, provider
      errors, context protocol, concurrent lifecycle, and machine output
      have regression tests — all green.
- [ ] A two-task slice workflow proves checks, push verification, and
      resumption (S12 gate).
- [ ] Human and machine interfaces share the execution contracts in
      `ARCHITECTURE.md`.
- [ ] No known core blocker remains; any missing external/physical platform
      evidence is named in the release notes, not silently omitted.

## 8. Sign-off

- [ ] All checked items above are true of the exact released revision.
- [ ] Release notes published; the release commit/tag is recorded in
      `docs/development/PROGRESS.md` with hosted CI run IDs.
- [ ] Post-release: monitor the issue tracker for install/platform reports
      for 72 hours before starting the next slice batch.

---

## Measured results — local gate run, 2026-10-09

Run against the working tree at parent commit `da20452` (development),
Python 3.13.13, Linux, per-test timeout 120s:

| Gate | Result |
|---|---|
| `python -m pytest` (full suite, 174s) | **14 failed, 533 passed, 1 skipped — NOT GREEN** |
| `python -m build` | PASS (wheel + sdist built; dynamic version resolved to 0.1.0; hatchling reported no README warnings) |
| Wheel contents | PASS: 44 character files, `engineering.md`, `__version__.py`, both entry points (`mythic`, `mythic-mcp`) |
| sdist contents | PASS: docs (13), tests (45), 49 Markdown files, LICENSE + NOTICE |
| Fresh editable install (`pip install -e .`) | PASS in workspace-hosted venv: `mythic --version` → 0.1.0, `--help` exit 0, `mythic doctor` runs offline with correct per-check statuses. `mythic-mcp` entry point registered; importing `mcp_server` without the `mcp` extra raises a clean `ImportError` directing the user to `pip install mcp` (intended optional-extra behavior). |
| `mythic_agent.bench` | startup `--help` 0.628s (3 runs), `import mythic_agent.cli` 0.24s, import peak RSS 8049.9 KB |
| Hosted CI matrix | pending release revision |

**Failing tests (must be green on a clean, committed revision before any
release):**

- `tests/test_review.py` (3 tests) — `NameError: name 'review_command' is
  not defined` in `mythic_agent/cli.py`; the `review` subcommand handler
  references a function that does not exist in the current working tree
  (another slice's in-progress change).
- `tests/test_provider_adapters.py` (3 tests) and `tests/test_providers.py`
  (1 test) — provider/doctor-check failures around missing keys and the
  loopback fixture; in-progress provider work, not release-blocker for the
  core offline gates but must be resolved or explicitly recorded.
- `tests/test_knowledge_graph.py` (3), `tests/test_long_term.py` (1),
  `tests/test_docgen.py` (1), `tests/test_markdown.py` (1),
  `tests/test_policy.py` (1, `_handle_commit` mutator) — failures in other
  in-progress slices' areas.

Also observed (working-tree, 2026-10-09): `mythic doctor` from a fresh
install reports a `sessions` warning —
`SessionStore.__init__() missing 2 required positional arguments:
'workspace' and 'state_root'` — indicating an in-progress session-store API
change in the working tree. All other checks behaved correctly offline.

The earlier `-x` run was stopped after
`tests/test_cli.py::test_resumed_completed_tools_are_not_executed_again`
failed with a transient `NameError: name 'doctor' is not defined` from a
mid-edit `cli.py`; that test passed in the full re-run. The suite must be
re-run green on a clean, committed revision before release sign-off; record
the final results in `docs/development/PROGRESS.md`.
