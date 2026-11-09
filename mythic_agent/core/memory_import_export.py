"""Memory import/export (All-Features roadmap slice M-164).

Part VII continues. The roadmap's words:
``a project's memory map + ledger as portable
files (they ride with the repo if the user
wishes).``

What already ships, and what this slice adds:

* A project's memory already ships as data on
  shipped roads: the project memory map
  (``core/project_memory_map.py``, M-150) holds
  one project's living facts in its closed
  sections - architecture, decisions, gotchas,
  where things live - and the self-improving
  ledger (``core/self_improving_ledger.py``,
  M-155) holds the candidate memories significant
  work taught, with their promotion standings.
  What neither layer holds is the portable file
  itself: one record that carries a project's map
  and ledger together, so the memory can ride with
  the repo if the user wishes, and be held again on
  the other side.
* This slice is that file, as a pure layer: a
  memory package is one project's memory map +
  ledger exported as one portable file record,
  validated as data WITH ITS PROVENANCE WHOLE -
  the project it packs, the session it was
  exported from and the day, what rides in it (the
  map entry ids and the map sections they stand
  in, the ledger candidate ids and the promotion
  states they stand in), who exported it, and
  where it was read from - composed BY IMPORT from
  the shipped holdings it packs (a project memory
  map book, a self-improving ledger book), each
  judged by its own layer's validation. The
  shipped data file
  (``mythic_agent/data/memory_import_export.yaml``)
  holds one example book in exactly the shape a
  real book file takes, a loader reads a book file
  anywhere on disk, the memory panel is DERIVED
  from the whole book (every package carried
  whole, in a settled order), a portability
  VERDICT is derived for the whole book, packages
  are shaped as session news, and a small
  in-memory registry model holds packages one by
  one. The agent layer owns holding a book for a
  session, exporting the session's map + ledger
  onto a package, and holding a judged package on
  import.

Honesty rules, enforced here and pinned by tests:

* **Ids only across the seam.** A package carries
  the map's and the ledger's pieces by id alone -
  the entries' and candidates' own words never
  cross into the package; the package names what
  rides, with its sections and standings, and the
  pieces themselves stay in their own layers.
* **Judged whole before anything is held.** An
  import is judged whole - provenance, contents
  and counts together, and against the holdings it
  claims to pack when they are named - before any
  package is held: a malformed or foreign package
  refuses by name, and nothing is partially held.
* **A piece rides once.** A map entry or a ledger
  candidate named by one package never rides in
  another package of the same book, and one
  session's export of one project stands once in a
  book.
* **Composed, never duplicated.** A package that
  packs shipped holdings is those holdings read
  onto this layer by import and judged by their
  own layers' validation, by id, section and
  standing alone.
* **Data only.** This layer holds packages as
  data: it reads no file itself beyond its own
  book files, sends nothing, posts nothing,
  schedules nothing, calls no model and persists
  nothing. Holding an imported package writes no
  live memory - the map and the ledger of any live
  session stand exactly as they stood.
"""

from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .project_memory_map import MAP_SECTIONS
from .project_memory_map import MemoryMapEntry
from .project_memory_map import validate_entry as _validate_map_entry
from .project_memory_map import normalize_section as _normalize_section
from .self_improving_ledger import PROMOTION_STATES
from .self_improving_ledger import CandidateMemory, PromotionDecision
from .self_improving_ledger import validate_candidate as _validate_candidate
from .self_improving_ledger import validate_decision as _validate_decision
from .self_improving_ledger import normalize_promotion_state as _normalize_state
from .validation import ValidationError

__all__ = [
    "MEMORY_IMPORT_EXPORT_RESOURCE",
    "MEMORY_IMPORT_EXPORT_SCHEMA",
    "MEMORY_IMPORT_EXPORT_SLICE",
    "PLAIN_EXPLANATION",
    "RIDE_KINDS",
    "USAGE",
    "MemoryExportBook",
    "MemoryPackage",
    "MemoryPackageRegistry",
    "PackagePanel",
    "PackagePanelRow",
    "PortabilityVerdict",
    "RideCount",
    "book_record",
    "build_book",
    "build_package",
    "build_panel",
    "build_row",
    "build_verdict",
    "derive_panel",
    "derive_verdict",
    "format_memory_import_export_screen",
    "format_package",
    "format_packages",
    "format_panel",
    "format_verdict",
    "inspect_package_source",
    "load_memory_import_export",
    "load_memory_import_export_file",
    "normalize_ride_kind",
    "package_from_ledger",
    "package_from_memory_books",
    "package_from_memory_map",
    "package_record",
    "package_refs",
    "panel_plain_words",
    "panel_record",
    "parse_memoryxport_args",
    "plain_words",
    "total_candidates",
    "total_map_entries",
    "total_pieces",
    "validate_book",
    "validate_package",
    "validate_panel",
    "validate_row",
    "validate_verdict",
    "verdict_plain_words",
    "verdict_record",
]

MEMORY_IMPORT_EXPORT_SLICE = "M-164"

MEMORY_IMPORT_EXPORT_RESOURCE = "memory_import_export.yaml"

MEMORY_IMPORT_EXPORT_SCHEMA = "mythic.memory_import_export/1"

#: The two kinds of piece one package may carry:
#: the project's memory-map entries and its
#: self-improving ledger's candidates.
RIDE_KINDS = ("map", "ledger")

_RIDE_KIND_ALIASES = {
    "map": "map",
    "memory-map": "map",
    "memory_map": "map",
    "ledger": "ledger",
    "self-improving-ledger": "ledger",
    "self_improving_ledger": "ledger",
}

_PACKAGE_KEYS = frozenset({
    "package_id", "id", "title", "name", "subject",
    "project", "source_session", "session",
    "map_entry_ids", "map_entries", "entries",
    "candidate_ids", "candidates",
    "map_sections", "sections",
    "ledger_states", "states",
    "exported_by", "exporter", "by", "who",
    "exported_on", "day", "date", "source",
})

_ROW_KEYS = frozenset({
    "package_id", "id", "title", "project", "source_session",
    "map_count", "map", "candidate_count", "candidates",
    "piece_count", "pieces", "exported_by", "exported_on",
})

_RIDE_COUNT_KEYS = frozenset({"kind", "items", "count"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "rows", "packages",
    "total_packages", "total",
    "total_map_entries", "map_entries",
    "total_candidates", "candidates",
    "total_pieces", "pieces",
    "ride_counts", "rides", "account", "statements",
})

_VERDICT_KEYS = frozenset({
    "total_packages", "total",
    "total_map_entries", "map_entries",
    "total_candidates", "candidates",
    "total_pieces", "pieces",
    "total_complete", "complete",
    "total_map_only", "map_only",
    "total_ledger_only", "ledger_only",
    "distinct_projects", "projects", "verdict",
})

_BOOK_KEYS = frozenset({"title", "name"})

_MEMORY_EXPORT_BOOK_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "packages", "records", "panels",
})

_EXAMPLE_TITLE = "Memory import/export at the M-163 slice boundary"

_EXAMPLE_PACKAGE_IDS = (
    "package-coder-memory", "package-samtal-memory")

_EXAMPLE_FIRST_PACKAGE_ID = "package-coder-memory"

_EXAMPLE_FIRST_PACKAGE_TITLE = (
    "the mythic-agent-coder memory, packed to ride with the repo")

_EXAMPLE_PANEL_ID = "panel-m163-boundary"

_EXAMPLE_PANEL_ROW_IDS = (
    "package-coder-memory", "package-samtal-memory")

_EXAMPLE_PANEL_ACCOUNT = (
    "The memory panel holds 2 packages: "
    "14 pieces in all, 11 map entries and "
    "3 ledger candidates: ledger 3, map 11.",
    "Packages stand by project, then day, then "
    "title, then package id, so two panels of "
    "one book diff cleanly, line by line.",
    "Every piece a package carries is carried "
    "from the project's own memory map and "
    "ledger, and a package whose contents "
    "disagree with those holdings is refused - "
    "a package carries only what its sources hold.",
    "The panel is read off the book at call "
    "time - it is derived, never stored loose.",
)

PLAIN_EXPLANATION = (
    "Memory import/export: a project's memory "
    "map + ledger as portable files - they ride "
    "with the repo if the user wishes. A memory "
    "package is one project's map and ledger "
    "exported as one portable file record, carried "
    "with its provenance whole: the project it "
    "packs, the session it was exported from and "
    "the day, what sections and standings ride in "
    "it (the map entry ids and their sections, "
    "the ledger candidate ids and their promotion "
    "states), who exported it, and where it was "
    "read from. An import is judged whole before "
    "anything is held, and a package whose "
    "contents disagree with the holdings it packs "
    "is refused. The memory panel is derived from "
    "the book at call time: every package standing "
    "whole, by project, then day, then title, then "
    "package id, and the portability verdict is "
    "derived for the whole book. This layer holds "
    "packages as data only: it sends nothing, "
    "posts nothing, schedules nothing, calls no "
    "model, persists nothing and writes no live "
    "memory."
)

