"""Conflict workbench (All-Features roadmap slice M-081).

Part IV — The Editor's Hand. The roadmap's words:
merge/rebase conflicts presented as decisions with both
sides' intent summarised; resolution is edited, tested,
and journaled like any change.

What already shipped, and what this slice adds:

* Git itself stops a merge or rebase at a conflict and
  leaves raw ``<<<<<<<`` / ``=======`` / ``>>>>>>>``
  markers in the file. Nothing in the tree presented
  those markers as decisions, said what either side was
  trying to do, or carried a chosen resolution through
  the EditJournal road like any other change.
* This slice is that workbench. Detection reads the
  real repository state (the unmerged paths, the
  in-progress operation, and the index stages). Each
  conflicted region becomes a decision — take ours,
  take theirs, take both, or edit the resolved text —
  and each side carries an intent summary derived from
  the actual commits and diffs: the side's commit
  subject, author and short hash, and the lines that
  side added and removed against the common base
  version of the file. A summary is built mechanically
  from that evidence, never invented: when a side has
  no commit or no base, the summary says exactly that.
* A resolution applies only when every region is
  decided, the resolved text is proven free of conflict
  markers before anything is written, and the agent
  layer writes it through the EditJournal, stages the
  file so git records it resolved, and then re-checks
  the repository — the resolution is tested against the
  real index, and the outcome is journaled as a
  ``conflict_resolution_applied`` session event.

Honesty rules, enforced here and pinned by the tests:

* **Intent is derived, never invented.** A side's
  summary names its real commit (subject, author,
  short hash) and its real line counts against the
  base stage; a deleted side, a missing base, and a
  missing commit are each stated plainly.
* **Every region must be decided.** Applying with a
  pending region refuses and names the undecided
  regions — nothing is resolved by default.
* **No markers survive a resolution.** Resolved text
  still carrying a conflict marker refuses before any
  write; an edit may produce any text except a text
  that reintroduces a marker.
* **The setting is a gate, not a guess.** With
  ``conflict_workbench`` off, resolutions through the
  agent layer refuse and say so; detection and the
  pure resolution maths stay available. A malformed
  stored setting raises, never defaults silently.
"""

from __future__ import annotations

__all__ = [
    "CHOICES",
    "CONFLICT_SLICE",
    "PLAIN_EXPLANATION",
    "SETTING_KEY",
    "USAGE",
    "Any",
    "BoolChange",
    "ConflictFile",
    "ConflictRegion",
    "Dict",
    "List",
    "Optional",
    "Resolution",
    "ResolutionOutcome",
    "Sequence",
    "SideIntent",
    "Tuple",
    "Workbench",
    "apply_resolution",
    "decide_resolution",
    "detect_workbench",
    "edit_resolution",
    "enabled_from_config",
    "format_conflict_workbench",
    "format_setting_change",
    "format_workbench",
    "parse_conflict_regions",
    "parse_conflicts_args",
    "resolve_text",
    "set_enabled",
    "start_resolution",
    "summarise_side",
]

import difflib
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

#: The slice that owns this module.
CONFLICT_SLICE = "M-081"

#: The config key the conflict-workbench gate lives under.
SETTING_KEY = "conflict_workbench"

#: Every choice a conflicted region may carry. ``pending``
#: is where every region starts; it is never a state a
#: resolution may apply in.
CHOICES: Tuple[str, ...] = ("pending", "ours", "theirs", "both", "edit")

#: The setting explained in plain words — the sentence
#: every surface shows.
PLAIN_EXPLANATION = (
    "Conflict workbench: when a merge or rebase stops on "
    "a conflict, each conflicted place in a file is shown "
    "as a decision — take our side, take their side, take "
    "both, or edit the resolved text yourself. Each side "
    "carries a summary of its intent built from the real "
    "commits: the commit's subject and author and the "
    "lines that side added and removed against the common "
    "base version — derived from the actual diffs, never "
    "invented, and a side with no base or no commit says "
    "so plainly. Every conflicted place must be decided "
    "before anything applies, and resolved text still "
    "carrying a conflict marker is refused. The chosen "
    "resolution is written through the edit journal like "
    "any change, staged so git records the file resolved, "
    "then re-checked against the real index, and the "
    "whole resolution is recorded on the session journal."
)

USAGE = "Usage: /conflicts, /conflicts on, or /conflicts off"

_GIT_TIMEOUT = 15


