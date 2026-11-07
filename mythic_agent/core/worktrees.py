"""Parallel worktrees (All-Features roadmap slice M-124).

Part VI - Agents as files - continues here. The
roadmap's words: ``each building crew member works
in its own git worktree on its own branch (the house
law from bitter experience); the coordinator merges
- never two writers in one tree.``

What already shipped, and what this slice adds:

* Parallel subagents already exist
  (``mythic_agent/agents/parallel.py`` - a thread-pool
  executor that runs independent tool calls
  concurrently and orders dependent ones), and a
  workspace already has a portable identity and
  contained file resolution
  (``mythic_agent/core/workspace.py``). The crew
  itself is already data (``core/crew_members.py``,
  M-121: every member holds one office). What
  nothing held is the worktree discipline itself as
  data: which member writes in which worktree, on
  which branch, for which slice, and the order in
  which the coordinator - the only merger - merges
  those branches. Parallel writers without that
  record are exactly how two writers end up in one
  tree.
* This slice is that record, as a pure layer: a
  worktree assignment validated as data (member,
  office, slice, branch, worktree path), a plan
  holding assignments under the house law, a loader
  for a plan file anywhere on disk, the coordinator
  merge plan derived from a plan in slice order, a
  worktree record shaped as session news, and a
  small in-memory registry model. The shipped data
  file (``mythic_agent/data/worktrees.yaml``) holds
  one example plan - the shipped M-121 casting, each
  member given its own worktree for an example wave
  - in exactly the shape a real wave's plan file
  takes. This module runs no git command, creates
  no worktree, merges nothing and imports no agent
  / UI code; the agent layer owns creating the real
  worktrees from a plan, holding the registry for a
  session, and carrying out the merges the plan
  names, in the plan's order.

Honesty rules, enforced here and pinned by tests:

* **Never two writers in one tree.** A plan refuses
  a duplicated worktree path, a duplicated branch,
  and a member holding two assignments - each is a
  spelling of two writers sharing one tree or one
  line of work, and each refuses whole, naming the
  collision.
* **The coordinator merges, and only the
  coordinator.** A plan names one coordinator, who
  holds no writer assignment in that plan. Every
  step of the derived merge plan names the
  coordinator as its merger, and a merge step
  naming anyone else refuses validation - merging
  is never a writer's own act in this layer's
  record.
* **Merges land in roadmap order.** The merge plan
  is derived, never stored: its steps are the
  plan's assignments ordered by slice number
  (assignment order breaking ties), so the order
  work is taken up in is the order it merges in.
* **Members and offices are the shipped crew's.**
  A member id reads exactly as the M-121 layer
  reads one and an office exactly as the M-121
  layer reads a crew office - composed with by
  import, never re-read here - so ``primary`` (the
  lead session itself) can never hold a worktree,
  and an unknown office refuses. The shipped
  example plan is pinned against the live M-121
  casting by tests: its members are the casting,
  in casting order, each holding its cast office.
* **Branch and path names are validated, never
  trusted.** A branch must be a git-safe name (no
  empty or dot-leading segment, no ``..``, no
  ``.lock`` ending, no whitespace or control
  characters); a worktree path must be a relative
  portable path of safe segments - never absolute,
  never carrying a ``..`` or ``.git`` segment - so
  a plan can never name a tree outside the place
  worktrees belong, or inside git's own metadata.
* **Malformed refuses.** An unknown member or
  office, a malformed slice / branch / path, a
  duplicate in one plan, and unknown keys in an
  assignment or plan mapping all raise instead of
  being skipped or guessed at.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id, normalize_office
from .validation import ValidationError

__all__ = [
    "PLAIN_EXPLANATION",
    "USAGE",
    "WORKTREES_RESOURCE",
    "WORKTREES_SCHEMA",
    "WORKTREES_SLICE",
    "MergeStep",
    "WorktreeAssignment",
    "WorktreePlan",
    "WorktreeRegistry",
    "build_assignment",
    "format_assignment",
    "format_assignments",
    "format_merge_plan",
    "format_worktrees_screen",
    "load_worktree_plan",
    "load_worktree_plan_file",
    "merge_plan_for",
    "normalize_branch",
    "normalize_slice_id",
    "normalize_worktree_path",
    "parse_worktrees_args",
    "plain_words",
    "suggest_branch",
    "suggest_path",
    "validate_assignment",
    "validate_merge_steps",
    "validate_plan",
    "worktree_record",
]

WORKTREES_SLICE = "M-124"

#: The packaged data resource holding the example plan.
WORKTREES_RESOURCE = "worktrees.yaml"

#: The schema word a worktree plan file must carry.
WORKTREES_SCHEMA = "mythic.worktrees/1"

#: The last slice on the roadmap (272 slices, M-001..M-272).
_LAST_SLICE = 272

PLAIN_EXPLANATION = (
    "Parallel worktrees: each building crew member "
    "works in its own git worktree on its own branch "
    "- never two writers in one tree - and the "
    "coordinator, who holds no worktree of their own "
    "in the plan, is the only one who merges. A plan "
    "holds one assignment per member (the member, "
    "the office it holds, the slice it builds, its "
    "branch and its worktree path); a duplicated "
    "member, branch or path refuses whole. The merge "
    "plan is derived from the assignments in slice "
    "order, every step merged by the coordinator. "
    "This layer holds plans and assignments as data "
    "only; it runs no git command and merges nothing "
    "itself."
)

USAGE = (
    "Usage: /worktrees, /worktrees show, "
    "/worktrees show <member>, /worktrees plan, "
    "/worktrees merges"
)

_ASSIGNMENT_KEYS = frozenset({
    "id", "assignment_id", "member", "member_id", "office",
    "slice", "slice_id", "branch", "path", "worktree_path",
})

_PLAN_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "plan_note", "coordinator", "assignments",
})

_SLICE_RE = re.compile(r"^[Mm]-(\d{1,3})$")

_BRANCH_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789-_/.")

_PATH_SEGMENT_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789-_.")


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def normalize_slice_id(value: Any) -> str:
    """The canonical slice id a word names (``M-124``).

    Slice words read case-insensitively as ``M-``
    plus a number on the roadmap (M-001..M-272).
    Anything else raises.
    """
    if isinstance(value, str):
        match = _SLICE_RE.match(value.strip())
        if match:
            number = int(match.group(1))
            if 1 <= number <= _LAST_SLICE:
                return f"M-{number:03d}"
    raise ValueError(
        f"a slice id must be M-001..M-{_LAST_SLICE:03d}, "
        f"got {value!r}")


def _slice_number(slice_id: str) -> int:
    return int(slice_id.split("-", 1)[1])


def normalize_branch(value: Any) -> str:
    """The canonical branch name a word names.

    A branch is one git-safe name: segments of
    letters, digits, dashes, underscores and dots
    joined by single slashes; no segment empty,
    dot-leading or ``.lock``-ending; never ``..``,
    never ``HEAD``, never leading / trailing slash
    or dot. Anything else raises.
    """
    if isinstance(value, str):
        wanted = value.strip()
        if wanted and len(wanted) <= 200 \
                and all(ch in _BRANCH_CHARS for ch in wanted) \
                and ".." not in wanted and wanted != "HEAD" \
                and not wanted.startswith(("/", ".")) \
                and not wanted.endswith(("/", ".")):
            segments = wanted.split("/")
            if all(segment and not segment.startswith(".")
                   and not segment.endswith(".lock")
                   for segment in segments):
                return wanted
    raise ValueError(
        f"a branch must be a git-safe name of segments joined "
        f"by single slashes, got {value!r}")


def normalize_worktree_path(value: Any) -> str:
    """The canonical worktree path a word names.

    A worktree path is a relative portable path:
    segments of letters, digits, dashes, underscores
    and dots joined by single slashes - never
    absolute, never a backslash, never a ``.``,
    ``..`` or ``.git`` segment, never a trailing
    slash. Anything else raises.
    """
    if isinstance(value, str):
        wanted = value.strip()
        if wanted and len(wanted) <= 240 and "\\" not in wanted \
                and "\x00" not in wanted \
                and not wanted.startswith("/") \
                and not wanted.endswith("/"):
            segments = wanted.split("/")
            if all(segment and segment not in (".", "..", ".git")
                   and all(ch in _PATH_SEGMENT_CHARS for ch in segment)
                   for segment in segments):
                return wanted
    raise ValueError(
        f"a worktree path must be a relative path of safe "
        f"segments, got {value!r}")


def suggest_path(member: Any) -> str:
    """The conventional worktree path for one member."""
    return f"worktrees/{normalize_member_id(member)}"


def suggest_branch(member: Any, slice_id: Any) -> str:
    """The conventional branch for one member's slice."""
    return (f"crew/{normalize_member_id(member)}/"
            f"{normalize_slice_id(slice_id).lower()}")


