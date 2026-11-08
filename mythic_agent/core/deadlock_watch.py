"""Cycle and deadlock detection (All-Features slice M-127).

Part VI - Agents as files - continues here. The
roadmap's words: ``delegation cycles, merge
conflicts between members, and duplicated work are
caught by the coordinator, not by the human.``

What already shipped, and what this slice adds:

* The crew itself is already data
  (``core/crew_members.py``, M-121: every member
  holds one office), the offices are formalised
  (``core/offices.py``, M-122, and
  ``core/custom_offices.py``, M-123), the worktree
  discipline is already data (``core/worktrees.py``,
  M-124), the dealing of a plan's slices to the crew
  is already data (``core/task_dealing.py``, M-125),
  and the traffic between members is already data
  (``core/crew_comms.py``, M-126). What nothing held
  is the coordinator's watch over that crew: who
  delegated work to whom, and who holds which slice
  at which path - the evidence from which the three
  hazards that stall a crew can be seen at all.
  Today a delegation that loops back on itself, two
  members writing the same path, and one slice dealt
  to two members are found by the human, late, or
  not found at all.
* This slice is that watch, as a pure layer: the
  evidence validated as data (a delegation - a
  delegator member, a delegatee member, the slice
  delegated - and a claim - a member, the slice it
  holds, the path it holds it at), the shipped data
  file (``mythic_agent/data/deadlock_watch.yaml``)
  holding one example watch in exactly the shape a
  real watch's file takes, a loader for a watch file
  anywhere on disk, the findings derived
  mechanically from the evidence alone, a finding
  record and a report record shaped as session
  news, and a small in-memory registry model. This
  module spawns no agent, stops no member, runs no
  git command and imports no agent / UI code; the
  agent layer owns holding the watch for a session
  and handing the findings to the coordinator.

Honesty rules, enforced here and pinned by tests:

* **Findings are derived, never stored.** A report
  is computed from the delegations and claims it is
  judged under, in a fixed order, so it can never
  disagree with them; the same evidence always
  yields the same findings (deterministic order,
  deterministic wording).
* **The hazards are the roadmap's three.** A
  finding is a ``delegation_cycle`` (a chain of
  delegations that loops back to its start - each
  member in the cycle waits on the next, so none of
  the cycle's work can finish: a deadlock), a
  ``merge_conflict`` (two different members holding
  the same path, whose work will meet as a merge
  conflict) or ``duplicated_work`` (two different
  members holding the same slice, the same work
  dealt twice) - no other kind is read, and an
  unknown kind refuses.
* **The evidence is allowed to be hazardous.**
  Validation checks the shape of a delegation or a
  claim, never its wisdom: a self-delegation, a
  cycle, a shared path and a shared slice are all
  well-formed evidence, because catching them is
  the detector's whole job. One member holding its
  own slice at two paths, or the same path on two
  of its own slices, is that member's own work and
  is never flagged: every hazard needs two
  different members.
* **Members, slices and paths are the shipped
  layers'.** A member id reads exactly as the M-121
  layer reads one, a slice id exactly as the M-124
  layer reads one, and a claim path exactly as the
  M-124 layer reads a worktree path - composed with
  by import, never re-read here.
* **Detection is data only; the coordinator acts.**
  No live crew is spawned or stopped by this slice
  and no git is executed: a finding here is a
  validated record derived from given evidence, not
  an action taken, and the coordinator acts on the
  findings through later roads. The roadmap names
  the board (Part VIII) as where crew state will be
  visible; that board does not exist yet, so the
  findings are visible through this slice's own
  /deadlock screen, and nothing here claims a board
  exists.
* **Malformed refuses.** An unknown kind, a
  malformed member, slice or path, and unknown keys
  in a delegation, a claim or a watch mapping all
  raise instead of being skipped or guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .validation import ValidationError
from .worktrees import normalize_slice_id, normalize_worktree_path

__all__ = [
    "FINDING_KINDS",
    "PLAIN_EXPLANATION",
    "USAGE",
    "WATCH_RESOURCE",
    "WATCH_SCHEMA",
    "WATCH_SLICE",
    "Claim",
    "DeadlockWatch",
    "DeadlockWatchRegistry",
    "Delegation",
    "Finding",
    "WatchReport",
    "build_claim",
    "build_delegation",
    "build_finding",
    "claim_record",
    "delegation_record",
    "detect_findings",
    "finding_record",
    "format_deadlock_screen",
    "format_finding",
    "format_findings",
    "format_kinds",
    "load_deadlock_watch",
    "load_deadlock_watch_file",
    "normalize_finding_kind",
    "normalize_slice_id",
    "parse_deadlock_args",
    "plain_words",
    "report_plain_words",
    "report_record",
    "validate_claim",
    "validate_delegation",
    "validate_finding",
    "validate_report",
    "validate_watch",
]

WATCH_SLICE = "M-127"

#: The packaged data resource holding the example watch.
WATCH_RESOURCE = "deadlock_watch.yaml"

#: The schema word a watch file must carry.
WATCH_SCHEMA = "mythic.deadlock_watch/1"

#: The finding kinds, in roadmap order: the cycle,
#: the conflict, the duplication.
FINDING_KINDS = (
    "delegation_cycle", "merge_conflict", "duplicated_work")

_KIND_READINGS = {
    "cycle": "delegation_cycle",
    "cycles": "delegation_cycle",
    "delegation_cycle": "delegation_cycle",
    "delegation_cycles": "delegation_cycle",
    "deadlock": "delegation_cycle",
    "deadlocks": "delegation_cycle",
    "conflict": "merge_conflict",
    "conflicts": "merge_conflict",
    "merge_conflict": "merge_conflict",
    "merge_conflicts": "merge_conflict",
    "duplicate": "duplicated_work",
    "duplicates": "duplicated_work",
    "duplicated": "duplicated_work",
    "duplicated_work": "duplicated_work",
}

PLAIN_EXPLANATION = (
    "Cycle and deadlock watch: the coordinator's "
    "evidence - who delegates work on which slice to "
    "whom, and who holds which slice at which path - "
    "is checked mechanically for the three hazards "
    "that stall a crew: a delegation cycle (members "
    "waiting on each other, a deadlock), a merge "
    "conflict (two members holding the same path), "
    "and duplicated work (two members holding the "
    "same slice). Every finding is derived from the "
    "evidence alone and is caught by the "
    "coordinator, not by the human. There is no Part "
    "VIII board yet, so the findings are visible on "
    "this slice's own screen, not on a board. This "
    "layer holds the watch as data only; it spawns "
    "no crew, stops no member and runs no git "
    "itself - the coordinator acts on the findings "
    "through later roads."
)

USAGE = (
    "Usage: /deadlock, /deadlock show, "
    "/deadlock show <member>, /deadlock kinds"
)

_DELEGATION_KEYS = frozenset({
    "id", "delegation_id", "delegator", "from_member",
    "delegatee", "to_member", "slice", "slice_id",
})

_CLAIM_KEYS = frozenset({
    "id", "claim_id", "member", "member_id",
    "slice", "slice_id", "path", "worktree_path",
})

_FINDING_KEYS = frozenset({
    "kind", "finding_kind", "members", "slice_ids",
    "slices", "paths", "title", "detail",
})

_WATCH_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "watch_note", "keeper", "delegations", "claims",
})

#: The shipped example watch's delegations, in file
#: order: (delegator, delegatee, slice). The shipped
#: data file is held to exactly this list by the
#: loader's example check. The first three loop -
#: cartographer to architect to forge_worker and
#: back to cartographer - and the last two are a
#: clean chain that is never flagged.
_EXAMPLE_DELEGATIONS = (
    ("cartographer", "architect", "M-127"),
    ("architect", "forge_worker", "M-127"),
    ("forge_worker", "cartographer", "M-127"),
    ("scribe", "auditor", "M-128"),
    ("auditor", "guardian", "M-128"),
)

#: The shipped example watch's claims, in file
#: order: (member, slice, path). Held to exactly
#: this list beside the delegations: engine.py is
#: held by two members on two slices (one merge
#: conflict), M-131 is held by two members at two
#: paths (one duplicated work), and the guardian's
#: claim is clean.
_EXAMPLE_CLAIMS = (
    ("forge_worker", "M-129", "mythic_agent/core/engine.py"),
    ("auditor", "M-130", "mythic_agent/core/engine.py"),
    ("scribe", "M-131", "mythic_agent/core/keeper.py"),
    ("skald", "M-131", "mythic_agent/core/metrics.py"),
    ("guardian", "M-127", "mythic_agent/core/deadlock_watch.py"),
)


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_title(value: Any) -> str:
    title = _clean_text(value, "a finding's title")
    if len(title) > 200 or "\x00" in title:
        raise ValueError(
            f"a finding's title must be plain text of at most "
            f"200 characters, got {len(title)} characters")
    return title


def _check_detail(value: Any) -> str:
    detail = _clean_text(value, "a finding's detail")
    if len(detail) > 2000 or "\x00" in detail:
        raise ValueError(
            f"a finding's detail must be plain text of at most "
            f"2000 characters, got {len(detail)} characters")
    return detail


def _check_members(value: Any) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes)) \
            or not isinstance(value, (list, tuple)):
        raise ValueError(
            f"a finding's members must be a list of member "
            f"ids, got {value!r}")
    members = tuple(normalize_member_id(m) for m in value)
    if not members:
        raise ValueError("a finding must name at least one member")
    if len(set(members)) != len(members):
        raise ValueError(
            "a finding names a member twice: %s"
            % ", ".join(sorted(
                m for m in set(members) if members.count(m) > 1)))
    return members


def _check_slices(value: Any) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes)) \
            or not isinstance(value, (list, tuple)):
        raise ValueError(
            f"a finding's slices must be a list of slice "
            f"ids, got {value!r}")
    return tuple(sorted({
        normalize_slice_id(s) for s in value}))


def _check_paths(value: Any) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes)) \
            or not isinstance(value, (list, tuple)):
        raise ValueError(
            f"a finding's paths must be a list of paths, "
            f"got {value!r}")
    return tuple(sorted({
        normalize_worktree_path(p) for p in value}))


def _member_words(members: Tuple[str, ...]) -> str:
    """Member ids as a plain list: ``a, b and c``."""
    if len(members) == 1:
        return members[0]
    if len(members) == 2:
        return f"{members[0]} and {members[1]}"
    return ", ".join(members[:-1]) + f" and {members[-1]}"


def normalize_finding_kind(value: Any) -> str:
    """The canonical finding kind a word names.

    Kind words read case-insensitively, with dashes
    read as underscores; the plain words ``cycle``
    and ``deadlock`` read as the cycle kind, and the
    short spellings of the other two kinds read as
    the one canonical kind. Anything else raises.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted in _KIND_READINGS:
            return _KIND_READINGS[wanted]
    raise ValueError(
        "a finding kind must be one of %s, got %r"
        % ("/".join(FINDING_KINDS), value))


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
# The delegation: one hand-off of work, as evidence.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class Delegation:
    """One delegation of work between members, as data.

    ``delegator`` is the member handing the work on;
    ``delegatee`` is the member receiving it;
    ``slice_id`` is the slice the delegated work
    belongs to. Constructing one validates its shape
    only: a delegation to oneself, or one closing a
    cycle, is well-formed evidence - catching it is
    the detector's job, not the validator's.
    """

    delegation_id: Optional[str] = None
    delegator: str = ""
    delegatee: str = ""
    slice_id: str = ""

    def __post_init__(self) -> None:
        if self.delegation_id is not None:
            object.__setattr__(
                self, "delegation_id",
                normalize_member_id(self.delegation_id))
        object.__setattr__(
            self, "delegator", normalize_member_id(self.delegator))
        object.__setattr__(
            self, "delegatee", normalize_member_id(self.delegatee))
        object.__setattr__(
            self, "slice_id", normalize_slice_id(self.slice_id))

    @property
    def is_self_delegation(self) -> bool:
        """True when a member delegates to itself."""
        return self.delegator == self.delegatee

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "crew_delegation",
            "slice": WATCH_SLICE,
            "delegation_id": self.delegation_id,
            "delegator": self.delegator,
            "delegatee": self.delegatee,
            "slice_id": self.slice_id,
        }


