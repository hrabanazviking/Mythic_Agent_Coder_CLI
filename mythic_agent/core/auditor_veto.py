"""The Auditor's veto (All-Features roadmap slice M-130).

Part VI - Agents as files - continues here. The
roadmap's words: ``no slice is "done" until the
Auditor's checks pass; the veto is a real gate in
the engine, not a custom.``

What already shipped, and what this slice adds:

* The crew itself is already data
  (``core/crew_members.py``, M-121: the casting
  holds an ``auditor`` member, Sólrún Hvítmynd,
  whose office is verify), the offices are
  formalised (M-122, M-123), and the worktrees,
  dealing, comms, deadlock watch, merge discipline
  and heterogeneous crews are already data (M-124
  to M-129). What nothing held is the Auditor's
  gate itself: which slices stand before the
  Auditor, which checks each slice carries, and
  what the Auditor's run of those checks found -
  so today a slice is "done" when its builder says
  so, a check that was never run looks the same as
  one that passed, and no record anywhere can veto
  a banking.
* This slice is that gate, as a pure layer: the
  evidence validated as data (a case - one slice
  standing before the Auditor, with its title and
  its builder; a check - one check the slice
  carries, required or not; and a result - what
  the Auditor's run of one check found, passed or
  failed, with the evidence for it), the shipped
  data file (``mythic_agent/data/auditor_veto.yaml``)
  holding one example veto ledger in exactly the
  shape a real ledger's file takes, a loader for a
  ledger file anywhere on disk, the verdicts and
  the gate state of every case derived mechanically
  from the evidence alone, a verdict record and a
  report record shaped as session news, and a small
  in-memory registry model. This module runs no
  check, executes no test suite, banks nothing and
  imports no agent / UI code; the agent layer owns
  holding the ledger for a session and handing the
  verdicts to the coordinator, and the banking road
  (M-205, M-206 - later slices, not yet shipped) is
  where a vetoed slice will be refused in code.

Honesty rules, enforced here and pinned by tests:

* **Verdicts are derived, never stored.** A
  report is computed from the cases, checks and
  results it is judged under, so it can never
  disagree with them; the same evidence always
  yields the same verdicts and the same gates
  (deterministic order, deterministic wording).
* **The Auditor is the shipped office.** The
  ledger's keeper is the M-121 casting's
  ``auditor`` member, member ids read exactly as
  the M-121 layer reads them
  (``core/crew_members.py``), and slice ids read
  exactly as the M-124 layer reads them
  (``core/worktrees.py``) - composed by import,
  never re-read here.
* **The verdicts are the roadmap's two vetoes.**
  A verdict is ``failed_check`` (a required check
  the slice carries was run and the Auditor's
  result says it failed) or ``unproven_check``
  (a required check the slice carries holds no
  result at all - a check with no evidence has
  not passed) - no other kind is read, and an
  unknown kind refuses. Each required check earns
  at most one verdict. A check that is not
  required never vetoes: the gate is the required
  checks, stated plainly. Passing is not a
  verdict: it is a case's gate state, derived
  beside the verdicts - a case passes exactly when
  every required check it carries holds a passing
  result, and is vetoed exactly when it holds a
  verdict.
* **The veto is data only; no check is run
  here.** No test suite is executed, no slice is
  banked or merged and no engine road is hooked
  in this slice: a verdict here is a validated
  record derived from given evidence, not an
  action taken, and the coordinator acts on the
  verdicts through later roads. No engine banking
  road exists in the shipped tree yet to wire the
  veto into (the banking discipline is M-205 /
  M-206, still queued), so nothing here claims
  one was wired. The roadmap names the board
  (Part VIII) as where crew state will be
  visible; that board does not exist yet, so the
  verdicts are visible through this slice's own
  /veto screen, and nothing here claims a board
  exists.
* **Malformed refuses.** An unknown kind or
  outcome, a malformed slice, member or check
  name, a slice audited twice, a check carried
  twice by one slice, two results for one check,
  a case carrying no checks at all, and unknown
  keys in a case, a check, a result, a verdict or
  a ledger mapping all raise instead of being
  skipped or guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .validation import ValidationError
from .worktrees import normalize_slice_id

__all__ = [
    "PLAIN_EXPLANATION",
    "USAGE",
    "VERDICT_KINDS",
    "VETO_RESOURCE",
    "VETO_SCHEMA",
    "VETO_SLICE",
    "AuditCase",
    "AuditCheck",
    "AuditResult",
    "AuditorLedger",
    "AuditorVetoRegistry",
    "GateState",
    "VetoReport",
    "VetoVerdict",
    "build_case",
    "build_check",
    "build_result",
    "build_verdict",
    "case_record",
    "check_record",
    "format_gates",
    "format_kinds",
    "format_verdict",
    "format_verdicts",
    "format_veto_screen",
    "judge_veto",
    "load_auditor_ledger",
    "load_auditor_ledger_file",
    "normalize_check_name",
    "normalize_outcome",
    "normalize_verdict_kind",
    "parse_veto_args",
    "plain_words",
    "report_plain_words",
    "report_record",
    "result_record",
    "validate_case",
    "validate_check",
    "validate_ledger",
    "validate_report",
    "validate_result",
    "validate_verdict",
    "verdict_record",
]

VETO_SLICE = "M-130"

#: The packaged data resource holding the example veto ledger.
VETO_RESOURCE = "auditor_veto.yaml"

#: The schema word a veto ledger file must carry.
VETO_SCHEMA = "mythic.auditor_veto/1"

#: The verdict kinds, in roadmap order: the check
#: that failed, then the check with no evidence.
VERDICT_KINDS = (
    "failed_check", "unproven_check")

_KIND_READINGS = {
    "failed": "failed_check",
    "fail": "failed_check",
    "failed_check": "failed_check",
    "red": "failed_check",
    "unproven": "unproven_check",
    "unproven_check": "unproven_check",
    "missing": "unproven_check",
    "no_evidence": "unproven_check",
    "unchecked": "unproven_check",
}

_OUTCOME_READINGS = {
    "passed": "passed",
    "pass": "passed",
    "green": "passed",
    "ok": "passed",
    "failed": "failed",
    "fail": "failed",
    "red": "failed",
}

#: The gate standings a case's gate state may carry.
_GATE_STATUSES = ("passed", "vetoed")

PLAIN_EXPLANATION = (
    "The Auditor's veto: no slice is done until "
    "the Auditor's checks pass - the veto is a "
    "gate, not a custom. Every verdict is derived "
    "from the given cases, checks and results "
    "alone: a required check that failed vetoes "
    "its slice, and a required check with no "
    "result at all vetoes it too, because a check "
    "with no evidence has not passed. There is no "
    "Part VIII board yet, so the verdicts are "
    "visible on this slice's own screen, not on a "
    "board. This layer holds the audit as data "
    "only; it runs no check, executes no test "
    "suite and banks nothing itself - the "
    "coordinator acts on the verdicts through "
    "later roads."
)

USAGE = (
    "Usage: /veto, /veto show, "
    "/veto show <slice>, /veto gates, "
    "/veto kinds"
)

_CASE_KEYS = frozenset({
    "id", "case_id", "slice", "slice_id",
    "title", "builder", "builder_id",
})

_CHECK_KEYS = frozenset({
    "id", "check_id", "slice", "slice_id",
    "name", "check", "check_name",
    "required", "is_required",
})

_RESULT_KEYS = frozenset({
    "id", "result_id", "slice", "slice_id",
    "check", "check_name", "name",
    "outcome", "result", "status",
    "evidence", "note",
})

_VERDICT_KEYS = frozenset({
    "kind", "verdict_kind", "slice", "slice_id",
    "check", "check_name", "title", "detail",
})

_LEDGER_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "ledger_note", "keeper", "cases", "checks",
    "results",
})

#: The shipped example ledger's cases, in file
#: order: (slice_id, title, builder). The shipped
#: data file is held to exactly this list by the
#: loader's example check: M-128 passes, M-129 is
#: vetoed on a failed check and M-127 is vetoed on
#: a check with no evidence.
_EXAMPLE_CASES = (
    ("M-127", "Cycle and deadlock detection grown",
     "cartographer"),
    ("M-128", "Merge discipline", "forge_worker"),
    ("M-129", "Heterogeneous crews", "scribe"),
)

#: The shipped example ledger's checks, in file
#: order: (slice_id, name, required) - the checks
#: each audited slice carries, all required.
_EXAMPLE_CHECKS = (
    ("M-127", "suite-green", True),
    ("M-127", "neighbour-suites-green", True),
    ("M-128", "suite-green", True),
    ("M-128", "banking-order-kept", True),
    ("M-129", "suite-green", True),
    ("M-129", "banking-order-kept", True),
)

#: The shipped example ledger's results, in file
#: order: (slice_id, check, outcome). M-127's
#: suite-green holds no result at all - the
#: unproven half of the example - and M-129's
#: suite-green was run and failed.
_EXAMPLE_RESULTS = (
    ("M-127", "neighbour-suites-green", "passed"),
    ("M-128", "suite-green", "passed"),
    ("M-128", "banking-order-kept", "passed"),
    ("M-129", "suite-green", "failed"),
    ("M-129", "banking-order-kept", "passed"),
)


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_title(value: Any) -> str:
    title = _clean_text(value, "a title")
    if len(title) > 200 or "\x00" in title:
        raise ValueError(
            f"a title must be plain text of at most "
            f"200 characters, got {len(title)} characters")
    return title


def _check_long_text(value: Any, what: str) -> str:
    text = _clean_text(value, what)
    if len(text) > 2000 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"2000 characters, got {len(text)} characters")
    return text


def normalize_check_name(value: Any) -> str:
    """The canonical check name a word names.

    Check words read case-insensitively, with
    spaces and underscores read as dashes: a name
    is dashes joining words of letters and digits,
    at most 100 characters. Anything else raises.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace(
            "_", "-").replace(" ", "-")
        parts = wanted.split("-")
        if wanted and len(wanted) <= 100 and all(
                part.isalnum() for part in parts):
            return wanted
    raise ValueError(
        f"a check name must be dash-joined words of "
        f"letters and digits, got {value!r}")


