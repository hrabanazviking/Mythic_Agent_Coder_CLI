"""Multi-file change sets (All-Features roadmap slice M-084).

Part IV — The Editor's Hand. The roadmap's words: a change
set is a named, reviewable unit across files with its test
evidence attached.

What already shipped, and what this slice adds:

* M-071 (``core/edit_formats.py``): one file at a time can
  be changed strictly — a whole-file rewrite, a unified
  diff, or search-and-replace blocks, each judged against
  the file's true current text, no fuzz, ever. Real work
  rarely touches one file: a rename, a new helper and its
  call sites, a fix and its test. Applied one file at a
  time, the in-between states are unreviewed and a refusal
  halfway through leaves the tree half-changed with no
  name for what was attempted.
* M-074 (``core/hunk_review.py``): one diff is reviewable
  hunk by hunk. A change set is the same idea one level
  up: many files, reviewed file by file, under one name.
* This slice is that grouping layer: a change set is a
  name plus a list of per-file edits (each in one of
  M-071's concrete formats), each file's edit decided
  accept or reject on its own, and the set's test
  evidence — which tests ran, their counted outcome, and
  where the log lives — carried as data on the set
  itself. The whole set is planned in memory first:
  every accepted edit is judged by M-071's unchanged
  strict appliers against the files' true current text
  before anything is written, so one stale file refuses
  the whole set and changes nothing. Accepted edits then
  ride the EditJournal road through the agent layer, one
  journaled write per file, so each file stays undoable
  like any agent edit. This module writes no file.

Honesty rules, enforced here and pinned by the slice's
tests:

* **A change set is named.** Work that lands together is
  reviewed, recorded, and undone under its name — an
  unnamed set refuses at construction, and the session
  record of an apply carries the name.
* **Every file is decided.** Applying a set with an
  undecided file in it refuses and names the undecided
  files — a file is never silently accepted by default,
  and never silently dropped by default either.
  Rejecting one file never kills the rest: the rejected
  file's edit simply never lands, and its absence is
  counted in the outcome, never hidden. Rejecting every
  file is an honest no-change outcome, not an error.
* **One file, one edit.** A set naming the same file
  twice refuses at construction — two edits to one file
  in one set would have no honest order; sequence two
  sets instead.
* **All-or-nothing planning, journaled writing.** Every
  accepted edit is judged in memory before any write:
  one refusal refuses the whole set and nothing is
  written at all. The writes themselves ride the
  EditJournal one file at a time — each journaled and
  undoable — so a failure mid-write is a journal matter
  with a recovery record, never a silent half-apply.
* **Test evidence is data, never decoration.** Evidence
  carries the command that ran, the passed / failed /
  skipped counts, and a log reference; its verdict is
  computed from the counts (a failure is a failed
  verdict, zero tests is "no tests ran", never
  "passed"). A set with no evidence attached says so
  plainly — absence is recorded as absence, never
  dressed up as a pass. Counts that do not add up
  (negative, or not numbers at all) refuse at attach
  time.
* **No fuzz, ever.** Judgement is M-071's ``apply_edit``
  unchanged — the set layer only groups, reviews, and
  carries evidence; it never loosens a per-file rule.
  The architect format is a split, not a payload, so it
  can never be a set member.
* **The setting is a gate, not a guess.** With
  ``change_sets`` off, set applies through the agent
  layer refuse and say so; the pure set maths stays
  available. A malformed stored setting raises, never
  defaults silently.
"""

from __future__ import annotations

__all__ = [
    "CHANGE_SETS_SLICE",
    "DECISIONS",
    "PLAIN_EXPLANATION",
    "SETTING_KEY",
    "USAGE",
    "Any",
    "BoolChange",
    "ChangeSet",
    "ChangeSetOutcome",
    "Dict",
    "FileEdit",
    "List",
    "Mapping",
    "Optional",
    "Sequence",
    "TestEvidence",
    "Tuple",
    "apply_change_set",
    "attach_evidence",
    "decide",
    "enabled_from_config",
    "format_change_set",
    "format_change_sets",
    "format_evidence",
    "format_setting_change",
    "make_edit",
    "make_evidence",
    "parse_changeset_args",
    "set_enabled",
    "start_change_set",
]

