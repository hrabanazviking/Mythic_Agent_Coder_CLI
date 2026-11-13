"""The Mythic Coder building itself (roadmap slice M-141).

Part VI continues here. The roadmap's words:
``the standing dogfood - each part of this road is
built by the crew it improves, under the
coordinator's discipline (as the October forge
proved it can).``

What already shipped, and what this slice adds:

* The crew is already data (``core/crew_members.py``,
  M-121): the members who build are that casting's
  own members, read by its ``normalize_member_id``
  by import. The slices they build are the road's
  own (``core/roadmap_slices.py``, M-017): a build
  record names a slice by the worktrees layer's
  ``normalize_slice_id`` (M-124) by import, and the
  part that slice belongs to is read off the shipped
  roadmap itself - never stored on the record, so a
  record can never claim a part the road does not
  give its slice. The cost court (M-140) was checked
  and is not composed: a build record names no spend.
  What nothing holds is the dogfood itself: which
  member built which slice of this road, held part
  by part under the coordinator's discipline.
* This slice is that dogfood, as a pure layer: a
  build record validated as data (the member who
  built, the slice built and a title naming the
  build - the record's part DERIVED from the shipped
  roadmap, never stored), a per-part report whose
  counts and account are DERIVED from the records of
  that part, the coordinator's ledger whose rows and
  account are DERIVED from the whole book, the
  shipped data file
  (``mythic_agent/data/dogfood.yaml``) holding one
  example dogfood book in exactly the shape a real
  dogfood file takes, a loader for a dogfood file
  anywhere on disk, records shaped as session news,
  and a small in-memory registry model. This module
  builds nothing live, spawns no agent, calls no
  model, persists nothing and imports no agent / UI
  code; the agent layer owns holding a dogfood book
  for a session.
Honesty rules, enforced here and pinned by tests:

* **A part is derived, never stored loose.** A
  build record names a slice and no part: its part
  is read off the shipped roadmap
  (``core/roadmap_slices.load_roadmap``, composed by
  import, never re-implemented), so a record naming
  a slice the road does not hold refuses, and a
  stored part key on a record refuses as an unknown
  key - a record can never claim its slice belongs
  to a part the road does not say.
* **A report is derived, never stored loose.** A
  per-part report's entry ids, builds, slices,
  members and account are read off the build records
  of that part, in held order, so a stored report
  that disagrees with the report derived from its
  records refuses. A report naming no account of its
  own refuses too.
* **The coordinator's ledger is derived, never
  stored loose.** The ledger's rows are the book's
  per-part reports, in the order the records first
  name each part; its totals are read off the rows
  and its account is read off the rows, so a stored
  ledger whose keeper, rows, totals or account
  disagree with the derived ledger refuses. The
  keeper is always the coordinator - the discipline
  this slice's roadmap words name; a ledger kept by
  anyone else refuses. The coordinator is not a crew
  member: the shipped offices note names the lead
  session itself the coordinator, never a working
  office, so the keeper word is this slice's own
  constant, not a casting member.
* **Members and slices are the shipped layers'
  own.** Member ids read exactly as the M-121 layer
  reads them and slice ids exactly as the worktrees
  layer reads them, both composed by import, so the
  member and slice a record names answer to exactly
  the validators a live build answers to.
* **Data only - no live road is claimed.** A build
  here is a validated record held as data: no slice
  is actually built, no crew runs live, nothing is
  merged or banked and nothing here claims a build
  happened live. The dogfood is visible through this
  slice's own /dogfood screen.
* **Malformed refuses.** A duplicate entry id in
  one book, a report or ledger naming a record the
  book holds no record for, and unknown keys in a
  record, a report, a ledger or a dogfood mapping
  all raise instead of being skipped or guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .roadmap_slices import TOTAL_PARTS, load_roadmap
from .validation import ValidationError
from .worktrees import normalize_slice_id

__all__ = [
    "COORDINATOR_KEEPER",
    "DOGFOOD_RESOURCE",
    "DOGFOOD_SCHEMA",
    "DOGFOOD_SLICE",
    "PLAIN_EXPLANATION",
    "USAGE",
    "CoordinatorLedger",
    "DogfoodBook",
    "DogfoodEntry",
    "DogfoodReport",
    "DogfoodRegistry",
    "book_record",
    "build_book",
    "build_entry",
    "build_ledger",
    "build_report",
    "derive_ledger",
    "derive_report",
    "entry_record",
    "format_dogfood_screen",
    "format_entries",
    "format_entry",
    "format_ledger",
    "format_report",
    "ledger_plain_words",
    "ledger_record",
    "load_dogfood",
    "load_dogfood_file",
    "parse_dogfood_args",
    "plain_words",
    "report_plain_words",
    "report_record",
    "validate_book",
    "validate_entry",
    "validate_ledger",
    "validate_report",
]

DOGFOOD_SLICE = "M-141"

#: The packaged data resource holding the example book.
DOGFOOD_RESOURCE = "dogfood.yaml"

#: The schema word a dogfood file must carry.
DOGFOOD_SCHEMA = "mythic.dogfood/1"

#: The keeper of the ledger: the coordinator, whose
#: discipline this slice's roadmap words name. The
#: coordinator is the lead session itself, not a
#: crew member, so this word is no casting member.
COORDINATOR_KEEPER = "coordinator"

_ENTRY_KEYS = frozenset({
    "entry_id", "id", "member", "member_id",
    "slice", "slice_id", "title", "name",
})

_REPORT_KEYS = frozenset({
    "report_id", "id", "part", "entries", "entry_ids",
    "builds", "build_count", "slices", "slice_ids",
    "members", "member_ids", "account", "statements",
})

_LEDGER_KEYS = frozenset({
    "ledger_id", "id", "keeper", "coordinator",
    "rows", "reports",
    "total_builds", "builds",
    "total_slices", "slices",
    "total_parts", "parts",
    "account", "statements",
})

_BOOK_KEYS = frozenset({"title", "name"})

_DOGFOOD_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "dogfood_note", "guide", "entries", "ledgers",
})

#: The shipped example book's title, held to this
#: by the loader's example check.
_EXAMPLE_TITLE = "Dogfood book at the M-140 slice boundary"

#: The shipped example's entry ids, in held order,
#: pinned by the loader.
_EXAMPLE_ENTRY_IDS = (
    "entry-m120-forge", "entry-m121-architect",
    "entry-m138-scribe", "entry-m139-forge",
    "entry-m140-forge", "entry-m140-auditor")

#: The shipped example's one ledger: kept by the
#: coordinator, its rows and totals pinned by the
#: loader.
_EXAMPLE_LEDGER_ID = "ledger-m140-boundary"

_EXAMPLE_LEDGER_ROWS = (5, 6)

_EXAMPLE_LEDGER_TOTALS = (6, 5, 2)

_EXAMPLE_LEDGER_ACCOUNT = (
    "The coordinator keeps this ledger: 2 part row(s) "
    "across 2 part(s).",
    "Total: 6 build(s) across 5 slice(s).",
    "The standing dogfood: each part of this road is "
    "built by the crew it improves.",
)

#: The shipped example's pinned first report: part
#: V's one build, its account pinned word-for-word
#: by the loader.
_EXAMPLE_FIRST_REPORT_ACCOUNT = (
    "Part 5 (Autonomy & Safety) was built by the crew "
    "it improves in 1 build(s) across 1 slice(s).",
    "Builders: forge_worker.",
    "Every build stands under the coordinator's "
    "discipline.",
)

PLAIN_EXPLANATION = (
    "The dogfood: this road builds itself - each "
    "part is built by the crew it improves, under "
    "the coordinator's discipline. A build record "
    "names the member who built and the slice built; "
    "its part is derived from the shipped roadmap, "
    "never stored on the record. A report reads one "
    "part's builds off its records, derived, never "
    "stored loose, and the coordinator keeps the "
    "ledger of the whole book the same way. This "
    "layer holds builds as data only; it builds "
    "nothing live, runs no crew and persists "
    "nothing itself."
)

USAGE = (
    "Usage: /dogfood, /dogfood show, "
    "/dogfood entry <entry-id>, "
    "/dogfood member <member-id>, "
    "/dogfood slice <slice-id>, "
    "/dogfood part <part-number>, "
    "/dogfood ledger"
)

_ROADMAP = None


def _roadmap():
    """The shipped roadmap, loaded once, by import."""
    global _ROADMAP
    if _ROADMAP is None:
        _ROADMAP = load_roadmap()
    return _ROADMAP


def _slice_part(slice_id: str) -> int:
    """The part the shipped road gives one slice."""
    try:
        return _roadmap().slice(slice_id).part
    except KeyError:
        raise ValueError(
            f"the shipped roadmap holds no slice "
            f"{slice_id!r}") from None


def _part_title(part: int) -> str:
    """The title the shipped road gives one part."""
    return _roadmap().part(part).title


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


def _check_part(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"a part must be a number, got {value!r}")
    if value < 1 or value > TOTAL_PARTS:
        raise ValueError(
            f"a part must be between 1 and {TOTAL_PARTS}, "
            f"got {value!r}")
    return value


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
# The build record: one member building one slice.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class DogfoodEntry:
    """One build record: a member built one slice.

    ``member`` is the member who built, ``slice_id``
    the slice built and ``title`` names the build.
    The record names NO part: its part is DERIVED
    from the shipped roadmap (see :attr:`part`), so
    a record can never claim a part the road does
    not give its slice, and a slice the road does
    not hold refuses at construction.
    """

    member: str
    slice_id: str
    title: str
    entry_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.entry_id is not None:
            object.__setattr__(
                self, "entry_id", normalize_member_id(self.entry_id))
        object.__setattr__(
            self, "member", normalize_member_id(self.member))
        object.__setattr__(
            self, "slice_id", normalize_slice_id(self.slice_id))
        object.__setattr__(
            self, "title", _check_title(self.title, "a build's title"))
        _slice_part(self.slice_id)

    @property
    def part(self) -> int:
        """This build's part, derived from the shipped roadmap."""
        return _slice_part(self.slice_id)

    @property
    def part_title(self) -> str:
        """The shipped road's title for this build's part."""
        return _part_title(self.part)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "dogfood_entry",
            "slice": DOGFOOD_SLICE,
            "entry_id": self.entry_id,
            "member": self.member,
            "slice_id": self.slice_id,
            "title": self.title,
            "part": self.part,
            "part_title": self.part_title,
        }


