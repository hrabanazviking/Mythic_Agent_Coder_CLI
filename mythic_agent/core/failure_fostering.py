"""Failure fostering (All-Features roadmap slice M-139).

Part VI continues here. The roadmap's words:
``a failed member's task is re-dealt with its
failure report attached; the same failure twice
escalates to the human with both reports.``

What already shipped, and what this slice adds:

* The dealing of a plan's slices is already data
  (``core/task_dealing.py``, M-125): a dealt
  assignment is one slice dealt to one member,
  validated by that layer itself. The members are
  the shipped crew (``core/crew_members.py``,
  M-121), and the traffic between members is
  already data (``core/crew_comms.py``, M-126) -
  checked here: a failure report is not a hand-off
  (the hand-off kinds are findings, diff and
  question; none carries failure semantics), so
  this slice holds its own report record and
  composes the dealing by import instead. Budgets
  (M-107) were checked and are not composed: a
  failure names no spend. What nothing holds is
  the fostering itself: what happens, as data,
  when a dealt task fails.
* This slice is that fostering, as a pure layer:
  a failure report validated as data (the member
  who failed, the slice, a failure key naming the
  failure, a title and a body), a fostered re-deal
  whose account is DERIVED from the original
  dealing and its failure report, an escalation
  whose account is DERIVED from the two reports
  of the same failure, the shipped data file
  (``mythic_agent/data/failure_fostering.yaml``)
  holding one example fostering book in exactly
  the shape a real fostering file takes, a loader
  for a fostering file anywhere on disk, records
  shaped as session news, and a small in-memory
  registry model. This module re-deals no task to
  a live agent, delivers no message, spawns
  nothing, calls no model, persists nothing and
  imports no agent / UI code; the agent layer
  owns holding a fostering book for a session.

Honesty rules, enforced here and pinned by tests:

* **A re-deal is derived, never stored loose.**
  A re-deal's account is read off the original
  dealing, the failure report attached to it and
  the member who fosters the task, so a stored
  re-deal whose account disagrees with the
  account derived from its own parts refuses.
  A re-deal naming no account of its own and
  judged against no dealing refuses too. The
  fostering member is never the member who
  failed, and the report must judge its own
  dealing: a report naming another member or
  another slice than the dealing's refuses.
* **An escalation is derived, never stored
  loose.** The same failure twice - two reports
  naming the same member, the same slice and the
  same failure key - escalates to the human with
  both reports attached: the escalation's account
  is read off those two reports, in held order,
  so a stored escalation whose member, slice,
  failure key, reports or account disagree with
  the derived escalation refuses. Two reports of
  different failures never escalate together.
* **Dealings and members are the shipped
  layers' own.** A re-deal's dealing is read by
  ``core/task_dealing.py`` itself (validate /
  build assignment, never re-implemented), so
  the member, office, slice, title and load a
  fostering walks answer to exactly the
  validators a live dealing answers to. Member
  ids read exactly as the M-121 layer reads
  them, composed by import.
* **Data only - no live road is claimed.** A
  fostering here is a validated record held as
  data: no task is actually re-dealt to a live
  agent, no escalation is delivered to the
  human, and nothing here claims a crew is live.
  The fostering is visible through this slice's
  own /foster screen, and nothing here claims a
  Part VIII board exists.
* **Malformed refuses.** A duplicate assignment
  slice, report id, re-deal id or escalation id
  in one book, a re-deal or escalation naming a
  dealing or report the book holds no record
  for, and unknown keys in a report, a re-deal,
  an escalation or a fostering mapping all raise
  instead of being skipped or guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .task_dealing import (
    DealtAssignment, build_assignment, validate_assignment)
from .validation import ValidationError
from .worktrees import normalize_slice_id

__all__ = [
    "FAILURE_FOSTERING_RESOURCE",
    "FAILURE_FOSTERING_SCHEMA",
    "FAILURE_FOSTERING_SLICE",
    "HUMAN_RECIPIENT",
    "PLAIN_EXPLANATION",
    "USAGE",
    "FailureEscalation",
    "FailureReport",
    "FosterBook",
    "FosterRegistry",
    "FosteredRedeal",
    "book_record",
    "build_book",
    "build_escalation",
    "build_redeal",
    "build_report",
    "derive_escalation",
    "derive_redeal",
    "escalation_plain_words",
    "escalation_record",
    "format_escalation",
    "format_fostering_screen",
    "format_redeal",
    "format_report",
    "format_reports",
    "load_failure_fostering",
    "load_failure_fostering_file",
    "parse_fostering_args",
    "plain_words",
    "redeal_plain_words",
    "redeal_record",
    "report_record",
    "validate_book",
    "validate_escalation",
    "validate_redeal",
    "validate_report",
]

FAILURE_FOSTERING_SLICE = "M-139"

#: The packaged data resource holding the example book.
FAILURE_FOSTERING_RESOURCE = "failure_fostering.yaml"

#: The schema word a fostering file must carry.
FAILURE_FOSTERING_SCHEMA = "mythic.failure_fostering/1"

#: The one recipient an escalation goes to.
HUMAN_RECIPIENT = "human"

_REPORT_KEYS = frozenset({
    "report_id", "id", "member", "member_id",
    "slice", "slice_id", "failure", "failure_key", "key",
    "title", "body", "text",
})

_REDEAL_KEYS = frozenset({
    "redeal_id", "id", "assignment", "dealing",
    "report", "failure_report", "foster_member", "foster",
    "account", "statements",
})

_ESCALATION_KEYS = frozenset({
    "escalation_id", "id", "member", "member_id",
    "slice", "slice_id", "failure", "failure_key", "key",
    "reports", "report_ids", "account", "statements",
})

_BOOK_KEYS = frozenset({"title", "name"})

_FOSTER_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "fostering_note", "guide", "assignments", "reports",
    "redeals", "escalations",
})

#: The shipped example book's title, held to this
#: by the loader's example check.
_EXAMPLE_TITLE = "Failure fostering at the M-138 slice boundary"

#: The shipped example's assignment slices and
#: report ids, in held order, pinned by the loader.
_EXAMPLE_ASSIGNMENT_SLICES = ("M-139", "M-138")

_EXAMPLE_REPORT_IDS = (
    "report-first", "report-second", "report-note")

#: The shipped example's one re-deal: the M-139
#: task fostered by the auditor, its account
#: pinned word-for-word by the loader.
_EXAMPLE_REDEAL_ID = "redeal-m139"

_EXAMPLE_REDEAL_FOSTER = "auditor"

_EXAMPLE_REDEAL_ACCOUNT = (
    "Slice M-139 'Failure fostering' was dealt "
    "to forge_worker.",
    "forge_worker reported failure 'replay-gap' "
    "on M-139: 'Replay gap found'.",
    "The task is re-dealt to auditor with its "
    "failure report attached.",
)

#: The shipped example's one escalation: the
#: replay-gap failure twice, its reports and its
#: account pinned word-for-word by the loader.
_EXAMPLE_ESCALATION_ID = "escalation-m139"

_EXAMPLE_ESCALATION_REPORTS = ("report-first", "report-second")

_EXAMPLE_ESCALATION_ACCOUNT = (
    "Report 1: forge_worker reported 'Replay gap "
    "found' (replay-gap) on M-139.",
    "Report 2: forge_worker reported 'Replay gap "
    "found again' (replay-gap) on M-139.",
    "The same failure 'replay-gap' on M-139 "
    "happened twice; it escalates to the human "
    "with both reports attached.",
)

PLAIN_EXPLANATION = (
    "Failure fostering: when a member's dealt "
    "task fails, the failure is held as a report "
    "- the member, the slice, the failure, a "
    "title and the body of what went wrong - and "
    "the task is re-dealt to another member with "
    "its failure report attached, the re-deal "
    "derived from the original dealing and the "
    "report, never stored loose. The same failure "
    "twice - the same member, slice and failure "
    "in two reports - escalates to the human "
    "with both reports attached, the escalation "
    "derived from those reports. This layer "
    "holds fosterings as data only; it re-deals "
    "no task to a live agent, delivers no "
    "escalation, spawns no agent and calls no "
    "model itself."
)

USAGE = (
    "Usage: /foster, /foster show, "
    "/foster report <report-id>, "
    "/foster redeal <slice-id>, "
    "/foster escalation <report-id>"
)


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_title(value: Any, what: str = "a title") -> str:
    text = _clean_text(value, what)
    if len(text) > 120 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"120 characters, got {len(text)} characters")
    return text


def _check_short_text(value: Any, what: str) -> str:
    text = _clean_text(value, what)
    if len(text) > 200 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"200 characters, got {len(text)} characters")
    return text


def _check_long_text(value: Any, what: str) -> str:
    text = _clean_text(value, what)
    if len(text) > 2000 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"2000 characters, got {len(text)} characters")
    return text


def _check_account(value: Any) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"an account must be a list of statements, "
            f"got {value!r}")
    account = tuple(
        _check_long_text(a, "an account statement")
        for a in value)
    if not account:
        raise ValueError("an account carries at least one statement")
    if len(account) > 16:
        raise ValueError(
            f"an account carries at most 16 statements, "
            f"got {len(account)}")
    if len(set(account)) != len(account):
        raise ValueError("an account states one statement twice")
    return account


def _pick_any(mapping: Dict[str, Any], spellings: Tuple[str, ...],
              what: str) -> Any:
    values = [mapping[s] for s in spellings if s in mapping]
    if not values:
        return None
    if any(value != values[0] for value in values[1:]):
        raise ValueError(f"a record names two different {what}")
    return values[0]


def _check_assignment(value: Any) -> DealtAssignment:
    """One dealing: the task-dealing layer's own reading."""
    if isinstance(value, DealtAssignment):
        return value
    if isinstance(value, dict):
        return validate_assignment(value)
    raise ValueError(
        f"a re-deal's dealing must be a dealt assignment "
        f"record, got {value!r}")