USAGE = (
    "Usage: /memoryxport, /memoryxport show, "
    "/memoryxport package <package-id>, "
    "/memoryxport project <project>, "
    "/memoryxport panel, /memoryxport verdict"
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


def _check_word(value: Any, what: str) -> str:
    try:
        return normalize_member_id(value)
    except ValueError:
        raise ValueError(
            f"{what} must be one plain word, "
            f"got {value!r}") from None


def _check_day(value: Any) -> str:
    text = _clean_text(value, "a record's exported-on day")
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        raise ValueError(
            f"a record's exported-on day must be an ISO "
            f"date (YYYY-MM-DD), got {text!r}") from None
    if parsed.isoformat() != text:
        raise ValueError(
            f"a record's exported-on day must be an ISO "
            f"date (YYYY-MM-DD), got {text!r}")
    return text


def normalize_ride_kind(value: Any) -> str:
    """The canonical ride kind a word names.

    A ride kind is one of :data:`RIDE_KINDS` -
    ``map`` (a project memory-map entry) or
    ``ledger`` (a self-improving ledger candidate) -
    read case-insensitively, with ``memory-map``
    read onto ``map`` and ``self-improving-ledger``
    onto ``ledger``. Anything else raises, plainly
    naming the two.
    """
    if isinstance(value, str):
        wanted = _RIDE_KIND_ALIASES.get(value.strip().lower())
        if wanted is not None:
            return wanted
    raise ValueError(
        "a ride kind must be one of %s, got %r"
        % ("/".join(RIDE_KINDS), value))


# ---------------------------------------------------------------------
# The memory package: one project's map + ledger, packed whole.
# ---------------------------------------------------------------------


def _check_ids(value: Any, what: str) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes)) \
            or not isinstance(value, (list, tuple)):
        raise ValueError(
            f"a package's {what} must be a list "
            f"of ids, got {value!r}")
    ids = tuple(_check_word(item, f"a {what} id") for item in value)
    if len(ids) > 512:
        raise ValueError(
            f"a package names at most 512 {what}, "
            f"got {len(ids)}")
    if len(set(ids)) != len(ids):
        raise ValueError(f"a package names one {what} id twice")
    return ids


def _check_sections(value: Any) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes)) \
            or not isinstance(value, (list, tuple)):
        raise ValueError(
            f"a package's map sections must be a list "
            f"of sections, got {value!r}")
    sections = tuple(_normalize_section(item) for item in value)
    if len(set(sections)) != len(sections):
        raise ValueError("a package names one map section twice")
    return tuple(sorted(sections, key=MAP_SECTIONS.index))


def _check_states(value: Any) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes)) \
            or not isinstance(value, (list, tuple)):
        raise ValueError(
            f"a package's ledger states must be a list "
            f"of states, got {value!r}")
    states = tuple(_normalize_state(item) for item in value)
    if len(set(states)) != len(states):
        raise ValueError("a package names one ledger state twice")
    return tuple(sorted(states, key=PROMOTION_STATES.index))


@dataclass(frozen=True)
class MemoryPackage:
    """One project's memory map + ledger, packed as one file record.

    ``title`` names the package in plain words;
    ``project`` is the project it packs;
    ``source_session`` names the session it was
    exported from; ``map_entry_ids`` are the map
    entries riding in it, by id alone, and
    ``map_sections`` the closed sections those
    entries stand in, in map order;
    ``candidate_ids`` are the ledger candidates
    riding in it, by id alone, and ``ledger_states``
    the promotion states those candidates stand in.
    The provenance stands whole beside the package:
    ``exported_by`` names who exported it,
    ``exported_on`` is the day, and ``source`` names
    where it was read from. A package rides at least
    one piece, and no id rides twice in one package
    - a piece rides once.
    """

    title: str
    project: str
    source_session: str
    map_entry_ids: Tuple[str, ...]
    candidate_ids: Tuple[str, ...]
    map_sections: Tuple[str, ...]
    ledger_states: Tuple[str, ...]
    exported_by: str
    exported_on: str
    source: str
    package_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.package_id is not None:
            object.__setattr__(
                self, "package_id", normalize_member_id(self.package_id))
        object.__setattr__(
            self, "title", _check_title(self.title, "a package's title"))
        object.__setattr__(
            self, "project",
            _check_title(self.project, "a package's project"))
        object.__setattr__(
            self, "source_session",
            _check_word(self.source_session, "a package's source session"))
        map_ids = _check_ids(self.map_entry_ids, "map entries")
        object.__setattr__(self, "map_entry_ids", map_ids)
        candidate_ids = _check_ids(self.candidate_ids, "ledger candidates")
        object.__setattr__(self, "candidate_ids", candidate_ids)
        shared = set(map_ids) & set(candidate_ids)
        if shared:
            raise ValueError(
                f"a package names one piece in both its map "
                f"and its ledger: {sorted(shared)[0]!r} - "
                f"a piece rides once")
        if not map_ids and not candidate_ids:
            raise ValueError(
                "a package carries at least one piece - a "
                "package that packs nothing exports nothing")
        sections = _check_sections(self.map_sections)
        object.__setattr__(self, "map_sections", sections)
        if bool(map_ids) != bool(sections):
            raise ValueError(
                "a package's map sections must name the "
                "sections its map entries stand in - sections "
                "ride exactly when entries ride")
        states = _check_states(self.ledger_states)
        object.__setattr__(self, "ledger_states", states)
        if bool(candidate_ids) != bool(states):
            raise ValueError(
                "a package's ledger states must name the "
                "states its candidates stand in - states "
                "ride exactly when candidates ride")
        object.__setattr__(
            self, "exported_by",
            _check_title(self.exported_by, "a package's exporter"))
        object.__setattr__(
            self, "exported_on", _check_day(self.exported_on))
        object.__setattr__(
            self, "source",
            _check_title(self.source, "a package's source"))

    @property
    def map_count(self) -> int:
        """How many map entries this package carries."""
        return len(self.map_entry_ids)

    @property
    def candidate_count(self) -> int:
        """How many ledger candidates this package carries."""
        return len(self.candidate_ids)

    @property
    def piece_count(self) -> int:
        """How many pieces this package carries, in all."""
        return self.map_count + self.candidate_count

    @property
    def rides_both(self) -> bool:
        """Whether this package rides map and ledger both."""
        return bool(self.map_entry_ids) and bool(self.candidate_ids)

    def counts(self) -> Dict[str, int]:
        """Each ride kind's size, read off the ids held."""
        return {"map": self.map_count, "ledger": self.candidate_count}

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "memory_import_export_package",
            "slice": MEMORY_IMPORT_EXPORT_SLICE,
            "package_id": self.package_id,
            "title": self.title,
            "project": self.project,
            "source_session": self.source_session,
            "map_entry_ids": list(self.map_entry_ids),
            "candidate_ids": list(self.candidate_ids),
            "map_sections": list(self.map_sections),
            "ledger_states": list(self.ledger_states),
            "map_count": self.map_count,
            "candidate_count": self.candidate_count,
            "piece_count": self.piece_count,
            "exported_by": self.exported_by,
            "exported_on": self.exported_on,
            "source": self.source,
        }


def _check_package_ref(value: Any) -> "MemoryPackage":
    if isinstance(value, MemoryPackage):
        return value
    if isinstance(value, dict):
        return validate_package(value)
    raise ValueError(f"a memory package is needed, got {value!r}")


def _map_entries(source: Any) -> Tuple[MemoryMapEntry, ...]:
    """The shipped map entries one source holds, judged by M-150."""
    from .project_memory_map import MemoryMapBook, MemoryMapRegistry
    if isinstance(source, MemoryMapBook):
        return source.entries
    if isinstance(source, MemoryMapRegistry):
        return source.list_entries()
    if isinstance(source, (list, tuple)):
        return tuple(_validate_map_entry(e) for e in source)
    if isinstance(source, (MemoryMapEntry, dict)):
        return (_validate_map_entry(source),)
    raise ValueError(f"memory map entries are needed, got {source!r}")


def _map_expectation(source: Any) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    """The ids and sections one map source yields, by import."""
    entries = _map_entries(source)
    ids = []
    for entry in entries:
        if entry.entry_id is None:
            raise ValueError(
                "a memory map entry with no id cannot ride "
                "in a package - a package carries pieces by id")
        ids.append(entry.entry_id)
    sections = tuple(sorted(
        {entry.section for entry in entries}, key=MAP_SECTIONS.index))
    return tuple(ids), sections


def _ledger_candidates(source: Any) -> Tuple[CandidateMemory, ...]:
    """The shipped ledger candidates one source holds, judged by M-155."""
    from .self_improving_ledger import (
        SelfImprovingBook, SelfImprovingRegistry)
    if isinstance(source, SelfImprovingBook):
        return source.candidates
    if isinstance(source, SelfImprovingRegistry):
        return source.list_candidates()
    if isinstance(source, (list, tuple)):
        return tuple(_validate_candidate(c) for c in source)
    if isinstance(source, (CandidateMemory, dict)):
        return (_validate_candidate(source),)
    raise ValueError(f"ledger candidates are needed, got {source!r}")


def _ledger_decisions(source: Any) -> Tuple[PromotionDecision, ...]:
    """The shipped ledger decisions one source holds, judged by M-155."""
    from .self_improving_ledger import (
        SelfImprovingBook, SelfImprovingRegistry)
    if isinstance(source, SelfImprovingBook):
        return source.decisions
    if isinstance(source, SelfImprovingRegistry):
        return source.list_decisions()
    if isinstance(source, (list, tuple)):
        return tuple(_validate_decision(d) for d in source)
    if isinstance(source, PromotionDecision):
        return (source,)
    return ()