def normalize_outcome(value: Any) -> str:
    """The canonical result outcome a word names.

    Outcome words read case-insensitively: ``pass``
    and ``green`` read as passed, ``fail`` and
    ``red`` read as failed. Anything else raises -
    an outcome is passed or failed, never a maybe.
    """
    if isinstance(value, str):
        wanted = value.strip().lower()
        if wanted in _OUTCOME_READINGS:
            return _OUTCOME_READINGS[wanted]
    raise ValueError(
        "a result outcome must be passed or failed, "
        f"got {value!r}")


def normalize_verdict_kind(value: Any) -> str:
    """The canonical verdict kind a word names.

    Kind words read case-insensitively, with dashes
    read as underscores; the plain words ``failed``
    and ``unproven`` read as the one canonical kind
    each names. Anything else raises.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted in _KIND_READINGS:
            return _KIND_READINGS[wanted]
    raise ValueError(
        "a verdict kind must be one of %s, got %r"
        % ("/".join(VERDICT_KINDS), value))


def _pick(mapping: Dict[str, Any], first: str, second: str,
          what: str) -> Any:
    """One field from its two spellings, or a refusal."""
    if first in mapping and second in mapping:
        if mapping[first] != mapping[second]:
            raise ValueError(f"a record names two different {what}")
        return mapping[first]
    if first in mapping:
        return mapping[first]
    return mapping.get(second)


def _pick_any(mapping: Dict[str, Any], spellings: Tuple[str, ...],
              what: str) -> Any:
    """One field from any of its spellings, or a refusal.

    Every spelling present must name the same
    value; two different values under two spellings
    of one field refuse, exactly as the two-spelling
    reading refuses.
    """
    values = [mapping[s] for s in spellings if s in mapping]
    if not values:
        return None
    if any(value != values[0] for value in values[1:]):
        raise ValueError(f"a record names two different {what}")
    return values[0]


# ---------------------------------------------------------------------
# The case: one slice standing before the Auditor, as evidence.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class AuditCase:
    """One slice standing before the Auditor, as data.

    ``slice_id`` is the roadmap slice under audit,
    read as the M-124 layer reads one; ``title`` is
    the slice's own title; ``builder`` is the M-121
    member who built it. Constructing one validates
    its shape only: which checks the slice carries
    and what they found are the ledger's and the
    judge's concerns, not the validator's.
    """

    case_id: Optional[str] = None
    slice_id: str = ""
    title: str = ""
    builder: str = ""

    def __post_init__(self) -> None:
        if self.case_id is not None:
            object.__setattr__(
                self, "case_id",
                normalize_member_id(self.case_id))
        object.__setattr__(
            self, "slice_id",
            normalize_slice_id(self.slice_id))
        object.__setattr__(
            self, "title", _check_title(self.title))
        object.__setattr__(
            self, "builder",
            normalize_member_id(self.builder))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "veto_case",
            "slice": VETO_SLICE,
            "case_id": self.case_id,
            "slice_id": self.slice_id,
            "title": self.title,
            "builder": self.builder,
        }


def validate_case(case: Any) -> AuditCase:
    """Validate one case into an AuditCase.

    Accepts an AuditCase or a mapping naming a
    ``slice_id`` (or ``slice``), a ``title``, a
    ``builder`` (or ``builder_id``) and an optional
    ``case_id`` (or ``id``). Naming both spellings
    of one field with different values refuses, and
    unknown keys refuse.
    """
    if isinstance(case, AuditCase):
        return case
    if not isinstance(case, dict):
        raise ValueError(
            f"a case must be a mapping, got {case!r}")
    unknown = set(case) - _CASE_KEYS
    if unknown:
        raise ValueError(
            "unknown case keys: %s"
            % ", ".join(sorted(unknown)))
    slice_id = _pick(case, "slice_id", "slice", "slices")
    if slice_id is None:
        raise ValueError("a case is missing its slice")
    if "title" not in case:
        raise ValueError("a case is missing its title")
    builder = _pick(case, "builder", "builder_id", "builders")
    if builder is None:
        raise ValueError("a case is missing its builder")
    kwargs: Dict[str, Any] = {
        "slice_id": slice_id, "title": case["title"],
        "builder": builder,
    }
    case_id = _pick(case, "case_id", "id", "case ids")
    if case_id is not None:
        kwargs["case_id"] = case_id
    return AuditCase(**kwargs)


def build_case(
        case: Any = None, **kwargs: Any) -> AuditCase:
    """Build one validated case.

    From an AuditCase, from a mapping (the spellings
    :func:`validate_case` reads), or from field
    words given as keyword arguments.
    """
    if isinstance(case, AuditCase) and not kwargs:
        return case
    if isinstance(case, dict) or case is None:
        merged: Dict[str, Any] = {}
        if isinstance(case, dict):
            merged.update(case)
        merged.update(kwargs)
        return validate_case(merged)
    raise ValueError(
        f"a case must be a mapping, got {case!r}")


# ---------------------------------------------------------------------
# The check: one check a slice carries, as evidence.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class AuditCheck:
    """One check a slice carries, as data.

    ``slice_id`` is the slice that carries the
    check; ``name`` is the check's name; ``required``
    says whether the gate turns on it - a required
    check vetoes its slice when it fails or holds
    no result, and a check that is not required
    never vetoes. Constructing one validates its
    shape only: what the check found is the
    result's concern, not the validator's.
    """

    check_id: Optional[str] = None
    slice_id: str = ""
    name: str = ""
    required: bool = True

    def __post_init__(self) -> None:
        if self.check_id is not None:
            object.__setattr__(
                self, "check_id",
                normalize_member_id(self.check_id))
        object.__setattr__(
            self, "slice_id",
            normalize_slice_id(self.slice_id))
        object.__setattr__(
            self, "name", normalize_check_name(self.name))
        if not isinstance(self.required, bool):
            raise ValueError(
                f"a check's required must be true or "
                f"false, got {self.required!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "veto_check",
            "slice": VETO_SLICE,
            "check_id": self.check_id,
            "slice_id": self.slice_id,
            "name": self.name,
            "required": bool(self.required),
        }


def validate_check(check: Any) -> AuditCheck:
    """Validate one check into an AuditCheck.

    Accepts an AuditCheck or a mapping naming a
    ``slice_id`` (or ``slice``), a ``name`` (or
    ``check`` / ``check_name``), an optional
    ``required`` (or ``is_required``, true when
    unnamed) and an optional ``check_id`` (or
    ``id``). Naming both spellings of one field
    with different values refuses, and unknown
    keys refuse.
    """
    if isinstance(check, AuditCheck):
        return check
    if not isinstance(check, dict):
        raise ValueError(
            f"a check must be a mapping, got {check!r}")
    unknown = set(check) - _CHECK_KEYS
    if unknown:
        raise ValueError(
            "unknown check keys: %s"
            % ", ".join(sorted(unknown)))
    slice_id = _pick(check, "slice_id", "slice", "slices")
    if slice_id is None:
        raise ValueError("a check is missing its slice")
    name = _pick_any(
        check, ("name", "check", "check_name"), "check names")
    if name is None:
        raise ValueError("a check is missing its name")
    kwargs: Dict[str, Any] = {
        "slice_id": slice_id, "name": name,
    }
    required = _pick(
        check, "required", "is_required", "required words")
    if required is not None:
        kwargs["required"] = required
    check_id = _pick(check, "check_id", "id", "check ids")
    if check_id is not None:
        kwargs["check_id"] = check_id
    return AuditCheck(**kwargs)


def build_check(
        check: Any = None, **kwargs: Any) -> AuditCheck:
    """Build one validated check.

    From an AuditCheck, from a mapping (the
    spellings :func:`validate_check` reads), or
    from field words given as keyword arguments.
    """
    if isinstance(check, AuditCheck) and not kwargs:
        return check
    if isinstance(check, dict) or check is None:
        merged: Dict[str, Any] = {}
        if isinstance(check, dict):
            merged.update(check)
        merged.update(kwargs)
        return validate_check(merged)
    raise ValueError(
        f"a check must be a mapping, got {check!r}")


# ---------------------------------------------------------------------
# The result: what the Auditor's run of one check found, as evidence.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class AuditResult:
    """What the Auditor's run of one check found, as data.

    ``slice_id`` and ``check`` name the check the
    result belongs to; ``outcome`` is passed or
    failed, nothing between; ``evidence`` is the
    plain record of what the run showed - a result
    without evidence is no evidence, so it is
    required. Constructing one validates its shape
    only: whether the check is carried and required
    is the judge's concern, not the validator's.
    """

    result_id: Optional[str] = None
    slice_id: str = ""
    check: str = ""
    outcome: str = ""
    evidence: str = ""

    def __post_init__(self) -> None:
        if self.result_id is not None:
            object.__setattr__(
                self, "result_id",
                normalize_member_id(self.result_id))
        object.__setattr__(
            self, "slice_id",
            normalize_slice_id(self.slice_id))
        object.__setattr__(
            self, "check", normalize_check_name(self.check))
        object.__setattr__(
            self, "outcome", normalize_outcome(self.outcome))
        object.__setattr__(
            self, "evidence",
            _check_long_text(self.evidence, "a result's evidence"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "veto_result",
            "slice": VETO_SLICE,
            "result_id": self.result_id,
            "slice_id": self.slice_id,
            "check": self.check,
            "outcome": self.outcome,
            "evidence": self.evidence,
        }


def validate_result(result: Any) -> AuditResult:
    """Validate one result into an AuditResult.

    Accepts an AuditResult or a mapping naming a
    ``slice_id`` (or ``slice``), a ``check`` (or
    ``check_name`` / ``name``), an ``outcome`` (or
    ``result`` / ``status``), an ``evidence`` (or
    ``note``) and an optional ``result_id`` (or
    ``id``). Naming both spellings of one field
    with different values refuses, and unknown
    keys refuse.
    """
    if isinstance(result, AuditResult):
        return result
    if not isinstance(result, dict):
        raise ValueError(
            f"a result must be a mapping, got {result!r}")
    unknown = set(result) - _RESULT_KEYS
    if unknown:
        raise ValueError(
            "unknown result keys: %s"
            % ", ".join(sorted(unknown)))
    slice_id = _pick(result, "slice_id", "slice", "slices")
    if slice_id is None:
        raise ValueError("a result is missing its slice")
    check = _pick_any(
        result, ("check", "check_name", "name"), "checks")
    if check is None:
        raise ValueError("a result is missing its check")
    outcome = _pick_any(
        result, ("outcome", "result", "status"), "outcomes")
    if outcome is None:
        raise ValueError("a result is missing its outcome")
    evidence = _pick(result, "evidence", "note", "evidence words")
    if evidence is None:
        raise ValueError("a result is missing its evidence")
    kwargs: Dict[str, Any] = {
        "slice_id": slice_id, "check": check,
        "outcome": outcome, "evidence": evidence,
    }
    result_id = _pick(result, "result_id", "id", "result ids")
    if result_id is not None:
        kwargs["result_id"] = result_id
    return AuditResult(**kwargs)


def build_result(
        result: Any = None, **kwargs: Any) -> AuditResult:
    """Build one validated result.

    From an AuditResult, from a mapping (the
    spellings :func:`validate_result` reads), or
    from field words given as keyword arguments.
    """
    if isinstance(result, AuditResult) and not kwargs:
        return result
    if isinstance(result, dict) or result is None:
        merged: Dict[str, Any] = {}
        if isinstance(result, dict):
            merged.update(result)
        merged.update(kwargs)
        return validate_result(merged)
    raise ValueError(
        f"a result must be a mapping, got {result!r}")


# ---------------------------------------------------------------------
# The verdict and the gate state: the judgements, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class VetoVerdict:
    """One veto on one slice, as data.

    ``kind`` is one of the roadmap's two kinds;
    ``slice_id`` is the slice vetoed; ``check`` is
    the required check the veto turns on; ``title``
    names the judgement in plain words and
    ``detail`` states the whole evidence for it. A
    verdict is derived from evidence by the judge -
    it is a record for the coordinator, never an
    action.
    """

    kind: str = ""
    slice_id: str = ""
    check: str = ""
    title: str = ""
    detail: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "kind", normalize_verdict_kind(self.kind))
        object.__setattr__(
            self, "slice_id",
            normalize_slice_id(self.slice_id))
        object.__setattr__(
            self, "check", normalize_check_name(self.check))
        object.__setattr__(self, "title", _check_title(self.title))
        object.__setattr__(
            self, "detail",
            _check_long_text(self.detail, "a verdict's detail"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "veto_verdict",
            "slice": VETO_SLICE,
            "kind": self.kind,
            "slice_id": self.slice_id,
            "check": self.check,
            "title": self.title,
            "detail": self.detail,
        }


def validate_verdict(verdict: Any) -> VetoVerdict:
    """Validate one verdict into a VetoVerdict.

    Accepts a VetoVerdict or a mapping naming a
    ``kind`` (or ``verdict_kind``), a ``slice_id``
    (or ``slice``), a ``check`` (or ``check_name``),
    a ``title`` and a ``detail``. Unknown keys
    refuse.
    """
    if isinstance(verdict, VetoVerdict):
        return verdict
    if not isinstance(verdict, dict):
        raise ValueError(
            f"a verdict must be a mapping, got {verdict!r}")
    unknown = set(verdict) - _VERDICT_KEYS
    if unknown:
        raise ValueError(
            "unknown verdict keys: %s" % ", ".join(sorted(unknown)))
    kind = _pick(verdict, "kind", "verdict_kind", "kinds")
    if kind is None:
        raise ValueError("a verdict is missing its kind")
    slice_id = _pick(verdict, "slice_id", "slice", "slices")
    if slice_id is None:
        raise ValueError("a verdict is missing its slice")
    check = _pick(verdict, "check", "check_name", "checks")
    if check is None:
        raise ValueError("a verdict is missing its check")
    for field in ("title", "detail"):
        if field not in verdict:
            raise ValueError(f"a verdict is missing its {field}")
    return VetoVerdict(
        kind=kind, slice_id=slice_id, check=check,
        title=verdict["title"], detail=verdict["detail"])


def build_verdict(verdict: Any = None, **kwargs: Any) -> VetoVerdict:
    """Build one validated verdict.

    From a VetoVerdict, from a mapping (the
    spellings :func:`validate_verdict` reads), or
    from field words given as keyword arguments.
    """
    if isinstance(verdict, VetoVerdict) and not kwargs:
        return verdict
    if isinstance(verdict, dict) or verdict is None:
        merged: Dict[str, Any] = {}
        if isinstance(verdict, dict):
            merged.update(verdict)
        merged.update(kwargs)
        return validate_verdict(merged)
    raise ValueError(
        f"a verdict must be a mapping, got {verdict!r}")


@dataclass(frozen=True)
class GateState:
    """One case's gate, as the evidence leaves it.

    ``slice_id``, ``title`` and ``builder`` are the
    case's own words; ``required`` counts the
    required checks the slice carries, ``proven``
    those holding a passing result, ``failed``
    those the Auditor's run failed, and ``unproven``
    those holding no result at all; ``status`` is
    ``passed`` exactly when no required check
    failed and none is unproven, and ``vetoed``
    otherwise. A gate state is derived from
    evidence by the judge - it is never stored.
    """

    slice_id: str = ""
    title: str = ""
    builder: str = ""
    status: str = "passed"
    required: int = 0
    proven: int = 0
    failed: int = 0
    unproven: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "slice_id",
            normalize_slice_id(self.slice_id))
        object.__setattr__(
            self, "title", _check_title(self.title))
        object.__setattr__(
            self, "builder",
            normalize_member_id(self.builder))
        for field in ("required", "proven", "failed", "unproven"):
            value = getattr(self, field)
            if isinstance(value, bool) \
                    or not isinstance(value, int) or value < 0:
                raise ValueError(
                    f"a gate's {field} must be a whole number "
                    f"of zero or more, got {value!r}")
        if self.proven + self.failed + self.unproven \
                != self.required:
            raise ValueError(
                "a gate's proven, failed and unproven checks "
                "must together be its required checks")
        if self.status not in _GATE_STATUSES:
            raise ValueError(
                "a gate's status must be one of %s, "
                "got %r" % ("/".join(_GATE_STATUSES),
                            self.status))
        vetoed = self.failed + self.unproven > 0
        if (self.status == "vetoed") != vetoed:
            raise ValueError(
                "a gate is vetoed exactly when a required "
                "check failed or holds no result, and "
                "passed exactly when none did")

    @property
    def is_passed(self) -> bool:
        """True when every required check is proven passed."""
        return self.status == "passed"

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "veto_gate",
            "slice": VETO_SLICE,
            "slice_id": self.slice_id,
            "title": self.title,
            "builder": self.builder,
            "status": self.status,
            "required": self.required,
            "proven": self.proven,
            "failed": self.failed,
            "unproven": self.unproven,
        }


# ---------------------------------------------------------------------
# The judge: verdicts and gates derived from the evidence alone.
# ---------------------------------------------------------------------


def _judge(cases: Tuple[AuditCase, ...],
           checks: Tuple[AuditCheck, ...],
           results: Tuple[AuditResult, ...]) -> Tuple[
               Tuple[VetoVerdict, ...], Tuple[GateState, ...]]:
    checks_by_slice: Dict[str, list] = {}
    for check in checks:
        checks_by_slice.setdefault(check.slice_id, []).append(check)
    results_by_key: Dict[Tuple[str, str], AuditResult] = {}
    for result in results:
        results_by_key[(result.slice_id, result.check)] = result
    by_kind: Dict[str, list] = {kind: [] for kind in VERDICT_KINDS}
    gates = []
    for case in cases:
        proven = failed = unproven = 0
        required_checks = [
            c for c in checks_by_slice.get(case.slice_id, [])
            if c.required]
        for check in required_checks:
            result = results_by_key.get(
                (case.slice_id, check.name))
            if result is None:
                unproven += 1
                by_kind["unproven_check"].append(VetoVerdict(
                    kind="unproven_check",
                    slice_id=case.slice_id,
                    check=check.name,
                    title=(
                        f"Vetoed: {case.slice_id} has no "
                        f"Auditor's evidence for {check.name}"),
                    detail=(
                        f"{case.slice_id} ({case.title}), built "
                        f"by {case.builder}, carries the "
                        f"required {check.name} check, and the "
                        f"ledger holds no result for it, so the "
                        f"Auditor has not passed it - a check "
                        f"with no evidence has not passed. No "
                        f"slice is done until the Auditor's "
                        f"checks pass, so {case.slice_id} does "
                        f"not bank until the {check.name} check "
                        f"is run and its passing result is "
                        f"held as evidence.")))
            elif result.outcome == "failed":
                failed += 1
                by_kind["failed_check"].append(VetoVerdict(
                    kind="failed_check",
                    slice_id=case.slice_id,
                    check=check.name,
                    title=(
                        f"Vetoed: {case.slice_id} failed the "
                        f"Auditor's {check.name} check"),
                    detail=(
                        f"The Auditor's run of the required "
                        f"{check.name} check on {case.slice_id} "
                        f"({case.title}), built by "
                        f"{case.builder}, came back failed: "
                        f"{result.evidence} No slice is done "
                        f"until the Auditor's checks pass, so "
                        f"{case.slice_id} does not bank until "
                        f"the failure is repaired and the check "
                        f"passes on a fresh run.")))
            else:
                proven += 1
        gates.append(GateState(
            slice_id=case.slice_id,
            title=case.title,
            builder=case.builder,
            status="vetoed" if failed + unproven else "passed",
            required=len(required_checks),
            proven=proven,
            failed=failed,
            unproven=unproven))
    verdicts: list = []
    for kind in VERDICT_KINDS:
        verdicts.extend(by_kind[kind])
    return tuple(verdicts), tuple(gates)


def _evidence_from(source: Any) -> Tuple[
        Tuple[AuditCase, ...], Tuple[AuditCheck, ...],
        Tuple[AuditResult, ...]]:
    if isinstance(source, AuditorLedger):
        return source.cases, source.checks, source.results
    if isinstance(source, AuditorVetoRegistry):
        return (source.list_cases(), source.list_checks(),
                source.list_results())
    if isinstance(source, dict):
        unknown = set(source) - {
            "cases", "checks", "results"}
        if unknown:
            raise ValueError(
                "unknown evidence keys: %s"
                % ", ".join(sorted(unknown)))
        raw_cases = source.get("cases") or ()
        raw_checks = source.get("checks") or ()
        raw_results = source.get("results") or ()
        for what, raw in (("cases", raw_cases),
                          ("checks", raw_checks),
                          ("results", raw_results)):
            if isinstance(raw, (str, bytes)) \
                    or not isinstance(raw, (list, tuple)):
                raise ValueError(
                    f"evidence {what} must be a list")
        return (
            tuple(build_case(c) for c in raw_cases),
            tuple(build_check(c) for c in raw_checks),
            tuple(build_result(r) for r in raw_results))
    raise ValueError(f"audit evidence is needed, got {source!r}")


def judge_veto(source: Any) -> Tuple[VetoVerdict, ...]:
    """Every verdict in *source*'s evidence, in fixed order.

    Accepts an AuditorLedger, an AuditorVetoRegistry
    or a mapping with ``cases``, ``checks`` and
    ``results`` lists. The mechanical judge of the
    slice, as data only: failed-check verdicts first
    (in case order, then check order), then
    unproven-check verdicts - the same evidence
    always yields the same verdicts.
    """
    cases, checks, results = _evidence_from(source)
    verdicts, _gates = _judge(cases, checks, results)
    return verdicts


@dataclass(frozen=True)
class VetoReport:
    """One report of verdicts and gates, derived from evidence.

    ``verdicts`` are the vetoes the judge derived,
    in judgement order; ``gates`` are the gate
    state of every audited case, in case order;
    ``vetoed`` is True when any verdict stands;
    ``slices`` are the audited slice ids, in case
    order. Constructing one validates it: every
    verdict is a verdict, every gate a gate state,
    and the slices are exactly the gates' slices.
    """

    verdicts: Tuple[VetoVerdict, ...] = ()
    gates: Tuple[GateState, ...] = ()
    vetoed: bool = False
    slices: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field in ("verdicts", "gates", "slices"):
            value = getattr(self, field)
            if isinstance(value, (str, bytes)) \
                    or not isinstance(value, (list, tuple)):
                raise ValueError(
                    f"a report's {field} must be a list, "
                    f"got {value!r}")
        object.__setattr__(self, "verdicts", tuple(
            v if isinstance(v, VetoVerdict)
            else validate_verdict(v) for v in self.verdicts))
        gates = []
        for gate in self.gates:
            if not isinstance(gate, GateState):
                raise ValueError(
                    f"a report's gates must be gate states, "
                    f"got {gate!r}")
            gates.append(gate)
        object.__setattr__(self, "gates", tuple(gates))
        object.__setattr__(self, "slices", tuple(
            normalize_slice_id(s) for s in self.slices))
        if tuple(g.slice_id for g in gates) != tuple(self.slices):
            raise ValueError(
                "a report's slices must be its gates' "
                "slices, in gate order")
        if bool(self.vetoed) != bool(self.verdicts):
            raise ValueError(
                "a report is vetoed exactly when it holds "
                "a verdict")

    @property
    def is_clean(self) -> bool:
        """True when the evidence holds no verdict."""
        return not self.verdicts

    def by_kind(self, kind: Any) -> Tuple[VetoVerdict, ...]:
        """Every verdict of one kind, in report order."""
        wanted = normalize_verdict_kind(kind)
        return tuple(v for v in self.verdicts if v.kind == wanted)

    def for_slice(self, slice_id: Any) -> Tuple[VetoVerdict, ...]:
        """Every verdict on one slice, in report order."""
        wanted = normalize_slice_id(slice_id)
        return tuple(
            v for v in self.verdicts if v.slice_id == wanted)

    def gate_for(self, slice_id: Any) -> GateState:
        """The one gate one slice holds; unknown raises."""
        wanted = normalize_slice_id(slice_id)
        for gate in self.gates:
            if gate.slice_id == wanted:
                return gate
        raise KeyError(f"no gate for the slice: {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "veto_report",
            "slice": VETO_SLICE,
            "count": len(self.verdicts),
            "clean": self.is_clean,
            "vetoed": bool(self.vetoed),
            "slices": list(self.slices),
            "failed_check": len(self.by_kind("failed_check")),
            "unproven_check": len(
                self.by_kind("unproven_check")),
            "verdicts": [v.to_record() for v in self.verdicts],
            "gates": [g.to_record() for g in self.gates],
        }


def validate_report(source: Any, report: Any) -> list:
    """Every problem in a claimed report of *source*, as strings.

    An empty list means the report answers the
    source exactly: every verdict and every gate
    the evidence yields, in judgement order, and
    nothing else - a report missing a veto, or
    holding one the evidence does not hold, is
    named.
    """
    if not isinstance(report, VetoReport):
        return [f"a veto report is needed, got {report!r}"]
    try:
        cases, checks, results = _evidence_from(source)
    except ValueError as exc:
        return [str(exc)]
    wanted_verdicts, wanted_gates = _judge(cases, checks, results)
    problems = []
    if tuple(report.verdicts) != wanted_verdicts \
            or tuple(report.gates) != wanted_gates:
        problems.append(
            "the report does not hold exactly the evidence's "
            "verdicts and gates, in judgement order: the "
            "report must catch every verdict the evidence "
            "holds, and no other verdict")
    return problems


def _report_from(cases, checks, results) -> VetoReport:
    verdicts, gates = _judge(cases, checks, results)
    return VetoReport(
        verdicts=verdicts, gates=gates,
        vetoed=bool(verdicts),
        slices=tuple(case.slice_id for case in cases))


# ---------------------------------------------------------------------
# The veto ledger: the evidence one file holds, under the Auditor.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class AuditorLedger:
    """A whole veto ledger: the evidence one file holds.

    ``keeper`` is the member id of the one who
    keeps the ledger - in the shipped example the
    auditor, the M-121 casting's Auditor, whose
    office is verify. Constructing one holds the
    ledger law: at least one case, no slice audited
    twice, no check carried twice by one slice, no
    two results for one check, and every case
    carrying at least one check - a slice carrying
    no checks is not auditable, it is unexamined.
    Checks and results naming a slice with no case
    are held but judge nothing, exactly as a stray
    reading judges nothing in the sibling layers.
    """

    cases: Tuple[AuditCase, ...] = ()
    checks: Tuple[AuditCheck, ...] = ()
    results: Tuple[AuditResult, ...] = ()
    keeper: str = ""
    ledger_note: str = ""

    def __post_init__(self) -> None:
        for field in ("cases", "checks", "results"):
            value = getattr(self, field)
            if isinstance(value, (str, bytes)) \
                    or not isinstance(value, (list, tuple)):
                raise ValueError(
                    f"a veto ledger's {field} must be a list, "
                    f"got {value!r}")
        cases = tuple(
            c if isinstance(c, AuditCase)
            else validate_case(c) for c in self.cases)
        checks = tuple(
            c if isinstance(c, AuditCheck)
            else validate_check(c) for c in self.checks)
        results = tuple(
            r if isinstance(r, AuditResult)
            else validate_result(r) for r in self.results)
        if not cases:
            raise ValueError(
                "a veto ledger must hold at least one case")
        seen_cases = set()
        for case in cases:
            if case.slice_id in seen_cases:
                raise ValueError(
                    f"a slice is audited twice: "
                    f"{case.slice_id} holds two cases")
            seen_cases.add(case.slice_id)
        seen_checks = set()
        for check in checks:
            key = (check.slice_id, check.name)
            if key in seen_checks:
                raise ValueError(
                    f"a check is carried twice: "
                    f"{check.slice_id} carries {check.name} "
                    f"twice")
            seen_checks.add(key)
        seen_results = set()
        for result in results:
            key = (result.slice_id, result.check)
            if key in seen_results:
                raise ValueError(
                    f"a check holds two results: "
                    f"{result.slice_id}'s {result.check}")
            seen_results.add(key)
        carried = {check.slice_id for check in checks}
        for case in cases:
            if case.slice_id not in carried:
                raise ValueError(
                    f"a case carries no checks: "
                    f"{case.slice_id} stands before the "
                    f"Auditor with nothing to run")
        object.__setattr__(self, "cases", cases)
        object.__setattr__(self, "checks", checks)
        object.__setattr__(self, "results", results)
        object.__setattr__(
            self, "keeper", normalize_member_id(self.keeper))
        object.__setattr__(
            self, "ledger_note", str(self.ledger_note or ""))

    def report(self) -> VetoReport:
        """The report this ledger's evidence yields."""
        return _report_from(self.cases, self.checks, self.results)

    def case_for(self, slice_id: Any) -> AuditCase:
        """The one case one slice holds; unknown raises."""
        wanted = normalize_slice_id(slice_id)
        for case in self.cases:
            if case.slice_id == wanted:
                return case
        raise KeyError(f"no case for the slice: {wanted!r}")

    def checks_for(self, slice_id: Any) -> Tuple[AuditCheck, ...]:
        """Every check one slice carries, in ledger order."""
        wanted = normalize_slice_id(slice_id)
        return tuple(
            c for c in self.checks if c.slice_id == wanted)

    def results_for(self, slice_id: Any) -> Tuple[AuditResult, ...]:
        """Every result held for one slice, in ledger order."""
        wanted = normalize_slice_id(slice_id)
        return tuple(
            r for r in self.results if r.slice_id == wanted)