def _check_report_ref(value: Any) -> "FailureReport":
    if isinstance(value, FailureReport):
        return value
    if isinstance(value, dict):
        return validate_report(value)
    raise ValueError(
        f"a failure report record is needed, got {value!r}")


# ---------------------------------------------------------------------
# The report: one failure of one dealt task, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class FailureReport:
    """One failure report: a dealt task that failed.

    ``member`` is the member whose task failed;
    ``slice_id`` is the slice the task was dealt
    for; ``failure_key`` names the failure itself
    (the word two reports of the same failure
    share); ``title`` names the report in plain
    words and ``body`` carries what went wrong.
    Constructing one validates it.
    """

    report_id: Optional[str] = None
    member: str = ""
    slice_id: str = ""
    failure_key: str = ""
    title: str = ""
    body: str = ""

    def __post_init__(self) -> None:
        if self.report_id is not None:
            object.__setattr__(
                self, "report_id", normalize_member_id(self.report_id))
        object.__setattr__(
            self, "member", normalize_member_id(self.member))
        object.__setattr__(
            self, "slice_id", normalize_slice_id(self.slice_id))
        object.__setattr__(
            self, "failure_key", normalize_member_id(self.failure_key))
        object.__setattr__(
            self, "title", _check_title(self.title, "a report's title"))
        object.__setattr__(
            self, "body", _check_long_text(self.body, "a report's body"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "failure_report",
            "slice": FAILURE_FOSTERING_SLICE,
            "report_id": self.report_id,
            "member": self.member,
            "slice_id": self.slice_id,
            "failure_key": self.failure_key,
            "title": self.title,
            "body": self.body,
        }


def validate_report(report: Any) -> FailureReport:
    """Validate one failure report into a FailureReport.

    Accepts a FailureReport or a mapping naming a
    ``member`` (or ``member_id``), a ``slice_id``
    (or ``slice``), a ``failure_key`` (or
    ``failure`` / ``key``), a ``title``, a ``body``
    (or ``text``) and an optional ``report_id``
    (or ``id``). Naming two spellings of one field
    with different values refuses, and unknown
    keys refuse.
    """
    if isinstance(report, FailureReport):
        return report
    if not isinstance(report, dict):
        raise ValueError(f"a report must be a mapping, got {report!r}")
    unknown = set(report) - _REPORT_KEYS
    if unknown:
        raise ValueError(
            "unknown report keys: %s" % ", ".join(sorted(unknown)))
    member = _pick_any(report, ("member", "member_id"), "members")
    if member is None:
        raise ValueError("a report is missing its member")
    slice_id = _pick_any(report, ("slice_id", "slice"), "slices")
    if slice_id is None:
        raise ValueError("a report is missing its slice")
    failure = _pick_any(
        report, ("failure_key", "failure", "key"), "failures")
    if failure is None:
        raise ValueError("a report is missing its failure")
    body = _pick_any(report, ("body", "text"), "bodies")
    if body is None:
        raise ValueError("a report is missing its body")
    if "title" not in report:
        raise ValueError("a report is missing its title")
    kwargs: Dict[str, Any] = {
        "member": member, "slice_id": slice_id,
        "failure_key": failure, "title": report["title"],
        "body": body}
    report_id = _pick_any(report, ("report_id", "id"), "report ids")
    if report_id is not None:
        kwargs["report_id"] = report_id
    return FailureReport(**kwargs)


def build_report(report: Any = None, **kwargs: Any) -> FailureReport:
    """Build one validated report, from a mapping or field words."""
    if isinstance(report, FailureReport) and not kwargs:
        return report
    if isinstance(report, dict) or report is None:
        merged: Dict[str, Any] = {}
        if isinstance(report, dict):
            merged.update(report)
        merged.update(kwargs)
        return validate_report(merged)
    raise ValueError(f"a report must be a mapping, got {report!r}")


# ---------------------------------------------------------------------
# The re-deal: a failed task fostered by another member, derived.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class FosteredRedeal:
    """One fostered re-deal: a failed task re-dealt, as data.

    ``assignment`` is the original M-125 dealing
    itself; ``report`` is the failure report
    attached to the re-deal; ``foster_member`` is
    the member the task is re-dealt to - never the
    member who failed; ``account`` is the plain
    statements the re-deal rests on, derived from
    the dealing, the report and the fostering
    member. A re-deal is normally derived (see
    :func:`derive_redeal`); constructing one
    directly validates its shape and that the
    report judges its own dealing.
    """

    redeal_id: Optional[str] = None
    assignment: Any = None
    report: Any = None
    foster_member: str = ""
    account: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.redeal_id is not None:
            object.__setattr__(
                self, "redeal_id", normalize_member_id(self.redeal_id))
        if self.assignment is None:
            raise ValueError("a re-deal is missing its dealing")
        object.__setattr__(
            self, "assignment", _check_assignment(self.assignment))
        if self.report is None:
            raise ValueError("a re-deal is missing its failure report")
        object.__setattr__(
            self, "report", _check_report_ref(self.report))
        object.__setattr__(
            self, "foster_member",
            normalize_member_id(self.foster_member))
        if self.foster_member == self.assignment.member:
            raise ValueError(
                "a failed task is fostered by another member - "
                "the member who failed never fosters their "
                "own failure")
        if self.report.member != self.assignment.member:
            raise ValueError(
                "a failure report judges its own dealing: the "
                "report's member disagrees with the dealing's")
        if self.report.slice_id != self.assignment.slice_id:
            raise ValueError(
                "a failure report judges its own dealing: the "
                "report's slice disagrees with the dealing's")
        object.__setattr__(
            self, "account", _check_account(self.account))

    @property
    def member(self) -> str:
        """The member whose task failed."""
        return self.assignment.member

    @property
    def slice_id(self) -> str:
        """The slice the fostered task was dealt for."""
        return self.assignment.slice_id

    @property
    def title(self) -> str:
        """The title of the fostered task."""
        return self.assignment.title

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "failure_fostering_redeal",
            "slice": FAILURE_FOSTERING_SLICE,
            "redeal_id": self.redeal_id,
            "assignment": self.assignment.to_record(),
            "report": self.report.to_record(),
            "foster_member": self.foster_member,
            "account": list(self.account),
        }


