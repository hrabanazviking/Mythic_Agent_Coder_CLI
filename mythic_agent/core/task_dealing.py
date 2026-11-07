"""Task dealing (All-Features roadmap slice M-125).

Part VI - Agents as files - continues here. The
roadmap's words: ``a plan's slices are dealt to the
crew by office fit and current load; the dealing is
visible on the board (Part VIII) and re-dealable by
the human.``

What already shipped, and what this slice adds:

* The crew itself is already data
  (``core/crew_members.py``, M-121: every member
  holds one office), the offices are formalised
  (``core/offices.py``, M-122, and
  ``core/custom_offices.py``, M-123), and the
  worktree discipline is already data
  (``core/worktrees.py``, M-124: which member writes
  in which tree, and the load a held worktree
  assignment already puts on a member). What
  nothing held is the dealing itself: given a plan
  - a list of slices, each naming the office its
  work fits - which member takes which slice, and
  why. Dealing done by feel is dealing nobody can
  check, and a plan dealt unevenly loads one member
  while another idles.
* This slice is that dealing, as a pure layer: a
  plan of tasks validated as data (slice, title,
  the office its work fits), the dealing derived
  mechanically from the plan, the shipped casting
  and the crew's current load - office fit first,
  then least load, casting order breaking ties -
  a loader for a plan file anywhere on disk, a
  re-deal that moves one slice to a named member,
  a dealing record shaped as session news, and a
  small in-memory registry model. The shipped data
  file (``mythic_agent/data/task_dealing.yaml``)
  holds one example plan - the next ten roadmap
  slices, M-125 to M-134, each naming the office
  its work fits - in exactly the shape a real
  plan's file takes. This module starts no crew,
  spawns no agent, runs no git command and imports
  no agent / UI code; the agent layer owns holding
  the dealing for a session and carrying out the
  human's re-deals.

Honesty rules, enforced here and pinned by tests:

* **The dealing is derived, never stored.** A
  dealing is computed from the plan, the members
  and the loads it is dealt under, in plan order,
  so it can never disagree with them; the same
  plan, members and loads always deal the same
  dealing (deterministic ids, deterministic
  tie-breaks).
* **Office fit first, then current load.** A task
  goes to a member holding the office the task
  names whenever one can take it; among equally
  fitting members the least loaded takes it, and
  casting order breaks the last tie. Every dealt
  assignment records the load its member holds
  after the deal, so the dealing shows its own
  arithmetic.
* **Members and offices are the shipped crew's.**
  A member id reads exactly as the M-121 layer
  reads one and an office exactly as the M-121
  layer reads a crew office - composed with by
  import, never re-read here - so ``primary`` (the
  lead session itself) can never be dealt a slice,
  and an unknown office refuses. A dealt
  assignment's office is its member's cast office,
  read from the casting, never a spelling the
  dealing invents.
* **Re-dealing is the human's, and it is explicit.**
  A re-deal moves one dealt slice to a named
  member of the crew and recomputes the loads;
  it never happens silently inside the dealing
  itself, and a slice that was never dealt, or a
  member the crew does not hold, refuses.
* **There is no Part VIII board yet.** The roadmap
  sentence names the board (Part VIII) as where a
  dealing will be visible; that board does not
  exist in this tree. The dealing is visible
  through this slice's own surfaces - the screen
  formatter both /dealing roads share - and
  nothing here claims a board exists.
* **Malformed refuses.** An unknown member or
  office, a malformed slice or title, a duplicate
  slice in one plan, a load that is not a
  non-negative count, and unknown keys in a task
  or plan mapping all raise instead of being
  skipped or guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id, normalize_office
from .validation import ValidationError
from .worktrees import normalize_slice_id

__all__ = [
    "DEALING_RESOURCE",
    "DEALING_SCHEMA",
    "DEALING_SLICE",
    "PLAIN_EXPLANATION",
    "USAGE",
    "Dealing",
    "DealingPlan",
    "DealingTask",
    "DealtAssignment",
    "TaskDealingRegistry",
    "build_assignment",
    "build_task",
    "deal_tasks",
    "dealing_record",
    "format_assignment",
    "format_assignments",
    "format_dealing_screen",
    "format_loads",
    "format_tasks",
    "load_dealing_plan",
    "load_dealing_plan_file",
    "member_loads",
    "normalize_slice_id",
    "parse_dealing_args",
    "plain_words",
    "redeal_dealing",
    "validate_assignment",
    "validate_dealing",
    "validate_plan",
    "validate_task",
]

DEALING_SLICE = "M-125"

#: The packaged data resource holding the example plan.
DEALING_RESOURCE = "task_dealing.yaml"

#: The schema word a dealing plan file must carry.
DEALING_SCHEMA = "mythic.task_dealing/1"

PLAIN_EXPLANATION = (
    "Task dealing: a plan's slices are dealt to "
    "the crew by office fit and current load - a "
    "slice goes first to a member holding the "
    "office its work fits, and among equally "
    "fitting members to the least loaded, casting "
    "order breaking ties - and every dealt slice "
    "records the load its member holds after the "
    "deal. The human may re-deal any slice to "
    "another member. There is no Part VIII board "
    "yet, so the dealing is visible on this "
    "slice's own screen, not on a board. This "
    "layer deals as data only; it starts no crew "
    "and spawns no agent itself."
)

USAGE = (
    "Usage: /dealing, /dealing show, "
    "/dealing show <member>, /dealing plan, "
    "/dealing loads"
)

_TASK_KEYS = frozenset({
    "slice", "slice_id", "office", "required_office", "title",
})

_PLAN_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "plan_note", "dealer", "tasks",
})

_TITLE_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789 -'&/().,")

#: The shipped example plan's tasks, in plan order:
#: (slice, title, required office). The shipped data
#: file is held to exactly this list by the loader's
#: example check, and the roadmap titles are the
#: roadmap's own for M-125..M-134.
_EXAMPLE_TASKS = (
    ("M-125", "Task dealing", "forge_worker"),
    ("M-126", "Crew comms", "scribe"),
    ("M-127", "Cycle and deadlock detection grown", "guardian"),
    ("M-128", "Merge discipline", "forge_worker"),
    ("M-129", "Heterogeneous crews", "polymath"),
    ("M-130", "The Auditor's veto", "auditor"),
    ("M-131", "Research swarms", "cartographer"),
    ("M-132", "Review panels", "auditor"),
    ("M-133", "Crew memory", "scribe"),
    ("M-134", "Stand-ups", "skald"),
)


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_title(value: Any) -> str:
    title = _clean_text(value, "a task's title")
    if len(title) > 120 or not all(
            ch in _TITLE_CHARS for ch in title):
        raise ValueError(
            f"a task's title must be plain words of at most "
            f"120 characters, got {value!r}")
    return title


def _check_load(value: Any, what: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) \
            or value < 0:
        raise ValueError(
            f"{what} must be a non-negative count, got {value!r}")
    return value


def _member_pair(entry: Any) -> Tuple[str, str]:
    """One crew member as (member id, cast office).

    Reads a CrewMember, any object carrying
    ``member_id`` / ``office``, or a mapping naming
    a ``member`` (or ``member_id`` / ``id``) and an
    ``office`` - the M-121 readings, by import.
    """
    if isinstance(entry, dict):
        member = None
        for key in ("member_id", "member", "id"):
            if key in entry:
                member = entry[key]
                break
        office = entry.get("office")
        if member is None or office is None:
            raise ValueError(
                f"a crew member must name a member and an "
                f"office, got {entry!r}")
        return (normalize_member_id(member),
                normalize_office(office))
    member = getattr(entry, "member_id", None)
    office = getattr(entry, "office", None)
    if member is None or office is None:
        raise ValueError(
            f"a crew member must carry a member id and an "
            f"office, got {entry!r}")
    return (normalize_member_id(member),
            normalize_office(office))


def _member_pairs(members: Any) -> Tuple[Tuple[str, str], ...]:
    if isinstance(members, (str, bytes)) \
            or not isinstance(members, (list, tuple)):
        raise ValueError(
            f"crew members must be a list of members, "
            f"got {members!r}")
    pairs = []
    seen = set()
    for entry in members:
        pair = _member_pair(entry)
        if pair[0] in seen:
            raise ValueError(
                f"the member {pair[0]!r} is named twice in "
                f"one crew; a member is dealt as one member")
        seen.add(pair[0])
        pairs.append(pair)
    return tuple(pairs)


def _check_loads(loads: Any,
                 pairs: Tuple[Tuple[str, str], ...]) -> Dict[str, int]:
    counts: Dict[str, int] = {member: 0 for member, _ in pairs}
    if loads is None:
        return counts
    if not isinstance(loads, dict):
        raise ValueError(
            f"current loads must be a mapping of member to "
            f"count, got {loads!r}")
    known = {member for member, _ in pairs}
    for member, load in loads.items():
        wanted = normalize_member_id(member)
        if wanted not in known:
            raise ValueError(
                f"a load names the member {wanted!r}, who is "
                f"not in this crew")
        counts[wanted] = _check_load(
            load, f"the load of {wanted!r}")
    return counts


# ---------------------------------------------------------------------
# The task: one slice of a plan, and the office its work fits.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class DealingTask:
    """One task of a dealing plan, as data.

    ``slice_id`` is the roadmap slice; ``title`` is
    the slice's own name; ``office`` is the crew
    office the slice's work fits - the office the
    dealing tries first. Constructing one validates
    it.
    """

    slice_id: str = ""
    title: str = ""
    office: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "slice_id", normalize_slice_id(self.slice_id))
        object.__setattr__(self, "title", _check_title(self.title))
        object.__setattr__(
            self, "office", normalize_office(self.office))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "dealing_task",
            "slice": DEALING_SLICE,
            "slice_id": self.slice_id,
            "title": self.title,
            "office": self.office,
        }


def _pick(mapping: Dict[str, Any], first: str, second: str,
          what: str) -> Any:
    """One field from its two spellings, or a refusal."""
    if first in mapping and second in mapping:
        if mapping[first] != mapping[second]:
            raise ValueError(f"a task names two different {what}")
        return mapping[first]
    if first in mapping:
        return mapping[first]
    return mapping.get(second)


def validate_task(task: Any) -> DealingTask:
    """Validate one dealing task into a DealingTask.

    Accepts a DealingTask or a mapping naming a
    ``slice_id`` (or ``slice``), a ``title`` and an
    ``office`` (or ``required_office``). Naming both
    spellings of one field with different values
    refuses, and unknown keys refuse.
    """
    if isinstance(task, DealingTask):
        return task
    if not isinstance(task, dict):
        raise ValueError(
            f"a dealing task must be a mapping, got {task!r}")
    unknown = set(task) - _TASK_KEYS
    if unknown:
        raise ValueError(
            "unknown dealing task keys: %s"
            % ", ".join(sorted(unknown)))
    slice_id = _pick(task, "slice_id", "slice", "slices")
    if slice_id is None:
        raise ValueError("a dealing task is missing its slice")
    office = _pick(task, "office", "required_office", "offices")
    if office is None:
        raise ValueError("a dealing task is missing its office")
    if "title" not in task:
        raise ValueError("a dealing task is missing its title")
    return DealingTask(
        slice_id=slice_id, title=task["title"], office=office)


def build_task(task: Any = None, **kwargs: Any) -> DealingTask:
    """Build one validated dealing task.

    From a DealingTask, from a mapping (the spellings
    :func:`validate_task` reads), or from field words
    given as keyword arguments.
    """
    if isinstance(task, DealingTask) and not kwargs:
        return task
    if isinstance(task, dict) or task is None:
        merged: Dict[str, Any] = {}
        if isinstance(task, dict):
            merged.update(task)
        merged.update(kwargs)
        return validate_task(merged)
    raise ValueError(
        f"a dealing task must be a mapping, got {task!r}")


# ---------------------------------------------------------------------
# The dealt assignment: one slice, dealt to one member.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class DealtAssignment:
    """One slice dealt to one crew member, as data.

    ``member`` is the member's M-121 member id;
    ``office`` is that member's cast office (read
    from the crew, never invented); ``slice_id`` /
    ``title`` / ``required_office`` name the task
    dealt; ``load_after`` is the load the member
    holds once this deal lands, counting the loads
    the dealing started under. Constructing one
    validates it.
    """

    assignment_id: Optional[str] = None
    member: str = ""
    office: str = ""
    slice_id: str = ""
    title: str = ""
    required_office: str = ""
    load_after: int = 0

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
        object.__setattr__(self, "title", _check_title(self.title))
        object.__setattr__(
            self, "required_office",
            normalize_office(self.required_office))
        object.__setattr__(
            self, "load_after",
            _check_load(self.load_after, "an assignment's load"))

    @property
    def fit(self) -> bool:
        """True when the member's office is the fitted office."""
        return self.office == self.required_office

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "task_dealing",
            "slice": DEALING_SLICE,
            "assignment_id": self.assignment_id,
            "member": self.member,
            "office": self.office,
            "slice_id": self.slice_id,
            "title": self.title,
            "required_office": self.required_office,
            "fit": self.fit,
            "load_after": self.load_after,
        }