def _example_problems(parsed_cases, parsed_checks,
                      parsed_results, keeper) -> list:
    problems = []
    held_cases = tuple(
        (c.slice_id, c.title, c.builder) for c in parsed_cases)
    if held_cases != _EXAMPLE_CASES:
        problems.append(
            "the shipped example ledger must hold exactly "
            "the three cases in file order, with their "
            "slices, titles and builders")
    held_checks = tuple(
        (c.slice_id, c.name, c.required) for c in parsed_checks)
    if held_checks != _EXAMPLE_CHECKS:
        problems.append(
            "the shipped example ledger must hold exactly "
            "the six checks in file order, with their "
            "slices, names and required words")
    held_results = tuple(
        (r.slice_id, r.check, r.outcome) for r in parsed_results)
    if held_results != _EXAMPLE_RESULTS:
        problems.append(
            "the shipped example ledger must hold exactly "
            "the five results in file order, with their "
            "slices, checks and outcomes")
    if keeper is not None and keeper != "auditor":
        problems.append(
            "the shipped example ledger is kept by the "
            "auditor")
    if held_cases == _EXAMPLE_CASES \
            and held_checks == _EXAMPLE_CHECKS \
            and held_results == _EXAMPLE_RESULTS:
        report = _report_from(
            tuple(parsed_cases), tuple(parsed_checks),
            tuple(parsed_results))
        kinds = [(v.kind, v.slice_id, v.check)
                 for v in report.verdicts]
        if kinds != [("failed_check", "M-129", "suite-green"),
                     ("unproven_check", "M-127", "suite-green")]:
            problems.append(
                "the shipped example ledger must yield "
                "exactly two verdicts, one of each kind, "
                "in judgement order")
        passed = report.gate_for("M-128")
        if passed.status != "passed" \
                or passed.required != 2 or passed.proven != 2:
            problems.append(
                "the shipped example ledger must leave "
                "M-128 passed, with both its required "
                "checks proven")
        vetoed127 = report.gate_for("M-127")
        if vetoed127.status != "vetoed" \
                or vetoed127.unproven != 1 \
                or vetoed127.proven != 1:
            problems.append(
                "the shipped example ledger must leave "
                "M-127 vetoed on its one unproven check")
        vetoed129 = report.gate_for("M-129")
        if vetoed129.status != "vetoed" \
                or vetoed129.failed != 1 \
                or vetoed129.proven != 1:
            problems.append(
                "the shipped example ledger must leave "
                "M-129 vetoed on its one failed check")
    return problems