def derive_redeal(assignment: Any, report: Any,
                  foster_member: Any) -> FosteredRedeal:
    """Derive one fostered re-deal from its dealing and report.

    *assignment* is the original dealing (an
    M-125 dealt assignment, read by that layer);
    *report* is the failure report attached to
    the re-deal - it must judge that dealing (same
    member, same slice); *foster_member* is the
    member the task is re-dealt to, never the
    member who failed. The account is read off
    those three: the dealing, the failure and the
    fostering, in that order. Deriving is
    deterministic: the same dealing, report and
    member derive the same re-deal, every time.
    """
    dealt = _check_assignment(assignment)
    failure = _check_report_ref(report)
    foster = normalize_member_id(foster_member)
    account = (
        f"Slice {dealt.slice_id} '{dealt.title}' was dealt "
        f"to {dealt.member}.",
        f"{failure.member} reported failure "
        f"'{failure.failure_key}' on {failure.slice_id}: "
        f"'{failure.title}'.",
        f"The task is re-dealt to {foster} with its "
        f"failure report attached.",
    )
    return FosteredRedeal(
        assignment=dealt, report=failure,
        foster_member=foster, account=account)


def validate_redeal(redeal: Any, assignment: Any = None,
                    report: Any = None) -> FosteredRedeal:
    """Validate one re-deal into a FosteredRedeal.

    Accepts a FosteredRedeal or a mapping naming
    an ``assignment`` (or ``dealing``), a ``report``
    (or ``failure_report``), a ``foster_member``
    (or ``foster``), an ``account`` (or
    ``statements``) and an optional ``redeal_id``
    (or ``id``). The re-deal is judged against the
    re-deal derived from its own dealing, report
    and fostering member: a stored account that
    disagrees with the derived account refuses,
    because an account is derived, never stored
    loose. When *assignment* / *report* are given,
    the re-deal's dealing and report must equal
    them. A stored re-deal naming no account of
    its own refuses, for the same reason.
    """
    if isinstance(redeal, FosteredRedeal):
        current = redeal
    elif isinstance(redeal, dict):
        unknown = set(redeal) - _REDEAL_KEYS
        if unknown:
            raise ValueError(
                "unknown re-deal keys: %s" % ", ".join(sorted(unknown)))
        dealt = _pick_any(
            redeal, ("assignment", "dealing"), "dealings")
        if dealt is None:
            raise ValueError("a re-deal is missing its dealing")
        failure = _pick_any(
            redeal, ("report", "failure_report"), "reports")
        if failure is None:
            raise ValueError("a re-deal is missing its failure report")
        foster = _pick_any(
            redeal, ("foster_member", "foster"), "fostering members")
        if foster is None:
            raise ValueError("a re-deal is missing its fostering member")
        account = _pick_any(
            redeal, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError(
                "a stored re-deal names no account of its own - "
                "derive it from its dealing and report")
        redeal_id = _pick_any(redeal, ("redeal_id", "id"), "re-deal ids")
        current = FosteredRedeal(
            redeal_id=redeal_id, assignment=dealt, report=failure,
            foster_member=foster, account=account)
    else:
        raise ValueError(f"a re-deal must be a mapping, got {redeal!r}")
    derived = derive_redeal(
        current.assignment, current.report, current.foster_member)
    if current.account != derived.account:
        raise ValueError(
            "a stored re-deal's account disagrees with the "
            "account derived from its dealing and report - "
            "an account is derived, never stored loose")
    if assignment is not None \
            and current.assignment != _check_assignment(assignment):
        raise ValueError(
            "a re-deal's dealing disagrees with the dealing "
            "it is judged against")
    if report is not None \
            and current.report != _check_report_ref(report):
        raise ValueError(
            "a re-deal's report disagrees with the report "
            "it is judged against")
    return current


def build_redeal(redeal: Any = None, assignment: Any = None,
                 report: Any = None, **kwargs: Any) -> FosteredRedeal:
    """Build one validated re-deal, from a mapping or field words."""
    if isinstance(redeal, FosteredRedeal) and not kwargs \
            and assignment is None and report is None:
        return validate_redeal(redeal)
    if isinstance(redeal, dict) or redeal is None:
        merged: Dict[str, Any] = {}
        if isinstance(redeal, dict):
            merged.update(redeal)
        merged.update(kwargs)
        return validate_redeal(merged, assignment, report)
    return validate_redeal(redeal, assignment, report)


# ---------------------------------------------------------------------
# The escalation: the same failure twice, to the human, derived.
# ---------------------------------------------------------------------


def _check_report_ids(value: Any) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes)) \
            or not isinstance(value, (list, tuple)):
        raise ValueError(
            f"an escalation's reports must be a list of "
            f"report ids, got {value!r}")
    ids = tuple(normalize_member_id(v) for v in value)
    if len(ids) != 2:
        raise ValueError(
            "an escalation holds both reports of the same "
            "failure: exactly two report ids")
    if ids[0] == ids[1]:
        raise ValueError(
            "an escalation holds two different reports - "
            "one report twice is not the same failure twice")
    return ids