# ---------------------------------------------------------------------
# The assignment: one member, one tree, one branch, one slice.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class WorktreeAssignment:
    """One crew member's worktree assignment, as data.

    ``member`` is the member's M-121 member id;
    ``office`` is the crew office it holds;
    ``slice_id`` is the roadmap slice it builds;
    ``branch`` is its own branch; ``path`` is its
    own worktree path. Constructing one validates
    it, so an assignment that exists is one the
    house law allows a plan to hold (plan-level
    collisions are the plan's own checks).
    """

    assignment_id: Optional[str] = None
    member: str = ""
    office: str = ""
    slice_id: str = ""
    branch: str = ""
    path: str = ""

    def __post_init__(self) -> None:
        if self.assignment_id is not None:
            object.__setattr__(
                self, "assignment_id",
                normalize_member_id(self.assignment_id))
        object.__setattr__(
            self, "member", normalize_member_id(self.member))
        object.__setattr__(
            self, "office", normalize_office(self.office))
        object.__setattr__(
            self, "slice_id", normalize_slice_id(self.slice_id))
        object.__setattr__(
            self, "branch", normalize_branch(self.branch))
        object.__setattr__(
            self, "path", normalize_worktree_path(self.path))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "worktree_assignment",
            "slice": WORKTREES_SLICE,
            "assignment_id": self.assignment_id,
            "member": self.member,
            "office": self.office,
            "slice_id": self.slice_id,
            "branch": self.branch,
            "path": self.path,
        }