def validate_ledger(data: Any, *,
                    require_example: bool = False) -> list:
    """Every problem in a veto ledger mapping, as plain strings.

    An empty list means the veto ledger is
    well-formed. With ``require_example`` the file
    must be exactly the shipped example: the three
    cases, six checks and five results in file
    order, kept by the auditor - and the report
    derived from it must hold exactly its two
    verdicts, one of each kind, with M-128 passed
    and M-127 and M-129 each vetoed on one check
    (the check the shipped file is held to; a real
    ledger's file is read without it).
    """
    if not isinstance(data, dict):
        return [f"a veto ledger must be a mapping, got {data!r}"]
    problems = []
    unknown = set(data) - _LEDGER_KEYS
    if unknown:
        problems.append(
            "unknown veto ledger keys: %s"
            % ", ".join(sorted(unknown)))
    if data.get("schema") != VETO_SCHEMA:
        problems.append(
            f"a veto ledger's schema must be "
            f"{VETO_SCHEMA!r}, got {data.get('schema')!r}")
    if data.get("slice") != VETO_SLICE:
        problems.append(
            f"a veto ledger's slice must be "
            f"{VETO_SLICE!r}, got {data.get('slice')!r}")
    keeper = None
    if data.get("keeper") is None:
        problems.append("a veto ledger is missing its keeper")
    else:
        try:
            keeper = normalize_member_id(data["keeper"])
        except ValueError as exc:
            problems.append(f"keeper: {exc}")
    raw_cases = data.get("cases")
    raw_checks = data.get("checks")
    raw_results = data.get("results")
    if not isinstance(raw_cases, list):
        problems.append("a veto ledger must hold a cases list")
        raw_cases = []
    if raw_checks is None:
        raw_checks = []
    if not isinstance(raw_checks, list):
        problems.append("a veto ledger must hold a checks list")
        raw_checks = []
    if raw_results is None:
        raw_results = []
    if not isinstance(raw_results, list):
        problems.append("a veto ledger must hold a results list")
        raw_results = []
    if isinstance(raw_cases, list) and not raw_cases:
        problems.append(
            "a veto ledger must hold at least one case")
    parsed_cases = []
    for index, entry in enumerate(raw_cases):
        try:
            parsed_cases.append(validate_case(entry))
        except ValueError as exc:
            problems.append(f"case {index + 1}: {exc}")
    parsed_checks = []
    for index, entry in enumerate(raw_checks):
        try:
            parsed_checks.append(validate_check(entry))
        except ValueError as exc:
            problems.append(f"check {index + 1}: {exc}")
    parsed_results = []
    for index, entry in enumerate(raw_results):
        try:
            parsed_results.append(validate_result(entry))
        except ValueError as exc:
            problems.append(f"result {index + 1}: {exc}")
    if len(parsed_cases) == len(raw_cases):
        seen = set()
        for case in parsed_cases:
            if case.slice_id in seen:
                problems.append(
                    f"a slice is audited twice: "
                    f"{case.slice_id} holds two cases")
            seen.add(case.slice_id)
    if len(parsed_checks) == len(raw_checks):
        seen = set()
        for check in parsed_checks:
            key = (check.slice_id, check.name)
            if key in seen:
                problems.append(
                    f"a check is carried twice: "
                    f"{check.slice_id} carries {check.name} "
                    f"twice")
            seen.add(key)
    if len(parsed_results) == len(raw_results):
        seen = set()
        for result in parsed_results:
            key = (result.slice_id, result.check)
            if key in seen:
                problems.append(
                    f"a check holds two results: "
                    f"{result.slice_id}'s {result.check}")
            seen.add(key)
    if len(parsed_cases) == len(raw_cases) \
            and len(parsed_checks) == len(raw_checks):
        carried = {check.slice_id for check in parsed_checks}
        for case in parsed_cases:
            if case.slice_id not in carried:
                problems.append(
                    f"a case carries no checks: "
                    f"{case.slice_id} stands before the "
                    f"Auditor with nothing to run")
    if require_example \
            and len(parsed_cases) == len(raw_cases) \
            and len(parsed_checks) == len(raw_checks) \
            and len(parsed_results) == len(raw_results):
        problems.extend(_example_problems(
            parsed_cases, parsed_checks,
            parsed_results, keeper))
    return problems


