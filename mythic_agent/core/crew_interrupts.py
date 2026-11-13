"""Crew interrupts with grace (All-Features roadmap slice M-144).

Part VI continues here. The roadmap's words:
``pausing one member, the whole crew, or one
slice - each leaves its worktree and journal
consistent.``

What already shipped, and what this slice adds:

* The crew itself is already data
  (``core/crew_members.py``, M-121): a member a
  pause names is that casting's own member, read
  by its ``normalize_member_id`` by import. A
  slice a pause names is a roadmap slice id as
  the worktree layer reads one
  (``core/worktrees.py``, M-124): its
  ``normalize_slice_id`` is composed by import
  too, so a paused slice answers to exactly the
  reading a worktree assignment answers to.
* The pieces a graceful pause must leave
  consistent already exist as live roads, and
  were read, not composed: named checkpoints
  (``core/checkpoints.py``, M-075) capture the
  working tree plus session state and judge a
  tree clean exactly when it matches the head
  checkpoint - a live store whose take / restore
  acts in the world, not a data vocabulary; the
  write-ahead journal (``core/journal.py``)
  is the live durability mechanism behind
  session checkpoints, its entries pending until
  committed - again a mechanism, not a record
  shape; the session store
  (``core/sessions.py``) is a live store whose
  ``interrupted`` status is a session lifecycle
  word (a process that ended during a turn), not
  a crew pause; the kill switch
  (``core/kill_switch.py``, M-108) is one halt
  for everything - instant and total - which is
  a different act from a graceful pause that
  lands at a resting point; and the budgets
  layer (``core/budgets.py``, M-107) already
  speaks of a graceful pause at a resting point,
  never a mid-edit death - the prose precedent
  for this slice's pause-point reading - but its
  pause is a budget verdict's record, not a
  pause of a member, a crew or a slice. Crew
  templates (``core/crew_templates.py``, M-143)
  were read too: a template names a formation
  that is summoned by name, while an interrupt
  names a scope - one member, the whole crew or
  one slice - so no formation record is composed
  here either. What nothing holds is the
  interrupt itself, as data: a named pause, its
  scope, and the worktree / journal / pause-point
  readings it was taken under, from which alone
  its consistency is judged.
* This slice is that interrupt book, as a pure
  layer: an interrupt record validated as data
  (one graceful pause, named in plain words,
  naming its scope and the readings it rests
  on), a consistency report per interrupt whose
  checks, consistency and account are DERIVED
  from the record's readings, an interrupt index
  whose rows, totals and account are DERIVED
  from the whole book, the shipped data file
  (``mythic_agent/data/crew_interrupts.yaml``)
  holding one example interrupt book in exactly
  the shape a real interrupt file takes, a
  loader for an interrupt file anywhere on
  disk, records shaped as session news, and a
  small in-memory registry model. This module
  pauses no member, halts no crew, signals no
  process, touches no worktree, writes no
  journal and imports no agent / UI code; the
  agent layer owns holding an interrupt book
  for a session and carrying a pause out.

Honesty rules, enforced here and pinned by tests:

* **Consistency is derived, never stored
  loose.** An interrupt record names its
  worktree reading (clean, checkpointed or
  dirty), its journal reading (flushed or
  pending) and its pause point (a resting point
  or mid-edit), and no consistency of its own:
  whether the pause leaves its worktree and
  journal consistent is read off those readings
  at call time, so a stored ``consistent`` /
  ``consistency`` / ``status`` / ``graceful``
  key on a record refuses as an unknown key,
  and no record can claim a grace its readings
  do not give it.
* **Scope and target stand together.** A
  member pause names exactly one member of the
  shipped casting and no slice; a slice pause
  names exactly one roadmap slice and no
  member; a crew pause names neither - its
  target is the whole crew. A record whose
  target disagrees with its scope refuses.
* **A report is derived, never stored loose.**
  A consistency report's checks, consistency
  and account are read off its interrupt's
  readings, in held order, so a stored report
  that disagrees with the report derived from
  its interrupt refuses. A report naming no
  account of its own refuses too.
* **The index is derived, never stored
  loose.** The index's rows are the book's
  reports, in held order; its totals are read
  off the records (every interrupt held, those
  leaving things consistent, those not yet) and
  its account is read off the rows and totals,
  so a stored index whose rows, totals or
  account disagree with the derived index
  refuses.
* **Targets are the shipped layers' own.** A
  member reads exactly as the M-121 layer reads
  one and a slice exactly as the M-124 layer
  reads one, both composed by import, so every
  target answers to exactly the validator the
  live roads answer to.
* **Data only - no live road is claimed.** An
  interrupt here is a validated record held as
  data: no member is paused, no crew is halted,
  no process is signalled, no worktree is
  touched, no journal is written and nothing is
  persisted. The pauses are visible through
  this slice's own /interrupts screen.
* **Malformed refuses.** A duplicate interrupt
  id in one book, a report or index naming an
  interrupt the book holds no record for, and
  unknown keys in a record, a report, an index
  or an interrupt mapping all raise instead of
  being skipped or guessed at.
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
    "CREW_INTERRUPTS_RESOURCE",
    "CREW_INTERRUPTS_SCHEMA",
    "CREW_INTERRUPTS_SLICE",
    "JOURNAL_STATES",
    "PAUSE_POINTS",
    "SCOPES",
    "USAGE",
    "WORKTREE_STATES",
    "ConsistencyReport",
    "CrewInterrupt",
    "CrewInterruptBook",
    "InterruptIndex",
    "InterruptRegistry",
    "book_record",
    "build_book",
    "build_index",
    "build_interrupt",
    "build_report",
    "derive_index",
    "derive_report",
    "format_crew_interrupts_screen",
    "format_index",
    "format_interrupt",
    "format_interrupts",
    "format_report",
    "index_plain_words",
    "index_record",
    "interrupt_record",
    "load_crew_interrupts",
    "load_crew_interrupts_file",
    "normalize_journal_state",
    "normalize_pause_point",
    "normalize_scope",
    "normalize_worktree_state",
    "parse_crew_interrupts_args",
    "plain_words",
    "report_plain_words",
    "report_record",
    "validate_book",
    "validate_index",
    "validate_interrupt",
    "validate_report",
]

CREW_INTERRUPTS_SLICE = "M-144"

#: The packaged data resource holding the example book.
CREW_INTERRUPTS_RESOURCE = "crew_interrupts.yaml"

#: The schema word a crew interrupts file must carry.
CREW_INTERRUPTS_SCHEMA = "mythic.crew_interrupts/1"

#: The scopes a pause may name, in roadmap order:
#: one member, the whole crew, or one slice.
SCOPES = ("member", "crew", "slice")

#: The worktree readings a pause may rest on: the
#: tree as it stands at the pause - clean or held
#: at a checkpoint leaves it consistent; dirty
#: does not.
WORKTREE_STATES = ("clean", "checkpointed", "dirty")

#: The journal readings a pause may rest on:
#: flushed leaves the journal consistent; an
#: entry still pending does not.
JOURNAL_STATES = ("flushed", "pending")

#: The points a pause may be taken at: a resting
#: point is a graceful pause; mid-edit is not.
PAUSE_POINTS = ("resting", "mid_edit")

_INTERRUPT_KEYS = frozenset({
    "interrupt_id", "id", "scope", "kind", "target_kind",
    "title", "headline", "detail", "description", "reason",
    "member", "member_id", "slice_id", "slice",
    "worktree", "worktree_state", "tree_state",
    "journal", "journal_state",
    "point", "resting_point", "pause_point",
})

_REPORT_KEYS = frozenset({
    "report_id", "id", "interrupt_id",
    "scope", "kind", "member", "member_id",
    "slice_id", "slice", "checks", "findings",
    "consistent", "is_consistent",
    "account", "statements",
})

_INDEX_KEYS = frozenset({
    "index_id", "id", "rows", "reports",
    "total_interrupts", "interrupts",
    "total_consistent", "consistent",
    "total_inconsistent", "inconsistent",
    "account", "statements",
})

_BOOK_KEYS = frozenset({"title", "name"})

_CREW_INTERRUPTS_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "interrupts_note", "guide", "entries", "indexes",
})

#: The shipped example book's title, held to this
#: by the loader's example check.
_EXAMPLE_TITLE = "Crew interrupt book at the M-143 slice boundary"

#: The shipped example's interrupt ids, in held
#: order, pinned by the loader.
_EXAMPLE_INTERRUPT_IDS = (
    "int-auditor-rest", "int-crew-rest",
    "int-slice-m143", "int-forge-worker-mid-edit")

#: The shipped example's scopes, in held order,
#: pinned by the loader: the roadmap's three
#: scopes, with the member scope standing twice.
_EXAMPLE_SCOPES = ("member", "crew", "slice", "member")

#: The shipped example's derived consistency, in
#: held order, pinned by the loader: three pauses
#: leave their worktree and journal consistent,
#: and the mid-edit pause honestly does not.
_EXAMPLE_CONSISTENCY = (True, True, True, False)

#: The shipped example's one index: its rows are
#: the interrupts in held order and its totals
#: are pinned by the loader.
_EXAMPLE_INDEX_ID = "index-m143-boundary"

_EXAMPLE_INDEX_ROWS = ("member", "crew", "slice", "member")

_EXAMPLE_INDEX_TOTALS = (4, 3, 1)

_EXAMPLE_INDEX_ACCOUNT = (
    "The book holds 4 crew interrupt(s): 3 leave "
    "the worktree and journal consistent, 1 do "
    "not yet.",
    "Every consistency word here is derived from "
    "the held records' worktree, journal and "
    "pause-point readings, never stored loose.",
    "An interrupt here is a record of a graceful "
    "pause; nothing in this book pauses a member, "
    "a crew or a slice.",
)

#: The shipped example's pinned first report: the
#: auditor pause's checks read off its readings,
#: its account pinned word-for-word by the loader.
_EXAMPLE_FIRST_REPORT_CHECKS = (
    "worktree clean: consistent",
    "journal flushed: consistent",
    "pause at a resting point: consistent",
)

_EXAMPLE_FIRST_REPORT_ACCOUNT = (
    "Pausing member auditor leaves its worktree "
    "and journal consistent.",
    "The pause lands at a resting point with the "
    "worktree clean or checkpointed and the "
    "journal flushed.",
    "This record pauses no one: it is data only, "
    "and no process is signalled by this layer.",
)

PLAIN_EXPLANATION = (
    "Crew interrupts with grace: pausing one "
    "member, the whole crew, or one slice - each "
    "leaves its worktree and journal consistent. "
    "An interrupt record names one pause in plain "
    "words, its scope and target, and the "
    "worktree, journal and pause-point readings "
    "it rests on. Whether the pause leaves things "
    "consistent is derived from those readings, "
    "never stored loose, and the consistency "
    "reports and the interrupt index are read off "
    "the held records, so a stored form that "
    "disagrees refuses. This layer holds "
    "interrupts as data only; it pauses no "
    "member, halts no crew, signals no process, "
    "touches no worktree, writes no journal and "
    "persists nothing itself."
)

USAGE = (
    "Usage: /interrupts, /interrupts show, "
    "/interrupts interrupt <interrupt-id>, "
    "/interrupts member <member-id>, "
    "/interrupts slice <slice-id>, "
    "/interrupts report <interrupt-id>, "
    "/interrupts index"
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


def _check_count(value: Any, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{what} must be a count, got {value!r}")
    if value < 0:
        raise ValueError(f"{what} must not be negative, got {value!r}")
    return value


def _check_bool(value: Any, what: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{what} must be true or false, got {value!r}")
    return value


def _normalize_word(value: Any, words: Tuple[str, ...],
                    what: str) -> str:
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted in words:
            return wanted
    raise ValueError(
        "a %s must be one of %s, got %r"
        % (what, "/".join(words), value))


def normalize_scope(value: Any) -> str:
    """The canonical pause scope a word names.

    A scope is ``member`` (one member of the
    crew), ``crew`` (the whole crew) or ``slice``
    (one slice of the road), read
    case-insensitively with dashes read as
    underscores. Anything else raises.
    """
    return _normalize_word(value, SCOPES, "pause scope")


def normalize_worktree_state(value: Any) -> str:
    """The canonical worktree reading a word names."""
    return _normalize_word(value, WORKTREE_STATES, "worktree reading")


def normalize_journal_state(value: Any) -> str:
    """The canonical journal reading a word names."""
    return _normalize_word(value, JOURNAL_STATES, "journal reading")


def normalize_pause_point(value: Any) -> str:
    """The canonical pause point a word names."""
    return _normalize_word(value, PAUSE_POINTS, "pause point")


def _worktree_check(state: str) -> str:
    if state == "dirty":
        return "worktree dirty: not consistent"
    return f"worktree {state}: consistent"


def _journal_check(state: str) -> str:
    if state == "pending":
        return "journal pending: not consistent"
    return "journal flushed: consistent"


def _point_check(point: str) -> str:
    if point == "mid_edit":
        return "pause taken mid-edit: not consistent"
    return "pause at a resting point: consistent"


#: Every check phrase a report may carry, in the
#: order a report carries them: worktree, journal,
#: pause point - each ending in its verdict.
_CHECK_SETS = (
    frozenset({
        "worktree clean: consistent",
        "worktree checkpointed: consistent",
        "worktree dirty: not consistent"}),
    frozenset({"journal flushed: consistent",
               "journal pending: not consistent"}),
    frozenset({"pause at a resting point: consistent",
               "pause taken mid-edit: not consistent"}),
)


def _check_checks(value: Any) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes)) \
            or not isinstance(value, (list, tuple)):
        raise ValueError(f"a report's checks must be a list, got {value!r}")
    checks = tuple(
        _check_long_text(c, "a report check") for c in value)
    if len(checks) != 3:
        raise ValueError(
            "a consistency report carries exactly three "
            "checks: worktree, journal and pause point")
    for check, allowed in zip(checks, _CHECK_SETS):
        if check not in allowed:
            raise ValueError(
                f"a report check names no known reading: {check!r}")
    return checks


def _target_label(scope: str, member: Optional[str],
                  slice_id: Optional[str]) -> str:
    if scope == "member":
        return f"member {member}"
    if scope == "slice":
        return f"slice {slice_id}"
    return "the whole crew"


def _check_scope_target(scope: str, member: Optional[str],
                        slice_id: Optional[str]) -> None:
    if scope == "member" and member is None:
        raise ValueError("a member pause names the member it pauses")
    if scope == "member" and slice_id is not None:
        raise ValueError("a member pause names no slice")
    if scope == "slice" and slice_id is None:
        raise ValueError("a slice pause names the slice it pauses")
    if scope == "slice" and member is not None:
        raise ValueError("a slice pause names no member")
    if scope == "crew" and (member is not None or slice_id is not None):
        raise ValueError(
            "a crew pause names neither a member nor a "
            "slice: its target is the whole crew")


# ---------------------------------------------------------------------
# The interrupt record: one graceful pause, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CrewInterrupt:
    """One graceful pause of a member, the crew or a slice.

    ``scope`` says what is paused - one ``member``,
    the whole ``crew`` or one ``slice`` - and the
    target stands with the scope: a member pause
    names its ``member`` (a member of the shipped
    casting), a slice pause names its ``slice_id``
    (a roadmap slice) and a crew pause names
    neither. ``title`` names the pause in plain
    words and ``detail`` says why it is taken.
    ``worktree`` / ``journal`` / ``point`` are the
    readings the pause rests on: the worktree as it
    stands, the journal's flush state, and the
    point the pause is taken at. The record names
    NO consistency and NO status of its own: both
    are read off the readings, so a record can
    never claim a grace its readings do not give.
    """

    scope: str
    title: str
    detail: str
    worktree: str
    journal: str
    point: str
    member: Optional[str] = None
    slice_id: Optional[str] = None
    interrupt_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.interrupt_id is not None:
            object.__setattr__(
                self, "interrupt_id",
                normalize_member_id(self.interrupt_id))
        object.__setattr__(self, "scope", normalize_scope(self.scope))
        object.__setattr__(
            self, "title", _check_title(self.title, "an interrupt's title"))
        object.__setattr__(
            self, "detail",
            _check_long_text(self.detail, "an interrupt's detail"))
        object.__setattr__(
            self, "worktree", normalize_worktree_state(self.worktree))
        object.__setattr__(
            self, "journal", normalize_journal_state(self.journal))
        object.__setattr__(
            self, "point", normalize_pause_point(self.point))
        if self.member is not None:
            object.__setattr__(
                self, "member", normalize_member_id(self.member))
        if self.slice_id is not None:
            object.__setattr__(
                self, "slice_id", normalize_slice_id(self.slice_id))
        _check_scope_target(self.scope, self.member, self.slice_id)

    @property
    def target(self) -> str:
        """What this pause names, derived from its scope."""
        if self.scope == "member":
            return self.member or ""
        if self.scope == "slice":
            return self.slice_id or ""
        return "crew"

    @property
    def checks(self) -> Tuple[str, ...]:
        """The consistency checks, derived from the readings."""
        return (
            _worktree_check(self.worktree),
            _journal_check(self.journal),
            _point_check(self.point))

    @property
    def consistent(self) -> bool:
        """Whether the pause leaves things consistent, derived."""
        return (
            self.worktree in ("clean", "checkpointed")
            and self.journal == "flushed"
            and self.point == "resting")

    @property
    def status(self) -> str:
        """The pause's standing, derived from its readings."""
        return "consistent" if self.consistent else "inconsistent"

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "crew_interrupt",
            "slice": CREW_INTERRUPTS_SLICE,
            "interrupt_id": self.interrupt_id,
            "scope": self.scope,
            "target": self.target,
            "title": self.title,
            "detail": self.detail,
            "member": self.member,
            "slice_id": self.slice_id,
            "worktree": self.worktree,
            "journal": self.journal,
            "point": self.point,
            "checks": list(self.checks),
            "consistent": self.consistent,
            "status": self.status,
        }


