"""External agents as crew (All-Features roadmap slice M-137).

Part VI continues here. The roadmap's words:
``an outside agent (over MCP, Part X) can hold
a seat with the same contracts and budgets.``

What already shipped, and what this slice adds:

* The crew itself is already data
  (``core/crew_members.py``, M-121): a member is
  an office, a posture and a set of tools - the
  contract an internal member works under. And
  budgets are already data
  (``core/budgets.py``, M-107): a per-task or
  per-session guard over tokens, cost, time and
  commands. What nothing held is the seat an
  OUTSIDE agent sits in - an agent that is not
  part of the house cast, arriving over the MCP
  road Part X will build.
* This slice is that seat, as a pure layer: a
  seat book validated as data - one seat per
  outside agent (the agent's own name, the home
  it arrives from, the transport it rides, the
  crew member record it sits as and the budget
  that guards it) under a title, plus seat
  checks whose findings are derived from the
  seat they judge - the shipped data file
  (``mythic_agent/data/external_agents.yaml``)
  holding one example seat book in exactly the
  shape a real seats file takes, a loader for a
  seats file anywhere on disk, records shaped
  as session news, and a small in-memory
  registry model. This module opens no MCP
  session, calls no model, spawns nothing and
  imports no agent / UI code; the agent layer
  owns holding the seats for a session.

Honesty rules, enforced here and pinned by tests:

* **Same contracts, same budgets.** A seat sits
  AS a crew member record, validated by the
  crew layer itself (composed by import from
  ``core/crew_members.py``, never re-read here),
  and is guarded by a budget validated by the
  budgets layer itself (``core/budgets.py``). A
  seat naming an office, a posture or a budget
  word the internal crew does not use refuses
  through those same validators - there is no
  second, laxer road for outsiders.
* **No foreign privileges.** A seat holds the
  fields above and no others: any further key -
  a privilege, an exemption, a wider tool right
  - is an unknown key and refuses whole. An
  outside agent gets exactly the terms an
  internal member gets, never more.
* **A check is derived, never stored loose.**
  A check's findings are read off its seat at
  check time - the seat's office, posture and
  budget, in plain words - so a stored check
  whose findings disagree with the seat it
  judges refuses, exactly as a stored stand-up
  digest does (M-134). A check judged against
  no seat and naming no findings of its own
  refuses for the same reason.
* **Data only - no live road is claimed.** The
  transport word ``mcp`` is data naming the
  road the roadmap assigns (Part X); nothing
  here opens that road, speaks that protocol
  or claims an outside agent is present. A seat
  here is a validated record of the terms an
  outside agent WOULD sit under. The roadmap
  names the board (Part VIII) as where crew
  state will be visible; that board does not
  exist yet, so the seats are visible through
  this slice's own /externals screen, and
  nothing here claims a board exists.
* **Malformed refuses.** An unknown transport,
  an empty agent name or home, a member naming
  no member id, a duplicate member or seat id
  anywhere in the book, a check naming a member
  the book holds no seat for, and unknown keys
  in a seat, a check or a seats mapping all
  raise instead of being skipped or guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .budgets import Budget, build_budget, validate_budget
from .crew_members import (
    CrewMember, build_member, normalize_member_id, validate_member)
from .validation import ValidationError

__all__ = [
    "EXTERNAL_AGENTS_RESOURCE",
    "EXTERNAL_AGENTS_SCHEMA",
    "EXTERNAL_AGENTS_SLICE",
    "PLAIN_EXPLANATION",
    "TRANSPORTS",
    "USAGE",
    "ExternalRegistry",
    "ExternalSeat",
    "SeatBook",
    "SeatCheck",
    "book_record",
    "build_book",
    "build_check",
    "build_seat",
    "check_plain_words",
    "check_record",
    "check_seat",
    "format_check",
    "format_external_agents_screen",
    "format_seat",
    "format_seats",
    "format_transports",
    "load_external_agents",
    "load_external_agents_file",
    "normalize_transport",
    "parse_external_args",
    "plain_words",
    "seat_record",
    "validate_book",
    "validate_check",
    "validate_seat",
]

EXTERNAL_AGENTS_SLICE = "M-137"

#: The packaged data resource holding the example seat book.
EXTERNAL_AGENTS_RESOURCE = "external_agents.yaml"

#: The schema word a seats file must carry.
EXTERNAL_AGENTS_SCHEMA = "mythic.external_agents/1"

#: The transports an outside agent can arrive
#: over: the MCP road, the only road the roadmap
#: names for outside agents (Part X). The word
#: is data here - no road is opened by it.
TRANSPORTS = ("mcp",)

_TRANSPORT_READINGS = {
    "mcp": "mcp",
    "model_context_protocol": "mcp",
}

#: The one verdict a seat check can reach: the
#: seat stands on the same terms as the crew.
CHECK_VERDICTS = ("same_terms",)

_SEAT_KEYS = frozenset({
    "seat_id", "id", "member", "crew_member", "member_record",
    "agent_name", "name", "agent", "home", "server", "origin",
    "transport", "road", "budget",
})

_CHECK_KEYS = frozenset({
    "check_id", "id", "member", "member_id", "transport",
    "road", "verdict", "findings", "statements",
})

_BOOK_KEYS = frozenset({"title", "name"})

_EXTERNALS_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "externals_note", "guide", "seats", "checks",
})

#: The shipped example book's title, held to this
#: by the loader's example check.
_EXAMPLE_TITLE = "External seats at the M-136 slice boundary"

#: The shipped example's seat ids and member ids,
#: in book order, pinned by the loader.
_EXAMPLE_SEAT_IDS = ("seat-atlas", "seat-ledger")

_EXAMPLE_MEMBER_IDS = ("atlas_reviewer", "ledger_hand")

#: The shipped example's budget scope per member:
#: one seat under each scope an internal budget
#: can guard, pinned by the loader.
_EXAMPLE_SCOPES = {
    "atlas_reviewer": "task",
    "ledger_hand": "session",
}

#: The shipped example's one check: the atlas
#: seat on the same terms, its findings pinned
#: word-for-word by the loader.
_EXAMPLE_CHECK_ID = "atlas-on-same-terms"

_EXAMPLE_CHECK_FINDINGS = (
    "The seat's office is auditor, one of the "
    "shipped crew offices.",
    "The seat's posture is read-only-scout, one "
    "of the shipped crew postures.",
    "The seat's budget is per-task: 20000 tokens, "
    "40 commands.",
)

PLAIN_EXPLANATION = (
    "External agents as crew: an outside agent, "
    "arriving over MCP (Part X), can hold a seat "
    "with the same contracts and budgets as the "
    "internal crew. A seat holds the agent's own "
    "name, the home it arrives from, the "
    "transport it rides, the crew member record "
    "it sits as - office, posture and tools, "
    "validated by the crew layer itself - and "
    "the budget that guards it, validated by "
    "the budgets layer itself, and no privilege "
    "of its own. This layer holds seats and "
    "checks as data only; it opens no MCP "
    "session, calls no model and spawns no "
    "agent itself."
)

USAGE = (
    "Usage: /externals, /externals show, "
    "/externals seat <member-id>, "
    "/externals check <member-id>, /externals mcp, "
    "/externals transports"
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


def _check_home(value: Any) -> str:
    text = _check_short_text(value, "a home")
    if any(ch.isspace() for ch in text):
        raise ValueError(
            f"a home is one label naming where the agent "
            f"arrives from, got {value!r}")
    return text


def _check_findings(value: Any) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"a check's findings must be a list of statements, "
            f"got {value!r}")
    findings = tuple(
        _check_long_text(f, "a finding") for f in value)
    if not findings:
        raise ValueError("a check carries at least one finding")
    if len(findings) > 8:
        raise ValueError(
            f"a check carries at most 8 findings, got {len(findings)}")
    if len(set(findings)) != len(findings):
        raise ValueError("a check states one finding twice")
    return findings


def normalize_transport(value: Any) -> str:
    """The canonical transport a word names.

    Transport words read case-insensitively, with
    dashes read as underscores: the full
    ``model_context_protocol`` spelling reads as
    ``mcp``. Anything else raises - an outside
    agent arrives over the one road the roadmap
    names, never a maybe.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted in _TRANSPORT_READINGS:
            return _TRANSPORT_READINGS[wanted]
    raise ValueError(
        "an external transport must be one of %s, got %r"
        % ("/".join(TRANSPORTS), value))