def _pick(mapping: Dict[str, Any], first: str, second: str,
          what: str) -> Any:
    """One field from its two spellings, or a refusal."""
    if first in mapping and second in mapping:
        if mapping[first] != mapping[second]:
            raise ValueError(f"an assignment names two different {what}")
        return mapping[first]
    if first in mapping:
        return mapping[first]
    return mapping.get(second)


def validate_assignment(assignment: Any) -> WorktreeAssignment:
    """Validate one worktree assignment into a WorktreeAssignment.

    Accepts a WorktreeAssignment or a mapping naming
    a ``member`` (or ``member_id``), an ``office``, a
    ``slice_id`` (or ``slice``), a ``branch``, a
    ``path`` (or ``worktree_path``) and an optional
    ``assignment_id`` (or ``id``). Naming both
    spellings of one field with different values
    refuses, and unknown keys refuse.
    """
    if isinstance(assignment, WorktreeAssignment):
        return assignment
    if not isinstance(assignment, dict):
        raise ValueError(
            f"a worktree assignment must be a mapping, "
            f"got {assignment!r}")
    unknown = set(assignment) - _ASSIGNMENT_KEYS
    if unknown:
        raise ValueError(
            "unknown worktree assignment keys: %s"
            % ", ".join(sorted(unknown)))
    member = _pick(assignment, "member", "member_id", "members")
    if member is None:
        raise ValueError("a worktree assignment is missing its member")
    slice_id = _pick(assignment, "slice_id", "slice", "slices")
    if slice_id is None:
        raise ValueError("a worktree assignment is missing its slice")
    path = _pick(assignment, "path", "worktree_path", "paths")
    if path is None:
        raise ValueError("a worktree assignment is missing its path")
    for field in ("office", "branch"):
        if field not in assignment:
            raise ValueError(
                f"a worktree assignment is missing its {field}")
    kwargs: Dict[str, Any] = {
        "member": member,
        "office": assignment["office"],
        "slice_id": slice_id,
        "branch": assignment["branch"],
        "path": path,
    }
    assignment_id = _pick(
        assignment, "assignment_id", "id", "assignment ids")
    if assignment_id is not None:
        kwargs["assignment_id"] = assignment_id
    return WorktreeAssignment(**kwargs)


