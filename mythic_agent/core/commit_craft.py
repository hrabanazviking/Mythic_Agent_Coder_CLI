"""Commit craft (All-Features roadmap slice M-080).

Part IV — The Editor's Hand. The roadmap's words:
commit-splitting by concern, message drafting from the
actual diff, and the house rules wired in (fetch +
remote-diff before push, never force-push, verify the
remote moved).

What already shipped, and what this slice adds:

* M-071 (``core/edit_formats.py``) and M-074
  (``core/hunk_review.py``): a unified diff is judged
  strictly, hunk by hunk — every hunk's stated counts are
  proven against its body at split time, no fuzz, ever.
  But nothing in the tree split a working-tree change
  into commits, drafted a message from a diff, or pushed
  under Volmarr's house rules: the TUI's ``/commit`` road
  staged everything, committed it under a hand-typed
  message, and ran a bare ``git push`` — no fetch, no
  remote-diff, no verification that the remote moved.
* This slice is the craft layer over the hunk layer: a
  working-tree diff is split into its files (every hunk
  judged by M-074's splitter, unchanged), the files are
  grouped by concern (code, tests, docs, config), each
  group carries a message drafted from its own actual
  diff, and a group is committed on its own — never
  swept up with the others. The push road wires the
  house rules in as refusals, not advice: fetch first,
  read the remote-diff, never force-push, and verify
  with ``ls-remote`` that the remote actually moved.

Honesty rules, enforced here and pinned by the slice's
tests:

* **A draft comes from the diff, never from a guess.**
  The subject's verb is read off the group's own
  changes (all-new files add, all-deleted files remove,
  anything else updates), its names are the group's own
  files, and its body is the group's own per-file
  counts. A group with no changes is never drafted —
  an empty diff refuses the plan outright.
* **Splitting rides the hunk layer.** Every hunk in
  the working diff is parsed and count-proven by
  M-074's ``split_diff`` unchanged; a malformed hunk
  refuses the whole plan before any group is proposed.
  One file belongs to exactly one concern, so a file's
  hunks are never split across commits — the split is
  by concern across files, stated plainly.
* **The house rules are the product.** A push through
  this layer always fetches first and reads the
  remote-diff (ahead/behind plus the diffstat against
  the remote branch) before anything is sent. A remote
  that holds commits this tree does not have refuses:
  pushing past it would need force, and this layer
  never force-pushes — its own push arguments are
  judged by the same validator that refuses any force
  flag, force refspec, or deletion refspec it is ever
  handed. After a push, ``ls-remote`` must show the
  remote holding exactly the pushed head, moved from
  where it stood; anything else is a failed push,
  reported as one, never as a success.
* **Up to date is an honest outcome, not a push.**
  When the remote already holds the local head, the
  verdict says so and nothing is sent.
* **Commit craft never commits on its own.** The
  trigger that will call this planner when work lands
  belongs to M-078 (auto-commit discipline) and is
  read here through a named seam that reports it
  honestly as not yet available — DEPENDS-ON-M-078.
  Until M-078 banks, plans are drafted and groups are
  committed only when asked.
* **The setting is a gate, not a guess.** With
  ``commit_craft`` off, commits and pushes through the
  agent layer refuse and say so; the pure planning and
  drafting maths stays available. A malformed stored
  setting raises, never defaults silently.

The ``\\ No newline at end of file`` marker lines in a
git diff are dropped before a file's hunks are judged:
they carry no count and change no judgement, and this
layer never applies a payload — staging rides
``git add`` on whole files, so the file's true bytes
land exactly as they stand.
"""

from __future__ import annotations

__all__ = [
    "AUTO_COMMIT_SLICE",
    "COMMIT_CRAFT_SLICE",
    "CONCERNS",
    "PLAIN_EXPLANATION",
    "SETTING_KEY",
    "USAGE",
    "Any",
    "BoolChange",
    "CommitGroup",
    "CommitPlan",
    "Dict",
    "FileChange",
    "List",
    "Optional",
    "PushVerdict",
    "Sequence",
    "Tuple",
    "VerifyVerdict",
    "ahead_behind",
    "auto_commit_trigger",
    "classify_concern",
    "collect_working_diff",
    "current_branch",
    "draft_message",
    "draft_subject",
    "enabled_from_config",
    "format_commit_craft",
    "format_commit_record",
    "format_plan",
    "format_push_record",
    "format_setting_change",
    "judge_push",
    "ls_remote_head",
    "parse_commitcraft_args",
    "plan_commits",
    "remote_diff_stat",
    "remote_tracking_head",
    "run_git",
    "set_enabled",
    "split_files",
    "validate_push_args",
    "verify_remote_moved",
]

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .hunk_review import Hunk, split_diff

