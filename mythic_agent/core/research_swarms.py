"""Research swarms (All-Features roadmap slice M-131).

Part VI - Agents as files - continues here. The
roadmap's words: ``Cartographer-led fan-out for
questions (docs, options, comparisons) returning
one digested answer with sources - the
deep-research pattern as a crew formation.``

What already shipped, and what this slice adds:

* The crew itself is already data
  (``core/crew_members.py``, M-121: the casting
  holds a ``cartographer`` member, Védis Eikleið,
  whose office is map & research), the offices are
  formalised (M-122, M-123), and the worktrees,
  dealing, comms, deadlock watch, merge
  discipline, heterogeneous crews and the
  Auditor's veto are already data (M-124 to
  M-130). What nothing held is the research
  formation itself: a question dealt out to
  several members at once, each reading one focus
  of it, and the one digested answer their
  findings add up to - so today a hard question is
  read by one member alone, in one pass, and no
  record anywhere holds who read what, what they
  found, or which sources the answer stands on.
* This slice is that formation, as a pure layer:
  the swarm validated as data (a question - the
  question asked, and the member who leads the
  swarm; an assignment - one member dealt one
  focus of the question, the docs, the options or
  the comparison, with the brief they were dealt;
  and a finding - what one member's reading found,
  in plain words, with the sources it stands on),
  the shipped data file
  (``mythic_agent/data/research_swarms.yaml``)
  holding one example swarm in exactly the shape a
  real swarm's file takes, a loader for a swarm
  file anywhere on disk, the digest derived
  mechanically from the findings alone, a digest
  record shaped as session news, and a small
  in-memory registry model. This module runs no
  research, calls no model, opens no page and
  imports no agent / UI code; the agent layer owns
  holding the swarm for a session and handing the
  digest to the human.

Honesty rules, enforced here and pinned by tests:

* **The digest is derived, never stored.** A
  digest is computed from the question, the
  assignments and the findings it is judged
  under, so it can never disagree with them; the
  same swarm always yields the same digest
  (deterministic order, deterministic wording).
* **The leader is the Cartographer.** A swarm's
  question names its leader as an M-121 member id
  read exactly as the M-121 layer reads one
  (``core/crew_members.py``) - composed by import,
  never re-read here - and the shipped example is
  held to the roadmap's word: its leader is the
  casting's ``cartographer`` member, the office
  whose duty is map & research (M-122).
* **A swarm is complete only when every
  assignment holds a finding.** An assignment
  whose member returned nothing is named in the
  digest as still out - never dropped, never
  filled in from another member's finding - and a
  finding from a member who holds no assignment
  refuses: nobody reports on a focus they were
  not dealt.
* **Every finding stands on sources.** A finding
  names at least one source, and the digest holds
  every source the findings cite, each once, in
  the order the findings cite them - an answer
  whose sources cannot be named is not a digested
  answer.
* **The swarm is data only; no research is run
  here.** No model is called, no page is opened,
  no crew is spawned and no member is tasked in
  this slice: a swarm here is a validated record
  of a fan-out and its findings, not the fan-out
  itself, and the members' live readings arrive
  through later roads. The roadmap names the
  board (Part VIII) as where crew state will be
  visible; that board does not exist yet, so the
  digest is visible through this slice's own
  /swarm screen, and nothing here claims a board
  exists.
* **Malformed refuses.** An unknown focus, a
  malformed member, question or source, a member
  dealt two assignments, two findings from one
  member, a finding from an undealt member, a
  swarm holding no assignments at all, and
  unknown keys in a question, an assignment, a
  finding, a digest or a swarm mapping all raise
  instead of being skipped or guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .validation import ValidationError

__all__ = [
    "FOCUS_KINDS",
    "PLAIN_EXPLANATION",
    "SWARM_RESOURCE",
    "SWARM_SCHEMA",
    "SWARM_SLICE",
    "USAGE",
    "ResearchSwarm",
    "ResearchSwarmRegistry",
    "SwarmAssignment",
    "SwarmDigest",
    "SwarmFinding",
    "SwarmQuestion",
    "assignment_record",
    "build_assignment",
    "build_digest",
    "build_finding",
    "build_question",
    "digest_plain_words",
    "digest_record",
    "digest_swarm",
    "finding_record",
    "format_digest",
    "format_finding",
    "format_findings",
    "format_focus_kinds",
    "format_swarm_screen",
    "load_research_swarm",
    "load_research_swarm_file",
    "normalize_focus_kind",
    "normalize_source",
    "parse_swarm_args",
    "plain_words",
    "question_record",
    "validate_assignment",
    "validate_digest",
    "validate_finding",
    "validate_question",
    "validate_swarm",
]

SWARM_SLICE = "M-131"

#: The packaged data resource holding the example swarm.
SWARM_RESOURCE = "research_swarms.yaml"

#: The schema word a swarm file must carry.
SWARM_SCHEMA = "mythic.research_swarms/1"

#: The focus kinds, in roadmap order: the docs,
#: the options, the comparison.
FOCUS_KINDS = ("docs", "options", "comparison")

_FOCUS_READINGS = {
    "docs": "docs",
    "doc": "docs",
    "documentation": "docs",
    "sources": "docs",
    "options": "options",
    "option": "options",
    "choices": "options",
    "comparison": "comparison",
    "compare": "comparison",
    "comparisons": "comparison",
    "versus": "comparison",
}

_QUESTION_KEYS = frozenset({
    "id", "question_id", "text", "question",
    "leader", "leader_id", "led_by",
})

_ASSIGNMENT_KEYS = frozenset({
    "id", "assignment_id", "member", "member_id",
    "focus", "focus_kind", "kind", "brief", "note",
})

_FINDING_KEYS = frozenset({
    "id", "finding_id", "member", "member_id",
    "summary", "finding", "text", "sources", "source",
})

_DIGEST_KEYS = frozenset({
    "question", "answer", "sources", "complete",
    "missing", "missing_members",
})

_SWARM_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "swarm_note", "leader", "question",
    "assignments", "findings",
})

#: The shipped example swarm's leader: the
#: roadmap's word - the cartographer leads.
_EXAMPLE_LEADER = "cartographer"

#: The shipped example swarm's assignments, in
#: file order: (member, focus). The shipped data
#: file is held to exactly this list by the
#: loader's example check.
_EXAMPLE_ASSIGNMENTS = (
    ("cartographer", "docs"),
    ("architect", "options"),
    ("scribe", "comparison"),
)

#: The shipped example swarm's findings, in file
#: order: the members who reported - every dealt
#: member, so the example digest is complete.
_EXAMPLE_FINDERS = (
    "cartographer", "architect", "scribe")

PLAIN_EXPLANATION = (
    "Research swarms: a Cartographer-led fan-out "
    "for questions - one question dealt out to "
    "several members at once, each reading one "
    "focus of it (the docs, the options, the "
    "comparison), returning one digested answer "
    "with sources. The digest is derived from "
    "the findings alone, and the swarm is "
    "complete exactly when every assignment "
    "holds a finding; an assignment still out "
    "is named, never dropped. There is no Part "
    "VIII board yet, so the digest is visible "
    "on this slice's own screen, not on a "
    "board. This layer holds the swarm as data "
    "only; it runs no research, calls no model "
    "and spawns no crew itself - the findings "
    "arrive through later roads."
)

USAGE = (
    "Usage: /swarm, /swarm show, "
    "/swarm show <member>, /swarm digest, "
    "/swarm sources, /swarm kinds"
)


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


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


def normalize_focus_kind(value: Any) -> str:
    """The canonical focus kind a word names.

    Focus words read case-insensitively, with
    dashes read as underscores: ``documentation``
    and ``sources`` read as docs, ``choices`` as
    options, ``versus`` as comparison. Anything
    else raises - a focus is one of the roadmap's
    three, never a maybe.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted in _FOCUS_READINGS:
            return _FOCUS_READINGS[wanted]
    raise ValueError(
        "a focus kind must be one of %s, got %r"
        % ("/".join(FOCUS_KINDS), value))