def validate_interrupt(interrupt: Any) -> CrewInterrupt:
    """Validate one interrupt record into a CrewInterrupt.

    Accepts a CrewInterrupt or a mapping naming a
    ``scope`` (or ``kind`` / ``target_kind``), a
    ``title`` (or ``headline``), a ``detail`` (or
    ``description`` / ``reason``), a ``worktree``
    (or ``worktree_state`` / ``tree_state``), a
    ``journal`` (or ``journal_state``), a ``point``
    (or ``resting_point`` / ``pause_point``), an
    optional ``interrupt_id`` (or ``id``), the
    ``member`` (or ``member_id``) a member pause
    names and the ``slice_id`` (or ``slice``) a
    slice pause names. Naming two spellings of
    one field with different values refuses, and
    unknown keys refuse - a stored consistency
    key among them, because consistency is
    derived from the readings, never stored on a
    record.
    """
    if isinstance(interrupt, CrewInterrupt):
        return interrupt
    if not isinstance(interrupt, dict):
        raise ValueError(
            f"an interrupt record must be a mapping, "
            f"got {interrupt!r}")
    unknown = set(interrupt) - _INTERRUPT_KEYS
    if unknown:
        raise ValueError(
            "unknown interrupt-record keys: %s"
            % ", ".join(sorted(unknown)))
    scope = _pick_any(
        interrupt, ("scope", "kind", "target_kind"), "scopes")
    if scope is None:
        raise ValueError("an interrupt record is missing its scope")
    title = _pick_any(interrupt, ("title", "headline"), "titles")
    if title is None:
        raise ValueError("an interrupt record is missing its title")
    detail = _pick_any(
        interrupt, ("detail", "description", "reason"), "details")
    if detail is None:
        raise ValueError("an interrupt record is missing its detail")
    worktree = _pick_any(
        interrupt, ("worktree", "worktree_state", "tree_state"),
        "worktree readings")
    if worktree is None:
        raise ValueError("an interrupt record is missing its worktree")
    journal = _pick_any(
        interrupt, ("journal", "journal_state"), "journal readings")
    if journal is None:
        raise ValueError("an interrupt record is missing its journal")
    point = _pick_any(
        interrupt, ("point", "resting_point", "pause_point"),
        "pause points")
    if point is None:
        raise ValueError("an interrupt record is missing its point")
    kwargs: Dict[str, Any] = {
        "scope": scope, "title": title, "detail": detail,
        "worktree": worktree, "journal": journal, "point": point}
    interrupt_id = _pick_any(
        interrupt, ("interrupt_id", "id"), "interrupt ids")
    if interrupt_id is not None:
        kwargs["interrupt_id"] = interrupt_id
    member = _pick_any(interrupt, ("member", "member_id"), "members")
    if member is not None:
        kwargs["member"] = member
    slice_id = _pick_any(
        interrupt, ("slice_id", "slice"), "slice ids")
    if slice_id is not None:
        kwargs["slice_id"] = slice_id
    return CrewInterrupt(**kwargs)