#: The slice that owns this module.
COMMIT_CRAFT_SLICE = "M-080"

#: The slice that will supply the auto-commit trigger
#: this layer reads through a seam (see
#: :func:`auto_commit_trigger`). Flagged DEPENDS-ON-M-078
#: in the team log: M-078 is built by a parallel team
#: from the same base and is not in this tree.
AUTO_COMMIT_SLICE = "M-078"

#: The config key the commit-craft gate lives under.
SETTING_KEY = "commit_craft"

#: Every concern a file may belong to, in the order
#: groups are proposed (code first, its tests next,
#: then docs, then config/data).
CONCERNS: Tuple[str, ...] = ("code", "tests", "docs", "config")

#: The setting explained in plain words — the sentence
#: every surface shows.
PLAIN_EXPLANATION = (
    "Commit craft: a working-tree change is split into "
    "commits by concern — code, tests, docs, and config "
    "land as separate commits, never swept into one — "
    "and each commit's message is drafted from its own "
    "actual diff: the verb from what the change does, "
    "the names and counts from the files themselves. "
    "Every hunk is judged by the same strict hunk layer "
    "as any diff (its stated counts proven against its "
    "body; no fuzz, ever), and one file belongs to "
    "exactly one concern, so a file's hunks are never "
    "split across commits. Pushing follows the house "
    "rules, wired in as refusals: fetch first, read the "
    "remote-diff before pushing, never force-push — a "
    "remote holding commits this tree lacks refuses "
    "instead — and verify with ls-remote afterwards "
    "that the remote actually moved to the pushed head. "
    "Commit craft never commits on its own: the trigger "
    "that will call it when work lands is M-078's, and "
    "until that banks, plans are drafted and groups "
    "committed only when asked."
)

USAGE = ("Usage: /commitcraft, /commitcraft on, "
         "/commitcraft off, /commitcraft plan, "
         "/commitcraft commit <concern>, or "
         "/commitcraft push")

_GIT_TIMEOUT = 60

_DOC_SUFFIXES = (".md", ".rst", ".txt")
_CONFIG_SUFFIXES = (".yaml", ".yml", ".toml", ".json",
                    ".ini", ".cfg", ".lock")


def classify_concern(path: str) -> str:
    """The concern one file belongs to, from its path.

    Tests are recognised by a ``tests`` / ``test`` path
    part or a ``test_`` / ``_test.py`` file name; docs by
    a docs tree, a document suffix, or a licence file;
    config by a ``data`` path part or a config/data
    suffix; everything else is code. The judgement is
    the path's alone — file contents are never sniffed —
    so the answer is the same on every machine.
    """
    parts = [p for p in path.replace("\\", "/").split("/")
             if p]
    name = parts[-1] if parts else path
    lowered = name.lower()
    if (any(p in ("tests", "test") for p in parts[:-1])
            or name.startswith("test_")
            or name.endswith("_test.py")):
        return "tests"
    if (parts and parts[0] == "docs"
            or lowered.endswith(_DOC_SUFFIXES)
            or lowered.startswith("licence")
            or lowered.startswith("license")):
        return "docs"
    if "data" in parts or lowered.endswith(_CONFIG_SUFFIXES):
        return "config"
    return "code"