def normalize_source(value: Any) -> str:
    """The canonical source a word names.

    A source is one plain reference - a path, a
    document name or a plain title - of at most
    300 characters, holding no control characters.
    Anything else raises.
    """
    source = _clean_text(value, "a source")
    if len(source) > 300 or "\x00" in source:
        raise ValueError(
            f"a source must be plain text of at most "
            f"300 characters, got {len(source)} characters")
    return source


def _check_sources(value: Any) -> Tuple[str, ...]:
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, (list, tuple)):
        items = list(value)
    else:
        raise ValueError(
            f"a finding's sources must be a list, got {value!r}")
    sources = tuple(normalize_source(item) for item in items)
    if not sources:
        raise ValueError(
            "a finding must name at least one source")
    if len(set(sources)) != len(sources):
        raise ValueError(
            "a finding names one source twice")
    return sources


def _pick_any(mapping: Dict[str, Any], spellings: Tuple[str, ...],
              what: str) -> Any:
    """One field from any of its spellings, or a refusal.

    Every spelling present must name the same
    value; two different values under two spellings
    of one field refuse.
    """
    values = [mapping[s] for s in spellings if s in mapping]
    if not values:
        return None
    if any(value != values[0] for value in values[1:]):
        raise ValueError(f"a record names two different {what}")
    return values[0]


# ---------------------------------------------------------------------
# The question: one question and the member who leads its swarm.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SwarmQuestion:
    """One question a swarm is asked, as data.

    ``text`` is the question itself; ``leader``
    is the M-121 member who leads the fan-out -
    the roadmap names the cartographer, and the
    shipped example is held to that word by the
    loader. Constructing one validates its shape
    only: who is dealt what is the swarm's
    concern, not the validator's.
    """

    question_id: Optional[str] = None
    text: str = ""
    leader: str = ""

    def __post_init__(self) -> None:
        if self.question_id is not None:
            object.__setattr__(
                self, "question_id",
                normalize_member_id(self.question_id))
        object.__setattr__(
            self, "text", _check_long_text(self.text, "a question"))
        object.__setattr__(
            self, "leader",
            normalize_member_id(self.leader))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "swarm_question",
            "slice": SWARM_SLICE,
            "question_id": self.question_id,
            "text": self.text,
            "leader": self.leader,
        }