def _ledger_from(data: Any, *, require_example: bool) -> AuditorLedger:
    problems = validate_ledger(data, require_example=require_example)
    if problems:
        raise ValidationError(
            "invalid veto ledger: " + "; ".join(problems))
    assert isinstance(data, dict)
    return AuditorLedger(
        cases=tuple(
            validate_case(entry) for entry in data["cases"]),
        checks=tuple(
            validate_check(entry)
            for entry in data.get("checks") or []),
        results=tuple(
            validate_result(entry)
            for entry in data.get("results") or []),
        keeper=data["keeper"],
        ledger_note=str(data.get("ledger_note") or ""))


def load_auditor_ledger(
        data: Optional[Dict[str, Any]] = None) -> AuditorLedger:
    """Load and validate the shipped example ledger (or *data*).

    The shipped file is held to the example check:
    exactly the three cases, six checks and five
    results, kept by the auditor, yielding exactly
    its two verdicts, one of each kind. Raises
    :class:`ValidationError` listing every problem
    when the record is not a well-formed veto
    ledger.
    """
    raw = data if data is not None else load_resource(
        VETO_RESOURCE)
    return _ledger_from(raw, require_example=True)


def load_auditor_ledger_file(path: Any) -> AuditorLedger:
    """Load and validate a veto ledger from a file at *path*.

    This is the road a real veto ledger arrives by:
    any file in the ledger shape, anywhere on disk,
    validated whole - a malformed file raises
    :class:`ValidationError` naming the problem,
    and a missing file raises ``FileNotFoundError``.
    The example check is not held: a ledger may
    hold a single case and no results yet.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _ledger_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: evidence held in registration order, ids
# deterministic. A registry refuses a supplied id already held, a
# slice audited twice, a check carried twice by one slice and two
# results for one check: repetition here is a second gate for one
# slice, not two pieces of evidence, so it is refused, never hidden.
# ---------------------------------------------------------------------


class AuditorVetoRegistry:
    """An in-memory registry of Auditor's-veto evidence.

    Cases, checks and results are held in
    registration order. Ids are deterministic: a
    caller-supplied id is used as given, and an
    unsupplied id is the next ``case-N`` /
    ``check-N`` / ``result-N`` in sequence, skipping
    any number a supplied id already took. A
    supplied id already held refuses. A ledger
    registered whole refuses a duplicated slice,
    check or result exactly as the ledger does.
    Storage beyond memory (a session's journal, a
    file) is the agent layer's concern; this model
    is neutral.
    """

    def __init__(self) -> None:
        self._cases: Dict[str, AuditCase] = {}
        self._checks: Dict[str, AuditCheck] = {}
        self._results: Dict[str, AuditResult] = {}
        self._next_case = 1
        self._next_check = 1
        self._next_result = 1

    def _fresh_case_id(self) -> str:
        while f"case-{self._next_case}" in self._cases:
            self._next_case += 1
        case_id = f"case-{self._next_case}"
        self._next_case += 1
        return case_id

    def _fresh_check_id(self) -> str:
        while f"check-{self._next_check}" in self._checks:
            self._next_check += 1
        check_id = f"check-{self._next_check}"
        self._next_check += 1
        return check_id

    def _fresh_result_id(self) -> str:
        while f"result-{self._next_result}" in self._results:
            self._next_result += 1
        result_id = f"result-{self._next_result}"
        self._next_result += 1
        return result_id

    def register_case(self, case: Any) -> AuditCase:
        """Register one case and hold it."""
        validated = build_case(case)
        for held in self._cases.values():
            if held.slice_id == validated.slice_id:
                raise ValueError(
                    f"a slice is audited twice: "
                    f"{validated.slice_id} holds two cases")
        if validated.case_id is not None \
                and validated.case_id in self._cases:
            raise ValueError(
                f"a case named "
                f"{validated.case_id!r} already exists")
        if validated.case_id is None:
            validated = replace(
                validated, case_id=self._fresh_case_id())
        self._cases[validated.case_id] = validated
        return validated

    def register_check(self, check: Any) -> AuditCheck:
        """Register one check and hold it."""
        validated = build_check(check)
        for held in self._checks.values():
            if held.slice_id == validated.slice_id \
                    and held.name == validated.name:
                raise ValueError(
                    f"a check is carried twice: "
                    f"{validated.slice_id} carries "
                    f"{validated.name} twice")
        if validated.check_id is not None \
                and validated.check_id in self._checks:
            raise ValueError(
                f"a check named "
                f"{validated.check_id!r} already exists")
        if validated.check_id is None:
            validated = replace(
                validated, check_id=self._fresh_check_id())
        self._checks[validated.check_id] = validated
        return validated

    def register_result(self, result: Any) -> AuditResult:
        """Register one result and hold it."""
        validated = build_result(result)
        for held in self._results.values():
            if held.slice_id == validated.slice_id \
                    and held.check == validated.check:
                raise ValueError(
                    f"a check holds two results: "
                    f"{validated.slice_id}'s "
                    f"{validated.check}")
        if validated.result_id is not None \
                and validated.result_id in self._results:
            raise ValueError(
                f"a result named {validated.result_id!r} "
                f"already exists")
        if validated.result_id is None:
            validated = replace(
                validated, result_id=self._fresh_result_id())
        self._results[validated.result_id] = validated
        return validated

    def register_ledger(self, ledger: Any) -> Tuple[
            Tuple[AuditCase, ...], Tuple[AuditCheck, ...],
            Tuple[AuditResult, ...]]:
        """Register every piece of one ledger's evidence, in order."""
        if not isinstance(ledger, AuditorLedger):
            raise ValueError(f"a veto ledger is needed, got {ledger!r}")
        cases = tuple(
            self.register_case(c) for c in ledger.cases)
        checks = tuple(
            self.register_check(c) for c in ledger.checks)
        results = tuple(
            self.register_result(r) for r in ledger.results)
        return cases, checks, results

    def get_case(self, case_id: Any) -> AuditCase:
        """The case one id names; an unknown id raises."""
        wanted = normalize_member_id(case_id)
        if wanted not in self._cases:
            raise KeyError(f"unknown case: {wanted!r}")
        return self._cases[wanted]

    def get_check(self, check_id: Any) -> AuditCheck:
        """The check one id names; an unknown id raises."""
        wanted = normalize_member_id(check_id)
        if wanted not in self._checks:
            raise KeyError(f"unknown check: {wanted!r}")
        return self._checks[wanted]

    def get_result(self, result_id: Any) -> AuditResult:
        """The result one id names; an unknown id raises."""
        wanted = normalize_member_id(result_id)
        if wanted not in self._results:
            raise KeyError(f"unknown result: {wanted!r}")
        return self._results[wanted]

    def list_cases(self) -> Tuple[AuditCase, ...]:
        """Every held case, in registration order."""
        return tuple(self._cases.values())

    def list_checks(self) -> Tuple[AuditCheck, ...]:
        """Every held check, in registration order."""
        return tuple(self._checks.values())

    def list_results(self) -> Tuple[AuditResult, ...]:
        """Every held result, in registration order."""
        return tuple(self._results.values())

    def verdicts(self) -> Tuple[VetoVerdict, ...]:
        """Every verdict in the held evidence, in judgement order."""
        return judge_veto(self)

    def report(self) -> VetoReport:
        """The report the held evidence yields."""
        return _report_from(
            self.list_cases(), self.list_checks(),
            self.list_results())

    def for_slice(self, slice_id: Any) -> Tuple[VetoVerdict, ...]:
        """Every held verdict on one slice, in order."""
        return self.report().for_slice(slice_id)