def _ledger_expectation(
        source: Any) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    """The ids and states one ledger source yields, by import."""
    candidates = _ledger_candidates(source)
    ids = []
    for candidate in candidates:
        if candidate.candidate_id is None:
            raise ValueError(
                "a ledger candidate with no id cannot ride "
                "in a package - a package carries pieces by id")
        ids.append(candidate.candidate_id)
    by_candidate = {d.candidate_id: d for d in _ledger_decisions(source)}
    states = set()
    for candidate in candidates:
        decision = by_candidate.get(candidate.candidate_id)
        states.add(decision.state if decision is not None else "candidate")
    ordered = tuple(sorted(states, key=PROMOTION_STATES.index))
    return tuple(ids), ordered


def validate_package(package: Any, map_source: Any = None,
                     ledger_source: Any = None) -> MemoryPackage:
    """Validate one package into a MemoryPackage.

    Accepts a package or a mapping naming a ``title``
    (or ``name`` / ``subject``), a ``project``, a
    ``source_session`` (or ``session``),
    ``map_entry_ids`` (or ``map_entries`` /
    ``entries``), ``candidate_ids`` (or
    ``candidates``), ``map_sections`` (or
    ``sections``), ``ledger_states`` (or ``states``),
    an ``exported_by`` (or ``exporter`` / ``by`` /
    ``who``), an ``exported_on`` (or ``day`` /
    ``date``), a ``source`` and an optional
    ``package_id`` (or ``id``). Naming two spellings
    of one field with different values refuses, and
    unknown keys refuse. With *map_source* and/or
    *ledger_source* given (a shipped memory-map or
    ledger holding, each judged by its own layer),
    the package is also judged against the holdings
    it packs: any disagreement in ids, sections or
    states refuses, because a package carries only
    what its sources hold - an import is judged
    whole before anything is held.
    """
    if isinstance(package, MemoryPackage):
        current = package
    elif isinstance(package, dict):
        unknown = set(package) - _PACKAGE_KEYS
        if unknown:
            raise ValueError(
                "unknown package keys: %s"
                % ", ".join(sorted(unknown)))

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            value = _pick_any(package, spellings, what)
            if value is None:
                raise ValueError(f"a package is missing its {what}")
            return value

        kwargs: Dict[str, Any] = {
            "title": _needed(("title", "name", "subject"), "title"),
            "project": _needed(("project",), "project"),
            "source_session": _needed(
                ("source_session", "session"), "source session"),
            "map_entry_ids": _needed(
                ("map_entry_ids", "map_entries", "entries"),
                "map entries"),
            "candidate_ids": _needed(
                ("candidate_ids", "candidates"), "ledger candidates"),
            "map_sections": _needed(
                ("map_sections", "sections"), "map sections"),
            "ledger_states": _needed(
                ("ledger_states", "states"), "ledger states"),
            "exported_by": _needed(
                ("exported_by", "exporter", "by", "who"), "exporter"),
            "exported_on": _needed(
                ("exported_on", "day", "date"), "exported-on day"),
            "source": _needed(("source",), "source"),
        }
        named_id = _pick_any(package, ("package_id", "id"), "package ids")
        if named_id is not None:
            kwargs["package_id"] = named_id
        current = MemoryPackage(**kwargs)
    else:
        raise ValueError(
            f"a package must be a mapping, got {package!r}")
    if map_source is not None:
        ids, sections = _map_expectation(map_source)
        if current.map_entry_ids != ids or current.map_sections != sections:
            raise ValueError(
                "a package whose map contents disagree with "
                "the memory map it packs is refused - a package "
                "carries only what its sources hold")
    if ledger_source is not None:
        ids, states = _ledger_expectation(ledger_source)
        if current.candidate_ids != ids or current.ledger_states != states:
            raise ValueError(
                "a package whose ledger contents disagree with "
                "the ledger it packs is refused - a package "
                "carries only what its sources hold")
    return current


def build_package(package: Any = None, **kwargs: Any) -> MemoryPackage:
    """Build one validated package, from a mapping or field words."""
    if isinstance(package, MemoryPackage) and not kwargs:
        return package
    if isinstance(package, dict) or package is None:
        merged: Dict[str, Any] = {}
        if isinstance(package, dict):
            merged.update(package)
        merged.update(kwargs)
        return validate_package(merged)
    raise ValueError(f"a package must be a mapping, got {package!r}")


def _package_for(*, title: Any, project: Any, source_session: Any,
                 map_entry_ids: Any, candidate_ids: Any,
                 map_sections: Any, ledger_states: Any,
                 exported_by: Any, exported_on: Any,
                 source: Any) -> MemoryPackage:
    """One package for shipped holdings, by id and count.

    The holdings' own words are never read here: only
    the ids, sections and states named beside them
    cross. A package naming no project, no session,
    no exporter or no day refuses - a package stands
    on its provenance, or it does not stand at all.
    """
    if project is None or (isinstance(project, str) and not project.strip()):
        raise ValueError(
            "a package must name the project it packs - "
            "a package of no project packs nothing")
    if source_session is None or (
            isinstance(source_session, str) and not source_session.strip()):
        raise ValueError(
            "a package must name the session it was "
            "exported from - a package from no session "
            "carries no provenance")
    if exported_by is None:
        raise ValueError(
            "a package must name who exported it - a "
            "package exported by no one is no record")
    if exported_on is None:
        raise ValueError(
            "a package must name the day it was exported "
            "on - a package from no day carries no provenance")
    return MemoryPackage(
        title=title, project=project, source_session=source_session,
        map_entry_ids=map_entry_ids, candidate_ids=candidate_ids,
        map_sections=map_sections, ledger_states=ledger_states,
        exported_by=exported_by, exported_on=exported_on, source=source)


def inspect_package_source(piece: Any) -> Dict[str, Any]:
    """Inspect one shipped piece: its references and counts only.

    The piece is judged by the layer that owns its
    type, never by whichever validator happens to
    accept its shape first. A memory-map holding
    reports its entry count; a ledger holding
    reports its candidate count; a package reports
    itself whole. A piece no shipped layer owns
    refuses.
    """
    if isinstance(piece, MemoryPackage):
        return {"project": piece.project,
                "map_count": piece.map_count,
                "candidate_count": piece.candidate_count}
    if isinstance(piece, MemoryMapEntry):
        return {"map_count": 1, "candidate_count": None}
    if isinstance(piece, CandidateMemory):
        return {"map_count": None, "candidate_count": 1}
    if isinstance(piece, dict):
        if "map_entry_ids" in piece or "candidate_ids" in piece:
            checked = validate_package(piece)
            return {"project": checked.project,
                    "map_count": checked.map_count,
                    "candidate_count": checked.candidate_count}
        try:
            _validate_map_entry(piece)
            return {"map_count": 1, "candidate_count": None}
        except Exception:
            pass
        try:
            _validate_candidate(piece)
            return {"map_count": None, "candidate_count": 1}
        except Exception:
            pass
    else:
        from .project_memory_map import MemoryMapBook, MemoryMapRegistry
        from .self_improving_ledger import (
            SelfImprovingBook, SelfImprovingRegistry)
        if isinstance(piece, (MemoryMapBook, MemoryMapRegistry)):
            return {"map_count": len(_map_entries(piece)),
                    "candidate_count": None}
        if isinstance(piece, (SelfImprovingBook, SelfImprovingRegistry)):
            return {"map_count": None,
                    "candidate_count": len(_ledger_candidates(piece))}
    raise ValueError(
        f"no shipped layer owns this piece, got {piece!r}")


def package_from_memory_map(
        source: Any, *, project: Any, source_session: Any,
        exported_by: Any, exported_on: Any,
        candidate_ids: Any = (), ledger_states: Any = (),
        source_word: Any = "project memory map",
        title: Any = None) -> MemoryPackage:
    """Build one package from a project's memory map, by import.

    The map - a book, a registry, entries or one
    entry (M-150), judged by that layer's own
    validation - is read onto a package BY IMPORT by
    its entry ids alone: the ids stand as the
    package's map contents, and the entries' own
    sections stand as the sections riding. The
    project, session and provenance are named beside
    it; ledger candidates, when any ride, are named
    beside it with their states. No entry's title,
    detail or reference is ever read here - only the
    ids and sections the map itself carries cross.
    """
    ids, sections = _map_expectation(source)
    return _package_for(
        title=title if title is not None else (
            f"memory of {project}, packed from its map"),
        project=project, source_session=source_session,
        map_entry_ids=ids, candidate_ids=candidate_ids,
        map_sections=sections, ledger_states=ledger_states,
        exported_by=exported_by, exported_on=exported_on,
        source=source_word)