def _pick_any(mapping: Dict[str, Any], spellings: Tuple[str, ...],
              what: str) -> Any:
    values = [mapping[s] for s in spellings if s in mapping]
    if not values:
        return None
    if any(value != values[0] for value in values[1:]):
        raise ValueError(f"a record names two different {what}")
    return values[0]


def _check_member(value: Any) -> CrewMember:
    """One seat's member: the crew layer's own reading.

    A CrewMember stands as it is; a mapping is
    read by ``core/crew_members.py`` itself, so
    the contract an outside agent sits under is
    validated by exactly the validators an
    internal member answers to. The member must
    name a member id - a seat is addressed by
    the member sitting in it.
    """
    if isinstance(value, CrewMember):
        member = value
    elif isinstance(value, dict):
        member = validate_member(value)
    else:
        raise ValueError(
            f"a seat's member must be a crew member record, "
            f"got {value!r}")
    if member.member_id is None:
        raise ValueError(
            "a seat's member must name a member id - "
            "a seat is addressed by its member")
    return member


def _check_budget(value: Any) -> Budget:
    """One seat's budget: the budgets layer's own reading.

    A Budget stands as it is; a mapping is read
    by ``core/budgets.py`` itself, so the budget
    guarding an outside agent is validated by
    exactly the validators an internal budget
    answers to - same scopes, same dimensions,
    no invented words.
    """
    if isinstance(value, Budget):
        return value
    if isinstance(value, dict):
        return validate_budget(value)
    raise ValueError(
        f"a seat's budget must be a budget record, got {value!r}")