# ---------------------------------------------------------------------
# Veto news, shaped as session records.
# ---------------------------------------------------------------------


def case_record(case: Any) -> Dict[str, Any]:
    """The session-news record of one case."""
    current = case if isinstance(
        case, AuditCase) else build_case(case)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.slice_id} ({current.title}) stands "
        f"before the Auditor, built by {current.builder}.")
    return record


def check_record(check: Any) -> Dict[str, Any]:
    """The session-news record of one check."""
    current = check if isinstance(
        check, AuditCheck) else build_check(check)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.slice_id} carries the Auditor's "
        f"{current.name} check"
        f"{'' if current.required else ' (not required)'}.")
    return record


def result_record(result: Any) -> Dict[str, Any]:
    """The session-news record of one result."""
    current = result if isinstance(
        result, AuditResult) else build_result(result)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"The Auditor's {current.check} on "
        f"{current.slice_id}: {current.outcome}.")
    return record


def plain_words(verdict: Any) -> str:
    """One verdict, in one plain sentence."""
    current = verdict if isinstance(verdict, VetoVerdict) \
        else build_verdict(verdict)
    return f"{current.title} - {current.detail}"


def verdict_record(verdict: Any) -> Dict[str, Any]:
    """The session-news record of one verdict.

    Carries the verdict's whole record plus a
    one-line plain headline, so a judgement made in
    a session is news with its shape attached, never
    a bare log line.
    """
    current = verdict if isinstance(verdict, VetoVerdict) \
        else build_verdict(verdict)
    record = current.to_record()
    record["news"] = True
    record["headline"] = plain_words(current)
    return record