def validate_entry(entry: Any) -> DogfoodEntry:
    """Validate one build record into a DogfoodEntry.

    Accepts a DogfoodEntry or a mapping naming a
    ``member`` (or ``member_id``), a ``slice_id``
    (or ``slice``), a ``title`` (or ``name``) and an
    optional ``entry_id`` (or ``id``). Naming two
    spellings of one field with different values
    refuses, and unknown keys refuse - a stored
    part key among them, because a part is derived
    from the shipped roadmap, never stored.
    """
    if isinstance(entry, DogfoodEntry):
        return entry
    if not isinstance(entry, dict):
        raise ValueError(f"a build record must be a mapping, got {entry!r}")
    unknown = set(entry) - _ENTRY_KEYS
    if unknown:
        raise ValueError(
            "unknown build-record keys: %s" % ", ".join(sorted(unknown)))
    member = _pick_any(entry, ("member", "member_id"), "members")
    if member is None:
        raise ValueError("a build record is missing its member")
    slice_id = _pick_any(entry, ("slice_id", "slice"), "slices")
    if slice_id is None:
        raise ValueError("a build record is missing its slice")
    title = _pick_any(entry, ("title", "name"), "titles")
    if title is None:
        raise ValueError("a build record is missing its title")
    kwargs: Dict[str, Any] = {
        "member": member, "slice_id": slice_id, "title": title}
    entry_id = _pick_any(entry, ("entry_id", "id"), "entry ids")
    if entry_id is not None:
        kwargs["entry_id"] = entry_id
    return DogfoodEntry(**kwargs)