# ---------------------------------------------------------------------
# The seat: one outside agent's place in the crew, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ExternalSeat:
    """One outside agent's seat in the crew, as data.

    ``member`` is the M-121 crew member record
    the agent sits as - its office, posture and
    tools are the contract it works under, the
    same contract an internal member holds;
    ``agent_name`` is the agent's own name;
    ``home`` is the one label naming where it
    arrives from; ``transport`` is the road it
    rides (``mcp``, the Part X road, held as
    data); ``budget`` is the M-107 budget that
    guards it. A seat holds no privilege of its
    own: these fields are all it has.
    Constructing one validates its shape only:
    whether its member already sits in its book
    is the book's concern.
    """

    seat_id: Optional[str] = None
    member: Any = None
    agent_name: str = ""
    home: str = ""
    transport: str = ""
    budget: Any = None

    def __post_init__(self) -> None:
        if self.seat_id is not None:
            object.__setattr__(
                self, "seat_id", normalize_member_id(self.seat_id))
        if self.member is None:
            raise ValueError("a seat is missing its member")
        object.__setattr__(self, "member", _check_member(self.member))
        object.__setattr__(
            self, "agent_name",
            _check_short_text(self.agent_name, "an agent name"))
        object.__setattr__(self, "home", _check_home(self.home))
        object.__setattr__(
            self, "transport", normalize_transport(self.transport))
        if self.budget is None:
            raise ValueError("a seat is missing its budget")
        object.__setattr__(self, "budget", _check_budget(self.budget))

    @property
    def member_id(self) -> str:
        """The member id of the member sitting in this seat."""
        return self.member.member_id

    @property
    def office(self) -> str:
        """The crew office this seat's contract names."""
        return self.member.office

    @property
    def posture(self) -> str:
        """The crew posture this seat's contract names."""
        return self.member.posture

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "external_seat",
            "slice": EXTERNAL_AGENTS_SLICE,
            "seat_id": self.seat_id,
            "member": self.member.to_record(),
            "agent_name": self.agent_name,
            "home": self.home,
            "transport": self.transport,
            "budget": self.budget.to_record(),
        }


def validate_seat(seat: Any) -> ExternalSeat:
    """Validate one seat into an ExternalSeat.

    Accepts an ExternalSeat or a mapping naming a
    ``member`` (or ``crew_member`` /
    ``member_record``) - itself an M-121 member
    mapping, read by the crew layer - an
    ``agent_name`` (or ``name`` / ``agent``), a
    ``home`` (or ``server`` / ``origin``), a
    ``transport`` (or ``road``), a ``budget`` -
    itself an M-107 budget mapping, read by the
    budgets layer - and an optional ``seat_id``
    (or ``id``). Naming two spellings of one
    field with different values refuses, and
    unknown keys refuse: a key this layer does
    not know is a privilege the seat does not
    get.
    """
    if isinstance(seat, ExternalSeat):
        return seat
    if not isinstance(seat, dict):
        raise ValueError(f"a seat must be a mapping, got {seat!r}")
    unknown = set(seat) - _SEAT_KEYS
    if unknown:
        raise ValueError(
            "unknown seat keys: %s" % ", ".join(sorted(unknown)))
    member = _pick_any(
        seat, ("member", "crew_member", "member_record"), "members")
    if member is None:
        raise ValueError("a seat is missing its member")
    agent_name = _pick_any(
        seat, ("agent_name", "name", "agent"), "agent names")
    if agent_name is None:
        raise ValueError("a seat is missing its agent name")
    home = _pick_any(seat, ("home", "server", "origin"), "homes")
    if home is None:
        raise ValueError("a seat is missing its home")
    transport = _pick_any(seat, ("transport", "road"), "transports")
    if transport is None:
        raise ValueError("a seat is missing its transport")
    if "budget" not in seat:
        raise ValueError("a seat is missing its budget")
    kwargs: Dict[str, Any] = {
        "member": member, "agent_name": agent_name, "home": home,
        "transport": transport, "budget": seat["budget"]}
    seat_id = _pick_any(seat, ("seat_id", "id"), "seat ids")
    if seat_id is not None:
        kwargs["seat_id"] = seat_id
    return ExternalSeat(**kwargs)