def package_from_ledger(
        source: Any, *, project: Any, source_session: Any,
        exported_by: Any, exported_on: Any,
        map_entry_ids: Any = (), map_sections: Any = (),
        source_word: Any = "self-improving ledger",
        title: Any = None) -> MemoryPackage:
    """Build one package from a project's ledger, by import.

    The ledger - a book, a registry, candidates or
    one candidate (M-155), judged by that layer's
    own validation, with its decisions judged the
    same way - is read onto a package BY IMPORT by
    its candidate ids alone: the ids stand as the
    package's ledger contents, and each candidate's
    standing (its decision's state, or ``candidate``
    while no decision stands) stands as the states
    riding. The project, session and provenance are
    named beside it; map entries, when any ride, are
    named beside it with their sections. No
    candidate's title, detail or provenance words
    are ever read here - only the ids and states the
    ledger itself carries cross.
    """
    ids, states = _ledger_expectation(source)
    return _package_for(
        title=title if title is not None else (
            f"memory of {project}, packed from its ledger"),
        project=project, source_session=source_session,
        map_entry_ids=map_entry_ids, candidate_ids=ids,
        map_sections=map_sections, ledger_states=states,
        exported_by=exported_by, exported_on=exported_on,
        source=source_word)


def package_from_memory_books(
        map_source: Any, ledger_source: Any, *, project: Any,
        source_session: Any, exported_by: Any, exported_on: Any,
        source_word: Any = "memory import/export",
        title: Any = None) -> MemoryPackage:
    """Build one package from a project's map + ledger, by import.

    The shipped memory map (M-150) and the shipped
    self-improving ledger (M-155) of one project are
    read onto one package BY IMPORT, each judged by
    its own layer's validation on the way: the map's
    entry ids and their sections, and the ledger's
    candidate ids and their standings, stand as the
    package's whole contents. The project, session
    and provenance are named beside them. This is
    the export road's own composition: the session's
    two holdings become one portable file record,
    and nothing of their words crosses - ids,
    sections and states alone.
    """
    map_ids, sections = _map_expectation(map_source)
    candidate_ids, states = _ledger_expectation(ledger_source)
    return _package_for(
        title=title if title is not None else (
            f"memory of {project}, packed to ride with the repo"),
        project=project, source_session=source_session,
        map_entry_ids=map_ids, candidate_ids=candidate_ids,
        map_sections=sections, ledger_states=states,
        exported_by=exported_by, exported_on=exported_on,
        source=source_word)


# ---------------------------------------------------------------------
# The memory panel: every package carried whole, derived.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PackagePanelRow:
    """One package carried whole into the panel.

    Every field is the package's own head: its id,
    title, project and source session, its map,
    ledger and whole piece counts, and its
    provenance head. :func:`validate_row` judged
    against its package refuses a row whose fields
    disagree with the row they derive.
    """

    package_id: str
    title: str
    project: str
    source_session: str
    map_count: int
    candidate_count: int
    piece_count: int
    exported_by: str
    exported_on: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "package_id", normalize_member_id(self.package_id))
        object.__setattr__(
            self, "title", _check_title(self.title, "a row's title"))
        object.__setattr__(
            self, "project", _check_title(self.project, "a row's project"))
        object.__setattr__(
            self, "source_session",
            _check_word(self.source_session, "a row's source session"))
        object.__setattr__(
            self, "map_count",
            _check_count(self.map_count, "a row's map count"))
        object.__setattr__(
            self, "candidate_count",
            _check_count(self.candidate_count, "a row's candidate count"))
        object.__setattr__(
            self, "piece_count",
            _check_count(self.piece_count, "a row's piece count"))
        if self.piece_count != self.map_count + self.candidate_count:
            raise ValueError(
                "a row's piece count must be its own "
                "map and ledger counts' sum")
        if self.piece_count < 1:
            raise ValueError(
                "a row's piece count must name at least "
                "one piece of its own")
        object.__setattr__(
            self, "exported_by",
            _check_title(self.exported_by, "a row's exporter"))
        object.__setattr__(
            self, "exported_on", _check_day(self.exported_on))

    @property
    def sort_key(self) -> Tuple[str, str, str, str]:
        """This row's place in panel order (derived).

        Rows stand by project, then day, then title,
        then package id.
        """
        return (self.project.lower(), self.exported_on,
                self.title.lower(), self.package_id)

    def count_for(self, kind: Any) -> int:
        """This row's count in one ride kind."""
        if normalize_ride_kind(kind) == "map":
            return self.map_count
        return self.candidate_count

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "memory_import_export_panel_row",
            "slice": MEMORY_IMPORT_EXPORT_SLICE,
            "package_id": self.package_id,
            "title": self.title,
            "project": self.project,
            "source_session": self.source_session,
            "map_count": self.map_count,
            "candidate_count": self.candidate_count,
            "piece_count": self.piece_count,
            "exported_by": self.exported_by,
            "exported_on": self.exported_on,
        }


def _row_for_package(package: MemoryPackage) -> PackagePanelRow:
    return PackagePanelRow(
        package_id=package.package_id, title=package.title,
        project=package.project, source_session=package.source_session,
        map_count=package.map_count,
        candidate_count=package.candidate_count,
        piece_count=package.piece_count,
        exported_by=package.exported_by,
        exported_on=package.exported_on)


def _check_row_ref(value: Any) -> PackagePanelRow:
    if isinstance(value, PackagePanelRow):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _ROW_KEYS
        if unknown:
            raise ValueError(
                "unknown row keys: %s" % ", ".join(sorted(unknown)))

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            picked = _pick_any(value, spellings, what)
            if picked is None:
                raise ValueError(f"a row is missing its {what}")
            return picked

        return PackagePanelRow(
            package_id=_needed(("package_id", "id"), "package id"),
            title=_needed(("title",), "title"),
            project=_needed(("project",), "project"),
            source_session=_needed(("source_session",), "source session"),
            map_count=_needed(("map_count", "map"), "map count"),
            candidate_count=_needed(
                ("candidate_count", "candidates"), "candidate count"),
            piece_count=_needed(("piece_count", "pieces"), "piece count"),
            exported_by=_needed(("exported_by",), "exporter"),
            exported_on=_needed(("exported_on",), "exported-on day"))
    raise ValueError(f"a panel row is needed, got {value!r}")


def validate_row(row: Any, package: Any = None) -> PackagePanelRow:
    """Validate one panel row into a PackagePanelRow.

    With *package* given, the row is judged against
    the row derived from that package: a stored row
    whose fields disagree with the derived row
    refuses.
    """
    current = _check_row_ref(row)
    if package is not None:
        checked = _check_package_ref(package)
        derived = _row_for_package(checked)
        if current != derived:
            raise ValueError(
                "a stored row disagrees with the row "
                "derived from its package")
    return current


def build_row(row: Any = None, package: Any = None,
              **kwargs: Any) -> PackagePanelRow:
    """Build one validated row, from a mapping or field words."""
    if isinstance(row, PackagePanelRow) and not kwargs:
        return validate_row(row, package)
    if isinstance(row, dict) or row is None:
        merged: Dict[str, Any] = {}
        if isinstance(row, dict):
            merged.update(row)
        merged.update(kwargs)
        return validate_row(merged, package)
    return validate_row(row, package)


@dataclass(frozen=True)
class RideCount:
    """One ride kind's count in a panel: its pieces tallied."""

    kind: str
    items: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "kind", normalize_ride_kind(self.kind))
        object.__setattr__(
            self, "items",
            _check_count(self.items, "a ride count's items"))

    def to_record(self) -> Dict[str, Any]:
        return {"kind": self.kind, "items": self.items}


def _check_ride_count_ref(value: Any) -> RideCount:
    if isinstance(value, RideCount):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _RIDE_COUNT_KEYS
        if unknown:
            raise ValueError(
                "unknown ride-count keys: %s"
                % ", ".join(sorted(unknown)))
        kind = _pick_any(value, ("kind",), "kinds")
        if kind is None:
            raise ValueError("a ride count is missing its kind")
        items = _pick_any(value, ("items", "count"), "counts")
        if items is None:
            raise ValueError("a ride count is missing its items")
        return RideCount(kind=kind, items=items)
    raise ValueError(f"a ride count is needed, got {value!r}")


def _panel_account(total_packages: int, total_pieces: int,
                   total_map: int, total_candidates: int,
                   ride_counts: Tuple[RideCount, ...]
                   ) -> Tuple[str, ...]:
    tallies = ", ".join(
        f"{count.kind} {count.items}"
        for count in sorted(ride_counts, key=lambda count: count.kind))
    return (
        f"The memory panel holds {total_packages} packages: "
        f"{total_pieces} pieces in all, {total_map} "
        f"map entries and {total_candidates} "
        f"ledger candidates: {tallies}.",
        "Packages stand by project, then day, then "
        "title, then package id, so two panels of "
        "one book diff cleanly, line by line.",
        "Every piece a package carries is carried from "
        "the project's own memory map and ledger, and "
        "a package whose contents disagree with those "
        "holdings is refused - a package carries only "
        "what its sources hold.",
        "The panel is read off the book at call time - "
        "it is derived, never stored loose.",
    )