from dataclasses import dataclass, replace
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .edit_formats import apply_edit, get_format

#: The slice that owns this module.
CHANGE_SETS_SLICE = "M-084"

#: The config key the change-set gate lives under.
SETTING_KEY = "change_sets"

#: Every decision a file edit may carry. ``pending`` is
#: where every edit starts; it is never a state to apply in.
DECISIONS: Tuple[str, ...] = ("pending", "accept", "reject")

#: The setting explained in plain words — the sentence
#: every surface shows.
PLAIN_EXPLANATION = (
    "Multi-file change sets: work that lands together is "
    "named and reviewed together. A change set is a name "
    "plus one edit per file — each edit in one of the "
    "usual formats (whole-file, unified diff, or "
    "search-and-replace) — and each file's edit is "
    "accepted or rejected on its own before anything "
    "applies. Rejecting one file never kills the rest. "
    "The whole set is judged in memory first, through "
    "the same strict appliers as any single edit (exact "
    "matches only, no fuzz, ever): one stale file refuses "
    "the whole set and nothing is written. Accepted edits "
    "are then written through the edit journal, one "
    "journaled write per file under the set's name. The "
    "set carries its test evidence as data — the command "
    "that ran, the passed, failed, and skipped counts, "
    "and where the log lives — with the verdict computed "
    "from those counts; a set with no evidence attached "
    "says so plainly, and missing evidence is never "
    "presented as a pass."
)

USAGE = "Usage: /changeset, /changeset on, or /changeset off"


@dataclass(frozen=True)
class FileEdit:
    """One file's edit inside a change set.

    ``format_id`` is one of M-071's concrete formats and
    ``payload`` is that format's payload for ``path`` —
    judged, at apply time, against the file's true
    current text by M-071's strict applier, unchanged.
    """

    path: str
    format_id: str
    payload: str

    def record(self) -> Dict[str, Any]:
        return {"path": self.path, "format": self.format_id}


def make_edit(path: str, format_id: str, payload: str) -> FileEdit:
    """Build one file edit, proving it can be judged.

    The format must be a real, appliable M-071 format —
    the architect split is a plan, not a payload, and can
    never be a set member. An unknown format refuses
    here, at construction, never halfway through an
    apply.
    """
    if not isinstance(path, str) or not path.strip():
        raise ValueError("a change set edit needs a file path")
    if not isinstance(payload, str):
        raise ValueError(
            f"the edit for {path} must carry its payload as text")
    fmt = get_format(format_id)
    if not fmt.appliable:
        raise ValueError(
            "the architect format is a split, not a payload: "
            "a change set member needs a concrete format "
            "(whole-file, unified-diff, or search-replace)")
    return FileEdit(path=path, format_id=fmt.id, payload=payload)


@dataclass(frozen=True)
class TestEvidence:
    """The test evidence attached to a change set.

    The command that ran, its counted outcome, and where
    its log lives — as data. The verdict is computed
    from the counts, never asserted: any failure is a
    failed verdict, and a run of zero tests is honestly
    "no tests ran", not a pass.
    """

    command: str
    passed: int
    failed: int
    skipped: int = 0
    log_ref: str = ""

    @property
    def total(self) -> int:
        return self.passed + self.failed + self.skipped

    @property
    def verdict(self) -> str:
        if self.total == 0:
            return "no tests ran"
        if self.failed:
            return "failed"
        return "passed"

    def record(self) -> Dict[str, Any]:
        return {"command": self.command, "passed": self.passed,
                "failed": self.failed, "skipped": self.skipped,
                "total": self.total, "log_ref": self.log_ref,
                "verdict": self.verdict}


