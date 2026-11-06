"""Guarded mass edits (roadmap slice M-093).

Part IV - The Editor's Hand. The roadmap's words:
``repo-wide edits require a dry-run report (files,
hunks, risks) approved before a single byte moves.``

What already shipped, and what this slice adds:

* M-071 (``core/edit_formats.py``) judges one file's
  edit strictly against its true current text.
  M-074 (``core/hunk_review.py``) makes one diff
  reviewable hunk by hunk. M-084
  (``core/change_sets.py``) groups many files under
  one name and plans them all-or-nothing in memory.
  But nothing stood guard over the *scale* of an
  edit: a plan touching thirty files could ride the
  same road as a one-line fix, with no moment where
  a person sees the whole blast - every file, every
  hunk, every risk - and says yes before it moves.
* This slice is that moment, as a pure layer. A
  proposed mass edit (each file's true current text
  and its proposed text) is turned into a dry-run
  report: per file, the hunks, added and removed
  lines a real unified diff counts, and the risks
  the texts themselves carry. The report carries a
  fingerprint of the exact proposal, and an approval
  is data bound to that fingerprint - approval for
  one report never covers another. This module
  writes no file, runs no edit and approves nothing
  itself; the agent layer owns applying an approved
  report through the EditJournal road.

Honesty rules, enforced here and pinned by tests:

* **The report is a dry run, never a deed.** Building
  a report changes nothing; the counts come from a
  real diff of the two texts given, never from a
  claim the caller makes about them.
* **Approval precedes movement, and binds exactly.**
  An approval record covers a report only when its
  fingerprint matches the report's fingerprint
  exactly. Changing one byte of one file after
  approval makes a different report, and the old
  approval does not cover it.
* **Risks are mechanical, never vibes.** A risk is
  named only for a fact in the texts or the path:
  binary content (a NUL byte), a proposal that
  deletes every line, a file at or over the
  large-file size M-087 named, a hunk count at or
  over the many-hunks line, a sensitive path (a
  credential, key or secret name). No other risk is
  invented, and a clean file says so by carrying no
  risks.
* **An unchanged file is not an edit.** A file whose
  proposed text equals its current text is listed,
  flagged ``no change``, and never counted among
  the changed files - a report is not padded.
* **One file, one entry.** A plan naming the same
  file twice refuses - two proposals for one file
  would have no honest order; sequence two plans.
* **Mass is counted, not felt.** A plan needs an
  approval when it changes two or more files, or
  when any changed file carries a high risk. A
  single ordinary changed file needs none - it
  rides the ordinary one-file roads.
* **The setting is a gate, not a guess.** With
  ``mass_edit_guard`` off, mass applies through
  the agent layer refuse and say so; the pure
  report maths stays available. A malformed stored
  setting raises, never defaults silently.
"""

from __future__ import annotations

__all__ = [
    "HIGH_RISKS",
    "LARGE_FILE_BYTES",
    "MANY_HUNKS",
    "MASS_EDIT_GUARD_SLICE",
    "PLAIN_EXPLANATION",
    "SETTING_KEY",
    "USAGE",
    "Any",
    "Approval",
    "BoolChange",
    "Dict",
    "FileReport",
    "List",
    "MassEditReport",
    "Optional",
    "Tuple",
    "approval_covers",
    "approve_report",
    "build_report",
    "enabled_from_config",
    "file_risks",
    "format_mass_edit_guard",
    "format_report",
    "format_setting_change",
    "parse_mass_edit_args",
    "require_approval",
    "set_enabled",
]

import difflib
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

#: The slice that owns this module.
MASS_EDIT_GUARD_SLICE = "M-093"

#: The config key the mass-edit gate lives under.
SETTING_KEY = "mass_edit_guard"

#: At or over this many bytes a file is large
#: (the line M-087's large-file care named).
LARGE_FILE_BYTES = 1_000_000

#: At or over this many hunks one file's change is
#: wide enough to name as a risk on its own.
MANY_HUNKS = 10