def build_assignment(assignment: Any = None,
                     **kwargs: Any) -> WorktreeAssignment:
    """Build one validated worktree assignment.

    From a WorktreeAssignment, from a mapping (the
    spellings :func:`validate_assignment` reads), or
    from field words given as keyword arguments.
    """
    if isinstance(assignment, WorktreeAssignment) and not kwargs:
        return assignment
    if isinstance(assignment, dict) or assignment is None:
        merged: Dict[str, Any] = {}
        if isinstance(assignment, dict):
            merged.update(assignment)
        merged.update(kwargs)
        return validate_assignment(merged)
    raise ValueError(
        f"a worktree assignment must be a mapping, "
        f"got {assignment!r}")


# ---------------------------------------------------------------------
# The merge step: one branch, merged by the coordinator, in order.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class MergeStep:
    """One step of a coordinator merge plan, as data.

    ``order`` is the step's 1-based place in the
    plan; ``slice_id`` / ``member`` / ``branch`` /
    ``path`` name the assignment being merged;
    ``merger`` names who merges it - in any valid
    plan, the plan's coordinator and no one else
    (held by :func:`validate_merge_steps`, which
    knows the plan a step claims to belong to).
    """

    order: int = 0
    slice_id: str = ""
    member: str = ""
    branch: str = ""
    path: str = ""
    merger: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.order, int) \
                or isinstance(self.order, bool) or self.order < 1:
            raise ValueError(
                f"a merge step's order must be a positive "
                f"integer, got {self.order!r}")
        object.__setattr__(
            self, "slice_id", normalize_slice_id(self.slice_id))
        object.__setattr__(
            self, "member", normalize_member_id(self.member))
        object.__setattr__(
            self, "branch", normalize_branch(self.branch))
        object.__setattr__(
            self, "path", normalize_worktree_path(self.path))
        object.__setattr__(
            self, "merger", normalize_member_id(self.merger))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "merge_step",
            "slice": WORKTREES_SLICE,
            "order": self.order,
            "slice_id": self.slice_id,
            "member": self.member,
            "branch": self.branch,
            "path": self.path,
            "merger": self.merger,
        }


# ---------------------------------------------------------------------
# The plan: a wave's assignments under one coordinator, as data.
# ---------------------------------------------------------------------


def _check_plan_collisions(
        assignments: Tuple[WorktreeAssignment, ...],
        coordinator: str) -> None:
    seen_members, seen_branches, seen_paths = set(), set(), set()
    for assignment in assignments:
        if assignment.member in seen_members:
            raise ValueError(
                f"the member {assignment.member!r} holds two "
                "assignments in one plan; one member, one tree")
        seen_members.add(assignment.member)
        if assignment.branch in seen_branches:
            raise ValueError(
                f"the branch {assignment.branch!r} is assigned "
                "twice in one plan; one branch, one writer")
        seen_branches.add(assignment.branch)
        if assignment.path in seen_paths:
            raise ValueError(
                f"the worktree {assignment.path!r} is assigned "
                "twice in one plan; never two writers in one tree")
        seen_paths.add(assignment.path)
    if coordinator in seen_members:
        raise ValueError(
            f"the coordinator {coordinator!r} holds a writer "
            "assignment in this plan; the coordinator merges, "
            "and does not write in a plan they merge")