def validate_delegation(delegation: Any) -> Delegation:
    """Validate one delegation into a Delegation.

    Accepts a Delegation or a mapping naming a
    ``delegator`` (or ``from_member``), a
    ``delegatee`` (or ``to_member``), a ``slice_id``
    (or ``slice``) and an optional ``delegation_id``
    (or ``id``). Naming both spellings of one field
    with different values refuses, and unknown keys
    refuse.
    """
    if isinstance(delegation, Delegation):
        return delegation
    if not isinstance(delegation, dict):
        raise ValueError(
            f"a delegation must be a mapping, got {delegation!r}")
    unknown = set(delegation) - _DELEGATION_KEYS
    if unknown:
        raise ValueError(
            "unknown delegation keys: %s"
            % ", ".join(sorted(unknown)))
    delegator = _pick(
        delegation, "delegator", "from_member", "delegators")
    if delegator is None:
        raise ValueError("a delegation is missing its delegator")
    delegatee = _pick(
        delegation, "delegatee", "to_member", "delegatees")
    if delegatee is None:
        raise ValueError("a delegation is missing its delegatee")
    slice_id = _pick(delegation, "slice_id", "slice", "slices")
    if slice_id is None:
        raise ValueError("a delegation is missing its slice")
    kwargs: Dict[str, Any] = {
        "delegator": delegator,
        "delegatee": delegatee,
        "slice_id": slice_id,
    }
    delegation_id = _pick(
        delegation, "delegation_id", "id", "delegation ids")
    if delegation_id is not None:
        kwargs["delegation_id"] = delegation_id
    return Delegation(**kwargs)


