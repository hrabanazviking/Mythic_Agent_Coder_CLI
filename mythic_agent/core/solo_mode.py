"""Solo mode dignity (All-Features roadmap slice M-142).

Part VI continues here. The roadmap's words:
``with the crew off, the single coder loses
nothing - crew is an amplifier, never a
requirement.``

What already shipped, and what this slice adds:

* The crew itself is already data
  (``core/crew_members.py``, M-121): a member who
  amplifies is that casting's own member, read by
  its ``normalize_member_id`` by import. Crew
  sizing (``core/crew_sizing.py``, M-135) was
  checked: its solo is a size band - one pair of
  hands recommended by a task's shape - not a
  parity of capabilities, so it is not composed
  here. No crew enable/disable setting exists in
  the shipped config defaults, and the
  single-agent path is the app's ordinary road;
  what nothing holds is the dignity itself, as
  data: which capabilities the single coder
  holds, and what the crew adds to each when it
  is on - amplification, never a capability the
  solo coder lacks.
* This slice is that parity, as a pure layer: a
  capability record validated as data (one
  capability the single coder holds, named in
  plain words, with the work it is - and, when
  the crew amplifies it, the member who
  amplifies it and the gain that amplification
  brings), an amplification report per member
  whose counts and account are DERIVED from the
  records that member amplifies, a parity ledger
  whose rows, totals and account are DERIVED
  from the whole book, the shipped data file
  (``mythic_agent/data/solo_mode.yaml``) holding
  one example solo mode book in exactly the
  shape a real solo mode file takes, a loader
  for a solo mode file anywhere on disk, records
  shaped as session news, and a small in-memory
  registry model. This module disables no crew,
  spawns no agent, calls no model, persists
  nothing and imports no agent / UI code; the
  agent layer owns holding a solo mode book for
  a session.
Honesty rules, enforced here and pinned by tests:

* **Parity is derived, never stored loose.** A
  capability record names no parity of its own:
  that the single coder holds it is read off the
  book itself - every record in the book is a
  capability held solo - so a stored
  ``crew_only`` / ``requires_crew`` /
  ``solo_holds`` key on a record refuses as an
  unknown key, and no record can claim a
  capability exists only when the crew is on.
* **Crew only amplifies.** A record may name the
  member who amplifies it and the gain that
  amplification brings; the two stand together
  or not at all, and the gain names what the
  crew ADDS (hands, eyes, speed) - never the
  capability itself, which the record already
  holds solo.
* **A report is derived, never stored loose.**
  An amplification report's capability ids,
  capability names, count and account are read
  off the records that member amplifies, in held
  order, so a stored report that disagrees with
  the report derived from its records refuses. A
  report naming no account of its own refuses
  too.
* **The parity ledger is derived, never stored
  loose.** The ledger's rows are the book's
  amplification reports, in the order the
  records first name each amplifying member; its
  totals are read off the records (every
  capability held, those amplified, those
  standing unamplified) and its account is read
  off the rows and totals, so a stored ledger
  whose rows, totals or account disagree with
  the derived ledger refuses.
* **Members are the shipped casting's own.**
  Member ids read exactly as the M-121 layer
  reads them, composed by import, so the member
  a record names answers to exactly the
  validator a live crew answers to.
* **Data only - no live road is claimed.** A
  capability here is a validated record held as
  data: no crew is disabled or spawned, no agent
  runs, no model is called and nothing is
  persisted. The parity is visible through this
  slice's own /solo screen.
* **Malformed refuses.** A duplicate capability
  id in one book, a report or ledger naming a
  record the book holds no record for, and
  unknown keys in a record, a report, a ledger
  or a solo mode mapping all raise instead of
  being skipped or guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .validation import ValidationError

__all__ = [
    "PLAIN_EXPLANATION",
    "SOLO_MODE_RESOURCE",
    "SOLO_MODE_SCHEMA",
    "SOLO_MODE_SLICE",
    "USAGE",
    "AmplificationReport",
    "ParityLedger",
    "SoloBook",
    "SoloCapability",
    "SoloRegistry",
    "book_record",
    "build_book",
    "build_capability",
    "build_ledger",
    "build_report",
    "capability_record",
    "derive_ledger",
    "derive_report",
    "format_capabilities",
    "format_capability",
    "format_ledger",
    "format_report",
    "format_solo_mode_screen",
    "ledger_plain_words",
    "ledger_record",
    "load_solo_mode",
    "load_solo_mode_file",
    "parse_solo_mode_args",
    "plain_words",
    "report_plain_words",
    "report_record",
    "validate_book",
    "validate_capability",
    "validate_ledger",
    "validate_report",
]

SOLO_MODE_SLICE = "M-142"

#: The packaged data resource holding the example book.
SOLO_MODE_RESOURCE = "solo_mode.yaml"

#: The schema word a solo mode file must carry.
SOLO_MODE_SCHEMA = "mythic.solo_mode/1"

_CAPABILITY_KEYS = frozenset({
    "capability_id", "id", "capability", "name",
    "title", "headline", "detail", "description",
    "amplifier", "member", "member_id",
    "gain", "amplification",
})

_REPORT_KEYS = frozenset({
    "report_id", "id", "member", "member_id",
    "capability_ids", "capabilities", "capability_names",
    "amplifications", "count", "account", "statements",
})

_LEDGER_KEYS = frozenset({
    "ledger_id", "id", "rows", "reports",
    "total_capabilities", "capabilities",
    "total_amplified", "amplified",
    "total_plain", "plain",
    "account", "statements",
})

_BOOK_KEYS = frozenset({"title", "name"})

_SOLO_MODE_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "solo_note", "guide", "entries", "ledgers",
})

#: The shipped example book's title, held to this
#: by the loader's example check.
_EXAMPLE_TITLE = "Solo mode book at the M-141 slice boundary"

#: The shipped example's capability ids, in held
#: order, pinned by the loader.
_EXAMPLE_CAPABILITY_IDS = (
    "cap-planning", "cap-editing", "cap-testing",
    "cap-reviewing", "cap-remembering", "cap-costing",
    "cap-shipping", "cap-judging")

#: The shipped example's one ledger: its rows are
#: the amplifying members in first-named order and
#: its totals are pinned by the loader.
_EXAMPLE_LEDGER_ID = "ledger-m141-boundary"

_EXAMPLE_LEDGER_ROWS = (
    "architect", "forge_worker", "auditor", "scribe")

_EXAMPLE_LEDGER_TOTALS = (8, 7, 1)

_EXAMPLE_LEDGER_ACCOUNT = (
    "With the crew off, the single coder holds all "
    "8 capability(ies) and loses nothing.",
    "Crew members amplify 7 capability(ies) through "
    "4 member(s); 1 capability(ies) stand unamplified.",
    "Crew is an amplifier, never a requirement.",
)

#: The shipped example's pinned first report: the
#: architect's one amplification, its account
#: pinned word-for-word by the loader.
_EXAMPLE_FIRST_REPORT_ACCOUNT = (
    "architect amplifies 1 of the single coder's "
    "capabilities when the crew is on: planning.",
    "The crew is an amplifier, never a requirement.",
    "With the crew off, the single coder holds "
    "every one of these alone and loses nothing.",
)

PLAIN_EXPLANATION = (
    "Solo mode dignity: with the crew off, the "
    "single coder loses nothing - crew is an "
    "amplifier, never a requirement. A capability "
    "record names one capability the single coder "
    "holds, in plain words, and may name the crew "
    "member who amplifies it when the crew is on "
    "and what that amplification adds. The parity "
    "is derived from the held records, never "
    "stored loose: every capability in the book "
    "is held solo, and the amplification reports "
    "and the parity ledger are read off the "
    "records, so a stored form that disagrees "
    "refuses. This layer holds capabilities as "
    "data only; it disables no crew, spawns no "
    "agent, calls no model and persists nothing "
    "itself."
)

USAGE = (
    "Usage: /solo, /solo show, "
    "/solo capability <capability-id>, "
    "/solo member <member-id>, "
    "/solo report <member-id>, "
    "/solo ledger"
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


def _check_id_list(value: Any, what: str) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes)) \
            or not isinstance(value, (list, tuple)):
        raise ValueError(f"{what} must be a list, got {value!r}")
    return tuple(normalize_member_id(v) for v in value)


# ---------------------------------------------------------------------
# The capability record: one capability held solo.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SoloCapability:
    """One capability the single coder holds, crew off.

    ``capability`` is the capability's own word,
    ``title`` names it in plain words and ``detail``
    says what the work is. ``amplifier`` is the crew
    member who amplifies it when the crew is on and
    ``gain`` is what that amplification adds; the
    two stand together or not at all. The record
    names NO parity: that the single coder holds
    this capability is read off the book itself, so
    a record can never claim a capability exists
    only when the crew is on.
    """

    capability: str
    title: str
    detail: str
    amplifier: Optional[str] = None
    gain: Optional[str] = None
    capability_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.capability_id is not None:
            object.__setattr__(
                self, "capability_id",
                normalize_member_id(self.capability_id))
        object.__setattr__(
            self, "capability", normalize_member_id(self.capability))
        object.__setattr__(
            self, "title", _check_title(self.title, "a capability's title"))
        object.__setattr__(
            self, "detail",
            _check_long_text(self.detail, "a capability's detail"))
        if self.amplifier is not None:
            object.__setattr__(
                self, "amplifier", normalize_member_id(self.amplifier))
        if self.gain is not None:
            object.__setattr__(
                self, "gain",
                _check_long_text(self.gain, "a capability's gain"))
        if (self.amplifier is None) != (self.gain is None):
            raise ValueError(
                "a capability's gain names its amplifier: "
                "the two stand together or not at all")

    @property
    def amplified(self) -> bool:
        """Whether a crew member amplifies this capability."""
        return self.amplifier is not None

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "solo_capability",
            "slice": SOLO_MODE_SLICE,
            "capability_id": self.capability_id,
            "capability": self.capability,
            "title": self.title,
            "detail": self.detail,
            "amplifier": self.amplifier,
            "gain": self.gain,
            "amplified": self.amplified,
        }


def validate_capability(capability: Any) -> SoloCapability:
    """Validate one capability record into a SoloCapability.

    Accepts a SoloCapability or a mapping naming a
    ``capability`` (or ``name``), a ``title`` (or
    ``headline``), a ``detail`` (or
    ``description``), an optional ``capability_id``
    (or ``id``) and an optional amplifier -
    ``amplifier`` (or ``member`` / ``member_id``)
    together with a ``gain`` (or ``amplification``).
    Naming two spellings of one field with
    different values refuses, and unknown keys
    refuse - a stored parity key among them,
    because parity is derived from the book, never
    stored on a record.
    """
    if isinstance(capability, SoloCapability):
        return capability
    if not isinstance(capability, dict):
        raise ValueError(
            f"a capability record must be a mapping, "
            f"got {capability!r}")
    unknown = set(capability) - _CAPABILITY_KEYS
    if unknown:
        raise ValueError(
            "unknown capability-record keys: %s"
            % ", ".join(sorted(unknown)))
    name = _pick_any(capability, ("capability", "name"), "capabilities")
    if name is None:
        raise ValueError("a capability record is missing its capability")
    title = _pick_any(capability, ("title", "headline"), "titles")
    if title is None:
        raise ValueError("a capability record is missing its title")
    detail = _pick_any(capability, ("detail", "description"), "details")
    if detail is None:
        raise ValueError("a capability record is missing its detail")
    kwargs: Dict[str, Any] = {
        "capability": name, "title": title, "detail": detail}
    capability_id = _pick_any(
        capability, ("capability_id", "id"), "capability ids")
    if capability_id is not None:
        kwargs["capability_id"] = capability_id
    amplifier = _pick_any(
        capability, ("amplifier", "member", "member_id"), "amplifiers")
    if amplifier is not None:
        kwargs["amplifier"] = amplifier
    gain = _pick_any(capability, ("gain", "amplification"), "gains")
    if gain is not None:
        kwargs["gain"] = gain
    return SoloCapability(**kwargs)


def build_capability(capability: Any = None, **kwargs: Any) -> SoloCapability:
    """Build one validated capability record, from a mapping or field words."""
    if isinstance(capability, SoloCapability) and not kwargs:
        return capability
    if isinstance(capability, dict) or capability is None:
        merged: Dict[str, Any] = {}
        if isinstance(capability, dict):
            merged.update(capability)
        merged.update(kwargs)
        return validate_capability(merged)
    raise ValueError(
        f"a capability record must be a mapping, got {capability!r}")


def _check_capability_ref(value: Any) -> SoloCapability:
    if isinstance(value, SoloCapability):
        return value
    if isinstance(value, dict):
        return validate_capability(value)
    raise ValueError(f"a capability record is needed, got {value!r}")


def _held_capabilities(source: Any) -> Tuple[SoloCapability, ...]:
    """The capability records one source holds, in held order."""
    if isinstance(source, SoloBook):
        return source.entries
    if isinstance(source, SoloRegistry):
        return source.list_capabilities()
    if isinstance(source, (list, tuple)):
        return tuple(_check_capability_ref(e) for e in source)
    raise ValueError(f"capability records are needed, got {source!r}")


# ---------------------------------------------------------------------
# The amplification report: one member's amplifications, derived.
# ---------------------------------------------------------------------


def _report_account(member: str,
                    caps: Tuple[SoloCapability, ...]) -> Tuple[str, ...]:
    names = ", ".join(c.capability for c in caps)
    return (
        f"{member} amplifies {len(caps)} of the single "
        f"coder's capabilities when the crew is on: "
        f"{names}.",
        "The crew is an amplifier, never a requirement.",
        "With the crew off, the single coder holds "
        "every one of these alone and loses nothing.",
    )


@dataclass(frozen=True)
class AmplificationReport:
    """One member's amplification report, derived from records.

    ``capability_ids`` are the records that member
    amplifies, in held order; ``capabilities`` are
    their capability words in the same order;
    ``amplifications`` is their count; ``account``
    is the report's own account. Every field is a
    derivation: :func:`validate_report` judged
    against records refuses a report whose fields
    disagree with the report those records derive.
    """

    member: str
    capability_ids: Tuple[str, ...] = ()
    capabilities: Tuple[str, ...] = ()
    amplifications: int = 0
    account: Tuple[str, ...] = ()
    report_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.report_id is not None:
            object.__setattr__(
                self, "report_id", normalize_member_id(self.report_id))
        object.__setattr__(
            self, "member", normalize_member_id(self.member))
        capability_ids = _check_id_list(
            self.capability_ids, "a report's capability ids")
        if len(set(capability_ids)) != len(capability_ids):
            raise ValueError("a report names one capability twice")
        object.__setattr__(self, "capability_ids", capability_ids)
        capabilities = _check_id_list(
            self.capabilities, "a report's capabilities")
        if len(set(capabilities)) != len(capabilities):
            raise ValueError("a report names one capability twice")
        object.__setattr__(self, "capabilities", capabilities)
        object.__setattr__(
            self, "amplifications",
            _check_count(self.amplifications, "a report's amplifications"))
        if self.amplifications != len(capability_ids):
            raise ValueError(
                "a report's amplifications must be its "
                "capability ids' count")
        if len(capabilities) != len(capability_ids):
            raise ValueError(
                "a report's capabilities must name its "
                "capability ids one for one")
        object.__setattr__(self, "account", _check_account(self.account))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "solo_amplification_report",
            "slice": SOLO_MODE_SLICE,
            "report_id": self.report_id,
            "member": self.member,
            "capability_ids": list(self.capability_ids),
            "capabilities": list(self.capabilities),
            "amplifications": self.amplifications,
            "account": list(self.account),
        }


def derive_report(source: Any, member: Any) -> AmplificationReport:
    """Derive one member's amplification report from records.

    The report's capability ids, capability words,
    count and account are read off the records that
    member amplifies alone, in held order. A member
    no record names as an amplifier raises
    ``KeyError``.
    """
    wanted = normalize_member_id(member)
    caps = tuple(
        e for e in _held_capabilities(source) if e.amplifier == wanted)
    if not caps:
        raise KeyError(f"no capability records name amplifier {wanted!r}")
    return AmplificationReport(
        member=wanted,
        capability_ids=tuple(
            e.capability_id for e in caps if e.capability_id),
        capabilities=tuple(e.capability for e in caps),
        amplifications=len(caps),
        account=_report_account(wanted, caps))


def validate_report(report: Any, source: Any = None) -> AmplificationReport:
    """Validate one amplification report into an AmplificationReport.

    Accepts an AmplificationReport or a mapping
    naming a ``member`` (or ``member_id``),
    ``capability_ids``, ``capabilities`` (or
    ``capability_names``), ``amplifications`` (or
    ``count``), an ``account`` (or ``statements``)
    and an optional ``report_id`` (or ``id``). With
    *source* given (capability records, a book or a
    registry), the report is judged against the
    report derived from those records: a stored
    report whose member, capability ids,
    capabilities, count or account disagree with
    the derived report refuses. A report naming no
    account refuses too.
    """
    if isinstance(report, AmplificationReport):
        current = report
    elif isinstance(report, dict):
        unknown = set(report) - _REPORT_KEYS
        if unknown:
            raise ValueError(
                "unknown report keys: %s" % ", ".join(sorted(unknown)))
        member = _pick_any(report, ("member", "member_id"), "members")
        if member is None:
            raise ValueError("a report is missing its member")
        capability_ids = _pick_any(
            report, ("capability_ids",), "capability ids")
        if capability_ids is None:
            raise ValueError("a report is missing its capability ids")
        capabilities = _pick_any(
            report, ("capabilities", "capability_names"), "capabilities")
        if capabilities is None:
            raise ValueError("a report is missing its capabilities")
        amplifications = _pick_any(
            report, ("amplifications", "count"), "amplifications")
        if amplifications is None:
            raise ValueError("a report is missing its amplifications")
        account = _pick_any(report, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a report names no account of its own")
        kwargs: Dict[str, Any] = {
            "member": member, "capability_ids": capability_ids,
            "capabilities": capabilities,
            "amplifications": amplifications, "account": account}
        report_id = _pick_any(report, ("report_id", "id"), "report ids")
        if report_id is not None:
            kwargs["report_id"] = report_id
        current = AmplificationReport(**kwargs)
    else:
        raise ValueError(f"a report must be a mapping, got {report!r}")
    if source is not None:
        derived = derive_report(source, current.member)
        if (current.capability_ids != derived.capability_ids
                or current.capabilities != derived.capabilities
                or current.amplifications != derived.amplifications
                or current.account != derived.account):
            raise ValueError(
                "a stored report disagrees with the report "
                "derived from its records")
    return current


def build_report(report: Any = None, source: Any = None,
                 **kwargs: Any) -> AmplificationReport:
    """Build one validated report, from a mapping or field words."""
    if isinstance(report, AmplificationReport) and not kwargs:
        return validate_report(report, source)
    if isinstance(report, dict) or report is None:
        merged: Dict[str, Any] = {}
        if isinstance(report, dict):
            merged.update(report)
        merged.update(kwargs)
        return validate_report(merged, source)
    return validate_report(report, source)


# ---------------------------------------------------------------------
# The parity ledger: the whole book, derived.
# ---------------------------------------------------------------------


def _ledger_account(rows: Tuple[AmplificationReport, ...],
                    total_capabilities: int, total_amplified: int,
                    total_plain: int) -> Tuple[str, ...]:
    return (
        f"With the crew off, the single coder holds "
        f"all {total_capabilities} capability(ies) "
        f"and loses nothing.",
        f"Crew members amplify {total_amplified} "
        f"capability(ies) through {len(rows)} "
        f"member(s); {total_plain} capability(ies) "
        f"stand unamplified.",
        "Crew is an amplifier, never a requirement.",
    )


def _check_report_ref(value: Any) -> AmplificationReport:
    if isinstance(value, AmplificationReport):
        return value
    if isinstance(value, dict):
        return validate_report(value)
    raise ValueError(f"a report is needed, got {value!r}")


@dataclass(frozen=True)
class ParityLedger:
    """The parity ledger of one solo mode book.

    ``rows`` are the book's amplification reports,
    in the order the records first name each
    amplifying member; ``total_capabilities`` is
    every capability the book holds,
    ``total_amplified`` those a crew member
    amplifies and ``total_plain`` those standing
    unamplified, and ``account`` is read off the
    rows and totals. A ledger whose totals are not
    its own records' counts refuses at
    construction: the amplified total must be its
    rows' own sum and the plain total the rest.
    """

    rows: Tuple[AmplificationReport, ...] = ()
    total_capabilities: int = 0
    total_amplified: int = 0
    total_plain: int = 0
    account: Tuple[str, ...] = ()
    ledger_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.ledger_id is not None:
            object.__setattr__(
                self, "ledger_id", normalize_member_id(self.ledger_id))
        if isinstance(self.rows, (str, bytes)) \
                or not isinstance(self.rows, (list, tuple)):
            raise ValueError(
                f"a ledger's rows must be a list of reports, "
                f"got {self.rows!r}")
        rows = tuple(_check_report_ref(r) for r in self.rows)
        members = [row.member for row in rows]
        if len(set(members)) != len(members):
            raise ValueError("a ledger names one member twice")
        object.__setattr__(self, "rows", rows)
        object.__setattr__(
            self, "total_capabilities",
            _check_count(
                self.total_capabilities, "a ledger's total capabilities"))
        object.__setattr__(
            self, "total_amplified",
            _check_count(self.total_amplified, "a ledger's total amplified"))
        object.__setattr__(
            self, "total_plain",
            _check_count(self.total_plain, "a ledger's total plain"))
        amplified = sum(row.amplifications for row in rows)
        if self.total_amplified != amplified:
            raise ValueError(
                "a ledger's amplified total must be its "
                "own rows' sum")
        if self.total_plain != self.total_capabilities - amplified:
            raise ValueError(
                "a ledger's plain total must be the "
                "capabilities its rows do not amplify")
        object.__setattr__(self, "account", _check_account(self.account))

    def row_for(self, member: Any) -> AmplificationReport:
        """The row one member names in this ledger."""
        wanted = normalize_member_id(member)
        for row in self.rows:
            if row.member == wanted:
                return row
        raise KeyError(f"no row in the ledger: member {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "solo_parity_ledger",
            "slice": SOLO_MODE_SLICE,
            "ledger_id": self.ledger_id,
            "rows": [row.to_record() for row in self.rows],
            "total_capabilities": self.total_capabilities,
            "total_amplified": self.total_amplified,
            "total_plain": self.total_plain,
            "account": list(self.account),
        }


def derive_ledger(source: Any) -> ParityLedger:
    """Derive the parity ledger from capability records.

    The rows are the amplification reports in the
    order the records first name each amplifying
    member; the totals are the records' own counts
    and the account is read off the rows and
    totals. An empty source refuses - a ledger of
    nothing is no ledger.
    """
    entries = _held_capabilities(source)
    if not entries:
        raise ValueError("a ledger needs at least one capability record")
    members: list = []
    for entry in entries:
        if entry.amplifier is not None \
                and entry.amplifier not in members:
            members.append(entry.amplifier)
    rows = tuple(derive_report(entries, member) for member in members)
    total_amplified = sum(1 for e in entries if e.amplified)
    return ParityLedger(
        rows=rows,
        total_capabilities=len(entries),
        total_amplified=total_amplified,
        total_plain=len(entries) - total_amplified,
        account=_ledger_account(
            rows, len(entries), total_amplified,
            len(entries) - total_amplified))


def validate_ledger(ledger: Any, source: Any = None) -> ParityLedger:
    """Validate one parity ledger into a ParityLedger.

    Accepts a ParityLedger or a mapping naming
    ``rows`` (or ``reports``),
    ``total_capabilities`` (or ``capabilities``),
    ``total_amplified`` (or ``amplified``),
    ``total_plain`` (or ``plain``), an ``account``
    (or ``statements``) and an optional
    ``ledger_id`` (or ``id``). With *source* given,
    the ledger is judged against the ledger derived
    from those records: a stored ledger whose rows,
    totals or account disagree with the derived
    ledger refuses.
    """
    if isinstance(ledger, ParityLedger):
        current = ledger
    elif isinstance(ledger, dict):
        unknown = set(ledger) - _LEDGER_KEYS
        if unknown:
            raise ValueError(
                "unknown ledger keys: %s" % ", ".join(sorted(unknown)))
        rows = _pick_any(ledger, ("rows", "reports"), "rows")
        if rows is None:
            raise ValueError("a ledger is missing its rows")
        total_capabilities = _pick_any(
            ledger, ("total_capabilities", "capabilities"),
            "total capabilities")
        if total_capabilities is None:
            raise ValueError("a ledger is missing its total capabilities")
        total_amplified = _pick_any(
            ledger, ("total_amplified", "amplified"), "total amplified")
        if total_amplified is None:
            raise ValueError("a ledger is missing its total amplified")
        total_plain = _pick_any(
            ledger, ("total_plain", "plain"), "total plain")
        if total_plain is None:
            raise ValueError("a ledger is missing its total plain")
        account = _pick_any(ledger, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a ledger names no account of its own")
        kwargs: Dict[str, Any] = {
            "rows": rows, "total_capabilities": total_capabilities,
            "total_amplified": total_amplified,
            "total_plain": total_plain, "account": account}
        ledger_id = _pick_any(ledger, ("ledger_id", "id"), "ledger ids")
        if ledger_id is not None:
            kwargs["ledger_id"] = ledger_id
        current = ParityLedger(**kwargs)
    else:
        raise ValueError(f"a ledger must be a mapping, got {ledger!r}")
    if source is not None:
        derived = derive_ledger(source)
        if (current.rows != derived.rows
                or current.total_capabilities
                != derived.total_capabilities
                or current.total_amplified != derived.total_amplified
                or current.total_plain != derived.total_plain
                or current.account != derived.account):
            raise ValueError(
                "a stored ledger disagrees with the ledger "
                "derived from its records")
    return current


def build_ledger(ledger: Any = None, source: Any = None,
                 **kwargs: Any) -> ParityLedger:
    """Build one validated ledger, from a mapping or field words."""
    if isinstance(ledger, ParityLedger) and not kwargs:
        return validate_ledger(ledger, source)
    if isinstance(ledger, dict) or ledger is None:
        merged: Dict[str, Any] = {}
        if isinstance(ledger, dict):
            merged.update(ledger)
        merged.update(kwargs)
        return validate_ledger(merged, source)
    return validate_ledger(ledger, source)


# ---------------------------------------------------------------------
# The solo mode book: capability records in held order, ledgers judged.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SoloBook:
    """One solo mode book: capabilities held solo, held whole.

    ``entries`` are the capability records, in held
    order; ``ledgers`` are parity ledgers of the
    book - derivations, judged against the book's
    records by :func:`validate_book`;
    ``solo_note`` is the book's own note.
    """

    title: str = ""
    entries: Tuple[SoloCapability, ...] = ()
    ledgers: Tuple[ParityLedger, ...] = ()
    solo_note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book's title"))
        if isinstance(self.entries, (str, bytes)) \
                or not isinstance(self.entries, (list, tuple)):
            raise ValueError(
                f"a book's entries must be a list of capability "
                f"records, got {self.entries!r}")
        entries = tuple(_check_capability_ref(e) for e in self.entries)
        if not entries:
            raise ValueError(
                "a solo mode book holds at least one capability record")
        seen = set()
        for entry in entries:
            if entry.capability_id is not None:
                if entry.capability_id in seen:
                    raise ValueError(
                        f"a capability record named "
                        f"{entry.capability_id!r} already exists")
                seen.add(entry.capability_id)
        object.__setattr__(self, "entries", entries)
        if isinstance(self.ledgers, (str, bytes)) \
                or not isinstance(self.ledgers, (list, tuple)):
            raise ValueError(
                f"a book's ledgers must be a list of ledgers, "
                f"got {self.ledgers!r}")
        ledgers = tuple(
            led if isinstance(led, ParityLedger)
            else validate_ledger(led)
            for led in self.ledgers)
        seen_ledgers = set()
        for ledger in ledgers:
            if ledger.ledger_id is not None:
                if ledger.ledger_id in seen_ledgers:
                    raise ValueError(
                        f"a ledger named {ledger.ledger_id!r} "
                        f"already exists")
                seen_ledgers.add(ledger.ledger_id)
        object.__setattr__(self, "ledgers", ledgers)
        if not isinstance(self.solo_note, str):
            raise ValueError("a book's note must be text")
        object.__setattr__(self, "solo_note", self.solo_note.strip())

    def capability_for(self, capability_id: Any) -> SoloCapability:
        """The capability record one id names in this book."""
        wanted = normalize_member_id(capability_id)
        for entry in self.entries:
            if entry.capability_id == wanted:
                return entry
        raise KeyError(f"no capability record in the book: {wanted!r}")

    def capabilities_for(self, member: Any) -> Tuple[SoloCapability, ...]:
        """Every record one member amplifies, in held order."""
        wanted = normalize_member_id(member)
        return tuple(e for e in self.entries if e.amplifier == wanted)

    def capabilities_named(
            self, capability: Any) -> Tuple[SoloCapability, ...]:
        """Every record one capability word names, in held order."""
        wanted = normalize_member_id(capability)
        return tuple(e for e in self.entries if e.capability == wanted)

    def ledger_for(self, ledger_id: Any) -> ParityLedger:
        """The ledger one id names in this book."""
        wanted = normalize_member_id(ledger_id)
        for ledger in self.ledgers:
            if ledger.ledger_id == wanted:
                return ledger
        raise KeyError(f"no ledger in the book: {wanted!r}")

    def capability_ids(self) -> Tuple[str, ...]:
        """Every held capability id, in held order."""
        return tuple(e.capability_id for e in self.entries if e.capability_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "solo_book",
            "slice": SOLO_MODE_SLICE,
            "title": self.title,
            "capability_ids": list(self.capability_ids()),
            "capability_count": len(self.entries),
            "ledger_count": len(self.ledgers),
        }


def validate_book(data: Any, *, require_example: bool = False) -> SoloBook:
    """Validate one solo mode mapping into a SoloBook.

    The mapping names a ``schema`` (the solo mode
    schema word), a ``guide`` mapping (its
    ``title``), an ``entries`` list and an optional
    ``ledgers`` list. Every record stands on its own
    validation, then the whole is judged: capability
    ids unique, and every ledger judged against the
    book's own capability records. With
    ``require_example`` the shipped example is held
    to its pinned shape: the pinned title, records
    and ledger, the ledger's pinned rows, totals and
    account word-for-word, and the first report's
    pinned account. Problems raise
    :class:`ValidationError` or ``ValueError``.
    """
    if isinstance(data, SoloBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a solo mode book must be a mapping, got {data!r}")
    unknown = set(data) - _SOLO_MODE_KEYS
    if unknown:
        raise ValidationError(
            "unknown solo mode keys: %s" % ", ".join(sorted(unknown)))
    if data.get("schema") != SOLO_MODE_SCHEMA:
        raise ValidationError(
            f"a solo mode book must carry schema "
            f"{SOLO_MODE_SCHEMA!r}, got {data.get('schema')!r}")
    if "entries" not in data:
        raise ValidationError("a solo mode book is missing its entries")
    if not isinstance(data["entries"], (list, tuple)):
        raise ValidationError("a solo mode book's entries must be a list")
    if data.get("ledgers") is not None \
            and not isinstance(data["ledgers"], (list, tuple)):
        raise ValidationError("a solo mode book's ledgers must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a solo mode book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a solo mode book is missing its title")
        note = data.get("solo_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a solo mode book's note must be text")
        book = SoloBook(
            title=title, entries=tuple(data["entries"]),
            ledgers=tuple(data.get("ledgers") or ()),
            solo_note=note)
        for ledger in book.ledgers:
            validate_ledger(ledger, book.entries)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if require_example:
        if book.title != _EXAMPLE_TITLE:
            raise ValidationError(
                "the shipped example solo mode book's title is "
                "not the pinned title")
        if book.capability_ids() != _EXAMPLE_CAPABILITY_IDS:
            raise ValidationError(
                "the shipped example's capability records are not "
                "the pinned records")
        ledger = book.ledger_for(_EXAMPLE_LEDGER_ID)
        if tuple(r.member for r in ledger.rows) != _EXAMPLE_LEDGER_ROWS:
            raise ValidationError(
                "the shipped example ledger does not name "
                "its pinned rows")
        totals = (
            ledger.total_capabilities, ledger.total_amplified,
            ledger.total_plain)
        if totals != _EXAMPLE_LEDGER_TOTALS:
            raise ValidationError(
                "the shipped example ledger does not carry "
                "its pinned totals")
        if ledger.account != _EXAMPLE_LEDGER_ACCOUNT:
            raise ValidationError(
                "the shipped example ledger does not carry "
                "its pinned account word-for-word")
        first = derive_report(book.entries, "architect")
        if first.account != _EXAMPLE_FIRST_REPORT_ACCOUNT:
            raise ValidationError(
                "the shipped example's first report does not "
                "carry its pinned account word-for-word")
    return book


def build_book(book: Any = None, **kwargs: Any) -> SoloBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, SoloBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "entries" in book or "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return SoloBook(**merged)
    if book is None:
        return SoloBook(**kwargs)
    raise ValueError(f"a solo mode book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> SoloBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_solo_mode(
        data: Optional[Dict[str, Any]] = None) -> SoloBook:
    """Load and validate the shipped example book (or *data*).

    The shipped file is held to the example check:
    the pinned title, capability records and ledger
    - the M-141 boundary book of capabilities and
    the parity ledger of it - so the shipped book
    covers the boundary this slice exists to hold.
    """
    raw = data if data is not None else load_resource(SOLO_MODE_RESOURCE)
    return _book_from(raw, require_example=True)


def load_solo_mode_file(path: Any) -> SoloBook:
    """Load and validate a solo mode book from a file at *path*.

    Any file in the solo mode shape, anywhere on
    disk, validated whole - a malformed file raises
    :class:`ValidationError` naming the problem, and
    a missing file raises ``FileNotFoundError``. The
    example check is not held: a real solo mode book
    stands on its own records.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held record by record, in held order.