def _run_git(root: Path, *args: str) -> Tuple[int, str, str]:
    proc = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, timeout=_GIT_TIMEOUT)
    return (proc.returncode,
            proc.stdout.decode("utf-8", errors="replace"),
            proc.stderr.decode("utf-8", errors="replace"))


def _stage_text(root: Path, stage: int, path: str) -> Optional[str]:
    code, out, _err = _run_git(root, "show", f":{stage}:{path}")
    return out if code == 0 else None


def _commit_info(root: Path, ref: str) -> Optional[Tuple[str, str, str]]:
    code, out, _err = _run_git(
        root, "log", "-1", "--format=%H%x00%s%x00%an", ref)
    if code != 0 or "\x00" not in out:
        return None
    sha, subject, author = out.strip().split("\x00", 2)
    return sha, subject, author


def summarise_side(label: str, commit: Optional[Tuple[str, str, str]],
                   base: Optional[str],
                   side: Optional[str]) -> str:
    """One side's intent, derived mechanically from evidence.

    *commit* is (sha, subject, author) or None; *base* is
    the common base version's text or None; *side* is this
    side's version text, or None when this side deleted
    the file. Nothing is paraphrased or guessed: the
    summary is the commit's own subject plus counted
    added/removed lines against the base.
    """
    if side is None:
        change = "this side deleted the file"
    elif base is None:
        change = "no common base version exists for this file"
    else:
        diff = difflib.unified_diff(
            base.splitlines(), side.splitlines(), lineterm="")
        added = removed = 0
        for line in diff:
            if line.startswith("+") and not line.startswith("+++"):
                added += 1
            elif line.startswith("-") and not line.startswith("---"):
                removed += 1
        change = f"against the base: +{added} -{removed} line(s)"
    if commit is None:
        return f"{label}: no commit recorded for this side; {change}"
    sha, subject, author = commit
    return (f"{label}: commit {sha[:7]} {subject!r} by "
            f"{author}; {change}")


@dataclass(frozen=True)
class SideIntent:
    label: str
    summary: str


@dataclass(frozen=True)
class ConflictRegion:
    """One conflicted place: both sides' lines, as data."""

    index: int
    ours_label: str
    theirs_label: str
    ours: Tuple[str, ...]
    theirs: Tuple[str, ...]
    base: Tuple[str, ...] = ()


def parse_conflict_regions(text: str) -> Tuple[ConflictRegion, ...]:
    """Parse conflict markers in *text* into regions.

    Handles the two-way marker form and the diff3 form
    (with a ``|||||||`` base section). Text outside the
    markers is not a region. A file with no markers has
    no regions; an unterminated marker raises.
    """
    regions: List[ConflictRegion] = []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.startswith("<<<<<<<"):
            i += 1
            continue
        ours_label = line[7:].strip()
        ours: List[str] = []
        base: List[str] = []
        theirs: List[str] = []
        section = "ours"
        i += 1
        closed = False
        while i < len(lines):
            current = lines[i]
            if current.startswith("|||||||") and section == "ours":
                section = "base"
            elif current.startswith("=======") and section != "theirs":
                section = "theirs"
            elif current.startswith(">>>>>>>"):
                regions.append(ConflictRegion(
                    index=len(regions), ours_label=ours_label,
                    theirs_label=current[7:].strip(),
                    ours=tuple(ours), theirs=tuple(theirs),
                    base=tuple(base)))
                closed = True
                i += 1
                break
            elif section == "ours":
                ours.append(current)
            elif section == "base":
                base.append(current)
            else:
                theirs.append(current)
            i += 1
        if not closed:
            raise ValueError(
                "a conflict marker opens but never closes; "
                "the file is not a readable conflict")
    return tuple(regions)


@dataclass(frozen=True)
class ConflictFile:
    path: str
    regions: Tuple[ConflictRegion, ...]
    ours_intent: str
    theirs_intent: str
    content: str = ""

    @property
    def region_count(self) -> int:
        return len(self.regions)


@dataclass(frozen=True)
class Workbench:
    operation: str
    files: Tuple[ConflictFile, ...]

    @property
    def conflicted(self) -> bool:
        return bool(self.files)

    def event(self) -> Dict[str, Any]:
        return {"type": "conflict_workbench_shown",
                "operation": self.operation,
                "files": [f.path for f in self.files],
                "regions": sum(f.region_count for f in self.files)}