@dataclass(frozen=True)
class FileChange:
    """One file's change, as data.

    ``old_path`` is None for a newly added file and
    ``new_path`` is None for a deleted one. ``hunks``
    are M-074 hunks, count-proven at split time. An
    untracked file carries no hunks — it has no diff —
    and its added count is the file's own line count,
    read by the collector and carried here as data.
    """

    path: str
    old_path: Optional[str]
    new_path: Optional[str]
    hunks: Tuple[Hunk, ...] = ()
    binary: bool = False
    untracked: bool = False
    untracked_lines: int = 0

    @property
    def added(self) -> int:
        if self.untracked:
            return self.untracked_lines
        return sum(1 for hunk in self.hunks
                   for line in hunk.body if line[:1] == "+")

    @property
    def removed(self) -> int:
        return sum(1 for hunk in self.hunks
                   for line in hunk.body if line[:1] == "-")

    @property
    def is_new(self) -> bool:
        return self.old_path is None

    @property
    def is_deleted(self) -> bool:
        return self.new_path is None

    def record(self) -> Dict[str, Any]:
        return {"path": self.path,
                "concern": classify_concern(self.path),
                "hunks": len(self.hunks),
                "added": self.added, "removed": self.removed,
                "new": self.is_new, "deleted": self.is_deleted,
                "binary": self.binary,
                "untracked": self.untracked}


_DIFF_GIT_RE = re.compile(r"^diff --git a/(.*?) b/(.*)$")


def split_files(payload: str) -> Tuple[FileChange, ...]:
    """Split a multi-file unified diff into its files.

    File boundaries come from ``diff --git`` headers
    (a bare ``---`` / ``+++`` pair also opens a file);
    each file's hunks are parsed and count-proven by
    M-074's :func:`split_diff`, unchanged — a malformed
    hunk anywhere refuses the whole split, before any
    group is proposed from it. ``\\ No newline`` marker
    lines are dropped (see the module docstring).
    """
    if not isinstance(payload, str):
        raise ValueError("a diff works on text")
    files: List[FileChange] = []
    state: Optional[Dict[str, Any]] = None

    def flush() -> None:
        nonlocal state
        if state is None:
            return
        hunks: Tuple[Hunk, ...] = ()
        if state["hunk_lines"]:
            hunks = split_diff("\n".join(state["hunk_lines"]))
        path = state["new"] or state["old"]
        if path is None:
            raise ValueError(
                "a diff file section names no file; "
                "nothing was planned")
        files.append(FileChange(
            path=path, old_path=state["old"],
            new_path=state["new"], hunks=hunks,
            binary=state["binary"]))
        state = None

    for line in payload.split("\n"):
        match = _DIFF_GIT_RE.match(line)
        if match:
            flush()
            state = {"old": match.group(1),
                     "new": match.group(2),
                     "hunk_lines": [], "binary": False}
            continue
        if line.startswith("--- "):
            if state is None or state["hunk_lines"]:
                flush()
                state = {"old": None, "new": None,
                         "hunk_lines": [], "binary": False}
            marker = line[4:].strip()
            state["old"] = (None if marker == "/dev/null"
                            else marker[2:] if marker.startswith("a/")
                            else marker)
            continue
        if line.startswith("+++ "):
            if state is None:
                raise ValueError(
                    f"not a unified diff: line {line!r}")
            marker = line[4:].strip()
            state["new"] = (None if marker == "/dev/null"
                            else marker[2:] if marker.startswith("b/")
                            else marker)
            continue
        if state is None:
            if line.strip() == "":
                continue
            raise ValueError(f"not a unified diff: line {line!r}")
        if line.startswith("Binary files "):
            state["binary"] = True
            continue
        if line.startswith("rename from "):
            state["old"] = line[len("rename from "):].strip()
            continue
        if line.startswith("rename to "):
            state["new"] = line[len("rename to "):].strip()
            continue
        if line.startswith("\\"):
            continue
        if line.startswith("@@ ") or state["hunk_lines"]:
            state["hunk_lines"].append(line)
            continue
        if line.strip() == "" or line.startswith(
                ("index ", "new file mode", "deleted file mode",
                 "old mode", "new mode", "similarity index")):
            continue
        raise ValueError(f"not a unified diff: line {line!r}")
    flush()
    return tuple(files)


@dataclass(frozen=True)
class CommitGroup:
    """One proposed commit: one concern, its files."""

    concern: str
    files: Tuple[FileChange, ...]

    @property
    def added(self) -> int:
        return sum(change.added for change in self.files)

    @property
    def removed(self) -> int:
        return sum(change.removed for change in self.files)

    @property
    def hunks(self) -> int:
        return sum(len(change.hunks) for change in self.files)

    def record(self) -> Dict[str, Any]:
        return {"concern": self.concern,
                "files": [change.record()
                          for change in self.files],
                "added": self.added, "removed": self.removed,
                "hunks": self.hunks,
                "draft_subject": draft_subject(self),
                "draft_message": draft_message(self)}