#: The risks that make even a one-file plan need an
#: approval before it moves.
HIGH_RISKS = ("binary content",
              "deletes every line",
              "sensitive path")

#: The setting explained in plain words.
PLAIN_EXPLANATION = (
    "Guarded mass edits: a repo-wide edit is first "
    "shown whole, as a dry-run report - every file "
    "it would touch, the hunks and added and removed "
    "lines a real diff counts, and the risks the "
    "texts themselves carry (binary content, a file "
    "emptied, a very large file, many hunks, a "
    "sensitive path). Nothing moves on the strength "
    "of the report alone: a plan that changes two "
    "or more files, or any file at high risk, needs "
    "an approval first, and the approval is bound "
    "to the report's exact fingerprint - change one "
    "byte afterwards and the approval no longer "
    "covers the plan. A file proposed unchanged is "
    "listed as no change and never counted.")

USAGE = ("Usage: /massedit, /massedit on, "
         "/massedit off, or /massedit show")


def _clean_path(path: Any) -> str:
    text = str(path or "").strip()
    return text[2:] if text.startswith("./") else text


def _is_sensitive(path: str) -> bool:
    parts = [p.lower() for p in path.split("/") if p]
    if not parts:
        return False
    name = parts[-1]
    if name in (".env", "credentials", "id_rsa",
                "id_ed25519"):
        return True
    if name.endswith((".pem", ".key")):
        return True
    if "secret" in name or ".ssh" in parts:
        return True
    return False


def file_risks(path: str, before: str,
               after: str) -> Tuple[str, ...]:
    """The risks one file's two texts carry.

    Mechanical only: each risk names a fact in the
    texts or the path. An unchanged file's only
    flag is ``no change``.
    """
    if before == after:
        return ("no change",)
    risks: List[str] = []
    if "\x00" in before or "\x00" in after:
        risks.append("binary content")
    if before and not after:
        risks.append("deletes every line")
    size = max(len(before.encode("utf-8")),
               len(after.encode("utf-8")))
    if size >= LARGE_FILE_BYTES:
        risks.append(
            f"large file ({size} bytes)")
    if _is_sensitive(path):
        risks.append("sensitive path")
    return tuple(risks)


def _diff_counts(before: str, after: str,
                 ) -> Tuple[int, int, int]:
    """(hunks, added, removed) from a real diff."""
    diff = difflib.unified_diff(
        before.splitlines(), after.splitlines(),
        lineterm="")
    hunks = added = removed = 0
    for line in diff:
        if line.startswith("@@ "):
            hunks += 1
        elif line.startswith("+") and \
                not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and \
                not line.startswith("---"):
            removed += 1
    return hunks, added, removed


@dataclass(frozen=True)
class FileReport:
    """One file in the dry run: counts and risks."""

    path: str
    hunks: int
    added: int
    removed: int
    risks: Tuple[str, ...]

    @property
    def changed(self) -> bool:
        return "no change" not in self.risks

    @property
    def high_risk(self) -> bool:
        return any(r in HIGH_RISKS for r in self.risks)

    def record(self) -> Dict[str, Any]:
        return {"path": self.path,
                "hunks": self.hunks,
                "added": self.added,
                "removed": self.removed,
                "risks": list(self.risks),
                "changed": self.changed,
                "high_risk": self.high_risk}