@dataclass(frozen=True)
class WorktreePlan:
    """A whole plan: the assignments one file deals, in file order.

    ``coordinator`` is the member id of the one who
    merges - never one of the assigned writers.
    Constructing one holds the house law: no member,
    branch or path twice, and the coordinator holds
    no assignment.
    """

    assignments: Tuple[WorktreeAssignment, ...] = ()
    coordinator: str = ""
    plan_note: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.assignments, (str, bytes)) \
                or not isinstance(self.assignments, (list, tuple)):
            raise ValueError(
                f"a plan's assignments must be a list of "
                f"assignments, got {self.assignments!r}")
        assignments = tuple(
            a if isinstance(a, WorktreeAssignment)
            else validate_assignment(a) for a in self.assignments)
        if not assignments:
            raise ValueError("a plan must hold at least one assignment")
        coordinator = normalize_member_id(self.coordinator)
        _check_plan_collisions(assignments, coordinator)
        object.__setattr__(self, "assignments", assignments)
        object.__setattr__(self, "coordinator", coordinator)
        object.__setattr__(
            self, "plan_note",
            str(self.plan_note or ""))

    def get(self, member: Any) -> WorktreeAssignment:
        """The assignment one member holds; unheld raises KeyError."""
        wanted = normalize_member_id(member)
        for assignment in self.assignments:
            if assignment.member == wanted:
                return assignment
        raise KeyError(f"no assignment holds the member: {wanted!r}")

    def merge_plan(self) -> Tuple[MergeStep, ...]:
        """This plan's merge steps, in slice order."""
        return merge_plan_for(self)


def merge_plan_for(plan: Any) -> Tuple[MergeStep, ...]:
    """Derive a plan's merge steps: slice order, coordinator merges.

    Steps are the plan's assignments ordered by slice
    number, assignment (file) order breaking ties,
    each step's merger the plan's coordinator. The
    plan is derived, never stored, so it can never
    disagree with the assignments it merges.
    """
    if not isinstance(plan, WorktreePlan):
        raise ValueError(f"a worktree plan is needed, got {plan!r}")
    ordered = sorted(
        enumerate(plan.assignments),
        key=lambda pair: (_slice_number(pair[1].slice_id), pair[0]))
    return tuple(
        MergeStep(order=index + 1, slice_id=assignment.slice_id,
                  member=assignment.member, branch=assignment.branch,
                  path=assignment.path, merger=plan.coordinator)
        for index, (_, assignment) in enumerate(ordered))


def validate_merge_steps(plan: Any, steps: Any) -> list:
    """Every problem in a claimed merge plan for *plan*, as strings.

    An empty list means the steps are exactly the
    plan's derived merge plan: every assignment
    merged exactly once, in slice order, every step
    merged by the plan's coordinator - a step naming
    any other merger is the coordinator-only refusal.
    """
    if not isinstance(plan, WorktreePlan):
        return [f"a worktree plan is needed, got {plan!r}"]
    if isinstance(steps, (str, bytes)) \
            or not isinstance(steps, (list, tuple)):
        return [f"merge steps must be a list of steps, got {steps!r}"]
    problems = []
    parsed = []
    for index, entry in enumerate(steps):
        if not isinstance(entry, MergeStep):
            problems.append(
                f"merge step {index + 1}: a merge step is needed, "
                f"got {entry!r}")
            continue
        parsed.append(entry)
    expected = merge_plan_for(plan)
    if len(parsed) != len(expected):
        problems.append(
            f"a merge plan for this plan holds {len(expected)} "
            f"steps, got {len(parsed)}")
    for step in parsed:
        if step.merger != plan.coordinator:
            problems.append(
                f"merge step {step.order}: {step.merger!r} may not "
                f"merge; only the coordinator "
                f"{plan.coordinator!r} merges")
    if parsed != list(expected):
        problems.append(
            "the merge steps are not this plan's derived merge "
            "plan: every assignment merged exactly once, in "
            "slice order, by the coordinator")
    return problems


