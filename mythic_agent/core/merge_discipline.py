"""Merge discipline (All-Features roadmap slice M-128).

Part VI - Agents as files - continues here. The
roadmap's words: ``member branches merge in slice
order with tests at each merge; a red merge stops
the line, not the whole crew.``

What already shipped, and what this slice adds:

* The crew itself is already data
  (``core/crew_members.py``, M-121: every member
  holds one office), the offices are formalised
  (``core/offices.py``, M-122, and
  ``core/custom_offices.py``, M-123), the worktree
  discipline is already data (``core/worktrees.py``,
  M-124: each member on its own branch, merges in
  slice order), the dealing of a plan's slices to
  the crew is already data (``core/task_dealing.py``,
  M-125: this slice's work fits the forge_worker),
  the traffic between members is already data
  (``core/crew_comms.py``, M-126), and the
  coordinator's watch over the crew is already data
  (``core/deadlock_watch.py``, M-127). What nothing
  held is the merging itself: which member merges
  which slice from which branch, in which order,
  with what test gate recorded at each merge, and
  what a red merge stops. Today branches land in
  whatever order they finish in, a merge with no
  test run behind it looks the same as a tested
  one, and one failed merge stalls the whole crew
  because nobody can say which line it belongs to.
* This slice is that discipline, as a pure layer:
  the evidence validated as data (a step - a member,
  the slice it merges, the branch it merges from -
  and a recorded merge - a member, a slice, a
  branch, the test gate recorded at the merge and
  the merge's outcome), the shipped data file
  (``mythic_agent/data/merge_discipline.yaml``)
  holding one example plan and ledger in exactly
  the shape a real plan and ledger's file takes,
  a loader for a plan file anywhere on disk, the
  verdicts and the state of every line derived
  mechanically from the evidence alone, a verdict
  record and a report record shaped as session
  news, and a small in-memory registry model. This
  module executes no git, performs no merge,
  spawns or stops no crew member and imports no
  agent / UI code; the agent layer owns holding
  the plan and ledger for a session and handing
  the verdicts to the coordinator.

Honesty rules, enforced here and pinned by tests:

* **Verdicts are derived, never stored.** A report
  is computed from the steps and merges it is
  judged under, in a fixed order, so it can never
  disagree with them; the same evidence always
  yields the same verdicts and the same lines
  (deterministic order, deterministic wording).
* **Merges land in slice order, per line.** A line
  is one member's own merging: its planned slices,
  in slice order. A recorded merge is judged
  against its own line alone - a merge attempted
  before its line's earlier slices have merged is
  out of order and advances nothing, however green
  it is, and one line's disorder never touches
  another line's standing.
* **A test gate is recorded at each merge.** A
  merge whose recorded gate is failed or missing
  is flagged and advances nothing: only a merge
  with a passed gate behind it can advance a line
  or stop it.
* **A red merge stops the line, not the crew.** A
  red (failed or conflicted) merge that was the
  line's next merge, with a passed gate, marks
  only that member's line stopped, at that slice;
  every other line keeps its own standing and its
  later green merges still advance. A green merge
  that is in order and gated advances its line by
  exactly that slice.
* **The verdicts are the roadmap's three.** A
  verdict is ``out_of_order`` (a merge attempted
  out of its line's slice order, or for a slice
  its line never planned), ``missing_test_gate``
  (a merge recorded with a failed or missing test
  gate) or ``line_stopped`` (a red merge, and any
  later merge attempted on the stopped line) - no
  other kind is read, and an unknown kind refuses.
  The checks run in that precedence along a line:
  a stopped line answers first, then order, then
  the gate, then the outcome.
* **Members, slices and branches are the shipped
  layers'.** A member id reads exactly as the
  M-121 layer reads one, a slice id and a branch
  exactly as the M-124 layer reads them - composed
  with by import, never re-read here.
* **Discipline is data only; the coordinator
  acts.** No git is executed and no real merge is
  performed by this slice, and no live crew is
  spawned or stopped: a verdict here is a
  validated record derived from given evidence,
  not an action taken, and the coordinator acts
  on the verdicts through later roads. The
  roadmap names the board (Part VIII) as where
  crew state will be visible; that board does not
  exist yet, so the verdicts are visible through
  this slice's own /merge screen, and nothing
  here claims a board exists.
* **Malformed refuses.** An unknown kind, gate or
  outcome, a malformed member, slice or branch,
  a duplicated step on one line, and unknown keys
  in a step, a merge, a verdict or a plan mapping
  all raise instead of being skipped or guessed
  at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .validation import ValidationError
from .worktrees import normalize_branch, normalize_slice_id

__all__ = [
    "DISCIPLINE_RESOURCE",
    "DISCIPLINE_SCHEMA",
    "DISCIPLINE_SLICE",
    "PLAIN_EXPLANATION",
    "USAGE",
    "VERDICT_KINDS",
    "LineState",
    "MergeAttempt",
    "MergeDiscipline",
    "MergeDisciplineRegistry",
    "MergeReport",
    "MergeStep",
    "MergeVerdict",
    "attempt_record",
    "build_attempt",
    "build_step",
    "build_verdict",
    "format_kinds",
    "format_lines",
    "format_merge_screen",
    "format_verdict",
    "format_verdicts",
    "judge_merges",
    "load_merge_discipline",
    "load_merge_discipline_file",
    "normalize_gate",
    "normalize_outcome",
    "normalize_slice_id",
    "normalize_verdict_kind",
    "parse_merge_args",
    "plain_words",
    "report_plain_words",
    "report_record",
    "step_record",
    "validate_attempt",
    "validate_plan",
    "validate_report",
    "validate_step",
    "validate_verdict",
    "verdict_record",
]

DISCIPLINE_SLICE = "M-128"

#: The packaged data resource holding the example plan and ledger.
DISCIPLINE_RESOURCE = "merge_discipline.yaml"

#: The schema word a plan file must carry.
DISCIPLINE_SCHEMA = "mythic.merge_discipline/1"

#: The verdict kinds, in roadmap order: the order,
#: the gate, the stopped line.
VERDICT_KINDS = (
    "out_of_order", "missing_test_gate", "line_stopped")

_KIND_READINGS = {
    "order": "out_of_order",
    "out_of_order": "out_of_order",
    "gate": "missing_test_gate",
    "missing_gate": "missing_test_gate",
    "missing_test_gate": "missing_test_gate",
    "untested": "missing_test_gate",
    "stopped": "line_stopped",
    "line_stopped": "line_stopped",
    "red": "line_stopped",
    "red_merge": "line_stopped",
}

_GATE_READINGS = {
    "passed": "passed",
    "pass": "passed",
    "failed": "failed",
    "fail": "failed",
    "missing": "missing",
    "none": "missing",
    "absent": "missing",
}

_OUTCOME_READINGS = {
    "green": "green",
    "red": "red",
    "failed": "red",
    "conflicted": "red",
    "conflict": "red",
}

PLAIN_EXPLANATION = (
    "Merge discipline: member branches merge in "
    "slice order along each member's own line, with "
    "a test gate recorded at each merge; a red merge "
    "stops only its own line, not the whole crew. "
    "Every verdict is derived from the given steps "
    "and recorded merges alone. There is no Part "
    "VIII board yet, so the verdicts are visible on "
    "this slice's own screen, not on a board. This "
    "layer holds the merging as data only; it "
    "executes no git, performs no real merge and "
    "spawns or stops no crew itself - the "
    "coordinator acts on the verdicts through later "
    "roads."
)

USAGE = (
    "Usage: /merge, /merge show, "
    "/merge show <member>, /merge lines, /merge kinds"
)

_STEP_KEYS = frozenset({
    "id", "step_id", "member", "member_id",
    "slice", "slice_id", "branch",
})

_ATTEMPT_KEYS = frozenset({
    "id", "attempt_id", "member", "member_id",
    "slice", "slice_id", "branch", "gate",
    "test_gate", "outcome", "result",
})

_VERDICT_KEYS = frozenset({
    "kind", "verdict_kind", "member", "member_id",
    "slice", "slice_id", "branch", "title", "detail",
})

_PLAN_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "plan_note", "keeper", "steps", "merges",
})

#: The shipped example plan's steps, in file order:
#: (member, slice, branch). The shipped data file
#: is held to exactly this list by the loader's
#: example check: four lines among the M-121
#: casting - forge_worker and scribe and auditor
#: holding two slices each, the guardian one.
_EXAMPLE_STEPS = (
    ("forge_worker", "M-125", "crew/forge_worker/m-125"),
    ("scribe", "M-126", "crew/scribe/m-126"),
    ("guardian", "M-127", "crew/guardian/m-127"),
    ("forge_worker", "M-128", "crew/forge_worker/m-128"),
    ("auditor", "M-130", "crew/auditor/m-130"),
    ("auditor", "M-132", "crew/auditor/m-132"),
    ("scribe", "M-133", "crew/scribe/m-133"),
)

#: The shipped example ledger's merges, in recorded
#: order: (member, slice, branch, gate, outcome).
#: Held to exactly this list beside the steps:
#: forge_worker's line advances on M-125 and stops
#: red at M-128, scribe's M-133 is attempted before
#: M-126 and its M-126 carries no gate, and
#: auditor's M-130 advances its own line untouched.
_EXAMPLE_MERGES = (
    ("forge_worker", "M-125", "crew/forge_worker/m-125",
     "passed", "green"),
    ("forge_worker", "M-128", "crew/forge_worker/m-128",
     "passed", "red"),
    ("scribe", "M-133", "crew/scribe/m-133",
     "passed", "green"),
    ("scribe", "M-126", "crew/scribe/m-126",
     "missing", "green"),
    ("auditor", "M-130", "crew/auditor/m-130",
     "passed", "green"),
)


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_title(value: Any) -> str:
    title = _clean_text(value, "a verdict's title")
    if len(title) > 200 or "\x00" in title:
        raise ValueError(
            f"a verdict's title must be plain text of at most "
            f"200 characters, got {len(title)} characters")
    return title


def _check_detail(value: Any) -> str:
    detail = _clean_text(value, "a verdict's detail")
    if len(detail) > 2000 or "\x00" in detail:
        raise ValueError(
            f"a verdict's detail must be plain text of at most "
            f"2000 characters, got {len(detail)} characters")
    return detail


def _slice_number(slice_id: str) -> int:
    return int(slice_id.split("-", 1)[1])


def normalize_verdict_kind(value: Any) -> str:
    """The canonical verdict kind a word names.

    Kind words read case-insensitively, with dashes
    read as underscores; the plain words ``order``,
    ``gate`` and ``red`` read as the one canonical
    kind each names. Anything else raises.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted in _KIND_READINGS:
            return _KIND_READINGS[wanted]
    raise ValueError(
        "a verdict kind must be one of %s, got %r"
        % ("/".join(VERDICT_KINDS), value))