@dataclass(frozen=True)
class FailureEscalation:
    """One escalation: the same failure twice, to the human.

    ``member`` is the member whose task failed
    twice; ``slice_id`` and ``failure_key`` name
    the failure the two reports share;
    ``report_ids`` are the two reports, in held
    order, both attached to the escalation;
    ``account`` is the plain statements the
    escalation rests on, derived from those two
    reports. ``recipient`` is always the human.
    An escalation is normally derived (see
    :func:`derive_escalation`); constructing one
    directly validates its shape only.
    """

    escalation_id: Optional[str] = None
    member: str = ""
    slice_id: str = ""
    failure_key: str = ""
    report_ids: Tuple[str, ...] = ()
    account: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.escalation_id is not None:
            object.__setattr__(
                self, "escalation_id",
                normalize_member_id(self.escalation_id))
        object.__setattr__(
            self, "member", normalize_member_id(self.member))
        object.__setattr__(
            self, "slice_id", normalize_slice_id(self.slice_id))
        object.__setattr__(
            self, "failure_key", normalize_member_id(self.failure_key))
        object.__setattr__(
            self, "report_ids", _check_report_ids(self.report_ids))
        object.__setattr__(
            self, "account", _check_account(self.account))

    @property
    def recipient(self) -> str:
        """The one recipient an escalation goes to: the human."""
        return HUMAN_RECIPIENT

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "failure_fostering_escalation",
            "slice": FAILURE_FOSTERING_SLICE,
            "escalation_id": self.escalation_id,
            "member": self.member,
            "slice_id": self.slice_id,
            "failure_key": self.failure_key,
            "recipient": self.recipient,
            "report_ids": list(self.report_ids),
            "account": list(self.account),
        }


def _held_reports(source: Any) -> Tuple[FailureReport, ...]:
    """The reports one source holds, in held order."""
    if isinstance(source, FosterBook):
        return source.reports
    if isinstance(source, FosterRegistry):
        return source.list_reports()
    if isinstance(source, (list, tuple)):
        return tuple(
            r if isinstance(r, FailureReport) else validate_report(r)
            for r in source)
    raise ValueError(f"failure reports are needed, got {source!r}")


def _report_named(reports: Tuple[FailureReport, ...],
                  ref: Any) -> FailureReport:
    if isinstance(ref, FailureReport):
        for report in reports:
            if report.report_id is not None \
                    and report.report_id == ref.report_id:
                return report
            if report == ref:
                return report
        raise KeyError(f"no held report matches: {ref!r}")
    wanted = normalize_member_id(ref)
    for report in reports:
        if report.report_id == wanted:
            return report
    raise KeyError(f"no held report: {wanted!r}")


def _escalation_account(first: FailureReport,
                        second: FailureReport) -> Tuple[str, ...]:
    return (
        f"Report 1: {first.member} reported '{first.title}' "
        f"({first.failure_key}) on {first.slice_id}.",
        f"Report 2: {second.member} reported '{second.title}' "
        f"({second.failure_key}) on {second.slice_id}.",
        f"The same failure '{first.failure_key}' on "
        f"{first.slice_id} happened twice; it escalates to "
        f"the human with both reports attached.",
    )


def derive_escalation(source: Any, first: Any,
                      second: Any = None) -> FailureEscalation:
    """Derive one escalation from the two reports of one failure.

    *source* is a FosterBook, a FosterRegistry or
    a list of reports; *first* names one report of
    the failure, by report id or as the report
    itself. With *second* given, the pair is the
    escalation's two reports; without it, the
    first two held reports sharing the named
    report's member, slice and failure key, in
    held order, are the pair. The two reports must
    share member, slice and failure key - the
    same failure twice - and the account is read
    off them, in held order. Deriving is
    deterministic.
    """
    reports = _held_reports(source)
    head = _report_named(reports, first)
    if head.report_id is None:
        raise ValueError(
            "an escalation's reports must name report ids - "
            "an escalation is addressed by its reports")
    if second is not None:
        tail = _report_named(reports, second)
        if tail.report_id is None:
            raise ValueError(
                "an escalation's reports must name report ids")
        pair = (head, tail)
        held = [r.report_id for r in reports]
        if held.index(pair[0].report_id) > held.index(pair[1].report_id):
            raise ValueError(
                "an escalation's reports stand in held order")
    else:
        pair = tuple(
            r for r in reports
            if (r.member, r.slice_id, r.failure_key)
            == (head.member, head.slice_id, head.failure_key))[:2]
        if len(pair) < 2:
            raise ValueError(
                "the same failure twice escalates: only one "
                "report of this failure is held")
    one, two = pair
    if (one.member, one.slice_id, one.failure_key) != (
            two.member, two.slice_id, two.failure_key):
        raise ValueError(
            "an escalation holds the same failure twice: its "
            "reports disagree on member, slice or failure")
    if one.report_id == two.report_id:
        raise ValueError(
            "an escalation holds two different reports")
    return FailureEscalation(
        member=one.member, slice_id=one.slice_id,
        failure_key=one.failure_key,
        report_ids=(one.report_id, two.report_id),
        account=_escalation_account(one, two))