def build_entry(entry: Any = None, **kwargs: Any) -> DogfoodEntry:
    """Build one validated build record, from a mapping or field words."""
    if isinstance(entry, DogfoodEntry) and not kwargs:
        return entry
    if isinstance(entry, dict) or entry is None:
        merged: Dict[str, Any] = {}
        if isinstance(entry, dict):
            merged.update(entry)
        merged.update(kwargs)
        return validate_entry(merged)
    raise ValueError(f"a build record must be a mapping, got {entry!r}")


def _check_entry_ref(value: Any) -> DogfoodEntry:
    if isinstance(value, DogfoodEntry):
        return value
    if isinstance(value, dict):
        return validate_entry(value)
    raise ValueError(f"a build record is needed, got {value!r}")


def _held_entries(source: Any) -> Tuple[DogfoodEntry, ...]:
    """The build records one source holds, in held order."""
    if isinstance(source, DogfoodBook):
        return source.entries
    if isinstance(source, DogfoodRegistry):
        return source.list_entries()
    if isinstance(source, (list, tuple)):
        return tuple(_check_entry_ref(e) for e in source)
    raise ValueError(f"build records are needed, got {source!r}")


# ---------------------------------------------------------------------
# The report: one part's builds, derived.
# ---------------------------------------------------------------------


def _report_account(part: int, entries: Tuple[DogfoodEntry, ...]) -> Tuple[str, ...]:
    slices: list = []
    members: list = []
    for entry in entries:
        if entry.slice_id not in slices:
            slices.append(entry.slice_id)
        if entry.member not in members:
            members.append(entry.member)
    return (
        f"Part {part} ({_part_title(part)}) was built by "
        f"the crew it improves in {len(entries)} build(s) "
        f"across {len(slices)} slice(s).",
        f"Builders: {', '.join(members)}.",
        "Every build stands under the coordinator's discipline.",
    )


@dataclass(frozen=True)
class DogfoodReport:
    """One part's dogfood report, derived from its records.

    ``entry_ids`` are the part's build records in
    held order; ``builds`` is their count; ``slices``
    and ``members`` are the distinct slices built and
    builders named, in held order; ``account`` is the
    report's own account of the part. Every field is
    a derivation: :func:`validate_report` judged
    against records refuses a report whose fields
    disagree with the report those records derive.
    """

    part: int
    entry_ids: Tuple[str, ...] = ()
    builds: int = 0
    slices: Tuple[str, ...] = ()
    members: Tuple[str, ...] = ()
    account: Tuple[str, ...] = ()
    report_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.report_id is not None:
            object.__setattr__(
                self, "report_id", normalize_member_id(self.report_id))
        object.__setattr__(self, "part", _check_part(self.part))
        entry_ids = _check_id_list(self.entry_ids, "a report's entry ids")
        if len(set(entry_ids)) != len(entry_ids):
            raise ValueError("a report names one build record twice")
        object.__setattr__(self, "entry_ids", entry_ids)
        object.__setattr__(
            self, "builds", _check_count(self.builds, "a report's builds"))
        if self.builds != len(entry_ids):
            raise ValueError(
                "a report's builds must be its entry ids' count")
        slices = tuple(
            normalize_slice_id(s) for s in _check_id_list(
                self.slices, "a report's slices"))
        if len(set(slices)) != len(slices):
            raise ValueError("a report names one slice twice")
        object.__setattr__(self, "slices", slices)
        members = _check_id_list(self.members, "a report's members")
        if len(set(members)) != len(members):
            raise ValueError("a report names one member twice")
        object.__setattr__(self, "members", members)
        object.__setattr__(self, "account", _check_account(self.account))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "dogfood_report",
            "slice": DOGFOOD_SLICE,
            "report_id": self.report_id,
            "part": self.part,
            "part_title": _part_title(self.part),
            "entry_ids": list(self.entry_ids),
            "builds": self.builds,
            "slices": list(self.slices),
            "members": list(self.members),
            "account": list(self.account),
        }


def derive_report(source: Any, part: Any) -> DogfoodReport:
    """Derive one part's report from build records, in held order.

    The report's entry ids, builds, slices, members
    and account are read off the records of that
    part alone. A part no record names raises
    ``KeyError``.
    """
    wanted = _check_part(part)
    entries = tuple(
        e for e in _held_entries(source) if e.part == wanted)
    if not entries:
        raise KeyError(f"no build records name part {wanted!r}")
    slices: list = []
    members: list = []
    for entry in entries:
        if entry.slice_id not in slices:
            slices.append(entry.slice_id)
        if entry.member not in members:
            members.append(entry.member)
    return DogfoodReport(
        part=wanted,
        entry_ids=tuple(e.entry_id for e in entries if e.entry_id),
        builds=len(entries),
        slices=tuple(slices),
        members=tuple(members),
        account=_report_account(wanted, entries))