def normalize_gate(value: Any) -> str:
    """The canonical test gate a word names.

    Gate words read case-insensitively: ``passed``
    (or ``pass``), ``failed`` (or ``fail``) and
    ``missing`` (or ``none`` / ``absent`` - no gate
    was recorded at the merge). Anything else
    raises.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted in _GATE_READINGS:
            return _GATE_READINGS[wanted]
    raise ValueError(
        "a test gate must be one of passed/failed/missing, "
        f"got {value!r}")


def normalize_outcome(value: Any) -> str:
    """The canonical merge outcome a word names.

    Outcome words read case-insensitively: ``green``
    (the merge landed) and ``red`` (the merge failed
    or conflicted - ``failed`` and ``conflicted``
    read as red). Anything else raises.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted in _OUTCOME_READINGS:
            return _OUTCOME_READINGS[wanted]
    raise ValueError(
        f"a merge outcome must be green or red, got {value!r}")


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


# ---------------------------------------------------------------------
# The step: one planned merge on one member's line, as evidence.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class MergeStep:
    """One planned merge: a member, its slice, its branch.

    ``member`` is the member whose line merges the
    slice; ``slice_id`` is the slice it merges;
    ``branch`` is the member branch it merges from,
    read exactly as the M-124 layer reads a branch.
    Constructing one validates its shape only: the
    order steps land in is the judge's concern, not
    the validator's.
    """

    step_id: Optional[str] = None
    member: str = ""
    slice_id: str = ""
    branch: str = ""

    def __post_init__(self) -> None:
        if self.step_id is not None:
            object.__setattr__(
                self, "step_id", normalize_member_id(self.step_id))
        object.__setattr__(
            self, "member", normalize_member_id(self.member))
        object.__setattr__(
            self, "slice_id", normalize_slice_id(self.slice_id))
        object.__setattr__(
            self, "branch", normalize_branch(self.branch))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "merge_step",
            "slice": DISCIPLINE_SLICE,
            "step_id": self.step_id,
            "member": self.member,
            "slice_id": self.slice_id,
            "branch": self.branch,
        }