def build_seat(seat: Any = None, **kwargs: Any) -> ExternalSeat:
    """Build one validated seat, from a mapping or field words."""
    if isinstance(seat, ExternalSeat) and not kwargs:
        return seat
    if isinstance(seat, dict) or seat is None:
        merged: Dict[str, Any] = {}
        if isinstance(seat, dict):
            merged.update(seat)
        merged.update(kwargs)
        return validate_seat(merged)
    raise ValueError(f"a seat must be a mapping, got {seat!r}")


# ---------------------------------------------------------------------
# The check: a seat judged to stand on the same terms, derived.
# ---------------------------------------------------------------------


def _budget_words(budget: Budget) -> str:
    """A budget's named limits in plain words, in dimension order."""
    parts = []
    if budget.token_limit is not None:
        parts.append(f"{budget.token_limit} tokens")
    if budget.cost_limit is not None:
        parts.append(f"${budget.cost_limit:.2f} cost")
    if budget.time_limit_seconds is not None:
        parts.append(f"{budget.time_limit_seconds:g} seconds")
    if budget.command_limit is not None:
        parts.append(f"{budget.command_limit} commands")
    if not parts:
        return "no limits named, as an internal budget may name none"
    return ", ".join(parts)


@dataclass(frozen=True)
class SeatCheck:
    """One check: a seat standing on the same terms, as data.

    ``member`` is the member the checked seat
    holds; ``transport`` is the road that seat
    rides; ``verdict`` is the one verdict a check
    can reach - ``same_terms``; ``findings`` are
    the plain statements the verdict rests on,
    read off the seat: its office, its posture
    and its budget. A check is normally derived
    from its seat (see :func:`check_seat`);
    constructing one directly validates its
    shape only.
    """

    check_id: Optional[str] = None
    member: str = ""
    transport: str = ""
    verdict: str = ""
    findings: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.check_id is not None:
            object.__setattr__(
                self, "check_id", normalize_member_id(self.check_id))
        object.__setattr__(
            self, "member", normalize_member_id(self.member))
        object.__setattr__(
            self, "transport", normalize_transport(self.transport))
        verdict = self.verdict.strip().lower().replace("-", "_") \
            if isinstance(self.verdict, str) else ""
        if verdict not in CHECK_VERDICTS:
            raise ValueError(
                "a check's verdict must be one of %s, got %r"
                % ("/".join(CHECK_VERDICTS), self.verdict))
        object.__setattr__(self, "verdict", verdict)
        object.__setattr__(
            self, "findings", _check_findings(self.findings))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "external_seat_check",
            "slice": EXTERNAL_AGENTS_SLICE,
            "check_id": self.check_id,
            "member": self.member,
            "transport": self.transport,
            "verdict": self.verdict,
            "findings": list(self.findings),
        }


def check_seat(seat: Any) -> SeatCheck:
    """Derive one check from a seat: the seat on the same terms.

    The findings are read off the seat itself -
    its member's office and posture, which the
    crew layer validated, and its budget's scope
    and limits, which the budgets layer
    validated - so the verdict ``same_terms``
    rests on the seat's own held terms and on
    nothing else. Deriving is deterministic: one
    seat derives one check, every time.
    """
    held = seat if isinstance(seat, ExternalSeat) else build_seat(seat)
    findings = (
        f"The seat's office is {held.office}, one of the "
        f"shipped crew offices.",
        f"The seat's posture is {held.posture}, one of the "
        f"shipped crew postures.",
        f"The seat's budget is per-{held.budget.scope}: "
        f"{_budget_words(held.budget)}.",
    )
    return SeatCheck(
        member=held.member_id, transport=held.transport,
        verdict="same_terms", findings=findings)