def _count(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"test evidence {name} count must be a whole "
            f"number; got {value!r}")
    if value < 0:
        raise ValueError(
            f"test evidence {name} count cannot be "
            f"negative; got {value}")
    return value


def make_evidence(command: str, passed: Any, failed: Any,
                  skipped: Any = 0, log_ref: str = ""
                  ) -> TestEvidence:
    """Build test evidence, proving its counts are honest.

    Counts must be non-negative whole numbers — a count
    that cannot be true refuses here, at attach time,
    instead of dressing a set in numbers nobody ran.
    """
    if not isinstance(command, str) or not command.strip():
        raise ValueError(
            "test evidence needs the command that ran")
    if not isinstance(log_ref, str):
        raise ValueError(
            "test evidence's log reference must be text "
            "(a path or a note; empty when there is none)")
    return TestEvidence(
        command=command, passed=_count(passed, "passed"),
        failed=_count(failed, "failed"),
        skipped=_count(skipped, "skipped"), log_ref=log_ref)


@dataclass(frozen=True)
class ChangeSet:
    """A named, reviewable unit across files.

    ``decisions`` runs parallel to ``edits``. Change sets
    are values: deciding or attaching evidence returns a
    new set and changes nothing in the old one, so a set
    can be shown, recorded, and only then applied.
    """

    name: str
    edits: Tuple[FileEdit, ...]
    decisions: Tuple[str, ...]
    evidence: Optional[TestEvidence] = None

    def decision(self, index: int) -> str:
        return self.decisions[index]

    def undecided(self) -> List[int]:
        return [i for i, d in enumerate(self.decisions)
                if d == "pending"]

    def counts(self) -> Dict[str, int]:
        result = {"accepted": 0, "rejected": 0, "pending": 0}
        for decision in self.decisions:
            if decision == "accept":
                result["accepted"] += 1
            elif decision == "reject":
                result["rejected"] += 1
            else:
                result["pending"] += 1
        return result

    def event(self) -> Dict[str, Any]:
        return {"type": "change_set_applied",
                "name": self.name,
                "files": [edit.path for edit in self.edits],
                "decisions": list(self.decisions),
                **self.counts(),
                "evidence": (self.evidence.record()
                             if self.evidence is not None else None)}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {**self.event(), "session_id": session_id,
                "journaled": journaled}