def validate_step(step: Any) -> MergeStep:
    """Validate one step into a MergeStep.

    Accepts a MergeStep or a mapping naming a
    ``member`` (or ``member_id``), a ``slice_id``
    (or ``slice``), a ``branch`` and an optional
    ``step_id`` (or ``id``). Naming both spellings
    of one field with different values refuses, and
    unknown keys refuse.
    """
    if isinstance(step, MergeStep):
        return step
    if not isinstance(step, dict):
        raise ValueError(f"a step must be a mapping, got {step!r}")
    unknown = set(step) - _STEP_KEYS
    if unknown:
        raise ValueError(
            "unknown step keys: %s" % ", ".join(sorted(unknown)))
    member = _pick(step, "member", "member_id", "members")
    if member is None:
        raise ValueError("a step is missing its member")
    slice_id = _pick(step, "slice_id", "slice", "slices")
    if slice_id is None:
        raise ValueError("a step is missing its slice")
    if "branch" not in step:
        raise ValueError("a step is missing its branch")
    kwargs: Dict[str, Any] = {
        "member": member,
        "slice_id": slice_id,
        "branch": step["branch"],
    }
    step_id = _pick(step, "step_id", "id", "step ids")
    if step_id is not None:
        kwargs["step_id"] = step_id
    return MergeStep(**kwargs)


def build_step(step: Any = None, **kwargs: Any) -> MergeStep:
    """Build one validated step.

    From a MergeStep, from a mapping (the spellings
    :func:`validate_step` reads), or from field
    words given as keyword arguments.
    """
    if isinstance(step, MergeStep) and not kwargs:
        return step
    if isinstance(step, dict) or step is None:
        merged: Dict[str, Any] = {}
        if isinstance(step, dict):
            merged.update(step)
        merged.update(kwargs)
        return validate_step(merged)
    raise ValueError(f"a step must be a mapping, got {step!r}")


# ---------------------------------------------------------------------
# The recorded merge: one merge as it was recorded, as evidence.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class MergeAttempt:
    """One recorded merge, as data.

    ``member`` is the member whose line attempted
    the merge; ``slice_id`` is the slice it tried to
    merge; ``branch`` is the branch it merged from;
    ``gate`` is the test gate recorded at the merge
    (``passed``, ``failed`` or ``missing``);
    ``outcome`` is the merge's outcome (``green`` or
    ``red``). Constructing one validates its shape
    only: an out-of-order, ungated or red merge is
    well-formed evidence - judging it is the
    judge's job, not the validator's.
    """

    attempt_id: Optional[str] = None
    member: str = ""
    slice_id: str = ""
    branch: str = ""
    gate: str = ""
    outcome: str = ""

    def __post_init__(self) -> None:
        if self.attempt_id is not None:
            object.__setattr__(
                self, "attempt_id",
                normalize_member_id(self.attempt_id))
        object.__setattr__(
            self, "member", normalize_member_id(self.member))
        object.__setattr__(
            self, "slice_id", normalize_slice_id(self.slice_id))
        object.__setattr__(
            self, "branch", normalize_branch(self.branch))
        object.__setattr__(self, "gate", normalize_gate(self.gate))
        object.__setattr__(
            self, "outcome", normalize_outcome(self.outcome))

    @property
    def is_red(self) -> bool:
        """True when the recorded merge went red."""
        return self.outcome == "red"

    @property
    def is_gated(self) -> bool:
        """True when a passing test gate is recorded."""
        return self.gate == "passed"

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "merge_attempt",
            "slice": DISCIPLINE_SLICE,
            "attempt_id": self.attempt_id,
            "member": self.member,
            "slice_id": self.slice_id,
            "branch": self.branch,
            "gate": self.gate,
            "outcome": self.outcome,
        }


def validate_attempt(attempt: Any) -> MergeAttempt:
    """Validate one recorded merge into a MergeAttempt.

    Accepts a MergeAttempt or a mapping naming a
    ``member`` (or ``member_id``), a ``slice_id``
    (or ``slice``), a ``branch``, a ``gate`` (or
    ``test_gate``), an ``outcome`` (or ``result``)
    and an optional ``attempt_id`` (or ``id``).
    Naming both spellings of one field with
    different values refuses, and unknown keys
    refuse.
    """
    if isinstance(attempt, MergeAttempt):
        return attempt
    if not isinstance(attempt, dict):
        raise ValueError(
            f"a recorded merge must be a mapping, got {attempt!r}")
    unknown = set(attempt) - _ATTEMPT_KEYS
    if unknown:
        raise ValueError(
            "unknown merge keys: %s" % ", ".join(sorted(unknown)))
    member = _pick(attempt, "member", "member_id", "members")
    if member is None:
        raise ValueError("a recorded merge is missing its member")
    slice_id = _pick(attempt, "slice_id", "slice", "slices")
    if slice_id is None:
        raise ValueError("a recorded merge is missing its slice")
    gate = _pick(attempt, "gate", "test_gate", "gates")
    if gate is None:
        raise ValueError("a recorded merge is missing its gate")
    outcome = _pick(attempt, "outcome", "result", "outcomes")
    if outcome is None:
        raise ValueError("a recorded merge is missing its outcome")
    if "branch" not in attempt:
        raise ValueError("a recorded merge is missing its branch")
    kwargs: Dict[str, Any] = {
        "member": member,
        "slice_id": slice_id,
        "branch": attempt["branch"],
        "gate": gate,
        "outcome": outcome,
    }
    attempt_id = _pick(attempt, "attempt_id", "id", "attempt ids")
    if attempt_id is not None:
        kwargs["attempt_id"] = attempt_id
    return MergeAttempt(**kwargs)


def build_attempt(attempt: Any = None, **kwargs: Any) -> MergeAttempt:
    """Build one validated recorded merge.

    From a MergeAttempt, from a mapping (the
    spellings :func:`validate_attempt` reads), or
    from field words given as keyword arguments.
    """
    if isinstance(attempt, MergeAttempt) and not kwargs:
        return attempt
    if isinstance(attempt, dict) or attempt is None:
        merged: Dict[str, Any] = {}
        if isinstance(attempt, dict):
            merged.update(attempt)
        merged.update(kwargs)
        return validate_attempt(merged)
    raise ValueError(
        f"a recorded merge must be a mapping, got {attempt!r}")


# ---------------------------------------------------------------------
# The verdict and the line: the discipline's judgements, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class MergeVerdict:
    """One judgement on one recorded merge, as data.

    ``kind`` is one of the roadmap's three kinds;
    ``member`` is the member whose line the merge
    belongs to; ``slice_id`` and ``branch`` are the
    slice and branch the merge named; ``title``
    names the judgement in plain words and
    ``detail`` states the whole evidence for it. A
    verdict is derived from evidence by the judge -
    it is a record for the coordinator, never an
    action.
    """

    kind: str = ""
    member: str = ""
    slice_id: str = ""
    branch: str = ""
    title: str = ""
    detail: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "kind", normalize_verdict_kind(self.kind))
        object.__setattr__(
            self, "member", normalize_member_id(self.member))
        object.__setattr__(
            self, "slice_id", normalize_slice_id(self.slice_id))
        object.__setattr__(
            self, "branch", normalize_branch(self.branch))
        object.__setattr__(self, "title", _check_title(self.title))
        object.__setattr__(
            self, "detail", _check_detail(self.detail))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "merge_verdict",
            "slice": DISCIPLINE_SLICE,
            "kind": self.kind,
            "member": self.member,
            "slice_id": self.slice_id,
            "branch": self.branch,
            "title": self.title,
            "detail": self.detail,
        }