def validate_escalation(escalation: Any,
                        source: Any = None) -> FailureEscalation:
    """Validate one escalation into a FailureEscalation.

    Accepts a FailureEscalation or a mapping naming
    a ``member`` (or ``member_id``), a ``slice_id``
    (or ``slice``), a ``failure_key`` (or
    ``failure`` / ``key``), ``report_ids`` (or
    ``reports``), an ``account`` (or ``statements``)
    and an optional ``escalation_id`` (or ``id``).
    When *source* is given (a book, a registry or a
    list of reports), the escalation is judged
    against the escalation derived from those
    reports: member, slice, failure, reports and
    any stored account must equal the derived
    ones (a missing account is read off the
    reports). A stored escalation naming no
    account of its own and judged against no
    reports refuses, because an account is derived
    off the reports, never stored loose.
    """
    derived = None
    if source is not None:
        ref = None
        if isinstance(escalation, FailureEscalation):
            ref = escalation.report_ids[0] if escalation.report_ids else None
        elif isinstance(escalation, dict):
            ids = _pick_any(
                escalation, ("report_ids", "reports"), "reports")
            if isinstance(ids, (list, tuple)) and ids:
                ref = ids[0]
        if ref is None:
            raise ValueError("an escalation is missing its reports")
        derived = derive_escalation(source, ref)
    if isinstance(escalation, FailureEscalation):
        current = escalation
    elif isinstance(escalation, dict):
        unknown = set(escalation) - _ESCALATION_KEYS
        if unknown:
            raise ValueError(
                "unknown escalation keys: %s"
                % ", ".join(sorted(unknown)))
        member = _pick_any(
            escalation, ("member", "member_id"), "members")
        if member is None:
            if derived is None:
                raise ValueError("an escalation is missing its member")
            member = derived.member
        slice_id = _pick_any(
            escalation, ("slice_id", "slice"), "slices")
        if slice_id is None:
            if derived is None:
                raise ValueError("an escalation is missing its slice")
            slice_id = derived.slice_id
        failure = _pick_any(
            escalation, ("failure_key", "failure", "key"), "failures")
        if failure is None:
            if derived is None:
                raise ValueError("an escalation is missing its failure")
            failure = derived.failure_key
        report_ids = _pick_any(
            escalation, ("report_ids", "reports"), "reports")
        if report_ids is None:
            if derived is None:
                raise ValueError("an escalation is missing its reports")
            report_ids = derived.report_ids
        account = _pick_any(
            escalation, ("account", "statements"), "accounts")
        if account is None:
            if derived is None:
                raise ValueError(
                    "a stored escalation names no account of its "
                    "own - derive it from its reports")
            account = derived.account
        esc_id = _pick_any(
            escalation, ("escalation_id", "id"), "escalation ids")
        current = FailureEscalation(
            escalation_id=esc_id, member=member, slice_id=slice_id,
            failure_key=failure, report_ids=report_ids,
            account=account)
    else:
        raise ValueError(
            f"an escalation must be a mapping, got {escalation!r}")
    if derived is not None:
        for field, label in (
                ("member", "member"), ("slice_id", "slice"),
                ("failure_key", "failure")):
            if getattr(current, field) != getattr(derived, field):
                raise ValueError(
                    f"an escalation's {label} disagrees with "
                    f"its reports")
        if current.report_ids != derived.report_ids:
            raise ValueError(
                "a stored escalation's reports disagree with "
                "the reports derived from the held reports - "
                "an escalation is derived off its reports, "
                "never stored loose")
        if current.account != derived.account:
            raise ValueError(
                "a stored escalation's account disagrees with "
                "the account derived from its reports - an "
                "account is derived off the reports, never "
                "stored loose")
    return current


def build_escalation(escalation: Any = None, source: Any = None,
                     **kwargs: Any) -> FailureEscalation:
    """Build one validated escalation, from a mapping or field words."""
    if isinstance(escalation, FailureEscalation) and not kwargs \
            and source is None:
        return escalation
    if isinstance(escalation, dict) or escalation is None:
        merged: Dict[str, Any] = {}
        if isinstance(escalation, dict):
            merged.update(escalation)
        merged.update(kwargs)
        return validate_escalation(merged, source)
    return validate_escalation(escalation, source)