@dataclass(frozen=True)
class CommitPlan:
    """A whole split: every group, in concern order."""

    groups: Tuple[CommitGroup, ...]

    def group(self, concern: str) -> CommitGroup:
        for group in self.groups:
            if group.concern == concern:
                return group
        raise ValueError(
            f"the plan holds no {concern!r} group; it "
            f"proposes: {', '.join(g.concern for g in self.groups)}")

    def record(self) -> Dict[str, Any]:
        return {"groups": [group.record()
                           for group in self.groups],
                "concerns": [group.concern
                             for group in self.groups],
                "files": sum(len(group.files)
                             for group in self.groups),
                "added": sum(group.added
                             for group in self.groups),
                "removed": sum(group.removed
                               for group in self.groups)}


def plan_commits(
        payload: str,
        untracked: Sequence[Tuple[str, int]] = ()
        ) -> CommitPlan:
    """Plan a working-tree change as commits by concern.

    *payload* is the tree's unified diff (against HEAD);
    *untracked* names the files git has never tracked,
    each with its own line count — they have no diff, so
    they join the plan as whole new files under their
    path's concern. An empty change refuses: there is
    nothing to draft from, and a draft from nothing
    would be a guess.
    """
    changes: List[FileChange] = list(split_files(payload))
    for path, lines in untracked:
        changes.append(FileChange(
            path=path, old_path=None, new_path=path,
            untracked=True, untracked_lines=lines))
    if not changes:
        raise ValueError(
            "there is nothing to commit — the working "
            "tree is clean; nothing was planned")
    by_concern: Dict[str, List[FileChange]] = {}
    for change in changes:
        by_concern.setdefault(
            classify_concern(change.path), []).append(change)
    groups = tuple(
        CommitGroup(concern=concern,
                    files=tuple(by_concern[concern]))
        for concern in CONCERNS if concern in by_concern)
    return CommitPlan(groups=groups)


def draft_subject(group: CommitGroup) -> str:
    """A commit subject drafted from the group's diff.

    The verb is read off the change itself: every file
    new is an add, every file deleted is a remove, and
    anything else — a modification, or a mix — is an
    update. The names are the group's own files (three
    named, the rest counted, never hidden).
    """
    if all(change.is_new for change in group.files):
        verb = "Add"
    elif all(change.is_deleted for change in group.files):
        verb = "Remove"
    else:
        verb = "Update"
    names = [change.path.rsplit("/", 1)[-1]
             for change in group.files]
    shown = ", ".join(names[:3])
    if len(names) > 3:
        shown += f", and {len(names) - 3} more"
    return f"{verb} {group.concern}: {shown}"


def draft_message(group: CommitGroup) -> str:
    """A full commit message drafted from the diff.

    Subject first (see :func:`draft_subject`), then the
    group's own evidence: one line per file with its
    true added/removed counts from the diff itself,
    and a closing line naming the drafter honestly.
    """
    lines = [draft_subject(group), ""]
    for change in group.files:
        tags = []
        if change.is_new:
            tags.append("new")
        if change.is_deleted:
            tags.append("deleted")
        if change.binary:
            tags.append("binary")
        if change.untracked:
            tags.append("untracked")
        suffix = f" ({', '.join(tags)})" if tags else ""
        lines.append(
            f"- {change.path} "
            f"(+{change.added} -{change.removed}){suffix}")
    lines.append("")
    lines.append(
        "Drafted from the actual diff by commit craft "
        "(M-080).")
    return "\n".join(lines)


# ---------------------------------------------------------------------
# The house rules: push discipline, as pure judgements.
# ---------------------------------------------------------------------

_FORCE_FLAGS = ("--force", "--force-with-lease", "-f",
                "--mirror", "--delete")


def validate_push_args(args: Sequence[str]) -> None:
    """Refuse any push argument that breaks the rules.

    Force in any spelling (a force flag, a
    force-with-lease, a ``+`` refspec), a deletion
    refspec (an empty source), and mirror/delete
    pushes are refused by name. This validator judges
    the push this layer itself builds, and any argument
    list it is ever handed — there is no road around it.
    """
    for arg in args:
        if arg in _FORCE_FLAGS or arg.startswith("--force"):
            raise ValueError(
                f"commit craft never force-pushes: the "
                f"push argument {arg!r} is refused; "
                f"nothing was pushed")
        if arg.startswith("+"):
            raise ValueError(
                f"commit craft never force-pushes: the "
                f"refspec {arg!r} forces the remote; "
                f"nothing was pushed")
        if ":" in arg and arg.split(":", 1)[0] == "":
            raise ValueError(
                f"a deletion refspec ({arg!r}) is not a "
                f"push this layer makes; nothing was pushed")