def validate_verdict(verdict: Any) -> MergeVerdict:
    """Validate one verdict into a MergeVerdict.

    Accepts a MergeVerdict or a mapping naming a
    ``kind`` (or ``verdict_kind``), a ``member``
    (or ``member_id``), a ``slice_id`` (or
    ``slice``), a ``branch``, a ``title`` and a
    ``detail``. Unknown keys refuse.
    """
    if isinstance(verdict, MergeVerdict):
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
    member = _pick(verdict, "member", "member_id", "members")
    if member is None:
        raise ValueError("a verdict is missing its member")
    slice_id = _pick(verdict, "slice_id", "slice", "slices")
    if slice_id is None:
        raise ValueError("a verdict is missing its slice")
    for field in ("branch", "title", "detail"):
        if field not in verdict:
            raise ValueError(f"a verdict is missing its {field}")
    return MergeVerdict(
        kind=kind,
        member=member,
        slice_id=slice_id,
        branch=verdict["branch"],
        title=verdict["title"],
        detail=verdict["detail"])


def build_verdict(verdict: Any = None, **kwargs: Any) -> MergeVerdict:
    """Build one validated verdict.

    From a MergeVerdict, from a mapping (the
    spellings :func:`validate_verdict` reads), or
    from field words given as keyword arguments.
    """
    if isinstance(verdict, MergeVerdict) and not kwargs:
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
class LineState:
    """One member's merge line, as the evidence leaves it.

    ``member`` is the line's member; ``merged`` are
    the slices the line has merged, in slice order;
    ``pending`` are the slices still waiting, in
    slice order; ``next_slice`` is the slice the
    line merges next (the first pending slice), or
    None when the line is complete; ``stopped`` is
    True when a red merge stopped the line, and
    ``stopped_slice`` is the slice it stopped at.
    A line is derived from evidence by the judge -
    it is never stored.
    """

    member: str = ""
    merged: Tuple[str, ...] = ()
    pending: Tuple[str, ...] = ()
    next_slice: Optional[str] = None
    stopped: bool = False
    stopped_slice: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "member", normalize_member_id(self.member))
        for field in ("merged", "pending"):
            value = getattr(self, field)
            if isinstance(value, (str, bytes)) \
                    or not isinstance(value, (list, tuple)):
                raise ValueError(
                    f"a line's {field} slices must be a list "
                    f"of slice ids, got {value!r}")
            object.__setattr__(self, field, tuple(sorted(
                {normalize_slice_id(s) for s in value},
                key=_slice_number)))
        if self.next_slice is not None:
            object.__setattr__(
                self, "next_slice",
                normalize_slice_id(self.next_slice))
        if self.stopped_slice is not None:
            object.__setattr__(
                self, "stopped_slice",
                normalize_slice_id(self.stopped_slice))
        if bool(self.stopped) != (self.stopped_slice is not None):
            raise ValueError(
                "a line is stopped exactly when it names the "
                "slice it stopped at")

    @property
    def is_complete(self) -> bool:
        """True when the line has merged every planned slice."""
        return self.next_slice is None and not self.stopped

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "merge_line",
            "slice": DISCIPLINE_SLICE,
            "member": self.member,
            "merged": list(self.merged),
            "pending": list(self.pending),
            "next_slice": self.next_slice,
            "stopped": bool(self.stopped),
            "stopped_slice": self.stopped_slice,
        }


# ---------------------------------------------------------------------
# The judge: verdicts and lines derived from the evidence alone.
# ---------------------------------------------------------------------


def _judge(steps: Tuple[MergeStep, ...],
           merges: Tuple[MergeAttempt, ...]) -> Tuple[
               Tuple[MergeVerdict, ...], Tuple[LineState, ...]]:
    planned: Dict[str, list] = {}
    for step in steps:
        planned.setdefault(step.member, []).append(step.slice_id)
    for member in planned:
        planned[member] = sorted(
            set(planned[member]), key=_slice_number)
    merged: Dict[str, list] = {m: [] for m in planned}
    stopped_at: Dict[str, Optional[str]] = {
        m: None for m in planned}
    by_kind: Dict[str, list] = {kind: [] for kind in VERDICT_KINDS}
    for attempt in merges:
        member = attempt.member
        line = planned.get(member)
        if line is None or attempt.slice_id not in line:
            by_kind["out_of_order"].append(MergeVerdict(
                kind="out_of_order",
                member=member,
                slice_id=attempt.slice_id,
                branch=attempt.branch,
                title=(
                    f"Out of order: {member} merges "
                    f"{attempt.slice_id} with no planned step"),
                detail=(
                    f"{member}'s line holds no planned step "
                    f"for {attempt.slice_id}, so the merge "
                    f"of {attempt.slice_id} from "
                    f"{attempt.branch} has no place in the "
                    f"line's slice order and advances "
                    f"nothing, caught for the coordinator "
                    f"to deal the slice or strike the "
                    f"merge.")))
            continue
        if stopped_at[member] is not None:
            by_kind["line_stopped"].append(MergeVerdict(
                kind="line_stopped",
                member=member,
                slice_id=attempt.slice_id,
                branch=attempt.branch,
                title=(
                    f"Line stopped: {member} merges "
                    f"{attempt.slice_id} on a stopped line"),
                detail=(
                    f"{member}'s line stopped at "
                    f"{stopped_at[member]} on a red merge, "
                    f"so the merge of {attempt.slice_id} "
                    f"from {attempt.branch} cannot land "
                    f"until the coordinator clears the "
                    f"stop; every other line keeps its "
                    f"own standing.")))
            continue
        waiting = [s for s in line if s not in merged[member]]
        expected = waiting[0] if waiting else None
        if attempt.slice_id != expected:
            by_kind["out_of_order"].append(MergeVerdict(
                kind="out_of_order",
                member=member,
                slice_id=attempt.slice_id,
                branch=attempt.branch,
                title=(
                    f"Out of order: {member} merges "
                    f"{attempt.slice_id} before {expected}"),
                detail=(
                    f"{member}'s line merges in slice "
                    f"order and {expected} has not merged "
                    f"yet, so the merge of "
                    f"{attempt.slice_id} from "
                    f"{attempt.branch} is refused and "
                    f"advances nothing, caught for the "
                    f"coordinator to land {expected} "
                    f"first.")))
            continue
        if attempt.gate != "passed":
            gate_words = (
                "its test gate failed"
                if attempt.gate == "failed"
                else "no test gate was recorded at it")
            by_kind["missing_test_gate"].append(MergeVerdict(
                kind="missing_test_gate",
                member=member,
                slice_id=attempt.slice_id,
                branch=attempt.branch,
                title=(
                    f"No passing gate: {member} merges "
                    f"{attempt.slice_id} untested"),
                detail=(
                    f"The merge of {attempt.slice_id} from "
                    f"{attempt.branch} was recorded with "
                    f"gate {attempt.gate} - {gate_words} - "
                    f"so it is flagged and advances "
                    f"nothing: a test gate is recorded at "
                    f"each merge, and only a passed gate "
                    f"lets a merge land.")))
            continue
        if attempt.outcome == "red":
            stopped_at[member] = attempt.slice_id
            by_kind["line_stopped"].append(MergeVerdict(
                kind="line_stopped",
                member=member,
                slice_id=attempt.slice_id,
                branch=attempt.branch,
                title=(
                    f"Line stopped: {member} merge of "
                    f"{attempt.slice_id} went red"),
                detail=(
                    f"The merge of {attempt.slice_id} from "
                    f"{attempt.branch} went red behind a "
                    f"passed gate, so {member}'s line "
                    f"stops at {attempt.slice_id} and no "
                    f"later slice on that line lands until "
                    f"the coordinator clears it; the red "
                    f"merge stops the line, not the whole "
                    f"crew - every other line keeps "
                    f"merging in its own order.")))
            continue
        merged[member].append(attempt.slice_id)
    verdicts: list = []
    for kind in VERDICT_KINDS:
        verdicts.extend(by_kind[kind])
    lines = []
    for member in sorted(planned):
        done = tuple(sorted(
            merged[member], key=_slice_number))
        pending = tuple(
            s for s in planned[member] if s not in done)
        lines.append(LineState(
            member=member,
            merged=done,
            pending=pending,
            next_slice=pending[0] if pending else None,
            stopped=stopped_at[member] is not None,
            stopped_slice=stopped_at[member]))
    return tuple(verdicts), tuple(lines)