def _operation(root: Path) -> Tuple[str, Optional[str]]:
    """The in-progress operation and its incoming ref, if any."""
    code, out, _err = _run_git(root, "rev-parse", "--git-dir")
    if code != 0:
        return "none", None
    git_dir = Path(out.strip())
    if not git_dir.is_absolute():
        git_dir = root / git_dir
    for name, op in (("MERGE_HEAD", "merge"),
                     ("CHERRY_PICK_HEAD", "cherry-pick"),
                     ("REVERT_HEAD", "revert")):
        marker = git_dir / name
        if marker.exists():
            return op, marker.read_text(
                encoding="utf-8", errors="replace").strip()
    for name in ("rebase-merge", "rebase-apply"):
        if (git_dir / name).exists():
            head = git_dir / name / "head-name"
            ref = (head.read_text(encoding="utf-8", errors="replace")
                   .strip() if head.exists() else None)
            return "rebase", ref
    return "none", None


def detect_workbench(root: Path | str) -> Workbench:
    """Read the real conflict state of the repo at *root*.

    A non-repository, or a repository with no unmerged
    paths, yields an empty workbench whose operation is
    stated honestly — never an error, never a guess.
    """
    root = Path(root)
    code, out, _err = _run_git(root, "rev-parse", "--is-inside-work-tree")
    if code != 0 or "true" not in out:
        return Workbench(operation="not-a-repository", files=())
    operation, incoming = _operation(root)
    code, out, _err = _run_git(
        root, "diff", "--name-only", "--diff-filter=U")
    if code != 0:
        return Workbench(operation=operation, files=())
    paths = sorted(p for p in out.splitlines() if p.strip())
    if not paths:
        return Workbench(operation=operation, files=())
    ours_commit = _commit_info(root, "HEAD")
    theirs_commit = (_commit_info(root, incoming)
                     if incoming else None)
    files: List[ConflictFile] = []
    for path in paths:
        target = root / path
        content = (target.read_text(encoding="utf-8", errors="replace")
                   if target.exists() else "")
        base = _stage_text(root, 1, path)
        ours = _stage_text(root, 2, path)
        theirs = _stage_text(root, 3, path)
        files.append(ConflictFile(
            path=path,
            regions=parse_conflict_regions(content) if content else (),
            ours_intent=summarise_side("ours", ours_commit, base, ours),
            theirs_intent=summarise_side(
                "theirs", theirs_commit, base, theirs),
            content=content))
    return Workbench(operation=operation, files=tuple(files))


@dataclass(frozen=True)
class Resolution:
    """Decisions over one conflicted file, as a value."""

    path: str
    regions: int
    choices: Tuple[str, ...]
    edited: Tuple[Tuple[int, Tuple[str, ...]], ...] = ()

    def choice(self, index: int) -> str:
        return self.choices[index]

    def undecided(self) -> List[int]:
        return [i for i, c in enumerate(self.choices) if c == "pending"]

    def counts(self) -> Dict[str, int]:
        result = {"ours": 0, "theirs": 0, "both": 0, "edited": 0,
                  "pending": 0}
        for choice in self.choices:
            if choice == "edit":
                result["edited"] += 1
            elif choice in result:
                result[choice] += 1
            else:
                result["pending"] += 1
        return result

    def event(self) -> Dict[str, Any]:
        return {"type": "conflict_resolution_applied",
                "path": self.path, "regions": self.regions,
                "choices": list(self.choices), **self.counts()}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {**self.event(), "session_id": session_id,
                "journaled": journaled}


def start_resolution(conflict_file: ConflictFile) -> Resolution:
    """Open a resolution: every region pending."""
    return Resolution(
        path=conflict_file.path, regions=conflict_file.region_count,
        choices=tuple("pending" for _ in range(conflict_file.region_count)))


def _check_index(resolution: Resolution, index: int) -> None:
    if not isinstance(index, int) or not 0 <= index < resolution.regions:
        raise ValueError(
            f"there is no conflicted place {index!r} in this "
            f"resolution; it holds {resolution.regions} place(s)")