def validate_report(report: Any, source: Any = None) -> DogfoodReport:
    """Validate one per-part report into a DogfoodReport.

    Accepts a DogfoodReport or a mapping naming a
    ``part``, ``entry_ids`` (or ``entries``),
    ``builds`` (or ``build_count``), ``slices`` (or
    ``slice_ids``), ``members`` (or ``member_ids``),
    an ``account`` (or ``statements``) and an
    optional ``report_id`` (or ``id``). With *source*
    given (build records, a book or a registry), the
    report is judged against the report derived from
    those records: a stored report whose part, entry
    ids, builds, slices, members or account disagree
    with the derived report refuses. A report naming
    no account refuses too.
    """
    if isinstance(report, DogfoodReport):
        current = report
    elif isinstance(report, dict):
        unknown = set(report) - _REPORT_KEYS
        if unknown:
            raise ValueError(
                "unknown report keys: %s" % ", ".join(sorted(unknown)))
        if "part" not in report:
            raise ValueError("a report is missing its part")
        entry_ids = _pick_any(
            report, ("entry_ids", "entries"), "entry ids")
        if entry_ids is None:
            raise ValueError("a report is missing its entry ids")
        builds = _pick_any(report, ("builds", "build_count"), "builds")
        if builds is None:
            raise ValueError("a report is missing its builds")
        slices = _pick_any(report, ("slices", "slice_ids"), "slices")
        if slices is None:
            raise ValueError("a report is missing its slices")
        members = _pick_any(report, ("members", "member_ids"), "members")
        if members is None:
            raise ValueError("a report is missing its members")
        account = _pick_any(report, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a report names no account of its own")
        kwargs: Dict[str, Any] = {
            "part": report["part"], "entry_ids": entry_ids,
            "builds": builds, "slices": slices,
            "members": members, "account": account}
        report_id = _pick_any(report, ("report_id", "id"), "report ids")
        if report_id is not None:
            kwargs["report_id"] = report_id
        current = DogfoodReport(**kwargs)
    else:
        raise ValueError(f"a report must be a mapping, got {report!r}")
    if source is not None:
        derived = derive_report(source, current.part)
        if (current.entry_ids != derived.entry_ids
                or current.builds != derived.builds
                or current.slices != derived.slices
                or current.members != derived.members
                or current.account != derived.account):
            raise ValueError(
                "a stored report disagrees with the report "
                "derived from its records")
    return current


def build_report(report: Any = None, source: Any = None,
                 **kwargs: Any) -> DogfoodReport:
    """Build one validated report, from a mapping or field words."""
    if isinstance(report, DogfoodReport) and not kwargs:
        return validate_report(report, source)
    if isinstance(report, dict) or report is None:
        merged: Dict[str, Any] = {}
        if isinstance(report, dict):
            merged.update(report)
        merged.update(kwargs)
        return validate_report(merged, source)
    return validate_report(report, source)


# ---------------------------------------------------------------------
# The coordinator's ledger: the whole book, derived.
# ---------------------------------------------------------------------


def _ledger_account(rows: Tuple[DogfoodReport, ...], total_builds: int,
                    total_slices: int) -> Tuple[str, ...]:
    return (
        f"The coordinator keeps this ledger: {len(rows)} "
        f"part row(s) across {len(rows)} part(s).",
        f"Total: {total_builds} build(s) across "
        f"{total_slices} slice(s).",
        "The standing dogfood: each part of this road is "
        "built by the crew it improves.",
    )


def _check_report_ref(value: Any) -> DogfoodReport:
    if isinstance(value, DogfoodReport):
        return value
    if isinstance(value, dict):
        return validate_report(value)
    raise ValueError(f"a report is needed, got {value!r}")


@dataclass(frozen=True)
class CoordinatorLedger:
    """The coordinator's ledger of one dogfood book.

    ``rows`` are the book's per-part reports, in the
    order the records first name each part; the
    totals are the rows' own sums (builds summed,
    slices counted distinct across rows, parts
    counted as rows) and ``account`` is read off the
    rows. A ledger whose totals are not its own
    rows' sums refuses at construction, and the
    keeper is always the coordinator.
    """

    keeper: str
    rows: Tuple[DogfoodReport, ...] = ()
    total_builds: int = 0
    total_slices: int = 0
    total_parts: int = 0
    account: Tuple[str, ...] = ()
    ledger_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.ledger_id is not None:
            object.__setattr__(
                self, "ledger_id", normalize_member_id(self.ledger_id))
        keeper = _clean_text(self.keeper, "a ledger's keeper")
        if keeper != COORDINATOR_KEEPER:
            raise ValueError(
                f"a dogfood ledger is kept by the coordinator, "
                f"got {keeper!r}")
        object.__setattr__(self, "keeper", keeper)
        if isinstance(self.rows, (str, bytes)) \
                or not isinstance(self.rows, (list, tuple)):
            raise ValueError(
                f"a ledger's rows must be a list of reports, "
                f"got {self.rows!r}")
        rows = tuple(_check_report_ref(r) for r in self.rows)
        if not rows:
            raise ValueError("a ledger holds at least one row")
        parts = [row.part for row in rows]
        if len(set(parts)) != len(parts):
            raise ValueError("a ledger names one part twice")
        object.__setattr__(self, "rows", rows)
        object.__setattr__(
            self, "total_builds",
            _check_count(self.total_builds, "a ledger's total builds"))
        object.__setattr__(
            self, "total_slices",
            _check_count(self.total_slices, "a ledger's total slices"))
        object.__setattr__(
            self, "total_parts",
            _check_count(self.total_parts, "a ledger's total parts"))
        builds = sum(row.builds for row in rows)
        slices = len({s for row in rows for s in row.slices})
        if (self.total_builds, self.total_slices, self.total_parts) != (
                builds, slices, len(rows)):
            raise ValueError(
                "a ledger's totals must be its own rows' sums")
        object.__setattr__(self, "account", _check_account(self.account))

    def row_for(self, part: Any) -> DogfoodReport:
        """The row one part names in this ledger."""
        wanted = _check_part(part)
        for row in self.rows:
            if row.part == wanted:
                return row
        raise KeyError(f"no row in the ledger: part {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "dogfood_ledger",
            "slice": DOGFOOD_SLICE,
            "ledger_id": self.ledger_id,
            "keeper": self.keeper,
            "rows": [row.to_record() for row in self.rows],
            "total_builds": self.total_builds,
            "total_slices": self.total_slices,
            "total_parts": self.total_parts,
            "account": list(self.account),
        }


def derive_ledger(source: Any) -> CoordinatorLedger:
    """Derive the coordinator's ledger from build records.

    The rows are the per-part reports in the order
    the records first name each part; the totals and
    account are read off the rows. An empty source
    refuses - a ledger of nothing is no ledger.
    """
    entries = _held_entries(source)
    if not entries:
        raise ValueError("a ledger needs at least one build record")
    parts: list = []
    for entry in entries:
        if entry.part not in parts:
            parts.append(entry.part)
    rows = tuple(derive_report(entries, part) for part in parts)
    total_builds = sum(row.builds for row in rows)
    total_slices = len({s for row in rows for s in row.slices})
    return CoordinatorLedger(
        keeper=COORDINATOR_KEEPER,
        rows=rows,
        total_builds=total_builds,
        total_slices=total_slices,
        total_parts=len(rows),
        account=_ledger_account(rows, total_builds, total_slices))


def validate_ledger(ledger: Any, source: Any = None) -> CoordinatorLedger:
    """Validate one coordinator's ledger into a CoordinatorLedger.

    Accepts a CoordinatorLedger or a mapping naming
    a ``keeper`` (or ``coordinator``), ``rows`` (or
    ``reports``), ``total_builds`` (or ``builds``),
    ``total_slices`` (or ``slices``), ``total_parts``
    (or ``parts``), an ``account`` (or
    ``statements``) and an optional ``ledger_id``
    (or ``id``). The keeper is always the
    coordinator; anyone else refusing. With *source*
    given, the ledger is judged against the ledger
    derived from those records: a stored ledger whose
    keeper, rows, totals or account disagree with
    the derived ledger refuses.
    """
    if isinstance(ledger, CoordinatorLedger):
        current = ledger
    elif isinstance(ledger, dict):
        unknown = set(ledger) - _LEDGER_KEYS
        if unknown:
            raise ValueError(
                "unknown ledger keys: %s" % ", ".join(sorted(unknown)))
        keeper = _pick_any(ledger, ("keeper", "coordinator"), "keepers")
        if keeper is None:
            raise ValueError("a ledger is missing its keeper")
        rows = _pick_any(ledger, ("rows", "reports"), "rows")
        if rows is None:
            raise ValueError("a ledger is missing its rows")
        total_builds = _pick_any(
            ledger, ("total_builds", "builds"), "total builds")
        if total_builds is None:
            raise ValueError("a ledger is missing its total builds")
        total_slices = _pick_any(
            ledger, ("total_slices", "slices"), "total slices")
        if total_slices is None:
            raise ValueError("a ledger is missing its total slices")
        total_parts = _pick_any(
            ledger, ("total_parts", "parts"), "total parts")
        if total_parts is None:
            raise ValueError("a ledger is missing its total parts")
        account = _pick_any(ledger, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a ledger names no account of its own")
        kwargs: Dict[str, Any] = {
            "keeper": keeper, "rows": rows,
            "total_builds": total_builds,
            "total_slices": total_slices,
            "total_parts": total_parts, "account": account}
        ledger_id = _pick_any(ledger, ("ledger_id", "id"), "ledger ids")
        if ledger_id is not None:
            kwargs["ledger_id"] = ledger_id
        current = CoordinatorLedger(**kwargs)
    else:
        raise ValueError(f"a ledger must be a mapping, got {ledger!r}")
    if source is not None:
        derived = derive_ledger(source)
        if (current.keeper != derived.keeper
                or current.rows != derived.rows
                or current.total_builds != derived.total_builds
                or current.total_slices != derived.total_slices
                or current.total_parts != derived.total_parts
                or current.account != derived.account):
            raise ValueError(
                "a stored ledger disagrees with the ledger "
                "derived from its records")
    return current


def build_ledger(ledger: Any = None, source: Any = None,
                 **kwargs: Any) -> CoordinatorLedger:
    """Build one validated ledger, from a mapping or field words."""
    if isinstance(ledger, CoordinatorLedger) and not kwargs:
        return validate_ledger(ledger, source)
    if isinstance(ledger, dict) or ledger is None:
        merged: Dict[str, Any] = {}
        if isinstance(ledger, dict):
            merged.update(ledger)
        merged.update(kwargs)
        return validate_ledger(merged, source)
    return validate_ledger(ledger, source)


# ---------------------------------------------------------------------
# The dogfood book: build records in held order, ledgers judged.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class DogfoodBook:
    """One dogfood book: a road's builds, held whole.

    ``entries`` are the build records, in held
    order; ``ledgers`` are coordinator's ledgers of
    the book - derivations, judged against the
    book's records by :func:`validate_book`;
    ``dogfood_note`` is the book's own note.
    """

    title: str = ""
    entries: Tuple[DogfoodEntry, ...] = ()
    ledgers: Tuple[CoordinatorLedger, ...] = ()
    dogfood_note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book's title"))
        if isinstance(self.entries, (str, bytes)) \
                or not isinstance(self.entries, (list, tuple)):
            raise ValueError(
                f"a book's entries must be a list of build records, "
                f"got {self.entries!r}")
        entries = tuple(_check_entry_ref(e) for e in self.entries)
        if not entries:
            raise ValueError("a dogfood book holds at least one build record")
        seen = set()
        for entry in entries:
            if entry.entry_id is not None:
                if entry.entry_id in seen:
                    raise ValueError(
                        f"a build record named {entry.entry_id!r} "
                        f"already exists")
                seen.add(entry.entry_id)
        object.__setattr__(self, "entries", entries)
        if isinstance(self.ledgers, (str, bytes)) \
                or not isinstance(self.ledgers, (list, tuple)):
            raise ValueError(
                f"a book's ledgers must be a list of ledgers, "
                f"got {self.ledgers!r}")
        ledgers = tuple(
            led if isinstance(led, CoordinatorLedger)
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
        if not isinstance(self.dogfood_note, str):
            raise ValueError("a book's note must be text")
        object.__setattr__(self, "dogfood_note", self.dogfood_note.strip())

    def entry_for(self, entry_id: Any) -> DogfoodEntry:
        """The build record one id names in this book."""
        wanted = normalize_member_id(entry_id)
        for entry in self.entries:
            if entry.entry_id == wanted:
                return entry
        raise KeyError(f"no build record in the book: {wanted!r}")

    def entries_for(self, member: Any) -> Tuple[DogfoodEntry, ...]:
        """Every build record one member filed, in held order."""
        wanted = normalize_member_id(member)
        return tuple(e for e in self.entries if e.member == wanted)

    def entries_on(self, slice_id: Any) -> Tuple[DogfoodEntry, ...]:
        """Every build record one slice names, in held order."""
        wanted = normalize_slice_id(slice_id)
        return tuple(e for e in self.entries if e.slice_id == wanted)

    def entries_in(self, part: Any) -> Tuple[DogfoodEntry, ...]:
        """Every build record of one part, in held order."""
        wanted = _check_part(part)
        return tuple(e for e in self.entries if e.part == wanted)

    def ledger_for(self, ledger_id: Any) -> CoordinatorLedger:
        """The ledger one id names in this book."""
        wanted = normalize_member_id(ledger_id)
        for ledger in self.ledgers:
            if ledger.ledger_id == wanted:
                return ledger
        raise KeyError(f"no ledger in the book: {wanted!r}")

    def entry_ids(self) -> Tuple[str, ...]:
        """Every held entry id, in held order."""
        return tuple(e.entry_id for e in self.entries if e.entry_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "dogfood_book",
            "slice": DOGFOOD_SLICE,
            "title": self.title,
            "entry_ids": list(self.entry_ids()),
            "entry_count": len(self.entries),
            "ledger_count": len(self.ledgers),
        }


def validate_book(data: Any, *, require_example: bool = False) -> DogfoodBook:
    """Validate one dogfood mapping into a DogfoodBook.

    The mapping names a ``schema`` (the dogfood
    schema word), a ``guide`` mapping (its
    ``title``), an ``entries`` list and an optional
    ``ledgers`` list. Every record stands on its own
    validation, then the whole is judged: entry ids
    unique, and every ledger judged against the
    book's own build records. With
    ``require_example`` the shipped example is held
    to its pinned shape: the pinned title, entries
    and ledger, the ledger's pinned rows, totals and
    account word-for-word, and the first report's
    pinned account. Problems raise
    :class:`ValidationError` or ``ValueError``.
    """
    if isinstance(data, DogfoodBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a dogfood book must be a mapping, got {data!r}")
    unknown = set(data) - _DOGFOOD_KEYS
    if unknown:
        raise ValidationError(
            "unknown dogfood keys: %s" % ", ".join(sorted(unknown)))
    if data.get("schema") != DOGFOOD_SCHEMA:
        raise ValidationError(
            f"a dogfood book must carry schema "
            f"{DOGFOOD_SCHEMA!r}, got {data.get('schema')!r}")
    if "entries" not in data:
        raise ValidationError("a dogfood book is missing its entries")
    if not isinstance(data["entries"], (list, tuple)):
        raise ValidationError("a dogfood book's entries must be a list")
    if data.get("ledgers") is not None \
            and not isinstance(data["ledgers"], (list, tuple)):
        raise ValidationError("a dogfood book's ledgers must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a dogfood book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a dogfood book is missing its title")
        note = data.get("dogfood_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a dogfood book's note must be text")
        book = DogfoodBook(
            title=title, entries=tuple(data["entries"]),
            ledgers=tuple(data.get("ledgers") or ()),
            dogfood_note=note)
        for ledger in book.ledgers:
            validate_ledger(ledger, book.entries)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if require_example:
        if book.title != _EXAMPLE_TITLE:
            raise ValidationError(
                "the shipped example dogfood book's title is "
                "not the pinned title")
        if book.entry_ids() != _EXAMPLE_ENTRY_IDS:
            raise ValidationError(
                "the shipped example's build records are not "
                "the pinned records")
        ledger = book.ledger_for(_EXAMPLE_LEDGER_ID)
        if ledger.keeper != COORDINATOR_KEEPER:
            raise ValidationError(
                "the shipped example ledger is not kept "
                "by the coordinator")
        if tuple(r.part for r in ledger.rows) != _EXAMPLE_LEDGER_ROWS:
            raise ValidationError(
                "the shipped example ledger does not name "
                "its pinned rows")
        totals = (
            ledger.total_builds, ledger.total_slices,
            ledger.total_parts)
        if totals != _EXAMPLE_LEDGER_TOTALS:
            raise ValidationError(
                "the shipped example ledger does not carry "
                "its pinned totals")
        if ledger.account != _EXAMPLE_LEDGER_ACCOUNT:
            raise ValidationError(
                "the shipped example ledger does not carry "
                "its pinned account word-for-word")
        first = derive_report(book.entries, 5)
        if first.account != _EXAMPLE_FIRST_REPORT_ACCOUNT:
            raise ValidationError(
                "the shipped example's first report does not "
                "carry its pinned account word-for-word")
    return book


def build_book(book: Any = None, **kwargs: Any) -> DogfoodBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, DogfoodBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "entries" in book or "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return DogfoodBook(**merged)
    if book is None:
        return DogfoodBook(**kwargs)
    raise ValueError(f"a dogfood book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> DogfoodBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_dogfood(
        data: Optional[Dict[str, Any]] = None) -> DogfoodBook:
    """Load and validate the shipped example book (or *data*).

    The shipped file is held to the example check:
    the pinned title, build records and ledger - the
    M-140 boundary book of builds and the
    coordinator's ledger of it - so the shipped book
    covers the boundary this slice exists to hold.
    """
    raw = data if data is not None else load_resource(DOGFOOD_RESOURCE)
    return _book_from(raw, require_example=True)


def load_dogfood_file(path: Any) -> DogfoodBook:
    """Load and validate a dogfood book from a file at *path*.

    Any file in the dogfood shape, anywhere on disk,
    validated whole - a malformed file raises
    :class:`ValidationError` naming the problem, and
    a missing file raises ``FileNotFoundError``. The
    example check is not held: a real dogfood book
    stands on its own records.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held record by record, in held order.
# ---------------------------------------------------------------------


class DogfoodRegistry:
    """One session's dogfood book, held record by record.

    The registry holds build records, never reports
    or ledgers: both are derivations, read off held
    records at call time, so nothing here can hold
    a total stale.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._entries: Dict[str, DogfoodEntry] = {}
        self._order: list = []
        self._next_entry = 1
        if book is not None:
            self.register_book(book)

    def _fresh_entry_id(self, held_ids: Any) -> str:
        while f"dogfood-{self._next_entry}" in held_ids:
            self._next_entry += 1
        fresh = f"dogfood-{self._next_entry}"
        self._next_entry += 1
        return fresh

    def register_entry(self, entry: Any) -> DogfoodEntry:
        """Register one build record into the held book.

        A record with no id is given a deterministic
        ``dogfood-N`` id. A record id already standing
        here refuses.
        """
        validated = build_entry(entry)
        held_ids = set(self._entries)
        if validated.entry_id is not None \
                and validated.entry_id in held_ids:
            raise ValueError(
                f"a build record named {validated.entry_id!r} "
                f"already exists")
        if validated.entry_id is None:
            validated = replace(
                validated, entry_id=self._fresh_entry_id(held_ids))
        self._entries[validated.entry_id] = validated
        self._order.append(validated.entry_id)
        return validated

    def register_book(self, book: Any) -> DogfoodBook:
        """Register every build record of one book, in order.

        The first book held sets the title; a later
        book under a different title refuses, as does
        a book naming a held record id. The book's
        ledgers are derivations, not holdings, and
        are not held.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a dogfood book "
                "under a different title")
        for entry in validated.entries:
            if entry.entry_id in self._entries:
                raise ValueError(
                    f"a build record named {entry.entry_id!r} "
                    f"already exists")
        self._title = validated.title
        for entry in validated.entries:
            self.register_entry(entry)
        return self.book()

    def get_entry(self, entry_id: Any) -> DogfoodEntry:
        """The build record one id names among the held records."""
        wanted = normalize_member_id(entry_id)
        if wanted not in self._entries:
            raise KeyError(f"unknown build record: {wanted!r}")
        return self._entries[wanted]

    def list_entries(self) -> Tuple[DogfoodEntry, ...]:
        """Every held build record, in the order they were held."""
        return tuple(self._entries[e] for e in self._order)

    def book(self) -> DogfoodBook:
        """The held build records as one validated book."""
        if self._title is None:
            raise ValueError("no dogfood book is held yet")
        return DogfoodBook(
            title=self._title, entries=self.list_entries())

    def report_for(self, part: Any) -> DogfoodReport:
        """Derive one part's report, at call time.

        The report is derived from the held records of
        that part, read at call time - the registry
        holds records, and this report is derived
        from them.
        """
        return derive_report(self.list_entries(), part)

    def ledger(self) -> CoordinatorLedger:
        """Derive the coordinator's ledger of the held book.

        The rows and account are the held records' own
        sums, read at call time.
        """
        return derive_ledger(self.list_entries())


# ---------------------------------------------------------------------
# Dogfood news, shaped as session records.
# ---------------------------------------------------------------------


def entry_record(entry: Any) -> Dict[str, Any]:
    """The session-news record of one build record."""
    current = entry if isinstance(entry, DogfoodEntry) \
        else build_entry(entry)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.member} built {current.slice_id} "
        f"(Part {current.part}): {current.title}.")
    return record


def report_record(report: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one per-part report.

    With *source* given, the report is first judged
    against the records it belongs to.
    """
    current = validate_report(report, source)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Part {current.part} was built by its own crew "
        f"across {current.builds} build(s).")
    return record


def ledger_record(ledger: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of the coordinator's ledger.

    With *source* given, the ledger is first judged
    against the records it belongs to.
    """
    current = validate_ledger(ledger, source)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"The coordinator's ledger: {current.total_builds} "
        f"build(s) across {len(current.rows)} row(s).")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one dogfood book."""
    current = book if isinstance(book, DogfoodBook) else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Dogfood book {current.title}: "
        f"{record['entry_count']} build record(s), "
        f"{record['ledger_count']} ledger(s).")
    return record


def plain_words(entry: Any) -> str:
    """One build record, in one plain sentence."""
    current = entry if isinstance(entry, DogfoodEntry) \
        else build_entry(entry)
    return (
        f"{current.member} built {current.slice_id} "
        f"(Part {current.part}, {current.part_title}): "
        f"{current.title}.")


def _book_parts(book: DogfoodBook) -> Tuple[int, ...]:
    parts: list = []
    for entry in book.entries:
        if entry.part not in parts:
            parts.append(entry.part)
    return tuple(parts)


def report_plain_words(source: Any) -> str:
    """Reports in plain words: every report, in full.

    Accepts a DogfoodReport or a DogfoodBook. Each
    report is told whole - its part and its account.
    """
    if isinstance(source, DogfoodReport):
        reports = (validate_report(source),)
        title = None
    elif isinstance(source, DogfoodBook):
        reports = tuple(
            derive_report(source.entries, part)
            for part in _book_parts(source))
        title = source.title
    else:
        raise ValueError(f"a dogfood source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    for report in reports:
        lines.append(
            f"Part {report.part} - {report.builds} build(s)")
        lines.extend(report.account)
    return "\n".join(lines)


def ledger_plain_words(source: Any) -> str:
    """The coordinator's ledger in plain words, in full.

    Accepts a CoordinatorLedger or a DogfoodBook.
    The ledger is told whole - its keeper, its rows
    and its account.
    """
    if isinstance(source, CoordinatorLedger):
        ledger = validate_ledger(source)
        title = None
    elif isinstance(source, DogfoodBook):
        ledger = derive_ledger(source.entries)
        title = source.title
    else:
        raise ValueError(f"a dogfood source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append(f"Ledger kept by {ledger.keeper}:")
    for row in ledger.rows:
        lines.append(
            f"Part {row.part} - {row.builds} build(s) "
            f"across {len(row.slices)} slice(s)")
    lines.extend(ledger.account)
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Screens: the formatters and the shared /dogfood grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> DogfoodBook:
    if source is None:
        return load_dogfood()
    if isinstance(source, DogfoodRegistry):
        return source.book()
    if isinstance(source, DogfoodBook):
        return source
    raise ValueError(f"a dogfood book is needed, got {source!r}")


def format_entry(entry: Any) -> str:
    """One build record as a screen line."""
    current = entry if isinstance(entry, DogfoodEntry) \
        else build_entry(entry)
    return (
        f"{current.entry_id or '-'}: {current.member} "
        f"built {current.slice_id} (Part {current.part}) - "
        f"{current.title}")


def format_entries(source: Any = None, member: Any = None) -> str:
    """Build records of one book, in held order.

    With *member* given, only that member's records
    are shown.
    """
    book = _source_book(source)
    entries = book.entries if member is None else book.entries_for(member)
    lines = [format_entry(entry) for entry in entries]
    if not lines:
        lines.append("No build records are held.")
    return "\n".join(lines)


def format_report(source: Any = None) -> str:
    """Reports as screen blocks: part over derived account.

    Accepts a DogfoodReport or a DogfoodBook; a book
    shows every report it derives, in book order.
    """
    if isinstance(source, DogfoodReport):
        reports = (validate_report(source),)
        lines: list = []
    else:
        book = _source_book(source)
        reports = tuple(
            derive_report(book.entries, part)
            for part in _book_parts(book))
        lines = [f"Reports in {book.title}:"]
    for report in reports:
        lines.append(
            f"Part {report.part} ({_part_title(report.part)}) - "
            f"{report.builds} build(s) across "
            f"{len(report.slices)} slice(s)")
        lines.extend(report.account)
    if isinstance(source, DogfoodReport):
        return "\n".join(lines)
    if len(lines) == 1:
        lines.append("Nothing here.")
    return "\n".join(lines)


def format_ledger(source: Any = None) -> str:
    """The coordinator's ledger as a screen block.

    Accepts a CoordinatorLedger or a DogfoodBook; a
    book shows the ledger it derives, its rows over
    its derived account.
    """
    if isinstance(source, CoordinatorLedger):
        ledger = validate_ledger(source)
        lines: list = []
    else:
        book = _source_book(source)
        ledger = derive_ledger(book.entries)
        lines = [f"Ledger in {book.title}:"]
    lines.append(f"Kept by {ledger.keeper}:")
    for row in ledger.rows:
        lines.append(
            f"Part {row.part} - {row.builds} build(s) "
            f"across {len(row.slices)} slice(s)")
    lines.extend(ledger.account)
    return "\n".join(lines)


def format_dogfood_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /dogfood.

    With nothing named, the shipped example dogfood
    book is shown - the example this slice ships -
    so the screen is never empty.
    """
    book = _source_book(source)
    lines = ["The Mythic Coder building itself (M-141) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_entries(book))
    lines.append("")
    lines.append(format_report(book))
    lines.append("")
    lines.append(format_ledger(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_dogfood_args(args: Any) -> Tuple[str, Any]:
    """Parse the /dogfood grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    dogfood book; ``entry <entry-id>`` shows one
    build record; ``member <member-id>`` shows one
    member's records; ``slice <slice-id>`` shows one
    slice's records; ``part <part-number>`` shows
    one part's report; ``ledger`` shows the
    coordinator's ledger. Anything else is a usage
    error naming the grammar. Returns
    ``(action, value-or-None)``; a part action's
    value is the part number itself.
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
    if head in ("entry", "member") and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "slice" and len(words) == 2:
        try:
            return (head, normalize_slice_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "part" and len(words) == 2:
        try:
            return (head, _check_part(int(words[1])))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