def _evidence_from(source: Any) -> Tuple[
        Tuple[MergeStep, ...], Tuple[MergeAttempt, ...]]:
    if isinstance(source, MergeDiscipline):
        return source.steps, source.merges
    if isinstance(source, MergeDisciplineRegistry):
        return source.list_steps(), source.list_attempts()
    if isinstance(source, dict):
        unknown = set(source) - {"steps", "merges"}
        if unknown:
            raise ValueError(
                "unknown evidence keys: %s"
                % ", ".join(sorted(unknown)))
        raw_steps = source.get("steps") or ()
        raw_merges = source.get("merges") or ()
        if isinstance(raw_steps, (str, bytes)) \
                or not isinstance(raw_steps, (list, tuple)):
            raise ValueError(
                "evidence steps must be a list of steps")
        if isinstance(raw_merges, (str, bytes)) \
                or not isinstance(raw_merges, (list, tuple)):
            raise ValueError(
                "evidence merges must be a list of merges")
        return (
            tuple(build_step(s) for s in raw_steps),
            tuple(build_attempt(m) for m in raw_merges))
    raise ValueError(f"merge evidence is needed, got {source!r}")


def judge_merges(source: Any) -> Tuple[MergeVerdict, ...]:
    """Every verdict in *source*'s evidence, in fixed order.

    Accepts a MergeDiscipline, a
    MergeDisciplineRegistry or a mapping with
    ``steps`` and ``merges`` lists. The mechanical
    judge of the discipline, as data only:
    out-of-order verdicts first (in recorded
    order), then missing-gate verdicts, then
    line-stopped verdicts - the same evidence
    always yields the same verdicts.
    """
    steps, merges = _evidence_from(source)
    verdicts, _lines = _judge(steps, merges)
    return verdicts


@dataclass(frozen=True)
class MergeReport:
    """One report of verdicts and lines, derived from evidence.

    ``verdicts`` are the judgements the judge
    derived, in judgement order; ``lines`` are the
    state of every planned line, in member order.
    Constructing one validates it: every verdict is
    a verdict and every line a line. A report with
    no verdicts is a clean ledger, not an error.
    """

    verdicts: Tuple[MergeVerdict, ...] = ()
    lines: Tuple[LineState, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.verdicts, (str, bytes)) \
                or not isinstance(self.verdicts, (list, tuple)):
            raise ValueError(
                f"a report's verdicts must be a list of "
                f"verdicts, got {self.verdicts!r}")
        if isinstance(self.lines, (str, bytes)) \
                or not isinstance(self.lines, (list, tuple)):
            raise ValueError(
                f"a report's lines must be a list of lines, "
                f"got {self.lines!r}")
        object.__setattr__(self, "verdicts", tuple(
            v if isinstance(v, MergeVerdict)
            else validate_verdict(v) for v in self.verdicts))
        object.__setattr__(self, "lines", tuple(
            line if isinstance(line, LineState) else line
            for line in self.lines))
        for line in self.lines:
            if not isinstance(line, LineState):
                raise ValueError(
                    f"a report's lines must be lines, got {line!r}")

    @property
    def is_clean(self) -> bool:
        """True when the evidence holds no verdict."""
        return not self.verdicts

    def by_kind(self, kind: Any) -> Tuple[MergeVerdict, ...]:
        """Every verdict of one kind, in report order."""
        wanted = normalize_verdict_kind(kind)
        return tuple(v for v in self.verdicts if v.kind == wanted)

    def for_member(self, member: Any) -> Tuple[MergeVerdict, ...]:
        """Every verdict on one member's line, in order."""
        wanted = normalize_member_id(member)
        return tuple(v for v in self.verdicts if v.member == wanted)

    def line_for(self, member: Any) -> LineState:
        """The one line one member holds; unknown raises."""
        wanted = normalize_member_id(member)
        for line in self.lines:
            if line.member == wanted:
                return line
        raise KeyError(f"no merge line for the member: {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "merge_report",
            "slice": DISCIPLINE_SLICE,
            "count": len(self.verdicts),
            "clean": self.is_clean,
            "out_of_order": len(self.by_kind("out_of_order")),
            "missing_test_gate": len(
                self.by_kind("missing_test_gate")),
            "line_stopped": len(self.by_kind("line_stopped")),
            "verdicts": [v.to_record() for v in self.verdicts],
            "lines": [line.to_record() for line in self.lines],
        }