def build_interrupt(interrupt: Any = None, **kwargs: Any) -> CrewInterrupt:
    """Build one validated interrupt record, from a mapping or field words."""
    if isinstance(interrupt, CrewInterrupt) and not kwargs:
        return interrupt
    if isinstance(interrupt, dict) or interrupt is None:
        merged: Dict[str, Any] = {}
        if isinstance(interrupt, dict):
            merged.update(interrupt)
        merged.update(kwargs)
        return validate_interrupt(merged)
    raise ValueError(
        f"an interrupt record must be a mapping, got {interrupt!r}")


def _check_interrupt_ref(value: Any) -> CrewInterrupt:
    if isinstance(value, CrewInterrupt):
        return value
    if isinstance(value, dict):
        return validate_interrupt(value)
    raise ValueError(f"an interrupt record is needed, got {value!r}")


def _held_interrupts(source: Any) -> Tuple[CrewInterrupt, ...]:
    """The interrupt records one source holds, in held order."""
    if isinstance(source, CrewInterruptBook):
        return source.entries
    if isinstance(source, InterruptRegistry):
        return source.list_interrupts()
    if isinstance(source, (list, tuple)):
        return tuple(_check_interrupt_ref(e) for e in source)
    raise ValueError(f"interrupt records are needed, got {source!r}")