def validate_plan(data: Any, *,
                  require_example: bool = False) -> list:
    """Every problem in a worktree plan mapping, as plain strings.

    An empty list means the plan is well-formed.
    With ``require_example`` the plan must be exactly
    the shipped example: the M-121 casting's members,
    in casting order, each holding its cast office,
    each on its conventional branch and path, slices
    dealt uniquely (the check the shipped file is
    held to; a real wave's plan file is read without
    it). The house-law collisions are always held.
    """
    if not isinstance(data, dict):
        return [f"a worktree plan must be a mapping, got {data!r}"]
    problems = []
    unknown = set(data) - _PLAN_KEYS
    if unknown:
        problems.append(
            "unknown worktree plan keys: %s"
            % ", ".join(sorted(unknown)))
    if data.get("schema") != WORKTREES_SCHEMA:
        problems.append(
            f"a worktree plan's schema must be "
            f"{WORKTREES_SCHEMA!r}, got {data.get('schema')!r}")
    if data.get("slice") != WORKTREES_SLICE:
        problems.append(
            f"a worktree plan's slice must be "
            f"{WORKTREES_SLICE!r}, got {data.get('slice')!r}")
    coordinator_raw = data.get("coordinator")
    coordinator = None
    if coordinator_raw is None:
        problems.append("a worktree plan is missing its coordinator")
    else:
        try:
            coordinator = normalize_member_id(coordinator_raw)
        except ValueError as exc:
            problems.append(f"coordinator: {exc}")
    raw = data.get("assignments")
    if not isinstance(raw, list) or not raw:
        problems.append(
            "a worktree plan must hold a non-empty assignments list")
        return problems
    parsed = []
    for index, entry in enumerate(raw):
        try:
            parsed.append(validate_assignment(entry))
        except ValueError as exc:
            problems.append(f"assignment {index + 1}: {exc}")
    if len(parsed) == len(raw) and coordinator is not None:
        try:
            _check_plan_collisions(tuple(parsed), coordinator)
        except ValueError as exc:
            problems.append(str(exc))
    if require_example and len(parsed) == len(raw):
        from .crew_members import load_casting
        casting = load_casting()
        held = tuple(a.member for a in parsed)
        expected = tuple(m.member_id for m in casting.members)
        if held != expected:
            problems.append(
                "the shipped example plan must hold exactly the "
                "M-121 casting's members in casting order (%s), "
                "got %s" % ("/".join(expected),
                            "/".join(held) or "none"))
        else:
            seen_slices = set()
            for assignment, member in zip(parsed, casting.members):
                if assignment.office != member.office:
                    problems.append(
                        f"the example assignment for "
                        f"{assignment.member!r} holds the office "
                        f"{assignment.office!r}, not its cast "
                        f"office {member.office!r}")
                if assignment.branch != suggest_branch(
                        assignment.member, assignment.slice_id):
                    problems.append(
                        f"the example assignment for "
                        f"{assignment.member!r} is not on its "
                        "conventional branch")
                if assignment.path != suggest_path(assignment.member):
                    problems.append(
                        f"the example assignment for "
                        f"{assignment.member!r} is not at its "
                        "conventional worktree path")
                if assignment.slice_id in seen_slices:
                    problems.append(
                        f"the example plan deals the slice "
                        f"{assignment.slice_id!r} twice")
                seen_slices.add(assignment.slice_id)
    return problems


def _plan_from(data: Any, *, require_example: bool) -> WorktreePlan:
    problems = validate_plan(data, require_example=require_example)
    if problems:
        raise ValidationError(
            "invalid worktree plan: " + "; ".join(problems))
    assert isinstance(data, dict)
    return WorktreePlan(
        assignments=tuple(
            validate_assignment(entry) for entry in data["assignments"]),
        coordinator=data["coordinator"],
        plan_note=str(data.get("plan_note") or ""))


def load_worktree_plan(
        data: Optional[Dict[str, Any]] = None) -> WorktreePlan:
    """Load and validate the shipped example plan (or *data*).

    The shipped file is held to the example check:
    exactly the M-121 casting, in casting order, each
    member on its conventional branch and path.
    Raises :class:`ValidationError` listing every
    problem when the record is not a well-formed plan.
    """
    raw = data if data is not None else load_resource(WORKTREES_RESOURCE)
    return _plan_from(raw, require_example=True)