def report_plain_words(report: Any) -> str:
    """One veto report, in one plain sentence."""
    current = report if isinstance(report, VetoReport) \
        else VetoReport(verdicts=report)
    if current.is_clean:
        return (
            "No veto stands: every audited slice's "
            "required checks are proven, so every "
            "gate is green.")
    caught = "; ".join(v.title for v in current.verdicts)
    return (
        f"{len(current.verdicts)} vetoes stand for the "
        f"coordinator: {caught}.")


def report_record(report: Any) -> Dict[str, Any]:
    """The session-news record of one veto report.

    ONE record holding every verdict and every gate
    with its full evidence - the report itself, as
    news for the coordinator.
    """
    current = report if isinstance(report, VetoReport) \
        else VetoReport(verdicts=report)
    record = current.to_record()
    record["news"] = True
    record["headline"] = report_plain_words(current)
    return record


# ---------------------------------------------------------------------
# The /veto surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def format_verdict(verdict: Any) -> str:
    """One verdict, in plain words."""
    current = verdict if isinstance(verdict, VetoVerdict) \
        else build_verdict(verdict)
    return f"  {current.kind}: {plain_words(current)}"


def _selected_verdicts(source: Any) -> Tuple[VetoVerdict, ...]:
    if source is None:
        return load_auditor_ledger().report().verdicts
    if isinstance(source, VetoReport):
        return source.verdicts
    if isinstance(source, (AuditorLedger,
                           AuditorVetoRegistry, dict)):
        return judge_veto(source)
    if isinstance(source, (str, bytes)) \
            or not isinstance(source, (list, tuple)):
        raise ValueError("verdicts must be a list of verdicts")
    return tuple(
        v if isinstance(v, VetoVerdict) else build_verdict(v)
        for v in source)