@dataclass(frozen=True)
class MassEditReport:
    """The whole dry run, with its fingerprint."""

    files: Tuple[FileReport, ...]
    fingerprint: str

    @property
    def changed_files(self) -> Tuple[FileReport, ...]:
        return tuple(f for f in self.files if f.changed)

    @property
    def total_hunks(self) -> int:
        return sum(f.hunks for f in self.changed_files)

    @property
    def total_added(self) -> int:
        return sum(f.added for f in self.changed_files)

    @property
    def total_removed(self) -> int:
        return sum(f.removed for f in self.changed_files)

    @property
    def risks(self) -> Tuple[str, ...]:
        seen: List[str] = []
        for entry in self.changed_files:
            for risk in entry.risks:
                label = risk.split(" (")[0]
                if label not in seen:
                    seen.append(label)
        return tuple(seen)

    @property
    def requires_approval(self) -> bool:
        if len(self.changed_files) >= 2:
            return True
        return any(f.high_risk
                   for f in self.changed_files)

    def record(self) -> Dict[str, Any]:
        return {"slice": MASS_EDIT_GUARD_SLICE,
                "fingerprint": self.fingerprint,
                "files": [f.record() for f in self.files],
                "changed_files": len(self.changed_files),
                "total_hunks": self.total_hunks,
                "total_added": self.total_added,
                "total_removed": self.total_removed,
                "risks": list(self.risks),
                "requires_approval":
                    self.requires_approval}