# ---------------------------------------------------------------------
# The book: one fostering whole, under a title.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class FosterBook:
    """One fostering book, whole, as data.

    ``title`` names the book; ``assignments`` are
    the original dealings (M-125 assignments, read
    by that layer), one per slice; ``reports`` are
    the failure reports in held order, each naming
    a report id; ``redeals`` are fostered re-deals,
    each judged as the book is built - its dealing
    and report must be the book's own held records
    and its account its derived account;
    ``escalations`` are escalations, each judged
    against this book's reports as the book is
    built, so a held escalation's account is
    always its reports' derived account.
    """

    title: str = ""
    assignments: Tuple[DealtAssignment, ...] = ()
    reports: Tuple[FailureReport, ...] = ()
    redeals: Tuple[FosteredRedeal, ...] = ()
    escalations: Tuple[FailureEscalation, ...] = ()
    fostering_note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_short_text(self.title, "a title"))
        assignments = tuple(
            a if isinstance(a, DealtAssignment)
            else validate_assignment(a) for a in self.assignments)
        if not assignments:
            raise ValueError("a fostering book holds at least one dealing")
        slices = [a.slice_id for a in assignments]
        if len(set(slices)) != len(slices):
            raise ValueError("a book deals one slice twice")
        object.__setattr__(self, "assignments", assignments)
        reports = tuple(
            r if isinstance(r, FailureReport) else validate_report(r)
            for r in self.reports)
        if not reports:
            raise ValueError("a fostering book holds at least one report")
        for report in reports:
            if report.report_id is None:
                raise ValueError("a book's reports name report ids")
        ids = [r.report_id for r in reports]
        if len(set(ids)) != len(ids):
            raise ValueError("a book holds one report id twice")
        object.__setattr__(self, "reports", reports)
        held_dealings = {a.slice_id: a for a in assignments}
        held_reports = {r.report_id: r for r in reports}
        redeals = []
        for raw in self.redeals:
            current = validate_redeal(raw)
            dealt = held_dealings.get(current.slice_id)
            if dealt is None or dealt != current.assignment:
                raise ValueError(
                    "a re-deal names a dealing the book holds "
                    "no assignment for")
            noted = held_reports.get(current.report.report_id)
            if noted is None or noted != current.report:
                raise ValueError(
                    "a re-deal names a report the book holds "
                    "no report for")
            redeals.append(current)
        redeal_ids = [r.redeal_id for r in redeals if r.redeal_id]
        if len(set(redeal_ids)) != len(redeal_ids):
            raise ValueError("a book holds one re-deal id twice")
        object.__setattr__(self, "redeals", tuple(redeals))
        escalations = []
        for raw in self.escalations:
            ref = raw.report_ids[0] if isinstance(
                raw, FailureEscalation) else _pick_any(
                    raw, ("report_ids", "reports"), "reports")
            if not ref:
                raise ValueError("an escalation is missing its reports")
            first = ref[0] if isinstance(ref, (list, tuple)) else ref
            if normalize_member_id(first) not in held_reports:
                raise ValueError(
                    "an escalation names a report the book "
                    "holds no report for")
            escalations.append(validate_escalation(raw, source=reports))
        esc_ids = [e.escalation_id for e in escalations if e.escalation_id]
        if len(set(esc_ids)) != len(esc_ids):
            raise ValueError("a book holds one escalation id twice")
        object.__setattr__(self, "escalations", tuple(escalations))
        if not isinstance(self.fostering_note, str):
            raise ValueError("a fostering book's note must be text")
        object.__setattr__(
            self, "fostering_note", self.fostering_note.strip())

    def assignment_for(self, slice_id: Any) -> DealtAssignment:
        """The dealing one slice names in this book."""
        wanted = normalize_slice_id(slice_id)
        for assignment in self.assignments:
            if assignment.slice_id == wanted:
                return assignment
        raise KeyError(f"no dealing in the book: {wanted!r}")

    def report_for(self, report_id: Any) -> FailureReport:
        """The report one id names in this book."""
        wanted = normalize_member_id(report_id)
        for report in self.reports:
            if report.report_id == wanted:
                return report
        raise KeyError(f"no report in the book: {wanted!r}")

    def reports_for(self, member: Any) -> Tuple[FailureReport, ...]:
        """Every report one member filed, in held order."""
        wanted = normalize_member_id(member)
        return tuple(r for r in self.reports if r.member == wanted)

    def redeal_for(self, redeal_id: Any) -> FosteredRedeal:
        """The re-deal one id names in this book."""
        wanted = normalize_member_id(redeal_id)
        for redeal in self.redeals:
            if redeal.redeal_id == wanted:
                return redeal
        raise KeyError(f"no re-deal in the book: {wanted!r}")

    def escalation_for(self, escalation_id: Any) -> FailureEscalation:
        """The escalation one id names in this book."""
        wanted = normalize_member_id(escalation_id)
        for escalation in self.escalations:
            if escalation.escalation_id == wanted:
                return escalation
        raise KeyError(f"no escalation in the book: {wanted!r}")

    def report_ids(self) -> Tuple[str, ...]:
        """Every held report id, in held order."""
        return tuple(r.report_id for r in self.reports if r.report_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "failure_fostering_book",
            "slice": FAILURE_FOSTERING_SLICE,
            "title": self.title,
            "report_ids": list(self.report_ids()),
            "assignment_count": len(self.assignments),
            "report_count": len(self.reports),
            "redeal_count": len(self.redeals),
            "escalation_count": len(self.escalations),
        }