def validate_report(source: Any, report: Any) -> list:
    """Every problem in a claimed report of *source*, as strings.

    An empty list means the report answers the
    source exactly: every verdict and every line
    the evidence yields, in judgement order, and
    nothing else - a report missing a verdict, or
    holding one the evidence does not hold, is
    named.
    """
    if not isinstance(report, MergeReport):
        return [f"a merge report is needed, got {report!r}"]
    try:
        steps, merges = _evidence_from(source)
    except ValueError as exc:
        return [str(exc)]
    wanted_verdicts, wanted_lines = _judge(steps, merges)
    problems = []
    if tuple(report.verdicts) != wanted_verdicts \
            or tuple(report.lines) != wanted_lines:
        problems.append(
            "the report does not hold exactly the evidence's "
            "verdicts and lines, in judgement order: the "
            "report must catch every verdict the evidence "
            "holds, and no other verdict")
    return problems


# ---------------------------------------------------------------------
# The plan and ledger: the evidence one file holds, under one keeper.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class MergeDiscipline:
    """A whole plan and ledger: the evidence one file holds.

    ``keeper`` is the member id of the one who keeps
    the discipline - in the shipped example the
    forge_worker, the office this slice's work fits.
    Constructing one holds the plan law: at least
    one step, and no line planning the same slice
    twice.
    """

    steps: Tuple[MergeStep, ...] = ()
    merges: Tuple[MergeAttempt, ...] = ()
    keeper: str = ""
    plan_note: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.steps, (str, bytes)) \
                or not isinstance(self.steps, (list, tuple)):
            raise ValueError(
                f"a plan's steps must be a list of steps, "
                f"got {self.steps!r}")
        if isinstance(self.merges, (str, bytes)) \
                or not isinstance(self.merges, (list, tuple)):
            raise ValueError(
                f"a ledger's merges must be a list of merges, "
                f"got {self.merges!r}")
        steps = tuple(
            s if isinstance(s, MergeStep) else validate_step(s)
            for s in self.steps)
        merges = tuple(
            m if isinstance(m, MergeAttempt)
            else validate_attempt(m) for m in self.merges)
        if not steps:
            raise ValueError("a plan must hold at least one step")
        seen = set()
        for step in steps:
            key = (step.member, step.slice_id)
            if key in seen:
                raise ValueError(
                    f"a line plans one slice twice: {step.member} "
                    f"holds {step.slice_id} in two steps")
            seen.add(key)
        object.__setattr__(self, "steps", steps)
        object.__setattr__(self, "merges", merges)
        object.__setattr__(
            self, "keeper", normalize_member_id(self.keeper))
        object.__setattr__(
            self, "plan_note", str(self.plan_note or ""))

    def report(self) -> MergeReport:
        """The report this plan and ledger's evidence yields."""
        verdicts, lines = _judge(self.steps, self.merges)
        return MergeReport(verdicts=verdicts, lines=lines)

    def steps_for(self, member: Any) -> Tuple[MergeStep, ...]:
        """Every step one member's line holds, in file order."""
        wanted = normalize_member_id(member)
        return tuple(s for s in self.steps if s.member == wanted)

    def merges_for(self, member: Any) -> Tuple[MergeAttempt, ...]:
        """Every recorded merge on one line, in recorded order."""
        wanted = normalize_member_id(member)
        return tuple(m for m in self.merges if m.member == wanted)


def validate_plan(data: Any, *,
                  require_example: bool = False) -> list:
    """Every problem in a plan mapping, as plain strings.

    An empty list means the plan and ledger are
    well-formed. With ``require_example`` the file
    must be exactly the shipped example: the seven
    steps and five merges in file order, kept by the
    forge_worker - and the report derived from it
    must hold exactly its three verdicts, one of
    each kind, with forge_worker's line stopped at
    M-128 and auditor's line advanced (the check the
    shipped file is held to; a real plan's file is
    read without it).
    """
    if not isinstance(data, dict):
        return [f"a merge plan must be a mapping, got {data!r}"]
    problems = []
    unknown = set(data) - _PLAN_KEYS
    if unknown:
        problems.append(
            "unknown merge plan keys: %s"
            % ", ".join(sorted(unknown)))
    if data.get("schema") != DISCIPLINE_SCHEMA:
        problems.append(
            f"a merge plan's schema must be "
            f"{DISCIPLINE_SCHEMA!r}, got {data.get('schema')!r}")
    if data.get("slice") != DISCIPLINE_SLICE:
        problems.append(
            f"a merge plan's slice must be "
            f"{DISCIPLINE_SLICE!r}, got {data.get('slice')!r}")
    keeper = None
    if data.get("keeper") is None:
        problems.append("a merge plan is missing its keeper")
    else:
        try:
            keeper = normalize_member_id(data["keeper"])
        except ValueError as exc:
            problems.append(f"keeper: {exc}")
    raw_steps = data.get("steps")
    raw_merges = data.get("merges")
    if not isinstance(raw_steps, list):
        problems.append("a merge plan must hold a steps list")
        raw_steps = []
    if raw_merges is None:
        raw_merges = []
    if not isinstance(raw_merges, list):
        problems.append("a merge plan must hold a merges list")
        raw_merges = []
    if isinstance(raw_steps, list) and not raw_steps:
        problems.append("a merge plan must hold at least one step")
    parsed_steps = []
    for index, entry in enumerate(raw_steps):
        try:
            parsed_steps.append(validate_step(entry))
        except ValueError as exc:
            problems.append(f"step {index + 1}: {exc}")
    parsed_merges = []
    for index, entry in enumerate(raw_merges):
        try:
            parsed_merges.append(validate_attempt(entry))
        except ValueError as exc:
            problems.append(f"merge {index + 1}: {exc}")
    if len(parsed_steps) == len(raw_steps):
        seen = set()
        for step in parsed_steps:
            key = (step.member, step.slice_id)
            if key in seen:
                problems.append(
                    f"a line plans one slice twice: {step.member} "
                    f"holds {step.slice_id} in two steps")
            seen.add(key)
    if require_example \
            and len(parsed_steps) == len(raw_steps) \
            and len(parsed_merges) == len(raw_merges):
        held_steps = tuple(
            (s.member, s.slice_id, s.branch) for s in parsed_steps)
        if held_steps != _EXAMPLE_STEPS:
            problems.append(
                "the shipped example plan must hold exactly "
                "the seven steps in file order, with their "
                "members, slices and branches")
        held_merges = tuple(
            (m.member, m.slice_id, m.branch, m.gate, m.outcome)
            for m in parsed_merges)
        if held_merges != _EXAMPLE_MERGES:
            problems.append(
                "the shipped example ledger must hold exactly "
                "the five merges in recorded order, with "
                "their members, slices, branches, gates and "
                "outcomes")
        if keeper is not None and keeper != "forge_worker":
            problems.append(
                "the shipped example plan is kept by the "
                "forge_worker")
        if held_steps == _EXAMPLE_STEPS \
                and held_merges == _EXAMPLE_MERGES:
            verdicts, lines = _judge(
                tuple(parsed_steps), tuple(parsed_merges))
            kinds = [v.kind for v in verdicts]
            if kinds != ["out_of_order", "missing_test_gate",
                         "line_stopped"]:
                problems.append(
                    "the shipped example plan must yield "
                    "exactly three verdicts, one of each "
                    "kind, in judgement order")
            by_member = {line.member: line for line in lines}
            forge = by_member.get("forge_worker")
            if forge is None or not forge.stopped \
                    or forge.stopped_slice != "M-128" \
                    or forge.merged != ("M-125",):
                problems.append(
                    "the shipped example plan must leave "
                    "forge_worker's line stopped at M-128 "
                    "with M-125 merged")
            auditor = by_member.get("auditor")
            if auditor is None or auditor.stopped \
                    or auditor.merged != ("M-130",) \
                    or auditor.next_slice != "M-132":
                problems.append(
                    "the shipped example plan must leave "
                    "auditor's line advanced on M-130, "
                    "unstopped, next M-132")
    return problems