def build_delegation(delegation: Any = None,
                     **kwargs: Any) -> Delegation:
    """Build one validated delegation.

    From a Delegation, from a mapping (the spellings
    :func:`validate_delegation` reads), or from field
    words given as keyword arguments.
    """
    if isinstance(delegation, Delegation) and not kwargs:
        return delegation
    if isinstance(delegation, dict) or delegation is None:
        merged: Dict[str, Any] = {}
        if isinstance(delegation, dict):
            merged.update(delegation)
        merged.update(kwargs)
        return validate_delegation(merged)
    raise ValueError(
        f"a delegation must be a mapping, got {delegation!r}")


# ---------------------------------------------------------------------
# The claim: one member holding one slice at one path, as evidence.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class Claim:
    """One member's claim on work, as data.

    ``member`` is the holding member's M-121 member
    id; ``slice_id`` is the slice it holds; ``path``
    is the path it holds the slice at, read exactly
    as the M-124 layer reads a worktree path.
    Constructing one validates its shape only: two
    claims sharing a slice or a path are well-formed
    evidence - catching the overlap is the
    detector's job.
    """

    claim_id: Optional[str] = None
    member: str = ""
    slice_id: str = ""
    path: str = ""

    def __post_init__(self) -> None:
        if self.claim_id is not None:
            object.__setattr__(
                self, "claim_id",
                normalize_member_id(self.claim_id))
        object.__setattr__(
            self, "member", normalize_member_id(self.member))
        object.__setattr__(
            self, "slice_id", normalize_slice_id(self.slice_id))
        object.__setattr__(
            self, "path", normalize_worktree_path(self.path))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "crew_claim",
            "slice": WATCH_SLICE,
            "claim_id": self.claim_id,
            "member": self.member,
            "slice_id": self.slice_id,
            "path": self.path,
        }


def validate_claim(claim: Any) -> Claim:
    """Validate one claim into a Claim.

    Accepts a Claim or a mapping naming a ``member``
    (or ``member_id``), a ``slice_id`` (or
    ``slice``), a ``path`` (or ``worktree_path``) and
    an optional ``claim_id`` (or ``id``). Naming
    both spellings of one field with different
    values refuses, and unknown keys refuse.
    """
    if isinstance(claim, Claim):
        return claim
    if not isinstance(claim, dict):
        raise ValueError(
            f"a claim must be a mapping, got {claim!r}")
    unknown = set(claim) - _CLAIM_KEYS
    if unknown:
        raise ValueError(
            "unknown claim keys: %s"
            % ", ".join(sorted(unknown)))
    member = _pick(claim, "member", "member_id", "members")
    if member is None:
        raise ValueError("a claim is missing its member")
    slice_id = _pick(claim, "slice_id", "slice", "slices")
    if slice_id is None:
        raise ValueError("a claim is missing its slice")
    path = _pick(claim, "path", "worktree_path", "paths")
    if path is None:
        raise ValueError("a claim is missing its path")
    kwargs: Dict[str, Any] = {
        "member": member,
        "slice_id": slice_id,
        "path": path,
    }
    claim_id = _pick(claim, "claim_id", "id", "claim ids")
    if claim_id is not None:
        kwargs["claim_id"] = claim_id
    return Claim(**kwargs)