def validate_question(question: Any) -> SwarmQuestion:
    """Validate one question into a SwarmQuestion.

    Accepts a SwarmQuestion or a mapping naming a
    ``text`` (or ``question``), a ``leader`` (or
    ``leader_id`` / ``led_by``) and an optional
    ``question_id`` (or ``id``). Naming two
    spellings of one field with different values
    refuses, and unknown keys refuse.
    """
    if isinstance(question, SwarmQuestion):
        return question
    if not isinstance(question, dict):
        raise ValueError(
            f"a question must be a mapping, got {question!r}")
    unknown = set(question) - _QUESTION_KEYS
    if unknown:
        raise ValueError(
            "unknown question keys: %s"
            % ", ".join(sorted(unknown)))
    text = _pick_any(question, ("text", "question"), "questions")
    if text is None:
        raise ValueError("a question is missing its text")
    leader = _pick_any(
        question, ("leader", "leader_id", "led_by"), "leaders")
    if leader is None:
        raise ValueError("a question is missing its leader")
    kwargs: Dict[str, Any] = {"text": text, "leader": leader}
    question_id = _pick_any(
        question, ("question_id", "id"), "question ids")
    if question_id is not None:
        kwargs["question_id"] = question_id
    return SwarmQuestion(**kwargs)


def build_question(
        question: Any = None, **kwargs: Any) -> SwarmQuestion:
    """Build one validated question.

    From a SwarmQuestion, from a mapping (the
    spellings :func:`validate_question` reads), or
    from field words given as keyword arguments.
    """
    if isinstance(question, SwarmQuestion) and not kwargs:
        return question
    if isinstance(question, dict) or question is None:
        merged: Dict[str, Any] = {}
        if isinstance(question, dict):
            merged.update(question)
        merged.update(kwargs)
        return validate_question(merged)
    raise ValueError(
        f"a question must be a mapping, got {question!r}")


# ---------------------------------------------------------------------
# The assignment: one member dealt one focus of the question.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SwarmAssignment:
    """One member dealt one focus, as data.

    ``member`` is the M-121 member dealt the
    focus; ``focus`` is the focus kind - the docs,
    the options or the comparison; ``brief`` is
    the plain-words brief the member was dealt.
    Constructing one validates its shape only:
    what the member found is the finding's
    concern, not the validator's.
    """

    assignment_id: Optional[str] = None
    member: str = ""
    focus: str = ""
    brief: str = ""

    def __post_init__(self) -> None:
        if self.assignment_id is not None:
            object.__setattr__(
                self, "assignment_id",
                normalize_member_id(self.assignment_id))
        object.__setattr__(
            self, "member",
            normalize_member_id(self.member))
        object.__setattr__(
            self, "focus", normalize_focus_kind(self.focus))
        object.__setattr__(
            self, "brief", _check_long_text(self.brief, "a brief"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "swarm_assignment",
            "slice": SWARM_SLICE,
            "assignment_id": self.assignment_id,
            "member": self.member,
            "focus": self.focus,
            "brief": self.brief,
        }


def validate_assignment(assignment: Any) -> SwarmAssignment:
    """Validate one assignment into a SwarmAssignment.

    Accepts a SwarmAssignment or a mapping naming
    a ``member`` (or ``member_id``), a ``focus``
    (or ``focus_kind`` / ``kind``), a ``brief``
    (or ``note``) and an optional ``assignment_id``
    (or ``id``). Naming two spellings of one field
    with different values refuses, and unknown
    keys refuse.
    """
    if isinstance(assignment, SwarmAssignment):
        return assignment
    if not isinstance(assignment, dict):
        raise ValueError(
            f"an assignment must be a mapping, got {assignment!r}")
    unknown = set(assignment) - _ASSIGNMENT_KEYS
    if unknown:
        raise ValueError(
            "unknown assignment keys: %s"
            % ", ".join(sorted(unknown)))
    member = _pick_any(
        assignment, ("member", "member_id"), "members")
    if member is None:
        raise ValueError("an assignment is missing its member")
    focus = _pick_any(
        assignment, ("focus", "focus_kind", "kind"), "focuses")
    if focus is None:
        raise ValueError("an assignment is missing its focus")
    brief = _pick_any(assignment, ("brief", "note"), "briefs")
    if brief is None:
        raise ValueError("an assignment is missing its brief")
    kwargs: Dict[str, Any] = {
        "member": member, "focus": focus, "brief": brief}
    assignment_id = _pick_any(
        assignment, ("assignment_id", "id"), "assignment ids")
    if assignment_id is not None:
        kwargs["assignment_id"] = assignment_id
    return SwarmAssignment(**kwargs)


def build_assignment(
        assignment: Any = None, **kwargs: Any) -> SwarmAssignment:
    """Build one validated assignment.

    From a SwarmAssignment, from a mapping (the
    spellings :func:`validate_assignment` reads),
    or from field words given as keyword arguments.
    """
    if isinstance(assignment, SwarmAssignment) and not kwargs:
        return assignment
    if isinstance(assignment, dict) or assignment is None:
        merged: Dict[str, Any] = {}
        if isinstance(assignment, dict):
            merged.update(assignment)
        merged.update(kwargs)
        return validate_assignment(merged)
    raise ValueError(
        f"an assignment must be a mapping, got {assignment!r}")


# ---------------------------------------------------------------------
# The finding: what one member's reading found, with its sources.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SwarmFinding:
    """One member's finding, as data.

    ``member`` is the M-121 member who reports;
    ``summary`` is what their reading found, in
    plain words; ``sources`` names what the
    finding stands on - at least one source, each
    named once. Constructing one validates its
    shape only: whether the member was dealt an
    assignment is the swarm's concern, not the
    validator's.
    """

    finding_id: Optional[str] = None
    member: str = ""
    summary: str = ""
    sources: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.finding_id is not None:
            object.__setattr__(
                self, "finding_id",
                normalize_member_id(self.finding_id))
        object.__setattr__(
            self, "member",
            normalize_member_id(self.member))
        object.__setattr__(
            self, "summary",
            _check_long_text(self.summary, "a summary"))
        object.__setattr__(
            self, "sources", _check_sources(self.sources))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "swarm_finding",
            "slice": SWARM_SLICE,
            "finding_id": self.finding_id,
            "member": self.member,
            "summary": self.summary,
            "sources": list(self.sources),
        }