@dataclass(frozen=True)
class PushVerdict:
    """Whether a push may proceed, and why, in data."""

    allowed: bool
    kind: str
    reason: str

    def record(self) -> Dict[str, Any]:
        return {"allowed": self.allowed, "kind": self.kind,
                "reason": self.reason}


def judge_push(local_head: Optional[str],
               remote_head: Optional[str],
               remote_is_ancestor: bool) -> PushVerdict:
    """Judge a push before it is attempted.

    The house rules, as one judgement: no local head is
    no push; a remote already holding the local head is
    honestly up to date (allowed=False — nothing to
    send, and nothing is); a remote with no such branch
    yet is a new branch; a remote whose head is an
    ancestor of the local head fast-forwards; and a
    remote holding anything else has diverged — pushing
    past it would need force, so it refuses and names
    the remedy (fetch, read the remote-diff, reconcile).
    """
    if not local_head:
        return PushVerdict(
            allowed=False, kind="no-local-head",
            reason="there is no local commit to push; "
                   "nothing was pushed")
    if remote_head and remote_head == local_head:
        return PushVerdict(
            allowed=False, kind="up-to-date",
            reason="the remote already holds this head; "
                   "there is nothing to push")
    if not remote_head:
        return PushVerdict(
            allowed=True, kind="new-branch",
            reason="the remote holds no such branch yet; "
                   "this push creates it")
    if remote_is_ancestor:
        return PushVerdict(
            allowed=True, kind="fast-forward",
            reason="the remote head is an ancestor of "
                   "the local head; the push fast-forwards")
    return PushVerdict(
        allowed=False, kind="diverged",
        reason="the remote holds commits this tree does "
               "not have — pushing past them would need "
               "force, and commit craft never "
               "force-pushes; fetch, read the "
               "remote-diff, and reconcile first; "
               "nothing was pushed")


@dataclass(frozen=True)
class VerifyVerdict:
    """Whether ls-remote proved the remote moved."""

    verified: bool
    kind: str
    reason: str

    def record(self) -> Dict[str, Any]:
        return {"verified": self.verified, "kind": self.kind,
                "reason": self.reason}


def verify_remote_moved(before: Optional[str],
                        after: Optional[str],
                        expected: Optional[str]) -> VerifyVerdict:
    """Verify, from ls-remote readings, that a push landed.

    The remote must now hold exactly the pushed head,
    and it must have moved to get there. A remote still
    holding the old head, or holding anything else, is
    a failed verification — reported as one, never
    rounded up to a success.
    """
    if not after or after != expected:
        return VerifyVerdict(
            verified=False, kind="not-landed",
            reason=f"ls-remote shows the remote holding "
                   f"{after or 'nothing'}, not the pushed "
                   f"head {expected or 'nothing'}; the "
                   f"push is not verified")
    if before and before == after:
        return VerifyVerdict(
            verified=False, kind="unchanged",
            reason="the remote did not move — it held "
                   "this head before the push and holds "
                   "it still; the push is not verified "
                   "as a move")
    return VerifyVerdict(
        verified=True, kind="moved",
        reason="ls-remote shows the remote moved to "
               "the pushed head")


def auto_commit_trigger() -> Dict[str, Any]:
    """The M-078 seam, read honestly.

    M-078 (auto-commit discipline) will supply the
    trigger that calls this planner when work lands.
    It is built by a parallel team from the same base
    and is not in this tree, so the seam reports it as
    unavailable — commit craft never invents a trigger
    of its own, and never commits unasked.
    DEPENDS-ON-M-078.
    """
    return {"slice": AUTO_COMMIT_SLICE, "available": False,
            "note": "commit craft never commits on its "
                    "own; the trigger that will call "
                    "the planner when work lands is "
                    "M-078's (auto-commit discipline) "
                    "and has not banked into this tree "
                    "yet — until it does, plans are "
                    "drafted and groups committed only "
                    "when asked"}