@dataclass(frozen=True)
class PackagePanel:
    """The memory panel of one book, derived whole.

    ``rows`` are the book's packages carried whole,
    in panel order (by project, then day, then
    title, then package id); ``total_packages`` is
    the rows' own count, ``total_map_entries`` the
    sum of their map pieces, ``total_candidates``
    the sum of their ledger pieces and
    ``total_pieces`` the sum of both;
    ``ride_counts`` are the per-kind tallies of
    every piece in the book; ``account`` is read off
    those numbers. A panel whose rows stand out of
    panel order, or whose tallies are not its own
    rows' tallies, refuses at construction;
    :func:`validate_panel` judged against a book
    refuses a stored panel that disagrees with the
    derived one.
    """

    rows: Tuple[PackagePanelRow, ...] = ()
    total_packages: int = 0
    total_map_entries: int = 0
    total_candidates: int = 0
    total_pieces: int = 0
    ride_counts: Tuple[RideCount, ...] = ()
    account: Tuple[str, ...] = ()
    panel_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.panel_id is not None:
            object.__setattr__(
                self, "panel_id", normalize_member_id(self.panel_id))
        if isinstance(self.rows, (str, bytes)) \
                or not isinstance(self.rows, (list, tuple)):
            raise ValueError(
                f"a panel's rows must be a list of rows, "
                f"got {self.rows!r}")
        rows = tuple(_check_row_ref(r) for r in self.rows)
        seen = set()
        for row in rows:
            if row.package_id in seen:
                raise ValueError(
                    f"a panel row for package {row.package_id!r} "
                    f"already exists")
            seen.add(row.package_id)
        keys = [row.sort_key for row in rows]
        if keys != sorted(keys):
            raise ValueError(
                "a panel's rows must stand in panel order "
                "(by project, then day, then title, then "
                "package id)")
        object.__setattr__(self, "rows", rows)
        object.__setattr__(
            self, "total_packages",
            _check_count(self.total_packages, "a panel's total packages"))
        if self.total_packages != len(rows):
            raise ValueError(
                "a panel's total packages must be its own "
                "rows' count")
        object.__setattr__(
            self, "total_map_entries",
            _check_count(
                self.total_map_entries, "a panel's total map entries"))
        if self.total_map_entries != sum(r.map_count for r in rows):
            raise ValueError(
                "a panel's total map entries must be its own "
                "rows' sum")
        object.__setattr__(
            self, "total_candidates",
            _check_count(
                self.total_candidates, "a panel's total candidates"))
        if self.total_candidates != sum(r.candidate_count for r in rows):
            raise ValueError(
                "a panel's total candidates must be its "
                "own rows' sum")
        object.__setattr__(
            self, "total_pieces",
            _check_count(self.total_pieces, "a panel's total pieces"))
        if self.total_pieces != sum(r.piece_count for r in rows):
            raise ValueError(
                "a panel's total pieces must be its own "
                "rows' sum")
        if self.total_pieces != (
                self.total_map_entries + self.total_candidates):
            raise ValueError(
                "a panel's total pieces must be its own "
                "map and ledger totals' sum")
        if isinstance(self.ride_counts, (str, bytes)) \
                or not isinstance(self.ride_counts, (list, tuple)):
            raise ValueError(
                f"a panel's ride counts must be a list, "
                f"got {self.ride_counts!r}")
        ride_counts = tuple(
            _check_ride_count_ref(c) for c in self.ride_counts)
        seen_kinds = set()
        for count in ride_counts:
            if count.kind in seen_kinds:
                raise ValueError(
                    f"a ride count named {count.kind!r} "
                    f"already exists")
            seen_kinds.add(count.kind)
        object.__setattr__(self, "ride_counts", ride_counts)
        if sum(c.items for c in ride_counts) != self.total_pieces:
            raise ValueError(
                "a panel's ride counts must sum to "
                "its own total pieces")
        tallies = {
            "map": sum(r.map_count for r in rows),
            "ledger": sum(r.candidate_count for r in rows)}
        for count in ride_counts:
            if count.items != tallies.get(count.kind, 0):
                raise ValueError(
                    "a panel's ride counts must be its "
                    "own rows' counts")
        if {k for k, v in tallies.items() if v} != {
                c.kind for c in ride_counts}:
            raise ValueError(
                "a panel's ride counts must name "
                "every kind its rows carry")
        object.__setattr__(self, "account", _check_account(self.account))

    def row_for(self, package_id: Any) -> PackagePanelRow:
        """The panel row one package names in this panel."""
        wanted = normalize_member_id(package_id)
        for row in self.rows:
            if row.package_id == wanted:
                return row
        raise KeyError(f"no row in the panel: package {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "memory_import_export_panel",
            "slice": MEMORY_IMPORT_EXPORT_SLICE,
            "panel_id": self.panel_id,
            "rows": [row.to_record() for row in self.rows],
            "total_packages": self.total_packages,
            "total_map_entries": self.total_map_entries,
            "total_candidates": self.total_candidates,
            "total_pieces": self.total_pieces,
            "ride_counts": [c.to_record() for c in self.ride_counts],
            "account": list(self.account),
        }


def _held_packages(source: Any) -> Tuple[MemoryPackage, ...]:
    if isinstance(source, MemoryExportBook):
        return source.packages
    if isinstance(source, MemoryPackageRegistry):
        return source.list_packages()
    if isinstance(source, (list, tuple)):
        return tuple(_check_package_ref(item) for item in source)
    raise ValueError(f"memory packages are needed, got {source!r}")


def derive_panel(source: Any) -> PackagePanel:
    """Derive the memory panel from one book.

    The rows are the book's packages carried whole,
    in panel order: by project, then day, then
    title, then package id. *source* is a book or a
    registry. A source holding no package refuses -
    a panel of nothing is no panel.
    """
    packages = _held_packages(source)
    if not packages:
        raise ValueError("a panel needs at least one memory package")
    rows = []
    for package in packages:
        if package.package_id is None:
            raise ValueError(
                "a panel row must name its package - a "
                "package with no id refuses derivation")
        rows.append(_row_for_package(package))
    rows = tuple(sorted(rows, key=lambda r: r.sort_key))
    tallies = {
        "map": sum(r.map_count for r in rows),
        "ledger": sum(r.candidate_count for r in rows)}
    ride_counts = tuple(
        RideCount(kind=kind, items=tallies[kind])
        for kind in RIDE_KINDS if tallies[kind])
    total_pieces = sum(r.piece_count for r in rows)
    return PackagePanel(
        rows=rows, total_packages=len(rows),
        total_map_entries=tallies["map"],
        total_candidates=tallies["ledger"],
        total_pieces=total_pieces, ride_counts=ride_counts,
        account=_panel_account(
            len(rows), total_pieces, tallies["map"],
            tallies["ledger"], ride_counts))


def validate_panel(panel: Any, source: Any = None
                   ) -> PackagePanel:
    """Validate one panel into a PackagePanel.

    Accepts a panel or a mapping naming ``rows`` (or
    ``packages``), a ``total_packages`` (or
    ``total``), ``total_map_entries``,
    ``total_candidates``, ``total_pieces``,
    ``ride_counts`` (or ``rides``), an ``account``
    (or ``statements``) and an optional ``panel_id``
    (or ``id``). With *source* given (a book), the
    panel is judged against the panel derived from
    that book.
    """
    if isinstance(panel, PackagePanel):
        current = panel
    elif isinstance(panel, dict):
        unknown = set(panel) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                "unknown panel keys: %s" % ", ".join(sorted(unknown)))
        rows = _pick_any(panel, ("rows", "packages"), "rows")
        if rows is None:
            raise ValueError("a panel is missing its rows")
        total = _pick_any(panel, ("total_packages", "total"), "totals")
        if total is None:
            raise ValueError("a panel is missing its total packages")
        map_total = _pick_any(
            panel, ("total_map_entries", "map_entries"), "map totals")
        if map_total is None:
            raise ValueError("a panel is missing its total map entries")
        cand_total = _pick_any(
            panel, ("total_candidates", "candidates"),
            "candidate totals")
        if cand_total is None:
            raise ValueError("a panel is missing its total candidates")
        pieces = _pick_any(panel, ("total_pieces", "pieces"), "pieces")
        if pieces is None:
            raise ValueError("a panel is missing its total pieces")
        ride_counts = _pick_any(
            panel, ("ride_counts", "rides"), "ride counts")
        if ride_counts is None:
            raise ValueError("a panel is missing its ride counts")
        account = _pick_any(panel, ("account", "statements"), "accounts")
        if account is None:
            raise ValueError("a panel names no account of its own")
        kwargs: Dict[str, Any] = {
            "rows": rows, "total_packages": total,
            "total_map_entries": map_total,
            "total_candidates": cand_total, "total_pieces": pieces,
            "ride_counts": ride_counts, "account": account}
        panel_id = _pick_any(panel, ("panel_id", "id"), "panel ids")
        if panel_id is not None:
            kwargs["panel_id"] = panel_id
        current = PackagePanel(**kwargs)
    else:
        raise ValueError(f"a panel must be a mapping, got {panel!r}")
    if source is not None:
        derived = derive_panel(source)
        if (current.rows != derived.rows
                or current.total_packages != derived.total_packages
                or current.total_map_entries != derived.total_map_entries
                or current.total_candidates != derived.total_candidates
                or current.total_pieces != derived.total_pieces
                or current.ride_counts != derived.ride_counts
                or current.account != derived.account):
            raise ValueError(
                "a stored panel disagrees with the panel "
                "derived from its book")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> PackagePanel:
    """Build one validated panel, from a mapping or field words."""
    if isinstance(panel, PackagePanel) and not kwargs:
        return validate_panel(panel, source)
    if isinstance(panel, dict) or panel is None:
        merged: Dict[str, Any] = {}
        if isinstance(panel, dict):
            merged.update(panel)
        merged.update(kwargs)
        return validate_panel(merged, source)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The portability verdict: the whole book judged, derived.