def validate_book(data: Any, *, require_example: bool = False) -> FosterBook:
    """Validate one fostering mapping into a FosterBook.

    The mapping names a ``schema`` (the fostering
    schema word), a ``guide`` mapping (its
    ``title``), an ``assignments`` list, a
    ``reports`` list and optional ``redeals`` and
    ``escalations`` lists. Every dealing is read
    by the task-dealing layer, then the whole is
    judged: one dealing per slice, report ids
    unique, every re-deal judged against its own
    derived account and the book's held records,
    and every escalation judged against the book's
    reports. With ``require_example`` the shipped
    example is held to its pinned shape: the
    pinned title, assignments and reports, and the
    pinned re-deal and escalation carrying their
    pinned accounts word-for-word. Problems raise
    :class:`ValidationError` or ``ValueError``.
    """
    if isinstance(data, FosterBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a fostering book must be a mapping, got {data!r}")
    unknown = set(data) - _FOSTER_KEYS
    if unknown:
        raise ValidationError(
            "unknown fostering keys: %s" % ", ".join(sorted(unknown)))
    if data.get("schema") != FAILURE_FOSTERING_SCHEMA:
        raise ValidationError(
            f"a fostering book must carry schema "
            f"{FAILURE_FOSTERING_SCHEMA!r}, got {data.get('schema')!r}")
    for field in ("assignments", "reports"):
        if field not in data:
            raise ValidationError(f"a fostering book is missing its {field}")
        if not isinstance(data[field], (list, tuple)):
            raise ValidationError(f"a fostering book's {field} must be a list")
    for field in ("redeals", "escalations"):
        if data.get(field) is not None \
                and not isinstance(data[field], (list, tuple)):
            raise ValidationError(f"a fostering book's {field} must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a fostering book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a fostering book is missing its title")
        note = data.get("fostering_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a fostering book's note must be text")
        book = FosterBook(
            title=title, assignments=tuple(data["assignments"]),
            reports=tuple(data["reports"]),
            redeals=tuple(data.get("redeals") or ()),
            escalations=tuple(data.get("escalations") or ()),
            fostering_note=note)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if require_example:
        if book.title != _EXAMPLE_TITLE:
            raise ValidationError(
                "the shipped example fostering book's title is "
                "not the pinned title")
        if tuple(a.slice_id for a in book.assignments) != (
                _EXAMPLE_ASSIGNMENT_SLICES):
            raise ValidationError(
                "the shipped example's dealings are not the "
                "pinned dealings")
        if book.report_ids() != _EXAMPLE_REPORT_IDS:
            raise ValidationError(
                "the shipped example's reports are not the "
                "pinned reports")
        redeal = book.redeal_for(_EXAMPLE_REDEAL_ID)
        if redeal.foster_member != _EXAMPLE_REDEAL_FOSTER:
            raise ValidationError(
                "the shipped example re-deal does not name its "
                "pinned fostering member")
        if redeal.account != _EXAMPLE_REDEAL_ACCOUNT:
            raise ValidationError(
                "the shipped example re-deal does not carry its "
                "pinned account word-for-word")
        escalation = book.escalation_for(_EXAMPLE_ESCALATION_ID)
        if escalation.report_ids != _EXAMPLE_ESCALATION_REPORTS:
            raise ValidationError(
                "the shipped example escalation does not name "
                "its pinned reports")
        if escalation.account != _EXAMPLE_ESCALATION_ACCOUNT:
            raise ValidationError(
                "the shipped example escalation does not carry "
                "its pinned account word-for-word")
        if escalation.recipient != HUMAN_RECIPIENT:
            raise ValidationError(
                "the shipped example escalation does not go "
                "to the human")
    return book


def build_book(book: Any = None, **kwargs: Any) -> FosterBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, FosterBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "assignments" in book or "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return FosterBook(**merged)
    if book is None:
        return FosterBook(**kwargs)
    raise ValueError(f"a fostering book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> FosterBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_failure_fostering(
        data: Optional[Dict[str, Any]] = None) -> FosterBook:
    """Load and validate the shipped example book (or *data*).

    The shipped file is held to the example check:
    the pinned title, dealings and reports, and the
    pinned re-deal and escalation - the replay-gap
    failure fostered by the auditor and escalated
    with both its reports - so the shipped book
    covers the boundary this slice exists to hold.
    """
    raw = data if data is not None else load_resource(
        FAILURE_FOSTERING_RESOURCE)
    return _book_from(raw, require_example=True)


def load_failure_fostering_file(path: Any) -> FosterBook:
    """Load and validate a fostering book from a file at *path*.

    Any file in the fostering shape, anywhere on
    disk, validated whole - a malformed file raises
    :class:`ValidationError` naming the problem,
    and a missing file raises ``FileNotFoundError``.
    The example check is not held: a real fostering
    book stands on its own records.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held record by record, in held order.
# ---------------------------------------------------------------------


class FosterRegistry:
    """One session's fostering book, held record by record.

    The registry holds dealings and reports, never
    re-deals or escalations: both are derivations,
    read off held records at call time, so nothing
    here can hold an account stale.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._assignments: Dict[str, DealtAssignment] = {}
        self._reports: Dict[str, FailureReport] = {}
        self._order: list = []
        self._next_report = 1
        if book is not None:
            self.register_book(book)

    def _fresh_report_id(self, held_ids: Any) -> str:
        while f"fostering-{self._next_report}" in held_ids:
            self._next_report += 1
        fresh = f"fostering-{self._next_report}"
        self._next_report += 1
        return fresh

    def register_assignment(self, assignment: Any) -> DealtAssignment:
        """Register one original dealing into the held book."""
        validated = build_assignment(assignment)
        if validated.slice_id in self._assignments:
            raise ValueError(
                f"a dealing for {validated.slice_id!r} already exists")
        self._assignments[validated.slice_id] = validated
        return validated

    def register_report(self, report: Any) -> FailureReport:
        """Register one failure report into the held book.

        A report with no id is given a deterministic
        ``fostering-N`` id. A report id already
        standing here refuses.
        """
        validated = build_report(report)
        held_ids = set(self._reports)
        if validated.report_id is not None \
                and validated.report_id in held_ids:
            raise ValueError(
                f"a report named {validated.report_id!r} already exists")
        if validated.report_id is None:
            validated = replace(
                validated, report_id=self._fresh_report_id(held_ids))
        self._reports[validated.report_id] = validated
        self._order.append(validated.report_id)
        return validated

    def register_book(self, book: Any) -> FosterBook:
        """Register every dealing and report of one book, in order.

        The first book held sets the title; a later
        book under a different title refuses, as does
        a book naming a held slice or report id. The
        book's re-deals and escalations are
        derivations, not holdings, and are not held.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a fostering book "
                "under a different title")
        for assignment in validated.assignments:
            if assignment.slice_id in self._assignments:
                raise ValueError(
                    f"a dealing for {assignment.slice_id!r} "
                    f"already exists")
        for report in validated.reports:
            if report.report_id in self._reports:
                raise ValueError(
                    f"a report named {report.report_id!r} "
                    f"already exists")
        self._title = validated.title
        for assignment in validated.assignments:
            self.register_assignment(assignment)
        for report in validated.reports:
            self.register_report(report)
        return self.book()

    def get_assignment(self, slice_id: Any) -> DealtAssignment:
        """The dealing one slice names among the held dealings."""
        wanted = normalize_slice_id(slice_id)
        if wanted not in self._assignments:
            raise KeyError(f"unknown dealing: {wanted!r}")
        return self._assignments[wanted]

    def get_report(self, report_id: Any) -> FailureReport:
        """The report one id names among the held reports."""
        wanted = normalize_member_id(report_id)
        if wanted not in self._reports:
            raise KeyError(f"unknown report: {wanted!r}")
        return self._reports[wanted]

    def list_assignments(self) -> Tuple[DealtAssignment, ...]:
        """Every held dealing, in the order they were held."""
        return tuple(self._assignments.values())

    def list_reports(self) -> Tuple[FailureReport, ...]:
        """Every held report, in the order they were held."""
        return tuple(self._reports[r] for r in self._order)

    def book(self) -> FosterBook:
        """The held dealings and reports as one validated book."""
        if self._title is None:
            raise ValueError("no fostering book is held yet")
        return FosterBook(
            title=self._title, assignments=self.list_assignments(),
            reports=self.list_reports())

    def redeal_for(self, slice_id: Any,
                   foster_member: Any) -> FosteredRedeal:
        """Derive the re-deal for one held slice, at call time.

        The re-deal is derived from the held dealing
        for the slice, the first held report judging
        it, and the fostering member named.
        """
        dealt = self.get_assignment(slice_id)
        for report in self.list_reports():
            if report.member == dealt.member \
                    and report.slice_id == dealt.slice_id:
                return derive_redeal(dealt, report, foster_member)
        raise KeyError(
            f"no held report judges the dealing: {dealt.slice_id!r}")

    def escalation_for(self, report: Any) -> FailureEscalation:
        """Derive the escalation for one held report, at call time.

        The account is the held reports' own words,
        read at call time - the registry holds
        reports, and this escalation is derived
        from them.
        """
        return derive_escalation(self.list_reports(), report)


# ---------------------------------------------------------------------
# Fostering news, shaped as session records.
# ---------------------------------------------------------------------


def report_record(report: Any) -> Dict[str, Any]:
    """The session-news record of one failure report."""
    current = report if isinstance(report, FailureReport) \
        else build_report(report)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.member} reported failure "
        f"'{current.failure_key}' on {current.slice_id}: "
        f"'{current.title}'.")
    return record


def redeal_record(redeal: Any, assignment: Any = None,
                  report: Any = None) -> Dict[str, Any]:
    """The session-news record of one fostered re-deal.

    With *assignment* / *report* given, the re-deal
    is first judged against them.
    """
    current = validate_redeal(redeal, assignment, report)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Slice {current.slice_id} re-dealt from "
        f"{current.member} to {current.foster_member} "
        f"with its failure report attached.")
    return record


def escalation_record(escalation: Any,
                      source: Any = None) -> Dict[str, Any]:
    """The session-news record of one escalation.

    With *source* given, the escalation is first
    judged against the reports it belongs to.
    """
    current = validate_escalation(escalation, source)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Failure '{current.failure_key}' on "
        f"{current.slice_id} escalates to the human "
        f"with both reports attached.")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one fostering book."""
    current = book if isinstance(book, FosterBook) else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Fostering book {current.title}: "
        f"{record['report_count']} report(s), "
        f"{record['redeal_count']} re-deal(s), "
        f"{record['escalation_count']} escalation(s).")
    return record