_ASSIGNMENT_KEYS = frozenset({
    "id", "assignment_id", "member", "member_id", "office",
    "slice", "slice_id", "title", "required_office",
    "load_after", "load",
})


def validate_assignment(assignment: Any) -> DealtAssignment:
    """Validate one dealt assignment into a DealtAssignment.

    Accepts a DealtAssignment or a mapping naming a
    ``member`` (or ``member_id``), an ``office``, a
    ``slice_id`` (or ``slice``), a ``title``, a
    ``required_office``, a ``load_after`` (or
    ``load``) and an optional ``assignment_id`` (or
    ``id``). Naming both spellings of one field with
    different values refuses, and unknown keys
    refuse.
    """
    if isinstance(assignment, DealtAssignment):
        return assignment
    if not isinstance(assignment, dict):
        raise ValueError(
            f"a dealt assignment must be a mapping, "
            f"got {assignment!r}")
    unknown = set(assignment) - _ASSIGNMENT_KEYS
    if unknown:
        raise ValueError(
            "unknown dealt assignment keys: %s"
            % ", ".join(sorted(unknown)))
    member = _pick(assignment, "member", "member_id", "members")
    if member is None:
        raise ValueError("a dealt assignment is missing its member")
    slice_id = _pick(assignment, "slice_id", "slice", "slices")
    if slice_id is None:
        raise ValueError("a dealt assignment is missing its slice")
    load = _pick(assignment, "load_after", "load", "loads")
    if load is None:
        raise ValueError(
            "a dealt assignment is missing its load_after")
    for field in ("office", "title", "required_office"):
        if field not in assignment:
            raise ValueError(
                f"a dealt assignment is missing its {field}")
    kwargs: Dict[str, Any] = {
        "member": member,
        "office": assignment["office"],
        "slice_id": slice_id,
        "title": assignment["title"],
        "required_office": assignment["required_office"],
        "load_after": load,
    }
    assignment_id = _pick(
        assignment, "assignment_id", "id", "assignment ids")
    if assignment_id is not None:
        kwargs["assignment_id"] = assignment_id
    return DealtAssignment(**kwargs)