# ---------------------------------------------------------------------
# The consistency report: one pause judged, derived.
# ---------------------------------------------------------------------


def _report_account(scope: str, member: Optional[str],
                    slice_id: Optional[str],
                    checks: Tuple[str, ...],
                    consistent: bool) -> Tuple[str, ...]:
    label = _target_label(scope, member, slice_id)
    if consistent:
        return (
            f"Pausing {label} leaves its worktree "
            f"and journal consistent.",
            "The pause lands at a resting point with the "
            "worktree clean or checkpointed and the "
            "journal flushed.",
            "This record pauses no one: it is data only, "
            "and no process is signalled by this layer.",
        )
    failing = [c for c in checks if c.endswith(": not consistent")]
    return (
        f"Pausing {label} does not yet leave its "
        f"worktree and journal consistent.",
        "Not yet consistent: " + "; ".join(failing) + ".",
        "This record pauses no one: it is data only, "
        "and no process is signalled by this layer.",
    )


@dataclass(frozen=True)
class ConsistencyReport:
    """One pause's consistency report, derived from its readings.

    ``checks`` are the three readings judged, in
    worktree / journal / pause-point order, each
    ending in its verdict; ``consistent`` is true
    exactly when every check is consistent;
    ``account`` is the report's own account. Every
    field is a derivation: :func:`validate_report`
    judged against an interrupt refuses a report
    whose fields disagree with the report that
    interrupt derives.
    """

    scope: str
    checks: Tuple[str, ...] = ()
    consistent: bool = False
    account: Tuple[str, ...] = ()
    member: Optional[str] = None
    slice_id: Optional[str] = None
    interrupt_id: Optional[str] = None
    report_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.report_id is not None:
            object.__setattr__(
                self, "report_id", normalize_member_id(self.report_id))
        if self.interrupt_id is not None:
            object.__setattr__(
                self, "interrupt_id",
                normalize_member_id(self.interrupt_id))
        object.__setattr__(self, "scope", normalize_scope(self.scope))
        if self.member is not None:
            object.__setattr__(
                self, "member", normalize_member_id(self.member))
        if self.slice_id is not None:
            object.__setattr__(
                self, "slice_id", normalize_slice_id(self.slice_id))
        _check_scope_target(self.scope, self.member, self.slice_id)
        checks = _check_checks(self.checks)
        object.__setattr__(self, "checks", checks)
        object.__setattr__(
            self, "consistent",
            _check_bool(self.consistent, "a report's consistency"))
        derived = all(c.endswith(": consistent") for c in checks)
        if self.consistent != derived:
            raise ValueError(
                "a report's consistency must be its own "
                "checks' verdict")
        object.__setattr__(self, "account", _check_account(self.account))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "crew_interrupt_consistency",
            "slice": CREW_INTERRUPTS_SLICE,
            "report_id": self.report_id,
            "interrupt_id": self.interrupt_id,
            "scope": self.scope,
            "member": self.member,
            "slice_id": self.slice_id,
            "checks": list(self.checks),
            "consistent": self.consistent,
            "account": list(self.account),
        }


def derive_report(interrupt: Any) -> ConsistencyReport:
    """Derive one pause's consistency report from its record.

    The report's checks, consistency and account
    are read off the interrupt's worktree, journal
    and pause-point readings alone.
    """
    current = _check_interrupt_ref(interrupt)
    return ConsistencyReport(
        scope=current.scope,
        checks=current.checks,
        consistent=current.consistent,
        account=_report_account(
            current.scope, current.member, current.slice_id,
            current.checks, current.consistent),
        member=current.member,
        slice_id=current.slice_id,
        interrupt_id=current.interrupt_id)