def build_claim(claim: Any = None, **kwargs: Any) -> Claim:
    """Build one validated claim.

    From a Claim, from a mapping (the spellings
    :func:`validate_claim` reads), or from field
    words given as keyword arguments.
    """
    if isinstance(claim, Claim) and not kwargs:
        return claim
    if isinstance(claim, dict) or claim is None:
        merged: Dict[str, Any] = {}
        if isinstance(claim, dict):
            merged.update(claim)
        merged.update(kwargs)
        return validate_claim(merged)
    raise ValueError(
        f"a claim must be a mapping, got {claim!r}")


# ---------------------------------------------------------------------
# The finding: one hazard caught from the evidence, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    """One hazard caught by the watch, as data.

    ``kind`` is one of the roadmap's three kinds;
    ``members`` are the members the hazard holds, in
    the order the detector names them (a cycle in
    delegation order from its first member, the
    other kinds in member order); ``slice_ids`` and
    ``paths`` are the slices and paths the hazard
    touches, each held once, in order; ``title``
    names the hazard in plain words and ``detail``
    states the whole evidence for it. A finding is
    derived from evidence by the detector - it is a
    record for the coordinator, never an action.
    """

    kind: str = ""
    members: Tuple[str, ...] = ()
    slice_ids: Tuple[str, ...] = ()
    paths: Tuple[str, ...] = ()
    title: str = ""
    detail: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "kind", normalize_finding_kind(self.kind))
        object.__setattr__(
            self, "members", _check_members(self.members))
        object.__setattr__(
            self, "slice_ids", _check_slices(self.slice_ids))
        object.__setattr__(
            self, "paths", _check_paths(self.paths))
        object.__setattr__(self, "title", _check_title(self.title))
        object.__setattr__(
            self, "detail", _check_detail(self.detail))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "deadlock_finding",
            "slice": WATCH_SLICE,
            "kind": self.kind,
            "members": list(self.members),
            "slice_ids": list(self.slice_ids),
            "paths": list(self.paths),
            "title": self.title,
            "detail": self.detail,
        }


def validate_finding(finding: Any) -> Finding:
    """Validate one finding into a Finding.

    Accepts a Finding or a mapping naming a ``kind``
    (or ``finding_kind``), ``members``, ``slice_ids``
    (or ``slices``), ``paths``, a ``title`` and a
    ``detail``. Unknown keys refuse.
    """
    if isinstance(finding, Finding):
        return finding
    if not isinstance(finding, dict):
        raise ValueError(
            f"a finding must be a mapping, got {finding!r}")
    unknown = set(finding) - _FINDING_KEYS
    if unknown:
        raise ValueError(
            "unknown finding keys: %s"
            % ", ".join(sorted(unknown)))
    kind = _pick(finding, "kind", "finding_kind", "kinds")
    if kind is None:
        raise ValueError("a finding is missing its kind")
    slice_ids = _pick(finding, "slice_ids", "slices", "slices")
    if slice_ids is None:
        raise ValueError("a finding is missing its slices")
    for field in ("members", "paths", "title", "detail"):
        if field not in finding:
            raise ValueError(f"a finding is missing its {field}")
    return Finding(
        kind=kind,
        members=finding["members"],
        slice_ids=slice_ids,
        paths=finding["paths"],
        title=finding["title"],
        detail=finding["detail"])


def build_finding(finding: Any = None, **kwargs: Any) -> Finding:
    """Build one validated finding.

    From a Finding, from a mapping (the spellings
    :func:`validate_finding` reads), or from field
    words given as keyword arguments.
    """
    if isinstance(finding, Finding) and not kwargs:
        return finding
    if isinstance(finding, dict) or finding is None:
        merged: Dict[str, Any] = {}
        if isinstance(finding, dict):
            merged.update(finding)
        merged.update(kwargs)
        return validate_finding(merged)
    raise ValueError(
        f"a finding must be a mapping, got {finding!r}")


# ---------------------------------------------------------------------
# The detector: findings derived from the evidence alone.
# ---------------------------------------------------------------------


def _delegation_cycles(
        delegations: Tuple[Delegation, ...],
) -> Tuple[Tuple[str, ...], ...]:
    """Every elementary delegation cycle, canonically.

    A cycle is named from its smallest member, in
    delegation order, the start never repeated at the
    end; a self-delegation is a cycle of one. Cycles
    are returned in sorted order, each exactly once.
    """
    graph: Dict[str, set] = {}
    for delegation in delegations:
        graph.setdefault(delegation.delegator, set()).add(
            delegation.delegatee)
        graph.setdefault(delegation.delegatee, set())
    cycles = set()
    for start in sorted(graph):
        stack = [(start, (start,))]
        while stack:
            node, path = stack.pop()
            for nxt in sorted(graph.get(node, ())):
                if nxt == start:
                    cycles.add(path)
                elif nxt > start and nxt not in path:
                    stack.append((nxt, path + (nxt,)))
    return tuple(sorted(cycles))


def _cycle_finding(cycle: Tuple[str, ...],
                   delegations: Tuple[Delegation, ...]) -> Finding:
    edges = {
        (cycle[index], cycle[(index + 1) % len(cycle)])
        for index in range(len(cycle))}
    slices = tuple(sorted({
        d.slice_id for d in delegations
        if (d.delegator, d.delegatee) in edges}))
    chain = " -> ".join(cycle + (cycle[0],))
    return Finding(
        kind="delegation_cycle",
        members=cycle,
        slice_ids=slices,
        paths=(),
        title=f"Delegation cycle: {chain}",
        detail=(
            f"The delegation chain {chain} loops back on "
            f"itself: each member in the cycle waits on "
            f"the next, so none of the cycle's work can "
            f"finish - a deadlock, caught for the "
            f"coordinator to break by re-dealing one "
            f"delegation in the cycle."))


def _conflict_findings(
        claims: Tuple[Claim, ...]) -> Tuple[Finding, ...]:
    by_path: Dict[str, list] = {}
    for claim in claims:
        by_path.setdefault(claim.path, []).append(claim)
    findings = []
    for path in sorted(by_path):
        held = by_path[path]
        members = tuple(sorted({c.member for c in held}))
        if len(members) < 2:
            continue
        slices = tuple(sorted({c.slice_id for c in held}))
        findings.append(Finding(
            kind="merge_conflict",
            members=members,
            slice_ids=slices,
            paths=(path,),
            title=f"Merge conflict on {path}",
            detail=(
                f"{_member_words(members)} hold the same "
                f"path, {path}, on "
                f"{', '.join(slices)}: their work will "
                f"meet as a merge conflict, caught for "
                f"the coordinator to settle before the "
                f"branches are merged.")))
    return tuple(findings)


def _duplication_findings(
        claims: Tuple[Claim, ...]) -> Tuple[Finding, ...]:
    by_slice: Dict[str, list] = {}
    for claim in claims:
        by_slice.setdefault(claim.slice_id, []).append(claim)
    findings = []
    for slice_id in sorted(by_slice):
        held = by_slice[slice_id]
        members = tuple(sorted({c.member for c in held}))
        if len(members) < 2:
            continue
        paths = tuple(sorted({c.path for c in held}))
        findings.append(Finding(
            kind="duplicated_work",
            members=members,
            slice_ids=(slice_id,),
            paths=paths,
            title=f"Duplicated work on {slice_id}",
            detail=(
                f"{_member_words(members)} hold the same "
                f"slice, {slice_id}, at "
                f"{', '.join(paths)}: the same work is "
                f"dealt twice, caught for the coordinator "
                f"to re-deal to one member.")))
    return tuple(findings)


def _detect(delegations: Tuple[Delegation, ...],
            claims: Tuple[Claim, ...]) -> Tuple[Finding, ...]:
    findings = [
        _cycle_finding(cycle, delegations)
        for cycle in _delegation_cycles(delegations)]
    findings.extend(_conflict_findings(claims))
    findings.extend(_duplication_findings(claims))
    return tuple(findings)


def _evidence_from(source: Any) -> Tuple[
        Tuple[Delegation, ...], Tuple[Claim, ...]]:
    if isinstance(source, DeadlockWatch):
        return source.delegations, source.claims
    if isinstance(source, DeadlockWatchRegistry):
        return source.list_delegations(), source.list_claims()
    if isinstance(source, dict):
        unknown = set(source) - {"delegations", "claims"}
        if unknown:
            raise ValueError(
                "unknown evidence keys: %s"
                % ", ".join(sorted(unknown)))
        raw_delegations = source.get("delegations") or ()
        raw_claims = source.get("claims") or ()
        if isinstance(raw_delegations, (str, bytes)) \
                or not isinstance(raw_delegations, (list, tuple)):
            raise ValueError(
                "evidence delegations must be a list of "
                "delegations")
        if isinstance(raw_claims, (str, bytes)) \
                or not isinstance(raw_claims, (list, tuple)):
            raise ValueError(
                "evidence claims must be a list of claims")
        return (
            tuple(build_delegation(d) for d in raw_delegations),
            tuple(build_claim(c) for c in raw_claims))
    raise ValueError(
        f"watch evidence is needed, got {source!r}")


def detect_findings(source: Any) -> Tuple[Finding, ...]:
    """Every hazard in *source*'s evidence, in fixed order.

    Accepts a DeadlockWatch, a DeadlockWatchRegistry
    or a mapping with ``delegations`` and ``claims``
    lists. The mechanical judge of the watch, as data
    only: delegation cycles first (each named from
    its smallest member), then merge conflicts (by
    path), then duplicated work (by slice) - the same
    evidence always yields the same findings.
    """
    delegations, claims = _evidence_from(source)
    return _detect(delegations, claims)


@dataclass(frozen=True)
class WatchReport:
    """One report of findings, derived from evidence.

    ``findings`` are the hazards the detector caught,
    in detection order. Constructing one validates
    it: every entry is a finding. An empty report is
    a clean watch, not an error.
    """

    findings: Tuple[Finding, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.findings, (str, bytes)) \
                or not isinstance(self.findings, (list, tuple)):
            raise ValueError(
                f"a report's findings must be a list of "
                f"findings, got {self.findings!r}")
        object.__setattr__(
            self, "findings", tuple(
                f if isinstance(f, Finding) else validate_finding(f)
                for f in self.findings))

    @property
    def is_clean(self) -> bool:
        """True when the evidence holds no hazard."""
        return not self.findings

    def by_kind(self, kind: Any) -> Tuple[Finding, ...]:
        """Every finding of one kind, in report order."""
        wanted = normalize_finding_kind(kind)
        return tuple(f for f in self.findings if f.kind == wanted)

    def for_member(self, member: Any) -> Tuple[Finding, ...]:
        """Every finding one member is held in, in order."""
        wanted = normalize_member_id(member)
        return tuple(
            f for f in self.findings if wanted in f.members)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "deadlock_report",
            "slice": WATCH_SLICE,
            "count": len(self.findings),
            "clean": self.is_clean,
            "cycles": len(self.by_kind("delegation_cycle")),
            "merge_conflicts": len(self.by_kind("merge_conflict")),
            "duplicated_work": len(self.by_kind("duplicated_work")),
            "findings": [f.to_record() for f in self.findings],
        }


def validate_report(source: Any, report: Any) -> list:
    """Every problem in a claimed report of *source*, as strings.

    An empty list means the report answers the
    source exactly: every hazard the evidence holds,
    in detection order, and nothing else - a report
    missing a hazard, or holding one the evidence
    does not hold, is named.
    """
    if not isinstance(report, WatchReport):
        return [f"a watch report is needed, got {report!r}"]
    try:
        wanted = detect_findings(source)
    except ValueError as exc:
        return [str(exc)]
    problems = []
    if tuple(report.findings) != wanted:
        problems.append(
            "the report does not hold exactly the evidence's "
            "findings, in detection order: the report must "
            "catch every hazard the evidence holds, and no "
            "other hazard")
    return problems


# ---------------------------------------------------------------------
# The watch: the evidence one file holds, under one keeper.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class DeadlockWatch:
    """A whole watch: the evidence one file holds, in file order.

    ``keeper`` is the member id of the one who keeps
    the watch - in the shipped example the guardian,
    the office this slice's work fits. Constructing
    one holds the watch law: at least one piece of
    evidence, a delegation or a claim.
    """

    delegations: Tuple[Delegation, ...] = ()
    claims: Tuple[Claim, ...] = ()
    keeper: str = ""
    watch_note: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.delegations, (str, bytes)) \
                or not isinstance(self.delegations, (list, tuple)):
            raise ValueError(
                f"a watch's delegations must be a list of "
                f"delegations, got {self.delegations!r}")
        if isinstance(self.claims, (str, bytes)) \
                or not isinstance(self.claims, (list, tuple)):
            raise ValueError(
                f"a watch's claims must be a list of claims, "
                f"got {self.claims!r}")
        delegations = tuple(
            d if isinstance(d, Delegation) else validate_delegation(d)
            for d in self.delegations)
        claims = tuple(
            c if isinstance(c, Claim) else validate_claim(c)
            for c in self.claims)
        if not delegations and not claims:
            raise ValueError(
                "a watch must hold at least one delegation "
                "or claim")
        object.__setattr__(self, "delegations", delegations)
        object.__setattr__(self, "claims", claims)
        object.__setattr__(
            self, "keeper", normalize_member_id(self.keeper))
        object.__setattr__(
            self, "watch_note", str(self.watch_note or ""))

    def report(self) -> WatchReport:
        """The report this watch's evidence yields."""
        return WatchReport(
            findings=_detect(self.delegations, self.claims))

    def delegations_for(self, member: Any) -> Tuple[Delegation, ...]:
        """Every delegation one member gives or receives."""
        wanted = normalize_member_id(member)
        return tuple(
            d for d in self.delegations
            if d.delegator == wanted or d.delegatee == wanted)

    def claims_for(self, member: Any) -> Tuple[Claim, ...]:
        """Every claim one member holds, in file order."""
        wanted = normalize_member_id(member)
        return tuple(c for c in self.claims if c.member == wanted)