def validate_check(check: Any, seat: Any = None) -> SeatCheck:
    """Validate one check into a SeatCheck.

    Accepts a SeatCheck or a mapping naming a
    ``member`` (or ``member_id``), a ``transport``
    (or ``road``), a ``verdict``, ``findings``
    (or ``statements``) and an optional
    ``check_id`` (or ``id``). When *seat* is
    given, the check is judged against it: the
    member and transport must be the seat's, the
    verdict must be the derived one, and any
    stored findings must equal the derived
    findings word-for-word (missing findings are
    read off the seat). A stored check naming no
    findings of its own and judged against no
    seat refuses, because findings are derived
    off the seat, never stored loose.
    """
    held_seat = None
    if seat is not None:
        held_seat = seat if isinstance(seat, ExternalSeat) \
            else build_seat(seat)
    derived = check_seat(held_seat) if held_seat is not None else None
    if isinstance(check, SeatCheck):
        current = check
    elif isinstance(check, dict):
        unknown = set(check) - _CHECK_KEYS
        if unknown:
            raise ValueError(
                "unknown check keys: %s" % ", ".join(sorted(unknown)))
        member = _pick_any(check, ("member", "member_id"), "members")
        if member is None:
            if derived is None:
                raise ValueError("a check is missing its member")
            member = derived.member
        transport = _pick_any(
            check, ("transport", "road"), "transports")
        if transport is None:
            if derived is None:
                raise ValueError("a check is missing its transport")
            transport = derived.transport
        verdict = check.get("verdict")
        if verdict is None:
            if derived is None:
                raise ValueError("a check is missing its verdict")
            verdict = derived.verdict
        findings = _pick_any(
            check, ("findings", "statements"), "findings")
        if findings is None:
            if derived is None:
                raise ValueError(
                    "a stored check names no findings of its own - "
                    "judge it against its seat")
            findings = derived.findings
        check_id = _pick_any(check, ("check_id", "id"), "check ids")
        current = SeatCheck(
            check_id=check_id, member=member, transport=transport,
            verdict=verdict, findings=findings)
    else:
        raise ValueError(f"a check must be a mapping, got {check!r}")
    if derived is not None:
        if current.member != derived.member:
            raise ValueError(
                "a check's member disagrees with its seat - "
                "a check judges its own seat")
        if current.transport != derived.transport:
            raise ValueError(
                "a check's transport disagrees with its seat")
        if current.verdict != derived.verdict:
            raise ValueError(
                "a check's verdict disagrees with the verdict "
                "derived from its seat")
        if current.findings != derived.findings:
            raise ValueError(
                "a stored check's findings disagree with the "
                "findings derived from its seat - findings are "
                "derived off the seat, never stored loose")
    return current


def build_check(check: Any = None, seat: Any = None,
                **kwargs: Any) -> SeatCheck:
    """Build one validated check, from a mapping or field words."""
    if isinstance(check, SeatCheck) and not kwargs and seat is None:
        return check
    if isinstance(check, dict) or check is None:
        merged: Dict[str, Any] = {}
        if isinstance(check, dict):
            merged.update(check)
        merged.update(kwargs)
        return validate_check(merged, seat)
    return validate_check(check, seat)


# ---------------------------------------------------------------------
# The book: the outside agents' seats whole, under a title.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SeatBook:
    """One seat book, whole, as data.

    ``title`` names the book; ``seats`` are the
    seats, in file order, one per member - a
    member holds one seat in a book; ``checks``
    are example checks, each judged against its
    seat as the book is built, so a held check's
    findings are always its seat's derived
    findings.
    """

    title: str = ""
    seats: Tuple[ExternalSeat, ...] = ()
    checks: Tuple[SeatCheck, ...] = ()
    externals_note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_short_text(self.title, "a title"))
        seats = tuple(
            s if isinstance(s, ExternalSeat) else validate_seat(s)
            for s in self.seats)
        members = [s.member_id for s in seats]
        if len(set(members)) != len(members):
            raise ValueError("a book holds two seats for one member")
        ids = [s.seat_id for s in seats if s.seat_id is not None]
        if len(set(ids)) != len(ids):
            raise ValueError("a book holds one seat id twice")
        object.__setattr__(self, "seats", seats)
        by_member = {s.member_id: s for s in seats}
        held = []
        for raw in self.checks:
            member = raw.member if isinstance(raw, SeatCheck) \
                else _pick_any(raw, ("member", "member_id"), "members")
            if member is None or normalize_member_id(member) \
                    not in by_member:
                raise ValueError(
                    "a check names a member the book holds "
                    "no seat for")
            held.append(validate_check(
                raw, seat=by_member[normalize_member_id(member)]))
        check_ids = [c.check_id for c in held if c.check_id is not None]
        if len(set(check_ids)) != len(check_ids):
            raise ValueError("a book holds one check id twice")
        object.__setattr__(self, "checks", tuple(held))
        if not isinstance(self.externals_note, str):
            raise ValueError("a seat book's note must be text")
        object.__setattr__(
            self, "externals_note", self.externals_note.strip())

    def seat_for(self, member: Any) -> ExternalSeat:
        """The seat one member holds in this book; unknown raises."""
        wanted = normalize_member_id(member)
        for seat in self.seats:
            if seat.member_id == wanted:
                return seat
        raise KeyError(f"no seat in the book for member: {wanted!r}")

    def seats_for(self, transport: Any) -> Tuple[ExternalSeat, ...]:
        """Every seat riding one transport, in book order."""
        wanted = normalize_transport(transport)
        return tuple(s for s in self.seats if s.transport == wanted)

    def member_ids(self) -> Tuple[str, ...]:
        """Every member holding a seat, in book order."""
        return tuple(s.member_id for s in self.seats)

    def seat_ids(self) -> Tuple[str, ...]:
        """Every held seat id, in book order (id-less skipped)."""
        return tuple(s.seat_id for s in self.seats if s.seat_id)

    def check_for(self, check_id: Any) -> SeatCheck:
        """The check one id names in this book; unknown raises."""
        wanted = normalize_member_id(check_id)
        for check in self.checks:
            if check.check_id == wanted:
                return check
        raise KeyError(f"no check in the seat book: {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "external_seat_book",
            "slice": EXTERNAL_AGENTS_SLICE,
            "title": self.title,
            "member_ids": list(self.member_ids()),
            "seat_count": len(self.seats),
            "check_count": len(self.checks),
        }