def validate_finding(finding: Any) -> SwarmFinding:
    """Validate one finding into a SwarmFinding.

    Accepts a SwarmFinding or a mapping naming a
    ``member`` (or ``member_id``), a ``summary``
    (or ``finding`` / ``text``), ``sources`` (or a
    single ``source``) and an optional
    ``finding_id`` (or ``id``). Naming two
    spellings of one field with different values
    refuses, and unknown keys refuse.
    """
    if isinstance(finding, SwarmFinding):
        return finding
    if not isinstance(finding, dict):
        raise ValueError(
            f"a finding must be a mapping, got {finding!r}")
    unknown = set(finding) - _FINDING_KEYS
    if unknown:
        raise ValueError(
            "unknown finding keys: %s"
            % ", ".join(sorted(unknown)))
    member = _pick_any(finding, ("member", "member_id"), "members")
    if member is None:
        raise ValueError("a finding is missing its member")
    summary = _pick_any(
        finding, ("summary", "finding", "text"), "summaries")
    if summary is None:
        raise ValueError("a finding is missing its summary")
    sources = _pick_any(finding, ("sources", "source"), "sources")
    if sources is None:
        raise ValueError("a finding is missing its sources")
    kwargs: Dict[str, Any] = {
        "member": member, "summary": summary, "sources": sources}
    finding_id = _pick_any(
        finding, ("finding_id", "id"), "finding ids")
    if finding_id is not None:
        kwargs["finding_id"] = finding_id
    return SwarmFinding(**kwargs)


def build_finding(
        finding: Any = None, **kwargs: Any) -> SwarmFinding:
    """Build one validated finding.

    From a SwarmFinding, from a mapping (the
    spellings :func:`validate_finding` reads), or
    from field words given as keyword arguments.
    """
    if isinstance(finding, SwarmFinding) and not kwargs:
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
# The swarm: one question, its assignments and its findings, whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ResearchSwarm:
    """One whole research swarm, as data.

    ``question`` is the SwarmQuestion asked;
    ``assignments`` are the fan-out, one per
    member; ``findings`` are what came back;
    ``leader`` and ``swarm_note`` are the file's
    own words about itself. A swarm is validated
    whole by :func:`validate_swarm`: the leader
    the file names and the leader the question
    names must agree, no member is dealt twice,
    no member reports twice, and every finding
    comes from a dealt member.
    """

    question: Optional[SwarmQuestion] = None
    assignments: Tuple[SwarmAssignment, ...] = ()
    findings: Tuple[SwarmFinding, ...] = ()
    leader: str = ""
    swarm_note: str = ""

    def assignment_for(self, member: Any) -> SwarmAssignment:
        """The assignment one member holds; undealt raises."""
        wanted = normalize_member_id(member)
        for assignment in self.assignments:
            if assignment.member == wanted:
                return assignment
        raise KeyError(f"no assignment for member: {wanted!r}")

    def finding_for(self, member: Any) -> SwarmFinding:
        """The finding one member returned; unreported raises."""
        wanted = normalize_member_id(member)
        for finding in self.findings:
            if finding.member == wanted:
                return finding
        raise KeyError(f"no finding from member: {wanted!r}")

    def missing_members(self) -> Tuple[str, ...]:
        """Dealt members who returned nothing, in dealing order."""
        reported = {finding.member for finding in self.findings}
        return tuple(
            assignment.member for assignment in self.assignments
            if assignment.member not in reported)

    def is_complete(self) -> bool:
        """True exactly when every assignment holds a finding."""
        return not self.missing_members()