def validate_watch(data: Any, *,
                   require_example: bool = False) -> list:
    """Every problem in a watch mapping, as plain strings.

    An empty list means the watch is well-formed.
    With ``require_example`` the watch must be
    exactly the shipped example: the five delegations
    and five claims in file order, kept by the
    guardian - and the report derived from it must
    hold exactly its three findings, one of each
    kind (the check the shipped file is held to; a
    real watch's file is read without it).
    """
    if not isinstance(data, dict):
        return [f"a deadlock watch must be a mapping, got {data!r}"]
    problems = []
    unknown = set(data) - _WATCH_KEYS
    if unknown:
        problems.append(
            "unknown deadlock watch keys: %s"
            % ", ".join(sorted(unknown)))
    if data.get("schema") != WATCH_SCHEMA:
        problems.append(
            f"a deadlock watch's schema must be "
            f"{WATCH_SCHEMA!r}, got {data.get('schema')!r}")
    if data.get("slice") != WATCH_SLICE:
        problems.append(
            f"a deadlock watch's slice must be "
            f"{WATCH_SLICE!r}, got {data.get('slice')!r}")
    keeper = None
    if data.get("keeper") is None:
        problems.append("a deadlock watch is missing its keeper")
    else:
        try:
            keeper = normalize_member_id(data["keeper"])
        except ValueError as exc:
            problems.append(f"keeper: {exc}")
    raw_delegations = data.get("delegations")
    raw_claims = data.get("claims")
    if not isinstance(raw_delegations, list):
        problems.append(
            "a deadlock watch must hold a delegations list")
        raw_delegations = []
    if not isinstance(raw_claims, list):
        problems.append("a deadlock watch must hold a claims list")
        raw_claims = []
    if isinstance(raw_delegations, list) \
            and isinstance(raw_claims, list) \
            and not raw_delegations and not raw_claims:
        problems.append(
            "a deadlock watch must hold at least one "
            "delegation or claim")
    parsed_delegations = []
    for index, entry in enumerate(raw_delegations):
        try:
            parsed_delegations.append(validate_delegation(entry))
        except ValueError as exc:
            problems.append(f"delegation {index + 1}: {exc}")
    parsed_claims = []
    for index, entry in enumerate(raw_claims):
        try:
            parsed_claims.append(validate_claim(entry))
        except ValueError as exc:
            problems.append(f"claim {index + 1}: {exc}")
    if require_example \
            and len(parsed_delegations) == len(raw_delegations) \
            and len(parsed_claims) == len(raw_claims):
        held_delegations = tuple(
            (d.delegator, d.delegatee, d.slice_id)
            for d in parsed_delegations)
        if held_delegations != _EXAMPLE_DELEGATIONS:
            problems.append(
                "the shipped example watch must hold exactly "
                "the five delegations in file order, with "
                "their delegators, delegatees and slices")
        held_claims = tuple(
            (c.member, c.slice_id, c.path) for c in parsed_claims)
        if held_claims != _EXAMPLE_CLAIMS:
            problems.append(
                "the shipped example watch must hold exactly "
                "the five claims in file order, with their "
                "members, slices and paths")
        if keeper is not None and keeper != "guardian":
            problems.append(
                "the shipped example watch is kept by the "
                "guardian")
        if held_delegations == _EXAMPLE_DELEGATIONS \
                and held_claims == _EXAMPLE_CLAIMS:
            kinds = [
                f.kind for f in _detect(
                    tuple(parsed_delegations),
                    tuple(parsed_claims))]
            if kinds != ["delegation_cycle", "merge_conflict",
                         "duplicated_work"]:
                problems.append(
                    "the shipped example watch must yield "
                    "exactly three findings, one of each "
                    "kind, in detection order")
    return problems