# ---------------------------------------------------------------------


def _verdict_word(total_complete: int, total_map_only: int,
                  total_ledger_only: int) -> str:
    """The verdict word a book's own tallies derive."""
    if total_map_only == 0 and total_ledger_only == 0:
        return "fully-portable"
    if total_complete == 0 and total_ledger_only == 0:
        return "map-only"
    if total_complete == 0 and total_map_only == 0:
        return "ledger-only"
    return "partially-portable"


@dataclass(frozen=True)
class PortabilityVerdict:
    """One portability verdict: a whole book judged, as data.

    ``total_packages`` counts the book's packages,
    ``total_map_entries`` their map pieces and
    ``total_candidates`` their ledger pieces;
    ``total_complete`` counts the packages riding
    map and ledger both, ``total_map_only`` those
    riding the map alone and ``total_ledger_only``
    those riding the ledger alone;
    ``distinct_projects`` counts how many projects
    those packages pack; ``verdict`` is the book's
    word - ``fully-portable`` when every package
    rides both holdings, ``map-only`` or
    ``ledger-only`` when no package rides both and
    only one holding rides at all,
    ``partially-portable`` otherwise.
    :func:`validate_verdict` judged against a book
    refuses a stored verdict that disagrees with the
    verdict derived from that book, and a verdict
    whose word is not its own tallies' word refuses
    at construction - a partial packing is never
    smoothed into a whole one.
    """

    total_packages: int
    total_map_entries: int
    total_candidates: int
    total_pieces: int
    total_complete: int
    total_map_only: int
    total_ledger_only: int
    distinct_projects: int
    verdict: str

    def __post_init__(self) -> None:
        for field, what in (
                ("total_packages", "total packages"),
                ("total_map_entries", "total map entries"),
                ("total_candidates", "total candidates"),
                ("total_pieces", "total pieces"),
                ("total_complete", "total complete"),
                ("total_map_only", "total map-only"),
                ("total_ledger_only", "total ledger-only"),
                ("distinct_projects", "distinct projects")):
            object.__setattr__(
                self, field,
                _check_count(getattr(self, field), f"a verdict's {what}"))
        if self.total_packages < 1:
            raise ValueError("a verdict judges at least one package")
        if self.total_pieces != (
                self.total_map_entries + self.total_candidates):
            raise ValueError(
                "a verdict's total pieces must be its own "
                "map and ledger totals' sum")
        if (self.total_complete + self.total_map_only
                + self.total_ledger_only) != self.total_packages:
            raise ValueError(
                "a verdict's complete, map-only and "
                "ledger-only packages must sum to its own "
                "total packages")
        if self.distinct_projects < 1 \
                or self.distinct_projects > self.total_packages:
            raise ValueError(
                "a verdict's distinct projects must stand "
                "between one and its own total packages")
        verdict = _clean_text(self.verdict, "a verdict's word")
        expected = _verdict_word(
            self.total_complete, self.total_map_only,
            self.total_ledger_only)
        if verdict != expected:
            raise ValueError(
                "a verdict's word must be its own counts' "
                "word - a verdict is derived, never stored "
                "loose")
        object.__setattr__(self, "verdict", verdict)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "memory_import_export_verdict",
            "slice": MEMORY_IMPORT_EXPORT_SLICE,
            "total_packages": self.total_packages,
            "total_map_entries": self.total_map_entries,
            "total_candidates": self.total_candidates,
            "total_pieces": self.total_pieces,
            "total_complete": self.total_complete,
            "total_map_only": self.total_map_only,
            "total_ledger_only": self.total_ledger_only,
            "distinct_projects": self.distinct_projects,
            "verdict": self.verdict,
        }


def derive_verdict(source: Any) -> PortabilityVerdict:
    """Derive the portability verdict of one book.

    The verdict's tallies are the derived panel's
    own counts read whole, its completeness counts
    are read off the packages themselves, its
    distinct count is read off the packages' actual
    projects, and its word is read off its
    completeness tallies. *source* is a book or a
    registry.
    """
    packages = _held_packages(source)
    panel = derive_panel(source)
    complete = sum(1 for p in packages if p.rides_both)
    map_only = sum(
        1 for p in packages
        if p.map_entry_ids and not p.candidate_ids)
    ledger_only = sum(
        1 for p in packages
        if p.candidate_ids and not p.map_entry_ids)
    return PortabilityVerdict(
        total_packages=panel.total_packages,
        total_map_entries=panel.total_map_entries,
        total_candidates=panel.total_candidates,
        total_pieces=panel.total_pieces,
        total_complete=complete, total_map_only=map_only,
        total_ledger_only=ledger_only,
        distinct_projects=len({p.project for p in packages}),
        verdict=_verdict_word(complete, map_only, ledger_only))


def _check_verdict_ref(value: Any) -> PortabilityVerdict:
    if isinstance(value, PortabilityVerdict):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _VERDICT_KEYS
        if unknown:
            raise ValueError(
                "unknown verdict keys: %s" % ", ".join(sorted(unknown)))

        def _needed(spellings: Tuple[str, ...], what: str) -> Any:
            picked = _pick_any(value, spellings, what)
            if picked is None:
                raise ValueError(f"a verdict is missing its {what}")
            return picked

        return PortabilityVerdict(
            total_packages=_needed(
                ("total_packages", "total"), "total packages"),
            total_map_entries=_needed(
                ("total_map_entries", "map_entries"),
                "total map entries"),
            total_candidates=_needed(
                ("total_candidates", "candidates"),
                "total candidates"),
            total_pieces=_needed(
                ("total_pieces", "pieces"), "total pieces"),
            total_complete=_needed(
                ("total_complete", "complete"), "total complete"),
            total_map_only=_needed(
                ("total_map_only", "map_only"), "total map-only"),
            total_ledger_only=_needed(
                ("total_ledger_only", "ledger_only"),
                "total ledger-only"),
            distinct_projects=_needed(
                ("distinct_projects", "projects"), "distinct projects"),
            verdict=_needed(("verdict",), "verdict word"))
    raise ValueError(f"a portability verdict is needed, got {value!r}")


def validate_verdict(verdict: Any, source: Any = None) -> PortabilityVerdict:
    """Validate one verdict into a PortabilityVerdict.

    With *source* given (a book), the verdict is
    judged against the verdict derived from that
    book: a stored verdict whose tallies, distinct
    count or word disagree with the derived verdict
    refuses.
    """
    current = _check_verdict_ref(verdict)
    if source is not None:
        derived = derive_verdict(source)
        if current != derived:
            raise ValueError(
                "a stored verdict disagrees with the "
                "verdict derived from its book")
    return current


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> PortabilityVerdict:
    """Build one validated verdict, from a mapping or field words."""
    if isinstance(verdict, PortabilityVerdict) and not kwargs:
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict) or verdict is None:
        merged: Dict[str, Any] = {}
        if isinstance(verdict, dict):
            merged.update(verdict)
        merged.update(kwargs)
        return validate_verdict(merged, source)
    return validate_verdict(verdict, source)


# ---------------------------------------------------------------------
# The book: packages in held order, panels judged.
# ---------------------------------------------------------------------


def _judge_packages(packages: Tuple[MemoryPackage, ...],
                    held: Tuple[MemoryPackage, ...] = ()) -> None:
    """Judge packages against held packages: the book's laws.

    One package per project and session - one
    session's export of one project stands once -
    and no piece riding in two packages: a map entry
    or a ledger candidate is packed once. *held*
    names packages already standing (a registry's),
    judged alongside.
    """
    all_packages = tuple(held) + tuple(packages)
    seen_exports = set()
    owners: Dict[str, str] = {}
    for package in all_packages:
        key = (package.project, package.source_session)
        if key in seen_exports:
            raise ValueError(
                f"the session {package.source_session!r} "
                f"already packs the project "
                f"{package.project!r} - one session's export "
                f"of one project stands once")
        seen_exports.add(key)
        for piece in tuple(package.map_entry_ids) + tuple(
                package.candidate_ids):
            if piece in owners:
                raise ValueError(
                    f"a piece packed twice: piece {piece!r} "
                    f"rides in two packages "
                    f"({owners[piece]!r} and "
                    f"{package.source_session!r}) - a piece "
                    f"is packed once")
            owners[piece] = package.source_session