def validate_swarm(data: Any, *, require_example: bool = False) -> ResearchSwarm:
    """Validate one swarm mapping into a ResearchSwarm.

    The mapping names a ``schema`` (the swarm
    schema word), a ``leader`` and a ``question``,
    an ``assignments`` list and a ``findings``
    list. Every piece is validated, then the whole
    is judged: the file's leader and the
    question's leader agree, the question's leader
    holds an assignment, no member is dealt twice
    or reports twice, every finding comes from a
    dealt member, and at least one assignment is
    dealt. With ``require_example`` the shipped
    example is held to its pinned shape: led by
    the cartographer, the three pinned assignments
    in order, and a finding from every dealt
    member. Problems raise :class:`ValidationError`
    or ``ValueError`` naming the problem.
    """
    if isinstance(data, ResearchSwarm):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a research swarm must be a mapping, got {data!r}")
    unknown = set(data) - _SWARM_KEYS
    if unknown:
        raise ValidationError(
            "unknown swarm keys: %s" % ", ".join(sorted(unknown)))
    if data.get("schema") != SWARM_SCHEMA:
        raise ValidationError(
            f"a research swarm must carry schema {SWARM_SCHEMA!r}, "
            f"got {data.get('schema')!r}")
    leader_raw = data.get("leader")
    if leader_raw is None:
        raise ValidationError("a research swarm is missing its leader")
    leader = normalize_member_id(leader_raw)
    if "question" not in data:
        raise ValidationError("a research swarm is missing its question")
    question = validate_question(data["question"])
    if question.leader != leader:
        raise ValidationError(
            f"a swarm's leader {leader!r} and its question's leader "
            f"{question.leader!r} disagree")
    raw_assignments = data.get("assignments")
    if not isinstance(raw_assignments, (list, tuple)) or not raw_assignments:
        raise ValidationError(
            "a research swarm must deal at least one assignment")
    assignments = tuple(
        validate_assignment(entry) for entry in raw_assignments)
    dealt = [assignment.member for assignment in assignments]
    if len(set(dealt)) != len(dealt):
        raise ValidationError(
            "a member is dealt two assignments in one swarm")
    if leader not in dealt:
        raise ValidationError(
            "a swarm's leader holds no assignment: the leader "
            "reads the docs focus of their own swarm")
    raw_findings = data.get("findings") or []
    if not isinstance(raw_findings, (list, tuple)):
        raise ValidationError("a swarm's findings must be a list")
    findings = tuple(validate_finding(entry) for entry in raw_findings)
    reporters = [finding.member for finding in findings]
    if len(set(reporters)) != len(reporters):
        raise ValidationError(
            "a member reports two findings in one swarm")
    for finding in findings:
        if finding.member not in dealt:
            raise ValidationError(
                f"a finding from {finding.member!r}, who holds no "
                f"assignment in this swarm, refuses")
    note = data.get("swarm_note") or ""
    if not isinstance(note, str):
        raise ValidationError("a swarm's note must be text")
    swarm = ResearchSwarm(
        question=question, assignments=assignments,
        findings=findings, leader=leader, swarm_note=note.strip())
    if require_example:
        if leader != _EXAMPLE_LEADER:
            raise ValidationError(
                f"the shipped example swarm is led by "
                f"{_EXAMPLE_LEADER!r}, got {leader!r}")
        shape = tuple(
            (a.member, a.focus) for a in assignments)
        if shape != _EXAMPLE_ASSIGNMENTS:
            raise ValidationError(
                "the shipped example swarm's assignments are not "
                "the pinned three, in order")
        if tuple(f.member for f in findings) != _EXAMPLE_FINDERS:
            raise ValidationError(
                "the shipped example swarm's findings are not "
                "the pinned three, in order")
        if not swarm.is_complete():
            raise ValidationError(
                "the shipped example swarm's digest must be complete")
    return swarm


