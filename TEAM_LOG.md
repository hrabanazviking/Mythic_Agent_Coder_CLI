# TEAM_LOG — Team 05 — M-079 README and licence guardians

## Charter (intent + acceptance)
Roadmap M-079: "the coder *refuses* to overwrite a README
(Volmarr's standing law) or touch licence files without
explicit word; the refusal is built into the edit layer."
Acceptance: the refusal proven on EVERY edit road the layer
serves (M-071 formats, M-072 anchored, M-073 repair,
M-074 hunk review, write/replace tool roads, and the direct
EditJournal roads the LSP / structural-rewrite / formatter
roads also ride); in-place README modification stays
possible; the "explicit word" is a user-given setting.
Crew cycle run as one agent's internal six roles (depth 2
cannot nest sub-agents — stated plainly, per instructions).

## Design (settled from the tree)
- Every edit road writes through one place:
  `mythic_agent/core/edits.py` `EditJournal.write`. The
guardian judgement lives THERE (plus classification at the
  agent layer), not in any one surface. LSP workspace edits,
  structural rewrite, and the formatter covenant call
  `journal.write` directly and are guarded by the same
  verdict (unclassified write to an existing file =
  overwrite; to a new file = create).
- Guarded names (basename, any depth, case-insensitive):
  README / README.<anything> -> kind `readme`;
  LICENSE, LICENCE, COPYING, NOTICE with any extension or
  suffix ('.', '-', '_' — LICENSE.md, LICENSE-MIT,
  COPYING.LESSER, NOTICE.txt) -> kind `licence`.
  NOTICES.md and LICENSES/<file> are honestly NOT guarded
  (basename law, pinned by tests).