def start_change_set(name: str,
                     edits: Sequence[FileEdit]) -> ChangeSet:
    """Open a change set: named, every file pending.

    The name is the unit's identity — unnamed work
    refuses. The set needs at least one file, and one
    file may appear only once: two edits to one file in
    one set would have no honest order.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError(
            "a change set needs a name — work that lands "
            "together is reviewed and recorded under its name")
    members = tuple(edits)
    if not members:
        raise ValueError(
            "a change set needs at least one file edit")
    seen: List[str] = []
    for edit in members:
        if not isinstance(edit, FileEdit):
            raise ValueError(
                "a change set is built from file edits — "
                "use the edit road so each one is judged; "
                f"got {edit!r}")
        if edit.path in seen:
            raise ValueError(
                f"change set {name.strip()!r} names "
                f"{edit.path} twice — one file, one edit "
                "per set; sequence two sets instead")
        seen.append(edit.path)
    return ChangeSet(
        name=name.strip(), edits=members,
        decisions=tuple("pending" for _ in members))


def _check_index(change_set: ChangeSet, index: int) -> None:
    if not isinstance(index, int) or not 0 <= index < len(change_set.edits):
        raise ValueError(
            f"there is no file {index!r} in change set "
            f"{change_set.name!r}; it holds "
            f"{len(change_set.edits)} file(s)")


def decide(change_set: ChangeSet, index: int,
           decision: str) -> ChangeSet:
    """Record an accept / reject decision for one file.

    Re-deciding a file replaces its decision, never
    stacks. ``pending`` is not a decision this road
    takes — a file is decided, or the set is not ready.
    """
    _check_index(change_set, index)
    if decision not in DECISIONS or decision == "pending":
        raise ValueError(
            f"a file is decided accept or reject; "
            f"got {decision!r}")
    decisions = list(change_set.decisions)
    decisions[index] = decision
    return replace(change_set, decisions=tuple(decisions))


def attach_evidence(change_set: ChangeSet,
                    evidence: TestEvidence) -> ChangeSet:
    """Attach test evidence to a set, as data.

    The evidence rides the set from here on — shown in
    its review, carried in its session record. Attaching
    new evidence replaces the old; the set without
    evidence keeps saying so plainly.
    """
    if not isinstance(evidence, TestEvidence):
        raise ValueError(
            "test evidence is built by the evidence road, "
            f"so its counts are proven; got {evidence!r}")
    return replace(change_set, evidence=evidence)


@dataclass(frozen=True)
class ChangeSetOutcome:
    """What an applied change set did, in counted data."""

    applied: int
    rejected: int
    units: int
    changed_files: int

    @property
    def changed(self) -> bool:
        return self.changed_files > 0

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "change_set_applied",
                "applied": self.applied,
                "rejected": self.rejected, "units": self.units,
                "changed_files": self.changed_files,
                "changed": self.changed,
                "session_id": session_id, "journaled": journaled}


def apply_change_set(change_set: ChangeSet,
                     currents: Mapping[str, Optional[str]]
                     ) -> Tuple[Dict[str, str], ChangeSetOutcome]:
    """Plan a fully-decided set against the true texts.

    Returns (new texts by path, outcome) — a plan, never
    a write. Every accepted edit is judged by M-071's
    ``apply_edit`` unchanged, in memory, against
    *currents* (a path absent from the mapping, or mapped
    to None, is a file that does not exist yet). Any one
    refusal refuses the whole set: no partial plan is
    returned, so a caller can only ever write a set that
    judged clean in full. Rejected files are left out
    entirely — their edits are never judged and never
    land. A set with every file rejected is an honest
    no-change outcome, not an error.
    """
    pending = change_set.undecided()
    if pending:
        names = ", ".join(
            f"{i} ({change_set.edits[i].path})" for i in pending)
        raise ValueError(
            f"file(s) {names} in change set "
            f"{change_set.name!r} are not decided yet — "
            "every file must be accepted or rejected "
            "before anything applies; nothing was changed")
    counts = change_set.counts()
    new_texts: Dict[str, str] = {}
    units = 0
    changed_files = 0
    for edit, decision in zip(change_set.edits,
                              change_set.decisions):
        if decision == "reject":
            continue
        current = currents.get(edit.path)
        try:
            new_text, applied = apply_edit(
                edit.format_id, current, edit.payload)
        except ValueError as exc:
            raise ValueError(
                f"change set {change_set.name!r}: the edit "
                f"for {edit.path} refused — {exc} The whole "
                "change set was refused and nothing was "
                "changed") from exc
        new_texts[edit.path] = new_text
        units += applied
        if new_text != current:
            changed_files += 1
    return new_texts, ChangeSetOutcome(
        applied=len(new_texts), rejected=counts["rejected"],
        units=units, changed_files=changed_files)


def enabled_from_config(config: Dict[str, Any]) -> bool:
    """The change-set setting stored in *config*.

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
        return {"type": "change_set_setting_changed",
                "from": self.before, "to": self.after}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "change_set_setting_changed",
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
            f"change sets are already "
            f"{'on' if before else 'off'}")
    return enabled, BoolChange(before=before, after=enabled)


# ---------------------------------------------------------------------
# The /changeset surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------