def validate_book(data: Any, *, require_example: bool = False) -> SeatBook:
    """Validate one seats mapping into a SeatBook.

    The mapping names a ``schema`` (the seats
    schema word), a ``guide`` mapping (its
    ``title``), a ``seats`` list and an optional
    ``checks`` list. Every seat is validated -
    its member by the crew layer, its budget by
    the budgets layer - then the whole is judged:
    one seat per member, seat ids unique, and
    every check judged against its seat. With
    ``require_example`` the shipped example is
    held to its pinned shape: the pinned title,
    the pinned seats in order, one seat under
    each budget scope, and the pinned example
    check carrying its pinned findings
    word-for-word. Problems raise
    :class:`ValidationError` or ``ValueError``
    naming the problem.
    """
    if isinstance(data, SeatBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a seat book must be a mapping, got {data!r}")
    unknown = set(data) - _EXTERNALS_KEYS
    if unknown:
        raise ValidationError(
            "unknown seats keys: %s" % ", ".join(sorted(unknown)))
    if data.get("schema") != EXTERNAL_AGENTS_SCHEMA:
        raise ValidationError(
            f"a seat book must carry schema "
            f"{EXTERNAL_AGENTS_SCHEMA!r}, got {data.get('schema')!r}")
    if "seats" not in data:
        raise ValidationError("a seat book is missing its seats")
    raw = data["seats"]
    if not isinstance(raw, (list, tuple)):
        raise ValidationError("a seat book's seats must be a list")
    raw_checks = data.get("checks") or []
    if not isinstance(raw_checks, (list, tuple)):
        raise ValidationError("a seat book's checks must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a seat book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a seat book is missing its title")
        seats = tuple(validate_seat(s) for s in raw)
        note = data.get("externals_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a seat book's note must be text")
        book = SeatBook(
            title=title, seats=seats, checks=tuple(raw_checks),
            externals_note=note)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if require_example:
        if book.title != _EXAMPLE_TITLE:
            raise ValidationError(
                "the shipped example seat book's title is not "
                "the pinned title")
        if book.seat_ids() != _EXAMPLE_SEAT_IDS:
            raise ValidationError(
                "the shipped example seat book's seats are not "
                "the pinned seats")
        if book.member_ids() != _EXAMPLE_MEMBER_IDS:
            raise ValidationError(
                "the shipped example seat book's members are not "
                "the pinned members")
        for member, scope in _EXAMPLE_SCOPES.items():
            if book.seat_for(member).budget.scope != scope:
                raise ValidationError(
                    f"the shipped example seat for {member} is not "
                    "under its pinned budget scope")
        check = book.check_for(_EXAMPLE_CHECK_ID)
        if check.findings != _EXAMPLE_CHECK_FINDINGS:
            raise ValidationError(
                "the shipped example check does not carry its "
                "pinned findings word-for-word")
        derived = check_seat(book.seat_for(check.member))
        if (derived.member, derived.transport, derived.verdict,
                derived.findings) != (check.member, check.transport,
                                      check.verdict, check.findings):
            raise ValidationError(
                "the shipped example check is not the check "
                "derived from its seat")
    return book


def build_book(book: Any = None, **kwargs: Any) -> SeatBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, SeatBook) and not kwargs:
        return book
    if isinstance(book, (list, tuple)) and not kwargs:
        raise ValueError("a book needs its title")
    if isinstance(book, dict):
        if "seats" in book or "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return SeatBook(**merged)
    if book is None:
        return SeatBook(**kwargs)
    raise ValueError(f"a seat book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> SeatBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_external_agents(data: Optional[Dict[str, Any]] = None) -> SeatBook:
    """Load and validate the shipped example seat book (or *data*).

    The shipped file is held to the example check:
    the pinned title, the pinned seats in order,
    one seat under each budget scope, and the
    pinned example check - the atlas seat on the
    same terms, its findings derived from its
    seat - so the shipped book covers the boundary
    this slice exists to hold.
    """
    raw = data if data is not None else load_resource(
        EXTERNAL_AGENTS_RESOURCE)
    return _book_from(raw, require_example=True)


def load_external_agents_file(path: Any) -> SeatBook:
    """Load and validate a seat book from a file at *path*.

    Any file in the seats shape, anywhere on disk,
    validated whole - a malformed file raises
    :class:`ValidationError` naming the problem,
    and a missing file raises
    ``FileNotFoundError``. The example check is
    not held: a real seat book stands on its own
    seats.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held seat by seat, in order.
# ---------------------------------------------------------------------


class ExternalRegistry:
    """One session's seat book, held seat by seat.

    The registry holds seats, never checks: a
    check is a derivation, read off a held seat
    at call time, so nothing here can hold a
    finding stale.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._seats: Dict[str, ExternalSeat] = {}
        self._order: list = []
        self._next_seat = 1
        if book is not None:
            self.register_book(book)

    def _fresh_seat_id(self, held_ids: Any) -> str:
        while f"external-{self._next_seat}" in held_ids:
            self._next_seat += 1
        fresh = f"external-{self._next_seat}"
        self._next_seat += 1
        return fresh

    def register_seat(self, seat: Any) -> ExternalSeat:
        """Register one seat into the held book.

        A seat with no id is given a deterministic
        ``external-N`` id. A second seat for a
        member already holding one refuses, as
        does a seat id already standing here.
        """
        validated = build_seat(seat)
        if validated.member_id in self._seats:
            raise ValueError(
                f"a seat for {validated.member_id!r} already exists")
        held_ids = {
            s.seat_id for s in self._seats.values() if s.seat_id}
        if validated.seat_id is not None \
                and validated.seat_id in held_ids:
            raise ValueError(
                f"a seat named {validated.seat_id!r} already exists")
        if validated.seat_id is None:
            validated = replace(
                validated, seat_id=self._fresh_seat_id(held_ids))
        self._seats[validated.member_id] = validated
        self._order.append(validated.member_id)
        return validated

    def register_book(self, book: Any) -> SeatBook:
        """Register every seat of one book, in order.

        The first book held sets the title; a
        later book under a different title
        refuses, as does a book holding a seat for
        a member already standing here. The book's
        checks are derivations, not holdings, and
        are not held.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a seat book under "
                "a different title")
        for seat in validated.seats:
            if seat.member_id in self._seats:
                raise ValueError(
                    f"a seat for {seat.member_id!r} already exists")
        self._title = validated.title
        for seat in validated.seats:
            self.register_seat(seat)
        return self.book()

    def get_seat(self, member: Any) -> ExternalSeat:
        """The seat one member holds among the held seats."""
        wanted = normalize_member_id(member)
        if wanted not in self._seats:
            raise KeyError(f"unknown member: {wanted!r}")
        return self._seats[wanted]

    def list_seats(self) -> Tuple[ExternalSeat, ...]:
        """Every held seat, in the order they were held."""
        return tuple(self._seats[m] for m in self._order)

    def seats_for(self, transport: Any) -> Tuple[ExternalSeat, ...]:
        """Every held seat riding one transport, in held order."""
        wanted = normalize_transport(transport)
        return tuple(
            s for s in self.list_seats() if s.transport == wanted)

    def book(self) -> SeatBook:
        """The held seats as one validated seat book."""
        if self._title is None:
            raise ValueError("no seat book is held yet")
        return SeatBook(title=self._title, seats=self.list_seats())

    def check_seat(self, member: Any) -> SeatCheck:
        """Derive the check for one held seat, at call time.

        The findings are the held seat's own
        office, posture and budget, read at call
        time - the registry holds seats, and this
        check is derived from them.
        """
        return check_seat(self.get_seat(member))


# ---------------------------------------------------------------------
# Seat news, shaped as session records.
# ---------------------------------------------------------------------


def seat_record(seat: Any) -> Dict[str, Any]:
    """The session-news record of one seat."""
    current = seat if isinstance(seat, ExternalSeat) \
        else build_seat(seat)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.agent_name} holds a seat as {current.member_id} "
        f"({current.office}, {current.posture}) under a "
        f"per-{current.budget.scope} budget.")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one seat book."""
    current = book if isinstance(book, SeatBook) else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Seat book {current.title}: {record['seat_count']} "
        f"outside seat(s) held.")
    return record