def decide_resolution(resolution: Resolution, index: int,
                      choice: str) -> Resolution:
    """Record an ours / theirs / both choice for one region.

    ``edit`` is not a choice this road takes — an edit
    must carry its edited text, through
    :func:`edit_resolution`, so it can be judged for
    markers. Re-deciding replaces, never stacks.
    """
    _check_index(resolution, index)
    if choice == "edit":
        raise ValueError(
            "an edit must carry its edited text — use the "
            "edit road, so the text can be judged")
    if choice not in CHOICES or choice == "pending":
        raise ValueError(
            f"a conflicted place is decided ours, theirs, or "
            f"both; got {choice!r}")
    choices = list(resolution.choices)
    choices[index] = choice
    edited = tuple((i, b) for i, b in resolution.edited if i != index)
    return replace(resolution, choices=tuple(choices), edited=edited)


def edit_resolution(resolution: Resolution, index: int,
                    text: Sequence[str] | str) -> Resolution:
    """Record edited resolved text for one region.

    The edited text is judged here, at edit time: text
    carrying a conflict marker refuses, because a
    resolution may produce any text except one that
    reintroduces the conflict.
    """
    _check_index(resolution, index)
    if isinstance(text, str):
        lines = text.split("\n")
        while lines and lines[-1] == "":
            lines.pop()
    else:
        lines = list(text)
    for line in lines:
        if line.startswith(("<<<<<<<", ">>>>>>>", "|||||||")):
            raise ValueError(
                "edited resolved text may not carry a conflict "
                "marker; nothing was changed")
    choices = list(resolution.choices)
    choices[index] = "edit"
    edited = tuple((i, b) for i, b in resolution.edited if i != index)
    edited = edited + ((index, tuple(lines)),)
    return replace(resolution, choices=tuple(choices), edited=edited)


@dataclass(frozen=True)
class ResolutionOutcome:
    applied: int
    changed: bool

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "conflict_resolution_applied",
                "applied": self.applied, "changed": self.changed,
                "session_id": session_id, "journaled": journaled}


def resolve_text(content: str, resolution: Resolution) -> str:
    """The resolved text for *content* under *resolution*.

    Pure: splices each decided region's chosen lines into
    the file in place of its markers. Raises on a pending
    region (named) or when the file's regions do not
    match the resolution's count.
    """
    pending = resolution.undecided()
    if pending:
        raise ValueError(
            "conflicted place(s) "
            + ", ".join(str(i) for i in pending)
            + " are not decided yet — every place must be "
            "decided ours, theirs, both, or edited before "
            "anything applies; nothing was changed")
    regions = parse_conflict_regions(content)
    if len(regions) != resolution.regions:
        raise ValueError(
            f"the file holds {len(regions)} conflicted place(s) "
            f"but the resolution decides {resolution.regions}; "
            "nothing was changed")
    edited = dict(resolution.edited)
    chosen: List[Tuple[str, ...]] = []
    for region in regions:
        choice = resolution.choice(region.index)
        if choice == "ours":
            chosen.append(region.ours)
        elif choice == "theirs":
            chosen.append(region.theirs)
        elif choice == "both":
            chosen.append(region.ours + region.theirs)
        else:
            chosen.append(edited[region.index])
    out: List[str] = []
    lines = content.split("\n")
    i = 0
    region_index = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("<<<<<<<"):
            out.extend(chosen[region_index])
            region_index += 1
            i += 1
            while i < len(lines) and not lines[i].startswith(">>>>>>>"):
                i += 1
            i += 1  # step past the closing marker
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


def apply_resolution(content: str, resolution: Resolution
                     ) -> Tuple[str, ResolutionOutcome]:
    """Resolve *content*, proving no marker survives."""
    new_text = resolve_text(content, resolution)
    if parse_conflict_regions(new_text) or any(
            line.startswith(("<<<<<<<", ">>>>>>>"))
            for line in new_text.split("\n")):
        raise ValueError(
            "the resolved text still carries a conflict "
            "marker; nothing was changed")
    return new_text, ResolutionOutcome(
        applied=resolution.regions, changed=new_text != content)