@dataclass(frozen=True)
class MemoryExportBook:
    """One memory export book: its packages, in held order.

    ``packages`` are the memory packages, in held
    order, each with its provenance whole, one per
    project and session, no piece riding in two
    packages. ``panels`` are the book's derivations -
    memory panels of the whole book, each judged
    against the book by :func:`validate_book`;
    ``canon_note`` is the book's own note. The total
    is the packages' own count, judged at
    construction.
    """

    title: str = ""
    packages: Tuple[MemoryPackage, ...] = ()
    panels: Tuple[PackagePanel, ...] = ()
    canon_note: str = ""
    total_packages: Optional[int] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book's title"))
        if isinstance(self.packages, (str, bytes)) \
                or not isinstance(self.packages, (list, tuple)):
            raise ValueError(
                f"a book's packages must be a list of "
                f"packages, got {self.packages!r}")
        packages = tuple(_check_package_ref(item) for item in self.packages)
        if not packages:
            raise ValueError("a memory export book holds at least one package")
        seen_ids = set()
        for package in packages:
            if package.package_id is not None:
                if package.package_id in seen_ids:
                    raise ValueError(
                        f"a package named "
                        f"{package.package_id!r} already exists")
                seen_ids.add(package.package_id)
        _judge_packages(packages)
        object.__setattr__(self, "packages", packages)
        if isinstance(self.panels, (str, bytes)) \
                or not isinstance(self.panels, (list, tuple)):
            raise ValueError(
                f"a book's panels must be a list of panels, "
                f"got {self.panels!r}")
        panels = tuple(
            p if isinstance(p, PackagePanel)
            else validate_panel(p)
            for p in self.panels)
        seen_panels = set()
        for panel in panels:
            if panel.panel_id is not None:
                if panel.panel_id in seen_panels:
                    raise ValueError(
                        f"a panel named {panel.panel_id!r} "
                        f"already exists")
                seen_panels.add(panel.panel_id)
        object.__setattr__(self, "panels", panels)
        if not isinstance(self.canon_note, str):
            raise ValueError("a book's note must be text")
        object.__setattr__(self, "canon_note", self.canon_note.strip())
        given = self.total_packages
        if given is None:
            object.__setattr__(self, "total_packages", len(packages))
        else:
            checked = _check_count(given, "a book's total packages")
            if checked != len(packages):
                raise ValueError(
                    "a book's total packages must be its "
                    "own packages' count")
            object.__setattr__(self, "total_packages", checked)

    def package_for(self, package_id: Any) -> MemoryPackage:
        """The package one id names in this book."""
        wanted = normalize_member_id(package_id)
        for package in self.packages:
            if package.package_id == wanted:
                return package
        raise KeyError(f"no package in the book: {wanted!r}")

    def package_for_project(self, project: Any) -> MemoryPackage:
        """The first package packing one project in this book."""
        wanted = _check_title(project, "a project")
        for package in self.packages:
            if package.project == wanted:
                return package
        raise KeyError(f"no package in the book packs {wanted!r}")

    def panel_for(self, panel_id: Any) -> PackagePanel:
        """The stored panel one id names in this book."""
        wanted = normalize_member_id(panel_id)
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel in the book: {wanted!r}")

    def package_ids(self) -> Tuple[str, ...]:
        """Every held package id, in held order."""
        return tuple(
            item.package_id for item in self.packages if item.package_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "memory_import_export_book",
            "slice": MEMORY_IMPORT_EXPORT_SLICE,
            "title": self.title,
            "package_ids": list(self.package_ids()),
            "package_count": len(self.packages),
            "panel_count": len(self.panels),
        }


def validate_book(data: Any, *, require_example: bool = False
                  ) -> MemoryExportBook:
    """Validate one memory-export mapping into a book.

    The mapping names a ``schema``, a ``guide``
    mapping (its ``title``), a ``packages`` list (or
    ``records``) and an optional ``panels`` list.
    Every package stands on its own validation, then
    the whole is judged: package ids unique, one
    package per project and session, no piece packed
    twice, and every stored panel judged against the
    book. With ``require_example`` the shipped
    example is held to its pinned shape.
    """
    if isinstance(data, MemoryExportBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a memory export book must be a mapping, got {data!r}")
    unknown = set(data) - _MEMORY_EXPORT_BOOK_KEYS
    if unknown:
        raise ValidationError(
            "unknown memory-export-book keys: %s"
            % ", ".join(sorted(unknown)))
    if data.get("schema") != MEMORY_IMPORT_EXPORT_SCHEMA:
        raise ValidationError(
            f"a memory export book must carry schema "
            f"{MEMORY_IMPORT_EXPORT_SCHEMA!r}, "
            f"got {data.get('schema')!r}")
    packages = _pick_any(data, ("packages", "records"), "packages")
    if packages is None:
        raise ValidationError("a memory export book is missing its packages")
    if not isinstance(packages, (list, tuple)):
        raise ValidationError("a memory export book's packages must be a list")
    if data.get("panels") is not None \
            and not isinstance(data["panels"], (list, tuple)):
        raise ValidationError("a memory export book's panels must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a memory export book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a memory export book is missing its title")
        note = data.get("canon_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a memory export book's note must be text")
        book = MemoryExportBook(
            title=title, packages=tuple(packages),
            panels=tuple(data.get("panels") or ()), canon_note=note)
        for panel in book.panels:
            validate_panel(panel, book)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if require_example:
        if book.title != _EXAMPLE_TITLE:
            raise ValidationError(
                "the shipped example memory export book's "
                "title is not the pinned title")
        if book.package_ids() != _EXAMPLE_PACKAGE_IDS:
            raise ValidationError(
                "the shipped example's packages are not "
                "the pinned packages")
        panel = book.panel_for(_EXAMPLE_PANEL_ID)
        if tuple(r.package_id for r in panel.rows) != _EXAMPLE_PANEL_ROW_IDS:
            raise ValidationError(
                "the shipped example panel does not name "
                "its pinned rows in panel order")
        if panel.account != _EXAMPLE_PANEL_ACCOUNT:
            raise ValidationError(
                "the shipped example panel does not carry "
                "its pinned account word-for-word")
        first = book.packages[0]
        if first.package_id != _EXAMPLE_FIRST_PACKAGE_ID \
                or first.title != _EXAMPLE_FIRST_PACKAGE_TITLE:
            raise ValidationError(
                "the shipped example's first package is "
                "not its pinned package of its pinned title")
    return book


def build_book(book: Any = None, **kwargs: Any) -> MemoryExportBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, MemoryExportBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return MemoryExportBook(**merged)
    if book is None:
        return MemoryExportBook(**kwargs)
    raise ValueError(f"a memory export book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> MemoryExportBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_memory_import_export(
        data: Optional[Dict[str, Any]] = None) -> MemoryExportBook:
    """Load and validate the shipped example book (or *data*)."""
    raw = data if data is not None else load_resource(
        MEMORY_IMPORT_EXPORT_RESOURCE)
    return _book_from(raw, require_example=True)


def load_memory_import_export_file(path: Any) -> MemoryExportBook:
    """Load and validate a memory export book from a file at *path*."""
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held package by package.
# ---------------------------------------------------------------------


class MemoryPackageRegistry:
    """One book's packages, held one by one.

    The registry holds packages, never panels or
    verdicts: the panel and the portability verdict
    are derivations, read off the whole held book at
    call time. A whole book is judged whole - as a
    book judges it, and against everything already
    held - before its packages are held in book
    order, so an import never lands partially. A
    package held here stands apart: a second package
    packing a held project from a held session, or
    naming a held piece, refuses - one export stands
    once and a piece is packed once.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._packages: Dict[str, MemoryPackage] = {}
        self._package_order: list = []
        self._next_package = 1
        if book is not None:
            self.register_book(book)

    def _fresh_package_id(self, held_ids: Any) -> str:
        while f"package-{self._next_package}" in held_ids:
            self._next_package += 1
        fresh = f"package-{self._next_package}"
        self._next_package += 1
        return fresh

    def _check_standing_free(self, package: MemoryPackage) -> None:
        _judge_packages((package,), held=self.list_packages())

    def register_package(self, package: Any) -> MemoryPackage:
        """Register one package into the held book."""
        validated = _check_package_ref(package)
        if validated.package_id is not None \
                and validated.package_id in self._packages:
            raise ValueError(
                f"a package named "
                f"{validated.package_id!r} already exists")
        self._check_standing_free(validated)
        return self._hold_package(validated)

    def _hold_package(self, validated: MemoryPackage) -> MemoryPackage:
        if validated.package_id is None:
            validated = replace(
                validated,
                package_id=self._fresh_package_id(set(self._packages)))
        self._packages[validated.package_id] = validated
        self._package_order.append(validated.package_id)
        return validated

    def register_book(self, book: Any) -> MemoryExportBook:
        """Register every package of one book, in order.

        The book is judged whole, and against the
        held book, before any of its packages is
        held: a refusal holds nothing new.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a memory "
                "export book under a different title")
        for package in validated.packages:
            if package.package_id in self._packages:
                raise ValueError(
                    f"a package named "
                    f"{package.package_id!r} already exists")
        _judge_packages(validated.packages, held=self.list_packages())
        self._title = validated.title
        for package in validated.packages:
            self._hold_package(package)
        return self.book()

    def get_package(self, package_id: Any) -> MemoryPackage:
        """The package one id names among the held packages."""
        wanted = normalize_member_id(package_id)
        if wanted not in self._packages:
            raise KeyError(f"unknown package: {wanted!r}")
        return self._packages[wanted]

    def package_for_project(self, project: Any) -> MemoryPackage:
        """The first held package packing one project."""
        wanted = _check_title(project, "a project")
        for package_id in self._package_order:
            package = self._packages[package_id]
            if package.project == wanted:
                return package
        raise KeyError(f"no package held packs {wanted!r}")

    def latest_package(self) -> MemoryPackage:
        """The most recently held package."""
        if not self._package_order:
            raise ValueError("no package is held yet")
        return self._packages[self._package_order[-1]]

    def list_packages(self) -> Tuple[MemoryPackage, ...]:
        """Every held package, in the order they were held."""
        return tuple(self._packages[item] for item in self._package_order)

    def book(self) -> MemoryExportBook:
        """The held packages as one validated book."""
        if self._title is None:
            raise ValueError("no memory export book is held yet")
        return MemoryExportBook(
            title=self._title, packages=self.list_packages())

    def panel(self) -> PackagePanel:
        """Derive the memory panel of the whole held book."""
        return derive_panel(self)

    def verdict(self) -> PortabilityVerdict:
        """Derive the portability verdict of the whole held book."""
        return derive_verdict(self)


