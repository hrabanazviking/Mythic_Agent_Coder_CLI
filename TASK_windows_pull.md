# Urgent Windows GitHub Desktop pull repair

Date: 2026-10-04. User supplied a GitHub Desktop error for `main`:
`invalid path 'Operational_Refactoring:-Mythic_Agent_Coder_CLI_Fix_1.md'`.

## Evidence and scope

Remote `main` at `674a16907a164298ee54db991a6f28e840957c97` still contains the
invalid filename. Development has the rename in `1abaab0c43a2041557fd1e3f538c87eb7c004d87`;
its six hosted Linux/macOS/Windows × Python 3.10/3.13 gates passed in run
`37258887547`. The merged main revision predates that fix.

Preserve all document bytes and Git history; rename the document on main to
`Operational_Refactoring-Mythic_Agent_Coder_CLI_Fix_1.md`. Add a tracked-path
regression check and run CI on main as well as development. No runtime changes,
force push, deletion of content, or changes to the user's local checkout.

## Acceptance

All tracked paths satisfy Windows filename rules; the document blob is identical;
maintained tests pass; normal push to main succeeds and remote revision is verified.
After fetching current origin, GitHub Desktop can pull the fixed final tree without
checking out the intervening invalid filename. Actual Desktop retry is on the
user's Windows machine and must not be claimed as tested here.

## Repair evidence

The new regression check reproduced the exact invalid filename before repair.
Renamed the document with identical contents and added the check to maintained
tests. Also carried over the already-tested Python 3.10 image dependency selector
so the restored six-job matrix can validate main. CI now runs for main pushes.
All four local maintained checks pass after the repair; hosted evidence follows.