def _fingerprint(entries: List[Dict[str, str]]) -> str:
    payload = json.dumps(
        entries, sort_keys=True,
        separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_report(plan: Any) -> MassEditReport:
    """Build the dry-run report for a proposed plan.

    *plan* is a list of mappings, each with ``path``,
    ``before`` and ``after`` (the file's true current
    text and its proposed text, both strings). The
    report counts a real diff per file and binds the
    whole proposal into one fingerprint. Anything
    malformed refuses in plain words.
    """
    if not isinstance(plan, (list, tuple)) or not plan:
        raise ValueError(
            "a mass edit plan needs at least one file")
    files: List[FileReport] = []
    entries: List[Dict[str, str]] = []
    seen = set()
    for item in plan:
        if not isinstance(item, dict):
            raise ValueError(
                "each plan entry must be a mapping with "
                "path, before and after")
        path = _clean_path(item.get("path"))
        if not path:
            raise ValueError(
                "each plan entry must name its file")
        if path in seen:
            raise ValueError(
                f"the plan names {path} twice - two "
                "proposals for one file have no honest "
                "order; sequence two plans instead")
        seen.add(path)
        before = item.get("before")
        after = item.get("after")
        if not isinstance(before, str) or \
                not isinstance(after, str):
            raise ValueError(
                f"{path}: before and after must be "
                "the file's texts (strings)")
        risks = list(file_risks(path, before, after))
        hunks, added, removed = _diff_counts(before, after)
        if hunks >= MANY_HUNKS and before != after:
            risks.append(f"many hunks ({hunks})")
        files.append(FileReport(
            path=path, hunks=hunks, added=added,
            removed=removed, risks=tuple(risks)))
        entries.append({
            "path": path,
            "before_sha256": hashlib.sha256(
                before.encode("utf-8")).hexdigest(),
            "after_sha256": hashlib.sha256(
                after.encode("utf-8")).hexdigest()})
    return MassEditReport(
        files=tuple(files),
        fingerprint=_fingerprint(entries))


@dataclass(frozen=True)
class Approval:
    """An approval, bound to one report's fingerprint."""

    fingerprint: str
    approved: bool = True

    def record(self) -> Dict[str, Any]:
        return {"type": "mass_edit_approved",
                "slice": MASS_EDIT_GUARD_SLICE,
                "fingerprint": self.fingerprint,
                "approved": self.approved}


def approve_report(report: MassEditReport) -> Approval:
    """Approve *report* exactly as it stands."""
    return Approval(fingerprint=report.fingerprint)


def approval_covers(report: MassEditReport,
                    approval: Any) -> bool:
    """True only when *approval* binds this report.

    The approval may be an Approval or its record
    mapping. Anything else, an approval marked not
    approved, or a fingerprint that differs by any
    amount covers nothing.
    """
    if isinstance(approval, Approval):
        record = approval.record()
    elif isinstance(approval, dict):
        record = approval
    else:
        return False
    if record.get("approved") is not True:
        return False
    return record.get("fingerprint") == report.fingerprint


def require_approval(report: MassEditReport,
                     approval: Any) -> None:
    """Refuse unless *approval* covers *report*.

    A report that needs no approval passes with any
    approval value, including none - the guard binds
    mass and high-risk plans, not ordinary edits.
    """
    if not report.requires_approval:
        return
    if approval_covers(report, approval):
        return
    raise ValueError(
        "this plan needs an approval of its dry-run "
        "report before a single byte moves - approve "
        "the report exactly as shown, then apply")


def format_report(report: MassEditReport) -> str:
    """The dry-run report, in plain words."""
    changed = report.changed_files
    lines = [
        f"Mass edit dry run (M-093): "
        f"{len(changed)} file(s) to change, "
        f"{report.total_hunks} hunk(s), "
        f"{report.total_added} line(s) added, "
        f"{report.total_removed} line(s) removed"]
    for entry in report.files:
        if not entry.changed:
            lines.append(f"{entry.path}: no change")
            continue
        line = (f"{entry.path}: {entry.hunks} hunk(s), "
                f"+{entry.added} -{entry.removed}")
        if entry.risks:
            line += " - risks: " + ", ".join(entry.risks)
        lines.append(line)
    if report.risks:
        lines.append(
            "Risks: " + ", ".join(report.risks))
    else:
        lines.append("Risks: none found in the texts")
    if report.requires_approval:
        lines.append(
            "Approval: required before any byte moves "
            f"(fingerprint {report.fingerprint[:12]})")
    else:
        lines.append(
            "Approval: not required - a single "
            "ordinary changed file")
    return "\n".join(lines)


def enabled_from_config(config: Dict[str, Any]) -> bool:
    """The mass_edit_guard setting stored in *config*.

    Absent means True (the setting ships on). A stored
    value that is not a bool raises - never guessed at.
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
        return {"type": "mass_edit_guard_setting_changed",
                "from": self.before, "to": self.after}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {**self.event(), "session_id": session_id,
                "journaled": journaled}


def set_enabled(config: Dict[str, Any],
                enabled: Any) -> Tuple[bool, BoolChange]:
    """Validate a gate change against *config*, purely."""
    if not isinstance(enabled, bool):
        raise ValueError(
            f"{SETTING_KEY} is turned on or off; "
            f"got {enabled!r}")
    before = enabled_from_config(config)
    if enabled == before:
        raise ValueError(
            f"mass edit guard is already "
            f"{'on' if before else 'off'}")
    return enabled, BoolChange(before=before, after=enabled)


def parse_mass_edit_args(args: str) -> Dict[str, Any]:
    """Parse the /massedit grammar both surfaces share."""
    text = (args or "").strip()
    if not text or text == "show":
        return {"action": "show"}
    if text == "on":
        return {"action": "on"}
    if text == "off":
        return {"action": "off"}
    raise ValueError(f"usage: {USAGE}")


def format_setting_change(record: Dict[str, Any]) -> str:
    state = "on" if record.get("to") else "off"
    return f"Mass edit guard is now {state}."


_DEMO_PLAN = (
    {"path": "demo.py",
     "before": "first = 1\nsecond = 2\n",
     "after": "first = 1\nsecond = 22\nthird = 3\n"},
    {"path": "notes.txt",
     "before": "keep me\n",
     "after": "keep me\n"},
    {"path": ".env",
     "before": "TOKEN=old\n",
     "after": "TOKEN=new\n"},
)


def format_mass_edit_guard(config: Dict[str, Any]) -> str:
    """The whole slice, in plain words, for /massedit.

    Built from build_report() / format_report(), so
    the show surface exercises the road it names: a
    demo plan dry-run - one ordinary change, one
    unchanged file, one sensitive path.
    """
    enabled = enabled_from_config(config)
    lines = ["Guarded mass edits (M-093) - "
             + PLAIN_EXPLANATION, ""]
    lines.append(f"Setting: {'on' if enabled else 'off'} "
                 f"({SETTING_KEY}).")
    lines.append("")
    lines.append(format_report(build_report(_DEMO_PLAN)))
    return "\n".join(lines)