# ---------------------------------------------------------------------
# Git readings: the collector and the push road's facts.
# ---------------------------------------------------------------------

def run_git(repo: Path | str, *args: str,
            timeout: int = _GIT_TIMEOUT) -> Tuple[int, str, str]:
    """Run one git command in *repo*; (code, out, err)."""
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, timeout=timeout)
    return (proc.returncode,
            proc.stdout.decode("utf-8", errors="replace"),
            proc.stderr.decode("utf-8", errors="replace"))


def collect_working_diff(
        repo: Path | str
        ) -> Tuple[str, Tuple[Tuple[str, int], ...], List[str]]:
    """Collect a repo's working diff and untracked files.

    Returns (diff text against HEAD — or, in a repo
    with no commit yet, the staged and unstaged diffs —
    untracked (path, line count) pairs, warnings). A
    directory that is not a git repository refuses:
    there is no diff to draft from, and none is invented.
    """
    code, out, err = run_git(repo, "rev-parse",
                             "--is-inside-work-tree")
    if code != 0 or "true" not in out:
        raise ValueError(
            f"not a git repository ({err.strip() or 'rev-parse failed'}); "
            "there is no diff to plan from")
    warnings: List[str] = []
    code, _out, _err = run_git(repo, "rev-parse", "--verify",
                               "HEAD")
    if code == 0:
        code, diff_text, err = run_git(
            repo, "diff", "HEAD", "--no-color")
        if code != 0:
            raise ValueError(
                f"git diff HEAD failed: {err.strip()}")
    else:
        parts = []
        for args in (("diff", "--cached", "--no-color"),
                     ("diff", "--no-color")):
            code, out, err = run_git(repo, *args)
            if code != 0:
                warnings.append(
                    f"git {' '.join(args)} exited {code}: "
                    f"{err.strip()}")
                continue
            parts.append(out)
        diff_text = "".join(parts)
    untracked: List[Tuple[str, int]] = []
    code, out, err = run_git(
        repo, "ls-files", "--others", "--exclude-standard")
    if code != 0:
        warnings.append(
            f"git ls-files --others exited {code}: "
            f"{err.strip()}")
    else:
        root = Path(repo)
        for name in out.splitlines():
            if not name:
                continue
            try:
                raw = (root / name).read_bytes()
            except OSError:
                untracked.append((name, 0))
                continue
            if b"\0" in raw[:8192]:
                untracked.append((name, 0))
                continue
            text = raw.decode("utf-8", errors="replace")
            untracked.append(
                (name, len(text.splitlines())))
    return diff_text, tuple(untracked), warnings


def current_branch(repo: Path | str) -> str:
    """The checked-out branch name, or '' when detached."""
    code, out, _err = run_git(repo, "branch", "--show-current")
    if code != 0:
        return ""
    return out.strip()


def ls_remote_head(repo: Path | str, remote: str,
                   branch: str) -> str:
    """The head *remote* holds for *branch*, per ls-remote.

    '' when the remote holds no such branch. A remote
    that cannot be read at all raises — a push is never
    judged against a remote nobody actually read.
    """
    code, out, err = run_git(
        repo, "ls-remote", remote, f"refs/heads/{branch}")
    if code != 0:
        raise ValueError(
            f"cannot read remote {remote!r}: "
            f"{err.strip() or 'ls-remote failed'}; "
            "nothing was pushed")
    for line in out.splitlines():
        fields = line.split()
        if fields:
            return fields[0]
    return ""


def remote_tracking_head(repo: Path | str, remote: str,
                         branch: str) -> str:
    """The fetched remote branch's head, or '' if none."""
    code, out, _err = run_git(
        repo, "rev-parse", "--verify", "--quiet",
        f"refs/remotes/{remote}/{branch}")
    if code != 0:
        return ""
    return out.strip()