def format_verdicts(source: Any = None) -> str:
    """The verdicts, in plain words, in judgement order.

    Accepts a list of verdicts, a VetoReport, an
    AuditorLedger or an AuditorVetoRegistry. With
    no source the shipped example ledger's verdicts
    are shown. With no verdicts at all the text
    states no veto stands, plainly.
    """
    selected = _selected_verdicts(source)
    if not selected:
        return ("The Auditor's veto: clean. No slice "
                "stands vetoed - every required check "
                "is proven.")
    lines = [
        f"The Auditor's veto: {len(selected)} vetoes "
        f"stand for the coordinator."]
    for verdict in selected:
        lines.append(format_verdict(verdict))
    return "\n".join(lines)


def _selected_gates(source: Any) -> Tuple[GateState, ...]:
    if source is None:
        return load_auditor_ledger().report().gates
    if isinstance(source, VetoReport):
        return source.gates
    if isinstance(source, AuditorLedger):
        return source.report().gates
    if isinstance(source, AuditorVetoRegistry):
        return source.report().gates
    raise ValueError(f"slice gates are needed, got {source!r}")


def format_gates(source: Any = None) -> str:
    """Every case's gate, in plain words, in case order.

    Accepts a VetoReport, an AuditorLedger or an
    AuditorVetoRegistry. With no source the shipped
    example ledger's gates are shown.
    """
    selected = _selected_gates(source)
    if not selected:
        return "Slice gates: no case is held yet."
    rendered = ["Slice gates:"]
    for gate in selected:
        if gate.is_passed:
            rendered.append(
                f"  {gate.slice_id} ({gate.title}): passed - "
                f"{gate.proven} of {gate.required} required "
                f"checks proven.")
        else:
            rendered.append(
                f"  {gate.slice_id} ({gate.title}): VETOED - "
                f"{gate.failed} failed, {gate.unproven} "
                f"unproven of {gate.required} required "
                f"checks.")
    return "\n".join(rendered)


def format_kinds() -> str:
    """The verdict kinds, in plain words."""
    return (
        "Verdict kinds: failed_check (a required "
        "check the slice carries was run and the "
        "Auditor's result says it failed), "
        "unproven_check (a required check the slice "
        "carries holds no result at all - a check "
        "with no evidence has not passed). A check "
        "that is not required never vetoes, and "
        "passing is a gate state, not a verdict: a "
        "slice passes exactly when every required "
        "check it carries holds a passing result.")


def format_veto_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /veto.

    With nothing named, the shipped example
    ledger's verdicts and gates are shown - the
    example this slice ships - so the screen is
    never empty. There is no Part VIII board yet;
    this screen is where the verdicts are visible.
    """
    lines = ["The Auditor's veto (M-130) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_verdicts(source))
    lines.append("")
    lines.append(format_gates(source))
    lines.append("")
    lines.append(format_kinds())
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_veto_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /veto grammar both surfaces share.

    No words (or ``show`` / ``list`` / ``verdicts``)
    shows the verdicts; ``show <slice>`` and a bare
    slice id show one slice's verdicts; ``gates``
    shows every case's gate; ``kinds`` asks for the
    kinds. Anything else is a usage error naming
    the grammar. Returns ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None \
        else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list", "verdicts"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head == "show" and len(words) == 2:
        try:
            return ("show", normalize_slice_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "gates" and len(words) == 1:
        return ("gates", None)
    if head == "kinds" and len(words) == 1:
        return ("kinds", None)
    if head in ("show", "kinds", "gates", "list", "verdicts"):
        raise ValueError(USAGE)
    if len(words) == 1:
        try:
            return ("show", normalize_slice_id(words[0]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