def build_assignment(assignment: Any = None,
                     **kwargs: Any) -> DealtAssignment:
    """Build one validated dealt assignment.

    From a DealtAssignment, from a mapping (the
    spellings :func:`validate_assignment` reads), or
    from field words given as keyword arguments.
    """
    if isinstance(assignment, DealtAssignment) and not kwargs:
        return assignment
    if isinstance(assignment, dict) or assignment is None:
        merged: Dict[str, Any] = {}
        if isinstance(assignment, dict):
            merged.update(assignment)
        merged.update(kwargs)
        return validate_assignment(merged)
    raise ValueError(
        f"a dealt assignment must be a mapping, "
        f"got {assignment!r}")


# ---------------------------------------------------------------------
# The plan: the tasks one file deals, under one dealer.
# ---------------------------------------------------------------------


def _check_task_collisions(tasks: Tuple[DealingTask, ...]) -> None:
    seen = set()
    for task in tasks:
        if task.slice_id in seen:
            raise ValueError(
                f"the slice {task.slice_id!r} is tasked twice "
                f"in one plan; one slice, one task")
        seen.add(task.slice_id)


@dataclass(frozen=True)
class DealingPlan:
    """A whole plan: the tasks one file deals, in file order.

    ``dealer`` is the member id of the one who deals
    - in the shipped example the house coordinator
    word. Constructing one holds the plan law: at
    least one task, and no slice tasked twice.
    """

    tasks: Tuple[DealingTask, ...] = ()
    dealer: str = ""
    plan_note: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.tasks, (str, bytes)) \
                or not isinstance(self.tasks, (list, tuple)):
            raise ValueError(
                f"a plan's tasks must be a list of tasks, "
                f"got {self.tasks!r}")
        tasks = tuple(
            t if isinstance(t, DealingTask) else validate_task(t)
            for t in self.tasks)
        if not tasks:
            raise ValueError("a plan must hold at least one task")
        _check_task_collisions(tasks)
        object.__setattr__(self, "tasks", tasks)
        object.__setattr__(
            self, "dealer", normalize_member_id(self.dealer))
        object.__setattr__(
            self, "plan_note", str(self.plan_note or ""))

    def get(self, slice_id: Any) -> DealingTask:
        """The task one slice names; untasked raises KeyError."""
        wanted = normalize_slice_id(slice_id)
        for task in self.tasks:
            if task.slice_id == wanted:
                return task
        raise KeyError(f"no task holds the slice: {wanted!r}")