# ---------------------------------------------------------------------


class SoloRegistry:
    """One session's solo mode book, held record by record.

    The registry holds capability records, never
    reports or ledgers: both are derivations, read
    off held records at call time, so nothing here
    can hold a total stale.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._entries: Dict[str, SoloCapability] = {}
        self._order: list = []
        self._next_entry = 1
        if book is not None:
            self.register_book(book)

    def _fresh_capability_id(self, held_ids: Any) -> str:
        while f"solo-{self._next_entry}" in held_ids:
            self._next_entry += 1
        fresh = f"solo-{self._next_entry}"
        self._next_entry += 1
        return fresh

    def register_capability(self, capability: Any) -> SoloCapability:
        """Register one capability record into the held book.

        A record with no id is given a deterministic
        ``solo-N`` id. A record id already standing
        here refuses.
        """
        validated = build_capability(capability)
        held_ids = set(self._entries)
        if validated.capability_id is not None \
                and validated.capability_id in held_ids:
            raise ValueError(
                f"a capability record named "
                f"{validated.capability_id!r} already exists")
        if validated.capability_id is None:
            validated = replace(
                validated,
                capability_id=self._fresh_capability_id(held_ids))
        self._entries[validated.capability_id] = validated
        self._order.append(validated.capability_id)
        return validated

    def register_book(self, book: Any) -> SoloBook:
        """Register every capability record of one book, in order.

        The first book held sets the title; a later
        book under a different title refuses, as does
        a book naming a held record id. The book's
        ledgers are derivations, not holdings, and
        are not held.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a solo mode book "
                "under a different title")
        for entry in validated.entries:
            if entry.capability_id in self._entries:
                raise ValueError(
                    f"a capability record named "
                    f"{entry.capability_id!r} already exists")
        self._title = validated.title
        for entry in validated.entries:
            self.register_capability(entry)
        return self.book()

    def get_capability(self, capability_id: Any) -> SoloCapability:
        """The capability record one id names among the held records."""
        wanted = normalize_member_id(capability_id)
        if wanted not in self._entries:
            raise KeyError(f"unknown capability record: {wanted!r}")
        return self._entries[wanted]

    def list_capabilities(self) -> Tuple[SoloCapability, ...]:
        """Every held capability record, in the order they were held."""
        return tuple(self._entries[e] for e in self._order)

    def book(self) -> SoloBook:
        """The held capability records as one validated book."""
        if self._title is None:
            raise ValueError("no solo mode book is held yet")
        return SoloBook(
            title=self._title, entries=self.list_capabilities())

    def report_for(self, member: Any) -> AmplificationReport:
        """Derive one member's amplification report, at call time.

        The report is derived from the held records
        that member amplifies, read at call time -
        the registry holds records, and this report
        is derived from them.
        """
        return derive_report(self.list_capabilities(), member)

    def ledger(self) -> ParityLedger:
        """Derive the parity ledger of the held book.

        The rows, totals and account are the held
        records' own counts, read at call time.
        """
        return derive_ledger(self.list_capabilities())