def _watch_from(data: Any, *, require_example: bool) -> DeadlockWatch:
    problems = validate_watch(data, require_example=require_example)
    if problems:
        raise ValidationError(
            "invalid deadlock watch: " + "; ".join(problems))
    assert isinstance(data, dict)
    return DeadlockWatch(
        delegations=tuple(
            validate_delegation(entry)
            for entry in data["delegations"]),
        claims=tuple(
            validate_claim(entry) for entry in data["claims"]),
        keeper=data["keeper"],
        watch_note=str(data.get("watch_note") or ""))


def load_deadlock_watch(
        data: Optional[Dict[str, Any]] = None) -> DeadlockWatch:
    """Load and validate the shipped example watch (or *data*).

    The shipped file is held to the example check:
    exactly the five delegations and five claims,
    kept by the guardian, yielding exactly its three
    findings, one of each kind. Raises
    :class:`ValidationError` listing every problem
    when the record is not a well-formed watch.
    """
    raw = data if data is not None else load_resource(WATCH_RESOURCE)
    return _watch_from(raw, require_example=True)


def load_deadlock_watch_file(path: Any) -> DeadlockWatch:
    """Load and validate a watch from a file at *path*.

    This is the road a real watch arrives by: any
    file in the watch shape, anywhere on disk,
    validated whole - a malformed file raises
    :class:`ValidationError` naming the problem, and
    a missing file raises ``FileNotFoundError``. The
    example check is not held: a watch may hold a
    single delegation.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _watch_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: evidence held in registration order, ids
# deterministic. A registry refuses a supplied id already held, and
# refuses nothing for repetition: the same delegation or claim given
# twice is two pieces of evidence - the detector reads sets of
# members, so repetition alone never makes a hazard.
# ---------------------------------------------------------------------


class DeadlockWatchRegistry:
    """An in-memory registry of watch evidence.

    Delegations and claims are held in registration
    order. Ids are deterministic: a caller-supplied
    id is used as given, and an unsupplied id is the
    next ``delegation-N`` / ``claim-N`` in sequence,
    skipping any number a supplied id already took.
    A supplied id already held refuses. Storage
    beyond memory (a session's journal, a file) is
    the agent layer's concern; this model is neutral.
    """

    def __init__(self) -> None:
        self._delegations: Dict[str, Delegation] = {}
        self._claims: Dict[str, Claim] = {}
        self._next_delegation = 1
        self._next_claim = 1

    def _fresh_delegation_id(self) -> str:
        while f"delegation-{self._next_delegation}" \
                in self._delegations:
            self._next_delegation += 1
        delegation_id = f"delegation-{self._next_delegation}"
        self._next_delegation += 1
        return delegation_id

    def _fresh_claim_id(self) -> str:
        while f"claim-{self._next_claim}" in self._claims:
            self._next_claim += 1
        claim_id = f"claim-{self._next_claim}"
        self._next_claim += 1
        return claim_id

    def register_delegation(self, delegation: Any) -> Delegation:
        """Register one delegation and hold it."""
        validated = build_delegation(delegation)
        if validated.delegation_id is not None \
                and validated.delegation_id in self._delegations:
            raise ValueError(
                f"a delegation named "
                f"{validated.delegation_id!r} already exists")
        if validated.delegation_id is None:
            validated = replace(
                validated,
                delegation_id=self._fresh_delegation_id())
        self._delegations[validated.delegation_id] = validated
        return validated

    def register_claim(self, claim: Any) -> Claim:
        """Register one claim and hold it."""
        validated = build_claim(claim)
        if validated.claim_id is not None \
                and validated.claim_id in self._claims:
            raise ValueError(
                f"a claim named {validated.claim_id!r} "
                f"already exists")
        if validated.claim_id is None:
            validated = replace(
                validated, claim_id=self._fresh_claim_id())
        self._claims[validated.claim_id] = validated
        return validated

    def register_watch(self, watch: Any) -> Tuple[
            Tuple[Delegation, ...], Tuple[Claim, ...]]:
        """Register every piece of one watch's evidence, in order."""
        if not isinstance(watch, DeadlockWatch):
            raise ValueError(f"a deadlock watch is needed, got {watch!r}")
        delegations = tuple(
            self.register_delegation(d) for d in watch.delegations)
        claims = tuple(
            self.register_claim(c) for c in watch.claims)
        return delegations, claims

    def get_delegation(self, delegation_id: Any) -> Delegation:
        """The delegation one id names; an unknown id raises."""
        wanted = normalize_member_id(delegation_id)
        if wanted not in self._delegations:
            raise KeyError(f"unknown delegation: {wanted!r}")
        return self._delegations[wanted]

    def get_claim(self, claim_id: Any) -> Claim:
        """The claim one id names; an unknown id raises."""
        wanted = normalize_member_id(claim_id)
        if wanted not in self._claims:
            raise KeyError(f"unknown claim: {wanted!r}")
        return self._claims[wanted]

    def list_delegations(self) -> Tuple[Delegation, ...]:
        """Every held delegation, in registration order."""
        return tuple(self._delegations.values())

    def list_claims(self) -> Tuple[Claim, ...]:
        """Every held claim, in registration order."""
        return tuple(self._claims.values())

    def findings(self) -> Tuple[Finding, ...]:
        """Every hazard in the held evidence, in detection order."""
        return _detect(self.list_delegations(), self.list_claims())

    def report(self) -> WatchReport:
        """The report the held evidence yields."""
        return WatchReport(findings=self.findings())

    def for_member(self, member: Any) -> Tuple[Finding, ...]:
        """Every held finding one member is held in, in order."""
        return self.report().for_member(member)


# ---------------------------------------------------------------------
# Watch news, shaped as session records.
# ---------------------------------------------------------------------


def delegation_record(delegation: Any) -> Dict[str, Any]:
    """The session-news record of one delegation."""
    current = delegation if isinstance(delegation, Delegation) \
        else build_delegation(delegation)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.delegator} delegates {current.slice_id} "
        f"to {current.delegatee}.")
    return record