# ---------------------------------------------------------------------
# The dealing: derived from a plan, a crew and its current load.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class Dealing:
    """One dealing of a plan, as data: assignments + undealt.

    ``assignments`` are the dealt slices, in plan
    order; ``undealt`` are the tasks no member could
    take (only possible when the crew is empty - a
    task is never silently dropped); ``base_loads``
    are the loads the dealing started under, as
    (member, load) pairs, kept so a re-deal can
    recompute the same arithmetic.
    """

    assignments: Tuple[DealtAssignment, ...] = ()
    undealt: Tuple[DealingTask, ...] = ()
    base_loads: Tuple[Tuple[str, int], ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.assignments, (str, bytes)) \
                or not isinstance(self.assignments, (list, tuple)):
            raise ValueError(
                f"a dealing's assignments must be a list, "
                f"got {self.assignments!r}")
        assignments = tuple(
            a if isinstance(a, DealtAssignment)
            else validate_assignment(a) for a in self.assignments)
        seen = set()
        for assignment in assignments:
            if assignment.slice_id in seen:
                raise ValueError(
                    f"the slice {assignment.slice_id!r} is dealt "
                    f"twice in one dealing; one slice, one member")
            seen.add(assignment.slice_id)
        if isinstance(self.undealt, (str, bytes)) \
                or not isinstance(self.undealt, (list, tuple)):
            raise ValueError(
                f"a dealing's undealt tasks must be a list, "
                f"got {self.undealt!r}")
        undealt = tuple(
            t if isinstance(t, DealingTask) else validate_task(t)
            for t in self.undealt)
        for task in undealt:
            if task.slice_id in seen:
                raise ValueError(
                    f"the slice {task.slice_id!r} is both dealt "
                    f"and undealt in one dealing")
        base = []
        for pair in self.base_loads:
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                raise ValueError(
                    f"a dealing's base loads must be (member, "
                    f"load) pairs, got {pair!r}")
            base.append((
                normalize_member_id(pair[0]),
                _check_load(pair[1], "a base load")))
        object.__setattr__(self, "assignments", assignments)
        object.__setattr__(self, "undealt", undealt)
        object.__setattr__(self, "base_loads", tuple(base))

    def get(self, slice_id: Any) -> DealtAssignment:
        """The assignment one slice holds; undealt raises."""
        wanted = normalize_slice_id(slice_id)
        for assignment in self.assignments:
            if assignment.slice_id == wanted:
                return assignment
        raise KeyError(f"no assignment holds the slice: {wanted!r}")

    def loads(self) -> Dict[str, int]:
        """Each dealt member's load after the dealing."""
        counts: Dict[str, int] = {}
        for assignment in self.assignments:
            counts[assignment.member] = assignment.load_after
        return counts