def plain_words(report: Any) -> str:
    """One failure report, in one plain sentence."""
    current = report if isinstance(report, FailureReport) \
        else build_report(report)
    return (
        f"{current.member} reported failure "
        f"'{current.failure_key}' on {current.slice_id}: "
        f"'{current.title}' - {current.body}")


def redeal_plain_words(source: Any) -> str:
    """Re-deals in plain words: every re-deal, in full.

    Accepts a FosteredRedeal or a FosterBook.
    Each re-deal is told whole - its dealing, its
    fostering member and its account.
    """
    if isinstance(source, FosteredRedeal):
        redeals = (validate_redeal(source),)
        title = None
    elif isinstance(source, FosterBook):
        redeals = source.redeals
        title = source.title
    else:
        raise ValueError(f"a fostering source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    for redeal in redeals:
        lines.append(
            f"{redeal.slice_id} - fostered by {redeal.foster_member}")
        lines.extend(redeal.account)
    return "\n".join(lines)


def escalation_plain_words(source: Any) -> str:
    """Escalations in plain words: every escalation, in full.

    Accepts a FailureEscalation or a FosterBook.
    Each escalation is told whole - its failure,
    its member and its account.
    """
    if isinstance(source, FailureEscalation):
        escalations = (source,)
        title = None
    elif isinstance(source, FosterBook):
        escalations = source.escalations
        title = source.title
    else:
        raise ValueError(f"a fostering source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    for escalation in escalations:
        lines.append(
            f"{escalation.failure_key} on {escalation.slice_id} "
            f"- escalated by {escalation.member} to the human")
        lines.extend(escalation.account)
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Screens: the formatters and the shared /foster grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> FosterBook:
    if source is None:
        return load_failure_fostering()
    if isinstance(source, FosterRegistry):
        return source.book()
    if isinstance(source, FosterBook):
        return source
    raise ValueError(f"a fostering book is needed, got {source!r}")


def format_report(report: Any) -> str:
    """One failure report as a screen line."""
    current = report if isinstance(report, FailureReport) \
        else build_report(report)
    return (
        f"{current.report_id or '-'}: {current.member} "
        f"[{current.failure_key}] '{current.title}' "
        f"({current.slice_id})")


def format_reports(source: Any = None, member: Any = None) -> str:
    """Reports of one book, in held order.

    With *member* given, only that member's
    reports are shown.
    """
    book = _source_book(source)
    reports = book.reports if member is None else book.reports_for(member)
    lines = [format_report(report) for report in reports]
    if not lines:
        lines.append("No failure reports are held.")
    return "\n".join(lines)


def format_redeal(source: Any = None) -> str:
    """Re-deals as screen blocks: dealing over derived account.

    Accepts a FosteredRedeal or a FosterBook; a
    book shows every re-deal it holds, in book
    order.
    """
    if isinstance(source, FosteredRedeal):
        redeals = (validate_redeal(source),)
        lines: list = []
    else:
        book = _source_book(source)
        redeals = book.redeals
        lines = [f"Re-deals in {book.title}:"]
    for redeal in redeals:
        lines.append(
            f"{redeal.slice_id} - {redeal.member} -> "
            f"{redeal.foster_member} (report attached)")
        lines.extend(redeal.account)
    if isinstance(source, FosteredRedeal):
        return "\n".join(lines)
    if len(lines) == 1:
        lines.append("Nothing here.")
    return "\n".join(lines)


def format_escalation(source: Any = None) -> str:
    """Escalations as screen blocks: failure over derived account.

    Accepts a FailureEscalation or a FosterBook; a
    book shows every escalation it holds, in book
    order.
    """
    if isinstance(source, FailureEscalation):
        escalations = (source,)
        lines: list = []
    else:
        book = _source_book(source)
        escalations = book.escalations
        lines = [f"Escalations in {book.title}:"]
    for escalation in escalations:
        lines.append(
            f"{escalation.failure_key} on {escalation.slice_id} "
            f"- {escalation.member} -> human (both reports "
            f"attached)")
        lines.extend(escalation.account)
    if isinstance(source, FailureEscalation):
        return "\n".join(lines)
    if len(lines) == 1:
        lines.append("Nothing here.")
    return "\n".join(lines)


def format_fostering_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /foster.

    With nothing named, the shipped example
    fostering book is shown - the example this
    slice ships - so the screen is never empty.
    """
    book = _source_book(source)
    lines = ["Failure fostering (M-139) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_reports(book))
    lines.append("")
    lines.append(format_redeal(book))
    lines.append("")
    lines.append(format_escalation(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_fostering_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /foster grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    fostering book; ``report <report-id>`` shows
    one report; ``redeal <slice-id>`` derives the
    re-deal of that slice's dealing; ``escalation
    <report-id>`` derives the escalation of that
    report's failure. Anything else is a usage
    error naming the grammar. Returns
    ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head in ("report", "escalation") and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "redeal" and len(words) == 2:
        try:
            return (head, normalize_slice_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