# ---------------------------------------------------------------------
# Solo mode news, shaped as session records.
# ---------------------------------------------------------------------


def capability_record(capability: Any) -> Dict[str, Any]:
    """The session-news record of one capability record."""
    current = capability if isinstance(capability, SoloCapability) \
        else build_capability(capability)
    record = current.to_record()
    record["news"] = True
    if current.amplifier is not None:
        record["headline"] = (
            f"{current.capability} is held by the single "
            f"coder alone; {current.amplifier} amplifies "
            f"it when the crew is on.")
    else:
        record["headline"] = (
            f"{current.capability} is held by the single "
            f"coder alone.")
    return record


def report_record(report: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one amplification report.

    With *source* given, the report is first judged
    against the records it belongs to.
    """
    current = validate_report(report, source)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.member} amplifies "
        f"{current.amplifications} capability(ies) - "
        f"amplification, never a requirement.")
    return record


def ledger_record(ledger: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of the parity ledger.

    With *source* given, the ledger is first judged
    against the records it belongs to.
    """
    current = validate_ledger(ledger, source)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Solo parity: {current.total_capabilities} "
        f"capability(ies) held, none lost with the "
        f"crew off.")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one solo mode book."""
    current = book if isinstance(book, SoloBook) else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Solo mode book {current.title}: "
        f"{record['capability_count']} capability "
        f"record(s), {record['ledger_count']} ledger(s).")
    return record


def plain_words(capability: Any) -> str:
    """One capability record, in one plain sentence."""
    current = capability if isinstance(capability, SoloCapability) \
        else build_capability(capability)
    text = (
        f"{current.capability} - {current.title}: "
        f"{current.detail}")
    if current.amplifier is not None:
        text += (
            f" {current.amplifier} amplifies it when "
            f"the crew is on: {current.gain}")
    return text


def _book_members(book: SoloBook) -> Tuple[str, ...]:
    members: list = []
    for entry in book.entries:
        if entry.amplifier is not None \
                and entry.amplifier not in members:
            members.append(entry.amplifier)
    return tuple(members)


def report_plain_words(source: Any) -> str:
    """Reports in plain words: every report, in full.

    Accepts an AmplificationReport or a SoloBook.
    Each report is told whole - its member and its
    account.
    """
    if isinstance(source, AmplificationReport):
        reports = (validate_report(source),)
        title = None
    elif isinstance(source, SoloBook):
        reports = tuple(
            derive_report(source.entries, member)
            for member in _book_members(source))
        title = source.title
    else:
        raise ValueError(f"a solo mode source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    for report in reports:
        lines.append(
            f"{report.member} - {report.amplifications} "
            f"amplification(s)")
        lines.extend(report.account)
    return "\n".join(lines)


def ledger_plain_words(source: Any) -> str:
    """The parity ledger in plain words, in full.

    Accepts a ParityLedger or a SoloBook. The
    ledger is told whole - its rows and its
    account.
    """
    if isinstance(source, ParityLedger):
        ledger = validate_ledger(source)
        title = None
    elif isinstance(source, SoloBook):
        ledger = derive_ledger(source.entries)
        title = source.title
    else:
        raise ValueError(f"a solo mode source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Parity ledger:")
    for row in ledger.rows:
        lines.append(
            f"{row.member} - {row.amplifications} "
            f"amplification(s)")
    lines.extend(ledger.account)
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Screens: the formatters and the shared /solo grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> SoloBook:
    if source is None:
        return load_solo_mode()
    if isinstance(source, SoloRegistry):
        return source.book()
    if isinstance(source, SoloBook):
        return source
    raise ValueError(f"a solo mode book is needed, got {source!r}")


def format_capability(capability: Any) -> str:
    """One capability record as a screen line."""
    current = capability if isinstance(capability, SoloCapability) \
        else build_capability(capability)
    line = (
        f"{current.capability_id or '-'}: {current.capability} "
        f"- {current.title}")
    if current.amplifier is not None:
        line += f" (amplified by {current.amplifier})"
    return line


def format_capabilities(source: Any = None, member: Any = None) -> str:
    """Capability records of one book, in held order.

    With *member* given, only the records that
    member amplifies are shown.
    """
    book = _source_book(source)
    entries = book.entries if member is None \
        else book.capabilities_for(member)
    lines = [format_capability(entry) for entry in entries]
    if not lines:
        lines.append("No capability records are held.")
    return "\n".join(lines)


def format_report(source: Any = None) -> str:
    """Reports as screen blocks: member over derived account.

    Accepts an AmplificationReport or a SoloBook; a
    book shows every report it derives, in book
    order.
    """
    if isinstance(source, AmplificationReport):
        reports = (validate_report(source),)
        lines: list = []
    else:
        book = _source_book(source)
        reports = tuple(
            derive_report(book.entries, member)
            for member in _book_members(book))
        lines = [f"Reports in {book.title}:"]
    for report in reports:
        lines.append(
            f"{report.member} - {report.amplifications} "
            f"amplification(s): "
            f"{', '.join(report.capabilities)}")
        lines.extend(report.account)
    if isinstance(source, AmplificationReport):
        return "\n".join(lines)
    if len(lines) == 1:
        lines.append("Nothing here.")
    return "\n".join(lines)


def format_ledger(source: Any = None) -> str:
    """The parity ledger as a screen block.

    Accepts a ParityLedger or a SoloBook; a book
    shows the ledger it derives, its rows over its
    derived account.
    """
    if isinstance(source, ParityLedger):
        ledger = validate_ledger(source)
        lines: list = []
    else:
        book = _source_book(source)
        ledger = derive_ledger(book.entries)
        lines = [f"Ledger in {book.title}:"]
    lines.append("Parity ledger:")
    for row in ledger.rows:
        lines.append(
            f"{row.member} - {row.amplifications} "
            f"amplification(s)")
    lines.extend(ledger.account)
    return "\n".join(lines)


def format_solo_mode_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /solo.

    With nothing named, the shipped example solo
    mode book is shown - the example this slice
    ships - so the screen is never empty.
    """
    book = _source_book(source)
    lines = ["Solo mode dignity (M-142) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_capabilities(book))
    lines.append("")
    lines.append(format_report(book))
    lines.append("")
    lines.append(format_ledger(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_solo_mode_args(args: Any) -> Tuple[str, Any]:
    """Parse the /solo grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the solo
    mode book; ``capability <capability-id>`` shows
    one capability record; ``member <member-id>``
    shows the records one member amplifies;
    ``report <member-id>`` shows one member's
    amplification report; ``ledger`` shows the
    parity ledger. Anything else is a usage error
    naming the grammar. Returns
    ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head == "ledger" and len(words) == 1:
        return ("ledger", None)
    if head in ("capability", "member", "report") and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