def deal_tasks(tasks: Any, members: Any,
               loads: Any = None) -> Dealing:
    """Deal *tasks* to *members* by office fit and current load.

    The mechanical judge of this layer, as data
    only: tasks are taken in the order given; each
    goes to the member ranked first by office fit
    (a member holding the task's office before one
    who does not), then by current load (the loads
    given, grown by every deal made here), then by
    crew order. Each assignment records the load its
    member holds after the deal. With an empty crew
    every task is undealt - named, never dropped.
    """
    if isinstance(tasks, DealingPlan):
        task_tuple = tasks.tasks
    elif isinstance(tasks, (str, bytes)) \
            or not isinstance(tasks, (list, tuple)):
        raise ValueError(
            f"dealing tasks must be a list of tasks, "
            f"got {tasks!r}")
    else:
        task_tuple = tuple(
            t if isinstance(t, DealingTask) else validate_task(t)
            for t in tasks)
    _check_task_collisions(task_tuple)
    pairs = _member_pairs(members)
    counts = _check_loads(loads, pairs)
    base_loads = tuple(
        (member, counts[member]) for member, _ in pairs
        if counts[member])
    assignments = []
    undealt = []
    for task in task_tuple:
        if not pairs:
            undealt.append(task)
            continue
        ranked = sorted(
            range(len(pairs)),
            key=lambda index: (
                0 if pairs[index][1] == task.office else 1,
                counts[pairs[index][0]],
                index))
        member, office = pairs[ranked[0]]
        counts[member] += 1
        assignments.append(DealtAssignment(
            member=member, office=office, slice_id=task.slice_id,
            title=task.title, required_office=task.office,
            load_after=counts[member]))
    return Dealing(
        assignments=tuple(assignments), undealt=tuple(undealt),
        base_loads=base_loads)


def redeal_dealing(dealing: Any, slice_id: Any, member: Any,
                   members: Any) -> Dealing:
    """A new dealing with one slice re-dealt to *member*.

    The human's re-deal, as data: the named slice
    moves to the named member of the crew (whose
    cast office the new assignment carries), and
    every load is recomputed from the dealing's
    base loads in assignment order. A slice that
    was never dealt, and a member the crew does not
    hold, refuse.
    """
    if not isinstance(dealing, Dealing):
        raise ValueError(f"a dealing is needed, got {dealing!r}")
    pairs = _member_pairs(members)
    by_member = dict(pairs)
    wanted_member = normalize_member_id(member)
    if wanted_member not in by_member:
        raise ValueError(
            f"the member {wanted_member!r} is not in this "
            f"crew; a slice is re-dealt to a crew member")
    current = dealing.get(slice_id)
    counts = {name: 0 for name, _ in pairs}
    for name, load in dealing.base_loads:
        if name in counts:
            counts[name] = load
    moved = []
    for assignment in dealing.assignments:
        if assignment.slice_id == current.slice_id:
            assignment = replace(
                assignment, member=wanted_member,
                office=by_member[wanted_member])
        counts[assignment.member] += 1
        moved.append(replace(
            assignment, load_after=counts[assignment.member]))
    return Dealing(
        assignments=tuple(moved), undealt=dealing.undealt,
        base_loads=dealing.base_loads)


def member_loads(members: Any, assignments: Any = None,
                 loads: Any = None) -> Dict[str, int]:
    """Every member's current load, in crew order.

    Starts from *loads* (the loads already held -
    for example one per worktree assignment a
    member holds under M-124) and adds one per
    dealt assignment in *assignments*. Members with
    no load read 0: the count is the whole crew's,
    never only the busy.
    """
    pairs = _member_pairs(members)
    counts = _check_loads(loads, pairs)
    if assignments is None:
        held: Tuple[DealtAssignment, ...] = ()
    elif isinstance(assignments, Dealing):
        held = assignments.assignments
    elif isinstance(assignments, TaskDealingRegistry):
        held = assignments.list_assignments()
    else:
        if isinstance(assignments, (str, bytes)) \
                or not isinstance(assignments, (list, tuple)):
            raise ValueError(
                "dealt assignments must be a list of assignments")
        held = tuple(
            a if isinstance(a, DealtAssignment)
            else build_assignment(a) for a in assignments)
    known = {member for member, _ in pairs}
    for assignment in held:
        if assignment.member not in known:
            raise ValueError(
                f"an assignment names the member "
                f"{assignment.member!r}, who is not in this crew")
        counts[assignment.member] += 1
    return counts