def ahead_behind(repo: Path | str, remote: str,
                 branch: str) -> Tuple[int, int]:
    """(ahead, behind) of HEAD against the remote branch.

    Behind counts the commits the remote holds that
    this tree does not — the number the diverged
    refusal stands on. No remote branch yet: every
    local commit is ahead, none behind.
    """
    code, out, _err = run_git(
        repo, "rev-parse", "--verify", "--quiet",
        f"refs/remotes/{remote}/{branch}")
    if code != 0:
        code, out, _err = run_git(repo, "rev-list",
                                  "--count", "HEAD")
        return (int(out.strip() or 0) if code == 0 else 0, 0)
    code, out, err = run_git(
        repo, "rev-list", "--left-right", "--count",
        f"{remote}/{branch}...HEAD")
    if code != 0:
        raise ValueError(
            f"cannot compare against {remote}/{branch}: "
            f"{err.strip()}")
    behind_text, ahead_text = out.split()
    return int(ahead_text), int(behind_text)


def remote_diff_stat(repo: Path | str, remote: str,
                     branch: str) -> str:
    """The remote-diff: diffstat of HEAD vs the remote.

    This is the reading the house rule demands before
    any push — what would actually change on the
    remote. '' when the remote holds no such branch
    (the whole branch is the change, and the verdict
    says so).
    """
    code, out, _err = run_git(
        repo, "rev-parse", "--verify", "--quiet",
        f"refs/remotes/{remote}/{branch}")
    if code != 0:
        return ""
    code, out, err = run_git(
        repo, "diff", f"{remote}/{branch}..HEAD", "--stat")
    if code != 0:
        raise ValueError(
            f"cannot read the remote-diff against "
            f"{remote}/{branch}: {err.strip()}")
    return out.strip()


# ---------------------------------------------------------------------
# The gate setting.
# ---------------------------------------------------------------------

def enabled_from_config(config: Dict[str, Any]) -> bool:
    """The commit-craft setting stored in *config*.

    Absent means True (the setting ships on). A stored
    value that is not a bool raises — never guessed at.
    """
    raw = config.get(SETTING_KEY, True)
    if not isinstance(raw, bool):
        raise ValueError(
            f"{SETTING_KEY} must be true or false, "
            f"got {type(raw).__name__}")
    return raw


@dataclass(frozen=True)
class BoolChange:
    """A recorded change of the gate setting."""

    before: bool
    after: bool

    def event(self) -> Dict[str, Any]:
        return {"type": "commit_craft_setting_changed",
                "from": self.before, "to": self.after}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "commit_craft_setting_changed",
                "from": self.before, "to": self.after,
                "session_id": session_id,
                "journaled": journaled}


def set_enabled(config: Dict[str, Any],
                enabled: Any) -> Tuple[bool, BoolChange]:
    """Validate a gate change against *config*, purely."""
    if not isinstance(enabled, bool):
        raise ValueError(
            f"{SETTING_KEY} is turned on or off; got {enabled!r}")
    before = enabled_from_config(config)
    if enabled == before:
        raise ValueError(
            f"commit craft is already "
            f"{'on' if before else 'off'}")
    return enabled, BoolChange(before=before, after=enabled)


# ---------------------------------------------------------------------
# The /commitcraft surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------

def parse_commitcraft_args(args: str) -> Dict[str, Any]:
    """Parse ``/commitcraft`` arguments.

    /commitcraft            -> show
    /commitcraft on         -> turn the gate on
    /commitcraft off        -> turn the gate off
    /commitcraft plan       -> draft the split for the tree
    /commitcraft commit <concern> -> commit one group
    /commitcraft push       -> push under the house rules
    """
    text = (args or "").strip()
    if not text:
        return {"action": "show"}
    if text == "on":
        return {"action": "setting", "enabled": True}
    if text == "off":
        return {"action": "setting", "enabled": False}
    if text == "plan":
        return {"action": "plan"}
    if text == "push":
        return {"action": "push"}
    if text.startswith("commit "):
        concern = text[len("commit "):].strip()
        if concern in CONCERNS:
            return {"action": "commit", "concern": concern}
        raise ValueError(
            f"a group is committed by its concern — one "
            f"of {', '.join(CONCERNS)}; got {concern!r}. "
            + USAGE)
    raise ValueError(USAGE)


def format_setting_change(record: Dict[str, Any]) -> str:
    """A setting change record, in plain words."""
    word = {True: "on", False: "off"}
    return (f"Commit craft: {word[record['from']]} -> "
            f"{word[record['to']]}.")