def check_record(check: Any, seat: Any = None) -> Dict[str, Any]:
    """The session-news record of one check.

    With *seat* given, the check is first judged
    against the seat it belongs to.
    """
    current = validate_check(check, seat)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.member} stands on the same terms: "
        f"{len(current.findings)} finding(s) derived from the seat.")
    return record


def plain_words(seat: Any) -> str:
    """One seat, in one plain sentence."""
    current = seat if isinstance(seat, ExternalSeat) \
        else build_seat(seat)
    return (
        f"{current.member_id} - {current.agent_name} from "
        f"{current.home} over {current.transport}: "
        f"{current.office} office, {current.posture} posture, "
        f"per-{current.budget.scope} budget")


def check_plain_words(source: Any) -> str:
    """Checks in plain words: every check, in full.

    Accepts a SeatCheck or a SeatBook. Each check
    is told whole - its member, its verdict and
    its findings - so nothing is hidden and
    nothing is invented.
    """
    if isinstance(source, SeatCheck):
        checks = (source,)
        title = None
    elif isinstance(source, SeatBook):
        checks = source.checks
        title = source.title
    else:
        raise ValueError(f"an externals source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    for check in checks:
        lines.append(
            f"{check.member} - verdict {check.verdict}")
        lines.extend(check.findings)
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Screens: the formatters and the shared /externals grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> SeatBook:
    if source is None:
        return load_external_agents()
    if isinstance(source, ExternalRegistry):
        return source.book()
    if isinstance(source, SeatBook):
        return source
    raise ValueError(f"a seat book is needed, got {source!r}")


def format_seat(seat: Any) -> str:
    """One seat as a screen line, with its contract and budget."""
    current = seat if isinstance(seat, ExternalSeat) \
        else build_seat(seat)
    return (
        f"{current.member_id} / {current.seat_id or '-'} "
        f"[{current.transport}] via {current.home}: "
        f"{current.agent_name} - {current.office} office, "
        f"{current.posture} posture, per-{current.budget.scope} budget")


def format_seats(source: Any = None, transport: Any = None) -> str:
    """Seats of one book, in book order.

    With *transport* given, only the seats riding
    that transport are shown.
    """
    book = _source_book(source)
    seats = book.seats if transport is None \
        else book.seats_for(transport)
    lines = [format_seat(seat) for seat in seats]
    if not lines:
        lines.append("No outside seats are held.")
    return "\n".join(lines)


def format_check(source: Any = None) -> str:
    """Checks as screen blocks: verdict over derived findings.

    Accepts a SeatCheck or a SeatBook; a book
    shows every check it holds, in book order.
    """
    if isinstance(source, SeatCheck):
        checks = (source,)
        lines: list = []
    else:
        book = _source_book(source)
        checks = book.checks
        lines = [f"Checks in {book.title}:"]
    for check in checks:
        lines.append(f"{check.member} - verdict {check.verdict}")
        lines.extend(check.findings)
    if isinstance(source, SeatCheck):
        return "\n".join(lines)
    if len(lines) == 1:
        lines.append("Nothing here.")
    return "\n".join(lines)


def format_transports() -> str:
    """The external transports, in order, as one line."""
    return "External transports: " + ", ".join(TRANSPORTS)


def format_external_agents_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /externals.

    With nothing named, the shipped example seat
    book is shown - the example this slice ships -
    so the screen is never empty.
    """
    book = _source_book(source)
    lines = ["External agents as crew (M-137) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_seats(book))
    lines.append("")
    lines.append(format_check(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_external_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /externals grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    seat book; ``seat <member-id>`` shows one
    member's seat; ``check <member-id>`` derives
    one seat's check; a transport word (``mcp``)
    shows that transport's seats; ``transports``
    lists the transports. Anything else is a
    usage error naming the grammar. Returns
    ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head == "transports" and len(words) == 1:
        return ("transports", None)
    if head in ("seat", "check") and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if len(words) == 1:
        try:
            return ("transport", normalize_transport(words[0]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