def validate_dealing(plan: Any, dealing: Any,
                     members: Any) -> list:
    """Every problem in a claimed dealing of *plan*, as strings.

    An empty list means the dealing answers the
    plan exactly: every task dealt exactly once or
    named undealt, every assignment to a member of
    the crew carrying that member's cast office -
    an assignment naming another office for its
    member is the composed-vocabulary refusal.
    """
    if not isinstance(plan, DealingPlan):
        return [f"a dealing plan is needed, got {plan!r}"]
    if not isinstance(dealing, Dealing):
        return [f"a dealing is needed, got {dealing!r}"]
    try:
        pairs = _member_pairs(members)
    except ValueError as exc:
        return [str(exc)]
    by_member = dict(pairs)
    problems = []
    dealt = {a.slice_id for a in dealing.assignments}
    undealt = {t.slice_id for t in dealing.undealt}
    for task in plan.tasks:
        if task.slice_id not in dealt | undealt:
            problems.append(
                f"the task {task.slice_id!r} is neither dealt "
                f"nor named undealt")
    for assignment in dealing.assignments:
        if assignment.member not in by_member:
            problems.append(
                f"the assignment for {assignment.slice_id!r} "
                f"names the member {assignment.member!r}, who "
                f"is not in this crew")
        elif assignment.office != by_member[assignment.member]:
            problems.append(
                f"the assignment for {assignment.slice_id!r} "
                f"gives {assignment.member!r} the office "
                f"{assignment.office!r}, not its cast office "
                f"{by_member[assignment.member]!r}")
        try:
            task = plan.get(assignment.slice_id)
        except KeyError:
            problems.append(
                f"the assignment for {assignment.slice_id!r} "
                f"deals a slice the plan does not task")
        else:
            if assignment.required_office != task.office \
                    or assignment.title != task.title:
                problems.append(
                    f"the assignment for {assignment.slice_id!r} "
                    f"does not carry the plan's task for that "
                    f"slice")
    return problems


def validate_plan(data: Any, *,
                  require_example: bool = False) -> list:
    """Every problem in a dealing plan mapping, as plain strings.

    An empty list means the plan is well-formed.
    With ``require_example`` the plan must be
    exactly the shipped example: the ten tasks
    M-125..M-134 in plan order, with the roadmap's
    titles and the offices named for them, dealt by
    the house coordinator - and the dealing derived
    from it against the shipped M-121 casting must
    deal every task to its fitted office (the check
    the shipped file is held to; a real plan's file
    is read without it).
    """
    if not isinstance(data, dict):
        return [f"a dealing plan must be a mapping, got {data!r}"]
    problems = []
    unknown = set(data) - _PLAN_KEYS
    if unknown:
        problems.append(
            "unknown dealing plan keys: %s"
            % ", ".join(sorted(unknown)))
    if data.get("schema") != DEALING_SCHEMA:
        problems.append(
            f"a dealing plan's schema must be "
            f"{DEALING_SCHEMA!r}, got {data.get('schema')!r}")
    if data.get("slice") != DEALING_SLICE:
        problems.append(
            f"a dealing plan's slice must be "
            f"{DEALING_SLICE!r}, got {data.get('slice')!r}")
    dealer = None
    if data.get("dealer") is None:
        problems.append("a dealing plan is missing its dealer")
    else:
        try:
            dealer = normalize_member_id(data["dealer"])
        except ValueError as exc:
            problems.append(f"dealer: {exc}")
    raw = data.get("tasks")
    if not isinstance(raw, list) or not raw:
        problems.append(
            "a dealing plan must hold a non-empty tasks list")
        return problems
    parsed = []
    for index, entry in enumerate(raw):
        try:
            parsed.append(validate_task(entry))
        except ValueError as exc:
            problems.append(f"task {index + 1}: {exc}")
    if len(parsed) == len(raw):
        try:
            _check_task_collisions(tuple(parsed))
        except ValueError as exc:
            problems.append(str(exc))
    if require_example and len(parsed) == len(raw):
        held = tuple(
            (t.slice_id, t.title, t.office) for t in parsed)
        if held != _EXAMPLE_TASKS:
            problems.append(
                "the shipped example plan must hold exactly "
                "the ten tasks M-125..M-134 in plan order, "
                "with their roadmap titles and fitted offices")
        if dealer is not None and dealer != "coordinator":
            problems.append(
                "the shipped example plan is dealt by the "
                "coordinator")
        if held == _EXAMPLE_TASKS:
            from .crew_members import load_casting
            casting = load_casting()
            dealing = deal_tasks(tuple(parsed), casting.members)
            if dealing.undealt:
                problems.append(
                    "the shipped example dealing leaves a task "
                    "undealt against the shipped casting")
            for assignment in dealing.assignments:
                if not assignment.fit:
                    problems.append(
                        f"the shipped example dealing deals "
                        f"{assignment.slice_id!r} off its fitted "
                        f"office")
    return problems


def _plan_from(data: Any, *, require_example: bool) -> DealingPlan:
    problems = validate_plan(data, require_example=require_example)
    if problems:
        raise ValidationError(
            "invalid dealing plan: " + "; ".join(problems))
    assert isinstance(data, dict)
    return DealingPlan(
        tasks=tuple(validate_task(entry) for entry in data["tasks"]),
        dealer=data["dealer"],
        plan_note=str(data.get("plan_note") or ""))


def load_dealing_plan(
        data: Optional[Dict[str, Any]] = None) -> DealingPlan:
    """Load and validate the shipped example plan (or *data*).

    The shipped file is held to the example check:
    exactly the ten tasks M-125..M-134, dealt by the
    coordinator, every one dealing to its fitted
    office against the shipped casting. Raises
    :class:`ValidationError` listing every problem
    when the record is not a well-formed plan.
    """
    raw = data if data is not None else load_resource(DEALING_RESOURCE)
    return _plan_from(raw, require_example=True)