def _plan_from(data: Any, *, require_example: bool) -> MergeDiscipline:
    problems = validate_plan(data, require_example=require_example)
    if problems:
        raise ValidationError(
            "invalid merge plan: " + "; ".join(problems))
    assert isinstance(data, dict)
    return MergeDiscipline(
        steps=tuple(
            validate_step(entry) for entry in data["steps"]),
        merges=tuple(
            validate_attempt(entry)
            for entry in data.get("merges") or []),
        keeper=data["keeper"],
        plan_note=str(data.get("plan_note") or ""))


def load_merge_discipline(
        data: Optional[Dict[str, Any]] = None) -> MergeDiscipline:
    """Load and validate the shipped example plan (or *data*).

    The shipped file is held to the example check:
    exactly the seven steps and five merges, kept by
    the forge_worker, yielding exactly its three
    verdicts, one of each kind. Raises
    :class:`ValidationError` listing every problem
    when the record is not a well-formed plan.
    """
    raw = data if data is not None else load_resource(
        DISCIPLINE_RESOURCE)
    return _plan_from(raw, require_example=True)


def load_merge_discipline_file(path: Any) -> MergeDiscipline:
    """Load and validate a plan from a file at *path*.

    This is the road a real plan arrives by: any
    file in the plan shape, anywhere on disk,
    validated whole - a malformed file raises
    :class:`ValidationError` naming the problem, and
    a missing file raises ``FileNotFoundError``. The
    example check is not held: a plan may hold a
    single step and no merges yet.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _plan_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: evidence held in registration order, ids
# deterministic. A registry refuses a supplied id already held, and
# refuses nothing for repetition: the same step or merge given twice
# is two pieces of evidence - repetition is judged, never hidden.
# ---------------------------------------------------------------------


class MergeDisciplineRegistry:
    """An in-memory registry of merge evidence.

    Steps and recorded merges are held in
    registration order. Ids are deterministic: a
    caller-supplied id is used as given, and an
    unsupplied id is the next ``step-N`` /
    ``attempt-N`` in sequence, skipping any number
    a supplied id already took. A supplied id
    already held refuses. A plan registered whole
    refuses a duplicated step on one line exactly
    as the plan does. Storage beyond memory (a
    session's journal, a file) is the agent layer's
    concern; this model is neutral.
    """

    def __init__(self) -> None:
        self._steps: Dict[str, MergeStep] = {}
        self._attempts: Dict[str, MergeAttempt] = {}
        self._next_step = 1
        self._next_attempt = 1

    def _fresh_step_id(self) -> str:
        while f"step-{self._next_step}" in self._steps:
            self._next_step += 1
        step_id = f"step-{self._next_step}"
        self._next_step += 1
        return step_id

    def _fresh_attempt_id(self) -> str:
        while f"attempt-{self._next_attempt}" in self._attempts:
            self._next_attempt += 1
        attempt_id = f"attempt-{self._next_attempt}"
        self._next_attempt += 1
        return attempt_id

    def register_step(self, step: Any) -> MergeStep:
        """Register one step and hold it."""
        validated = build_step(step)
        for held in self._steps.values():
            if (held.member, held.slice_id) == (
                    validated.member, validated.slice_id):
                raise ValueError(
                    f"a line plans one slice twice: "
                    f"{validated.member} holds "
                    f"{validated.slice_id} in two steps")
        if validated.step_id is not None \
                and validated.step_id in self._steps:
            raise ValueError(
                f"a step named {validated.step_id!r} already exists")
        if validated.step_id is None:
            validated = replace(
                validated, step_id=self._fresh_step_id())
        self._steps[validated.step_id] = validated
        return validated

    def register_attempt(self, attempt: Any) -> MergeAttempt:
        """Register one recorded merge and hold it."""
        validated = build_attempt(attempt)
        if validated.attempt_id is not None \
                and validated.attempt_id in self._attempts:
            raise ValueError(
                f"a merge named {validated.attempt_id!r} "
                f"already exists")
        if validated.attempt_id is None:
            validated = replace(
                validated, attempt_id=self._fresh_attempt_id())
        self._attempts[validated.attempt_id] = validated
        return validated

    def register_plan(self, plan: Any) -> Tuple[
            Tuple[MergeStep, ...], Tuple[MergeAttempt, ...]]:
        """Register every piece of one plan's evidence, in order."""
        if not isinstance(plan, MergeDiscipline):
            raise ValueError(f"a merge plan is needed, got {plan!r}")
        steps = tuple(self.register_step(s) for s in plan.steps)
        attempts = tuple(
            self.register_attempt(m) for m in plan.merges)
        return steps, attempts

    def get_step(self, step_id: Any) -> MergeStep:
        """The step one id names; an unknown id raises."""
        wanted = normalize_member_id(step_id)
        if wanted not in self._steps:
            raise KeyError(f"unknown step: {wanted!r}")
        return self._steps[wanted]

    def get_attempt(self, attempt_id: Any) -> MergeAttempt:
        """The recorded merge one id names; an unknown id raises."""
        wanted = normalize_member_id(attempt_id)
        if wanted not in self._attempts:
            raise KeyError(f"unknown merge: {wanted!r}")
        return self._attempts[wanted]

    def list_steps(self) -> Tuple[MergeStep, ...]:
        """Every held step, in registration order."""
        return tuple(self._steps.values())

    def list_attempts(self) -> Tuple[MergeAttempt, ...]:
        """Every held recorded merge, in registration order."""
        return tuple(self._attempts.values())

    def verdicts(self) -> Tuple[MergeVerdict, ...]:
        """Every verdict in the held evidence, in judgement order."""
        verdicts, _lines = _judge(
            self.list_steps(), self.list_attempts())
        return verdicts

    def report(self) -> MergeReport:
        """The report the held evidence yields."""
        verdicts, lines = _judge(
            self.list_steps(), self.list_attempts())
        return MergeReport(verdicts=verdicts, lines=lines)

    def for_member(self, member: Any) -> Tuple[MergeVerdict, ...]:
        """Every held verdict on one member's line, in order."""
        return self.report().for_member(member)


# ---------------------------------------------------------------------
# Merge news, shaped as session records.
# ---------------------------------------------------------------------


def step_record(step: Any) -> Dict[str, Any]:
    """The session-news record of one step."""
    current = step if isinstance(step, MergeStep) \
        else build_step(step)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.member} merges {current.slice_id} "
        f"from {current.branch}.")
    return record