def claim_record(claim: Any) -> Dict[str, Any]:
    """The session-news record of one claim."""
    current = claim if isinstance(claim, Claim) \
        else build_claim(claim)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.member} holds {current.slice_id} "
        f"at {current.path}.")
    return record


def plain_words(finding: Any) -> str:
    """One finding, in one plain sentence."""
    current = finding if isinstance(finding, Finding) \
        else build_finding(finding)
    return f"{current.title} - {current.detail}"


def finding_record(finding: Any) -> Dict[str, Any]:
    """The session-news record of one finding.

    Carries the finding's whole record plus a
    one-line plain headline, so a hazard caught in a
    session is news with its shape attached, never a
    bare log line.
    """
    current = finding if isinstance(finding, Finding) \
        else build_finding(finding)
    record = current.to_record()
    record["news"] = True
    record["headline"] = plain_words(current)
    return record


def report_plain_words(report: Any) -> str:
    """One watch report, in one plain sentence."""
    current = report if isinstance(report, WatchReport) \
        else WatchReport(findings=report)
    if current.is_clean:
        return "The watch is clean: no hazard is caught."
    caught = "; ".join(f.title for f in current.findings)
    return (
        f"{len(current.findings)} hazards caught for the "
        f"coordinator: {caught}.")


def report_record(report: Any) -> Dict[str, Any]:
    """The session-news record of one watch report.

    ONE record holding every finding with its full
    evidence - the report itself, as news for the
    coordinator.
    """
    current = report if isinstance(report, WatchReport) \
        else WatchReport(findings=report)
    record = current.to_record()
    record["news"] = True
    record["headline"] = report_plain_words(current)
    return record