def _swarm_from(data: Any, *, require_example: bool) -> ResearchSwarm:
    try:
        return validate_swarm(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_research_swarm(
        data: Optional[Dict[str, Any]] = None) -> ResearchSwarm:
    """Load and validate the shipped example swarm (or *data*).

    The shipped file is held to the example check:
    exactly the cartographer leading, the three
    pinned assignments and a finding from each,
    yielding a complete digest. Raises
    :class:`ValidationError` naming the problem
    when the record is not a well-formed swarm.
    """
    raw = data if data is not None else load_resource(SWARM_RESOURCE)
    return _swarm_from(raw, require_example=True)


def load_research_swarm_file(path: Any) -> ResearchSwarm:
    """Load and validate a research swarm from a file at *path*.

    This is the road a real swarm arrives by: any
    file in the swarm shape, anywhere on disk,
    validated whole - a malformed file raises
    :class:`ValidationError` naming the problem,
    and a missing file raises ``FileNotFoundError``.
    The example check is not held: a real swarm may
    still be waiting on findings.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _swarm_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The digest: one digested answer with sources, derived, never stored.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SwarmDigest:
    """One digested answer, derived from a swarm.

    ``question`` is the question the swarm was
    asked; ``answer`` is the one digested answer
    in plain words; ``sources`` holds every source
    the findings cite, each once, in citing
    order; ``complete`` says whether every
    assignment holds a finding; ``missing`` names
    the dealt members still out, in dealing order.
    """

    question: str = ""
    answer: str = ""
    sources: Tuple[str, ...] = ()
    complete: bool = False
    missing: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "question",
            _check_long_text(self.question, "a question"))
        object.__setattr__(
            self, "answer", _check_long_text(self.answer, "an answer"))
        sources = tuple(
            normalize_source(source) for source in self.sources)
        if len(set(sources)) != len(sources):
            raise ValueError("a digest names one source twice")
        object.__setattr__(self, "sources", sources)
        if not isinstance(self.complete, bool):
            raise ValueError(
                f"a digest's complete must be true or false, "
                f"got {self.complete!r}")
        missing = tuple(
            normalize_member_id(member) for member in self.missing)
        if len(set(missing)) != len(missing):
            raise ValueError("a digest names one missing member twice")
        object.__setattr__(self, "missing", missing)
        if self.complete and self.missing:
            raise ValueError(
                "a complete digest names no missing members")
        if not self.complete and not self.missing:
            raise ValueError(
                "an incomplete digest must name who is still out")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "swarm_digest",
            "slice": SWARM_SLICE,
            "question": self.question,
            "answer": self.answer,
            "sources": list(self.sources),
            "complete": bool(self.complete),
            "missing": list(self.missing),
        }


def digest_swarm(source: Any) -> SwarmDigest:
    """The digest one swarm yields, derived from its findings alone.

    Accepts a ResearchSwarm or a ResearchSwarmRegistry.
    The answer joins the findings' summaries in
    assignment order - the dealt order, not the
    order findings happened to arrive - and the
    sources are every source the findings cite,
    each once, in that same order. The digest is
    complete exactly when no assignment is missing
    its finding.
    """
    if isinstance(source, ResearchSwarmRegistry):
        swarm = source.swarm()
    elif isinstance(source, ResearchSwarm):
        swarm = source
    else:
        raise ValueError(f"a research swarm is needed, got {source!r}")
    assert swarm.question is not None
    ordered = []
    for assignment in swarm.assignments:
        for finding in swarm.findings:
            if finding.member == assignment.member:
                ordered.append(finding)
                break
    answer = " ".join(finding.summary for finding in ordered)
    if not answer:
        answer = "No findings have come back yet."
    sources: list = []
    for finding in ordered:
        for source_name in finding.sources:
            if source_name not in sources:
                sources.append(source_name)
    missing = swarm.missing_members()
    return SwarmDigest(
        question=swarm.question.text, answer=answer,
        sources=tuple(sources), complete=not missing,
        missing=missing)


def validate_digest(digest: Any, swarm: Any = None) -> SwarmDigest:
    """Validate one digest into a SwarmDigest.

    Accepts a SwarmDigest or a mapping naming a
    ``question``, an ``answer``, ``sources``, a
    ``complete`` word and the ``missing`` members
    (or ``missing_members``). When *swarm* is
    given, the digest is also judged against the
    digest that swarm derives: any disagreement
    refuses, because a digest is derived, never
    stored.
    """
    if isinstance(digest, SwarmDigest):
        current = digest
    elif isinstance(digest, dict):
        unknown = set(digest) - _DIGEST_KEYS
        if unknown:
            raise ValueError(
                "unknown digest keys: %s" % ", ".join(sorted(unknown)))
        if "question" not in digest or "answer" not in digest:
            raise ValueError("a digest is missing its question or answer")
        missing = _pick_any(
            digest, ("missing", "missing_members"), "missing lists")
        current = SwarmDigest(
            question=digest["question"], answer=digest["answer"],
            sources=tuple(digest.get("sources") or ()),
            complete=bool(digest.get("complete", False)),
            missing=tuple(missing or ()))
    else:
        raise ValueError(f"a digest must be a mapping, got {digest!r}")
    if swarm is not None:
        derived = digest_swarm(swarm)
        if current != derived:
            raise ValueError(
                "a stored digest disagrees with the digest its "
                "swarm derives - a digest is derived, never stored")
    return current


def build_digest(
        digest: Any = None, **kwargs: Any) -> SwarmDigest:
    """Build one validated digest.

    From a SwarmDigest, from a mapping (the
    spellings :func:`validate_digest` reads), or
    from field words given as keyword arguments.
    """
    if isinstance(digest, SwarmDigest) and not kwargs:
        return digest
    if isinstance(digest, dict) or digest is None:
        merged: Dict[str, Any] = {}
        if isinstance(digest, dict):
            merged.update(digest)
        merged.update(kwargs)
        return validate_digest(merged)
    raise ValueError(f"a digest must be a mapping, got {digest!r}")


# ---------------------------------------------------------------------
# The registry model: a swarm held piece by piece, in order, with
# deterministic ids. A registry refuses a supplied id already held,
# a member dealt twice and a member reporting twice: repetition
# here is a second dealing for one member, not two pieces of a
# swarm, so it is refused, never hidden.
# ---------------------------------------------------------------------


class ResearchSwarmRegistry:
    """One session's swarm, held piece by piece."""

    def __init__(self, question: Any = None) -> None:
        self._question: Optional[SwarmQuestion] = (
            build_question(question) if question is not None else None)
        self._assignments: Dict[str, SwarmAssignment] = {}
        self._findings: Dict[str, SwarmFinding] = {}
        self._next_assignment = 1
        self._next_finding = 1

    def hold_question(self, question: Any) -> SwarmQuestion:
        """Hold the swarm's one question; a second refuses."""
        validated = build_question(question)
        if self._question is not None:
            raise ValueError("a swarm holds one question only")
        if validated.question_id is None:
            validated = replace(validated, question_id="question-1")
        self._question = validated
        return validated

    def question(self) -> SwarmQuestion:
        """The held question; none held raises."""
        if self._question is None:
            raise KeyError("no question is held in this registry")
        return self._question

    def _fresh_assignment_id(self) -> str:
        while f"assignment-{self._next_assignment}" in self._assignments:
            self._next_assignment += 1
        fresh = f"assignment-{self._next_assignment}"
        self._next_assignment += 1
        return fresh

    def _fresh_finding_id(self) -> str:
        while f"finding-{self._next_finding}" in self._findings:
            self._next_finding += 1
        fresh = f"finding-{self._next_finding}"
        self._next_finding += 1
        return fresh

    def register_assignment(self, assignment: Any) -> SwarmAssignment:
        """Register one assignment and hold it."""
        validated = build_assignment(assignment)
        for held in self._assignments.values():
            if held.member == validated.member:
                raise ValueError(
                    f"a member is dealt twice: {validated.member} "
                    f"holds two assignments")
        if validated.assignment_id is not None \
                and validated.assignment_id in self._assignments:
            raise ValueError(
                f"an assignment named {validated.assignment_id!r} "
                f"already exists")
        if validated.assignment_id is None:
            validated = replace(
                validated, assignment_id=self._fresh_assignment_id())
        self._assignments[validated.assignment_id] = validated
        return validated

    def register_finding(self, finding: Any) -> SwarmFinding:
        """Register one finding and hold it.

        The finding's member must hold an assignment
        in this registry - nobody reports on a focus
        they were not dealt.
        """
        validated = build_finding(finding)
        dealt = {held.member for held in self._assignments.values()}
        if validated.member not in dealt:
            raise ValueError(
                f"a finding from {validated.member!r}, who holds "
                f"no assignment in this swarm, refuses")
        for held in self._findings.values():
            if held.member == validated.member:
                raise ValueError(
                    f"a member reports twice: {validated.member} "
                    f"holds two findings")
        if validated.finding_id is not None \
                and validated.finding_id in self._findings:
            raise ValueError(
                f"a finding named {validated.finding_id!r} "
                f"already exists")
        if validated.finding_id is None:
            validated = replace(
                validated, finding_id=self._fresh_finding_id())
        self._findings[validated.finding_id] = validated
        return validated

    def register_swarm(self, swarm: Any) -> ResearchSwarm:
        """Register every piece of one swarm, in order."""
        if not isinstance(swarm, ResearchSwarm):
            raise ValueError(f"a research swarm is needed, got {swarm!r}")
        self.hold_question(swarm.question)
        for assignment in swarm.assignments:
            self.register_assignment(assignment)
        for finding in swarm.findings:
            self.register_finding(finding)
        return self.swarm()

    def get_assignment(self, assignment_id: Any) -> SwarmAssignment:
        """The assignment one id names; an unknown id raises."""
        wanted = normalize_member_id(assignment_id)
        if wanted not in self._assignments:
            raise KeyError(f"unknown assignment: {wanted!r}")
        return self._assignments[wanted]

    def get_finding(self, finding_id: Any) -> SwarmFinding:
        """The finding one id names; an unknown id raises."""
        wanted = normalize_member_id(finding_id)
        if wanted not in self._findings:
            raise KeyError(f"unknown finding: {wanted!r}")
        return self._findings[wanted]

    def list_assignments(self) -> Tuple[SwarmAssignment, ...]:
        """Every held assignment, in registration order."""
        return tuple(self._assignments.values())

    def list_findings(self) -> Tuple[SwarmFinding, ...]:
        """Every held finding, in registration order."""
        return tuple(self._findings.values())

    def assignments_for(self, member: Any) -> Tuple[SwarmAssignment, ...]:
        """Every held assignment of one member (at most one)."""
        wanted = normalize_member_id(member)
        return tuple(
            held for held in self._assignments.values()
            if held.member == wanted)

    def findings_for(self, member: Any) -> Tuple[SwarmFinding, ...]:
        """Every held finding of one member (at most one)."""
        wanted = normalize_member_id(member)
        return tuple(
            held for held in self._findings.values()
            if held.member == wanted)

    def swarm(self) -> ResearchSwarm:
        """The held pieces as one validated swarm."""
        question = self.question()
        return ResearchSwarm(
            question=question,
            assignments=self.list_assignments(),
            findings=self.list_findings(),
            leader=question.leader)

    def digest(self) -> SwarmDigest:
        """The digest the held swarm yields."""
        return digest_swarm(self.swarm())


# ---------------------------------------------------------------------
# Swarm news, shaped as session records.
# ---------------------------------------------------------------------


def question_record(question: Any) -> Dict[str, Any]:
    """The session-news record of one question."""
    current = question if isinstance(
        question, SwarmQuestion) else build_question(question)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"A research swarm is asked, led by {current.leader}: "
        f"{current.text}")
    return record