def attempt_record(attempt: Any) -> Dict[str, Any]:
    """The session-news record of one recorded merge."""
    current = attempt if isinstance(attempt, MergeAttempt) \
        else build_attempt(attempt)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.member} merge of {current.slice_id} "
        f"recorded {current.outcome} with gate "
        f"{current.gate}.")
    return record


def plain_words(verdict: Any) -> str:
    """One verdict, in one plain sentence."""
    current = verdict if isinstance(verdict, MergeVerdict) \
        else build_verdict(verdict)
    return f"{current.title} - {current.detail}"


def verdict_record(verdict: Any) -> Dict[str, Any]:
    """The session-news record of one verdict.

    Carries the verdict's whole record plus a
    one-line plain headline, so a judgement made in
    a session is news with its shape attached, never
    a bare log line.
    """
    current = verdict if isinstance(verdict, MergeVerdict) \
        else build_verdict(verdict)
    record = current.to_record()
    record["news"] = True
    record["headline"] = plain_words(current)
    return record


def report_plain_words(report: Any) -> str:
    """One merge report, in one plain sentence."""
    current = report if isinstance(report, MergeReport) \
        else MergeReport(verdicts=report)
    if current.is_clean:
        return "The merge ledger is clean: every line advances in order."
    caught = "; ".join(v.title for v in current.verdicts)
    return (
        f"{len(current.verdicts)} verdicts stand for the "
        f"coordinator: {caught}.")


def report_record(report: Any) -> Dict[str, Any]:
    """The session-news record of one merge report.

    ONE record holding every verdict and every line
    with its full evidence - the report itself, as
    news for the coordinator.
    """
    current = report if isinstance(report, MergeReport) \
        else MergeReport(verdicts=report)
    record = current.to_record()
    record["news"] = True
    record["headline"] = report_plain_words(current)
    return record


# ---------------------------------------------------------------------
# The /merge surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def format_verdict(verdict: Any) -> str:
    """One verdict, in plain words."""
    current = verdict if isinstance(verdict, MergeVerdict) \
        else build_verdict(verdict)
    return f"  {current.kind}: {plain_words(current)}"


def _selected_verdicts(source: Any) -> Tuple[MergeVerdict, ...]:
    if source is None:
        return load_merge_discipline().report().verdicts
    if isinstance(source, MergeReport):
        return source.verdicts
    if isinstance(source, (MergeDiscipline,
                           MergeDisciplineRegistry, dict)):
        return judge_merges(source)
    if isinstance(source, (str, bytes)) \
            or not isinstance(source, (list, tuple)):
        raise ValueError("verdicts must be a list of verdicts")
    return tuple(
        v if isinstance(v, MergeVerdict) else build_verdict(v)
        for v in source)


def format_verdicts(source: Any = None) -> str:
    """The verdicts, in plain words, in judgement order.

    Accepts a list of verdicts, a MergeReport, a
    MergeDiscipline or a MergeDisciplineRegistry.
    With no source the shipped example plan's
    verdicts are shown. With no verdicts at all the
    text states the ledger is clean, plainly.
    """
    selected = _selected_verdicts(source)
    if not selected:
        return ("Merge discipline: clean. No out-of-order "
                "merge, missing test gate or stopped line "
                "stands.")
    lines = [
        f"Merge discipline: {len(selected)} verdicts stand "
        f"for the coordinator."]
    for verdict in selected:
        lines.append(format_verdict(verdict))
    return "\n".join(lines)


def _selected_lines(source: Any) -> Tuple[LineState, ...]:
    if source is None:
        return load_merge_discipline().report().lines
    if isinstance(source, MergeReport):
        return source.lines
    if isinstance(source, MergeDiscipline):
        return source.report().lines
    if isinstance(source, MergeDisciplineRegistry):
        return source.report().lines
    raise ValueError(f"merge lines are needed, got {source!r}")


def format_lines(source: Any = None) -> str:
    """Every line's state, in plain words, in member order.

    Accepts a MergeReport, a MergeDiscipline or a
    MergeDisciplineRegistry. With no source the
    shipped example plan's lines are shown.
    """
    selected = _selected_lines(source)
    if not selected:
        return "Merge lines: no line is planned yet."
    rendered = ["Merge lines:"]
    for line in selected:
        merged_words = ", ".join(line.merged) if line.merged \
            else "none"
        if line.stopped:
            standing = f"stopped at {line.stopped_slice}"
        elif line.next_slice is None:
            standing = "complete"
        else:
            standing = f"next {line.next_slice}"
        rendered.append(
            f"  {line.member}: merged {merged_words}; {standing}.")
    return "\n".join(rendered)


def format_kinds() -> str:
    """The verdict kinds, in plain words."""
    return (
        "Verdict kinds: out_of_order (a merge attempted "
        "out of its line's slice order, or for a slice "
        "its line never planned), missing_test_gate (a "
        "merge recorded with a failed or missing test "
        "gate, flagged and advancing nothing), "
        "line_stopped (a red merge stopping only its "
        "own line at that slice, and any later merge "
        "attempted on the stopped line).")


def format_merge_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /merge.

    With nothing named, the shipped example plan's
    verdicts and lines are shown - the example this
    slice ships - so the screen is never empty.
    There is no Part VIII board yet; this screen is
    where the verdicts are visible.
    """
    lines = ["Merge discipline (M-128) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_verdicts(source))
    lines.append("")
    lines.append(format_lines(source))
    lines.append("")
    lines.append(format_kinds())
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_merge_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /merge grammar both surfaces share.

    No words (or ``show`` / ``list`` / ``verdicts``)
    shows the verdicts; ``show <member>`` and a bare
    member id show one member's verdicts; ``lines``
    shows every line's state; ``kinds`` asks for the
    kinds. Anything else is a usage error naming the
    grammar. Returns ``(action, value-or-None)``.
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
            return ("show", normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "lines" and len(words) == 1:
        return ("lines", None)
    if head == "kinds" and len(words) == 1:
        return ("kinds", None)
    if head in ("show", "kinds", "lines", "list", "verdicts"):
        raise ValueError(USAGE)
    if len(words) == 1:
        try:
            return ("show", normalize_member_id(words[0]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