# ---------------------------------------------------------------------
# The visible surface: how the book stands, read off any book.
# ---------------------------------------------------------------------


def package_refs(source: Any) -> Tuple[Tuple[str, str], ...]:
    """Every package one source holds, in panel order.

    Each held package's project and the session it
    was exported from, in the order the derived
    panel shows them. *source* is a book or a
    registry.
    """
    panel = derive_panel(source)
    return tuple((row.project, row.source_session) for row in panel.rows)


def total_map_entries(source: Any) -> int:
    """The map entries one source holds, in all."""
    return derive_panel(source).total_map_entries


def total_candidates(source: Any) -> int:
    """The ledger candidates one source holds, in all."""
    return derive_panel(source).total_candidates


def total_pieces(source: Any) -> int:
    """The pieces one source holds, in all."""
    return derive_panel(source).total_pieces


# ---------------------------------------------------------------------
# Package news, shaped as session records.
# ---------------------------------------------------------------------


def package_record(package: Any) -> Dict[str, Any]:
    """The session-news record of one memory package."""
    current = package if isinstance(package, MemoryPackage) \
        else build_package(package)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Memory package for {current.project} from "
        f"session {current.source_session}: "
        f"\"{current.title}\" - {current.piece_count} pieces "
        f"(map {current.map_count}, ledger "
        f"{current.candidate_count}), exported by "
        f"{current.exported_by} on {current.exported_on}.")
    return record_out


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived panel."""
    current = validate_panel(panel, source)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Memory panel: {current.total_packages} packages - "
        f"{current.total_pieces} pieces, "
        f"{current.total_map_entries} map entries, "
        f"{current.total_candidates} ledger candidates.")
    return record_out


def verdict_record(verdict: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived verdict."""
    current = validate_verdict(verdict, source)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Portability verdict: {current.verdict} - "
        f"{current.total_complete} packages ride both, "
        f"{current.total_map_only} map-only, "
        f"{current.total_ledger_only} ledger-only, across "
        f"{current.distinct_projects} projects.")
    return record_out


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one memory export book."""
    current = book if isinstance(book, MemoryExportBook) \
        else build_book(book)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Memory import/export {current.title}: "
        f"{record_out['package_count']} packages held.")
    return record_out


def plain_words(package: Any) -> str:
    """One memory package, in one plain sentence."""
    current = package if isinstance(package, MemoryPackage) \
        else build_package(package)
    return (
        f"\"{current.title}\" packs {current.project} "
        f"from session {current.source_session}: "
        f"{current.map_count} map entries in sections "
        f"{', '.join(current.map_sections) or 'none'}, "
        f"{current.candidate_count} ledger candidates "
        f"standing {', '.join(current.ledger_states) or 'none'}. "
        f"It was exported by {current.exported_by} on "
        f"{current.exported_on} (read from {current.source}).")


def panel_plain_words(source: Any) -> str:
    """The memory panel in plain words, in full."""
    if isinstance(source, PackagePanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, MemoryExportBook):
        panel = derive_panel(source)
        title = source.title
    else:
        raise ValueError(
            f"a memory export source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Memory packages, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.package_id}: \"{row.title}\" - "
            f"{row.project} from session {row.source_session}, "
            f"{row.piece_count} pieces (map {row.map_count}, "
            f"ledger {row.candidate_count}), exported by "
            f"{row.exported_by} on {row.exported_on}")
    lines.extend(panel.account)
    return "\n".join(lines)


def verdict_plain_words(source: Any) -> str:
    """The portability verdict in plain words."""
    if isinstance(source, PortabilityVerdict):
        verdict = validate_verdict(source)
    elif isinstance(source, (MemoryExportBook, MemoryPackageRegistry)):
        verdict = derive_verdict(source)
    else:
        raise ValueError(
            f"a memory export source is needed, got {source!r}")
    return (
        f"Portability verdict: {verdict.verdict} - "
        f"{verdict.total_packages} packages carry "
        f"{verdict.total_pieces} pieces "
        f"({verdict.total_map_entries} map entries, "
        f"{verdict.total_candidates} ledger candidates) "
        f"across {verdict.distinct_projects} projects: "
        f"{verdict.total_complete} ride both, "
        f"{verdict.total_map_only} map-only, "
        f"{verdict.total_ledger_only} ledger-only.")


# ---------------------------------------------------------------------
# Screens: the formatters and the /memoryxport grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> MemoryExportBook:
    if source is None:
        return load_memory_import_export()
    if isinstance(source, MemoryPackageRegistry):
        return source.book()
    if isinstance(source, MemoryExportBook):
        return source
    raise ValueError(f"a memory export book is needed, got {source!r}")


def format_package(package: Any) -> str:
    """One memory package as a screen block, provenance whole."""
    current = package if isinstance(package, MemoryPackage) \
        else build_package(package)
    lines = [
        f"{current.package_id or '-'}: \"{current.title}\" - "
        f"{current.project} from session {current.source_session}, "
        f"exported by {current.exported_by} on {current.exported_on}",
        f"Map: {current.map_count} entries - "
        f"{', '.join(current.map_entry_ids) or 'none'} "
        f"(sections: {', '.join(current.map_sections) or 'none'}).",
        f"Ledger: {current.candidate_count} candidates - "
        f"{', '.join(current.candidate_ids) or 'none'} "
        f"(states: {', '.join(current.ledger_states) or 'none'}).",
        f"(read from {current.source})",
        "This record holds a memory package as data - "
        "it writes no live memory itself.",
    ]
    return "\n".join(lines)


def format_packages(source: Any = None,
                    project: Any = None) -> str:
    """Memory packages of one book, in held order.

    With *project* named, only the packages packing
    that project stand.
    """
    book = _source_book(source)
    wanted = _check_title(
        project, "a project") if project is not None else None
    lines = []
    for item in book.packages:
        if wanted is not None and item.project != wanted:
            continue
        lines.append(
            f"{item.package_id or '-'}: \"{item.title}\" - "
            f"{item.project} from session {item.source_session}, "
            f"{item.piece_count} pieces (map {item.map_count}, "
            f"ledger {item.candidate_count}), exported by "
            f"{item.exported_by} on {item.exported_on}")
    if not lines:
        lines.append("No memory packages are held.")
    return "\n".join(lines)


def format_panel(source: Any = None) -> str:
    """The memory panel as a screen block."""
    if isinstance(source, PackagePanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        if not book.packages:
            return (f"Memory panel in {book.title}:\n"
                    f"No memory packages are held.")
        panel = derive_panel(book)
        lines = [f"Memory panel in {book.title}:"]
    lines.append("Memory packages, in panel order:")
    for row in panel.rows:
        lines.append(
            f"{row.package_id}: \"{row.title}\" - "
            f"{row.project} from session {row.source_session}, "
            f"{row.piece_count} pieces (map {row.map_count}, "
            f"ledger {row.candidate_count}), exported by "
            f"{row.exported_by} on {row.exported_on}")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None) -> str:
    """The portability verdict as a screen block, for the whole book."""
    if isinstance(source, PortabilityVerdict):
        verdict = validate_verdict(source)
        lines = [verdict_plain_words(verdict)]
    else:
        book = _source_book(source)
        verdict = derive_verdict(book)
        lines = [f"Portability verdict in {book.title}:",
                 verdict_plain_words(verdict)]
    lines.append(
        "This verdict is a derivation for reporting - "
        "it changes nothing any live memory holds.")
    return "\n".join(lines)


def format_memory_import_export_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /memoryxport."""
    book = _source_book(source)
    lines = ["Memory Import/Export (M-164) - "
             + PLAIN_EXPLANATION, ""]
    lines.append(format_packages(book))
    lines.append("")
    lines.append(format_panel(book))
    lines.append("")
    lines.append(format_verdict(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_memoryxport_args(args: Any) -> Tuple[str, Any]:
    """Parse the /memoryxport grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    memory export book; ``package <package-id>``
    shows one package with its provenance whole;
    ``project <project>`` shows the packages packing
    one project; ``panel`` shows the memory panel
    derived from the whole book; ``verdict`` shows
    the portability verdict derived for the whole
    book. Anything else is a usage error naming the
    grammar. Returns ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head in ("panel", "verdict") and len(words) == 1:
        return (head, None)
    if head == "package" and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "project" and len(words) == 2:
        try:
            return (head, _check_word(words[1], "a project"))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