- Verdict matrix (pure `judge()` in the new module):
  * readme + overwrite/delete: REFUSED — unless the
    explicit word is on record, or (overwrite only) the
    current text is a barely-anything stub (<=5 non-empty
    lines, <=200 chars; the standing law's own exception).
  * readme + inplace/create: allowed (modify in place is
    the campaign's own README practice; creating overwrites
    nothing).
  * licence + ANY operation (create/overwrite/inplace/
    delete): REFUSED without the word; stub exception
    never extends to licences. Allowed with the word.
  * A no-change write (new == old) is not a touch and is
    not judged. Undo is restoration of an already-judged
    edit and is not re-judged (documented in the module).
- Operation classification: whole-file format = overwrite;
  unified-diff / search-replace formats = inplace;
  anchored range/search and Agent `_write_hash_anchored`:
  a span covering the whole file = overwrite, else inplace
  (journal's own anchored roads classify the same way, one
  trailing newline excluded from the search comparison);
  hunk review = inplace; EditJournal.replace = inplace.
- Explicit word = setting `guardian_explicit_word`
  (bool, ships FALSE in config_defaults.yaml — a permission,
  never presumed; malformed stored value raises). Given /
  taken back via `/guardians word on|off`, journaled as
  `guardian_word_changed` with the save-failure revert
  pattern of M-072..M-074. Agent passes its config's word
  into EditJournal; tool roads carry it via `_journal_for`;
  agent-less journals read the stored config.
- M-073 interaction proven: a GuardianRefusal (a ValueError
  subclass carrying its verdict) is RE-RAISED by all three
  repair roads, never turned into a repair packet — no
  retry can fix a missing explicit word.
- Surface: `/guardians` (show with worked examples built
  from guard_kind/judge/is_stub_readme/format_guard_check),
  `/guardians word on|off`, `/guardians check <path>` —
  one parser + formatters shared by terminal and TUI
  (CommandHandler + chat-screen help/usage/routing).

## Files
- NEW mythic_agent/core/file_guardians.py (498 lines):
  GUARDIANS_SLICE, SETTING_KEY, GUARDED_KINDS,
  LICENCE_STEMS, OPERATIONS, stub bounds, PLAIN_EXPLANATION,
  USAGE, guard_kind, is_stub_readme, GuardianRefusal,
  GuardVerdict (event/record), judge, guard_or_raise,
  explicit_from_config, WordChange, set_explicit_word,
  parse_guardians_args, format_setting_change,
  format_guard_check, format_guardians.
- mythic_agent/core/edits.py: EditJournal gains
  explicit_word (ctor + per-call), `_explicit_word()`,
  `write(..., operation=..., explicit_word=...)` judging
  via guard_or_raise before any journal record or file
  movement; replace -> inplace; write_anchored_range /
  write_anchored_search classify by span; __all__ +=
  GuardianRefusal, explicit_from_config, guard_or_raise.
- mythic_agent/agents/llm.py: Agent.guardian_status /
  set_guardian_word (journaled, revert pattern);
  apply_edit_format classifies + passes the word;
  _write_hash_anchored classifies by applied span;
  apply_hunk_review writes inplace with the word;
  apply_edit_format_with_repair final write classified;
  all three *_with_repair roads re-raise GuardianRefusal.
- mythic_agent/agents/tools.py: `_journal_for(root, agent)`
  carries the agent's word into every tool-road journal
  (write_file / replace_file_content, anchored + plain).
- mythic_agent/terminal.py: /guardians branch + help line.
- mythic_agent/agents/command_handler.py: dispatch +
  _handle_guardians.
- mythic_agent/ui/screens/chat_screen.py: help line,
  usage text, system-command routing list.
- mythic_agent/data/config_defaults.yaml:
  guardian_explicit_word: false.
- NEW tests/test_file_guardians.py: 97 tests.
- TEAM_LOG.md: this file.

## Verify (counts from on-disk logs in this worktree only)
- m079-targeted2.log: tests/test_file_guardians.py +
  test_config_catalog.py = 108 passed, 3 failed — the 3
  failures are ONLY the pending catalogue delta below.
  The slice file alone (m079-targeted.log, earlier run):
  97 passed.
- m079-related1.log: test_edits + test_edit_formats +
  test_hash_anchored + test_apply_repair + test_hunk_review
  + test_config_catalog + test_edit_truth +
  test_structural_rewrite = 348 passed (run before the
  catalogue revert; the catalogue file is the only delta).
- m079-related2.log: test_format_covenant + test_smart_files
  + test_type_depth + test_policy + test_sessions =
  126 passed.
- m079-related4.log: test_runtime + test_validation +
  test_recovery = 65 passed.
- m079-static.log: test_static_gate = 4 passed (dead-code
  gate included — no quarantine fix needed).
- m079-related3.log: test_lsp_rename + test_lsp_navigation
  + test_docgen + test_public_api + test_ownership =
  207 passed, 4 failed — ALL 4 are the inventory deltas
  below (public_api x2, ownership x2; ownership also wants
  the new module to have git history, which this commit
  gives it).

## Inventory deltas for the coordinator (NOT edited here)
1. config_catalog.yaml — add the next free S-entry:
   name guardian_explicit_word, scope top-level, type bool,
   default 'False', source
   mythic_agent/data/config_defaults.yaml, effect:
   'README and licence guardians (M-079): the user's
   explicit word for guarded files. The guardians are
   always on and live in the edit layer (EditJournal): a
   whole-file overwrite of an existing README refuses on
   every edit road, as does deleting one, while modifying
   a README in place, creating a README, and overwriting
   a barely-anything stub README (<=5 non-empty lines,
   <=200 characters) are allowed; licence files (LICENSE,
   LICENCE, COPYING, NOTICE, any extension or suffix)
   refuse every touch. False (default — never presumed)
   refuses and changes nothing; true records the user's
   explicit word and allows the guarded operations,
   still journaled. A guardian refusal is never a
   repair-loop packet. /guardians shows the guards,
   /guardians check <path> judges one path,
   /guardians word on|off gives or takes back the word
   (journaled guardian_word_changed, save-failure
   revert). Undo is restoration, not re-judged.'
   (Until applied: test_config_catalog.py's
   test_every_defaults_key_is_catalogued,
   test_every_schema_key_is_catalogued, and
   test_setting_types_and_defaults_match_the_defaults_files
   fail on this one key — expected delta, named not chased.)
2. PUBLIC_API.md — regenerate: new module
   mythic_agent/core/file_guardians.py (names in its
   __all__), edits.py += GuardianRefusal,
   explicit_from_config, guard_or_raise; Agent +=
   guardian_status, set_guardian_word; tools += _journal_for
   is private — generator decides.
3. OWNERSHIP.md — regenerate: new core module +
   tests/test_file_guardians.py.
4. roadmap_slices.yaml — flip M-079 to done.
5. CAMPAIGN_STATE.md — ledger row for M-079 (74 -> 75
   banked when integrated in roadmap order).

## Dependency flags
- None on other Wave-1 slices: no shared file with
  M-075..M-078/M-080..M-084 surfaces was edited except
  llm.py / tools.py / terminal.py / command_handler.py /
  chat_screen.py / edits.py, all in M-079-owned regions
  (guardian methods + /guardians branches). Integration
  in roadmap order should be clean; llm.py is the likeliest
  textual neighbour of M-075/M-078 work — anchors used were
  unique, diff is +109/-few in llm.py.
- Behaviour note for sibling slices: any team test that
  writes a README/LICENSE fixture THROUGH EditJournal or
  the tool roads in a real tree will now meet the guardian;
  in-place edits and tmp-dir creations are unaffected
  except licence creation, which now refuses without the
  word. This is the slice working as specified.

## Lessons
- The repair loop (M-073) catches ValueError broadly; any
  new refusal class that is not a stale-target refusal
  must explicitly re-raise there, or it gets packet-ized.
- Anchored search cannot match a target carrying the
  file's trailing newline (needle gains an empty line) —
  whole-file detection must normalise one trailing
  newline, which the journal now does.
- Parallel-wave S-number claims collide by construction;
  the catalogue entry belongs to integration, exactly as
  the wave plan says.

## Bank-prep packet
Commit on hammer/team-05, style "M-079 ...". Coordinator:
integrate in roadmap order, apply the 5 inventory deltas
above, run the FULL suite on this laptop, push the
campaign branch (explicit refspec + ls-remote verify).