def assignment_record(assignment: Any) -> Dict[str, Any]:
    """The session-news record of one assignment."""
    current = assignment if isinstance(
        assignment, SwarmAssignment) else build_assignment(assignment)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.member} is dealt the {current.focus} "
        f"focus of the swarm.")
    return record


def finding_record(finding: Any) -> Dict[str, Any]:
    """The session-news record of one finding."""
    current = finding if isinstance(
        finding, SwarmFinding) else build_finding(finding)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.member} reports back to the swarm "
        f"on {len(current.sources)} source(s).")
    return record


def digest_record(digest: Any) -> Dict[str, Any]:
    """The session-news record of one digest."""
    current = digest if isinstance(
        digest, SwarmDigest) else build_digest(digest)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        "The swarm's digested answer is complete."
        if current.complete else
        "The swarm's digest is still out: "
        + ", ".join(current.missing) + " to report.")
    return record


def plain_words(question: Any) -> str:
    """One question, in one plain sentence."""
    current = question if isinstance(
        question, SwarmQuestion) else build_question(question)
    return f"Led by {current.leader}: {current.text}"


def digest_plain_words(digest: Any) -> str:
    """One digest, in one plain sentence."""
    current = digest if isinstance(
        digest, SwarmDigest) else build_digest(digest)
    if current.complete:
        return (
            f"Complete, on {len(current.sources)} source(s): "
            f"{current.answer}")
    return (
        f"Still out ({', '.join(current.missing)}): "
        f"{current.answer}")