def enabled_from_config(config: Dict[str, Any]) -> bool:
    """The conflict-workbench setting stored in *config*.

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
    before: bool
    after: bool

    def event(self) -> Dict[str, Any]:
        return {"type": "conflict_workbench_setting_changed",
                "from": self.before, "to": self.after}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "conflict_workbench_setting_changed",
                "from": self.before, "to": self.after,
                "session_id": session_id, "journaled": journaled}


def set_enabled(config: Dict[str, Any],
                enabled: Any) -> Tuple[bool, BoolChange]:
    """Validate a gate change against *config*, purely."""
    if not isinstance(enabled, bool):
        raise ValueError(
            f"{SETTING_KEY} is turned on or off; got {enabled!r}")
    before = enabled_from_config(config)
    if enabled == before:
        raise ValueError(
            f"conflict workbench is already "
            f"{'on' if before else 'off'}")
    return enabled, BoolChange(before=before, after=enabled)


# ---------------------------------------------------------------------
# The /conflicts surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------

def parse_conflicts_args(args: str) -> Dict[str, Any]:
    """Parse ``/conflicts`` arguments.

    /conflicts       -> show
    /conflicts on    -> turn the gate on
    /conflicts off   -> turn the gate off
    """
    text = (args or "").strip()
    if not text:
        return {"action": "show"}
    if text == "on":
        return {"action": "setting", "enabled": True}
    if text == "off":
        return {"action": "setting", "enabled": False}
    raise ValueError(USAGE)


def format_setting_change(record: Dict[str, Any]) -> str:
    word = {True: "on", False: "off"}
    return (f"Conflict workbench: {word[record['from']]} -> "
            f"{word[record['to']]}.")


def format_workbench(workbench: Workbench) -> str:
    """A workbench — every file, region and intent, plainly."""
    if not workbench.files:
        return (f"No conflicts in progress "
                f"(operation: {workbench.operation}).")
    lines = [f"Conflicts — operation: {workbench.operation}, "
             f"{len(workbench.files)} file(s):"]
    for conflict_file in workbench.files:
        lines.append(f"  {conflict_file.path}: "
                     f"{conflict_file.region_count} place(s)")
        lines.append(f"    intent — {conflict_file.ours_intent}")
        lines.append(f"    intent — {conflict_file.theirs_intent}")
        for region in conflict_file.regions:
            lines.append(
                f"    place {region.index}: "
                f"ours ({region.ours_label}) "
                f"{len(region.ours)} line(s) / "
                f"theirs ({region.theirs_label}) "
                f"{len(region.theirs)} line(s)")
            for line in region.ours:
                lines.append(f"      < {line}")
            for line in region.theirs:
                lines.append(f"      > {line}")
    return "\n".join(lines)


_SAMPLE = (
    "title = 'Guide'\n<<<<<<< HEAD\nprice = 10\n=======\n"
    "price = 12\n>>>>>>> pricing-branch\nend = True\n")


def format_conflict_workbench(config: Dict[str, Any],
                              root: Any = None) -> str:
    """The whole slice, in plain words, for /conflicts.

    With *root*, the live workbench for that repository
    (built by detect_workbench) is shown after the
    explanation. The worked example is built from
    parse_conflict_regions() / summarise_side() /
    start_resolution() / decide_resolution() /
    edit_resolution() / apply_resolution() /
    format_workbench(), so every public road this module
    offers is exercised by its own show surface.
    """
    enabled = enabled_from_config(config)
    lines = ["Conflict workbench (M-081) — " + PLAIN_EXPLANATION, ""]
    lines.append(f"Setting: {'on' if enabled else 'off'} "
                 f"({SETTING_KEY}).")
    sample_file = ConflictFile(
        path="guide.py",
        regions=parse_conflict_regions(_SAMPLE),
        ours_intent=summarise_side(
            "ours", ("aaaaaaa1", "Set the guide price", "Volmarr"),
            "price = 9\n", "price = 10\n"),
        theirs_intent=summarise_side(
            "theirs", ("bbbbbbb2", "Raise the guide price", "Volmarr"),
            "price = 9\n", "price = 12\n"),
        content=_SAMPLE)
    lines.append("")
    lines.append(format_workbench(
        Workbench(operation="merge", files=(sample_file,))))
    resolution = decide_resolution(
        start_resolution(sample_file), 0, "theirs")
    new_text, outcome = apply_resolution(_SAMPLE, resolution)
    lines.append(
        f"Decide place 0 as theirs: {outcome.applied} place "
        f"resolved — the file now reads "
        f"{new_text.splitlines()[1]!r}, and no marker remains.")
    edited = edit_resolution(start_resolution(sample_file), 0,
                             ["price = 11"])
    new_text, outcome = apply_resolution(_SAMPLE, edited)
    lines.append(
        f"Edit place 0 instead: the file now reads "
        f"{new_text.splitlines()[1]!r}.")
    if root is not None:
        lines.append("")
        lines.append("This repository:")
        lines.append(format_workbench(detect_workbench(root)))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)