def load_worktree_plan_file(path: Any) -> WorktreePlan:
    """Load and validate a worktree plan from a file at *path*.

    This is the road a real wave's plan arrives by:
    any file in the plan shape, anywhere on disk,
    validated whole - a malformed file raises
    :class:`ValidationError` naming the problem, and
    a missing file raises ``FileNotFoundError``. The
    example check is not held: a plan may deal a
    single assignment.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _plan_from(raw, require_example=False)


# ---------------------------------------------------------------------
# Assignment news, shaped as a session record.
# ---------------------------------------------------------------------


def worktree_record(assignment: Any) -> Dict[str, Any]:
    """The session-news record of one worktree assignment.

    Carries the assignment's whole record plus a
    one-line plain headline, so a member taking up
    its tree in a session is news with its shape
    attached, never a bare log line.
    """
    current = assignment if isinstance(assignment, WorktreeAssignment) \
        else build_assignment(assignment)
    record = current.to_record()
    record["news"] = True
    record["headline"] = plain_words(current)
    return record


def plain_words(assignment: Any) -> str:
    """One assignment, in one plain sentence."""
    current = assignment if isinstance(assignment, WorktreeAssignment) \
        else build_assignment(assignment)
    office_title = current.office.replace("_", " ")
    return (
        f"{current.member} ({office_title}) builds "
        f"{current.slice_id} in {current.path} on branch "
        f"{current.branch} - the only writer in that tree.")


# ---------------------------------------------------------------------
# The registry model: assignments held in registration order, ids
# deterministic.
# ---------------------------------------------------------------------


class WorktreeRegistry:
    """An in-memory registry of worktree assignments.

    Assignments are held in registration order. Ids
    are deterministic: a caller-supplied id is used
    as given, and an unsupplied id is the next
    ``worktree-N`` in sequence, skipping any number a
    supplied id already took. The house law is held
    across the whole registry, not just one plan: a
    member, branch or path already held refuses -
    never two writers in one tree, whichever plan
    dealt them. Storage beyond memory (a session's
    journal, a file) is the agent layer's concern;
    this model is neutral.
    """

    def __init__(self) -> None:
        self._assignments: Dict[str, WorktreeAssignment] = {}
        self._next = 1

    def _fresh_id(self) -> str:
        while f"worktree-{self._next}" in self._assignments:
            self._next += 1
        assignment_id = f"worktree-{self._next}"
        self._next += 1
        return assignment_id

    def register(self, assignment: Any) -> WorktreeAssignment:
        """Register one assignment and hold it; collisions refuse."""
        validated = build_assignment(assignment)
        if validated.assignment_id is None:
            validated = replace(
                validated, assignment_id=self._fresh_id())
        elif validated.assignment_id in self._assignments:
            raise ValueError(
                f"a worktree assignment named "
                f"{validated.assignment_id!r} already exists")
        for held in self._assignments.values():
            if held.member == validated.member:
                raise ValueError(
                    f"the member {validated.member!r} already "
                    "holds a worktree assignment")
            if held.branch == validated.branch:
                raise ValueError(
                    f"the branch {validated.branch!r} is already "
                    "assigned; one branch, one writer")
            if held.path == validated.path:
                raise ValueError(
                    f"the worktree {validated.path!r} is already "
                    "assigned; never two writers in one tree")
        self._assignments[validated.assignment_id] = validated
        return validated

    def register_plan(self, plan: Any) -> Tuple[WorktreeAssignment, ...]:
        """Register every assignment of one plan, in file order."""
        if not isinstance(plan, WorktreePlan):
            raise ValueError(f"a worktree plan is needed, got {plan!r}")
        return tuple(self.register(a) for a in plan.assignments)

    def get(self, assignment_id: Any) -> WorktreeAssignment:
        """The assignment one id names; an unknown id raises KeyError."""
        wanted = normalize_member_id(assignment_id)
        if wanted not in self._assignments:
            raise KeyError(f"unknown worktree assignment: {wanted!r}")
        return self._assignments[wanted]

    def by_member(self, member: Any) -> WorktreeAssignment:
        """The assignment one member holds; unheld raises KeyError."""
        wanted = normalize_member_id(member)
        for held in self._assignments.values():
            if held.member == wanted:
                return held
        raise KeyError(f"no assignment holds the member: {wanted!r}")

    def by_branch(self, branch: Any) -> WorktreeAssignment:
        """The assignment on one branch; unheld raises KeyError."""
        wanted = normalize_branch(branch)
        for held in self._assignments.values():
            if held.branch == wanted:
                return held
        raise KeyError(f"no assignment holds the branch: {wanted!r}")

    def by_path(self, path: Any) -> WorktreeAssignment:
        """The assignment at one worktree path; unheld raises."""
        wanted = normalize_worktree_path(path)
        for held in self._assignments.values():
            if held.path == wanted:
                return held
        raise KeyError(f"no assignment holds the worktree: {wanted!r}")

    def list_assignments(self, office: Any = None
                         ) -> Tuple[WorktreeAssignment, ...]:
        """Every held assignment, in registration order, by office."""
        assignments = tuple(self._assignments.values())
        if office is None:
            return assignments
        wanted = normalize_office(office)
        return tuple(a for a in assignments if a.office == wanted)


# ---------------------------------------------------------------------
# The /worktrees surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def format_assignment(assignment: Any) -> str:
    """One assignment, in plain words."""
    current = assignment if isinstance(assignment, WorktreeAssignment) \
        else build_assignment(assignment)
    name = current.assignment_id or current.member
    return f"  {name}: {plain_words(current)}"


def format_assignments(assignments: Any = None) -> str:
    """The assignments, in plain words, in the order given.

    With no assignments at all the text starts with
    the plain statement of that fact.
    """
    if assignments is None:
        selected: Tuple[WorktreeAssignment, ...] = ()
    elif isinstance(assignments, WorktreeRegistry):
        selected = assignments.list_assignments()
    elif isinstance(assignments, WorktreePlan):
        selected = assignments.assignments
    else:
        if isinstance(assignments, (str, bytes)) \
                or not isinstance(assignments, (list, tuple)):
            raise ValueError(
                "worktree assignments must be a list of assignments")
        selected = tuple(
            a if isinstance(a, WorktreeAssignment)
            else build_assignment(a) for a in assignments)
    if not selected:
        return "Worktree assignments: none. No crew member holds a tree."
    lines = [f"Worktree assignments: {len(selected)} held."]
    for assignment in selected:
        lines.append(format_assignment(assignment))
    return "\n".join(lines)


def format_merge_plan(plan: Any) -> str:
    """One plan's merge steps, in plain words, in merge order."""
    if not isinstance(plan, WorktreePlan):
        raise ValueError(f"a worktree plan is needed, got {plan!r}")
    steps = merge_plan_for(plan)
    lines = [
        f"Merge plan: {len(steps)} branches, merged in slice "
        f"order by the coordinator ({plan.coordinator}) only."]
    for step in steps:
        lines.append(
            f"  {step.order}. {step.slice_id} - {step.member}'s "
            f"branch {step.branch} (from {step.path}), merged by "
            f"{step.merger}.")
    return "\n".join(lines)


def format_worktrees_screen(assignments: Any = None) -> str:
    """The whole slice, in plain words, for /worktrees."""
    lines = ["Parallel worktrees (M-124) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_assignments(assignments))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_worktrees_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /worktrees grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    assignments; ``show <member>`` and a bare member
    id show one member's assignment; ``plan`` asks
    for the whole plan; ``merges`` asks for the
    merge plan. Anything else is a usage error
    naming the grammar. Returns ``(action,
    value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None \
        else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head == "show" and len(words) == 2:
        try:
            return ("show", normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "plan" and len(words) == 1:
        return ("plan", None)
    if head == "merges" and len(words) == 1:
        return ("merges", None)
    if head in ("show", "plan", "merges"):
        raise ValueError(USAGE)
    if len(words) == 1:
        try:
            return ("show", normalize_member_id(words[0]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