def load_dealing_plan_file(path: Any) -> DealingPlan:
    """Load and validate a dealing plan from a file at *path*.

    This is the road a real plan arrives by: any
    file in the plan shape, anywhere on disk,
    validated whole - a malformed file raises
    :class:`ValidationError` naming the problem,
    and a missing file raises ``FileNotFoundError``.
    The example check is not held: a plan may task
    a single slice.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _plan_from(raw, require_example=False)


# ---------------------------------------------------------------------
# Dealing news, shaped as a session record.
# ---------------------------------------------------------------------


def dealing_record(assignment: Any) -> Dict[str, Any]:
    """The session-news record of one dealt assignment.

    Carries the assignment's whole record plus a
    one-line plain headline, so a slice dealt to a
    member in a session is news with its shape
    attached, never a bare log line.
    """
    current = assignment if isinstance(assignment, DealtAssignment) \
        else build_assignment(assignment)
    record = current.to_record()
    record["news"] = True
    record["headline"] = plain_words(current)
    return record


def plain_words(assignment: Any) -> str:
    """One dealt assignment, in one plain sentence."""
    current = assignment if isinstance(assignment, DealtAssignment) \
        else build_assignment(assignment)
    office_title = current.office.replace("_", " ")
    if current.fit:
        fit_words = "an office fit"
    else:
        fit_words = (
            f"off the fitted office "
            f"({current.required_office.replace('_', ' ')})")
    return (
        f"{current.slice_id} ({current.title}) is dealt to "
        f"{current.member} ({office_title}) - {fit_words}; "
        f"load {current.load_after} after this deal.")


# ---------------------------------------------------------------------
# The registry model: dealt assignments held in registration order,
# ids deterministic.
# ---------------------------------------------------------------------


class TaskDealingRegistry:
    """An in-memory registry of dealt assignments.

    Assignments are held in registration order. Ids
    are deterministic: a caller-supplied id is used
    as given, and an unsupplied id is the next
    ``dealing-N`` in sequence, skipping any number a
    supplied id already took. One slice is dealt
    once in a registry: a slice already held
    refuses, and is moved only by an explicit
    re-deal. Loads are counted from what the
    registry holds, in registration order. Storage
    beyond memory (a session's journal, a file) is
    the agent layer's concern; this model is
    neutral.
    """

    def __init__(self) -> None:
        self._assignments: Dict[str, DealtAssignment] = {}
        self._next = 1

    def _fresh_id(self) -> str:
        while f"dealing-{self._next}" in self._assignments:
            self._next += 1
        assignment_id = f"dealing-{self._next}"
        self._next += 1
        return assignment_id

    def register(self, assignment: Any) -> DealtAssignment:
        """Register one dealt assignment and hold it."""
        validated = build_assignment(assignment)
        if validated.assignment_id is not None \
                and validated.assignment_id in self._assignments:
            raise ValueError(
                f"a dealt assignment named "
                f"{validated.assignment_id!r} already exists")
        for held in self._assignments.values():
            if held.slice_id == validated.slice_id:
                raise ValueError(
                    f"the slice {validated.slice_id!r} is "
                    f"already dealt in this registry; re-deal "
                    f"it explicitly to move it")
        if validated.assignment_id is None:
            validated = replace(
                validated, assignment_id=self._fresh_id())
        self._assignments[validated.assignment_id] = validated
        return validated

    def register_dealing(self, dealing: Any
                         ) -> Tuple[DealtAssignment, ...]:
        """Register every assignment of one dealing, in order."""
        if not isinstance(dealing, Dealing):
            raise ValueError(f"a dealing is needed, got {dealing!r}")
        return tuple(self.register(a) for a in dealing.assignments)

    def get(self, assignment_id: Any) -> DealtAssignment:
        """The assignment one id names; an unknown id raises."""
        wanted = normalize_member_id(assignment_id)
        if wanted not in self._assignments:
            raise KeyError(f"unknown dealt assignment: {wanted!r}")
        return self._assignments[wanted]

    def by_slice(self, slice_id: Any) -> DealtAssignment:
        """The assignment one slice holds; undealt raises."""
        wanted = normalize_slice_id(slice_id)
        for held in self._assignments.values():
            if held.slice_id == wanted:
                return held
        raise KeyError(f"no assignment holds the slice: {wanted!r}")

    def by_member(self, member: Any) -> Tuple[DealtAssignment, ...]:
        """Every assignment one member holds, in order held."""
        wanted = normalize_member_id(member)
        return tuple(
            a for a in self._assignments.values()
            if a.member == wanted)

    def list_assignments(self) -> Tuple[DealtAssignment, ...]:
        """Every held assignment, in registration order."""
        return tuple(self._assignments.values())

    def loads(self) -> Dict[str, int]:
        """Each held member's dealt count, in order first dealt."""
        counts: Dict[str, int] = {}
        for held in self._assignments.values():
            counts[held.member] = counts.get(held.member, 0) + 1
        return counts

    def redeal(self, slice_id: Any, member: Any,
               office: Any) -> DealtAssignment:
        """Move one held slice to a named member, loads recomputed.

        The registry's own re-deal: the slice's
        assignment is replaced in place (same id,
        same position) carrying the new member and
        that member's cast office as named by the
        caller - the caller reads the office from
        the crew; this model holds no casting - and
        every held assignment's load is recomputed
        in registration order from no base load. A
        slice the registry does not hold refuses.
        """
        current = self.by_slice(slice_id)
        wanted_member = normalize_member_id(member)
        wanted_office = normalize_office(office)
        counts: Dict[str, int] = {}
        for key, held in list(self._assignments.items()):
            if held.assignment_id == current.assignment_id:
                held = replace(
                    held, member=wanted_member,
                    office=wanted_office)
            counts[held.member] = counts.get(held.member, 0) + 1
            held = replace(held, load_after=counts[held.member])
            self._assignments[key] = held
        return self.by_slice(slice_id)


# ---------------------------------------------------------------------
# The /dealing surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def format_assignment(assignment: Any) -> str:
    """One dealt assignment, in plain words."""
    current = assignment if isinstance(assignment, DealtAssignment) \
        else build_assignment(assignment)
    name = current.assignment_id or current.slice_id
    return f"  {name}: {plain_words(current)}"


def _selected_assignments(source: Any
                          ) -> Tuple[DealtAssignment, ...]:
    if source is None:
        return ()
    if isinstance(source, TaskDealingRegistry):
        return source.list_assignments()
    if isinstance(source, Dealing):
        return source.assignments
    if isinstance(source, (str, bytes)) \
            or not isinstance(source, (list, tuple)):
        raise ValueError(
            "dealt assignments must be a list of assignments")
    return tuple(
        a if isinstance(a, DealtAssignment) else build_assignment(a)
        for a in source)


def format_assignments(assignments: Any = None) -> str:
    """The dealt assignments, in plain words, in the order given.

    Accepts a list of assignments, a Dealing, or a
    TaskDealingRegistry. With no assignments at all
    the text starts with the plain statement of
    that fact.
    """
    selected = _selected_assignments(assignments)
    if not selected:
        return "Dealt assignments: none. No slice is dealt."
    lines = [f"Dealt assignments: {len(selected)} dealt."]
    for assignment in selected:
        lines.append(format_assignment(assignment))
    return "\n".join(lines)


def format_loads(loads: Any = None) -> str:
    """The crew's loads, in plain words.

    Accepts a member-to-count mapping, a Dealing, a
    TaskDealingRegistry, or a list of assignments
    (counted). With nothing held the text says so
    plainly.
    """
    if loads is None:
        counts: Dict[str, int] = {}
    elif isinstance(loads, dict):
        counts = {}
        for member, load in loads.items():
            counts[normalize_member_id(member)] = _check_load(
                load, "a member's load")
    elif isinstance(loads, Dealing):
        counts = {}
        for assignment in loads.assignments:
            counts[assignment.member] = assignment.load_after
    else:
        counts = {}
        for assignment in _selected_assignments(loads):
            counts[assignment.member] = \
                counts.get(assignment.member, 0) + 1
    if not counts:
        return "Crew load: none. No member holds a dealt slice."
    lines = ["Crew load: %s." % ", ".join(
        f"{member} {counts[member]}" for member in counts)]
    return "\n".join(lines)


def format_tasks(plan: Any) -> str:
    """One plan's tasks, in plain words, in plan order.

    Accepts a DealingPlan or a list of tasks.
    """
    if isinstance(plan, DealingPlan):
        tasks = plan.tasks
    elif isinstance(plan, (str, bytes)) \
            or not isinstance(plan, (list, tuple)):
        raise ValueError(
            f"a dealing plan is needed, got {plan!r}")
    else:
        tasks = tuple(
            t if isinstance(t, DealingTask) else validate_task(t)
            for t in plan)
    if not tasks:
        return "Dealing plan: no tasks."
    lines = [f"Dealing plan: {len(tasks)} tasks."]
    for task in tasks:
        lines.append(
            f"  {task.slice_id}: {task.title} - fits "
            f"{task.office.replace('_', ' ')}.")
    return "\n".join(lines)


def format_dealing_screen(assignments: Any = None) -> str:
    """The whole slice, in plain words, for /dealing.

    With nothing named, the shipped example plan's
    dealing against the shipped casting is shown -
    the example this slice ships - so the screen is
    never empty. There is no Part VIII board yet;
    this screen is where the dealing is visible.
    """
    if assignments is None:
        from .crew_members import load_casting
        shown: Any = deal_tasks(
            load_dealing_plan(), load_casting().members)
    else:
        shown = assignments
    lines = ["Task dealing (M-125) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_assignments(shown))
    lines.append("")
    lines.append(format_loads(shown))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_dealing_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /dealing grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    dealt assignments; ``show <member>`` and a bare
    member id show one member's assignments;
    ``plan`` asks for the plan's tasks; ``loads``
    asks for the crew's loads. Anything else is a
    usage error naming the grammar. Returns
    ``(action, value-or-None)``.
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
    if head == "loads" and len(words) == 1:
        return ("loads", None)
    if head in ("show", "plan", "loads"):
        raise ValueError(USAGE)
    if len(words) == 1:
        try:
            return ("show", normalize_member_id(words[0]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