def format_plan(record: Dict[str, Any]) -> str:
    """A commit plan record, group by group, plainly."""
    lines = [f"Commit plan — {record['files']} file(s), "
             f"+{record['added']} -{record['removed']}, "
             f"in {len(record['groups'])} commit(s) "
             f"by concern:"]
    for group in record["groups"]:
        lines.append(
            f"  [{group['concern']}] {group['draft_subject']}")
        for change in group["files"]:
            lines.append(
                f"    {change['path']} "
                f"(+{change['added']} -{change['removed']})")
    lines.append(
        "Commit one group with /commitcraft commit "
        "<concern>; the rest stay in the working tree.")
    return "\n".join(lines)


def format_commit_record(record: Dict[str, Any]) -> str:
    """A committed group's record, in plain words."""
    return (f"Committed [{record['concern']}] "
            f"{record['sha'][:12]}: {record['subject']} "
            f"({len(record['files'])} file(s), "
            f"+{record['added']} -{record['removed']}).")


def format_push_record(record: Dict[str, Any]) -> str:
    """A house-rules push record, in plain words."""
    if not record["pushed"]:
        return (f"Push to {record['remote']}/"
                f"{record['branch']}: not sent — "
                f"{record['verdict']['reason']}.")
    return (f"Pushed {record['remote']}/{record['branch']}: "
            f"{(record['before'] or 'none')[:12]} -> "
            f"{record['after'][:12]} — verified by "
            f"ls-remote: the remote moved to the pushed "
            f"head.")


_SAMPLE_DIFF = (
    "diff --git a/app.py b/app.py\n"
    "--- a/app.py\n"
    "+++ b/app.py\n"
    "@@ -1,2 +1,2 @@\n"
    " alpha = 1\n"
    "-beta = 2\n"
    "+beta = 20\n"
    "diff --git a/tests/test_app.py b/tests/test_app.py\n"
    "--- a/tests/test_app.py\n"
    "+++ b/tests/test_app.py\n"
    "@@ -1,1 +1,1 @@\n"
    "-assert beta == 2\n"
    "+assert beta == 20\n"
    "diff --git a/NOTES.md b/NOTES.md\n"
    "--- a/NOTES.md\n"
    "+++ b/NOTES.md\n"
    "@@ -1,1 +1,1 @@\n"
    "-beta is 2\n"
    "+beta is 20")


def format_commit_craft(config: Dict[str, Any]) -> str:
    """The whole slice, in plain words, for /commitcraft.

    Built from split_files() / plan_commits() /
    draft_message() / validate_push_args() /
    judge_push() / verify_remote_moved() /
    auto_commit_trigger(), so every public road this
    module offers is exercised by its own show surface:
    one change touching code, tests, and docs splits
    into three drafted commits, and the push discipline
    shows both its fast-forward and its diverged
    refusal, plus the ls-remote verification.
    """
    enabled = enabled_from_config(config)
    lines = ["Commit craft (M-080) — " + PLAIN_EXPLANATION, ""]
    lines.append(f"Setting: {'on' if enabled else 'off'} "
                 f"({SETTING_KEY}).")
    lines.append("")
    changes = split_files(_SAMPLE_DIFF)
    plan = plan_commits(_SAMPLE_DIFF)
    lines.append(
        f"The sample change touches {len(changes)} "
        f"file(s) and splits into {len(plan.groups)} "
        f"commits by concern:")
    lines.append(format_plan(plan.record()))
    lines.append("")
    lines.append("The first group's drafted message:")
    lines.append(plan.groups[0].record()["draft_message"])
    lines.append("")
    house_args = ["push", "origin", "HEAD:refs/heads/main"]
    validate_push_args(house_args)
    lines.append(
        "The house push (" + " ".join(house_args) + ") "
        "passes the push-argument judgement: no force, "
        "no deletion, ever.")
    verdict = judge_push("aaa111", "bbb222", False)
    lines.append(
        f"A diverged remote refuses: {verdict.reason}")
    verdict = judge_push("bbb222", "aaa111", True)
    lines.append(
        f"A fast-forward is allowed: {verdict.reason}.")
    verified = verify_remote_moved("aaa111", "bbb222",
                                   "bbb222")
    lines.append(
        f"Afterwards ls-remote verifies the move: "
        f"{verified.reason}.")
    trigger = auto_commit_trigger()
    lines.append(
        f"Auto-commit trigger: {trigger['note']}.")
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)