# ---------------------------------------------------------------------
# The /deadlock surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def format_finding(finding: Any) -> str:
    """One finding, in plain words."""
    current = finding if isinstance(finding, Finding) \
        else build_finding(finding)
    return f"  {current.kind}: {plain_words(current)}"


def _selected_findings(source: Any) -> Tuple[Finding, ...]:
    if source is None:
        return load_deadlock_watch().report().findings
    if isinstance(source, WatchReport):
        return source.findings
    if isinstance(source, (DeadlockWatch, DeadlockWatchRegistry, dict)):
        return detect_findings(source)
    if isinstance(source, (str, bytes)) \
            or not isinstance(source, (list, tuple)):
        raise ValueError("findings must be a list of findings")
    return tuple(
        f if isinstance(f, Finding) else build_finding(f)
        for f in source)


def format_findings(source: Any = None) -> str:
    """The findings, in plain words, in detection order.

    Accepts a list of findings, a WatchReport, a
    DeadlockWatch or a DeadlockWatchRegistry. With
    no source the shipped example watch's findings
    are shown. With no hazards at all the text states
    the watch is clean, plainly.
    """
    selected = _selected_findings(source)
    if not selected:
        return ("Deadlock watch: clean. No delegation cycle, "
                "merge conflict or duplicated work is caught.")
    lines = [
        f"Deadlock watch: {len(selected)} hazards caught "
        f"for the coordinator."]
    for finding in selected:
        lines.append(format_finding(finding))
    return "\n".join(lines)


def format_kinds() -> str:
    """The finding kinds, in plain words."""
    return (
        "Finding kinds: delegation_cycle (a chain of "
        "delegations looping back to its start - each "
        "member waits on the next, a deadlock), "
        "merge_conflict (two members holding the same "
        "path, whose work will meet as a merge "
        "conflict), duplicated_work (two members "
        "holding the same slice, the same work dealt "
        "twice).")


def format_deadlock_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /deadlock.

    With nothing named, the shipped example watch's
    findings are shown - the example this slice
    ships - so the screen is never empty. There is
    no Part VIII board yet; this screen is where the
    findings are visible.
    """
    lines = ["Deadlock watch (M-127) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_findings(source))
    lines.append("")
    lines.append(format_kinds())
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_deadlock_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /deadlock grammar both surfaces share.

    No words (or ``show`` / ``list`` / ``findings``)
    shows the findings; ``show <member>`` and a bare
    member id show one member's findings; ``kinds``
    asks for the kinds. Anything else is a usage
    error naming the grammar. Returns
    ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None \
        else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list", "findings"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head == "show" and len(words) == 2:
        try:
            return ("show", normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "kinds" and len(words) == 1:
        return ("kinds", None)
    if head in ("show", "kinds", "list", "findings"):
        raise ValueError(USAGE)
    if len(words) == 1:
        try:
            return ("show", normalize_member_id(words[0]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