def validate_report(report: Any, source: Any = None) -> ConsistencyReport:
    """Validate one consistency report into a ConsistencyReport.

    Accepts a ConsistencyReport or a mapping
    naming a ``scope``, ``checks`` (or
    ``findings``), a ``consistent`` (or
    ``is_consistent``), an ``account`` (or
    ``statements``) and optional ``member``,
    ``slice_id``, ``interrupt_id`` and
    ``report_id`` (or ``id``) spellings. With
    *source* given (one interrupt record), the
    report is judged against the report derived
    from that interrupt: a stored report whose
    scope, target, checks, consistency or
    account disagree with the derived report
    refuses. A report naming no account refuses
    too.
    """
    if isinstance(report, ConsistencyReport):
        current = report
    elif isinstance(report, dict):
        unknown = set(report) - _REPORT_KEYS
        if unknown:
            raise ValueError(
                "unknown report keys: %s" % ", ".join(sorted(unknown)))
        scope = _pick_any(report, ("scope", "kind"), "scopes")
        if scope is None:
            raise ValueError("a report is missing its scope")
        checks = _pick_any(report, ("checks", "findings"), "checks")
        if checks is None:
            raise ValueError("a report is missing its checks")
        consistent = _pick_any(
            report, ("consistent", "is_consistent"), "consistencies")
        if consistent is None:
            raise ValueError("a report is missing its consistency")
        account = _pick_any(report, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a report names no account of its own")
        kwargs: Dict[str, Any] = {
            "scope": scope, "checks": checks,
            "consistent": consistent, "account": account}
        member = _pick_any(report, ("member", "member_id"), "members")
        if member is not None:
            kwargs["member"] = member
        slice_id = _pick_any(report, ("slice_id", "slice"), "slice ids")
        if slice_id is not None:
            kwargs["slice_id"] = slice_id
        interrupt_id = _pick_any(
            report, ("interrupt_id",), "interrupt ids")
        if interrupt_id is not None:
            kwargs["interrupt_id"] = interrupt_id
        report_id = _pick_any(report, ("report_id", "id"), "report ids")
        if report_id is not None:
            kwargs["report_id"] = report_id
        current = ConsistencyReport(**kwargs)
    else:
        raise ValueError(f"a report must be a mapping, got {report!r}")
    if source is not None:
        derived = derive_report(source)
        if (current.scope != derived.scope
                or current.member != derived.member
                or current.slice_id != derived.slice_id
                or current.checks != derived.checks
                or current.consistent != derived.consistent
                or current.account != derived.account):
            raise ValueError(
                "a stored report disagrees with the report "
                "derived from its interrupt")
    return current


def build_report(report: Any = None, source: Any = None,
                 **kwargs: Any) -> ConsistencyReport:
    """Build one validated report, from a mapping or field words."""
    if isinstance(report, ConsistencyReport) and not kwargs:
        return validate_report(report, source)
    if isinstance(report, dict) or report is None:
        merged: Dict[str, Any] = {}
        if isinstance(report, dict):
            merged.update(report)
        merged.update(kwargs)
        return validate_report(merged, source)
    return validate_report(report, source)


# ---------------------------------------------------------------------
# The interrupt index: the whole book, derived.
# ---------------------------------------------------------------------


def _index_account(rows: Tuple[ConsistencyReport, ...],
                   total_interrupts: int, total_consistent: int,
                   total_inconsistent: int) -> Tuple[str, ...]:
    return (
        f"The book holds {total_interrupts} crew "
        f"interrupt(s): {total_consistent} leave "
        f"the worktree and journal consistent, "
        f"{total_inconsistent} do not yet.",
        "Every consistency word here is derived from "
        "the held records' worktree, journal and "
        "pause-point readings, never stored loose.",
        "An interrupt here is a record of a graceful "
        "pause; nothing in this book pauses a member, "
        "a crew or a slice.",
    )


def _check_report_ref(value: Any) -> ConsistencyReport:
    if isinstance(value, ConsistencyReport):
        return value
    if isinstance(value, dict):
        return validate_report(value)
    raise ValueError(f"a report is needed, got {value!r}")


@dataclass(frozen=True)
class InterruptIndex:
    """The interrupt index of one crew interrupt book.

    ``rows`` are the book's consistency reports,
    in held order; ``total_interrupts`` is every
    pause the book holds, ``total_consistent``
    those leaving their worktree and journal
    consistent and ``total_inconsistent`` those
    not yet, and ``account`` is read off the rows
    and totals. An index whose totals are not its
    own rows' counts refuses at construction.
    """

    rows: Tuple[ConsistencyReport, ...] = ()
    total_interrupts: int = 0
    total_consistent: int = 0
    total_inconsistent: int = 0
    account: Tuple[str, ...] = ()
    index_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.index_id is not None:
            object.__setattr__(
                self, "index_id", normalize_member_id(self.index_id))
        if isinstance(self.rows, (str, bytes)) \
                or not isinstance(self.rows, (list, tuple)):
            raise ValueError(
                f"an index's rows must be a list of reports, "
                f"got {self.rows!r}")
        rows = tuple(_check_report_ref(r) for r in self.rows)
        object.__setattr__(self, "rows", rows)
        object.__setattr__(
            self, "total_interrupts",
            _check_count(
                self.total_interrupts, "an index's total interrupts"))
        object.__setattr__(
            self, "total_consistent",
            _check_count(
                self.total_consistent, "an index's total consistent"))
        object.__setattr__(
            self, "total_inconsistent",
            _check_count(
                self.total_inconsistent, "an index's total inconsistent"))
        if self.total_interrupts != len(rows):
            raise ValueError(
                "an index's interrupt total must be its "
                "own rows' count")
        consistent = sum(1 for row in rows if row.consistent)
        if self.total_consistent != consistent:
            raise ValueError(
                "an index's consistent total must be its "
                "rows' consistent count")
        if self.total_inconsistent != len(rows) - consistent:
            raise ValueError(
                "an index's inconsistent total must be its "
                "rows' remaining count")
        object.__setattr__(self, "account", _check_account(self.account))

    def row_for(self, interrupt_id: Any) -> ConsistencyReport:
        """The row one interrupt id names in this index."""
        wanted = normalize_member_id(interrupt_id)
        for row in self.rows:
            if row.interrupt_id == wanted:
                return row
        raise KeyError(f"no row in the index: interrupt {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "crew_interrupt_index",
            "slice": CREW_INTERRUPTS_SLICE,
            "index_id": self.index_id,
            "rows": [row.to_record() for row in self.rows],
            "total_interrupts": self.total_interrupts,
            "total_consistent": self.total_consistent,
            "total_inconsistent": self.total_inconsistent,
            "account": list(self.account),
        }


def derive_index(source: Any) -> InterruptIndex:
    """Derive the interrupt index from interrupt records.

    The rows are the interrupts' consistency
    reports, in held order; the totals are the
    records' own derived counts and the account
    is read off the rows and totals. An empty
    source refuses - an index of nothing is no
    index.
    """
    entries = _held_interrupts(source)
    if not entries:
        raise ValueError("an index needs at least one interrupt record")
    rows = tuple(derive_report(entry) for entry in entries)
    total_consistent = sum(1 for entry in entries if entry.consistent)
    return InterruptIndex(
        rows=rows,
        total_interrupts=len(entries),
        total_consistent=total_consistent,
        total_inconsistent=len(entries) - total_consistent,
        account=_index_account(
            rows, len(entries), total_consistent,
            len(entries) - total_consistent))


def validate_index(index: Any, source: Any = None) -> InterruptIndex:
    """Validate one interrupt index into an InterruptIndex.

    Accepts an InterruptIndex or a mapping naming
    ``rows`` (or ``reports``),
    ``total_interrupts`` (or ``interrupts``),
    ``total_consistent`` (or ``consistent``),
    ``total_inconsistent`` (or ``inconsistent``),
    an ``account`` (or ``statements``) and an
    optional ``index_id`` (or ``id``). With
    *source* given, the index is judged against
    the index derived from those records: a
    stored index whose rows, totals or account
    disagree with the derived index refuses.
    """
    if isinstance(index, InterruptIndex):
        current = index
    elif isinstance(index, dict):
        unknown = set(index) - _INDEX_KEYS
        if unknown:
            raise ValueError(
                "unknown index keys: %s" % ", ".join(sorted(unknown)))
        rows = _pick_any(index, ("rows", "reports"), "rows")
        if rows is None:
            raise ValueError("an index is missing its rows")
        total_interrupts = _pick_any(
            index, ("total_interrupts", "interrupts"), "total interrupts")
        if total_interrupts is None:
            raise ValueError("an index is missing its total interrupts")
        total_consistent = _pick_any(
            index, ("total_consistent", "consistent"), "total consistent")
        if total_consistent is None:
            raise ValueError("an index is missing its total consistent")
        total_inconsistent = _pick_any(
            index, ("total_inconsistent", "inconsistent"),
            "total inconsistent")
        if total_inconsistent is None:
            raise ValueError("an index is missing its total inconsistent")
        account = _pick_any(index, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("an index names no account of its own")
        kwargs: Dict[str, Any] = {
            "rows": rows, "total_interrupts": total_interrupts,
            "total_consistent": total_consistent,
            "total_inconsistent": total_inconsistent,
            "account": account}
        index_id = _pick_any(index, ("index_id", "id"), "index ids")
        if index_id is not None:
            kwargs["index_id"] = index_id
        current = InterruptIndex(**kwargs)
    else:
        raise ValueError(f"an index must be a mapping, got {index!r}")
    if source is not None:
        derived = derive_index(source)
        if (current.rows != derived.rows
                or current.total_interrupts != derived.total_interrupts
                or current.total_consistent != derived.total_consistent
                or current.total_inconsistent != derived.total_inconsistent
                or current.account != derived.account):
            raise ValueError(
                "a stored index disagrees with the index "
                "derived from its records")
    return current


def build_index(index: Any = None, source: Any = None,
                **kwargs: Any) -> InterruptIndex:
    """Build one validated index, from a mapping or field words."""
    if isinstance(index, InterruptIndex) and not kwargs:
        return validate_index(index, source)
    if isinstance(index, dict) or index is None:
        merged: Dict[str, Any] = {}
        if isinstance(index, dict):
            merged.update(index)
        merged.update(kwargs)
        return validate_index(merged, source)
    return validate_index(index, source)


# ---------------------------------------------------------------------
# The interrupt book: pause records in held order, indexes judged.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CrewInterruptBook:
    """One crew interrupt book: graceful pauses, held whole.

    ``entries`` are the interrupt records, in held
    order; ``indexes`` are interrupt indexes of
    the book - derivations, judged against the
    book's records by :func:`validate_book`;
    ``interrupts_note`` is the book's own note.
    """

    title: str = ""
    entries: Tuple[CrewInterrupt, ...] = ()
    indexes: Tuple[InterruptIndex, ...] = ()
    interrupts_note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book's title"))
        if isinstance(self.entries, (str, bytes)) \
                or not isinstance(self.entries, (list, tuple)):
            raise ValueError(
                f"a book's entries must be a list of interrupt "
                f"records, got {self.entries!r}")
        entries = tuple(_check_interrupt_ref(e) for e in self.entries)
        if not entries:
            raise ValueError(
                "a crew interrupt book holds at least one "
                "interrupt record")
        seen_ids = set()
        for entry in entries:
            if entry.interrupt_id is not None:
                if entry.interrupt_id in seen_ids:
                    raise ValueError(
                        f"an interrupt record named "
                        f"{entry.interrupt_id!r} already exists")
                seen_ids.add(entry.interrupt_id)
        object.__setattr__(self, "entries", entries)
        if isinstance(self.indexes, (str, bytes)) \
                or not isinstance(self.indexes, (list, tuple)):
            raise ValueError(
                f"a book's indexes must be a list of indexes, "
                f"got {self.indexes!r}")
        indexes = tuple(
            idx if isinstance(idx, InterruptIndex)
            else validate_index(idx)
            for idx in self.indexes)
        seen_indexes = set()
        for index in indexes:
            if index.index_id is not None:
                if index.index_id in seen_indexes:
                    raise ValueError(
                        f"an index named {index.index_id!r} "
                        f"already exists")
                seen_indexes.add(index.index_id)
        object.__setattr__(self, "indexes", indexes)
        if not isinstance(self.interrupts_note, str):
            raise ValueError("a book's note must be text")
        object.__setattr__(
            self, "interrupts_note", self.interrupts_note.strip())

    def interrupt_for(self, interrupt_id: Any) -> CrewInterrupt:
        """The interrupt record one id names in this book."""
        wanted = normalize_member_id(interrupt_id)
        for entry in self.entries:
            if entry.interrupt_id == wanted:
                return entry
        raise KeyError(f"no interrupt record in the book: {wanted!r}")

    def interrupts_for_member(self, member: Any) -> Tuple[CrewInterrupt, ...]:
        """Every member pause naming one member, in held order."""
        wanted = normalize_member_id(member)
        return tuple(
            e for e in self.entries
            if e.scope == "member" and e.member == wanted)

    def interrupts_for_slice(self, slice_id: Any) -> Tuple[CrewInterrupt, ...]:
        """Every slice pause naming one slice, in held order."""
        wanted = normalize_slice_id(slice_id)
        return tuple(
            e for e in self.entries
            if e.scope == "slice" and e.slice_id == wanted)

    def interrupts_with_scope(self, scope: Any) -> Tuple[CrewInterrupt, ...]:
        """Every pause of one scope, in held order."""
        wanted = normalize_scope(scope)
        return tuple(e for e in self.entries if e.scope == wanted)

    def index_for(self, index_id: Any) -> InterruptIndex:
        """The index one id names in this book."""
        wanted = normalize_member_id(index_id)
        for index in self.indexes:
            if index.index_id == wanted:
                return index
        raise KeyError(f"no index in the book: {wanted!r}")

    def interrupt_ids(self) -> Tuple[str, ...]:
        """Every held interrupt id, in held order."""
        return tuple(e.interrupt_id for e in self.entries if e.interrupt_id)

    def scopes(self) -> Tuple[str, ...]:
        """Every held pause's scope, in held order."""
        return tuple(e.scope for e in self.entries)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "crew_interrupt_book",
            "slice": CREW_INTERRUPTS_SLICE,
            "title": self.title,
            "interrupt_ids": list(self.interrupt_ids()),
            "interrupt_count": len(self.entries),
            "index_count": len(self.indexes),
        }


def validate_book(data: Any, *, require_example: bool = False) -> CrewInterruptBook:
    """Validate one crew interrupts mapping into a CrewInterruptBook.

    The mapping names a ``schema`` (the crew
    interrupts schema word), a ``guide`` mapping
    (its ``title``), an ``entries`` list and an
    optional ``indexes`` list. Every record stands
    on its own validation, then the whole is
    judged: interrupt ids unique, and every index
    judged against the book's own interrupt
    records. With ``require_example`` the shipped
    example is held to its pinned shape: the
    pinned title, records and index, the index's
    pinned rows, totals and account word-for-word,
    and the first report's pinned checks and
    account. Problems raise
    :class:`ValidationError` or ``ValueError``.
    """
    if isinstance(data, CrewInterruptBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a crew interrupt book must be a mapping, got {data!r}")
    unknown = set(data) - _CREW_INTERRUPTS_KEYS
    if unknown:
        raise ValidationError(
            "unknown crew interrupts keys: %s" % ", ".join(sorted(unknown)))
    if data.get("schema") != CREW_INTERRUPTS_SCHEMA:
        raise ValidationError(
            f"a crew interrupt book must carry schema "
            f"{CREW_INTERRUPTS_SCHEMA!r}, got {data.get('schema')!r}")
    if "entries" not in data:
        raise ValidationError("a crew interrupt book is missing its entries")
    if not isinstance(data["entries"], (list, tuple)):
        raise ValidationError("a crew interrupt book's entries must be a list")
    if data.get("indexes") is not None \
            and not isinstance(data["indexes"], (list, tuple)):
        raise ValidationError("a crew interrupt book's indexes must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a crew interrupt book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a crew interrupt book is missing its title")
        note = data.get("interrupts_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a crew interrupt book's note must be text")
        book = CrewInterruptBook(
            title=title, entries=tuple(data["entries"]),
            indexes=tuple(data.get("indexes") or ()),
            interrupts_note=note)
        for index in book.indexes:
            validate_index(index, book.entries)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if require_example:
        if book.title != _EXAMPLE_TITLE:
            raise ValidationError(
                "the shipped example crew interrupt book's title is "
                "not the pinned title")
        if book.interrupt_ids() != _EXAMPLE_INTERRUPT_IDS:
            raise ValidationError(
                "the shipped example's interrupt records are not "
                "the pinned records")
        if book.scopes() != _EXAMPLE_SCOPES:
            raise ValidationError(
                "the shipped example's scopes are not "
                "the pinned scopes")
        if tuple(e.consistent for e in book.entries) != _EXAMPLE_CONSISTENCY:
            raise ValidationError(
                "the shipped example's pauses do not derive "
                "their pinned consistency")
        index = book.index_for(_EXAMPLE_INDEX_ID)
        if tuple(r.scope for r in index.rows) != _EXAMPLE_INDEX_ROWS:
            raise ValidationError(
                "the shipped example index does not name "
                "its pinned rows")
        totals = (
            index.total_interrupts, index.total_consistent,
            index.total_inconsistent)
        if totals != _EXAMPLE_INDEX_TOTALS:
            raise ValidationError(
                "the shipped example index does not carry "
                "its pinned totals")
        if index.account != _EXAMPLE_INDEX_ACCOUNT:
            raise ValidationError(
                "the shipped example index does not carry "
                "its pinned account word-for-word")
        first = derive_report(book.entries[0])
        if first.checks != _EXAMPLE_FIRST_REPORT_CHECKS:
            raise ValidationError(
                "the shipped example's first report does not "
                "carry its pinned checks")
        if first.account != _EXAMPLE_FIRST_REPORT_ACCOUNT:
            raise ValidationError(
                "the shipped example's first report does not "
                "carry its pinned account word-for-word")
    return book


def build_book(book: Any = None, **kwargs: Any) -> CrewInterruptBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, CrewInterruptBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "entries" in book or "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return CrewInterruptBook(**merged)
    if book is None:
        return CrewInterruptBook(**kwargs)
    raise ValueError(f"a crew interrupt book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> CrewInterruptBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_crew_interrupts(
        data: Optional[Dict[str, Any]] = None) -> CrewInterruptBook:
    """Load and validate the shipped example book (or *data*).

    The shipped file is held to the example check:
    the pinned title, interrupt records and index -
    the M-143 boundary book of the roadmap's three
    pause scopes - so the shipped book covers the
    pauses this slice exists to hold.
    """
    raw = data if data is not None else load_resource(CREW_INTERRUPTS_RESOURCE)
    return _book_from(raw, require_example=True)


def load_crew_interrupts_file(path: Any) -> CrewInterruptBook:
    """Load and validate a crew interrupt book from a file at *path*.

    Any file in the crew interrupts shape, anywhere
    on disk, validated whole - a malformed file
    raises :class:`ValidationError` naming the
    problem, and a missing file raises
    ``FileNotFoundError``. The example check is
    not held: a real interrupt book stands on its
    own records.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held record by record, in held order.
# ---------------------------------------------------------------------


class InterruptRegistry:
    """One session's crew interrupt book, held record by record.

    The registry holds interrupt records, never
    reports or indexes: both are derivations, read
    off held records at call time, so nothing here
    can hold a consistency stale.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._entries: Dict[str, CrewInterrupt] = {}
        self._order: list = []
        self._next_entry = 1
        if book is not None:
            self.register_book(book)

    def _fresh_interrupt_id(self, held_ids: Any) -> str:
        while f"interrupt-{self._next_entry}" in held_ids:
            self._next_entry += 1
        fresh = f"interrupt-{self._next_entry}"
        self._next_entry += 1
        return fresh

    def register_interrupt(self, interrupt: Any) -> CrewInterrupt:
        """Register one interrupt record into the held book.

        A record with no id is given a deterministic
        ``interrupt-N`` id. A record id already
        standing here refuses.
        """
        validated = build_interrupt(interrupt)
        held_ids = set(self._entries)
        if validated.interrupt_id is not None \
                and validated.interrupt_id in held_ids:
            raise ValueError(
                f"an interrupt record named "
                f"{validated.interrupt_id!r} already exists")
        if validated.interrupt_id is None:
            validated = replace(
                validated,
                interrupt_id=self._fresh_interrupt_id(held_ids))
        self._entries[validated.interrupt_id] = validated
        self._order.append(validated.interrupt_id)
        return validated

    def register_book(self, book: Any) -> CrewInterruptBook:
        """Register every interrupt record of one book, in order.

        The first book held sets the title; a later
        book under a different title refuses, as does
        a book naming a held record id. The book's
        indexes are derivations, not holdings, and
        are not held.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a crew interrupt book "
                "under a different title")
        for entry in validated.entries:
            if entry.interrupt_id in self._entries:
                raise ValueError(
                    f"an interrupt record named "
                    f"{entry.interrupt_id!r} already exists")
        self._title = validated.title
        for entry in validated.entries:
            self.register_interrupt(entry)
        return self.book()

    def get_interrupt(self, interrupt_id: Any) -> CrewInterrupt:
        """The interrupt record one id names among the held records."""
        wanted = normalize_member_id(interrupt_id)
        if wanted not in self._entries:
            raise KeyError(f"unknown interrupt record: {wanted!r}")
        return self._entries[wanted]

    def list_interrupts(self) -> Tuple[CrewInterrupt, ...]:
        """Every held interrupt record, in the order they were held."""
        return tuple(self._entries[e] for e in self._order)

    def book(self) -> CrewInterruptBook:
        """The held interrupt records as one validated book."""
        if self._title is None:
            raise ValueError("no crew interrupt book is held yet")
        return CrewInterruptBook(
            title=self._title, entries=self.list_interrupts())

    def report_for(self, interrupt_id: Any) -> ConsistencyReport:
        """Derive one pause's consistency report, at call time.

        The report is derived from the held record
        the id names, read at call time - the
        registry holds records, and this report is
        derived from them.
        """
        return derive_report(self.get_interrupt(interrupt_id))

    def index(self) -> InterruptIndex:
        """Derive the interrupt index of the held book.

        The rows, totals and account are the held
        records' own derived counts, read at call
        time.
        """
        return derive_index(self.list_interrupts())


# ---------------------------------------------------------------------
# Crew interrupt news, shaped as session records.
# ---------------------------------------------------------------------


def interrupt_record(interrupt: Any) -> Dict[str, Any]:
    """The session-news record of one interrupt record."""
    current = interrupt if isinstance(interrupt, CrewInterrupt) \
        else build_interrupt(interrupt)
    record = current.to_record()
    record["news"] = True
    label = _target_label(current.scope, current.member, current.slice_id)
    if current.consistent:
        record["headline"] = (
            f"Pausing {label} leaves its worktree and "
            f"journal consistent.")
    else:
        record["headline"] = (
            f"Pausing {label} does not yet leave its "
            f"worktree and journal consistent.")
    return record


def report_record(report: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one consistency report.

    With *source* given, the report is first judged
    against the interrupt it belongs to.
    """
    current = validate_report(report, source)
    record = current.to_record()
    record["news"] = True
    label = _target_label(current.scope, current.member, current.slice_id)
    if current.consistent:
        record["headline"] = (
            f"Pausing {label} is consistent: "
            f"{'; '.join(current.checks)}.")
    else:
        record["headline"] = (
            f"Pausing {label} is not yet consistent: "
            f"{'; '.join(current.checks)}.")
    return record


def index_record(index: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of the interrupt index.

    With *source* given, the index is first judged
    against the records it belongs to.
    """
    current = validate_index(index, source)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Crew interrupts: {current.total_interrupts} "
        f"pause(s), {current.total_consistent} leaving "
        f"the worktree and journal consistent.")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one crew interrupt book."""
    current = book if isinstance(book, CrewInterruptBook) else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Crew interrupt book {current.title}: "
        f"{record['interrupt_count']} interrupt "
        f"record(s), {record['index_count']} index(es).")
    return record


def plain_words(interrupt: Any) -> str:
    """One interrupt record, in one plain sentence."""
    current = interrupt if isinstance(interrupt, CrewInterrupt) \
        else build_interrupt(interrupt)
    label = _target_label(current.scope, current.member, current.slice_id)
    point_phrase = "a resting point" if current.point == "resting" \
        else "mid-edit"
    verdict = "leaves" if current.consistent else "does not yet leave"
    return (
        f"{current.title} - pausing {label}: "
        f"{current.detail} The worktree is "
        f"{current.worktree}, the journal is "
        f"{current.journal}, and the pause is taken at "
        f"{point_phrase}: this pause {verdict} its "
        f"worktree and journal consistent.")


def report_plain_words(source: Any) -> str:
    """Consistency reports in plain words: every report, in full.

    Accepts a ConsistencyReport or a
    CrewInterruptBook. Each report is told whole -
    its pause and its account.
    """
    if isinstance(source, ConsistencyReport):
        reports = (validate_report(source),)
        title = None
    elif isinstance(source, CrewInterruptBook):
        reports = tuple(
            derive_report(entry) for entry in source.entries)
        title = source.title
    else:
        raise ValueError(f"a crew interrupt source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    for report in reports:
        label = _target_label(report.scope, report.member, report.slice_id)
        verdict = "consistent" if report.consistent else "not yet consistent"
        lines.append(f"Pausing {label} - {verdict}")
        lines.extend(report.account)
    return "\n".join(lines)


def index_plain_words(source: Any) -> str:
    """The interrupt index in plain words, in full.

    Accepts an InterruptIndex or a CrewInterruptBook.
    The index is told whole - its rows and its
    account.
    """
    if isinstance(source, InterruptIndex):
        index = validate_index(source)
        title = None
    elif isinstance(source, CrewInterruptBook):
        index = derive_index(source.entries)
        title = source.title
    else:
        raise ValueError(f"a crew interrupt source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Interrupt index:")
    for row in index.rows:
        label = _target_label(row.scope, row.member, row.slice_id)
        verdict = "consistent" if row.consistent else "not yet consistent"
        lines.append(f"Pausing {label} - {verdict}")
    lines.extend(index.account)
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Screens: the formatters and the shared /interrupts grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> CrewInterruptBook:
    if source is None:
        return load_crew_interrupts()
    if isinstance(source, InterruptRegistry):
        return source.book()
    if isinstance(source, CrewInterruptBook):
        return source
    raise ValueError(f"a crew interrupt book is needed, got {source!r}")


def format_interrupt(interrupt: Any) -> str:
    """One interrupt record as a screen line."""
    current = interrupt if isinstance(interrupt, CrewInterrupt) \
        else build_interrupt(interrupt)
    label = _target_label(current.scope, current.member, current.slice_id)
    verdict = "consistent" if current.consistent else "not yet consistent"
    return (
        f"{current.interrupt_id or '-'}: {current.scope} - "
        f"{current.title} (pausing {label}: {verdict})")


def format_interrupts(source: Any = None, member: Any = None,
                      scope: Any = None) -> str:
    """Interrupt records of one book, in held order.

    With *member* given, only the member pauses
    naming that member are shown; with *scope*
    given, only the pauses of that scope.
    """
    book = _source_book(source)
    entries = book.entries
    if member is not None:
        wanted = normalize_member_id(member)
        entries = tuple(
            e for e in entries
            if e.scope == "member" and e.member == wanted)
    if scope is not None:
        wanted_scope = normalize_scope(scope)
        entries = tuple(e for e in entries if e.scope == wanted_scope)
    lines = [format_interrupt(entry) for entry in entries]
    if not lines:
        lines.append("No interrupt records are held.")
    return "\n".join(lines)


def format_report(source: Any = None) -> str:
    """Consistency reports as screen blocks: pause over derived account.

    Accepts a ConsistencyReport or a
    CrewInterruptBook; a book shows every report
    it derives, in book order.
    """
    if isinstance(source, ConsistencyReport):
        reports = (validate_report(source),)
        lines: list = []
    else:
        book = _source_book(source)
        reports = tuple(
            derive_report(entry) for entry in book.entries)
        lines = [f"Consistency reports in {book.title}:"]
    for report in reports:
        label = _target_label(report.scope, report.member, report.slice_id)
        verdict = "consistent" if report.consistent else "not yet consistent"
        lines.append(f"Pausing {label} - {verdict}")
        lines.extend(report.account)
    if isinstance(source, ConsistencyReport):
        return "\n".join(lines)
    if len(lines) == 1:
        lines.append("Nothing here.")
    return "\n".join(lines)


def format_index(source: Any = None) -> str:
    """The interrupt index as a screen block.

    Accepts an InterruptIndex or a CrewInterruptBook;
    a book shows the index it derives, its rows
    over its derived account.
    """
    if isinstance(source, InterruptIndex):
        index = validate_index(source)
        lines: list = []
    else:
        book = _source_book(source)
        index = derive_index(book.entries)
        lines = [f"Index in {book.title}:"]
    lines.append("Interrupt index:")
    for row in index.rows:
        label = _target_label(row.scope, row.member, row.slice_id)
        verdict = "consistent" if row.consistent else "not yet consistent"
        lines.append(f"Pausing {label} - {verdict}")
    lines.extend(index.account)
    return "\n".join(lines)


def format_crew_interrupts_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /interrupts.

    With nothing named, the shipped example crew
    interrupt book is shown - the example this
    slice ships - so the screen is never empty.
    """
    book = _source_book(source)
    lines = ["Crew interrupts (M-144) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_interrupts(book))
    lines.append("")
    lines.append(format_report(book))
    lines.append("")
    lines.append(format_index(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_crew_interrupts_args(args: Any) -> Tuple[str, Any]:
    """Parse the /interrupts grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    crew interrupt book; ``interrupt
    <interrupt-id>`` shows one pause record;
    ``member <member-id>`` shows the pauses naming
    one member; ``slice <slice-id>`` shows the
    pauses naming one slice; ``report
    <interrupt-id>`` shows one pause's consistency
    report; ``index`` shows the interrupt index.
    Anything else is a usage error naming the
    grammar. Returns ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head == "index" and len(words) == 1:
        return ("index", None)
    if head in ("interrupt", "member", "report") and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "slice" and len(words) == 2:
        try:
            return (head, normalize_slice_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