# ---------------------------------------------------------------------
# Screens: the formatters and the shared /swarm grammar.
# ---------------------------------------------------------------------


def _source_swarm(source: Any) -> ResearchSwarm:
    if source is None:
        return load_research_swarm()
    if isinstance(source, ResearchSwarmRegistry):
        return source.swarm()
    if isinstance(source, ResearchSwarm):
        return source
    raise ValueError(f"a research swarm is needed, got {source!r}")


def format_finding(finding: Any) -> str:
    """One finding as a screen line, with its sources."""
    current = finding if isinstance(
        finding, SwarmFinding) else build_finding(finding)
    return (
        f"{current.member}: {current.summary} "
        f"[sources: {'; '.join(current.sources)}]")


def format_findings(source: Any = None) -> str:
    """Every finding of one swarm, in assignment order."""
    swarm = _source_swarm(source)
    lines = []
    for assignment in swarm.assignments:
        try:
            finding = swarm.finding_for(assignment.member)
        except KeyError:
            lines.append(
                f"{assignment.member} "
                f"({assignment.focus}): still out.")
        else:
            lines.append(
                f"{assignment.focus} - " + format_finding(finding))
    return "\n".join(lines) if lines else "No assignments are held."


def format_digest(source: Any = None) -> str:
    """One swarm's digested answer, with its sources."""
    digest = digest_swarm(_source_swarm(source))
    lines = [digest_plain_words(digest), "Sources:"]
    lines.extend(f"- {name}" for name in digest.sources)
    return "\n".join(lines)


def format_focus_kinds() -> str:
    """The three focus kinds, in roadmap order."""
    return "Focus kinds: " + ", ".join(FOCUS_KINDS)


def format_swarm_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /swarm.

    With nothing named, the shipped example
    swarm's digest is shown - the example this
    slice ships - so the screen is never empty.
    There is no Part VIII board yet; this screen
    is where the digest is visible.
    """
    swarm = _source_swarm(source)
    lines = ["Research swarms (M-131) - " + PLAIN_EXPLANATION, ""]
    lines.append(plain_words(swarm.question))
    lines.append("")
    lines.append(format_findings(swarm))
    lines.append("")
    lines.append(format_digest(swarm))
    lines.append("")
    lines.append(format_focus_kinds())
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_swarm_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /swarm grammar both surfaces share.

    No words (or ``show`` / ``list`` / ``findings``)
    shows the swarm; ``show <member>`` and a bare
    member id show one member's finding;
    ``digest`` shows the digested answer;
    ``sources`` shows the digest's sources;
    ``kinds`` asks for the focus kinds. Anything
    else is a usage error naming the grammar.
    Returns ``(action, value-or-None)``.
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
    if head == "digest" and len(words) == 1:
        return ("digest", None)
    if head == "sources" and len(words) == 1:
        return ("sources", None)
    if head == "kinds" and len(words) == 1:
        return ("kinds", None)
    if head in ("show", "digest", "sources", "kinds",
                "list", "findings"):
        raise ValueError(USAGE)
    if len(words) == 1:
        try:
            return ("show", normalize_member_id(words[0]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