def parse_changeset_args(args: str) -> Dict[str, Any]:
    """Parse ``/changeset`` arguments.

    /changeset       -> show
    /changeset on    -> turn the gate on
    /changeset off   -> turn the gate off
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
    """A setting change record, in plain words."""
    word = {True: "on", False: "off"}
    return (f"Change sets: {word[record['from']]} -> "
            f"{word[record['to']]}.")


def format_evidence(evidence: Optional[TestEvidence]) -> str:
    """Test evidence, in plain words — or its absence."""
    if evidence is None:
        return "Test evidence: none attached."
    record = evidence.record()
    lines = [
        f"Test evidence: {record['verdict']} — "
        f"{record['passed']} passed, {record['failed']} "
        f"failed, {record['skipped']} skipped "
        f"({record['total']} total) from "
        f"{record['command']!r}."]
    if record["log_ref"]:
        lines.append(f"  log: {record['log_ref']}")
    return "\n".join(lines)


def format_change_set(change_set: ChangeSet) -> str:
    """A change set, file by file, in plain words."""
    lines = [f"Change set {change_set.name!r} — "
             f"{len(change_set.edits)} file(s):"]
    for index, edit in enumerate(change_set.edits):
        lines.append(
            f"  file {index}: {edit.path} "
            f"({edit.format_id}) "
            f"[{change_set.decision(index)}]")
    counts = change_set.counts()
    lines.append(
        f"Decisions: {counts['accepted']} accepted, "
        f"{counts['rejected']} rejected, "
        f"{counts['pending']} undecided.")
    lines.append(format_evidence(change_set.evidence))
    return "\n".join(lines)


_SAMPLE_APP = "alpha = 1\nbeta = 2\n"

_SAMPLE_SEARCH = (
    "<<<<<<< SEARCH\nalpha = 1\n=======\nalpha = 10\n"
    ">>>>>>> REPLACE")


def format_change_sets(config: Dict[str, Any]) -> str:
    """The whole slice, in plain words, for /changeset.

    Built from start_change_set() / make_edit() /
    decide() / attach_evidence() / make_evidence() /
    apply_change_set() / format_change_set(), so every
    public road this module offers is exercised by its
    own show surface: a two-file set where the code edit
    is accepted and the notes file is rejected — the
    rejected file honestly never lands — with its test
    evidence attached, then the same set fully accepted.
    """
    enabled = enabled_from_config(config)
    lines = ["Multi-file change sets (M-084) — "
             + PLAIN_EXPLANATION, ""]
    lines.append(f"Setting: {'on' if enabled else 'off'} "
                 f"({SETTING_KEY}).")
    lines.append("")
    evidence = make_evidence(
        "pytest tests/test_app.py -q", 12, 0, 1,
        "logs/sample-tests.log")
    change_set = attach_evidence(start_change_set(
        "sample: bump alpha, draft notes",
        [make_edit("app.py", "search-replace", _SAMPLE_SEARCH),
         make_edit("notes.txt", "whole-file",
                   "release notes\n")]), evidence)
    lines.append("A sample change set, as it is reviewed:")
    lines.append(format_change_set(change_set))
    currents = {"app.py": _SAMPLE_APP, "notes.txt": None}
    decided = decide(decide(change_set, 0, "accept"), 1, "reject")
    new_texts, outcome = apply_change_set(decided, currents)
    lines.append("")
    lines.append(
        f"Accept app.py, reject notes.txt: "
        f"{outcome.applied} file applied "
        f"({outcome.units} edit unit), {outcome.rejected} "
        f"rejected — app.py's first line is now "
        f"{new_texts['app.py'].splitlines()[0]!r} and "
        "notes.txt was never created: rejecting one file "
        "never kills the rest, and a rejected edit never "
        "lands.")
    accepted = decide(change_set, 0, "accept")
    accepted = decide(accepted, 1, "accept")
    new_texts, outcome = apply_change_set(accepted, currents)
    lines.append(
        f"Accept both: {outcome.applied} files applied, "
        f"{outcome.changed_files} changed — notes.txt is "
        f"created holding {new_texts['notes.txt']!r}. Its "
        f"evidence verdict is {evidence.verdict!r}, "
        "computed from the counts, never asserted.")
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)
